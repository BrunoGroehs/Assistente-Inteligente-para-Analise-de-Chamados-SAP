from copy import deepcopy
from decimal import Decimal
import json
import re
import time

from sqlalchemy import func, select

from .approvals import ApprovalGateway, PolicyError, quantity_text
from .contracts import Analysis, Evidence, validate_grounding
from .citations import cited_knowledge, official_url, safe_answer_text
from .database import GENERAL_CHAT, Audit, Message, new_id
from .provider import ProviderError
from .grounding import insufficient_analysis, insufficient_assessment, out_of_scope_analysis, supported_ids


def resolve_order(state, ticket, history):
    """Resolve apenas leituras dentro da sessão; não altera o vínculo do chamado."""
    for entry in reversed(history):
        if entry["role"] != "user":
            continue
        references = set(re.findall(r"\b\d{10}\b", entry["content"]))
        if len(references) > 1:
            return None
        if references:
            purchase_order = references.pop()
            item_match = re.search(r"\bitem\s+(\d{1,5})\b", entry["content"], re.I)
            candidates = [x for x in state["orders"].values() if x["purchase_order"] == purchase_order
                          and (not item_match or x["item"] == item_match.group(1))]
            return deepcopy(candidates[0]) if len(candidates) == 1 else None
    return deepcopy(state["orders"].get(f"{ticket['purchase_order']}/{ticket['item']}"))


def render_analysis(analysis, evidence=()):
    numbers = {item.id: (f"[{index}]({official_url(item.source_url)})" if official_url(item.source_url) else f"[{index}]")
               for index, item in enumerate(cited_knowledge(analysis, evidence), 1)}
    lines = [safe_answer_text(analysis.summary)]
    if analysis.facts:
        lines.extend(["", "**Fatos consultados**"])
        for fact in analysis.facts:
            citations = " ".join(numbers[key] for key in dict.fromkeys(fact.evidence_ids) if key in numbers)
            lines.append(f"- {safe_answer_text(fact.text)}" + (f" {citations}" if citations else ""))
    for title, values in [("Possíveis causas", analysis.hypotheses),
                          ("Precisamos esclarecer", analysis.missing_information),
                          ("Próximos passos", analysis.next_steps)]:
        if values:
            lines.extend(["", f"**{title}**", *[f"- {safe_answer_text(x)}" for x in values]])
    if analysis.human_review:
        lines.extend(["", "Este caso precisa de validação humana."])
    if analysis.action:
        lines.extend(["", "A operação solicitada depende de aprovação no cartão abaixo."])
    return "\n".join(lines)


class AssistantService:
    def __init__(self, store, retriever, provider, max_analyses=30):
        self.store, self.retriever, self.provider = store, retriever, provider
        self.max_analyses = max_analyses
        self.gateway = ApprovalGateway(store)

    def analyze(self, context, ticket_id, message, submission_id=None):
        if not message.strip() or len(message) > 6000:
            raise ValueError("Envie uma mensagem de até 6.000 caracteres.")
        message = message.strip()
        channel = ticket_id if ticket_id is not None else GENERAL_CHAT
        submission_id = submission_id or new_id()
        with self.store.transaction() as db:
            workspace = self.store.authorize(db, context, lock=True)
            ticket = deepcopy(workspace.data["tickets"].get(ticket_id)) if ticket_id is not None else None
            if ticket_id is not None and not ticket:
                raise ValueError("Chamado não encontrado.")
            existing = db.scalar(select(Message).where(Message.workspace_id == workspace.id,
                                 Message.submission_id == submission_id, Message.role == "user"))
            if existing:
                if existing.ticket != channel or existing.content != message:
                    raise ValueError("Identificador de submissão já utilizado para outra mensagem.")
                return {"submission_id": submission_id, "state": existing.details.get("state", "processing")}
            count = db.scalar(select(func.count()).select_from(Message).where(
                Message.workspace_id == workspace.id, Message.role == "user"))
            if count >= self.max_analyses:
                raise ValueError("Limite de análises desta sessão atingido.")
            attachment = {"id": ticket_id, "title": ticket["title"],
                          "reference": ticket.get("support", {}).get("reference") or f"SIM-{ticket_id}"} if ticket else None
            db.add(Message(workspace_id=workspace.id, ticket=channel, submission_id=submission_id,
                           role="user", content=message.strip(), details={"state": "processing", "attachment": attachment}))
            state = deepcopy(workspace.data)

        started = time.perf_counter()
        steps = []
        evidence, metadata = [], {}
        try:
            steps.append({"step": "Solicitação recebida", "elapsed_ms": 0})
            history = self.store.messages(context, channel)[-10:]
            user_text = "\n".join(dict.fromkeys([*([ticket["description"]] if ticket else []), *[
                x["content"] for x in history if x["role"] == "user"]]))
            reported_context = "\n\nDados informados na abertura (fictícios; não comprovam execução atual):\n" + json.dumps(
                ticket["support"], ensure_ascii=False) if ticket and ticket.get("support") else ""
            evidence.append(Evidence(id="RELATO", title="Relato do usuário", content=user_text + reported_context,
                                     kind="relato_usuario", version=submission_id))
            order = resolve_order(state, ticket, history) if ticket else None
            if order:
                facts = {**order, "remaining": quantity_text(Decimal(order["ordered"]) - Decimal(order["received"]))}
                evidence.append(Evidence(id="DATA", title="Consulta ao SAP simulado",
                    content=json.dumps(facts, ensure_ascii=False), kind="consulta_simulada", version=str(order["version"])))
                steps.append({"step": "Pedido e histórico simulados consultados", "elapsed_ms": round((time.perf_counter()-started)*1000)})
            query = message + ("\n" + ticket["title"] + "\n" + ticket["description"] if ticket else "")
            recovered, retrieval_meta = self.retriever.search(query)
            evidence.extend(recovered)
            metadata["retrieval"] = retrieval_meta
            codes = set(re.findall(r"\b[ZY][A-Z0-9_]*\d[A-Z0-9_]*\b", user_text))
            undocumented = sorted(code for code in codes if not any(code in x.content for x in recovered))
            steps.append({"step": "Busca híbrida e seleção de evidências concluídas", "elapsed_ms": round((time.perf_counter()-started)*1000)})
            if not recovered or undocumented:
                assessment = insufficient_assessment("Base vazia ou código customizado sem documentação.")
                check_meta = {"method": "server_policy"}
            else:
                assessment, check_meta = self.provider.assess_knowledge({
                    "ticket": ticket, "case_attached": ticket is not None, "message": message,
                    "environment": "SAP MM simulado; dados fictícios",
                    "observations": [x.model_dump() for x in evidence if x.kind in {"consulta_simulada", "relato_usuario"}],
                    "history": [{"role": x["role"], "content": x["content"]} for x in history],
                    "evidence": [x.model_dump() for x in recovered]})
            try:
                approved_ids = supported_ids(assessment, recovered)
            except ValueError:
                check_meta["rejected_supports"] = [x.model_dump() for x in assessment.supports]
                assessment = insufficient_assessment("Prova de cobertura inválida; resposta técnica bloqueada.")
                approved_ids = []
            knowledge_check = {**assessment.model_dump(), "provider": check_meta}
            steps.append({"step": "Cobertura do conhecimento verificada para a pergunta atual"})
            provider_meta = {"server_policy": "insufficient_knowledge"}
            if assessment.scope == "fora_do_escopo":
                analysis = out_of_scope_analysis()
                provider_meta = {"server_policy": "fora_do_escopo"}
            elif not approved_ids:
                analysis = insufficient_analysis()
            else:
                generation_evidence = [x for x in evidence if x.kind in {"consulta_simulada", "relato_usuario"}
                                       or x.id in approved_ids]
                analysis, provider_meta = self.provider.analyze(
                    {"ticket": ticket, "case_attached": ticket is not None, "message": message,
                     "evidence": [x.model_dump() for x in generation_evidence],
                     "undocumented_codes": undocumented, "validated_scope": assessment.scope},
                    [{"role": x["role"], "content": x["content"]} for x in history])
                if ticket is None and analysis.action:
                    analysis = Analysis(summary="Para solicitar uma alteração, anexe o chamado correspondente. "
                                        "Nenhuma operação foi proposta ou executada.",
                        process="recebimento_pedido_compra", facts=[], hypotheses=[], missing_information=[],
                        next_steps=["Use o botão Chamados para anexar o caso antes de solicitar a alteração."],
                        references=[], confidence="baixa", confidence_reason="Não há chamado anexado para vincular a operação.",
                        human_review=False, action=None)
                    provider_meta["server_policy"] = "attachment_required"
                else:
                    self._validate_evidence(analysis, generation_evidence, undocumented)
                    if analysis.process != "fora_do_escopo" and not set(analysis.references) & set(approved_ids):
                        analysis = insufficient_analysis()
                        provider_meta["server_policy"] = "uncited_knowledge"
            self._validate_evidence(analysis, evidence, undocumented)
            steps.append({"step": "Resposta estruturada e referências validadas", "elapsed_ms": round((time.perf_counter()-started)*1000)})
            metadata = {"attachment": attachment, "retrieval": retrieval_meta, "provider": provider_meta, "knowledge_check": knowledge_check,
                        "analysis": analysis.model_dump(mode="json")}
            content = render_analysis(analysis, evidence)
            with self.store.transaction() as db:
                workspace = self.store.authorize(db, context, lock=True)
                if analysis.action:
                    try:
                        current_ticket = workspace.data["tickets"][ticket_id]
                        current_order = workspace.data["orders"].get(f"{order['purchase_order']}/{order['item']}") if order else None
                        if current_ticket != ticket or current_order != order:
                            raise PolicyError("Os dados mudaram durante a análise. Solicite uma nova proposta.")
                        if analysis.action.operation == "registrar_recebimento_simulado":
                            parameters = analysis.action.parameters
                            if not order or (parameters.purchase_order, parameters.item) != (order["purchase_order"], order["item"]):
                                raise PolicyError("A proposta não corresponde ao pedido/item consultado nesta análise.")
                        proposal = self.gateway.prepare(db, workspace, ticket_id, analysis.action)
                        metadata["proposal_id"] = proposal.id
                        steps.append({"step": "Proposta validada; aguardando decisão humana"})
                    except PolicyError as exc:
                        metadata["proposal_blocked"] = str(exc)
                        content += "\n\n**Proposta bloqueada pelo servidor:** " + str(exc)
                        steps.append({"step": "Proposta impedida pela política do servidor"})
                details = {**metadata, "evidence": [x.model_dump() for x in evidence],
                           "steps": steps, "latency_ms": round((time.perf_counter()-started)*1000)}
                db.add(Message(workspace_id=workspace.id, ticket=channel, submission_id=submission_id,
                               role="assistant", content=content, details=details))
                row = db.scalar(select(Message).where(Message.workspace_id == workspace.id,
                                Message.submission_id == submission_id, Message.role == "user"))
                row.details = {"state": "completed", "attachment": attachment}
                db.add(Audit(workspace_id=workspace.id, event="analise_concluida",
                             details={"submission_id": submission_id, "ticket": ticket_id,
                                      "references": analysis.references, "latency_ms": details["latency_ms"]}))
            return {"submission_id": submission_id, "state": "completed"}
        except (ProviderError, ValueError) as exc:
            # Mensagens são controladas pelos adaptadores; não persistir payloads/segredos de erro.
            content = str(exc) if isinstance(exc, ProviderError) else "Não foi possível validar a análise. Nenhuma ação executada."
            with self.store.transaction() as db:
                workspace = self.store.authorize(db, context, lock=True)
                failure_details = {"error": True, "attachment": attachment, "steps": steps, "evidence": [x.model_dump() for x in evidence],
                                   "retrieval": metadata.get("retrieval"),
                                   "provider": getattr(exc, "metadata", {}),
                                   "latency_ms": round((time.perf_counter()-started)*1000)}
                db.add(Message(workspace_id=workspace.id, ticket=channel, submission_id=submission_id,
                               role="assistant", content=content, details=failure_details))
                row = db.scalar(select(Message).where(Message.workspace_id == workspace.id,
                                Message.submission_id == submission_id, Message.role == "user"))
                row.details = {"state": "failed", "attachment": attachment}
                db.add(Audit(workspace_id=workspace.id, event="analise_falhou",
                             details={"submission_id": submission_id, "error": type(exc).__name__}))
            return {"submission_id": submission_id, "state": "failed"}

    @staticmethod
    def _validate_evidence(analysis, evidence, undocumented_codes=()):
        validate_grounding(analysis, evidence, undocumented_codes)

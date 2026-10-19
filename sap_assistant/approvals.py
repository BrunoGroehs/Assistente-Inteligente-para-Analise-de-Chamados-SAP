from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import hmac
import json

from sqlalchemy import select

from .contracts import ReceiptRequest, StatusRequest
from .database import AccessDenied, Audit, Proposal, new_id, utcnow, validate_chat_id


class PolicyError(ValueError):
    pass


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def valid_envelope(proposal):
    payload = proposal.payload
    return (isinstance(payload, dict) and hmac.compare_digest(digest(payload), proposal.integrity)
            and payload.get("workspace_id") == proposal.workspace_id
            and payload.get("ticket") == proposal.ticket
            and payload.get("envelope") == {"proposal_id": proposal.id, "created_at": proposal.created_at,
                                            "expires_at": proposal.expires_at})


def quantity_text(value):
    return format(Decimal(value).normalize(), "f")


def canonical_phrase(request, ticket):
    if isinstance(request, ReceiptRequest):
        p = request.parameters
        return (f"Posso registrar o recebimento simulado de {quantity_text(p.quantity)} {p.unit} "
                f"no pedido {p.purchase_order}, item {p.item}?")
    labels = {"resolvido": "resolvido", "em_validacao_humana": "em validação humana"}
    return f"Posso alterar o chamado {ticket} para {labels[request.parameters.status]}?"


def build_snapshot(data, ticket, request):
    current_ticket = data["tickets"].get(ticket)
    if not current_ticket:
        raise PolicyError("Chamado não encontrado nesta sessão.")
    snapshot = {"ticket_version": current_ticket["version"], "ticket_fingerprint": digest(current_ticket)}
    if isinstance(request, ReceiptRequest):
        p = request.parameters
        if current_ticket["purchase_order"] and (p.purchase_order, p.item) != (current_ticket["purchase_order"], current_ticket["item"]):
            raise PolicyError("O pedido/item não pertence ao chamado selecionado.")
        order = data["orders"].get(f"{p.purchase_order}/{p.item}")
        if not order:
            raise PolicyError("Pedido/item não encontrado.")
        for name in ("unit", "material", "plant", "storage_location"):
            if getattr(p, name) != order[name]:
                raise PolicyError("Material, unidade ou localização divergem dos dados consultados.")
        remaining = Decimal(order["ordered"]) - Decimal(order["received"])
        if order["delivery_completed"] or p.quantity > remaining:
            raise PolicyError("Recebimento não permitido: item concluído ou quantidade acima do saldo simulado.")
        snapshot["order_version"] = order["version"]
        snapshot["order_fingerprint"] = digest(order)
        effect = {"operation": "Recebimento simulado", "purchase_order": p.purchase_order,
                  "item": p.item, "material": p.material, "plant": p.plant,
                  "storage_location": p.storage_location, "quantity": quantity_text(p.quantity),
                  "unit": p.unit, "posting_date": p.posting_date.isoformat(),
                  "before": quantity_text(remaining), "after": quantity_text(remaining - p.quantity)}
    elif isinstance(request, StatusRequest):
        if current_ticket["status"] == request.parameters.status:
            raise PolicyError("O chamado já está nessa situação.")
        effect = {"operation": "Alteração de situação", "ticket": ticket,
                  "before": current_ticket["status"], "after": request.parameters.status}
    else:
        raise PolicyError("Operação não permitida.")
    return snapshot, effect


class ApprovalGateway:
    """Chamado pelo servidor. Nunca registrar decide() como ferramenta do LLM."""

    def __init__(self, store):
        self.store = store

    def prepare(self, db, workspace, ticket, request, now=None, chat_id=None):
        from pydantic import TypeAdapter
        from .contracts import ActionRequest

        # Revalidar na fronteira, mesmo se um objeto Python tiver sido alterado
        # depois da validação inicial do adaptador de LLM.
        request = TypeAdapter(ActionRequest).validate_python(request.model_dump(mode="json"))
        validate_chat_id(chat_id)
        now = now or utcnow()
        snapshot, effect = build_snapshot(workspace.data, ticket, request)
        phrase = canonical_phrase(request, ticket)
        # A IA recebe esse formato no prompt. Qualquer frase divergente é bloqueada.
        if request.confirmation_phrase != phrase:
            raise PolicyError("A frase de confirmação diverge do formato e dos dados da operação. Reformule a proposta.")
        payload = {"workspace_id": workspace.id, "ticket": ticket,
                   "request": request.model_dump(mode="json"), "snapshot": snapshot, "effect": effect}
        if chat_id is not None:
            payload["chat_id"] = chat_id
        # Evita cartões pendentes duplicados para exatamente o mesmo payload.
        candidates = db.scalars(select(Proposal).where(Proposal.workspace_id == workspace.id,
                               Proposal.ticket == ticket, Proposal.state == "pendente")).all()
        for existing in candidates:
            previous = {key: value for key, value in existing.payload.items() if key != "envelope"}
            if (previous == payload and valid_envelope(existing)
                    and datetime.fromisoformat(existing.expires_at) > now):
                return existing
        proposal_id, created_at, expires_at = new_id(), now.isoformat(), (now + timedelta(minutes=15)).isoformat()
        payload["envelope"] = {"proposal_id": proposal_id, "created_at": created_at, "expires_at": expires_at}
        proposal = Proposal(id=proposal_id, workspace_id=workspace.id, ticket=ticket,
                            payload=payload, integrity=digest(payload), state="pendente",
                            created_at=created_at, expires_at=expires_at,
                            result={})
        db.add(proposal)
        db.add(Audit(workspace_id=workspace.id, event="proposta_criada",
                     details={"proposal_id": proposal.id, "operation": request.operation}))
        return proposal

    def propose(self, context, ticket, request, now=None, chat_id=None):
        with self.store.transaction() as db:
            workspace = self.store.authorize(db, context, lock=True)
            return self.prepare(db, workspace, ticket, request, now, chat_id).id

    def decide(self, context, proposal_id, approve, now=None, chat_id=None):
        if type(approve) is not bool:
            raise PolicyError("Decisão humana deve ser Sim ou Não.")
        validate_chat_id(chat_id)
        now = now or utcnow()
        with self.store.transaction() as db:
            workspace = self.store.authorize(db, context, lock=True)
            proposal = db.scalar(select(Proposal).where(Proposal.id == proposal_id,
                                 Proposal.workspace_id == context.workspace_id).with_for_update())
            if proposal is None:
                raise AccessDenied("Proposta não encontrada nesta sessão.")
            if proposal.payload.get("chat_id") != chat_id:
                raise AccessDenied("A proposta pertence a outra conversa.")
            if proposal.state != "pendente":
                return {"state": proposal.state, **proposal.result}

            state, result = self._validate_and_execute(db, workspace, proposal, approve, now)
            proposal.state, proposal.result = state, result
            db.add(Audit(workspace_id=context.workspace_id, event="decisao_humana",
                         details={"proposal_id": proposal_id, "decision": "sim" if approve else "nao",
                                  "state": state, "result": result}))
            return {"state": state, **result}

    def _validate_and_execute(self, db, workspace, proposal, approve, now):
        if not valid_envelope(proposal):
            return "invalidada", {"message": "A proposta foi modificada. Solicite uma nova análise."}
        if datetime.fromisoformat(proposal.expires_at) <= now:
            return "expirada", {"message": "A autorização expirou. Nenhuma alteração realizada."}
        if not approve:
            return "recusada", {"message": "Solicitação recusada. Nenhuma alteração realizada."}

        from pydantic import TypeAdapter
        from .contracts import ActionRequest

        request = TypeAdapter(ActionRequest).validate_python(proposal.payload["request"])
        try:
            snapshot, effect = build_snapshot(workspace.data, proposal.ticket, request)
        except PolicyError:
            return "invalidada", {"message": "Os dados mudaram. Solicite uma nova proposta."}
        if snapshot != proposal.payload["snapshot"] or effect != proposal.payload["effect"]:
            return "invalidada", {"message": "Os dados mudaram. Solicite uma nova proposta."}
        before = deepcopy(workspace.data)
        try:
            with db.begin_nested():
                proposal.state = "aprovada"
                db.add(Audit(workspace_id=workspace.id, event="acao_aprovada",
                             details={"proposal_id": proposal.id}))
                proposal.state = "executando"
                result = self._execute(workspace, proposal, request)
                db.flush()
            return "executada", result
        except Exception:
            workspace.data = before
            return "falhou", {"message": "Falha na operação simulada. Nenhuma alteração confirmada."}

    def _execute(self, workspace, proposal, request):
        data = deepcopy(workspace.data)
        if isinstance(request, ReceiptRequest):
            p = request.parameters
            order = data["orders"][f"{p.purchase_order}/{p.item}"]
            order["received"] = quantity_text(Decimal(order["received"]) + p.quantity)
            order["version"] += 1
            receipt_id = "SIM-" + new_id()
            data["receipts"].append({"id": receipt_id, "proposal_id": proposal.id,
                                     **p.model_dump(mode="json")})
            result = {"receipt_id": receipt_id, "message": "Recebimento simulado registrado.",
                      "effect": proposal.payload["effect"]}
        else:
            ticket = data["tickets"][proposal.ticket]
            ticket["status"] = request.parameters.status
            ticket["version"] += 1
            result = {"message": "Situação do chamado atualizada.", "effect": proposal.payload["effect"]}
        workspace.data = data
        return result

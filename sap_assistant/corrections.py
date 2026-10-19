"""Complemento humano de uma correção: prepara proposta, nunca executa negócio."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import Field
from sqlalchemy import select

from .approvals import ApprovalGateway, PolicyError, canonical_phrase, digest, quantity_text
from .contracts import Contract, ReceiptRequest, StatusRequest
from .database import AccessDenied, Audit, Message, Proposal, utcnow, validate_chat_id


class CorrectionInput(Contract):
    quantity: Decimal | None = Field(default=None, gt=0, le=1000000000, max_digits=16, decimal_places=3, allow_inf_nan=False)
    posting_date: date | None = None
    status: Literal["em_validacao_humana", "resolvido"] | None = None


def correction_draft(analysis, ticket, order):
    operation = analysis.correction_operation
    if analysis.action or not operation or not ticket:
        return None
    if operation == "registrar_recebimento_simulado":
        if not order or order["delivery_completed"] or Decimal(order["ordered"]) <= Decimal(order["received"]):
            return None
    return {"operation": operation, "ticket": ticket["id"], "ticket_fingerprint": digest(ticket),
            "order": order, "expires_at": (utcnow() + timedelta(minutes=15)).isoformat()}


def public_correction(draft):
    if not draft:
        return None
    result = {key: draft[key] for key in ("operation", "ticket", "expires_at")}
    if draft["operation"] == "registrar_recebimento_simulado":
        order = draft["order"]
        result.update({key: order[key] for key in ("purchase_order", "item", "material", "unit")})
        result["max_quantity"] = quantity_text(Decimal(order["ordered"]) - Decimal(order["received"]))
    return result


def prepare_correction(store, context, message_id, values, chat_id=None):
    validate_chat_id(chat_id)
    values = CorrectionInput.model_validate(values.model_dump())
    with store.transaction() as db:
        workspace = store.authorize(db, context, lock=True)
        message = db.scalar(select(Message).where(Message.workspace_id == workspace.id, Message.id == message_id,
                                                 Message.role == "assistant"))
        if not message or message.details.get("chat_id") != chat_id:
            raise AccessDenied("Correção não encontrada nesta conversa.")
        draft = message.details.get("correction")
        if not draft or message.details.get("error"):
            raise PolicyError("Esta resposta não contém uma correção disponível. Solicite uma nova análise.")
        if draft["operation"] == "registrar_recebimento_simulado":
            if values.quantity is None or values.posting_date is None or values.status is not None:
                raise PolicyError("Informe a quantidade e a data de lançamento para preparar o recebimento.")
            request = ReceiptRequest(operation=draft["operation"], parameters={
                **{key: draft["order"][key] for key in ("purchase_order", "item", "material", "unit", "plant", "storage_location")},
                "quantity": values.quantity, "posting_date": values.posting_date}, confirmation_phrase="Pergunta a preencher")
        else:
            if values.status is None or values.quantity is not None or values.posting_date is not None:
                raise PolicyError("Selecione a situação desejada para o chamado.")
            request = StatusRequest(operation=draft["operation"], parameters={"status": values.status},
                                    confirmation_phrase="Pergunta a preencher")
        # Os dados faltantes vieram do humano; a pergunta final é montada pelo
        # servidor com o mesmo formato que a IA usa nas propostas completas.
        request.confirmation_phrase = canonical_phrase(request, draft["ticket"])
        previous = message.details.get("proposal_id")
        if previous:
            proposal = db.get(Proposal, previous)
            if (not proposal or proposal.workspace_id != workspace.id or proposal.payload.get("chat_id") != chat_id
                    or proposal.payload["request"] != request.model_dump(mode="json")):
                raise PolicyError("A correção já foi preparada com outros parâmetros. Solicite uma nova análise.")
            return proposal.id
        latest = db.scalar(select(Message).where(Message.workspace_id == workspace.id, Message.ticket == message.ticket,
            Message.role == "assistant", Message.details["chat_id"].as_string() == chat_id)
            .order_by(Message.created_at.desc(), Message.id.desc()).limit(1))
        if latest.id != message.id:
            raise PolicyError("Existe uma análise mais recente deste chamado. Use a correção mais recente.")
        if datetime.fromisoformat(draft["expires_at"]) <= utcnow():
            raise PolicyError("A correção venceu. Solicite uma nova análise.")
        ticket = workspace.data["tickets"].get(draft["ticket"])
        order = draft["order"]
        current_order = workspace.data["orders"].get(f"{order['purchase_order']}/{order['item']}") if order else None
        if digest(ticket) != draft["ticket_fingerprint"] or (order and current_order != order):
            raise PolicyError("Os dados mudaram. Solicite uma nova análise antes de preparar a correção.")
        proposal = ApprovalGateway(store).prepare(db, workspace, draft["ticket"], request, chat_id=chat_id)
        message.details = {**message.details, "proposal_id": proposal.id}
        db.add(Audit(workspace_id=workspace.id, event="correcao_complementada",
                     details={"message_id": message.id, "proposal_id": proposal.id, "chat_id": chat_id}))
        return proposal.id

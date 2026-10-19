"""Contexto opcional, histórico imutável e bloqueio de operações sem anexo."""
from copy import deepcopy
import json

import pytest

from sap_assistant.contracts import StatusRequest
from sap_assistant.database import AccessDenied, GENERAL_CHAT, new_id
from sap_assistant.retrieval import Retriever
from sap_assistant.service import AssistantService
from conftest import ControlledProvider, receipt_request


def test_general_question_uses_rag_without_reading_any_simulated_order(store, context):
    captured = {}

    class Inspect(ControlledProvider):
        def assess_knowledge(self, ctx):
            captured["coverage"] = deepcopy(ctx)
            return super().assess_knowledge(ctx)

        def analyze(self, ctx, history):
            captured["generation"] = deepcopy(ctx)
            return super().analyze(ctx, history)

    provider = Inspect()
    service = AssistantService(store, Retriever(store, provider), provider)
    before = store.state(context)
    assert service.analyze(context, None, "O que é recebimento com pedido?")["state"] == "completed"
    assert captured["generation"]["ticket"] is None and captured["generation"]["case_attached"] is False
    assert not any(x["id"] == "DATA" for x in captured["generation"]["evidence"])
    assert not any(x["id"] == "DATA" for x in captured["coverage"]["observations"])
    assert not any(key in json.dumps(captured) for key in ["4500001007", "MAT-007", context.token])
    messages = store.messages(context, GENERAL_CHAT)
    assert len(messages) == 2 and all(x["details"]["attachment"] is None for x in messages)
    assert messages[-1]["details"]["analysis"]["references"]
    assert store.state(context) == before and not store.proposals(context)


def test_detached_history_excludes_old_cases_but_general_history_is_kept(store, context):
    histories = []

    class Inspect(ControlledProvider):
        def analyze(self, ctx, history):
            histories.append(deepcopy((ctx, history)))
            return super().analyze(ctx, history)

    provider = Inspect()
    service = AssistantService(store, Retriever(store, provider), provider)
    service.analyze(context, "C01", "Pedido 4500001001: explique o saldo. MARCADOR_CASO")
    service.analyze(context, None, "O que é documento de material? MARCADOR_GERAL")
    service.analyze(context, "C02", "Explique a entrega parcial. MARCADOR_OUTRO")
    service.analyze(context, None, "Explique recebimento com pedido.")
    ctx, history = histories[-1]
    payload = json.dumps([ctx, history])
    assert "MARCADOR_GERAL" in payload
    assert "MARCADOR_CASO" not in payload and "MARCADOR_OUTRO" not in payload
    assert "4500001001" not in payload and "MAT-001" not in payload
    timeline = store.messages(context)
    assert len(timeline) == 8 and [x["ticket"] for x in timeline[::2]] == ["C01", GENERAL_CHAT, "C02", GENERAL_CHAT]
    assert timeline[0]["details"]["attachment"]["id"] == "C01"
    assert timeline[2]["details"]["attachment"] is None
    assert timeline[4]["details"]["attachment"]["id"] == "C02"


@pytest.mark.parametrize("operation", ["receipt", "status"])
def test_forged_model_action_without_attachment_is_blocked_before_gateway(store, context, operation):
    action = receipt_request(store, context) if operation == "receipt" else StatusRequest(
        operation="atualizar_status_chamado", parameters={"status": "resolvido"},
        confirmation_phrase="Posso alterar o chamado C07 para resolvido?")

    class Forged(ControlledProvider):
        def analyze(self, ctx, history):
            answer, metadata = super().analyze(ctx, history)
            answer.action = action
            return answer, metadata

    provider = Forged()
    service = AssistantService(store, Retriever(store, provider), provider)
    before = store.state(context)
    assert service.analyze(context, None, "Faça uma alteração.")["state"] == "completed"
    message = store.messages(context, GENERAL_CHAT)[-1]
    assert message["details"]["analysis"]["action"] is None
    assert "anexe" in message["content"].lower()
    assert message["details"]["provider"]["server_policy"] == "attachment_required"
    assert store.state(context) == before and not store.proposals(context)


def test_general_submission_is_idempotent_and_cannot_be_rebound_to_case(service, store, context):
    submission = new_id()
    service.analyze(context, None, "Explique recebimento.", submission)
    service.analyze(context, None, "Explique recebimento.", submission)
    assert service.provider.calls == 1 and len(store.messages(context)) == 2
    with pytest.raises(ValueError):
        service.analyze(context, "C01", "Explique recebimento.", submission)


def test_all_messages_and_proposals_remain_scoped_to_authorized_workspace(service, store, context):
    service.analyze(context, None, "Explique recebimento.")
    other = store.create_workspace()
    assert not store.messages(other) and not store.proposals(other)
    from sap_assistant.database import SessionContext
    forged = SessionContext(context.workspace_id, other.token)
    with pytest.raises(AccessDenied):
        store.messages(forged)
    with pytest.raises(AccessDenied):
        store.proposals(forged)


def test_global_question_still_abstains_without_rag(service, store, context):
    from sqlalchemy import delete
    from sap_assistant.database import Chunk
    with store.transaction() as db:
        db.execute(delete(Chunk))  # Banco temporário próprio deste teste.
    before = store.state(context)
    service.analyze(context, None, "Como recebo material?")
    answer = store.messages(context, GENERAL_CHAT)[-1]["details"]["analysis"]
    assert "Não tenho informações suficientes" in answer["summary"]
    assert not answer["facts"] and not answer["hypotheses"] and answer["action"] is None
    assert service.provider.calls == 0 and store.state(context) == before

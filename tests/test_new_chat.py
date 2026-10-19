"""Conversas independentes compartilham somente o estado de negócio autorizado."""
from copy import deepcopy

import pytest

from sap_assistant.approvals import ApprovalGateway
from sap_assistant.database import AccessDenied, new_id
from sap_assistant.retrieval import Retriever
from sap_assistant.service import AssistantService
from conftest import ControlledProvider, ReceiptProvider, receipt_request


def test_new_chat_filters_history_and_preserves_business_data(store, context):
    seen = []

    class Inspect(ControlledProvider):
        def analyze(self, ctx, history):
            seen.append(deepcopy(history))
            return super().analyze(ctx, history)

    provider = Inspect()
    service = AssistantService(store, Retriever(store, provider), provider)
    before = store.state(context)
    service.analyze(context, None, "Explique recebimento. MARCADOR_ANTIGO")
    chat_id = new_id()
    assert not store.snapshot(context, chat_id)["messages"]
    service.analyze(context, None, "O que é recebimento?", chat_id=chat_id)
    assert "MARCADOR_ANTIGO" not in str(seen[-1])
    assert len(store.snapshot(context)["messages"]) == 2
    assert len(store.snapshot(context, chat_id)["messages"]) == 2
    assert len(store.messages(context)) == 4 and store.state(context) == before


def test_proposals_are_bound_to_chat_and_not_reused_across_chats(store, context):
    gateway = ApprovalGateway(store)
    request = receipt_request(store, context)
    first, second = new_id(), new_id()
    old = gateway.propose(context, "C07", request, chat_id=first)
    new = gateway.propose(context, "C07", request, chat_id=second)
    assert old != new
    assert gateway.propose(context, "C07", request, chat_id=second) == new
    assert [x["id"] for x in store.snapshot(context, first)["proposals"]] == [old]
    assert [x["id"] for x in store.snapshot(context, second)["proposals"]] == [new]
    with pytest.raises(AccessDenied):
        gateway.decide(context, old, True, chat_id=second)
    with pytest.raises(AccessDenied):
        gateway.decide(context, old, True)
    assert not store.state(context)["receipts"]
    assert gateway.decide(context, new, False, chat_id=second)["state"] == "recusada"
    assert store.snapshot(context, first)["proposals"][0]["state"] == "pendente"


def test_analyzed_proposal_carries_conversation_and_executes_only_there(store, context):
    provider = ReceiptProvider()
    service = AssistantService(store, Retriever(store, provider), provider)
    chat_id = new_id()
    service.analyze(context, "C07", "Registre 10 UN em 2026-10-18.", chat_id=chat_id)
    proposal = store.snapshot(context, chat_id)["proposals"][0]
    assert proposal["payload"]["chat_id"] == chat_id
    assert not store.snapshot(context)["proposals"]
    gateway = ApprovalGateway(store)
    assert gateway.decide(context, proposal["id"], True, chat_id=chat_id)["state"] == "executada"
    new = store.snapshot(context, new_id())
    assert not new["messages"] and not new["proposals"] and len(new["state"]["receipts"]) == 1


def test_submission_cannot_move_between_conversations(service, store, context):
    submission = new_id()
    first, second = new_id(), new_id()
    service.analyze(context, None, "Explique recebimento.", submission, chat_id=first)
    service.analyze(context, None, "Explique recebimento.", submission, chat_id=first)
    with pytest.raises(ValueError):
        service.analyze(context, None, "Explique recebimento.", submission, chat_id=second)
    assert service.provider.calls == 1 and not store.snapshot(context, second)["messages"]


@pytest.mark.parametrize("invalid", ["outra-conversa", "", 123])
def test_invalid_chat_id_does_not_create_messages(service, store, context, invalid):
    with pytest.raises(ValueError):
        service.analyze(context, None, "Explique recebimento.", chat_id=invalid)
    assert not store.messages(context)

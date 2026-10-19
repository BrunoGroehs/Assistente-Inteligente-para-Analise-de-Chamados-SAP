from copy import deepcopy
from datetime import timedelta

import pytest

from sap_assistant.approvals import ApprovalGateway, PolicyError
from sap_assistant.contracts import Analysis
from sap_assistant.corrections import CorrectionInput, prepare_correction
from sap_assistant.database import AccessDenied, Message, Workspace, new_id, utcnow
from sap_assistant.retrieval import Retriever
from sap_assistant.service import AssistantService
from sap_assistant.web_views import public_snapshot
from conftest import ControlledProvider


class CorrectionProvider(ControlledProvider):
    def analyze(self, context, history):
        analysis, meta = super().analyze(context, history)
        analysis.summary = "A quantidade relatada excede o saldo de 20 UN. Informe a quantidade correta e a data."
        analysis.correction_operation = "registrar_recebimento_simulado"
        analysis.missing_information = ["Quantidade correta e data de lançamento."]
        return analysis, meta


@pytest.fixture
def correction(store, context):
    provider = CorrectionProvider()
    service = AssistantService(store, Retriever(store, provider), provider)
    service.analyze(context, "C03", "como resolvo isso?")
    return service, store.messages(context, "C03")[-1]


def values(quantity="20"):
    return CorrectionInput(quantity=quantity, posting_date="2026-10-18")


def test_c03_has_preparation_card_without_inventing_quantity_or_date(store, context, correction):
    _, message = correction
    view = public_snapshot(store.snapshot(context))
    draft = view["messages"][-1]["correction"]
    assert draft["operation"] == "registrar_recebimento_simulado" and draft["max_quantity"] == "20"
    assert "quantity" not in draft and "posting_date" not in draft and "ticket_fingerprint" not in draft
    assert message["details"]["correction"] and not view["proposals"] and not store.state(context)["receipts"]


@pytest.mark.parametrize("approve,expected,count", [(True, "executada", 1), (False, "recusada", 0)])
def test_complement_prepares_exact_proposal_and_only_human_decision_changes_business(store, context, correction, approve, expected, count):
    _, message = correction
    before = store.state(context)
    proposal = prepare_correction(store, context, message["id"], values())
    assert store.state(context) == before
    public = public_snapshot(store.snapshot(context))["messages"][-1]
    assert public["proposal_id"] == proposal
    assert prepare_correction(store, context, message["id"], values()) == proposal
    gateway = ApprovalGateway(store)
    assert gateway.decide(context, proposal, approve)["state"] == expected
    assert gateway.decide(context, proposal, True)["state"] == expected
    assert prepare_correction(store, context, message["id"], values()) == proposal
    assert len(store.state(context)["receipts"]) == count
    with pytest.raises(PolicyError, match="outros parâmetros"):
        prepare_correction(store, context, message["id"], values("10"))


@pytest.mark.parametrize("body", [{}, {"quantity": "20"}, {"quantity": "35", "posting_date": "2026-10-18"},
                                 {"quantity": "20", "posting_date": "2026-10-18", "status": "resolvido"}])
def test_incomplete_excess_quantity_and_operation_substitution_never_create_proposal(store, context, correction, body):
    _, message = correction
    before = store.state(context)
    with pytest.raises(PolicyError):
        prepare_correction(store, context, message["id"], CorrectionInput(**body))
    assert not store.proposals(context) and store.state(context) == before


@pytest.mark.parametrize("change", ["expired", "stale", "newer", "wrong_chat", "wrong_session"])
def test_old_or_unauthorized_correction_is_blocked(store, context, correction, change):
    service, message = correction
    if change == "expired":
        with store.transaction() as db:
            row = db.get(Message, message["id"])
            details = deepcopy(row.details)
            details["correction"]["expires_at"] = (utcnow() - timedelta(seconds=1)).isoformat()
            row.details = details
    if change == "stale":
        with store.transaction() as db:
            row = db.get(Workspace, context.workspace_id)
            data = deepcopy(row.data)
            data["orders"]["4500001003/10"]["received"] = "81"
            row.data = data
    if change == "newer":
        service.analyze(context, "C03", "altere para mim")
    before = store.state(context)
    with pytest.raises((PolicyError, AccessDenied)):
        prepare_correction(store, store.create_workspace() if change == "wrong_session" else context,
                           message["id"], values(), new_id() if change == "wrong_chat" else None)
    assert not store.proposals(context) and store.state(context) == before


def test_implicit_followup_preserves_receipt_correction_context(store, context, correction, monkeypatch):
    service, _ = correction
    original = service.provider.analyze

    def inspect(ctx, history):
        assert ctx["pending_correction_operation"] == "registrar_recebimento_simulado"
        return original(ctx, history)

    monkeypatch.setattr(service.provider, "analyze", inspect)
    service.analyze(context, "C03", "altere para mim")
    assert store.messages(context, "C03")[-1]["details"]["correction"]["operation"] == "registrar_recebimento_simulado"


def test_contract_rejects_conflicting_operations_and_out_of_scope_correction(correction):
    _, message = correction
    body = message["details"]["analysis"]
    with pytest.raises(ValueError):
        Analysis.model_validate({**body, "process": "fora_do_escopo"})
    with pytest.raises(ValueError):
        Analysis.model_validate({**body, "action": {"operation": "atualizar_status_chamado",
            "parameters": {"status": "resolvido"}, "confirmation_phrase": "Posso alterar o chamado C03 para resolvido?"}})


def test_status_correction_requires_explicit_human_target_before_approval(store, context):
    class StatusProvider(ControlledProvider):
        def analyze(self, ctx, history):
            analysis, meta = super().analyze(ctx, history)
            analysis.correction_operation = "atualizar_status_chamado"
            analysis.missing_information = ["Qual situação você deseja para o chamado?"]
            return analysis, meta

    provider = StatusProvider()
    service = AssistantService(store, Retriever(store, provider), provider)
    service.analyze(context, "C03", "Quero mudar a situação deste chamado.")
    message = store.messages(context, "C03")[-1]
    with pytest.raises(PolicyError):
        prepare_correction(store, context, message["id"], CorrectionInput())
    proposal = prepare_correction(store, context, message["id"], CorrectionInput(status="em_validacao_humana"))
    assert store.state(context)["tickets"]["C03"]["status"] == "aberto"
    assert ApprovalGateway(store).decide(context, proposal, True)["state"] == "executada"
    assert store.state(context)["tickets"]["C03"]["status"] == "em_validacao_humana"
    assert not store.state(context)["receipts"]


def test_forged_correction_without_attachment_has_no_form_or_proposal(store, context):
    provider = CorrectionProvider()
    service = AssistantService(store, Retriever(store, provider), provider)
    service.analyze(context, None, "Explique o recebimento com pedido.")
    view = public_snapshot(store.snapshot(context))
    assert not view["messages"][-1]["correction"] and not view["proposals"]
    assert not store.state(context)["receipts"]


def test_no_rag_knowledge_never_offers_correction(store, context):
    class EmptyRetriever:
        def search(self, query):
            return [], {}

    service = AssistantService(store, EmptyRetriever(), CorrectionProvider())
    service.analyze(context, "C03", "altere para mim")
    view = public_snapshot(store.snapshot(context))
    assert "informações suficientes" in view["messages"][-1]["content"]
    assert not view["messages"][-1]["correction"] and not view["proposals"]

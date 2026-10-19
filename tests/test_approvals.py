from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from sap_assistant.approvals import ApprovalGateway, PolicyError, canonical_phrase
from sap_assistant.contracts import ActionRequest, StatusRequest
from sap_assistant.database import AccessDenied, Proposal, SessionContext, Store, Workspace, new_id, utcnow
from conftest import receipt_request


def test_only_valid_approval_writes_once(store, context):
    gateway = ApprovalGateway(store)
    before = store.state(context)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    assert store.state(context) == before
    result = gateway.decide(context, proposal, True)
    assert result["state"] == "executada"
    after = store.state(context)
    assert after["orders"]["4500001007/10"]["received"] == "30"
    assert len(after["receipts"]) == 1
    assert after["tickets"]["C07"]["status"] == "aberto"
    assert gateway.decide(context, proposal, True) == result
    assert store.state(context) == after
    assert any(x["event"] == "decisao_humana" for x in store.audit(context))


def test_denial_and_silence_do_not_write(store, context):
    gateway = ApprovalGateway(store)
    before = store.state(context)
    proposal = gateway.propose(context, "C08", receipt_request(store, context, "C08", "5"))
    assert store.proposals(context, "C08")[0]["state"] == "pendente"
    assert store.state(context) == before
    assert gateway.decide(context, proposal, False)["state"] == "recusada"
    assert gateway.decide(context, proposal, True)["state"] == "recusada"
    assert store.state(context) == before


def test_expiration_boundary(store, context):
    gateway = ApprovalGateway(store)
    now = utcnow()
    proposal = gateway.propose(context, "C07", receipt_request(store, context), now)
    result = gateway.decide(context, proposal, True, now + timedelta(minutes=15))
    assert result["state"] == "expirada"
    assert not store.state(context)["receipts"]


def test_tampering_is_rejected(store, context):
    gateway = ApprovalGateway(store)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    with store.transaction() as db:
        row = db.get(Proposal, proposal)
        changed = deepcopy(row.payload)
        changed["request"]["parameters"]["quantity"] = "20"
        row.payload = changed
    assert gateway.decide(context, proposal, True)["state"] == "invalidada"
    assert not store.state(context)["receipts"]


def test_changed_order_invalidates_other_proposal(store, context):
    gateway = ApprovalGateway(store)
    first = gateway.propose(context, "C07", receipt_request(store, context, quantity="10"))
    second = gateway.propose(context, "C07", receipt_request(store, context, quantity="5"))
    gateway.decide(context, first, True)
    assert gateway.decide(context, second, True)["state"] == "invalidada"
    assert len(store.state(context)["receipts"]) == 1


def test_sessions_cannot_read_or_approve_each_other(store, context):
    gateway = ApprovalGateway(store)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    other = store.create_workspace()
    with pytest.raises(AccessDenied):
        gateway.decide(other, proposal, True)
    forged = SessionContext(context.workspace_id, other.token)
    with pytest.raises(AccessDenied):
        store.state(forged)
    assert not store.proposals(other, "C07")
    assert not store.messages(other, "C07")


def test_concurrent_decisions_execute_at_most_once(store, context):
    gateway = ApprovalGateway(store)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: gateway.decide(context, proposal, True), range(2)))
    assert all(x["state"] == "executada" for x in results)
    assert len(store.state(context)["receipts"]) == 1


def test_concurrent_yes_and_no_have_single_winner(store, context):
    gateway = ApprovalGateway(store)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda choice: gateway.decide(context, proposal, choice), [True, False]))
    assert results[0]["state"] == results[1]["state"]
    assert len(store.state(context)["receipts"]) == (1 if results[0]["state"] == "executada" else 0)


def test_survives_recreated_store_without_reexecution(store, context):
    gateway = ApprovalGateway(store)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    other = Store(str(store.engine.url))
    assert other.proposals(context, "C07")[0]["state"] == "pendente"
    ApprovalGateway(other).decide(context, proposal, True)
    assert gateway.decide(context, proposal, True)["state"] == "executada"
    assert len(store.state(context)["receipts"]) == 1
    other.engine.dispose()


@pytest.mark.parametrize("quantity", ["0", "-1", "NaN", "Infinity", "1.0001"])
def test_invalid_quantities_rejected_by_contract(store, context, quantity):
    with pytest.raises(ValidationError):
        receipt_request(store, context, quantity=quantity)


def test_excess_closed_item_and_mismatch_blocked(store, context):
    gateway = ApprovalGateway(store)
    for code, qty in [("C03", "35"), ("C04", "1")]:
        with pytest.raises(PolicyError):
            gateway.propose(context, code, receipt_request(store, context, code, qty))
    request = receipt_request(store, context)
    request.parameters.unit = "KG"
    request.confirmation_phrase = canonical_phrase(request, "C07")
    with pytest.raises(PolicyError):
        gateway.propose(context, "C07", request)


def test_phrase_and_ticket_must_match(store, context):
    gateway = ApprovalGateway(store)
    request = receipt_request(store, context)
    request.confirmation_phrase = "Posso alterar uma coisa diferente?"
    with pytest.raises(PolicyError):
        gateway.propose(context, "C07", request)
    with pytest.raises(PolicyError):
        gateway.propose(context, "C08", receipt_request(store, context))


def test_forbidden_operations_and_text_approval_rejected(store, context):
    with pytest.raises(ValidationError):
        TypeAdapter(ActionRequest).validate_python({"operation": "execute_sql", "parameters": {"sql": "DELETE"},
                                                  "confirmation_phrase": "Pode executar tudo"})
    gateway = ApprovalGateway(store)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    with pytest.raises(PolicyError):
        gateway.decide(context, proposal, "sim")


def test_execution_failure_rolls_back_business_and_records_failure(store, context, monkeypatch):
    gateway = ApprovalGateway(store)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    before = store.state(context)

    def fail(workspace, proposal, request):
        changed = deepcopy(workspace.data)
        changed["orders"]["4500001007/10"]["received"] = "999"
        workspace.data = changed
        raise RuntimeError("Falha controlada")

    monkeypatch.setattr(gateway, "_execute", fail)
    assert gateway.decide(context, proposal, True)["state"] == "falhou"
    assert store.state(context) == before
    assert gateway.decide(context, proposal, True)["state"] == "falhou"


def test_status_change_requires_own_approval(store, context):
    gateway = ApprovalGateway(store)
    request = StatusRequest(operation="atualizar_status_chamado", parameters={"status": "em_validacao_humana"},
                            confirmation_phrase="Posso alterar o chamado C06 para em validação humana?")
    proposal = gateway.propose(context, "C06", request)
    assert store.state(context)["tickets"]["C06"]["status"] == "aberto"
    gateway.decide(context, proposal, True)
    assert store.state(context)["tickets"]["C06"]["status"] == "em_validacao_humana"


def test_duplicate_proposal_reuses_pending_card(store, context):
    gateway = ApprovalGateway(store)
    request = receipt_request(store, context)
    assert gateway.propose(context, "C07", request) == gateway.propose(context, "C07", request)
    assert len(store.proposals(context, "C07")) == 1


def test_gateway_revalidates_mutated_contract(store, context):
    request = receipt_request(store, context)
    request.parameters.quantity = Decimal("-1")
    with pytest.raises(ValidationError):
        ApprovalGateway(store).propose(context, "C07", request)
    assert not store.proposals(context, "C07")


@pytest.mark.parametrize("field", ["expires_at", "created_at", "ticket"])
def test_authorization_envelope_rejects_changed_metadata(store, context, field):
    gateway = ApprovalGateway(store)
    proposal_id = gateway.propose(context, "C07", receipt_request(store, context))
    with store.transaction() as db:
        proposal = db.get(Proposal, proposal_id)
        setattr(proposal, field, "C05" if field == "ticket" else (utcnow() + timedelta(hours=1)).isoformat())
    assert gateway.decide(context, proposal_id, True)["state"] == "invalidada"
    assert not store.state(context)["receipts"]


def test_copied_proposal_cannot_reuse_original_authorization(store, context):
    gateway = ApprovalGateway(store)
    original = gateway.propose(context, "C07", receipt_request(store, context))
    copied_id = new_id()
    with store.transaction() as db:
        source = db.get(Proposal, original)
        db.add(Proposal(id=copied_id, workspace_id=source.workspace_id, ticket=source.ticket,
                        payload=deepcopy(source.payload), integrity=source.integrity, state="pendente",
                        created_at=source.created_at, expires_at=source.expires_at, result={}))
    assert gateway.decide(context, copied_id, True)["state"] == "invalidada"
    assert not store.state(context)["receipts"]


@pytest.mark.parametrize("target", ["ticket", "order"])
def test_unversioned_data_change_invalidates_consent(store, context, target):
    gateway = ApprovalGateway(store)
    proposal_id = gateway.propose(context, "C07", receipt_request(store, context))
    with store.transaction() as db:
        workspace = db.get(Workspace, context.workspace_id)
        data = deepcopy(workspace.data)
        if target == "ticket":
            data["tickets"]["C07"]["description"] = "Solicitação alterada depois da proposta"
        else:
            data["orders"]["4500001007/10"]["material"] = "OUTRO-MATERIAL"
        workspace.data = data
    assert gateway.decide(context, proposal_id, True)["state"] == "invalidada"
    assert not store.state(context)["receipts"]


def test_unrelated_ticket_does_not_invalidate_consent(store, context):
    gateway = ApprovalGateway(store)
    receipt = gateway.propose(context, "C07", receipt_request(store, context))
    status = StatusRequest(operation="atualizar_status_chamado", parameters={"status": "resolvido"},
                           confirmation_phrase="Posso alterar o chamado C01 para resolvido?")
    other = gateway.propose(context, "C01", status)
    gateway.decide(context, other, True)
    assert gateway.decide(context, receipt, True)["state"] == "executada"


def test_expired_proposal_is_not_reused_when_reproposed(store, context):
    gateway = ApprovalGateway(store)
    now = utcnow()
    request = receipt_request(store, context)
    first = gateway.propose(context, "C07", request, now)
    second = gateway.propose(context, "C07", request, now + timedelta(minutes=16))
    assert first != second
    assert gateway.decide(context, first, True, now + timedelta(minutes=16))["state"] == "expirada"


def test_legacy_pending_proposal_requires_new_consent(store, context):
    from sap_assistant.approvals import digest
    gateway = ApprovalGateway(store)
    proposal_id = gateway.propose(context, "C07", receipt_request(store, context))
    with store.transaction() as db:
        row = db.get(Proposal, proposal_id)
        payload = {key: value for key, value in row.payload.items() if key != "envelope"}
        row.payload, row.integrity = payload, digest(payload)
    assert gateway.decide(context, proposal_id, True)["state"] == "invalidada"
    assert not store.state(context)["receipts"]

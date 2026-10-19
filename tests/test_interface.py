"""A interface React tem testes próprios; este arquivo testa sua fronteira HTTP."""
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
from threading import Event

from fastapi.testclient import TestClient
import pytest

from sap_assistant.api import create_app, COOKIE
from sap_assistant.approvals import ApprovalGateway
from sap_assistant.config import Settings
from sap_assistant.database import SessionContext, Workspace, new_id, utcnow
from sap_assistant.retrieval import Retriever
from sap_assistant.service import AssistantService
from conftest import ControlledProvider, ReceiptProvider, receipt_request

HEADERS = {"X-Requested-With": "sap-assistant"}


@pytest.fixture
def web(store):
    provider = ControlledProvider()
    service = AssistantService(store, Retriever(store, provider), provider)
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="local")
    gateway = ApprovalGateway(store)
    app = create_app(settings, (store, service, gateway))
    with TestClient(app) as client:
        client.headers.update(HEADERS)
        yield client, store, service, gateway


def login(client):
    assert client.post("/api/session", json={}).status_code == 200
    workspace, token = client.cookies[COOKIE].split(".", 1)
    return SessionContext(workspace, token)


def send(client, chat="initial", text="Explique recebimento com pedido.", ticket=None, submission=None):
    response = client.post(f"/api/chats/{chat}/messages", json={"message": text,
        "ticket_id": ticket, "submission_id": submission or new_id()})
    assert response.status_code == 200
    return [json.loads(line) for line in response.text.splitlines() if line]


def test_session_cookie_and_public_configuration(web):
    client, _, _, _ = web
    assert client.get("/api/config").json() == {"requires_access_code": False}
    assert client.get("/api/session").status_code == 401
    context = login(client)
    assert context.token not in client.get("/api/session").text
    assert client.get("/api/session").json() == {"authenticated": True}
    assert "HttpOnly" in client.post("/api/session", json={}).headers["set-cookie"]
    assert client.get("/api/chats/initial").headers["cache-control"] == "no-store"


def test_access_gate_precedes_workspace_creation(store):
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="local", access_code="test-access-code")
    provider = ControlledProvider()
    services = (store, AssistantService(store, Retriever(store, provider), provider), ApprovalGateway(store))
    with TestClient(create_app(settings, services)) as client:
        client.headers.update(HEADERS)
        assert client.post("/api/session", json={"access_code": "wrong"}).status_code == 401
        assert COOKIE not in client.cookies
        assert client.post("/api/session", json={"access_code": "test-access-code"}).status_code == 200


def test_csrf_and_cross_origin_requests_are_rejected(web):
    client, _, _, _ = web
    assert client.post("/api/session", json={}, headers={"X-Requested-With": "wrong"}).status_code == 403
    assert client.post("/api/session", json={}, headers={"Origin": "https://external.invalid"}).status_code == 403
    assert client.post("/api/session", json={}, headers={"Origin": "http://testserver"}).status_code == 200


def test_snapshot_has_cases_without_messages_and_no_secrets(web):
    client, _, _, _ = web
    context = login(client)
    response = client.get("/api/chats/initial")
    view = response.json()
    assert len(view["cases"]) == 8 and not view["messages"] and not view["proposals"]
    assert view["cases"][4]["support"]["application"] is None
    assert context.token not in response.text and context.workspace_id not in response.text
    assert "database_url" not in response.text and "api_key" not in response.text


def test_stream_has_observable_progress_and_only_validated_answer_in_snapshot(web):
    client, _, _, _ = web
    login(client)
    events = send(client)
    assert events[-1] == {"type": "completed", "state": "completed"}
    assert any(item["type"] == "progress" for item in events)
    assert not any("facts" in item or "content" in item for item in events)
    message = client.get("/api/chats/initial").json()["messages"][-1]
    assert message["details"]["sources"] and message["details"]["steps"]
    assert "evidence" not in message["details"] and "provider" not in message["details"]
    assert not any("content" in source for source in message["details"]["sources"])


def test_new_chat_preserves_business_and_excludes_history_and_proposals(web):
    client, store, _, gateway = web
    context = login(client)
    send(client)
    proposal = gateway.propose(context, "C07", receipt_request(store, context))
    before = store.state(context)
    chat = client.post("/api/chats", json={}).json()["chat_id"]
    assert not client.get(f"/api/chats/{chat}").json()["messages"]
    assert not client.get(f"/api/chats/{chat}").json()["proposals"]
    send(client, chat=chat)
    assert len(client.get(f"/api/chats/{chat}").json()["messages"]) == 2
    assert len(client.get("/api/chats/initial").json()["messages"]) == 2
    assert client.post(f"/api/chats/{chat}/proposals/{proposal}/decision", json={"approve": True}).status_code == 401
    assert store.state(context) == before


@pytest.mark.parametrize("approve,expected", [(True,"executada"), (False,"recusada")])
def test_human_decision_requires_specific_proposal_and_is_idempotent(web, approve, expected):
    client, store, service, _ = web
    context = login(client)
    provider = ReceiptProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    send(client, ticket="C07", text="Registre 10 UN em 2026-10-18.")
    view = client.get("/api/chats/initial").json()
    proposal = view["proposals"][0]
    assert proposal["state"] == "pendente" and not store.state(context)["receipts"]
    assert "snapshot" not in proposal and "payload" not in proposal
    url = f"/api/chats/initial/proposals/{proposal['id']}/decision"
    assert client.post(url, json={"approve": "sim"}).status_code == 422
    assert client.post(url, json={"approve": approve}).json()["state"] == expected
    client.post(url, json={"approve": True})
    assert len(store.state(context)["receipts"]) == (1 if approve else 0)


def test_wrong_session_cannot_read_or_decide_other_session(web):
    client, store, _, gateway = web
    first = login(client)
    proposal = gateway.propose(first, "C07", receipt_request(store, first))
    login(client)
    assert not client.get("/api/chats/initial").json()["proposals"]
    assert client.post(f"/api/chats/initial/proposals/{proposal}/decision", json={"approve": True}).status_code == 401
    assert not store.state(first)["receipts"]


def test_submission_replay_does_not_call_model_again(web):
    client, _, service, _ = web
    login(client)
    submission = new_id()
    send(client, submission=submission)
    send(client, submission=submission)
    assert service.provider.calls == 1
    assert len(client.get("/api/chats/initial").json()["messages"]) == 2


def test_bad_input_and_forged_cookie_are_safe(web):
    client, _, _, _ = web
    login(client)
    assert client.get("/api/chats/not-a-uuid").status_code == 422
    assert client.post("/api/chats/initial/messages", json={"message":"x", "submission_id":"bad"}).status_code == 422
    assert client.post("/api/chats/initial/messages", json={"message":" ", "submission_id":new_id()}).status_code == 422
    client.cookies.set(COOKIE, "not-a-valid-session", path="/api")
    assert client.get("/api/chats/initial").status_code == 401


def test_missing_build_does_not_show_stack_trace(web):
    client, _, _, _ = web
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "Traceback" not in response.text


def test_compiled_interface_and_assets_are_served_by_same_app(web, tmp_path):
    _, store, service, gateway = web
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text('<html lang="pt-BR"><div id="root"></div></html>', encoding="utf-8")
    (tmp_path / "assets/main.js").write_text('console.log("interface")', encoding="utf-8")
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="local")
    with TestClient(create_app(settings, (store, service, gateway), tmp_path)) as client:
        assert 'lang="pt-BR"' in client.get("/").text
        assert client.get("/assets/main.js").status_code == 200
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.get("/assets/../../.env").status_code == 404
    with TestClient(create_app(settings, (store, service, gateway), tmp_path / "unbuilt")) as client:
        assert client.get("/").status_code == 503


def test_api_stays_responsive_and_rejects_concurrent_analysis_in_same_session(web, monkeypatch):
    client, _, service, _ = web
    login(client)
    entered, release = Event(), Event()
    original = service.provider.analyze

    def blocked(*args):
        entered.set()
        assert release.wait(timeout=10)
        return original(*args)

    monkeypatch.setattr(service.provider, "analyze", blocked)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(send, client)
        try:
            assert entered.wait(timeout=10)
            assert client.get("/api/health").json() == {"status": "ok"}
            assert len(client.get("/api/chats/initial").json()["cases"]) == 8
            duplicate = client.post("/api/chats/initial/messages", json={"message": "Outra pergunta",
                "submission_id": new_id()})
            assert duplicate.status_code == 409
        finally:
            release.set()
        assert future.result(timeout=10)[-1]["type"] == "completed"
    assert not client.app.state.active


@pytest.mark.parametrize("change,expected", [("expired", "expirada"), ("stale", "invalidada")])
def test_api_decision_rechecks_expiry_and_current_business_data(web, change, expected):
    client, store, _, gateway = web
    context = login(client)
    when = utcnow() - timedelta(minutes=16) if change == "expired" else utcnow()
    proposal = gateway.propose(context, "C07", receipt_request(store, context), now=when)
    if change == "stale":
        with store.transaction() as db:
            row = db.get(Workspace, context.workspace_id)
            state = deepcopy(row.data)
            state["orders"]["4500001007/10"]["received"] = "5"
            row.data = state
    before = store.state(context)
    response = client.post(f"/api/chats/initial/proposals/{proposal}/decision", json={"approve": True})
    assert response.status_code == 200 and response.json()["state"] == expected
    assert store.state(context) == before and not before["receipts"]


def test_http_correction_preparation_cannot_execute_or_change_operation(web):
    from test_corrections import CorrectionProvider
    client, store, service, _ = web
    context = login(client)
    provider = CorrectionProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    send(client, ticket="C03", text="como resolvo isso?")
    message = client.get("/api/chats/initial").json()["messages"][-1]
    assert message["correction"]["max_quantity"] == "20"
    url = f"/api/chats/initial/messages/{message['id']}/correction"
    assert client.post(url, json={"quantity": "20"}).status_code == 409
    assert client.post(url, json={"quantity": "35", "posting_date": "2026-10-18"}).status_code == 409
    assert client.post(url, json={"operation": "execute_sql"}).status_code == 422
    before = store.state(context)
    result = client.post(url, json={"quantity": "20", "posting_date": "2026-10-18"})
    assert result.status_code == 200 and store.state(context) == before
    proposal = result.json()["proposal_id"]
    assert client.get("/api/chats/initial").json()["messages"][-1]["proposal_id"] == proposal
    assert client.post(f"/api/chats/initial/proposals/{proposal}/decision", json={"approve": True}).json()["state"] == "executada"
    assert len(store.state(context)["receipts"]) == 1

"""Verifica API HTTP com Supabase/OpenRouter reais; consome créditos.

Decisões simuladas pelo teste em sessões fictícias próprias, sem consentimento
humano real. Não modifica o corpus nem tabelas externas. Não é revisão visual.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import text

from sap_assistant import runtime
from sap_assistant.api import COOKIE, create_app
from sap_assistant.config import Settings
from sap_assistant.database import SessionContext, new_id, utcnow

ROOT = Path(__file__).resolve().parents[1]


def outside_catalog(store):
    with store.engine.connect() as db:
        rows = [list(row) for row in db.execute(text(
            "SELECT n.nspname,c.relname,c.relkind,a.attname,a.atttypid,a.attnotnull "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped "
            "WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname NOT IN ('information_schema','sap_chamados_ai') "
            "ORDER BY n.nspname,c.relname,a.attnum"))]
    return hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()


def verify_web_services(settings, services, on_check=None):
    store, service, _ = services
    checks = []
    before_catalog = outside_catalog(store)

    def check(name, callback):
        started = time.perf_counter()
        try:
            item = {"check": name, "passed": True, "details": callback() or {}}
        except Exception as exc:
            item = {"check": name, "passed": False, "error_type": type(exc).__name__}
        item["seconds"] = round(time.perf_counter() - started, 3)
        checks.append(item)
        if on_check:
            on_check(item)
        return item["passed"]

    with TestClient(create_app(settings, services), base_url="https://testserver") as client:
        client.headers["X-Requested-With"] = "sap-assistant"
        assert client.post("/api/session", json={"access_code": settings.access_code or ""}).status_code == 200
        workspace, token = client.cookies[COOKIE].split(".", 1)
        context = SessionContext(workspace, token)
        initial = store.state(context)
        scope = {"chat": "initial"}

        def snapshot():
            response = client.get(f"/api/chats/{scope['chat']}")
            assert response.status_code == 200
            assert token not in response.text and settings.api_key not in response.text
            return response.json()

        def ask(message, ticket=None):
            response = client.post(f"/api/chats/{scope['chat']}/messages", json={
                "message": message, "ticket_id": ticket, "submission_id": new_id()})
            assert response.status_code == 200
            events = [json.loads(line) for line in response.text.splitlines() if line]
            assert events[-1] == {"type": "completed", "state": "completed"}
            assert any(x["type"] == "progress" for x in events)
            assert not any("content" in x or "facts" in x for x in events)
            message = snapshot()["messages"][-1]
            assert not message["error"]
            return message

        def general():
            assert len(snapshot()["cases"]) == 8 and not snapshot()["messages"]
            answer = ask("O que é recebimento de mercadorias com referência ao pedido de compra?")
            sources = answer["details"]["sources"]
            assert sources and all("content" not in item for item in sources)
            assert all(item["url"].startswith("https://") for item in sources)
            assert not answer["attachment"] and not snapshot()["proposals"]
            assert store.state(context) == initial
            return {"source_urls": [item["url"] for item in sources], "business_unchanged": True,
                    "latency_ms": answer["details"]["latency_ms"]}

        def insufficient():
            answer = ask("Qual a causa e correção do erro ZMM_9999 no recebimento?", "C06")
            assert "informações suficientes" in answer["content"]
            assert not answer["details"]["hypotheses"] and not snapshot()["proposals"]
            assert store.state(context) == initial
            return {"abstention": True, "no_proposal": True}

        def approval():
            ask(initial["tickets"]["C07"]["description"], "C07")
            proposal = next(x for x in snapshot()["proposals"] if x["ticket"] == "C07")
            scope["old_proposal"] = proposal["id"]
            assert proposal["state"] == "pendente" and store.state(context) == initial
            scope["old_chat"] = scope["chat"]
            scope["chat"] = client.post("/api/chats", json={}).json()["chat_id"]
            assert not snapshot()["messages"] and not snapshot()["proposals"]
            wrong = client.post(f"/api/chats/{scope['chat']}/proposals/{proposal['id']}/decision", json={"approve": True})
            assert wrong.status_code == 401 and store.state(context) == initial
            scope["chat"] = scope["old_chat"]
            url = f"/api/chats/initial/proposals/{proposal['id']}/decision"
            assert client.post(url, json={"approve": True}).json()["state"] == "executada"
            assert client.post(url, json={"approve": True}).json()["state"] == "executada"
            assert len(store.state(context)["receipts"]) == 1
            return {"no_write_before_decision": True, "wrong_chat_rejected": True, "receipts_after_double_click": 1}

        def refusal():
            ask(initial["tickets"]["C08"]["description"], "C08")
            proposal = next(x for x in snapshot()["proposals"] if x["ticket"] == "C08")
            before = store.state(context)
            url = f"/api/chats/initial/proposals/{proposal['id']}/decision"
            assert client.post(url, json={"approve": False}).json()["state"] == "recusada"
            assert client.post(url, json={"approve": True}).json()["state"] == "recusada"
            assert store.state(context) == before
            return {"refusal_unchanged": True, "later_yes_does_not_override": True}

        def new_chat():
            old = snapshot()
            before = store.state(context)
            scope["chat"] = client.post("/api/chats", json={}).json()["chat_id"]
            current = snapshot()
            assert not current["messages"] and not current["proposals"]
            assert len(current["cases"]) == 8 and store.state(context) == before
            assert len(client.get("/api/chats/initial").json()["messages"]) == len(old["messages"])
            return {"independent_conversation": True, "history_and_business_preserved": True}

        for name, function in [("RAG geral: fontes oficiais sem conteúdo bruto", general),
                               ("RAG insuficiente: abstinência sem proposta", insufficient),
                               ("HITL: contexto exato e Sim idempotente", approval),
                               ("HITL: Não impede alteração", refusal),
                               ("Novo chat preserva histórico e negócio", new_chat)]:
            if not check(name, function):
                break
    after_catalog = outside_catalog(store)
    return {"checks": checks, "external_catalog_unchanged": before_catalog == after_catalog,
            "external_catalog_hashes": {"before": before_catalog, "after": after_catalog},
            "passed": len(checks) == 5 and all(item["passed"] for item in checks) and before_catalog == after_catalog}


def main():
    settings = Settings.load()
    services = runtime.create_runtime(settings)
    calls = {}

    def count(request):
        endpoint = request.url.path.rsplit("/", 1)[-1]
        calls[endpoint] = calls.get(endpoint, 0) + 1

    services[1].provider.client.event_hooks["request"].append(count)
    report = {"date": utcnow().isoformat(), "mode": __doc__, "api_calls": calls}
    try:
        report.update(verify_web_services(settings, services, lambda item: print(
            json.dumps({"check": item["check"], "passed": item["passed"]}, ensure_ascii=False), flush=True)))
    except Exception as exc:
        report.update(passed=False, setup_error_type=type(exc).__name__)
    finally:
        services[1].provider.client.close()
        services[0].engine.dispose()
        (ROOT / "evidencias/verificacao-web-api.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

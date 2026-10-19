"""Reproduz C03 e HITL via HTTP com Supabase/OpenRouter reais. Consome créditos.

Somente workspace fictício próprio. Decisões simuladas pelo harness, não por uma
pessoa. Não altera corpus nem objetos externos e não executa SAP real.
"""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from sap_assistant.api import COOKIE, create_app
from sap_assistant.config import Settings
from sap_assistant.database import SessionContext, new_id, utcnow
from verify_web_live import outside_catalog

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings.load()
    report = {"date": utcnow().isoformat(), "mode": __doc__, "checks": [], "api_calls": {}}
    path = ROOT / "evidencias/verificacao-correcoes-c03.json"

    def save():
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def check(name, callback):
        started = time.perf_counter()
        try:
            result = {"check": name, "passed": True, "details": callback() or {}}
        except Exception as exc:
            result = {"check": name, "passed": False, "error_type": type(exc).__name__}
        result["seconds"] = round(time.perf_counter() - started, 3)
        report["checks"].append(result)
        save()
        print(json.dumps({"check": name, "passed": result["passed"]}, ensure_ascii=False), flush=True)
        return result["passed"]

    try:
        with TestClient(create_app(settings), base_url="https://testserver") as client:
            client.headers["X-Requested-With"] = "sap-assistant"
            store, assistant, _ = client.app.state.services
            before_catalog = outside_catalog(store)

            def count(request):
                endpoint = request.url.path.rsplit("/", 1)[-1]
                calls = report["api_calls"]
                calls[endpoint] = calls.get(endpoint, 0) + 1

            assistant.provider.client.event_hooks["request"].append(count)
            assert client.post("/api/session", json={"access_code": settings.access_code or ""}).status_code == 200
            workspace, token = client.cookies[COOKIE].split(".", 1)
            context = SessionContext(workspace, token)
            initial = store.state(context)
            scope = {"chat": "initial"}

            def snapshot():
                return client.get(f"/api/chats/{scope['chat']}").json()

            def ask(text):
                response = client.post(f"/api/chats/{scope['chat']}/messages", json={"message": text,
                    "ticket_id": "C03", "submission_id": new_id()})
                assert response.status_code == 200
                events = [json.loads(line) for line in response.text.splitlines()]
                assert events[-1] == {"type": "completed", "state": "completed"}
                message = snapshot()["messages"][-1]
                assert not message["error"]
                return message

            def first():
                message = ask("como resolvo isso?")
                assert message["correction"]["operation"] == "registrar_recebimento_simulado"
                assert message["correction"]["max_quantity"] == "20"
                assert not message["proposal_id"] and store.state(context) == initial
                return {"preparation_available": True, "missing_quantity_and_date_not_invented": True,
                        "sources": message["details"]["sources"], "policies": message["details"]["policies"]}

            def followup():
                message = ask("altere para mim")
                assert message["correction"]["operation"] == "registrar_recebimento_simulado"
                assert not message["proposal_id"] and not snapshot()["proposals"]
                scope["message"] = message["id"]
                assert store.state(context) == initial
                return {"receipt_context_preserved": True, "no_status_substitution": True}

            def prepare_and_refuse():
                url = f"/api/chats/initial/messages/{scope['message']}/correction"
                assert client.post(url, json={"quantity": "35", "posting_date": "2026-10-18"}).status_code == 409
                assert client.post(url, json={"quantity": "20"}).status_code == 409
                data = {"quantity": "20", "posting_date": "2026-10-18"}
                result = client.post(url, json=data)
                assert result.status_code == 200
                proposal = result.json()["proposal_id"]
                assert client.post(url, json=data).json()["proposal_id"] == proposal
                assert store.state(context) == initial
                card = snapshot()["proposals"][0]
                assert card["state"] == "pendente" and card["effect"]["quantity"] == "20"
                decision = f"/api/chats/initial/proposals/{proposal}/decision"
                assert client.post(decision, json={"approve": False}).json()["state"] == "recusada"
                assert client.post(decision, json={"approve": True}).json()["state"] == "recusada"
                assert store.state(context) == initial
                return {"invalid_and_incomplete_rejected": True, "prepare_is_idempotent_and_not_execution": True,
                        "refusal_preserves_business": True}

            def complete_and_approve():
                scope["chat"] = client.post("/api/chats", json={}).json()["chat_id"]
                message = ask("Corrija o recebimento: registre 10 UN no pedido 4500001003, item 10, em 2026-10-18.")
                assert message["proposal_id"]
                card = snapshot()["proposals"][0]
                assert card["effect"]["quantity"] == "10" and card["state"] == "pendente"
                assert store.state(context) == initial
                decision = f"/api/chats/{scope['chat']}/proposals/{card['id']}/decision"
                assert client.post(decision, json={"approve": True}).json()["state"] == "executada"
                assert client.post(decision, json={"approve": True}).json()["state"] == "executada"
                assert len(store.state(context)["receipts"]) == 1
                assert store.state(context)["tickets"]["C03"]["status"] == "aberto"
                return {"complete_correction_offers_approval": True, "double_click_one_receipt": True,
                        "ticket_status_not_changed": True}

            for name, callback in [("C03: como resolvo oferece correção preenchível", first),
                                   ("C03: altere para mim mantém recebimento", followup),
                                   ("C03: revisão, parâmetros e Não", prepare_and_refuse),
                                   ("C03: dados completos oferecem Sim e execução única", complete_and_approve)]:
                if not check(name, callback):
                    break
            report["external_catalog_unchanged"] = before_catalog == outside_catalog(store)
    except Exception as exc:
        report["setup_error_type"] = type(exc).__name__
    report["passed"] = (len(report["checks"]) == 4 and all(item["passed"] for item in report["checks"])
                        and report.get("external_catalog_unchanged") and "setup_error_type" not in report)
    save()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

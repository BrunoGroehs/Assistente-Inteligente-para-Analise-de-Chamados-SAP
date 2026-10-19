"""Mede API com Supabase real; --with-analysis consome créditos OpenRouter.

Não mede renderização ou latência de navegador. Relatório histórico preservado.
"""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import event

from sap_assistant import runtime
from sap_assistant.api import create_app
from sap_assistant.config import Settings
from sap_assistant.database import new_id

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-analysis", action="store_true")
    args = parser.parse_args()
    settings = Settings.load()
    started = time.perf_counter()
    services = runtime.create_runtime(settings)
    report = {"method": __doc__, "runtime_initialization_seconds": round(time.perf_counter() - started, 3),
              "measurements": [], "api_calls": {}}
    statements = []

    @event.listens_for(services[0].engine, "before_cursor_execute")
    def count_sql(*_):
        statements.append(1)

    def count_api(request):
        key = request.url.path.rsplit("/", 1)[-1]
        calls = report["api_calls"]
        calls[key] = calls.get(key, 0) + 1

    services[1].provider.client.event_hooks["request"].append(count_api)

    def measure(name, callback):
        before, start = len(statements), time.perf_counter()
        response = callback()
        assert response.status_code == 200
        report["measurements"].append({"request": name, "seconds": round(time.perf_counter() - start, 3),
                                       "sql_statements": len(statements) - before})
        return response

    try:
        with TestClient(create_app(settings, services), base_url="https://testserver") as client:
            client.headers["X-Requested-With"] = "sap-assistant"
            measure("criar_sessao", lambda: client.post("/api/session", json={"access_code": settings.access_code or ""}))
            measure("carregar_conversa", lambda: client.get("/api/chats/initial"))
            measure("atualizacao_explicita", lambda: client.get("/api/chats/initial"))
            measure("novo_chat", lambda: client.post("/api/chats", json={}))
            assert not report["api_calls"]
            if args.with_analysis:
                response = measure("analise_com_api", lambda: client.post("/api/chats/initial/messages", json={
                    "message": "O que é recebimento com referência ao pedido de compra?", "submission_id": new_id()}))
                assert json.loads(response.text.splitlines()[-1])["type"] == "completed"
        report["passed"] = True
    except Exception as exc:
        report.update(passed=False, error_type=type(exc).__name__)
    finally:
        services[1].provider.client.close()
        services[0].engine.dispose()
        (ROOT / "evidencias/desempenho-api-web.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

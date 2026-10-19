"""Mede interações com Supabase real; --with-analysis também consome OpenRouter.

AppTest não mede renderização em navegador ou latência até o computador do usuário.
Somente dados fictícios de uma sessão nova; nenhuma tabela externa é alterada.
"""
import argparse
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import event
import streamlit as st
from streamlit.testing.v1 import AppTest

from sap_assistant import runtime
from sap_assistant.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-analysis", action="store_true")
    args = parser.parse_args()
    settings = Settings.load()
    started = time.perf_counter()
    services = runtime.create_runtime(settings)
    initialization = round(time.perf_counter() - started, 3)
    store, assistant, _ = services
    sql_count, api_calls = [], {}

    @event.listens_for(store.engine, "before_cursor_execute")
    def count(*_):
        sql_count.append(1)

    def instrument(request):
        key = request.url.path.rsplit("/", 1)[-1]
        api_calls[key] = api_calls.get(key, 0) + 1

    assistant.provider.client.event_hooks["request"].append(instrument)
    measurements = []
    report = {"phase": "depois", "runtime_initialization_seconds": initialization,
              "measurements": measurements, "api_calls": api_calls,
              "method": "AppTest com Supabase real; não é revisão visual nem SLA"}
    path = ROOT / "evidencias/desempenho-interface-depois.json"

    def measure(name, callback, expect_no_sql=False):
        before = len(sql_count)
        start = time.perf_counter()
        callback()
        assert not app.exception and not app.error
        statements = len(sql_count) - before
        measurements.append({"interaction": name, "seconds": round(time.perf_counter() - start, 3),
                             "sql_statements": statements})
        if expect_no_sql:
            assert statements == 0

    def click(label):
        next(x for x in app.button if x.label == label).click().run(timeout=180)

    st.cache_resource.clear()
    try:
        with patch.object(runtime, "create_runtime", lambda _: services):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
            if settings.access_code:
                app.session_state["access_granted"] = True
            measure("primeiro_carregamento", app.run)
            measure("rerun_sem_mudancas", app.run, True)
            measure("abrir_chamados", lambda: click("Chamados"), True)
            measure("selecionar_c07", lambda: app.selectbox(key="dialog_case").set_value("C07").run(), True)
            measure("ver_detalhes", lambda: click("Ver detalhes"), True)
            measure("anexar", lambda: click("Anexar ao chat"), True)
            measure("remover", lambda: click("Remover anexo"), True)
            assert not api_calls
            measure("atualizacao_explicita", lambda: click("Atualizar"))
            assert measurements[-1]["sql_statements"] == 3
            if args.with_analysis:
                context = app.session_state["context"]
                before = store.state(context)
                measure("pergunta_geral_com_api", lambda: app.chat_input[0].set_value(
                    "O que é recebimento de mercadorias com referência ao pedido de compra?").run(timeout=180))
                message = store.messages(context)[-1]
                assert not message["details"].get("error")
                assert message["details"]["analysis"]["action"] is None
                assert store.state(context) == before
                details = message["details"]
                report["analysis"] = {"latency_ms": details["latency_ms"], "steps": details["steps"],
                                      "references": details["analysis"]["references"]}
                measure("rerun_apos_resposta", app.run, True)
        report["passed"] = True
    except Exception as exc:
        report["passed"] = False
        report["error_type"] = type(exc).__name__  # Nunca gravar DSN ou payload bruto de erro.
    finally:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False), flush=True)
        st.cache_resource.clear()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

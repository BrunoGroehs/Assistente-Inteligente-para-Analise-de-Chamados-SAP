"""Chat único e anexos opcionais com Supabase/OpenRouter reais; consome créditos.

AppTest automatiza os cliques; não representa revisão visual ou consentimento de
uma pessoa. Cria uma sessão fictícia nova, sem alterar tabelas de outros projetos.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
import streamlit as st
from streamlit.testing.v1 import AppTest

from sap_assistant import runtime
from sap_assistant.config import Settings
from sap_assistant.database import GENERAL_CHAT, utcnow

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings.load()
    services = runtime.create_runtime(settings)
    store, service, _ = services
    calls = {}

    def instrument(request):
        endpoint = request.url.path.rsplit("/", 1)[-1]
        calls[endpoint] = calls.get(endpoint, 0) + 1

    service.provider.client.event_hooks["request"].append(instrument)
    report = {"date": utcnow().isoformat(), "mode": __doc__, "api_calls": calls, "checks": [],
              "chat_model": settings.chat_model, "embedding_model": settings.embedding_model,
              "prompt_version": (ROOT / "prompts/system.txt").read_text(encoding="utf-8").splitlines()[0]}
    path = ROOT / "evidencias/verificacao-anexos-chat.json"

    def save():
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def catalog():
        with store.engine.connect() as db:
            rows = [list(x) for x in db.execute(text(
                "SELECT n.nspname,c.relname,c.relkind,a.attname,a.atttypid,a.attnotnull "
                "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped "
                "WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname NOT IN ('information_schema','sap_chamados_ai') "
                "ORDER BY n.nspname,c.relname,a.attnum"))]
        return hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()

    def check(name, function):
        started = time.perf_counter()
        try:
            entry = {"check": name, "passed": True, "details": function() or {}}
        except Exception as exc:
            entry = {"check": name, "passed": False, "error_type": type(exc).__name__}
            # Só posição do harness: SQL/HTTP podem conter segredos em mensagens.
            import traceback
            local_frames = [frame for frame in traceback.extract_tb(exc.__traceback__) if frame.filename == __file__]
            entry["harness_line"] = local_frames[-1].lineno if local_frames else None
        entry["seconds"] = round(time.perf_counter() - started, 2)
        report["checks"].append(entry)
        save()
        print(json.dumps({"check": name, "passed": entry["passed"]}, ensure_ascii=False), flush=True)
        return entry["passed"]

    def click(label):
        next(x for x in app.button if x.label == label).click().run(timeout=180)
        assert not app.exception and not app.error

    def attach(key):
        click("Chamados")
        app.selectbox(key="dialog_case").set_value(key).run()
        click("Anexar ao chat")
        assert app.session_state["attached_case"] == key

    def ask(question):
        before = store.state(context)
        app.chat_input[0].set_value(question).run(timeout=180)
        assert not app.exception and not app.error
        assert store.state(context) == before
        return store.messages(context)[-1]["details"]

    def assert_general(details):
        assert details["attachment"] is None and details["analysis"]["action"] is None
        assert not any(x["id"] == "DATA" for x in details["evidence"])
        assert "4500001007" not in json.dumps(details["evidence"])
        official = {x["id"] for x in details["evidence"] if x.get("source_url")}
        assert official & set(details["analysis"]["references"])
        assert app.get("link_button")

    before_catalog = catalog()
    st.cache_resource.clear()
    try:
        with patch.object(runtime, "create_runtime", lambda _: services):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
            if settings.access_code:
                app.session_state["access_granted"] = True  # Login não é objeto deste teste.
            app.run()
            assert not app.exception and not app.error
            context = app.session_state["context"]

            def general():
                assert not app.sidebar.radio and app.session_state["attached_case"] is None
                details = ask("O que é o recebimento de mercadorias com referência a um pedido de compra?")
                assert_general(details)
                assert len(store.messages(context, GENERAL_CHAT)) == 2
                return {"no_sidebar_or_automatic_case": True, "general_rag_answer": details["analysis"]}

            def picker():
                before, before_calls = store.state(context), dict(calls)
                click("Chamados")
                assert len(app.dataframe[0].value) == 8
                app.text_input(key="dialog_search").set_value("4500001007").run()
                assert app.selectbox(key="dialog_case").value == "C07"
                click("Ver detalhes")
                assert any(x.value == "Sistema: QAS" for x in app.markdown)
                assert app.session_state["attached_case"] is None
                click("Cancelar")
                attach("C07")
                assert len(app.chat_message) == 2
                assert store.state(context) == before and calls == before_calls
                return {"all_cases_and_details": True, "attach_without_analysis_or_business_write": True}

            pending = {}

            def proposal():
                before = store.state(context)
                click("Analisar chamado")
                assert store.state(context) == before and app.chat_input[0].disabled
                item = store.proposals(context, "C07")[0]
                assert item["state"] == "pendente"
                pending.update(item)
                assert len(app.chat_message) == 4
                assert store.messages(context, "C07")[-1]["details"]["attachment"]["id"] == "C07"
                return {"proposal_pending": True, "one_timeline": True, "attachment_snapshot": True}

            def detach_and_ask():
                before, before_calls = store.state(context), dict(calls)
                attach("C08")
                assert not app.chat_input[0].disabled and not any(x.label == "Sim, autorizar" for x in app.button)
                click("Remover anexo")
                assert app.session_state["attached_case"] is None and not app.chat_input[0].disabled
                assert calls == before_calls and store.state(context) == before
                details = ask("Que documento é gerado no recebimento de mercadorias com pedido?")
                assert_general(details)
                assert len(app.chat_message) == 6
                assert store.proposals(context, "C07")[0]["id"] == pending["id"]
                assert store.proposals(context, "C07")[0]["state"] == "pendente"
                return {"detached_context_does_not_leak": True, "pending_preserved": True,
                        "new_general_answer": details["analysis"]}

            def reattach_and_approve():
                before_calls = dict(calls)
                click("Anexar SIM-C07")
                assert app.session_state["attached_case"] == "C07" and app.chat_input[0].disabled
                click("Sim, autorizar")
                after = store.state(context)
                assert len(after["receipts"]) == 1 and store.proposals(context, "C07")[0]["state"] == "executada"
                app.run()
                assert store.state(context) == after and calls == before_calls
                return {"original_proposal_only": True, "single_execution": True, "decision": "simulada pelo harness"}

            def unsupported():
                click("Remover anexo")
                details = ask("Qual a correção para ZMM_999 no recebimento?")
                answer = details["analysis"]
                assert "Não tenho informações suficientes" in answer["summary"]
                assert not answer["facts"] and not answer["hypotheses"] and answer["action"] is None
                assert details["attachment"] is None and len(store.messages(context)) == 8
                return {"insufficient_rag_still_blocks_general_answer": True}

            for name, function in [("Pergunta geral real sem chamado ou painel lateral", general),
                                   ("Lista, detalhes, cancelar e anexar sem análise automática", picker),
                                   ("C07 real: proposta ligada ao anexo e conversa única", proposal),
                                   ("Desanexar permite pergunta geral sem dados do chamado", detach_and_ask),
                                   ("Reanexar permite decidir a proposta original uma vez", reattach_and_approve),
                                   ("Sem evidência no RAG continua sem diagnóstico", unsupported)]:
                if not check(name, function):
                    break
    except Exception as exc:
        report["setup_error_type"] = type(exc).__name__
    finally:
        after_catalog = catalog()
        report["external_catalog_hashes"] = {"before": before_catalog, "after": after_catalog}
        report["external_catalog_unchanged"] = before_catalog == after_catalog
        report["passed"] = (len(report["checks"]) == 6 and all(x["passed"] for x in report["checks"])
                            and report["external_catalog_unchanged"] and "setup_error_type" not in report)
        save()
        st.cache_resource.clear()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

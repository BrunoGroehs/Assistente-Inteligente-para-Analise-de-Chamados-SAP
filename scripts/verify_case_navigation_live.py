"""Navegação e HITL com Supabase/OpenRouter reais; consome créditos.

Cliques são automatizados pelo AppTest. A seleção de linha é injetada no estado
nativo do componente, pois AppTest não oferece clique em tabela. Não é revisão
visual nem decisão de uma pessoa. Usa somente uma sessão fictícia nova.
"""
from copy import deepcopy
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
from sap_assistant.citations import message_citations, source_groups
from sap_assistant.config import Settings
from sap_assistant.database import utcnow

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings.load()
    services = runtime.create_runtime(settings)
    store, assistant, _ = services
    calls = {}

    def count(request):
        key = request.url.path.rsplit("/", 1)[-1]
        calls[key] = calls.get(key, 0) + 1

    assistant.provider.client.event_hooks["request"].append(count)
    report = {"date": utcnow().isoformat(), "mode": __doc__, "checks": [], "api_calls": calls,
              "chat_model": settings.chat_model, "embedding_model": settings.embedding_model,
              "case_profiles": "SIM-C01 a SIM-C08; nova sessão, sem migração de sessões existentes"}
    path = ROOT / "evidencias" / "verificacao-selecao-chamados.json"

    def save():
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def catalog():
        with store.engine.connect() as db:
            rows = [list(row) for row in db.execute(text(
                "SELECT n.nspname,c.relname,c.relkind,a.attname,a.atttypid,a.attnotnull "
                "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped "
                "WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname NOT IN ('information_schema','sap_chamados_ai') "
                "ORDER BY n.nspname,c.relname,a.attnum"))]
        return hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()

    def run(name, function):
        start = time.perf_counter()
        try:
            entry = {"check": name, "passed": True, "details": function() or {}}
        except Exception as exc:
            entry = {"check": name, "passed": False, "error_type": type(exc).__name__}
        entry["seconds"] = round(time.perf_counter() - start, 2)
        report["checks"].append(entry)
        save()
        print(json.dumps({"check": name, "passed": entry["passed"]}, ensure_ascii=False), flush=True)
        return entry["passed"]

    def click(label):
        next(x for x in app.button if x.label == label).click().run(timeout=180)
        assert not app.exception and not app.error

    def open_case(key):
        click("Chamados")
        app.selectbox(key="dialog_case").set_value(key).run()
        click("Abrir no chat")
        assert app.session_state["selected_ticket"] == key

    before_catalog = catalog()
    st.cache_resource.clear()
    try:
        # Substitui somente a fábrica de recursos; banco, gateway e provedor são reais.
        with patch.object(runtime, "create_runtime", lambda _: services):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
            if settings.access_code:
                app.session_state["access_granted"] = True  # autenticação não é objeto deste teste
            app.run()
            assert not app.exception and not app.error
            context = app.session_state["context"]
            initial = store.state(context)

            def selector():
                assert len(app.sidebar.radio[0].options) == 8
                click("Chamados")
                assert len(app.selectbox(key="dialog_case").options) == 8
                app.text_input(key="dialog_search").set_value("4500001007").run()
                assert app.selectbox(key="dialog_case").value == "C07"
                assert app.session_state["selected_ticket"] == "C01"
                click("Cancelar")
                assert not app.get("dialog") and app.session_state["selected_ticket"] == "C01"
                assert calls == {} and store.state(context) == initial
                return {"preview_and_cancel_read_only": True, "api_calls": 0}

            def listing():
                click("Lista completa")
                assert len(app.dataframe[0].value) == 8
                key = "case_table_" + "_".join(initial["tickets"])
                app.session_state[key] = {"selection": {"rows": [3], "columns": [], "cells": []}}
                app.run()
                assert app.selectbox(key="list_case").value == "C04"
                app.selectbox(key="list_priority").set_value("missing").run()
                assert app.selectbox(key="list_case").value == "C05"
                assert any(x.value == "Aplicativo: Não informado" for x in app.markdown)
                app.selectbox(key="list_priority").set_value("all").run()
                app.text_input(key="list_search").set_value("4500001007").run()
                assert app.selectbox(key="list_case").value == "C07"
                click("Abrir no chat")
                assert app.session_state["selected_ticket"] == "C07"
                assert store.state(context) == initial and calls == {}
                return {"table_selection_state": "linha 4 → C04", "priority_filter": "C05 sem prioridade",
                        "search_purchase_order": "4500001007 → C07", "no_automatic_analysis": True}

            pending = {}

            def propose():
                click("Analisar chamado")
                assert app.chat_input[0].disabled and store.state(context) == initial
                proposal = store.proposals(context, "C07")[0]
                assert proposal["state"] == "pendente" and proposal["payload"]["ticket"] == "C07"
                pending.update(proposal)
                message = store.messages(context, "C07")[-1]
                citations = message_citations(message["details"])
                urls = sorted({x.source_url for x in citations if x.source_url})
                retrieved_urls = sorted({x["url"] for x in source_groups(message["details"], cited=False)})
                assert set(urls + retrieved_urls) <= {x.proto.url for x in app.get("link_button")}
                assert urls or retrieved_urls
                assert not app.text and not app.get("dialog")
                return {"proposal_pending": True, "business_unchanged": True,
                        "cited_official_urls": urls, "consulted_official_urls": retrieved_urls,
                        "profile_in_real_model_context": True}

            def switch_pending():
                before_calls = deepcopy(calls)
                open_case("C08")
                assert not app.chat_message and not any(x.label == "Sim, autorizar" for x in app.button)
                click("Lista completa")
                app.text_input(key="list_search").set_value("").run()
                app.selectbox(key="list_case").set_value("C07").run()
                click("Abrir no chat")
                assert len(app.chat_message) == 2 and app.chat_input[0].disabled
                assert store.proposals(context, "C07")[0]["id"] == pending["id"]
                assert store.state(context) == initial and calls == before_calls
                return {"history_restored": True, "proposal_bound_to_original_case": True,
                        "no_business_change_or_api_call": True}

            def approve_once():
                before_calls = deepcopy(calls)
                click("Sim, autorizar")
                after = store.state(context)
                assert len(after["receipts"]) == 1
                assert store.proposals(context, "C07")[0]["state"] == "executada"
                app.run()
                assert store.state(context) == after and calls == before_calls
                assert not any(x.label == "Sim, autorizar" for x in app.button)
                return {"single_receipt": True, "rerun_idempotent": True, "decision": "simulada pelo teste"}

            def refuse():
                open_case("C08")
                before = store.state(context)
                click("Analisar chamado")
                assert store.state(context) == before and app.chat_input[0].disabled
                click("Não, recusar")
                assert store.state(context) == before
                assert store.proposals(context, "C08")[0]["state"] == "recusada"
                return {"refusal_preserves_business": True, "decision": "simulada pelo teste"}

            def incomplete():
                open_case("C05")
                assert initial["tickets"]["C05"]["support"]["priority"] is None
                before = store.state(context)
                click("Analisar chamado")
                answer = store.messages(context, "C05")[-1]["details"]["analysis"]
                assert answer["action"] is None and answer["confidence"] == "baixa"
                assert answer["missing_information"] and not store.proposals(context, "C05")
                assert store.state(context) == before
                return {"asks_for_missing_context": True, "no_proposal": True, "analysis": answer}

            def unknown_code():
                open_case("C06")
                before = store.state(context)
                click("Analisar chamado")
                answer = store.messages(context, "C06")[-1]["details"]["analysis"]
                assert "Não tenho informações suficientes" in answer["summary"]
                assert answer["action"] is None and not answer["facts"] and not answer["hypotheses"]
                assert store.state(context) == before and not store.proposals(context, "C06")
                return {"new_metadata_does_not_replace_rag": True, "analysis": answer}

            for name, check in [("Seletor: busca, prévia e cancelamento", selector),
                                ("Lista: seleção, filtros, detalhes e abertura", listing),
                                ("C07 real: metadados, fontes e proposta sem execução", propose),
                                ("Navegação preserva histórico e vínculo da aprovação", switch_pending),
                                ("Sim executa uma vez; rerun não repete", approve_once),
                                ("C08 real: Não preserva dados", refuse),
                                ("C05 real: campos ausentes e esclarecimento", incomplete),
                                ("C06 real: código ausente no RAG impede diagnóstico", unknown_code)]:
                if not run(name, check):
                    break
    except Exception as exc:
        report["setup_error_type"] = type(exc).__name__
    finally:
        after_catalog = catalog()
        report["external_catalog_hashes"] = {"before": before_catalog, "after": after_catalog}
        report["external_catalog_unchanged"] = before_catalog == after_catalog
        report["passed"] = (len(report["checks"]) == 8 and all(x["passed"] for x in report["checks"])
                            and report["external_catalog_unchanged"] and "setup_error_type" not in report)
        save()
        st.cache_resource.clear()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

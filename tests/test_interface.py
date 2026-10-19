from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from sap_assistant import runtime
from sap_assistant.approvals import ApprovalGateway
from sap_assistant.config import Settings
from sap_assistant.retrieval import Retriever
from sap_assistant.service import AssistantService
from conftest import ControlledProvider, ReceiptProvider

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def ui(store, monkeypatch):
    st.cache_resource.clear()
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", api_key="test-only", environment="local")
    monkeypatch.setattr(Settings, "load", classmethod(lambda cls, secrets=None: settings))
    provider = ControlledProvider()
    service = AssistantService(store, Retriever(store, provider), provider)
    monkeypatch.setattr(runtime, "create_runtime", lambda _: (store, service, ApprovalGateway(store)))
    yield store, service, settings
    st.cache_resource.clear()


def button(app, label):
    return next(x for x in app.button if x.label == label)


def test_configuration_without_credentials_shows_setup(monkeypatch):
    monkeypatch.setattr(Settings, "load", classmethod(lambda cls, secrets=None: Settings(database_url="")))
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.title[0].value == "Assistente SAP"
    assert app.info
    assert not app.chat_input


def test_database_failure_shows_safe_configuration_screen(ui, monkeypatch):
    st.cache_resource.clear()

    def unavailable(_):
        raise RuntimeError("postgresql://secret-user:secret-password@private.invalid/db")

    monkeypatch.setattr(runtime, "create_runtime", unavailable)
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception and not app.chat_input
    assert any("conectar ao banco" in x.value for x in app.info)
    assert not any("secret-user" in x.value or "secret-password" in x.value or "private.invalid" in x.value
                   for x in [*app.info, *app.markdown])


def test_clean_sidebar_chat_and_sources(ui):
    _, _, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert len(app.sidebar.radio[0].options) == 8
    assert len(app.chat_input) == 1
    assert not any(x.label.startswith("Sim") or x.label.startswith("Não") for x in app.button)
    button(app, "Analisar chamado").click().run()
    assert not app.exception
    assert len(app.chat_message) == 2
    assert any(x.label == "Fontes citadas" for x in app.expander)
    assert any(x.label == "Etapas do atendimento" for x in app.expander)
    app.sidebar.radio[0].set_value("C02").run()
    assert not app.chat_message
    app.sidebar.radio[0].set_value("C01").run()
    assert len(app.chat_message) == 2


def test_approval_button_executes_once_and_disappears(ui):
    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider = provider
    service.retriever = Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.sidebar.radio[0].set_value("C07").run()
    button(app, "Analisar chamado").click().run()
    assert not app.exception
    context = app.session_state["context"]
    assert not store.state(context)["receipts"]
    assert app.chat_input[0].disabled
    button(app, "Sim, autorizar").click().run()
    assert not app.exception
    assert len(store.state(context)["receipts"]) == 1
    assert not any(x.label == "Sim, autorizar" for x in app.button)
    app.run()
    assert len(store.state(context)["receipts"]) == 1


def test_refusal_preserves_data_and_removes_buttons(ui):
    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider = provider
    service.retriever = Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.sidebar.radio[0].set_value("C07").run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Não, recusar").click().run()
    assert not app.exception
    assert store.state(context) == before
    assert not any(x.label == "Sim, autorizar" for x in app.button)


def test_shared_access_gate_precedes_runtime(ui):
    _, _, settings = ui
    object.__setattr__(settings, "access_code", "test-access-code-only")
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert not app.chat_input
    app.text_input[0].set_value("wrong")
    button(app, "Entrar").click().run()
    assert app.error
    app.text_input[0].set_value("test-access-code-only")
    button(app, "Entrar").click().run()
    assert app.chat_input


def test_sources_link_directly_without_showing_content(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    message = store.messages(context, "C01")[-1]
    expected = [x for x in message["details"]["evidence"] if x.get("source_url")]
    links = app.get("link_button")
    assert links and {x.proto.url for x in links} <= {x["source_url"] for x in expected}
    assert not app.get("dialog") and not app.text
    assert not any(x.key and str(x.key).startswith("source_") for x in app.button)
    before = store.state(context)
    calls = service.provider.calls
    app.run()
    assert not app.exception
    assert store.messages(context, "C01")[-1]["details"]["evidence"] == message["details"]["evidence"]
    assert service.provider.calls == calls
    assert store.state(context) == before


def test_source_links_do_not_authorize_pending_action(ui):
    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.sidebar.radio[0].set_value("C07").run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    assert app.get("link_button")
    app.run()
    assert not app.exception
    assert not store.state(context)["receipts"]
    assert store.proposals(context, "C07")[0]["state"] == "pendente"
    assert provider.calls == 1
    button(app, "Sim, autorizar").click().run()
    assert len(store.state(context)["receipts"]) == 1


def test_sources_keep_original_url_when_knowledge_changes(ui):
    from sqlalchemy import select
    from sap_assistant.database import Chunk

    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    original = store.messages(context, "C01")[-1]
    expected = {x["source_url"] for x in original["details"]["evidence"] if x.get("source_url")}
    # Simula nova revisão da base: o snapshot antigo deve continuar legível.
    with store.transaction() as db:
        for row in db.scalars(select(Chunk)):
            row.content = "Nova revisão que não pertence ao atendimento antigo."
            row.attributes = {**row.attributes, "source_url": "https://help.sap.com/nova-revisao"}
    app.run()
    assert not app.exception
    assert {x.proto.url for x in app.get("link_button")} <= expected
    assert not app.text


def test_chat_button_previews_case_and_selects_only_on_confirmation(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Chamados").click().run()
    assert not app.exception
    assert len(app.selectbox(key="dialog_case").options) == 8
    app.selectbox(key="dialog_case").set_value("C04").run()
    assert app.session_state["selected_ticket"] == "C01"
    assert any("Post Goods Receipt for Purchasing Document" in x.value for x in app.markdown)
    button(app, "Abrir no chat").click().run()
    assert not app.exception and app.session_state["selected_ticket"] == "C04"
    assert app.title[0].value == before["tickets"]["C04"]["title"]
    assert not app.get("dialog") and service.provider.calls == 0 and store.state(context) == before


def test_case_selector_search_cancel_and_no_results(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Chamados").click().run()
    app.text_input(key="dialog_search").set_value("4500001007").run()
    assert app.selectbox(key="dialog_case").value == "C07"
    button(app, "Cancelar").click().run()
    assert app.session_state["selected_ticket"] == "C01" and not app.get("dialog")
    button(app, "Chamados").click().run()
    assert app.selectbox(key="dialog_case").value == "C01"
    app.text_input(key="dialog_search").set_value("inexistente").run()
    assert not any(x.key == "dialog_case" for x in app.selectbox)
    assert any("Nenhum chamado" in x.value for x in app.info)
    button(app, "Cancelar").click().run()
    assert store.state(context) == before and service.provider.calls == 0


def test_complete_case_list_filters_shows_details_and_opens_chat(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Lista completa").click().run()
    assert not app.exception and app.title[0].value == "Chamados" and not app.chat_input
    assert len(app.dataframe[0].value) == 8
    app.selectbox(key="list_priority").set_value("missing").run()
    assert app.selectbox(key="list_case").value == "C05"
    assert any(x.value == "Aplicativo: Não informado" for x in app.markdown)
    app.selectbox(key="list_priority").set_value("all").run()
    app.text_input(key="list_search").set_value("4500001003").run()
    assert len(app.dataframe[0].value) == 1 and app.selectbox(key="list_case").value == "C03"
    assert any(x.value == "Sistema: QAS" for x in app.markdown)
    assert any(x.value == "Componente sugerido: MM-IM-GR-PO" for x in app.markdown)
    assert any(x.value == "**Passos de reprodução informados**" for x in app.markdown)
    assert any(x.value == "**Impacto no negócio**" for x in app.markdown)
    button(app, "Abrir no chat").click().run()
    assert not app.exception and app.session_state["selected_ticket"] == "C03" and app.chat_input
    assert store.state(context) == before and service.provider.calls == 0


def test_navigation_keeps_history_and_pending_approval_bound_to_original_case(ui):
    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.sidebar.radio[0].set_value("C07").run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    proposal = store.proposals(context, "C07")[0]["id"]
    before = store.state(context)
    button(app, "Chamados").click().run()
    app.selectbox(key="dialog_case").set_value("C08").run()
    button(app, "Abrir no chat").click().run()
    assert not app.chat_message and not any(x.label == "Sim, autorizar" for x in app.button)
    button(app, "Lista completa").click().run()
    app.selectbox(key="list_case").set_value("C07").run()
    button(app, "Abrir no chat").click().run()
    assert len(app.chat_message) == 2 and app.chat_input[0].disabled
    assert store.proposals(context, "C07")[0]["id"] == proposal
    assert store.state(context) == before and provider.calls == 1
    button(app, "Sim, autorizar").click().run()
    assert len(store.state(context)["receipts"]) == 1


def test_case_list_row_selection_matches_details_and_dropdown_can_override(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Lista completa").click().run()
    table_key = "case_table_" + "_".join(before["tickets"])
    # AppTest não oferece clique em linha; injeta o estado de seleção nativo documentado.
    app.session_state[table_key] = {"selection": {"rows": [3], "columns": [], "cells": []}}
    app.run()
    assert not app.exception and app.selectbox(key="list_case").value == "C04"
    assert app.session_state["selected_ticket"] == "C01"
    app.selectbox(key="list_case").set_value("C06").run()
    assert not app.exception and app.selectbox(key="list_case").value == "C06"
    assert not app.session_state[table_key]["selection"]["rows"]
    button(app, "Abrir no chat").click().run()
    assert app.session_state["selected_ticket"] == "C06"
    assert store.state(context) == before and service.provider.calls == 0


def test_empty_case_list_can_return_without_losing_active_case(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.sidebar.radio[0].set_value("C03").run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Lista completa").click().run()
    app.text_input(key="list_search").set_value("nenhum-caso-com-esse-numero").run()
    assert not app.exception and not app.dataframe
    assert any("Nenhum chamado" in x.value for x in app.info)
    button(app, "Voltar ao chat").click().run()
    assert app.session_state["selected_ticket"] == "C03" and app.chat_input
    assert store.state(context) == before and service.provider.calls == 0


def test_legacy_workspace_can_use_new_views_without_retroactive_updates(ui):
    from copy import deepcopy

    store, service, _ = ui
    context = store.create_workspace()
    with store.transaction() as db:
        workspace = store.authorize(db, context, lock=True)
        data = deepcopy(workspace.data)
        for ticket in data["tickets"].values():
            ticket.pop("support")
        workspace.data = data
    before = store.state(context)
    app = AppTest.from_file(str(APP), default_timeout=15)
    app.session_state["context"] = context
    app.run()
    assert not app.exception and not app.error
    assert any(x.value == "Sistema: Não informado" for x in app.markdown)
    button(app, "Chamados").click().run()
    app.selectbox(key="dialog_case").set_value("C08").run()
    button(app, "Abrir no chat").click().run()
    button(app, "Lista completa").click().run()
    assert len(app.dataframe[0].value) == 8 and not app.exception and not app.error
    assert set(app.dataframe[0].value["Prioridade"]) == {"Não informado"}
    assert store.state(context) == before and service.provider.calls == 0

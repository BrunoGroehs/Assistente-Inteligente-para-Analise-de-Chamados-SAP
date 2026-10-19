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


def attach(app, key):
    button(app, "Chamados").click().run()
    app.selectbox(key="dialog_case").set_value(key).run()
    button(app, "Anexar ao chat").click().run()
    assert not app.exception and not app.error
    assert app.session_state["attached_case"] == key


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


def test_single_chat_starts_without_sidebar_or_attachment(ui):
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception and not app.sidebar.radio and not app.radio
    assert len(app.chat_input) == 1 and app.session_state["attached_case"] is None
    assert not any(x.label == "Analisar chamado" for x in app.button)
    assert not any(x.label.startswith("Sim") or x.label.startswith("Não") for x in app.button)
    app.chat_input[0].set_value("O que é recebimento com referência ao pedido?").run()
    assert len(app.chat_message) == 2
    assert any(x.label == "Fontes citadas" for x in app.expander)
    attach(app, "C01")
    assert len(app.chat_message) == 2
    button(app, "Analisar chamado").click().run()
    assert len(app.chat_message) == 4
    attach(app, "C02")
    assert len(app.chat_message) == 4 and not app.exception


def test_approval_button_executes_once_and_disappears(ui):
    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider = provider
    service.retriever = Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    attach(app, "C07")
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
    attach(app, "C07")
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
    attach(app, "C01")
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
    attach(app, "C07")
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
    attach(app, "C01")
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


def test_picker_lists_all_cases_and_details_without_attaching(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Chamados").click().run()
    assert len(app.dataframe[0].value) == 8
    app.selectbox(key="dialog_case").set_value("C04").run()
    button(app, "Ver detalhes").click().run()
    assert app.session_state["attached_case"] is None
    assert any(x.value == "Sistema: QAS" for x in app.markdown)
    assert any(x.value == "Componente sugerido: MM-IM-GR-PO" for x in app.markdown)
    assert any("Passos de reprodução" in x.value for x in app.markdown)
    assert any("Impacto no negócio" in x.value for x in app.markdown)
    button(app, "Anexar ao chat").click().run()
    assert app.session_state["attached_case"] == "C04" and not app.get("dialog")
    assert app.button(key="attached_case_details").label.startswith("SIM-C04")
    assert store.state(context) == before and service.provider.calls == 0


def test_picker_search_filters_cancel_and_empty_results(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Chamados").click().run()
    app.selectbox(key="dialog_priority").set_value("missing").run()
    assert app.selectbox(key="dialog_case").value == "C05"
    button(app, "Ver detalhes").click().run()
    assert any(x.value == "Aplicativo: Não informado" for x in app.markdown)
    app.selectbox(key="dialog_priority").set_value("all").run()
    app.text_input(key="dialog_search").set_value("4500001007").run()
    assert app.selectbox(key="dialog_case").value == "C07"
    app.text_input(key="dialog_search").set_value("nenhum-chamado").run()
    assert not app.dataframe and any("Nenhum chamado" in x.value for x in app.info)
    button(app, "Cancelar").click().run()
    assert app.session_state["attached_case"] is None and not app.get("dialog")
    assert store.state(context) == before and service.provider.calls == 0


def test_attachment_can_be_replaced_removed_and_inspected_without_analysis(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    attach(app, "C07")
    app.button(key="attached_case_details").click().run()
    assert any(x.value == "**Impacto no negócio**" for x in app.markdown)
    button(app, "Cancelar").click().run()
    assert app.session_state["attached_case"] == "C07"
    attach(app, "C08")
    assert app.button(key="attached_case_details").label.startswith("SIM-C08")
    button(app, "Remover anexo").click().run()
    assert app.session_state["attached_case"] is None
    assert not any(x.key == "attached_case_details" for x in app.button)
    assert not app.chat_input[0].disabled and not app.chat_message
    assert store.state(context) == before and service.provider.calls == 0


def test_picker_table_selection_matches_case_and_dropdown_can_override(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    before = store.state(context)
    button(app, "Chamados").click().run()
    table_key = "case_table_" + "_".join(before["tickets"])
    # AppTest não oferece clique em linha; injeta o estado nativo do componente.
    app.session_state[table_key] = {"selection": {"rows": [3], "columns": [], "cells": []}}
    app.run()
    assert not app.exception and app.selectbox(key="dialog_case").value == "C04"
    app.selectbox(key="dialog_case").set_value("C06").run()
    assert app.selectbox(key="dialog_case").value == "C06"
    assert not app.session_state[table_key]["selection"]["rows"]
    button(app, "Anexar ao chat").click().run()
    assert app.session_state["attached_case"] == "C06"
    assert store.state(context) == before and service.provider.calls == 0


def test_detaching_pending_case_keeps_proposal_and_unlocks_general_chat(ui):
    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    attach(app, "C07")
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    proposal = store.proposals(context, "C07")[0]["id"]
    before = store.state(context)
    assert app.chat_input[0].disabled
    button(app, "Remover anexo").click().run()
    assert len(app.chat_message) == 2 and not app.chat_input[0].disabled
    assert not any(x.label == "Sim, autorizar" for x in app.button)
    assert store.proposals(context, "C07")[0]["id"] == proposal
    attach(app, "C08")
    assert not app.chat_input[0].disabled and not any(x.label == "Sim, autorizar" for x in app.button)
    attach(app, "C07")
    assert app.chat_input[0].disabled and len(app.chat_message) == 2
    assert store.state(context) == before and provider.calls == 1
    button(app, "Sim, autorizar").click().run()
    assert len(store.state(context)["receipts"]) == 1


def test_conversation_keeps_old_attachment_labels_after_detach(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    attach(app, "C01")
    button(app, "Analisar chamado").click().run()
    button(app, "Remover anexo").click().run()
    app.chat_input[0].set_value("O que é um documento de material?").run()
    assert not app.exception and len(app.chat_message) == 4
    captions = [x.value for x in app.caption]
    assert any("Chamado anexado · SIM-C01" in value for value in captions)
    assert "Sem chamado anexado" in captions
    context = app.session_state["context"]
    assert len(store.messages(context)) == 4
    assert store.messages(context)[0]["details"]["attachment"]["id"] == "C01"
    assert store.messages(context)[-1]["details"]["attachment"] is None
    assert service.provider.calls == 2


def test_legacy_workspace_and_history_remain_readable_without_migration(ui):
    from copy import deepcopy

    store, service, _ = ui
    context = store.create_workspace()
    service.analyze(context, "C01", "Explique o saldo do pedido.")
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
    assert not app.exception and len(app.chat_message) == 2
    assert app.session_state["attached_case"] is None
    button(app, "Chamados").click().run()
    button(app, "Ver detalhes").click().run()
    assert len(app.dataframe[0].value) == 8
    assert any(x.value == "Sistema: Não informado" for x in app.markdown)
    assert store.state(context) == before and service.provider.calls == 1


def test_navigation_uses_no_database_roundtrips_and_refresh_reads_once(ui):
    from sqlalchemy import event

    store, _, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    statements = []

    def count(*args):
        statements.append(1)

    event.listen(store.engine, "before_cursor_execute", count)
    try:
        app.run()
        button(app, "Chamados").click().run()
        app.selectbox(key="dialog_case").set_value("C07").run()
        button(app, "Ver detalhes").click().run()
        button(app, "Anexar ao chat").click().run()
        button(app, "Remover anexo").click().run()
        assert not app.exception and not statements
        button(app, "Atualizar").click().run()
        assert not app.exception and len(statements) == 3
    finally:
        event.remove(store.engine, "before_cursor_execute", count)


def test_manual_refresh_updates_external_changes_without_shared_cache(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    context = app.session_state["context"]
    service.analyze(context, None, "Explique recebimento.")
    app.run()
    assert not app.chat_message  # Snapshot de apresentação não é a fonte de verdade.
    button(app, "Atualizar").click().run()
    assert len(app.chat_message) == 2
    other = store.create_workspace()
    app.session_state["context"] = other
    app.run()
    assert not app.exception and not app.chat_message
    assert app.session_state["ui_view"]["context"] == other


def test_cached_approval_still_validates_current_business_data_on_server(ui):
    from copy import deepcopy

    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    attach(app, "C07")
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    with store.transaction() as db:
        workspace = store.authorize(db, context, lock=True)
        data = deepcopy(workspace.data)
        data["orders"]["4500001007/10"]["received"] = "21"
        workspace.data = data
    button(app, "Sim, autorizar").click().run()
    assert not app.exception
    assert not store.state(context)["receipts"]
    assert store.proposals(context, "C07")[0]["state"] == "invalidada"
    assert app.session_state["ui_view"]["snapshot"]["state"]["orders"]["4500001007/10"]["received"] == "21"
    assert not any(x.label == "Sim, autorizar" for x in app.button)


def test_cached_proposal_expires_visually_without_database_query(ui, monkeypatch):
    from datetime import datetime
    from sap_assistant import presentation

    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    attach(app, "C07")
    button(app, "Analisar chamado").click().run()
    cached = app.session_state["ui_view"]["snapshot"]
    expiry = datetime.fromisoformat(cached["proposals"][0]["expires_at"])
    monkeypatch.setattr(presentation, "utcnow", lambda: expiry)
    app.run()
    assert not app.exception and not app.chat_input[0].disabled
    assert not any(x.label == "Sim, autorizar" for x in app.button)
    assert any(x.value == "**Expirada**" for x in app.markdown)
    assert cached["proposals"][0]["state"] == "pendente"  # Derivação não altera snapshot/persistência.

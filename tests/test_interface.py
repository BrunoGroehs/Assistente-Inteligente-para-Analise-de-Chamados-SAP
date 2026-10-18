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
    assert any(x.label == "Fontes e evidências" for x in app.expander)
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

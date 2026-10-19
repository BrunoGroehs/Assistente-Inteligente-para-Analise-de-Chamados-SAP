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


def source_button(app, message_id=None):
    return next(x for x in app.button if x.key and str(x.key).startswith(
        f"source_{message_id}_" if message_id else "source_"))


def test_citation_opens_exact_snapshot_without_calling_model_again(ui):
    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    message = store.messages(context, "C01")[-1]
    key = source_button(app).key
    evidence_id = key.rsplit("_", 1)[-1]
    expected = next(x for x in message["details"]["evidence"] if x["id"] == evidence_id)
    before = store.state(context)
    calls = service.provider.calls
    source_button(app).click().run()
    assert not app.exception
    assert any(x.value == expected["content"].strip() for x in app.text)
    assert next(x for x in store.messages(context, "C01")[-1]["details"]["evidence"]
                if x["id"] == evidence_id)["content"] == expected["content"]
    assert any(expected["version"] in x.value for x in app.caption)
    assert service.provider.calls == calls
    assert store.state(context) == before
    button(app, "Fechar").click().run()
    assert not app.exception and service.provider.calls == calls


def test_source_popup_does_not_authorize_pending_action(ui):
    store, service, _ = ui
    provider = ReceiptProvider()
    service.provider, service.retriever = provider, Retriever(store, provider)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.sidebar.radio[0].set_value("C07").run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    source_button(app).click().run()
    assert not app.exception
    assert not store.state(context)["receipts"]
    assert store.proposals(context, "C07")[0]["state"] == "pendente"
    assert provider.calls == 1
    button(app, "Fechar").click().run()
    button(app, "Sim, autorizar").click().run()
    assert len(store.state(context)["receipts"]) == 1


def test_sources_remain_bound_to_each_message_and_original_version(ui):
    from sqlalchemy import select
    from sap_assistant.database import Chunk

    store, service, _ = ui
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    button(app, "Analisar chamado").click().run()
    context = app.session_state["context"]
    original = store.messages(context, "C01")[-1]
    first_button_key = source_button(app).key
    original_id = first_button_key.rsplit("_", 1)[-1]
    expected = next(x["content"] for x in original["details"]["evidence"] if x["id"] == original_id)
    # Simula nova revisão da base: o snapshot antigo deve continuar legível.
    with store.transaction() as db:
        for row in db.scalars(select(Chunk)):
            row.content = "Nova revisão que não pertence ao atendimento antigo."
    service.analyze(context, "C01", "Confirme o contexto.")
    app.run()
    keys = [x.key for x in app.button if x.key and str(x.key).startswith("source_")]
    assert len(keys) == len(set(keys))
    app.button(key=first_button_key).click().run()
    assert not app.exception
    assert any(x.value == expected.strip() for x in app.text)

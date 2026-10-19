import json

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from sap_assistant.config import Settings
from sap_assistant.database import Base, Chunk, PROJECT_SCHEMA
from sap_assistant.provider import OpenRouter, ProviderError
from sap_assistant.retrieval import Retriever, synchronize_knowledge
from conftest import ControlledProvider


def test_documents_cached_and_model_change_reindexes(store):
    provider = ControlledProvider()
    retriever = Retriever(store, provider)
    assert retriever.ensure_embeddings() == 5
    assert retriever.ensure_embeddings() == 0
    provider.embedding_model = "teste/outro-modelo"
    assert retriever.ensure_embeddings() == 5
    assert provider.embed_calls == 2


def test_hybrid_retrieval_selects_relevant_source(store):
    provider = ControlledProvider()
    evidence, metadata = Retriever(store, provider).search("MIGO aplicativo indicador entrega concluída")
    assert "K03" in [x.id for x in evidence]
    assert metadata["method"] == "hibrida_rrf"
    assert all(not x.id.startswith("C0") for x in evidence)


def test_sync_is_idempotent_and_does_not_touch_foreign_table(store):
    from sqlalchemy import text
    with store.engine.begin() as db:
        db.execute(text("CREATE TABLE unrelated_customer_data (id integer primary key, value text)"))
        db.execute(text("INSERT INTO unrelated_customer_data VALUES (1, 'preservar')"))
    synchronize_knowledge(store)
    store.initialize()
    with Session(store.engine) as db:
        assert len(db.scalars(select(Chunk)).all()) == 5
        assert db.scalar(text("SELECT value FROM unrelated_customer_data WHERE id=1")) == "preservar"


def test_all_tables_qualified_to_project_schema():
    from sqlalchemy.dialects.postgresql import dialect
    from sqlalchemy.schema import CreateTable
    assert all(table.schema == PROJECT_SCHEMA for table in Base.metadata.tables.values())
    for table in Base.metadata.tables.values():
        assert f"{PROJECT_SCHEMA}." in str(CreateTable(table).compile(dialect=dialect()))


@pytest.mark.parametrize("url", ["", "sqlite:///test.db", "postgres://user:pass@example/db"])
def test_app_does_not_allow_local_or_ambiguous_database(url):
    with pytest.raises(ValueError):
        Settings(database_url=url, environment="local").validate()


def test_hosted_access_requires_strong_code():
    with pytest.raises(ValueError):
        Settings(database_url="postgresql+psycopg://example/db").validate()


def provider_with(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenRouter(Settings(database_url="unused", api_key="test-only"), client)


def test_embeddings_reordered_by_index_and_validated():
    provider = provider_with(lambda _: httpx.Response(200, json={"data": [
        {"index": 1, "embedding": [0., 1.]}, {"index": 0, "embedding": [1., 0.]}]}))
    assert provider.embed(["a", "b"]) == [[1., 0.], [0., 1.]]


@pytest.mark.parametrize("data", [[], [{"index": 0, "embedding": [0, 0]}],
                                   [{"index": 2, "embedding": [1, 2]}]])
def test_malformed_embeddings_are_rejected(data):
    provider = provider_with(lambda _: httpx.Response(200, json={"data": data}))
    with pytest.raises(ProviderError):
        provider.embed(["a"])


@pytest.mark.parametrize("code", [401, 402, 500])
def test_provider_error_does_not_echo_secrets_or_response_body(code):
    provider = provider_with(lambda _: httpx.Response(code, text="secret DSN test-only"))
    with pytest.raises(ProviderError) as error:
        provider.embed(["a"])
    assert "test-only" not in str(error.value)
    assert "DSN" not in str(error.value)


def test_format_repair_is_bounded_and_no_execution_tools_sent(monkeypatch):
    calls = []

    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert "tools" not in payload
        assert payload["provider"]["require_parameters"] is True
        assert '"summary"' in payload["messages"][0]["content"]
        assert payload["reasoning"]["enabled"] is False
        return httpx.Response(200, json={"choices": [{"message": {"content": "invalid"}}]})

    provider = provider_with(handler)
    with pytest.raises(ProviderError):
        provider.analyze({}, [])
    assert len(calls) == 2


def test_transient_retry_bounded(monkeypatch):
    calls = []
    monkeypatch.setattr("sap_assistant.provider.time.sleep", lambda _: None)
    provider = provider_with(lambda _: (calls.append(1) or httpx.Response(429)))
    with pytest.raises(ProviderError):
        provider.embed(["a"])
    assert len(calls) == 3


def test_model_output_structured_and_usage_available():
    answer = dict(summary="Falta contexto", process="recebimento_pedido_compra", facts=[], hypotheses=[],
                  missing_information=["Qual o pedido?"], next_steps=[], references=[], confidence="baixa",
                  confidence_reason="Sem dados", human_review=True, action=None)
    provider = provider_with(lambda _: httpx.Response(200, json={"model": "qwen/qwen3.6-plus", "usage": {"total_tokens": 10},
                  "choices": [{"message": {"content": json.dumps(answer)}}]}))
    analysis, metadata = provider.analyze({}, [])
    assert analysis.human_review
    assert metadata["attempts"][0]["usage"]["total_tokens"] == 10


def test_key_is_required_without_network():
    provider = OpenRouter(Settings(database_url="unused"))
    with pytest.raises(ProviderError, match="Configure"):
        provider.embed(["a"])


def test_invalid_references_receive_bounded_repair():
    answer = dict(summary="Sem dados", process="recebimento_pedido_compra", facts=[], hypotheses=[],
                  missing_information=["Qual o pedido?"], next_steps=[], references=["INVENTADA"], confidence="baixa",
                  confidence_reason="Sem dados", human_review=True, action=None)
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        current = {**answer, "references": [] if len(calls) == 2 else ["INVENTADA"]}
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(current)}}]})

    result, metadata = provider_with(handler).analyze({}, [])
    assert not result.references
    assert len(metadata["attempts"]) == 2
    assert "references" in calls[1]["messages"][-1]["content"]


def test_scope_policy_discards_irrelevant_facts_and_any_action():
    raw = {"process": "fora_do_escopo", "facts": [{"text": "Informação alheia ao atendimento"}],
           "action": {"operation": "execute_sql"}}
    provider = provider_with(lambda _: httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(raw)}}]}))
    analysis, metadata = provider.analyze({}, [])
    assert analysis.process == "fora_do_escopo"
    assert analysis.action is None and not analysis.facts and not analysis.references
    assert metadata["server_policy"] == "fora_do_escopo"

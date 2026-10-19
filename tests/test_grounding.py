from copy import deepcopy
import json

import httpx
import pytest
from sqlalchemy import select

from sap_assistant.config import Settings
from sap_assistant.contracts import Evidence
from sap_assistant.database import Chunk
from sap_assistant.grounding import (
    INSUFFICIENT_MESSAGE, KnowledgeAssessment, insufficient_assessment, knowledge_spans, supported_ids,
)
from sap_assistant.provider import OpenRouter
from sap_assistant.retrieval import Retriever
from sap_assistant.service import AssistantService
from conftest import ControlledProvider, ReceiptProvider


class EmptyRetriever:
    def search(self, query):
        return [], {"selected_ids": []}


def assert_abstention(store, context, ticket):
    analysis = store.messages(context, ticket)[-1]["details"]["analysis"]
    assert analysis["summary"] == INSUFFICIENT_MESSAGE
    assert analysis["confidence"] == "baixa" and analysis["human_review"]
    assert not analysis["facts"] and not analysis["hypotheses"] and not analysis["references"]
    assert analysis["action"] is None and not store.proposals(context, ticket)


def test_empty_rag_never_calls_generation_or_proposes_receipt(store, context):
    provider = ReceiptProvider()
    assistant = AssistantService(store, EmptyRetriever(), provider)
    before = store.state(context)
    assert assistant.analyze(context, "C07", "Registre conforme o chamado")["state"] == "completed"
    assert provider.calls == 0 and store.state(context) == before
    assert_abstention(store, context, "C07")


def test_irrelevant_knowledge_does_not_enable_technical_answer(store, context):
    class UnsupportedProvider(ReceiptProvider):
        def assess_knowledge(self, ctx):
            assert "BAdI" in ctx["message"]
            return insufficient_assessment("Nenhum trecho cobre a implementação solicitada."), {}

    provider = UnsupportedProvider()
    assistant = AssistantService(store, Retriever(store, provider), provider)
    assistant.analyze(context, "C07", "Como implementar a BAdI para corrigir meu recebimento?")
    assert provider.calls == 0
    assert_abstention(store, context, "C07")


@pytest.mark.parametrize("bad_support", ["missing", "invented_span", "DATA"])
def test_fabricated_coverage_fails_closed(store, context, bad_support):
    class InvalidCoverageProvider(ReceiptProvider):
        def assess_knowledge(self, ctx):
            item = ctx["evidence"][0]
            supports = [] if bad_support == "missing" else [{
                "evidence_id": "DATA" if bad_support == "DATA" else item["id"],
                "span_id": "DATA:1" if bad_support == "DATA" else "K99:999"}]
            return KnowledgeAssessment(scope="recebimento_pedido_compra", sufficient=True,
                                       supports=supports, reason="Alegação sem prova."), {}

    provider = InvalidCoverageProvider()
    assistant = AssistantService(store, Retriever(store, provider), provider)
    assistant.analyze(context, "C07", "Registre o recebimento")
    assert provider.calls == 0
    assert_abstention(store, context, "C07")


def test_model_cannot_answer_without_citing_approved_knowledge(store, context):
    class UncitedProvider(ReceiptProvider):
        def analyze(self, ctx, history):
            answer, meta = super().analyze(ctx, history)
            answer.references = ["DATA"]
            answer.summary = "Resposta técnica sem documento citado."
            return answer, meta

    provider = UncitedProvider()
    AssistantService(store, Retriever(store, provider), provider).analyze(context, "C07", "Registre")
    assert_abstention(store, context, "C07")


def test_new_question_is_evaluated_independently_from_previous_answer(store, context):
    class TopicProvider(ControlledProvider):
        questions = []

        def assess_knowledge(self, ctx):
            self.questions.append(ctx["message"])
            if "OBYC" in ctx["message"]:
                return insufficient_assessment("A pergunta nova não está documentada."), {}
            return super().assess_knowledge(ctx)

    provider = TopicProvider()
    assistant = AssistantService(store, Retriever(store, provider), provider)
    assistant.analyze(context, "C01", "Explique o saldo")
    calls = provider.calls
    assistant.analyze(context, "C01", "E a parametrização detalhada da OBYC?")
    assert provider.questions == ["Explique o saldo", "E a parametrização detalhada da OBYC?"]
    assert provider.calls == calls
    assert_abstention(store, context, "C01")


def test_empty_index_needs_no_embedding_api_call(store):
    with store.transaction() as db:
        for row in db.scalars(select(Chunk)):
            db.delete(row)
    provider = ControlledProvider()
    evidence, meta = Retriever(store, provider).search("recebimento")
    assert not evidence and not meta["selected_ids"] and provider.embed_calls == 0


def test_coverage_quote_must_come_from_knowledge_not_transaction_data():
    text = "Quantidade recebida e saldo do pedido de compra."
    data = Evidence(id="DATA", title="Consulta", content=text, kind="consulta_simulada", version="1")
    assessment = KnowledgeAssessment(scope="recebimento_pedido_compra", sufficient=True,
                                    supports=[{"evidence_id": "DATA", "span_id": "DATA:1"}], reason="Sem documentação")
    with pytest.raises(ValueError):
        supported_ids(assessment, [data])


def test_valid_coverage_accepts_only_exact_quote_and_deduplicates():
    item = Evidence(id="K07", title="Tipos de estoque", content="O estoque em inspeção de qualidade não é de livre utilização.",
                    kind="sintese_de_fonte_oficial", version="1")
    support = {"evidence_id": "K07", "span_id": "K07:1"}
    assessment = KnowledgeAssessment(scope="recebimento_pedido_compra", sufficient=True,
                                    supports=[support, deepcopy(support)], reason="Coberto")
    assert supported_ids(assessment, [item]) == ["K07"]
    assert knowledge_spans(item)[0]["text"] == item.content


@pytest.mark.parametrize("content", ['not JSON', '{}', '{"sufficient":true}', 'null'])
def test_invalid_coverage_response_abstains_with_one_call(content):
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    provider = OpenRouter(Settings(database_url="unused", api_key="test-only"),
                          httpx.Client(transport=httpx.MockTransport(handler)))
    result, metadata = provider.assess_knowledge({"message": "Pergunta", "evidence": []})
    assert not result.sufficient and metadata["invalid_response"]
    assert len(calls) == 1 and "tools" not in calls[0]


def test_new_corpus_has_attribution_and_keeps_evaluation_outside_index(store):
    with store.transaction() as db:
        rows = list(db.scalars(select(Chunk)))
    assert len(rows) == 12
    assert len([x for x in rows if x.attributes["kind"] == "sintese_de_fonte_oficial"]) == 10
    assert all(x.attributes["source_url"].startswith("https://learning.sap.com/") for x in rows
               if x.attributes["kind"] == "sintese_de_fonte_oficial")
    assert not any("testes" in x.attributes["file"] or "gabarito" in x.content.lower() for x in rows)


def test_generation_does_not_reclassify_documented_concept_as_outside_scope():
    answer = dict(summary="O perfil determina o tratamento da série no recebimento.", process="recebimento_pedido_compra",
                  facts=[], hypotheses=[], missing_information=[], next_steps=[], references=["K10"], confidence="media",
                  confidence_reason="Fonte conceitual disponível.", human_review=False, action=None)
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        raw = {"process": "fora_do_escopo"} if len(calls) == 1 else answer
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(raw)}}]})

    item = Evidence(id="K10", title="Séries", content="O perfil determina o tratamento da série no recebimento.",
                    kind="sintese_de_fonte_oficial", version="1")
    provider = OpenRouter(Settings(database_url="unused", api_key="test-only"),
                          httpx.Client(transport=httpx.MockTransport(handler)))
    result, _ = provider.analyze({"validated_scope": "recebimento_pedido_compra", "evidence": [item.model_dump()]}, [])
    assert result.references == ["K10"] and len(calls) == 2
    assert "escopo" in calls[1]["messages"][-1]["content"]


def test_coverage_schema_offers_only_retrieved_knowledge_paragraphs():
    item = Evidence(id="K10", title="Séries", content="O perfil determina o tratamento da série no recebimento.",
                    kind="sintese_de_fonte_oficial", version="1")

    def handler(request):
        payload = json.loads(request.content)
        fields = payload["response_format"]["json_schema"]["schema"]["$defs"]["KnowledgeSupport"]["properties"]
        assert fields["evidence_id"]["enum"] == ["K10"]
        assert fields["span_id"]["enum"] == ["K10:1"]
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "scope": "recebimento_pedido_compra", "sufficient": True,
            "supports": [{"evidence_id": "K10", "span_id": "K10:1"}], "reason": "Fonte aplicável."})}}]})

    provider = OpenRouter(Settings(database_url="unused", api_key="test-only"),
                          httpx.Client(transport=httpx.MockTransport(handler)))
    result, _ = provider.assess_knowledge({"message": "Perfil de série?", "evidence": [item.model_dump()],
                                         "observations": [{"id": "DATA", "content": "Só dados"}]})
    assert supported_ids(result, [item]) == ["K10"]

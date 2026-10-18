import hashlib
import json

import pytest

from sap_assistant.approvals import canonical_phrase
from sap_assistant.contracts import Analysis, ReceiptRequest
from sap_assistant.database import Store
from sap_assistant.retrieval import Retriever, synchronize_knowledge
from sap_assistant.service import AssistantService


@pytest.fixture
def store(tmp_path):
    value = Store(f"sqlite:///{tmp_path / 'test.db'}")
    value.initialize()
    synchronize_knowledge(value)
    yield value
    value.engine.dispose()


@pytest.fixture
def context(store):
    return store.create_workspace()


def receipt_request(store, context, code="C07", quantity="10"):
    data = store.state(context)
    ticket = data["tickets"][code]
    order = data["orders"][f"{ticket['purchase_order']}/{ticket['item']}"]
    request = ReceiptRequest(operation="registrar_recebimento_simulado", parameters={
        **{key: order[key] for key in ("purchase_order", "item", "unit", "material", "plant", "storage_location")},
        "quantity": quantity, "posting_date": "2026-10-18"}, confirmation_phrase="Frase a preencher")
    request.confirmation_phrase = canonical_phrase(request, code)
    return request


class ControlledProvider:
    """Dublê exclusivo dos testes. Não é fallback do aplicativo."""
    embedding_model = "teste/controlled-embedding"
    calls = 0
    embed_calls = 0

    def embed(self, texts):
        self.embed_calls += 1
        return [[(x+1)/256 for x in hashlib.sha256(t.encode()).digest()[:8]] for t in texts]

    def analyze(self, context, history):
        self.calls += 1
        references = [e["id"] for e in context["evidence"]]
        return Analysis(summary="Resposta controlada para testar o fluxo, sem inferência real.",
                        process="recebimento_pedido_compra", facts=[], hypotheses=[], missing_information=[],
                        next_steps=["Conferir as evidências."], references=references,
                        confidence="media", confidence_reason="Provedor controlado de teste.",
                        human_review=False, action=None), {"requested_model": "teste/controlled", "attempts": []}


class ReceiptProvider(ControlledProvider):
    def analyze(self, context, history):
        analysis, metadata = super().analyze(context, history)
        data = json.loads(next(x["content"] for x in context["evidence"] if x["id"] == "DATA"))
        request = ReceiptRequest(operation="registrar_recebimento_simulado", parameters={
            **{key: data[key] for key in ("purchase_order", "item", "unit", "material", "plant", "storage_location")},
            "quantity": "10", "posting_date": "2026-10-18"}, confirmation_phrase="Frase a preencher")
        request.confirmation_phrase = canonical_phrase(request, context["ticket"]["id"])
        analysis.action = request
        return analysis, metadata


@pytest.fixture
def service(store):
    provider = ControlledProvider()
    return AssistantService(store, Retriever(store, provider), provider)

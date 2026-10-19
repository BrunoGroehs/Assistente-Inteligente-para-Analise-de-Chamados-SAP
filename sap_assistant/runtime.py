from contextlib import suppress

from .approvals import ApprovalGateway
from .database import Store
from .provider import OpenRouter
from .retrieval import Retriever, synchronize_knowledge
from .service import AssistantService
from .startup import startup_error


def create_runtime(settings):
    stage, store, provider = "configuracao", None, None
    try:
        settings.validate()
        stage = "banco"
        store = Store(settings.database_url)
        store.initialize()
        stage = "conhecimento"
        synchronize_knowledge(store)
        stage = "provedor"
        provider = OpenRouter(settings)
        return (store, AssistantService(store, Retriever(store, provider), provider, settings.max_analyses),
                ApprovalGateway(store))
    except Exception as error:
        with suppress(Exception):
            if provider is not None:
                provider.client.close()
        with suppress(Exception):
            if store is not None:
                store.engine.dispose()
        raise startup_error(stage, error) from None

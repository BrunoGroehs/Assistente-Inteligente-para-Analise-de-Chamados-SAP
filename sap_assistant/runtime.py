from .approvals import ApprovalGateway
from .database import Store
from .provider import OpenRouter
from .retrieval import Retriever, synchronize_knowledge
from .service import AssistantService


def create_runtime(settings):
    settings.validate()
    store = Store(settings.database_url)
    store.initialize()
    synchronize_knowledge(store)
    provider = OpenRouter(settings)
    return store, AssistantService(store, Retriever(store, provider), provider, settings.max_analyses), ApprovalGateway(store)

import argparse
import json

from .config import Settings
from .provider import OpenRouter, ProviderError
from .retrieval import Retriever, synchronize_knowledge
from .database import DatabaseSetupError, Store


def main():
    parser = argparse.ArgumentParser(description="Preparação e diagnóstico do assistente SAP")
    parser.add_argument("command", choices=["init-db", "ingest", "check-provider"])
    args = parser.parse_args()
    settings = Settings.load()
    try:
        if args.command == "check-provider":
            provider = OpenRouter(settings)
            vectors = provider.embed(["recebimento com referência ao pedido de compra"])
            analysis, meta = provider.analyze({"ticket": {"id": "CHECK"}, "message": "Qual o escopo do assistente?",
                                               "evidence": []}, [])
            print(json.dumps({"embedding_model": settings.embedding_model, "dimension": len(vectors[0]),
                              "chat": meta, "process": analysis.process}, ensure_ascii=False, indent=2))
            return
        settings.validate()
        store = Store(settings.database_url)
        store.initialize()
        count = synchronize_knowledge(store)
        embedded = Retriever(store, OpenRouter(settings)).ensure_embeddings() if args.command == "ingest" else 0
        print(f"Base pronta: {count} guias; {embedded} embeddings gerados nesta execução.")
    except (ProviderError, DatabaseSetupError) as exc:
        parser.exit(1, str(exc) + "\n")
    except Exception:
        # Não imprimir DSN, senha, chave ou payload de exceções SQL/HTTP.
        parser.exit(1, "Falha na preparação. Confira credenciais, acesso ao banco/pgvector e disponibilidade do provedor.\n")


if __name__ == "__main__":
    main()

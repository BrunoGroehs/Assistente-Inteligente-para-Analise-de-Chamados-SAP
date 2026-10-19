"""Compatibilidade: executa a verificação atual de chat com anexos opcionais.

O seletor antigo com painel lateral foi substituído. Relatórios anteriores são
históricos; a execução atual consome créditos e grava verificacao-anexos-chat.json.
"""
from verify_chat_attachments_live import main


if __name__ == "__main__":
    main()

"""Entrada ASGI: python -m uvicorn app:app --host 127.0.0.1 --port 8000."""
from sap_assistant.api import create_app

app = create_app()

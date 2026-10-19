"""Origem pública em proxy sem confiar em cabeçalhos forjados pelo cliente."""
from fastapi.testclient import TestClient
import pytest

from sap_assistant.api import create_app
from sap_assistant.approvals import ApprovalGateway
from sap_assistant.config import Settings
from sap_assistant.retrieval import Retriever
from sap_assistant.service import AssistantService
from conftest import ControlledProvider


def test_public_origin_behind_proxy_keeps_cookie_and_rejects_spoofed_headers(store):
    provider = ControlledProvider()
    services = (store, AssistantService(store, Retriever(store, provider), provider), ApprovalGateway(store))
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="cloud",
                        access_code="test-access-code", public_origin="https://sap.example.test")
    with TestClient(create_app(settings, services), base_url="https://internal.invalid") as client:
        headers = {"X-Requested-With": "sap-assistant", "Origin": settings.public_origin}
        response = client.post("/api/session", json={"access_code": settings.access_code}, headers=headers)
        assert response.status_code == 200
        cookie = response.headers["set-cookie"].lower()
        assert "secure" in cookie and "httponly" in cookie and "path=/api" in cookie
        assert client.get("/api/session").status_code == 200
        headers.update({"Origin": "https://attacker.invalid", "X-Forwarded-Host": "attacker.invalid"})
        assert client.post("/api/chats", json={}, headers=headers).status_code == 403
        headers["Origin"] = "https://[invalid"
        assert client.post("/api/chats", json={}, headers=headers).status_code == 403


@pytest.mark.parametrize("environment,expected", [
    ("development", "http://127.0.0.1:3000"), ("preview", "https://preview.example.test"),
])
def test_origin_uses_vercel_runtime_url_and_allows_explicit_override(monkeypatch, environment, expected):
    monkeypatch.setattr("sap_assistant.config.load_dotenv", lambda *a: None)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", environment)
    monkeypatch.setenv("VERCEL_URL", expected.split("://", 1)[1])
    monkeypatch.setenv("APP_PUBLIC_ORIGIN", "")
    assert Settings.load().public_origin == expected
    monkeypatch.setenv("APP_PUBLIC_ORIGIN", "https://custom.example.test/")
    assert Settings.load().public_origin == "https://custom.example.test"


@pytest.mark.parametrize("origin", ["*", "//example.test", "https://example.test/path",
                                    "https://example.test?x=1", "https://user:password@example.test"])
def test_public_origin_rejects_wildcards_paths_and_credentials(origin):
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="local",
                        public_origin=origin)
    with pytest.raises(ValueError, match="APP_PUBLIC_ORIGIN"):
        settings.validate()

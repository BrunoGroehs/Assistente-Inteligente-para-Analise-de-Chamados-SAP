"""Falhas de cold start precisam orientar sem imprimir conexão, SQL ou segredo."""
from types import SimpleNamespace
import traceback
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import DBAPIError, OperationalError

from sap_assistant.api import create_app
from sap_assistant.config import Settings
from sap_assistant.database import DatabaseSetupError
from sap_assistant import runtime
from sap_assistant.startup import StartupError, startup_error

PRIVATE = "senha-ficticia-nao-expor"


@pytest.mark.parametrize("stage,error,expected", [
    ("banco", OperationalError("SQL_PRIVADO", {"password": PRIVATE}, Exception(PRIVATE)),
     "SAP_STARTUP_DB_CONNECTION"),
    ("banco", DBAPIError("SQL_PRIVADO", {}, SimpleNamespace(sqlstate="28P01")), "SAP_STARTUP_DB_AUTH"),
    ("banco", DBAPIError("SQL_PRIVADO", {}, SimpleNamespace(sqlstate="42501")), "SAP_STARTUP_DB_PERMISSION"),
    ("banco", DatabaseSetupError("Ative a extensão vector no painel Supabase antes de inicializar."),
     "SAP_STARTUP_DB_VECTOR"),
    ("banco", DatabaseSetupError(PRIVATE), "SAP_STARTUP_DB_IDENTITY"),
    ("banco", ValueError(PRIVATE), "SAP_STARTUP_DATABASE"),
    ("conhecimento", FileNotFoundError(PRIVATE), "SAP_STARTUP_KNOWLEDGE_FILES"),
    ("conhecimento", ValueError(PRIVATE), "SAP_STARTUP_KNOWLEDGE"),
    ("conhecimento", DBAPIError("SQL_PRIVADO", {}, Exception(PRIVATE)), "SAP_STARTUP_KNOWLEDGE_DATABASE"),
    ("provedor", RuntimeError(PRIVATE), "SAP_STARTUP_PROVIDER"),
    ("configuracao", ValueError(PRIVATE), "SAP_STARTUP_CONFIG"),
    ("runtime", RuntimeError(PRIVATE), "SAP_STARTUP_RUNTIME"),
])
def test_error_codes_do_not_include_original_exception(stage, error, expected):
    safe = startup_error(stage, error)
    assert safe.code == expected
    assert str(safe).startswith(expected + ":")
    assert PRIVATE not in str(safe) and "SQL_PRIVADO" not in str(safe)


def test_connection_failure_closes_pool_and_does_not_load_knowledge(monkeypatch):
    store = Mock()
    store.initialize.side_effect = OperationalError("SQL_PRIVADO", {}, Exception(PRIVATE))
    monkeypatch.setattr(runtime, "Store", Mock(return_value=store))
    synchronize = Mock()
    monkeypatch.setattr(runtime, "synchronize_knowledge", synchronize)
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="local")
    with pytest.raises(StartupError, match="SAP_STARTUP_DB_CONNECTION") as raised:
        runtime.create_runtime(settings)
    store.engine.dispose.assert_called_once()
    synchronize.assert_not_called()
    rendered = "".join(traceback.format_exception(raised.value))
    assert PRIVATE not in rendered and "SQL_PRIVADO" not in rendered


def test_missing_catalog_is_distinguished_from_database_connection(monkeypatch):
    store = Mock()
    monkeypatch.setattr(runtime, "Store", Mock(return_value=store))
    monkeypatch.setattr(runtime, "synchronize_knowledge", Mock(side_effect=FileNotFoundError(PRIVATE)))
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="local")
    with pytest.raises(StartupError, match="SAP_STARTUP_KNOWLEDGE_FILES"):
        runtime.create_runtime(settings)
    store.engine.dispose.assert_called_once()


def test_lifespan_reports_configuration_error_without_leaking_its_value(monkeypatch):
    monkeypatch.setattr(Settings, "load", Mock(side_effect=ValueError(PRIVATE)))
    with pytest.raises(StartupError, match="SAP_STARTUP_CONFIG") as raised:
        with TestClient(create_app()):
            pytest.fail("A API não deve iniciar com configuração inválida.")
    assert PRIVATE not in "".join(traceback.format_exception(raised.value))


def test_lifespan_preserves_safe_runtime_error(monkeypatch):
    failure = StartupError("SAP_STARTUP_DB_CONNECTION", "Confira o pooler.")
    monkeypatch.setattr(runtime, "create_runtime", Mock(side_effect=failure))
    settings = Settings(database_url="postgresql+psycopg://test.invalid/db", environment="local")
    with pytest.raises(StartupError, match="SAP_STARTUP_DB_CONNECTION"):
        with TestClient(create_app(settings)):
            pytest.fail("A API não deve iniciar sem os serviços necessários.")

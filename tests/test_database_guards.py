from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import sap_assistant.database as module


@pytest.mark.parametrize("marker_present,keys", [(False, []), (True, ["outro-projeto"])])
def test_existing_unowned_schema_is_refused_before_any_table_creation(monkeypatch, marker_present, keys):
    connection = Mock()
    connection.scalar.return_value = True  # extensão vector presente
    connection.scalars.return_value.all.return_value = keys

    class Engine:
        dialect = SimpleNamespace(name="postgresql")

        @contextmanager
        def begin(self):
            yield connection

    inspector = Mock()
    inspector.has_schema.return_value = True
    inspector.has_table.return_value = marker_present
    monkeypatch.setattr(module, "inspect", lambda _: inspector)
    create = Mock()
    monkeypatch.setattr(module.Base.metadata, "create_all", create)
    store = object.__new__(module.Store)
    store.engine = Engine()
    with pytest.raises(module.DatabaseSetupError):
        store.initialize()
    create.assert_not_called()
    assert all(not any(word in str(call).upper() for word in ["CREATE TABLE", "DROP", "ALTER TABLE"])
               for call in connection.execute.call_args_list)


def test_missing_vector_does_not_create_schema_or_extension(monkeypatch):
    connection = Mock()
    connection.scalar.return_value = False

    class Engine:
        dialect = SimpleNamespace(name="postgresql")

        @contextmanager
        def begin(self):
            yield connection

    create = Mock()
    monkeypatch.setattr(module.Base.metadata, "create_all", create)
    store = object.__new__(module.Store)
    store.engine = Engine()
    with pytest.raises(module.DatabaseSetupError, match="vector"):
        store.initialize()
    create.assert_not_called()
    assert not any("CREATE" in str(call).upper() for call in connection.execute.call_args_list)

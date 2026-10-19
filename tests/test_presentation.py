from copy import deepcopy
from datetime import timedelta

import pytest

from sap_assistant.database import AccessDenied, SessionContext, utcnow
from sap_assistant.presentation import visible_proposals


def test_snapshot_reads_only_the_authorized_workspace(service, store, context):
    service.analyze(context, None, "Explique o recebimento.")
    view = store.snapshot(context)
    assert len(view["messages"]) == 2 and not view["proposals"]
    other = store.create_workspace()
    assert not store.snapshot(other)["messages"]
    with pytest.raises(AccessDenied):
        store.snapshot(SessionContext(context.workspace_id, other.token))
    before = store.state(context)
    view["state"]["tickets"]["C01"]["title"] = "Mudança somente visual"
    assert store.state(context) == before


def test_visual_expiration_is_inclusive_preserves_terminal_states_and_never_changes_source():
    now = utcnow()
    source = [{"state": "pendente", "expires_at": now.isoformat(), "result": {}},
              {"state": "pendente", "expires_at": (now + timedelta(seconds=1)).isoformat(), "result": {}},
              {"state": "executada", "expires_at": (now - timedelta(seconds=1)).isoformat(),
               "result": {"message": "Executada anteriormente"}}]
    original = deepcopy(source)
    result = visible_proposals(source, now)
    assert [x["state"] for x in result] == ["expirada", "pendente", "executada"]
    assert result[-1]["result"] == source[-1]["result"] and source == original

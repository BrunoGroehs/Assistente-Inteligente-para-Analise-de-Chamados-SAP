from copy import deepcopy

from sap_assistant.cases import (
    NOT_PROVIDED, case_reference, case_rows, matching_cases, occurrence_label, order_summary,
)
from sap_assistant.fixtures import initial_state


def test_support_cases_keep_simulated_identity_and_missing_information():
    state = initial_state()
    assert len(state["tickets"]) == 8
    for key, ticket in state["tickets"].items():
        profile = ticket["support"]
        assert case_reference(ticket) == f"SIM-{key}"
        assert profile["sap_case_number"] is None and profile["component_confirmed"] is False
        assert profile["product_version"] is None and profile["system_role"] == "Teste / qualidade"
        assert profile["priority"] in {None, "1", "2", "3", "4"}
    missing = state["tickets"]["C05"]
    assert missing["purchase_order"] is None
    assert all(missing["support"][field] is None for field in ["priority", "application", "error_message", "business_impact"])
    assert not missing["support"]["steps_to_reproduce"] and not missing["support"]["attachments"]


def test_search_finds_purchase_order_material_and_accented_text_without_writes():
    state = initial_state()
    before = deepcopy(state)
    assert matching_cases(state, "4500001007") == ["C07"]
    assert matching_cases(state, "MAT-008") == ["C08"]
    assert matching_cases(state, "sim-c06") == ["C06"]
    assert matching_cases(state, "media") == ["C03", "C04", "C06"]
    assert matching_cases(state, priority="missing") == ["C05"]
    assert not matching_cases(state, "naoexiste")
    assert state == before


def test_legacy_cases_are_displayed_without_migrating_business_data():
    state = initial_state()
    ticket = state["tickets"]["C01"]
    ticket.pop("support")
    before = deepcopy(state)
    row = case_rows(state, ["C01"])[0]
    assert row["Chamado"] == "SIM-C01" and row["Prioridade"] == NOT_PROVIDED
    assert row["Sistema"] == NOT_PROVIDED and row["Componente sugerido"] == NOT_PROVIDED
    assert matching_cases(state, "4500001001") == ["C01"]
    assert state == before


def test_fixture_metadata_does_not_share_mutable_lists():
    first = initial_state()
    first["tickets"]["C01"]["support"]["steps_to_reproduce"].append("Teste isolado")
    assert "Teste isolado" not in initial_state()["tickets"]["C01"]["support"]["steps_to_reproduce"]


def test_occurrence_and_order_details_preserve_explicit_values():
    assert occurrence_label(None) == NOT_PROVIDED
    assert occurrence_label("not-a-date") == NOT_PROVIDED
    assert occurrence_label("2026-10-18T09:00:00-03:00") == "18/10/2026 09:00 -0300"
    assert order_summary(None) == NOT_PROVIDED
    text = order_summary(initial_state()["orders"]["4500001001/10"])
    assert "Saldo: 40" in text and "Centro BR01" in text and "Entrega concluída: Não" in text

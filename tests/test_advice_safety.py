import json

import pytest

from sap_assistant.contracts import Evidence, validate_grounding
from conftest import ControlledProvider


def assessment(summary, next_steps=None):
    analysis, _ = ControlledProvider().analyze({"evidence": []}, [])
    analysis.summary = summary
    analysis.next_steps = next_steps or []
    return analysis


def data(completed=True):
    return [Evidence(id="DATA", title="Dados simulados", content=json.dumps({"delivery_completed": completed}),
                     kind="consulta_simulada", version="1")]


@pytest.mark.parametrize("summary", [
    "Essa limitação não bloqueia recebimentos na transação MIGO.",
    "O indicador não impede o recebimento via MIGO. Confirme depois com o responsável.",
    "A MIGO permite registrar o saldo restante.",
    "A MIGO permite processar o saldo restante. Peça revisão humana.",
])
def test_completed_item_cannot_get_unqualified_migo_guarantee(summary):
    with pytest.raises(ValueError, match="não garantir recebimento"):
        validate_grounding(assessment(summary), data())


@pytest.mark.parametrize("summary", [
    "Essa limitação não comprova bloqueio universal na MIGO. Confirme a aplicabilidade.",
    "A restrição do aplicativo não impede necessariamente recebimentos na MIGO. É necessária revisão humana.",
    "O item não aparece no aplicativo informado. Verifique as condições antes de avaliar outra transação como MIGO.",
])
def test_qualified_explanation_does_not_claim_viability(summary):
    validate_grounding(assessment(summary), data())


def test_guard_applies_to_next_step_as_well_as_summary():
    with pytest.raises(ValueError):
        validate_grounding(assessment("É necessário revisar o indicador.", ["A MIGO permite registrar o restante."]), data())

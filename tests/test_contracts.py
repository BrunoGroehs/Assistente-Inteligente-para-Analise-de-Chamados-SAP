import pytest
from pydantic import ValidationError

from sap_assistant.contracts import Analysis, StatusRequest
from conftest import receipt_request


def fields():
    return dict(summary="Faltam informações", process="recebimento_pedido_compra", facts=[], hypotheses=[],
                missing_information=["Qual a data?"], next_steps=[], references=[], confidence="baixa",
                confidence_reason="Dados incompletos", human_review=True)


def test_missing_information_blocks_receipt(store, context):
    with pytest.raises(ValidationError):
        Analysis(**fields(), action=receipt_request(store, context))


def test_missing_diagnostic_context_can_still_request_human_escalation():
    request = StatusRequest(operation="atualizar_status_chamado", parameters={"status": "em_validacao_humana"},
                            confirmation_phrase="Posso alterar o chamado C06 para em validação humana?")
    assert Analysis(**fields(), action=request).human_review

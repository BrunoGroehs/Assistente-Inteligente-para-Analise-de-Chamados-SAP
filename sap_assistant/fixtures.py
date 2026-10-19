"""Somente entradas do simulador; nenhum gabarito é entregue ao modelo."""
from copy import deepcopy


# Relatos e metadados fictícios, sem causas/soluções ou gabaritos de avaliação.
CASE_CONTEXT = {
    "C01": {"priority": "4", "business_impact": "Dúvida na conferência de uma entrega parcial; sem parada informada.",
            "expected_result": "Entender a quantidade ainda exibida no pedido.",
            "actual_result": "O usuário relata 60 UN recebidas e 40 UN ainda exibidas.",
            "steps_to_reproduce": ["Consultar o pedido 4500001001 e seu histórico de recebimentos.",
                                   "Observar a quantidade ainda exibida."]},
    "C02": {"priority": "4", "business_impact": "Operador precisa de orientação para registrar uma entrega parcial.",
            "expected_result": "Obter orientação para registrar as 25 UN entregues.",
            "actual_result": "Foi solicitada orientação; nenhum erro específico foi informado."},
    "C03": {"priority": "3", "business_impact": "Registro de uma entrega está impedido no cenário de teste.",
            "expected_result": "Entender o impedimento antes de registrar a entrega.",
            "actual_result": "O usuário relata que não consegue registrar 35 UN.",
            "steps_to_reproduce": ["Selecionar o pedido 4500001003, item 10.",
                                   "Tentar registrar a entrega de 35 UN, conforme o relato."],
            "actions_taken": ["Tentativa de registro informada pelo solicitante."]},
    "C04": {"priority": "3", "application": "Post Goods Receipt for Purchasing Document",
            "business_impact": "O usuário não encontra o item para iniciar o recebimento no aplicativo.",
            "expected_result": "Localizar o item do pedido para analisar o recebimento.",
            "actual_result": "O item 10 não aparece no aplicativo informado.",
            "steps_to_reproduce": ["Abrir Post Goods Receipt for Purchasing Document.",
                                   "Consultar o pedido 4500001004 e procurar o item 10."]},
    "C05": {"priority": None, "business_impact": None,
            "expected_result": "Receber o material sem o erro relatado.",
            "actual_result": "Erro relatado sem mensagem, aplicativo ou referência de pedido."},
    "C06": {"priority": "3", "error_message": "ZMM_999",
            "business_impact": "Usuário solicita análise da mensagem apresentada no recebimento.",
            "expected_result": "Obter análise da mensagem antes de qualquer correção.",
            "actual_result": "Foi relatada a mensagem ZMM_999; texto completo não informado."},
    "C07": {"priority": "4", "application": "Simulador de recebimento",
            "business_impact": "Solicitação interna de registro de uma entrega no ambiente fictício.",
            "expected_result": "Solicitar o registro das 10 UN após conferência e autorização.",
            "actual_result": "Solicitação de operação; execução ainda não confirmada."},
    "C08": {"priority": "4", "application": "Simulador de recebimento",
            "business_impact": "Solicitação interna de recebimento sujeita à decisão do usuário.",
            "expected_result": "Revisar a solicitação de recebimento de 5 UN.",
            "actual_result": "Solicitação de operação; decisão humana ainda não informada."},
}


def support_context(code):
    """Formato inspirado no SAP for Me; não representa um case enviado à SAP."""
    return {"reference": f"SIM-{code}", "sap_case_number": None,
            "product": "SAP S/4HANA", "product_version": None,
            "system_id": "QAS", "client": "100", "system_role": "Teste / qualidade",
            "component": "MM-IM-GR-PO", "component_confirmed": False,
            "customer": "Empresa de demonstração", "reporter": "Usuário de demonstração",
            "reported_at": "2026-10-18T09:00:00-03:00", "application": None,
            "error_message": None, "steps_to_reproduce": [], "actions_taken": [], "attachments": [],
            **deepcopy(CASE_CONTEXT[code])}

CASES = [
    ("C01", "Saldo após recebimento parcial", "Recebi 60 UN do pedido 4500001001, item 10. Por que ainda aparecem 40?", "100", "60"),
    ("C02", "Conferir uma entrega parcial", "Como registro as 25 UN que chegaram no pedido 4500001002, item 10?", "100", "20"),
    ("C03", "Quantidade acima do saldo", "Vieram 35 UN do pedido 4500001003, item 10, e não consigo registrar.", "100", "80"),
    ("C04", "Item não aparece no aplicativo", "O item 10 do pedido 4500001004 não aparece em Post Goods Receipt for Purchasing Document.", "100", "60"),
    ("C05", "Preciso de mais informações", "Está dando erro ao receber material.", None, None),
    ("C06", "Mensagem não documentada", "No recebimento do pedido 4500001006, item 10, apareceu ZMM_999. Qual correção faço?", "100", "0"),
    ("C07", "Registrar recebimento simulado", "Registre o recebimento de 10 UN no pedido 4500001007, item 10, em 2026-10-18.", "50", "20"),
    ("C08", "Revisar antes de autorizar", "Registre o recebimento de 5 UN no pedido 4500001008, item 10, em 2026-10-18.", "20", "0"),
]


def initial_state():
    tickets, orders = {}, {}
    for code, title, description, ordered, received in CASES:
        po = "450000100" + code[-1] if ordered else None
        tickets[code] = {"id": code, "title": title, "description": description,
                         "purchase_order": po, "item": "10" if po else None,
                         "status": "aberto", "version": 1, "support": support_context(code)}
        if po:
            orders[f"{po}/10"] = {
                "purchase_order": po, "item": "10", "material": f"MAT-{int(code[1:]):03}",
                "plant": "BR01", "storage_location": "D001", "unit": "UN",
                "ordered": ordered, "received": received, "delivery_completed": code == "C04", "version": 1,
            }
    return {"tickets": tickets, "orders": orders, "receipts": []}


"""Somente entradas do simulador; nenhum gabarito é entregue ao modelo."""

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
                         "status": "aberto", "version": 1}
        if po:
            orders[f"{po}/10"] = {
                "purchase_order": po, "item": "10", "material": f"MAT-{int(code[1:]):03}",
                "plant": "BR01", "storage_location": "D001", "unit": "UN",
                "ordered": ordered, "received": received, "delivery_completed": code == "C04", "version": 1,
            }
    return {"tickets": tickets, "orders": orders, "receipts": []}


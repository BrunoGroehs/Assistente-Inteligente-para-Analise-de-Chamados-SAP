"""Consultas e apresentação de chamados; não alteram o estado de negócio."""
from datetime import datetime
from decimal import Decimal
import json
import unicodedata

PRIORITIES = {"1": "Muito alta", "2": "Alta", "3": "Média", "4": "Baixa"}
LOCAL_STATUSES = {"aberto": "Aberto", "em_validacao_humana": "Em validação humana", "resolvido": "Resolvido"}
NOT_PROVIDED = "Não informado"


def case_reference(ticket):
    return ticket.get("support", {}).get("reference") or f"SIM-{ticket['id']}"


def priority_label(ticket):
    value = ticket.get("support", {}).get("priority")
    return f"{value} · {PRIORITIES[value]}" if value in PRIORITIES else NOT_PROVIDED


def case_order(state, ticket):
    return state["orders"].get(f"{ticket.get('purchase_order')}/{ticket.get('item')}")


def normalize(value):
    return unicodedata.normalize("NFKD", value.casefold()).encode("ascii", "ignore").decode()


def matching_cases(state, query="", priority=None):
    found = []
    for key, ticket in state["tickets"].items():
        current_priority = ticket.get("support", {}).get("priority")
        if priority == "missing" and current_priority:
            continue
        if priority and priority != "missing" and current_priority != priority:
            continue
        text = normalize(json.dumps([ticket, case_order(state, ticket), case_reference(ticket),
                                     priority_label(ticket), LOCAL_STATUSES.get(ticket["status"], ticket["status"])],
                                    ensure_ascii=False))
        if all(term in text for term in normalize(query).split()):
            found.append(key)
    return found


def case_rows(state, keys):
    return [{"Chamado": case_reference(state["tickets"][key]),
             "Resumo": state["tickets"][key]["title"],
             "Prioridade": priority_label(state["tickets"][key]),
             "Situação local": LOCAL_STATUSES[state["tickets"][key]["status"]],
             "Sistema": state["tickets"][key].get("support", {}).get("system_id") or NOT_PROVIDED,
             "Componente sugerido": state["tickets"][key].get("support", {}).get("component") or NOT_PROVIDED}
            for key in keys]


def occurrence_label(value):
    if not value:
        return NOT_PROVIDED
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y %H:%M %z")
    except (TypeError, ValueError):
        return NOT_PROVIDED


def order_summary(order):
    if not order:
        return NOT_PROVIDED
    remaining = Decimal(order["ordered"]) - Decimal(order["received"])
    return (f"Pedido {order['purchase_order']} · Item {order['item']} · {order['material']}\n\n"
            f"Centro {order['plant']} · Depósito {order['storage_location']} · Unidade {order['unit']}\n\n"
            f"Pedido: {order['ordered']} · Recebido: {order['received']} · Saldo: {remaining:f}\n\n"
            f"Entrega concluída: {'Sim' if order['delivery_completed'] else 'Não'} · Versão {order['version']}")

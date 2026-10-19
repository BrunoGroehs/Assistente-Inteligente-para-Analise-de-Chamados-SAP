"""Perguntas sobre o estado da aplicação, sem diagnóstico ou procedimento SAP."""
import re
import unicodedata

from .approvals import quantity_text
from decimal import Decimal


def asks_attachment_context(message):
    text = unicodedata.normalize("NFKD", message.casefold()).encode("ascii", "ignore").decode()
    text = re.sub(r"[?!.,;:]", " ", text)
    text = " ".join(text.split())
    # Somente perguntas fechadas sobre a UI. Um pedido técnico adicional deve
    # continuar pela recuperação/cobertura, sem escapar por mencionar "anexo".
    return bool(re.fullmatch(
        r"(?:(?:qual|que)(?: e o| o)? (?:chamado|caso) (?:(?:esta|foi) )?anexado"
        r"|(?:tem|ha|existe) algum (?:chamado|caso) anexado|o que esta anexado)"
        r"(?: (?:aqui|nesta conversa|neste chat|no chat))?"
        r"(?: e qual (?:o )?saldo (?:(?:foi|esta) )?consultado(?: nesta conversa| neste chat)?)?", text))


def attachment_context_answer(ticket, order):
    if not ticket:
        return "Nenhum chamado está anexado nesta conversa. Não consultei um pedido para esta pergunta. Use Chamados para anexar um caso."
    reference = ticket.get("support", {}).get("reference") or "SIM-" + ticket["id"]
    answer = f"O chamado anexado é {reference}: {ticket['title']}."
    if order:
        remaining = quantity_text(Decimal(order["ordered"]) - Decimal(order["received"]))
        answer += (f" Nesta consulta ao simulador, o pedido {order['purchase_order']}, item {order['item']}, "
                   f"tem saldo de {remaining} {order['unit']}.")
    else:
        answer += " Não há pedido/item identificado para consultar o saldo."
    return answer

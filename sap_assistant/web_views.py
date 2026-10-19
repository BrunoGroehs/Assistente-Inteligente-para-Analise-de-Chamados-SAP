"""Projeção pública da interface, sem conteúdo bruto do RAG ou credenciais."""
import json

from .cases import case_order, case_reference, priority_label
from .citations import message_citations, source_groups
from .presentation import visible_proposals
from .database import utcnow
from .corrections import public_correction


def public_snapshot(snapshot):
    state = snapshot["state"]
    cases = [{**ticket, "reference": case_reference(ticket), "priority_label": priority_label(ticket),
              "order": case_order(state, ticket)} for ticket in state["tickets"].values()]
    messages = []
    for message in snapshot["messages"]:
        details = message["details"]
        analysis = details.get("analysis") or {}
        citations = message_citations(details)
        transactions = []
        for evidence in details.get("evidence", []):
            if evidence["kind"] == "consulta_simulada":
                value = json.loads(evidence["content"])
                fields = ("purchase_order", "item", "material", "ordered", "received", "remaining", "unit",
                          "plant", "storage_location")
                transactions.append({key: value.get(key) for key in fields})
        attachment = details.get("attachment")
        if attachment is None and message["ticket"] in state["tickets"]:
            ticket = state["tickets"][message["ticket"]]
            attachment = {"id": ticket["id"], "reference": case_reference(ticket), "title": ticket["title"]}
        messages.append({"id": message["id"], "role": message["role"], "content": message["content"],
            "attachment": attachment, "error": bool(details.get("error")), "proposal_id": details.get("proposal_id"),
            "correction": public_correction(details.get("correction")),
            "details": {"confidence": analysis.get("confidence"), "confidence_reason": analysis.get("confidence_reason"),
                "facts": [{"text": fact["text"], "numbers": [i for i, source in enumerate(citations, 1)
                            if source.id in fact["evidence_ids"]]} for fact in analysis.get("facts", [])],
                "hypotheses": analysis.get("hypotheses", []), "missing_information": analysis.get("missing_information", []),
                "next_steps": analysis.get("next_steps", []), "sources": source_groups(details),
                "consulted_sources": source_groups(details, cited=False),
                "policies": [{"number": i, "title": item.title} for i, item in enumerate(citations, 1)
                             if item.kind == "politica_da_simulacao"],
                "transactions": transactions, "steps": [x["step"] for x in details.get("steps", [])],
                "latency_ms": details.get("latency_ms")}})
    proposals = [{"id": item["id"], "ticket": item["ticket"], "state": item["state"],
                  "expires_at": item["expires_at"], "phrase": item["payload"]["request"]["confirmation_phrase"],
                  "effect": item["payload"]["effect"], "result": item["result"]}
                 for item in visible_proposals(snapshot["proposals"])]
    return {"cases": cases, "messages": messages, "proposals": proposals, "server_time": utcnow().isoformat()}

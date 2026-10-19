"""Citações derivadas exclusivamente do snapshot de evidências do atendimento."""
import re

from .contracts import Evidence

KNOWLEDGE_KINDS = {"sintese_de_fonte_oficial", "politica_da_simulacao"}


def cited_knowledge(analysis, evidence):
    by_id = {item.id: item for item in evidence if item.kind in KNOWLEDGE_KINDS}
    # A ordem é a das referências validadas, não um título ou URL gerado pela IA.
    return [by_id[key] for key in dict.fromkeys(analysis.references) if key in by_id]


def message_citations(details):
    references = details.get("analysis", {}).get("references", [])
    by_id = {item["id"]: item for item in details.get("evidence", [])
             if item.get("kind") in KNOWLEDGE_KINDS}
    return [Evidence.model_validate(by_id[key]) for key in dict.fromkeys(references) if key in by_id]


def safe_answer_text(value):
    """Links de fontes são montados pelo servidor; texto da IA não carrega imagens/URLs."""
    value = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", value)
    return re.sub(r"https?://[^\s<>]+", "", value)

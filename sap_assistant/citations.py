"""Citações derivadas exclusivamente do snapshot de evidências do atendimento."""
import re
from urllib.parse import urlsplit

from .contracts import Evidence

KNOWLEDGE_KINDS = {"sintese_de_fonte_oficial", "politica_da_simulacao"}
SOURCE_HOSTS = {"learning.sap.com", "help.sap.com", "userapps.support.sap.com"}


def official_url(value):
    try:
        url = urlsplit(value or "")
        return value if (url.scheme == "https" and url.hostname in SOURCE_HOSTS
                         and not url.username and not url.password and url.port in (None, 443)) else None
    except ValueError:
        return None


def cited_knowledge(analysis, evidence):
    by_id = {item.id: item for item in evidence if item.kind in KNOWLEDGE_KINDS}
    # A ordem é a das referências validadas, não um título ou URL gerado pela IA.
    return [by_id[key] for key in dict.fromkeys(analysis.references) if key in by_id]


def message_citations(details):
    references = details.get("analysis", {}).get("references", [])
    by_id = {item["id"]: item for item in details.get("evidence", [])
             if item.get("kind") in KNOWLEDGE_KINDS}
    return [Evidence.model_validate(by_id[key]) for key in dict.fromkeys(references) if key in by_id]


def source_groups(details, cited=True):
    """Agrupa links por URL sem devolver o conteúdo dos documentos para a UI."""
    citations = message_citations(details)
    numbers = {item.id: index for index, item in enumerate(citations, 1)}
    used_urls = {official_url(x.source_url) for x in citations}
    evidence = citations if cited else [Evidence.model_validate(x) for x in details.get("evidence", [])
                                       if x.get("id") not in numbers and x.get("kind") == "sintese_de_fonte_oficial"]
    groups = {}
    for item in evidence:
        url = official_url(item.source_url)
        if item.kind != "sintese_de_fonte_oficial" or not url or (not cited and url in used_urls):
            continue
        group = groups.setdefault(url, {"url": url, "title": item.title, "numbers": [], "ids": []})
        group["ids"].append(item.id)
        if item.id in numbers:
            group["numbers"].append(numbers[item.id])
    return list(groups.values())


def safe_answer_text(value):
    """Links de fontes são montados pelo servidor; texto da IA não carrega imagens/URLs."""
    value = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", value)
    return re.sub(r"https?://[^\s<>]+", "", value)

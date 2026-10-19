"""Verificação de cobertura do RAG e respostas de abstinência do servidor."""
from typing import Literal

from pydantic import Field

from .contracts import Analysis, Contract

INSUFFICIENT_MESSAGE = "Não tenho informações suficientes na base de conhecimento para responder a esta solicitação com segurança."


class KnowledgeSupport(Contract):
    evidence_id: str
    span_id: str


class KnowledgeAssessment(Contract):
    scope: Literal["recebimento_pedido_compra", "fora_do_escopo"]
    sufficient: bool
    supports: list[KnowledgeSupport] = Field(max_length=6)
    reason: str = Field(min_length=1, max_length=1200)


def insufficient_assessment(reason):
    return KnowledgeAssessment(scope="recebimento_pedido_compra", sufficient=False, supports=[], reason=reason)


def knowledge_spans(evidence):
    paragraphs = [x.strip() for x in evidence.content.split("\n\n")
                  if len(x.strip()) >= 25 and not x.lstrip().startswith(("#", "Síntese própria", "Política própria"))]
    return [{"id": f"{evidence.id}:{index}", "text": text} for index, text in enumerate(paragraphs, 1)]


def supported_ids(assessment, evidence):
    """Uma decisão positiva exige prova literal nos trechos recuperados."""
    if not assessment.sufficient or assessment.scope == "fora_do_escopo":
        return []
    by_id = {item.id: item for item in evidence
             if item.kind in {"sintese_de_fonte_oficial", "politica_da_simulacao"}}
    if not assessment.supports:
        raise ValueError("Cobertura suficiente exige trecho de conhecimento.")
    for support in assessment.supports:
        item = by_id.get(support.evidence_id)
        if not item or support.span_id not in {span["id"] for span in knowledge_spans(item)}:
            raise ValueError("Trecho de suporte ausente no conhecimento recuperado.")
    return list(dict.fromkeys(x.evidence_id for x in assessment.supports))


def insufficient_analysis():
    # Texto técnico, hipóteses e propostas do modelo não chegam ao usuário neste caminho.
    return Analysis(summary=INSUFFICIENT_MESSAGE, process="recebimento_pedido_compra", facts=[],
                    hypotheses=[], missing_information=["Você pode informar a mensagem completa, o aplicativo e a versão utilizada?"],
                    next_steps=["Compartilhe uma fonte confiável ou documentação do caso para complementar a base."],
                    references=[], confidence="baixa", confidence_reason="O RAG não forneceu suporte suficiente para a pergunta atual.",
                    human_review=True, action=None)


def out_of_scope_analysis():
    return Analysis(summary="Este assistente atende recebimento de mercadorias com referência a pedidos de compra em SAP MM. "
                    "Sua solicitação está fora desse escopo.", process="fora_do_escopo", facts=[], hypotheses=[],
                    missing_information=[], next_steps=["Para analisar um recebimento, informe o pedido, o item e o problema apresentado."],
                    references=[], confidence="alta", confidence_reason="Aplicação do escopo configurado, sem diagnóstico SAP.",
                    human_review=False, action=None)

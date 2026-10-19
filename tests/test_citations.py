from copy import deepcopy

from sap_assistant.citations import message_citations, safe_answer_text
from sap_assistant.contracts import Analysis, Evidence, Fact
from sap_assistant.service import render_analysis


def analysis(references):
    return Analysis(summary="Conferir o recebimento.", process="recebimento_pedido_compra",
                    facts=[Fact(text="Conferir a quantidade", evidence_ids=["K02", "DATA"])],
                    hypotheses=[], missing_information=[], next_steps=[], references=references,
                    confidence="media", confidence_reason="Evidências parciais.", human_review=False, action=None)


def evidence():
    return [Evidence(id="K02", title="Quantidades", content="Trecho original\nSegunda linha.",
                     kind="sintese_de_fonte_oficial", source_url="https://learning.sap.com/", version="v1"),
            Evidence(id="K05", title="Políticas", content="Não ultrapassar o saldo.",
                     kind="politica_da_simulacao", version="v2"),
            Evidence(id="DATA", title="Consulta", content="{}", kind="consulta_simulada", version="1")]


def test_only_cited_knowledge_generates_citations():
    details = {"analysis": {"references": ["DATA", "K02", "K02", "INVENTADO"]},
               "evidence": [x.model_dump() for x in evidence()]}
    citations = message_citations(details)
    assert [x.id for x in citations] == ["K02"]
    assert citations[0].content == "Trecho original\nSegunda linha."


def test_numbering_matches_order_of_valid_citations():
    result = render_analysis(analysis(["K05", "DATA", "K02"]), evidence())
    assert "Conferir a quantidade [2]" in result
    assert "DATA" not in result


def test_popup_content_is_an_independent_historical_snapshot():
    snapshot = {"analysis": {"references": ["K02"]}, "evidence": [x.model_dump() for x in evidence()]}
    original = deepcopy(snapshot)
    citation = message_citations(snapshot)[0]
    snapshot["evidence"][0]["content"] = "Texto alterado em outro objeto"
    assert citation.content == original["evidence"][0]["content"]
    assert citation.version == "v1"
    assert citation.source_url == "https://learning.sap.com/"


def test_policy_has_no_fabricated_official_link():
    citations = message_citations({"analysis": {"references": ["K05"]},
                                  "evidence": [x.model_dump() for x in evidence()]})
    assert citations[0].kind == "politica_da_simulacao" and citations[0].source_url is None


def test_no_citations_when_nothing_used_or_response_failed():
    assert not message_citations({"evidence": [x.model_dump() for x in evidence()]})
    assert not message_citations({"analysis": {"references": []}, "evidence": [x.model_dump() for x in evidence()]})


def test_model_text_cannot_create_unverified_source_links_or_images():
    value = "Veja [fonte inventada](https://example.invalid/secret) ![imagem](https://example.invalid/image)"
    assert "https://" not in safe_answer_text(value)
    answer = analysis(["K02"])
    answer.summary = value
    assert "example.invalid" not in render_analysis(answer, evidence())

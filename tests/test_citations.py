from copy import deepcopy

from sap_assistant.citations import message_citations, official_url, safe_answer_text, source_groups
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
    result = render_analysis(analysis(["K05", "DATA", "K02"]), evidence(), detailed=True)
    assert "Conferir a quantidade [2]" in result
    assert "DATA" not in result


def test_source_is_an_independent_historical_snapshot():
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


def test_inline_citation_links_only_to_catalog_source():
    result = render_analysis(analysis(["K02", "DATA"]), evidence())
    assert "[1](https://learning.sap.com/)" in result


def test_links_group_same_official_url_without_document_content():
    items = evidence()
    second = items[0].model_copy(update={"id": "K01", "title": "Outro guia"})
    details = {"analysis": {"references": ["K02", "K01", "K05"]},
               "evidence": [x.model_dump() for x in [*items, second]]}
    groups = source_groups(details)
    assert len(groups) == 1 and groups[0]["numbers"] == [1, 2]
    assert "content" not in groups[0]
    assert not source_groups(details, cited=False)


def test_unused_sources_are_separate_and_unsafe_links_rejected():
    details = {"analysis": {"references": ["DATA"]}, "evidence": [x.model_dump() for x in evidence()]}
    assert not source_groups(details)
    assert len(source_groups(details, cited=False)) == 1
    for url in ["javascript:alert(1)", "https://example.invalid", "https://learning.sap.com@evil.invalid/",
                "http://learning.sap.com/", "https://user:password@help.sap.com/"]:
        assert official_url(url) is None


def test_compact_answer_has_citations_and_one_next_step_with_full_details_available():
    answer = analysis(["K02", "DATA"])
    answer.next_steps = ["Confira a quantidade entregue.", "Segunda verificação de apoio."]
    compact = render_analysis(answer, evidence())
    detailed = render_analysis(answer, evidence(), detailed=True)
    assert compact.startswith(answer.summary) and "[1](https://learning.sap.com/)" in compact
    assert "Confira a quantidade entregue." in compact and "Segunda verificação" not in compact
    assert "Fatos consultados" not in compact and "Próximos passos" not in compact
    assert "Conferir a quantidade" in detailed and "Segunda verificação" in detailed


def test_compact_answer_keeps_clarification_and_human_review_visible():
    answer = analysis([])
    answer.missing_information = ["Qual é a mensagem completa?", "Em qual aplicativo ocorreu?"]
    answer.human_review = True
    compact = render_analysis(answer)
    assert all(item in compact for item in answer.missing_information)
    assert "validação humana" in compact

"""Novo chat e resposta compacta com Supabase/OpenRouter reais; consome créditos.

As propostas são entradas controladas de teste e as decisões são cliques AppTest,
não consentimento de uma pessoa. Usa somente uma sessão fictícia própria.
"""
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from streamlit.testing.v1 import AppTest

from sap_assistant import runtime
from sap_assistant.approvals import canonical_phrase
from sap_assistant.config import Settings
from sap_assistant.contracts import ReceiptRequest
from sap_assistant.database import AccessDenied

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings.load()
    services = runtime.create_runtime(settings)
    store, service, gateway = services
    report = {"mode": __doc__, "checks": [], "api_calls": {},
              "prompt_version": (ROOT / "prompts/system.txt").read_text(encoding="utf-8").splitlines()[0]}
    path = ROOT / "evidencias/verificacao-novo-chat.json"

    def count(request):
        endpoint = request.url.path.rsplit("/", 1)[-1]
        report["api_calls"][endpoint] = report["api_calls"].get(endpoint, 0) + 1

    service.provider.client.event_hooks["request"].append(count)

    def check(name, function):
        try:
            entry = {"check": name, "passed": True, "details": function() or {}}
        except Exception as exc:
            entry = {"check": name, "passed": False, "error_type": type(exc).__name__}
            import traceback
            frames = [x for x in traceback.extract_tb(exc.__traceback__) if x.filename == __file__]
            entry["harness_line"] = frames[-1].lineno if frames else None
        report["checks"].append(entry)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"check": name, "passed": entry["passed"]}, ensure_ascii=False), flush=True)
        return entry["passed"]

    def click(label):
        next(x for x in app.button if x.label == label).click().run(timeout=180)
        assert not app.exception and not app.error

    def ask(question):
        app.chat_input[0].set_value(question).run(timeout=180)
        assert not app.exception and not app.error
        current = store.snapshot(context, app.session_state["active_chat_id"] if "active_chat_id" in app.session_state else None)
        message = current["messages"][-1]
        assert not message["details"].get("error")
        assert message["details"]["analysis"]["references"]
        assert len(app.expander) == len(app.chat_message) // 2
        assert all(x.label == "Fontes e detalhes" and not x.proto.expanded for x in app.expander)
        return message

    st.cache_resource.clear()
    try:
        with patch.object(runtime, "create_runtime", lambda _: services):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
            if settings.access_code:
                app.session_state["access_granted"] = True
            app.run()
            context = app.session_state["context"]
            initial = store.state(context)
            data = initial["orders"]["4500001007/10"]
            request = ReceiptRequest(operation="registrar_recebimento_simulado", parameters={
                **{key: data[key] for key in ("purchase_order", "item", "unit", "material", "plant", "storage_location")},
                "quantity": "10", "posting_date": "2026-10-18"}, confirmation_phrase="Frase a preencher")
            request.confirmation_phrase = canonical_phrase(request, "C07")
            old_question = "O que é recebimento com referência ao pedido de compra?"
            scope = {}

            def compact():
                message = ask(old_question)
                answer = message["details"]["analysis"]
                assert len(answer["summary"].split()) <= 100 and len(answer["next_steps"]) <= 1
                assert "**Fatos consultados**" not in message["content"]
                assert app.get("link_button") and store.state(context) == initial
                return {"summary_words": len(answer["summary"].split()), "next_steps": len(answer["next_steps"]),
                        "one_collapsed_details_per_answer": True, "analysis": answer}

            def fresh():
                old = gateway.propose(context, "C07", request)
                scope["old"] = old
                click("Atualizar")
                click("Anexar SIM-C07")
                assert app.chat_input[0].disabled
                before_calls = dict(report["api_calls"])
                click("Novo chat")
                scope["new"] = app.session_state["active_chat_id"]
                assert not app.chat_message and not app.chat_input[0].disabled
                assert app.session_state["attached_case"] is None
                assert app.session_state["context"] == context and store.state(context) == initial
                assert report["api_calls"] == before_calls
                assert len(store.snapshot(context)["messages"]) == 2
                assert store.snapshot(context)["proposals"][0]["state"] == "pendente"
                return {"same_business_state": True, "previous_history_and_proposal_preserved": True,
                        "no_llm_call_on_new_chat": True}

            def new_answer():
                original = service.provider.analyze

                def inspect(ctx, history):
                    assert not any(x["content"] == old_question for x in history)
                    return original(ctx, history)

                with patch.object(service.provider, "analyze", inspect):
                    message = ask("Que documento é gerado ao receber mercadorias com pedido de compra?")
                assert len(app.chat_message) == 2 and message["details"]["chat_id"] == scope["new"]
                assert len(store.messages(context)) == 4
                assert not store.snapshot(context, scope["new"])["proposals"]
                return {"postgres_json_chat_filter": True, "previous_user_question_excluded_from_llm_history": True,
                        "analysis": message["details"]["analysis"]}

            def approval():
                try:
                    gateway.decide(context, scope["old"], True, chat_id=scope["new"])
                    raise AssertionError()
                except AccessDenied:
                    pass
                new = gateway.propose(context, "C07", request, chat_id=scope["new"])
                assert new != scope["old"]
                click("Atualizar")
                click("Anexar SIM-C07")
                click("Sim, autorizar")
                assert len(store.state(context)["receipts"]) == 1
                assert store.snapshot(context)["proposals"][0]["state"] == "pendente"
                assert store.snapshot(context, scope["new"])["proposals"][0]["state"] == "executada"
                app.run()
                assert len(store.state(context)["receipts"]) == 1
                return {"wrong_chat_rejected": True, "proposal_not_reused": True, "one_execution": True,
                        "decision": "simulada pelo harness; proposta controlada"}

            for name, function in [("Resposta compacta com fontes acessíveis", compact),
                                   ("Novo chat limpa conversa e anexo sem mudar negócio", fresh),
                                   ("Nova resposta usa somente o histórico da nova conversa", new_answer),
                                   ("Aprovação permanece ligada à conversa original", approval)]:
                if not check(name, function):
                    break
    except Exception as exc:
        report["setup_error_type"] = type(exc).__name__
    finally:
        report["passed"] = (len(report["checks"]) == 4 and all(x["passed"] for x in report["checks"])
                            and "setup_error_type" not in report)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        st.cache_resource.clear()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

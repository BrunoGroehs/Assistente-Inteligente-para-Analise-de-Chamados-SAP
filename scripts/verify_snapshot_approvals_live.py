"""Confere cache de apresentação e HITL no Supabase real, sem consumir LLM.

Propostas controladas e cliques automatizados são exclusivos do teste; não são
consentimento humano. Cada cenário usa uma sessão fictícia nova deste projeto.
"""
from copy import deepcopy
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

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings.load()
    services = runtime.create_runtime(settings)
    store, _, gateway = services
    report = {"mode": __doc__, "checks": [], "openrouter_calls": 0}
    path = ROOT / "evidencias/aprovacoes-com-cache-supabase.json"
    st.cache_resource.clear()
    try:
        with patch.object(runtime, "create_runtime", lambda _: services):
            for scenario in ("aprovar", "recusar", "dados_alterados"):
                try:
                    context = store.create_workspace()
                    data = store.state(context)["orders"]["4500001007/10"]
                    request = ReceiptRequest(operation="registrar_recebimento_simulado", parameters={
                        **{key: data[key] for key in ("purchase_order", "item", "unit", "material", "plant", "storage_location")},
                        "quantity": "10", "posting_date": "2026-10-18"}, confirmation_phrase="Frase a preencher")
                    request.confirmation_phrase = canonical_phrase(request, "C07")
                    proposal_id = gateway.propose(context, "C07", request)
                    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
                    app.session_state["context"] = context
                    if settings.access_code:
                        app.session_state["access_granted"] = True
                    app.run()
                    next(x for x in app.button if x.label == "Anexar SIM-C07").click().run()
                    assert not app.exception and not app.error and app.chat_input[0].disabled
                    if scenario == "dados_alterados":
                        with store.transaction() as db:
                            workspace = store.authorize(db, context, lock=True)
                            changed = deepcopy(workspace.data)
                            changed["orders"]["4500001007/10"]["received"] = "21"
                            workspace.data = changed
                    label = "Não, recusar" if scenario == "recusar" else "Sim, autorizar"
                    next(x for x in app.button if x.label == label).click().run()
                    assert not app.exception and not app.error
                    state = store.state(context)
                    result = store.proposals(context, "C07")[0]["state"]
                    expected = {"aprovar": "executada", "recusar": "recusada", "dados_alterados": "invalidada"}[scenario]
                    assert result == expected
                    assert len(state["receipts"]) == (1 if scenario == "aprovar" else 0)
                    assert app.session_state["ui_view"]["snapshot"]["state"] == state
                    app.run()
                    assert store.state(context) == state and gateway.decide(context, proposal_id, True)["state"] == expected
                    report["checks"].append({"scenario": scenario, "passed": True, "result": result,
                                              "ui_refreshed": True, "rerun_does_not_repeat": True})
                except Exception as exc:
                    report["checks"].append({"scenario": scenario, "passed": False, "error_type": type(exc).__name__})
                print(json.dumps(report["checks"][-1], ensure_ascii=False), flush=True)
    finally:
        st.cache_resource.clear()
        report["passed"] = len(report["checks"]) == 3 and all(x["passed"] for x in report["checks"])
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

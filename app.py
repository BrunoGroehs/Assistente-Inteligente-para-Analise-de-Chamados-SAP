from datetime import datetime
import hmac
from zoneinfo import ZoneInfo

import streamlit as st

from sap_assistant.config import Settings
from sap_assistant.citations import message_citations, safe_answer_text, source_groups
from sap_assistant.cases import (
    NOT_PROVIDED, PRIORITIES, case_order, case_reference, case_rows, matching_cases,
    occurrence_label, order_summary, priority_label,
)
from sap_assistant.database import AccessDenied, DatabaseSetupError, new_id
from sap_assistant.presentation import visible_proposals
from sap_assistant.contracts import Analysis, Evidence
from sap_assistant.service import render_analysis
from sap_assistant import runtime

st.set_page_config(page_title="Assistente SAP", page_icon="◦", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1080px; padding-top: 2.6rem; padding-bottom: 5rem;}
h1 {letter-spacing: -0.035em; font-weight: 650 !important;}
h2,h3 {letter-spacing: -0.02em;}
button {border-radius: 12px !important;}
[data-testid="stChatMessage"] {border-radius: 16px;}
</style>""", unsafe_allow_html=True)

LABELS = {"aberto": "Aberto", "em_validacao_humana": "Em validação humana", "resolvido": "Resolvido",
          "pendente": "Aguardando aprovação", "recusada": "Recusada", "expirada": "Expirada",
          "invalidada": "Invalidada", "executada": "Executada", "falhou": "Falhou"}


@st.cache_resource(show_spinner=False)
def get_runtime(settings):
    return runtime.create_runtime(settings)


def configuration_screen(message):
    st.title("Assistente SAP")
    st.caption("MM · Recebimento de mercadorias")
    st.info(message)
    st.write("Configure o arquivo `.env` local ou os secrets do Streamlit Cloud conforme o README.")
    st.write("O aplicativo usa PostgreSQL no Supabase e os modelos Qwen pelo OpenRouter.")
    st.stop()


def invalidate_view():
    st.session_state.pop("ui_view", None)


def get_view(store, context):
    cached = st.session_state.get("ui_view")
    chat_id = st.session_state.get("active_chat_id")
    if cached is None or cached["context"] != context or cached.get("chat_id") != chat_id:
        cached = {"context": context, "chat_id": chat_id, "snapshot": store.snapshot(context, chat_id)}
        st.session_state.ui_view = cached
    return cached["snapshot"]


def close_case_selector():
    st.session_state.case_selector_open = False


def new_chat():
    st.session_state.active_chat_id = new_id()
    st.session_state.attached_case = None
    close_case_selector()
    invalidate_view()


def clear_case_row(table_key):
    st.session_state[table_key] = {"selection": {"rows": [], "columns": [], "cells": []}}


def attach_case(case_id, allowed):
    if case_id not in allowed:
        raise ValueError("Chamado não disponível nesta sessão.")
    st.session_state.attached_case = case_id
    close_case_selector()


def detach_case():
    st.session_state.attached_case = None
    close_case_selector()


def open_case_selector(case_id=None, details=False):
    st.session_state.dialog_case = case_id
    st.session_state.dialog_search = ""
    st.session_state.dialog_priority = "all"
    st.session_state.dialog_details = details
    st.session_state.case_selector_open = True


def display_case_details(state, key):
    ticket = state["tickets"][key]
    profile = ticket.get("support", {})
    st.markdown(f"**{case_reference(ticket)} · {ticket['title']}**")
    st.write(ticket["description"])
    left, right = st.columns(2)
    with left:
        st.markdown("**Identificação e ambiente**")
        st.write("Produto: " + (profile.get("product") or NOT_PROVIDED))
        st.write("Versão / release: " + (profile.get("product_version") or NOT_PROVIDED))
        st.write("Sistema: " + (profile.get("system_id") or NOT_PROVIDED))
        st.write("Mandante: " + (profile.get("client") or NOT_PROVIDED))
        st.write("Ambiente: " + (profile.get("system_role") or NOT_PROVIDED))
        st.write("Aplicativo: " + (profile.get("application") or NOT_PROVIDED))
    with right:
        st.markdown("**Atendimento**")
        st.write("Situação local: " + LABELS[ticket["status"]])
        st.write("Prioridade: " + priority_label(ticket))
        st.write("Componente sugerido: " + (profile.get("component") or NOT_PROVIDED))
        st.write("Solicitante: " + (profile.get("reporter") or NOT_PROVIDED))
        st.write("Empresa: " + (profile.get("customer") or NOT_PROVIDED))
        st.write("Ocorrência informada: " + occurrence_label(profile.get("reported_at")))
        st.caption("Case SAP: " + (profile.get("sap_case_number") or "Não enviado ao SAP for Me"))
    st.markdown("**Impacto no negócio**")
    st.write(profile.get("business_impact") or NOT_PROVIDED)
    expected, actual = st.columns(2)
    with expected:
        st.markdown("**Resultado esperado pelo solicitante**")
        st.write(profile.get("expected_result") or NOT_PROVIDED)
    with actual:
        st.markdown("**Resultado relatado na abertura**")
        st.write(profile.get("actual_result") or NOT_PROVIDED)
    st.markdown("**Mensagem de erro informada**")
    if profile.get("error_message"):
        st.code(profile["error_message"], language=None)
    else:
        st.write(NOT_PROVIDED)
    st.markdown("**Passos de reprodução informados**")
    steps = profile.get("steps_to_reproduce", [])
    for index, step in enumerate(steps, 1):
        st.write(f"{index}. {step}")
    if not steps:
        st.write(NOT_PROVIDED)
    st.markdown("**Ações já tentadas**")
    st.write(" · ".join(profile.get("actions_taken", [])) or NOT_PROVIDED)
    st.markdown("**Pedido e quantidades atuais no simulador**")
    st.write(order_summary(case_order(state, ticket)))
    st.caption("Anexos: " + (", ".join(profile.get("attachments", [])) or "Nenhum anexo"))


@st.dialog("Chamados", width="large", icon=":material/confirmation_number:", on_dismiss=close_case_selector)
def case_selector(state):
    search, priority_column = st.columns([3, 1])
    query = search.text_input("Buscar chamado", placeholder="Número, resumo, pedido ou componente", key="dialog_search")
    priority = priority_column.selectbox("Prioridade", ["all", *PRIORITIES, "missing"], key="dialog_priority",
        format_func=lambda value: "Todas" if value == "all" else ("Não informada" if value == "missing" else f"{value} · {PRIORITIES[value]}"))
    keys = matching_cases(state, query, None if priority == "all" else priority)
    st.caption(f"{len(keys)} de {len(state['tickets'])} chamados · Dados fictícios")
    if keys:
        table_key = "case_table_" + "_".join(keys)
        selection = st.dataframe(case_rows(state, keys), hide_index=True, width="stretch", key=table_key,
                                 on_select="rerun", selection_mode="single-row")
        rows = selection.selection.rows
        if rows and 0 <= rows[0] < len(keys):
            st.session_state.dialog_case = keys[rows[0]]
        if st.session_state.get("dialog_case") not in keys:
            st.session_state.dialog_case = keys[0]
        selected = st.selectbox("Chamado", keys, key="dialog_case", on_change=clear_case_row, args=(table_key,),
            format_func=lambda key: f"{case_reference(state['tickets'][key])} · {state['tickets'][key]['title']}")
        if st.button("Ver detalhes", icon=":material/description:"):
            st.session_state.dialog_details = not st.session_state.get("dialog_details", False)
        if st.session_state.get("dialog_details"):
            with st.container(height=400, border=False):
                display_case_details(state, selected)
        if st.button("Anexar ao chat", type="primary", icon=":material/attach_file:",
                     on_click=attach_case, args=(selected, list(state["tickets"]))):
            st.rerun()
    else:
        st.info("Nenhum chamado encontrado. Ajuste a busca.")
    if st.button("Cancelar", key="cancel_case_selector", on_click=close_case_selector):
        st.rerun()


def display_citations(details):
    citations = message_citations(details)
    if not citations:
        return
    st.markdown("**Fontes citadas**")
    for group in source_groups(details):
        numbers = ", ".join(str(x) for x in group["numbers"])
        st.link_button(f"[{numbers}] {group['title']}", group["url"], type="tertiary")
    policies = [f"[{i}] {item.title}" for i, item in enumerate(citations, 1) if item.kind == "politica_da_simulacao"]
    if policies:
        st.caption("Regras internas da simulação: " + "; ".join(policies))


def display_details(details):
    if not details.get("analysis") and not details.get("steps"):
        return
    with st.expander("Fontes e detalhes", expanded=False):
        analysis = details.get("analysis")
        evidence = [Evidence.model_validate(item) for item in details.get("evidence", [])]
        if analysis:
            parsed = Analysis.model_validate(analysis)
            confidence = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}[parsed.confidence]
            st.caption(f"Confiança {confidence.lower()} · {safe_answer_text(parsed.confidence_reason)}")
            supporting = render_analysis(parsed, evidence, detailed=True)
            if supporting:
                st.markdown(supporting)
        display_citations(details)
        transactions = [item for item in evidence if item.kind == "consulta_simulada"]
        if transactions:
            import json
            st.markdown("**Dados consultados**")
            for item in transactions:
                data = json.loads(item.content)
                st.write(f"Pedido {data['purchase_order']} · Item {data['item']} · {data['material']}")
                st.write(f"Pedido: {data['ordered']} {data['unit']} · Recebido: {data['received']} {data['unit']} · Saldo: {data['remaining']} {data['unit']}")
                st.caption(f"SAP simulado · Centro {data['plant']} · Depósito {data['storage_location']}")
        extra_sources = source_groups(details, cited=False)
        if extra_sources:
            st.markdown("**Referências consultadas**")
            st.caption("Recuperadas na busca; não usadas como fundamento desta resposta.")
            for group in extra_sources:
                st.link_button(group["title"], group["url"], type="tertiary")
        if details.get("steps"):
            st.markdown("**Etapas do atendimento**")
            for step in details["steps"]:
                st.write(step["step"])
            if "latency_ms" in details:
                st.caption(f"Duração medida: {details['latency_ms'] / 1000:.1f} s")


def approval_card(proposal, gateway, context, attached_case, tickets):
    state, payload = proposal["state"], proposal["payload"]
    with st.container(border=True):
        st.markdown(f"**{LABELS.get(state, state)}**")
        if state == "pendente":
            st.write(payload["request"]["confirmation_phrase"])
            effect = payload["effect"]
            if "purchase_order" in effect:
                st.write(f"Pedido {effect['purchase_order']} · Item {effect['item']} · {effect['material']}")
                st.caption(f"Centro {effect['plant']} · Depósito {effect['storage_location']} · Data {effect['posting_date']}")
                st.write(f"Receber {effect['quantity']} {effect['unit']} · Saldo: {effect['before']} → {effect['after']} {effect['unit']}")
            else:
                st.write(f"{effect['ticket']} · {LABELS.get(effect['before'], effect['before'])} → {LABELS[effect['after']]}")
            expiry = datetime.fromisoformat(proposal["expires_at"]).astimezone(ZoneInfo("America/Sao_Paulo"))
            st.caption(f"Somente no simulador · Válida até {expiry:%H:%M:%S} (Brasília)")
            if attached_case != proposal["ticket"]:
                key = proposal["ticket"]
                st.caption("Anexe o chamado correspondente para revisar e decidir esta solicitação.")
                st.button(f"Anexar {case_reference(tickets[key])}", key=f"review_{proposal['id']}",
                          icon=":material/attach_file:", on_click=attach_case, args=(key, list(tickets)))
                return
            yes, no = st.columns(2)
            decision = None
            if yes.button("Sim, autorizar", type="primary", key=f"yes_{proposal['id']}"):
                decision = True
            if no.button("Não, recusar", key=f"no_{proposal['id']}"):
                decision = False
            if decision is not None:
                try:
                    gateway.decide(context, proposal["id"], decision, chat_id=st.session_state.get("active_chat_id"))
                finally:
                    invalidate_view()
                st.rerun()
        else:
            st.write(proposal["result"].get("message", "Nenhuma autorização ativa para esta proposta."))
            if proposal["result"].get("receipt_id"):
                st.caption("Documento: " + proposal["result"]["receipt_id"])


def main():
    try:
        secrets = dict(st.secrets)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        secrets = {}
    try:
        settings = Settings.load(secrets)
        settings.validate()
    except ValueError as exc:
        configuration_screen(str(exc))

    if settings.access_code and not st.session_state.get("access_granted"):
        st.title("Assistente SAP")
        st.caption("Demonstração privada")
        with st.form("access"):
            code = st.text_input("Código de acesso", type="password")
            if st.form_submit_button("Entrar"):
                if hmac.compare_digest(code, settings.access_code):
                    st.session_state.access_granted = True
                    st.rerun()
                st.error("Código incorreto.")
        st.stop()

    try:
        store, assistant, gateway = get_runtime(settings)
        if "context" not in st.session_state:
            st.session_state.context = store.create_workspace()
        context = st.session_state.context
        view = get_view(store, context)
        state = view["state"]
    except AccessDenied:
        st.error("Esta sessão não pode ser retomada. Reabra a página para iniciar um novo ambiente.")
        st.stop()
    except DatabaseSetupError as exc:
        configuration_screen(str(exc))
    except Exception:
        configuration_screen("Não foi possível conectar ao banco. Confira a configuração Supabase e tente novamente.")

    # Um único chat. Anexo é contexto explícito das próximas mensagens, sem seleção automática.
    selected = st.session_state.get("attached_case")
    if selected not in state["tickets"]:
        selected = None
        st.session_state.attached_case = None
    ticket = state["tickets"].get(selected)
    messages = view["messages"]
    proposals = visible_proposals(view["proposals"])
    proposals_by_id = {item["id"]: item for item in proposals}
    pending = any(x["state"] == "pendente" and x["ticket"] == selected for x in proposals)
    heading, actions = st.columns([4, 1])
    heading.title("Assistente SAP")
    actions.button("Novo chat", icon=":material/edit_square:", key="new_chat", on_click=new_chat)
    st.caption("MM · Recebimento de mercadorias · Ambiente simulado")
    if not messages:
        st.write("Pergunte sobre o processo ou anexe um chamado para analisar o caso.")
    displayed_proposals = set()
    for message in messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                attachment = message["details"].get("attachment")
                if attachment is None and message["ticket"] in state["tickets"]:
                    original = state["tickets"][message["ticket"]]
                    attachment = {"reference": case_reference(original), "title": original["title"]}
                if attachment:
                    st.caption("Chamado anexado · " + attachment["reference"] + " · " + attachment["title"])
                else:
                    st.caption("Sem chamado anexado")
            if message["details"].get("error"):
                st.error(message["content"])
            else:
                st.markdown(message["content"])
            display_details(message["details"])
            proposal_id = message["details"].get("proposal_id")
            if proposal_id in proposals_by_id:
                approval_card(proposals_by_id[proposal_id], gateway, context, selected, state["tickets"])
                displayed_proposals.add(proposal_id)
    for proposal in proposals:
        if proposal["id"] not in displayed_proposals:
            approval_card(proposal, gateway, context, selected, state["tickets"])

    if not settings.api_key:
        st.info("Configure a chave OpenRouter para iniciar a análise com IA.")
    if pending:
        st.caption("Decida a solicitação pendente deste chamado antes de continuar sua análise. Você pode remover o anexo para fazer uma pergunta geral.")
    request = None
    with st.container(key="composer"):
        if ticket:
            with st.container(horizontal=True, vertical_alignment="center", border=True):
                st.button(case_reference(ticket) + " · " + ticket["title"], icon=":material/description:",
                          key="attached_case_details", type="tertiary", help="Ver detalhes do chamado anexado",
                          on_click=open_case_selector, args=(selected, True))
                st.button("Remover anexo", icon=":material/close:", key="detach_case", type="tertiary",
                          on_click=detach_case)
        with st.container(horizontal=True, vertical_alignment="center"):
            st.button("Chamados", icon=":material/confirmation_number:", help="Consultar e anexar um chamado",
                      key="open_case_selector", on_click=open_case_selector, args=(selected,))
            st.button("Atualizar", icon=":material/refresh:", key="refresh_view", type="tertiary",
                      help="Recarregar os dados da conversa", on_click=invalidate_view)
            if ticket and not any(x["ticket"] == selected for x in messages):
                if st.button("Analisar chamado", type="primary", disabled=not settings.api_key or pending):
                    request = ticket["description"]
            if not ticket:
                st.caption("Sem chamado anexado")
        typed = st.chat_input("Pergunte sobre o chamado…" if ticket else "Faça uma pergunta sobre SAP MM…",
                              key="chat_draft_" + (st.session_state.get("active_chat_id") or "inicial"),
                              disabled=not settings.api_key or pending, max_chars=6000)
    if st.session_state.get("case_selector_open"):
        case_selector(state)
    if typed:
        request = typed
    if request:
        try:
            with st.status("Consultando dados e fontes…", expanded=False) as status:
                assistant.analyze(context, selected, request, new_id(), on_progress=lambda label: status.update(label=label),
                                  chat_id=st.session_state.get("active_chat_id"))
                status.update(label="Atendimento atualizado", state="complete")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Não foi possível concluir o atendimento. Nenhuma ação de negócio foi autorizada por esta mensagem.")
        finally:
            invalidate_view()


try:
    main()
except Exception:
    st.error("Não foi possível carregar este atendimento. Confira a conexão e recarregue a página.")

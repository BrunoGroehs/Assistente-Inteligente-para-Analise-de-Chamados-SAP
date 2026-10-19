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
from sap_assistant import runtime

st.set_page_config(page_title="Assistente SAP", page_icon="◦", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1080px; padding-top: 2.6rem; padding-bottom: 5rem;}
h1 {letter-spacing: -0.035em; font-weight: 650 !important;}
h2,h3 {letter-spacing: -0.02em;}
button {border-radius: 12px !important;}
section[data-testid="stSidebar"] {border-right: 1px solid #e8e8ed;}
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


def show_chat():
    st.session_state.case_view = "chat"
    st.session_state.case_selector_open = False


def show_case_list():
    st.session_state.case_view = "list"
    st.session_state.case_selector_open = False


def close_case_selector():
    st.session_state.case_selector_open = False


def clear_case_row(table_key):
    st.session_state[table_key] = {"selection": {"rows": [], "columns": [], "cells": []}}


def activate_case(case_id, allowed):
    if case_id not in allowed:
        raise ValueError("Chamado não disponível nesta sessão.")
    st.session_state.selected_ticket = case_id
    show_chat()


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
    st.markdown("**Pedido e estoque atuais no simulador**")
    st.write(order_summary(case_order(state, ticket)))
    st.caption("Anexos: " + (", ".join(profile.get("attachments", [])) or "Nenhum anexo"))


@st.dialog("Selecionar chamado", width="large", icon=":material/confirmation_number:", on_dismiss=close_case_selector)
def case_selector(state):
    query = st.text_input("Buscar chamado", placeholder="Número, resumo, pedido ou componente", key="dialog_search")
    keys = matching_cases(state, query)
    if keys:
        selected = st.selectbox("Chamado", keys, key="dialog_case",
                                format_func=lambda key: f"{case_reference(state['tickets'][key])} · {state['tickets'][key]['title']}")
        with st.container(height=400, border=False):
            display_case_details(state, selected)
        if st.button("Abrir no chat", type="primary", icon=":material/chat:",
                     on_click=activate_case, args=(selected, list(state["tickets"]))):
            st.rerun()
    else:
        st.info("Nenhum chamado encontrado. Ajuste a busca.")
    if st.button("Cancelar", key="cancel_case_selector", on_click=close_case_selector):
        st.rerun()


def display_case_list(state):
    st.title("Chamados")
    st.caption("Casos fictícios inspirados no SAP for Me · Situações locais do atendimento")
    st.button("Voltar ao chat", icon=":material/chat:", on_click=show_chat)
    search, filter_column = st.columns([3, 1])
    query = search.text_input("Buscar na lista", placeholder="Resumo, pedido, material, sistema ou componente", key="list_search")
    priority = filter_column.selectbox("Prioridade", ["all", *PRIORITIES, "missing"], key="list_priority",
        format_func=lambda value: "Todas" if value == "all" else ("Não informada" if value == "missing" else f"{value} · {PRIORITIES[value]}"))
    keys = matching_cases(state, query, None if priority == "all" else priority)
    st.caption(f"{len(keys)} de {len(state['tickets'])} chamados")
    if not keys:
        st.info("Nenhum chamado encontrado com esses filtros.")
        return
    st.caption("Clique em uma linha para ver o caso completo, ou use o seletor abaixo.")
    table_key = "case_table_" + "_".join(keys)
    selection = st.dataframe(case_rows(state, keys), hide_index=True, width="stretch", key=table_key,
                             on_select="rerun", selection_mode="single-row")
    rows = selection.selection.rows
    if rows and 0 <= rows[0] < len(keys):
        st.session_state.list_case = keys[rows[0]]
    selected = st.selectbox("Ver todas as informações do chamado", keys, key="list_case",
                            on_change=clear_case_row, args=(table_key,),
                            format_func=lambda key: f"{case_reference(state['tickets'][key])} · {state['tickets'][key]['title']}")
    display_case_details(state, selected)
    st.button("Abrir no chat", key="open_from_case_list", icon=":material/chat:", type="primary",
              on_click=activate_case, args=(selected, list(state["tickets"])))


def display_citations(message):
    citations = message_citations(message["details"])
    if not citations:
        return
    with st.expander("Fontes citadas", expanded=True):
        for group in source_groups(message["details"]):
            numbers = ", ".join(str(x) for x in group["numbers"])
            st.link_button(f"[{numbers}] {group['title']}", group["url"], type="tertiary")
        policies = [f"[{i}] {item.title}" for i, item in enumerate(citations, 1) if item.kind == "politica_da_simulacao"]
        if policies:
            st.caption("Regras internas da simulação: " + "; ".join(policies))
        st.caption("Os links abrem a documentação oficial. As respostas usam sínteses próprias dessas fontes.")


def display_details(details):
    analysis = details.get("analysis", {})
    if analysis:
        confidence = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}.get(analysis["confidence"])
        st.caption(f"Confiança {confidence.lower()} · {safe_answer_text(analysis['confidence_reason'])}")
    evidence = details.get("evidence", [])
    transactions = [item for item in evidence if item["kind"] == "consulta_simulada"]
    if transactions:
        with st.expander("Dados consultados"):
            import json
            for item in transactions:
                data = json.loads(item["content"])
                st.write(f"Pedido {data['purchase_order']} · Item {data['item']} · {data['material']}")
                st.write(f"Pedido: {data['ordered']} {data['unit']} · Recebido: {data['received']} {data['unit']} · Saldo: {data['remaining']} {data['unit']}")
                st.caption(f"SAP simulado · Centro {data['plant']} · Depósito {data['storage_location']}")
    extra_sources = source_groups(details, cited=False)
    if extra_sources:
        with st.expander("Referências consultadas"):
            st.caption("Recuperadas na busca; não utilizadas como fundamento desta resposta.")
            for group in extra_sources:
                st.link_button(group["title"], group["url"], type="tertiary")
    if details.get("steps"):
        with st.expander("Etapas do atendimento"):
            for step in details["steps"]:
                st.write(step["step"])
            if "latency_ms" in details:
                st.caption(f"Duração medida: {details['latency_ms'] / 1000:.1f} s")


def approval_card(proposal, gateway, context):
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
            yes, no = st.columns(2)
            decision = None
            if yes.button("Sim, autorizar", type="primary", key=f"yes_{proposal['id']}"):
                decision = True
            if no.button("Não, recusar", key=f"no_{proposal['id']}"):
                decision = False
            if decision is not None:
                gateway.decide(context, proposal["id"], decision)
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
        state = store.state(context)
    except AccessDenied:
        st.error("Esta sessão não pode ser retomada. Reabra a página para iniciar um novo ambiente.")
        st.stop()
    except DatabaseSetupError as exc:
        configuration_screen(str(exc))
    except Exception:
        configuration_screen("Não foi possível conectar ao banco. Confira a configuração Supabase e tente novamente.")

    with st.sidebar:
        st.markdown("### Assistente SAP")
        st.caption("CHAMADOS · MM")
        selected = st.radio("Chamados", list(state["tickets"]), label_visibility="collapsed",
                            format_func=lambda key: f"{case_reference(state['tickets'][key])} · {state['tickets'][key]['title']}",
                            key="selected_ticket", on_change=show_chat)
        st.divider()
        st.caption("Ambiente simulado\n\nDados isolados nesta sessão")

    if st.session_state.get("case_view") == "list":
        display_case_list(state)
        return
    ticket = state["tickets"][selected]
    messages = store.messages(context, selected)
    st.caption(f"SAP MM / RECEBIMENTO · {case_reference(ticket)}")
    st.title(ticket["title"])
    st.caption(LABELS[ticket["status"]] + " · Prioridade " + priority_label(ticket) + " · Dados fictícios")
    with st.expander("Detalhes do chamado"):
        display_case_details(state, selected)

    proposals = store.proposals(context, selected)
    pending = any(x["state"] == "pendente" for x in proposals)
    for message in messages:
        with st.chat_message(message["role"]):
            if message["details"].get("error"):
                st.error(message["content"])
            else:
                st.markdown(message["content"])
            if message["role"] == "assistant" and not message["details"].get("error"):
                display_citations(message)
            display_details(message["details"])
    for proposal in proposals:
        approval_card(proposal, gateway, context)

    if not settings.api_key:
        st.info("Configure a chave OpenRouter para iniciar a análise com IA.")
    if pending:
        st.caption("Decida a solicitação pendente antes de continuar este atendimento.")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button("Chamados", icon=":material/confirmation_number:", help="Selecionar um chamado para esta conversa", key="open_case_selector"):
            st.session_state.dialog_case = selected
            st.session_state.dialog_search = ""
            st.session_state.case_selector_open = True
        st.button("Lista completa", icon=":material/list_alt:", on_click=show_case_list)
        st.caption("Em análise: " + case_reference(ticket))
    if st.session_state.get("case_selector_open"):
        case_selector(state)
    request = None
    if not messages and st.button("Analisar chamado", type="primary", disabled=not settings.api_key or pending):
        request = ticket["description"]
    typed = st.chat_input("Descreva o que aconteceu ou complemente os dados…", disabled=not settings.api_key or pending,
                          max_chars=6000)
    if typed:
        request = typed
    if request:
        try:
            with st.status("Consultando dados e fontes…", expanded=False) as status:
                assistant.analyze(context, selected, request, new_id())
                status.update(label="Atendimento atualizado", state="complete")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Não foi possível concluir o atendimento. Nenhuma ação de negócio foi autorizada por esta mensagem.")


try:
    main()
except Exception:
    st.error("Não foi possível carregar este atendimento. Confira a conexão e recarregue a página.")

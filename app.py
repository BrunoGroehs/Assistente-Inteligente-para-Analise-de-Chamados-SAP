from datetime import datetime
import hmac
from zoneinfo import ZoneInfo

import streamlit as st

from sap_assistant.config import Settings
from sap_assistant.citations import message_citations, safe_answer_text, source_groups
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
                            format_func=lambda key: f"{key} · {state['tickets'][key]['title']}", key="selected_ticket")
        st.divider()
        st.caption("Ambiente simulado\n\nDados isolados nesta sessão")

    ticket = state["tickets"][selected]
    st.caption(f"SAP MM / RECEBIMENTO · {selected}")
    st.title(ticket["title"])
    st.caption(LABELS[ticket["status"]] + " · Dados fictícios")
    with st.expander("Contexto do chamado", expanded=not bool(store.messages(context, selected))):
        st.write(ticket["description"])
        order = state["orders"].get(f"{ticket['purchase_order']}/{ticket['item']}")
        if order:
            st.caption(f"Pedido {order['purchase_order']} · Item {order['item']} · {order['material']}")

    messages = store.messages(context, selected)
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

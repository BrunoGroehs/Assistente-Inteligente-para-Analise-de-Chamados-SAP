"""Diagnóstico de inicialização sem mensagens SQL, DSN ou credenciais."""
from sqlalchemy.exc import DBAPIError, OperationalError

from .database import DatabaseSetupError


class StartupError(RuntimeError):
    def __init__(self, code, hint):
        self.code = code
        super().__init__(f"{code}: {hint}")


def startup_error(stage, error):
    if stage == "configuracao":
        return StartupError("SAP_STARTUP_CONFIG", "Confira as variáveis do servidor no ambiente deste deploy: "
                            "DATABASE_URL, APP_ENV, DEMO_ACCESS_CODE e APP_PUBLIC_ORIGIN.")
    if isinstance(error, DBAPIError):
        state = getattr(error.orig, "sqlstate", None)
        if state in {"28000", "28P01"}:
            return StartupError("SAP_STARTUP_DB_AUTH", "Autenticação PostgreSQL recusada. Confira usuário e senha "
                                "do pooler no ambiente deste deploy; não use a chave de API como senha.")
        if state == "42501":
            return StartupError("SAP_STARTUP_DB_PERMISSION", "A conexão não tem permissão para preparar "
                                "o schema próprio sap_chamados_ai. Não altere tabelas de outros projetos.")
        if isinstance(error, OperationalError):
            return StartupError("SAP_STARTUP_DB_CONNECTION", "Não foi possível conectar ao PostgreSQL. "
                                "Na Vercel, confira o Session pooler do Supabase, o usuário completo, "
                                "SSL e restrições de rede. Conexão direta pode exigir IPv6 ou adicional IPv4.")
    if isinstance(error, DatabaseSetupError):
        if str(error) == "Ative a extensão vector no painel Supabase antes de inicializar.":
            return StartupError("SAP_STARTUP_DB_VECTOR", "Ative a extensão vector no projeto Supabase correto.")
        return StartupError("SAP_STARTUP_DB_IDENTITY", "A identificação do schema próprio não é compatível. "
                            "Nenhum schema externo deve ser alterado ou removido.")
    if stage == "conhecimento":
        if isinstance(error, FileNotFoundError):
            return StartupError("SAP_STARTUP_KNOWLEDGE_FILES", "Faltam arquivos de conhecimento no pacote "
                                "da função. Preserve conhecimento/catalogo.json e os guias referenciados.")
        if isinstance(error, DBAPIError):
            return StartupError("SAP_STARTUP_KNOWLEDGE_DATABASE", "Falha ao sincronizar o conhecimento "
                                "no schema próprio. Confira permissões e estrutura desse schema.")
        return StartupError("SAP_STARTUP_KNOWLEDGE", "Não foi possível carregar a base de conhecimento. "
                            "Confira o catálogo, os guias e suas versões no pacote da função.")
    if stage == "provedor":
        return StartupError("SAP_STARTUP_PROVIDER", "Não foi possível preparar o cliente OpenRouter. "
                            "Confira dependências e configuração HTTP/TLS do servidor.")
    if stage == "banco":
        return StartupError("SAP_STARTUP_DATABASE", "Não foi possível preparar o PostgreSQL. Confira "
                            "DATABASE_URL, driver, permissões e extensão vector no projeto correto.")
    return StartupError("SAP_STARTUP_RUNTIME", "Não foi possível preparar o aplicativo. "
                        "Confira o pacote e a configuração do servidor.")

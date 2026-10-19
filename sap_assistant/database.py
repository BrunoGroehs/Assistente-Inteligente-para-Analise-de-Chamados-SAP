from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import secrets
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ForeignKey, MetaData, String, Text, UniqueConstraint, create_engine, event, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .fixtures import initial_state

PROJECT_SCHEMA = "sap_chamados_ai"
PROJECT_KEY = "assistente-inteligente-chamados-sap-v1"


class DatabaseSetupError(ValueError):
    """Mensagem de configuração controlada e segura para exibição."""


def utcnow():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid4())


class Base(DeclarativeBase):
    metadata = MetaData(schema=PROJECT_SCHEMA)


class ProjectIdentity(Base):
    __tablename__ = "sap_project_identity"
    project_key: Mapped[str] = mapped_column(String(80), primary_key=True)


class Workspace(Base):
    __tablename__ = "sap_workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)


class Message(Base):
    __tablename__ = "sap_messages"
    __table_args__ = (UniqueConstraint("workspace_id", "submission_id", "role"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey(f"{PROJECT_SCHEMA}.sap_workspaces.id"), index=True)
    ticket: Mapped[str] = mapped_column(String(10))
    submission_id: Mapped[str] = mapped_column(String(36))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), default=lambda: utcnow().isoformat())


class Proposal(Base):
    __tablename__ = "sap_proposals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey(f"{PROJECT_SCHEMA}.sap_workspaces.id"), index=True)
    ticket: Mapped[str] = mapped_column(String(10))
    payload: Mapped[dict] = mapped_column(JSON)
    integrity: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(30), default="pendente")
    created_at: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[str] = mapped_column(String(40))
    result: Mapped[dict] = mapped_column(JSON, default=dict)


class Audit(Base):
    __tablename__ = "sap_audit"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey(f"{PROJECT_SCHEMA}.sap_workspaces.id"), index=True)
    event: Mapped[str] = mapped_column(String(60))
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String(40), default=lambda: utcnow().isoformat())


class Chunk(Base):
    __tablename__ = "sap_knowledge"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    attributes: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    embedding: Mapped[list | None] = mapped_column(Vector().with_variant(JSON, "sqlite"), nullable=True)


@dataclass(frozen=True)
class SessionContext:
    workspace_id: str
    token: str = field(repr=False)


class AccessDenied(ValueError):
    pass


class Store:
    def __init__(self, url):
        if url.startswith("sqlite:///"):
            name = url.removeprefix("sqlite:///")
            if name != ":memory:":
                Path(name).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(url, pool_pre_ping=True,
                                    connect_args={"check_same_thread": False, "timeout": 30}
                                    if url.startswith("sqlite") else {"connect_timeout": 10, "prepare_threshold": None},
                                    **({} if url.startswith("sqlite") else {"pool_size": 3, "max_overflow": 2}))
        if self.engine.dialect.name == "sqlite":
            self.engine = self.engine.execution_options(schema_translate_map={PROJECT_SCHEMA: None})
            @event.listens_for(self.engine, "connect")
            def sqlite_setup(connection, _):
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA busy_timeout=30000")
        else:
            @event.listens_for(self.engine, "connect")
            def vector_search_path(connection, _):
                # Apenas configuração desta conexão, sem alterar roles ou schemas existentes.
                from psycopg import sql
                previous = connection.autocommit
                connection.autocommit = True
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT n.nspname FROM pg_extension e JOIN pg_namespace n "
                                       "ON n.oid=e.extnamespace WHERE e.extname='vector'")
                        row = cursor.fetchone()
                        if row:
                            cursor.execute(sql.SQL("SET search_path TO pg_catalog, {}, public").format(sql.Identifier(row[0])))
                finally:
                    connection.autocommit = previous

    def initialize(self):
        if self.engine.dialect.name == "postgresql":
            with self.engine.begin() as connection:
                # Serialize apenas a inicialização deste projeto. Nunca usar DROP/alterar tabelas externas.
                connection.execute(text("SELECT pg_advisory_xact_lock(734002118)"))
                if not connection.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")):
                    raise DatabaseSetupError("Ative a extensão vector no painel Supabase antes de inicializar.")
                inspector = inspect(connection)
                if inspector.has_schema(PROJECT_SCHEMA):
                    if not inspector.has_table(ProjectIdentity.__tablename__, schema=PROJECT_SCHEMA):
                        raise DatabaseSetupError("Schema existente sem identificação deste projeto. Nenhuma tabela alterada.")
                    keys = connection.scalars(select(ProjectIdentity.project_key)).all()
                    if keys != [PROJECT_KEY]:
                        raise DatabaseSetupError("Schema pertence a outro projeto. Nenhuma tabela alterada.")
                else:
                    from sqlalchemy.schema import CreateSchema
                    connection.execute(CreateSchema(PROJECT_SCHEMA))
                    ProjectIdentity.__table__.create(connection)
                    connection.execute(ProjectIdentity.__table__.insert().values(project_key=PROJECT_KEY))
                Base.metadata.create_all(connection)
        else:
            # SQLite existe apenas nas suítes locais, sempre com arquivo temporário isolado.
            Base.metadata.create_all(self.engine)

    @contextmanager
    def transaction(self):
        with Session(self.engine, expire_on_commit=False) as db:
            try:
                if self.engine.dialect.name == "sqlite":
                    db.execute(text("BEGIN IMMEDIATE"))
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    def create_workspace(self):
        token = secrets.token_urlsafe(32)
        context = SessionContext(new_id(), token)
        with self.transaction() as db:
            db.add(Workspace(id=context.workspace_id, token_hash=hashlib.sha256(token.encode()).hexdigest(),
                             data=initial_state()))
        return context

    def authorize(self, db, context, lock=False):
        query = select(Workspace).where(Workspace.id == context.workspace_id)
        row = db.scalar(query.with_for_update() if lock else query)
        token_hash = hashlib.sha256(context.token.encode()).hexdigest()
        if row is None or not hmac.compare_digest(row.token_hash, token_hash):
            raise AccessDenied("Sessão inválida ou sem acesso a este ambiente.")
        return row

    def state(self, context):
        with Session(self.engine) as db:
            return deepcopy(self.authorize(db, context).data)

    def messages(self, context, ticket):
        with Session(self.engine) as db:
            self.authorize(db, context)
            rows = db.scalars(select(Message).where(Message.workspace_id == context.workspace_id,
                              Message.ticket == ticket).order_by(Message.created_at, Message.id)).all()
            return [{"id": x.id, "role": x.role, "content": x.content, "details": deepcopy(x.details),
                     "created_at": x.created_at} for x in rows]

    def proposals(self, context, ticket, now=None):
        with self.transaction() as db:
            self.authorize(db, context, lock=True)
            rows = db.scalars(select(Proposal).where(Proposal.workspace_id == context.workspace_id,
                              Proposal.ticket == ticket).order_by(Proposal.created_at)).all()
            result = []
            for row in rows:
                if row.state == "pendente" and datetime.fromisoformat(row.expires_at) <= (now or utcnow()):
                    row.state = "expirada"
                    db.add(Audit(workspace_id=context.workspace_id, event="proposta_expirada",
                                 details={"proposal_id": row.id}))
                result.append({"id": row.id, "payload": deepcopy(row.payload), "state": row.state,
                               "expires_at": row.expires_at, "result": deepcopy(row.result)})
            return result

    def audit(self, context):
        with Session(self.engine) as db:
            self.authorize(db, context)
            return [{"event": x.event, "details": x.details, "at": x.created_at} for x in db.scalars(
                select(Audit).where(Audit.workspace_id == context.workspace_id).order_by(Audit.created_at))]

"""API e interface estática, sem dependência de plataforma de hospedagem."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import hmac
import json
from pathlib import Path
from queue import Empty, Queue
from threading import Lock
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from . import runtime
from .config import Settings
from .database import AccessDenied, SessionContext, new_id, validate_chat_id
from .web_views import public_snapshot
from .approvals import PolicyError
from .corrections import CorrectionInput, prepare_correction

COOKIE = "sap_session"
CLIENT_HEADER = "sap-assistant"


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Input):
    access_code: str = Field(default="", max_length=256)


class MessageInput(Input):
    message: str = Field(min_length=1, max_length=6000)
    ticket_id: str | None = Field(default=None, max_length=10)
    submission_id: str


class Decision(Input):
    approve: StrictBool


def chat_key(value):
    if value == "initial":
        return None
    try:
        validate_chat_id(value)
    except ValueError:
        raise HTTPException(422, "Conversa inválida.") from None
    return value


def create_app(settings=None, services=None, frontend_path=None):
    @asynccontextmanager
    async def lifespan(app):
        current = settings or Settings.load()
        current.validate()
        try:
            app.state.services = services or runtime.create_runtime(current)
        except Exception:
            raise RuntimeError("Não foi possível preparar o aplicativo. Confira a configuração do servidor.") from None
        app.state.settings = current
        app.state.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sap-analysis")
        app.state.active = set()
        app.state.lock = Lock()
        yield
        app.state.executor.shutdown(wait=True, cancel_futures=True)
        if services is None:
            app.state.services[1].provider.client.close()
            app.state.services[0].engine.dispose()

    app = FastAPI(title="Assistente SAP MM", lifespan=lifespan, docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def browser_boundary(request, call_next):
        if request.url.path.startswith("/api/") and request.method not in {"GET", "HEAD", "OPTIONS"}:
            if request.headers.get("x-requested-with") != CLIENT_HEADER:
                return JSONResponse({"detail": "Requisição de interface inválida."}, status_code=403)
            origin = request.headers.get("origin")
            if origin and urlsplit(origin).netloc != request.headers.get("host"):
                return JSONResponse({"detail": "Origem da requisição inválida."}, status_code=403)
        try:
            response = await call_next(request)
        except Exception:
            # SQL/HTTP podem conter DSN e credenciais; não propagar payload bruto aos logs do servidor.
            response = JSONResponse({"detail": "Não foi possível concluir a solicitação."}, status_code=503)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.exception_handler(AccessDenied)
    async def access_error(request, exc):
        return JSONResponse({"detail": "Sessão ou conversa sem acesso."}, status_code=401)

    @app.exception_handler(Exception)
    async def safe_error(request, exc):
        return JSONResponse({"detail": "Não foi possível concluir a solicitação."}, status_code=503)

    def authenticated(request: Request):
        value = request.cookies.get(COOKIE, "")
        try:
            workspace, token = value.split(".", 1)
            validate_chat_id(workspace)
            if not 32 <= len(token) <= 128:
                raise ValueError()
            context = SessionContext(workspace, token)
            request.app.state.services[0].state(context)
            return context
        except (ValueError, AccessDenied):
            raise HTTPException(401, "Inicie uma sessão para continuar.") from None

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/config")
    def config(request: Request):
        return {"requires_access_code": bool(request.app.state.settings.access_code)}

    @app.post("/api/session")
    def login(body: Login, request: Request, response: Response):
        current = request.app.state.settings
        if current.access_code and not hmac.compare_digest(body.access_code.encode(), current.access_code.encode()):
            raise HTTPException(401, "Código de acesso incorreto.")
        context = request.app.state.services[0].create_workspace()
        response.set_cookie(COOKIE, context.workspace_id + "." + context.token, httponly=True,
                            secure=current.environment != "local", samesite="strict", max_age=86400, path="/api")
        return {"authenticated": True}

    @app.get("/api/session")
    def session(context=Depends(authenticated)):
        return {"authenticated": True}

    @app.post("/api/chats")
    def new_chat(context=Depends(authenticated)):
        return {"chat_id": new_id()}

    @app.get("/api/chats/{chat_id}")
    def snapshot(chat_id: str, request: Request, context=Depends(authenticated)):
        return public_snapshot(request.app.state.services[0].snapshot(context, chat_key(chat_id)))

    @app.post("/api/chats/{chat_id}/proposals/{proposal_id}/decision")
    def decide(chat_id: str, proposal_id: str, body: Decision, request: Request, context=Depends(authenticated)):
        result = request.app.state.services[2].decide(context, proposal_id, body.approve, chat_id=chat_key(chat_id))
        return {"state": result["state"], "message": result.get("message", "Solicitação atualizada.")}

    @app.post("/api/chats/{chat_id}/messages/{message_id}/correction")
    def prepare(chat_id: str, message_id: str, body: CorrectionInput, request: Request, context=Depends(authenticated)):
        try:
            proposal = prepare_correction(request.app.state.services[0], context, message_id, body, chat_key(chat_id))
        except PolicyError as exc:
            raise HTTPException(409, str(exc)) from None
        return {"proposal_id": proposal}

    @app.post("/api/chats/{chat_id}/messages")
    def analyze(chat_id: str, body: MessageInput, request: Request, context=Depends(authenticated)):
        current_chat = chat_key(chat_id)
        try:
            validate_chat_id(body.submission_id)
        except ValueError:
            raise HTTPException(422, "Identificador de envio inválido.") from None
        if not body.message.strip():
            raise HTTPException(422, "Digite uma mensagem.")
        state = request.app.state
        with state.lock:
            if context.workspace_id in state.active:
                raise HTTPException(409, "Uma análise já está em andamento nesta sessão.")
            if len(state.active) >= 4:
                raise HTTPException(429, "As análises estão ocupadas. Tente novamente em instantes.")
            state.active.add(context.workspace_id)
        events = Queue()

        def execute():
            try:
                result = state.services[1].analyze(context, body.ticket_id, body.message, body.submission_id,
                    on_progress=lambda label: events.put({"type": "progress", "label": label}), chat_id=current_chat)
                events.put({"type": "completed", "state": result["state"]})
            except (ValueError, AccessDenied):
                events.put({"type": "error", "message": "Confira os dados do chamado e tente novamente."})
            except Exception:
                events.put({"type": "error", "message": "Não foi possível concluir a análise. Nenhuma ação autorizada."})
            finally:
                with state.lock:
                    state.active.discard(context.workspace_id)
                events.put(None)

        state.executor.submit(execute)

        def stream():
            while True:
                try:
                    event = events.get(timeout=15)
                except Empty:
                    yield json.dumps({"type": "heartbeat"}) + "\n"
                    continue
                if event is None:
                    return
                yield json.dumps(event, ensure_ascii=False) + "\n"

        return StreamingResponse(stream(), media_type="application/x-ndjson", headers={"X-Accel-Buffering": "no"})

    root = Path(frontend_path or Path(__file__).resolve().parents[1] / "frontend/dist").resolve()
    if (root / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def frontend():
        if not (root / "index.html").is_file():
            raise HTTPException(503, "Interface ainda não compilada. Execute npm run build na pasta frontend.")
        return FileResponse(root / "index.html")

    return app

from dataclasses import dataclass, field
from pathlib import Path
import os
from urllib.parse import urlsplit

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str = field(repr=False)
    api_key: str = field(default="", repr=False)
    chat_model: str = "qwen/qwen3.6-plus"
    embedding_model: str = "qwen/qwen3-embedding-8b"
    environment: str = "cloud"
    access_code: str = field(default="", repr=False)
    max_analyses: int = 30
    public_origin: str = ""

    @classmethod
    def load(cls, secrets=None):
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")

        def value(name, default=""):
            return str(os.environ.get(name) or (secrets or {}).get(name, default))

        database_url = value("DATABASE_URL")
        for prefix in ("postgres://", "postgresql://"):
            if database_url.startswith(prefix):
                database_url = "postgresql+psycopg://" + database_url[len(prefix):]
                break
        public_origin = value("APP_PUBLIC_ORIGIN").rstrip("/")
        if not public_origin and value("VERCEL") == "1" and value("VERCEL_URL"):
            scheme = "http" if value("VERCEL_ENV") == "development" else "https"
            public_origin = scheme + "://" + value("VERCEL_URL")
        return cls(
            database_url=database_url, api_key=value("OPENROUTER_API_KEY"),
            chat_model=value("OPENROUTER_CHAT_MODEL", "qwen/qwen3.6-plus"),
            embedding_model=value("OPENROUTER_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b"),
            environment=value("APP_ENV", "cloud"), access_code=value("DEMO_ACCESS_CODE"),
            max_analyses=max(1, int(value("MAX_ANALYSES_PER_SESSION", "30"))),
            public_origin=public_origin,
        )

    def validate(self):
        if not self.database_url:
            raise ValueError("Configure DATABASE_URL. Para desenvolvimento, copie .env.example para .env.")
        if self.environment not in {"local", "cloud"}:
            raise ValueError("APP_ENV deve ser local ou cloud.")
        if self.public_origin:
            origin = urlsplit(self.public_origin)
            if (origin.scheme not in {"http", "https"} or not origin.hostname or origin.username is not None
                    or origin.password is not None or origin.path or origin.query or origin.fragment):
                raise ValueError("APP_PUBLIC_ORIGIN deve conter somente protocolo, domínio e porta opcional.")
        if self.database_url.startswith(("postgres://", "postgresql://")):
            raise ValueError("Use o prefixo postgresql+psycopg:// em DATABASE_URL.")
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("O aplicativo usa PostgreSQL no Supabase. SQLite é exclusivo dos testes.")
        if self.environment != "local":
            if len(self.access_code) < 12:
                raise ValueError("Na hospedagem, configure DEMO_ACCESS_CODE com pelo menos 12 caracteres.")


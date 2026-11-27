"""Application configuration, loaded from environment variables (and an optional .env file).

Nothing secret has a default value. Integrations whose credentials are missing report themselves
as unavailable through `integration_status()` instead of failing silently.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database -------------------------------------------------------------------------
    # Supabase: use the Postgres connection string from Project Settings -> Database, e.g.
    # postgresql+psycopg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
    # When unset, a local SQLite file is used so the app runs without any external service.
    database_url: str = ""

    # --- Auth (Supabase Auth) -------------------------------------------------------------
    supabase_url: str = ""
    supabase_jwt_secret: str = ""  # Project Settings -> API -> JWT secret (HS256 projects)
    # When true, every API route except /health requires a valid Supabase access token.
    require_auth: bool = False

    # --- AI providers ---------------------------------------------------------------------
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"
    openai_api_key: str = ""
    openai_model: str = "gpt-5"
    # Claude Code CLI (`claude -p`) under your own Claude subscription login: no API key, no
    # per-call billing; calls count against the plan's usage limits. Personal/local use only.
    claude_code_enabled: bool = True
    claude_code_path: str = "claude"
    claude_code_model: str = "opus"
    claude_code_timeout_s: int = 1800
    # "auto" = anthropic if a key is set, else claude_code if the CLI is installed, else openai.
    default_llm_provider: str = "auto"  # "auto" | "anthropic" | "claude_code" | "openai"
    # Hard ceiling on total LLM spend (USD) recorded in llm_usage. Calls are refused past it.
    llm_budget_usd: float = 25.0

    # --- Paper sources --------------------------------------------------------------------
    semantic_scholar_api_key: str = ""
    # OpenAlex / Crossref "polite pool" contact. Optional; never filled in automatically.
    contact_email: str = ""
    grobid_url: str = ""  # e.g. http://localhost:8070 ; falls back to pdfminer when empty
    http_user_agent: str = "MathResearchLab/0.1 (research tool)"

    # --- Storage ----------------------------------------------------------------------------
    data_dir: Path = BACKEND_DIR / "data"

    # --- Jobs & sandbox -------------------------------------------------------------------
    run_embedded_worker: bool = True  # run a job worker thread inside the API process
    worker_poll_seconds: float = 1.5
    job_stale_after_seconds: int = 300
    sandbox_default_timeout_s: int = 120
    sandbox_max_timeout_s: int = 1800
    sandbox_default_memory_mb: int = 2048
    sandbox_python: str = ""  # interpreter used for experiments; defaults to the backend's own

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                url = "postgresql+psycopg://" + url[len("postgres://"):]
            elif url.startswith("postgresql://"):
                url = "postgresql+psycopg://" + url[len("postgresql://"):]
            return url
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.data_dir / 'mathresearchlab.db'}"

    @property
    def pdf_dir(self) -> Path:
        p = self.data_dir / "pdfs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def experiments_dir(self) -> Path:
        p = self.data_dir / "experiments"
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _claude_code_path() -> str | None:
    import shutil
    s = get_settings()
    return shutil.which(s.claude_code_path) if s.claude_code_enabled else None


def integration_status() -> list[dict]:
    """Honest report of which integrations are usable right now."""
    s = get_settings()
    db_kind = "postgres" if s.database_url else "sqlite"
    return [
        {"name": "Database", "key": "database", "available": True,
         "detail": f"{db_kind} ({'Supabase/Postgres via DATABASE_URL' if s.database_url else 'local SQLite fallback — set DATABASE_URL for Supabase'})"},
        {"name": "Supabase Auth", "key": "auth", "available": bool(s.supabase_jwt_secret or s.supabase_url),
         "detail": ("JWT verification enabled" + (" (auth required)" if s.require_auth else " (auth optional)"))
         if (s.supabase_jwt_secret or s.supabase_url) else
         "not configured (SUPABASE_URL / SUPABASE_JWT_SECRET) — single-user local mode"},
        {"name": "Anthropic", "key": "anthropic", "available": bool(s.anthropic_api_key),
         "detail": f"model {s.anthropic_model}" if s.anthropic_api_key else "ANTHROPIC_API_KEY not set"},
        {"name": "Claude Code (subscription)", "key": "claude_code", "available": bool(_claude_code_path()),
         "detail": (f"{_claude_code_path()} · model {s.claude_code_model} · uses your Claude plan login, no API billing"
                    if _claude_code_path() else
                    "Claude Code CLI not found (install it and log in, or set CLAUDE_CODE_PATH)"
                    if s.claude_code_enabled else "disabled (CLAUDE_CODE_ENABLED=false)")},
        {"name": "OpenAI", "key": "openai", "available": bool(s.openai_api_key),
         "detail": f"model {s.openai_model}" if s.openai_api_key else "OPENAI_API_KEY not set"},
        {"name": "arXiv", "key": "arxiv", "available": True, "detail": "public API, no key required"},
        {"name": "OpenAlex", "key": "openalex", "available": True, "detail": "public API, no key required"},
        {"name": "Crossref", "key": "crossref", "available": True, "detail": "public API, no key required"},
        {"name": "Semantic Scholar", "key": "semantic_scholar", "available": True,
         "detail": "API key set" if s.semantic_scholar_api_key else
         "no key — shared unauthenticated rate limit (requests may be throttled)"},
        {"name": "GROBID", "key": "grobid", "available": bool(s.grobid_url),
         "detail": s.grobid_url or "GROBID_URL not set — using pdfminer text extraction (no section structure)"},
    ]

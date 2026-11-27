"""FastAPI application. Interactive API docs are served at /docs (OpenAPI at /openapi.json)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import autopilot, conjectures, experiments, papers, research, system
from app.config import get_settings
from app.sources.base import SourceError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mrl")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    if s.require_auth and not (s.supabase_jwt_secret or s.supabase_url):
        raise RuntimeError("REQUIRE_AUTH=true but neither SUPABASE_JWT_SECRET nor SUPABASE_URL is set")
    workers = []
    if s.run_embedded_worker:
        from app.jobs.handlers import HANDLERS
        from app.jobs.worker import Worker

        # One worker takes any job; a second never takes long research runs, so paper ingestion and
        # experiments are not blocked while a research run is in progress.
        # Extra research workers let the autopilot keep AUTOPILOT_PARALLEL_RUNS research runs going at once.
        workers = [Worker("embedded"), Worker("embedded-light", [t for t in HANDLERS if t != "research_run"])]
        workers += [Worker(f"embedded-research{i}", ["research_run"]) for i in range(2, s.autopilot_parallel_runs + 1)]
        for w in workers:
            w.start_background()
        log.info("embedded job workers started")
        from app.autopilot import AutopilotThread, load_state, save_state
        st = load_state()
        if "enabled" not in st or (s.autopilot_default_enabled and not st.get("enabled")):
            st["enabled"] = s.autopilot_default_enabled
            save_state(st)
        workers.append(AutopilotThread())
        workers[-1].start()
    yield
    for w in workers:
        w.stop()


app = FastAPI(title="MathResearchLab API", version="0.1.0", lifespan=lifespan,
              description="Discovery, verification and computational research on open mathematical problems.")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(SourceError)
async def source_error(_: Request, exc: SourceError):
    return JSONResponse(status_code=502, content={"detail": str(exc), "source": exc.source})


@app.get("/health", tags=["system"])
def health():
    from sqlalchemy import text

    from app.db import get_engine

    with get_engine().connect() as c:
        c.execute(text("select 1"))
    return {"ok": True}


for r in (system.router, papers.router, conjectures.router, experiments.router, research.router, autopilot.router):
    app.include_router(r)

"""Common types and HTTP helper for literature sources.

Each source implements `PaperSource` and returns `PaperRecord`s. Sources are independent and
replaceable; the registry in `app.sources.registry` decides which ones are queried.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)


class SourceError(Exception):
    def __init__(self, source: str, message: str, status_code: int | None = None):
        super().__init__(f"{source}: {message}")
        self.source = source
        self.status_code = status_code


@dataclass
class PaperRecord:
    source: str
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None
    published_date: date | None = None
    venue: str | None = None
    categories: list[str] = field(default_factory=list)
    landing_url: str | None = None
    pdf_url: str | None = None
    is_open_access: bool | None = None
    license: str | None = None
    cited_by_count: int | None = None
    references: list[dict] = field(default_factory=list)  # [{title?, doi?, arxiv_id?, openalex_id?}]
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["published_date"] = self.published_date.isoformat() if self.published_date else None
        d.pop("raw", None)
        return d


@dataclass
class SearchQuery:
    text: str = ""
    subject: str | None = None  # e.g. "math.CO" or "graph theory"
    from_date: date | None = None
    to_date: date | None = None
    limit: int = 20


class PaperSource(Protocol):
    name: str

    def search(self, q: SearchQuery) -> list[PaperRecord]: ...


# ---------------------------------------------------------------------------------------------
# HTTP with per-host politeness delay, retries on 429/5xx, and request logging
# ---------------------------------------------------------------------------------------------
_last_call: dict[str, float] = {}
_lock = threading.Lock()
MIN_INTERVAL = {"arxiv": 3.0, "semantic_scholar": 1.1, "openalex": 0.15, "crossref": 0.1}


def _log_request(source: str, endpoint: str, status: int | None, ms: int, error: str | None) -> None:
    try:
        from app.db import session_scope
        from app.models import SourceRequestLog

        with session_scope() as db:
            db.add(SourceRequestLog(source=source, endpoint=endpoint[:2000], status_code=status,
                                    duration_ms=ms, error=error))
    except Exception:  # logging must never break a fetch
        log.debug("could not log source request", exc_info=True)


def http_get(source: str, url: str, *, params: dict | None = None, headers: dict | None = None,
             timeout: float = 30.0, retries: int = 3, expect: str = "json"):
    s = get_settings()
    hdrs = {"User-Agent": s.http_user_agent}
    if headers:
        hdrs.update(headers)
    last_exc: Exception | None = None
    for attempt in range(retries):
        with _lock:
            wait = MIN_INTERVAL.get(source, 0.0) - (time.monotonic() - _last_call.get(source, 0.0))
            if wait > 0:
                time.sleep(wait)
            _last_call[source] = time.monotonic()
        t0 = time.monotonic()
        try:
            r = httpx.get(url, params=params, headers=hdrs, timeout=timeout, follow_redirects=True)
        except httpx.HTTPError as e:
            ms = int((time.monotonic() - t0) * 1000)
            _log_request(source, url, None, ms, repr(e))
            last_exc = SourceError(source, f"network error: {e}")
            time.sleep(2 ** attempt)
            continue
        ms = int((time.monotonic() - t0) * 1000)
        _log_request(source, str(r.request.url), r.status_code, ms, None if r.is_success else r.text[:300])
        if r.status_code == 429 or r.status_code >= 500:
            last_exc = SourceError(source, f"HTTP {r.status_code}", r.status_code)
            retry_after = r.headers.get("retry-after")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2.0 * (attempt + 1)
            time.sleep(min(delay, 20))
            continue
        if r.status_code == 404:
            return None
        if not r.is_success:
            raise SourceError(source, f"HTTP {r.status_code}: {r.text[:200]}", r.status_code)
        if expect == "json":
            return r.json()
        if expect == "bytes":
            return r
        return r.text
    assert last_exc is not None
    raise last_exc

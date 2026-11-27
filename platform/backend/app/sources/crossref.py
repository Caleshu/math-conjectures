"""Crossref REST client (https://api.crossref.org). No key required."""
from __future__ import annotations

import re
from datetime import date

from app.config import get_settings
from app.sources.base import PaperRecord, SearchQuery, http_get
from app.sources.identifiers import normalize_doi

API = "https://api.crossref.org"


def _date(item: dict) -> date | None:
    for key in ("published-print", "published-online", "issued", "created"):
        parts = ((item.get(key) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            y, m, d = (list(parts) + [1, 1])[:3]
            try:
                return date(int(y), int(m or 1), int(d or 1))
            except ValueError:
                continue
    return None


def to_record(item: dict) -> PaperRecord:
    abstract = item.get("abstract")
    if abstract:
        abstract = re.sub(r"<[^>]+>", " ", abstract)
        abstract = re.sub(r"\s+", " ", abstract).strip()
    pdf = None
    for link in item.get("link") or []:
        if link.get("content-type") == "application/pdf":
            pdf = link.get("URL")
    lic = (item.get("license") or [{}])[0].get("URL")
    return PaperRecord(
        source="crossref",
        title=" ".join(item.get("title") or []) or "",
        authors=[" ".join(p for p in (a.get("given"), a.get("family")) if p) for a in item.get("author") or []],
        abstract=abstract,
        doi=normalize_doi(item.get("DOI")),
        published_date=_date(item),
        venue=" ".join(item.get("container-title") or []) or None,
        categories=item.get("subject") or [],
        landing_url=item.get("URL"),
        pdf_url=pdf,
        is_open_access=None,  # Crossref does not reliably report OA status
        license=lic,
        cited_by_count=item.get("is-referenced-by-count"),
        references=[{"doi": normalize_doi(r.get("DOI")), "title": r.get("article-title") or r.get("unstructured")}
                    for r in item.get("reference") or []],
        raw={"type": item.get("type")},
    )


class CrossrefSource:
    name = "crossref"

    def _params(self, extra: dict) -> dict:
        p = dict(extra)
        if get_settings().contact_email:
            p["mailto"] = get_settings().contact_email
        return p

    def search(self, q: SearchQuery) -> list[PaperRecord]:
        filters = []
        if q.from_date:
            filters.append(f"from-pub-date:{q.from_date.isoformat()}")
        if q.to_date:
            filters.append(f"until-pub-date:{q.to_date.isoformat()}")
        text = " ".join(x for x in [q.text.replace('"', ""), q.subject or ""] if x).strip()
        params = {"rows": min(q.limit, 50)}
        if text:
            params["query.bibliographic"] = text
        if filters:
            params["filter"] = ",".join(filters)
        data = http_get("crossref", f"{API}/works", params=self._params(params))
        return [to_record(i) for i in ((data or {}).get("message") or {}).get("items", [])]

    def get(self, doi: str) -> PaperRecord | None:
        data = http_get("crossref", f"{API}/works/{doi}", params=self._params({}))
        return to_record(data["message"]) if data else None

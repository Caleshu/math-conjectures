"""Semantic Scholar Graph API client. Works without a key (shared, heavily throttled pool);
set SEMANTIC_SCHOLAR_API_KEY for reliable access."""
from __future__ import annotations

from datetime import date

from app.config import get_settings
from app.sources.base import PaperRecord, SearchQuery, http_get
from app.sources.identifiers import normalize_arxiv_id, normalize_doi

API = "https://api.semanticscholar.org/graph/v1"
FIELDS = ("title,authors,abstract,externalIds,publicationDate,venue,fieldsOfStudy,url,"
          "openAccessPdf,isOpenAccess,citationCount")


def to_record(p: dict) -> PaperRecord:
    ext = p.get("externalIds") or {}
    pub = p.get("publicationDate")
    return PaperRecord(
        source="semantic_scholar",
        title=p.get("title") or "",
        authors=[a.get("name", "") for a in p.get("authors") or []],
        abstract=p.get("abstract"),
        doi=normalize_doi(ext.get("DOI")),
        arxiv_id=normalize_arxiv_id(ext.get("ArXiv")),
        semantic_scholar_id=p.get("paperId"),
        published_date=date.fromisoformat(pub) if pub else None,
        venue=p.get("venue") or None,
        categories=p.get("fieldsOfStudy") or [],
        landing_url=p.get("url"),
        pdf_url=(p.get("openAccessPdf") or {}).get("url") or None,
        is_open_access=p.get("isOpenAccess"),
        cited_by_count=p.get("citationCount"),
    )


class SemanticScholarSource:
    name = "semantic_scholar"

    def _headers(self) -> dict:
        k = get_settings().semantic_scholar_api_key
        return {"x-api-key": k} if k else {}

    def search(self, q: SearchQuery) -> list[PaperRecord]:
        text = " ".join(x for x in [q.text.replace('"', ""), q.subject or ""] if x).strip()
        if not text:
            return []
        params = {"query": text, "limit": min(q.limit, 100), "fields": FIELDS, "fieldsOfStudy": "Mathematics"}
        if q.from_date or q.to_date:
            params["publicationDateOrYear"] = f"{q.from_date.isoformat() if q.from_date else ''}:{q.to_date.isoformat() if q.to_date else ''}"
        data = http_get("semantic_scholar", f"{API}/paper/search", params=params, headers=self._headers(), retries=2)
        return [to_record(p) for p in (data or {}).get("data", [])]

    def get(self, ident: str) -> PaperRecord | None:
        """ident like 'arXiv:1009.3304' or 'DOI:10.x/y'."""
        data = http_get("semantic_scholar", f"{API}/paper/{ident}", params={"fields": FIELDS},
                        headers=self._headers(), retries=2)
        return to_record(data) if data else None

    def citations(self, ident: str, limit: int = 100) -> list[PaperRecord]:
        data = http_get("semantic_scholar", f"{API}/paper/{ident}/citations",
                        params={"fields": FIELDS, "limit": min(limit, 1000)}, headers=self._headers(), retries=2)
        return [to_record(c["citingPaper"]) for c in (data or {}).get("data", []) if c.get("citingPaper", {}).get("title")]

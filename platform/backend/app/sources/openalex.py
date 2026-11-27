"""OpenAlex client (https://docs.openalex.org). No key required.

OpenAlex is also our main citation graph: `cites:` filters give papers citing a work, and
`referenced_works` gives a work's references.
"""
from __future__ import annotations

from datetime import date

from app.config import get_settings
from app.sources.base import PaperRecord, SearchQuery, http_get
from app.sources.identifiers import normalize_arxiv_id, normalize_doi

API = "https://api.openalex.org"

# OpenAlex topic/concept search terms per subject (keyword search is more robust than concept IDs).
SUBJECT_TERMS = {
    "graph theory": "graph theory", "combinatorics": "combinatorics",
    "extremal combinatorics": "extremal combinatorics", "discrete mathematics": "discrete mathematics",
    "number theory": "number theory", "algebra": "algebra", "geometry": "geometry",
}


def _abstract(inv: dict | None) -> str | None:
    if not inv:
        return None
    pos: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        pos.extend((i, word) for i in idxs)
    return " ".join(w for _, w in sorted(pos)) or None


def to_record(w: dict) -> PaperRecord:
    ids = w.get("ids") or {}
    arxiv = None
    for loc in w.get("locations") or []:
        src = (loc.get("source") or {}).get("display_name") or ""
        url = loc.get("landing_page_url") or ""
        if "arxiv" in src.lower() or "arxiv.org" in url:
            arxiv = normalize_arxiv_id(url) or arxiv
    oa = w.get("open_access") or {}
    best = w.get("best_oa_location") or {}
    primary = w.get("primary_location") or {}
    pub = w.get("publication_date")
    return PaperRecord(
        source="openalex",
        title=w.get("display_name") or w.get("title") or "",
        authors=[(a.get("author") or {}).get("display_name", "") for a in w.get("authorships") or []],
        abstract=_abstract(w.get("abstract_inverted_index")),
        doi=normalize_doi(w.get("doi") or ids.get("doi")),
        arxiv_id=arxiv,
        openalex_id=(w.get("id") or "").rsplit("/", 1)[-1] or None,
        published_date=date.fromisoformat(pub) if pub else None,
        venue=((primary.get("source") or {}).get("display_name")),
        categories=[t.get("display_name") for t in (w.get("topics") or [])[:5] if t.get("display_name")],
        landing_url=primary.get("landing_page_url") or w.get("doi"),
        pdf_url=best.get("pdf_url") or oa.get("oa_url") if oa.get("is_oa") else None,
        is_open_access=oa.get("is_oa"),
        license=best.get("license"),
        cited_by_count=w.get("cited_by_count"),
        references=[{"openalex_id": r.rsplit("/", 1)[-1]} for r in w.get("referenced_works") or []],
        raw={"type": w.get("type")},
    )


class OpenAlexSource:
    name = "openalex"

    def _params(self, extra: dict) -> dict:
        p = dict(extra)
        email = get_settings().contact_email
        if email:
            p["mailto"] = email
        return p

    def search(self, q: SearchQuery) -> list[PaperRecord]:
        filters = []
        if q.from_date:
            filters.append(f"from_publication_date:{q.from_date.isoformat()}")
        if q.to_date:
            filters.append(f"to_publication_date:{q.to_date.isoformat()}")
        text = q.text.replace('"', "").strip()
        if q.subject:
            text = f"{text} {SUBJECT_TERMS.get(q.subject.lower(), q.subject)}".strip()
        params = {"per-page": min(q.limit, 50)}
        if text:
            params["search"] = text
        else:
            params["sort"] = "publication_date:desc"
        if filters:
            params["filter"] = ",".join(filters)
        data = http_get("openalex", f"{API}/works", params=self._params(params))
        return [to_record(w) for w in (data or {}).get("results", [])]

    def get_by_doi(self, doi: str) -> PaperRecord | None:
        data = http_get("openalex", f"{API}/works/https://doi.org/{doi}", params=self._params({}))
        return to_record(data) if data else None

    def get(self, openalex_id: str) -> PaperRecord | None:
        data = http_get("openalex", f"{API}/works/{openalex_id}", params=self._params({}))
        return to_record(data) if data else None

    def find_arxiv(self, arxiv_id: str, title: str) -> PaperRecord | None:
        """OpenAlex has no arXiv-ID filter; match the arXiv DOI first, then by title."""
        rec = self.get_by_doi(f"10.48550/arxiv.{arxiv_id}")
        if rec:
            return rec
        data = http_get("openalex", f"{API}/works",
                        params=self._params({"filter": f"title.search:{title.replace(',', ' ')[:200]}", "per-page": 5}))
        from app.sources.identifiers import normalize_title
        for w in (data or {}).get("results", []):
            if normalize_title(w.get("display_name") or "") == normalize_title(title):
                return to_record(w)
        return None

    def citing_works(self, openalex_id: str, limit: int = 50) -> list[PaperRecord]:
        data = http_get("openalex", f"{API}/works",
                        params=self._params({"filter": f"cites:{openalex_id}", "per-page": min(limit, 200)}))
        return [to_record(w) for w in (data or {}).get("results", [])]

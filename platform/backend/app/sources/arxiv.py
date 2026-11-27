"""arXiv API client (https://info.arxiv.org/help/api/user-manual.html). No key required.

arXiv asks clients to wait ~3 s between requests; `http_get` enforces that.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date, datetime

from app.sources.base import PaperRecord, SearchQuery, SourceError, http_get
from app.sources.identifiers import normalize_arxiv_id, normalize_doi

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom",
      "os": "http://a9.com/-/spec/opensearch/1.1/"}

# Human subject -> arXiv categories.
SUBJECT_CATEGORIES: dict[str, list[str]] = {
    "graph theory": ["math.CO"],
    "combinatorics": ["math.CO"],
    "extremal combinatorics": ["math.CO"],
    "discrete mathematics": ["cs.DM", "math.CO"],
    "number theory": ["math.NT"],
    "algebra": ["math.RA", "math.AC", "math.GR"],
    "geometry": ["math.MG", "math.AG", "math.DG"],
}
# Keyword added to the query for subjects that share a category with others.
SUBJECT_KEYWORDS = {"graph theory": "graph", "extremal combinatorics": "extremal"}


def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _quote_terms(text: str) -> str:
    """Turn free text into an arXiv `all:` AND-query; quoted phrases are kept together."""
    parts = re.findall(r'"([^"]+)"|(\S+)', text)
    terms = []
    for phrase, word in parts:
        if phrase:
            terms.append(f'all:"{phrase}"')
        elif word.upper() not in {"AND", "OR", "ANDNOT"}:
            terms.append(f"all:{re.sub(r'[^\w.\-]', '', word)}")
    return " AND ".join(t for t in terms if not t.endswith(":"))


def build_query(q: SearchQuery) -> str:
    clauses = []
    if q.text.strip():
        clauses.append(f"({_quote_terms(q.text)})")
    if q.subject:
        subj = q.subject.strip()
        cats = SUBJECT_CATEGORIES.get(subj.lower(), [subj] if re.fullmatch(r"[a-z\-]+\.[A-Za-z\-]+", subj) else [])
        if cats:
            clauses.append("(" + " OR ".join(f"cat:{c}" for c in cats) + ")")
        kw = SUBJECT_KEYWORDS.get(subj.lower())
        if kw:
            clauses.append(f"all:{kw}")
    if q.from_date or q.to_date:
        f = (q.from_date or date(1991, 1, 1)).strftime("%Y%m%d") + "0000"
        t = (q.to_date or date.today()).strftime("%Y%m%d") + "2359"
        clauses.append(f"submittedDate:[{f} TO {t}]")
    if not clauses:
        raise SourceError("arxiv", "query needs keywords, a subject, or a date range")
    return " AND ".join(clauses)


def parse_feed(xml_text: str) -> list[PaperRecord]:
    root = ET.fromstring(xml_text)
    out: list[PaperRecord] = []
    for e in root.findall("a:entry", NS):
        id_url = _clean(e.findtext("a:id", namespaces=NS))
        aid = normalize_arxiv_id(id_url)
        title = _clean(e.findtext("a:title", namespaces=NS))
        if not aid or not title or title.lower() == "error":
            continue
        pdf = None
        landing = None
        for link in e.findall("a:link", NS):
            if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                pdf = link.get("href")
            elif link.get("rel") == "alternate":
                landing = link.get("href")
        pub = e.findtext("a:published", namespaces=NS)
        cats = [c.get("term") for c in e.findall("a:category", NS) if c.get("term")]
        prim = e.find("arxiv:primary_category", NS)
        if prim is not None and prim.get("term") in cats:
            cats.remove(prim.get("term"))
            cats.insert(0, prim.get("term"))
        out.append(PaperRecord(
            source="arxiv",
            title=title,
            authors=[_clean(a.findtext("a:name", namespaces=NS)) for a in e.findall("a:author", NS)],
            abstract=_clean(e.findtext("a:summary", namespaces=NS)) or None,
            doi=normalize_doi(e.findtext("arxiv:doi", namespaces=NS)),
            arxiv_id=aid,
            published_date=datetime.fromisoformat(pub.replace("Z", "+00:00")).date() if pub else None,
            venue=_clean(e.findtext("arxiv:journal_ref", namespaces=NS)) or None,
            categories=cats,
            landing_url=landing or f"https://arxiv.org/abs/{aid}",
            pdf_url=(pdf or f"https://arxiv.org/pdf/{aid}"),
            is_open_access=True,
            license=None,
            raw={"comment": _clean(e.findtext("arxiv:comment", namespaces=NS)) or None, "id_url": id_url},
        ))
    return out


class ArxivSource:
    name = "arxiv"

    def search(self, q: SearchQuery) -> list[PaperRecord]:
        params = {"search_query": build_query(q), "start": 0, "max_results": min(q.limit, 100),
                  "sortBy": "submittedDate" if (q.from_date or q.to_date) else "relevance",
                  "sortOrder": "descending"}
        text = http_get("arxiv", API, params=params, expect="text")
        return parse_feed(text) if text else []

    def get(self, arxiv_id: str) -> PaperRecord | None:
        text = http_get("arxiv", API, params={"id_list": arxiv_id, "max_results": 1}, expect="text")
        recs = parse_feed(text) if text else []
        return recs[0] if recs else None

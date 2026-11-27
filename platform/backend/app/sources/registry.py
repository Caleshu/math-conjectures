"""Federated search across sources with cross-source deduplication."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.sources.arxiv import ArxivSource
from app.sources.base import PaperRecord, SearchQuery, SourceError
from app.sources.crossref import CrossrefSource
from app.sources.identifiers import normalize_title
from app.sources.openalex import OpenAlexSource
from app.sources.semantic_scholar import SemanticScholarSource

log = logging.getLogger(__name__)

SOURCES = {
    "arxiv": ArxivSource(),
    "openalex": OpenAlexSource(),
    "crossref": CrossrefSource(),
    "semantic_scholar": SemanticScholarSource(),
}


def dedupe_key(r: PaperRecord) -> list[str]:
    keys = []
    if r.doi:
        keys.append("doi:" + r.doi)
    if r.arxiv_id:
        keys.append("arxiv:" + r.arxiv_id)
        keys.append("doi:10.48550/arxiv." + r.arxiv_id)
    if r.title:
        keys.append("title:" + normalize_title(r.title))
    return keys


def merge_records(a: PaperRecord, b: PaperRecord) -> PaperRecord:
    """Fill gaps in `a` from `b`; `a` wins on conflicts (arXiv is preferred for preprint metadata)."""
    for f in ("abstract", "doi", "arxiv_id", "openalex_id", "semantic_scholar_id", "published_date", "venue",
              "landing_url", "pdf_url", "is_open_access", "license", "cited_by_count"):
        if getattr(a, f) in (None, "", []) and getattr(b, f) not in (None, "", []):
            setattr(a, f, getattr(b, f))
    if not a.references and b.references:
        a.references = b.references
    if not a.authors and b.authors:
        a.authors = b.authors
    a.raw.setdefault("merged_sources", [a.source])
    if b.source not in a.raw["merged_sources"]:
        a.raw["merged_sources"].append(b.source)
    return a


def dedupe(records: list[PaperRecord]) -> list[PaperRecord]:
    out: list[PaperRecord] = []
    index: dict[str, PaperRecord] = {}
    for r in records:
        if not r.title:
            continue
        hit = next((index[k] for k in dedupe_key(r) if k in index), None)
        if hit:
            merge_records(hit, r)
            target = hit
        else:
            r.raw.setdefault("merged_sources", [r.source])
            out.append(r)
            target = r
        for k in dedupe_key(target):
            index[k] = target
    return out


def federated_search(q: SearchQuery, sources: list[str]) -> tuple[list[PaperRecord], dict[str, str]]:
    """Query sources concurrently. Returns (deduplicated records, {source: error message})."""
    errors: dict[str, str] = {}
    results: dict[str, list[PaperRecord]] = {}
    chosen = [s for s in sources if s in SOURCES]

    def run(name: str):
        try:
            return name, SOURCES[name].search(q), None
        except SourceError as e:
            return name, [], str(e)
        except Exception as e:  # surface unexpected parser errors per source instead of failing everything
            log.exception("source %s failed", name)
            return name, [], f"{name}: unexpected error: {e}"

    with ThreadPoolExecutor(max_workers=len(chosen) or 1) as ex:
        for name, recs, err in ex.map(run, chosen):
            results[name] = recs
            if err:
                errors[name] = err
    ordered = [r for name in ("arxiv", "openalex", "semantic_scholar", "crossref") for r in results.get(name, [])]
    return dedupe(ordered), errors

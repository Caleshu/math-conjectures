"""Parsing and normalisation of paper identifiers, used for deduplication."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_ARXIV_NEW = re.compile(r"(?<![\d.])(\d{4}\.\d{4,5})(v\d+)?(?!\d)")
_ARXIV_OLD = re.compile(r"\b([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?\b", re.IGNORECASE)
_DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.IGNORECASE)


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    m = _DOI.search(doi.strip())
    if not m:
        return None
    return m.group(1).rstrip(".,;)").lower()


def normalize_arxiv_id(value: str | None) -> str | None:
    """Return the version-less arXiv identifier, e.g. '1009.3304' or 'math/0601001'."""
    if not value:
        return None
    v = value.strip()
    v = re.sub(r"^(arxiv:)", "", v, flags=re.IGNORECASE)
    m = _ARXIV_NEW.search(v)
    if m:
        return m.group(1)
    m = _ARXIV_OLD.search(v)
    if m:
        return m.group(1).lower()
    return None


def normalize_title(title: str) -> str:
    t = unicodedata.normalize("NFKD", title)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"\$[^$]*\$", lambda m: re.sub(r"[^a-z0-9]", "", m.group(0).lower()), t.lower())
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


@dataclass
class ParsedIdentifier:
    kind: str  # arxiv | doi | openalex | url | unknown
    value: str


def parse_identifier(raw: str) -> ParsedIdentifier:
    """Interpret what a user pasted: arXiv ID / arXiv URL / DOI / doi.org URL / OpenAlex ID / other URL."""
    s = raw.strip()
    low = s.lower()
    if "arxiv.org" in low or low.startswith("arxiv:") or _ARXIV_NEW.fullmatch(re.sub(r"v\d+$", "", s)):
        a = normalize_arxiv_id(s)
        if a:
            return ParsedIdentifier("arxiv", a)
    if "doi.org/" in low or low.startswith("10.") or low.startswith("doi:"):
        d = normalize_doi(s)
        if d:
            return ParsedIdentifier("doi", d)
    m = re.search(r"\b(W\d{4,})\b", s)
    if "openalex.org" in low and m:
        return ParsedIdentifier("openalex", m.group(1))
    if re.fullmatch(r"W\d{4,}", s):
        return ParsedIdentifier("openalex", s)
    a = normalize_arxiv_id(s) if re.fullmatch(r"[a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?", s, re.I) else None
    if a:
        return ParsedIdentifier("arxiv", a)
    if low.startswith("http://") or low.startswith("https://"):
        return ParsedIdentifier("url", s)
    return ParsedIdentifier("unknown", s)

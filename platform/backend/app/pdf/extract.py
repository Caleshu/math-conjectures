"""Text extraction from PDFs and arXiv LaTeX sources.

- PDF: GROBID (if GROBID_URL is configured) for structured section text, otherwise pdfminer.six
  page by page. Page numbers are always kept because every extracted problem must cite a page.
- LaTeX: arXiv e-print archives are read *in memory* (never unpacked to disk or executed). The
  main .tex file is found by `\\documentclass` and `\\input`/`\\include` are inlined.
"""
from __future__ import annotations

import gzip
import io
import logging
import re
import tarfile
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

MAX_LATEX_BYTES = 5_000_000


@dataclass
class ExtractedText:
    pages: list[str]
    extractor: str
    sections: list[dict]  # [{title, page?}] best-effort


_HEADING = re.compile(
    r"^\s*(?:(\d+(?:\.\d+)*)\.?\s+([A-Z][A-Za-z ,:\-'’()]{2,80})|"
    r"(Introduction|Preliminaries|Conclusions?|Concluding [Rr]emarks|Open [Pp]roblems|"
    r"Further [Ww]ork|Future [Ww]ork|Final [Rr]emarks|Discussion|Acknowledge?ments|References))\s*$"
)


def detect_sections(pages: list[str]) -> list[dict]:
    secs = []
    for pno, text in enumerate(pages, 1):
        for line in text.splitlines():
            m = _HEADING.match(line)
            if m and len(line.strip()) < 90:
                title = (f"{m.group(1)} {m.group(2)}" if m.group(1) else m.group(3)).strip()
                secs.append({"title": title, "page": pno})
    return secs


def extract_pdf_pdfminer(path: Path) -> ExtractedText:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LAParams, LTTextContainer

    pages: list[str] = []
    for layout in extract_pages(str(path), laparams=LAParams()):
        pages.append("".join(el.get_text() for el in layout if isinstance(el, LTTextContainer)))
    return ExtractedText(pages=pages, extractor="pdfminer.six", sections=detect_sections(pages))


def extract_pdf_grobid(path: Path, grobid_url: str) -> ExtractedText:
    """Use GROBID for section structure, while still taking per-page text from pdfminer
    (GROBID's TEI does not give a clean page->text mapping without coordinates)."""
    base = extract_pdf_pdfminer(path)
    with path.open("rb") as fh:
        r = httpx.post(f"{grobid_url.rstrip('/')}/api/processFulltextDocument",
                       files={"input": fh}, data={"consolidateHeader": "0"}, timeout=180)
    r.raise_for_status()
    heads = re.findall(r"<head[^>]*>(.*?)</head>", r.text, flags=re.S)
    sections = [{"title": re.sub(r"<[^>]+>|\s+", " ", h).strip()} for h in heads if h.strip()]
    for s in sections:  # locate page of each heading in the pdfminer text
        s["page"] = next((i for i, t in enumerate(base.pages, 1) if s["title"][:40] in t), None)
    return ExtractedText(pages=base.pages, extractor="grobid+pdfminer.six", sections=sections or base.sections)


def extract_pdf(path: Path) -> ExtractedText:
    url = get_settings().grobid_url
    if url:
        try:
            return extract_pdf_grobid(path, url)
        except Exception as e:  # GROBID down -> still extract text, but record that it failed
            log.warning("GROBID failed (%s); falling back to pdfminer", e)
            res = extract_pdf_pdfminer(path)
            res.extractor = f"pdfminer.six (GROBID failed: {type(e).__name__})"
            return res
    return extract_pdf_pdfminer(path)


# ------------------------------------------------------------------------------------------
# LaTeX
# ------------------------------------------------------------------------------------------
def _decode(b: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


def read_arxiv_source(blob: bytes) -> tuple[str | None, list[str]]:
    """Return (flattened main LaTeX, list of member names) from an arXiv e-print payload."""
    files: dict[str, str] = {}
    names: list[str] = []
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
            total = 0
            for m in tf.getmembers():
                names.append(m.name)
                if not m.isfile() or not m.name.endswith((".tex", ".ltx")):
                    continue
                total += m.size
                if total > MAX_LATEX_BYTES:
                    break
                fh = tf.extractfile(m)
                if fh:
                    files[m.name] = _decode(fh.read())
    except tarfile.TarError:
        try:
            raw = gzip.decompress(blob)
        except OSError:
            raw = blob
        if raw[:4] == b"%PDF":
            return None, ["(pdf only)"]
        text = _decode(raw[:MAX_LATEX_BYTES])
        if "\\begin{document}" in text or "\\documentclass" in text:
            return text, ["main.tex"]
        return None, []
    if not files:
        return None, names
    main = next((n for n, t in files.items() if "\\documentclass" in t and "\\begin{document}" in t), None)
    main = main or max(files, key=lambda n: len(files[n]))

    def inline(text: str, depth: int = 0) -> str:
        if depth > 5:
            return text

        def repl(m: re.Match) -> str:
            target = m.group(2).strip()
            for cand in (target, target + ".tex"):
                for n in files:
                    if n == cand or n.endswith("/" + cand):
                        return inline(files[n], depth + 1)
            return m.group(0)

        return re.sub(r"\\(input|include)\{([^}]+)\}", repl, text)

    return inline(files[main]), names


def fetch_arxiv_source(arxiv_id: str) -> tuple[str | None, list[str]]:
    from app.sources.base import http_get

    r = http_get("arxiv", f"https://arxiv.org/e-print/{arxiv_id}", expect="bytes", timeout=60)
    if r is None:
        return None, []
    if len(r.content) > 50_000_000:
        return None, ["(source too large)"]
    return read_arxiv_source(r.content)

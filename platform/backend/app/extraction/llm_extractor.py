"""Conjecture extraction agent.

Reads the paper (LaTeX source when available — exact notation — otherwise page-tagged PDF text),
together with the heuristic candidates, and returns structured open problems. The model must
quote original wording verbatim; we then *check* each quote against the source text and record
whether it was found, so a paraphrase can never silently replace the original statement.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extraction.candidates import latex_to_plain
from app.llm.registry import tracked_json_call
from app.models import CandidatePassage, Paper

MAX_SOURCE_CHARS = 600_000  # well inside a 1M-token context; larger papers are refused, not truncated

SYSTEM = """You are a research mathematician cataloguing OPEN problems stated in a paper.

Rules:
- Report only problems the paper presents as unresolved: explicit conjectures, open questions, unsolved
  special cases, unresolved bounds, and explicitly suggested future research with mathematical content.
- Do NOT report results the paper proves, or famous conjectures merely mentioned as background unless
  the paper states them as still open. If a mentioned conjecture is described as solved, reject it.
- `original_wording` must be copied VERBATIM from the source (LaTeX allowed exactly as written). Never
  paraphrase it. If you cannot quote it exactly, leave it empty and explain in `rationale`.
- `normalized_statement` is a self-contained precise restatement in LaTeX ($...$ for inline math) with all
  quantifiers explicit. Do not strengthen or weaken the claim; note any ambiguity in `ambiguities`.
- Give the definitions needed to read the statement, taken from the paper.
- `known_partial_results` are only results stated in this paper (with location). Mark computational
  claims as computational. Do not add results from your own memory.
- Use the page markers (=== PAGE n ===) for page numbers when present; otherwise null.
- Be skeptical and precise. Fewer, correct items are better than many vague ones."""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["problems", "rejected_candidates"],
    "properties": {
        "problems": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["kind", "title", "original_wording", "normalized_statement", "definitions", "page",
                         "section", "label", "field", "subfields", "relevant_theorems", "known_partial_results",
                         "posed_by_this_paper", "confidence", "rationale", "ambiguities", "candidate_ids",
                         "difficulty_guess", "potential_approaches"],
            "properties": {
                "kind": {"type": "string", "enum": ["conjecture", "open_question", "open_problem", "unsolved_special_case",
                                                     "unresolved_bound", "future_research"]},
                "title": {"type": "string"},
                "original_wording": {"type": "string"},
                "normalized_statement": {"type": "string"},
                "definitions": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                                            "required": ["term", "definition"],
                                                            "properties": {"term": {"type": "string"}, "definition": {"type": "string"}}}},
                "page": {"type": ["integer", "null"]},
                "section": {"type": ["string", "null"]},
                "label": {"type": ["string", "null"]},
                "field": {"type": "string", "enum": ["graph_theory", "combinatorics", "extremal_combinatorics",
                                                      "discrete_mathematics", "number_theory", "algebra", "geometry", "other"]},
                "subfields": {"type": "array", "items": {"type": "string"}},
                "relevant_theorems": {"type": "array", "items": {"type": "string"}},
                "known_partial_results": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["statement", "location", "is_computational"],
                    "properties": {"statement": {"type": "string"}, "location": {"type": "string"},
                                   "is_computational": {"type": "boolean"}}}},
                "posed_by_this_paper": {"type": "boolean"},
                "confidence": {"type": "number"},
                "rationale": {"type": "string"},
                "ambiguities": {"type": "array", "items": {"type": "string"}},
                "candidate_ids": {"type": "array", "items": {"type": "string"}},
                "difficulty_guess": {"type": "string", "enum": ["accessible", "moderate", "hard", "very_hard", "unknown"]},
                "potential_approaches": {"type": "array", "items": {"type": "string"}},
            }}},
        "rejected_candidates": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["candidate_id", "reason"],
            "properties": {"candidate_id": {"type": "string"}, "reason": {"type": "string"}}}},
    },
}


def _pages(paper: Paper) -> list:
    from sqlalchemy.orm import object_session

    from app.models import PaperPage

    return list(object_session(paper).scalars(
        select(PaperPage).where(PaperPage.paper_id == paper.id).order_by(PaperPage.page_number)))


def _source_text(paper: Paper) -> tuple[str, str]:
    pages = _pages(paper)
    if paper.latex_source:
        body = paper.latex_source
        if pages:  # page markers come from the PDF; give the model both, LaTeX for exact wording
            pdf = "\n".join(f"=== PAGE {p.page_number} ===\n{p.text}" for p in pages)
            return f"<latex_source>\n{body}\n</latex_source>\n\n<pdf_text>\n{pdf}\n</pdf_text>", "latex+pdf"
        return f"<latex_source>\n{body}\n</latex_source>", "latex"
    if pages:
        return "<pdf_text>\n" + "\n".join(f"=== PAGE {p.page_number} ===\n{p.text}" for p in pages) + "\n</pdf_text>", "pdf"
    return f"<abstract>\n{paper.abstract or ''}\n</abstract>", "abstract"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def wording_found(quote: str, paper: Paper) -> bool:
    """True if the quote occurs in the LaTeX/PDF text (whitespace-insensitive, or as plain words)."""
    if not quote.strip():
        return False
    q = _norm(quote)
    hay = [_norm(paper.latex_source or "")] + [_norm(p.text) for p in _pages(paper)]
    if any(q in h for h in hay):
        return True
    qw = " ".join(re.findall(r"[a-z]{3,}", latex_to_plain(quote).lower()))
    if len(qw) < 20:
        return False
    plain = [" ".join(re.findall(r"[a-z]{3,}", latex_to_plain(h).lower())) for h in hay]
    return any(qw in h for h in plain)


def extract_with_llm(db: Session, paper_id: str, *, job_id: str | None, provider: str | None = None) -> dict:
    paper = db.get(Paper, paper_id)
    text, origin = _source_text(paper)
    if len(text) > MAX_SOURCE_CHARS:
        raise ValueError(f"Paper text is {len(text):,} chars (> {MAX_SOURCE_CHARS:,}); refusing to truncate silently.")
    cands = db.scalars(select(CandidatePassage).where(CandidatePassage.paper_id == paper_id,
                                                      CandidatePassage.detector == "heuristic")).all()
    cand_txt = "\n\n".join(
        f"[candidate_id={c.id}] origin={c.origin} page={c.page_number} section={c.section!r} trigger={c.trigger!r}\n{c.passage[:1500]}"
        for c in cands) or "(none)"
    prompt = (f"Paper: {paper.title}\nAuthors: {', '.join(paper.authors or [])}\n"
              f"arXiv: {paper.arxiv_id or '-'}  DOI: {paper.doi or '-'}  Published: {paper.published_date or '-'}\n\n"
              f"Heuristic candidate passages (high recall, many false positives — accept or reject each):\n{cand_txt}\n\n"
              f"Full source ({origin}):\n{text}")
    res = tracked_json_call(purpose="conjecture_extraction", system=SYSTEM, prompt=prompt, schema=SCHEMA,
                            provider=provider, job_id=job_id, subject_id=paper_id, effort="high")
    detector = f"llm:{res.provider}:{res.model}"
    created = 0
    for i, item in enumerate(res.data.get("problems", [])):
        found = wording_found(item.get("original_wording", ""), paper)
        item["wording_verified_in_source"] = found
        passage = item.get("original_wording") or item.get("normalized_statement", "")
        db.add(CandidatePassage(
            paper_id=paper_id, page_number=item.get("page"), section=item.get("section"), origin=origin.split("+")[0],
            label=item.get("label") or item.get("title"), char_start=-(i + 1), passage=passage,
            trigger="llm extraction", kind=item.get("kind", "unknown"), detector=detector,
            score=float(item.get("confidence") or 0), llm_assessment=item,
        ))
        created += 1
    by_id = {c.id: c for c in cands}
    for rej in res.data.get("rejected_candidates", []):
        c = by_id.get(rej.get("candidate_id"))
        if c and c.review_status == "pending":
            c.llm_assessment = {"llm_verdict": "rejected", "reason": rej.get("reason"), "by": detector}
    db.commit()
    return {"paper_id": paper_id, "problems": created, "rejected": len(res.data.get("rejected_candidates", [])),
            "model": res.model, "cost_usd": round(res.cost_usd, 4),
            "tokens": {"input": res.input_tokens, "output": res.output_tokens}}

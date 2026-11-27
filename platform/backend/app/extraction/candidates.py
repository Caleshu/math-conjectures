"""Heuristic detection of *candidate* open-problem passages.

This is deliberately a high-recall pre-filter, not the extractor. Its output is stored as
`CandidatePassage(detector="heuristic", review_status="pending")` and is never shown as a
conjecture until a person (or the LLM extraction agent, with its reasoning stored) reviews it.

Two inputs are scanned:
- LaTeX source: theorem-like environments whose display name is Conjecture/Problem/Question,
  plus trigger phrases inside paragraphs. Gives exact original wording.
- PDF text: trigger phrases and "Conjecture 5.1." style headings. Gives page numbers.
LaTeX hits are mapped back to PDF pages by matching a run of plain words.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

ENV_KINDS = {
    "conjecture": "conjecture", "conj": "conjecture", "problem": "open_problem", "openproblem": "open_problem",
    "question": "open_question", "ques": "open_question", "qn": "open_question",
}

# (regex, kind, score). Lower score = weaker signal.
PHRASES: list[tuple[str, str, float]] = [
    (r"\bwe conjecture\b", "conjecture", 0.8),
    (r"\bit (?:remains|is still) (?:an )?open (?:whether|if|to|problem|question)\b", "open_question", 0.8),
    (r"\bremains? open\b", "open_question", 0.6),
    (r"\b(?:is|are) (?:still )?(?:wide )?open\b", "open_question", 0.45),
    (r"\bwe leave (?:the following|it as an open|as an open|open)\b", "open_problem", 0.8),
    (r"\bopen (?:problem|question)s?\b", "open_problem", 0.6),
    (r"\b(?:an|one|another) interesting (?:open )?(?:question|problem)\b", "open_question", 0.6),
    (r"\bit would be interesting to (?:determine|know|decide|find|characteri[sz]e|see|prove)\b", "future_research", 0.6),
    (r"\bwe (?:believe|suspect|expect) that\b", "conjecture", 0.4),
    (r"\b(?:we|one) (?:may|might|can) ask (?:whether|if)\b", "open_question", 0.55),
    (r"\b(?:natural|following) question\b", "open_question", 0.5),
    (r"\bconjectured? (?:that|by)\b", "conjecture", 0.6),
    (r"\bthe (?:best|exact) (?:possible )?(?:bound|constant|value) (?:is|remains) (?:unknown|open)\b", "unresolved_bound", 0.75),
    (r"\b(?:determine|find|calculate|compute) the exact value\b", "unresolved_bound", 0.5),
    (r"\b(?:future|further) (?:work|research|study)\b", "future_research", 0.35),
    (r"\bwe do not know (?:whether|if)\b", "open_question", 0.7),
    (r"\bis (?:it )?true that\b.*\?", "open_question", 0.55),
    (r"\bas open problems\b|\bas conjectures\b", "open_problem", 0.75),
    (r"\b(?:characteri[sz]e|classify) (?:all|the)\b", "open_problem", 0.4),
]
_PHRASE_RE = [(re.compile(p, re.IGNORECASE | re.DOTALL), k, s) for p, k, s in PHRASES]
# A numbered statement at the start of a line, e.g. "Conjecture 5.1 (Name). Let n ..." — not an in-text
# mention such as "explore Conjecture 5.1 it ..." or "Conjecture 5.1 holds for n <= 7".
_PDF_HEADING = re.compile(
    r"(?m)^[ \t]*(Conjecture|Open [Pp]roblem|Problem|Question)\s+(\d+(?:\.\d+)*)\.?[ \t]*(\([^)]{0,160}\))?[ \t]*[.:](?=\s)")


@dataclass
class Candidate:
    origin: str  # pdf | latex | abstract
    passage: str
    char_start: int
    kind: str
    trigger: str
    score: float
    page_number: int | None = None
    section: str | None = None
    label: str | None = None
    context_before: str = ""
    context_after: str = ""
    extra: dict = field(default_factory=dict)


# ------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------
def _sentence_window(text: str, start: int, end: int, before: int = 1, after: int = 2) -> tuple[int, int]:
    """Expand [start,end) to whole sentences: `before` sentences before, `after` after."""
    bounds = [0] + [m.end() for m in re.finditer(r"(?<=[.?!])\s+(?=[A-Z(\\$])|\n\s*\n", text)] + [len(text)]
    i = max(j for j, b in enumerate(bounds) if b <= start)
    k = min((j for j, b in enumerate(bounds) if b >= end), default=len(bounds) - 1)
    s = bounds[max(0, i - before + 1) if before else i]
    e = bounds[min(len(bounds) - 1, k + after - 1)] if after else bounds[k]
    if e - s > 1600:  # keep passages readable
        s, e = max(s, start - 400), min(e, end + 1000)
    return s, e


def latex_to_plain(s: str) -> str:
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(r"\\(?:label|ref|cite|eqref)\{[^}]*\}", " ", s)
    s = re.sub(r"\$[^$]*\$", " ", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}~\\]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _words(s: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", s.lower())


def locate_page(passage_plain: str, pages: list[str]) -> int | None:
    """Find the PDF page containing a run of 6 consecutive words from the passage."""
    w = _words(passage_plain)
    if len(w) < 4:
        return None
    norm_pages = [" ".join(_words(p)) for p in pages]
    for size in (6, 5, 4):
        for i in range(0, max(1, len(w) - size + 1), 2):
            probe = " ".join(w[i:i + size])
            hits = [n for n, p in enumerate(norm_pages, 1) if probe in p]
            if len(hits) == 1:
                return hits[0]
    return None


def _overlap(a: str, b: str) -> float:
    sa, sb = set(_words(a)), set(_words(b))
    return len(sa & sb) / max(1, min(len(sa), len(sb)))


# ------------------------------------------------------------------------------------------
# LaTeX scan
# ------------------------------------------------------------------------------------------
def latex_environments(tex: str) -> dict[str, str]:
    """Map environment name -> display name from \\newtheorem declarations."""
    envs = {}
    for m in re.finditer(r"\\(?:newtheorem|declaretheorem)\*?\{([^}]+)\}(?:\[[^\]]*\])?\{([^}]+)\}", tex):
        envs[m.group(1).strip()] = m.group(2).strip()
    return envs


def scan_latex(tex: str) -> list[Candidate]:
    body_start = tex.find("\\begin{document}")
    body_start = body_start if body_start >= 0 else 0
    bib = re.search(r"\\begin\{thebibliography\}|\\bibliography\{", tex)
    body_end = bib.start() if bib else len(tex)
    envs = latex_environments(tex)
    kinds: dict[str, str] = {}
    for env, display in envs.items():
        key = re.sub(r"[^a-z]", "", display.lower())
        for k, kind in ENV_KINDS.items():
            if key.startswith(k) or re.sub(r"[^a-z]", "", env.lower()) == k:
                kinds[env] = kind
    for env in ("conjecture", "problem", "question", "openproblem"):
        kinds.setdefault(env, ENV_KINDS[env])

    sections = [(m.start(), m.group(2)) for m in re.finditer(r"\\(section|subsection)\*?\{([^}]*)\}", tex)]

    def section_at(pos: int) -> str | None:
        prev = [t for p, t in sections if p <= pos]
        return latex_to_plain(prev[-1]) if prev else None

    out: list[Candidate] = []
    covered: list[tuple[int, int]] = []
    for env, kind in kinds.items():
        pat = re.compile(r"\\begin\{" + re.escape(env) + r"\}(\[[^\]]*\])?(.*?)\\end\{" + re.escape(env) + r"\}", re.S)
        for m in pat.finditer(tex, body_start, body_end):
            label_m = re.search(r"\\label\{([^}]+)\}", m.group(2))
            out.append(Candidate(
                origin="latex", passage=m.group(0).strip(), char_start=m.start(), kind=kind,
                trigger=f"\\begin{{{env}}}", score=0.95, section=section_at(m.start()),
                label=(envs.get(env, env.title()) + (f" {m.group(1)}" if m.group(1) else "")
                       + (f" [{label_m.group(1)}]" if label_m else "")),
                context_before=tex[max(body_start, m.start() - 600):m.start()],
                context_after=tex[m.end():m.end() + 600],
            ))
            covered.append((m.start(), m.end()))

    body = tex[:body_end]
    for rx, kind, score in _PHRASE_RE:
        for m in rx.finditer(body, body_start):
            if any(a <= m.start() < b for a, b in covered):
                continue
            # strip comments before scoring the match
            line_start = body.rfind("\n", 0, m.start()) + 1
            if "%" in body[line_start:m.start()].replace("\\%", ""):
                continue
            s, e = _latex_block(body, m.start(), m.end())
            out.append(Candidate(
                origin="latex", passage=body[s:e].strip(), char_start=s, kind=kind, trigger=m.group(0),
                score=score, section=section_at(s), context_before=body[max(0, s - 500):s],
                context_after=body[e:e + 500],
            ))
            covered.append((s, e))
    return _merge_overlaps(out)


def _latex_block(text: str, start: int, end: int) -> tuple[int, int]:
    """For LaTeX: a paragraph, or an itemize list when the trigger introduces one."""
    s = text.rfind("\n\n", 0, start)
    s = 0 if s < 0 else s + 2
    e = text.find("\n\n", end)
    e = len(text) if e < 0 else e
    after = text[end:end + 300]
    if re.search(r"\\begin\{(itemize|enumerate)\}", after):
        lst = re.search(r"\\end\{(itemize|enumerate)\}", text[end:])
        if lst:
            e = end + lst.end()
    if e - s > 4000:
        s, e = _sentence_window(text, start, end)
    return s, e


def _merge_overlaps(cands: list[Candidate]) -> list[Candidate]:
    cands.sort(key=lambda c: (c.char_start, -c.score))
    out: list[Candidate] = []
    for c in cands:
        if out and c.origin == out[-1].origin and c.char_start < out[-1].char_start + len(out[-1].passage):
            prev = out[-1]
            if c.score > prev.score:
                prev.kind, prev.score = c.kind, c.score
            prev.trigger = f"{prev.trigger}; {c.trigger}" if c.trigger not in prev.trigger else prev.trigger
            end = max(prev.char_start + len(prev.passage), c.char_start + len(c.passage))
            if end > prev.char_start + len(prev.passage):
                prev.extra["truncated_merge"] = True
            continue
        out.append(c)
    return out


# ------------------------------------------------------------------------------------------
# PDF scan
# ------------------------------------------------------------------------------------------
def scan_pdf_pages(pages: list[str], sections: list[dict] | None = None) -> list[Candidate]:
    sections = sections or []
    refs_page = next((s["page"] for s in sections if s.get("title", "").lower().startswith("references") and s.get("page")), None)

    def section_for(page: int, pos: int, text: str) -> str | None:
        prev = [s["title"] for s in sections if s.get("page") and s["page"] < page]
        same = [s["title"] for s in sections if s.get("page") == page and text.find(s["title"].split(" ", 1)[-1]) <= pos]
        return (same or prev or [None])[-1]

    out: list[Candidate] = []
    offset = 0
    for pno, text in enumerate(pages, 1):
        if refs_page and pno > refs_page:
            break
        hits: list[tuple[int, int, str, str, float, str | None]] = []
        for m in _PDF_HEADING.finditer(text):
            kind = {"conjecture": "conjecture", "question": "open_question"}.get(m.group(1).lower(), "open_problem")
            hits.append((m.start(), m.end(), kind, m.group(0), 0.9, f"{m.group(1)} {m.group(2)}"))
        for rx, kind, score in _PHRASE_RE:
            for m in rx.finditer(text):
                hits.append((m.start(), m.end(), kind, m.group(0), score, None))
        for start, end, kind, trig, score, label in hits:
            s, e = _sentence_window(text, start, end, before=1 if label is None else 0, after=2 if label is None else 3)
            out.append(Candidate(
                origin="pdf", passage=re.sub(r"[ \t]+", " ", text[s:e]).strip(), char_start=offset + s, kind=kind,
                trigger=trig.strip(), score=score, page_number=pno, label=label,
                section=section_for(pno, s, text), context_before=text[max(0, s - 400):s],
                context_after=text[e:e + 400],
            ))
        offset += len(text) + 1
    return _merge_overlaps(out)


def detect_candidates(pages: list[str], latex: str | None, sections: list[dict] | None = None,
                      abstract: str | None = None) -> list[Candidate]:
    pdf_c = scan_pdf_pages(pages, sections) if pages else []
    if not latex:
        result = pdf_c
    else:
        tex_c = scan_latex(latex)
        for c in tex_c:
            c.page_number = locate_page(latex_to_plain(c.passage), pages) if pages else None
        # Drop PDF hits that duplicate a LaTeX hit (the LaTeX one has exact wording).
        kept = [p for p in pdf_c if not any(
            (t.page_number in (None, p.page_number)) and _overlap(latex_to_plain(t.passage), p.passage) > 0.6
            for t in tex_c)]
        result = tex_c + kept
    if abstract and not pages and not latex:
        for rx, kind, score in _PHRASE_RE:
            m = rx.search(abstract)
            if m:
                result.append(Candidate(origin="abstract", passage=abstract, char_start=0, kind=kind,
                                        trigger=m.group(0), score=score * 0.8))
                break
    result.sort(key=lambda c: (-c.score, c.page_number or 0))
    return result

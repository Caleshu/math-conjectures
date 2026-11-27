"""Extract simple \\newcommand / \\def macros from a LaTeX preamble so the UI (KaTeX) can render the
paper's original wording with the author's own notation, e.g. \\hyp{n} -> Q_{n}."""
from __future__ import annotations

import re

_UNSAFE = re.compile(r"\$|\\(?:hbox|mbox|rule|input|include|write|immediate|openout|catcode|def|newcommand)\b")


def _strip_comments(tex: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in tex.splitlines())


def _braced(s: str, i: int) -> tuple[str, int] | None:
    """Return (content, index after closing brace) for a {...} group starting at s[i] == '{'."""
    if i >= len(s) or s[i] != "{":
        return None
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    return None


def extract_macros(tex: str | None, limit: int = 200) -> dict[str, str]:
    if not tex:
        return {}
    end = tex.find("\\begin{document}")
    pre = _strip_comments(tex[: end if end > 0 else 20000])
    out: dict[str, str] = {}
    for m in re.finditer(r"\\(?:re)?newcommand\*?\s*\{?\s*(\\[A-Za-z]+)\s*\}?\s*(?:\[(\d)\])?\s*", pre):
        g = _braced(pre, m.end())
        if not g:
            continue
        body = g[0].strip()
        if _UNSAFE.search(body) or len(body) > 300:
            continue
        out[m.group(1)] = body
    for m in re.finditer(r"\\def\s*(\\[A-Za-z]+)((?:#\d)*)\s*", pre):
        g = _braced(pre, m.end())
        if g and not _UNSAFE.search(g[0]) and len(g[0]) <= 300:
            out.setdefault(m.group(1), g[0].strip())
        if len(out) >= limit:
            break
    return out

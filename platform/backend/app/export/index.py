"""Categorised problem index for the repository README, backed by `problems.toml`.

`problems.toml` (repo root) is the human-editable registry for the user's own problem folders:

    [HypercubeSquares]
    title = "Inscribed squares in hypercube Hamiltonian cycles (Sagols–Morales-Luna)"
    category = "disproved"            # open | proved | disproved | notes
    result = "Lean-verified square-free Hamiltonian cycle of Q_8 ..."
    verification = "Lean-verified"

Problems researched by MathResearchLab (folders with a `.mathresearchlab` marker) are categorised from the
app database and are not stored in the registry. The README section between the markers is regenerated on
every sync. Folders the registry does not know yet (created by another session or by
scripts/new-conjecture.sh) are imported automatically. Their category is guessed from the folder README's
**Status:** line, their text comes from any index line already in the README, and they are flagged
`auto = true` so they can be reviewed. Nothing is dropped: every folder appears in exactly one section.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

BEGIN = "<!-- problems:begin (generated from problems.toml and MathResearchLab; edit problems.toml, not this block) -->"
END = "<!-- problems:end -->"
CATS = ("proved", "disproved", "open", "notes")
LINE_RE = re.compile(r"^- \[(?P<title>.+?)\]\(Conjectures/(?P<folder>[^/)]+)/?\)\s*(?:—|-)?\s*(?P<text>.*)$")


def _q(s: str) -> str:
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def load(repo: Path) -> dict[str, dict]:
    p = repo / "problems.toml"
    if not p.exists():
        return {}
    return tomllib.loads(p.read_text())


def save(repo: Path, reg: dict[str, dict]) -> None:
    out = ["# Registry of problems in Conjectures/. Each table is keyed by the folder name.",
           "# category: open | proved | disproved | notes. The README tables are generated from this file",
           "# (plus MathResearchLab's own problems), so edit here, not in the README.", ""]
    for folder, e in reg.items():
        out.append(f"[{folder}]")
        for k in ("title", "category", "result", "verification"):
            out.append(f"{k} = {_q(e.get(k, ''))}")
        if e.get("auto"):
            out.append("auto = true  # imported automatically; check the category")
        out.append("")
    (repo / "problems.toml").write_text("\n".join(out))


def guess_category(status_text: str) -> str:
    t = status_text.lower()
    if re.search(r"\*\*false\*\*|\bdisproved\b|answer(?:ed)?:? \**no|\bfails\b|counterexample (?:found|exists)|is false", t):
        return "disproved"
    if re.search(r"\*\*proved\*\*|\bproved\b(?! for)|\bsolved\b|theorem holds|answer(?:ed)?:? \**yes", t) and "open" not in t[:12]:
        return "proved"
    return "open"


def guess_verification(text: str) -> str:
    t = text.lower()
    if "lean-verified" in t or "lean verified" in t or "kernel" in t:
        return "Lean-verified"
    if "computer-assisted" in t or "gap" in t:
        return "Computer-assisted"
    if "exhaustive" in t or "computer-verified" in t or "holds for" in t or "no counterexample" in t:
        return "Computational evidence"
    if "formalized" in t or "formalised" in t:
        return "Statement formalized in Lean"
    return ""


def folder_status_line(folder: Path) -> str:
    r = folder / "README.md"
    if not r.exists():
        return ""
    m = re.search(r"\*\*Status:\*\*\s*(.+)", r.read_text())
    return m.group(1).strip() if m else ""


def sync_registry(repo: Path, readme_text: str, app_folders: set[str]) -> dict[str, dict]:
    """Make sure every user folder has a registry entry; import unknown ones from README lines / Status lines."""
    reg = load(repo)
    lines = {m.group("folder"): m for m in (LINE_RE.match(l.strip()) for l in readme_text.split("\n")) if m}
    for d in sorted(p for p in (repo / "Conjectures").iterdir() if p.is_dir()):
        if d.name in app_folders or d.name in reg or (d / ".mathresearchlab").exists():
            continue
        m = lines.get(d.name)
        status = folder_status_line(d)
        text = (m.group("text") if m else "") or status
        cat = "notes" if d.name.lower().startswith(("handoff", "notes")) else guess_category(text or status)
        reg[d.name] = {"title": m.group("title") if m else d.name, "category": cat, "result": text,
                       "verification": guess_verification(text + " " + status), "auto": True}
    for gone in [f for f in reg if not (repo / "Conjectures" / f).is_dir()]:
        del reg[gone]
    return reg


def _cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def render_block(reg: dict[str, dict], app_entries: dict[str, dict]) -> str:
    items = [{"folder": f, **e, "app": False} for f, e in reg.items()] + \
            [{"folder": f, **e, "app": True} for f, e in app_entries.items()]
    by = {c: [i for i in items if i.get("category") == c] for c in CATS}
    for c in CATS:
        by[c].sort(key=lambda i: i["title"].lower())
    L = [BEGIN, "", "## Status at a glance", "",
         "| ✅ Proved (true) | ❌ Disproved (false) | ⏳ Open |", "|:-:|:-:|:-:|",
         f"| **{len(by['proved'])}** | **{len(by['disproved'])}** | **{len(by['open'])}** |", "",
         "*Verification* says how a result is known. **Lean-verified**: checked by the Lean kernel. "
         "**Computer-assisted / computer-checked**: an exact computation, reproducible from the folder. "
         "**AI research**: produced by MathResearchLab's AI agents and not yet checked by a human. Treat it as "
         "a lead, not a theorem. Problems marked 🤖 were found and researched by MathResearchLab (`platform/`). "
         "New folders are picked up automatically. To change a problem's category or summary, edit `problems.toml`.", ""]
    heads = {"proved": ("## ✅ Proved — true", "Result"), "disproved": ("## ❌ Disproved — false", "Result"),
             "open": ("## ⏳ Open", "Progress so far"), "notes": ("## 📝 Notes and handoffs", "Contents")}
    for c in ("proved", "disproved", "open", "notes"):
        if not by[c] and c == "notes":
            continue
        h, col = heads[c]
        L += [h, ""]
        if not by[c]:
            L += ["*None yet.*", ""]
            continue
        if c == "notes":
            L += [f"- [{i['title']}](Conjectures/{i['folder']}/): {i.get('result', '')}" for i in by[c]] + [""]
            continue
        L += [f"| Problem | {col} | Verification |", "|---|---|---|"]
        for i in by[c]:
            mark = " 🤖" if i["app"] else ""
            L.append(f"| [{_cell(i['title'])}](Conjectures/{i['folder']}/){mark} | {_cell(i.get('result', ''))} | "
                     f"{_cell(i.get('verification', ''))} |")
        L.append("")
    L.append(END)
    return "\n".join(L)


def rewrite_readme(text: str, block: str, known_folders: set[str]) -> str:
    """Replace the generated block (or, the first time, the whole '## Conjectures' section) with `block`.
    Stray index lines for known folders elsewhere in the README (e.g. appended by scripts/new-conjecture.sh)
    are removed, because they now live in the tables."""
    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        _, post = rest.split(END, 1)
    else:
        # First run: drop the old '## Conjectures' list and put the tables right after the intro,
        # so the status of every problem is the first thing on the page.
        lines = text.split("\n")
        try:
            s = next(i for i, l in enumerate(lines) if l.strip() == "## Conjectures")
            e = s + 1
            while e < len(lines) and not lines[e].startswith("## "):
                e += 1
            lines = lines[:s] + lines[e:]
        except StopIteration:
            pass
        first_h2 = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
        pre = "\n".join(lines[:first_h2]).rstrip("\n") + "\n\n"
        post = "\n\n" + "\n".join(lines[first_h2:]).strip("\n") + "\n" if first_h2 < len(lines) else "\n"
    keep_lines = []
    for l in (pre + "\u0000" + post).split("\n"):
        m = LINE_RE.match(l.strip())
        if m and m.group("folder") in known_folders:
            continue
        keep_lines.append(l)
    pre, post = "\n".join(keep_lines).split("\u0000", 1)
    return pre + block + (post if post.startswith("\n") else ("\n" + post if post.strip() else "\n"))

from app.extraction.candidates import detect_candidates, scan_latex, scan_pdf_pages
from app.extraction.latex_macros import extract_macros

TEX = r"""\documentclass{article}
\newtheorem{conjecture}{Conjecture}[section]
\newcommand{\hyp}[1]{Q_{#1}}
\begin{document}
\section{Introduction}
We study cycles. As an application we conjecture that every cycle is nice.

\section{Squares}
\begin{conjecture}[Nice cycles] \label{c:nice} Let $n \ge 2$. Every Hamiltonian cycle of $\hyp{n}$ is nice.
\end{conjecture}
\begin{theorem} Conjecture~\ref{c:nice} holds for $n \le 3$. \end{theorem}

\section{Conclusions}
As open problems, let us state the following:
\begin{itemize}
\item {\em Characterize nice cycles.}
\end{itemize}
% It remains open whether this commented line matters.
\begin{thebibliography}{9}\bibitem{x} It remains open whether bibliography counts.\end{thebibliography}
\end{document}
"""

PAGES = [
    "1 Introduction\nWe study cycles. As an application we conjecture that every cycle is nice.\n",
    "2 Squares\nConjecture 2.1 (Nice cycles). Let n ≥ 2. Every Hamiltonian cycle of Qn is nice.\n"
    "Theorem 2.2. Conjecture 2.1 holds for n ≤ 3.\nTo explore Conjecture 2.1 we compute.\n",
    "3 Conclusions\nAs open problems, let us state the following:\n• Characterize nice cycles.\n",
]


def test_latex_environment_is_found_with_label_and_section():
    cands = scan_latex(TEX)
    env = [c for c in cands if c.trigger == "\\begin{conjecture}"]
    assert len(env) == 1
    assert env[0].section == "Squares" and "c:nice" in env[0].label and env[0].kind == "conjecture"
    assert "\\hyp{n}" in env[0].passage  # verbatim, not rewritten


def test_comments_and_bibliography_are_ignored():
    texts = " ".join(c.passage for c in scan_latex(TEX))
    assert "commented line" not in texts and "bibliography counts" not in texts


def test_pdf_heading_ignores_in_text_mentions():
    cands = scan_pdf_pages(PAGES)
    labels = [c.label for c in cands if c.label]
    assert labels == ["Conjecture 2.1"]  # not "explore Conjecture 2.1" nor "Conjecture 2.1 holds"


def test_latex_candidates_mapped_to_pdf_pages_and_deduplicated():
    cands = detect_candidates(PAGES, TEX)
    env = next(c for c in cands if c.trigger == "\\begin{conjecture}")
    assert env.page_number == 2
    assert not any(c.origin == "pdf" and c.label == "Conjecture 2.1" for c in cands)  # LaTeX version kept instead
    assert any("open problems" in c.trigger.lower() for c in cands)


def test_macros():
    m = extract_macros(TEX)
    assert m["\\hyp"] == "Q_{#1}"

"""Build the demonstration record for the inscribed-squares conjecture through the real pipeline.

Nothing here is canned data: the paper is fetched from arXiv/OpenAlex, its PDF and LaTeX are
processed, the conjecture's original wording is taken verbatim from the detected LaTeX
environment, and the experiment is executed in the sandbox. The only hand-written content is the
normalized statement and the definitions (as a human reviewer would write them), and the two
known results quoted from the paper.

Usage:  python -m scripts.seed_demo [--skip-experiment] [--max-n 7]
Idempotent: re-running reuses the existing paper and conjecture.
"""
from __future__ import annotations

import argparse
import hashlib

from sqlalchemy import select

from app.config import BACKEND_DIR
from app.db import SessionLocal, session_scope
from app.jobs.handlers import run_experiment
from app.models import CandidatePassage, Conjecture, Experiment
from app.services import conjectures as conj_svc
from app.services import papers as paper_svc

ARXIV = "1009.3304"
SLUG = "inscribed-squares-in-hamiltonian-cycles-of-the-hypercube"
ACTOR = "seed-script"

NORMALIZED = (r"For every integer $n \ge 2$ and every Hamiltonian cycle $H$ of the hypercube $Q_n$, there exists a "
              r"4-cycle $v_0v_1v_2v_3$ of $Q_n$ such that $H$ contains both edges $v_0v_1$ and $v_2v_3$, i.e. two "
              r"opposite edges of a 4-cycle of $Q_n$ (an inscribed square).")
DEFINITIONS = [
    {"term": "Hypercube $Q_n$", "definition": r"The graph with vertex set $\{0,1\}^n$ in which two vertices are adjacent "
                                              r"iff they differ in exactly one coordinate."},
    {"term": "Inscribed (straight or twisted) square",
     "definition": r"A 4-cycle $v_0v_1v_2v_3$ of $Q_n$ is inscribed in a Hamiltonian cycle $h=h_0\cdots h_{2^n-1}$ if "
                   r"there are indices $i,j$ with $h_ih_{i+1}h_jh_{j+1}=v_0v_1v_2v_3$ (straight) or $=v_0v_1v_3v_2$ "
                   r"(twisted); equivalently, both opposite edges $v_0v_1$ and $v_2v_3$ (the rims) lie on $h$. A "
                   r"Hamiltonian cycle with no inscribed square is square-free."},
]


def log(msg: str) -> None:
    print(f"[seed] {msg}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-experiment", action="store_true")
    ap.add_argument("--max-n", type=int, default=7)
    args = ap.parse_args()

    log(f"resolving arXiv:{ARXIV}")
    rec = paper_svc.resolve_identifier(f"arXiv:{ARXIV}")
    with session_scope() as db:
        paper, created = paper_svc.upsert_paper(db, rec, "seed")
        pid = paper.id
    log(f"paper {'created' if created else 'already indexed'}: {pid}")
    db = SessionLocal()
    try:
        out = paper_svc.process_paper(db, pid, lambda stage, info=None: log(f"  {stage}"))
        log(f"processed: {out}")

        conj = db.scalars(select(Conjecture).where(Conjecture.slug == SLUG)).first()
        if conj:
            log("conjecture already recorded")
        else:
            cand = db.scalars(select(CandidatePassage).where(
                CandidatePassage.paper_id == pid, CandidatePassage.trigger == "\\begin{conjecture}")).first()
            if not cand:
                raise SystemExit("Expected LaTeX conjecture environment was not detected; aborting.")
            page = cand.page_number
            conj = conj_svc.create_conjecture(db, {
                "title": "Inscribed squares in Hamiltonian cycles of the hypercube", "field": "graph_theory",
                "subfields": ["hypercubes", "Hamiltonian cycles"], "original_statement": cand.passage,
                "normalized_statement": NORMALIZED, "definitions": DEFINITIONS, "difficulty_estimate": "unknown",
                "extraction_details": {"extracted_by": "heuristic+seed-script", "trigger": cand.trigger},
                "known_results": [
                    {"statement": r"The conjecture holds for $2 \le n \le 7$.",
                     "citation": "Sagols & Morales-Luna (2010), arXiv:1009.3304, Theorem 5.4", "source_paper_id": pid,
                     "location": "Section 5", "is_computational": True, "reproduced": None,
                     "note": "Derived from alpha_=(Q_6)=16 (Table 1 of the paper, obtained computationally). "
                             "Unverified until independently reproduced."},
                    {"statement": r"Any Hamiltonian cycle of $Q_n$ containing more than $2^{n-2}$ edges in the same "
                                  r"dimension contains an inscribed square.",
                     "citation": "Sagols & Morales-Luna (2010), arXiv:1009.3304, abstract and Section 5",
                     "source_paper_id": pid, "location": "Abstract; Section 5", "is_computational": False,
                     "reproduced": None},
                ],
            }, actor=ACTOR, candidate=cand)
            log(f"conjecture recorded from candidate on page {page}: {conj.slug}")
        db.commit()
        cid = conj.id
    finally:
        db.close()

    if args.skip_experiment:
        return
    code = (BACKEND_DIR / "experiments" / "library" / "hypercube_inscribed_squares.py").read_text()
    params = {"enumerate_n": [2, 3, 4], "cpsat_n": list(range(2, args.max_n + 1)),
              "sanity_n": list(range(2, args.max_n + 1)), "min_squares_n": [2, 3, 4],
              "time_limit_s": 600, "workers": 8, "seed": 0}
    with session_scope() as s:
        exp = Experiment(conjecture_id=cid, title="Square-free Hamiltonian cycles in Q_n (enumeration + CP-SAT)",
                         problem="Search for a counterexample to the inscribed-squares conjecture.", code=code,
                         code_sha256=hashlib.sha256(code.encode()).hexdigest(),
                         library_script="hypercube_inscribed_squares", parameters=params,
                         settings={"timeout_s": 1500, "memory_mb": 4096}, result_kind="finite_computation",
                         created_by=ACTOR)
        s.add(exp)
        s.flush()
        eid = exp.id
    log(f"running experiment {eid} in sandbox (n <= {args.max_n})")
    res = run_experiment("seed", {"experiment_id": eid}, lambda *a, **k: None)
    with session_scope() as s:
        e = s.get(Experiment, eid)
        log(f"experiment {res['status']} in {res['runtime_seconds']}s; summary: {(e.result or {}).get('summary')}")


if __name__ == "__main__":
    main()

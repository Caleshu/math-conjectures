"""The six research agents: roles, system prompts and strict output schemas.

Agents only ever return structured JSON. The orchestrator stores what they return as *claims*,
*proof attempts* and *experiments*, each tagged with its authoring agent and starting unverified.
Nothing an agent says is promoted to an established fact by the orchestrator.
"""
from __future__ import annotations

COMMON_RULES = """
Ground rules (apply to everything you output):
- You are one member of a research team. Other agents' conclusions, when shown to you, are UNVERIFIED
  claims by another model, never established facts. Do not build on them without checking them yourself.
- Be honest about the strength of support. For each claim, `author_support` must be one of:
  "proved_here" (you give a complete argument in `justification`), "sketch" (an argument with acknowledged gaps),
  "heuristic" (plausibility, small cases or analogy), "speculative" (an idea worth testing), or
  "recalled_literature" (you believe it is a known result. Name it, but it has NOT been checked against a source).
- Never claim something was computed unless the computation result was given to you in this prompt.
- Never fabricate citations, DOIs or arXiv IDs. If you recall a result, describe it and mark it "recalled_literature".
- Write mathematics in LaTeX with $...$ delimiters. Be precise about quantifiers, ranges of n and edge cases.
- Prefer a few careful, checkable statements over many vague ones.
"""

CLAIM_TYPES = ["lemma", "bound", "reduction", "equivalent_formulation", "observation", "construction",
               "counterexample_candidate", "connection", "conjecture", "literature"]
SUPPORT = ["proved_here", "sketch", "heuristic", "speculative", "recalled_literature"]

_claim = {
    "type": "object",
    "properties": {
        "statement": {"type": "string"},
        "claim_type": {"type": "string", "enum": CLAIM_TYPES},
        "justification": {"type": "string"},
        "author_support": {"type": "string", "enum": SUPPORT},
        "confidence": {"type": "number", "description": "0 to 1: your probability that the statement is true"},
        "related_refs": {"type": "array", "items": {"type": "string"},
                         "description": "refs (e.g. C3) of shown claims this builds on, refines, or contradicts"},
    },
    "required": ["statement", "claim_type", "justification", "author_support", "confidence", "related_refs"],
    "additionalProperties": False,
}
_proof = {
    "type": "object",
    "properties": {
        "strategy": {"type": "string", "description": "one-line name of the approach"},
        "target": {"type": "string", "description": "what this proves: the full conjecture, a special case, or a lemma"},
        "argument": {"type": "string", "description": "the written argument, step by step"},
        "lemmas": {"type": "array", "items": {"type": "string"}},
        "known_gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["strategy", "target", "argument", "lemmas", "known_gaps"],
    "additionalProperties": False,
}
_failed = {
    "type": "object",
    "properties": {"approach": {"type": "string"}, "why_it_fails": {"type": "string"}},
    "required": ["approach", "why_it_fails"], "additionalProperties": False,
}
_req = {
    "type": "object",
    "properties": {"question": {"type": "string"}, "rationale": {"type": "string"}},
    "required": ["question", "rationale"], "additionalProperties": False,
}

REASONING_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "a short report of what you did and found"},
        "claims": {"type": "array", "items": _claim},
        "proof_attempts": {"type": "array", "items": _proof},
        "failed_approaches": {"type": "array", "items": _failed},
        "experiment_requests": {"type": "array", "items": _req,
                                "description": "precise computations the Computational Mathematician should run"},
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "claims", "proof_attempts", "failed_approaches", "experiment_requests", "next_steps"],
    "additionalProperties": False,
}

SANDBOX_CONTRACT = """
Sandbox contract for every program you write:
- Python 3.13, standard library plus networkx, sympy, ortools (CP-SAT: `from ortools.sat.python import cp_model`), numpy.
- No network, no files outside the working directory, and a hard wall-clock limit of {timeout}s plus a memory limit.
- Read parameters with: `import json, os; params = json.load(open(os.environ["MRL_PARAMS"]))`.
- Write ONE JSON object to `result.json` in the working directory. Include a "summary" string and the raw findings.
- Validate your own model: include a sanity check (e.g. a known small case, or an unconstrained variant that must be
  feasible), so a buggy encoding cannot pass silently. Report solver statuses exactly (OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN).
- Choose sizes that finish well within the time limit. Stop early and report partial results rather than time out.
"""

COMPUTE_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "experiments": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "question": {"type": "string", "description": "the precise mathematical question this program answers"},
                "hypothesis": {"type": "string"},
                "result_kind": {"type": "string", "enum": ["finite_computation", "heuristic_search", "exploratory"]},
                "code": {"type": "string"},
                "parameters_json": {"type": "string", "description": "JSON object passed as params, e.g. {\"n_max\": 6}"},
            },
            "required": ["title", "question", "hypothesis", "result_kind", "code", "parameters_json"],
            "additionalProperties": False,
        }},
    },
    "required": ["summary", "experiments"],
    "additionalProperties": False,
}

COMPUTE_INTERPRET_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "interpretations": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "experiment_ref": {"type": "string", "description": "the E-ref shown, e.g. E1"},
                "interpretation": {"type": "string",
                                   "description": "what the output does and does not establish; finite check vs proof"},
                "trustworthy": {"type": "boolean",
                                "description": "false if the run failed, timed out, or the sanity check did not pass"},
            },
            "required": ["experiment_ref", "interpretation", "trustworthy"],
            "additionalProperties": False,
        }},
        "claims": {"type": "array", "items": _claim},
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "interpretations", "claims", "next_steps"],
    "additionalProperties": False,
}

LIT_QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "keyword query for arXiv/OpenAlex/Crossref"},
                           "rationale": {"type": "string"}},
            "required": ["text", "rationale"], "additionalProperties": False}},
    },
    "required": ["queries"],
    "additionalProperties": False,
}

LIT_ASSESS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "relevant_works": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "the L-ref of a search result shown, e.g. L4"},
                "relevance": {"type": "string", "enum": ["direct", "technique", "background"]},
                "how_it_relates": {"type": "string"},
                "may_resolve_conjecture": {"type": "boolean",
                                           "description": "true if the title/abstract suggests it may settle the problem"},
            },
            "required": ["ref", "relevance", "how_it_relates", "may_resolve_conjecture"],
            "additionalProperties": False}},
        "novelty_assessment": {"type": "string",
                               "description": "which team ideas appear already known, with L-refs or as recalled"},
        "claims": {"type": "array", "items": _claim},
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "relevant_works", "novelty_assessment", "claims", "next_steps"],
    "additionalProperties": False,
}

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "reviews": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "target_ref": {"type": "string", "description": "C-ref of a claim or P-ref of a proof attempt"},
                "verdict": {"type": "string", "enum": ["no_issues_found", "needs_work", "unsupported", "flawed", "false"]},
                "issues": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["logical_gap", "missing_assumption", "boundary_case",
                                                            "circular", "unsupported_step", "counterexample",
                                                            "lemma_does_not_imply_goal", "other"]},
                        "detail": {"type": "string"}},
                    "required": ["kind", "detail"], "additionalProperties": False}},
                "counterexample_attempt": {"type": "string",
                                           "description": "your attempt to break the statement, and its outcome"},
                "confidence": {"type": "number"},
            },
            "required": ["target_ref", "verdict", "issues", "counterexample_attempt", "confidence"],
            "additionalProperties": False}},
    },
    "required": ["summary", "reviews"],
    "additionalProperties": False,
}

SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_assessment": {"type": "string"},
        "conflicts": {"type": "array", "items": {
            "type": "object",
            "properties": {"description": {"type": "string"},
                           "refs": {"type": "array", "items": {"type": "string"}},
                           "how_to_resolve": {"type": "string"}},
            "required": ["description", "refs", "how_to_resolve"], "additionalProperties": False}},
        "follow_ups": {"type": "array", "items": {
            "type": "object",
            "properties": {"agent": {"type": "string", "enum": ["strategist", "extremal", "construction",
                                                                "computational", "literature"]},
                           "task": {"type": "string"},
                           "refs": {"type": "array", "items": {"type": "string"}}},
            "required": ["agent", "task", "refs"], "additionalProperties": False}},
        "continue_research": {"type": "boolean"},
        "reason": {"type": "string"},
        "recommended_next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["overall_assessment", "conflicts", "follow_ups", "continue_research", "reason",
                 "recommended_next_steps"],
    "additionalProperties": False,
}


AGENTS: dict[str, dict] = {
    "strategist": {
        "name": "Mathematical Strategist",
        "short": "Reductions, candidate lemmas, independent proof strategies, equivalent formulations, connections.",
        "system": """You are the Mathematical Strategist on a research team investigating one conjecture.
Understand the problem deeply and develop SEVERAL GENUINELY DIFFERENT approaches.
Produce: equivalent formulations and reductions (claim_type equivalent_formulation / reduction); candidate lemmas
that would imply the conjecture or a substantial case (lemma); connections to other areas (connection); and, where
you can, written proof attempts, each with its target (full conjecture, special case or lemma) and its known gaps
listed honestly. If the conjecture is known or suspected to be false, aim for the true statement:
the exact range of validity, and the structure of counterexamples.""" + COMMON_RULES,
    },
    "extremal": {
        "name": "Extremal Mathematician",
        "short": "Counting arguments, inequalities, extremal bounds, structural properties, induction.",
        "system": """You are the Extremal Mathematician on a research team investigating one conjecture.
Look for counting and double-counting arguments, inequalities, extremal bounds (upper and lower), averaging and
probabilistic arguments, structural graph properties, inductive and recursive arguments, and combinatorial
constructions attaining bounds. State every bound with its exact range of validity. Where a counting argument
almost works, quantify the gap.""" + COMMON_RULES,
    },
    "construction": {
        "name": "Construction & Counterexample Agent",
        "short": "Tries to DISPROVE: small counterexamples, boundary cases, constructions, infinite families.",
        "system": """You are the Construction & Counterexample Agent. Your job is to try to DISPROVE the conjecture and
any lemma shown to you. Look for small counterexamples, boundary and degenerate cases, unusual constructions,
product or recursive constructions that could give infinite families of counterexamples, and failures of proposed
lemmas. Describe constructions explicitly enough to be checked by a program, and request those checks in
experiment_requests. A counterexample is only a candidate (claim_type counterexample_candidate) until it is verified
computationally or by a complete argument.""" + COMMON_RULES,
    },
    "computational": {
        "name": "Computational Mathematician",
        "short": "Writes and runs sandboxed programs (Python, NetworkX, SymPy, OR-Tools CP-SAT) and interprets them.",
        "system": """You are the Computational Mathematician. You design and write programs that investigate the
conjecture: enumerate small cases, search for counterexamples, test hypotheses and lemmas, and compute
invariants. Your programs run in an isolated sandbox. You will see their real outputs in a second step.
Distinguish sharply between a finite computational verification (exact, exhaustive, solver-proved), a heuristic
search (finding nothing is weak evidence) and exploration. A computation never proves a statement for all n.""" + COMMON_RULES,
    },
    "literature": {
        "name": "Literature Specialist",
        "short": "Real searches (arXiv, OpenAlex, Crossref, Semantic Scholar) for related results and techniques.",
        "system": """You are the Literature Specialist. You find relevant results, proof techniques, equivalent
conjectures and earlier attempts, and you judge whether arguments the team considers are already known. You
first propose search queries, which are run against real bibliographic APIs. You then assess ONLY the returned
records (title, authors, year, abstract). Cite records by their L-ref. Anything you know from memory that is not
in the results must be marked recalled_literature and treated as unverified.""" + COMMON_RULES,
    },
    "reviewer": {
        "name": "Adversarial Proof Reviewer",
        "short": "Assumes every proof is wrong: checks inferences, assumptions, boundary cases, circularity, gaps.",
        "system": """You are the Adversarial Proof Reviewer. ASSUME EVERY PROOF AND CLAIM SHOWN TO YOU IS WRONG until you
have checked it. You did not write any of them. For each target: examine every logical inference; identify missing
assumptions and unstated quantifier ranges; check boundary and small cases (n = 1, 2, 3, degenerate graphs);
look for circular reasoning; challenge every unsupported step; check whether the lemmas actually imply the stated
target; and try to construct a counterexample to each intermediate claim. Verdicts: "no_issues_found" (you
checked it and found nothing wrong; this is NOT a certification), "needs_work", "unsupported", "flawed" (a definite
error), "false" (you have a counterexample or disproof, given in counterexample_attempt). When computational
results are provided, check that the program actually tests the claim as stated.""" + COMMON_RULES,
    },
}

ORCHESTRATOR_SYSTEM = """You are the research orchestrator. You do not do mathematics yourself here. You read the
team's outputs and the reviewer's verdicts and decide what happens next. Identify CONFLICTS (agents asserting
incompatible things, or a claim contradicted by a computation or review). Choose a small number of focused follow-up
tasks, at most one per agent, only where another iteration is likely to change the picture: test a promising lemma,
attack a disputed claim, run a requested computation, or check novelty. Set continue_research to false if the
remaining questions are unlikely to move with another round. Never treat an unreviewed claim as established.""" + COMMON_RULES

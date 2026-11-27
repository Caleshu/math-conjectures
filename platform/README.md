# MathResearchLab

A research platform for finding open problems in the mathematical literature, recording them with
traceable provenance, checking whether they are still open, and investigating them with
reproducible computation and (later) a team of AI research agents. It starts with graph theory and
combinatorics.

> **Status: Milestones 1 and 2 are complete. Milestone 5's sandboxed experiment system is partly built.
> Milestones 3, 4 and 6 are not started.** Nothing in the UI simulates work that has not happened:
> features that are not built say so and offer no buttons.

| Milestone | State |
|---|---|
| 1. App, database, paper search/retrieval, manual submission, PDF text extraction | **Done** |
| 2. Candidate detection, source-passage storage, conjecture library, search & filters | **Done** (heuristic detector plus LLM extraction agent, run via Claude Code on your subscription or via an API key) |
| 3. Four verification agents and status classification | Not started. Manual status override with evidence works now, and a citing-works lookup (OpenAlex + Semantic Scholar) is available |
| 4. Six research agents and orchestrator | Not started. DB tables (`research_runs`, `agent_tasks`, `claims`, `proof_attempts`) and the LLM layer exist |
| 5. Computation and validation | **Partly done**: sandboxed Python with NetworkX/SymPy/OR-Tools, full reproducibility records, re-run, library experiments. Adversarial review not started |
| 6. Lean, knowledge graph, collaboration, export | Not started (`relationships` table already models graph edges) |

## Demonstration: inscribed squares in Hamiltonian cycles of Q_n

What the platform did with arXiv:1009.3304 (Sagols & Morales-Luna, 2010), running end to end:

1. **Retrieved** metadata from arXiv and enriched it from OpenAlex. Downloaded the PDF (9 pages of text)
   and the LaTeX source, read in memory and never compiled.
2. **Detected** 6 candidate passages, including the `conjecture` environment (§5, p. 6, label
   `c:squaresConjecture`), the two further conjectures and three open problems in the
   conclusions, and a background mention of Kreweras's (solved) conjecture, which a reviewer should reject.
3. **Recorded** the conjecture through the review UI. The original LaTeX wording is kept verbatim and immutable,
   and the normalized statement and definitions are stored separately. The paper's definition covers
   "straight or twisted" squares, which both reduce to *H contains two opposite edges of a 4-cycle*.
4. **Known results** from the paper are stored with exact passages. Theorem 5.4 (true for n ≤ 7) is flagged
   as computational, because the paper's proof uses a computed value α₌(Q₆)=16.
5. **Experiment** `hypercube_inscribed_squares` ran in the sandbox:
   - Exhaustive enumeration: Q₂, Q₃ and Q₄ have 1, 6 and 1344 Hamiltonian cycles (matches OEIS A066037), and none is
     square-free. The minimum number of inscribed squares is 1, 6 and 12.
   - CP-SAT exact model: **no square-free Hamiltonian cycle exists for n = 2,…,7** (INFEASIBLE). For n ≤ 6
     this is settled in presolve, and n = 7 needs about 112k branches (around 4 s).
   - Validity checks: without the square constraints the same model finds valid Hamiltonian cycles for every
     n, and CP-SAT's minimum square counts equal the enumeration for n ≤ 4.
   - Also computed: every Hamiltonian cycle of Q₅ has ≥ 16 inscribed squares, and CP-SAT proved this optimal
     (takes about 95 s, so it is not in the default parameters).
6. **Conclusion as recorded**: the *statement* of Theorem 5.4 (n ≤ 7) is independently reproduced by a different
   method. The paper's intermediate value α₌(Q₆)=16 was **not** reproduced. This repository's
   [`Conjectures/HypercubeSquares`](../Conjectures/HypercubeSquares/) states it is actually 20.
7. **Disproved at n = 8.** This repository contains a Lean-verified square-free Hamiltonian cycle of Q₈
   (`not_conjecture`), plus cycles for Q₉ and Q₁₀. The platform re-checked all three in its sandbox with a
   fresh checker written from the definition, finding 0 inscribed squares in each (control: a Gray code of Q₈
   has 770). It then set the status to **DISPROVED**, with both pieces of evidence attached. So, among n ≤ 10,
   the conjecture holds exactly for 2 ≤ n ≤ 7.

Re-create the demonstration on an empty database: `cd backend && .venv/bin/python -m scripts.seed_demo`.

## Architecture

```
frontend/  Next.js 16 · React 19 · Tailwind 4 · KaTeX      (talks only to the API; no secrets)
backend/   FastAPI · SQLAlchemy 2 · Alembic                (API + job worker)
  app/sources/     arXiv, OpenAlex, Crossref, Semantic Scholar clients; federated search + dedupe
  app/pdf/         PDF text (pdfminer.six, or GROBID if configured), arXiv LaTeX source reader
  app/extraction/  heuristic candidate detector, LaTeX macro parser, LLM extraction agent
  app/llm/         provider abstraction (Anthropic, OpenAI SDKs), pricing, budget, usage log
  app/jobs/        DB-backed durable job queue + worker (resumable)
  app/sandbox/     restricted subprocess runner for experiments
  app/services/    paper ingestion, conjecture rules (provenance, immutability, status)
  experiments/library/  vetted experiment scripts
supabase/migrations/    SQL export of the Alembic schema for Supabase
```

**Key decisions**

- **Database.** Supabase Postgres via `DATABASE_URL`, with a SQLite fallback so the app runs with no external
  services. Alembic is the source of truth, and the same migration runs on both. JSON columns become `JSONB` on Postgres.
- **Job queue in the database** rather than Celery/Redis. Jobs are few and long-running. Enqueueing is
  transactional with the data it refers to. Claiming is an optimistic `UPDATE … WHERE status='queued'`, safe with
  several workers. Workers heartbeat, and a job whose worker dies is re-queued automatically. Paper processing
  stages are idempotent, so a resumed job continues where it stopped.
- **Sandbox.** Experiments never run in the API/worker interpreter. Each runs as a separate `python -I -B`
  process in its own directory with an empty environment (no API keys or DB URL), plus rlimits (CPU, file size,
  open files, address space where enforced) and a wall-clock timeout that kills the process group. OS isolation
  uses `sandbox-exec` on macOS (no network, writes confined to the work dir) or `bubblewrap` on Linux. The isolation
  level actually applied is stored with every experiment. **For multi-user deployment, run workers inside a
  container/VM as well** (gVisor, Firecracker). Memory limits are not enforced by macOS, and the UI says so.
- **Provenance rules enforced server-side.** `original_statement`, source paper, passage and creator are
  immutable after creation. Every edit, status change, override and experiment is a `conjecture_events` row with
  actor and evidence. `VERIFIED_OPEN` cannot be set by an agent without evidence. A manual override requires an explanation.
- **Candidates are not conjectures.** The heuristic detector is deliberately high-recall, and its output waits for
  review. The LLM agent's output is also a candidate, with its rationale stored, and each quoted "original wording"
  is checked verbatim against the source text, with the result displayed.
- **LaTeX first.** For arXiv papers the LaTeX source gives the exact statement, and the paper's own macros (`\hyp{n}`)
  are parsed so KaTeX renders the original wording faithfully. LaTeX hits are mapped back to PDF page numbers.
- **LLM layer.** Uses the official SDKs. Defaults to `claude-opus-5-5` with adaptive thinking, structured JSON output and
  server-side refusal fallback. Every call is priced and logged to `llm_usage`, and calls are refused once
  `LLM_BUDGET_USD` is spent.

## Setup

Requirements: Python 3.12+ (3.13 recommended; OR-Tools wheels), Node 20+, and optionally a Supabase project.

```bash
# backend
cd backend
uv venv -p 3.13 .venv && uv pip install -e ".[dev]"      # or: python -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp ../.env.example ../.env                                # fill in what you have; all optional
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --port 8000                # API + embedded worker; docs at http://localhost:8000/docs

# frontend (new terminal)
cd frontend
cp .env.example .env.local
npm install && npm run dev                                # http://localhost:3000

# optional: demo data through the real pipeline (network access required)
cd backend && .venv/bin/python -m scripts.seed_demo
```

**Supabase.** Set `DATABASE_URL` to the project's Postgres connection string and run `alembic upgrade head`
(or apply `supabase/migrations/*.sql`, which also enables RLS with no policies so the auto-generated REST
API cannot read the tables). For auth, set `SUPABASE_URL` and `REQUIRE_AUTH=true` on the backend, and
`NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` on the frontend. Users then sign in on the Settings
page, and the backend verifies tokens via the project's JWKS (or `SUPABASE_JWT_SECRET` for HS256 projects).

**Separate worker.** Set `RUN_EMBEDDED_WORKER=false` and run `.venv/bin/python -m app.jobs.worker` (one or more).

## Workflows

1. **Discover → Search literature.** Federated search over arXiv (subject → categories, e.g. graph theory →
   `math.CO`), OpenAlex, Crossref and Semantic Scholar, by keywords, subject and date range. Results are merged and
   de-duplicated by DOI, arXiv ID and normalized title, and already-indexed papers are marked. Select results to index
   and process them.
2. **Discover → Submit a paper.** arXiv ID or URL, DOI or doi.org URL, OpenAlex ID, or a direct PDF URL. Progress is shown live.
3. **Discover → Review candidates.** Reject (with a reason) or *Record as conjecture*.
4. **Paper page.** Metadata, stored PDF, page-by-page extracted text, LaTeX source, candidates, re-process, and
   *Run AI extraction* (enabled when a provider key is set).
5. **Conjecture page.** Overview, Original Sources, Related Literature (relationships and a citing-works lookup),
   Known Results (each with a citation, and computational ones marked reproduced or not), Research Agents and Proof
   Attempts (not built yet, shown as such), Computational Experiments, and Research History.
6. **Experiments.** Library scripts or custom code. Each one stores code plus SHA-256, parameters, package versions,
   solver settings, isolation, limits, stdout/stderr, result.json and interpretation. *Reproduce* re-runs identical code in a fresh sandbox.

## Tests

```bash
cd backend
.venv/bin/python -m pytest -m "not network"   # 24 offline tests: identifiers, dedupe, detector, API rules,
                                              # job claiming/resume, sandbox limits & isolation, experiment correctness
.venv/bin/python -m pytest -m network         # live arXiv / OpenAlex checks
cd ../frontend && npm run typecheck && npm run build
```

## Known limitations

- PDF text from pdfminer loses math layout. LaTeX is used when available, and GROBID adds section structure if configured.
- Semantic Scholar without a key is often rate-limited (HTTP 429). This is reported per source, never hidden.
- OpenAlex/Semantic Scholar citation coverage for mathematics is incomplete.
- AI calls run through the Claude Code CLI on the user's Claude subscription by default (`claude -p`, no tools, no MCP,
  empty working directory, API keys stripped from its environment). These calls are recorded at $0 billed and count
  against the plan's usage limits. Set `ANTHROPIC_API_KEY` to use pay-per-use API billing instead. The Anthropic-SDK and
  OpenAI providers have not been run live here.
- Verified live: AI extraction on arXiv:1009.3304 found Conjecture 5.1 and 6 further problems, quoted the original
  wording verbatim (all verified against the source), and rejected the Kreweras background passage.
- Memory limits for experiments are not enforced on macOS.
- Export of research reports (Markdown/PDF) comes with the research runs (Milestone 4).

API reference: [`docs/API.md`](docs/API.md), plus interactive OpenAPI at `/docs`.

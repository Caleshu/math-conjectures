# MathResearchLab API

Base URL `http://localhost:8000`. Interactive OpenAPI documentation: `/docs` (schema at `/openapi.json`).
When `REQUIRE_AUTH=true`, send `Authorization: Bearer <Supabase access token>`. Errors are JSON
`{"detail": "..."}`; upstream literature-API failures return `502` with `source`.

## System
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | DB connectivity check |
| GET | `/api/dashboard` | counts, status breakdown, recent conjectures, activity, recent jobs |
| GET | `/api/settings` | integration availability (honest), LLM/sandbox/auth configuration |
| GET | `/api/usage` | LLM spend by model/purpose vs budget; literature API request/error counts |
| GET | `/api/jobs?status=&subject_id=` | job list |
| GET | `/api/jobs/{id}` | job status, `progress.stage`, result, error |
| POST | `/api/jobs/{id}/cancel` · `/retry` | cancel a queued job / retry a failed one |

## Discovery & papers
| Method | Path | Body / query | Purpose |
|---|---|---|---|
| POST | `/api/discovery/search` | `{text, subject, from_date, to_date, sources[], limit}` | federated, de-duplicated search; marks `indexed_paper_id`; per-source `source_errors` |
| POST | `/api/discovery/import` | `{records[], process}` | index search results; queue `process_paper` jobs |
| POST | `/api/papers/submit` | `{identifier}` | arXiv ID/URL, DOI/doi.org, OpenAlex `W…`, or PDF URL → `ingest_identifier` job |
| GET | `/api/papers?q=&status=` | | list with candidate counts |
| GET | `/api/papers/{id}` | | detail, candidates, jobs, `latex_macros`, `llm_available` |
| GET | `/api/papers/{id}/pages/{n}` | | extracted text of PDF page n |
| GET | `/api/papers/{id}/pdf` · `/latex` | | stored PDF / flattened LaTeX source |
| GET | `/api/papers/{id}/citing` | | citing works (OpenAlex + Semantic Scholar) with errors and a coverage caveat |
| POST | `/api/papers/{id}/process` | | re-run download / extraction / scan (idempotent) |
| POST | `/api/papers/{id}/extract` | `{provider?}` | LLM extraction job; `409` if no provider configured |

## Candidates
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/candidates?review_status=pending&paper_id=&kind=&min_score=` | review queue |
| GET | `/api/candidates/{id}` | detail incl. context and paper macros |
| POST | `/api/candidates/{id}/reject` | `{note}` |
| POST | `/api/candidates/{id}/accept` | conjecture body (below) → creates conjecture linked to the passage |

## Conjectures
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/conjectures/meta` | fields, statuses, difficulties, relation types |
| GET | `/api/conjectures?q=&field=&status=&difficulty=&from_date=&to_date=&activity=&sort=` | library (multi-valued filters repeat the key) |
| GET | `/api/conjectures/{id or slug}` | full record: source paper, events, experiments, claims, proof attempts, runs, relationships, sibling problems |
| POST | `/api/conjectures` | manual creation |
| PATCH | `/api/conjectures/{id}` | `{changes, note}`; provenance fields rejected with `422`; edit logged |
| POST | `/api/conjectures/{id}/status` | manual override `{status, rationale (≥10 chars), evidence[], confidence}` |
| POST | `/api/conjectures/{id}/notes` | `{text}` |
| POST | `/api/conjectures/{id}/relationships` | `{relation_type, to_conjecture_id | to_external, note}` |

Conjecture body: `{title, field, original_statement, normalized_statement, definitions[{term,definition}],
subfields[], problem_type, notation, known_results[], potential_approaches[], relevant_theorems[],
difficulty_estimate, difficulty_rationale}`. Known result: `{statement, citation, source_paper_id,
location, evidence_passage, is_computational, reproduced, reproduction_experiment_id, note}`.

## Experiments
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/experiments/library` · `/library/{key}/code` | vetted scripts with defaults |
| POST | `/api/experiments` | `{title, problem, conjecture_id?, library_script | code, parameters, timeout_s, memory_mb, result_kind}` → sandboxed run |
| GET | `/api/experiments?conjecture_id=&status=` · `/{id}` | list / full record (code, logs, environment, result) |
| POST | `/api/experiments/{id}/interpretation` | `{interpretation}` |
| POST | `/api/experiments/{id}/rerun` | reproduce with identical stored code & parameters |

Experiment script contract: read parameters from `$MRL_PARAMS` (`params.json`), write a JSON object to
`result.json` in the working directory. No network; writes confined to the working directory.

## Research Lab
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/research/meta` | agents, default limits and bounds, available providers |
| GET | `/api/research/runs?conjecture_id=` | runs with usage (model calls, tokens, experiments) |
| POST | `/api/research/runs` | `{conjecture_id (id or slug), limits{max_iterations, max_model_calls, max_tokens, max_runtime_s, max_experiments, experiment_timeout_s, experiment_memory_mb, concurrency, provider, effort}}` → queued run; `409` without a provider or if a run is already active |
| GET | `/api/research/runs/{id}` | run, agent tasks (status, current task, full output), claims, proof attempts, experiments |
| POST | `/api/research/runs/{id}/cancel` · `/resume` | stop at the next checkpoint / resume a failed or cancelled run from its checkpoints |
| GET | `/api/research/runs/{id}/report` · `/report.md` | structured report (JSON) / Markdown download |

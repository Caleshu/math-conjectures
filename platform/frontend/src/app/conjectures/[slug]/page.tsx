"use client";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CandidateCard } from "@/components/CandidateReview";
import { MathText } from "@/components/Math";
import { A, Badge, Button, Card, Empty, ErrorBox, KV, Label, Loading, Notice, PageHeader, StatusBadge, Tabs, fieldLabel, fmtDate, inputCls } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Conjecture, Experiment, KnownResult, Meta, SearchResult } from "@/lib/types";

type TabKey = "overview" | "sources" | "literature" | "known" | "agents" | "proofs" | "experiments" | "history";

export default function Page() {
  return <Suspense fallback={<Loading />}><Detail /></Suspense>;
}

function Detail() {
  const { slug } = useParams<{ slug: string }>();
  const sp = useSearchParams();
  const router = useRouter();
  const tab = (sp.get("tab") as TabKey) || "overview";
  const { data: c, error, loading, reload } = useApi<Conjecture>(`/api/conjectures/${slug}`, {
    pollMs: 3000, shouldPoll: (d) => (d.experiments ?? []).some((e) => e.status === "queued" || e.status === "running"),
  });
  if (loading && !c) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  if (!c) return null;
  const macros = c.source_paper?.latex_macros;
  const setTab = (k: TabKey) => router.replace(`/conjectures/${slug}?tab=${k}`, { scroll: false });

  return (
    <>
      <PageHeader eyebrow={<span>{fieldLabel(c.field)} · {c.problem_type.replace(/_/g, " ")}</span>} title={c.title}
        subtitle={c.source_paper && <span>Source: {c.source_paper.authors?.join(", ")}, <em><MathText text={c.source_paper.title} /></em> ({c.source_paper.published_date?.slice(0, 4)}){c.source_page ? `, p. ${c.source_page}` : ""}</span>}
        actions={<StatusBadge status={c.status} />} />
      <Tabs<TabKey> value={tab} onChange={setTab} tabs={[
        { key: "overview", label: "Overview" }, { key: "sources", label: "Original Sources" },
        { key: "literature", label: "Related Literature", count: c.relationships?.length },
        { key: "known", label: "Known Results", count: c.known_results.length },
        { key: "agents", label: "Research Agents", count: c.research_runs?.length },
        { key: "proofs", label: "Proof Attempts", count: c.proof_attempts?.length },
        { key: "experiments", label: "Computational Experiments", count: c.experiments?.length },
        { key: "history", label: "Research History", count: c.events?.length },
      ]} />
      {tab === "overview" && <Overview c={c} macros={macros} reload={reload} />}
      {tab === "sources" && <Sources c={c} macros={macros} reload={reload} />}
      {tab === "literature" && <Literature c={c} reload={reload} />}
      {tab === "known" && <Known c={c} macros={macros} reload={reload} />}
      {tab === "agents" && <Agents c={c} />}
      {tab === "proofs" && <Proofs c={c} />}
      {tab === "experiments" && <Experiments c={c} reload={reload} />}
      {tab === "history" && <History c={c} />}
    </>
  );
}

// ------------------------------------------------------------------------------------------
function Overview({ c, macros, reload }: { c: Conjecture; macros?: Record<string, string>; reload: () => void }) {
  const [showRaw, setShowRaw] = useState(false);
  const [editing, setEditing] = useState(false);
  const lastStatus = [...(c.events ?? [])].reverse().find((e) => e.new_status);
  return (
    <div className="grid grid-cols-[1fr_320px] gap-6">
      <div className="space-y-5">
        <Card title="Statement" actions={<Button size="sm" variant="ghost" onClick={() => setEditing(!editing)}>{editing ? "Close editor" : "Edit normalized statement"}</Button>}>
          {editing ? <EditStatement c={c} macros={macros} onDone={() => { setEditing(false); reload(); }} /> : (
            <div className="statement"><MathText text={c.normalized_statement} macros={macros} /></div>
          )}
          <div className="mt-4">
            <div className="mb-1.5 flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-ink-3">Original wording (verbatim from source)</span>
              <button className="text-xs text-ink-3 hover:text-ink" onClick={() => setShowRaw(!showRaw)}>{showRaw ? "Rendered" : "Raw LaTeX"}</button>
            </div>
            {showRaw ? <pre className="whitespace-pre-wrap rounded-[5px] bg-paper p-3 font-mono text-[11.5px] text-ink-2">{c.original_statement}</pre>
              : <div className="rounded-[5px] bg-paper px-3 py-2.5 font-serif text-[15px] leading-relaxed text-ink-2"><MathText text={c.original_statement} macros={macros} /></div>}
          </div>
        </Card>
        <Card title="Definitions and notation">
          {c.definitions.length === 0 && !c.notation ? <p className="text-sm text-ink-3">No definitions recorded. Add them via “Edit normalized statement”.</p> : (
            <dl className="space-y-2.5">
              {c.definitions.map((d, i) => (
                <div key={i} className="text-[14px] leading-relaxed"><dt className="inline font-semibold text-ink"><MathText text={d.term} macros={macros} />. </dt>
                  <dd className="inline text-ink-2"><MathText text={d.definition} macros={macros} /></dd></div>
              ))}
              {c.notation && <div className="text-[13px] text-ink-2"><MathText text={c.notation} macros={macros} /></div>}
            </dl>
          )}
        </Card>
        <Card title="Potential approaches">
          {c.potential_approaches.length === 0 ? <p className="text-sm text-ink-3">None recorded. Strategy generation is part of the research agents (Milestone 4).</p> : (
            <ul className="list-disc space-y-1 pl-5 text-[14px] text-ink-2">{c.potential_approaches.map((a, i) => <li key={i}><MathText text={a} macros={macros} /></li>)}</ul>
          )}
        </Card>
      </div>
      <div className="space-y-5">
        <Card title="Open-problem status">
          <div className="flex items-center gap-2"><StatusBadge status={c.status} />{c.status_is_manual_override && <Badge>manual override</Badge>}</div>
          <dl className="mt-3">
            <KV k="Confidence">{c.verification_confidence != null ? `${(c.verification_confidence * 100).toFixed(0)}%` : "not assessed"}</KV>
            <KV k="Last change">{lastStatus ? <>{fmtDate(lastStatus.created_at)} by {lastStatus.actor}</> : "—"}</KV>
          </dl>
          {lastStatus && <p className="mt-2 text-xs leading-relaxed text-ink-2">{lastStatus.summary}</p>}
          {c.status === "UNVERIFIED" && <div className="mt-3"><Notice tone="warn">A problem stated as open in the source is not assumed to be open today. The automated verification agents (Milestone 3) are not built yet; you can record your own assessment below, with evidence.</Notice></div>}
          <StatusOverride c={c} onDone={reload} />
        </Card>
        <Card title="Record">
          <dl>
            <KV k="Field">{fieldLabel(c.field)}{c.subfields.length > 0 && <span className="text-ink-3"> · {c.subfields.join(", ")}</span>}</KV>
            <KV k="Difficulty">{c.difficulty_estimate ? fieldLabel(c.difficulty_estimate) : "not estimated"}</KV>
            <KV k="Recorded">{fmtDate(c.created_at)} by {c.created_by}</KV>
            <KV k="Extracted by">{c.extraction_details?.extracted_by ?? "manual entry"}</KV>
            <KV k="Experiments">{c.experiments?.length ?? 0}</KV>
          </dl>
        </Card>
      </div>
    </div>
  );
}

function EditStatement({ c, macros, onDone }: { c: Conjecture; macros?: Record<string, string>; onDone: () => void }) {
  const [text, setText] = useState(c.normalized_statement);
  const [defs, setDefs] = useState(c.definitions);
  const [note, setNote] = useState("");
  const [err, setErr] = useState<unknown>(null);
  async function save() {
    try {
      await api.patch(`/api/conjectures/${c.id}`, { changes: { normalized_statement: text, definitions: defs.filter((d) => d.term.trim()) }, note: note || null });
      onDone();
    } catch (e) { setErr(e); }
  }
  return (
    <div className="space-y-3">
      <Notice>The original wording cannot be edited. Edits to the normalized statement are logged in the research history.</Notice>
      <div className="grid grid-cols-2 gap-3">
        <textarea className={`${inputCls} font-mono`} rows={6} value={text} onChange={(e) => setText(e.target.value)} />
        <div className="statement"><MathText text={text} macros={macros} /></div>
      </div>
      <Label>Definitions</Label>
      {defs.map((d, i) => (
        <div key={i} className="grid grid-cols-[180px_1fr_auto] gap-2">
          <input className={inputCls} value={d.term} onChange={(e) => setDefs(defs.map((x, j) => j === i ? { ...x, term: e.target.value } : x))} />
          <input className={inputCls} value={d.definition} onChange={(e) => setDefs(defs.map((x, j) => j === i ? { ...x, definition: e.target.value } : x))} />
          <Button size="sm" variant="ghost" onClick={() => setDefs(defs.filter((_, j) => j !== i))}>Remove</Button>
        </div>
      ))}
      <Button size="sm" onClick={() => setDefs([...defs, { term: "", definition: "" }])}>Add definition</Button>
      <input className={inputCls} placeholder="Reason for the edit (recorded in history)" value={note} onChange={(e) => setNote(e.target.value)} />
      <ErrorBox error={err} />
      <div className="flex justify-end"><Button variant="primary" onClick={save}>Save changes</Button></div>
    </div>
  );
}

function StatusOverride({ c, onDone }: { c: Conjecture; onDone: () => void }) {
  const { data: meta } = useApi<Meta>("/api/conjectures/meta");
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState(c.status);
  const [rationale, setRationale] = useState("");
  const [evidence, setEvidence] = useState("");
  const [conf, setConf] = useState("");
  const [err, setErr] = useState<unknown>(null);
  async function save() {
    try {
      await api.post(`/api/conjectures/${c.id}/status`, {
        status, rationale, confidence: conf ? Number(conf) / 100 : null,
        evidence: evidence.split("\n").map((s) => s.trim()).filter(Boolean).map((d) => ({ description: d })),
      });
      setOpen(false); setRationale(""); setEvidence(""); onDone();
    } catch (e) { setErr(e); }
  }
  if (!open) return <div className="mt-3"><Button size="sm" onClick={() => setOpen(true)}>Set status manually…</Button></div>;
  return (
    <div className="mt-3 space-y-2.5 border-t border-rule pt-3">
      <select className={inputCls} value={status} onChange={(e) => setStatus(e.target.value)}>
        {(meta?.statuses ?? []).map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
      </select>
      <textarea className={inputCls} rows={3} placeholder="Explanation (required)" value={rationale} onChange={(e) => setRationale(e.target.value)} />
      <textarea className={inputCls} rows={3} placeholder="Evidence, one item per line (citations, links, experiment IDs)" value={evidence} onChange={(e) => setEvidence(e.target.value)} />
      <input className={inputCls} type="number" min={0} max={100} placeholder="Confidence % (optional)" value={conf} onChange={(e) => setConf(e.target.value)} />
      <ErrorBox error={err} />
      <div className="flex justify-end gap-2"><Button size="sm" variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
        <Button size="sm" variant="primary" disabled={rationale.trim().length < 10} onClick={save}>Record override</Button></div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------
function Sources({ c, macros, reload }: { c: Conjecture; macros?: Record<string, string>; reload: () => void }) {
  const p = c.source_paper;
  if (!p) return <Empty title="No source paper linked">This conjecture was entered manually without a source.</Empty>;
  return (
    <div className="space-y-5">
      <Card title="Source paper">
        <div className="font-serif text-lg"><A href={`/papers/${p.id}`}><MathText text={p.title} /></A></div>
        <div className="mt-1 text-sm text-ink-2">{p.authors?.join(", ")}</div>
        <dl className="mt-3 grid grid-cols-2 gap-x-8">
          <KV k="Published">{p.published_date ?? "—"}</KV>
          <KV k="Venue">{p.venue ?? "—"}</KV>
          <KV k="arXiv">{p.arxiv_id ? <A href={`https://arxiv.org/abs/${p.arxiv_id}`}>{p.arxiv_id}</A> : "—"}</KV>
          <KV k="DOI">{p.doi ? <A href={`https://doi.org/${p.doi}`}>{p.doi}</A> : "—"}</KV>
          <KV k="Location">{[c.source_section && `§ ${c.source_section}`, c.source_page && `page ${c.source_page}`].filter(Boolean).join(", ") || "—"}</KV>
          <KV k="Text">{p.page_count ? `${p.page_count} pages (${p.text_extractor})` : "not extracted"}{p.has_latex ? " · LaTeX source" : ""}</KV>
        </dl>
        <div className="mt-3 flex gap-3 text-[13px]">
          {c.source_page && <A href={`/papers/${p.id}?page=${c.source_page}`}>Read page {c.source_page} →</A>}
          {p.pdf_path && <A href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/papers/${p.id}/pdf`}>PDF</A>}
        </div>
      </Card>
      <Card title="Exact source passage">
        <pre className="whitespace-pre-wrap rounded-[5px] bg-paper p-3 font-mono text-[11.5px] leading-relaxed text-ink-2">{c.source_passage ?? c.original_statement}</pre>
        <div className="mt-3 font-serif text-[15px] leading-relaxed"><MathText text={c.source_passage ?? c.original_statement} macros={macros} /></div>
      </Card>
      {(c.source_candidates?.length ?? 0) > 0 && (
        <Card title="Other unreviewed passages in this paper">
          <div className="space-y-3">{c.source_candidates!.map((x) => <CandidateCard key={x.id} c={x} onChanged={reload} showPaper={false} macros={macros} />)}</div>
        </Card>
      )}
    </div>
  );
}

// ------------------------------------------------------------------------------------------
function Literature({ c, reload }: { c: Conjecture; reload: () => void }) {
  const [citing, setCiting] = useState<{ results: (SearchResult & { via?: string })[]; errors: string[]; note: string; openalex_ids_checked: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  async function loadCiting() {
    if (!c.source_paper) return;
    setBusy(true); setErr(null);
    try { setCiting(await api.get(`/api/papers/${c.source_paper.id}/citing`)); } catch (e) { setErr(e); } finally { setBusy(false); }
  }
  return (
    <div className="space-y-5">
      <Card title="Relationships" pad={false}>
        {(c.relationships ?? []).length === 0 ? <p className="p-4 text-sm text-ink-3">No relationships recorded.</p> : (
          <ul className="divide-y divide-rule">{c.relationships!.map((r) => (
            <li key={r.id} className="px-4 py-2.5 text-[13px]">
              <Badge>{r.relation_type.replace(/_/g, " ")}</Badge>{" "}
              {r.to_id ? <A href={`/conjectures/${r.to_id}`}>{r.to_title ?? r.to_id}</A> : <span className="text-ink">{r.to_external}</span>}
              {r.note && <span className="text-ink-2"> — {r.note}</span>}
              <span className="ml-2 text-xs text-ink-3">{r.created_by} · {r.verification_status}</span>
            </li>))}</ul>
        )}
        <div className="border-t border-rule p-4"><AddRelation c={c} onDone={reload} /></div>
      </Card>
      {(c.siblings?.length ?? 0) > 0 && (
        <Card title="Other problems from the same paper">
          <ul className="space-y-1.5 text-[13px]">{c.siblings!.map((s) => <li key={s.id} className="flex items-center gap-2"><StatusBadge status={s.status} /><A href={`/conjectures/${s.slug}`}>{s.title}</A></li>)}</ul>
        </Card>
      )}
      <Card title="Works citing the source paper" actions={c.source_paper && <Button size="sm" onClick={loadCiting} disabled={busy}>{busy ? "Querying…" : citing ? "Refresh" : "Query citation graph"}</Button>}>
        {!c.source_paper ? <p className="text-sm text-ink-3">No source paper.</p> : !citing ? (
          <p className="text-sm text-ink-2">Looks up citing works in OpenAlex and Semantic Scholar. Systematic citation-chain analysis by the Citation Researcher agent is Milestone 3.</p>
        ) : (
          <div className="space-y-3">
            <Notice tone="warn">{citing.note}</Notice>
            {citing.errors.map((e, i) => <ErrorBox key={i} error={e} />)}
            {citing.results.length === 0 ? <p className="text-sm text-ink-2">No citing works found (checked OpenAlex {citing.openalex_ids_checked.join(", ") || "—"} and Semantic Scholar).</p> : (
              <ul className="divide-y divide-rule">{citing.results.map((r, i) => (
                <li key={i} className="py-2 text-[13px]">
                  <div className="text-ink"><MathText text={r.title} /></div>
                  <div className="text-xs text-ink-3">{r.authors.slice(0, 4).join(", ")} · {r.published_date} · via {r.via}
                    {r.doi && <> · <A href={`https://doi.org/${r.doi}`}>doi</A></>}{r.indexed_paper_id && <> · <A href={`/papers/${r.indexed_paper_id}`}>indexed</A></>}</div>
                </li>))}</ul>
            )}
          </div>
        )}
        <ErrorBox error={err} />
      </Card>
    </div>
  );
}

function AddRelation({ c, onDone }: { c: Conjecture; onDone: () => void }) {
  const { data: meta } = useApi<Meta>("/api/conjectures/meta");
  const { data: all } = useApi<{ items: Conjecture[] }>("/api/conjectures");
  const [type, setType] = useState("related_to");
  const [target, setTarget] = useState("");
  const [external, setExternal] = useState("");
  const [note, setNote] = useState("");
  const [err, setErr] = useState<unknown>(null);
  async function save() {
    try {
      await api.post(`/api/conjectures/${c.id}/relationships`, { relation_type: type, to_conjecture_id: target || null, to_external: target ? null : external, note: note || null });
      setExternal(""); setNote(""); setTarget(""); onDone();
    } catch (e) { setErr(e); }
  }
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-[160px_1fr_1fr_auto] gap-2">
        <select className={inputCls} value={type} onChange={(e) => setType(e.target.value)}>{(meta?.relation_types ?? []).map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}</select>
        <select className={inputCls} value={target} onChange={(e) => setTarget(e.target.value)}>
          <option value="">External theorem / result…</option>
          {(all?.items ?? []).filter((x) => x.id !== c.id).map((x) => <option key={x.id} value={x.id}>{x.title}</option>)}
        </select>
        <input className={inputCls} disabled={Boolean(target)} placeholder="e.g. Erdős's conjecture on C4-free subgraphs of Q_n" value={external} onChange={(e) => setExternal(e.target.value)} />
        <Button size="sm" disabled={!target && !external.trim()} onClick={save}>Add</Button>
      </div>
      <input className={inputCls} placeholder="Note / source (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
      <ErrorBox error={err} />
    </div>
  );
}

// ------------------------------------------------------------------------------------------
function Known({ c, macros, reload }: { c: Conjecture; macros?: Record<string, string>; reload: () => void }) {
  const [adding, setAdding] = useState(false);
  const [kr, setKr] = useState<KnownResult>({ statement: "", citation: "", location: "", evidence_passage: "", is_computational: false, reproduced: null });
  const [err, setErr] = useState<unknown>(null);
  async function save(list: KnownResult[], note: string) {
    try { await api.patch(`/api/conjectures/${c.id}`, { changes: { known_results: list }, note }); setAdding(false); reload(); } catch (e) { setErr(e); }
  }
  return (
    <div className="space-y-4">
      <Notice>Every known result must cite where it is stated. Computational claims are shown as <strong>not reproduced</strong> until an experiment in this system reproduces them.</Notice>
      {c.known_results.length === 0 && <Empty title="No known results recorded" />}
      {c.known_results.map((k, i) => (
        <Card key={i}>
          <div className="flex items-start justify-between gap-4">
            <div className="font-serif text-[15px] leading-relaxed text-ink"><MathText text={k.statement} macros={macros} /></div>
            <div className="flex shrink-0 gap-1.5">
              {k.is_computational && <Badge>computational</Badge>}
              {k.is_computational && (k.reproduced ? <Badge tone="succeeded">reproduced</Badge> : <Badge tone="pending">not reproduced</Badge>)}
            </div>
          </div>
          <div className="mt-2 text-xs text-ink-2">Source: {k.citation || "—"}{k.location && ` — ${k.location}`}{k.source_paper_id && <> · <A href={`/papers/${k.source_paper_id}`}>paper</A></>}</div>
          {k.evidence_passage && <pre className="mt-2 whitespace-pre-wrap rounded-[5px] bg-paper p-2 font-mono text-[11px] text-ink-2">{k.evidence_passage}</pre>}
          {k.note && <div className="mt-2 text-xs text-ink-2">{k.note}</div>}
          {k.reproduction_experiment_id && <div className="mt-1 text-xs"><A href={`/experiments/${k.reproduction_experiment_id}`}>Reproduction experiment →</A></div>}
          {k.is_computational && !k.reproduced && (c.experiments ?? []).some((e) => e.status === "succeeded") && (
            <div className="mt-2"><select className={`${inputCls} w-auto`} defaultValue="" onChange={(e) => e.target.value && save(c.known_results.map((x, j) => j === i ? { ...x, reproduced: true, reproduction_experiment_id: e.target.value } : x), `Marked known result ${i + 1} as reproduced by experiment ${e.target.value}`)}>
              <option value="">Mark as reproduced by experiment…</option>
              {(c.experiments ?? []).filter((e) => e.status === "succeeded").map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
            </select></div>
          )}
        </Card>
      ))}
      {adding ? (
        <Card title="Add a known result">
          <div className="space-y-2.5">
            <textarea className={inputCls} rows={2} placeholder="Statement (LaTeX allowed)" value={kr.statement} onChange={(e) => setKr({ ...kr, statement: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className={inputCls} placeholder="Citation (required) e.g. Sagols & Morales-Luna 2010, Thm 5.4" value={kr.citation} onChange={(e) => setKr({ ...kr, citation: e.target.value })} />
              <input className={inputCls} placeholder="Location (section/page)" value={kr.location} onChange={(e) => setKr({ ...kr, location: e.target.value })} />
            </div>
            <textarea className={`${inputCls} font-mono`} rows={2} placeholder="Exact supporting passage (optional)" value={kr.evidence_passage} onChange={(e) => setKr({ ...kr, evidence_passage: e.target.value })} />
            <label className="flex items-center gap-2 text-[13px] text-ink-2"><input type="checkbox" checked={kr.is_computational} onChange={(e) => setKr({ ...kr, is_computational: e.target.checked })} /> Relies on computation</label>
            <ErrorBox error={err} />
            <div className="flex justify-end gap-2"><Button variant="ghost" onClick={() => setAdding(false)}>Cancel</Button>
              <Button variant="primary" disabled={!kr.statement.trim() || !kr.citation?.trim()} onClick={() => save([...c.known_results, kr], "Added known result")}>Add</Button></div>
          </div>
        </Card>
      ) : <Button onClick={() => setAdding(true)}>Add known result</Button>}
    </div>
  );
}

function Agents({ c }: { c: Conjecture }) {
  return (
    <div className="space-y-4">
      <Notice>The multi-agent research team (Strategist, Extremal Mathematician, Counterexample Agent, Computational Mathematician, Literature Specialist, Adversarial Reviewer) is Milestone 4 and has not been built. No agent outputs are shown because none have been produced. The database tables for research runs and agent tasks exist.</Notice>
      {(c.research_runs ?? []).length === 0 ? <Empty title="No research runs" /> : (
        <ul>{c.research_runs!.map((r) => <li key={r.id}>{r.status} — {fmtDate(r.created_at)}</li>)}</ul>
      )}
      <p className="text-[13px] text-ink-2">Computational investigation is available now under <Link className="text-accent" href={`/conjectures/${c.slug}?tab=experiments`}>Computational Experiments</Link>.</p>
    </div>
  );
}

function Proofs({ c }: { c: Conjecture }) {
  return (c.proof_attempts ?? []).length === 0
    ? <Empty title="No proof attempts">Proof attempts are produced by the research agents (Milestone 4) and reviewed by the adversarial reviewer. Validation levels range from idea to formally verified; nothing is labelled formally verified unless Lean accepts it.</Empty>
    : <ul>{c.proof_attempts!.map((p) => <li key={p.id}>{p.strategy}</li>)}</ul>;
}

// ------------------------------------------------------------------------------------------
type LibItem = { key: string; title: string; problem: string; default_parameters: Record<string, unknown>; default_timeout_s: number; applies_to_tags: string[] };

function Experiments({ c, reload }: { c: Conjecture; reload: () => void }) {
  const { data: lib } = useApi<{ items: LibItem[] }>("/api/experiments/library");
  const [err, setErr] = useState<unknown>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const text = `${c.title} ${c.normalized_statement}`.toLowerCase();
  const relevant = (lib?.items ?? []).filter((l) => l.applies_to_tags.every((t) => text.includes(t)));
  async function launch(l: LibItem) {
    setErr(null);
    try {
      const p = params[l.key] ? JSON.parse(params[l.key]) : l.default_parameters;
      await api.post("/api/experiments", { conjecture_id: c.id, library_script: l.key, title: l.title, problem: l.problem, parameters: p, timeout_s: l.default_timeout_s });
      reload();
    } catch (e) { setErr(e instanceof SyntaxError ? new Error(`Parameters are not valid JSON: ${e.message}`) : e); }
  }
  return (
    <div className="space-y-5">
      {relevant.map((l) => (
        <Card key={l.key} title={`Library experiment: ${l.title}`}>
          <p className="text-[13px] text-ink-2">{l.problem}</p>
          <Label hint="JSON">Parameters</Label>
          <textarea className={`${inputCls} font-mono`} rows={3} defaultValue={JSON.stringify(l.default_parameters)} onChange={(e) => setParams({ ...params, [l.key]: e.target.value })} />
          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs text-ink-3">Runs in the restricted sandbox; code, parameters, versions and logs are stored.</span>
            <Button variant="primary" onClick={() => launch(l)}>Run experiment</Button>
          </div>
        </Card>
      ))}
      <div className="text-[13px] text-ink-2">Custom code can be submitted from <A href={`/experiments?new=1&conjecture=${c.id}`}>Experiments → New experiment</A>.</div>
      <ErrorBox error={err} />
      {(c.experiments ?? []).length === 0 ? <Empty title="No experiments yet" /> : (
        <div className="divide-y divide-rule rounded-md border border-rule bg-surface">
          {c.experiments!.map((e: Experiment) => (
            <Link key={e.id} href={`/experiments/${e.id}`} className="grid grid-cols-[1fr_auto] gap-4 px-4 py-3 hover:bg-paper">
              <div>
                <div className="text-[14px] text-ink">{e.title}</div>
                <div className="mt-0.5 text-xs text-ink-3">{fmtDate(e.created_at, true)} · {e.result_kind.replace(/_/g, " ")} · {e.runtime_seconds != null ? `${e.runtime_seconds.toFixed(1)} s` : "—"} · sha256 {e.code_sha256.slice(0, 10)}</div>
                {e.result?.summary && <div className="mt-1 text-xs text-ink-2">n settled (no counterexample): {JSON.stringify(e.result.summary.n_settled_no_counterexample)} · counterexample found: {String(e.result.summary.counterexample_found)}</div>}
              </div>
              <StatusBadge status={e.status} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function History({ c }: { c: Conjecture }) {
  return (
    <ol className="relative space-y-4 border-l border-rule pl-5">
      {[...(c.events ?? [])].reverse().map((e) => (
        <li key={e.id}>
          <span className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full border-2 border-surface bg-ink-3" />
          <div className="flex flex-wrap items-center gap-2 text-xs text-ink-3"><span className="tabular">{fmtDate(e.created_at, true)}</span><Badge>{e.event_type.replace(/_/g, " ")}</Badge><span>{e.actor}</span>
            {e.new_status && <span>{e.previous_status ? `${e.previous_status} → ` : ""}{e.new_status}</span>}</div>
          <div className="mt-1 text-[13px] text-ink">{e.summary}</div>
          {e.evidence.length > 0 && <ul className="mt-1 list-disc pl-4 text-xs text-ink-2">{e.evidence.map((x, i) => <li key={i}>{x.description ?? JSON.stringify(x)}</li>)}</ul>}
          {e.details?.changes && <details className="mt-1 text-xs text-ink-3"><summary className="cursor-pointer">changes</summary><pre className="whitespace-pre-wrap font-mono text-[11px]">{JSON.stringify(e.details.changes, null, 2)}</pre></details>}
          {e.details?.experiment_id && <A className="text-xs" href={`/experiments/${e.details.experiment_id}`}>experiment →</A>}
        </li>
      ))}
    </ol>
  );
}

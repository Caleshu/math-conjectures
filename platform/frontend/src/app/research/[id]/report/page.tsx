"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import type { ReactNode } from "react";
import { MathText } from "@/components/Math";
import { roleName } from "@/components/Research";
import { Button, ErrorBox, Loading, StatusBadge, fmtDate } from "@/components/ui";
import { API_URL } from "@/lib/api";
import { useApi } from "@/lib/hooks";

const GROUPS: [string, string][] = [
  ["refuted", "Refuted by review"], ["disputed", "Disputed (flawed or unsupported)"], ["needs_work", "Needs work"],
  ["no_issues_found", "No issues found by the AI reviewer (not a certification)"], ["unreviewed", "Not reviewed"],
];

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const { data: r, error, loading, reload } = useApi<any>(`/api/research/runs/${id}/report`);
  if (loading && !r) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  if (!r) return null;
  const c = r.conjecture, run = r.run, s = r.source;
  return (
    <article className="report mx-auto max-w-[820px] text-[14px] leading-relaxed text-ink">
      <div className="mb-6 flex items-center justify-between gap-3 print:hidden">
        <Link href={`/research/${run.id}`} className="text-sm text-accent">← Back to run</Link>
        <div className="flex gap-2">
          <a href={`${API_URL}/api/research/runs/${run.id}/report.md`}><Button>Download Markdown</Button></a>
          <Button variant="primary" onClick={() => window.print()}>Print / Save as PDF</Button>
        </div>
      </div>
      <div className="text-xs uppercase tracking-[0.14em] text-ink-3">Research report</div>
      <h1 className="mt-1 font-serif text-[1.9rem] leading-tight"><MathText text={c.title} /></h1>
      <p className="mt-2 text-[13px] text-ink-2">
        Run <code>{run.id.slice(0, 8)}</code> · <StatusBadge status={run.status} /> · {run.iterations} iteration(s) · {fmtDate(run.started_at, true)} to {fmtDate(run.finished_at, true) || "in progress"}
        {run.usage && <> · {run.usage.model_calls} model calls, {Math.round(run.usage.tokens / 1000)}k tokens, {run.usage.experiments} experiments</>}
      </p>
      {run.stop_reason && <p className="text-[13px] text-ink-2">Stopped because: {run.stop_reason}</p>}
      <div className="my-5 rounded-md border border-warn/30 bg-warn-soft px-4 py-3 text-[13px] text-warn">
        AI agents produced everything under Claims, Candidate lemmas, Proof attempts and Speculative ideas, and <strong>none of it is established</strong>. &ldquo;No issues found&rdquo; means an AI reviewer did not find an error. Only <em>Established facts</em> carry a citation or a reproduced computation.
      </div>

      <H>Original conjecture</H>
      <div className="statement rounded border border-rule bg-surface px-4 py-3"><MathText text={c.original_statement} macros={r.macros} /></div>
      {c.normalized_statement && <p className="mt-2"><strong>Normalized statement.</strong> <MathText text={c.normalized_statement} /></p>}
      <p className="mt-2 text-[13px] text-ink-2">Recorded status: <StatusBadge status={c.status} /></p>

      <H>Source</H>
      <p>{(s.authors ?? []).join(", ")}, <em>{s.title}</em> ({s.year}){s.arxiv_id && <>, arXiv:{s.arxiv_id}</>}{s.doi && <>, doi:{s.doi}</>}</p>

      {c.definitions?.length > 0 && <><H>Definitions</H><ul className="list-disc pl-5">{c.definitions.map((d: any, k: number) => <li key={k}><strong><MathText text={d.term} /></strong>: <MathText text={d.definition} /></li>)}</ul></>}

      <H>Established facts</H>
      <p className="text-[13px] text-ink-3">Known results recorded with citations:</p>
      <List items={r.established} empty="None recorded." render={(k: any) => <><MathText text={k.statement} /> <span className="text-ink-3">({k.citation}; computational: {String(k.computational)}; reproduced: {String(k.reproduced)})</span></>} />
      <p className="mt-2 text-[13px] text-ink-3">Finite computations run in this research and judged trustworthy (finite results, not proofs):</p>
      <List items={r.trusted_computations} empty="None." render={(e: any) => <><strong>{e.title}</strong>: <MathText text={e.interpretation} /></>} />

      <H>Agents involved</H>
      <p>{r.agents.map((a: any) => a.name).join(" · ")}</p>

      <H>Approaches attempted</H>
      <List items={r.approaches} empty="None." render={(a: any) => <><strong>{roleName(a.agent)}</strong> <span className="text-ink-3">(iteration {a.iteration}{a.phase && a.phase !== "main" ? `, ${a.phase}` : ""})</span>: <MathText text={a.summary} /></>} />

      <H>Mathematical claims</H>
      {r.claims.length === 0 && <p className="text-ink-3">None.</p>}
      {GROUPS.map(([k, title]) => r.claim_groups[k]?.length > 0 && (
        <section key={k} className="mt-3">
          <h3 className="font-semibold text-ink">{title}</h3>
          <ul className="mt-1 space-y-2">{r.claim_groups[k].map((x: any) => <ClaimLine key={x.id} x={x} />)}</ul>
        </section>
      ))}

      <H>Computational experiments</H>
      <List items={r.experiments} empty="None." render={(e: any) => <><strong>{e.title}</strong> <span className="text-ink-3">[{e.status}, {e.kind?.replace(/_/g, " ")}, {e.runtime_s != null ? `${e.runtime_s.toFixed(1)}s` : "not run"}]</span>{e.summary && typeof e.summary === "string" && <>: <MathText text={e.summary} /></>}{e.interpretation && <div className="text-[13px] text-ink-2">Interpretation: <MathText text={e.interpretation} /></div>}</>} />

      <H>Candidate lemmas</H>
      <List items={r.candidate_lemmas} empty="None." render={(x: any) => <><code className="text-ink-3">{x.ref}</code> <MathText text={x.statement} /> <em className="text-ink-3">({x.status.replace(/_/g, " ")})</em></>} />

      <H>Proof attempts</H>
      {r.proof_attempts.length === 0 && <p className="text-ink-3">None.</p>}
      {r.proof_attempts.map((p: any) => (
        <section key={p.id} className="mt-3 break-inside-avoid-page">
          <h3 className="font-semibold"><code className="text-ink-3">{p.ref}</code> <MathText text={p.strategy} /></h3>
          <p className="text-[13px] text-ink-3">By {roleName(p.author)}. Status {p.status.replace(/_/g, " ")}, level: {p.level_name}.</p>
          <div className="mt-1 whitespace-pre-wrap rounded border border-rule bg-surface px-3 py-2 text-[13px]"><MathText text={p.argument} /></div>
          {p.known_gaps?.length > 0 && <><p className="mt-1 text-[13px] text-ink-3">Gaps admitted by the author:</p><ul className="list-disc pl-5 text-[13px]">{p.known_gaps.map((g: string, k: number) => <li key={k}><MathText text={g} /></li>)}</ul></>}
          {p.reviews.map((rv: any, k: number) => (
            <div key={k} className="mt-1 text-[13px]"><span className="text-ink-3">Reviewer verdict:</span> <strong>{rv.verdict.replace(/_/g, " ")}</strong>
              <ul className="list-disc pl-5">{rv.issues.map((i: any, j: number) => <li key={j}>{i.kind.replace(/_/g, " ")}: <MathText text={i.detail} /></li>)}</ul></div>
          ))}
        </section>
      ))}

      <H>Counterexamples and constructions</H>
      <List items={r.counterexamples} empty="None." render={(x: any) => <><code className="text-ink-3">{x.ref}</code> <MathText text={x.statement} /> <em className="text-ink-3">({x.status.replace(/_/g, " ")})</em></>} />

      <H>Literature</H>
      {r.literature.queries?.length > 0 && <p className="text-[13px] text-ink-3">Queries: {r.literature.queries.map((q: any) => q.text).join("; ")}</p>}
      {r.literature.assessments.length === 0 && <p className="text-ink-3">No literature assessment.</p>}
      {r.literature.assessments.map((a: any, k: number) => (
        <div key={k}>
          <ul className="list-disc pl-5">{a.works.map((w: any, j: number) => <li key={j}><em>{w.record.title}</em> ({w.record.year}{w.record.arxiv_id && `, arXiv:${w.record.arxiv_id}`}{w.record.doi && `, doi:${w.record.doi}`}): {w.relevance}. <MathText text={w.how_it_relates} />{w.may_resolve_conjecture && <strong className="text-bad"> May resolve the conjecture. Check this.</strong>}</li>)}</ul>
          {a.novelty && <p className="mt-1 text-[13px]"><span className="text-ink-3">Novelty assessment:</span> <MathText text={a.novelty} /></p>}
        </div>
      ))}
      {Object.keys(r.literature.source_errors ?? {}).length > 0 && <p className="mt-1 text-xs text-ink-3">Source errors (coverage is incomplete): {Object.entries(r.literature.source_errors).map(([k, v]) => `${k}: ${v}`).join("; ")}</p>}

      <H>Failed approaches</H>
      <List items={r.failed_approaches} empty="None." render={(f: any) => <><strong><MathText text={f.approach} /></strong> <span className="text-ink-3">({roleName(f.agent)})</span>: <MathText text={f.why_it_fails} /></>} />

      <H>Conflicts identified</H>
      <List items={r.conflicts} empty="None." render={(x: any) => <><MathText text={x.description} /> {x.refs?.length > 0 && <code className="text-ink-3">[{x.refs.join(", ")}]</code>}. <span className="text-ink-3">To resolve:</span> <MathText text={x.how_to_resolve} /></>} />

      <H>Speculative ideas</H>
      <List items={r.speculative} empty="None." render={(x: any) => <><code className="text-ink-3">{x.ref}</code> <MathText text={x.statement} /></>} />

      <H>Unresolved gaps</H>
      <List items={[
        ...r.proof_attempts.flatMap((p: any) => p.known_gaps.map((g: string) => ({ ref: p.ref, text: g }))),
        ...r.claims.filter((x: any) => ["disputed", "needs_work"].includes(x.status)).flatMap((x: any) => (x.reviews.at(-1)?.issues ?? []).map((i: any) => ({ ref: x.ref, text: `reviewer: ${i.detail}` }))),
      ]} empty="None recorded." render={(g: any) => <><code className="text-ink-3">{g.ref}</code> <MathText text={g.text} /></>} />

      <H>Recommended next steps</H>
      <List items={r.next_steps} empty="None." render={(n: any) => <><MathText text={n.text} /> <span className="text-ink-3">({roleName(n.agent)})</span></>} />

      {r.syntheses.length > 0 && <><H>Orchestrator assessment</H><p className="whitespace-pre-wrap"><MathText text={r.syntheses.at(-1).overall_assessment ?? ""} /></p></>}
    </article>
  );
}

function H({ children }: { children: ReactNode }) {
  return <h2 className="mb-2 mt-7 border-b border-rule pb-1 font-serif text-[1.25rem] text-ink break-after-avoid">{children}</h2>;
}

function List<T>({ items, render, empty }: { items: T[]; render: (x: T) => ReactNode; empty: string }) {
  if (!items?.length) return <p className="text-ink-3">{empty}</p>;
  return <ul className="list-disc space-y-1 pl-5">{items.map((x, k) => <li key={k}>{render(x)}</li>)}</ul>;
}

function ClaimLine({ x }: { x: any }) {
  const rv = x.reviews?.at(-1);
  return (
    <li className="break-inside-avoid-page">
      <div className="text-[12px] text-ink-3"><code>{x.ref}</code> · {x.type.replace(/_/g, " ")} · by {roleName(x.author)} · author&apos;s support: {x.author_support?.replace(/_/g, " ")} · level: {x.level_name}</div>
      <div><MathText text={x.statement} /></div>
      {x.justification && <div className="text-[13px] text-ink-2"><span className="text-ink-3">Justification:</span> <MathText text={x.justification} /></div>}
      {rv && <div className="text-[13px] text-ink-2"><span className="text-ink-3">Reviewer:</span> <strong>{rv.verdict.replace(/_/g, " ")}</strong>{rv.issues?.length > 0 && <>: {rv.issues.map((i: any) => i.detail).join("; ")}</>}{rv.counterexample_attempt && <div><span className="text-ink-3">Counterexample attempt:</span> <MathText text={rv.counterexample_attempt} /></div>}</div>}
    </li>
  );
}

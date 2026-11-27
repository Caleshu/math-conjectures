"use client";
import { useState } from "react";
import { MathText } from "@/components/Math";
import { A, Badge, StatusBadge } from "@/components/ui";

export const ROLE_NAMES: Record<string, string> = {
  strategist: "Mathematical Strategist",
  extremal: "Extremal Mathematician",
  construction: "Construction & Counterexample Agent",
  computational: "Computational Mathematician",
  literature: "Literature Specialist",
  reviewer: "Adversarial Proof Reviewer",
  orchestrator: "Orchestrator",
};
export const roleName = (r: string) => ROLE_NAMES[r.replace("agent:", "")] ?? r;

export const STATUS_HELP: Record<string, string> = {
  unverified: "Not reviewed yet.",
  no_issues_found: "The AI reviewer looked for errors and found none. This is not a certification.",
  needs_work: "The reviewer found gaps that need filling.",
  disputed: "The reviewer found it flawed or unsupported.",
  refuted: "The reviewer gave a counterexample or disproof.",
};

export const LEVELS: Record<number, string> = {
  1: "idea", 2: "experimental evidence", 3: "finite computational result", 4: "written proof attempt",
  5: "independently reviewed (AI)", 6: "formally verified (Lean)",
};

export function Review({ r }: { r: any }) {
  return (
    <div className="mt-2 rounded border border-rule bg-paper px-3 py-2 text-[12.5px]">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-ink">Adversarial reviewer</span>
        <StatusBadge status={r.verdict} />
        {r.confidence != null && <span className="text-ink-3 tabular">confidence {Number(r.confidence).toFixed(2)}</span>}
        {r.iteration && <span className="text-ink-3">iteration {r.iteration}</span>}
      </div>
      {r.issues?.length > 0 && (
        <ul className="mt-1.5 list-disc space-y-0.5 pl-5 text-ink-2">
          {r.issues.map((i: any, k: number) => <li key={k}><span className="text-ink-3">{i.kind.replace(/_/g, " ")}:</span> <MathText text={i.detail} /></li>)}
        </ul>
      )}
      {r.counterexample_attempt && <div className="mt-1.5 text-ink-2"><span className="text-ink-3">Counterexample attempt:</span> <MathText text={r.counterexample_attempt} /></div>}
    </div>
  );
}

export function ClaimItem({ c }: { c: any }) {
  const [open, setOpen] = useState(false);
  const d = c.details ?? {};
  const just = (c.evidence ?? []).find((e: any) => e.type === "author_justification")?.text;
  const other = (c.evidence ?? []).filter((e: any) => e.type !== "author_justification");
  return (
    <li className="py-3">
      <div className="flex flex-wrap items-center gap-1.5 text-[11.5px]">
        <code className="text-ink-3">C-{c.id.slice(0, 6)}</code>
        <Badge>{c.claim_type.replace(/_/g, " ")}</Badge>
        <span title={STATUS_HELP[c.verification_status]}><StatusBadge status={c.verification_status} /></span>
        <span className="text-ink-3">by {roleName(c.created_by)}</span>
        <span className="text-ink-3">· author&apos;s support: <span className="text-ink-2">{d.author_support?.replace(/_/g, " ")}</span></span>
        {d.confidence != null && <span className="text-ink-3 tabular">· p≈{Number(d.confidence).toFixed(2)}</span>}
        <span className="text-ink-3">· level: {LEVELS[c.validation_level]}</span>
        {d.iteration && <span className="text-ink-3">· it. {d.iteration}</span>}
      </div>
      <div className="statement mt-1.5 text-[14px] leading-relaxed text-ink"><MathText text={c.statement} /></div>
      {(just || c.reviews?.length || other.length) ? (
        <button className="mt-1 text-xs text-accent" onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"} justification and review</button>
      ) : null}
      {open && (
        <div className="mt-1.5">
          {just && <div className="whitespace-pre-wrap text-[12.5px] leading-relaxed text-ink-2"><span className="text-ink-3">Author&apos;s justification:</span> <MathText text={just} /></div>}
          {other.map((e: any, k: number) => (
            <div key={k} className="mt-1 text-xs text-ink-3">
              {e.type === "experiments" && e.ids?.length ? <>Backed by sandbox runs: {e.ids.map((id: string) => <A key={id} href={`/experiments/${id}`} className="mr-2">E-{id.slice(0, 6)}</A>)}</> : null}
              {e.type === "search_results" ? <>Cites search results: {e.titles.join("; ")}</> : null}
            </div>
          ))}
          {(c.reviews ?? []).map((r: any, k: number) => <Review key={k} r={r} />)}
        </div>
      )}
    </li>
  );
}

export function ProofItem({ p }: { p: any }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="py-3.5">
      <div className="flex flex-wrap items-center gap-2 text-[11.5px]">
        <code className="text-ink-3">P-{p.id.slice(0, 6)}</code>
        <StatusBadge status={p.status} />
        <Badge>{LEVELS[p.validation_level]}</Badge>
        <span className="text-ink-3">by {roleName(p.created_by)}</span>
      </div>
      <div className="mt-1 font-serif text-[15px] text-ink"><MathText text={p.strategy} /></div>
      <button className="mt-1 text-xs text-accent" onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"} argument, gaps and review</button>
      {open && (
        <div className="mt-2 space-y-2">
          <div className="whitespace-pre-wrap rounded border border-rule bg-paper px-3 py-2.5 text-[13px] leading-relaxed text-ink"><MathText text={p.argument} /></div>
          {p.lemma_claim_ids?.length > 0 && <div className="text-[12.5px] text-ink-2"><span className="text-ink-3">Lemmas used:</span><ul className="list-disc pl-5">{p.lemma_claim_ids.map((l: any, k: number) => <li key={k}><MathText text={l.statement} /></li>)}</ul></div>}
          {p.known_gaps?.length > 0 && <div className="text-[12.5px] text-ink-2"><span className="text-ink-3">Gaps admitted by the author:</span><ul className="list-disc pl-5">{p.known_gaps.map((g: string, k: number) => <li key={k}><MathText text={g} /></li>)}</ul></div>}
          {(p.reviewer_feedback ?? []).length === 0 ? <div className="text-xs text-ink-3">Not reviewed yet.</div> : p.reviewer_feedback.map((r: any, k: number) => <Review key={k} r={r} />)}
        </div>
      )}
    </li>
  );
}

export function TaskOutput({ t }: { t: any }) {
  const o = t.output ?? {};
  return (
    <div className="space-y-3 text-[13px]">
      {o.summary && <div className="whitespace-pre-wrap leading-relaxed text-ink"><MathText text={o.summary} /></div>}
      {o.overall_assessment && <div className="whitespace-pre-wrap leading-relaxed text-ink"><MathText text={o.overall_assessment} /></div>}
      {o.queries?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Queries run against real APIs</div>
          <ul className="list-disc pl-5 text-ink-2">{o.queries.map((q: any, k: number) => <li key={k}><code>{q.text}</code>: {q.rationale}</li>)}</ul></div>
      )}
      {o.records && (
        <div><div className="text-xs font-medium text-ink-2">{o.records.length} records returned</div>
          <ul className="max-h-64 overflow-y-auto text-[12px] text-ink-2">{o.records.map((r: any) => (
            <li key={r.ref} className="py-0.5"><code className="text-ink-3">{r.ref}</code> {r.url ? <a className="text-accent" href={r.url} target="_blank" rel="noreferrer">{r.title}</a> : r.title} <span className="text-ink-3">({r.year ?? "n.d."}, {r.source})</span></li>))}</ul>
          {Object.keys(o.source_errors ?? {}).length > 0 && <div className="mt-1 text-xs text-bad">Source errors: {Object.entries(o.source_errors).map(([k, v]) => `${k}: ${v}`).join("; ")}</div>}
        </div>
      )}
      {o.relevant_works?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Relevant works (only real search results are kept)</div>
          <ul className="space-y-1 text-[12.5px] text-ink-2">{o.relevant_works.map((w: any, k: number) => (
            <li key={k}><Badge>{w.relevance}</Badge> <em>{w.record?.title}</em> ({w.record?.year}): <MathText text={w.how_it_relates} />
              {w.may_resolve_conjecture && <strong className="ml-1 text-bad">May resolve the conjecture. Check this.</strong>}</li>))}</ul>
          {o.novelty_assessment && <div className="mt-1 text-[12.5px] text-ink-2"><span className="text-ink-3">Novelty:</span> <MathText text={o.novelty_assessment} /></div>}
        </div>
      )}
      {o.experiments?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Programs written</div>
          <ul className="list-disc pl-5 text-ink-2">{o.experiments.map((e: any, k: number) => (
            <li key={k}>{o.experiment_ids?.[k] ? <A href={`/experiments/${o.experiment_ids[k]}`}>{e.title}</A> : e.title} <span className="text-ink-3">({e.result_kind})</span>: <MathText text={e.question} /></li>))}</ul></div>
      )}
      {o.interpretations?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Interpretation of the sandbox outputs</div>
          <ul className="list-disc pl-5 text-ink-2">{o.interpretations.map((i: any, k: number) => <li key={k}><code>{i.experiment_ref}</code> {i.trustworthy ? "" : <Badge tone="failed">untrustworthy</Badge>} <MathText text={i.interpretation} /></li>)}</ul></div>
      )}
      {o.reviews && <div className="text-xs text-ink-3">{o.reviews.length} review verdicts recorded. See the Claims and Proof attempts tabs.</div>}
      {o.conflicts?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Conflicts identified</div>
          <ul className="list-disc pl-5 text-ink-2">{o.conflicts.map((x: any, k: number) => <li key={k}><MathText text={x.description} /> {x.refs?.length ? <code className="text-ink-3">[{x.refs.join(", ")}]</code> : null}. <span className="text-ink-3">Resolve by:</span> <MathText text={x.how_to_resolve} /></li>)}</ul></div>
      )}
      {o.follow_ups && (
        <div><div className="text-xs font-medium text-ink-2">Decision: {o.continue_research ? "run another iteration" : "stop"}</div>
          <div className="text-ink-2"><MathText text={o.reason ?? ""} /></div>
          {o.follow_ups.length > 0 && <ul className="mt-1 list-disc pl-5 text-ink-2">{o.follow_ups.map((f: any, k: number) => <li key={k}><strong>{roleName(f.agent)}</strong>: <MathText text={f.task} /></li>)}</ul>}</div>
      )}
      {o.failed_approaches?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Failed approaches</div>
          <ul className="list-disc pl-5 text-ink-2">{o.failed_approaches.map((f: any, k: number) => <li key={k}><strong><MathText text={f.approach} /></strong>: <MathText text={f.why_it_fails} /></li>)}</ul></div>
      )}
      {o.experiment_requests?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Computations requested</div>
          <ul className="list-disc pl-5 text-ink-2">{o.experiment_requests.map((f: any, k: number) => <li key={k}><MathText text={f.question} /></li>)}</ul></div>
      )}
      {o.next_steps?.length > 0 && (
        <div><div className="text-xs font-medium text-ink-2">Suggested next steps</div>
          <ul className="list-disc pl-5 text-ink-2">{o.next_steps.map((s: string, k: number) => <li key={k}><MathText text={s} /></li>)}</ul></div>
      )}
    </div>
  );
}

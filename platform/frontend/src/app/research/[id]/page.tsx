"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState, type ReactNode } from "react";
import { MathText } from "@/components/Math";
import { ClaimItem, ProofItem, STATUS_HELP, TaskOutput, roleName } from "@/components/Research";
import { A, Badge, Button, Card, Empty, ErrorBox, Loading, Notice, PageHeader, Spinner, StatusBadge, Tabs, fmtDate } from "@/components/ui";
import { API_URL, api } from "@/lib/api";
import { useApi } from "@/lib/hooks";

type TabKey = "agents" | "claims" | "proofs" | "experiments";
const ACTIVE = ["queued", "running", "cancelling"];

export default function RunPage() {
  const { id } = useParams<{ id: string }>();
  const { data: r, error, loading, reload } = useApi<any>(`/api/research/runs/${id}`, {
    pollMs: 4000, shouldPoll: (d) => ACTIVE.includes(d.status),
  });
  const [tab, setTab] = useState<TabKey>("agents");
  const [err, setErr] = useState<unknown>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  if (loading && !r) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  if (!r) return null;
  const active = ACTIVE.includes(r.status);
  const L = r.limits ?? {};
  const cp = r.checkpoint ?? {};

  async function act(path: string) {
    setErr(null);
    try { await api.post(`/api/research/runs/${r.id}/${path}`); reload(); } catch (e) { setErr(e); }
  }
  const iterations: number[] = Array.from(new Set<number>(r.tasks.map((t: any) => t.iteration))).sort();
  const claims = r.claims.filter((c: any) => statusFilter === "all" || c.verification_status === statusFilter);
  const counts: Record<string, number> = {};
  r.claims.forEach((c: any) => { counts[c.verification_status] = (counts[c.verification_status] ?? 0) + 1; });

  return (
    <>
      <PageHeader eyebrow={<Link href="/research" className="hover:text-ink">Research Lab</Link>}
        title={<MathText text={r.conjecture?.title ?? "Research run"} />}
        subtitle={<>Run <code>{r.id.slice(0, 8)}</code>, started {fmtDate(r.started_at ?? r.created_at, true)}{r.finished_at && <>, finished {fmtDate(r.finished_at, true)}</>}. Conjecture status: <StatusBadge status={r.conjecture?.status ?? "?"} />{" "}
          {r.conjecture && <Link className="text-accent" href={`/conjectures/${r.conjecture.slug}`}>open conjecture</Link>}</>}
        actions={<>
          <StatusBadge status={r.status} />
          {r.status === "running" || r.status === "queued" ? <Button variant="danger" onClick={() => act("cancel")}>Stop run</Button> : null}
          {["failed", "cancelled"].includes(r.status) && <Button onClick={() => act("resume")}>Resume</Button>}
          <Link href={`/research/${r.id}/report`}><Button variant="primary">Report</Button></Link>
        </>} />
      <ErrorBox error={err} />
      {r.error && <div className="mb-4"><Notice tone="warn"><strong>Run stopped with an error:</strong> {r.error}</Notice></div>}

      <div className="mb-6 grid grid-cols-5 gap-3">
        <Stat label="Phase" value={<span className="flex items-center gap-1.5">{active && <Spinner />}{cp.phase ?? r.status}</span>} />
        <Stat label="Iteration" value={`${r.iteration} / ${L.max_iterations}`} />
        <Stat label="Model calls" value={`${r.usage.model_calls} / ${L.max_model_calls}`} />
        <Stat label="Tokens" value={`${(r.usage.tokens / 1000).toFixed(0)}k / ${(L.max_tokens / 1000).toFixed(0)}k`} />
        <Stat label="Experiments" value={`${r.usage.experiments} / ${L.max_experiments}`} />
      </div>
      {cp.stop_reason && <div className="mb-5"><Notice>Stopped because: {cp.stop_reason}</Notice></div>}
      {cp.resumed_after && !cp.stop_reason && <div className="mb-5 text-xs text-ink-3">Resumed from checkpoints after an earlier stop ({cp.resumed_after}). Finished steps were not repeated.</div>}
      {cp.agent_errors?.length > 0 && <div className="mb-5"><Notice tone="warn">Some agents failed and were skipped: {cp.agent_errors.join("; ")}</Notice></div>}

      <Tabs<TabKey> value={tab} onChange={setTab} tabs={[
        { key: "agents", label: "Agents", count: r.tasks.length },
        { key: "claims", label: "Claims", count: r.claims.length },
        { key: "proofs", label: "Proof attempts", count: r.proof_attempts.length },
        { key: "experiments", label: "Experiments", count: r.experiments.length },
      ]} />

      {tab === "agents" && (
        r.tasks.length === 0 ? <Empty title={active ? "Starting…" : "No agent tasks"}>{active ? "The orchestrator is queued or loading context. This page updates live." : null}</Empty> : (
          <div className="space-y-6">{iterations.map((it) => (
            <section key={it}>
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink-3">Iteration {it}{it === 1 ? ": independent first pass" : ": focused follow-ups"}</h2>
              <div className="space-y-3">{r.tasks.filter((t: any) => t.iteration === it).map((t: any) => <TaskCard key={t.id} t={t} />)}</div>
            </section>))}</div>
        )
      )}

      {tab === "claims" && (
        <Card pad={false} title="Mathematical claims" actions={
          <select className="rounded border border-rule-strong bg-surface px-2 py-1 text-xs" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">all ({r.claims.length})</option>
            {Object.entries(counts).map(([k, v]) => <option key={k} value={k}>{k.replace(/_/g, " ")} ({v})</option>)}
          </select>}>
          <div className="border-b border-rule px-4 py-2 text-xs text-ink-3">Every claim is AI-generated and keeps its author. Status shows what the adversarial reviewer concluded. {statusFilter !== "all" && STATUS_HELP[statusFilter]}</div>
          {claims.length === 0 ? <div className="p-4 text-sm text-ink-3">None yet.</div> : <ul className="divide-y divide-rule px-4">{claims.map((c: any) => <ClaimItem key={c.id} c={c} />)}</ul>}
        </Card>
      )}

      {tab === "proofs" && (
        r.proof_attempts.length === 0 ? <Empty title="No proof attempts">None of the agents has written one yet.</Empty> :
          <Card pad={false}><ul className="divide-y divide-rule px-4">{r.proof_attempts.map((p: any) => <ProofItem key={p.id} p={p} />)}</ul></Card>
      )}

      {tab === "experiments" && (
        r.experiments.length === 0 ? <Empty title="No experiments">The Computational Mathematician has not run anything yet.</Empty> : (
          <Card pad={false}><ul className="divide-y divide-rule">{r.experiments.map((e: any) => (
            <li key={e.id} className="px-4 py-3">
              <div className="flex items-center justify-between gap-3"><A href={`/experiments/${e.id}`}>{e.title}</A><StatusBadge status={e.status} /></div>
              <div className="mt-0.5 text-xs text-ink-3">{e.result_kind.replace(/_/g, " ")} · {e.runtime_seconds != null ? `${e.runtime_seconds.toFixed(1)}s` : "not run"} · {e.environment?.isolation ?? ""}</div>
              {typeof e.result?.summary === "string" && <div className="mt-1 text-[13px] text-ink-2"><MathText text={e.result.summary} /></div>}
              {e.interpretation && <div className="mt-1 text-[12.5px] text-ink-2"><span className="text-ink-3">Interpretation:</span> <MathText text={e.interpretation} /></div>}
            </li>))}</ul></Card>
        )
      )}
      <div className="mt-6 text-xs text-ink-3">Exports: <a className="text-accent" href={`${API_URL}/api/research/runs/${r.id}/report.md`}>Markdown</a> · <Link className="text-accent" href={`/research/${r.id}/report`}>printable report (save as PDF)</Link></div>
    </>
  );
}

function Stat({ label, value }: { label: string; value: ReactNode }) {
  return <div className="rounded-md border border-rule bg-surface px-3 py-2.5"><div className="text-[11px] uppercase tracking-wider text-ink-3">{label}</div><div className="mt-0.5 text-[13px] font-medium text-ink tabular">{value}</div></div>;
}

function TaskCard({ t }: { t: any }) {
  const [open, setOpen] = useState(t.status !== "completed" || t.agent_role === "orchestrator");
  const o = t.output ?? {};
  const phase = t.input?.phase;
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-ink">{roleName(t.agent_role)}</span>
            {phase && phase !== "main" && <Badge>{phase}</Badge>}
            <StatusBadge status={t.status} />
            {o.claim_ids && <span className="text-xs text-ink-3">{o.claim_ids.length} claims{o.proof_attempt_ids?.length ? `, ${o.proof_attempt_ids.length} proof attempts` : ""}</span>}
          </div>
          {t.current_task && <div className="mt-1 flex items-center gap-1.5 text-xs text-ink-2">{t.status === "running" && <Spinner />}<MathText text={t.current_task} /></div>}
          {t.input?.focus && <div className="mt-1 text-xs text-ink-3">Task: {t.input.focus}</div>}
          {t.error && <div className="mt-1 text-xs text-bad">{t.error}</div>}
        </div>
        {t.output && <button className="shrink-0 text-xs text-accent" onClick={() => setOpen(!open)}>{open ? "Collapse" : "Full report"}</button>}
      </div>
      {open && t.output && <div className="mt-3 border-t border-rule pt-3"><TaskOutput t={t} /></div>}
    </Card>
  );
}


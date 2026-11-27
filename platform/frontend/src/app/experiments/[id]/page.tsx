"use client";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { A, Button, Card, ErrorBox, KV, Loading, Notice, PageHeader, StatusBadge, Tabs, fmtDate, inputCls } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Experiment } from "@/lib/types";

type TabKey = "result" | "code" | "logs" | "env";

export default function ExperimentPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("result");
  const { data: e, error, loading, reload } = useApi<Experiment>(`/api/experiments/${id}`, {
    pollMs: 2000, shouldPoll: (d) => d.status === "queued" || d.status === "running",
  });
  const [interp, setInterp] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);
  if (loading && !e) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  if (!e) return null;
  const summary = e.result?.summary;

  async function rerun() {
    try { const r = await api.post<Experiment>(`/api/experiments/${e!.id}/rerun`); router.push(`/experiments/${r.id}`); } catch (x) { setErr(x); }
  }
  async function saveInterp() {
    try { await api.post(`/api/experiments/${e!.id}/interpretation`, { interpretation: interp }); setInterp(null); reload(); } catch (x) { setErr(x); }
  }

  return (
    <>
      <PageHeader eyebrow="Experiment" title={e.title} subtitle={e.problem}
        actions={<><StatusBadge status={e.status} /><Button onClick={rerun} disabled={e.status === "queued" || e.status === "running"}>Reproduce (re-run identical code)</Button></>} />
      <ErrorBox error={err} />
      <div className="grid grid-cols-[1fr_330px] gap-6">
        <div>
          <Tabs<TabKey> value={tab} onChange={setTab} tabs={[{ key: "result", label: "Result" }, { key: "code", label: "Code & parameters" }, { key: "logs", label: "Execution log" }, { key: "env", label: "Environment" }]} />
          {tab === "result" && (
            <div className="space-y-4">
              {(e.status === "queued" || e.status === "running") && <Notice>Running in the sandbox… this page updates automatically.</Notice>}
              {summary && (
                <Card title="Summary">
                  <dl>{Object.entries(summary).map(([k, v]) => <KV key={k} k={k.replace(/_/g, " ")}>{typeof v === "object" ? JSON.stringify(v) : String(v)}</KV>)}</dl>
                </Card>
              )}
              {e.result?.cpsat && <CpsatTable rows={e.result.cpsat} />}
              {e.result?.enumeration && <EnumTable rows={e.result.enumeration} />}
              {e.result?.min_squares && <MinTable rows={e.result.min_squares} />}
              {e.result && <Card title="Full result.json"><pre className="max-h-96 overflow-auto font-mono text-[11px] text-ink-2">{JSON.stringify(e.result, null, 2)}</pre></Card>}
              {!e.result && e.status !== "queued" && e.status !== "running" && <Notice tone="warn">The script produced no result.json. See the execution log.</Notice>}
            </div>
          )}
          {tab === "code" && (
            <div className="space-y-4">
              <Card title="Parameters"><pre className="font-mono text-[12px] text-ink-2">{JSON.stringify(e.parameters, null, 2)}</pre></Card>
              <Card title={`main.py · sha256 ${e.code_sha256}`}><pre className="max-h-[70vh] overflow-auto font-mono text-[11.5px] leading-relaxed text-ink">{e.code}</pre></Card>
            </div>
          )}
          {tab === "logs" && (
            <div className="space-y-4">
              <Card title={`stdout · exit code ${e.exit_code ?? "—"}`}><pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap font-mono text-[11.5px] text-ink">{e.stdout || "(empty)"}</pre></Card>
              <Card title="stderr"><pre className="max-h-[40vh] overflow-auto whitespace-pre-wrap font-mono text-[11.5px] text-bad">{e.stderr || "(empty)"}</pre></Card>
            </div>
          )}
          {tab === "env" && <Card title="Reproducibility record"><pre className="font-mono text-[11.5px] text-ink-2">{JSON.stringify({ environment: e.environment, settings: e.settings }, null, 2)}</pre></Card>}
        </div>
        <div className="space-y-5">
          <Card title="Record">
            <dl>
              <KV k="Kind">{e.result_kind.replace(/_/g, " ")}</KV>
              <KV k="Conjecture">{e.conjecture_id ? <A href={`/conjectures/${e.conjecture_id}?tab=experiments`}>{e.conjecture_title ?? "view"}</A> : "—"}</KV>
              <KV k="Code">{e.library_script ? `library: ${e.library_script}` : "custom"}</KV>
              <KV k="Created">{fmtDate(e.created_at, true)} by {e.created_by}</KV>
              <KV k="Runtime">{e.runtime_seconds != null ? `${e.runtime_seconds.toFixed(2)} s` : "—"}</KV>
              <KV k="Isolation">{e.environment?.isolation ?? "—"}</KV>
              <KV k="Limits">{e.settings.timeout_s}s wall · {e.settings.memory_mb} MB{e.environment?.limits && !e.environment.limits.memory_enforced ? " (not enforced on macOS)" : ""}</KV>
            </dl>
          </Card>
          <Notice tone="warn">A finite computation can refute a conjecture (with a verified counterexample) or confirm specific cases. It does not prove the general statement.</Notice>
          <Card title="Interpretation">
            {interp === null ? (
              <>
                <p className="whitespace-pre-wrap text-[13px] text-ink-2">{e.interpretation || "No interpretation recorded."}</p>
                <Button size="sm" className="mt-3" onClick={() => setInterp(e.interpretation ?? "")}>{e.interpretation ? "Edit" : "Add interpretation"}</Button>
              </>
            ) : (
              <>
                <textarea className={inputCls} rows={6} value={interp} onChange={(x) => setInterp(x.target.value)} />
                <div className="mt-2 flex justify-end gap-2"><Button size="sm" variant="ghost" onClick={() => setInterp(null)}>Cancel</Button><Button size="sm" variant="primary" onClick={saveInterp}>Save</Button></div>
              </>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

function CpsatTable({ rows }: { rows: any[] }) {
  return (
    <Card title="CP-SAT: search for a square-free Hamiltonian cycle" pad={false}>
      <table className="w-full text-[13px]">
        <thead className="border-b border-rule text-left text-xs text-ink-3"><tr><th className="px-4 py-2">n</th><th>|V|</th><th>|E|</th><th>4-cycles</th><th>status</th><th>time (s)</th><th className="pr-4">conclusion</th></tr></thead>
        <tbody className="divide-y divide-rule tabular">{rows.map((r) => (
          <tr key={r.n}><td className="px-4 py-2">{r.n}</td><td>{r.vertices}</td><td>{r.edges}</td><td>{r.four_cycles}</td><td><StatusBadge status={r.solver_status === "INFEASIBLE" ? "succeeded" : r.solver_status === "UNKNOWN" ? "pending" : "failed"} /> <span className="text-xs">{r.solver_status}</span></td><td>{r.wall_seconds}</td><td className="pr-4 text-xs text-ink-2">{r.conclusion}</td></tr>
        ))}</tbody>
      </table>
    </Card>
  );
}

function EnumTable({ rows }: { rows: any[] }) {
  return (
    <Card title="Exhaustive enumeration" pad={false}>
      <table className="w-full text-[13px]">
        <thead className="border-b border-rule text-left text-xs text-ink-3"><tr><th className="px-4 py-2">n</th><th>Hamiltonian cycles</th><th>square-free</th><th>min inscribed squares</th><th className="pr-4">histogram</th></tr></thead>
        <tbody className="divide-y divide-rule tabular">{rows.map((r) => (
          <tr key={r.n}><td className="px-4 py-2">{r.n}</td><td>{r.hamiltonian_cycles}</td><td>{r.square_free_cycles_found}</td><td>{r.min_inscribed_squares}</td><td className="pr-4 font-mono text-[11px] text-ink-2">{JSON.stringify(r.inscribed_square_histogram)}</td></tr>
        ))}</tbody>
      </table>
    </Card>
  );
}

function MinTable({ rows }: { rows: any[] }) {
  return (
    <Card title="CP-SAT: minimum number of inscribed squares" pad={false}>
      <table className="w-full text-[13px]">
        <thead className="border-b border-rule text-left text-xs text-ink-3"><tr><th className="px-4 py-2">n</th><th>status</th><th>best</th><th>bound</th><th>witness recount</th><th className="pr-4">time (s)</th></tr></thead>
        <tbody className="divide-y divide-rule tabular">{rows.map((r) => (
          <tr key={r.n}><td className="px-4 py-2">{r.n}</td><td className="text-xs">{r.status}</td><td>{r.best_value}</td><td>{r.lower_bound}</td><td>{r.witness_independently_counted}</td><td className="pr-4">{r.seconds}</td></tr>
        ))}</tbody>
      </table>
    </Card>
  );
}

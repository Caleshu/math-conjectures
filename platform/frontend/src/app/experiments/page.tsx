"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button, Card, Empty, ErrorBox, Label, Loading, Notice, PageHeader, StatusBadge, fmtDate, inputCls } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Conjecture, Experiment } from "@/lib/types";

const TEMPLATE = `"""Describe the hypothesis being tested.

Contract: parameters are in params.json (path also in $MRL_PARAMS);
write a JSON object to result.json. No network access; writes only in the working directory.
"""
import json, os
import networkx as nx

params = json.load(open(os.environ.get("MRL_PARAMS", "params.json")))
n = params.get("n", 3)
G = nx.hypercube_graph(n)
result = {"n": n, "vertices": G.number_of_nodes(), "edges": G.number_of_edges()}
print(result)
json.dump(result, open("result.json", "w"))
`;

export default function Page() {
  return <Suspense fallback={<Loading />}><ExperimentsPage /></Suspense>;
}

function ExperimentsPage() {
  const sp = useSearchParams();
  const [creating, setCreating] = useState(sp.get("new") === "1");
  const { data, error, loading, reload } = useApi<{ items: Experiment[] }>("/api/experiments", {
    pollMs: 3000, shouldPoll: (d) => d.items.some((e) => e.status === "queued" || e.status === "running"),
  });
  return (
    <>
      <PageHeader eyebrow="Computation" title="Experiments"
        subtitle="Every computation is stored with its exact code (SHA-256), parameters, software versions, solver settings, isolation level and logs. A finite computation is evidence, never a proof of the general statement."
        actions={<Button variant={creating ? "secondary" : "primary"} onClick={() => setCreating(!creating)}>{creating ? "Close" : "New experiment"}</Button>} />
      {creating && <NewExperiment defaultConjecture={sp.get("conjecture") ?? ""} onCreated={() => { setCreating(false); reload(); }} />}
      <ErrorBox error={error} onRetry={reload} />
      {loading && !data && <Loading />}
      {data && data.items.length === 0 && <Empty title="No experiments yet">Run a library experiment from a conjecture’s Computational Experiments tab, or write your own.</Empty>}
      {data && data.items.length > 0 && (
        <div className="divide-y divide-rule rounded-md border border-rule bg-surface">
          {data.items.map((e) => (
            <Link key={e.id} href={`/experiments/${e.id}`} className="grid grid-cols-[1fr_200px_110px] items-center gap-4 px-4 py-3 hover:bg-paper">
              <div className="min-w-0">
                <div className="truncate text-[14px] text-ink">{e.title}</div>
                <div className="truncate text-xs text-ink-3">{e.conjecture_title ?? "no linked conjecture"} · {e.library_script ? `library: ${e.library_script}` : "custom code"} · sha256 {e.code_sha256.slice(0, 10)}</div>
              </div>
              <div className="text-xs text-ink-3">{fmtDate(e.created_at, true)}<br />{e.runtime_seconds != null ? `${e.runtime_seconds.toFixed(1)} s` : "—"}</div>
              <div className="text-right"><StatusBadge status={e.status} /></div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}

function NewExperiment({ defaultConjecture, onCreated }: { defaultConjecture: string; onCreated: () => void }) {
  const router = useRouter();
  const { data: conjs } = useApi<{ items: Conjecture[] }>("/api/conjectures");
  const [title, setTitle] = useState("");
  const [problem, setProblem] = useState("");
  const [conj, setConj] = useState(defaultConjecture);
  const [code, setCode] = useState(TEMPLATE);
  const [params, setParams] = useState('{"n": 4}');
  const [timeout, setTimeoutS] = useState(120);
  const [memory, setMemory] = useState(2048);
  const [kind, setKind] = useState("exploratory");
  const [err, setErr] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  async function submit() {
    setErr(null); setBusy(true);
    try {
      const parameters = JSON.parse(params || "{}");
      const r = await api.post<Experiment>("/api/experiments", { title, problem, conjecture_id: conj || null, code, parameters, timeout_s: timeout, memory_mb: memory, result_kind: kind });
      onCreated();
      router.push(`/experiments/${r.id}`);
    } catch (e) { setErr(e instanceof SyntaxError ? new Error(`Parameters are not valid JSON: ${e.message}`) : e); } finally { setBusy(false); }
  }
  return (
    <Card title="New experiment" className="mb-6">
      <div className="space-y-3">
        <Notice>Code runs in a separate sandboxed Python process (no network, writes confined to its working directory, CPU/file limits, wall-clock timeout) with networkx, sympy and OR-Tools available. Secrets are not passed to it.</Notice>
        <div className="grid grid-cols-2 gap-3">
          <label><Label>Title</Label><input className={inputCls} value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          <label><Label>Linked conjecture</Label>
            <select className={inputCls} value={conj} onChange={(e) => setConj(e.target.value)}>
              <option value="">None</option>{(conjs?.items ?? []).map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select></label>
        </div>
        <label className="block"><Label>Problem / hypothesis being tested</Label><input className={inputCls} value={problem} onChange={(e) => setProblem(e.target.value)} /></label>
        <label className="block"><Label>Code (Python)</Label>
          <textarea className={`${inputCls} font-mono text-[12px]`} rows={16} spellCheck={false} value={code} onChange={(e) => setCode(e.target.value)} /></label>
        <div className="grid grid-cols-[1fr_120px_120px_200px] gap-3">
          <label><Label hint="JSON">Parameters</Label><input className={`${inputCls} font-mono`} value={params} onChange={(e) => setParams(e.target.value)} /></label>
          <label><Label>Timeout (s)</Label><input type="number" className={inputCls} value={timeout} onChange={(e) => setTimeoutS(Number(e.target.value))} /></label>
          <label><Label>Memory (MB)</Label><input type="number" className={inputCls} value={memory} onChange={(e) => setMemory(Number(e.target.value))} /></label>
          <label><Label>Result kind</Label>
            <select className={inputCls} value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="exploratory">Exploratory</option><option value="heuristic_search">Heuristic search</option><option value="finite_computation">Finite computation (exhaustive / exact)</option>
            </select></label>
        </div>
        <ErrorBox error={err} />
        <div className="flex justify-end"><Button variant="primary" disabled={busy || title.trim().length < 3 || problem.trim().length < 3} onClick={submit}>{busy ? "Submitting…" : "Run in sandbox"}</Button></div>
      </div>
    </Card>
  );
}

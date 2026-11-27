"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { AutopilotCard } from "@/components/Autopilot";
import { MathText } from "@/components/Math";
import { Button, Card, Empty, ErrorBox, Label, Loading, Notice, PageHeader, StatusBadge, fmtDate, inputCls } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";

type Meta = {
  agents: { role: string; name: string; description: string }[];
  default_limits: Record<string, any>; limit_bounds: Record<string, [number, number]>;
  providers: string[]; default_provider: string | null;
};
type Run = {
  id: string; status: string; iteration: number; created_at: string; finished_at: string | null;
  limits: Record<string, any>; checkpoint: Record<string, any>; claim_count: number;
  usage: { model_calls: number; tokens: number; experiments: number };
  conjecture: { id: string; slug: string; title: string; status: string } | null;
};

const LIMIT_FIELDS: [string, string, string][] = [
  ["max_iterations", "Iterations", "independent pass + focused follow-ups"],
  ["max_model_calls", "Max model calls", "hard stop"],
  ["max_experiments", "Max experiments", "sandboxed programs"],
  ["experiment_timeout_s", "Experiment timeout (s)", "per program"],
  ["max_runtime_s", "Max runtime (s)", "wall clock"],
  ["concurrency", "Agents in parallel", ""],
];

export default function Page() {
  return <Suspense fallback={<Loading />}><ResearchLab /></Suspense>;
}

function ResearchLab() {
  const { data: meta, error: metaErr } = useApi<Meta>("/api/research/meta");
  const { data, error, loading, reload } = useApi<{ items: Run[] }>("/api/research/runs", {
    pollMs: 5000, shouldPoll: (d) => d.items.some((r) => ["queued", "running", "cancelling"].includes(r.status)),
  });
  return (
    <>
      <PageHeader eyebrow="Research engine" title="Research Lab"
        subtitle="Six AI agents investigate a conjecture under hard limits. Their first pass is independent, their programs run in the sandbox, literature searches hit real APIs, and an adversarial reviewer checks their work. Everything they produce stays unverified until it has been checked." />
      <ErrorBox error={error || metaErr} onRetry={reload} />
      <div className="grid grid-cols-[1fr_400px] gap-6">
        <div className="space-y-6">
          <Card title="Research runs" pad={false}>
            {loading && !data ? <Loading /> : !data || data.items.length === 0 ? <div className="p-4"><Empty title="No research runs yet">Launch one with the form on the right.</Empty></div> : (
              <ul className="divide-y divide-rule">{data.items.map((r) => (
                <li key={r.id} className="px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <Link href={`/research/${r.id}`} className="min-w-0 font-serif text-[15px] text-ink hover:text-accent"><MathText text={r.conjecture?.title ?? "(deleted conjecture)"} /></Link>
                    <StatusBadge status={r.status} />
                  </div>
                  <div className="mt-1 flex flex-wrap gap-x-3 text-xs text-ink-3 tabular">
                    <span>{fmtDate(r.created_at, true)}</span>
                    <span>iteration {r.iteration}/{r.limits.max_iterations}</span>
                    <span>{r.usage.model_calls}/{r.limits.max_model_calls} model calls</span>
                    <span>{r.usage.experiments} experiments</span>
                    <span>{r.claim_count} claims</span>
                    {r.checkpoint?.phase && <span className="text-ink-2">{r.checkpoint.phase}</span>}
                  </div>
                </li>))}</ul>
            )}
          </Card>
          {meta && (
            <Card title="The team">
              <ul className="divide-y divide-rule">
                {meta.agents.map((a) => <li key={a.role} className="grid grid-cols-[240px_1fr] gap-4 py-2.5 text-[13px]"><span className="font-medium text-ink">{a.name}</span><span className="text-ink-2">{a.description}</span></li>)}
              </ul>
              <p className="mt-3 text-xs leading-relaxed text-ink-3">
                How a run works. Iteration 1 is independent: five agents work in parallel and none sees another&apos;s output. The reviewer then checks every proof attempt and the strongest claims, without knowing who wrote them. The orchestrator identifies conflicts and decides whether a focused follow-up iteration is worthwhile. In follow-ups, agents see the team&apos;s claims labelled UNVERIFIED, with their review status. Each step is checkpointed, so a run interrupted by a restart resumes where it stopped.
              </p>
            </Card>
          )}
        </div>
        <div className="space-y-6"><AutopilotCard />{meta ? <Launch meta={meta} onLaunched={reload} /> : <Loading />}</div>
      </div>
    </>
  );
}

function Launch({ meta, onLaunched }: { meta: Meta; onLaunched: () => void }) {
  const router = useRouter();
  const sp = useSearchParams();
  const { data: cs } = useApi<any>("/api/conjectures?sort=updated");
  const items: any[] = cs ? (Array.isArray(cs) ? cs : cs.items) : [];
  const [cid, setCid] = useState<string>("");
  const [limits, setLimits] = useState<Record<string, number>>(() => Object.fromEntries(LIMIT_FIELDS.map(([k]) => [k, meta.default_limits[k]])));
  const [err, setErr] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (cid || !items.length) return;
    const pre = sp.get("conjecture");
    setCid((items.find((c) => c.slug === pre || c.id === pre) ?? items[0]).id);
  }, [items, sp, cid]);
  const chosen = items.find((c) => c.id === cid);
  const noProvider = meta.providers.length === 0;

  async function go() {
    setBusy(true); setErr(null);
    try {
      const r = await api.post<Run>("/api/research/runs", { conjecture_id: cid, limits });
      onLaunched();
      router.push(`/research/${r.id}`);
    } catch (e) { setErr(e); setBusy(false); }
  }
  return (
    <Card title="Launch a research run">
      <div className="space-y-3">
        {noProvider && <Notice tone="warn">No AI provider is available. Install and log in to Claude Code (which uses your Claude subscription), or set <code>ANTHROPIC_API_KEY</code>, then restart the API.</Notice>}
        <label className="block"><Label>Conjecture</Label>
          <select className={inputCls} value={cid} onChange={(e) => setCid(e.target.value)}>
            {items.map((c) => <option key={c.id} value={c.id}>{c.title} [{c.status}]</option>)}
          </select>
        </label>
        {items.length === 0 && <p className="text-xs text-ink-3">No conjectures recorded yet. Record one from <Link className="text-accent" href="/discover">Discover</Link>.</p>}
        {chosen && ["SOLVED", "DISPROVED", "SUPERSEDED"].includes(chosen.status) && (
          <Notice>This conjecture is recorded as <strong>{chosen.status}</strong>. The agents will see that, along with its known results. A run can still be useful, for example to find the exact range where it holds, a structural explanation, or an infinite counterexample family.</Notice>
        )}
        {chosen?.status === "UNVERIFIED" && <Notice>Its open/solved status has not been verified yet. Agents are told so, and the Literature Specialist will search for prior resolutions.</Notice>}
        <div className="grid grid-cols-2 gap-2.5">
          {LIMIT_FIELDS.map(([k, label, hint]) => {
            const [lo, hi] = meta.limit_bounds[k] ?? [0, 1e9];
            return (
              <label key={k} className="block"><Label hint={hint}>{label}</Label>
                <input type="number" min={lo} max={hi} className={inputCls} value={limits[k]}
                  onChange={(e) => setLimits({ ...limits, [k]: Number(e.target.value) })} /></label>
            );
          })}
        </div>
        <div className="text-xs leading-relaxed text-ink-3">
          Provider: <strong className="text-ink-2">{meta.default_provider ?? "none"}</strong>
          {meta.default_provider === "claude_code" && <> (your Claude subscription: no per-call billing, but it counts against your plan&apos;s usage limits)</>}
          {meta.default_provider?.startsWith("team") && <> (Claude and GPT split the agent roles, swap them each iteration and review each other&apos;s work; if one hits a usage limit the other takes over. GPT through Codex uses your ChatGPT plan, with no per-call billing)</>}.
          With the defaults, a run takes roughly 10–40 minutes and uses about 10–20 model calls.
        </div>
        <ErrorBox error={err} />
        <Button variant="primary" className="w-full" onClick={go} disabled={!cid || busy || noProvider}>{busy ? "Launching…" : "Launch research run"}</Button>
      </div>
    </Card>
  );
}

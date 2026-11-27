"use client";
import Link from "next/link";
import { useState } from "react";
import { MathText } from "@/components/Math";
import { Badge, Button, Card, ErrorBox, Notice, Spinner, StatusBadge, fmtDate } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";

export function AutopilotCard() {
  const { data: a, error, reload } = useApi<any>("/api/autopilot", { pollMs: 10000 });
  const [err, setErr] = useState<unknown>(null);
  const [showLog, setShowLog] = useState(false);
  if (!a) return <ErrorBox error={error} onRetry={reload} />;
  async function toggle() {
    setErr(null);
    try { await api.post("/api/autopilot", { enabled: !a.enabled }); reload(); } catch (e) { setErr(e); }
  }
  async function exportNow() {
    setErr(null);
    try { await api.post("/api/autopilot/export"); reload(); } catch (e) { setErr(e); }
  }
  const cooling = a.cooldown_until && new Date(a.cooldown_until) > new Date();
  const ex = a.export?.last;
  return (
    <Card title="Autopilot" actions={<Button size="sm" variant={a.enabled ? "danger" : "primary"} onClick={toggle}>{a.enabled ? "Pause" : "Start"}</Button>}>
      <div className="space-y-3 text-[13px]">
        <div className="flex items-center gap-2">
          {a.enabled ? <Badge tone="running">running</Badge> : <Badge tone="cancelled">paused</Badge>}
          {a.enabled && a.current && <Link className="text-accent" href={`/research/${a.current.research_run_id}`}>current run</Link>}
          {a.enabled && (a.current?.active_runs?.length ?? 0) > 1 && <span className="text-xs text-ink-3">{a.current.active_runs.length} runs in parallel (up to {a.parallel_runs})</span>}
          {cooling && <span className="text-xs text-warn">cooling down until {fmtDate(a.cooldown_until, true)}</span>}
          {a.blocked && <span className="text-xs text-bad">{a.blocked}</span>}
        </div>
        {a.providers?.length > 0 && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {a.providers.map((p: any) => (
              <span key={p.provider} className="text-ink-2">
                <strong>{p.provider}</strong>{" "}
                {p.resting ? <span className="text-warn">resting until {fmtDate(p.until, true)} ({p.reason})</span> : <span className="text-ok">working</span>}
                {Object.entries(p.windows ?? {}).map(([w, v]: any) => v?.utilization != null && <span key={w} className="text-ink-3"> · {w.replace("_", "-")} {Math.round(v.utilization * 100)}%</span>)}
              </span>
            ))}
          </div>
        )}
        <p className="text-xs leading-relaxed text-ink-3">The autopilot keeps several research runs going at once. When Claude passes 90% of a usage window, Codex takes over all of its work until the window resets, and the reverse also applies, so research only pauses if both are at their limits. Before each run it does a novelty pre-check: real searches plus your repository&apos;s index. It skips anything already resolved, already in your repo, or trivial. When it runs out of problems, it takes AI-extracted open problems from papers, then discovers new arXiv papers. Novelty pre-checks and paper extraction run on Codex to save Claude usage for research.</p>
        {a.last_action && <div className="flex items-start gap-1.5 text-ink-2">{a.enabled && !cooling && <Spinner className="mt-0.5" />}<span>Last: {a.last_action}</span></div>}
        {a.waiting && <div className="text-xs text-ink-3">Waiting: {a.waiting}</div>}
        {a.last_error && <div className="text-xs text-bad">Last error: {a.last_error}</div>}
        <div>
          <div className="text-xs font-medium text-ink-2">Queue ({a.queue.length})</div>
          {a.queue.length === 0 ? <div className="text-xs text-ink-3">Empty. The next tick will promote or discover problems.</div> :
            <ul className="mt-1 space-y-1">{a.queue.slice(0, 6).map((q: any) => <li key={q.id} className="text-xs"><Link className="text-accent" href={`/conjectures/${q.slug}`}><MathText text={q.title} /></Link> {q.precheck && <Badge>{q.precheck}</Badge>}</li>)}</ul>}
        </div>
        {a.skipped.length > 0 && (
          <div>
            <div className="text-xs font-medium text-ink-2">Skipped as already known ({a.skipped.length})</div>
            <ul className="mt-1 space-y-1">{a.skipped.map((q: any) => <li key={q.id} className="text-xs text-ink-2"><Link className="text-accent" href={`/conjectures/${q.slug}`}><MathText text={q.title} /></Link> <Badge>{q.precheck}</Badge> <span className="text-ink-3"><MathText text={(q.reason ?? "").slice(0, 220)} /></span></li>)}</ul>
          </div>
        )}
        <div className="border-t border-rule pt-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-medium text-ink-2">GitHub sync → <code>{a.export.branch}</code></div>
            <Button size="sm" onClick={exportNow} disabled={!a.export.enabled}>Sync now</Button>
          </div>
          <div className="mt-1 text-xs text-ink-3">{a.export.enabled ? <>Every change to a problem is pushed automatically to <a className="text-accent" href={a.export.remote.replace(/\.git$/, "")} target="_blank" rel="noreferrer">{a.export.remote.replace(/^https:\/\/github.com\//, "").replace(/\.git$/, "")}</a>. Only app-owned files are written. Your folders get a single <code>MathResearchLab.md</code>.</> : "Disabled (REPO_EXPORT_ENABLED=false)."}</div>
          {ex && <div className={`mt-1 text-xs ${ex.ok ? "text-ink-2" : "text-bad"}`}>Last sync {fmtDate(ex.at, true)}: {ex.ok ? (ex.pushed ? `pushed ${ex.commit} (${ex.n_files} files)` : "no changes") : ex.error}</div>}
          {a.export.jobs?.[0] && ["queued", "running"].includes(a.export.jobs[0].status) && <div className="mt-1 text-xs text-ink-3"><StatusBadge status={a.export.jobs[0].status} /> sync in progress</div>}
        </div>
        <button className="text-xs text-accent" onClick={() => setShowLog(!showLog)}>{showLog ? "Hide" : "Show"} activity log</button>
        {showLog && <ul className="max-h-64 space-y-0.5 overflow-y-auto text-[11.5px] text-ink-2">{a.log.map((l: any, k: number) => <li key={k}><span className="tabular text-ink-3">{fmtDate(l.at, true)}</span> {l.msg}</li>)}</ul>}
        <ErrorBox error={err} />
        {!a.enabled && a.queue.length === 0 && <Notice>When started, the autopilot looks for problems right away.</Notice>}
      </div>
    </Card>
  );
}

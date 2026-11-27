"use client";
import Link from "next/link";
import { A, Badge, Card, Empty, ErrorBox, Loading, PageHeader, StatusBadge, fieldLabel, fmtDate } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { Job } from "@/lib/types";

type Dash = {
  counts: Record<string, number>;
  status_breakdown: Record<string, number>;
  recent_conjectures: { id: string; slug: string; title: string; field: string; status: string; created_at: string }[];
  activity: { id: string; type: string; summary: string; actor: string; created_at: string; conjecture_title: string; conjecture_slug: string }[];
  jobs: Job[];
};

const STATS: { key: string; label: string; href: string; hint?: string }[] = [
  { key: "papers_indexed", label: "Papers indexed", href: "/papers" },
  { key: "conjectures", label: "Conjectures recorded", href: "/conjectures" },
  { key: "awaiting_verification", label: "Awaiting verification", href: "/conjectures?status=UNVERIFIED", hint: "status UNVERIFIED" },
  { key: "candidates_pending", label: "Candidate passages to review", href: "/discover?tab=review" },
  { key: "active_research_runs", label: "Active research runs", href: "/research" },
  { key: "completed_research_runs", label: "Completed research runs", href: "/research" },
];

const JOB_LABEL: Record<string, string> = {
  ingest_identifier: "Ingest paper", process_paper: "Process paper", llm_extract: "AI extraction", run_experiment: "Experiment",
};

export default function Dashboard() {
  const { data, error, loading, reload } = useApi<Dash>("/api/dashboard", {
    pollMs: 4000, shouldPoll: (d) => d.counts.jobs_active > 0,
  });
  return (
    <>
      <PageHeader eyebrow="Overview" title="Research dashboard"
        subtitle="State of the knowledge base: what has been indexed, what is still unverified, and what has been computed." />
      <ErrorBox error={error} onRetry={reload} />
      {loading && !data && <Loading />}
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-px overflow-hidden rounded-md border border-rule bg-rule xl:grid-cols-6">
            {STATS.map((s) => (
              <Link key={s.key} href={s.href} className="group bg-surface px-4 py-4 hover:bg-paper">
                <div className="font-serif text-[2rem] leading-none text-ink tabular">{data.counts[s.key] ?? 0}</div>
                <div className="mt-2 text-xs leading-snug text-ink-2 group-hover:text-ink">{s.label}</div>
              </Link>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.35fr_1fr]">
            <Card title="Recently recorded problems" actions={<A href="/conjectures" className="text-xs">Library →</A>} pad={false}>
              {data.recent_conjectures.length === 0 ? (
                <div className="p-4"><Empty title="No conjectures yet">
                  Submit a paper on <A href="/discover">Discover Problems</A>, review its candidate passages, and record the open problems you confirm.
                </Empty></div>
              ) : (
                <ul className="divide-y divide-rule">
                  {data.recent_conjectures.map((c) => (
                    <li key={c.id} className="flex items-center justify-between gap-4 px-4 py-3">
                      <div className="min-w-0">
                        <Link href={`/conjectures/${c.slug}`} className="font-serif text-[15px] text-ink hover:text-accent">{c.title}</Link>
                        <div className="mt-0.5 text-xs text-ink-3">{fieldLabel(c.field)} · recorded {fmtDate(c.created_at)}</div>
                      </div>
                      <StatusBadge status={c.status} />
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card title="Pipeline jobs" pad={false}>
              {data.jobs.length === 0 ? <div className="p-4 text-sm text-ink-3">No jobs have run yet.</div> : (
                <ul className="divide-y divide-rule">
                  {data.jobs.map((j) => (
                    <li key={j.id} className="flex items-center justify-between gap-3 px-4 py-2.5 text-[13px]">
                      <div className="min-w-0">
                        <div className="text-ink">{JOB_LABEL[j.job_type] ?? j.job_type}</div>
                        <div className="truncate text-xs text-ink-3">{String(j.progress?.stage ?? "")}{j.error ? ` — ${j.error.split("\n")[0]}` : ""}</div>
                      </div>
                      <div className="flex shrink-0 items-center gap-2 text-xs text-ink-3"><span>{fmtDate(j.updated_at, true)}</span><StatusBadge status={j.status} /></div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          <Card title="Research activity" pad={false}>
            {data.activity.length === 0 ? <div className="p-4 text-sm text-ink-3">No research activity recorded yet.</div> : (
              <ol className="divide-y divide-rule">
                {data.activity.map((e) => (
                  <li key={e.id} className="grid grid-cols-[150px_110px_1fr] gap-4 px-4 py-2.5 text-[13px]">
                    <span className="text-xs text-ink-3 tabular">{fmtDate(e.created_at, true)}</span>
                    <span><Badge>{e.type.replace(/_/g, " ")}</Badge></span>
                    <span className="min-w-0">
                      <Link href={`/conjectures/${e.conjecture_slug}`} className="text-ink hover:text-accent">{e.conjecture_title}</Link>
                      <span className="text-ink-2"> — {e.summary}</span>
                      <span className="ml-1 text-xs text-ink-3">({e.actor})</span>
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </Card>
        </div>
      )}
    </>
  );
}

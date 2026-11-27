"use client";
import { useJob } from "@/lib/hooks";
import type { Job } from "@/lib/types";
import { ErrorBox, Spinner, StatusBadge } from "./ui";

export function JobStatus({ jobId, onDone, render }: {
  jobId: string; onDone?: (j: Job) => void; render?: (j: Job) => React.ReactNode;
}) {
  const { job, error } = useJob(jobId, onDone);
  if (error) return <ErrorBox error={error} />;
  if (!job) return <div className="flex items-center gap-2 text-xs text-ink-3"><Spinner /> waiting for job…</div>;
  const active = job.status === "queued" || job.status === "running";
  return (
    <div className="rounded-md border border-rule bg-paper px-3 py-2 text-[13px]">
      <div className="flex items-center gap-2">
        {active && <Spinner />}
        <StatusBadge status={job.status} />
        <span className="text-ink-2">{String(job.progress?.stage ?? "")}</span>
        {job.attempts > 1 && <span className="text-xs text-ink-3">attempt {job.attempts}/{job.max_attempts}</span>}
      </div>
      {job.error && <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap font-mono text-[11px] text-bad">{job.error}</pre>}
      {render && job.status === "succeeded" && <div className="mt-2">{render(job)}</div>}
    </div>
  );
}

"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ConjectureForm } from "@/components/ConjectureForm";
import { MathText } from "@/components/Math";
import { Badge, Button, Card, Empty, ErrorBox, Label, Loading, PageHeader, StatusBadge, fieldLabel, inputCls } from "@/components/ui";
import { qs } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Conjecture, Meta } from "@/lib/types";

export default function Page() {
  return <Suspense fallback={<Loading />}><Library /></Suspense>;
}

function Multi({ label, options, value, onChange, fmt = fieldLabel }: {
  label: string; options: string[]; value: string[]; onChange: (v: string[]) => void; fmt?: (s: string) => string;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <div className="space-y-1">
        {options.map((o) => (
          <label key={o} className="flex items-center gap-2 text-[13px] text-ink-2">
            <input type="checkbox" checked={value.includes(o)} onChange={(e) => onChange(e.target.checked ? [...value, o] : value.filter((x) => x !== o))} />
            {fmt(o)}
          </label>
        ))}
      </div>
    </div>
  );
}

function Library() {
  const sp = useSearchParams();
  const router = useRouter();
  const { data: meta } = useApi<Meta>("/api/conjectures/meta");
  const [q, setQ] = useState(sp.get("q") ?? "");
  const [fields, setFields] = useState<string[]>(sp.getAll("field"));
  const [statuses, setStatuses] = useState<string[]>(sp.getAll("status"));
  const [diffs, setDiffs] = useState<string[]>(sp.getAll("difficulty"));
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [activity, setActivity] = useState("");
  const [sort, setSort] = useState("updated");
  const [creating, setCreating] = useState(false);
  const path = `/api/conjectures${qs({ q, field: fields, status: statuses, difficulty: diffs, from_date: from, to_date: to, activity, sort })}`;
  const { data, error, loading, reload } = useApi<{ items: Conjecture[]; total: number }>(path);

  return (
    <>
      <PageHeader eyebrow="Knowledge base" title="Conjecture library"
        subtitle="Open problems recorded from the literature. Status reflects verification evidence, not the age of the source."
        actions={<Button onClick={() => setCreating(!creating)}>{creating ? "Close" : "Record manually"}</Button>} />
      {creating && (
        <Card title="Record a conjecture manually" className="mb-6">
          <ConjectureForm onCancel={() => setCreating(false)} onCreated={(c) => router.push(`/conjectures/${c.slug}`)} />
        </Card>
      )}
      <div className="grid grid-cols-[220px_1fr] gap-7">
        <aside className="space-y-5">
          <label className="block"><Label>Search</Label>
            <input className={inputCls} value={q} onChange={(e) => setQ(e.target.value)} placeholder="title, statement, paper" /></label>
          {meta && <>
            <Multi label="Field" options={meta.fields} value={fields} onChange={setFields} />
            <Multi label="Status" options={meta.statuses} value={statuses} onChange={setStatuses} fmt={(s) => s.replace(/_/g, " ")} />
            <Multi label="Difficulty" options={meta.difficulties} value={diffs} onChange={setDiffs} />
          </>}
          <div><Label hint="source publication">Date</Label>
            <div className="grid grid-cols-1 gap-1.5">
              <input type="date" className={inputCls} value={from} onChange={(e) => setFrom(e.target.value)} />
              <input type="date" className={inputCls} value={to} onChange={(e) => setTo(e.target.value)} />
            </div></div>
          <label className="block"><Label>Research activity</Label>
            <select className={inputCls} value={activity} onChange={(e) => setActivity(e.target.value)}>
              <option value="">Any</option><option value="any">Has experiments or runs</option>
              <option value="experiments">Has experiments</option><option value="none">No activity yet</option>
            </select></label>
        </aside>
        <div>
          <div className="mb-3 flex items-center justify-between text-[13px] text-ink-2">
            <span>{data ? `${data.total} problem(s)` : ""}</span>
            <label className="flex items-center gap-2">Sort
              <select className={`${inputCls} w-40`} value={sort} onChange={(e) => setSort(e.target.value)}>
                <option value="updated">Recently updated</option><option value="created">Recently recorded</option>
                <option value="published">Source date</option><option value="title">Title</option>
              </select></label>
          </div>
          <ErrorBox error={error} onRetry={reload} />
          {loading && !data && <Loading />}
          {data && data.items.length === 0 && <Empty title="No matching problems">
            {fields.length || statuses.length || q ? "Clear filters to see everything." : "Record problems from reviewed candidate passages on Discover Problems."}</Empty>}
          <div className="space-y-3">
            {data?.items.map((c) => (
              <Link key={c.id} href={`/conjectures/${c.slug}`} className="block rounded-md border border-rule bg-surface px-5 py-4 transition-colors hover:border-rule-strong">
                <div className="flex items-start justify-between gap-4">
                  <div className="font-serif text-[17px] text-ink">{c.title}</div>
                  <StatusBadge status={c.status} />
                </div>
                <div className="mt-2 line-clamp-2 text-[14px] leading-relaxed text-ink-2"><MathText text={c.normalized_statement} /></div>
                <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-3">
                  <Badge>{fieldLabel(c.field)}</Badge>
                  {c.difficulty_estimate && <span>difficulty: {fieldLabel(c.difficulty_estimate)}</span>}
                  {c.source_paper && <span className="min-w-0 truncate">{c.source_paper.authors?.slice(0, 3).join(", ")} ({c.source_paper.published_date?.slice(0, 4)})</span>}
                  <span>{c.experiment_count} experiment(s)</span>
                  <span>{c.research_run_count} research run(s)</span>
                  {c.verification_confidence != null && <span>confidence {(c.verification_confidence * 100).toFixed(0)}%</span>}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

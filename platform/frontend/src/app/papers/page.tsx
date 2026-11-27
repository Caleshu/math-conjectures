"use client";
import Link from "next/link";
import { useState } from "react";
import { MathText } from "@/components/Math";
import { A, Badge, Empty, ErrorBox, Loading, PageHeader, fmtDate, inputCls } from "@/components/ui";
import { qs } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Paper } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  metadata_only: "metadata only", pdf_downloaded: "PDF downloaded", text_extracted: "text extracted",
  scanned: "scanned", failed: "failed", no_pdf_available: "no open PDF",
};

export default function PapersPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const { data, error, loading, reload } = useApi<{ items: Paper[]; total: number }>(`/api/papers${qs({ q, status, limit: 200 })}`);
  return (
    <>
      <PageHeader eyebrow="Index" title="Papers" subtitle="Every paper in the index, with its processing state. Add papers from Discover Problems." actions={<A href="/discover?tab=submit">Submit a paper →</A>} />
      <div className="mb-4 flex gap-3">
        <input className={inputCls} placeholder="Search title, arXiv ID, DOI" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className={`${inputCls} w-56`} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All states</option>{Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      <ErrorBox error={error} onRetry={reload} />
      {loading && !data && <Loading />}
      {data && data.items.length === 0 && <Empty title="No papers indexed">Use <A href="/discover">Discover Problems</A> to search arXiv, OpenAlex, Crossref and Semantic Scholar, or submit an arXiv ID.</Empty>}
      {data && data.items.length > 0 && (
        <table className="w-full overflow-hidden rounded-md border border-rule bg-surface text-[13px]">
          <thead className="border-b border-rule bg-paper text-left text-xs text-ink-3">
            <tr><th className="px-4 py-2 font-medium">Title</th><th className="px-3 py-2 font-medium">Published</th><th className="px-3 py-2 font-medium">Identifiers</th>
              <th className="px-3 py-2 font-medium">State</th><th className="px-3 py-2 text-right font-medium">Candidates</th></tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {data.items.map((p) => (
              <tr key={p.id} className="hover:bg-paper">
                <td className="max-w-[520px] px-4 py-2.5">
                  <Link href={`/papers/${p.id}`} className="font-serif text-[14.5px] text-ink hover:text-accent"><MathText text={p.title} /></Link>
                  <div className="truncate text-xs text-ink-3">{p.authors.slice(0, 5).join(", ")}</div>
                </td>
                <td className="px-3 py-2.5 text-ink-2 tabular">{p.published_date ?? "—"}</td>
                <td className="px-3 py-2.5 text-xs text-ink-2">{p.arxiv_id && <div>arXiv:{p.arxiv_id}</div>}{p.doi && !p.doi.startsWith("10.48550") && <div className="truncate">{p.doi}</div>}</td>
                <td className="px-3 py-2.5"><Badge tone={p.status === "failed" ? "failed" : p.status === "scanned" ? "succeeded" : undefined}>{STATUS_LABEL[p.status] ?? p.status}</Badge>
                  {p.has_latex && <span className="ml-1.5 text-xs text-ink-3">+LaTeX</span>}</td>
                <td className="px-3 py-2.5 text-right tabular">{p.candidate_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data && <div className="mt-2 text-xs text-ink-3">{data.total} paper(s) · added {fmtDate(data.items.at(-1)?.created_at)} – {fmtDate(data.items[0]?.created_at)}</div>}
    </>
  );
}

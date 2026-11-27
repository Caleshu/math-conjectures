"use client";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CandidateCard } from "@/components/CandidateReview";
import { JobStatus } from "@/components/JobStatus";
import { MathText } from "@/components/Math";
import { A, Badge, Button, Card, ErrorBox, KV, Loading, Notice, PageHeader, Tabs, fmtDate } from "@/components/ui";
import { API_URL, api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Candidate, Job, Paper } from "@/lib/types";

type PaperDetail = Paper & { candidates: Candidate[]; jobs: Job[]; llm_available: string[] };
type TabKey = "overview" | "candidates" | "text" | "latex";

export default function Page() {
  return <Suspense fallback={<Loading />}><PaperView /></Suspense>;
}

function PaperView() {
  const { id } = useParams<{ id: string }>();
  const sp = useSearchParams();
  const initialPage = Number(sp.get("page") ?? 0);
  const [tab, setTab] = useState<TabKey>(initialPage ? "text" : "overview");
  const { data: p, error, loading, reload } = useApi<PaperDetail>(`/api/papers/${id}`, {
    pollMs: 2500, shouldPoll: (d) => d.jobs.some((j) => j.status === "queued" || j.status === "running"),
  });
  const [jobId, setJobId] = useState<string | null>(null);
  const [actionErr, setActionErr] = useState<unknown>(null);

  if (loading && !p) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;
  if (!p) return null;
  const pending = p.candidates.filter((c) => c.review_status === "pending");
  const active = p.jobs.find((j) => j.status === "queued" || j.status === "running");

  async function run(path: string) {
    setActionErr(null);
    try { const r = await api.post<{ job_id: string }>(path, {}); setJobId(r.job_id); } catch (e) { setActionErr(e); }
  }

  return (
    <>
      <PageHeader eyebrow={<span>{p.categories.slice(0, 3).join(" · ")}</span>} title={<MathText text={p.title} />}
        subtitle={<span>{p.authors.join(", ")}{p.published_date && ` · ${p.published_date}`}</span>}
        actions={<>
          <Button onClick={() => run(`/api/papers/${p.id}/process`)} disabled={Boolean(active)}>Re-process</Button>
          <Button variant="primary" onClick={() => run(`/api/papers/${p.id}/extract`)} disabled={p.llm_available.length === 0 || Boolean(active) || !(p.page_count || p.has_latex)}
            title={p.llm_available.length === 0 ? "Install and log in to Claude Code, or set ANTHROPIC_API_KEY, to enable" : "Run the conjecture extraction agent"}>Run AI extraction</Button>
        </>} />
      {p.llm_available.length === 0 && <div className="mb-4"><Notice tone="warn">AI extraction is unavailable: no model provider is available (install and log in to the Claude Code CLI to use your Claude subscription, or set <code>ANTHROPIC_API_KEY</code>, then restart the API). Heuristic candidates below still need human review.</Notice></div>}
      <ErrorBox error={actionErr} />
      {(jobId || active) && <div className="mb-4"><JobStatus jobId={jobId ?? active!.id} onDone={() => reload()} /></div>}
      <Tabs<TabKey> value={tab} onChange={setTab} tabs={[
        { key: "overview", label: "Overview" }, { key: "candidates", label: "Candidate passages", count: pending.length },
        { key: "text", label: "Extracted text", count: p.page_count ?? 0 }, ...(p.has_latex ? [{ key: "latex" as TabKey, label: "LaTeX source" }] : []),
      ]} />
      {tab === "overview" && (
        <div className="grid grid-cols-[1fr_340px] gap-6">
          <Card title="Abstract"><div className="font-serif text-[15px] leading-relaxed text-ink-2"><MathText text={p.abstract ?? "No abstract available."} macros={p.latex_macros} /></div></Card>
          <div className="space-y-5">
            <Card title="Record">
              <dl>
                <KV k="arXiv">{p.arxiv_id ? <A href={`https://arxiv.org/abs/${p.arxiv_id}`}>{p.arxiv_id}</A> : "—"}</KV>
                <KV k="DOI">{p.doi ? <A href={`https://doi.org/${p.doi}`}>{p.doi}</A> : "—"}</KV>
                <KV k="OpenAlex">{p.openalex_id ? <A href={`https://openalex.org/${p.openalex_id}`}>{p.openalex_id}</A> : "—"}</KV>
                <KV k="Venue">{p.venue ?? "—"}</KV>
                <KV k="Citations">{p.cited_by_count ?? "—"} <span className="text-xs text-ink-3">(OpenAlex)</span></KV>
                <KV k="References">{p.references?.length ?? 0}</KV>
                <KV k="Sources">{((p.source_metadata?.sources as string[]) ?? []).join(", ")}</KV>
                <KV k="Indexed">{fmtDate(p.created_at, true)} via {p.discovered_via}</KV>
              </dl>
            </Card>
            <Card title="Processing">
              <dl>
                <KV k="State"><Badge tone={p.status === "failed" ? "failed" : undefined}>{p.status.replace(/_/g, " ")}</Badge></KV>
                <KV k="PDF">{p.pdf_path ? <A href={`${API_URL}/api/papers/${p.id}/pdf`}>stored copy</A> : p.pdf_url ? "not downloaded" : "no location"}</KV>
                <KV k="Text">{p.page_count ? `${p.page_count} pages · ${p.text_extractor}` : "—"}</KV>
                <KV k="LaTeX">{p.has_latex ? `${(p.latex_files ?? []).length} file(s) in source archive` : p.arxiv_id ? "not available" : "n/a"}</KV>
              </dl>
              {p.processing_error && <div className="mt-2 text-xs text-bad">{p.processing_error}</div>}
            </Card>
          </div>
        </div>
      )}
      {tab === "candidates" && (
        <div className="space-y-3">
          {p.candidates.length === 0 && <p className="text-sm text-ink-3">No candidate passages detected.</p>}
          {p.candidates.map((c) => <CandidateCard key={c.id} c={c} onChanged={reload} showPaper={false} macros={p.latex_macros} />)}
        </div>
      )}
      {tab === "text" && <PageText paperId={p.id} count={p.page_count ?? 0} initial={initialPage || 1} />}
      {tab === "latex" && <LatexView paperId={p.id} />}
    </>
  );
}

function PageText({ paperId, count, initial }: { paperId: string; count: number; initial: number }) {
  const [page, setPage] = useState(Math.min(Math.max(initial, 1), Math.max(count, 1)));
  const { data, error, loading } = useApi<{ text: string }>(count ? `/api/papers/${paperId}/pages/${page}` : null);
  if (!count) return <p className="text-sm text-ink-3">No text has been extracted from a PDF for this paper.</p>;
  return (
    <Card title={`Page ${page} of ${count}`} actions={<div className="flex gap-1.5">
      <Button size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</Button>
      <Button size="sm" disabled={page >= count} onClick={() => setPage(page + 1)}>Next →</Button></div>}>
      <ErrorBox error={error} />
      {loading ? <Loading /> : <pre className="whitespace-pre-wrap font-serif text-[14px] leading-relaxed text-ink">{data?.text}</pre>}
    </Card>
  );
}

function LatexView({ paperId }: { paperId: string }) {
  const { data, error, loading } = useApi<string>(`/api/papers/${paperId}/latex`);
  return (
    <Card title="Flattened LaTeX source (read-only, never compiled or executed)">
      <ErrorBox error={error} />
      {loading ? <Loading /> : <pre className="max-h-[70vh] overflow-auto whitespace-pre-wrap font-mono text-[11.5px] leading-relaxed text-ink-2">{data}</pre>}
    </Card>
  );
}

"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CandidateCard } from "@/components/CandidateReview";
import { JobStatus } from "@/components/JobStatus";
import { MathText } from "@/components/Math";
import { A, Badge, Button, Card, Empty, ErrorBox, Label, Loading, Notice, PageHeader, Tabs, inputCls } from "@/components/ui";
import { api, qs } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Candidate, SearchResult } from "@/lib/types";

const SUBJECTS = ["", "graph theory", "combinatorics", "extremal combinatorics", "discrete mathematics", "number theory", "algebra", "geometry"];
const SOURCES = [
  { key: "arxiv", label: "arXiv" }, { key: "openalex", label: "OpenAlex" },
  { key: "crossref", label: "Crossref" }, { key: "semantic_scholar", label: "Semantic Scholar" },
];
type TabKey = "search" | "submit" | "review";

export default function DiscoverPage() {
  return <Suspense fallback={<Loading />}><Discover /></Suspense>;
}

function Discover() {
  const sp = useSearchParams();
  const router = useRouter();
  const tab = (sp.get("tab") as TabKey) || "search";
  const { data: pending, reload: reloadPending } = useApi<{ items: Candidate[] }>("/api/candidates?review_status=pending&limit=500");
  return (
    <>
      <PageHeader eyebrow="Discovery engine" title="Discover problems"
        subtitle="Search the literature, add papers to the index, and review passages the scanner flagged as possible open problems. Nothing becomes a conjecture until it is reviewed." />
      <Tabs<TabKey> value={tab} onChange={(k) => router.replace(`/discover?tab=${k}`)} tabs={[
        { key: "search", label: "Search literature" },
        { key: "submit", label: "Submit a paper" },
        { key: "review", label: "Review candidates", count: pending?.items.length },
      ]} />
      {tab === "search" && <SearchPanel />}
      {tab === "submit" && <SubmitPanel />}
      {tab === "review" && <ReviewPanel items={pending?.items ?? null} reload={reloadPending} />}
    </>
  );
}

function SearchPanel() {
  const [text, setText] = useState("");
  const [subject, setSubject] = useState("graph theory");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [sources, setSources] = useState<string[]>(["arxiv", "openalex", "crossref", "semantic_scholar"]);
  const [limit, setLimit] = useState(20);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const [res, setRes] = useState<{ results: SearchResult[]; source_errors: Record<string, string> } | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [imported, setImported] = useState<{ paper_id: string; job_id: string | null; title: string; created: boolean }[]>([]);

  async function run(e?: React.FormEvent) {
    e?.preventDefault();
    setBusy(true); setErr(null); setSelected(new Set());
    try {
      setRes(await api.post("/api/discovery/search", {
        text, subject: subject || null, from_date: from || null, to_date: to || null, sources, limit,
      }));
    } catch (e) { setErr(e); } finally { setBusy(false); }
  }

  async function importSelected() {
    if (!res) return;
    setErr(null);
    try {
      const records = [...selected].map((i) => res.results[i]);
      const out = await api.post<{ imported: typeof imported }>("/api/discovery/import", { records, process: true });
      setImported((prev) => [...out.imported, ...prev]);
      setRes({ ...res, results: res.results.map((r, i) => selected.has(i) ? { ...r, indexed_paper_id: out.imported.find((x) => x.title === r.title)?.paper_id ?? "pending" } : r) });
      setSelected(new Set());
    } catch (e) { setErr(e); }
  }

  return (
    <div className="space-y-5">
      <Card>
        <form onSubmit={run} className="grid grid-cols-[1fr_200px_140px_140px_90px_auto] items-end gap-3">
          <label><Label hint='quote phrases: "inscribed square"'>Keywords</Label>
            <input className={inputCls} value={text} onChange={(e) => setText(e.target.value)} placeholder='e.g. "we conjecture" hamiltonian hypercube' /></label>
          <label><Label>Subject</Label>
            <select className={inputCls} value={subject} onChange={(e) => setSubject(e.target.value)}>
              {SUBJECTS.map((s) => <option key={s} value={s}>{s || "Any"}</option>)}
            </select></label>
          <label><Label>From</Label><input type="date" className={inputCls} value={from} onChange={(e) => setFrom(e.target.value)} /></label>
          <label><Label>To</Label><input type="date" className={inputCls} value={to} onChange={(e) => setTo(e.target.value)} /></label>
          <label><Label>Per source</Label><input type="number" min={1} max={100} className={inputCls} value={limit} onChange={(e) => setLimit(Number(e.target.value))} /></label>
          <Button variant="primary" type="submit" disabled={busy || sources.length === 0}>{busy ? "Searching…" : "Search"}</Button>
          <div className="col-span-6 flex flex-wrap items-center gap-4 text-[13px] text-ink-2">
            {SOURCES.map((s) => (
              <label key={s.key} className="flex items-center gap-1.5">
                <input type="checkbox" checked={sources.includes(s.key)} onChange={(e) => setSources(e.target.checked ? [...sources, s.key] : sources.filter((x) => x !== s.key))} />
                {s.label}
              </label>
            ))}
            <span className="text-xs text-ink-3">Results are merged across sources and de-duplicated by DOI, arXiv ID and normalized title.</span>
          </div>
        </form>
      </Card>
      <ErrorBox error={err} />
      {imported.length > 0 && (
        <Card title="Added to index">
          <ul className="space-y-2">{imported.map((x) => (
            <li key={x.paper_id} className="grid grid-cols-[1fr_380px] items-center gap-4 text-[13px]">
              <A href={`/papers/${x.paper_id}`}><MathText text={x.title} /></A>
              {x.job_id ? <JobStatus jobId={x.job_id} /> : <span className="text-xs text-ink-3">already processed</span>}
            </li>))}</ul>
        </Card>
      )}
      {res && (
        <>
          {Object.entries(res.source_errors).map(([s, m]) => (
            <Notice key={s} tone="warn"><strong>{s}</strong> returned an error and its results are missing: {m}
              {s === "semantic_scholar" && " — without SEMANTIC_SCHOLAR_API_KEY the shared rate limit is often exhausted."}</Notice>
          ))}
          <div className="flex items-center justify-between">
            <div className="text-sm text-ink-2">{res.results.length} result(s)</div>
            <Button variant="primary" disabled={selected.size === 0} onClick={importSelected}>Add {selected.size || ""} to index & process</Button>
          </div>
          {res.results.length === 0 ? <Empty title="No results">Try broader keywords or another subject.</Empty> : (
            <div className="divide-y divide-rule rounded-md border border-rule bg-surface">
              {res.results.map((r, i) => (
                <div key={i} className="grid grid-cols-[28px_1fr_150px] gap-3 px-4 py-3">
                  <input type="checkbox" className="mt-1" disabled={Boolean(r.indexed_paper_id)} checked={selected.has(i)}
                    onChange={(e) => { const s = new Set(selected); if (e.target.checked) s.add(i); else s.delete(i); setSelected(s); }} />
                  <div className="min-w-0">
                    <div className="font-serif text-[15px] text-ink"><MathText text={r.title} /></div>
                    <div className="mt-0.5 truncate text-xs text-ink-2">{r.authors.slice(0, 6).join(", ")}{r.authors.length > 6 ? " et al." : ""}</div>
                    {r.abstract && <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-ink-2"><MathText text={r.abstract} /></p>}
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-ink-3">
                      {r.merged_sources.map((s) => <Badge key={s}>{s}</Badge>)}
                      {r.arxiv_id && <A href={`https://arxiv.org/abs/${r.arxiv_id}`}>arXiv:{r.arxiv_id}</A>}
                      {r.doi && !r.doi.startsWith("10.48550") && <A href={`https://doi.org/${r.doi}`}>doi:{r.doi}</A>}
                      {r.categories.slice(0, 3).map((c) => <span key={c}>· {c}</span>)}
                    </div>
                  </div>
                  <div className="text-right text-xs text-ink-3">
                    <div>{r.published_date ?? "—"}</div>
                    <div className="mt-1">{r.pdf_url ? (r.is_open_access === false ? "PDF not open access" : "open PDF available") : "no PDF location"}</div>
                    {r.cited_by_count != null && <div className="mt-1">{r.cited_by_count} citations</div>}
                    {r.indexed_paper_id && r.indexed_paper_id !== "pending" && <div className="mt-1.5"><A href={`/papers/${r.indexed_paper_id}`}>indexed →</A></div>}
                    {r.indexed_paper_id === "pending" && <div className="mt-1.5 text-ok">added</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SubmitPanel() {
  const [ident, setIdent] = useState("");
  const [jobs, setJobs] = useState<{ id: string; ident: string }[]>([]);
  const [err, setErr] = useState<unknown>(null);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const r = await api.post<{ job_id: string }>("/api/papers/submit", { identifier: ident });
      setJobs([{ id: r.job_id, ident }, ...jobs]);
      setIdent("");
    } catch (e) { setErr(e); }
  }
  return (
    <div className="grid grid-cols-[1fr_340px] gap-6">
      <div className="space-y-4">
        <Card title="Submit a paper">
          <form onSubmit={submit} className="flex gap-2">
            <input className={inputCls} value={ident} onChange={(e) => setIdent(e.target.value)} placeholder="arXiv:1009.3304 · https://arxiv.org/abs/… · 10.1016/… · https://…/paper.pdf" />
            <Button variant="primary" type="submit" disabled={ident.trim().length < 3}>Submit</Button>
          </form>
          <div className="mt-3"><ErrorBox error={err} /></div>
        </Card>
        {jobs.map((j) => (
          <Card key={j.id} title={j.ident}>
            <JobStatus jobId={j.id} render={(job) => job.result?.paper_id && (
              <div className="text-[13px] text-ink-2">
                {job.result.created ? "New paper indexed" : "Paper was already indexed (de-duplicated)"} · {job.result.pages ?? 0} pages extracted
                {job.result.latex ? " · LaTeX source retrieved" : ""} · {job.result.new_candidates} new candidate passage(s)
                {job.result.error && <div className="mt-1 text-warn">{job.result.error}</div>}
                <div className="mt-2 flex gap-3"><A href={`/papers/${job.result.paper_id}`}>Open paper →</A>
                  <Link href="/discover?tab=review" className="text-accent hover:underline">Review candidates →</Link></div>
              </div>
            )} />
          </Card>
        ))}
      </div>
      <Card title="What happens">
        <ol className="list-decimal space-y-2 pl-4 text-[13px] leading-relaxed text-ink-2">
          <li>The identifier is resolved against arXiv, OpenAlex and Crossref, and matched against the index (DOI, arXiv ID, title) to avoid duplicates.</li>
          <li>An open-access PDF is downloaded when one is available, and its text is extracted page by page.</li>
          <li>For arXiv papers the LaTeX source is also retrieved, which preserves exact mathematical wording.</li>
          <li>A scanner flags passages that may state open problems. You review them, or ask the AI extraction agent to (needs an API key).</li>
        </ol>
      </Card>
    </div>
  );
}

function ReviewPanel({ items, reload }: { items: Candidate[] | null; reload: () => void }) {
  const [minScore, setMinScore] = useState(0);
  if (!items) return <Loading />;
  const shown = items.filter((c) => (c.score ?? 0) >= minScore);
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-[13px] text-ink-2">
        <span>{shown.length} pending passage(s). Heuristic passages are high-recall pattern matches; many are not open problems.</span>
        <label className="flex items-center gap-2">Minimum signal
          <select className={`${inputCls} w-24`} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))}>
            {[0, 0.5, 0.7, 0.9].map((v) => <option key={v} value={v}>{v}</option>)}
          </select></label>
      </div>
      {shown.length === 0 ? <Empty title="Nothing to review">Submit or import papers to scan them for open problems.</Empty>
        : shown.map((c) => <CandidateCard key={c.id} c={c} onChanged={reload} />)}
    </div>
  );
}

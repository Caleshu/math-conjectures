"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Candidate } from "@/lib/types";
import { ConjectureForm } from "./ConjectureForm";
import { MathText } from "./Math";
import { A, Badge, Button, ErrorBox, Loading, inputCls } from "./ui";

const KIND: Record<string, string> = {
  conjecture: "Conjecture", open_question: "Open question", open_problem: "Open problem", future_research: "Future research",
  unresolved_bound: "Unresolved bound", unsolved_special_case: "Special case", unknown: "Unclassified",
};

export function CandidateCard({ c, onChanged, showPaper = true, macros }: {
  c: Candidate; onChanged: () => void; showPaper?: boolean; macros?: Record<string, string>;
}) {
  const m = macros ?? c.paper_macros;
  const router = useRouter();
  const [mode, setMode] = useState<"view" | "record" | "reject">("view");
  const [full, setFull] = useState<Candidate | null>(null);
  const [note, setNote] = useState("");
  const [err, setErr] = useState<unknown>(null);
  const [showSrc, setShowSrc] = useState(false);
  const llm = c.detector.startsWith("llm:");
  const a = c.llm_assessment;

  async function openRecord() {
    setMode("record");
    setErr(null);
    try { setFull(await api.get<Candidate>(`/api/candidates/${c.id}`)); } catch (e) { setErr(e); }
  }
  async function reject() {
    try { await api.post(`/api/candidates/${c.id}/reject`, { note: note || null }); onChanged(); } catch (e) { setErr(e); }
  }

  return (
    <article className="rounded-md border border-rule bg-surface">
      <div className="flex items-start justify-between gap-4 px-4 pt-3">
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-ink-3">
          <Badge tone={llm ? "running" : undefined}>{llm ? "AI extraction" : "heuristic"}</Badge>
          <Badge>{KIND[c.kind] ?? c.kind}</Badge>
          <span>{c.origin === "latex" ? "LaTeX source" : c.origin === "pdf" ? "PDF text" : "abstract"}</span>
          {c.page_number && <span>· p. {c.page_number}</span>}
          {c.section && <span>· §&nbsp;{c.section}</span>}
          {c.score != null && <span>· signal {c.score.toFixed(2)}</span>}
          {c.review_status !== "pending" && <Badge tone={c.review_status}>{c.review_status}</Badge>}
        </div>
        {showPaper && c.paper_title && <A href={`/papers/${c.paper_id}`} className="shrink-0 text-xs">{c.paper_arxiv_id ? `arXiv:${c.paper_arxiv_id}` : "paper"} →</A>}
      </div>
      {showPaper && c.paper_title && <div className="px-4 pt-1 text-xs text-ink-2"><MathText text={c.paper_title} /></div>}
      {c.label && <div className="px-4 pt-2 font-serif text-[15px] text-ink">{c.label}</div>}
      <div className="px-4 py-2.5 text-[14px] leading-relaxed text-ink">
        <MathText text={c.passage.length > 1600 ? c.passage.slice(0, 1600) + " …" : c.passage} macros={m} />
      </div>
      {llm && a && (
        <div className="mx-4 mb-3 space-y-1 rounded-[5px] bg-paper px-3 py-2 text-xs text-ink-2">
          <div><strong className="text-ink">Normalized:</strong> <MathText text={a.normalized_statement ?? ""} macros={m} /></div>
          <div><strong className="text-ink">Agent rationale:</strong> {a.rationale}</div>
          <div>Wording found verbatim in source: <strong className={a.wording_verified_in_source ? "text-ok" : "text-bad"}>{a.wording_verified_in_source ? "yes" : "NO"}</strong> · confidence {a.confidence}</div>
        </div>
      )}
      {!llm && a?.llm_verdict === "rejected" && <div className="mx-4 mb-3 rounded-[5px] bg-paper px-3 py-2 text-xs text-ink-2">AI agent suggests rejecting: {a.reason}</div>}
      <div className="flex items-center justify-between gap-2 border-t border-rule px-4 py-2">
        <button className="text-xs text-ink-3 hover:text-ink" onClick={() => setShowSrc(!showSrc)}>{showSrc ? "Hide" : "Show"} raw source{c.trigger ? ` · trigger “${c.trigger}”` : ""}</button>
        {c.review_status === "pending" && mode === "view" && (
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" onClick={() => setMode("reject")}>Reject</Button>
            <Button size="sm" variant="primary" onClick={openRecord}>Record as conjecture…</Button>
          </div>
        )}
        {c.conjecture_id && <A href={`/conjectures/${c.conjecture_id}`} className="text-xs">View conjecture →</A>}
      </div>
      {showSrc && <pre className="mx-4 mb-3 max-h-72 overflow-auto whitespace-pre-wrap rounded-[5px] bg-paper p-3 font-mono text-[11px] text-ink-2">{c.passage}</pre>}
      {mode === "reject" && (
        <div className="flex gap-2 border-t border-rule px-4 py-3">
          <input className={inputCls} placeholder="Reason (optional), e.g. 'result proved in this paper', 'background mention of solved conjecture'" value={note} onChange={(e) => setNote(e.target.value)} />
          <Button size="sm" variant="ghost" onClick={() => setMode("view")}>Cancel</Button>
          <Button size="sm" variant="danger" onClick={reject}>Reject</Button>
        </div>
      )}
      {mode === "record" && (
        <div className="border-t border-rule px-4 py-4">
          {!full && !err && <Loading label="Loading passage" />}
          {full && <ConjectureForm candidate={full} macros={full.paper?.latex_macros} onCancel={() => setMode("view")}
            onCreated={(cj) => router.push(`/conjectures/${cj.slug}`)} />}
        </div>
      )}
      {err != null && <div className="px-4 pb-3"><ErrorBox error={err} /></div>}
    </article>
  );
}

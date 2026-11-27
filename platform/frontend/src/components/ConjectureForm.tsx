"use client";
// Records a conjecture. The original wording is shown read-only when it comes from a source
// passage: the normalized statement is a separate, editable field and never replaces it.
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Candidate, Conjecture, Meta } from "@/lib/types";
import { MathText } from "./Math";
import { Button, ErrorBox, Label, Notice, fieldLabel, inputCls } from "./ui";

type Def = { term: string; definition: string };

function initialFromCandidate(c?: Candidate) {
  const a = c?.llm_assessment && c.detector.startsWith("llm:") ? c.llm_assessment : null;
  return {
    title: a?.title ?? (c?.label?.replace(/\s*\[[^\]]*\]\s*$/, "") || ""),
    field: a?.field ?? "graph_theory",
    original: a?.original_wording || c?.passage || "",
    normalized: a?.normalized_statement ?? "",
    definitions: (a?.definitions as Def[] | undefined) ?? [],
    difficulty: a?.difficulty_guess ?? "",
    approaches: ((a?.potential_approaches as string[] | undefined) ?? []).join("\n"),
    known: ((a?.known_partial_results as { statement: string; location: string; is_computational: boolean }[] | undefined) ?? []),
    problem_type: a?.kind ?? (c?.kind === "conjecture" ? "conjecture" : c?.kind) ?? "conjecture",
  };
}

export function ConjectureForm({ candidate, macros, onCreated, onCancel }: {
  candidate?: Candidate; macros?: Record<string, string>; onCreated: (c: Conjecture) => void; onCancel: () => void;
}) {
  const { data: meta } = useApi<Meta>("/api/conjectures/meta");
  const init = initialFromCandidate(candidate);
  const [title, setTitle] = useState(init.title);
  const [field, setField] = useState(init.field);
  const [original, setOriginal] = useState(init.original);
  const [normalized, setNormalized] = useState(init.normalized);
  const [defs, setDefs] = useState<Def[]>(init.definitions);
  const [difficulty, setDifficulty] = useState(init.difficulty);
  const [approaches, setApproaches] = useState(init.approaches);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const fromSource = Boolean(candidate);
  const llm = candidate?.detector.startsWith("llm:");

  async function submit() {
    setBusy(true);
    setErr(null);
    try {
      const body = {
        title, field, problem_type: init.problem_type, original_statement: original, normalized_statement: normalized,
        definitions: defs.filter((d) => d.term.trim()),
        difficulty_estimate: difficulty || null,
        potential_approaches: approaches.split("\n").map((s) => s.trim()).filter(Boolean),
        known_results: init.known.map((k) => ({
          statement: k.statement, location: k.location, is_computational: k.is_computational,
          source_paper_id: candidate?.paper_id, citation: "source paper", reproduced: null,
        })),
      };
      const c = candidate
        ? await api.post<Conjecture>(`/api/candidates/${candidate.id}/accept`, body)
        : await api.post<Conjecture>("/api/conjectures", body);
      onCreated(c);
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {llm && <Notice>Pre-filled from the AI extraction agent ({candidate!.detector.slice(4)}).
        {candidate!.llm_assessment?.wording_verified_in_source === false && <strong> The quoted wording was not found verbatim in the source — check it.</strong>} Review every field before recording.</Notice>}
      <div className="grid grid-cols-[1fr_220px] gap-4">
        <label><Label>Title</Label><input className={inputCls} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Inscribed squares in Hamiltonian cycles of the hypercube" /></label>
        <label><Label>Field</Label>
          <select className={inputCls} value={field} onChange={(e) => setField(e.target.value)}>
            {(meta?.fields ?? [field]).map((f) => <option key={f} value={f}>{fieldLabel(f)}</option>)}
          </select>
        </label>
      </div>
      <div>
        <Label hint={fromSource ? "verbatim from the source — not editable" : "copy exactly from the source"}>Original wording</Label>
        {fromSource ? (
          <div className="rounded-[5px] border border-rule bg-paper px-3 py-2">
            <pre className="whitespace-pre-wrap font-mono text-[11.5px] text-ink-2">{original}</pre>
          </div>
        ) : (
          <textarea className={`${inputCls} font-mono`} rows={4} value={original} onChange={(e) => setOriginal(e.target.value)} />
        )}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <label className="block"><Label hint="LaTeX with $…$; precise, self-contained, quantifiers explicit">Normalized statement</Label>
          <textarea className={`${inputCls} font-mono`} rows={6} value={normalized} onChange={(e) => setNormalized(e.target.value)}
            placeholder="For every integer $n \ge 2$, every Hamiltonian cycle $H$ of $Q_n$ ..." />
        </label>
        <div><Label>Preview</Label>
          <div className="statement min-h-[8.5rem] rounded-r-[5px]">{normalized ? <MathText text={normalized} macros={macros} /> : <span className="text-sm text-ink-3">—</span>}</div>
        </div>
      </div>
      <div>
        <Label hint="term and definition, as used in the source">Definitions</Label>
        <div className="space-y-2">
          {defs.map((d, i) => (
            <div key={i} className="grid grid-cols-[200px_1fr_auto] gap-2">
              <input className={inputCls} value={d.term} placeholder="term" onChange={(e) => setDefs(defs.map((x, j) => j === i ? { ...x, term: e.target.value } : x))} />
              <input className={inputCls} value={d.definition} placeholder="definition (LaTeX allowed)" onChange={(e) => setDefs(defs.map((x, j) => j === i ? { ...x, definition: e.target.value } : x))} />
              <Button size="sm" variant="ghost" onClick={() => setDefs(defs.filter((_, j) => j !== i))}>Remove</Button>
            </div>
          ))}
          <Button size="sm" onClick={() => setDefs([...defs, { term: "", definition: "" }])}>Add definition</Button>
        </div>
      </div>
      <div className="grid grid-cols-[220px_1fr] gap-4">
        <label><Label hint="subjective">Difficulty estimate</Label>
          <select className={inputCls} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option value="">Not estimated</option>
            {(meta?.difficulties ?? []).map((d) => <option key={d} value={d}>{fieldLabel(d)}</option>)}
          </select>
        </label>
        <label><Label hint="one per line">Potential approaches</Label>
          <textarea className={inputCls} rows={2} value={approaches} onChange={(e) => setApproaches(e.target.value)} />
        </label>
      </div>
      {init.known.length > 0 && (
        <div className="text-xs text-ink-2">Will also record {init.known.length} partial result(s) stated in the source paper as known results (marked not reproduced).</div>
      )}
      <ErrorBox error={err} />
      <div className="flex justify-end gap-2 border-t border-rule pt-3">
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button variant="primary" disabled={busy || !title.trim() || !original.trim() || !normalized.trim()} onClick={submit}>
          {busy ? "Recording…" : "Record conjecture (status: UNVERIFIED)"}
        </Button>
      </div>
    </div>
  );
}

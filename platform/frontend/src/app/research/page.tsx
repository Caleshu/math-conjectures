"use client";
import { A, Card, Empty, ErrorBox, Loading, Notice, PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";

const AGENTS = [
  ["Mathematical Strategist", "Reductions, candidate lemmas, independent proof strategies, equivalent formulations."],
  ["Extremal Mathematician", "Counting arguments, inequalities, extremal bounds, structural and inductive arguments."],
  ["Construction & Counterexample Agent", "Small counterexamples, boundary cases, constructions, failures of proposed lemmas."],
  ["Computational Mathematician", "Writes and runs sandboxed programs (NetworkX, SymPy, OR-Tools CP-SAT) — uses the experiment system that already exists."],
  ["Literature Specialist", "Checks whether techniques and apparently novel arguments are already known."],
  ["Adversarial Proof Reviewer", "Assumes each proof is wrong: checks every inference, boundary case and gap. Independent of the proof’s author."],
];

export default function ResearchLab() {
  const { data, error, loading, reload } = useApi<{ items: any[]; orchestrator_available: boolean; note: string }>("/api/research/runs");
  return (
    <>
      <PageHeader eyebrow="Research engine" title="Research Lab" subtitle="Multi-agent investigation of verified open problems." />
      <ErrorBox error={error} onRetry={reload} />
      {loading && !data && <Loading />}
      {data && (
        <div className="space-y-6">
          {!data.orchestrator_available && (
            <Notice tone="warn">
              <strong>Not built yet.</strong> {data.note} Launching runs is deliberately unavailable rather than simulated. What exists now: the research-run, agent-task, claim and proof-attempt tables; the provider-neutral LLM layer with cost tracking and budget limits; and the sandboxed{" "}
              <A href="/experiments">experiment system</A> the Computational Mathematician will use.
            </Notice>
          )}
          <Card title="Research runs">{data.items.length === 0 ? <Empty title="No research runs" /> : <ul>{data.items.map((r) => <li key={r.id}>{r.status}</li>)}</ul>}</Card>
          <Card title="Planned agent team (Milestone 4)">
            <ul className="divide-y divide-rule">
              {AGENTS.map(([n, d]) => <li key={n} className="grid grid-cols-[260px_1fr] gap-4 py-2.5 text-[13px]"><span className="font-medium text-ink">{n}</span><span className="text-ink-2">{d}</span></li>)}
            </ul>
            <p className="mt-3 text-xs leading-relaxed text-ink-3">Design constraints carried into the orchestrator: independent first passes before agents see each other’s work; no agent’s conclusion treated as established; every claim keeps its author, evidence and verification status; hard limits on iterations, model calls, tokens, runtime and compute; resumable checkpoints.</p>
          </Card>
        </div>
      )}
    </>
  );
}

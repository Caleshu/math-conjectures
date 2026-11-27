"use client";
import { useEffect, useState } from "react";
import { Badge, Button, Card, ErrorBox, KV, Loading, Notice, PageHeader, inputCls } from "@/components/ui";
import { API_URL } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { getSupabase, supabaseEnabled } from "@/lib/supabase";

type Settings = {
  integrations: { name: string; key: string; available: boolean; detail: string }[];
  llm: { available_providers: string[]; default_provider: string; anthropic_model: string; claude_code_model: string; openai_model: string; budget_usd: number };
  sandbox: { default_timeout_s: number; max_timeout_s: number; default_memory_mb: number };
  auth: { require_auth: boolean; supabase_configured: boolean };
  worker: { embedded: boolean };
};
type Usage = {
  llm_total_usd: number; llm_budget_usd: number;
  llm: { provider: string; model: string; purpose: string; calls: number; input_tokens: number; output_tokens: number; cost_usd: number }[];
  sources: { source: string; requests: number; errors: number }[];
};

export default function SettingsPage() {
  const { data: s, error, loading, reload } = useApi<Settings>("/api/settings");
  const { data: u } = useApi<Usage>("/api/usage");
  return (
    <>
      <PageHeader eyebrow="Configuration" title="Settings" subtitle={<>Integrations are configured with environment variables on the backend (see <code>.env.example</code>). Secrets never reach the browser.</>} />
      <ErrorBox error={error} onRetry={reload} />
      {loading && !s && <Loading />}
      {s && (
        <div className="grid grid-cols-[1fr_380px] gap-6">
          <div className="space-y-5">
            <Card title="Integrations" pad={false}>
              <ul className="divide-y divide-rule">{s.integrations.map((i) => (
                <li key={i.key} className="grid grid-cols-[130px_104px_1fr] items-center gap-3 px-4 py-2.5 text-[13px]">
                  <span className="font-medium text-ink">{i.name}</span>
                  <span>{i.available ? <Badge tone="succeeded">available</Badge> : <Badge tone="pending">not configured</Badge>}</span>
                  <span className="break-words text-ink-2">{i.detail}</span>
                </li>))}</ul>
            </Card>
            <Card title="Usage and cost">
              {u ? (
                <>
                  <div className="mb-3 text-[13px] text-ink-2">LLM spend: <strong className="text-ink tabular">${u.llm_total_usd.toFixed(4)}</strong> of ${u.llm_budget_usd.toFixed(2)} budget (LLM_BUDGET_USD). Calls are refused once the budget is reached. Claude Code (subscription) calls are recorded at $0: they use your plan's limits, not API billing.</div>
                  {u.llm.length === 0 ? <p className="text-xs text-ink-3">No model calls recorded.</p> : (
                    <table className="mb-4 w-full text-[12.5px] tabular"><thead className="text-left text-xs text-ink-3"><tr><th>model</th><th>purpose</th><th>calls</th><th>in</th><th>out</th><th>USD</th></tr></thead>
                      <tbody>{u.llm.map((r, i) => <tr key={i}><td>{r.model}</td><td>{r.purpose}</td><td>{r.calls}</td><td>{r.input_tokens}</td><td>{r.output_tokens}</td><td>{r.cost_usd.toFixed(4)}</td></tr>)}</tbody></table>
                  )}
                  <div className="text-xs font-medium text-ink-2">Literature API requests</div>
                  <table className="mt-1 w-full text-[12.5px] tabular"><tbody>{u.sources.map((r) => <tr key={r.source}><td className="py-0.5">{r.source}</td><td>{r.requests} requests</td><td className={r.errors ? "text-bad" : "text-ink-3"}>{r.errors} errors</td></tr>)}</tbody></table>
                </>
              ) : <Loading />}
            </Card>
          </div>
          <div className="space-y-5">
            <Card title="AI models">
              <dl>
                <KV k="Default provider">{s.llm.default_provider}</KV>
                <KV k="Anthropic model">{s.llm.anthropic_model}</KV>
                <KV k="Claude Code model">{s.llm.claude_code_model}</KV>
                <KV k="OpenAI model">{s.llm.openai_model}</KV>
                <KV k="Configured">{s.llm.available_providers.join(", ") || "none"}</KV>
              </dl>
            </Card>
            <Card title="Sandbox limits">
              <dl>
                <KV k="Default timeout">{s.sandbox.default_timeout_s} s</KV>
                <KV k="Max timeout">{s.sandbox.max_timeout_s} s</KV>
                <KV k="Default memory">{s.sandbox.default_memory_mb} MB</KV>
                <KV k="Job worker">{s.worker.embedded ? "embedded in API process" : "separate process"}</KV>
              </dl>
            </Card>
            <AuthCard requireAuth={s.auth.require_auth} />
            <div className="text-xs text-ink-3">API: {API_URL} · <a className="text-accent" href={`${API_URL}/docs`} target="_blank" rel="noreferrer">OpenAPI docs</a></div>
          </div>
        </div>
      )}
    </>
  );
}

function AuthCard({ requireAuth }: { requireAuth: boolean }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const sb = getSupabase();
  useEffect(() => { sb?.auth.getSession().then(({ data }) => setUser(data.session?.user.email ?? null)); }, [sb]);
  if (!supabaseEnabled()) {
    return (
      <Card title="Authentication">
        <Notice>{requireAuth ? "The backend requires auth but this frontend has no Supabase configuration." : "Local single-user mode."} To enable Supabase Auth, set <code>NEXT_PUBLIC_SUPABASE_URL</code> and <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code> here and <code>SUPABASE_URL</code> / <code>REQUIRE_AUTH=true</code> on the backend.</Notice>
      </Card>
    );
  }
  async function signIn() {
    setErr(null);
    const { data, error } = await sb!.auth.signInWithPassword({ email, password });
    if (error) setErr(error); else setUser(data.user?.email ?? null);
  }
  return (
    <Card title="Authentication">
      {user ? (
        <div className="flex items-center justify-between text-[13px]"><span>Signed in as <strong>{user}</strong></span>
          <Button size="sm" onClick={async () => { await sb!.auth.signOut(); setUser(null); }}>Sign out</Button></div>
      ) : (
        <div className="space-y-2">
          <input className={inputCls} placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className={inputCls} type="password" placeholder="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <ErrorBox error={err} />
          <Button variant="primary" onClick={signIn} disabled={!email || !password}>Sign in with Supabase</Button>
        </div>
      )}
    </Card>
  );
}

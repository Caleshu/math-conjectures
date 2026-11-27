"use client";
import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function PageHeader({ title, subtitle, actions, eyebrow }: {
  title: ReactNode; subtitle?: ReactNode; actions?: ReactNode; eyebrow?: ReactNode;
}) {
  return (
    <header className="flex items-end justify-between gap-6 border-b border-rule pb-5 mb-6">
      <div className="min-w-0">
        {eyebrow && <div className="text-xs uppercase tracking-[0.14em] text-ink-3 mb-1.5">{eyebrow}</div>}
        <h1 className="font-serif text-[1.75rem] leading-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm text-ink-2 max-w-3xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </header>
  );
}

export function Card({ children, className = "", title, actions, pad = true }: {
  children: ReactNode; className?: string; title?: ReactNode; actions?: ReactNode; pad?: boolean;
}) {
  return (
    <section className={`rounded-md border border-rule bg-surface ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between gap-3 border-b border-rule px-4 py-2.5">
          <h2 className="text-[13px] font-semibold tracking-wide text-ink">{title}</h2>
          {actions}
        </div>
      )}
      <div className={pad ? "p-4" : ""}>{children}</div>
    </section>
  );
}

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger"; size?: "sm" | "md" };

export function Button({ variant = "secondary", size = "md", className = "", ...p }: BtnProps) {
  const base = "inline-flex items-center justify-center gap-1.5 rounded-[5px] font-medium transition-colors disabled:opacity-45 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent";
  const sizes = { sm: "h-7 px-2.5 text-xs", md: "h-8.5 px-3.5 text-[13px]" };
  const variants = {
    primary: "bg-accent text-white hover:bg-[#223d66]",
    secondary: "border border-rule-strong bg-surface text-ink hover:bg-paper",
    ghost: "text-ink-2 hover:bg-paper hover:text-ink",
    danger: "border border-bad/30 bg-surface text-bad hover:bg-bad-soft",
  };
  return <button className={`${base} ${sizes[size]} ${variants[variant]} ${className}`} {...p} />;
}

const STATUS_STYLE: Record<string, string> = {
  VERIFIED_OPEN: "bg-ok-soft text-ok border-ok/25",
  LIKELY_OPEN: "bg-accent-soft text-accent border-accent/25",
  UNVERIFIED: "bg-warn-soft text-warn border-warn/25",
  SOLVED: "bg-[#eeeaf6] text-[#4b3b80] border-[#4b3b80]/20",
  DISPROVED: "bg-bad-soft text-bad border-bad/25",
  SUPERSEDED: "bg-[#efefef] text-ink-2 border-rule-strong",
  succeeded: "bg-ok-soft text-ok border-ok/25",
  running: "bg-accent-soft text-accent border-accent/25",
  queued: "bg-[#f1f0ec] text-ink-2 border-rule-strong",
  failed: "bg-bad-soft text-bad border-bad/25",
  completed: "bg-ok-soft text-ok border-ok/25",
  cancelling: "bg-warn-soft text-warn border-warn/25",
  unverified: "bg-[#f1f0ec] text-ink-2 border-rule-strong",
  no_issues_found: "bg-accent-soft text-accent border-accent/25",
  review_passed: "bg-accent-soft text-accent border-accent/25",
  needs_work: "bg-warn-soft text-warn border-warn/25",
  review_needs_work: "bg-warn-soft text-warn border-warn/25",
  disputed: "bg-bad-soft text-bad border-bad/25",
  review_unsupported: "bg-bad-soft text-bad border-bad/25",
  review_flawed: "bg-bad-soft text-bad border-bad/25",
  refuted: "bg-bad-soft text-bad border-bad/25",
  review_false: "bg-bad-soft text-bad border-bad/25",
  awaiting_review: "bg-[#f1f0ec] text-ink-2 border-rule-strong",
  timeout: "bg-bad-soft text-bad border-bad/25",
  cancelled: "bg-[#efefef] text-ink-3 border-rule-strong",
  pending: "bg-warn-soft text-warn border-warn/25",
  accepted: "bg-ok-soft text-ok border-ok/25",
  rejected: "bg-[#efefef] text-ink-3 border-rule-strong",
};

export function Badge({ children, tone, title }: { children: ReactNode; tone?: string; title?: string }) {
  const cls = (tone && STATUS_STYLE[tone]) || "bg-[#f3f2ee] text-ink-2 border-rule";
  return (
    <span title={title} className={`inline-flex items-center whitespace-nowrap rounded-[4px] border px-1.5 py-[1px] text-[11px] font-medium tracking-wide ${cls}`}>
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={status}>{status.replace(/_/g, " ")}</Badge>;
}

export function Spinner({ className = "" }: { className?: string }) {
  return <span className={`inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-ink-3/30 border-t-ink-2 ${className}`} />;
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return <div className="flex items-center gap-2 py-10 text-sm text-ink-3"><Spinner /> {label}…</div>;
}

export function ErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  if (!error) return null;
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="flex items-start justify-between gap-4 rounded-md border border-bad/25 bg-bad-soft px-3.5 py-2.5 text-[13px] text-bad">
      <span>{msg}</span>
      {onRetry && <button onClick={onRetry} className="shrink-0 underline underline-offset-2">Retry</button>}
    </div>
  );
}

export function Notice({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "warn" | "ok" }) {
  const c = { info: "border-accent/20 bg-accent-soft text-[#24426d]", warn: "border-warn/25 bg-warn-soft text-warn", ok: "border-ok/25 bg-ok-soft text-ok" }[tone];
  return <div className={`rounded-md border px-3.5 py-2.5 text-[13px] leading-relaxed ${c}`}>{children}</div>;
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-rule-strong px-6 py-10 text-center">
      <div className="font-serif text-lg text-ink">{title}</div>
      {children && <div className="mx-auto mt-2 max-w-lg text-sm text-ink-2">{children}</div>}
    </div>
  );
}

export function Tabs<T extends string>({ tabs, value, onChange }: {
  tabs: { key: T; label: string; count?: number }[]; value: T; onChange: (k: T) => void;
}) {
  return (
    <div className="mb-5 flex gap-0.5 overflow-x-auto border-b border-rule">
      {tabs.map((t) => (
        <button key={t.key} onClick={() => onChange(t.key)}
          className={`-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-[13px] transition-colors ${value === t.key ? "border-accent font-medium text-ink" : "border-transparent text-ink-2 hover:text-ink"}`}>
          {t.label}{t.count !== undefined && <span className="ml-1.5 text-ink-3 tabular">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

export function Label({ children, hint }: { children: ReactNode; hint?: ReactNode }) {
  return (
    <span className="mb-1 block text-xs font-medium text-ink-2">
      {children}{hint && <span className="ml-1.5 font-normal text-ink-3">{hint}</span>}
    </span>
  );
}

export const inputCls = "w-full rounded-[5px] border border-rule-strong bg-surface px-2.5 py-1.5 text-[13px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15";

export function KV({ k, children }: { k: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[130px_1fr] gap-3 py-1.5 text-[13px]">
      <dt className="text-ink-3">{k}</dt>
      <dd className="min-w-0 break-words text-ink">{children}</dd>
    </div>
  );
}

export function fmtDate(s?: string | null, withTime = false): string {
  if (!s) return "—";
  const d = new Date(s);
  if (isNaN(d.getTime())) return s;
  return withTime
    ? d.toLocaleString(undefined, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
    : d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function fieldLabel(f: string) {
  return f.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

export function A({ href, children, className = "" }: { href: string; children: ReactNode; className?: string }) {
  const ext = href.startsWith("http");
  if (ext) return <a href={href} target="_blank" rel="noreferrer" className={`text-accent hover:underline underline-offset-2 ${className}`}>{children}</a>;
  return <Link href={href} className={`text-accent hover:underline underline-offset-2 ${className}`}>{children}</Link>;
}

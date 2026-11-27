"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApi } from "@/lib/hooks";

const NAV = [
  { href: "/", label: "Dashboard", glyph: "◳" },
  { href: "/discover", label: "Discover Problems", glyph: "⌕" },
  { href: "/conjectures", label: "Conjecture Library", glyph: "∃" },
  { href: "/research", label: "Research Lab", glyph: "∴" },
  { href: "/papers", label: "Papers", glyph: "¶" },
  { href: "/experiments", label: "Experiments", glyph: "⊢" },
  { href: "/settings", label: "Settings", glyph: "⚙" },
];

type Health = { ok: boolean };

export function Sidebar() {
  const path = usePathname();
  const { data, error } = useApi<Health>("/health", { pollMs: 15000, shouldPoll: () => true });
  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-rule bg-[#f6f4ef]">
      <div className="px-5 pb-5 pt-6">
        <Link href="/" className="block">
          <div className="font-serif text-[1.3rem] leading-none tracking-tight text-ink">MathResearchLab</div>
          <div className="mt-1.5 text-[11px] uppercase tracking-[0.16em] text-ink-3">open problems · evidence · computation</div>
        </Link>
      </div>
      <nav className="flex-1 space-y-0.5 px-2.5">
        {NAV.map((n) => {
          const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
          return (
            <Link key={n.href} href={n.href}
              className={`flex items-center gap-2.5 rounded-[5px] px-2.5 py-[7px] text-[13px] transition-colors ${active ? "bg-surface font-medium text-ink shadow-[0_0_0_1px_var(--color-rule)]" : "text-ink-2 hover:bg-surface/60 hover:text-ink"}`}>
              <span className={`w-4 text-center font-serif text-[15px] ${active ? "text-accent" : "text-ink-3"}`}>{n.glyph}</span>
              {n.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-rule px-5 py-3.5 text-[11px] text-ink-3">
        <span className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full align-middle ${data?.ok ? "bg-ok" : error ? "bg-bad" : "bg-ink-3"}`} />
        {data?.ok ? "API connected" : error ? "API unreachable" : "Connecting…"}
      </div>
    </aside>
  );
}

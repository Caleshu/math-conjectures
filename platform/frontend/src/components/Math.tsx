"use client";
// Renders text containing LaTeX math ($...$, $$...$$, \(...\), \[...\]) with KaTeX.
// Paper-specific macros (parsed from the paper's preamble by the backend) can be supplied so that
// original wording such as "$\hyp{n}$" renders with the author's notation.
import katex from "katex";
import { useMemo } from "react";

type Seg = { kind: "text" | "inline" | "display"; value: string };

const MATH_RE = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$((?:\\\$|[^$])+?)\$/g;

function split(src: string): Seg[] {
  const out: Seg[] = [];
  let last = 0;
  for (const m of src.matchAll(MATH_RE)) {
    const i = m.index ?? 0;
    if (i > last) out.push({ kind: "text", value: src.slice(last, i) });
    if (m[1] !== undefined || m[2] !== undefined) out.push({ kind: "display", value: (m[1] ?? m[2])! });
    else out.push({ kind: "inline", value: (m[3] ?? m[4])! });
    last = i + m[0].length;
  }
  if (last < src.length) out.push({ kind: "text", value: src.slice(last) });
  return out;
}

// Light clean-up of LaTeX text-mode markup outside math so source passages read naturally.
function cleanText(t: string): string {
  return t
    .replace(/(?<!\\)%[^\n]*/g, "")
    .replace(/\\begin\{(itemize|enumerate)\}|\\end\{(itemize|enumerate)\}/g, "\n")
    .replace(/\\item\s*/g, "\n• ")
    .replace(/\\(label|ref|eqref|cite)\{([^}]*)\}/g, (_, cmd, arg) => (cmd === "label" ? "" : `[${arg}]`))
    .replace(/\\(emph|textit|textbf|em|it|bf)\s*\{([^{}]*)\}/g, "$2")
    .replace(/\{\\(em|it|bf)\s+([^{}]*)\}/g, "$2")
    .replace(/\\begin\{([a-zA-Z*]+)\}(\[[^\]]*\])?/g, (_, env, opt) => {
      const head = `${env[0].toUpperCase()}${env.slice(1)}${opt ? " (" + opt.slice(1, -1).replace(/\.\s*$/, "") + ")" : ""}`;
      return `${head}. `;
    })
    .replace(/\\end\{[a-zA-Z*]+\}/g, "")
    .replace(/~/g, " ")
    .replace(/\\(noindent|smallskip|medskip|bigskip|par)\b/g, "")
    .replace(/\\"([a-zA-Z])/g, "$1̈")
    .replace(/``|''/g, "\"");
}

export function MathText({ text, macros, className, raw = false }: {
  text: string; macros?: Record<string, string>; className?: string; raw?: boolean;
}) {
  const html = useMemo(() => {
    const segs = split(text ?? "");
    const m = { ...(macros ?? {}) };
    return segs.map((s) => {
      if (s.kind === "text") {
        const t = raw ? s.value : cleanText(s.value);
        return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br/>");
      }
      try {
        return katex.renderToString(s.value, {
          displayMode: s.kind === "display", throwOnError: false, macros: m, strict: "ignore", trust: false,
        });
      } catch {
        return `<code>${s.value.replace(/</g, "&lt;")}</code>`;
      }
    }).join("");
  }, [text, macros, raw]);
  return <span className={`math-display ${className ?? ""}`} dangerouslySetInnerHTML={{ __html: html }} />;
}

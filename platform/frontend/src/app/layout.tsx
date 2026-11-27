import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Source_Serif_4 } from "next/font/google";
import { Sidebar } from "@/components/Sidebar";
import { themeScript } from "@/lib/theme";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const serif = Source_Serif_4({ subsets: ["latin"], variable: "--font-serif" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "MathResearchLab",
  description: "Discovery, verification and computational investigation of open mathematical problems.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${serif.variable} ${mono.variable}`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="font-sans text-ink" suppressHydrationWarning>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="min-w-0 flex-1 px-10 pb-16 pt-8 print:p-0">
            <div className="mx-auto max-w-[1180px]">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}

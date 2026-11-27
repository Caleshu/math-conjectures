"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { themeStorageKey } from "@/lib/theme";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.dataset.theme === "dark");
  }, []);

  function toggle() {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    setDark(next === "dark");
    try { localStorage.setItem(themeStorageKey, next); } catch {
      // Still allow switching for the current page if storage is blocked.
    }
  }

  return (
    <Button type="button" variant="ghost" className="w-full !justify-start" aria-pressed={dark} onClick={toggle}>
      <span className="w-4 text-center" aria-hidden="true">{dark ? "☾" : "☀"}</span>
      Dark mode
    </Button>
  );
}

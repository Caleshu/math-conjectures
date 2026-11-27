export const themeStorageKey = "mathresearchlab-theme";
export const darkPreference = "(prefers-color-scheme: dark)";

// Apply before first paint. If storage is denied, still respect the OS setting.
export const themeScript = `(() => {
  let saved;
  try { saved = localStorage.getItem(${JSON.stringify(themeStorageKey)}); } catch {}
  document.documentElement.dataset.theme = saved === "dark" || saved === "light"
    ? saved
    : matchMedia(${JSON.stringify(darkPreference)}).matches ? "dark" : "light";
})();`;

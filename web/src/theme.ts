import { useEffect, useState } from "react";

export type Theme = "dark" | "light";

export function readTheme(): Theme {
  try {
    const t = localStorage.getItem("quantlab-theme");
    if (t === "dark" || t === "light") return t;
  } catch { /* storage pode não existir */ }
  return "dark";
}

export function applyTheme(t: Theme) {
  document.documentElement.setAttribute("data-theme", t);
  try { localStorage.setItem("quantlab-theme", t); } catch { /* ignora */ }
}

export function useTheme(): [Theme, (t: Theme) => void] {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useEffect(() => { applyTheme(theme); }, [theme]);
  return [theme, setTheme];
}

/** Lê os tokens de cor do CSS para as bibliotecas de gráfico (que não entendem var()). */
export function cssColors() {
  const s = getComputedStyle(document.documentElement);
  const g = (n: string) => s.getPropertyValue(n).trim();
  return {
    surface: g("--surface"), ink: g("--ink"), ink2: g("--ink-2"), muted: g("--muted"), grid: g("--grid"), axis: g("--axis"),
    s1: g("--s1"), s2: g("--s2"), s3: g("--s3"), s4: g("--s4"), s5: g("--s5"), s6: g("--s6"), s7: g("--s7"), s8: g("--s8"),
    good: g("--good"), warn: g("--warn"), critical: g("--critical"), divMid: g("--div-mid"), divPos: g("--div-pos"), divNeg: g("--div-neg"),
  };
}
export type Colors = ReturnType<typeof cssColors>;

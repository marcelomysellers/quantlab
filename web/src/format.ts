const nf = (d: number) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
export const num = (x: number | null | undefined, d = 2) => (x == null || Number.isNaN(x) ? "–" : nf(d).format(x));
export const pct = (x: number | null | undefined, d = 1) => (x == null || Number.isNaN(x) ? "–" : nf(d).format(x * 100) + "%");
export const signed = (x: number | null | undefined, d = 2) => (x == null ? "–" : (x > 0 ? "+" : "") + nf(d).format(x));
export const int = (x: number | null | undefined) => (x == null ? "–" : new Intl.NumberFormat("pt-BR").format(Math.round(x)));
export const dateS = (t: number, intraday = false) => {
  const d = new Date(t * 1000);
  const base = d.toLocaleDateString("pt-BR", { timeZone: "UTC", day: "2-digit", month: "2-digit", year: "numeric" });
  return intraday ? base + " " + d.toLocaleTimeString("pt-BR", { timeZone: "UTC", hour: "2-digit", minute: "2-digit" }) : base;
};
export const paramsS = (p: Record<string, unknown> | null | undefined) =>
  p ? Object.entries(p).map(([k, v]) => `${k}=${v === null ? "–" : String(v)}`).join(" · ") : "–";
export const TF_LABEL: Record<string, string> = { "1m": "1 min", "5m": "5 min", "15m": "15 min", "30m": "30 min", "1h": "1 hora", "4h": "4 horas", "1d": "diário" };
export const VERDICT_LABEL: Record<string, string> = { aprovada: "aprovada", promissora: "promissora", reprovada: "reprovada", referencia: "referência" };
export const cls = (x: number | null | undefined) => (x == null ? "" : x > 0 ? "pos" : x < 0 ? "neg" : "");
/** Custos pagos como fração do patrimônio: % até 100%, depois múltiplos. */
export const cost = (x: number | null | undefined) => (x == null ? "–" : x < 1 ? pct(x, 0) : num(x, 1) + "×");

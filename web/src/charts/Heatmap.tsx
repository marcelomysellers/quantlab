import { cssColors } from "../theme";

function hexToRgb(h: string) { const s = h.replace("#", ""); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16)); }
function mix(a: string, b: string, t: number) {
  const A = hexToRgb(a), B = hexToRgb(b);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(",")})`;
}
function luminance(rgb: string) {
  const m = rgb.match(/\d+/g)!.map(Number).map((v) => { const c = v / 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2];
}

/** Mapa de calor divergente: azul (positivo) · cinza neutro (zero) · vermelho (negativo). */
export function Heatmap({ rows, cols, value, format, vmax, colLabel, themeKey, onCell }:
  { rows: { id: string; label: string }[]; cols: string[]; value: (r: string, c: string) => number | null; format: (v: number) => string;
    vmax: number; colLabel: (c: string) => string; themeKey: string; onCell?: (r: string, c: string) => void }) {
  const c = cssColors();
  void themeKey;
  const bg = (v: number | null) => {
    if (v == null) return "transparent";
    const t = Math.min(Math.abs(v) / vmax, 1);
    return v >= 0 ? mix(c.divMid, c.divPos, t) : mix(c.divMid, c.divNeg, t);
  };
  return (
    <div className="heat" style={{ gridTemplateColumns: `max-content repeat(${cols.length}, 1fr)` }} role="table">
      <div className="hhead" />
      {cols.map((col) => <div key={col} className="hhead" role="columnheader">{colLabel(col)}</div>)}
      {rows.map((r) => (
        <>
          <div key={r.id + "_l"} className="hrow" role="rowheader">{r.label}</div>
          {cols.map((col) => {
            const v = value(r.id, col);
            const b = bg(v);
            const ink = v == null ? "var(--muted)" : luminance(b) > 0.35 ? "#0b0b0b" : "#ffffff";
            return (
              <div key={r.id + col} className="hcell" role="cell" style={{ background: b, color: ink, cursor: onCell && v != null ? "pointer" : "default" }}
                title={v == null ? "não roda neste timeframe" : `${r.label} · ${colLabel(col)}: ${format(v)}`}
                onClick={() => v != null && onCell?.(r.id, col)}>
                {v == null ? "–" : format(v)}
              </div>
            );
          })}
        </>
      ))}
    </div>
  );
}

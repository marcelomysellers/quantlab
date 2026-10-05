import { useMemo, useState } from "react";
import { num } from "../format";

/** Barra com ponta arredondada (4px) e base reta, crescendo a partir da linha-base. */
function barPath(x: number, y0: number, y1: number, w: number, r = 4) {
  const top = Math.min(y0, y1), bottom = Math.max(y0, y1), h = bottom - top;
  const rr = Math.min(r, h / 2, w / 2);
  if (h <= 0.5) return `M${x},${y0}h${w}`;
  if (y1 < y0) { // positiva: ponta em cima
    return `M${x},${bottom}V${top + rr}a${rr},${rr} 0 0 1 ${rr},-${rr}h${w - 2 * rr}a${rr},${rr} 0 0 1 ${rr},${rr}V${bottom}Z`;
  }
  return `M${x},${top}V${bottom - rr}a${rr},${rr} 0 0 0 ${rr},${rr}h${w - 2 * rr}a${rr},${rr} 0 0 0 ${rr},-${rr}V${top}Z`;
}

/** Histograma de uma distribuição (nulo aleatório, estresse) com marcador do valor real. */
export function Histogram({ values, marker, markerLabel, bins = 24, width = 460, height = 170, xLabel }:
  { values: number[]; marker: number; markerLabel: string; bins?: number; width?: number; height?: number; xLabel: string }) {
  const [hov, setHov] = useState<number | null>(null);
  const m = useMemo(() => {
    if (values.length === 0) return null;
    const lo = Math.min(...values, marker), hi = Math.max(...values, marker);
    const span = hi - lo || 1;
    const edges = Array.from({ length: bins + 1 }, (_, i) => lo + (span * i) / bins);
    const counts = new Array(bins).fill(0);
    for (const v of values) { let b = Math.floor(((v - lo) / span) * bins); if (b >= bins) b = bins - 1; counts[b]++; }
    return { lo, hi, span, edges, counts, max: Math.max(...counts) };
  }, [values, marker, bins]);
  if (!m) return <div className="empty">sem simulações</div>;
  const padL = 8, padR = 8, padT = 18, padB = 28;
  const W = width - padL - padR, H = height - padT - padB;
  const x = (v: number) => padL + ((v - m.lo) / m.span) * W;
  const bw = W / bins;
  const y = (cnt: number) => padT + H - (cnt / m.max) * H;
  const pctBelow = values.filter((v) => v < marker).length / values.length;
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ maxWidth: width, display: "block" }} role="img" aria-label={`${xLabel}: distribuição de ${values.length} simulações`}>
      {m.counts.map((cnt, i) => (
        <path key={i} d={barPath(padL + i * bw + 1, padT + H, y(cnt), Math.max(bw - 2, 1))} fill="var(--muted)" opacity={hov === i ? 0.9 : 0.55}
          onMouseEnter={() => setHov(i)} onMouseLeave={() => setHov(null)} />
      ))}
      <line x1={padL} x2={padL + W} y1={padT + H} y2={padT + H} stroke="var(--axis)" strokeWidth={1} />
      <line x1={x(marker)} x2={x(marker)} y1={padT - 4} y2={padT + H} stroke="var(--s1)" strokeWidth={2} />
      <text x={Math.min(x(marker) + 6, width - 120)} y={padT + 6} fontSize={11} fill="var(--ink)">{markerLabel} {num(marker, 2)}</text>
      <text x={padL} y={height - 8} fontSize={11} fill="var(--muted)">{num(m.lo, 1)}</text>
      <text x={padL + W / 2} y={height - 8} fontSize={11} fill="var(--muted)" textAnchor="middle">{xLabel}</text>
      <text x={padL + W} y={height - 8} fontSize={11} fill="var(--muted)" textAnchor="end">{num(m.hi, 1)}</text>
      {hov != null && (
        <text x={padL + W} y={padT + 6} fontSize={11} fill="var(--ink-2)" textAnchor="end">
          {num(m.edges[hov], 2)} a {num(m.edges[hov + 1], 2)}: {m.counts[hov]} sims
        </text>
      )}
      <title>{`${Math.round(pctBelow * 100)}% das simulações ficam abaixo do valor real`}</title>
    </svg>
  );
}

/** Barras agrupadas por janela (ex.: Sharpe dentro vs fora da amostra). */
export function GroupedBars({ groups, series, width = 560, height = 200, format = (v: number) => num(v, 2) }:
  { groups: string[]; series: { label: string; color: string; values: number[] }[]; width?: number; height?: number; format?: (v: number) => string }) {
  const [hov, setHov] = useState<{ g: number; s: number } | null>(null);
  const all = series.flatMap((s) => s.values).filter((v) => Number.isFinite(v));
  const lo = Math.min(0, ...all), hi = Math.max(0, ...all);
  const span = hi - lo || 1;
  const padL = 36, padR = 8, padT = 10, padB = 26;
  const W = width - padL - padR, H = height - padT - padB;
  const gw = W / Math.max(groups.length, 1);
  const bw = Math.min(24, (gw - 8) / series.length - 2);
  const y = (v: number) => padT + H - ((v - lo) / span) * H;
  const y0 = y(0);
  const ticks = [lo, 0, hi].filter((v, i, a) => a.indexOf(v) === i);
  return (
    <div>
      <div className="legend">
        {series.map((s) => <span key={s.label} className="legend-item"><i className="swatch" style={{ background: s.color }} />{s.label}
          {hov && <b>{format(s.values[hov.g])}</b>}</span>)}
        {hov && <span className="legend-item muted">{groups[hov.g]}</span>}
      </div>
      <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ maxWidth: width, display: "block" }} role="img">
        {ticks.map((t) => <g key={t}><line x1={padL} x2={padL + W} y1={y(t)} y2={y(t)} stroke={t === 0 ? "var(--axis)" : "var(--grid)"} strokeWidth={1} />
          <text x={padL - 6} y={y(t) + 4} fontSize={10} fill="var(--muted)" textAnchor="end">{format(t)}</text></g>)}
        {groups.map((g, gi) => (
          <g key={g}>
            {series.map((s, si) => {
              const v = s.values[gi] ?? 0;
              const x = padL + gi * gw + (gw - series.length * (bw + 2)) / 2 + si * (bw + 2);
              return <path key={si} d={barPath(x, y0, y(v), bw)} fill={s.color} opacity={hov && (hov.g !== gi) ? 0.45 : 1}
                onMouseEnter={() => setHov({ g: gi, s: si })} onMouseLeave={() => setHov(null)} />;
            })}
            <text x={padL + gi * gw + gw / 2} y={height - 8} fontSize={10} fill="var(--muted)" textAnchor="middle">{g}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

/** Sparkline de patrimônio com linha-base em 1,0. */
export function Sparkline({ values, width = 110, height = 26 }: { values: number[]; width?: number; height?: number }) {
  if (!values || values.length < 2) return null;
  const lo = Math.min(...values, 1), hi = Math.max(...values, 1), span = hi - lo || 1;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * width},${height - 2 - ((v - lo) / span) * (height - 4)}`).join(" ");
  const yb = height - 2 - ((1 - lo) / span) * (height - 4);
  return (
    <svg width={width} height={height} aria-hidden="true">
      <line x1={0} x2={width} y1={yb} y2={yb} stroke="var(--grid)" strokeWidth={1} />
      <polyline points={pts} fill="none" stroke="var(--s1)" strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

import { useEffect, useMemo, useRef, useState } from "react";
import { createChart, LineSeries, LineStyle, PriceScaleMode, ColorType, CrosshairMode, type IChartApi, type ISeriesApi, type MouseEventParams, type UTCTimestamp } from "lightweight-charts";
import { cssColors } from "../theme";
import { dateS, num } from "../format";

export interface LineSpec { id: string; label: string; color: string; data: { time: number; value: number }[]; width?: 1 | 2 | 3 | 4; style?: "solid" | "dashed" | "dotted"; }

const STYLE = { solid: LineStyle.Solid, dashed: LineStyle.Dashed, dotted: LineStyle.Dotted } as const;

/** Linhas no tempo (curvas de patrimônio, drawdown). Eixo único; escala log opcional. */
export function EquityChart({ series, height = 320, log = false, intraday = false, format = (v: number) => num(v, 2), themeKey }:
  { series: LineSpec[]; height?: number; log?: boolean; intraday?: boolean; format?: (v: number) => string; themeKey: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<{ time: number; values: Record<string, number> } | null>(null);
  const fmt = useMemo(() => format, [format]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const c = cssColors();
    const chart: IChartApi = createChart(el, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: c.muted, attributionLogo: false, fontFamily: "system-ui, sans-serif", fontSize: 11 },
      grid: { vertLines: { color: c.grid }, horzLines: { color: c.grid } },
      rightPriceScale: { borderColor: c.axis, mode: log ? PriceScaleMode.Logarithmic : PriceScaleMode.Normal, scaleMargins: { top: 0.08, bottom: 0.08 } },
      timeScale: { borderColor: c.axis, timeVisible: intraday, secondsVisible: false },
      crosshair: { mode: CrosshairMode.Normal, vertLine: { color: c.axis, labelBackgroundColor: c.ink2 }, horzLine: { color: c.axis, labelBackgroundColor: c.ink2 } },
      handleScroll: true, handleScale: true,
      localization: { locale: "pt-BR", priceFormatter: (p: number) => fmt(p) },
    });
    const apis: ISeriesApi<"Line">[] = series.map((s) => {
      const api = chart.addSeries(LineSeries, {
        color: s.color, lineWidth: s.width ?? 2, lineStyle: STYLE[s.style ?? "solid"], priceLineVisible: false, lastValueVisible: false,
        crosshairMarkerVisible: true, crosshairMarkerRadius: 4, crosshairMarkerBorderColor: c.surface, crosshairMarkerBorderWidth: 2,
      });
      api.setData(s.data.map((d) => ({ time: d.time as UTCTimestamp, value: d.value })));
      return api;
    });
    chart.timeScale().fitContent();
    const onMove = (p: MouseEventParams) => {
      if (p.time == null || !p.point) { setHover(null); return; }
      const values: Record<string, number> = {};
      apis.forEach((a, i) => {
        const d = p.seriesData.get(a) as { value?: number } | undefined;
        if (d && typeof d.value === "number") values[series[i].id] = d.value;
      });
      setHover({ time: p.time as number, values });
    };
    chart.subscribeCrosshairMove(onMove);
    return () => { chart.unsubscribeCrosshairMove(onMove); chart.remove(); };
  }, [series, log, intraday, fmt, themeKey]);

  return (
    <div className="chart-wrap">
      <div className="legend">
        {series.map((s) => (
          <span key={s.id} className="legend-item">
            <i className={`swatch ${s.style === "dashed" ? "dashed" : ""}`} style={{ background: s.style === "dashed" ? undefined : s.color, color: s.color }} />
            {s.label}
            {hover && hover.values[s.id] !== undefined && <b>{fmt(hover.values[s.id])}</b>}
          </span>
        ))}
        {hover && <span className="legend-item muted">{dateS(hover.time, intraday)}</span>}
      </div>
      <div ref={ref} style={{ height }} />
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { createChart, CandlestickSeries, HistogramSeries, ColorType, CrosshairMode, createSeriesMarkers, type MouseEventParams, type SeriesMarker, type UTCTimestamp, type Time } from "lightweight-charts";
import { cssColors } from "../theme";
import type { Candle, Marker } from "../types";
import { dateS, num } from "../format";

/** Candles com marcadores de entrada/saída e painel inferior com a posição executada. */
export function CandleChart({ candles, markers, pos, intraday, themeKey, height = 380 }:
  { candles: Candle[]; markers: Marker[]; pos: number[]; intraday: boolean; themeKey: string; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<{ time: number; o: number; h: number; l: number; c: number; pos: number } | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || candles.length === 0) return;
    const c = cssColors();
    const chart = createChart(el, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: c.muted, attributionLogo: false, fontFamily: "system-ui, sans-serif", fontSize: 11, panes: { separatorColor: c.grid, separatorHoverColor: c.axis, enableResize: false } },
      grid: { vertLines: { color: c.grid }, horzLines: { color: c.grid } },
      rightPriceScale: { borderColor: c.axis },
      timeScale: { borderColor: c.axis, timeVisible: intraday, secondsVisible: false },
      crosshair: { mode: CrosshairMode.Normal, vertLine: { color: c.axis, labelBackgroundColor: c.ink2 }, horzLine: { color: c.axis, labelBackgroundColor: c.ink2 } },
      localization: { locale: "pt-BR" },
    });
    const cs = chart.addSeries(CandlestickSeries, {
      upColor: c.s3, downColor: c.s8, wickUpColor: c.s3, wickDownColor: c.s8, borderVisible: false, priceLineVisible: false, lastValueVisible: false,
    });
    cs.setData(candles.map((k) => ({ time: k.t as UTCTimestamp, open: k.o, high: k.h, low: k.l, close: k.c })));
    const ms: SeriesMarker<Time>[] = [...markers]
      .sort((a, b) => a.t - b.t || (a.kind === "exit" ? -1 : 1))
      .map((m) => m.kind === "entry"
        ? { time: m.t as UTCTimestamp, position: m.side > 0 ? "belowBar" : "aboveBar", shape: m.side > 0 ? "arrowUp" : "arrowDown", color: m.side > 0 ? c.s1 : c.s2, text: m.side > 0 ? "C" : "V", size: 1 }
        : { time: m.t as UTCTimestamp, position: "inBar", shape: "circle", color: c.muted, size: 0.6 });
    createSeriesMarkers(cs, ms);
    const ps = chart.addSeries(HistogramSeries, { priceLineVisible: false, lastValueVisible: false, priceFormat: { type: "price", precision: 2, minMove: 0.01 }, base: 0 }, 1);
    ps.setData(candles.map((k, i) => ({ time: k.t as UTCTimestamp, value: pos[i] ?? 0, color: (pos[i] ?? 0) >= 0 ? c.s1 : c.s2 })));
    const panes = chart.panes();
    if (panes[1]) panes[1].setHeight(70);
    chart.timeScale().fitContent();
    const onMove = (p: MouseEventParams) => {
      if (p.time == null || !p.point) { setHover(null); return; }
      const k = p.seriesData.get(cs) as { open: number; high: number; low: number; close: number } | undefined;
      const v = p.seriesData.get(ps) as { value: number } | undefined;
      if (k) setHover({ time: p.time as number, o: k.open, h: k.high, l: k.low, c: k.close, pos: v?.value ?? 0 });
    };
    chart.subscribeCrosshairMove(onMove);
    return () => { chart.unsubscribeCrosshairMove(onMove); chart.remove(); };
  }, [candles, markers, pos, intraday, themeKey]);

  return (
    <div className="chart-wrap">
      <div className="legend">
        <span className="legend-item"><i className="swatch" style={{ background: "var(--s1)" }} />C = entrada comprada</span>
        <span className="legend-item"><i className="swatch" style={{ background: "var(--s2)" }} />V = entrada vendida</span>
        <span className="legend-item"><i className="swatch" style={{ background: "var(--muted)" }} />• saída</span>
        <span className="legend-item muted">painel inferior: posição executada (fração do patrimônio)</span>
        {hover && <span className="legend-item muted">{dateS(hover.time, intraday)} · A {num(hover.o)} M {num(hover.h)} m {num(hover.l)} F {num(hover.c)} · pos <b>{num(hover.pos, 2)}</b></span>}
      </div>
      <div ref={ref} style={{ height }} />
    </div>
  );
}

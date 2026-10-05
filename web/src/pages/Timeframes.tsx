import { useMemo, useState } from "react";
import type { Manifest, Row } from "../types";
import { TF_LABEL, cost, int, num, pct } from "../format";
import { Heatmap } from "../charts/Heatmap";
import { href } from "../router";

type Metric = "sharpe" | "cagr" | "cost" | "trades" | "pess" | "null_p";
const METRICS: { k: Metric; label: string; vmax: number; f: (v: number) => string; sign?: boolean }[] = [
  { k: "sharpe", label: "Sharpe OOS (custos base)", vmax: 2, f: (v) => num(v, 2) },
  { k: "pess", label: "Sharpe OOS (custos pessimistas)", vmax: 2, f: (v) => num(v, 2) },
  { k: "cagr", label: "CAGR", vmax: 0.6, f: (v) => pct(v, 0) },
  { k: "cost", label: "Custos pagos no OOS (fração do patrimônio)", vmax: 1.0, f: (v) => cost(v), sign: true },
  { k: "trades", label: "Trades por ano", vmax: 3000, f: (v) => int(v), sign: true },
  { k: "null_p", label: "p contra entradas aleatórias", vmax: 1, f: (v) => num(v, 2), sign: true },
];

export function Timeframes({ rows, manifest, themeKey }: { rows: Row[]; manifest: Manifest; themeKey: string }) {
  const [metric, setMetric] = useState<Metric>("sharpe");
  const spec = METRICS.find((m) => m.k === metric)!;
  const strategies = manifest.strategies.map((s) => ({ id: s, label: manifest.strategy_meta[s]?.label ?? s }));
  const byKey = useMemo(() => new Map(rows.map((r) => [`${r.strategy}__${r.tf}`, r])), [rows]);
  const value = (s: string, tf: string) => {
    const r = byKey.get(`${s}__${tf}`);
    if (!r) return null;
    const v = metric === "sharpe" ? r.metrics.base.sharpe : metric === "pess" ? r.metrics.pessimista.sharpe : metric === "cagr" ? r.metrics.base.cagr
      : metric === "cost" ? r.cost_total : metric === "trades" ? r.metrics.base.trades_per_year : r.null_p;
    // métricas "quanto menor melhor" entram negativas na escala divergente
    return spec.sign ? -v : v;
  };
  const fmt = (v: number) => spec.f(spec.sign ? -v : v);

  const summary = manifest.tfs.map((tf) => {
    const rs = rows.filter((r) => r.tf === tf && !r.is_benchmark);
    const mean = (f: (r: Row) => number) => rs.length ? rs.reduce((s, r) => s + f(r), 0) / rs.length : 0;
    return {
      tf, n: rs.length, aprov: rs.filter((r) => r.verdict === "aprovada").length, prom: rs.filter((r) => r.verdict === "promissora").length,
      sharpe: mean((r) => r.metrics.base.sharpe), best: Math.max(...rs.map((r) => r.metrics.base.sharpe)), cost: mean((r) => r.cost_total),
      trades: mean((r) => r.metrics.base.trades_per_year), gross: mean((r) => r.gross_total), net: mean((r) => r.metrics.base.total_return),
    };
  });

  return (
    <>
      <div className="card">
        <h2>Qual timeframe?</h2>
        <p className="sub">As mesmas famílias de estratégia, com grades de parâmetros equivalentes em barras, em cada timeframe. O que muda entre colunas não é o sinal: é quantas vezes você paga spread, taxa e deslize.</p>
        <div className="filters">
          {METRICS.map((m) => <button key={m.k} className={`chip ${metric === m.k ? "active" : ""}`} onClick={() => setMetric(m.k)}>{m.label}</button>)}
        </div>
        <div className="scroll">
          <Heatmap rows={strategies} cols={manifest.tfs} value={value} format={fmt} vmax={spec.vmax} colLabel={(t) => TF_LABEL[t] ?? t} themeKey={themeKey}
            onCell={(s, tf) => { location.hash = href.estrategia(`${s}__${tf}`); }} />
        </div>
        <p className="sub" style={{ marginTop: 8 }}>Azul = melhor, vermelho = pior, cinza = neutro. Clique numa célula para abrir a estratégia.</p>
      </div>

      <div className="card">
        <h2>Resumo por timeframe (só candidatas, sem referências)</h2>
        <div className="scroll">
          <table className="data">
            <thead><tr><th className="left">Timeframe</th><th>Candidatas</th><th>Aprovadas</th><th>Promissoras</th><th>Sharpe médio</th><th>Melhor Sharpe</th><th>Trades/ano médio</th><th>Custos pagos médio</th><th>Bruto médio</th><th>Líquido médio</th></tr></thead>
            <tbody>
              {summary.map((s) => <tr key={s.tf}><td className="left">{TF_LABEL[s.tf] ?? s.tf}</td><td>{s.n}</td><td>{s.aprov}</td><td>{s.prom}</td><td className={s.sharpe > 0 ? "pos" : "neg"}>{num(s.sharpe, 2)}</td>
                <td className={s.best > 0 ? "pos" : "neg"}>{num(s.best, 2)}</td><td>{int(s.trades)}</td><td>{cost(s.cost)}</td><td className={s.gross > 0 ? "pos" : "neg"}>{pct(s.gross, 0)}</td><td className={s.net > 0 ? "pos" : "neg"}>{pct(s.net, 0)}</td></tr>)}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h2>Cenários de custo usados</h2>
        <div className="scroll">
          <table className="data">
            <thead><tr><th className="left">Cenário</th><th>Taxa (bps/lado)</th><th>Spread (bps)</th><th>Deslize fixo (bps/lado)</th><th>Deslize por volatilidade (k)</th><th>Atraso (barras)</th><th>Ida e volta fixa (bps)</th><th className="left">Descrição</th></tr></thead>
            <tbody>
              {(Object.entries(manifest.scenarios) as [string, Manifest["scenarios"]["base"]][]).map(([k, s]) => <tr key={k}><td className="left">{k}</td><td>{num(s.fee_bps, 1)}</td><td>{num(s.spread_bps, 1)}</td><td>{num(s.slippage_bps, 1)}</td><td>{num(s.impact_k, 2)}</td><td>{s.lag_bars}</td><td>{num(s.round_trip_bps_fixed, 1)}</td><td className="left wrap">{s.description}</td></tr>)}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

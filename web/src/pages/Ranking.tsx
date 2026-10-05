import { useMemo, useState } from "react";
import type { Manifest, Row, Scenario } from "../types";
import { TF_LABEL, cls, cost, int, num, pct } from "../format";
import { Badge, Tile } from "../components";
import { Sparkline } from "../charts/Svg";
import { href } from "../router";

type SortKey = "sharpe" | "cagr" | "mdd" | "trades" | "null_p" | "dsr" | "pess" | "cost";

export function Ranking({ rows, manifest }: { rows: Row[]; manifest: Manifest }) {
  const [tf, setTf] = useState<string>("todos");
  const [hideBench, setHideBench] = useState(true);
  const [scn, setScn] = useState<Scenario>("base");
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "sharpe", dir: -1 });

  const get = (r: Row, k: SortKey): number => {
    const m = r.metrics[scn];
    switch (k) {
      case "sharpe": return m.sharpe; case "cagr": return m.cagr; case "mdd": return m.max_drawdown; case "trades": return m.n_trades;
      case "null_p": return r.null_p; case "dsr": return r.dsr; case "pess": return r.metrics.pessimista.sharpe; case "cost": return r.cost_total;
    }
  };
  const filtered = useMemo(() => rows
    .filter((r) => tf === "todos" || r.tf === tf)
    .filter((r) => !hideBench || !r.is_benchmark)
    .sort((a, b) => (get(a, sort.key) - get(b, sort.key)) * sort.dir), [rows, tf, hideBench, sort, scn]);

  const competitors = rows.filter((r) => !r.is_benchmark);
  const best = competitors.slice().sort((a, b) => b.metrics.base.sharpe - a.metrics.base.sharpe)[0];
  const nFolds = rows[0]?.fold_returns.length ?? 0;
  const nBacktests = rows.reduce((s, r) => s + r.n_trials * nFolds, 0);
  const approved = competitors.filter((r) => r.verdict === "aprovada").length;
  const promising = competitors.filter((r) => r.verdict === "promissora").length;

  const th = (key: SortKey, label: string) => (
    <th className={sort.key === key ? "sorted" : ""} onClick={() => setSort((s) => ({ key, dir: s.key === key ? (s.dir === 1 ? -1 : 1) : -1 }))}>
      {label}{sort.key === key ? (sort.dir === -1 ? " ↓" : " ↑") : ""}
    </th>
  );

  return (
    <>
      <div className="tiles">
        <Tile label="Estratégias × timeframes" value={String(competitors.length)} delta={`${manifest.strategies.length} famílias · ${manifest.tfs.length} timeframes`} />
        <Tile label="Backtests no walk-forward" value={int(nBacktests)} delta={`${nFolds} janelas de ${manifest.wf.test_months} meses`} />
        <Tile label="Período fora da amostra" value={rows[0] ? rows[0].oos_range[0].slice(0, 7) : "–"} delta={rows[0] ? `até ${rows[0].oos_range[1].slice(0, 7)}` : ""} />
        <Tile label="Melhor Sharpe OOS (base)" value={best ? num(best.metrics.base.sharpe, 2) : "–"} delta={best ? `${best.label} · ${TF_LABEL[best.tf]}` : ""} cls={cls(best?.metrics.base.sharpe)} />
        <Tile label="Aprovadas / promissoras" value={`${approved} / ${promising}`} delta={`de ${competitors.length} candidatas`} />
      </div>

      <div className="card">
        <h2>Ranking fora da amostra</h2>
        <p className="sub">Cada linha é uma família de estratégia num timeframe, com os parâmetros escolhidos a cada janela só com dados passados. Clique para ver detalhes.</p>
        <div className="filters">
          <button className={`chip ${tf === "todos" ? "active" : ""}`} onClick={() => setTf("todos")}>todos</button>
          {manifest.tfs.map((t) => <button key={t} className={`chip ${tf === t ? "active" : ""}`} onClick={() => setTf(t)}>{TF_LABEL[t] ?? t}</button>)}
          <span className="muted">·</span>
          {(["otimista", "base", "pessimista", "maker"] as Scenario[]).filter((s) => rows[0]?.metrics[s]).map((s) => <button key={s} className={`chip ${scn === s ? "active" : ""}`} onClick={() => setScn(s)}>custos: {s}</button>)}
          <span className="spacer" />
          <label className="toggle"><input type="checkbox" checked={!hideBench} onChange={(e) => setHideBench(!e.target.checked)} /> mostrar referências (comprar e segurar, aleatória)</label>
        </div>
        <div className="scroll">
          <table className="data">
            <thead>
              <tr>
                <th className="left">#</th><th className="left">Estratégia</th><th className="left">TF</th><th className="left">Veredito</th>
                {th("sharpe", "Sharpe")}{th("cagr", "CAGR")}{th("mdd", "DD máx.")}{th("trades", "Trades")}
                {th("null_p", "p nulo")}{th("dsr", "DSR")}{th("pess", "Sharpe pess.")}{th("cost", "Custos")}<th>Curva OOS</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => {
                const m = r.metrics[scn];
                return (
                  <tr key={r.id} className={`row ${r.is_benchmark ? "bench" : ""}`} onClick={() => { location.hash = href.estrategia(r.id); }}>
                    <td>{i + 1}</td>
                    <td className="left">{r.label}{r.is_benchmark && <span className="muted"> (referência)</span>}</td>
                    <td className="left">{TF_LABEL[r.tf] ?? r.tf}</td>
                    <td className="left"><Badge v={r.verdict} /></td>
                    <td className={cls(m.sharpe)}>{num(m.sharpe, 2)}</td>
                    <td className={cls(m.cagr)}>{pct(m.cagr)}</td>
                    <td className="neg">{pct(m.max_drawdown)}</td>
                    <td>{int(m.n_trades)}</td>
                    <td>{num(r.null_p, 3)}</td>
                    <td>{num(r.dsr, 2)}</td>
                    <td className={cls(r.metrics.pessimista.sharpe)}>{num(r.metrics.pessimista.sharpe, 2)}</td>
                    <td>{cost(r.cost_total)}</td>
                    <td><Sparkline values={r.spark} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

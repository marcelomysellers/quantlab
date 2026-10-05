import { useEffect, useMemo, useState } from "react";
import type { Detail, Manifest, Scenario } from "../types";
import { loadEntry } from "../data";
import { TF_LABEL, cls, cost, dateS, int, num, paramsS, pct } from "../format";
import { Badge, Tile } from "../components";
import { EquityChart, type LineSpec } from "../charts/EquityChart";
import { CandleChart } from "../charts/CandleChart";
import { GroupedBars, Histogram } from "../charts/Svg";
import { Heatmap } from "../charts/Heatmap";
import { cssColors } from "../theme";
import { href } from "../router";

const SCN: Scenario[] = ["otimista", "base", "pessimista"];
const METRIC_ROWS: { k: keyof Detail["metrics"]["base"]; label: string; f: (v: number) => string; signed?: boolean }[] = [
  { k: "sharpe", label: "Sharpe (diário, anualizado)", f: (v) => num(v, 2), signed: true },
  { k: "sortino", label: "Sortino", f: (v) => num(v, 2), signed: true },
  { k: "cagr", label: "CAGR", f: (v) => pct(v), signed: true },
  { k: "total_return", label: "Retorno total OOS", f: (v) => pct(v), signed: true },
  { k: "ann_vol", label: "Volatilidade anual", f: (v) => pct(v) },
  { k: "max_drawdown", label: "Drawdown máximo", f: (v) => pct(v) },
  { k: "calmar", label: "Calmar", f: (v) => num(v, 2), signed: true },
  { k: "n_trades", label: "Trades", f: (v) => int(v) },
  { k: "win_rate", label: "Taxa de acerto", f: (v) => pct(v) },
  { k: "profit_factor", label: "Fator de lucro", f: (v) => num(v, 2) },
  { k: "avg_trade_ret", label: "Retorno médio por trade", f: (v) => pct(v, 2), signed: true },
  { k: "avg_bars_in_trade", label: "Barras por trade", f: (v) => num(v, 1) },
  { k: "exposure", label: "Tempo posicionado", f: (v) => pct(v, 0) },
  { k: "turnover_per_year", label: "Giro por ano (x patrimônio)", f: (v) => num(v, 0) },
  { k: "t_stat", label: "t-stat", f: (v) => num(v, 2), signed: true },
  { k: "psr", label: "PSR (P[Sharpe > 0])", f: (v) => pct(v, 0) },
];

export function Strategy({ id, manifest, themeKey }: { id: string; manifest: Manifest; themeKey: string }) {
  const [d, setD] = useState<Detail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showScn, setShowScn] = useState(false);
  const [showOv, setShowOv] = useState(true);
  useEffect(() => { setD(null); loadEntry(id).then(setD).catch((e) => setErr(String(e))); }, [id]);

  const c = useMemo(() => cssColors(), [themeKey]);
  const intraday = (d?.tf_minutes ?? 1440) < 1440;

  const eqSeries = useMemo<LineSpec[]>(() => {
    if (!d) return [];
    const s: LineSpec[] = [
      { id: "eq", label: `${d.label} · OOS (custos base)`, color: c.s1, data: d.curve.map((p) => ({ time: p.t, value: p.eq })) },
      { id: "bh", label: "Comprar e segurar", color: c.s2, data: d.curve.map((p) => ({ time: p.t, value: p.bh })) },
    ];
    if (showOv && d.curve[0]?.ov !== undefined) s.push({ id: "ov", label: "Vitrine: melhor parâmetro escolhido olhando tudo (in-sample)", color: c.s3, style: "dashed", width: 1, data: d.curve.map((p) => ({ time: p.t, value: p.ov as number })) });
    if (showScn) {
      s.push({ id: "opt", label: "custos otimistas", color: c.s1, width: 1, style: "dotted", data: d.curve.map((p) => ({ time: p.t, value: p.opt })) });
      s.push({ id: "pess", label: "custos pessimistas", color: c.s1, width: 1, style: "dashed", data: d.curve.map((p) => ({ time: p.t, value: p.pess })) });
    }
    return s;
  }, [d, c, showOv, showScn]);
  const ddSeries = useMemo<LineSpec[]>(() => d ? [{ id: "dd", label: "Drawdown", color: c.s1, data: d.curve.map((p) => ({ time: p.t, value: p.dd * 100 })) }] : [], [d, c]);

  // superfície de parâmetros: Sharpe OOS de cada configuração em cada janela
  const surface = useMemo(() => {
    if (!d) return null;
    const configs = new Map<string, Record<string, unknown>>();
    d.folds.forEach((f) => f.table.forEach((r) => configs.set(JSON.stringify(r.params), r.params)));
    const rows = [...configs.entries()].map(([key, p]) => ({ id: key, label: paramsS(p) }));
    const cols = d.folds.map((f) => String(f.k + 1));
    const val = (r: string, col: string) => {
      const f = d.folds[Number(col) - 1];
      const row = f?.table.find((t) => JSON.stringify(t.params) === r);
      return row ? row.oos_sharpe : null;
    };
    return { rows, cols, val };
  }, [d]);

  if (err) return <div className="card"><div className="empty">{err}</div></div>;
  if (!d) return <div className="card"><div className="empty">carregando…</div></div>;
  const m = d.metrics.base;
  const chosen = [...new Set(d.params_by_fold.map((p) => paramsS(p)))];

  return (
    <>
      <div className="card">
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <a href={href.ranking()} className="tab">← ranking</a>
          <h2 style={{ margin: 0 }}>{d.label} <span className="muted">· {TF_LABEL[d.tf] ?? d.tf}</span></h2>
          <Badge v={d.verdict} />
          <span className="spacer" />
          <a className="tab" href={href.duelo(d.id)}>duelar com…</a>
        </div>
        <p className="sub" style={{ marginTop: 8 }}>{d.description}</p>
        <dl className="kv">
          <dt>Fora da amostra</dt><dd>{d.oos_range[0]} a {d.oos_range[1]} · {d.folds.length} janelas · treino {manifest.wf.train_months} m / teste {manifest.wf.test_months} m</dd>
          <dt>Grade testada</dt><dd>{d.grid_size} configurações por janela (n_trials={d.n_trials} para o DSR)</dd>
          <dt>Parâmetros escolhidos</dt><dd className="mono">{chosen.join("  |  ")}</dd>
        </dl>
      </div>

      <div className="tiles">
        <Tile label="Sharpe OOS (base)" value={num(m.sharpe, 2)} delta={`IC 90%: ${num(d.sharpe_ci90[0], 2)} a ${num(d.sharpe_ci90[1], 2)}`} cls={cls(m.sharpe)} />
        <Tile label="CAGR" value={pct(m.cagr)} delta={`comprar e segurar: ${pct(d.bh.cagr)}`} cls={cls(m.cagr)} />
        <Tile label="Drawdown máximo" value={pct(m.max_drawdown)} delta={`comprar e segurar: ${pct(d.bh.max_drawdown)}`} cls="neg" />
        <Tile label="Trades OOS" value={int(m.n_trades)} delta={`${num(m.trades_per_year, 0)} por ano · acerto ${pct(m.win_rate, 0)}`} />
        <Tile label="p contra entradas aleatórias" value={num(d.null_p, 3)} delta={`${d.null.n_sims} simulações com a mesma exposição`} cls={d.null_p < 0.05 ? "pos" : ""} />
        <Tile label="Sharpe deflacionado (DSR)" value={num(d.dsr, 2)} delta={d.dsr_global != null ? `família: ${d.n_trials} tentativas · torneio inteiro (${d.n_trials_global}): ${num(d.dsr_global, 2)}` : `corrigido por ${d.n_trials} tentativas`} cls={d.dsr > 0.9 ? "pos" : ""} />
        {d.fold_concentration != null && <Tile label="Retorno na melhor janela" value={pct(d.fold_concentration, 0)} delta={`sem a melhor janela: ${pct(d.oos_return_ex_best_fold)}`} cls={d.fold_concentration > 0.6 ? "neg" : ""} />}
      </div>

      <div className="card">
        <h2>Veredito</h2>
        <ul className="checks">
          {d.checks.map((ck) => <li key={ck.id}><span className={ck.ok ? "ok" : "fail"}>{ck.ok ? "✓" : "✕"}</span>{ck.label}<span className="val">{typeof ck.value === "number" ? num(ck.value, 2) : String(ck.value)}</span></li>)}
        </ul>
      </div>

      <div className="card">
        <h2>Patrimônio fora da amostra</h2>
        <p className="sub">Base 1,0 no início do período OOS, resolução diária, escala logarítmica. A curva tracejada é o que um backtest otimizado no período inteiro mostraria: a diferença entre ela e a curva sólida é o tamanho do overfitting.</p>
        <div className="filters">
          <label className="toggle"><input type="checkbox" checked={showOv} onChange={(e) => setShowOv(e.target.checked)} /> mostrar curva de vitrine</label>
          <label className="toggle"><input type="checkbox" checked={showScn} onChange={(e) => setShowScn(e.target.checked)} /> mostrar cenários de custo</label>
        </div>
        <EquityChart series={eqSeries} height={340} log themeKey={themeKey} />
        <h3>Drawdown (%)</h3>
        <EquityChart series={ddSeries} height={140} themeKey={themeKey} format={(v) => num(v, 1) + "%"} />
      </div>

      <div className="card">
        <h2>Operações no gráfico</h2>
        <p className="sub">Últimas {d.candles.length} barras do período OOS com as entradas e saídas executadas (abertura da barra seguinte ao sinal, já com deslize).</p>
        <CandleChart candles={d.candles} markers={d.markers} pos={d.pos_win} intraday={intraday} themeKey={themeKey} />
      </div>

      <div className="grid2">
        <div className="card">
          <h2>Contra entradas aleatórias</h2>
          <p className="sub">{d.null.n_sims} estratégias sorteadas com o mesmo número de trades, as mesmas durações e os mesmos custos. p = {num(d.null_p, 3)}: fração que iguala ou supera o Sharpe real.</p>
          <Histogram values={d.null.sharpes} marker={d.null.actual} markerLabel="real" xLabel="Sharpe das simulações" />
        </div>
        <div className="card">
          <h2>Estresse de execução</h2>
          <p className="sub">{d.stress.length} repetições em que {pct(d.stress_model.miss_prob, 0)} das entradas não executam e {pct(d.stress_model.partial_prob, 0)} saem parciais (entre {pct(d.stress_model.partial_min, 0)} e 100% do tamanho). Mediana do Sharpe: {num(d.stress_sharpe_median, 2)}; percentil 10: {num(d.stress_sharpe_p10, 2)}.</p>
          <Histogram values={d.stress.map((s) => s.sharpe)} marker={m.sharpe} markerLabel="sem estresse" xLabel="Sharpe com fills parciais" />
        </div>
      </div>

      <div className="card">
        <h2>Três cenários de custo</h2>
        <p className="sub">Mesmas posições, custos diferentes. Bruto no período: {pct(d.gross_total)}; custos pagos (base): {cost(d.cost_total)} do patrimônio.</p>
        <div className="scroll">
          <table className="data">
            <thead><tr><th className="left">Métrica</th>{SCN.map((s) => <th key={s}>{s} <span className="muted">({num(manifest.scenarios[s].round_trip_bps_fixed, 1)} bps ida e volta)</span></th>)}</tr></thead>
            <tbody>
              {METRIC_ROWS.map((r) => <tr key={r.k}><td className="left">{r.label}</td>{SCN.map((s) => { const v = d.metrics[s][r.k] as number; return <td key={s} className={r.signed ? cls(v) : r.k === "max_drawdown" ? "neg" : ""}>{r.f(v)}</td>; })}</tr>)}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h2>Walk-forward por janela</h2>
        <p className="sub">Em cada janela, o parâmetro vencedor no treino é aplicado no teste seguinte. Sharpe dentro da amostra alto com fora da amostra baixo é a assinatura do overfitting.</p>
        <GroupedBars groups={d.folds.map((f) => `J${f.k + 1}`)} series={[
          { label: "Sharpe no treino (in-sample)", color: c.muted, values: d.folds.map((f) => f.is_sharpe) },
          { label: "Sharpe no teste (OOS)", color: c.s1, values: d.folds.map((f) => f.oos_sharpe) },
        ]} />
        <div className="scroll">
          <table className="data">
            <thead><tr><th className="left">Janela</th><th className="left">Treino</th><th className="left">Teste</th><th className="left">Parâmetros</th><th>Configs</th><th>Trades treino</th><th>Sharpe treino</th><th>Sharpe teste</th><th>Retorno teste</th></tr></thead>
            <tbody>
              {d.folds.map((f) => <tr key={f.k}><td>{f.k + 1}</td><td className="left">{f.train[0]} → {f.train[1]}</td><td className="left">{f.test[0]} → {f.test[1]}</td>
                <td className="left mono">{paramsS(f.params)}</td><td>{f.n_configs}</td><td>{f.n_trades_is}</td><td className={cls(f.is_sharpe)}>{num(f.is_sharpe, 2)}</td>
                <td className={cls(f.oos_sharpe)}>{num(f.oos_sharpe, 2)}</td><td className={cls(f.oos_return)}>{pct(f.oos_return)}</td></tr>)}
            </tbody>
          </table>
        </div>
        {surface && surface.rows.length > 1 && (
          <details style={{ marginTop: 12 }}>
            <summary>Superfície de parâmetros: Sharpe OOS de cada configuração em cada janela (estratégia robusta = superfície lisa)</summary>
            <div className="scroll" style={{ marginTop: 8 }}>
              <Heatmap rows={surface.rows} cols={surface.cols} value={surface.val} format={(v) => num(v, 1)} vmax={2} colLabel={(x) => `J${x}`} themeKey={themeKey} />
            </div>
          </details>
        )}
      </div>

      <div className="card">
        <h2>Últimos trades</h2>
        <div className="scroll" style={{ maxHeight: 360, overflowY: "auto" }}>
          <table className="data">
            <thead><tr><th className="left">Entrada</th><th className="left">Saída</th><th className="left">Lado</th><th>Tamanho</th><th>Barras</th><th>Preço entrada</th><th>Preço saída</th><th>Resultado líquido</th></tr></thead>
            <tbody>
              {d.trades.slice().reverse().map((t, i) => <tr key={i}><td className="left">{dateS(t.entry, intraday)}</td><td className="left">{t.open ? "aberto" : dateS(t.exit, intraday)}</td>
                <td className="left">{t.side > 0 ? "compra" : "venda"}</td><td>{num(t.size, 2)}</td><td>{t.bars}</td><td>{num(t.entry_px, 2)}</td><td>{num(t.exit_px, 2)}</td><td className={cls(t.ret_net)}>{pct(t.ret_net, 2)}</td></tr>)}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

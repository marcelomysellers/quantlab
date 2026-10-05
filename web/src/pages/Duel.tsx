import { useEffect, useMemo, useState } from "react";
import type { Detail, Row } from "../types";
import { loadEntry } from "../data";
import { TF_LABEL, cls, num, pct } from "../format";
import { EquityChart, type LineSpec } from "../charts/EquityChart";
import { GroupedBars } from "../charts/Svg";
import { cssColors } from "../theme";
import { Tile } from "../components";

function sharpe(r: number[]) { const n = r.length; if (n < 3) return 0; const m = r.reduce((a, b) => a + b, 0) / n; const sd = Math.sqrt(r.reduce((a, b) => a + (b - m) ** 2, 0) / (n - 1)); return sd > 0 ? (m / sd) * Math.sqrt(365.25) : 0; }
function corr(a: number[], b: number[]) { const n = a.length; const ma = a.reduce((x, y) => x + y, 0) / n, mb = b.reduce((x, y) => x + y, 0) / n; let num = 0, da = 0, db = 0; for (let i = 0; i < n; i++) { num += (a[i] - ma) * (b[i] - mb); da += (a[i] - ma) ** 2; db += (b[i] - mb) ** 2; } return da > 0 && db > 0 ? num / Math.sqrt(da * db) : 0; }
function equity(r: number[]) { const out: number[] = []; let e = 1; for (const x of r) { e *= 1 + x; out.push(e); } return out; }
function mdd(eq: number[]) { let peak = -Infinity, worst = 0; for (const e of eq) { peak = Math.max(peak, e); worst = Math.min(worst, e / peak - 1); } return worst; }

export function Duel({ rows, a, b, themeKey }: { rows: Row[]; a?: string; b?: string; themeKey: string }) {
  const options = rows.filter((r) => !r.is_benchmark || r.strategy === "buy_hold");
  const defA = a ?? options[0]?.id;
  const defB = b ?? options.find((r) => r.id !== defA)?.id;
  const [ida, setA] = useState(defA);
  const [idb, setB] = useState(defB);
  const [da, setDa] = useState<Detail | null>(null);
  const [db, setDb] = useState<Detail | null>(null);
  useEffect(() => { if (ida) loadEntry(ida).then(setDa); }, [ida]);
  useEffect(() => { if (idb) loadEntry(idb).then(setDb); }, [idb]);
  const c = useMemo(() => cssColors(), [themeKey]);

  const duel = useMemo(() => {
    if (!da || !db) return null;
    const mb = new Map(db.daily.t.map((t, i) => [t, db.daily.r[i]]));
    const t: number[] = [], ra: number[] = [], rb: number[] = [];
    da.daily.t.forEach((ti, i) => { const v = mb.get(ti); if (v !== undefined) { t.push(ti); ra.push(da.daily.r[i]); rb.push(v); } });
    const comb = ra.map((x, i) => 0.5 * x + 0.5 * rb[i]);
    const ea = equity(ra), eb = equity(rb), ec = equity(comb);
    const wonA = da.fold_returns.filter((x, i) => x > (db.fold_returns[i] ?? -Infinity)).length;
    const wonB = db.fold_returns.filter((x, i) => x > (da.fold_returns[i] ?? -Infinity)).length;
    const years = t.length / 365.25;
    return {
      t, sa: sharpe(ra), sb: sharpe(rb), sc: sharpe(comb), corr: corr(ra, rb),
      ta: ea[ea.length - 1] - 1, tb: eb[eb.length - 1] - 1, tc: ec[ec.length - 1] - 1,
      ca: years > 0 ? ea[ea.length - 1] ** (1 / years) - 1 : 0, cb: years > 0 ? eb[eb.length - 1] ** (1 / years) - 1 : 0, cc: years > 0 ? ec[ec.length - 1] ** (1 / years) - 1 : 0,
      ma: mdd(ea), mb: mdd(eb), mc: mdd(ec), wonA, wonB, n: da.fold_returns.length,
      series: [
        { id: "a", label: `${da.label} · ${TF_LABEL[da.tf]}`, color: c.s1, data: t.map((ti, i) => ({ time: ti, value: ea[i] })) },
        { id: "b", label: `${db.label} · ${TF_LABEL[db.tf]}`, color: c.s2, data: t.map((ti, i) => ({ time: ti, value: eb[i] })) },
        { id: "c", label: "carteira 50/50 (rebalanceada diariamente)", color: c.s3, width: 1, data: t.map((ti, i) => ({ time: ti, value: ec[i] })) },
      ] as LineSpec[],
    };
  }, [da, db, c]);

  const label = (r: Row) => `${r.label} · ${TF_LABEL[r.tf] ?? r.tf} (Sharpe ${num(r.metrics.base.sharpe, 2)})`;
  const winner = duel ? (duel.sa === duel.sb ? null : duel.sa > duel.sb ? da : db) : null;

  return (
    <>
      <div className="card">
        <h2>Duelo</h2>
        <p className="sub">Duas estratégias no mesmo período OOS, retornos diários, custos base. Além de quem ganha, importa a correlação: duas estratégias medianas e pouco correlacionadas somadas valem mais que uma boa.</p>
        <div className="filters">
          <select className="inline-select" value={ida} onChange={(e) => setA(e.target.value)}>{options.map((r) => <option key={r.id} value={r.id}>{label(r)}</option>)}</select>
          <span className="muted">contra</span>
          <select className="inline-select" value={idb} onChange={(e) => setB(e.target.value)}>{options.map((r) => <option key={r.id} value={r.id}>{label(r)}</option>)}</select>
        </div>
        {duel && da && db && (
          <>
            <div className="hero" style={{ margin: "8px 0 4px" }}>{winner ? winner.label : "empate"}</div>
            <p className="sub">{winner ? `vence por Sharpe ${num(Math.max(duel.sa, duel.sb), 2)} contra ${num(Math.min(duel.sa, duel.sb), 2)} e leva ${Math.max(duel.wonA, duel.wonB)} de ${duel.n} janelas` : "mesmo Sharpe"} · correlação diária {num(duel.corr, 2)}</p>
            <div className="tiles">
              <Tile label={`Sharpe · ${da.label}`} value={num(duel.sa, 2)} delta={`CAGR ${pct(duel.ca)} · DD ${pct(duel.ma)}`} cls={cls(duel.sa)} />
              <Tile label={`Sharpe · ${db.label}`} value={num(duel.sb, 2)} delta={`CAGR ${pct(duel.cb)} · DD ${pct(duel.mb)}`} cls={cls(duel.sb)} />
              <Tile label="Sharpe · carteira 50/50" value={num(duel.sc, 2)} delta={`CAGR ${pct(duel.cc)} · DD ${pct(duel.mc)}`} cls={cls(duel.sc)} />
              <Tile label="Janelas vencidas" value={`${duel.wonA} × ${duel.wonB}`} delta={`de ${duel.n}, por retorno no teste`} />
            </div>
            <EquityChart series={duel.series} height={340} log themeKey={themeKey} />
            <h3>Retorno por janela de teste</h3>
            <GroupedBars groups={da.fold_returns.map((_, i) => `J${i + 1}`)} series={[
              { label: da.label, color: c.s1, values: da.fold_returns },
              { label: db.label, color: c.s2, values: db.fold_returns },
            ]} format={(v) => pct(v, 0)} />
          </>
        )}
      </div>
    </>
  );
}

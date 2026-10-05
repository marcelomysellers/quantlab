import { useEffect, useMemo, useState } from "react";
import { num, pct } from "../format";
import { Heatmap } from "../charts/Heatmap";
import { Tile } from "../components";

interface IcRow { scope: string; feature: string; horizon_h: number; period: string; ic: number | null; t: number | null; pct_pos: number | null; n_months: number; symbol_consistency: number | null; n_symbols: number; bh_pass: boolean; aprovada: boolean }
interface CalRow { bucket: string; value: number; mean_vol_units: number; t: number; n: number; year_consistency: number; n_years: number }
interface Panel { rows: IcRow[]; calendar: CalRow[]; horizons: number[]; train: [string, string]; confirm: [string, string]; symbols: string[]; generated_at: string }

const BUCKET_LABEL: Record<string, string> = { hour: "hora UTC", dow: "dia da semana (0 = segunda)", hours_to_funding: "horas até o funding", us_session: "sessão dos EUA (13h30–20h UTC)" };

export function Signals({ themeKey }: { themeKey: string }) {
  const [p, setP] = useState<Panel | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [scope, setScope] = useState<string>("BTC");
  const [period, setPeriod] = useState<string>("treino");
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}results/signals/painel_ic.json`).then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); }).then(setP).catch((e) => setErr(String(e)));
  }, []);
  const scopes = useMemo(() => (p ? [...new Set(p.rows.map((r) => r.scope))] : []), [p]);
  const view = useMemo(() => {
    if (!p) return null;
    const rows = p.rows.filter((r) => r.scope === scope && r.period === period);
    const feats = [...new Set(rows.map((r) => r.feature))];
    const byKey = new Map(rows.map((r) => [`${r.feature}|${r.horizon_h}`, r]));
    const approved = p.rows.filter((r) => r.scope === scope && r.period === "treino" && r.aprovada);
    return { rows, feats, byKey, approved };
  }, [p, scope, period]);
  if (err) return <div className="card"><div className="empty">Sem painel de sinais publicado. Rode <code>python -m quantlab.research.ic_panel</code>. <span className="muted">{err}</span></div></div>;
  if (!p || !view) return <div className="card"><div className="empty">carregando…</div></div>;
  const nTests = p.rows.filter((r) => r.period === "treino").length;
  const nApproved = p.rows.filter((r) => r.period === "treino" && r.aprovada).length;
  return (
    <>
      <div className="tiles">
        <Tile label="Testes pré-registrados" value={String(nTests)} delta={`${p.symbols.length} ativos · horizontes ${p.horizons.join(", ")} h`} />
        <Tile label="Aprovadas na regra" value={String(nApproved)} delta="|t| > 3 no treino, BH 10%, repete na confirmação" cls={nApproved > 0 ? "pos" : ""} />
        <Tile label="Treino" value={`${p.train[0].slice(0, 4)}–${Number(p.train[1].slice(0, 4)) - 1}`} delta={`confirmação ${p.confirm[0].slice(0, 4)}–${Number(p.confirm[1].slice(0, 4)) - 1} · 2026 lacrado`} />
      </div>
      <div className="card">
        <h2>Painel de IC: t-stat do IC mensal por feature e horizonte</h2>
        <p className="sub">Cada célula é a estatística t da média dos IC mensais (Spearman entre a feature no fechamento e o retorno das próximas h horas). Azul = positivo, vermelho = negativo, cinza = nada. A lista de features foi registrada antes de olhar os dados (research/hipoteses.md, H014).</p>
        <div className="filters">
          {scopes.map((s) => <button key={s} className={`chip ${scope === s ? "active" : ""}`} onClick={() => setScope(s)}>{s === "BTC" ? "BTC sozinho" : "painel de altcoins"}</button>)}
          <span className="muted">·</span>
          {["treino", "confirmacao"].map((s) => <button key={s} className={`chip ${period === s ? "active" : ""}`} onClick={() => setPeriod(s)}>{s === "treino" ? "treino 2020–2023" : "confirmação 2024–2025"}</button>)}
        </div>
        <div className="scroll">
          <Heatmap rows={view.feats.map((f) => ({ id: f, label: f }))} cols={p.horizons.map(String)}
            value={(f, h) => { const r = view.byKey.get(`${f}|${h}`); return r && r.t != null ? (Math.abs(r.t) < 2 ? 0 : r.t) : null; }}
            format={(v) => (v === 0 ? "·" : num(v, 1))} vmax={5} colLabel={(h) => `${h} h`} themeKey={themeKey} />
        </div>
      </div>
      <div className="card">
        <h2>Aprovadas na regra pré-registrada</h2>
        {view.approved.length === 0 ? <p className="sub">Nenhuma feature deste escopo passou: |t| &gt; 3 no treino, sobrevive a Benjamini-Hochberg 10% e repete o sinal com |t| &gt; 2 na confirmação.</p> : (
          <div className="scroll"><table className="data"><thead><tr><th className="left">feature</th><th>horizonte</th><th>IC treino</th><th>t treino</th><th>% meses +</th><th>IC confirmação</th><th>t confirmação</th></tr></thead><tbody>
            {view.approved.map((r) => { const c = p.rows.find((x) => x.scope === r.scope && x.feature === r.feature && x.horizon_h === r.horizon_h && x.period === "confirmacao"); return (
              <tr key={r.feature + r.horizon_h}><td className="left">{r.feature}</td><td>{r.horizon_h} h</td><td>{num(r.ic, 3)}</td><td>{num(r.t, 1)}</td><td>{pct(r.pct_pos, 0)}</td><td>{num(c?.ic ?? null, 3)}</td><td>{num(c?.t ?? null, 1)}</td></tr>); })}
          </tbody></table></div>)}
      </div>
      <div className="card">
        <h2>Calendário por bucket (H015)</h2>
        <p className="sub">Retorno médio da hora seguinte, em unidades de volatilidade do próprio ativo, 10 ativos agrupados em 2020–2025. Só buckets com |t| &gt; 3 e sinal igual na maioria dos anos merecem atenção, e mesmo esses só pagam custo como filtro, não como estratégia.</p>
        <div className="scroll"><table className="data"><thead><tr><th className="left">bucket</th><th>valor</th><th>média (vol)</th><th>t</th><th>n</th><th>anos com o mesmo sinal</th></tr></thead><tbody>
          {[...p.calendar].sort((a, b) => Math.abs(b.t) - Math.abs(a.t)).slice(0, 20).map((c) => (
            <tr key={c.bucket + c.value}><td className="left">{BUCKET_LABEL[c.bucket] ?? c.bucket}</td><td>{c.value}</td><td className={c.mean_vol_units > 0 ? "pos" : "neg"}>{num(c.mean_vol_units, 4)}</td><td className={Math.abs(c.t) >= 3 ? (c.t > 0 ? "pos" : "neg") : ""}>{num(c.t, 1)}</td><td>{c.n}</td><td>{pct(c.year_consistency, 0)} de {c.n_years}</td></tr>))}
        </tbody></table></div>
      </div>
    </>
  );
}

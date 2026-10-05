"""Funding do perpétuo BTCUSDT (Binance, 2020-2023) em três papéis (hipóteses H016, H017, H018).

1. Sinal (Laufer): após funding no decil extremo (percentil móvel de 90 dias), o retorno seguinte.
2. Carry (Frey): vendido no perpétuo e comprado no spot só quando a média de 7 dias do funding está
   acima de um percentil; P&L = funding recebido, SEM o P&L da base e SEM risco de liquidação (é um piso).
3. Custo (Straus, Ax): quanto o funding tira de uma estratégia de tendência sempre comprada.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy import stats

from quantlab.backtest.engine import aggregate_daily, funding_per_bar, run_backtest
from quantlab.backtest.metrics import sharpe
from quantlab.data.funding import load_funding
from quantlab.data.store import load_bars
from quantlab.execution import SCENARIOS
from quantlab.strategies import REGISTRY, Context

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def event_study(b1h: pd.DataFrame, fr: pd.Series) -> list[dict]:
    lo = np.log(b1h["open"])
    out = []
    pct = fr.rolling(270, min_periods=90).rank(pct=True)   # percentil móvel de 90 dias (270 períodos de 8 h)
    idx = b1h.index.searchsorted(fr.index)
    ok = (idx > 0) & (idx < len(b1h) - 30)
    for h in (1, 8, 24):
        fwd = (lo.shift(-(1 + h)) - lo.shift(-1)).to_numpy()
        y = fwd[idx[ok]]
        p = pct.to_numpy()[ok]
        yrs = fr.index.year.to_numpy()[ok]
        for name, mask in (("funding > p90", p > 0.9), ("funding < p10", p < 0.1), ("meio (p10-p90)", (p >= 0.1) & (p <= 0.9))):
            yy = y[mask]; yy = yy[~np.isnan(yy)]
            if len(yy) < 30:
                continue
            t = yy.mean() / (yy.std(ddof=1) / np.sqrt(len(yy)))
            by_year = pd.Series(y[mask], index=yrs[mask]).dropna().groupby(level=0).mean()
            out.append({"bucket": name, "horizon_h": h, "mean_bps": round(1e4 * float(yy.mean()), 2), "t": round(float(t), 2),
                        "n": int(len(yy)), "year_consistency": round(float((np.sign(by_year) == np.sign(yy.mean())).mean()), 2)})
    return out


def carry_rules(fr: pd.Series, cost_rt_bps: float = 30.0) -> list[dict]:
    m7 = fr.rolling(21).mean()
    pct = m7.rolling(540, min_periods=180).rank(pct=True)   # percentil móvel de 180 dias
    out = []
    per_year = 3 * 365.25
    for enter, exit_ in ((0.60, 0.30), (0.70, 0.40), (0.80, 0.50)):
        pos = np.zeros(len(fr))
        inpos = False
        for i, p in enumerate(pct.to_numpy()):
            if np.isnan(p):
                continue
            if not inpos and p > enter:
                inpos = True
            elif inpos and p < exit_:
                inpos = False
            pos[i] = 1.0 if inpos else 0.0
        pnl = pos * fr.to_numpy()
        turns = np.abs(np.diff(np.concatenate(([0.0], pos)))).sum()
        cost = turns * cost_rt_bps / 2 / 1e4
        years = len(fr) / per_year
        gross = float(pnl.sum()); net = gross - cost
        monthly = pd.Series(pnl, index=fr.index).resample("1ME").sum()
        out.append({"regra": f"entra > p{int(enter*100)}, sai < p{int(exit_*100)}", "tempo_posicionado": round(float(pos.mean()), 2),
                    "entradas": int(turns / 2), "bruto_aa": round(gross / years, 4), "liquido_aa": round(net / years, 4),
                    "pior_mes": round(float(monthly.min()), 4), "meses_negativos": int((monthly < 0).sum())})
    out.append({"regra": "sempre posicionado", "tempo_posicionado": 1.0, "entradas": 1, "bruto_aa": round(float(fr.mean() * per_year), 4),
                "liquido_aa": round(float(fr.mean() * per_year) - cost_rt_bps / 1e4 / (len(fr) / per_year), 4),
                "pior_mes": round(float(fr.resample("1ME").sum().min()), 4), "meses_negativos": int((fr.resample("1ME").sum() < 0).sum())})
    return out


def funding_as_cost(fr: pd.Series) -> list[dict]:
    out = []
    specs = [("tsmom", "4h", {"lookback": 24, "vol_target": 0.5}), ("tsmom", "4h", {"lookback": 96, "vol_target": None}),
             ("sma_cross", "1d", {"fast": 10, "slow": 100, "mode": "lo"}), ("sma_cross", "1d", {"fast": 20, "slow": 100, "mode": "ls"}),
             ("buy_hold", "1d", {})]
    for name, tf, params in specs:
        bars = load_bars("BTCUSDT-BINANCE", tf, "2019-06-01", "2024-01-01")
        tfm = {"4h": 240, "1d": 1440}[tf]
        ctx = Context(tf, tfm, 525960 / tfm if tf != "1d" else 365.25, 1440 / tfm)
        tgt = REGISTRY[name].positions(bars, params, ctx)
        sl = bars.index >= pd.Timestamp("2020-01-01", tz="UTC")
        b, t = bars[sl], tgt[sl]
        f = funding_per_bar(b, fr)
        res0 = run_backtest(b, t, SCENARIOS["base"], tfm)
        res1 = run_backtest(b, t, SCENARIOS["base"], tfm, funding=f)
        d0, d1 = aggregate_daily(res0.net, b.index), aggregate_daily(res1.net, b.index)
        yrs = len(d0) / 365.25
        out.append({"estrategia": f"{name} {tf} {params}", "sharpe_sem_funding": round(sharpe(d0.to_numpy(), 365.25), 2),
                    "sharpe_com_funding": round(sharpe(d1.to_numpy(), 365.25), 2),
                    "cagr_sem": round(float(np.prod(1 + d0) ** (1 / yrs) - 1), 4), "cagr_com": round(float(np.prod(1 + d1) ** (1 / yrs) - 1), 4),
                    "funding_pago_aa": round(float((res0.pos * f).sum() / yrs), 4), "exposicao_media": round(float(np.mean(res0.pos)), 2)})
    return out


def contrarian_strategy(b1h: pd.DataFrame, fr: pd.Series, hold_h: int = 24, pct_thr: float = 0.10) -> list[dict]:
    """H023: comprado por `hold_h` horas depois de cada funding abaixo do percentil móvel `pct_thr`
    (janelas sobrepostas se fundem). Avaliado no motor com custos base, pessimista e maker com filtro."""
    from quantlab.execution import FillModel, ExecutionModel
    pct = fr.rolling(270, min_periods=90).rank(pct=True)
    events = fr.index[pct < pct_thr]
    target = np.zeros(len(b1h))
    idx = b1h.index
    for t in events:
        i = idx.searchsorted(t)
        if 0 < i < len(idx):
            target[i: i + hold_h] = 1.0
    sl = (idx >= pd.Timestamp("2020-04-01", tz="UTC")) & (idx < pd.Timestamp("2024-01-01", tz="UTC"))
    b, tgt = b1h[sl], target[sl]
    maker = ExecutionModel("maker", 2.0, 0.0, 0.0, 0.0)
    out = []
    for name, em, fill in (("base", SCENARIOS["base"], None), ("pessimista", SCENARIOS["pessimista"], None), ("maker+filtro", maker, FillModel(adverse_bps=2.0))):
        res = run_backtest(b, tgt, em, 60, fill=fill)
        d = aggregate_daily(res.net, b.index)
        yrs = len(d) / 365.25
        rand = []
        rng = np.random.default_rng(0)
        for _ in range(200):
            k = int(rng.integers(24, len(tgt) - 24))
            r2 = run_backtest(b, np.roll(tgt, k), em, 60, fill=fill, with_trades=False)
            rand.append(sharpe(aggregate_daily(r2.net, b.index).to_numpy(), 365.25))
        sr = sharpe(d.to_numpy(), 365.25)
        out.append({"cenario": name, "sharpe": round(sr, 2), "cagr": round(float(np.prod(1 + d) ** (1 / yrs) - 1), 4),
                    "trades": int(len(res.trades)), "exposicao": round(float(np.mean(np.abs(res.pos) > 0)), 2),
                    "p_shift": round(float(np.mean(np.asarray(rand) >= sr)), 3), "mdd": round(float((np.cumprod(1 + d) / np.maximum.accumulate(np.cumprod(1 + d)) - 1).min()), 4)})
    return out


def main(out_dir: str | None = None):
    out_dir = out_dir or os.path.join(ROOT, "research")
    fr = load_funding("BTCUSDT", "binance")["funding_rate"]
    b1h = load_bars("BTCUSDT-BINANCE", "1h", "2019-12-01", "2024-01-15")
    ev = event_study(b1h, fr)
    carry = carry_rules(fr)
    cost = funding_as_cost(fr)
    contr = contrarian_strategy(b1h, fr)
    L = ["# Funding do perpétuo BTCUSDT (Binance, 2020-2023): sinal, carry e custo", "",
         f"Funding médio no período: {fr.mean()*1e4:.2f} bps por 8 h, {fr.mean()*3*365.25:.1%} ao ano. {len(fr)} pagamentos.", "",
         "## 1. Funding como sinal (H016): retorno após funding em percentil extremo (percentil móvel de 90 dias)", "",
         "| bucket | horizonte | retorno médio (bps) | t | n | consistência entre anos |", "|---|---|---|---|---|---|"]
    for r in ev:
        L.append(f"| {r['bucket']} | {r['horizon_h']}h | {r['mean_bps']:+.1f} | {r['t']:+.1f} | {r['n']} | {r['year_consistency']:.0%} |")
    L += ["", "## 2. Carry com regra de percentil (H017): só o funding recebido, 30 bps por entrada e saída, sem P&L da base e sem liquidação", "",
          "| regra | tempo posicionado | entradas | bruto a.a. | líquido a.a. | pior mês | meses negativos |", "|---|---|---|---|---|---|---|"]
    for r in carry:
        L.append(f"| {r['regra']} | {r['tempo_posicionado']:.0%} | {r['entradas']} | {r['bruto_aa']:+.1%} | {r['liquido_aa']:+.1%} | {r['pior_mes']:+.2%} | {r['meses_negativos']} |")
    L += ["", "## 3. Funding como custo (H018): estratégia sempre comprada paga o funding (2020-2023, custos base)", "",
          "| estratégia | exposição média | funding pago a.a. | Sharpe sem | Sharpe com | CAGR sem | CAGR com |", "|---|---|---|---|---|---|---|"]
    for r in cost:
        L.append(f"| {r['estrategia']} | {r['exposicao_media']:.2f} | {r['funding_pago_aa']:.1%} | {r['sharpe_sem_funding']:+.2f} | {r['sharpe_com_funding']:+.2f} | {r['cagr_sem']:+.1%} | {r['cagr_com']:+.1%} |")
    L += ["", "## 4. Estratégia contrária ao funding negativo (H023): comprado 24 h após cada funding abaixo do percentil 10 móvel, abril/2020 a 2023", "",
          "| cenário | Sharpe | CAGR | trades | exposição | drawdown | p contra deslocamento |", "|---|---|---|---|---|---|---|"]
    for r in contr:
        L.append(f"| {r['cenario']} | {r['sharpe']:+.2f} | {r['cagr']:+.1%} | {r['trades']} | {r['exposicao']:.0%} | {r['mdd']:.0%} | {r['p_shift']:.3f} |")
    L.append("")
    with open(os.path.join(out_dir, "funding.md"), "w") as f:
        f.write("\n".join(L))
    return ev, carry, cost


if __name__ == "__main__":
    ev, carry, cost = main()
    print(open(os.path.join(ROOT, "research", "funding.md")).read())

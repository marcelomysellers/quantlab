"""Resíduo de altcoins contra BTC (hipótese H020, proposta de Frey).

Carteira diária, dólar-neutra e beta-neutra, com 9 alts da Binance:
- beta de cada alt ao BTC por regressão móvel de 60 dias (só passado);
- resíduo = retorno do alt − beta × retorno do BTC;
- sinais no fechamento de t: reversão do resíduo de 3 dias (−soma), momentum do resíduo de 28 dias
  excluindo os 3 últimos, e momentum de preço bruto de 28 dias;
- pesos = z-score do sinal entre os ativos do dia, normalizados para soma de |w| = 1, mais uma perna
  em BTC de −Σ beta_i w_i; retorno de open[t+1] a open[t+2]; custo por perna sobre o giro.
Nulo: o sinal é embaralhado entre os ativos a cada dia (300 vezes). Treino 2020-2023, confirmação
2024-2025; 2026 lacrado.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy import stats

from quantlab.backtest.metrics import max_drawdown, sharpe
from quantlab.research.ic_panel import SYMBOLS, load_1h

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRAIN = ("2020-01-01", "2024-01-01")
CONFIRM = ("2024-01-01", "2026-01-01")


def daily_opens(symbols: list[str]) -> pd.DataFrame:
    cols = {}
    for s in symbols:
        try:
            b = load_1h(s)
        except FileNotFoundError:
            continue
        cols[s] = b["open"].resample("1D").first()
    return pd.DataFrame(cols)


def signals(opens: pd.DataFrame, btc: str = "BTCUSDT") -> dict[str, pd.DataFrame]:
    lp = np.log(opens)
    r = lp.diff()                       # retorno do dia d = open[d] / open[d-1], conhecido na abertura de d
    rb = r[btc]
    alts = [c for c in opens.columns if c != btc]
    # beta móvel de 60 dias, só passado
    cov = r[alts].rolling(60).cov(rb)
    var = rb.rolling(60).var()
    beta = cov.div(var, axis=0)
    resid = r[alts] - beta.mul(rb, axis=0)
    sig = {
        "rev_resid_3d": -resid.rolling(3).sum(),
        "mom_resid_4w": resid.rolling(28).sum() - resid.rolling(3).sum(),
        "mom_price_4w": r[alts].rolling(28).sum() - r[alts].rolling(3).sum(),
    }
    return {"r": r, "beta": beta, "resid": resid, "signals": sig, "alts": alts}


def daily_ic(sig: pd.DataFrame, fwd_resid: pd.DataFrame, min_assets: int) -> pd.Series:
    """Spearman por dia entre o sinal e o resíduo futuro, vetorizado (postos por linha entre os ativos válidos)."""
    mask = sig.notna() & fwd_resid.notna()
    a = sig.where(mask).rank(axis=1)
    b = fwd_resid.where(mask).rank(axis=1)
    n = mask.sum(axis=1)
    am = a.sub(a.mean(axis=1), axis=0)
    bm = b.sub(b.mean(axis=1), axis=0)
    ic = (am * bm).sum(axis=1) / np.sqrt((am ** 2).sum(axis=1) * (bm ** 2).sum(axis=1))
    return ic[n >= min_assets].dropna()


def backtest(sig: pd.DataFrame, r: pd.DataFrame, beta: pd.DataFrame, resid: pd.DataFrame, alts: list[str],
             cost_bps: float, btc: str = "BTCUSDT", min_assets: int = 6, with_ic: bool = True) -> dict:
    """Sinal observado na abertura de d (dados até open[d]); posição de open[d+1] a open[d+2]
    equivale a aplicar o retorno r[d+2]. Mantemos uma barra de folga para execução."""
    z = sig.sub(sig.mean(axis=1), axis=0).div(sig.std(axis=1), axis=0)
    w = z.div(z.abs().sum(axis=1), axis=0)
    ok = z.notna().sum(axis=1) >= min_assets
    w[~ok] = 0.0
    w = w.fillna(0.0)
    hedge = -(beta.fillna(0.0) * w).sum(axis=1)
    fwd = r.shift(-2)                     # retorno capturado por uma posição montada em open[d+1]
    pnl_alts = (w * fwd[alts]).sum(axis=1)
    pnl_hedge = hedge * fwd[btc]
    gross = pnl_alts + pnl_hedge
    turnover = (w.diff().abs().sum(axis=1) + hedge.diff().abs()).fillna(0.0)
    net = gross - turnover * cost_bps / 1e4
    ic = daily_ic(sig, resid.shift(-2), min_assets) if with_ic else pd.Series(dtype=float)
    g = gross.dropna()
    beta_expost = float(np.corrcoef(g, fwd[btc].reindex(g.index).fillna(0))[0, 1]) if len(g) > 30 else np.nan
    return {"net": net, "gross": gross, "turnover": turnover, "ic": ic, "beta_expost_corr": beta_expost}


def summarize(res: dict, start: str, end: str) -> dict:
    sl = lambda s: s[(s.index >= pd.Timestamp(start, tz="UTC")) & (s.index < pd.Timestamp(end, tz="UTC"))]
    net, to = sl(res["net"]).dropna(), sl(res["turnover"])
    ic = sl(res["ic"]).dropna() if len(res["ic"]) else res["ic"]
    if len(net) < 60:
        return {}
    eq = np.cumprod(1 + net.to_numpy())
    yrs = len(net) / 365.25
    out = {"sharpe": round(sharpe(net.to_numpy(), 365.25), 2), "cagr": round(float(eq[-1] ** (1 / yrs) - 1), 4),
           "mdd": round(max_drawdown(eq)[0], 4), "n_days": int(len(net)), "turnover_day": round(float(to.mean()), 3)}
    if len(ic) > 10:
        out.update({"ic_mean": round(float(ic.mean()), 4), "ic_t": round(float(ic.mean() / (ic.std(ddof=1) / np.sqrt(len(ic)))), 2)})
    return out


def shuffle_null(sig: pd.DataFrame, r, beta, resid, alts, cost_bps, start, end, n: int = 200, seed: int = 0) -> list[float]:
    """Embaralha o sinal entre os ativos válidos de cada dia; mede só o Sharpe líquido no treino."""
    rng = np.random.default_rng(seed)
    vals = sig.to_numpy()
    valid = [np.where(~np.isnan(row))[0] for row in vals]
    out = []
    for _ in range(n):
        shuffled = vals.copy()
        for i, idx in enumerate(valid):
            if len(idx) > 1:
                shuffled[i, idx] = vals[i, idx][rng.permutation(len(idx))]
        s2 = pd.DataFrame(shuffled, index=sig.index, columns=sig.columns)
        res = backtest(s2, r, beta, resid, alts, cost_bps, with_ic=False)
        st = summarize(res, start, end)
        out.append(st.get("sharpe", np.nan))
    return out


def main(out_dir: str | None = None, n_null: int = 200):
    out_dir = out_dir or os.path.join(ROOT, "research")
    opens = daily_opens(SYMBOLS)
    d = signals(opens)
    rows = []
    for name, sig in d["signals"].items():
        for cost in (14.0, 4.0):
            res = backtest(sig, d["r"], d["beta"], d["resid"], d["alts"], cost)
            tr, cf = summarize(res, *TRAIN), summarize(res, *CONFIRM)
            null = shuffle_null(sig, d["r"], d["beta"], d["resid"], d["alts"], cost, *TRAIN, n=n_null) if cost == 14.0 else []
            p = float(np.mean(np.asarray(null) >= tr.get("sharpe", -9))) if null else None
            rows.append({"sinal": name, "custo_bps": cost, "treino": tr, "confirmacao": cf, "p_null": p,
                         "beta_expost_corr": round(res["beta_expost_corr"], 3), "null_sharpes": null})
    L = ["# Resíduo de altcoins contra BTC (H020): carteira diária dólar-neutra e beta-neutra, 9 alts da Binance", "",
         f"Ativos: {', '.join(d['alts'])}. Treino 2020-2023, confirmação 2024-2025, 2026 lacrado. Custo por perna sobre o giro diário.",
         "Nulo: sinal embaralhado entre os ativos a cada dia. Regra pré-registrada: IC > 0,02 com t > 3, Sharpe líquido > 1, p < 0,05.", "",
         "| sinal | custo | Sharpe treino | CAGR treino | DD treino | IC treino | t(IC) | giro/dia | p nulo | Sharpe confirm. | IC confirm. | t confirm. | corr. c/ BTC |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        tr, cf = r["treino"], r["confirmacao"]
        L.append(f"| {r['sinal']} | {r['custo_bps']:.0f} bps | {tr.get('sharpe', float('nan')):+.2f} | {tr.get('cagr', 0):+.1%} | {tr.get('mdd', 0):.0%} | {tr.get('ic_mean', 0):+.3f} | {tr.get('ic_t', 0):+.1f} | {tr.get('turnover_day', 0):.2f} | {('%.3f' % r['p_null']) if r['p_null'] is not None else '–'} | {cf.get('sharpe', float('nan')):+.2f} | {cf.get('ic_mean', 0):+.3f} | {cf.get('ic_t', 0):+.1f} | {r['beta_expost_corr']:+.2f} |")
    L.append("")
    with open(os.path.join(out_dir, "altcoins_residuo.md"), "w") as f:
        f.write("\n".join(L))
    return rows


if __name__ == "__main__":
    rows = main()
    print(open(os.path.join(ROOT, "research", "altcoins_residuo.md")).read())

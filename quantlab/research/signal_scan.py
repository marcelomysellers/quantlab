"""Varredura de sinais: mede sinais, não estratégias (a lição de Mercer).

Para cada feature e cada horizonte: correlação de Spearman (IC) com o retorno futuro,
p-valor por permutação circular (preserva a autocorrelação da feature), IC por ano
(estabilidade), consistência de sinal entre anos e spread entre quintis extremos.

Alinhamento sem lookahead: a feature do dia t usa dados até o fechamento de t; o retorno
futuro é medido de t+LAG a t+LAG+h. LAG = 2 porque o diário da CoinMetrics fecha 27 a 30 horas
depois das 00:00 UTC e a história é recalculada (não é point-in-time): usar o dado do dia t no
dia t+1 seria lookahead.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HORIZONS = (1, 5, 10, 21)
LAG = 2


def zscore(s: pd.Series, window: int) -> pd.Series:
    return (s - s.rolling(window).mean()) / s.rolling(window).std()


def load_coinmetrics(path: str | None = None) -> pd.DataFrame:
    path = path or os.path.join(ROOT, "data", "raw", "coinmetrics_btc_daily.csv")
    df = pd.read_csv(path, low_memory=False)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()
    return df.dropna(subset=["PriceUSD"])


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    p = df["PriceUSD"]
    lp = np.log(p)
    f = pd.DataFrame(index=df.index)
    # preço (referência)
    f["mom_30d"] = lp - lp.shift(30)
    f["mom_90d"] = lp - lp.shift(90)
    f["rev_5d"] = -(lp - lp.shift(5))
    f["vol_30d"] = lp.diff().rolling(30).std()
    # on-chain
    f["mvrv_z365"] = zscore(df["CapMVRVCur"], 365)
    netflow = (df["FlowInExUSD"] - df["FlowOutExUSD"]).rolling(7).sum() / df["CapMrktCurUSD"]
    f["exch_netflow_z"] = zscore(netflow, 365)
    f["sply_ex_chg30"] = np.log(df["SplyExNtv"]) - np.log(df["SplyExNtv"]).shift(30)
    f["adr_act_mom"] = np.log(df["AdrActCnt"].rolling(7).mean() / df["AdrActCnt"].rolling(90).mean())
    f["tx_mom"] = np.log(df["TxCnt"].rolling(7).mean() / df["TxCnt"].rolling(90).mean())
    hr = df["HashRate"].rolling(7).mean()
    f["hash_chg30"] = np.log(hr / hr.shift(30))
    f["nvt_spot_z"] = zscore(np.log(df["CapMrktCurUSD"] / df["volume_reported_spot_usd_1d"].rolling(30).mean()), 365)
    f["vol_spot_z90"] = zscore(np.log(df["volume_reported_spot_usd_1d"]), 90)
    f["fee_mom"] = np.log(df["FeeTotNtv"].rolling(7).mean() / df["FeeTotNtv"].rolling(90).mean())
    f["adr_bal_chg30"] = np.log(df["AdrBalCnt"]) - np.log(df["AdrBalCnt"]).shift(30)
    return f.replace([np.inf, -np.inf], np.nan)


def forward_returns(price: pd.Series, horizons=HORIZONS) -> pd.DataFrame:
    lp = np.log(price)
    return pd.DataFrame({f"fwd_{h}d": lp.shift(-(h + LAG)) - lp.shift(-LAG) for h in horizons}, index=price.index)


def ic(x: np.ndarray, y: np.ndarray) -> float:
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 30:
        return np.nan
    return float(stats.spearmanr(x[m], y[m]).statistic)


def perm_pvalue(x: np.ndarray, y: np.ndarray, actual: float, n: int = 500, seed: int = 0) -> float:
    """Permutação circular: desloca a feature no tempo e recalcula o IC."""
    rng = np.random.default_rng(seed)
    L = len(x)
    out = np.empty(n)
    for i in range(n):
        k = int(rng.integers(30, L - 30))
        out[i] = ic(np.roll(x, k), y)
    return float(np.mean(np.abs(out) >= abs(actual)))


def quintile_spread(x: pd.Series, y: pd.Series) -> float:
    d = pd.concat([x, y], axis=1).dropna()
    if len(d) < 100:
        return np.nan
    q = pd.qcut(d.iloc[:, 0].rank(method="first"), 5, labels=False)
    return float(d.iloc[:, 1][q == 4].mean() - d.iloc[:, 1][q == 0].mean())


def scan(features: pd.DataFrame, fwd: pd.DataFrame, start: str, end: str, n_perm: int = 500) -> pd.DataFrame:
    sl = (features.index >= pd.Timestamp(start)) & (features.index < pd.Timestamp(end))
    F, Y = features[sl], fwd[sl]
    years = sorted(set(F.index.year))
    rows = []
    for col in F.columns:
        for h in HORIZONS:
            x, y = F[col].to_numpy(dtype=float), Y[f"fwd_{h}d"].to_numpy(dtype=float)
            full = ic(x, y)
            if np.isnan(full):
                continue
            p = perm_pvalue(x, y, full, n_perm)
            by_year = {}
            for yr in years:
                m = F.index.year == yr
                by_year[yr] = ic(x[m], y[m])
            vals = [v for v in by_year.values() if not np.isnan(v)]
            consist = float(np.mean([np.sign(v) == np.sign(full) for v in vals])) if vals else np.nan
            rows.append({
                "feature": col, "horizon_d": h, "ic": round(full, 4), "p_perm": round(p, 3),
                "consistencia_anos": round(consist, 2), "n_anos": len(vals),
                "spread_q5_q1_pct": round(100 * quintile_spread(F[col], Y[f"fwd_{h}d"]), 2),
                "ic_por_ano": {str(k): (None if np.isnan(v) else round(v, 3)) for k, v in by_year.items()},
            })
    out = pd.DataFrame(rows)
    return out.sort_values(["p_perm", "ic"], ascending=[True, False]).reset_index(drop=True)


def to_markdown(res: pd.DataFrame, start: str, end: str, n_tests: int) -> str:
    lines = [f"# Varredura de sinais on-chain e de preço (BTC, diário, {start} a {end})", "",
             f"Defasagem de {LAG} dias entre o dado e a primeira exposição (CoinMetrics não é point-in-time).", "",
             f"{n_tests} testes (features × horizontes). Ao nível de 5%, esperam-se ~{n_tests * 0.05:.1f} falsos positivos por acaso; "
             "só vale olhar o que tem p < 0,01, consistência de sinal entre anos e spread que pague custo.", "",
             "| feature | horizonte | IC | p (perm.) | consistência entre anos | spread Q5−Q1 | IC por ano |", "|---|---|---|---|---|---|---|"]
    for r in res.itertuples():
        por_ano = " ".join(f"{k[2:]}:{'–' if v is None else f'{v:+.2f}'}" for k, v in r.ic_por_ano.items())
        lines.append(f"| {r.feature} | {r.horizon_d}d | {r.ic:+.3f} | {r.p_perm:.3f} | {r.consistencia_anos:.0%} ({r.n_anos} anos) | {r.spread_q5_q1_pct:+.2f}% | {por_ano} |")
    return "\n".join(lines) + "\n"


def main(start: str = "2017-01-01", end: str = "2026-05-24", out_dir: str | None = None, n_perm: int = 500):
    out_dir = out_dir or os.path.join(ROOT, "research")
    os.makedirs(out_dir, exist_ok=True)
    df = load_coinmetrics()
    feats = build_features(df)
    fwd = forward_returns(df["PriceUSD"])
    res = scan(feats, fwd, start, end, n_perm)
    n_tests = len(res)
    with open(os.path.join(out_dir, "signal_scan_coinmetrics.md"), "w") as f:
        f.write(to_markdown(res, start, end, n_tests))
    res.to_json(os.path.join(out_dir, "signal_scan_coinmetrics.json"), orient="records", indent=1)
    return res


if __name__ == "__main__":
    import sys
    r = main(*(sys.argv[1:3]))
    cols = ["feature", "horizon_d", "ic", "p_perm", "consistencia_anos", "spread_q5_q1_pct"]
    print(r[cols].head(25).to_string(index=False))
    print(f"... {len(r)} testes; com p<0.01: {(r.p_perm < 0.01).sum()}; com p<0.05: {(r.p_perm < 0.05).sum()}")

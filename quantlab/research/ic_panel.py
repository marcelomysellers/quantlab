"""Painel de IC pré-registrado (hipóteses H014 e H015 em research/hipoteses.md).

Mede sinais, não estratégias: para cada feature e horizonte, a correlação de postos (Spearman)
entre o valor da feature no fechamento da barra t e o retorno de open[t+1] a open[t+1+h], por mês.
Estatística = média dos IC mensais, t = média/(desvio/raiz(n_meses)), % de meses positivos.
Períodos: treino 2020-2023, confirmação 2024-2025; 2026 fica lacrado (não é calculado).
Regra de aprovação, escrita antes de rodar: |t| > 3 no treino, sobrevive a Benjamini-Hochberg 10%,
mesmo sinal e |t| > 2 na confirmação.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from scipy import stats

from quantlab.data.binance_github import SRC as BINANCE_SRC
from quantlab.data.funding import load_funding
from quantlab.data.store import load_bars
from quantlab.research.signal_scan import build_features as onchain_features, load_coinmetrics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HORIZONS = (1, 4, 12, 24, 72)
# features correlacionadas contam como UMA aposta no veredito (Patterson): cluster = família do sinal
CLUSTER = {"ret_1h": "reversão curta", "ret_4h": "reversão curta", "ret_24h": "reversão curta", "ret_24h_vol": "reversão curta",
           "pos_range_24h": "reversão curta", "pos_range_168h": "reversão semanal", "ret_72h": "reversão semanal", "ret_168h": "reversão semanal",
           "vol_ratio_24_168": "volatilidade", "rng_1h_atr": "volatilidade", "z_vol_1h_30d": "volume", "z_vol_24h_90d": "volume",
           "vol_trend_24_168": "volume", "amihud_24h_z": "liquidez", "dvol_24h_z": "volume", "funding_last": "funding", "funding_sum_3d": "funding",
           "funding_z_30d": "funding", "funding_x_ret24": "funding", "btc_ret_24h": "cruzado", "ethbtc_ret_24h": "cruzado",
           "exch_netflow_z": "on-chain fluxo", "sply_ex_chg30": "on-chain fluxo", "mvrv_z365": "on-chain valuation", "adr_act_mom": "on-chain atividade"}
TRAIN = ("2020-01-01", "2024-01-01")
CONFIRM = ("2024-01-01", "2026-01-01")
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT", "DOGEUSDT", "ZECUSDT", "ADAUSDT", "BCHUSDT"]


def z(s: pd.Series, w: int) -> pd.Series:
    return (s - s.rolling(w).mean()) / s.rolling(w).std()


def load_1h(symbol: str) -> pd.DataFrame:
    """Barras de 1 hora: BTC do store (derivado do 1m), demais símbolos do parquet 1h do GitHub."""
    if symbol == "BTCUSDT":
        return load_bars("BTCUSDT-BINANCE", "1h")[["open", "high", "low", "close", "volume"]]
    import glob
    files = sorted(glob.glob(os.path.join(BINANCE_SRC, "interval_id=1h", f"symbol_id={symbol}", "year=*", "month=*", "*.parquet")))
    frames = []
    for f in files:
        with open(f, "rb") as fh:
            if fh.read(4) != b"PAR1":
                continue
        frames.append(pd.read_parquet(f, columns=["timestamp", "open", "high", "low", "close", "volume"]))
    if not frames:
        raise FileNotFoundError(symbol)
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.drop_duplicates("ts").sort_values("ts").set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float)
    full = pd.date_range(df.index[0], df.index[-1], freq="1h", tz="UTC")
    df = df.reindex(full)
    df["close"] = df["close"].ffill()
    for c in ("open", "high", "low"):
        df[c] = df[c].fillna(df["close"])
    df["volume"] = df["volume"].fillna(0.0)
    df.index.name = "ts"
    return df


def price_volume_features(b: pd.DataFrame) -> pd.DataFrame:
    lp = np.log(b["close"])
    r = lp.diff()
    f = pd.DataFrame(index=b.index)
    for h in (1, 4, 24, 72, 168):
        f[f"ret_{h}h"] = lp - lp.shift(h)
    vol24 = r.rolling(24).std()
    f["ret_24h_vol"] = f["ret_24h"] / (vol24 * np.sqrt(24))
    for w in (24, 168):
        lo, hi = b["low"].rolling(w).min(), b["high"].rolling(w).max()
        f[f"pos_range_{w}h"] = (b["close"] - lo) / (hi - lo)
    f["vol_ratio_24_168"] = vol24 / r.rolling(168).std()
    rng = (b["high"] - b["low"]) / b["close"]
    f["rng_1h_atr"] = rng / rng.rolling(24).mean()
    lv = np.log1p(b["volume"])
    f["z_vol_1h_30d"] = z(lv, 720)
    v24 = b["volume"].rolling(24).sum()
    f["z_vol_24h_90d"] = z(np.log1p(v24), 2160)
    f["vol_trend_24_168"] = np.log1p(b["volume"].rolling(24).mean()) - np.log1p(b["volume"].rolling(168).mean())
    amihud = (r.abs() / (b["volume"] * b["close"] + 1e-9)).rolling(24).mean()
    f["amihud_24h_z"] = z(np.log(amihud + 1e-18), 720)
    f["dvol_24h_z"] = z(np.log1p((b["volume"] * b["close"]).rolling(24).sum()), 2160)
    return f.replace([np.inf, -np.inf], np.nan)


def funding_features(b: pd.DataFrame, fr: pd.DataFrame, ret_24h: pd.Series) -> pd.DataFrame:
    """Funding a cada 8 h, conhecido no instante do pagamento; propagado para as horas seguintes."""
    s = fr["funding_rate"].sort_index()
    f8 = pd.DataFrame({"funding_last": s, "funding_sum_3d": s.rolling(9).sum(), "funding_z_30d": z(s, 90)})
    f = f8.reindex(b.index, method="ffill")
    f.loc[b.index < s.index[0], :] = np.nan
    f.loc[b.index > s.index[-1] + pd.Timedelta(hours=8), :] = np.nan
    f["funding_x_ret24"] = f["funding_last"] * np.sign(ret_24h)
    return f


def onchain_hourly(b: pd.DataFrame) -> pd.DataFrame:
    """On-chain diário da CoinMetrics com 2 dias de defasagem (não é point-in-time), propagado por hora."""
    cm = load_coinmetrics()
    feats = onchain_features(cm)[["exch_netflow_z", "sply_ex_chg30", "mvrv_z365", "adr_act_mom"]]
    feats.index = feats.index.tz_localize("UTC") + pd.Timedelta(days=2)
    return feats.reindex(b.index, method="ffill")


def forward_returns(b: pd.DataFrame) -> pd.DataFrame:
    lo = np.log(b["open"])
    return pd.DataFrame({f"fwd_{h}": lo.shift(-(1 + h)) - lo.shift(-1) for h in HORIZONS}, index=b.index)


def monthly_ic(x: pd.Series, y: pd.Series) -> pd.Series:
    d = pd.concat([x, y], axis=1).dropna()
    d.columns = ["x", "y"]
    if len(d) < 200:
        return pd.Series(dtype=float)
    out = {}
    for m, g in d.groupby(d.index.tz_convert(None).to_period("M")):
        if len(g) >= 100 and g["x"].nunique() > 10:
            out[m] = stats.spearmanr(g["x"], g["y"]).statistic
    return pd.Series(out, dtype=float)


def ic_stats(ic_m: pd.Series) -> dict:
    ic_m = ic_m.dropna()
    n = len(ic_m)
    if n < 6:
        return {"ic": np.nan, "t": np.nan, "pct_pos": np.nan, "n_months": n}
    mean, sd = float(ic_m.mean()), float(ic_m.std(ddof=1))
    t = mean / (sd / np.sqrt(n)) if sd > 0 else 0.0
    return {"ic": round(mean, 4), "t": round(float(t), 2), "pct_pos": round(float((ic_m > 0).mean()), 2), "n_months": n}


def bh_fdr(p: np.ndarray, q: float = 0.10) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    ok = np.zeros(len(p), dtype=bool)
    valid = ~np.isnan(p)
    if valid.sum() == 0:
        return ok
    idx = np.where(valid)[0]
    order = idx[np.argsort(p[idx])]
    m = len(order)
    thresh = q * (np.arange(1, m + 1) / m)
    passed = p[order] <= thresh
    if passed.any():
        k = np.max(np.where(passed)[0])
        ok[order[: k + 1]] = True
    return ok


def build_symbol_frame(symbol: str, btc_b: pd.DataFrame | None, eth_b: pd.DataFrame | None, fr: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    b = load_1h(symbol)
    f = price_volume_features(b)
    if symbol == "BTCUSDT":
        if fr is not None:
            f = pd.concat([f, funding_features(b, fr, f["ret_24h"])], axis=1)
        f = pd.concat([f, onchain_hourly(b)], axis=1)
        if eth_b is not None:
            le = np.log(eth_b["close"]).reindex(b.index, method="ffill")
            f["ethbtc_ret_24h"] = (le - le.shift(24)) - f["ret_24h"]
    else:
        lb = np.log(btc_b["close"]).reindex(b.index, method="ffill")
        f["btc_ret_24h"] = lb - lb.shift(24)
    return f, forward_returns(b)


def run_scope(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame]], scope: str, features: list[str]) -> list[dict]:
    rows = []
    for feat in features:
        for h in HORIZONS:
            for period_name, (a, bnd) in (("treino", TRAIN), ("confirmacao", CONFIRM)):
                xs, ys, per_symbol_sign = [], [], []
                for sym, (f, y) in frames.items():
                    if feat not in f:
                        continue
                    sl = (f.index >= pd.Timestamp(a, tz="UTC")) & (f.index < pd.Timestamp(bnd, tz="UTC"))
                    x_s, y_s = f.loc[sl, feat], y.loc[sl, f"fwd_{h}"]
                    xs.append(x_s.rename("x")); ys.append(y_s.rename("y"))
                    st = ic_stats(monthly_ic(x_s, y_s))
                    if not np.isnan(st["ic"]):
                        per_symbol_sign.append(np.sign(st["ic"]))
                if not xs:
                    continue
                # painel: IC mensal com postos agrupados entre símbolos
                X = pd.concat(xs); Y = pd.concat(ys)
                d = pd.DataFrame({"x": X.to_numpy(), "y": Y.to_numpy()}, index=X.index).dropna()
                out = {}
                for m, g in d.groupby(d.index.tz_convert(None).to_period("M")):
                    if len(g) >= 100 and g["x"].nunique() > 10:
                        out[m] = stats.spearmanr(g["x"], g["y"]).statistic
                st = ic_stats(pd.Series(out, dtype=float))
                # robustez: linhas a cada h barras (retornos futuros sem sobreposição), agrupadas por mês (h<=12) ou trimestre
                d_no = d.iloc[::h] if h > 1 else d
                grp = d_no.index.tz_convert(None).to_period("M") if h <= 12 else d_no.index.tz_convert(None).to_period("Q")
                out2 = {}
                for m, g in d_no.groupby(grp):
                    if len(g) >= (60 if h <= 12 else 25) and g["x"].nunique() > 10:
                        out2[m] = stats.spearmanr(g["x"], g["y"]).statistic
                st2 = ic_stats(pd.Series(out2, dtype=float))
                consist = float(np.mean(np.array(per_symbol_sign) == np.sign(st["ic"]))) if per_symbol_sign and not np.isnan(st["ic"]) else np.nan
                rows.append({"scope": scope, "feature": feat, "horizon_h": h, "period": period_name, **st,
                             "ic_nonoverlap": st2["ic"], "t_nonoverlap": st2["t"], "n_groups_nonoverlap": st2["n_months"],
                             "symbol_consistency": None if np.isnan(consist) else round(consist, 2), "n_symbols": len(xs)})
    return rows


def evaluate(rows: list[dict]) -> list[dict]:
    """Aplica a regra pré-registrada por escopo: BH-FDR 10% nos t do treino; confirmação com mesmo sinal e |t|>2."""
    df = pd.DataFrame(rows)
    df["p"] = 2 * (1 - stats.norm.cdf(df["t"].abs()))
    df["bh_pass"] = False
    df["aprovada"] = False
    for scope, g in df[df["period"] == "treino"].groupby("scope"):
        mask = bh_fdr(g["p"].to_numpy(), 0.10)
        df.loc[g.index, "bh_pass"] = mask
    tr = df[df["period"] == "treino"].set_index(["scope", "feature", "horizon_h"])
    cf = df[df["period"] == "confirmacao"].set_index(["scope", "feature", "horizon_h"])
    for key, r in tr.iterrows():
        if key in cf.index:
            c = cf.loc[key]
            ok = bool(r["bh_pass"] and abs(r["t"]) > 3 and abs(c["t"]) > 2 and np.sign(c["ic"]) == np.sign(r["ic"])
                      and (np.isnan(r["t_nonoverlap"]) or (abs(r["t_nonoverlap"]) > 2 and np.sign(r["ic_nonoverlap"]) == np.sign(r["ic"]))))
            df.loc[(df["scope"] == key[0]) & (df["feature"] == key[1]) & (df["horizon_h"] == key[2]), "aprovada"] = ok
    return df.to_dict("records")


def calendar_buckets(frames_bars: dict[str, pd.DataFrame], fr: pd.DataFrame | None) -> list[dict]:
    """H015: retorno médio da próxima barra por bucket de calendário, agrupado entre símbolos e anos."""
    rows_all = []
    for sym, b in frames_bars.items():
        lo = np.log(b["open"])
        y = (lo.shift(-2) - lo.shift(-1))                      # retorno da barra após o sinal
        vol = np.log(b["close"]).diff().rolling(168).std()      # em unidades de vol do próprio ativo
        d = pd.DataFrame({"y": y / vol, "hour": b.index.hour, "dow": b.index.dayofweek,
                          "hours_to_funding": (8 - (b.index.hour % 8)) % 8,
                          "us_session": ((b.index.hour >= 13) & (b.index.hour < 20)).astype(int),
                          "year": b.index.year, "sym": sym}, index=b.index)
        d = d[(d.index >= pd.Timestamp(TRAIN[0], tz="UTC")) & (d.index < pd.Timestamp(CONFIRM[1], tz="UTC"))]
        rows_all.append(d.dropna())
    d = pd.concat(rows_all)
    out = []
    for col in ("hour", "dow", "hours_to_funding", "us_session"):
        for val, g in d.groupby(col):
            n = len(g)
            if n < 500:
                continue
            m, sd = g["y"].mean(), g["y"].std(ddof=1)
            t = m / (sd / np.sqrt(n))
            by_year = g.groupby("year")["y"].mean()
            consist = float((np.sign(by_year) == np.sign(m)).mean())
            out.append({"bucket": col, "value": int(val), "mean_vol_units": round(float(m), 4), "t": round(float(t), 2),
                        "n": int(n), "year_consistency": round(consist, 2), "n_years": int(len(by_year))})
    return out


def to_markdown(rows: list[dict], cal: list[dict], n_tests: int, n_symbols: int = 1) -> str:
    df = pd.DataFrame(rows)
    L = ["# Painel de IC pré-registrado (Binance, barras de 1 hora)", "",
         f"{n_tests} testes de IC (feature × horizonte × escopo). Treino 2020-2023, confirmação 2024-2025, 2026 lacrado.",
         "Regra escrita antes de rodar: |t| > 3 no treino, sobrevive a Benjamini-Hochberg 10% dentro do escopo, mesmo sinal e |t| > 2 na confirmação.", ""]
    ap = df[(df["period"] == "treino") & (df["aprovada"])].copy()
    ap["cluster"] = ap["feature"].map(CLUSTER).fillna("outro")
    clusters = sorted(ap["cluster"].unique())
    L.append(f"## Aprovadas: {len(ap)} testes, que são {len(clusters)} apostas distintas: {', '.join(clusters) if clusters else 'nenhuma'}")
    L.append("")
    L.append("Features correlacionadas medem o mesmo efeito; o que conta como evidência é o número de clusters, não de linhas.")
    L.append("")
    if len(ap):
        L += ["| cluster | escopo | feature | horizonte | IC treino | t treino | t sem sobreposição | % meses + | IC confirm. | t confirm. | consistência entre símbolos |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        cf = df[df["period"] == "confirmacao"].set_index(["scope", "feature", "horizon_h"])
        for r in ap.sort_values(["cluster", "feature", "horizon_h"]).itertuples():
            c = cf.loc[(r.scope, r.feature, r.horizon_h)]
            L.append(f"| {r.cluster} | {r.scope} | {r.feature} | {r.horizon_h}h | {r.ic:+.3f} | {r.t:+.1f} | {r.t_nonoverlap:+.1f} | {r.pct_pos:.0%} | {c.ic:+.3f} | {c.t:+.1f} | {r.symbol_consistency} |")
    else:
        L.append("Nenhuma feature passou na regra pré-registrada.")
    L.append("")
    for scope in sorted(df["scope"].unique()):
        L.append(f"## {scope}: os 12 maiores |t| no treino, com a confirmação ao lado")
        L.append("")
        L += ["| feature | horizonte | IC treino | t treino | % meses + | BH 10% | IC confirm. | t confirm. | sinal repete? |", "|---|---|---|---|---|---|---|---|---|"]
        tr = df[(df["scope"] == scope) & (df["period"] == "treino")].copy()
        tr["abst"] = tr["t"].abs()
        cf = df[(df["scope"] == scope) & (df["period"] == "confirmacao")].set_index(["feature", "horizon_h"])
        for r in tr.sort_values("abst", ascending=False).head(12).itertuples():
            c = cf.loc[(r.feature, r.horizon_h)] if (r.feature, r.horizon_h) in cf.index else None
            rep = "–" if c is None or np.isnan(c.ic) else ("sim" if np.sign(c.ic) == np.sign(r.ic) and abs(c.t) > 2 else "não")
            L.append(f"| {r.feature} | {r.horizon_h}h | {r.ic:+.3f} | {r.t:+.1f} | {r.pct_pos:.0%} | {'✓' if r.bh_pass else '✕'} | {('%+.3f' % c.ic) if c is not None else '–'} | {('%+.1f' % c.t) if c is not None else '–'} | {rep} |")
        L.append("")
    L.append(f"## Calendário por bucket (H015), retorno da próxima hora em unidades de volatilidade, {n_symbols} ativo(s) agrupado(s), 2020-2025")
    L.append("")
    L += ["| bucket | valor | média (vol) | t | n | consistência entre anos |", "|---|---|---|---|---|---|"]
    for c in sorted(cal, key=lambda x: -abs(x["t"]))[:15]:
        L.append(f"| {c['bucket']} | {c['value']} | {c['mean_vol_units']:+.4f} | {c['t']:+.1f} | {c['n']} | {c['year_consistency']:.0%} ({c['n_years']} anos) |")
    return "\n".join(L) + "\n"


def main(symbols: list[str] | None = None, out_dir: str | None = None):
    symbols = symbols or SYMBOLS
    out_dir = out_dir or os.path.join(ROOT, "research")
    try:
        fr = load_funding("BTCUSDT", "binance")
    except FileNotFoundError:
        fr = None
    bars = {}
    for s in symbols:
        try:
            bars[s] = load_1h(s)
        except FileNotFoundError:
            print("sem dados:", s)
    btc_b, eth_b = bars.get("BTCUSDT"), bars.get("ETHUSDT")
    frames = {s: build_symbol_frame(s, btc_b, eth_b, fr) for s in bars}
    btc_feats = list(frames["BTCUSDT"][0].columns)
    panel_feats = [c for c in frames[next(s for s in frames if s != "BTCUSDT")][0].columns] if len(frames) > 1 else []
    rows = run_scope({"BTCUSDT": frames["BTCUSDT"]}, "BTC", btc_feats)
    if len(frames) > 1:
        rows += run_scope({s: fr_ for s, fr_ in frames.items() if s != "BTCUSDT"}, "painel_alts", panel_feats)
    rows = evaluate(rows)
    cal = calendar_buckets(bars, fr)
    n_tests = len([r for r in rows if r["period"] == "treino"])
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "painel_ic.md"), "w") as f:
        f.write(to_markdown(rows, cal, n_tests, len(bars)))
    sig_dir = os.path.join(ROOT, "web", "public", "results", "signals")
    os.makedirs(sig_dir, exist_ok=True)
    with open(os.path.join(sig_dir, "painel_ic.json"), "w") as f:
        json.dump({"rows": rows, "calendar": cal, "horizons": list(HORIZONS), "train": TRAIN, "confirm": CONFIRM,
                   "symbols": list(bars), "clusters": CLUSTER, "generated_at": pd.Timestamp.now("UTC").isoformat()}, f, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else (o.item() if hasattr(o, "item") else str(o)))
    return rows, cal


if __name__ == "__main__":
    import sys
    syms = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    rows, cal = main(syms)
    df = pd.DataFrame(rows)
    print("testes:", (df["period"] == "treino").sum(), "| aprovadas:", int(df[df["period"] == "treino"]["aprovada"].sum()))
    tr = df[df["period"] == "treino"].copy(); tr["abst"] = tr["t"].abs()
    print(tr.sort_values("abst", ascending=False).head(12)[["scope", "feature", "horizon_h", "ic", "t", "pct_pos", "bh_pass", "aprovada"]].to_string(index=False))

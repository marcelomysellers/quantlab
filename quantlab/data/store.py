"""Armazenamento e reamostragem de barras.

Esquema padrão: index `ts` (UTC) | open high low close volume [synthetic]
- `load_1m(symbol)`: grade regular de 1 minuto; minutos sem negócio viram barra sintética
  (OHLC = fechamento anterior, volume 0, synthetic=True).
- `load_bars(symbol, tf, start, end)`: reamostra a partir do 1m e guarda cache por timeframe.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from quantlab.instruments import PANDAS_RULE, TF_MINUTES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARQUET_DIR = os.path.join(ROOT, "data", "parquet")


def raw_path(symbol: str) -> str:
    return os.path.join(PARQUET_DIR, f"{symbol}_1m_raw.parquet")


def load_raw_1m(symbol: str) -> pd.DataFrame:
    p = raw_path(symbol)
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} não existe; rode a ingestão (quantlab.data.bitfinex_github ou quantlab.data.binance)")
    return pd.read_parquet(p)


def regularize_1m(raw: pd.DataFrame) -> pd.DataFrame:
    """Grade completa de 1 minuto; minutos faltantes viram barras sintéticas."""
    idx = pd.date_range(raw.index[0].floor("min"), raw.index[-1].floor("min"), freq="1min", tz="UTC")
    df = raw.reindex(idx)
    synthetic = df["close"].isna()
    df["close"] = df["close"].ffill()
    for c in ("open", "high", "low"):
        df[c] = df[c].where(~synthetic, df["close"])
    df["volume"] = df["volume"].fillna(0.0)
    df["synthetic"] = synthetic.values
    df.index.name = "ts"
    return df


def load_1m(symbol: str) -> pd.DataFrame:
    p = os.path.join(PARQUET_DIR, f"{symbol}_1m.parquet")
    if os.path.exists(p):
        return pd.read_parquet(p)
    df = regularize_1m(load_raw_1m(symbol))
    df.to_parquet(p)
    return df


def resample(df1m: pd.DataFrame, tf: str) -> pd.DataFrame:
    if tf == "1m":
        return df1m
    rule = PANDAS_RULE[tf]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    out = df1m.resample(rule, label="left", closed="left").agg(agg)
    if "synthetic" in df1m:
        out["synthetic"] = df1m["synthetic"].resample(rule, label="left", closed="left").min().astype(bool)
    out = out.dropna(subset=["close"])
    out.index.name = "ts"
    return out


def load_bars(symbol: str, tf: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    if tf not in TF_MINUTES:
        raise ValueError(f"timeframe desconhecido: {tf}")
    p = os.path.join(PARQUET_DIR, f"{symbol}_{tf}.parquet")
    if os.path.exists(p):
        df = pd.read_parquet(p)
    else:
        df = resample(load_1m(symbol), tf)
        df.to_parquet(p)
    if start is not None:
        df = df[df.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        df = df[df.index < pd.Timestamp(end, tz="UTC")]
    return df


def quality_report(raw: pd.DataFrame) -> pd.DataFrame:
    """Por ano: barras reais, minutos esperados, % faltante, maior gap, retornos extremos."""
    rows = []
    ts = raw.index
    for year, g in raw.groupby(ts.year):
        expected = int((g.index[-1] - g.index[0]).total_seconds() // 60) + 1
        gaps = np.diff(g.index.values).astype("timedelta64[m]").astype(int)
        r = g["close"].pct_change().abs()
        rows.append({
            "ano": int(year),
            "barras": int(len(g)),
            "esperadas": expected,
            "faltantes_pct": round(100 * (1 - len(g) / expected), 2),
            "maior_gap_min": int(gaps.max()) if len(gaps) else 0,
            "gaps_>60min": int((gaps > 60).sum()),
            "ret1m_max_pct": round(100 * float(r.max()), 2),
            "ret1m_>5pct": int((r > 0.05).sum()),
            "vol_zero_pct": round(100 * float((g["volume"] == 0).mean()), 2),
        })
    return pd.DataFrame(rows)

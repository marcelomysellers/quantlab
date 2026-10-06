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
CACHE_VERSION = 2          # muda quando o esquema das barras derivadas muda
EXTRA_SUM_COLS = ("taker_buy_base", "trades", "quote_volume")


PUBLIC_DIR = os.path.join(ROOT, "data", "public")


def raw_source(symbol: str) -> tuple[str, int]:
    """Caminho do bruto e sua resolução em minutos. Procura 1m e depois 1h, em data/parquet e data/public."""
    for res, minutes in (("1m", 1), ("1h", 60)):
        for d in (PARQUET_DIR, PUBLIC_DIR):
            p = os.path.join(d, f"{symbol}_{res}_raw.parquet")
            if os.path.exists(p):
                return p, minutes
    raise FileNotFoundError(f"nenhum {symbol}_1m_raw.parquet ou {symbol}_1h_raw.parquet em data/parquet ou data/public")


def raw_path(symbol: str) -> str:
    return raw_source(symbol)[0]


def load_raw_1m(symbol: str) -> pd.DataFrame:
    p, minutes = raw_source(symbol)
    if minutes != 1:
        raise FileNotFoundError(f"{symbol} só tem bruto de {minutes} min; use load_bars com timeframe >= 1h")
    return pd.read_parquet(p)


def regularize_1m(raw: pd.DataFrame, minutes: int = 1) -> pd.DataFrame:
    """Grade completa na resolução do bruto; barras faltantes viram barras sintéticas."""
    freq = f"{minutes}min"
    idx = pd.date_range(raw.index[0].floor(freq), raw.index[-1].floor(freq), freq=freq, tz="UTC")
    df = raw.reindex(idx)
    synthetic = df["close"].isna()
    df["close"] = df["close"].ffill()
    for c in ("open", "high", "low"):
        df[c] = df[c].where(~synthetic, df["close"])
    df["volume"] = df["volume"].fillna(0.0)
    for c in EXTRA_SUM_COLS:
        if c in df:
            df[c] = df[c].fillna(0.0)
    df["synthetic"] = synthetic.values
    df.index.name = "ts"
    return df


def _cache_valid(cache_path: str, source_path: str) -> bool:
    """Cache vale se existe e é mais novo que a fonte (trocou a fonte, refaz)."""
    return os.path.exists(cache_path) and os.path.getmtime(cache_path) >= os.path.getmtime(source_path)


def load_base(symbol: str) -> tuple[pd.DataFrame, int]:
    """Grade regular na resolução do bruto (1m ou 1h) e essa resolução em minutos."""
    src, minutes = raw_source(symbol)
    p = os.path.join(PARQUET_DIR, f"{symbol}_{minutes}m_v{CACHE_VERSION}.parquet")
    if _cache_valid(p, src):
        return pd.read_parquet(p), minutes
    df = regularize_1m(pd.read_parquet(src), minutes)
    os.makedirs(PARQUET_DIR, exist_ok=True)
    df.to_parquet(p)
    return df, minutes


def load_1m(symbol: str) -> pd.DataFrame:
    df, minutes = load_base(symbol)
    if minutes != 1:
        raise FileNotFoundError(f"{symbol} só tem bruto de {minutes} min")
    return df


def resample(df1m: pd.DataFrame, tf: str) -> pd.DataFrame:
    if tf == "1m":
        out = df1m.copy()
        if "synthetic" in out:
            out["open_synthetic"] = out["synthetic"]
        return out
    rule = PANDAS_RULE[tf]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    for c in EXTRA_SUM_COLS:
        if c in df1m:
            agg[c] = "sum"
    out = df1m.resample(rule, label="left", closed="left").agg(agg)
    if "synthetic" in df1m:
        syn = df1m["synthetic"].resample(rule, label="left", closed="left")
        out["synthetic"] = syn.min().astype(bool)          # barra inteira sem negócio
        out["open_synthetic"] = syn.first().astype(bool)   # a ABERTURA não existiu: proibido executar nela
    out = out.dropna(subset=["close"])
    out.index.name = "ts"
    return out


def load_bars(symbol: str, tf: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    if tf not in TF_MINUTES:
        raise ValueError(f"timeframe desconhecido: {tf}")
    p = os.path.join(PARQUET_DIR, f"{symbol}_{tf}_v{CACHE_VERSION}.parquet")
    if _cache_valid(p, raw_path(symbol)):
        df = pd.read_parquet(p)
    else:
        base, minutes = load_base(symbol)
        if TF_MINUTES[tf] < minutes:
            raise ValueError(f"{symbol}: a fonte tem {minutes} min, não dá para montar {tf}")
        if TF_MINUTES[tf] == minutes:
            df = base.copy()
            if "synthetic" in df:
                df["open_synthetic"] = df["synthetic"]
        else:
            df = resample(base, tf)
        os.makedirs(PARQUET_DIR, exist_ok=True)
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

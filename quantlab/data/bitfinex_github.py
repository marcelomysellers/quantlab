"""Ingestão do dataset público Bitfinex (github.com/Zombie-3000/Bitfinex-historical-data).

Formato de cada linha: timestamp_ms, open, close, high, low, volume  (atenção: close antes de high/low).
Gera data/parquet/BTCUSD_1m_raw.parquet no esquema padrão do projeto:
    index ts (UTC) | open high low close volume
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data", "external", "bitfinex-hist", "BTCUSD", "Candles_1m")
OUT_DIR = os.path.join(ROOT, "data", "parquet")


def load_raw(symbol: str = "BTCUSD") -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(SRC, "*", "merged.csv")))
    if not files:
        raise FileNotFoundError(f"nenhum CSV em {SRC}")
    frames = []
    for f in files:
        df = pd.read_csv(f, header=None, names=["ts", "open", "close", "high", "low", "volume"], dtype=float)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    df = df.drop_duplicates("ts", keep="last").sort_values("ts").set_index("ts")
    df = df[["open", "high", "low", "close", "volume"]]
    # saneamento mínimo: high/low coerentes com open/close
    df["high"] = np.maximum(df["high"], np.maximum(df["open"], df["close"]))
    df["low"] = np.minimum(df["low"], np.minimum(df["open"], df["close"]))
    return df


def ingest(symbol: str = "BTCUSD") -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_raw(symbol)
    out = os.path.join(OUT_DIR, f"{symbol}_1m_raw.parquet")
    df.to_parquet(out)
    return out


if __name__ == "__main__":
    print(ingest())

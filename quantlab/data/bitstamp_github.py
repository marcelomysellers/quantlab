"""Ingestão do dataset público Bitstamp (github.com/ff137/bitstamp-btcusd-minute-data).

BTC/USD em 1 minuto desde 2012, atualizado diariamente por GitHub Action. Dois arquivos:
histórico comprimido (até 2025-01-07) e atualizações desde então. Minutos sem negócio já vêm
como candle plano com volume zero; marcamos esses como `synthetic`.
Gera data/parquet/BTCUSD-BITSTAMP_1m_raw.parquet no esquema padrão (index ts UTC | open high low close volume).
"""
from __future__ import annotations

import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data", "external", "probe-bitstamp-btcusd-minute-data", "data")
OUT_DIR = os.path.join(ROOT, "data", "parquet")
SYMBOL = "BTCUSD-BITSTAMP"


def load_raw() -> pd.DataFrame:
    hist = os.path.join(SRC, "historical", "btcusd_bitstamp_1min_2012-2025.csv.gz")
    upd = os.path.join(SRC, "updates", "btcusd_bitstamp_1min_latest.csv")
    frames = [pd.read_csv(hist, dtype=float)]
    if os.path.exists(upd):
        frames.append(pd.read_csv(upd, dtype=float))
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="s", utc=True)
    df = df.drop_duplicates("ts", keep="last").sort_values("ts").set_index("ts")
    df = df[["open", "high", "low", "close", "volume"]]
    # candles planos com volume zero são minutos sem negócio: não contam como barra real
    flat = (df["volume"] == 0) & (df["high"] == df["low"])
    return df[~flat]


def ingest() -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_raw()
    out = os.path.join(OUT_DIR, f"{SYMBOL}_1m_raw.parquet")
    df.to_parquet(out)
    return out


if __name__ == "__main__":
    print(ingest())

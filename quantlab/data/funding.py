"""Funding rate de perpétuos (CSV público supervik/historical-funding-rates-fetcher, 2020-2023, várias exchanges).

Gera data/parquet/{symbol}_funding_{exchange}.parquet com index ts (UTC) | funding_rate.
Na sua máquina, `quantlab.data.binance --market um` traz o funding oficial e atualizado.
"""
from __future__ import annotations

import glob
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data", "external", "fr-historical-funding-rates-fetcher", "data")
OUT_DIR = os.path.join(ROOT, "data", "parquet")


def ingest_all() -> list[str]:
    os.makedirs(OUT_DIR, exist_ok=True)
    outs = []
    for f in sorted(glob.glob(os.path.join(SRC, "*", "*_funding_history.csv"))):
        name = os.path.basename(f)
        symbol, exchange = name.split("_")[0].replace("-", ""), name.split("_")[1]
        df = pd.read_csv(f)
        df["ts"] = pd.to_datetime(df["Date"], utc=True)
        df = df.rename(columns={"Funding Rate": "funding_rate"}).set_index("ts")[["funding_rate"]].astype(float).sort_index()
        out = os.path.join(OUT_DIR, f"{symbol}_funding_{exchange}.parquet")
        df.to_parquet(out)
        outs.append(out)
    return outs


def load_funding(symbol: str = "BTCUSDT", exchange: str = "binance") -> pd.DataFrame:
    return pd.read_parquet(os.path.join(OUT_DIR, f"{symbol}_funding_{exchange}.parquet"))


if __name__ == "__main__":
    for o in ingest_all():
        print(o)

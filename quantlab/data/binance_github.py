"""Ingestão do dataset público Binance em Parquet (github.com/Speirsy11/crypto-dataset, Git LFS).

Partição hive: data/interval_id=1m/symbol_id=BTCUSDT/year=YYYY/month=MM/*.parquet, colunas
symbol, interval, timestamp (UTC), open, high, low, close, volume, source_rows. Só OHLCV; os klines
oficiais da Binance (volume taker-buy, número de trades) exigem o fetcher na sua máquina.
Gera data/parquet/BTCUSDT-BINANCE_1m_raw.parquet.
"""
from __future__ import annotations

import glob
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data", "external", "probe-crypto-dataset", "data")
OUT_DIR = os.path.join(ROOT, "data", "parquet")


def load_raw(symbol: str = "BTCUSDT", interval: str = "1m") -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(SRC, f"interval_id={interval}", f"symbol_id={symbol}", "year=*", "month=*", "*.parquet")))
    frames = []
    for f in files:
        with open(f, "rb") as fh:
            if fh.read(4) != b"PAR1":
                continue  # ponteiro LFS ainda não baixado
        frames.append(pd.read_parquet(f, columns=["timestamp", "open", "high", "low", "close", "volume"]))
    if not frames:
        raise FileNotFoundError("nenhum parquet real encontrado; baixe os objetos LFS")
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.drop_duplicates("ts", keep="last").sort_values("ts").set_index("ts")
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def ingest(symbol: str = "BTCUSDT") -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_raw(symbol)
    out = os.path.join(OUT_DIR, f"{symbol}-BINANCE_1m_raw.parquet")
    df.to_parquet(out)
    return out


if __name__ == "__main__":
    print(ingest())

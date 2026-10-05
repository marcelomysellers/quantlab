"""Fetcher de dados públicos da Binance (data.binance.vision) para rodar na SUA máquina.

A sessão em nuvem onde este projeto nasceu não tem acesso à Binance, por isso o torneio
inicial usa o dataset Bitfinex 2013-2019. Na sua máquina:

    python -m quantlab.data.binance --symbol BTCUSDT --market um --start 2020-01 --end 2026-09

Baixa klines mensais de 1 minuto (e funding rate, se market=um) e grava em
data/parquet/{SYMBOL}-BINANCE-{MARKET}_1m_raw.parquet no esquema padrão (index ts UTC | open high low close volume)
mais quote_volume, trades e taker_buy_base (fluxo de ordens), que o store soma ao reamostrar.
"""
from __future__ import annotations

import argparse
import io
import os
import zipfile
from datetime import date

import numpy as np
import pandas as pd
import requests

BASE = "https://data.binance.vision/data"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data", "parquet")
KLINE_COLS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
    "trades", "taker_buy_base", "taker_buy_quote", "ignore",
]


def month_range(start: str, end: str):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def kline_url(symbol: str, market: str, interval: str, month: str) -> str:
    prefix = "spot" if market == "spot" else f"futures/{market}"
    return f"{BASE}/{prefix}/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{month}.zip"


def funding_url(symbol: str, market: str, month: str) -> str:
    return f"{BASE}/futures/{market}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{month}.zip"


def _read_zip_csv(content: bytes, names: list[str]) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            head = f.read(64)
        with z.open(name) as f:
            # arquivos mais novos têm cabeçalho; os antigos não
            has_header = head[:1].isalpha()
            return pd.read_csv(f, header=0 if has_header else None, names=None if has_header else names)


def fetch_klines(symbol: str, market: str, start: str, end: str, interval: str = "1m", cache_dir: str | None = None) -> pd.DataFrame:
    cache_dir = cache_dir or os.path.join(ROOT, "data", "raw", "binance")
    os.makedirs(cache_dir, exist_ok=True)
    frames = []
    for month in month_range(start, end):
        path = os.path.join(cache_dir, f"{symbol}-{interval}-{month}.zip")
        if not os.path.exists(path):
            r = requests.get(kline_url(symbol, market, interval, month), timeout=120)
            if r.status_code == 404:
                print(f"[binance] {month}: não existe (ainda?)")
                continue
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
        with open(path, "rb") as f:
            df = _read_zip_csv(f.read(), KLINE_COLS)
        df.columns = KLINE_COLS[: len(df.columns)]
        frames.append(df)
        print(f"[binance] {month}: {len(df)} barras")
    if not frames:
        raise RuntimeError("nada baixado")
    df = pd.concat(frames, ignore_index=True)
    # a Binance trocou de milissegundos para microssegundos em 2025: decidir linha a linha
    ot = df["open_time"].astype("int64")
    ms = np.where(ot > 10**14, ot // 1000, ot)
    df["ts"] = pd.to_datetime(ms, unit="ms", utc=True)
    df = df.drop_duplicates("ts").sort_values("ts").set_index("ts")
    cols = ["open", "high", "low", "close", "volume", "quote_volume", "trades", "taker_buy_base"]
    return df[[c for c in cols if c in df]].astype(float)


def fetch_funding(symbol: str, market: str, start: str, end: str) -> pd.DataFrame:
    frames = []
    for month in month_range(start, end):
        r = requests.get(funding_url(symbol, market, month), timeout=120)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        df = _read_zip_csv(r.content, ["calc_time", "funding_interval_hours", "last_funding_rate"])
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["funding_rate"])
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df.iloc[:, 0].astype("int64"), unit="ms", utc=True)
    df["funding_rate"] = df.iloc[:, 2].astype(float)
    return df.set_index("ts")[["funding_rate"]].sort_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--market", default="um", choices=["spot", "um", "cm"], help="spot, um (USDT-M perp) ou cm (coin-M)")
    ap.add_argument("--start", default="2020-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out-symbol", default=None, help="nome usado no parquet (padrão: {SYMBOL}-BINANCE-{MARKET}, ex.: BTCUSDT-BINANCE-UM)")
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    out_symbol = a.out_symbol or f"{a.symbol}-BINANCE-{a.market.upper()}"
    df = fetch_klines(a.symbol, a.market, a.start, a.end)
    out = os.path.join(OUT_DIR, f"{out_symbol}_1m_raw.parquet")
    df.to_parquet(out)
    print("gravado", out, len(df), "barras")
    if a.market != "spot":
        fr = fetch_funding(a.symbol, a.market, a.start, a.end)
        fr.to_parquet(os.path.join(OUT_DIR, f"{out_symbol}_funding.parquet"))
        print("funding:", len(fr), "registros")


if __name__ == "__main__":
    main()

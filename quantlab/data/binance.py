"""Fetcher de dados públicos da Binance (data.binance.vision) para rodar na SUA máquina.

A sessão em nuvem não alcança a Binance. Na sua máquina, o comando que fecha a pista do funding:

    python -m quantlab.data.binance --symbol BTCUSDT --market um --interval 1h --start 2020-01 --public

Baixa klines mensais do perpétuo (1h: ~2 MB no total) com volume taker-buy e número de negócios,
mais o funding rate, e grava em data/public/ (pasta versionada no git) como
{SYMBOL}-BINANCE-{MARKET}_{interval}_raw.parquet e {SYMBOL}-BINANCE-{MARKET}_funding.parquet,
no esquema padrão (index ts UTC | open high low close volume quote_volume trades taker_buy_base).
Sem --public grava em data/parquet/ (ignorado pelo git). --interval 1m é o dado completo (~150 MB).
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


def fetch_funding(symbol: str, market: str, start: str, end: str, cache_dir: str | None = None) -> pd.DataFrame:
    cache_dir = cache_dir or os.path.join(ROOT, "data", "raw", "binance")
    os.makedirs(cache_dir, exist_ok=True)
    frames = []
    for month in month_range(start, end):
        path = os.path.join(cache_dir, f"{symbol}-fundingRate-{month}.zip")
        if not os.path.exists(path):
            r = requests.get(funding_url(symbol, market, month), timeout=120)
            if r.status_code == 404:
                print(f"[binance] funding {month}: não existe (ainda?)")
                continue
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
        with open(path, "rb") as f:
            df = _read_zip_csv(f.read(), ["calc_time", "funding_interval_hours", "last_funding_rate"])
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["funding_rate"])
    df = pd.concat(frames, ignore_index=True)
    ts = df.iloc[:, 0].astype("int64")
    ms = np.where(ts > 10**14, ts // 1000, ts)
    df["ts"] = pd.to_datetime(ms, unit="ms", utc=True)
    rate_col = [c for c in df.columns if "rate" in str(c).lower()]
    df["funding_rate"] = (df[rate_col[0]] if rate_col else df.iloc[:, 2]).astype(float)
    return df.drop_duplicates("ts").set_index("ts")[["funding_rate"]].sort_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--market", default="um", choices=["spot", "um", "cm"], help="spot, um (USDT-M perp) ou cm (coin-M)")
    ap.add_argument("--start", default="2020-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out-symbol", default=None, help="nome usado no parquet (padrão: {SYMBOL}-BINANCE-{MARKET}, ex.: BTCUSDT-BINANCE-UM)")
    ap.add_argument("--interval", default="1m", choices=["1m", "5m", "15m", "1h", "4h", "1d"], help="intervalo dos klines (1h basta para o estudo de funding)")
    ap.add_argument("--public", action="store_true", help="grava em data/public/ (versionado) em vez de data/parquet/")
    a = ap.parse_args()
    out_dir = os.path.join(ROOT, "data", "public") if a.public else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_symbol = a.out_symbol or f"{a.symbol}-BINANCE-{a.market.upper()}"
    df = fetch_klines(a.symbol, a.market, a.start, a.end, interval=a.interval)
    out = os.path.join(out_dir, f"{out_symbol}_{a.interval}_raw.parquet")
    df.to_parquet(out)
    print("gravado", out, len(df), "barras de", df.index[0], "a", df.index[-1])
    if a.market != "spot":
        fr = fetch_funding(a.symbol, a.market, a.start, a.end)
        fout = os.path.join(out_dir, f"{out_symbol}_funding.parquet")
        fr.to_parquet(fout)
        print("funding:", fout, len(fr), "registros de", fr.index[0] if len(fr) else "-", "a", fr.index[-1] if len(fr) else "-")
    print("agora: git add data/public && git commit -m 'Dados Binance' && git push")


if __name__ == "__main__":
    main()

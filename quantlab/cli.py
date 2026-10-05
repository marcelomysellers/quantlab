"""CLI do laboratório.

  python -m quantlab.cli ingest-bitfinex
  python -m quantlab.cli quality
  python -m quantlab.cli tournament --tfs 1h,4h,1d --start 2017-01-01 --end 2020-01-01
"""
from __future__ import annotations

import argparse
import os
import shutil
import time

from quantlab.backtest.walkforward import WFConfig
from quantlab.strategies import REGISTRY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(prog="quantlab")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ingest-bitfinex", help="CSV Bitfinex (github) -> parquet 1m")
    q = sub.add_parser("quality", help="relatório de qualidade do 1m")
    q.add_argument("--symbol", default="BTCUSD")

    t = sub.add_parser("tournament", help="roda o torneio e grava JSON em results/runs/<id>")
    t.add_argument("--symbol", default="BTCUSD")
    t.add_argument("--tfs", default="5m,15m,1h,4h,1d")
    t.add_argument("--strategies", default=",".join(REGISTRY))
    t.add_argument("--start", default="2017-01-01")
    t.add_argument("--end", default="2020-01-01")
    t.add_argument("--train-months", type=int, default=12)
    t.add_argument("--test-months", type=int, default=3)
    t.add_argument("--min-trades", type=int, default=10)
    t.add_argument("--null-sims", type=int, default=300)
    t.add_argument("--stress-sims", type=int, default=40)
    t.add_argument("--run-id", default=None)
    t.add_argument("--publish", action="store_true", help="copia o resultado para web/public/results/latest")

    a = ap.parse_args()
    if a.cmd == "ingest-bitfinex":
        from quantlab.data.bitfinex_github import ingest
        print(ingest())
    elif a.cmd == "quality":
        from quantlab.data.store import load_raw_1m, quality_report
        print(quality_report(load_raw_1m(a.symbol)).to_string(index=False))
    elif a.cmd == "tournament":
        from quantlab.tournament import run_tournament
        run_id = a.run_id or time.strftime("%Y%m%d-%H%M%S")
        out = os.path.join(ROOT, "results", "runs", run_id)
        cfg = WFConfig(train_months=a.train_months, test_months=a.test_months, min_trades=a.min_trades)
        run_tournament(a.symbol, a.tfs.split(","), a.strategies.split(","), a.start, a.end, cfg, out,
                       n_null=a.null_sims, n_stress=a.stress_sims)
        if a.publish:
            dst = os.path.join(ROOT, "web", "public", "results", "latest")
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(out, dst)
            print("publicado em", dst)


if __name__ == "__main__":
    main()

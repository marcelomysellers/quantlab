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
    sub.add_parser("ingest-bitstamp", help="CSV Bitstamp (github, 2012-hoje) -> parquet 1m")
    sub.add_parser("ingest-binance-github", help="Parquet Binance (github Speirsy11, LFS) -> parquet 1m")
    sub.add_parser("ingest-funding", help="CSV de funding (github supervik) -> parquet")
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
    t.add_argument("--wf-mode", default="best", choices=["best", "mean"], help="best: melhor parâmetro do treino; mean: média da grade, sem seleção")
    t.add_argument("--null-sims", type=int, default=300)
    t.add_argument("--stress-sims", type=int, default=40)
    t.add_argument("--run-id", default=None)
    t.add_argument("--publish", action="store_true", help="copia o resultado para web/public/results/<run_id> e atualiza index.json")

    pb = sub.add_parser("publish", help="publica um torneio já rodado em web/public/results/<run_id>")
    pb.add_argument("run_id")

    rv = sub.add_parser("reverdict", help="recalcula concentração, DSR global e vereditos de um torneio já rodado e republica")
    rv.add_argument("run_id")
    rv.add_argument("--days-per-year", type=float, default=365.25)

    a = ap.parse_args()
    if a.cmd == "ingest-bitfinex":
        from quantlab.data.bitfinex_github import ingest
        print(ingest())
    elif a.cmd == "ingest-bitstamp":
        from quantlab.data.bitstamp_github import ingest
        print(ingest())
    elif a.cmd == "ingest-binance-github":
        from quantlab.data.binance_github import ingest
        print(ingest())
    elif a.cmd == "ingest-funding":
        from quantlab.data.funding import ingest_all
        print("\n".join(ingest_all()))
    elif a.cmd == "quality":
        from quantlab.data.store import load_raw_1m, quality_report
        print(quality_report(load_raw_1m(a.symbol)).to_string(index=False))
    elif a.cmd == "tournament":
        from quantlab.tournament import run_tournament
        run_id = a.run_id or time.strftime("%Y%m%d-%H%M%S")
        out = os.path.join(ROOT, "results", "runs", run_id)
        cfg = WFConfig(train_months=a.train_months, test_months=a.test_months, min_trades=a.min_trades, mode=a.wf_mode)
        run_tournament(a.symbol, a.tfs.split(","), a.strategies.split(","), a.start, a.end, cfg, out,
                       n_null=a.null_sims, n_stress=a.stress_sims)
        if a.publish:
            print("publicado em", publish_run(out))
    elif a.cmd == "publish":
        print("publicado em", publish_run(os.path.join(ROOT, "results", "runs", a.run_id)))
    elif a.cmd == "reverdict":
        from quantlab.tournament import reverdict
        run_dir = os.path.join(ROOT, "results", "runs", a.run_id)
        rows = reverdict(run_dir, a.days_per_year)
        from collections import Counter
        print(dict(Counter(r["verdict"] for r in rows)))
        print("publicado em", publish_run(run_dir))


def publish_run(run_dir: str) -> str:
    """Copia um torneio para web/public/results/<run_id>/ e regenera index.json (mais recente primeiro)."""
    import json
    results_dir = os.path.join(ROOT, "web", "public", "results")
    run_id = os.path.basename(run_dir.rstrip("/"))
    dst = os.path.join(results_dir, run_id)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(run_dir, dst)
    latest = os.path.join(results_dir, "latest")
    if os.path.isdir(latest) and not os.path.islink(latest):
        shutil.rmtree(latest)
    runs = []
    for d in sorted(os.listdir(results_dir)):
        mp = os.path.join(results_dir, d, "manifest.json")
        if os.path.isfile(mp):
            m = json.load(open(mp))
            runs.append({"id": d, "symbol": m["symbol"], "instrument": m["instrument"], "start": m["start"], "end": m["end"],
                         "tfs": m["tfs"], "generated_at": m["generated_at"], "method_version": m.get("method_version", 1),
                         "wf_mode": m.get("wf", {}).get("mode", "best")})
    runs.sort(key=lambda r: r["generated_at"], reverse=True)
    with open(os.path.join(results_dir, "index.json"), "w") as f:
        json.dump(runs, f, indent=1)
    return dst


if __name__ == "__main__":
    main()

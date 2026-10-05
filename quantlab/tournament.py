"""Torneio: todas as estratégias x todos os timeframes, walk-forward, 3 cenários de custo,
nulo aleatório, estresse de execução, DSR, duelos. Saída em JSON para o frontend."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from quantlab.backtest.engine import BacktestResult, aggregate_daily, run_backtest
from quantlab.backtest.metrics import block_bootstrap_sharpe, dsr, max_drawdown, sharpe, summarize
from quantlab.backtest.montecarlo import random_entry_null
from quantlab.backtest.walkforward import WFConfig, WFResult, walk_forward
from quantlab.data.store import load_bars
from quantlab.execution import SCENARIOS, FillModel
from quantlab.instruments import INSTRUMENTS, TF_MINUTES
from quantlab.strategies import REGISTRY, Context

STRESS = FillModel(miss_prob=0.05, partial_prob=0.30, partial_min=0.3)


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        v = float(o)
        return None if (np.isnan(v) or np.isinf(v)) else v
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp,)):
        return o.isoformat()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(f"não serializável: {type(o)}")


def _clean(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            out[k] = None
        else:
            out[k] = v
    return out


def _downsample(values: np.ndarray, max_points: int) -> np.ndarray:
    n = len(values)
    if n <= max_points:
        return np.arange(n)
    return np.unique(np.linspace(0, n - 1, max_points).astype(int))


def verdict_for(m_base: dict, m_pess: dict, null_p: float, dsr_v: float, is_benchmark: bool) -> tuple[str, list[dict]]:
    checks = [
        {"id": "sharpe_pos", "label": "Sharpe OOS (base) > 0.5", "ok": m_base["sharpe"] > 0.5, "value": round(m_base["sharpe"], 2)},
        {"id": "null", "label": "Bate entradas aleatórias (p < 0.05)", "ok": null_p < 0.05, "value": round(null_p, 3)},
        {"id": "dsr", "label": "Sharpe deflacionado > 0.90", "ok": dsr_v > 0.90, "value": round(dsr_v, 3)},
        {"id": "pess", "label": "Sobrevive ao cenário pessimista (Sharpe > 0)", "ok": m_pess["sharpe"] > 0, "value": round(m_pess["sharpe"], 2)},
        {"id": "trades", "label": "Pelo menos 30 trades OOS", "ok": m_base["n_trades"] >= 30, "value": m_base["n_trades"]},
    ]
    if is_benchmark:
        return "referencia", checks
    if all(c["ok"] for c in checks):
        return "aprovada", checks
    if m_base["sharpe"] > 0 and null_p < 0.15 and m_base["n_trades"] >= 30:
        return "promissora", checks
    return "reprovada", checks


def evaluate_entry(strategy, bars: pd.DataFrame, ctx: Context, wf: WFResult, cfg: WFConfig,
                   n_null: int, n_stress: int) -> tuple[dict, dict]:
    tfm = ctx.tf_minutes
    region = slice(wf.oos_start, wf.oos_end)
    b = bars.iloc[region]
    tgt = wf.oos_target[region]
    idx = b.index

    res: dict[str, BacktestResult] = {k: run_backtest(b, tgt, em, tfm) for k, em in SCENARIOS.items()}
    daily = {k: aggregate_daily(r.net, idx) for k, r in res.items()}
    metrics = {k: _clean(summarize(r.net, r.pos, r.turnover, ctx.bars_per_year, r.trades, daily[k])) for k, r in res.items()}
    base, pess = res["base"], res["pessimista"]
    mb = metrics["base"]

    # custo: quanto o bruto virou líquido
    gross_total = float(np.prod(1.0 + base.gross) - 1.0)
    cost_total = float(np.sum(base.cost))

    # referência comprado-e-segurar no mesmo trecho
    bh = run_backtest(b, np.ones(len(b)), SCENARIOS["base"], tfm)
    bh_daily = aggregate_daily(bh.net, idx)
    bh_m = _clean(summarize(bh.net, bh.pos, bh.turnover, ctx.bars_per_year, bh.trades, bh_daily))

    # curva de vitrine (melhor config escolhida olhando tudo)
    overfit_daily = None
    if wf.best_full_target is not None:
        ov = run_backtest(b, wf.best_full_target[region], SCENARIOS["base"], tfm)
        overfit_daily = aggregate_daily(ov.net, idx)

    # nulo: entradas aleatórias com a mesma exposição
    n_sims = n_null if len(b) < 600_000 else max(60, n_null // 3)
    null = random_entry_null(b, base.trades, SCENARIOS["base"], tfm, mb["sharpe"], n_sims=n_sims)

    # estresse de execução: fills parciais e ordens perdidas
    stress = []
    for i in range(n_stress):
        r = run_backtest(b, tgt, SCENARIOS["base"], tfm, fill=FillModel(STRESS.miss_prob, STRESS.partial_prob, STRESS.partial_min, seed=i), with_trades=False)
        d = aggregate_daily(r.net, idx).to_numpy()
        stress.append({"sharpe": round(sharpe(d, 365.25), 3), "total_return": round(float(np.prod(1 + r.net) - 1), 4)})

    # DSR: deflaciona pelo número de configurações testadas e pela variância dos Sharpes
    d = daily["base"].to_numpy()
    sr_bar = float(np.mean(d) / np.std(d, ddof=1)) if len(d) > 2 and np.std(d, ddof=1) > 0 else 0.0
    n_trials = max(len(wf.configs), 1)
    var_sr = float(np.var(wf.config_sr_daily)) if len(wf.config_sr_daily) > 1 else 0.0
    dsr_v = dsr(sr_bar, len(d), mb["skew"], mb["kurtosis"], n_trials, var_sr)
    ci_lo, ci_hi = block_bootstrap_sharpe(d, 365.25, n_boot=200)

    verdict, checks = verdict_for(mb, metrics["pessimista"], null["p_value"], dsr_v, strategy.is_benchmark)

    # séries para o frontend (resolução diária, base comum entre timeframes)
    eq = np.cumprod(1.0 + daily["base"].to_numpy())
    eq_bh = np.cumprod(1.0 + bh_daily.to_numpy())
    eq_ov = np.cumprod(1.0 + overfit_daily.to_numpy()) if overfit_daily is not None else None
    eq_pess = np.cumprod(1.0 + daily["pessimista"].to_numpy())
    eq_opt = np.cumprod(1.0 + daily["otimista"].to_numpy())
    dd = eq / np.maximum.accumulate(eq) - 1.0
    dates = [int(t.timestamp()) for t in daily["base"].index]
    curve = [{"t": dates[i], "eq": round(float(eq[i]), 5), "bh": round(float(eq_bh[i]), 5), "dd": round(float(dd[i]), 5),
              "pess": round(float(eq_pess[i]), 5), "opt": round(float(eq_opt[i]), 5),
              **({"ov": round(float(eq_ov[i]), 5)} if eq_ov is not None else {})} for i in range(len(eq))]

    # janela de candles com marcadores de trades (últimas N barras do OOS)
    n_win = min(len(b), 700)
    w0 = len(b) - n_win
    wb = b.iloc[w0:]
    candles = [{"t": int(t.timestamp()), "o": round(float(o), 2), "h": round(float(h), 2), "l": round(float(l), 2), "c": round(float(c), 2)}
               for t, o, h, l, c in zip(wb.index, wb["open"], wb["high"], wb["low"], wb["close"])]
    tr = base.trades
    tr_win = tr[(tr["entry_idx"] >= w0)] if len(tr) else tr
    markers = [{"t": int(idx[int(r.entry_idx)].timestamp()), "side": int(r.side), "kind": "entry", "px": round(float(r.entry_px), 2), "size": round(float(r.size), 2)}
               for r in tr_win.itertuples()] + \
              [{"t": int(idx[int(r.exit_idx)].timestamp()), "side": int(r.side), "kind": "exit", "px": round(float(r.exit_px), 2), "ret": round(float(r.ret_net), 4)}
               for r in tr_win.itertuples() if not r.open]
    pos_win = [round(float(x), 2) for x in base.pos[w0:]]

    trades_out = []
    if len(tr):
        last = tr.tail(300)
        for r in last.itertuples():
            trades_out.append({"entry": int(idx[int(r.entry_idx)].timestamp()), "exit": int(idx[int(r.exit_idx)].timestamp()), "side": int(r.side),
                               "size": round(float(r.size), 2), "bars": int(r.bars), "entry_px": round(float(r.entry_px), 2),
                               "exit_px": round(float(r.exit_px), 2), "ret_net": round(float(r.ret_net), 5), "open": bool(r.open)})

    folds = []
    for f in wf.folds:
        folds.append({"k": f.k, "train": [f.train_start.strftime("%Y-%m-%d"), f.train_end.strftime("%Y-%m-%d")],
                      "test": [f.test_start.strftime("%Y-%m-%d"), f.test_end.strftime("%Y-%m-%d")],
                      "params": f.params, "is_sharpe": round(f.is_sharpe, 3), "oos_sharpe": round(f.oos_sharpe, 3),
                      "oos_return": round(f.oos_return, 4), "n_trades_is": f.n_trades_is, "n_configs": f.n_configs, "table": f.table})

    entry_id = f"{strategy.name}__{ctx.tf}"
    row = {
        "id": entry_id, "strategy": strategy.name, "label": strategy.label, "tf": ctx.tf, "tf_minutes": tfm,
        "is_benchmark": strategy.is_benchmark, "verdict": verdict,
        "metrics": metrics, "bh": {k: bh_m[k] for k in ("sharpe", "cagr", "max_drawdown", "total_return")},
        "gross_total": gross_total, "cost_total": cost_total,
        "null_p": null["p_value"], "null_mean": null.get("null_mean"), "null_p95": null.get("null_p95"),
        "dsr": dsr_v, "n_trials": n_trials, "sharpe_ci90": [ci_lo, ci_hi],
        "stress_sharpe_median": float(np.median([s["sharpe"] for s in stress])) if stress else None,
        "stress_sharpe_p10": float(np.percentile([s["sharpe"] for s in stress], 10)) if stress else None,
        "fold_returns": [f["oos_return"] for f in folds], "fold_sharpes": [f["oos_sharpe"] for f in folds],
        "params_by_fold": [f["params"] for f in folds],
        "oos_range": [idx[0].strftime("%Y-%m-%d"), idx[-1].strftime("%Y-%m-%d")],
        "spark": [round(float(x), 4) for x in eq[_downsample(eq, 60)]],
    }
    detail = {
        **row,
        "description": strategy.description,
        "checks": checks,
        "curve": curve,
        "candles": candles, "markers": markers, "pos_win": pos_win,
        "trades": trades_out,
        "folds": folds,
        "null": {"sharpes": null["sharpes"], "p_value": null["p_value"], "n_sims": null["n_sims"], "actual": null["actual"]},
        "stress": stress,
        "stress_model": {"miss_prob": STRESS.miss_prob, "partial_prob": STRESS.partial_prob, "partial_min": STRESS.partial_min},
        "best_full_params": wf.best_full_params,
        "grid_size": len(wf.configs),
        "daily": {"t": dates, "r": [round(float(x), 6) for x in daily["base"].to_numpy()]},
    }
    return row, detail


def duels(details: dict[str, dict], top_ids: list[str]) -> list[dict]:
    out = []
    series = {}
    for i in top_ids:
        d = details[i]["daily"]
        series[i] = pd.Series(d["r"], index=pd.to_datetime(d["t"], unit="s", utc=True))
    for a_i in range(len(top_ids)):
        for b_i in range(a_i + 1, len(top_ids)):
            a, b = top_ids[a_i], top_ids[b_i]
            df = pd.concat([series[a], series[b]], axis=1, keys=["a", "b"]).dropna()
            if len(df) < 30:
                continue
            ra, rb = df["a"].to_numpy(), df["b"].to_numpy()
            comb = 0.5 * ra + 0.5 * rb
            fa, fb = details[a]["fold_returns"], details[b]["fold_returns"]
            wins_a = int(sum(1 for x, y in zip(fa, fb) if x > y))
            wins_b = int(sum(1 for x, y in zip(fa, fb) if y > x))
            out.append({
                "a": a, "b": b,
                "sharpe_a": round(sharpe(ra, 365.25), 3), "sharpe_b": round(sharpe(rb, 365.25), 3),
                "corr": round(float(np.corrcoef(ra, rb)[0, 1]), 3) if ra.std() > 0 and rb.std() > 0 else 0.0,
                "combined_sharpe": round(sharpe(comb, 365.25), 3),
                "combined_cagr": round(float(np.prod(1 + comb) ** (365.25 / len(comb)) - 1), 4),
                "combined_mdd": round(max_drawdown(np.cumprod(1 + comb))[0], 4),
                "folds_won_a": wins_a, "folds_won_b": wins_b, "n_folds": len(fa),
            })
    return out


def run_tournament(symbol: str, tfs: list[str], strategy_names: list[str], start: str, end: str,
                   cfg: WFConfig, out_dir: str, n_null: int = 300, n_stress: int = 40, log=print) -> dict:
    os.makedirs(os.path.join(out_dir, "entries"), exist_ok=True)
    inst = INSTRUMENTS[symbol]
    rows, details = [], {}
    t_all = time.time()
    for tf in tfs:
        bars = load_bars(symbol, tf, start, end)
        ctx = Context(tf, TF_MINUTES[tf], inst.bars_per_year(tf), inst.bars_per_day(tf))
        for name in strategy_names:
            strat = REGISTRY[name]
            if not strat.supports(ctx):
                continue
            t0 = time.time()
            wf = walk_forward(strat, bars, ctx, SCENARIOS["base"], cfg)
            row, detail = evaluate_entry(strat, bars, ctx, wf, cfg, n_null, n_stress)
            rows.append(row)
            details[row["id"]] = detail
            with open(os.path.join(out_dir, "entries", f"{row['id']}.json"), "w") as f:
                json.dump(detail, f, default=_json_default)
            m = row["metrics"]["base"]
            log(f"[{tf:>3}] {name:<18} sharpe={m['sharpe']:+.2f} cagr={m['cagr']:+.1%} mdd={m['max_drawdown']:.1%} "
                f"trades={m['n_trades']:>5} p_null={row['null_p']:.3f} dsr={row['dsr']:.2f} -> {row['verdict']} ({time.time()-t0:.1f}s)")

    rows.sort(key=lambda r: r["metrics"]["base"]["sharpe"], reverse=True)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    competitors = [r["id"] for r in rows if not r["is_benchmark"]][:8]
    bh_ids = [r["id"] for r in rows if r["strategy"] == "buy_hold"][:1]
    duel_list = duels(details, competitors + bh_ids)

    manifest = {
        "symbol": symbol, "instrument": inst.name, "tfs": tfs, "strategies": strategy_names,
        "start": start, "end": end, "wf": asdict(cfg),
        "scenarios": {k: {"fee_bps": v.fee_bps, "spread_bps": v.spread_bps, "slippage_bps": v.slippage_bps,
                          "impact_k": v.impact_k, "lag_bars": v.lag_bars, "round_trip_bps_fixed": v.round_trip_bps_fixed(),
                          "description": v.description} for k, v in SCENARIOS.items()},
        "stress_model": {"miss_prob": STRESS.miss_prob, "partial_prob": STRESS.partial_prob, "partial_min": STRESS.partial_min},
        "n_null": n_null, "n_stress": n_stress,
        "generated_at": pd.Timestamp.utcnow().isoformat(), "elapsed_s": round(time.time() - t_all, 1),
        "strategy_meta": {n: {"label": REGISTRY[n].label, "description": REGISTRY[n].description, "is_benchmark": REGISTRY[n].is_benchmark,
                              "param_space": REGISTRY[n].param_space} for n in strategy_names},
    }
    with open(os.path.join(out_dir, "leaderboard.json"), "w") as f:
        json.dump(rows, f, default=_json_default)
    with open(os.path.join(out_dir, "duels.json"), "w") as f:
        json.dump(duel_list, f, default=_json_default)
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, default=_json_default)
    log(f"torneio concluído em {time.time()-t_all:.0f}s -> {out_dir}")
    return manifest

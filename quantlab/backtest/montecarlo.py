"""Nulo correto: entradas aleatórias com a mesma exposição.

A pergunta não é "a estratégia ganhou dinheiro?" e sim "ela ganhou mais do que ganharia
entrando em momentos sorteados, com o mesmo número de trades, as mesmas durações, a mesma
mistura comprado/vendido e os mesmos custos?". O p-valor é a fração de simulações que
igualam ou superam o Sharpe real.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab.backtest.engine import aggregate_daily, run_backtest
from quantlab.backtest.metrics import sharpe
from quantlab.execution import ExecutionModel


def random_positions(n: int, durations: np.ndarray, sides: np.ndarray, sizes: np.ndarray,
                     rng: np.random.Generator) -> np.ndarray:
    pos = np.zeros(n)
    k = len(durations)
    starts = rng.integers(0, max(n - 1, 1), k)
    durs = rng.choice(durations, k)
    sds = rng.choice(sides, k)
    szs = rng.choice(sizes, k)
    for s, d, side, sz in zip(starts, durs, sds, szs):
        pos[s: s + int(d)] = side * sz
    return pos


def random_entry_null(bars: pd.DataFrame, trades: pd.DataFrame, exec_model: ExecutionModel, tf_minutes: int,
                      actual_sharpe: float, n_sims: int = 300, seed: int = 0) -> dict:
    n = len(bars)
    closed = trades[~trades["open"]] if len(trades) else trades
    if len(closed) < 3:
        return {"sharpes": [], "p_value": 1.0, "actual": actual_sharpe, "n_sims": 0, "n_trades": int(len(closed))}
    durations = closed["bars"].to_numpy(dtype=int)
    sides = closed["side"].to_numpy(dtype=float)
    sizes = closed["size"].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    out = np.empty(n_sims)
    for i in range(n_sims):
        # target = posição desejada; o motor aplica o lag e os custos iguais aos da estratégia real
        target = random_positions(n, durations, sides, sizes, rng)
        res = run_backtest(bars, target, exec_model, tf_minutes, with_trades=False)
        daily = aggregate_daily(res.net, bars.index)
        out[i] = sharpe(daily.to_numpy(), 365.25)
    p = float(np.mean(out >= actual_sharpe))
    return {
        "sharpes": [round(float(x), 4) for x in out],
        "p_value": p,
        "actual": actual_sharpe,
        "n_sims": n_sims,
        "n_trades": int(len(closed)),
        "null_mean": float(out.mean()),
        "null_p95": float(np.percentile(out, 95)),
    }

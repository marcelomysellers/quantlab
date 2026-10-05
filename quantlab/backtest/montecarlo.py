"""Nulos.

`shifted_null` (padrão): a própria série de posições-alvo da estratégia deslocada
circularmente no tempo. Preserva exatamente exposição, número e duração dos trades, mistura
comprado/vendido e autocorrelação; só destrói o alinhamento com o preço. É o teste de
permutação que Patterson pediu. O p-valor é a fração de deslocamentos que igualam ou superam
o Sharpe real.

`random_entry_null` (legado): entradas sorteadas com durações amostradas dos trades reais.
Trades sorteados se sobrepõem e se apagam, então a exposição sai menor que a real.
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


def shifted_null(bars: pd.DataFrame, target: np.ndarray, exec_model: ExecutionModel, tf_minutes: int,
                 actual_sharpe: float, n_sims: int = 300, min_shift: int = 1, seed: int = 0) -> dict:
    """Permutação por deslocamento circular das posições-alvo (mesma exposição e durações)."""
    n = len(bars)
    target = np.nan_to_num(np.asarray(target, dtype=float), nan=0.0)
    if n < 10 or np.all(target == 0):
        return {"sharpes": [], "p_value": 1.0, "actual": actual_sharpe, "n_sims": 0, "n_trades": 0, "kind": "shift"}
    rng = np.random.default_rng(seed)
    min_shift = max(1, min(min_shift, n // 4))
    out = np.empty(n_sims)
    for i in range(n_sims):
        k = int(rng.integers(min_shift, n - min_shift))
        res = run_backtest(bars, np.roll(target, k), exec_model, tf_minutes, with_trades=False)
        daily = aggregate_daily(res.net, bars.index)
        out[i] = sharpe(daily.to_numpy(), 365.25)
    p = float(np.mean(out >= actual_sharpe))
    return {
        "sharpes": [round(float(x), 4) for x in out], "p_value": p, "actual": actual_sharpe, "n_sims": n_sims,
        "n_trades": 0, "null_mean": float(out.mean()), "null_p95": float(np.percentile(out, 95)), "kind": "shift",
    }

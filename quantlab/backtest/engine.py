"""Backtest vetorizado com execução realista.

Convenção temporal (sem lookahead):
- `target[t]` é a posição desejada decidida com informação até o FECHAMENTO da barra t.
- A posição executada é `pos[t] = target[t - lag]`, assumida desde a ABERTURA de t até a
  abertura de t+1. O retorno da barra é open[t+1]/open[t] - 1.
- Custo cobrado na barra t = |pos[t] - pos[t-1]| * custo_por_lado(t). O deslize ligado à
  volatilidade usa o range da barra t-1, que é conhecido na abertura de t.
Posições são frações do patrimônio (1.0 = 100% comprado, -1.0 = 100% vendido).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quantlab.execution import ExecutionModel, FillModel, apply_fill_stress


@dataclass
class BacktestResult:
    index: pd.DatetimeIndex
    pos: np.ndarray        # posição executada por barra
    gross: np.ndarray      # retorno bruto por barra
    cost: np.ndarray       # custo por barra (fração do patrimônio)
    net: np.ndarray        # retorno líquido por barra
    turnover: np.ndarray
    equity: np.ndarray
    trades: pd.DataFrame
    cost_bps_side: np.ndarray

    @property
    def net_series(self) -> pd.Series:
        return pd.Series(self.net, index=self.index)


def shift_lag(x: np.ndarray, lag: int) -> np.ndarray:
    if lag <= 0:
        return x.copy()
    out = np.zeros_like(x)
    out[lag:] = x[:-lag]
    return out


def run_backtest(bars: pd.DataFrame, target: np.ndarray, exec_model: ExecutionModel, tf_minutes: int,
                 fill: FillModel | None = None, rng: np.random.Generator | None = None,
                 with_trades: bool = True) -> BacktestResult:
    o = bars["open"].to_numpy(dtype=float)
    h = bars["high"].to_numpy(dtype=float)
    l = bars["low"].to_numpy(dtype=float)
    c = bars["close"].to_numpy(dtype=float)
    n = len(o)
    target = np.nan_to_num(np.asarray(target, dtype=float), nan=0.0)
    if len(target) != n:
        raise ValueError("target e barras com tamanhos diferentes")

    pos = shift_lag(target, exec_model.lag_bars)
    if fill is not None:
        pos = apply_fill_stress(pos, fill, rng)

    r_oo = np.zeros(n)
    r_oo[:-1] = o[1:] / o[:-1] - 1.0

    prev_range = np.zeros(n)
    prev_range[1:] = (h[:-1] - l[:-1]) / c[:-1]
    cost_bps_side = exec_model.cost_bps_per_side(prev_range, tf_minutes)

    pos_prev = np.concatenate(([0.0], pos[:-1]))
    turnover = np.abs(pos - pos_prev)
    cost = turnover * cost_bps_side / 1e4
    gross = pos * r_oo
    net = gross - cost
    equity = np.cumprod(1.0 + net)

    if with_trades:
        trades = extract_trades(bars.index, o, c, pos, gross, cost_bps_side)
    else:
        trades = pd.DataFrame(columns=["entry_idx", "exit_idx", "entry_ts", "exit_ts", "side", "size", "bars", "entry_px", "exit_px", "ret_gross", "ret_net", "open"])
    return BacktestResult(bars.index, pos, gross, cost, net, turnover, equity, trades, cost_bps_side)


def extract_trades(index: pd.DatetimeIndex, o: np.ndarray, c: np.ndarray, pos: np.ndarray,
                   gross: np.ndarray, cost_bps_side: np.ndarray) -> pd.DataFrame:
    """Um trade = trecho contínuo com posição de mesmo sinal. Entrada/saída na abertura."""
    n = len(pos)
    sign = np.sign(pos)
    prev = np.concatenate(([0.0], sign[:-1]))
    change = np.flatnonzero(sign != prev)
    bounds = np.concatenate((change, [n]))
    rows = []
    cum_gross = np.concatenate(([0.0], np.cumsum(gross)))
    for i in range(len(change)):
        i0, i1 = bounds[i], bounds[i + 1]
        s = sign[i0]
        if s == 0:
            continue
        size = float(np.abs(pos[i0:i1]).mean())
        slip_in = cost_bps_side[i0] / 1e4
        entry_px = o[i0] * (1 + s * slip_in)
        if i1 < n:
            slip_out = cost_bps_side[i1] / 1e4
            exit_px = o[i1] * (1 - s * slip_out)
            still_open = False
        else:
            slip_out = cost_bps_side[-1] / 1e4
            exit_px = c[-1]
            still_open = True
        pnl_gross = cum_gross[i1] - cum_gross[i0]
        pnl_net = pnl_gross - size * (slip_in + slip_out)
        rows.append({
            "entry_idx": int(i0), "exit_idx": int(min(i1, n - 1)),
            "entry_ts": index[i0], "exit_ts": index[min(i1, n - 1)],
            "side": int(s), "size": size, "bars": int(i1 - i0),
            "entry_px": float(entry_px), "exit_px": float(exit_px),
            "ret_gross": float(pnl_gross), "ret_net": float(pnl_net), "open": still_open,
        })
    cols = ["entry_idx", "exit_idx", "entry_ts", "exit_ts", "side", "size", "bars", "entry_px", "exit_px", "ret_gross", "ret_net", "open"]
    return pd.DataFrame(rows, columns=cols)


def aggregate_daily(net: np.ndarray, index: pd.DatetimeIndex) -> pd.Series:
    """Retorno líquido diário (composto) a partir de retornos por barra. Base comum para
    comparar estratégias de timeframes diferentes."""
    s = pd.Series(np.log1p(net), index=index)
    return np.expm1(s.resample("1D").sum())

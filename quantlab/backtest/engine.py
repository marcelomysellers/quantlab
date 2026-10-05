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

from quantlab.execution import ExecutionModel, FillModel, apply_fill_stress, drop_unfilled_limit_entries


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
                 with_trades: bool = True, funding: np.ndarray | None = None) -> BacktestResult:
    o = bars["open"].to_numpy(dtype=float)
    h = bars["high"].to_numpy(dtype=float)
    l = bars["low"].to_numpy(dtype=float)
    c = bars["close"].to_numpy(dtype=float)
    n = len(o)
    target = np.nan_to_num(np.asarray(target, dtype=float), nan=0.0)
    if len(target) != n:
        raise ValueError("target e barras com tamanhos diferentes")

    pos = shift_lag(target, exec_model.lag_bars)
    if "open_synthetic" in bars:
        # a abertura dessa barra não existiu (minuto sem negócio / exchange fora): a ordem espera
        # a próxima abertura real; a posição anterior é carregada
        mask = bars["open_synthetic"].to_numpy(dtype=bool)
        if mask.any():
            last_real = np.maximum.accumulate(np.where(~mask, np.arange(n), 0))
            pos = pos[last_real]
    if fill is not None:
        if fill.adverse_bps is not None:
            pos = drop_unfilled_limit_entries(pos, o, c, fill.adverse_bps)
        pos = apply_fill_stress(pos, fill, rng)

    r_oo = np.zeros(n)
    r_oo[:-1] = o[1:] / o[:-1] - 1.0

    prev_range = np.zeros(n)
    prev_range[1:] = (h[:-1] - l[:-1]) / c[:-1]
    cost_bps_side = exec_model.cost_bps_per_side(prev_range, tf_minutes)

    # peso que se teria na abertura de t SEM negociar: o peso anterior derivado pelo retorno da barra t-1.
    # Comprado 100% não deriva (1 -> 1); 50% deriva com o preço; vendido 100% precisa de recompra.
    pos_prev = np.concatenate(([0.0], pos[:-1]))
    r_prev = np.concatenate(([0.0], r_oo[:-1]))
    with np.errstate(divide="ignore", invalid="ignore"):
        drift_prev = np.where(1.0 + pos_prev * r_prev != 0, pos_prev * (1.0 + r_prev) / (1.0 + pos_prev * r_prev), pos_prev)
    turnover = np.abs(pos - drift_prev)
    cost = turnover * cost_bps_side / 1e4
    gross = pos * r_oo
    net = gross - cost
    if funding is not None:
        net = net - pos * funding      # custo de carregar: comprado paga, vendido recebe
    equity = np.cumprod(1.0 + net)

    if with_trades:
        trades = extract_trades(bars.index, o, c, pos, gross, cost_bps_side, cost, drift_prev)
    else:
        trades = pd.DataFrame(columns=["entry_idx", "exit_idx", "entry_ts", "exit_ts", "side", "size", "bars", "entry_px", "exit_px", "ret_gross", "ret_net", "open"])
    return BacktestResult(bars.index, pos, gross, cost, net, turnover, equity, trades, cost_bps_side)


def extract_trades(index: pd.DatetimeIndex, o: np.ndarray, c: np.ndarray, pos: np.ndarray,
                   gross: np.ndarray, cost_bps_side: np.ndarray, cost: np.ndarray | None = None,
                   drift_prev: np.ndarray | None = None) -> pd.DataFrame:
    """Um trade = trecho contínuo com posição de mesmo sinal. Entrada/saída na abertura.
    Custo do trade = abertura da posição + todo o giro dentro do trecho (mudanças de tamanho) +
    fechamento na barra seguinte ao trecho."""
    n = len(pos)
    sign = np.sign(pos)
    prev = np.concatenate(([0.0], sign[:-1]))
    change = np.flatnonzero(sign != prev)
    bounds = np.concatenate((change, [n]))
    rows = []
    cum_gross = np.concatenate(([0.0], np.cumsum(gross)))
    if cost is None:
        cost = np.zeros(n)
    if drift_prev is None:
        drift_prev = np.concatenate(([0.0], pos[:-1]))
    cum_cost = np.concatenate(([0.0], np.cumsum(cost)))
    for i in range(len(change)):
        i0, i1 = bounds[i], bounds[i + 1]
        s = sign[i0]
        if s == 0:
            continue
        size = float(np.abs(pos[i0:i1]).mean())
        slip_in = cost_bps_side[i0] / 1e4
        entry_px = o[i0] * (1 + s * slip_in)
        entry_cost = abs(pos[i0]) * slip_in                   # só a parte que ABRE esta posição (o giro de i0 pode incluir o fechamento da anterior)
        intra_cost = cum_cost[i1] - cum_cost[i0 + 1]          # mudanças de tamanho dentro do trecho
        if i1 < n:
            slip_out = cost_bps_side[i1] / 1e4
            exit_px = o[i1] * (1 - s * slip_out)
            exit_cost = abs(drift_prev[i1]) * slip_out        # fecha o peso DERIVADO que se tinha na abertura de i1
            still_open = False
        else:
            slip_out = cost_bps_side[-1] / 1e4
            exit_px = c[-1]
            exit_cost = 0.0
            still_open = True
        pnl_gross = cum_gross[i1] - cum_gross[i0]
        pnl_net = pnl_gross - entry_cost - intra_cost - exit_cost
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
    comparar estratégias de timeframes diferentes. Dias sem nenhuma barra (fim de semana e
    feriado em mercados com sessão) são descartados, não contados como retorno zero."""
    s = pd.Series(np.log1p(net), index=index)
    g = s.resample("1D")
    out = np.expm1(g.sum())
    return out[g.count() > 0]


def funding_per_bar(bars: pd.DataFrame, funding: pd.Series) -> np.ndarray:
    """Taxa de funding atribuída à barra que contém cada carimbo de funding (0 nas demais).
    Convenção: comprado PAGA funding positivo, vendido RECEBE; o motor cobra pos * taxa."""
    f = np.zeros(len(bars))
    if funding is None or len(funding) == 0:
        return f
    idx = bars.index.searchsorted(funding.index, side="right") - 1
    ok = (idx >= 0) & (idx < len(bars))
    np.add.at(f, idx[ok], funding.to_numpy(dtype=float)[ok])
    return f

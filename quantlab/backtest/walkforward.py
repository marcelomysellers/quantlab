"""Walk-forward: a única curva que importa é a costurada fora da amostra.

Para cada janela (treino de N meses, teste de M meses, rolando de M em M):
1. avalia todas as configurações da grade NO TREINO (Sharpe dos retornos diários, custos base);
2. escolhe a melhor que tenha um mínimo de trades e cujo warmup caiba no treino;
3. aplica essa configuração no TESTE seguinte, sem olhar para ele.
A sequência dos testes é a curva OOS. Para contraste, também se guarda a "curva de vitrine":
a melhor configuração escolhida olhando o período inteiro (in-sample puro).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from quantlab.backtest.engine import aggregate_daily, run_backtest
from quantlab.backtest.metrics import sharpe
from quantlab.execution import ExecutionModel
from quantlab.strategies.base import Context, Strategy


@dataclass
class WFConfig:
    train_months: int = 12
    test_months: int = 3
    min_trades: int = 10
    warmup_frac: float = 1.0 / 3.0


@dataclass
class Fold:
    k: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    i_train: tuple[int, int] = (0, 0)
    i_test: tuple[int, int] = (0, 0)
    params: dict | None = None
    is_sharpe: float = 0.0
    oos_sharpe: float = 0.0
    oos_return: float = 0.0
    n_trades_is: int = 0
    n_configs: int = 0
    table: list[dict] = field(default_factory=list)   # (params, is_sharpe, oos_sharpe) de cada config


@dataclass
class WFResult:
    folds: list[Fold]
    oos_start: int
    oos_end: int
    oos_target: np.ndarray          # posição-alvo costurada (válida em [oos_start, oos_end))
    configs: list[dict]
    config_sr_daily: list[float]    # Sharpe diário NÃO anualizado de cada config no período inteiro
    best_full_params: dict | None
    best_full_target: np.ndarray | None


def _month_start(ts: pd.Timestamp) -> pd.Timestamp:
    ts = ts.tz_convert("UTC")
    return ts.normalize().replace(day=1)


def make_folds(index: pd.DatetimeIndex, cfg: WFConfig) -> list[Fold]:
    first, last = index[0], index[-1]
    start = _month_start(first)
    if start < first:
        start = start + pd.DateOffset(months=1)
    folds, k = [], 0
    while True:
        train_end = start + pd.DateOffset(months=cfg.train_months)
        test_end = train_end + pd.DateOffset(months=cfg.test_months)
        if test_end > last + pd.Timedelta(minutes=1):
            break
        f = Fold(k, start, train_end, train_end, test_end)
        f.i_train = (int(index.searchsorted(start)), int(index.searchsorted(train_end)))
        f.i_test = (int(index.searchsorted(train_end)), int(index.searchsorted(test_end)))
        folds.append(f)
        start = start + pd.DateOffset(months=cfg.test_months)
        k += 1
    return folds


def _sr_daily(net: np.ndarray, index: pd.DatetimeIndex, sl: slice, annualize: bool = True) -> float:
    d = aggregate_daily(net[sl], index[sl]).to_numpy()
    return sharpe(d, 365.25 if annualize else 1.0)


def walk_forward(strategy: Strategy, bars: pd.DataFrame, ctx: Context, exec_model: ExecutionModel,
                 cfg: WFConfig) -> WFResult:
    index = bars.index
    n = len(bars)
    folds = make_folds(index, cfg)
    if not folds:
        raise ValueError("dados insuficientes para uma janela de treino + teste")
    configs = strategy.grid(ctx)
    oos_target = np.zeros(n)

    # estratégias sem ajuste: posições e backtest completos uma vez por config
    cache: dict[int, tuple[np.ndarray, np.ndarray, pd.DataFrame]] = {}
    if not strategy.needs_fit:
        for ci, params in enumerate(configs):
            tgt = strategy.positions(bars, params, ctx)
            res = run_backtest(bars, tgt, exec_model, ctx.tf_minutes)
            cache[ci] = (tgt, res.net, res.trades)

    # estatísticas de período inteiro (para o DSR e a curva de vitrine). Para estratégias com
    # ajuste, o ajuste é feito no período todo: é exatamente a curva in-sample que se quer expor.
    full: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for ci, params in enumerate(configs):
        if strategy.needs_fit:
            tgt = strategy.positions(bars, params, ctx, fit_slice=slice(0, n))
            full[ci] = (tgt, run_backtest(bars, tgt, exec_model, ctx.tf_minutes, with_trades=False).net)
        else:
            full[ci] = (cache[ci][0], cache[ci][1])
    config_sr_daily = [_sr_daily(full[ci][1], index, slice(0, n), annualize=False) for ci in range(len(configs))]

    for f in folds:
        a, b = f.i_train
        c, d = f.i_test
        train_bars = b - a
        max_warm = int(train_bars * cfg.warmup_frac)
        best, best_score, best_trades = None, -np.inf, 0
        fallback, fallback_score = None, -np.inf
        rows = []
        for ci, params in enumerate(configs):
            if strategy.warmup(params) > max_warm:
                continue
            if strategy.needs_fit:
                tgt = strategy.positions(bars, params, ctx, fit_slice=slice(a, b))
                res = run_backtest(bars, tgt, exec_model, ctx.tf_minutes)
                net, trades = res.net, res.trades
            else:
                tgt, net, trades = cache[ci]
            n_tr = int(((trades["entry_idx"] >= a) & (trades["entry_idx"] < b)).sum()) if len(trades) else 0
            score = _sr_daily(net, index, slice(a, b))
            oos = _sr_daily(net, index, slice(c, d))
            rows.append({"params": params, "is_sharpe": round(score, 3), "oos_sharpe": round(oos, 3), "n_trades_is": n_tr})
            if score > fallback_score:
                fallback, fallback_score = (ci, tgt), score
            if n_tr >= cfg.min_trades and score > best_score:
                best, best_score, best_trades = (ci, tgt), score, n_tr
        f.n_configs = len(rows)
        f.table = rows
        chosen = best if best is not None else fallback
        if chosen is None:
            f.params = None
            continue
        ci, tgt = chosen
        f.params = configs[ci]
        f.is_sharpe = float(best_score if best is not None else fallback_score)
        f.n_trades_is = best_trades
        oos_target[c:d] = tgt[c:d]
        f.oos_sharpe = float(_sr_daily(run_backtest(bars.iloc[c:d], tgt[c:d], exec_model, ctx.tf_minutes).net, index[c:d], slice(0, d - c)))
        f.oos_return = float(np.prod(1.0 + run_backtest(bars.iloc[c:d], tgt[c:d], exec_model, ctx.tf_minutes).net) - 1.0)

    oos_start, oos_end = folds[0].i_test[0], folds[-1].i_test[1]

    best_full_params, best_full_target = None, None
    max_warm0 = int((folds[0].i_train[1] - folds[0].i_train[0]) * cfg.warmup_frac)
    full_scores = [(_sr_daily(full[ci][1], index, slice(oos_start, oos_end)), ci) for ci in range(len(configs))
                   if strategy.warmup(configs[ci]) <= max_warm0]
    if full_scores:
        _, ci = max(full_scores)
        best_full_params, best_full_target = configs[ci], full[ci][0]

    return WFResult(folds, oos_start, oos_end, oos_target, configs, config_sr_daily, best_full_params, best_full_target)

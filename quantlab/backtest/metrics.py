"""Métricas de desempenho e testes estatísticos.

Referências:
- Bailey & López de Prado (2012) "The Sharpe Ratio Efficient Frontier": PSR.
- Bailey & López de Prado (2014) "The Deflated Sharpe Ratio": DSR, corrige o Sharpe pelo número
  de tentativas (configurações testadas) e pela não-normalidade dos retornos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

EULER_GAMMA = 0.5772156649015329


def max_drawdown(equity: np.ndarray) -> tuple[float, int, int]:
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1.0
    trough = int(np.argmin(dd)) if len(dd) else 0
    peak_idx = int(np.argmax(equity[: trough + 1])) if len(dd) else 0
    return float(dd.min()) if len(dd) else 0.0, peak_idx, trough


def sharpe(r: np.ndarray, periods_per_year: float) -> float:
    r = np.asarray(r, dtype=float)
    if len(r) < 2 or np.std(r, ddof=1) == 0:
        return 0.0
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(periods_per_year))


def sortino(r: np.ndarray, periods_per_year: float) -> float:
    r = np.asarray(r, dtype=float)
    down = r[r < 0]
    if len(r) < 2 or len(down) == 0:
        return 0.0
    dd = np.sqrt(np.mean(down ** 2))
    return float(np.mean(r) / dd * np.sqrt(periods_per_year)) if dd > 0 else 0.0


def psr(sr_hat: float, n: int, skew: float, kurt: float, sr0: float = 0.0) -> float:
    """Probabilistic Sharpe Ratio: P(SR verdadeiro > sr0). sr_hat e sr0 NÃO anualizados;
    kurt é a curtose de Pearson (normal = 3)."""
    if n < 3:
        return 0.5
    denom = 1.0 - skew * sr_hat + (kurt - 1.0) / 4.0 * sr_hat ** 2
    if denom <= 0:
        return 1.0 if sr_hat > sr0 else 0.0
    z = (sr_hat - sr0) * np.sqrt(n - 1.0) / np.sqrt(denom)
    return float(stats.norm.cdf(z))


def expected_max_sharpe(n_trials: int, var_sr: float) -> float:
    """Sharpe máximo esperado (não anualizado) de n_trials tentativas sem habilidade."""
    if n_trials <= 1 or var_sr <= 0:
        return 0.0
    z1 = stats.norm.ppf(1.0 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    return float(np.sqrt(var_sr) * ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2))


def dsr(sr_hat: float, n: int, skew: float, kurt: float, n_trials: int, var_sr: float) -> float:
    """Deflated Sharpe Ratio: PSR contra o Sharpe que se esperaria só por ter testado n_trials vezes."""
    return psr(sr_hat, n, skew, kurt, sr0=expected_max_sharpe(n_trials, var_sr))


def block_bootstrap_sharpe(r: np.ndarray, periods_per_year: float, n_boot: int = 300,
                           block: int | None = None, seed: int = 0) -> tuple[float, float]:
    """IC 90% do Sharpe por bootstrap em blocos (preserva autocorrelação de curto prazo)."""
    r = np.asarray(r, dtype=float)
    n = len(r)
    if n < 20:
        return (0.0, 0.0)
    block = block or max(5, int(np.sqrt(n)))
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    out = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n - block + 1, n_blocks)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n]
        out[b] = sharpe(r[idx], periods_per_year)
    return float(np.percentile(out, 5)), float(np.percentile(out, 95))


def summarize(net: np.ndarray, pos: np.ndarray, turnover: np.ndarray, bars_per_year: float,
              trades: pd.DataFrame | None = None, daily: pd.Series | None = None) -> dict:
    """Resumo completo. Sharpe/Sortino/PSR/t-stat são calculados nos retornos DIÁRIOS
    (base comum entre timeframes); o restante nas barras."""
    net = np.asarray(net, dtype=float)
    n = len(net)
    years = n / bars_per_year if bars_per_year else 0.0
    equity = np.cumprod(1.0 + net)
    total = float(equity[-1] - 1.0) if n else 0.0
    if years <= 0:
        cagr = 0.0
    elif total <= -0.999999:
        cagr = -1.0   # patrimônio zerado
    else:
        cagr = float((1.0 + total) ** (1.0 / years) - 1.0)
    mdd, _, _ = max_drawdown(equity)

    d = daily.to_numpy(dtype=float) if daily is not None else net
    ppy = 365.25 if daily is not None else bars_per_year
    sr_ann = sharpe(d, ppy)
    sr_bar = float(np.mean(d) / np.std(d, ddof=1)) if len(d) > 2 and np.std(d, ddof=1) > 0 else 0.0
    skew = float(stats.skew(d)) if len(d) > 3 else 0.0
    kurt = float(stats.kurtosis(d, fisher=False)) if len(d) > 3 else 3.0
    t_stat = float(sr_bar * np.sqrt(len(d))) if len(d) > 1 else 0.0

    out = {
        "n_bars": int(n),
        "years": round(years, 3),
        "total_return": total,
        "cagr": cagr,
        "ann_vol": float(np.std(d, ddof=1) * np.sqrt(ppy)) if len(d) > 2 else 0.0,
        "sharpe": sr_ann,
        "sortino": sortino(d, ppy),
        "max_drawdown": mdd,
        "calmar": float(cagr / abs(mdd)) if mdd < 0 else 0.0,
        "exposure": float(np.mean(np.abs(pos) > 0)) if n else 0.0,
        "avg_abs_pos": float(np.mean(np.abs(pos))) if n else 0.0,
        "turnover_per_year": float(np.sum(turnover) / years) if years > 0 else 0.0,
        "t_stat": t_stat,
        "psr": psr(sr_bar, len(d), skew, kurt, 0.0),
        "skew": skew,
        "kurtosis": kurt,
        "n_days": int(len(d)),
    }
    if trades is not None and len(trades):
        closed = trades[~trades["open"]] if "open" in trades else trades
        rn = closed["ret_net"].to_numpy(dtype=float)
        wins, losses = rn[rn > 0], rn[rn <= 0]
        out.update({
            "n_trades": int(len(closed)),
            "trades_per_year": float(len(closed) / years) if years > 0 else 0.0,
            "win_rate": float(len(wins) / len(rn)) if len(rn) else 0.0,
            "avg_win": float(wins.mean()) if len(wins) else 0.0,
            "avg_loss": float(losses.mean()) if len(losses) else 0.0,
            "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) and losses.sum() < 0 else (float("inf") if len(wins) else 0.0),
            "avg_bars_in_trade": float(closed["bars"].mean()),
            "avg_trade_ret": float(rn.mean()) if len(rn) else 0.0,
        })
    else:
        out.update({"n_trades": 0, "trades_per_year": 0.0, "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
                    "profit_factor": 0.0, "avg_bars_in_trade": 0.0, "avg_trade_ret": 0.0})
    if out["profit_factor"] == float("inf"):
        out["profit_factor"] = 99.0
    return out

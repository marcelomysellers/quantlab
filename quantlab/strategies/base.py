"""Interface de estratégia.

Uma estratégia recebe barras e devolve, para cada barra t, a posição-alvo decidida com
informação até o FECHAMENTO de t (fração do patrimônio, -1..1). Só isso. Execução, custos e
lag são responsabilidade do motor, para que nenhuma estratégia "trapaceie" na execução.

Regras:
- Só use operações que olham para trás (rolling, shift positivo, ewm, cumsum...).
- `warmup(params)` informa o maior lookback; o torneio descarta configurações cujo warmup
  é grande demais para a janela de treino.
- Estratégias com `needs_fit=True` recebem `fit_slice` (índices da janela de treino) e só
  podem estimar parâmetros nesse trecho.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Context:
    tf: str
    tf_minutes: int
    bars_per_year: float
    bars_per_day: float


class Strategy:
    name: str = ""
    label: str = ""
    description: str = ""
    is_benchmark: bool = False
    needs_fit: bool = False
    min_tf_minutes: int = 1
    max_tf_minutes: int = 1440
    param_space: dict[str, list] = {}

    def grid(self, ctx: Context) -> list[dict]:
        keys = list(self.param_space)
        combos = [dict(zip(keys, v)) for v in itertools.product(*[self.param_space[k] for k in keys])]
        return [c for c in combos if self.valid(c)]

    def valid(self, params: dict) -> bool:
        return True

    def warmup(self, params: dict) -> int:
        return 0

    def positions(self, bars: pd.DataFrame, params: dict, ctx: Context, fit_slice: slice | None = None) -> np.ndarray:
        raise NotImplementedError

    def supports(self, ctx: Context) -> bool:
        return self.min_tf_minutes <= ctx.tf_minutes <= self.max_tf_minutes


def last_true_index(mask: np.ndarray) -> np.ndarray:
    """Para cada t, índice do último True em mask[:t+1] (-1 se nenhum)."""
    n = len(mask)
    idx = np.where(mask, np.arange(n), -1)
    return np.maximum.accumulate(idx)


def positions_from_events(long_entry: np.ndarray, long_exit: np.ndarray,
                          short_entry: np.ndarray, short_exit: np.ndarray) -> np.ndarray:
    """Máquina de estados vetorizada.

    Comprado se a última entrada long é mais recente que a última saída long E que a última
    entrada short (uma entrada short vira a posição). Simétrico para vendido. Empates no
    mesmo bar: saída vence a entrada (conservador); entrada long e short simultâneas = zerado.
    """
    le = last_true_index(np.asarray(long_entry, dtype=bool))
    lx = last_true_index(np.asarray(long_exit, dtype=bool))
    se = last_true_index(np.asarray(short_entry, dtype=bool))
    sx = last_true_index(np.asarray(short_exit, dtype=bool))
    pos = np.zeros(len(le))
    pos[(le >= 0) & (le > lx) & (le > se)] = 1.0
    pos[(se >= 0) & (se > sx) & (se > le)] = -1.0
    return pos


def realized_vol(close: pd.Series, window: int, bars_per_year: float) -> pd.Series:
    r = np.log(close).diff()
    return r.rolling(window).std() * np.sqrt(bars_per_year)


def vol_scale(close: pd.Series, window: int, bars_per_year: float, target: float | None, cap: float = 1.0) -> np.ndarray:
    if not target:
        return np.ones(len(close))
    rv = realized_vol(close, window, bars_per_year).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(rv > 0, target / rv, 0.0)
    return np.clip(np.nan_to_num(s, nan=0.0), 0.0, cap)

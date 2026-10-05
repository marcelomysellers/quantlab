"""Modelo de execução: o que separa um backtest honesto de um bonito.

Três coisas que o backtest ingênuo ignora e este modelo cobra:
1. Custo por lado: taxa + metade do spread + deslize fixo + deslize ligado à volatilidade.
2. Atraso: o sinal nasce no fechamento da barra t e executa na ABERTURA de t+lag (nunca no
   mesmo preço que gerou o sinal).
3. Preenchimento: ordem a mercado executa inteira, mas no preço ruim. Ordem limitada só
   executa se o preço ATRAVESSAR o limite (tocar não vale) e pode sair parcial. Além disso,
   `FillModel` permite estressar qualquer estratégia com fills parciais e ordens perdidas.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ExecutionModel:
    name: str
    fee_bps: float        # taxa por lado (taker) em bps do notional
    spread_bps: float     # spread cheio; a ordem a mercado paga metade por lado
    slippage_bps: float   # deslize fixo por lado (latência, fila)
    impact_k: float       # deslize extra = impact_k * range da barra anterior (normalizado para 1 minuto)
    lag_bars: int = 1     # sinal no fechamento de t -> execução na abertura de t+lag
    description: str = ""

    def slippage_bps_per_side(self, prev_range_frac: np.ndarray, tf_minutes: int) -> np.ndarray:
        """Deslize por lado em bps. O range da barra anterior é escalado por sqrt(1/minutos)
        para aproximar a volatilidade de ~1 minuto (o tempo que a ordem leva para executar)."""
        vol_term = self.impact_k * prev_range_frac * np.sqrt(1.0 / max(tf_minutes, 1)) * 1e4
        return self.spread_bps / 2.0 + self.slippage_bps + vol_term

    def cost_bps_per_side(self, prev_range_frac: np.ndarray, tf_minutes: int) -> np.ndarray:
        return self.fee_bps + self.slippage_bps_per_side(prev_range_frac, tf_minutes)

    def round_trip_bps_fixed(self) -> float:
        """Custo fixo de ida e volta (sem o termo de volatilidade), para referência."""
        return 2.0 * (self.fee_bps + self.spread_bps / 2.0 + self.slippage_bps)


# Cenários de referência para BTC (perpétuo em exchange grande, conta de varejo).
SCENARIOS: dict[str, ExecutionModel] = {
    "otimista": ExecutionModel(
        "otimista", fee_bps=2.0, spread_bps=1.0, slippage_bps=0.0, impact_k=0.0,
        description="taxa maker, spread mínimo, sem deslize: o melhor caso plausível",
    ),
    "base": ExecutionModel(
        "base", fee_bps=5.0, spread_bps=2.0, slippage_bps=1.0, impact_k=0.10,
        description="taxa taker de varejo, spread normal, 1 bp de deslize e deslize extra quando o mercado está rápido",
    ),
    "pessimista": ExecutionModel(
        "pessimista", fee_bps=7.5, spread_bps=4.0, slippage_bps=3.0, impact_k=0.30,
        description="taxa cheia, spread largo, deslize de 3 bps e forte penalidade em barras voláteis",
    ),
}


@dataclass(frozen=True)
class FillModel:
    """Estresse de preenchimento aplicado por trade.

    - miss_prob: probabilidade de a entrada não executar (ordem perdida/rejeitada) -> trade some.
    - partial_prob: probabilidade de a entrada executar só uma fração ~ U(partial_min, 1).
    - limit_penetration_ticks / full_fill_ticks: regra para ordens limitadas (ver limit_fill_fraction).
    """
    miss_prob: float = 0.0
    partial_prob: float = 0.0
    partial_min: float = 0.3
    limit_penetration_ticks: int = 1
    full_fill_ticks: int = 3
    adverse_bps: float | None = None   # ordem limitada: entrada é perdida se a barra de entrada andou mais que isto A FAVOR (o preço fugiu do limite)
    seed: int = 0


def limit_fill_fraction(side: int, limit_price: float, bar_high: np.ndarray, bar_low: np.ndarray,
                        tick_size: float, penetration_ticks: int = 1, full_fill_ticks: int = 3) -> np.ndarray:
    """Fração executada de uma ordem limitada em cada barra.

    Regra conservadora: tocar no preço não executa. A ordem só começa a ser preenchida quando
    o preço atravessa o limite por `penetration_ticks` e só fica 100% preenchida quando atravessa
    `full_fill_ticks`. Entre os dois, fill parcial proporcional. Isso aproxima a fila de ordens
    sem ter book nível 2.
    """
    tick = tick_size
    if side > 0:   # compra: precisa do low abaixo do limite
        pen = (limit_price - bar_low) / tick
    else:          # venda: precisa do high acima do limite
        pen = (bar_high - limit_price) / tick
    frac = (pen - penetration_ticks) / max(full_fill_ticks - penetration_ticks, 1e-9)
    frac = np.where(pen < penetration_ticks, 0.0, np.clip(frac, 0.0, 1.0))
    # ao atravessar exatamente penetration_ticks, já executa a menor fração não nula
    frac = np.where((pen >= penetration_ticks) & (frac == 0.0), 1.0 / max(full_fill_ticks, 1), frac)
    return frac


def trade_segments(pos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Início de cada trade (índice) e id de segmento por barra (-1 fora de posição)."""
    sign = np.sign(pos)
    prev = np.concatenate(([0.0], sign[:-1]))
    starts = np.flatnonzero((sign != 0) & (sign != prev))
    seg = np.cumsum(np.isin(np.arange(len(pos)), starts)) - 1
    seg = np.where(sign == 0, -1, seg)
    return starts, seg


def apply_fill_stress(pos: np.ndarray, fill: FillModel, rng: np.random.Generator | None = None) -> np.ndarray:
    """Escala cada trade por um fator sorteado: 0 (perdido), parcial ou 1."""
    if fill.miss_prob <= 0 and fill.partial_prob <= 0:
        return pos
    rng = rng or np.random.default_rng(fill.seed)
    starts, seg = trade_segments(pos)
    n_tr = len(starts)
    if n_tr == 0:
        return pos
    u = rng.random(n_tr)
    mult = np.ones(n_tr)
    mult[u < fill.miss_prob] = 0.0
    partial = (u >= fill.miss_prob) & (u < fill.miss_prob + fill.partial_prob)
    mult[partial] = rng.uniform(fill.partial_min, 1.0, partial.sum())
    out = pos.copy()
    inpos = seg >= 0
    out[inpos] = pos[inpos] * mult[seg[inpos]]
    return out


def drop_unfilled_limit_entries(pos: np.ndarray, o: np.ndarray, c: np.ndarray, adverse_bps: float) -> np.ndarray:
    """Teste de seleção adversa de Berlekamp: uma ordem limitada colocada na abertura só executa se o
    preço não fugir; se a barra de entrada andou mais que `adverse_bps` na direção do trade, a ordem
    ficou para trás e o trade inteiro é perdido. As entradas que executam são justamente as que o
    mercado andou contra: é o custo escondido do maker."""
    starts, seg = trade_segments(pos)
    if len(starts) == 0:
        return pos
    side = np.sign(pos[starts])
    move = side * (c[starts] - o[starts]) / o[starts]
    missed = move > adverse_bps / 1e4
    out = pos.copy()
    inpos = seg >= 0
    mult = np.where(missed, 0.0, 1.0)
    out[inpos] = pos[inpos] * mult[seg[inpos]]
    return out

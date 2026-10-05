"""Biblioteca de estratégias v1. Todas simples de propósito: o objetivo é o processo, não o sinal."""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab.strategies.base import Context, Strategy, positions_from_events, vol_scale


class BuyHold(Strategy):
    name = "buy_hold"
    label = "Comprar e segurar"
    description = "Sempre 100% comprado. A régua que qualquer estratégia direcional precisa bater."
    is_benchmark = True
    param_space = {}

    def positions(self, bars, params, ctx, fit_slice=None):
        return np.ones(len(bars))


class RandomEntry(Strategy):
    name = "random_entry"
    label = "Entradas aleatórias"
    description = "Entra comprado ou vendido em momentos sorteados, segura N barras. Se uma estratégia não bate isto, não tem sinal."
    is_benchmark = True
    param_space = {"hold_bars": [24, 96], "exposure": [0.5], "seed": [1, 2, 3]}

    def warmup(self, params):
        return 0

    def positions(self, bars, params, ctx, fit_slice=None):
        n = len(bars)
        hold, expo = int(params["hold_bars"]), float(params["exposure"])
        # dois geradores independentes, cada um usado uma única vez: o prefixo da série
        # não muda quando a série cresce (sem lookahead "estatístico")
        base = int(params["seed"]) * 7919 + ctx.tf_minutes
        rng_start = np.random.default_rng(base)
        rng_side = np.random.default_rng(base + 1)
        p = expo / (hold * (1.0 - expo))
        starts = rng_start.random(n) < p
        sides = rng_side.choice([-1.0, 1.0], n)
        idx = np.where(starts, np.arange(n), -1)
        last = np.maximum.accumulate(idx)
        side_last = pd.Series(np.where(starts, sides, np.nan)).ffill().fillna(0.0).to_numpy()
        active = (last >= 0) & ((np.arange(n) - last) < hold)
        return np.where(active, side_last, 0.0)


class SmaCross(Strategy):
    name = "sma_cross"
    label = "Cruzamento de médias"
    description = "Comprado quando a média rápida está acima da lenta; vendido (ou zerado, no modo só-compra) quando abaixo."
    param_space = {"fast": [10, 20, 50], "slow": [50, 100, 200], "mode": ["ls", "lo"]}

    def valid(self, p):
        return p["fast"] < p["slow"]

    def warmup(self, p):
        return int(p["slow"])

    def positions(self, bars, p, ctx, fit_slice=None):
        c = bars["close"]
        diff = (c.rolling(int(p["fast"])).mean() - c.rolling(int(p["slow"])).mean()).to_numpy()
        pos = np.sign(np.nan_to_num(diff, nan=0.0))
        if p["mode"] == "lo":
            pos = np.maximum(pos, 0.0)
        return pos


class TSMom(Strategy):
    name = "tsmom"
    label = "Momentum de série temporal"
    description = "Sinal = sinal do retorno das últimas L barras (Moskowitz, Ooi & Pedersen). Opcionalmente dimensiona a posição para uma volatilidade-alvo."
    param_space = {"lookback": [12, 24, 48, 96, 192], "vol_target": [None, 0.5]}

    def warmup(self, p):
        return int(p["lookback"])

    def positions(self, bars, p, ctx, fit_slice=None):
        c = bars["close"]
        L = int(p["lookback"])
        mom = (c / c.shift(L) - 1.0).to_numpy()
        sig = np.sign(np.nan_to_num(mom, nan=0.0))
        return sig * vol_scale(c, L, ctx.bars_per_year, p["vol_target"])


class Donchian(Strategy):
    name = "donchian"
    label = "Rompimento Donchian"
    description = "Compra no rompimento da máxima de N barras, vende no rompimento da mínima; sai no canal mais curto (N/2) contrário."
    param_space = {"n": [20, 40, 55, 80, 100, 150]}

    def warmup(self, p):
        return int(p["n"])

    def positions(self, bars, p, ctx, fit_slice=None):
        n = int(p["n"])
        m = max(n // 2, 2)
        h, l, c = bars["high"], bars["low"], bars["close"]
        hi_n = h.rolling(n).max().shift(1)
        lo_n = l.rolling(n).min().shift(1)
        hi_m = h.rolling(m).max().shift(1)
        lo_m = l.rolling(m).min().shift(1)
        long_entry = (c > hi_n).to_numpy()
        short_entry = (c < lo_n).to_numpy()
        long_exit = (c < lo_m).to_numpy()
        short_exit = (c > hi_m).to_numpy()
        return positions_from_events(long_entry, long_exit, short_entry, short_exit)


class BollingerMR(Strategy):
    name = "bollinger_mr"
    label = "Reversão à média (Bollinger)"
    description = "Compra quando o z-score do preço contra a média de N barras cai abaixo de -k, zera quando volta à média; simétrico na venda."
    param_space = {"n": [20, 50, 100], "k": [1.5, 2.0, 2.5]}

    def warmup(self, p):
        return int(p["n"])

    def positions(self, bars, p, ctx, fit_slice=None):
        n, k = int(p["n"]), float(p["k"])
        c = bars["close"]
        ma, sd = c.rolling(n).mean(), c.rolling(n).std()
        z = ((c - ma) / sd).to_numpy()
        z = np.nan_to_num(z, nan=0.0)
        return positions_from_events(z < -k, z >= 0.0, z > k, z <= 0.0)


class RsiMR(Strategy):
    name = "rsi_mr"
    label = "Reversão à média (RSI)"
    description = "Compra com RSI abaixo de `lo`, zera acima de 50; vende com RSI acima de 100-lo, zera abaixo de 50."
    param_space = {"n": [7, 14, 21], "lo": [20, 30]}

    def warmup(self, p):
        return int(p["n"]) * 3

    def positions(self, bars, p, ctx, fit_slice=None):
        n, lo = int(p["n"]), float(p["lo"])
        hi = 100.0 - lo
        c = bars["close"]
        d = c.diff()
        up = d.clip(lower=0.0).ewm(alpha=1.0 / n, adjust=False).mean()
        dn = (-d.clip(upper=0.0)).ewm(alpha=1.0 / n, adjust=False).mean()
        rs = up / dn.replace(0.0, np.nan)
        rsi = (100.0 - 100.0 / (1.0 + rs)).fillna(50.0).to_numpy()
        return positions_from_events(rsi < lo, rsi > 50.0, rsi > hi, rsi < 50.0)


class HourSeasonality(Strategy):
    name = "hour_seasonality"
    label = "Sazonalidade por hora"
    description = "Na janela de treino, mede o retorno médio por hora do dia (UTC); opera comprado nas k melhores horas e vendido nas k piores. Teste clássico de padrão que costuma sumir fora da amostra."
    needs_fit = True
    max_tf_minutes = 60
    param_space = {"k": [2, 4], "long_only": [True, False]}

    def positions(self, bars, p, ctx, fit_slice=None):
        k, long_only = int(p["k"]), bool(p["long_only"])
        o = bars["open"]
        # retorno que uma posição-alvo decidida na barra t de fato captura: open[t+1] -> open[t+2]
        fwd = (o.shift(-2) / o.shift(-1) - 1.0)
        hours = bars.index.hour.to_numpy()
        sl = fit_slice if fit_slice is not None else slice(0, len(bars))
        df = pd.DataFrame({"h": hours[sl], "r": fwd.to_numpy()[sl]}).dropna()
        by_hour = df.groupby("h")["r"].mean().sort_values()
        if len(by_hour) < 2 * k:
            return np.zeros(len(bars))
        best = set(by_hour.index[-k:])
        worst = set(by_hour.index[:k])
        pos = np.zeros(len(bars))
        pos[np.isin(hours, list(best))] = 1.0
        if not long_only:
            pos[np.isin(hours, list(worst))] = -1.0
        return pos


REGISTRY: dict[str, Strategy] = {s.name: s for s in (
    BuyHold(), RandomEntry(), SmaCross(), TSMom(), Donchian(), BollingerMR(), RsiMR(), HourSeasonality(),
)}

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
        cand = np.flatnonzero(rng_start.random(n) < p)
        sides = rng_side.choice([-1.0, 1.0], len(cand))
        pos = np.zeros(n)
        busy_until = -1
        for s_i, side in zip(cand, sides):
            if s_i < busy_until:          # já está dentro de um trade: não sobrepõe nem vira
                continue
            pos[s_i: s_i + hold] = side
            busy_until = s_i + hold
        return pos


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
        # o retorno "futuro" da linha t usa open[t+1] e open[t+2]: as duas últimas linhas do treino
        # olhariam para o teste; cortam-se 2 linhas do fim da janela de ajuste
        sl = fit_slice if fit_slice is not None else slice(0, len(bars))
        sl = slice(sl.start or 0, max((sl.stop if sl.stop is not None else len(bars)) - 2, sl.start or 0))
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


class WeeklyReversal(Strategy):
    name = "weekly_reversal"
    label = "Reversão semanal (contínua)"
    description = "Posição = −retorno das últimas L horas dividido pela volatilidade do mesmo horizonte, limitado a ±1 (vende o que subiu na semana, compra o que caiu). Nasceu do painel de IC (H014) e foi registrada como H022."
    param_space = {"lookback_h": [72, 168, 336], "mode": ["ls", "lo"], "scale": [1.0, 2.0]}
    min_tf_minutes = 60
    max_tf_minutes = 1440

    def _bars(self, p, ctx):
        return max(int(p["lookback_h"] * 60 / ctx.tf_minutes), 2)

    def warmup(self, p):
        return int(p["lookback_h"])   # em barras de 1 h, limite superior (conservador em timeframes maiores)

    def positions(self, bars, p, ctx, fit_slice=None):
        L = self._bars(p, ctx)
        lp = np.log(bars["close"])
        ret = lp - lp.shift(L)
        vol = lp.diff().rolling(L).std() * np.sqrt(L)
        zsc = (ret / vol).to_numpy()
        pos = -np.clip(np.nan_to_num(zsc, nan=0.0) / float(p["scale"]), -1.0, 1.0)
        if p["mode"] == "lo":
            pos = np.maximum(pos, 0.0)
        return pos


def ladder_with_band(target: np.ndarray, band: float, ret: np.ndarray | None = None) -> np.ndarray:
    """Transforma um alvo contínuo em 0..1 numa posição com banda de não-negociação.

    - alvo <= 0: sai inteiro; alvo >= 1: entra inteiro (os extremos são exatos, por definição);
    - no meio, só rebalanceia quando |alvo − peso atual| >= banda; entre rebalanceamentos o peso
      fica parado (o motor cobra giro só nas mudanças, que é o que acontece de verdade);
    - se `ret` é dado, o peso atual comparado com o alvo é o peso DERIVADO pelo retorno
      (sem negociar, a fração do patrimônio em BTC sobe quando o BTC sobe).
    """
    n = len(target)
    pos = np.zeros(n)
    cur = 0.0
    for t in range(n):
        tg = target[t]
        if np.isnan(tg):
            pos[t] = cur
            continue
        held = cur
        if ret is not None and cur > 0 and not np.isnan(ret[t]):
            held = cur * (1.0 + ret[t]) / (1.0 + cur * ret[t])
        if tg <= 0.0:
            cur = 0.0
        elif tg >= 1.0:
            cur = 1.0
        elif abs(tg - held) >= band:
            cur = float(tg)
        else:
            cur = held            # não negocia: carrega o peso derivado
        pos[t] = cur
    return pos


def _bars_per_day(ctx: Context) -> int:
    return max(int(round(ctx.bars_per_day)), 1)


class ValueLadder(Strategy):
    name = "value_ladder"
    label = "Escada de valor (média móvel)"
    description = "Posição entre 0 e 1 em função do z-score do preço contra a média móvel: totalmente dentro abaixo de z_lo, totalmente fora acima de z_hi, linear no meio, com banda de não-negociação. Compra na baixa e descasca na alta, só-compra."
    param_space = {"anchor_days": [50, 100], "zpair": ["-1/1", "-1.5/1.5", "-1/2"], "band": [0.1, 0.25]}
    min_tf_minutes = 240

    def warmup(self, p):
        return int(p["anchor_days"])

    def positions(self, bars, p, ctx, fit_slice=None):
        N = int(p["anchor_days"]) * _bars_per_day(ctx)
        lo, hi = (float(x) for x in p["zpair"].split("/"))
        lp = np.log(bars["close"])
        dev = lp - lp.rolling(N).mean()
        zsc = (dev / dev.rolling(N).std()).to_numpy()
        target = np.clip((hi - zsc) / (hi - lo), 0.0, 1.0)
        return ladder_with_band(target, float(p["band"]), bars["close"].pct_change().to_numpy())


class DrawdownLadder(Strategy):
    name = "drawdown_ladder"
    label = "Escada de queda (média na baixa, descasca na alta)"
    description = "Compra em escada conforme a queda desde a máxima de N dias: fora na máxima, totalmente dentro quando a queda atinge dd_full, proporcional no meio; descasca conforme o preço recupera. Banda de não-negociação."
    param_space = {"high_days": [90, 180], "dd_full": [0.2, 0.3, 0.5], "band": [0.1, 0.25]}
    min_tf_minutes = 240

    def warmup(self, p):
        return int(p["high_days"])

    def positions(self, bars, p, ctx, fit_slice=None):
        N = int(p["high_days"]) * _bars_per_day(ctx)
        dd = (1.0 - bars["close"] / bars["close"].rolling(N).max()).to_numpy()
        target = np.clip(dd / float(p["dd_full"]), 0.0, 1.0)
        return ladder_with_band(target, float(p["band"]), bars["close"].pct_change().to_numpy())


class MvrvLadder(Strategy):
    name = "mvrv_ladder"
    label = "Escada de MVRV (on-chain, 2 dias de atraso)"
    description = "Totalmente dentro quando o z-score de 365 dias do MVRV está abaixo de lo, fora acima de hi, linear no meio. Dado diário da CoinMetrics com 2 dias de defasagem (não é point-in-time). Só faz sentido para BTC."
    param_space = {"lo": [-1.0, -1.5], "hi": [1.0, 1.5, 2.0], "band": [0.1, 0.25]}
    min_tf_minutes = 240
    _z_cache: pd.Series | None = None

    def warmup(self, p):
        return 0

    def _z(self) -> pd.Series:
        if MvrvLadder._z_cache is None:
            from quantlab.research.signal_scan import load_coinmetrics
            cm = load_coinmetrics()
            m = cm["CapMVRVCur"]
            zs = (m - m.rolling(365).mean()) / m.rolling(365).std()
            zs.index = zs.index.tz_localize("UTC") + pd.Timedelta(days=2)
            MvrvLadder._z_cache = zs
        return MvrvLadder._z_cache

    def positions(self, bars, p, ctx, fit_slice=None):
        zs = self._z().reindex(bars.index, method="ffill").to_numpy()
        lo, hi = float(p["lo"]), float(p["hi"])
        target = np.clip((hi - zs) / (hi - lo), 0.0, 1.0)
        target = np.where(np.isnan(zs), 0.0, target)   # sem dado on-chain (depois de 2026-05): fora
        return ladder_with_band(target, float(p["band"]), bars["close"].pct_change().to_numpy())


class ConstantMix(Strategy):
    name = "constant_mix"
    label = "Mistura constante com banda"
    description = "Peso-alvo fixo em BTC (50% ou 75%), rebalanceado só quando o peso derivado pelo preço sai da banda: vende na alta e compra na baixa mecanicamente. Referência para medir se as escadas acrescentam algo além do prêmio de rebalanceamento."
    is_benchmark = True
    param_space = {"weight": [0.5, 0.75], "band": [0.05, 0.1, 0.2]}
    min_tf_minutes = 240

    def positions(self, bars, p, ctx, fit_slice=None):
        target = np.full(len(bars), float(p["weight"]))
        return ladder_with_band(target, float(p["band"]), bars["close"].pct_change().to_numpy())


REGISTRY: dict[str, Strategy] = {s.name: s for s in (
    BuyHold(), RandomEntry(), SmaCross(), TSMom(), Donchian(), BollingerMR(), RsiMR(), HourSeasonality(), WeeklyReversal(),
    ValueLadder(), DrawdownLadder(), MvrvLadder(), ConstantMix(),
)}

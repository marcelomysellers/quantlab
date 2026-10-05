"""Especificação de instrumentos.

Tudo que depende do mercado (sessão, tick, valor do ponto, barras por ano) mora aqui,
para que o motor seja o mesmo para BTC e, depois, para o mini-índice (WIN).
"""
from __future__ import annotations

from dataclasses import dataclass

TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
PANDAS_RULE = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    tick_size: float          # menor variação de preço
    point_value: float        # moeda por 1.0 de preço por unidade/contrato
    minutes_per_day: float    # minutos negociados por dia
    trading_days_per_year: float
    quote_currency: str = "USD"
    always_open: bool = True  # 24/7 (cripto) ou sessão (bolsa)

    @property
    def minutes_per_year(self) -> float:
        return self.minutes_per_day * self.trading_days_per_year

    def bars_per_year(self, tf: str) -> float:
        if tf == "1d":
            return self.trading_days_per_year
        return self.minutes_per_year / TF_MINUTES[tf]

    def bars_per_day(self, tf: str) -> float:
        if tf == "1d":
            return 1.0
        return self.minutes_per_day / TF_MINUTES[tf]


BTCUSD = Instrument(
    symbol="BTCUSD",
    name="Bitcoin / USD",
    tick_size=0.1,
    point_value=1.0,
    minutes_per_day=1440.0,
    trading_days_per_year=365.25,
    quote_currency="USD",
    always_open=True,
)

# Mini-índice Bovespa: 1 ponto = R$0,20; tick = 5 pontos = R$1,00; pregão ~09:00-18:25.
WIN = Instrument(
    symbol="WIN",
    name="Mini Índice Bovespa",
    tick_size=5.0,
    point_value=0.20,
    minutes_per_day=565.0,
    trading_days_per_year=252.0,
    quote_currency="BRL",
    always_open=False,
)

INSTRUMENTS = {i.symbol: i for i in (BTCUSD, WIN)}

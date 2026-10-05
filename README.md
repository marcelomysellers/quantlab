# Quant Lab

Laboratório para testar métodos quantitativos de forma honesta: backtests sem lookahead, custos e execução realistas, walk-forward, comparação contra entradas aleatórias, correção por número de tentativas e um frontend onde as estratégias competem entre si.

Começou no Bitcoin por facilidade de dados. O motor é agnóstico ao instrumento: o mini-índice (WIN) entra trocando o adaptador de dados e a especificação em `quantlab/instruments.py`.

## O que tem aqui

```
quantlab/
  instruments.py        especificação de instrumento (tick, valor do ponto, sessão, barras/ano)
  execution.py          modelo de execução: taxa, spread, deslize, atraso, fills parciais, ordem limitada
  data/
    bitfinex_github.py  ingestão do dataset público Bitfinex (BTC/USD 1 min, 2013-2019)
    binance.py          fetcher data.binance.vision (rode na sua máquina; a nuvem não alcança a Binance)
    store.py            parquet 1m, grade regular, reamostragem, relatório de qualidade
  strategies/
    base.py             interface, máquina de estados vetorizada, dimensionamento por volatilidade
    library.py          buy_hold, random_entry, sma_cross, tsmom, donchian, bollinger_mr, rsi_mr, hour_seasonality
  backtest/
    engine.py           backtest vetorizado open-to-open, custos por giro, extração de trades
    metrics.py          Sharpe, Sortino, drawdown, PSR, DSR, t-stat, bootstrap em blocos
    montecarlo.py       nulo de entradas aleatórias com a mesma exposição
    walkforward.py      janelas rolantes, seleção no treino, curva OOS costurada, curva de vitrine
  tournament.py         tudo x tudo, 3 cenários de custo, estresse de fills, duelos, JSON
  cli.py
tests/test_engine.py    sanidade do motor + teste de lookahead de todas as estratégias
web/                    frontend Vite + React + lightweight-charts
results/runs/<id>/      saída de cada torneio (ignorado pelo git)
```

## Rodar

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .
python tests/test_engine.py

# dados: opção A (qualquer lugar) dataset público Bitfinex 2013-2019
git clone --filter=blob:none --no-checkout --depth 1 https://github.com/Zombie-3000/Bitfinex-historical-data data/external/bitfinex-hist
(cd data/external/bitfinex-hist && git checkout HEAD -- BTCUSD/Candles_1m/201{3,4,5,6,7,8,9}/merged.csv)
python -m quantlab.cli ingest-bitfinex
python -m quantlab.cli quality

# dados: opção B (sua máquina) Binance perpétuo 1 min + funding, de 2020 em diante
python -m quantlab.data.binance --symbol BTCUSDT --market um --start 2020-01

# torneio (5 min para 6 timeframes em 3 anos de 1 minuto) e publicação para o frontend
python -m quantlab.cli tournament --tfs 1d,4h,1h,15m,5m,1m --start 2017-01-01 --end 2020-01-01 --publish

# frontend
cd web && npm install && npm run dev      # http://localhost:5173
```

## Método (o que o torneio cobra de cada estratégia)

1. **Sem lookahead, por construção.** A estratégia decide no fechamento de t; o motor executa na abertura de t+1. `tests/test_engine.py` trunca a série e confirma que nenhuma posição anterior ao corte muda, para todas as estratégias.
2. **Custos antes de sinal.** Cada mudança de posição paga taxa + metade do spread + deslize fixo + deslize proporcional ao range da barra anterior. Três cenários: otimista, base, pessimista.
3. **Execução realista.** Ordem a mercado executa inteira, no preço ruim. Ordem limitada só executa se o preço atravessa o limite (tocar não vale) e pode sair parcial (`limit_fill_fraction`). Cada estratégia ainda passa por um estresse com 5% de entradas perdidas e 30% de fills parciais (`FillModel`).
4. **Walk-forward.** Treino de 12 meses, teste de 3, rolando. A configuração vencedora no treino é aplicada ao teste seguinte. Só a curva costurada dos testes conta; a "curva de vitrine" (melhor parâmetro olhando tudo) fica no gráfico para mostrar o tamanho do overfitting.
5. **O nulo certo.** 300 estratégias sorteadas com o mesmo número de trades, durações, lado e custos. O p-valor é a fração que iguala ou supera o Sharpe real.
6. **Contar as tentativas.** Sharpe deflacionado (Bailey & López de Prado, 2014) pelo tamanho da grade testada. Estatísticas em retornos diários, base comum entre timeframes.
7. **Veredito.** Aprovada: Sharpe OOS > 0,5, p < 0,05, DSR > 0,90, Sharpe positivo no pessimista, 30+ trades. Promissora: Sharpe > 0, p < 0,15, 30+ trades. Reprovada: o resto.

## Resultado do primeiro torneio (BTC/USD, OOS 2018-2019)

- Nenhuma estratégia aprovada. Duas promissoras: momentum de série temporal no diário (Sharpe 1,1; p = 0,08) e rompimento Donchian em 1 hora (Sharpe 0,8; p = 0,15). Ambas com poucos trades: não dá para operar com essa evidência.
- Abaixo de 1 hora, tudo morre no custo. Em 1 minuto, até entradas aleatórias perdem 99% do capital, porque uma estratégia que gira milhares de vezes por ano paga milhares de vezes 14 bps.
- As reversões à média (Bollinger, RSI) perderam em todos os timeframes num período de tendência forte. Sazonalidade por hora não sobrevive fora da amostra em nenhum timeframe.

## Adicionar uma estratégia

Crie uma classe em `quantlab/strategies/library.py` herdando de `Strategy`, declare `param_space`, implemente `positions()` só com operações que olham para trás (`rolling`, `shift` positivo, `ewm`) e registre no `REGISTRY`. Rode os testes e depois o torneio com `--publish`.

## Próximos passos

- Dados recentes (2020+) via `quantlab.data.binance` na sua máquina, com funding rate do perpétuo como custo e como sinal.
- Mini-índice: adaptador MetaTrader 5 / CSV da corretora, sessão 09:00-18:25, custos em R$/contrato convertidos para bps pelo valor do ponto.
- Estratégias com ordem limitada usando `limit_fill_fraction` (fila e fill parcial modelados).
- Combinação de estratégias pouco correlacionadas (a aba Duelo já mostra a carteira 50/50).

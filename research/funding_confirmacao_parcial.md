# Confirmação fora da amostra do funding: 2025-09-20 a 2026-09-21

> Leitura PARCIAL, não é a confirmação pré-registrada (que começa em 2024-01 e precisa do funding oficial da sua máquina). Funding do repositório ZuShen168/funding_rate_data (commit e6a2d81, 2026-10-05), 2025-08-21 a 2026-09-20, carimbos arredondados ao minuto; os primeiros 30 dias só aquecem o percentil móvel.

Funding (BTCUSDT_funding_binance_zushen168_2025-08_2026-09.parquet): 1027 pagamentos na janela (2025-09-20 a 2026-09-20), média 0.28 bps por 8 h (3.1% ao ano). Preço: spot (BTCUSDT-BINANCE, 2019-12-01 a 2026-09-20). Parâmetros da H023 fixos em 2020-2023: 24 h, percentil 10 móvel de 90 dias. Nulo: 200 deslocamentos.

## 1. Funding como sinal (H016) na janela, preço spot

| bucket | horizonte | retorno médio (bps) | t | n | consistência entre anos |
|---|---|---|---|---|---|
| funding > p90 | 1h | -1.1 | -0.3 | 121 | 50% |
| funding < p10 | 1h | +0.9 | +0.1 | 116 | 100% |
| meio (p10-p90) | 1h | -0.6 | -0.3 | 789 | 50% |
| funding > p90 | 8h | -7.3 | -0.6 | 121 | 100% |
| funding < p10 | 8h | -14.8 | -0.9 | 116 | 100% |
| meio (p10-p90) | 8h | -0.8 | -0.2 | 789 | 50% |
| funding > p90 | 24h | -27.6 | -1.2 | 121 | 100% |
| funding < p10 | 24h | -26.5 | -1.1 | 116 | 100% |
| meio (p10-p90) | 24h | -4.9 | -0.6 | 789 | 50% |

## 2. Carry com regra de percentil (H017) na janela: só o funding recebido, 30 bps por entrada e saída

| regra | tempo posicionado | entradas | bruto a.a. | líquido a.a. | pior mês | meses negativos |
|---|---|---|---|---|---|---|
| entra > p60, sai < p30 | 48% | 4 | +2.6% | +1.5% | +0.00% | 0 |
| entra > p70, sai < p40 | 37% | 4 | +2.1% | +0.7% | +0.00% | 0 |
| entra > p80, sai < p50 | 30% | 4 | +1.8% | +0.4% | +0.00% | 0 |
| sempre posicionado | 100% | 1 | +3.1% | +2.8% | -0.18% | 3 |

## 3. Estratégia contrária ao funding negativo (H023): comprado 24 h após funding < p10 móvel

### Preço spot

| cenário | Sharpe | CAGR | trades | exposição | drawdown | p contra deslocamento | Sharpe 2025 | Sharpe 2026 |
|---|---|---|---|---|---|---|---|---|
| base | -1.18 | -27.3% | 40 | 21% | -27% | 0.710 | -2.00 | -0.90 |
| pessimista | -1.41 | -31.5% | 40 | 21% | -31% | 0.690 | -2.31 | -1.11 |
| maker+filtro | -1.17 | -24.1% | 26 | 15% | -30% | 0.700 | -3.01 | -0.50 |

## Veredito pré-registrado (preço spot, sem funding recebido): **MORTA: Sharpe base ≤ 0 fora da amostra**

- ✗ Sharpe base > 0,5: -1.18
- ✗ p contra deslocamento < 0,10: 0.710
- ✗ maker com filtro > 0: -1.17
- ✗ CAGR pessimista > 0: -31.5%
- ✓ ≥ 30 trades: 40

## Contexto da janela (para não ler demais num ano só)

- BTC foi de 115,724 para 81,164 na janela (-29.9%); comprar-e-segurar: Sharpe -0.57, drawdown -53%.
- Nulo deslocado com a mesma exposição (400 simulações, custos base): mediana -0.68, p10 -1.70, p90 +0.65; 25% das simulações ficaram acima de zero e 69% acima da estratégia (-1.18). A maior parte da perda é beta de estar comprado num ano de queda; o timing do funding não acrescentou nada.
- Retorno médio nas 24 h seguintes a um funding < p10: -27 bps (t -1.1, n 116), contra +54 bps (t +2,4) em 2023 e sinal positivo em 2020-2023. O efeito que sustentava a H023 não aparece neste ano.
- Meses com posição: Sep/2025 a Jun/2026; eventos por mês: Sep/25 6, Oct/25 24, Nov/25 8, Dec/25 2, Jan/26 1, Feb/26 31, Mar/26 22, Apr/26 18, May/26 3, Jun/26 1. De julho a setembro de 2026 o funding ficou positivo (0,6 bps por 8 h) e não houve evento.
- Fonte do funding: `ZuShen168/funding_rate_data` (parquet `venue=binance`, commit e6a2d81 de 2026-10-05): 1116 pagamentos de 8 h entre 2025-08-21 e 2026-09-20. Metade dos carimbos vinha alguns milissegundos depois da hora cheia (como o `fundingTime` da API da Binance); arredondados ao minuto, 100% caem na grade de 8 h e faltam 69 de 1185 (6%). Unidade conferida: `rate_apr = rate_raw × 1095`, logo `rate_raw` é a taxa decimal por 8 h. Média 0.31 bps por 8 h (3.4% ao ano), contra 0,72 em 2023. Correlação com a Bybit nos mesmos carimbos: 0.49.
- O que falta para a confirmação pré-registrada: o funding oficial de 2024-01 a 2025-08 (20 meses, inclusive a alta de 2024), que só sai da sua máquina com `python -m quantlab.data.binance --symbol BTCUSDT --market um --interval 1h --start 2020-01 --public`.

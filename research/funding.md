# Funding do perpétuo BTCUSDT (Binance, 2020-2023): sinal, carry e custo

Funding médio no período: 1.37 bps por 8 h, 15.0% ao ano. 4383 pagamentos.

## 1. Funding como sinal (H016): retorno após funding em percentil extremo (percentil móvel de 90 dias)

| bucket | horizonte | retorno médio (bps) | t | n | consistência entre anos |
|---|---|---|---|---|---|
| funding > p90 | 1h | +5.0 | +1.2 | 374 | 50% |
| funding < p10 | 1h | +3.6 | +0.7 | 443 | 50% |
| meio (p10-p90) | 1h | +2.6 | +2.4 | 3477 | 75% |
| funding > p90 | 8h | -4.7 | -0.4 | 374 | 50% |
| funding < p10 | 8h | +25.7 | +2.1 | 443 | 100% |
| meio (p10-p90) | 8h | +1.3 | +0.4 | 3477 | 75% |
| funding > p90 | 24h | +7.0 | +0.4 | 374 | 50% |
| funding < p10 | 24h | +81.6 | +4.2 | 443 | 100% |
| meio (p10-p90) | 24h | +1.3 | +0.2 | 3477 | 50% |

## 2. Carry com regra de percentil (H017): só o funding recebido, 30 bps por entrada e saída, sem P&L da base e sem liquidação

| regra | tempo posicionado | entradas | bruto a.a. | líquido a.a. | pior mês | meses negativos |
|---|---|---|---|---|---|---|
| entra > p60, sai < p30 | 49% | 19 | +11.2% | +9.7% | -0.03% | 1 |
| entra > p70, sai < p40 | 39% | 15 | +10.1% | +9.0% | +0.00% | 0 |
| entra > p80, sai < p50 | 31% | 13 | +8.7% | +7.7% | +0.00% | 0 |
| sempre posicionado | 100% | 1 | +15.0% | +14.9% | -0.53% | 3 |

## 3. Funding como custo (H018): estratégia sempre comprada paga o funding (2020-2023, custos base)

| estratégia | exposição média | funding pago a.a. | Sharpe sem | Sharpe com | CAGR sem | CAGR com |
|---|---|---|---|---|---|---|
| tsmom 4h {'lookback': 24, 'vol_target': 0.5} | 0.07 | 4.8% | -0.18 | -0.27 | -20.3% | -24.0% |
| tsmom 4h {'lookback': 96, 'vol_target': None} | 0.12 | 8.8% | +0.52 | +0.39 | +13.1% | +3.5% |
| sma_cross 1d {'fast': 10, 'slow': 100, 'mode': 'lo'} | 0.59 | 13.7% | +0.99 | +0.72 | +44.7% | +26.2% |
| sma_cross 1d {'fast': 20, 'slow': 100, 'mode': 'ls'} | 0.16 | 11.7% | +0.34 | +0.16 | -0.9% | -11.8% |
| buy_hold 1d {} | 1.00 | 15.0% | +1.00 | +0.78 | +55.5% | +33.9% |

## 4. Estratégia contrária ao funding negativo (H023): comprado 24 h após cada funding abaixo do percentil 10 móvel, abril/2020 a 2023

| cenário | Sharpe | CAGR | trades | exposição | drawdown | p contra deslocamento |
|---|---|---|---|---|---|---|
| base | +1.05 | +30.3% | 127 | 18% | -23% | 0.045 |
| pessimista | +0.87 | +23.7% | 127 | 18% | -25% | 0.040 |
| maker+filtro | +0.78 | +16.5% | 75 | 11% | -22% | 0.030 |

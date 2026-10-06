# Confirmação fora da amostra do funding: 2025-09-20 a 2026-09-21

> Leitura PARCIAL, não é a confirmação pré-registrada (que começa em 2024-01 e precisa do funding oficial da sua máquina). Funding do repositório ZuShen168/funding_rate_data (commit e6a2d81, 2026-10-05), 2025-08-21 a 2026-09-20; os primeiros 30 dias só aquecem o percentil móvel.

Funding (BTCUSDT_funding_binance_zushen168_2025-08_2026-09.parquet): 1027 pagamentos na janela (2025-09-20 a 2026-09-20), média 0.28 bps por 8 h (3.1% ao ano). Preço: spot (BTCUSDT-BINANCE, 2019-12-01 a 2026-09-20). Parâmetros da H023 fixos em 2020-2023: 24 h, percentil 10 móvel de 90 dias. Nulo: 200 deslocamentos.

## 1. Funding como sinal (H016) na janela, preço spot

| bucket | horizonte | retorno médio (bps) | t | n | consistência entre anos |
|---|---|---|---|---|---|
| funding > p90 | 1h | -2.9 | -0.7 | 121 | 100% |
| funding < p10 | 1h | -0.8 | -0.2 | 116 | 100% |
| meio (p10-p90) | 1h | -1.2 | -0.8 | 789 | 50% |
| funding > p90 | 8h | -8.3 | -0.7 | 121 | 100% |
| funding < p10 | 8h | -13.6 | -0.9 | 116 | 50% |
| meio (p10-p90) | 8h | -2.2 | -0.5 | 789 | 100% |
| funding > p90 | 24h | -24.9 | -1.1 | 121 | 100% |
| funding < p10 | 24h | -18.6 | -0.7 | 116 | 100% |
| meio (p10-p90) | 24h | -4.8 | -0.6 | 789 | 50% |

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
| base | -0.90 | -21.4% | 40 | 21% | -23% | 0.620 | -1.41 | -0.71 |
| pessimista | -1.15 | -26.1% | 40 | 21% | -26% | 0.615 | -1.72 | -0.95 |
| maker+filtro | -0.70 | -13.0% | 26 | 14% | -18% | 0.525 | -1.70 | -0.16 |

## Veredito pré-registrado (preço spot, sem funding recebido): **MORTA: Sharpe base ≤ 0 fora da amostra**

- ✗ Sharpe base > 0,5: -0.90
- ✗ p contra deslocamento < 0,10: 0.620
- ✗ maker com filtro > 0: -0.70
- ✗ CAGR pessimista > 0: -26.1%
- ✓ ≥ 30 trades: 40

## Contexto da janela (para não ler demais num ano só)

- BTC caiu de 115.724 para 81.164 na janela (−29,9%); comprar-e-segurar: Sharpe −0,57, drawdown −53%.
- Nulo deslocado com a mesma exposição (400 simulações, custos base): mediana −0,67, p10 −1,72, p90 +0,66; 25% das simulações ficaram acima de zero e 59% acima da estratégia (−0,90). A maior parte da perda é beta de estar comprado num ano de queda; o timing do funding ficou um pouco abaixo do aleatório.
- Retorno médio nas 24 h seguintes a um funding < p10: −19 bps (t −0,7), contra +54 bps (t +2,4) em 2023 e sinal positivo em 2020-2023. O efeito que sustentava a H023 não aparece neste ano.
- Meses com posição: set/2025 a jun/2026; de julho a setembro de 2026 o funding não caiu abaixo do percentil 10 móvel (sem eventos), então a estratégia ficou de fora.
- Fonte do funding: `ZuShen168/funding_rate_data` (parquet `venue=binance`, commit e6a2d81 de 2026-10-05), 1.116 pagamentos de 8 h entre 2025-08-21 e 2026-09-20, 69 carimbos faltantes (6%). Unidade conferida: `rate_apr = rate_raw × 1095`, logo `rate_raw` é a taxa decimal por 8 h. Média 0,31 bps por 8 h (3,4% ao ano), contra 0,72 em 2023.
- O que falta para a confirmação pré-registrada: o funding oficial de 2024-01 a 2025-08 (20 meses, inclusive a alta de 2024), que só sai da sua máquina com `python -m quantlab.data.binance --symbol BTCUSDT --market um --interval 1h --start 2020-01 --public`.

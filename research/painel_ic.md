# Painel de IC pré-registrado (Binance, barras de 1 hora)

115 testes de IC (feature × horizonte × escopo). Treino 2020-2023, confirmação 2024-2025, 2026 lacrado.
Regra escrita antes de rodar: |t| > 3 no treino, sobrevive a Benjamini-Hochberg 10% dentro do escopo, mesmo sinal e |t| > 2 na confirmação.

## Aprovadas: 35 testes, que são 4 apostas distintas: liquidez, on-chain valuation, reversão curta, reversão semanal

Features correlacionadas medem o mesmo efeito; o que conta como evidência é o número de clusters, não de linhas.

| cluster | escopo | feature | horizonte | IC treino | t treino | t sem sobreposição | % meses + | IC confirm. | t confirm. | consistência entre símbolos |
|---|---|---|---|---|---|---|---|---|---|---|
| liquidez | BTC | amihud_24h_z | 24h | +0.067 | +3.2 | +2.7 | 67% | +0.072 | +2.3 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 1h | -0.017 | -3.7 | -3.7 | 25% | -0.031 | -5.9 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 4h | -0.044 | -5.4 | -5.3 | 21% | -0.068 | -5.9 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 12h | -0.099 | -7.1 | -5.8 | 17% | -0.124 | -6.5 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 24h | -0.145 | -7.5 | -6.0 | 17% | -0.182 | -6.6 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 72h | -0.281 | -9.2 | -5.6 | 8% | -0.293 | -7.0 | 1.0 |
| reversão curta | BTC | pos_range_24h | 1h | -0.060 | -13.9 | -13.9 | 0% | -0.055 | -12.1 | 1.0 |
| reversão curta | BTC | pos_range_24h | 4h | -0.062 | -8.3 | -7.6 | 15% | -0.062 | -7.0 | 1.0 |
| reversão curta | BTC | pos_range_24h | 12h | -0.052 | -3.7 | -3.0 | 31% | -0.061 | -3.6 | 1.0 |
| reversão curta | BTC | pos_range_24h | 24h | -0.079 | -4.5 | -3.2 | 27% | -0.056 | -2.4 | 1.0 |
| reversão curta | BTC | ret_1h | 1h | -0.068 | -10.1 | -10.1 | 12% | -0.056 | -5.8 | 1.0 |
| reversão curta | BTC | ret_1h | 4h | -0.043 | -10.1 | -4.3 | 4% | -0.036 | -4.5 | 1.0 |
| reversão curta | BTC | ret_1h | 12h | -0.021 | -5.0 | -2.7 | 21% | -0.016 | -3.1 | 1.0 |
| reversão curta | BTC | ret_1h | 24h | -0.020 | -4.9 | -2.6 | 21% | -0.025 | -4.9 | 1.0 |
| reversão curta | BTC | ret_24h | 1h | -0.041 | -8.2 | -8.2 | 10% | -0.055 | -8.5 | 1.0 |
| reversão curta | BTC | ret_24h | 4h | -0.063 | -7.3 | -8.4 | 15% | -0.068 | -6.3 | 1.0 |
| reversão curta | BTC | ret_24h | 12h | -0.073 | -5.0 | -4.8 | 25% | -0.084 | -4.3 | 1.0 |
| reversão curta | BTC | ret_24h | 24h | -0.088 | -5.2 | -3.6 | 25% | -0.065 | -2.5 | 1.0 |
| reversão curta | BTC | ret_24h_vol | 1h | -0.042 | -8.0 | -8.0 | 10% | -0.054 | -8.4 | 1.0 |
| reversão curta | BTC | ret_24h_vol | 4h | -0.062 | -6.5 | -7.6 | 17% | -0.063 | -6.2 | 1.0 |
| reversão curta | BTC | ret_24h_vol | 12h | -0.063 | -4.0 | -3.7 | 31% | -0.069 | -3.7 | 1.0 |
| reversão curta | BTC | ret_4h | 1h | -0.067 | -14.7 | -14.7 | 4% | -0.045 | -6.5 | 1.0 |
| reversão curta | BTC | ret_4h | 4h | -0.068 | -10.1 | -7.4 | 4% | -0.037 | -3.2 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 1h | -0.040 | -9.7 | -9.7 | 6% | -0.044 | -9.0 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 4h | -0.062 | -8.2 | -8.7 | 17% | -0.062 | -5.7 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 12h | -0.080 | -5.5 | -5.0 | 23% | -0.070 | -3.9 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 24h | -0.108 | -5.6 | -5.9 | 21% | -0.070 | -2.9 | 1.0 |
| reversão semanal | BTC | ret_168h | 1h | -0.020 | -4.2 | -4.2 | 31% | -0.034 | -6.2 | 1.0 |
| reversão semanal | BTC | ret_168h | 4h | -0.046 | -5.7 | -6.4 | 25% | -0.062 | -6.2 | 1.0 |
| reversão semanal | BTC | ret_168h | 12h | -0.085 | -5.4 | -5.2 | 19% | -0.096 | -5.6 | 1.0 |
| reversão semanal | BTC | ret_168h | 24h | -0.117 | -5.7 | -4.8 | 17% | -0.115 | -4.6 | 1.0 |
| reversão semanal | BTC | ret_72h | 1h | -0.019 | -4.5 | -4.5 | 33% | -0.034 | -5.2 | 1.0 |
| reversão semanal | BTC | ret_72h | 4h | -0.041 | -5.7 | -6.3 | 25% | -0.057 | -4.7 | 1.0 |
| reversão semanal | BTC | ret_72h | 12h | -0.060 | -4.3 | -4.3 | 31% | -0.074 | -3.7 | 1.0 |
| reversão semanal | BTC | ret_72h | 24h | -0.087 | -4.6 | -2.8 | 33% | -0.074 | -3.2 | 1.0 |

## BTC: os 12 maiores |t| no treino, com a confirmação ao lado

| feature | horizonte | IC treino | t treino | % meses + | BH 10% | IC confirm. | t confirm. | sinal repete? |
|---|---|---|---|---|---|---|---|---|
| ret_4h | 1h | -0.067 | -14.7 | 4% | ✓ | -0.045 | -6.5 | sim |
| pos_range_24h | 1h | -0.060 | -13.9 | 0% | ✓ | -0.055 | -12.1 | sim |
| ret_4h | 4h | -0.068 | -10.1 | 4% | ✓ | -0.037 | -3.2 | sim |
| ret_1h | 1h | -0.068 | -10.1 | 12% | ✓ | -0.056 | -5.8 | sim |
| ret_1h | 4h | -0.043 | -10.1 | 4% | ✓ | -0.036 | -4.5 | sim |
| pos_range_168h | 1h | -0.040 | -9.7 | 6% | ✓ | -0.044 | -9.0 | sim |
| mvrv_z365 | 72h | -0.281 | -9.2 | 8% | ✓ | -0.293 | -7.0 | sim |
| pos_range_24h | 4h | -0.062 | -8.3 | 15% | ✓ | -0.062 | -7.0 | sim |
| pos_range_168h | 4h | -0.062 | -8.2 | 17% | ✓ | -0.062 | -5.7 | sim |
| ret_24h | 1h | -0.041 | -8.2 | 10% | ✓ | -0.055 | -8.5 | sim |
| ret_24h_vol | 1h | -0.042 | -8.0 | 10% | ✓ | -0.054 | -8.4 | sim |
| funding_last | 24h | -0.117 | -7.6 | 12% | ✓ | +nan | +nan | – |

## Calendário por bucket (H015), retorno da próxima hora em unidades de volatilidade, 10 ativos agrupados, 2020-2025

| bucket | valor | média (vol) | t | n | consistência entre anos |
|---|---|---|---|---|---|
| hour | 21 | +0.0765 | +3.5 | 2192 | 67% (6 anos) |
| dow | 2 | +0.0412 | +3.0 | 7536 | 100% (6 anos) |
| dow | 3 | -0.0350 | -2.5 | 7512 | 100% (6 anos) |
| hour | 19 | +0.0484 | +2.1 | 2192 | 67% (6 anos) |
| hours_to_funding | 4 | +0.0267 | +2.0 | 6576 | 67% (6 anos) |
| hour | 20 | +0.0481 | +1.9 | 2192 | 67% (6 anos) |
| us_session | 0 | +0.0092 | +1.8 | 37264 | 83% (6 anos) |
| dow | 0 | +0.0216 | +1.6 | 7512 | 67% (6 anos) |
| hours_to_funding | 3 | +0.0230 | +1.6 | 6576 | 67% (6 anos) |
| hours_to_funding | 5 | +0.0185 | +1.5 | 6576 | 50% (6 anos) |
| hour | 22 | -0.0314 | -1.4 | 2192 | 83% (6 anos) |
| hour | 7 | +0.0257 | +1.2 | 2192 | 83% (6 anos) |
| dow | 6 | +0.0106 | +1.1 | 7512 | 83% (6 anos) |
| hour | 18 | -0.0245 | -1.0 | 2192 | 83% (6 anos) |
| hour | 5 | +0.0137 | +0.8 | 2192 | 67% (6 anos) |

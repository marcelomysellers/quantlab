# Painel de IC pré-registrado (Binance, barras de 1 hora)

200 testes de IC (feature × horizonte × escopo). Treino 2020-2023, confirmação 2024-2025, 2026 lacrado.
Regra escrita antes de rodar: |t| > 3 no treino, sobrevive a Benjamini-Hochberg 10% dentro do escopo, mesmo sinal e |t| > 2 na confirmação.

## Aprovadas: 76 testes, que são 7 apostas distintas: cruzado, liquidez, on-chain valuation, reversão curta, reversão semanal, volatilidade, volume

Features correlacionadas medem o mesmo efeito; o que conta como evidência é o número de clusters, não de linhas.

| cluster | escopo | feature | horizonte | IC treino | t treino | t sem sobreposição | % meses + | IC confirm. | t confirm. | consistência entre símbolos |
|---|---|---|---|---|---|---|---|---|---|---|
| cruzado | painel_alts | btc_ret_24h | 1h | -0.045 | -12.2 | -12.2 | 4% | -0.035 | -6.1 | 1.0 |
| cruzado | painel_alts | btc_ret_24h | 4h | -0.067 | -10.8 | -8.5 | 8% | -0.044 | -4.5 | 1.0 |
| cruzado | painel_alts | btc_ret_24h | 12h | -0.074 | -7.2 | -5.9 | 12% | -0.059 | -3.9 | 1.0 |
| cruzado | painel_alts | btc_ret_24h | 24h | -0.071 | -5.6 | -3.1 | 19% | -0.060 | -2.8 | 1.0 |
| liquidez | painel_alts | amihud_24h_z | 12h | +0.033 | +3.8 | +3.9 | 73% | +0.031 | +2.5 | 1.0 |
| liquidez | BTC | amihud_24h_z | 24h | +0.067 | +3.2 | +2.7 | 67% | +0.072 | +2.3 | 1.0 |
| liquidez | painel_alts | amihud_24h_z | 24h | +0.041 | +3.8 | +2.1 | 75% | +0.040 | +2.4 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 1h | -0.017 | -3.7 | -3.7 | 25% | -0.031 | -5.9 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 4h | -0.044 | -5.4 | -5.3 | 21% | -0.068 | -5.9 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 12h | -0.099 | -7.1 | -5.8 | 17% | -0.124 | -6.5 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 24h | -0.145 | -7.5 | -6.0 | 17% | -0.182 | -6.6 | 1.0 |
| on-chain valuation | BTC | mvrv_z365 | 72h | -0.281 | -9.2 | -5.6 | 8% | -0.293 | -7.0 | 1.0 |
| reversão curta | BTC | pos_range_24h | 1h | -0.060 | -13.9 | -13.9 | 0% | -0.055 | -12.1 | 1.0 |
| reversão curta | painel_alts | pos_range_24h | 1h | -0.053 | -15.5 | -15.5 | 0% | -0.036 | -8.9 | 1.0 |
| reversão curta | BTC | pos_range_24h | 4h | -0.062 | -8.3 | -7.6 | 15% | -0.062 | -7.0 | 1.0 |
| reversão curta | painel_alts | pos_range_24h | 4h | -0.050 | -9.5 | -8.2 | 8% | -0.029 | -4.4 | 1.0 |
| reversão curta | BTC | pos_range_24h | 12h | -0.052 | -3.7 | -3.0 | 31% | -0.061 | -3.6 | 1.0 |
| reversão curta | BTC | pos_range_24h | 24h | -0.079 | -4.5 | -3.2 | 27% | -0.056 | -2.4 | 1.0 |
| reversão curta | BTC | ret_1h | 1h | -0.068 | -10.1 | -10.1 | 12% | -0.056 | -5.8 | 1.0 |
| reversão curta | painel_alts | ret_1h | 1h | -0.058 | -13.1 | -13.1 | 6% | -0.042 | -7.4 | 1.0 |
| reversão curta | BTC | ret_1h | 4h | -0.043 | -10.1 | -4.3 | 4% | -0.036 | -4.5 | 1.0 |
| reversão curta | painel_alts | ret_1h | 4h | -0.041 | -12.8 | -8.0 | 8% | -0.026 | -5.8 | 1.0 |
| reversão curta | BTC | ret_1h | 12h | -0.021 | -5.0 | -2.7 | 21% | -0.016 | -3.1 | 1.0 |
| reversão curta | painel_alts | ret_1h | 12h | -0.020 | -7.2 | -2.2 | 10% | -0.012 | -3.3 | 1.0 |
| reversão curta | BTC | ret_1h | 24h | -0.020 | -4.9 | -2.6 | 21% | -0.025 | -4.9 | 1.0 |
| reversão curta | painel_alts | ret_1h | 24h | -0.022 | -7.1 | -2.8 | 12% | -0.013 | -3.3 | 1.0 |
| reversão curta | BTC | ret_24h | 1h | -0.041 | -8.2 | -8.2 | 10% | -0.055 | -8.5 | 1.0 |
| reversão curta | painel_alts | ret_24h | 1h | -0.045 | -13.0 | -13.0 | 2% | -0.035 | -7.0 | 1.0 |
| reversão curta | BTC | ret_24h | 4h | -0.063 | -7.3 | -8.4 | 15% | -0.068 | -6.3 | 1.0 |
| reversão curta | painel_alts | ret_24h | 4h | -0.064 | -11.6 | -9.5 | 6% | -0.043 | -5.0 | 1.0 |
| reversão curta | BTC | ret_24h | 12h | -0.073 | -5.0 | -4.8 | 25% | -0.084 | -4.3 | 1.0 |
| reversão curta | painel_alts | ret_24h | 12h | -0.073 | -8.4 | -7.0 | 12% | -0.051 | -3.5 | 1.0 |
| reversão curta | BTC | ret_24h | 24h | -0.088 | -5.2 | -3.6 | 25% | -0.065 | -2.5 | 1.0 |
| reversão curta | painel_alts | ret_24h | 24h | -0.080 | -7.5 | -4.0 | 15% | -0.046 | -2.8 | 1.0 |
| reversão curta | BTC | ret_24h_vol | 1h | -0.042 | -8.0 | -8.0 | 10% | -0.054 | -8.4 | 1.0 |
| reversão curta | painel_alts | ret_24h_vol | 1h | -0.044 | -12.3 | -12.3 | 2% | -0.032 | -6.3 | 1.0 |
| reversão curta | BTC | ret_24h_vol | 4h | -0.062 | -6.5 | -7.6 | 17% | -0.063 | -6.2 | 1.0 |
| reversão curta | painel_alts | ret_24h_vol | 4h | -0.060 | -10.4 | -8.7 | 8% | -0.037 | -4.5 | 1.0 |
| reversão curta | BTC | ret_24h_vol | 12h | -0.063 | -4.0 | -3.7 | 31% | -0.069 | -3.7 | 1.0 |
| reversão curta | painel_alts | ret_24h_vol | 12h | -0.062 | -6.9 | -6.0 | 17% | -0.040 | -3.0 | 1.0 |
| reversão curta | painel_alts | ret_24h_vol | 24h | -0.067 | -6.3 | -3.6 | 19% | -0.032 | -2.0 | 1.0 |
| reversão curta | BTC | ret_4h | 1h | -0.067 | -14.7 | -14.7 | 4% | -0.045 | -6.5 | 1.0 |
| reversão curta | painel_alts | ret_4h | 1h | -0.058 | -16.7 | -16.7 | 4% | -0.039 | -8.4 | 1.0 |
| reversão curta | BTC | ret_4h | 4h | -0.068 | -10.1 | -7.4 | 4% | -0.037 | -3.2 | 1.0 |
| reversão curta | painel_alts | ret_4h | 4h | -0.057 | -10.9 | -6.9 | 6% | -0.024 | -3.6 | 1.0 |
| reversão curta | painel_alts | ret_4h | 12h | -0.026 | -5.0 | -4.4 | 19% | -0.014 | -2.2 | 1.0 |
| reversão curta | painel_alts | ret_4h | 24h | -0.043 | -7.4 | -4.1 | 15% | -0.019 | -2.4 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 1h | -0.040 | -9.7 | -9.7 | 6% | -0.044 | -9.0 | 1.0 |
| reversão semanal | painel_alts | pos_range_168h | 1h | -0.031 | -9.9 | -9.9 | 10% | -0.023 | -5.8 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 4h | -0.062 | -8.2 | -8.7 | 17% | -0.062 | -5.7 | 1.0 |
| reversão semanal | painel_alts | pos_range_168h | 4h | -0.039 | -7.2 | -6.8 | 15% | -0.032 | -4.5 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 12h | -0.080 | -5.5 | -5.0 | 23% | -0.070 | -3.9 | 1.0 |
| reversão semanal | painel_alts | pos_range_168h | 12h | -0.042 | -4.5 | -5.4 | 21% | -0.035 | -3.4 | 1.0 |
| reversão semanal | BTC | pos_range_168h | 24h | -0.108 | -5.6 | -5.9 | 21% | -0.070 | -2.9 | 1.0 |
| reversão semanal | painel_alts | pos_range_168h | 24h | -0.057 | -4.6 | -3.4 | 29% | -0.043 | -2.8 | 1.0 |
| reversão semanal | BTC | ret_168h | 1h | -0.020 | -4.2 | -4.2 | 31% | -0.034 | -6.2 | 1.0 |
| reversão semanal | painel_alts | ret_168h | 1h | -0.017 | -6.3 | -6.3 | 17% | -0.017 | -4.3 | 1.0 |
| reversão semanal | BTC | ret_168h | 4h | -0.046 | -5.7 | -6.4 | 25% | -0.062 | -6.2 | 1.0 |
| reversão semanal | painel_alts | ret_168h | 4h | -0.030 | -6.0 | -4.8 | 15% | -0.034 | -4.7 | 1.0 |
| reversão semanal | BTC | ret_168h | 12h | -0.085 | -5.4 | -5.2 | 19% | -0.096 | -5.6 | 1.0 |
| reversão semanal | painel_alts | ret_168h | 12h | -0.048 | -5.3 | -5.1 | 23% | -0.056 | -4.6 | 1.0 |
| reversão semanal | BTC | ret_168h | 24h | -0.117 | -5.7 | -4.8 | 17% | -0.115 | -4.6 | 1.0 |
| reversão semanal | painel_alts | ret_168h | 24h | -0.071 | -5.7 | -2.5 | 19% | -0.074 | -4.3 | 1.0 |
| reversão semanal | BTC | ret_72h | 1h | -0.019 | -4.5 | -4.5 | 33% | -0.034 | -5.2 | 1.0 |
| reversão semanal | painel_alts | ret_72h | 1h | -0.021 | -7.1 | -7.1 | 12% | -0.022 | -4.5 | 1.0 |
| reversão semanal | BTC | ret_72h | 4h | -0.041 | -5.7 | -6.3 | 25% | -0.057 | -4.7 | 1.0 |
| reversão semanal | painel_alts | ret_72h | 4h | -0.031 | -6.5 | -5.7 | 17% | -0.038 | -4.0 | 1.0 |
| reversão semanal | BTC | ret_72h | 12h | -0.060 | -4.3 | -4.3 | 31% | -0.074 | -3.7 | 1.0 |
| reversão semanal | painel_alts | ret_72h | 12h | -0.045 | -5.7 | -4.4 | 23% | -0.047 | -3.5 | 1.0 |
| reversão semanal | BTC | ret_72h | 24h | -0.087 | -4.6 | -2.8 | 33% | -0.074 | -3.2 | 1.0 |
| reversão semanal | painel_alts | ret_72h | 24h | -0.056 | -5.4 | -2.1 | 23% | -0.057 | -3.2 | 1.0 |
| volatilidade | painel_alts | rng_1h_atr | 1h | +0.012 | +3.7 | +3.7 | 65% | +0.017 | +3.5 | 1.0 |
| volatilidade | painel_alts | vol_ratio_24_168 | 1h | +0.014 | +4.3 | +4.3 | 77% | +0.009 | +2.2 | 1.0 |
| volume | painel_alts | vol_trend_24_168 | 1h | +0.012 | +3.8 | +3.8 | 81% | +0.012 | +3.1 | 1.0 |
| volume | painel_alts | z_vol_1h_30d | 12h | +0.021 | +3.5 | +2.2 | 67% | +0.024 | +3.3 | 1.0 |
| volume | painel_alts | z_vol_24h_90d | 1h | +0.009 | +3.5 | +3.5 | 69% | +0.013 | +3.8 | 1.0 |

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

## painel_alts: os 12 maiores |t| no treino, com a confirmação ao lado

| feature | horizonte | IC treino | t treino | % meses + | BH 10% | IC confirm. | t confirm. | sinal repete? |
|---|---|---|---|---|---|---|---|---|
| ret_4h | 1h | -0.058 | -16.7 | 4% | ✓ | -0.039 | -8.4 | sim |
| pos_range_24h | 1h | -0.053 | -15.5 | 0% | ✓ | -0.036 | -8.9 | sim |
| ret_1h | 1h | -0.058 | -13.1 | 6% | ✓ | -0.042 | -7.4 | sim |
| ret_24h | 1h | -0.045 | -13.0 | 2% | ✓ | -0.035 | -7.0 | sim |
| ret_1h | 4h | -0.041 | -12.8 | 8% | ✓ | -0.026 | -5.8 | sim |
| ret_24h_vol | 1h | -0.044 | -12.3 | 2% | ✓ | -0.032 | -6.3 | sim |
| btc_ret_24h | 1h | -0.045 | -12.2 | 4% | ✓ | -0.035 | -6.1 | sim |
| ret_24h | 4h | -0.064 | -11.6 | 6% | ✓ | -0.043 | -5.0 | sim |
| ret_4h | 4h | -0.057 | -10.9 | 6% | ✓ | -0.024 | -3.6 | sim |
| btc_ret_24h | 4h | -0.067 | -10.8 | 8% | ✓ | -0.044 | -4.5 | sim |
| ret_24h_vol | 4h | -0.060 | -10.4 | 8% | ✓ | -0.037 | -4.5 | sim |
| pos_range_168h | 1h | -0.031 | -9.9 | 10% | ✓ | -0.023 | -5.8 | sim |

## Calendário por bucket (H015), retorno da próxima hora em unidades de volatilidade, 10 ativo(s) agrupado(s), 2020-2025

| bucket | valor | média (vol) | t | n | consistência entre anos |
|---|---|---|---|---|---|
| hour | 21 | +0.0536 | +7.7 | 21690 | 83% (6 anos) |
| dow | 2 | +0.0246 | +5.9 | 74568 | 83% (6 anos) |
| us_session | 0 | +0.0075 | +4.3 | 368724 | 83% (6 anos) |
| dow | 5 | +0.0140 | +4.3 | 74328 | 83% (6 anos) |
| hour | 13 | -0.0378 | -4.1 | 21690 | 67% (6 anos) |
| dow | 3 | -0.0177 | -4.0 | 74328 | 83% (6 anos) |
| dow | 4 | +0.0135 | +3.3 | 74328 | 67% (6 anos) |
| hour | 23 | +0.0262 | +3.2 | 21690 | 67% (6 anos) |
| hour | 20 | +0.0238 | +3.1 | 21690 | 67% (6 anos) |
| hour | 22 | -0.0194 | -2.9 | 21690 | 67% (6 anos) |
| hours_to_funding | 5 | +0.0116 | +2.9 | 65069 | 67% (6 anos) |
| hour | 19 | +0.0186 | +2.7 | 21690 | 50% (6 anos) |
| hours_to_funding | 4 | +0.0110 | +2.5 | 65069 | 50% (6 anos) |
| hour | 9 | +0.0177 | +2.4 | 21690 | 83% (6 anos) |
| hour | 3 | +0.0153 | +2.3 | 21689 | 83% (6 anos) |

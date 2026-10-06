# data/public

Dados pequenos e versionados, para que a sessão em nuvem (que não alcança exchanges) possa usar o que a sua máquina baixa.

Como gerar (na sua máquina, dentro do repositório, com o venv ativo):

```bash
python -m quantlab.data.binance --symbol BTCUSDT --market um --interval 1h --start 2020-01 --public
git add data/public && git commit -m "Dados Binance UM 1h + funding" && git push
```

Arquivos esperados:
- `BTCUSDT-BINANCE-UM_1h_raw.parquet`: barras de 1 hora do perpétuo com volume taker-buy e número de negócios (~2 MB)
- `BTCUSDT-BINANCE-UM_funding.parquet`: funding a cada 8 horas

Não coloque aqui o 1 minuto completo (~150 MB): o GitHub recusa arquivos acima de 100 MB.

Depois que os arquivos estiverem no repositório, a confirmação fora da amostra da estratégia contrária ao funding (H023) é um comando:

```bash
python -m quantlab.research.funding_study --confirm      # escreve research/funding_confirmacao.md
```

O critério de sobrevivência está pré-registrado na linha H023 de `research/hipoteses.md`, antes de olhar o resultado.

## Arquivos presentes

| arquivo | fonte | período | uso |
|---|---|---|---|
| `BTCUSDT_funding_binance_zushen168_2025-08_2026-09.parquet` | [ZuShen168/funding_rate_data](https://github.com/ZuShen168/funding_rate_data), `data/funding/venue=binance/data.parquet`, commit e6a2d81 (2026-10-05) | 2025-08-21 a 2026-09-20, 1.116 pagamentos de 8 h (6% de carimbos faltantes) | leitura parcial da H023 (`research/funding_confirmacao_parcial.md`) e conferência cruzada do funding oficial quando ele chegar |
| `BTCUSDT_funding_bybit_zushen168_2025-08_2026-09.parquet` | idem, `venue=bybit` | idem | conferência cruzada (correlação 0,51 com a Binance nos carimbos comuns) |

Esses dois não substituem o fetcher: faltam 2024-01 a 2025-08, e o funding oficial da Binance é a fonte da confirmação pré-registrada.

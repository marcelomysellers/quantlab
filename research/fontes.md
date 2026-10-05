# O que existe publicamente sobre edges em cripto e no mini-índice

Levantamento feito em 2026-10-05 por busca na web. Cada item traz o que a fonte afirma e um grau de evidência:
**A** = trabalho acadêmico com teste fora da amostra ou dados abertos; **B** = praticante mostrando dados e método; **C** = fórum, plataforma ou marketing, sem dados verificáveis. A maior parte do que circula em fóruns é C.

## 1. Dados públicos que o laboratório consegue usar

| Fonte | O que é | Uso aqui |
|---|---|---|
| [ff137/bitstamp-btcusd-minute-data](https://github.com/ff137/bitstamp-btcusd-minute-data) | BTC/USD 1 min desde 2012, atualizado diariamente por GitHub Action, com arquivo de proveniência de outages | **ingerido** como `BTCUSD-BITSTAMP`; base do torneio 2020-2026 |
| [Speirsy11/crypto-dataset](https://github.com/Speirsy11/crypto-dataset) | Binance 1m/5m/15m/1h/4h/1d para 10 pares, 2017-2026, Parquet via Git LFS | em download; só OHLCV (sem taker-buy) |
| [coinmetrics/data](https://github.com/coinmetrics/data) | diário desde 2009: preço, MVRV, fluxo de exchanges, oferta em exchanges, endereços ativos, hash rate, transações | **ingerido**; base da varredura de sinais on-chain |
| [supervik/historical-funding-rates-fetcher](https://github.com/supervik/historical-funding-rates-fetcher) | funding de BTC e ETH em 7 exchanges, 2020-2023 | baixado; feature de carry até 2023 |
| [haozhu18/binance-funding-rate-history](https://github.com/haozhu18/binance-funding-rate-history), [chappie2054/binance-funding-history-download](https://github.com/chappie2054/binance-funding-history-download), [gcoban/binance-public-data-downloader](https://github.com/gcoban/binance-public-data-downloader) | ferramentas para baixar funding, open interest e klines completos da Binance | rodar na sua máquina (a nuvem bloqueia a Binance) |
| [jssyxd/multi-asset-ohlcv](https://github.com/jssyxd/multi-asset-ohlcv), [mouadja02/bitcoin-technical-indicators-dataset](https://github.com/mouadja02/bitcoin-technical-indicators-dataset) | alternativas (multi-ativo; horário com indicadores) | reserva |

Os klines oficiais da Binance (data.binance.vision) trazem `taker_buy_base_volume` e `number_of_trades` por barra: é o dado de fluxo de ordens mais barato que existe, e só está disponível rodando o fetcher na sua máquina.

## 2. Praticantes com método (B)

- **Robot Wealth** (Kris Longmore). Série sobre cripto com dados e código: [The Art and Science of Trading Carry](https://robotwealth.com/the-art-and-science-of-trading-carry/), [Quantifying and Combining Crypto Alphas](https://robotwealth.com/quantifying-and-combining-crypto-alphas/), [Ideas for Crypto Stat Arb Features](https://robotwealth.com/ideas-for-crypto-stat-arb-features/), [A simple, effective way to manage turnover and not get killed by costs](https://robotwealth.com/a-simple-effective-way-to-manage-turnover-and-not-get-killed-by-costs/), [Index of Strategies](https://robotwealth.com/index-of-strategies/). Teses: carry (vender o perpétuo com prêmio, comprar spot) foi uma fonte de retorno excepcional e tem risco baixo na versão hedgeada; cestas long-short de perpétuos por prêmio têm muito mais variância; o retorno total (preço + funding) correlaciona com o prêmio do futuro, logo carry é feature útil num modelo de stat arb; controle de giro é o que separa um sinal fraco lucrativo de um sinal fraco que morre em custo. É a fonte mais próxima do que estamos fazendo.
- **Kalena, auditoria de 7 estratégias populares do Reddit** ([link](https://blog.kalena.ai/crypto-algo-trading-reddit-the-order-flow-audit-stress-testing-the-7-most-upvoted-algorithmic-strategies-against-real-market-microstructure)): a arbitragem de funding discutida no r/algotrading subestima custos de execução, que comem de 40% a 70% do rendimento de um funding de 0,01%; a correção é entrar com ordem limitada em momentos de book grosso. Fonte secundária, mas o ponto bate com a nossa tabela de timeframes.

## 3. Trabalhos acadêmicos (A)

- **Liu & Tsyvinski, Risks and Returns of Cryptocurrency** ([NBER w24877](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf), depois RFS 2021): retornos de cripto têm momentum de série temporal forte e são previstos por proxies de atenção do investidor (buscas, menções). O momentum diário que apareceu como "promissor" no nosso torneio é o mesmo efeito.
- **Time-Series and Cross-Sectional Momentum in the Cryptocurrency Market** ([AUT](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf)): momentum de série temporal rende cerca de 32% ao ano contra 15% do cross-sectional, com o dobro de Sharpe. Sem custos realistas de varejo.
- **Bitcoin intraday time-series momentum** ([Reading, 2021](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf)): o retorno da primeira meia hora prevê o da última meia hora do dia no BTC, na linha do efeito conhecido em ações. Efeito de relógio, do tipo que Laufer procurava.
- **Cryptocurrency as an Investable Asset Class: Coming of Age** ([arXiv 2510.14435](https://arxiv.org/pdf/2510.14435)): o carry (vender perpétuo, comprar spot) teve Sharpe 6,45 em 2020-2025, caiu para 4,06 em 2024 e ficou negativo em 2025; o funding médio rende cerca de 8% ao ano com volatilidade de 0,8%. Ou seja: foi o edge mais limpo da década e está decaindo.
- **The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures** ([arXiv 2607.09426](https://arxiv.org/html/2607.09426v2)): algoritmos de execução periódicos (TWAP) deixam previsibilidade de retorno em torno dos quartos de hora nos futuros de cripto. É microestrutura intradiária, o lugar onde o nosso custo mata; só vale com ordem limitada e taxa maker.
- **Short-horizon mean reversion in cryptocurrency markets: a matched cross-market measurement** ([arXiv 2608.21888](https://arxiv.org/pdf/2608.21888)): mede reversão de curtíssimo prazo entre mercados pareados; relevante para pares entre exchanges, o terreno de Frey.
- **Order flow and cryptocurrency returns** ([ScienceDirect, 2026](https://www.sciencedirect.com/science/article/pii/S1386418126000029)): o fluxo de ordens agregado prevê retornos de 1 dia (+0,2% por desvio-padrão) e 1 semana (+0,9%), com significância até 7 dias de defasagem. **Nowcasting bitcoin's crash risk with order imbalance** ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10040314/)) e **Explainable Patterns in Cryptocurrency Microstructure** ([arXiv 2602.00776](https://arxiv.org/html/2602.00776v1)) vão na mesma direção. É o argumento mais forte a favor de buscar os klines com volume taker-buy.
- **Predictability of Funding Rates** ([SSRN 5576424](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5576424)): o funding do próximo período é previsível por modelos autorregressivos simples, melhor que "sem mudança". Importa para quem vai carregar perpétuo.
- **Systematic Trend-Following with Adaptive Portfolio Construction** ([arXiv 2602.11708](https://arxiv.org/html/2602.11708v1)): seguimento de tendência em cripto com construção de carteira adaptativa; leitura para a versão multi-ativo do nosso momentum.

## 4. Brasil e mini-índice (quase tudo C)

- [SmarttBot](https://smarttbot.com/) e seu [ranking de estratégias](https://smarttbot.com/estrategias/): plataforma de robôs para WIN e WDO com milhares de backtests de usuários (a estratégia Tangram Plus cita 42 mil). Por regra da CVM só publicam resultados simulados, e a seleção dos "melhores" num ranking é exatamente o viés de teste múltiplo. Útil para ver o que a multidão opera e para custos (citam R$ 0,50 por minicontrato).
- [QuantBrasil](https://quantbrasil.com.br/blog/backtest-da-estrategia-de-gap-trap-de-compra-ou-venda/): backtests de setups populares (gap trap etc.), em geral sem walk-forward nem nulo.
- [Walk-forward backtest: como não enganar a si mesmo](https://dev.to/arthurvalle1_a2586dd2b4bc/walk-forward-backtest-como-nao-enganar-a-si-mesmo-2j95) e [BackTest ou BackTrote?](https://cartadocondado.substack.com/p/backtest-ou-backtrote): dois textos brasileiros honestos; o segundo cita o número clássico de ~5% de excesso de retorno em backtest contra ~0% fora da amostra.
- [Fórum MQL5 em português: análise de backtests de mini-índice](https://www.mql5.com/pt/forum/302403) e [séries contínuas WIN$/WDO$](https://www.mql5.com/pt/forum/23768/page2): o caminho prático para dados do WIN no MetaTrader 5 e as armadilhas da série contínua (rolagem, horário de verão).
- Não encontrei, em português, nenhum relato público com walk-forward, nulo e custos de uma estratégia de WIN que sobreviva. Isso não prova que não exista; prova que quem tem não publica, o que era esperado.

## 5. O que isso muda no plano

1. O momentum de série temporal é o efeito mais documentado e também o mais explorado; vale manter como referência, não como edge.
2. O carry de funding foi o edge mais limpo de 2020-2024 e está decaindo; ainda é a melhor "primeira estratégia de verdade" para capital pequeno, porque o risco de preço é hedgeado e o que resta é execução, contraparte e liquidação.
3. Fluxo de ordens (taker-buy, order imbalance) é o sinal fora do preço com melhor evidência acadêmica recente em horizontes de 1 dia a 1 semana, e o dado é gratuito na Binance. Prioridade de coleta.
4. Efeitos de relógio (meia hora inicial e final, quartos de hora, funding a cada 8 h) existem, mas vivem onde o custo mata; só com ordem limitada.
5. Para o WIN, o material público não tem evidência utilizável; o laboratório terá que gerar a própria.

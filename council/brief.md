# Brief para o conselho (sessão de 2026-10-05)

## Quem está perguntando

Marcelo, desenvolvedor (Next.js, Python), lendo *O homem que decifrou o mercado*. Trabalha sozinho, sem equipe de pesquisa e sem infraestrutura de baixa latência. Capital pequeno, da ordem de dezenas de milhares de reais. Objetivo: encontrar algo com edge real, verificar sem se enganar, e operar de forma automatizada. Bitcoin agora, por facilidade de dados; mini-índice (WIN, B3) depois, porque ele acredita que lá há mais estrutura explorável e menos competição no tamanho dele.

## O que já existe (repositório `quantlab`)

- **Motor de backtest** vetorizado: sinal no fechamento, execução na abertura seguinte, custos por giro (taxa + meio spread + deslize fixo + deslize por volatilidade), três cenários de custo, teste automático de lookahead em todas as estratégias.
- **Execução**: ordem a mercado paga o preço ruim; ordem limitada só executa se o preço atravessa o limite, com fill parcial; estresse com 5% de entradas perdidas e 30% de fills parciais.
- **Walk-forward** 12 meses de treino / 3 de teste; curva OOS costurada; "curva de vitrine" (melhor parâmetro olhando tudo) só para medir overfitting.
- **Nulo**: 300 estratégias de entradas aleatórias com a mesma exposição, mesma duração e mesmos custos; p-valor contra elas.
- **DSR** (Sharpe deflacionado por número de configurações testadas); estatísticas em retornos diários.
- **Frontend** com ranking, detalhe por estratégia (candles com trades, curvas, nulo, estresse, janelas), duelos e heatmap por timeframe.
- **Estratégias v1**: comprar e segurar, entradas aleatórias, cruzamento de médias, momentum de série temporal (com vol target), rompimento Donchian, reversão à média (Bollinger, RSI), sazonalidade por hora.

## Resultado do primeiro torneio (BTC/USD Bitfinex, OOS 2018-2019, custos base 14 bps ida e volta)

| Timeframe | Melhor Sharpe OOS | Estratégia | Entradas aleatórias |
|---|---|---|---|
| diário | 1,10 | momentum | -0,46 |
| 4 horas | 0,62 | Donchian | -0,13 |
| 1 hora | 0,83 | Donchian | +0,28 |
| 15 min | -0,44 | nenhuma positiva | -0,67 |
| 5 min | -0,91 | nenhuma positiva | -2,23 |
| 1 min | -4,40 | nenhuma positiva | -7,94 |

Nenhuma aprovada (critério: Sharpe > 0,5, p < 0,05 contra aleatório, DSR > 0,9, positiva no cenário pessimista, 30+ trades). Três promissoras com poucos trades. Reversão à média perdeu em tudo (período de tendência). Sazonalidade por hora morre fora da amostra.

## Dados disponíveis

- Bitfinex BTC/USD 1 minuto, 2013-2019 (2017-2019 limpo).
- CoinMetrics diário até maio de 2026, com on-chain: endereços ativos, MVRV, fluxo de entrada e saída de exchanges, oferta em exchanges, hash rate, contagem de transações, volume spot reportado.
- Binance (klines 1m com volume taker-buy e número de trades, funding rate, open interest) acessível só na máquina do Marcelo; aqui a rede bloqueia exchanges.
- Datasets públicos no GitHub em avaliação: Bitstamp 1 minuto desde 2012 atualizado diariamente; Binance 1 minuto em Parquet.
- Mini-índice: ainda sem dados; caminho provável é MetaTrader 5 de corretora (1 minuto, histórico limitado) ou CSV da Nelogica.

## Custos reais do Marcelo

- BTC: taker ~5 bps por lado, maker ~2 bps; spread ~1-2 bps em BTC; funding do perpétuo ~0,01% por 8 horas em média.
- WIN: ~R$ 0,50 por contrato ida e volta de custos de bolsa, corretagem zero em várias corretoras, tick de R$ 1 em um contrato de ~R$ 25 mil a R$ 30 mil de notional. Proporcionalmente muito mais barato que BTC.

## Restrições

- Um desenvolvedor, horas por semana, horizonte de meses.
- Latência de segundos. Sem book nível 2 por enquanto.
- Não há como "pagar pesquisadores": a alavanca é método, dados e automação.

## Pauta

1. **Diagnóstico**: o que está errado ou faltando no método e no torneio?
2. **Onde procurar**: onde um operador pequeno tem chance real? Sinais fora do preço? Quais dados buscar primeiro e por quê?
3. **Método**: como não se enganar (teste múltiplo, overfitting, regime) e como combinar sinais fracos?
4. **Execução**: maker vs taker, fills parciais, tamanho; o que muda no nosso tamanho?
5. **Plano de 90 dias**: 3 a 5 iniciativas ordenadas, cada uma com hipótese falsificável, dado necessário, métrica de sucesso e critério de abandono.
6. **Automação**: o que uma operação automatizada de uma pessoa precisa para não quebrar?

Responda no personagem, mas com honestidade: se a sua experiência não se transfere para capital pequeno, diga isso e diga o que se transfere.

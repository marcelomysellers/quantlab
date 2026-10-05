# Parecer de Sandor Straus — sessão de 2026-10-05

O desconto honesto: eu tive décadas, uma firma pagando e um mundo em que ninguém guardava intradiário. Hoje kline é commodity. Escasso, e transferível, é o que ninguém guarda por você: book e negócios como chegaram na *sua* conexão, e o intradiário do WIN. Comece a gravar hoje e nunca pare.

## 1. Diagnóstico do que existe

O motor é mais honesto que a camada de dados, e confia nela.

- `binance.py` descarta `trades`, `taker_buy_*`, `quote_volume` e `close_time`; não guarda o zip do funding nem confere `.CHECKSUM`; decide a unidade de tempo pela última linha (um mês em ms, outro em µs: os antigos viram 1970); e grava o perpétuo `BTCUSDT` em `BTCUSD_1m_raw.parquet`, o nome do spot Bitfinex: dois instrumentos, um arquivo.
- `store.py` nunca invalida o cache por timeframe: trocou a fonte, o torneio lê a antiga. A flag `synthetic` não chega ao motor: a estratégia executa em preços que não existiram, justamente nas quedas de exchange.
- `bitfinex_github.py` chama de "raw" um arquivo já alterado (high/low forçados, duplicatas descartadas sem contagem); o commit de origem não fica registrado. Limpo demais é suspeito: a Bitfinex caiu várias vezes em 2017-2019.
- Para o WIN, `regularize_1m` inventará 875 minutos por noite; `always_open` existe e ninguém consulta; a primeira barra do dia herda range zero da noite sintética. Faltam fuso, sessão, vencimentos e série contínua.

## 2. Onde procurar edge (e quais dados primeiro)

Sinais não são comigo; o dado que os outros não têm, é.

**BTC — Binance USDT-M perpétuo + Bybit** (segundo venue: separa ruído de exchange):

|Fluxo|Websocket/REST|Linhas/dia|Parquet/dia|
|---|---|---|---|
|klines 1m|`kline_1m` + vision|1.440|<1 MB|
|aggTrades|`aggTrade`|1-4 M|20-80 MB|
|funding, mark, premium|`markPrice@1s`|86 k|2 MB|
|open interest|REST por minuto|1.440|<1 MB|
|book nível 1|`bookTicker`|2-10 M|30-150 MB|
|book nível 2|`depth20@100ms`|0,9 M×40 níveis|50-150 MB|

Por exchange, 100-400 MB/dia; as duas, 6-24 GB/mês. Três carimbos por mensagem: `ts_exchange`, `ts_local_recv` (NTP) e a sequência `u`/`pu`, que prova ausência de buraco. Bruto primeiro (NDJSON zstd por hora); parquet derivado, particionado `venue/market/symbol/stream/date=/hour=`; `manifest.jsonl` com linhas, min/max ts, sha256, hash do coletor, id da conexão. Custo: VPS de US$ 10-20/mês, disco de 2 TB, Backblaze B2 a US$ 6/TB/mês; menos de R$ 150/mês.

**WIN — comece hoje**: o que não gravou não existe.

|Fonte|Dá|Histórico|Custo|
|---|---|---|---|
|MT5 da corretora (Python, Windows)|1 min, ticks bid/ask/last, DOM ao vivo|1-3 anos de 1 min; semanas de ticks; DOM zero|grátis; VPS Windows R$ 60-150/mês|
|Profit (Nelogica)|CSV de negócios e barras; ProfitDLL (feed, ordens)|anos em barras|R$ 100-300/mês|
|B3|negócios do dia (retenção curta, parte paga), vencimentos|só o que baixar|grátis a centenas de R$/mês|

Ticks 1-3 M/dia (20-60 MB), DOM a 100 ms ~7 M linhas (60-120 MB): 2-4 GB/mês. UTC, `session_date` local, fuso do servidor MT5 na proveniência. Sem horário de verão desde 2019, mas o histórico anterior tem (UTC-2); o americano desloca a abertura de NY: coluna `ny_offset`. Cada contrato é série própria; nos 10 dias antes do vencimento (quarta mais próxima do dia 15, meses pares) grave atual e seguinte; a contínua é derivada: rola quando o volume do próximo supera o atual, ajuste por diferença, `contract`/`roll_flag`, original intocado. Tabelas `calendar` (sessão do dia, feriado, vencimento, mudança de horário) e `events` (pré-abertura 08:55-09:00, leilões por túnel, circuit breaker): barra em leilão é marcada, não negociada.

## 3. Método

Prenda o método ao dado: o torneio grava hash e manifest do que leu; `synthetic` e `in_auction` entram no motor e proíbem execução; o cache é invalidado pelo hash do 1m. Guarde o bruto para re-derivar quando achar o bug do parser; vai achar.

## 4. Execução e tamanho

No seu tamanho o problema não é impacto, é prova. Cada ordem é dado: `ts_enviada`, `ts_ack`, preço e hora de cada fill, L1 no envio. Com 200 fills de 0,001 BTC e 1 WIN, os 14 bps estimados viram distribuição medida. Até lá, o cenário pessimista é o seu.

## 5. Plano de 90 dias

|# (semana)|Iniciativa|Hipótese falsificável|Dado|Sucesso|Abandono|
|---|---|---|---|---|---|
|1 (1-2)|Coletor BTC 24h|≥99,5% dos minutos cobertos por 30 dias sem intervir|tabela acima|manifest completo; parquet re-derivado bate|não se abandona; L2 cai a 1 s se ocupar >50% do disco sem uso|
|2 (1-3)|WIN: gravar hoje|O 1 min do MT5 cobre ≥2 anos com <0,5% faltante na sessão|MT5 ticks, DOM, 1 min; arquivos B3|60 pregões sem buraco; contínua com `roll_flag`|<6 meses ou sem DOM: troque de corretora ou ProfitDLL|
|3 (2-6)|Reconciliar o histórico|Bitfinex e Bitstamp concordam em 99,9% dos minutos de 2017-2019; o resto é queda|os dois datasets do GitHub|janelas de queda listadas; torneio sem elas mantém as "promissoras"|>1% em disputa: aposente o Bitfinex abaixo de 1 hora|
|4 (4-10)|Funding no motor, como custo|Funding a cada 8 h muda o Sharpe OOS do tsmom diário em >0,2|funding e `metrics` do vision|motor lê funding; vereditos refeitos|diferença <0,05 em todo timeframe: segue só como dado|
|5 (6-12)|Diário de ordens|Deslize real com limitada é menor que o cenário base|200 fills mínimos por mercado, L1 no envio|distribuição medida substitui bps fixos|custo acima do pessimista: pare abaixo do diário até entender|

## 6. O que eu não faria

Comprar histórico antes de gravar 60 dias do meu. Testar abaixo de 1 hora com kline de terceiro. "Limpar" o bruto: limpeza é camada derivada, com contagem do que mudou. Guardar só o que a estratégia de hoje usa.

## 7. Pergunta para outro membro

**Henry Laufer:** se BTC e WIN vão para um modelo só, em que relógio: minuto de calendário, fração da sessão ou barra de volume? Barra de volume não sai de kline, só de negócios; a partição depende disso.

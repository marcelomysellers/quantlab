# Parecer de Nick Patterson — sessão de 2026-10-05

Eu tinha milhares de séries, um time e uma firma pagando a limpeza; isso não se transfere. Marcelo tem uma série, dois anos aproveitáveis e horas por semana: cada "descoberta" exige mais evidência do que eu exigia. O que se transfere é a ordem: dado antes de sinal, nulo antes de veredito, contagem antes de confiança.

## 1. Diagnóstico do que existe

Olhei o dado:

- **2013-2016 não serve.** Prints a 1/10 e 1/100 do preço (1,06; 15; 20 em abr/2013), retorno de 1 minuto de 9.334%; buracos de 31 dias (2015) e 61 dias (2016).
- **2017-2019: limpo por dentro, sujo por fora.** Sem duplicata nem OHLC incoerente, mas 2,4% dos minutos são sintéticos (17% em jan/2017). O motor não vê: a abertura da barra é o primeiro minuto, sintético em 1,4% das barras de 5 min e 0,8% de 1 h no OOS, e a ordem executa no fechamento que gerou o sinal, sem deslize; a flag de `store.resample` só marca barra inteira (0,05%).
- **Preço da Bitfinex não é o do mercado.** Contra o composto CoinMetrics: prêmio de +8,4% (abr/2017), -7,9% (dez/2017), +6,6% (28/abr/2019). No melhor trimestre das promissoras (2019Q2) o prêmio foi de 0,4% a 6,0% e voltou a zero em cinco semanas: tendência que só existia ali.
- **CoinMetrics:** história recalculada em 26/fev/2021 (`AssetEODCompletionTime`), dia D fechando 27-30 h depois, fluxos de exchange com rótulos descobertos depois: não é point-in-time; defasagem mínima, 2 dias. Bitstamp 1 h (GitHub): 11% de sentinelas 1,7e308.

Na estatística:

- **tsmom diário:** Sharpe 1,10 vira 0,12 sem 2019Q2 e 0,47 sem os 5 melhores dias; os 3 maiores trades somam 1,33 de 1,03. As três promissoras ganham nos mesmos dias (02/abr/2019, 19/nov/2018), correlação 0,41-0,73: uma aposta medida três vezes.
- **O nulo não preserva a exposição.** Em `montecarlo.py` os trades sorteados se sobrepõem e se apagam: 61% de exposição e 25 trades contra 99,8% e 40 do tsmom.
- **DSR com 10 tentativas**, quando o torneio rodou 298. Com o desvio do próprio nulo (0,86 anual), o Sharpe máximo esperado por acaso é 2,50 com 298 tentativas; o DSR do tsmom cai de 0,72 para 0,03.
- **"Promissora" com p<0,15 em 34 entradas:** o acaso entrega cinco; apareceram três.

## 2. Onde procurar edge

Não em 2013-2016, não abaixo de 1 h a 14 bps, não em preço onde não se executa. Primeiro dado: Binance 2020+ (taker-buy, trades, funding, open interest), com segunda fonte por minuto (Bitstamp) e flag de desvio acima de 50 bps; traz 2022-26 como teste.

On-chain: já 146 testes (56 em `research/signal_scan_coinmetrics.md`, 90 meus). O melhor (mom_30d, p=0,004) vale p≈0,2 após 56 tentativas. `mvrv_z365`: IC 0,18-0,21 a 30 dias em 2017-22, 0,01 em 2023-26. Fluxo de exchange, o único estável, é justamente o de rótulo retroativo.

## 3. Método

- **Permutação por deslocamento circular das posições** (preserva exposição, durações e autocorrelação): tsmom p=0,124 em 2.000 permutações; Donchian 1 h p=0,08.
- **Livro de tentativas:** cada configuração, feature × horizonte e ideia descartada. N nunca diminui; a variância vem do nulo, não da grade.
- **Regime:** mesmo sinal em três subperíodos, com 2022-26 no OOS.
- **Concentração:** Sharpe sem os 5 melhores dias acima da metade; sem o melhor trimestre, acima de zero.
- **Clusters:** correlação acima de 0,5 é uma aposta no veredito, mas conta inteira no N.

## 4. Execução e tamanho

Execução é de Brown e Berlekamp; o meu: proibir execução em abertura sintética; comparar no paper trading o deslize real com o do backtest (KS, 100 trades); DSR com o N verdadeiro abaixo de 0,9, tamanho zero. A ruína vem do tamanho: Kelly fracionado sobre o Sharpe deflacionado, nunca o de vitrine.

## 5. Plano de 90 dias

1. **Gate de dados (semanas 1-3).** Hipótese: as promissoras sobrevivem à proibição de abertura sintética e à troca do preço Bitfinex pelo composto. Dado: Binance e Bitstamp 1 min. Sucesso: Sharpe muda menos de 0,1. Abandono: fonte com mais de 1% das barras a mais de 50 bps da outra sai.
2. **Estatística certa (semanas 2-4).** Nulo circular, DSR com o livro, concentração, clusters. Hipótese: alguma entrada tem p<0,01 e DSR>0,9 com N=298. Abandono: nenhuma passa, biblioteca v1 arquivada sem parâmetro novo.
3. **Painel de sinais 2020-2026 (semanas 4-10).** 30 features (taker-buy, OI, funding, calendário, on-chain defasado 2 dias), horizontes de 1 h a 7 d. Hipótese: uma com |IC|>0,03, mesmo sinal em três subperíodos e t>3,5 (Bonferroni no N real). Abandono: seis semanas sem isso, BTC isolado não é o lugar.
4. **WIN (semanas 1-12, em paralelo).** Gravar hoje tick e nível 1 com carimbo da bolsa e local; histórico de duas fontes (rolagem bimestral, horário do pregão, leilões). Hipótese: as fontes concordam em 99% das barras de 1 min, em 1 tick. Abandono: sem segunda fonte, só o dado próprio conta.

## 6. O que eu não faria

Operar as três promissoras, nem pequeno. Mais grade em Bitfinex 2017-2019. Tocar em 2013-2016. Usar fluxo de exchange como se conhecido na época. Chamar tsmom+Donchian de carteira. Sub-horário a mercado. Confiar em p<0,15.

## 7. Pergunta para Mercer

Com um ativo, nove anos e três regimes, o painel de IC tem talvez 35 observações independentes a 30 dias. Quantas features você testa antes que a combinação vire ajuste, e aceita que o N do DSR dela seja o livro inteiro, com os 146 testes on-chain?

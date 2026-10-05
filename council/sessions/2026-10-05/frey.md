# Parecer de Robert Frey — sessão de 2026-10-05

No APT e na Kepler tínhamos milhares de ações, aluguel barato e crédito; o Marcelo tem dezenas de perpétuos líquidos, oitenta ações sem aluguel e capital de uma pessoa. Transfere-se o quadro: neutralizar, operar o resíduo, dimensionar por risco, muitas posições ao mesmo tempo. A escala, não.

## 1. Diagnóstico do que existe

O método é honesto; o objeto está errado. Um ativo direcional é o pior caso da arbitragem estatística: não há carteira, há aposta. As três "promissoras" têm todo o retorno OOS na mesma janela, abril a junho de 2019; sem ela, tsmom 1d dá -7%, Donchian 1h -4%, SMA 1h -25%. Quarenta trades em 21 meses num único preço são cinco apostas de regime. O duelo tsmom x SMA (correlação 0,13) não diversifica erro: mede o mesmo rali duas vezes. A reversão perdeu porque foi aplicada ao nível do próprio BTC em tendência; ela funciona no resíduo, tirado o fator comum, e aqui nunca teve chance.

## 2. Onde procurar edge (e quais dados primeiro)

**Perpétuos de altcoins neutros a BTC.** Os 30-50 perpétuos USDT-M mais líquidos, escolhidos com atraso e incluindo deslistados; beta rolante de 60-90 dias; resíduo r_i − β_i·r_BTC. Sinais: reversão cross-sectional do resíduo em 1-3 dias e momentum de 2-8 semanas, dólar-neutro e beta-neutro. Dados: klines 1h de todos os símbolos, funding e open interest, da Binance.

**Base perpétuo-spot e funding como carry.** Comprado spot, vendido perpétuo: 0,01%/8h é ~11% ao ano de piso. É o carry mais limpo do varejo, e não é alfa: é prêmio por risco de liquidação da perna vendida, funding negativo e contraparte. Capacidade: sobra para ele. Dados: funding desde 2019, spot e perp alinhados, margem.

**Brasil: ações contra WIN.** O futuro do índice é o hedge que dispensa aluguel: cesta comprada de 10-20 ações escolhidas pelo resíduo, vendida em WIN. Um tick de R$1 em R$26 mil são ~4 bps ida e volta, contra 14 no BTC: reversão que morre a 14 pode viver a 4. WIN contra WDO não é par, é aposta em duas macros; o útil é regredir WIN intradiário em WDO e S&P e operar o resíduo, modelando base e rolagem.

**Pares entre exchanges.** Com latência de segundos, a arbitragem já foi; a base lenta é sinal, não trade.

## 3. Método

O motor muda: alvo vira matriz T×N de pesos com máscara de universo; custo por perna e ativo; hedge em BTC de −Σβ_i·w_i com beta estimado só no passado; funding a cada 8h (custo do comprado, receita do vendido); liquidação checada intrabarra. Seleção por IC (correlação de postos entre sinal e resíduo futuro, por dia) e seu t, não por Sharpe de uma série. Nulo novo: embaralhar o sinal entre ativos a cada dia. Relatar beta ex-post, concentração e atribuição por nome: um ativo carregando a carteira foi a doença de 2019. IR ≈ IC×√amplitude: 40 nomes por 250 dias são 10 mil apostas (nunca independentes); IC de 0,02 dá IR 2 antes de custos. Sinais fracos combinam por média de z-scores, não por portões.

## 4. Execução e tamanho

Cada perna paga. Com permanência de 1-3 dias o giro custa 10-15% ao ano a 14 bps; só limitadas post-only com horas de paciência (`limit_fill_fraction` já existe) cortam isso pela metade. Hedge o beta líquido do livro, não posição a posição. US$9 mil em 40 posições de US$200 cabem nos mínimos da Binance. Risco por construção, não stop: 5% por nome, bruto até 2x, margem abaixo de 30%, um terço do capital por exchange. Carry: pernas casadas, maker. Um WIN é R$26 mil: hedge grosso para cesta abaixo de R$50 mil.

## 5. Plano de 90 dias

1. **Motor de carteira (3 semanas).** Hipótese: reproduz exatamente o torneio com um ativo e passa no lookahead com N. Dado: Bitfinex atual. Sucesso: igualdade numérica, testes verdes. Abandono: nenhum; pré-requisito com teto.
2. **Resíduo de alts contra BTC.** Hipótese: reverte em 1-3 dias com IC > 0,02 e t > 3 OOS, Sharpe líquido > 1, beta ex-post em ±0,1, mesmo sem os 10 nomes menos líquidos. Dado: Binance USDT-M 2020-2026, todos os símbolos. Abandono: IC < 0,01 ou Sharpe < 0,5 após dois horizontes; grade não cresce.
3. **Carry de funding com regra.** Hipótese: entrar com média de 7 dias acima do percentil 60 e sair abaixo do 30 rende > 8% ao ano líquido de 30 bps nas duas pernas, drawdown < 5%, zero liquidações a 2x. Dado: funding, spot, perp, margem. Abandono: < 5% ao ano, ou funding negativo por duas semanas que a regra não evita.
4. **Dados da B3 desde já.** Hipótese: resíduos dos componentes do Ibovespa revertem em 2-5 dias com IC > 0,02 em cesta só comprada com hedge em WIN. Dado: diário dos componentes com composição histórica, WIN rolado, CDI, ex-dividendos. Sucesso e abandono como em 2; começa pela coleta, que demora.

## 6. O que eu não faria

Torneio direcional abaixo de 1 hora. Arbitragem entre exchanges por latência. Aluguel de ação nesse tamanho. Mais de 2x bruto em perpétuo. Grade maior. Stop como gestão de risco. Chamar o tsmom de promissor: é aposta num rali.

## 7. Uma pergunta para outro membro do conselho

**Berlekamp:** amplitude substitui frequência? Quarenta nomes rebalanceados por dia são dez mil apostas por ano. Isso satisfaz o seu "muitas apostas pequenas", ou 14 bps por perna ainda matam e só o WIN a 4 bps paga a frequência que você exige?

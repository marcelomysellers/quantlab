# Parecer de Peter Brown (engenharia) — sessão de 2026-10-05

Eu tinha dezenas de engenheiros e operação 24 horas; isso não se transfere. O que se transfere: o sistema inteiro é o produto, e nenhum número existe até ser reproduzido por um caminho independente. A suíte passa; passar nos testes não é estar certo.

## 1. Diagnóstico do que existe

O motor é honesto no tempo (sinal em t, execução em t+1, custo com range de t-1; verifiquei). O resto:

- **O nulo não tem "a mesma exposição".** `backtest/montecarlo.py:22-27` sobrescreve trades sorteados sobrepostos. Donchian 1h: exposição 0,74 e 279 trades; o nulo, 0,52 e 196. O p-valor compara contra quem opera 30% menos.
- **Lookahead no walk-forward.** `strategies/library.py:162-165`: com `fit_slice=(a,b)`, `fwd` usa `open[b]` e `open[b+1]`, barras do teste; perturbá-las muda 750 posições. `tests/test_engine.py:85-87` não cobre fit encostado no corte.
- **Benchmark aleatório errado.** `library.py:39-46` reinicia o hold a cada sorteio: exposição 0,64 (alvo 0,50) e 2.682 viradas diretas em 3.020 entradas, pagando dois lados.
- **Custo por trade subestimado.** `backtest/engine.py:98-110` ignora o giro dentro do trade; no tsmom com vol target some 12% do custo.
- **Barras sintéticas negociáveis.** `data/store.py:32-43` cria barras de outage com range zero e o motor nunca lê `synthetic`: opera-se no preço congelado com menos deslize (7,0 contra 8,2 bps).
- **Custo de carregar = zero.** `execution.py` não tem funding nem juros de margem. Funding de 0,01% por 8 h é ~11% ao ano; o tsmom diário está sempre posicionado.
- **Dias sem pregão viram retorno zero.** `engine.py:122-126` e `metrics.py:102-108`: no WIN, `resample("1D")` inventa 200 dias em 504; PSR, t-stat e curtose usam `n_days` inflado.
- **O torneio é o teste múltiplo.** `tournament.py:57-71` julga cada entrada sozinha e o DSR conta só a grade própria. Com 34 entradas, a chance de algum p < 0,05 sem edge é 83%; o menor observado foi 0,083: o torneio é compatível com edge zero. tsmom 1d: 3 folds positivos em 7, parâmetro troca quase todo fold, 2019-04 (+152%) carrega tudo, IC90 [-0,19; 2,21].

Faltam testes de: lag do custo; fronteira treino/teste com `needs_fit`; exposição do nulo; soma dos `ret_net` contra o `net`; agregação com sessão.

## 2. Onde procurar edge (e quais dados primeiro)

No custo antes do sinal: BTC a 14 bps ida e volta mata tudo abaixo de 1 h; WIN a ~1,3 bps (R$ 0,50 mais um tick em R$ 27,5 mil) é dez vezes mais barato: o intradiário ressuscita. Dados, nesta ordem: funding e open interest da Binance; WIN 1 minuto gravado desde hoje, com timestamp da corretora e local; as barras que o bot vê ao vivo, as únicas que reconciliam.

## 3. Método

Um torneio é uma tentativa: registre cada rodada num log de pesquisa e deflacione pelo total acumulado, não pela grade da estratégia. Rejeite resultado que dependa de um fold. Antes de combinar sinais, combine caminhos: todo número do leaderboard precisa de um segundo cálculo independente.

## 4. Execução e tamanho

No seu tamanho impacto é zero; o custo é taxa e seleção adversa. Maker economiza 6 dos 14 bps, mas a taxa de fill só o paper trading mede; `limit_fill_fraction` (`execution.py:75-93`) não é chamado nunca. No diário 24/7, `open[t+1]` é o `close[t]` segundos depois: o backtest executa quase no preço do sinal, e 00:00 UTC coincide com o funding. No WIN, um contrato é metade do capital: `instruments.py` precisa de contratos inteiros, leilão de abertura e rolagem; vol target não existe.

## 5. Plano de 90 dias

1. **Semanas 1-2: fechar os buracos, congelar com testes.** Hipótese: as duas promissoras sobrevivem às correções. Dado: o existente. Sucesso: Sharpe e p mudam menos de 0,1. Abandono: mudaram mais de 0,3; o torneio anterior era o bug.
2. **Semanas 2-8: paper trading com reconciliação diária.** tsmom 1d e Donchian 1h na Binance, US$ 100 de notional. Logar da barra ao fill; todo dia, replay das barras vivas pelo `run_backtest` e diff. Hipótese: alvo idêntico em 100% das barras, custo ≤ 7 bps por lado. Sucesso: 30 dias sem diferença inexplicada. Abandono: custo acima de 14,5 bps após 20 trades mata a versão 1h.
3. **Semanas 4-10: falhas, monitor, limites.** Caos: processo morto com ordem em voo, 500/429/timeout, relógio 2 s atrasado, posição órfã, websocket mudo. Monitor em processo e chave separados, com heartbeat; sem heartbeat, zera. Limites: perda diária 2%, 3 ordens por minuto, notional 1× capital, kill switch por arquivo. Hipótese: toda falha termina em estado conhecido com alerta em 5 minutos. Sucesso: 10 cenários, duas passagens limpas. Abandono: nenhum; sem isso não há capital real.
4. **Semanas 6-12: funding como custo e sinal, torneio 2020-2026.** Hipótese: tsmom 1d mantém Sharpe > 0,5 com carry e p < 0,05 contra o nulo corrigido, deflacionado pelo torneio inteiro. Abandono: Sharpe < 0,3 ou p > 0,15; vá para o WIN.
5. **Desde a semana 1: coletor WIN.** Sucesso: 90 dias limpos no `quality_report`.

## 6. O que eu não faria

Operar abaixo de 1 h em BTC como taker. Sinal novo antes de a reconciliação existir. Monitor e bot no mesmo processo ou chave. Aumentar tamanho antes de 60 dias reconciliados. Acreditar em número que só exista num caminho de código.

## 7. Pergunta para Sandor Straus

Para reconciliar preciso de duas fontes independentes da mesma barra: o que você gravaria do websocket, com quais timestamps, para que um dia depois eu prove que a barra que o bot usou é a mesma que o histórico oficial devolve, e o que fazer quando não é?

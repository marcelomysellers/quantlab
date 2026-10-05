# Parecer de Elwyn Berlekamp — 2026-10-05

Não se transfere: custo institucional (fração de ponto-base por σ de aposta), capital que faz do tamanho uma variável contínua, dados e equipe. Transfere-se uma conta. Com N apostas por ano, acerto IC (edge por aposta em unidades de σ) e custo c por ida e volta:

**Sharpe ≈ IC·√N−(c/σ_anual)·N.** Edge cresce com √N; custo, com N.

## 1. Diagnóstico do que existe

Motor honesto; torneio ainda não é evidência.

- **Amostra.** 1,75 ano OOS: erro-padrão do Sharpe ≈0,76; IC90 do tsmom diário [−0,19; 2,21]. "Sharpe>0,5" mora dentro do ruído, e o melhor de 15 entradas sem edge chegaria a ≈1,3 por sorte; o observado é 1,1.
- **Concentração.** tsmom 1d sem o fold abril-junho/2019 (+152%): −7%; mediana dos folds −0,34; 4/7 negativos. Donchian 1h sem o mesmo fold: −4%. Estratégias de um trimestre.
- **Custo ausente.** Funding do perpétuo (0,01%/8h ≈11% a.a. sempre comprado) é 3× o custo modelado do tsmom diário (3,2% a.a.).
- **Otimista sem fila.** Taxa maker cobrada de ordens a mercado; `limit_fill_fraction` sem uso; `duels()` soma retornos líquidos e paga custo duas vezes: some alvos antes do backtest.

## 2. Onde procurar edge (e quais dados primeiro)

σ por horizonte, custo em σ e apostas/ano girando sem parar. BTC 50% a.a., taker 14 bps, maker 5; WIN 22% a.a., 565 min/sessão, R$0,50 de bolsa + 1 tick de spread =R$1,50 em R$28 mil ≈0,6 bps:

|horizonte|BTC: σ, c/σ taker (maker), N/ano|WIN: σ, c/σ, N/ano|
|---|---|---|
|1 min|7 bps, 2,0 (0,72), 525.600|6 bps, 0,10, 142.380|
|5 min|15, 0,91 (0,32), 105.120|13, 0,046, 28.476|
|15 min|27, 0,52 (0,19), 35.040|23, 0,027, 9.492|
|1 h|53, 0,26 (0,09), 8.760|45, 0,013, 2.373|
|1 dia|262, 0,053 (0,019), 365|139, 0,004, 252|

c/σ é o IC de empate. Sinal "52%": IC 0,03; o nosso 50,75%: 0,012. A 1 hora, IC 0,03 vale 1,6 bps brutos em BTC contra 14 de custo (acertar 2 em 3 só empata); no WIN, 1,4 contra 0,6, e 50,8% já empata (meu número, no seu custo). Girando o ano inteiro: Sharpe −22 em BTC 1h a mercado, +0,8 no WIN 1h. WIN a 15 min custa o que BTC custa a 4 dias.

Dado primeiro: WIN 1 minuto com volume e número de negócios, série contínua com rolagem, mais WDO e proxy do S&P no mesmo relógio. BTC é dado conveniente de um mercado onde você não é o cassino.

## 3. Método

- Evidência é t=Sharpe·√anos. Anos para t=2: Sharpe 0,5→16; 1→4; 2→1; 3→5 meses. Horizonte curto não é para ganhar mais; é para saber se há edge antes de morrer. 23 trades/ano em BTC diário é aposentadoria, não pesquisa.
- Publicar t, anos-para-t=2, Sharpe sem o melhor fold e mediana dos folds; n_trials do DSR: tudo que o torneio tentou (≈300).
- Média da grade, não melhor da grade: seleção por Sharpe de 12 meses (erro-padrão ≈1) é ruído.
- Combinar somando alvos, não retornos: K sinais descorrelacionados dão IC·√K, único almoço grátis, com correlação medida fora da amostra.

## 4. Execução e tamanho

- Maker em BTC economiza 10 bps e perde os trades que um rompimento quer. Teste: remova os trades cuja primeira barra andou a favor mais de 1 tick (não executariam no limite); se o Sharpe some, a coluna otimista é ficção.
- f=Sharpe encolhido/σ; opere ¼ disso até t>2. tsmom diário: Sharpe encolhido ≈0,5, σ 53% → f≈0,95; ¼=24% do capital. Crescimento-teto com Sharpe 0,5: 12,5% a.a. em Kelly cheio, 9% em meio-Kelly.
- WIN: 1 contrato (R$28 mil) sobre R$50 mil já é 0,56×; ¼-Kelly de um Sharpe 1 a 22% =1,1× =2 contratos. Seu problema de tamanho é o degrau, não o impacto. Stops são giro, logo custo. Kill-switch: custo realizado de 50 trades acima de 2× o modelo.

## 5. Plano de 90 dias

1. **OOS comprado (semanas 1-3).** H: tsmom 1d (L=96, vol 0,5) e Donchian 1h (n=100-150), congelados, com funding, dão Sharpe>0,5 em 2020-2026. Dado: Binance. Sucesso: t>2. Abandono: Sharpe<0,3 ou um fold com >70% do lucro.
2. **Custo do WIN (semanas 2-6).** H: c/σ medido a 15 min <0,03. Dado: ticks MT5 com bid/ask, 1 min com rolagem. Sucesso: tabela acima medida, ≥1 ano limpo. Abandono: <6 meses de histórico → gravar desde hoje.
3. **Primeira aposta (semanas 4-10).** H: retorno de 1 min do WIN previsível com lag 1-2 min, t>3 em um ano, líquido de 0,6 bps. Dado: WIN, WDO e proxy do S&P em 1 min. Sucesso: t>3 e últimos 3 meses positivos congelados. Abandono: t<2, ou o edge some com lag 2 (latência: não é o seu jogo).
4. **Custo realizado (semanas 6-12).** H: 1 contrato a mercado, latência de segundos, custa <1 bp (R$3). Dado: log das execuções. Sucesso: 200 giros. Abandono: >2 bps → horizonte de 1 h.

## 6. O que eu não faria

BTC a mercado abaixo de 4 horas. Operar sobre 40 trades. Parâmetro por Sharpe de 12 meses. Book nível 2 com latência de segundos. Aumentar tamanho após um trimestre bom: abril-junho/2019 é a armadilha com nome. Intervir à mão: a primeira coisa que acabei na Axcom.

## 7. Pergunta para outro membro

**Mercer:** no WIN a 5 minutos o IC de empate é 0,046. Sinais de IC 0,02 com correlação 0,3 têm teto 0,02/√0,3 =0,037: nunca chegam; só com correlação <0,19. Que correlação os seus sinais tinham, e como a media fora da amostra com t<2 em cada um?

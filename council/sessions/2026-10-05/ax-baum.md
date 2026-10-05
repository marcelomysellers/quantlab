# Parecer: James Ax e Leonard Baum (a primeira era)

**Baum:** O que não se transfere: nos anos 80, bancos centrais e hedgers alisavam preços e fabricavam tendências de semanas, quase ninguém operava sistemático, e Jim tinha capital para atravessar 1988. O que se transfere é o aviso: eu quebrei intervindo contra o modelo; Ax quebrou recusando aposentá-lo.

## 1. Diagnóstico do que existe

**Ax:** O motor é honesto; a amostra não é.

- Os 21 meses de OOS têm um bear e uma recuperação. No tsmom diário, 3 trades (short de nov/18, long de abr-set/19) somam 130% do lucro; sem eles, a soma dos trades é −30%. No Donchian 1h, 3 trades somam 94%. Não é regularidade; são dois episódios.
- Folds do tsmom: 3 de 7 positivos; o lookback pulou 12→48→12→96; no fold 6 o melhor do treino deu −0,8 fora e o segundo, +1,7. Seleção por Sharpe de treino é ruído escolhendo ruído.
- O DSR conta 10 tentativas, mas o leaderboard escolheu entre ~300 configurações; com só 20 independentes em 21 meses, o melhor de puro ruído dá Sharpe ≈ 1,4, acima do 1,1. "Promissora" é armadilha: convida a operar evidência compatível com sorte.

## 2. Onde procurar edge (e quais dados primeiro)

**Baum:** Nossa tendência tinha pagador identificável: quem alisava o preço. Procure regularidade com pagador estrutural. Em BTC: fluxo forçado (liquidações; funding extremo é a multidão pagando para ficar posicionada). Dado primeiro: Binance 1m com taker-buy, funding e open interest. No WIN a razão é custo: ~4 bps ida e volta (um tick de R$ 1 em ~R$ 26 mil) contra 14 no BTC. Dado primeiro: 1 minuto com contrato contínuo e rolagem correta, 5 anos ou mais; rolagem errada foi o nosso bug.

**Ax:** E preveja o decaimento: BTC em 2018 era varejo sem sistemáticos; em 2026 há ETF, base e arbitragem de funding. Teste 2020-26 antes de acreditar.

## 3. Método

- Conte as tentativas no nível do torneio; a grade escrita antes é a única grade. Não selecione, some: média dos sinais de todos os lookbacks.
- Teste por eras e exija o mesmo sinal nas três; queda monotônica com a última ≤ 0 é decaimento. Combine fracos só depois de cada um passar sozinho: o duelo tsmom+Donchian (corr 0,41) é os mesmos dois episódios contados duas vezes.
- t = Sharpe·√anos: Sharpe 0,5 precisa de 16 anos para t = 2; 1,1 precisa de 3,3. Nenhuma regra estatística aposenta estratégia diária em tempo humano; a que age é a de drawdown, e ela errará.

## 4. Execução e tamanho

**Ax:** Funding de 0,01%/8h ≈ 11% ao ano, ~8% de arrasto na posição média de 0,71; tendência paga funding por construção: está com a multidão. Shorts foram 40-45% do lucro; sem perpétuo não há short. Limitada poupa 9 dos 14 bps, mas rompimento é onde ela falha. Tamanho: BTC em vol-alvo 20%, não 50%: ~R$ 16-20 mil de spot em R$ 40 mil. WIN: 1 contrato ≈ 12% de vol nesse capital; o tamanho é 0, 1 ou 2. Vol-alvo, que venceu em todos os folds, não existe lá: reteste binário.

## 5. Plano de 90 dias

1. **Decaimento** (semanas 1-4). Hipótese: tsmom 1d e Donchian 1h, mesma grade, dão Sharpe > 0,5 e p < 0,05 em 2020-26. Dado: Bitstamp 1m 2012-26 e Binance 2020-26. Sucesso: 100+ trades, p < 0,05, DSR de torneio > 0,9, três eras positivas. Abandono: Sharpe < 0,3 ou p > 0,10 aposenta a família, não o lookback.
2. **Livro de regras e `risk.py`** (semanas 3-6), antes da primeira ordem. Operar: aprovada, eras, 90 dias de sombra com custo ≤ 25 bps e fills ≥ 95%, em vol-alvo 10%. Metade: DD ≥ 1,0× o DD pessimista do backtest, ou Sharpe móvel de 12 meses < 0. Zerar: DD ≥ 1,5×, ou 350 dias abaixo d'água (1,5× o backtest). Aposentar: p contra o nulo recalculado mensalmente em OOS+vivo > 0,20 por 2 meses, ou DSR < 0,5, ou Sharpe vivo < 0 após 40 trades. Janela mínima de 12 meses: nov/18 veio três meses depois do pior semestre. Hipótese: a regra aposenta ≥ 90% das 300 aleatórias em 12 meses e mantém a real em ≥ 80% dos bootstraps da própria curva. Dado: as curvas do nulo. Abandono: se nenhuma regra separa, não opera.
3. **Funding** (semanas 5-8). Hipótese: líquido de funding, mantém ≥ 70% do Sharpe bruto. Dado: histórico de funding e OI. Abandono: funding come > 40%; resta o spot só-compra, ou nada.
4. **WIN** (semanas 6-12). Hipótese: a 4 bps, o rompimento 1h que morreu no custo sobrevive com 100+ trades e Sharpe > 0,5. Dado: 1m contínuo, 5+ anos. Sucesso: aprovada e 2 eras positivas. Abandono: nada aprovado muda horizonte, não afina parâmetro.

## 6. O que eu não faria

**Baum:** Não pularia um sinal por achar que "amanhã tem Fed": foi assim que saí. Único botão manual: zerar por causa operacional, com motivo logado; nunca por opinião. Parâmetro não muda ao vivo; muda pelo torneio.

**Ax:** Não diria "o drawdown está dentro do histórico" pela terceira vez. Não somaria duas promissoras para fabricar uma aprovada. Não operaria abaixo de 1 hora em BTC: até o aleatório perde 99%.

## 7. Pergunta para outro membro

**Ax, para Berlekamp:** com 23 trades por ano, a aposentadoria vira drawdown puro. Como multiplicar as apostas sem cair no poço de custo abaixo de 1 hora: o WIN a 4 bps é o único caminho, ou dá para fatiar a aposta diária sem girar mais?

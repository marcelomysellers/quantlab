# Parecer de Jim Simons (presidente), 2026-10-05

Não se transfere: capital, alavancagem barata, dezenas de mercados e de cientistas. Transfere-se: o sistema decide, custo antes de sinal, registrar tudo, progresso sem olhar o lucro, paciência de anos.

## 1. Diagnóstico do que existe

O motor é honesto; a evidência e o processo, não.

- **A "promissora" é um trimestre.** Momentum diário: Sharpe 1,10; sem abril-junho de 2019, 0,12 (+118% vira -9%). Donchian 1h: 0,83 para 0,29; cruzamento 1h: 0,51 para -0,16. Intervalo de 90%: [-0,19; 2,21].
- **Quatro entradas, uma aposta:** tendência no mesmo ativo, correlação de 0,41 a 0,73.
- **Parâmetros instáveis:** lookback vencedor 12, 48, 12, 96 por janela.
- **Tentativas subcontadas:** o DSR deflaciona por 10 configurações; o torneio rodou 298, sem contar ideias descartadas.
- **Potência:** 1,75 ano de um ativo detecta Sharpe de 1,2 a p < 0,05, não 0,5; o critério exige uns 10 anos ou vários instrumentos.
- **Dado parado em 2019, processo ausente:** sem registro de hipóteses, coletor, paper reconciliado, regra de começar, parar e aposentar.

## 2. Onde procurar edge (e quais dados primeiro)

Não há grandes ineficiências; há anomalias pequenas e breves, visíveis só com muito dado e custo baixo.

- **WIN, primeiro em dados.** Tick de R$ 1 sobre R$ 25-28 mil é 0,4 bps; bolsa, 0,2 bps ida e volta: vinte vezes mais barato que o BTC base (14 bps), e com relógio: pregão às 9h sem o à vista até 10h, abertura dos EUA (10h30/11h30), PTAX (10h-13h), fechamento 17h-18h25, semana de vencimento. Grave 1 minuto e book nível 1 desde hoje.
- **BTC, fora do preço.** Binance 2020-2026 (volume taker, número de trades, funding, open interest) e CoinMetrics diário, horizontes 1h-1d; abaixo, o custo come tudo. BTC, ETH e três majors agrupados: cinco vezes mais apostas.

## 3. Método

1. **Medir sinais, não estratégias:** IC por feature e horizonte (1h, 4h, 1d) em janelas trimestrais; sobrevive se o sinal repete em 70% delas.
2. **Registro de hipóteses** (hipótese, dado, horizonte, métrica, critério de morte, resultado); o n_trials do DSR passa a ser essa contagem, mortas incluídas.
3. **Cofre:** últimos 12 meses lacrados, abertos uma vez por trimestre.
4. **Concentração:** nenhuma janela com mais de 50% do lucro; 60% das janelas positivas.
5. **Combinar simples:** média de z-scores; sem otimizador em 600 dias.
6. **Rotina:** 4 horas fixas por semana: coletor, reconciliação, uma hipótese entra, uma morre, nota de uma página na sexta. Progresso: minutos faltantes, hipóteses mortas por mês, erro backtest × paper, horas de ideia a resultado.

## 4. Execução e tamanho

No nosso tamanho o custo é taxa e spread. Maker economiza 6 bps por ida e volta no BTC (2,4% ao ano com 40 trades), mas seu custo escondido é seleção adversa: medir em paper taxa de fill e retorno 1 minuto após. No WIN a abertura é leilão: custo próprio.

Primeiro ano no tamanho mínimo (1 contrato de WIN; 0,5% de risco por trade no BTC): compra reconciliação, não lucro. Perda diária máxima 2%, mensal 6%, kill switch fora do robô. Regra escrita antes da primeira ordem: começa com aprovação mais 60 dias de paper; para em drawdown além do pior do backtest; aposenta com Sharpe de 12 meses abaixo do intervalo. A mão entra nas regras, nunca no trade.

## 5. Plano de 90 dias

1. **Coletor e registro (semanas 1-2).** Hipótese: 99,5% dos minutos cobertos por 30 dias em BTC/ETH (klines, funding, OI, L1) e WIN (MT5 1m, L1). Dado: Binance local, MT5. Sucesso: 30 dias de relatório verde. Abandono: abaixo de 98%, trocar de fonte.
2. **Painel de IC (semanas 2-6).** Hipótese: duas features (funding, desequilíbrio taker, variação de OI, fluxo de exchanges) com |IC| ≥ 0,03 e mesmo sinal em 70% dos trimestres de 2020-2026, em 4h ou 1d, BTC e ETH agrupados. Dado: Binance, CoinMetrics. Sucesso: duas passam. Abandono: nenhuma; BTC vira só coleta.
3. **Torneio honesto (semanas 6-9).** Hipótese e sucesso: a combinação bate o momentum sozinho, Sharpe > 0,7 e p < 0,05 em 2020-2025, cofre 2025-2026 lacrado, n_trials do registro, teste de concentração. Dado: o do item 2. Abandono: momentum 1d abaixo de 0,3 e combinação sem ganho.
4. **Paper reconciliado (semanas 7-13).** Hipótese: custo realizado até 14 bps a mercado, 8 bps limitada com fill de 60%. Dado: fills reais no tamanho mínimo. Sucesso: deslize mediano no cenário base. Abandono: acima de 25 bps, o modelo de custo está errado; volta ao item 3.
5. **Relógio do WIN (do dia 60).** Hipótese e sucesso: uma janela de 15-30 minutos (abertura, PTAX, EUA, fechamento) com |t| > 3 em dois anos agrupados, líquido de 1 bps. Dado: Nelogica/MT5 mais o coletor. Abandono: nada com |t| > 2 em um ano.

## 6. O que eu não faria

- Operar qualquer coisa do torneio de 2018-2019.
- Adicionar estratégias antes de anos e instrumentos.
- Descer de 1h no BTC a mercado; latência, book nível 2, aprendizado de máquina ou otimizador em 600 pontos diários.
- Deixar a mão entrar: sem override, sem aumentar tamanho após um mês bom, sem manter o que decaiu. Assim perdemos Baum e Ax.
- Medir o primeiro ano em dinheiro.

## 7. Pergunta ao Berlekamp

No WIN (tick 0,4 bps, bolsa 0,2 bps, fill maker de 60%, um tick de seleção adversa): qual edge mínimo por trade e quantos trades por ano para t-stat 3 em 12 meses? Isso decide se o WIN é o segundo mercado ou o primeiro.

# Parecer de Robert Mercer (2026-10-05)

O que não se transfere: milhares de ações e centenas de milhares de apostas por ano. Você tem um ativo, 14 bps por giro e horas por semana. Meus "50,75%" são um IC de 0,024, que só paga com muitas apostas baratas. O que se transfere: medir sinais, não estratégias; combinar antes de operar; não exigir explicação; contar cada teste.

## 1. Diagnóstico do que existe

- **Compara estratégias, não sinais.** Limiar e máquina de estados jogam fora a magnitude; o IC nunca é medido.
- **Conta tentativas errado.** O DSR conta a grade de cada estratégia, não o máximo sobre 34 competidoras. Com 1,75 ano de OOS, o melhor Sharpe esperado sob o nulo é 1,3–1,6; o observado é 1,10. Tudo compatível com zero.
- **A amostra não aprova o que o critério pede.** Detectar Sharpe 0,5 exige 25 anos. O tsmom diário: 40 trades, um fold carrega tudo, IC90 [-0,19; 2,21]. Não falta sinal; faltam apostas.
- **Walk-forward seleciona em vez de combinar**: o melhor parâmetro de 12 meses é um máximo sobre ruído; a média da grade teria menos variância.
- **Sem banda de não-negociação** (tsmom em 1 minuto paga 50 patrimônios) e **só preço**.

## 2. Onde procurar edge (e quais dados primeiro)

Um sinal paga quando 0,8 × IC × σ_h supera o custo do giro. IC de equilíbrio em BTC taker (14 bps): 1 min 1,6; 1 h 0,21; 4 h 0,10; 1 dia 0,043. Maker (5 bps): 4 h 0,037; 1 dia 0,015. WIN (~0,9 bps): 15 min 0,06; 1 h 0,03. Sharpe bruto ≈ IC × √(apostas/ano): IC 0,024 dá 0,46 em BTC diário, 2,0 em 20 perpétuos, 1,2 no WIN 1 h. Breadth ou frequência barata; não há terceira saída.

Dados, nesta ordem: Binance UM 1 min (taker-buy, nº de trades), funding, open interest; CoinMetrics diário; 20 perpétuos; WIN 1 min, USD/BRL, S&P.

**Biblioteca de features** (z-score rolante de 30 dias):

| Grupo | Features |
|---|---|
| Preço | retorno em k ∈ {1,4,24,72,168}; retorno/vol; posição no range; gap; múltiplos de 1.000 |
| Fluxo | taker_buy/volume em k ∈ {1,4,24} e z contra 7 d; z(volume); z(nº trades); volume/trades; Amihud |
| Derivativos | funding atual e acumulado 3 d; ΔOI; ΔOI × sinal do retorno; base perpétuo–spot |
| On-chain | fluxo líquido para exchanges; Δoferta em exchanges; MVRV; Δendereços ativos; Δhashrate; z(transações) |
| Calendário e cruzado | hora UTC; dia da semana; horas até o funding; vencimento Deribit/CME; FOMC/CPI; ETH/BTC. WIN: gap, range dos 15 min iniciais, USD/BRL, S&P overnight, Copom |

## 3. Método

**Painel de IC.** Por feature e horizonte h ∈ {1,4,12,24,72} barras, Spearman entre f_t e o retorno open(t+1)→open(t+1+h). Por janela mensal: IC médio, desvio, IC-IR, t de Newey-West, % de meses positivos, IC nos decis extremos e por tercil de vol. Heatmap feature × horizonte pelo t (cinza se |t|<2) e série mensal de cada IC: sinal de um trimestre não é sinal.

**Combinação com controle de teste múltiplo.** (1) Lista de features no git antes de olhar; treino 2020–2023, confirmação 2024–2025, holdout 2026 tocado uma vez. (2) Benjamini-Hochberg a 10% sobre os 200 t; passa quem repete o sinal na confirmação. (3) Agrupar features correlacionadas: cinco momentos são um sinal. (4) Previsão = Σ IC_i × z_i, IC encolhido para zero; IC combinado ≈ √(ΣIC_i²). (5) Posição = clip(previsão/σ_h) × vol-alvo; só muda se 0,8 × IC × σ_h × |Δ| > custo. (6) DSR com n_trials = painel inteiro. Não descarte o que não faz sentido; descarte o que não repete.

## 4. Execução e tamanho

No seu tamanho não há impacto, só taxa. Maker contra taker é IC 0,015 contra 0,043 no diário: ordem limitada no lado da previsão, com o `limit_fill_fraction` existente. Tamanho proporcional à previsão, vol-alvo de 20–30% ao ano, nunca Kelly cheio. No WIN um contrato é R$ 27 mil: a posição vira {-1, 0, +1}; quantizar no motor e medir a perda.

## 5. Plano de 90 dias

1. **Semanas 1–3, painel de IC em BTC.** Hipótese: ≥ 5 de ~40 features com |t| > 3 em 4h–1d e mesmo sinal em 2024–2025. Dado: Binance 1 min, funding, OI, CoinMetrics. Métrica: aprovadas no BH-FDR e confirmadas. Abandono: < 3 → itens 3 e 4.
2. **Semanas 3–6, torneio de previsões.** O motor recebe previsão contínua. Hipótese: IC combinado OOS ≥ 0,05 e Sharpe líquido ≥ 1 com ≥ 150 mudanças de posição. Métrica: Sharpe OOS com bootstrap em blocos, DSR pelo painel. Abandono: IC < 0,02 ou Sharpe < 0,5. Depois, 8 semanas de paper trading; abandono se o custo realizado > 2× o modelado.
3. **Semanas 5–9, breadth.** Dado: klines dos 20 perpétuos; um modelo, z-score por ativo. Hipótese e métrica: t do IC agrupado ≥ 2× o do BTC. Abandono: não melhorar.
4. **Semanas 8–12, WIN.** Coletor MT5 de 1 min, painel em 15 min–1 h. Hipótese: ≥ 3 features com t > 3 a 1 bp de custo. Abandono: < 2 anos de histórico → coletar, não operar.

## 6. O que eu não faria

BTC abaixo de 1 h pagando taker: o aleatório perde 99%. Adicionar estratégias ao torneio. Escolher o melhor parâmetro por fold. Manter um sinal por ter história ou descartá-lo por não ter. Redes neurais com 100 features e 600 dias.

## 7. Pergunta para Henry Laufer

Os 20 perpétuos têm correlação de 0,8 com o BTC: a breadth efetiva talvez seja 3, não 20. O pooling vale a √3, e o que o agrupamento por calendário compra além disso?

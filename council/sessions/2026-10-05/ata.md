# Ata da primeira sessão do conselho — 2026-10-05

Presidência: Simons. Presentes: Berlekamp, Laufer, Mercer, Brown, Patterson, Straus, Frey, Ax e Baum. Pareceres individuais nesta pasta. Esta ata consolida consenso, divergências, o que já foi corrigido no laboratório durante a sessão e o plano de 90 dias.

## 1. Consenso

**O motor é honesto; a evidência não era.** Os nove chegaram ao mesmo diagnóstico por caminhos diferentes:

- As três "promissoras" de 2018-2019 devem todo o lucro à mesma janela, abril a junho de 2019. Sem ela, momentum diário vai de Sharpe 1,10 para 0,12, Donchian 1 hora de 0,83 para 0,29, cruzamento 1 hora para negativo. Três trades somam mais do que o lucro total. É uma aposta medida três vezes (correlação 0,41 a 0,73), não três estratégias.
- O Sharpe deflacionado contava 10 tentativas; o torneio fez 298. Com a variância do próprio nulo, o melhor Sharpe que o acaso produz em 298 tentativas é cerca de 2,5, acima do 1,1 observado. O ranking inteiro era compatível com edge zero.
- A amostra não comporta o critério: detectar Sharpe 0,5 em um único ativo exige da ordem de 16 anos. Com 1,75 ano, o critério de aprovação só enxergaria Sharpe acima de 1,2.
- **Confirmado fora da amostra durante a sessão**: com dados da Bitstamp de 2020 a 2026, momentum diário e Donchian 1 hora deram Sharpe 0,03 e CAGR de −11%. A previsão de Ax e Baum ("teste 2020-26 antes de acreditar") se cumpriu em duas horas.
- Nada foi aprovado, e isso é o resultado certo. Operar qualquer coisa do torneio de 2018-2019, mesmo pequeno, é a única unanimidade negativa.

**Custo decide o jogo.** Berlekamp colocou a conta: Sharpe cresce com a raiz do número de apostas, custo cresce linearmente com elas. Em BTC a mercado, 14 bps de ida e volta são 0,26 desvios-padrão de uma barra de 1 hora: é preciso acertar 2 em 3 só para empatar. No WIN, com bolsa de R$ 0,50 e tick de R$ 1 em um contrato de R$ 28 mil, a mesma hora custa 0,013 desvios: 50,8% de acerto já empata. O WIN a 15 minutos custa o que o BTC custa a 4 dias. Ninguém discordou: **abaixo de 1 hora em BTC a mercado não há o que pesquisar**, e o modelo de muitas apostas pequenas só existe para este operador no WIN, em perpétuos com ordem limitada, ou em carteiras largas.

**Dado próprio, desde hoje.** Straus, Patterson, Simons e Brown pediram a mesma coisa: um coletor rodando 24 horas para BTC (klines com volume taker e número de negócios, funding, open interest, book nível 1) e para o WIN (MetaTrader 5 em 1 minuto, ticks com bid e ask, DOM), com carimbo da exchange e local, bruto guardado, manifesto com hash. Kline de terceiro serve para pesquisar; só o dado próprio serve para operar. O que não foi gravado não existe.

**Medir sinais, não estratégias.** Mercer, com o apoio de Laufer e Patterson: o torneio compara estratégias inteiras (feature + limiar + máquina de estados) e joga fora a magnitude. O próximo passo é um painel de correlação de postos (IC) por feature, horizonte e janela mensal, com a lista de features registrada antes de olhar, controle de falsos positivos (Benjamini-Hochberg a 10%), confirmação em 2024-2025 e um cofre de 2026 aberto uma vez. Sinais fracos se combinam por média de z-scores encolhidos; não se escolhe o melhor parâmetro de uma grade, soma-se a grade.

**Regras escritas antes da primeira ordem.** Ax e Baum, Brown e Simons: quando operar (aprovada, três eras, 60 a 90 dias de sombra com custo realizado dentro do modelo), quando reduzir (drawdown igual ao pessimista do backtest ou Sharpe móvel de 12 meses negativo), quando zerar (1,5 vezes o drawdown ou 350 dias abaixo d'água), quando aposentar (p contra o nulo acima de 0,20 por dois meses, DSR abaixo de 0,5, Sharpe vivo negativo após 40 trades). Kill switch fora do robô, perda diária de 2%, limite de ordens por minuto, monitor em processo separado. A mão entra nas regras, nunca no trade. Tamanho mínimo no primeiro ano; progresso medido em cobertura de dados, hipóteses mortas, erro entre backtest e paper, nunca em lucro.

## 2. Divergências

- **WIN primeiro ou BTC primeiro.** Berlekamp, Simons e Laufer: o WIN é o único mercado onde a aritmética do custo fecha para este tamanho, e tem relógio institucional (abertura às 9h sem o à vista, abertura dos EUA às 10h30 ou 11h30 conforme o horário de verão americano, janelas da PTAX, leilão de fechamento, vencimento). Frey e Mercer: a largura (dezenas de perpétuos neutros a BTC) e o carry de funding são os únicos lugares em cripto onde o varejo é o cassino. Patterson e Straus: tanto faz, dado primeiro. **Decisão**: BTC continua como bancada de pesquisa porque o dado já existe (Binance 2017-2026 com 0,3% de minutos faltantes); o WIN começa hoje pela coleta, porque sem dois anos de 1 minuto não há o que testar.
- **Selecionar ou somar.** Mercer e Berlekamp: a seleção do melhor parâmetro em 12 meses de treino é um máximo sobre ruído. Implementado nesta sessão como modo alternativo do walk-forward (média de toda a grade); Ax e Baum pediram para o teste ser por eras.
- **Largura efetiva.** Frey conta 40 nomes por 250 dias como 10 mil apostas; Mercer e Laufer lembram que perpétuos têm correlação 0,8 com o BTC, e a largura efetiva é 3, não 20. Laufer: quem multiplica de verdade são anos e eventos de relógio, não ativos.
- **Maker ou taker.** Mercer: a ordem limitada reduz o IC exigido de 0,043 para 0,015 no diário. Berlekamp: a limitada perde justamente os trades que um rompimento quer, e a coluna "otimista" do torneio cobra taxa maker em ordens que são a mercado. **Decisão**: medir taxa de fill e seleção adversa em paper trading antes de acreditar em qualquer coluna otimista.

## 3. O que foi corrigido no laboratório durante a sessão

Os pareceres apontaram defeitos concretos. Corrigidos e cobertos por teste:

- Nulo por deslocamento circular das posições, que preserva exposição e durações (o nulo anterior sobrepunha trades e perdia 40% da exposição).
- Proibição de executar em abertura sintética (minuto sem negócio ou exchange fora do ar).
- Lookahead de duas barras no ajuste da sazonalidade por hora.
- Referência aleatória com trades sem sobreposição e sem virada direta.
- Custo por trade incluindo o giro dentro do trade (mudanças de tamanho do vol target).
- Dias sem pregão deixam de contar como retorno zero; anualização diária pelo calendário do instrumento.
- Funding como custo de carregar no motor (mecanismo pronto; o histórico completo depende do fetcher na máquina do Marcelo).
- DSR global: todas as configurações do torneio como tentativas e a variância do nulo como variância; concentração de retorno por janela; Sharpe sem os cinco melhores dias; os três entram no veredito.
- Walk-forward com modo "média da grade".
- Fetcher da Binance: unidade de tempo linha a linha, volume taker e número de negócios preservados, nome por mercado; cache invalidado quando a fonte muda.
- Defasagem de dois dias nos dados on-chain da CoinMetrics (não são point-in-time).
- Registro de hipóteses em `research/hipoteses.md`, cuja contagem é o N do DSR.

Pendentes, por ordem: motor em painel e em carteira (pesos T×N, hedge de beta, funding por perna, folds por timestamp, `Strategy.fit` separado), regularização por sessão e calendário do WIN (fuso, feriados, vencimento, série contínua, leilões), teste de seleção adversa da ordem limitada, duelos somando posições em vez de retornos, reconciliação diária entre paper trading e motor, coletor.

## 4. Plano de 90 dias

Cada iniciativa tem hipótese, dado, sucesso e abandono nos pareceres; aqui, a ordem e os marcos.

| semanas | iniciativa | dono da ideia | marco de sucesso | abandono |
|---|---|---|---|---|
| 1-2 | Coletor BTC (Binance perpétuo: klines com taker, funding, OI, L1) e WIN (MT5: 1 min, ticks, DOM), proveniência e manifesto; livro de regras v0 | Straus, Brown, Ax e Baum | 30 dias com 99,5% dos minutos cobertos | abaixo de 98%: trocar de fonte |
| 2-6 | Painel de IC em 2020-2026 na Binance: ~40 features pré-registradas em 5 grupos, horizontes de 1 h a 3 d, janelas mensais, BH-FDR 10%, confirmação 2024-25, cofre 2026 | Mercer, Patterson, Simons | ≥ 2 features com IC ≥ 0,03, t > 3 e mesmo sinal em 70% das janelas | nenhuma: BTC vira só coleta |
| 3-6 | Motor em painel e em carteira | Laufer, Frey | reproduz o torneio de um ativo e passa no lookahead com N ativos | pré-requisito com teto |
| 5-9 | Carry de funding com regra de percentil; resíduo de alts contra BTC | Frey | carry > 8% a.a. líquido, DD < 5%, zero liquidações a 2x; resíduo com IC > 0,02 e t > 3 | carry < 5%; resíduo com IC < 0,01 |
| 6-12 | Paper trading no tamanho mínimo, reconciliado diariamente com o motor; monitor separado, kill switch, limites | Brown, Simons, Berlekamp | custo realizado ≤ 14 bps a mercado, ≤ 8 bps limitada com fill ≥ 60%; 200 fills medidos | custo acima de 25 bps: o modelo de custo está errado |
| do dia 60 | WIN: calendário e relógio (abertura, EUA, PTAX, fechamento), série contínua com rolagem, duas fontes concordando em 99% das barras; hipóteses H011 e H012 | Laufer, Berlekamp | uma feature com t > 3, estável por ano, ≥ 2 bps líquidos | < 2 anos de histórico: coletar, não operar |

Critérios que valem para tudo: nada de 2018-2019 é operado; nada abaixo de 1 hora em BTC a mercado; aprovação exige DSR global acima de 0,9, 100 ou mais trades, três eras com o mesmo sinal, nenhuma janela com mais de 60% do lucro, Sharpe sem os cinco melhores dias acima da metade; tamanho zero até lá.

## 5. Perguntas cruzadas e respostas provisórias do presidente

- *Simons, Laufer, Frey e Ax a Berlekamp* (edge mínimo e apostas por ano no WIN; a fila do leilão; largura substitui frequência): pela tabela de Berlekamp, IC de 0,03 a 1 hora no WIN dá Sharpe perto de 0,8 por ano; t igual a 3 em doze meses exigiria Sharpe 3, o que nenhum sinal fraco isolado entrega. O caminho é combinar sinais pouco correlacionados ou aceitar dois a três anos de evidência. Um a três contratos não movem o book do WIN; o risco do leilão é de fill, não de impacto, e se mede com o diário de ordens. Largura substitui frequência na fórmula, mas a largura efetiva em cripto é pequena e cada perna paga 14 bps: só com ordem limitada.
- *Berlekamp e Patterson a Mercer* (correlação entre sinais; quantas features antes de virar ajuste): sinais com correlação 0,3 têm teto, por isso os cinco grupos de features são de naturezas diferentes; cerca de 40 features pré-registradas, FDR de 10%, janela de confirmação, e o registro inteiro, incluindo os 146 testes on-chain já feitos, como N do DSR da combinação.
- *Mercer a Laufer* (largura efetiva 3): o pooling compra a raiz de 3; o agrupamento por evento de relógio compra anos vezes eventos, que é onde o poder estatístico realmente aparece.
- *Straus a Laufer* (qual relógio para um modelo conjunto): tempo relativo ao evento, não hora do dia; barras de volume exigem negócios, então o coletor guarda aggTrades.
- *Brown a Straus* (duas fontes por barra): BTC já tem Bitstamp e Binance ingeridas; WIN precisa de duas corretoras ou MT5 mais Nelogica.

## 6. Decisões

1. Nenhuma estratégia atual é operável. O laboratório muda de "comparar estratégias" para "medir sinais e combinar".
2. Coleta própria começa esta semana, BTC e WIN, antes de qualquer pesquisa nova.
3. O registro de hipóteses é a fonte do N do DSR; nada é testado sem entrada prévia nele.
4. O livro de regras de operação é escrito antes do primeiro paper trade, com os limiares de Ax e Baum como ponto de partida.
5. O primeiro ano se mede em cobertura de dados, hipóteses mortas, erro backtest versus paper e latência de ideia a resultado. Não em dinheiro.
6. Próxima sessão quando o painel de IC tiver resultado ou em 30 dias, o que vier primeiro.

# Parecer de Henry Laufer — sessão de 2026-10-05

O que não se transfere: eu tinha dezenas de mercados e décadas de dados limpos; "um modelo para todos os mercados" fazia sentido porque havia todos os mercados. O que se transfere é aritmética: sinal fraco só aparece com muita observação, e observação se ganha agrupando instrumentos, anos e eventos.

## 1. Diagnóstico do que existe

O motor é honesto: lag, custo por giro, nulo com a mesma exposição, vitrine separada do OOS. 21 meses de um ativo não respondem nada: o IC de 90% do melhor (tsmom diário, 40 trades) é [-0,19; 2,21], entre perder e ser ótimo. Separar Sharpe 0,5 de zero pede ~16 anos de uma série, ou 16 anos-instrumento pouco correlacionados. Nada tem 100 trades OOS; abaixo disso eu não leio.

A sazonalidade por hora matou uma ideia certa do jeito certo: escolhe k entre 24 horas com 365 observações por hora (erro-padrão ~5 bps; efeito real, se existir, de 1-3 bps), num ativo só, em hora UTC, que espalha a abertura americana entre 13h30 e 14h30 conforme o horário de verão. Em 1h: bruto +1%, custos 263%. Testou ruído mais custo.

Dois detalhes: o DSR deflaciona pela grade de uma estratégia, mas o ranking escolheu entre 300+ configurações; e `regularize_1m` preenche todo minuto do calendário: no WIN são ~900 barras sintéticas por noite, que matam as features de relógio.

## 2. Onde procurar edge (e quais dados primeiro)

Onde o relógio é institucional; o WIN tem muito mais relógio que o BTC: abertura às 9h digerindo o gap da noite; abertura dos EUA, que cai às 10h30 ou 11h30 de Brasília conforme o mês, porque o Brasil aboliu o horário de verão: a feature se define em hora de Nova York; as janelas da PTAX (10h-13h10) e o último dia útil do mês, via dólar; leilão de fechamento do à vista (~17h) e depois uma hora de futuro sem o à vista; vencimento na quarta mais próxima do dia 15 dos meses pares. No BTC: funding às 0h, 8h e 16h UTC; abertura dos EUA (13h30/14h30 UTC); fim de semana e reabertura do CME.

Dados, nesta ordem: (1) Bitstamp desde 2012 e Binance com funding, 1 min, BTC, ETH e dois majors: o painel de cripto; (2) WIN 1 min costurando várias corretoras, mais WDO e as cinco maiores ações do índice; (3) gravar WIN a partir de hoje: cada dia gravado é painel.

## 3. Método

Feature relativa ao evento, não à hora do dia: minutos desde a abertura, minutos desde o funding, dias até o vencimento. Retorno em unidades da volatilidade do instrumento, senão o painel vira o ativo mais volátil. Hipótese escrita antes do teste. Critério: t agrupado > 3 e mesmo sinal em dois terços das células instrumento×ano. Cripto tem correlação ~0,8 entre ativos: cinco ativos valem pouco mais de um; quem multiplica são anos e eventos.

O motor muda assim: `load_panel(symbols, tf)` com regularização por sessão (`Instrument` ganha fuso, sessão, feriados, vencimento e série contínua ajustada); `calendar.py` gerando as features de relógio por barra; `Strategy.fit(panel, train_range)` separado de `positions(bars, model)`; folds por timestamp; score no treino pela carteira de risco igual, com tabela por instrumento; nulo por instrumento; veredito com 100 trades e consistência por célula.

## 4. Execução e tamanho

No WIN a ida e volta custa ~1 bp (taxa 0,2, tick 0,4) contra 14 no BTC: um efeito de 2-3 bps paga no WIN e morre no BTC. No WIN o tamanho é 1, 2 ou 3 contratos: o modelo decide direção e horário, não tamanho; vol target vira "opera ou não". No BTC o relógio é filtro, não estratégia.

## 5. Plano de 90 dias

1. **Motor em painel (semanas 1-3).** Hipótese: o nulo é calibrado. Dado: Bitstamp + Binance. Sucesso: testes passam; 20 sementes de entradas aleatórias dão p uniforme. Abandono: não há; infraestrutura com prazo.
2. **Relógio do BTC em painel (semanas 2-6).** Hipótese: em torno do funding positivo o retorno condicional é negativo; a meia hora após a abertura dos EUA continua o movimento noturno. Dado: painel de 1 com funding. Sucesso: t > 3, mesmo sinal em 80% dos anos-ativo, 300+ eventos OOS, líquido a custo maker. Abandono: nenhum |t| > 2,5; relógio vira só filtro.
3. **Dados e calendário do WIN (semanas 4-10).** Hipótese: os 15 min após 9h continuam o gap medido pelo S&P futuro; 17h-18h25 reverte. Dado: WIN, WDO, S&P futuro e cinco ações em 1 min. Sucesso: uma feature com t > 3, estável por ano, 2+ bps líquidos. Abandono: menos de 2 anos de histórico e nenhum |t| > 2 agrupando com as ações.
4. **Relógio como filtro (semanas 8-12).** Hipótese: tsmom diário e Donchian 1h executando só em janelas líquidas mantêm o bruto e cortam custo. Sucesso: custo cai 30% com bruto dentro do ruído. Abandono: Sharpe OOS cai.

## 6. O que eu não faria

Nada abaixo de 15 min no BTC: a resposta já veio. Nenhum parâmetro por instrumento antes do efeito aparecer no painel. Nenhuma hora-do-dia como feature; só tempo relativo ao evento. Nada com menos de 100 trades.

## 7. Pergunta

Para Berlekamp: achado um efeito de 2-3 bps na abertura das 9h do WIN, uma aposta por dia em 1 a 3 contratos, a fila do leilão de abertura come o efeito? Quantas apostas por dia esse tamanho comporta antes que frequência vire custo? O painel acha o efeito; você diz se ele paga.

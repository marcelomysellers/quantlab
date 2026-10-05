# Conselho

Uma estrutura de agentes que modela, a partir de fontes públicas, as pessoas que construíram a Renaissance Technologies. Cada pessoa tem uma **carta** em `personas/`: quem foi, o que fez, no que acreditava, como abordaria o nosso problema e onde a experiência dela não se transfere para capital pequeno. As cartas são modelos estilizados montados a partir de fontes públicas (Zuckerman, *The Man Who Solved the Market*, 2019; TED 2015 do Simons; relatório do Senado dos EUA de 2014 sobre basket options; entrevistas e palestras públicas). Não são as pessoas, e as recomendações são do modelo, não delas.

## Como convocar

1. Atualize `brief.md` com o estado atual do projeto e as perguntas da pauta.
2. Peça ao Claude Code: *"convoque o conselho"*. Ele cria um agente por carta, em paralelo, cada um lendo a própria carta, o brief e o repositório, e grava um parecer em `sessions/<data>/<pessoa>.md`.
3. O presidente (Simons) consolida os pareceres em `sessions/<data>/ata.md`: consenso, divergências e um plano priorizado.

## Membros

| Pessoa | Papel no conselho | Voz |
|---|---|---|
| Jim Simons | presidente | pessoas, cultura, paciência, infraestrutura, "o sistema decide" |
| Elwyn Berlekamp | frequência e tamanho das apostas | muitas apostas pequenas, custo por trade, teoria da informação |
| Henry Laufer | modelo único | um modelo para todos os mercados, pooling de dados, efeitos de calendário |
| Robert Mercer | sinais | sinais fracos sem explicação, combinação, "50,75% das vezes" |
| Peter Brown | engenharia | rigor de código, bugs, sistema de ponta a ponta |
| Nick Patterson | estatística | limpeza de dados, razão sinal/ruído, ceticismo com histórias |
| Sandor Straus | dados | coletar e guardar tudo, o dado é o fosso |
| Robert Frey | arbitragem estatística | neutralidade, resíduos, carteiras e não apostas |
| Ax e Baum | a primeira era | o que funcionou nos anos 80 e como a mão humana estragou |

# Peter Brown

**Quem foi (público).** Cientista da computação da IBM (fala e tradução estatística, com Mercer). Entrou na Renaissance em 1993, co-construiu o sistema de ações, co-CEO a partir de 2010 e CEO único desde 2017. Conhecido pela intensidade de trabalho, pela atenção obsessiva a detalhes de implementação e por tratar o fundo como um único sistema de engenharia, de dados a execução.

**No que acreditava (público).** O modelo é um programa, e programas têm bugs; um bug no sistema pode custar mais que um ano de pesquisa (o livro conta o episódio em que um erro de código no sistema de ações foi encontrado por David Magerman e corrigido antes de o sistema finalmente funcionar). Tudo de ponta a ponta: coleta, limpeza, previsão, otimização, execução, reconciliação. Logs e reconciliação diária entre o que o modelo pediu e o que o mercado deu.

**Como abordaria o nosso problema.** Elogiaria o teste de lookahead e pediria mais: testes de unidade para cada custo, reconciliação entre o backtest e o paper trading com os mesmos sinais (as diferenças revelam bugs e custos escondidos), simulação de falhas (API caiu no meio de uma ordem, posição órfã, relógio errado). Diria que a operação automatizada de uma pessoa precisa de um kill switch, limite diário de perda, limite de ordens por minuto, e um monitor independente do bot. Perguntaria o que acontece às 3 da manhã quando a exchange devolve erro 500.

**Onde a experiência não se transfere.** Ele tinha times de engenharia. O que se transfere: tratar o sistema inteiro, não o sinal, como o produto, e desconfiar de todo resultado até ser reproduzido por um caminho independente.

**Voz na sessão.** Engenharia, falhas, reconciliação. Pergunta "como você sabe que isso está certo?".

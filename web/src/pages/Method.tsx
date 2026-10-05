import type { Manifest } from "../types";
import { num, pct } from "../format";

export function Method({ manifest }: { manifest: Manifest }) {
  return (
    <div className="card prose">
      <h2>Como o torneio funciona</h2>
      <p className="sub">Gerado em {new Date(manifest.generated_at).toLocaleString("pt-BR")} · {manifest.instrument} · dados de {manifest.start} a {manifest.end} · {num(manifest.elapsed_s, 0)} s de cálculo.</p>
      <h3>1. Sem lookahead, por construção</h3>
      <p>A estratégia decide a posição no fechamento da barra t. O motor executa na abertura de t+1, nunca no preço que gerou o sinal. Um teste automático confirma que truncar a série não muda nenhuma posição anterior ao corte, para todas as estratégias.</p>
      <h3>2. Custos antes de sinal</h3>
      <p>Cada mudança de posição paga taxa, metade do spread, deslize fixo e um deslize extra proporcional ao range da barra anterior (mercado rápido = execução pior). Três cenários: otimista, base e pessimista. Uma estratégia que só funciona no otimista não funciona.</p>
      <h3>3. Execução realista, não execução de backtest</h3>
      <p>Ordens a mercado executam inteiras, no preço ruim. Ordens limitadas, quando usadas, só executam se o preço atravessa o limite (tocar não vale) e podem sair parciais. Além disso, cada estratégia passa por um estresse em que {pct(manifest.stress_model.miss_prob, 0)} das entradas não executam e {pct(manifest.stress_model.partial_prob, 0)} saem parciais: o Sharpe que sobra é o que vale.</p>
      <h3>4. Walk-forward</h3>
      <p>Treino de {manifest.wf.train_months} meses, teste de {manifest.wf.test_months} meses, rolando. Em cada janela a melhor configuração do treino (por Sharpe diário, com mínimo de {manifest.wf.min_trades} trades) é aplicada ao teste seguinte. A curva costurada dos testes é o único resultado que conta. A "curva de vitrine" (melhor parâmetro escolhido olhando o período todo) aparece junto só para mostrar o tamanho do overfitting.</p>
      <h3>5. O nulo certo</h3>
      <p>{manifest.null_kind === "shift"
        ? `Cada estratégia é comparada com ${manifest.n_null} versões de si mesma com as posições deslocadas circularmente no tempo: mesma exposição, mesmos trades e durações, mesma mistura comprado/vendido, mesmos custos; só o alinhamento com o preço é destruído. O p-valor é a fração de deslocamentos que empatam ou superam o Sharpe real.`
        : `Cada estratégia é comparada com ${manifest.n_null} estratégias sorteadas com o mesmo número de trades, as mesmas durações, a mesma mistura comprado/vendido e os mesmos custos. O p-valor é a fração de sorteios que empatam ou superam o Sharpe real.`} Comparar com comprar-e-segurar não basta: num mercado que caiu 80%, qualquer coisa que fique fora parece boa.</p>
      <h3>5b. Concentração e tentativas</h3>
      <p>Três perguntas a mais, nascidas do conselho: quanto do lucro veio de uma única janela (nenhuma pode passar de 60%), quanto sobra sem os cinco melhores dias (mais da metade do Sharpe), e qual é o Sharpe deflacionado contando TODAS as configurações que o torneio testou, com a variância do próprio nulo. O walk-forward também pode rodar em modo "média da grade": em vez de escolher o melhor parâmetro do treino, que é um máximo sobre ruído, usa a média das posições de todas as configurações.</p>
      <h3>6. Contar as tentativas</h3>
      <p>Testar 16 configurações e mostrar a melhor é trapaça estatística. O Sharpe deflacionado (Bailey & López de Prado, 2014) é a probabilidade de o Sharpe ser positivo depois de descontar o número de configurações testadas e a não-normalidade dos retornos. Métricas de significância usam retornos diários, a base comum entre timeframes.</p>
      <h3>7. Veredito</h3>
      <ul>
        <li><b>aprovada</b>: Sharpe OOS base &gt; 0,5, p contra aleatórias &lt; 0,05, DSR &gt; 0,90, Sharpe positivo no cenário pessimista, pelo menos 30 trades.</li>
        <li><b>promissora</b>: Sharpe OOS &gt; 0,3 com CAGR positivo, p &lt; 0,15, pelo menos 30 trades, nenhuma janela com mais de 60% do lucro e Sharpe positivo sem os 5 melhores dias. Vale investigar, não vale operar.</li>
        <li><b>reprovada</b>: o resto. A maioria. É assim que deve ser.</li>
      </ul>
      <h3>Como adicionar uma estratégia</h3>
      <p>Crie uma classe em <code>quantlab/strategies/library.py</code> herdando de <code>Strategy</code>, declare <code>param_space</code>, implemente <code>positions()</code> só com operações que olham para trás e registre no <code>REGISTRY</code>. Rode <code>python tests/test_engine.py</code> (o teste de lookahead cobre a nova estratégia) e depois <code>python -m quantlab.cli tournament --publish</code>.</p>
    </div>
  );
}

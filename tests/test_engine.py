"""Sanidade do motor e das estratégias. Rode: python -m pytest -q  (ou python tests/test_engine.py)."""
import numpy as np
import pandas as pd

from quantlab.backtest.engine import run_backtest, aggregate_daily
from quantlab.backtest.metrics import summarize, psr, dsr
from quantlab.execution import ExecutionModel, FillModel, apply_fill_stress, limit_fill_fraction, SCENARIOS
from quantlab.strategies import REGISTRY, Context, positions_from_events

ZERO = ExecutionModel("zero", 0, 0, 0, 0)


def synth_bars(n=500, seed=0):
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.01, n)
    close = 100 * np.cumprod(1 + r)
    open_ = np.concatenate(([100.0], close[:-1]))
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.005, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.005, n))
    idx = pd.date_range("2020-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": 1.0}, index=idx)


def test_buy_hold_matches_open_to_open():
    bars = synth_bars()
    res = run_backtest(bars, np.ones(len(bars)), ZERO, 60)
    # lag 1: posição vale a partir da barra 1; retorno acumulado = open[-1]/open[1]
    assert np.isclose(res.equity[-1], bars["open"].iloc[-1] / bars["open"].iloc[1])
    assert res.trades.shape[0] == 1 and bool(res.trades["open"].iloc[0])


def test_costs_charged_on_turnover():
    bars = synth_bars()
    em = ExecutionModel("c", fee_bps=10, spread_bps=0, slippage_bps=0, impact_k=0)
    target = np.ones(len(bars))
    res = run_backtest(bars, target, em, 60)
    assert np.isclose(res.cost.sum(), 10 / 1e4)           # só a entrada
    flip = np.where(np.arange(len(bars)) % 2 == 0, 1.0, -1.0)
    res2 = run_backtest(bars, flip, em, 60)
    assert abs(res2.turnover[2:].mean() - 2.0) < 0.05      # vira a cada barra (o lado vendido deriva um pouco)
    assert res2.cost.sum() > 0.5                            # custo devora tudo


def test_no_lookahead_in_engine():
    """Mudar a última barra não pode alterar nada antes dela."""
    bars = synth_bars()
    target = np.sign(np.sin(np.arange(len(bars)) / 7))
    a = run_backtest(bars, target, SCENARIOS["base"], 60)
    bars2 = bars.copy()
    bars2.iloc[-1, bars2.columns.get_loc("open")] *= 1.5
    b = run_backtest(bars2, target, SCENARIOS["base"], 60)
    assert np.allclose(a.net[:-2], b.net[:-2])


def test_positions_from_events():
    le = np.array([1, 0, 0, 0, 0, 0, 0], bool)
    lx = np.array([0, 0, 1, 0, 0, 0, 0], bool)
    se = np.array([0, 0, 0, 0, 1, 0, 0], bool)
    sx = np.array([0, 0, 0, 0, 0, 0, 1], bool)
    assert positions_from_events(le, lx, se, sx).tolist() == [1, 1, 0, 0, -1, -1, 0]
    # entrada short vira a posição long sem precisar de saída
    le = np.array([1, 0, 0, 0], bool); se = np.array([0, 0, 1, 0], bool); z = np.zeros(4, bool)
    assert positions_from_events(le, z, se, z).tolist() == [1, 1, -1, -1]


def test_fill_stress_and_limit_rule():
    pos = np.array([0, 1, 1, 0, -1, -1, -1, 0, 1, 0], float)
    stressed = apply_fill_stress(pos, FillModel(miss_prob=1.0))
    assert np.all(stressed == 0)
    stressed = apply_fill_stress(pos, FillModel(partial_prob=1.0, partial_min=0.5, seed=1))
    assert np.all(np.abs(stressed[pos != 0]) >= 0.5) and np.all(np.abs(stressed[pos != 0]) <= 1.0)
    # ordem limitada de compra a 100, tick 1: tocar (low=100) não executa; low=99 executa parcial; low=97 executa tudo
    frac = limit_fill_fraction(+1, 100.0, np.array([101, 101, 101.0]), np.array([100, 99, 97.0]), 1.0, 1, 3)
    assert frac[0] == 0.0 and 0 < frac[1] < 1 and frac[2] == 1.0


def test_strategies_have_no_lookahead():
    bars = synth_bars(1500, seed=3)
    ctx = Context("1h", 60, 8766.0, 24.0)
    cut = 1000
    for name, strat in REGISTRY.items():
        if not strat.supports(ctx):
            continue
        for params in strat.grid(ctx)[:3]:
            fit = slice(0, 600) if strat.needs_fit else None
            full = strat.positions(bars, params, ctx, fit)
            part = strat.positions(bars.iloc[:cut], params, ctx, fit)
            assert np.allclose(full[:cut], part), f"lookahead em {name} {params}"
            assert np.all(np.abs(full) <= 1.0 + 1e-9), f"posição fora de [-1,1] em {name}"


def test_metrics_and_dsr_behave():
    rng = np.random.default_rng(0)
    r = rng.normal(0.001, 0.01, 1000)
    m = summarize(r, np.ones(1000), np.zeros(1000), 365.25)
    assert m["sharpe"] > 0 and 0 < m["psr"] <= 1
    # mais tentativas -> DSR menor
    d1 = dsr(0.1, 1000, 0.0, 3.0, n_trials=1, var_sr=0.01)
    d2 = dsr(0.1, 1000, 0.0, 3.0, n_trials=100, var_sr=0.01)
    assert d1 > d2
    assert psr(0.0, 1000, 0.0, 3.0) == 0.5


def test_daily_aggregation():
    bars = synth_bars(48)
    net = np.full(48, 0.001)
    d = aggregate_daily(net, bars.index)
    assert len(d) == 2 and np.isclose(d.iloc[0], (1.001 ** 24) - 1)


def test_fit_strategies_do_not_peek_past_train_window():
    """Mudar o TESTE não pode mudar o que a estratégia com ajuste aprendeu no TREINO."""
    bars = synth_bars(1500, seed=5)
    ctx = Context("1h", 60, 8766.0, 24.0)
    for name, strat in REGISTRY.items():
        if not strat.needs_fit or not strat.supports(ctx):
            continue
        params = strat.grid(ctx)[0]
        a = strat.positions(bars, params, ctx, fit_slice=slice(0, 1000))
        bars2 = bars.copy()
        bars2.iloc[1000:, bars2.columns.get_loc("open")] *= 1.3   # altera só o teste
        b = strat.positions(bars2, params, ctx, fit_slice=slice(0, 1000))
        assert np.allclose(a, b), f"{name} aprende com dados do teste"


def test_trade_costs_add_up():
    """Soma dos resultados líquidos por trade = retorno líquido total (sem posição aberta no fim)."""
    bars = synth_bars(400, seed=7)
    rng = np.random.default_rng(1)
    target = np.where(rng.random(400) < 0.1, rng.choice([-1.0, 0.0, 0.5, 1.0], 400), np.nan)
    target = pd.Series(target).ffill().fillna(0.0).to_numpy().copy()
    target[-5:] = 0.0
    res = run_backtest(bars, target, SCENARIOS["pessimista"], 60)
    assert np.isclose(res.trades["ret_net"].sum(), res.net.sum(), atol=1e-9)
    assert np.isclose(res.trades["ret_gross"].sum(), res.gross.sum(), atol=1e-9)


def test_daily_aggregation_skips_days_without_bars():
    idx = pd.to_datetime(["2024-01-01 10:00", "2024-01-01 11:00", "2024-01-04 10:00"], utc=True)
    d = aggregate_daily(np.array([0.01, 0.01, -0.02]), pd.DatetimeIndex(idx))
    assert len(d) == 2 and np.isclose(d.iloc[0], 1.01 ** 2 - 1)


def test_drift_is_not_charged_but_maintenance_is():
    """Comprado 100% não paga nada para manter; 50% constante paga a recompra/venda que mantém o peso."""
    bars = synth_bars(300, seed=11)
    em = ExecutionModel("c", fee_bps=10, spread_bps=0, slippage_bps=0, impact_k=0)
    full = run_backtest(bars, np.ones(300), em, 60)
    half = run_backtest(bars, np.full(300, 0.5), em, 60)
    assert np.isclose(full.turnover[2:].sum(), 0.0)
    assert half.turnover[2:].sum() > 0.0
    # peso derivado informado pela estratégia: giro zero entre rebalanceamentos
    pos = np.full(300, 0.5)
    r = bars["open"].pct_change().shift(-1).fillna(0.0).to_numpy()   # retorno open->open da própria barra
    for t in range(1, 300):
        pos[t] = pos[t - 1] * (1 + r[t - 1]) / (1 + pos[t - 1] * r[t - 1])
    target = np.concatenate((pos[1:], [pos[-1]]))   # o motor aplica 1 barra de atraso: alvo[t] = peso desejado em t+1
    res = run_backtest(bars, target, em, 60)
    assert res.turnover[3:].sum() < 1e-9


def test_no_execution_on_synthetic_open():
    bars = synth_bars(50)
    bars["open_synthetic"] = False
    bars.iloc[10:13, bars.columns.get_loc("open_synthetic")] = True
    target = np.zeros(50); target[9:] = 1.0
    res = run_backtest(bars, target, ZERO, 60)
    assert res.pos[10] == 0 and res.pos[11] == 0 and res.pos[12] == 0 and res.pos[13] == 1


if __name__ == "__main__":
    import sys
    g = dict(globals())
    fails = 0
    for k, f in g.items():
        if k.startswith("test_") and callable(f):
            try:
                f(); print("ok  ", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
            except Exception as e:
                fails += 1; print("ERR ", k, repr(e))
    sys.exit(1 if fails else 0)

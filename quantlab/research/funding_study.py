"""Funding do perpétuo BTCUSDT (Binance) em três papéis (H016, H017, H018) e a estratégia contrária (H023).

Estudo original (2020-2023, funding do dataset supervik):

    python -m quantlab.research.funding_study

Confirmação fora da amostra (2024 em diante, funding oficial trazido por quantlab.data.binance para data/public):

    python -m quantlab.research.funding_study --confirm [--start 2024-01-01] [--end 2026-10-01]

Na confirmação os parâmetros da H023 ficam fixos (24 h, percentil 10 móvel de 90 dias) e o critério de
sobrevivência está pré-registrado em research/hipoteses.md: Sharpe base > 0,5, p < 0,10 contra deslocamento,
maker com filtro > 0, CAGR pessimista > 0 e pelo menos 30 trades, tudo dentro da janela de confirmação,
no preço do perpétuo e sem contar o funding recebido.

1. Sinal (Laufer): após funding no decil extremo (percentil móvel de 90 dias), o retorno seguinte.
2. Carry (Frey): vendido no perpétuo e comprado no spot só quando a média de 7 dias do funding está
   acima de um percentil; P&L = funding recebido, SEM o P&L da base e SEM risco de liquidação (é um piso).
3. Custo (Straus, Ax): quanto o funding tira de uma estratégia de tendência sempre comprada.
4. Contrária (H023): comprado 24 h depois de cada funding abaixo do percentil 10 móvel.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

from quantlab.backtest.engine import aggregate_daily, funding_per_bar, run_backtest
from quantlab.backtest.metrics import sharpe
from quantlab.data.funding import load_funding
from quantlab.data.store import load_bars
from quantlab.execution import SCENARIOS, ExecutionModel, FillModel
from quantlab.strategies import REGISTRY, Context

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOLD_H = 24          # parâmetros fixos da H023 (escolhidos em 2020-2023, não se mexe na confirmação)
PCT_THR = 0.10
PCT_WINDOW = 270     # 90 dias de funding a cada 8 h
PCT_MIN = 90


def _window(index: pd.DatetimeIndex, start: str | None, end: str | None) -> np.ndarray:
    m = np.ones(len(index), dtype=bool)
    if start:
        m &= np.asarray(index >= pd.Timestamp(start, tz="UTC"))
    if end:
        m &= np.asarray(index < pd.Timestamp(end, tz="UTC"))
    return m


def event_study(b1h: pd.DataFrame, fr: pd.Series, start: str | None = None, end: str | None = None) -> list[dict]:
    """Retorno após funding em percentil extremo. O percentil usa toda a série; só os eventos na janela contam."""
    lo = np.log(b1h["open"])
    out = []
    pct = fr.rolling(PCT_WINDOW, min_periods=PCT_MIN).rank(pct=True)
    idx = b1h.index.searchsorted(fr.index)
    ok = (idx > 0) & (idx < len(b1h) - 30) & _window(fr.index, start, end)
    for h in (1, 8, 24):
        fwd = (lo.shift(-(1 + h)) - lo.shift(-1)).to_numpy()
        y = fwd[idx[ok]]
        p = pct.to_numpy()[ok]
        yrs = fr.index.year.to_numpy()[ok]
        for name, mask in (("funding > p90", p > 0.9), ("funding < p10", p < 0.1), ("meio (p10-p90)", (p >= 0.1) & (p <= 0.9))):
            yy = y[mask]; yy = yy[~np.isnan(yy)]
            if len(yy) < 30:
                continue
            t = yy.mean() / (yy.std(ddof=1) / np.sqrt(len(yy)))
            by_year = pd.Series(y[mask], index=yrs[mask]).dropna().groupby(level=0).mean()
            out.append({"bucket": name, "horizon_h": h, "mean_bps": round(1e4 * float(yy.mean()), 2), "t": round(float(t), 2),
                        "n": int(len(yy)), "year_consistency": round(float((np.sign(by_year) == np.sign(yy.mean())).mean()), 2)})
    return out


def carry_rules(fr: pd.Series, cost_rt_bps: float = 30.0, start: str | None = None, end: str | None = None) -> list[dict]:
    """Carry com regra de percentil. Percentis sobre a série inteira; P&L só dentro da janela."""
    m7 = fr.rolling(21).mean()
    pct = m7.rolling(540, min_periods=180).rank(pct=True)   # percentil móvel de 180 dias
    win = _window(fr.index, start, end)
    frw = fr[win]
    out = []
    per_year = 3 * 365.25
    years = len(frw) / per_year
    for enter, exit_ in ((0.60, 0.30), (0.70, 0.40), (0.80, 0.50)):
        pos = np.zeros(len(fr))
        inpos = False
        for i, p in enumerate(pct.to_numpy()):
            if np.isnan(p):
                continue
            if not inpos and p > enter:
                inpos = True
            elif inpos and p < exit_:
                inpos = False
            pos[i] = 1.0 if inpos else 0.0
        posw = pos[win]
        pnl = posw * frw.to_numpy()
        turns = np.abs(np.diff(np.concatenate(([0.0], posw)))).sum()
        cost = turns * cost_rt_bps / 2 / 1e4
        gross = float(pnl.sum()); net = gross - cost
        monthly = pd.Series(pnl, index=frw.index).resample("1ME").sum()
        out.append({"regra": f"entra > p{int(enter*100)}, sai < p{int(exit_*100)}", "tempo_posicionado": round(float(posw.mean()), 2),
                    "entradas": int(round(turns / 2)), "bruto_aa": round(gross / years, 4), "liquido_aa": round(net / years, 4),
                    "pior_mes": round(float(monthly.min()), 4), "meses_negativos": int((monthly < 0).sum())})
    out.append({"regra": "sempre posicionado", "tempo_posicionado": 1.0, "entradas": 1, "bruto_aa": round(float(frw.mean() * per_year), 4),
                "liquido_aa": round(float(frw.mean() * per_year) - cost_rt_bps / 1e4 / years, 4),
                "pior_mes": round(float(frw.resample("1ME").sum().min()), 4), "meses_negativos": int((frw.resample("1ME").sum() < 0).sum())})
    return out


def funding_as_cost(fr: pd.Series) -> list[dict]:
    out = []
    specs = [("tsmom", "4h", {"lookback": 24, "vol_target": 0.5}), ("tsmom", "4h", {"lookback": 96, "vol_target": None}),
             ("sma_cross", "1d", {"fast": 10, "slow": 100, "mode": "lo"}), ("sma_cross", "1d", {"fast": 20, "slow": 100, "mode": "ls"}),
             ("buy_hold", "1d", {})]
    for name, tf, params in specs:
        bars = load_bars("BTCUSDT-BINANCE", tf, "2019-06-01", "2024-01-01")
        tfm = {"4h": 240, "1d": 1440}[tf]
        ctx = Context(tf, tfm, 525960 / tfm if tf != "1d" else 365.25, 1440 / tfm)
        tgt = REGISTRY[name].positions(bars, params, ctx)
        sl = bars.index >= pd.Timestamp("2020-01-01", tz="UTC")
        b, t = bars[sl], tgt[sl]
        f = funding_per_bar(b, fr)
        res0 = run_backtest(b, t, SCENARIOS["base"], tfm)
        res1 = run_backtest(b, t, SCENARIOS["base"], tfm, funding=f)
        d0, d1 = aggregate_daily(res0.net, b.index), aggregate_daily(res1.net, b.index)
        yrs = len(d0) / 365.25
        out.append({"estrategia": f"{name} {tf} {params}", "sharpe_sem_funding": round(sharpe(d0.to_numpy(), 365.25), 2),
                    "sharpe_com_funding": round(sharpe(d1.to_numpy(), 365.25), 2),
                    "cagr_sem": round(float(np.prod(1 + d0) ** (1 / yrs) - 1), 4), "cagr_com": round(float(np.prod(1 + d1) ** (1 / yrs) - 1), 4),
                    "funding_pago_aa": round(float((res0.pos * f).sum() / yrs), 4), "exposicao_media": round(float(np.mean(res0.pos)), 2)})
    return out


def contrarian_target(b1h: pd.DataFrame, fr: pd.Series, hold_h: int = HOLD_H, pct_thr: float = PCT_THR) -> np.ndarray:
    """Alvo 0/1 da H023: comprado por `hold_h` barras de 1 h depois de cada funding abaixo do percentil móvel (janelas sobrepostas se fundem).
    O sinal usa o funding carimbado em t e a execução fica para a abertura de t+1 (defasagem do motor)."""
    pct = fr.rolling(PCT_WINDOW, min_periods=PCT_MIN).rank(pct=True)
    events = fr.index[pct < pct_thr]
    target = np.zeros(len(b1h))
    idx = b1h.index
    for t in events:
        i = idx.searchsorted(t)
        if 0 < i < len(idx):
            target[i: i + hold_h] = 1.0
    return target


def contrarian_strategy(b1h: pd.DataFrame, fr: pd.Series, hold_h: int = HOLD_H, pct_thr: float = PCT_THR,
                        start: str = "2020-04-01", end: str = "2024-01-01", with_funding: bool = False,
                        n_null: int = 200, seed: int = 0) -> list[dict]:
    """H023 no motor com custos base, pessimista e maker com filtro de seleção adversa; nulo por deslocamento circular.
    `with_funding=True` credita/cobra o funding de cada barra posicionada (só faz sentido no preço do perpétuo)."""
    target = contrarian_target(b1h, fr, hold_h, pct_thr)
    sl = _window(b1h.index, start, end)
    b, tgt = b1h[sl], target[sl]
    f = funding_per_bar(b, fr) if with_funding else None
    maker = ExecutionModel("maker", 2.0, 0.0, 0.0, 0.0)
    out = []
    for name, em, fill in (("base", SCENARIOS["base"], None), ("pessimista", SCENARIOS["pessimista"], None), ("maker+filtro", maker, FillModel(adverse_bps=2.0))):
        res = run_backtest(b, tgt, em, 60, fill=fill, funding=f)
        d = aggregate_daily(res.net, b.index)
        yrs = len(d) / 365.25
        sr = sharpe(d.to_numpy(), 365.25)
        rand = []
        rng = np.random.default_rng(seed)
        for _ in range(n_null):
            k = int(rng.integers(hold_h, len(tgt) - hold_h))
            r2 = run_backtest(b, np.roll(tgt, k), em, 60, fill=fill, with_trades=False, funding=f)
            rand.append(sharpe(aggregate_daily(r2.net, b.index).to_numpy(), 365.25))
        eq = np.cumprod(1 + d.to_numpy())
        years = pd.DatetimeIndex(d.index).year
        by_year = {int(y): round(sharpe(d.to_numpy()[years == y], 365.25), 2) for y in np.unique(years) if (years == y).sum() >= 60}
        out.append({"cenario": name, "sharpe": round(sr, 2), "cagr": round(float(eq[-1] ** (1 / yrs) - 1), 4),
                    "trades": int(len(res.trades)), "exposicao": round(float(np.mean(np.abs(res.pos) > 0)), 2),
                    "p_shift": round(float(np.mean(np.asarray(rand) >= sr)), 3) if n_null else float("nan"),
                    "mdd": round(float((eq / np.maximum.accumulate(eq) - 1).min()), 4), "sharpe_por_ano": by_year})
    return out


def confirm_verdict(rows: list[dict]) -> tuple[str, list[str]]:
    """Critério pré-registrado (research/hipoteses.md, H023). Devolve (veredito, lista de checagens)."""
    r = {x["cenario"]: x for x in rows}
    base, pess, maker = r["base"], r["pessimista"], r["maker+filtro"]
    checks = [("Sharpe base > 0,5", base["sharpe"] > 0.5, f"{base['sharpe']:+.2f}"),
              ("p contra deslocamento < 0,10", base["p_shift"] < 0.10, f"{base['p_shift']:.3f}"),
              ("maker com filtro > 0", maker["sharpe"] > 0, f"{maker['sharpe']:+.2f}"),
              ("CAGR pessimista > 0", pess["cagr"] > 0, f"{pess['cagr']:+.1%}"),
              ("≥ 30 trades", base["trades"] >= 30, str(base["trades"]))]
    lines = [f"- {'✓' if ok else '✗'} {name}: {val}" for name, ok, val in checks]
    if all(ok for _, ok, _ in checks):
        return "CONFIRMADA: primeira candidata a paper trading", lines
    if base["sharpe"] <= 0:
        return "MORTA: Sharpe base ≤ 0 fora da amostra", lines
    return "INCONCLUSIVA: não morreu, não confirmou; só reabre com mais 12 meses de dados", lines


def _table(L: list[str], header: list[str], rows: list[list[str]]) -> None:
    L.append("| " + " | ".join(header) + " |")
    L.append("|" + "---|" * len(header))
    for r in rows:
        L.append("| " + " | ".join(r) + " |")


def confirm(start: str = "2024-01-01", end: str | None = None, out_dir: str | None = None, n_null: int = 200) -> dict:
    out_dir = out_dir or os.path.join(ROOT, "research")
    fr = load_funding("BTCUSDT", "binance")["funding_rate"]
    fr = fr[~fr.index.duplicated()].sort_index()
    last = fr.index[-1]
    end = end or (last + pd.Timedelta(hours=8)).strftime("%Y-%m-%d")
    if last < pd.Timestamp(start, tz="UTC") + pd.Timedelta(days=180):
        raise SystemExit(f"o funding disponível termina em {last:%Y-%m-%d}, menos de 6 meses depois de {start}: "
                         "rode o fetcher da Binance na sua máquina (data/public/README.md) e commite data/public")
    sources = []
    for sym, label in (("BTCUSDT-BINANCE-UM", "perpétuo"), ("BTCUSDT-BINANCE", "spot")):
        try:
            sources.append((sym, label, load_bars(sym, "1h", "2019-12-01", end)))
        except (FileNotFoundError, ValueError):
            continue
    if not sources:
        raise SystemExit("sem barras de 1 h da Binance (nem perpétuo em data/public, nem spot em data/parquet)")
    sym0, label0, b0 = sources[0]
    fr_w = fr[_window(fr.index, start, end)]
    L = [f"# Confirmação fora da amostra do funding: {start} a {end}", "",
         f"Funding oficial: {len(fr_w)} pagamentos na janela ({fr_w.index[0]:%Y-%m-%d} a {fr_w.index[-1]:%Y-%m-%d}), "
         f"média {fr_w.mean()*1e4:.2f} bps por 8 h ({fr_w.mean()*3*365.25:.1%} ao ano). "
         f"Preço: {', '.join(f'{l} ({s}, {b.index[0]:%Y-%m-%d} a {b.index[-1]:%Y-%m-%d})' for s, l, b in sources)}. "
         f"Parâmetros da H023 fixos em 2020-2023: {HOLD_H} h, percentil {int(PCT_THR*100)} móvel de 90 dias. Nulo: {n_null} deslocamentos.", "",
         f"## 1. Funding como sinal (H016) na janela, preço {label0}", ""]
    ev = event_study(b0, fr, start, end)
    _table(L, ["bucket", "horizonte", "retorno médio (bps)", "t", "n", "consistência entre anos"],
           [[r["bucket"], f"{r['horizon_h']}h", f"{r['mean_bps']:+.1f}", f"{r['t']:+.1f}", str(r["n"]), f"{r['year_consistency']:.0%}"] for r in ev])
    L += ["", "## 2. Carry com regra de percentil (H017) na janela: só o funding recebido, 30 bps por entrada e saída", ""]
    _table(L, ["regra", "tempo posicionado", "entradas", "bruto a.a.", "líquido a.a.", "pior mês", "meses negativos"],
           [[r["regra"], f"{r['tempo_posicionado']:.0%}", str(r["entradas"]), f"{r['bruto_aa']:+.1%}", f"{r['liquido_aa']:+.1%}", f"{r['pior_mes']:+.2%}", str(r["meses_negativos"])]
            for r in carry_rules(fr, start=start, end=end)])
    L += ["", f"## 3. Estratégia contrária ao funding negativo (H023): comprado {HOLD_H} h após funding < p{int(PCT_THR*100)} móvel", ""]
    results = {}
    for sym, label, b in sources:
        for with_f in ((False, True) if label == "perpétuo" else (False,)):
            key = f"{label}{' + funding recebido' if with_f else ''}"
            rows = contrarian_strategy(b, fr, start=start, end=end, with_funding=with_f, n_null=n_null)
            results[key] = rows
            L += [f"### Preço {key}", ""]
            years = sorted({y for r in rows for y in r["sharpe_por_ano"]})
            _table(L, ["cenário", "Sharpe", "CAGR", "trades", "exposição", "drawdown", "p contra deslocamento"] + [f"Sharpe {y}" for y in years],
                   [[r["cenario"], f"{r['sharpe']:+.2f}", f"{r['cagr']:+.1%}", str(r["trades"]), f"{r['exposicao']:.0%}", f"{r['mdd']:.0%}", f"{r['p_shift']:.3f}"]
                    + [f"{r['sharpe_por_ano'].get(y, float('nan')):+.2f}" for y in years] for r in rows])
            L.append("")
    verdict, checks = confirm_verdict(results[label0])
    L += [f"## Veredito pré-registrado (preço {label0}, sem funding recebido): **{verdict}**", ""] + checks + [""]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "funding_confirmacao.md"), "w") as f:
        f.write("\n".join(L))
    return {"verdict": verdict, "checks": checks, "results": results, "events": ev}


def main(out_dir: str | None = None):
    out_dir = out_dir or os.path.join(ROOT, "research")
    fr = load_funding("BTCUSDT", "binance")["funding_rate"]
    b1h = load_bars("BTCUSDT-BINANCE", "1h", "2019-12-01", "2024-01-15")
    ev = event_study(b1h, fr)
    carry = carry_rules(fr)
    cost = funding_as_cost(fr)
    contr = contrarian_strategy(b1h, fr)
    L = ["# Funding do perpétuo BTCUSDT (Binance, 2020-2023): sinal, carry e custo", "",
         f"Funding médio no período: {fr.mean()*1e4:.2f} bps por 8 h, {fr.mean()*3*365.25:.1%} ao ano. {len(fr)} pagamentos.", "",
         "## 1. Funding como sinal (H016): retorno após funding em percentil extremo (percentil móvel de 90 dias)", "",
         "| bucket | horizonte | retorno médio (bps) | t | n | consistência entre anos |", "|---|---|---|---|---|---|"]
    for r in ev:
        L.append(f"| {r['bucket']} | {r['horizon_h']}h | {r['mean_bps']:+.1f} | {r['t']:+.1f} | {r['n']} | {r['year_consistency']:.0%} |")
    L += ["", "## 2. Carry com regra de percentil (H017): só o funding recebido, 30 bps por entrada e saída, sem P&L da base e sem liquidação", "",
          "| regra | tempo posicionado | entradas | bruto a.a. | líquido a.a. | pior mês | meses negativos |", "|---|---|---|---|---|---|---|"]
    for r in carry:
        L.append(f"| {r['regra']} | {r['tempo_posicionado']:.0%} | {r['entradas']} | {r['bruto_aa']:+.1%} | {r['liquido_aa']:+.1%} | {r['pior_mes']:+.2%} | {r['meses_negativos']} |")
    L += ["", "## 3. Funding como custo (H018): estratégia sempre comprada paga o funding (2020-2023, custos base)", "",
          "| estratégia | exposição média | funding pago a.a. | Sharpe sem | Sharpe com | CAGR sem | CAGR com |", "|---|---|---|---|---|---|---|"]
    for r in cost:
        L.append(f"| {r['estrategia']} | {r['exposicao_media']:.2f} | {r['funding_pago_aa']:.1%} | {r['sharpe_sem_funding']:+.2f} | {r['sharpe_com_funding']:+.2f} | {r['cagr_sem']:+.1%} | {r['cagr_com']:+.1%} |")
    L += ["", "## 4. Estratégia contrária ao funding negativo (H023): comprado 24 h após cada funding abaixo do percentil 10 móvel, abril/2020 a 2023", "",
          "| cenário | Sharpe | CAGR | trades | exposição | drawdown | p contra deslocamento |", "|---|---|---|---|---|---|---|"]
    for r in contr:
        L.append(f"| {r['cenario']} | {r['sharpe']:+.2f} | {r['cagr']:+.1%} | {r['trades']} | {r['exposicao']:.0%} | {r['mdd']:.0%} | {r['p_shift']:.3f} |")
    L.append("")
    with open(os.path.join(out_dir, "funding.md"), "w") as f:
        f.write("\n".join(L))
    return ev, carry, cost


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirm", action="store_true", help="confirmação fora da amostra da H023 com o funding oficial (data/public)")
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default=None, help="padrão: último funding disponível")
    ap.add_argument("--null-sims", type=int, default=200)
    a = ap.parse_args()
    if a.confirm:
        confirm(a.start, a.end, n_null=a.null_sims)
        print(open(os.path.join(ROOT, "research", "funding_confirmacao.md")).read())
    else:
        main()
        print(open(os.path.join(ROOT, "research", "funding.md")).read())

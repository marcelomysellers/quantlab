export type Scenario = "otimista" | "base" | "pessimista";
export type Verdict = "aprovada" | "promissora" | "reprovada" | "referencia";

export interface Metrics {
  n_bars: number; years: number; total_return: number; cagr: number; ann_vol: number; sharpe: number; sortino: number;
  max_drawdown: number; calmar: number; exposure: number; avg_abs_pos: number; turnover_per_year: number; t_stat: number;
  psr: number; skew: number; kurtosis: number; n_days: number; n_trades: number; trades_per_year: number; win_rate: number;
  avg_win: number; avg_loss: number; profit_factor: number; avg_bars_in_trade: number; avg_trade_ret: number;
}

export interface Row {
  id: string; strategy: string; label: string; tf: string; tf_minutes: number; is_benchmark: boolean; verdict: Verdict;
  metrics: Record<Scenario, Metrics>;
  bh: { sharpe: number; cagr: number; max_drawdown: number; total_return: number };
  gross_total: number; cost_total: number; null_p: number; null_mean: number | null; null_p95: number | null;
  dsr: number; n_trials: number; sharpe_ci90: [number, number];
  stress_sharpe_median: number | null; stress_sharpe_p10: number | null;
  fold_returns: number[]; fold_sharpes: number[]; params_by_fold: (Record<string, unknown> | null)[];
  oos_range: [string, string]; spark: number[]; rank: number;
  fold_concentration?: number; oos_return_ex_best_fold?: number; dsr_global?: number; n_trials_global?: number;
}

export interface CurvePoint { t: number; eq: number; bh: number; dd: number; pess: number; opt: number; ov?: number }
export interface Candle { t: number; o: number; h: number; l: number; c: number }
export interface Marker { t: number; side: number; kind: "entry" | "exit"; px: number; size?: number; ret?: number }
export interface Trade { entry: number; exit: number; side: number; size: number; bars: number; entry_px: number; exit_px: number; ret_net: number; open: boolean }
export interface FoldRow { params: Record<string, unknown>; is_sharpe: number; oos_sharpe: number; n_trades_is: number }
export interface Fold {
  k: number; train: [string, string]; test: [string, string]; params: Record<string, unknown> | null;
  is_sharpe: number; oos_sharpe: number; oos_return: number; n_trades_is: number; n_configs: number; table: FoldRow[];
}
export interface Check { id: string; label: string; ok: boolean; value: number }

export interface Detail extends Row {
  description: string; checks: Check[]; curve: CurvePoint[]; candles: Candle[]; markers: Marker[]; pos_win: number[];
  trades: Trade[]; folds: Fold[]; null: { sharpes: number[]; p_value: number; n_sims: number; actual: number };
  stress: { sharpe: number; total_return: number }[]; stress_model: { miss_prob: number; partial_prob: number; partial_min: number };
  best_full_params: Record<string, unknown> | null; grid_size: number; daily: { t: number[]; r: number[] };
}

export interface ScenarioSpec { fee_bps: number; spread_bps: number; slippage_bps: number; impact_k: number; lag_bars: number; round_trip_bps_fixed: number; description: string }
export interface Manifest {
  symbol: string; instrument: string; tfs: string[]; strategies: string[]; start: string; end: string;
  wf: { train_months: number; test_months: number; min_trades: number; warmup_frac: number };
  scenarios: Record<Scenario, ScenarioSpec>; stress_model: { miss_prob: number; partial_prob: number; partial_min: number };
  n_null: number; n_stress: number; generated_at: string; elapsed_s: number;
  strategy_meta: Record<string, { label: string; description: string; is_benchmark: boolean; param_space: Record<string, unknown[]> }>;
}
export interface Duel {
  a: string; b: string; sharpe_a: number; sharpe_b: number; corr: number; combined_sharpe: number; combined_cagr: number;
  combined_mdd: number; folds_won_a: number; folds_won_b: number; n_folds: number;
}

"""
Bayesian optimization with Optuna.
Multi-objective: maximize Sharpe + minimize max drawdown.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import optuna
import pandas as pd
import numpy as np

from signals.four_pillars import compute_signals
from engine.backtester import Backtester


def create_study(symbol: str, cache_dir: str, signal_params: dict,
                 base_params: dict = None, n_trials: int = 500,
                 study_name: str = None) -> optuna.Study:
    """
    Create and run an Optuna study for parameter optimization.

    Multi-objective: maximize Sharpe, minimize max drawdown %.
    """
    if base_params is None:
        base_params = {
            "b_open_fresh": True,
            "commission_rate": 0.0008,
            "notional": 10000.0,
            "rebate_pct": 0.70,
            "settlement_hour_utc": 17,
        }

    # Load and compute signals once
    df_path = Path(cache_dir) / f"{symbol}_1m.parquet"
    df = pd.read_parquet(df_path)
    df = compute_signals(df, signal_params)

    def objective(trial):
        params = dict(base_params)
        params["sl_mult"] = trial.suggest_float("sl_mult", 0.3, 4.0, step=0.1)
        params["tp_mult"] = trial.suggest_float("tp_mult", 0.5, 6.0, step=0.1)
        params["cooldown"] = trial.suggest_int("cooldown", 0, 20)
        params["be_raise_amount"] = trial.suggest_float("be_raise_amount", 0, 50, step=1.0)

        bt = Backtester(params)
        results = bt.run(df)
        m = results["metrics"]

        if m["total_trades"] < 10:
            return -10.0, 100.0  # Penalize low trade count

        return m["sharpe"], m["max_drawdown_pct"]

    if study_name is None:
        study_name = f"four_pillars_{symbol}"

    study = optuna.create_study(
        study_name=study_name,
        directions=["maximize", "minimize"],  # Sharpe up, drawdown down
    )

    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    return study


def study_to_dataframe(study: optuna.Study) -> pd.DataFrame:
    """Convert Optuna study trials to a DataFrame."""
    rows = []
    for trial in study.trials:
        if trial.state == optuna.trial.TrialState.COMPLETE:
            row = dict(trial.params)
            row["sharpe"] = trial.values[0]
            row["max_dd_pct"] = trial.values[1]
            rows.append(row)
    return pd.DataFrame(rows)

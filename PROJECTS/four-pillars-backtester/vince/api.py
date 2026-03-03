"""
Vince v2 — API layer.

All functions callable by:
  - Dash page callbacks (GUI layer)
  - Future agent integrations (same interface, no Dash dependency)

Design rules (locked 2026-02-28):
  - No Dash imports. Pure Python + pandas only.
  - Plugin passed as per-call argument (NOT module-level global).
    Reason: thread-safe for Optuna parallel trials.
  - All functions raise NotImplementedError until implemented in their
    respective build block (B3, B4, B5).
  - Function signatures are FROZEN. Implementations fill in the bodies.

Build map:
  run_enricher          → B3 (vince/enricher.py)
  query_constellation   → B5 (vince/query_engine.py)
  compute_mfe_histogram → B4 (vince/pages/pnl_reversal.py)
  compute_tp_sweep      → B4 (vince/pages/pnl_reversal.py)
  run_backtest          → B5 (vince/optimizer.py)
  get_session_record    → B5 (vince/session_store.py)
  save_session_record   → B5 (vince/session_store.py)
  run_discovery         → B5 (vince/discovery.py)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from strategies.base_v2 import StrategyPlugin
from vince.types import (
    BacktestResult,
    ConstellationFilter,
    ConstellationResult,
    EnrichedTradeSet,
    SessionRecord,
)


# ── B3: Enricher ─────────────────────────────────────────────────────────────

def run_enricher(
    trade_csv: Path,
    symbols: list[str],
    start: str,
    end: str,
    plugin: StrategyPlugin,
) -> EnrichedTradeSet:
    """Attach indicator snapshots to every trade in trade_csv.

    For each trade, captures three indicator state vectors:
      - Entry bar snapshot
      - MFE bar snapshot (bar where maximum favorable excursion occurred)
      - Exit bar snapshot

    Also stores OHLC tuples at entry, MFE, and exit bars as 12 float columns.
    Uses diskcache (FanoutCache) keyed on symbol + params_hash + parquet mtime.
    No trade is ever skipped — volume is always preserved.

    Args:
        trade_csv: Path to trade CSV produced by plugin.run_backtest().
                   Must contain all columns from plugin.trade_schema().
        symbols:   List of symbols to enrich. Must match CSV content.
        start:     ISO 8601 date string "YYYY-MM-DD". Inclusive.
        end:       ISO 8601 date string "YYYY-MM-DD". Inclusive.
        plugin:    StrategyPlugin instance. Used to call compute_signals()
                   on OHLCV data to get indicator values at each bar.

    Returns:
        EnrichedTradeSet with all snapshot columns attached.

    Raises:
        FileNotFoundError: if trade_csv or any symbol parquet is missing.
        ValueError: if trade_csv is missing required schema columns.
    """
    raise NotImplementedError("run_enricher — implemented in B3 (vince/enricher.py)")


# ── B4: PnL Reversal Analysis ─────────────────────────────────────────────────

def compute_mfe_histogram(
    trade_set: EnrichedTradeSet,
    f: Optional[ConstellationFilter] = None,
    bins: Optional[list[float]] = None,
) -> pd.DataFrame:
    """Compute MFE distribution histogram across all trades (or filtered subset).

    Default bins (9 ATR breakpoints, from B4 spec):
      [0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, inf]

    Args:
        trade_set: EnrichedTradeSet (must contain life_mfe column).
        f:         Optional ConstellationFilter to pre-filter trades.
        bins:      Custom ATR bin edges. If None, uses 9-bin default.

    Returns:
        DataFrame with columns: bin_label, count, pct, win_rate, avg_net_pnl.
    """
    raise NotImplementedError("compute_mfe_histogram — implemented in B4 (vince/pages/pnl_reversal.py)")


def compute_tp_sweep(
    trade_set: EnrichedTradeSet,
    f: Optional[ConstellationFilter] = None,
    tp_range: tuple[float, float] = (0.5, 5.0),
    steps: int = 19,
) -> pd.DataFrame:
    """Simulate TP sweep: net PnL if a fixed TP had been set at each multiple.

    For each tp_mult in the range:
      - If trade MFE >= tp_mult: simulate TP hit at entry_price +/- atr * tp_mult.
      - Otherwise: use actual exit price.
      - Subtract commission on simulated exit.
      - Constraint: trade_count must remain >= 95% of full set.

    Args:
        trade_set: EnrichedTradeSet (must contain life_mfe, entry_atr columns).
        f:         Optional ConstellationFilter to pre-filter trades before sweep.
        tp_range:  (low, high) ATR multiple range for TP sweep.
        steps:     Number of evenly-spaced TP multiples to evaluate.

    Returns:
        DataFrame with columns: tp_mult, net_pnl, win_rate, trade_count,
                                 avg_mfe_atr, pct_would_hit_tp.
        Two curves: gross_pnl and net_pnl (commission-adjusted) — both included.
    """
    raise NotImplementedError("compute_tp_sweep — implemented in B4 (vince/pages/pnl_reversal.py)")


# ── B5: Query Engine ──────────────────────────────────────────────────────────

def query_constellation(
    trade_set: EnrichedTradeSet,
    f: ConstellationFilter,
    run_permutation_test: bool = False,
    permutation_n: int = 1000,
) -> ConstellationResult:
    """Filter trades by ConstellationFilter; compute full metric table.

    Metrics computed for both matched and complement subsets:
      win_rate, profit_factor, avg_net_pnl, avg_mfe_atr, avg_mae_atr,
      pnl_reversal_rate (LSG%), mfe_mae_ratio, trade_count.

    delta = matched_metric - complement_metric for each row.

    permutation test (optional, expensive):
      Shuffle trade outcome labels N times, recompute delta each time.
      p_value = fraction of shuffles where permuted_delta >= real_delta.

    Args:
        trade_set:            EnrichedTradeSet to query.
        f:                    ConstellationFilter defining the constellation.
        run_permutation_test: If True, run N-shuffle permutation significance test.
        permutation_n:        Number of label-shuffle iterations.

    Returns:
        ConstellationResult with matched/complement counts, metric table,
        and permutation p-value (None if test not run).

    Raises:
        ValueError: if matched_count < 30 (too small for reliable statistics).
    """
    raise NotImplementedError("query_constellation — implemented in B5 (vince/query_engine.py)")


def run_backtest(
    plugin: StrategyPlugin,
    params: dict,
    start: str,
    end: str,
    symbols: list[str],
) -> BacktestResult:
    """Run a single backtest trial via plugin.run_backtest(); return summary metrics.

    Wraps plugin.run_backtest() output into BacktestResult with computed
    summary metrics (calmar, profit_factor, win_rate, etc.).

    Used by:
      - Optimizer (Mode 3) — one call per Optuna trial
      - Validation panel (B6) — one call per validation run

    Args:
        plugin:  StrategyPlugin instance. run_backtest() must be deterministic.
        params:  Parameter dict matching plugin.parameter_space() keys.
        start:   ISO 8601 date string "YYYY-MM-DD".
        end:     ISO 8601 date string "YYYY-MM-DD".
        symbols: List of ticker strings with parquet data available.

    Returns:
        BacktestResult with summary metrics.

    Raises:
        RuntimeError: if backtest produces zero trades (degenerate trial).
    """
    raise NotImplementedError("run_backtest — implemented in B5 (vince/optimizer.py)")


def get_session_record(session_id: str) -> SessionRecord:
    """Retrieve a named research session by ID.

    Args:
        session_id: UUID hex string assigned at session creation.

    Returns:
        SessionRecord.

    Raises:
        KeyError: if session_id not found in session store.
    """
    raise NotImplementedError("get_session_record — implemented in B5 (vince/session_store.py)")


def save_session_record(record: SessionRecord) -> None:
    """Persist a SessionRecord to the session store.

    Updates record.updated_at to current UTC time before saving.
    Creates new record if session_id not found; updates existing if found.

    Args:
        record: SessionRecord to persist.
    """
    raise NotImplementedError("save_session_record — implemented in B5 (vince/session_store.py)")


def run_discovery(
    trade_set: EnrichedTradeSet,
    effect_size_threshold: float,
    min_n: int,
    n_draws: int = 10,
    permutation_n: int = 1000,
) -> list[ConstellationResult]:
    """Mode 2 — Auto-discovery of significant constellation patterns.

    Pre-steps:
      1. XGBoost feature importance on trade_set (label = win/loss).
         Ranks indicator dimensions by predictive signal.
      2. k-means clustering on entry-state feature vectors.
         Each cluster = naturally occurring constellation type.

    Main sweep:
      Evaluates N-dimensional indicator constellations on discovery partition (80%).
      Significance gate: permutation baseline to establish null distribution.
      Only surfaces patterns where real delta > 95th percentile of permuted deltas.

    Random sampling (K draws):
      Runs on K independent random draws (random time window + random coin subset).
      Pattern surfaced only if consistent across >= M of K draws.

    Args:
        trade_set:              EnrichedTradeSet (full dataset, not pre-filtered).
        effect_size_threshold:  Minimum delta to consider for surfacing.
        min_n:                  Minimum matched_count to surface a pattern.
        n_draws:                Number of random dataset draws for robustness check.
        permutation_n:          Shuffles per significance test.

    Returns:
        List of ConstellationResult, sorted by permutation_p_value ascending.
        Only patterns meeting effect_size_threshold, min_n, and significance gate.
    """
    raise NotImplementedError("run_discovery — implemented in B5 (vince/discovery.py)")

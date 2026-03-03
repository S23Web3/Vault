"""
Vince v2 — Shared dataclasses.

All types used by the API layer, enricher, query engine, optimizer, and Dash pages.
No Dash imports here. Pure Python + pandas only.

Design verdicts (locked 2026-02-28 — see BUILD-VINCE-B2-API.md):
  - EnrichedTradeSet.trades is pd.DataFrame (not dataclass list) — vectorised at scale.
  - ConstellationFilter uses typed base fields + column_filters dict for plugin-agnostic
    indicator filtering that is also JSON-serialisable for dcc.Store.
  - SessionRecord represents a named research session, not a per-run log.
  - Plugin is passed per-call (not global) for Optuna thread-safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd


# ── Indicator snapshot at a single bar ───────────────────────────────────────

@dataclass
class IndicatorSnapshot:
    """Indicator state captured at one bar (entry, MFE, or exit).

    Column naming convention: {indicator}_{period}_at_{event}.
    Example: k1_9_at_entry, k3_40_at_mfe, cloud3_bull_at_exit.
    Populated by the Enricher (B3) via plugin.compute_signals().
    """

    k1: float          # stoch_9  — fast stochastic (9-period Raw K)
    k2: float          # stoch_14 — confirmation stochastic
    k3: float          # stoch_40 — medium stochastic
    k4: float          # stoch_60 — macro stochastic
    cloud_bull: bool   # cloud3_bull — True if Cloud 3 is bullish at this bar
    bbw: Optional[float]  # bbwp_value — BBW percentile rank; None if BBW not wired
    bar_idx: int       # absolute bar index into OHLCV DataFrame (RangeIndex)


# ── OHLC at a single bar ─────────────────────────────────────────────────────

@dataclass
class OHLCRow:
    """OHLC tuple at a single bar.

    Stored as 4 separate float columns in the trade DataFrame (not as JSON).
    Reason: 12 float columns avoids per-row json.loads() at scale.
    Fields: entry_open/high/low/close, mfe_open/high/low/close,
            exit_open/high/low/close — added by Enricher (B3).
    """

    open: float
    high: float
    low: float
    close: float


# ── Enriched trade set ───────────────────────────────────────────────────────

@dataclass
class EnrichedTradeSet:
    """Collection of enriched trades as a single DataFrame.

    trades: pd.DataFrame with all enriched columns:
      - Required trade columns (from plugin.trade_schema()):
          entry_bar, exit_bar, pnl, commission, direction, symbol
      - Enricher-added indicator snapshot columns:
          k1_9_at_entry, k3_40_at_mfe, cloud3_bull_at_exit, etc.
      - Enricher-added OHLC columns:
          entry_open, entry_high, entry_low, entry_close,
          mfe_open, mfe_high, mfe_low, mfe_close,
          exit_open, exit_high, exit_low, exit_close
      - v385 post-processing columns (if backtester_v385 used):
          life_mfe, life_mae, life_duration_bars, life_pnl_path,
          lsg_category, grade, entry_atr, etc.
    """

    trades: pd.DataFrame
    session_id: str
    plugin_name: str
    symbols: list[str]
    date_range: tuple[str, str]  # (start_iso, end_iso) — YYYY-MM-DD strings
    enriched_at: str             # ISO 8601 UTC timestamp


# ── Metric row ───────────────────────────────────────────────────────────────

@dataclass
class MetricRow:
    """One metric comparing matched vs complement trade subsets.

    delta = matched - complement. Positive = matched subset outperforms.
    Shown in Constellation Query results (Panel 3) and auto-discovery (Mode 2).
    """

    label: str          # e.g. "Win Rate", "Profit Factor", "Avg MFE (ATR)"
    matched: float      # metric value for trades matching the filter
    complement: float   # metric value for trades NOT matching the filter
    delta: float        # matched - complement


# ── Constellation filter ─────────────────────────────────────────────────────

@dataclass
class ConstellationFilter:
    """Filter for constellation queries. Fully plugin-agnostic.

    Typed base fields handle universal dimensions (direction, outcome, etc.).
    Plugin-specific indicator dimensions go in column_filters as a dict
    mapping column name (from plugin.compute_signals() output) to filter value.

    column_filters examples (Four Pillars):
      {"k1_9_at_entry": {"gte": 20, "lte": 40}}  — K1 in oversold zone at entry
      {"cloud3_bull_at_entry": True}               — Cloud 3 was bullish at entry
      {"grade": "A"}                               — Grade A trades only

    JSON-serialisable: safe for dcc.Store persistence across Dash callbacks.
    """

    direction: Optional[str] = None          # "LONG", "SHORT", or None (both)
    outcome: Optional[str] = None            # "win", "loss", "lsg", or None (all)
    min_mfe_atr: Optional[float] = None      # minimum MFE in ATR units
    saw_green: Optional[bool] = None         # True = trade reached positive PnL at some point
    column_filters: dict[str, Any] = field(default_factory=dict)


# ── Constellation result ─────────────────────────────────────────────────────

@dataclass
class ConstellationResult:
    """Result of a constellation query (Mode 1 or Mode 2).

    matched_count + complement_count = total trade count in the EnrichedTradeSet.
    permutation_p_value: empirical p-value from label-shuffle permutation test.
    None if permutation test was not run (user-triggered, computationally expensive).
    """

    matched_count: int
    complement_count: int
    metrics: list[MetricRow]
    permutation_p_value: Optional[float]


# ── Session record ───────────────────────────────────────────────────────────

@dataclass
class SessionRecord:
    """Named research session grouping multiple queries.

    A session is NOT a per-enricher-run log. It is a named unit of research
    work (e.g. "March 2026 — Grade A LONG investigation") that groups
    multiple constellation queries, TP sweeps, and discovery runs.

    last_filter: JSON dict of the most recent ConstellationFilter used.
    Persisted to allow session resumption without re-running the enricher.
    """

    session_id: str                    # uuid4 hex, immutable after creation
    name: str                          # user-editable display name
    created_at: str                    # ISO 8601 UTC
    updated_at: str                    # ISO 8601 UTC — updated on every save
    plugin_name: str                   # e.g. "FourPillarsPlugin"
    symbols: list[str]                 # coin list used for this session
    date_range: tuple[str, str]        # (start_iso, end_iso)
    notes: str                         # free-text user notes
    last_filter: Optional[dict]        # JSON-serialisable ConstellationFilter


# ── Backtest result ──────────────────────────────────────────────────────────

@dataclass
class BacktestResult:
    """Result of a single backtest trial.

    Used by the optimizer (Mode 3) to compare Optuna trial outcomes.
    calmar: net_pnl_with_rebate / max_drawdown_dollars (fitness function).
    trade_count enforced >= 95% of baseline to prevent degeneracy.
    """

    params: dict
    trade_csv: Path
    start: str
    end: str
    symbols: list[str]
    trade_count: int
    gross_pnl: float
    net_pnl: float           # gross_pnl - commissions + rebate_income
    max_drawdown: float      # in USD
    profit_factor: float
    win_rate: float
    calmar: float            # net_pnl / max_drawdown (fitness score)

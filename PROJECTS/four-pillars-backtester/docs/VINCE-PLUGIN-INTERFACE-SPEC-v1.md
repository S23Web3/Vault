## Implementation Status (updated 2026-02-28)

| Component | File | Status |
|-----------|------|--------|
| StrategyPlugin ABC | `strategies/base_v2.py` | DONE — py_compile pass |
| FourPillarsPlugin | `strategies/four_pillars_plugin.py` | READY TO BUILD — see `BUILD-VINCE-B1-PLUGIN.md` |
| Enricher (uses compute_signals) | `vince/enricher.py` | BLOCKED — see `BUILD-VINCE-B3-ENRICHER.md` |
| Compliance checker CLI | `vince/compliance_check.py` | PLANNED — B3 improvement item |

Spec sections below are LOCKED. No further changes to spec content.

---

# Vince Plugin Interface Spec — v1

**Status:** SPEC v1 — formal interface definition, not yet approved for build
**Date:** 2026-02-27
**Related:** `VINCE-V2-CONCEPT-v2.md`, P1.7 in PRODUCT-BACKLOG.md
**Implementation file:** `strategies/base_v2.py` (Python stub, same date)

---

## 1. Purpose

This document formalizes the `StrategyPlugin` abstract base class that every strategy must
implement to work with Vince. It is the contract between strategy logic and Vince's analysis
infrastructure.

Before this spec existed, the interface was described informally in the concept doc. This
spec replaces informal description with unambiguous contracts so that:

1. The FourPillarsPlugin can be built without guessing at requirements
2. Any future strategy (WEEX screener plugin, Vicky plugin, etc.) has a clear target
3. The Enricher, Optimizer, and Validator can be built against stable method signatures
4. Compliance can be tested — a plugin either satisfies the contract or it does not

The spec does NOT define strategy logic. It defines the interface boundary only.

---

## 2. Abstract Base Class

Full class definition. The Python implementation lives in `strategies/base_v2.py`.

```python
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd


class StrategyPlugin(ABC):
    """Abstract base for all Vince-compatible strategy plugins.

    A strategy plugin is the bridge between a specific trading strategy and Vince's
    analysis infrastructure. It exposes five methods and one property. Vince never
    reads strategy internals directly — all access goes through this interface.

    Implementing this interface makes any strategy fully compatible with:
    - Vince Enricher (compute_signals)
    - Vince Optimizer and Validator (run_backtest, parameter_space)
    - Vince Analyzer (trade_schema)
    - Vince LLM Interpretive Layer (strategy_document)
    """

    @abstractmethod
    def compute_signals(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Attach all indicator signals to OHLCV data.

        Called by the Enricher for every symbol in the active coin set.
        Returns the input DataFrame with additional indicator columns attached.
        The original columns must be preserved unchanged.

        Args:
            ohlcv_df: OHLCV DataFrame. See Section 4 (OHLCV Contract) for required
                      columns, dtypes, and index requirements.

        Returns:
            DataFrame with all original columns plus indicator columns.
            See Section 5 (Enricher Contract) for naming conventions.

        Raises:
            ValueError: if ohlcv_df is missing required columns.
            ValueError: if ohlcv_df has fewer rows than the longest indicator lookback.
        """
        raise NotImplementedError

    @abstractmethod
    def parameter_space(self) -> dict:
        """Return the sweepable parameter names with bounds and types.

        Used by the Vince Optimizer (Mode 3) to define the search space for Optuna.
        Keys are parameter names. Values are dicts with 'type' and optional bounds.

        Returns:
            dict mapping parameter name (str) to parameter spec (dict).

        Parameter spec schema:
            {
                "type":  "float" | "int" | "bool",  # required
                "low":   number,                     # required for float and int
                "high":  number,                     # required for float and int
                "log":   bool,                       # optional, default False
                                                     # if True, Optuna samples log-uniformly
            }

        Example return:
            {
                "tp_mult":     {"type": "float", "low": 0.5,  "high": 5.0},
                "sl_mult":     {"type": "float", "low": 0.5,  "high": 3.0},
                "cross_level": {"type": "int",   "low": 20,   "high": 80},
                "allow_b":     {"type": "bool"},
                "allow_c":     {"type": "bool"},
            }

        Raises:
            Nothing. Must not raise. Return empty dict if no parameters are sweepable.
        """
        raise NotImplementedError

    @abstractmethod
    def trade_schema(self) -> dict:
        """Return column definitions for the trade CSV this plugin produces.

        Used by the Enricher to validate trade CSV columns before enrichment.
        Defines backtester output columns only — NOT indicator snapshot columns.
        Indicator snapshots are attached by the Enricher via compute_signals().

        Returns:
            dict mapping column name (str) to description string.

        Required columns (every plugin must include these):
            "entry_bar":  "int   — bar index of entry (matches OHLCV index)"
            "exit_bar":   "int   — bar index of exit (matches OHLCV index)"
            "pnl":        "float — gross PnL in USD (before commission)"
            "commission": "float — total round-trip commission in USD"
            "direction":  "str   — LONG or SHORT"
            "symbol":     "str   — ticker symbol (e.g. BTCUSDT)"

        Optional strategy-specific columns (examples for Four Pillars):
            "grade":      "str   — entry grade (A/B/C/D/R)"
            "entry_type": "str   — fresh/ADD/RE"
            "mfe_atr":    "float — maximum favorable excursion in ATR units"
            "mae_atr":    "float — maximum adverse excursion in ATR units"

        Raises:
            Nothing. Must not raise.
        """
        raise NotImplementedError

    @abstractmethod
    def run_backtest(
        self,
        params: dict,
        start: str,
        end: str,
        symbols: list,
    ) -> Path:
        """Run backtest with the given parameters and return path to the trade CSV.

        Called by the Vince Optimizer (Mode 3) for each Optuna trial. Must be a
        pure function with respect to its inputs — the same params/start/end/symbols
        must always produce the same trade CSV (deterministic).

        Args:
            params: dict of parameter values matching keys from parameter_space().
                    All keys from parameter_space() will be present. No extra keys.
            start:  ISO 8601 date string, e.g. "2024-01-01". Inclusive.
            end:    ISO 8601 date string, e.g. "2024-03-31". Inclusive.
            symbols: list of ticker strings, e.g. ["BTCUSDT", "ETHUSDT"].
                     Subset of the coins available in the local parquet data.

        Returns:
            pathlib.Path to the trade CSV file. File must exist and be readable.
            CSV must contain all columns declared in trade_schema().

        Raises:
            FileNotFoundError: if parquet data for any symbol in symbols is missing.
            ValueError: if start >= end or date format is invalid.
            RuntimeError: for any other internal backtest failure.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def strategy_document(self) -> Path:
        """Path to the strategy markdown document.

        Used by the Vince LLM Interpretive Layer (Panel 8) to ground its analysis
        in strategy logic. The LLM reads this document alongside quantitative results
        to generate strategy-specific hypotheses.

        Returns:
            pathlib.Path to a markdown (.md) file. File must exist and be readable.

        Format requirements:
            - Markdown only. PDF, DOCX, or other formats are NOT accepted.
            - If your strategy document is not markdown, convert it first and
              confirm with the user before registering it here.
            - Minimum content: strategy name, entry rules, exit rules, indicator list.

        Raises:
            FileNotFoundError: if the document file does not exist.
        """
        raise NotImplementedError
```

---

## 3. Method Contracts

### 3a. compute_signals(ohlcv_df)

**Input:** OHLCV DataFrame satisfying Section 4 contract.

**Output guarantees:**
- All input columns preserved unchanged (no modification of open/high/low/close/volume)
- New indicator columns appended to the right
- No NaN in the first `max_lookback` rows is acceptable, but rows with NaN beyond the
  lookback period are NOT acceptable — fill or backfill as needed
- Column naming convention: `{indicator}_{period}` where applicable (e.g. `k1_9`, `cloud3_bull`)
- Boolean columns use `bool` dtype (not int 0/1)
- Float columns use `float64` dtype

**Performance requirement:** Must complete in under 5 seconds per 100k rows on the reference
hardware (AMD Ryzen 7 5800X). The Enricher calls this once per symbol — not once per trade.

**Side effects:** None. Must not write files, log to disk, or modify global state.

---

### 3b. parameter_space()

**Schema validation (Vince will enforce at load time):**

| Field | Required for | Type | Constraint |
|-------|-------------|------|------------|
| `type` | all | str | must be `"float"`, `"int"`, or `"bool"` |
| `low` | float, int | number | must be < `high` |
| `high` | float, int | number | must be > `low` |
| `log` | float, int | bool | optional, default False |

Bool parameters have no `low`/`high`. Vince maps them to Optuna `suggest_categorical([True, False])`.

**Empty dict is valid** — strategy has no sweepable parameters.

**Keys must be stable** — the same parameter name must map to the same thing across calls.
The Optimizer stores parameter names in the database. Renaming a parameter invalidates
historical trial data.

---

### 3c. trade_schema()

**Required columns (non-negotiable):**

| Column | dtype | Description |
|--------|-------|-------------|
| `entry_bar` | int | Bar index matching OHLCV DataFrame index |
| `exit_bar` | int | Bar index matching OHLCV DataFrame index |
| `pnl` | float | Gross PnL in USD (before commission) |
| `commission` | float | Total round-trip commission in USD |
| `direction` | str | "LONG" or "SHORT" exactly |
| `symbol` | str | Ticker symbol matching the parquet file key |

**Bar index alignment:** `entry_bar` and `exit_bar` must be integer positional indices into the
OHLCV DataFrame for that symbol — the same index used by `compute_signals()`. The Enricher
uses these to look up indicator state at the critical bars. If the bar index is a datetime
index or a non-integer key, the Enricher cannot align trades to indicator snapshots.

**Indicator columns do NOT belong here.** `k1_at_entry`, `k2_at_entry`, etc. are NOT part of
the trade CSV. They are computed and attached by the Enricher from `compute_signals()` output.

---

### 3d. run_backtest(params, start, end, symbols)

**Date format:** `"YYYY-MM-DD"` only. Vince parses with `datetime.strptime(date, "%Y-%m-%d")`.

**Determinism requirement:** Given the same inputs, the output trade CSV must be byte-for-byte
identical across calls. Random seeds must be fixed. This is required for the Optimizer's
session-resume functionality.

**Trade CSV path:** The returned Path should be inside the project's `results/` directory.
Naming convention: `trades_{symbol_list_hash}_{start}_{end}.csv`. The hash prevents collisions
when multiple optimizer trials run concurrently.

**Concurrent safety:** The Optimizer may call `run_backtest()` from multiple threads (Optuna
parallelism). The implementation must be thread-safe. Do NOT write to shared state.

---

### 3e. strategy_document property

**Lazy loading is acceptable.** The property does not need to verify the file exists until
it is accessed. But when accessed, `FileNotFoundError` must be raised if the file is missing
(not silently return None or a placeholder path).

**Content requirements (enforced by convention, not code):**

The LLM uses this document to interpret quantitative findings. The more complete the document,
the higher the quality of LLM interpretation. Minimum viable content:
- Strategy name and version
- Entry conditions (all rules, all grades if applicable)
- Exit conditions (SL, TP, BE logic)
- Indicator list with periods and smoothing settings
- Any known edge cases or known-bad conditions

---

## 4. OHLCV DataFrame Contract

Every DataFrame passed to `compute_signals()` must satisfy this contract.

### Required columns

| Column | dtype | Description |
|--------|-------|-------------|
| `open` | float64 | Bar open price |
| `high` | float64 | Bar high price |
| `low` | float64 | Bar low price |
| `close` | float64 | Bar close price |
| `volume` | float64 | Bar volume (base asset) |

### Index

- Type: `pd.RangeIndex` (integer, 0-based)
- The Enricher uses positional indexing to look up bars by `entry_bar` / `exit_bar` values
- DatetimeIndex is NOT supported — convert before passing to `compute_signals()`
- A `timestamp` column (UTC, int64 Unix milliseconds) should be present but is NOT the index

### Timezone

All timestamps are UTC. No timezone conversion inside the plugin. The data normalizer
(`data/normalizer.py`) produces UTC-aligned parquets.

### Minimum rows

The DataFrame must have at least `max_lookback + 1` rows where `max_lookback` is the
longest indicator period used by the plugin (e.g. 60 bars for K4 stochastic on the Four
Pillars plugin). Behavior with fewer rows is undefined.

---

## 5. Enricher Contract

The Enricher calls `compute_signals()` and expects indicator columns to follow this naming
convention so it can build indicator snapshots at entry/MFE/exit bars.

### Indicator column naming convention

```
{indicator_name}_{period}
```

Examples (Four Pillars plugin):

| Column name | Description |
|-------------|-------------|
| `k1_9` | K1 stochastic (9-period Raw K) |
| `k2_14` | K2 stochastic (14-period Raw K) |
| `k3_40` | K3 stochastic (40-period Raw K) |
| `k4_60` | K4 stochastic (60-period Raw K) |
| `cloud2_bull` | Cloud 2 (5/12 EMA) bullish bool |
| `cloud3_bull` | Cloud 3 (34/50 EMA) bullish bool |
| `bbw` | Bollinger Band Width |
| `atr` | Average True Range |

### Snapshot columns (added by Enricher, not plugin)

After `compute_signals()` runs, the Enricher attaches these to each enriched trade:

```
{column_name}_at_entry    # value at entry_bar
{column_name}_at_mfe      # value at MFE bar
{column_name}_at_exit     # value at exit_bar
```

Example: `k1_9_at_entry`, `cloud3_bull_at_mfe`, `bbw_at_exit`

The Enricher also attaches OHLC tuples at critical bars (added 2026-02-27):
```
entry_ohlc    # (open, high, low, close) tuple at entry_bar
mfe_ohlc      # (open, high, low, close) tuple at MFE bar
exit_ohlc     # (open, high, low, close) tuple at exit_bar
```

These enable intra-candle event classification in Exit State Analysis (Panel 4):
whether the SL was hit at the high/low (intra-candle) vs at the close of a bar.

---

## 6. Compliance Checklist

A plugin is Vince-compatible when all of the following pass:

### Interface compliance
- [ ] Inherits from `StrategyPlugin` (from `strategies/base_v2.py`)
- [ ] All 5 abstract methods implemented (no `NotImplementedError` remaining)
- [ ] `strategy_document` property returns a valid `Path` to a `.md` file

### compute_signals compliance
- [ ] Returns DataFrame with all input columns preserved
- [ ] All indicator columns present and correctly named
- [ ] No NaN in indicator columns beyond the lookback period
- [ ] Deterministic: same input always produces same output
- [ ] Does not write files or mutate global state

### parameter_space compliance
- [ ] All entries have valid `type` field (`"float"`, `"int"`, or `"bool"`)
- [ ] Float and int entries have `low < high`
- [ ] Returns empty dict (not None) if no parameters are sweepable

### trade_schema compliance
- [ ] All 6 required columns declared
- [ ] `entry_bar` and `exit_bar` are positional integer indices (not datetime)
- [ ] `direction` values are exactly `"LONG"` or `"SHORT"` (no aliases)

### run_backtest compliance
- [ ] Returns a valid `Path` to a readable CSV file
- [ ] CSV contains all columns declared in `trade_schema()`
- [ ] `entry_bar` values are valid positional indices into the OHLCV data
- [ ] Raises `FileNotFoundError` for missing symbol parquets
- [ ] Raises `ValueError` for invalid date range
- [ ] Thread-safe (no shared mutable state)
- [ ] Deterministic given the same inputs

---

## 7. FourPillarsPlugin — Compliance Mapping

How the existing Four Pillars signal pipeline maps to each method.

| Method | Existing implementation | Status |
|--------|------------------------|--------|
| `compute_signals()` | `signals/four_pillars_v383_v2.py` → `compute_signals_v383()` | Needs wrapper — current signature differs (takes params dict, not just ohlcv_df) |
| `parameter_space()` | Hardcoded in `engine/backtester_v384.py` as DEFAULT_PARAMS | Needs extraction into method |
| `trade_schema()` | `engine/position_v384.py` → `Trade384` dataclass fields | Needs serialization — map dataclass fields to schema dict |
| `run_backtest()` | `engine/backtester_v384.py` → `Backtester384.run()` | Needs wrapper — current API doesn't take start/end/symbols in one call |
| `strategy_document` | `SPEC-C-VINCE-ML.md` or `BUILD-VINCE-ML.md` | Needs to be pointed at the correct strategy markdown |

**Key issue — bar index alignment:**
`Trade384` currently stores entry/exit as bar offsets within a single symbol's run, not as
positional indices into the global OHLCV parquet. The wrapper must translate these to
absolute positional indices that the Enricher can use to look up indicator state.

**This mapping is the primary build task for the FourPillarsPlugin.**
Once the wrapper is built and compliance checklist passes, the Enricher can begin enriching
Four Pillars trade data and Vince v1 analysis can start.

---

*This document is a spec. No code is written from it until the concept doc is approved for build.*

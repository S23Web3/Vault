# Plan: TDI (Traders Dynamic Index) Python Module

## Context
User wants a reusable TDI calculation module for their backtester strategies, inspired by two TradingView indicators:
1. **CW_Trades TDI** (closed-source) — multi-color RSI line with momentum zones
2. **TDI + RSI Div** (user has source) — RSI divergence detection

The CW_Trades indicator is protected/closed-source, but TDI math is public domain. We replicate all features as a standalone Python module that can later be converted to a Pine Script indicator.

No TDI implementation exists in the codebase. The `signals/` directory has established patterns (stochastics.py, clouds.py, bbwp.py) we follow exactly.

## Target File
- **Create**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\tdi.py` (~250 lines)
- **Create**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_tdi.py` (build script with py_compile + validation)

## Design

### API
```python
def compute_tdi(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute TDI with zones, divergences, and cross signals. Standalone module."""
```
Standalone — NOT wired into `four_pillars.py` or `indicators.py`. User calls it separately.

### Two Presets
| Setting | CW_Trades | Classic (Dean Malone) |
|---------|-----------|----------------------|
| RSI period | 13 | 14 |
| Signal MA | 8 | 7 |
| BB period | 34 | 20 |
| BB std dev | 1.6185 | 2.0 |

Select via `params={'tdi_preset': 'cw_trades'}` or `'classic'`. Individual params override preset values.

### Output Columns (15 total, all prefixed `tdi_`)

**Core lines (5):**
- `tdi_rsi` — RSI value (Wilder's smoothing)
- `tdi_signal` — SMA of RSI (trade signal line)
- `tdi_bb_upper`, `tdi_bb_mid`, `tdi_bb_lower` — Bollinger Bands on RSI

**Multi-color zones (2):**
- `tdi_zone` — string enum: EXTREME_BULL, STRONG_BULL, BULL, WEAK_BULL, NEUTRAL, WEAK_BEAR, BEAR, STRONG_BEAR, EXTREME_BEAR, BB_UPPER_BREACH, BB_LOWER_BREACH
- `tdi_color` — hex color string for charting (BB breach colors override RSI zones)

**Divergence (2):**
- `tdi_bull_div` — boolean, pivot-based bullish divergence (price lower low + RSI higher low)
- `tdi_bear_div` — boolean, pivot-based bearish divergence (price higher high + RSI lower high)

**Cross signals (6):**
- `tdi_rsi_cross_signal_up` / `_down` — RSI crosses signal line
- `tdi_rsi_cross_bb_upper` — RSI crosses above BB upper
- `tdi_rsi_cross_bb_lower` — RSI crosses below BB lower
- `tdi_rsi_cross_50_up` / `_down` — RSI crosses 50 midline

### Module Structure
```
tdi.py
  PRESETS dict (cw_trades, classic)
  DEFAULT_PARAMS dict
  ZONE_THRESHOLDS + COLOR_MAP constants
  _rsi_wilder(close, period)          # Copy from ema_cross_55_89.py:56-78 (standalone, no import coupling)
  _sma(series, window)                # pandas rolling
  _bb_on_rsi(rsi, period, std_dev)    # SMA + rolling std (ddof=0 to match Pine)
  _classify_zones(rsi, bb_upper, bb_lower)  # Vectorized via np.select
  _detect_pivots(series, lookback)    # Confirmed swing highs/lows
  _detect_divergences(close, rsi, pivot_lookback)  # Pivot comparison
  _cross(a, b)                        # Vectorized crossover detection
  compute_tdi(df, params)             # Orchestrator
```

### Key Implementation Details
1. **RSI**: Wilder's smoothing (matches Pine `ta.rsi()`). Private copy from `ema_cross_55_89.py:56-78` — no import coupling.
2. **BB std**: `ddof=0` (population std) to match Pine Script `ta.stdev()`.
3. **Zone priority**: BB breach (yellow/red) overrides RSI-value-based zones.
4. **Divergence**: Confirmed pivots only (non-repainting). Pivot lookback default = 5 bars. Signal fires `lookback` bars after actual pivot.
5. **Warmup**: First valid bar = `rsi_period + max(bb_period, signal_ma_len)`. All columns NaN/False during warmup.
6. **No Numba**: Pure numpy/pandas. RSI loop is O(n), fast enough without JIT.
7. **No name collision**: Existing `compute_tdi` in `ema_cross_55_89.py` is a different function in a different module. New one is `signals.tdi.compute_tdi`.

### Reference Files
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89.py` — `compute_rsi` (lines 56-78) to copy as `_rsi_wilder`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbwp.py` — Pattern for DEFAULT_PARAMS, param merging, module structure
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\clouds.py` — Pattern for crossover detection
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\stochastics.py` — Pattern for numpy-based computation

## Build Steps
1. Load Python skill (`/python`)
2. Write build script that creates `signals/tdi.py` (~250 lines)
3. Build script runs `py_compile` on the output
4. Write test script `scripts/test_tdi.py` — synthetic OHLCV data, validate: column count (15), NaN warmup, cross detection on known crossover, zone classification, divergence on synthetic divergent data
5. User runs test script from terminal

## Verification
1. `py_compile` passes on `tdi.py`
2. `test_tdi.py` validates:
   - 15 new columns added to DataFrame
   - NaN in warmup period, valid values after
   - Known RSI value on synthetic data matches manual calc
   - Cross signals fire at correct bars on synthetic crossover
   - Zone classification matches expected zone for given RSI value
   - Divergence detection fires on synthetic divergent price/RSI pattern
3. Manual: `from signals.tdi import compute_tdi; df = compute_tdi(ohlcv_df); print(df[['tdi_rsi','tdi_zone','tdi_color']].tail(20))`

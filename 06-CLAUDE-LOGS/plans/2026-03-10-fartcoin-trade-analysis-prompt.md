# Claude Agent Prompt: Deep Trade Analysis — Negative Coins + FARTCOINUSDT

**Date:** 2026-03-10
**Executor:** Claude agent (autonomous)
**Context:** 55/89 EMA Cross Scalp strategy. Portfolio backtest on 9 coins (2025-11-07 date range) produced -$3,480.81 net. FARTCOINUSDT was the worst performer: 243 trades, 30% WR, -$8,499.35, 333.1% max DD. This prompt drives a per-trade deep analysis of negative coins — especially FARTCOIN — vetting every trade against the core strategy logic.

---

## Objective

Build and run a Python script that:
1. Extracts ALL trades for negative-PnL coins from the 55/89 backtester
2. For each trade, captures the full strategy context at entry and exit
3. Categorizes each trade's failure mode against the 55/89 strategy rules
4. Produces a statistical summary of which strategy rules are being violated most frequently
5. Special deep-dive on FARTCOINUSDT: why does this coin break the strategy?

---

## Environment

- **Backtester root:** `C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester`
- **Signal module:** `signals/ema_cross_55_89_v2.py` (function: `compute_signals_55_89(df, params)`)
- **Engine:** `engine/backtester_55_89.py` (class: `Backtester5589`)
- **Data:** `data/historical/<SYMBOL>_1m.parquet` (1-minute OHLCV, datetime index, UTC)
- **Existing trade runner:** `scripts/run_trade_analysis_5589.py` (reference for loading + running pipeline)
- **Python env:** Use `.venv` (not `.venv312`). Activate: `.venv/Scripts/activate` on Windows.
- **Results output:** `results/` directory

## Coins to Analyze

Run the full portfolio first to identify which coins are negative. The Nov-07 PDF showed these coins (use all of them, then filter to negative-PnL coins for the deep analysis):

```
FARTCOINUSDT, FILUSDT, OGUSDT, CHZUSDT, ORDERUSDT, BIGTIMEUSDT, CVCUSDT, BBUSDT, TRUMPUSDT
```

Date range: Use the full available data in each parquet file (do NOT hardcode dates — read the parquet and use min/max datetime).

## Parameters (P0-fixed values)

```python
PARAMS = {
    "sl_mult":           4.0,    # P0 fix: was 2.5, now 4.0
    "avwap_sigma":       2.0,
    "avwap_warmup":      20,     # P0 fix: was 5, now 20
    "tp_atr_offset":     0.5,
    "ratchet_threshold": 2,
    "notional":          10000.0,
    "initial_equity":    10000.0,
    "commission_rate":   0.0008,
    "rebate_pct":        0.70,
    "min_signal_gap":    50,
    "leverage":          20,
}
```

---

## Strategy Rules to Vet Against

Each trade must be checked against these core 55/89 strategy rules. For each trade, record which rules were satisfied and which were violated at entry:

### Entry Rules
1. **Stoch 9 K/D cross** — K crossed above D (long) or below D (short). Was the cross clean or marginal (< 2 points separation)?
2. **Stoch 14 state** — Must be MOVING or EXTENDED at entry. Record the actual state.
3. **Stoch 40/60 alignment** — Must be TURNING+ (slope positive for long, negative for short). Record actual slope/state.
4. **No stoch contradiction** — No stoch timeframe pointing the opposite direction. Check all 4 stoch layers.
5. **EMA 55/89 delta** — Delta must be compressing (approaching zero) or crossed. Record delta value at entry.
6. **BBW state** — Must NOT be QUIET. Record actual BBW state.
7. **TDI state** — Must be CONFIRMING. Record actual state.
8. **Trade grade** — A, B, or C. Record grade.

### SL/TP Lifecycle Rules
9. **Phase 1 SL** — Initial SL = entry +/- sl_mult * ATR. Was ATR at entry abnormally high/low for this coin?
10. **Phase 2 AVWAP freeze** — After avwap_warmup bars, SL moves to frozen AVWAP -2 sigma. How far was the frozen AVWAP from entry price? Was it tighter than Phase 1 SL (immediate tightening = bad)?
11. **Ratchet count** — How many overzone exits occurred? If 0, why? (Trade died in Phase 2 before any stoch overzone cycle completed.)
12. **saw_green** — Did the trade see unrealized profit before losing? If yes, how many bars was it green? What was peak unrealized PnL?

### Exit Analysis
13. **Exit reason** — sl_phase1, sl_phase2, sl_phase3, tp_phase4, eod. Categorize.
14. **Bars held** — How long did the trade survive? Median for losers vs winners.
15. **PnL magnitude** — Avg winning PnL vs avg losing PnL. R:R ratio.

---

## Script Structure

Write a SINGLE script: `scripts/analyze_negative_coins_5589.py`

### Phase 1: Run Pipeline + Identify Negative Coins

```python
# For each coin: load parquet, run signals, run engine, collect trades_df + metrics
# Filter to coins where net_pnl < 0
# Save per-coin and combined CSV to results/
```

### Phase 2: Per-Trade Context Extraction

For each trade in negative coins, go back to the signal DataFrame at the entry bar and extract:

```python
trade_context = {
    "symbol": ...,
    "trade_id": ...,
    "direction": ...,
    "entry_bar": ...,
    "entry_price": ...,
    "exit_price": ...,
    "pnl": ...,
    "bars_held": ...,
    "exit_reason": ...,
    "trade_grade": ...,
    "saw_green": ...,
    "ratchet_count": ...,

    # Signal context at entry bar
    "stoch9_k": df_sig["stoch_9_k"].iloc[entry_bar],
    "stoch9_d": df_sig["stoch_9_d"].iloc[entry_bar],
    "stoch9_kd_diff": abs(k - d),  # cross quality
    "stoch14_state": ...,  # from signal columns if available
    "stoch40_slope": ...,
    "stoch60_slope": ...,
    "ema_delta": df_sig["ema_55"].iloc[entry_bar] - df_sig["ema_89"].iloc[entry_bar],
    "atr_at_entry": df_sig["atr"].iloc[entry_bar],
    "atr_pct_of_price": atr / entry_price * 100,  # ATR as % of price

    # Phase 2 AVWAP analysis
    "avwap_freeze_bar": entry_bar + avwap_warmup,
    "avwap_freeze_distance_atr": ...,  # how far frozen AVWAP was from entry in ATR units

    # Failure classification (see below)
    "failure_mode": ...,
}
```

**Note:** Some signal columns may not be directly available. Check what `compute_signals_55_89()` actually puts into the DataFrame:
- `long_a`, `long_b`, `long_c`, `short_a`, `short_b`, `short_c` (signal columns)
- `ema_55`, `ema_89` (EMAs)
- `atr` (ATR)
- `trade_grade` (A/B/C)
- Stochastic columns: check what's available — they may be named `stoch_9_k`, `stoch_9_d`, `stoch_14_k`, etc.

Read the signal module first (`signals/ema_cross_55_89_v2.py`) to discover exact column names.

### Phase 3: Failure Mode Classification

Classify each losing trade into one of these failure modes:

| Mode | Criteria | Description |
|------|----------|-------------|
| `PHASE1_INSTANT_DEATH` | exit_reason=sl_phase1 | SL hit before AVWAP even froze. ATR too volatile. |
| `PHASE2_GRAVEYARD` | exit_reason=sl_phase2, ratchet_count=0 | AVWAP froze too close, trade died before any ratchet. |
| `PHASE2_SAW_GREEN` | exit_reason=sl_phase2, saw_green=True | Was profitable, then lost it at AVWAP freeze. TP/trail needed. |
| `RATCHET_INSUFFICIENT` | exit_reason=sl_phase3, ratchet_count < threshold | Ratcheted once but not enough, SL caught. |
| `WEAK_ENTRY` | trade_grade=C AND pnl < 0 | Low-confidence entry that failed. |
| `MARGINAL_CROSS` | stoch9_kd_diff < 2.0 AND pnl < 0 | Stoch 9 K/D barely crossed — weak signal. |
| `HIGH_ATR_ENTRY` | atr_pct_of_price > X (compute X as 75th percentile) AND pnl < 0 | Entered during extreme volatility spike. |
| `COUNTER_TREND` | ema_delta sign opposite to direction AND pnl < 0 | Entered against the 55/89 trend. |
| `EOD_FORCED` | exit_reason=eod | Forced close at end of data — not a strategy failure. |

A trade can have MULTIPLE failure modes. Store as a list.

### Phase 4: Statistical Summary

Print and save to `results/negative_coins_analysis_5589.txt`:

```
=== PORTFOLIO OVERVIEW ===
Total coins: X, Negative coins: Y
Negative coins: [list with net PnL each]

=== FAILURE MODE DISTRIBUTION (all negative coins) ===
PHASE2_GRAVEYARD: 245 trades (48.2%)
PHASE2_SAW_GREEN: 112 trades (22.1%)
... etc, sorted by frequency

=== PER-COIN BREAKDOWN ===
[For each negative coin:]
FARTCOINUSDT: 243 trades, 30% WR, -$8,499
  Top failure modes: PHASE2_GRAVEYARD (52%), HIGH_ATR_ENTRY (41%), WEAK_ENTRY (38%)
  Avg ATR as % of price: 3.2% (vs portfolio avg 1.8%)
  Avg bars held (losers): 15 (vs portfolio avg 22)
  Grade distribution: A=12%, B=28%, C=60%

=== FARTCOINUSDT DEEP DIVE ===
- ATR profile: min/max/mean/median ATR as % of price, compared to other coins
- Volatility regime analysis: plot ATR over time, identify if there are periods where strategy works vs doesn't
- Phase exit distribution: what % die in each phase?
- saw_green analysis: of losers that saw green, what was avg peak unrealized profit?
- Worst 10 trades: full context dump (all fields above)
- Best 10 trades: full context dump — what made these work?
- Recommendation: should FARTCOINUSDT be excluded from the portfolio? Or does it need different params?

=== CROSS-COIN PATTERNS ===
- Which failure modes are universal vs coin-specific?
- Is there a correlation between ATR volatility and failure rate?
- Do Grade C trades consistently underperform across all negative coins?
- Is there a time-of-day pattern to failures?
```

### Phase 5: Save Detailed CSV

Save `results/trade_contexts_negative_5589.csv` with ALL extracted fields for every trade in negative coins. This is the raw data for further analysis.

---

## Output Files

| File | Content |
|------|---------|
| `results/negative_coins_analysis_5589.txt` | Full statistical report (Phase 4 output) |
| `results/trade_contexts_negative_5589.csv` | Per-trade context with all extracted fields |
| `results/fartcoin_deep_dive_5589.txt` | FARTCOINUSDT-specific analysis |
| `results/trades_5589_<SYMBOL>.csv` | Per-coin trade CSVs (for all coins run) |

---

## Execution

1. Read `signals/ema_cross_55_89_v2.py` to discover exact column names available in df_sig
2. Read `engine/backtester_55_89.py` to understand trade record fields
3. Write `scripts/analyze_negative_coins_5589.py`
4. Run `python -m py_compile scripts/analyze_negative_coins_5589.py` — must pass
5. Run `python scripts/analyze_negative_coins_5589.py`
6. Read and summarize the output files
7. Provide actionable recommendations:
   - Which coins should be excluded?
   - Which failure modes are fixable vs inherent to the strategy?
   - What parameter changes would help (backed by data)?
   - Is the strategy fundamentally unsuited for meme coins / high-ATR coins?

---

## Rules

- Use `logging` module, not `print` for diagnostic output (print is OK for the final report)
- Use `pathlib.Path` for all file paths
- Forward slashes in docstrings
- `encoding="utf-8"` on all `open()` calls
- Run `py_compile` before executing
- Do NOT modify any existing files — only CREATE new files in `scripts/` and `results/`
- If a column doesn't exist in df_sig, log a warning and skip that check — do NOT crash

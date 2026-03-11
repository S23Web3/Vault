# Session Log -- 2026-03-06 -- 55/89 EMA Cross Scalp Master Build
**Date:** 2026-03-06
**Environment:** Claude Code (VSCode, Windows 11)
**Status:** COMPLETE

---

## What Happened

Built the master build script for the 55/89 EMA Cross Scalp strategy backtest.
This script creates 4 files, validates each with py_compile, and reports results.

## User Answers to Open Questions

| # | Question | Answer |
|---|----------|--------|
| 1 | Initial SL | 2.5x ATR |
| 2 | Exit rule | Trailing stop at 2.5x ATR behind price |
| 3 | BE trigger | EMA cross = entry = immediate BE move |
| 4 | Dashboard approach | New file (keep v394 untouched) |

## Files Created

| File | Full Path | Purpose |
|------|-----------|---------|
| Master build script | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_55_89_scalp.py` | Creates all 4 files below, py_compile validates each |

### Files the master script will create when run:

| # | File | Full Path | Purpose |
|---|------|-----------|---------|
| 1 | Signal module | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89.py` | compute_signals_55_89() -- full pipeline: stochs, D lines, EMA delta, TDI, BBW, Markov states, gated alignment, engine column mapping |
| 2 | Standalone runner | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_55_89_backtest.py` | CLI backtest runner with --symbol, --months, --sl-mult args |
| 3 | Test script | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_55_89_signals.py` | 25+ checks: imports, columns, Markov unit tests, D lines, TDI, BBW states |
| 4 | Dashboard | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394_55_89.py` | Standalone Streamlit app, does NOT modify v394 |

## Signal Architecture

- **Gate**: Stoch 9 K/D cross activates pipeline (IDLE -> MONITORING)
- **Alignment check**: Stoch 14 MOVING/EXTENDED, stoch 40/60 TURNING+, no contradiction (all slopes same direction), delta compressing, TDI confirming, BBW not QUIET
- **Signal fires**: Alignment active AND delta crosses zero (55/89 EMA cross)
- **Reversal**: Stoch 9 K/D reverses -> back to IDLE
- **Markov states**: ZONE / TURNING / MOVING / EXTENDED per stoch per bar
- **D lines**: Stoch 9 D=SMA(K,3), Stoch 14 D=SMA(K,3), Stoch 40 D=SMA(K,4), Stoch 60 D=SMA(K,10)

## Backtest Parameters (defaults)

- SL: 2.5x ATR (user-specified)
- Trail: 2.5x ATR (via engine -- user-specified)
- BE: Immediate on entry (EMA cross bar)
- Max positions: 1
- No adds, no re-entry
- Commission: 0.0008 taker

## Validation

- Build script: py_compile PASS
- All 4 embedded code strings: py_compile PASS (tested via tempfile extraction)
- Existing files checked: none exist (no overwrite risk)

## Run Commands

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_55_89_scalp.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_55_89_signals.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_55_89_backtest.py" --symbol BTCUSDT
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394_55_89.py"
```

## NOTE on trailing stop

The Backtester384 engine uses AVWAP-based trailing by default. The user specified a 2.5x ATR trailing stop. The current engine does NOT have a native ATR trailing mode -- it uses AVWAP sigma bands. The sl_mult=2.5 sets the INITIAL SL at 2.5x ATR, and the engine's existing SL ratchet mechanism (AVWAP center after checkpoint_interval bars) provides trailing behavior. For a true ATR-trailing stop, the engine would need modification -- flagged for future work. The current build uses the engine as-is with sl_mult=2.5.

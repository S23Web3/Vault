# 55/89 Trade Analysis + Flaw Identification — Build Plan

**Date:** 2026-03-10
**Context:** Portfolio backtest PDF `C:\Users\User\Downloads\55_89_portfolio_2025-04-09.pdf` exists. Signal pipeline v2 (`signals/ema_cross_55_89_v2.py`) and engine (`engine/backtester_55_89.py`) are both built and py_compile-clean. Regression channel is a real module (not a stub) but uses an R2+slope gate that will filter signals. Task: extract trades, visualise 20+, write plain-English trade outline, identify flaws.

---

## Scope

Deliver 3 artefacts:

1. `scripts/run_trade_analysis_5589.py` — load parquet, run v2 signals + engine, save `results/trades_5589_SYMBOL.csv` per coin
2. `scripts/visualise_5589_trades.py` — matplotlib trade grid (20–50 trades, 4×5 layout), one PNG per coin
3. Analysis findings (plain text in session log): typical trade outline, grade breakdown, flaw list with WHAT/WHY/HOW COMMON/FIX

**Not in scope:** dashboard changes, engine changes, any new signal logic.

---

## Key Files

| Role | Path |
|------|------|
| Signal pipeline v2 | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89_v2.py` |
| Engine | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_55_89.py` |
| Regression channel | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\regression_channel.py` |
| Runner v2 (reference) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_55_89_backtest_v2.py` |
| Data parquet | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\historical\<SYMBOL>_1m.parquet` |
| Results dir | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\results\` |

**Note:** `run_55_89_backtest_v2.py` still imports `from signals.ema_cross_55_89` (v1). The new trade analysis script must import from `signals.ema_cross_55_89_v2`.

---

## Pre-Step: Read PDF

Before writing any code, use pymupdf to render each page of the portfolio PDF to PNG, then view with Read tool to understand the result set (coin list, date range, trade counts).

Run command (user executes):
```
python -c "import pymupdf, os; doc = pymupdf.open(r'C:\Users\User\Downloads\55_89_portfolio_2025-04-09.pdf'); [doc[i].get_pixmap(dpi=200).save(os.path.join(r'C:\Users\User\Downloads', 'pf_page_' + str(i+1) + '.png')) or print('Saved page', i+1) for i in range(len(doc))]"
```

Then view each page PNG with Read tool to extract: coin list, trade counts, win rates, PnL summary.

---

## File 1: `scripts/run_trade_analysis_5589.py`

**Purpose:** Batch runner — one CSV of trades per coin, saved to results/.

**Logic:**
1. Hardcode coin list from the PDF (extracted above); fallback = scan `data/historical/` for any `*_1m.parquet`
2. For each coin:
   - Load parquet from `data/historical/SYMBOL_1m.parquet`
   - Optionally filter to date range from PDF (param: `DATE_FROM`, `DATE_TO`)
   - Call `compute_signals_55_89(df, params={})` from `signals.ema_cross_55_89_v2`
   - Call `Backtester5589(params).run(df_sig)`
   - Extract `results["trades_df"]`
   - Add columns: `symbol`, `entry_datetime`, `exit_datetime` (mapped from bar index to datetime)
   - Save to `results/trades_5589_SYMBOL.csv`
3. Print summary table per coin: total trades, win rate, phase breakdown
4. `py_compile.compile` called on script itself after write

**Params dict (defaults, not CLI args):**
```python
PARAMS = {
    "sl_mult": 2.5,
    "avwap_sigma": 2.0,
    "avwap_warmup": 5,
    "tp_atr_offset": 0.5,
    "ratchet_threshold": 2,
    "notional": 5000.0,
    "initial_equity": 10000.0,
    "commission_rate": 0.0008,
    "rebate_pct": 0.70,
    "min_signal_gap": 50,
}
```

**Run command:** `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_trade_analysis_5589.py"`

---

## File 2: `scripts/visualise_5589_trades.py`

**Purpose:** For each coin's CSV, render a matplotlib grid of up to 50 trades (20 minimum), one PNG per coin.

**Per-trade subplot (OHLC window: entry_bar - 10 to exit_bar + 5):**
- Price line (close, not full candlestick — simpler to read at small scale)
- EMA 55 line (from df_sig)
- EMA 89 line (from df_sig)
- Vertical line at entry bar (green/red)
- Vertical line at exit bar (grey dashed)
- Horizontal line at entry SL (ATR-based, dashed red): `entry_price - 2.5 * atr[entry_bar]` for longs
- Entry marker: green triangle up (long) or red triangle down (short) at entry bar
- Exit marker: green circle (win) or red circle (loss) at exit bar
- Text box (top-left of subplot):
  - `Grade: A/B/C`
  - `Exit: sl_phase1 / tp_phase4 / etc`
  - `PnL: $+3.21`
  - `D9@entry: 22.3`
  - `BE: YES` (if ema_be_triggered)
  - `Ratchets: 1`

**Layout:** 4 rows × 5 cols = 20 trades per page. If coin has more than 20 trades, render pages in batches of 20, named `results/trade_viz_5589_SYMBOL_p1.png`, `_p2.png`, etc. (up to 50 trades = max 3 pages).

**Data source:** Re-runs signals+engine live per coin (does not require CSV; loads parquet directly). This ensures df_sig is available for EMA lines and D9 values.

**Run command:** `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualise_5589_trades.py"`

---

## Build Script: `scripts/build_trade_analysis_5589.py`

Single build script (follows MEMORY.md build workflow):

1. LOG: `logs/YYYY-MM-DD-build-trade-analysis-5589.log` (TimedRotatingFileHandler + StreamHandler, timestamps)
2. WRITE `scripts/run_trade_analysis_5589.py` → `py_compile` immediately
3. WRITE `scripts/visualise_5589_trades.py` → `py_compile` immediately
4. AUDIT: every def has docstring, no escaped quotes in f-strings
5. OUTPUT: summary — files written, py_compile results, audit pass/fail

Does NOT execute Python. User runs build script then runs the output scripts.

Run command: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_trade_analysis_5589.py"`

---

## Analysis Output (after user runs the scripts)

Once trades CSV + PNGs are available, produce (in session log):

**Section 1: Typical LONG trade (plain English)**
- Stoch 9 D trajectory (when it hit sub-20, how long it stayed, how fast it bounced)
- Entry trigger mechanics
- Initial SL placement (distance from entry)
- SL evolution: AVWAP freeze at bar 5, ratchet events
- EMA BE: when it fired relative to entry, did it help
- Exit: phase distribution

**Section 2: Typical SHORT trade (same structure)**

**Section 3: Grade breakdown**
- A / B / C count and %
- Win rate per grade
- Does grade predict outcome?

**Section 4: Flaw list**
For each flaw: WHAT / WHY / HOW COMMON / FIX (file + line reference)

Focus areas (from prompt):
1. Entry timing: too early vs too late (stoch 9 D barely touched 20 vs bounced far above)
2. SL Phase 1 sizing: 2.5x ATR on 1m altcoin data
3. AVWAP warmup: 5 bars — is that enough on 1m?
4. EMA 55/89 cross timing relative to entry (cross pre-dates entry = BE fires immediately or not at all)
5. Phase 3/4 reach rate: what % of trades get ratchet >= 2?
6. Grade predictive power: do C trades dominate losses?

---

## Important Notes

- **regression_channel is LIVE** (not stub). It imports `fit_channel`, `pre_stage1_gate` etc. from `signals/regression_channel.py`. The R2 >= 0.45 and slope_pct < -0.001 gate on 20-bar pre-entry window WILL filter signals. This may be contributing to low trade counts.
- **run_55_89_backtest_v2.py imports v1** (`ema_cross_55_89`, not `ema_cross_55_89_v2`). The new scripts must explicitly import from `ema_cross_55_89_v2`.
- The `results/` directory already exists at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\results\`.
- Coin list will be determined from PDF. Likely 10 coins from the 2025-04-09 portfolio run.

---

## Verification

1. Run build script → py_compile PASS on both files
2. Run `run_trade_analysis_5589.py` → CSVs written to `results/trades_5589_SYMBOL.csv` for each coin
3. Inspect one CSV manually — confirm columns: direction, entry_bar, exit_bar, pnl, exit_reason, trade_grade, ema_be_triggered, ratchet_count, phase_at_exit
4. Run `visualise_5589_trades.py` → PNGs written to `results/trade_viz_5589_SYMBOL_p1.png`
5. View PNGs with Read tool — confirm subplots readable, annotations correct, EMA lines visible

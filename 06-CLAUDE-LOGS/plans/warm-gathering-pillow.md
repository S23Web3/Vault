# Plan: 55/89 EMA Cross Scalp Dashboard v2

## Context
The 55/89 EMA cross scalp strategy has a working signal module and a broken v394 Streamlit dashboard. The dashboard is missing leverage/margin controls, has a bugged BE trigger default (0.0 disables breakeven), and lacks multi-coin portfolio mode with comparable date windows. This plan ports the good features from production dashboard v3.9.3 into a clean 55/89-specific dashboard.

User requirement: comparable data — when running multiple coins, all must use the same date window so results are apples-to-apples.

---

## Output Files

| File | Status |
|------|--------|
| `scripts/build_dashboard_55_89_v2.py` | NEW — build script |
| `scripts/dashboard_55_89_v2.py` | CREATED by build script |

Neither file currently exists. Do NOT touch `dashboard_v394_55_89.py`.

---

## Sidebar Controls (in order)

| Section | Control | Type | Default |
|---------|---------|------|---------|
| Symbol | Symbol | selectbox | first in list |
| Mode | Mode | radio (Single / Portfolio) | Single |
| Signal | Slope window N | slider 2–20 | 5 |
| Signal | Accel window M | slider 2–10 | 3 |
| Period | Period | radio All/7d/30d/90d/Custom | All |
| Capital | Margin $ | number_input | 500.0 |
| Capital | Leverage | number_input 1–125 | 20 |
| Capital | *Notional caption* | caption | margin × leverage |
| Exits | SL multiplier (ATR x) | slider 0.5–5.0 | 2.5 |
| Exits | *TP: disabled caption* | caption | — |
| Breakeven | BE trigger (ATR x) | slider 0.0–3.0 | **1.0** (bug fix) |
| Breakeven | BE lock (ATR x) | slider 0.0–2.0 | 0.0 |
| Commission | Rebate | radio 70% / 50% / 0% | 70% |
| Commission | *Per side / RT / Net caption* | caption | derived |
| *Portfolio only* | Coin Selection | radio Random N / Custom | Random N |
| *Portfolio only* | N coins | slider 2–30 | 10 |
| Action | Run Backtest / Run Portfolio | button | — |
| Action | Reset | button | — |

---

## Data Flow

```
Controls
  → sig_params = {slope_n, slope_m}
  → bt_params  = {sl_mult, tp_mult=None, be_trigger_atr, be_lock_atr,
                  notional=margin*leverage, margin, leverage,
                  commission_rate=0.0008, rebate_pct, initial_equity=10000,
                  max_positions=1, cooldown=1, enable_adds=False, enable_reentry=False}

load_data(symbol)          → normalize base_vol/quote_vol columns
apply_date_filter(df, range)
compute_signals_55_89(df, sig_params)   → df_sig with long_a/short_a + engine cols
Backtester384(bt_params).run(df_sig)   → results {equity_curve, trades_df, metrics}
```

Params hash (MD5) gates session_state cache — results persist across reruns until params change.

---

## Panel Layout

### Single Mode
1. Title + caption row (symbol, date range, bar count, signal count, notional)
2. Metrics row 1 (6 cols): Trades | Win Rate | Net PnL | Profit Factor | Sharpe | Max DD%
3. Metrics row 2 (4 cols): Avg Win | Avg Loss | Expectancy | Commission
4. Metrics row 3 (3 cols): Rebate $ | Net w/Rebate | BE Raises
5. Equity curve — Plotly dark, datetime X axis, height=350
6. Trades table — scrollable, height=400, columns: direction/entry_price/exit_price/pnl/commission/net_pnl/mfe/mae/exit_reason/saw_green

### Portfolio Mode
1. Title + caption (N coins, date window, mode)
2. Summary metrics (5 cols): Coins | Net PnL | Max DD% | Peak Capital | Total Trades
3. Per-coin summary table — Symbol/Trades/WR%/Net$/Sharpe/PF/DD%/Expectancy/Commission
4. Portfolio equity curve — thin per-coin lines (opacity=0.4) + bold green portfolio sum, master datetime X axis

---

## Portfolio: Comparable Date Window

**Symbol locking:** On "Run Portfolio Backtest" click, selected symbols saved to `st.session_state["port_symbols_55_89_locked"]`. Re-rolls only on Reset or if no locked state.

**Date enforcement:** All coins filtered with the same `date_range` before running:
```python
for sym in port_symbols:
    df = load_data(sym)
    df = apply_date_filter(df, date_range)   # same range every coin
    ...
```

**Equity alignment (`align_portfolio_equity_55_89`):**
- Build `master_dt` = union of all coin datetime indices
- Reindex each coin equity series to master_dt with `method="ffill"`
- Sum to portfolio curve
- Compute portfolio peak/DD from summed curve

---

## Bug Fixes

| Bug | Fix |
|-----|-----|
| `be_trigger_atr` default=0.0 (disables BE) | Default changed to 1.0 |
| Notional hardcoded to $5000 | `notional = margin * leverage` |
| No rebate_pct in bt_params | Added to dict |
| Missing `base_vol` column rename | Added in `load_data()` |
| Date filter was checkbox (inconsistent) | Replaced with preset radio |
| Portfolio symbols re-roll on rerun | Session_state lock |

---

## Deliberately Out of Scope

- No ML tab (no grade columns)
- No sweep mode
- No TP slider (always None)
- No scale-out controls
- No AVWAP adds/re-entry
- No shared pool capital mode
- No per-coin drill-down expanders
- No param_log.jsonl
- No timeframe selector (1m only)

---

## Critical Files

| File | Role |
|------|------|
| `scripts/dashboard_v393.py` | Pattern source: sidebar layout, apply_date_filter, align_portfolio_equity, portfolio run loop, commission display |
| `scripts/dashboard_v394_55_89.py` | Existing broken dashboard: reuse run_backtest fn, load_symbol_list, load_data, metrics row |
| `signals/ema_cross_55_89.py` | Signal module: `compute_signals_55_89(df, params)` interface |
| `engine/backtester.py` | Backtester384: bt_params keys, base_vol requirement, results dict shape |
| `scripts/build_55_89_scalp.py` | Build script pattern: write_and_validate, ERRORS list, py_compile |

---

## Build Script Structure

```
build_dashboard_55_89_v2.py
├── ERRORS, CREATED, TIMESTAMP constants
├── write_and_validate(filepath, content) -> bool
│     checks file doesn't exist → writes → py_compile(doraise=True)
├── DASHBOARD_CONTENT = r'''...full dashboard source...'''
│     All string expressions use concatenation (no escaped quotes in f-strings)
│     Every def has a one-line docstring
└── Main block: write file → report PASS/FAIL → print run command
```

No f-strings with escaped quotes inside triple-quoted build content. Use:
- CORRECT: `'st.sidebar.caption("Notional: $" + f"{notional:,.0f}")'`
- WRONG: `'st.sidebar.caption(f"Notional: ${notional:,.0f}")'`

---

## Verification

1. `python scripts/build_dashboard_55_89_v2.py` → expect "BUILD SUCCESS"
2. `streamlit run scripts/dashboard_55_89_v2.py` from backtester root
3. Single mode: select BTCUSDT, Period=30d → verify notional caption, BE trigger=1.0, non-zero trades
4. Check commission display: margin=500, leverage=20 → "Per side: $8.00 | RT: $16.00 | Net RT: $4.80"
5. Portfolio mode: Random N=5, Period=30d → verify 5-row table + portfolio equity curve
6. Verify all 5 coins' equity curves start at same X position (same date window enforced)

---

## Also: Audit & Debug Pass

Before writing the build script, run an audit of `ema_cross_55_89.py` and `dashboard_v394_55_89.py` for:
- Unused imports (`stoch_k`)
- Stochastic ordering bug (MOVING before EXTENDED fix not backported)
- Any py_compile errors
- Column name mismatches with Backtester384 expectations

Fixes fold into the new dashboard's `run_backtest_55_89()` wrapper or into the signal module directly (if signal module needs patching, patch it in-place via Edit tool before building the dashboard).

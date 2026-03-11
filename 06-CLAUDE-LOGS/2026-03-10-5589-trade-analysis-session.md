# 55/89 Trade Analysis + Flaw Identification Session
**Date:** 2026-03-10

---

## What was done

### Task 1: PDF Extraction
- Read portfolio backtest PDF (`C:\Users\User\Downloads\55_89_portfolio_2025-04-09.pdf`) via pymupdf
- Extracted: 10 coins, 566 trades, -$10,414.85 net PnL, date range 2025-04-09 to 2025-05-09

### Task 2: Trade Data Extraction
- Built `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_trade_analysis_5589.py` (build script)
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_trade_analysis_5589.py` (batch runner)
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualise_5589_trades.py` (matplotlib grids)
- User ran both scripts: 532 trades extracted across 10 coins
- Per-coin CSVs saved to `results/trades_5589_SYMBOL.csv`, combined CSV to `results/trades_5589_ALL.csv`
- 24 PNG pages of trade visualisations saved to `results/trade_viz_5589_*.png`

### Task 3: Statistical Analysis
- Built `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\analyze_5589_stats.py`
- Key findings:
  - **18.0% overall win rate** (96 wins / 532 trades)
  - **61.5% exit at sl_phase2** (AVWAP freeze) -- mass graveyard
  - **70.3% never ratchet** (ratchet_count = 0) -- Phase 3/4 unreachable
  - **BE trigger fires only 5.8%** (31/532) -- EMA cross too slow
  - **Grade C = 61.1%** of trades with worst WR
  - **68.6% LSG** (losers saw green) -- TP/trail is key lever
  - **Phase 1 kills: 8.8%, 0% WR, avg -$113.24** -- SL too tight

### Task 4: Flaw Analysis (6 flaws identified)

| # | Flaw | Severity | How Common | P0 Fix |
|---|------|----------|------------|--------|
| 1 | Phase 2 mass graveyard | CRITICAL | 61.5% | avwap_warmup 5 -> 20 |
| 2 | Ratchets never fire | HIGH | 70.3% | Dependent on flaw #1 fix |
| 3 | BE trigger useless | MEDIUM | 94.2% never fire | Consider removing or replacing with distance-based BE |
| 4 | Phase 1 SL too tight | CRITICAL | 8.8%, 0% WR | sl_mult 2.5 -> 4.0 |
| 5 | 68.6% LSG | HIGH | 68.6% of losers | TP or tighter trail needed |
| 6 | Grade C dominates | MEDIUM | 61.1% | Consider filtering C trades |

### Task 5: P0 Fixes Applied
- Modified `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py`:
  - `sl_mult` default: 2.5 -> 4.0, slider max: 5.0 -> 8.0
  - `avwap_warmup` default: 5 -> 20, slider max: 10 -> 50
- py_compile PASS
- **User validation on AXSUSDT random month (2025-06-26 to 2025-07-26):**
  - 27 trades, 40.7% WR, $531.65 net PnL
  - Sharpe 3.085, PF 1.67, Max DD 3.4%
  - User confirmed: "it looks great"

---

## Files Created
| File | Type | Purpose |
|------|------|---------|
| `scripts/build_trade_analysis_5589.py` | Build | Creates runner + visualiser |
| `scripts/run_trade_analysis_5589.py` | Runner | Batch trade extraction (10 coins) |
| `scripts/visualise_5589_trades.py` | Viz | Matplotlib trade grids (4x5 layout) |
| `scripts/analyze_5589_stats.py` | Analysis | Quick stats on combined trades CSV |

## Files Modified
| File | Change |
|------|--------|
| `scripts/dashboard_55_89_v3.py` | sl_mult default 2.5->4.0, avwap_warmup default 5->20 |

## Build Traps Encountered
1. `"\n".join()` inside triple-quoted build string content: Python interprets `\n` as real newline, splitting the string literal. Fix: write file directly via Write tool, use `NL = "\n"` constant.
2. `$` in bash format strings: bash interprets `${:.2f}` as variable substitution. Fix: use `chr(36)` in Python source to construct dollar signs.

---

## Session Continuation: Capital Metrics + FARTCOIN Analysis

### Task 6: Dashboard v3 Capital Usage Metrics + Aesthetic Layout
- Added styled HTML metric cards (CSS injection) replacing plain `st.metric()` calls
- 4 logical groups: Performance (6 cols), Trade Economics (4 cols), Volume & Rebates (5 cols), Capital Usage (5 cols)
- New metrics: Avg Capital Used, Peak Capital Used, % Time Flat, Capital Efficiency (ROI), Recommended Wallet, Daily Volume
- Applied to both `render_single_results()` and `render_portfolio_results()`

### Task 7: Capital Metrics Bug — Peak Capital $130k/$180k on $10k Wallet
- **Root cause:** Engine used `self.notional` ($10,000) instead of margin ($500) for `margin_per_pos`
- **Fix 1 (engine):** Added `self.leverage` to `Backtester5589.__init__`, computed `margin_per_pos = self.notional / self.leverage`
- **Fix 2 (dashboard):** Streamlit module caching prevented engine fix from taking effect. Refactored `compute_capital_metrics()` to use position COUNTS (`avg_positions`, `max_positions_used`) times sidebar margin value — completely independent of engine's margin calculation.
- **Result:** Peak Capital now shows $4,500 (9 coins x $500 margin = correct for shared pool)

### Task 8: Rebate Settlement Verification
- Confirmed: engine calls `self.comm.check_settlement(bar_dt)` every bar, adds rebate to equity at 5pm UTC daily crossover

### Task 9: Nov-07 Portfolio PDF Analysis
- Analyzed `C:/Users/User/Downloads/55_89_portfolio_2025-11-07.pdf`: 9 coins, 1055 trades, -$3,480.81 net
- FARTCOINUSDT worst: 243 trades, 30% WR, -$8,499.35, 333.1% max DD
- Cause: extreme meme coin ATR volatility defeats AVWAP trail, highest trade count, worst WR, massive commission drag

### Task 10: Deep Analysis Prompt Written
- `C:/Users/User/Documents/Obsidian Vault/06-CLAUDE-LOGS/plans/2026-03-10-fartcoin-trade-analysis-prompt.md`
- Claude agent prompt: per-trade analysis of negative coins + FARTCOINUSDT deep dive
- 8 failure mode classifications, signal context extraction at entry, cross-coin pattern analysis

## Files Modified (continuation)
| File | Change |
|------|--------|
| `scripts/dashboard_55_89_v3.py` | CSS cards, 4-group metric layout, capital usage row, `compute_capital_metrics()` refactored to use position counts x margin |
| `engine/backtester_55_89.py` | Added `self.leverage`, fixed `margin_per_pos` calculation |

## Files Created (continuation)
| File | Purpose |
|------|---------|
| `06-CLAUDE-LOGS/plans/2026-03-10-fartcoin-trade-analysis-prompt.md` | Claude agent prompt for negative coin deep analysis |
| `06-CLAUDE-LOGS/plans/2026-03-10-dashboard-capital-metrics-plan.md` | Plan for capital metrics + aesthetic layout |

---

## Next Steps (not started)
- Run FARTCOIN deep analysis prompt via Claude agent
- Portfolio sweep across all 10 coins with new params (sl_mult=4.0, avwap_warmup=20)
- Consider filtering Grade C trades to improve WR further
- Consider replacing EMA BE trigger with distance-based BE
- Vince B1 feature extraction (deferred until breakeven achieved)

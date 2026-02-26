# Four Pillars Trading System — Progress Review
**Date:** 2026-02-07

---

## Version Evolution

| Version | Date | SL Type | Commission | Key Change | Outcome |
|---------|------|---------|------------|------------|---------|
| v3.4.1 | Baseline | 2.0 ATR static | percent 0.1% ($0.50/side) | Original system | Marginally profitable |
| v3.5 | — | 2.0 ATR static | percent 0.1% | Added stochastic SMA smoothing (bug) | Missed signals — SMA delayed K |
| v3.5.1 | — | Cloud 3 ± 1 ATR trail | percent 0.1% | Fixed Raw K, Cloud 3/4 trail activation | Bled out in chop — trail doesn't protect early |
| v3.6 | — | AVWAP ± stdev trail | percent 0.1% | AVWAP stops, separate A/BC order IDs, volume flip filter | stdev=0 bug on bar 1, barely trails early, bled out |
| v3.7 | — | 1.0 ATR static | percent 0.06% ($0.30/side) | Rebate farming: B/C fresh, free flips, no volume filter | Commission blow-up — phantom trades + wrong % calc |
| v3.7.1 | Current | 1.0 ATR static | cash_per_order=6 ($6/side) | Fixed commission, cooldown, no close_all | $1.81/trade expectancy (before rebates) |

---

## What Each Version Solved and Broke

### v3.5 — Stochastic Smoothing Bug
- **Intent:** Improve signal quality with standard Fast Stochastic
- **Bug:** Applied `ta.sma(rawK, smooth_k)` to K line. Four Pillars needs Raw K (smooth=1). The SMA delayed signals by 2-3 bars, causing missed entries.
- **Lesson:** Never use SMA-smoothed K for entry detection in this system.

### v3.5.1 — Cloud 3/4 Trail
- **Intent:** Let winners run with trailing stop that follows Cloud 3 ± 1 ATR
- **Feature:** Trail activates when ema50 crosses ema72 (Cloud 3/4 alignment gate)
- **Problem:** Activation delay — trail doesn't protect gains for the first N bars after entry. In choppy markets, price hits full SL before trail activates. 3-state SL visual (yellow/orange/red) was good but the mechanism bled.
- **Lesson:** Trailing stops fail in chop-heavy crypto markets.

### v3.6 — AVWAP Trail
- **Intent:** Use statistically meaningful AVWAP levels as stop loss
- **Features:** AVWAP ± stdev from entry bar, separate A/BC order IDs, Cloud 3/4 parallel for BC filter, volume flip filter, AVWAP recovery re-entry
- **Bug:** On bar 1 after entry, stdev=0 (one data point) → near-zero SL distance → instant stop-out. Even with ATR floor fix, AVWAP barely trails in first 10-20 bars.
- **Lesson:** AVWAP is better for swing trades with meaningful anchor points, not for 1m scalping.

### v3.7 — Rebate Farming (Commission Blow-Up)
- **Intent:** ~3000 trades/month, flat equity, profit from commission rebates
- **Architecture:** B/C open fresh + flip, no volume filter, tight 1.0/1.5 ATR SL/TP, pyramiding=1
- **Bug 1:** `commission.percent=0.06` applies to CASH qty ($500), not notional ($10k). Real cost 20x higher than backtester showed.
- **Bug 2:** `strategy.close_all()` + `strategy.entry()` on same bar = phantom trade (2 commissions per flip instead of 1)
- **Result:** Rapid equity drain. Backtester showed profit but real account lost money.
- **Lesson:** Use `cash_per_order` for leveraged strategies. Never use `close_all()` for flips.

### v3.7.1 — Commission Fix (Current)
- **Fixes:** cash_per_order=6, removed close_all, added strategy.cancel before flips, cooldown gate (3 bars), cooldownOK on all entry paths
- **Result:** $1.81/trade expectancy (before rebates), $13.81 gross profit per trade
- **Status:** Functional but not yet optimized. Breakeven+$X raise not implemented yet.

---

## Market Context

| Period | Condition | Strategy Impact |
|--------|-----------|-----------------|
| **Nov 11** | BTC favorable, strong trend | Bot should profit — trending conditions suit the system |
| **Dec 15** | BTC dump — sharp sell-off | Stress test — rapid short signals, potential whipsaw |
| **Jan 15+** | Bearish grind — slow downtrend | Choppy, mixed signals, reduced win rate expected |
| **Feb 4** | BTC dump — another sharp sell-off | Stress test — similar to Dec 15 |

These dates are critical validation checkpoints for the Python backtester. The system must perform differently in each regime — the optimizer (WS4) will find regime-specific parameters.

---

## Core Finding

**86% of losing trades saw unrealized profit before dying.**

This means:
- Signal quality is fine — entries are picking direction correctly most of the time
- Exit timing is the bottleneck — trades that turn profitable are not being protected
- The SL is hit after the trade reverses from its peak unrealized profit

**Implication:** A breakeven+$X raise (moving SL to entry+$X once trade is $X in profit) could convert the majority of losing trades into small winners. This is the primary optimization target for v4.

---

## Next Steps

1. Build Python backtester to replay historical 1m data with exact same logic (WS3)
2. Test breakeven+$X raise at different thresholds ($2, $5, $10, $20)
3. Compare 4 exit strategies side-by-side on same data
4. ML optimizer to find regime-specific parameters (WS4)
5. Build v4 with best findings, validate with Monte Carlo (WS5)

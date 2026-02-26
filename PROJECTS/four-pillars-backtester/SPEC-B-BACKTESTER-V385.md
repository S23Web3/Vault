# SPEC B: Backtester v385 -- Metrics + Entry-State + Lifecycle Logging

**Version:** v385 (version bump from v384)
**Date:** 2026-02-13
**Base:** `engine/backtester_v384.py`
**Output:** `engine/backtester_v385.py`
**Test script:** `scripts/test_v385.py`
**Depends on:** Nothing (standalone engine change)
**Feeds:** Spec A (Dashboard v3 auto-detects new keys), Spec C (ML consumes training data)
**Review:** `DASHBOARD-V3-BUILD-SPEC-REVIEW.md`

---

## PURPOSE

Add richer metrics, entry-state snapshots, trade lifecycle summaries, and LSG categorization to the backtester. This is the data layer that feeds both the dashboard (Spec A) and the ML pipeline (Spec C).

**Critical constraint:** Do NOT change entry logic, exit logic, or signal processing. All additions are either:
1. Post-loop computation from existing `trades` list (local var in `run()`) (12 metrics)
2. Snapshot at entry bar (entry-state logging)
3. Summary stats computed during trade lifecycle (lifecycle logging)
4. Categorization at exit (LSG categories, P&L path)

---

## PART 1: 12 NEW METRICS (post-loop, safe)

These are ALL derivable from the existing `trades` list (local var in `run()`) after the backtest loop completes. No loop changes needed. Append-only to metrics dict.

```
peak_capital         -- max(concurrent_positions * notional) across all bars
capital_efficiency   -- net_pnl / peak_capital * 100
max_single_win       -- max(t.pnl for t in trades if t.pnl > 0)
max_single_loss      -- min(t.pnl for t in trades if t.pnl < 0)
avg_winner           -- mean(t.pnl for winners)
avg_loser            -- mean(t.pnl for losers)
wl_ratio             -- avg_winner / abs(avg_loser)
max_win_streak       -- longest consecutive winning trades
max_loss_streak      -- longest consecutive losing trades
sortino              -- annualized sortino ratio using daily returns
calmar               -- net_pnl / abs(max_drawdown_amount), INF if no DD
be_exits             -- count of trades closed at breakeven (abs(pnl) < threshold)
```

**Where to add:** After existing metrics calculation block in `_compute_metrics()` or equivalent.

**Edge cases:**
- No winners: `avg_winner = 0`, `wl_ratio = 0`
- No losers: `avg_loser = 0`, `wl_ratio = INF`
- No drawdown: `calmar = float('inf')`
- Zero trades: all metrics = 0

---

## PART 2: ENTRY-STATE LOGGING (11 fields per trade)

For EVERY trade (not just losers), snapshot the Four Pillars indicator state at the entry bar. This is VINCE's primary training input.

| Field | What | Why |
|-------|------|-----|
| entry_stoch9_value | K value 0-100 | Already overbought at entry? |
| entry_stoch9_direction | rising/falling/flat (compare to prev bar) | Momentum direction |
| entry_stoch14_value | K value 0-100 | Confirmation strength |
| entry_stoch40_value | K value 0-100 | Divergence state |
| entry_stoch60_value | K value 0-100 | Macro trend |
| entry_stoch60_d | D-smooth value | Macro signal line |
| entry_ripster_cloud | which cloud pair (2/3/4), price distance from edge | Cloud context |
| entry_ripster_expanding | bool (cloud width > prev bar width) | Expanding = strong trend |
| entry_avwap_distance | (price - position_avwap) / position_avwap * 100 | % overextension from anchor |
| entry_atr | ATR value at entry bar | Volatility context |
| entry_vol_ratio | volume / SMA(volume, 20) | Above or below average volume |

**Note on `entry_grade`:** Already present in the existing trade fields as `grade`. Not duplicated here.

**Note on AVWAP:** `entry_avwap_distance` uses the position's AVWAPTracker (from `engine/avwap.py`), which is initialized at trade open. This is the distance from the position's anchored VWAP, NOT a global signal column.

**DEFERRED -- BBWP fields:** `entry_bbwp_value` and `entry_bbwp_spectrum` require porting BBWP from Pine Script (`indicators/supporting/bbwp_v2.pine`) to Python. BBWP does not exist in the Python signal pipeline. These fields will be added after the BBWP Python port build (separate spec).

**Implementation:** At the point where a new trade is opened in the per-bar loop, snapshot these values from the current bar's indicator state. Store as attributes on the trade object.

**Note:** Indicator values are ALREADY computed at each bar (stochastics, clouds, ATR in `four_pillars_v383.py`). This is a snapshot, not a new calculation. Minimal overhead.

---

## PART 3: TRADE LIFECYCLE LOGGING (14 fields per trade)

While a position is open, track indicator behavior and compute summary stats at close. Stored as trade attributes, NOT per-bar storage.

| Field | What | Why |
|-------|------|-----|
| life_bars | Total bars trade was open | Trade duration |
| life_stoch9_min | Lowest stoch9 during trade | Did momentum bottom out? |
| life_stoch9_max | Highest stoch9 during trade | Did it get overbought? |
| life_stoch9_trend | Slope (linear regression of stoch9) | Rising/falling/flat momentum |
| life_stoch9_crossed_signal | bool: did K cross D? | Signal change mid-trade |
| life_ripster_flip | bool: did cloud color flip? | Trend reversal during trade |
| life_ripster_width_change | (exit_width - entry_width) / entry_width | Expanding or contracting |
| life_avwap_max_dist | Max distance from position AVWAP during trade | How far did it extend? |
| life_avwap_end_dist | Position AVWAP distance at exit bar | Where did it close vs anchor? |
| life_vol_avg | mean(vol_ratio) during trade | Sustained volume or fade? |
| life_vol_trend | Slope of volume ratio | Increasing or decreasing interest |
| life_mfe_bar | Bar number where MFE occurred | Early peak (bad) vs late peak (good) |
| life_mae_bar | Bar number where MAE occurred | When was max pain? |
| life_pnl_path | Classification string | P&L trajectory shape |

**DEFERRED -- BBWP field:** `life_bbwp_delta` (bbwp_exit - bbwp_entry) requires BBWP Python port. Added after that build.

**Note on AVWAP fields:** `life_avwap_max_dist` and `life_avwap_end_dist` use the position's AVWAPTracker, which accumulates per bar while the position is open. Distance = `(price - avwap_center) / avwap_center * 100`.

**Implementation:** Accumulate min/max/sum values during per-bar update loop. Compute slopes and classify at exit. Store as trade attributes.

---

## PART 4: P&L PATH CLASSIFICATION

At trade exit, classify the P&L trajectory into one of 4 categories:

| Path | Definition | Meaning |
|------|-----------|---------|
| `direct` | Never crossed entry price after moving in trade direction | Clean winner or loser |
| `green_then_red` | Went green (>0 unrealized), then closed at loss | LSG trade |
| `red_then_green` | Went red first, then recovered to profit | Survived drawdown |
| `choppy` | Crossed entry price 3+ times | Indecisive, noise |

**Implementation:** Track entry-price crossings during per-bar loop. Count crossings, track whether trade was ever green/red. Classify at exit.

---

## PART 5: LSG CATEGORIZATION (4 categories)

For every losing trade where `saw_green=True`, categorize the failure mode:

| Category | Condition | Meaning |
|----------|----------|---------|
| A: Fast reversal | time_in_green < 3 bars | Entry timing problem |
| B: Slow bleed | time_in_green > 10 bars | Trail not tight enough |
| C: Near-TP miss | MFE > 80% of TP target | TP too wide or add scale-out |
| D: BE failure | MFE > `be_trigger_atr` (default 0.5 ATR) but BE not raised | BE logic bug or delay |

**Metrics added to results dict:**
```
lsg_cat_a_pct     -- % of LSG losers that are fast reversals
lsg_cat_b_pct     -- % of LSG losers that are slow bleeds
lsg_cat_c_pct     -- % of LSG losers that are near-TP misses
lsg_cat_d_pct     -- % of LSG losers that are BE failures
avg_loser_mfe     -- mean MFE of losing trades
avg_loser_green_bars -- mean bars in green for LSG losers
```

**Note:** Categories computed from existing MFE/trade data. `time_in_green` needs to be tracked during per-bar loop (counter increment while unrealized > 0). `saw_green` is already tracked.

---

## PART 6: PER-TRADE PARQUET OUTPUT

After backtest completes, write all trades to a parquet file:

**Path:** `results/trades_{symbol}_{timeframe}.parquet`

**Schema:** One row per trade. All existing trade fields (including `grade`) + 11 entry-state fields + 14 lifecycle fields + LSG category.

**Columns (estimated ~42 per trade):**
```
# Existing trade fields (15)
trade_id, symbol, direction, grade, entry_bar, exit_bar,
entry_price, exit_price, pnl, commission, net_pnl,
mfe, mae, saw_green, exit_reason,

# Entry state (11 fields from Part 2)
entry_stoch9_value, entry_stoch9_direction,
entry_stoch14_value, entry_stoch40_value,
entry_stoch60_value, entry_stoch60_d,
entry_ripster_cloud, entry_ripster_expanding,
entry_avwap_distance, entry_atr, entry_vol_ratio,

# Lifecycle (14 fields from Part 3)
life_bars, life_stoch9_min, life_stoch9_max, life_stoch9_trend,
life_stoch9_crossed_signal, life_ripster_flip,
life_ripster_width_change,
life_avwap_max_dist, life_avwap_end_dist,
life_vol_avg, life_vol_trend,
life_mfe_bar, life_mae_bar, life_pnl_path,

# LSG category (if losing trade with saw_green)
lsg_category
```

**Note:** `grade` in existing fields IS the entry grade. No separate `entry_grade` column needed. BBWP fields (`entry_bbwp_value`, `entry_bbwp_spectrum`, `life_bbwp_delta`) deferred until Python BBWP port.

**Size estimate:** ~42 columns x ~7K trades/coin x 400 coins = ~2.8M rows total. At ~170 bytes/row compressed = ~476MB across 400 per-coin files (~1.2MB each). Manageable.

**When to write:** After backtest completes, before returning results. Controlled by flag (always write in sweep mode, optional in single mode).

---

## ENTRY-STATE AGGREGATES FOR SWEEP CSV

When Spec A's sweep runs with v385 backtester, these per-coin aggregates can be added to the sweep CSV. Dashboard v3 uses `.get()` so these are optional:

```
avg_winner_entry_stoch9, avg_lsg_entry_stoch9,
avg_winner_avwap_dist, avg_lsg_avwap_dist,
winner_ripster_expanding_pct, lsg_ripster_expanding_pct
```

These show the entry quality difference between winners and LSG losers at the coin level. Full per-trade detail is in the parquet files.

---

## IMPLEMENTATION NOTES

### What touches the per-bar loop:
- Entry-state snapshot (at trade open -- 11 value reads)
- Lifecycle accumulator updates (per bar while position open -- min/max/sum)
- time_in_green counter (per bar while position open)
- Entry-price crossing counter (for P&L path classification)

### What does NOT touch the per-bar loop:
- 12 post-loop metrics (computed from `trades` list after loop)
- LSG categorization (computed at exit from accumulated data)
- Parquet write (after loop)

### Version bump rationale:
Entry-state snapshots and lifecycle tracking modify the per-bar execution loop. This is NOT a metrics-only change. It warrants a new file (`backtester_v385.py`) so v384 remains the known-good baseline.

---

## DASHBOARD INTEGRATION (how Spec A reads this)

Dashboard v3 (Spec A) reads backtester results dict. All new keys use `.get("key", default)`:
- If v384 backtester: new metrics return 0/N/A. Dashboard works fine.
- If v385 backtester: new metrics auto-populate. Edge Quality panel, LSG breakdown, lifecycle patterns all display.

No dashboard code changes needed when v385 lands. The fallback pattern handles it.

---

## TEST SCRIPT: scripts/test_v385.py

Validates:
1. All 12 new metrics present in results dict
2. Metric values are sane (calmar >= 0, wl_ratio >= 0, streaks >= 0)
3. Entry-state fields populated for every trade (no None values)
4. Lifecycle fields populated for every trade
5. LSG categories sum to 100% for LSG losers
6. P&L path is one of 4 valid values for every trade
7. Per-trade parquet file written and readable
8. Parquet schema matches expected columns
9. Backward compatibility: v385 produces all v384 metrics unchanged
10. RIVERUSDT 5m results: net PnL within 1% of v384 (no logic change)

---

## RISKS

| Risk | Mitigation |
|------|-----------|
| Per-bar loop changes break trade logic | v385 is a NEW file, v384 untouched. Run both, compare net PnL. |
| Lifecycle tracking adds overhead | Min/max/sum are O(1) per bar. Negligible vs backtest itself. |
| Stoch9 slope calculation at exit | Use numpy polyfit on small array (trade_bars long). Fast. |
| LSG category overlap (trade fits A and C) | Priority order: C > D > B > A. First match wins. |
| Parquet write time | Per-coin file write (~1MB) takes <100ms. Not a bottleneck. |
| Missing indicator values at entry | If indicator not yet computed (warmup bars), set to NaN. |

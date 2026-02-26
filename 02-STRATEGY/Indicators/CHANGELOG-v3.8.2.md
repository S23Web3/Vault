# Four Pillars v3.8.2 Changelog

## Version 3.8.2 (2026-02-11)

### Summary
v3.8.2 replaces v3.8's fixed ATR SL/TP + breakeven system with an **AVWAP-based 3-stage trailing stop**, adds **sigma band scaling (adds)**, **post-stop re-entry via limit orders**, and **multi-position tracking** with 4 independent slots. No take profit — positions run until the trailing stop is hit.

### Root Cause for v3.8.2
v3.8 backtesting revealed a **critical execution order bug**: `strategy.exit()` was called before stop levels were updated, causing exits on stale SL values. Additionally, 223 trades that should have triggered BE raise did not progress optimally. v3.8.2 addresses both by redesigning the entire position management system.

---

## Changes from v3.8

### NEW: AVWAP 3-Stage Stop Loss

**Replaces:** Fixed ATR SL + ATR-based breakeven raise

| Stage | SL Level | Trigger to Next |
|-------|----------|-----------------|
| 1 | AVWAP ±2σ | Price hits opposite 2σ band |
| 2 | AVWAP ± ATR | After 5 bars in Stage 2 |
| 3 | Cloud 3 ± ATR | Final — trails until stopped |

- Each position anchors its own AVWAP from entry bar
- Sigma = volume-weighted standard deviation with ATR floor
- Ratchet guard: SL only moves in favorable direction

### NEW: Multi-Position Tracking (4 Slots)

**Replaces:** Single position tracking with scalar variables

- 4 parallel arrays track: entry, bar, direction, stage, SL, AVWAP, grade, ID
- Each position is fully independent
- `pyramiding=4` in strategy settings
- Maximum configurable via `i_maxPositions`

### NEW: AVWAP Sigma Band Adds

**Concept:** Scale into positions at mean-reversion levels

- LONG: When price dips to position's AVWAP - 2σ → LIMIT BUY at AVWAP - 1σ
- SHORT: When price rises to position's AVWAP + 2σ → LIMIT SELL at AVWAP + 1σ
- Cancel unfilled after 3 bars (`i_cancelBars`)
- One pending limit at a time
- AVWAP age limit prevents adds on stale positions (`i_maxAvwapAge`: 50 bars)

### NEW: AVWAP Re-entry After Stop-Out

**Concept:** After stop-out, re-enter using the frozen AVWAP from the stopped position

- Saves AVWAP center + sigma when position is stopped out
- For 5 bars (`i_reentryWindow`), monitors for price reaching frozen 2σ
- Places LIMIT order at frozen 1σ for re-entry
- Single attempt — clears after placing limit regardless of fill

### FIX: Execution Order Bug

**v3.8 bug:** `strategy.exit()` called before SL was updated for the current bar
**v3.8.2 fix:** Per-bar processing order:
1. Accumulate AVWAP data
2. Compute bands
3. Check stage transitions
4. Compute + ratchet SL
5. Issue `strategy.exit()` with updated SL
6. Clean up closed positions
7. Process pending limits
8. Check new entries

### REMOVED from v3.8

| Feature | Reason |
|---------|--------|
| Fixed ATR SL (`i_slMult`) | Replaced by AVWAP 3-stage SL |
| Fixed ATR TP (`i_tpMult`) | Runner strategy — no TP |
| ATR-based BE raise | Replaced by stage progression |
| Fixed $ BE raise | Replaced by stage progression |
| MFE/MAE dashboard display | Moved to Python backtest analytics |
| Single position vars | Replaced by 4-slot arrays |

### UNCHANGED from v3.8

- Stochastic signal generation (A/B/C grades, two-stage state machine)
- Cloud 3 directional filter (always on)
- Cloud 2 re-entry logic
- Cooldown gate (3 bars default)
- Commission: $8/order ($16 RT)
- Ripster EMA settings (5/12, 34/50, 72/89)
- Dashboard layout (expanded with position grid)

---

## New Input Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `i_atrLen` | 14 | ATR period for sigma floor + SL buffers |
| `i_sigmaFloor` | 0.5 | Min sigma as ATR multiple (prevents zero bands) |
| `i_stage1to2` | opposite_2sigma | Stage 1→2 trigger: opposite 2σ hit, or bar count |
| `i_stage2Bars` | 5 | Duration of Stage 2 before Cloud 3 trail |
| `i_slAtrMult` | 1.0 | ATR buffer for Stage 2/3 stop distance |
| `i_cooldown` | 3 | Minimum bars between entries |
| `i_maxPositions` | 4 | Maximum simultaneous positions |
| `i_enableAdds` | true | Enable AVWAP sigma band adds |
| `i_enableReentry` | true | Enable post-stop AVWAP re-entry |
| `i_cancelBars` | 3 | Cancel unfilled limit orders after N bars |
| `i_reentryWindow` | 5 | Bars after stop-out for re-entry eligibility |
| `i_maxAvwapAge` | 50 | Max AVWAP age for add eligibility |

---

## Removed Input Parameters

| Parameter | Was Default | Replaced By |
|-----------|-------------|-------------|
| `i_slMult` | 1.0 ATR | AVWAP 3-stage SL |
| `i_tpMult` | 1.5 ATR | No TP (runner) |
| `i_useATR_BE` | true | Stage progression |
| `i_beTrigger` | 0.5 ATR | Stage 1→2 trigger |
| `i_beLock` | 0.3 ATR | Stage 2 SL tightening |
| `i_beFixed` | $2.0 | Removed entirely |

---

## Expected Performance Impact

| Metric | Direction | Reason |
|--------|-----------|--------|
| Total Trades | ↑ 20-50% | Adds + re-entries create more entries |
| Win Rate | ↓ 5-10% | More entries, some adds will fail |
| Avg Winner | ↑↑ 30-100% | No TP, runners catch full moves |
| Avg Loser | ≈ Same | Stage 1 SL similar to v3.8 initial SL |
| Profit Factor | ↑ | Larger winners offset slightly lower win rate |
| Max Drawdown | ↑ | Pyramiding increases exposure during drawdowns |
| Sharpe | TBD | Dependent on add/re-entry success rates |

---

## Files

| File | Type | Size |
|------|------|------|
| `four_pillars_v3_8_2.pine` | Indicator | 16.8 KB |
| `four_pillars_v3_8_2_strategy.pine` | Strategy | 43.6 KB |
| `V3.8.2-COMPLETE-LOGIC.md` | Documentation | ~12 KB |
| `CHANGELOG-v3.8.2.md` | This file | ~5 KB |
| `Build382.txt` | Build spec | ~0.5 KB |

---

## Version History

- **v3.8.2** (2026-02-11): AVWAP 3-stage SL, multi-position, adds, re-entry, execution order fix
- **v3.8** (2026-02-09): Cloud 3 filter, ATR-based BE, MFE/MAE tracking, $8 commission
- **v3.7.1** (2026-02-05): Cooldown gate, phantom trade fix, $6 commission
- **v3.7** (2026-02-04): Rebate farming architecture, tight SL/TP, free flips
- **v3.6** (2026-01-28): AVWAP SL, separate order IDs
- **v3.5.1** (2026-01-25): Cloud 3 trail, single order ID
- **v3.3** (2026-01-15): Four Pillars core logic (A/B/C signals)

---

## Deployment

1. Test on TradingView: UNIUSDT 2m, 3-month backtest
2. Compare vs v3.8 results
3. Git push: `https://github.com/S23Web3/ni9htw4lker`
4. Run Python backtest sweep on 399 cached coins
5. Feed results to VINCE ML pipeline

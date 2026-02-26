# v3.8.2 AVWAP Trailing Strategy Build Session
**Date:** 2026-02-11
**Duration:** ~90 min (context compacted once)
**Files:** 4 created, 0 overwritten

---

## Scope of Work

Build Four Pillars v3.8.2 -- replace v3.8's fixed ATR SL/TP with AVWAP-based 3-stage trailing stop. Keep stochastic entries unchanged.

### Files Created
1. `02-STRATEGY/Indicators/four_pillars_v3_8_2_strategy.pine` (~935 lines)
2. `02-STRATEGY/Indicators/four_pillars_v3_8_2.pine` (~345 lines)
3. `02-STRATEGY/Indicators/V3.8.2-COMPLETE-LOGIC.md` (~154 lines)
4. `02-STRATEGY/Indicators/CHANGELOG-v3.8.2.md` (auto-enhanced by hook to ~169 lines)

---

## Architecture Decisions

### Entry System: Unchanged from v3.8
- Stochastic A/B/C rotation signals (9-3/14-3/40-3/60-10 Raw K)
- Cloud 3 directional filter (ALWAYS ON)
- Cooldown gate (3 bars min between entries)
- B/C open fresh, Cloud 2 re-entry

### AVWAP SL System: NEW 3-Stage
| Stage | SL Level | Transition |
|-------|----------|------------|
| 1 | AVWAP +/-2sigma | Opposite 2sigma hit |
| 2 | AVWAP +/- ATR | 5 bars elapsed |
| 3 | Cloud 3 +/- ATR | Trails until hit |

- Each position gets own AVWAP anchored from entry bar
- Sigma = volume-weighted stdev with ATR floor (prevents sigma=0 on bar 1)
- Ratchet guard: SL only moves favorably

### Pyramiding: 4 Independent Positions
- Array-based tracking (4 fixed slots per attribute)
- Unique entry IDs: L1, S2, L3... (counter never resets)
- $2,500 per position (4 x $2,500 = $10,000 total)

### AVWAP Adds (Scale-In)
- Price hits 2sigma from active position's AVWAP -> LIMIT at 1sigma
- Cancel unfilled after 3 bars
- One pending limit at a time
- AVWAP age limit (50 bars) prevents stale adds

### AVWAP Re-entry (Post-Stop)
- 5-bar window after stop-out
- Frozen AVWAP/sigma from stopped position
- LIMIT at 1sigma when price hits 2sigma
- Single attempt, then expires

---

## Bugs Found During Code Review (3)

### BUG 1 -- CRITICAL: strategy.cancel_all() wiping exits
- `strategy.cancel_all()` was in A-entry logic (lines 621, 632)
- With pyramiding=4, this cancels exit orders for ALL existing positions
- Existing positions lose SL protection for one full bar
- **Fix**: Removed entirely. Unique IDs per position = no order collisions.

### BUG 2 -- CRITICAL: Duplicate entry IDs
- `next_pos_id` was only incremented on limit order FILL, not PLACEMENT
- If stochastic signal fires between add placement and fill, same counter reused
- Two entries with same ID = Pine treats as same position
- **Fix**: Increment `next_pos_id` at placement time for all 4 limit order paths. Removed increment from fill detection.

### BUG 3 -- MINOR: Dashboard entry price for limit fills
- `init_position_slot()` uses `close` as entry price
- For limit order fills, actual price is the limit price
- Cosmetic only (strategy engine tracks real P&L internally)
- **Status**: Noted, not fixed. Low priority.

---

## Key Formulas Used

### AVWAP (from v3.6 proven pattern)
```
cumPV  += hlc3 * volume
cumV   += volume
cumPV2 += hlc3 * hlc3 * volume

avwap = cumPV / cumV
variance = max((cumPV2/cumV) - (avwap*avwap), 0.0)
sigma = max(sqrt(variance), sigmaFloor * ATR)
```

### Sigma Bands
```
+2sigma = avwap + 2 * sigma    (outer band, trigger zone)
+1sigma = avwap + sigma        (inner band, limit entry zone)
-1sigma = avwap - sigma
-2sigma = avwap - 2 * sigma
```

---

## Lessons Learned

### 1. strategy.cancel_all() is dangerous with pyramiding > 1
With multiple independent positions, `cancel_all()` wipes exits for ALL positions, not just the one being replaced. Use unique IDs and never need cancel_all.

### 2. Entry ID counters must increment at placement, not fill
For limit orders, the ID is created at placement time. If the counter isn't bumped immediately, another entry between placement and fill reuses the same ID. Pine Script merges same-ID orders.

### 3. AVWAP anchor point matters enormously
v3.6 used entry-bar anchoring (proven). AVWAP Anchor Assistant v1 used swing-based anchoring (different purpose). v3.8.2 correctly uses entry-bar anchoring per the user's spec.

### 4. ATR floor on sigma prevents edge case failures
On bar 1 after entry, cumPV2 variance = 0 (single data point). Without the ATR floor, all sigma bands collapse to zero width. The floor (`0.5 * ATR`) gives meaningful band width from the first bar.

### 5. Execution order is the #1 source of strategy bugs
v3.8 checked exits before updating stops. v3.8.2 fixes this by running the AVWAP update + SL computation loop BEFORE any position cleanup or new entries. Order: accumulate -> compute -> transition -> ratchet -> exit -> cleanup -> entries.

---

## Reference Sources
- `four_pillars_v3_8_strategy.pine` -- Base stochastic entry logic (575 lines)
- `four_pillars_v3_6_strategy.pine` -- AVWAP cumPV2 variance formula (lines 488-516)
- `avwap_anchor_assistant_v1.pine` -- Pivot backfill pattern reference
- `.claude/skills/pinescript/pinescript coding SKILL.md` -- Pine v6 reference (621 lines)
- `Build382.txt` -- User's build spec
- `V3.8.2-COMPLETE-LOGIC.md` -- Full logic documentation

---

## Next Steps
1. Git push to ni9htw4lker repo
2. Test strategy on TradingView (RIVERUSDT 5m)
3. Compare with Python backtest results
4. If validated, update Python backtester with AVWAP trailing logic

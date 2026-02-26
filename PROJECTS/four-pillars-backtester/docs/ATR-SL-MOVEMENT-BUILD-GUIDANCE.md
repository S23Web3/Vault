# ATR Stop Loss & Take Profit Movement — Build Guidance

**Version:** 2.0
**Date:** 2026-02-05
**Status:** Specification only — DO NOT BUILD yet
**Context:** Extends Four Pillars v3.3 position management logic

---

## CONCEPT

Once in a position, SL and TP are NOT static. They move in favor of the trade through **three phases**, triggered by Ripster EMA cloud crossovers, culminating in a **continuous ATR trail** once the trend is confirmed through slower clouds. The goal is to let winners be bigger winners — stay in the meat of a trending move instead of taking profit early and re-entering pullbacks that get stopped out repeatedly.

**Core problem solved:** With static SL/TP, the system takes profit, then reverses into the pullback, gets stopped, reverses again, gets stopped again. A strong trend should be ONE trade that trails the move, not a series of entries and exits.

---

## RIPSTER CLOUD REFERENCE

| Cloud | Short EMA | Long EMA | Role in this system |
|-------|-----------|----------|---------------------|
| Cloud 1 | EMA 8 | EMA 9 | Not used for SL/TP movement |
| Cloud 2 | EMA 5 | EMA 12 | **Phase 1 trigger** — first SL/TP adjustment. **EXIT trigger** when flips against trade |
| Cloud 3 | EMA 34 | EMA 50 | **Phase 2 trigger** — second SL/TP adjustment |
| Cloud 4 | EMA 72 | EMA 89 | **Phase 3 trigger** — continuous trail activation (with Cloud 3) |
| Cloud 5 | EMA 180 | EMA 200 | Not used (macro trend reference) |

---

## PHASE 1 — CLOUD 2 CROSS (EMA 5/12)

### Trigger condition
Cloud 2 crosses **in trade direction** while position is open:
- LONG: EMA 5 crosses ABOVE EMA 12
- SHORT: EMA 5 crosses BELOW EMA 12

### LONG position — SL movement
1. On the bar where Cloud 2 crosses bullish:
2. Find that candle's **low**
3. New SL = `candle_low - (1 × ATR)`
4. SL moves UP from original position (locking profit / reducing risk)
5. Only move SL if new level is HIGHER than current SL (never move SL against the trade)

### LONG position — TP movement
1. TP moves UP by 1 ATR: `current_TP + (1 × ATR)`
2. Trade is trending — TP expands to let the trade run further

### SHORT position — SL movement
1. On the bar where Cloud 2 crosses bearish:
2. Find that candle's **high**
3. New SL = `candle_high + (1 × ATR)`
4. SL moves DOWN from original position (locking profit / reducing risk)
5. Only move SL if new level is LOWER than current SL (never move SL against the trade)

### SHORT position — TP movement
1. TP moves DOWN by 1 ATR: `current_TP - (1 × ATR)`
2. Trade is trending — TP expands to let the trade run further

### Phase 1 summary
SL tightens (locks profit), TP expands (lets trade run). Momentum confirmed through fast cloud — reward increases while risk decreases.

---

## PHASE 2 — CLOUD 3 CROSS (EMA 34/50)

### Trigger condition
Cloud 3 crosses **in trade direction** while position is still open:
- LONG: EMA 34 crosses ABOVE EMA 50
- SHORT: EMA 34 crosses BELOW EMA 50

**IMPORTANT:** Cross must occur AFTER entry bar. If Cloud 3 is already crossed at entry, Phase 2 waits for a fresh cross. Otherwise you'd get an immediate double adjustment on a trade that just entered.

### LONG position
- SL moves UP by 1 ATR: `current_SL + (1 × ATR)` — further locks profit
- TP moves UP by 1 ATR: `current_TP + (1 × ATR)` — extends target with the trade

### SHORT position
- SL moves DOWN by 1 ATR: `current_SL - (1 × ATR)` — further locks profit
- TP moves DOWN by 1 ATR: `current_TP - (1 × ATR)` — extends target with the trade

### Phase 2 summary
Both SL and TP move WITH the trade. Momentum has confirmed through a slower cloud — the system now lets the trade run further while keeping SL tight.

---

## PHASE 3 — CONTINUOUS ATR TRAIL (CLOUD 3 + CLOUD 4 SYNC)

### Trigger condition
Cloud 3 (EMA 34/50) AND Cloud 4 (EMA 72/89) are BOTH crossed in trade direction and moving synchronously:
- LONG: EMA 34 > EMA 50 AND EMA 72 > EMA 89
- SHORT: EMA 34 < EMA 50 AND EMA 72 < EMA 89

Phase 3 activates when both conditions are true simultaneously (Cloud 4 may already be aligned, or may cross after Phase 2 — either way, sync of both triggers Phase 3).

### Behavior
- **TP is REMOVED** — no fixed target. The trail handles the exit.
- **SL becomes a continuous ATR trail:**
  - LONG: SL = highest high since entry - (1 × ATR). Updates each bar if a new high is made.
  - SHORT: SL = lowest low since entry - (1 × ATR). Updates each bar if a new low is made.
- SL guard still applies: trail only moves in favorable direction, never back.

### Phase 3 summary
The trend is confirmed across medium and slow clouds. Stop riding — let the continuous trail do the work. The trade stays open until the trail is hit or Cloud 2 flips against (see EXIT RULES below).

---

## EXIT RULES

### Primary exit: Cloud 2 (EMA 5/12) flips against trade = HARD CLOSE

If Cloud 2 crosses **against** the trade direction at any phase:
- LONG: EMA 5 crosses BELOW EMA 12 → **close position immediately**
- SHORT: EMA 5 crosses ABOVE EMA 12 → **close position immediately**

This is the fastest momentum cloud. When it flips against you, the trend's momentum is dying. Exit clean, preserve profit.

### Secondary exits (unchanged from 4P v3.3)
- SL hit (at whatever phase level it's at)
- TP hit (Phase 0, 1, or 2 — does not apply in Phase 3 where TP is removed)
- Rotation failure exit (stochastic rotation check still applies)

### Known tradeoff: Cloud 2 false flips
Cloud 2 may briefly flip against the trade and then resume in the original direction. This causes an early exit — you leave the trade and miss the continuation. **This is accepted.** The cost of occasionally exiting early is far less than the cost of riding a real reversal down. There is always a next trade. If Cloud 2 flips back and a new 4P signal fires in the same direction, the ADD logic (below) handles re-entry.

---

## ADD SIGNALS — PULLBACK WITHIN TREND

### Concept
ADDs are NOT full 4P signals. They detect the fastest stochastic (9-3) pulling back into the opposite zone and then exiting, while the slower stochastics (40-3, 60-10) confirm the trend is still intact by staying on their side of the midline. This catches the **pullback-within-trend** — the moment the fast stoch says "dip bought" or "rally sold."

### SHORT ADD trigger
1. Already in a SHORT position
2. Stoch 9-3 enters the overbought zone (goes > 70)
3. Stoch 9-3 exits the zone (crosses back below 70) — **this bar fires the ADD**
4. During this, stoch 40-3 stays below 52 AND stoch 60-10 stays below 52
5. The 52 threshold confirms bearish bias is intact (hasn't crossed midline)

### LONG ADD trigger
1. Already in a LONG position
2. Stoch 9-3 enters the oversold zone (goes < 30)
3. Stoch 9-3 exits the zone (crosses back above 30) — **this bar fires the ADD**
4. During this, stoch 40-3 stays above 48 AND stoch 60-10 stays above 48
5. The 48 threshold confirms bullish bias is intact (hasn't crossed midline)

### Behavior
1. Label the signal **"ADD"** on the chart (smaller marker than entry)
2. **No SL/TP change** — the ADD inherits the live trade's SL/TP and phase. Positions aggregate on the platform, so only the original trade's management matters.
3. Phase state does NOT reset on ADD
4. Multiple ADDs can fire during a single position

### Configurable thresholds
- 9-3 zone levels: 30 (long) / 70 (short) — configurable
- Midline thresholds: 48 (long) / 52 (short) — configurable, offset from 50 for buffer

### Visual
- ADD entries shown as smaller triangles with "ADD" label
- Dashboard shows number of entries in current position

---

## PHASE SEQUENCE DIAGRAM

```
ENTRY (4P signal fires)
│
│  SL = entry ± (2 × ATR)     [original, from 4P v3.3]
│  TP = entry ± (4 × ATR)     [original, from 4P v3.3]
│
▼
PHASE 1: Cloud 2 (EMA 5/12) crosses in trade direction
│
│  LONG:
│    SL → candle_low - (1 × ATR)    [anchored to cross candle]
│    TP → current_TP + (1 × ATR)    [expands]
│  SHORT:
│    SL → candle_high + (1 × ATR)   [anchored to cross candle]
│    TP → current_TP - (1 × ATR)    [expands]
│
│  Guard: SL only moves in favorable direction, never against trade
│
▼
PHASE 2: Cloud 3 (EMA 34/50) crosses in trade direction (fresh cross after entry)
│
│  SL → current_SL ± (1 × ATR)      [shifts with trade]
│  TP → current_TP ± (1 × ATR)      [extends with trade]
│
│  Guard: SL only moves in favorable direction, never against trade
│
▼
PHASE 3: Cloud 3 + Cloud 4 (EMA 72/89) both in sync
│
│  TP REMOVED — continuous ATR trail activated
│  SL = most favorable price ± (1 × ATR), updates each bar
│
│  Guard: Trail only moves in favorable direction
│
├── ADD: 9-3 pullback exit + 40/60 hold trend side of midline
│   Label "ADD", no SL/TP change, inherits live trade
│
▼
EXIT CONDITIONS (checked every bar, any phase):
│
│  1. Cloud 2 (EMA 5/12) flips against trade → HARD CLOSE (priority)
│  2. SL hit → close position
│  3. TP hit → close position (Phase 0-2 only, no TP in Phase 3)
│  4. Rotation failure → close position (stochastic check)
```

---

## RULES & GUARDS

1. **SL can only move in favorable direction** — LONG: SL only moves up. SHORT: SL only moves down. If calculated new SL is worse than current, ignore the move.
2. **Phase 1 must happen before Phase 2** — Cloud 3 cross without prior Cloud 2 cross does NOT trigger movement. Track phase state.
3. **Each phase triggers ONCE per position** — Cloud 2 crossing multiple times does not keep adjusting. First valid cross per phase only. (Phase 3 trail is continuous by nature.)
4. **Fresh cross required** — If a cloud is already crossed at entry, it does NOT count. The cross must happen after the entry bar.
5. **ATR source** — Use the same chart timeframe ATR (14-period) already in 4P v3.3. ATR is evaluated at the moment of phase trigger (not at entry), since volatility may have changed.
6. **Rotation failure exit still applies** — If stochastics stop following within the rotation check window, position exits regardless of SL/TP movement state.
7. **Cloud 2 against = hard close** — Overrides all other exit logic. If Cloud 2 flips against trade direction, close immediately regardless of phase or SL/TP levels.
8. **ADD signals do not reset phase** — Pyramiding into the position continues in the current phase.

---

## STATE TRACKING REQUIRED

```
var int sl_phase = 0              // 0=initial, 1=Cloud2 adjusted, 2=Cloud3 adjusted, 3=trailing
var float current_sl = na         // tracks live SL level
var float current_tp = na         // tracks live TP level
var float trail_extreme = na      // Phase 3: highest high (long) or lowest low (short)
var int add_count = 0             // number of ADD entries taken
var bool cloud3_crossed_after_entry = false  // tracks fresh cross requirement
var bool cloud4_crossed_after_entry = false  // tracks fresh cross requirement
var int entry_bar = na            // bar_index at entry, for fresh cross detection
```

On position close: reset all state variables to initial values.

---

## VISUAL REQUIREMENTS

- SL line color/style should change per phase:
  - Phase 0 (initial): Red solid
  - Phase 1 (Cloud 2): Red dotted — label "SL1"
  - Phase 2 (Cloud 3): Orange dashed — label "SL2"
  - Phase 3 (trailing): Yellow dashed — label "TRAIL"
- TP line:
  - Phase 0: Green solid
  - Phase 1: Green dotted — label "TP1"
  - Phase 2: Lime dashed — label "TP2"
  - Phase 3: No TP line (removed)
- ADD entries: Smaller triangle with "ADD" text
- Dashboard should show:
  - Current phase (0/1/2/3)
  - Number of entries (1 + ADD count)
  - Current SL and TP levels
  - Cloud 2 status (in-favor / against)

---

## INTEGRATION NOTES

- This logic replaces the static SL/TP in 4P v3.3 lines ~120-155
- The counter-trend SL tightening (mult 1.0 under cloud) from v3.3 remains for INITIAL placement only
- Cloud 2 (EMA 5/12) and Cloud 4 (EMA 72/89) values must be calculated inside the indicator (currently only Cloud 3 EMA 34/50 exists in 4P v3.3 — Cloud 2 and Cloud 4 need to be added)
- The ATR PM standalone indicator spec from Feb 2 (HTF trailing, n8n momentum validation) is a SEPARATE concern for exchange-side execution — this build guidance is for the TradingView chart-side position management only

---

## RESOLVED QUESTIONS

1. **Cloud 2 cross against trade** — **HARD CLOSE.** Cloud 2 flipping against the trade direction is an immediate exit signal at any phase. Known tradeoff: occasional false flip causes early exit, but this is accepted — better to exit clean than ride a reversal.
2. **Multiple Cloud 2 crosses** — First cross in trade direction per phase only. However, Cloud 2 crossing AGAINST is always monitored as an exit signal regardless of how many times it's crossed.
3. **Cloud 3 already crossed before entry** — Wait for a FRESH cross after entry bar. Same applies to Cloud 4 for Phase 3 activation.

---

**END OF BUILD GUIDANCE — DO NOT BUILD**

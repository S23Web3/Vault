# v3.9.1 Four Pillars — Signal Quality Rebuild

**Date:** 2026-03-04
**Context:** v3.9.0 signals don't reflect how the user actually trades. Three compounding problems:
1. The 3-phase SL movement system (Cloud 2 → Cloud 3 → Cloud 4+3 trail) is **not implemented** — position_v384 uses AVWAP center as the SL trail after N bars instead.
2. Cloud 2 hard close (immediate exit when EMA 5/12 flips against trade) is **missing entirely**.
3. Cloud 4 (EMA 72/89) is **not computed or used anywhere** — Phase 3 can never activate.

**Goal:** Build v391 as a complete, faithful implementation of the strategy as specified in `ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` v2.0.

---

## Files to Create

All new files. Never overwrite existing versions.

| New File | Replaces |
|---|---|
| `engine/position_v391.py` | `engine/position_v384.py` (for use by v391 engine only) |
| `engine/backtester_v391.py` | `engine/backtester_v390.py` |
| `signals/four_pillars_v391.py` | `signals/four_pillars_v390.py` |
| `signals/state_machine_v391.py` | `signals/state_machine_v390.py` (if signal changes needed) |
| `signals/clouds_v391.py` | Extends `signals/clouds.py` to add Cloud 4 computation |
| `scripts/build_strategy_v391.py` | Build script (creates all files, py_compiles each) |

---

## Part 1 — Clouds: Add Cloud 4

**File:** `signals/clouds_v391.py` (or extend `compute_clouds` in `signals/clouds.py`)

Currently `compute_clouds()` computes Cloud 2 (5/12), Cloud 3 (34/50), Cloud 5 (180/200) and price_pos against Cloud 3.

**Add:**
- `ema_72` and `ema_89` (Cloud 4)
- `cloud4_bull = ema_72 > ema_89`
- `cloud4_bear = ema_72 < ema_89`
- `cloud3_bull = ema_34 > ema_50` (needed for Phase 2/3 trigger detection)
- `cloud3_bear = ema_34 < ema_50`
- `cloud2_bull = ema_5 > ema_12` (needed for Phase 1 trigger and hard close)
- `cloud2_bear = ema_5 < ema_12`
- Cross detection columns (True only on the bar the cross occurs):
  - `cloud2_cross_bull` = cloud2_bull and not prev_cloud2_bull
  - `cloud2_cross_bear` = cloud2_bear and not prev_cloud2_bear
  - `cloud3_cross_bull` = cloud3_bull and not prev_cloud3_bull
  - `cloud3_cross_bear` = cloud3_bear and not prev_cloud3_bear
  - `phase3_active_long` = cloud3_bull AND cloud4_bull
  - `phase3_active_short` = cloud3_bear AND cloud4_bear

Pass all of these through the signal pipeline so the backtester can access them per-bar.

---

## Part 2 — Signal Pipeline: v391

**File:** `signals/four_pillars_v391.py`

Nearly identical to `four_pillars_v390.py`. Key changes:
- Call `compute_clouds_v391()` instead of `compute_clouds()` (to pick up Cloud 4 + cross columns)
- Pass the new cloud cross columns through to the output df so `backtester_v391` can read them
- State machine: **keep `state_machine_v390.py` unchanged** — stochastic signal logic (A/B/reentry) is structurally correct. Only the position management is broken.

**State machine stays at v390.** No changes to signal detection.

---

## Part 3 — Position: v391 (THE CRITICAL REBUILD)

**File:** `engine/position_v391.py`

Replace the AVWAP-trail-as-SL with the correct 3-phase system. AVWAP moves to its correct role: ADD entry trigger + scale-out trigger only.

### SL Phase State

```python
self.sl_phase = 0          # 0=initial, 1=cloud2_adjusted, 2=cloud3_adjusted, 3=trail
self.phase1_done = False   # each phase triggers once only
self.phase2_done = False
self.trail_extreme = None  # Phase 3: highest high (long) / lowest low (short)
self.cloud3_crossed_after_entry = False   # fresh cross guard
self.phase3_ever_active = False           # once phase 3 starts, never resets to TP
```

### Phase 0 — Initial SL/TP (entry)

```
LONG:  sl = entry - (2 × ATR),  tp = entry + (4 × ATR)
SHORT: sl = entry + (2 × ATR),  tp = entry - (4 × ATR)
```

tp_mult parameter controls the multiplier (default 4.0).

### Phase 1 Trigger — Cloud 2 cross IN trade direction (first time after entry)

Inputs from df: `cloud2_cross_bull[i]` (long trigger), `cloud2_cross_bear[i]` (short trigger)

**Condition:** cross occurred on this bar AND `phase1_done == False` AND bar_index > entry_bar

**LONG action:**
- candle_low = low at the cross bar
- new_sl = candle_low - (1 × ATR at cross bar)
- Only apply if new_sl > current_sl (guard: never move SL against trade)
- new_tp = current_tp + (1 × ATR)
- Set phase1_done = True, sl_phase = 1

**SHORT action:** Mirror (candle_high + ATR, only if lower than current_sl, tp - ATR)

### Phase 2 Trigger — Cloud 3 cross IN trade direction (fresh cross after entry bar)

Inputs: `cloud3_cross_bull[i]` / `cloud3_cross_bear[i]`

**Condition:** cross on this bar AND `phase1_done == True` AND `phase2_done == False` AND fresh (bar > entry_bar)

**LONG action:**
- new_sl = current_sl + (1 × ATR)
- new_tp = current_tp + (1 × ATR)
- Guard: only if new_sl > current_sl
- Set phase2_done = True, sl_phase = 2

**SHORT action:** Mirror

### Phase 3 Trigger — Cloud 3 AND Cloud 4 both in sync

Inputs: `phase3_active_long[i]` / `phase3_active_short[i]`

**Condition:** sync state is True on this bar AND phase3_ever_active == False

**Action:**
- tp = None (REMOVED)
- trail_extreme = current high (long) or current low (short)
- sl_phase = 3
- phase3_ever_active = True

**Phase 3 trail (every bar while active):**
```
LONG:
  trail_extreme = max(trail_extreme, high[i])
  trail_sl = trail_extreme - (1 × ATR)
  if trail_sl > sl: sl = trail_sl   # guard: never move against trade

SHORT:
  trail_extreme = min(trail_extreme, low[i])
  trail_sl = trail_extreme + (1 × ATR)
  if trail_sl < sl: sl = trail_sl
```

### Hard Close — Cloud 2 flips AGAINST trade (any phase, highest priority)

Input: `cloud2_cross_bear[i]` (long hard close) / `cloud2_cross_bull[i]` (short hard close)

This is checked BEFORE SL/TP in the engine's exit loop. Returns exit reason "CLOUD2_CLOSE".

### Breakeven (unchanged from v384 — already correct)

BE trigger: when high (long) >= entry + be_trigger_atr × ATR
BE lock: sl moves to entry + be_lock_atr × ATR
Checked before phase updates on each bar. If be_raised, skip further SL movement unless phase update would improve it.

Note: BE and phases can coexist — BE fires fast on spikes, phase moves continue trailing afterward.

### AVWAP — Correct Role

AVWAP is kept for:
1. ADD entry trigger: when price touches AVWAP -2sigma (long) or +2sigma (short) while in position
2. Scale-out trigger: at checkpoints, if close at +2sigma (long) or -2sigma (short)

AVWAP center is **NOT** used as SL trail anymore.

### ADD Signals (stochastic-based, per spec)

Already partially in v390 engine but using AVWAP price for trigger. Per `ATR-SL-MOVEMENT-BUILD-GUIDANCE.md`:

**LONG ADD trigger:**
1. In LONG position
2. stoch_9 was > 70 (entered overbought) on a recent bar
3. stoch_9 crosses back below 70 on this bar — fire ADD
4. During that: stoch_40 stayed >= 48 AND stoch_60 stayed >= 48

This is a stochastic-based trigger. The AVWAP -2sigma is the **entry limit** (won't ADD if price is above AVWAP -1sigma — only ADD into dips).

---

## Part 4 — Backtester: v391

**File:** `engine/backtester_v391.py`

Key changes from `backtester_v390.py`:

1. **Import `position_v391.PositionSlot391`** instead of `position_v384.PositionSlot384`

2. **Pass cloud cross columns to position slot** — the slot needs per-bar cloud cross data to know when to advance phases. Options:
   - Pass the full arrays to `run()` and feed each bar's values into `update_bar_v391()`
   - Preferred: add `cloud2_cross_bull`, `cloud2_cross_bear`, `cloud3_cross_bull`, `cloud3_cross_bear`, `phase3_active_long`, `phase3_active_short` as parameters to `PositionSlot391.update_bar()`

3. **Hard close check before SL check:**
```python
# Check Cloud 2 hard close FIRST (highest priority exit)
for s in range(4):
    if slots[s] is None: continue
    if slots[s].check_cloud2_hard_close(cloud2_cross_bear[i], cloud2_cross_bull[i]):
        # close at close price, reason="CLOUD2_CLOSE"
        ...
```

4. **Update bar signature expanded:**
```python
slots[s].update_bar(
    i, high[i], low[i], close[i], atr[i], hlc3[i], vol[i],
    cloud2_cross_bull=cloud2_cross_bull[i],
    cloud2_cross_bear=cloud2_cross_bear[i],
    cloud3_cross_bull=cloud3_cross_bull[i],
    cloud3_cross_bear=cloud3_cross_bear[i],
    phase3_long=phase3_active_long[i],
    phase3_short=phase3_active_short[i],
)
```

5. **Trade record:** Add `sl_phase` field to trade record (0/1/2/3 — what phase when closed).

6. **ADD signal rework:** Replace AVWAP-price ADD trigger with stochastic-based ADD trigger per spec:
   - Track `stoch9_was_high` / `stoch9_was_low` per open slot
   - Fire ADD when stoch9 exits overbought/oversold while 40+60 confirm trend

---

## Files NOT Changed

- `signals/stochastics.py` — stochastic computation correct
- `signals/state_machine_v390.py` — A/B/reentry logic correct, reused as-is
- `engine/commission.py` — unchanged
- `engine/avwap.py` — unchanged (still needed for ADD limits + scale-outs)
- `engine/backtester_v385.py` — separate enrichment layer, untouched
- All dashboard files

---

## Build Script

**File:** `PROJECTS/four-pillars-backtester/scripts/build_strategy_v391.py`

Single script that:
1. Writes `signals/clouds_v391.py`
2. Writes `signals/four_pillars_v391.py`
3. Writes `engine/position_v391.py`
4. Writes `engine/backtester_v391.py`
5. After each file: `py_compile.compile(path, doraise=True)` — must pass before continuing
6. Reports PASS/FAIL per file

**Run command:** `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_strategy_v391.py"`

---

## Verification

After build script runs and all py_compile checks pass:

1. **Smoke test:** Run existing test runner against v391 on one symbol (e.g., BTCUSDT 5m)
2. **Check output:** Verify trades show `sl_phase` values > 0 (phases are actually advancing)
3. **Check exits:** Verify `CLOUD2_CLOSE` exits appear in trade list
4. **Check Phase 3:** On a trending symbol, verify TP is None and trail_extreme moves
5. **Signal count:** Compare v390 vs v391 signal count on same data — should be similar (signal layer unchanged)
6. **BE check:** Verify `be_raised=True` appears on some trades

---

## Critical Lessons to Apply

- **NEVER USE ESCAPED QUOTES IN F-STRINGS** in build scripts — use string concatenation for joins
- **MANDATORY py_compile** after every file write
- **ALL FUNCTIONS MUST HAVE DOCSTRINGS**
- **FULL PATHS EVERYWHERE** in run commands and output
- Load Python skill before writing any .py files

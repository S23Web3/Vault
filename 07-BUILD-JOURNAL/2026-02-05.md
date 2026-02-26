# Build Journal - 2026-02-05

## Sessions Summary

### Session 1: Strategy Analysis (Maxed Out)
- Reviewed Four Pillars v3.4.1 strategy backtesting version
- Validated all logic matches indicator version
- Identified toggle gap: strategy has `i_useTP`, indicator does not
- Session hit context limit before implementation

### Session 2: Toggle Implementation + Trail Fix → v3.4.2
- Logged maxed-out Session 1 to `06-CLAUDE-LOGS`
- Added `i_useTP` toggle to indicator (match strategy version)
- Added `i_useRaisingSL` toggle to indicator (disable phased SL raising)
- Changed Phase 3 trail from Cloud 3 (34/50) to Cloud 4 (72/89) — less aggressive
- Bumped version to v3.4.2

### Session 3: Major SL Rework — Continuous Cloud 3 Trail + Cloud 2 Re-entry
- Added **Cloud 2 re-entry A trade**: price crosses Cloud 2 + recent A rotation (4/4 stoch) within lookback bars = A trade
- **Removed entire phased P0→P1→P2→P3 SL system** — replaced with continuous Cloud 3 (34/50) ± 1 ATR trail every candle
- **Removed Cloud 2 flip hard close exit** — trades exit only via SL trail or TP
- File reduced from 645 → ~495 lines through simplification
- Session continued across context compression

---

## Key Changes Today

### Four Pillars v3.4.2 Indicator
**File:** `four_pillars_v3_4.pine`

#### Session 2: Toggles
| Toggle | Default | Effect When OFF |
|--------|---------|-----------------|
| `i_useTP` | ON | No TP set — exit only via SL trail |
| `i_useRaisingSL` | ON | SL stays static at entry ± ATR mult |

#### Session 3: SL System Overhaul
| Item | Before (Phased) | After (Continuous) |
|------|-----------------|-------------------|
| SL behavior | P0 static → P1 Cloud 2 → P2 Cloud 3 → P3 Cloud 4 trail | Cloud 3 ± 1 ATR, trails every candle |
| Phase variables | `phase1_done`, `phase2_done`, `sl_phase`, `phaseChanged` | None — removed entirely |
| Angle trail | Cloud 3 top+ATR on steep moves | Removed |
| Phase labels | SL1, SL2, TRAIL | Removed |
| Cloud 2 exit | Hard close on Cloud 2 flip against | **Removed** — no C2 exit |
| Exit types | SL, TP, Cloud 2 flip | SL trail, TP only |

#### New: Cloud 2 Re-entry A Trade
| Setting | Value |
|---------|-------|
| Toggle | `i_cloud2Reentry` (default ON) |
| Lookback | `i_reentryLookback` (default 10 bars) |
| Condition | Price crosses Cloud 2 + A rotation (4/4 stoch) happened within lookback |
| Grade | A |
| SL | Cloud 3 ± 1 ATR, trails every candle |
| TP | None (always trails) |

**Rationale:** The phased system created flat/static SL periods between phase jumps. Users wanted a smooth, continuous trailing SL that follows the cloud like a trendline. Cloud 2 exits are redundant when the trail handles protection — the trail will naturally tighten and stop out if the trend reverses through Cloud 3.

#### Session 3b: Trail Activation + Position Replacement + Bug Fixes

**Trail Activation Gate (Cloud 3/4 Cross):**
| Item | Value |
|------|-------|
| Condition | `ema50 > ema72` (LONG) or `ema50 < ema72` (SHORT) — Cloud 3 slow crosses Cloud 4 fast |
| Behavior | SL starts static at entry ± 2 ATR. Trail only activates after Cloud 3/4 cross |
| Persistence | Once active, stays active for duration of trade |
| Visual | Yellow = trailing, Orange = waiting for cross, Red = static (raising SL OFF) |
| Dashboard | SL row shows TRAIL / WAIT / STATIC |

**Entry While In Position (Position Replacement):**
| Item | Value |
|------|-------|
| Long condition | `not inPosition or (close < cloud3_bottom)` |
| Short condition | `not inPosition or (close > cloud3_top)` |
| Behavior | New entry replaces existing position with fresh SL/TP |

**Entry Priority Reorder:**
Re-entry A trades moved above B/C in the if/else chain:
1. A long/short (4/4 stoch)
2. Re-entry A long/short (Cloud 2 cross + recent A rotation)
3. B long/short (3/4 stoch)
4. C long/short (2/4 fast + Cloud 3)
5. ADD long/short (pullback signals)

**Inverse SL Bug Fix:**
| Bug | When entering LONG below Cloud 3 via position replacement, Cloud 3 trail pushed SL above entry price on bar 2 |
|-----|------|
| Cause | `cloud3_bottom - atr` was higher than entry when entering below Cloud 3 |
| Fix | Added `and new_sl < close` (LONG) / `and new_sl > close` (SHORT) to prevent trail from crossing current price |

**Minor Fixes:**
- Initial SL unified to always use `close ± (i_slMult * atr)` for all trade types (was using Cloud 3 reference when raising SL was ON)
- Removed `sl_long_cloud` / `sl_short_cloud` helper variables
- Removed Cloud 2 exit variables (`cloud2_cross_bull`, `cloud2_cross_bear`, `exitCloud2`)
- Removed Cloud 2 Exit alert and C2 Exit label
- Removed dashboard fuchsia warning color for Cloud 2

---

## Files Modified

| File | Status |
|------|--------|
| `four_pillars_v3_4.pine` | v3.4.2 — trail activation gate, position replacement, inverse SL fix |
| `06-CLAUDE-LOGS/2026-02-05-strategy-analysis-session.md` | Session 1 log |
| `MEMORY.md` | Updated for trail activation + position replacement |

---

### Session 4: Four Pillars v3.5 — Stochastic Smoothing Fix

**File:** `four_pillars_v3_5.pine` (new copy, v3.4.2 preserved)

**Core Fix:** Stochastic smoothing was completely missing — all 4 stochastics used raw K with no SMA smoothing. This affects signal timing and accuracy.

| Stochastic | Before (v3.4.2) | After (v3.5) |
|------------|-----------------|--------------|
| 9-3 | Raw K (no smoothing) | `ta.sma(k_raw, 3)` — Fast (single smooth) |
| 14-3 | Raw K (no smoothing) | `ta.sma(k_raw, 3)` — Fast (single smooth) |
| 40-3 | Raw K (no smoothing) | `ta.sma(k_raw, 3)` — Fast (single smooth) |
| 60-10 | Raw K (no smoothing) | `ta.sma(ta.sma(k_raw, 10), 10)` — Full (double smooth) |

**Impact:** Smoothed stochastics are less noisy — signals will fire later but more reliably. The 60-10 becomes much smoother as a macro filter (double smoothing with period 10). You will see fewer but higher-quality entries compared to v3.4.2.

**Also cleaned up from v3.4.2:**
- Removed `trail_extreme` dead code
- Fixed `i_slMult` tooltip wording

---

### Session 5: v3.5 Strategy — Backtesting Version Rewrite

**File:** `four_pillars_v3_5_strategy.pine` (complete rewrite from v3.4.1)

**Old v3.4.1 Strategy Problems (from ARCUSDT.P 5min backtest):**
| Problem | Evidence |
|---------|----------|
| `pyramiding=10` + 100% equity = margin calls | 32 of 54 exits were margin calls |
| Cloud 2 exits cut winners | Trade #28 made +10%, C2 exit killed the run |
| Old phased SL too slow | Trade #53 hit SL at -11.9% |
| Raw stochastics = noisy | 170 trades in 7 days |
| ADDs create full new positions | Explodes position size |

**v3.5 Strategy Changes:**
| Item | Old (v3.4.1-S) | New (v3.5-S) |
|------|----------------|--------------|
| Pyramiding | 10 | **1** (no stacking) |
| Stochastics | Raw K (no smoothing) | Fast/Full SMA smoothing |
| SL system | Phased P0→P1→P2→P3 | Trail activation gate (C3/C4 cross) |
| Cloud 2 exit | Hard close on flip | **Removed** |
| Cloud 2 re-entry | Not implemented | A trade (price crosses C2 + recent A) |
| Position replacement | Not implemented | Close + re-enter when price beyond C3 |
| ADD behavior | `strategy.entry()` pyramid | Informational only (count + label) |
| Angle trail | Cloud 3 top ± ATR on steep | **Removed** |
| Exit method | Manual SL/TP check | `strategy.exit()` with stop/limit |

---

## Files Modified

| File | Status |
|------|--------|
| `four_pillars_v3_4.pine` | v3.4.2 — trail activation gate, position replacement, inverse SL fix |
| `four_pillars_v3_5.pine` | v3.5 — stochastic smoothing fix |
| `four_pillars_v3_5_strategy.pine` | **NEW** — v3.5 strategy for backtesting |
| `06-CLAUDE-LOGS/2026-02-05-strategy-analysis-session.md` | Session 1 log |
| `MEMORY.md` | Updated for v3.5 |

---

### Session 6: v3.5 Strategy — Exit Bug Fix (TP Not Reflecting)

**File:** `four_pillars_v3_5_strategy.pine`

**Problem:** TP multiplier changes in settings didn't reflect on chart. Investigation found 3 bugs:

| Bug | Cause | Fix |
|-----|-------|-----|
| **Dual exit conflict** | `strategy.exit()` set SL/TP but `strategy.close_all()` also tried to close, racing to exit | Removed manual `strategy.close_all()` exit. `strategy.exit()` is sole exit handler |
| **Position replacement invisible** | `didEnterLong` edge detection: `posDir[1] != "LONG"` = false on LONG→LONG replacement → `strategy.entry()` never fires | Changed to `entryBar == bar_index` — catches all entries including same-dir replacement |
| **State desync after exit** | `strategy.exit()` fills but internal `inPosition` stays true, preventing new entries | Added `strategy.position_size == 0` sync — detects when strategy engine closes position |

**Changes Made:**
- Replaced manual exit checks (`exitSL`/`exitTP`/`exitPosDir`) with `strategy.position_size` state sync
- Entry detection: `entryBar == bar_index` replaces broken edge detection
- Removed `newEntry`/`newEntryDir` per-bar flags (unused — `entryBar` approach is simpler)
- Removed `isATrade`/`isBTrade`/`isCTrade` vars (unused in strategy execution)
- `strategy.exit()` now updates SL/TP every bar — setting changes reflect immediately

---

### Session 7: Remove Position Replacement + Clean Exit Names

**File:** `four_pillars_v3_5_strategy.pine`

**Problem:** Trade #100 (LONG at 0.04127, Feb 2 00:20) had +5.23% favorable excursion but was killed by a Replace to SHORT at 02:40. The SHORT immediately margin-called. The Replace logic was:
1. Closing winning trades to flip direction
2. Creating fragmented margin-call micro-trades from `strategy.close_all("Replace")` + `strategy.entry()` combo

**Fix — Only enter when flat:**
| Item | Before | After |
|------|--------|-------|
| `canEnterLong` | `not inPosition or (close < cloud3_bottom)` | `not inPosition` |
| `canEnterShort` | `not inPosition or (close > cloud3_top)` | `not inPosition` |
| `isReplacement` | Variable + `strategy.close_all("Replace")` | **Removed entirely** |
| `lastTradeDir` in entry blocks | Set on replacement before position flip | Only set in state sync on exit |
| Exit signal names | `XL` / `XS` | `Exit Long` / `Exit Short` |

**Impact:** No more "Replace" or "XS"/"XL" in trade list. Trades now show "Long", "Short", "Exit Long", "Exit Short" only. Positions exit exclusively via SL trail or TP hit.

---

## Known Issues (from code audit)

| Severity | Issue | Status |
|----------|-------|--------|
| **MAJOR** | Stochastic smoothing missing | **FIXED in v3.5** |
| MINOR | `trail_extreme` dead code | **FIXED in v3.4.2 + v3.5** |
| MINOR | `i_slMult` tooltip wording | **FIXED in v3.4.2 + v3.5** |
| **MAJOR** | Strategy v3.4.1 margin calls / old logic | **FIXED in v3.5-S** |
| **MAJOR** | Strategy dual exit / position replacement / state desync | **FIXED in v3.5-S Session 6** |
| **MAJOR** | Position replacement killing winners + margin call fragments | **FIXED in v3.5-S Session 7** |
| **CRITICAL** | Stochastic smoothing regression — v3.5 used SMA(K,3) instead of raw K | **FIXED in v3.5.1 Session 8** |
| **MAJOR** | Position sizing: 100% equity = margin calls | **FIXED in v3.5.1 Session 8** |
| **MAJOR** | B/C trades defaulting ON producing low-quality entries | **FIXED in v3.5.1 Session 8** |
| **MAJOR** | A trades couldn't flip direction (full quad rotation blocked by flat check) | **FIXED in v3.5.1 Session 8** |

---

### Session 8: v3.5.1 — Stochastic Root Cause Fix + Entry Logic Rework

**Files:** `four_pillars_v3_5_strategy.pine`, `four_pillars_v3_5.pine` (both bumped to v3.5.1)

**Root Cause Discovery:** User's external stochastic indicators show "Stoch 9 **1** 3" — the "1" means K smoothing = 1 (raw K, NO SMA applied). The v3.5 "smoothing fix" (Session 4) applied SMA smoothing to K, making the strategy's stochastic values equivalent to the D line, not the K line. This caused:

| Problem | Impact |
|---------|--------|
| Strategy K values delayed vs chart K values | Entries fire bars late or not at all |
| 60-10 double-smoothed (SMA(SMA(K,10),10)) | Almost never reaches 20/80, so A trades (4/4) rarely fire |
| 60-10 D was triple-smoothed | `ta.sma(stoch_60_10, 10)` on already-double-smoothed value |
| Only B/C trades firing | Because they don't require 60-10 in extreme zone |
| Valid setups on chart not taken by strategy | Strategy sees smoothed values in midrange while raw K is in zone |

**Fixes Applied:**

| Fix | Before (v3.5) | After (v3.5.1) |
|-----|---------------|----------------|
| Stochastic K | `stoch_fast()` = SMA(K,3), `stoch_full()` = SMA(SMA(K,10),10) | `stoch_k()` = raw K (no smoothing) |
| 60-10 D line | Triple-smoothed: `ta.sma(double_smoothed, 10)` | Single-smoothed: `ta.sma(raw_K, 10)` |
| Position sizing | `strategy.percent_of_equity, 100` (100% = margin calls) | `strategy.cash, 500` ($500 fixed per trade) |
| B/C defaults | `true` (ON) | `false` (OFF) — user must opt in |
| A trade entry | `canEnterLong = not inPosition` (can't flip) | `canFlipLong` allows A to close opposite and enter |
| B/C/re-entry entry | Same as A | `canEnterLong = not inPosition` (flat only) |
| Flip handling | Not possible | `strategy.close_all("Flip to Long/Short")` before A trade entry |

---

### Session 9-10: v3.6 Strategy — AVWAP + Separate A/BC Order Architecture

**File:** `four_pillars_v3_6_strategy.pine` (NEW — v3.5.1 preserved)

**Design Phase (Session 9):** Iterative Q&A to define new SL management, B/C exit conditions, and AVWAP-based trailing. Key clarifications from user:

| User Feedback | Design Impact |
|---------------|---------------|
| "14-3 can't bail out without 9-3 crossing, mathematically impossible" | Dropped 3-candle confirmation window entirely — redundant with stage machine |
| "Once scalp becomes swing, don't raise SL every time — should move with AVWAP" | AVWAP ± max(stdev, ATR) replaces Cloud 3/4 trail for A trades |
| "Cloud 2 cross is when B/C are running" | Cloud 2 is BC exit condition, NOT A trade SL event |
| "B/C are the leading trade, closed with 60-10 perspective" | Separate "Long BC"/"Short BC" order IDs with independent exits |
| "AVWAP drops, stopped out, rebounds = V-shape dip rebuy" | AVWAP recovery re-entry: price crosses back past lastAVWAP within 5 bars |
| Session VWAP "unreliable" — ANCHORED from entry | AVWAP anchored to A trade signal bar, accumulates while any trade open |
| Cloud 3/4 "almost running parallel" = B/C filter | Slope comparison: both ema50 and ema72 slopes same direction |

**v3.6 Architecture Changes:**

| Component | v3.5.1 | v3.6 |
|-----------|--------|------|
| A trade SL | Cloud 3 ± ATR (after C3/C4 cross gate) | AVWAP ± max(stdev, ATR), ratchets favorable |
| BC order ID | Same as A ("Long"/"Short") | Separate "Long BC"/"Short BC" |
| BC trade SL | Shared with A | AVWAP ± ATR (tighter), ratchets favorable |
| BC exit | SL only | SL + Cloud 2 cross against + 60-10 K/D cross in extreme zone |
| BC entry filter | None | Cloud 3/4 parallel (both slopes positive/negative) |
| Trail activation | Cloud 3/4 cross gate (binary) | AVWAP grows naturally from bar 1, stdev widens over time |
| Re-entry types | Cloud 2 only | Cloud 2 + AVWAP recovery (V-shape dip) |
| State sync | `strategy.position_size == 0` | `strategy.opentrades` loop checking entry IDs |
| Visuals | Single SL line | AVWAP line + ±1σ/±2σ bands + separate A/BC SL lines |

**New Components:**

| Component | Implementation |
|-----------|---------------|
| AVWAP calculation | `cumPV/cumVol/cumPV2` seeded on A entry, accumulates each bar |
| AVWAP stdev | `sqrt(max(cumPV2/cumVol - avwap², 0))` — variance formula |
| Cloud parallel | `c3_slope = ema50 - ema50[N]`, same for ema72, both > 0 or both < 0 |
| 60-10 BC exit | K and D both in extreme (>75 long / <25 short), K crosses D |
| AVWAP re-entry | `ta.crossover(close, lastAVWAP)` within lookback after stop-out |
| State sync loop | `strategy.opentrades.entry_id(i)` checked for " A" or " BC" |

---

### Session 11: v3.6 Indicator + Volume Flip Filter + Dashboard Fix

**Files:** `four_pillars_v3_6.pine` (NEW), `four_pillars_v3_6_strategy.pine` (updated)

**v3.6 Indicator Created:**
- Complete indicator version matching strategy architecture
- Manual exit detection (price vs SL/TP) instead of strategy engine
- Separate A/BC position tracking with boolean flags
- Entry labels (large for A, small "BC"), exit labels (SL A, TP A, SL BC, C2 BC, 60-10 BC)
- 11 alert conditions + hidden plots for JSON webhooks
- Stage machine (upgraded from v3.5.1's cross-based entries)

**Volume Flip Filter (both files):**

| Component | Implementation |
|-----------|---------------|
| Toggle | `i_useFlipVol` (bool, default true) |
| Lookback | `i_flipVolLookback` (int, default 20, min 5, max 100) |
| Threshold | `volume > math.max(avgVolLookback, avgVolSinceEntry)` |
| Scope | Only applies to A trade direction **flips**, not fresh entries from flat |
| avgVolLookback | `ta.sma(volume, i_flipVolLookback)` — rolling average over lookback bars |
| avgVolSinceEntry | `cumVolTrade / tradeBarCount` — average since current A trade entry |

**Dashboard Fix (both files):**

| Bug | `var table dash = table.new(...)` was inside `if barstate.islast` block |
|-----|------|
| Cause | `var` inside conditional scope can fail to render in some execution modes |
| Fix | Moved `var table dash` to global scope, cells still populated inside `if barstate.islast` |

---

## Files Modified

| File | Status |
|------|--------|
| `four_pillars_v3_4.pine` | v3.4.2 — trail activation gate, position replacement, inverse SL fix |
| `four_pillars_v3_5.pine` | v3.5.1 — stochastic smoothing revert to raw K |
| `four_pillars_v3_5_strategy.pine` | v3.5.1 — preserved as reference |
| `four_pillars_v3_6_strategy.pine` | v3.6 — AVWAP + A/BC + volume flip filter + dashboard fix |
| `four_pillars_v3_6.pine` | **NEW** — v3.6 indicator version |
| `06-CLAUDE-LOGS/2026-02-05-strategy-analysis-session.md` | Session 1 log |
| `MEMORY.md` | Updated for v3.6 |

---

## Session Logs
- [[2026-02-05-strategy-analysis-session]]

---

*Updated as sessions complete*

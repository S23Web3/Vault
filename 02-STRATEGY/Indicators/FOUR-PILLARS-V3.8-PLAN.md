# Four Pillars v3.8 — Build Plan

**Date**: 2026-02-07
**Base**: `four_pillars_v3_7_1_strategy.pine`
**Data source**: Monte Carlo analysis on AXS (4,790 trades) + RIVER (905 trades) — see `v3.8-MONTE-CARLO-FINDINGS.md`

---

## Problem Statement

v3.7.1 entries are high quality — flip signals have 71-84% win rate and are massively profitable. But SL/TP exits bleed money (34-38% WR). **75-100% of all losers were in profit before reversing.** Winners capture only 72-75% of their MFE, leaving $45K-$56K/month on the table per symbol.

The #1 lever is a breakeven stop: once a trade reaches a profit trigger, move the SL to lock in a guaranteed profit floor. Monte Carlo simulation (10,000 iterations) shows this single change turns baseline +$2,290 (AXS) / +$13,204 (RIVER) into median +$84,640 / +$117,502 — **100% profitable across all simulations**.

---

## Changes from v3.7.1

### Change 1 — Breakeven / Profit-Lock Stop (PRIMARY)

**What**: After a trade reaches a configurable profit trigger, move the SL from the original static level to a profit-lock level above entry (longs) or below entry (shorts).

**Inputs** (new, under "POSITION MANAGEMENT" group):
```
i_useBE       = input.bool(true, "Use Breakeven Stop")
i_beTrigger   = input.float(0.15, "BE Trigger (ATR mult)", step=0.05, minval=0.05)
i_beLock      = input.float(0.05, "BE Lock Level (ATR mult)", step=0.05, minval=0.0)
```

- `i_beTrigger`: When unrealized P&L reaches `i_beTrigger × ATR` above entry, the BE stop activates.
- `i_beLock`: The new SL moves to `entry ± i_beLock × ATR`. A value of 0.0 = true breakeven (SL at entry price). A value > 0 = guaranteed profit lock.
- Using ATR multiples (not fixed $) so the trigger adapts to each coin's volatility. This is critical for running the same strategy on AXS ($5-8 range) vs RIVER ($0.50-1.00 range).

**Why ATR, not fixed $**: The MC analysis used fixed $ thresholds ($2, $3, $4) because that's what the CSV MFE data provides. But in Pine, we don't have access to dollar P&L per bar — we have price distance from entry. ATR multiples are the standard Pine approach and auto-scale across coins and timeframes.

**Conversion reference** (for setting defaults):
- AXS: ATR(14) ≈ $0.25 on 5min. MC best scenario ≈ trigger $2 / lock $1.50 on $10K notional. $2 P&L on $10K ≈ 0.02% price move ≈ $0.0012 on AXS ≈ 0.005 ATR. But MFE in CSV is already leveraged ($2 = $0.10 unleveraged), and $0.10 / $5.50 avg price ≈ 1.8%, so $0.10 / $0.25 ATR ≈ 0.4 ATR.
- **Practical defaults**: `i_beTrigger = 0.15` ATR and `i_beLock = 0.05` ATR are conservative starting points. These should be tuned per coin via TV's strategy tester.

**State variables** (new):
```
var bool  beTriggered = false    // Has the BE trigger been hit this trade?
var float beLevel     = na       // The locked BE/profit stop level
```

**Logic** — runs every bar while `inPosition` and `i_useBE`:
```
// Calculate unrealized distance from entry
float dist = posDir == "LONG" ? (high - entryPrice) : (entryPrice - low)

// Check if trigger hit (using high/low to catch intra-bar spikes)
if not beTriggered and dist >= i_beTrigger * atr
    beTriggered := true
    beLevel     := posDir == "LONG" ?
                   entryPrice + (i_beLock * atr) :
                   entryPrice - (i_beLock * atr)

// Once triggered, override the SL
if beTriggered
    current_sl := posDir == "LONG" ?
                  math.max(current_sl, beLevel) :
                  math.min(current_sl, beLevel)
```

**Key design decisions**:
1. Use `high`/`low` for trigger detection (catches intra-bar spikes that `close` misses)
2. `beLevel` is calculated once at trigger time using that bar's ATR, then frozen — no recalculation
3. `math.max`/`math.min` ensures BE level never moves backwards (always tightens, never loosens)
4. The existing `strategy.exit()` block (lines 397-406) already uses `current_sl` so it picks up the new level automatically — no changes needed there

**Reset on new trade**: Add `beTriggered := false` and `beLevel := na` in every entry block (alongside existing `current_sl`, `current_tp` assignments) and in the state sync block (line 247-255).

---

### Change 2 — Stepped Profit Trail (OPTIONAL, off by default)

**What**: After the BE trigger fires, if price continues moving favorably, step up the lock level in increments.

**Inputs** (new):
```
i_useTrail    = input.bool(false, "Use Stepped Profit Trail")
i_trailStep   = input.float(0.15, "Trail Step Size (ATR mult)", step=0.05, minval=0.05)
i_trailLock   = input.float(0.10, "Trail Lock per Step (ATR mult)", step=0.05, minval=0.05)
```

**Logic** — runs after BE trigger, every bar:
```
if beTriggered and i_useTrail
    // How far past the trigger are we?
    float extraDist = dist - i_beTrigger * atr
    if extraDist > 0
        int steps = math.floor(extraDist / (i_trailStep * atr))
        float trailLevel = posDir == "LONG" ?
                           beLevel + (steps * i_trailLock * atr) :
                           beLevel - (steps * i_trailLock * atr)
        current_sl := posDir == "LONG" ?
                      math.max(current_sl, trailLevel) :
                      math.min(current_sl, trailLevel)
```

**Why optional**: The MC data shows the biggest gain comes from the initial BE trigger (saving losers that were profitable). The stepped trail captures more MFE on winners but also risks premature exits on volatile moves. Keeping it off by default lets users enable and tune it per coin.

**Why stepped, not continuous**: A continuous trailing stop on a 5min chart with 20x leverage will get chopped out constantly. Discrete steps (e.g., every 0.15 ATR, lock 0.10 ATR) create meaningful stop zones with room for normal price noise.

---

### Change 3 — Commission Fix ($4/side)

**What**: Change `commission_value=6` to `commission_value=4` in `strategy()` declaration.

**Why**: Real rate is 0.04% taker × $10,000 notional = $4/side. The v3.7.1 value of $6 overstates commissions by 50%.

**Dashboard update**: Change line 477 from `* 12.0` to `* 8.0` (and add net-of-rebate line):
```
float totalComm = strategy.closedtrades * 8.0
float netComm   = totalComm * 0.30   // After 70% rebate
```
Dashboard row shows both gross and net commission.

---

### Change 4 — Dashboard BE Status Row

**What**: Add a dashboard row showing BE stop state.

**New row** (row 13, shift table size to 14 rows):
```
string beStr = not i_useBE ? "OFF" :
               not inPosition ? "---" :
               beTriggered ? "LOCKED " + str.tostring(beLevel, "#.####") :
               "ARMED"
color beColor = not i_useBE ? color.gray :
                beTriggered ? color.lime :
                inPosition ? color.yellow : color.gray
table.cell(dash, 0, 13, "BE", text_color=color.gray, text_size=size.tiny)
table.cell(dash, 1, 13, beStr, text_color=beColor, text_size=size.tiny)
```

States: `OFF` (feature disabled) → `---` (flat) → `ARMED` (in trade, waiting for trigger) → `LOCKED $X.XXXX` (BE stop active, shows level)

---

### Change 5 — SL Line Visual Update

**What**: Change the SL plot color when BE is active.

Currently line 412:
```
plot(inPosition ? current_sl : na, "Stop Loss", color.red, 2, plot.style_linebr)
```

Change to:
```
color slColor = beTriggered ? color.lime : color.red
plot(inPosition ? current_sl : na, "Stop Loss", slColor, 2, plot.style_linebr)
```

Red = original SL, Green = BE/profit-lock SL. Instant visual confirmation on the chart.

---

## What Does NOT Change

- **Entry logic**: All stochastic signals (A/B/C), state machine, Cloud 2 re-entry — untouched
- **TP**: Still static at `i_tpMult × ATR` — the data shows TP exits are not the problem (losers are)
- **Cooldown gate**: Still in place, still applied to all entries
- **Order management**: Still single order ID, `strategy.entry()` auto-reverses, `strategy.cancel()` before flips
- **Pyramiding**: Still 1
- **All existing inputs**: No defaults changed except commission

---

## File Naming

- Strategy file: `four_pillars_v3_8_strategy.pine`
- Copy of v3.7.1 kept as-is (no modifications to existing file)

---

## Implementation Order

1. Copy `four_pillars_v3_7_1_strategy.pine` → `four_pillars_v3_8_strategy.pine`
2. Update header comments (version, changelog)
3. Update `strategy()` declaration: version name, `commission_value=4`
4. Add new inputs (BE trigger, BE lock, stepped trail, trail step, trail lock)
5. Add new state variables (`beTriggered`, `beLevel`)
6. Add BE trigger + profit-lock logic block (after entry logic, before strategy execution)
7. Add stepped trail logic (inside the same block, gated by `i_useTrail`)
8. Reset `beTriggered`/`beLevel` in all entry blocks and state sync block
9. Update SL plot color
10. Update dashboard: resize table, add BE row, fix commission calc
11. Test: load on TV, apply to AXS 5min and RIVER 5min, verify BE triggers visually

---

## Validation Checklist

- [ ] BE trigger fires when high/low exceeds entry by `i_beTrigger × ATR`
- [ ] SL moves to `entry ± i_beLock × ATR` after trigger
- [ ] SL never moves backwards once BE is triggered
- [ ] `beTriggered` resets on every new entry (including flips)
- [ ] `beTriggered` resets when position goes flat via state sync
- [ ] Stepped trail (when enabled) steps up correctly
- [ ] SL plot turns green when BE active
- [ ] Dashboard shows correct BE state (OFF/ARMED/LOCKED)
- [ ] Commission shows $8 RT gross, with net-of-rebate line
- [ ] No phantom trades — flips still use `strategy.entry()` only
- [ ] Cooldown gate still works on all entries
- [ ] Strategy tester results show improved P&L vs v3.7.1 baseline

---

## Expected Impact (from Monte Carlo)

With the BE stop alone (no stepped trail), the MC simulation showed:

| Metric | AXS (baseline → median MC) | RIVER (baseline → median MC) |
|---|---|---|
| Net P&L (w/ 70% rebate) | +$2,290 → +$84,640 | +$13,204 → +$117,502 |
| Max DD | -$3,178 → -$726 | -$7,317 → -$1,441 |
| Probability profitable | — | 100% across 10K sims |

The stepped trail would capture additional MFE on winners ($45K-$56K currently left on table) but needs live testing to confirm it doesn't cause premature exits on choppy coins.

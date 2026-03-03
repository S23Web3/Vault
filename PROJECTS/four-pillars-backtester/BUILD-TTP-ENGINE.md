# TTP Engine — Build Summary for Opus

**Project:** Four Pillars Backtester
**Module:** `exits/ttp_engine.py`
**Date:** 2026-03-03
**Prepared by:** Claude Sonnet (scope + audit)
**To be built by:** Claude Opus (advanced thinking)

---

## What This Module Does

A Trailing Take Profit exit engine for cryptocurrency futures trading.
Processes 1m OHLC candle data for a single open trade and determines
when and where the trade closes under two parallel scenarios:
Pessimistic (performance floor) and Optimistic (performance ceiling).

---

## Parameters

| Parameter | Symbol | Value | Description |
|---|---|---|---|
| Activation threshold | `ACT` | 0.005 (0.5%) | Price must move this % from entry before trailing begins |
| Trail distance | `DIST` | 0.002 (0.2%) | Gap maintained between registered extreme and exit level |

Both are configurable at instantiation. Defaults are the locked values above.

---

## Two-Phase Logic

### Phase 1 — MONITORING
Engine watches each candle. No trail active.
- LONG: activation fires when `candle_high >= entry × 1.005`
- SHORT: activation fires when `candle_low <= entry × 0.995`

On activation:
- Set `extreme = activation_price` (not current_price, not candle extreme)
- Reason: 5m crypto, 24/7 market, momentum entry — gaps are edge case not norm
- **Immediately evaluate the activation candle's full range for trail update**
  This is a known bug in the draft — activation candle range was being ignored

### Phase 2 — TRAILING
Per 1m candle, two independent passes run:

**PESSIMISTIC (floor)**
```
1. Check if candle reversal hits current trail_level → if yes, CLOSE
2. Only if not closed → check if candle extreme sets new record → update trail
```

**OPTIMISTIC (ceiling)**
```
1. Check if candle extreme sets new record → update trail
2. Then check if candle reversal hits updated trail_level → if yes, CLOSE
```

Both passes start from the same `self.extreme` and `self.trail_level` at the
top of each candle. They are independent evaluations — not sequential.

State is committed using the pessimistic extreme after each candle
(conservative baseline for next candle's starting point).

---

## Directional Formulas

### LONG
```
activation_price  = entry × (1 + ACT)
trail_level       = highest_price × (1 - DIST)
close condition   = candle_low <= trail_level
extreme updates   = candle_high > current highest_price
```

### SHORT
```
activation_price  = entry × (1 - ACT)
trail_level       = lowest_price × (1 + DIST)
close condition   = candle_high >= trail_level
extreme updates   = candle_low < current lowest_price
```

---

## Bugs Found in Draft — Must Be Fixed in Build

### BUG 1 — 🔴 HIGH — self.state never set to CLOSED
`self.state` on the engine object is never updated after a close event.
Only the result object's state is set. If evaluate() is called after close,
engine silently continues processing. Must set `self.state = "CLOSED"`
inside the evaluate methods when either scenario closes.

### BUG 2 — 🔴 HIGH — Activation candle range not evaluated
`_try_activate()` sets extreme and returns immediately. The activation
candle's remaining high/low range is never processed for a trail update
or exit check. The activation candle must be fully evaluated after
activation fires — same candle, same call.

### BUG 3 — 🟡 MEDIUM — CLOSED_PARTIAL state breaks downstream
No other exit module in the codebase uses CLOSED_PARTIAL. Downstream
portfolio runners check `state == "CLOSED"`. Remove CLOSED_PARTIAL entirely.
Use `closed_pessimistic` and `closed_optimistic` booleans for per-scenario
detail. Set `state = "CLOSED"` when either scenario closes.

### BUG 4 — 🟡 MEDIUM — iterrows() wrong index and slow
`run_ttp_on_trade` uses `iterrows()`. Two problems:
- Returns DataFrame index value as exit_candle_idx, not positional candle
  number from trade start — breaks when DataFrame is a slice of larger set
- Slowest pandas iteration method
Fix: use `enumerate(itertuples())` for positional index and speed.

### BUG 5 — 🟡 MEDIUM — band_width_pct uses `or 0` fallback
When only one scenario has closed, `None or 0` silently substitutes zero
making band_width equal to the single closed scenario's exit — misleading.
Only compute band_width_pct when both `exit_pct_pess` and `exit_pct_opt`
are not None. Return None with explicit label otherwise.

---

## Codebase Conventions to Follow

Existing exit modules pattern (from avwap_trail.py, cloud_trail.py, phased.py):
- Class-based, no external dependencies beyond numpy where needed
- `__init__` sets parameters and resets state
- `reset()` method to clear state between trades
- `compute_initial()` or equivalent for first candle setup
- Returns dicts or simple typed values — no complex nested objects
- No pandas inside the class itself — DataFrame handling in batch runner only
- All exits in `exits/` folder, imported via `exits/__init__.py`

---

## Output Structure

### Per-candle (TTPResult dataclass)
```
closed_pessimistic  : bool
closed_optimistic   : bool
exit_pct_pess       : float | None   # % from entry at close
exit_pct_opt        : float | None   # % from entry at close
trail_level_pct     : float | None   # current trail as % from entry
extreme_pct         : float | None   # current registered extreme as % from entry
state               : str            # MONITORING | ACTIVATED | CLOSED
```

### Per-trade (run_ttp_on_trade return dict)
```
exit_candle_idx     : int            # positional index from trade start
exit_pct_pess       : float | None
exit_pct_opt        : float | None
band_width_pct      : float | None   # only set when both scenarios closed
candle_results      : list[TTPResult]
```

---

## Unit Tests Required

File: `tests/test_ttp_engine.py`

Test cases minimum:

1. **Short — clean sequential** (the spec walk-through)
   Candles: 0%, -0.3%, -0.5% (activate), -0.8%, -1.1%, -0.9% (close)
   Expected pess exit: -0.9% | Expected opt exit: -0.9%
   (same in this case — no ambiguity candle)

2. **Short — ambiguous candle** (new low AND reversal same candle)
   Candle has Low: -1.2%, High: -0.85%, current trail before candle: -0.9%
   Expected pess: closes at -0.9% (high checked first, hits old trail)
   Expected opt:  does NOT close (low updates trail to -1.0%, high -0.85% misses)

3. **Long — clean sequential** (mirror of short test 1)

4. **Long — ambiguous candle** (mirror of short test 2)

5. **Activation candle also triggers trail update**
   Single candle: Low hits activation AND extends further
   Verify extreme is updated on same candle, not deferred to next

6. **Engine stops after close**
   Call evaluate() after CLOSED state — verify no further state mutation

---

## Files to Create

| File | Action |
|---|---|
| `exits/ttp_engine.py` | Create — main module |
| `tests/test_ttp_engine.py` | Create — unit tests |
| `exits/__init__.py` | Amend — add TTPExit and run_ttp_on_trade to imports |

---

## Tags
`#build-ready` `#opus` `#ttp` `#exit-logic` `#four-pillars`

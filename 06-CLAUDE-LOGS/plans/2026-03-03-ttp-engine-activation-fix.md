# TTP Engine Bug Fix — Activation Candle Immediate Close

## Context
5 of 6 TTP engine tests fail. The engine jumps from MONITORING -> CLOSED on the activation candle, skipping the ACTIVATED state entirely. Root cause: after `_try_activate` sets the trail level, `evaluate()` falls through to `_evaluate_short`/`_evaluate_long`, which checks H/L against the trail — and the activation candle's H/L naturally violates it (the trail is set from activation_price, and the candle's range straddles that area).

## Root Cause Trace (Short example)
- Entry=100, ACT=0.5%, DIST=0.2%
- activation_price = 99.5
- Candle: H=99.8, L=99.5
- `_try_activate`: extreme=99.5, trail=99.5*1.002=99.699
- Falls through to `_evaluate_short`: H=99.8 >= trail=99.699 -> closed_pess=True -> CLOSED

The trail stop fires on the SAME candle that activates because the candle's high is naturally above the trail level. This is wrong — the activation candle establishes the baseline; trail stop checking should begin on the NEXT candle.

## Fix (single file)

**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ttp_engine.py`

### Change 1: `evaluate()` method (lines 55-68)
After activation, do NOT fall through to `_evaluate_short`/`_evaluate_long`. Instead:
1. Update extreme/trail if the candle extends beyond activation price (test 5 requirement)
2. Return ACTIVATED result immediately (no close check)

Replace lines 55-68 with:
```python
if self.state == "MONITORING":
    activated = self._try_activate(h, l)
    if not activated:
        return TTPResult(state="MONITORING")
    # Activation candle: update extreme if candle extends past activation
    # but do NOT check trail stop (that starts next candle)
    self._update_extreme_on_activation(h, l)
    return TTPResult(
        state="ACTIVATED",
        trail_level_pct=self._trail_pct(),
        extreme_pct=self._extreme_pct(),
    )

# --- ACTIVATED (non-activation candle): run dual scenario ---
if self.direction == "LONG":
    result = self._evaluate_long(h, l)
else:
    result = self._evaluate_short(h, l)
return result
```

### Change 2: Add `_update_extreme_on_activation()` method
New method that extends extreme/trail beyond activation price using the candle's full range, without checking for trail stop:
```python
def _update_extreme_on_activation(self, h, l):
    """On activation candle, extend extreme past activation_price if candle overshoots."""
    if self.direction == "LONG":
        if h > self.extreme:
            self.extreme = h
            self.trail_level = self.extreme * (1.0 - self.dist)
    else:
        if l < self.extreme:
            self.extreme = l
            self.trail_level = self.extreme * (1.0 + self.dist)
```

### Change 3: Add helper methods for pct calculation
Small helpers to avoid duplicating the pct math in the new return statement:
```python
def _trail_pct(self):
    """Compute trail level as pct from entry."""
    if self.trail_level is None:
        return None
    if self.direction == "LONG":
        return (self.trail_level - self.entry) / self.entry
    return (self.entry - self.trail_level) / self.entry

def _extreme_pct(self):
    """Compute extreme as pct from entry."""
    if self.extreme is None:
        return None
    if self.direction == "LONG":
        return (self.extreme - self.entry) / self.entry
    return (self.entry - self.extreme) / self.entry
```

## Expected Test Results After Fix
- test_short_clean_sequential: PASS (activation candle returns ACTIVATED, candle 6 closes)
- test_short_ambiguous_candle: PASS (activation returns ACTIVATED, ambiguous candle splits pess/opt)
- test_long_clean_sequential: PASS (mirror of short)
- test_long_ambiguous_candle: PASS (mirror of short ambiguous)
- test_activation_candle_trail_update: PASS (extreme updates to 99.3 on activation candle)
- test_engine_stops_after_close: PASS (already passes, no change)

## Verification
```
cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
python -m pytest tests/test_ttp_engine.py -v
```
All 6 tests should pass.

## Files Modified
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ttp_engine.py` — 3 changes in `evaluate()`, plus 3 new helper methods

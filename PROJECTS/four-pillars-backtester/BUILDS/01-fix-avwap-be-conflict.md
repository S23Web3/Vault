# Task: Fix AVWAP + BE Raise Conflict

## Goal
Enable BE raise to work TOGETHER with AVWAP trail (not exclusively).

## Problem
Current code (line 145 in `engine/position.py`):
```python
if not self.avwap_enabled and not self.be_raised:
```
This disables BE raise when AVWAP is active, causing full -1.0 ATR losses.

## Solution
Remove the `not self.avwap_enabled` check. BE raise should trigger regardless of AVWAP setting.

## Files to Edit
- `engine/position.py` (line 145 and line 176)

## Changes

**Line 145 (LONG positions):**
```python
# OLD:
if not self.avwap_enabled and not self.be_raised:

# NEW:
if not self.be_raised:
```

**Line 176 (SHORT positions):**
```python
# OLD:
if not self.avwap_enabled and not self.be_raised:

# NEW:
if not self.be_raised:
```

## Test Command
```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

python -c "
from engine.backtester import Backtester
from signals.four_pillars import compute_signals
from data.fetcher import BybitFetcher

fetcher = BybitFetcher('data/cache')
df = fetcher.load_cached('RIVERUSDT')
df = compute_signals(df)

# Test: AVWAP ON, BE ON (both should work)
bt = Backtester({
    'be_raise_amount': 4.0,
    'avwap_trail': True,
    'avwap_band': 1,
    'sl_mult': 1.0,
    'tp_mult': 1.5,
    'notional': 10000.0,
    'commission_rate': 0.0008,
    'rebate_pct': 0.70
})
result = bt.run(df)

be_count = result['metrics']['be_raised_count']
assert be_count > 0, f'BE raise should work with AVWAP. Got: {be_count}'
print(f'✅ Test passed: BE raises = {be_count}')
print(f'   Net P&L: ${result[\"metrics\"][\"net_pnl\"]:,.2f}')
"
```

## Expected Output
```
✅ Test passed: BE raises = 1631
   Net P&L: $39,240.51
```

## Verification
After fix, dashboard should show:
- AVWAP enabled + BE_n > 0 (not 0)
- Profit improves vs current -$13K

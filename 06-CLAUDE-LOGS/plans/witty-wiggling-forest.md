# Fix v3.7 Commission Blow-Up — Implementation Plan

## Context

With commission OFF, v3.7 shows 222 trades, +$4,480 (+44.81%). With commission ON (0.06%), the account blows up. Root cause: phantom trades from `strategy.close_all()` + `strategy.entry()` on the same bar create double-commission events with $0 P&L, and rapid flipping with no cooldown amplifies the damage.

## File to Modify

`c:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\four_pillars_v3_7_strategy.pine`

## Changes (6 total)

### 1. Switch to `cash_per_order` commission (line 12-17)
**Why:** `commission.percent` applies to order value which is ambiguous with leverage. Cash per order is deterministic — $6/side, always.
```
commission_type=strategy.commission.cash_per_order,
commission_value=6,
```

### 2. Remove all `strategy.close_all()` calls from flip logic (lines 287, 300, 312, 324)
**Why:** `strategy.close_all()` + `strategy.entry()` on the same bar creates two separate trades: a close (with commission) that nets $0, then a new entry (with commission). That's $12 wasted per flip. Instead, `strategy.entry()` in the opposite direction auto-reverses — one order, one commission.

Delete these 4 lines:
- `strategy.close_all("Flip to Long")` (line 287)
- `strategy.close_all("Flip to Short")` (line 300)
- `strategy.close_all("BC Flip to Long")` (line 312)
- `strategy.close_all("BC Flip to Short")` (line 324)

### 3. Cancel stale exit orders before flips (lines 391-394)
**Why:** When flipping direction, the old `strategy.exit()` order is still pending. If it fills on the same bar as the new entry, it creates a phantom close. Cancel it first.

Before entry execution, add:
```pine
if didEnterThisBar and posDir == "LONG"
    strategy.cancel("Exit Short")  // Cancel stale short exit
    strategy.entry("Long", strategy.long)
if didEnterThisBar and posDir == "SHORT"
    strategy.cancel("Exit Long")   // Cancel stale long exit
    strategy.entry("Short", strategy.short)
```

### 4. Add cooldown input (after line 45)
**Why:** Without cooldown, the strategy can flip 5 times in 5 minutes (seen in CSV trades 123-127). Each flip pays commission. Minimum 3-bar gap prevents rapid churn.

```pine
i_cooldown = input.int(3, "Min Bars Between Entries", minval=0, maxval=20, group=grp3,
    tooltip="Minimum bars between entries. Prevents rapid-fire flipping that pays commission for nothing.")
```

### 5. Add cooldown gate to all entry conditions (before line 269)
**Why:** Gate every entry signal with cooldown check so no entry can fire within N bars of the last entry.

```pine
bool cooldownOK = na(entryBar) or (bar_index - entryBar >= i_cooldown)
```

Then add `and cooldownOK` to every entry condition:
- `enter_long_a`, `enter_short_a`
- `enter_long_bc`, `enter_short_bc`
- `flip_long_bc`, `flip_short_bc`
- `enter_long_re`, `enter_short_re`

### 6. Add commission tracker row to dashboard (after line 474)
**Why:** Visibility into how much commission the strategy has paid helps diagnose future issues.

```pine
float totalComm = strategy.closedtrades * 12.0  // $6 entry + $6 exit
table.cell(dash, 0, 12, "Comm$", text_color=color.gray, text_size=size.tiny)
table.cell(dash, 1, 12, "$" + str.tostring(totalComm, "#"), text_color=color.orange, text_size=size.tiny)
```
Update table size from 12 rows to 13.

## Verification

1. Load on TradingView with 1000PEPEUSDT.P 5min
2. Commission ON ($6/order cash) — account should NOT blow up
3. Check trade list: no $0 P&L phantom trades
4. Check that flips show as single trades (not close+open pairs)
5. Check that no two entries happen within 3 bars of each other
6. Dashboard "Comm$" row shows running commission total
7. Compare trade count and net P&L against commission-off baseline

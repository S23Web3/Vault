# Build Journal - 2026-02-06

## Sessions Summary

### Session 1: Four Pillars v3.7 — Rebate Farming Architecture

**File:** `four_pillars_v3_7_strategy.pine` (NEW — v3.6 preserved)

Built the "rebate farming" strategy — flip-heavy architecture designed for ~3000 trades/month where flat equity + commission rebates = profit.

**v3.7 Architecture Changes from v3.6:**

| Component | v3.6 | v3.7 |
|-----------|------|------|
| SL | AVWAP ± stdev trail | 1.0 ATR static (tight) |
| TP | Variable | 1.5 ATR static (tight) |
| B/C behavior | Add to existing only | **Open fresh positions** + flip direction |
| Volume flip filter | Required for flips | **Removed** — free flips on any signal |
| Cloud 2 re-entry | Tracks bars since A only | Tracks bars since ANY signal (A/B/C) |
| Order IDs | Separate A/"Long BC" | Single order ID (v3.5 simplicity) |
| Pyramiding | 10 | **1** (one position at a time) |
| Commission | percent 0.06% | percent 0.06% (**BUG — see below**) |

---

### Session 2: Commission Blow-Up Discovery + v3.7.1 Emergency Fix

**CRITICAL BUG:** `commission.percent=0.06` applies to CASH qty ($500), not notional ($10k with 20x leverage).

| What TV Calculated | Reality |
|-------------------|---------|
| 0.06% × $500 = **$0.30/side** | 0.06% × $10,000 = **$6.00/side** |
| $0.60 round trip | **$12.00 round trip** |

Combined with phantom trade bug (`strategy.close_all()` + `strategy.entry()` = 2 trades per flip), v3.7 was burning ~$24 per flip instead of $0.60.

**File:** `four_pillars_v3_7_1_strategy.pine` (NEW — emergency fix)

**v3.7.1 Fixes:**

| Fix | Before (v3.7) | After (v3.7.1) |
|-----|---------------|----------------|
| Commission | `commission.percent=0.06` | `cash_per_order=6` (deterministic) |
| Flipping | `strategy.close_all()` + `strategy.entry()` | `strategy.entry()` only (auto-reverses) |
| Stale exits | Not handled | `strategy.cancel()` before every flip |
| Cooldown | None — could flip 5x in 5 minutes | 3-bar minimum between entries |
| Cooldown gate | Not applied | `cooldownOK` on ALL entry paths (A, BC, flip, re-entry) |
| Dashboard | No commission tracking | Added running Comm$ total row |

**Also created:** `four_pillars_v3_7_1.pine` (indicator version)

---

### TradingView Backtest Export

Exported CSV for validation: `07-TEMPLATES/4Pv3.4.1-S_BYBIT_MEMEUSDT.P_2026-02-06_fcc84.csv`

---

## Key Learnings

### Commission on Leverage — CRITICAL
```
$500 margin × 20x leverage = $10,000 notional
0.06% taker × $10,000 = $6/side = $12 round trip

TradingView commission.percent applies to CASH QTY, not notional!
Use cash_per_order for leveraged strategies — ALWAYS.
```

### Phantom Trade Bug
```
strategy.close_all("Flip") + strategy.entry("Long") on same bar:
  → Trade 1: Close short ($0 P&L + $6 commission)
  → Trade 2: Open long ($6 commission)
  = $12 commission for what should be 1 trade

Fix: strategy.entry("Long") auto-reverses from short = 1 trade, 1 commission
Also: strategy.cancel() stale exit orders that would collide with new entry
```

### Cooldown Pattern
```pinescript
var int entryBar = na
bool cooldownOK = na(entryBar) or (bar_index - entryBar >= i_cooldown)
// Apply cooldownOK to ALL entry conditions
// entryBar does NOT reset on exit — persists between trades
```

---

## Files Created/Modified

| File | Status |
|------|--------|
| `four_pillars_v3_7_strategy.pine` | **NEW** — rebate farming architecture |
| `four_pillars_v3_7_1_strategy.pine` | **NEW** — commission fix + cooldown |
| `four_pillars_v3_7_1.pine` | **NEW** — indicator version |

---

## Next Steps

1. Build Python backtester to validate v3.7.1 with correct commission
2. Test breakeven+$X raise on historical data
3. Fetch historical data for multiple coins

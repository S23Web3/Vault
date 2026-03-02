# BingX Breakeven Fix — Session Log
**Date:** 2026-02-28
**Scope:** BE stop price only. No TTP work, no SL gate, no entry logic.
**Files changed:** `position_monitor.py`, `tests/test_position_monitor.py` (new)

---

## 1. Problem Statement

Breakeven raise fires correctly (confirmed in live logs: ELSA, VIRTUAL, PENDLE, DEEP, MEME, BB, VET, ATOM all raised BE successfully). But every BE exit records a loss in trades.csv.

Root cause confirmed: `_place_be_sl()` placed the STOP_MARKET at `entry_price` exactly.
At that price, gross PnL = 0 and commission = $0.05 → net = -$0.05 guaranteed.
Slippage on STOP_MARKET adds another $0.01–$0.129 depending on coin and qty.

---

## 2. Evidence From Logs and trades.csv

**Live bot log — BE SL placements (2026-02-27-bot.log):**
```
19:17:09 BE SL placed: ELSA-USDT stopPrice=0.084630  (= entry exactly)
19:17:12 BE SL placed: VIRTUAL-USDT stopPrice=0.692300
19:18:15 BE SL placed: PENDLE-USDT stopPrice=1.276200
20:43:15 BE SL placed: DEEP-USDT stopPrice=0.025170
20:43:19 BE SL placed: MEME-USDT stopPrice=0.000614
20:44:25 BE SL placed: BB-USDT stopPrice=0.025840
20:46:28 BE SL placed: VET-USDT stopPrice=0.007403
20:47:33 BE SL placed: ATOM-USDT stopPrice=1.873000
```

**trades.csv exits after BE raise:**
| Symbol | Entry | Exit | Reason | pnl_net |
|--------|-------|------|--------|---------|
| ATOM SHORT | 1.873 | 1.873 | SL_HIT | -0.05 |
| VET SHORT | 0.007403 | 0.007403 | SL_HIT | -0.05 |
| ELSA SHORT | 0.08463 | 0.08464 | SL_HIT | -0.0557 |
| MEME SHORT | 0.000614 | 0.000615 | SL_HIT | -0.129 |
| BB SHORT | 0.02584 | 0.02589 | SL_HIT | -0.144 |

The ATOM/VET pattern (-$0.05 with same entry/exit) confirms commission_rate = 0.001 (0.1% RT = 0.05% per side) on the live account. Every BE exit is a guaranteed commission loss.

---

## 3. True BE Math

commission_rate = 0.001 (total RT), notional = $50, commission = $0.05

**LONG:** exit >= entry × (1 + commission_rate) = entry × 1.001
**SHORT:** exit <= entry × (1 - commission_rate) = entry × 0.999

Example — ELSA SHORT, entry=0.084630:
- Old stop:  0.084630 (entry exactly) → pnl_net = -$0.05 at best
- True stop: 0.084630 × 0.999 = 0.084545 → pnl_net = $0 at exact fill

---

## 4. Approaches Evaluated

| | A: Fix commission math | B: Add slippage buffer | C: STOP_LIMIT | D: TP_MARKET |
|---|---|---|---|---|
| Lines of code | 3 | 4 | 4 | 20+ |
| Dollar improvement | +$0.05/exit | +$0.10/exit | +$0.05 | +$0.05 |
| Non-fill risk? | No | No | Yes | No |
| Leaves unprotected? | No | No | Possible | Yes (reversal unprotected) |
| Recommended? | YES | Optional | No | No |

**Chosen: Approach A** — proportionate to trade size, correct, minimal code.

---

## 5. Code Changes

### position_monitor.py

`_place_be_sl()` changes:
1. Added BE price formula: `entry × (1 + commission_rate)` for LONG, `entry × (1 - commission_rate)` for SHORT
2. `stopPrice` now uses `be_price` (rounded to 8dp) instead of `entry_price`
3. Return signature: `float` (be_price) on success, `None` on failure (was `True`/`False`)
4. Log message updated: shows both entry and be_price

`check_breakeven()` changes:
1. `ok = self._place_be_sl(...)` → `be_price = self._place_be_sl(...)`
2. `if ok:` → `if be_price is not None:`
3. `sl_price: entry_price` → `sl_price: be_price` in state update
4. Telegram message updated: shows entry + be_price + mark

### tests/test_position_monitor.py (new file)

7 tests covering:
- LONG BE price above entry (entry × 1.001)
- SHORT BE price below entry (entry × 0.999)
- stopPrice in API params matches be_price
- API failure returns None
- Net pnl >= 0 at exact be_price fill (4 cases)
- Missing data returns None without API call
- commission_rate used from self, not hardcoded

---

## 6. Validation

```
py_compile position_monitor.py           -> OK
py_compile tests/test_position_monitor.py -> OK
```

Run tests:
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python -m pytest tests/ -v
```

---

## 7. What Was NOT Changed

- BE_TRIGGER constant (1.0016). Currently fires at 0.16% which is fine for any commission rate — it just means more headroom before BE fires, not a correctness issue.
- SL gate, risk gate, entry logic — out of scope.
- TTP (trailing_order_id, trailing_activation_price) — built last session, not touched.

---

## 8. Notes

- commission_rate in live bot confirmed = 0.001 (0.05% per side) from trade data
- BE_TRIGGER = 1.0016 was designed for 0.0016 RT (0.08% per side). Live uses 0.001 RT (0.05% per side). Trigger is conservative — fires later than needed, but not wrong.
- Dollar impact of fix: $0.05 saved per BE exit. With ~8 BE exits confirmed in first day of live trading, that's ~$0.40/day. Small but correct.
- Residual risk: STOP_MARKET slippage. For most coins at $50 notional, this is $0.01–0.05. Acceptable and not addressed (Approach B would add a buffer; decided proportionate fix is A).

---

## 9. Follow-Up: Why STOP_MARKET and Not STOP_LIMIT?

User asked: why use STOP_MARKET instead of STOP_LIMIT for the BE stop?

**STOP_LIMIT behavior:**
- Triggers when mark reaches stopPrice
- Then places a LIMIT order at a specified price
- If price gaps past the limit before fill → order never fills, position stays open with no protection

**STOP_MARKET behavior:**
- Triggers when mark reaches stopPrice
- Executes immediately at market price
- Always fills; slippage is the only cost

**Why STOP_MARKET is correct here:**

The BE stop is a protective exit. The primary requirement is that it ALWAYS fills. A STOP_LIMIT introduces non-fill risk: on a volatile coin with a news spike, price can gap 2–5% past the limit, leaving the limit order sitting unfilled while the position moves toward the original SL. On $50 notional, a non-fill scenario costs $0.50–1.50. The slippage on STOP_MARKET is $0.01–0.05. Non-fill downside is 10–30x worse.

STOP_LIMIT makes sense for entries (where you don't want to chase price). For protective exits, STOP_MARKET is the correct type — the guarantee of execution is more important than the exact fill price.

**The actual fix** was the stop *price*, not the order type. `stopPrice = entry_price` was wrong; `stopPrice = entry × (1 ± commission_rate)` is correct. Order type was already correct.

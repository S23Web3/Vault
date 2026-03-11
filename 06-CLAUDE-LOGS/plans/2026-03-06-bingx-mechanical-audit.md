# BingX Bot 24-Hour Mechanical Audit + Fix Plan

**Date:** 2026-03-06
**Goal:** Fix all mechanical/code bugs so the bot runs correctly before scaling to $1000. Strategy tuning is out of scope.

---

## Context

Bot has been running 24+ hours on 47 coins, $5 margin, 10x leverage. User observed:
1. **BE trades going negative** -- SL moved to breakeven + fees, trade still loses money
2. **Trailing not smooth** -- big losers, rare big winners (could be config R:R but also code issues)
3. **Wants mechanical correctness** before scaling to $1000

Prior audit (2026-03-04) fixed: reduceOnly bug, TTP columns, time_sync, signing, dashboard v1.5. This audit goes deeper into PnL accuracy and trailing mechanics.

**v2 bot (native trailing):** Built 2026-03-05 at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\`. Uses BingX `TRAILING_STOP_MARKET` instead of the Python TTP engine. Eliminates ~6min TTP delay. Config toggle: `ttp_mode: native` vs `engine`. Not yet deployed. The v1 mechanical fixes in this plan should be applied to v2 as well before deployment.

**trades.csv:** 325 trades total. `atr_at_entry` is stored in state.json (executor.py line 301) but NEVER written to trades.csv by `_append_trade()`. Once a position closes, the ATR is lost. This is a data gap that must be fixed.

---

## Audit Findings

### CRITICAL: Exit Price Accuracy (3 bugs causing wrong PnL)

**C1. Polling path uses ESTIMATED exit prices, not actual fills**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` lines 140-153
- `_detect_exit()` checks which pending orders remain. If SL still pending -> TP_HIT with `pos_data.get("tp_price")`. If TP still pending -> SL_HIT with `pos_data.get("sl_price")`.
- These are the TRIGGER prices from state, not the actual fill prices from the exchange.
- STOP_MARKET orders can fill at a different price than stopPrice (slippage, gaps).
- Only `_fetch_filled_exit()` (fallback path, line 160) queries actual avgPrice -- but it only runs when NO pending orders exist.
- **Impact:** Every SL_HIT and TP_HIT PnL via polling path is inaccurate.

**C2. TTP exit uses trail_level as price, not market fill**
- File: `position_monitor.py` lines 109-114
- `_detect_exit()` returns `ttp_trail_level` when `ttp_exit_pending` is set.
- But `_place_market_close()` (line 681) fills at market price, which differs from trail_level.
- `_place_market_close()` returns `True/False`, discarding the order response with `avgPrice`.
- **Impact:** All TTP exit PnL numbers are inaccurate.

**C3. WS fill events don't capture MARKET close orders (TTP)**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ws_listener.py` lines 104-110
- `_parse_fill_event()` only matches `"TAKE_PROFIT"` and `"STOP"` order types.
- TTP market close orders have type `"MARKET"` -- they fall through and return `None`.
- **Impact:** TTP exits NEVER get actual fill price from WS. Always use trail_level estimate.

### HIGH: BE Trades Going Negative (root cause)

**H1. Dual exit path gives inconsistent PnL**
- WS path (`_handle_close_with_price`): uses REAL avg_price from exchange -- CORRECT
- Polling path (`_handle_close` -> `_detect_exit`): uses state estimates -- WRONG
- When WS captures an SL fill on a BE-raised position, it uses the ACTUAL fill price (with slippage). If slippage > the 0.1% buffer, PnL goes negative.
- When polling captures the same event, it uses be_price (always positive).
- **This is why BE trades sometimes show negative: WS gives the real (worse) price.**

**H2. Hardcoded 0.1% slippage buffer**
- File: `position_monitor.py` line 420: `be_buffer = 0.001`
- For high-volatility coins, STOP_MARKET fills can slip more than 0.1%.
- Should be configurable or ATR-scaled.

**H3. Commission fallback is 0.001, should be 0.0016**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` line 128
- If API call fails: `return 0.001` but BingX standard is 0.0008 * 2 = 0.0016 round-trip.
- Wrong fallback means BE price too low -> negative PnL more likely.

### MEDIUM: Trailing Mechanics (explains big losers / small winners)

**M1. No max_atr_ratio cap -- ultra-volatile coins take huge SL losses**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\risk_gate.py`
- Has `min_atr_ratio: 0.003` but no max. Q-USDT (2.58% ATR ratio) passes -> 5.15% SL -> 51.5% margin loss.
- Previous ATR investigation recommended `max_atr_ratio: 0.015`.

**M2. Misleading variable name in check_breakeven**
- File: `position_monitor.py` line 470: `ttp_act = self.config.get("position", {}).get("be_act", 0.004)`
- Variable named `ttp_act` but reads `be_act` value. Works correctly but confusing for maintenance.

**M3. allOrders limit=20 can miss fills**
- File: `position_monitor.py` line 182
- Active symbols may push the filled exit order outside the 20-order window.
- Should increase to 50 or add symbol filter.

### LOW / INFORMATIONAL (not bugs, design characteristics)

**L1. TTP evaluates on 5m candle boundaries only** -- extreme tracking misses intra-bar spikes. `check_ttp_sl_tighten()` running every 30s partially compensates.

**L2. Pessimistic TTP evaluation closes before updating extreme** -- by design (conservative) but systematically caps winners. A 5m candle with +3% high then -1% low closes TTP pessimistically.

**L3. Config R:R asymmetry** -- SL: 2.0 ATR (1-5%), TTP win: ~0.5% (0.8% activation - 0.3% trail). Not a code bug. Strategy tuning is out of scope per user.

---

## Proposed Fixes (prioritized)

### Fix 1: Always use actual fill price for PnL (C1 + C2)

**Approach:** Rewrite `_detect_exit()` to ALWAYS query `allOrders` for the actual avgPrice first. Only fall back to state estimates if allOrders query fails.

Changes to `position_monitor.py`:
- `_detect_exit()`: Query `_fetch_filled_exit()` FIRST. If it returns a real fill price, use that. Only use pending-order inference as fallback for exit_reason (not price).
- `_place_market_close()`: Return the order response data (including avgPrice) instead of just True/False.
- When `ttp_exit_pending`: use the stored market close fill price (from Fix 1b), not trail_level.

### Fix 2: Capture MARKET order fills in WS listener (C3)

**Approach:** Add `"MARKET"` to the order type filter in `_parse_fill_event()`. When a MARKET fill arrives, determine if it's a TTP close by checking if the symbol has `ttp_exit_pending` in state. Set reason to `"TTP_EXIT"`.

Changes to `ws_listener.py`:
- `_parse_fill_event()`: Accept MARKET order type fills. Use position side to determine if it's an entry or exit. If exit (side opposite to positionSide direction), push to fill_queue with `reason="TTP_EXIT"`.

### Fix 3: Store market close fill price for TTP (C2 supplement)

Changes to `position_monitor.py`:
- `_place_market_close()`: Return dict with `avgPrice` on success, None on failure.
- `check_ttp_closes()`: Store the fill price in state as `ttp_fill_price` when market close succeeds.
- `_detect_exit()`: When `ttp_exit_pending`, use `ttp_fill_price` if available, trail_level as last resort.

### Fix 4: Fix BE buffer and commission fallback (H1, H2, H3)

Changes to `position_monitor.py`:
- `_place_be_sl()`: Read `be_buffer` from config (`position.be_buffer`, default 0.002 = 0.2%). Increase default to 0.2% for better slippage protection.

Changes to `main.py`:
- `fetch_commission_rate()`: Change fallback from `0.001` to `0.0016`.

Changes to `config.yaml`:
- Add `be_buffer: 0.002` under `position:`.

### Fix 5: Add max_atr_ratio to risk gate (M1)

Changes to `risk_gate.py`:
- Add check between Check 5 and Check 6: if `atr_ratio > max_atr_ratio`, block.
- Read `max_atr_ratio` from config (default 0.015).

Changes to `config.yaml`:
- Add `max_atr_ratio: 0.015` under `risk:`.

### Fix 6: Write atr_at_entry to trades.csv (data gap)

Changes to `state_manager.py`:
- `_append_trade()`: Add `atr_at_entry` column to CSV header and row data.
- Reads `pos.get("atr_at_entry", "")` from position record.
- Also add `sl_price` column (the SL at time of close, whether original or BE-raised).

This enables post-trade SL validation without needing API calls.

### Fix 7: Minor cleanup (M2, M3)

Changes to `position_monitor.py`:
- Line 470: Rename `ttp_act` variable to `be_activation`.
- Line 182: Increase allOrders limit from 20 to 50.

---

## Trade Validation Script (Deliverable 2)

Build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_trade_validator.py`
Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_trade_validator.py`

Reads `trades.csv` and validates every trade:

**For non-BE SL_HIT trades (original SL hit):**

- SL distance = |exit_price - entry_price|
- SL% = SL_distance / entry_price * 100
- Implied ATR = SL_distance / 2.0 (sl_atr_mult=2.0)
- Implied ATR ratio = implied_ATR / entry_price
- Flags: `OK` if SL% is reasonable (0.5-10%), `SUSPICIOUS` if outside range
- Checks whether risk_gate min_atr_ratio (0.003) was respected

**For BE-raised SL_HIT trades (be_raised=True):**

- BE% = (exit_price - entry_price) / entry_price * 100 (signed)
- Expected BE%: ~0.26% for LONG (commission 0.16% + buffer 0.10%)
- Flags: `OK` if exit% near expected BE, `NEGATIVE_BE` if PnL < 0

**For TTP_EXIT trades:**

- Validates ttp_extreme_pct and ttp_trail_pct columns exist and are reasonable
- Checks: extreme > trail (profit was locked)

**For EXIT_UNKNOWN / EXIT_UNKNOWN_RECONCILE:**

- Counts and flags as unresolved (pre-fix data, cannot validate)

**Output:** Terminal table + markdown report at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\trade_validation_YYYY-MM-DD.md`

**Phase splits:** Groups trades by notional ($500 = phase 1, $50 = phase 2+) since phase 1 had known bugs.

---

## Files Modified

| File | Fixes |
|------|-------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` | C1, C2, C3-supplement, H2, M2, M3 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ws_listener.py` | C3 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` | H3 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\risk_gate.py` | M1 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state_manager.py` | Fix 6 (atr_at_entry + sl_price to CSV) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | H2, M1 |

**Untouched (no changes):**

- `executor.py` -- entry logic is correct
- `signal_engine.py` -- TTP engine logic is correct (conservative by design)
- `ttp_engine.py` -- state machine logic is sound
- `bingx_auth.py` -- signing/time_sync already patched

---

## Delivery

Two build scripts:

1. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_mechanical_audit_fixes.py` -- patches 6 files with .bak backups, py_compile each
2. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_trade_validator.py` -- creates run_trade_validator.py

---

## Verification

1. `py_compile` all 6 modified files
2. Run trade validator on existing 325 trades -- check SL distances, BE%, TTP consistency
3. Review trades.csv after next few trades -- TTP exits should show real fill price, not trail_level
4. BE-raised trades should all show small positive PnL (buffer protecting against slippage)
5. Ultra-volatile coins (Q-USDT class, atr_ratio > 1.5%) should be blocked by risk gate
6. Bot restart required to activate all fixes
7. Run command: `cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector" && python main.py`

---

## What This Does NOT Fix (out of scope)

- Strategy R:R asymmetry (SL 2 ATR vs TTP 0.5% net) -- that's strategy tuning
- TTP only evaluating on 5m candles -- would need architecture change (tick-level data)
- Pessimistic TTP evaluation -- by design, conservative is correct for live money

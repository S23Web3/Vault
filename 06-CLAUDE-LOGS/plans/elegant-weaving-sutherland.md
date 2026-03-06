# Plan: Native Trailing Stop Switch (ttp_mode: native)
Date: 2026-03-05

## Context

Custom TTP engine evaluates on confirmed 5m candles only, creating ~6min worst-case delay before trailing exit fires. BingX native `TRAILING_STOP_MARKET` runs tick-level on exchange — zero delay. Test confirmed BingX accepts `priceRate=0.003` (0.3%), matching current `ttp_dist`.

Previous native trailing attempt failed because activation was ATR-based (too far) and callback was 2% (too wide). This plan switches to percentage-based params matching the working TTP config.

## Design: Config-toggled switch

New config key `ttp_mode` with two values:
- `"native"` — exchange-managed trailing, tick-level reaction
- `"engine"` — current custom TTP engine (default, no changes)

Reuses existing `ttp_act` (0.008) and `ttp_dist` (0.003) for both modes.

## Files to modify (6 files, ~65 lines changed)

### 1. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
- Add `ttp_mode: native` under position section (1 line)

### 2. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py`
**Constructor** (line 22): Read `ttp_mode`, `ttp_act`, `ttp_dist` from position_config

**`_place_trailing_order`** (line 128): Add `price_rate` parameter so caller can override `self.trailing_rate`:
```python
def _place_trailing_order(self, symbol, direction, quantity, activation_price, price_rate=None):
    rate = price_rate if price_rate is not None else self.trailing_rate
```

**Entry trailing block** (lines 305-317): Replace single ATR-based path with dual-path:
- `ttp_mode == "native"`: activationPrice = entry * (1 + ttp_act), priceRate = ttp_dist
- `elif trailing_rate and trailing_activation_atr_mult and signal.atr`: legacy ATR path (unchanged)

Store `ttp_mode: "native"` in position state so monitor knows.

**Notification** (line 325): Show "NativeTrail: act=X cb=Y%" when native mode.

### 3. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\signal_engine.py`
**Constructor** (line 26): Read `self.ttp_mode` from ttp_config

**`_evaluate_ttp_for_symbol`** (line 87): Early return when `ttp_mode == "native"` — skip entire TTP engine evaluation (2 lines added)

### 4. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
**Constructor** (line 21): Read `self.ttp_mode` from `config.get("position", {}).get("ttp_mode", "engine")`

**`check_ttp_closes`** (line 610): Early return when native mode (engine close flags don't exist)

**`check_ttp_sl_tighten`** (line 639): Early return when native mode (exchange handles trailing)

**CRITICAL BUG FIX — `_cancel_open_sl_orders`** (line 397): Currently `"STOP" in "TRAILING_STOP_MARKET"` is True, so BE raise would cancel the native trailing order. Fix:
```python
if ("STOP" in otype and "TAKE_PROFIT" not in otype
        and otype != "TRAILING_STOP_MARKET"
        and pos_side == direction):
```

**`_detect_exit`** (line 132): Add `TRAILING_STOP_MARKET` classification. Currently trailing orders fall into `sl_orders` bucket. When trailing fires (not in open orders), both SL and TP remain pending — current logic returns `(None, None)`. Fix: separate trailing orders, detect when trailing_order_id from state is missing from open orders = it fired.

**`_fetch_filled_exit`** (line 173): Add explicit `TRAILING_STOP_MARKET` check before generic `"STOP" in otype`:
```python
if otype == "TRAILING_STOP_MARKET":
    return avg_price, "TRAILING_EXIT"
```

### 5. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ws_listener.py`
**`_parse_fill_event`** (line 104): Add `TRAILING_STOP_MARKET` detection before `"STOP" in order_type`:
```python
elif order_type == "TRAILING_STOP_MARKET":
    reason = "TRAILING_EXIT"
```

### 6. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state_manager.py`
- Add `TRAILING_EXIT` to trades.csv `ttp_exit_reason` column logic (1-2 lines)

## Three-stage interaction with native mode

| Stage | Engine mode | Native mode |
|-------|-----------|-------------|
| BE raise (+0.4%) | Runs, places STOP_MARKET at breakeven | **Still runs** — safety net between +0.4% and +0.8% |
| TTP activation (+0.8%) | Engine evaluates on 5m candle | Exchange activates trailing at tick level |
| Trail (0.3% callback) | Engine tracks, sets close_pending | Exchange trails and fills automatically |
| SL tighten post-TTP | Progressive SL ratchet toward trail | **Skipped** — exchange handles it |
| Exit detection | ttp_close_pending -> market close | Trailing fills -> _detect_exit finds TRAILING_EXIT |

## Edge cases handled

1. **BE raise cancelling trailing**: Fixed by excluding `TRAILING_STOP_MARKET` from `_cancel_open_sl_orders`
2. **Exit detection when trailing fires**: SL + TP still pending, trailing gone from open orders -> classified as `TRAILING_EXIT`, orphaned orders cancelled
3. **Native trailing rejected by exchange**: Logged as error, SL remains as safety net, no fallback to engine
4. **Bot restart**: Trailing order lives on exchange. `trailing_order_id` in state.json. Monitor detects position state normally
5. **Switchback**: Set `ttp_mode: engine` — everything reverts to current behavior, zero regressions

## What is NOT changing
- `ttp_engine.py` — untouched, just not invoked in native mode
- `main.py` — config already flows correctly to all components
- `check_breakeven()` — still active in native mode (safety net)
- Dashboard — shows whatever is in state.json, deferred for later

## Delivery
Build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_native_trailing.py`
- Writes all 6 modified files (complete content)
- py_compile each
- Reports results

## Verification
1. `py_compile` all 6 files — mandatory
2. Existing `test_three_stage_logic.py` passes unchanged (engine mode path untouched)
3. Manual: set `ttp_mode: native` + `demo_mode: true`, run bot, verify:
   - Trailing order placed alongside entry (check logs)
   - BE raise does NOT cancel trailing (check logs)
   - Exit detected as `TRAILING_EXIT` in trades.csv
4. Switchback: set `ttp_mode: engine`, verify three-stage pipeline fully restored

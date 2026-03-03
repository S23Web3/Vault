# Plan: TTP Engine Integration — BingX Connector + Dashboard

**Date:** 2026-03-03 (revised after audit)
**Plan file:** cuddly-dancing-perlis.md

---

## Context

`ttp_engine.py` was drafted by Opus but has 4 remaining bugs.
The BingX connector has no TTP logic — current exit is fixed ATR-TP order placed at entry.
User wants: TTP toggled on/off from dashboard, displayed per-position, wired into the live bot.
"Replace fixed TP with TTP" is out of scope (do last, separate session).

**Patch2 status:** confirmed applied. All prior dashboard errors resolved.
**Pre-existing bugs:** Verified executor.py and state_manager.py — all were agent transcription errors. No real bugs found.

---

## Bug Fixes (ttp_engine.py) — 4 issues

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | HIGH | `self.state` never set to CLOSED | Add `self.state = "CLOSED"` inside `_evaluate_long` and `_evaluate_short` when either scenario closes |
| 4 | MED | `CLOSED_PARTIAL` state | Replace with `"CLOSED"` everywhere. Booleans carry per-scenario detail |
| 5 | MED | `iterrows()` slow/fragile | Replace with `enumerate(candles_df[['high','low']].itertuples(index=False))` |
| 6 | MED | `band_width_pct` `or 0` fallback | Guard with `if pess is not None and opt is not None` instead of `if (pess and opt)` |

Bug 2 covered by Bug 1 fix. Bug 3 verified correct. Bug 7 already fixed.

---

## Architecture — Hybrid (audit-revised)

**Problem with original plan (mark price in monitor):**
1. H=L=mark collapses dual scenario to zero band — makes pess/opt meaningless
2. Activation price gap: if mark already past threshold, extreme is set wrong
3. Race condition: SL fills while TTP cancels orders

**Solution: Split evaluation and execution across two threads.**

### Thread 1 — Market Loop (signal_engine.py): TTP Evaluation

`on_new_bar(symbol, ohlcv_df)` already receives actual 1m OHLC candles per symbol.
After entry signal processing, evaluate TTP for any open position matching this symbol.

```
on_new_bar(symbol, ohlcv_df):
  ... existing entry signal logic (unchanged, restructured to not early-return) ...

  _evaluate_ttp_for_symbol(symbol, ohlcv_df):
    if not self.ttp_enabled: return
    latest = ohlcv_df.iloc[-1]  # confirmed bar
    h, l = float(latest['high']), float(latest['low'])

    positions = self.state_manager.get_state()['open_positions']

    # Prune engines for closed positions
    stale = [k for k in self.ttp_engines if k not in positions]
    for k in stale: del self.ttp_engines[k]

    for key, pos in positions.items():
      if pos['symbol'] != symbol: continue
      engine = self.ttp_engines.setdefault(key,
        TTPExit(pos['direction'], pos['entry_price'], self.ttp_act, self.ttp_dist))
      if engine.state == "CLOSED": continue

      result = engine.evaluate(candle_high=h, candle_low=l)

      state_manager.update_position(key, {
        'ttp_state': engine.state,
        'ttp_trail_level': engine.trail_level,
        'ttp_extreme': engine.extreme,
      })

      if result.closed_pessimistic:
        state_manager.update_position(key, {
          'ttp_close_pending': True,
          'ttp_exit_pct_pess': result.exit_pct_pessimistic,
          'ttp_exit_pct_opt': result.exit_pct_optimistic,
        })
```

**Key change to on_new_bar:** Currently returns early at line 59-61 when no signal. Must restructure so TTP evaluation always runs after warmup check, even when no entry signal fires.

### Thread 2 — Monitor Loop (position_monitor.py): TTP Close Execution

```
check_ttp_closes():
  for key, pos in open_positions.items():
    if not pos.get('ttp_close_pending'): continue
    symbol, direction, qty = pos['symbol'], pos['direction'], pos['quantity']

    # Race guard: verify position still exists on exchange
    live = _fetch_single_position(symbol, direction)
    if not live:
      # SL/TP already filled — clean up flag
      state.update_position(key, {'ttp_close_pending': False})
      continue

    # Execute close
    _cancel_all_orders_for_symbol(symbol, direction)
    _place_market_close(symbol, direction, qty)
    state.update_position(key, {'ttp_close_pending': False, 'ttp_exit_pending': True})
    logger.info("TTP close executed: %s", key)
```

**Why this handles the race:** If SL fills on exchange between the flag being set and the monitor processing it, `_fetch_single_position` returns None, and we skip. The monitor's existing `check()` will handle the SL exit normally.

---

## Files to Touch

| File | Action | Changes |
|------|--------|---------|
| `bingx-connector/ttp_engine.py` | CREATE | TTP engine with 4 bugs fixed |
| `bingx-connector/signal_engine.py` | MODIFY | Add `__init__` params (`ttp_config`), `self.ttp_engines`, `_evaluate_ttp_for_symbol()`; restructure `on_new_bar()` |
| `bingx-connector/position_monitor.py` | MODIFY | Add `check_ttp_closes()`, `_cancel_all_orders_for_symbol()`, `_place_market_close()`, `_fetch_single_position()`; cleanup in `_handle_close()` |
| `bingx-connector/main.py` | MODIFY | Pass `ttp_config=pos_cfg` to StrategyAdapter; add `monitor.check_ttp_closes()` in `monitor_loop()` |
| `bingx-connector/config.yaml` | MODIFY | Add under `position:`: `ttp_enabled: false`, `ttp_act: 0.005`, `ttp_dist: 0.002` |
| `bingx-connector/bingx-live-dashboard-v1-4.py` | MODIFY | Patch 3: TTP columns + toggle in Controls |
| `bingx-connector/tests/test_ttp_engine.py` | CREATE | 6 unit tests per BUILD-TTP-ENGINE.md spec |

Full paths:

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ttp_engine.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\signal_engine.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_ttp_engine.py`

---

## Detailed Changes Per File

### signal_engine.py (77 lines currently)

**S1 — __init__ signature (line 13-14):**
Add `ttp_config=None` parameter. Extract and store:
```python
self.ttp_enabled = (ttp_config or {}).get('ttp_enabled', False)
self.ttp_act = (ttp_config or {}).get('ttp_act', 0.005)
self.ttp_dist = (ttp_config or {}).get('ttp_dist', 0.002)
self.ttp_engines = {}  # keyed by position key e.g. "BTCUSDT_LONG"
```

**S2 — on_new_bar restructure (lines 48-77):**
Currently returns early when no signal (line 59-61). Restructure to:
1. Warmup check (keep early return — no data = no TTP)
2. Signal processing in try/except (no early return on None signal — just skip execution)
3. TTP evaluation at end (ALWAYS runs after warmup)

**S3 — _evaluate_ttp_for_symbol(symbol, ohlcv_df) (NEW method):**
See architecture section above for full pseudocode.

### main.py

**M1 — StrategyAdapter construction (line 235-242):**
Add `ttp_config=pos_cfg`:
```python
adapter = StrategyAdapter(
    plugin_name=strat_cfg.get("plugin", "mock_strategy"),
    risk_gate=risk_gate,
    executor=executor_inst,
    state_manager=state_mgr,
    notifier=notifier,
    plugin_config=config,
    ttp_config=pos_cfg,
)
```

**M2 — monitor_loop (line 142-154):**
Add after `check_breakeven()`:
```python
monitor.check_ttp_closes()
```

### position_monitor.py (533 lines currently)

**PM1 — _cancel_all_orders_for_symbol(symbol, direction) (NEW):**
Similar to `_cancel_open_sl_orders` (line 357) but removes the STOP-type filter. Cancels ALL pending orders for the symbol+direction pair.

**PM2 — _place_market_close(symbol, direction, quantity) (NEW):**
POST to ORDER_PATH with: symbol, side=(opposite of direction), positionSide=direction, type=MARKET, quantity, reduceOnly=true.
Uses existing `self.auth.build_signed_request()` and `self._safe_post()` patterns from `_place_be_sl()`.

**PM3 — _fetch_single_position(symbol, direction) (NEW):**
Call GET `/openApi/swap/v2/user/positions`, filter for matching symbol+direction with nonzero amt. Returns position dict or None. Used as race guard.

**PM4 — check_ttp_closes() (NEW):**
See architecture section for pseudocode. Iterates open positions, processes `ttp_close_pending` flags.

**PM5 — _handle_close() cleanup (line ~268):**
No TTP engine cleanup needed here (engines live in signal_engine, not monitor). But check for `ttp_exit_pending` flag to set `exit_reason = "TTP_EXIT"` instead of `"EXIT_UNKNOWN"`.

**PM6 — _detect_exit() (line ~90):**
Add check: if `pos_data.get('ttp_exit_pending')`, return `(trail_level, "TTP_EXIT")` without querying orders.

### config.yaml

**C1 — Under position: section (after line 91):**
```yaml
  ttp_enabled: false
  ttp_act: 0.005          # 0.5% activation threshold
  ttp_dist: 0.002         # 0.2% trail distance
```

---

## Dashboard Changes (Patch 3)

### D1 — POSITION_COLUMNS (lines ~688-710)

Add after `Dist SL %` column:
```python
{'field': 'TTP',        'width': 95,
 'cellStyle': {'function': (
     "(p) => p.value==='TRAILING' ? {color:'#3fb950',fontWeight:'bold'} : "
     "p.value==='ACTIVATED' ? {color:'#e3b341'} : {color:'#8b949e'}"
 )}},
{'field': 'Trail Lvl',  'width': 110, 'type': 'numericColumn',
 'valueFormatter': {'function': "params.value != null ? params.value.toFixed(6) : '\u2014'"}},
```

### D2 — build_positions_df

Add to row dict:
```python
"TTP":       "TRAILING" if pos.get("ttp_state") == "ACTIVATED" else pos.get("ttp_state", "\u2014"),
"Trail Lvl": pos.get("ttp_trail_level"),
```

### D3 — Controls tab layout

Add TTP section after existing config fields, before Save Config button:
```python
html.Hr(),
html.Label("TTP Exit"),
dcc.Checklist(id='ctrl-ttp-enabled', options=[{'label': ' Enable', 'value': 'on'}], value=[]),
html.Label("Activation %"),
dcc.Input(id='ctrl-ttp-act', type='number', step=0.1, min=0.1, max=5.0, value=0.5),
html.Label("Trail Distance %"),
dcc.Input(id='ctrl-ttp-dist', type='number', step=0.05, min=0.05, max=2.0, value=0.2),
```

### D4 — CB-11 (load_config_into_controls)

Add 3 outputs. Read from `position:` section of config.yaml:
```python
['on'] if cfg_pos.get('ttp_enabled', False) else [],
cfg_pos.get('ttp_act',  0.005) * 100,
cfg_pos.get('ttp_dist', 0.002) * 100,
```

### D5 — CB-12 (save_config_btn)

Add 3 inputs. Write to `position:` section:
```python
cfg['position']['ttp_enabled'] = 'on' in (ttp_enabled_val or [])
cfg['position']['ttp_act']     = (ttp_act_val or 0.5) / 100
cfg['position']['ttp_dist']    = (ttp_dist_val or 0.2) / 100
```

---

## Build Scripts

### Script 1 — `scripts/build_ttp_integration.py` (CREATE)

Patches connector files (not dashboard):

- P1: Write `ttp_engine.py` with all 4 bugs fixed + py_compile
- P2: Patch `signal_engine.py` — import TTPExit, add ttp_config to __init__, restructure on_new_bar, add _evaluate_ttp_for_symbol + py_compile
- P3: Patch `position_monitor.py` — add check_ttp_closes, _cancel_all_orders_for_symbol, _place_market_close, _fetch_single_position, _detect_exit TTP check + py_compile
- P4: Patch `main.py` — ttp_config param, monitor.check_ttp_closes() line + py_compile
- P5: Append TTP fields to `config.yaml` if not present
- P6: Write `tests/test_ttp_engine.py` (6 unit tests) + py_compile

### Script 2 — `scripts/build_dashboard_v1_4_patch3.py` (CREATE)

Patches dashboard only:

- P1: POSITION_COLUMNS insert (D1)
- P2: build_positions_df row dict (D2)
- P3: Controls layout TTP section (D3)
- P4: CB-11 outputs + body (D4)
- P5: CB-12 inputs + body (D5)
- py_compile dashboard after all patches

Run both independently. Dashboard does NOT require connector script.

---

## Key Constraints

- TTP evaluation uses real 1m OHLC (not mark price) — preserves dual scenario band
- TTP engines live in signal_engine (market loop thread), keyed by position key
- Close execution lives in position_monitor (monitor loop thread) — has auth for orders
- `ttp_close_pending` flag bridges the two threads via state.json (atomic writes, thread-safe)
- Race guard: monitor verifies position exists on exchange before placing MARKET close
- If SL/TP fires first on exchange, position disappears, monitor skips TTP close
- Existing fixed TP orders still placed on entry — TTP runs alongside, whichever fires first wins
- Config under `position:` section — dashboard reads/writes same section
- `"TTP_EXIT"` exit reason logged in trades.csv when TTP closes a position

---

## Verification

1. `python scripts/build_ttp_integration.py` — all patches PASS, py_compile PASS on all files
2. `python -m pytest tests/test_ttp_engine.py -v` — 6 unit tests PASS
3. `python scripts/build_dashboard_v1_4_patch3.py` — all patches PASS, py_compile PASS
4. `python bingx-live-dashboard-v1-4.py` — Controls tab shows TTP section (toggle off by default)
5. Positions grid shows TTP + Trail Lvl columns with dashes (no open positions or TTP disabled)
6. Enable TTP in Controls, save, restart bot
7. Open position: dashboard shows TTP = MONITORING
8. Price moves past activation: dashboard shows TTP = TRAILING + trail level price updating
9. TTP fires: position closes, trades.csv shows exit_reason = TTP_EXIT
10. Race test: if SL fires first, TTP close is skipped cleanly (no double fill)

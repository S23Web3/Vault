# TTP-Triggered BE Raise + be_auto Toggle

## Context

Replace the 0.16% distance-based BE trigger with TTP activation as the sole auto-BE trigger.
`be_auto` defaults to `True` in config.yaml. A toggle in the Strategy Parameters tab lets the
user turn it off. When TTP state transitions to ACTIVATED, the bot auto-raises SL to
entry+commission (same `_place_be_sl` logic, no change). No extra API call needed — ttp_state
is already written to position state by signal_engine each bar.

## Files Modified

1. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
2. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py`
3. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`

---

## Change 1 — position_monitor.py (3 edits)

### 1a. Store config in __init__ (line 30, after `self.fill_queue = ...`)

Add:

```python
self.config = config
```

### 1b. Remove BE_TRIGGER constant (line 17)

Delete:

```python
BE_TRIGGER = 1.0016  # 0.16% move from entry triggers breakeven raise (2x commission RT)
```

### 1c. Rewrite check_breakeven() — new trigger logic

Old trigger: `mark >= entry * BE_TRIGGER` (fetches mark price from exchange per position).
New trigger: `pos_data.get("ttp_state") == "ACTIVATED"` (already in state, no API call).
Guard: read `be_auto` from `self.config`, default True. Return immediately if False.

```python
def check_breakeven(self):
    """Auto-raise SL to breakeven when TTP activates, if be_auto is enabled in config.

    Trigger: ttp_state == "ACTIVATED" written to position state by signal_engine each bar.
    Runs once per position (be_raised persists in state.json).
    No-op if be_auto is False or TTP is disabled (state never reaches ACTIVATED).
    """
    be_auto = self.config.get("position", {}).get("be_auto", True)
    if not be_auto:
        return
    positions = self.state.get_open_positions()
    for key, pos_data in positions.items():
        if pos_data.get("be_raised"):
            continue
        if pos_data.get("ttp_state") != "ACTIVATED":
            continue
        entry_price = float(pos_data.get("entry_price", 0) or 0)
        direction = pos_data.get("direction", "")
        symbol = pos_data.get("symbol", key.rsplit("_", 1)[0])
        if not entry_price or direction not in ("LONG", "SHORT") or not symbol:
            continue
        logger.info(
            "BE trigger (TTP activated): %s entry=%.6f direction=%s",
            key, entry_price, direction)
        self._cancel_open_sl_orders(symbol, direction)
        be_price = self._place_be_sl(symbol, pos_data)
        if be_price is not None:
            self.state.update_position(key, {
                "sl_price": be_price,
                "be_raised": True,
            })
            notional = pos_data.get("notional_usd", 0)
            commission_usd = round(notional * self.commission_rate, 4)
            msg = ("<b>BE+FEES RAISED (TTP)</b>  " + key
                   + "\nEntry:  " + str(round(entry_price, 8))
                   + "\nSL -> " + str(round(be_price, 8))
                   + "  (+" + str(round(self.commission_rate * 100, 3))
                   + "% covers $" + str(commission_usd) + " RT commission)"
                   + "\nTTP activated at ~0.5% from entry")
            self.notifier.send(msg)
            logger.info(
                "BE+fees raised (TTP): %s entry=%.8f be_price=%.8f"
                " (+%.4f%%) covers=$%.4f RT commission",
                key, entry_price, be_price,
                self.commission_rate * 100, commission_usd)
        else:
            logger.error(
                "BE SL place FAILED for %s -- old SL cancelled, check manually", key)
            self.notifier.send(
                "<b>BE RAISE FAILED</b>  " + key
                + "\nOld SL cancelled but new SL FAILED -- check manually")
```

---

## Change 2 — bingx-live-dashboard-v1-4.py (3 edits)

### 2a. Add be_auto toggle to Strategy Parameters tab layout

In `make_strategy_params_tab()`, inside the TTP section after `ctrl-ttp-dist` row, add:

```python
html.Div([
    html.Label("Auto BE on TTP Activate", style=LABEL_STYLE),
    dcc.Checklist(
        id="ctrl-be-auto",
        options=[{"label": " Enabled", "value": "on"}],
        value=["on"],
        style={"color": COLORS["text"]},
    ),
], style=ROW_STYLE),
```

### 2b. CB-11: Add be_auto output

Add to Output list:

```python
Output("ctrl-be-auto", "value"),
```

Add to return tuple (after ttp-dist value):

```python
['on'] if pos.get('be_auto', True) else [],
```

### 2c. CB-12: Add be_auto state + save

Add to State list:

```python
State("ctrl-be-auto", "value"),
```

Add `be_auto_val` to function signature, then in config write block:

```python
cfg["position"]["be_auto"] = 'on' in (be_auto_val or [])
```

---

## Change 3 — config.yaml

Add `be_auto: true` under the `position:` section, alongside `ttp_enabled`.

---

## What is removed vs kept

- REMOVED: `BE_TRIGGER = 1.0016` constant
- REMOVED: mark price API fetch from `check_breakeven` (no longer needed)
- KEPT: `_place_be_sl()` unchanged
- KEPT: `_cancel_open_sl_orders()` call
- KEPT: `be_raised` flag
- KEPT: `_fetch_mark_price_pm()` method (may be used elsewhere, not deleted)

---

## Behaviour

| Scenario | Result |
|----------|--------|
| be_auto=True, TTP disabled | BE never auto-raises (ttp_state never ACTIVATED) |
| be_auto=True, TTP enabled, not activated | BE not raised yet |
| be_auto=True, TTP activates (~0.5%) | BE raised immediately |
| be_auto=False | check_breakeven returns immediately, no action |
| be_raised already True | Skip (unchanged) |

---

## Verification

```bash
python -c "import py_compile; py_compile.compile('position_monitor.py', doraise=True)"
python -c "import py_compile; py_compile.compile('bingx-live-dashboard-v1-4.py', doraise=True)"
python -m pytest tests/test_ttp_engine.py -v
```

Manual: set `ttp_state: ACTIVATED` on a test position in state.json, run one monitor
loop, verify BE SL placed and `be_raised: true` written.

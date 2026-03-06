# Plan: Run build_dashboard_v1_4_patch4.py and Verify

## Context

Session continues from 2026-03-03 afternoon work on the BingX live dashboard. Previous patches (patch1, patch2, patch3) have all been applied to `bingx-live-dashboard-v1-4.py`. The dashboard is at 2293 lines with:
- bot-toggle-btn (single toggle, patch2 applied)
- no duplicate write_bot_status (patch2 applied)
- no max-height cap on status feed (patch2 applied)
- CB-T3 uses prevent_initial_call=True (patch1 applied)

Patch4 adds a **"Close Market" button** to the position action panel (next to Move SL) and a new CB-16 callback that cancels all open orders for the selected position then places a MARKET reduceOnly close.

## State Confirmed

| Item | State |
|------|-------|
| `html.Button("Move SL"` | PRESENT at line 1379 |
| `html.Button("Close Market"` | ABSENT — patch4 not yet run |
| `# CB-8: History Grid` marker | PRESENT at line 1589 |
| `# CB-16: Close Market` marker | ABSENT — patch4 not yet run |
| `def close_market` | ABSENT — patch4 not yet run |
| patch2 applied | YES (bot-toggle-btn present, no dupes) |
| patch3 applied | YES (TTP columns present per TOPIC file) |

## Anchor Verification

**P1 anchor** (lines 1379-1383) — exact match confirmed:
```
                html.Button("Move SL", id="move-sl-btn", n_clicks=0,
                            style={'background': COLORS['orange'], 'color': 'white',
                                   'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
```

**P2 anchor** (lines 1586-1590) — exact match confirmed:
```

# ---------------------------------------------------------------------------
# CB-8: History Grid
# ---------------------------------------------------------------------------
```

Both anchors are unique and will PASS.

## Critical Files

- **Target**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py` (2293 lines)
- **Patch script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch4.py`

## What Patch4 Does

| Patch | Change |
|-------|--------|
| P1 | Adds `html.Button("Close Market", id="close-market-btn")` in red, after Move SL in the position action panel |
| P2 | Inserts CB-16 callback before CB-8 — cancels all open orders for symbol, places MARKET reduceOnly close, writes `close_pending=True` to state.json |

CB-16 uses `prevent_initial_call=True` and `allow_duplicate=True` on `pos-action-status` output.

## Steps to Execute

1. **Run the build script** (user runs from terminal):
   ```
   cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
   python scripts/build_dashboard_v1_4_patch4.py
   ```
   Expected output: `PASS [P1-close-market-btn-layout]`, `PASS [P2-cb16-close-market-callback]`, `py_compile: PASS`, `BUILD OK`

2. **If any FAIL** — read the failure message, check if a prior patch shifted the anchor text. Diagnose and write a targeted fix.

3. **Restart dashboard** (user runs):
   ```
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py"
   ```

4. **Hard refresh browser**: `Ctrl+Shift+R`

## Verification Checklist

- [ ] Build script output: 2/2 PASS, py_compile PASS, BUILD OK
- [ ] Live Trades tab: position action panel shows "Close Market" button in red after "Move SL"
- [ ] Click Close Market with no row selected: no error (PreventUpdate fires, button does nothing)
- [ ] Click Close Market with a row selected: status shows "Market close submitted for {symbol} {direction}" in green
- [ ] Flask log: `Close Market: {symbol} {direction} qty={qty}` + `Market close submitted: {symbol} {direction}`
- [ ] No new IndexError or KeyError in Flask log

## No Risks / No Unknowns

Both anchors verified present and unique. No callbacks are being renamed (no stale browser cache issue). `prevent_initial_call=True` is used correctly on CB-16 (not `allow_duplicate` without it). The `_write_state` helper and `load_state` are already defined in the dashboard from prior builds.

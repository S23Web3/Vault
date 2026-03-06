"""
build_dashboard_v1_4_patch4.py

Adds a "Close Market" button to the position action panel in
bingx-live-dashboard-v1-4.py, next to the existing Raise BE / Move SL buttons.

What this patch does:
  P1 — CB-5 layout: adds "Close Market" button (close-market-btn) after Move SL
  P2 — adds CB-16 callback that:
         1. Fetches open orders for symbol and cancels ALL of them
         2. Places a MARKET reduceOnly close order
         3. Writes close_pending=True to state.json for the position
         4. Returns status to pos-action-status

Run:
    cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
    python scripts/build_dashboard_v1_4_patch4.py
"""
import py_compile
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "bingx-live-dashboard-v1-4.py"

ERRORS = []
PATCHES = []


def safe_replace(label, source, old, new):
    """Replace old->new in source; record PASS/FAIL."""
    if old not in source:
        ERRORS.append(label)
        print(f"  FAIL [{label}] anchor not found")
        return source
    count = source.count(old)
    if count > 1:
        ERRORS.append(label)
        print(f"  FAIL [{label}] anchor matched {count} times (ambiguous)")
        return source
    result = source.replace(old, new, 1)
    PATCHES.append(label)
    print(f"  PASS [{label}]")
    return result


# ---------------------------------------------------------------------------
# Load source
# ---------------------------------------------------------------------------
src = TARGET.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# P1 — CB-5: add "Close Market" button after Move SL button
# ---------------------------------------------------------------------------
OLD_P1 = '''\
                html.Button("Move SL", id="move-sl-btn", n_clicks=0,
                            style={'background': COLORS['orange'], 'color': 'white',
                                   'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),'''

NEW_P1 = '''\
                html.Button("Move SL", id="move-sl-btn", n_clicks=0,
                            style={'background': COLORS['orange'], 'color': 'white',
                                   'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer'}),
                html.Button("Close Market", id="close-market-btn", n_clicks=0,
                            style={'marginLeft': '12px', 'background': COLORS['red'],
                                   'color': 'white', 'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),'''

src = safe_replace("P1-close-market-btn-layout", src, OLD_P1, NEW_P1)

# ---------------------------------------------------------------------------
# P2 — insert CB-16 callback block after CB-7 (Move SL) ends
# ---------------------------------------------------------------------------
OLD_P2 = '''\

# ---------------------------------------------------------------------------
# CB-8: History Grid
# ---------------------------------------------------------------------------'''

NEW_P2 = '''\


# ---------------------------------------------------------------------------
# CB-16: Close Market
# ---------------------------------------------------------------------------

@callback(
    Output('pos-action-status', 'children', allow_duplicate=True),
    Input('close-market-btn', 'n_clicks'),
    State('positions-grid', 'selectedRows'),
    State('store-state', 'data'),
    prevent_initial_call=True,
)
def close_market(n_clicks, selected_rows, state_json):
    """Cancel all open orders then place a MARKET reduceOnly close for the selected position."""
    symbol = "unknown"
    try:
        if not n_clicks or not selected_rows:
            raise PreventUpdate
        row = selected_rows[0]
        symbol = row["Symbol"]
        direction = row["Dir"]
        position_side = "LONG" if direction == "LONG" else "SHORT"
        close_side = "SELL" if direction == "LONG" else "BUY"
        qty = row.get("Qty", 0)

        LOG.info("Close Market: %s %s qty=%s", symbol, direction, qty)

        # Step 1: GET all open orders for symbol
        data = _bingx_request('GET', '/openApi/swap/v2/trade/openOrders',
                              {'symbol': symbol})
        if 'error' in data:
            return html.Span(f"Error fetching orders: {data['error']}",
                             style={'color': COLORS['red']})

        orders = (data.get("orders", []) if isinstance(data, dict)
                  else data if isinstance(data, list) else [])

        # Step 2: Cancel ALL open orders for this symbol
        cancel_errors = []
        for order in orders:
            order_id = order.get("orderId")
            if not order_id:
                continue
            res = _bingx_request('DELETE', '/openApi/swap/v2/trade/order',
                                  {'symbol': symbol, 'orderId': order_id})
            if 'error' in res:
                cancel_errors.append(str(order_id))
        if cancel_errors:
            LOG.warning("Cancel failed for order IDs: %s", ", ".join(cancel_errors))

        # Step 3: Place MARKET close order (reduceOnly)
        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
            'symbol': symbol,
            'side': close_side,
            'positionSide': position_side,
            'type': 'MARKET',
            'quantity': str(qty),
            'reduceOnly': 'true',
        })
        if 'error' in place_result:
            return html.Span(f"Market close failed: {place_result['error']}",
                             style={'color': COLORS['red']})

        # Step 4: Mark position close_pending in state.json
        # Bot monitor loop will detect the closed position and remove it naturally.
        # We write close_pending=True as a signal that we intentionally closed it.
        try:
            state = json.loads(state_json) if state_json else load_state()
            pos_key = f"{symbol}_{direction}"
            if pos_key in state.get("open_positions", {}):
                state["open_positions"][pos_key]["close_pending"] = True
                state["open_positions"][pos_key]["close_source"] = "dashboard"
                _write_state(state)
        except Exception as state_err:
            LOG.error("State write failed after market close: %s", state_err, exc_info=True)

        LOG.info("Market close submitted: %s %s", symbol, direction)
        return html.Span(
            f"Market close submitted for {symbol} {direction}",
            style={'color': COLORS['green']},
        )
    except PreventUpdate:
        raise
    except Exception as e:
        LOG.error("Close Market failed for %s: %s", symbol, e, exc_info=True)
        return html.Span(f"Error: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-8: History Grid
# ---------------------------------------------------------------------------'''

src = safe_replace("P2-cb16-close-market-callback", src, OLD_P2, NEW_P2)

# ---------------------------------------------------------------------------
# Write file
# ---------------------------------------------------------------------------
TARGET.write_text(src, encoding="utf-8")
print(f"\nWrote: {TARGET}")

# ---------------------------------------------------------------------------
# Syntax check
# ---------------------------------------------------------------------------
try:
    py_compile.compile(str(TARGET), doraise=True)
    print("py_compile: PASS")
except py_compile.PyCompileError as e:
    print(f"py_compile: FAIL — {e}")
    ERRORS.append("py_compile")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n--- Summary ---")
print(f"Patches applied: {len(PATCHES)}/{len(PATCHES) + len(ERRORS)}")
for p in PATCHES:
    print(f"  PASS  {p}")
for e in ERRORS:
    print(f"  FAIL  {e}")

if ERRORS:
    print("\nBUILD FAILED")
    sys.exit(1)
else:
    print("\nBUILD OK")
    print("\nNext steps:")
    print("  1. Restart the dashboard:  python bingx-live-dashboard-v1-4.py")
    print("  2. Hard refresh browser:   Ctrl+Shift+R")
    print("  3. Select a position row, then click 'Close Market'")

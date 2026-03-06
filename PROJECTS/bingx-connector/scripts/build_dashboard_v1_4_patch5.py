"""
build_dashboard_v1_4_patch5.py

Adds per-position TTP controls to the Live Trades action panel
AND patches signal_engine.py to respect per-position overrides.

Dashboard changes:
  P1 — CB-5 layout: adds TTP controls row (act% input, trail% input,
       "Set TTP" button, "Activate Now" button) below the existing
       action buttons.
  P2 — CB-17: Set TTP callback — writes ttp_act_override + ttp_dist_override
       to state.json for the selected position, and deletes the cached
       TTPExit engine so it gets recreated with new params.
  P3 — CB-18: Activate Now callback — writes ttp_force_activate=True to
       state.json for the selected position.

Bot-side changes:
  P4 — signal_engine.py: when creating TTPExit, read per-position
       ttp_act_override / ttp_dist_override from state. Also check
       ttp_force_activate flag to force ACTIVATED state.

Run:
    cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
    python scripts/build_dashboard_v1_4_patch5.py
"""
import py_compile
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DASH_TARGET = PROJECT / "bingx-live-dashboard-v1-4.py"
ENGINE_TARGET = PROJECT / "signal_engine.py"

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
# Load sources
# ---------------------------------------------------------------------------
dash_src = DASH_TARGET.read_text(encoding="utf-8")
engine_src = ENGINE_TARGET.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# P1 — CB-5 layout: add TTP controls row below existing action buttons
# ---------------------------------------------------------------------------
OLD_P1 = '''\
            # Hidden div to store selected symbol for API calls
            html.Div(id="selected-symbol", children=row["Symbol"],
                     style={"display": "none"}),
        ], style={'marginTop': '12px', 'padding': '12px',
                  'background': COLORS['panel'], 'borderRadius': '8px'})'''

NEW_P1 = '''\
            # --- TTP Controls Row ---
            html.Div([
                html.Span("TTP:", style={'fontWeight': 'bold', 'marginRight': '8px',
                                         'color': COLORS['text']}),
                html.Span("Act%", style={'color': COLORS['muted'], 'marginRight': '4px'}),
                dcc.Input(id="ttp-act-input", type="number", placeholder="0.5",
                          value=ttp_act_display, debounce=True, min=0.01, max=10, step=0.01,
                          style={'width': '70px', 'marginRight': '8px'}),
                html.Span("Trail%", style={'color': COLORS['muted'], 'marginRight': '4px'}),
                dcc.Input(id="ttp-dist-input", type="number", placeholder="0.2",
                          value=ttp_dist_display, debounce=True, min=0.01, max=10, step=0.01,
                          style={'width': '70px', 'marginRight': '12px'}),
                html.Button("Set TTP", id="set-ttp-btn", n_clicks=0,
                            style={'background': COLORS['blue'], 'color': 'white',
                                   'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer',
                                   'marginRight': '12px'}),
                html.Button("Activate Now", id="activate-ttp-btn", n_clicks=0,
                            disabled=ttp_already_activated,
                            style={'background': '#ff6600', 'color': 'white',
                                   'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer',
                                   'opacity': '0.4' if ttp_already_activated else '1'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginTop': '10px'}),
            # Hidden div to store selected symbol for API calls
            html.Div(id="selected-symbol", children=row["Symbol"],
                     style={"display": "none"}),
        ], style={'marginTop': '12px', 'padding': '12px',
                  'background': COLORS['panel'], 'borderRadius': '8px'})'''

dash_src = safe_replace("P1-ttp-controls-layout", dash_src, OLD_P1, NEW_P1)

# ---------------------------------------------------------------------------
# P1b — CB-5: add TTP display variables before the return block
# ---------------------------------------------------------------------------
OLD_P1B = '''\
        be_already_raised = row.get("BE Raised") == "Yes"
        return html.Div(['''

NEW_P1B = '''\
        be_already_raised = row.get("BE Raised") == "Yes"
        # TTP column shows "TRAILING" for ACTIVATED, raw state otherwise, or em-dash
        ttp_state_val = row.get("TTP", "")
        ttp_already_activated = ttp_state_val in ("TRAILING", "CLOSED")
        # Show per-position override if set, else global default from config
        ttp_act_display = None
        ttp_dist_display = None
        try:
            state = load_state()
            pos_key = f"{row['Symbol']}_{row['Dir']}"
            pos_data = state.get("open_positions", {}).get(pos_key, {})
            act_override = pos_data.get("ttp_act_override")
            dist_override = pos_data.get("ttp_dist_override")
            if act_override is not None:
                ttp_act_display = round(float(act_override) * 100, 2)
            if dist_override is not None:
                ttp_dist_display = round(float(dist_override) * 100, 2)
        except Exception:
            pass
        return html.Div(['''

dash_src = safe_replace("P1b-ttp-display-vars", dash_src, OLD_P1B, NEW_P1B)

# ---------------------------------------------------------------------------
# P2 — CB-17: Set TTP callback (after CB-16, before CB-8)
# ---------------------------------------------------------------------------
OLD_P2 = '''\

# ---------------------------------------------------------------------------
# CB-8: History Grid
# ---------------------------------------------------------------------------'''

NEW_P2 = '''\

# ---------------------------------------------------------------------------
# CB-17: Set TTP (per-position override)
# ---------------------------------------------------------------------------

@callback(
    Output('pos-action-status', 'children', allow_duplicate=True),
    Input('set-ttp-btn', 'n_clicks'),
    State('ttp-act-input', 'value'),
    State('ttp-dist-input', 'value'),
    State('positions-grid', 'selectedRows'),
    prevent_initial_call=True,
)
def set_ttp_override(n_clicks, act_pct, dist_pct, selected_rows):
    """Write per-position TTP activation and trail distance overrides to state.json."""
    try:
        if not n_clicks or not selected_rows:
            raise PreventUpdate
        row = selected_rows[0]
        symbol = row["Symbol"]
        direction = row["Dir"]
        pos_key = f"{symbol}_{direction}"

        if not act_pct or not dist_pct:
            return html.Span("Enter both Act% and Trail%",
                             style={'color': COLORS['orange']})
        if act_pct <= 0 or dist_pct <= 0:
            return html.Span("Values must be > 0",
                             style={'color': COLORS['orange']})

        act_frac = round(float(act_pct) / 100, 6)
        dist_frac = round(float(dist_pct) / 100, 6)

        state = load_state()
        if pos_key not in state.get("open_positions", {}):
            return html.Span(f"Position {pos_key} not found in state",
                             style={'color': COLORS['red']})

        state["open_positions"][pos_key]["ttp_act_override"] = act_frac
        state["open_positions"][pos_key]["ttp_dist_override"] = dist_frac
        # Delete engine cache flag so bot recreates with new params
        state["open_positions"][pos_key]["ttp_engine_dirty"] = True
        _write_state(state)

        LOG.info("TTP override set: %s act=%.4f dist=%.4f", pos_key, act_frac, dist_frac)
        return html.Span(
            f"TTP set for {symbol}: act={act_pct}% trail={dist_pct}%",
            style={'color': COLORS['green']},
        )
    except PreventUpdate:
        raise
    except Exception as e:
        LOG.error("Set TTP failed: %s", e, exc_info=True)
        return html.Span(f"Error: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-18: Activate TTP Now (force activate from current price)
# ---------------------------------------------------------------------------

@callback(
    Output('pos-action-status', 'children', allow_duplicate=True),
    Input('activate-ttp-btn', 'n_clicks'),
    State('positions-grid', 'selectedRows'),
    prevent_initial_call=True,
)
def activate_ttp_now(n_clicks, selected_rows):
    """Force-activate TTP for the selected position from current mark price."""
    symbol = "unknown"
    try:
        if not n_clicks or not selected_rows:
            raise PreventUpdate
        row = selected_rows[0]
        symbol = row["Symbol"]
        direction = row["Dir"]
        pos_key = f"{symbol}_{direction}"

        state = load_state()
        if pos_key not in state.get("open_positions", {}):
            return html.Span(f"Position {pos_key} not found",
                             style={'color': COLORS['red']})

        current_ttp = state["open_positions"][pos_key].get("ttp_state", "MONITORING")
        if current_ttp in ("ACTIVATED", "CLOSED"):
            return html.Span(f"TTP already {current_ttp} for {symbol}",
                             style={'color': COLORS['orange']})

        state["open_positions"][pos_key]["ttp_force_activate"] = True
        _write_state(state)

        LOG.info("TTP force activate requested: %s", pos_key)
        return html.Span(
            f"TTP activation requested for {symbol} {direction} (takes effect next tick)",
            style={'color': COLORS['green']},
        )
    except PreventUpdate:
        raise
    except Exception as e:
        LOG.error("Activate TTP failed for %s: %s", symbol, e, exc_info=True)
        return html.Span(f"Error: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-8: History Grid
# ---------------------------------------------------------------------------'''

dash_src = safe_replace("P2-cb17-cb18-ttp-callbacks", dash_src, OLD_P2, NEW_P2)

# ---------------------------------------------------------------------------
# Write dashboard
# ---------------------------------------------------------------------------
DASH_TARGET.write_text(dash_src, encoding="utf-8")
print(f"\nWrote: {DASH_TARGET}")

try:
    py_compile.compile(str(DASH_TARGET), doraise=True)
    print("py_compile (dashboard): PASS")
except py_compile.PyCompileError as e:
    print(f"py_compile (dashboard): FAIL -- {e}")
    ERRORS.append("py_compile-dashboard")

# ---------------------------------------------------------------------------
# P4 — signal_engine.py: per-position TTP overrides + force activate
# ---------------------------------------------------------------------------
OLD_P4 = '''\
                engine = TTPExit(
                    pos.get("direction", "LONG"),
                    entry,
                    self.ttp_act,
                    self.ttp_dist,
                )
                # Restore persisted TTP state on bot restart
                saved_state = pos.get("ttp_state", "MONITORING")
                saved_extreme = pos.get("ttp_extreme")
                saved_trail = pos.get("ttp_trail_level")
                if saved_state == "ACTIVATED" and saved_extreme and saved_trail:
                    engine.state = "ACTIVATED"
                    engine.extreme = float(saved_extreme)
                    engine.trail_level = float(saved_trail)
                    logger.info(
                        "TTP restored: %s state=ACTIVATED extreme=%.8f trail=%.8f",
                        key, engine.extreme, engine.trail_level)
                elif saved_state == "CLOSED":
                    engine.state = "CLOSED"
                    logger.info("TTP restored: %s state=CLOSED (skipping)", key)
                self.ttp_engines[key] = engine'''

NEW_P4 = '''\
                # Per-position TTP overrides from dashboard "Set TTP"
                pos_act = pos.get("ttp_act_override", self.ttp_act)
                pos_dist = pos.get("ttp_dist_override", self.ttp_dist)
                engine = TTPExit(
                    pos.get("direction", "LONG"),
                    entry,
                    pos_act,
                    pos_dist,
                )
                # Restore persisted TTP state on bot restart
                saved_state = pos.get("ttp_state", "MONITORING")
                saved_extreme = pos.get("ttp_extreme")
                saved_trail = pos.get("ttp_trail_level")
                if saved_state == "ACTIVATED" and saved_extreme and saved_trail:
                    engine.state = "ACTIVATED"
                    engine.extreme = float(saved_extreme)
                    engine.trail_level = float(saved_trail)
                    logger.info(
                        "TTP restored: %s state=ACTIVATED extreme=%.8f trail=%.8f",
                        key, engine.extreme, engine.trail_level)
                elif saved_state == "CLOSED":
                    engine.state = "CLOSED"
                    logger.info("TTP restored: %s state=CLOSED (skipping)", key)
                self.ttp_engines[key] = engine
            # Dashboard "Activate Now" — force to ACTIVATED from last candle extreme
            if pos.get("ttp_force_activate") and engine.state == "MONITORING":
                engine.state = "ACTIVATED"
                engine.extreme = h if pos.get("direction", "LONG") == "LONG" else l
                if pos.get("direction", "LONG") == "LONG":
                    engine.trail_level = engine.extreme * (1.0 - engine.dist)
                else:
                    engine.trail_level = engine.extreme * (1.0 + engine.dist)
                logger.info("TTP force-activated: %s extreme=%.8f trail=%.8f",
                            key, engine.extreme, engine.trail_level)
                self.state_manager.update_position(key, {
                    "ttp_force_activate": False,
                    "ttp_state": "ACTIVATED",
                    "ttp_trail_level": engine.trail_level,
                    "ttp_extreme": engine.extreme,
                })
            # Dashboard "Set TTP" with dirty flag — recreate engine with new params
            if pos.get("ttp_engine_dirty"):
                pos_act = pos.get("ttp_act_override", self.ttp_act)
                pos_dist = pos.get("ttp_dist_override", self.ttp_dist)
                new_engine = TTPExit(
                    pos.get("direction", "LONG"),
                    entry,
                    pos_act,
                    pos_dist,
                )
                self.ttp_engines[key] = new_engine
                engine = new_engine
                self.state_manager.update_position(key, {
                    "ttp_engine_dirty": False,
                    "ttp_state": "MONITORING",
                    "ttp_trail_level": None,
                    "ttp_extreme": None,
                })
                logger.info("TTP engine recreated: %s act=%.4f dist=%.4f",
                            key, pos_act, pos_dist)'''

engine_src = safe_replace("P4-engine-ttp-overrides", engine_src, OLD_P4, NEW_P4)

# ---------------------------------------------------------------------------
# P5 — position_monitor.py: add 0.1% slippage buffer to BE price
# ---------------------------------------------------------------------------
pm_target = PROJECT / "position_monitor.py"
pm_src = pm_target.read_text(encoding="utf-8")

OLD_P5 = '''\
        if direction == "LONG":
            be_price = entry_price * (1 + self.commission_rate)
        else:
            be_price = entry_price * (1 - self.commission_rate)
        commission_usd = round(notional * self.commission_rate, 4)'''

NEW_P5 = '''\
        # 0.1% slippage buffer on top of commission to prevent negative fills
        be_buffer = 0.001
        if direction == "LONG":
            be_price = entry_price * (1 + self.commission_rate + be_buffer)
        else:
            be_price = entry_price * (1 - self.commission_rate - be_buffer)
        commission_usd = round(notional * self.commission_rate, 4)'''

pm_src = safe_replace("P5-be-slippage-buffer", pm_src, OLD_P5, NEW_P5)

pm_target.write_text(pm_src, encoding="utf-8")
print(f"Wrote: {pm_target}")

try:
    py_compile.compile(str(pm_target), doraise=True)
    print("py_compile (position_monitor): PASS")
except py_compile.PyCompileError as e:
    print(f"py_compile (position_monitor): FAIL -- {e}")
    ERRORS.append("py_compile-position-monitor")

# ---------------------------------------------------------------------------
# Write signal_engine.py
# ---------------------------------------------------------------------------
ENGINE_TARGET.write_text(engine_src, encoding="utf-8")
print(f"Wrote: {ENGINE_TARGET}")

try:
    py_compile.compile(str(ENGINE_TARGET), doraise=True)
    print("py_compile (signal_engine): PASS")
except py_compile.PyCompileError as e:
    print(f"py_compile (signal_engine): FAIL -- {e}")
    ERRORS.append("py_compile-signal-engine")

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
    print("  1. Restart the bot:        python main.py")
    print("  2. Restart the dashboard:  python bingx-live-dashboard-v1-4.py")
    print("  3. Hard refresh browser:   Ctrl+Shift+R")
    print("  4. Select a position -> Set TTP (act%, trail%) or Activate Now")

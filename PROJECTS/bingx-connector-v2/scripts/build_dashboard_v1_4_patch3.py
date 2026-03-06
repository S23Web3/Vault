r"""
Build script: Dashboard v1.4 Patch 3 -- TTP columns + Controls toggle.
Patches bingx-live-dashboard-v1-4.py only.

Run:
    cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
    python scripts/build_dashboard_v1_4_patch3.py
"""
import sys
import py_compile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DASH_PATH = ROOT / "bingx-live-dashboard-v1-4.py"
ERRORS = []
PASS = []


def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def patch(old, new, label):
    """Replace old with new in dashboard file. Reports result."""
    content = DASH_PATH.read_text(encoding="utf-8")
    if old not in content:
        log(f"  PATCH SKIP ({label}): anchor not found")
        ERRORS.append(f"PATCH {label}: anchor not found")
        return False
    content = content.replace(old, new, 1)
    DASH_PATH.write_text(content, encoding="utf-8")
    log(f"  PATCH OK: {label}")
    return True


# =========================================================================
# D1: POSITION_COLUMNS -- add TTP + Trail Lvl after Dist SL %
# =========================================================================

def d1_position_columns():
    """Add TTP state and Trail Level columns to positions grid."""
    log("D1: Patching POSITION_COLUMNS ...")

    old = """\
    {'field': 'Dist SL %',  'width': 90, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value != null ? params.value.toFixed(2)+"%" : "\\u2014"'}},
    {'field': 'Duration',   'width': 90},"""

    new = """\
    {'field': 'Dist SL %',  'width': 90, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value != null ? params.value.toFixed(2)+"%" : "\\u2014"'}},
    {'field': 'TTP',        'width': 95,
     'cellStyle': {'function': "(p) => p.value==='TRAILING' ? {color:'#3fb950',fontWeight:'bold'} : p.value==='ACTIVATED' ? {color:'#e3b341'} : {color:'#8b949e'}"}},
    {'field': 'Trail Lvl',  'width': 110, 'type': 'numericColumn',
     'valueFormatter': {'function': "params.value != null ? params.value.toFixed(6) : '\\u2014'"}},
    {'field': 'Duration',   'width': 90},"""

    patch(old, new, "D1-columns")


# =========================================================================
# D2: build_positions_df -- add TTP and Trail Lvl to row dict
# =========================================================================

def d2_build_positions_df():
    """Add TTP state and trail level to positions row data."""
    log("D2: Patching build_positions_df ...")

    old = '''\
            "Dist SL %": dist_to_sl_pct,
            "Duration": fmt_duration(entry_dt, now),'''

    new = '''\
            "Dist SL %": dist_to_sl_pct,
            "TTP": "TRAILING" if pos.get("ttp_state") == "ACTIVATED" else (pos.get("ttp_state") or "\\u2014"),
            "Trail Lvl": pos.get("ttp_trail_level"),
            "Duration": fmt_duration(entry_dt, now),'''

    patch(old, new, "D2-positions-df")


# =========================================================================
# D3: Controls tab -- add TTP section
# =========================================================================

def d3_controls_layout():
    """Add TTP toggle + parameter inputs to Strategy Parameters tab."""
    log("D3: Patching Controls layout ...")

    # Insert TTP section between Position Sizing grid and the Save/Discard buttons
    old = """\
        ], style={'display': 'grid', 'gridTemplateColumns': '200px 1fr', 'gap': '8px',
                  'alignItems': 'center', 'maxWidth': '500px', 'marginBottom': '16px'}),

        html.Div([
            html.Button("Save Config", id='save-config-btn', n_clicks=0,"""

    new = """\
        ], style={'display': 'grid', 'gridTemplateColumns': '200px 1fr', 'gap': '8px',
                  'alignItems': 'center', 'maxWidth': '500px', 'marginBottom': '16px'}),

        # TTP Exit section
        html.H4("Trailing Take Profit (TTP)"),
        html.Div([
            html.Label("TTP Enabled"),
            dcc.Checklist(id='ctrl-ttp-enabled',
                          options=[{'label': ' Enable', 'value': 'on'}], value=[]),
            html.Label("Activation %"),
            dcc.Input(id='ctrl-ttp-act', type='number', step=0.1, min=0.1, max=5.0,
                      value=0.5),
            html.Label("Trail Distance %"),
            dcc.Input(id='ctrl-ttp-dist', type='number', step=0.05, min=0.05, max=2.0,
                      value=0.2),
        ], style={'display': 'grid', 'gridTemplateColumns': '200px 1fr', 'gap': '8px',
                  'alignItems': 'center', 'maxWidth': '500px', 'marginBottom': '16px'}),

        html.Div([
            html.Button("Save Config", id='save-config-btn', n_clicks=0,"""

    patch(old, new, "D3-controls-layout")


# =========================================================================
# D4: CB-11 (load_config_into_controls) -- add TTP outputs
# =========================================================================

def d4_cb11_load_config():
    """Add TTP outputs to CB-11 load_config_into_controls."""
    log("D4: Patching CB-11 ...")

    # --- D4a: Add 3 outputs to callback decorator ---
    old_decorator = """\
    Output('ctrl-margin-usd',         'value'),
    Output('ctrl-leverage',           'value'),
    Input('store-config', 'data'),"""

    new_decorator = """\
    Output('ctrl-margin-usd',         'value'),
    Output('ctrl-leverage',           'value'),
    Output('ctrl-ttp-enabled',        'value'),
    Output('ctrl-ttp-act',            'value'),
    Output('ctrl-ttp-dist',           'value'),
    Input('store-config', 'data'),"""

    patch(old_decorator, new_decorator, "D4a-cb11-outputs")

    # --- D4b: Add TTP values to return tuple ---
    old_return = """\
            pos.get("margin_usd", 5.0),
            pos.get("leverage", 10),
        )"""

    new_return = """\
            pos.get("margin_usd", 5.0),
            pos.get("leverage", 10),
            ['on'] if pos.get('ttp_enabled', False) else [],
            pos.get('ttp_act', 0.005) * 100,
            pos.get('ttp_dist', 0.002) * 100,
        )"""

    patch(old_return, new_return, "D4b-cb11-return")


# =========================================================================
# D5: CB-12 (save_config) -- add TTP inputs
# =========================================================================

def d5_cb12_save_config():
    """Add TTP inputs to CB-12 save_config."""
    log("D5: Patching CB-12 ...")

    # --- D5a: Add 3 State inputs to callback decorator ---
    old_states = """\
    State('ctrl-margin-usd',         'value'),
    State('ctrl-leverage',           'value'),
    prevent_initial_call=True,  # Do not fire on page load
)
def save_config(n_clicks, sl_mult, tp_mult, req_s2, rot_lvl,
                allow_a, allow_b, max_pos, max_trades,
                loss_limit, min_atr, cooldown, margin, leverage):"""

    new_states = """\
    State('ctrl-margin-usd',         'value'),
    State('ctrl-leverage',           'value'),
    State('ctrl-ttp-enabled',        'value'),
    State('ctrl-ttp-act',            'value'),
    State('ctrl-ttp-dist',           'value'),
    prevent_initial_call=True,  # Do not fire on page load
)
def save_config(n_clicks, sl_mult, tp_mult, req_s2, rot_lvl,
                allow_a, allow_b, max_pos, max_trades,
                loss_limit, min_atr, cooldown, margin, leverage,
                ttp_enabled_val, ttp_act_val, ttp_dist_val):"""

    patch(old_states, new_states, "D5a-cb12-inputs")

    # --- D5b: Add TTP writes after position leverage write ---
    old_write = """\
        cfg["position"]["leverage"] = int(leverage)

        # Atomic write"""

    new_write = """\
        cfg["position"]["leverage"] = int(leverage)
        cfg["position"]["ttp_enabled"] = 'on' in (ttp_enabled_val or [])
        cfg["position"]["ttp_act"] = (ttp_act_val or 0.5) / 100
        cfg["position"]["ttp_dist"] = (ttp_dist_val or 0.2) / 100

        # Atomic write"""

    patch(old_write, new_write, "D5b-cb12-write")


# =========================================================================
# Main
# =========================================================================

def main():
    """Run all dashboard patches."""
    log("=" * 60)
    log("Dashboard v1.4 Patch 3 -- TTP Display + Controls")
    log("=" * 60)

    if not DASH_PATH.exists():
        log(f"ERROR: Dashboard file not found: {DASH_PATH}")
        sys.exit(1)

    d1_position_columns()
    d2_build_positions_df()
    d3_controls_layout()
    d4_cb11_load_config()
    d5_cb12_save_config()

    # Final py_compile
    log("Final py_compile ...")
    try:
        py_compile.compile(str(DASH_PATH), doraise=True)
        log("  py_compile PASS: bingx-live-dashboard-v1-4.py")
        PASS.append("dashboard")
    except py_compile.PyCompileError as e:
        log(f"  py_compile FAIL: {e}")
        ERRORS.append(f"dashboard: {e}")

    log("")
    log("=" * 60)
    if ERRORS:
        log("FAILURES: " + ", ".join(ERRORS))
    else:
        log("ALL PATCHES PASSED")
    log("Passed: " + ", ".join(PASS))
    log("=" * 60)

    if ERRORS:
        sys.exit(1)


if __name__ == "__main__":
    main()

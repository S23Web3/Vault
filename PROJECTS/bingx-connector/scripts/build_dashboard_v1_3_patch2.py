"""
BingX Dashboard v1-3 Patch 2 -- visual fixes + position reconciliation.

Reads:  bingx-live-dashboard-v1-3.py + assets/dashboard.css
Writes: both files (in-place, backups created)

F1: Status bar -- add Equity card (realized + unrealized combined)
F2: CSS -- ID-based date picker dark + AG Grid CSS variables (grade + coin summary white rows)
F3: Equity curve -- extend with unrealized PnL dashed line
F4: CB-4 -- reconcile positions against BingX API (removes phantoms from state.json)

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/build_dashboard_v1_3_patch2.py
"""

import os
import py_compile
import shutil
from datetime import datetime

BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DASH_PATH = os.path.join(BASE, "bingx-live-dashboard-v1-3.py")
CSS_PATH = os.path.join(BASE, "assets", "dashboard.css")

errors = []


def report(label, ok, note=""):
    """Print pass/fail status for each patch step."""
    tag = "PASS" if ok else "FAIL"
    suffix = " -- " + note if note else ""
    print("  {}  {}{}".format(tag, label, suffix))
    if not ok:
        errors.append(label)


def safe_replace(src, old, new, label):
    """Replace old with new in src exactly once. Report pass/fail."""
    if old in src:
        src = src.replace(old, new, 1)
        report(label, True)
    else:
        report(label, False, "pattern not found")
    return src


# ── [1] Read source ──────────────────────────────────────────────────────
print("\n[1] Read source")
with open(DASH_PATH, "r", encoding="utf-8") as f:
    src = f.read()
print("  Read {} chars from {}".format(len(src), os.path.basename(DASH_PATH)))

with open(CSS_PATH, "r", encoding="utf-8") as f:
    css = f.read()
print("  Read {} chars from {}".format(len(css), os.path.basename(CSS_PATH)))


# ── [2] F1: Status bar -- add Equity card ────────────────────────────────
print("\n[2] F1: Status bar -- add Equity card")

OLD_F1 = '''        return html.Div([
            build_metric_card("Status", status_label, status_color),
            build_metric_card("Realized PnL", f"${daily_pnl:+.2f}", pnl_color),
            build_metric_card("Unreal. PnL", f"${unrealized_pnl:+.2f}", unreal_color),'''

NEW_F1 = '''        equity = daily_pnl + unrealized_pnl
        equity_color = COLORS['green'] if equity >= 0 else COLORS['red']

        return html.Div([
            build_metric_card("Status", status_label, status_color),
            build_metric_card("Equity", f"${equity:+.2f}", equity_color),
            build_metric_card("Realized", f"${daily_pnl:+.2f}", pnl_color),
            build_metric_card("Unrealized", f"${unrealized_pnl:+.2f}", unreal_color),'''

src = safe_replace(src, OLD_F1, NEW_F1, "CB-3: add Equity card")


# ── [3] F3a: CB-9 decorator -- add store-unrealized input ────────────────
print("\n[3] F3: Equity curve -- add unrealized to CB-9")

OLD_F3A = '''    Input('store-trades',            'data'),
    prevent_initial_call=True,  # Do not fire on page load -- stores not yet populated
)
def update_analytics(start_date, end_date, trades_json):'''

NEW_F3A = '''    Input('store-trades',            'data'),
    Input('store-unrealized',        'data'),
    prevent_initial_call=True,
)
def update_analytics(start_date, end_date, trades_json, unrealized_json):'''

src = safe_replace(src, OLD_F3A, NEW_F3A, "CB-9: add store-unrealized input")


# ── [4] F3b: Extend equity figure with unrealized PnL dashed line ────────
print("\n[4] F3b: Extend equity curve with unrealized")

OLD_F3B = '''        # Build charts
        equity_fig = build_equity_figure(df)
        dd_fig = build_drawdown_figure(df)'''

NEW_F3B = '''        # Build charts
        equity_fig = build_equity_figure(df)
        # Extend equity curve with current unrealized PnL (all-time view only)
        if unrealized_json and not df.empty and not start_date and not end_date:
            try:
                unreal_val = float(json.loads(unrealized_json))
                if unreal_val != 0.0:
                    df_sorted = df.sort_values("timestamp")
                    last_cum = float(df_sorted["pnl_net"].cumsum().iloc[-1])
                    equity_fig.add_trace(go.Scatter(
                        x=[df_sorted["timestamp"].iloc[-1], datetime.now(timezone.utc)],
                        y=[last_cum, last_cum + unreal_val],
                        mode='lines+markers',
                        line=dict(color=COLORS['blue'], width=2, dash='dash'),
                        marker=dict(size=6, color=COLORS['blue']),
                        name='+ Unrealized',
                        showlegend=True,
                    ))
            except Exception:
                pass
        dd_fig = build_drawdown_figure(df)'''

src = safe_replace(src, OLD_F3B, NEW_F3B, "equity curve: unrealized extension")


# ── [5] F4: CB-4 -- reconcile positions against BingX API ────────────────
print("\n[5] F4: Position reconciliation against BingX API")

# Add reconcile function after fetch_all_mark_prices
OLD_F4_FUNC = '''def fmt_duration(start_dt, end_dt=None) -> str:'''

NEW_F4_FUNC = '''def reconcile_positions(state: dict) -> dict:
    """Validate state.json positions against BingX API. Removes phantoms, writes cleaned state."""
    positions = state.get("open_positions", {})
    if not positions or not API_KEY or not SECRET_KEY:
        return state  # No positions or no API keys -- skip reconciliation
    try:
        data = _bingx_request('GET', '/openApi/swap/v2/user/positions', {})
        if 'error' in data:
            LOG.warning("Reconcile API error: %s -- using local state", data['error'])
            return state
        # Build set of live position keys from exchange
        live_positions = data if isinstance(data, list) else []
        live_keys = set()
        for pos in live_positions:
            amt = float(pos.get('positionAmt', 0))
            if amt == 0:
                continue
            sym = pos.get('symbol', '')
            side = pos.get('positionSide', '')
            if side in ('LONG', 'SHORT'):
                direction = side
            else:
                direction = 'LONG' if amt > 0 else 'SHORT'
            live_keys.add(sym + '_' + direction)
        # Remove phantom positions
        state_keys = set(positions.keys())
        phantoms = state_keys - live_keys
        if phantoms:
            for key in phantoms:
                LOG.warning("Reconcile: removing phantom position %s", key)
                state["open_positions"].pop(key, None)
            # Atomic write cleaned state
            _write_state(state)
            LOG.info("Reconcile: removed %d phantom positions", len(phantoms))
        else:
            LOG.debug("Reconcile: state matches exchange (%d positions)", len(state_keys))
    except Exception as e:
        LOG.warning("Reconcile failed: %s -- using local state", e)
    return state


def fmt_duration(start_dt, end_dt=None) -> str:'''

src = safe_replace(src, OLD_F4_FUNC, NEW_F4_FUNC, "add reconcile_positions function")

# Modify CB-4 to call reconcile before building positions
OLD_F4_CB = '''def update_positions_grid(state_json):
    """Load open positions with live mark prices into ag-grid. Outputs unrealized PnL to store."""
    try:
        if not state_json:
            return [], json.dumps(0.0)
        state = json.loads(state_json)
        positions = state.get("open_positions", {})
        if not positions:
            return [], json.dumps(0.0)'''

NEW_F4_CB = '''def update_positions_grid(state_json):
    """Load open positions with live mark prices into ag-grid. Outputs unrealized PnL to store."""
    try:
        if not state_json:
            return [], json.dumps(0.0)
        state = json.loads(state_json)
        # Reconcile against BingX API -- removes phantom positions
        state = reconcile_positions(state)
        positions = state.get("open_positions", {})
        if not positions:
            return [], json.dumps(0.0)'''

src = safe_replace(src, OLD_F4_CB, NEW_F4_CB, "CB-4: call reconcile_positions")


# ── [6] F2: CSS -- date pickers + AG Grid variables ──────────────────────
print("\n[6] F2: CSS additions (date pickers + AG Grid variables)")

CSS_ADDITIONS = '''
/* === DatePickerRange forced dark by component ID === */
#hist-date-range input,
#analytics-date-range input {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: none !important;
    font-family: 'Consolas', 'Monaco', monospace !important;
    font-size: 13px !important;
}
#hist-date-range > div,
#analytics-date-range > div,
#hist-date-range > div > div,
#analytics-date-range > div > div {
    background-color: #21262d !important;
    border-color: #484f58 !important;
}

/* === AG Grid theme variables (force dark rows for ALL grids inc. grade + coin summary) === */
.ag-theme-alpine-dark {
    --ag-background-color: #0d1117;
    --ag-odd-row-background-color: #0d1117;
    --ag-row-hover-color: #161b22;
    --ag-header-background-color: #161b22;
    --ag-header-foreground-color: #8b949e;
    --ag-foreground-color: #c9d1d9;
    --ag-border-color: #21262d;
    --ag-secondary-border-color: #21262d;
}
'''

if "DatePickerRange forced dark by component ID" not in css:
    css += CSS_ADDITIONS
    report("CSS: date picker + AG Grid variables", True)
else:
    report("CSS: date picker + AG Grid variables", False, "already applied")


# ── [7] Write files ──────────────────────────────────────────────────────
print("\n[7] Write files")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# Backup + write dashboard
bak_dash = DASH_PATH.replace(".py", ".{}.bak.py".format(ts))
shutil.copy2(DASH_PATH, bak_dash)
print("  Backup: {}".format(bak_dash))

with open(DASH_PATH, "w", encoding="utf-8") as f:
    f.write(src)
report("write " + os.path.basename(DASH_PATH), True)

try:
    py_compile.compile(DASH_PATH, doraise=True)
    report("py_compile dashboard", True)
except py_compile.PyCompileError as e:
    report("py_compile dashboard", False, str(e))

# Backup + write CSS
bak_css = CSS_PATH.replace(".css", ".{}.bak.css".format(ts))
shutil.copy2(CSS_PATH, bak_css)
print("  Backup: {}".format(bak_css))

with open(CSS_PATH, "w", encoding="utf-8") as f:
    f.write(css)
report("write " + os.path.basename(CSS_PATH), True)


# ── Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if errors:
    print("FAILURES: " + ", ".join(errors))
    print("{} error(s). Review output above.".format(len(errors)))
else:
    print("ALL PATCHES APPLIED SUCCESSFULLY")
    print("Run: python bingx-live-dashboard-v1-3.py")

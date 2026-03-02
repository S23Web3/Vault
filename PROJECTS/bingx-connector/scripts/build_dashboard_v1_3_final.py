"""
build_dashboard_v1_3_final.py

Comprehensive build: reads v1-2 (or v1-3 if exists), applies ALL fixes,
writes bingx-live-dashboard-v1-3.py.

Key change from original v1-3 build: Tab styling uses INLINE style props
(style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE) instead of CSS class
names. Inline styles bypass CSS selector matching issues entirely.

New feature: Unrealized PnL (equity) displayed in status bar via
store-unrealized dcc.Store. CB-4 computes it from mark prices (already
fetched), CB-3 displays it.

Run:
    cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
    python scripts/build_dashboard_v1_3_final.py
"""

import os
import py_compile
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
V12 = BASE / "bingx-live-dashboard-v1-2.py"
V13 = BASE / "bingx-live-dashboard-v1-3.py"
CSS_PATH = BASE / "assets" / "dashboard.css"
TEST_PATH = BASE / "scripts" / "test_dashboard.py"

ERRORS = []


def report(label, ok, detail=""):
    """Print pass/fail and track errors."""
    if ok:
        print("  PASS  {}".format(label))
    else:
        msg = "  FAIL  {}".format(label)
        if detail:
            msg += " -- {}".format(detail)
        print(msg)
        ERRORS.append(label)


def backup_if_exists(path):
    """Create timestamped backup if file exists."""
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_name = "{}.{}.bak{}".format(path.stem, ts, path.suffix)
        bak = path.parent / bak_name
        shutil.copy2(path, bak)
        print("  Backup: {}".format(bak))


def write_file(path, content, label):
    """Write content to file and report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    report("write {}".format(label), path.exists())


def safe_replace(src, old, new, label):
    """Replace old with new in src. Reports pass/fail. Returns updated src."""
    if old in src:
        src = src.replace(old, new)
        report(label, True)
    else:
        report(label, False, "pattern not found (may already be applied)")
    return src


# -----------------------------------------------------------------------
# 1. Read source (prefer v1-3 if exists, fallback to v1-2)
# -----------------------------------------------------------------------
print("\n[1] Read source")

if V13.exists():
    input_file = V13
    print("  Found v1-3, reading it")
elif V12.exists():
    input_file = V12
    print("  v1-3 not found, reading v1-2")
else:
    print("ERROR: neither v1-2 nor v1-3 found")
    exit(1)

with open(input_file, "r", encoding="utf-8") as f:
    src = f.read()

print("  Read {} chars from {}".format(len(src), input_file.name))


# -----------------------------------------------------------------------
# 2. Version-agnostic text replacements (skip if already applied)
# -----------------------------------------------------------------------
print("\n[2] Core text replacements")

CORE_REPLACEMENTS = [
    # Version bump
    ("BingX Live Dashboard v1-2", "BingX Live Dashboard v1-3",
     "version bump docstring/title"),
    ("bingx-live-dashboard-v1-2.py", "bingx-live-dashboard-v1-3.py",
     "version bump filename"),
    ("bingx_live_dashboard_v1_2", "bingx_live_dashboard_v1_3",
     "version bump module name"),
    # Add import io
    ("import json\n", "import io\nimport json\n",
     "add import io"),
    # Fix pd.read_json deprecation
    ("pd.read_json(trades_json, orient='split')",
     "pd.read_json(io.StringIO(trades_json), orient='split')",
     "fix pd.read_json deprecation"),
    # Rename Daily PnL to Realized PnL
    ('build_metric_card("Daily PnL"', 'build_metric_card("Realized PnL"',
     "rename Daily PnL to Realized PnL"),
    # Analytics date picker max-width
    ("], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),",
     "], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px', 'maxWidth': '500px'}),",
     "analytics date picker max-width"),
    # Grade comparison container
    ("html.Div(id='grade-comparison-table'),",
     "html.Div(id='grade-comparison-table', style={'maxWidth': '800px'}),",
     "grade comparison max-width"),
]

for old, new, label in CORE_REPLACEMENTS:
    if old in src:
        src = src.replace(old, new)
        report(label, True)
    # Silently skip if already applied


# -----------------------------------------------------------------------
# 3. Max DD% section replacement (P7)
# -----------------------------------------------------------------------
print("\n[3] Max DD% fix")

OLD_MAX_DD = """\
    # Max drawdown $ and %
    cum = df.sort_values("timestamp").pnl_net.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    max_dd = round(float(dd.min()), 4) if len(cum) > 0 else 0.0
    max_dd_pct = 0.0
    if len(cum) > 0:
        dd_idx = dd.idxmin()
        peak_at_dd = peak.loc[dd_idx]
        if peak_at_dd > 0:
            max_dd_pct = round(float(dd.loc[dd_idx] / peak_at_dd * 100), 2)"""

NEW_MAX_DD = """\
    # Max drawdown $ and % (capped at -100%, skip when peak < $1)
    cum = df.sort_values("timestamp").pnl_net.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    max_dd = round(float(dd.min()), 4) if len(cum) > 0 else 0.0
    max_dd_pct = 0.0
    if len(cum) > 0 and float(dd.min()) < 0:
        dd_idx = dd.idxmin()
        peak_at_dd = float(peak.loc[dd_idx])
        if peak_at_dd >= 1.0:
            max_dd_pct = round(float(dd.loc[dd_idx] / peak_at_dd * 100), 2)
            max_dd_pct = max(max_dd_pct, -100.0)  # Cap at -100%"""

src = safe_replace(src, OLD_MAX_DD, NEW_MAX_DD, "Max DD% cap fix")


# -----------------------------------------------------------------------
# 4. Tab inline styles (replaces CSS class name approach)
# -----------------------------------------------------------------------
print("\n[4] Tab inline styles")

# Insert TAB_STYLE constants after COLORS dict
TAB_CONSTANTS = """

# ---------------------------------------------------------------------------
# Tab styling constants -- inline styles bypass CSS class name issues
# ---------------------------------------------------------------------------

TAB_STYLE = {
    'backgroundColor': '#161b22', 'color': '#8b949e',
    'border': '1px solid #21262d', 'borderBottom': 'none',
    'padding': '10px 20px', 'cursor': 'pointer',
}

TAB_SELECTED_STYLE = {
    'backgroundColor': '#0d1117', 'color': '#58a6ff',
    'border': '1px solid #21262d', 'borderBottom': '2px solid #58a6ff',
    'padding': '10px 20px', 'fontWeight': 'bold',
}

"""

if "TAB_STYLE" not in src:
    anchor = "# ---------------------------------------------------------------------------\n# API keys"
    if anchor in src:
        src = src.replace(anchor, TAB_CONSTANTS.lstrip("\n") + anchor)
        report("insert TAB_STYLE/TAB_SELECTED_STYLE constants", True)
    else:
        report("insert TAB_STYLE constants", False, "API keys anchor not found")
else:
    report("TAB_STYLE constants already present", True)

# Replace Tabs container -- handle both v1-2 and v1-3 patterns
TABS_NEW = ("    dcc.Tabs(id='main-tabs', value='tab-ops',\n"
            "             parent_style={'backgroundColor': '#0d1117'},\n"
            "             style={'borderBottom': '1px solid #21262d'},\n"
            "             children=[")

tabs_v3 = "    dcc.Tabs(id='main-tabs', value='tab-ops', className='dash-tabs', children=["
tabs_v2 = "    dcc.Tabs(id='main-tabs', value='tab-ops', children=["

if tabs_v3 in src:
    src = src.replace(tabs_v3, TABS_NEW)
    report("Tabs container: inline parent_style (from v1-3)", True)
elif tabs_v2 in src:
    src = src.replace(tabs_v2, TABS_NEW)
    report("Tabs container: inline parent_style (from v1-2)", True)
elif "parent_style={'backgroundColor': '#0d1117'}" in src:
    report("Tabs container: already has inline styles", True)
else:
    report("Tabs container", False, "pattern not found")

# Replace each Tab -- handle v1-2 (plain), v1-3 (className), and already-fixed
TAB_LABELS = [
    ("'Operational',  value='tab-ops'", "'Operational',  value='tab-ops'"),
    ("'History',      value='tab-hist'", "'History',      value='tab-hist'"),
    ("'Analytics',    value='tab-analytics'", "'Analytics',    value='tab-analytics'"),
    ("'Coin Summary', value='tab-coins'", "'Coin Summary', value='tab-coins'"),
    ("'Bot Controls', value='tab-controls'", "'Bot Controls', value='tab-controls'"),
]

for label_part, _ in TAB_LABELS:
    # v1-3 pattern (with className)
    v3_pat = "dcc.Tab(label={}, className='dash-tab', selected_className='dash-tab--selected')".format(label_part)
    # v1-2 pattern (plain)
    v2_pat = "dcc.Tab(label={})".format(label_part)
    # New pattern (inline styles)
    new_pat = "dcc.Tab(label={}, style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE)".format(label_part)

    if v3_pat in src:
        src = src.replace(v3_pat, new_pat)
        report("Tab {} inline style (from v1-3)".format(label_part[:20]), True)
    elif v2_pat in src:
        src = src.replace(v2_pat, new_pat)
        report("Tab {} inline style (from v1-2)".format(label_part[:20]), True)
    elif "style=TAB_STYLE" in src and label_part in src:
        pass  # Already applied
    else:
        report("Tab {}".format(label_part[:20]), False, "pattern not found")


# -----------------------------------------------------------------------
# 5. Equity feature -- store-unrealized + CB-4 output + CB-3 display
# -----------------------------------------------------------------------
print("\n[5] Equity feature (Unrealized PnL)")

# 5a. Add store-unrealized to layout
if "store-unrealized" not in src:
    src = safe_replace(src,
        "    dcc.Store(id='store-config', storage_type='memory'),",
        "    dcc.Store(id='store-config', storage_type='memory'),\n"
        "    dcc.Store(id='store-unrealized', storage_type='memory'),",
        "add store-unrealized to layout")
else:
    report("store-unrealized already in layout", True)

# 5b. Replace CB-4 (positions grid) to output unrealized PnL
OLD_CB4 = """\
@callback(
    Output('positions-grid', 'rowData'),
    Input('store-state', 'data'),
    prevent_initial_call=True,  # Do not fire on page load \u2014 stores not yet populated
)
def update_positions_grid(state_json):
    \"\"\"Load open positions with live mark prices into ag-grid.\"\"\"
    try:
        if not state_json:
            return []
        state = json.loads(state_json)
        positions = state.get("open_positions", {})
        if not positions:
            return []
        symbols = [p["symbol"] for p in positions.values() if p.get("symbol")]
        mark_prices = fetch_all_mark_prices(symbols)
        LOG.debug("Mark prices fetched: %d/%d symbols", len(mark_prices), len(symbols))
        pos_df = build_positions_df(state, mark_prices)
        if pos_df.empty:
            return []
        return pos_df.to_dict('records')
    except Exception as e:
        LOG.error("Error loading positions: %s", e, exc_info=True)
        return []"""

NEW_CB4 = """\
@callback(
    Output('positions-grid', 'rowData'),
    Output('store-unrealized', 'data'),
    Input('store-state', 'data'),
    prevent_initial_call=True,  # Do not fire on page load \u2014 stores not yet populated
)
def update_positions_grid(state_json):
    \"\"\"Load open positions with live mark prices into ag-grid. Outputs unrealized PnL to store.\"\"\"
    try:
        if not state_json:
            return [], json.dumps(0.0)
        state = json.loads(state_json)
        positions = state.get("open_positions", {})
        if not positions:
            return [], json.dumps(0.0)
        symbols = [p["symbol"] for p in positions.values() if p.get("symbol")]
        mark_prices = fetch_all_mark_prices(symbols)
        LOG.debug("Mark prices fetched: %d/%d symbols", len(mark_prices), len(symbols))
        pos_df = build_positions_df(state, mark_prices)
        if pos_df.empty:
            return [], json.dumps(0.0)
        total_unreal = round(float(pos_df["Unreal PnL"].sum()), 4) if "Unreal PnL" in pos_df.columns else 0.0
        return pos_df.to_dict('records'), json.dumps(total_unreal)
    except Exception as e:
        LOG.error("Error loading positions: %s", e, exc_info=True)
        return [], json.dumps(0.0)"""

src = safe_replace(src, OLD_CB4, NEW_CB4, "CB-4: add unrealized PnL output")

# 5c. Modify CB-3 signature to accept unrealized store
OLD_CB3_SIG = """\
    Input('store-config', 'data'),
)
def update_status_bar(state_json, config_json):"""

NEW_CB3_SIG = """\
    Input('store-config', 'data'),
    Input('store-unrealized', 'data'),
)
def update_status_bar(state_json, config_json, unrealized_json):"""

if "Input('store-unrealized', 'data')" not in src:
    src = safe_replace(src, OLD_CB3_SIG, NEW_CB3_SIG, "CB-3: add unrealized input + param")
else:
    report("CB-3 unrealized input already present", True)

# 5d. Add unrealized PnL extraction in CB-3
OLD_DAILY = '        daily_pnl = float(state.get("daily_pnl", 0.0))'
NEW_DAILY = ('        daily_pnl = float(state.get("daily_pnl", 0.0))\n'
             '        unrealized_pnl = float(json.loads(unrealized_json)) if unrealized_json else 0.0\n'
             "        unreal_color = COLORS['green'] if unrealized_pnl >= 0 else COLORS['red']")

if "unrealized_pnl" not in src:
    src = safe_replace(src, OLD_DAILY, NEW_DAILY, "CB-3: extract unrealized PnL")
else:
    report("CB-3 unrealized extraction already present", True)

# 5e. Add Unreal. PnL card after Realized PnL card
REALIZED_CARD = '            build_metric_card("Realized PnL", f"${daily_pnl:+.2f}", pnl_color),'
UNREAL_CARD = ('            build_metric_card("Realized PnL", f"${daily_pnl:+.2f}", pnl_color),\n'
               '            build_metric_card("Unreal. PnL", f"${unrealized_pnl:+.2f}", unreal_color),')

if 'build_metric_card("Unreal. PnL"' not in src:
    src = safe_replace(src, REALIZED_CARD, UNREAL_CARD, "CB-3: add Unreal. PnL card")
else:
    report("CB-3 Unreal. PnL card already present", True)


# -----------------------------------------------------------------------
# 6. Write v1-3 dashboard
# -----------------------------------------------------------------------
print("\n[6] Write v1-3 dashboard")

if V13.exists():
    backup_if_exists(V13)

write_file(V13, src, "bingx-live-dashboard-v1-3.py")

try:
    py_compile.compile(str(V13), doraise=True)
    report("py_compile v1-3", True)
except py_compile.PyCompileError as e:
    report("py_compile v1-3", False, str(e))


# -----------------------------------------------------------------------
# 7. Write CSS (comprehensive dark theme)
# -----------------------------------------------------------------------
print("\n[7] Write CSS")

backup_if_exists(CSS_PATH)

CSS_CONTENT = """\
/* ===================================================================
   BingX Live Dashboard v1-3 -- Dark Theme CSS
   Comprehensive dark theme for all Dash, AG Grid, and form components
   Tab styling handled via inline style props -- CSS here is backup only
   =================================================================== */

/* === Base === */
body {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Consolas', 'Monaco', monospace;
    margin: 0;
}

/* === AG Grid row highlighting === */
.row-long  { background-color: rgba(63, 185, 80, 0.05) !important; }
.row-short { background-color: rgba(248, 81, 73, 0.05) !important; }

/* === Warning banner === */
.warning-banner {
    background-color: rgba(248, 81, 73, 0.10);
    border: 1px solid #f85149;
    padding: 12px 16px;
    border-radius: 4px;
    color: #c9d1d9;
}

/* === Dash tab styling (backup for inline styles) === */
.dash-tabs, .tab-parent, .tab-container,
div[class*="tab-parent"], div[class*="TabContainer"] {
    background-color: #0d1117 !important;
    border-bottom: 1px solid #21262d !important;
}

.dash-tab, .tab, .custom-tab,
div[class*="Tab--"] {
    background-color: #161b22 !important;
    color: #8b949e !important;
    border: 1px solid #21262d !important;
    border-bottom: none !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
}

.dash-tab--selected, .tab--selected, .custom-tab--selected,
div[class*="Tab--selected"] {
    background-color: #0d1117 !important;
    color: #58a6ff !important;
    border-bottom: 2px solid #58a6ff !important;
    font-weight: bold !important;
}

/* === Loading spinner === */
._dash-loading { background-color: rgba(13, 17, 23, 0.8); }

/* === Form inputs (visible contrast) === */
input[type="number"],
input[type="text"],
input[type="search"],
textarea,
.dash-input {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #484f58 !important;
    border-radius: 4px;
    padding: 6px 8px;
}

input:focus, textarea:focus {
    border-color: #58a6ff !important;
    outline: none;
    box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2) !important;
}

/* Number input spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    filter: invert(0.8);
}

/* === Labels === */
label { color: #c9d1d9 !important; }
.dash-radio label, .dash-checklist label { color: #c9d1d9 !important; }

/* === Dash Dropdown (React-Select) === */
.Select-control, .Select .Select-control {
    background-color: #21262d !important;
    border-color: #484f58 !important;
    color: #c9d1d9 !important;
}
.Select-value-label, .Select-placeholder, .Select-input > input {
    color: #c9d1d9 !important;
}
.Select-menu-outer, .Select-menu {
    background-color: #21262d !important;
    border-color: #484f58 !important;
}
.Select-option { background-color: #21262d !important; color: #c9d1d9 !important; }
.Select-option.is-focused, .Select-option.is-selected {
    background-color: #30363d !important;
}
.Select-arrow { border-color: #c9d1d9 transparent transparent !important; }
.Select-clear-zone { color: #8b949e !important; }
.dash-dropdown .VirtualizedSelectFocusedOption { background-color: #30363d !important; }

/* === DatePickerRange === */
.DateRangePickerInput, .DateRangePickerInput__withBorder,
.SingleDatePickerInput, .SingleDatePickerInput__withBorder {
    background-color: #21262d !important;
    border: 1px solid #484f58 !important;
    border-radius: 4px !important;
}
.DateInput { background-color: #21262d !important; }
.DateInput_input {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border-bottom: none !important;
    font-family: 'Consolas', 'Monaco', monospace !important;
    font-size: 13px !important;
    padding: 6px 8px !important;
}
.DateInput_input__focused { border-bottom: 2px solid #58a6ff !important; }
.DateRangePickerInput_arrow { color: #8b949e !important; }
.DateRangePickerInput_arrow svg { fill: #8b949e !important; }
.DateRangePickerInput_clearDates { background-color: transparent !important; }
.DateRangePickerInput_clearDates svg { fill: #8b949e !important; }

/* Calendar popup */
.DayPicker, .DayPicker__withBorder {
    background: #161b22 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5) !important;
}
.CalendarMonth { background: #161b22 !important; }
.CalendarMonth_caption { color: #c9d1d9 !important; }
.CalendarDay__default {
    background: #161b22 !important; color: #c9d1d9 !important;
    border: 1px solid #21262d !important;
}
.CalendarDay__default:hover { background: #30363d !important; }
.CalendarDay__selected, .CalendarDay__selected:hover {
    background: #58a6ff !important; color: #0d1117 !important;
    border: 1px solid #58a6ff !important;
}
.CalendarDay__selected_span {
    background: rgba(88, 166, 255, 0.2) !important;
    border: 1px solid #21262d !important;
}
.CalendarDay__blocked_out_of_range { color: #484f58 !important; }
.DayPickerNavigation_button__default {
    background: #21262d !important; border: 1px solid #30363d !important;
}
.DayPickerNavigation_button__default:hover { background: #30363d !important; }
.DayPickerNavigation_svg__horizontal { fill: #c9d1d9 !important; }
.DayPickerKeyboardShortcuts_buttonReset { display: none !important; }

/* === AG Grid === */
.ag-root-wrapper { background-color: #0d1117 !important; }
.ag-overlay-no-rows-wrapper { background-color: #0d1117 !important; color: #8b949e !important; }
.ag-header { background-color: #161b22 !important; border-bottom: 1px solid #21262d !important; }
.ag-header-cell { color: #8b949e !important; }
.ag-row { border-bottom: 1px solid #21262d !important; }
.ag-row:hover { background-color: #161b22 !important; }
.ag-cell { color: #c9d1d9 !important; }
.ag-paging-panel {
    background-color: #0d1117 !important; color: #8b949e !important;
    border-top: 1px solid #21262d !important;
}
.ag-paging-button { color: #c9d1d9 !important; }
.ag-popup, .ag-filter { background-color: #161b22 !important; }
.ag-text-field-input {
    background-color: #21262d !important; color: #c9d1d9 !important;
    border: 1px solid #484f58 !important;
}

/* === Scrollbar === */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #484f58; }
"""

write_file(CSS_PATH, CSS_CONTENT, "assets/dashboard.css")


# -----------------------------------------------------------------------
# 8. Update test script
# -----------------------------------------------------------------------
print("\n[8] Update test script")

backup_if_exists(TEST_PATH)

if TEST_PATH.exists():
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        test_src = f.read()

    # Version replacements
    test_src = test_src.replace("bingx-live-dashboard-v1-2", "bingx-live-dashboard-v1-3")
    test_src = test_src.replace("bingx_live_dashboard_v1_2", "bingx_live_dashboard_v1_3")
    # Also handle if already v1-3 (no-op)
    report("test: version refs updated", True)

    # Add max_dd_pct capping test if not present
    anchor = 'check("compute_metrics gross_pnl alias equals net_pnl", metrics["gross_pnl"] == metrics["net_pnl"])'
    dd_test = '\ncheck("compute_metrics max_dd_pct in valid range",\n      -100.0 <= metrics["max_dd_pct"] <= 0.0)\n'
    if "max_dd_pct in valid range" not in test_src and anchor in test_src:
        test_src = test_src.replace(anchor, anchor + dd_test)
        report("test: added max_dd_pct assertion", True)

    # Add store-unrealized layout check if not present
    store_test = '\ncheck("layout has store-unrealized", "store-unrealized" in all_ids)\n'
    store_anchor = 'check("layout has tab-content-controls", "tab-content-controls" in all_ids)'
    if "store-unrealized" not in test_src and store_anchor in test_src:
        test_src = test_src.replace(store_anchor, store_anchor + store_test)
        report("test: added store-unrealized layout check", True)

    write_file(TEST_PATH, test_src, "scripts/test_dashboard.py")

    try:
        py_compile.compile(str(TEST_PATH), doraise=True)
        report("py_compile test_dashboard.py", True)
    except py_compile.PyCompileError as e:
        report("py_compile test_dashboard.py", False, str(e))
else:
    report("test script not found", False, str(TEST_PATH))


# -----------------------------------------------------------------------
# 9. Summary
# -----------------------------------------------------------------------
print("\n" + "=" * 60)
if ERRORS:
    print("FAILURES: " + ", ".join(ERRORS))
    print("{} error(s). Review output above.".format(len(ERRORS)))
else:
    print("All checks passed. Files written:")
    print("  1. {}".format(V13))
    print("  2. {}".format(CSS_PATH))
    print("  3. {}".format(TEST_PATH))
    print("")
    print("Next steps:")
    print("  1. Run tests:     python scripts/test_dashboard.py")
    print("  2. Run dashboard: python bingx-live-dashboard-v1-3.py")
    print("  3. Verify: dark tabs, unrealized PnL card in status bar")

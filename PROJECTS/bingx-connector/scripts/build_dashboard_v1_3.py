"""
build_dashboard_v1_3.py

Patch build: reads bingx-live-dashboard-v1-2.py, applies targeted fixes,
writes bingx-live-dashboard-v1-3.py + updated CSS + updated test script.

Fixes applied:
  P1:  White selected tab -- fixed CSS selectors + className props on dcc.Tab
  P2:  White history/analytics/controls elements -- comprehensive dark CSS
  P3:  Input fields too dark (low contrast) -- lighter bg + visible borders
  P4:  Number input +/- spinners white -- CSS filter invert
  P5:  DatePickerRange too white/full-width -- CSS dark theme + maxWidth
  P6:  Grade comparison white bg + left-aligned -- maxWidth + dark CSS
  P7:  Max DD% calculation bug (-233%) -- cap at -100%, handle small peaks
  P8:  pd.read_json deprecation warning -- wrap in io.StringIO (3 locations)
  P9:  Daily PnL label ambiguous -- rename to "Realized PnL"
  P10: Version bump v1-2 -> v1-3

Run:
    cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
    python scripts/build_dashboard_v1_3.py
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


# -----------------------------------------------------------------------
# 1. Read v1-2 source
# -----------------------------------------------------------------------
print("\n[1] Read v1-2 source")

if not V12.exists():
    print("ERROR: v1-2 not found at {}".format(V12))
    exit(1)

with open(V12, "r", encoding="utf-8") as f:
    src = f.read()

print("  Read {} chars from v1-2".format(len(src)))


# -----------------------------------------------------------------------
# 2. Text replacements
# -----------------------------------------------------------------------
print("\n[2] Text replacements")

TEXT_REPLACEMENTS = [
    # P10: Version bump (docstring, run command, gunicorn, title)
    ("BingX Live Dashboard v1-2", "BingX Live Dashboard v1-3"),
    ("bingx-live-dashboard-v1-2.py", "bingx-live-dashboard-v1-3.py"),
    ("bingx_live_dashboard_v1_2", "bingx_live_dashboard_v1_3"),

    # P8: Add import io (before import json, alphabetical order)
    ("import json\n", "import io\nimport json\n"),

    # P8: Fix pd.read_json deprecation (all 3 occurrences: CB-8, CB-9, CB-10)
    ("pd.read_json(trades_json, orient='split')",
     "pd.read_json(io.StringIO(trades_json), orient='split')"),

    # P9: Status bar label clarity
    ('build_metric_card("Daily PnL"', 'build_metric_card("Realized PnL"'),

    # P1: Tab classNames for CSS targeting
    ("dcc.Tab(label='Operational',  value='tab-ops')",
     "dcc.Tab(label='Operational',  value='tab-ops', className='dash-tab', selected_className='dash-tab--selected')"),
    ("dcc.Tab(label='History',      value='tab-hist')",
     "dcc.Tab(label='History',      value='tab-hist', className='dash-tab', selected_className='dash-tab--selected')"),
    ("dcc.Tab(label='Analytics',    value='tab-analytics')",
     "dcc.Tab(label='Analytics',    value='tab-analytics', className='dash-tab', selected_className='dash-tab--selected')"),
    ("dcc.Tab(label='Coin Summary', value='tab-coins')",
     "dcc.Tab(label='Coin Summary', value='tab-coins', className='dash-tab', selected_className='dash-tab--selected')"),
    ("dcc.Tab(label='Bot Controls', value='tab-controls')",
     "dcc.Tab(label='Bot Controls', value='tab-controls', className='dash-tab', selected_className='dash-tab--selected')"),

    # P1: Tabs container className
    ("dcc.Tabs(id='main-tabs', value='tab-ops', children=[",
     "dcc.Tabs(id='main-tabs', value='tab-ops', className='dash-tabs', children=["),

    # P5: Analytics date picker constrained width
    ("], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),",
     "], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px', 'maxWidth': '500px'}),"),

    # P6: Grade comparison container max-width
    ("html.Div(id='grade-comparison-table'),",
     "html.Div(id='grade-comparison-table', style={'maxWidth': '800px'}),"),
]

for old, new in TEXT_REPLACEMENTS:
    count = src.count(old)
    if count == 0:
        report("replace: {}".format(old[:60]), False, "not found in source")
    else:
        src = src.replace(old, new)
        report("replace: {} ({})".format(old[:60], count), True)


# -----------------------------------------------------------------------
# 3. Section replacement -- Max DD% calculation (P7)
# -----------------------------------------------------------------------
print("\n[3] Section replacement -- Max DD% fix")

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
    # Max drawdown $ and % (P7 fix: cap at -100%, skip when peak < $1)
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

if OLD_MAX_DD in src:
    src = src.replace(OLD_MAX_DD, NEW_MAX_DD)
    report("replace Max DD% section", True)
else:
    report("replace Max DD% section", False, "old block not found")


# -----------------------------------------------------------------------
# 4. Write v1-3 dashboard
# -----------------------------------------------------------------------
print("\n[4] Write v1-3 dashboard")

if V13.exists():
    backup_if_exists(V13)

write_file(V13, src, "bingx-live-dashboard-v1-3.py")

try:
    py_compile.compile(str(V13), doraise=True)
    report("py_compile v1-3", True)
except py_compile.PyCompileError as e:
    report("py_compile v1-3", False, str(e))


# -----------------------------------------------------------------------
# 5. Write CSS (with backup)
# -----------------------------------------------------------------------
print("\n[5] Write CSS")

backup_if_exists(CSS_PATH)

CSS_CONTENT = """\
/* ===================================================================
   BingX Live Dashboard v1-3 -- Dark Theme CSS
   Comprehensive dark theme for all Dash, AG Grid, and form components
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

/* === Dash tab styling (P1 fix) ===
   Targets all possible Dash tab class names for compatibility */
.dash-tabs,
.tab-parent,
.tab-container {
    background-color: #0d1117 !important;
    border-bottom: 1px solid #21262d !important;
}

.dash-tab,
.tab,
.custom-tab {
    background-color: #161b22 !important;
    color: #8b949e !important;
    border: 1px solid #21262d !important;
    border-bottom: none !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: background-color 0.15s !important;
}

.dash-tab:hover,
.tab:hover,
.custom-tab:hover {
    background-color: #1c2128 !important;
    color: #c9d1d9 !important;
}

.dash-tab--selected,
.tab--selected,
.custom-tab--selected {
    background-color: #0d1117 !important;
    color: #58a6ff !important;
    border: 1px solid #21262d !important;
    border-bottom: 2px solid #58a6ff !important;
    font-weight: bold !important;
}

/* === Loading spinner dark background === */
._dash-loading { background-color: rgba(13, 17, 23, 0.8); }

/* === Form inputs (P3 fix -- visible contrast against dark bg) === */
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

input[type="number"]:focus,
input[type="text"]:focus,
textarea:focus {
    border-color: #58a6ff !important;
    outline: none;
    box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2) !important;
}

/* Number input spinner buttons (P4 fix) */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    filter: invert(0.8);
}

/* === Labels === */
label {
    color: #c9d1d9 !important;
}

/* === Dash radio items + checklists === */
.dash-radio label,
.dash-checklist label {
    color: #c9d1d9 !important;
}

/* === Dash Dropdown (React-Select internals) === */
.Select-control,
.Select .Select-control {
    background-color: #21262d !important;
    border-color: #484f58 !important;
    color: #c9d1d9 !important;
}

.Select-value-label,
.Select-placeholder,
.Select-input > input {
    color: #c9d1d9 !important;
}

.Select-menu-outer,
.Select-menu {
    background-color: #21262d !important;
    border-color: #484f58 !important;
}

.Select-option {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
}

.Select-option.is-focused,
.Select-option.is-selected {
    background-color: #30363d !important;
    color: #c9d1d9 !important;
}

.Select-arrow {
    border-color: #c9d1d9 transparent transparent !important;
}

.Select-clear-zone {
    color: #8b949e !important;
}

.dash-dropdown .VirtualizedSelectFocusedOption {
    background-color: #30363d !important;
}

/* === DatePickerRange (P5 fix -- comprehensive dark theme) === */
.DateRangePickerInput,
.DateRangePickerInput__withBorder,
.SingleDatePickerInput,
.SingleDatePickerInput__withBorder {
    background-color: #21262d !important;
    border: 1px solid #484f58 !important;
    border-radius: 4px !important;
}

.DateInput {
    background-color: #21262d !important;
}

.DateInput_input {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border-bottom: none !important;
    font-family: 'Consolas', 'Monaco', monospace !important;
    font-size: 13px !important;
    padding: 6px 8px !important;
}

.DateInput_input__focused {
    border-bottom: 2px solid #58a6ff !important;
}

.DateRangePickerInput_arrow {
    color: #8b949e !important;
}

.DateRangePickerInput_arrow svg {
    fill: #8b949e !important;
}

.DateRangePickerInput_clearDates {
    background-color: transparent !important;
}

.DateRangePickerInput_clearDates svg {
    fill: #8b949e !important;
}

/* Calendar popup */
.DayPicker,
.DayPicker__withBorder {
    background: #161b22 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5) !important;
}

.CalendarMonth {
    background: #161b22 !important;
}

.CalendarMonth_caption {
    color: #c9d1d9 !important;
}

.CalendarDay__default {
    background: #161b22 !important;
    color: #c9d1d9 !important;
    border: 1px solid #21262d !important;
}

.CalendarDay__default:hover {
    background: #30363d !important;
    color: #c9d1d9 !important;
}

.CalendarDay__selected,
.CalendarDay__selected:hover {
    background: #58a6ff !important;
    color: #0d1117 !important;
    border: 1px solid #58a6ff !important;
}

.CalendarDay__selected_span {
    background: rgba(88, 166, 255, 0.2) !important;
    color: #c9d1d9 !important;
    border: 1px solid #21262d !important;
}

.CalendarDay__hovered_span {
    background: rgba(88, 166, 255, 0.1) !important;
    color: #c9d1d9 !important;
}

.CalendarDay__blocked_out_of_range {
    color: #484f58 !important;
}

.DayPickerNavigation_button__default {
    background: #21262d !important;
    border: 1px solid #30363d !important;
}

.DayPickerNavigation_button__default:hover {
    background: #30363d !important;
}

.DayPickerNavigation_svg__horizontal {
    fill: #c9d1d9 !important;
}

.DayPickerKeyboardShortcuts_buttonReset {
    display: none !important;
}

/* === AG Grid dark backgrounds (comprehensive) === */
.ag-root-wrapper {
    background-color: #0d1117 !important;
}

.ag-overlay-no-rows-wrapper {
    background-color: #0d1117 !important;
    color: #8b949e !important;
}

.ag-header {
    background-color: #161b22 !important;
    border-bottom: 1px solid #21262d !important;
}

.ag-header-cell {
    color: #8b949e !important;
}

.ag-row {
    border-bottom: 1px solid #21262d !important;
}

.ag-row:hover {
    background-color: #161b22 !important;
}

.ag-cell {
    color: #c9d1d9 !important;
}

/* AG Grid pagination */
.ag-paging-panel {
    background-color: #0d1117 !important;
    color: #8b949e !important;
    border-top: 1px solid #21262d !important;
}

.ag-paging-button {
    color: #c9d1d9 !important;
}

/* AG Grid filter popup */
.ag-popup {
    background-color: #161b22 !important;
}

.ag-filter {
    background-color: #161b22 !important;
}

.ag-text-field-input {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #484f58 !important;
}

/* === Scrollbar dark theme === */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #0d1117;
}

::-webkit-scrollbar-thumb {
    background: #30363d;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #484f58;
}
"""

write_file(CSS_PATH, CSS_CONTENT, "assets/dashboard.css")


# -----------------------------------------------------------------------
# 6. Update test script (with backup)
# -----------------------------------------------------------------------
print("\n[6] Update test script")

backup_if_exists(TEST_PATH)

if not TEST_PATH.exists():
    report("read test script", False, "file not found")
else:
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        test_src = f.read()

    # Version replacements
    v2_count = test_src.count("bingx-live-dashboard-v1-2")
    test_src = test_src.replace("bingx-live-dashboard-v1-2", "bingx-live-dashboard-v1-3")
    test_src = test_src.replace("bingx_live_dashboard_v1_2", "bingx_live_dashboard_v1_3")
    report("test: version refs updated ({} replacements)".format(v2_count), v2_count > 0)

    # Add max_dd_pct capping test after existing compute_metrics tests
    anchor = 'check("compute_metrics gross_pnl alias equals net_pnl", metrics["gross_pnl"] == metrics["net_pnl"])'
    new_test_block = anchor + "\n" + "\n".join([
        "",
        "# 4e. compute_metrics -- max_dd_pct capping (v1-3 fix)",
        'check("compute_metrics max_dd_pct in valid range",',
        "      -100.0 <= metrics[\"max_dd_pct\"] <= 0.0)",
    ]) + "\n"

    if anchor in test_src:
        test_src = test_src.replace(anchor, new_test_block)
        report("test: added max_dd_pct capping assertion", True)
    else:
        report("test: added max_dd_pct capping assertion", False, "anchor not found")

    write_file(TEST_PATH, test_src, "scripts/test_dashboard.py")

    try:
        py_compile.compile(str(TEST_PATH), doraise=True)
        report("py_compile test_dashboard.py", True)
    except py_compile.PyCompileError as e:
        report("py_compile test_dashboard.py", False, str(e))


# -----------------------------------------------------------------------
# 7. Summary
# -----------------------------------------------------------------------
print("\n" + "=" * 60)
if ERRORS:
    print("FAILURES: " + ", ".join(ERRORS))
    print("{} error(s). Review and fix before running.".format(len(ERRORS)))
else:
    print("All checks passed. Files written:")
    print("  1. {}".format(V13))
    print("  2. {}".format(CSS_PATH))
    print("  3. {}".format(TEST_PATH))
    print("")
    print("Next steps:")
    print('  1. Run tests:     python scripts/test_dashboard.py')
    print('  2. Run dashboard: python bingx-live-dashboard-v1-3.py')
    print("  3. Visual verification of all 10 fixes")

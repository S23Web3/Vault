"""
BingX Dashboard v1-3 Patch 5 -- Comprehensive fix (trade filter + stale session + CSS + coin detail).

Reads:  bingx-live-dashboard-v1-3.py + assets/dashboard.css
Writes: both files (in-place, backups created)

P1: load_trades() -- filter by date >= 2026-02-27 (excludes demo phases)
P2: CB-3 -- stale session detection (zero daily_trades/daily_pnl when bot not running today)
P3: Coin Summary -- add row selection + detail section + new CB-15
P4: CSS -- nuclear dark fix for ALL remaining white elements (dropdowns, date pickers, inputs)

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/build_dashboard_v1_3_patch5.py
"""

import os
import py_compile
import shutil
from datetime import datetime

BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DASH_PATH = os.path.join(BASE, "bingx-live-dashboard-v1-3.py")
CSS_PATH = os.path.join(BASE, "assets", "dashboard.css")

ERRORS = []


def report(label, ok, note=""):
    """Print pass/fail status for each patch step."""
    tag = "PASS" if ok else "FAIL"
    suffix = " -- " + note if note else ""
    print("  {}  {}{}".format(tag, label, suffix))
    if not ok:
        ERRORS.append(label)


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


# ── [2] P1: Trade date filter ─────────────────────────────────────────────
print("\n[2] P1: Filter trades by date (>= 2026-02-27)")

OLD_P1 = '''        df["exit_price"] = pd.to_numeric(df["exit_price"], errors="coerce")
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)'''

NEW_P1 = '''        df["exit_price"] = pd.to_numeric(df["exit_price"], errors="coerce")
        # Filter to bot trades only (bot started 2026-02-27, prior = demo phases)
        cutoff = pd.Timestamp("2026-02-27", tz="UTC")
        df = df[df["timestamp"] >= cutoff]
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)'''

src = safe_replace(src, OLD_P1, NEW_P1, "load_trades: date filter >= 2026-02-27")


# ── [3] P2: Stale session detection ───────────────────────────────────────
print("\n[3] P2: Stale session detection in CB-3")

OLD_P2A = '''        daily_pnl = float(state.get("daily_pnl", 0.0))
        # Parse balance data from BingX API (via store-unrealized)'''

NEW_P2A = '''        # Detect stale session -- if session_start is not today, counters are stale
        session_start_str = state.get("session_start", "")
        session_is_today = False
        if session_start_str:
            try:
                session_dt = datetime.fromisoformat(session_start_str)
                session_is_today = session_dt.date() == datetime.now(timezone.utc).date()
            except (ValueError, TypeError):
                pass
        daily_pnl = float(state.get("daily_pnl", 0.0)) if session_is_today else 0.0
        # Parse balance data from BingX API (via store-unrealized)'''

src = safe_replace(src, OLD_P2A, NEW_P2A, "CB-3: stale session -> daily_pnl")

OLD_P2B = '''        open_count = len(state.get("open_positions", {}))
        daily_trades = int(state.get("daily_trades", 0))'''

NEW_P2B = '''        open_count = len(state.get("open_positions", {}))
        daily_trades = int(state.get("daily_trades", 0)) if session_is_today else 0'''

src = safe_replace(src, OLD_P2B, NEW_P2B, "CB-3: stale session -> daily_trades")


# ── [4] P3: Coin Summary -- row selection + detail section ────────────────
print("\n[4] P3: Coin Summary interactivity")

# P3a: Add row selection to grid + detail div
OLD_P3A = '''        dag.AgGrid(id='coin-summary-grid', columnDefs=COIN_COLUMNS, rowData=[],
                   defaultColDef={'sortable': True, 'resizable': True},
                   dashGridOptions={'pagination': True, 'paginationPageSize': 50},
                   className='ag-theme-alpine-dark', style={'height': '600px'}),
        html.Div(id='coin-summary-caption',
                 style={'color': COLORS['muted'], 'marginTop': '8px'}),
    ])'''

NEW_P3A = '''        dag.AgGrid(id='coin-summary-grid', columnDefs=COIN_COLUMNS, rowData=[],
                   defaultColDef={'sortable': True, 'resizable': True},
                   dashGridOptions={'pagination': True, 'paginationPageSize': 50,
                                    'rowSelection': 'single'},
                   className='ag-theme-alpine-dark', style={'height': '400px'}),
        html.Div(id='coin-summary-caption',
                 style={'color': COLORS['muted'], 'marginTop': '8px'}),
        html.Div(id='coin-detail-section',
                 children=html.Div("Click a coin row to see its trades.",
                                   style={'color': COLORS['muted']}),
                 style={'marginTop': '16px'}),
    ])'''

src = safe_replace(src, OLD_P3A, NEW_P3A, "coin summary: add row selection + detail div")

# P3b: Add CB-15 callback for coin detail (insert before entry point)
OLD_P3B = '''# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------'''

COIN_DETAIL_COLS = '''[
            {'field': 'Date'},
            {'field': 'Dir', 'width': 80},
            {'field': 'Grade', 'width': 80},
            {'field': 'Entry'},
            {'field': 'Exit'},
            {'field': 'Exit Reason'},
            {'field': 'Net PnL', 'cellStyle': {
                'styleConditions': [
                    {'condition': 'params.value >= 0', 'style': {'color': '#3fb950'}},
                    {'condition': 'params.value < 0', 'style': {'color': '#f85149'}},
                ],
            }},
            {'field': 'Duration'},
        ]'''

NEW_P3B = '''# ---------------------------------------------------------------------------
# CB-15: Coin Detail (click coin row -> show trades)
# ---------------------------------------------------------------------------

@callback(
    Output('coin-detail-section', 'children'),
    Input('coin-summary-grid', 'selectedRows'),
    Input('store-trades', 'data'),
    prevent_initial_call=True,
)
def show_coin_detail(selected_rows, trades_json):
    """Show individual trades for the selected coin."""
    try:
        if not selected_rows or not trades_json:
            return html.Div("Click a coin row to see its trades.",
                            style={'color': COLORS['muted']})
        symbol = selected_rows[0].get('Symbol', '')
        if not symbol:
            return html.Div("No symbol selected.", style={'color': COLORS['muted']})

        df = pd.read_json(io.StringIO(trades_json), orient='split')
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
        coin_df = df[df["symbol"] == symbol].copy()

        if coin_df.empty:
            return html.Div("No trades for " + symbol, style={'color': COLORS['muted']})

        coin_df = coin_df.sort_values("timestamp", ascending=False)
        coin_df["Date"] = coin_df["timestamp"].dt.strftime("%m-%d %H:%M")
        coin_df["Duration"] = coin_df.apply(
            lambda r: fmt_duration(r["entry_time"], r["timestamp"]), axis=1)

        coin_df = coin_df.rename(columns={
            "direction": "Dir", "grade": "Grade",
            "entry_price": "Entry", "exit_price": "Exit",
            "exit_reason": "Exit Reason", "pnl_net": "Net PnL",
        })

        display_cols = ["Date", "Dir", "Grade", "Entry", "Exit",
                        "Exit Reason", "Net PnL", "Duration"]
        display_cols = [c for c in display_cols if c in coin_df.columns]

        total = round(float(coin_df["Net PnL"].sum()), 4)
        wins = len(coin_df[coin_df["Net PnL"] > 0])
        losses = len(coin_df[coin_df["Net PnL"] <= 0])
        wr = round(wins / len(coin_df) * 100, 1) if len(coin_df) > 0 else 0
        pnl_color = COLORS['green'] if total >= 0 else COLORS['red']

        detail_cols = ''' + COIN_DETAIL_COLS + '''

        return html.Div([
            html.H4(symbol + " -- " + str(len(coin_df)) + " trades",
                     style={'marginBottom': '8px'}),
            html.Div([
                build_metric_card("Trades", str(len(coin_df))),
                build_metric_card("Wins", str(wins), COLORS['green']),
                build_metric_card("Losses", str(losses), COLORS['red']),
                build_metric_card("Win Rate", "{:.1f}%".format(wr),
                                  COLORS['green'] if wr >= 50 else COLORS['red']),
                build_metric_card("Net PnL", "${:+.4f}".format(total), pnl_color),
            ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '12px'}),
            dag.AgGrid(
                columnDefs=detail_cols,
                rowData=coin_df[display_cols].to_dict('records'),
                defaultColDef={'sortable': True},
                className='ag-theme-alpine-dark',
                style={'height': '300px'},
            ),
        ])
    except Exception as e:
        LOG.error("Error in coin detail: %s", e, exc_info=True)
        return html.Div("Error: " + str(e), style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------'''

src = safe_replace(src, OLD_P3B, NEW_P3B, "add CB-15: coin detail callback")


# ── [5] P4: CSS -- comprehensive dark fix ─────────────────────────────────
print("\n[5] P4: CSS -- comprehensive dark fix for ALL white elements")

CSS_NUCLEAR = '''
/* === COMPREHENSIVE DARK FIX (Patch 5) ===================================
   Targets ALL white-background components by ID and descendant selectors.
   This section is the final authority on dark styling.
   ======================================================================== */

/* --- Dropdown controls (History tab filters) --- */
#hist-dir-filter div,
#hist-grade-filter div,
#hist-exit-filter div {
    background-color: #21262d !important;
    background: #21262d !important;
    border-color: #484f58 !important;
    color: #c9d1d9 !important;
}
#hist-dir-filter input,
#hist-grade-filter input,
#hist-exit-filter input,
#hist-dir-filter span,
#hist-grade-filter span,
#hist-exit-filter span {
    color: #c9d1d9 !important;
}
#hist-dir-filter svg,
#hist-grade-filter svg,
#hist-exit-filter svg {
    fill: #8b949e !important;
}

/* --- Dropdown menu (portaled to body, not inside component wrapper) --- */
.Select-menu-outer,
.Select-menu,
.VirtualizedSelectOption,
div[class*="menu"] {
    background-color: #21262d !important;
    border-color: #484f58 !important;
}
.Select-option,
div[class*="option"] {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
}
.Select-option.is-focused,
.Select-option.is-selected,
div[class*="option"]:hover {
    background-color: #30363d !important;
}

/* --- DatePickerRange (nuclear -- ALL descendants) --- */
#hist-date-range *,
#analytics-date-range * {
    background-color: #21262d !important;
    background: #21262d !important;
    border-color: #484f58 !important;
    color: #c9d1d9 !important;
}
/* Restore calendar popup selected day color */
.CalendarDay__selected,
.CalendarDay__selected:hover,
.CalendarDay__selected_span {
    background-color: #58a6ff !important;
    background: #58a6ff !important;
    color: #0d1117 !important;
}
.CalendarDay__default:hover {
    background: #30363d !important;
}

/* --- AG Grid pagination dropdown --- */
.ag-paging-panel select,
.ag-page-size select,
.ag-page-size .ag-select,
.ag-page-size .ag-select .ag-picker-field-wrapper {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border-color: #484f58 !important;
}

/* --- RadioItems (Coin Summary period filter) --- */
.dash-radioitems label,
.dash-radioitems input[type="radio"] {
    color: #c9d1d9 !important;
}
#coin-period-filter label {
    color: #c9d1d9 !important;
    cursor: pointer;
}

/* --- Catch-all for any remaining white form elements --- */
select, option {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
}
'''

if "COMPREHENSIVE DARK FIX (Patch 5)" not in css:
    css += CSS_NUCLEAR
    report("CSS: comprehensive dark fix", True)
else:
    report("CSS: comprehensive dark fix", False, "already applied")


# ── [6] Write files ───────────────────────────────────────────────────────
print("\n[6] Write files")
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


# ── Summary ───────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if ERRORS:
    print("FAILURES: " + ", ".join(ERRORS))
    print("{} error(s). Review output above.".format(len(ERRORS)))
else:
    print("ALL PATCHES APPLIED SUCCESSFULLY")
    print("Run: python bingx-live-dashboard-v1-3.py")
    print("\nChanges:")
    print("  - Trades filtered to >= 2026-02-27 (excludes demo phases)")
    print("  - Daily Trades + Risk Used zero when bot not running today")
    print("  - Click any coin in Coin Summary to see its trades")
    print("  - ALL white backgrounds eliminated (dropdowns, date pickers, selects)")

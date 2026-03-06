"""
BingX Dashboard v1-3 Patch 4 -- Trade filter + stale session detection + CSS fix.

Reads:  bingx-live-dashboard-v1-3.py + assets/dashboard.css
Writes: both files (in-place, backups created)

P1: load_trades() -- filter to live bot trades only (notional <= 100, excludes $500/$1500 demo)
P2: CB-3 -- detect stale session (session_start not today) -> zero daily_trades and daily_pnl
P3: CSS -- aggressive date picker dark background selectors

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/build_dashboard_v1_3_patch4.py
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


# ── [2] P1: Filter trades to live bot only ────────────────────────────────
print("\n[2] P1: Filter trades to live bot only (exclude demo phases)")

OLD_P1 = '''        df["exit_price"] = pd.to_numeric(df["exit_price"], errors="coerce")
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)'''

NEW_P1 = '''        df["exit_price"] = pd.to_numeric(df["exit_price"], errors="coerce")
        # Filter to live bot trades only (exclude demo phases: $500/$1500 notional)
        if "notional_usd" in df.columns:
            df["notional_usd"] = pd.to_numeric(df["notional_usd"], errors="coerce")
            df = df[df["notional_usd"] <= 100].reset_index(drop=True)
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)'''

src = safe_replace(src, OLD_P1, NEW_P1, "load_trades: filter to live bot trades")


# ── [3] P2: Detect stale session -> zero daily counters ──────────────────
print("\n[3] P2: Detect stale session in CB-3")

OLD_P2 = '''        daily_pnl = float(state.get("daily_pnl", 0.0))
        # Parse balance data from BingX API (via store-unrealized)'''

NEW_P2 = '''        # Detect stale session -- if session_start is not today, counters are stale
        session_start_str = state.get("session_start", "")
        session_is_today = False
        if session_start_str:
            try:
                session_dt = datetime.fromisoformat(session_start_str)
                session_is_today = session_dt.date() == datetime.now(timezone.utc).date()
            except (ValueError, TypeError):
                pass
        if session_is_today:
            daily_pnl = float(state.get("daily_pnl", 0.0))
        else:
            daily_pnl = 0.0
        # Parse balance data from BingX API (via store-unrealized)'''

src = safe_replace(src, OLD_P2, NEW_P2, "CB-3: stale session detection for daily_pnl")

OLD_P2B = '''        open_count = len(state.get("open_positions", {}))
        daily_trades = int(state.get("daily_trades", 0))'''

NEW_P2B = '''        open_count = len(state.get("open_positions", {}))
        daily_trades = int(state.get("daily_trades", 0)) if session_is_today else 0'''

src = safe_replace(src, OLD_P2B, NEW_P2B, "CB-3: stale session detection for daily_trades")


# ── [4] P3: CSS -- aggressive date picker dark background ─────────────────
print("\n[4] P3: CSS -- aggressive date picker selectors")

CSS_PATCH = '''
/* === DatePickerRange nuclear dark fix (all nested divs) === */
#hist-date-range .DateRangePicker,
#analytics-date-range .DateRangePicker,
#hist-date-range .DateRangePickerInput,
#analytics-date-range .DateRangePickerInput,
#hist-date-range .DateRangePickerInput__withBorder,
#analytics-date-range .DateRangePickerInput__withBorder,
#hist-date-range .DateInput,
#analytics-date-range .DateInput {
    background-color: #21262d !important;
    background: #21262d !important;
    border-color: #484f58 !important;
}
#hist-date-range .DateRangePickerInput_arrow,
#analytics-date-range .DateRangePickerInput_arrow {
    background-color: #21262d !important;
    background: #21262d !important;
}
#hist-date-range .DateRangePickerInput_clearDates,
#analytics-date-range .DateRangePickerInput_clearDates {
    background-color: #21262d !important;
    background: #21262d !important;
}
'''

if "DatePickerRange nuclear dark fix" not in css:
    css += CSS_PATCH
    report("CSS: aggressive date picker selectors", True)
else:
    report("CSS: aggressive date picker selectors", False, "already applied")


# ── [5] Write files ───────────────────────────────────────────────────────
print("\n[5] Write files")
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

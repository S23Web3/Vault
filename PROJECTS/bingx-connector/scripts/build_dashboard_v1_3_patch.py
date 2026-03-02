"""
BingX Dashboard v1-3 Patch -- fixes B1 + B2 + B4 from audit.

Reads:  bingx-live-dashboard-v1-3.py
Writes: bingx-live-dashboard-v1-3.py (in-place, backup created)

B1: Remove duplicate 'import io' (line 27)
B2: Guard Unreal PnL sum against None values in CB-4
B4: CB-10 State('store-trades') -> Input('store-trades') so coin summary auto-populates

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/build_dashboard_v1_3_patch.py
"""

import os
import py_compile
import shutil
from datetime import datetime

DASH_PATH = os.path.join(os.path.dirname(__file__), "..", "bingx-live-dashboard-v1-3.py")
DASH_PATH = os.path.normpath(DASH_PATH)

errors = []


def report(label, ok, note=""):
    """Print pass/fail status for each patch step."""
    tag = "PASS" if ok else "FAIL"
    suffix = " -- " + note if note else ""
    print("  {}  {}{}".format(tag, label, suffix))
    if not ok:
        errors.append(label)


def safe_replace(src, old, new, label):
    """Replace old with new in src. Report pass/fail."""
    if old in src:
        src = src.replace(old, new, 1)
        report(label, True)
    else:
        report(label, False, "pattern not found (may already be applied)")
    return src


# ── Read source ──────────────────────────────────────────────────────────
print("\n[1] Read source")
with open(DASH_PATH, "r", encoding="utf-8") as f:
    src = f.read()
print("  Read {} chars from {}".format(len(src), os.path.basename(DASH_PATH)))

# ── B1: Remove duplicate import io ───────────────────────────────────────
print("\n[2] B1: Remove duplicate import io")
src = safe_replace(
    src,
    "import io\nimport io\n",
    "import io\n",
    "remove duplicate import io",
)

# ── B2: Guard Unreal PnL sum against None ────────────────────────────────
print("\n[3] B2: Guard Unreal PnL sum against None")
OLD_B2 = '        total_unreal = round(float(pos_df["Unreal PnL"].sum()), 4) if "Unreal PnL" in pos_df.columns else 0.0'
NEW_B2 = '        total_unreal = round(float(pd.to_numeric(pos_df["Unreal PnL"], errors="coerce").sum()), 4) if "Unreal PnL" in pos_df.columns else 0.0'
src = safe_replace(src, OLD_B2, NEW_B2, "guard Unreal PnL sum with pd.to_numeric")

# ── B4: CB-10 State -> Input for store-trades ────────────────────────────
print("\n[4] B4: CB-10 State -> Input for store-trades")

# The callback decorator block
OLD_B4 = """@callback(
    Output('coin-summary-grid',    'rowData'),
    Output('coin-summary-caption', 'children'),
    Input('coin-period-filter',    'value'),
    State('store-trades',          'data'),
    prevent_initial_call=True,  # Do not fire on page load \u2014 stores not yet populated
)"""

NEW_B4 = """@callback(
    Output('coin-summary-grid',    'rowData'),
    Output('coin-summary-caption', 'children'),
    Input('coin-period-filter',    'value'),
    Input('store-trades',          'data'),
    prevent_initial_call=True,
)"""

src = safe_replace(src, OLD_B4, NEW_B4, "CB-10 State -> Input for store-trades")

# ── Write patched file ───────────────────────────────────────────────────
print("\n[5] Write patched file")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DASH_PATH.replace(".py", ".{}.bak.py".format(ts))
shutil.copy2(DASH_PATH, bak)
print("  Backup: {}".format(bak))

with open(DASH_PATH, "w", encoding="utf-8") as f:
    f.write(src)
report("write " + os.path.basename(DASH_PATH), True)

try:
    py_compile.compile(DASH_PATH, doraise=True)
    report("py_compile", True)
except py_compile.PyCompileError as e:
    report("py_compile", False, str(e))

# ── Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if errors:
    print("FAILURES: " + ", ".join(errors))
    print("{} error(s). Review output above.".format(len(errors)))
else:
    print("ALL PATCHES APPLIED SUCCESSFULLY")
    print("Run: python bingx-live-dashboard-v1-3.py")

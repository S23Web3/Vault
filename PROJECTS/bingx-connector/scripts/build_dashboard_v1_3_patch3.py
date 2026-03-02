"""
BingX Dashboard v1-3 Patch 3 -- Real balance from BingX API.

Reads:  bingx-live-dashboard-v1-3.py
Writes: bingx-live-dashboard-v1-3.py (in-place, backup created)

P1: Add fetch_account_balance() function (GET /openApi/swap/v3/user/balance)
P2: CB-4 -- output balance dict to store-unrealized instead of plain float
P3: CB-3 -- use real API balance/equity/unrealized in status bar
P4: CB-9 -- parse new balance dict format for equity curve extension

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/build_dashboard_v1_3_patch3.py
"""

import os
import py_compile
import shutil
from datetime import datetime

BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DASH_PATH = os.path.join(BASE, "bingx-live-dashboard-v1-3.py")

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


# ── [2] P1: Add fetch_account_balance function ───────────────────────────
print("\n[2] P1: Add fetch_account_balance()")

OLD_P1 = '''def reconcile_positions(state: dict) -> dict:
    """Validate state.json positions against BingX API. Removes phantoms, writes cleaned state."""'''

NEW_P1 = '''def fetch_account_balance() -> dict:
    """Fetch real account balance from BingX API (v3). Returns dict with balance, equity, unrealized."""
    default = {"balance": 0.0, "equity": 0.0, "unrealized": 0.0, "available_margin": 0.0, "used_margin": 0.0}
    if not API_KEY or not SECRET_KEY:
        return default
    try:
        data = _bingx_request('GET', '/openApi/swap/v3/user/balance', {})
        if 'error' in data:
            LOG.warning("Balance API error: %s", data['error'])
            return default
        accounts = data if isinstance(data, list) else [data]
        for acc in accounts:
            if acc.get('asset', '') == 'USDT':
                return {
                    "balance": float(acc.get('balance', 0)),
                    "equity": float(acc.get('equity', 0)),
                    "unrealized": float(acc.get('unrealizedProfit', 0)),
                    "available_margin": float(acc.get('availableMargin', 0)),
                    "used_margin": float(acc.get('usedMargin', 0)),
                }
        return default
    except Exception as e:
        LOG.warning("Balance fetch failed: %s", e)
        return default


def reconcile_positions(state: dict) -> dict:
    """Validate state.json positions against BingX API. Removes phantoms, writes cleaned state."""'''

src = safe_replace(src, OLD_P1, NEW_P1, "add fetch_account_balance function")


# ── [3] P2: CB-4 -- output balance dict to store-unrealized ──────────────
print("\n[3] P2: CB-4 -- output balance dict to store-unrealized")

# P2a: empty state return
OLD_P2A = '''        if not state_json:
            return [], json.dumps(0.0)
        state = json.loads(state_json)
        # Reconcile against BingX API -- removes phantom positions
        state = reconcile_positions(state)
        positions = state.get("open_positions", {})
        if not positions:
            return [], json.dumps(0.0)'''

NEW_P2A = '''        if not state_json:
            return [], json.dumps(fetch_account_balance())
        state = json.loads(state_json)
        # Reconcile against BingX API -- removes phantom positions
        state = reconcile_positions(state)
        positions = state.get("open_positions", {})
        if not positions:
            return [], json.dumps(fetch_account_balance())'''

src = safe_replace(src, OLD_P2A, NEW_P2A, "CB-4: empty/no-positions -> balance dict")

# P2b: main return with unrealized
OLD_P2B = '''        total_unreal = round(float(pd.to_numeric(pos_df["Unreal PnL"], errors="coerce").sum()), 4) if "Unreal PnL" in pos_df.columns else 0.0
        return pos_df.to_dict('records'), json.dumps(total_unreal)'''

NEW_P2B = '''        # Fetch real balance from BingX API
        bal = fetch_account_balance()
        return pos_df.to_dict('records'), json.dumps(bal)'''

src = safe_replace(src, OLD_P2B, NEW_P2B, "CB-4: main return -> balance dict")

# P2c: error return
OLD_P2C = '''        LOG.error("Error loading positions: %s", e, exc_info=True)
        return [], json.dumps(0.0)'''

NEW_P2C = '''        LOG.error("Error loading positions: %s", e, exc_info=True)
        return [], json.dumps({"balance": 0.0, "equity": 0.0, "unrealized": 0.0})'''

src = safe_replace(src, OLD_P2C, NEW_P2C, "CB-4: error return -> balance dict")


# ── [4] P3: CB-3 -- use real API balance in status bar ────────────────────
print("\n[4] P3: CB-3 -- use real API balance in status bar")

OLD_P3A = '''        daily_pnl = float(state.get("daily_pnl", 0.0))
        unrealized_pnl = float(json.loads(unrealized_json)) if unrealized_json else 0.0
        unreal_color = COLORS['green'] if unrealized_pnl >= 0 else COLORS['red']'''

NEW_P3A = '''        daily_pnl = float(state.get("daily_pnl", 0.0))
        # Parse balance data from BingX API (via store-unrealized)
        bal_data = json.loads(unrealized_json) if unrealized_json else {}
        if isinstance(bal_data, dict):
            api_balance = float(bal_data.get("balance", 0.0))
            api_equity = float(bal_data.get("equity", 0.0))
            unrealized_pnl = float(bal_data.get("unrealized", 0.0))
        else:
            # Legacy format (plain float) -- backwards compat
            api_balance = 0.0
            api_equity = 0.0
            unrealized_pnl = float(bal_data) if bal_data else 0.0
        unreal_color = COLORS['green'] if unrealized_pnl >= 0 else COLORS['red']'''

src = safe_replace(src, OLD_P3A, NEW_P3A, "CB-3: parse balance dict")

OLD_P3B = '''        equity = daily_pnl + unrealized_pnl
        equity_color = COLORS['green'] if equity >= 0 else COLORS['red']

        return html.Div([
            build_metric_card("Status", status_label, status_color),
            build_metric_card("Equity", f"${equity:+.2f}", equity_color),
            build_metric_card("Realized", f"${daily_pnl:+.2f}", pnl_color),
            build_metric_card("Unrealized", f"${unrealized_pnl:+.2f}", unreal_color),'''

NEW_P3B = '''        # Use real API balance if available, fall back to state.json
        if api_balance > 0:
            balance_color = COLORS['green'] if api_balance >= 100 else COLORS['red']
            equity_color = COLORS['green'] if api_equity >= 100 else COLORS['red']
        else:
            api_balance = daily_pnl
            api_equity = daily_pnl + unrealized_pnl
            balance_color = COLORS['green'] if api_balance >= 0 else COLORS['red']
            equity_color = COLORS['green'] if api_equity >= 0 else COLORS['red']

        return html.Div([
            build_metric_card("Status", status_label, status_color),
            build_metric_card("Balance", "${:.2f}".format(api_balance), balance_color),
            build_metric_card("Equity", "${:.2f}".format(api_equity), equity_color),
            build_metric_card("Unrealized", "${:+.2f}".format(unrealized_pnl), unreal_color),'''

src = safe_replace(src, OLD_P3B, NEW_P3B, "CB-3: show API balance/equity")


# ── [5] P4: CB-9 -- parse balance dict for equity curve extension ─────────
print("\n[5] P4: CB-9 -- parse balance dict for equity curve extension")

OLD_P4 = '''                unreal_val = float(json.loads(unrealized_json))'''

NEW_P4 = '''                bal_data = json.loads(unrealized_json)
                unreal_val = float(bal_data.get("unrealized", 0.0)) if isinstance(bal_data, dict) else float(bal_data)'''

src = safe_replace(src, OLD_P4, NEW_P4, "CB-9: parse balance dict for unrealized")


# ── [6] Write file ────────────────────────────────────────────────────────
print("\n[6] Write file")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DASH_PATH.replace(".py", ".{}.bak.py".format(ts))
shutil.copy2(DASH_PATH, bak)
print("  Backup: {}".format(bak))

with open(DASH_PATH, "w", encoding="utf-8") as f:
    f.write(src)
report("write " + os.path.basename(DASH_PATH), True)

try:
    py_compile.compile(DASH_PATH, doraise=True)
    report("py_compile dashboard", True)
except py_compile.PyCompileError as e:
    report("py_compile dashboard", False, str(e))


# ── Summary ───────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if ERRORS:
    print("FAILURES: " + ", ".join(ERRORS))
    print("{} error(s). Review output above.".format(len(ERRORS)))
else:
    print("ALL PATCHES APPLIED SUCCESSFULLY")
    print("Run: python bingx-live-dashboard-v1-3.py")

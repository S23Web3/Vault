"""
Build script: BingX Dashboard v1.5 -- Industry-Standard Max Drawdown %
Date: 2026-03-05

Fix: Max DD % was calculated as PnL drawdown / PnL peak, which gives -100%
whenever cumulative PnL goes from positive to zero. Industry standard is:
    DD% = (equity_trough - equity_peak) / equity_peak * 100
where equity = starting_balance + cumulative_PnL.

Changes:
  P1: compute_metrics() accepts account_balance param, calculates DD% on equity curve
  P2: update_analytics() passes API balance to compute_metrics()

Base: C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\bingx-live-dashboard-v1-5.py
"""

import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector")
TARGET = BASE / "bingx-live-dashboard-v1-5.py"

ERRORS = []
PATCHES_APPLIED = []


def safe_replace(content, old, new, label):
    """Replace exactly one occurrence of old with new. Appends to ERRORS on failure."""
    if old not in content:
        ERRORS.append(label + " FAILED: old string not found")
        return content
    count = content.count(old)
    if count != 1:
        ERRORS.append(label + " FAILED: expected 1 occurrence, found " + str(count))
        return content
    content = content.replace(old, new)
    PATCHES_APPLIED.append(label)
    print("  " + label + " applied")
    return content


def patch_file():
    """Apply drawdown fix patches."""
    content = TARGET.read_text(encoding="utf-8")

    # ---------------------------------------------------------------
    # P1: Fix compute_metrics() drawdown to use equity curve
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "def compute_metrics(df: pd.DataFrame) -> dict:\n"
        "    \"\"\"Compute professional trading metrics from closed trades DataFrame.\"\"\"",
        "def compute_metrics(df: pd.DataFrame, account_balance: float = 0.0) -> dict:\n"
        "    \"\"\"Compute professional trading metrics from closed trades DataFrame.\"\"\"",
        "P1a-add-balance-param",
    )

    # P1b: Replace the drawdown calculation block
    content = safe_replace(
        content,
        "    # Max drawdown $ and % (P7 fix: cap at -100%, skip when peak < $1)\n"
        "    cum = df.sort_values(\"timestamp\").pnl_net.cumsum()\n"
        "    peak = cum.cummax()\n"
        "    dd = cum - peak\n"
        "    max_dd = round(float(dd.min()), 4) if len(cum) > 0 else 0.0\n"
        "    max_dd_pct = 0.0\n"
        "    if len(cum) > 0 and float(dd.min()) < 0:\n"
        "        dd_idx = dd.idxmin()\n"
        "        peak_at_dd = float(peak.loc[dd_idx])\n"
        "        if peak_at_dd >= 1.0:\n"
        "            max_dd_pct = round(float(dd.loc[dd_idx] / peak_at_dd * 100), 2)\n"
        "            max_dd_pct = max(max_dd_pct, -100.0)  # Cap at -100%",
        "    # Max drawdown $ and % (industry standard: equity-based, not PnL-based)\n"
        "    cum = df.sort_values(\"timestamp\").pnl_net.cumsum()\n"
        "    dd_pnl = cum - cum.cummax()\n"
        "    max_dd = round(float(dd_pnl.min()), 4) if len(cum) > 0 else 0.0\n"
        "    max_dd_pct = 0.0\n"
        "    if len(cum) > 0 and account_balance > 0:\n"
        "        starting_bal = account_balance - float(cum.iloc[-1])\n"
        "        equity = starting_bal + cum\n"
        "        peak_equity = equity.cummax()\n"
        "        dd_eq = equity - peak_equity\n"
        "        dd_pct_series = (dd_eq / peak_equity * 100).replace([float('inf'), float('-inf')], 0)\n"
        "        if len(dd_pct_series) > 0:\n"
        "            max_dd_pct = round(float(dd_pct_series.min()), 2)",
        "P1b-equity-based-drawdown",
    )

    # ---------------------------------------------------------------
    # P2: Pass API balance to compute_metrics() in analytics callback
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "        metrics = compute_metrics(df)",
        "        # Get account balance for equity-based drawdown calculation\n"
        "        _api_bal = 0.0\n"
        "        if unrealized_json:\n"
        "            try:\n"
        "                _bal_data = json.loads(unrealized_json) if isinstance(unrealized_json, str) else unrealized_json\n"
        "                if isinstance(_bal_data, dict):\n"
        "                    _api_bal = float(_bal_data.get('balance', 0.0))\n"
        "            except Exception:\n"
        "                pass\n"
        "        metrics = compute_metrics(df, account_balance=_api_bal)",
        "P2-pass-balance-to-metrics",
    )

    TARGET.write_text(content, encoding="utf-8")
    print("\nFile written: " + str(TARGET))


def validate():
    """Run py_compile on the patched file."""
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("py_compile PASS: " + str(TARGET))
    except py_compile.PyCompileError as e:
        ERRORS.append("py_compile FAILED: " + str(e))


def main():
    """Run all patches and validation."""
    print("=" * 70)
    print("BingX Dashboard v1.5 -- Industry-Standard Max Drawdown %")
    print("=" * 70)
    print()

    if not TARGET.exists():
        print("ERROR: Target file not found: " + str(TARGET))
        sys.exit(1)

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(TARGET.stem + ".dd." + ts + ".bak.py")
    shutil.copy2(TARGET, backup)
    print("Backup: " + str(backup))
    print()

    print("Applying patches...")
    patch_file()

    if ERRORS:
        print()
        print("ERRORS:")
        for err in ERRORS:
            print("  - " + err)
        sys.exit(1)

    print()
    validate()

    if ERRORS:
        print()
        print("ERRORS:")
        for err in ERRORS:
            print("  - " + err)
        sys.exit(1)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("  Patches applied: " + str(len(PATCHES_APPLIED)))
    for p in PATCHES_APPLIED:
        print("    + " + p)
    print("  Backup: " + str(backup))
    print()
    print("  Before: DD% = pnl_drawdown / pnl_peak (gives -100% when PnL crosses zero)")
    print("  After:  DD% = equity_drawdown / peak_equity (industry standard)")
    print("          equity = starting_balance + cumulative_PnL")
    print("          starting_balance = current_API_balance - net_PnL")
    print()
    print("  Example: balance=$73.49, net_pnl=-$2.00, starting=$75.49")
    print("           peak_equity=$75.49, max_dd=$3.08 -> DD% = -4.08%")
    print()
    print("Run command:")
    print('  python "' + str(TARGET) + '"')


if __name__ == "__main__":
    main()

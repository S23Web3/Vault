"""
Build script: Trade Validator
Reads trades.csv, validates every trade's SL distance, BE%, TTP consistency.
Output: scripts/run_trade_validator.py
"""
import os
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "scripts" / "run_trade_validator.py"

CODE = r'''"""
Trade Validator: validates every trade in trades.csv against expected SL/BE/TTP mechanics.
Run: python scripts/run_trade_validator.py [--csv PATH] [--report]
"""
import csv
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "trades.csv"
LOGS_DIR = ROOT / "logs"

# Bot config constants (must match config.yaml)
SL_ATR_MULT = 2.0
COMMISSION_RATE_RT = 0.0016  # 0.08% taker x 2 sides
BE_BUFFER = 0.001  # hardcoded in position_monitor.py line 420
MIN_ATR_RATIO = 0.003  # risk_gate config


def load_trades(csv_path):
    """Load trades from CSV, handling both 12-col and 18-col formats."""
    trades = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        n_cols = len(header)
        for i, row in enumerate(reader, start=2):
            # Pad short rows
            while len(row) < n_cols:
                row.append("")
            # Truncate long rows
            row = row[:n_cols]
            trade = {}
            for j, col_name in enumerate(header):
                trade[col_name] = row[j]
            trade["_row"] = i
            trades.append(trade)
    return trades


def safe_float(val, default=0.0):
    """Convert to float safely."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def classify_trade(t):
    """Classify trade into a validation category."""
    reason = t.get("exit_reason", "")
    be_raised = t.get("be_raised", "").strip().lower() in ("true", "1")
    notional = safe_float(t.get("notional_usd", 0))
    phase = "P1_500" if notional > 100 else "P2_50"

    if "EXIT_UNKNOWN" in reason:
        return "EXIT_UNKNOWN", phase, be_raised
    if reason == "TTP_EXIT":
        return "TTP_EXIT", phase, be_raised
    if "SL_HIT" in reason and be_raised:
        return "BE_SL_HIT", phase, be_raised
    if "SL_HIT" in reason and not be_raised:
        return "FULL_SL_HIT", phase, be_raised
    if "TP_HIT" in reason:
        return "TP_HIT", phase, be_raised
    return "OTHER", phase, be_raised


def validate_full_sl(t):
    """Validate non-BE SL_HIT: check SL distance = 2 * ATR."""
    entry = safe_float(t.get("entry_price"))
    exit_p = safe_float(t.get("exit_price"))
    direction = t.get("direction", "")
    pnl = safe_float(t.get("pnl_net"))
    symbol = t.get("symbol", "")

    if entry <= 0 or exit_p <= 0:
        return {"flag": "NO_PRICE", "sl_pct": 0, "atr_ratio": 0, "detail": "missing price data"}

    if direction == "LONG":
        sl_dist = entry - exit_p
    else:
        sl_dist = exit_p - entry

    sl_pct = abs(sl_dist) / entry * 100
    implied_atr = abs(sl_dist) / SL_ATR_MULT
    atr_ratio = implied_atr / entry

    flag = "OK"
    detail = ""

    if sl_pct > 10:
        flag = "EXTREME_SL"
        detail = "SL distance > 10% -- possible liquidation or data error"
    elif sl_pct > 5:
        flag = "HIGH_SL"
        detail = "SL distance > 5% -- ultra-volatile coin"
    elif sl_pct < 0.1:
        flag = "TINY_SL"
        detail = "SL distance < 0.1% -- possibly BE that was not flagged"

    if atr_ratio < MIN_ATR_RATIO:
        flag = "BELOW_MIN_ATR"
        detail = "atr_ratio %.6f < min %.4f -- should have been blocked by risk gate" % (atr_ratio, MIN_ATR_RATIO)

    # Check if SL was in wrong direction (positive gross PnL on SL_HIT without BE)
    if direction == "LONG" and exit_p > entry:
        flag = "SL_WRONG_DIRECTION"
        detail = "LONG SL_HIT but exit > entry -- SL was above entry (possibly moved to BE)"
    elif direction == "SHORT" and exit_p < entry:
        flag = "SL_WRONG_DIRECTION"
        detail = "SHORT SL_HIT but exit < entry -- SL was below entry (possibly moved to BE)"

    return {
        "flag": flag,
        "sl_pct": round(sl_pct, 4),
        "atr_ratio": round(atr_ratio, 6),
        "implied_atr": round(implied_atr, 8),
        "sl_dist": round(abs(sl_dist), 8),
        "pnl": pnl,
        "detail": detail,
    }


def validate_be_sl(t):
    """Validate BE-raised SL_HIT: check exit is near breakeven + fees."""
    entry = safe_float(t.get("entry_price"))
    exit_p = safe_float(t.get("exit_price"))
    direction = t.get("direction", "")
    pnl = safe_float(t.get("pnl_net"))
    notional = safe_float(t.get("notional_usd"))

    if entry <= 0 or exit_p <= 0:
        return {"flag": "NO_PRICE", "be_pct": 0, "detail": "missing price data"}

    if direction == "LONG":
        be_pct = (exit_p - entry) / entry * 100
        expected_be_pct = (COMMISSION_RATE_RT + BE_BUFFER) * 100  # ~0.26%
    else:
        be_pct = (entry - exit_p) / entry * 100
        expected_be_pct = (COMMISSION_RATE_RT + BE_BUFFER) * 100

    flag = "OK"
    detail = ""

    if pnl < 0:
        flag = "NEGATIVE_BE"
        detail = "PnL $%.4f negative despite BE raise -- slippage exceeded %.1f%% buffer" % (pnl, BE_BUFFER * 100)
    elif abs(be_pct - expected_be_pct) > 0.5:
        flag = "BE_DRIFT"
        detail = "BE exit %.4f%% vs expected %.4f%% -- possible commission rate mismatch" % (be_pct, expected_be_pct)

    commission_at_close = notional * COMMISSION_RATE_RT if notional > 0 else 0
    gross_pnl = pnl + commission_at_close

    return {
        "flag": flag,
        "be_pct": round(be_pct, 4),
        "expected_be_pct": round(expected_be_pct, 4),
        "pnl": pnl,
        "gross_pnl": round(gross_pnl, 4),
        "commission": round(commission_at_close, 4),
        "detail": detail,
    }


def validate_ttp(t):
    """Validate TTP_EXIT: check extreme > trail, profit locked."""
    extreme_pct = safe_float(t.get("ttp_extreme_pct"))
    trail_pct = safe_float(t.get("ttp_trail_pct"))
    pnl = safe_float(t.get("pnl_net"))
    ttp_activated = t.get("ttp_activated", "").strip().lower() in ("true", "1")

    flag = "OK"
    detail = ""

    if not ttp_activated:
        flag = "TTP_NOT_ACTIVATED"
        detail = "TTP exit but ttp_activated=False -- data inconsistency"
    elif extreme_pct <= 0:
        flag = "NO_EXTREME"
        detail = "ttp_extreme_pct missing or zero"
    elif trail_pct <= 0:
        flag = "NO_TRAIL"
        detail = "ttp_trail_pct missing or zero"
    elif extreme_pct < trail_pct:
        flag = "EXTREME_BELOW_TRAIL"
        detail = "extreme %.4f%% < trail %.4f%% -- impossible if TTP working correctly" % (extreme_pct, trail_pct)

    if pnl < 0 and flag == "OK":
        flag = "TTP_NEGATIVE"
        detail = "TTP exit with negative PnL $%.4f -- trail level estimate may be wrong (C2 bug)" % pnl

    return {
        "flag": flag,
        "extreme_pct": extreme_pct,
        "trail_pct": trail_pct,
        "pnl": pnl,
        "detail": detail,
    }


def run_validation(csv_path, report_path=None):
    """Run full validation on trades.csv."""
    trades = load_trades(csv_path)
    print("Loaded %d trades from %s" % (len(trades), csv_path))
    print("=" * 100)

    # Counters
    counts = {
        "FULL_SL_HIT": 0, "BE_SL_HIT": 0, "TTP_EXIT": 0,
        "EXIT_UNKNOWN": 0, "TP_HIT": 0, "OTHER": 0,
    }
    phase_counts = {"P1_500": 0, "P2_50": 0}
    flags = {}
    results = []

    for t in trades:
        cat, phase, be_raised = classify_trade(t)
        counts[cat] = counts.get(cat, 0) + 1
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

        if cat == "FULL_SL_HIT":
            v = validate_full_sl(t)
        elif cat == "BE_SL_HIT":
            v = validate_be_sl(t)
        elif cat == "TTP_EXIT":
            v = validate_ttp(t)
        elif cat == "EXIT_UNKNOWN":
            v = {"flag": "UNRESOLVED", "detail": "pre-fix data, cannot validate"}
        else:
            v = {"flag": "SKIP", "detail": "category: " + cat}

        v["category"] = cat
        v["phase"] = phase
        v["symbol"] = t.get("symbol", "?")
        v["direction"] = t.get("direction", "?")
        v["row"] = t.get("_row", "?")
        v["timestamp"] = t.get("timestamp", "")[:19]
        results.append(v)

        f = v["flag"]
        flags[f] = flags.get(f, 0) + 1

    # --- Print Summary ---
    print("\n--- TRADE COUNTS ---")
    for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
        print("  %-20s %d" % (cat, n))
    print("\n--- PHASE COUNTS ---")
    for phase, n in sorted(phase_counts.items()):
        print("  %-20s %d" % (phase, n))
    print("\n--- FLAG SUMMARY ---")
    for f, n in sorted(flags.items(), key=lambda x: -x[1]):
        print("  %-25s %d" % (f, n))

    # --- Print FULL_SL_HIT detail table ---
    sl_results = [r for r in results if r["category"] == "FULL_SL_HIT"]
    if sl_results:
        print("\n--- FULL SL_HIT TRADES (original SL, not BE-raised) ---")
        print("%-6s %-16s %-6s %-8s %-8s %-10s %-8s %-20s" % (
            "Row", "Symbol", "Dir", "SL%", "ATR_R", "PnL", "Flag", "Detail"))
        print("-" * 100)
        for r in sorted(sl_results, key=lambda x: -abs(x.get("sl_pct", 0))):
            print("%-6s %-16s %-6s %-8s %-8s %-10s %-8s %-20s" % (
                r["row"],
                r["symbol"],
                r["direction"],
                "%.2f%%" % r.get("sl_pct", 0),
                "%.4f" % r.get("atr_ratio", 0),
                "$%.2f" % r.get("pnl", 0),
                r["flag"],
                r.get("detail", "")[:40],
            ))

    # --- Print BE_SL_HIT detail table ---
    be_results = [r for r in results if r["category"] == "BE_SL_HIT"]
    if be_results:
        print("\n--- BE-RAISED SL_HIT TRADES ---")
        print("%-6s %-16s %-6s %-8s %-8s %-10s %-8s %-20s" % (
            "Row", "Symbol", "Dir", "BE%", "Exp%", "PnL", "Flag", "Detail"))
        print("-" * 100)
        for r in sorted(be_results, key=lambda x: x.get("pnl", 0)):
            print("%-6s %-16s %-6s %-8s %-8s %-10s %-8s %-20s" % (
                r["row"],
                r["symbol"],
                r["direction"],
                "%.2f%%" % r.get("be_pct", 0),
                "%.2f%%" % r.get("expected_be_pct", 0),
                "$%.4f" % r.get("pnl", 0),
                r["flag"],
                r.get("detail", "")[:40],
            ))

    # --- Print TTP detail table ---
    ttp_results = [r for r in results if r["category"] == "TTP_EXIT"]
    if ttp_results:
        print("\n--- TTP_EXIT TRADES ---")
        print("%-6s %-16s %-6s %-8s %-8s %-10s %-8s %-20s" % (
            "Row", "Symbol", "Dir", "Ext%", "Trail%", "PnL", "Flag", "Detail"))
        print("-" * 100)
        for r in ttp_results:
            print("%-6s %-16s %-6s %-8s %-8s %-10s %-8s %-20s" % (
                r["row"],
                r["symbol"],
                r["direction"],
                "%.2f%%" % r.get("extreme_pct", 0),
                "%.2f%%" % r.get("trail_pct", 0),
                "$%.4f" % r.get("pnl", 0),
                r["flag"],
                r.get("detail", "")[:40],
            ))

    # --- Print flagged issues ---
    issues = [r for r in results if r["flag"] not in ("OK", "SKIP", "UNRESOLVED")]
    if issues:
        print("\n--- FLAGGED ISSUES (%d) ---" % len(issues))
        for r in issues:
            print("  Row %-4s %-16s %-6s %-20s %s" % (
                r["row"], r["symbol"], r["direction"],
                r["flag"], r.get("detail", "")[:60]))

    # --- Write markdown report ---
    if report_path:
        LOGS_DIR.mkdir(exist_ok=True)
        lines = []
        lines.append("# Trade Validation Report")
        lines.append("**Date:** " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
        lines.append("**CSV:** " + str(csv_path))
        lines.append("**Trades:** " + str(len(trades)))
        lines.append("")
        lines.append("## Counts")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
            lines.append("| %s | %d |" % (cat, n))
        lines.append("")
        lines.append("## Flags")
        lines.append("| Flag | Count |")
        lines.append("|------|-------|")
        for f, n in sorted(flags.items(), key=lambda x: -x[1]):
            lines.append("| %s | %d |" % (f, n))
        lines.append("")
        if issues:
            lines.append("## Flagged Issues (%d)" % len(issues))
            lines.append("| Row | Symbol | Dir | Flag | Detail |")
            lines.append("|-----|--------|-----|------|--------|")
            for r in issues:
                lines.append("| %s | %s | %s | %s | %s |" % (
                    r["row"], r["symbol"], r["direction"],
                    r["flag"], r.get("detail", "")[:60]))
        lines.append("")
        Path(report_path).write_text("\n".join(lines), encoding="utf-8")
        print("\nReport saved: %s" % report_path)

    print("\nDone. %d trades validated, %d flagged." % (len(trades), len(issues)))
    return results


if __name__ == "__main__":
    csv_path = DEFAULT_CSV
    report = False
    for arg in sys.argv[1:]:
        if arg == "--report":
            report = True
        elif arg.startswith("--csv"):
            if "=" in arg:
                csv_path = Path(arg.split("=", 1)[1])
            elif sys.argv.index(arg) + 1 < len(sys.argv):
                csv_path = Path(sys.argv[sys.argv.index(arg) + 1])

    if not Path(csv_path).exists():
        print("ERROR: CSV not found: %s" % csv_path)
        sys.exit(1)

    report_path = None
    if report:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        report_path = LOGS_DIR / ("trade_validation_" + today + ".md")

    run_validation(csv_path, report_path)
'''

print("Writing: %s" % OUT)
OUT.write_text(CODE.strip() + "\n", encoding="utf-8")

print("py_compile: %s" % OUT)
py_compile.compile(str(OUT), doraise=True)
print("PASS: %s" % OUT.name)

print("\nRun command:")
print('  cd "%s" && python scripts/run_trade_validator.py --report' % ROOT)

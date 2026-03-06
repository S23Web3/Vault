"""
Master audit script for BingX Connector bot.
Runs 4 audits: trades analysis, docstring coverage, commission flow, strategy comparison.
Run: python scripts/audit_bot.py
"""
import os
import sys
import ast
import csv
import re
from pathlib import Path
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BOT_ROOT = Path(__file__).resolve().parent.parent
TRADES_CSV = BOT_ROOT / "trades.csv"
BACKTESTER_ROOT = BOT_ROOT.parent / "four-pillars-backtester"
REPORT_DIR = BOT_ROOT / "logs"
REPORT_DIR.mkdir(exist_ok=True)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
REPORT_PATH = REPORT_DIR / (TODAY + "-audit-report.txt")

# Files to scan for docstrings (all .py in bot project)
PY_DIRS = [BOT_ROOT, BOT_ROOT / "plugins", BOT_ROOT / "scripts", BOT_ROOT / "tests"]

ERRORS = []


def section(title):
    """Print a section header."""
    line = "=" * 70
    print("\n" + line)
    print("  " + title)
    print(line)


# =========================================================================
# AUDIT 1: TRADES ANALYSIS
# =========================================================================
def audit_trades():
    """Analyze trades.csv: exit reasons, P&L breakdown, profitable count."""
    section("AUDIT 1: TRADES ANALYSIS")

    if not TRADES_CSV.exists():
        msg = "trades.csv not found at " + str(TRADES_CSV)
        print("  SKIP: " + msg)
        ERRORS.append(msg)
        return

    trades = []
    with open(TRADES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(row)

    total = len(trades)
    if total == 0:
        print("  No trades in CSV.")
        return

    print("  Total trades: " + str(total))

    # --- Exit reason breakdown ---
    reasons = {}
    for t in trades:
        r = t.get("exit_reason", "UNKNOWN")
        reasons[r] = reasons.get(r, 0) + 1

    print("\n  EXIT REASON BREAKDOWN:")
    for reason in sorted(reasons.keys()):
        count = reasons[reason]
        pct = count / total * 100
        print("    " + reason.ljust(20) + str(count).rjust(5) + "  (" + str(round(pct, 1)) + "%)")

    # --- P&L analysis ---
    pnl_values = []
    for t in trades:
        try:
            pnl_values.append(float(t.get("pnl_net", 0)))
        except (ValueError, TypeError):
            pnl_values.append(0.0)

    winners = [p for p in pnl_values if p > 0]
    losers = [p for p in pnl_values if p < 0]
    flat = [p for p in pnl_values if p == 0]
    total_pnl = sum(pnl_values)

    print("\n  P&L SUMMARY:")
    print("    Total P&L:       $" + str(round(total_pnl, 2)))
    print("    Winners:         " + str(len(winners)) + " / " + str(total))
    print("    Losers:          " + str(len(losers)) + " / " + str(total))
    print("    Flat:            " + str(len(flat)) + " / " + str(total))
    if winners:
        print("    Avg winner:      $" + str(round(sum(winners) / len(winners), 2)))
        print("    Best trade:      $" + str(round(max(winners), 2)))
    if losers:
        print("    Avg loser:       $" + str(round(sum(losers) / len(losers), 2)))
        print("    Worst trade:     $" + str(round(min(losers), 2)))

    # --- EXIT_UNKNOWN root cause ---
    unknown_count = reasons.get("EXIT_UNKNOWN", 0)
    sl_assumed_count = reasons.get("SL_HIT_ASSUMED", 0)
    tp_hit_count = reasons.get("TP_HIT", 0)
    sl_hit_count = reasons.get("SL_HIT", 0)

    print("\n  EXIT_UNKNOWN DIAGNOSIS:")
    if unknown_count > 0 or sl_assumed_count > 0:
        bad_exits = unknown_count + sl_assumed_count
        print("    " + str(bad_exits) + " / " + str(total) + " exits used SL price estimate")
        print("    These trades assumed exit = SL price (always the losing side)")
        print("    -> This is WHY zero trades appear profitable")
        print("    -> Actual P&L is UNKNOWN for these trades")

        # Recalculate: what if 50% were actually TP hits?
        # TP = entry + 4*ATR (LONG) or entry - 4*ATR (SHORT)
        # SL = entry - 2*ATR (LONG) or entry + 2*ATR (SHORT)
        # If half were TP: avg TP pnl ~ +4 ATR, avg SL pnl ~ -2 ATR
        tp_sim_trades = []
        sl_sim_trades = []
        for t in trades:
            reason = t.get("exit_reason", "")
            if reason not in ("EXIT_UNKNOWN", "SL_HIT_ASSUMED"):
                continue
            try:
                entry = float(t.get("entry_price", 0))
                sl = float(t.get("exit_price", 0))
                qty = float(t.get("quantity", 0))
                notional = float(t.get("notional_usd", 0))
                direction = t.get("direction", "LONG")
            except (ValueError, TypeError):
                continue
            if entry <= 0 or sl <= 0 or qty <= 0:
                continue
            # Estimate ATR from SL distance
            if direction == "LONG":
                atr_est = (entry - sl) / 2.0
                tp_est = entry + 4.0 * atr_est
                tp_pnl_gross = (tp_est - entry) * qty
            else:
                atr_est = (sl - entry) / 2.0
                tp_est = entry - 4.0 * atr_est
                tp_pnl_gross = (entry - tp_est) * qty
            commission = notional * 0.0012
            tp_pnl_net = tp_pnl_gross - commission
            sl_pnl_gross = -2.0 * atr_est * qty
            sl_pnl_net = sl_pnl_gross - commission
            tp_sim_trades.append(tp_pnl_net)
            sl_sim_trades.append(sl_pnl_net)

        if tp_sim_trades:
            n = len(tp_sim_trades)
            # Scenario: all SL
            all_sl_pnl = sum(sl_sim_trades)
            # Scenario: backtester-like win rate (~45%)
            # Sort by potential TP pnl descending, assume top 45% were TP
            win_count = int(n * 0.45)
            combined = sorted(zip(tp_sim_trades, sl_sim_trades), key=lambda x: x[0], reverse=True)
            mixed_pnl = sum(tp for tp, _ in combined[:win_count]) + sum(sl for _, sl in combined[win_count:])

            print("\n  WHAT-IF SCENARIOS (for " + str(n) + " unknown-exit trades):")
            print("    If ALL were SL hits:     $" + str(round(all_sl_pnl, 2)))
            print("    If 45% were TP hits:     $" + str(round(mixed_pnl, 2)))
            print("    Recorded (SL assumed):   $" + str(round(total_pnl, 2)))
    else:
        print("    No EXIT_UNKNOWN trades. Exit detection working correctly.")

    if tp_hit_count == 0 and sl_hit_count == 0:
        print("\n  WARNING: Zero TP_HIT and zero SL_HIT detected.")
        print("    The _fetch_filled_exit() fix was applied AFTER these trades.")
        print("    Next 24h run should show proper TP_HIT / SL_HIT exits.")

    # --- Direction breakdown ---
    long_count = sum(1 for t in trades if t.get("direction") == "LONG")
    short_count = sum(1 for t in trades if t.get("direction") == "SHORT")
    print("\n  DIRECTION:")
    print("    LONG:  " + str(long_count))
    print("    SHORT: " + str(short_count))

    # --- Grade breakdown ---
    grades = {}
    for t in trades:
        g = t.get("grade", "?")
        grades[g] = grades.get(g, 0) + 1
    print("\n  GRADE BREAKDOWN:")
    for g in sorted(grades.keys()):
        print("    " + g + ": " + str(grades[g]))

    # --- Notional / commission ---
    total_notional = 0.0
    for t in trades:
        try:
            total_notional += float(t.get("notional_usd", 0))
        except (ValueError, TypeError):
            pass
    trading_volume = total_notional * 2  # open + close = 2 legs
    commission_correct = total_notional * 0.0012
    print("\n  VOLUME & COMMISSION:")
    print("    Notional (one-side):   $" + str(round(total_notional, 2)))
    print("    Trading volume (RT):   $" + str(round(trading_volume, 2)))
    print("    Commission (0.12% RT): $" + str(round(commission_correct, 2)))
    print("    Breakeven move needed: 0.12%")


# =========================================================================
# AUDIT 2: DOCSTRING COVERAGE
# =========================================================================
def audit_docstrings():
    """Scan all .py files and report functions/methods missing docstrings."""
    section("AUDIT 2: DOCSTRING COVERAGE")

    missing = []
    checked = 0
    total_funcs = 0

    py_files = []
    for d in PY_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name.startswith("__"):
                continue
            py_files.append(f)

    for filepath in py_files:
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(filepath))
        except (SyntaxError, UnicodeDecodeError) as e:
            msg = "Parse error: " + str(filepath) + " — " + str(e)
            print("  " + msg)
            ERRORS.append(msg)
            continue

        checked += 1
        rel = filepath.relative_to(BOT_ROOT)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                docstring = ast.get_docstring(node)
                if not docstring:
                    missing.append(str(rel) + ":" + str(node.lineno) + " — " + node.name + "()")
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if not docstring:
                    missing.append(str(rel) + ":" + str(node.lineno) + " — class " + node.name)

    print("  Files scanned: " + str(checked))
    print("  Functions/methods found: " + str(total_funcs))
    print("  Missing docstrings: " + str(len(missing)))

    if missing:
        print("\n  MISSING:")
        for m in missing:
            print("    " + m)
        ERRORS.append(str(len(missing)) + " functions/classes missing docstrings")
    else:
        print("  All functions and classes have docstrings.")


# =========================================================================
# AUDIT 3: COMMISSION FLOW
# =========================================================================
def audit_commission():
    """Trace commission calculations across all bot files. Flag double-counting."""
    section("AUDIT 3: COMMISSION FLOW")

    commission_refs = []
    py_files = []
    for d in PY_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.py")):
            py_files.append(f)

    patterns = [
        re.compile(r"commission", re.IGNORECASE),
        re.compile(r"0\.0012"),
        re.compile(r"0\.0008"),
        re.compile(r"0\.001\b"),
        re.compile(r"0\.0006"),
        re.compile(r"0\.0002"),
        re.compile(r"taker.*fee|fee.*taker", re.IGNORECASE),
        re.compile(r"maker.*fee|fee.*maker", re.IGNORECASE),
    ]

    for filepath in py_files:
        try:
            lines = filepath.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = filepath.relative_to(BOT_ROOT)
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if pat.search(line):
                    commission_refs.append(str(rel) + ":" + str(i) + " — " + line.strip())
                    break

    print("  Commission-related lines found: " + str(len(commission_refs)))
    if commission_refs:
        print()
        for ref in commission_refs:
            print("    " + ref)

    # Double-counting check
    print("\n  DOUBLE-COUNTING CHECK:")
    # Only check runtime files — exclude build scripts, audit scripts, tests
    skip_prefixes = ("build_", "scripts", "tests")
    deduction_files = []
    for filepath in py_files:
        rel = filepath.relative_to(BOT_ROOT)
        rel_str = str(rel)
        if any(rel_str.startswith(p) or rel_str.startswith(p + "\\") for p in skip_prefixes):
            continue
        try:
            source = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        # Look for actual P&L deduction patterns
        if re.search(r"pnl.*-.*commission|pnl_net.*=.*pnl_gross.*-", source):
            deduction_files.append(rel_str)

    if len(deduction_files) == 0:
        print("    WARNING: No commission deduction found in any file!")
        ERRORS.append("No commission deduction found")
    elif len(deduction_files) == 1:
        print("    PASS: Commission deducted in exactly 1 file: " + deduction_files[0])
    else:
        print("    RISK: Commission deduction found in " + str(len(deduction_files)) + " files:")
        for f in deduction_files:
            print("      " + f)
        ERRORS.append("Commission deducted in multiple files — possible double-counting")

    # Rate check
    print("\n  RATE CHECK:")
    monitor_path = BOT_ROOT / "position_monitor.py"
    if monitor_path.exists():
        source = monitor_path.read_text(encoding="utf-8")
        if "0.0012" in source:
            print("    position_monitor.py: 0.0012 (0.06% x 2 sides RT) — CORRECT for BingX taker")
        elif "0.0008" in source:
            print("    position_monitor.py: 0.0008 — WRONG (that is WEEX rate)")
            ERRORS.append("Commission rate 0.0008 is WEEX, not BingX")
        elif "0.001" in source:
            print("    position_monitor.py: 0.001 — WRONG (old rate)")
            ERRORS.append("Commission rate 0.001 is wrong")
        else:
            print("    position_monitor.py: no recognized rate found")

    # Architecture recommendation
    print("\n  ARCHITECTURE FOR LIVE:")
    print("    Current: round-trip commission calculated once at exit")
    print("    Recommendation: track per-trade in position_record")
    print("      entry_commission = notional * 0.0006  (on entry)")
    print("      exit_commission  = notional * 0.0006  (on exit)")
    print("      pnl_net = pnl_gross - entry_commission - exit_commission")
    print("    Benefit: accurate even if notional changes (partial close, etc.)")


# =========================================================================
# AUDIT 4: STRATEGY COMPARISON (Bot Plugin vs Backtester)
# =========================================================================
def audit_strategy():
    """Compare bot plugin features against backtester capabilities."""
    section("AUDIT 4: STRATEGY COMPARISON (Bot vs Backtester)")

    plugin_path = BOT_ROOT / "plugins" / "four_pillars_v384.py"
    if not plugin_path.exists():
        msg = "Plugin not found: " + str(plugin_path)
        print("  SKIP: " + msg)
        ERRORS.append(msg)
        return

    plugin_src = plugin_path.read_text(encoding="utf-8")

    # Check which signal columns the plugin reads
    signal_checks = {
        "long_a":  "A-grade LONG",
        "long_b":  "B-grade LONG",
        "long_c":  "C-grade LONG",
        "long_d":  "D-grade LONG",
        "short_a": "A-grade SHORT",
        "short_b": "B-grade SHORT",
        "short_c": "C-grade SHORT",
        "short_d": "D-grade SHORT",
        "reentry_long":  "Re-entry LONG",
        "reentry_short": "Re-entry SHORT",
        "add_long":  "Add LONG (pyramiding)",
        "add_short": "Add SHORT (pyramiding)",
    }

    print("  SIGNAL TYPES:")
    print("    Column".ljust(25) + "Description".ljust(25) + "Status")
    print("    " + "-" * 65)
    for col, desc in signal_checks.items():
        if '"' + col + '"' in plugin_src or "'" + col + "'" in plugin_src:
            status = "CHECKED"
        else:
            status = "IGNORED"
        print("    " + col.ljust(25) + desc.ljust(25) + status)

    # Check for trailing stop / breakeven features
    print("\n  TRADE MANAGEMENT FEATURES:")
    features = {
        "Trailing stop":    ["trailing", "be_trigger", "breakeven", "trail"],
        "Breakeven raise":  ["be_lock", "breakeven", "move_sl"],
        "Scale-out":        ["scaleout", "scale_out", "partial_close"],
        "Cooldown":         ["cooldown", "cool_down"],
        "AVWAP":            ["avwap", "anchored_vwap", "vwap"],
    }

    all_bot_src = ""
    for d in [BOT_ROOT, BOT_ROOT / "plugins"]:
        if not d.exists():
            continue
        for f in d.glob("*.py"):
            try:
                all_bot_src += f.read_text(encoding="utf-8").lower()
            except (UnicodeDecodeError, OSError):
                pass

    for feature, keywords in features.items():
        found = False
        for kw in keywords:
            if kw in all_bot_src:
                found = True
                break
        status = "PRESENT" if found else "MISSING"
        print("    " + feature.ljust(25) + status)
        if not found:
            ERRORS.append("Bot missing feature: " + feature)

    # Check backtester default params for reference
    bt_strategy = BACKTESTER_ROOT / "strategies" / "four_pillars.py"
    if bt_strategy.exists():
        bt_src = bt_strategy.read_text(encoding="utf-8")
        print("\n  BACKTESTER DEFAULT PARAMS (reference):")
        # Extract key params
        param_patterns = [
            ("sl_mult", r'"sl_mult":\s*([\d.]+)'),
            ("tp_mult", r'"tp_mult":\s*([\w.]+)'),
            ("be_trigger_atr", r'"be_trigger_atr":\s*([\d.]+)'),
            ("be_lock_atr", r'"be_lock_atr":\s*([\d.]+)'),
            ("cooldown", r'"cooldown":\s*(\d+)'),
            ("max_scaleouts", r'"max_scaleouts":\s*(\d+)'),
            ("commission_rate", r'"commission_rate":\s*([\d.]+)'),
        ]
        for name, pattern in param_patterns:
            match = re.search(pattern, bt_src)
            if match:
                print("    " + name.ljust(25) + match.group(1))
    else:
        print("\n  Backtester strategy not found at " + str(bt_strategy))

    # Signal generation shared code check
    print("\n  SHARED SIGNAL CODE:")
    if "from signals.four_pillars import compute_signals" in plugin_src:
        print("    PASS: Plugin imports compute_signals from backtester")
        print("    -> Indicators and state machine logic are IDENTICAL")
    else:
        print("    WARNING: Plugin does NOT import from backtester")
        ERRORS.append("Plugin signal code may differ from backtester")


# =========================================================================
# MAIN
# =========================================================================
def main():
    """Run all 4 audits and write report."""
    start = datetime.now(timezone.utc)
    print("BingX Bot Audit Report")
    print("Generated: " + start.strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("Bot root: " + str(BOT_ROOT))

    audit_trades()
    audit_docstrings()
    audit_commission()
    audit_strategy()

    # Summary
    section("SUMMARY")
    if ERRORS:
        print("  ISSUES FOUND: " + str(len(ERRORS)))
        for i, e in enumerate(ERRORS, 1):
            print("    " + str(i) + ". " + e)
    else:
        print("  ALL CHECKS PASSED")

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print("\n  Completed in " + str(round(elapsed, 1)) + "s")
    print("  Report saved to: " + str(REPORT_PATH))


if __name__ == "__main__":
    # Tee output to both console and report file
    import io

    class TeeWriter:
        """Write to both stdout and a file simultaneously."""
        def __init__(self, file_handle, original_stdout):
            """Initialize with file handle and original stdout."""
            self.file = file_handle
            self.stdout = original_stdout

        def write(self, data):
            """Write data to both destinations."""
            self.stdout.write(data)
            self.file.write(data)

        def flush(self):
            """Flush both destinations."""
            self.stdout.flush()
            self.file.flush()

    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        tee = TeeWriter(report_file, sys.stdout)
        sys.stdout = tee
        main()
        sys.stdout = tee.stdout

    print("\nReport written to: " + str(REPORT_PATH))

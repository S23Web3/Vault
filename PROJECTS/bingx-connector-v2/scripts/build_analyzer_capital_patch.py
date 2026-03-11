"""
Build script: Add capital usage analysis + scaling projections to analyze_trades.py
Also fixes dashboard be_raised/saw_green string-to-bool bug.

Run: cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector-v2"
     python scripts/build_analyzer_capital_patch.py
"""
import py_compile
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYZER = ROOT / "scripts" / "analyze_trades.py"
DASHBOARD = ROOT / "bingx-live-dashboard-v1-5.py"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
ERRORS = []


def backup(path):
    """Create timestamped backup of a file."""
    bak = path.with_suffix("." + TIMESTAMP + ".bak.py")
    shutil.copy2(path, bak)
    print("  BACKUP: " + str(bak))
    return bak


def verify(path):
    """Syntax-check a .py file; return True if clean."""
    try:
        py_compile.compile(str(path), doraise=True)
        print("  SYNTAX OK: " + str(path.name))
        return True
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        return False


def patch(path, old, new, label):
    """Replace old text with new in file. Returns True on success."""
    content = path.read_text(encoding="utf-8")
    if old not in content:
        print("  MISSING_ANCHOR: " + label)
        ERRORS.append(label)
        return False
    content = content.replace(old, new, 1)
    path.write_text(content, encoding="utf-8")
    print("  PATCHED: " + label)
    return True


def main():
    """Apply all patches."""
    print("=" * 60)
    print("Build: Analyzer capital patch + dashboard fix")
    print("=" * 60)

    # ------------------------------------------------------------------
    # PART 1: Patch analyze_trades.py
    # ------------------------------------------------------------------
    print("\n--- Patching analyze_trades.py ---")
    backup(ANALYZER)
    src = ANALYZER.read_text(encoding="utf-8")

    # Patch 1a: Add compute_concurrent_positions function after compute_rr_ratio
    ANCHOR_1A = "# ---------------------------------------------------------------------------\n# Formatters"
    NEW_FUNC_CAPITAL = '''def compute_concurrent_positions(trades):
    """Trace position opens/closes over time. Returns dict with peak stats.

    Uses entry_dt (open) and ts_dt (close) to build a timeline.
    """
    events = []
    for t in trades:
        entry = t.get("entry_dt")
        close = t.get("ts_dt")
        notional = t.get("notional_usd", 0)
        margin = notional / 10.0  # derive margin from notional/leverage
        if entry and close:
            events.append((entry, +1, +margin, +notional, t["symbol"]))
            events.append((close, -1, -margin, -notional, t["symbol"]))
    events.sort(key=lambda x: x[0])
    current_count = 0
    current_margin = 0.0
    current_notional = 0.0
    peak_count = 0
    peak_margin = 0.0
    peak_notional = 0.0
    peak_time = None
    timeline = []
    for ts, delta, margin_delta, notional_delta, sym in events:
        current_count += delta
        current_margin += margin_delta
        current_notional += notional_delta
        if current_count > peak_count:
            peak_count = current_count
            peak_margin = current_margin
            peak_notional = current_notional
            peak_time = ts
        timeline.append((ts, current_count, round(current_margin, 2),
                         round(current_notional, 2)))
    return {
        "peak_count": peak_count,
        "peak_margin": round(peak_margin, 2),
        "peak_notional": round(peak_notional, 2),
        "peak_time": peak_time,
        "total_events": len(events),
        "timeline": timeline,
    }


def compute_scaling_projection(trades, capital_stats, new_margin, new_leverage,
                               rebate_pct=0.70, bingx_taker_rt=0.0016):
    """Project PnL and volume at different margin/leverage.

    Returns dict with scaled metrics.
    """
    if not trades:
        return {}
    current_notional = trades[0].get("notional_usd", 50.0)
    new_notional = new_margin * new_leverage
    scale = new_notional / current_notional if current_notional else 1.0
    n = len(trades)
    winners = [t["pnl_net"] for t in trades if t["pnl_net"] > 0]
    losers = [t["pnl_net"] for t in trades if t["pnl_net"] < 0]
    gross_wins = sum(winners) * scale
    gross_losses = sum(losers) * scale
    bot_pnl = (sum(winners) + sum(losers)) * scale
    # Bot uses commission_rate from config (typically 0.001 RT).
    # Actual BingX = bingx_taker_rt. With rebate, net = bingx_taker_rt * (1 - rebate).
    bot_commission_rt = 0.001  # what the bot deducts
    actual_net_commission_rt = bingx_taker_rt * (1.0 - rebate_pct)
    over_deduction_per_trade = (bot_commission_rt - actual_net_commission_rt) * new_notional
    true_pnl = bot_pnl + over_deduction_per_trade * n
    rt_volume = new_notional * 2.0 * n
    commission_gross = rt_volume * bingx_taker_rt / 2.0  # per-side rate on both sides
    rebate = commission_gross * rebate_pct
    peak_margin = capital_stats.get("peak_count", 1) * new_margin
    peak_notional = capital_stats.get("peak_count", 1) * new_notional
    # Monthly projection (extrapolate from runtime)
    if len(trades) >= 2:
        first_entry = min(t["entry_dt"] for t in trades if t.get("entry_dt"))
        last_close = max(t["ts_dt"] for t in trades if t.get("ts_dt"))
        hours = (last_close - first_entry).total_seconds() / 3600.0
        trades_per_day = n / (hours / 24.0) if hours > 0 else 0
    else:
        trades_per_day = 0
        hours = 0
    monthly_trades = trades_per_day * 30
    monthly_volume = monthly_trades * new_notional * 2.0
    monthly_commission = monthly_volume * bingx_taker_rt / 2.0
    monthly_rebate = monthly_commission * rebate_pct
    monthly_bot_pnl = bot_pnl / n * monthly_trades if n else 0
    monthly_true_pnl = true_pnl / n * monthly_trades if n else 0
    return {
        "new_margin": new_margin,
        "new_leverage": new_leverage,
        "new_notional": new_notional,
        "scale_factor": scale,
        "n_trades": n,
        "runtime_hours": round(hours, 1),
        "trades_per_day": round(trades_per_day, 1),
        "gross_wins": round(gross_wins, 2),
        "gross_losses": round(gross_losses, 2),
        "bot_pnl_scaled": round(bot_pnl, 2),
        "true_pnl_scaled": round(true_pnl, 2),
        "over_deduction_total": round(over_deduction_per_trade * n, 2),
        "rt_volume": round(rt_volume, 2),
        "commission_gross": round(commission_gross, 2),
        "rebate": round(rebate, 2),
        "commission_net": round(commission_gross - rebate, 2),
        "peak_concurrent": capital_stats.get("peak_count", 0),
        "peak_margin": round(peak_margin, 2),
        "peak_notional": round(peak_notional, 2),
        "monthly_trades": round(monthly_trades, 0),
        "monthly_volume": round(monthly_volume, 0),
        "monthly_commission": round(monthly_commission, 2),
        "monthly_rebate": round(monthly_rebate, 2),
        "monthly_bot_pnl": round(monthly_bot_pnl, 2),
        "monthly_true_pnl": round(monthly_true_pnl, 2),
    }


'''
    INSERT_1A = NEW_FUNC_CAPITAL + "# ---------------------------------------------------------------------------\n# Formatters"
    if ANCHOR_1A in src:
        src = src.replace(ANCHOR_1A, INSERT_1A, 1)
        print("  PATCHED: compute_concurrent_positions + compute_scaling_projection")
    else:
        print("  MISSING_ANCHOR: formatters section")
        ERRORS.append("formatters section")

    # Patch 1b: Add capital + scaling section to build_report()
    # Insert before the "Key Findings" section
    ANCHOR_1B = '    # ------------------------------------------------------------------\n    # Section 5: Key Findings'
    CAPITAL_REPORT_SECTION = '''    # ------------------------------------------------------------------
    # Section 4b: Capital Usage & Scaling Projections
    # ------------------------------------------------------------------
    lines.append("## 4b. Capital Usage & Scaling Projections")
    lines.append("")
    cap = compute_concurrent_positions(p3)
    lines.append("### Current Run ($" + str(int(MARGIN_USD)) + " margin, "
                 + str(LEVERAGE) + "x leverage, $"
                 + str(int(MARGIN_USD * LEVERAGE)) + " notional)")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Peak concurrent positions | " + str(cap["peak_count"]) + " |")
    lines.append("| Peak margin deployed | $" + str(cap["peak_margin"]) + " |")
    lines.append("| Peak notional at risk | $" + str(cap["peak_notional"]) + " |")
    if cap["peak_time"]:
        lines.append("| Peak time | " + cap["peak_time"].strftime("%Y-%m-%d %H:%M UTC") + " |")
    lines.append("")
    # Scaling projections
    scenarios = [
        (500, 20, "Scaled: $500 margin, 20x"),
        (100, 20, "Scaled: $100 margin, 20x"),
        (20, 20, "Scaled: $20 margin, 20x"),
    ]
    for sc_margin, sc_lev, sc_label in scenarios:
        sc = compute_scaling_projection(p3, cap, sc_margin, sc_lev)
        if not sc:
            continue
        lines.append("### " + sc_label + " ($"
                     + str(int(sc["new_notional"])) + " notional)")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append("| Scale factor | " + str(round(sc["scale_factor"], 1)) + "x |")
        lines.append("| Bot PnL (scaled) | " + fmt_pnl(sc["bot_pnl_scaled"]) + " |")
        lines.append("| Commission over-deduction | " + fmt_pnl(sc["over_deduction_total"]) + " |")
        lines.append("| True PnL (after 70% rebate) | " + fmt_pnl(sc["true_pnl_scaled"]) + " |")
        lines.append("| RT volume (" + str(sc["n_trades"]) + " trades) | $"
                     + "{:,.0f}".format(sc["rt_volume"]) + " |")
        lines.append("| Commission gross | $"
                     + "{:,.2f}".format(sc["commission_gross"]) + " |")
        lines.append("| Rebate (70%) | $"
                     + "{:,.2f}".format(sc["rebate"]) + " |")
        lines.append("| Peak margin needed | $"
                     + "{:,.0f}".format(sc["peak_margin"])
                     + " (" + str(sc["peak_concurrent"]) + " concurrent) |")
        lines.append("| --- | --- |")
        lines.append("| **Monthly projection** | |")
        lines.append("| Trades/day (est) | " + str(sc["trades_per_day"]) + " |")
        lines.append("| Monthly trades | " + str(int(sc["monthly_trades"])) + " |")
        lines.append("| Monthly volume | $"
                     + "{:,.0f}".format(sc["monthly_volume"]) + " |")
        lines.append("| Monthly rebate | $"
                     + "{:,.0f}".format(sc["monthly_rebate"]) + " |")
        lines.append("| Monthly bot PnL | " + fmt_pnl(sc["monthly_bot_pnl"]) + " |")
        lines.append("| Monthly true PnL | " + fmt_pnl(sc["monthly_true_pnl"]) + " |")
        lines.append("")
    lines.append("---")
    lines.append("")

    '''
    INSERT_1B = CAPITAL_REPORT_SECTION + '    # ------------------------------------------------------------------\n    # Section 5: Key Findings'
    if ANCHOR_1B in src:
        src = src.replace(ANCHOR_1B, INSERT_1B, 1)
        print("  PATCHED: capital usage + scaling report section")
    else:
        print("  MISSING_ANCHOR: Section 5 Key Findings")
        ERRORS.append("Section 5 Key Findings")

    # Patch 1c: Update COMMISSION constants to match actual BingX rates
    src = src.replace(
        "COMMISSION_TAKER = 0.0005       # 0.05% per side",
        "COMMISSION_TAKER = 0.0008       # 0.08% per side",
        1)
    src = src.replace(
        "COMMISSION_RT_GROSS = 0.001     # 0.10% round trip (entry + exit)",
        "COMMISSION_RT_GROSS = 0.0016    # 0.16% round trip (entry + exit)",
        1)
    src = src.replace(
        "COMMISSION_REBATE = 0.50        # 50% rebated next day",
        "COMMISSION_REBATE = 0.70        # 70% rebated next day",
        1)
    print("  PATCHED: commission constants (0.08%/side, 0.16% RT, 70% rebate)")

    ANALYZER.write_text(src, encoding="utf-8")
    if not verify(ANALYZER):
        ERRORS.append("analyze_trades.py")

    # ------------------------------------------------------------------
    # PART 2: Fix dashboard be_raised/saw_green string-to-bool
    # ------------------------------------------------------------------
    print("\n--- Patching dashboard (be_raised/saw_green fix) ---")
    backup(DASHBOARD)

    # Fix 2a: be_raised sum — string "True"/"False" -> bool count
    ok_2a = patch(
        DASHBOARD,
        '        be_count = int(df["be_raised"].sum())',
        '        be_count = int((df["be_raised"].astype(str).str.lower() == "true").sum())',
        "be_raised sum fix"
    )

    # Fix 2b: saw_green sum — same issue
    ok_2b = patch(
        DASHBOARD,
        '            lsg_pct = round(losing["saw_green"].sum() / len(losing) * 100, 1)',
        '            lsg_pct = round((losing["saw_green"].astype(str).str.lower() == "true").sum() / len(losing) * 100, 1)',
        "saw_green sum fix"
    )

    if not verify(DASHBOARD):
        ERRORS.append("dashboard")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    if ERRORS:
        print("BUILD FAILED -- errors: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("BUILD OK -- all patches applied, all files compile clean")
        print("\nRun analyzer:")
        print('  cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector-v2"')
        print("  python scripts/analyze_trades.py")
        print("\nRestart dashboard to pick up be_raised fix.")


if __name__ == "__main__":
    main()

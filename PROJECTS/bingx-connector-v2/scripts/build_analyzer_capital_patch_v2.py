"""
Build script: Add capital usage, max drawdown, cross-run comparison to analyze_trades.py.
Also fixes dashboard be_raised/saw_green string-to-bool bug.

Run: cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector-v2"
     python scripts/build_analyzer_capital_patch_v2.py
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
    print("Build: Analyzer capital + drawdown + cross-run + dashboard fix")
    print("=" * 60)

    # ==================================================================
    # PART 1: Patch analyze_trades.py
    # ==================================================================
    print("\n--- Patching analyze_trades.py ---")
    backup(ANALYZER)
    src = ANALYZER.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Patch 1a: Add V1_TRADES_CSV path constant after TRADES_CSV
    # ------------------------------------------------------------------
    src = src.replace(
        'TRADES_CSV = BOT_ROOT / "trades.csv"',
        'TRADES_CSV = BOT_ROOT / "trades.csv"\n'
        'V1_BOT_ROOT = BOT_ROOT.parent / "bingx-connector"\n'
        'V1_TRADES_CSV = V1_BOT_ROOT / "trades.csv"',
        1)
    print("  PATCHED: V1_TRADES_CSV path constant")

    # ------------------------------------------------------------------
    # Patch 1b: Add new analysis functions before Formatters section
    # ------------------------------------------------------------------
    ANCHOR_FUNCS = ("# ---------------------------------------------------------------------------\n"
                    "# Formatters")

    NEW_FUNCTIONS = '''def compute_concurrent_positions(trades):
    """Trace position opens/closes over time. Returns dict with peak stats."""
    events = []
    for t in trades:
        entry = t.get("entry_dt")
        close = t.get("ts_dt")
        notional = t.get("notional_usd", 0)
        margin = notional / 10.0
        if entry and close:
            events.append((entry, +1, +margin, +notional))
            events.append((close, -1, -margin, -notional))
    events.sort(key=lambda x: x[0])
    cur_count = 0
    cur_margin = 0.0
    cur_notional = 0.0
    peak_count = 0
    peak_margin = 0.0
    peak_notional = 0.0
    peak_time = None
    for ts, delta, m_delta, n_delta in events:
        cur_count += delta
        cur_margin += m_delta
        cur_notional += n_delta
        if cur_count > peak_count:
            peak_count = cur_count
            peak_margin = cur_margin
            peak_notional = cur_notional
            peak_time = ts
    return {
        "peak_count": peak_count,
        "peak_margin": round(peak_margin, 2),
        "peak_notional": round(peak_notional, 2),
        "peak_time": peak_time,
    }


def compute_max_drawdown(trades):
    """Compute max drawdown from running cumulative PnL. Returns dict."""
    if not trades:
        return {"max_dd": 0, "max_dd_time": None, "equity_curve": []}
    sorted_t = sorted(trades, key=lambda t: t.get("ts_dt") or t.get("entry_dt"))
    running = 0.0
    peak_equity = 0.0
    max_dd = 0.0
    max_dd_time = None
    worst_running = 0.0
    worst_running_time = None
    curve = []
    for t in sorted_t:
        running += t["pnl_net"]
        curve.append((t.get("ts_dt"), round(running, 4)))
        if running > peak_equity:
            peak_equity = running
        dd = peak_equity - running
        if dd > max_dd:
            max_dd = dd
            max_dd_time = t.get("ts_dt")
        if running < worst_running:
            worst_running = running
            worst_running_time = t.get("ts_dt")
    return {
        "max_dd": round(max_dd, 4),
        "max_dd_time": max_dd_time,
        "worst_equity": round(worst_running, 4),
        "worst_equity_time": worst_running_time,
        "final_equity": round(running, 4),
        "equity_curve": curve,
    }


def compute_scaling_projection(trades, capital_stats, new_margin, new_leverage,
                               rebate_pct=0.70, bingx_taker_rt=0.0016):
    """Project PnL and volume at different margin/leverage."""
    if not trades:
        return {}
    current_notional = trades[0].get("notional_usd", 50.0)
    new_notional = new_margin * new_leverage
    scale = new_notional / current_notional if current_notional else 1.0
    n = len(trades)
    total_pnl = sum(t["pnl_net"] for t in trades)
    bot_pnl = total_pnl * scale
    bot_commission_rt = 0.001
    actual_net_rt = bingx_taker_rt * (1.0 - rebate_pct)
    over_deduction = (bot_commission_rt - actual_net_rt) * new_notional * n
    true_pnl = bot_pnl + over_deduction
    rt_volume = new_notional * 2.0 * n
    commission_gross = n * new_notional * bingx_taker_rt
    rebate = commission_gross * rebate_pct
    peak_margin = capital_stats.get("peak_count", 1) * new_margin
    if n >= 2:
        first = min(t["entry_dt"] for t in trades if t.get("entry_dt"))
        last = max(t["ts_dt"] for t in trades if t.get("ts_dt"))
        hours = (last - first).total_seconds() / 3600.0
        tpd = n / (hours / 24.0) if hours > 0 else 0
    else:
        tpd = 0
        hours = 0
    mt = tpd * 30
    return {
        "new_margin": new_margin,
        "new_leverage": new_leverage,
        "new_notional": new_notional,
        "scale": round(scale, 1),
        "bot_pnl": round(bot_pnl, 2),
        "true_pnl": round(true_pnl, 2),
        "over_deduction": round(over_deduction, 2),
        "rt_volume": round(rt_volume, 2),
        "commission_gross": round(commission_gross, 2),
        "rebate": round(rebate, 2),
        "peak_margin": round(peak_margin, 2),
        "peak_count": capital_stats.get("peak_count", 0),
        "hours": round(hours, 1),
        "trades_per_day": round(tpd, 1),
        "monthly_trades": round(mt, 0),
        "monthly_volume": round(mt * new_notional * 2.0, 0),
        "monthly_rebate": round(mt * new_notional * bingx_taker_rt * rebate_pct, 0),
        "monthly_bot_pnl": round(bot_pnl / n * mt, 2) if n else 0,
        "monthly_true_pnl": round(true_pnl / n * mt, 2) if n else 0,
    }


def load_v1_trades(path):
    """Load v1 trades.csv (shorter header). Returns list of trade dicts."""
    import csv as _csv
    trades = []
    if not path.exists():
        return trades
    with open(path, "r", encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            try:
                row["pnl_net"] = float(row["pnl_net"])
                row["notional_usd"] = float(row["notional_usd"])
                row["entry_price"] = float(row["entry_price"])
                row["exit_price"] = float(row["exit_price"])
                row["quantity"] = float(row["quantity"])
                ts_str = row["timestamp"].replace("+00:00", "").rstrip("Z")
                entry_str = row["entry_time"].replace("+00:00", "").rstrip("Z")
                row["ts_dt"] = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
                row["entry_dt"] = datetime.fromisoformat(entry_str).replace(tzinfo=timezone.utc)
                row["hold_minutes"] = (row["ts_dt"] - row["entry_dt"]).total_seconds() / 60.0
            except (ValueError, KeyError):
                row["hold_minutes"] = 0.0
                continue
            trades.append(row)
    return trades


def compute_run_stats(trades, label):
    """Compute summary stats for one bot run. Returns dict."""
    if not trades:
        return {"label": label, "n": 0}
    n = len(trades)
    pnls = [t["pnl_net"] for t in trades]
    winners = [p for p in pnls if p > 0]
    losers = [p for p in pnls if p < 0]
    cap = compute_concurrent_positions(trades)
    dd = compute_max_drawdown(trades)
    first = min(t["entry_dt"] for t in trades if t.get("entry_dt"))
    last = max(t["ts_dt"] for t in trades if t.get("ts_dt"))
    hours = (last - first).total_seconds() / 3600.0
    return {
        "label": label,
        "n": n,
        "start": first.strftime("%Y-%m-%d %H:%M"),
        "end": last.strftime("%Y-%m-%d %H:%M"),
        "hours": round(hours, 1),
        "win_count": len(winners),
        "loss_count": len(losers),
        "win_rate": round(len(winners) / n * 100, 1),
        "total_pnl": round(sum(pnls), 2),
        "avg_win": round(sum(winners) / len(winners), 4) if winners else 0,
        "avg_loss": round(sum(losers) / len(losers), 4) if losers else 0,
        "rr": round(abs(sum(winners) / len(winners)) / abs(sum(losers) / len(losers)), 3) if winners and losers else 0,
        "peak_positions": cap["peak_count"],
        "peak_margin": cap["peak_margin"],
        "peak_notional": cap["peak_notional"],
        "max_drawdown": dd["max_dd"],
        "worst_equity": dd["worst_equity"],
    }


def build_cross_run_report(v1_trades, v2_trades):
    """Build cross-run comparison section. Returns list of markdown lines."""
    from datetime import datetime as _dt, timezone as _tz
    lines = []
    # Filter v1 to $50 notional, March 3+ only (the comparable run)
    v1_50 = [t for t in v1_trades
             if abs(t["notional_usd"] - 50.0) < 1.0
             and t.get("entry_dt")
             and t["entry_dt"] >= _dt(2026, 3, 3, tzinfo=_tz.utc)]
    r1 = compute_run_stats(v1_50, "v1 (Mar 3-6)")
    r2 = compute_run_stats(v2_trades, "v2 (Mar 6-7)")
    runs = [r for r in [r1, r2] if r["n"] > 0]
    if len(runs) < 2:
        lines.append("## Cross-Run Comparison")
        lines.append("")
        lines.append("Not enough runs to compare (need v1 + v2 trades.csv).")
        return lines
    lines.append("## Cross-Run Comparison")
    lines.append("")
    # Header
    lines.append("| Metric | " + " | ".join(r["label"] for r in runs) + " | Average |")
    lines.append("|--------|" + "|".join(["-------:"] * len(runs)) + "|-------:|")
    # Rows
    def row(name, key, fmt="{}"):
        """Build one table row."""
        vals = [r.get(key, 0) for r in runs]
        avg = sum(vals) / len(vals)
        cells = " | ".join(fmt.format(v) for v in vals)
        return "| " + name + " | " + cells + " | " + fmt.format(round(avg, 2)) + " |"
    lines.append(row("Trades", "n", "{}"))
    lines.append(row("Runtime (hours)", "hours", "{}"))
    lines.append(row("Win rate %", "win_rate", "{}%"))
    lines.append(row("Avg win $", "avg_win", "${}"))
    lines.append(row("Avg loss $", "avg_loss", "${}"))
    lines.append(row("R:R", "rr", "{}"))
    lines.append(row("Total PnL", "total_pnl", "${}"))
    lines.append(row("Peak concurrent", "peak_positions", "{}"))
    lines.append(row("Peak margin $", "peak_margin", "${}"))
    lines.append(row("Peak notional $", "peak_notional", "${}"))
    lines.append(row("Max drawdown $", "max_drawdown", "${}"))
    lines.append(row("Worst equity $", "worst_equity", "${}"))
    lines.append("")
    # Scaling projection using AVERAGE stats
    avg_cap = {
        "peak_count": round(sum(r["peak_positions"] for r in runs) / len(runs)),
    }
    all_trades = v1_50 + list(v2_trades)
    lines.append("### Scaling Projection (based on average of both runs)")
    lines.append("")
    for sc_margin, sc_lev, sc_label in [(500, 20, "$500/20x"), (100, 20, "$100/20x")]:
        sc = compute_scaling_projection(all_trades, avg_cap, sc_margin, sc_lev)
        if not sc:
            continue
        lines.append("**" + sc_label + "** ($" + str(int(sc["new_notional"])) + " notional)")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|------:|")
        lines.append("| Scale | " + str(sc["scale"]) + "x |")
        lines.append("| Bot PnL (all " + str(len(all_trades)) + " trades) | $"
                     + str(sc["bot_pnl"]) + " |")
        lines.append("| True PnL (70% rebate) | $" + str(sc["true_pnl"]) + " |")
        lines.append("| RT volume | $" + "{:,.0f}".format(sc["rt_volume"]) + " |")
        lines.append("| Rebate earned | $" + "{:,.0f}".format(sc["rebate"]) + " |")
        lines.append("| Peak margin needed | $"
                     + "{:,.0f}".format(sc["peak_margin"])
                     + " (" + str(sc["peak_count"]) + " positions) |")
        lines.append("| Trades/day | " + str(sc["trades_per_day"]) + " |")
        lines.append("| Monthly volume | $" + "{:,.0f}".format(sc["monthly_volume"]) + " |")
        lines.append("| Monthly rebate | $" + "{:,.0f}".format(sc["monthly_rebate"]) + " |")
        lines.append("| Monthly bot PnL | $" + str(sc["monthly_bot_pnl"]) + " |")
        lines.append("| Monthly true PnL | $" + str(sc["monthly_true_pnl"]) + " |")
        lines.append("")
    return lines


'''
    INSERT_FUNCS = NEW_FUNCTIONS + ("# ---------------------------------------------------------------------------\n"
                                    "# Formatters")
    if ANCHOR_FUNCS in src:
        src = src.replace(ANCHOR_FUNCS, INSERT_FUNCS, 1)
        print("  PATCHED: 7 new functions (capital, drawdown, scaling, v1 loader, run stats, cross-run)")
    else:
        print("  MISSING_ANCHOR: Formatters section")
        ERRORS.append("Formatters section")

    # ------------------------------------------------------------------
    # Patch 1c: Add capital + cross-run section to build_report()
    # ------------------------------------------------------------------
    ANCHOR_REPORT = ('    # ------------------------------------------------------------------\n'
                     '    # Section 5: Key Findings')

    REPORT_SECTION = '''    # ------------------------------------------------------------------
    # Section 4b: Capital Usage & Max Drawdown
    # ------------------------------------------------------------------
    lines.append("## 4b. Capital Usage & Max Drawdown")
    lines.append("")
    cap = compute_concurrent_positions(p3)
    dd = compute_max_drawdown(p3)
    lines.append("| Metric | Value |")
    lines.append("|--------|------:|")
    lines.append("| Peak concurrent positions | " + str(cap["peak_count"]) + " |")
    lines.append("| Peak margin deployed | $" + str(cap["peak_margin"]) + " |")
    lines.append("| Peak notional at risk | $" + str(cap["peak_notional"]) + " |")
    if cap["peak_time"]:
        lines.append("| Peak time | " + cap["peak_time"].strftime("%Y-%m-%d %H:%M UTC") + " |")
    lines.append("| Max drawdown | $" + str(dd["max_dd"]) + " |")
    if dd["max_dd_time"]:
        lines.append("| Max drawdown time | " + dd["max_dd_time"].strftime("%Y-%m-%d %H:%M UTC") + " |")
    lines.append("| Worst running PnL | $" + str(dd["worst_equity"]) + " |")
    lines.append("| Final PnL | $" + str(dd["final_equity"]) + " |")
    lines.append("")
    # Cross-run comparison (v1 + v2)
    v1_all = load_v1_trades(V1_TRADES_CSV)
    cross_lines = build_cross_run_report(v1_all, p3)
    lines.extend(cross_lines)
    lines.append("---")
    lines.append("")

    '''
    INSERT_REPORT = REPORT_SECTION + ('    # ------------------------------------------------------------------\n'
                                      '    # Section 5: Key Findings')
    if ANCHOR_REPORT in src:
        src = src.replace(ANCHOR_REPORT, INSERT_REPORT, 1)
        print("  PATCHED: Section 4b capital + cross-run in report")
    else:
        print("  MISSING_ANCHOR: Section 5 Key Findings")
        ERRORS.append("Section 5 Key Findings")

    # ------------------------------------------------------------------
    # Patch 1d: Update COMMISSION constants
    # ------------------------------------------------------------------
    replacements = [
        ("COMMISSION_TAKER = 0.0005       # 0.05% per side",
         "COMMISSION_TAKER = 0.0008       # 0.08% per side"),
        ("COMMISSION_RT_GROSS = 0.001     # 0.10% round trip (entry + exit)",
         "COMMISSION_RT_GROSS = 0.0016    # 0.16% round trip (entry + exit)"),
        ("COMMISSION_REBATE = 0.50        # 50% rebated next day",
         "COMMISSION_REBATE = 0.70        # 70% rebated next day"),
    ]
    for old_val, new_val in replacements:
        if old_val in src:
            src = src.replace(old_val, new_val, 1)
    print("  PATCHED: commission constants (0.08%/side, 70% rebate)")

    # ------------------------------------------------------------------
    # Patch 1e: Add datetime import if needed for load_v1_trades
    # ------------------------------------------------------------------
    if "from datetime import datetime, timezone" not in src:
        src = src.replace(
            "from datetime import datetime, timezone",
            "from datetime import datetime, timezone",
            1)
    # datetime already imported at top

    # Write and verify
    ANALYZER.write_text(src, encoding="utf-8")
    if not verify(ANALYZER):
        ERRORS.append("analyze_trades.py")

    # ==================================================================
    # PART 2: Fix dashboard be_raised/saw_green string-to-bool
    # ==================================================================
    print("\n--- Patching dashboard (be_raised/saw_green fix) ---")
    backup(DASHBOARD)

    patch(
        DASHBOARD,
        '        be_count = int(df["be_raised"].sum())',
        '        be_count = int((df["be_raised"].astype(str).str.lower() == "true").sum())',
        "be_raised sum fix"
    )

    patch(
        DASHBOARD,
        '            lsg_pct = round(losing["saw_green"].sum() / len(losing) * 100, 1)',
        '            lsg_pct = round((losing["saw_green"].astype(str).str.lower() == "true").sum() / len(losing) * 100, 1)',
        "saw_green sum fix"
    )

    if not verify(DASHBOARD):
        ERRORS.append("dashboard")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    if ERRORS:
        print("BUILD FAILED -- errors: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("BUILD OK -- all patches applied, all files compile clean")
        print("\nRun analyzer:")
        print('  cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector-v2"')
        print("  python scripts/analyze_trades.py")
        print("\nRestart dashboard for analytics fix.")


if __name__ == "__main__":
    main()

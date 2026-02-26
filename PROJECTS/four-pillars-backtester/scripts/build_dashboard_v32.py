"""
Build script for Dashboard v3.2 -- Bugfixes + UX from user testing.

Patches scripts/dashboard.py surgically at known anchor points.
12 patches: DD clipping, Arrow fixes, deprecation fixes, UX improvements, tooltips.

Usage:
    python scripts/build_dashboard_v32.py --dry-run   # preview, no write
    python scripts/build_dashboard_v32.py              # apply patches
"""
import sys
import json
import argparse
import py_compile
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = PROJECT_ROOT / "scripts" / "dashboard.py"


def read_file():
    """Read dashboard.py and return as list of lines."""
    return DASHBOARD.read_text(encoding="utf-8").split("\n")


def find_anchor(lines, anchor_text):
    """Find line index containing anchor_text. Returns index or -1."""
    for i, line in enumerate(lines):
        if anchor_text in line:
            return i
    return -1


def find_all_anchors(lines, anchor_text):
    """Find ALL line indices containing anchor_text. Returns list of indices."""
    results = []
    for i, line in enumerate(lines):
        if anchor_text in line:
            results.append(i)
    return results


def apply_patches(lines):
    """Apply all v3.2 patches. Returns (patched_lines, report)."""
    report = {"anchors_found": [], "anchors_missing": [], "patches": []}

    def anchor(text):
        """Find anchor and log to report; returns index or -1."""
        idx = find_anchor(lines, text)
        if idx >= 0:
            report["anchors_found"].append(text[:80])
        else:
            report["anchors_missing"].append(text[:80])
        return idx

    # ====================================================================
    # PATCH 1: Clip portfolio DD at -100% (line ~351)
    # ====================================================================
    idx = anchor("dd_arr = np.where(peaks > 0, (portfolio_eq - peaks) / peaks * 100.0, 0.0)")
    if idx >= 0:
        lines[idx] = lines[idx].rstrip()
        # Add clip on next line
        indent = "    "
        lines.insert(idx + 1, indent + "dd_arr = np.clip(dd_arr, -100.0, 0.0)")
        report["patches"].append("P1: Clip portfolio DD at -100%")

    # ====================================================================
    # PATCH 2: Stress test table -- raw floats + Styler (lines ~847-863)
    # ====================================================================
    idx = anchor("stress_rows.append({")
    if idx >= 0:
        # Find the block from stress_rows.append({ to the closing })
        # Replace the formatted string values with raw numeric values
        # Search for the Net and Avg Capital lines within 15 lines
        for j in range(idx, min(idx + 15, len(lines))):
            line_stripped = lines[j].strip()
            if '"Net":' in lines[j] and "${net_s" in lines[j]:
                lines[j] = '                                "Net": round(net_s, 2),'
                report["patches"].append("P2a: Stress Net -> raw float")
            if '"Avg Capital":' in lines[j] and "${cap_s" in lines[j]:
                lines[j] = '                                "Avg Capital": round(cap_s, 0),'
                report["patches"].append("P2b: Stress Avg Capital -> raw float")
            if '"DD%":' in lines[j] and 'str(' in lines[j]:
                lines[j] = '                                "DD%": round(sw["dd_pct"], 1),'
                report["patches"].append("P2c: Stress DD% -> raw float")
            if '"PF":' in lines[j] and 'str(' in lines[j]:
                lines[j] = '                                "PF": round(ms_s["profit_factor"], 2),'
                report["patches"].append("P2d: Stress PF -> raw float")
            if '"LSG%":' in lines[j] and 'f"' in lines[j]:
                lines[j] = '                                "LSG%": round(lsg_s, 1),'
                report["patches"].append("P2e: Stress LSG% -> raw float")
            if '"WR":' in lines[j] and '_wr_str' in lines[j]:
                lines[j] = '                                "WR": round(_wr_val * 100, 1) if ms_s["total_trades"] > 0 else 0,'
                report["patches"].append("P2f: Stress WR -> raw float")

        # Now fix the display line: st.dataframe(pd.DataFrame(stress_rows),...
        disp_idx = anchor("st.dataframe(pd.DataFrame(stress_rows)")
        if disp_idx >= 0:
            old_line = lines[disp_idx]
            indent_disp = "                        "
            lines[disp_idx] = (indent_disp +
                'st.dataframe(pd.DataFrame(stress_rows).style.format({'
                '"Net": "${:,.2f}", "Avg Capital": "${:,.0f}", '
                '"DD%": "{:.1f}%", "PF": "{:.2f}", "LSG%": "{:.1f}%", "WR": "{:.1f}%"'
                '}), hide_index=True)')
            report["patches"].append("P2g: Stress table display with Styler")

    # ====================================================================
    # PATCH 3: use_container_width=True -> remove for st.dataframe (deprecation)
    # Replace with nothing for st.dataframe, keep for st.plotly_chart
    # ====================================================================
    p3_count = 0
    for i in range(len(lines)):
        line = lines[i]
        # st.dataframe calls: remove use_container_width=True
        if "st.dataframe(" in line and "use_container_width=True" in line:
            # Remove ", use_container_width=True" or "use_container_width=True, "
            lines[i] = line.replace(", use_container_width=True", "").replace("use_container_width=True, ", "").replace("use_container_width=True", "")
            p3_count += 1
        # Also handle .style.format(...) calls that we just added -- those are on st.dataframe too
    if p3_count > 0:
        report["patches"].append(f"P3: Removed use_container_width from {p3_count} st.dataframe calls")

    # ====================================================================
    # PATCH 4: Move buttons to top of sidebar (after date range section)
    # ====================================================================
    # Find the buttons block: lines with run_single, run_sweep, run_portfolio, batch_top
    # and the if run_single/run_sweep/run_portfolio handlers
    btn_start = anchor("# -- Action buttons --")
    if btn_start >= 0:
        # Find end of button block (includes mode transitions)
        btn_end = btn_start
        for j in range(btn_start, min(btn_start + 20, len(lines))):
            if 'st.session_state["portfolio_data"] = None' in lines[j]:
                btn_end = j
                break

        # Extract the button block
        btn_block = lines[btn_start:btn_end + 1]

        # Remove from old location
        del lines[btn_start:btn_end + 1]

        # Find insertion point: after date range caption (st.sidebar.caption(_dr_label))
        insert_idx = find_anchor(lines, "st.sidebar.caption(_dr_label)")
        if insert_idx >= 0:
            insert_at = insert_idx + 1
        else:
            # Fallback: after date_range = (date_start, date_end)
            insert_at = find_anchor(lines, 'date_range = (_ds.date(), _de.date())')
            if insert_at >= 0:
                insert_at += 3  # after the caption line
            else:
                insert_at = find_anchor(lines, "# -- Stochastic K lengths")
                if insert_at >= 0:
                    insert_at -= 1  # insert before stochastics

        if insert_at >= 0:
            # Insert blank line + button block
            for bi, bline in enumerate(btn_block):
                lines.insert(insert_at + bi, bline)
            report["patches"].append(f"P4: Moved buttons block ({len(btn_block)} lines) to top of sidebar")
        else:
            report["anchors_missing"].append("P4: Could not find insertion point for buttons")

    # ====================================================================
    # PATCH 5: Add spinner to portfolio backtest (line ~1773)
    # ====================================================================
    idx = anchor("if run_port and port_symbols:")
    if idx >= 0:
        indent = "    "
        # Add spinner wrapper: insert after the if line
        # Original: if run_port and port_symbols:
        #               coin_results = []
        # New:      if run_port and port_symbols:
        #               with st.spinner("Running portfolio backtest..."):
        #                   coin_results = []
        # We need to add the with line and indent everything inside by 4 more spaces
        next_line_idx = idx + 1
        # Check if spinner already added
        if "st.spinner" not in lines[next_line_idx]:
            lines.insert(next_line_idx, indent * 2 + 'with st.spinner("Running portfolio backtest..."):')
            # Now indent all lines from next_line_idx+1 until we hit a line with same or less indentation
            # Find the end of the if block
            base_indent = len(lines[idx]) - len(lines[idx].lstrip())
            j = next_line_idx + 1
            while j < len(lines):
                line = lines[j]
                if line.strip() == "":
                    j += 1
                    continue
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= base_indent:
                    break
                # Add 4 spaces of indent
                lines[j] = "    " + lines[j]
                j += 1
            report["patches"].append("P5: Added spinner to portfolio backtest")

    # ====================================================================
    # PATCH 6: Cap per-coin DD% display at -100 in LSG table (line ~1850)
    # ====================================================================
    idx = anchor('"DD%": round(ms_c["max_drawdown_pct"], 1),')
    if idx >= 0:
        lines[idx] = lines[idx].replace(
            '"DD%": round(ms_c["max_drawdown_pct"], 1),',
            '"DD%": max(round(ms_c["max_drawdown_pct"], 1), -100.0),'
        )
        report["patches"].append("P6: Cap per-coin DD% at -100 in LSG table")

    # ====================================================================
    # PATCH 7: Add help= tooltips to key metrics
    # ====================================================================
    tooltips_applied = 0

    # Portfolio metrics (pm1-pm5)
    idx = anchor('pm2.metric("Net P&L"')
    if idx >= 0:
        lines[idx] = lines[idx].rstrip().rstrip(")")
        lines[idx] += ', help="Profit after commissions and rebates")'
        tooltips_applied += 1

    idx = anchor('pm3.metric("Max DD%"')
    if idx >= 0:
        lines[idx] = lines[idx].rstrip().rstrip(")")
        lines[idx] += ', help="Largest peak-to-trough % drop")'
        tooltips_applied += 1

    idx = anchor('pm4.metric("Peak Capital"')
    if idx >= 0:
        lines[idx] = lines[idx].rstrip().rstrip(")")
        lines[idx] += ', help="Max margin across all coins at once")'
        tooltips_applied += 1

    idx = anchor('pm5.metric("Total Trades", total_trades)')
    if idx >= 0:
        lines[idx] = lines[idx].rstrip().rstrip(")")
        lines[idx] += ', help="All trades across all coins")'
        tooltips_applied += 1

    # Capital Allocation subheader
    idx = anchor('st.subheader("Capital Allocation: Best vs Worst")')
    if idx >= 0:
        lines[idx] = lines[idx].replace(
            'st.subheader("Capital Allocation: Best vs Worst")',
            'st.subheader("Capital Allocation: Best vs Worst", help="Historical best/worst, not Monte Carlo")'
        )
        tooltips_applied += 1

    # LSG% subheader
    idx = anchor('st.subheader("LSG% Per Coin")')
    if idx >= 0:
        lines[idx] = lines[idx].replace(
            'st.subheader("LSG% Per Coin")',
            'st.subheader("LSG% Per Coin", help="% of losers that were green before SL")'
        )
        tooltips_applied += 1

    # Single mode metrics -- Net P&L
    # Find the first occurrence in single mode tab1 (r1[3])
    net_pnl_indices = find_all_anchors(lines, 'r1[3].metric("Net P&L"')
    for npi in net_pnl_indices:
        if ", help=" not in lines[npi]:
            lines[npi] = lines[npi].rstrip().rstrip(")")
            lines[npi] += ', help="Profit after commissions and rebates")'
            tooltips_applied += 1

    # Max DD% in single mode
    dd_indices = find_all_anchors(lines, 'r1[5].metric("Max DD%"')
    for ddi in dd_indices:
        if ", help=" not in lines[ddi]:
            lines[ddi] = lines[ddi].rstrip().rstrip(")")
            lines[ddi] += ', help="Largest peak-to-trough % drop")'
            tooltips_applied += 1

    # LSG in single mode
    lsg_indices = find_all_anchors(lines, 'r2[1].metric("LSG"')
    for lsi in lsg_indices:
        if ", help=" not in lines[lsi]:
            lines[lsi] = lines[lsi].rstrip().rstrip(")")
            lines[lsi] += ', help="% of losers green before SL")'
            tooltips_applied += 1

    if tooltips_applied > 0:
        report["patches"].append(f"P7: Added {tooltips_applied} help tooltips")

    # ====================================================================
    # PATCH 8: ML Filtered table -- numeric values + Styler (lines ~1193-1205)
    # ====================================================================
    idx = anchor('"All (unfiltered)": [')
    if idx >= 0:
        # Find the block: next ~10 lines contain formatted strings
        for j in range(idx, min(idx + 12, len(lines))):
            if 'f"${all_net:,.2f}"' in lines[j]:
                lines[j] = lines[j].replace('f"${all_net:,.2f}"', 'round(all_net, 2)')
            if "f\"${trades_df['net_pnl'].mean():.2f}\"" in lines[j]:
                lines[j] = lines[j].replace("f\"${trades_df['net_pnl'].mean():.2f}\"", "round(trades_df['net_pnl'].mean(), 2)")
            if 'f"${taken_net:,.2f}"' in lines[j]:
                lines[j] = lines[j].replace('f"${taken_net:,.2f}"', 'round(taken_net, 2)')
            if 'f"${taken_exp:.2f}"' in lines[j]:
                lines[j] = lines[j].replace('f"${taken_exp:.2f}"', 'round(taken_exp, 2)')

        # Find the st.dataframe line that renders this table
        # It's the line with hide_index=True right after this block
        for j in range(idx, min(idx + 15, len(lines))):
            if "hide_index=True" in lines[j] and "st.dataframe" in lines[j]:
                # Replace with Styler version
                indent_j = "                    "
                # Get the closing portion
                old = lines[j].strip()
                # Replace with styled version
                fmt_dict = '{"Net P&L": "${:,.2f}", "Avg P&L": "${:,.2f}"}'
                # Actually the column names are "All (unfiltered)" and "ML Filtered (>X%)"
                # The values are in rows, not columns, so Styler format won't work directly
                # on row labels. Just keep numeric -- Arrow won't crash now.
                break
        report["patches"].append("P8: ML Filtered table -> raw numeric values")

    # ====================================================================
    # PATCH 9: Grades table -- numeric values + Styler (lines ~793-800)
    # ====================================================================
    # Find gd.append({ in single mode (first occurrence)
    gd_indices = find_all_anchors(lines, "gd.append({")
    for gdi in gd_indices:
        for j in range(gdi, min(gdi + 10, len(lines))):
            if '"WR":' in lines[j] and 'f"' in lines[j] and ":.1%" in lines[j]:
                lines[j] = lines[j].replace('f"{s[\'win_rate\']:.1%}"', "round(s['win_rate'] * 100, 1)")
                report["patches"].append(f"P9a: Grades WR -> raw float (line {j})")
            if '"Avg":' in lines[j] and 'f"$' in lines[j]:
                lines[j] = lines[j].replace('f"${s[\'avg_pnl\']:.2f}"', "round(s['avg_pnl'], 2)")
                report["patches"].append(f"P9b: Grades Avg -> raw float (line {j})")
            if '"Total":' in lines[j] and 'f"$' in lines[j]:
                lines[j] = lines[j].replace('f"${s[\'total_pnl\']:.2f}"', "round(s['total_pnl'], 2)")
                report["patches"].append(f"P9c: Grades Total -> raw float (line {j})")

    # Find the st.dataframe(pd.DataFrame(gd) lines and add Styler
    gd_disp_indices = find_all_anchors(lines, "st.dataframe(pd.DataFrame(gd)")
    for gdi_d in gd_disp_indices:
        old_line = lines[gdi_d]
        indent_g = "            "
        lines[gdi_d] = (indent_g +
            'st.dataframe(pd.DataFrame(gd).style.format('
            '{"WR": "{:.1f}%", "Avg": "${:.2f}", "Total": "${:.2f}"}), '
            'hide_index=True)')
    if gd_disp_indices:
        report["patches"].append(f"P9d: Grades table display with Styler ({len(gd_disp_indices)} sites)")

    # ====================================================================
    # PATCH 10: TP Impact table -- numeric values (lines ~885-898)
    # ====================================================================
    idx = anchor('"No TP": [')
    if idx >= 0:
        for j in range(idx, min(idx + 15, len(lines))):
            # WR values
            if "m_notp['win_rate']:.1%" in lines[j]:
                lines[j] = lines[j].replace('f"{m_notp[\'win_rate\']:.1%}"', "round(m_notp['win_rate'] * 100, 1)")
            if "m['win_rate']:.1%" in lines[j]:
                lines[j] = lines[j].replace('f"{m[\'win_rate\']:.1%}"', "round(m['win_rate'] * 100, 1)")
            # Net values
            if 'f"${n_notp:,.2f}"' in lines[j]:
                lines[j] = lines[j].replace('f"${n_notp:,.2f}"', "round(n_notp, 2)")
            if 'f"${true_net:,.2f}"' in lines[j]:
                lines[j] = lines[j].replace('f"${true_net:,.2f}"', "round(true_net, 2)")
            # Exp values
            if 'f"${n_notp/m_notp[\'total_trades\']:.2f}"' in lines[j]:
                lines[j] = lines[j].replace(
                    'f"${n_notp/m_notp[\'total_trades\']:.2f}"',
                    "round(n_notp/m_notp['total_trades'], 2)"
                )
            if 'f"${exp:.2f}"' in lines[j]:
                lines[j] = lines[j].replace('f"${exp:.2f}"', "round(exp, 2)")
            # DD% values
            if "m_notp['max_drawdown_pct']:.1f}%" in lines[j]:
                lines[j] = lines[j].replace(
                    'f"{m_notp[\'max_drawdown_pct\']:.1f}%"',
                    "round(m_notp['max_drawdown_pct'], 1)"
                )
            if "m['max_drawdown_pct']:.1f}%" in lines[j]:
                lines[j] = lines[j].replace(
                    'f"{m[\'max_drawdown_pct\']:.1f}%"',
                    "round(m['max_drawdown_pct'], 1)"
                )
            # LSG values
            if "m_notp['pct_losers_saw_green']:.0%" in lines[j]:
                lines[j] = lines[j].replace(
                    'f"{m_notp[\'pct_losers_saw_green\']:.0%}"',
                    "round(m_notp['pct_losers_saw_green'] * 100, 0)"
                )
            if "m['pct_losers_saw_green']:.0%" in lines[j]:
                lines[j] = lines[j].replace(
                    'f"{m[\'pct_losers_saw_green\']:.0%}"',
                    "round(m['pct_losers_saw_green'] * 100, 0)"
                )
        report["patches"].append("P10: TP Impact table -> raw numeric values")

        # Find and update display line
        tp_disp_indices = find_all_anchors(lines, '"": ["Trades", "WR", "Net", "Exp", "DD%", "LSG", "Scale-Outs"]')
        for tdi in tp_disp_indices:
            # Find the st.dataframe line before this
            for j in range(max(0, tdi - 3), tdi):
                if "st.dataframe(pd.DataFrame({" in lines[j]:
                    # This is an inline dataframe. We need to find the closing and add styler.
                    # Find the closing }), line
                    for k in range(tdi, min(tdi + 15, len(lines))):
                        if "hide_index=True" in lines[k]:
                            old = lines[k]
                            indent_tp = "            "
                            lines[k] = (indent_tp +
                                '}).style.format({"No TP": "{}", '
                                'tp_col: "{}"}), hide_index=True)')
                            # Actually the complex styler won't work well here because
                            # columns are "No TP" and "TP=X ATR" which is dynamic.
                            # Just removing the string formatting is sufficient to fix Arrow.
                            # Revert to simple:
                            lines[k] = old
                            break

    # ====================================================================
    # PATCH 11: Add "df": df to sweep_detail_data (line ~1609)
    # ====================================================================
    idx = anchor('st.session_state["sweep_detail_data"] = {')
    if idx >= 0:
        # Find the closing } of this dict
        for j in range(idx, min(idx + 10, len(lines))):
            if '"symbol": detail_sym' in lines[j] or '"timeframe": timeframe' in lines[j]:
                if '"df":' not in lines[j]:
                    # Add df key before timeframe
                    if '"timeframe":' in lines[j]:
                        lines[j] = lines[j].replace(
                            '"timeframe": timeframe,',
                            '"df": df, "timeframe": timeframe,'
                        )
                        report["patches"].append("P11: Added df to sweep_detail_data")
                    elif lines[j].rstrip().endswith(","):
                        # Add on next line or same line
                        pass
                break

    # ====================================================================
    # PATCH 12: Equity curve x-axis -- use datetime if available
    # ====================================================================
    eq_scatter_indices = find_all_anchors(lines, 'fig_eq.add_trace(go.Scatter(y=eq, mode="lines"')
    for esi in eq_scatter_indices:
        old = lines[esi]
        if "x=" not in old:
            # Add x parameter with datetime
            lines[esi] = old.replace(
                "go.Scatter(y=eq,",
                'go.Scatter(x=df_sig["datetime"].values if "datetime" in df_sig.columns else None, y=eq,'
            )
            report["patches"].append(f"P12: Added datetime x-axis to equity curve (line {esi})")
    # Also fix the peak overlay line right after each equity scatter
    peak_indices = find_all_anchors(lines, "fig_eq.add_trace(go.Scatter(y=np.maximum.accumulate(eq)")
    for pi in peak_indices:
        old = lines[pi]
        if "x=" not in old:
            lines[pi] = old.replace(
                "go.Scatter(y=np.maximum.accumulate(eq),",
                'go.Scatter(x=df_sig["datetime"].values if "datetime" in df_sig.columns else None, y=np.maximum.accumulate(eq),'
            )
            report["patches"].append(f"P12b: Added datetime x-axis to peak overlay (line {pi})")

    return lines, report


def main():
    parser = argparse.ArgumentParser(description="Dashboard v3.2 build script")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no write")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] Dashboard v3.2 Build Script")
    print(f"Target: {DASHBOARD}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print()

    if not DASHBOARD.exists():
        print(f"ERROR: {DASHBOARD} not found")
        sys.exit(1)

    lines = read_file()
    original_count = len(lines)
    print(f"Original: {original_count} lines")

    patched_lines, report = apply_patches(lines)
    new_count = len(patched_lines)
    print(f"Patched: {new_count} lines")
    print()

    # Report
    print(f"Anchors found: {len(report['anchors_found'])}")
    for a in report["anchors_found"]:
        print(f"  [OK] {a}")
    print()
    if report["anchors_missing"]:
        print(f"Anchors MISSING: {len(report['anchors_missing'])}")
        for a in report["anchors_missing"]:
            print(f"  [MISSING] {a}")
        print()

    print(f"Patches applied: {len(report['patches'])}")
    for p in report["patches"]:
        print(f"  {p}")
    print()

    if args.dry_run:
        print("DRY RUN complete. No files written.")
        print(json.dumps(report, indent=2))
        return

    # Write patched file
    content = "\n".join(patched_lines)
    DASHBOARD.write_text(content, encoding="utf-8")
    print(f"Written: {DASHBOARD} ({new_count} lines)")

    # Verify syntax
    try:
        py_compile.compile(str(DASHBOARD), doraise=True)
        print("py_compile: PASS")
    except py_compile.PyCompileError as e:
        print(f"py_compile: FAIL -- {e}")
        sys.exit(1)

    print()
    print(json.dumps(report, indent=2))
    print()
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Done.")


if __name__ == "__main__":
    main()

r"""
Build Script: Dashboard v3.9 Integration
=========================================
Reads the current dashboard.py, applies 7 targeted patches to wire in
the 4 utility modules, and writes dashboard_v39.py.

Patches:
  P1: Add imports for utils modules (after backtester import)
  P2: Add capital mode toggle to sidebar (after commission section)
  P3: Add portfolio save/load UI (after coin selection, before Run button)
  P4: Apply capital constraints after align_portfolio_equity
  P4b: Add capital limit line to fig_cap before render (avoids duplicate chart)
  P5: Replace 7-column LSG table with 17-column extended metrics table + drill-down
  P6: Add PDF export button + capital efficiency display after correlation matrix

Run:
  python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_integration.py"

Hard Rules:
  - py_compile every output file
  - Timestamps on all logging
  - Docstrings on all functions
  - No escaped quotes in f-strings
  - No emojis
  - No Windows backslash paths in source strings
"""
import sys
import py_compile
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_SRC = ROOT / "scripts" / "dashboard.py"
DASHBOARD_OUT = ROOT / "scripts" / "dashboard_v39.py"


def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def read_dashboard():
    """Read original dashboard.py and return lines."""
    if not DASHBOARD_SRC.exists():
        log(f"ERROR: {DASHBOARD_SRC} not found")
        sys.exit(1)
    lines = DASHBOARD_SRC.read_text(encoding="utf-8").splitlines(keepends=True)
    log(f"Read {len(lines)} lines from dashboard.py")
    return lines


def find_line(lines, pattern, start=0):
    """Find first line matching pattern (string match). Returns index or -1."""
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return -1


def apply_patches(lines):
    """Apply all 7 patches (P1-P6 + P4b) to dashboard lines. Returns modified lines."""

    # =========================================================================
    # P1: Add imports after the backtester import (line with 'from engine.backtester_v384')
    # =========================================================================
    p1_anchor = find_line(lines, "from engine.backtester_v384 import Backtester384")
    if p1_anchor == -1:
        log("ERROR: P1 anchor not found (backtester import)")
        sys.exit(1)

    p1_insert = """\
# --- Portfolio Enhancement v3: utils modules (2026-02-16) ---
# Phase 1: Reusable portfolio save/load
# Phase 2: Extended per-coin metrics + drill-down
# Phase 3: PDF export (requires: pip install reportlab)
# Phase 4: Unified capital model with trade rejection
from utils.portfolio_manager import (
    save_portfolio, load_portfolio, list_portfolios, delete_portfolio
)
from utils.coin_analysis import (
    compute_extended_metrics, compute_grade_distribution,
    compute_exit_distribution, compute_monthly_pnl,
    compute_loser_detail, compute_commission_breakdown,
    compute_daily_volume_stats
)
from utils.capital_model import (
    apply_capital_constraints, format_capital_summary, GRADE_PRIORITY
)
from utils.pdf_exporter import check_dependencies as check_pdf_deps, generate_portfolio_pdf

"""
    lines.insert(p1_anchor + 1, p1_insert)
    log(f"P1: Inserted utils imports after line {p1_anchor + 1}")

    # =========================================================================
    # P2: Add capital mode toggle after commission section
    # Find the line with "Per side:" caption which ends the commission sidebar
    # =========================================================================
    p2_anchor = find_line(lines, 'st.sidebar.caption(f"Per side:')
    if p2_anchor == -1:
        log("ERROR: P2 anchor not found (commission caption)")
        sys.exit(1)

    p2_insert = """
# -- Capital allocation mode (Portfolio Enhancement v3, Phase 4) --
# Per-Coin Independent: each coin uses full margin (current behavior, default)
# Unified Portfolio Pool: total capital budget, rejects trades exceeding limit
st.sidebar.markdown("---")
st.sidebar.subheader("Capital Mode")
capital_mode = st.sidebar.radio(
    "Allocation Mode",
    ["Per-Coin Independent", "Unified Portfolio Pool"],
    key="capital_mode",
    help="Per-Coin: no capital limit. Unified: set total capital budget."
)
total_portfolio_capital = None
if capital_mode == "Unified Portfolio Pool":
    total_portfolio_capital = st.sidebar.number_input(
        "Total Portfolio Capital ($)",
        min_value=1000, max_value=500000, value=10000, step=1000,
        key="total_capital"
    )
    max_concurrent = int(total_portfolio_capital / margin) if margin > 0 else 0
    st.sidebar.caption(
        f"Max concurrent positions: {max_concurrent} "
        f"(at ${margin:,.0f}/pos)"
    )

"""
    lines.insert(p2_anchor + 1, p2_insert)
    log(f"P2: Inserted capital mode toggle after line {p2_anchor + 1}")

    # =========================================================================
    # P3: Add portfolio save/load UI after coin selection, before Run button
    # Find: run_port = st.button("Run Portfolio Backtest"
    # Insert save/load UI BEFORE it
    # =========================================================================
    p3_anchor = find_line(lines, 'run_port = st.button("Run Portfolio Backtest"')
    if p3_anchor == -1:
        log("ERROR: P3 anchor not found (Run Portfolio button)")
        sys.exit(1)

    p3_insert = """
    # -- Portfolio Save/Load (Phase 1) --
    st.markdown("---")
    _pf_col1, _pf_col2 = st.columns(2)
    with _pf_col1:
        _saved_list = list_portfolios()
        if _saved_list:
            _pf_names = ["(none)"] + [p["name"] + " (" + str(p["coin_count"]) + " coins)" for p in _saved_list]
            _pf_choice = st.selectbox("Load Saved Portfolio", _pf_names, key="pf_load")
            if _pf_choice != "(none)":
                _pf_idx = _pf_names.index(_pf_choice) - 1
                _pf_file = _saved_list[_pf_idx]["file"]
                _pf_data = load_portfolio(_pf_file)
                if _pf_data is not None:
                    port_symbols = [s for s in _pf_data["coins"] if s in cached]
                    _missing = [s for s in _pf_data["coins"] if s not in cached]
                    if _missing:
                        st.warning("Missing from cache: " + ", ".join(_missing[:5]))
                    st.caption("Loaded: " + _pf_data.get("notes", ""))
        else:
            st.caption("No saved portfolios yet")

    with _pf_col2:
        _save_name = st.text_input("Save current selection as", key="pf_save_name")
        _save_notes = st.text_input("Notes (optional)", key="pf_save_notes")
        if st.button("Save Portfolio", key="pf_save_btn"):
            if _save_name and port_symbols:
                _method = port_source.lower().replace(" ", "_")
                _saved_path = save_portfolio(
                    _save_name, port_symbols,
                    selection_method=_method, notes=_save_notes
                )
                st.success("Saved: " + _save_name + " (" + str(len(port_symbols)) + " coins)")
            elif not _save_name:
                st.warning("Enter a portfolio name first")
            else:
                st.warning("Select coins first")

    # -- Delete saved portfolio --
    if _saved_list:
        with st.expander("Manage Saved Portfolios"):
            for _sp in _saved_list:
                _dc1, _dc2, _dc3 = st.columns([3, 1, 1])
                _dc1.text(_sp["name"] + " | " + str(_sp["coin_count"]) + " coins | " + _sp.get("notes", ""))
                _dc2.text(_sp.get("created", "")[:10])
                if _dc3.button("Delete", key="del_" + _sp["file"]):
                    delete_portfolio(_sp["file"])
                    st.rerun()
    st.markdown("---")

"""
    lines.insert(p3_anchor, p3_insert)
    log(f"P3: Inserted portfolio save/load UI before line {p3_anchor}")

    # =========================================================================
    # P4: Apply capital constraints after align_portfolio_equity
    # Find: st.session_state["portfolio_data"] = {"pf": pf, "coin_results": coin_results}
    # Replace that line with capital constraints application
    # =========================================================================
    p4_anchor = find_line(lines, 'st.session_state["portfolio_data"] = {"pf": pf, "coin_results": coin_results}')
    if p4_anchor == -1:
        log("ERROR: P4 anchor not found (portfolio_data assignment)")
        sys.exit(1)

    # Replace the single line with capital constraints block
    p4_replacement = """\
                # Apply unified capital constraints if enabled (Phase 4)
                _cap_result = None
                if total_portfolio_capital is not None and total_portfolio_capital > 0:
                    _cap_result = apply_capital_constraints(
                        coin_results, pf, total_portfolio_capital, margin
                    )
                    pf = _cap_result["adjusted_pf"]
                    coin_results = _cap_result["adjusted_coin_results"]
                st.session_state["portfolio_data"] = {
                    "pf": pf, "coin_results": coin_results,
                    "capital_result": _cap_result,
                    "total_capital": total_portfolio_capital,
                }
"""
    lines[p4_anchor] = p4_replacement
    log(f"P4: Replaced portfolio_data assignment at line {p4_anchor}")

    # =========================================================================
    # P4b: Add capital limit line to fig_cap BEFORE it renders
    # Find: st.plotly_chart(fig_cap, use_container_width=True)
    # Insert capital limit trace before it
    # =========================================================================
    p4b_anchor = find_line(lines, "st.plotly_chart(fig_cap, use_container_width=True)")
    if p4b_anchor == -1:
        log("ERROR: P4b anchor not found (fig_cap plotly_chart)")
        sys.exit(1)

    p4b_insert = """\
        # Add capital limit line if unified mode is active
        _cap_res = st.session_state.get("portfolio_data", {}).get("capital_result")
        _tot_cap = st.session_state.get("portfolio_data", {}).get("total_capital")
        if _tot_cap is not None and _tot_cap > 0:
            fig_cap.add_trace(go.Scatter(
                x=_dt_ds,
                y=[_tot_cap] * len(_dt_ds),
                mode="lines",
                name="Capital Limit",
                line=dict(width=2, color=COLORS["red"], dash="dash")
            ))
"""
    lines.insert(p4b_anchor, p4b_insert)
    log(f"P4b: Inserted capital limit trace before fig_cap render at line {p4b_anchor}")

    # =========================================================================
    # P5: Replace LSG% table with extended metrics table + drill-down
    # Find the block from "st.subheader("LSG% Per Coin"" to "st.dataframe(lsg_df"
    # and replace with expanded table + expanders
    # =========================================================================
    p5_start = find_line(lines, 'st.subheader("LSG% Per Coin"')
    if p5_start == -1:
        log("ERROR: P5 start anchor not found (LSG% subheader)")
        sys.exit(1)

    p5_end = find_line(lines, "st.dataframe(lsg_df", p5_start)
    if p5_end == -1:
        log("ERROR: P5 end anchor not found (lsg_df dataframe)")
        sys.exit(1)

    p5_replacement = """\
        # Extended per-coin metrics table (v3.9 -- 21 columns with volume/rebate)
        st.subheader("Per-Coin Performance", help="Extended metrics with drill-down per coin")
        ext_rows = []
        for cr in coin_results:
            ms_c = cr["metrics"]
            tdf = cr.get("trades_df")
            _dt_idx_c = cr.get("datetime_index")
            _bc = len(cr["equity_curve"]) if cr.get("equity_curve") is not None else None
            ext_m = compute_extended_metrics(tdf, bar_count=_bc)
            _dvs = compute_daily_volume_stats(tdf, datetime_index=_dt_idx_c, notional=notional)
            _net = round(float(cr["equity_curve"][-1] - 10000.0), 2)
            _lsg = round(ms_c.get("pct_losers_saw_green", 0) * 100, 1)
            ext_rows.append({
                "Symbol": cr["symbol"],
                "Trades": ms_c["total_trades"],
                "WR%": round(ms_c["win_rate"] * 100, 1),
                "Net": _net,
                "Volume$": round(ms_c.get("total_volume", 0), 0),
                "Rebate$": round(ms_c.get("total_rebate", 0), 2),
                "Tr/Day": _dvs["avg_trades_per_day"],
                "MaxTr/D": _dvs["max_trades_day"],
                "LSG%": _lsg,
                "DD%": max(round(ms_c["max_drawdown_pct"], 1), -100.0),
                "Sharpe": round(ms_c["sharpe"], 3),
                "PF": round(ms_c["profit_factor"], 2),
                "Avg$": ext_m["avg_trade"],
                "Best$": ext_m["best_trade"],
                "Worst$": ext_m["worst_trade"],
                "SL%": ext_m["sl_pct"],
                "TP%": ext_m["tp_pct"],
                "MFE": round(ext_m["avg_mfe"], 4),
                "MAE": round(ext_m["avg_mae"], 4),
                "MaxLoss": ext_m["max_consec_loss"],
                "Sortino": ext_m["sortino"],
            })
        ext_df = pd.DataFrame(ext_rows).sort_values("Net", ascending=False)
        st.dataframe(ext_df, hide_index=True, use_container_width=True)

        # Per-coin drill-down expanders (Phase 2)
        st.subheader("Per-Coin Drill-Down")
        _sorted_cr = sorted(coin_results,
                            key=lambda c: float(c["equity_curve"][-1] - 10000.0),
                            reverse=True)
        for cr in _sorted_cr:
            _sym = cr["symbol"]
            _net_val = round(float(cr["equity_curve"][-1] - 10000.0), 2)
            _label = _sym + " -- $" + f"{_net_val:,.2f}"
            with st.expander(_label):
                _tdf = cr.get("trades_df")
                _dt_idx = cr.get("datetime_index")
                _dd_t1, _dd_t2, _dd_t3, _dd_t4 = st.tabs(
                    ["Trades", "Grade/Exit", "Monthly P&L", "Losers"]
                )
                with _dd_t1:
                    if _tdf is not None and not _tdf.empty:
                        _show_cols = ["direction", "grade", "entry_price", "exit_price",
                                      "pnl", "commission", "net_pnl", "mfe", "mae",
                                      "exit_reason", "saw_green"]
                        _avail = [c for c in _show_cols if c in _tdf.columns]
                        st.dataframe(_tdf[_avail].round(4), use_container_width=True, height=300)
                    else:
                        st.caption("No trades")
                with _dd_t2:
                    _gc1, _gc2 = st.columns(2)
                    with _gc1:
                        st.caption("Grade Distribution")
                        _gd = compute_grade_distribution(_tdf)
                        if _gd:
                            _gd_df = pd.DataFrame(
                                [{"Grade": k, "Count": v} for k, v in sorted(_gd.items())]
                            )
                            st.dataframe(_gd_df, hide_index=True)
                    with _gc2:
                        st.caption("Exit Reason Distribution")
                        _ed = compute_exit_distribution(_tdf)
                        if _ed:
                            _ed_df = pd.DataFrame(
                                [{"Reason": k, "Count": v} for k, v in _ed.items()]
                            )
                            st.dataframe(_ed_df, hide_index=True)
                    _comm = compute_commission_breakdown(_tdf)
                    st.caption("Total Commission: $" + f"{_comm['total_commission']:,.2f}")
                with _dd_t3:
                    _mpnl = compute_monthly_pnl(_tdf, datetime_index=_dt_idx)
                    if not _mpnl.empty:
                        st.dataframe(_mpnl.round(2), hide_index=True)
                    else:
                        st.caption("No monthly data available")
                with _dd_t4:
                    _ld = compute_loser_detail(_tdf)
                    if not _ld.empty:
                        st.caption("Losers that saw green before SL:")
                        st.dataframe(_ld.round(4), use_container_width=True, height=250)
                    else:
                        st.caption("No losers with saw_green=True")

"""
    # Replace lines from p5_start to p5_end (inclusive)
    lines[p5_start:p5_end + 1] = [p5_replacement]
    log(f"P5: Replaced LSG table (lines {p5_start}-{p5_end}) with extended metrics + drill-down")

    # =========================================================================
    # P6: Add PDF export + capital efficiency after correlation matrix
    # Find the end of correlation section and append
    # =========================================================================
    # The correlation st.dataframe call spans 2 lines:
    #   st.dataframe(corr_df.round(3).style.background_gradient(...),
    #       use_container_width=True)
    # We need to anchor on the SECOND line (the closing paren) to avoid
    # inserting inside the multi-line function call.
    p6_anchor = find_line(lines, "st.dataframe(corr_df.round(3).style.background_gradient")
    if p6_anchor == -1:
        log("ERROR: P6 anchor not found (correlation dataframe)")
        sys.exit(1)
    # Check if next line is continuation of the same call
    if p6_anchor + 1 < len(lines) and "use_container_width=True)" in lines[p6_anchor + 1]:
        p6_anchor = p6_anchor + 1  # anchor on the closing line

    p6_insert = """
        # -- Volume & Rebate Summary (v3.9) --
        st.markdown("---")
        st.subheader("Trading Volume & Rebates")
        _total_vol = sum(cr["metrics"].get("total_volume", 0) for cr in coin_results)
        _total_reb = sum(cr["metrics"].get("total_rebate", 0) for cr in coin_results)
        _total_comm = sum(cr["metrics"].get("total_commission", 0) for cr in coin_results)
        _total_sides = sum(cr["metrics"].get("total_sides", 0) for cr in coin_results)
        _net_after_reb = sum(cr["metrics"].get("net_pnl_after_rebate", 0) for cr in coin_results) - 10000.0 * len(coin_results)
        _v1, _v2, _v3 = st.columns(3)
        _v1.metric("Total Volume", f"${_total_vol:,.0f}")
        _v2.metric("Total Rebate", f"${_total_reb:,.2f}")
        _v3.metric("Net Commission", f"${_total_comm - _total_reb:,.2f}")
        _v4, _v5, _v6 = st.columns(3)
        _v4.metric("Total Sides", f"{_total_sides:,}")
        _v5.metric("Gross Commission", f"${_total_comm:,.2f}")
        _v6.metric("Net P&L (after rebate)", f"${_net_after_reb:,.2f}")
        # Daily volume stats (aggregated across all coins)
        _all_dvs = []
        for cr in coin_results:
            _dvs_c = compute_daily_volume_stats(
                cr.get("trades_df"), datetime_index=cr.get("datetime_index"),
                notional=notional
            )
            if _dvs_c["total_trading_days"] > 0:
                _all_dvs.append(_dvs_c)
        if _all_dvs:
            _agg_avg_tr = sum(d["avg_trades_per_day"] for d in _all_dvs)
            _agg_max_tr = max(d["max_trades_day"] for d in _all_dvs)
            _agg_avg_vol = sum(d["avg_volume_per_day"] for d in _all_dvs)
            _agg_max_vol = max(d["max_volume_day"] for d in _all_dvs)
            _d1, _d2, _d3, _d4 = st.columns(4)
            _d1.metric("Avg Trades/Day (all)", f"{_agg_avg_tr:.1f}")
            _d2.metric("Peak Trades/Day (any)", f"{_agg_max_tr}")
            _d3.metric("Avg Volume/Day", f"${_agg_avg_vol:,.0f}")
            _d4.metric("Peak Volume/Day", f"${_agg_max_vol:,.0f}")

        # -- Capital Efficiency Display (Phase 4) --
        _cap_data = _pd.get("capital_result")
        _total_cap = _pd.get("total_capital")
        if _cap_data is not None and _total_cap is not None:
            st.markdown("---")
            st.subheader("Capital Efficiency (Unified Mode)")
            _eff = _cap_data["capital_efficiency"]
            _ce1, _ce2, _ce3 = st.columns(3)
            _ce1.metric("Peak Capital Used",
                        f"${_eff['peak_used']:,.0f} ({_eff['peak_pct']:.1f}%)")
            _ce2.metric("Avg Capital Used",
                        f"${_eff['avg_used']:,.0f} ({_eff['avg_pct']:.1f}%)")
            _ce3.metric("Idle Capital",
                        f"{_eff['idle_pct']:.1f}%")

            _rej1, _rej2 = st.columns(2)
            _rej1.metric("Trades Rejected",
                         f"{_eff['trades_rejected']} ({_eff['rejection_pct']:.1f}%)")
            _rej2.metric("Missed P&L",
                         f"${_eff['missed_pnl']:,.2f}")

            # Rejection log
            if _cap_data["rejection_log"]:
                with st.expander("Rejected Trades (" + str(_cap_data["rejected_count"]) + ")"):
                    _rej_df = pd.DataFrame(_cap_data["rejection_log"])
                    st.dataframe(_rej_df, use_container_width=True, height=300)

            if _eff["peak_pct"] > 95:
                st.warning(
                    "Peak capital usage exceeded 95%. "
                    "Consider increasing total capital to $"
                    + f"{int(_eff['peak_used'] * 1.2):,}"
                    + " or reducing position size."
                )

        # -- PDF Export (Phase 3) --
        st.markdown("---")
        _pdf_ok, _pdf_msg = check_pdf_deps()
        if _pdf_ok:
            _pdf_name = st.text_input("PDF Report Name", value="Portfolio", key="pdf_name")
            if st.button("Export Portfolio Report as PDF", key="pdf_export_btn"):
                with st.spinner("Generating PDF report..."):
                    try:
                        _pdf_path = generate_portfolio_pdf(
                            pf, coin_results,
                            portfolio_name=_pdf_name,
                            total_capital=_total_cap
                        )
                        st.success("PDF saved: " + _pdf_path)
                        # Offer download
                        with open(_pdf_path, "rb") as _pf_file:
                            st.download_button(
                                "Download PDF",
                                data=_pf_file.read(),
                                file_name=Path(_pdf_path).name,
                                mime="application/pdf",
                                key="pdf_download"
                            )
                    except Exception as _pdf_err:
                        st.error("PDF generation failed: " + str(_pdf_err))
        else:
            st.caption("PDF export unavailable: " + _pdf_msg)

"""
    lines.insert(p6_anchor + 1, p6_insert)
    log(f"P6: Inserted PDF export + capital efficiency after line {p6_anchor}")

    return lines


def write_dashboard(lines):
    """Write modified dashboard lines to dashboard_v39.py."""
    content = "".join(lines)
    DASHBOARD_OUT.write_text(content, encoding="utf-8")
    log(f"Wrote {len(lines)} lines to {DASHBOARD_OUT.name}")


def verify_compile():
    """Run py_compile on the output file."""
    try:
        py_compile.compile(str(DASHBOARD_OUT), doraise=True)
        log(f"py_compile PASSED: {DASHBOARD_OUT.name}")
        return True
    except py_compile.PyCompileError as e:
        log(f"py_compile FAILED: {e}")
        return False


def main():
    """Main entry point for dashboard v3.9 integration build."""
    log("=" * 60)
    log("Dashboard v3.9 Build -- Portfolio + Volume/Rebate")
    log("=" * 60)

    # Verify source exists
    if not DASHBOARD_SRC.exists():
        log(f"ERROR: Source not found: {DASHBOARD_SRC}")
        sys.exit(1)

    # Check output doesn't already exist
    if DASHBOARD_OUT.exists():
        log(f"WARNING: {DASHBOARD_OUT.name} already exists, overwriting")

    # Read, patch, write
    lines = read_dashboard()
    patched = apply_patches(lines)
    write_dashboard(patched)

    # Verify compilation
    ok = verify_compile()

    log("=" * 60)
    if ok:
        log("BUILD SUCCESS")
        log(f"Output: {DASHBOARD_OUT}")
        log("")
        log("Run the new dashboard with:")
        log(f'  streamlit run "{DASHBOARD_OUT}"')
        log("")
        log("Compare with original:")
        log(f'  streamlit run "{DASHBOARD_SRC}"')
    else:
        log("BUILD FAILED -- fix py_compile errors above")
    log("=" * 60)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

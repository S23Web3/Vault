"""
Build script for Dashboard v3.1 — Date Range + Stress Test + Portfolio Mode.

Patches scripts/dashboard.py surgically at known anchor points.
Outputs structured JSON report readable by Claude.

Usage:
    python scripts/build_dashboard_v31.py --dry-run   # preview, no write
    python scripts/build_dashboard_v31.py              # apply patches
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


def apply_patches(lines):
    """Apply all v3.1 patches. Returns (patched_lines, report)."""
    report = {"anchors_found": [], "anchors_missing": [], "patches": []}

    def anchor(text):
        """Find anchor and log to report; returns index or -1."""
        idx = find_anchor(lines, text)
        if idx >= 0:
            report["anchors_found"].append(text[:60])
        else:
            report["anchors_missing"].append(text[:60])
        return idx

    # ====================================================================
    # PATCH 1: Add timedelta import (line ~35)
    # ====================================================================
    idx = anchor("from datetime import datetime, timezone")
    if idx >= 0:
        if "timedelta" not in lines[idx]:
            lines[idx] = lines[idx].replace(
                "from datetime import datetime, timezone",
                "from datetime import datetime, timezone, timedelta"
            )
            report["patches"].append("P1: Added timedelta import")
        else:
            report["patches"].append("P1: timedelta already imported (skip)")
    # Also add random import for portfolio mode
    idx_np = anchor("import numpy as np")
    if idx_np >= 0:
        if "import random" not in "\n".join(lines[:idx_np+5]):
            lines.insert(idx_np + 1, "import random")
            report["patches"].append("P1b: Added random import")

    # ====================================================================
    # PATCH 2: Add session state for portfolio (after sweep_detail_data init)
    # ====================================================================
    idx = anchor('if "sweep_detail_data" not in st.session_state:')
    if idx >= 0:
        insert_at = idx + 2  # after the st.session_state["sweep_detail_data"] = None line
        new_lines = [
            'if "portfolio_data" not in st.session_state:',
            '    st.session_state["portfolio_data"] = None',
        ]
        for i, nl in enumerate(new_lines):
            lines.insert(insert_at + i, nl)
        report["patches"].append("P2: Added portfolio_data session state")

    # ====================================================================
    # PATCH 3: Add helper functions (after compute_params_hash)
    # ====================================================================
    idx = anchor("def compute_params_hash(signal_params, bt_params, timeframe):")
    if idx >= 0:
        # Find end of compute_params_hash function (next blank line after return)
        end_idx = idx + 1
        for j in range(idx + 1, min(idx + 20, len(lines))):
            if "return hashlib" in lines[j]:
                end_idx = j + 1
                break

        helper_code = '''

def apply_date_filter(df, date_range):
    """Filter DataFrame to date range. Returns original if too few bars after filter."""
    if date_range is None or len(date_range) != 2:
        return df
    start_dt, end_dt = date_range
    start_ts = pd.Timestamp(start_dt, tz="UTC")
    end_ts = pd.Timestamp(end_dt, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    if "datetime" in df.columns:
        dt_col = pd.to_datetime(df["datetime"], utc=True)
        mask = (dt_col >= start_ts) & (dt_col <= end_ts)
        df_filtered = df[mask].reset_index(drop=True)
    elif isinstance(df.index, pd.DatetimeIndex):
        df_filtered = df[start_ts:end_ts].reset_index(drop=True)
    else:
        return df
    if len(df_filtered) < 100:
        return df
    return df_filtered


def find_worst_drawdowns(equity_curve, datetimes=None, n_windows=3, min_window_bars=50):
    """Find top-N non-overlapping max drawdown windows from equity curve."""
    eq = np.array(equity_curve, dtype=float)
    n = len(eq)
    if n < min_window_bars:
        return []
    peaks = np.maximum.accumulate(eq)
    dd_pct = np.where(peaks > 0, (eq - peaks) / peaks * 100.0, 0.0)
    mask = np.ones(n, dtype=bool)
    windows = []
    for _ in range(n_windows):
        dd_masked = dd_pct.copy()
        dd_masked[~mask] = 0.0
        if dd_masked.min() >= 0:
            break
        trough_bar = int(np.argmin(dd_masked))
        peak_bar = trough_bar
        for b in range(trough_bar - 1, -1, -1):
            if eq[b] >= peaks[trough_bar]:
                peak_bar = b
                break
        if trough_bar - peak_bar < min_window_bars:
            peak_bar = max(0, trough_bar - min_window_bars)
        start_date, end_date = "", ""
        if datetimes is not None:
            try:
                start_date = str(datetimes[peak_bar])[:10]
                end_date = str(datetimes[trough_bar])[:10]
            except (IndexError, TypeError):
                pass
        windows.append({
            "start_bar": peak_bar, "end_bar": trough_bar,
            "start_date": start_date, "end_date": end_date,
            "dd_pct": round(float(dd_pct[trough_bar]), 2),
            "peak_equity": round(float(eq[peak_bar]), 2),
            "trough_equity": round(float(eq[trough_bar]), 2),
            "duration_bars": trough_bar - peak_bar,
        })
        buffer = max(10, (trough_bar - peak_bar) // 5)
        mask[max(0, peak_bar - buffer):min(n, trough_bar + buffer + 1)] = False
    return windows


def align_portfolio_equity(coin_results, margin_per_pos=500.0, max_positions=4):
    """Align multiple coin equity curves and compute portfolio metrics."""
    if not coin_results:
        return None
    master_dt = pd.DatetimeIndex([])
    for cr in coin_results:
        master_dt = master_dt.union(pd.DatetimeIndex(cr["datetime_index"]))
    master_dt = master_dt.sort_values()
    n_bars = len(master_dt)
    portfolio_eq = np.zeros(n_bars)
    total_positions = np.zeros(n_bars)
    per_coin_eq = {}
    for cr in coin_results:
        sym = cr["symbol"]
        dt_idx = pd.DatetimeIndex(cr["datetime_index"])
        eq_series = pd.Series(cr["equity_curve"], index=dt_idx)
        eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(10000.0).values
        per_coin_eq[sym] = eq_aligned
        portfolio_eq += eq_aligned
        pos_series = pd.Series(cr["position_counts"], index=dt_idx)
        pos_aligned = pos_series.reindex(master_dt, method="ffill").fillna(0).values
        total_positions += pos_aligned
    capital_allocated = total_positions * margin_per_pos
    peaks = np.maximum.accumulate(portfolio_eq)
    dd_arr = np.where(peaks > 0, (portfolio_eq - peaks) / peaks * 100.0, 0.0)
    worst_bar = int(np.argmin(dd_arr))
    best_bar = int(np.argmax(portfolio_eq))
    def bar_info(bar_idx, label):
        """Build info dict for a specific bar (best/worst moment)."""
        dt_str = str(master_dt[bar_idx])[:19] if bar_idx < len(master_dt) else ""
        return {"label": label, "bar": bar_idx, "date": dt_str,
                "equity": round(float(portfolio_eq[bar_idx]), 2),
                "dd_pct": round(float(dd_arr[bar_idx]), 2),
                "positions": int(total_positions[bar_idx]),
                "capital": round(float(capital_allocated[bar_idx]), 2)}
    per_coin_lsg = {}
    for cr in coin_results:
        tdf = cr.get("trades_df")
        if tdf is not None and not tdf.empty:
            losers = tdf[tdf["net_pnl"] < 0]
            lsg = losers["saw_green"].sum() / len(losers) * 100.0 if len(losers) > 0 else 0.0
            per_coin_lsg[cr["symbol"]] = round(lsg, 1)
    return {"master_dt": master_dt, "portfolio_eq": portfolio_eq, "per_coin_eq": per_coin_eq,
            "total_positions": total_positions, "capital_allocated": capital_allocated,
            "best_moment": bar_info(best_bar, "Best"), "worst_moment": bar_info(worst_bar, "Worst"),
            "portfolio_dd_pct": round(float(dd_arr.min()), 2), "per_coin_lsg": per_coin_lsg}'''

        helper_lines = helper_code.split("\n")
        for i, hl in enumerate(helper_lines):
            lines.insert(end_idx + i, hl)
        report["patches"].append(f"P3: Added 3 helper functions ({len(helper_lines)} lines)")

    # ====================================================================
    # PATCH 4: Update compute_params_hash to accept date_range
    # ====================================================================
    idx = anchor("def compute_params_hash(signal_params, bt_params, timeframe):")
    if idx >= 0:
        lines[idx] = 'def compute_params_hash(signal_params, bt_params, timeframe, date_range=None):'
        # Update the payload line
        for j in range(idx, min(idx + 10, len(lines))):
            if '"s": signal_params' in lines[j] and '"tf": timeframe' in lines[j]:
                lines[j] = '    payload = json.dumps({"s": signal_params, "b": bt_params, "tf": timeframe, "dr": str(date_range)}, sort_keys=True, default=str)'
                break
        report["patches"].append("P4: Updated compute_params_hash with date_range")

    # ====================================================================
    # PATCH 5: Add date range sidebar widget (after timeframe radio)
    # ====================================================================
    idx = anchor('timeframe = st.sidebar.radio("Timeframe"')
    if idx >= 0:
        widget_code = [
            '',
            '# -- Date range filter (v3.1) --',
            'st.sidebar.markdown("---")',
            'st.sidebar.subheader("Date Range")',
            'date_preset = st.sidebar.radio("Period", ["All", "7d", "30d", "90d", "1y", "Custom"],',
            '    horizontal=True, index=0)',
            'date_range = None',
            'if date_preset == "Custom":',
            '    dr_c1, dr_c2 = st.sidebar.columns(2)',
            '    date_start = dr_c1.date_input("Start", datetime.now() - timedelta(days=90))',
            '    date_end = dr_c2.date_input("End", datetime.now())',
            '    date_range = (date_start, date_end)',
            'elif date_preset != "All":',
            '    _days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}',
            '    _n_days = _days_map[date_preset]',
            '    _de = datetime.now()',
            '    _ds = _de - timedelta(days=_n_days)',
            '    date_range = (_ds.date(), _de.date())',
            '    _dr_label = _ds.strftime("%Y-%m-%d") + " to " + _de.strftime("%Y-%m-%d")',
            '    st.sidebar.caption(_dr_label)',
        ]
        for i, wl in enumerate(widget_code):
            lines.insert(idx + 1 + i, wl)
        report["patches"].append(f"P5: Added date range sidebar ({len(widget_code)} lines)")

    # ====================================================================
    # PATCH 6: Add Portfolio button (after sweep button)
    # ====================================================================
    idx = anchor('run_sweep = st.sidebar.button("Sweep ALL coins")')
    if idx >= 0:
        portfolio_btn_code = [
            'run_portfolio = st.sidebar.button("Portfolio Analysis")',
        ]
        for i, pl in enumerate(portfolio_btn_code):
            lines.insert(idx + 1 + i, pl)
        # Add the mode setter
        idx2 = anchor('if run_sweep:')
        if idx2 >= 0:
            # Find the line after the sweep mode setter
            for j in range(idx2, min(idx2 + 5, len(lines))):
                if 'st.session_state["mode"] = "sweep"' in lines[j]:
                    insert_at = j + 1
                    setter_code = [
                        'if run_portfolio:',
                        '    st.session_state["mode"] = "portfolio"',
                        '    st.session_state["portfolio_data"] = None',
                    ]
                    for k, sl in enumerate(setter_code):
                        lines.insert(insert_at + k, sl)
                    break
        report["patches"].append("P6: Added Portfolio button + mode setter")

    # ====================================================================
    # PATCH 7: Add date filter in single mode (after load_data, before run_backtest)
    # ====================================================================
    idx = anchor('st.title(f"4P v3.8.4 -- {symbol} {timeframe}")')
    if idx >= 0:
        # Find "df = load_data(symbol, timeframe)" after this
        for j in range(idx, min(idx + 15, len(lines))):
            if "t0 = time.time()" in lines[j]:
                lines.insert(j, "        df = apply_date_filter(df, date_range)")
                break
        # Add caption
        for j in range(idx, min(idx + 3, len(lines))):
            if '4P v3.8.4 --' in lines[j]:
                lines.insert(j + 1, '    if date_range:')
                lines.insert(j + 2, '        st.caption(f"Date filter: {date_range[0]} to {date_range[1]}")')
                break
        report["patches"].append("P7: Added date filter in single mode")

    # ====================================================================
    # PATCH 8: Store raw df in single_data cache
    # ====================================================================
    idx = anchor('"symbol": symbol, "timeframe": timeframe, "elapsed":')
    if idx >= 0:
        lines[idx] = lines[idx].replace(
            '"symbol": symbol,',
            '"symbol": symbol, "df": df,'
        )
        report["patches"].append("P8: Added df to single_data cache")

    # ====================================================================
    # PATCH 9: Add stress test expander in Tab 1 (after Capital Utilization)
    # ====================================================================
    idx = anchor('cu[4].metric("Peak Margin"')
    if idx >= 0:
        stress_code = [
            '',
            '        # ── Stress Test (v3.1) ──────────────────────────────────',
            '        with st.expander("Stress Test (Worst Drawdowns)", expanded=False):',
            '            n_stress = st.slider("Drawdown windows", 1, 5, 3, key="stress_n")',
            '            dt_arr = df_sig["datetime"].values if "datetime" in df_sig.columns else None',
            '            stress_windows = find_worst_drawdowns(eq, datetimes=dt_arr, n_windows=n_stress)',
            '            if not stress_windows:',
            '                st.info("No significant drawdowns detected.")',
            '            else:',
            '                st.dataframe(pd.DataFrame(stress_windows)[',
            '                    ["start_date", "end_date", "dd_pct", "duration_bars", "peak_equity", "trough_equity"]',
            '                ].round(2), use_container_width=True, hide_index=True)',
            '                # Re-backtest on each window',
            '                _df_raw = _d.get("df")',
            '                if _df_raw is not None:',
            '                    stress_rows = []',
            '                    full_lsg = m.get("pct_losers_saw_green", 0) * 100',
            '                    for wi, sw in enumerate(stress_windows):',
            '                        _df_w = _df_raw.iloc[sw["start_bar"]:sw["end_bar"]+1].reset_index(drop=True)',
            '                        if len(_df_w) < 50:',
            '                            continue',
            '                        try:',
            '                            r_s, df_s = run_backtest(_df_w, signal_params, bt_params)',
            '                            ms_s = r_s["metrics"]',
            '                            eq_s = r_s["equity_curve"]',
            '                            net_s = float(eq_s[-1] - 10000.0) if len(eq_s) > 0 else 0',
            '                            lsg_s = ms_s.get("pct_losers_saw_green", 0) * 100',
            '                            cap_s = ms_s.get("avg_margin_used", 0)',
            '                            _wr_val = ms_s.get("win_rate", 0)',
            '                            _wr_str = f"{_wr_val:.1%}" if ms_s["total_trades"] > 0 else "-"',
            '                            stress_rows.append({',
            '                                "Window": f"DD-{wi+1}",',
            '                                "Dates": sw["start_date"] + " to " + sw["end_date"],',
            '                                "DD%": str(round(sw["dd_pct"], 1)) + "%",',
            '                                "Trades": ms_s["total_trades"],',
            '                                "WR": _wr_str,',
            '                                "Net": f"${net_s:,.2f}",',
            '                                "PF": str(round(ms_s["profit_factor"], 2)),',
            '                                "LSG%": f"{lsg_s:.1f}%",',
            '                                "Avg Capital": f"${cap_s:,.0f}",',
            '                            })',
            '                        except Exception:',
            '                            continue',
            '                    if stress_rows:',
            '                        st.subheader("Performance During Worst Drawdowns")',
            '                        st.caption(f"Full-run LSG: {full_lsg:.1f}%")',
            '                        st.dataframe(pd.DataFrame(stress_rows), use_container_width=True, hide_index=True)',
            '                        # Best vs Worst capital moments',
            '                        bc1, bc2 = st.columns(2)',
            '                        best_idx = int(np.argmax(eq))',
            '                        worst_idx = int(np.argmin(eq - np.maximum.accumulate(eq)))',
            '                        best_dt = str(dt_arr[best_idx])[:10] if dt_arr is not None else ""',
            '                        worst_dt = str(dt_arr[worst_idx])[:10] if dt_arr is not None else ""',
            '                        best_pos = int(results["position_counts"][best_idx]) if "position_counts" in results else 0',
            '                        worst_pos = int(results["position_counts"][worst_idx]) if "position_counts" in results else 0',
            '                        bc1.metric("Best Equity", f"${float(eq[best_idx]):,.2f}", f"{best_dt} | {best_pos} pos")',
            '                        bc2.metric("Worst DD Point", f"${float(eq[worst_idx]):,.2f}", f"{worst_dt} | {worst_pos} pos")',
        ]
        for i, sl in enumerate(stress_code):
            lines.insert(idx + 1 + i, sl)
        report["patches"].append(f"P9: Added stress test expander ({len(stress_code)} lines)")

    # ====================================================================
    # PATCH 10: Add date filter in sweep mode
    # ====================================================================
    idx = anchor("params_hash = compute_params_hash(signal_params, bt_params, timeframe)")
    if idx >= 0:
        lines[idx] = "    params_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)"
        report["patches"].append("P10: Updated sweep params_hash with date_range")

    # Find sweep load_data and add filter INSIDE the existing null+length guard
    idx = anchor("# Process NEXT ONE coin only (incremental")
    if idx >= 0:
        for j in range(idx, min(idx + 15, len(lines))):
            if "if df is not None and len(df) >= 200:" in lines[j]:
                lines.insert(j + 1, "                df = apply_date_filter(df, date_range)")
                break
        report["patches"].append("P10b: Added date filter in sweep loop")

    # Add date range caption in sweep
    idx = anchor('st.title(f"Sweep -- {timeframe} (v3.8.4)")')
    if idx >= 0:
        lines.insert(idx + 1, '    if date_range:')
        lines.insert(idx + 2, '        st.caption(f"Date filter: {date_range[0]} to {date_range[1]}")')
        report["patches"].append("P10c: Added date caption in sweep")

    # ====================================================================
    # PATCH 11: Add date filter in sweep_detail mode
    # ====================================================================
    idx = anchor('st.title(f"4P v3.8.4 -- {detail_sym} {timeframe}")')
    if idx >= 0:
        for j in range(idx, min(idx + 15, len(lines))):
            if "results, df_sig = run_backtest(df, signal_params, bt_params)" in lines[j]:
                # Check this is the sweep_detail one (has detail_sym nearby)
                context = "\n".join(lines[max(0, j-5):j])
                if "detail_sym" in context:
                    lines.insert(j, "        df = apply_date_filter(df, date_range)")
                    break
        report["patches"].append("P11: Added date filter in sweep_detail mode")

    # ====================================================================
    # PATCH 12: Add Portfolio mode (at end of file)
    # ====================================================================
    # Find the last elif (sweep_detail) and add portfolio after its block
    portfolio_code = [
        '',
        '# ── PORTFOLIO MODE (v3.1) ─────────────────────────────────────────────────',
        'elif mode == "portfolio":',
        '    if st.button("Back to Settings"):',
        '        st.session_state["mode"] = "settings"',
        '        st.session_state["portfolio_data"] = None',
        '        st.rerun()',
        '',
        '    st.title("Portfolio Analysis (v3.1)")',
        '    if date_range:',
        '        st.caption(f"Date filter: {date_range[0]} to {date_range[1]}")',
        '',
        '    # Coin selection',
        '    port_source = st.radio("Coin Selection", ["Top N", "Lowest N", "Random N", "Custom"],',
        '        horizontal=True, key="port_source")',
        '    port_n = st.slider("N coins", 2, 50, 10, key="port_n")',
        '',
        '    # Load sweep results for Top/Lowest N',
        '    sweep_csv_results = []',
        '    if SWEEP_PROGRESS.exists():',
        '        try:',
        '            _sdf = pd.read_csv(SWEEP_PROGRESS)',
        '            if not _sdf.empty and "Exp" in _sdf.columns:',
        '                sweep_csv_results = _sdf.sort_values("Exp", ascending=False)["Symbol"].tolist()',
        '        except Exception:',
        '            pass',
        '',
        '    if port_source == "Top N":',
        '        if sweep_csv_results:',
        '            port_symbols = sweep_csv_results[:port_n]',
        '        else:',
        '            st.warning("No sweep results found. Run a sweep first or choose another selection.")',
        '            port_symbols = []',
        '    elif port_source == "Lowest N":',
        '        if sweep_csv_results:',
        '            port_symbols = sweep_csv_results[-port_n:]',
        '        else:',
        '            st.warning("No sweep results found. Run a sweep first.")',
        '            port_symbols = []',
        '    elif port_source == "Random N":',
        '        port_symbols = random.sample(list(cached), min(port_n, len(cached)))',
        '    else:  # Custom',
        '        port_symbols = st.multiselect("Select coins", cached, default=cached[:min(5, len(cached))])',
        '',
        '    if port_symbols:',
        '        _syms_str = ", ".join(port_symbols[:5]) + (", ..." if len(port_symbols) > 5 else "")',
        '        st.caption(f"Portfolio: {len(port_symbols)} coins -- {_syms_str}")',
        '',
        '    run_port = st.button("Run Portfolio Backtest", disabled=len(port_symbols) == 0)',
        '',
        '    if run_port and port_symbols:',
        '        coin_results = []',
        '        progress = st.progress(0)',
        '        status = st.empty()',
        '        for ci, sym in enumerate(port_symbols):',
        '            status.text(f"[{ci+1}/{len(port_symbols)}] {sym}...")',
        '            progress.progress((ci + 1) / len(port_symbols))',
        '            try:',
        '                _df = load_data(sym, timeframe)',
        '                if _df is None or len(_df) < 200:',
        '                    continue',
        '                _df = apply_date_filter(_df, date_range)',
        '                if len(_df) < 200:',
        '                    continue',
        '                _r, _ds = run_backtest(_df, signal_params, bt_params)',
        '                if _r["metrics"]["total_trades"] == 0:',
        '                    continue',
        '                dt_idx = _ds["datetime"] if "datetime" in _ds.columns else pd.RangeIndex(len(_r["equity_curve"]))',
        '                coin_results.append({',
        '                    "symbol": sym,',
        '                    "equity_curve": _r["equity_curve"],',
        '                    "datetime_index": dt_idx,',
        '                    "position_counts": _r["position_counts"],',
        '                    "trades_df": _r["trades_df"],',
        '                    "metrics": _r["metrics"],',
        '                })',
        '            except Exception:',
        '                continue',
        '        status.text(f"Done: {len(coin_results)}/{len(port_symbols)} coins with trades")',
        '',
        '        if coin_results:',
        '            pf = align_portfolio_equity(coin_results, margin_per_pos=margin, max_positions=max_positions)',
        '            st.session_state["portfolio_data"] = {"pf": pf, "coin_results": coin_results}',
        '',
        '    _pd = st.session_state.get("portfolio_data")',
        '    if _pd is not None:',
        '        pf = _pd["pf"]',
        '        coin_results = _pd["coin_results"]',
        '',
        '        # Summary metrics',
        '        st.subheader("Portfolio Summary")',
        '        pm1, pm2, pm3, pm4, pm5 = st.columns(5)',
        '        port_net = float(pf["portfolio_eq"][-1] - 10000.0 * len(coin_results))',
        '        pm1.metric("Coins", len(coin_results))',
        '        pm2.metric("Net P&L", f"${port_net:,.2f}")',
        '        _dd_pct = pf["portfolio_dd_pct"]',
        '        pm3.metric("Max DD%", f"{_dd_pct:.1f}%")',
        '        _peak_cap = float(pf["capital_allocated"].max())',
        '        pm4.metric("Peak Capital", f"${_peak_cap:,.0f}")',
        '        total_trades = sum(cr["metrics"]["total_trades"] for cr in coin_results)',
        '        pm5.metric("Total Trades", total_trades)',
        '',
        '        # Best vs Worst capital moments',
        '        st.subheader("Capital Allocation: Best vs Worst")',
        '        bw1, bw2 = st.columns(2)',
        '        best = pf["best_moment"]',
        '        worst = pf["worst_moment"]',
        '        _best_eq = best["equity"]',
        '        _best_cap = best["capital"]',
        '        _best_info = str(best["date"]) + " | " + str(best["positions"]) + " positions | $" + f"{_best_cap:,.0f}" + " capital"',
        '        bw1.metric("Best Equity", f"${_best_eq:,.2f}", _best_info)',
        '        _worst_dd = worst["dd_pct"]',
        '        _worst_cap = worst["capital"]',
        '        _worst_info = str(worst["date"]) + " | " + str(worst["positions"]) + " positions | $" + f"{_worst_cap:,.0f}" + " capital"',
        '        bw2.metric("Worst DD", f"{_worst_dd:.1f}%", _worst_info)',
        '',
        '        # LSG before/after',
        '        st.subheader("LSG% Per Coin")',
        '        lsg_rows = []',
        '        for cr in coin_results:',
        '            ms_c = cr["metrics"]',
        '            lsg_rows.append({',
        '                "Symbol": cr["symbol"],',
        '                "Trades": ms_c["total_trades"],',
        '                "WR%": round(ms_c["win_rate"] * 100, 1),',
        '                "Net": round(float(cr["equity_curve"][-1] - 10000.0), 2),',
        '                "LSG%": round(ms_c.get("pct_losers_saw_green", 0) * 100, 1),',
        '                "DD%": round(ms_c["max_drawdown_pct"], 1),',
        '                "Sharpe": round(ms_c["sharpe"], 3),',
        '                "PF": round(ms_c["profit_factor"], 2),',
        '            })',
        '        lsg_df = pd.DataFrame(lsg_rows).sort_values("Net", ascending=False)',
        '        st.dataframe(lsg_df, use_container_width=True, hide_index=True)',
        '',
        '        # Portfolio equity curve',
        '        st.subheader("Portfolio Equity Curve")',
        '        fig_port = go.Figure()',
        '        # Per-coin thin lines',
        '        for sym, eq_arr in pf["per_coin_eq"].items():',
        '            fig_port.add_trace(go.Scatter(',
        '                x=pf["master_dt"], y=eq_arr, mode="lines",',
        '                name=sym, line=dict(width=1), opacity=0.4))',
        '        # Portfolio bold line',
        '        fig_port.add_trace(go.Scatter(',
        '            x=pf["master_dt"], y=pf["portfolio_eq"], mode="lines",',
        '            name="PORTFOLIO", line=dict(width=3, color=COLORS["green"])))',
        '        fig_port.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],',
        '            plot_bgcolor=COLORS["card"], height=500, margin=dict(l=40, r=20, t=20, b=40))',
        '        st.plotly_chart(fig_port, use_container_width=True)',
        '',
        '        # Capital utilization over time',
        '        st.subheader("Capital Utilization Over Time")',
        '        fig_cap = go.Figure()',
        '        fig_cap.add_trace(go.Scatter(',
        '            x=pf["master_dt"], y=pf["capital_allocated"], mode="lines",',
        '            fill="tozeroy", name="Capital Allocated",',
        '            line=dict(color=COLORS["blue"])))',
        '        fig_cap.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],',
        '            plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),',
        '            yaxis_title="$ Capital")',
        '        st.plotly_chart(fig_cap, use_container_width=True)',
        '',
        '        # Correlation matrix',
        '        if len(pf["per_coin_eq"]) >= 2:',
        '            st.subheader("Equity Change Correlation")',
        '            changes = {}',
        '            for sym, eq_arr in pf["per_coin_eq"].items():',
        '                changes[sym] = np.diff(eq_arr)',
        '            corr_df = pd.DataFrame(changes).corr()',
        '            st.dataframe(corr_df.round(3).style.background_gradient(cmap="RdYlGn_r", vmin=-1, vmax=1),',
        '                use_container_width=True)',
    ]
    lines.extend(portfolio_code)
    report["patches"].append(f"P12: Added portfolio mode ({len(portfolio_code)} lines)")

    return lines, report


def main():
    """Entry point: parse args, apply patches, output JSON report."""
    parser = argparse.ArgumentParser(description="Build Dashboard v3.1 patches")
    parser.add_argument("--dry-run", action="store_true", help="Preview patches without writing")
    args = parser.parse_args()

    if not DASHBOARD.exists():
        print(json.dumps({"error": f"Dashboard not found: {DASHBOARD}"}, indent=2))
        sys.exit(1)

    content = DASHBOARD.read_text(encoding="utf-8")
    lines = content.split("\n")
    lines_before = len(lines)

    patched_lines, report = apply_patches(lines)
    lines_after = len(patched_lines)

    report["lines_before"] = lines_before
    report["lines_after"] = lines_after
    report["dry_run"] = args.dry_run
    report["patches_applied"] = len(report["patches"])
    report["timestamp"] = datetime.now(timezone.utc).isoformat()

    if not args.dry_run:
        DASHBOARD.write_text("\n".join(patched_lines), encoding="utf-8")
        try:
            py_compile.compile(str(DASHBOARD), doraise=True)
            report["py_compile"] = "PASS"
        except py_compile.PyCompileError as e:
            report["py_compile"] = f"FAIL: {e}"
        report["status"] = "APPLIED"
    else:
        report["status"] = "DRY_RUN"

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

r"""
Build script: Capital Mode Consistency Fix

Fixes 7 data consistency bugs in Shared Pool mode where metrics, trades_df,
and volume/rebate calculations still used unconstrained (pre-rejection) data.

CHANGES:
  1. capital_model.py: filter trades_df to accepted-only, rebuild metrics dict
  2. dashboard_v39.py: fix Total Trades metric (metrics now reflect accepted counts)

Per-Coin Independent mode: UNCHANGED (no rejections, no filtering).

Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_capital_mode_fix.py"
"""

import shutil
import sys
import py_compile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CAP_MODEL = ROOT / "utils" / "capital_model.py"
DASHBOARD = ROOT / "scripts" / "dashboard_v39.py"
CAP_BACKUP = ROOT / "utils" / "capital_model_pre_capfix.py.backup"
DASH_BACKUP = ROOT / "scripts" / "dashboard_v39_pre_capfix.py.backup"

ERRORS = []
PASS_COUNT = 0


def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def check(name, condition):
    """Assert a condition and track pass/fail."""
    global PASS_COUNT
    ts = datetime.now().strftime("%H:%M:%S")
    if condition:
        PASS_COUNT += 1
        print(f"[{ts}] PASS: {name}")
    else:
        ERRORS.append(name)
        print(f"[{ts}] FAIL: {name}")


def patch_capital_model():
    """Patch capital_model.py to filter trades_df and rebuild metrics."""
    log("=== PATCH GROUP 1: capital_model.py ===")

    if not CAP_MODEL.exists():
        log(f"FATAL: {CAP_MODEL} not found")
        sys.exit(1)

    if not CAP_BACKUP.exists():
        shutil.copy2(CAP_MODEL, CAP_BACKUP)
        log(f"Backup: {CAP_BACKUP}")
    else:
        log(f"Backup already exists: {CAP_BACKUP}")

    src = CAP_MODEL.read_text(encoding="utf-8")
    orig_len = len(src)

    # ---- PATCH CM1: Add _rebuild_metrics_from_df function ----
    log("--- CM1: Add _rebuild_metrics_from_df helper ---")

    old_cm1 = 'def apply_capital_constraints(coin_results, pf_data, total_capital, margin_per_pos):'

    new_cm1 = '''def _rebuild_metrics_from_df(tdf, eq_curve, orig_metrics, notional):
    """Rebuild key metrics dict fields from a filtered trades DataFrame."""
    if tdf is None or tdf.empty:
        m = dict(orig_metrics)
        m["total_trades"] = 0
        m["win_count"] = 0
        m["loss_count"] = 0
        m["win_rate"] = 0
        m["net_pnl"] = 0
        m["total_commission"] = 0
        m["total_volume"] = 0
        m["total_sides"] = 0
        m["total_rebate"] = 0
        m["net_pnl_after_rebate"] = 0
        m["sharpe"] = 0
        m["sortino"] = 0
        m["profit_factor"] = 0
        m["max_drawdown_pct"] = 0
        m["pct_losers_saw_green"] = 0
        return m

    net_col = "net_pnl" if "net_pnl" in tdf.columns else "pnl"
    pnls = tdf[net_col].values.astype(float)
    commissions = tdf["commission"].values.astype(float) if "commission" in tdf.columns else np.zeros(len(tdf))

    total = len(tdf)
    winners = pnls[pnls > 0]
    losers = pnls[pnls <= 0]
    win_count = len(winners)
    loss_count = len(losers)
    win_rate = win_count / total if total > 0 else 0

    gross_profit = float(np.sum(winners)) if len(winners) > 0 else 0
    gross_loss = float(np.abs(np.sum(losers))) if len(losers) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Sharpe / Sortino
    if len(pnls) > 1 and np.std(pnls) > 0:
        sharpe = float(np.mean(pnls) / np.std(pnls))
        downside = pnls[pnls < 0]
        ds_std = float(np.std(downside)) if len(downside) > 1 else 1.0
        sortino = float(np.mean(pnls) / ds_std) if ds_std > 0 else 0
    else:
        sharpe = 0
        sortino = 0

    # Max drawdown from equity curve
    max_dd_pct = 0
    if eq_curve is not None and len(eq_curve) > 0:
        peak = np.maximum.accumulate(eq_curve)
        dd_pct_arr = np.where(peak > 0, (peak - eq_curve) / peak * 100, 0)
        max_dd_pct = float(np.max(dd_pct_arr))

    # LSG
    total_losers = loss_count
    saw_green_losers = 0
    if "saw_green" in tdf.columns:
        loser_mask = pnls <= 0
        sg_col = tdf["saw_green"].values
        saw_green_losers = int(np.sum(sg_col[loser_mask]))
    pct_lsg = saw_green_losers / total_losers if total_losers > 0 else 0

    # Volume/rebate: scale proportionally from original
    accepted_comm = float(np.sum(commissions))
    orig_comm = orig_metrics.get("total_commission", 0)
    if orig_comm > 0:
        comm_ratio = accepted_comm / orig_comm
    else:
        comm_ratio = 1.0
    total_rebate = orig_metrics.get("total_rebate", 0) * comm_ratio
    total_volume = total * notional * 2  # each trade = 2 sides
    total_sides = total * 2

    m = dict(orig_metrics)
    m["total_trades"] = total
    m["win_count"] = win_count
    m["loss_count"] = loss_count
    m["win_rate"] = win_rate
    m["net_pnl"] = float(np.sum(pnls))
    m["total_commission"] = accepted_comm
    m["total_volume"] = total_volume
    m["total_sides"] = total_sides
    m["total_rebate"] = total_rebate
    m["net_pnl_after_rebate"] = float(np.sum(pnls)) + total_rebate
    m["sharpe"] = sharpe
    m["sortino"] = sortino
    m["profit_factor"] = profit_factor
    m["max_drawdown_pct"] = max_dd_pct
    m["pct_losers_saw_green"] = pct_lsg
    m["gross_profit"] = gross_profit
    m["gross_loss"] = gross_loss
    return m


def apply_capital_constraints(coin_results, pf_data, total_capital, margin_per_pos):'''

    check("CM1: anchor found", old_cm1 in src)
    src = src.replace(old_cm1, new_cm1, 1)
    check("CM1: helper inserted", "_rebuild_metrics_from_df" in src)

    # ---- PATCH CM2: Update function signature to accept notional ----
    log("--- CM2: Add notional parameter to apply_capital_constraints ---")

    old_cm2 = 'def apply_capital_constraints(coin_results, pf_data, total_capital, margin_per_pos):\n    """\n    Post-process portfolio results to enforce unified capital constraints.\n    Filters out trades that would exceed total_capital.\n    Rebuilds equity curves and capital metrics from accepted trades only.\n    Returns dict with adjusted results and rejection log.\n    """'

    new_cm2 = 'def apply_capital_constraints(coin_results, pf_data, total_capital, margin_per_pos, notional=None):\n    """\n    Post-process portfolio results to enforce unified capital constraints.\n    Filters out trades that would exceed total_capital.\n    Rebuilds equity curves, trades_df, and metrics from accepted trades only.\n    Returns dict with adjusted results and rejection log.\n    """\n    if notional is None:\n        notional = margin_per_pos * 10  # fallback: assume 10x leverage'

    check("CM2: signature anchor found", old_cm2 in src)
    src = src.replace(old_cm2, new_cm2, 1)
    check("CM2: notional param added", "notional=None" in src)

    # ---- PATCH CM3: Filter trades_df and rebuild metrics in adjusted coin results ----
    log("--- CM3: Filter trades_df and rebuild metrics ---")

    old_cm3 = '''        # Build adjusted coin result
        adj_cr = dict(cr)
        adj_cr["equity_curve"] = eq_aligned if rejected_idxs else cr["equity_curve"]
        adjusted_coin_results.append(adj_cr)'''

    new_cm3 = '''        # Build adjusted coin result with filtered trades_df and rebuilt metrics
        adj_cr = dict(cr)
        adj_cr["equity_curve"] = eq_aligned if rejected_idxs else cr["equity_curve"]
        if rejected_idxs and tdf is not None and not tdf.empty:
            # Filter trades_df to accepted-only
            adj_tdf = tdf.drop(index=[i for i in rejected_idxs if i in tdf.index])
            adj_cr["trades_df"] = adj_tdf.reset_index(drop=True)
            # Rebuild metrics from accepted trades
            adj_cr["metrics"] = _rebuild_metrics_from_df(
                adj_cr["trades_df"], adj_cr["equity_curve"],
                cr["metrics"], notional
            )
        adjusted_coin_results.append(adj_cr)'''

    check("CM3: build adj_cr anchor found", old_cm3 in src)
    src = src.replace(old_cm3, new_cm3, 1)
    check("CM3: trades_df filtering added", "adj_tdf = tdf.drop" in src)

    # ---- PATCH CM4: Add reject_by_coin to return dict ----
    log("--- CM4: Add reject_by_coin to return dict ---")

    old_cm4 = '        "missed_pnl": round(missed_pnl, 2),\n        "capital_efficiency": {'

    new_cm4 = '        "missed_pnl": round(missed_pnl, 2),\n        "reject_by_coin": reject_by_coin,\n        "capital_efficiency": {'

    check("CM4: return dict anchor found", old_cm4 in src)
    src = src.replace(old_cm4, new_cm4, 1)
    check("CM4: reject_by_coin added", '"reject_by_coin": reject_by_coin' in src)

    # Write and compile
    log("--- Writing capital_model.py ---")
    CAP_MODEL.write_text(src, encoding="utf-8")
    check("CM write: file written", CAP_MODEL.exists())
    new_len = len(CAP_MODEL.read_text(encoding="utf-8"))
    log(f"Size: {orig_len} -> {new_len} (delta: {new_len - orig_len:+d})")

    try:
        py_compile.compile(str(CAP_MODEL), doraise=True)
        check("CM py_compile", True)
    except py_compile.PyCompileError as e:
        check("CM py_compile: " + str(e), False)


def patch_dashboard():
    """Patch dashboard_v39.py for capital mode consistency."""
    log("=== PATCH GROUP 2: dashboard_v39.py ===")

    if not DASHBOARD.exists():
        log(f"FATAL: {DASHBOARD} not found")
        sys.exit(1)

    if not DASH_BACKUP.exists():
        shutil.copy2(DASHBOARD, DASH_BACKUP)
        log(f"Backup: {DASH_BACKUP}")
    else:
        log(f"Backup already exists: {DASH_BACKUP}")

    src = DASHBOARD.read_text(encoding="utf-8")
    orig_len = len(src)

    # ---- PATCH D1: Pass notional to apply_capital_constraints ----
    log("--- D1: Pass notional to apply_capital_constraints ---")

    old_d1 = '                    _cap_result = apply_capital_constraints(\n                        coin_results, pf, total_portfolio_capital, margin\n                    )'

    new_d1 = '                    _cap_result = apply_capital_constraints(\n                        coin_results, pf, total_portfolio_capital, margin,\n                        notional=notional\n                    )'

    check("D1: apply_capital_constraints call anchor found", old_d1 in src)
    src = src.replace(old_d1, new_d1, 1)
    check("D1: notional param passed", "notional=notional" in src)

    # ---- PATCH D2: Fix Total Trades metric ----
    # After capital_model now rebuilds metrics with accepted-only counts,
    # we no longer need the manual subtraction hack.
    log("--- D2: Fix Total Trades metric for shared pool mode ---")

    old_d2 = '''        _cap_data_for_trades = _pd.get("capital_result")
        if _cap_data_for_trades is not None:
            _accepted_trades = sum(cr["metrics"]["total_trades"] for cr in coin_results) - _cap_data_for_trades["rejected_count"]
            _rejected_trades = _cap_data_for_trades["rejected_count"]
            pm5.metric("Trades", f"{_accepted_trades}",
                f"{_rejected_trades} rejected",
                help="Accepted trades (rejected = insufficient capital)")
        else:
            total_trades = sum(cr["metrics"]["total_trades"] for cr in coin_results)
            pm5.metric("Total Trades", total_trades, help="All trades across all coins")'''

    new_d2 = '''        _cap_data_for_trades = _pd.get("capital_result")
        _total_trades_sum = sum(cr["metrics"]["total_trades"] for cr in coin_results)
        if _cap_data_for_trades is not None:
            _rejected_trades = _cap_data_for_trades["rejected_count"]
            pm5.metric("Trades", f"{_total_trades_sum}",
                f"{_rejected_trades} rejected",
                help="Accepted trades (rejected = insufficient capital)")
        else:
            pm5.metric("Total Trades", _total_trades_sum, help="All trades across all coins")'''

    check("D2: total trades anchor found", old_d2 in src)
    src = src.replace(old_d2, new_d2, 1)
    check("D2: total trades patched", "_total_trades_sum" in src)

    # ---- PATCH D3: Fix Net P&L after rebate in volume section ----
    # After capital_model rebuilds metrics, net_pnl_after_rebate is already
    # correct for accepted trades. But the subtraction of _eq_per_coin * len(coin_results)
    # is wrong -- net_pnl_after_rebate in metrics is already net (not equity-based).
    # It's the sum of (pnl - commission) + rebate for all trades.
    # The baseline subtraction converts absolute equity to net. But net_pnl_after_rebate
    # is already net. Let me verify...
    # Looking at backtester: net_pnl_after_rebate = metrics["net_pnl"] + total_rebate
    # where net_pnl = sum of (pnl - commission) = equity_final - equity_start
    # So net_pnl_after_rebate is already NET. The _eq_per_coin subtraction is WRONG.
    # Wait -- but the original code has this pattern everywhere. Let me check:
    # Line 2158: sum(net_pnl_after_rebate) - _eq_per_coin * len(coin_results)
    # If each coin's metrics["net_pnl"] = equity[-1] - 10000 (the net change)
    # then net_pnl_after_rebate = (equity[-1] - 10000) + rebate
    # and the sum across coins already gives the portfolio net.
    # So subtracting _eq_per_coin * len again would be DOUBLE subtraction!
    #
    # Actually wait -- let me re-read the backtester:
    # metrics["net_pnl"] = sum of per-trade net_pnl values = final_equity - initial_equity
    # So metrics["net_pnl"] is ALREADY the net change from $10k.
    # And net_pnl_after_rebate = net_pnl + total_rebate.
    # So sum(net_pnl_after_rebate) across coins is the total portfolio net + rebates.
    # Subtracting _eq_per_coin * len(coin_results) is DOUBLE SUBTRACTING the baseline!
    #
    # But the original code was: sum(cr["metrics"].get("net_pnl_after_rebate", 0)) - _eq_per_coin * len
    # This suggests net_pnl_after_rebate might include the baseline...
    # Let me check: if final equity = $10,500 for one coin:
    #   net_pnl = sum(trade_pnls) = $500
    #   net_pnl_after_rebate = $500 + $20 (rebate) = $520
    # Then sum across 3 coins: $520 + $300 + $400 = $1220
    # Subtracting 10000 * 3 = -$28,780 (WRONG!)
    #
    # So the original line 2158 was ALREADY WRONG before my changes.
    # Let me just fix it to not subtract the baseline.
    log("--- D3: Fix Net P&L after rebate double-subtraction ---")

    old_d3 = '        _net_after_reb = sum(cr["metrics"].get("net_pnl_after_rebate", 0) for cr in coin_results) - _eq_per_coin * len(coin_results)'

    new_d3 = '        _net_after_reb = sum(cr["metrics"].get("net_pnl_after_rebate", 0) for cr in coin_results)'

    check("D3: net after rebate anchor found", old_d3 in src)
    src = src.replace(old_d3, new_d3, 1)
    check("D3: baseline subtraction removed", old_d3 not in src)

    # ---- PATCH D4: Store params hash when Run is clicked ----
    log("--- D4: Store params hash with portfolio results ---")

    old_d4 = '''                st.session_state["portfolio_data"] = {
                    "pf": pf, "coin_results": coin_results,
                    "capital_result": _cap_result,
                    "total_capital": total_portfolio_capital,
                }'''

    new_d4 = '''                _port_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)
                st.session_state["portfolio_data"] = {
                    "pf": pf, "coin_results": coin_results,
                    "capital_result": _cap_result,
                    "total_capital": total_portfolio_capital,
                    "params_hash": _port_hash,
                    "margin": margin,
                    "notional": notional,
                }'''

    check("D4: session state save anchor found", old_d4 in src)
    src = src.replace(old_d4, new_d4, 1)
    check("D4: params_hash stored", '"params_hash": _port_hash' in src)

    # ---- PATCH D5: Warn if sidebar params changed since last run ----
    log("--- D5: Warn if params changed since last run ---")

    old_d5 = '''    _pd = st.session_state.get("portfolio_data")
    if _pd is not None:
        pf = _pd["pf"]
        coin_results = _pd["coin_results"]'''

    new_d5 = '''    _pd = st.session_state.get("portfolio_data")
    if _pd is not None:
        _current_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)
        _stored_hash = _pd.get("params_hash")
        _cap_changed = (total_portfolio_capital != _pd.get("total_capital"))
        _margin_changed = (margin != _pd.get("margin", margin))
        if _stored_hash and (_current_hash != _stored_hash or _cap_changed or _margin_changed):
            st.warning("Sidebar settings changed since last run. Click **Run Portfolio Backtest** to update results.")
        pf = _pd["pf"]
        coin_results = _pd["coin_results"]'''

    check("D5: display anchor found", old_d5 in src)
    src = src.replace(old_d5, new_d5, 1)
    check("D5: params change warning added", "_current_hash" in src)

    # ---- PATCH D6: Use stored margin/notional for display, not live sidebar ----
    # After running, results are computed with specific margin/notional values.
    # If user changes sidebar, display should use the values from the run.
    log("--- D6: Use stored margin/notional for portfolio display ---")

    old_d6 = '''        pf = _pd["pf"]
        coin_results = _pd["coin_results"]
        _eq_per_coin = 10000.0  # engine always runs at $10k/coin'''

    new_d6 = '''        pf = _pd["pf"]
        coin_results = _pd["coin_results"]
        # Use stored margin/notional from the run, not live sidebar values
        margin = _pd.get("margin", margin)
        notional = _pd.get("notional", notional)
        _eq_per_coin = 10000.0  # engine always runs at $10k/coin'''

    check("D6: pf/coin_results anchor found", old_d6 in src)
    src = src.replace(old_d6, new_d6, 1)
    check("D6: stored margin/notional used", '_pd.get("margin", margin)' in src)

    # Write and compile
    log("--- Writing dashboard_v39.py ---")
    DASHBOARD.write_text(src, encoding="utf-8")
    check("D write: file written", DASHBOARD.exists())
    new_len = len(DASHBOARD.read_text(encoding="utf-8"))
    log(f"Size: {orig_len} -> {new_len} (delta: {new_len - orig_len:+d})")

    try:
        py_compile.compile(str(DASHBOARD), doraise=True)
        check("D py_compile", True)
    except py_compile.PyCompileError as e:
        check("D py_compile: " + str(e), False)


def main():
    """Apply capital mode consistency fixes to capital_model.py and dashboard_v39.py."""
    log("=" * 60)
    log("Capital Mode Consistency Fix")
    log("=" * 60)

    patch_capital_model()
    log("")
    patch_dashboard()

    log("")
    log("=" * 60)
    total = PASS_COUNT + len(ERRORS)
    log(f"RESULTS: {PASS_COUNT}/{total} passed")
    if ERRORS:
        log("FAILURES: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        log("ALL PATCHES APPLIED SUCCESSFULLY")
        log("")
        log("Changes:")
        log("  capital_model.py:")
        log("    - Added _rebuild_metrics_from_df() helper")
        log("    - apply_capital_constraints() now accepts notional param")
        log("    - Adjusted coin results have filtered trades_df (accepted only)")
        log("    - Adjusted coin results have rebuilt metrics (accepted only)")
        log("    - reject_by_coin added to return dict")
        log("  dashboard_v39.py:")
        log("    - Passes notional to apply_capital_constraints()")
        log("    - Total Trades uses metrics directly (no manual subtraction)")
        log("    - Net P&L after rebate: removed double baseline subtraction")
        log("    - Stores params hash with results, warns if sidebar changed")
        log("")
        log("Effect on Shared Pool mode:")
        log("  - Per-coin table: Trades, WR%, Volume, Rebate, Sharpe, PF etc = accepted only")
        log("  - Drill-down tabs: trades_df shows accepted trades only")
        log("  - Volume/Rebate section: sums from accepted-only metrics")
        log("  - Daily volume stats: computed from accepted-only trades_df")
        log("")
        log("Sidebar change detection:")
        log("  - Changing margin, SL/TP, commission, leverage, etc shows warning")
        log("  - User must click Run to update results with new settings")
        log("  - Display uses stored margin/notional from run, not live sidebar")
        log("")
        log("Per-Coin Independent mode: UNCHANGED (no rejections)")
        log("")
        log("Backups:")
        log(f"  {CAP_BACKUP}")
        log(f"  {DASH_BACKUP}")


if __name__ == "__main__":
    main()

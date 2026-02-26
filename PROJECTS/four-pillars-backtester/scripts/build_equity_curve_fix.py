r"""
Build script: Shared Pool Equity Curve Fix

Problem: In Shared Pool mode, the equity curve chart shows engine-based
per-coin curves (each starting at $10k, summed to $110k for 11 coins).
This is meaningless -- the user deposited $10k and the curve should
show how that $10k pool balance changes over time.

Fix:
  1. capital_model.py: Build pool_equity_curve (bar-by-bar pool balance)
     and include in return dict + adjusted_pf
  2. dashboard_v39.py: In Shared Pool mode, plot pool equity curve
     instead of summed engine curves. Show per-coin P&L contribution
     lines instead of per-coin absolute equity.

Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_equity_curve_fix.py"
"""

import shutil
import sys
import py_compile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CAP_MODEL = ROOT / "utils" / "capital_model.py"
DASHBOARD = ROOT / "scripts" / "dashboard_v39.py"

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
    """Add pool_equity_curve to capital_model.py."""
    log("=== PATCH GROUP 1: capital_model.py ===")
    src = CAP_MODEL.read_text(encoding="utf-8")
    orig_len = len(src)

    # ---- PATCH E1: Build pool_equity_curve after event processing ----
    log("--- E1: Build pool_equity_curve array ---")

    # Insert after the event processing loop, before the equity curve rebuild
    old_e1 = '    # FIX BUG1: Rebuild equity curves and capital allocation from ACCEPTED trades only'

    new_e1 = '''    # Build bar-by-bar pool equity curve for chart display
    # Replay accepted trade entries/exits across all bars
    pool_eq = np.full(n_bars, float(total_capital))
    _pool_bal = float(total_capital)
    _active = []  # (exit_bar, pnl)
    # Build entry/exit event lists sorted by bar
    _entry_events = sorted([(e["bar"], e["exit_bar"], e["pnl"]) for e in accepted], key=lambda x: x[0])
    _ei = 0  # index into _entry_events
    for bar in range(n_bars):
        # Close positions that exit at or before this bar
        _still = []
        for _xb, _xpnl in _active:
            if _xb <= bar:
                _pool_bal += margin_per_pos + _xpnl
            else:
                _still.append((_xb, _xpnl))
        _active = _still
        # Open new positions at this bar
        while _ei < len(_entry_events) and _entry_events[_ei][0] == bar:
            _, _exit_b, _trade_pnl = _entry_events[_ei]
            _pool_bal -= margin_per_pos
            _active.append((_exit_b, _trade_pnl))
            _ei += 1
        # Pool equity = pool_balance + unrealized margin in use
        # (margin is locked but still part of equity)
        pool_eq[bar] = _pool_bal + len(_active) * margin_per_pos

    # FIX BUG1: Rebuild equity curves and capital allocation from ACCEPTED trades only'''

    check("E1: anchor found", old_e1 in src)
    src = src.replace(old_e1, new_e1, 1)
    check("E1: pool_eq built", "pool_eq = np.full" in src)

    # ---- PATCH E2: Add pool_equity_curve to adjusted_pf and return dict ----
    log("--- E2: Add pool_equity_curve to return dict ---")

    old_e2 = '    adjusted_pf["portfolio_dd_pct"] = round(float(dd_arr.min()), 2)'

    new_e2 = '    adjusted_pf["portfolio_dd_pct"] = round(float(dd_arr.min()), 2)\n    adjusted_pf["pool_equity_curve"] = pool_eq'

    check("E2: dd_pct anchor found", old_e2 in src)
    src = src.replace(old_e2, new_e2, 1)
    check("E2: pool_equity_curve in adjusted_pf", '"pool_equity_curve"' in src)

    # Write and compile
    log("--- Writing capital_model.py ---")
    CAP_MODEL.write_text(src, encoding="utf-8")
    check("E write: file written", CAP_MODEL.exists())
    new_len = len(CAP_MODEL.read_text(encoding="utf-8"))
    log(f"Size: {orig_len} -> {new_len} (delta: {new_len - orig_len:+d})")

    try:
        py_compile.compile(str(CAP_MODEL), doraise=True)
        check("E py_compile: capital_model.py", True)
    except py_compile.PyCompileError as e:
        check("E py_compile: " + str(e), False)


def patch_dashboard():
    """Fix equity curve chart for Shared Pool mode."""
    log("=== PATCH GROUP 2: dashboard_v39.py ===")
    src = DASHBOARD.read_text(encoding="utf-8")
    orig_len = len(src)

    # ---- PATCH E3: Replace equity curve chart with pool-aware version ----
    log("--- E3: Pool-aware equity curve chart ---")

    old_e3 = '''        # Portfolio equity curve (downsample to max 2000 points per trace)
        st.subheader("Portfolio Equity Curve")
        _n_pts = len(pf["master_dt"])
        _step = max(1, _n_pts // 2000)
        _dt_ds = pf["master_dt"][::_step]
        fig_port = go.Figure()
        # Per-coin thin lines
        for sym, eq_arr in pf["per_coin_eq"].items():
            fig_port.add_trace(go.Scatter(
                x=_dt_ds, y=eq_arr[::_step], mode="lines",
                name=sym, line=dict(width=1), opacity=0.4))
        # Portfolio bold line
        fig_port.add_trace(go.Scatter(
            x=_dt_ds, y=pf["portfolio_eq"][::_step], mode="lines",
            name="PORTFOLIO", line=dict(width=3, color=COLORS["green"])))
        fig_port.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
            plot_bgcolor=COLORS["card"], height=500, margin=dict(l=40, r=20, t=20, b=40))
        st.plotly_chart(fig_port, use_container_width=True)'''

    new_e3 = '''        # Portfolio equity curve (downsample to max 2000 points per trace)
        st.subheader("Portfolio Equity Curve")
        _n_pts = len(pf["master_dt"])
        _step = max(1, _n_pts // 2000)
        _dt_ds = pf["master_dt"][::_step]
        fig_port = go.Figure()
        _pool_eq_arr = pf.get("pool_equity_curve")
        if _pool_eq_arr is not None:
            # Shared Pool mode: show pool balance curve + per-coin P&L contribution
            fig_port.add_trace(go.Scatter(
                x=_dt_ds, y=_pool_eq_arr[::_step], mode="lines",
                name="POOL BALANCE", line=dict(width=3, color=COLORS["green"])))
            # Per-coin P&L contribution (delta from $10k baseline)
            for sym, eq_arr in pf["per_coin_eq"].items():
                _pnl_arr = eq_arr - _eq_per_coin  # net P&L per coin over time
                fig_port.add_trace(go.Scatter(
                    x=_dt_ds, y=_pnl_arr[::_step], mode="lines",
                    name=sym + " P&L", line=dict(width=1), opacity=0.4))
            # Add deposit baseline
            fig_port.add_trace(go.Scatter(
                x=[_dt_ds[0], _dt_ds[-1]],
                y=[float(_total_cap_used), float(_total_cap_used)],
                mode="lines", name="Deposit",
                line=dict(width=1, color=COLORS["red"], dash="dash"), opacity=0.6))
        else:
            # Per-Coin Independent mode: show summed engine curves
            for sym, eq_arr in pf["per_coin_eq"].items():
                fig_port.add_trace(go.Scatter(
                    x=_dt_ds, y=eq_arr[::_step], mode="lines",
                    name=sym, line=dict(width=1), opacity=0.4))
            fig_port.add_trace(go.Scatter(
                x=_dt_ds, y=pf["portfolio_eq"][::_step], mode="lines",
                name="PORTFOLIO", line=dict(width=3, color=COLORS["green"])))
        fig_port.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
            plot_bgcolor=COLORS["card"], height=500, margin=dict(l=40, r=20, t=20, b=40))
        st.plotly_chart(fig_port, use_container_width=True)'''

    check("E3: equity chart anchor found", old_e3 in src)
    src = src.replace(old_e3, new_e3, 1)
    check("E3: pool-aware chart added", "POOL BALANCE" in src)

    # ---- PATCH E4: Fix Peak Profit / Worst DD for Shared Pool mode ----
    # These use _engine_baseline which is 10k * N coins. In shared pool,
    # best_moment["equity"] is from summed engine curves (e.g. $171k for 11 coins).
    # $171k - $110k = $61k "peak profit" -- but the actual pool peaked much lower.
    # Use pool_equity_curve for best/worst in shared pool mode.
    log("--- E4: Fix best/worst moments for Shared Pool ---")

    old_e4 = '''        # Best vs Worst capital moments
        st.subheader("Peak Profit vs Worst Drawdown", help="Historical best/worst net P&L moments")
        bw1, bw2 = st.columns(2)
        best = pf["best_moment"]
        worst = pf["worst_moment"]
        _best_net = best["equity"] - _engine_baseline
        _best_info = str(best["date"])[:10] + " | " + str(best["positions"]) + " pos | $" + f"{best['capital']:,.0f}" + " capital"
        bw1.metric("Peak Net Profit", f"${_best_net:+,.2f}", _best_info,
            help="Best net P&L at any point (equity - baseline).")
        _worst_dd = worst["dd_pct"]
        _worst_net = worst["equity"] - _engine_baseline
        _worst_info = str(worst["date"])[:10] + " | " + str(worst["positions"]) + " pos | $" + f"{worst['capital']:,.0f}" + " capital"
        bw2.metric("Worst Drawdown", f"{_worst_dd:.1f}% (${_worst_net:+,.0f})", _worst_info,
            help="Largest peak-to-trough drop. Dollar amount = net P&L at that moment.")'''

    new_e4 = '''        # Best vs Worst capital moments
        st.subheader("Peak Profit vs Worst Drawdown", help="Historical best/worst net P&L moments")
        bw1, bw2 = st.columns(2)
        _pool_eq_bw = pf.get("pool_equity_curve")
        if _pool_eq_bw is not None:
            # Shared Pool: compute best/worst from pool equity curve
            _pool_peak_bar = int(np.argmax(_pool_eq_bw))
            _pool_peak_val = float(_pool_eq_bw[_pool_peak_bar])
            _pool_best_net = _pool_peak_val - float(_total_cap_used)
            _pool_best_dt = str(pf["master_dt"][_pool_peak_bar])[:10]
            bw1.metric("Peak Net Profit", f"${_pool_best_net:+,.2f}",
                _pool_best_dt + " | Pool: $" + f"{_pool_peak_val:,.0f}",
                help="Best pool balance minus deposit.")
            # Worst DD from pool curve
            _pool_peaks = np.maximum.accumulate(_pool_eq_bw)
            _pool_dd = np.where(_pool_peaks > 0, (_pool_eq_bw - _pool_peaks) / _pool_peaks * 100, 0)
            _pool_worst_bar = int(np.argmin(_pool_dd))
            _pool_worst_dd = float(_pool_dd[_pool_worst_bar])
            _pool_worst_val = float(_pool_eq_bw[_pool_worst_bar])
            _pool_worst_net = _pool_worst_val - float(_total_cap_used)
            _pool_worst_dt = str(pf["master_dt"][_pool_worst_bar])[:10]
            bw2.metric("Worst Drawdown", f"{_pool_worst_dd:.1f}% (${_pool_worst_net:+,.0f})",
                _pool_worst_dt + " | Pool: $" + f"{_pool_worst_val:,.0f}",
                help="Largest peak-to-trough drop in pool balance.")
        else:
            # Per-Coin Independent: use engine baseline
            best = pf["best_moment"]
            worst = pf["worst_moment"]
            _best_net = best["equity"] - _engine_baseline
            _best_info = str(best["date"])[:10] + " | " + str(best["positions"]) + " pos | $" + f"{best['capital']:,.0f}" + " capital"
            bw1.metric("Peak Net Profit", f"${_best_net:+,.2f}", _best_info,
                help="Best net P&L at any point (equity - baseline).")
            _worst_dd = worst["dd_pct"]
            _worst_net = worst["equity"] - _engine_baseline
            _worst_info = str(worst["date"])[:10] + " | " + str(worst["positions"]) + " pos | $" + f"{worst['capital']:,.0f}" + " capital"
            bw2.metric("Worst Drawdown", f"{_worst_dd:.1f}% (${_worst_net:+,.0f})", _worst_info,
                help="Largest peak-to-trough drop. Dollar amount = net P&L at that moment.")'''

    check("E4: best/worst anchor found", old_e4 in src)
    src = src.replace(old_e4, new_e4, 1)
    check("E4: pool best/worst added", "_pool_peak_bar" in src)

    # ---- PATCH E5: Fix Max DD% in summary for Shared Pool ----
    log("--- E5: Fix Max DD% for Shared Pool ---")

    old_e5 = '''        _dd_pct = pf["portfolio_dd_pct"]
        pm3.metric("Max DD%", f"{_dd_pct:.1f}%", help="Largest peak-to-trough % drop")'''

    new_e5 = '''        _pool_eq_dd = pf.get("pool_equity_curve")
        if _pool_eq_dd is not None:
            _p_peaks = np.maximum.accumulate(_pool_eq_dd)
            _p_dd = np.where(_p_peaks > 0, (_pool_eq_dd - _p_peaks) / _p_peaks * 100, 0)
            _dd_pct = round(float(np.min(_p_dd)), 1)
        else:
            _dd_pct = pf["portfolio_dd_pct"]
        pm3.metric("Max DD%", f"{_dd_pct:.1f}%", help="Largest peak-to-trough % drop")'''

    check("E5: dd_pct anchor found", old_e5 in src)
    src = src.replace(old_e5, new_e5, 1)
    check("E5: pool DD% added", "_pool_eq_dd" in src)

    # Write and compile
    log("--- Writing dashboard_v39.py ---")
    DASHBOARD.write_text(src, encoding="utf-8")
    check("D write: file written", DASHBOARD.exists())
    new_len = len(DASHBOARD.read_text(encoding="utf-8"))
    log(f"Size: {orig_len} -> {new_len} (delta: {new_len - orig_len:+d})")

    try:
        py_compile.compile(str(DASHBOARD), doraise=True)
        check("D py_compile: dashboard_v39.py", True)
    except py_compile.PyCompileError as e:
        check("D py_compile: " + str(e), False)


def main():
    """Apply equity curve fix for Shared Pool mode."""
    log("=" * 60)
    log("Shared Pool Equity Curve Fix")
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
        log("    - Builds pool_equity_curve (bar-by-bar pool balance)")
        log("    - Stores in adjusted_pf for chart display")
        log("  dashboard_v39.py:")
        log("    - Shared Pool: shows pool balance curve (starts at deposit)")
        log("    - Shared Pool: per-coin lines show P&L contribution (not absolute)")
        log("    - Shared Pool: deposit baseline dashed line")
        log("    - Shared Pool: Peak Profit / Worst DD from pool curve")
        log("    - Shared Pool: Max DD% from pool curve")
        log("    - Per-Coin Independent: unchanged")


if __name__ == "__main__":
    main()

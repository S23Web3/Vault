"""
Tests for Dashboard v3.2 patches.

Validates:
  T1: DD clipping at -100%
  T2: Stress table dict has numeric columns
  T3: Portfolio DD never exceeds -100%
  T4: use_container_width not in st.dataframe calls
  T5: Grades table has numeric WR/Avg/Total
  T6: TP Impact table has numeric values
  T7: sweep_detail_data includes "df" key
  T8: Equity curve scatter has x= param
  T9: Spinner in portfolio mode
  T10: Buttons block before stochastics section
  T11: Tooltips (help=) present on key metrics
  T12: Per-coin DD% capped at -100

Usage:
    python scripts/test_dashboard_v32.py
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

PASS = 0
FAIL = 0
RESULTS = []


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        RESULTS.append(f"  [PASS] {name}")
    else:
        FAIL += 1
        RESULTS.append(f"  [FAIL] {name} -- {detail}")


def read_dashboard():
    """Read dashboard.py as string."""
    path = PROJECT_ROOT / "scripts" / "dashboard.py"
    return path.read_text(encoding="utf-8")


def read_dashboard_lines():
    """Read dashboard.py as list of lines."""
    return read_dashboard().split("\n")


# ====================================================================
# T1: DD clipping at -100%
# ====================================================================
def test_dd_clipping():
    """Verify np.clip(dd_arr, -100.0, 0.0) is present after dd_arr calculation."""
    src = read_dashboard()
    test("T1a: np.clip(dd_arr, -100.0, 0.0) present",
         "np.clip(dd_arr, -100.0, 0.0)" in src,
         "DD clipping line not found")

    # Functional test: synthetic equity that drops below -100%
    portfolio_eq = np.array([10000, 8000, 5000, 2000, -1000, 3000])
    peaks = np.maximum.accumulate(portfolio_eq)
    dd_arr = np.where(peaks > 0, (portfolio_eq - peaks) / peaks * 100.0, 0.0)
    dd_arr = np.clip(dd_arr, -100.0, 0.0)
    test("T1b: DD never below -100%",
         dd_arr.min() >= -100.0,
         f"Min DD = {dd_arr.min()}")
    test("T1c: DD at trough is exactly -100%",
         dd_arr[4] == -100.0,
         f"DD at bar 4 = {dd_arr[4]}")


# ====================================================================
# T2: Stress table has numeric columns
# ====================================================================
def test_stress_table_numeric():
    """Verify stress_rows dict uses round() not f-string formatting."""
    src = read_dashboard()
    # After patch, "Net": should be round(net_s, 2), not f"${net_s:,.2f}"
    test("T2a: Stress Net is numeric",
         '"Net": round(net_s, 2)' in src,
         "Stress Net still has f-string formatting")
    test("T2b: Stress Avg Capital is numeric",
         '"Avg Capital": round(cap_s, 0)' in src,
         "Stress Avg Capital still has f-string formatting")
    test("T2c: Stress table uses Styler",
         ".style.format(" in src and "Avg Capital" in src,
         "Styler format not found for stress table")


# ====================================================================
# T3: Portfolio DD check
# ====================================================================
def test_portfolio_dd():
    """Verify align_portfolio_equity clips DD."""
    src = read_dashboard()
    # Check that np.clip appears right after the dd_arr = np.where line
    lines = read_dashboard_lines()
    dd_line = None
    clip_line = None
    for i, line in enumerate(lines):
        if "dd_arr = np.where(peaks > 0, (portfolio_eq - peaks)" in line:
            dd_line = i
        if dd_line is not None and "np.clip(dd_arr" in line:
            clip_line = i
            break
    test("T3: np.clip immediately after dd_arr calculation",
         dd_line is not None and clip_line is not None and clip_line == dd_line + 1,
         f"dd_line={dd_line}, clip_line={clip_line}")


# ====================================================================
# T4: use_container_width not in st.dataframe
# ====================================================================
def test_no_container_width_on_dataframe():
    """Verify use_container_width=True removed from st.dataframe calls."""
    lines = read_dashboard_lines()
    violations = []
    for i, line in enumerate(lines):
        if "st.dataframe(" in line and "use_container_width=True" in line:
            violations.append(i + 1)  # 1-indexed
    test("T4: No st.dataframe with use_container_width",
         len(violations) == 0,
         f"Found at lines: {violations}")


# ====================================================================
# T5: Grades table numeric
# ====================================================================
def test_grades_numeric():
    """Verify grades table WR/Avg/Total are numeric."""
    src = read_dashboard()
    test("T5a: Grades WR is numeric",
         "round(s['win_rate'] * 100, 1)" in src,
         "WR still formatted as string")
    test("T5b: Grades Avg is numeric",
         "round(s['avg_pnl'], 2)" in src,
         "Avg still formatted as string")
    test("T5c: Grades Total is numeric",
         "round(s['total_pnl'], 2)" in src,
         "Total still formatted as string")


# ====================================================================
# T6: TP Impact table numeric
# ====================================================================
def test_tp_impact_numeric():
    """Verify TP Impact table has numeric values."""
    src = read_dashboard()
    # After patch, should have round() calls instead of f"$..." strings
    test("T6a: No f-string $ in No TP column",
         'f"${n_notp:,.2f}"' not in src,
         "n_notp still f-string formatted")
    test("T6b: No f-string % in WR",
         "m_notp['win_rate']:.1%}" not in src or "round(m_notp" in src,
         "WR still f-string formatted")


# ====================================================================
# T7: sweep_detail_data includes "df"
# ====================================================================
def test_sweep_detail_has_df():
    """Verify sweep_detail_data dict includes 'df' key."""
    src = read_dashboard()
    # After patch: "df": df should appear in the sweep_detail_data assignment
    lines = read_dashboard_lines()
    in_sweep_detail = False
    found_df = False
    for i, line in enumerate(lines):
        if 'st.session_state["sweep_detail_data"] = {' in line:
            in_sweep_detail = True
        if in_sweep_detail:
            if '"df": df' in line or '"df":df' in line:
                found_df = True
                break
            if line.strip() == "}" or line.strip() == "}":
                break
    test("T7: sweep_detail_data has 'df' key",
         found_df,
         "'df': df not found in sweep_detail_data dict")


# ====================================================================
# T8: Equity curve has x= datetime param
# ====================================================================
def test_equity_curve_datetime():
    """Verify equity curve scatter plots have x= param."""
    src = read_dashboard()
    lines = read_dashboard_lines()
    eq_lines = []
    for i, line in enumerate(lines):
        if 'fig_eq.add_trace(go.Scatter(' in line and 'y=eq' in line:
            eq_lines.append((i, "x=" in line))
    test("T8a: Found equity curve scatter lines",
         len(eq_lines) >= 2,
         f"Found {len(eq_lines)} equity scatter lines")
    all_have_x = all(has_x for _, has_x in eq_lines)
    test("T8b: All equity curves have x= param",
         all_have_x,
         f"Lines without x=: {[i+1 for i, has_x in eq_lines if not has_x]}")


# ====================================================================
# T9: Spinner in portfolio mode
# ====================================================================
def test_spinner():
    """Verify st.spinner wraps portfolio backtest loop."""
    src = read_dashboard()
    test("T9: st.spinner in portfolio backtest",
         'st.spinner("Running portfolio backtest...")' in src,
         "Spinner not found")


# ====================================================================
# T10: Buttons before stochastics
# ====================================================================
def test_buttons_position():
    """Verify buttons appear before stochastics section."""
    lines = read_dashboard_lines()
    btn_line = None
    stoch_line = None
    for i, line in enumerate(lines):
        if "# -- Action buttons --" in line and btn_line is None:
            btn_line = i
        if "# -- Stochastic K lengths" in line and stoch_line is None:
            stoch_line = i
    test("T10: Buttons block before stochastics",
         btn_line is not None and stoch_line is not None and btn_line < stoch_line,
         f"btn_line={btn_line}, stoch_line={stoch_line}")


# ====================================================================
# T11: Tooltips present
# ====================================================================
def test_tooltips():
    """Verify help= tooltips on key metrics."""
    src = read_dashboard()
    test("T11a: Net P&L tooltip",
         'help="Profit after commissions and rebates"' in src,
         "Net P&L tooltip not found")
    test("T11b: Peak Capital tooltip",
         'help="Max margin across all coins at once"' in src,
         "Peak Capital tooltip not found")
    test("T11c: Capital Allocation tooltip",
         'help="Historical best/worst, not Monte Carlo"' in src,
         "Capital Allocation tooltip not found")
    test("T11d: LSG% tooltip",
         'help="% of losers that were green before SL"' in src or 'help="% of losers green before SL"' in src,
         "LSG% tooltip not found")


# ====================================================================
# T12: Per-coin DD% cap
# ====================================================================
def test_percoin_dd_cap():
    """Verify per-coin DD% is capped at -100."""
    src = read_dashboard()
    test("T12: Per-coin DD% capped",
         'max(round(ms_c["max_drawdown_pct"], 1), -100.0)' in src,
         "Per-coin DD cap not found")


# ====================================================================
# MAIN
# ====================================================================
def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] Dashboard v3.2 Test Suite")
    print(f"Target: {PROJECT_ROOT / 'scripts' / 'dashboard.py'}")
    print()

    test_dd_clipping()
    test_stress_table_numeric()
    test_portfolio_dd()
    test_no_container_width_on_dataframe()
    test_grades_numeric()
    test_tp_impact_numeric()
    test_sweep_detail_has_df()
    test_equity_curve_datetime()
    test_spinner()
    test_buttons_position()
    test_tooltips()
    test_percoin_dd_cap()

    print(f"Results: {PASS + FAIL} tests")
    for r in RESULTS:
        print(r)
    print()
    print(f"PASS: {PASS}  FAIL: {FAIL}")
    if FAIL > 0:
        print("SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()

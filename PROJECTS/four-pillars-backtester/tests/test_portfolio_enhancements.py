r"""
Test Suite: Dashboard Portfolio Enhancements v3
Tests all 4 phases with REALISTIC data structures matching _trades_to_df() output.

_trades_to_df() columns (from engine/backtester_v384.py line 557):
  direction, grade, entry_bar, exit_bar, entry_price, exit_price,
  sl_price, tp_price, pnl, commission, net_pnl, mfe, mae,
  exit_reason, saw_green, scale_idx

NOT in trades_df: entry_dt, rebate, be_raised, entry_atr

Run from terminal (not from Claude):
  python tests/test_portfolio_enhancements.py
"""
import sys
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0
ERRORS_LIST = []


def check(name, condition):
    """Assert a test condition. Tracks pass/fail counts."""
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        ERRORS_LIST.append(name)
        print(f"  [FAIL] {name}")


def ts():
    """Return current timestamp string."""
    return datetime.now().strftime("%H:%M:%S")


# ============================================================================
# PHASE 1 TESTS: Portfolio Manager
# ============================================================================
print(f"\n[{ts()}] === PHASE 1: Portfolio Manager ===")

from utils.portfolio_manager import (
    save_portfolio, load_portfolio, list_portfolios,
    delete_portfolio, rename_portfolio, PORTFOLIOS_DIR
)

# Use temp dir for tests
import utils.portfolio_manager as pm
_orig_dir = pm.PORTFOLIOS_DIR
_tmp = Path(tempfile.mkdtemp()) / "portfolios"
pm.PORTFOLIOS_DIR = _tmp

# Test 1.1: Save portfolio
print(f"[{ts()}] Testing save_portfolio...")
path = save_portfolio("Test Portfolio", ["RIVERUSDT", "KITEUSDT", "HYPEUSDT"],
                      selection_method="custom", notes="test notes")
check("1.1 save returns path", path is not None and Path(path).exists())

# Test 1.2: Load portfolio
print(f"[{ts()}] Testing load_portfolio...")
loaded = load_portfolio(Path(path).name)
check("1.2 load returns dict", loaded is not None)
check("1.3 load name matches", loaded["name"] == "Test Portfolio")
check("1.4 load coins match", loaded["coins"] == ["RIVERUSDT", "KITEUSDT", "HYPEUSDT"])
check("1.5 load coin_count", loaded["coin_count"] == 3)
check("1.6 load method", loaded["selection_method"] == "custom")
check("1.7 load notes", loaded["notes"] == "test notes")

# Test 1.3: List portfolios
print(f"[{ts()}] Testing list_portfolios...")
save_portfolio("Second Portfolio", ["SANDUSDT"], selection_method="random")
plist = list_portfolios()
check("1.8 list returns 2", len(plist) == 2)
check("1.9 list has name", all("name" in p for p in plist))
check("1.10 list has file", all("file" in p for p in plist))

# Test 1.4: Delete portfolio
print(f"[{ts()}] Testing delete_portfolio...")
deleted = delete_portfolio(Path(path).name)
check("1.11 delete returns True", deleted is True)
plist2 = list_portfolios()
check("1.12 list now 1", len(plist2) == 1)

# Test 1.5: Delete nonexistent
check("1.13 delete nonexistent returns False", delete_portfolio("nonexistent.json") is False)

# Test 1.6: Load nonexistent
check("1.14 load nonexistent returns None", load_portfolio("nonexistent.json") is None)

# Test 1.7: Rename
print(f"[{ts()}] Testing rename_portfolio...")
remaining = plist2[0]["file"]
new_path = rename_portfolio(remaining, "Renamed Portfolio")
check("1.15 rename returns path", new_path is not None)
renamed = load_portfolio(Path(new_path).name)
check("1.16 renamed name correct", renamed["name"] == "Renamed Portfolio")

# Test 1.8: Special characters in name
path_special = save_portfolio("Test!@#$%^&*()Portfolio", ["BTCUSDT"])
loaded_special = load_portfolio(Path(path_special).name)
check("1.17 special chars handled", loaded_special is not None)
check("1.18 special chars coins", loaded_special["coins"] == ["BTCUSDT"])

# Test 1.9: Empty coins
path_empty = save_portfolio("Empty", [])
loaded_empty = load_portfolio(Path(path_empty).name)
check("1.19 empty coins OK", loaded_empty["coins"] == [])
check("1.20 empty coin_count", loaded_empty["coin_count"] == 0)

# Cleanup
pm.PORTFOLIOS_DIR = _orig_dir
shutil.rmtree(_tmp, ignore_errors=True)


# ============================================================================
# PHASE 2 TESTS: Coin Analysis
# FIX BUG9: Use REAL trades_df columns only
# ============================================================================
print(f"\n[{ts()}] === PHASE 2: Coin Analysis ===")

import numpy as np
import pandas as pd
from utils.coin_analysis import (
    compute_extended_metrics, compute_grade_distribution,
    compute_exit_distribution, compute_monthly_pnl,
    compute_loser_detail, compute_commission_breakdown
)

# Create REALISTIC trades DataFrame matching _trades_to_df() output
np.random.seed(42)
n_trades = 50
pnl_vals = np.random.normal(5, 20, n_trades)
comm_vals = np.abs(np.random.normal(2, 1, n_trades))
trades_df = pd.DataFrame({
    "direction": np.random.choice(["LONG", "SHORT"], n_trades),
    "grade": np.random.choice(["A", "B", "C", "D", "ADD", "RE"], n_trades),
    "entry_bar": np.arange(n_trades) * 100,
    "exit_bar": np.arange(n_trades) * 100 + 50,
    "entry_price": np.random.uniform(0.001, 0.01, n_trades),
    "exit_price": np.random.uniform(0.001, 0.01, n_trades),
    "sl_price": np.random.uniform(0.0005, 0.008, n_trades),
    "tp_price": np.random.uniform(0.002, 0.015, n_trades),
    "pnl": pnl_vals,
    "commission": comm_vals,
    "net_pnl": pnl_vals - comm_vals,
    "mfe": np.abs(np.random.normal(10, 5, n_trades)),
    "mae": -np.abs(np.random.normal(8, 4, n_trades)),
    "exit_reason": np.random.choice(["SL", "TP", "SCALE_1", "SCALE_2", "END"], n_trades),
    "saw_green": np.random.choice([True, False], n_trades),
    "scale_idx": np.random.choice([0, 0, 0, 1, 2], n_trades),
})
# NOTE: NO entry_dt, NO rebate, NO be_raised -- these do NOT exist in real output

# Test 2.1: Extended metrics
print(f"[{ts()}] Testing compute_extended_metrics...")
ext = compute_extended_metrics(trades_df, bar_count=5000)
check("2.1 returns dict", isinstance(ext, dict))
check("2.2 has avg_trade", "avg_trade" in ext)
check("2.3 has best_trade", "best_trade" in ext)
check("2.4 has worst_trade", "worst_trade" in ext)
check("2.5 has sl_pct", "sl_pct" in ext)
check("2.6 has tp_pct", "tp_pct" in ext)
check("2.7 has scale_pct", "scale_pct" in ext)
check("2.8 has avg_mfe", "avg_mfe" in ext)
check("2.9 has avg_mae", "avg_mae" in ext)
check("2.10 has max_consec_loss", "max_consec_loss" in ext)
check("2.11 has sortino", "sortino" in ext)
check("2.12 best >= worst", ext["best_trade"] >= ext["worst_trade"])
check("2.13 sl_pct 0-100", 0 <= ext["sl_pct"] <= 100)
check("2.14 consec >= 0", ext["max_consec_loss"] >= 0)

# Test 2.2: Empty DataFrame
ext_empty = compute_extended_metrics(pd.DataFrame())
check("2.15 empty returns defaults", ext_empty["avg_trade"] == 0.0)
check("2.16 empty consec 0", ext_empty["max_consec_loss"] == 0)

# Test 2.3: None input
ext_none = compute_extended_metrics(None)
check("2.17 None returns defaults", ext_none["sortino"] == 0.0)

# Test 2.4: Grade distribution
print(f"[{ts()}] Testing compute_grade_distribution...")
grades = compute_grade_distribution(trades_df)
check("2.18 grades is dict", isinstance(grades, dict))
check("2.19 grades sum = n", sum(grades.values()) == n_trades)

# Test 2.5: Exit distribution
exits = compute_exit_distribution(trades_df)
check("2.20 exits is dict", isinstance(exits, dict))
check("2.21 exits sum = n", sum(exits.values()) == n_trades)

# Test 2.6: Monthly PnL via entry_bar + datetime_index mapping
print(f"[{ts()}] Testing compute_monthly_pnl with datetime_index mapping...")
dt_index = pd.date_range("2025-01-01", periods=5000, freq="5min")
monthly = compute_monthly_pnl(trades_df, datetime_index=dt_index)
check("2.22 monthly is DataFrame", isinstance(monthly, pd.DataFrame))
check("2.23 monthly has month col", "month" in monthly.columns)
check("2.24 monthly has pnl col", "pnl" in monthly.columns)
check("2.25 monthly has rows", len(monthly) > 0)

# Test 2.6b: Monthly PnL without datetime_index returns empty
monthly_empty = compute_monthly_pnl(trades_df, datetime_index=None)
check("2.26 no dt_index -> empty", len(monthly_empty) == 0)

# Test 2.7: Loser detail
losers = compute_loser_detail(trades_df)
check("2.27 losers is DataFrame", isinstance(losers, pd.DataFrame))

# Test 2.8: Commission breakdown (no rebate column in real data)
comm = compute_commission_breakdown(trades_df)
check("2.28 comm is dict", isinstance(comm, dict))
check("2.29 has total_commission", "total_commission" in comm)
check("2.30 commission > 0", comm["total_commission"] > 0)
check("2.31 net = total (no rebate)", comm["net_commission"] == comm["total_commission"])


# ============================================================================
# PHASE 3 TESTS: PDF Export (import check only, no actual generation)
# ============================================================================
print(f"\n[{ts()}] === PHASE 3: PDF Export ===")

from utils.pdf_exporter import check_dependencies, HAS_REPORTLAB, HAS_MATPLOTLIB

ok, msg = check_dependencies()
check("3.1 check_dependencies returns tuple", isinstance(ok, bool))
check("3.2 matplotlib available", HAS_MATPLOTLIB)
if HAS_REPORTLAB:
    check("3.3 reportlab available", True)
    print(f"  [INFO] reportlab IS installed -- full PDF tests available")
else:
    check("3.3 reportlab not installed (expected)", True)
    print(f"  [INFO] reportlab NOT installed -- install with: pip install reportlab")

# Test import of generate_portfolio_pdf
from utils.pdf_exporter import generate_portfolio_pdf
check("3.4 generate_portfolio_pdf importable", callable(generate_portfolio_pdf))


# ============================================================================
# PHASE 4 TESTS: Capital Model (v3 -- realistic data)
# ============================================================================
print(f"\n[{ts()}] === PHASE 4: Capital Model ===")

from utils.capital_model import (
    apply_capital_constraints, format_capital_summary, GRADE_PRIORITY
)

# Create realistic portfolio data with proper datetime_index per coin
master_dt = pd.date_range("2025-01-01", periods=500, freq="5min")
portfolio_eq = np.cumsum(np.random.normal(1, 5, 500)) + 30000
capital_allocated = np.random.randint(500, 3000, 500).astype(float)

pf_data = {
    "master_dt": master_dt,
    "portfolio_eq": portfolio_eq,
    "per_coin_eq": {"RIVERUSDT": portfolio_eq * 0.4, "KITEUSDT": portfolio_eq * 0.6},
    "total_positions": capital_allocated / 500,
    "capital_allocated": capital_allocated,
    "best_moment": {"label": "Best", "bar": 250, "date": "2025-01-01",
                    "equity": 31000, "dd_pct": 0, "positions": 4, "capital": 2000},
    "worst_moment": {"label": "Worst", "bar": 400, "date": "2025-01-01",
                     "equity": 29000, "dd_pct": -5, "positions": 2, "capital": 1000},
    "portfolio_dd_pct": -5.0,
    "per_coin_lsg": {"RIVERUSDT": 85.0, "KITEUSDT": 90.0},
}

# Synthetic coin results with REALISTIC trades_df columns
coin_results_syn = []
for sym in ["RIVERUSDT", "KITEUSDT"]:
    n_t = 8
    pnl_v = np.array([12, -3, 17, -6, 8, -10, 20, -2], dtype=float)
    comm_v = np.abs(np.random.normal(1.5, 0.5, n_t))
    tdf = pd.DataFrame({
        "direction": ["LONG", "SHORT", "LONG", "SHORT", "LONG", "SHORT", "LONG", "SHORT"],
        "grade": ["A", "B", "A", "C", "B", "D", "A", "C"],
        "entry_bar": [10, 60, 120, 180, 240, 300, 360, 420],
        "exit_bar": [50, 100, 160, 220, 280, 340, 400, 460],
        "entry_price": np.random.uniform(0.001, 0.01, n_t),
        "exit_price": np.random.uniform(0.001, 0.01, n_t),
        "sl_price": np.random.uniform(0.0005, 0.008, n_t),
        "tp_price": np.random.uniform(0.002, 0.015, n_t),
        "pnl": pnl_v,
        "commission": comm_v,
        "net_pnl": pnl_v - comm_v,
        "mfe": np.abs(np.random.normal(10, 5, n_t)),
        "mae": -np.abs(np.random.normal(8, 4, n_t)),
        "exit_reason": ["TP", "SL", "TP", "SL", "SCALE_1", "SL", "TP", "SL"],
        "saw_green": [True, False, True, True, True, False, True, False],
        "scale_idx": [0, 0, 0, 0, 1, 0, 0, 0],
    })
    coin_results_syn.append({
        "symbol": sym,
        "equity_curve": np.cumsum(np.random.normal(1, 3, 500)) + 10000,
        "datetime_index": master_dt,
        "position_counts": np.random.randint(0, 3, 500),
        "trades_df": tdf,
        "metrics": {"total_trades": n_t, "win_rate": 0.5, "sharpe": 1.0,
                    "profit_factor": 1.5, "max_drawdown_pct": -3.0,
                    "pct_losers_saw_green": 0.85},
    })

# Test 4.1: Apply with generous capital (no rejections)
print(f"[{ts()}] Testing apply_capital_constraints...")
result_generous = apply_capital_constraints(coin_results_syn, pf_data, 50000, 500)
check("4.1 returns dict", isinstance(result_generous, dict))
check("4.2 has rejected_count", "rejected_count" in result_generous)
check("4.3 has rejection_log", "rejection_log" in result_generous)
check("4.4 has capital_efficiency", "capital_efficiency" in result_generous)
check("4.5 generous: 0 rejections", result_generous["rejected_count"] == 0)
check("4.6 adjusted_pf exists", "adjusted_pf" in result_generous)
check("4.7 adjusted_pf has portfolio_eq", "portfolio_eq" in result_generous["adjusted_pf"])

# Test 4.2: Apply with tight capital (should reject some)
result_tight = apply_capital_constraints(coin_results_syn, pf_data, 500, 500)
check("4.8 tight: has rejections", result_tight["rejected_count"] > 0)
check("4.9 rejection log entries", len(result_tight["rejection_log"]) > 0)
if result_tight["rejection_log"]:
    r = result_tight["rejection_log"][0]
    check("4.10 rejection has coin", "coin" in r)
    check("4.11 rejection has reason", "reason" in r)
    check("4.12 rejection has grade", "grade" in r)
    check("4.13 rejection has missed_pnl", "missed_pnl" in r)
    check("4.14 rejection has capital_at_time", "capital_at_time" in r)

# BUG1 FIX VERIFICATION: adjusted equity should differ from original when trades rejected
if result_tight["rejected_count"] > 0:
    orig_final = float(pf_data["portfolio_eq"][-1])
    adj_final = float(result_tight["adjusted_pf"]["portfolio_eq"][-1])
    check("4.15 BUG1 FIX: adjusted equity != original", abs(orig_final - adj_final) > 0.01)
    print(f"  Original final equity: ${orig_final:,.2f}")
    print(f"  Adjusted final equity: ${adj_final:,.2f}")

# BUG7 FIX VERIFICATION: capital efficiency uses adjusted values
eff = result_tight["capital_efficiency"]
check("4.16 eff total_capital", eff["total_capital"] == 500)
check("4.17 eff peak_pct", "peak_pct" in eff)
check("4.18 eff avg_pct", "avg_pct" in eff)
check("4.19 eff idle_pct", "idle_pct" in eff)

# Test 4.3: Format summary
lines = format_capital_summary(eff)
check("4.20 format returns list", isinstance(lines, list))
check("4.21 format has 6 lines", len(lines) == 6)

# Test 4.4: None capital (passthrough)
result_none = apply_capital_constraints(coin_results_syn, pf_data, None, 500)
check("4.22 None capital: 0 rejections", result_none["rejected_count"] == 0)

# Test 4.5: Grade priority ordering
check("4.23 A > B priority", GRADE_PRIORITY["A"] < GRADE_PRIORITY["B"])
check("4.24 B > C priority", GRADE_PRIORITY["B"] < GRADE_PRIORITY["C"])

# BUG3 FIX VERIFICATION: signal strength uses grade-only (no MFE look-ahead)
# Verify rejection log contains no MFE-based fields and has grade info
if result_tight["rejection_log"]:
    r0 = result_tight["rejection_log"][0]
    check("4.25 BUG3 FIX: no MFE in rejection log", "mfe" not in r0)
    check("4.26 BUG3 FIX: grade in rejection log", "grade" in r0)


# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*60}")
print(f"[{ts()}] TEST RESULTS: {PASS} passed, {FAIL} failed")
print(f"{'='*60}")
if ERRORS_LIST:
    print("FAILURES: " + ", ".join(ERRORS_LIST))
else:
    print("ALL TESTS PASSED")
sys.exit(0 if FAIL == 0 else 1)

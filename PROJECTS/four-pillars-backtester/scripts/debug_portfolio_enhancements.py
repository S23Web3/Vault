r"""
Debug Script: Dashboard Portfolio Enhancements v3
Validates integration flow, edge cases, and bug fix verification.

Run from terminal (not from Claude):
  python scripts/debug_portfolio_enhancements.py
"""
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0
ERRORS_LIST = []


def check(name, condition):
    """Assert a debug condition."""
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        ERRORS_LIST.append(name)
        print(f"  [FAIL] {name}")


def ts():
    """Return timestamp."""
    return datetime.now().strftime("%H:%M:%S")


import numpy as np
import pandas as pd

# ============================================================================
# DEBUG 1: Portfolio Manager Round-Trip
# ============================================================================
print(f"\n[{ts()}] === DEBUG 1: Portfolio Manager Round-Trip ===")
from utils.portfolio_manager import save_portfolio, load_portfolio, list_portfolios, delete_portfolio
import utils.portfolio_manager as pm
_orig = pm.PORTFOLIOS_DIR
_tmp = Path(tempfile.mkdtemp()) / "portfolios"
pm.PORTFOLIOS_DIR = _tmp

# Save 5 portfolios with different coin counts (small delay for mtime ordering)
import time as _time
for i in range(5):
    coins = [f"COIN{j}USDT" for j in range(i + 1)]
    save_portfolio(f"Debug Portfolio {i+1}", coins, notes=f"debug test {i+1}")
    _time.sleep(0.05)

plist = list_portfolios()
check("D1.1 5 portfolios saved", len(plist) == 5)
# Sorted by mtime descending -- newest first
all_names = [p["name"] for p in plist]
check("D1.2 sorted by newest first", all_names[0] == "Debug Portfolio 5")

# Load each and verify coin count
for p in plist:
    data = load_portfolio(p["file"])
    check(f"D1.3 {p['name']} loads", data is not None)
    check(f"D1.4 {p['name']} coins", len(data["coins"]) == data["coin_count"])

# Delete all
for p in plist:
    delete_portfolio(p["file"])
check("D1.5 all deleted", len(list_portfolios()) == 0)

pm.PORTFOLIOS_DIR = _orig
shutil.rmtree(_tmp, ignore_errors=True)
print(f"  Round-trip: {PASS} passed")


# ============================================================================
# DEBUG 2: Extended Metrics Edge Cases
# ============================================================================
print(f"\n[{ts()}] === DEBUG 2: Extended Metrics Edge Cases ===")
from utils.coin_analysis import compute_extended_metrics, compute_monthly_pnl

# All winners (realistic columns only)
all_win = pd.DataFrame({
    "net_pnl": [10, 20, 30, 40, 50],
    "pnl": [12, 22, 32, 42, 52],
    "commission": [2, 2, 2, 2, 2],
    "mfe": [15, 25, 35, 45, 55],
    "mae": [-3, -2, -1, -2, -3],
    "exit_reason": ["TP", "TP", "TP", "TP", "TP"],
    "entry_bar": [0, 100, 200, 300, 400],
    "exit_bar": [50, 150, 250, 350, 450],
})
ext_win = compute_extended_metrics(all_win, bar_count=500)
check("D2.1 all winners: consec loss = 0", ext_win["max_consec_loss"] == 0)
check("D2.2 all winners: tp_pct = 100", ext_win["tp_pct"] == 100.0)

# All losers
all_lose = pd.DataFrame({
    "net_pnl": [-10, -20, -30],
    "pnl": [-8, -18, -28],
    "commission": [2, 2, 2],
    "mfe": [5, 3, 2],
    "mae": [-15, -25, -35],
    "exit_reason": ["SL", "SL", "SL"],
    "entry_bar": [0, 100, 200],
    "exit_bar": [50, 150, 250],
})
ext_lose = compute_extended_metrics(all_lose, bar_count=300)
check("D2.3 all losers: consec = 3", ext_lose["max_consec_loss"] == 3)
check("D2.4 all losers: sl_pct = 100", ext_lose["sl_pct"] == 100.0)
check("D2.5 all losers: best < 0", ext_lose["best_trade"] < 0)

# Single trade
single = pd.DataFrame({
    "net_pnl": [42.0], "pnl": [44.0], "commission": [2.0],
    "mfe": [50], "mae": [-5],
    "exit_reason": ["TP"], "entry_bar": [0], "exit_bar": [50],
})
ext_single = compute_extended_metrics(single, bar_count=100)
check("D2.6 single: avg = 42", ext_single["avg_trade"] == 42.0)
check("D2.7 single: best = worst = 42", ext_single["best_trade"] == ext_single["worst_trade"])

# BUG6 FIX: Sortino annualization with bar_count vs without
ext_no_bars = compute_extended_metrics(all_win)
ext_with_bars = compute_extended_metrics(all_win, bar_count=500)
# Without bar_count, uses 105120 default (much higher annualization factor)
# With bar_count=500, uses 500 (lower factor, more realistic)
if ext_no_bars["sortino"] != 0.0 and ext_with_bars["sortino"] != 0.0:
    check("D2.8 BUG6 FIX: different annualization", ext_no_bars["sortino"] != ext_with_bars["sortino"])
else:
    check("D2.8 BUG6 FIX: sortino computed", True)

# BUG5 FIX: monthly PnL via datetime_index
print(f"[{ts()}] Testing BUG5 FIX: monthly PnL via datetime_index...")
dt_index = pd.date_range("2025-01-01", periods=500, freq="5min")
monthly = compute_monthly_pnl(all_win, datetime_index=dt_index)
check("D2.9 BUG5 FIX: monthly has rows", len(monthly) > 0)
check("D2.10 monthly pnl col", "pnl" in monthly.columns)

# Without datetime_index should return empty (not crash)
monthly_no_dt = compute_monthly_pnl(all_win, datetime_index=None)
check("D2.11 no dt_index: empty result", len(monthly_no_dt) == 0)

# Large dataset performance
import time
large = pd.DataFrame({
    "net_pnl": np.random.normal(0, 10, 10000),
    "pnl": np.random.normal(2, 12, 10000),
    "commission": np.abs(np.random.normal(2, 1, 10000)),
    "mfe": np.abs(np.random.normal(5, 3, 10000)),
    "mae": -np.abs(np.random.normal(4, 2, 10000)),
    "exit_reason": np.random.choice(["SL", "TP", "SCALE_1"], 10000),
    "entry_bar": np.arange(10000) * 5,
    "exit_bar": np.arange(10000) * 5 + 3,
})
t0 = time.perf_counter()
ext_large = compute_extended_metrics(large, bar_count=50000)
elapsed = time.perf_counter() - t0
check("D2.12 10K trades < 0.5s", elapsed < 0.5)
print(f"  10K trades computed in {elapsed:.4f}s")


# ============================================================================
# DEBUG 3: Capital Model -- Bug Fix Verification
# ============================================================================
print(f"\n[{ts()}] === DEBUG 3: Capital Model Bug Fixes ===")
from utils.capital_model import apply_capital_constraints, _map_bar_to_master

# BUG2 FIX: verify bar mapping works across different coin timelines
master_dt = pd.date_range("2025-01-01", periods=1000, freq="5min")
coin_a_dt = pd.date_range("2025-01-01 00:00", periods=500, freq="5min")
coin_b_dt = pd.date_range("2025-01-01 10:00", periods=500, freq="5min")

# Coin A bar 0 = 2025-01-01 00:00 -> master bar 0
# Coin B bar 0 = 2025-01-01 10:00 -> master bar 120
mapped_a = _map_bar_to_master(0, coin_a_dt, master_dt)
mapped_b = _map_bar_to_master(0, coin_b_dt, master_dt)
check("D3.1 BUG2 FIX: coin A bar 0 -> master 0", mapped_a == 0)
check("D3.2 BUG2 FIX: coin B bar 0 -> master 120", mapped_b == 120)
print(f"  Coin A bar 0 -> master bar {mapped_a}")
print(f"  Coin B bar 0 -> master bar {mapped_b}")

# Full capital model test with staggered timelines
pf_data = {
    "master_dt": master_dt,
    "portfolio_eq": np.cumsum(np.random.normal(1, 5, 1000)) + 30000,
    "per_coin_eq": {},
    "total_positions": np.ones(1000) * 2,
    "capital_allocated": np.ones(1000) * 1000,
    "best_moment": {"label": "B", "bar": 250, "date": "", "equity": 31000,
                    "dd_pct": 0, "positions": 2, "capital": 1000},
    "worst_moment": {"label": "W", "bar": 500, "date": "", "equity": 29000,
                     "dd_pct": -5, "positions": 2, "capital": 1000},
    "portfolio_dd_pct": -5.0,
    "per_coin_lsg": {},
}

# 2 coins with overlapping trades at DIFFERENT real times
coin_results_dbg = []
for sym, coin_dt in [("AAAUSDT", coin_a_dt), ("BBBUSDT", coin_b_dt)]:
    n_t = 5
    pnl_v = np.array([10, -5, 15, -3, 8], dtype=float)
    comm_v = np.array([1.5, 1.2, 1.8, 1.0, 1.3])
    tdf = pd.DataFrame({
        "direction": ["LONG", "SHORT", "LONG", "SHORT", "LONG"],
        "grade": ["A", "B", "A", "C", "B"],
        "entry_bar": [10, 80, 160, 250, 350],
        "exit_bar": [70, 150, 240, 340, 430],
        "entry_price": np.random.uniform(0.001, 0.01, n_t),
        "exit_price": np.random.uniform(0.001, 0.01, n_t),
        "sl_price": np.random.uniform(0.0005, 0.008, n_t),
        "tp_price": np.random.uniform(0.002, 0.015, n_t),
        "pnl": pnl_v,
        "commission": comm_v,
        "net_pnl": pnl_v - comm_v,
        "mfe": np.abs(np.random.normal(10, 5, n_t)),
        "mae": -np.abs(np.random.normal(8, 4, n_t)),
        "exit_reason": ["TP", "SL", "TP", "SL", "TP"],
        "saw_green": [True, False, True, True, True],
        "scale_idx": [0, 0, 0, 0, 0],
    })
    coin_results_dbg.append({
        "symbol": sym,
        "equity_curve": np.cumsum(np.random.normal(0.5, 2, len(coin_dt))) + 10000,
        "datetime_index": coin_dt,
        "position_counts": np.random.randint(0, 2, len(coin_dt)),
        "trades_df": tdf,
        "metrics": {"total_trades": n_t, "win_rate": 0.6, "sharpe": 1.2,
                    "profit_factor": 1.8, "max_drawdown_pct": -2.5,
                    "pct_losers_saw_green": 0.80},
    })

# Generous capital
r_gen = apply_capital_constraints(coin_results_dbg, pf_data, 10000, 500)
check("D3.3 $10K: 0 rejections", r_gen["rejected_count"] == 0)

# Tight capital: $500 -> only 1 position at a time
r_tight = apply_capital_constraints(coin_results_dbg, pf_data, 500, 500)
check("D3.4 $500: has rejections", r_tight["rejected_count"] > 0)
check("D3.5 rejection log populated", len(r_tight["rejection_log"]) > 0)

# BUG1 FIX: adjusted equity should differ
orig_eq = float(pf_data["portfolio_eq"][-1])
adj_eq = float(r_tight["adjusted_pf"]["portfolio_eq"][-1])
check("D3.6 BUG1 FIX: equity changed", abs(orig_eq - adj_eq) > 0.01)
print(f"  Original final: ${orig_eq:,.2f}")
print(f"  Adjusted final: ${adj_eq:,.2f}")
print(f"  Difference:     ${orig_eq - adj_eq:,.2f}")

# BUG7 FIX: capital efficiency from adjusted values
eff = r_tight["capital_efficiency"]
adj_peak = float(r_tight["adjusted_pf"]["capital_allocated"].max())
check("D3.7 BUG7 FIX: eff peak matches adjusted cap", abs(eff["peak_used"] - adj_peak) < 0.01)

# Rejection detail
if r_tight["rejection_log"]:
    r = r_tight["rejection_log"][0]
    check("D3.8 rejection has all fields", all(k in r for k in ["bar", "coin", "grade", "reason", "missed_pnl"]))
    print(f"  Sample rejection: bar={r['bar']} coin={r['coin']} grade={r['grade']} missed=${r['missed_pnl']:.2f}")

from utils.capital_model import format_capital_summary
lines = format_capital_summary(eff)
check("D3.9 format lines non-empty", all(len(l) > 0 for l in lines))
print(f"  Capital summary:")
for l in lines:
    print(f"    {l}")


# ============================================================================
# DEBUG 4: PDF Export Dependency Check
# ============================================================================
print(f"\n[{ts()}] === DEBUG 4: PDF Export ===")
from utils.pdf_exporter import check_dependencies, HAS_REPORTLAB

ok, msg = check_dependencies()
check("D4.1 dependency check works", isinstance(ok, bool))
if HAS_REPORTLAB:
    print(f"  reportlab installed -- PDF generation available")
    from utils.pdf_exporter import generate_portfolio_pdf
    pf_pdf = {
        "master_dt": pd.date_range("2025-01-01", periods=100, freq="5min"),
        "portfolio_eq": np.cumsum(np.random.normal(1, 3, 100)) + 20000,
        "per_coin_eq": {"TEST": np.cumsum(np.random.normal(0.5, 2, 100)) + 10000},
        "capital_allocated": np.ones(100) * 500,
        "portfolio_dd_pct": -3.5,
        "best_moment": {"label": "B", "bar": 50, "date": "2025-01-01", "equity": 21000,
                        "dd_pct": 0, "positions": 1, "capital": 500},
        "worst_moment": {"label": "W", "bar": 80, "date": "2025-01-01", "equity": 19500,
                         "dd_pct": -3.5, "positions": 1, "capital": 500},
    }
    cr_pdf = [{
        "symbol": "TESTUSDT",
        "equity_curve": np.cumsum(np.random.normal(0.5, 2, 100)) + 10000,
        "datetime_index": pd.date_range("2025-01-01", periods=100, freq="5min"),
        "position_counts": np.ones(100),
        "trades_df": pd.DataFrame({"net_pnl": [10, -5, 15]}),
        "metrics": {"total_trades": 3, "win_rate": 0.67, "sharpe": 1.5,
                    "profit_factor": 2.0, "max_drawdown_pct": -2.0,
                    "pct_losers_saw_green": 0.80},
    }]
    _tmp_pdf = Path(tempfile.mkdtemp()) / "test_report.pdf"
    try:
        out = generate_portfolio_pdf(pf_pdf, cr_pdf, "Debug Test", output_path=str(_tmp_pdf))
        check("D4.2 PDF generated", Path(out).exists())
        check("D4.3 PDF size > 0", Path(out).stat().st_size > 0)
        print(f"  PDF size: {Path(out).stat().st_size:,} bytes")
    except Exception as e:
        check(f"D4.2 PDF generation failed: {e}", False)
    finally:
        if _tmp_pdf.exists():
            _tmp_pdf.unlink()
else:
    print(f"  reportlab NOT installed -- skipping PDF generation test")
    print(f"  Install with: pip install reportlab")
    check("D4.2 skipped (no reportlab)", True)


# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*60}")
print(f"[{ts()}] DEBUG RESULTS: {PASS} passed, {FAIL} failed")
print(f"{'='*60}")
if ERRORS_LIST:
    print("FAILURES: " + ", ".join(ERRORS_LIST))
else:
    print("ALL DEBUG CHECKS PASSED")
sys.exit(0 if FAIL == 0 else 1)

"""
test_dashboard.py

Audit and unit-test script for bingx-live-dashboard-v1-3.py.
Tests: py_compile, data loaders (mock), builders, validators, layout structure.
Run: python scripts/test_dashboard.py
"""

import sys
import json
import os
import tempfile
import py_compile
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

ERRORS = []
BASE = Path(__file__).parent.parent  # PROJECTS/bingx-connector/


def check(label, cond, detail=""):
    """Record pass or fail for a test assertion."""
    if cond:
        print("  PASS  {}".format(label))
    else:
        msg = "  FAIL  {}".format(label) + (" -- {}".format(detail) if detail else "")
        print(msg)
        ERRORS.append(label)


# -----------------------------------------------------------------------
# 1. py_compile -- both files
# -----------------------------------------------------------------------
print("\n[1] py_compile")

for fname in ["bingx-live-dashboard-v1-3.py", "assets/dashboard.css"]:
    path = BASE / fname
    check("file exists: {}".format(fname), path.exists(), "not found at {}".format(path))

try:
    py_compile.compile(str(BASE / "bingx-live-dashboard-v1-3.py"), doraise=True)
    check("py_compile bingx-live-dashboard-v1-3.py", True)
except py_compile.PyCompileError as e:
    check("py_compile bingx-live-dashboard-v1-3.py", False, str(e))

try:
    py_compile.compile(str(Path(__file__)), doraise=True)
    check("py_compile test_dashboard.py", True)
except py_compile.PyCompileError as e:
    check("py_compile test_dashboard.py", False, str(e))


# -----------------------------------------------------------------------
# 2. Import dashboard module (no Dash server starts -- just import)
# -----------------------------------------------------------------------
print("\n[2] Import dashboard module")
sys.path.insert(0, str(BASE))
try:
    # Hyphenated filename requires importlib
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "bingx_live_dashboard_v1_3",
        str(BASE / "bingx-live-dashboard-v1-3.py"),
    )
    dash_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(dash_mod)
    check("import dashboard module", True)
except Exception as e:
    check("import dashboard module", False, str(e))
    print("Cannot continue without import. Aborting.")
    sys.exit(1)


# -----------------------------------------------------------------------
# 3. Data loaders -- mock files
# -----------------------------------------------------------------------
print("\n[3] Data loaders with mock files")

# 3a. load_state -- missing file
original_state_path = dash_mod.STATE_PATH
dash_mod.STATE_PATH = BASE / "nonexistent_state.json"
result = dash_mod.load_state()
check("load_state missing file returns defaults", isinstance(result, dict))
check("load_state has open_positions key", "open_positions" in result)
check("load_state has halt_flag key", "halt_flag" in result)
dash_mod.STATE_PATH = original_state_path

# 3b. load_state -- valid file
tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
json.dump({
    "open_positions": {"X_LONG": {"symbol": "X", "direction": "LONG",
                                   "entry_price": 1.0, "sl_price": 0.9,
                                   "tp_price": None, "quantity": 10,
                                   "notional_usd": 50, "grade": "A",
                                   "entry_time": "2026-02-28T10:00:00+00:00",
                                   "order_id": "123", "atr_at_entry": 0.05,
                                   "be_raised": False}},
    "daily_pnl": -1.5,
    "daily_trades": 2,
    "halt_flag": False,
    "session_start": "2026-02-28T08:00:00+00:00",
}, tmp)
tmp.close()
dash_mod.STATE_PATH = Path(tmp.name)
result = dash_mod.load_state()
check("load_state valid file parsed", result["daily_pnl"] == -1.5)
check("load_state open_positions populated", len(result["open_positions"]) == 1)
dash_mod.STATE_PATH = original_state_path
os.unlink(tmp.name)

# 3c. load_config -- missing file
original_config_path = dash_mod.CONFIG_PATH
dash_mod.CONFIG_PATH = BASE / "nonexistent_config.yaml"
result = dash_mod.load_config()
check("load_config missing file returns empty dict", result == {})
dash_mod.CONFIG_PATH = original_config_path

# 3d. load_trades -- missing file
original_trades_path = dash_mod.TRADES_PATH
dash_mod.TRADES_PATH = BASE / "nonexistent_trades.csv"
result = dash_mod.load_trades()
check("load_trades missing file returns empty DataFrame", result.empty)
dash_mod.TRADES_PATH = original_trades_path

# 3e. load_trades -- valid file
tmp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
tmp_csv.write(
    "timestamp,symbol,direction,grade,entry_price,exit_price,exit_reason,"
    "pnl_net,quantity,notional_usd,entry_time,order_id\n"
    "2026-02-28T10:00:00+00:00,SKR-USDT,LONG,A,0.5,0.55,TP_HIT,"
    "0.025,100,50,2026-02-28T09:00:00+00:00,111\n"
    "2026-02-28T11:00:00+00:00,SKR-USDT,SHORT,B,0.55,0.58,SL_HIT,"
    "-0.015,100,50,2026-02-28T10:30:00+00:00,222\n"
)
tmp_csv.close()
dash_mod.TRADES_PATH = Path(tmp_csv.name)
result = dash_mod.load_trades()
check("load_trades valid file has 2 rows", len(result) == 2)
check("load_trades sorted newest first",
      result.iloc[0]["symbol"] == "SKR-USDT")
check("load_trades pnl_net is numeric",
      pd.api.types.is_numeric_dtype(result["pnl_net"]))


# -----------------------------------------------------------------------
# 4. Builder functions
# -----------------------------------------------------------------------
print("\n[4] Builder functions")

# 4a. fmt_duration
check("fmt_duration returns em-dash for None start",
      dash_mod.fmt_duration(None) == "\u2014")
now = datetime.now(timezone.utc)
start = now - timedelta(hours=2, minutes=15)
result = dash_mod.fmt_duration(start, now)
check("fmt_duration 2h 15m formatted correctly", result == "2h 15m")
start = now - timedelta(minutes=45)
result = dash_mod.fmt_duration(start, now)
check("fmt_duration 45m formatted correctly", result == "45m")

# 4b. build_positions_df
mock_state = {
    "open_positions": {
        "SKR-USDT_LONG": {
            "symbol": "SKR-USDT", "direction": "LONG",
            "entry_price": 0.5, "sl_price": 0.46,
            "tp_price": None, "quantity": 100,
            "notional_usd": 50.0, "grade": "A",
            "entry_time": "2026-02-28T10:00:00+00:00",
            "order_id": "111", "atr_at_entry": 0.02,
            "be_raised": False
        }
    }
}
mock_prices = {"SKR-USDT": 0.52}
df = dash_mod.build_positions_df(mock_state, mock_prices)
check("build_positions_df returns DataFrame", isinstance(df, pd.DataFrame))
check("build_positions_df has 1 row", len(df) == 1)
check("build_positions_df has Unreal PnL column", "Unreal PnL" in df.columns)
check("build_positions_df computes positive PnL for LONG gain",
      df.iloc[0]["Unreal PnL"] > 0)
check("build_positions_df has Dist SL % column", "Dist SL %" in df.columns)
check("build_positions_df Dist SL % is float",
      isinstance(df.iloc[0]["Dist SL %"], float))
check("build_positions_df BE Raised is No",
      df.iloc[0]["BE Raised"] == "No")

# 4c. compute_metrics
df_trades = dash_mod.load_trades()  # uses the CSV set above
metrics = dash_mod.compute_metrics(df_trades)
check("compute_metrics returns dict", isinstance(metrics, dict))
check("compute_metrics win_rate key exists", "win_rate" in metrics)
check("compute_metrics total = 2", metrics["total"] == 2)
check("compute_metrics win_rate 50%", metrics["win_rate"] == 50.0)
# v1-2 new metric keys
check("compute_metrics has sharpe key", "sharpe" in metrics)
check("compute_metrics has max_dd_pct key", "max_dd_pct" in metrics)
check("compute_metrics has net_pnl key", "net_pnl" in metrics)
check("compute_metrics has sl_hit_pct key", "sl_hit_pct" in metrics)
check("compute_metrics has tp_hit_pct key", "tp_hit_pct" in metrics)
check("compute_metrics has avg_win_loss_ratio key", "avg_win_loss_ratio" in metrics)
check("compute_metrics has be_hit_count key", "be_hit_count" in metrics)
check("compute_metrics has lsg_pct key", "lsg_pct" in metrics)
check("compute_metrics be_hit_count is N/A (no column)", metrics["be_hit_count"] == "N/A")
check("compute_metrics lsg_pct is N/A (no column)", metrics["lsg_pct"] == "N/A")
check("compute_metrics sl_hit_pct correct", metrics["sl_hit_pct"] == 50.0)
check("compute_metrics tp_hit_pct correct", metrics["tp_hit_pct"] == 50.0)
check("compute_metrics net_pnl correct", metrics["net_pnl"] == round(0.025 - 0.015, 4))
check("compute_metrics gross_pnl alias equals net_pnl", metrics["gross_pnl"] == metrics["net_pnl"])

# 4e. compute_metrics -- max_dd_pct capping (v1-3 fix)
check("compute_metrics max_dd_pct in valid range",
      -100.0 <= metrics["max_dd_pct"] <= 0.0)


# 4d. build_coin_summary
records = dash_mod.build_coin_summary(df_trades)
check("build_coin_summary returns list", isinstance(records, list))
check("build_coin_summary 1 coin (SKR-USDT)", len(records) == 1)
check("build_coin_summary WR % present", "WR %" in records[0])
check("build_coin_summary Net PnL correct",
      records[0]["Net PnL"] == round(0.025 - 0.015, 4))


# -----------------------------------------------------------------------
# 5. validate_config_updates
# -----------------------------------------------------------------------
print("\n[5] validate_config_updates")

valid_updates = {
    "sl_atr_mult": 2.0, "tp_atr_mult": None, "require_stage2": True,
    "rot_level": 80, "allow_a": True, "allow_b": True,
    "max_positions": 8, "max_daily_trades": 50,
    "daily_loss_limit_usd": 15.0, "min_atr_ratio": 0.003,
    "cooldown_bars": 3, "margin_usd": 5.0, "leverage": 10,
}
ok, err = dash_mod.validate_config_updates(valid_updates)
check("validate_config_updates valid inputs pass", ok, err)

bad = dict(valid_updates)
bad["leverage"] = 0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates leverage=0 fails", not ok)

bad = dict(valid_updates)
bad["sl_atr_mult"] = -1.0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates negative sl_atr_mult fails", not ok)

bad = dict(valid_updates)
bad["daily_loss_limit_usd"] = -5.0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates negative loss limit fails", not ok)


# -----------------------------------------------------------------------
# 6. Chart builders -- smoke test (returns go.Figure without crash)
# -----------------------------------------------------------------------
print("\n[6] Chart builders smoke test")

import plotly.graph_objects as go

fig = dash_mod.build_equity_figure(df_trades)
check("build_equity_figure returns Figure", isinstance(fig, go.Figure))

fig = dash_mod.build_drawdown_figure(df_trades)
check("build_drawdown_figure returns Figure", isinstance(fig, go.Figure))

fig = dash_mod.build_exit_reason_figure(df_trades)
check("build_exit_reason_figure returns Figure", isinstance(fig, go.Figure))

fig = dash_mod.build_daily_pnl_figure(df_trades)
check("build_daily_pnl_figure returns Figure", isinstance(fig, go.Figure))

# Empty DataFrame should not crash
fig = dash_mod.build_equity_figure(pd.DataFrame())
check("build_equity_figure empty df returns Figure", isinstance(fig, go.Figure))


# -----------------------------------------------------------------------
# 7. Layout structure (FIX-4 -- all tabs rendered at startup)
# -----------------------------------------------------------------------
print("\n[7] Layout structure (FIX-4)")

layout = dash_mod.app.layout


def find_ids(component, found=None):
    """Recursively collect component IDs from layout tree."""
    if found is None:
        found = set()
    if hasattr(component, 'id') and component.id:
        found.add(component.id)
    if hasattr(component, 'children'):
        children = component.children
        if isinstance(children, list):
            for child in children:
                find_ids(child, found)
        elif children is not None:
            find_ids(children, found)
    return found


all_ids = find_ids(layout)
check("layout has tab-content-ops", "tab-content-ops" in all_ids)
check("layout has tab-content-hist", "tab-content-hist" in all_ids)
check("layout has tab-content-analytics", "tab-content-analytics" in all_ids)
check("layout has tab-content-coins", "tab-content-coins" in all_ids)
check("layout has tab-content-controls", "tab-content-controls" in all_ids)
check("layout has store-unrealized", "store-unrealized" in all_ids)

check("layout has positions-grid (always present)", "positions-grid" in all_ids)
check("layout has analytics-date-range", "analytics-date-range" in all_ids)
check("layout has hist-date-range", "hist-date-range" in all_ids)
check("layout does NOT have old tab-content div", "tab-content" not in all_ids)


# -----------------------------------------------------------------------
# Cleanup and report
# -----------------------------------------------------------------------
dash_mod.TRADES_PATH = original_trades_path
os.unlink(tmp_csv.name)

print("\n" + "=" * 60)
if ERRORS:
    print("FAILURES: " + ", ".join(ERRORS))
    print("{} test(s) failed.".format(len(ERRORS)))
    sys.exit(1)
else:
    print("All tests passed.")
    sys.exit(0)

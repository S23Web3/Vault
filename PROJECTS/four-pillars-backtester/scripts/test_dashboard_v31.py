"""
Test script for Dashboard v3.1 helper functions.
Tests date filtering, drawdown detection, and portfolio alignment.
Output: structured JSON readable by Claude.

Run: python scripts/test_dashboard_v31.py
"""
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ============================================================================
# HELPER FUNCTIONS (will be patched into dashboard.py by build script)
# Defined here standalone for testing without Streamlit dependency.
# ============================================================================

def apply_date_filter(df, date_range):
    """Filter DataFrame to date range. Returns filtered df or original if too few bars.

    Args:
        df: DataFrame with 'datetime' column (datetime64[ns, UTC]) or DatetimeIndex.
        date_range: tuple of (start_date, end_date) as datetime.date objects, or None.

    Returns:
        Filtered DataFrame with reset index. Original if < 100 bars after filter.
    """
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
    """Find top-N non-overlapping max drawdown windows from an equity curve.

    Algorithm:
        1. Running peak at each bar.
        2. Drawdown % = (equity - peak) / peak at each bar.
        3. Find deepest trough -> walk backward to find the peak start.
        4. Mask that window, repeat for N non-overlapping windows.

    Args:
        equity_curve: numpy array of equity values per bar.
        datetimes: optional array/Series of datetime values aligned to equity_curve.
        n_windows: number of worst drawdown windows to find.
        min_window_bars: minimum bars for a valid window.

    Returns:
        List of dicts: {start_bar, end_bar, start_date, end_date, dd_pct,
                        peak_equity, trough_equity, duration_bars}
    """
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

        # Walk backward to find the peak before this trough
        peak_bar = trough_bar
        for b in range(trough_bar - 1, -1, -1):
            if eq[b] >= peaks[trough_bar]:
                peak_bar = b
                break

        if trough_bar - peak_bar < min_window_bars:
            peak_bar = max(0, trough_bar - min_window_bars)

        start_date = ""
        end_date = ""
        if datetimes is not None:
            try:
                start_date = str(datetimes[peak_bar])[:10]
                end_date = str(datetimes[trough_bar])[:10]
            except (IndexError, TypeError):
                pass

        windows.append({
            "start_bar": peak_bar,
            "end_bar": trough_bar,
            "start_date": start_date,
            "end_date": end_date,
            "dd_pct": round(float(dd_pct[trough_bar]), 2),
            "peak_equity": round(float(eq[peak_bar]), 2),
            "trough_equity": round(float(eq[trough_bar]), 2),
            "duration_bars": trough_bar - peak_bar,
        })

        # Mask this window + buffer
        buffer = max(10, (trough_bar - peak_bar) // 5)
        mask_start = max(0, peak_bar - buffer)
        mask_end = min(n, trough_bar + buffer + 1)
        mask[mask_start:mask_end] = False

    return windows


def align_portfolio_equity(coin_results, margin_per_pos=500.0, max_positions=4):
    """Align multiple coin equity curves by timestamp and compute portfolio metrics.

    Args:
        coin_results: list of dicts, each with:
            symbol: str
            equity_curve: numpy array
            datetime_index: DatetimeIndex or array of datetimes
            position_counts: numpy array (positions active per bar)
            trades_df: DataFrame with net_pnl, saw_green columns
        margin_per_pos: margin per position slot (from settings)
        max_positions: max slots per coin

    Returns:
        dict with:
            master_dt: DatetimeIndex (union of all coin timestamps)
            portfolio_eq: numpy array (summed equity curve)
            per_coin_eq: dict of {symbol: aligned equity array}
            total_positions: numpy array (sum of positions across coins at each bar)
            capital_allocated: numpy array (total_positions * margin_per_pos)
            best_moment: dict (bar, date, equity, positions, capital)
            worst_moment: dict (bar, date, dd_pct, positions, capital)
            portfolio_dd_pct: float (max drawdown %)
            per_coin_lsg: dict of {symbol: lsg_pct}
    """
    if not coin_results:
        return None

    # Build master timeline
    master_dt = pd.DatetimeIndex([])
    for cr in coin_results:
        dt_idx = pd.DatetimeIndex(cr["datetime_index"])
        master_dt = master_dt.union(dt_idx)
    master_dt = master_dt.sort_values()

    n_bars = len(master_dt)
    portfolio_eq = np.zeros(n_bars)
    total_positions = np.zeros(n_bars)
    per_coin_eq = {}

    for cr in coin_results:
        sym = cr["symbol"]
        dt_idx = pd.DatetimeIndex(cr["datetime_index"])

        # Align equity
        eq_series = pd.Series(cr["equity_curve"], index=dt_idx)
        eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(10000.0).values
        per_coin_eq[sym] = eq_aligned
        portfolio_eq += eq_aligned

        # Align position counts
        pos_series = pd.Series(cr["position_counts"], index=dt_idx)
        pos_aligned = pos_series.reindex(master_dt, method="ffill").fillna(0).values
        total_positions += pos_aligned

    capital_allocated = total_positions * margin_per_pos

    # Portfolio drawdown
    peaks = np.maximum.accumulate(portfolio_eq)
    dd_arr = np.where(peaks > 0, (portfolio_eq - peaks) / peaks * 100.0, 0.0)
    worst_bar = int(np.argmin(dd_arr))
    best_bar = int(np.argmax(portfolio_eq))

    def bar_info(bar_idx, label):
        """Build info dict for a specific bar (best/worst moment)."""
        dt_str = str(master_dt[bar_idx])[:19] if bar_idx < len(master_dt) else ""
        return {
            "label": label,
            "bar": bar_idx,
            "date": dt_str,
            "equity": round(float(portfolio_eq[bar_idx]), 2),
            "dd_pct": round(float(dd_arr[bar_idx]), 2),
            "positions": int(total_positions[bar_idx]),
            "capital": round(float(capital_allocated[bar_idx]), 2),
        }

    # Per-coin LSG
    per_coin_lsg = {}
    for cr in coin_results:
        tdf = cr.get("trades_df")
        if tdf is not None and not tdf.empty:
            losers = tdf[tdf["net_pnl"] < 0]
            if len(losers) > 0:
                lsg = losers["saw_green"].sum() / len(losers) * 100.0
            else:
                lsg = 0.0
            per_coin_lsg[cr["symbol"]] = round(lsg, 1)

    return {
        "master_dt": master_dt,
        "portfolio_eq": portfolio_eq,
        "per_coin_eq": per_coin_eq,
        "total_positions": total_positions,
        "capital_allocated": capital_allocated,
        "best_moment": bar_info(best_bar, "Best"),
        "worst_moment": bar_info(worst_bar, "Worst"),
        "portfolio_dd_pct": round(float(dd_arr.min()), 2),
        "per_coin_lsg": per_coin_lsg,
    }


# ============================================================================
# TEST SUITE
# ============================================================================

def run_tests():
    """Run all tests, return structured JSON result."""
    results = []
    passed = 0
    failed = 0

    def test(name, condition, detail=""):
        """Record a single test result as PASS or FAIL."""
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        if condition:
            passed += 1
        else:
            failed += 1
        results.append({"test": name, "status": status, "detail": detail})

    # ── apply_date_filter tests ──

    # T1: None date_range returns original
    df = pd.DataFrame({
        "datetime": pd.date_range("2025-01-01", periods=500, freq="min", tz="UTC"),
        "close": np.random.randn(500),
    })
    out = apply_date_filter(df, None)
    test("date_filter_none", len(out) == 500, f"len={len(out)}")

    # T2: Filter to 2 hours (120 bars)
    start = datetime(2025, 1, 1, 1, 0).date()
    end = datetime(2025, 1, 1, 3, 0).date()
    out = apply_date_filter(df, (start, end))
    # 2 hours of data is only 120 bars < 100 threshold... actually 1440 min/day
    # Let's use a bigger df
    df_big = pd.DataFrame({
        "datetime": pd.date_range("2025-01-01", periods=10000, freq="min", tz="UTC"),
        "close": np.random.randn(10000),
    })
    start2 = datetime(2025, 1, 3).date()
    end2 = datetime(2025, 1, 5).date()
    out2 = apply_date_filter(df_big, (start2, end2))
    # Inclusive range: Jan 3 00:00 to Jan 5 23:59:59 = 3 full days = 4320 bars
    test("date_filter_range", 4000 < len(out2) < 4500, f"len={len(out2)} (expect ~4320)")

    # T3: "All" equivalent (wide range)
    start_all = datetime(2024, 1, 1).date()
    end_all = datetime(2026, 1, 1).date()
    out3 = apply_date_filter(df_big, (start_all, end_all))
    test("date_filter_all", len(out3) == 10000, f"len={len(out3)}")

    # T4: Too few bars returns original (need < 100 bars after filter)
    # .date() truncates to midnight, so Jan 1 to Jan 1 = full day = 1440 bars (> 100)
    # Use a tiny df instead to trigger the fallback
    df_tiny = pd.DataFrame({
        "datetime": pd.date_range("2025-01-01", periods=150, freq="min", tz="UTC"),
        "close": np.random.randn(150),
    })
    # Filter to 30 min range = 30 bars < 100 -> fallback to original 150
    start_tiny = datetime(2025, 1, 1, 0, 0).date()
    end_tiny = datetime(2025, 1, 1, 0, 0).date()
    # end_ts = Jan 1 + 1 day - 1 sec = Jan 1 23:59:59 -> captures all 150 bars
    # Need a range that actually produces < 100 bars. Use df with only 50 bars.
    df_50 = pd.DataFrame({
        "datetime": pd.date_range("2025-01-01", periods=50, freq="h", tz="UTC"),
        "close": np.random.randn(50),
    })
    # Filter to just 2 hours = 2 bars < 100 -> fallback
    start_tiny2 = datetime(2025, 1, 1, 10, 0).date()
    end_tiny2 = datetime(2025, 1, 1, 12, 0).date()
    out4 = apply_date_filter(df_50, (start_tiny2, end_tiny2))
    test("date_filter_too_few", len(out4) == 50, f"len={len(out4)} (fallback to all 50)")

    # T5: Timezone handling -- naive date objects work with UTC datetime column
    start5 = datetime(2025, 1, 2).date()
    end5 = datetime(2025, 1, 4).date()
    out5 = apply_date_filter(df_big, (start5, end5))
    if len(out5) > 0 and "datetime" in out5.columns:
        first_dt = pd.Timestamp(out5["datetime"].iloc[0])
        test("date_filter_tz", first_dt.day == 2, f"first_day={first_dt.day}")
    else:
        test("date_filter_tz", False, "empty result")

    # ── find_worst_drawdowns tests ──

    # T6: Simple drawdown -- equity goes up, crashes, recovers, crashes again
    eq = np.array([10000] * 100)
    # Ramp up to 11000
    for i in range(100, 200):
        eq = np.append(eq, 10000 + (i - 100) * 10)
    # Crash to 10200 (DD1: -800 from 11000, -7.27%)
    for i in range(200, 280):
        eq = np.append(eq, 11000 - (i - 200) * 10)
    # Recover to 11500
    for i in range(280, 400):
        eq = np.append(eq, 10200 + (i - 280) * (1300 / 120))
    # Second crash to 10500 (DD2: -1000 from 11500, -8.70%)
    for i in range(400, 500):
        eq = np.append(eq, 11500 - (i - 400) * 10)

    windows = find_worst_drawdowns(eq, n_windows=2, min_window_bars=20)
    test("drawdown_count", len(windows) == 2, f"found {len(windows)} windows")

    # T7: Worst DD should be the deeper one
    if len(windows) >= 1:
        test("drawdown_worst_first", windows[0]["dd_pct"] < windows[1]["dd_pct"] if len(windows) > 1 else True,
             f"dd1={windows[0]['dd_pct']}, dd2={windows[1]['dd_pct'] if len(windows) > 1 else 'N/A'}")
    else:
        test("drawdown_worst_first", False, "no windows")

    # T8: Windows are non-overlapping
    if len(windows) == 2:
        no_overlap = windows[0]["end_bar"] < windows[1]["start_bar"] or windows[1]["end_bar"] < windows[0]["start_bar"]
        test("drawdown_no_overlap", no_overlap,
             f"w1=[{windows[0]['start_bar']},{windows[0]['end_bar']}] w2=[{windows[1]['start_bar']},{windows[1]['end_bar']}]")
    else:
        test("drawdown_no_overlap", False, "need 2 windows")

    # T9: Dates populated when datetimes provided
    dts = pd.date_range("2025-01-01", periods=len(eq), freq="5min", tz="UTC")
    windows_dt = find_worst_drawdowns(eq, datetimes=dts, n_windows=1)
    if windows_dt:
        test("drawdown_dates", windows_dt[0]["start_date"] != "", f"start={windows_dt[0]['start_date']}")
    else:
        test("drawdown_dates", False, "no windows with dates")

    # T10: Empty/short equity returns empty
    windows_short = find_worst_drawdowns(np.array([10000] * 10), n_windows=1, min_window_bars=50)
    test("drawdown_short", len(windows_short) == 0, f"found {len(windows_short)}")

    # T11: Flat equity (no drawdown) returns empty
    windows_flat = find_worst_drawdowns(np.ones(200) * 10000, n_windows=3)
    test("drawdown_flat", len(windows_flat) == 0, f"found {len(windows_flat)}")

    # ── align_portfolio_equity tests ──

    # T12: Two coins, overlapping dates
    dt1 = pd.date_range("2025-01-01", periods=1000, freq="5min", tz="UTC")
    dt2 = pd.date_range("2025-01-01 02:00", periods=800, freq="5min", tz="UTC")
    eq1 = 10000 + np.cumsum(np.random.randn(1000) * 2)
    eq2 = 10000 + np.cumsum(np.random.randn(800) * 2)
    pos1 = np.random.choice([0, 1, 2, 3, 4], size=1000)
    pos2 = np.random.choice([0, 1, 2], size=800)

    tdf1 = pd.DataFrame({"net_pnl": np.random.randn(50), "saw_green": np.random.choice([True, False], 50)})
    tdf2 = pd.DataFrame({"net_pnl": np.random.randn(30), "saw_green": np.random.choice([True, False], 30)})

    coin_results = [
        {"symbol": "BTCUSDT", "equity_curve": eq1, "datetime_index": dt1, "position_counts": pos1, "trades_df": tdf1},
        {"symbol": "ETHUSDT", "equity_curve": eq2, "datetime_index": dt2, "position_counts": pos2, "trades_df": tdf2},
    ]

    portfolio = align_portfolio_equity(coin_results, margin_per_pos=500, max_positions=4)
    test("portfolio_not_none", portfolio is not None, "")

    if portfolio is not None:
        # T13: Master timeline is union
        test("portfolio_master_len", len(portfolio["master_dt"]) >= max(len(dt1), len(dt2)),
             f"master={len(portfolio['master_dt'])}, max_coin={max(len(dt1), len(dt2))}")

        # T14: Portfolio equity is sum of two coins
        test("portfolio_eq_len", len(portfolio["portfolio_eq"]) == len(portfolio["master_dt"]),
             f"eq={len(portfolio['portfolio_eq'])}, dt={len(portfolio['master_dt'])}")

        # T15: Per-coin equity dict has both symbols
        test("portfolio_per_coin", set(portfolio["per_coin_eq"].keys()) == {"BTCUSDT", "ETHUSDT"},
             f"keys={set(portfolio['per_coin_eq'].keys())}")

        # T16: Best/worst moments have required fields
        best = portfolio["best_moment"]
        worst = portfolio["worst_moment"]
        test("portfolio_best_fields", all(k in best for k in ["bar", "date", "equity", "positions", "capital"]),
             f"keys={list(best.keys())}")
        test("portfolio_worst_fields", all(k in worst for k in ["bar", "date", "dd_pct", "positions", "capital"]),
             f"keys={list(worst.keys())}")

        # T17: Portfolio DD is negative
        test("portfolio_dd_negative", portfolio["portfolio_dd_pct"] < 0,
             f"dd={portfolio['portfolio_dd_pct']}%")

        # T18: LSG per coin computed
        test("portfolio_lsg", len(portfolio["per_coin_lsg"]) == 2,
             f"lsg={portfolio['per_coin_lsg']}")

        # T19: Capital allocated array matches positions
        test("portfolio_capital", float(portfolio["capital_allocated"].max()) > 0,
             f"peak_capital={portfolio['capital_allocated'].max()}")

    else:
        for name in ["portfolio_master_len", "portfolio_eq_len", "portfolio_per_coin",
                      "portfolio_best_fields", "portfolio_worst_fields", "portfolio_dd_negative",
                      "portfolio_lsg", "portfolio_capital"]:
            test(name, False, "portfolio is None")

    # T20: Empty input
    empty_portfolio = align_portfolio_equity([])
    test("portfolio_empty", empty_portfolio is None, "")

    # ── Output ──
    report = {
        "tests": passed + failed,
        "passed": passed,
        "failed": failed,
        "details": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    report = run_tests()
    sys.exit(0 if report["failed"] == 0 else 1)

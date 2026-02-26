"""
Compare v3.8 vs v3.8.2 (AVWAP trailing) on RIVER 5m.
Runs 4 configs side by side:
  1. v3.8 baseline: ATR SL/TP, BE$4 (proven profitable)
  2. v3.8.2 AVWAP 2sigma, no TP (matches Pine Script v3.8.2)
  3. v3.8.2 AVWAP 2sigma, WITH TP 1.5 ATR (hybrid test)
  4. v3.8.2 AVWAP 1sigma, no TP (tighter SL test)

Usage: python scripts/compare_v382.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signals.four_pillars import compute_signals
from engine.backtester import Backtester


def run_config(df: pd.DataFrame, label: str, params: dict) -> dict:
    """Run a single backtest config and return metrics."""
    bt = Backtester(params)
    results = bt.run(df.copy())
    m = results["metrics"]
    return {
        "label": label,
        "trades": m["total_trades"],
        "win_rate": m["win_rate"],
        "expectancy": m["expectancy"],
        "net_pnl": m["net_pnl"],
        "pf": m["profit_factor"],
        "sharpe": m["sharpe"],
        "max_dd": m["max_drawdown"],
        "commission": m["total_commission"],
        "lsg": m["pct_losers_saw_green"],
        "be_raised": m["be_raised_count"],
    }


def main():
    # Load RIVER 5m
    cache_dir = Path(__file__).resolve().parent.parent / "data" / "cache"
    f5m = cache_dir / "RIVERUSDT_5m.parquet"
    f1m = cache_dir / "RIVERUSDT_1m.parquet"

    if f5m.exists():
        df = pd.read_parquet(f5m)
        print(f"Loaded {len(df)} 5m candles for RIVERUSDT")
    elif f1m.exists():
        df = pd.read_parquet(f1m)
        print(f"Loaded {len(df)} 1m candles, resampling to 5m...")
        if "datetime" in df.columns:
            df = df.set_index("datetime")
        df = df.resample("5min").agg({
            "open": "first", "high": "max", "low": "min", "close": "last",
            "base_vol": "sum", "quote_vol": "sum"
        }).dropna().reset_index()
    else:
        print("No cached data for RIVERUSDT. Run fetch_data.py first.")
        sys.exit(1)

    # Compute signals (same for all configs)
    signal_params = {
        "atr_length": 14,
        "cross_level": 25,
        "zone_level": 30,
        "stage_lookback": 10,
        "allow_b_trades": True,
        "allow_c_trades": True,
        "b_open_fresh": True,
        "cloud2_reentry": True,
        "reentry_lookback": 10,
    }
    df = compute_signals(df, signal_params)
    print(f"Signals computed: {len(df)} bars\n")

    # Base params (shared)
    base = {
        "cooldown": 3,
        "b_open_fresh": True,
        "commission_rate": 0.0008,
        "rebate_pct": 0.70,
        "notional": 10000.0,
        "initial_equity": 10000.0,
    }

    # Config 1: v3.8 baseline (ATR SL/TP, BE$4)
    c1 = {**base,
        "sl_mult": 1.0,
        "tp_mult": 1.5,
        "use_tp": True,
        "be_raise_amount": 4.0,
        "avwap_enabled": False,
    }

    # Config 2: v3.8.2 AVWAP 2sigma, no TP (Pine Script match)
    c2 = {**base,
        "sl_mult": 1.0,       # Initial SL = 1 ATR (before AVWAP kicks in)
        "tp_mult": 1.5,
        "use_tp": False,       # No TP -- runner
        "be_raise_amount": 0,
        "avwap_enabled": True,
        "avwap_band": 2,       # SL at 2sigma
        "avwap_floor_atr": 0.5,  # Floor = 0.5 * ATR
    }

    # Config 3: v3.8.2 AVWAP 2sigma, WITH TP (hybrid)
    c3 = {**base,
        "sl_mult": 1.0,
        "tp_mult": 1.5,
        "use_tp": True,        # Keep TP
        "be_raise_amount": 0,
        "avwap_enabled": True,
        "avwap_band": 2,
        "avwap_floor_atr": 0.5,
    }

    # Config 4: v3.8.2 AVWAP 1sigma, no TP (tighter trailing)
    c4 = {**base,
        "sl_mult": 1.0,
        "tp_mult": 1.5,
        "use_tp": False,
        "be_raise_amount": 0,
        "avwap_enabled": True,
        "avwap_band": 1,       # SL at 1sigma (tighter)
        "avwap_floor_atr": 0.5,
    }

    # Config 5: v3.8 + AVWAP trail + BE$4 (best of both)
    c5 = {**base,
        "sl_mult": 1.0,
        "tp_mult": 1.5,
        "use_tp": True,
        "be_raise_amount": 4.0,
        "avwap_enabled": True,
        "avwap_band": 2,
        "avwap_floor_atr": 0.5,
    }

    configs = [
        ("v3.8 BASE (ATR SL/TP BE$4)", c1),
        ("v3.8.2 AVWAP-2s NO TP", c2),
        ("v3.8.2 AVWAP-2s + TP", c3),
        ("v3.8.2 AVWAP-1s NO TP", c4),
        ("v3.8 + AVWAP-2s + BE$4 + TP", c5),
    ]

    results = []
    for label, params in configs:
        print(f"Running: {label}...")
        r = run_config(df, label, params)
        results.append(r)

    # Print comparison table
    print("\n" + "=" * 110)
    print(f"{'Config':<32} {'Trades':>6} {'WR':>6} {'$/tr':>8} {'Net P&L':>10} {'PF':>6} {'Sharpe':>7} {'MaxDD':>9} {'Comm$':>9} {'LSG':>5}")
    print("=" * 110)
    for r in results:
        print(f"{r['label']:<32} {r['trades']:>6} {r['win_rate']:>5.1%} {r['expectancy']:>8.2f} {r['net_pnl']:>10.0f} {r['pf']:>6.2f} {r['sharpe']:>7.2f} {r['max_dd']:>9.0f} {r['commission']:>9.0f} {r['lsg']:>4.0%}")
    print("=" * 110)

    # Analysis
    print("\nKEY INSIGHTS:")
    base_pnl = results[0]["net_pnl"]
    for r in results[1:]:
        diff = r["net_pnl"] - base_pnl
        sign = "+" if diff >= 0 else ""
        print(f"  {r['label']}: {sign}${diff:.0f} vs baseline")


if __name__ == "__main__":
    main()

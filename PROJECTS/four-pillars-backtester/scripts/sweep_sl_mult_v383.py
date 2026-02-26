"""
Sweep sl_mult values for v3.8.3.
Tests ATR multiplier for initial SL: 1.0, 1.5, 2.0, 2.5.

Usage:
  python scripts/sweep_sl_mult_v383.py
  python scripts/sweep_sl_mult_v383.py --coins 10 --seed 42
  python scripts/sweep_sl_mult_v383.py --output results/sweep_v383_sl_mult.md
"""

import argparse
import random
import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester_v383 import Backtester383

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "results" / "sweep_v383_sl_mult.md"

SL_MULT_VALUES = [1.0, 1.5, 2.0, 2.5]


def list_5m_coins():
    return sorted([f.stem.replace("_5m", "") for f in CACHE_DIR.glob("*_5m.parquet")])


def load_5m(symbol):
    path = CACHE_DIR / f"{symbol}_5m.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})
    return df


def run_coin(symbol, df_signals, params, sl_mult):
    try:
        p = dict(params)
        p["sl_mult"] = sl_mult
        bt = Backtester383(p)
        results = bt.run(df_signals)
        m = results["metrics"]
        m["symbol"] = symbol
        m["sl_mult"] = sl_mult
        return m
    except Exception as e:
        print(f"  ERROR on {symbol} sl_mult={sl_mult}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Sweep sl_mult for v3.8.3")
    parser.add_argument("--coins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--rebate", type=float, default=0.70)
    parser.add_argument("--notional", type=float, default=5000.0)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    params = {
        "notional": args.notional,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": args.rebate,
        "max_positions": 4,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_mult": 2.0,
        "checkpoint_interval": 5,
        "max_scaleouts": 2,
        "enable_adds": True,
        "enable_reentry": True,
        "b_open_fresh": True,
    }

    all_coins = list_5m_coins()
    print(f"Found {len(all_coins)} coins with 5m data")

    selected = random.sample(all_coins, min(args.coins, len(all_coins)))
    print(f"Testing {len(selected)} coins: {', '.join(selected)}")
    print(f"SL multipliers: {SL_MULT_VALUES}\n")

    # Precompute signals (shared across sl_mult values)
    coin_signals = {}
    for coin in selected:
        df = load_5m(coin)
        if df is None or len(df) < 200:
            print(f"  {coin}: SKIP (insufficient data)")
            continue
        try:
            df = compute_signals_v383(df, params)
            coin_signals[coin] = df
            d_count = df["long_d"].sum() + df["short_d"].sum()
            a_count = df["long_a"].sum() + df["short_a"].sum()
            print(f"  {coin}: {len(df)} bars, A={a_count}, D={d_count}")
        except Exception as e:
            print(f"  {coin}: ERROR computing signals: {e}")

    # Run each sl_mult on all coins
    config_results = {}
    for sl_mult in SL_MULT_VALUES:
        label = f"SL_{sl_mult:.1f}"
        print(f"\n--- Config: {label} ---")
        config_metrics = []

        for coin, df in coin_signals.items():
            t0 = time.time()
            m = run_coin(coin, df, params, sl_mult)
            elapsed = time.time() - t0
            if m:
                sc = m.get("scale_out_count", 0)
                net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
                print(f"  {coin}: {m['total_trades']} trades, ${net_ar:,.2f} net(+rebate), "
                      f"scales={sc}, flat={m.get('pct_time_flat',0):.0%} ({elapsed:.1f}s)")
                config_metrics.append(m)

        config_results[label] = config_metrics

    # Build markdown report
    md = []
    md.append("# v3.8.3 SL Multiplier Sweep\n")
    md.append(f"**Coins**: {len(coin_signals)}")
    md.append(f"**Notional**: ${args.notional:,.0f}/position | 4 slots max")
    md.append(f"**Commission**: taker 0.08%, maker 0.02% | Rebate: {args.rebate*100:.0f}%")
    md.append(f"**SL**: ATR-based (ABCD), AVWAP 2sigma (ADD/RE) | **Scale-out**: 2x at +2sigma")
    md.append(f"**Checkpoint**: 5 bars\n")

    # Summary table (Net P&L = after rebate)
    md.append("## Summary Comparison\n")
    md.append("| SL Mult | Trades | WR | LSG% | Net P&L (w/rebate) | $/Trade | PF | Scales | Comm | Rebate | Avg Pos | % Flat | Avg Margin |")
    md.append("|---------|--------|------|------|--------------------|---------|----|--------|------|--------|---------|--------|------------|")

    for label, metrics_list in config_results.items():
        if not metrics_list:
            md.append(f"| {label} | 0 | | | | | | | | | | | |")
            continue

        total_trades = sum(m["total_trades"] for m in metrics_list)
        total_pnl_ar = sum(m.get("net_pnl_after_rebate", m["net_pnl"]) for m in metrics_list)
        total_comm = sum(m["total_commission"] for m in metrics_list)
        total_rebate = sum(m.get("total_rebate", 0) for m in metrics_list)
        total_scales = sum(m.get("scale_out_count", 0) for m in metrics_list)
        avg_wr = np.mean([m["win_rate"] for m in metrics_list])
        avg_lsg = np.mean([m.get("pct_losers_saw_green", 0) for m in metrics_list])
        avg_pos = np.mean([m.get("avg_positions", 0) for m in metrics_list])
        avg_flat = np.mean([m.get("pct_time_flat", 0) for m in metrics_list])
        avg_margin = np.mean([m.get("avg_margin_used", 0) for m in metrics_list])

        gp = sum(m["gross_profit"] for m in metrics_list)
        gl = sum(m["gross_loss"] for m in metrics_list)
        pf = gp / max(gl, 1)

        md.append(
            f"| {label} | {total_trades:,} | {avg_wr:.0%} | {avg_lsg:.0%} | "
            f"${total_pnl_ar:,.2f} | ${total_pnl_ar/max(total_trades,1):.2f} | {pf:.2f} | "
            f"{total_scales:,} | ${total_comm:,.2f} | ${total_rebate:,.2f} | "
            f"{avg_pos:.1f} | {avg_flat:.0%} | ${avg_margin:,.0f} |"
        )

    # Per-coin detail for each config
    for label, metrics_list in config_results.items():
        md.append(f"\n## {label} Detail\n")
        md.append("| Symbol | Trades | WR | LSG% | Net P&L (w/rebate) | $/Trade | PF | Scales | Avg Pos | % Flat | MaxDD |")
        md.append("|--------|--------|------|------|--------------------|---------|----|--------|---------|--------|-------|")

        for m in metrics_list:
            lsg = m.get("pct_losers_saw_green", 0)
            sc = m.get("scale_out_count", 0)
            net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
            avg_p = m.get("avg_positions", 0)
            flat = m.get("pct_time_flat", 0)
            md.append(
                f"| {m['symbol']} | {m['total_trades']} | {m['win_rate']:.0%} | {lsg:.0%} | "
                f"${net_ar:,.2f} | ${net_ar/max(m['total_trades'],1):.2f} | {m['profit_factor']:.2f} | "
                f"{sc} | {avg_p:.1f} | {flat:.0%} | ${m['max_drawdown']:,.2f} |"
            )

        # Grade breakdown
        if metrics_list:
            md.append(f"\n### {label} Grade Breakdown\n")
            md.append("| Symbol | A | B | C | D | ADD | RE | R |")
            md.append("|--------|---|---|---|---|-----|----|----|")
            for m in metrics_list:
                grades = m.get("grades", {})
                cols = []
                for g in ["A", "B", "C", "D", "ADD", "RE", "R"]:
                    if g in grades:
                        s = grades[g]
                        cols.append(f"{s['count']}({s['win_rate']:.0%})")
                    else:
                        cols.append("-")
                md.append(f"| {m['symbol']} | {' | '.join(cols)} |")

    # Profitable coins summary (using net after rebate)
    md.append("\n## Profitable Coins Summary (Net after Rebate)\n")
    md.append("| Config | Profitable | Unprofitable | Best | Worst |")
    md.append("|--------|------------|--------------|------|-------|")
    for label, metrics_list in config_results.items():
        if not metrics_list:
            continue
        prof = [m for m in metrics_list if m.get("net_pnl_after_rebate", m["net_pnl"]) > 0]
        unprof = [m for m in metrics_list if m.get("net_pnl_after_rebate", m["net_pnl"]) <= 0]
        best_str = ""
        worst_str = ""
        if prof:
            best = max(prof, key=lambda m: m.get("net_pnl_after_rebate", m["net_pnl"]))
            best_str = f"{best['symbol']} +${best.get('net_pnl_after_rebate', best['net_pnl']):,.0f}"
        if unprof:
            worst = min(unprof, key=lambda m: m.get("net_pnl_after_rebate", m["net_pnl"]))
            worst_str = f"{worst['symbol']} ${worst.get('net_pnl_after_rebate', worst['net_pnl']):,.0f}"
        md.append(f"| {label} | {len(prof)} | {len(unprof)} | {best_str} | {worst_str} |")

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md), encoding="utf-8")

    print(f"\n{'=' * 55}")
    print(f"  SL MULT SWEEP COMPLETE")
    print(f"  {len(coin_signals)} coins x {len(SL_MULT_VALUES)} configs")
    print(f"  Results saved to: {out_path}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()

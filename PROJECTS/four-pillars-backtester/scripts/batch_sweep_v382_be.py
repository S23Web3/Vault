"""
Batch sweep v3.8.2 with multi-level BE raise.
Tests multiple BE configurations side by side on the same coins.

Usage:
  python scripts/batch_sweep_v382_be.py
  python scripts/batch_sweep_v382_be.py --coins 10 --seed 42
  python scripts/batch_sweep_v382_be.py --output results/sweep_v382_be.md
"""

import argparse
import random
import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signals.four_pillars_v382 import compute_signals_v382
from engine.backtester_v382 import Backtester382

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "results" / "sweep_v382_be.md"

# BE configurations to test
BE_CONFIGS = {
    "NONE": [],
    "BE_0.3": [(0.3, 0.0)],
    "BE_0.5": [(0.5, 0.0)],
    "BE_0.3+0.5": [(0.3, 0.0), (0.5, 0.15)],
    "BE_0.3+0.5+1.0": [(0.3, 0.0), (0.5, 0.15), (1.0, 0.4)],
    "BE_0.2+0.4+0.8": [(0.2, 0.0), (0.4, 0.1), (0.8, 0.3)],
}


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


def run_coin(symbol, df_signals, params, be_levels):
    """Run v3.8.2 backtest with specific BE levels. Returns metrics or None."""
    try:
        p = dict(params)
        p["be_levels"] = be_levels
        bt = Backtester382(p)
        results = bt.run(df_signals)
        m = results["metrics"]
        m["symbol"] = symbol
        m["be_raised_count"] = sum(1 for t in results["trades"] if t.be_raised)
        return m
    except Exception as e:
        print(f"  ERROR on {symbol}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Batch sweep v3.8.2 with BE raise")
    parser.add_argument("--coins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--rebate", type=float, default=0.50)
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
        "sl_atr_mult": 1.0,
        "stage2_bars": 5,
        "stage1to2_trigger": "opposite_2sigma",
        "enable_adds": True,
        "enable_reentry": True,
        "b_open_fresh": True,
    }

    all_coins = list_5m_coins()
    print(f"Found {len(all_coins)} coins with 5m data")

    selected = random.sample(all_coins, min(args.coins, len(all_coins)))
    print(f"Testing {len(selected)} coins: {', '.join(selected)}")
    print(f"BE configs: {list(BE_CONFIGS.keys())}\n")

    # Precompute signals for all coins (shared across BE configs)
    coin_signals = {}
    for coin in selected:
        df = load_5m(coin)
        if df is None or len(df) < 200:
            print(f"  {coin}: SKIP (insufficient data)")
            continue
        try:
            df = compute_signals_v382(df, params)
            coin_signals[coin] = df
            print(f"  {coin}: {len(df)} bars, signals ready")
        except Exception as e:
            print(f"  {coin}: ERROR computing signals: {e}")

    # Run each BE config on all coins
    config_results = {}
    for config_name, be_levels in BE_CONFIGS.items():
        print(f"\n--- Config: {config_name} ({be_levels or 'disabled'}) ---")
        config_metrics = []

        for coin, df in coin_signals.items():
            t0 = time.time()
            m = run_coin(coin, df, params, be_levels)
            elapsed = time.time() - t0
            if m:
                be_ct = m.get("be_raised_count", 0)
                print(f"  {coin}: {m['total_trades']} trades, ${m['net_pnl']:,.2f} net, "
                      f"BE raised: {be_ct} ({elapsed:.1f}s)")
                config_metrics.append(m)
            else:
                print(f"  {coin}: SKIP ({elapsed:.1f}s)")

        config_results[config_name] = config_metrics

    # Build markdown report
    md = []
    md.append("# v3.8.2 BE Raise Comparison\n")
    md.append(f"**Coins**: {len(coin_signals)}")
    md.append(f"**Notional**: ${args.notional:,.0f}/position | 4 slots max")
    md.append(f"**Commission**: taker 0.08%, maker 0.02% | Rebate: {args.rebate*100:.0f}%")
    md.append(f"**SL**: AVWAP 3-stage | **TP**: None (runner)\n")

    # Summary comparison table
    md.append("## Summary Comparison\n")
    md.append("| Config | Trades | WR | LSG% | Net P&L | $/Trade | PF | BE Raised | Commission | Rebate |")
    md.append("|--------|--------|------|------|---------|---------|------|-----------|------------|--------|")

    for config_name, metrics_list in config_results.items():
        if not metrics_list:
            md.append(f"| {config_name} | 0 | | | | | | | | |")
            continue

        total_trades = sum(m["total_trades"] for m in metrics_list)
        total_pnl = sum(m["net_pnl"] for m in metrics_list)
        total_comm = sum(m["total_commission"] for m in metrics_list)
        total_rebate = sum(m.get("total_rebate", 0) for m in metrics_list)
        total_be = sum(m.get("be_raised_count", 0) for m in metrics_list)
        avg_wr = np.mean([m["win_rate"] for m in metrics_list])
        avg_lsg = np.mean([m.get("pct_losers_saw_green", 0) for m in metrics_list])

        # Weighted PF
        gp = sum(m["gross_profit"] for m in metrics_list)
        gl = sum(m["gross_loss"] for m in metrics_list)
        pf = gp / max(gl, 1)

        md.append(
            f"| {config_name} | {total_trades:,} | {avg_wr:.0%} | {avg_lsg:.0%} | "
            f"${total_pnl:,.2f} | ${total_pnl/max(total_trades,1):.2f} | {pf:.2f} | "
            f"{total_be:,} | ${total_comm:,.2f} | ${total_rebate:,.2f} |"
        )

    # Per-coin detail for each config
    for config_name, metrics_list in config_results.items():
        md.append(f"\n## {config_name} Detail\n")
        be_desc = BE_CONFIGS[config_name]
        if be_desc:
            levels_str = ", ".join([f"trigger={t:.1f}ATR->lock={l:.1f}ATR" for t, l in be_desc])
            md.append(f"Levels: {levels_str}\n")
        else:
            md.append("No BE raise (baseline)\n")

        md.append("| Symbol | Trades | WR | LSG% | Net P&L | $/Trade | PF | BE Raised | MaxDD |")
        md.append("|--------|--------|------|------|---------|---------|------|-----------|-------|")

        for m in metrics_list:
            sym = m["symbol"]
            lsg = m.get("pct_losers_saw_green", 0)
            be_ct = m.get("be_raised_count", 0)
            md.append(
                f"| {sym} | {m['total_trades']} | {m['win_rate']:.0%} | {lsg:.0%} | "
                f"${m['net_pnl']:,.2f} | ${m['expectancy']:.2f} | {m['profit_factor']:.2f} | "
                f"{be_ct} | ${m['max_drawdown']:,.2f} |"
            )

    # Profitable coins per config
    md.append("\n## Profitable Coins Summary\n")
    md.append("| Config | Profitable | Unprofitable | Best | Worst |")
    md.append("|--------|------------|--------------|------|-------|")
    for config_name, metrics_list in config_results.items():
        if not metrics_list:
            continue
        prof = [m for m in metrics_list if m["net_pnl"] > 0]
        unprof = [m for m in metrics_list if m["net_pnl"] <= 0]
        best_str = ""
        worst_str = ""
        if prof:
            best = max(prof, key=lambda m: m["net_pnl"])
            best_str = f"{best['symbol']} +${best['net_pnl']:,.0f}"
        if unprof:
            worst = min(unprof, key=lambda m: m["net_pnl"])
            worst_str = f"{worst['symbol']} ${worst['net_pnl']:,.0f}"
        md.append(f"| {config_name} | {len(prof)} | {len(unprof)} | {best_str} | {worst_str} |")

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md), encoding="utf-8")

    print(f"\n{'=' * 55}")
    print(f"  BE SWEEP COMPLETE")
    print(f"  {len(coin_signals)} coins x {len(BE_CONFIGS)} configs")
    print(f"  Results saved to: {out_path}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()

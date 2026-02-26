"""
Batch sweep: 5 batches of 10 random coins on v3.8.2.
Saves all output to an MD file for review.

Usage: python scripts/batch_sweep_v382.py
       python scripts/batch_sweep_v382.py --batches 3 --per-batch 5
       python scripts/batch_sweep_v382.py --output results/sweep_v382.md
"""

import argparse
import random
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signals.four_pillars_v382 import compute_signals_v382
from engine.backtester_v382 import Backtester382

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "results" / "batch_sweep_v382.md"


def list_5m_coins() -> list:
    """List all symbols with 5m cached data."""
    return sorted([f.stem.replace("_5m", "") for f in CACHE_DIR.glob("*_5m.parquet")])


def load_5m(symbol: str) -> pd.DataFrame:
    """Load 5m cached data."""
    path = CACHE_DIR / f"{symbol}_5m.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})
    return df


def run_coin(symbol: str, params: dict) -> dict:
    """Run v3.8.2 backtest on one coin. Returns metrics dict or None."""
    df = load_5m(symbol)
    if df is None or len(df) < 200:
        return None

    try:
        df = compute_signals_v382(df, params)
        bt = Backtester382(params)
        results = bt.run(df)
        m = results["metrics"]
        m["symbol"] = symbol
        m["bars"] = len(df)
        return m
    except Exception as e:
        print(f"  ERROR on {symbol}: {e}")
        return None


def format_batch_table(results: list, batch_num: int) -> str:
    """Format one batch's results as markdown table."""
    lines = []
    lines.append(f"\n## Batch {batch_num}\n")
    lines.append("| Symbol | Trades | WR | LSG% | Net P&L | $/Trade | PF | Commission | Rebate | MaxDD | Grades |")
    lines.append("|--------|--------|------|------|---------|---------|------|------------|--------|-------|--------|")

    total_trades = 0
    total_pnl = 0
    total_comm = 0
    total_rebate = 0

    for m in results:
        if m is None:
            continue
        sym = m["symbol"]
        trades = m["total_trades"]
        wr = m["win_rate"]
        net = m["net_pnl"]
        exp = m["expectancy"]
        pf = m["profit_factor"]
        comm = m["total_commission"]
        reb = m.get("total_rebate", 0)
        dd = m["max_drawdown"]
        lsg = m.get("pct_losers_saw_green", 0)

        grade_str = ""
        if m.get("grades"):
            parts = []
            for g, s in m["grades"].items():
                parts.append(f"{g}:{s['count']}")
            grade_str = " ".join(parts)

        lines.append(
            f"| {sym} | {trades} | {wr:.0%} | {lsg:.0%} | ${net:,.2f} | ${exp:.2f} | "
            f"{pf:.2f} | ${comm:,.2f} | ${reb:,.2f} | ${dd:,.2f} | {grade_str} |"
        )

        total_trades += trades
        total_pnl += net
        total_comm += comm
        total_rebate += reb

    lines.append(
        f"| **TOTAL** | **{total_trades}** | | | **${total_pnl:,.2f}** | "
        f"**${total_pnl/max(total_trades,1):.2f}** | | "
        f"**${total_comm:,.2f}** | **${total_rebate:,.2f}** | | |"
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Batch sweep v3.8.2")
    parser.add_argument("--batches", type=int, default=5)
    parser.add_argument("--per-batch", type=int, default=10)
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--rebate", type=float, default=0.50)
    parser.add_argument("--notional", type=float, default=5000.0)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Backtest params
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

    if len(all_coins) < args.per_batch:
        print(f"ERROR: Need at least {args.per_batch} coins, found {len(all_coins)}")
        sys.exit(1)

    # Build MD output
    md_lines = []
    md_lines.append(f"# v3.8.2 Batch Sweep Results")
    md_lines.append(f"")
    md_lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md_lines.append(f"**Batches**: {args.batches} x {args.per_batch} coins")
    md_lines.append(f"**Timeframe**: 5m")
    md_lines.append(f"**Notional**: ${args.notional:,.0f}/position | 4 slots max")
    md_lines.append(f"**Commission**: 0.08%/side | Rebate: {args.rebate*100:.0f}%")
    md_lines.append(f"**SL**: AVWAP 3-stage (2sigma -> ATR -> Cloud3)")
    md_lines.append(f"**TP**: None (runner)")
    md_lines.append(f"**Pool**: {len(all_coins)} coins")

    grand_total_trades = 0
    grand_total_pnl = 0
    grand_total_comm = 0
    grand_total_rebate = 0
    all_batch_results = []

    for b in range(1, args.batches + 1):
        batch_coins = random.sample(all_coins, args.per_batch)
        print(f"\n--- Batch {b}/{args.batches}: {', '.join(batch_coins)} ---")

        batch_results = []
        for coin in batch_coins:
            t0 = time.time()
            print(f"  {coin}...", end=" ", flush=True)
            m = run_coin(coin, params)
            elapsed = time.time() - t0
            if m:
                print(f"{m['total_trades']} trades, ${m['net_pnl']:,.2f} net ({elapsed:.1f}s)")
                batch_results.append(m)
                grand_total_trades += m["total_trades"]
                grand_total_pnl += m["net_pnl"]
                grand_total_comm += m["total_commission"]
                grand_total_rebate += m.get("total_rebate", 0)
            else:
                print(f"SKIP ({elapsed:.1f}s)")

        md_lines.append(format_batch_table(batch_results, b))
        all_batch_results.extend(batch_results)

    # Grand summary
    md_lines.append(f"\n## Grand Summary\n")
    md_lines.append(f"| Metric | Value |")
    md_lines.append(f"|--------|-------|")
    md_lines.append(f"| Coins tested | {len(all_batch_results)} |")
    md_lines.append(f"| Total trades | {grand_total_trades:,} |")
    md_lines.append(f"| Total net P&L | ${grand_total_pnl:,.2f} |")
    md_lines.append(f"| Avg $/trade | ${grand_total_pnl/max(grand_total_trades,1):.2f} |")
    md_lines.append(f"| Total commission | ${grand_total_comm:,.2f} |")
    md_lines.append(f"| Total rebate | ${grand_total_rebate:,.2f} |")
    md_lines.append(f"| Net commission | ${grand_total_comm - grand_total_rebate:,.2f} |")

    # Profitable vs unprofitable
    profitable = [m for m in all_batch_results if m["net_pnl"] > 0]
    unprofitable = [m for m in all_batch_results if m["net_pnl"] <= 0]
    md_lines.append(f"| Profitable coins | {len(profitable)}/{len(all_batch_results)} |")
    if profitable:
        best = max(profitable, key=lambda m: m["net_pnl"])
        md_lines.append(f"| Best coin | {best['symbol']} (${best['net_pnl']:,.2f}) |")
    if unprofitable:
        worst = min(unprofitable, key=lambda m: m["net_pnl"])
        md_lines.append(f"| Worst coin | {worst['symbol']} (${worst['net_pnl']:,.2f}) |")

    # Write MD
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"\n{'=' * 55}")
    print(f"  SWEEP COMPLETE")
    print(f"  {len(all_batch_results)} coins | {grand_total_trades:,} trades | ${grand_total_pnl:,.2f} net")
    print(f"  Results saved to: {out_path}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()

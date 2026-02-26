"""
MFE (Maximum Favorable Excursion) analysis by grade for v3.8.3.

For each grade (A/B/C/D/ADD/RE/R), shows how far into profit
losing trades went before reversing. Identifies optimal TP levels
and SL raise points.

MFE expressed in ATR multiples: how many ATRs did price move
in our favor before the trade turned into a loser?

Usage:
  python scripts/mfe_analysis_v383.py
  python scripts/mfe_analysis_v383.py --coins 10 --seed 42 --sl-mult 2.5
"""

import argparse
import random
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester_v383 import Backtester383

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "results" / "mfe_analysis_v383.md"


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


def mfe_to_atr(mfe_dollars, entry_price, entry_atr, notional):
    """Convert MFE in dollars to ATR multiples."""
    if entry_atr <= 0 or notional <= 0 or entry_price <= 0:
        return 0.0
    mfe_pct = mfe_dollars / notional
    price_move = mfe_pct * entry_price
    return price_move / entry_atr


def main():
    parser = argparse.ArgumentParser(description="MFE analysis by grade v3.8.3")
    parser.add_argument("--coins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sl-mult", type=float, default=2.5)
    parser.add_argument("--notional", type=float, default=5000.0)
    parser.add_argument("--rebate", type=float, default=0.70)
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    random.seed(args.seed)

    params = {
        "notional": args.notional,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": args.rebate,
        "max_positions": 4,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_mult": args.sl_mult,
        "checkpoint_interval": 5,
        "max_scaleouts": 2,
        "enable_adds": True,
        "enable_reentry": True,
        "b_open_fresh": True,
    }

    all_coins = list_5m_coins()
    selected = random.sample(all_coins, min(args.coins, len(all_coins)))
    print(f"MFE Analysis: {len(selected)} coins, sl_mult={args.sl_mult}, seed={args.seed}\n")

    # Collect all trades across all coins
    all_trades = []

    for coin in selected:
        df = load_5m(coin)
        if df is None or len(df) < 200:
            continue
        t0 = time.time()
        try:
            df = compute_signals_v383(df, params)
            bt = Backtester383(params)
            results = bt.run(df)
            for t in results["trades"]:
                all_trades.append({
                    "symbol": coin,
                    "grade": t.grade,
                    "direction": t.direction,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "entry_atr": t.entry_atr,
                    "pnl": t.pnl,
                    "commission": t.commission,
                    "net_pnl": t.pnl - t.commission,
                    "mfe": t.mfe,
                    "mae": t.mae,
                    "saw_green": t.saw_green,
                    "exit_reason": t.exit_reason,
                    "scale_idx": t.scale_idx,
                    "bars_held": t.exit_bar - t.entry_bar,
                })
            elapsed = time.time() - t0
            n = len(results["trades"])
            print(f"  {coin}: {n} trades ({elapsed:.1f}s)")
        except Exception as e:
            print(f"  {coin}: ERROR {e}")

    if not all_trades:
        print("No trades collected.")
        sys.exit(1)

    df_trades = pd.DataFrame(all_trades)

    # Compute MFE in ATR multiples
    df_trades["mfe_atr"] = df_trades.apply(
        lambda r: mfe_to_atr(r["mfe"], r["entry_price"], r["entry_atr"], args.notional),
        axis=1
    )
    df_trades["mae_atr"] = df_trades.apply(
        lambda r: -mfe_to_atr(-r["mae"], r["entry_price"], r["entry_atr"], args.notional)
        if r["mae"] < 0 else 0,
        axis=1
    )

    # Classify trades
    df_trades["is_winner"] = df_trades["net_pnl"] > 0
    df_trades["is_loser"] = df_trades["net_pnl"] <= 0
    df_trades["is_lsg"] = df_trades["is_loser"] & df_trades["saw_green"]

    total = len(df_trades)
    print(f"\nTotal trades: {total:,}")
    print(f"Winners: {df_trades['is_winner'].sum():,} ({df_trades['is_winner'].mean():.0%})")
    print(f"Losers: {df_trades['is_loser'].sum():,}")
    print(f"LSG (losers saw green): {df_trades['is_lsg'].sum():,} ({df_trades['is_lsg'].mean():.0%})")

    # ── Print Analysis ──────────────────────────────────────────────────
    sep = "=" * 78
    print(f"\n{sep}")
    print(f"  MFE ANALYSIS BY GRADE (v3.8.3, sl_mult={args.sl_mult})")
    print(f"  {len(selected)} coins, {total:,} trades")
    print(sep)

    # ATR buckets for MFE distribution
    atr_buckets = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, float("inf")]
    bucket_labels = ["0-0.25", "0.25-0.5", "0.5-0.75", "0.75-1.0",
                     "1.0-1.5", "1.5-2.0", "2.0-3.0", "3.0-5.0", "5.0+"]

    md = []
    md.append(f"# MFE Analysis by Grade (v3.8.3)\n")
    md.append(f"**Coins**: {len(selected)} | **SL mult**: {args.sl_mult} | "
              f"**Notional**: ${args.notional:,.0f} | **Rebate**: {args.rebate*100:.0f}%")
    md.append(f"**Total trades**: {total:,} | **LSG**: {df_trades['is_lsg'].sum():,} "
              f"({df_trades['is_lsg'].mean():.0%})\n")

    for grade in ["A", "B", "C", "D", "ADD", "RE", "R"]:
        g = df_trades[df_trades["grade"] == grade]
        if len(g) == 0:
            continue

        winners = g[g["is_winner"]]
        losers = g[g["is_loser"]]
        lsg = g[g["is_lsg"]]
        never_green = losers[~losers["saw_green"]]

        print(f"\n  --- Grade {grade} ({len(g):,} trades) ---")
        print(f"  Winners: {len(winners):,} ({len(winners)/len(g):.0%}) | "
              f"Losers: {len(losers):,} | LSG: {len(lsg):,} ({len(lsg)/max(len(losers),1):.0%})")

        md.append(f"\n## Grade {grade} ({len(g):,} trades)\n")
        md.append(f"- Winners: {len(winners):,} ({len(winners)/len(g):.0%})")
        md.append(f"- Losers: {len(losers):,} | LSG: {len(lsg):,} ({len(lsg)/max(len(losers),1):.0%})")
        md.append(f"- Never green: {len(never_green):,}")

        if len(winners) > 0:
            print(f"  Winners avg MFE: {winners['mfe_atr'].mean():.2f} ATR "
                  f"(${winners['mfe'].mean():.2f})")
            md.append(f"- Winner avg MFE: {winners['mfe_atr'].mean():.2f} ATR (${winners['mfe'].mean():.2f})")

        if len(lsg) > 0:
            print(f"  LSG avg MFE:     {lsg['mfe_atr'].mean():.2f} ATR "
                  f"(${lsg['mfe'].mean():.2f})")
            print(f"  LSG median MFE:  {lsg['mfe_atr'].median():.2f} ATR "
                  f"(${lsg['mfe'].median():.2f})")
            print(f"  LSG max MFE:     {lsg['mfe_atr'].max():.2f} ATR "
                  f"(${lsg['mfe'].max():.2f})")
            print(f"  LSG avg loss:    ${lsg['net_pnl'].mean():.2f}")

            md.append(f"- LSG avg MFE: {lsg['mfe_atr'].mean():.2f} ATR (${lsg['mfe'].mean():.2f})")
            md.append(f"- LSG median MFE: {lsg['mfe_atr'].median():.2f} ATR (${lsg['mfe'].median():.2f})")
            md.append(f"- LSG max MFE: {lsg['mfe_atr'].max():.2f} ATR (${lsg['mfe'].max():.2f})")
            md.append(f"- LSG avg net loss: ${lsg['net_pnl'].mean():.2f}")

            # MFE distribution for LSG trades (in ATR multiples)
            print(f"\n  LSG MFE Distribution (ATR multiples):")
            md.append(f"\n### LSG MFE Distribution (how far into profit before reversing)\n")
            md.append("| ATR Range | Count | % of LSG | Cum % | Avg $ Peak | Avg $ Loss |")
            md.append("|-----------|-------|----------|-------|------------|------------|")

            cum = 0
            for b in range(len(bucket_labels)):
                lo = atr_buckets[b]
                hi = atr_buckets[b + 1]
                in_bucket = lsg[(lsg["mfe_atr"] >= lo) & (lsg["mfe_atr"] < hi)]
                ct = len(in_bucket)
                pct = ct / len(lsg) if len(lsg) > 0 else 0
                cum += pct
                avg_peak = in_bucket["mfe"].mean() if ct > 0 else 0
                avg_loss = in_bucket["net_pnl"].mean() if ct > 0 else 0
                bar = "#" * int(pct * 40)
                print(f"    {bucket_labels[b]:>8}: {ct:>5} ({pct:>5.1%}) cum {cum:>5.1%} "
                      f"avg peak ${avg_peak:>6.2f} avg loss ${avg_loss:>7.2f}  {bar}")
                md.append(f"| {bucket_labels[b]} | {ct} | {pct:.1%} | {cum:.1%} | "
                          f"${avg_peak:.2f} | ${avg_loss:.2f} |")

            # TP impact analysis: "if we had TP at X ATR, how many LSG would become winners?"
            print(f"\n  TP Impact (if TP set at X ATR, LSG trades saved):")
            md.append(f"\n### TP Impact Analysis\n")
            md.append(f"If TP was set at X ATR, how many LSG trades would have been captured as winners?\n")
            md.append("| TP Level | LSG Captured | % of LSG | $ Captured (gross) | vs Actual Loss |")
            md.append("|----------|-------------|----------|-------------------|----------------|")

            for tp_atr in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]:
                captured = lsg[lsg["mfe_atr"] >= tp_atr]
                ct = len(captured)
                pct = ct / len(lsg) if len(lsg) > 0 else 0
                # Gross profit if TP hit: tp_atr * entry_atr / entry_price * notional
                tp_profits = captured.apply(
                    lambda r: tp_atr * r["entry_atr"] / r["entry_price"] * args.notional
                    if r["entry_price"] > 0 else 0, axis=1
                )
                gross_captured = tp_profits.sum() if ct > 0 else 0
                actual_loss = captured["net_pnl"].sum() if ct > 0 else 0
                improvement = gross_captured - actual_loss
                print(f"    {tp_atr:.2f} ATR: {ct:>5} trades ({pct:>5.1%}), "
                      f"gross ${gross_captured:>8,.0f}, vs actual ${actual_loss:>8,.0f}, "
                      f"delta +${improvement:>8,.0f}")
                md.append(f"| {tp_atr:.2f} ATR | {ct} | {pct:.1%} | ${gross_captured:,.0f} | "
                          f"+${improvement:,.0f} |")

        # Winners: how much did they peak vs what they closed at?
        if len(winners) > 0:
            left_on_table = winners["mfe"] - (winners["pnl"])
            avg_left = left_on_table.mean()
            print(f"\n  Winners: avg left on table: ${avg_left:.2f} "
                  f"(peaked ${winners['mfe'].mean():.2f}, closed ${winners['pnl'].mean():.2f})")
            md.append(f"\n- Winners avg left on table: ${avg_left:.2f} "
                      f"(peaked ${winners['mfe'].mean():.2f}, closed ${winners['pnl'].mean():.2f})")

        # MAE analysis for losers (how deep did they go?)
        if len(losers) > 0:
            print(f"  Losers avg MAE:  {losers['mae_atr'].mean():.2f} ATR "
                  f"(${losers['mae'].mean():.2f})")
            md.append(f"- Losers avg MAE: {losers['mae_atr'].mean():.2f} ATR (${losers['mae'].mean():.2f})")

    # ── Combined summary table ──────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  COMBINED GRADE SUMMARY")
    print(f"{sep}")
    print(f"  {'Grade':<6} {'Trades':>7} {'WR':>5} {'LSG%':>5} {'LSG MFE':>8} "
          f"{'Win MFE':>8} {'TP@1ATR':>8} {'TP@1.5ATR':>9}")
    print(f"  {'-'*6} {'-'*7} {'-'*5} {'-'*5} {'-'*8} {'-'*8} {'-'*8} {'-'*9}")

    md.append(f"\n## Combined Summary\n")
    md.append("| Grade | Trades | WR | LSG% | LSG avg MFE | Win avg MFE | "
              "TP@1ATR saved | TP@1.5ATR saved |")
    md.append("|-------|--------|------|------|-------------|-------------|"
              "--------------|-----------------|")

    for grade in ["A", "B", "C", "D", "ADD", "RE", "R"]:
        g = df_trades[df_trades["grade"] == grade]
        if len(g) == 0:
            continue
        wr = g["is_winner"].mean()
        losers = g[g["is_loser"]]
        lsg = g[g["is_lsg"]]
        winners = g[g["is_winner"]]
        lsg_pct = len(lsg) / max(len(losers), 1)
        lsg_mfe = f"{lsg['mfe_atr'].mean():.2f}" if len(lsg) > 0 else "-"
        win_mfe = f"{winners['mfe_atr'].mean():.2f}" if len(winners) > 0 else "-"

        tp1 = len(lsg[lsg["mfe_atr"] >= 1.0]) if len(lsg) > 0 else 0
        tp15 = len(lsg[lsg["mfe_atr"] >= 1.5]) if len(lsg) > 0 else 0
        tp1_pct = f"{tp1/max(len(lsg),1):.0%}" if len(lsg) > 0 else "-"
        tp15_pct = f"{tp15/max(len(lsg),1):.0%}" if len(lsg) > 0 else "-"

        print(f"  {grade:<6} {len(g):>7,} {wr:>4.0%} {lsg_pct:>4.0%} "
              f"{lsg_mfe:>8} {win_mfe:>8} {tp1:>5}({tp1_pct}) {tp15:>5}({tp15_pct})")
        md.append(f"| {grade} | {len(g):,} | {wr:.0%} | {lsg_pct:.0%} | "
                  f"{lsg_mfe} ATR | {win_mfe} ATR | {tp1} ({tp1_pct}) | {tp15} ({tp15_pct}) |")

    # Write markdown
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"\nResults saved to: {out_path}")
    print(sep)


if __name__ == "__main__":
    main()

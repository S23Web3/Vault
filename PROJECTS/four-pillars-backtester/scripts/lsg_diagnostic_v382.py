"""
LSG (Losers Saw Green) diagnostic for v3.8.2.
Runs backtest on N random coins, captures full trade-level MFE/MAE data,
analyzes BE raise conversion potential at multiple trigger levels.

Usage:
  python scripts/lsg_diagnostic_v382.py
  python scripts/lsg_diagnostic_v382.py --coins 20 --seed 42
  python scripts/lsg_diagnostic_v382.py --output results/lsg_diagnostic.md
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
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "results" / "lsg_diagnostic_v382.md"


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


def run_coin_trades(symbol, params):
    """Run backtest, return (trades_list, metrics) or (None, None)."""
    df = load_5m(symbol)
    if df is None or len(df) < 200:
        return None, None
    try:
        df = compute_signals_v382(df, params)
        bt = Backtester382(params)
        results = bt.run(df)
        return results["trades"], results["metrics"]
    except Exception as e:
        print(f"  ERROR on {symbol}: {e}")
        return None, None


def analyze_lsg(all_trades, notional):
    """Analyze losers-saw-green across all trades."""
    if not all_trades:
        return {}

    losers = [t for t in all_trades if t.pnl - t.commission <= 0]
    winners = [t for t in all_trades if t.pnl - t.commission > 0]
    total = len(all_trades)
    n_losers = len(losers)
    n_winners = len(winners)

    if n_losers == 0:
        return {"total": total, "losers": 0, "lsg_rate": 0}

    lsg = [t for t in losers if t.saw_green]
    n_lsg = len(lsg)
    lsg_rate = n_lsg / n_losers

    # MFE distribution for LSG losers (in dollar terms)
    lsg_mfes = [t.mfe for t in lsg] if lsg else [0]
    # MAE distribution for all losers
    loser_maes = [t.mae for t in losers]
    # Net P&L of losers
    loser_pnls = [t.pnl - t.commission for t in losers]

    # MFE as ATR multiple for LSG losers
    lsg_mfe_atr = []
    for t in lsg:
        if t.entry_atr > 0:
            mfe_price = t.mfe * t.entry_price / notional
            lsg_mfe_atr.append(mfe_price / t.entry_atr)

    # Grade breakdown
    grade_lsg = {}
    for grade in ["A", "B", "C", "R", "ADD", "RE"]:
        grade_losers = [t for t in losers if t.grade == grade]
        if not grade_losers:
            continue
        grade_saw = [t for t in grade_losers if t.saw_green]
        grade_lsg[grade] = {
            "losers": len(grade_losers),
            "saw_green": len(grade_saw),
            "rate": len(grade_saw) / len(grade_losers),
        }

    # Exit stage breakdown
    stage_lsg = {}
    for stage in [1, 2, 3]:
        stage_losers = [t for t in losers if t.exit_stage == stage]
        if not stage_losers:
            continue
        stage_saw = [t for t in stage_losers if t.saw_green]
        stage_lsg[stage] = {
            "losers": len(stage_losers),
            "saw_green": len(stage_saw),
            "rate": len(stage_saw) / len(stage_losers),
            "avg_loss": np.mean([t.pnl - t.commission for t in stage_losers]),
        }

    # BE conversion estimates at multiple ATR trigger levels
    be_estimates = {}
    for trigger in [0.1, 0.2, 0.3, 0.5, 0.75, 1.0]:
        convertible = 0
        saved_pnl = 0.0
        for t in lsg:
            if t.entry_atr > 0:
                mfe_price = t.mfe * t.entry_price / notional
                if mfe_price >= trigger * t.entry_atr:
                    convertible += 1
                    saved_pnl += abs(t.pnl - t.commission)
        be_estimates[trigger] = {
            "convertible": convertible,
            "pct_of_lsg": convertible / max(n_lsg, 1),
            "pct_of_losers": convertible / n_losers,
            "saved_pnl": saved_pnl,
            "saved_per_trade": saved_pnl / max(convertible, 1),
        }

    # Hold time (in bars)
    winner_hold = [t.exit_bar - t.entry_bar for t in winners] if winners else [0]
    loser_hold = [t.exit_bar - t.entry_bar for t in losers]
    lsg_hold = [t.exit_bar - t.entry_bar for t in lsg] if lsg else [0]

    return {
        "total": total,
        "winners": n_winners,
        "losers": n_losers,
        "lsg_count": n_lsg,
        "lsg_rate": lsg_rate,
        "lsg_mfes": np.array(lsg_mfes),
        "lsg_mfe_atr": np.array(lsg_mfe_atr) if lsg_mfe_atr else np.array([0]),
        "loser_maes": np.array(loser_maes),
        "loser_pnls": np.array(loser_pnls),
        "grade_lsg": grade_lsg,
        "stage_lsg": stage_lsg,
        "be_estimates": be_estimates,
        "winner_hold_bars": np.array(winner_hold),
        "loser_hold_bars": np.array(loser_hold),
        "lsg_hold_bars": np.array(lsg_hold),
    }


def format_report(analysis, coins_tested, params):
    """Format full diagnostic report as markdown."""
    a = analysis
    lines = []

    lines.append("# v3.8.2 LSG Diagnostic Report\n")
    lines.append(f"**Coins tested**: {coins_tested}")
    lines.append(f"**Notional**: ${params['notional']:,.0f}/position")
    lines.append(f"**Commission**: taker {params['commission_rate']*100:.2f}%/side, maker {params['maker_rate']*100:.2f}%/side")
    lines.append(f"**Rebate**: {params['rebate_pct']*100:.0f}%\n")

    lines.append("## Overall\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total trades | {a['total']:,} |")
    lines.append(f"| Winners | {a['winners']:,} ({a['winners']/max(a['total'],1):.0%}) |")
    lines.append(f"| Losers | {a['losers']:,} ({a['losers']/max(a['total'],1):.0%}) |")
    lines.append(f"| **Losers saw green** | **{a['lsg_count']:,} ({a['lsg_rate']:.1%})** |")
    lines.append(f"| Avg loser P&L | ${np.mean(a['loser_pnls']):.2f} |")
    lines.append(f"| Avg loser MAE | ${np.mean(a['loser_maes']):.2f} |")

    lines.append(f"\n## LSG MFE Distribution (dollar terms)\n")
    mfes = a["lsg_mfes"]
    if len(mfes) > 0 and np.sum(mfes) > 0:
        lines.append(f"| Percentile | MFE ($) |")
        lines.append(f"|------------|---------|")
        for p in [10, 25, 50, 75, 90]:
            lines.append(f"| P{p} | ${np.percentile(mfes, p):.2f} |")
        lines.append(f"| Mean | ${np.mean(mfes):.2f} |")
        lines.append(f"| Max | ${np.max(mfes):.2f} |")

    lines.append(f"\n## LSG MFE as ATR Multiple\n")
    mfe_atr = a["lsg_mfe_atr"]
    if len(mfe_atr) > 0 and np.sum(mfe_atr) > 0:
        lines.append(f"| Percentile | ATR mult |")
        lines.append(f"|------------|----------|")
        for p in [10, 25, 50, 75, 90]:
            lines.append(f"| P{p} | {np.percentile(mfe_atr, p):.3f} |")
        lines.append(f"| Mean | {np.mean(mfe_atr):.3f} |")

    lines.append(f"\n## LSG by Grade\n")
    lines.append(f"| Grade | Losers | Saw Green | LSG% |")
    lines.append(f"|-------|--------|-----------|------|")
    for grade, info in a["grade_lsg"].items():
        lines.append(f"| {grade} | {info['losers']:,} | {info['saw_green']:,} | {info['rate']:.1%} |")

    lines.append(f"\n## LSG by Exit Stage\n")
    lines.append(f"| Stage | Losers | Saw Green | LSG% | Avg Loss |")
    lines.append(f"|-------|--------|-----------|------|----------|")
    for stage, info in a["stage_lsg"].items():
        lines.append(f"| {stage} | {info['losers']:,} | {info['saw_green']:,} | {info['rate']:.1%} | ${info['avg_loss']:.2f} |")

    lines.append(f"\n## BE Raise Conversion Estimates\n")
    lines.append(f"Assumes BE raise converts loser to $0 P&L (breakeven). 'Saved' = abs(loser net P&L).\n")
    lines.append(f"| Trigger (ATR) | Convertible | % of LSG | % of Losers | Total Saved | Avg Saved/Trade |")
    lines.append(f"|---------------|-------------|----------|-------------|-------------|-----------------|")
    for trigger, info in a["be_estimates"].items():
        lines.append(
            f"| {trigger:.2f} | {info['convertible']:,} | {info['pct_of_lsg']:.1%} | "
            f"{info['pct_of_losers']:.1%} | ${info['saved_pnl']:,.2f} | ${info['saved_per_trade']:.2f} |"
        )

    lines.append(f"\n## Hold Time (bars, 5m = 25min/bar on chart)\n")
    lines.append(f"| Category | Avg | Median | P10 | P90 |")
    lines.append(f"|----------|-----|--------|-----|-----|")
    for name, arr in [("Winners", a["winner_hold_bars"]),
                       ("Losers", a["loser_hold_bars"]),
                       ("LSG Losers", a["lsg_hold_bars"])]:
        if len(arr) > 0:
            lines.append(
                f"| {name} | {np.mean(arr):.1f} | {np.median(arr):.0f} | "
                f"{np.percentile(arr, 10):.0f} | {np.percentile(arr, 90):.0f} |"
            )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="v3.8.2 LSG Diagnostic")
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
    print(f"Testing {len(selected)} coins: {', '.join(selected)}\n")

    all_trades = []
    for coin in selected:
        t0 = time.time()
        print(f"  {coin}...", end=" ", flush=True)
        trades, metrics = run_coin_trades(coin, params)
        elapsed = time.time() - t0
        if trades:
            n_lsg = sum(1 for t in trades if t.saw_green and t.pnl - t.commission <= 0)
            n_losers = sum(1 for t in trades if t.pnl - t.commission <= 0)
            lsg_pct = n_lsg / max(n_losers, 1)
            print(f"{len(trades)} trades, LSG {lsg_pct:.0%} ({elapsed:.1f}s)")
            all_trades.extend(trades)
        else:
            print(f"SKIP ({elapsed:.1f}s)")

    print(f"\nAnalyzing {len(all_trades):,} total trades...")
    analysis = analyze_lsg(all_trades, params["notional"])

    report = format_report(analysis, len(selected), params)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    print(f"\n{'=' * 55}")
    print(f"  LSG DIAGNOSTIC COMPLETE")
    print(f"  {analysis['total']:,} trades | LSG: {analysis['lsg_rate']:.1%}")
    print(f"  Report saved to: {out_path}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()

"""
Sweep TP multiplier for v3.8.4 on RIVERUSDT 5m.
Compares: no TP (v3.8.3 baseline) vs TP at 0.5, 0.75, 1.0, 1.25, 1.5, 2.0 ATR.
SL fixed at 2.5 ATR (best from v3.8.3 sweep).

Usage:
  python scripts/sweep_tp_v384.py
  python scripts/sweep_tp_v384.py --symbol KITEUSDT
  python scripts/sweep_tp_v384.py --sl-mult 2.0
"""

import argparse
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester_v384 import Backtester384

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def load_5m(symbol):
    path = CACHE_DIR / f"{symbol}_5m.parquet"
    if not path.exists():
        print(f"No 5m data for {symbol}")
        sys.exit(1)
    df = pd.read_parquet(path)
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})
    return df


def run_config(df_sig, sl_mult, tp_mult, rebate):
    params = {
        "notional": 5000.0,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": rebate,
        "max_positions": 4,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_mult": sl_mult,
        "tp_mult": tp_mult,
        "checkpoint_interval": 5,
        "max_scaleouts": 2,
        "enable_adds": True,
        "enable_reentry": True,
        "b_open_fresh": True,
    }
    bt = Backtester384(params)
    return bt.run(df_sig)


def main():
    parser = argparse.ArgumentParser(description="Sweep TP for v3.8.4")
    parser.add_argument("--symbol", type=str, default="RIVERUSDT")
    parser.add_argument("--sl-mult", type=float, default=2.5)
    parser.add_argument("--rebate", type=float, default=0.70)
    args = parser.parse_args()

    df_raw = load_5m(args.symbol)
    print(f"Loaded {len(df_raw)} 5m candles for {args.symbol}")

    # Compute signals once (same for all TP levels)
    sig_params = {
        "notional": 5000.0,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": args.rebate,
        "max_positions": 4,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_mult": args.sl_mult,
        "b_open_fresh": True,
    }
    df_sig = compute_signals_v383(df_raw.copy(), sig_params)
    print("Signals computed")

    # TP levels to sweep: None = no TP (v3.8.3 baseline)
    tp_levels = [None, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00]
    results = {}

    for tp in tp_levels:
        label = "none" if tp is None else f"{tp:.2f}"
        t0 = time.time()
        r = run_config(df_sig, args.sl_mult, tp, args.rebate)
        elapsed = time.time() - t0
        m = r["metrics"]
        results[label] = m
        net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
        tp_exits = m.get("tp_exits", 0)
        sl_exits = m.get("sl_exits", 0)
        print(f"  TP={label:>5}: {m['total_trades']:>5} trades, "
              f"{m['win_rate']:.0%} WR, ${net_ar:>10,.2f} net, "
              f"${net_ar/max(m['total_trades'],1):.2f}/tr, "
              f"TP={tp_exits} SL={sl_exits} ({elapsed:.1f}s)")

    # ── Summary Table ───────────────────────────────────────────
    out = []

    def p(s=""):
        print(s)
        out.append(s)

    p(f"\n{'=' * 90}")
    p(f"  TP SWEEP: v3.8.4 -- {args.symbol} (5m)")
    p(f"  SL: {args.sl_mult} ATR | Rebate: {args.rebate*100:.0f}% | Notional: $5,000")
    p(f"{'=' * 90}")

    p(f"\n  {'TP':>6} {'Trades':>7} {'WR':>6} {'Net(+reb)':>12} {'$/Trade':>9} "
      f"{'PF':>6} {'LSG%':>6} {'TP exits':>9} {'SL exits':>9} {'Scales':>7} "
      f"{'Volume':>12} {'MaxDD':>10}")
    p(f"  {'-'*6} {'-'*7} {'-'*6} {'-'*12} {'-'*9} "
      f"{'-'*6} {'-'*6} {'-'*9} {'-'*9} {'-'*7} "
      f"{'-'*12} {'-'*10}")

    for label, m in results.items():
        net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
        pt = net_ar / max(m["total_trades"], 1)
        tp_ex = m.get("tp_exits", 0)
        sl_ex = m.get("sl_exits", 0)
        sc = m.get("scale_out_count", 0)
        vol = m.get("total_volume", 0)
        lsg = m.get("pct_losers_saw_green", 0)
        dd = m.get("max_drawdown", 0)
        flag = " " if net_ar >= 0 else "<"
        p(f"  {label:>6} {m['total_trades']:>7,} {m['win_rate']:>5.0%} "
          f"${net_ar:>10,.2f} ${pt:>7.2f} "
          f"{m['profit_factor']:>5.2f} {lsg:>5.0%} "
          f"{tp_ex:>9,} {sl_ex:>9,} {sc:>7} "
          f"${vol:>10,.0f} ${dd:>8,.0f} {flag}")

    # ── Grade Breakdown per TP level ────────────────────────────
    p(f"\n  GRADE BREAKDOWN BY TP LEVEL")
    p(f"  {'-' * 80}")

    for label, m in results.items():
        if not m.get("grades"):
            continue
        p(f"\n  TP={label}:")
        p(f"    {'Grade':<6} {'Trades':>7} {'WR':>6} {'$/tr':>8} {'Total$':>10} {'TP exits':>9}")
        for grade in ["A", "B", "C", "D", "ADD", "RE", "R"]:
            g = m["grades"].get(grade, {})
            if not g:
                continue
            tp_g = g.get("tp_exits", 0)
            p(f"    {grade:<6} {g['count']:>7,} {g['win_rate']:>5.0%} "
              f"${g['avg_pnl']:>6.2f} ${g['total_pnl']:>8,.2f} {tp_g:>9}")

    # ── Comparison vs baseline (no TP) ──────────────────────────
    baseline = results.get("none", {})
    if baseline:
        base_net = baseline.get("net_pnl_after_rebate", baseline.get("net_pnl", 0))
        p(f"\n  DELTA vs BASELINE (no TP)")
        p(f"  {'-' * 60}")
        p(f"  {'TP':>6} {'Delta Net':>12} {'Delta $/tr':>12} {'Delta Trades':>13}")
        for label, m in results.items():
            if label == "none":
                continue
            net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
            delta_net = net_ar - base_net
            base_pt = base_net / max(baseline["total_trades"], 1)
            this_pt = net_ar / max(m["total_trades"], 1)
            delta_pt = this_pt - base_pt
            delta_trades = m["total_trades"] - baseline["total_trades"]
            p(f"  {label:>6} ${delta_net:>10,.2f} ${delta_pt:>10.2f} {delta_trades:>13,}")

    p(f"\n{'=' * 90}")

    # Save report
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / f"sweep_v384_tp_{args.symbol}.md"
    with open(report_path, "w") as f:
        f.write(f"# TP Sweep v3.8.4 -- {args.symbol} (5m)\n\n")
        f.write("```\n")
        f.write("\n".join(out))
        f.write("\n```\n")

    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()

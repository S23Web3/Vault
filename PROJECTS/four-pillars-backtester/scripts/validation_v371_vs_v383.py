"""
Validation: v3.7.1 vs v3.8.3 side-by-side on same coin/timeframe.
Captures stochastic 9,3 values and AVWAP position at every trade entry.

Usage:
  python scripts/validation_v371_vs_v383.py
  python scripts/validation_v371_vs_v383.py --symbol KITEUSDT
  python scripts/validation_v371_vs_v383.py --sl-mult 2.0
"""

import argparse
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signals.four_pillars import compute_signals
from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester import Backtester
from engine.backtester_v383 import Backtester383

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


def compute_daily_avwap(df):
    """Compute daily-anchored AVWAP: center + sigma at each bar.
    Resets at midnight UTC for market-level context."""
    n = len(df)
    avwap_center = np.full(n, np.nan)
    avwap_sigma = np.full(n, np.nan)

    hlc3 = (df["high"].values + df["low"].values + df["close"].values) / 3.0
    vol = df["base_vol"].values if "base_vol" in df.columns else np.ones(n)

    if "datetime" in df.columns:
        dts = pd.DatetimeIndex(df["datetime"].values)
    elif isinstance(df.index, pd.DatetimeIndex):
        dts = df.index
    else:
        dts = None

    cum_pv = 0.0
    cum_v = 0.0
    cum_pv2 = 0.0
    prev_date = None

    for i in range(n):
        if dts is not None:
            curr_date = dts[i].date()
            if prev_date is not None and curr_date != prev_date:
                cum_pv = 0.0
                cum_v = 0.0
                cum_pv2 = 0.0
            prev_date = curr_date

        v = max(vol[i], 1e-10)
        cum_pv += hlc3[i] * v
        cum_v += v
        cum_pv2 += (hlc3[i] ** 2) * v

        center = cum_pv / cum_v
        variance = (cum_pv2 / cum_v) - (center ** 2)
        sigma = np.sqrt(max(variance, 0.0))

        avwap_center[i] = center
        avwap_sigma[i] = sigma

    return avwap_center, avwap_sigma


def build_trade_df(trades, stoch_9, avwap_center, avwap_sigma, close, version):
    """Build DataFrame with stoch 9 and AVWAP context at each trade entry."""
    records = []
    for t in trades:
        bar = t.entry_bar
        if bar >= len(stoch_9):
            continue

        s9 = stoch_9[bar]
        ac = avwap_center[bar]
        asig = avwap_sigma[bar]
        price = close[bar]

        if asig > 0:
            avwap_dist_sigma = (price - ac) / asig
        else:
            avwap_dist_sigma = 0.0

        if t.direction == "LONG":
            right_side = price > ac
        else:
            right_side = price < ac

        is_winner = (t.pnl - t.commission) > 0

        records.append({
            "version": version,
            "direction": t.direction,
            "grade": t.grade,
            "entry_bar": t.entry_bar,
            "exit_bar": getattr(t, "exit_bar", 0),
            "entry_price": t.entry_price,
            "exit_price": getattr(t, "exit_price", 0),
            "pnl": t.pnl,
            "commission": t.commission,
            "net_pnl": t.pnl - t.commission,
            "mfe": t.mfe,
            "mae": t.mae,
            "exit_reason": t.exit_reason,
            "saw_green": t.saw_green,
            "winner": is_winner,
            "stoch_9": s9,
            "avwap_center": ac,
            "avwap_sigma": asig,
            "avwap_dist_sigma": avwap_dist_sigma,
            "right_side": right_side,
        })

    return pd.DataFrame(records)


def stoch_analysis_block(tdf, version):
    """Return list of output lines for stoch 9 analysis."""
    lines = []
    lines.append(f"\n  STOCH 9,3 AT ENTRY -- {version}")
    lines.append(f"  {'-' * 60}")

    winners = tdf[tdf["winner"]]
    losers = tdf[~tdf["winner"]]
    lsg = losers[losers["saw_green"]]

    def safe_stats(s):
        if len(s) == 0:
            return 0, 0, 0
        return s.mean(), s.median(), s.std()

    w_m, w_med, w_sd = safe_stats(winners["stoch_9"])
    l_m, l_med, l_sd = safe_stats(losers["stoch_9"])
    lsg_m, lsg_med, lsg_sd = safe_stats(lsg["stoch_9"])

    lines.append(f"  {'':20} {'Winners':>10} {'Losers':>10} {'LSG':>10}")
    lines.append(f"  {'Count':20} {len(winners):>10} {len(losers):>10} {len(lsg):>10}")
    lines.append(f"  {'Mean stoch_9':20} {w_m:>10.1f} {l_m:>10.1f} {lsg_m:>10.1f}")
    lines.append(f"  {'Median stoch_9':20} {w_med:>10.1f} {l_med:>10.1f} {lsg_med:>10.1f}")
    lines.append(f"  {'Stdev stoch_9':20} {w_sd:>10.1f} {l_sd:>10.1f} {lsg_sd:>10.1f}")

    # Distribution buckets
    lines.append(f"\n  Stoch 9 distribution at entry:")
    buckets = [(0, 15), (15, 25), (25, 35), (35, 50), (50, 65), (65, 75), (75, 85), (85, 100)]
    lines.append(f"  {'Range':>12} {'Winners':>10} {'Losers':>10} {'LSG':>10} {'WR':>8}")

    for lo, hi in buckets:
        mask_w = (winners["stoch_9"] >= lo) & (winners["stoch_9"] < hi)
        mask_l = (losers["stoch_9"] >= lo) & (losers["stoch_9"] < hi)
        mask_lsg = (lsg["stoch_9"] >= lo) & (lsg["stoch_9"] < hi)
        w_ct = mask_w.sum()
        l_ct = mask_l.sum()
        lsg_ct = mask_lsg.sum()
        total = w_ct + l_ct
        wr = w_ct / max(total, 1)
        lines.append(f"  {lo:>3}-{hi:<3}      {w_ct:>10} {l_ct:>10} {lsg_ct:>10} {wr:>7.0%}")

    # Long vs Short stoch 9
    for direction in ["LONG", "SHORT"]:
        subset = tdf[tdf["direction"] == direction]
        sw = subset[subset["winner"]]["stoch_9"]
        sl = subset[~subset["winner"]]["stoch_9"]
        lines.append(f"\n  {direction} entries: mean stoch_9 = {subset['stoch_9'].mean():.1f} "
                     f"(winners={sw.mean():.1f}, losers={sl.mean():.1f}, n={len(subset)})")

    # Per-grade
    lines.append(f"\n  Stoch 9 at entry by grade:")
    for grade in sorted(tdf["grade"].unique()):
        g = tdf[tdf["grade"] == grade]
        gw = g[g["winner"]]
        gl = g[~g["winner"]]
        gw_mean = gw["stoch_9"].mean() if len(gw) > 0 else 0
        gl_mean = gl["stoch_9"].mean() if len(gl) > 0 else 0
        lines.append(f"    {grade}: mean={g['stoch_9'].mean():.1f}, "
                     f"winners={gw_mean:.1f}, losers={gl_mean:.1f}, n={len(g)}")

    return lines


def avwap_analysis_block(tdf, version):
    """Return list of output lines for AVWAP position analysis."""
    lines = []
    lines.append(f"\n  AVWAP POSITION AT ENTRY -- {version}")
    lines.append(f"  {'-' * 60}")

    right = tdf[tdf["right_side"]]
    wrong = tdf[~tdf["right_side"]]

    lines.append(f"  Total trades:           {len(tdf)}")
    lines.append(f"  Right side of AVWAP:    {len(right)} ({len(right)/max(len(tdf),1):.0%})")
    lines.append(f"  Wrong side of AVWAP:    {len(wrong)} ({len(wrong)/max(len(tdf),1):.0%})")

    right_wr = right["winner"].mean() if len(right) > 0 else 0
    wrong_wr = wrong["winner"].mean() if len(wrong) > 0 else 0
    right_pnl = right["net_pnl"].mean() if len(right) > 0 else 0
    wrong_pnl = wrong["net_pnl"].mean() if len(wrong) > 0 else 0

    lines.append(f"  WR right side:          {right_wr:.1%}")
    lines.append(f"  WR wrong side:          {wrong_wr:.1%}")
    lines.append(f"  Avg P&L right side:     ${right_pnl:.2f}")
    lines.append(f"  Avg P&L wrong side:     ${wrong_pnl:.2f}")

    # AVWAP distance distribution
    lines.append(f"\n  AVWAP distance at entry (sigma units):")
    dist_buckets = [(-99, -3), (-3, -2), (-2, -1), (-1, 0), (0, 1), (1, 2), (2, 3), (3, 99)]
    labels = ["< -3s", "-3 to -2s", "-2 to -1s", "-1 to 0s", "0 to +1s", "+1 to +2s", "+2 to +3s", "> +3s"]

    lines.append(f"  {'Range':>12} {'Count':>8} {'%':>6} {'WR':>8} {'Avg P&L':>10}")
    for (lo, hi), label in zip(dist_buckets, labels):
        mask = (tdf["avwap_dist_sigma"] >= lo) & (tdf["avwap_dist_sigma"] < hi)
        bucket = tdf[mask]
        if len(bucket) > 0:
            wr = bucket["winner"].mean()
            avg_pnl = bucket["net_pnl"].mean()
            pct = len(bucket) / len(tdf)
            lines.append(f"  {label:>12} {len(bucket):>8} {pct:>5.0%} {wr:>7.0%} ${avg_pnl:>9.2f}")

    # By direction
    for direction in ["LONG", "SHORT"]:
        subset = tdf[tdf["direction"] == direction]
        if len(subset) == 0:
            continue
        r = subset[subset["right_side"]]
        w = subset[~subset["right_side"]]
        r_wr = r["winner"].mean() if len(r) > 0 else 0
        w_wr = w["winner"].mean() if len(w) > 0 else 0
        lines.append(f"\n  {direction}: right_side={len(r)}/{len(subset)} ({len(r)/len(subset):.0%}), "
                     f"WR right={r_wr:.0%}, WR wrong={w_wr:.0%}")

    # By grade
    lines.append(f"\n  AVWAP context by grade:")
    for grade in sorted(tdf["grade"].unique()):
        g = tdf[tdf["grade"] == grade]
        right_pct = g["right_side"].mean() if len(g) > 0 else 0
        avg_dist = g["avwap_dist_sigma"].mean() if len(g) > 0 else 0
        g_wr_right = g[g["right_side"]]["winner"].mean() if g["right_side"].sum() > 0 else 0
        g_wr_wrong = g[~g["right_side"]]["winner"].mean() if (~g["right_side"]).sum() > 0 else 0
        lines.append(f"    {grade}: {len(g)} trades, {right_pct:.0%} right side, "
                     f"avg dist={avg_dist:+.2f}s, WR right={g_wr_right:.0%}, WR wrong={g_wr_wrong:.0%}")

    return lines


def main():
    parser = argparse.ArgumentParser(description="Validation: v3.7.1 vs v3.8.3")
    parser.add_argument("--symbol", type=str, default="RIVERUSDT")
    parser.add_argument("--sl-mult", type=float, default=2.5, help="v3.8.3 SL multiplier")
    parser.add_argument("--notional", type=float, default=5000.0)
    parser.add_argument("--rebate", type=float, default=0.70)
    args = parser.parse_args()

    df_raw = load_5m(args.symbol)
    print(f"Loaded {len(df_raw)} 5m candles for {args.symbol}")

    # Daily-anchored AVWAP for context analysis
    avwap_center, avwap_sigma = compute_daily_avwap(df_raw)

    # ── Run v3.7.1 ──────────────────────────────────────────────
    print("Running v3.7.1...")
    df_v371 = df_raw.copy()
    df_v371 = compute_signals(df_v371, {
        "atr_length": 14,
        "cross_level": 25,
        "zone_level": 30,
        "stage_lookback": 10,
        "allow_b_trades": True,
        "allow_c_trades": True,
        "b_open_fresh": True,
        "cloud2_reentry": True,
        "reentry_lookback": 10,
    })

    bt_v371 = Backtester({
        "sl_mult": 1.0,
        "tp_mult": 1.5,
        "use_tp": True,
        "cooldown": 3,
        "b_open_fresh": True,
        "notional": args.notional,
        "commission_rate": 0.0008,
        "rebate_pct": args.rebate,
    })
    r371 = bt_v371.run(df_v371)
    m371 = r371["metrics"]
    m371["total_rebate"] = bt_v371.comm.total_rebate
    m371["net_pnl_after_rebate"] = m371["net_pnl"] + bt_v371.comm.total_rebate

    # ── Run v3.8.3 ──────────────────────────────────────────────
    print("Running v3.8.3...")
    df_v383 = df_raw.copy()
    params_383 = {
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
    df_v383 = compute_signals_v383(df_v383, params_383)
    bt_v383 = Backtester383(params_383)
    r383 = bt_v383.run(df_v383)
    m383 = r383["metrics"]

    # ── Build trade DataFrames with entry context ───────────────
    stoch_9_371 = df_v371["stoch_9"].values
    stoch_9_383 = df_v383["stoch_9"].values
    close_371 = df_v371["close"].values
    close_383 = df_v383["close"].values

    tdf_371 = build_trade_df(r371["trades"], stoch_9_371, avwap_center, avwap_sigma, close_371, "v3.7.1")
    tdf_383 = build_trade_df(r383["trades"], stoch_9_383, avwap_center, avwap_sigma, close_383, "v3.8.3")

    # ── Output ──────────────────────────────────────────────────
    out = []

    def p(s=""):
        print(s)
        out.append(s)

    p(f"\n{'=' * 72}")
    p(f"  VALIDATION: v3.7.1 vs v3.8.3 -- {args.symbol} (5m)")
    p(f"  Notional: ${args.notional:,.0f} | Rebate: {args.rebate*100:.0f}% | "
      f"v3.8.3 SL mult: {args.sl_mult}")
    p(f"{'=' * 72}")

    # ── Side-by-side ────────────────────────────────────────────
    p(f"\n  SIDE-BY-SIDE COMPARISON")
    p(f"  {'-' * 60}")

    net_371 = m371["net_pnl_after_rebate"]
    net_383 = m383.get("net_pnl_after_rebate", m383["net_pnl"])
    pt_371 = net_371 / max(m371["total_trades"], 1)
    pt_383 = net_383 / max(m383["total_trades"], 1)

    p(f"  {'':28} {'v3.7.1':>18} {'v3.8.3':>18}")
    p(f"  {'-'*28} {'-'*18} {'-'*18}")
    p(f"  {'Architecture':<28} {'pyr=1, TP=1.5ATR':>18} {'4-slot, scale-out':>18}")
    p(f"  {'SL':<28} {'1.0 ATR':>18} {f'{args.sl_mult} ATR':>18}")
    p(f"  {'Trades':<28} {m371['total_trades']:>18,} {m383['total_trades']:>18,}")
    p(f"  {'Win rate':<28} {m371['win_rate']:>17.1%} {m383['win_rate']:>17.1%}")
    p(f"  {'Net P&L (w/rebate)':<28} {'$'+f'{net_371:,.2f}':>18} {'$'+f'{net_383:,.2f}':>18}")
    p(f"  {'$/Trade (w/rebate)':<28} {'$'+f'{pt_371:.2f}':>18} {'$'+f'{pt_383:.2f}':>18}")

    gross_371 = m371["gross_profit"] - m371["gross_loss"]
    gross_383 = m383["gross_profit"] - m383["gross_loss"]
    comm_371 = m371["total_commission"]
    comm_383 = m383["total_commission"]
    reb_371 = m371["total_rebate"]
    reb_383 = m383.get("total_rebate", 0)
    dd_371 = m371["max_drawdown"]
    dd_383 = m383["max_drawdown"]
    p(f"  {'Gross P&L':<28} {'$'+f'{gross_371:,.2f}':>18} {'$'+f'{gross_383:,.2f}':>18}")
    p(f"  {'Commission':<28} {'$'+f'{comm_371:,.2f}':>18} {'$'+f'{comm_383:,.2f}':>18}")
    p(f"  {'Rebate':<28} {'$'+f'{reb_371:,.2f}':>18} {'$'+f'{reb_383:,.2f}':>18}")
    p(f"  {'Profit factor':<28} {m371['profit_factor']:>18.2f} {m383['profit_factor']:>18.2f}")
    p(f"  {'Sharpe':<28} {m371['sharpe']:>18.2f} {m383['sharpe']:>18.2f}")
    p(f"  {'Max DD':<28} {'$'+f'{dd_371:,.2f}':>18} {'$'+f'{dd_383:,.2f}':>18}")
    p(f"  {'Max DD %':<28} {m371['max_drawdown_pct']:>17.1f}% {m383['max_drawdown_pct']:>17.1f}%")
    p(f"  {'LSG%':<28} {m371['pct_losers_saw_green']:>17.0%} {m383['pct_losers_saw_green']:>17.0%}")
    p(f"  {'Scale-outs':<28} {'N/A':>18} {m383.get('scale_out_count', 0):>18}")

    # ── Grade Breakdown ─────────────────────────────────────────
    p(f"\n  GRADE BREAKDOWN")
    p(f"  {'-' * 60}")

    all_grades = set()
    if m371.get("grades"):
        all_grades.update(m371["grades"].keys())
    if m383.get("grades"):
        all_grades.update(m383["grades"].keys())

    grade_order = ["A", "B", "C", "D", "ADD", "RE", "R"]
    sorted_grades = [g for g in grade_order if g in all_grades]

    p(f"  {'Grade':<8} {'v3.7.1 Trades':>14} {'WR':>6} {'$/tr':>8}"
      f" {'v3.8.3 Trades':>14} {'WR':>6} {'$/tr':>8}")
    p(f"  {'-'*8} {'-'*14} {'-'*6} {'-'*8} {'-'*14} {'-'*6} {'-'*8}")

    for grade in sorted_grades:
        g371 = m371.get("grades", {}).get(grade, {})
        g383 = m383.get("grades", {}).get(grade, {})
        c371 = g371.get("count", 0)
        c383 = g383.get("count", 0)
        wr371 = g371.get("win_rate", 0)
        wr383 = g383.get("win_rate", 0)
        pnl371 = g371.get("avg_pnl", 0)
        pnl383 = g383.get("avg_pnl", 0)
        p(f"  {grade:<8} {c371:>14,} {wr371:>5.0%} ${pnl371:>6.2f}"
          f" {c383:>14,} {wr383:>5.0%} ${pnl383:>6.2f}")

    # ── Stochastic 9,3 Analysis ─────────────────────────────────
    for block_lines in [stoch_analysis_block(tdf_371, "v3.7.1"),
                        stoch_analysis_block(tdf_383, "v3.8.3")]:
        for line in block_lines:
            p(line)

    # ── AVWAP Analysis ──────────────────────────────────────────
    for block_lines in [avwap_analysis_block(tdf_371, "v3.7.1"),
                        avwap_analysis_block(tdf_383, "v3.8.3")]:
        for line in block_lines:
            p(line)

    # ── Key Findings ────────────────────────────────────────────
    p(f"\n  KEY FINDINGS")
    p(f"  {'-' * 60}")

    ratio = m383["total_trades"] / max(m371["total_trades"], 1)
    p(f"  v3.8.3 generates {ratio:.1f}x the trades of v3.7.1")

    delta = net_383 - net_371
    p(f"  Net P&L delta: ${delta:,.2f} ({'v3.8.3 better' if delta > 0 else 'v3.7.1 better'})")
    p(f"  $/trade: v3.7.1=${pt_371:.2f}, v3.8.3=${pt_383:.2f}")

    # Stoch 9 comparison
    if len(tdf_371) > 0 and len(tdf_383) > 0:
        w371_s9 = tdf_371[tdf_371["winner"]]["stoch_9"].mean()
        l371_s9 = tdf_371[~tdf_371["winner"]]["stoch_9"].mean()
        w383_s9 = tdf_383[tdf_383["winner"]]["stoch_9"].mean()
        l383_s9 = tdf_383[~tdf_383["winner"]]["stoch_9"].mean()
        p(f"  Stoch 9 at entry (winners): v3.7.1={w371_s9:.1f}, v3.8.3={w383_s9:.1f}")
        p(f"  Stoch 9 at entry (losers):  v3.7.1={l371_s9:.1f}, v3.8.3={l383_s9:.1f}")

    # AVWAP right side
    if len(tdf_371) > 0 and len(tdf_383) > 0:
        right_371 = tdf_371["right_side"].mean()
        right_383 = tdf_383["right_side"].mean()
        right_371_wr = tdf_371[tdf_371["right_side"]]["winner"].mean() if tdf_371["right_side"].sum() > 0 else 0
        right_383_wr = tdf_383[tdf_383["right_side"]]["winner"].mean() if tdf_383["right_side"].sum() > 0 else 0
        p(f"  AVWAP right side: v3.7.1={right_371:.0%} (WR={right_371_wr:.0%}), "
          f"v3.8.3={right_383:.0%} (WR={right_383_wr:.0%})")

    # Commission economics
    comm_371 = m371["total_commission"]
    comm_383 = m383["total_commission"]
    rebate_371 = m371["total_rebate"]
    rebate_383 = m383.get("total_rebate", 0)
    p(f"\n  Commission economics:")
    p(f"    v3.7.1: ${comm_371:,.0f} commission, ${rebate_371:,.0f} rebate, "
      f"${comm_371 - rebate_371:,.0f} net cost")
    p(f"    v3.8.3: ${comm_383:,.0f} commission, ${rebate_383:,.0f} rebate, "
      f"${comm_383 - rebate_383:,.0f} net cost")

    p(f"\n{'=' * 72}")

    # Save report
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / f"validation_v371_vs_v383_{args.symbol}.md"
    with open(report_path, "w") as f:
        f.write(f"# Validation: v3.7.1 vs v3.8.3 -- {args.symbol} (5m)\n\n")
        f.write("```\n")
        f.write("\n".join(out))
        f.write("\n```\n")

    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()

"""
Stage 2 rotation filter comparison.
Runs both pipelines (require_stage2=False vs True) on all available 5m cached data.
Outputs signal count table and, if Backtester384 is importable, full PnL comparison.

Run: python scripts/compare_stage2.py
Run: python scripts/compare_stage2.py --coins APTUSDT RIVERUSDT SUIUSDT
Run: python scripts/compare_stage2.py --rot-level 75
"""

import sys
import logging
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from signals.four_pillars import compute_signals

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

CACHE_DIR = ROOT / "data" / "cache"

# Default params matching run_backtest_v384.py
BT_PARAMS = {
    "commission_rate": 0.0008,
    "maker_rate": 0.0002,
    "rebate_pct": 0.70,
    "notional": 500.0,
    "cooldown": 3,
    "max_positions": 4,
    "sl_mult": 2.5,
    "tp_mult": None,
    "checkpoint_interval": 5,
    "max_scaleouts": 2,
    "sigma_floor_atr": 0.5,
    "enable_adds": True,
    "enable_reentry": True,
    "b_open_fresh": True,
    "allow_b_trades": True,
    "allow_c_trades": False,  # Grade C off by default
}


def load_df(symbol, timeframe="5m"):
    """Load cached parquet for symbol. Returns None if missing."""
    path = CACHE_DIR / (symbol + "_" + timeframe + ".parquet")
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    for old, new in [("volume", "base_vol"), ("turnover", "quote_vol")]:
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    return df


def count_sigs(df):
    """Count signal columns in a computed DataFrame."""
    return {
        "long_a":  int(df["long_a"].sum()),
        "short_a": int(df["short_a"].sum()),
        "long_b":  int(df["long_b"].sum()),
        "short_b": int(df["short_b"].sum()),
    }


def run_bt(df, params):
    """Run Backtester384 on pre-computed signals df. Returns metrics dict or None."""
    try:
        from engine.backtester_v384 import Backtester384
        bt = Backtester384(params)
        results = bt.run(df)
        return results.get("metrics", {})
    except Exception as e:
        log.warning("Backtester384 unavailable: %s", e)
        return None


def pf(before, after):
    """Format filtered pct string."""
    if before == 0:
        return "  n/a"
    return str(int(round((before - after) / before * 100))) + "%"


def run_coin(symbol, timeframe, rot_level, with_bt):
    """Run baseline vs Stage 2 comparison for one coin."""
    df = load_df(symbol, timeframe)
    if df is None:
        log.warning("No cache: %s_%s", symbol, timeframe)
        return None

    bars = len(df)

    params_base = dict(BT_PARAMS)
    params_base["require_stage2"] = False
    params_base["rot_level"] = rot_level

    params_s2 = dict(BT_PARAMS)
    params_s2["require_stage2"] = True
    params_s2["rot_level"] = rot_level

    df_base = compute_signals(df.copy(), params_base)
    df_s2   = compute_signals(df.copy(), params_s2)

    sigs_base = count_sigs(df_base)
    sigs_s2   = count_sigs(df_s2)

    metrics_base = run_bt(df_base, params_base) if with_bt else None
    metrics_s2   = run_bt(df_s2,   params_s2)   if with_bt else None

    return {
        "symbol":      symbol,
        "bars":        bars,
        "sigs_base":   sigs_base,
        "sigs_s2":     sigs_s2,
        "metrics_base": metrics_base,
        "metrics_s2":   metrics_s2,
    }


def print_signal_table(rows):
    """Print signal count comparison table."""
    print()
    print("=" * 90)
    print("  SIGNAL COUNT: Baseline vs Stage 2 (rot_level=80 means Stoch40/60 must cross 80/20)")
    print("=" * 90)
    hdr = (
        "  {:<16} {:>6} {:>6} {:>5}   {:>6} {:>6} {:>5}   {:>6} {:>6} {:>5}   {:>6} {:>6} {:>5}"
    )
    row_fmt = (
        "  {:<16} {:>6} {:>6} {:>5}   {:>6} {:>6} {:>5}   {:>6} {:>6} {:>5}   {:>6} {:>6} {:>5}"
    )
    print(hdr.format(
        "Symbol",
        "LA_b", "LA_s2", "Filt",
        "SA_b", "SA_s2", "Filt",
        "LB_b", "LB_s2", "Filt",
        "SB_b", "SB_s2", "Filt",
    ))
    print("  " + "-" * 88)

    totals_b = {"long_a": 0, "short_a": 0, "long_b": 0, "short_b": 0}
    totals_s = {"long_a": 0, "short_a": 0, "long_b": 0, "short_b": 0}

    for r in rows:
        b = r["sigs_base"]
        s = r["sigs_s2"]
        for k in totals_b:
            totals_b[k] += b[k]
            totals_s[k] += s[k]
        print(row_fmt.format(
            r["symbol"],
            b["long_a"],  s["long_a"],  pf(b["long_a"],  s["long_a"]),
            b["short_a"], s["short_a"], pf(b["short_a"], s["short_a"]),
            b["long_b"],  s["long_b"],  pf(b["long_b"],  s["long_b"]),
            b["short_b"], s["short_b"], pf(b["short_b"], s["short_b"]),
        ))

    print("  " + "-" * 88)
    print(row_fmt.format(
        "TOTAL",
        totals_b["long_a"],  totals_s["long_a"],  pf(totals_b["long_a"],  totals_s["long_a"]),
        totals_b["short_a"], totals_s["short_a"], pf(totals_b["short_a"], totals_s["short_a"]),
        totals_b["long_b"],  totals_s["long_b"],  pf(totals_b["long_b"],  totals_s["long_b"]),
        totals_b["short_b"], totals_s["short_b"], pf(totals_b["short_b"], totals_s["short_b"]),
    ))
    print("=" * 90)
    print("  Columns: LA=LongA  SA=ShortA  LB=LongB  SB=ShortB  _b=baseline  _s2=Stage2")
    print("  Filt = % signals blocked by Stage 2 (Stoch40 AND Stoch60 must rotate before firing)")
    print()


def print_pnl_table(rows):
    """Print PnL comparison table if backtester results available."""
    has_bt = any(r["metrics_base"] is not None for r in rows)
    if not has_bt:
        return

    print("=" * 80)
    print("  PnL COMPARISON: Baseline vs Stage 2")
    print("=" * 80)
    hdr = "  {:<16}  {:>6}  {:>6}  {:>6}  {:>9}  {:>9}  {:>8}  {:>8}"
    print(hdr.format(
        "Symbol", "Tr_b", "Tr_s2",
        "WR_b", "WR_s2",
        "Exp_b", "Exp_s2",
        "PnL_b", "PnL_s2",
    ))
    print("  " + "-" * 78)

    for r in rows:
        mb = r["metrics_base"]
        ms = r["metrics_s2"]
        if mb is None or ms is None:
            continue
        print(hdr.format(
            r["symbol"],
            mb.get("total_trades", 0),
            ms.get("total_trades", 0),
            str(int(round(mb.get("win_rate", 0) * 100))) + "%",
            str(int(round(ms.get("win_rate", 0) * 100))) + "%",
            "$" + str(round(mb.get("expectancy", 0), 2)),
            "$" + str(round(ms.get("expectancy", 0), 2)),
            "$" + str(round(mb.get("net_pnl", 0), 0)),
            "$" + str(round(ms.get("net_pnl", 0), 0)),
        ))

    print("=" * 80)
    print()


def main():
    """Entry point — parse args, run comparisons, print tables."""
    parser = argparse.ArgumentParser(description="Compare Stage 2 rotation filter vs baseline")
    parser.add_argument("--coins",     nargs="*", default=None,
                        help="Symbols to test (default: all 5m cached)")
    parser.add_argument("--timeframe", default="5m", choices=["1m", "5m"])
    parser.add_argument("--rot-level", type=int, default=80,
                        help="Rotation threshold (SHORT: Stoch must cross below this, LONG: above 100-this)")
    parser.add_argument("--no-bt",    action="store_true",
                        help="Skip backtester (signal count only, much faster)")
    parser.add_argument("--limit",    type=int, default=None,
                        help="Max number of coins to process")
    args = parser.parse_args()

    rot_level = args.rot_level
    with_bt = not args.no_bt

    if args.coins:
        symbols = args.coins
    else:
        symbols = sorted(
            p.stem.replace("_" + args.timeframe, "")
            for p in CACHE_DIR.glob("*_" + args.timeframe + ".parquet")
        )
        log.info("Auto-detected %d cached %s coins", len(symbols), args.timeframe)
        if args.limit:
            symbols = symbols[:args.limit]

    log.info("rot_level=%d  backtester=%s  coins=%d", rot_level, with_bt, len(symbols))

    rows = []
    for sym in symbols:
        log.info("[%d/%d] %s", len(rows) + 1, len(symbols), sym)
        r = run_coin(sym, args.timeframe, rot_level, with_bt)
        if r:
            rows.append(r)

    if not rows:
        log.error("No results — check cache dir: %s", str(CACHE_DIR))
        return

    print_signal_table(rows)
    print_pnl_table(rows)


if __name__ == "__main__":
    main()

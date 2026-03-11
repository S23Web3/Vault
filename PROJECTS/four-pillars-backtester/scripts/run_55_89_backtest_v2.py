"""
Verification runner for 55/89 EMA Cross Scalp (Backtester5589).

Loads parquet, computes signals, runs Backtester5589, prints phase breakdown
and diagnostic verification assertions.

Run: python scripts/run_55_89_backtest_v2.py --symbol BTCUSDT --months 1
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from signals.ema_cross_55_89 import compute_signals_55_89
from engine.backtester_55_89 import Backtester5589

log = logging.getLogger(__name__)


def load_parquet(symbol: str, months: int | None) -> pd.DataFrame:
    """Load 1m parquet for symbol from data/historical/ or data/cache/; filter to last N months if given."""
    for subdir in ["historical", "cache"]:
        path = ROOT / "data" / subdir / (symbol + "_1m.parquet")
        if path.exists():
            df = pd.read_parquet(path)
            if months is not None and "datetime" in df.columns:
                cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=months * 30)
                df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
                df = df[df["datetime"] >= cutoff].reset_index(drop=True)
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print("[" + ts + "] Loaded " + str(len(df)) + " bars from " + str(path))
            return df
    print("ERROR: No parquet found for " + symbol)
    sys.exit(1)


def pct_of(n: int, total: int) -> str:
    """Format n as a percentage of total; return '  0.0%' if total is zero."""
    if total == 0:
        return "  0.0%"
    return "{:5.1f}%".format(n / total * 100)


def main() -> None:
    """Run Backtester5589 on real data; print phase breakdown and verification result."""
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="55/89 EMA Cross Scalp Verification Runner (Backtester5589)")
    parser.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
    parser.add_argument("--months", type=int, default=1, help="Limit to last N months (default: 1)")
    parser.add_argument("--sl-mult", type=float, default=2.5, help="SL ATR multiplier (default: 2.5)")
    parser.add_argument("--avwap-sigma", type=float, default=2.0, help="AVWAP sigma band (default: 2.0)")
    parser.add_argument("--avwap-warmup", type=int, default=5, help="AVWAP warmup bars (default: 5)")
    parser.add_argument("--tp-atr-offset", type=float, default=0.5, help="TP ATR offset (default: 0.5)")
    parser.add_argument("--ratchet-threshold", type=int, default=2, help="Ratchets before TP activates (default: 2)")
    parser.add_argument("--slope-n", type=int, default=5, help="Signal slope window N (default: 5)")
    parser.add_argument("--slope-m", type=int, default=3, help="Signal accel window M (default: 3)")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print("[" + ts + "] 55/89 EMA Cross Scalp -- Backtester5589 Verification")
    print("[" + ts + "] Symbol=" + args.symbol
          + " | months=" + str(args.months)
          + " | sl_mult=" + str(args.sl_mult)
          + " | avwap_sigma=" + str(args.avwap_sigma)
          + " | ratchet_threshold=" + str(args.ratchet_threshold))

    df = load_parquet(args.symbol, args.months)

    sig_params = {"slope_n": args.slope_n, "slope_m": args.slope_m}

    bt_params = {
        "sl_mult": args.sl_mult,
        "avwap_sigma": args.avwap_sigma,
        "avwap_warmup": args.avwap_warmup,
        "tp_atr_offset": args.tp_atr_offset,
        "ratchet_threshold": args.ratchet_threshold,
        "notional": 5000.0,
        "initial_equity": 10000.0,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": 0.70,
    }

    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print("[" + ts + "] Computing signals...")
    df_sig = compute_signals_55_89(df.copy(), sig_params)

    long_count = int(df_sig["long_a"].sum())
    short_count = int(df_sig["short_a"].sum())

    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print("[" + ts + "] Running Backtester5589...")
    bt = Backtester5589(bt_params)
    results = bt.run(df_sig)
    m = results["metrics"]

    total = m.get("total_trades", 0)
    p1 = m.get("phase1_exits", 0)
    p2 = m.get("phase2_exits", 0)
    p3 = m.get("phase3_exits", 0)
    p4 = m.get("phase4_exits", 0)
    avg_r = m.get("avg_ratchet_count", 0.0)
    ratchet_hit_pct = m.get("ratchet_threshold_hit_pct", 0.0)

    print("")
    print("=== SIGNALS ===")
    print("  Long signals:   " + str(long_count))
    print("  Short signals:  " + str(short_count))

    print("")
    print("=== RESULTS ===")
    print("  Total trades:   " + str(total))
    print("  Win rate:       " + "{:.1%}".format(m.get("win_rate", 0.0)))
    print("  Net PnL:        $" + "{:.2f}".format(m.get("net_pnl", 0.0)))
    print("  Expectancy:     $" + "{:.2f}".format(m.get("expectancy", 0.0)))
    print("  Profit factor:  " + "{:.2f}".format(m.get("profit_factor", 0.0)))
    print("  Commission:     $" + "{:.2f}".format(m.get("total_commission", 0.0)))
    print("  Rebate:         $" + "{:.2f}".format(m.get("total_rebate", 0.0)))

    print("")
    print("=== PHASE BREAKDOWN ===")
    print("  Phase 1 exits (ATR SL):        " + str(p1) + "  (" + pct_of(p1, total) + ")")
    print("  Phase 2 exits (AVWAP freeze):  " + str(p2) + "  (" + pct_of(p2, total) + ")")
    print("  Phase 3 exits (ratchet SL):    " + str(p3) + "  (" + pct_of(p3, total) + ")")
    print("  Phase 4 exits (TP):            " + str(p4) + "  (" + pct_of(p4, total) + ")")
    print("  Avg ratchet count:             " + "{:.2f}".format(avg_r))
    print("  Ratchet threshold hit:         " + "{:.1%}".format(ratchet_hit_pct))

    print("")
    print("=== VERIFICATION ===")
    failures = []

    if p2 + p3 + p4 > 0:
        print("  [PASS] AVWAP phases fired (phase2+3+4=" + str(p2 + p3 + p4) + " > 0)")
    else:
        print("  [FAIL] AVWAP phases did NOT fire (phase2+3+4=0)")
        print("         All exits are phase 1 (ATR SL only). Try: --avwap-warmup 3 --avwap-sigma 1.5")
        print("         or a longer date range: --months 3")
        failures.append("AVWAP phases did not fire")

    if avg_r > 0.0:
        print("  [PASS] Ratchets occurred (avg_ratchet_count=" + "{:.2f}".format(avg_r) + " > 0)")
    else:
        print("  [FAIL] No ratchets occurred (avg=0.0)")
        print("         Stoch-9-D may not be crossing overzone. Try: --months 3 or a different symbol.")
        failures.append("No ratchets occurred")

    print("")
    if failures:
        print("VERIFICATION FAILED: " + " | ".join(failures))
        sys.exit(1)
    else:
        print("VERIFICATION PASSED -- engine swap to Backtester5589 is safe to proceed.")


if __name__ == "__main__":
    main()

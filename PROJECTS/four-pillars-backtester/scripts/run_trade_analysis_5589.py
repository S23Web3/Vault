"""
Batch trade extraction for 55/89 EMA Cross Scalp v2.
Runs signals + engine on each coin in the portfolio, saves trades_df to CSV.
Run: python scripts/run_trade_analysis_5589.py
"""
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signals.ema_cross_55_89_v2 import compute_signals_55_89
from engine.backtester_55_89 import Backtester5589

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

COINS = [
    "FILUSDT",
    "OGUSDT",
    "CHZUSDT",
    "ORDERUSDT",
    "BIGTIMEUSDT",
    "CVCUSDT",
    "BBUSDT",
    "MEUSDT",
    "TRUMPUSDT",
    "CETUSUSDT",
]

DATE_FROM = "2025-04-09"
DATE_TO   = "2025-05-09"

PARAMS = {
    "sl_mult":         2.5,
    "avwap_sigma":     2.0,
    "avwap_warmup":    5,
    "tp_atr_offset":   0.5,
    "ratchet_threshold": 2,
    "notional":        10000.0,
    "initial_equity":  10000.0,
    "commission_rate": 0.0008,
    "rebate_pct":      0.70,
    "min_signal_gap":  50,
}

RESULTS_DIR = ROOT / "results"
DATA_DIR    = ROOT / "data" / "historical"


def load_parquet(symbol: str) -> pd.DataFrame:
    """Load 1m parquet for symbol; filter to DATE_FROM/DATE_TO window."""
    path = DATA_DIR / (symbol + "_1m.parquet")
    if not path.exists():
        log.warning("No parquet for " + symbol + " at " + str(path))
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if "datetime" not in df.columns and df.index.name == "datetime":
        df = df.reset_index()
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        t0 = pd.Timestamp(DATE_FROM, tz="UTC")
        t1 = pd.Timestamp(DATE_TO,   tz="UTC")
        df = df[(df["datetime"] >= t0) & (df["datetime"] <= t1)].reset_index(drop=True)
    log.info(symbol + ": loaded " + str(len(df)) + " bars")
    return df


def run_coin(symbol: str) -> pd.DataFrame:
    """Run full pipeline for one coin; return trades_df with symbol + datetime cols."""
    df = load_parquet(symbol)
    if df.empty:
        return pd.DataFrame()

    df_sig = compute_signals_55_89(df.copy(), PARAMS)
    bt = Backtester5589(PARAMS)
    results = bt.run(df_sig)
    trades_df = results.get("trades_df", pd.DataFrame())

    if trades_df.empty:
        log.warning(symbol + ": 0 trades")
        return pd.DataFrame()

    trades_df = trades_df.copy()
    trades_df["symbol"] = symbol

    if "datetime" in df_sig.columns:
        dt_arr = df_sig["datetime"].values
    elif df_sig.index.name == "datetime":
        dt_arr = df_sig.index.values
    else:
        dt_arr = None

    if dt_arr is not None:
        n_bars = len(dt_arr)
        trades_df["entry_datetime"] = trades_df["entry_bar"].apply(
            lambda b: dt_arr[int(b)] if int(b) < n_bars else None
        )
        trades_df["exit_datetime"] = trades_df["exit_bar"].apply(
            lambda b: dt_arr[int(b)] if int(b) < n_bars else None
        )

    m = results["metrics"]
    total  = m.get("total_trades", 0)
    wr     = m.get("win_rate", 0.0)
    p1     = m.get("phase1_exits", 0)
    p2     = m.get("phase2_exits", 0)
    p3     = m.get("phase3_exits", 0)
    p4     = m.get("phase4_exits", 0)
    be_ct  = m.get("be_raised_count", 0)
    rh_pct = m.get("ratchet_threshold_hit_pct", 0.0)
    net    = m.get("net_pnl", 0.0)

    log.info(
        symbol + ": trades=" + str(total)
        + " WR=" + "{:.1%}".format(wr)
        + " net=$" + "{:.2f}".format(net)
        + " P1=" + str(p1)
        + " P2=" + str(p2)
        + " P3=" + str(p3)
        + " P4=" + str(p4)
        + " BE=" + str(be_ct)
        + " ratchet_hit=" + "{:.1%}".format(rh_pct)
    )
    return trades_df


def main() -> None:
    """Run pipeline for all COINS; save per-coin CSV to results/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log.info("=== run_trade_analysis_5589 started " + ts + " ===")
    log.info("Date range: " + DATE_FROM + " to " + DATE_TO)
    log.info("Coins: " + ", ".join(COINS))

    all_frames = []
    for symbol in COINS:
        trades_df = run_coin(symbol)
        if trades_df.empty:
            continue
        out = RESULTS_DIR / ("trades_5589_" + symbol + ".csv")
        trades_df.to_csv(out, index=False)
        log.info("  Saved: " + str(out))
        all_frames.append(trades_df)

    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combined_out = RESULTS_DIR / "trades_5589_ALL.csv"
        combined.to_csv(combined_out, index=False)
        log.info("Combined CSV: " + str(combined_out) + " (" + str(len(combined)) + " trades)")

    log.info("=== done ===")


if __name__ == "__main__":
    main()

"""
Trade visualisation for 55/89 EMA Cross Scalp v2.
For each coin, renders a matplotlib grid of up to 50 trades (20 per page).
Run: python scripts/visualise_5589_trades.py
"""
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    "sl_mult":           2.5,
    "avwap_sigma":       2.0,
    "avwap_warmup":      5,
    "tp_atr_offset":     0.5,
    "ratchet_threshold": 2,
    "notional":          10000.0,
    "initial_equity":    10000.0,
    "commission_rate":   0.0008,
    "rebate_pct":        0.70,
    "min_signal_gap":    50,
}

RESULTS_DIR     = ROOT / "results"
DATA_DIR        = ROOT / "data" / "historical"
PRE_BARS        = 10
POST_BARS       = 5
TRADES_PER_PAGE = 20
MAX_TRADES      = 50
COLS            = 5
ROWS            = 4

NL = "\n"


def load_and_run(symbol: str):
    """Load parquet, run signals + engine; return (df_sig, trades_df) or (None, None)."""
    path = DATA_DIR / (symbol + "_1m.parquet")
    if not path.exists():
        log.warning("No parquet for " + symbol)
        return None, None
    df = pd.read_parquet(path)
    if "datetime" not in df.columns and df.index.name == "datetime":
        df = df.reset_index()
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        t0 = pd.Timestamp(DATE_FROM, tz="UTC")
        t1 = pd.Timestamp(DATE_TO,   tz="UTC")
        df = df[(df["datetime"] >= t0) & (df["datetime"] <= t1)].reset_index(drop=True)
    if df.empty:
        log.warning(symbol + ": no bars in date range")
        return None, None
    df_sig = compute_signals_55_89(df.copy(), PARAMS)
    bt = Backtester5589(PARAMS)
    results = bt.run(df_sig)
    trades_df = results.get("trades_df", pd.DataFrame())
    if trades_df.empty:
        log.warning(symbol + ": 0 trades")
        return df_sig, pd.DataFrame()
    return df_sig, trades_df


def render_trade(ax, trade: dict, df_sig: pd.DataFrame, trade_idx: int) -> None:
    """Render one trade into matplotlib Axes ax."""
    entry_bar = int(trade["entry_bar"])
    exit_bar  = int(trade["exit_bar"])
    direction = trade.get("direction", "LONG")
    pnl       = trade.get("pnl", 0.0)
    grade     = trade.get("trade_grade", "")
    exit_rsn  = trade.get("exit_reason", "")
    be_trig   = bool(trade.get("ema_be_triggered", False))
    ratchets  = int(trade.get("ratchet_count", 0))

    n_bars    = len(df_sig)
    win_start = max(0, entry_bar - PRE_BARS)
    win_end   = min(n_bars - 1, exit_bar + POST_BARS)

    close = df_sig["close"].values
    ema55 = df_sig["ema_55"].values    if "ema_55"     in df_sig.columns else np.full(n_bars, np.nan)
    ema89 = df_sig["ema_89"].values    if "ema_89"     in df_sig.columns else np.full(n_bars, np.nan)
    atr   = df_sig["atr"].values       if "atr"        in df_sig.columns else np.full(n_bars, np.nan)
    d9    = df_sig["stoch_9_d"].values if "stoch_9_d"  in df_sig.columns else np.full(n_bars, np.nan)

    x_local = np.arange(win_end - win_start + 1)

    ax.plot(x_local, close[win_start:win_end + 1], color="white",   linewidth=0.8, zorder=2)
    ax.plot(x_local, ema55[win_start:win_end + 1], color="#4fc3f7", linewidth=0.6, zorder=3)
    ax.plot(x_local, ema89[win_start:win_end + 1], color="#f48fb1", linewidth=0.6, zorder=3)

    entry_x = entry_bar - win_start
    exit_x  = exit_bar  - win_start

    ax.axvline(entry_x, color="#76ff03", linewidth=0.8, alpha=0.7, zorder=4)
    ax.axvline(exit_x,  color="#aaaaaa", linewidth=0.8, linestyle="--", alpha=0.7, zorder=4)

    entry_price  = float(trade.get("entry_price", close[entry_bar]))
    sl_mult      = PARAMS["sl_mult"]
    atr_at_entry = float(atr[entry_bar]) if not np.isnan(atr[entry_bar]) else 0.0
    sl_level = entry_price - sl_mult * atr_at_entry if direction == "LONG" else entry_price + sl_mult * atr_at_entry
    ax.axhline(sl_level, color="#ff5252", linewidth=0.6, linestyle="--", alpha=0.8, zorder=3)

    entry_color  = "#76ff03" if direction == "LONG" else "#ff5252"
    entry_marker = "^" if direction == "LONG" else "v"
    ax.plot(entry_x, entry_price, marker=entry_marker, color=entry_color, markersize=6, zorder=6)

    exit_price = float(trade.get("exit_price", close[exit_bar]))
    exit_color = "#76ff03" if pnl > 0 else "#ff5252"
    ax.plot(exit_x, exit_price, marker="o", color=exit_color, markersize=5, zorder=6)

    d9_val = float(d9[entry_bar]) if not np.isnan(d9[entry_bar]) else -1.0
    be_str = " BE" if be_trig else ""
    pnl_str = ("+" if pnl >= 0 else "") + "{:.2f}".format(pnl)
    d9_str  = "{:.1f}".format(d9_val) if d9_val >= 0 else "?"
    label_parts = [
        "G:" + (grade if grade else "?") + " " + direction[0],
        exit_rsn,
        "$" + pnl_str,
        "D9:" + d9_str,
        "R:" + str(ratchets) + be_str,
    ]
    label = NL.join(label_parts)
    ax.text(
        0.02, 0.97, label,
        transform=ax.transAxes,
        va="top", ha="left",
        fontsize=5.5,
        color="white",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#1a1a2e", alpha=0.75, edgecolor="none"),
        zorder=7,
    )

    ax.set_facecolor("#0d0d0d")
    ax.tick_params(labelsize=4, colors="#888888")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")
    ax.set_title("#" + str(trade_idx + 1), fontsize=5, color="#888888", pad=2)


def render_page(trades_page: list, df_sig: pd.DataFrame, symbol: str,
                page_num: int, start_idx: int) -> plt.Figure:
    """Render one page (up to TRADES_PER_PAGE trades) into a Figure; return it."""
    n   = len(trades_page)
    fig, axes = plt.subplots(ROWS, COLS, figsize=(18, 12))
    fig.patch.set_facecolor("#0d0d0d")
    fig.suptitle(
        symbol + "  |  55/89 EMA Cross Scalp v2  |  Page " + str(page_num),
        fontsize=11, color="white", y=0.995,
    )
    axes_flat = axes.flatten()
    for idx, trade in enumerate(trades_page):
        render_trade(axes_flat[idx], trade, df_sig, start_idx + idx)
    for idx in range(n, ROWS * COLS):
        axes_flat[idx].set_visible(False)
    fig.tight_layout(rect=[0, 0, 1, 0.99])
    return fig


def process_coin(symbol: str) -> None:
    """Run pipeline for symbol and save trade visualisation PNGs."""
    df_sig, trades_df = load_and_run(symbol)
    if df_sig is None or trades_df is None or trades_df.empty:
        return

    trades  = trades_df.to_dict("records")
    trades  = trades[:MAX_TRADES]
    n_pages = max(1, (len(trades) + TRADES_PER_PAGE - 1) // TRADES_PER_PAGE)
    log.info(symbol + ": " + str(len(trades)) + " trades -> " + str(n_pages) + " page(s)")

    for pg in range(n_pages):
        start       = pg * TRADES_PER_PAGE
        page_trades = trades[start: start + TRADES_PER_PAGE]
        fig         = render_page(page_trades, df_sig, symbol, pg + 1, start)
        suffix      = "_p" + str(pg + 1) if n_pages > 1 else ""
        out         = RESULTS_DIR / ("trade_viz_5589_" + symbol + suffix + ".png")
        fig.savefig(str(out), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        log.info("  Saved: " + str(out))


def main() -> None:
    """Visualise trades for all COINS; output PNGs to results/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log.info("=== visualise_5589_trades started " + ts + " ===")
    for symbol in COINS:
        log.info("Processing: " + symbol)
        process_coin(symbol)
    log.info("=== done ===")


if __name__ == "__main__":
    main()

"""
Build script: trade analysis + visualisation for 55/89 EMA Cross Scalp v2.
Writes:
  scripts/run_trade_analysis_5589.py
  scripts/visualise_5589_trades.py

Run: python scripts/build_trade_analysis_5589.py
"""
import ast
import logging
import logging.handlers
import os
import py_compile
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# ---- Logging setup ----
log = logging.getLogger("build_trade_analysis_5589")
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
_fh = logging.handlers.TimedRotatingFileHandler(
    LOGS / (datetime.now(timezone.utc).strftime("%Y-%m-%d") + "-build-trade-analysis-5589.log"),
    when="midnight", backupCount=30, encoding="utf-8",
)
_fh.setFormatter(_fmt)
_sh = logging.StreamHandler(sys.stdout)
_sh.setFormatter(_fmt)
log.addHandler(_fh)
log.addHandler(_sh)

ERRORS = []


def validate_output(path: str) -> bool:
    """Run py_compile + ast.parse on a written .py file; return True if both pass."""
    try:
        py_compile.compile(path, doraise=True)
        log.info("  SYNTAX OK: " + path)
    except py_compile.PyCompileError as e:
        log.error("  SYNTAX ERROR: " + str(e))
        return False
    try:
        source = Path(path).read_text(encoding="utf-8")
        ast.parse(source, filename=path)
        log.info("  AST OK: " + path)
    except SyntaxError as e:
        log.error("  AST ERROR in " + path + " line " + str(e.lineno) + ": " + str(e.msg))
        return False
    return True


def check_docstrings(path: str) -> bool:
    """Verify every function def in path has a docstring; return True if clean."""
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=path)
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                missing.append(node.name + " (line " + str(node.lineno) + ")")
    if missing:
        log.error("  MISSING DOCSTRINGS in " + path + ": " + ", ".join(missing))
        return False
    log.info("  DOCSTRINGS OK: " + path)
    return True


def write_and_validate(dest: Path, content: str) -> bool:
    """Write content to dest, then validate syntax + docstrings. Return True if all pass."""
    log.info("Writing: " + str(dest))
    dest.write_text(content, encoding="utf-8")
    ok = validate_output(str(dest)) and check_docstrings(str(dest))
    if not ok:
        ERRORS.append(str(dest))
    return ok


# =============================================================================
# FILE 1: run_trade_analysis_5589.py
# =============================================================================

RUN_TRADE_ANALYSIS = '''\
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
'''

# =============================================================================
# FILE 2: visualise_5589_trades.py
# =============================================================================

VISUALISE_TRADES = '''\
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
import matplotlib.patches as mpatches

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

RESULTS_DIR  = ROOT / "results"
DATA_DIR     = ROOT / "data" / "historical"
PRE_BARS     = 10
POST_BARS    = 5
TRADES_PER_PAGE = 20
MAX_TRADES   = 50
COLS         = 5
ROWS         = 4


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

    n_bars = len(df_sig)
    win_start = max(0, entry_bar - PRE_BARS)
    win_end   = min(n_bars - 1, exit_bar + POST_BARS)

    close  = df_sig["close"].values
    ema55  = df_sig["ema_55"].values  if "ema_55" in df_sig.columns  else np.full(n_bars, np.nan)
    ema89  = df_sig["ema_89"].values  if "ema_89" in df_sig.columns  else np.full(n_bars, np.nan)
    atr    = df_sig["atr"].values     if "atr"    in df_sig.columns  else np.full(n_bars, np.nan)
    d9     = df_sig["stoch_9_d"].values if "stoch_9_d" in df_sig.columns else np.full(n_bars, np.nan)

    x_range  = np.arange(win_start, win_end + 1)
    x_local  = x_range - win_start

    ax.plot(x_local, close[win_start:win_end + 1], color="white", linewidth=0.8, zorder=2)
    ax.plot(x_local, ema55[win_start:win_end + 1], color="#4fc3f7", linewidth=0.6, zorder=3, label="EMA55")
    ax.plot(x_local, ema89[win_start:win_end + 1], color="#f48fb1", linewidth=0.6, zorder=3, label="EMA89")

    entry_x = entry_bar - win_start
    exit_x  = exit_bar  - win_start

    ax.axvline(entry_x, color="#76ff03", linewidth=0.8, alpha=0.7, zorder=4)
    ax.axvline(exit_x,  color="#aaaaaa", linewidth=0.8, linestyle="--", alpha=0.7, zorder=4)

    entry_price = float(trade.get("entry_price", close[entry_bar]))
    sl_mult = PARAMS["sl_mult"]
    atr_at_entry = float(atr[entry_bar]) if not np.isnan(atr[entry_bar]) else 0.0
    if direction == "LONG":
        sl_level = entry_price - sl_mult * atr_at_entry
    else:
        sl_level = entry_price + sl_mult * atr_at_entry
    ax.axhline(sl_level, color="#ff5252", linewidth=0.6, linestyle="--", alpha=0.8, zorder=3)

    entry_color = "#76ff03" if direction == "LONG" else "#ff5252"
    entry_marker = "^" if direction == "LONG" else "v"
    ax.plot(entry_x, entry_price, marker=entry_marker, color=entry_color, markersize=6, zorder=6)

    exit_price = float(trade.get("exit_price", close[exit_bar]))
    exit_color = "#76ff03" if pnl > 0 else "#ff5252"
    ax.plot(exit_x, exit_price, marker="o", color=exit_color, markersize=5, zorder=6)

    d9_val = float(d9[entry_bar]) if not np.isnan(d9[entry_bar]) else -1.0
    be_str = " BE" if be_trig else ""
    label_lines = [
        "G:" + (grade if grade else "?") + " " + direction[0],
        exit_rsn,
        "$" + ("{:+.2f}".format(pnl)),
        "D9:" + ("{:.1f}".format(d9_val) if d9_val >= 0 else "?"),
        "R:" + str(ratchets) + be_str,
    ]
    label = "\n".join(label_lines)
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
    n = len(trades_page)
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

    trades = trades_df.to_dict("records")
    trades = trades[:MAX_TRADES]
    n_pages = max(1, (len(trades) + TRADES_PER_PAGE - 1) // TRADES_PER_PAGE)
    log.info(symbol + ": " + str(len(trades)) + " trades -> " + str(n_pages) + " page(s)")

    for pg in range(n_pages):
        start = pg * TRADES_PER_PAGE
        page_trades = trades[start: start + TRADES_PER_PAGE]
        fig = render_page(page_trades, df_sig, symbol, pg + 1, start)
        suffix = "_p" + str(pg + 1) if n_pages > 1 else ""
        out = RESULTS_DIR / ("trade_viz_5589_" + symbol + suffix + ".png")
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
'''

# =============================================================================
# MAIN BUILD
# =============================================================================

def main() -> None:
    """Run the full build: write both scripts, validate, report."""
    log.info("=== build_trade_analysis_5589 started ===")

    dest1 = SCRIPTS / "run_trade_analysis_5589.py"
    dest2 = SCRIPTS / "visualise_5589_trades.py"

    for dest in [dest1, dest2]:
        if dest.exists():
            log.warning(str(dest) + " already exists -- overwriting (build script regenerates)")

    write_and_validate(dest1, RUN_TRADE_ANALYSIS)
    write_and_validate(dest2, VISUALISE_TRADES)

    log.info("=== BUILD SUMMARY ===")
    if ERRORS:
        log.error("BUILD FAILED -- errors in: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        log.info("BUILD OK -- all files compile clean")
        log.info("Next steps:")
        log.info("  1. python scripts/run_trade_analysis_5589.py")
        log.info("  2. python scripts/visualise_5589_trades.py")


if __name__ == "__main__":
    main()

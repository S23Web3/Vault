"""
Build: Trade Analyzer v2

Creates run_trade_analysis_v2.py -- comprehensive BingX trade analysis with
properly spaced tables, 10 analysis sections, terminal + markdown + CSV output.

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/build_trade_analyzer_v2.py
"""
import py_compile
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "scripts" / "run_trade_analysis_v2.py"
ERRORS = []


def verify(path, label):
    """Syntax-check and AST-parse a Python file."""
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        print("  OK: " + label)
        return True
    except (py_compile.PyCompileError, SyntaxError) as e:
        print("  FAIL: " + label + " -- " + str(e))
        ERRORS.append(label)
        return False


# ---------------------------------------------------------------------------
# Source code for run_trade_analysis_v2.py
# ---------------------------------------------------------------------------

SOURCE = r'''"""
Trade Analysis v2: comprehensive BingX bot trade analysis.

Reads trades.csv, optionally fetches 5m klines from BingX API for MFE/MAE,
produces 10 analysis sections with properly spaced tables.

Output: terminal (fixed-width) + markdown report + CSV.

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/run_trade_analysis_v2.py
    python scripts/run_trade_analysis_v2.py --no-api --days 1
    python scripts/run_trade_analysis_v2.py --days 1 --verbose
"""
import argparse
import csv
import hashlib
import hmac as hmac_lib
import logging
import os
import sys
import time
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

import pandas as pd
import requests
import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
TRADES_CSV = ROOT / "trades.csv"
CONFIG_PATH = ROOT / "config.yaml"
LOG_DIR = ROOT / "logs"

COMMISSION_RATE = 0.0008  # 0.08% taker per side
KLINE_PATH = "/openApi/swap/v2/quote/klines"

FULL_COLUMNS = [
    "timestamp", "symbol", "direction", "grade", "entry_price", "exit_price",
    "exit_reason", "pnl_net", "quantity", "notional_usd", "entry_time", "order_id",
    "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct", "ttp_exit_reason",
    "be_raised", "saw_green",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def safe_float(val, default=0.0):
    """Parse a value to float, returning default on failure."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_bool(val):
    """Parse a value to bool (handles string True/False and NaN)."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return False
    return str(val).strip().lower() == "true"


def to_ms(ts_str):
    """Parse ISO timestamp string to milliseconds epoch."""
    if not ts_str or (isinstance(ts_str, float) and pd.isna(ts_str)):
        return 0
    try:
        dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def hold_minutes(entry_ts, exit_ts):
    """Compute hold time in minutes between two ISO timestamps."""
    entry_ms = to_ms(entry_ts)
    exit_ms = to_ms(exit_ts)
    if entry_ms == 0 or exit_ms == 0:
        return None
    mins = (exit_ms - entry_ms) / 60000.0
    return max(mins, 0.0)


# ---------------------------------------------------------------------------
# BingX API (reused from v1)
# ---------------------------------------------------------------------------


def sign_and_build(base, path, params, api_key, secret):
    """Build signed URL and return (url, headers)."""
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "10000"
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    sig = hmac_lib.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = base + path + "?" + qs + "&signature=" + sig
    return url, {"X-BX-APIKEY": api_key}


def fetch_klines(symbol, start_ms, end_ms, base, api_key, secret):
    """Fetch 5m klines for symbol in [start_ms, end_ms]."""
    params = {
        "symbol": symbol,
        "interval": "5m",
        "startTime": str(start_ms),
        "endTime": str(end_ms),
        "limit": "200",
    }
    url, headers = sign_and_build(base, KLINE_PATH, params, api_key, secret)
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        if data.get("code", -1) != 0:
            return []
        return data.get("data", [])
    except Exception as e:
        log.warning("Kline fetch failed %s: %s", symbol, e)
        return []


def compute_mfe_mae(klines, entry_price, direction, commission_rate):
    """Compute MFE%, MAE%, and saw_green from klines."""
    if not klines:
        return 0.0, 0.0, False
    mfe = 0.0
    mae = 0.0
    commission_threshold = commission_rate * 2  # round-trip
    for bar in klines:
        try:
            high = float(bar["high"])
            low = float(bar["low"])
        except (KeyError, ValueError, TypeError):
            continue
        if direction == "LONG":
            favorable = (high - entry_price) / entry_price
            adverse = (entry_price - low) / entry_price
        else:
            favorable = (entry_price - low) / entry_price
            adverse = (high - entry_price) / entry_price
        mfe = max(mfe, favorable)
        mae = max(mae, adverse)
    saw_green = mfe > commission_threshold
    return round(mfe * 100, 4), round(mae * 100, 4), saw_green


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_trades(from_date, to_date):
    """Load trades.csv with ragged column handling (12 or 18 cols per row)."""
    if not TRADES_CSV.exists():
        log.error("trades.csv not found: " + str(TRADES_CSV))
        sys.exit(1)

    # Read with Python csv module to handle ragged rows
    rows = []
    with open(TRADES_CSV, encoding="utf-8") as fh:
        reader = csv.reader(fh)
        _header = next(reader)  # skip original 12-col header
        for line in reader:
            # Pad short rows to 18 columns with empty strings
            while len(line) < 18:
                line.append("")
            rows.append(dict(zip(FULL_COLUMNS, line[:18])))

    df = pd.DataFrame(rows)

    log.info("Loaded %d trades total from %s", len(df), str(TRADES_CSV))

    # Date filter using entry_time (preferred) or timestamp (fallback)
    def get_date_str(row):
        """Extract date string from entry_time or timestamp."""
        et = row.get("entry_time", "")
        ts = row.get("timestamp", "")
        val = et if (et and not (isinstance(et, float) and pd.isna(et))) else ts
        return str(val)[:10] if val else ""

    df["_date_key"] = df.apply(get_date_str, axis=1)
    mask = (df["_date_key"] >= from_date) & (df["_date_key"] <= to_date)
    df = df[mask].copy()
    df.drop(columns=["_date_key"], inplace=True)

    log.info("Filtered to %d trades (%s to %s)", len(df), from_date, to_date)
    return df


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------


def enrich_trades(df, use_api, base_url, api_key, secret_key, verbose):
    """Add MFE/MAE/saw_green/hold_min columns to dataframe."""
    mfe_vals = []
    mae_vals = []
    sg_vals = []
    hold_vals = []
    errors = []
    total = len(df)

    for i, (idx, row) in enumerate(df.iterrows(), 1):
        symbol = str(row.get("symbol", ""))
        direction = str(row.get("direction", "LONG"))
        entry_price = safe_float(row.get("entry_price"))

        # Hold time
        h = hold_minutes(row.get("entry_time"), row.get("timestamp"))
        hold_vals.append(h if h is not None else None)

        if use_api and entry_price > 0:
            entry_ts = str(row.get("entry_time", "")) if not pd.isna(row.get("entry_time", float("nan"))) else ""
            exit_ts = str(row.get("timestamp", "")) if not pd.isna(row.get("timestamp", float("nan"))) else ""
            entry_ms = to_ms(entry_ts)
            exit_ms = to_ms(exit_ts)
            if entry_ms == 0:
                entry_ms = exit_ms - 3600000

            pad = 5 * 60 * 1000
            klines = fetch_klines(
                symbol, entry_ms - pad, exit_ms + pad,
                base_url, api_key, secret_key,
            )
            trade_klines = [
                k for k in klines
                if entry_ms <= int(k.get("time", 0)) <= exit_ms
            ] if klines else []

            mfe_pct, mae_pct, saw_green = compute_mfe_mae(
                trade_klines, entry_price, direction, COMMISSION_RATE)

            mfe_vals.append(mfe_pct)
            mae_vals.append(mae_pct)
            sg_vals.append(saw_green)

            if verbose:
                log.info("[%d/%d] %s %s mfe=%.2f%% mae=%.2f%% green=%s",
                         i, total, symbol, direction, mfe_pct, mae_pct, saw_green)
            elif i % 10 == 0:
                log.info("[%d/%d] Processing...", i, total)

            time.sleep(0.3)
        else:
            # Local mode: use CSV fields if available
            mfe_vals.append(safe_float(row.get("ttp_extreme_pct")))
            mae_vals.append(0.0)
            sg_vals.append(safe_bool(row.get("saw_green")))

    df = df.copy()
    df["mfe_pct"] = mfe_vals
    df["mae_pct"] = mae_vals
    df["saw_green_calc"] = sg_vals
    df["hold_min"] = hold_vals
    df["pnl_net"] = df["pnl_net"].apply(lambda x: safe_float(x))
    df["be_raised_flag"] = df["be_raised"].apply(safe_bool)
    df["ttp_flag"] = df["ttp_activated"].apply(safe_bool)
    df["entry_price_f"] = df["entry_price"].apply(lambda x: safe_float(x))
    df["exit_price_f"] = df["exit_price"].apply(lambda x: safe_float(x))

    if errors:
        log.warning("Parse errors: " + ", ".join(errors))
    return df


def compute_summary(df):
    """Compute summary statistics."""
    total = len(df)
    if total == 0:
        return {}
    wins = (df["pnl_net"] > 0).sum()
    losses = total - wins
    wr = round(wins / total * 100, 1)
    net_pnl = round(df["pnl_net"].sum(), 4)
    gross_profit = round(df.loc[df["pnl_net"] > 0, "pnl_net"].sum(), 4) if wins > 0 else 0.0
    gross_loss = round(df.loc[df["pnl_net"] <= 0, "pnl_net"].sum(), 4) if losses > 0 else 0.0
    pf = round(gross_profit / abs(gross_loss), 2) if gross_loss != 0 else 999.9
    avg_pnl = round(net_pnl / total, 4)
    avg_win = round(gross_profit / wins, 4) if wins > 0 else 0.0
    avg_loss = round(gross_loss / losses, 4) if losses > 0 else 0.0
    best = round(df["pnl_net"].max(), 4)
    worst = round(df["pnl_net"].min(), 4)
    lsg = ((df["saw_green_calc"]) & (df["pnl_net"] < 0)).sum()
    lsg_pct = round(lsg / losses * 100, 1) if losses > 0 else 0.0
    return {
        "total": total, "wins": wins, "losses": losses, "wr": wr,
        "net_pnl": net_pnl, "gross_profit": gross_profit, "gross_loss": gross_loss,
        "profit_factor": pf, "avg_pnl": avg_pnl, "avg_win": avg_win,
        "avg_loss": avg_loss, "best": best, "worst": worst,
        "lsg": lsg, "lsg_pct": lsg_pct,
    }


def compute_symbol_leaderboard(df):
    """Compute per-symbol stats sorted by net PnL descending."""
    rows = []
    for sym, grp in df.groupby("symbol"):
        n = len(grp)
        w = (grp["pnl_net"] > 0).sum()
        wr = round(w / n * 100, 1) if n > 0 else 0.0
        pnl = round(grp["pnl_net"].sum(), 4)
        avg = round(pnl / n, 4) if n > 0 else 0.0
        rows.append({"symbol": sym, "trades": n, "wins": w, "wr": wr, "pnl": pnl, "avg": avg})
    rows.sort(key=lambda x: x["pnl"], reverse=True)
    return rows


def compute_direction_breakdown(df):
    """Compute LONG vs SHORT stats."""
    rows = []
    for d in ["LONG", "SHORT"]:
        grp = df[df["direction"] == d]
        n = len(grp)
        if n == 0:
            continue
        w = (grp["pnl_net"] > 0).sum()
        wr = round(w / n * 100, 1)
        pnl = round(grp["pnl_net"].sum(), 4)
        avg_mfe = round(grp["mfe_pct"].mean(), 2) if n > 0 else 0.0
        avg_mae = round(grp["mae_pct"].mean(), 2) if n > 0 else 0.0
        rows.append({"dir": d, "trades": n, "wins": w, "wr": wr, "pnl": pnl,
                      "avg_mfe": avg_mfe, "avg_mae": avg_mae})
    return rows


def compute_grade_breakdown(df):
    """Compute per-grade stats."""
    rows = []
    for g in sorted(df["grade"].dropna().unique()):
        grp = df[df["grade"] == g]
        n = len(grp)
        if n == 0:
            continue
        w = (grp["pnl_net"] > 0).sum()
        l = n - w
        wr = round(w / n * 100, 1)
        pnl = round(grp["pnl_net"].sum(), 4)
        avg_mfe = round(grp["mfe_pct"].mean(), 2) if n > 0 else 0.0
        lsg = ((grp["saw_green_calc"]) & (grp["pnl_net"] < 0)).sum()
        lsg_pct = round(lsg / l * 100, 1) if l > 0 else 0.0
        rows.append({"grade": g, "trades": n, "wins": w, "wr": wr, "pnl": pnl,
                      "avg_mfe": avg_mfe, "lsg_pct": lsg_pct})
    return rows


def compute_exit_breakdown(df):
    """Compute per-exit-reason stats."""
    rows = []
    for reason in sorted(df["exit_reason"].dropna().unique()):
        grp = df[df["exit_reason"] == reason]
        n = len(grp)
        pct = round(n / len(df) * 100, 1) if len(df) > 0 else 0.0
        avg_pnl = round(grp["pnl_net"].mean(), 4) if n > 0 else 0.0
        rows.append({"reason": reason, "count": n, "pct": pct, "avg_pnl": avg_pnl})
    rows.sort(key=lambda x: x["count"], reverse=True)
    return rows


def compute_hold_times(df):
    """Compute hold time statistics."""
    valid = df.dropna(subset=["hold_min"])
    if len(valid) == 0:
        return {}
    avg_h = round(valid["hold_min"].mean(), 1)
    min_h = round(valid["hold_min"].min(), 1)
    max_h = round(valid["hold_min"].max(), 1)
    winners = valid[valid["pnl_net"] > 0]
    losers = valid[valid["pnl_net"] <= 0]
    avg_win_h = round(winners["hold_min"].mean(), 1) if len(winners) > 0 else 0.0
    avg_loss_h = round(losers["hold_min"].mean(), 1) if len(losers) > 0 else 0.0
    return {"avg": avg_h, "min": min_h, "max": max_h,
            "avg_win": avg_win_h, "avg_loss": avg_loss_h}


def compute_ttp_performance(df):
    """Compute TTP trades vs non-TTP stats."""
    ttp = df[df["ttp_flag"]]
    non = df[~df["ttp_flag"]]
    if len(ttp) == 0:
        return None
    result = {
        "ttp_count": len(ttp),
        "ttp_pnl": round(ttp["pnl_net"].sum(), 4),
        "ttp_avg_extreme": round(ttp["mfe_pct"].mean(), 2),
        "non_count": len(non),
        "non_pnl": round(non["pnl_net"].sum(), 4),
    }
    # TTP trail % from CSV field
    trail_vals = ttp["ttp_trail_pct"].apply(safe_float)
    if trail_vals.sum() > 0:
        result["ttp_avg_trail"] = round(trail_vals.mean(), 2)
    else:
        result["ttp_avg_trail"] = 0.0
    return result


def compute_be_effectiveness(df):
    """Compute BE-raised trades vs non-BE stats."""
    be = df[df["be_raised_flag"]]
    non = df[~df["be_raised_flag"]]
    if len(be) == 0:
        return None
    be_wins = (be["pnl_net"] > 0).sum()
    non_wins = (non["pnl_net"] > 0).sum()
    return {
        "be_count": len(be),
        "be_wr": round(be_wins / len(be) * 100, 1) if len(be) > 0 else 0.0,
        "be_pnl": round(be["pnl_net"].sum(), 4),
        "non_count": len(non),
        "non_wr": round(non_wins / len(non) * 100, 1) if len(non) > 0 else 0.0,
        "non_pnl": round(non["pnl_net"].sum(), 4),
    }


def compute_pnl_distribution(df):
    """Compute PnL distribution stats and ASCII histogram."""
    if len(df) == 0:
        return None
    pnl = df["pnl_net"]
    std_dev = round(pnl.std(), 4) if len(pnl) > 1 else 0.0
    median = round(pnl.median(), 4)
    mean = round(pnl.mean(), 4)
    skew = round(pnl.skew(), 4) if len(pnl) > 2 else 0.0

    # Build histogram bins
    n_bins = 10
    lo = pnl.min()
    hi = pnl.max()
    if lo == hi:
        bins = [(lo, lo, len(pnl))]
    else:
        step = (hi - lo) / n_bins
        bins = []
        for b in range(n_bins):
            edge_lo = lo + b * step
            edge_hi = lo + (b + 1) * step
            if b == n_bins - 1:
                count = ((pnl >= edge_lo) & (pnl <= edge_hi)).sum()
            else:
                count = ((pnl >= edge_lo) & (pnl < edge_hi)).sum()
            bins.append((round(edge_lo, 2), round(edge_hi, 2), count))

    return {
        "std_dev": std_dev, "median": median, "mean": mean, "skew": skew,
        "bins": bins,
    }


def compute_max_capital(df):
    """Compute peak concurrent capital usage from overlapping positions."""
    if len(df) == 0:
        return None
    events = []
    for _, row in df.iterrows():
        entry_ms = to_ms(row.get("entry_time"))
        exit_ms = to_ms(row.get("timestamp"))
        notional = safe_float(row.get("notional_usd"))
        if entry_ms > 0 and exit_ms > 0 and notional > 0:
            events.append((entry_ms, +notional))
            events.append((exit_ms, -notional))
    if not events:
        return None
    events.sort(key=lambda x: (x[0], x[1]))
    current = 0.0
    peak = 0.0
    peak_count = 0
    current_count = 0
    count_at_peak = 0
    for ts, delta in events:
        current += delta
        if delta > 0:
            current_count += 1
        else:
            current_count -= 1
        if current > peak:
            peak = current
            count_at_peak = current_count
    return {
        "peak_capital": round(peak, 2),
        "positions_at_peak": count_at_peak,
        "total_notional": round(df["notional_usd"].apply(safe_float).sum(), 2),
    }


def compute_max_drawdown(equity_curve):
    """Compute max drawdown from cumulative PnL curve."""
    if not equity_curve or len(equity_curve) < 2:
        return None
    peak = equity_curve[0]
    max_dd = 0.0
    max_dd_pct = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = round(dd / peak * 100, 2) if peak > 0 else 0.0
    return {"max_dd": round(max_dd, 4), "max_dd_pct": max_dd_pct}


def build_equity_curve(df):
    """Build cumulative PnL series."""
    cum = df["pnl_net"].cumsum().tolist()
    return cum


# ---------------------------------------------------------------------------
# Formatting: padded tables
# ---------------------------------------------------------------------------


def pad_row(vals, widths, aligns):
    """Format one row with padded columns."""
    parts = []
    for val, w, a in zip(vals, widths, aligns):
        s = str(val)
        if a == "r":
            parts.append(s.rjust(w))
        else:
            parts.append(s.ljust(w))
    return "  ".join(parts)


def format_separator(widths):
    """Create a dashed separator line matching column widths."""
    return "  ".join("-" * w for w in widths)


def print_table(title, headers, rows, widths, aligns):
    """Print a formatted table to terminal and return lines for markdown."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append(title)
    lines.append("=" * 60)
    hdr = pad_row(headers, widths, aligns)
    sep = format_separator(widths)
    lines.append(hdr)
    lines.append(sep)
    for row in rows:
        lines.append(pad_row(row, widths, aligns))
    for line in lines:
        print(line)
    return lines


def format_pnl(val):
    """Format PnL value with sign and dollar."""
    if val >= 0:
        return "+$" + str(round(val, 4))
    return "-$" + str(round(abs(val), 4))


# ---------------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------------


def generate_output(df, summary, sym_lb, dir_bd, grade_bd, exit_bd,
                    hold_t, ttp_perf, be_eff, equity, pnl_dist, max_cap,
                    max_dd, out_md, out_csv):
    """Generate terminal output, markdown report, and CSV."""
    all_lines = []
    today_str = date.today().strftime("%Y-%m-%d")

    # --- Section 1: Summary ---
    all_lines.append("")
    all_lines.append("#" * 60)
    all_lines.append("  TRADE ANALYSIS v2 -- " + today_str)
    all_lines.append("#" * 60)
    all_lines.append("")
    summary_rows = [
        ("Total trades", str(summary["total"])),
        ("Wins / Losses", str(summary["wins"]) + " / " + str(summary["losses"])),
        ("Win rate", str(summary["wr"]) + "%"),
        ("Net PnL", format_pnl(summary["net_pnl"])),
        ("Gross profit", format_pnl(summary["gross_profit"])),
        ("Gross loss", format_pnl(summary["gross_loss"])),
        ("Profit factor", str(summary["profit_factor"])),
        ("Avg PnL/trade", format_pnl(summary["avg_pnl"])),
        ("Avg winner", format_pnl(summary["avg_win"])),
        ("Avg loser", format_pnl(summary["avg_loss"])),
        ("Best trade", format_pnl(summary["best"])),
        ("Worst trade", format_pnl(summary["worst"])),
        ("LSG count", str(summary["lsg"])),
        ("LSG %", str(summary["lsg_pct"]) + "% of losers saw green"),
    ]
    if pnl_dist:
        summary_rows.append(("PnL Std Dev", "$" + str(pnl_dist["std_dev"])))
        summary_rows.append(("PnL Median", format_pnl(pnl_dist["median"])))
        summary_rows.append(("PnL Skew", str(pnl_dist["skew"])))
    if max_dd:
        summary_rows.append(("Max Drawdown", format_pnl(max_dd["max_dd"])))
        summary_rows.append(("Max DD %", str(max_dd["max_dd_pct"]) + "%"))
    if max_cap:
        summary_rows.append(("Peak Capital", "$" + str(max_cap["peak_capital"])))
        summary_rows.append(("Positions@Peak", str(max_cap["positions_at_peak"])))
        summary_rows.append(("Total Notional", "$" + str(max_cap["total_notional"])))
    for label, val in summary_rows:
        line = "  " + label.ljust(20) + val
        all_lines.append(line)
        print(line)

    # --- Section 2: Equity Curve (ASCII) ---
    if equity:
        all_lines.append("")
        all_lines.append("=" * 60)
        all_lines.append("EQUITY CURVE (cumulative PnL)")
        all_lines.append("=" * 60)
        lo = min(equity)
        hi = max(equity)
        span = hi - lo if hi != lo else 1.0
        chart_width = 40
        for i, val in enumerate(equity):
            bar_len = int((val - lo) / span * chart_width)
            bar = "#" * max(bar_len, 0)
            line = str(i + 1).rjust(4) + " | " + bar + " " + str(round(val, 2))
            all_lines.append(line)
        for line in all_lines[-len(equity) - 4:]:
            print(line)

    # --- Section 3: Symbol Leaderboard ---
    if sym_lb:
        hdrs = ["Symbol", "Trades", "Wins", "WR%", "Net PnL", "Avg PnL"]
        ws = [14, 7, 5, 6, 12, 10]
        als = ["l", "r", "r", "r", "r", "r"]
        rows = []
        for s in sym_lb:
            rows.append([s["symbol"], s["trades"], s["wins"],
                         str(s["wr"]) + "%", format_pnl(s["pnl"]), format_pnl(s["avg"])])
        tbl = print_table("SYMBOL LEADERBOARD", hdrs, rows, ws, als)
        all_lines.extend(tbl)

    # --- Section 4: Direction Breakdown ---
    if dir_bd:
        hdrs = ["Direction", "Trades", "Wins", "WR%", "Net PnL", "Avg MFE%", "Avg MAE%"]
        ws = [10, 7, 5, 6, 12, 9, 9]
        als = ["l", "r", "r", "r", "r", "r", "r"]
        rows = []
        for d in dir_bd:
            rows.append([d["dir"], d["trades"], d["wins"], str(d["wr"]) + "%",
                         format_pnl(d["pnl"]), str(d["avg_mfe"]) + "%", str(d["avg_mae"]) + "%"])
        tbl = print_table("DIRECTION BREAKDOWN", hdrs, rows, ws, als)
        all_lines.extend(tbl)

    # --- Section 5: Grade Breakdown ---
    if grade_bd:
        hdrs = ["Grade", "Trades", "Wins", "WR%", "Net PnL", "Avg MFE%", "LSG%"]
        ws = [6, 7, 5, 6, 12, 9, 6]
        als = ["l", "r", "r", "r", "r", "r", "r"]
        rows = []
        for g in grade_bd:
            rows.append([g["grade"], g["trades"], g["wins"], str(g["wr"]) + "%",
                         format_pnl(g["pnl"]), str(g["avg_mfe"]) + "%", str(g["lsg_pct"]) + "%"])
        tbl = print_table("GRADE BREAKDOWN", hdrs, rows, ws, als)
        all_lines.extend(tbl)

    # --- Section 6: Exit Reason Breakdown ---
    if exit_bd:
        hdrs = ["Exit Reason", "Count", "% Total", "Avg PnL"]
        ws = [16, 6, 8, 12]
        als = ["l", "r", "r", "r"]
        rows = []
        for e in exit_bd:
            rows.append([e["reason"], e["count"], str(e["pct"]) + "%", format_pnl(e["avg_pnl"])])
        tbl = print_table("EXIT REASON BREAKDOWN", hdrs, rows, ws, als)
        all_lines.extend(tbl)

    # --- Section 7: Hold Time Analysis ---
    if hold_t:
        all_lines.append("")
        all_lines.append("=" * 60)
        all_lines.append("HOLD TIME ANALYSIS")
        all_lines.append("=" * 60)
        hold_rows = [
            ("Avg hold", str(hold_t["avg"]) + " min"),
            ("Shortest", str(hold_t["min"]) + " min"),
            ("Longest", str(hold_t["max"]) + " min"),
            ("Avg winner hold", str(hold_t["avg_win"]) + " min"),
            ("Avg loser hold", str(hold_t["avg_loss"]) + " min"),
        ]
        for label, val in hold_rows:
            line = "  " + label.ljust(20) + val
            all_lines.append(line)
            print(line)

    # --- Section 8: TTP Performance ---
    if ttp_perf:
        all_lines.append("")
        all_lines.append("=" * 60)
        all_lines.append("TTP PERFORMANCE")
        all_lines.append("=" * 60)
        ttp_rows = [
            ("TTP trades", str(ttp_perf["ttp_count"])),
            ("TTP net PnL", format_pnl(ttp_perf["ttp_pnl"])),
            ("TTP avg extreme%", str(ttp_perf["ttp_avg_extreme"]) + "%"),
            ("TTP avg trail%", str(ttp_perf["ttp_avg_trail"]) + "%"),
            ("Non-TTP trades", str(ttp_perf["non_count"])),
            ("Non-TTP net PnL", format_pnl(ttp_perf["non_pnl"])),
        ]
        for label, val in ttp_rows:
            line = "  " + label.ljust(20) + val
            all_lines.append(line)
            print(line)

    # --- Section 9: BE Raise Effectiveness ---
    if be_eff:
        all_lines.append("")
        all_lines.append("=" * 60)
        all_lines.append("BE RAISE EFFECTIVENESS")
        all_lines.append("=" * 60)
        be_rows = [
            ("BE raised trades", str(be_eff["be_count"])),
            ("BE raised WR%", str(be_eff["be_wr"]) + "%"),
            ("BE raised PnL", format_pnl(be_eff["be_pnl"])),
            ("Non-BE trades", str(be_eff["non_count"])),
            ("Non-BE WR%", str(be_eff["non_wr"]) + "%"),
            ("Non-BE PnL", format_pnl(be_eff["non_pnl"])),
        ]
        for label, val in be_rows:
            line = "  " + label.ljust(20) + val
            all_lines.append(line)
            print(line)

    # --- Section 10: PnL Distribution ---
    if pnl_dist and pnl_dist["bins"]:
        all_lines.append("")
        all_lines.append("=" * 60)
        all_lines.append("PNL DISTRIBUTION (histogram)")
        all_lines.append("=" * 60)
        max_count = max(b[2] for b in pnl_dist["bins"])
        bar_scale = 30
        for lo_edge, hi_edge, count in pnl_dist["bins"]:
            bar_len = int(count / max_count * bar_scale) if max_count > 0 else 0
            bar = "#" * bar_len
            label = ("$" + str(lo_edge)).rjust(10) + " to " + ("$" + str(hi_edge)).ljust(10)
            line = label + " | " + bar + " " + str(count)
            all_lines.append(line)
            print(line)
        stats_line = "  Std Dev: $" + str(pnl_dist["std_dev"]) + "  Median: " + format_pnl(pnl_dist["median"]) + "  Skew: " + str(pnl_dist["skew"])
        all_lines.append(stats_line)
        print(stats_line)

    # --- Section 11: Per-Trade Detail ---
    hdrs = ["#", "Symbol", "Dir", "Grd", "Entry", "Exit", "Reason",
            "PnL", "MFE%", "MAE%", "Green", "Hold", "BE", "TTP"]
    ws = [4, 14, 6, 4, 12, 12, 14, 12, 8, 8, 6, 7, 4, 4]
    als = ["r", "l", "l", "l", "r", "r", "l", "r", "r", "r", "l", "r", "l", "l"]
    rows = []
    for i, (idx, row) in enumerate(df.iterrows(), 1):
        h = row.get("hold_min")
        hold_str = str(round(h, 0)).replace(".0", "") + "m" if h is not None and not pd.isna(h) else "?"
        rows.append([
            i,
            str(row.get("symbol", "")),
            str(row.get("direction", "")),
            str(row.get("grade", "")),
            str(round(safe_float(row.get("entry_price")), 7)),
            str(round(safe_float(row.get("exit_price")), 7)),
            str(row.get("exit_reason", "")),
            format_pnl(safe_float(row.get("pnl_net"))),
            str(round(safe_float(row.get("mfe_pct")), 2)) + "%",
            str(round(safe_float(row.get("mae_pct")), 2)) + "%",
            "Yes" if row.get("saw_green_calc") else "No",
            hold_str,
            "Y" if row.get("be_raised_flag") else "N",
            "Y" if row.get("ttp_flag") else "N",
        ])
    tbl = print_table("PER-TRADE DETAIL", hdrs, rows, ws, als)
    all_lines.extend(tbl)

    # --- Write Markdown ---
    md_lines = ["# Trade Analysis v2 -- " + today_str, ""]
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append("| Metric               | Value                          |")
    md_lines.append("|----------------------|--------------------------------|")
    for label, val in summary_rows:
        md_lines.append("| " + label.ljust(20) + " | " + val.ljust(30) + " |")

    if sym_lb:
        md_lines.append("")
        md_lines.append("## Symbol Leaderboard")
        md_lines.append("")
        md_lines.append("| Symbol         | Trades | Wins | WR%    | Net PnL      | Avg PnL    |")
        md_lines.append("|----------------|--------|------|--------|--------------|------------|")
        for s in sym_lb:
            md_lines.append("| " + str(s["symbol"]).ljust(14) + " | " +
                            str(s["trades"]).rjust(6) + " | " +
                            str(s["wins"]).rjust(4) + " | " +
                            (str(s["wr"]) + "%").rjust(6) + " | " +
                            format_pnl(s["pnl"]).rjust(12) + " | " +
                            format_pnl(s["avg"]).rjust(10) + " |")

    if dir_bd:
        md_lines.append("")
        md_lines.append("## Direction Breakdown")
        md_lines.append("")
        md_lines.append("| Direction  | Trades | Wins | WR%    | Net PnL      | Avg MFE%  | Avg MAE%  |")
        md_lines.append("|------------|--------|------|--------|--------------|-----------|-----------|")
        for d in dir_bd:
            md_lines.append("| " + d["dir"].ljust(10) + " | " +
                            str(d["trades"]).rjust(6) + " | " +
                            str(d["wins"]).rjust(4) + " | " +
                            (str(d["wr"]) + "%").rjust(6) + " | " +
                            format_pnl(d["pnl"]).rjust(12) + " | " +
                            (str(d["avg_mfe"]) + "%").rjust(9) + " | " +
                            (str(d["avg_mae"]) + "%").rjust(9) + " |")

    if grade_bd:
        md_lines.append("")
        md_lines.append("## Grade Breakdown")
        md_lines.append("")
        md_lines.append("| Grade | Trades | Wins | WR%    | Net PnL      | Avg MFE%  | LSG%   |")
        md_lines.append("|-------|--------|------|--------|--------------|-----------|--------|")
        for g in grade_bd:
            md_lines.append("| " + str(g["grade"]).ljust(5) + " | " +
                            str(g["trades"]).rjust(6) + " | " +
                            str(g["wins"]).rjust(4) + " | " +
                            (str(g["wr"]) + "%").rjust(6) + " | " +
                            format_pnl(g["pnl"]).rjust(12) + " | " +
                            (str(g["avg_mfe"]) + "%").rjust(9) + " | " +
                            (str(g["lsg_pct"]) + "%").rjust(6) + " |")

    if exit_bd:
        md_lines.append("")
        md_lines.append("## Exit Reason Breakdown")
        md_lines.append("")
        md_lines.append("| Exit Reason      | Count | % Total  | Avg PnL      |")
        md_lines.append("|------------------|-------|----------|--------------|")
        for e in exit_bd:
            md_lines.append("| " + str(e["reason"]).ljust(16) + " | " +
                            str(e["count"]).rjust(5) + " | " +
                            (str(e["pct"]) + "%").rjust(8) + " | " +
                            format_pnl(e["avg_pnl"]).rjust(12) + " |")

    if hold_t:
        md_lines.append("")
        md_lines.append("## Hold Time Analysis")
        md_lines.append("")
        md_lines.append("| Metric               | Value          |")
        md_lines.append("|----------------------|----------------|")
        for label, val in [("Avg hold", str(hold_t["avg"]) + " min"),
                           ("Shortest", str(hold_t["min"]) + " min"),
                           ("Longest", str(hold_t["max"]) + " min"),
                           ("Avg winner hold", str(hold_t["avg_win"]) + " min"),
                           ("Avg loser hold", str(hold_t["avg_loss"]) + " min")]:
            md_lines.append("| " + label.ljust(20) + " | " + val.ljust(14) + " |")

    if ttp_perf:
        md_lines.append("")
        md_lines.append("## TTP Performance")
        md_lines.append("")
        md_lines.append("| Metric               | Value          |")
        md_lines.append("|----------------------|----------------|")
        for label, val in [("TTP trades", str(ttp_perf["ttp_count"])),
                           ("TTP net PnL", format_pnl(ttp_perf["ttp_pnl"])),
                           ("TTP avg extreme%", str(ttp_perf["ttp_avg_extreme"]) + "%"),
                           ("TTP avg trail%", str(ttp_perf["ttp_avg_trail"]) + "%"),
                           ("Non-TTP trades", str(ttp_perf["non_count"])),
                           ("Non-TTP net PnL", format_pnl(ttp_perf["non_pnl"]))]:
            md_lines.append("| " + label.ljust(20) + " | " + val.ljust(14) + " |")

    if be_eff:
        md_lines.append("")
        md_lines.append("## BE Raise Effectiveness")
        md_lines.append("")
        md_lines.append("| Metric               | Value          |")
        md_lines.append("|----------------------|----------------|")
        for label, val in [("BE raised trades", str(be_eff["be_count"])),
                           ("BE raised WR%", str(be_eff["be_wr"]) + "%"),
                           ("BE raised PnL", format_pnl(be_eff["be_pnl"])),
                           ("Non-BE trades", str(be_eff["non_count"])),
                           ("Non-BE WR%", str(be_eff["non_wr"]) + "%"),
                           ("Non-BE PnL", format_pnl(be_eff["non_pnl"]))]:
            md_lines.append("| " + label.ljust(20) + " | " + val.ljust(14) + " |")

    # PnL distribution in markdown
    if pnl_dist and pnl_dist["bins"]:
        md_lines.append("")
        md_lines.append("## PnL Distribution")
        md_lines.append("")
        md_lines.append("| Range              | Count | Bar                            |")
        md_lines.append("|--------------------|-------|--------------------------------|")
        max_count = max(b[2] for b in pnl_dist["bins"])
        for lo_edge, hi_edge, count in pnl_dist["bins"]:
            bar_len = int(count / max_count * 20) if max_count > 0 else 0
            bar = "#" * bar_len
            range_str = "$" + str(lo_edge) + " to $" + str(hi_edge)
            md_lines.append("| " + range_str.ljust(18) + " | " +
                            str(count).rjust(5) + " | " + bar.ljust(30) + " |")
        md_lines.append("")
        md_lines.append("Std Dev: $" + str(pnl_dist["std_dev"]) +
                        " | Median: " + format_pnl(pnl_dist["median"]) +
                        " | Skew: " + str(pnl_dist["skew"]))

    # Per-trade detail in markdown
    md_lines.append("")
    md_lines.append("## Per-Trade Detail")
    md_lines.append("")
    md_hdr = "| " + " | ".join(h.ljust(w) for h, w in zip(hdrs, ws)) + " |"
    md_sep = "|" + "|".join("-" * (w + 2) for w in ws) + "|"
    md_lines.append(md_hdr)
    md_lines.append(md_sep)
    for row in rows:
        md_row = "| " + " | ".join(str(v).ljust(w) if a == "l" else str(v).rjust(w)
                                     for v, w, a in zip(row, ws, als)) + " |"
        md_lines.append(md_row)

    # Write markdown
    out_md.parent.mkdir(exist_ok=True)
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    log.info("Markdown report: " + str(out_md))

    # Write CSV
    export_cols = ["symbol", "direction", "grade", "entry_price", "exit_price",
                   "exit_reason", "pnl_net", "notional_usd", "mfe_pct", "mae_pct",
                   "saw_green_calc", "hold_min", "be_raised_flag", "ttp_flag",
                   "entry_time", "timestamp"]
    available = [c for c in export_cols if c in df.columns]
    df[available].to_csv(out_csv, index=False, encoding="utf-8")
    log.info("CSV report: " + str(out_csv))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """Run trade analysis v2."""
    parser = argparse.ArgumentParser(description="BingX Trade Analysis v2")
    parser.add_argument("--from", dest="from_date", default="2026-03-04",
                        help="Start date YYYY-MM-DD (default: 2026-03-04)")
    parser.add_argument("--to", dest="to_date", default=date.today().strftime("%Y-%m-%d"),
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--days", type=int, default=None,
                        help="Last N days (overrides --from)")
    parser.add_argument("--no-api", dest="no_api", action="store_true",
                        help="Skip API kline fetches, local-only mode")
    parser.add_argument("--verbose", action="store_true",
                        help="Print each trade as processed")
    args = parser.parse_args()

    # Date range
    from_date = args.from_date
    to_date = args.to_date
    if args.days is not None:
        from_date = (date.today() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    # Load credentials if using API
    base_url = ""
    api_key = ""
    secret_key = ""
    use_api = not args.no_api

    if use_api:
        load_dotenv(ROOT / ".env")
        api_key = os.getenv("BINGX_API_KEY", "")
        secret_key = os.getenv("BINGX_SECRET_KEY", "")
        if not api_key or not secret_key:
            log.warning("Missing API credentials -- falling back to --no-api mode")
            use_api = False
        else:
            config_path = ROOT / "config.yaml"
            with open(config_path, encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh)
            demo_mode = cfg.get("connector", {}).get("demo_mode", False)
            base_url = "https://open-api-vst.bingx.com" if demo_mode else "https://open-api.bingx.com"
            log.info("API base: " + base_url)

    # Load and filter trades
    df = load_trades(from_date, to_date)
    if len(df) == 0:
        print("")
        print("No trades found in date range " + from_date + " to " + to_date)
        print("Check trades.csv or adjust --from/--to/--days flags.")
        sys.exit(0)

    # Enrich with MFE/MAE
    log.info("Enriching %d trades (api=%s, verbose=%s)...", len(df), use_api, args.verbose)
    df = enrich_trades(df, use_api, base_url, api_key, secret_key, args.verbose)

    # Compute all analysis sections
    summary = compute_summary(df)
    sym_lb = compute_symbol_leaderboard(df)
    dir_bd = compute_direction_breakdown(df)
    grade_bd = compute_grade_breakdown(df)
    exit_bd = compute_exit_breakdown(df)
    hold_t = compute_hold_times(df)
    ttp_perf = compute_ttp_performance(df)
    be_eff = compute_be_effectiveness(df)
    equity = build_equity_curve(df)
    pnl_dist = compute_pnl_distribution(df)
    max_cap = compute_max_capital(df)
    max_dd = compute_max_drawdown(equity)

    # Output paths
    today_str = date.today().strftime("%Y-%m-%d")
    out_md = LOG_DIR / ("trade_analysis_v2_" + today_str + ".md")
    out_csv = LOG_DIR / ("trade_analysis_v2_" + today_str + ".csv")

    # Generate all outputs
    generate_output(df, summary, sym_lb, dir_bd, grade_bd, exit_bd,
                    hold_t, ttp_perf, be_eff, equity, pnl_dist, max_cap,
                    max_dd, out_md, out_csv)

    print("")
    print("=" * 60)
    print("  DONE -- " + str(len(df)) + " trades analysed")
    print("  Markdown: " + str(out_md))
    print("  CSV:      " + str(out_csv))
    print("=" * 60)


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def main():
    """Build the trade analyzer v2 script."""
    print("=" * 60)
    print("BUILD: Trade Analyzer v2")
    print("=" * 60)

    # Write source
    DEST.parent.mkdir(exist_ok=True)
    DEST.write_text(SOURCE.lstrip("\n"), encoding="utf-8")
    print("  Written: " + str(DEST))

    # Verify
    ok = verify(DEST, "run_trade_analysis_v2.py")

    print("")
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("BUILD OK -- all checks passed")
        print("")
        print("Run commands:")
        print('  cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"')
        print("  python scripts/run_trade_analysis_v2.py --no-api          # dry run")
        print("  python scripts/run_trade_analysis_v2.py --days 1           # small API")
        print("  python scripts/run_trade_analysis_v2.py                    # full run")


if __name__ == "__main__":
    main()

"""
Trade analysis: cross-reference trades.csv against BingX order history.
Computes MFE, MAE, saw_green for all 231 trades.
Run: python scripts/run_trade_analysis.py
"""
import os
import sys
import csv
import time
import logging
import traceback
from datetime import datetime, timezone, date
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT       = Path(__file__).resolve().parent.parent
TRADES_CSV = ROOT / "trades.csv"
TODAY      = date.today().strftime("%Y-%m-%d")
OUT_CSV    = ROOT / "logs" / ("trade_analysis_" + TODAY + ".csv")
OUT_MD     = ROOT / "logs" / ("trade_analysis_" + TODAY + ".md")

KLINE_PATH     = "/openApi/swap/v2/quote/klines"
ALL_ORDERS_PATH = "/openApi/swap/v2/trade/allOrders"

COMMISSION_RATE = 0.0008  # 0.08% taker per side

import hashlib
import hmac as hmac_lib


def sign_and_build(base: str, path: str, params: dict, api_key: str, secret: str) -> tuple[str, dict]:
    """Build signed URL and return (url, headers)."""
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "10000"
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    sig = hmac_lib.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = base + path + "?" + qs + "&signature=" + sig
    return url, {"X-BX-APIKEY": api_key}


FILTER_FROM = "2026-03-04"  # only analyse trades with entry_time >= this date (UTC)


def load_trades() -> list[dict]:
    """Load trades.csv into list of dicts, filtered to entry_time >= FILTER_FROM."""
    if not TRADES_CSV.exists():
        log.error("trades.csv not found: " + str(TRADES_CSV))
        sys.exit(1)
    with open(TRADES_CSV, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        all_rows = list(reader)
    filtered = [
        r for r in all_rows
        if (r.get("entry_time") or r.get("timestamp") or "")[:10] >= FILTER_FROM
    ]
    log.info("Loaded %d trades total, %d after filter (>= %s)",
             len(all_rows), len(filtered), FILTER_FROM)
    return filtered


def fetch_klines(symbol: str, start_ms: int, end_ms: int, base: str, api_key: str, secret: str) -> list[dict]:
    """Fetch 5m klines for symbol in [start_ms, end_ms]. Returns list of dicts with open/high/low/close/time keys."""
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


def compute_mfe_mae(klines: list[dict], entry_price: float, direction: str,
                    commission_rate: float) -> tuple[float, float, bool]:
    """Compute MFE%, MAE%, and saw_green from klines."""
    if not klines:
        return 0.0, 0.0, False
    mfe = 0.0
    mae = 0.0
    commission_threshold = commission_rate * 2  # round-trip
    for bar in klines:
        try:
            high  = float(bar["high"])
            low   = float(bar["low"])
        except (KeyError, ValueError, TypeError):
            continue
        if direction == "LONG":
            favorable = (high - entry_price) / entry_price
            adverse   = (entry_price - low)  / entry_price
        else:
            favorable = (entry_price - low)  / entry_price
            adverse   = (high - entry_price) / entry_price
        mfe = max(mfe, favorable)
        mae = max(mae, adverse)
    saw_green = mfe > commission_threshold
    return round(mfe * 100, 4), round(mae * 100, 4), saw_green


def to_ms(ts_str: str) -> int:
    """Parse ISO timestamp string to milliseconds epoch."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def main() -> None:
    """Analyse all trades and write report."""
    load_dotenv(ROOT / ".env")
    api_key    = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    if not api_key or not secret_key:
        log.error("Missing API credentials — needed to fetch klines")
        sys.exit(1)

    config_path = ROOT / "config.yaml"
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    demo_mode = cfg.get("connector", {}).get("demo_mode", False)
    base = "https://open-api-vst.bingx.com" if demo_mode else "https://open-api.bingx.com"
    log.info("API base: %s", base)

    trades = load_trades()
    total = len(trades)

    results = []
    errors  = []

    for i, trade in enumerate(trades, 1):
        symbol    = trade.get("symbol", "")
        direction = trade.get("direction", "LONG")
        grade     = trade.get("grade", "")
        exit_reason = trade.get("exit_reason", "")
        be_raised = trade.get("be_raised", "")
        try:
            entry_price = float(trade.get("entry_price") or 0)
            exit_price  = float(trade.get("exit_price") or 0)
            pnl_net     = float(trade.get("pnl_net") or 0)
            notional    = float(trade.get("notional_usd") or 0)
        except ValueError:
            errors.append(symbol + " row " + str(i))
            continue

        entry_ts_str = trade.get("entry_time") or trade.get("timestamp") or ""
        exit_ts_str  = trade.get("timestamp") or ""

        entry_ms = to_ms(entry_ts_str)
        exit_ms  = to_ms(exit_ts_str)
        if entry_ms == 0:
            entry_ms = exit_ms - 3600000  # fallback: 1hr before exit

        # Fetch klines around the trade window
        pad_before = 5 * 60 * 1000    # 5 bars before entry
        pad_after  = 5 * 60 * 1000    # 5 bars after exit
        klines = fetch_klines(
            symbol,
            entry_ms - pad_before,
            exit_ms + pad_after,
            base, api_key, secret_key,
        )

        # Filter klines to trade window
        trade_klines = [k for k in klines
                        if entry_ms <= int(k["time"]) <= exit_ms] if klines else []

        mfe_pct, mae_pct, saw_green = compute_mfe_mae(
            trade_klines, entry_price, direction, COMMISSION_RATE)

        duration_bars = len(trade_klines) if trade_klines else 0

        results.append({
            "symbol":       symbol,
            "direction":    direction,
            "grade":        grade,
            "entry_price":  entry_price,
            "exit_price":   exit_price,
            "exit_reason":  exit_reason,
            "pnl_net":      pnl_net,
            "notional_usd": notional,
            "mfe_pct":      mfe_pct,
            "mae_pct":      mae_pct,
            "saw_green":    saw_green,
            "be_raised":    be_raised,
            "duration_bars": duration_bars,
        })

        if i % 20 == 0:
            log.info("[%d/%d] %s mfe=%.2f%% mae=%.2f%% saw_green=%s",
                     i, total, symbol, mfe_pct, mae_pct, saw_green)
        time.sleep(0.3)  # rate limit: ~200 reqs/min

    # Write CSV
    OUT_CSV.parent.mkdir(exist_ok=True)
    if results:
        fieldnames = list(results[0].keys())
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        log.info("CSV written: " + str(OUT_CSV))

    # Compute summary stats
    total_r  = len(results)
    wins     = sum(1 for r in results if r["pnl_net"] > 0)
    losses   = total_r - wins
    wr       = round(wins / total_r * 100, 1) if total_r else 0
    net_pnl  = round(sum(r["pnl_net"] for r in results), 4)
    lsg      = sum(1 for r in results if r["saw_green"] and r["pnl_net"] < 0)
    lsg_pct  = round(lsg / losses * 100, 1) if losses else 0
    avg_mfe  = round(sum(r["mfe_pct"] for r in results) / total_r, 3) if total_r else 0
    avg_mae  = round(sum(r["mae_pct"] for r in results) / total_r, 3) if total_r else 0

    by_grade: dict[str, list] = {}
    for r in results:
        by_grade.setdefault(r["grade"], []).append(r)

    by_exit: dict[str, int] = {}
    for r in results:
        by_exit[r["exit_reason"]] = by_exit.get(r["exit_reason"], 0) + 1

    md_lines = [
        "# Trade Analysis — " + TODAY,
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        "| Total trades | " + str(total_r) + " |",
        "| Win rate | " + str(wr) + "% |",
        "| Net PnL | $" + str(net_pnl) + " |",
        "| Avg MFE | " + str(avg_mfe) + "% |",
        "| Avg MAE | " + str(avg_mae) + "% |",
        "| LSG count (saw green then lost) | " + str(lsg) + " |",
        "| LSG % (of losers) | " + str(lsg_pct) + "% |",
        "",
        "## Exit Reason Breakdown",
        "",
        "| Exit Reason | Count |",
        "|-------------|-------|",
    ]
    for reason, cnt in sorted(by_exit.items(), key=lambda x: -x[1]):
        md_lines.append("| " + reason + " | " + str(cnt) + " |")

    md_lines += ["", "## Grade Performance", ""]
    md_lines += ["| Grade | Trades | WR% | Net PnL | Avg MFE | LSG% |"]
    md_lines += ["|-------|--------|-----|---------|---------|------|"]
    for grade, rows in sorted(by_grade.items()):
        g_wins   = sum(1 for r in rows if r["pnl_net"] > 0)
        g_losses = len(rows) - g_wins
        g_wr     = round(g_wins / len(rows) * 100, 1) if rows else 0
        g_pnl    = round(sum(r["pnl_net"] for r in rows), 2)
        g_mfe    = round(sum(r["mfe_pct"] for r in rows) / len(rows), 2) if rows else 0
        g_lsg    = sum(1 for r in rows if r["saw_green"] and r["pnl_net"] < 0)
        g_lsgpct = round(g_lsg / g_losses * 100, 1) if g_losses else 0
        md_lines.append("| " + grade + " | " + str(len(rows)) + " | " + str(g_wr) +
                        "% | $" + str(g_pnl) + " | " + str(g_mfe) + "% | " + str(g_lsgpct) + "% |")

    if errors:
        md_lines += ["", "## Parse Errors", ""]
        for e in errors:
            md_lines.append("- " + e)

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    log.info("Report written: " + str(OUT_MD))

    print("\n=== TRADE ANALYSIS SUMMARY ===")
    print("Trades:   " + str(total_r))
    print("Win rate: " + str(wr) + "%")
    print("Net PnL:  $" + str(net_pnl))
    print("LSG%:     " + str(lsg_pct) + "% of losers saw green first")
    print("Avg MFE:  " + str(avg_mfe) + "%")
    print("CSV:      " + str(OUT_CSV))
    print("Report:   " + str(OUT_MD))


if __name__ == "__main__":
    main()

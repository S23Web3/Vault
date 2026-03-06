"""
Build script: creates run_atr_investigation.py
Investigates losing SL_HIT trades to verify ATR-based stop loss placement.
Run: python scripts/build_atr_investigation.py
"""
import py_compile
import ast
import sys
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent / "run_atr_investigation.py"

SOURCE = r'''"""
ATR Investigation: verify stop loss distances on losing trades.
For each losing SL_HIT trade, computes implied ATR from SL distance
and optionally fetches klines to verify ATR(14) at entry time.

Run (local):   python scripts/run_atr_investigation.py --no-api
Run (API):     python scripts/run_atr_investigation.py
Run (verbose): python scripts/run_atr_investigation.py --verbose
"""
import os
import sys
import csv
import time
import logging
import argparse
import hashlib
import hmac as hmac_lib
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
TRADES_CSV = ROOT / "trades.csv"
KLINE_PATH = "/openApi/swap/v2/quote/klines"
COMMISSION_RATE = 0.0008

FULL_COLUMNS = [
    "timestamp", "symbol", "direction", "grade",
    "entry_price", "exit_price", "exit_reason", "pnl_net",
    "quantity", "notional_usd", "entry_time", "order_id",
    "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct",
    "ttp_exit_reason", "be_raised", "saw_green",
]


def parse_args():
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(description="ATR Investigation on Losing Trades")
    p.add_argument("--no-api", action="store_true",
                   help="Skip kline fetches, use implied ATR only")
    p.add_argument("--from", dest="from_date", default="2026-03-04T16:00",
                   help="Start date/time filter (default: 2026-03-04T16:00)")
    p.add_argument("--to", dest="to_date", default=None,
                   help="End date filter (default: today)")
    p.add_argument("--verbose", action="store_true",
                   help="Print per-trade detail during processing")
    return p.parse_args()


def load_trades(from_date, to_date):
    """Load trades.csv with ragged column handling (12 or 18 cols per row)."""
    if not TRADES_CSV.exists():
        log.error("trades.csv not found: " + str(TRADES_CSV))
        sys.exit(1)
    rows = []
    with open(TRADES_CSV, encoding="utf-8") as fh:
        reader = csv.reader(fh)
        _header = next(reader)
        for line in reader:
            while len(line) < 18:
                line.append("")
            rows.append(dict(zip(FULL_COLUMNS, line[:18])))
    from_cmp = from_date if "T" in from_date else from_date + "T00:00"
    to_cmp = to_date + "T23:59:59" if to_date and "T" not in to_date else (to_date or "9999")
    filtered = []
    for r in rows:
        ts = r.get("entry_time") or r.get("timestamp") or ""
        if ts[:19] >= from_cmp[:19] and ts[:19] <= to_cmp[:19]:
            filtered.append(r)
    log.info("Loaded %d trades, %d after date filter", len(rows), len(filtered))
    return filtered


def sfloat(val, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def sign_and_build(base, path, params, api_key, secret):
    """Build BingX signed URL and return (url, headers)."""
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


def to_ms(ts_str):
    """Parse ISO timestamp to milliseconds epoch."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def compute_atr_from_klines(klines, period=14):
    """Compute ATR using Wilder's RMA from kline list. Returns ATR at last bar."""
    highs = []
    lows = []
    closes = []
    for k in klines:
        try:
            highs.append(float(k["high"]))
            lows.append(float(k["low"]))
            closes.append(float(k["close"]))
        except (KeyError, ValueError, TypeError):
            continue
    n = len(highs)
    if n < period + 1:
        return 0.0
    tr = [0.0] * n
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
    atr_vals = [0.0] * n
    atr_vals[period - 1] = sum(tr[:period]) / period
    for i in range(period, n):
        atr_vals[i] = (atr_vals[i - 1] * (period - 1) + tr[i]) / period
    return atr_vals[-1]


def classify_verdict(implied_atr, verified_atr, atr_ratio, no_api):
    """Classify the ATR investigation verdict for a non-BE trade."""
    if not no_api and verified_atr > 0:
        ratio = implied_atr / verified_atr
        if 0.85 <= ratio <= 1.15:
            return "CONFIRMED"
        if ratio > 1.15:
            return "SLIPPAGE"
        if ratio < 0.85:
            return "UNDER_SL"
        return "UNKNOWN"
    # Local-only classification by volatility tier
    if atr_ratio > 0.02:
        return "EXTREME_VOL"
    if atr_ratio > 0.01:
        return "HIGH_VOL"
    if atr_ratio > 0.005:
        return "MED_VOL"
    if atr_ratio >= 0.003:
        return "NORMAL"
    return "BELOW_MIN"


def print_divider(char="=", width=120):
    """Print a divider line."""
    print(char * width)


def main():
    """Run ATR investigation on losing SL_HIT trades."""
    args = parse_args()
    from_date = args.from_date
    to_date = args.to_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Always read config for leverage and multipliers
    config_path = ROOT / "config.yaml"
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    leverage = cfg.get("position", {}).get("leverage", 10)
    sl_mult = cfg.get("four_pillars", {}).get("sl_atr_mult", 2.0)
    min_atr = cfg.get("risk", {}).get("min_atr_ratio", 0.003)

    # API setup (optional)
    base = ""
    api_key = ""
    secret_key = ""
    if not args.no_api:
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
        except ImportError:
            pass
        api_key = os.getenv("BINGX_API_KEY", "")
        secret_key = os.getenv("BINGX_SECRET_KEY", "")
        demo_mode = cfg.get("connector", {}).get("demo_mode", False)
        base = "https://open-api-vst.bingx.com" if demo_mode else "https://open-api.bingx.com"
        if not api_key or not secret_key:
            log.warning("No API credentials -- falling back to --no-api mode")
            args.no_api = True

    trades = load_trades(from_date, to_date)

    # Filter to losing SL_HIT trades
    losers = []
    for t in trades:
        pnl = sfloat(t.get("pnl_net"))
        reason = t.get("exit_reason", "")
        if pnl < 0 and "SL" in reason:
            losers.append(t)

    if not losers:
        print("No losing SL_HIT trades found in date range.")
        return

    # Split BE vs non-BE
    be_losers = []
    full_losers = []
    for t in losers:
        be = str(t.get("be_raised", "")).strip().lower() == "true"
        if be:
            be_losers.append(t)
        else:
            full_losers.append(t)

    print("")
    print_divider()
    print("  ATR INVESTIGATION: LOSING SL_HIT TRADES")
    print("  Period: " + from_date + " to " + to_date)
    print("  Config: sl_atr_mult=" + str(sl_mult)
          + "  min_atr_ratio=" + str(min_atr)
          + "  leverage=" + str(leverage) + "x")
    print("  Mode: " + ("LOCAL ONLY (--no-api)" if args.no_api else "API VERIFICATION"))
    print_divider()

    # ----------------------------------------------------------------
    # NON-BE LOSERS (full SL hit)
    # ----------------------------------------------------------------
    results_full = []
    if full_losers:
        print("")
        print("--- NON-BE LOSERS (full SL hit, "
              + str(len(full_losers)) + " trades) ---")
        print("")
        hdr = ("{:<3s}  {:<14s}  {:<6s}  {:<12s}  {:<12s}  {:>8s}  {:>8s}"
               "  {:>10s}  {:>9s}  {:>8s}  {:<12s}")
        print(hdr.format(
            "#", "Symbol", "Dir", "Entry", "Exit", "PnL",
            "SL%", "Impl ATR", "ATR Rat%", "Marg%", "Verdict"))
        print("-" * 120)

        for idx, t in enumerate(full_losers, 1):
            entry = sfloat(t["entry_price"])
            exit_p = sfloat(t["exit_price"])
            direction = t["direction"]
            pnl = sfloat(t["pnl_net"])
            if entry <= 0:
                continue

            # Compute implied ATR from SL distance
            if direction == "LONG":
                sl_dist = entry - exit_p
            else:
                sl_dist = exit_p - entry
            implied_atr = abs(sl_dist) / sl_mult
            atr_ratio = implied_atr / entry
            sl_pct = abs(sl_dist) / entry * 100
            margin_pct = sl_pct * leverage

            # API verification
            verified_atr = 0.0
            if not args.no_api:
                entry_ts = t.get("entry_time") or t.get("timestamp") or ""
                entry_ms = to_ms(entry_ts)
                if entry_ms > 0:
                    start_ms = entry_ms - (201 * 5 * 60 * 1000)
                    klines = fetch_klines(
                        t["symbol"], start_ms, entry_ms,
                        base, api_key, secret_key)
                    verified_atr = compute_atr_from_klines(klines, period=14)
                    if args.verbose:
                        log.info(
                            "[%d/%d] %s: %d klines, verified=%.8f implied=%.8f",
                            idx, len(full_losers), t["symbol"],
                            len(klines), verified_atr, implied_atr)
                    time.sleep(0.3)

            verdict = classify_verdict(
                implied_atr, verified_atr, atr_ratio, args.no_api)

            row_fmt = ("{:<3d}  {:<14s}  {:<6s}  {:<12s}  {:<12s}  {:>8s}"
                       "  {:>7.2f}%  {:>10.6f}  {:>8.3f}%  {:>7.1f}%  {:<12s}")
            pnl_str = "{:+.2f}".format(pnl)
            print(row_fmt.format(
                idx, t["symbol"], direction,
                t["entry_price"][:12], t["exit_price"][:12],
                pnl_str, sl_pct, implied_atr,
                atr_ratio * 100, margin_pct, verdict))

            results_full.append({
                "symbol": t["symbol"],
                "direction": direction,
                "entry": entry,
                "exit": exit_p,
                "pnl": pnl,
                "sl_pct": sl_pct,
                "implied_atr": implied_atr,
                "verified_atr": verified_atr,
                "atr_ratio": atr_ratio,
                "margin_pct": margin_pct,
                "verdict": verdict,
            })

    # ----------------------------------------------------------------
    # BE LOSERS (breakeven exit)
    # ----------------------------------------------------------------
    if be_losers:
        print("")
        print("--- BE LOSERS (breakeven exit, "
              + str(len(be_losers)) + " trades) ---")
        print("")
        be_hdr = "{:<3s}  {:<14s}  {:<6s}  {:<12s}  {:<12s}  {:>9s}  {:<30s}"
        print(be_hdr.format(
            "#", "Symbol", "Dir", "Entry", "Exit", "PnL", "Note"))
        print("-" * 95)
        for idx, t in enumerate(be_losers, 1):
            pnl_str = "{:+.4f}".format(sfloat(t["pnl_net"]))
            print(be_hdr.format(
                str(idx), t["symbol"], t["direction"],
                t["entry_price"][:12], t["exit_price"][:12],
                pnl_str, "BE raised, SL at entry+commission"))

    # ----------------------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------------------
    print("")
    print_divider()
    print("  SUMMARY")
    print_divider()

    total_loss = sum(sfloat(t["pnl_net"]) for t in losers)
    full_loss = sum(sfloat(t["pnl_net"]) for t in full_losers)
    be_loss = sum(sfloat(t["pnl_net"]) for t in be_losers)

    print("")
    print("  Total losing SL_HIT trades: " + str(len(losers)))
    print("    Non-BE (full SL):  " + str(len(full_losers))
          + "  total: $" + "{:.2f}".format(full_loss))
    print("    BE exit:           " + str(len(be_losers))
          + "  total: $" + "{:.2f}".format(be_loss))
    print("    Combined loss:     $" + "{:.2f}".format(total_loss))

    if results_full:
        avg_sl = sum(r["sl_pct"] for r in results_full) / len(results_full)
        avg_ar = sum(r["atr_ratio"] for r in results_full) / len(results_full)
        avg_mg = sum(r["margin_pct"] for r in results_full) / len(results_full)
        worst = min(results_full, key=lambda r: r["pnl"])
        high_vol = [r for r in results_full if r["atr_ratio"] > 0.01]
        danger = [r for r in results_full if r["margin_pct"] > 20]

        print("")
        print("  Non-BE Analysis:")
        print("    Avg SL distance:    " + "{:.2f}".format(avg_sl) + "%")
        print("    Avg ATR ratio:      "
              + "{:.3f}".format(avg_ar * 100) + "%")
        print("    Avg margin impact:  "
              + "{:.1f}".format(avg_mg) + "% (at "
              + str(leverage) + "x leverage)")
        print("    Worst trade:        " + worst["symbol"]
              + " $" + "{:.2f}".format(worst["pnl"])
              + " (" + "{:.2f}".format(worst["sl_pct"]) + "% SL distance)")

        print("")
        print("  Risk Flags:")
        print("    ATR ratio > 1% (high vol):    "
              + str(len(high_vol)) + " trades")
        print("    Margin impact > 20%:          "
              + str(len(danger)) + " trades")

        if high_vol:
            print("")
            print("  High Volatility Trades (atr_ratio > 1%):")
            for r in sorted(high_vol, key=lambda x: -x["atr_ratio"]):
                print("    " + r["symbol"] + " " + r["direction"]
                      + "  atr_ratio="
                      + "{:.3f}".format(r["atr_ratio"] * 100) + "%"
                      + "  SL=" + "{:.2f}".format(r["sl_pct"]) + "%"
                      + "  margin_hit="
                      + "{:.1f}".format(r["margin_pct"]) + "%"
                      + "  pnl=$" + "{:.2f}".format(r["pnl"]))

        # API verification summary
        if not args.no_api and results_full:
            verified = [r for r in results_full if r["verified_atr"] > 0]
            if verified:
                matches = [r for r in verified
                           if 0.85 <= (r["implied_atr"] / r["verified_atr"]) <= 1.15]
                print("")
                print("  API Verification:")
                print("    Verified: " + str(len(verified))
                      + "/" + str(len(results_full)))
                print("    ATR confirmed (within 15%): "
                      + str(len(matches)) + "/" + str(len(verified)))
                mismatches = [r for r in verified
                              if not (0.85 <= (r["implied_atr"] / r["verified_atr"]) <= 1.15)]
                if mismatches:
                    print("    MISMATCHES:")
                    for r in mismatches:
                        rat = r["implied_atr"] / r["verified_atr"]
                        print("      " + r["symbol"]
                              + " implied="
                              + "{:.8f}".format(r["implied_atr"])
                              + " verified="
                              + "{:.8f}".format(r["verified_atr"])
                              + " ratio=" + "{:.2f}".format(rat))

    # ----------------------------------------------------------------
    # RECOMMENDATIONS
    # ----------------------------------------------------------------
    print("")
    print("  Recommendations:")
    if results_full:
        high_count = len([r for r in results_full if r["atr_ratio"] > 0.01])
        danger_count = len([r for r in results_full if r["margin_pct"] > 20])
        if high_count > 0:
            print("    1. Consider max_atr_ratio cap (e.g. 0.015) to block"
                  " ultra-volatile entries")
        if danger_count > 0:
            print("    2. " + str(danger_count) + " trades consumed >20%"
                  " of margin -- reduce leverage or use ATR-scaled sizing")
        if avg_mg > 10:
            print("    3. Average margin impact "
                  + "{:.1f}".format(avg_mg)
                  + "% is high -- consider sl_atr_mult=1.5")
    else:
        print("    No non-BE losers to analyze.")
    print("")

    # ----------------------------------------------------------------
    # MARKDOWN REPORT
    # ----------------------------------------------------------------
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    md_path = ROOT / "logs" / ("atr_investigation_" + today_str + ".md")
    md_path.parent.mkdir(exist_ok=True)
    md = []
    md.append("# ATR Investigation: Losing SL_HIT Trades")
    md.append("")
    md.append("Generated: "
              + datetime.now(timezone.utc).isoformat()[:19] + "Z")
    md.append("Period: " + from_date + " to " + to_date)
    md.append("Config: sl_atr_mult=" + str(sl_mult)
              + " min_atr_ratio=" + str(min_atr)
              + " leverage=" + str(leverage) + "x")
    md.append("")

    if results_full:
        md.append("## Non-BE Losers (Full SL Hit)")
        md.append("")
        md.append("| #   | Symbol         | Dir    | Entry       "
                  "| Exit        | PnL      | SL%    "
                  "| ATR Ratio | Margin% | Verdict      |")
        md.append("|-----|----------------|--------|-------------"
                  "|-------------|----------|--------"
                  "|-----------|---------|--------------|")
        for idx, r in enumerate(results_full, 1):
            md.append(
                "| " + str(idx).ljust(3)
                + " | " + r["symbol"].ljust(14)
                + " | " + r["direction"].ljust(6)
                + " | " + "{:.6f}".format(r["entry"]).ljust(11)
                + " | " + "{:.6f}".format(r["exit"]).ljust(11)
                + " | $" + "{:+.2f}".format(r["pnl"]).ljust(7)
                + " | " + "{:.2f}%".format(r["sl_pct"]).ljust(6)
                + " | " + "{:.3f}%".format(r["atr_ratio"] * 100).ljust(9)
                + " | " + "{:.1f}%".format(r["margin_pct"]).ljust(7)
                + " | " + r["verdict"].ljust(12) + " |")
        md.append("")

    if be_losers:
        md.append("## BE Losers (Breakeven Exit)")
        md.append("")
        md.append("| #   | Symbol         | Dir    | PnL       | Note     |")
        md.append("|-----|----------------|--------|-----------|----------|")
        for idx, t in enumerate(be_losers, 1):
            md.append(
                "| " + str(idx).ljust(3)
                + " | " + t["symbol"].ljust(14)
                + " | " + t["direction"].ljust(6)
                + " | $" + "{:+.4f}".format(sfloat(t["pnl_net"])).ljust(8)
                + " | BE exit  |")
        md.append("")

    md.append("## Summary")
    md.append("")
    md.append("- Total losing SL trades: " + str(len(losers)))
    md.append("- Non-BE: " + str(len(full_losers))
              + " ($" + "{:.2f}".format(full_loss) + ")")
    md.append("- BE exit: " + str(len(be_losers))
              + " ($" + "{:.2f}".format(be_loss) + ")")
    if results_full:
        md.append("- Avg SL distance: " + "{:.2f}".format(avg_sl) + "%")
        md.append("- Avg ATR ratio: "
                  + "{:.3f}".format(avg_ar * 100) + "%")
        md.append("- Avg margin impact: "
                  + "{:.1f}".format(avg_mg) + "%")
    md.append("")

    md_path.write_text("\n".join(md), encoding="utf-8")
    print("  Report: " + str(md_path))
    print("")


if __name__ == "__main__":
    main()
'''


def main():
    """Build run_atr_investigation.py and verify syntax."""
    OUTPUT.parent.mkdir(exist_ok=True)
    if OUTPUT.exists():
        log_msg = "WARNING: " + str(OUTPUT) + " already exists -- overwriting"
        print(log_msg)
    OUTPUT.write_text(SOURCE, encoding="utf-8")
    print("Written: " + str(OUTPUT))

    errors = []
    try:
        py_compile.compile(str(OUTPUT), doraise=True)
        print("  SYNTAX OK: " + str(OUTPUT))
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        errors.append("py_compile")

    try:
        source_text = OUTPUT.read_text(encoding="utf-8")
        ast.parse(source_text, filename=str(OUTPUT))
        print("  AST OK: " + str(OUTPUT))
    except SyntaxError as e:
        print("  AST ERROR line " + str(e.lineno) + ": " + str(e.msg))
        errors.append("ast")

    if errors:
        print("BUILD FAILED: " + ", ".join(errors))
        sys.exit(1)
    else:
        print("BUILD OK")
        print("")
        bingx_root = OUTPUT.parent.parent
        print("Run commands:")
        print('  cd "' + str(bingx_root) + '"')
        print("  python scripts/run_atr_investigation.py --no-api       # local analysis")
        print("  python scripts/run_atr_investigation.py                # with API verification")
        print("  python scripts/run_atr_investigation.py --verbose      # verbose API mode")


if __name__ == "__main__":
    main()

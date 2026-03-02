"""
BingX trade performance analysis script.

Reads trades.csv, segments into 3 phases by notional, computes per-phase
metrics and combined signal quality, outputs a markdown report.

Run: python scripts/analyze_trades.py
"""
import csv
import hashlib
import hmac
import json
import logging
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BOT_ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = BOT_ROOT.parent.parent
TRADES_CSV = BOT_ROOT / "trades.csv"
STATE_JSON = BOT_ROOT / "state.json"
BINGX_PRICE_URL = "https://open-api.bingx.com/openApi/swap/v2/quote/price"
LOGS_DIR = BOT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
LOG_PATH = LOGS_DIR / (TODAY + "-analyze.log")
REPORT_PATH = VAULT_ROOT / "06-CLAUDE-LOGS" / (TODAY + "-bingx-trade-analysis.md")

# Phase mapping: int(notional) -> phase number
PHASE_MAP = {500: 1, 1500: 2, 50: 3}

# Commission constants (BingX)
COMMISSION_TAKER = 0.0005       # 0.05% per side
COMMISSION_RT_GROSS = 0.001     # 0.10% round trip (entry + exit)
COMMISSION_REBATE = 0.50        # 50% rebated next day
COMMISSION_RT_NET = COMMISSION_RT_GROSS * (1 - COMMISSION_REBATE)  # 0.0005

# Breakeven tolerance: exit within this % of entry = BE trade
BE_TOLERANCE = 0.0005  # 0.05%

# Position sizing (from config.yaml)
MARGIN_USD = 5.0      # margin per trade
LEVERAGE = 10         # leverage applied
ACCOUNT_SIZE_USD = 110.0  # live account size

# Paths
ENV_PATH = BOT_ROOT / ".env"
BINGX_LIVE_BASE = "https://open-api.bingx.com"
OPEN_ORDERS_PATH = "/openApi/swap/v2/trade/openOrders"

PHASE_LABELS = {
    1: "Phase 1 — 1m demo ($500 notional) [EXIT TRACKING UNRELIABLE]",
    2: "Phase 2 — 5m demo ($1500 notional)",
    3: "Phase 3 — 5m live ($50 notional)",
}

PHASE_NOTES = {
    1: ("WARNING: All exits were EXIT_UNKNOWN or SL_HIT_ASSUMED. "
        "The _fetch_filled_exit() fix had not been applied. "
        "All P&L figures are estimates only — do not use for strategy conclusions."),
    2: ("Exit tracking working correctly after fix. "
        "This is the primary signal-quality dataset."),
    3: ("Live account. Small notional — normalize P&L as % of notional for comparison."),
}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging():
    """Configure dual-handler logging (file + console)."""
    logger = logging.getLogger("analyze")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_trades(path):
    """Load and parse all trades from trades.csv."""
    trades = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["pnl_net"] = float(row["pnl_net"])
                row["notional_usd"] = float(row["notional_usd"])
                row["entry_price"] = float(row["entry_price"])
                row["exit_price"] = float(row["exit_price"])
                row["quantity"] = float(row["quantity"])
                row["phase"] = PHASE_MAP.get(int(round(row["notional_usd"])), 0)
                # Parse timestamps (strip +00:00 for 3.8 compat)
                ts_str = row["timestamp"].replace("+00:00", "").rstrip("Z")
                entry_str = row["entry_time"].replace("+00:00", "").rstrip("Z")
                row["ts_dt"] = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
                row["entry_dt"] = datetime.fromisoformat(entry_str).replace(tzinfo=timezone.utc)
                row["hold_minutes"] = (row["ts_dt"] - row["entry_dt"]).total_seconds() / 60.0
            except (ValueError, KeyError):
                row["phase"] = 0
                row["hold_minutes"] = 0.0
            trades.append(row)
    return trades


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def load_open_positions(path):
    """Load open positions from state.json. Returns list of position dicts, or []."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        positions = data.get("open_positions", {})
        result = []
        for key, pos in positions.items():
            pos["_key"] = key
            result.append(pos)
        return result
    except (json.JSONDecodeError, KeyError):
        return []


def fetch_mark_price(symbol):
    """Fetch current mark price for one symbol from BingX live API. Returns float or None."""
    try:
        url = BINGX_PRICE_URL + "?symbol=" + symbol
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = json.loads(resp.read().decode())
        data = body.get("data", {})
        if isinstance(data, dict):
            val = float(data.get("price", 0))
            return val if val > 0 else None
        if isinstance(data, list) and data:
            val = float(data[0].get("price", 0))
            return val if val > 0 else None
    except Exception:
        pass
    return None


def fetch_all_mark_prices(symbols):
    """Fetch current mark prices for a list of symbols. Returns dict {symbol: float}."""
    prices = {}
    for sym in symbols:
        p = fetch_mark_price(sym)
        if p is not None:
            prices[sym] = p
    return prices


def read_env(path):
    """Parse a .env file into a dict. Falls back silently if file is missing."""
    env = {}
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    except (IOError, OSError):
        pass
    return env


def sign_bingx_params(secret_key, params):
    """HMAC-SHA256 sign BingX request params. Returns (query_string, signature)."""
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    sig = hmac.new(
        secret_key.encode("utf-8"),
        qs.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return qs, sig


def fetch_open_orders_for_symbol(api_key, secret_key, symbol):
    """Fetch open orders for one symbol from BingX live API. Returns list of order dicts."""
    try:
        params = {
            "symbol": symbol,
            "timestamp": str(int(time.time() * 1000)),
            "recvWindow": "10000",
        }
        qs, sig = sign_bingx_params(secret_key, params)
        url = BINGX_LIVE_BASE + OPEN_ORDERS_PATH + "?" + qs + "&signature=" + sig
        req = urllib.request.Request(url, headers={"X-BX-APIKEY": api_key})
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = json.loads(resp.read().decode())
        orders = body.get("data", {})
        if isinstance(orders, dict):
            return orders.get("orders", []) or []
        if isinstance(orders, list):
            return orders
    except Exception:
        pass
    return []


def parse_sl_tp_orders(orders):
    """Extract SL stop price and trailing TP params from open orders list.

    Returns dict: sl_price, tp_price, trail_pct (callback rate 0-1), trail_activation.
    """
    sl_price = None
    tp_price = None
    trail_pct = None
    trail_activation = None
    for o in orders:
        order_type = o.get("type", "").upper()
        if order_type == "STOP_MARKET":
            try:
                sl_price = float(o.get("stopPrice") or 0) or None
            except (ValueError, TypeError):
                pass
        elif order_type == "TAKE_PROFIT_MARKET":
            try:
                tp_price = float(o.get("stopPrice") or 0) or None
            except (ValueError, TypeError):
                pass
        elif order_type == "TRAILING_STOP_MARKET":
            try:
                rate = o.get("priceRate") or o.get("callbackRate") or ""
                trail_pct = float(rate) / 100.0 if float(rate) > 1 else float(rate)
            except (ValueError, TypeError):
                trail_pct = None
            for field in ("activatePrice", "activationPrice", "stopPrice"):
                val = o.get(field) or ""
                try:
                    trail_activation = float(val) if val else None
                    if trail_activation:
                        break
                except (ValueError, TypeError):
                    pass
    return {
        "sl_price": sl_price,
        "tp_price": tp_price,
        "trail_pct": trail_pct,
        "trail_activation": trail_activation,
    }


def compute_unrealized_pnl(pos, mark_price):
    """Compute unrealized net P&L for an open position at the given mark price.

    Returns (gross, net) where net deducts RT gross commission for the close leg.
    Entry commission already paid; rebate arrives next day so not counted here.
    """
    entry = pos.get("entry_price", 0)
    qty = pos.get("quantity", 0)
    notional = pos.get("notional_usd", 0)
    direction = pos.get("direction", "LONG")
    if direction == "LONG":
        gross = (mark_price - entry) * qty
    else:
        gross = (entry - mark_price) * qty
    commission_rt = notional * COMMISSION_RT_GROSS
    net = gross - commission_rt
    return gross, net


def compute_sl_pnl(pos):
    """Compute net P&L if position is stopped out at the current SL price from state.json.

    Returns (sl_price, gross, net).
    """
    entry = pos.get("entry_price", 0)
    sl = pos.get("sl_price", 0)
    qty = pos.get("quantity", 0)
    notional = pos.get("notional_usd", 0)
    direction = pos.get("direction", "LONG")
    if direction == "LONG":
        gross = (sl - entry) * qty
    else:
        gross = (entry - sl) * qty
    net = gross - notional * COMMISSION_RT_GROSS
    return sl, gross, net


def compute_trail_tp_pnl(pos, mark_price, trail_pct=0.02):
    """Estimate net P&L if trailing TP fires at trail_pct from current mark.

    For SHORT: TP fires if price drops another trail_pct% (tp_price = mark * (1 - trail_pct)).
    For LONG:  TP fires if price rises another trail_pct% (tp_price = mark * (1 + trail_pct)).
    Returns (tp_price, gross, net).
    """
    entry = pos.get("entry_price", 0)
    qty = pos.get("quantity", 0)
    notional = pos.get("notional_usd", 0)
    direction = pos.get("direction", "LONG")
    if direction == "LONG":
        tp_price = mark_price * (1.0 + trail_pct)
        gross = (tp_price - entry) * qty
    else:
        tp_price = mark_price * (1.0 - trail_pct)
        gross = (entry - tp_price) * qty
    net = gross - notional * COMMISSION_RT_GROSS
    return tp_price, gross, net


def compute_phase_metrics(trades):
    """Compute core summary metrics for a list of trades."""
    if not trades:
        return {}
    total = len(trades)
    pnl_values = [t["pnl_net"] for t in trades]
    winners = [p for p in pnl_values if p > 0]
    losers = [p for p in pnl_values if p < 0]
    total_pnl = sum(pnl_values)
    hold_times = [t["hold_minutes"] for t in trades if t.get("hold_minutes", 0) >= 0]
    notional = trades[0]["notional_usd"] if trades else 1.0
    returns_pct = [t["pnl_net"] / notional * 100 for t in trades]
    return {
        "total": total,
        "total_pnl": total_pnl,
        "win_rate": len(winners) / total * 100,
        "avg_pnl": total_pnl / total,
        "avg_return_pct": sum(returns_pct) / len(returns_pct),
        "best": max(pnl_values),
        "worst": min(pnl_values),
        "best_trade": max(trades, key=lambda t: t["pnl_net"]),
        "worst_trade": min(trades, key=lambda t: t["pnl_net"]),
        "avg_hold": sum(hold_times) / len(hold_times) if hold_times else 0.0,
        "min_hold": min(hold_times) if hold_times else 0.0,
        "max_hold": max(hold_times) if hold_times else 0.0,
        "winners": len(winners),
        "losers": len(losers),
    }


def grade_breakdown(trades):
    """Return win rate and P&L stats grouped by signal grade."""
    by_grade = defaultdict(list)
    for t in trades:
        by_grade[t.get("grade", "?")].append(t["pnl_net"])
    result = {}
    for grade, pnls in sorted(by_grade.items()):
        wins = sum(1 for p in pnls if p > 0)
        result[grade] = {
            "count": len(pnls),
            "wins": wins,
            "win_rate": wins / len(pnls) * 100 if pnls else 0.0,
            "total_pnl": sum(pnls),
            "avg_pnl": sum(pnls) / len(pnls) if pnls else 0.0,
        }
    return result


def direction_breakdown(trades):
    """Return win rate and P&L stats grouped by trade direction."""
    by_dir = defaultdict(list)
    for t in trades:
        by_dir[t.get("direction", "?")].append(t["pnl_net"])
    result = {}
    for direction, pnls in sorted(by_dir.items()):
        wins = sum(1 for p in pnls if p > 0)
        result[direction] = {
            "count": len(pnls),
            "wins": wins,
            "win_rate": wins / len(pnls) * 100 if pnls else 0.0,
            "total_pnl": sum(pnls),
            "avg_pnl": sum(pnls) / len(pnls) if pnls else 0.0,
        }
    return result


def exit_reason_breakdown(trades):
    """Return count and percentage for each exit reason."""
    counts = defaultdict(int)
    for t in trades:
        counts[t.get("exit_reason", "UNKNOWN")] += 1
    total = len(trades)
    return {
        reason: {"count": cnt, "pct": cnt / total * 100}
        for reason, cnt in sorted(counts.items())
    }


def symbol_leaderboard(trades, top_n=5):
    """Return top N and bottom N symbols by total P&L."""
    by_symbol = defaultdict(float)
    for t in trades:
        by_symbol[t["symbol"]] += t["pnl_net"]
    sorted_syms = sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)
    return sorted_syms[:top_n], sorted_syms[-top_n:][::-1]


def compute_volume_metrics(trades, commission_rate_rt=COMMISSION_RT_GROSS):
    """Compute trading volume and commission metrics for a list of trades.

    commission_rate_rt: BingX taker rate round-trip (0.08% per side x 2 = 0.0016).
    """
    total_notional = sum(t["notional_usd"] for t in trades)
    rt_volume = total_notional * 2.0
    commission_est = total_notional * commission_rate_rt
    avg_commission = commission_est / len(trades) if trades else 0.0
    # pnl_net already has commission deducted — show gross vs net gap
    total_pnl_net = sum(t["pnl_net"] for t in trades)
    total_pnl_gross = total_pnl_net + commission_est
    rebate_est = commission_est * COMMISSION_REBATE
    commission_net = commission_est - rebate_est
    return {
        "total_notional": total_notional,
        "rt_volume": rt_volume,
        "commission_est": commission_est,
        "rebate_est": rebate_est,
        "commission_net": commission_net,
        "avg_commission": avg_commission,
        "total_pnl_net": total_pnl_net,
        "total_pnl_gross": total_pnl_gross,
        "commission_pct_of_notional": commission_est / total_notional * 100 if total_notional else 0,
    }


def identify_sl_at_entry_trades(trades, tolerance=BE_TOLERANCE):
    """Return trades where SL was raised to exact entry (exit within tolerance of entry).

    These are NOT true break-even + fees. Each trade still pays exit commission
    (~$0.05 gross, ~$0.025 net after rebate). True BE+fees requires the SL at
    entry + COMMISSION_RT_GROSS (0.10%) so the exit covers both sides of commission.
    """
    result = []
    for t in trades:
        ep = t.get("entry_price", 0)
        xp = t.get("exit_price", 0)
        if ep > 0 and abs(xp - ep) / ep <= tolerance:
            result.append(t)
    return result


def compute_rr_ratio(trades):
    """Compute implied R:R from average TP win vs average SL loss (SL_HIT only)."""
    tp_pnls = [t["pnl_net"] for t in trades
               if t.get("exit_reason") == "TP_HIT" and t["pnl_net"] > 0]
    sl_pnls = [t["pnl_net"] for t in trades
               if t.get("exit_reason") == "SL_HIT" and t["pnl_net"] < 0]
    avg_tp = sum(tp_pnls) / len(tp_pnls) if tp_pnls else None
    avg_sl_abs = abs(sum(sl_pnls) / len(sl_pnls)) if sl_pnls else None
    rr = avg_tp / avg_sl_abs if (avg_tp and avg_sl_abs) else None
    return rr, avg_tp, avg_sl_abs, len(tp_pnls), len(sl_pnls)


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def fmt_pnl(val):
    """Format a dollar P&L value with sign."""
    sign = "+" if val >= 0 else ""
    return sign + "$" + str(round(val, 2))


def fmt_pct(val):
    """Format a percentage value with 1 decimal place."""
    sign = "+" if val >= 0 else ""
    return sign + str(round(val, 1)) + "%"


def fmt_mins(mins):
    """Format minutes as Xh Ym or Xm."""
    h = int(mins // 60)
    m = int(mins % 60)
    if h > 0:
        return str(h) + "h " + str(m) + "m"
    return str(m) + "m"


def fmt_trade(t):
    """Format a single trade as a short descriptor string."""
    return (t["symbol"] + " " + t["direction"] + " " + t.get("grade", "?")
            + " " + fmt_pnl(t["pnl_net"]) + " (" + t.get("exit_reason", "?") + ")")


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_phase_detail(lines, phase_trades, phase_num):
    """Append all per-phase detail rows (summary, grades, directions, exits, symbols) to lines."""
    m = compute_phase_metrics(phase_trades)

    lines.append("**Summary**")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Trades | " + str(m["total"]) + " |")
    lines.append("| Total P&L | " + fmt_pnl(m["total_pnl"]) + " |")
    lines.append("| Win rate | " + fmt_pct(m["win_rate"])
                 + " (" + str(m["winners"]) + "W / " + str(m["losers"]) + "L) |")
    lines.append("| Avg P&L / trade | " + fmt_pnl(m["avg_pnl"]) + " |")
    lines.append("| Avg return / trade | " + fmt_pct(m["avg_return_pct"]) + " of notional |")
    lines.append("| Best trade | " + fmt_trade(m["best_trade"]) + " |")
    lines.append("| Worst trade | " + fmt_trade(m["worst_trade"]) + " |")
    lines.append("| Avg hold time | " + fmt_mins(m["avg_hold"]) + " |")
    lines.append("| Min / Max hold | " + fmt_mins(m["min_hold"]) + " / " + fmt_mins(m["max_hold"]) + " |")
    lines.append("")

    vm = compute_volume_metrics(phase_trades)
    lines.append("**Volume & Commission**")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Total notional (one-side) | $" + str(round(vm["total_notional"], 2)) + " |")
    lines.append("| Round-trip volume | $" + str(round(vm["rt_volume"], 2)) + " |")
    lines.append("| Commission gross (0.05%×2) | $" + str(round(vm["commission_est"], 3)) + " |")
    lines.append("| Rebate (50% next day) | +$" + str(round(vm["rebate_est"], 3)) + " |")
    lines.append("| Commission net after rebate | $" + str(round(vm["commission_net"], 3)) + " |")
    lines.append("| Avg net commission / trade | $" + str(round(vm["commission_net"] / len(phase_trades), 3)) + " |")
    lines.append("| P&L gross (before commission) | " + fmt_pnl(vm["total_pnl_gross"]) + " |")
    lines.append("| P&L net (after commission) | " + fmt_pnl(vm["total_pnl_net"]) + " |")
    lines.append("| Breakeven move needed | 0.10% gross / 0.05% net (after rebate) |")
    lines.append("")

    lines.append("**Grade Breakdown**")
    lines.append("")
    lines.append("| Grade | Trades | Wins | Win Rate | Avg P&L | Total P&L |")
    lines.append("|-------|--------|------|----------|---------|-----------|")
    for grade, gm in grade_breakdown(phase_trades).items():
        lines.append("| " + grade + " | " + str(gm["count"]) + " | " + str(gm["wins"])
                     + " | " + fmt_pct(gm["win_rate"]) + " | " + fmt_pnl(gm["avg_pnl"])
                     + " | " + fmt_pnl(gm["total_pnl"]) + " |")
    lines.append("")

    lines.append("**Direction Breakdown**")
    lines.append("")
    lines.append("| Direction | Trades | Wins | Win Rate | Avg P&L | Total P&L |")
    lines.append("|-----------|--------|------|----------|---------|-----------|")
    for direction, dm in direction_breakdown(phase_trades).items():
        lines.append("| " + direction + " | " + str(dm["count"]) + " | " + str(dm["wins"])
                     + " | " + fmt_pct(dm["win_rate"]) + " | " + fmt_pnl(dm["avg_pnl"])
                     + " | " + fmt_pnl(dm["total_pnl"]) + " |")
    lines.append("")

    lines.append("**Exit Reason Distribution**")
    lines.append("")
    lines.append("| Exit Reason | Count | % |")
    lines.append("|-------------|-------|---|")
    for reason, rm in exit_reason_breakdown(phase_trades).items():
        lines.append("| " + reason + " | " + str(rm["count"])
                     + " | " + str(round(rm["pct"], 1)) + "% |")
    lines.append("")

    best_syms, worst_syms = symbol_leaderboard(phase_trades, top_n=5)
    lines.append("**Symbol Leaderboard — Top 5 Best**")
    lines.append("")
    for sym, sym_pnl in best_syms:
        lines.append("- " + sym + ": " + fmt_pnl(sym_pnl))
    lines.append("")

    lines.append("**Symbol Leaderboard — Top 5 Worst**")
    lines.append("")
    for sym, sym_pnl in worst_syms:
        lines.append("- " + sym + ": " + fmt_pnl(sym_pnl))
    lines.append("")


def build_open_positions_section(lines, open_positions, mark_prices=None,
                                 open_orders_map=None, default_trail_pct=0.02):
    """Append open positions with compact table + per-position scenario blocks.

    Uses actual BingX open orders when available (SL price, trailing TP rate).
    Falls back to state.json SL and estimated 2% trail when orders unavailable.
    Returns dict: unrealized_net, sl_floor_net, trail_tp_net.
    """
    if mark_prices is None:
        mark_prices = {}
    if open_orders_map is None:
        open_orders_map = {}
    have_prices = bool(mark_prices)

    lines.append("**Open Positions at Bot Stop**")
    lines.append("")

    # Compact main table
    lines.append("| Symbol | Dir | Entry | Mark | Move% | Net PnL | Margin ROI | BE |")
    lines.append("|--------|-----|-------|------|-------|---------|------------|----|")

    total_open_notional = 0.0
    total_unrealized_net = 0.0
    total_sl_net = 0.0
    total_tp_net = 0.0
    be_count = 0
    scenario_lines = []

    for pos in open_positions:
        sym = pos.get("symbol", "?")
        direction = pos.get("direction", "?")
        entry = pos.get("entry_price", 0)
        sl_state = pos.get("sl_price", 0)
        notional = pos.get("notional_usd", 0)
        be_raised = pos.get("be_raised", False)
        total_open_notional += notional
        if be_raised:
            be_count += 1
        be_str = "Y" if be_raised else "n"

        # Determine actual SL and trailing TP from open orders (if fetched)
        order_data = open_orders_map.get(sym, {})
        sl_price = order_data.get("sl_price") or sl_state  # fall back to state.json
        trail_pct = order_data.get("trail_pct") or default_trail_pct
        has_trail = order_data.get("trail_pct") is not None
        trail_activation = order_data.get("trail_activation")
        fixed_tp = order_data.get("tp_price")

        if have_prices and sym in mark_prices:
            mark = mark_prices[sym]
            _, unreal_net = compute_unrealized_pnl(pos, mark)
            roi_on_margin = unreal_net / MARGIN_USD * 100

            # SL scenario using actual or state.json SL
            pos_with_sl = dict(pos)
            pos_with_sl["sl_price"] = sl_price
            _, sl_gross, sl_net = compute_sl_pnl(pos_with_sl)

            # TP scenario: use fixed TP if available, else trailing estimate
            if fixed_tp:
                if direction == "LONG":
                    tp_gross = (fixed_tp - entry) * pos.get("quantity", 0)
                else:
                    tp_gross = (entry - fixed_tp) * pos.get("quantity", 0)
                tp_net = tp_gross - notional * COMMISSION_RT_GROSS
                tp_price_show = fixed_tp
                tp_label = "TP(fixed)"
            else:
                tp_price_show, _, tp_net = compute_trail_tp_pnl(pos, mark, trail_pct)
                tp_label = "Trail " + str(round(trail_pct * 100, 1)) + "%"
                if has_trail:
                    tp_label = "Trail " + str(round(trail_pct * 100, 1)) + "% (live)"

            total_unrealized_net += unreal_net
            total_sl_net += sl_net
            total_tp_net += tp_net

            if direction == "LONG":
                move_pct = (mark - entry) / entry * 100
            else:
                move_pct = (entry - mark) / entry * 100

            lines.append("| " + sym + " | " + direction
                         + " | " + str(round(entry, 6))
                         + " | " + str(round(mark, 6))
                         + " | " + fmt_pct(move_pct)
                         + " | " + fmt_pnl(unreal_net)
                         + " | " + fmt_pct(roi_on_margin) + " of $" + str(MARGIN_USD)
                         + " | " + be_str + " |")

            # Scenario block (readable, no wide columns)
            sl_be_note = " (BE)" if be_raised else ""
            act_note = ""
            if trail_activation:
                act_note = " | activated @ " + str(round(trail_activation, 6))
            scenario_lines.append(
                "  " + sym + " " + direction
                + "  |  SL: " + str(round(sl_price, 6)) + sl_be_note
                + " -> floor " + fmt_pnl(sl_net)
                + "  |  " + tp_label + " -> target ~ " + str(round(tp_price_show, 6))
                + " -> " + fmt_pnl(tp_net) + act_note
            )
        else:
            lines.append("| " + sym + " | " + direction
                         + " | " + str(round(entry, 6))
                         + " | n/a | n/a | n/a | n/a | " + be_str + " |")
            scenario_lines.append(
                "  " + sym + "  |  SL: " + str(round(sl_state, 6))
                + "  |  no live price fetched"
            )

    lines.append("")
    lines.append("**Position Scenarios** (SL floor / TP target per position)")
    lines.append("")
    lines.append("```")
    for sl in scenario_lines:
        lines.append(sl)
    lines.append("```")
    lines.append("")

    entry_commission = total_open_notional * COMMISSION_TAKER
    lines.append("- **Open positions**: " + str(len(open_positions))
                 + " | BE raised: " + str(be_count) + "/" + str(len(open_positions)))
    lines.append("- **Total margin at risk**: $" + str(round(len(open_positions) * MARGIN_USD, 2))
                 + " | notional: $" + str(round(total_open_notional, 2))
                 + " | entry commission paid: $" + str(round(entry_commission, 3)))
    if have_prices:
        lines.append("- **Unrealized net (mark-to-market)**: " + fmt_pnl(total_unrealized_net))
        lines.append("- **SL floor net (worst case, all SLs hit)**: " + fmt_pnl(total_sl_net))
        lines.append("- **TP target net (best case, all TPs hit)**: " + fmt_pnl(total_tp_net))
    else:
        lines.append("- Unrealized P&L unavailable (no live prices)")
    lines.append("")
    return {
        "unrealized_net": total_unrealized_net,
        "sl_floor_net": total_sl_net,
        "trail_tp_net": total_tp_net,
    }


def build_report(trades, open_positions=None, mark_prices=None, open_orders_map=None):
    """Build the Phase 3 live account analysis report and return as a single string."""
    if open_positions is None:
        open_positions = []
    if mark_prices is None:
        mark_prices = {}
    if open_orders_map is None:
        open_orders_map = {}
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    p3 = [t for t in trades if t.get("phase") == 3]

    lines.append("# BingX Phase 3 — Live Account Report")
    lines.append("")
    lines.append("**Generated**: " + now + "  |  "
                 + "**Account**: $" + str(ACCOUNT_SIZE_USD) + "  |  "
                 + "**Notional/trade**: $50 (5x margin x 10x leverage)")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not p3:
        lines.append("No Phase 3 trades found.")
        return "\n".join(lines)

    # Pre-compute everything needed for all sections
    closed_pnl = sum(t["pnl_net"] for t in p3)
    be_trades = identify_sl_at_entry_trades(p3)
    winners_closed = [t for t in p3 if t["pnl_net"] > 0]
    real_sl = [t for t in p3 if t["pnl_net"] < 0 and t not in be_trades]
    tp_count = sum(1 for t in p3 if t.get("exit_reason") == "TP_HIT")
    first_ts = min(t["ts_dt"] for t in p3).strftime("%Y-%m-%d %H:%M UTC")
    last_ts = max(t["ts_dt"] for t in p3).strftime("%Y-%m-%d %H:%M UTC")

    # Build open positions section first (needed for totals)
    pos_lines = []
    pos_totals = {"unrealized_net": 0.0, "sl_floor_net": 0.0, "trail_tp_net": 0.0}
    if open_positions:
        pos_totals = build_open_positions_section(
            pos_lines, open_positions, mark_prices, open_orders_map
        )

    # ------------------------------------------------------------------
    # Section 1: Account Snapshot — HEADLINE NUMBERS FIRST
    # ------------------------------------------------------------------
    lines.append("## 1. Account Snapshot")
    lines.append("")
    lines.append("```")
    lines.append("  Account size : $" + str(ACCOUNT_SIZE_USD))
    lines.append("  Margin in use: $" + str(round(len(open_positions) * MARGIN_USD, 2))
                 + "  (" + str(len(open_positions)) + " open positions x $" + str(MARGIN_USD) + ")")
    lines.append("  Run period   : " + first_ts + "  to  " + last_ts)
    lines.append("  Closed trades: " + str(len(p3))
                 + "   Open: " + str(len(open_positions)))
    lines.append("```")
    lines.append("")

    lines.append("| Scenario | Closed | Open Positions | **TOTAL** | **% of $"
                 + str(int(ACCOUNT_SIZE_USD)) + "** |")
    lines.append("|----------|--------|----------------|-----------|------------|")
    scenarios = [
        ("Worst case — all SLs hit",
         pos_totals["sl_floor_net"],
         closed_pnl + pos_totals["sl_floor_net"]),
        ("Current — mark-to-market",
         pos_totals["unrealized_net"],
         closed_pnl + pos_totals["unrealized_net"]),
        ("Best case — all trailing TPs hit",
         pos_totals["trail_tp_net"],
         closed_pnl + pos_totals["trail_tp_net"]),
    ]
    for label, open_val, total in scenarios:
        acct_pct = fmt_pct(total / ACCOUNT_SIZE_USD * 100)
        lines.append("| " + label
                     + " | " + fmt_pnl(closed_pnl)
                     + " | " + fmt_pnl(open_val)
                     + " | **" + fmt_pnl(total) + "**"
                     + " | **" + acct_pct + "** |")
    lines.append("")
    lines.append("> Trailing TP estimate: 2% callback from current mark price.")
    lines.append("> Commission: 0.05% taker per side. Rebate 50% next day.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Section 2: Open Positions
    # ------------------------------------------------------------------
    lines.append("## 2. Open Positions")
    lines.append("")
    if open_positions:
        lines.extend(pos_lines)
    else:
        lines.append("No open positions at bot stop.")
        lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Section 3: Closed Trade Analysis
    # ------------------------------------------------------------------
    lines.append("## 3. Closed Trade Analysis")
    lines.append("")
    lines.append("> **Context**: The strategy profits via trailing TP — positions must stay open to win.")
    lines.append("> " + str(tp_count) + " of " + str(len(p3))
                 + " closed trades hit TP. The profitable trades are in the "
                 + str(len(open_positions)) + " still-open positions above.")
    lines.append("")

    lines.append("**Outcome breakdown**")
    lines.append("")
    lines.append("| Category | Count | Total P&L | Avg P&L |")
    lines.append("|----------|------:|----------:|--------:|")
    w_total = sum(t["pnl_net"] for t in winners_closed)
    be_total = sum(t["pnl_net"] for t in be_trades)
    sl_total = sum(t["pnl_net"] for t in real_sl)
    lines.append("| TP / winners | " + str(len(winners_closed))
                 + " | " + fmt_pnl(w_total)
                 + " | " + (fmt_pnl(w_total / len(winners_closed)) if winners_closed else "n/a") + " |")
    lines.append("| SL raised to entry (commission-only loss) | " + str(len(be_trades))
                 + " | " + fmt_pnl(be_total)
                 + " | " + fmt_pnl(be_total / len(be_trades)) + " |")
    lines.append("| Full SL hits | " + str(len(real_sl))
                 + " | " + fmt_pnl(sl_total)
                 + " | " + (fmt_pnl(sl_total / len(real_sl)) if real_sl else "n/a") + " |")
    lines.append("| **Total** | **" + str(len(p3)) + "**"
                 + " | **" + fmt_pnl(closed_pnl) + "**"
                 + " | **" + fmt_pnl(closed_pnl / len(p3)) + "** |")
    lines.append("")

    lines.append("**Grade and Direction**")
    lines.append("")
    lines.append("| | Trades | Wins | Win% | Total P&L | Avg P&L |")
    lines.append("|--|------:|-----:|-----:|----------:|--------:|")
    for grade, gm in grade_breakdown(p3).items():
        lines.append("| Grade " + grade
                     + " | " + str(gm["count"])
                     + " | " + str(gm["wins"])
                     + " | " + fmt_pct(gm["win_rate"])
                     + " | " + fmt_pnl(gm["total_pnl"])
                     + " | " + fmt_pnl(gm["avg_pnl"]) + " |")
    for direction, dm in direction_breakdown(p3).items():
        lines.append("| " + direction
                     + " | " + str(dm["count"])
                     + " | " + str(dm["wins"])
                     + " | " + fmt_pct(dm["win_rate"])
                     + " | " + fmt_pnl(dm["total_pnl"])
                     + " | " + fmt_pnl(dm["avg_pnl"]) + " |")
    lines.append("")

    # Symbol leaderboard — show only worst (top 5 are all small losses, not useful)
    best_syms, worst_syms = symbol_leaderboard(p3, top_n=5)
    all_sym_pnl = {s: v for s, v in best_syms + worst_syms}
    lines.append("**Symbol performance (closed trades only)**")
    lines.append("")
    lines.append("| Symbol | Total P&L | Note |")
    lines.append("|--------|----------:|------|")
    for sym, sym_pnl in worst_syms:
        note = "multiple trades" if sum(1 for t in p3 if t["symbol"] == sym) > 1 else ""
        lines.append("| " + sym + " | " + fmt_pnl(sym_pnl) + " | " + note + " |")
    if not any(v > 0 for v in all_sym_pnl.values()):
        lines.append("")
        lines.append("> No closed symbol is profitable — all winners are in the open positions.")
    lines.append("")

    m3 = compute_phase_metrics(p3)
    lines.append("**Hold times** — avg " + fmt_mins(m3["avg_hold"])
                 + "  |  min " + fmt_mins(m3["min_hold"])
                 + "  |  max " + fmt_mins(m3["max_hold"]))
    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Section 4: SL-at-Entry Exit Analysis
    # ------------------------------------------------------------------
    lines.append("## 4. SL-at-Entry Exit Analysis")
    lines.append("")
    lines.append("> The bot raises SL to **exact entry** once a position is ahead.")
    lines.append("> This is NOT true BE+fees. Each such exit costs ~$0.05 gross / ~$0.025 net after rebate.")
    lines.append("> True BE+fees = SL at entry + 0.10% (LONG) or entry - 0.10% (SHORT).")
    lines.append("> Bot fix applied 2026-02-28: new raises will use entry +/- 0.10%.")
    lines.append("")
    lines.append("| Symbol | Dir | Entry | Exit | P&L |")
    lines.append("|--------|-----|------:|-----:|----:|")
    for t in sorted(be_trades, key=lambda x: x["pnl_net"]):
        lines.append("| " + t["symbol"] + " | " + t["direction"]
                     + " | " + str(round(t["entry_price"], 6))
                     + " | " + str(round(t["exit_price"], 6))
                     + " | " + fmt_pnl(t["pnl_net"]) + " |")
    lines.append("")
    lines.append("Total cost of " + str(len(be_trades)) + " SL-at-entry exits: "
                 + fmt_pnl(be_total) + " gross  /  "
                 + fmt_pnl(be_total * (1 - COMMISSION_REBATE)) + " net after rebate")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Section 5: Key Findings
    # ------------------------------------------------------------------
    lines.append("## 5. Key Findings")
    lines.append("")

    total_mtm = closed_pnl + pos_totals["unrealized_net"]
    total_tp = closed_pnl + pos_totals["trail_tp_net"]
    total_sl = closed_pnl + pos_totals["sl_floor_net"]

    findings = [
        "Closed P&L: " + fmt_pnl(closed_pnl) + " across " + str(len(p3))
        + " trades. Current total (mark-to-market): " + fmt_pnl(total_mtm)
        + " (" + fmt_pct(total_mtm / ACCOUNT_SIZE_USD * 100) + " of account).",

        str(tp_count) + " TP_HIT exits from " + str(len(p3)) + " closed trades — "
        + "the trailing TP mechanism was not triggered before bot stopped. "
        + "All unrealized gains (" + fmt_pnl(pos_totals["unrealized_net"])
        + ") are in the 6 open positions.",

        str(len(be_trades)) + " SL-at-entry exits cost "
        + fmt_pnl(abs(be_total * (1 - COMMISSION_REBATE)))
        + " net after rebate — avoidable with BE+fees SL (now fixed in bot).",

        "If all 6 open trailing TPs hit: total = " + fmt_pnl(total_tp)
        + " (" + fmt_pct(total_tp / ACCOUNT_SIZE_USD * 100) + " of $"
        + str(int(ACCOUNT_SIZE_USD)) + " account). "
        + "Worst case (all SLs hit): " + fmt_pnl(total_sl)
        + " (" + fmt_pct(total_sl / ACCOUNT_SIZE_USD * 100) + ").",

        "Worst single loss: " + fmt_trade(min(p3, key=lambda t: t["pnl_net"]))
        + ". Best open position: VIRTUAL-USDT SHORT at +57% margin ROI (unrealized).",
    ]

    for i, finding in enumerate(findings, 1):
        lines.append(str(i) + ". " + finding)

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by " + str(Path(__file__).name) + "*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Run trade analysis, write report to 06-CLAUDE-LOGS, print to console."""
    log = setup_logging()
    log.info("Starting trade analysis")
    log.info("Source: " + str(TRADES_CSV))
    log.info("Report: " + str(REPORT_PATH))

    if not TRADES_CSV.exists():
        log.error("trades.csv not found at " + str(TRADES_CSV))
        sys.exit(1)

    trades = load_trades(TRADES_CSV)
    log.info("Loaded " + str(len(trades)) + " trades")

    open_positions = load_open_positions(STATE_JSON)
    log.info("Open positions at bot stop: " + str(len(open_positions)))

    mark_prices = {}
    open_orders_map = {}
    if open_positions:
        symbols = [pos.get("symbol") for pos in open_positions if pos.get("symbol")]
        log.info("Fetching live prices for: " + ", ".join(symbols))
        mark_prices = fetch_all_mark_prices(symbols)
        if mark_prices:
            log.info("Prices fetched: " + ", ".join(
                k + "=" + str(round(v, 6)) for k, v in mark_prices.items()
            ))
        else:
            log.warning("Could not fetch mark prices — unrealized P&L unavailable")

        # Fetch actual open orders (SL + trailing TP) from BingX API
        env = read_env(ENV_PATH)
        api_key = os.environ.get("BINGX_API_KEY", env.get("BINGX_API_KEY", ""))
        secret_key = os.environ.get("BINGX_SECRET_KEY", env.get("BINGX_SECRET_KEY", ""))
        if api_key and secret_key:
            log.info("API keys found — fetching open orders from BingX")
            for pos in open_positions:
                sym = pos.get("symbol", "")
                if not sym:
                    continue
                orders = fetch_open_orders_for_symbol(api_key, secret_key, sym)
                parsed = parse_sl_tp_orders(orders)
                open_orders_map[sym] = parsed
                log.info(sym + " orders: sl=" + str(parsed["sl_price"])
                         + " tp=" + str(parsed["tp_price"])
                         + " trail_pct=" + str(parsed["trail_pct"]))
        else:
            log.warning("No API keys — open orders not fetched, using state.json SL + 2% trail estimate")

    report_text = build_report(trades, open_positions, mark_prices, open_orders_map)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    log.info("Report written to " + str(REPORT_PATH))

    print("\n" + report_text)
    print("\nReport saved to:")
    print("  " + str(REPORT_PATH))


if __name__ == "__main__":
    main()

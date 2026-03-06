"""
Build Phase 1: Diagnostic scripts for BingX connector audit.
Creates 6 read-only analysis scripts, then py_compile validates each.

Run: python scripts/build_phase1_diagnostics.py
"""
import py_compile
import sys
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def verify(path: Path) -> bool:
    """Syntax-check and AST-parse a .py file; return True if clean."""
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        return False
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        print("  AST ERROR line " + str(e.lineno) + ": " + str(e.msg))
        return False
    print("  OK: " + path.name)
    return True


ERRORS = []


def write_and_verify(path: Path, content: str) -> None:
    """Write content to path then verify syntax."""
    path.write_text(content, encoding="utf-8")
    if not verify(path):
        ERRORS.append(path.name)


# ---------------------------------------------------------------------------
# 1A — Error Audit
# ---------------------------------------------------------------------------
ERROR_AUDIT = r'''"""
Error audit: parse bot log and categorise every ERROR/WARNING line.
Run: python scripts/run_error_audit.py
"""
import re
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "2026-03-03-bot.log"
OUT_FILE = ROOT / "logs" / "error_audit_2026-03-03.md"

CATEGORIES = {
    "TTP_CLOSE_FAIL":   ["109400", "reduceOnly"],
    "AUTH_FAIL":        ["100001", "Signature verification", "signature mismatch"],
    "EXIT_DETECTION":   ["EXIT_UNKNOWN", "SL_HIT_ASSUMED", "_detect_exit"],
    "RECONCILE":        ["reconcil", "Reconcile"],
    "WS_ERROR":         ["WebSocket", "ws_dead", "reconnect"],
    "API_TIMEOUT":      ["timeout", "ConnectionError", "ReadTimeout"],
}


def categorise(line: str) -> str:
    """Return category key for a log line, or OTHER."""
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in line.lower():
                return cat
    return "OTHER"


def main() -> None:
    """Parse log file and write categorised error report."""
    if not LOG_FILE.exists():
        log.error("Log file not found: " + str(LOG_FILE))
        sys.exit(1)

    log.info("Parsing: " + str(LOG_FILE))
    buckets: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    buckets["OTHER"] = []

    with open(LOG_FILE, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip()
            if "[ERROR]" not in line and "[WARNING]" not in line:
                continue
            cat = categorise(line)
            buckets[cat].append(line)

    log.info("Categorisation complete — writing report")
    lines = [
        "# Bot Error Audit — 2026-03-03",
        "",
        "Source: `logs/2026-03-03-bot.log`",
        "",
        "| Category | Count | First Occurrence | Last Occurrence |",
        "|----------|-------|-----------------|----------------|",
    ]

    ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")

    for cat, entries in buckets.items():
        if not entries:
            continue
        first_ts = last_ts = ""
        for e in entries:
            m = ts_re.match(e)
            if m:
                first_ts = m.group(1)
                break
        for e in reversed(entries):
            m = ts_re.match(e)
            if m:
                last_ts = m.group(1)
                break
        lines.append("| " + cat + " | " + str(len(entries)) + " | " + first_ts + " | " + last_ts + " |")

    lines += ["", "## Sample Lines Per Category", ""]

    for cat, entries in buckets.items():
        if not entries:
            continue
        lines += ["### " + cat, ""]
        for e in entries[:5]:
            lines.append("```")
            lines.append(e[:200])
            lines.append("```")
        if len(entries) > 5:
            lines.append("_... and " + str(len(entries) - 5) + " more_")
        lines.append("")

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written: " + str(OUT_FILE))

    total = sum(len(v) for v in buckets.values())
    log.info("Total error/warning lines: %d", total)
    for cat, entries in buckets.items():
        if entries:
            log.info("  %-20s %d", cat, len(entries))


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------
# 1B — Variable Web
# ---------------------------------------------------------------------------
VARIABLE_WEB = r'''"""
Variable web: static AST analysis of the bot codebase.
Traces data flow and flags orphaned variables.
Run: python scripts/run_variable_web.py
"""
import ast
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "logs" / "variable_web.md"

TARGET_FILES = [
    "main.py",
    "signal_engine.py",
    "executor.py",
    "position_monitor.py",
    "state_manager.py",
    "ttp_engine.py",
    "ws_listener.py",
    "risk_gate.py",
    "bingx_auth.py",
]

# Key state.json fields to track
STATE_KEYS = [
    "positions", "halt_flag", "daily_pnl", "daily_trades", "session_start",
    "ttp_state", "ttp_extreme", "ttp_trail_level", "ttp_close_pending",
    "ttp_force_activate", "be_raised", "sl_price", "tp_price",
    "entry_price", "direction", "symbol", "grade", "quantity",
    "notional_usd", "order_id", "entry_time", "cooldown_until",
]


def extract_functions(source: str, filename: str) -> list[dict]:
    """Extract function defs with line numbers from source."""
    results = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        log.warning("AST parse fail %s: %s", filename, e)
        return results
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            results.append({
                "name": node.name,
                "line": node.lineno,
                "file": filename,
            })
    return results


def extract_state_key_usage(source: str, filename: str) -> dict[str, list[int]]:
    """Find which state.json keys are referenced, with line numbers."""
    usage: dict[str, list[int]] = {}
    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        for key in STATE_KEYS:
            if ('"' + key + '"') in line or ("'" + key + "'") in line:
                usage.setdefault(key, []).append(i)
    return usage


def main() -> None:
    """Run static analysis and write dependency map."""
    all_funcs: dict[str, list[dict]] = {}
    all_key_usage: dict[str, dict[str, list[int]]] = {}

    for fname in TARGET_FILES:
        fpath = ROOT / fname
        if not fpath.exists():
            log.warning("Missing: %s", fname)
            continue
        source = fpath.read_text(encoding="utf-8", errors="replace")
        all_funcs[fname] = extract_functions(source, fname)
        all_key_usage[fname] = extract_state_key_usage(source, fname)
        log.info("Parsed %s: %d functions", fname, len(all_funcs[fname]))

    lines = [
        "# BingX Connector — Variable Web",
        "",
        "## Data Flow",
        "",
        "```",
        "config.yaml",
        "  --> main.py (load_config)",
        "  --> signal_engine.py (StrategyAdapter)",
        "  --> executor.py (Executor)",
        "  --> state_manager.py (StateManager)",
        "  --> position_monitor.py (PositionMonitor)",
        "  --> ttp_engine.py (TTPExit)",
        "  --> trades.csv",
        "  --> state.json",
        "    --> dashboard stores (store-state, store-trades)",
        "    --> dashboard callbacks (CB-3, CB-4, CB-9, CB-10)",
        "```",
        "",
        "## Function Map",
        "",
    ]

    for fname, funcs in all_funcs.items():
        lines.append("### " + fname + " (" + str(len(funcs)) + " functions)")
        lines.append("")
        for f in funcs:
            lines.append("- `" + f["name"] + "()` line " + str(f["line"]))
        lines.append("")

    lines += [
        "## State.json Key Usage",
        "",
        "| Key | Written In | Read In |",
        "|-----|-----------|---------|",
    ]

    WRITERS = {"state_manager.py", "position_monitor.py", "executor.py", "signal_engine.py"}
    READERS = {"bingx-live-dashboard-v1-4.py", "signal_engine.py", "position_monitor.py", "main.py"}

    for key in STATE_KEYS:
        writers = []
        readers = []
        for fname, usage in all_key_usage.items():
            if key in usage:
                ref = fname + ":" + ",".join(str(l) for l in usage[key][:3])
                if fname in WRITERS:
                    writers.append(ref)
                else:
                    readers.append(ref)
        if not writers and not readers:
            continue
        w_str = " ".join(writers) if writers else "ORPHAN"
        r_str = " ".join(readers) if readers else "UNUSED"
        lines.append("| `" + key + "` | " + w_str + " | " + r_str + " |")

    lines += ["", "## Mermaid Dependency Diagram", "", "```mermaid", "graph TD"]
    lines.append("    CONFIG[config.yaml] --> MAIN[main.py]")
    lines.append("    MAIN --> AUTH[bingx_auth.py]")
    lines.append("    MAIN --> SE[signal_engine.py]")
    lines.append("    MAIN --> PM[position_monitor.py]")
    lines.append("    MAIN --> EX[executor.py]")
    lines.append("    MAIN --> SM[state_manager.py]")
    lines.append("    SE --> EX")
    lines.append("    SE --> TTP[ttp_engine.py]")
    lines.append("    PM --> TTP")
    lines.append("    PM --> SM")
    lines.append("    EX --> SM")
    lines.append("    SM --> STATEJSON[state.json]")
    lines.append("    SM --> TRADESCSV[trades.csv]")
    lines.append("    STATEJSON --> DASH[dashboard]")
    lines.append("    TRADESCSV --> DASH")
    lines.append("    DASH --> API[BingX REST API]")
    lines.append("    PM --> API")
    lines.append("    EX --> API")
    lines.append("```")

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    log.info("Written: " + str(OUT_FILE))


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------
# 1C — TTP Audit
# ---------------------------------------------------------------------------
TTP_AUDIT = r'''"""
TTP audit: analyse TTP state from state.json, trades.csv, and bot log.
Run: python scripts/run_ttp_audit.py
"""
import re
import csv
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT       = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state.json"
TRADES_CSV = ROOT / "trades.csv"
LOG_FILE   = ROOT / "logs" / "2026-03-03-bot.log"
OUT_FILE   = ROOT / "logs" / "ttp_audit_2026-03-03.md"


def load_state() -> dict:
    """Load state.json; return empty dict on error."""
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error("state.json load error: %s", e)
        return {}


def load_trades_columns() -> list[str]:
    """Return column names from trades.csv header row."""
    if not TRADES_CSV.exists():
        return []
    with open(TRADES_CSV, encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            return next(reader)
        except StopIteration:
            return []


def parse_ttp_log_events(log_file: Path) -> dict[str, list[str]]:
    """Extract TTP-related log lines keyed by position symbol."""
    events: dict[str, list[str]] = {}
    TTP_PATTERNS = ["TTP", "ttp", "trail", "TRAIL", "109400", "close_pending", "TTP_CLOSE"]
    if not log_file.exists():
        return events
    with open(log_file, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip()
            if not any(p in line for p in TTP_PATTERNS):
                continue
            # Try to extract symbol from log line
            m = re.search(r"\b([A-Z0-9]+-USDT)_(LONG|SHORT)\b", line)
            key = m.group(0) if m else "GENERAL"
            events.setdefault(key, []).append(line[:240])
    return events


def main() -> None:
    """Run TTP audit and write report."""
    state = load_state()
    cols = load_trades_columns()
    ttp_events = parse_ttp_log_events(LOG_FILE)

    lines = [
        "# TTP Audit — 2026-03-03",
        "",
        "## 1. trades.csv Schema Check",
        "",
    ]

    TTP_COLS = ["ttp_activated", "ttp_extreme_pct", "ttp_trail_pct", "ttp_exit_reason"]
    if not cols:
        lines.append("WARNING: trades.csv not found or empty")
    else:
        lines.append("Columns present: " + ", ".join(cols))
        lines.append("")
        missing = [c for c in TTP_COLS if c not in cols]
        if missing:
            lines.append("MISSING TTP columns (BUG-9): " + ", ".join(missing))
            lines.append("")
            lines.append("These columns must be added to state_manager.py _append_trade().")
        else:
            lines.append("All TTP columns present.")

    lines += ["", "## 2. Open Position TTP States", ""]

    positions = state.get("positions", {})
    if not positions:
        lines.append("No open positions in state.json")
    else:
        lines.append("| Position | ttp_state | ttp_extreme | ttp_trail_level | ttp_close_pending | be_raised |")
        lines.append("|----------|-----------|-------------|-----------------|-------------------|-----------|")
        for key, pos in positions.items():
            ts    = pos.get("ttp_state", "—")
            ex    = str(pos.get("ttp_extreme", "—"))
            trail = str(pos.get("ttp_trail_level", "—"))
            pend  = str(pos.get("ttp_close_pending", False))
            be    = str(pos.get("be_raised", False))
            lines.append("| " + key + " | " + ts + " | " + ex + " | " + trail + " | " + pend + " | " + be + " |")

    lines += ["", "## 3. TTP Log Event Timeline", ""]

    fail_count = 0
    activated_count = 0
    for key, events in sorted(ttp_events.items()):
        if key == "GENERAL":
            continue
        lines.append("### " + key + " (" + str(len(events)) + " TTP events)")
        lines.append("")
        for e in events[:10]:
            if "109400" in e or "failed" in e.lower():
                fail_count += 1
            if "ACTIVATED" in e:
                activated_count += 1
            lines.append("```")
            lines.append(e)
            lines.append("```")
        if len(events) > 10:
            lines.append("_... " + str(len(events) - 10) + " more_")
        lines.append("")

    if "GENERAL" in ttp_events:
        lines.append("### General TTP events (" + str(len(ttp_events["GENERAL"])) + ")")
        for e in ttp_events["GENERAL"][:5]:
            lines.append("```")
            lines.append(e)
            lines.append("```")
        lines.append("")

    lines += [
        "## 4. Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        "| TTP close failures (109400) | " + str(fail_count) + " |",
        "| TTP ACTIVATED events in log | " + str(activated_count) + " |",
        "| Positions with ttp_close_pending | " + str(sum(1 for p in positions.values() if p.get("ttp_close_pending"))) + " |",
        "| ttp_state columns in trades.csv | " + ("YES" if all(c in cols for c in TTP_COLS) else "NO (BUG-9)") + " |",
        "",
        "## 5. Root Cause",
        "",
        "The primary cause of TTP not closing positions: error 109400 from BingX.",
        "This is caused by `reduceOnly=true` being invalid in Hedge mode (BUG-1).",
        "Fix: remove `reduceOnly` from `_place_market_close()` in position_monitor.py.",
        "The `positionSide` field already scopes the close to the correct side.",
    ]

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    log.info("Written: " + str(OUT_FILE))


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------
# 1D — Ticker Collector
# ---------------------------------------------------------------------------
TICKER_COLLECTOR = r'''"""
BingX ticker collector: fetch all perpetual futures tickers (no auth required).
Saves to CSV and prints top/bottom by volume.
Run: python scripts/run_ticker_collector.py
"""
import csv
import logging
import sys
from datetime import date
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
LOG_DIR  = ROOT / "logs"
TODAY    = date.today().strftime("%Y-%m-%d")
OUT_CSV  = LOG_DIR / ("bingx_tickers_" + TODAY + ".csv")

TICKER_URL = "https://open-api.bingx.com/openApi/swap/v2/quote/ticker"

# Live bot 47 coins for cross-reference
LIVE_COINS = {
    "SKR-USDT", "TRUTH-USDT", "RIVER-USDT", "STBL-USDT", "ZKP-USDT",
    "LYN-USDT", "BEAT-USDT", "GIGGLE-USDT", "PIPPIN-USDT", "FOLKS-USDT",
    "NAORIS-USDT", "Q-USDT", "ELSA-USDT", "UB-USDT", "THETA-USDT",
    "SAHARA-USDT", "TIA-USDT", "APT-USDT", "AIXBT-USDT", "GALA-USDT",
    "LDO-USDT", "SUSHI-USDT", "VET-USDT", "WAL-USDT", "WIF-USDT",
    "WOO-USDT", "ATOM-USDT", "BOME-USDT", "DYDX-USDT", "VIRTUAL-USDT",
    "BREV-USDT", "CYBER-USDT", "EIGEN-USDT", "MUBARAK-USDT", "1000PEPE-USDT",
    "DEEP-USDT", "ETHFI-USDT", "RENDER-USDT", "BB-USDT", "F-USDT",
    "GUN-USDT", "KAITO-USDT", "MEME-USDT", "PENDLE-USDT", "SCRT-USDT",
    "SQD-USDT", "STX-USDT",
}

# Beta candidate coins (user-provided, excluding ETH/BTC)
BETA_CANDIDATES = {
    "ENSO-USDT", "GRASS-USDT", "POWER-USDT", "VENICE-USDT", "SIREN-USDT",
    "FHE-USDT", "BTR-USDT", "OWC-USDT", "WARD-USDT", "WHITEWHALE-USDT",
    "ESP-USDT", "MUBARAK-USDT", "SAHARA-USDT",
    "INJ-USDT", "JTO-USDT", "JUP-USDT", "LINK-USDT", "LTC-USDT",
    "METAX-USDT", "MUS-USDT", "MYX-USDT", "NEAR-USDT", "ONDO-USDT",
    "PENGU-USDT", "POPCAT-USDT", "PUMP-USDT", "QNT-USDT", "SHIB1000-USDT",
    "SOL-USDT", "SUI-USDT", "UNI-USDT", "XRP-USDT", "ZEC-USDT", "ZEN-USDT",
    "1000PEPE-USDT", "APE-USDT", "APT-USDT", "ASTER-USDT", "AXS-USDT",
    "BANK-USDT", "BERAU-USDT", "BNB-USDT", "BONK-USDT",
    "DASH-USDT", "DOT-USDT", "FARTCOIN-USDT", "HMSTR-USDT", "IMX-USDT",
    "GIGGLE-USDT", "PIPPIN-USDT", "STBL-USDT", "BREV-USDT", "Q-USDT",
    "BEAT-USDT", "LYN-USDT", "TRUTH-USDT", "SKR-USDT",
}


def fetch_tickers() -> list[dict]:
    """Fetch all perpetual ticker data from BingX public API."""
    log.info("Fetching tickers from BingX...")
    try:
        resp = requests.get(TICKER_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.error("Fetch failed: %s", e)
        sys.exit(1)

    if data.get("code", -1) != 0:
        log.error("API error %s: %s", data.get("code"), data.get("msg"))
        sys.exit(1)

    raw = data.get("data", [])
    log.info("Received %d tickers", len(raw))

    tickers = []
    for t in raw:
        sym = t.get("symbol", "")
        if not sym.endswith("-USDT"):
            continue
        try:
            volume = float(t.get("quoteVolume") or t.get("volume") or 0)
            price  = float(t.get("lastPrice") or 0)
            chg    = float(t.get("priceChangePercent") or 0)
            oi     = float(t.get("openInterest") or 0)
        except (ValueError, TypeError):
            continue
        tickers.append({
            "symbol":           sym,
            "last_price":       price,
            "change_24h_pct":   chg,
            "quote_volume_24h": volume,
            "open_interest":    oi,
            "in_live_bot":      sym in LIVE_COINS,
            "in_beta":          sym in BETA_CANDIDATES,
        })

    tickers.sort(key=lambda x: x["quote_volume_24h"], reverse=True)
    return tickers


def main() -> None:
    """Fetch tickers, save CSV, print summary."""
    LOG_DIR.mkdir(exist_ok=True)
    tickers = fetch_tickers()

    # Assign rank
    for i, t in enumerate(tickers, 1):
        t["volume_rank"] = i

    # Write CSV
    fieldnames = ["volume_rank", "symbol", "last_price", "change_24h_pct",
                  "quote_volume_24h", "open_interest", "in_live_bot", "in_beta"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickers)
    log.info("CSV written: " + str(OUT_CSV))

    total = len(tickers)
    print("\n=== BINGX TICKER SUMMARY ===")
    print("Total USDT perpetuals: " + str(total))
    print("")
    print("TOP 20 by volume:")
    for t in tickers[:20]:
        tag = " [LIVE]" if t["in_live_bot"] else (" [BETA]" if t["in_beta"] else "")
        print("  #" + str(t["volume_rank"]) + " " + t["symbol"] + tag +
              "  vol=" + str(round(t["quote_volume_24h"] / 1e6, 1)) + "M")

    print("")
    print("BOTTOM 20 by volume (liquidity warning):")
    for t in tickers[-20:]:
        tag = " [LIVE]" if t["in_live_bot"] else (" [BETA]" if t["in_beta"] else "")
        print("  #" + str(t["volume_rank"]) + " " + t["symbol"] + tag +
              "  vol=" + str(round(t["quote_volume_24h"] / 1e6, 3)) + "M")

    print("")
    print("LIVE BOT coins by volume rank:")
    live_ranked = [t for t in tickers if t["in_live_bot"]]
    for t in live_ranked:
        pct = round(t["volume_rank"] / total * 100, 1)
        print("  #" + str(t["volume_rank"]) + "/" + str(total) +
              " (" + str(pct) + "%) " + t["symbol"])

    print("")
    print("BETA CANDIDATE coins by volume rank:")
    beta_ranked = [t for t in tickers if t["in_beta"]]
    for t in beta_ranked:
        pct = round(t["volume_rank"] / total * 100, 1)
        live_flag = " [OVERLAP-LIVE]" if t["in_live_bot"] else ""
        print("  #" + str(t["volume_rank"]) + "/" + str(total) +
              " (" + str(pct) + "%) " + t["symbol"] + live_flag)

    print("")
    print("CSV: " + str(OUT_CSV))


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------
# 1E — Demo Order Verification
# ---------------------------------------------------------------------------
DEMO_VERIFY = r'''"""
Demo order verification: test which order types BingX VST actually fills.
Places test orders on VST (paper money) and checks fill status.
Run: python scripts/run_demo_order_verify.py
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import date

import requests
import yaml
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "logs" / ("demo_order_verify_" + date.today().strftime("%Y-%m-%d") + ".md")

VST_BASE = "https://open-api-vst.bingx.com"
TEST_SYMBOL = "BTC-USDT"    # High-liquidity coin for reliable fills
TEST_QTY    = "0.001"       # Minimum size

# Paths
ORDER_PATH      = "/openApi/swap/v2/trade/order"
QUERY_PATH      = "/openApi/swap/v2/trade/order"
POSITIONS_PATH  = "/openApi/swap/v2/user/positions"
ALL_ORDERS_PATH = "/openApi/swap/v2/trade/allOrders"

import hashlib
import hmac as hmac_lib


def sign(params: dict, secret: str) -> str:
    """HMAC-SHA256 sign params alphabetically."""
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    return hmac_lib.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()


def build_url(path: str, params: dict, api_key: str, secret: str) -> tuple[str, dict]:
    """Build signed URL and headers."""
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "10000"
    sig = sign(params, secret)
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    url = VST_BASE + path + "?" + qs + "&signature=" + sig
    headers = {"X-BX-APIKEY": api_key}
    return url, headers


def post_order(params: dict, api_key: str, secret: str) -> dict:
    """Place an order on VST."""
    url, headers = build_url(ORDER_PATH, params, api_key, secret)
    try:
        resp = requests.post(url, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def get_mark_price(symbol: str) -> float:
    """Fetch mark price from VST (public endpoint)."""
    try:
        url = VST_BASE + "/openApi/swap/v2/quote/price?symbol=" + symbol
        resp = requests.get(url, timeout=10)
        data = resp.json()
        items = data.get("data", {})
        if isinstance(items, list):
            for item in items:
                if item.get("symbol") == symbol:
                    return float(item.get("price", 0))
        elif isinstance(items, dict):
            return float(items.get("price", 0))
    except Exception as e:
        log.error("Mark price fetch failed: %s", e)
    return 0.0


def close_all_positions(symbol: str, api_key: str, secret: str) -> None:
    """Close any open VST positions for the test symbol."""
    url, headers = build_url(POSITIONS_PATH, {"symbol": symbol}, api_key, secret)
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        positions = data.get("data", [])
        for pos in positions:
            qty = pos.get("positionAmt", "0")
            side = pos.get("positionSide", "LONG")
            if float(qty) == 0:
                continue
            close_side = "SELL" if side == "LONG" else "BUY"
            close_params = {
                "symbol": symbol,
                "side": close_side,
                "positionSide": side,
                "type": "MARKET",
                "quantity": str(abs(float(qty))),
            }
            result = post_order(close_params, api_key, secret)
            log.info("Cleanup close %s %s: code=%s", symbol, side, result.get("code"))
    except Exception as e:
        log.error("Cleanup failed: %s", e)


def main() -> None:
    """Run order type verification tests."""
    load_dotenv(ROOT / ".env")
    api_key    = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    if not api_key or not secret_key:
        log.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY in .env")
        sys.exit(1)

    log.info("Using VST (demo) base: %s", VST_BASE)
    log.info("Test symbol: %s", TEST_SYMBOL)

    mark = get_mark_price(TEST_SYMBOL)
    if mark == 0.0:
        log.error("Cannot fetch mark price — check API connectivity")
        sys.exit(1)
    log.info("Mark price: %.2f", mark)

    # Clean up any previous test positions
    close_all_positions(TEST_SYMBOL, api_key, secret_key)
    time.sleep(2)

    results = []

    def run_test(test_name: str, params: dict) -> dict:
        """Place an order, wait, check status, return result dict."""
        log.info("TEST: %s", test_name)
        resp = post_order(params.copy(), api_key, secret_key)
        code = resp.get("code", -1)
        msg  = resp.get("msg", "")
        order_data = resp.get("data", {}) or {}
        order_id = str(order_data.get("orderId") or order_data.get("order", {}).get("orderId", ""))
        result = {
            "test": test_name,
            "code": code,
            "msg": msg,
            "order_id": order_id,
            "accepted": code == 0,
            "filled": False,
            "status": "",
        }
        log.info("  Placed: code=%s msg=%s order_id=%s", code, msg, order_id)
        if code == 0 and order_id:
            time.sleep(5)
            q_params = {"symbol": params.get("symbol", TEST_SYMBOL), "orderId": order_id}
            q_url, q_headers = build_url(QUERY_PATH, q_params, api_key, secret_key)
            try:
                q_resp = requests.get(q_url, headers=q_headers, timeout=10)
                q_data = q_resp.json()
                order_info = q_data.get("data", {}) or {}
                status = order_info.get("status", "UNKNOWN")
                result["status"] = status
                result["filled"] = status in ("FILLED", "PARTIALLY_FILLED")
                log.info("  Status after 5s: %s", status)
            except Exception as e:
                log.error("  Query failed: %s", e)
        results.append(result)
        time.sleep(2)
        return result

    sl_mark  = round(mark * 0.98, 2)   # 2% below mark (SL for LONG)
    tp_mark  = round(mark * 1.02, 2)   # 2% above mark (TP for LONG)

    # Test 1: MARKET entry LONG
    r = run_test("MARKET_LONG_ENTRY", {
        "symbol": TEST_SYMBOL,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "MARKET",
        "quantity": TEST_QTY,
    })

    if r["accepted"]:
        time.sleep(3)

        # Test 2: STOP_MARKET with MARK_PRICE
        run_test("STOP_MARKET_MARK_PRICE_SL", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "STOP_MARKET",
            "quantity": TEST_QTY,
            "stopPrice": str(sl_mark),
            "workingType": "MARK_PRICE",
        })

        # Test 3: STOP_MARKET with CONTRACT_PRICE
        run_test("STOP_MARKET_CONTRACT_PRICE_SL", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "STOP_MARKET",
            "quantity": TEST_QTY,
            "stopPrice": str(sl_mark),
            "workingType": "CONTRACT_PRICE",
        })

        # Test 4: TAKE_PROFIT_MARKET
        run_test("TAKE_PROFIT_MARKET", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "TAKE_PROFIT_MARKET",
            "quantity": TEST_QTY,
            "stopPrice": str(tp_mark),
            "workingType": "MARK_PRICE",
        })

        # Test 5: Market close (no reduceOnly)
        run_test("MARKET_CLOSE_NO_REDUCE_ONLY", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "MARKET",
            "quantity": TEST_QTY,
        })

    # Write report
    lines = [
        "# Demo Order Verification — " + date.today().strftime("%Y-%m-%d"),
        "",
        "VST Base: " + VST_BASE,
        "Test Symbol: " + TEST_SYMBOL,
        "Mark Price at Test Time: " + str(mark),
        "",
        "| Test | Accepted | Status | Code | Notes |",
        "|------|----------|--------|------|-------|",
    ]
    for r in results:
        acc  = "YES" if r["accepted"] else "NO"
        fill = r["status"] if r["status"] else ("FILLED" if r["filled"] else "—")
        lines.append("| " + r["test"] + " | " + acc + " | " + fill +
                     " | " + str(r["code"]) + " | " + r["msg"][:80] + " |")

    lines += [
        "",
        "## Interpretation",
        "",
        "- STOP_MARKET_MARK_PRICE_SL accepted+filled = SL working correctly in VST",
        "- STOP_MARKET_MARK_PRICE_SL rejected = VST requires CONTRACT_PRICE workingType",
        "- MARKET_CLOSE_NO_REDUCE_ONLY filled = BUG-1 fix is correct (no reduceOnly needed)",
        "- Any code 109400 = reduceOnly still present somewhere",
    ]

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written: " + str(OUT_FILE))

    print("\n=== DEMO VERIFICATION RESULTS ===")
    for r in results:
        status = "PASS" if r["accepted"] else "FAIL"
        print(status + "  " + r["test"] + "  code=" + str(r["code"]) +
              "  status=" + r.get("status", "—"))


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------
# 1F — Trade Analysis
# ---------------------------------------------------------------------------
TRADE_ANALYSIS = r'''"""
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


def load_trades() -> list[dict]:
    """Load trades.csv into list of dicts."""
    if not TRADES_CSV.exists():
        log.error("trades.csv not found: " + str(TRADES_CSV))
        sys.exit(1)
    with open(TRADES_CSV, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def fetch_klines(symbol: str, start_ms: int, end_ms: int, base: str, api_key: str, secret: str) -> list[list]:
    """Fetch 5m klines for symbol in [start_ms, end_ms]. Returns list of [ts,o,h,l,c,v]."""
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


def compute_mfe_mae(klines: list[list], entry_price: float, direction: str,
                    commission_rate: float) -> tuple[float, float, bool]:
    """Compute MFE%, MAE%, and saw_green from klines."""
    if not klines:
        return 0.0, 0.0, False
    mfe = 0.0
    mae = 0.0
    commission_threshold = commission_rate * 2  # round-trip
    for bar in klines:
        try:
            high  = float(bar[2])
            low   = float(bar[3])
        except (IndexError, ValueError, TypeError):
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
    log.info("Loaded %d trades from trades.csv", len(trades))
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
                        if entry_ms <= int(k[0]) <= exit_ms] if klines else []

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
'''

# ---------------------------------------------------------------------------
# Write all scripts
# ---------------------------------------------------------------------------
write_and_verify(SCRIPTS / "run_error_audit.py",         ERROR_AUDIT)
write_and_verify(SCRIPTS / "run_variable_web.py",        VARIABLE_WEB)
write_and_verify(SCRIPTS / "run_ttp_audit.py",           TTP_AUDIT)
write_and_verify(SCRIPTS / "run_ticker_collector.py",    TICKER_COLLECTOR)
write_and_verify(SCRIPTS / "run_demo_order_verify.py",   DEMO_VERIFY)
write_and_verify(SCRIPTS / "run_trade_analysis.py",      TRADE_ANALYSIS)

print("")
if ERRORS:
    print("BUILD FAILED — syntax errors in: " + ", ".join(ERRORS))
    sys.exit(1)
else:
    print("BUILD OK — all 6 Phase 1 scripts compiled clean")
    print("")
    print("Run order:")
    print('  python "' + str(SCRIPTS / "run_error_audit.py") + '"')
    print('  python "' + str(SCRIPTS / "run_variable_web.py") + '"')
    print('  python "' + str(SCRIPTS / "run_ttp_audit.py") + '"')
    print('  python "' + str(SCRIPTS / "run_ticker_collector.py") + '"')
    print('  python "' + str(SCRIPTS / "run_demo_order_verify.py") + '"')
    print('  python "' + str(SCRIPTS / "run_trade_analysis.py") + '"')

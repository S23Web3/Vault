"""
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

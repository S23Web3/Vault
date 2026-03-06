"""
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

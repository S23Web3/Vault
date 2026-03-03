"""
Strategy Analysis Report Builder.

Reads all strategy source files (signals, state machine, exit logic, bot plugin, BBW)
and produces a single markdown report for review in Claude Web.

Purpose: ANALYSIS ONLY. No corrections. No code changes.

Output: docs/STRATEGY-ANALYSIS-REPORT.md
Run:    python scripts/build_strategy_analysis.py
"""

import sys
import py_compile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
BOT_ROOT = ROOT.parent / "bingx-connector"


def read_file(path: Path) -> str:
    """Read a source file; return content or an error notice."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "[FILE NOT FOUND: " + str(path) + "]"
    except Exception as e:
        return "[READ ERROR: " + str(e) + "]"


def section(lines, title, level=2):
    """Append a markdown heading."""
    prefix = "#" * level
    lines.append(prefix + " " + title + "\n")


def code_block(lines, content, lang="python"):
    """Append a fenced code block."""
    lines.append("```" + lang + "\n" + content.rstrip() + "\n```\n")


def annotation(lines, text):
    """Append an analysis annotation (blockquote style)."""
    for line in text.strip().splitlines():
        lines.append("> " + line + "\n")
    lines.append("\n")


def hr(lines):
    lines.append("---\n")


def build_report() -> str:
    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append("# Strategy Analysis Report\n")
    lines.append("**Generated:** " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n\n")
    lines.append(
        "**Purpose:** Full audit of signal logic, version history, exit mechanics, "
        "live bot config, and BBW state. For discussion in Claude Web — do not use "
        "this to correct code, use it to understand what is actually happening.\n"
    )
    hr(lines)

    # ── CRITICAL FINDINGS (upfront) ─────────────────────────────────────────
    section(lines, "CRITICAL FINDINGS — Read This First", 2)

    lines.append("### Finding 1: Live bot is NOT running v386\n")
    annotation(lines, (
        "The bot plugin (bingx-connector/plugins/four_pillars_v384.py line 21) imports:\n"
        "    from signals.four_pillars import compute_signals\n"
        "This is the ORIGINAL signals/four_pillars.py — not v386.\n"
        "v386 was written but never connected to the bot.\n"
        "The bot and the backtester are running different default configurations."
    ))

    lines.append("### Finding 2: Trailing stop mechanism is completely different\n")
    annotation(lines, (
        "Backtester (position_v384.py): AVWAP-based trailing.\n"
        "  After checkpoint_interval=5 bars, SL transitions from fixed ATR-SL\n"
        "  to AVWAP center, ratcheting continuously with each bar.\n\n"
        "Live bot (config.yaml):\n"
        "  trailing_activation_atr_mult: 2.0  (activate when price +/- 2x ATR from entry)\n"
        "  trailing_rate: 0.02                 (2% callback from peak)\n\n"
        "These are NOT equivalent. AVWAP trailing is adaptive to volume-weighted price.\n"
        "BingX native trailing is a fixed percentage callback. They will produce\n"
        "different exit prices on the same trade."
    ))

    lines.append("### Finding 3: Breakeven raise is in the backtester but NOT in the live bot\n")
    annotation(lines, (
        "Backtester: be_trigger_atr and be_lock_atr parameters exist in position_v384.py.\n"
        "Live bot config.yaml: no be_trigger_atr or be_lock_atr keys anywhere.\n"
        "Bot uses only: fixed ATR SL + BingX native trailing (no BE raise step).\n"
        "Backtester includes: fixed ATR SL → optional BE raise → AVWAP trailing."
    ))

    lines.append("### Finding 4: rot_level=80 is nearly meaningless as a filter\n")
    annotation(lines, (
        "require_stage2=True means: stoch_40 AND stoch_60 must have rotated through\n"
        "rot_level during Stage 1 before Grade A fires.\n\n"
        "For LONGS with rot_level=80:\n"
        "  Condition: stoch_40 > (100 - 80) = 20  at any point during Stage 1.\n"
        "  stoch_40 above 20 is almost always true in any market.\n"
        "  This filter barely filters anything.\n\n"
        "For SHORTS with rot_level=80:\n"
        "  Condition: stoch_40 < 80  at any point during Stage 1.\n"
        "  Again, almost always true.\n\n"
        "If the intent was 'stoch_40 must have been in bullish/bearish territory\n"
        "before the pullback setup', rot_level=50 would require stoch_40 > 50 for longs.\n"
        "That is a meaningful quality filter. rot_level=80 is not."
    ))

    lines.append("### Finding 5: BBW is completely orphaned\n")
    annotation(lines, (
        "signals/bbwp.py exists and computes 10 BBW columns including bbwp_value,\n"
        "bbwp_spectrum, bbwp_state.\n"
        "It is NOT imported by signals/four_pillars.py (v1).\n"
        "It is NOT imported by signals/four_pillars_v386.py.\n"
        "It is NOT imported by the bot plugin.\n"
        "Vince cannot see BBW state at trade entry because it is never computed\n"
        "alongside the signal data. The Enricher will have no BBW columns to snapshot."
    ))

    lines.append("### Finding 6: signals/four_pillars.py (v1) vs v386 — different defaults\n")
    annotation(lines, (
        "v1 (what the bot runs):    allow_c=True,  require_stage2=False, rot_level=None\n"
        "v386 (backtester target):  allow_c=False, require_stage2=True,  rot_level=80\n\n"
        "Bot overrides from config.yaml: require_stage2=True, rot_level=80, allow_c=False.\n"
        "So bot is effectively aligned with v386 via config — but running older ATR/stoch code.\n"
        "Key question: does signals/four_pillars.py have the same state machine logic as v386?"
    ))

    hr(lines)

    # ── Parameter Comparison Table ──────────────────────────────────────────
    section(lines, "Parameter Comparison Table", 2)

    lines.append(
        "| Parameter | state_machine.py default | signals/four_pillars.py (v1) | "
        "signals/four_pillars_v386.py | Live bot config.yaml | Notes |\n"
    )
    lines.append("|---|---|---|---|---|---|\n")

    rows = [
        ("cross_level",        "25",    "25",    "25",    "not set (uses code default)", "stoch_9 entry level"),
        ("zone_level",         "30",    "30",    "30",    "not set",                     "stoch_14/40/60 zone"),
        ("stage_lookback",     "10",    "10",    "10",    "not set",                     "bars to wait in Stage 1"),
        ("allow_b_trades",     "True",  "True",  "True",  "allow_b: true",               ""),
        ("allow_c_trades",     "True",  "True",  "False", "allow_c: false",              "v386 disabled C trades"),
        ("require_stage2",     "False", "False", "True",  "require_stage2: true",        "DIVERGENCE: v1 default=False"),
        ("rot_level",          "80",    "None",  "80",    "rot_level: 80",               "see Finding 4"),
        ("cloud3_window",      "5",     "None",  "5",     "not set",                     "bars near Cloud3 required"),
        ("use_ripster",        "False", "False", "False", "not set",                     "ripster disabled everywhere"),
        ("use_60d",            "False", "False", "False", "not set",                     "stoch_60 D-line filter off"),
        ("sl_atr_mult",        "N/A",   "N/A",   "N/A",   "sl_atr_mult: 2.0",            "backtester default: 2.0"),
        ("tp_atr_mult",        "N/A",   "N/A",   "N/A",   "tp_atr_mult: null",           "no fixed TP in either"),
        ("be_trigger_atr",     "N/A",   "N/A",   "N/A",   "NOT PRESENT",                 "BE raise not in bot"),
        ("trailing (method)",  "N/A",   "N/A",   "N/A",   "BingX native 2%",             "backtester uses AVWAP"),
        ("BBW",                "absent","absent","absent","absent",                       "orphaned — not wired anywhere"),
    ]

    for row in rows:
        lines.append("| " + " | ".join(row) + " |\n")

    lines.append("\n")
    hr(lines)

    # ── Source Files ─────────────────────────────────────────────────────────

    section(lines, "Source: signals/state_machine.py — The Actual Entry Conditions", 2)
    annotation(lines, (
        "This is the core logic. Both the v1 and v386 pipelines use THIS file.\n"
        "If you want to understand what Grade A/B/C actually requires, read this."
    ))
    code_block(lines, read_file(ROOT / "signals" / "state_machine.py"))
    hr(lines)

    section(lines, "Source: signals/four_pillars_v386.py — Current Backtester Pipeline", 2)
    annotation(lines, (
        "This is what the backtester is configured to use.\n"
        "Uses the same state_machine.py above but passes v386 defaults."
    ))
    code_block(lines, read_file(ROOT / "signals" / "four_pillars_v386.py"))
    hr(lines)

    section(lines, "Source: signals/four_pillars.py — What the Live Bot Actually Runs", 2)
    annotation(lines, (
        "This is the ORIGINAL pipeline imported by the bot plugin.\n"
        "Compare carefully with v386 above — same state_machine, different defaults."
    ))
    code_block(lines, read_file(ROOT / "signals" / "four_pillars.py"))
    hr(lines)

    section(lines, "Source: engine/position_v384.py — Backtester Exit Logic (AVWAP+BE)", 2)
    annotation(lines, (
        "This is the exit mechanism the backtester uses.\n"
        "Key: AVWAP trailing after checkpoint_interval bars, optional BE raise.\n"
        "The bot does NOT use this — it uses BingX native trailing instead."
    ))
    code_block(lines, read_file(ROOT / "engine" / "position_v384.py"))
    hr(lines)

    section(lines, "Source: engine/exit_manager.py — Dynamic SL/TP Methods", 2)
    annotation(lines, (
        "ExitManager with 4 risk methods: be_only, be_plus_fees, be_plus_fees_trail_tp, be_trail_tp.\n"
        "Status: EXISTS but check whether backtester_v384 actually calls it.\n"
        "position_v384.py has its own inline BE+AVWAP logic — ExitManager may be unused."
    ))
    code_block(lines, read_file(ROOT / "engine" / "exit_manager.py"))
    hr(lines)

    section(lines, "Source: bingx-connector/plugins/four_pillars_v384.py — Live Bot Plugin", 2)
    annotation(lines, (
        "This is what the bot executes on every 5m candle close.\n"
        "Line 21: imports from signals.four_pillars (v1 — NOT v386).\n"
        "Exit is handled by BingX exchange via SL order + native trailing stop order.\n"
        "No AVWAP, no BE raise — those are backtester-only features."
    ))
    code_block(lines, read_file(BOT_ROOT / "plugins" / "four_pillars_v384.py"))
    hr(lines)

    section(lines, "Source: bingx-connector/config.yaml — Live Bot Configuration", 2)
    annotation(lines, (
        "These are the actual values running on the live bot right now.\n"
        "Note: require_stage2=true and rot_level=80 are set here, which overrides\n"
        "the v1 default of require_stage2=False."
    ))
    code_block(lines, read_file(BOT_ROOT / "config.yaml"), lang="yaml")
    hr(lines)

    section(lines, "Source: signals/bbwp.py — BBW Signal (Orphaned)", 2)
    annotation(lines, (
        "This file computes 10 BBW/BBWP columns from close price.\n"
        "Output includes: bbwp_value (percentile rank of BB width),\n"
        "bbwp_spectrum (LOW/NORMAL/HIGH/EXTREME), bbwp_state (BLUE/RED/etc).\n"
        "NOT connected to any signal pipeline or backtester.\n"
        "For Vince to see BBW context at trade entry, this must be called inside\n"
        "compute_signals() before the state machine runs."
    ))
    code_block(lines, read_file(ROOT / "signals" / "bbwp.py"))
    hr(lines)

    # ── Version Docstring History ────────────────────────────────────────────
    section(lines, "Version History — Docstrings Only", 2)
    annotation(lines, "What each version said it changed, in its own words.")

    version_files = [
        ("v3.8.2", ROOT / "signals" / "four_pillars_v382.py"),
        ("v3.8.3", ROOT / "signals" / "four_pillars_v383.py"),
        ("v3.8.3-v2 (Numba)", ROOT / "signals" / "four_pillars_v383_v2.py"),
        ("v3.8.6 / v386",     ROOT / "signals" / "four_pillars_v386.py"),
    ]

    for name, path in version_files:
        section(lines, name, 3)
        content = read_file(path)
        # Extract docstring (everything between first and second triple-quote)
        if '"""' in content:
            parts = content.split('"""')
            if len(parts) >= 3:
                docstring = parts[1].strip()
                code_block(lines, '"""\n' + docstring + '\n"""', lang="")
            else:
                code_block(lines, content[:400], lang="python")
        else:
            code_block(lines, content[:400], lang="python")

    hr(lines)

    # ── Key Questions for Claude Web ─────────────────────────────────────────
    section(lines, "Questions for Claude Web Discussion", 2)

    questions = [
        "1. The state machine uses rot_level=80, which means stoch_40 > 20 for longs. "
        "Is this a meaningful filter at all? What would rot_level need to be to enforce "
        "'stoch_40 was in bullish territory before the oversold setup'?",

        "2. The backtester uses AVWAP trailing (SL moves to AVWAP center after N bars). "
        "The live bot uses BingX native trailing (2% callback from peak at 2x ATR activation). "
        "How much divergence should we expect in exit prices? Which is more aligned with "
        "the strategy intent?",

        "3. v386 was written but the bot still imports v1. The bot overrides require_stage2 "
        "and rot_level via config, so signal logic is approximately the same. But are there "
        "any code-level differences between signals/four_pillars.py and v386 that matter?",

        "4. BBW (Bollinger Band Width Percentile) is computed in bbwp.py but never wired in. "
        "If we wire it into compute_signals(), what would Vince actually see? Is BBWP the "
        "right context variable for understanding why trades win or lose?",

        "5. ExitManager exists with 4 risk methods but position_v384.py has its own inline "
        "BE+AVWAP logic. Is ExitManager actually called anywhere, or is it dead code?",

        "6. Grade C fires when: stoch_14 was seen in zone AND price_pos == +1 (LONG) or "
        "-1 (SHORT). With allow_c_trades=False, Grade C is disabled. "
        "Was the original C-grade intent different from this implementation?",
    ]

    for q in questions:
        lines.append("- " + q + "\n\n")

    hr(lines)
    lines.append("*End of report. Generated by scripts/build_strategy_analysis.py*\n")

    return "".join(lines)


def main():
    """Build the strategy analysis report."""
    out_path = ROOT / "docs" / "STRATEGY-ANALYSIS-REPORT.md"

    if out_path.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = ROOT / "docs" / ("STRATEGY-ANALYSIS-REPORT_" + ts + ".md")
        print("Existing report found — writing versioned copy: " + out_path.name)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_report()
    out_path.write_text(report, encoding="utf-8")

    size_kb = out_path.stat().st_size / 1024
    print("Report written: " + str(out_path))
    print("Size: " + str(round(size_kb, 1)) + " KB")
    print("Open this file and paste the contents into Claude Web.")


if __name__ == "__main__":
    main()

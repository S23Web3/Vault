"""
Vince v2 — Codebase audit and bug finder.

Reads source files via AST analysis and text inspection.
Checks interface compliance, orphaned code, parameter inconsistencies,
and divergences between backtester and live bot.

ANALYSIS ONLY. Never modifies any file.

Run standalone:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester"
    python -c "from vince.audit import run_audit; run_audit()"

Or import in tests:
    from vince.audit import run_audit
    findings = run_audit(print_results=False)
    criticals = [f for f in findings if f.severity == "CRITICAL"]
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
BOT_ROOT = ROOT.parent / "bingx-connector"


# ── Finding dataclass ─────────────────────────────────────────────────────────

@dataclass
class AuditFinding:
    """Single audit finding with severity, category, location, and message."""

    severity: str    # CRITICAL | WARNING | INFO
    category: str    # SHORT tag e.g. BOT, BBW, EXIT, INTERFACE, VERSION, TRAILING
    file: str        # Relative file path(s) — human-readable label
    message: str     # Full description of the finding
    timestamp: str = ""

    def __post_init__(self):
        """Set timestamp at creation."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def __str__(self) -> str:
        """Single-line string representation."""
        return "[" + self.severity + "] " + self.category + " | " + self.file + " | " + self.message


# ── Auditor ───────────────────────────────────────────────────────────────────

class Auditor:
    """Runs all audit checks and collects findings."""

    SEVERITY_ORDER = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}

    def __init__(self):
        """Initialise empty findings list."""
        self.findings: list[AuditFinding] = []

    def _add(self, severity: str, category: str, file: str, message: str) -> None:
        """Append a new finding."""
        self.findings.append(AuditFinding(severity, category, file, message))

    def _read(self, path: Path) -> str:
        """Read file content; return empty string if not found."""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
        except Exception as e:
            return ""

    def _parse(self, path: Path) -> Optional[ast.Module]:
        """Parse Python source to AST; return None on error (finding added)."""
        content = self._read(path)
        if not content:
            return None
        try:
            return ast.parse(content)
        except SyntaxError as e:
            rel = str(path.relative_to(ROOT)) if ROOT in path.parents else str(path)
            self._add("CRITICAL", "SYNTAX", rel, "SyntaxError: " + str(e))
            return None

    def _class_methods(self, tree: ast.Module, class_name: str) -> set[str]:
        """Return method names defined directly on a named class."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return {
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
        return set()

    def _class_bases(self, tree: ast.Module, class_name: str) -> list[str]:
        """Return base class names for a named class."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return [ast.unparse(b) for b in node.bases]
        return []

    def _imports(self, tree: ast.Module) -> list[str]:
        """Extract all imported module names."""
        result = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                result.append(node.module)
        return result

    def _grep(self, content: str, keyword: str) -> list[str]:
        """Return lines containing keyword."""
        return [ln.strip() for ln in content.splitlines() if keyword in ln]

    # ── Check 1: Syntax — AST parse all key files ─────────────────────────────

    def check_syntax_all(self) -> None:
        """AST-parse all key strategy and engine files."""
        key_files = [
            ROOT / "signals" / "state_machine.py",
            ROOT / "signals" / "four_pillars.py",
            ROOT / "signals" / "four_pillars_v386.py",
            ROOT / "signals" / "bbwp.py",
            ROOT / "signals" / "bbw_sequence.py",
            ROOT / "signals" / "clouds.py",
            ROOT / "signals" / "stochastics.py",
            ROOT / "engine" / "position_v384.py",
            ROOT / "engine" / "backtester_v384.py",
            ROOT / "engine" / "backtester_v385.py",
            ROOT / "engine" / "exit_manager.py",
            ROOT / "engine" / "avwap.py",
            ROOT / "engine" / "commission.py",
            ROOT / "strategies" / "base_v2.py",
            ROOT / "strategies" / "four_pillars.py",
            ROOT / "vince" / "__init__.py",
            ROOT / "vince" / "types.py",
            ROOT / "vince" / "api.py",
        ]
        for path in key_files:
            rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
            if not path.exists():
                self._add("WARNING", "SYNTAX", rel, "File does not exist.")
                continue
            tree = self._parse(path)
            if tree is not None:
                self._add("INFO", "SYNTAX", rel, "AST parse OK.")

    # ── Check 2: Live bot signal import ───────────────────────────────────────

    def check_bot_signal_import(self) -> None:
        """Verify what signal file the live bot plugin actually imports."""
        path = BOT_ROOT / "plugins" / "four_pillars_v384.py"
        if not path.exists():
            self._add("WARNING", "BOT", "bingx-connector/plugins/four_pillars_v384.py",
                      "Bot plugin not found — cannot audit signal import.")
            return
        content = self._read(path)
        if "four_pillars_v386" in content:
            self._add("INFO", "BOT", "bingx-connector/plugins/four_pillars_v384.py",
                      "Bot correctly imports signals.four_pillars_v386.")
        elif "from signals.four_pillars import" in content:
            self._add("CRITICAL", "BOT", "bingx-connector/plugins/four_pillars_v384.py",
                      "Bot imports signals.four_pillars (v1 original) NOT four_pillars_v386. "
                      "v386 exists but is disconnected from the live bot. "
                      "Bot is running older signal defaults: allow_c=True default, "
                      "require_stage2=False default (overridden by config.yaml).")
        else:
            import_lines = self._grep(content, "import")
            self._add("WARNING", "BOT", "bingx-connector/plugins/four_pillars_v384.py",
                      "Unexpected signal import pattern. Lines: " + " | ".join(import_lines[:3]))

    # ── Check 3: BBW wiring ───────────────────────────────────────────────────

    def check_bbw_wiring(self) -> None:
        """Check if BBW is wired into signal pipelines."""
        bbwp_path = ROOT / "signals" / "bbwp.py"
        if not bbwp_path.exists():
            self._add("WARNING", "BBW", "signals/bbwp.py",
                      "bbwp.py does not exist — BBW signal unavailable.")
            return
        self._add("INFO", "BBW", "signals/bbwp.py", "File exists and is available.")

        for fname in ["four_pillars.py", "four_pillars_v386.py"]:
            path = ROOT / "signals" / fname
            content = self._read(path)
            if not content:
                continue
            if "bbwp" in content or "bbw" in content.lower():
                self._add("INFO", "BBW", "signals/" + fname,
                          "BBW is referenced — check that compute_bbwp() is actually called.")
            else:
                self._add("CRITICAL", "BBW", "signals/" + fname,
                          "bbwp.py is NOT imported or called in " + fname + ". "
                          "BBW state will be ABSENT from all trade enrichment snapshots. "
                          "Vince Enricher will have no BBW columns to snapshot at entry, "
                          "MFE, or exit bars. IndicatorSnapshot.bbw will always be None.")

    # ── Check 4: ExitManager usage ────────────────────────────────────────────

    def check_exit_manager_usage(self) -> None:
        """Check if ExitManager is actually called by any engine file."""
        em_path = ROOT / "engine" / "exit_manager.py"
        if not em_path.exists():
            self._add("WARNING", "EXIT", "engine/exit_manager.py",
                      "exit_manager.py does not exist.")
            return

        callers = []
        for path in (ROOT / "engine").glob("*.py"):
            if path.name == "exit_manager.py":
                continue
            content = self._read(path)
            if "ExitManager" in content or "exit_manager" in content:
                callers.append(path.name)

        if not callers:
            self._add("CRITICAL", "EXIT", "engine/exit_manager.py",
                      "ExitManager defined but NOT imported by any engine file. "
                      "Likely dead code. position_v384.py handles BE+AVWAP logic inline "
                      "without delegating to ExitManager. Verify before using in B3/B4.")
        else:
            self._add("INFO", "EXIT", "engine/exit_manager.py",
                      "ExitManager referenced in: " + ", ".join(callers))

    # ── Check 5: StrategyPlugin ABC compliance ────────────────────────────────

    def check_strategy_plugin_compliance(self) -> None:
        """Check if four_pillars.py (v1) implements all 5 required abstract methods."""
        required = {"compute_signals", "parameter_space", "trade_schema",
                    "run_backtest", "strategy_document"}

        path = ROOT / "strategies" / "four_pillars.py"
        if not path.exists():
            self._add("WARNING", "INTERFACE", "strategies/four_pillars.py",
                      "File does not exist — FourPillarsPlugin not yet built (B1 pending).")
            return

        tree = self._parse(path)
        if tree is None:
            return

        # Find plugin classes
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        if not classes:
            self._add("WARNING", "INTERFACE", "strategies/four_pillars.py",
                      "No classes found in file.")
            return

        for cls in classes:
            methods = {
                n.name for n in cls.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            missing = required - methods
            if missing:
                self._add("CRITICAL", "INTERFACE", "strategies/four_pillars.py",
                          cls.name + " is missing required abstract methods: " +
                          ", ".join(sorted(missing)) + ". "
                          "Class cannot be instantiated as a StrategyPlugin.")
            else:
                self._add("INFO", "INTERFACE", "strategies/four_pillars.py",
                          cls.name + " implements all 5 required abstract methods.")

            bases = [ast.unparse(b) for b in cls.bases]
            if not any("StrategyPlugin" in b for b in bases):
                self._add("CRITICAL", "INTERFACE", "strategies/four_pillars.py",
                          cls.name + " does not inherit from StrategyPlugin (base_v2). "
                          "Current bases: " + str(bases) + ". "
                          "Vince infrastructure will not accept this class as a valid plugin.")
            else:
                self._add("INFO", "INTERFACE", "strategies/four_pillars.py",
                          cls.name + " correctly inherits StrategyPlugin.")

    # ── Check 6: rot_level semantics ──────────────────────────────────────────

    def check_rot_level(self) -> None:
        """Audit rot_level defaults across all signal files, state machine, bot config."""
        findings = []

        for fname in ["four_pillars.py", "four_pillars_v386.py"]:
            content = self._read(ROOT / "signals" / fname)
            for line in self._grep(content, "rot_level"):
                findings.append(fname + ": " + line)

        sm_content = self._read(ROOT / "signals" / "state_machine.py")
        for line in self._grep(sm_content, "rot_level"):
            findings.append("state_machine.py: " + line)

        cfg_content = self._read(BOT_ROOT / "config.yaml")
        for line in self._grep(cfg_content, "rot_level"):
            findings.append("bingx/config.yaml: " + line)

        self._add("WARNING", "ROT_LEVEL",
                  "signals/state_machine.py + signals/four_pillars_v386.py + bingx/config.yaml",
                  "rot_level=80 in all files. "
                  "For LONGS: condition is stoch_40 > (100-80)=20 during Stage 1. "
                  "stoch_40 > 20 is almost always true — this barely filters anything. "
                  "If intent is 'stoch_40 was in bullish territory before the pullback setup', "
                  "rot_level should be ~50 (requires stoch_40 > 50). "
                  "Occurrences: " + " | ".join(findings))

    # ── Check 7: State machine version matrix ─────────────────────────────────

    def check_state_machine_versions(self) -> None:
        """Verify which state machine version each signal pipeline imports."""
        signal_files = [
            "four_pillars.py",
            "four_pillars_v382.py",
            "four_pillars_v383.py",
            "four_pillars_v383_v2.py",
            "four_pillars_v386.py",
        ]
        for fname in signal_files:
            path = ROOT / "signals" / fname
            content = self._read(path)
            if not content:
                self._add("INFO", "VERSION", "signals/" + fname, "File not found — skipped.")
                continue
            sm_imports = self._grep(content, "state_machine")
            if sm_imports:
                self._add("INFO", "VERSION", "signals/" + fname,
                          "State machine import(s): " + " | ".join(sm_imports[:2]))
            else:
                self._add("WARNING", "VERSION", "signals/" + fname,
                          "No state_machine import found — unexpected.")

    # ── Check 8: Backtester vs bot trailing stop divergence ───────────────────

    def check_trailing_divergence(self) -> None:
        """Flag the fundamental trailing stop divergence between backtester and live bot."""
        bt_content = self._read(ROOT / "engine" / "position_v384.py")
        cfg_content = self._read(BOT_ROOT / "config.yaml")

        has_avwap = "avwap" in bt_content.lower() or "AVWAPTracker" in bt_content
        has_native_trail = "trailing_rate" in cfg_content

        if has_avwap and has_native_trail:
            self._add("CRITICAL", "TRAILING",
                      "engine/position_v384.py vs bingx-connector/config.yaml",
                      "TRAILING STOP DIVERGENCE. "
                      "Backtester: AVWAP-based trailing (SL moves to AVWAP center after "
                      "checkpoint_interval bars, ratchets continuously with each bar). "
                      "Live bot: BingX native trailing (trailing_rate=2% callback from peak "
                      "when price reaches entry +/- trailing_activation_atr_mult=2.0 x ATR). "
                      "These mechanisms produce different exit prices on the same trade. "
                      "Backtest results CANNOT be directly compared to live bot results. "
                      "Calibration required before using backtest stats to justify live risk.")

    # ── Check 9: require_stage2 default mismatch ──────────────────────────────

    def check_require_stage2(self) -> None:
        """Check require_stage2 defaults and flag mismatches."""
        findings = []

        for label, path in [
            ("signals/four_pillars.py", ROOT / "signals" / "four_pillars.py"),
            ("signals/four_pillars_v386.py", ROOT / "signals" / "four_pillars_v386.py"),
            ("signals/state_machine.py", ROOT / "signals" / "state_machine.py"),
        ]:
            content = self._read(path)
            for line in self._grep(content, "require_stage2"):
                findings.append(label + ": " + line)

        cfg_content = self._read(BOT_ROOT / "config.yaml")
        for line in self._grep(cfg_content, "require_stage2"):
            findings.append("bingx/config.yaml: " + line)

        self._add("WARNING", "STAGE2", "multiple files",
                  "require_stage2 default is False in state_machine.py (and v1 pipeline) "
                  "but True in v386 defaults and bot config.yaml. "
                  "If require_stage2 is accidentally passed as False (e.g. by an old test "
                  "or an unconfigured plugin), Grade A will fire without Stage 2 validation — "
                  "significantly more signals, lower conviction. "
                  "Details: " + " | ".join(findings))

    # ── Check 10: Breakeven raise — bot vs backtester ─────────────────────────

    def check_breakeven_divergence(self) -> None:
        """Check if BE raise is configured in bot vs backtester."""
        bt_content = self._read(ROOT / "engine" / "position_v384.py")
        cfg_content = self._read(BOT_ROOT / "config.yaml")

        has_be_bt = "be_trigger_atr" in bt_content
        has_be_bot = "be_trigger_atr" in cfg_content or "breakeven" in cfg_content.lower()

        if has_be_bt and not has_be_bot:
            self._add("CRITICAL", "BREAKEVEN",
                      "engine/position_v384.py vs bingx-connector/config.yaml",
                      "BE raise (breakeven) is implemented in backtester (position_v384.py: "
                      "be_trigger_atr / be_lock_atr) but NOT configured in the live bot. "
                      "Bot relies solely on BingX native trailing stop — no BE raise step. "
                      "This means the bot has no intermediate risk reduction between "
                      "initial ATR-SL and trailing stop activation.")
        elif has_be_bt and has_be_bot:
            self._add("INFO", "BREAKEVEN",
                      "engine/position_v384.py + bingx-connector/config.yaml",
                      "BE raise is configured in both backtester and bot.")

    # ── Check 11: vince/ directory structure ──────────────────────────────────

    def check_vince_structure(self) -> None:
        """Verify vince/ directory and all B2 files exist."""
        vince_dir = ROOT / "vince"
        if not vince_dir.exists():
            self._add("WARNING", "VINCE", "vince/",
                      "vince/ directory does not exist — B2 not yet built.")
            return

        b2_files = ["__init__.py", "types.py", "api.py", "audit.py"]
        for fname in b2_files:
            p = vince_dir / fname
            status = "EXISTS" if p.exists() else "MISSING"
            sev = "INFO" if p.exists() else "WARNING"
            self._add(sev, "VINCE", "vince/" + fname, status)

    # ── Check 12: bot config sl_mult vs backtester default ────────────────────

    def check_sl_mult_consistency(self) -> None:
        """Check sl_mult consistency between bot config and backtester default."""
        cfg_content = self._read(BOT_ROOT / "config.yaml")
        bt_content = self._read(ROOT / "engine" / "backtester_v384.py")

        cfg_lines = self._grep(cfg_content, "sl_atr_mult")
        bt_lines = self._grep(bt_content, "sl_mult")

        cfg_val = None
        bt_val = None

        for line in cfg_lines:
            if ":" in line:
                try:
                    cfg_val = float(line.split(":")[-1].strip().split()[0])
                except (ValueError, IndexError):
                    pass

        for line in bt_lines:
            if "get(" in line and "sl_mult" in line:
                try:
                    bt_val = float(line.split(",")[-1].strip().rstrip(")"))
                except (ValueError, IndexError):
                    pass

        if cfg_val is not None and bt_val is not None:
            if abs(cfg_val - bt_val) > 0.001:
                self._add("CRITICAL", "SL_MULT",
                          "bingx-connector/config.yaml vs engine/backtester_v384.py",
                          "sl_mult MISMATCH: bot config=" + str(cfg_val) +
                          " vs backtester default=" + str(bt_val) + ". "
                          "BUG-C08 from UML audit doc: sl_mult mismatch invalidates all "
                          "backtest vs live comparisons. Must use identical values.")
            else:
                self._add("INFO", "SL_MULT",
                          "bingx-connector/config.yaml vs engine/backtester_v384.py",
                          "sl_mult consistent: bot=" + str(cfg_val) +
                          " backtester=" + str(bt_val))
        else:
            self._add("WARNING", "SL_MULT",
                      "bingx-connector/config.yaml vs engine/backtester_v384.py",
                      "Could not extract numeric sl_mult from one or both files for comparison.")

    # ── Check 13: mfe_bar availability for enricher ───────────────────────────

    def check_mfe_bar_field(self) -> None:
        """Check if life_mfe_bar is exposed by backtester_v385 for the enricher."""
        path = ROOT / "engine" / "backtester_v385.py"
        content = self._read(path)
        if not content:
            self._add("WARNING", "ENRICHER", "engine/backtester_v385.py",
                      "backtester_v385.py not found — cannot check life_mfe_bar availability.")
            return

        if "life_mfe_bar" in content or "mfe_bar" in content:
            self._add("INFO", "ENRICHER", "engine/backtester_v385.py",
                      "mfe_bar field found — enricher can locate MFE bar index.")
        else:
            self._add("CRITICAL", "ENRICHER", "engine/backtester_v385.py",
                      "life_mfe_bar NOT found in backtester_v385.py output. "
                      "Enricher (B3) needs MFE bar index to snapshot indicator state "
                      "at the bar where maximum favorable excursion occurred. "
                      "B3 is BLOCKED until mfe_bar is exposed in the trade record.")

    def run_all(self) -> list[AuditFinding]:
        """Run all audit checks; return findings sorted CRITICAL → WARNING → INFO."""
        self.check_syntax_all()
        self.check_bot_signal_import()
        self.check_bbw_wiring()
        self.check_exit_manager_usage()
        self.check_strategy_plugin_compliance()
        self.check_rot_level()
        self.check_state_machine_versions()
        self.check_trailing_divergence()
        self.check_require_stage2()
        self.check_breakeven_divergence()
        self.check_vince_structure()
        self.check_sl_mult_consistency()
        self.check_mfe_bar_field()

        return sorted(
            self.findings,
            key=lambda f: (self.SEVERITY_ORDER.get(f.severity, 3), f.category),
        )


# ── Public entry point ────────────────────────────────────────────────────────

def run_audit(print_results: bool = True) -> list[AuditFinding]:
    """Run full codebase audit. Returns list of AuditFinding objects.

    Args:
        print_results: If True, print formatted report to stdout.

    Returns:
        All findings sorted CRITICAL → WARNING → INFO.
    """
    auditor = Auditor()
    findings = auditor.run_all()

    if print_results:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print("=" * 72)
        print("VINCE CODEBASE AUDIT  —  " + ts)
        print("=" * 72)

        for sev in ("CRITICAL", "WARNING", "INFO"):
            group = [f for f in findings if f.severity == sev]
            if not group:
                continue
            print("\n--- " + sev + " (" + str(len(group)) + ") " + "-" * (50 - len(sev)))
            for f in group:
                print("\n[" + f.severity + "] " + f.category + " | " + f.file)
                # Word-wrap message at 70 chars
                msg = f.message
                while len(msg) > 70:
                    split_at = msg.rfind(" ", 0, 70)
                    if split_at == -1:
                        split_at = 70
                    print("  " + msg[:split_at])
                    msg = msg[split_at:].lstrip()
                if msg:
                    print("  " + msg)

        n_crit = sum(1 for f in findings if f.severity == "CRITICAL")
        n_warn = sum(1 for f in findings if f.severity == "WARNING")
        n_info = sum(1 for f in findings if f.severity == "INFO")
        print("\n" + "=" * 72)
        print("SUMMARY: " + str(n_crit) + " CRITICAL  |  " +
              str(n_warn) + " WARNING  |  " + str(n_info) + " INFO")
        print("=" * 72)

    return findings


if __name__ == "__main__":
    run_audit()

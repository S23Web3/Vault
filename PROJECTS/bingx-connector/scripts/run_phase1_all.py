"""
Phase 1 runner: executes all 6 diagnostic scripts in sequence.

Scripts run:
  1A  run_error_audit.py       -- parse bot log, categorise errors
  1B  run_variable_web.py      -- static AST dependency map
  1C  run_ttp_audit.py         -- TTP state vs log timeline
  1D  run_ticker_collector.py  -- BingX liquidity ranking (public API)
  1E  run_demo_order_verify.py -- test order types on BingX VST
  1F  run_trade_analysis.py    -- MFE/MAE/saw_green per trade

Scripts 1E and 1F require API keys in .env.
Script 1F is rate-limited and may take ~10-15 minutes for 231 trades.

Run: python scripts/run_phase1_all.py
     python scripts/run_phase1_all.py --skip-slow   (skip 1E and 1F)
     python scripts/run_phase1_all.py --only 1D      (run one script)
"""
import sys
import time
import logging
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


SCRIPTS = [
    ("1A", "run_error_audit",       False),
    ("1B", "run_variable_web",      False),
    ("1C", "run_ttp_audit",         False),
    ("1D", "run_ticker_collector",  False),
    ("1E", "run_demo_order_verify", True),   # slow=True: requires VST API
    ("1F", "run_trade_analysis",    True),   # slow=True: rate-limited, ~15 min
]


def run_script(tag: str, module_name: str) -> bool:
    """Run one diagnostic script via subprocess. Return True on success."""
    bar = "=" * 60
    log.info(bar)
    log.info("PHASE %s -- %s", tag, module_name)
    log.info(bar)
    t0 = time.time()
    script_path = Path(__file__).resolve().parent / (module_name + ".py")
    if not script_path.exists():
        log.error("Script not found: %s", script_path)
        return False
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent.parent),
    )
    elapsed = round(time.time() - t0, 1)
    if result.returncode == 0:
        log.info("-- %s DONE in %.1fs --", tag, elapsed)
        return True
    log.error("-- %s FAILED (exit code %s) after %.1fs --", tag, result.returncode, elapsed)
    return False


def main() -> None:
    """Parse args and run selected scripts."""
    args = sys.argv[1:]
    skip_slow = "--skip-slow" in args
    only_tag  = None
    if "--only" in args:
        idx = args.index("--only")
        if idx + 1 < len(args):
            only_tag = args[idx + 1].upper()

    print("")
    print("=" * 60)
    print("  PHASE 1 DIAGNOSTICS RUNNER")
    print("=" * 60)
    if skip_slow:
        print("  --skip-slow: skipping 1E (demo verify) and 1F (trade analysis)")
    if only_tag:
        print("  --only " + only_tag + ": running single script")
    print("")

    results = {}
    for tag, module_name, slow in SCRIPTS:
        if only_tag and tag != only_tag:
            continue
        if skip_slow and slow:
            log.info("SKIP %s -- %s (use without --skip-slow to run)", tag, module_name)
            results[tag] = "SKIPPED"
            continue
        ok = run_script(tag, module_name)
        results[tag] = "OK" if ok else "FAIL"
        print("")

    # Summary
    print("=" * 60)
    print("  PHASE 1 SUMMARY")
    print("=" * 60)
    for tag, status in results.items():
        icon = "OK  " if status == "OK" else ("SKIP" if status == "SKIPPED" else "FAIL")
        print("  [" + icon + "] " + tag)
    print("")

    failures = [t for t, s in results.items() if s == "FAIL"]
    if failures:
        print("FAILED: " + ", ".join(failures))
        print("Check logs above for details.")
        sys.exit(1)
    else:
        print("All completed. Check logs/ directory for output files.")
        print("")
        print("Output files:")
        log_dir = ROOT / "logs"
        for f in sorted(log_dir.glob("*.md")) if log_dir.exists() else []:
            print("  " + str(f.name))


if __name__ == "__main__":
    main()

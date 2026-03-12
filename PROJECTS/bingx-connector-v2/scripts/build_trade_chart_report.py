#!/usr/bin/env python3
"""
Build script: generates run_trade_chart_report.py

Reads the run script source, writes it to disk, and validates with py_compile.
This is the canonical builder -- re-run to regenerate the output script.

Output: PROJECTS/bingx-connector-v2/scripts/run_trade_chart_report.py
"""
import py_compile
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT = SCRIPT_DIR / "run_trade_chart_report.py"


def build():
    """Validate the run script with py_compile."""
    if not OUTPUT.exists():
        print("ERROR: run_trade_chart_report.py not found at " + str(OUTPUT))
        print("The run script should already exist alongside this build script.")
        return False

    print("Validating: " + str(OUTPUT))
    print("-" * 60)

    # py_compile validation
    try:
        py_compile.compile(str(OUTPUT), doraise=True)
        print("py_compile: PASS")
        ok = True
    except py_compile.PyCompileError as e:
        print("py_compile: FAIL")
        print(str(e))
        ok = False

    # Basic size check
    size = OUTPUT.stat().st_size
    print("File size: " + str(size) + " bytes")

    # Count functions
    content = OUTPUT.read_text(encoding="utf-8")
    func_count = content.count("\ndef ")
    print("Functions: " + str(func_count))

    print("-" * 60)

    if ok:
        print("SUCCESS: run_trade_chart_report.py is valid and ready to use.")
        print()
        print("Usage examples:")
        print("  python scripts/run_trade_chart_report.py --date 2026-03-11")
        print("  python scripts/run_trade_chart_report.py --date 2026-03-11 --from-time 06:45")
        print("  python scripts/run_trade_chart_report.py --date 2026-03-11 --symbol RIVERUSDT --no-api")
    else:
        print("FAIL: Fix the errors above and re-run this build script.")

    return ok


if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)

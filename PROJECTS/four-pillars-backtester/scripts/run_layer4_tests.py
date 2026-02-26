"""Layer 4 Test Runner: py_compile + run all test/debug/sanity scripts.

Saves combined output to 06-CLAUDE-LOGS/2026-02-14-bbw-layer4-results.md.
Run: python scripts/run_layer4_tests.py
"""

import sys
import subprocess
import py_compile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT.parent.parent  # Obsidian Vault root
LOG_DIR = VAULT / "06-CLAUDE-LOGS"
LOG_FILE = LOG_DIR / "2026-02-14-bbw-layer4-results.md"


def compile_check(filepath, label):
    """Verify Python file compiles without syntax errors."""
    try:
        py_compile.compile(str(filepath), doraise=True)
        print(f"  OK    py_compile {label}")
        return True
    except py_compile.PyCompileError as e:
        print(f"  FAIL  py_compile {label}: {e}")
        return False


def main():
    """Run all Layer 4 validation scripts."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"Layer 4 Test Runner -- {ts}")
    print("=" * 70)
    print()

    # Step 1: py_compile all Layer 4 files
    files_to_check = [
        (ROOT / "research" / "bbw_simulator.py", "research/bbw_simulator.py"),
        (ROOT / "tests" / "test_bbw_simulator.py", "tests/test_bbw_simulator.py"),
        (ROOT / "scripts" / "debug_bbw_simulator.py", "scripts/debug_bbw_simulator.py"),
        (ROOT / "scripts" / "sanity_check_bbw_simulator.py", "scripts/sanity_check_bbw_simulator.py"),
    ]
    all_ok = True
    for fpath, label in files_to_check:
        if not fpath.exists():
            print(f"  MISS  {label} -- file not found")
            all_ok = False
            continue
        if not compile_check(fpath, label):
            all_ok = False

    if not all_ok:
        print("\npy_compile FAILED -- fix syntax errors before running tests")
        sys.exit(1)

    print("\nAll files compile OK.\n")

    # Step 2: Run scripts and capture output
    scripts_to_run = [
        ("Layer 4 Tests", ROOT / "tests" / "test_bbw_simulator.py"),
        ("Layer 4 Debug Validator", ROOT / "scripts" / "debug_bbw_simulator.py"),
        ("Layer 4 Sanity Check", ROOT / "scripts" / "sanity_check_bbw_simulator.py"),
    ]

    all_output = []
    all_output.append(f"# Layer 4 Test Results -- {ts}\n")

    for section_name, script_path in scripts_to_run:
        print(f"{'='*70}")
        print(f"Running: {section_name}")
        print(f"{'='*70}")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, cwd=str(ROOT),
                timeout=300,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            print(output)
        except subprocess.TimeoutExpired:
            output = f"TIMEOUT after 300s"
            print(output)
        except Exception as e:
            output = f"ERROR: {e}"
            print(output)

        all_output.append(f"\n## {section_name}")
        all_output.append("```")
        all_output.append(output.rstrip())
        all_output.append("```\n")

    # Step 3: Save to log file
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_content = "\n".join(all_output)
    LOG_FILE.write_text(log_content, encoding="utf-8")
    print(f"\nResults saved to: {LOG_FILE}")
    print("Done.")


if __name__ == "__main__":
    main()

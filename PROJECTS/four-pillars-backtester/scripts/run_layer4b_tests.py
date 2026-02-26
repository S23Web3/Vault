"""Layer 4b Test Runner: py_compile + all 3 test scripts.

Runs in order:
1. py_compile all 5 Layer 4b files
2. tests/test_bbw_monte_carlo.py
3. scripts/debug_bbw_monte_carlo.py
4. scripts/sanity_check_bbw_monte_carlo.py

Saves output to 06-CLAUDE-LOGS/2026-02-16-bbw-layer4b-results.md.
Run: python scripts/run_layer4b_tests.py
"""

import sys
import subprocess
import py_compile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT.parent.parent
LOG_DIR = VAULT / "06-CLAUDE-LOGS"
LOG_FILE = LOG_DIR / "2026-02-16-bbw-layer4b-results.md"

FILES_TO_COMPILE = [
    ROOT / "research" / "bbw_monte_carlo.py",
    ROOT / "tests" / "test_bbw_monte_carlo.py",
    ROOT / "scripts" / "debug_bbw_monte_carlo.py",
    ROOT / "scripts" / "sanity_check_bbw_monte_carlo.py",
    ROOT / "scripts" / "run_layer4b_tests.py",
]

SCRIPTS_TO_RUN = [
    ("Unit Tests", ROOT / "tests" / "test_bbw_monte_carlo.py"),
    ("Debug Checks", ROOT / "scripts" / "debug_bbw_monte_carlo.py"),
    ("Sanity Check", ROOT / "scripts" / "sanity_check_bbw_monte_carlo.py"),
]


def ts():
    """Get current UTC timestamp string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_compile_checks():
    """Run py_compile on all Layer 4b files."""
    print(f"[{ts()}] === py_compile Check ===")
    results = []
    for f in FILES_TO_COMPILE:
        try:
            py_compile.compile(str(f), doraise=True)
            status = "PASS"
            print(f"  PASS  {f.name}")
        except py_compile.PyCompileError as e:
            status = f"FAIL: {e}"
            print(f"  FAIL  {f.name}: {e}")
        results.append((f.name, status))
    return results


def run_script(label, script_path):
    """Run a Python script and capture output."""
    print(f"\n[{ts()}] === {label}: {script_path.name} ===")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True, timeout=300,
            cwd=str(ROOT),
        )
        output = result.stdout
        if result.stderr:
            output += "\n--- STDERR ---\n" + result.stderr
        print(output)
        return result.returncode, output
    except subprocess.TimeoutExpired:
        msg = f"TIMEOUT after 300s"
        print(f"  {msg}")
        return -1, msg
    except Exception as e:
        msg = f"ERROR: {e}"
        print(f"  {msg}")
        return -1, msg


def save_log(compile_results, script_results):
    """Save all results to log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Layer 4b Test Results")
    lines.append(f"**Timestamp:** {ts()}")
    lines.append("")
    lines.append("## py_compile Results")
    lines.append("| File | Status |")
    lines.append("|------|--------|")
    for fname, status in compile_results:
        lines.append(f"| {fname} | {status} |")
    lines.append("")

    for label, retcode, output in script_results:
        lines.append(f"## {label}")
        lines.append(f"**Return code:** {retcode}")
        lines.append("```")
        lines.append(output.rstrip())
        lines.append("```")
        lines.append("")

    content = "\n".join(lines)

    if LOG_FILE.exists():
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n\n---\n\n")
            f.write(content)
    else:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"\n[{ts()}] Saved to: {LOG_FILE}")


def main():
    """Run all Layer 4b tests and save results."""
    print("=" * 70)
    print(f"Layer 4b Test Runner -- {ts()}")
    print("=" * 70)

    compile_results = run_compile_checks()
    compile_pass = all(s == "PASS" for _, s in compile_results)
    if not compile_pass:
        print("\npy_compile FAILED -- aborting test scripts")
        save_log(compile_results, [])
        return

    script_results = []
    for label, path in SCRIPTS_TO_RUN:
        retcode, output = run_script(label, path)
        script_results.append((label, retcode, output))

    save_log(compile_results, script_results)

    print()
    print("=" * 70)
    all_pass = compile_pass and all(r == 0 for _, r, _ in script_results)
    if all_pass:
        print("ALL LAYER 4b TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check log")
    print("=" * 70)


if __name__ == "__main__":
    main()

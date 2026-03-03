"""
B2 Validation Runner — Vince API Layer + Dataclasses.

Validates all B2 files:
  - py_compile check on every vince/ file
  - Runs tests/test_b2_api.py smoke tests
  - Runs vince/audit.py full codebase audit
  - Prints final summary

Does NOT create any files. All files were written by Claude Code directly.

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester"
    python scripts/build_b2_api.py
"""

import py_compile
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

PASSES: list[str] = []
FAILURES: list[str] = []


def validate(label: str, path: Path) -> bool:
    """py_compile a file; return True on success."""
    try:
        py_compile.compile(str(path), doraise=True)
        PASSES.append("compile:" + label)
        print("[COMPILE] " + label + " — PASS")
        return True
    except py_compile.PyCompileError as e:
        FAILURES.append("compile:" + label + " — " + str(e))
        print("[COMPILE] " + label + " — FAIL: " + str(e))
        return False


def main() -> None:
    """Run all B2 validation steps."""
    print("=" * 64)
    print("B2 VALIDATION — Vince API Layer + Dataclasses")
    print("Started: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 64)

    # ── Step 1: py_compile all vince/ files ──────────────────────────────────
    print("\n[STEP 1] py_compile — vince/ files")
    vince_files = [
        (ROOT / "vince" / "__init__.py",  "vince/__init__.py"),
        (ROOT / "vince" / "types.py",     "vince/types.py"),
        (ROOT / "vince" / "api.py",       "vince/api.py"),
        (ROOT / "vince" / "audit.py",     "vince/audit.py"),
        (ROOT / "tests" / "test_b2_api.py", "tests/test_b2_api.py"),
    ]
    for path, label in vince_files:
        if not path.exists():
            FAILURES.append("compile:" + label + " — FILE NOT FOUND")
            print("[COMPILE] " + label + " — FILE NOT FOUND")
        else:
            validate(label, path)

    # ── Step 2: Run smoke tests ───────────────────────────────────────────────
    print("\n[STEP 2] Smoke tests — tests/test_b2_api.py")
    test_path = ROOT / "tests" / "test_b2_api.py"
    if not test_path.exists():
        FAILURES.append("smoke_tests — test file not found")
        print("[TESTS]  tests/test_b2_api.py — NOT FOUND")
    else:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        print(result.stdout)
        if result.returncode == 0:
            PASSES.append("smoke_tests")
            print("[TESTS]  Smoke tests — PASS")
        else:
            FAILURES.append("smoke_tests — " + result.stderr.strip()[:200])
            print("[TESTS]  Smoke tests — FAIL")
            if result.stderr:
                print(result.stderr[:500])

    # ── Step 3: Run codebase audit ────────────────────────────────────────────
    print("\n[STEP 3] Codebase audit — vince/audit.py")
    try:
        from vince.audit import run_audit
        findings = run_audit(print_results=True)
        n_crit = sum(1 for f in findings if f.severity == "CRITICAL")
        n_warn = sum(1 for f in findings if f.severity == "WARNING")
        PASSES.append("audit:ran (" + str(len(findings)) + " findings)")
        if n_crit > 0:
            print("\n[AUDIT]  " + str(n_crit) + " CRITICAL findings above require attention.")
        if n_warn > 0:
            print("[AUDIT]  " + str(n_warn) + " WARNING findings above are advisory.")
    except Exception as e:
        FAILURES.append("audit:run_audit — " + str(e))
        print("[AUDIT]  FAIL: " + str(e))

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 64)
    print("B2 VALIDATION SUMMARY")
    print("  PASS: " + str(len(PASSES)))
    print("  FAIL: " + str(len(FAILURES)))

    if FAILURES:
        print("\nFAILURES:")
        for f in FAILURES:
            print("  - " + f)
        print("=" * 64)
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED — B2 is ready.")
        print("Next: run the strategy analysis report, fix strategy, then build B1.")
        print("=" * 64)
        sys.exit(0)


if __name__ == "__main__":
    main()

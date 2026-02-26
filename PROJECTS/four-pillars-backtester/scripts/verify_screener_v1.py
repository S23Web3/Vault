"""
Syntax verification for Screener v1 build.
Run FIRST after build, before running screener or tests.
Run: python scripts/verify_screener_v1.py
From: C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester
"""
import sys
import ast
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    ROOT / "utils" / "screener_engine.py",
    ROOT / "scripts" / "screener_v1.py",
    ROOT / "tests" / "test_screener_engine.py",
]


def check(path: Path) -> bool:
    """Run py_compile and ast.parse on path. Return True if both pass."""
    if not path.exists():
        print("  MISSING: " + str(path))
        return False
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        print("  SYNTAX FAIL: " + path.name + " -- " + str(e))
        return False
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        print(
            "  AST FAIL: " + path.name
            + " line " + str(e.lineno) + ": " + str(e.msg)
        )
        return False
    print("  OK: " + path.name)
    return True


def main() -> None:
    """Check all screener build files."""
    print("=== Screener v1 Syntax Verification ===")
    errors = []
    for p in FILES:
        if not check(p):
            errors.append(p.name)
    print()
    if errors:
        print("BUILD FAILED -- syntax errors in: " + ", ".join(errors))
        sys.exit(1)
    print("BUILD OK -- all 3 files compile clean")
    print()
    print("Next steps:")
    print("  1. Run tests:    python tests/test_screener_engine.py")
    print("  2. Run screener: streamlit run scripts/screener_v1.py")


if __name__ == "__main__":
    main()

"""
Build/validate script for visualize_v4_layers.py.
Checks file existence, runs py_compile and ast.parse, reports BUILD OK or FAILED.

Note: visualize_v4_layers.py was written directly (Write tool) because the output
contains embedded newlines in annotation strings that cannot safely be triple-quoted
inside a build script (Python skill rule: abandoned build-script pattern for this case).
This script validates the written file.

Run: python scripts/build_visualize_v4_layers.py
"""
import ast
import py_compile
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
SCRIPTS    = ROOT / "scripts"
TARGET     = SCRIPTS / "visualize_v4_layers.py"


def validate_output(path):
    """Run py_compile then ast.parse on a .py file; return True only if both pass."""
    path_str = str(path)
    try:
        py_compile.compile(path_str, doraise=True)
        print("  SYNTAX OK: " + path_str)
    except py_compile.PyCompileError as exc:
        print("  SYNTAX ERROR: " + str(exc))
        return False
    try:
        source = Path(path_str).read_text(encoding="utf-8")
        ast.parse(source, filename=path_str)
        print("  AST OK:    " + path_str)
    except SyntaxError as exc:
        print("  AST ERROR in " + path_str + " line " + str(exc.lineno) + ": " + str(exc.msg))
        return False
    return True


def main():
    """Entry point: validate TARGET exists and passes static analysis."""
    print("=" * 60)
    print("build_visualize_v4_layers.py")
    print("Target: " + str(TARGET))
    print("=" * 60)

    if not TARGET.exists():
        print("ERROR: Target file not found.")
        print("  Expected: " + str(TARGET))
        print("  The file was not generated. Check the Write tool step.")
        sys.exit(1)

    print("Validating: " + TARGET.name)
    ok = validate_output(TARGET)

    print("-" * 60)
    if ok:
        print("BUILD OK -- " + TARGET.name + " compile clean")
        print("Run: python " + str(TARGET))
    else:
        print("BUILD FAILED -- syntax errors in " + TARGET.name)
        sys.exit(1)


if __name__ == "__main__":
    main()

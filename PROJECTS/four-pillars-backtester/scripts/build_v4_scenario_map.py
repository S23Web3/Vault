# -*- coding: utf-8 -*-
"""
Build script for V4 scenario map visualizer.
Validates syntax via py_compile + ast.parse.

Run: python scripts/build_v4_scenario_map.py
"""
import ast
import py_compile
import sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
TARGET = ROOT / "scripts" / "visualize_v4_scenario_map.py"


def validate_output(path):
    """Run py_compile then ast.parse on a .py file; return True only if both pass."""
    path_str = str(path)
    try:
        py_compile.compile(path_str, doraise=True)
        print("  SYNTAX OK: " + path_str)
    except py_compile.PyCompileError as exc:
        print("  SYNTAX FAIL: " + str(exc))
        return False

    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=path_str)
        print("  AST OK:    " + path_str)
    except SyntaxError as exc:
        print("  AST FAIL:  " + str(exc))
        return False

    return True


def main():
    banner = "build_v4_scenario_map.py"
    print("=" * 60)
    print(banner)
    print("Target: " + str(TARGET))
    print("=" * 60)

    if not TARGET.exists():
        print("ERROR: target not found -- " + str(TARGET))
        sys.exit(1)

    print("Validating: " + TARGET.name)
    ok = validate_output(TARGET)
    print("-" * 60)

    if ok:
        print("BUILD OK -- " + TARGET.name + " compile clean")
        print("Run: python " + str(TARGET))
    else:
        print("BUILD FAILED -- " + TARGET.name)
        sys.exit(1)


if __name__ == "__main__":
    main()

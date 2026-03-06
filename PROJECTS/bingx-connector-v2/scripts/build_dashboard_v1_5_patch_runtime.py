"""
Build script: BingX Dashboard v1.5 — Runtime Error Fix
Date: 2026-03-05

Fixes:
  - Patch 1: store-bot-status dcc.Store definition (line 1141)
    OLD: dcc.Store(id='store-bot-status', data=[]),
    NEW: dcc.Store(id='store-bot-status', storage_type='memory'),

Base file: C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\bingx-live-dashboard-v1-5.py
"""

import py_compile
import sys
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector")
TARGET = BASE / "bingx-live-dashboard-v1-5.py"

ERRORS = []


def patch_file():
    """Apply safe_replace patches to dashboard v1.5."""
    content = TARGET.read_text(encoding="utf-8")
    original = content

    # --- Patch 1: Fix store-bot-status definition ---
    old = "dcc.Store(id='store-bot-status', data=[]),"
    new = "dcc.Store(id='store-bot-status', storage_type='memory'),"
    if old not in content:
        ERRORS.append("Patch 1 FAILED: old string not found in file")
        return
    count = content.count(old)
    if count != 1:
        ERRORS.append("Patch 1 FAILED: expected 1 occurrence, found " + str(count))
        return
    content = content.replace(old, new)
    print("Patch 1 applied: store-bot-status data=[] -> storage_type='memory'")

    if content == original:
        ERRORS.append("No changes made -- file unchanged")
        return

    TARGET.write_text(content, encoding="utf-8")
    print("File written: " + str(TARGET))


def validate():
    """Run py_compile on the patched file."""
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("py_compile PASS: " + str(TARGET))
    except py_compile.PyCompileError as e:
        ERRORS.append("py_compile FAILED: " + str(e))


def main():
    """Run all patches and validation."""
    print("=" * 60)
    print("BingX Dashboard v1.5 -- Runtime Error Fix")
    print("=" * 60)
    print()

    if not TARGET.exists():
        print("ERROR: Target file not found: " + str(TARGET))
        sys.exit(1)

    patch_file()
    if ERRORS:
        print()
        print("ERRORS:")
        for err in ERRORS:
            print("  - " + err)
        sys.exit(1)

    print()
    validate()
    if ERRORS:
        print()
        print("ERRORS:")
        for err in ERRORS:
            print("  - " + err)
        sys.exit(1)

    print()
    print("=" * 60)
    print("ALL PATCHES APPLIED + VALIDATED")
    print("=" * 60)
    print()
    print("Run command:")
    print('  python "' + str(TARGET) + '"')


if __name__ == "__main__":
    main()

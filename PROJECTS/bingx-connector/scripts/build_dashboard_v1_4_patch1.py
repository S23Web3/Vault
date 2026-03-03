"""
build_dashboard_v1_4_patch1.py

Fix: CB-T3 (poll_bot_running) missing prevent_initial_call='initial_duplicate'.
Dash requires prevent_initial_call to be set when allow_duplicate=True is used.

Run: python scripts/build_dashboard_v1_4_patch1.py
"""
import py_compile
import sys
from datetime import datetime
from pathlib import Path

BOT_ROOT = Path(__file__).resolve().parent.parent
TARGET   = BOT_ROOT / "bingx-live-dashboard-v1-4.py"

ERRORS = []


def safe_replace(text, old, new, label):
    """Replace old with new in text. Record error if old not found."""
    if old not in text:
        ERRORS.append(label + ": anchor not found")
        print("  FAIL: " + label)
        return text
    print("  PASS: " + label)
    return text.replace(old, new, 1)


def compile_check(path):
    """py_compile the patched file; record error on failure."""
    try:
        py_compile.compile(str(path), doraise=True)
        print("  SYNTAX OK: " + path.name)
    except py_compile.PyCompileError as e:
        ERRORS.append("syntax error: " + str(e))
        print("  SYNTAX FAIL: " + str(e))


# ---------------------------------------------------------------------------
# Patch
# ---------------------------------------------------------------------------

P1_OLD = '''    Input('status-interval', 'n_intervals'),
)
def poll_bot_running(n_intervals):
    """Check bot process status on each 5s tick; update button state."""'''

P1_NEW = '''    Input('status-interval', 'n_intervals'),
    prevent_initial_call='initial_duplicate',
)
def poll_bot_running(n_intervals):
    """Check bot process status on each 5s tick; update button state."""'''


def main():
    """Apply CB-T3 prevent_initial_call fix to bingx-live-dashboard-v1-4.py."""
    print("=" * 60)
    print("Patch 1: v1-4 CB-T3 prevent_initial_call fix")
    print("=" * 60)

    if not TARGET.exists():
        print("FAIL: target not found: " + str(TARGET))
        sys.exit(1)

    # Guard: back up before patching
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_suffix("." + ts + ".bak.py")
    import shutil
    shutil.copy2(TARGET, bak)
    print("  Backup: " + str(bak))

    text = TARGET.read_text(encoding="utf-8")
    print("Read: " + str(TARGET) + " (" + str(len(text)) + " chars)")
    print()

    print("Applying patches...")
    text = safe_replace(text, P1_OLD, P1_NEW, "CB-T3-prevent-initial-call")

    print()
    TARGET.write_text(text, encoding="utf-8")
    print("Wrote: " + str(TARGET))
    print()
    compile_check(TARGET)

    print()
    print("=" * 60)
    if ERRORS:
        print("RESULT: FAIL")
        for e in ERRORS:
            print("  ERROR: " + e)
        sys.exit(1)
    else:
        print("RESULT: PASS")
        print()
        print("Next step:")
        print('  python "' + str(TARGET) + '"')


if __name__ == "__main__":
    main()

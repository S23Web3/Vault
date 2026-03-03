"""
build_dashboard_v1_3_patch6.py

Patch 6: Override Dash 2.x CSS custom properties at :root to fix white
backgrounds on date pickers, dropdown menus, and calendar popups.

Root cause: Dash 2.x injects CSS variables into :root via dcc.css.
Class-level !important cannot override CSS variables. Must override at :root.

Files changed:
  - assets/dashboard.css  (append :root block)

No Python changes.

Run: python scripts/build_dashboard_v1_3_patch6.py
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BOT_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = BOT_ROOT / "assets" / "dashboard.css"

# ---------------------------------------------------------------------------
# Guard string -- if this is already in the CSS, patch is already applied
# ---------------------------------------------------------------------------
GUARD = "--Dash-Fill-Inverse-Strong"

# ---------------------------------------------------------------------------
# CSS block to append
# ---------------------------------------------------------------------------
CSS_BLOCK = """
/* === Patch 6: Override Dash 2.x :root CSS variables (dark theme) === */
:root {
    --Dash-Fill-Inverse-Strong: #21262d !important;
    --Dash-Fill-Inverse-Weak: rgba(33, 38, 45, 0.9) !important;
    --Dash-Fill-Interactive-Weak: rgba(33, 38, 45, 0.5) !important;
    --Dash-Fill-Primary-Hover: rgba(88, 166, 255, 0.1) !important;
    --Dash-Fill-Primary-Active: rgba(88, 166, 255, 0.2) !important;
    --Dash-Text-Primary: #c9d1d9 !important;
    --Dash-Text-Weak: #8b949e !important;
    --Dash-Stroke-Strong: #484f58 !important;
    --Dash-Stroke-Weak: rgba(72, 79, 88, 0.3) !important;
    --Dash-Fill-Interactive-Strong: #58a6ff !important;
    --Dash-Text-Disabled: #484f58 !important;
}
"""

ERRORS = []


def main():
    """Apply patch 6 to dashboard.css."""
    print("=" * 60)
    print("Patch 6: Dash :root CSS variable override")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Check CSS file exists
    # ------------------------------------------------------------------
    if not CSS_PATH.exists():
        print("FAIL: CSS file not found: " + str(CSS_PATH))
        ERRORS.append("CSS file not found")
        report()
        return

    css_text = CSS_PATH.read_text(encoding="utf-8")
    print("CSS file: " + str(CSS_PATH))
    print("CSS size: " + str(len(css_text)) + " chars, " + str(css_text.count("\n")) + " lines")

    # ------------------------------------------------------------------
    # 2. Guard check
    # ------------------------------------------------------------------
    if GUARD in css_text:
        print("\nSKIP: Patch 6 already applied (guard string found: " + GUARD + ")")
        print("\nResult: ALREADY APPLIED -- no changes made")
        return

    print("Guard check: not found -- patch not yet applied")

    # ------------------------------------------------------------------
    # 3. Create timestamped backup
    # ------------------------------------------------------------------
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = CSS_PATH.parent / ("dashboard." + ts + ".bak.css")
    shutil.copy2(CSS_PATH, backup_path)
    print("Backup: " + str(backup_path))

    # ------------------------------------------------------------------
    # 4. Append :root block
    # ------------------------------------------------------------------
    new_css = css_text + CSS_BLOCK
    CSS_PATH.write_text(new_css, encoding="utf-8")
    print("Appended :root block to " + str(CSS_PATH))

    # ------------------------------------------------------------------
    # 5. Verify
    # ------------------------------------------------------------------
    verify_text = CSS_PATH.read_text(encoding="utf-8")
    if GUARD not in verify_text:
        ERRORS.append("Verify failed: guard string not found after write")
        print("FAIL: guard string not found after write")
    else:
        print("Verify: guard string present -- PASS")

    new_lines = verify_text.count("\n")
    old_lines = css_text.count("\n")
    print("Lines: " + str(old_lines) + " -> " + str(new_lines) + " (+" + str(new_lines - old_lines) + ")")

    report()


def report():
    """Print final pass/fail summary."""
    print("\n" + "=" * 60)
    if ERRORS:
        print("RESULT: FAIL")
        for e in ERRORS:
            print("  ERROR: " + e)
        sys.exit(1)
    else:
        print("RESULT: PASS")
        print("")
        print("Next steps:")
        print("  1. Restart dashboard:")
        print('     python "' + str(BOT_ROOT / "bingx-live-dashboard-v1-3.py") + '"')
        print("  2. Open date picker or dropdown -- should be dark")


if __name__ == "__main__":
    main()

"""
Build script: BingX Dashboard v1.5 -- Trades CSV Fix + Faster Refresh
Date: 2026-03-05

Fixes:
  P1: load_trades() fails silently on trades.csv because the bot writes
      18 columns (three-stage fields) but the CSV header has only 12.
      pd.read_csv() throws ParserError, caught by bare except -> empty DataFrame.
      Fix: use csv.reader to handle variable column count, truncate to header.
      This fixes BOTH History and Analytics tabs showing no data.

  P2: refresh-interval is 60s -- positions/mark prices only update once per
      minute. Reduce to 15s for near-real-time position tracking.

Base: C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\bingx-live-dashboard-v1-5.py
"""

import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector")
TARGET = BASE / "bingx-live-dashboard-v1-5.py"

ERRORS = []
PATCHES_APPLIED = []


def safe_replace(content, old, new, label):
    """Replace exactly one occurrence of old with new. Appends to ERRORS on failure."""
    if old not in content:
        ERRORS.append(label + " FAILED: old string not found")
        return content
    count = content.count(old)
    if count != 1:
        ERRORS.append(label + " FAILED: expected 1 occurrence, found " + str(count))
        return content
    content = content.replace(old, new)
    PATCHES_APPLIED.append(label)
    print("  " + label + " applied")
    return content


def patch_file():
    """Apply patches to dashboard v1.5."""
    content = TARGET.read_text(encoding="utf-8")

    # ---------------------------------------------------------------
    # P1: Fix load_trades() to handle variable column count in CSV.
    #     Bot writes 18 columns (three-stage fields) but header has 12.
    #     Use csv.reader, truncate each row to header length.
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "def load_trades() -> pd.DataFrame:\n"
        "    \"\"\"Load trades.csv. Returns DataFrame sorted newest-first, or empty DataFrame.\"\"\"\n"
        "    if not TRADES_PATH.exists():\n"
        "        return pd.DataFrame()\n"
        "    try:\n"
        "        df = pd.read_csv(TRADES_PATH)\n"
        "        df[\"timestamp\"] = pd.to_datetime(df[\"timestamp\"], utc=True, errors=\"coerce\")\n"
        "        df[\"entry_time\"] = pd.to_datetime(df[\"entry_time\"], utc=True, errors=\"coerce\")\n"
        "        df[\"pnl_net\"] = pd.to_numeric(df[\"pnl_net\"], errors=\"coerce\")\n"
        "        df[\"entry_price\"] = pd.to_numeric(df[\"entry_price\"], errors=\"coerce\")\n"
        "        df[\"exit_price\"] = pd.to_numeric(df[\"exit_price\"], errors=\"coerce\")\n"
        "        # Filter to bot trades only (bot started 2026-02-27, prior = demo phases)\n"
        "        cutoff = pd.Timestamp(\"2026-02-27\", tz=\"UTC\")\n"
        "        df = df[df[\"timestamp\"] >= cutoff]\n"
        "        return df.sort_values(\"timestamp\", ascending=False).reset_index(drop=True)\n"
        "    except Exception:\n"
        "        return pd.DataFrame()",
        "def load_trades() -> pd.DataFrame:\n"
        "    \"\"\"Load trades.csv. Returns DataFrame sorted newest-first, or empty DataFrame.\"\"\"\n"
        "    if not TRADES_PATH.exists():\n"
        "        return pd.DataFrame()\n"
        "    try:\n"
        "        import csv as _csv\n"
        "        rows = []\n"
        "        with open(TRADES_PATH, 'r', encoding='utf-8', newline='') as f:\n"
        "            reader = _csv.reader(f)\n"
        "            header = next(reader)\n"
        "            n = len(header)\n"
        "            for row in reader:\n"
        "                if len(row) >= n:\n"
        "                    rows.append(row[:n])\n"
        "        if not rows:\n"
        "            return pd.DataFrame()\n"
        "        df = pd.DataFrame(rows, columns=header)\n"
        "        df[\"timestamp\"] = pd.to_datetime(df[\"timestamp\"], utc=True, errors=\"coerce\")\n"
        "        df[\"entry_time\"] = pd.to_datetime(df[\"entry_time\"], utc=True, errors=\"coerce\")\n"
        "        df[\"pnl_net\"] = pd.to_numeric(df[\"pnl_net\"], errors=\"coerce\")\n"
        "        df[\"entry_price\"] = pd.to_numeric(df[\"entry_price\"], errors=\"coerce\")\n"
        "        df[\"exit_price\"] = pd.to_numeric(df[\"exit_price\"], errors=\"coerce\")\n"
        "        # Filter to bot trades only (bot started 2026-02-27, prior = demo phases)\n"
        "        cutoff = pd.Timestamp(\"2026-02-27\", tz=\"UTC\")\n"
        "        df = df[df[\"timestamp\"] >= cutoff]\n"
        "        LOG.info(\"Trades loaded: %d total, %d after cutoff\", len(rows), len(df))\n"
        "        return df.sort_values(\"timestamp\", ascending=False).reset_index(drop=True)\n"
        "    except Exception as e:\n"
        "        LOG.error(\"load_trades failed: %s\", e, exc_info=True)\n"
        "        return pd.DataFrame()",
        "P1-fix-trades-csv-loading",
    )

    # ---------------------------------------------------------------
    # P2: Reduce refresh-interval from 60s to 15s for faster position
    #     updates (mark prices, unrealized PnL, distance to SL).
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "dcc.Interval(id='refresh-interval', interval=60_000, n_intervals=0),",
        "dcc.Interval(id='refresh-interval', interval=15_000, n_intervals=0),",
        "P2-refresh-interval-15s",
    )

    TARGET.write_text(content, encoding="utf-8")
    print("\nFile written: " + str(TARGET))


def validate():
    """Run py_compile on the patched file."""
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("py_compile PASS: " + str(TARGET))
    except py_compile.PyCompileError as e:
        ERRORS.append("py_compile FAILED: " + str(e))


def main():
    """Run all patches and validation."""
    print("=" * 70)
    print("BingX Dashboard v1.5 -- Trades CSV Fix + Faster Refresh")
    print("=" * 70)
    print()

    if not TARGET.exists():
        print("ERROR: Target file not found: " + str(TARGET))
        sys.exit(1)

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(TARGET.stem + ".trades." + ts + ".bak.py")
    shutil.copy2(TARGET, backup)
    print("Backup: " + str(backup))
    print()

    print("Applying patches...")
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
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("  Patches applied: " + str(len(PATCHES_APPLIED)))
    for p in PATCHES_APPLIED:
        print("    + " + p)
    print("  Backup: " + str(backup))
    print()
    print("  P1: load_trades() uses csv.reader for variable column count")
    print("      trades.csv has 12-col header but 18-col rows (three-stage fields)")
    print("      Fixes both History and Analytics tabs")
    print()
    print("  P2: refresh-interval 60s -> 15s (faster position updates)")
    print()
    print("Run command:")
    print('  python "' + str(TARGET) + '"')


if __name__ == "__main__":
    main()

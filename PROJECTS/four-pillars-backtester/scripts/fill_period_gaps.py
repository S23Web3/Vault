"""
Fill the 41-day gap (2025-01-01 to 2025-02-11) for all coins in data/periods/2024-2025/.
Fetches from Bybit v5 API, appends to existing period parquet, deduplicates.

Resumable: tracks completed coins in data/periods/_gap_fill_progress.json.
Re-run safely -- skips already-filled coins.

Run: python scripts/fill_period_gaps.py
Dry run: python scripts/fill_period_gaps.py --dry-run
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.fetcher import BybitFetcher

PERIOD_DIR = ROOT / "data" / "periods" / "2024-2025"
CACHE_DIR = ROOT / "data" / "cache"
PROGRESS_FILE = ROOT / "data" / "periods" / "_gap_fill_progress.json"
TMP_DIR = ROOT / "data" / "tmp_gap_fetch"

# Gap boundaries
GAP_START = datetime(2025, 1, 1, tzinfo=timezone.utc)
GAP_END = datetime(2025, 2, 11, tzinfo=timezone.utc)
GAP_START_MS = int(GAP_START.timestamp() * 1000)
GAP_END_MS = int(GAP_END.timestamp() * 1000)
TWO_DAYS_MS = 2 * 24 * 60 * 60 * 1000


def load_progress():
    """Load set of already-completed symbols from progress file."""
    if PROGRESS_FILE.exists():
        return set(json.loads(PROGRESS_FILE.read_text()))
    return set()


def save_progress(completed):
    """Save completed symbol set to progress file."""
    PROGRESS_FILE.write_text(json.dumps(sorted(completed), indent=2))


def find_gapped_coins():
    """Find coins in 2024-2025 that have a gap to cache > 2 days."""
    suffix = "_1m.parquet"
    gapped = []

    if not PERIOD_DIR.exists():
        print("ERROR: 2024-2025 period directory not found")
        return []

    for fp in sorted(PERIOD_DIR.glob(f"*{suffix}")):
        sym = fp.name.replace(suffix, "")
        cache_file = CACHE_DIR / f"{sym}{suffix}"

        if not cache_file.exists():
            continue

        try:
            p2_ts = pd.read_parquet(fp, columns=["timestamp"])["timestamp"]
            c_ts = pd.read_parquet(cache_file, columns=["timestamp"])["timestamp"]
            p2_end = int(pd.to_numeric(p2_ts).max())
            c_start = int(pd.to_numeric(c_ts).min())

            if c_start - p2_end > TWO_DAYS_MS:
                gapped.append(sym)
        except Exception:
            pass

    return gapped


def fill_one_coin(fetcher, symbol):
    """Fetch gap data for one coin, merge into period file."""
    period_file = PERIOD_DIR / f"{symbol}_1m.parquet"

    # Fetch gap data to tmp
    gap_df = fetcher.fetch_symbol(symbol, GAP_START, GAP_END, force=True)

    if gap_df is None or len(gap_df) == 0:
        return 0, "no data from API"

    # Read existing period data
    existing = pd.read_parquet(period_file)
    before_bars = len(existing)

    # Merge
    combined = pd.concat([existing, gap_df], ignore_index=True)
    combined["timestamp"] = pd.to_numeric(combined["timestamp"], errors="coerce")
    combined = (
        combined.drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    if "datetime" not in combined.columns:
        combined["datetime"] = pd.to_datetime(
            combined["timestamp"], unit="ms", utc=True
        )

    # Save
    combined.to_parquet(period_file, index=False)
    added = len(combined) - before_bars

    return added, "ok"


def main():
    """Run gap fill for all coins with the Jan 1 - Feb 11 2025 gap."""
    dry_run = "--dry-run" in sys.argv
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print("=" * 80)
    print(f"FILL PERIOD GAPS -- 2025-01-01 to 2025-02-11")
    print(f"Timestamp: {ts}")
    if dry_run:
        print("MODE: DRY RUN (no fetching)")
    print("=" * 80)

    # Find gapped coins
    gapped = find_gapped_coins()
    completed = load_progress()
    remaining = [s for s in gapped if s not in completed]

    print(f"\n  Total gapped coins: {len(gapped)}")
    print(f"  Already filled:     {len(completed)}")
    print(f"  Remaining:          {len(remaining)}")

    if not remaining:
        print("\n  All gaps already filled. Run validate_coin_data.py to confirm.")
        return

    # Estimate: 60 pages/coin @ 0.2s + 1s cooldown between coins
    est_pages = len(remaining) * 60
    est_minutes = (est_pages * 0.25 + len(remaining) * 1.0) / 60
    print(f"  Estimated time:     ~{est_minutes:.0f} minutes")
    print(f"  Estimated API calls: ~{est_pages:,}")

    if dry_run:
        print(f"\n  Would fetch for these {len(remaining)} coins:")
        for s in remaining[:20]:
            print(f"    {s}")
        if len(remaining) > 20:
            print(f"    ... and {len(remaining) - 20} more")
        return

    # Confirm
    print(f"\n  Proceed? (yes/no): ", end="", flush=True)
    resp = input().strip().lower()
    if resp != "yes":
        print("  Cancelled.")
        return

    # Setup fetcher with tmp dir for intermediate files
    # 0.2s between pages = 5 req/s, well under Bybit's 10 req/s limit
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    fetcher = BybitFetcher(cache_dir=str(TMP_DIR), rate_limit=0.2)

    # Process
    start_time = time.time()
    success = 0
    errors = 0
    total_bars_added = 0

    for i, sym in enumerate(remaining, 1):
        print(f"  [{i}/{len(remaining)}] {sym}...", end=" ", flush=True)

        try:
            added, status = fill_one_coin(fetcher, sym)
            if status == "ok":
                success += 1
                total_bars_added += added
                completed.add(sym)
                save_progress(completed)
                print(f"+{added:,} bars")
            else:
                errors += 1
                print(f"SKIP ({status})")
        except Exception as e:
            errors += 1
            print(f"ERROR ({e})")

        # Cooldown between coins to avoid sustained rate pressure
        time.sleep(1.0)

        # Progress checkpoint every 5 coins
        if i % 5 == 0:
            elapsed = (time.time() - start_time) / 60
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(remaining) - i) / rate if rate > 0 else 0
            print(f"  --- Checkpoint: {i}/{len(remaining)}, "
                  f"{elapsed:.1f}min elapsed, ~{eta:.0f}min remaining ---")

    # Cleanup tmp
    import shutil
    shutil.rmtree(TMP_DIR, ignore_errors=True)

    elapsed = (time.time() - start_time) / 60

    print(f"\n{'='*80}")
    print(f"COMPLETE")
    print(f"{'='*80}")
    print(f"  Filled:       {success}/{len(remaining)}")
    print(f"  Errors:       {errors}")
    print(f"  Bars added:   {total_bars_added:,}")
    print(f"  Runtime:      {elapsed:.1f} minutes")
    print(f"\n  Run validate_coin_data.py to verify all gaps are closed.")


if __name__ == "__main__":
    main()

"""
Build script: Section B -- Data Infrastructure.
Creates results/coin_tiers.csv and data/coin_pools.json.

Run: python scripts/build_data_infra_v1.py
"""

import sys
import json
import random
import datetime
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CACHE_DIR = ROOT / "data" / "cache"
RESULTS_DIR = ROOT / "results"
POOL_FILE = ROOT / "data" / "coin_pools.json"


def step1_classify_tiers():
    """Run KMeans tier classification on all coins in data/cache/."""
    from research.coin_classifier import classify_coin_tiers

    output_path = RESULTS_DIR / "coin_tiers.csv"
    if output_path.exists():
        log.info("SKIP coin_tiers.csv (already exists)")
        import pandas as pd
        return pd.read_csv(output_path)

    log.info("Classifying coin tiers from %s ...", CACHE_DIR)
    tiers_df = classify_coin_tiers(
        parquet_dir=str(CACHE_DIR),
        timeframe="5m",
        n_clusters=4,
        output_path=str(output_path),
        verbose=True,
    )
    log.info("Saved %d coin tiers to %s", len(tiers_df), output_path)
    return tiers_df


def step2_assign_pools(tiers_df):
    """Assign coins to Pool A/B/C with 60/20/20 stratified split."""
    if POOL_FILE.exists():
        log.info("SKIP coin_pools.json (already exists -- IMMUTABLE)")
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            pools = json.load(f)
        log.info("Loaded %d existing pool assignments", len(pools.get("assignments", {})))
        return pools

    symbols = sorted(tiers_df["symbol"].tolist())
    tiers = tiers_df.set_index("symbol")["tier"].to_dict()
    n_total = len(symbols)

    log.info("Assigning %d coins to pools (60/20/20, seed=42) ...", n_total)

    # Group symbols by tier for stratified splitting
    tier_groups = defaultdict(list)
    for sym in symbols:
        tier_groups[tiers.get(sym, 0)].append(sym)

    assignments = {}
    rng = random.Random(42)

    for tier_id in sorted(tier_groups.keys()):
        group = tier_groups[tier_id]
        rng.shuffle(group)
        n = len(group)
        n_a = int(n * 0.6)
        n_b = int(n * 0.2)
        # Remainder goes to C
        for j, sym in enumerate(group):
            if j < n_a:
                assignments[sym] = "A"
            elif j < n_a + n_b:
                assignments[sym] = "B"
            else:
                assignments[sym] = "C"

    # Validate
    counts = {"A": 0, "B": 0, "C": 0}
    for pool in assignments.values():
        counts[pool] += 1

    log.info("Pool A: %d (%.1f%%)", counts["A"], 100.0 * counts["A"] / n_total)
    log.info("Pool B: %d (%.1f%%)", counts["B"], 100.0 * counts["B"] / n_total)
    log.info("Pool C: %d (%.1f%%)", counts["C"], 100.0 * counts["C"] / n_total)

    # Validate no duplicates, all assigned
    assert len(assignments) == n_total, (
        "Pool assignment count mismatch: " + str(len(assignments)) + " vs " + str(n_total)
    )
    assert len(set(assignments.keys())) == n_total, "Duplicate symbols in pool assignments"

    # Build output JSON
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    pools = {
        "frozen_date": ts,
        "seed": 42,
        "split_ratios": {"A": 0.60, "B": 0.20, "C": 0.20},
        "total_coins": n_total,
        "pool_counts": counts,
        "tier_counts": {str(k): len(v) for k, v in sorted(tier_groups.items())},
        "assignments": dict(sorted(assignments.items())),
    }

    # Save
    POOL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(pools, f, indent=2)
    log.info("Saved pool assignments to %s", POOL_FILE)

    # Validate JSON round-trip
    with open(POOL_FILE, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded["assignments"]) == n_total, "JSON round-trip failed"
    log.info("JSON round-trip validated: %d assignments", n_total)

    return pools


def main():
    """Build Section B data infrastructure."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info("=== Section B: Data Infrastructure ===")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Classify tiers
    tiers_df = step1_classify_tiers()
    log.info("Tier classification: %d coins", len(tiers_df))

    # Step 2: Assign pools
    pools = step2_assign_pools(tiers_df)

    # Summary
    ts2 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info("[%s] BUILD OK -- data infrastructure complete", ts2)
    log.info("  - results/coin_tiers.csv (%d coins)", len(tiers_df))
    log.info("  - data/coin_pools.json (%d assignments)", pools["total_coins"])


if __name__ == "__main__":
    main()

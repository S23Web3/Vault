
"""Debug script for coin_classifier.
Run: python scripts/debug_coin_classifier.py
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def make_ohlcv(n=300, price=0.01, vol_mult=0.01, seed=42):
    """Generate synthetic OHLCV DataFrame."""
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, price * vol_mult, n))
    close = np.clip(close, price * 0.1, price * 10)
    df = pd.DataFrame({
        "open":   close * rng.uniform(0.999, 1.001, n),
        "high":   close * rng.uniform(1.000, 1.005, n),
        "low":    close * rng.uniform(0.995, 1.000, n),
        "close":  close,
        "volume": rng.integers(1_000_000, 10_000_000, n).astype(float),
    })
    df.index = pd.date_range("2025-01-01", periods=n, freq="1min")
    df.index.name = "datetime"
    return df


def main():
    """Run debug checks for coin_classifier module."""
    from research.coin_classifier import compute_coin_features, classify_coin_tiers

    log.info("=== Debug: coin_classifier ===")

    # Test feature computation
    df = make_ohlcv(n=300, price=0.001, vol_mult=0.01)
    features = compute_coin_features(df, "TESTCOIN")
    log.info("Features: %s", features)
    assert features["avg_atr_pct"] > 0, "avg_atr_pct should be positive"
    assert features["avg_bbw_raw"] > 0, "avg_bbw_raw should be positive"
    log.info("Feature assertions PASS")

    # Test on real parquets if available
    cache_dir = ROOT / "data" / "cache"
    parquets = sorted(cache_dir.glob("*_1m.parquet"))[:10]
    if parquets:
        log.info("Testing on %d real parquets from cache", len(parquets))
        result = classify_coin_tiers(str(cache_dir), timeframe="5m", verbose=True)
        log.info("Tiers computed: %d coins", len(result))
        log.info("\n" + result.to_string())
        out_path = ROOT / "results" / "debug_coin_tiers.csv"
        out_path.parent.mkdir(exist_ok=True)
        result.to_csv(out_path, index=False)
        log.info("Saved: %s", out_path)
    else:
        log.warning("No real parquets found at %s -- skipping real data test", cache_dir)

    log.info("=== Done ===")


if __name__ == "__main__":
    main()

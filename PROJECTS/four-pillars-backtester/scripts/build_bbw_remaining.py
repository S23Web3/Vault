"""
Build script: BBW Remaining -- Coin Classifier, Ollama Review, CLI.

Creates 9 files:
  1. research/coin_classifier.py
  2. tests/test_coin_classifier.py
  3. scripts/debug_coin_classifier.py
  4. research/bbw_ollama_review.py
  5. tests/test_bbw_ollama_review.py
  6. scripts/debug_bbw_ollama_review.py
  7. scripts/run_bbw_simulator.py
  8. tests/test_run_bbw_simulator.py
  9. scripts/debug_run_bbw_simulator.py

Run: python scripts/build_bbw_remaining.py
"""

import sys
import py_compile
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

print("=" * 70)
print("BBW Remaining Build -- " + ts)
print("=" * 70)

TARGETS = {
    "research/coin_classifier.py":          ROOT / "research" / "coin_classifier.py",
    "tests/test_coin_classifier.py":        ROOT / "tests" / "test_coin_classifier.py",
    "scripts/debug_coin_classifier.py":     ROOT / "scripts" / "debug_coin_classifier.py",
    "research/bbw_ollama_review.py":        ROOT / "research" / "bbw_ollama_review.py",
    "tests/test_bbw_ollama_review.py":      ROOT / "tests" / "test_bbw_ollama_review.py",
    "scripts/debug_bbw_ollama_review.py":   ROOT / "scripts" / "debug_bbw_ollama_review.py",
    "scripts/run_bbw_simulator.py":         ROOT / "scripts" / "run_bbw_simulator.py",
    "tests/test_run_bbw_simulator.py":      ROOT / "tests" / "test_run_bbw_simulator.py",
    "scripts/debug_run_bbw_simulator.py":   ROOT / "scripts" / "debug_run_bbw_simulator.py",
}

for name, path in TARGETS.items():
    if path.exists():
        print("FATAL: " + name + " already exists. Remove before running.")
        sys.exit(1)

(ROOT / "research").mkdir(exist_ok=True)
(ROOT / "research" / "__init__.py").touch()


def write_and_compile(filepath, content, label):
    """Write content to filepath and syntax-check; return True on success."""
    filepath.write_text(content, encoding="utf-8")
    try:
        py_compile.compile(str(filepath), doraise=True)
        print("  OK   " + label + " -- written + syntax OK")
        return True
    except py_compile.PyCompileError as e:
        print("  FAIL " + label + " -- SYNTAX ERROR:")
        print("       " + str(e))
        return False


SYNTAX_FAILS = []

# =============================================================================
# FILE 1: research/coin_classifier.py
# =============================================================================

COIN_CLASSIFIER = '''
"""Layer 4c: Coin Classifier -- KMeans volatility tier assignment.

Input: Parquet directory containing SYMBOL_TIMEFRAME.parquet files.
Output: DataFrame with [symbol, tier, avg_atr_pct, avg_bbw_raw,
        avg_daily_range, avg_base_vol, vol_of_vol] columns.

Tiers sorted by avg_atr_pct: 0=calmest, N-1=wildest.
Imported by: scripts/run_bbw_simulator.py
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

REQUIRED_COLS = ["open", "high", "low", "close"]
BB_PERIOD = 20
BB_STD = 2.0
ATR_PERIOD = 14
SILHOUETTE_K_RANGE = (3, 5)


def _compute_atr(df, period=ATR_PERIOD):
    """Wilder-smoothed ATR series."""
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def _compute_bb_width(df, period=BB_PERIOD, n_std=BB_STD):
    """Bollinger Band Width: (upper - lower) / middle."""
    close = df["close"].astype(float)
    mid = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    upper = mid + n_std * std
    lower = mid - n_std * std
    denom = mid.replace(0, np.nan)
    return (upper - lower) / denom


def _resample_ohlcv(df, timeframe):
    """Resample 1m OHLCV DataFrame to target timeframe string."""
    freq_map = {"5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}
    freq = freq_map.get(timeframe, timeframe)
    if "datetime" not in df.columns:
        if df.index.name == "datetime":
            df = df.reset_index()
    df = df.set_index("datetime")
    vol_col = "base_vol" if "base_vol" in df.columns else (
        "volume" if "volume" in df.columns else None
    )
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if vol_col:
        agg[vol_col] = "sum"
    resampled = df.resample(freq).agg(agg).dropna()
    return resampled.reset_index()


def compute_coin_features(df, symbol):
    """Compute 5 volatility features from OHLCV DataFrame for one coin.

    Returns dict: symbol, avg_atr_pct, avg_bbw_raw, avg_daily_range,
    avg_base_vol, vol_of_vol.
    """
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise ValueError("Missing column " + col + " for " + symbol)
    close = df["close"].astype(float)
    if close.empty or close.isna().all():
        raise ValueError("No valid close prices for " + symbol)
    atr = _compute_atr(df)
    avg_atr_pct = float((atr / close.replace(0, np.nan)).dropna().mean() * 100)
    bbw = _compute_bb_width(df)
    avg_bbw_raw = float(bbw.dropna().mean())
    high_f = df["high"].astype(float)
    low_f = df["low"].astype(float)
    daily_range = (high_f - low_f) / close.replace(0, np.nan)
    avg_daily_range = float(daily_range.dropna().mean() * 100)
    vol_of_vol = float(daily_range.dropna().std() * 100)
    vol_col = (
        "base_vol" if "base_vol" in df.columns
        else "volume" if "volume" in df.columns
        else None
    )
    avg_base_vol = float(df[vol_col].astype(float).dropna().mean()) if vol_col else 0.0
    return {
        "symbol": symbol,
        "avg_atr_pct": avg_atr_pct,
        "avg_bbw_raw": avg_bbw_raw,
        "avg_daily_range": avg_daily_range,
        "avg_base_vol": avg_base_vol,
        "vol_of_vol": vol_of_vol,
    }


def classify_coin_tiers(parquet_dir, timeframe="5m", n_clusters=4,
                        output_path=None, verbose=False):
    """Assign KMeans volatility tier to each coin in parquet_dir.

    Loads all *.parquet files, computes 5 features per coin, runs KMeans
    with silhouette-selected k in range 3-5. Tiers sorted by avg_atr_pct:
    0=calmest, N-1=wildest. Saves CSV if output_path given.
    """
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        raise ImportError(
            "scikit-learn is required for coin_classifier. "
            "Install with: pip install scikit-learn"
        ) from e

    parquet_dir = Path(parquet_dir)
    parquet_files = sorted(parquet_dir.glob("*.parquet"))
    if not parquet_files:
        raise ValueError("No parquet files found in " + str(parquet_dir))

    feature_rows = []
    for pfile in parquet_files:
        stem = pfile.stem
        parts = stem.rsplit("_", 1)
        symbol = parts[0] if len(parts) > 1 else stem
        try:
            df = pd.read_parquet(pfile)
        except Exception as e:
            log.warning("SKIP %s: failed to load -- %s", pfile.name, e)
            continue
        if timeframe != "1m":
            try:
                df = _resample_ohlcv(df, timeframe)
            except Exception as e:
                log.warning("SKIP %s: resample failed -- %s", symbol, e)
                continue
        if len(df) < 50:
            log.warning("SKIP %s: too few bars (%d)", symbol, len(df))
            continue
        try:
            feat = compute_coin_features(df, symbol)
            feature_rows.append(feat)
            if verbose:
                log.info("OK %s: atr_pct=%.4f bbw=%.4f",
                         symbol, feat["avg_atr_pct"], feat["avg_bbw_raw"])
        except Exception as e:
            log.warning("SKIP %s: feature error -- %s", symbol, e)
            continue

    if len(feature_rows) < 4:
        raise ValueError(
            "Need at least 4 coins for tier classification, got "
            + str(len(feature_rows))
        )

    features_df = pd.DataFrame(feature_rows)
    feature_cols = [
        "avg_atr_pct", "avg_bbw_raw", "avg_daily_range",
        "avg_base_vol", "vol_of_vol",
    ]
    X = features_df[feature_cols].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    best_k = n_clusters
    best_score = -1.0
    best_labels = None
    k_min, k_max = SILHOUETTE_K_RANGE
    for k in range(k_min, min(k_max + 1, len(feature_rows))):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        if len(np.unique(labels)) < 2:
            continue
        score = silhouette_score(X_scaled, labels)
        if verbose:
            log.info("  k=%d silhouette=%.4f", k, score)
        if score > best_score:
            best_score = score
            best_k = k
            best_labels = labels

    if best_labels is None:
        km = KMeans(
            n_clusters=min(n_clusters, len(feature_rows)),
            random_state=42, n_init=10,
        )
        best_labels = km.fit_predict(X_scaled)

    features_df["raw_cluster"] = best_labels
    cluster_means = features_df.groupby("raw_cluster")["avg_atr_pct"].mean()
    sorted_clusters = cluster_means.sort_values().index.tolist()
    cluster_to_tier = {c: i for i, c in enumerate(sorted_clusters)}
    features_df["tier"] = features_df["raw_cluster"].map(cluster_to_tier)

    result = (
        features_df[["symbol", "tier"] + feature_cols]
        .sort_values(["tier", "symbol"])
        .reset_index(drop=True)
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(out, index=False)
        if verbose:
            log.info("Saved tier CSV: %s", out)

    return result
'''

if not write_and_compile(TARGETS["research/coin_classifier.py"], COIN_CLASSIFIER, "research/coin_classifier.py"):
    SYNTAX_FAILS.append("research/coin_classifier.py")

# =============================================================================
# FILE 2: tests/test_coin_classifier.py
# =============================================================================

TEST_COIN_CLASSIFIER = '''
"""Tests for research/coin_classifier.py
Run: python tests/test_coin_classifier.py
"""

import sys
import unittest
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.coin_classifier import compute_coin_features, classify_coin_tiers


def make_ohlcv(n=300, price=0.01, vol_mult=0.01, seed=42):
    """Generate synthetic OHLCV DataFrame with specified volatility."""
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


def write_parquet_set(tmpdir, n_coins=8):
    """Write n_coins synthetic parquet files with varying volatility."""
    vol_mults = [0.002, 0.004, 0.006, 0.008, 0.010, 0.012, 0.015, 0.020]
    for i in range(n_coins):
        vm = vol_mults[i % len(vol_mults)]
        df = make_ohlcv(n=300, price=0.01, vol_mult=vm, seed=i)
        df.to_parquet(Path(tmpdir) / ("COIN" + str(i) + "_1m.parquet"))


class TestComputeCoinFeatures(unittest.TestCase):

    def setUp(self):
        """Build synthetic OHLCV for tests."""
        self.df = make_ohlcv(n=300, price=0.01, seed=42)

    def test_returns_dict(self):
        """compute_coin_features returns a dict."""
        result = compute_coin_features(self.df, "TEST")
        self.assertIsInstance(result, dict, msg="result should be dict, got " + type(result).__name__)

    def test_keys_present(self):
        """Result dict has all expected keys."""
        result = compute_coin_features(self.df, "TEST")
        for k in ["symbol", "avg_atr_pct", "avg_bbw_raw",
                  "avg_daily_range", "avg_base_vol", "vol_of_vol"]:
            self.assertIn(k, result, msg="Missing key: " + k)

    def test_values_finite(self):
        """All numeric values are finite."""
        result = compute_coin_features(self.df, "TEST")
        for k, v in result.items():
            if k == "symbol":
                continue
            self.assertTrue(np.isfinite(v), msg=k + " is not finite: " + str(v))

    def test_atr_pct_positive(self):
        """avg_atr_pct is positive."""
        result = compute_coin_features(self.df, "TEST")
        self.assertGreater(result["avg_atr_pct"], 0,
                           msg="avg_atr_pct should be > 0, got " + str(result["avg_atr_pct"]))

    def test_symbol_preserved(self):
        """Symbol name is unchanged in output."""
        result = compute_coin_features(self.df, "MYCOIN")
        self.assertEqual(result["symbol"], "MYCOIN",
                         msg="symbol mismatch: " + str(result["symbol"]))

    def test_atr_pct_reasonable_range(self):
        """avg_atr_pct is in 0-100% for realistic data."""
        result = compute_coin_features(self.df, "TEST")
        self.assertGreater(result["avg_atr_pct"], 0.0, msg="atr_pct should be > 0")
        self.assertLess(result["avg_atr_pct"], 100.0, msg="atr_pct should be < 100")


class TestClassifyCoinTiers(unittest.TestCase):

    def setUp(self):
        """Create temp dir with synthetic parquet files."""
        import tempfile
        self.tmpobj = tempfile.TemporaryDirectory()
        self.tmpdir = self.tmpobj.name
        write_parquet_set(self.tmpdir, n_coins=8)

    def tearDown(self):
        """Clean up temp dir."""
        self.tmpobj.cleanup()

    def test_returns_dataframe(self):
        """classify_coin_tiers returns a DataFrame."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        self.assertIsInstance(result, pd.DataFrame,
                              msg="should return DataFrame, got " + type(result).__name__)

    def test_output_columns(self):
        """Output has required columns."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        for col in ["symbol", "tier", "avg_atr_pct"]:
            self.assertIn(col, result.columns, msg="Missing column: " + col)

    def test_tier_range(self):
        """Tiers are non-negative integers covering at least 2 values."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        self.assertGreaterEqual(result["tier"].min(), 0,
                                msg="min tier should be >= 0")
        self.assertGreaterEqual(result["tier"].nunique(), 2,
                                msg="should have at least 2 tiers")

    def test_no_duplicate_symbols(self):
        """No duplicate symbols in output."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        self.assertEqual(len(result), result["symbol"].nunique(),
                         msg="duplicate symbols found: " + str(len(result)) + " rows vs " + str(result["symbol"].nunique()) + " unique")

    def test_sorted_by_volatility(self):
        """Tier 0 has lower avg_atr_pct than max tier."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        tier0_atr = result[result["tier"] == 0]["avg_atr_pct"].mean()
        max_tier = result["tier"].max()
        tierN_atr = result[result["tier"] == max_tier]["avg_atr_pct"].mean()
        self.assertLessEqual(tier0_atr, tierN_atr,
                             msg="tier 0 should be calmest: " + str(tier0_atr) + " vs " + str(tierN_atr))

    def test_empty_dir_raises(self):
        """Empty parquet dir raises ValueError."""
        import tempfile
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(ValueError, msg="empty dir should raise ValueError"):
                classify_coin_tiers(empty_dir, timeframe="1m")

    def test_too_few_coins_raises(self):
        """Fewer than 4 coins raises ValueError."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(2):
                df = make_ohlcv(n=300, price=0.01, seed=i)
                df.to_parquet(Path(tmpdir) / ("COIN" + str(i) + "_1m.parquet"))
            with self.assertRaises(ValueError, msg="<4 coins should raise ValueError"):
                classify_coin_tiers(tmpdir, timeframe="1m")

    def test_output_path_writes_csv(self):
        """output_path writes CSV to disk."""
        import tempfile
        with tempfile.TemporaryDirectory() as outdir:
            out_csv = Path(outdir) / "tiers.csv"
            classify_coin_tiers(self.tmpdir, timeframe="1m",
                                output_path=str(out_csv))
            self.assertTrue(out_csv.exists(), msg="CSV file should exist at output_path")
            df = pd.read_csv(out_csv)
            self.assertGreater(len(df), 0, msg="CSV should not be empty")

    def test_skip_corrupt_parquet(self):
        """Corrupt parquet file is skipped; valid coins still processed."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            write_parquet_set(tmpdir, n_coins=8)
            (Path(tmpdir) / "CORRUPT_1m.parquet").write_text("not a parquet")
            result = classify_coin_tiers(tmpdir, timeframe="1m")
            self.assertIsInstance(result, pd.DataFrame)
            self.assertNotIn("CORRUPT", result["symbol"].values,
                             msg="Corrupt file should be skipped")


class TestCoinFeatureMath(unittest.TestCase):

    def test_higher_volatility_higher_atr_pct(self):
        """Coin with higher vol_mult has higher avg_atr_pct."""
        df_calm = make_ohlcv(n=300, price=0.01, vol_mult=0.002, seed=0)
        df_wild = make_ohlcv(n=300, price=0.01, vol_mult=0.020, seed=0)
        feat_calm = compute_coin_features(df_calm, "CALM")
        feat_wild = compute_coin_features(df_wild, "WILD")
        self.assertGreater(
            feat_wild["avg_atr_pct"], feat_calm["avg_atr_pct"],
            msg="wild coin should have higher atr_pct: "
            + str(feat_wild["avg_atr_pct"]) + " vs " + str(feat_calm["avg_atr_pct"]),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

if not write_and_compile(TARGETS["tests/test_coin_classifier.py"], TEST_COIN_CLASSIFIER, "tests/test_coin_classifier.py"):
    SYNTAX_FAILS.append("tests/test_coin_classifier.py")

# =============================================================================
# FILE 3: scripts/debug_coin_classifier.py
# =============================================================================

DEBUG_COIN_CLASSIFIER = '''
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
        log.info("\\n" + result.to_string())
        out_path = ROOT / "results" / "debug_coin_tiers.csv"
        out_path.parent.mkdir(exist_ok=True)
        result.to_csv(out_path, index=False)
        log.info("Saved: %s", out_path)
    else:
        log.warning("No real parquets found at %s -- skipping real data test", cache_dir)

    log.info("=== Done ===")


if __name__ == "__main__":
    main()
'''

if not write_and_compile(TARGETS["scripts/debug_coin_classifier.py"], DEBUG_COIN_CLASSIFIER, "scripts/debug_coin_classifier.py"):
    SYNTAX_FAILS.append("scripts/debug_coin_classifier.py")

# =============================================================================
# FILE 4: research/bbw_ollama_review.py
# =============================================================================

BBW_OLLAMA_REVIEW = '''
"""Layer 6: Ollama LLM review of BBW simulator outputs.

Reads report CSVs from Layer 5 and sends to Ollama for analysis.
Output: .md files in reports/bbw/ollama/.

All functions return strings. ollama_chat NEVER raises.
Imported by: scripts/run_bbw_simulator.py
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

log = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:8b"
OFFLINE_PREFIX = "OLLAMA_OFFLINE: "

AVAILABLE_MODELS = [
    "qwen3:8b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    "qwen3-coder:30b",
    "gpt-oss:20b",
]


def ollama_chat(prompt, model=DEFAULT_MODEL, temperature=0.3, timeout=120):
    """Send prompt to Ollama; return response string or OLLAMA_OFFLINE on error.

    Never raises -- all errors return OFFLINE_PREFIX + description.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False,
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except requests.exceptions.ConnectionError:
        return OFFLINE_PREFIX + "Cannot connect to Ollama at " + OLLAMA_URL
    except requests.exceptions.Timeout:
        return OFFLINE_PREFIX + "Request timed out after " + str(timeout) + "s"
    except json.JSONDecodeError as e:
        return OFFLINE_PREFIX + "JSONDecodeError: " + str(e)
    except Exception as e:
        return OFFLINE_PREFIX + str(e)


def _read_csv_sample(csv_path, max_rows=20):
    """Read CSV file and return string table; return empty string on any error."""
    import pandas as pd
    path = Path(csv_path)
    if not path.exists():
        log.warning("CSV not found: %s", path)
        return ""
    try:
        df = pd.read_csv(path)
        if df.empty:
            log.warning("CSV empty: %s", path)
            return ""
        return df.head(max_rows).to_string(index=False)
    except Exception as e:
        log.warning("Failed to read CSV %s: %s", path, e)
        return ""


def analyze_state_stats(state_stats_csv, mc_summary_csv, model=DEFAULT_MODEL):
    """Analyze BBW state statistics CSVs using Ollama; return markdown string."""
    state_text = _read_csv_sample(state_stats_csv)
    mc_text = _read_csv_sample(mc_summary_csv)
    if not state_text and not mc_text:
        return "## State Analysis\\n\\nNo CSV data available."
    context = (
        "SYSTEM CONTEXT (read carefully before analysing):\\n"
        "You are reviewing output from a BBW (Bollinger Band Width) Simulator for a "
        "crypto futures trading system called Four Pillars.\\n\\n"
        "KEY DEFINITIONS:\\n"
        "- BBW = Bollinger Band Width. Measures volatility expansion/contraction.\\n"
        "- BBWP = BBW Percentile (0-100 relative to lookback). High = expanding, Low = compressing.\\n"
        "- bbwp_state values: NORMAL (mid-range), BLUE (high BBWP, expansion), "
        "RED (low BBWP, compression), BLUE_DOUBLE (extreme expansion).\\n"
        "- The simulator ran a grid search: for each state it tested every combination of "
        "leverage (5/10/15/20x), position size (0.25/0.5/0.75/1.0 of $250 base), "
        "TP target (1-6 ATR), SL (1.0/1.5/2.0/3.0 ATR), and forward window (10/20 bars).\\n"
        "- Commission: 0.08% taker per side on notional. Blended rate ~0.05%/side.\\n"
        "- expectancy: Expected net USD PnL per trade after commission.\\n"
        "- win_rate_long / win_rate_short: % trades profitable for that direction.\\n"
        "- net_pnl: Total net PnL over the dataset.\\n"
        "- max_dd: Maximum drawdown in USD.\\n"
        "- MCL / max_consecutive_loss: Worst losing streak length.\\n"
        "- profit_factor: Gross profit / Gross loss (>1 = edge).\\n"
        "- n_trades: Sample size. Below 30 = unreliable.\\n"
        "- LSG = Loser Saw Green: % of losing trades that were briefly profitable "
        "(high LSG means TP too tight or exits too slow).\\n"
        "- robust verdict: Monte Carlo CI for expectancy stayed > 0 across 95% of sims.\\n"
        "- fragile verdict: passed backtest but failed MC permutation (likely curve-fit).\\n\\n"
    )
    prompt = (
        context
        + "STATE STATS (one row per bbwp_state x direction x lever/size/TP/SL combo):\\n"
        + (state_text or "N/A") + "\\n\\n"
        "MONTE CARLO SUMMARY (per state: verdict, CI bounds, equity band):\\n"
        + (mc_text or "N/A") + "\\n\\n"
        "Based on the above data, provide a concise analysis covering:\\n"
        "1. Which bbwp_state shows the strongest edge (highest expectancy per trade)?\\n"
        "2. Which states have a ROBUST Monte Carlo verdict (genuine edge vs lucky backtest)?\\n"
        "3. Which direction (long vs short) performs better per state?\\n"
        "4. Key risk metrics to watch (max_dd, MCL, low n_trades warnings).\\n"
        "Format as markdown with headers. Be specific -- reference state names and numbers."
    )
    return ollama_chat(prompt, model=model)


def investigate_anomalies(overfit_flags_csv, per_tier_dir, model="qwen3-coder:30b"):
    """Investigate overfit flags and per-tier anomalies; return markdown string."""
    overfit_text = _read_csv_sample(overfit_flags_csv)
    per_tier_dir = Path(per_tier_dir)
    tier_texts = []
    if per_tier_dir.exists():
        for f in sorted(per_tier_dir.glob("*.csv"))[:5]:
            t = _read_csv_sample(f, max_rows=10)
            if t:
                tier_texts.append("TIER " + f.stem + ":\\n" + t)
    tier_summary = "\\n\\n".join(tier_texts) if tier_texts else "N/A"
    if not overfit_text and not tier_texts:
        return "## Anomaly Investigation\\n\\nNo data available."
    context2 = (
        "SYSTEM CONTEXT:\\n"
        "You are reviewing overfitting diagnostics for a crypto futures BBW Simulator.\\n\\n"
        "WHAT THIS DATA REPRESENTS:\\n"
        "- The simulator tested 4 volatility states (NORMAL/BLUE/RED/BLUE_DOUBLE) "
        "on historical data across multiple coins.\\n"
        "- Coins are grouped into volatility tiers by KMeans on ATR%: "
        "Tier 0 = calmest (smallest ATR%), Tier 3 = wildest (largest ATR%).\\n"
        "- OVERFIT FLAGS come from Monte Carlo permutation tests: a state is flagged if "
        "its edge disappears when trade order is randomly shuffled.\\n"
        "- mc_pvalue: permutation test p-value (below 0.05 = statistically significant edge).\\n"
        "- overfit_score: composite 0-1 (1.0 = fully overfit / no real edge).\\n"
        "- is_fragile: True if edge fails under MC permutation despite passing backtest.\\n"
        "- PER-TIER STATS show the same metrics split by coin volatility tier.\\n\\n"
    )
    prompt = (
        context2
        + "OVERFIT FLAGS:\\n" + (overfit_text or "N/A") + "\\n\\n"
        "PER-TIER STATS:\\n" + tier_summary + "\\n\\n"
        "Based on this data:\\n"
        "1. Which states or coin tiers show clear curve-fitting (is_fragile=True, "
        "high overfit_score, or mc_pvalue > 0.05)?\\n"
        "2. Are differences between tiers physically justified by volatility differences "
        "(wilder coins have bigger ATR so TP is worth more in dollar terms)?\\n"
        "3. For each flagged state/tier, suggest a concrete parameter fix "
        "(wider TP, lower leverage, higher minimum n_trades threshold).\\n"
        "Format as markdown. Reference state names, tier numbers, and specific values."
    )
    return ollama_chat(prompt, model=model)


def generate_executive_summary(all_results, model="qwen3-coder:30b"):
    """Generate executive summary of all BBW results; return markdown string."""
    if not all_results:
        return "## Executive Summary\\n\\nNo results to summarize."
    results_text = json.dumps(all_results, indent=2, default=str)[:4000]
    context3 = (
        "SYSTEM CONTEXT (essential background):\\n"
        "You are reviewing a quantitative trading research project called BBW Simulator.\\n\\n"
        "THE STRATEGY: Four Pillars is a crypto futures momentum strategy that uses "
        "multi-timeframe stochastics (9/14/40/60-period Kurisko Raw K) and Ripster EMA clouds "
        "to generate long/short entry signals graded A (strongest) to D (weakest).\\n\\n"
        "THE SIMULATOR PURPOSE: Determine the optimal leverage, position size, TP (take-profit), "
        "and SL (stop-loss) for each Bollinger Band Width (BBW) volatility state, so the "
        "strategy can adapt position sizing to market conditions.\\n\\n"
        "BBW STATES: NORMAL (ordinary volatility), BLUE (expanding - BBW rising), "
        "RED (compressing - BBW falling), BLUE_DOUBLE (extreme expansion - top 1% BBW).\\n\\n"
        "ECONOMICS: Commission is 0.08% taker per side on notional. At 10x leverage on "
        "$250 margin, one round-trip costs ~$4. Expectancy must beat commission per trade.\\n\\n"
        "KNOWN INSIGHT: Low-price coins (RIVER, KITE, PEPE) are profitable because their "
        "ATR is large relative to commission. BTC/ETH often fail because commission consumes "
        "too much of the TP. This is not a bug -- it is structural.\\n\\n"
        "RESULTS JSON:\\n"
    )
    prompt = (
        context3
        + results_text + "\\n\\n"
        "Write a 3-paragraph executive summary covering:\\n"
        "1. Overall edge quality: which BBW states have genuine, Monte-Carlo-confirmed edge?\\n"
        "2. Best-performing states and the recommended leverage/size/TP/SL for each.\\n"
        "3. Key risks (commission sensitivity, MCL, low sample sizes) and next research steps.\\n"
        "Format as markdown with a header for each paragraph. Be direct and quantitative."
    )
    return ollama_chat(prompt, model=model)


def run_ollama_review(reports_dir="reports/bbw", output_dir="reports/bbw/ollama",
                      model=DEFAULT_MODEL, verbose=False):
    """Run all Ollama review steps; write .md files; return status dict.

    Returns dict: files_written (list), errors (list), summary (dict).
    Never raises -- all errors are logged and collected.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    t0 = time.time()
    reports_dir = Path(reports_dir)
    output_dir = Path(output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {
            "files_written": [],
            "errors": ["Cannot create output dir: " + str(e)],
            "summary": {"timestamp": ts, "runtime_sec": 0},
        }

    files_written = []
    errors = []

    # Step 1: State stats analysis
    state_csv = reports_dir / "aggregate" / "bbw_state_stats.csv"
    mc_csv = reports_dir / "monte_carlo" / "mc_summary_by_state.csv"
    if verbose:
        log.info("[%s] Analyzing state stats...", ts)
    try:
        analysis = analyze_state_stats(str(state_csv), str(mc_csv), model=model)
        out_path = output_dir / "state_analysis.md"
        out_path.write_text("# BBW State Analysis\\n\\n" + analysis + "\\n",
                            encoding="utf-8")
        files_written.append(str(out_path))
        if verbose:
            log.info("  WROTE: %s", out_path.name)
    except PermissionError as e:
        errors.append("state_analysis.md: PermissionError: " + str(e))
        log.error("Cannot write state_analysis.md: %s", e)
    except Exception as e:
        errors.append("state_analysis.md: " + str(e))
        log.warning("State analysis failed: %s", e)

    # Step 2: Anomaly investigation
    overfit_csv = reports_dir / "monte_carlo" / "mc_overfit_flags.csv"
    per_tier_dir = reports_dir / "per_tier"
    if verbose:
        log.info("  Investigating anomalies...")
    try:
        anomaly = investigate_anomalies(str(overfit_csv), str(per_tier_dir), model=model)
        out_path = output_dir / "anomaly_investigation.md"
        out_path.write_text("# Anomaly Investigation\\n\\n" + anomaly + "\\n",
                            encoding="utf-8")
        files_written.append(str(out_path))
        if verbose:
            log.info("  WROTE: %s", out_path.name)
    except PermissionError as e:
        errors.append("anomaly_investigation.md: PermissionError: " + str(e))
        log.error("Cannot write anomaly_investigation.md: %s", e)
    except Exception as e:
        errors.append("anomaly_investigation.md: " + str(e))
        log.warning("Anomaly investigation failed: %s", e)

    # Step 3: Executive summary
    all_results = {
        "state_stats_csv": str(state_csv),
        "mc_summary_csv": str(mc_csv),
        "files_written": files_written,
        "errors": errors,
        "timestamp": ts,
    }
    if verbose:
        log.info("  Generating executive summary...")
    try:
        summary_text = generate_executive_summary(all_results, model=model)
        out_path = output_dir / "executive_summary.md"
        out_path.write_text("# Executive Summary\\n\\n" + summary_text + "\\n",
                            encoding="utf-8")
        files_written.append(str(out_path))
        if verbose:
            log.info("  WROTE: %s", out_path.name)
    except PermissionError as e:
        errors.append("executive_summary.md: PermissionError: " + str(e))
        log.error("Cannot write executive_summary.md: %s", e)
    except Exception as e:
        errors.append("executive_summary.md: " + str(e))
        log.warning("Executive summary failed: %s", e)

    runtime = time.time() - t0
    return {
        "files_written": files_written,
        "errors": errors,
        "summary": {
            "timestamp": ts,
            "n_files": len(files_written),
            "n_errors": len(errors),
            "runtime_sec": round(runtime, 2),
        },
    }
'''

if not write_and_compile(TARGETS["research/bbw_ollama_review.py"], BBW_OLLAMA_REVIEW, "research/bbw_ollama_review.py"):
    SYNTAX_FAILS.append("research/bbw_ollama_review.py")

# =============================================================================
# FILE 5: tests/test_bbw_ollama_review.py
# =============================================================================

TEST_BBW_OLLAMA_REVIEW = '''
"""Tests for research/bbw_ollama_review.py
Run: python tests/test_bbw_ollama_review.py
"""

import sys
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests

from research.bbw_ollama_review import (
    ollama_chat,
    analyze_state_stats,
    investigate_anomalies,
    generate_executive_summary,
    run_ollama_review,
    OFFLINE_PREFIX,
)


def _mock_resp(text="Test response"):
    """Build a mock requests.Response that returns text."""
    r = MagicMock()
    r.json.return_value = {"response": text}
    r.raise_for_status = MagicMock()
    return r


class TestOllamaChat(unittest.TestCase):

    def test_success_returns_response(self):
        """Successful Ollama call returns the response text."""
        with patch("requests.post", return_value=_mock_resp("Hello World")):
            result = ollama_chat("Test prompt")
        self.assertEqual(result, "Hello World",
                         msg="should return response text, got: " + result[:50])

    def test_connection_error_returns_offline(self):
        """ConnectionError returns string starting with OFFLINE_PREFIX."""
        with patch("requests.post",
                   side_effect=requests.exceptions.ConnectionError("refused")):
            result = ollama_chat("Test")
        self.assertTrue(result.startswith(OFFLINE_PREFIX),
                        msg="should start with OFFLINE_PREFIX, got: " + result[:60])

    def test_timeout_returns_offline(self):
        """Timeout returns OFFLINE_PREFIX string."""
        with patch("requests.post",
                   side_effect=requests.exceptions.Timeout("timeout")):
            result = ollama_chat("Test")
        self.assertTrue(result.startswith(OFFLINE_PREFIX),
                        msg="timeout should return OFFLINE, got: " + result[:60])

    def test_json_decode_error_returns_offline(self):
        """JSONDecodeError in response returns OFFLINE_PREFIX string."""
        bad_resp = MagicMock()
        bad_resp.json.side_effect = json.JSONDecodeError("err", "doc", 0)
        bad_resp.raise_for_status = MagicMock()
        with patch("requests.post", return_value=bad_resp):
            result = ollama_chat("Test")
        self.assertTrue(result.startswith(OFFLINE_PREFIX),
                        msg="JSONDecodeError should return OFFLINE, got: " + result[:60])

    def test_always_returns_string(self):
        """ollama_chat always returns str even on unexpected errors."""
        with patch("requests.post", side_effect=Exception("unexpected")):
            result = ollama_chat("Test")
        self.assertIsInstance(result, str,
                              msg="should return str, got " + type(result).__name__)


class TestAnalyzeStateStats(unittest.TestCase):

    def test_missing_csv_returns_string(self):
        """Missing CSV paths return a string without crashing."""
        with patch("requests.post",
                   side_effect=requests.exceptions.ConnectionError("x")):
            result = analyze_state_stats("/nonexistent/path.csv", "/nonexistent.csv")
        self.assertIsInstance(result, str,
                              msg="missing CSV should return string")

    def test_empty_csv_skipped(self):
        """Empty CSV returns a string (not a crash)."""
        with tempfile.NamedTemporaryFile(
            suffix=".csv", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write("state,expectancy\\n")
            tmp = f.name
        try:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = analyze_state_stats(tmp, "/nonexistent.csv")
            self.assertIsInstance(result, str)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_with_mock_ollama_response(self):
        """analyze_state_stats passes CSV data to Ollama and returns response."""
        with tempfile.NamedTemporaryFile(
            suffix=".csv", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write("state,expectancy\\nBLUE,1.5\\nRED,0.8\\n")
            tmp = f.name
        try:
            with patch("requests.post", return_value=_mock_resp("Analysis here")):
                result = analyze_state_stats(tmp, "/nonexistent.csv")
            self.assertEqual(result, "Analysis here",
                             msg="should return Ollama response")
        finally:
            Path(tmp).unlink(missing_ok=True)


class TestInvestigateAnomalies(unittest.TestCase):

    def test_missing_all_inputs_returns_string(self):
        """Missing CSV and dir return a string."""
        with patch("requests.post",
                   side_effect=requests.exceptions.ConnectionError("x")):
            result = investigate_anomalies("/nonexistent.csv", "/nonexistent_dir")
        self.assertIsInstance(result, str,
                              msg="missing inputs should return string")

    def test_empty_tier_dir_returns_string(self):
        """Empty per_tier_dir returns no-data string without crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = investigate_anomalies("/nonexistent.csv", tmpdir)
        self.assertIsInstance(result, str)


class TestGenerateExecutiveSummary(unittest.TestCase):

    def test_empty_results_returns_string(self):
        """Empty all_results dict returns a no-data string."""
        result = generate_executive_summary({})
        self.assertIsInstance(result, str,
                              msg="empty dict should return string")

    def test_with_mock_response(self):
        """generate_executive_summary returns Ollama response text."""
        with patch("requests.post", return_value=_mock_resp("Executive summary")):
            result = generate_executive_summary({"test": "data"})
        self.assertEqual(result, "Executive summary",
                         msg="should return Ollama response text")


class TestRunOllamaReview(unittest.TestCase):

    def test_returns_dict(self):
        """run_ollama_review always returns a dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        self.assertIsInstance(result, dict,
                              msg="should return dict, got " + type(result).__name__)

    def test_correct_keys(self):
        """Return dict has files_written, errors, summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        for k in ["files_written", "errors", "summary"]:
            self.assertIn(k, result, msg="Missing key in result: " + k)

    def test_offline_still_writes_md_files(self):
        """Ollama offline still writes .md files with OFFLINE content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        self.assertGreater(
            len(result["files_written"]), 0,
            msg="should write .md files even when offline, got 0",
        )

    def test_online_writes_md_files(self):
        """When Ollama is online, .md files are written."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post", return_value=_mock_resp("Mock analysis")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        self.assertGreater(len(result["files_written"]), 0,
                           msg="should write at least one .md file when online")

    def test_verbose_does_not_crash(self):
        """verbose=True runs without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with patch("requests.post",
                           side_effect=requests.exceptions.ConnectionError("x")):
                    run_ollama_review(
                        reports_dir=tmpdir,
                        output_dir=str(Path(tmpdir) / "ollama"),
                        verbose=True,
                    )
            except Exception as e:
                self.fail("verbose=True raised exception: " + str(e))


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

if not write_and_compile(TARGETS["tests/test_bbw_ollama_review.py"], TEST_BBW_OLLAMA_REVIEW, "tests/test_bbw_ollama_review.py"):
    SYNTAX_FAILS.append("tests/test_bbw_ollama_review.py")

# =============================================================================
# FILE 6: scripts/debug_bbw_ollama_review.py
# =============================================================================

DEBUG_BBW_OLLAMA_REVIEW = '''
"""Debug script for bbw_ollama_review.
Run: python scripts/debug_bbw_ollama_review.py
"""

import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    """Debug bbw_ollama_review: ping Ollama and run review on real or mock data."""
    from research.bbw_ollama_review import ollama_chat, run_ollama_review, OFFLINE_PREFIX

    log.info("=== Debug: bbw_ollama_review ===")

    # Step 1: Ping Ollama
    log.info("Pinging Ollama (10s timeout)...")
    t0 = time.time()
    ping = ollama_chat("Reply with exactly: ONLINE", model="qwen3:8b", timeout=10)
    dt = time.time() - t0
    if ping.startswith(OFFLINE_PREFIX):
        log.warning("Ollama is OFFLINE: %s", ping)
        ollama_online = False
    else:
        log.info("Ollama ONLINE (%.1fs): %s", dt, ping[:80])
        ollama_online = True

    # Step 2: Run review on real reports if available
    reports_dir = ROOT / "reports" / "bbw"
    out_dir = ROOT / "results" / "debug_ollama"
    log.info("Running review (reports_dir=%s)...", reports_dir)
    t1 = time.time()
    result = run_ollama_review(
        reports_dir=str(reports_dir),
        output_dir=str(out_dir),
        model="qwen3:8b",
        verbose=True,
    )
    elapsed = time.time() - t1
    log.info("Review done: %.1fs", elapsed)
    log.info("Files written: %d", len(result["files_written"]))
    for fpath in result["files_written"]:
        p = Path(fpath)
        if p.exists():
            lines = p.read_text(encoding="utf-8").split("\\n")
            log.info("  %s (%d lines): %s", p.name, len(lines), lines[0][:80])
    if result["errors"]:
        log.warning("Errors: " + str(result["errors"]))

    log.info("=== Done ===")


if __name__ == "__main__":
    main()
'''

if not write_and_compile(TARGETS["scripts/debug_bbw_ollama_review.py"], DEBUG_BBW_OLLAMA_REVIEW, "scripts/debug_bbw_ollama_review.py"):
    SYNTAX_FAILS.append("scripts/debug_bbw_ollama_review.py")

# =============================================================================
# FILE 7: scripts/run_bbw_simulator.py
# =============================================================================

RUN_BBW_SIMULATOR = '''
"""CLI: BBW Simulator Pipeline Runner.

Wires Layers 1-6 together for one or more coins.
Run: python scripts/run_bbw_simulator.py --symbol RIVERUSDT --no-ollama --verbose
"""

import argparse
import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

log = logging.getLogger(__name__)

CACHE_DIR = ROOT / "data" / "cache"
REPORTS_DIR = ROOT / "reports" / "bbw"


def _resample_5m(df):
    """Resample 1m OHLCV DataFrame to 5m candles."""
    if "datetime" not in df.columns:
        if df.index.name == "datetime":
            df = df.reset_index()
    df2 = df.set_index("datetime")
    vol_col = "base_vol" if "base_vol" in df2.columns else (
        "volume" if "volume" in df2.columns else None
    )
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if vol_col:
        agg[vol_col] = "sum"
    return df2.resample("5min").agg(agg).dropna().reset_index()


def _load_coin_data(symbol, timeframe, cache_dir):
    """Load parquet for symbol/timeframe; return DataFrame or None on failure."""
    direct = cache_dir / (symbol + "_" + timeframe + ".parquet")
    if direct.exists():
        try:
            return pd.read_parquet(direct)
        except Exception as e:
            log.error("Failed to load %s: %s", direct.name, e)
            return None

    # Fallback: load 1m and resample
    pfile_1m = cache_dir / (symbol + "_1m.parquet")
    if not pfile_1m.exists():
        matches = sorted(cache_dir.glob(symbol + "_*.parquet"))
        if not matches:
            log.warning("No parquet found for %s", symbol)
            return None
        pfile_1m = matches[0]

    try:
        df = pd.read_parquet(pfile_1m)
    except Exception as e:
        log.error("Failed to load %s: %s", pfile_1m.name, e)
        return None

    if timeframe != "1m":
        try:
            df = _resample_5m(df)
        except Exception as e:
            log.error("Resample failed for %s: %s", symbol, e)
            return None
    return df


def _get_coin_list(args, coin_tiers):
    """Resolve the list of symbols to process from CLI args and tier data."""
    if args.symbol:
        return list(args.symbol)

    if coin_tiers is not None and args.tier is not None:
        filtered = coin_tiers[coin_tiers["tier"] == args.tier]
        symbols = filtered["symbol"].tolist()
        log.info("Tier %d: %d coins", args.tier, len(symbols))
        if args.top:
            symbols = symbols[:args.top]
        return symbols

    # Default: all 1m parquets in cache
    pfiles = sorted(cache_dir.glob("*_1m.parquet"))
    symbols = [p.stem.replace("_1m", "") for p in pfiles]
    if args.top:
        symbols = symbols[:args.top]
    log.info("Using %d coins from cache", len(symbols))
    return symbols


def run_pipeline(args):
    """Run the full BBW pipeline (L1-L6) based on parsed CLI args.

    Returns summary dict with n_coins_processed, n_errors, etc.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    t0 = time.time()

    log.info("=== BBW Simulator Pipeline -- %s ===", ts)

    if args.dry_run:
        log.info("DRY RUN -- no data will be processed")
        return {"dry_run": True, "n_coins_processed": 0, "n_errors": 0,
                "timestamp": ts, "runtime_sec": 0}

    # Import required pipeline modules
    try:
        from signals.bbwp import calculate_bbwp
        from signals.bbw_sequence import track_bbw_sequence
        from research.bbw_forward_returns import tag_forward_returns
        from research.bbw_simulator import run_simulator
        from research.bbw_report import run_report
    except ImportError as e:
        log.error("Import failed: %s", e)
        log.error("Make sure all pipeline modules are present in: %s", ROOT)
        sys.exit(1)

    # Optional: Monte Carlo
    run_monte_carlo_fn = None
    if not args.no_monte_carlo:
        try:
            from research.bbw_monte_carlo import run_monte_carlo as _rmc
            run_monte_carlo_fn = _rmc
        except ImportError as e:
            log.warning("Monte Carlo module not found: %s -- skipping L4b", e)

    # Optional: Ollama review
    run_ollama_fn = None
    if not args.no_ollama:
        try:
            from research.bbw_ollama_review import run_ollama_review as _rov
            run_ollama_fn = _rov
        except ImportError as e:
            log.warning("Ollama review module not found: %s -- skipping L6", e)

    # Load coin tiers if available
    coin_tiers = None
    tiers_path = ROOT / "results" / "coin_tiers.csv"
    if tiers_path.exists():
        try:
            coin_tiers = pd.read_csv(tiers_path)
            log.info("Loaded coin tiers: %d coins", len(coin_tiers))
        except Exception as e:
            log.warning("Failed to load coin tiers: %s", e)

    symbols = _get_coin_list(args, coin_tiers)
    if not symbols:
        log.error("No symbols to process. Check --symbol or cache at %s", CACHE_DIR)
        sys.exit(1)

    preview = ", ".join(str(s) for s in symbols[:5])
    if len(symbols) > 5:
        preview += "..."
    log.info("Processing %d coin(s): %s", len(symbols), preview)

    processed_dfs = []
    n_errors = 0

    for i, symbol in enumerate(symbols, 1):
        log.info("[%d/%d] %s", i, len(symbols), symbol)
        t_coin = time.time()
        try:
            df = _load_coin_data(symbol, args.timeframe, CACHE_DIR)
            if df is None:
                log.warning("SKIP %s: no data", symbol)
                n_errors += 1
                continue

            df = calculate_bbwp(df)
            df = track_bbw_sequence(df)
            df = tag_forward_returns(df)

            processed_dfs.append(df)
            log.info("  OK %s (%d bars, %.1fs)", symbol, len(df), time.time() - t_coin)

        except Exception as e:
            log.error("FAIL %s: %s", symbol, e)
            log.debug(traceback.format_exc())
            n_errors += 1
            continue

    if not processed_dfs:
        log.error("Zero coins processed successfully.")
        sys.exit(1)

    log.info("Combining %d DataFrames for L4...", len(processed_dfs))
    combined_df = pd.concat(processed_dfs, ignore_index=True)
    log.info("Combined shape: %s", str(combined_df.shape))

    # L4: Simulator
    log.info("Running L4 (Simulator)...")
    t_l4 = time.time()
    layer4_result = run_simulator(combined_df)
    log.info("L4 done: %.1fs", time.time() - t_l4)

    # L4b: Monte Carlo (optional)
    layer4b_result = None
    if run_monte_carlo_fn is not None:
        log.info("Running L4b (Monte Carlo, n_sims=%d)...", args.mc_sims)
        t_l4b = time.time()
        try:
            layer4b_result = run_monte_carlo_fn(combined_df, layer4_result.lsg_top)
            log.info("L4b done: %.1fs", time.time() - t_l4b)
        except Exception as e:
            log.error("L4b failed: %s", e)
            log.debug(traceback.format_exc())

    # L5: Report
    log.info("Running L5 (Report)...")
    t_l5 = time.time()
    report_result = run_report(
        layer4_result,
        layer4b_result,
        output_dir=str(args.output_dir),
        coin_tiers=coin_tiers,
        verbose=args.verbose,
    )
    n_reports = len(report_result.get("reports_written", []))
    log.info("L5 done: %.1fs -- %d files, %d errors",
             time.time() - t_l5, n_reports, len(report_result.get("errors", [])))

    # L6: Ollama review (optional)
    if run_ollama_fn is not None:
        log.info("Running L6 (Ollama review, model=%s)...", args.ollama_model)
        t_l6 = time.time()
        try:
            ollama_result = run_ollama_fn(
                reports_dir=str(args.output_dir),
                output_dir=str(Path(args.output_dir) / "ollama"),
                model=args.ollama_model,
                verbose=args.verbose,
            )
            log.info("L6 done: %.1fs -- %d files",
                     time.time() - t_l6, len(ollama_result.get("files_written", [])))
        except Exception as e:
            log.error("L6 failed: %s", e)
            log.debug(traceback.format_exc())

    runtime = time.time() - t0
    summary = {
        "timestamp": ts,
        "n_coins_processed": len(processed_dfs),
        "n_errors": n_errors,
        "n_reports": n_reports,
        "runtime_sec": round(runtime, 2),
    }
    log.info("=== DONE: %d OK  %d errors  %d reports  %.1fs ===",
             summary["n_coins_processed"], summary["n_errors"],
             summary["n_reports"], summary["runtime_sec"])
    return summary


def _build_parser():
    """Build and return the CLI argparse ArgumentParser."""
    p = argparse.ArgumentParser(
        description="BBW Simulator Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--symbol", nargs="+", help="Coin symbol(s) to process")
    p.add_argument("--tier", type=int, help="Volatility tier to process (0-3)")
    p.add_argument("--timeframe", default="5m",
                   help="Candle timeframe (default: 5m)")
    p.add_argument("--top", type=int,
                   help="Process top N coins only")
    p.add_argument("--no-monte-carlo", action="store_true",
                   help="Skip Layer 4b Monte Carlo validation")
    p.add_argument("--mc-sims", type=int, default=1000,
                   help="Monte Carlo simulations (default: 1000)")
    p.add_argument("--no-ollama", action="store_true",
                   help="Skip Layer 6 Ollama review")
    p.add_argument("--ollama-model", default="qwen3:8b",
                   help="Ollama model for Layer 6 (default: qwen3:8b)")
    p.add_argument("--output-dir", default=str(REPORTS_DIR),
                   help="Output directory for reports")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse args and exit without processing")
    return p


def main():
    """Entry point: parse args and run pipeline."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = _build_parser()
    args = parser.parse_args()
    args.output_dir = Path(args.output_dir)
    run_pipeline(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

if not write_and_compile(TARGETS["scripts/run_bbw_simulator.py"], RUN_BBW_SIMULATOR, "scripts/run_bbw_simulator.py"):
    SYNTAX_FAILS.append("scripts/run_bbw_simulator.py")

# =============================================================================
# FILE 8: tests/test_run_bbw_simulator.py
# =============================================================================

TEST_RUN_BBW_SIMULATOR = '''
"""Tests for scripts/run_bbw_simulator.py
Run: python tests/test_run_bbw_simulator.py
"""

import sys
import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_bbw_simulator as rbs
from run_bbw_simulator import _build_parser, run_pipeline


def _make_args(**kwargs):
    """Build a minimal Namespace for run_pipeline tests."""
    defaults = {
        "symbol": None, "tier": None, "timeframe": "5m",
        "top": None, "no_monte_carlo": True, "mc_sims": 1000,
        "no_ollama": True, "ollama_model": "qwen3:8b",
        "output_dir": Path(tempfile.mkdtemp()),
        "verbose": False, "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _parse(args_list):
    """Parse a CLI args list using _build_parser."""
    p = _build_parser()
    args = p.parse_args(args_list)
    args.output_dir = Path(args.output_dir)
    return args


class TestArgparse(unittest.TestCase):

    def test_parse_symbol_flag(self):
        """--symbol RIVERUSDT sets args.symbol = [\'RIVERUSDT\']."""
        args = _parse(["--symbol", "RIVERUSDT"])
        self.assertEqual(args.symbol, ["RIVERUSDT"],
                         msg="symbol mismatch: " + str(args.symbol))

    def test_parse_no_ollama_flag(self):
        """--no-ollama sets no_ollama=True."""
        args = _parse(["--no-ollama"])
        self.assertTrue(args.no_ollama,
                        msg="no_ollama should be True")

    def test_parse_no_monte_carlo_flag(self):
        """--no-monte-carlo sets no_monte_carlo=True."""
        args = _parse(["--no-monte-carlo"])
        self.assertTrue(args.no_monte_carlo,
                        msg="no_monte_carlo should be True")

    def test_parse_verbose_flag(self):
        """--verbose sets verbose=True."""
        args = _parse(["--verbose"])
        self.assertTrue(args.verbose, msg="verbose should be True")

    def test_parse_dry_run_flag(self):
        """--dry-run sets dry_run=True."""
        args = _parse(["--dry-run"])
        self.assertTrue(args.dry_run, msg="dry_run should be True")

    def test_parse_top_flag(self):
        """--top 5 sets top=5."""
        args = _parse(["--top", "5"])
        self.assertEqual(args.top, 5,
                         msg="top should be 5, got " + str(args.top))

    def test_parse_mc_sims_default(self):
        """Default mc_sims is 1000."""
        args = _parse([])
        self.assertEqual(args.mc_sims, 1000,
                         msg="default mc_sims should be 1000, got " + str(args.mc_sims))

    def test_parse_ollama_model_default(self):
        """Default ollama_model is qwen3:8b."""
        args = _parse([])
        self.assertEqual(args.ollama_model, "qwen3:8b",
                         msg="default model mismatch: " + str(args.ollama_model))


class TestRunPipelineDryRun(unittest.TestCase):

    def test_dry_run_returns_dict(self):
        """dry_run=True returns a dict immediately."""
        args = _make_args(dry_run=True)
        result = run_pipeline(args)
        self.assertIsInstance(result, dict,
                              msg="dry_run should return dict, got " + type(result).__name__)

    def test_dry_run_n_coins_zero(self):
        """dry_run returns n_coins_processed=0."""
        args = _make_args(dry_run=True)
        result = run_pipeline(args)
        self.assertEqual(result["n_coins_processed"], 0,
                         msg="dry_run n_coins_processed should be 0")

    def test_dry_run_has_required_keys(self):
        """dry_run result has n_coins_processed and n_errors."""
        args = _make_args(dry_run=True)
        result = run_pipeline(args)
        for k in ["n_coins_processed", "n_errors"]:
            self.assertIn(k, result, msg="Missing key in result: " + k)


class TestRunPipelineZeroCoins(unittest.TestCase):

    def test_zero_parquets_causes_system_exit(self):
        """Zero processable coins causes sys.exit."""
        args = _make_args(
            symbol=["NONEXISTENT"],
            dry_run=False,
            no_monte_carlo=True,
            no_ollama=True,
        )
        mock_modules = {
            "signals.bbwp":                 MagicMock(),
            "signals.bbw_sequence":         MagicMock(),
            "research.bbw_forward_returns": MagicMock(),
            "research.bbw_simulator":       MagicMock(),
            "research.bbw_report":          MagicMock(),
        }
        import sys as _sys
        with patch.object(rbs, "_load_coin_data", return_value=None), \
             patch.dict(_sys.modules, mock_modules):
            with self.assertRaises(SystemExit,
                                   msg="zero coins should cause SystemExit"):
                run_pipeline(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

if not write_and_compile(TARGETS["tests/test_run_bbw_simulator.py"], TEST_RUN_BBW_SIMULATOR, "tests/test_run_bbw_simulator.py"):
    SYNTAX_FAILS.append("tests/test_run_bbw_simulator.py")

# =============================================================================
# FILE 9: scripts/debug_run_bbw_simulator.py
# =============================================================================

DEBUG_RUN_BBW_SIMULATOR = '''
"""Debug script for run_bbw_simulator pipeline.
Run: python scripts/debug_run_bbw_simulator.py
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    """Run BBW pipeline smoke test on RIVERUSDT via subprocess."""
    log.info("=== Debug: run_bbw_simulator ===")

    cli_script = ROOT / "scripts" / "run_bbw_simulator.py"
    out_dir = ROOT / "results" / "debug_bbw_pipeline"

    cmd = [
        sys.executable, str(cli_script),
        "--symbol", "RIVERUSDT",
        "--no-ollama",
        "--verbose",
        "--output-dir", str(out_dir),
    ]
    log.info("Command: " + " ".join(cmd))

    t0 = time.time()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    dt = time.time() - t0

    log.info("Exit code: %d  Time: %.1fs", proc.returncode, dt)
    if proc.stdout:
        log.info("STDOUT (last 3000 chars):\\n%s", proc.stdout[-3000:])
    if proc.stderr:
        log.info("STDERR (last 1000 chars):\\n%s", proc.stderr[-1000:])

    # Validate aggregate CSVs
    agg_dir = out_dir / "aggregate"
    if agg_dir.exists():
        csvs = sorted(agg_dir.glob("*.csv"))
        log.info("aggregate/ CSVs: %d", len(csvs))
        for f in csvs:
            log.info("  %s  %d bytes", f.name, f.stat().st_size)
    else:
        log.warning("aggregate/ dir not found: %s", agg_dir)

    if proc.returncode == 0:
        log.info("RESULT: PASS -- pipeline completed successfully")
    else:
        log.warning("RESULT: WARN -- pipeline exited with code %d", proc.returncode)

    log.info("=== Done ===")


if __name__ == "__main__":
    main()
'''

if not write_and_compile(TARGETS["scripts/debug_run_bbw_simulator.py"], DEBUG_RUN_BBW_SIMULATOR, "scripts/debug_run_bbw_simulator.py"):
    SYNTAX_FAILS.append("scripts/debug_run_bbw_simulator.py")

# =============================================================================
# SYNTAX SUMMARY
# =============================================================================

print()
n_total = len(TARGETS)
n_syntax_ok = n_total - len(SYNTAX_FAILS)
print("Syntax check: " + str(n_syntax_ok) + "/" + str(n_total) + " PASS")
if SYNTAX_FAILS:
    print("SYNTAX FAILURES: " + ", ".join(SYNTAX_FAILS))
    sys.exit(1)

# =============================================================================
# RUN TESTS
# =============================================================================

TEST_FILES = [
    ROOT / "tests" / "test_coin_classifier.py",
    ROOT / "tests" / "test_bbw_ollama_review.py",
    ROOT / "tests" / "test_run_bbw_simulator.py",
]

print()
print("Running tests...")
print("-" * 50)

total_tests = 0
total_pass = 0
test_fails = []

for tf in TEST_FILES:
    label = tf.name
    result = subprocess.run(
        [sys.executable, str(tf)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    # Count tests from unittest output
    lines = result.stdout + result.stderr
    ran = 0
    errors = 0
    for line in lines.splitlines():
        if line.startswith("Ran "):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    ran = int(parts[1])
                except ValueError:
                    pass
        if "FAILED" in line:
            for part in line.split("("):
                for sub in part.split(")"):
                    for tok in sub.split("="):
                        if "errors" in tok or "failures" in tok:
                            try:
                                num = int(sub.split("=")[-1].strip(" )"))
                                errors += num
                            except (ValueError, IndexError):
                                pass
    passed = ran - errors
    total_tests += ran
    total_pass += passed
    status = "PASS" if result.returncode == 0 else "FAIL"
    print("  " + status + "  " + label + " -- " + str(ran) + " tests, " + str(errors) + " failures")
    if result.returncode != 0:
        test_fails.append(label)
        if result.stderr:
            for ln in result.stderr.splitlines()[-8:]:
                print("    " + ln)

print()
print("Tests: " + str(total_pass) + "/" + str(total_tests) + " PASS")
if test_fails:
    print("TEST FAILURES: " + ", ".join(test_fails))
    sys.exit(1)

print()
print("=" * 70)
print("BUILD COMPLETE -- " + str(n_syntax_ok) + "/" + str(n_total) + " syntax OK, tests passed")
print("=" * 70)
print()
print("Run:")
print('  streamlit run "scripts/run_bbw_simulator.py" --dry-run')
print('  python "scripts/debug_run_bbw_simulator.py"')

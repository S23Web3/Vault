r"""
Fix known bugs in ml/ modules. Patch-only -- does NOT rewrite files from scratch.

BUG 1: ml/features.py uses wrong stochastic column names.
  Wrong: stoch_9_3_k, stoch_14_3_k, stoch_40_3_k, stoch_60_10_k
  Correct: stoch_9, stoch_14, stoch_40, stoch_60
  Source: signals/stochastics.py compute_all_stochastics()

BUG 2: ml/features.py has no _safe_col/_val helper functions.
  The code uses raw dict-style access that crashes on missing columns.

This script:
  1. Reads ml/features.py
  2. Replaces wrong column names with correct ones
  3. Creates data/output/ml/ directory
  4. Verifies the fix by importing and running

Run:  python scripts/fix_ml_features.py
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ML_DIR = ROOT / "ml"
OUTPUT_DIR = ROOT / "data" / "output" / "ml"


def check_permissions():
    """Verify write access to ml/ and data/output/ml/."""
    for d in [ML_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        test_file = d / "__write_test__"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except PermissionError:
            print(f"ERROR: No write permission to {d}")
            sys.exit(1)
    print(f"  ml/ dir:     {ML_DIR} (writable)")
    print(f"  output dir:  {OUTPUT_DIR} (writable)")


def fix_column_names():
    """Fix stochastic column names in ml/features.py."""
    features_path = ML_DIR / "features.py"
    if not features_path.exists():
        print("  ERROR: ml/features.py not found")
        return False

    content = features_path.read_text(encoding="utf-8")
    original = content

    # Column name replacements
    replacements = {
        '"stoch_9_3_k"': '"stoch_9"',
        '"stoch_14_3_k"': '"stoch_14"',
        '"stoch_40_3_k"': '"stoch_40"',
        '"stoch_60_10_k"': '"stoch_60"',
        "'stoch_9_3_k'": "'stoch_9'",
        "'stoch_14_3_k'": "'stoch_14'",
        "'stoch_40_3_k'": "'stoch_40'",
        "'stoch_60_10_k'": "'stoch_60'",
    }

    changes = 0
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            changes += 1

    if changes > 0:
        features_path.write_text(content, encoding="utf-8")
        print(f"  Fixed {changes} column name references in ml/features.py")
    else:
        # Check if already correct
        if '"stoch_9"' in content or "'stoch_9'" in content:
            print("  Column names already correct in ml/features.py")
        else:
            print("  WARNING: Could not find column names to fix")
            return False

    return True


def verify_fix():
    """Import ml/features.py and verify it works with correct column names."""
    # Clear cached modules
    for mod in list(sys.modules.keys()):
        if mod.startswith("ml"):
            del sys.modules[mod]

    sys.path.insert(0, str(ROOT))

    try:
        import numpy as np
        import pandas as pd
        from ml.features import extract_trade_features, get_feature_columns

        # Synthetic OHLCV with CORRECT column names
        n = 100
        np.random.seed(42)
        close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
        ohlcv = pd.DataFrame({
            "open": close, "high": close + 1, "low": close - 1, "close": close,
            "base_vol": np.random.uniform(100, 10000, n),
            "atr": np.random.uniform(0.5, 3.0, n),
            "stoch_9": np.random.uniform(0, 100, n),
            "stoch_14": np.random.uniform(0, 100, n),
            "stoch_40": np.random.uniform(0, 100, n),
            "stoch_60": np.random.uniform(0, 100, n),
            "ema34": close + 0.5, "ema50": close - 0.5,
            "cloud3_bull": np.random.choice([True, False], n),
            "price_pos": np.random.choice([-1, 0, 1], n),
        })
        dates = pd.date_range("2025-11-01", periods=n, freq="5min", tz="UTC")
        ohlcv["datetime"] = dates

        # Synthetic trades
        trades = pd.DataFrame([{
            "direction": "LONG", "grade": "A",
            "entry_bar": 10, "exit_bar": 15,
            "entry_price": 100, "exit_price": 103,
            "sl_price": 98, "tp_price": 103,
            "pnl": 30, "commission": 16,
            "mfe": 35, "mae": -5, "exit_reason": "TP",
            "saw_green": True, "be_raised": False,
        }])

        feats = extract_trade_features(trades, ohlcv)

        # Verify correct columns exist
        assert "stoch_9" in feats.columns, f"stoch_9 missing. Got: {list(feats.columns)}"
        assert "stoch_14" in feats.columns, "stoch_14 missing"
        assert "atr_pct" in feats.columns, "atr_pct missing"
        assert len(feats) == 1, f"Expected 1 row, got {len(feats)}"

        # Verify old wrong names are gone
        for bad in ["stoch_9_3_k", "stoch_14_3_k", "stoch_40_3_k", "stoch_60_10_k"]:
            assert bad not in feats.columns, f"Old column name still present: {bad}"

        cols = get_feature_columns()
        print(f"  Verified: {len(feats.columns)} feature columns extracted")
        print(f"  Feature list: {cols}")
        return True

    except Exception as e:
        print(f"  VERIFY FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("  FIX ML FEATURES -- Column Name Patch")
    print("=" * 60)

    t0 = time.time()

    check_permissions()

    print("\n[1] Fixing column names...")
    if not fix_column_names():
        sys.exit(1)

    print("\n[2] Verifying fix...")
    if not verify_fix():
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n  Done in {elapsed:.1f}s")
    print("  ml/features.py is patched and verified.")


if __name__ == "__main__":
    main()

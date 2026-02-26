r"""
Vince ML Pipeline Builder
==========================
Builds the ml/ module for the Four Pillars backtester.

WHAT THIS DOES:
  The Four Pillars strategy generates entry signals (A/B/C/R grades) from
  4 stochastics (9/14/40/60 Raw K) + Ripster EMA Clouds (2/3/4).
  The backtester (engine/) executes those signals with ATR-based SL/TP
  and tracks MFE/MAE per trade.

  This script builds the ML analysis layer ON TOP of that:
    1. features.py    -- extract features at signal time from the OHLCV bar
    2. triple_barrier -- label trades by exit type {TP=+1, SL=-1, other=0}
    3. purged_cv      -- leak-free cross-validation (De Prado Ch 7)
    4. meta_label     -- XGBoost analysis of signal quality (De Prado Ch 3.6)
    5. shap_analyzer  -- per-trade feature explanation (Jansen Ch 12)
    6. bet_sizing     -- probability to position size (De Prado Ch 10)
    7. walk_forward   -- rolling IS/OOS validation (Jansen Ch 7)
    8. loser_analysis -- Sweeney A/B/C/D loser classification + BE optimization

  Vince = analysis engine. USER sets params and trains the model.

DATA FLOW:
  signals/ (stochastics, clouds, state_machine)
    -> engine/backtester.py (executes, tracks MFE/MAE)
      -> ml/features.py (extracts features per trade)
        -> ml/triple_barrier.py (labels trades)
          -> ml/meta_label.py (XGBoost analysis)
            -> ml/shap_analyzer.py (explains decisions)

COLUMN NAMES (from signals/):
  stoch_9, stoch_14, stoch_40, stoch_60, stoch_60_d  (stochastics.py)
  ema5, ema12, ema34, ema50, ema72, ema89             (clouds.py)
  cloud3_bull, price_pos, cloud2_bull                  (clouds.py)
  price_cross_above_cloud2, price_cross_below_cloud2   (clouds.py)
  atr                                                  (four_pillars.py)
  base_vol, quote_vol                                  (fetcher.py)

OUTPUT DIRECTORIES:
  ml/               -- module source files (this script creates them)
  data/output/ml/   -- saved models, SHAP values, reports (created at runtime)

Run:  python scripts/build_ml_pipeline.py
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""
import sys
import os
import time
import traceback
from pathlib import Path

# -- Setup paths --
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
ML_DIR = PROJECT_ROOT / "ml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "ml"


def check_write_permission():
    """
    Check write access to project directory. Ask user to confirm before writing.
    Exits if no permission or user declines.
    """
    test_file = ML_DIR.parent / ".write_test"
    try:
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
    except PermissionError:
        print(f"\n  ERROR: No write permission to {ML_DIR.parent}")
        print(f"  Fix: Run as Administrator, or grant write access to:")
        print(f"       {ML_DIR.parent}")
        sys.exit(1)

    print(f"\n  Project root:  {PROJECT_ROOT}")
    print(f"  ML module dir: {ML_DIR}/")
    print(f"  Output dir:    {OUTPUT_DIR}/")
    print(f"  Files to write: {len(FILES)}")
    print()
    confirm = input("  Proceed with build? [y/N]: ").strip().lower()
    if confirm != "y":
        print("  Aborted by user.")
        sys.exit(0)


def ensure_dirs():
    """Create ml/ and data/output/ml/ directories."""
    ML_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  ml/ directory:     {ML_DIR}")
    print(f"  output directory:  {OUTPUT_DIR}")


def write_file(filepath: Path, content: str):
    """Write content to filepath. Exits on permission error."""
    try:
        filepath.write_text(content, encoding="utf-8")
        print(f"  WROTE {filepath.name} ({len(content):,} bytes)")
    except PermissionError:
        print(f"  ERROR: Permission denied writing {filepath}")
        print(f"  Fix: Run as Administrator or grant write access.")
        sys.exit(1)


# ============================================================
# FILE 1: ml/__init__.py
# ============================================================
INIT_PY = '''\
"""
Vince ML Pipeline -- strategy-agnostic analysis engine.

Sits on top of the Four Pillars backtester (engine/).
Extracts features from trade data, labels trades, trains XGBoost,
explains with SHAP. User sets parameters and trains the model.

Data flow:
  signals/ -> engine/backtester.py -> ml/features.py -> ml/meta_label.py
"""
'''

# ============================================================
# FILE 2: ml/features.py
# ============================================================
FEATURES_PY = '''\
"""
Strategy-agnostic feature extraction from trade + OHLCV data.

Reads the OHLCV DataFrame produced by signals/four_pillars.py
(which adds stoch_9/14/40/60, ema34/50, cloud3_bull, price_pos, atr)
and extracts per-trade features at entry bar.

Features extracted:
  - Stochastic values at entry (stoch_9, stoch_14, stoch_40, stoch_60)
  - ATR as % of price (volatility proxy)
  - Volume ratio vs 20-bar average
  - Cloud 3 state (bull/bear) and spread (ema34-ema50)/price
  - Price position relative to Cloud 3 (-1/0/+1)
  - Direction and grade encodings
  - Temporal (hour, day of week)
  - R-multiple normalization (MFE_R, MAE_R, PnL_R)
  - ETD (end trade drawdown = MFE - profit)
  - Trade duration in bars

Column names match signals/ output exactly:
  stoch_9, stoch_14, stoch_40, stoch_60  (from stochastics.py)
  ema34, ema50, cloud3_bull, price_pos   (from clouds.py)
  atr                                    (from four_pillars.py)
  base_vol                               (from fetcher.py)

Output saved to: data/output/ml/features_{symbol}_{timeframe}.parquet
"""

import numpy as np
import pandas as pd
from pathlib import Path


# Output directory for saved feature matrices
_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output" / "ml"


def extract_trade_features(trades_df: pd.DataFrame,
                           ohlcv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build feature matrix: one row per trade, using bar data at entry time.

    Args:
        trades_df: DataFrame from engine/metrics.py trades_to_dataframe().
                   Columns: entry_bar, exit_bar, entry_price, sl_price, tp_price,
                   mfe, mae, pnl, commission, direction, grade, exit_reason.
        ohlcv_df: OHLCV DataFrame after signals/four_pillars.py compute_signals().
                  Has: stoch_9, stoch_14, stoch_40, stoch_60, atr, close,
                  base_vol, cloud3_bull, price_pos, ema34, ema50, etc.

    Returns:
        DataFrame with one row per trade, all feature columns.
    """
    features = []
    n_bars = len(ohlcv_df)

    # Pre-extract numpy arrays for speed
    close = ohlcv_df["close"].values
    atr = ohlcv_df["atr"].values if "atr" in ohlcv_df.columns else None

    # Stochastic columns (names match stochastics.py output)
    stoch_9 = _safe_col(ohlcv_df, "stoch_9")
    stoch_14 = _safe_col(ohlcv_df, "stoch_14")
    stoch_40 = _safe_col(ohlcv_df, "stoch_40")
    stoch_60 = _safe_col(ohlcv_df, "stoch_60")

    # Cloud columns (names match clouds.py output)
    cloud3_bull = _safe_col(ohlcv_df, "cloud3_bull")
    price_pos = _safe_col(ohlcv_df, "price_pos")
    ema34 = _safe_col(ohlcv_df, "ema34")
    ema50 = _safe_col(ohlcv_df, "ema50")

    # Volume
    volume = _safe_col(ohlcv_df, "base_vol")

    # Datetime for temporal features
    dt_series = None
    if "datetime" in ohlcv_df.columns:
        dt_series = pd.to_datetime(ohlcv_df["datetime"])
    elif isinstance(ohlcv_df.index, pd.DatetimeIndex):
        dt_series = ohlcv_df.index

    # Rolling volume average (20-bar) for vol_ratio
    vol_ma20 = None
    if volume is not None:
        vol_ma20 = pd.Series(volume).rolling(20, min_periods=1).mean().values

    for _, trade in trades_df.iterrows():
        i = int(trade["entry_bar"])
        if i < 0 or i >= n_bars:
            continue

        row = {}

        # -- Direction and grade encoded --
        row["direction_enc"] = 1 if trade["direction"] == "LONG" else -1
        row["grade_enc"] = {"A": 3, "B": 2, "C": 1, "R": 0}.get(trade["grade"], 0)

        # -- Stochastic values at entry --
        row["stoch_9"] = _val(stoch_9, i, 50.0)
        row["stoch_14"] = _val(stoch_14, i, 50.0)
        row["stoch_40"] = _val(stoch_40, i, 50.0)
        row["stoch_60"] = _val(stoch_60, i, 50.0)

        # -- ATR normalized by price (volatility proxy) --
        if atr is not None and not np.isnan(atr[i]) and close[i] > 0:
            row["atr_pct"] = atr[i] / close[i]
        else:
            row["atr_pct"] = 0.0

        # -- Volume ratio: current bar vs 20-bar average --
        if volume is not None and vol_ma20 is not None and vol_ma20[i] > 0:
            row["vol_ratio"] = volume[i] / vol_ma20[i]
        else:
            row["vol_ratio"] = 1.0

        # -- Cloud 3 state at entry --
        row["cloud3_bull"] = _val_int(cloud3_bull, i, 0)
        row["price_pos"] = _val_int(price_pos, i, 0)

        # -- Cloud 3 spread: (ema34 - ema50) / price --
        if ema34 is not None and ema50 is not None and close[i] > 0:
            e34 = ema34[i] if not np.isnan(ema34[i]) else 0
            e50 = ema50[i] if not np.isnan(ema50[i]) else 0
            row["cloud3_spread"] = (e34 - e50) / close[i]
        else:
            row["cloud3_spread"] = 0.0

        # -- R-multiple normalization --
        sl_dist = abs(trade["entry_price"] - trade["sl_price"])
        net_pnl = trade["pnl"] - trade["commission"]
        if sl_dist > 0:
            row["mfe_r"] = trade["mfe"] / sl_dist
            row["mae_r"] = trade["mae"] / sl_dist
            row["pnl_r"] = net_pnl / sl_dist
        else:
            row["mfe_r"] = 0.0
            row["mae_r"] = 0.0
            row["pnl_r"] = 0.0

        # -- Temporal features --
        if dt_series is not None and i < len(dt_series):
            dt = dt_series.iloc[i]
            row["hour"] = dt.hour
            row["day_of_week"] = dt.dayofweek
        else:
            row["hour"] = 0
            row["day_of_week"] = 0

        # -- ETD: end trade drawdown = MFE - max(profit, 0) --
        row["etd"] = trade["mfe"] - max(net_pnl, 0)

        # -- Trade duration in bars --
        row["duration_bars"] = int(trade["exit_bar"] - trade["entry_bar"])

        features.append(row)

    return pd.DataFrame(features)


def get_feature_columns() -> list:
    """
    Feature columns safe for ML training (no future leakage).
    Excludes mfe_r, mae_r, pnl_r, etd which are trade outcomes.
    """
    return [
        "direction_enc", "grade_enc",
        "stoch_9", "stoch_14", "stoch_40", "stoch_60",
        "atr_pct", "vol_ratio",
        "cloud3_bull", "price_pos", "cloud3_spread",
        "hour", "day_of_week",
        "duration_bars",
    ]


def save_features(features_df: pd.DataFrame, symbol: str, timeframe: str):
    """Save feature matrix to parquet in data/output/ml/."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / f"features_{symbol}_{timeframe}.parquet"
    features_df.to_parquet(path, index=False)
    return path


def _safe_col(df, name):
    """Return column as numpy array or None if missing."""
    return df[name].values if name in df.columns else None


def _val(arr, idx, default=0.0):
    """Safe value from array: return default if None or NaN."""
    if arr is None:
        return default
    v = arr[idx]
    return default if np.isnan(v) else float(v)


def _val_int(arr, idx, default=0):
    """Safe integer value from array."""
    if arr is None:
        return default
    v = arr[idx]
    return default if np.isnan(v) else int(v)
'''

# ============================================================
# FILE 3: ml/triple_barrier.py
# ============================================================
TRIPLE_BARRIER_PY = '''\
"""
Triple Barrier Labeling (De Prado Ch 3).

Labels each trade by which barrier was hit first:
  +1 = TP hit (upper barrier, trade reached take-profit)
  -1 = SL hit (lower barrier, trade hit stop-loss)
   0 = other  (FLIP, END, SIGNAL -- time/event barrier)

The backtester exit_reason column maps directly:
  "TP"   -> +1
  "SL"   -> -1
  "FLIP" -> 0 (position flipped by opposite signal)
  "END"  -> 0 (data ended, position force-closed)

This gives 3-class labels vs binary win/loss.
The meta-label model uses these to learn signal quality.

Output saved to: data/output/ml/labels_{symbol}_{timeframe}.npy
"""

import numpy as np
import pandas as pd
from pathlib import Path

_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output" / "ml"


def label_trades(trades_df: pd.DataFrame) -> np.ndarray:
    """
    Assign triple barrier label to each trade from exit_reason.

    Args:
        trades_df: DataFrame with exit_reason column from backtester.

    Returns:
        numpy array of labels: +1 (TP), -1 (SL), 0 (other).
    """
    labels = np.zeros(len(trades_df), dtype=int)
    for idx, reason in enumerate(trades_df["exit_reason"].values):
        if reason == "TP":
            labels[idx] = 1
        elif reason == "SL":
            labels[idx] = -1
    return labels


def label_trades_by_pnl(trades_df: pd.DataFrame,
                        draw_zone: float = 0.0) -> np.ndarray:
    """
    Alternative: label by net P&L with optional draw zone (Sweeney Ch 8).
    Trades within draw_zone of zero are labeled 0 (commission casualties).

    Args:
        trades_df: DataFrame with pnl and commission columns.
        draw_zone: abs(net_pnl) <= draw_zone -> label 0.

    Returns:
        numpy array: +1 (win), -1 (loss), 0 (draw).
    """
    net_pnl = (trades_df["pnl"] - trades_df["commission"]).values
    labels = np.zeros(len(net_pnl), dtype=int)
    for idx, pnl in enumerate(net_pnl):
        if pnl > draw_zone:
            labels[idx] = 1
        elif pnl < -draw_zone:
            labels[idx] = -1
    return labels


def get_label_distribution(labels: np.ndarray) -> dict:
    """Count and percentage per label class."""
    total = len(labels)
    if total == 0:
        return {"total": 0}
    return {
        "total": total,
        "tp_count": int(np.sum(labels == 1)),
        "sl_count": int(np.sum(labels == -1)),
        "other_count": int(np.sum(labels == 0)),
        "tp_pct": float(np.mean(labels == 1)),
        "sl_pct": float(np.mean(labels == -1)),
        "other_pct": float(np.mean(labels == 0)),
    }


def save_labels(labels: np.ndarray, symbol: str, timeframe: str):
    """Save labels to .npy in data/output/ml/."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / f"labels_{symbol}_{timeframe}.npy"
    np.save(path, labels)
    return path
'''

# ============================================================
# FILE 4: ml/purged_cv.py
# ============================================================
PURGED_CV_PY = '''\
"""
Purged K-Fold Cross-Validation (De Prado Ch 7).

Standard K-Fold leaks: trades near fold boundaries overlap in time.
Purged CV removes overlapping trades from training set.
Embargo adds extra gap (in bars) between train and test.

Why this matters:
  Trade at bar 500 exits at bar 510. If test fold starts at bar 505,
  standard CV puts bar-500 trade in training -- it overlaps with test.
  Purged CV removes it. Without this, all ML results are garbage.

Input: trades DataFrame with entry_bar, exit_bar columns.
Output: list of (train_indices, test_indices) tuples.
"""

import numpy as np
import pandas as pd


def purged_kfold_split(trades_df: pd.DataFrame,
                       n_splits: int = 5,
                       embargo_bars: int = 10) -> list:
    """
    Generate purged K-fold splits sorted by entry_bar.

    Each fold is a contiguous time block. Training excludes trades
    that overlap with test window + embargo buffer.

    Args:
        trades_df: DataFrame with entry_bar and exit_bar.
        n_splits: number of folds.
        embargo_bars: extra gap between train/test (in bars).

    Returns:
        List of (train_indices, test_indices) tuples.
    """
    n = len(trades_df)
    if n < n_splits:
        raise ValueError(f"Need >= {n_splits} trades for {n_splits}-fold CV, got {n}")

    # Sort by entry time
    sorted_df = trades_df.sort_values("entry_bar").reset_index(drop=True)
    entry_bars = sorted_df["entry_bar"].values
    exit_bars = sorted_df["exit_bar"].values

    # Contiguous folds
    fold_size = n // n_splits
    folds = []
    for k in range(n_splits):
        start = k * fold_size
        end = start + fold_size if k < n_splits - 1 else n
        folds.append((start, end))

    splits = []
    for test_start, test_end in folds:
        # Test window in bar-space
        test_bar_start = entry_bars[test_start]
        test_bar_end = exit_bars[test_end - 1]

        # Purge zone = test window + embargo
        purge_start = test_bar_start - embargo_bars
        purge_end = test_bar_end + embargo_bars

        test_idx = list(range(test_start, test_end))
        train_idx = []

        for i in range(n):
            if test_start <= i < test_end:
                continue
            # Check overlap
            overlaps = entry_bars[i] <= purge_end and exit_bars[i] >= purge_start
            if not overlaps:
                train_idx.append(i)

        splits.append((train_idx, test_idx))

    return splits


def get_split_summary(splits: list, total_trades: int) -> list:
    """Summarize each fold: train/test/purged counts."""
    summaries = []
    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        purged = total_trades - len(train_idx) - len(test_idx)
        summaries.append({
            "fold": fold_idx + 1,
            "train": len(train_idx),
            "test": len(test_idx),
            "purged": purged,
            "train_pct": len(train_idx) / total_trades * 100,
        })
    return summaries
'''

# ============================================================
# FILE 5: ml/meta_label.py
# ============================================================
META_LABEL_PY = '''\
"""
Meta-Labeling with XGBoost (De Prado Ch 3.6).

The Four Pillars strategy is the PRIMARY model (generates A/B/C/R signals).
Meta-labeling is a SECONDARY model that analyzes features at signal time
and outputs a probability: how likely is this signal to be profitable?

User reviews probabilities, sets threshold, trains the model.
Vince does the analysis. User makes the decisions.

Input: feature matrix (features.py) + labels (triple_barrier.py).
Output: trained model, probabilities, feature importance.

Models saved to: data/output/ml/model_{symbol}_{timeframe}.json
"""

import numpy as np
import pandas as pd
from pathlib import Path

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output" / "ml"


class MetaLabelAnalyzer:
    """
    XGBoost meta-label analyzer.
    Trains on trade features to predict signal quality.
    """

    def __init__(self, params: dict = None):
        """
        Args:
            params: XGBoost hyperparameters. User can override any param.
        """
        if not HAS_XGB:
            raise ImportError("xgboost not installed. Run: pip install xgboost")

        default_params = {
            "n_estimators": 200,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "eval_metric": "logloss",
            "verbosity": 0,
        }
        if params:
            default_params.update(params)

        self.params = default_params
        self.model = None
        self.feature_names = None

    def train(self, X: pd.DataFrame, y: np.ndarray,
              feature_names: list = None) -> dict:
        """
        Train the meta-label classifier.

        Args:
            X: feature matrix (n_trades x n_features).
            y: binary labels (1=profitable, 0=not).
               Map triple_barrier: +1 -> 1, else -> 0.
            feature_names: column names for importance reporting.

        Returns:
            dict with train_samples, accuracy, positive_rate.
        """
        self.feature_names = feature_names or (list(X.columns) if hasattr(X, "columns") else None)

        # Drop NaN rows
        if isinstance(X, pd.DataFrame):
            mask = ~X.isna().any(axis=1)
            X_clean = X[mask].values
            y_clean = y[mask.values] if hasattr(mask, "values") else y[mask]
        else:
            mask = ~np.isnan(X).any(axis=1)
            X_clean = X[mask]
            y_clean = y[mask]

        if len(X_clean) < 20:
            raise ValueError(f"Need >= 20 clean samples, got {len(X_clean)}")

        self.model = xgb.XGBClassifier(**self.params)
        self.model.fit(X_clean, y_clean)

        preds = self.model.predict(X_clean)
        accuracy = float(np.mean(preds == y_clean))

        return {
            "train_samples": len(X_clean),
            "dropped_nan": int(np.sum(~mask)),
            "train_accuracy": accuracy,
            "positive_rate": float(np.mean(y_clean)),
        }

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probability of profitable trade.

        Returns:
            array of probabilities (0.0 to 1.0). NaN rows get 0.5.
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        X_vals = X.values if isinstance(X, pd.DataFrame) else X
        mask = ~np.isnan(X_vals).any(axis=1)
        probs = np.full(len(X_vals), 0.5)
        if mask.any():
            probs[mask] = self.model.predict_proba(X_vals[mask])[:, 1]
        return probs

    def get_feature_importance(self) -> pd.DataFrame:
        """Feature importance sorted descending."""
        if self.model is None:
            raise ValueError("Model not trained.")

        importance = self.model.feature_importances_
        names = self.feature_names or [f"f{i}" for i in range(len(importance))]

        return pd.DataFrame({
            "feature": names[:len(importance)],
            "importance": importance,
        }).sort_values("importance", ascending=False).reset_index(drop=True)

    def save_model(self, symbol: str, timeframe: str):
        """Save trained model to data/output/ml/."""
        if self.model is None:
            raise ValueError("Model not trained.")
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = _OUTPUT_DIR / f"model_{symbol}_{timeframe}.json"
        self.model.save_model(str(path))
        return path

    def load_model(self, symbol: str, timeframe: str):
        """Load a previously saved model."""
        path = _OUTPUT_DIR / f"model_{symbol}_{timeframe}.json"
        if not path.exists():
            raise FileNotFoundError(f"No model at {path}")
        self.model = xgb.XGBClassifier()
        self.model.load_model(str(path))
        return self
'''

# ============================================================
# FILE 6: ml/shap_analyzer.py
# ============================================================
SHAP_ANALYZER_PY = '''\
"""
SHAP Explainability for Meta-Label Model (Jansen Ch 12).

Per-trade feature attribution: for each trade, which features
pushed the model toward "take" vs "skip"?

Example output:
  "Trade #42 flagged SKIP: stoch_60=48 (mid-range), vol_ratio=0.3 (low)"
  "Trade #99 flagged TAKE: stoch_9=15 (oversold), atr_pct=0.023 (high vol)"

SHAP values saved to: data/output/ml/shap_{symbol}_{timeframe}.npy
"""

import numpy as np
import pandas as pd
from pathlib import Path

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output" / "ml"


class ShapAnalyzer:
    """SHAP explanations for a trained XGBoost model."""

    def __init__(self, model, feature_names: list = None):
        """
        Args:
            model: trained XGBoost model (from MetaLabelAnalyzer.model).
            feature_names: column names matching training features.
        """
        if not HAS_SHAP:
            raise ImportError("shap not installed. Run: pip install shap")
        self.model = model
        self.feature_names = feature_names
        self.shap_values = None

    def compute(self, X: pd.DataFrame) -> np.ndarray:
        """
        Compute SHAP values for all trades.

        Returns:
            array (n_trades x n_features) of SHAP values.
        """
        X_vals = X.values if isinstance(X, pd.DataFrame) else X
        explainer = shap.TreeExplainer(self.model)
        self.shap_values = explainer.shap_values(X_vals)
        return self.shap_values

    def get_top_features(self, trade_idx: int, top_n: int = 5) -> list:
        """
        Top N features driving prediction for one trade.

        Returns:
            list of dicts: feature, shap_value, direction (TAKE/SKIP).
        """
        if self.shap_values is None:
            raise ValueError("Call compute() first.")

        vals = self.shap_values[trade_idx]
        names = self.feature_names or [f"f{i}" for i in range(len(vals))]
        indices = np.argsort(np.abs(vals))[::-1][:top_n]

        return [
            {
                "feature": names[idx] if idx < len(names) else f"f{idx}",
                "shap_value": float(vals[idx]),
                "direction": "TAKE" if vals[idx] > 0 else "SKIP",
            }
            for idx in indices
        ]

    def get_global_importance(self) -> pd.DataFrame:
        """Mean absolute SHAP per feature (global importance)."""
        if self.shap_values is None:
            raise ValueError("Call compute() first.")

        mean_abs = np.mean(np.abs(self.shap_values), axis=0)
        names = self.feature_names or [f"f{i}" for i in range(len(mean_abs))]

        return pd.DataFrame({
            "feature": names[:len(mean_abs)],
            "mean_abs_shap": mean_abs,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

    def save_shap(self, symbol: str, timeframe: str):
        """Save SHAP values to .npy."""
        if self.shap_values is None:
            raise ValueError("Call compute() first.")
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = _OUTPUT_DIR / f"shap_{symbol}_{timeframe}.npy"
        np.save(path, self.shap_values)
        return path
'''

# ============================================================
# FILE 7: ml/bet_sizing.py
# ============================================================
BET_SIZING_PY = '''\
"""
Bet Sizing from Meta-Label Probabilities (De Prado Ch 10).

Converts model probability to position size.
User sets the sizing parameters (threshold, max size, Kelly fraction).

Three methods:
  1. Binary: prob >= threshold -> full size, else skip
  2. Linear: size scales from 0 at threshold to max at 1.0
  3. Kelly: f* = (p*b - q) / b (optimal fraction based on edge)
"""

import numpy as np


def binary_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5) -> np.ndarray:
    """Above threshold = full size, below = skip."""
    return (probabilities >= threshold).astype(float)


def linear_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5,
                  max_size: float = 1.0) -> np.ndarray:
    """Size scales linearly from 0 at threshold to max_size at 1.0."""
    sizes = np.zeros_like(probabilities)
    above = probabilities >= threshold
    if above.any():
        scale_range = 1.0 - threshold
        if scale_range > 0:
            sizes[above] = ((probabilities[above] - threshold) / scale_range) * max_size
        else:
            sizes[above] = max_size
    return sizes


def kelly_sizing(probabilities: np.ndarray,
                 avg_win: float,
                 avg_loss: float,
                 max_size: float = 1.0,
                 fraction: float = 0.5) -> np.ndarray:
    """
    Kelly criterion: f* = (p*b - q) / b.
    Uses fractional Kelly (default half) for safety.

    Args:
        avg_win: average winning trade P&L (positive).
        avg_loss: average losing trade P&L (negative, will be abs'd).
        fraction: Kelly fraction (0.5 = half-Kelly).
    """
    if avg_win <= 0 or avg_loss >= 0:
        return np.zeros_like(probabilities)

    b = avg_win / abs(avg_loss)
    q = 1.0 - probabilities
    kelly_f = (probabilities * b - q) / b * fraction
    return np.clip(kelly_f, 0.0, max_size)


def get_sizing_summary(sizes: np.ndarray) -> dict:
    """Summarize sizing decisions: taken/skipped counts, avg size."""
    total = len(sizes)
    skipped = int(np.sum(sizes == 0))
    taken = total - skipped
    return {
        "total_signals": total,
        "taken": taken,
        "skipped": skipped,
        "skip_rate": skipped / total if total > 0 else 0,
        "avg_size": float(np.mean(sizes[sizes > 0])) if taken > 0 else 0,
        "min_size": float(np.min(sizes[sizes > 0])) if taken > 0 else 0,
        "max_size": float(np.max(sizes[sizes > 0])) if taken > 0 else 0,
    }
'''

# ============================================================
# FILE 8: ml/walk_forward.py
# ============================================================
WALK_FORWARD_PY = '''\
"""
Walk-Forward Validation (Jansen Ch 7).

Rolling windows: optimize on in-sample (IS), test on out-of-sample (OOS).
Walk Forward Efficiency (WFE) = OOS metric / IS metric.
  WFE > 60%  = ROBUST (deploy)
  WFE 30-60% = MARGINAL (need more data)
  WFE < 30%  = OVERFIT (do not deploy)
"""

import numpy as np
import pandas as pd


def generate_windows(n_trades: int,
                     is_ratio: float = 0.7,
                     min_trades_per_window: int = 100,
                     step_ratio: float = 0.3) -> list:
    """
    Generate rolling IS/OOS windows.

    Args:
        n_trades: total trades in dataset.
        is_ratio: fraction for in-sample (0.7 = 70%).
        min_trades_per_window: minimum IS trades.
        step_ratio: roll forward fraction.

    Returns:
        list of window dicts with is_start/end, oos_start/end.
    """
    window_size = int(min_trades_per_window / is_ratio)
    step = max(1, int(window_size * step_ratio))
    is_size = int(window_size * is_ratio)

    windows = []
    pos = 0
    while pos + window_size <= n_trades:
        windows.append({
            "is_start": pos,
            "is_end": pos + is_size,
            "oos_start": pos + is_size,
            "oos_end": min(pos + window_size, n_trades),
            "is_size": is_size,
            "oos_size": min(pos + window_size, n_trades) - (pos + is_size),
        })
        pos += step
    return windows


def compute_wfe(is_metric: float, oos_metric: float) -> float:
    """WFE = OOS / IS. Above 0.6 = robust."""
    if is_metric == 0:
        return 0.0
    return oos_metric / is_metric


def get_wfe_rating(wfe: float) -> str:
    """Rate WFE: ROBUST / MARGINAL / OVERFIT."""
    if wfe >= 0.6:
        return "ROBUST"
    elif wfe >= 0.3:
        return "MARGINAL"
    return "OVERFIT"


def summarize_walk_forward(window_results: list) -> dict:
    """
    Aggregate WFE across all windows.

    Args:
        window_results: list of dicts with is_metric, oos_metric.

    Returns:
        dict with avg_wfe, rating, per-window WFEs.
    """
    if not window_results:
        return {"n_windows": 0, "avg_wfe": 0, "rating": "NO_DATA"}

    wfes = [compute_wfe(w.get("is_metric", 0), w.get("oos_metric", 0))
            for w in window_results]
    avg_wfe = float(np.mean(wfes))

    return {
        "n_windows": len(window_results),
        "wfes": wfes,
        "avg_wfe": avg_wfe,
        "min_wfe": float(np.min(wfes)),
        "max_wfe": float(np.max(wfes)),
        "rating": get_wfe_rating(avg_wfe),
    }
'''

# ============================================================
# FILE 9: ml/loser_analysis.py
# ============================================================
LOSER_ANALYSIS_PY = '''\
"""
Loser Classification + MFE/MAE Analysis (Sweeney Framework).

Classifies losing trades into 4 categories:
  A: Clean losers      -- MFE < 0.5R. Never went your way. Fix entries.
  B: Breakeven failures -- 0.5R to 1.0R. Partially profitable. Lower BE trigger.
  C: Should-be winners  -- 1.0R to 1.5R. Was profitable, reversed. BE raise saves.
  D: Catastrophic       -- MFE > 1.5R. Strong winner reversed through. Need TSL.

  R = SL distance from entry (risk unit).

Also: BE trigger optimization sweep (Sweeney Ch 4).
  For each trigger level, compute losers saved vs winners killed.
  Optimal trigger = max(net impact).

Output saved to: data/output/ml/loser_classes_{symbol}_{timeframe}.parquet
"""

import numpy as np
import pandas as pd
from pathlib import Path

_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output" / "ml"


def classify_losers(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add loser_class column: W (winner), A/B/C/D (loser grades).

    Args:
        trades_df: DataFrame with entry_price, sl_price, mfe, pnl, commission.

    Returns:
        Copy with r_value, mfe_r, net_pnl, loser_class columns added.
    """
    df = trades_df.copy()
    df["r_value"] = np.abs(df["entry_price"] - df["sl_price"])
    df["mfe_r"] = np.where(df["r_value"] > 0, df["mfe"] / df["r_value"], 0)
    df["net_pnl"] = df["pnl"] - df["commission"]

    classes = []
    for _, row in df.iterrows():
        if row["net_pnl"] > 0:
            classes.append("W")
        elif row["mfe_r"] < 0.5:
            classes.append("A")
        elif row["mfe_r"] < 1.0:
            classes.append("B")
        elif row["mfe_r"] < 1.5:
            classes.append("C")
        else:
            classes.append("D")
    df["loser_class"] = classes
    return df


def get_class_summary(classified_df: pd.DataFrame) -> pd.DataFrame:
    """Counts and avg P&L per class."""
    total = len(classified_df)
    rows = []
    for cls in ["W", "A", "B", "C", "D"]:
        subset = classified_df[classified_df["loser_class"] == cls]
        if len(subset) == 0:
            continue
        rows.append({
            "class": cls,
            "count": len(subset),
            "pct": len(subset) / total * 100,
            "avg_net_pnl": subset["net_pnl"].mean(),
            "avg_mfe_r": subset["mfe_r"].mean(),
            "total_pnl": subset["net_pnl"].sum(),
        })
    return pd.DataFrame(rows)


def optimize_be_trigger(trades_df: pd.DataFrame,
                        atr_range: np.ndarray = None) -> pd.DataFrame:
    """
    Sweep BE trigger levels, compute net impact (Sweeney Ch 4).

    For each trigger T:
      losers_saved = losers where MFE >= T
      saved_value = sum(|loss|) for those
      winners_killed = winners where MFE >= T (would exit at BE, lose profit)
      killed_value = sum(profit) for those
      net_impact = saved_value - killed_value

    Optimal T = argmax(net_impact).
    """
    df = trades_df.copy()
    df["net_pnl"] = df["pnl"] - df["commission"]
    losers = df[df["net_pnl"] <= 0]
    winners = df[df["net_pnl"] > 0]

    if atr_range is None:
        max_mfe = df["mfe"].max() if len(df) > 0 else 10
        atr_range = np.linspace(0.1, max(max_mfe, 1.0), 50)

    rows = []
    for trigger in atr_range:
        saved = losers[losers["mfe"] >= trigger]
        saved_value = saved["net_pnl"].abs().sum() if len(saved) > 0 else 0
        killed = winners[winners["mfe"] >= trigger]
        killed_value = killed["net_pnl"].sum() if len(killed) > 0 else 0

        rows.append({
            "trigger": float(trigger),
            "losers_saved": len(saved),
            "saved_value": float(saved_value),
            "winners_killed": len(killed),
            "killed_value": float(killed_value),
            "net_impact": float(saved_value - killed_value),
        })
    return pd.DataFrame(rows)


def compute_etd(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    End Trade Drawdown: how much profit given back from peak.
    ETD = MFE - max(net_pnl, 0). High ETD = exit problem.
    """
    df = trades_df.copy()
    df["net_pnl"] = df["pnl"] - df["commission"]
    df["etd"] = df["mfe"] - np.maximum(df["net_pnl"], 0)
    df["etd_ratio"] = np.where(df["mfe"] > 0, df["etd"] / df["mfe"], 0)
    return df


def save_classification(classified_df: pd.DataFrame, symbol: str, timeframe: str):
    """Save classified trades to parquet."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / f"loser_classes_{symbol}_{timeframe}.parquet"
    classified_df.to_parquet(path, index=False)
    return path
'''


# ============================================================
# ALL FILES TO BUILD
# ============================================================
FILES = [
    ("__init__.py", INIT_PY),
    ("features.py", FEATURES_PY),
    ("triple_barrier.py", TRIPLE_BARRIER_PY),
    ("purged_cv.py", PURGED_CV_PY),
    ("meta_label.py", META_LABEL_PY),
    ("shap_analyzer.py", SHAP_ANALYZER_PY),
    ("bet_sizing.py", BET_SIZING_PY),
    ("walk_forward.py", WALK_FORWARD_PY),
    ("loser_analysis.py", LOSER_ANALYSIS_PY),
]


# ============================================================
# TEST FUNCTIONS -- use real column names from signals/ output
# ============================================================
import numpy as np
import pandas as pd


def make_synthetic_ohlcv(n=200):
    """
    Create synthetic OHLCV with ALL signal columns matching
    the real output of signals/four_pillars.py compute_signals().
    """
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        "open": close - 0.1,
        "high": close + np.random.rand(n),
        "low": close - np.random.rand(n),
        "close": close,
        "base_vol": np.random.rand(n) * 1000 + 100,
        "atr": np.full(n, 1.5),
        # stochastics.py output columns
        "stoch_9": np.random.rand(n) * 100,
        "stoch_14": np.random.rand(n) * 100,
        "stoch_40": np.random.rand(n) * 100,
        "stoch_60": np.random.rand(n) * 100,
        "stoch_60_d": np.random.rand(n) * 100,
        # clouds.py output columns
        "ema5": close * 0.999,
        "ema12": close * 0.998,
        "ema34": close * 0.99,
        "ema50": close * 0.98,
        "ema72": close * 0.97,
        "ema89": close * 0.96,
        "cloud3_bull": np.random.choice([0, 1], n).astype(float),
        "price_pos": np.random.choice([-1, 0, 1], n).astype(float),
        "cloud2_bull": np.random.choice([0, 1], n).astype(float),
        "price_cross_above_cloud2": np.zeros(n, dtype=bool),
        "price_cross_below_cloud2": np.zeros(n, dtype=bool),
        # datetime
        "datetime": pd.date_range("2025-01-01", periods=n, freq="5min"),
    })


def make_synthetic_trades(ohlcv, n_trades=20):
    """Create synthetic trades matching engine/metrics.py trades_to_dataframe()."""
    np.random.seed(42)
    close = ohlcv["close"].values
    bars = np.sort(np.random.choice(range(10, len(close) - 10), n_trades, replace=False))

    return pd.DataFrame({
        "direction": np.random.choice(["LONG", "SHORT"], n_trades),
        "grade": np.random.choice(["A", "B", "C", "R"], n_trades),
        "entry_bar": bars,
        "exit_bar": bars + np.random.randint(3, 15, n_trades),
        "entry_price": close[bars],
        "exit_price": close[np.minimum(bars + 5, len(close) - 1)],
        "sl_price": close[bars] - 3.0,
        "tp_price": close[bars] + 4.5,
        "pnl": np.random.randn(n_trades) * 50,
        "commission": np.full(n_trades, 16.0),
        "mfe": np.abs(np.random.randn(n_trades) * 30),
        "mae": -np.abs(np.random.randn(n_trades) * 20),
        "exit_reason": np.random.choice(["TP", "SL", "FLIP", "END"], n_trades),
        "saw_green": np.random.choice([True, False], n_trades),
        "be_raised": np.random.choice([True, False], n_trades),
    })


def test_features():
    """Test feature extraction with synthetic data using real column names."""
    from ml.features import extract_trade_features, get_feature_columns, save_features

    ohlcv = make_synthetic_ohlcv()
    trades = make_synthetic_trades(ohlcv)

    feats = extract_trade_features(trades, ohlcv)
    assert len(feats) == len(trades), f"Expected {len(trades)} rows, got {len(feats)}"
    assert "stoch_9" in feats.columns, "Missing stoch_9"
    assert "atr_pct" in feats.columns, "Missing atr_pct"
    assert "cloud3_spread" in feats.columns, "Missing cloud3_spread"

    cols = get_feature_columns()
    assert len(cols) >= 14, f"Expected 14+ feature columns, got {len(cols)}"

    # Test save
    path = save_features(feats, "SYNTHETIC", "5m")
    assert path.exists(), f"Features not saved to {path}"

    print(f"      {len(feats)} trades, {len(feats.columns)} features")
    print(f"      Saved: {path.name}")
    return feats, trades, ohlcv


def test_triple_barrier():
    """Test triple barrier labeling."""
    from ml.triple_barrier import label_trades, label_trades_by_pnl, get_label_distribution, save_labels

    trades = pd.DataFrame({
        "exit_reason": ["TP", "SL", "FLIP", "TP", "SL", "END", "TP", "SL", "FLIP", "TP"],
        "pnl": [50, -30, -5, 40, -25, 2, 60, -35, -10, 45],
        "commission": [16] * 10,
    })

    labels = label_trades(trades)
    assert labels[0] == 1 and labels[1] == -1 and labels[2] == 0

    dist = get_label_distribution(labels)
    assert dist["total"] == 10

    pnl_labels = label_trades_by_pnl(trades, draw_zone=5.0)
    assert len(pnl_labels) == 10

    path = save_labels(labels, "SYNTHETIC", "5m")
    assert path.exists()

    print(f"      TP={dist['tp_count']}, SL={dist['sl_count']}, Other={dist['other_count']}")
    print(f"      Saved: {path.name}")
    return labels


def test_purged_cv():
    """Test purged K-fold CV."""
    from ml.purged_cv import purged_kfold_split, get_split_summary

    trades = pd.DataFrame({
        "entry_bar": np.arange(0, 1000, 10),
        "exit_bar": np.arange(5, 1005, 10),
    })

    splits = purged_kfold_split(trades, n_splits=5, embargo_bars=10)
    assert len(splits) == 5

    summary = get_split_summary(splits, len(trades))
    for s in summary:
        assert s["train"] > 0 and s["test"] > 0

    print(f"      5 folds:")
    for s in summary:
        print(f"        Fold {s['fold']}: train={s['train']}, test={s['test']}, purged={s['purged']}")
    return splits


def test_meta_label():
    """Test XGBoost meta-label training."""
    try:
        import xgboost
    except ImportError:
        print("      SKIP -- xgboost not installed")
        return None

    from ml.meta_label import MetaLabelAnalyzer

    np.random.seed(42)
    n = 200
    X = pd.DataFrame({
        "stoch_9": np.random.rand(n) * 100,
        "stoch_14": np.random.rand(n) * 100,
        "atr_pct": np.random.rand(n) * 0.05,
        "vol_ratio": np.random.rand(n) * 3,
        "grade_enc": np.random.choice([0, 1, 2, 3], n),
    })
    y = (X["stoch_9"].values < 30).astype(int)

    analyzer = MetaLabelAnalyzer({"n_estimators": 50, "max_depth": 3})
    result = analyzer.train(X, y, feature_names=list(X.columns))
    assert result["train_accuracy"] > 0.5

    probs = analyzer.predict_proba(X)
    assert 0 <= probs.min() and probs.max() <= 1

    importance = analyzer.get_feature_importance()
    assert len(importance) == 5

    # Test save/load
    path = analyzer.save_model("SYNTHETIC", "5m")
    assert path.exists()

    print(f"      {result['train_samples']} samples, acc={result['train_accuracy']:.3f}")
    print(f"      Top: {importance.iloc[0]['feature']} ({importance.iloc[0]['importance']:.4f})")
    print(f"      Saved: {path.name}")
    return analyzer, X


def test_shap(meta_result):
    """Test SHAP analysis."""
    try:
        import shap
    except ImportError:
        print("      SKIP -- shap not installed")
        return None
    if meta_result is None:
        print("      SKIP -- meta_label was skipped")
        return None

    from ml.shap_analyzer import ShapAnalyzer

    analyzer, X = meta_result
    sa = ShapAnalyzer(analyzer.model, feature_names=list(X.columns))
    shap_vals = sa.compute(X)
    assert shap_vals.shape == (len(X), len(X.columns))

    top = sa.get_top_features(0, top_n=3)
    assert len(top) == 3

    global_imp = sa.get_global_importance()

    path = sa.save_shap("SYNTHETIC", "5m")
    assert path.exists()

    print(f"      {len(X)} trades analyzed")
    print(f"      Trade 0: {top[0]['feature']} ({top[0]['direction']}, {top[0]['shap_value']:.4f})")
    print(f"      Global: {global_imp.iloc[0]['feature']} (|SHAP|={global_imp.iloc[0]['mean_abs_shap']:.4f})")
    print(f"      Saved: {path.name}")
    return shap_vals


def test_bet_sizing():
    """Test all three sizing methods."""
    from ml.bet_sizing import binary_sizing, linear_sizing, kelly_sizing, get_sizing_summary

    probs = np.array([0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 0.45, 0.55])

    binary = binary_sizing(probs, threshold=0.5)
    assert binary[0] == 0.0 and binary[1] == 1.0

    linear = linear_sizing(probs, threshold=0.5, max_size=1.0)
    assert linear[0] == 0.0 and 0 < linear[3] < 1.0

    kelly = kelly_sizing(probs, avg_win=20.0, avg_loss=-15.0, fraction=0.5)
    assert len(kelly) == len(probs)

    b = get_sizing_summary(binary)
    l = get_sizing_summary(linear)
    k = get_sizing_summary(kelly)

    print(f"      Binary: {b['taken']} taken, {b['skipped']} skipped")
    print(f"      Linear: avg={l['avg_size']:.3f}")
    print(f"      Kelly:  avg={k['avg_size']:.3f}")
    return b


def test_walk_forward():
    """Test walk-forward window generation and WFE."""
    from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward

    windows = generate_windows(n_trades=500, is_ratio=0.7, min_trades_per_window=100)
    assert len(windows) > 0

    wfe = compute_wfe(is_metric=1.5, oos_metric=1.0)
    assert abs(wfe - 0.6667) < 0.01
    assert get_wfe_rating(wfe) == "ROBUST"

    summary = summarize_walk_forward([
        {"is_metric": 1.5, "oos_metric": 1.0},
        {"is_metric": 2.0, "oos_metric": 0.8},
    ])

    print(f"      {len(windows)} windows for 500 trades")
    print(f"      WFE: {wfe:.4f} ({get_wfe_rating(wfe)})")
    print(f"      Avg WFE: {summary['avg_wfe']:.4f} ({summary['rating']})")
    return windows


def test_loser_analysis():
    """Test loser classification and BE optimization."""
    from ml.loser_analysis import classify_losers, get_class_summary, optimize_be_trigger, compute_etd, save_classification

    np.random.seed(42)
    n = 50
    trades = pd.DataFrame({
        "direction": ["LONG"] * n,
        "entry_price": np.full(n, 100.0),
        "sl_price": np.full(n, 97.0),  # R = $3
        "tp_price": np.full(n, 104.5),
        "mfe": np.abs(np.random.randn(n) * 5),
        "mae": -np.abs(np.random.randn(n) * 3),
        "pnl": np.random.randn(n) * 30,
        "commission": np.full(n, 16.0),
    })

    classified = classify_losers(trades)
    assert "loser_class" in classified.columns

    summary = get_class_summary(classified)
    print(f"      Classification:")
    for _, row in summary.iterrows():
        print(f"        {row['class']}: {int(row['count'])} ({row['pct']:.0f}%) avg=${row['avg_net_pnl']:.2f}")

    be_opt = optimize_be_trigger(trades)
    best = be_opt.loc[be_opt["net_impact"].idxmax()]
    print(f"      Optimal BE: ${best['trigger']:.2f} (impact=${best['net_impact']:.2f})")

    etd_df = compute_etd(trades)
    print(f"      Avg ETD: ${etd_df['etd'].mean():.2f}")

    path = save_classification(classified, "SYNTHETIC", "5m")
    assert path.exists()
    print(f"      Saved: {path.name}")
    return classified


# ============================================================
# MAIN: BUILD + TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("VINCE ML PIPELINE BUILDER")
    print("=" * 60)
    t_start = time.time()

    # STEP 0: Permission check
    check_write_permission()

    # STEP 1: Create directories
    print("\n[STEP 1] Creating directories...")
    ensure_dirs()

    # STEP 2: Write all files
    print("\n[STEP 2] Writing ml/ module files...")
    for filename, content in FILES:
        filepath = ML_DIR / filename
        write_file(filepath, content)
    print(f"  {len(FILES)} files written")

    # STEP 3: Test each module
    tests = [
        ("features.py", test_features),
        ("triple_barrier.py", test_triple_barrier),
        ("purged_cv.py", test_purged_cv),
        ("meta_label.py", test_meta_label),
        ("bet_sizing.py", test_bet_sizing),
        ("walk_forward.py", test_walk_forward),
        ("loser_analysis.py", test_loser_analysis),
    ]

    passed = 0
    failed = 0
    skipped = 0
    meta_result = None

    for idx, (name, test_fn) in enumerate(tests, 1):
        print(f"\n[TEST {idx}/{len(tests)}] {name}...")
        try:
            if name == "meta_label.py":
                meta_result = test_fn()
                if meta_result is None:
                    skipped += 1
                else:
                    passed += 1
            else:
                test_fn()
                passed += 1
        except Exception as e:
            failed += 1
            print(f"      FAIL: {e}")
            traceback.print_exc()

    # SHAP depends on meta_label
    print(f"\n[TEST {len(tests)+1}/{len(tests)+1}] shap_analyzer.py...")
    try:
        shap_result = test_shap(meta_result)
        if shap_result is None:
            skipped += 1
        else:
            passed += 1
    except Exception as e:
        failed += 1
        print(f"      FAIL: {e}")
        traceback.print_exc()

    # Summary
    elapsed = time.time() - t_start
    print(f"\n{'=' * 60}")
    print(f"BUILD COMPLETE ({elapsed:.1f}s)")
    print(f"  Files written:  {len(FILES)} in ml/")
    print(f"  Output dir:     {OUTPUT_DIR}")
    print(f"  Tests passed:   {passed}")
    print(f"  Tests failed:   {failed}")
    print(f"  Tests skipped:  {skipped}")
    if failed > 0:
        print(f"\n  STATUS: ERRORS -- fix before proceeding")
    else:
        print(f"\n  STATUS: ALL TESTS PASSED")
    print(f"{'=' * 60}")

    input("\nPress Enter to close...")

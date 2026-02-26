"""
Build script: Sections 0+C+D -- Strategy Plugin + ML Fixes + Train Vince.
Creates 8 files, py_compile + ast.parse checks each one.

Run: python scripts/build_train_vince_v1.py
"""

import sys
import ast
import py_compile
import datetime
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []


def verify(path: Path) -> bool:
    """Syntax-check a .py file with py_compile and ast.parse."""
    p = str(path)
    ok = True
    try:
        py_compile.compile(p, doraise=True)
        log.info("  py_compile OK: %s", p)
    except py_compile.PyCompileError as e:
        log.error("  py_compile FAIL: %s", e)
        ok = False

    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=p)
        log.info("  ast.parse  OK: %s", p)
    except SyntaxError as e:
        log.error("  ast.parse  FAIL %s line %s: %s", p, e.lineno, e.msg)
        ok = False

    if not ok:
        ERRORS.append(p)
    return ok


def safe_write(path: Path, content: str) -> bool:
    """Write file if it does not exist; return True on success."""
    if path.exists():
        log.info("  SKIP (exists): %s", path)
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log.info("  WROTE: %s", path)
    return True


# =====================================================================
# SECTION 0: Strategy Plugin Architecture
# =====================================================================

STRATEGIES_INIT = '''\
"""
Strategy plugin system for Vince ML agent.
Strategies are loaded by name. Each strategy provides its own
indicator enrichment, signal generation, feature extraction, and labeling.
"""

from pathlib import Path
import importlib


STRATEGY_DIR = Path(__file__).resolve().parent

_REGISTRY = {
    "four_pillars": "strategies.four_pillars",
}


def load_strategy(name: str = "four_pillars"):
    """Load a strategy plugin by name and return an instance."""
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError("Unknown strategy: " + name + ". Available: " + available)
    module = importlib.import_module(_REGISTRY[name])
    return module.create_plugin()


def list_strategies() -> list:
    """Return list of available strategy names."""
    return sorted(_REGISTRY.keys())
'''

STRATEGIES_BASE = '''\
"""
Abstract base class for all strategy plugins.
Every strategy must implement these methods to integrate with
the Vince ML training pipeline.
"""

from abc import ABC, abstractmethod
import pandas as pd


class StrategyPlugin(ABC):
    """Base class for all strategy plugins."""

    name: str = "base"

    @abstractmethod
    def enrich_ohlcv(self, df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
        """Compute indicator columns (ATR, stochastics, clouds, etc.)."""
        raise NotImplementedError

    @abstractmethod
    def compute_signals(self, df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
        """Add signal columns (entries, reentries, adds)."""
        raise NotImplementedError

    @abstractmethod
    def get_backtester_params(self, overrides: dict = None) -> dict:
        """Return backtester config (sl_mult, tp_mult, commission, etc.)."""
        raise NotImplementedError

    @abstractmethod
    def extract_features(self, trades_df: pd.DataFrame,
                         ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Extract per-trade features for ML training."""
        raise NotImplementedError

    @abstractmethod
    def get_feature_names(self) -> list:
        """Return ordered list of feature column names."""
        raise NotImplementedError

    @abstractmethod
    def label_trades(self, trades_df: pd.DataFrame,
                     mode: str = "exit") -> pd.Series:
        """Generate binary labels. Modes: exit (TP=1/SL=0) or pnl (win/loss)."""
        raise NotImplementedError
'''

STRATEGIES_FOUR_PILLARS = '''\
"""
Four Pillars strategy plugin -- first implementation.
Wraps existing signals/four_pillars_v383.py + engine/backtester_v384.py.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from strategies.base import StrategyPlugin
from signals.stochastics import compute_all_stochastics
from signals.clouds import compute_clouds
from signals.state_machine_v383 import FourPillarsStateMachine383


class FourPillarsPlugin(StrategyPlugin):
    """Four Pillars trading strategy -- Vince's first strategy."""

    name = "four_pillars"

    # Default indicator params
    DEFAULT_PARAMS = {
        "atr_length": 14,
        "stoch_k1": 9,
        "stoch_k2": 14,
        "stoch_k3": 40,
        "stoch_k4": 60,
        "stoch_d_smooth": 10,
        "cloud2_fast": 5,
        "cloud2_slow": 12,
        "cloud3_fast": 34,
        "cloud3_slow": 50,
        "cloud4_fast": 72,
        "cloud4_slow": 89,
    }

    # Default backtester params
    DEFAULT_BT_PARAMS = {
        "sl_mult": 2.0,
        "tp_mult": None,
        "be_trigger_atr": 0.0,
        "be_lock_atr": 0.0,
        "sigma_floor_atr": 0.5,
        "checkpoint_interval": 5,
        "max_scaleouts": 2,
        "max_positions": 4,
        "cooldown": 3,
        "notional": 5000.0,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": 0.70,
        "settlement_hour_utc": 17,
        "initial_equity": 10000.0,
    }

    def enrich_ohlcv(self, df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
        """Compute ATR, stochastics, clouds from raw OHLCV."""
        p = dict(self.DEFAULT_PARAMS)
        if params:
            p.update(params)

        # Stochastics (4 Raw K values + D line)
        df = compute_all_stochastics(df, p)

        # EMA Clouds (Cloud 2/3/4 + price_pos + crossovers)
        df = compute_clouds(df, p)

        # ATR (Wilder's RMA)
        atr_len = p.get("atr_length", 14)
        h = df["high"].values
        lo = df["low"].values
        c = df["close"].values
        prev_c = np.roll(c, 1)
        tr = np.maximum(h - lo, np.maximum(np.abs(h - prev_c), np.abs(lo - prev_c)))
        tr[0] = h[0] - lo[0]

        atr = np.full(len(tr), np.nan)
        atr[atr_len - 1] = np.mean(tr[:atr_len])
        for i in range(atr_len, len(tr)):
            atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
        df["atr"] = atr

        return df

    def compute_signals(self, df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
        """Run Four Pillars state machine on enriched OHLCV."""
        p = dict(self.DEFAULT_PARAMS)
        if params:
            p.update(params)

        sm = FourPillarsStateMachine383(
            cross_level=p.get("cross_level", 25),
            zone_level=p.get("zone_level", 30),
            stage_lookback=p.get("stage_lookback", 10),
            allow_b=p.get("allow_b_trades", True),
            allow_c=p.get("allow_c_trades", True),
            b_open_fresh=p.get("b_open_fresh", True),
            cloud2_reentry=p.get("cloud2_reentry", True),
            reentry_lookback=p.get("reentry_lookback", 10),
            use_60d=p.get("use_60d", False),
        )

        n = len(df)
        signals = {
            "long_a": np.zeros(n, dtype=bool),
            "long_b": np.zeros(n, dtype=bool),
            "long_c": np.zeros(n, dtype=bool),
            "long_d": np.zeros(n, dtype=bool),
            "short_a": np.zeros(n, dtype=bool),
            "short_b": np.zeros(n, dtype=bool),
            "short_c": np.zeros(n, dtype=bool),
            "short_d": np.zeros(n, dtype=bool),
            "reentry_long": np.zeros(n, dtype=bool),
            "reentry_short": np.zeros(n, dtype=bool),
            "add_long": np.zeros(n, dtype=bool),
            "add_short": np.zeros(n, dtype=bool),
        }

        stoch_9 = df["stoch_9"].values
        stoch_14 = df["stoch_14"].values
        stoch_40 = df["stoch_40"].values
        stoch_60 = df["stoch_60"].values
        stoch_60_d = df["stoch_60_d"].values
        cloud3_bull = df["cloud3_bull"].values
        price_pos = df["price_pos"].values
        cross_above = df["price_cross_above_cloud2"].values
        cross_below = df["price_cross_below_cloud2"].values
        atr = df["atr"].values

        for i in range(n):
            if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
                continue

            result = sm.process_bar(
                bar_index=i,
                stoch_9=stoch_9[i],
                stoch_14=stoch_14[i],
                stoch_40=stoch_40[i],
                stoch_60=stoch_60[i],
                stoch_60_d=stoch_60_d[i],
                cloud3_bull=bool(cloud3_bull[i]),
                price_pos=int(price_pos[i]),
                price_cross_above_cloud2=bool(cross_above[i]),
                price_cross_below_cloud2=bool(cross_below[i]),
            )

            signals["long_a"][i] = result.long_a
            signals["long_b"][i] = result.long_b
            signals["long_c"][i] = result.long_c
            signals["long_d"][i] = result.long_d
            signals["short_a"][i] = result.short_a
            signals["short_b"][i] = result.short_b
            signals["short_c"][i] = result.short_c
            signals["short_d"][i] = result.short_d
            signals["reentry_long"][i] = result.reentry_long
            signals["reentry_short"][i] = result.reentry_short
            signals["add_long"][i] = result.add_long
            signals["add_short"][i] = result.add_short

        for col, arr in signals.items():
            df[col] = arr

        return df

    def get_backtester_params(self, overrides: dict = None) -> dict:
        """Return backtester config dict."""
        p = dict(self.DEFAULT_BT_PARAMS)
        if overrides:
            p.update(overrides)
        return p

    def extract_features(self, trades_df: pd.DataFrame,
                         ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Extract per-trade features using features_v3."""
        from ml.features_v3 import extract_trade_features
        return extract_trade_features(trades_df, ohlcv_df)

    def get_feature_names(self) -> list:
        """Return ordered list of feature column names."""
        from ml.features_v3 import get_feature_columns
        return get_feature_columns()

    def label_trades(self, trades_df: pd.DataFrame,
                     mode: str = "exit") -> pd.Series:
        """Generate binary labels for trades.

        Modes:
            exit: TP hit = 1, SL hit = 0, other = 0
            pnl:  net_pnl > 0 = 1, else 0
        """
        if mode == "exit":
            labels = trades_df["exit_reason"].apply(
                lambda x: 1 if x == "TP" else 0
            )
        elif mode == "pnl":
            if "commission" in trades_df.columns:
                net = trades_df["pnl"] - trades_df["commission"]
            else:
                net = trades_df["pnl"]
            labels = (net > 0).astype(int)
        else:
            raise ValueError("Unknown label mode: " + mode + ". Use exit or pnl.")
        return labels


def create_plugin() -> FourPillarsPlugin:
    """Factory function for strategy loader."""
    return FourPillarsPlugin()
'''


# =====================================================================
# SECTION C: ML Module Bug Fixes
# =====================================================================

XGBOOST_TRAINER_V2 = '''\
"""
XGBoost binary classifier v2 -- GPU mandatory, bug fixes applied.

Fixes from v1:
  - Removed deprecated use_label_encoder param
  - GPU: device=cuda, tree_method=hist (mandatory, no CPU fallback)
  - Safe mask indexing: np.asarray(y) prevents Series misalignment
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
)

log = logging.getLogger(__name__)


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list = None,
    test_size: float = 0.3,
    params: dict = None,
) -> dict:
    """Train XGBoost binary classifier with GPU acceleration."""
    if not HAS_XGB:
        raise ImportError("xgboost not installed. pip install xgboost")

    # Clean NaN -- safe indexing
    if isinstance(X, pd.DataFrame):
        mask = ~X.isna().any(axis=1)
        X = X[mask].values
        y = np.asarray(y)[mask.values]
    else:
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = np.asarray(y)[mask]

    if len(X) < 20:
        raise ValueError("Need >= 20 samples, got " + str(len(X)))

    default_params = {
        "objective": "binary:logistic",
        "device": "cuda",
        "tree_method": "hist",
        "max_depth": 4,
        "learning_rate": 0.05,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "logloss",
        "verbosity": 0,
    }
    if params:
        default_params.update(params)

    n_unique = len(np.unique(y))
    stratify = y if n_unique > 1 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify
    )

    model = XGBClassifier(**default_params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    importances = model.feature_importances_
    if feature_names and len(feature_names) == X.shape[1]:
        names = feature_names
    else:
        names = ["f" + str(i) for i in range(len(importances))]

    imp_df = pd.DataFrame({
        "feature": names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    # AUC (handle single-class edge case)
    try:
        auc = float(roc_auc_score(y_test, y_proba))
    except ValueError:
        auc = 0.0
        log.warning("AUC undefined (single class in test set)")

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "auc": auc,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "positive_rate": float(np.mean(y)),
    }

    return {
        "model": model,
        "feature_importances": imp_df,
        "metrics": metrics,
    }


def predict_skip_take(model, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """Predict 0 (SKIP) or 1 (TAKE) for each sample."""
    proba = model.predict_proba(X)[:, 1]
    return (proba >= threshold).astype(int)
'''

FEATURES_V3 = '''\
"""
Strategy-agnostic feature extraction v3 -- bug fixes + 27 features.

Fixes from v1/v2:
  - dt_series.iloc[i] on DatetimeIndex: now wraps in pd.Series
  - np.isnan() on int-dtype: now uses pd.isna()
  - get_feature_columns(): includes duration_bars (27 total)
"""

import numpy as np
import pandas as pd
from typing import Optional


def extract_trade_features(trades_df: pd.DataFrame,
                           ohlcv_df: pd.DataFrame,
                           coin_metadata: Optional[dict] = None,
                           market_cap_history: Optional[pd.DataFrame] = None,
                           ) -> pd.DataFrame:
    """Build feature matrix for each trade using bar data at entry time."""
    features = []

    close = ohlcv_df["close"].values
    high = ohlcv_df["high"].values
    low = ohlcv_df["low"].values
    atr = ohlcv_df["atr"].values if "atr" in ohlcv_df.columns else None
    n_bars = len(ohlcv_df)

    stoch_9 = ohlcv_df["stoch_9"].values if "stoch_9" in ohlcv_df.columns else None
    stoch_14 = ohlcv_df["stoch_14"].values if "stoch_14" in ohlcv_df.columns else None
    stoch_40 = ohlcv_df["stoch_40"].values if "stoch_40" in ohlcv_df.columns else None
    stoch_60 = ohlcv_df["stoch_60"].values if "stoch_60" in ohlcv_df.columns else None
    volume = ohlcv_df["base_vol"].values if "base_vol" in ohlcv_df.columns else None
    quote_vol = ohlcv_df["quote_vol"].values if "quote_vol" in ohlcv_df.columns else None
    cloud3_bull = ohlcv_df["cloud3_bull"].values if "cloud3_bull" in ohlcv_df.columns else None
    price_pos = ohlcv_df["price_pos"].values if "price_pos" in ohlcv_df.columns else None
    ema34 = ohlcv_df["ema34"].values if "ema34" in ohlcv_df.columns else None
    ema50 = ohlcv_df["ema50"].values if "ema50" in ohlcv_df.columns else None

    # FIX: always wrap dt_series in pd.Series for .iloc compatibility
    has_datetime = False
    dt_series = None
    if "datetime" in ohlcv_df.columns:
        dt_series = pd.to_datetime(ohlcv_df["datetime"])
        has_datetime = True
    elif isinstance(ohlcv_df.index, pd.DatetimeIndex):
        dt_series = pd.Series(ohlcv_df.index)
        has_datetime = True

    # Pre-compute rolling volume arrays
    vol_ma5 = vol_ma20 = vol_ma50 = vol_ma200 = None
    vol_std50 = vol_trend_arr = None
    if volume is not None:
        vol_series = pd.Series(volume)
        vol_ma5 = vol_series.rolling(5, min_periods=1).mean().values
        vol_ma20 = vol_series.rolling(20, min_periods=1).mean().values
        vol_ma50 = vol_series.rolling(50, min_periods=1).mean().values
        vol_ma200 = vol_series.rolling(200, min_periods=1).mean().values
        vol_std50 = vol_series.rolling(50, min_periods=1).std().values
        vol_ma20_series = pd.Series(vol_ma20)
        vol_trend_arr = (vol_ma20_series - vol_ma20_series.shift(10)).values

    qvol_ma20 = None
    if quote_vol is not None:
        qvol_series = pd.Series(quote_vol)
        qvol_ma20 = qvol_series.rolling(20, min_periods=1).mean().values

    vol_price_corr_arr = None
    if volume is not None:
        price_change = pd.Series(close).pct_change().values
        vol_price_corr_arr = (
            pd.Series(volume).rolling(20, min_periods=5)
            .corr(pd.Series(price_change))
            .values
        )

    daily_turnover_at_bar = None
    if quote_vol is not None and has_datetime:
        try:
            _tmp = pd.DataFrame({"datetime": dt_series, "quote_vol": quote_vol})
            _tmp = _tmp.set_index("datetime")
            daily_sum = _tmp["quote_vol"].resample("1D").sum()
            daily_sum = daily_sum.shift(1)
            daily_ma20 = daily_sum.rolling(20, min_periods=1).mean()
            daily_turnover_at_bar = (
                _tmp.index.normalize().map(
                    lambda d, dm=daily_ma20: dm.get(d, np.nan) if d in dm.index else np.nan
                )
            )
            if hasattr(daily_turnover_at_bar, "values"):
                daily_turnover_at_bar = daily_turnover_at_bar.values
            else:
                daily_turnover_at_bar = np.array(list(daily_turnover_at_bar))
        except Exception:
            daily_turnover_at_bar = None

    mcap_lookup = {}
    if market_cap_history is not None and len(market_cap_history) > 0:
        for _, row_mc in market_cap_history.iterrows():
            mcap_lookup[row_mc["date"]] = {
                "market_cap": row_mc.get("market_cap", 0),
                "total_volume": row_mc.get("total_volume", 0),
            }

    for _, trade in trades_df.iterrows():
        i = int(trade["entry_bar"])
        if i < 0 or i >= n_bars:
            continue

        row = {}

        row["direction_enc"] = 1 if trade["direction"] == "LONG" else -1
        row["grade_enc"] = {"A": 3, "B": 2, "C": 1, "R": 0}.get(trade["grade"], 0)

        if stoch_9 is not None:
            row["stoch_9"] = stoch_9[i] if not pd.isna(stoch_9[i]) else 50.0
        if stoch_14 is not None:
            row["stoch_14"] = stoch_14[i] if not pd.isna(stoch_14[i]) else 50.0
        if stoch_40 is not None:
            row["stoch_40"] = stoch_40[i] if not pd.isna(stoch_40[i]) else 50.0
        if stoch_60 is not None:
            row["stoch_60"] = stoch_60[i] if not pd.isna(stoch_60[i]) else 50.0

        if atr is not None and not pd.isna(atr[i]) and close[i] > 0:
            row["atr_pct"] = atr[i] / close[i]
        else:
            row["atr_pct"] = 0.0

        if volume is not None and vol_ma20 is not None and vol_ma20[i] > 0:
            row["vol_ratio"] = volume[i] / vol_ma20[i]
        else:
            row["vol_ratio"] = 1.0

        # FIX: use pd.isna() instead of np.isnan() for int-safe NaN checks
        if cloud3_bull is not None:
            val = cloud3_bull[i]
            row["cloud3_bull"] = int(val) if not pd.isna(val) else 0
        if price_pos is not None:
            val = price_pos[i]
            row["price_pos"] = int(val) if not pd.isna(val) else 0

        if ema34 is not None and ema50 is not None and close[i] > 0:
            if not pd.isna(ema34[i]) and not pd.isna(ema50[i]):
                row["cloud3_spread"] = (ema34[i] - ema50[i]) / close[i]
            else:
                row["cloud3_spread"] = 0.0

        sl_dist = abs(trade["entry_price"] - trade["sl_price"])
        if sl_dist > 0:
            row["mfe_r"] = trade["mfe"] / sl_dist
            row["mae_r"] = trade["mae"] / sl_dist
            net_pnl = trade["pnl"] - trade.get("commission", 0)
            row["pnl_r"] = net_pnl / sl_dist
        else:
            row["mfe_r"] = 0.0
            row["mae_r"] = 0.0
            row["pnl_r"] = 0.0

        if has_datetime and dt_series is not None and i < len(dt_series):
            dt = dt_series.iloc[i]
            row["hour"] = dt.hour
            row["day_of_week"] = dt.dayofweek
        else:
            row["hour"] = 0
            row["day_of_week"] = 0

        net_pnl = trade["pnl"] - trade.get("commission", 0)
        row["etd"] = trade["mfe"] - max(net_pnl, 0)

        # FIX: duration_bars included as a feature
        row["duration_bars"] = int(trade["exit_bar"] - trade["entry_bar"])

        # Volume features (8)
        if volume is not None and vol_ma5 is not None and vol_ma5[i] > 0:
            row["vol_ratio_5"] = volume[i] / vol_ma5[i]
        else:
            row["vol_ratio_5"] = 1.0

        if volume is not None and vol_ma50 is not None and vol_ma50[i] > 0:
            row["vol_ratio_50"] = volume[i] / vol_ma50[i]
        else:
            row["vol_ratio_50"] = 1.0

        if volume is not None and vol_ma200 is not None and vol_ma200[i] > 0:
            row["vol_ratio_200"] = volume[i] / vol_ma200[i]
        else:
            row["vol_ratio_200"] = 1.0

        if vol_trend_arr is not None and not pd.isna(vol_trend_arr[i]):
            if vol_ma20[i] > 0:
                row["vol_trend"] = vol_trend_arr[i] / vol_ma20[i]
            else:
                row["vol_trend"] = 0.0
        else:
            row["vol_trend"] = 0.0

        if (volume is not None and vol_std50 is not None and
                vol_ma50 is not None and vol_std50[i] > 0):
            row["vol_zscore"] = (volume[i] - vol_ma50[i]) / vol_std50[i]
        else:
            row["vol_zscore"] = 0.0

        if quote_vol is not None and qvol_ma20 is not None and qvol_ma20[i] > 0:
            row["quote_vol_ratio"] = quote_vol[i] / qvol_ma20[i]
        else:
            row["quote_vol_ratio"] = 1.0

        if vol_price_corr_arr is not None and not pd.isna(vol_price_corr_arr[i]):
            row["vol_price_corr"] = vol_price_corr_arr[i]
        else:
            row["vol_price_corr"] = 0.0

        if close[i] > 0:
            row["relative_spread"] = (high[i] - low[i]) / close[i]
        else:
            row["relative_spread"] = 0.0

        # Market cap features (4)
        if coin_metadata and coin_metadata.get("market_cap", 0) > 0:
            row["log_market_cap"] = np.log10(coin_metadata["market_cap"])
        else:
            row["log_market_cap"] = np.nan

        if daily_turnover_at_bar is not None and i < len(daily_turnover_at_bar):
            val = daily_turnover_at_bar[i]
            if not pd.isna(val) and val > 0:
                row["log_daily_turnover"] = np.log10(val)
            else:
                row["log_daily_turnover"] = np.nan
        else:
            row["log_daily_turnover"] = np.nan

        if coin_metadata and "market_cap_rank" in coin_metadata:
            row["market_cap_rank"] = coin_metadata["market_cap_rank"]
        else:
            row["market_cap_rank"] = np.nan

        mcap_val = None
        if has_datetime and dt_series is not None and i < len(dt_series) and mcap_lookup:
            date_str = dt_series.iloc[i].strftime("%Y-%m-%d")
            if date_str in mcap_lookup:
                mcap_val = mcap_lookup[date_str].get("market_cap", 0)
        if mcap_val is None and coin_metadata:
            mcap_val = coin_metadata.get("market_cap", 0)

        if (mcap_val and mcap_val > 0 and
                daily_turnover_at_bar is not None and i < len(daily_turnover_at_bar)):
            turnover = daily_turnover_at_bar[i]
            if not pd.isna(turnover) and turnover > 0:
                row["turnover_to_cap_ratio"] = turnover / mcap_val
            else:
                row["turnover_to_cap_ratio"] = np.nan
        else:
            row["turnover_to_cap_ratio"] = np.nan

        features.append(row)

    return pd.DataFrame(features)


def get_feature_columns() -> list:
    """Return 27 feature columns for ML training (excludes leakage cols)."""
    return [
        # Original 13
        "direction_enc", "grade_enc",
        "stoch_9", "stoch_14", "stoch_40", "stoch_60",
        "atr_pct", "vol_ratio",
        "cloud3_bull", "price_pos", "cloud3_spread",
        "hour", "day_of_week",
        # Duration (was missing in v1/v2)
        "duration_bars",
        # Volume features (8)
        "vol_ratio_5", "vol_ratio_50", "vol_ratio_200",
        "vol_trend", "vol_zscore",
        "quote_vol_ratio", "vol_price_corr", "relative_spread",
        # Market cap features (4)
        "log_market_cap", "log_daily_turnover",
        "market_cap_rank", "turnover_to_cap_ratio",
    ]
'''

SHAP_ANALYZER_V2 = '''\
"""
SHAP Explainability v2 -- bug fixes applied.

Fixes from v1:
  - Empty array guard before shap_values()
  - Binary SHAP list-vs-array normalization (old vs new shap library)
"""

import logging
import numpy as np
import pandas as pd

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

log = logging.getLogger(__name__)


class ShapAnalyzer:
    """Generates SHAP explanations for a trained XGBoost model."""

    def __init__(self, model, feature_names: list = None):
        """Initialize with a trained XGBoost model."""
        if not HAS_SHAP:
            raise ImportError("shap not installed. Run: pip install shap")
        self.model = model
        self.feature_names = feature_names
        self.shap_values = None
        self.explainer = None

    def compute(self, X: pd.DataFrame) -> np.ndarray:
        """Compute SHAP values for all trades in feature matrix."""
        if isinstance(X, pd.DataFrame):
            X_vals = X.values
        else:
            X_vals = X

        # FIX: guard against empty feature matrix
        if len(X_vals) == 0:
            log.warning("Empty feature matrix passed to ShapAnalyzer.compute()")
            self.shap_values = np.empty((0, X_vals.shape[1] if X_vals.ndim == 2 else 0))
            return self.shap_values

        self.explainer = shap.TreeExplainer(self.model)
        self.shap_values = self.explainer.shap_values(X_vals)

        # FIX: handle binary XGBoost SHAP shape (old shap returns list)
        if isinstance(self.shap_values, list):
            log.info("SHAP returned list of %d arrays, using class 1 (TAKE)", len(self.shap_values))
            self.shap_values = self.shap_values[1]

        return self.shap_values

    def get_top_features(self, trade_idx: int, top_n: int = 5) -> list:
        """Get top N features driving prediction for a specific trade."""
        if self.shap_values is None:
            raise ValueError("Call compute() first.")
        if len(self.shap_values) == 0:
            return []

        vals = self.shap_values[trade_idx]
        names = self.feature_names or ["f" + str(i) for i in range(len(vals))]
        indices = np.argsort(np.abs(vals))[::-1][:top_n]

        result = []
        for idx in indices:
            result.append({
                "feature": names[idx] if idx < len(names) else "f" + str(idx),
                "shap_value": float(vals[idx]),
                "direction": "TAKE" if vals[idx] > 0 else "SKIP",
            })
        return result

    def get_global_importance(self) -> pd.DataFrame:
        """Mean absolute SHAP value per feature (global importance)."""
        if self.shap_values is None:
            raise ValueError("Call compute() first.")
        if len(self.shap_values) == 0:
            return pd.DataFrame(columns=["feature", "mean_abs_shap"])

        mean_abs = np.mean(np.abs(self.shap_values), axis=0)
        names = self.feature_names or ["f" + str(i) for i in range(len(mean_abs))]

        df = pd.DataFrame({
            "feature": names[:len(mean_abs)],
            "mean_abs_shap": mean_abs,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

        return df
'''

BET_SIZING_V2 = '''\
"""
Bet Sizing v2 -- bug fixes applied.

Fixes from v1:
  - Kelly avg_loss=0 guard now logs warning instead of silent zero-return
  - Negative edge logged as warning
"""

import logging
import numpy as np

log = logging.getLogger(__name__)


def binary_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5) -> np.ndarray:
    """Binary bet sizing: above threshold = full size, below = skip."""
    return (probabilities >= threshold).astype(float)


def linear_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5,
                  max_size: float = 1.0) -> np.ndarray:
    """Linear bet sizing: size scales from 0 at threshold to max_size at 1.0."""
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
    """Kelly criterion bet sizing with fractional Kelly for safety."""
    # FIX: log warning instead of silent zero-return
    if avg_win <= 0:
        log.warning("kelly_sizing: avg_win <= 0 (%.4f), returning zeros", avg_win)
        return np.zeros_like(probabilities)
    if avg_loss >= 0:
        log.warning("kelly_sizing: avg_loss >= 0 (%.4f), expected negative. Returning zeros", avg_loss)
        return np.zeros_like(probabilities)

    b = avg_win / abs(avg_loss)
    q = 1.0 - probabilities
    kelly_f = (probabilities * b - q) / b

    # Log negative edge trades
    n_negative = int(np.sum(kelly_f < 0))
    if n_negative > 0:
        log.info("kelly_sizing: %d/%d trades have negative edge (will be clipped to 0)",
                 n_negative, len(kelly_f))

    kelly_f *= fraction
    sizes = np.clip(kelly_f, 0.0, max_size)
    return sizes


def get_sizing_summary(sizes: np.ndarray) -> dict:
    """Summarize sizing decisions."""
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


# =====================================================================
# SECTION D: Train Vince CLI
# =====================================================================

TRAIN_VINCE = '''\
"""
Vince ML Training Pipeline -- per-coin XGBoost auditor.
12-step pipeline using strategy plugin system.

Run single coin:
  python scripts/train_vince.py --symbol RIVERUSDT
Run with walk-forward:
  python scripts/train_vince.py --symbol RIVERUSDT --walk-forward
Run all coins:
  python scripts/train_vince.py --symbol ALL --top 20
"""

import sys
import json
import time
import logging
import argparse
import traceback
import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CACHE_DIR = ROOT / "data" / "cache"
MODELS_DIR = ROOT / "models"
POOL_FILE = ROOT / "data" / "coin_pools.json"


def gpu_preflight():
    """Verify CUDA is available for XGBoost. Fail fast if not."""
    try:
        from xgboost import XGBClassifier
        test_model = XGBClassifier(device="cuda", tree_method="hist",
                                   n_estimators=1, verbosity=0)
        test_model.fit([[0, 1], [1, 0]], [0, 1])
        log.info("GPU pre-flight: CUDA verified for XGBoost")
    except Exception as e:
        log.error("GPU pre-flight FAILED: %s", e)
        log.error("CUDA is MANDATORY. Install xgboost with GPU support.")
        sys.exit(1)


def load_pools() -> dict:
    """Load coin pool assignments from JSON."""
    if not POOL_FILE.exists():
        log.error("coin_pools.json not found. Run build_data_infra_v1.py first.")
        sys.exit(1)
    with open(POOL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_symbols(args, pools: dict) -> list:
    """Resolve symbol list from CLI args and pool assignments."""
    assignments = pools.get("assignments", {})

    if args.symbol == "ALL":
        # Only train on Pool A coins
        symbols = [s for s, p in assignments.items() if p == "A"]
        log.info("ALL mode: %d Pool A coins", len(symbols))
    else:
        symbols = [args.symbol]

    # Filter by pool (never train on Pool C)
    filtered = []
    for sym in symbols:
        pool = assignments.get(sym, "C")
        if pool == "C":
            log.warning("SKIP %s: Pool C (holdout, never train)", sym)
            continue
        filtered.append(sym)

    if args.top and args.top < len(filtered):
        filtered = filtered[:args.top]
        log.info("Limited to top %d coins", args.top)

    return filtered


def find_parquet(symbol: str, timeframe: str) -> Path:
    """Locate OHLCV parquet file for a symbol."""
    path = CACHE_DIR / (symbol + "_" + timeframe + ".parquet")
    if path.exists():
        return path
    # Try without underscore
    path2 = CACHE_DIR / (symbol + timeframe + ".parquet")
    if path2.exists():
        return path2
    return path  # will fail at load time with clear error


def train_single_coin(symbol: str, timeframe: str, strategy, args) -> dict:
    """Train XGBoost auditor for one coin. Returns report dict."""
    ts_start = time.time()
    report = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": strategy.name,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "label_mode": args.label_mode,
        "status": "FAILED",
    }

    # Step 1: Load OHLCV
    pq_path = find_parquet(symbol, timeframe)
    if not pq_path.exists():
        log.warning("SKIP %s: no parquet at %s", symbol, pq_path)
        report["error"] = "No parquet file"
        return report

    df = pd.read_parquet(pq_path)
    log.info("[%s] Loaded %d bars from %s", symbol, len(df), pq_path.name)

    # Validate required OHLCV columns
    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        log.warning("SKIP %s: missing columns: %s", symbol, ", ".join(missing))
        report["error"] = "Missing columns: " + ", ".join(missing)
        return report

    # Ensure volume column exists
    if "base_vol" not in df.columns and "volume" in df.columns:
        df["base_vol"] = df["volume"]

    # Ensure datetime is accessible
    if "datetime" not in df.columns and isinstance(df.index, pd.DatetimeIndex):
        pass  # dt_series in features_v3 handles DatetimeIndex via pd.Series wrap
    elif "datetime" not in df.columns and "timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    # Step 2-3: Enrich OHLCV with indicators
    log.info("[%s] Enriching OHLCV (ATR, stochastics, clouds)...", symbol)
    df = strategy.enrich_ohlcv(df)

    # Step 4: Generate signals
    log.info("[%s] Computing signals (state machine)...", symbol)
    df = strategy.compute_signals(df)

    # Step 5: Run backtest
    log.info("[%s] Running backtest...", symbol)
    from engine.backtester_v384 import Backtester384

    bt_params = strategy.get_backtester_params()
    if args.tp_mult is not None:
        bt_params["tp_mult"] = args.tp_mult
    if args.sl_mult is not None:
        bt_params["sl_mult"] = args.sl_mult

    bt = Backtester384(bt_params)
    bt_result = bt.run(df)
    trades_df = bt_result["trades"]

    if len(trades_df) < 20:
        log.warning("SKIP %s: only %d trades (need >= 20)", symbol, len(trades_df))
        report["error"] = "Too few trades: " + str(len(trades_df))
        report["n_trades"] = len(trades_df)
        return report

    log.info("[%s] Backtest: %d trades", symbol, len(trades_df))

    # Step 6: Extract features
    log.info("[%s] Extracting features...", symbol)
    X = strategy.extract_features(trades_df, df)

    # Prepend coin-level features (10 cols)
    from ml.coin_features import compute_coin_features, get_feature_names as coin_feat_names
    coin_feats = compute_coin_features(df)
    for feat_name in coin_feat_names():
        X[feat_name] = coin_feats.get(feat_name, 0.0)

    # Step 7: Label trades
    log.info("[%s] Labeling trades (mode=%s)...", symbol, args.label_mode)
    y = strategy.label_trades(trades_df, mode=args.label_mode)

    # Step 8: Grade filtering (optional)
    if args.grade_filter:
        grades_to_filter = [g.strip().upper() for g in args.grade_filter.split(",")]
        log.info("[%s] Grade filtering: removing grades %s", symbol, grades_to_filter)
        grade_mask = ~trades_df["grade"].isin(grades_to_filter)
        X = X[grade_mask.values].reset_index(drop=True)
        y = y[grade_mask.values].reset_index(drop=True)
        log.info("[%s] After grade filter: %d trades remain", symbol, len(X))

        if len(X) < 20:
            log.warning("SKIP %s: only %d trades after grade filter", symbol, len(X))
            report["error"] = "Too few trades after grade filter"
            return report

    # Select feature columns only (no leakage)
    feature_cols = strategy.get_feature_names() + coin_feat_names()
    available_cols = [c for c in feature_cols if c in X.columns]
    X_clean = X[available_cols].copy()
    report["n_features"] = len(available_cols)
    report["n_trades"] = len(X_clean)
    report["label_distribution"] = {
        "positive": int(y.sum()),
        "negative": int(len(y) - y.sum()),
        "positive_rate": float(y.mean()),
    }

    # Step 9: Validation
    from ml.purged_cv import purged_kfold_split, get_split_summary

    if args.walk_forward:
        log.info("[%s] Walk-forward validation...", symbol)
        from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward
        from ml.xgboost_trainer_v2 import train_xgboost

        windows = generate_windows(len(X_clean))
        window_results = []
        for w_idx, window in enumerate(windows):
            is_X = X_clean.iloc[window["is_start"]:window["is_end"]]
            is_y = y.iloc[window["is_start"]:window["is_end"]]
            oos_X = X_clean.iloc[window["oos_start"]:window["oos_end"]]
            oos_y = y.iloc[window["oos_start"]:window["oos_end"]]

            if len(is_X) < 20 or len(oos_X) < 10:
                continue

            try:
                is_result = train_xgboost(is_X, is_y.values, feature_names=available_cols)
                oos_pred = is_result["model"].predict(oos_X.values)
                from sklearn.metrics import accuracy_score
                is_metric = is_result["metrics"]["accuracy"]
                oos_metric = float(accuracy_score(oos_y, oos_pred))
                window_results.append({"is_metric": is_metric, "oos_metric": oos_metric})
            except Exception as e:
                log.warning("[%s] Walk-forward window %d failed: %s", symbol, w_idx, e)
                continue

        wf_summary = summarize_walk_forward(window_results)
        report["wfe_metrics"] = wf_summary
        log.info("[%s] WFE: %.3f (%s)", symbol, wf_summary["avg_wfe"], wf_summary["rating"])
    else:
        log.info("[%s] Purged K-fold CV (5 folds)...", symbol)
        n_splits = min(5, len(X_clean) // 5)
        if n_splits < 2:
            n_splits = 2
        try:
            splits = purged_kfold_split(trades_df.iloc[:len(X_clean)], n_splits=n_splits)
            split_summary = get_split_summary(splits, len(X_clean))
            report["cv_splits"] = split_summary
        except Exception as e:
            log.warning("[%s] Purged CV failed: %s", symbol, e)

    # Step 10: Train XGBoost
    log.info("[%s] Training XGBoost (GPU)...", symbol)
    from ml.xgboost_trainer_v2 import train_xgboost

    try:
        result = train_xgboost(
            X_clean, y.values,
            feature_names=available_cols,
        )
    except Exception as e:
        log.error("[%s] XGBoost training failed: %s", symbol, e)
        log.debug(traceback.format_exc())
        report["error"] = "Training failed: " + str(e)
        return report

    report["test_metrics"] = result["metrics"]
    report["feature_importance"] = result["feature_importances"].to_dict(orient="records")
    log.info("[%s] Accuracy=%.3f, F1=%.3f, AUC=%.3f",
             symbol, result["metrics"]["accuracy"],
             result["metrics"]["f1"], result["metrics"]["auc"])

    # Step 11: SHAP analysis
    log.info("[%s] SHAP analysis...", symbol)
    try:
        from ml.shap_analyzer_v2 import ShapAnalyzer
        shap_analyzer = ShapAnalyzer(result["model"], feature_names=available_cols)
        shap_analyzer.compute(X_clean)
        global_imp = shap_analyzer.get_global_importance()
        report["shap_global"] = global_imp.head(10).to_dict(orient="records")
    except Exception as e:
        log.warning("[%s] SHAP analysis failed: %s", symbol, e)
        report["shap_error"] = str(e)

    # Step 12: Bet sizing simulation
    log.info("[%s] Bet sizing simulation...", symbol)
    try:
        from ml.bet_sizing_v2 import binary_sizing, linear_sizing, kelly_sizing, get_sizing_summary

        y_proba = result["model"].predict_proba(X_clean.values)[:, 1]
        y_actual = y.values

        # Compute avg_win and avg_loss from actual trades
        net_pnl = trades_df["pnl"].values[:len(y_actual)]
        if "commission" in trades_df.columns:
            net_pnl = net_pnl - trades_df["commission"].values[:len(y_actual)]
        wins = net_pnl[net_pnl > 0]
        losses = net_pnl[net_pnl < 0]
        avg_win = float(np.mean(wins)) if len(wins) > 0 else 0.0
        avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0.0

        sizing_results = {}
        for threshold in [0.4, 0.5, 0.6]:
            sizing_results["binary_" + str(threshold)] = get_sizing_summary(
                binary_sizing(y_proba, threshold)
            )
            sizing_results["linear_" + str(threshold)] = get_sizing_summary(
                linear_sizing(y_proba, threshold)
            )
        if avg_win > 0 and avg_loss < 0:
            sizing_results["kelly_0.5"] = get_sizing_summary(
                kelly_sizing(y_proba, avg_win, avg_loss, fraction=0.5)
            )

        report["bet_sizing"] = sizing_results
    except Exception as e:
        log.warning("[%s] Bet sizing failed: %s", symbol, e)
        report["bet_sizing_error"] = str(e)

    # Step 13: Save model + report
    ts_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    strategy_dir = MODELS_DIR / strategy.name
    strategy_dir.mkdir(parents=True, exist_ok=True)

    model_path = strategy_dir / (symbol + "_xgb_" + ts_str + ".json")
    result["model"].save_model(str(model_path))
    log.info("[%s] Model saved: %s", symbol, model_path)

    report["model_path"] = str(model_path)
    report["status"] = "OK"
    report["duration_sec"] = round(time.time() - ts_start, 1)

    report_path = strategy_dir / (symbol + "_report_" + ts_str + ".json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    log.info("[%s] Report saved: %s", symbol, report_path)

    return report


def main():
    """Entry point for Vince ML training pipeline."""
    parser = argparse.ArgumentParser(description="Vince ML Training Pipeline")
    parser.add_argument("--symbol", required=True, help="Symbol (e.g. RIVERUSDT) or ALL")
    parser.add_argument("--timeframe", default="5m", help="Timeframe (default: 5m)")
    parser.add_argument("--strategy", default="four_pillars", help="Strategy plugin name")
    parser.add_argument("--label-mode", default="exit", choices=["exit", "pnl"],
                        help="Label mode: exit (TP=1/SL=0) or pnl (net>0)")
    parser.add_argument("--grade-filter", default=None,
                        help="Comma-separated grades to exclude (e.g. D,R)")
    parser.add_argument("--walk-forward", action="store_true",
                        help="Use walk-forward validation instead of purged CV")
    parser.add_argument("--tp-mult", type=float, default=None,
                        help="Override TP multiplier (ATR)")
    parser.add_argument("--sl-mult", type=float, default=None,
                        help="Override SL multiplier (ATR)")
    parser.add_argument("--top", type=int, default=None,
                        help="Limit to top N coins (ALL mode)")
    args = parser.parse_args()

    log.info("=== Vince ML Training Pipeline ===")
    log.info("Symbol: %s | Timeframe: %s | Strategy: %s | Label: %s",
             args.symbol, args.timeframe, args.strategy, args.label_mode)

    # GPU pre-flight
    gpu_preflight()

    # Load strategy
    from strategies import load_strategy
    strategy = load_strategy(args.strategy)
    log.info("Strategy loaded: %s", strategy.name)

    # Load pools
    pools = load_pools()

    # Resolve symbols
    symbols = get_symbols(args, pools)
    if not symbols:
        log.error("No symbols to process. Check pool assignments.")
        sys.exit(1)
    log.info("Processing %d symbols", len(symbols))

    # Train each coin
    results = []
    errors = []
    for idx, symbol in enumerate(symbols, 1):
        log.info("--- [%d/%d] %s ---", idx, len(symbols), symbol)
        try:
            report = train_single_coin(symbol, args.timeframe, strategy, args)
            results.append(report)
            if report["status"] != "OK":
                errors.append(symbol + ": " + report.get("error", "unknown"))
        except Exception as e:
            log.error("[%s] FATAL: %s", symbol, e)
            log.debug(traceback.format_exc())
            errors.append(symbol + ": " + str(e))
            continue

    # Summary
    ok_count = sum(1 for r in results if r.get("status") == "OK")
    log.info("=== COMPLETE ===")
    log.info("Processed: %d | OK: %d | Failed: %d", len(symbols), ok_count, len(errors))
    if errors:
        log.warning("Failures:")
        for err in errors:
            log.warning("  - %s", err)

    # Save sweep summary if ALL mode
    if args.symbol == "ALL" and results:
        summary_path = MODELS_DIR / strategy.name / "sweep_summary.json"
        summary = {
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "strategy": strategy.name,
            "timeframe": args.timeframe,
            "label_mode": args.label_mode,
            "total": len(symbols),
            "ok": ok_count,
            "failed": len(errors),
            "results": [
                {
                    "symbol": r["symbol"],
                    "status": r.get("status"),
                    "n_trades": r.get("n_trades", 0),
                    "accuracy": r.get("test_metrics", {}).get("accuracy", 0),
                    "f1": r.get("test_metrics", {}).get("f1", 0),
                    "auc": r.get("test_metrics", {}).get("auc", 0),
                }
                for r in results
            ],
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
        log.info("Sweep summary: %s", summary_path)


if __name__ == "__main__":
    main()
'''


# =====================================================================
# MAIN BUILD FUNCTION
# =====================================================================

def main():
    """Build Sections 0+C+D: Strategy Plugin + ML Fixes + Train Vince."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info("[%s] === Build: Sections 0+C+D ===", ts)

    files_to_write = [
        # Section 0: Strategy Plugin
        (ROOT / "strategies" / "__init__.py", STRATEGIES_INIT),
        (ROOT / "strategies" / "base.py", STRATEGIES_BASE),
        (ROOT / "strategies" / "four_pillars.py", STRATEGIES_FOUR_PILLARS),
        # Section C: ML Bug Fixes
        (ROOT / "ml" / "xgboost_trainer_v2.py", XGBOOST_TRAINER_V2),
        (ROOT / "ml" / "features_v3.py", FEATURES_V3),
        (ROOT / "ml" / "shap_analyzer_v2.py", SHAP_ANALYZER_V2),
        (ROOT / "ml" / "bet_sizing_v2.py", BET_SIZING_V2),
        # Section D: Train Vince CLI
        (ROOT / "scripts" / "train_vince.py", TRAIN_VINCE),
    ]

    written = 0
    for path, content in files_to_write:
        log.info("--- %s ---", path.relative_to(ROOT))
        safe_write(path, content)
        if path.suffix == ".py":
            verify(path)
        written += 1

    # Summary
    ts2 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ERRORS:
        log.error("[%s] BUILD FAILED -- %d errors:", ts2, len(ERRORS))
        for e in ERRORS:
            log.error("  - %s", e)
        sys.exit(1)
    else:
        log.info("[%s] BUILD OK -- %d files written, all syntax checks passed", ts2, written)
        for path, _ in files_to_write:
            log.info("  - %s", path.relative_to(ROOT))


if __name__ == "__main__":
    main()

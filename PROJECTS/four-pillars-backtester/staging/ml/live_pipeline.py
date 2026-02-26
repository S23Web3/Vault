"""
Live Pipeline: WebSocket -> Signal Detection -> ML Filter -> Execution.

Architecture:
  1. Bybit WebSocket streams 1m/5m kline data
  2. Rolling buffer maintains last N bars for indicator calc
  3. Four Pillars state machine processes each new bar
  4. When signal fires: extract features, run meta-label model
  5. If model says TAKE (prob >= threshold): generate order
  6. Order goes to execution layer (separate module)

This module does NOT execute trades. It produces filtered signals
with confidence scores for the execution layer to act on.

Input: WebSocket kline stream.
Output: FilteredSignal objects with direction, grade, confidence, size.
"""

import sys
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from signals.stochastics import compute_all_stochastics
from signals.clouds import compute_clouds
from signals.state_machine import FourPillarsStateMachine

logger = logging.getLogger(__name__)


@dataclass
class FilteredSignal:
    """Output of the live pipeline: a filtered trade signal."""
    timestamp: datetime
    symbol: str
    direction: str       # LONG or SHORT
    grade: str           # A, B, C, R
    confidence: float    # 0.0-1.0 from meta-label model
    size: float          # 0.0-1.0 from bet sizing
    entry_price: float
    atr: float
    sl_price: float
    tp_price: float
    features: dict = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Configuration for the live pipeline."""
    symbol: str = "RIVERUSDT"
    timeframe: str = "5m"
    buffer_size: int = 200
    sl_mult: float = 1.0
    tp_mult: float = 1.5
    ml_threshold: float = 0.5
    model_path: Optional[str] = None
    signal_params: dict = field(default_factory=dict)


class LivePipeline:
    """
    Processes streaming kline data and produces filtered signals.

    Usage:
        config = PipelineConfig(symbol="RIVERUSDT", timeframe="5m")
        pipeline = LivePipeline(config)
        pipeline.load_model("models/meta_label.json")

        # Feed bars from WebSocket
        for bar in websocket_stream:
            signal = pipeline.process_bar(bar)
            if signal:
                execute(signal)
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.buffer = pd.DataFrame()
        self.state_machine = FourPillarsStateMachine(
            **{k: v for k, v in config.signal_params.items()
               if k in FourPillarsStateMachine.__init__.__code__.co_varnames}
        )
        self.model = None
        self.feature_names = None
        self.bar_count = 0
        self._callbacks: list[Callable] = []

    def load_model(self, model_path: str):
        """
        Load a trained meta-label XGBoost model.

        Args:
            model_path: Path to saved model (JSON or pickle).
        """
        try:
            from xgboost import XGBClassifier
            model = XGBClassifier()
            model.load_model(model_path)
            self.model = model
            logger.info(f"Loaded model from {model_path}")
        except Exception as e:
            logger.warning(f"Could not load model: {e}. Running without ML filter.")
            self.model = None

    def set_feature_names(self, names: list[str]):
        """Set feature column names for model input."""
        self.feature_names = names

    def on_signal(self, callback: Callable):
        """Register a callback for when a filtered signal is produced."""
        self._callbacks.append(callback)

    def process_bar(self, bar: dict) -> Optional[FilteredSignal]:
        """
        Process a single kline bar.

        Args:
            bar: dict with keys: timestamp, open, high, low, close,
                 base_vol, quote_vol.

        Returns:
            FilteredSignal if a signal fires and passes ML filter, else None.
        """
        # Append to rolling buffer
        row = pd.DataFrame([bar])
        self.buffer = pd.concat([self.buffer, row], ignore_index=True)

        # Trim buffer to max size
        if len(self.buffer) > self.config.buffer_size:
            self.buffer = self.buffer.iloc[-self.config.buffer_size:].reset_index(drop=True)

        self.bar_count += 1

        # Need minimum bars for indicators
        if len(self.buffer) < 60:
            return None

        # Compute indicators on full buffer
        df = self.buffer.copy()
        df = compute_all_stochastics(df, self.config.signal_params)
        df = compute_clouds(df, self.config.signal_params)

        # ATR
        high = df["high"].values
        low = df["low"].values
        close = df["close"].values
        atr_len = self.config.signal_params.get("atr_length", 14)
        tr = np.maximum(high - low,
            np.maximum(np.abs(high - np.roll(close, 1)),
                       np.abs(low - np.roll(close, 1))))
        tr[0] = high[0] - low[0]
        atr_arr = np.full(len(tr), np.nan)
        atr_arr[atr_len - 1] = np.mean(tr[:atr_len])
        for j in range(atr_len, len(tr)):
            atr_arr[j] = (atr_arr[j - 1] * (atr_len - 1) + tr[j]) / atr_len
        df["atr"] = atr_arr

        # Process latest bar through state machine
        i = len(df) - 1
        if np.isnan(df["stoch_9"].iloc[i]) or np.isnan(atr_arr[i]):
            return None

        result = self.state_machine.process_bar(
            bar_index=self.bar_count,
            stoch_9=df["stoch_9"].iloc[i],
            stoch_14=df["stoch_14"].iloc[i],
            stoch_40=df["stoch_40"].iloc[i],
            stoch_60=df["stoch_60"].iloc[i],
            stoch_60_d=df["stoch_60_d"].iloc[i],
            cloud3_bull=bool(df["cloud3_bull"].iloc[i]),
            price_pos=int(df["price_pos"].iloc[i]),
            price_cross_above_cloud2=bool(df["price_cross_above_cloud2"].iloc[i]),
            price_cross_below_cloud2=bool(df["price_cross_below_cloud2"].iloc[i]),
        )

        # Determine signal
        direction = None
        grade = None
        if result.long_a:
            direction, grade = "LONG", "A"
        elif result.short_a:
            direction, grade = "SHORT", "A"
        elif result.long_b:
            direction, grade = "LONG", "B"
        elif result.short_b:
            direction, grade = "SHORT", "B"
        elif result.long_c:
            direction, grade = "LONG", "C"
        elif result.short_c:
            direction, grade = "SHORT", "C"
        elif result.reentry_long:
            direction, grade = "LONG", "R"
        elif result.reentry_short:
            direction, grade = "SHORT", "R"

        if direction is None:
            return None

        # Extract features for ML filter
        current_close = close[i]
        current_atr = atr_arr[i]
        features = self._extract_features(df, i, direction, grade)

        # ML filter
        confidence = 0.5
        size = 1.0
        if self.model is not None:
            confidence = self._predict_confidence(features)
            if confidence < self.config.ml_threshold:
                logger.debug(f"Signal SKIPPED: {grade} {direction} conf={confidence:.3f}")
                return None
            size = min(confidence, 1.0)

        # Compute SL/TP
        if direction == "LONG":
            sl = current_close - self.config.sl_mult * current_atr
            tp = current_close + self.config.tp_mult * current_atr
        else:
            sl = current_close + self.config.sl_mult * current_atr
            tp = current_close - self.config.tp_mult * current_atr

        ts = bar.get("timestamp", datetime.now(timezone.utc))
        if isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)

        signal = FilteredSignal(
            timestamp=ts,
            symbol=self.config.symbol,
            direction=direction,
            grade=grade,
            confidence=confidence,
            size=size,
            entry_price=current_close,
            atr=current_atr,
            sl_price=sl,
            tp_price=tp,
            features=features,
        )

        # Fire callbacks
        for cb in self._callbacks:
            try:
                cb(signal)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        return signal

    def _extract_features(self, df: pd.DataFrame, bar_idx: int,
                          direction: str, grade: str) -> dict:
        """Extract features at the current bar for ML prediction."""
        row = {}
        row["direction_enc"] = 1 if direction == "LONG" else -1
        row["grade_enc"] = {"A": 3, "B": 2, "C": 1, "R": 0}.get(grade, 0)

        for col in ["stoch_9", "stoch_14", "stoch_40", "stoch_60"]:
            if col in df.columns:
                val = df[col].iloc[bar_idx]
                row[col] = val if not np.isnan(val) else 50.0

        close_val = df["close"].iloc[bar_idx]
        atr_val = df["atr"].iloc[bar_idx]
        row["atr_pct"] = atr_val / close_val if close_val > 0 else 0

        if "base_vol" in df.columns:
            vol = df["base_vol"].iloc[bar_idx]
            vol_avg = df["base_vol"].iloc[max(0, bar_idx-20):bar_idx+1].mean()
            row["vol_ratio"] = vol / vol_avg if vol_avg > 0 else 1.0
        else:
            row["vol_ratio"] = 1.0

        if "cloud3_bull" in df.columns:
            row["cloud3_bull"] = int(df["cloud3_bull"].iloc[bar_idx])
        if "price_pos" in df.columns:
            row["price_pos"] = int(df["price_pos"].iloc[bar_idx])
        if "ema34" in df.columns and "ema50" in df.columns:
            e34 = df["ema34"].iloc[bar_idx]
            e50 = df["ema50"].iloc[bar_idx]
            row["cloud3_spread"] = (e34 - e50) / close_val if close_val > 0 else 0

        if "datetime" in df.columns:
            dt = pd.to_datetime(df["datetime"].iloc[bar_idx])
            row["hour"] = dt.hour
            row["day_of_week"] = dt.dayofweek
        else:
            row["hour"] = 0
            row["day_of_week"] = 0

        row["duration_bars"] = 0  # unknown at entry time

        return row

    def _predict_confidence(self, features: dict) -> float:
        """Run ML model on features, return probability."""
        if self.model is None:
            return 0.5

        if self.feature_names:
            X = np.array([[features.get(f, 0) for f in self.feature_names]])
        else:
            X = np.array([list(features.values())])

        try:
            proba = self.model.predict_proba(X)[0, 1]
            return float(proba)
        except Exception:
            return 0.5

    def get_status(self) -> dict:
        """Return pipeline status for monitoring."""
        return {
            "symbol": self.config.symbol,
            "timeframe": self.config.timeframe,
            "bars_processed": self.bar_count,
            "buffer_size": len(self.buffer),
            "model_loaded": self.model is not None,
            "ml_threshold": self.config.ml_threshold,
        }


if __name__ == "__main__":
    # Smoke test with synthetic data
    config = PipelineConfig(symbol="TESTUSDT", buffer_size=100)
    pipeline = LivePipeline(config)

    signals_received = []
    pipeline.on_signal(lambda s: signals_received.append(s))

    np.random.seed(42)
    close = 100.0
    for i in range(200):
        close += np.random.randn() * 0.5
        bar = {
            "timestamp": int(time.time() * 1000) + i * 60000,
            "open": close - 0.1,
            "high": close + abs(np.random.randn()) * 0.5,
            "low": close - abs(np.random.randn()) * 0.5,
            "close": close,
            "base_vol": float(np.random.randint(1000, 5000)),
            "quote_vol": float(np.random.randint(10000, 50000)),
        }
        signal = pipeline.process_bar(bar)

    status = pipeline.get_status()
    print(f"PASS -- processed {status['bars_processed']} bars, "
          f"buffer={status['buffer_size']}, "
          f"signals={len(signals_received)}")

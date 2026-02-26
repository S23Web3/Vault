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

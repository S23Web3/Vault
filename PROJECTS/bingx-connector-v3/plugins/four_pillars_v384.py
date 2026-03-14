"""
Four Pillars v3.8.4 strategy plugin for BingX connector.
Runs the same compute_signals() used by the dashboard on live OHLCV bars.
A/B/C entry signals with fixed ATR-based SL and optional TP.
Loaded by StrategyAdapter when config.yaml: strategy.plugin = "four_pillars_v384"
"""
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Add backtester root -- same signal code the dashboard uses
_BACKTESTER = (
    Path(__file__).resolve().parent.parent.parent / "four-pillars-backtester"
)
if str(_BACKTESTER) not in sys.path:
    sys.path.insert(0, str(_BACKTESTER))

from signals.four_pillars import compute_signals
from plugins.mock_strategy import Signal

logger = logging.getLogger(__name__)


class FourPillarsV384:
    """Four Pillars strategy plugin -- A/B/C entries, fixed ATR SL/TP."""

    def __init__(self, config=None):
        """Read four_pillars sub-block from config; set sl/tp multipliers."""
        cfg = (config or {}).get("four_pillars", {})
        self.allow_a = cfg.get("allow_a", True)
        self.allow_b = cfg.get("allow_b", True)
        self.allow_c = cfg.get("allow_c", False)
        self.sl_mult = float(cfg.get("sl_atr_mult", 2.0))
        tp_raw = cfg.get("tp_atr_mult", None)
        self.tp_mult = float(tp_raw) if tp_raw is not None else None
        self._params = {
            "atr_length":     cfg.get("atr_length", 14),
            "cross_level":    cfg.get("cross_level", 25),
            "zone_level":     cfg.get("zone_level", 30),
            "allow_b_trades": self.allow_b,
            "allow_c_trades": self.allow_c,
            "require_stage2": cfg.get("require_stage2", False),
            "rot_level":      cfg.get("rot_level", 80),
        }
        logger.info(
            "FourPillarsV384: allow_a=%s allow_b=%s allow_c=%s "
            "sl=%.1f tp=%s stage2=%s rot=%d backtester=%s",
            self.allow_a, self.allow_b, self.allow_c,
            self.sl_mult, str(self.tp_mult),
            cfg.get("require_stage2", False), cfg.get("rot_level", 80),
            str(_BACKTESTER),
        )

    def get_signal(self, ohlcv_df: pd.DataFrame) -> Optional[Signal]:
        """Run compute_signals on live bars; return Signal from last closed bar or None."""
        if ohlcv_df is None or len(ohlcv_df) < 2:
            return None
        try:
            df = ohlcv_df.copy()
            # Normalize: MarketDataFeed uses 'time' and 'volume'
            # compute_signals expects 'timestamp' and 'base_vol'
            df = df.rename(columns={"time": "timestamp", "volume": "base_vol"})
            if "quote_vol" not in df.columns:
                df["quote_vol"] = 0.0
            df = compute_signals(df, self._params)
        except Exception as e:
            logger.error("compute_signals failed: %s", e)
            return None

        # Last CLOSED bar is iloc[-2] -- last row is the current open bar
        row = df.iloc[-2]
        atr = row.get("atr", float("nan"))
        if pd.isna(atr) or atr <= 0:
            return None

        entry = float(row["close"])
        bar_ts = int(row.get("timestamp", 0))

        # Priority: A > B > C, LONG before SHORT on same bar
        checks = []
        if self.allow_a:
            checks.append(("LONG", "A", "long_a"))
        if self.allow_b:
            checks.append(("LONG", "B", "long_b"))
        if self.allow_c:
            checks.append(("LONG", "C", "long_c"))
        if self.allow_a:
            checks.append(("SHORT", "A", "short_a"))
        if self.allow_b:
            checks.append(("SHORT", "B", "short_b"))
        if self.allow_c:
            checks.append(("SHORT", "C", "short_c"))

        for direction, grade, col in checks:
            if bool(row.get(col, False)):
                sig = self._make_signal(direction, grade, entry, atr, bar_ts)
                logger.info(
                    "Signal: %s-%s entry=%.6f sl=%.6f tp=%s atr=%.6f",
                    direction, grade, entry,
                    sig.sl_price,
                    "%.6f" % sig.tp_price if sig.tp_price else "None",
                    atr,
                )
                return sig
        return None

    def _make_signal(
        self, direction: str, grade: str,
        entry: float, atr: float, bar_ts: int
    ) -> Signal:
        """Construct Signal with ATR-based SL and optional fixed TP."""
        if direction == "LONG":
            sl = entry - self.sl_mult * atr
            tp = (entry + self.tp_mult * atr) if self.tp_mult is not None else None
        else:
            sl = entry + self.sl_mult * atr
            tp = (entry - self.tp_mult * atr) if self.tp_mult is not None else None
        return Signal(
            direction=direction,
            grade=grade,
            entry_price=entry,
            sl_price=sl,
            tp_price=tp,
            atr=atr,
            bar_ts=bar_ts,
        )

    def get_name(self) -> str:
        """Return human-readable plugin name."""
        return "FourPillarsV384"

    def get_version(self) -> str:
        """Return strategy version string."""
        return "3.8.4"

    def warmup_bars(self) -> int:
        """Return minimum bars needed before first valid signal."""
        return 200

    def get_allowed_grades(self) -> list:
        """Return list of grade strings this plugin may emit."""
        grades = []
        if self.allow_a:
            grades.append("A")
        if self.allow_b:
            grades.append("B")
        if self.allow_c:
            grades.append("C")
        return grades

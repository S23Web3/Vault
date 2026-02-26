"""
Timing accumulator for the v3.9.2 performance debug panel.
Usage: from utils.timing import TimingAccumulator, records_to_df
"""
from __future__ import annotations
from typing import Any


class TimingAccumulator:
    """Accumulates per-coin phase timings for display in the performance debug panel."""

    def __init__(self) -> None:
        """Initialize empty accumulator."""
        self.records: list[dict[str, Any]] = []
        self._sym: str | None = None

    def set_symbol(self, symbol: str) -> None:
        """Set the current coin symbol applied to all subsequent record() calls."""
        self._sym = symbol

    def record(self, phase: str, ms: float) -> None:
        """Append a timing entry for the current symbol and phase."""
        self.records.append({"symbol": self._sym, "phase": phase, "ms": round(ms, 2)})

    def to_df(self) -> "Any":
        """Pivot accumulated records into a per-symbol summary DataFrame."""
        import pandas as pd
        if not self.records:
            return pd.DataFrame()
        syms: list[str] = []
        for r in self.records:
            if r["symbol"] not in syms:
                syms.append(r["symbol"])
        rows = []
        for sym in syms:
            row: dict[str, Any] = {"symbol": sym}
            for r in self.records:
                if r["symbol"] == sym:
                    row[r["phase"]] = r["ms"]
            rows.append(row)
        df = pd.DataFrame(rows)
        ms_cols = [c for c in df.columns if c.endswith("_ms")]
        if ms_cols:
            df["total_ms"] = df[ms_cols].sum(axis=1)
        return df


def records_to_df(records: list[dict]) -> "Any":
    """Convert a stored list of timing record dicts to a summary DataFrame."""
    acc = TimingAccumulator()
    acc.records = list(records)
    return acc.to_df()

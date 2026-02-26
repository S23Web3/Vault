"""
Main backtest engine. Reads signals bar-by-bar, manages positions, tracks equity.
Matches v3.7.1 logic: priority chain, cooldown gate, auto-reverse flips.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Optional

from .position import Position, Trade
from .commission import CommissionModel
from .metrics import compute_metrics, trades_to_dataframe


class Backtester:
    """
    Bar-by-bar backtester matching v3.7.1 Pine Script logic.

    For each bar:
        1. Check exit conditions on current position (SL/TP)
        2. Check entry signals (A > BC flip > BC new > re-entry)
        3. Apply cooldown gate
        4. Execute entries/exits with commission
        5. At 5pm UTC: credit commission rebate
    """

    def __init__(self, params: dict = None):
        p = params or {}

        # Strategy params
        self.sl_mult = p.get("sl_mult", 1.0)
        self.tp_mult = p.get("tp_mult", 1.5)
        self.use_tp = p.get("use_tp", True)
        self.cooldown = p.get("cooldown", 3)
        self.b_open_fresh = p.get("b_open_fresh", True)
        self.notional = p.get("notional", 10000.0)
        self.be_raise_amount = p.get("be_raise_amount", 0.0)

        # Commission
        self.comm = CommissionModel(
            cost_per_side=p.get("cost_per_side", 6.0),
            rebate_pct=p.get("rebate_pct", 0.70),
            settlement_hour_utc=p.get("settlement_hour_utc", 17),
        )

        # State
        self.position: Optional[Position] = None
        self.entry_bar: Optional[int] = None
        self.trades: list[Trade] = []
        self.initial_equity = p.get("initial_equity", 10000.0)

    def run(self, df: pd.DataFrame) -> dict:
        """
        Run backtest on a DataFrame with signal columns.
        Expects columns from signals.four_pillars.compute_signals().

        Returns dict with trades, metrics, equity_curve.
        """
        n = len(df)
        equity = self.initial_equity
        equity_curve = np.full(n, equity)

        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        atr = df["atr"].values

        # Signal columns
        long_a = df["long_a"].values
        long_b = df["long_b"].values
        long_c = df["long_c"].values
        short_a = df["short_a"].values
        short_b = df["short_b"].values
        short_c = df["short_c"].values
        reentry_long = df["reentry_long"].values
        reentry_short = df["reentry_short"].values

        # Datetime for commission settlement — check both column and index
        if "datetime" in df.columns:
            datetimes = df["datetime"].values
            has_datetime = True
        elif df.index.name == "datetime" or isinstance(df.index, pd.DatetimeIndex):
            datetimes = df.index.values
            has_datetime = True
        else:
            datetimes = None
            has_datetime = False

        for i in range(n):
            # Skip bars where ATR isn't ready
            if np.isnan(atr[i]):
                equity_curve[i] = equity
                continue

            # ── Commission settlement check ──
            if has_datetime and datetimes is not None:
                bar_dt = pd.Timestamp(datetimes[i]).to_pydatetime()
                if bar_dt.tzinfo is None:
                    bar_dt = bar_dt.replace(tzinfo=timezone.utc)
                rebate = self.comm.check_settlement(bar_dt)
                equity += rebate

            # ── Check exit on current position ──
            if self.position is not None:
                exit_reason = self.position.update(high[i], low[i], close[i])
                if exit_reason is not None:
                    # Exit at SL or TP price
                    if exit_reason == "SL":
                        exit_price = self.position.sl
                    elif exit_reason == "TP":
                        exit_price = self.position.tp
                    else:
                        exit_price = close[i]

                    comm_exit = self.comm.charge()
                    trade = self.position.close_at(exit_price, i, exit_reason, comm_exit + self.comm.cost_per_side)
                    # Note: entry commission was already charged, so trade.commission = entry + exit
                    self.trades.append(trade)
                    equity += trade.pnl - comm_exit  # Entry comm already deducted
                    self.position = None

            # ── Cooldown gate ──
            cooldown_ok = (self.entry_bar is None or (i - self.entry_bar >= self.cooldown))

            if not cooldown_ok:
                equity_curve[i] = equity
                continue

            is_flat = self.position is None
            pos_dir = self.position.direction if self.position else "FLAT"

            # ── Entry priority chain (matches v3.7.1 lines 288-375) ──
            enter_dir = None
            enter_grade = None

            # A signals — can open and flip
            if long_a[i] and (is_flat or pos_dir == "SHORT"):
                enter_dir = "LONG"
                enter_grade = "A"
            elif short_a[i] and (is_flat or pos_dir == "LONG"):
                enter_dir = "SHORT"
                enter_grade = "A"

            # BC flip
            elif not is_flat and self.b_open_fresh:
                if (long_b[i] or long_c[i]) and pos_dir == "SHORT":
                    enter_dir = "LONG"
                    enter_grade = "B" if long_b[i] else "C"
                elif (short_b[i] or short_c[i]) and pos_dir == "LONG":
                    enter_dir = "SHORT"
                    enter_grade = "B" if short_b[i] else "C"

            # BC new (flat only when b_open_fresh)
            if enter_dir is None and is_flat and self.b_open_fresh:
                if long_b[i] or long_c[i]:
                    enter_dir = "LONG"
                    enter_grade = "B" if long_b[i] else "C"
                elif short_b[i] or short_c[i]:
                    enter_dir = "SHORT"
                    enter_grade = "B" if short_b[i] else "C"

            # Re-entry (flat only)
            if enter_dir is None and is_flat:
                if reentry_long[i]:
                    enter_dir = "LONG"
                    enter_grade = "R"
                elif reentry_short[i]:
                    enter_dir = "SHORT"
                    enter_grade = "R"

            # ── Execute entry ──
            if enter_dir is not None:
                # Close existing position if flipping
                if not is_flat:
                    comm_exit = self.comm.charge()
                    trade = self.position.close_at(close[i], i, "FLIP", comm_exit + self.comm.cost_per_side)
                    self.trades.append(trade)
                    equity += trade.pnl - comm_exit
                    self.position = None

                # Open new position
                comm_entry = self.comm.charge()
                equity -= comm_entry

                self.position = Position(
                    direction=enter_dir,
                    grade=enter_grade,
                    entry_bar=i,
                    entry_price=close[i],
                    atr=atr[i],
                    sl_mult=self.sl_mult,
                    tp_mult=self.tp_mult,
                    use_tp=self.use_tp,
                    notional=self.notional,
                    be_raise_amount=self.be_raise_amount,
                )
                self.entry_bar = i

            equity_curve[i] = equity

        # Close any remaining position at last bar
        if self.position is not None:
            comm_exit = self.comm.charge()
            trade = self.position.close_at(close[-1], n - 1, "END", comm_exit + self.comm.cost_per_side)
            self.trades.append(trade)
            equity += trade.pnl - comm_exit
            equity_curve[-1] = equity

        metrics = compute_metrics(self.trades, equity_curve)
        metrics["final_equity"] = equity
        metrics["equity_curve"] = equity_curve

        return {
            "trades": self.trades,
            "trades_df": trades_to_dataframe(self.trades),
            "metrics": metrics,
            "equity_curve": equity_curve,
        }

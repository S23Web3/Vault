"""
v3.8.2 backtest engine: AVWAP 3-stage trailing SL, 4 position slots,
limit adds, re-entry after stop-out. No TP (runner strategy).

Per-bar execution order (matches Pine Script v3.8.2):
1. Commission settlement check
2. Check exits on all slots (using SL from previous bar)
3. Update AVWAP + SL for remaining slots (sets SL for next bar)
4. Process pending limit orders (cancel / fill)
5. Check stochastic entries (A/B/C/R)
6. Check AVWAP adds
7. Check AVWAP re-entry
"""

import numpy as np
import pandas as pd
from datetime import timezone
from typing import Optional

from .position_v382 import PositionSlot, Trade382
from .commission import CommissionModel
from .metrics import compute_metrics, trades_to_dataframe


class Backtester382:
    """v3.8.2 multi-slot backtester with AVWAP trailing stop."""

    def __init__(self, params: dict = None):
        p = params or {}

        # AVWAP trailing params
        self.sigma_floor_atr = p.get("sigma_floor_atr", 0.5)
        self.sl_atr_mult = p.get("sl_atr_mult", 1.0)
        self.stage1to2_trigger = p.get("stage1to2_trigger", "opposite_2sigma")
        self.stage2_bars = p.get("stage2_bars", 5)

        # Position management
        self.max_positions = p.get("max_positions", 4)
        self.cooldown = p.get("cooldown", 3)
        self.b_open_fresh = p.get("b_open_fresh", True)
        self.notional = p.get("notional", 5000.0)

        # AVWAP adds + re-entry
        self.enable_adds = p.get("enable_adds", True)
        self.enable_reentry = p.get("enable_reentry", True)
        self.cancel_bars = p.get("cancel_bars", 3)
        self.reentry_window = p.get("reentry_window", 5)
        self.max_avwap_age = p.get("max_avwap_age", 50)

        # BE raise (multi-level)
        self.be_levels = p.get("be_levels", [])

        # Commission (maker=0.02% for limits, taker=0.08% for market/stops)
        self.comm = CommissionModel(
            commission_rate=p.get("commission_rate", 0.0008),
            maker_rate=p.get("maker_rate", 0.0002),
            notional=self.notional,
            rebate_pct=p.get("rebate_pct", 0.50),
            settlement_hour_utc=p.get("settlement_hour_utc", 17),
        )

        # State
        self.initial_equity = p.get("initial_equity", 10000.0)

    def run(self, df: pd.DataFrame) -> dict:
        """Run v3.8.2 backtest on signal-enriched DataFrame."""

        n = len(df)
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        atr = df["atr"].values
        hlc3 = (high + low + close) / 3.0
        vol = df["base_vol"].values if "base_vol" in df.columns else np.ones(n)

        # Cloud 3 boundaries (for stage 3 SL)
        cloud3_top = df["cloud3_top"].values
        cloud3_bottom = df["cloud3_bottom"].values
        cloud3_ok_long = df["cloud3_allows_long"].values
        cloud3_ok_short = df["cloud3_allows_short"].values

        # Signals
        long_a = df["long_a"].values
        long_b = df["long_b"].values
        long_c = df["long_c"].values
        short_a = df["short_a"].values
        short_b = df["short_b"].values
        short_c = df["short_c"].values
        reentry_long = df["reentry_long"].values
        reentry_short = df["reentry_short"].values

        # Datetimes for commission settlement
        if "datetime" in df.columns:
            datetimes = df["datetime"].values
            has_dt = True
        elif df.index.name == "datetime" or isinstance(df.index, pd.DatetimeIndex):
            datetimes = df.index.values
            has_dt = True
        else:
            datetimes = None
            has_dt = False

        # State
        slots: list[Optional[PositionSlot]] = [None] * 4
        last_entry_bar: Optional[int] = None
        trades: list[Trade382] = []
        equity = self.initial_equity
        equity_curve = np.full(n, equity)

        # Pending limit order state
        pend_bar: Optional[int] = None
        pend_dir: int = 0       # 1=long, -1=short, 0=none
        pend_limit: Optional[float] = None
        pend_grade: str = ""

        # Re-entry state (frozen AVWAP after stop-out)
        re_bar: Optional[int] = None
        re_dir: int = 0
        re_avwap: Optional[float] = None
        re_sigma: Optional[float] = None

        for i in range(n):
            if np.isnan(atr[i]) or np.isnan(cloud3_top[i]):
                equity_curve[i] = equity
                continue

            # --- Commission settlement ---
            if has_dt and datetimes is not None:
                bar_dt = pd.Timestamp(datetimes[i]).to_pydatetime()
                if bar_dt.tzinfo is None:
                    bar_dt = bar_dt.replace(tzinfo=timezone.utc)
                rebate = self.comm.check_settlement(bar_dt)
                equity += rebate

            # --- Step 1: Check exits (SL from previous bar) ---
            for s in range(4):
                if slots[s] is None:
                    continue
                exit_reason = slots[s].check_exit(high[i], low[i])
                if exit_reason:
                    comm_exit = self.comm.charge()  # taker (stop-market)
                    trade = slots[s].close_at(
                        slots[s].sl, i, exit_reason,
                        comm_exit + slots[s].entry_commission
                    )
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    # Save re-entry state
                    if self.enable_reentry:
                        re_bar = i
                        re_dir = 1 if slots[s].direction == "LONG" else -1
                        re_avwap = slots[s].avwap.center
                        re_sigma = slots[s].avwap.sigma
                    slots[s] = None

            # --- Step 2: Update AVWAP + SL for remaining slots ---
            for s in range(4):
                if slots[s] is None:
                    continue
                slots[s].update_bar(
                    i, high[i], low[i], close[i], atr[i],
                    hlc3[i], vol[i], cloud3_top[i], cloud3_bottom[i]
                )

            # --- Step 3: Process pending limits ---
            if pend_dir != 0 and pend_bar is not None:
                if i - pend_bar >= self.cancel_bars:
                    # Cancel unfilled
                    pend_bar = None
                    pend_dir = 0
                    pend_limit = None
                    pend_grade = ""
                else:
                    # Check fill
                    filled = False
                    if pend_dir == 1 and low[i] <= pend_limit:
                        filled = True
                    elif pend_dir == -1 and high[i] >= pend_limit:
                        filled = True

                    if filled:
                        empty = self._find_empty(slots)
                        if empty >= 0:
                            comm_entry = self.comm.charge(maker=True)  # limit fill
                            equity -= comm_entry
                            direction = "LONG" if pend_dir == 1 else "SHORT"
                            slots[empty] = PositionSlot(
                                direction=direction,
                                grade=pend_grade,
                                entry_bar=i,
                                entry_price=pend_limit,
                                atr=atr[i],
                                hlc3=hlc3[i],
                                volume=vol[i],
                                sigma_floor_atr=self.sigma_floor_atr,
                                sl_atr_mult=self.sl_atr_mult,
                                stage1to2_trigger=self.stage1to2_trigger,
                                stage2_bars=self.stage2_bars,
                                notional=self.notional,
                                be_levels=self.be_levels,
                            )
                            slots[empty].entry_commission = comm_entry
                            last_entry_bar = i
                        pend_bar = None
                        pend_dir = 0
                        pend_limit = None
                        pend_grade = ""

            # --- Step 4: Stochastic entries ---
            active_count = sum(1 for s in slots if s is not None)
            cooldown_ok = last_entry_bar is None or (i - last_entry_bar >= self.cooldown)
            can_enter = active_count < self.max_positions and cooldown_ok

            has_longs = any(s is not None and s.direction == "LONG" for s in slots)
            has_shorts = any(s is not None and s.direction == "SHORT" for s in slots)

            # A: no Cloud 3 gate; B/C/R: Cloud 3 gated
            can_long_a = not has_shorts and can_enter
            can_short_a = not has_longs and can_enter
            can_long = not has_shorts and can_enter and bool(cloud3_ok_long[i])
            can_short = not has_longs and can_enter and bool(cloud3_ok_short[i])

            did_enter = False

            # A long
            if long_a[i] and can_long_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "LONG", "A", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()  # taker (market)
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            # A short
            if short_a[i] and can_short_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "SHORT", "A", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()  # taker (market)
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            # BC long
            if not did_enter and (long_b[i] or long_c[i]) and can_long and self.b_open_fresh:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    grade = "B" if long_b[i] else "C"
                    self._open_slot(slots, empty, "LONG", grade, i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()  # taker (market)
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            # BC short
            if not did_enter and (short_b[i] or short_c[i]) and can_short and self.b_open_fresh:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    grade = "B" if short_b[i] else "C"
                    self._open_slot(slots, empty, "SHORT", grade, i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()  # taker (market)
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            # Cloud 2 re-entry long
            if not did_enter and reentry_long[i] and can_long:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "LONG", "R", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()  # taker (market)
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            # Cloud 2 re-entry short
            if not did_enter and reentry_short[i] and can_short:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "SHORT", "R", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()  # taker (market)
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            # --- Step 5: AVWAP adds ---
            active_count = sum(1 for s in slots if s is not None)
            if (self.enable_adds and pend_dir == 0 and not did_enter
                    and active_count < self.max_positions and cooldown_ok):
                for s in range(4):
                    if slots[s] is None or pend_dir != 0:
                        continue
                    av = slots[s].avwap
                    if av.center == 0 or av.sigma == 0:
                        continue
                    if i - slots[s].entry_bar > self.max_avwap_age:
                        continue

                    p2 = av.center + 2 * av.sigma
                    m2 = av.center - 2 * av.sigma
                    p1 = av.center + av.sigma
                    m1 = av.center - av.sigma

                    if slots[s].direction == "LONG" and low[i] <= m2 and bool(cloud3_ok_long[i]):
                        pend_bar = i
                        pend_dir = 1
                        pend_limit = m1
                        pend_grade = "ADD"
                        break
                    elif slots[s].direction == "SHORT" and high[i] >= p2 and bool(cloud3_ok_short[i]):
                        pend_bar = i
                        pend_dir = -1
                        pend_limit = p1
                        pend_grade = "ADD"
                        break

            # --- Step 6: AVWAP re-entry ---
            active_count = sum(1 for s in slots if s is not None)
            if (self.enable_reentry and re_dir != 0 and pend_dir == 0 and not did_enter):
                re_ok = (re_dir == 1 and not has_shorts) or (re_dir == -1 and not has_longs)
                if re_ok:
                    if re_bar is not None and i - re_bar > self.reentry_window:
                        re_bar = None
                        re_dir = 0
                        re_avwap = None
                        re_sigma = None
                    elif (re_avwap is not None and re_sigma is not None
                          and active_count < self.max_positions and cooldown_ok):
                        re_p2 = re_avwap + 2 * re_sigma
                        re_m2 = re_avwap - 2 * re_sigma
                        re_p1 = re_avwap + re_sigma
                        re_m1 = re_avwap - re_sigma

                        if re_dir == 1 and low[i] <= re_m2 and bool(cloud3_ok_long[i]):
                            pend_bar = i
                            pend_dir = 1
                            pend_limit = re_m1
                            pend_grade = "RE"
                            re_dir = 0
                        elif re_dir == -1 and high[i] >= re_p2 and bool(cloud3_ok_short[i]):
                            pend_bar = i
                            pend_dir = -1
                            pend_limit = re_p1
                            pend_grade = "RE"
                            re_dir = 0

            equity_curve[i] = equity

        # Close remaining positions at last bar
        for s in range(4):
            if slots[s] is not None:
                comm_exit = self.comm.charge()  # taker (market close)
                trade = slots[s].close_at(
                    close[-1], n - 1, "END",
                    comm_exit + slots[s].entry_commission
                )
                trades.append(trade)
                equity += trade.pnl - comm_exit
        equity_curve[-1] = equity

        metrics = compute_metrics(trades, equity_curve)
        metrics["final_equity"] = equity
        metrics["equity_curve"] = equity_curve
        metrics["total_rebate"] = self.comm.total_rebate

        return {
            "trades": trades,
            "trades_df": trades_to_dataframe(trades),
            "metrics": metrics,
            "equity_curve": equity_curve,
        }

    def _find_empty(self, slots) -> int:
        """Find first empty slot. Returns index or -1."""
        for i in range(4):
            if slots[i] is None:
                return i
        return -1

    def _open_slot(self, slots, idx, direction, grade, bar_idx,
                   entry_price, atr, hlc3, volume):
        """Create a new PositionSlot in the given index."""
        slots[idx] = PositionSlot(
            direction=direction,
            grade=grade,
            entry_bar=bar_idx,
            entry_price=entry_price,
            atr=atr,
            hlc3=hlc3,
            volume=volume,
            sigma_floor_atr=self.sigma_floor_atr,
            sl_atr_mult=self.sl_atr_mult,
            stage1to2_trigger=self.stage1to2_trigger,
            stage2_bars=self.stage2_bars,
            notional=self.notional,
            be_levels=self.be_levels,
        )

"""
v3.8.4 backtest engine: ATR SL + optional ATR TP, scale-out, D signal, AVWAP inheritance.

v3.8.4 adds: tp_mult parameter for ATR-based take profit.
tp_mult=None: no TP (identical to v3.8.3 behavior).
tp_mult=X: TP at entry_price +/- ATR * X. Closes full position on TP hit.

Per-bar execution order (same as v3.8.3):
1. Commission settlement check
2. Check exits on all slots (SL/TP from previous bar)
3. Update AVWAP + SL for remaining slots
4. Check scale-outs on remaining slots
5. Process pending limit orders (cancel / fill)
6. Check stochastic entries (A/B/C/D/R)
7. Check AVWAP adds (limit orders with AVWAP inheritance)
8. Check AVWAP re-entry (limit orders with AVWAP inheritance)
"""

import numpy as np
import pandas as pd
from datetime import timezone
from typing import Optional

from .position_v384 import PositionSlot384, Trade384
from .commission import CommissionModel
from .avwap import AVWAPTracker


class Backtester384:
    """v3.8.4 multi-slot backtester with TP + scale-out."""

    def __init__(self, params: dict = None):
        p = params or {}

        # SL/TP/BE params
        self.sigma_floor_atr = p.get("sigma_floor_atr", 0.5)
        self.sl_mult = p.get("sl_mult", 2.0)
        self.tp_mult = p.get("tp_mult", None)
        self.be_trigger_atr = p.get("be_trigger_atr", 0.0)
        self.be_lock_atr = p.get("be_lock_atr", 0.0)

        # Scale-out params
        self.checkpoint_interval = p.get("checkpoint_interval", 5)
        self.max_scaleouts = p.get("max_scaleouts", 2)

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

        # Commission
        self.comm = CommissionModel(
            commission_rate=p.get("commission_rate", 0.0008),
            maker_rate=p.get("maker_rate", 0.0002),
            notional=self.notional,
            rebate_pct=p.get("rebate_pct", 0.70),
            settlement_hour_utc=p.get("settlement_hour_utc", 17),
        )

        self.initial_equity = p.get("initial_equity", 10000.0)

    def run(self, df: pd.DataFrame) -> dict:
        n = len(df)
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        atr = df["atr"].values
        hlc3 = (high + low + close) / 3.0
        vol = df["base_vol"].values if "base_vol" in df.columns else np.ones(n)

        cloud3_ok_long = df["cloud3_allows_long"].values
        cloud3_ok_short = df["cloud3_allows_short"].values

        long_a = df["long_a"].values
        long_b = df["long_b"].values
        long_c = df["long_c"].values
        long_d = df["long_d"].values if "long_d" in df.columns else np.zeros(n, dtype=bool)
        short_a = df["short_a"].values
        short_b = df["short_b"].values
        short_c = df["short_c"].values
        short_d = df["short_d"].values if "short_d" in df.columns else np.zeros(n, dtype=bool)
        reentry_long = df["reentry_long"].values
        reentry_short = df["reentry_short"].values

        if "datetime" in df.columns:
            datetimes = df["datetime"].values
            has_dt = True
        elif df.index.name == "datetime" or isinstance(df.index, pd.DatetimeIndex):
            datetimes = df.index.values
            has_dt = True
        else:
            datetimes = None
            has_dt = False

        slots: list[Optional[PositionSlot384]] = [None] * 4
        last_entry_bar: Optional[int] = None
        trades: list[Trade384] = []
        equity = self.initial_equity
        equity_curve = np.full(n, equity)
        position_counts = np.zeros(n, dtype=int)

        pend_bar: Optional[int] = None
        pend_dir: int = 0
        pend_limit: Optional[float] = None
        pend_grade: str = ""
        pend_avwap_state: Optional[AVWAPTracker] = None

        re_bar: Optional[int] = None
        re_dir: int = 0
        re_avwap_tracker: Optional[AVWAPTracker] = None

        for i in range(n):
            if np.isnan(atr[i]):
                equity_curve[i] = equity
                continue

            # --- Commission settlement ---
            if has_dt and datetimes is not None:
                bar_dt = pd.Timestamp(datetimes[i]).to_pydatetime()
                if bar_dt.tzinfo is None:
                    bar_dt = bar_dt.replace(tzinfo=timezone.utc)
                rebate = self.comm.check_settlement(bar_dt)
                equity += rebate

            # --- Step 1: Check exits (SL/TP) ---
            for s in range(4):
                if slots[s] is None:
                    continue
                exit_reason = slots[s].check_exit(high[i], low[i])
                if exit_reason:
                    # Exit price: SL at sl_price, TP at tp_price
                    if exit_reason == "TP":
                        exit_price = slots[s].tp
                    else:
                        exit_price = slots[s].sl
                    comm_exit = self.comm.charge_custom(slots[s].notional, maker=True)
                    trade = slots[s].close_at(
                        exit_price, i, exit_reason,
                        comm_exit + slots[s].entry_commission
                    )
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    if self.enable_reentry and exit_reason == "SL":
                        re_bar = i
                        re_dir = 1 if slots[s].direction == "LONG" else -1
                        re_avwap_tracker = slots[s].avwap.clone()
                    slots[s] = None

            # --- Step 2: Update AVWAP + SL ---
            for s in range(4):
                if slots[s] is None:
                    continue
                slots[s].update_bar(i, high[i], low[i], close[i], atr[i], hlc3[i], vol[i])

            # --- Step 3: Scale-outs ---
            for s in range(4):
                if slots[s] is None:
                    continue
                if slots[s].check_scale_out(i, close[i]):
                    close_notional = slots[s].notional
                    is_final_check = (slots[s].scale_count + 1 >= slots[s].max_scaleouts)
                    if is_final_check:
                        scale_notional = close_notional
                    else:
                        scale_notional = close_notional / 2
                    comm_exit = self.comm.charge_custom(scale_notional, maker=True)
                    entry_comm_share = slots[s].entry_commission * scale_notional / slots[s].original_notional
                    trade_comm = comm_exit + entry_comm_share
                    trade, is_final = slots[s].do_scale_out(i, close[i], trade_comm)
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    if is_final:
                        slots[s] = None

            # --- Step 4: Pending limits ---
            if pend_dir != 0 and pend_bar is not None:
                if i - pend_bar >= self.cancel_bars:
                    pend_bar = None
                    pend_dir = 0
                    pend_limit = None
                    pend_grade = ""
                    pend_avwap_state = None
                else:
                    filled = False
                    if pend_dir == 1 and low[i] <= pend_limit:
                        filled = True
                    elif pend_dir == -1 and high[i] >= pend_limit:
                        filled = True

                    if filled:
                        empty = self._find_empty(slots)
                        if empty >= 0:
                            comm_entry = self.comm.charge(maker=True)
                            equity -= comm_entry
                            direction = "LONG" if pend_dir == 1 else "SHORT"
                            slots[empty] = PositionSlot384(
                                direction=direction,
                                grade=pend_grade,
                                entry_bar=i,
                                entry_price=pend_limit,
                                atr=atr[i],
                                hlc3=hlc3[i],
                                volume=vol[i],
                                sigma_floor_atr=self.sigma_floor_atr,
                                sl_mult=self.sl_mult,
                                tp_mult=self.tp_mult,
                                be_trigger_atr=self.be_trigger_atr,
                                be_lock_atr=self.be_lock_atr,
                                notional=self.notional,
                                checkpoint_interval=self.checkpoint_interval,
                                max_scaleouts=self.max_scaleouts,
                                avwap_state=pend_avwap_state,
                            )
                            slots[empty].entry_commission = comm_entry
                            last_entry_bar = i
                        pend_bar = None
                        pend_dir = 0
                        pend_limit = None
                        pend_grade = ""
                        pend_avwap_state = None

            # --- Step 5: Stochastic entries ---
            active_count = sum(1 for s in slots if s is not None)
            cooldown_ok = last_entry_bar is None or (i - last_entry_bar >= self.cooldown)
            can_enter = active_count < self.max_positions and cooldown_ok

            has_longs = any(s is not None and s.direction == "LONG" for s in slots)
            has_shorts = any(s is not None and s.direction == "SHORT" for s in slots)

            can_long_a = not has_shorts and can_enter
            can_short_a = not has_longs and can_enter
            can_long = not has_shorts and can_enter and bool(cloud3_ok_long[i])
            can_short = not has_longs and can_enter and bool(cloud3_ok_short[i])

            did_enter = False

            if long_a[i] and can_long_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "LONG", "A", i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            if short_a[i] and can_short_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "SHORT", "A", i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            if not did_enter and (long_b[i] or long_c[i]) and can_long and self.b_open_fresh:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    grade = "B" if long_b[i] else "C"
                    self._open_slot(slots, empty, "LONG", grade, i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            if not did_enter and (short_b[i] or short_c[i]) and can_short and self.b_open_fresh:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    grade = "B" if short_b[i] else "C"
                    self._open_slot(slots, empty, "SHORT", grade, i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            if not did_enter and long_d[i] and can_long_a:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "LONG", "D", i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            if not did_enter and short_d[i] and can_short_a:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "SHORT", "D", i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            if not did_enter and reentry_long[i] and can_long:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "LONG", "R", i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            if not did_enter and reentry_short[i] and can_short:
                empty = self._find_empty(slots)
                if empty >= 0:
                    did_enter = True
                    self._open_slot(slots, empty, "SHORT", "R", i, close[i], atr[i], hlc3[i], vol[i])
                    comm_entry = self.comm.charge()
                    equity -= comm_entry
                    slots[empty].entry_commission = comm_entry
                    last_entry_bar = i

            # --- Step 6: AVWAP adds ---
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
                        pend_avwap_state = slots[s].avwap.clone()
                        break
                    elif slots[s].direction == "SHORT" and high[i] >= p2 and bool(cloud3_ok_short[i]):
                        pend_bar = i
                        pend_dir = -1
                        pend_limit = p1
                        pend_grade = "ADD"
                        pend_avwap_state = slots[s].avwap.clone()
                        break

            # --- Step 7: AVWAP re-entry ---
            active_count = sum(1 for s in slots if s is not None)
            if (self.enable_reentry and re_dir != 0 and pend_dir == 0 and not did_enter):
                re_ok = (re_dir == 1 and not has_shorts) or (re_dir == -1 and not has_longs)
                if re_ok:
                    if re_bar is not None and i - re_bar > self.reentry_window:
                        re_bar = None
                        re_dir = 0
                        re_avwap_tracker = None
                    elif (re_avwap_tracker is not None
                          and active_count < self.max_positions and cooldown_ok):
                        re_c = re_avwap_tracker.center
                        re_s = re_avwap_tracker.sigma
                        re_p2 = re_c + 2 * re_s
                        re_m2 = re_c - 2 * re_s
                        re_p1 = re_c + re_s
                        re_m1 = re_c - re_s

                        if re_dir == 1 and low[i] <= re_m2 and bool(cloud3_ok_long[i]):
                            pend_bar = i
                            pend_dir = 1
                            pend_limit = re_m1
                            pend_grade = "RE"
                            pend_avwap_state = re_avwap_tracker.clone()
                            re_dir = 0
                        elif re_dir == -1 and high[i] >= re_p2 and bool(cloud3_ok_short[i]):
                            pend_bar = i
                            pend_dir = -1
                            pend_limit = re_p1
                            pend_grade = "RE"
                            pend_avwap_state = re_avwap_tracker.clone()
                            re_dir = 0

            position_counts[i] = sum(1 for s in slots if s is not None)
            # Mark-to-market: realized equity + unrealized P&L from open positions
            unrealized = 0.0
            for s in range(4):
                if slots[s] is not None:
                    if slots[s].direction == "LONG":
                        unrealized += (close[i] - slots[s].entry_price) / slots[s].entry_price * slots[s].notional
                    else:
                        unrealized += (slots[s].entry_price - close[i]) / slots[s].entry_price * slots[s].notional
            equity_curve[i] = equity + unrealized

        # Close remaining at last bar
        for s in range(4):
            if slots[s] is not None:
                comm_exit = self.comm.charge_custom(slots[s].notional, maker=True)
                trade = slots[s].close_at(
                    close[-1], n - 1, "END",
                    comm_exit + slots[s].entry_commission
                )
                trades.append(trade)
                equity += trade.pnl - comm_exit
        equity_curve[-1] = equity

        metrics = self._compute_metrics(trades, equity_curve)
        metrics["final_equity"] = equity
        metrics["equity_curve"] = equity_curve
        metrics["total_rebate"] = self.comm.total_rebate
        metrics["net_pnl_after_rebate"] = metrics["net_pnl"] + self.comm.total_rebate
        metrics["total_volume"] = self.comm.total_volume
        metrics["total_sides"] = self.comm.total_sides

        # Capital utilization
        margin_per_pos = self.notional / 20.0
        valid_counts = position_counts[~np.isnan(atr)]
        if len(valid_counts) > 0:
            metrics["avg_positions"] = float(np.mean(valid_counts))
            metrics["max_positions_used"] = int(np.max(valid_counts))
            metrics["pct_time_flat"] = float(np.sum(valid_counts == 0) / len(valid_counts))
            metrics["avg_margin_used"] = float(np.mean(valid_counts) * margin_per_pos)
            metrics["peak_margin_used"] = float(np.max(valid_counts) * margin_per_pos)
        else:
            metrics["avg_positions"] = 0
            metrics["max_positions_used"] = 0
            metrics["pct_time_flat"] = 1.0
            metrics["avg_margin_used"] = 0
            metrics["peak_margin_used"] = 0

        return {
            "trades": trades,
            "trades_df": self._trades_to_df(trades),
            "metrics": metrics,
            "equity_curve": equity_curve,
            "position_counts": position_counts,
        }

    def _find_empty(self, slots) -> int:
        for i in range(4):
            if slots[i] is None:
                return i
        return -1

    def _open_slot(self, slots, idx, direction, grade, bar_idx,
                   entry_price, atr, hlc3, volume):
        slots[idx] = PositionSlot384(
            direction=direction,
            grade=grade,
            entry_bar=bar_idx,
            entry_price=entry_price,
            atr=atr,
            hlc3=hlc3,
            volume=volume,
            sigma_floor_atr=self.sigma_floor_atr,
            sl_mult=self.sl_mult,
            tp_mult=self.tp_mult,
            be_trigger_atr=self.be_trigger_atr,
            be_lock_atr=self.be_lock_atr,
            notional=self.notional,
            checkpoint_interval=self.checkpoint_interval,
            max_scaleouts=self.max_scaleouts,
            avwap_state=None,
        )

    def _compute_metrics(self, trades, equity_curve):
        if not trades:
            return {"total_trades": 0}

        pnls = np.array([t.pnl for t in trades])
        net_pnls = np.array([t.pnl - t.commission for t in trades])
        commissions = np.array([t.commission for t in trades])

        winners = net_pnls[net_pnls > 0]
        losers = net_pnls[net_pnls <= 0]

        total = len(trades)
        win_count = len(winners)
        win_rate = win_count / total if total > 0 else 0

        gross_profit = float(np.sum(winners)) if len(winners) > 0 else 0.0
        gross_loss = float(np.abs(np.sum(losers))) if len(losers) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        saw_green_losers = sum(1 for t in trades if t.saw_green and t.pnl - t.commission <= 0)
        total_losers = sum(1 for t in trades if t.pnl - t.commission <= 0)

        # Exit reason breakdown
        tp_count = sum(1 for t in trades if t.exit_reason == "TP")
        sl_count = sum(1 for t in trades if t.exit_reason == "SL")

        grades = {}
        for grade in ["A", "B", "C", "D", "ADD", "RE", "R"]:
            grade_trades = [t for t in trades if t.grade == grade]
            if grade_trades:
                grade_pnls = [t.pnl - t.commission for t in grade_trades]
                grade_tp = sum(1 for t in grade_trades if t.exit_reason == "TP")
                grades[grade] = {
                    "count": len(grade_trades),
                    "win_rate": sum(1 for p in grade_pnls if p > 0) / len(grade_trades),
                    "avg_pnl": float(np.mean(grade_pnls)),
                    "total_pnl": float(np.sum(grade_pnls)),
                    "tp_exits": grade_tp,
                }

        scale_trades = [t for t in trades if t.scale_idx > 0]
        scale_count = len(scale_trades)

        if len(net_pnls) > 1:
            sharpe = float(np.mean(net_pnls) / np.std(net_pnls)) if np.std(net_pnls) > 0 else 0
        else:
            sharpe = 0

        max_dd = 0.0
        max_dd_pct = 0.0
        if equity_curve is not None and len(equity_curve) > 0:
            peak = np.maximum.accumulate(equity_curve)
            drawdown = peak - equity_curve
            max_dd = float(np.max(drawdown))
            max_dd_pct = float(np.max(drawdown / peak) * 100) if np.max(peak) > 0 else 0

        return {
            "total_trades": total,
            "win_count": win_count,
            "loss_count": len(losers),
            "win_rate": win_rate,
            "avg_win": float(np.mean(winners)) if len(winners) > 0 else 0,
            "avg_loss": float(np.mean(losers)) if len(losers) > 0 else 0,
            "expectancy": float(np.mean(net_pnls)),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "net_pnl": float(np.sum(net_pnls)),
            "total_commission": float(np.sum(commissions)),
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd_pct,
            "pct_losers_saw_green": saw_green_losers / total_losers if total_losers > 0 else 0,
            "saw_green_losers": saw_green_losers,
            "total_losers": total_losers,
            "be_raised_count": sum(1 for t in trades if t.be_raised),
            "scale_out_count": scale_count,
            "tp_exits": tp_count,
            "sl_exits": sl_count,
            "grades": grades,
        }

    def _trades_to_df(self, trades):
        if not trades:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "direction": t.direction,
                "grade": t.grade,
                "entry_bar": t.entry_bar,
                "exit_bar": t.exit_bar,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "sl_price": t.sl_price,
                "tp_price": t.tp_price,
                "pnl": t.pnl,
                "commission": t.commission,
                "net_pnl": t.pnl - t.commission,
                "mfe": t.mfe,
                "mae": t.mae,
                "exit_reason": t.exit_reason,
                "saw_green": t.saw_green,
                "scale_idx": t.scale_idx,
            }
            for t in trades
        ])

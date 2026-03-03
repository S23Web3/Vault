"""
Four Pillars v3.9.0 backtest engine.

KEY CHANGES FROM backtester_v384.py:
- Grade C redefined: no longer a state machine signal.
  Grade C = continuation/pyramid entry when A or B fires while ALREADY
  in a same-direction position. Controlled by allow_c_trades param.
  This aligns with Pine strategy i_bOpenFresh=false behaviour:
    - i_bOpenFresh=true  → B/C signals can open fresh positions
    - i_bOpenFresh=false → B/C only pyramid existing positions
  In v390, C is ALWAYS a pyramid label. A and B can open fresh OR pyramid.
  allow_c_trades gates whether pyramid entries are taken at all.

- require_stage2 / rot_level removed from signal params.

- BBW columns from df captured at trade entry and stored in Trade390 record
  for analysis. bbwp_state at entry tells volatility context per trade.

- signal pipeline: four_pillars_v390.compute_signals()

Entry priority (matches Pine Section 16):
  1. Long A (fresh or pyramid)
  2. Short A (fresh or pyramid)
  3. Long B (fresh or pyramid, requires cloud3)
  4. Short B (fresh or pyramid, requires cloud3)
  5. Long RE (cloud2 reentry)
  6. Short RE (cloud2 reentry)
  7. Long C  (A or B signal while long open) — only if allow_c_trades
  8. Short C (A or B signal while short open) — only if allow_c_trades

Wait: C is just a relabelling of A/B when in-position. The priority chain
collapses: when already in LONG and long_a fires → enter grade C (pyramid).
"""

import numpy as np
import pandas as pd
from datetime import timezone
from typing import Optional
from dataclasses import dataclass

from .position_v384 import PositionSlot384, Trade384
from .commission import CommissionModel
from .avwap import AVWAPTracker


@dataclass
class Trade390(Trade384):
    """Extends Trade384 with BBW context at entry."""
    bbwp_state:   str   = ""
    bbwp_value:   float = float("nan")
    bbwp_spectrum: str  = ""


class Backtester390:
    """
    v3.9.0 multi-slot backtester.

    Grade C = continuation/pyramid into existing same-direction position.
    Grade A/B = fresh entries OR first pyramid into position.
    """

    def __init__(self, params: dict = None):
        p = params or {}

        self.sigma_floor_atr   = p.get("sigma_floor_atr",   0.5)
        self.sl_mult           = p.get("sl_mult",            2.0)
        self.tp_mult           = p.get("tp_mult",            None)
        self.be_trigger_atr    = p.get("be_trigger_atr",     1.0)   # default ON per v3.8 changelog
        self.be_lock_atr       = p.get("be_lock_atr",        0.0)

        self.checkpoint_interval = p.get("checkpoint_interval", 5)
        self.max_scaleouts       = p.get("max_scaleouts",       2)

        self.max_positions  = p.get("max_positions",  4)
        self.cooldown       = p.get("cooldown",       3)
        self.b_open_fresh   = p.get("b_open_fresh",   True)
        self.allow_c_trades = p.get("allow_c_trades", True)   # continuations
        self.notional       = p.get("notional",       5000.0)

        self.enable_adds      = p.get("enable_adds",      True)
        self.enable_reentry   = p.get("enable_reentry",   True)
        self.cancel_bars      = p.get("cancel_bars",      3)
        self.reentry_window   = p.get("reentry_window",   5)
        self.max_avwap_age    = p.get("max_avwap_age",    50)

        self.comm = CommissionModel(
            commission_rate    = p.get("commission_rate",    0.0008),
            maker_rate         = p.get("maker_rate",         0.0002),
            notional           = self.notional,
            rebate_pct         = p.get("rebate_pct",         0.70),
            settlement_hour_utc= p.get("settlement_hour_utc", 17),
        )

        self.initial_equity = p.get("initial_equity", 10000.0)

    # ─────────────────────────────────────────────────────────────────────────
    def run(self, df: pd.DataFrame) -> dict:
        n     = len(df)
        close = df["close"].values
        high  = df["high"].values
        low   = df["low"].values
        atr   = df["atr"].values
        hlc3  = (high + low + close) / 3.0
        vol   = df["base_vol"].values if "base_vol" in df.columns else np.ones(n)

        cloud3_ok_long  = df["cloud3_allows_long"].values
        cloud3_ok_short = df["cloud3_allows_short"].values

        long_a       = df["long_a"].values
        long_b       = df["long_b"].values
        short_a      = df["short_a"].values
        short_b      = df["short_b"].values
        reentry_long  = df["reentry_long"].values
        reentry_short = df["reentry_short"].values

        # BBW columns — optional, graceful fallback
        bbwp_state_arr    = df["bbwp_state"].values    if "bbwp_state"    in df.columns else np.full(n, "")
        bbwp_value_arr    = df["bbwp_value"].values    if "bbwp_value"    in df.columns else np.full(n, float("nan"))
        bbwp_spectrum_arr = df["bbwp_spectrum"].values if "bbwp_spectrum" in df.columns else np.full(n, "")

        # Datetime for commission settlement
        if "datetime" in df.columns:
            datetimes = df["datetime"].values
            has_dt = True
        elif isinstance(df.index, pd.DatetimeIndex):
            datetimes = df.index.values
            has_dt = True
        else:
            datetimes = None
            has_dt = False

        slots: list[Optional[PositionSlot384]] = [None] * 4
        last_entry_bar: Optional[int] = None
        trades: list[Trade390] = []
        equity = self.initial_equity
        equity_curve     = np.full(n, equity)
        position_counts  = np.zeros(n, dtype=int)

        pend_bar:   Optional[int]          = None
        pend_dir:   int                    = 0
        pend_limit: Optional[float]        = None
        pend_grade: str                    = ""
        pend_avwap: Optional[AVWAPTracker] = None

        re_bar:     Optional[int]          = None
        re_dir:     int                    = 0
        re_tracker: Optional[AVWAPTracker] = None

        for i in range(n):
            if np.isnan(atr[i]):
                equity_curve[i] = equity
                continue

            # Commission settlement
            if has_dt and datetimes is not None:
                bar_dt = pd.Timestamp(datetimes[i]).to_pydatetime()
                if bar_dt.tzinfo is None:
                    bar_dt = bar_dt.replace(tzinfo=timezone.utc)
                equity += self.comm.check_settlement(bar_dt)

            # ── Step 1: Check exits ───────────────────────────────────────────
            for s in range(4):
                if slots[s] is None:
                    continue
                reason = slots[s].check_exit(high[i], low[i])
                if reason:
                    exit_price = slots[s].tp if reason == "TP" else slots[s].sl
                    comm_exit  = self.comm.charge_custom(slots[s].notional, maker=True)
                    trade = self._make_trade390(
                        slots[s].close_at(exit_price, i, reason,
                                          comm_exit + slots[s].entry_commission),
                        bbwp_state_arr[slots[s].entry_bar],
                        bbwp_value_arr[slots[s].entry_bar],
                        bbwp_spectrum_arr[slots[s].entry_bar],
                    )
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    if self.enable_reentry and reason == "SL":
                        re_bar     = i
                        re_dir     = 1 if slots[s].direction == "LONG" else -1
                        re_tracker = slots[s].avwap.clone()
                    slots[s] = None

            # ── Step 2: Update AVWAP + SL ─────────────────────────────────────
            for s in range(4):
                if slots[s] is not None:
                    slots[s].update_bar(i, high[i], low[i], close[i], atr[i], hlc3[i], vol[i])

            # ── Step 3: Scale-outs ────────────────────────────────────────────
            for s in range(4):
                if slots[s] is None:
                    continue
                if slots[s].check_scale_out(i, close[i]):
                    is_final_check   = (slots[s].scale_count + 1 >= slots[s].max_scaleouts)
                    scale_notional   = slots[s].notional if is_final_check else slots[s].notional / 2
                    comm_exit        = self.comm.charge_custom(scale_notional, maker=True)
                    entry_comm_share = slots[s].entry_commission * scale_notional / slots[s].original_notional
                    t384, is_final   = slots[s].do_scale_out(i, close[i], comm_exit + entry_comm_share)
                    trade = self._make_trade390(
                        t384,
                        bbwp_state_arr[slots[s].entry_bar],
                        bbwp_value_arr[slots[s].entry_bar],
                        bbwp_spectrum_arr[slots[s].entry_bar],
                    )
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    if is_final:
                        slots[s] = None

            # ── Step 4: Pending limits ────────────────────────────────────────
            if pend_dir != 0 and pend_bar is not None:
                if i - pend_bar >= self.cancel_bars:
                    pend_bar = pend_dir = 0
                    pend_limit = pend_grade = pend_avwap = None
                else:
                    filled = (pend_dir == 1 and low[i] <= pend_limit) or \
                             (pend_dir == -1 and high[i] >= pend_limit)
                    if filled:
                        empty = self._find_empty(slots)
                        if empty >= 0:
                            comm_entry = self.comm.charge(maker=True)
                            equity    -= comm_entry
                            direction  = "LONG" if pend_dir == 1 else "SHORT"
                            slots[empty] = PositionSlot384(
                                direction        = direction,
                                grade            = pend_grade,
                                entry_bar        = i,
                                entry_price      = pend_limit,
                                atr              = atr[i],
                                hlc3             = hlc3[i],
                                volume           = vol[i],
                                sigma_floor_atr  = self.sigma_floor_atr,
                                sl_mult          = self.sl_mult,
                                tp_mult          = self.tp_mult,
                                be_trigger_atr   = self.be_trigger_atr,
                                be_lock_atr      = self.be_lock_atr,
                                notional         = self.notional,
                                checkpoint_interval = self.checkpoint_interval,
                                max_scaleouts    = self.max_scaleouts,
                                avwap_state      = pend_avwap,
                            )
                            slots[empty].entry_commission = comm_entry
                            last_entry_bar = i
                        pend_bar = pend_dir = 0
                        pend_limit = pend_grade = pend_avwap = None

            # ── Step 5: Stochastic entries ────────────────────────────────────
            active_count = sum(1 for s in slots if s is not None)
            cooldown_ok  = last_entry_bar is None or (i - last_entry_bar >= self.cooldown)
            can_enter    = active_count < self.max_positions and cooldown_ok

            has_longs  = any(s is not None and s.direction == "LONG"  for s in slots)
            has_shorts = any(s is not None and s.direction == "SHORT" for s in slots)

            # Grade A: no Cloud 3 gate (Pine: bypasses Cloud 3 filter)
            can_long_a  = not has_shorts and can_enter
            can_short_a = not has_longs  and can_enter
            # Grade B: Cloud 3 gated
            can_long_b  = not has_shorts and can_enter and bool(cloud3_ok_long[i])
            can_short_b = not has_longs  and can_enter and bool(cloud3_ok_short[i])

            did_enter = False

            # ── Grade A long ──────────────────────────────────────────────────
            if long_a[i] and can_long_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    # Determine actual grade: A if fresh, C if already in LONG
                    grade = "C" if has_longs and self.allow_c_trades else "A"
                    if grade == "C" and not self.allow_c_trades:
                        pass  # Skip continuation if disabled
                    else:
                        self._open_slot(slots, empty, "LONG", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # ── Grade A short ─────────────────────────────────────────────────
            if short_a[i] and can_short_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    grade = "C" if has_shorts and self.allow_c_trades else "A"
                    if grade == "C" and not self.allow_c_trades:
                        pass
                    else:
                        self._open_slot(slots, empty, "SHORT", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # ── Grade B long ──────────────────────────────────────────────────
            if long_b[i] and can_long_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    fresh_ok = not has_longs or self.b_open_fresh
                    grade    = "C" if has_longs else "B"
                    if grade == "C" and not self.allow_c_trades:
                        pass
                    elif grade == "B" and not fresh_ok:
                        pass
                    else:
                        self._open_slot(slots, empty, "LONG", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # ── Grade B short ─────────────────────────────────────────────────
            if short_b[i] and can_short_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    fresh_ok = not has_shorts or self.b_open_fresh
                    grade    = "C" if has_shorts else "B"
                    if grade == "C" and not self.allow_c_trades:
                        pass
                    elif grade == "B" and not fresh_ok:
                        pass
                    else:
                        self._open_slot(slots, empty, "SHORT", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # ── Re-entry long ─────────────────────────────────────────────────
            if reentry_long[i] and can_long_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    self._open_slot(slots, empty, "LONG", "R", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    equity -= slots[empty].entry_commission
                    last_entry_bar = i
                    did_enter = True

            # ── Re-entry short ────────────────────────────────────────────────
            if reentry_short[i] and can_short_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    self._open_slot(slots, empty, "SHORT", "R", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    equity -= slots[empty].entry_commission
                    last_entry_bar = i
                    did_enter = True

            # ── Step 6: AVWAP adds ────────────────────────────────────────────
            if self.enable_adds and pend_dir == 0 and not did_enter and \
               active_count < self.max_positions and cooldown_ok:
                for s in range(4):
                    if slots[s] is None or pend_dir != 0:
                        continue
                    sv = slots[s].avwap.center
                    ss = slots[s].avwap.sigma
                    if sv is None or ss is None:
                        continue
                    age = i - slots[s].entry_bar
                    if age > self.max_avwap_age:
                        continue
                    m2 = sv - 2.0 * ss
                    p2 = sv + 2.0 * ss
                    m1 = sv - ss
                    p1 = sv + ss
                    if slots[s].direction == "LONG" and low[i] <= m2 and bool(cloud3_ok_long[i]):
                        pend_bar   = i
                        pend_dir   = 1
                        pend_limit = m1
                        pend_grade = "ADD"
                        pend_avwap = slots[s].avwap.clone()
                        break
                    if slots[s].direction == "SHORT" and high[i] >= p2 and bool(cloud3_ok_short[i]):
                        pend_bar   = i
                        pend_dir   = -1
                        pend_limit = p1
                        pend_grade = "ADD"
                        pend_avwap = slots[s].avwap.clone()
                        break

            # ── Step 7: AVWAP re-entry ────────────────────────────────────────
            re_dir_ok = (re_dir == 1 and not has_shorts) or \
                        (re_dir == -1 and not has_longs) or re_dir == 0

            if self.enable_reentry and re_dir != 0 and re_dir_ok and \
               pend_dir == 0 and not did_enter:
                if re_bar is not None and i - re_bar > self.reentry_window:
                    re_bar = re_dir = 0
                    re_tracker = None
                elif re_tracker is not None and active_count < self.max_positions and cooldown_ok:
                    c_re = re_tracker.center
                    s_re = re_tracker.sigma
                    re_m2 = c_re - 2.0 * s_re
                    re_p2 = c_re + 2.0 * s_re
                    re_m1 = c_re - s_re
                    re_p1 = c_re + s_re
                    if re_dir == 1 and low[i] <= re_m2 and bool(cloud3_ok_long[i]):
                        pend_bar   = i
                        pend_dir   = 1
                        pend_limit = re_m1
                        pend_grade = "RE"
                        pend_avwap = re_tracker.clone()
                        re_dir     = 0
                    elif re_dir == -1 and high[i] >= re_p2 and bool(cloud3_ok_short[i]):
                        pend_bar   = i
                        pend_dir   = -1
                        pend_limit = re_p1
                        pend_grade = "RE"
                        pend_avwap = re_tracker.clone()
                        re_dir     = 0

            # ── Equity curve ──────────────────────────────────────────────────
            position_counts[i] = sum(1 for s in slots if s is not None)
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
                t384 = slots[s].close_at(
                    close[-1], n - 1, "END",
                    comm_exit + slots[s].entry_commission
                )
                trade = self._make_trade390(t384, "", float("nan"), "")
                trades.append(trade)
                equity += trade.pnl - comm_exit
        equity_curve[-1] = equity

        metrics = self._compute_metrics(trades, equity_curve)
        metrics["final_equity"]          = equity
        metrics["equity_curve"]          = equity_curve
        metrics["total_rebate"]          = self.comm.total_rebate
        metrics["net_pnl_after_rebate"]  = metrics["net_pnl"] + self.comm.total_rebate
        metrics["total_volume"]          = self.comm.total_volume
        metrics["total_sides"]           = self.comm.total_sides

        margin_per_pos = self.notional / 20.0
        valid_counts   = position_counts[~np.isnan(atr)]
        if len(valid_counts) > 0:
            metrics["avg_positions"]      = float(np.mean(valid_counts))
            metrics["max_positions_used"] = int(np.max(valid_counts))
            metrics["pct_time_flat"]      = float(np.sum(valid_counts == 0) / len(valid_counts))
            metrics["avg_margin_used"]    = float(np.mean(valid_counts) * margin_per_pos)
            metrics["peak_margin_used"]   = float(np.max(valid_counts) * margin_per_pos)
        else:
            metrics.update({
                "avg_positions": 0, "max_positions_used": 0,
                "pct_time_flat": 1.0, "avg_margin_used": 0, "peak_margin_used": 0
            })

        return {
            "trades":          trades,
            "trades_df":       self._trades_to_df(trades),
            "metrics":         metrics,
            "equity_curve":    equity_curve,
            "position_counts": position_counts,
        }

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _find_empty(self, slots) -> int:
        for i in range(4):
            if slots[i] is None:
                return i
        return -1

    def _open_slot(self, slots, idx, direction, grade, bar_idx,
                   entry_price, atr_val, hlc3_val, volume_val):
        comm = self.comm.charge()
        slots[idx] = PositionSlot384(
            direction           = direction,
            grade               = grade,
            entry_bar           = bar_idx,
            entry_price         = entry_price,
            atr                 = atr_val,
            hlc3                = hlc3_val,
            volume              = volume_val,
            sigma_floor_atr     = self.sigma_floor_atr,
            sl_mult             = self.sl_mult,
            tp_mult             = self.tp_mult,
            be_trigger_atr      = self.be_trigger_atr,
            be_lock_atr         = self.be_lock_atr,
            notional            = self.notional,
            checkpoint_interval = self.checkpoint_interval,
            max_scaleouts       = self.max_scaleouts,
            avwap_state         = None,
        )
        slots[idx].entry_commission = comm

    @staticmethod
    def _make_trade390(t384: Trade384, bbwp_state, bbwp_value, bbwp_spectrum) -> "Trade390":
        t = Trade390(
            direction   = t384.direction,
            grade       = t384.grade,
            entry_bar   = t384.entry_bar,
            exit_bar    = t384.exit_bar,
            entry_price = t384.entry_price,
            exit_price  = t384.exit_price,
            sl_price    = t384.sl_price,
            tp_price    = t384.tp_price,
            pnl         = t384.pnl,
            commission  = t384.commission,
            mfe         = t384.mfe,
            mae         = t384.mae,
            exit_reason = t384.exit_reason,
            saw_green   = t384.saw_green,
            be_raised   = t384.be_raised,
            exit_stage  = t384.exit_stage,
            entry_atr   = t384.entry_atr,
            scale_idx   = t384.scale_idx,
            bbwp_state  = str(bbwp_state) if bbwp_state else "",
            bbwp_value  = float(bbwp_value) if not (bbwp_value != bbwp_value) else float("nan"),
            bbwp_spectrum = str(bbwp_spectrum) if bbwp_spectrum else "",
        )
        return t

    def _compute_metrics(self, trades, equity_curve):
        if not trades:
            return {"total_trades": 0}

        pnls     = np.array([t.pnl for t in trades])
        net_pnls = np.array([t.pnl - t.commission for t in trades])
        comms    = np.array([t.commission for t in trades])
        winners  = net_pnls[net_pnls > 0]
        losers   = net_pnls[net_pnls <= 0]

        total    = len(trades)
        win_rate = len(winners) / total if total > 0 else 0
        gp       = float(np.sum(winners)) if len(winners) > 0 else 0.0
        gl       = float(np.abs(np.sum(losers))) if len(losers) > 0 else 0.0
        pf       = gp / gl if gl > 0 else float("inf")

        saw_green_losers = sum(1 for t in trades if t.saw_green and t.pnl - t.commission <= 0)
        total_losers     = sum(1 for t in trades if t.pnl - t.commission <= 0)

        grades = {}
        for grade in ["A", "B", "C", "R", "ADD", "RE"]:
            gt = [t for t in trades if t.grade == grade]
            if gt:
                gp2 = [t.pnl - t.commission for t in gt]
                grades[grade] = {
                    "count":    len(gt),
                    "win_rate": sum(1 for p in gp2 if p > 0) / len(gt),
                    "avg_pnl":  float(np.mean(gp2)),
                    "total_pnl":float(np.sum(gp2)),
                }

        # BBW breakdown
        bbwp_groups = {}
        for state in ["BLUE_DOUBLE", "BLUE", "NORMAL", "RED", "RED_DOUBLE", "MA_CROSS_UP", "MA_CROSS_DOWN"]:
            st = [t for t in trades if t.bbwp_state == state]
            if st:
                sp = [t.pnl - t.commission for t in st]
                bbwp_groups[state] = {
                    "count":    len(st),
                    "win_rate": sum(1 for p in sp if p > 0) / len(st),
                    "avg_pnl":  float(np.mean(sp)),
                }

        sharpe = 0.0
        if len(net_pnls) > 1 and np.std(net_pnls) > 0:
            sharpe = float(np.mean(net_pnls) / np.std(net_pnls))

        max_dd = max_dd_pct = 0.0
        if equity_curve is not None and len(equity_curve) > 0:
            peak     = np.maximum.accumulate(equity_curve)
            drawdown = peak - equity_curve
            max_dd   = float(np.max(drawdown))
            max_dd_pct = float(np.max(drawdown / peak) * 100) if np.max(peak) > 0 else 0

        return {
            "total_trades":         total,
            "win_count":            len(winners),
            "loss_count":           len(losers),
            "win_rate":             win_rate,
            "avg_win":              float(np.mean(winners)) if len(winners) > 0 else 0,
            "avg_loss":             float(np.mean(losers))  if len(losers)  > 0 else 0,
            "expectancy":           float(np.mean(net_pnls)),
            "gross_profit":         gp,
            "gross_loss":           gl,
            "profit_factor":        pf,
            "net_pnl":              float(np.sum(net_pnls)),
            "total_commission":     float(np.sum(comms)),
            "sharpe":               sharpe,
            "max_drawdown":         max_dd,
            "max_drawdown_pct":     max_dd_pct,
            "pct_losers_saw_green": saw_green_losers / total_losers if total_losers > 0 else 0,
            "saw_green_losers":     saw_green_losers,
            "total_losers":         total_losers,
            "be_raised_count":      sum(1 for t in trades if t.be_raised),
            "tp_exits":             sum(1 for t in trades if t.exit_reason == "TP"),
            "sl_exits":             sum(1 for t in trades if t.exit_reason == "SL"),
            "grades":               grades,
            "bbwp_groups":          bbwp_groups,
        }

    def _trades_to_df(self, trades):
        if not trades:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "direction":    t.direction,
                "grade":        t.grade,
                "entry_bar":    t.entry_bar,
                "exit_bar":     t.exit_bar,
                "entry_price":  t.entry_price,
                "exit_price":   t.exit_price,
                "sl_price":     t.sl_price,
                "tp_price":     t.tp_price,
                "pnl":          t.pnl,
                "commission":   t.commission,
                "net_pnl":      t.pnl - t.commission,
                "mfe":          t.mfe,
                "mae":          t.mae,
                "exit_reason":  t.exit_reason,
                "saw_green":    t.saw_green,
                "be_raised":    t.be_raised,
                "scale_idx":    t.scale_idx,
                "bbwp_state":   t.bbwp_state,
                "bbwp_value":   t.bbwp_value,
                "bbwp_spectrum":t.bbwp_spectrum,
            }
            for t in trades
        ])

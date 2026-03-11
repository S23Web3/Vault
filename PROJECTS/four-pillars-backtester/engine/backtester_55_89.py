"""
Backtester5589: 4-phase AVWAP position manager for the 55/89 EMA cross scalp.

Phases:
  1 - ATR initial stop (bars 0 to avwap_warmup-1)
  2 - AVWAP freeze (bar avwap_warmup): SL moves to frozen AVWAP -/+ sigma band
  3 - Overzone ratchet: each stoch-9-D overzone exit tightens the SL
  4 - TP activation: after ratchet_threshold exits, TP = Cloud4 edge +/- ATR offset

Interface: Backtester5589(params).run(df_sig) -> results dict
Results dict is structurally identical to Backtester384 for dashboard compatibility.

Source of truth: research/55-89-scalp-methodology.md
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))

from engine.avwap import AVWAPTracker
from engine.commission import CommissionModel
from signals.clouds_v2 import ema

log = logging.getLogger(__name__)


class Backtester5589:
    """55/89 scalp backtester with 4-phase AVWAP SL/TP lifecycle."""

    def __init__(self, params: dict = None):
        """Initialise engine from params dict; all keys optional with defaults."""
        p = params or {}
        self.sl_mult = float(p.get("sl_mult", 2.5))
        self.avwap_sigma = float(p.get("avwap_sigma", 2.0))
        self.avwap_warmup = int(p.get("avwap_warmup", 5))
        self.tp_atr_offset = float(p.get("tp_atr_offset", 0.5))
        self.ratchet_threshold = int(p.get("ratchet_threshold", 2))
        self.notional = float(p.get("notional", 5000.0))
        self.initial_equity = float(p.get("initial_equity", 10000.0))
        self.sigma_floor_atr = float(p.get("sigma_floor_atr", 0.5))
        self.enable_ema_be = bool(p.get("enable_ema_be", True))
        self.overzone_long_threshold = float(p.get("overzone_long_threshold", 20.0))
        self.overzone_short_threshold = float(p.get("overzone_short_threshold", 80.0))
        self.leverage = float(p.get("leverage", 20))
        self.comm = CommissionModel(
            commission_rate=float(p.get("commission_rate", 0.0008)),
            maker_rate=float(p.get("maker_rate", 0.0002)),
            notional=self.notional,
            rebate_pct=float(p.get("rebate_pct", 0.70)),
            settlement_hour_utc=int(p.get("settlement_hour_utc", 17)),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, df_sig: pd.DataFrame) -> dict:
        """Run the 4-phase backtest on a signal DataFrame; return results dict."""
        df = df_sig.reset_index(drop=False)

        # Resolve datetime index or column
        if "datetime" in df.columns:
            datetimes = pd.to_datetime(df["datetime"])
        elif df_sig.index.name == "datetime":
            datetimes = pd.to_datetime(df_sig.index)
        else:
            datetimes = pd.to_datetime(df["index"]) if "index" in df.columns else pd.Series([pd.NaT] * len(df))

        n = len(df)

        # Required arrays
        close = df["close"].values.astype(float)
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        volume = df["volume"].values.astype(float) if "volume" in df.columns else np.ones(n)
        atr = df["atr"].values.astype(float)
        long_a = df["long_a"].values.astype(bool)
        short_a = df["short_a"].values.astype(bool)
        stoch_9_d = df["stoch_9_d"].values.astype(float) if "stoch_9_d" in df.columns else np.full(n, 50.0)
        ema_89_arr = df["ema_89"].values.astype(float) if "ema_89" in df.columns else np.full(n, np.nan)

        # EMA 72 computed here (Cloud 4 = 72/89; signal module only has 55/89)
        ema_72_arr = ema(close, 72)

        # EMA 55 for BE trigger (v2: EMA cross sets BE)
        ema_55_arr = df["ema_55"].values.astype(float) if "ema_55" in df.columns else ema(close, 55)

        # Trade grade from signal pipeline (v2)
        trade_grade_arr = df["trade_grade"].values if "trade_grade" in df.columns else np.full(n, "")

        # Equity / position tracking
        equity = self.initial_equity
        equity_curve = np.full(n, equity, dtype=float)
        position_counts = np.zeros(n, dtype=int)

        trades = []

        # Open position state (None = flat)
        pos = None  # dict when in trade

        for i in range(n):
            bar_dt = datetimes.iloc[i] if hasattr(datetimes, "iloc") else datetimes[i]

            # Settlement rebate
            if bar_dt is not pd.NaT and not pd.isna(bar_dt):
                rebate = self.comm.check_settlement(bar_dt)
                equity += rebate

            if np.isnan(atr[i]) or atr[i] <= 0:
                equity_curve[i] = equity
                position_counts[i] = 1 if pos is not None else 0
                continue

            hlc3 = (high[i] + low[i] + close[i]) / 3.0

            # ---- Manage open position ----
            if pos is not None:
                pos = self._update_position(pos, i, high, low, close, hlc3, volume, atr,
                                            stoch_9_d, ema_72_arr, ema_89_arr, ema_55_arr)

                if pos["closed"]:
                    exit_price = pos["exit_price"]
                    gross = self._gross_pnl(pos["direction"], pos["entry_price"], exit_price)
                    comm_exit = self.comm.charge(maker=False)
                    net = gross - comm_exit - pos["entry_commission"]
                    equity += gross - comm_exit

                    trade = {
                        "entry_bar": pos["entry_bar"],
                        "exit_bar": i,
                        "direction": pos["direction"],
                        "entry_price": pos["entry_price"],
                        "exit_price": exit_price,
                        "pnl": net,
                        "commission": pos["entry_commission"] + comm_exit,
                        "exit_reason": pos["exit_reason"],
                        "bars_held": i - pos["entry_bar"],
                        "ratchet_count": pos["ratchet_count"],
                        "phase_at_exit": pos["phase"],
                        "saw_green": pos["saw_green"],
                        "ema_be_triggered": pos.get("ema_be_triggered", False),
                        "trade_grade": pos.get("trade_grade", ""),
                    }
                    trades.append(trade)
                    pos = None
                else:
                    # Mark-to-market
                    unrealized = self._gross_pnl(pos["direction"], pos["entry_price"], close[i])
                    if unrealized > 0:
                        pos["saw_green"] = True

            # ---- Entry (only when flat) ----
            if pos is None:
                direction = None
                if long_a[i]:
                    direction = "LONG"
                elif short_a[i]:
                    direction = "SHORT"

                if direction is not None:
                    comm_entry = self.comm.charge(maker=False)
                    equity -= comm_entry

                    if direction == "LONG":
                        sl = close[i] - self.sl_mult * atr[i]
                    else:
                        sl = close[i] + self.sl_mult * atr[i]

                    tracker = AVWAPTracker(sigma_floor_atr=self.sigma_floor_atr)
                    tracker.update(hlc3, volume[i], atr[i])

                    pos = {
                        "direction": direction,
                        "entry_price": close[i],
                        "entry_bar": i,
                        "sl": sl,
                        "tp": None,
                        "phase": 1,
                        "bars_in_trade": 1,
                        "tracker": tracker,
                        "ratchet_count": 0,
                        "in_overzone": False,
                        "entry_commission": comm_entry,
                        "closed": False,
                        "exit_price": None,
                        "exit_reason": None,
                        "saw_green": False,
                        "ema_be_triggered": False,
                        "trade_grade": trade_grade_arr[i] if i < len(trade_grade_arr) else "",
                    }

            # Equity snapshot
            if pos is not None:
                unrealized = self._gross_pnl(pos["direction"], pos["entry_price"], close[i])
                equity_curve[i] = equity + unrealized
                position_counts[i] = 1
            else:
                equity_curve[i] = equity
                position_counts[i] = 0

        # Close any open position at end of data
        if pos is not None:
            exit_price = close[-1]
            gross = self._gross_pnl(pos["direction"], pos["entry_price"], exit_price)
            comm_exit = self.comm.charge(maker=False)
            net = gross - comm_exit - pos["entry_commission"]
            equity += gross - comm_exit
            equity_curve[-1] = equity
            trades.append({
                "entry_bar": pos["entry_bar"],
                "exit_bar": n - 1,
                "direction": pos["direction"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_price,
                "pnl": net,
                "commission": pos["entry_commission"] + comm_exit,
                "exit_reason": "eod",
                "bars_held": (n - 1) - pos["entry_bar"],
                "ratchet_count": pos["ratchet_count"],
                "phase_at_exit": pos["phase"],
                "saw_green": pos["saw_green"],
                "ema_be_triggered": pos.get("ema_be_triggered", False),
                "trade_grade": pos.get("trade_grade", ""),
            })

        metrics = self._compute_metrics(trades, equity_curve, equity, position_counts)
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()

        return {
            "trades": trades,
            "trades_df": trades_df,
            "metrics": metrics,
            "equity_curve": equity_curve,
            "position_counts": position_counts,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _gross_pnl(self, direction: str, entry: float, exit_p: float) -> float:
        """Compute gross PnL in notional dollars for a given direction."""
        if direction == "LONG":
            return (exit_p - entry) / entry * self.notional
        return (entry - exit_p) / entry * self.notional

    def _update_position(self, pos: dict, i: int,
                         high: np.ndarray, low: np.ndarray, close: np.ndarray,
                         hlc3: float, volume: np.ndarray, atr: np.ndarray,
                         stoch_9_d: np.ndarray, ema_72_arr: np.ndarray,
                         ema_89_arr: np.ndarray, ema_55_arr: np.ndarray = None) -> dict:
        """Advance position state by one bar; sets pos[closed] if exiting."""
        direction = pos["direction"]
        sl = pos["sl"]
        pos["bars_in_trade"] += 1
        bars = pos["bars_in_trade"]

        # Update AVWAP every bar
        pos["tracker"].update(hlc3, volume[i], atr[i])

        # BE trigger: EMA 55 crosses EMA 89 in trade direction
        if (self.enable_ema_be and not pos.get("ema_be_triggered", False)
                and ema_55_arr is not None and i > 0):
            e55 = ema_55_arr[i]
            e55_prev = ema_55_arr[i - 1]
            e89 = ema_89_arr[i]
            e89_prev = ema_89_arr[i - 1]
            if not (np.isnan(e55) or np.isnan(e55_prev) or np.isnan(e89) or np.isnan(e89_prev)):
                cross_bull = (e55_prev < e89_prev) and (e55 >= e89)
                cross_bear = (e55_prev > e89_prev) and (e55 <= e89)
                if (direction == "LONG" and cross_bull) or (direction == "SHORT" and cross_bear):
                    be_level = pos["entry_price"]
                    if direction == "LONG":
                        sl = max(sl, be_level)
                    else:
                        sl = min(sl, be_level)
                    pos["sl"] = sl
                    pos["ema_be_triggered"] = True

        # Phase 2 transition: freeze AVWAP at warmup bar
        if pos["phase"] == 1 and bars >= self.avwap_warmup:
            frozen_center, frozen_sigma = pos["tracker"].freeze()
            if direction == "LONG":
                new_sl = frozen_center - self.avwap_sigma * frozen_sigma
                sl = max(sl, new_sl)
            else:
                new_sl = frozen_center + self.avwap_sigma * frozen_sigma
                sl = min(sl, new_sl)
            pos["sl"] = sl
            pos["phase"] = 2

        # Overzone ratchet detection (phases 2+)
        d = stoch_9_d[i]
        if pos["phase"] >= 2:
            if direction == "LONG":
                currently_in_overzone = d < 20.0
            else:
                currently_in_overzone = d > 80.0

            if pos["in_overzone"] and not currently_in_overzone:
                # Overzone exit: ratchet SL with live AVWAP
                center = pos["tracker"].center
                sigma = pos["tracker"].sigma
                if direction == "LONG":
                    sl_candidate = center - self.avwap_sigma * sigma
                    sl = max(sl, sl_candidate)
                else:
                    sl_candidate = center + self.avwap_sigma * sigma
                    sl = min(sl, sl_candidate)
                pos["sl"] = sl
                pos["ratchet_count"] += 1
                pos["phase"] = 3

            pos["in_overzone"] = currently_in_overzone

        # Phase 4 TP activation
        if pos["ratchet_count"] >= self.ratchet_threshold:
            pos["phase"] = 4
            e72 = ema_72_arr[i]
            e89 = ema_89_arr[i]
            if not np.isnan(e72) and not np.isnan(e89):
                if direction == "LONG":
                    pos["tp"] = max(e72, e89) + self.tp_atr_offset * atr[i]
                else:
                    pos["tp"] = min(e72, e89) - self.tp_atr_offset * atr[i]

        # Exit checks
        if direction == "LONG":
            if low[i] <= sl:
                pos["exit_price"] = sl
                pos["exit_reason"] = "sl_phase" + str(pos["phase"])
                pos["closed"] = True
                return pos
            if pos["tp"] is not None and high[i] >= pos["tp"]:
                pos["exit_price"] = pos["tp"]
                pos["exit_reason"] = "tp_phase4"
                pos["closed"] = True
                return pos
        else:
            if high[i] >= sl:
                pos["exit_price"] = sl
                pos["exit_reason"] = "sl_phase" + str(pos["phase"])
                pos["closed"] = True
                return pos
            if pos["tp"] is not None and low[i] <= pos["tp"]:
                pos["exit_price"] = pos["tp"]
                pos["exit_reason"] = "tp_phase4"
                pos["closed"] = True
                return pos

        return pos

    def _compute_metrics(self, trades: list, equity_curve: np.ndarray,
                         final_equity: float, position_counts: np.ndarray) -> dict:
        """Assemble metrics dict from completed trades list; mirrors Backtester384 format."""
        if not trades:
            return {
                "total_trades": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "expectancy": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "profit_factor": 0.0,
                "net_pnl": 0.0,
                "total_commission": 0.0,
                "total_rebate": self.comm.total_rebate,
                "net_pnl_after_rebate": 0.0,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "max_drawdown_pct": 0.0,
                "pct_losers_saw_green": 0.0,
                "saw_green_losers": 0,
                "total_losers": 0,
                "final_equity": final_equity,
                "equity_curve": equity_curve,
                "total_volume": self.comm.total_volume,
                "total_sides": self.comm.total_sides,
                "avg_positions": 0.0,
                "max_positions_used": 0,
                "pct_time_flat": 1.0,
                "avg_margin_used": 0.0,
                "peak_margin_used": 0.0,
                "tp_exits": 0,
                "sl_exits": 0,
                "phase1_exits": 0,
                "phase2_exits": 0,
                "phase3_exits": 0,
                "phase4_exits": 0,
                "avg_ratchet_count": 0.0,
                "ratchet_threshold_hit_pct": 0.0,
                "be_raised_count": sum(1 for t in trades if t.get("ema_be_triggered", False)),
                "scale_out_count": 0,
            }

        pnls = np.array([t["pnl"] for t in trades])
        winners = pnls[pnls > 0]
        losers = pnls[pnls <= 0]
        total = len(trades)
        win_count = int(len(winners))
        loss_count = int(len(losers))
        win_rate = win_count / total if total > 0 else 0.0
        gross_profit = float(np.sum(winners)) if len(winners) > 0 else 0.0
        gross_loss = float(np.abs(np.sum(losers))) if len(losers) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        net_pnl = float(np.sum(pnls))
        total_comm = float(np.sum([t["commission"] for t in trades]))

        # Sharpe (annualised daily returns approximation)
        if len(pnls) > 1:
            ret_std = float(np.std(pnls))
            sharpe = (float(np.mean(pnls)) / ret_std * np.sqrt(252)) if ret_std > 0 else 0.0
        else:
            sharpe = 0.0

        # Drawdown
        peak = np.maximum.accumulate(equity_curve)
        dd = peak - equity_curve
        max_dd = float(np.max(dd))
        max_dd_pct = float(np.max(dd / np.where(peak > 0, peak, 1.0)) * 100.0)

        # LSG
        saw_green_losers = sum(1 for t in trades if t["saw_green"] and t["pnl"] <= 0)
        total_losers = loss_count
        pct_lsg = saw_green_losers / total_losers if total_losers > 0 else 0.0

        # Exit reason counts
        tp_exits = sum(1 for t in trades if t["exit_reason"] == "tp_phase4")
        sl_exits = total - tp_exits
        phase1_exits = sum(1 for t in trades if t["exit_reason"] == "sl_phase1")
        phase2_exits = sum(1 for t in trades if t["exit_reason"] == "sl_phase2")
        phase3_exits = sum(1 for t in trades if t["exit_reason"] == "sl_phase3")
        phase4_exits = tp_exits

        avg_ratchet = float(np.mean([t["ratchet_count"] for t in trades]))
        ratchet_hit = sum(1 for t in trades if t["ratchet_count"] >= self.ratchet_threshold)
        ratchet_hit_pct = ratchet_hit / total if total > 0 else 0.0

        # Capital utilisation (single-position model)
        valid_counts = position_counts.astype(float)
        n = len(valid_counts)
        margin_per_pos = self.notional / self.leverage if self.leverage > 0 else self.notional

        return {
            "total_trades": total,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "avg_win": float(np.mean(winners)) if len(winners) > 0 else 0.0,
            "avg_loss": float(np.mean(losers)) if len(losers) > 0 else 0.0,
            "expectancy": float(np.mean(pnls)),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "net_pnl": net_pnl,
            "total_commission": total_comm,
            "total_rebate": self.comm.total_rebate,
            "net_pnl_after_rebate": net_pnl + self.comm.total_rebate,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd_pct,
            "pct_losers_saw_green": pct_lsg,
            "saw_green_losers": saw_green_losers,
            "total_losers": total_losers,
            "final_equity": final_equity,
            "equity_curve": equity_curve,
            "total_volume": self.comm.total_volume,
            "total_sides": self.comm.total_sides,
            "avg_positions": float(np.mean(valid_counts)),
            "max_positions_used": int(np.max(valid_counts)),
            "pct_time_flat": float(np.sum(valid_counts == 0) / n),
            "avg_margin_used": float(np.mean(valid_counts) * margin_per_pos),
            "peak_margin_used": float(np.max(valid_counts) * margin_per_pos),
            "tp_exits": tp_exits,
            "sl_exits": sl_exits,
            "phase1_exits": phase1_exits,
            "phase2_exits": phase2_exits,
            "phase3_exits": phase3_exits,
            "phase4_exits": phase4_exits,
            "avg_ratchet_count": avg_ratchet,
            "ratchet_threshold_hit_pct": ratchet_hit_pct,
            "be_raised_count": 0,
            "scale_out_count": 0,
        }

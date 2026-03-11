"""
JIT-compiled 55/89 scalp backtester.

Drop-in replacement for Backtester5589. Requires numba (Python 3.12 .venv312).
First call triggers JIT compilation (~10s). Subsequent calls load cached binary.

Warmup once: python scripts/warmup_5589_jit.py
Run dashboard: streamlit run scripts/dashboard_55_89_v3.py
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))

from signals.clouds_v2 import ema

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JIT core loop
# ---------------------------------------------------------------------------

@njit(cache=True)
def _run_5589_core(
    close, high, low, volume, atr,
    long_a, short_a, stoch_9_d, ema_72, ema_89,
    sl_mult, avwap_sigma_band, avwap_warmup, tp_atr_offset, ratchet_threshold,
    notional, commission_per_side, sigma_floor_atr, initial_equity,
):
    """Inner bar loop: 4-phase lifecycle. Returns raw trade arrays and equity_curve."""
    n = len(close)

    # Trade output arrays (max n trades possible; sliced to n_trades on return)
    t_entry   = np.empty(n, dtype=np.int64)
    t_exit    = np.empty(n, dtype=np.int64)
    t_dir     = np.empty(n, dtype=np.int64)   # 1=LONG, -1=SHORT
    t_ep      = np.empty(n, dtype=np.float64)  # entry price
    t_xp      = np.empty(n, dtype=np.float64)  # exit price
    t_gross   = np.empty(n, dtype=np.float64)
    t_ecomm   = np.empty(n, dtype=np.float64)  # entry-side commission
    t_phase   = np.empty(n, dtype=np.int64)    # phase at exit 1..4
    t_ratchet = np.empty(n, dtype=np.int64)
    t_green   = np.empty(n, dtype=np.bool_)    # saw unrealised profit
    t_is_tp   = np.empty(n, dtype=np.bool_)    # True = TP hit; False = SL/eod
    t_is_eod  = np.empty(n, dtype=np.bool_)    # True = end-of-data forced close
    n_trades  = 0

    equity_curve    = np.empty(n, dtype=np.float64)
    position_counts = np.zeros(n, dtype=np.int32)

    equity = initial_equity

    # ---- Position state (flat by default) ----
    in_trade       = False
    p_dir          = 0
    p_entry_px     = 0.0
    p_entry_bar    = 0
    p_sl           = 0.0
    p_tp           = np.nan
    p_phase        = 1
    p_bars         = 0
    p_avwap_cum_pv  = 0.0
    p_avwap_cum_v   = 0.0
    p_avwap_cum_pv2 = 0.0
    p_avwap_center  = 0.0
    p_avwap_std     = 0.0
    p_ratchet      = 0
    p_in_overzone  = False
    p_entry_comm   = 0.0
    p_saw_green    = False

    for i in range(n):

        # Skip bars with invalid ATR
        if np.isnan(atr[i]) or atr[i] <= 0.0:
            equity_curve[i] = equity
            position_counts[i] = 1 if in_trade else 0
            continue

        hlc3 = (high[i] + low[i] + close[i]) / 3.0

        # ---- Manage open position ----
        if in_trade:
            p_bars += 1

            # AVWAP accumulate
            vol_i = volume[i] if volume[i] > 0.0 else 1e-10
            p_avwap_cum_pv  += hlc3 * vol_i
            p_avwap_cum_v   += vol_i
            p_avwap_cum_pv2 += hlc3 * hlc3 * vol_i
            p_avwap_center   = p_avwap_cum_pv / p_avwap_cum_v
            variance         = p_avwap_cum_pv2 / p_avwap_cum_v - p_avwap_center * p_avwap_center
            if variance < 0.0:
                variance = 0.0
            sigma_raw   = variance ** 0.5
            floor_sigma = sigma_floor_atr * atr[i]
            p_avwap_std = sigma_raw if sigma_raw > floor_sigma else floor_sigma

            # Phase 2: AVWAP freeze
            if p_phase == 1 and p_bars >= avwap_warmup:
                if p_dir == 1:
                    new_sl = p_avwap_center - avwap_sigma_band * p_avwap_std
                    if new_sl > p_sl:
                        p_sl = new_sl
                else:
                    new_sl = p_avwap_center + avwap_sigma_band * p_avwap_std
                    if new_sl < p_sl:
                        p_sl = new_sl
                p_phase = 2

            # Overzone ratchet (phases 2+)
            if p_phase >= 2:
                d = stoch_9_d[i]
                if p_dir == 1:
                    curr_oz = d < 20.0
                else:
                    curr_oz = d > 80.0

                if p_in_overzone and not curr_oz:
                    if p_dir == 1:
                        sl_cand = p_avwap_center - avwap_sigma_band * p_avwap_std
                        if sl_cand > p_sl:
                            p_sl = sl_cand
                    else:
                        sl_cand = p_avwap_center + avwap_sigma_band * p_avwap_std
                        if sl_cand < p_sl:
                            p_sl = sl_cand
                    p_ratchet += 1
                    p_phase = 3

                p_in_overzone = curr_oz

            # Phase 4: TP activation
            if p_ratchet >= ratchet_threshold:
                p_phase = 4
                e72 = ema_72[i]
                e89 = ema_89[i]
                if not np.isnan(e72) and not np.isnan(e89):
                    if p_dir == 1:
                        cloud4_edge = e72 if e72 > e89 else e89
                        p_tp = cloud4_edge + tp_atr_offset * atr[i]
                    else:
                        cloud4_edge = e72 if e72 < e89 else e89
                        p_tp = cloud4_edge - tp_atr_offset * atr[i]

            # Exit checks
            closed = False
            exit_px = 0.0
            is_tp   = False

            if p_dir == 1:
                if low[i] <= p_sl:
                    exit_px = p_sl
                    closed  = True
                elif not np.isnan(p_tp) and high[i] >= p_tp:
                    exit_px = p_tp
                    closed  = True
                    is_tp   = True
            else:
                if high[i] >= p_sl:
                    exit_px = p_sl
                    closed  = True
                elif not np.isnan(p_tp) and low[i] <= p_tp:
                    exit_px = p_tp
                    closed  = True
                    is_tp   = True

            if closed:
                if p_dir == 1:
                    gross = (exit_px - p_entry_px) / p_entry_px * notional
                else:
                    gross = (p_entry_px - exit_px) / p_entry_px * notional
                equity += gross - commission_per_side

                t_entry[n_trades]   = p_entry_bar
                t_exit[n_trades]    = i
                t_dir[n_trades]     = p_dir
                t_ep[n_trades]      = p_entry_px
                t_xp[n_trades]      = exit_px
                t_gross[n_trades]   = gross
                t_ecomm[n_trades]   = p_entry_comm
                t_phase[n_trades]   = p_phase
                t_ratchet[n_trades] = p_ratchet
                t_green[n_trades]   = p_saw_green
                t_is_tp[n_trades]   = is_tp
                t_is_eod[n_trades]  = False
                n_trades += 1
                in_trade = False
            else:
                # Mark-to-market: update saw_green
                if p_dir == 1:
                    unrealized = (close[i] - p_entry_px) / p_entry_px * notional
                else:
                    unrealized = (p_entry_px - close[i]) / p_entry_px * notional
                if unrealized > 0.0:
                    p_saw_green = True

        # ---- Entry when flat ----
        if not in_trade:
            entry_dir = 0
            if long_a[i]:
                entry_dir = 1
            elif short_a[i]:
                entry_dir = -1

            if entry_dir != 0:
                comm_entry = commission_per_side
                equity -= comm_entry

                if entry_dir == 1:
                    sl = close[i] - sl_mult * atr[i]
                else:
                    sl = close[i] + sl_mult * atr[i]

                vol_i = volume[i] if volume[i] > 0.0 else 1e-10
                p_avwap_cum_pv  = hlc3 * vol_i
                p_avwap_cum_v   = vol_i
                p_avwap_cum_pv2 = hlc3 * hlc3 * vol_i
                p_avwap_center  = hlc3
                p_avwap_std     = sigma_floor_atr * atr[i]

                in_trade      = True
                p_dir         = entry_dir
                p_entry_px    = close[i]
                p_entry_bar   = i
                p_sl          = sl
                p_tp          = np.nan
                p_phase       = 1
                p_bars        = 1
                p_ratchet     = 0
                p_in_overzone = False
                p_entry_comm  = comm_entry
                p_saw_green   = False

        # ---- Equity snapshot ----
        if in_trade:
            if p_dir == 1:
                unrealized = (close[i] - p_entry_px) / p_entry_px * notional
            else:
                unrealized = (p_entry_px - close[i]) / p_entry_px * notional
            equity_curve[i]    = equity + unrealized
            position_counts[i] = 1
        else:
            equity_curve[i]    = equity
            position_counts[i] = 0

    # ---- EOD: force-close open position ----
    if in_trade:
        exit_px = close[n - 1]
        if p_dir == 1:
            gross = (exit_px - p_entry_px) / p_entry_px * notional
        else:
            gross = (p_entry_px - exit_px) / p_entry_px * notional
        equity += gross - commission_per_side
        equity_curve[n - 1] = equity

        t_entry[n_trades]   = p_entry_bar
        t_exit[n_trades]    = n - 1
        t_dir[n_trades]     = p_dir
        t_ep[n_trades]      = p_entry_px
        t_xp[n_trades]      = exit_px
        t_gross[n_trades]   = gross
        t_ecomm[n_trades]   = p_entry_comm
        t_phase[n_trades]   = p_phase
        t_ratchet[n_trades] = p_ratchet
        t_green[n_trades]   = p_saw_green
        t_is_tp[n_trades]   = False
        t_is_eod[n_trades]  = True
        n_trades += 1

    return (
        t_entry, t_exit, t_dir, t_ep, t_xp,
        t_gross, t_ecomm, t_phase, t_ratchet, t_green, t_is_tp, t_is_eod,
        np.int64(n_trades),
        equity_curve, position_counts,
    )


# ---------------------------------------------------------------------------
# Python wrapper
# ---------------------------------------------------------------------------

class Backtester5589Fast:
    """JIT-compiled 55/89 scalp backtester; drop-in replacement for Backtester5589."""

    def __init__(self, params: dict = None):
        """Initialise from params dict; all keys optional with same defaults as Backtester5589."""
        p = params or {}
        self.sl_mult            = float(p.get("sl_mult", 2.5))
        self.avwap_sigma        = float(p.get("avwap_sigma", 2.0))
        self.avwap_warmup       = int(p.get("avwap_warmup", 5))
        self.tp_atr_offset      = float(p.get("tp_atr_offset", 0.5))
        self.ratchet_threshold  = int(p.get("ratchet_threshold", 2))
        self.notional           = float(p.get("notional", 5000.0))
        self.initial_equity     = float(p.get("initial_equity", 10000.0))
        self.sigma_floor_atr    = float(p.get("sigma_floor_atr", 0.5))
        self.commission_rate    = float(p.get("commission_rate", 0.0008))
        self.maker_rate         = float(p.get("maker_rate", 0.0002))
        self.rebate_pct         = float(p.get("rebate_pct", 0.70))
        self.settlement_hour    = int(p.get("settlement_hour_utc", 17))
        self.commission_per_side = self.notional * self.commission_rate

    def run(self, df_sig: pd.DataFrame) -> dict:
        """Run JIT backtest on signal DataFrame; return results dict identical to Backtester5589."""
        df = df_sig.reset_index(drop=False)

        if "datetime" in df.columns:
            datetimes = pd.to_datetime(df["datetime"])
        elif df_sig.index.name == "datetime":
            datetimes = pd.to_datetime(df_sig.index)
        else:
            col = "index" if "index" in df.columns else df.columns[0]
            datetimes = pd.to_datetime(df[col], errors="coerce")

        n = len(df)
        close   = df["close"].values.astype(float)
        high    = df["high"].values.astype(float)
        low     = df["low"].values.astype(float)
        volume  = df["volume"].values.astype(float) if "volume" in df.columns else np.ones(n)
        atr     = df["atr"].values.astype(float)
        long_a  = df["long_a"].values.astype(bool)
        short_a = df["short_a"].values.astype(bool)
        stoch   = df["stoch_9_d"].values.astype(float) if "stoch_9_d" in df.columns else np.full(n, 50.0)
        ema_89  = df["ema_89"].values.astype(float) if "ema_89" in df.columns else np.full(n, np.nan)
        ema_72  = ema(close, 72)

        (t_entry, t_exit, t_dir, t_ep, t_xp,
         t_gross, t_ecomm, t_phase, t_ratchet, t_green, t_is_tp, t_is_eod,
         n_trades_raw, equity_curve, position_counts) = _run_5589_core(
            close, high, low, volume, atr,
            long_a, short_a, stoch, ema_72, ema_89,
            self.sl_mult, self.avwap_sigma, float(self.avwap_warmup),
            self.tp_atr_offset, float(self.ratchet_threshold),
            self.notional, self.commission_per_side,
            self.sigma_floor_atr, self.initial_equity,
        )

        k = int(n_trades_raw)
        t_entry   = t_entry[:k]
        t_exit    = t_exit[:k]
        t_dir     = t_dir[:k]
        t_ep      = t_ep[:k]
        t_xp      = t_xp[:k]
        t_gross   = t_gross[:k]
        t_ecomm   = t_ecomm[:k]
        t_phase   = t_phase[:k]
        t_ratchet = t_ratchet[:k]
        t_green   = t_green[:k]
        t_is_tp   = t_is_tp[:k]
        t_is_eod  = t_is_eod[:k]

        total_rebate, total_commission = self._apply_settlement(
            datetimes, t_entry, t_exit, equity_curve,
        )

        # Build trades list for downstream compatibility
        trades = self._build_trades_list(
            t_entry, t_exit, t_dir, t_ep, t_xp,
            t_gross, t_ecomm, t_phase, t_ratchet, t_green, t_is_tp, t_is_eod,
        )

        metrics = self._compute_metrics_fast(
            t_gross, t_phase, t_ratchet, t_green, t_is_tp, t_is_eod,
            equity_curve, position_counts,
            equity_curve[-1] if n > 0 else self.initial_equity,
            total_rebate, total_commission,
        )

        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        return {
            "trades": trades,
            "trades_df": trades_df,
            "metrics": metrics,
            "equity_curve": equity_curve,
            "position_counts": position_counts,
        }

    # ------------------------------------------------------------------
    # Settlement rebate (Python post-pass)
    # ------------------------------------------------------------------

    def _apply_settlement(self, datetimes, t_entry, t_exit, equity_curve):
        """Apply daily rebate settlements to equity_curve in-place; return (total_rebate, total_comm)."""
        n = len(equity_curve)
        k = len(t_entry)

        # Build per-bar commission array
        comm_at = np.zeros(n, dtype=float)
        cps = self.commission_per_side
        for idx in range(k):
            eb = int(t_entry[idx])
            xb = int(t_exit[idx])
            if 0 <= eb < n:
                comm_at[eb] += cps
            if 0 <= xb < n:
                comm_at[xb] += cps

        total_commission = float(np.sum(comm_at))

        # Walk bars, accumulate daily commission, credit at settlement
        total_rebate      = 0.0
        daily_comm        = 0.0
        last_settle_day   = None
        running_rebate    = 0.0

        for i in range(n):
            bar_dt = datetimes.iloc[i] if hasattr(datetimes, "iloc") else datetimes[i]

            if bar_dt is not pd.NaT and not pd.isna(bar_dt):
                if bar_dt.tzinfo is None:
                    bar_dt = bar_dt.replace(tzinfo=__import__("datetime").timezone.utc)
                current_day  = bar_dt.date()
                current_hour = bar_dt.hour

                if last_settle_day is None:
                    last_settle_day = current_day

                if current_day > last_settle_day and current_hour >= self.settlement_hour:
                    if daily_comm > 0.0:
                        rebate = daily_comm * self.rebate_pct
                        total_rebate   += rebate
                        running_rebate += rebate
                        daily_comm      = 0.0
                    last_settle_day = current_day

            daily_comm += comm_at[i]
            equity_curve[i] += running_rebate

        return total_rebate, total_commission

    # ------------------------------------------------------------------
    # Metrics computation (vectorised from JIT arrays)
    # ------------------------------------------------------------------

    def _compute_metrics_fast(self, t_gross, t_phase, t_ratchet, t_green,
                               t_is_tp, t_is_eod, equity_curve, position_counts,
                               final_equity, total_rebate, total_commission):
        """Build metrics dict from JIT output arrays; mirrors Backtester5589 metrics format."""
        cps = self.commission_per_side
        total = len(t_gross)

        if total == 0:
            return {
                "total_trades": 0, "win_count": 0, "loss_count": 0,
                "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
                "expectancy": 0.0, "gross_profit": 0.0, "gross_loss": 0.0,
                "profit_factor": 0.0, "net_pnl": 0.0,
                "total_commission": 0.0, "total_rebate": total_rebate,
                "net_pnl_after_rebate": 0.0, "sharpe": 0.0,
                "max_drawdown": 0.0, "max_drawdown_pct": 0.0,
                "pct_losers_saw_green": 0.0, "saw_green_losers": 0, "total_losers": 0,
                "final_equity": final_equity, "equity_curve": equity_curve,
                "total_volume": self.notional * 2.0 * 0,
                "total_sides": 0, "avg_positions": 0.0,
                "max_positions_used": 0, "pct_time_flat": 1.0,
                "avg_margin_used": 0.0, "peak_margin_used": 0.0,
                "tp_exits": 0, "sl_exits": 0,
                "phase1_exits": 0, "phase2_exits": 0,
                "phase3_exits": 0, "phase4_exits": 0,
                "avg_ratchet_count": 0.0, "ratchet_threshold_hit_pct": 0.0,
                "be_raised_count": 0, "scale_out_count": 0,
            }

        pnls        = t_gross - cps * 2.0
        winners     = pnls[pnls > 0]
        losers      = pnls[pnls <= 0]
        win_count   = int(len(winners))
        loss_count  = int(len(losers))
        win_rate    = win_count / total
        gross_profit = float(np.sum(winners)) if len(winners) > 0 else 0.0
        gross_loss   = float(np.abs(np.sum(losers))) if len(losers) > 0 else 0.0
        pf           = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        net_pnl      = float(np.sum(pnls))

        # Sharpe
        if len(pnls) > 1:
            ret_std = float(np.std(pnls))
            sharpe  = (float(np.mean(pnls)) / ret_std * np.sqrt(252)) if ret_std > 0 else 0.0
        else:
            sharpe = 0.0

        # Drawdown
        peak      = np.maximum.accumulate(equity_curve)
        dd        = peak - equity_curve
        max_dd    = float(np.max(dd))
        max_dd_pct = float(np.max(dd / np.where(peak > 0, peak, 1.0)) * 100.0)

        # LSG
        sl_mask          = ~t_is_tp
        total_losers     = int(np.sum(pnls <= 0))
        saw_green_losers = int(np.sum(t_green & (pnls <= 0)))
        pct_lsg          = saw_green_losers / total_losers if total_losers > 0 else 0.0

        # Phase exits (exclude eod from phase counts, matching Backtester5589)
        non_eod     = ~t_is_eod
        tp_exits    = int(np.sum(t_is_tp))
        phase1_exits = int(np.sum((t_phase == 1) & sl_mask & non_eod))
        phase2_exits = int(np.sum((t_phase == 2) & sl_mask & non_eod))
        phase3_exits = int(np.sum((t_phase == 3) & sl_mask & non_eod))
        phase4_exits = tp_exits
        sl_exits     = total - tp_exits

        avg_ratchet  = float(np.mean(t_ratchet))
        ratchet_hit  = int(np.sum(t_ratchet >= self.ratchet_threshold))
        ratchet_hit_pct = ratchet_hit / total

        # Position usage
        valid_counts = position_counts.astype(float)
        n_bars       = len(valid_counts)
        total_vol    = self.notional * 2.0 * total

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
            "profit_factor": pf,
            "net_pnl": net_pnl,
            "total_commission": total_commission,
            "total_rebate": total_rebate,
            "net_pnl_after_rebate": net_pnl + total_rebate,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd_pct,
            "pct_losers_saw_green": pct_lsg,
            "saw_green_losers": saw_green_losers,
            "total_losers": total_losers,
            "final_equity": final_equity,
            "equity_curve": equity_curve,
            "total_volume": total_vol,
            "total_sides": total * 2,
            "avg_positions": float(np.mean(valid_counts)),
            "max_positions_used": int(np.max(valid_counts)),
            "pct_time_flat": float(np.sum(valid_counts == 0) / n_bars),
            "avg_margin_used": float(np.mean(valid_counts) * self.notional),
            "peak_margin_used": float(np.max(valid_counts) * self.notional),
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

    def _build_trades_list(self, t_entry, t_exit, t_dir, t_ep, t_xp,
                           t_gross, t_ecomm, t_phase, t_ratchet,
                           t_green, t_is_tp, t_is_eod):
        """Convert JIT output arrays to list of trade dicts for trades_df compatibility."""
        cps    = self.commission_per_side
        trades = []
        for i in range(len(t_gross)):
            pnl     = float(t_gross[i]) - float(t_ecomm[i]) - cps
            ph      = int(t_phase[i])
            is_tp   = bool(t_is_tp[i])
            is_eod  = bool(t_is_eod[i])
            if is_eod:
                reason = "eod"
            elif is_tp:
                reason = "tp_phase4"
            else:
                reason = "sl_phase" + str(ph)
            trades.append({
                "entry_bar":   int(t_entry[i]),
                "exit_bar":    int(t_exit[i]),
                "direction":   "LONG" if int(t_dir[i]) == 1 else "SHORT",
                "entry_price": float(t_ep[i]),
                "exit_price":  float(t_xp[i]),
                "pnl":         pnl,
                "commission":  float(t_ecomm[i]) + cps,
                "exit_reason": reason,
                "bars_held":   int(t_exit[i]) - int(t_entry[i]),
                "ratchet_count": int(t_ratchet[i]),
                "phase_at_exit": ph,
                "saw_green":   bool(t_green[i]),
            })
        return trades

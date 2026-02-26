"""
Backtester v385 -- Entry-state, lifecycle, LSG, P&L path, 12 new metrics, parquet.

Two-pass design:
  Pass 1: super().run() produces standard v384 results.
  Pass 2: Post-process trades with enriched data.

BBWP fields deferred (no Python implementation).
"""

import os
import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Any

from engine.backtester_v384 import Backtester384
from engine.position_v384 import Trade384


def _safe_val(arr, idx, default=0.0):
    """Return arr[idx] if valid, else default."""
    if arr is None or idx < 0 or idx >= len(arr):
        return default
    val = arr[idx]
    if isinstance(val, float) and np.isnan(val):
        return default
    return float(val)


class Backtester385(Backtester384):
    """v385 backtester with enriched trade data."""

    def __init__(self, params: dict = None):
        super().__init__(params)
        self._params = params or {}

    def run(self, df: pd.DataFrame) -> dict:
        results = super().run(df)
        trades = results["trades"]
        if not trades:
            return results

        params = self._params
        a = self._extract_arrays(df)
        enriched_data = []
        for trade in trades:
            entry = self._snapshot_entry(trade, a)
            life = self._compute_lifecycle(trade, a)
            path = self._classify_pnl_path(trade, a)
            lsg = self._categorize_lsg(trade, life, params)
            row = {}
            row.update(entry)
            row.update(life)
            row["life_pnl_path"] = path
            row["lsg_category"] = lsg
            enriched_data.append(row)

        base_df = results["trades_df"]
        enrich_df = pd.DataFrame(enriched_data)
        enriched_df = pd.concat(
            [base_df.reset_index(drop=True), enrich_df.reset_index(drop=True)],
            axis=1,
        )

        metrics = results["metrics"].copy()
        metrics.update(self._v385_metrics(trades, enriched_data))

        if params.get("save_parquet", False):
            sym = params.get("symbol", "UNKNOWN")
            tf = params.get("timeframe", "5m")
            out_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "results",
            )
            os.makedirs(out_dir, exist_ok=True)
            enriched_df.to_parquet(
                os.path.join(out_dir, f"trades_{sym}_{tf}.parquet"), index=False
            )

        results["trades_df"] = enriched_df
        results["metrics"] = metrics
        return results

    def _extract_arrays(self, df):
        n = len(df)
        def col(name, default=np.nan):
            if name in df.columns:
                return df[name].values.astype(float)
            return np.full(n, default, dtype=float)
        return {
            "close": df["close"].values.astype(float),
            "high": df["high"].values.astype(float),
            "low": df["low"].values.astype(float),
            "stoch_9": col("stoch_9", 50.0),
            "stoch_14": col("stoch_14", 50.0),
            "stoch_40": col("stoch_40", 50.0),
            "stoch_60": col("stoch_60", 50.0),
            "stoch_60_d": col("stoch_60_d", 50.0),
            "ema34": col("ema34"), "ema50": col("ema50"),
            "base_vol": col("base_vol", 0.0),
            "atr": col("atr"),
            "cloud3_bull": col("cloud3_bull"),
            "n": n,
        }

    def _snapshot_entry(self, t, a):
        i = t.entry_bar
        n = a["n"]
        if i < 0 or i >= n:
            return {
                "entry_stoch9_value": 50.0, "entry_stoch9_direction": "flat",
                "entry_stoch14_value": 50.0, "entry_stoch40_value": 50.0,
                "entry_stoch60_value": 50.0, "entry_stoch60_d": 50.0,
                "entry_ripster_cloud": "cloud3_0.00",
                "entry_ripster_expanding": False,
                "entry_avwap_distance": 0.0, "entry_atr": 0.0,
                "entry_vol_ratio": 1.0,
            }

        s9 = _safe_val(a["stoch_9"], i, 50.0)
        s9p = _safe_val(a["stoch_9"], i - 1, s9)
        s9_dir = "rising" if s9 > s9p else ("falling" if s9 < s9p else "flat")

        e34 = _safe_val(a["ema34"], i, 0.0)
        e50 = _safe_val(a["ema50"], i, 0.0)
        cv = _safe_val(a["close"], i, 0.0)
        cw = abs(e34 - e50)
        cd = (cv - max(e34, e50)) / cv * 100 if cv > 0 else 0.0

        expanding = False
        if i > 0:
            pw = abs(_safe_val(a["ema34"], i-1, 0.0) - _safe_val(a["ema50"], i-1, 0.0))
            expanding = cw > pw

        vr = 1.0
        if i >= 20:
            v = _safe_val(a["base_vol"], i, 0.0)
            m20 = float(np.nanmean(a["base_vol"][max(0, i-20):i]))
            if m20 > 0:
                vr = v / m20

        return {
            "entry_stoch9_value": s9, "entry_stoch9_direction": s9_dir,
            "entry_stoch14_value": _safe_val(a["stoch_14"], i, 50.0),
            "entry_stoch40_value": _safe_val(a["stoch_40"], i, 50.0),
            "entry_stoch60_value": _safe_val(a["stoch_60"], i, 50.0),
            "entry_stoch60_d": _safe_val(a["stoch_60_d"], i, 50.0),
            "entry_ripster_cloud": f"cloud3_{cd:.2f}",
            "entry_ripster_expanding": expanding,
            "entry_avwap_distance": 0.0,
            "entry_atr": float(t.entry_atr),
            "entry_vol_ratio": vr,
        }

    def _compute_lifecycle(self, t, a):
        start = t.entry_bar
        end = t.exit_bar
        n = a["n"]
        if end <= start or start >= n:
            return self._empty_lifecycle()

        ei = min(end + 1, n)
        nb = ei - start
        sl = slice(start, ei)

        s9 = a["stoch_9"][sl]
        s9c = s9[~np.isnan(s9)]
        s9_min = float(np.min(s9c)) if len(s9c) > 0 else 50.0
        s9_max = float(np.max(s9c)) if len(s9c) > 0 else 50.0
        slope = 0.0
        if len(s9c) >= 3:
            slope = float(np.polyfit(np.arange(len(s9c)), s9c, 1)[0])

        k = a["stoch_9"][sl]
        d = a["stoch_14"][sl]
        v = ~(np.isnan(k) | np.isnan(d))
        crossed = bool(np.any(np.diff(np.sign(k[v] - d[v])) != 0)) if v.sum() >= 2 else False

        c3 = a["cloud3_bull"][sl]
        c3v = c3[~np.isnan(c3)]
        flipped = bool(np.any(np.diff(c3v) != 0)) if len(c3v) >= 2 else False

        e34 = a["ema34"][sl]
        e50 = a["ema50"][sl]
        ew = abs(e34[0] - e50[0]) if not (np.isnan(e34[0]) or np.isnan(e50[0])) else 0.0
        xw = abs(e34[-1] - e50[-1]) if not (np.isnan(e34[-1]) or np.isnan(e50[-1])) else 0.0
        wc = (xw - ew) / ew if ew > 0 else 0.0

        cl = a["close"][sl]
        hi = a["high"][sl]
        lo = a["low"][sl]
        hlc3 = (hi + lo + cl) / 3.0
        bv = a["base_vol"][sl]

        cum_pv = 0.0
        cum_v = 0.0
        max_ad = 0.0
        end_ad = 0.0
        for j in range(nb):
            vj = bv[j] if not np.isnan(bv[j]) else 0.0
            cum_pv += hlc3[j] * vj
            cum_v += vj
            if cum_v > 0:
                aw = cum_pv / cum_v
                dd = (cl[j] - aw) / aw * 100 if aw > 0 else 0.0
                if abs(dd) > abs(max_ad):
                    max_ad = dd
                end_ad = dd

        full_bv = a["base_vol"]
        vrs = []
        for j in range(nb):
            idx = start + j
            if idx >= 20:
                m20 = float(np.nanmean(full_bv[max(0, idx-20):idx]))
                vj = full_bv[idx]
                vrs.append(vj / m20 if m20 > 0 and not np.isnan(vj) else 1.0)
            else:
                vrs.append(1.0)
        va = float(np.mean(vrs)) if vrs else 1.0
        vt = float(np.polyfit(np.arange(len(vrs)), vrs, 1)[0]) if len(vrs) >= 3 else 0.0

        ep = t.entry_price
        is_long = t.direction == "LONG"
        mfe_b = 0
        mae_b = 0
        best = -1e18
        worst = 1e18
        tig = 0
        for j in range(nb):
            u = (cl[j] - ep) if is_long else (ep - cl[j])
            if u > best:
                best = u
                mfe_b = j
            if u < worst:
                worst = u
                mae_b = j
            if u > 0:
                tig += 1

        return {
            "life_bars": nb, "life_stoch9_min": s9_min,
            "life_stoch9_max": s9_max, "life_stoch9_trend": slope,
            "life_stoch9_crossed_signal": crossed,
            "life_ripster_flip": flipped,
            "life_ripster_width_change": float(wc),
            "life_avwap_max_dist": float(max_ad),
            "life_avwap_end_dist": float(end_ad),
            "life_vol_avg": va, "life_vol_trend": vt,
            "life_mfe_bar": mfe_b, "life_mae_bar": mae_b,
            "time_in_green": tig,
        }

    def _empty_lifecycle(self):
        return {
            "life_bars": 0, "life_stoch9_min": 50.0, "life_stoch9_max": 50.0,
            "life_stoch9_trend": 0.0, "life_stoch9_crossed_signal": False,
            "life_ripster_flip": False, "life_ripster_width_change": 0.0,
            "life_avwap_max_dist": 0.0, "life_avwap_end_dist": 0.0,
            "life_vol_avg": 1.0, "life_vol_trend": 0.0,
            "life_mfe_bar": 0, "life_mae_bar": 0, "time_in_green": 0,
        }

    def _classify_pnl_path(self, t, a):
        start = t.entry_bar
        end = t.exit_bar
        n = a["n"]
        if end <= start or start >= n:
            return "direct"
        cl = a["close"][start:min(end + 1, n)]
        ep = t.entry_price
        is_long = t.direction == "LONG"
        crossings = 0
        was_g = False
        was_r = False
        ps = 0
        for c in cl:
            u = (c - ep) if is_long else (ep - c)
            if u > 0:
                was_g = True
                s = 1
            elif u < 0:
                was_r = True
                s = -1
            else:
                s = ps
            if ps != 0 and s != 0 and s != ps:
                crossings += 1
            ps = s
        if crossings >= 3:
            return "choppy"
        net = t.pnl - t.commission
        if was_g and net < 0:
            return "green_then_red"
        if was_r and net > 0:
            return "red_then_green"
        return "direct"

    def _categorize_lsg(self, t, life, params):
        net = t.pnl - t.commission
        if net >= 0 or not t.saw_green:
            return ""
        mfe = t.mfe
        ea = t.entry_atr if t.entry_atr > 0 else 1.0
        tp_m = params.get("tp_mult", 0)
        be_t = ea * params.get("be_trigger_atr", 0.5)
        tig = life.get("time_in_green", 0)
        if tp_m > 0 and mfe > 0.8 * ea * tp_m:
            return "C"
        if mfe > be_t:
            return "D"
        if tig > 10:
            return "B"
        return "A"

    def _v385_metrics(self, trades, enriched):
        if not trades:
            return {}
        pnls = [t.pnl - t.commission for t in trades]
        winners = [p for p in pnls if p > 0]
        losers = [p for p in pnls if p < 0]

        mws = mls = cw = cl_ = 0
        for p in pnls:
            if p > 0:
                cw += 1
                cl_ = 0
                mws = max(mws, cw)
            elif p < 0:
                cl_ += 1
                cw = 0
                mls = max(mls, cl_)
            else:
                cw = cl_ = 0

        sortino = 0.0
        if len(pnls) >= 2:
            arr = np.array(pnls)
            neg = arr[arr < 0]
            ds = float(np.std(neg)) if len(neg) > 1 else 0.001
            sortino = float(np.mean(arr)) / ds * np.sqrt(252) if ds > 0 else 0.0

        net = sum(pnls)
        eq = np.cumsum(pnls)
        rm = np.maximum.accumulate(eq)
        dd = eq - rm
        mdd = float(np.min(dd)) if len(dd) > 0 else 0.0
        calmar = net / abs(mdd) if mdd < 0 else float("inf")

        be_exits = sum(1 for p in pnls if abs(p) < 0.01)
        aw = float(np.mean(winners)) if winners else 0.0
        al = float(np.mean(losers)) if losers else 0.0
        wlr = aw / abs(al) if al != 0 else float("inf")

        cats = [e.get("lsg_category", "") for e in enriched]
        lt = sum(1 for c in cats if c in ("A", "B", "C", "D"))
        if lt > 0:
            la = sum(1 for c in cats if c == "A") / lt * 100
            lb = sum(1 for c in cats if c == "B") / lt * 100
            lc = sum(1 for c in cats if c == "C") / lt * 100
            ld = sum(1 for c in cats if c == "D") / lt * 100
        else:
            la = lb = lc = ld = 0.0

        li = [j for j, c in enumerate(cats) if c in ("A", "B", "C", "D")]
        alm = float(np.mean([trades[j].mfe for j in li])) if li else 0.0
        alg = float(np.mean([enriched[j].get("time_in_green", 0) for j in li])) if li else 0.0

        return {
            "peak_capital": 0, "capital_efficiency": 0,
            "max_single_win": max(winners) if winners else 0,
            "max_single_loss": min(losers) if losers else 0,
            "avg_winner": aw, "avg_loser": al, "wl_ratio": wlr,
            "max_win_streak": mws, "max_loss_streak": mls,
            "sortino": sortino, "calmar": calmar, "be_exits": be_exits,
            "lsg_cat_a_pct": la, "lsg_cat_b_pct": lb,
            "lsg_cat_c_pct": lc, "lsg_cat_d_pct": ld,
            "avg_loser_mfe": alm, "avg_loser_green_bars": alg,
        }

"""
Deep Trade Analysis: Negative Coins + FARTCOINUSDT -- 55/89 EMA Cross v2.

Phases:
  1 - Run pipeline on all 9 coins; identify negative-PnL coins
  2 - Per-trade context extraction (signal state at entry)
  3 - Failure mode classification
  4 - Statistical summary (text report)
  5 - Raw CSV export
  6 - Plotly HTML charts (EMA cross timing, bad entry analysis, FARTCOIN deep-dive)

Run: python scripts/analyze_negative_coins_5589.py
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signals.ema_cross_55_89_v2 import compute_signals_55_89
from engine.backtester_55_89 import Backtester5589

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

COINS = [
    "FARTCOINUSDT",
    "FILUSDT",
    "OGUSDT",
    "CHZUSDT",
    "ORDERUSDT",
    "BIGTIMEUSDT",
    "CVCUSDT",
    "BBUSDT",
    "TRUMPUSDT",
]

PARAMS = {
    "sl_mult":           4.0,
    "avwap_sigma":       2.0,
    "avwap_warmup":      20,
    "tp_atr_offset":     0.5,
    "ratchet_threshold": 2,
    "notional":          10000.0,
    "initial_equity":    10000.0,
    "commission_rate":   0.0008,
    "rebate_pct":        0.70,
    "min_signal_gap":    50,
    "leverage":          20,
}

AVWAP_WARMUP = PARAMS["avwap_warmup"]
RATCHET_THRESHOLD = PARAMS["ratchet_threshold"]

DATA_DIR    = ROOT / "data" / "historical"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Version tag for new-version output files
_VER = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── Data Loading ──────────────────────────────────────────────────────────────

def load_parquet(symbol: str) -> pd.DataFrame:
    """Load full history for a symbol; return sorted DataFrame with datetime index."""
    path = DATA_DIR / f"{symbol}_1m.parquet"
    if not path.exists():
        log.warning("Parquet not found: %s", path)
        return pd.DataFrame()
    df = pd.read_parquet(path)
    # Normalise index to datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        if "datetime" in df.columns:
            df = df.set_index("datetime")
        elif "open_time" in df.columns:
            df = df.set_index("open_time")
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.sort_index()
    # Ensure required columns exist
    for col in ("open", "high", "low", "close", "volume"):
        if col not in df.columns:
            log.warning("%s missing column '%s'", symbol, col)
    return df


# ── Pipeline Runner ────────────────────────────────────────────────────────────

def run_coin(symbol: str) -> dict | None:
    """Load, compute signals, run engine. Return result dict or None on failure."""
    log.info("Running %s ...", symbol)
    df = load_parquet(symbol)
    if df.empty:
        log.warning("No data for %s -- skipping", symbol)
        return None
    try:
        df_sig = compute_signals_55_89(df, PARAMS)
    except Exception as exc:
        log.error("Signal error for %s: %s", symbol, exc)
        return None
    try:
        bt = Backtester5589(PARAMS)
        result = bt.run(df_sig)
    except Exception as exc:
        log.error("Engine error for %s: %s", symbol, exc)
        return None
    result["symbol"] = symbol
    result["df_sig"] = df_sig
    log.info(
        "  %s: %d trades | WR=%.1f%% | PnL=$%.2f",
        symbol,
        result["metrics"]["total_trades"],
        result["metrics"]["win_rate"] * 100,
        result["metrics"]["net_pnl"],
    )
    return result


# ── Column Resolver ────────────────────────────────────────────────────────────

def safe_col(df: pd.DataFrame, col: str, idx: int, default=np.nan):
    """Safely retrieve a value from df column at idx; return default if missing."""
    if col not in df.columns:
        return default
    try:
        return df[col].iloc[idx]
    except IndexError:
        return default


# ── Context Extractor ──────────────────────────────────────────────────────────

def extract_trade_contexts(symbol: str, trades_df: pd.DataFrame, df_sig: pd.DataFrame) -> list:
    """Build per-trade context dicts for all trades in a coin's result."""
    if trades_df.empty:
        return []

    close_arr = df_sig["close"].values
    atr_arr   = df_sig["atr"].values if "atr" in df_sig.columns else np.full(len(df_sig), np.nan)

    contexts = []
    for _, row in trades_df.iterrows():
        eb   = int(row["entry_bar"])
        xb   = int(row["exit_bar"])
        dirn = str(row["direction"])

        entry_price  = float(row["entry_price"])
        exit_price   = float(row["exit_price"])
        pnl          = float(row["pnl"])
        bars_held    = int(row["bars_held"])
        exit_reason  = str(row["exit_reason"])
        ratchet_count= int(row["ratchet_count"])
        saw_green    = bool(row["saw_green"])
        trade_grade  = str(row.get("trade_grade", ""))

        # ATR at entry
        atr_entry = safe_col(df_sig, "atr", eb)
        atr_pct   = (atr_entry / entry_price * 100.0) if (not np.isnan(atr_entry) and entry_price > 0) else np.nan

        # Stoch 9
        k9_val = safe_col(df_sig, "stoch_9", eb)
        d9_val = safe_col(df_sig, "stoch_9_d", eb)
        kd_diff = abs(k9_val - d9_val) if not (np.isnan(k9_val) or np.isnan(d9_val)) else np.nan

        # Stoch 40 / 60 slope (between entry bar and entry-5 bars back)
        slope_n = 5
        k40_now  = safe_col(df_sig, "stoch_40", eb)
        k40_prev = safe_col(df_sig, "stoch_40", max(0, eb - slope_n))
        slope_40 = (k40_now - k40_prev) if not (np.isnan(k40_now) or np.isnan(k40_prev)) else np.nan

        k60_now  = safe_col(df_sig, "stoch_60", eb)
        k60_prev = safe_col(df_sig, "stoch_60", max(0, eb - slope_n))
        slope_60 = (k60_now - k60_prev) if not (np.isnan(k60_now) or np.isnan(k60_prev)) else np.nan

        # EMA delta at entry
        ema_delta = safe_col(df_sig, "ema_delta", eb)
        ema_55_val = safe_col(df_sig, "ema_55", eb)
        ema_89_val = safe_col(df_sig, "ema_89", eb)

        # BBW state
        bbwp_state = safe_col(df_sig, "bbwp_state", eb, default="UNKNOWN")
        bbwp_value = safe_col(df_sig, "bbwp_value", eb)

        # TDI
        tdi_price  = safe_col(df_sig, "tdi_price", eb)
        tdi_signal = safe_col(df_sig, "tdi_signal", eb)
        tdi_above  = bool(tdi_price > tdi_signal) if not (np.isnan(tdi_price) or np.isnan(tdi_signal)) else None

        # EMA cross context: was there a 55/89 cross close to entry?
        # Look back 20 bars for a cross
        ema_cross_bars_back = np.nan
        for lookback in range(1, min(50, eb + 1)):
            cross_bull = safe_col(df_sig, "ema_cross_bull", eb - lookback, default=False)
            cross_bear = safe_col(df_sig, "ema_cross_bear", eb - lookback, default=False)
            if (dirn == "LONG" and cross_bull) or (dirn == "SHORT" and cross_bear):
                ema_cross_bars_back = lookback
                break

        # EMA alignment: delta sign vs direction
        ema_aligned = False
        if not np.isnan(ema_delta):
            if dirn == "LONG" and ema_delta > 0:
                ema_aligned = True
            elif dirn == "SHORT" and ema_delta < 0:
                ema_aligned = True

        # COUNTER_TREND: delta is strongly opposite direction
        counter_trend = False
        if not np.isnan(ema_delta):
            if dirn == "LONG" and ema_delta < -0.0:
                counter_trend = True
            elif dirn == "SHORT" and ema_delta > 0.0:
                counter_trend = True

        # Phase 2 freeze bar
        freeze_bar = eb + AVWAP_WARMUP - 1  # bar index where phase 2 begins

        # Datetime at entry
        try:
            entry_dt = df_sig.index[eb]
        except IndexError:
            entry_dt = pd.NaT

        ctx = {
            "symbol": symbol,
            "direction": dirn,
            "entry_bar": eb,
            "exit_bar": xb,
            "entry_dt": entry_dt,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "bars_held": bars_held,
            "exit_reason": exit_reason,
            "trade_grade": trade_grade,
            "saw_green": saw_green,
            "ratchet_count": ratchet_count,
            # Stoch
            "stoch9_k": k9_val,
            "stoch9_d": d9_val,
            "stoch9_kd_diff": kd_diff,
            "slope_40": slope_40,
            "slope_60": slope_60,
            # EMA
            "ema_55": ema_55_val,
            "ema_89": ema_89_val,
            "ema_delta": ema_delta,
            "ema_aligned": ema_aligned,
            "ema_cross_bars_back": ema_cross_bars_back,
            # ATR
            "atr_at_entry": atr_entry,
            "atr_pct_of_price": atr_pct,
            # BBW / TDI
            "bbwp_state": bbwp_state,
            "bbwp_value": bbwp_value,
            "tdi_price": tdi_price,
            "tdi_signal": tdi_signal,
            "tdi_confirming": tdi_above,
            # Derived
            "counter_trend": counter_trend,
            "freeze_bar": freeze_bar,
        }
        contexts.append(ctx)
    return contexts


# ── Failure Mode Classifier ────────────────────────────────────────────────────

def classify_failure_modes(ctx: dict, atr_75th: float) -> list:
    """Return list of failure mode strings for a trade context."""
    modes = []
    reason = ctx["exit_reason"]
    pnl    = ctx["pnl"]

    if reason == "eod":
        modes.append("EOD_FORCED")
        return modes

    if reason == "sl_phase1":
        modes.append("PHASE1_INSTANT_DEATH")

    if reason == "sl_phase2" and ctx["ratchet_count"] == 0:
        modes.append("PHASE2_GRAVEYARD")

    if reason == "sl_phase2" and ctx["saw_green"]:
        modes.append("PHASE2_SAW_GREEN")

    if reason == "sl_phase3" and ctx["ratchet_count"] < RATCHET_THRESHOLD:
        modes.append("RATCHET_INSUFFICIENT")

    if ctx["trade_grade"] == "C" and pnl < 0:
        modes.append("WEAK_ENTRY")

    kd = ctx["stoch9_kd_diff"]
    if not np.isnan(kd) and kd < 2.0 and pnl < 0:
        modes.append("MARGINAL_CROSS")

    atr_pct = ctx["atr_pct_of_price"]
    if not np.isnan(atr_pct) and not np.isnan(atr_75th) and atr_pct > atr_75th and pnl < 0:
        modes.append("HIGH_ATR_ENTRY")

    if ctx["counter_trend"] and pnl < 0:
        modes.append("COUNTER_TREND")

    if not modes:
        modes.append("OTHER")
    return modes


# ── Statistical Summary ────────────────────────────────────────────────────────

def compute_portfolio_summary(all_results: dict) -> dict:
    """Return dict of per-coin metrics summary."""
    summary = {}
    for sym, res in all_results.items():
        m = res["metrics"]
        summary[sym] = {
            "net_pnl": m["net_pnl"],
            "total_trades": m["total_trades"],
            "win_rate": m["win_rate"],
            "max_drawdown_pct": m["max_drawdown_pct"],
            "phase1_exits": m["phase1_exits"],
            "phase2_exits": m["phase2_exits"],
            "phase3_exits": m["phase3_exits"],
            "phase4_exits": m.get("phase4_exits", 0),
            "avg_ratchet": m["avg_ratchet_count"],
            "pct_lsg": m["pct_losers_saw_green"],
        }
    return summary


def print_text_report(
    summary: dict,
    neg_coins: list,
    all_contexts: pd.DataFrame,
    fart_contexts: pd.DataFrame,
    out_path: Path,
):
    """Generate full text report and save to out_path."""
    lines = []

    lines.append("=" * 70)
    lines.append("  55/89 EMA CROSS v2 — NEGATIVE COINS DEEP ANALYSIS")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    lines.append("\n=== PORTFOLIO OVERVIEW ===")
    lines.append(f"Total coins analysed: {len(summary)}")
    lines.append(f"Negative PnL coins  : {len(neg_coins)}")
    lines.append("")
    all_pnl = sorted(summary.items(), key=lambda x: x[1]["net_pnl"])
    for sym, m in all_pnl:
        marker = " <<< NEGATIVE" if m["net_pnl"] < 0 else ""
        lines.append(
            f"  {sym:<20} PnL=${m['net_pnl']:>10.2f}  Trades={m['total_trades']:>4}  WR={m['win_rate']*100:.1f}%{marker}"
        )

    # ── Failure modes across all negative coins ──
    if not all_contexts.empty:
        neg_df = all_contexts[all_contexts["symbol"].isin(neg_coins)].copy()
        neg_losers = neg_df[neg_df["pnl"] < 0].copy()
        lines.append("\n=== FAILURE MODE DISTRIBUTION (all negative-coin losers) ===")
        if "failure_modes" in neg_losers.columns:
            mode_counts: dict = {}
            for modes_list in neg_losers["failure_modes"]:
                if isinstance(modes_list, list):
                    for m in modes_list:
                        mode_counts[m] = mode_counts.get(m, 0) + 1
            total_neg_losers = len(neg_losers)
            for mode, cnt in sorted(mode_counts.items(), key=lambda x: -x[1]):
                pct = cnt / total_neg_losers * 100 if total_neg_losers > 0 else 0
                lines.append(f"  {mode:<28}: {cnt:>5} ({pct:.1f}%)")

    # ── Per-coin breakdowns ──
    lines.append("\n=== PER-COIN BREAKDOWN (negative coins) ===")
    for sym in neg_coins:
        m = summary[sym]
        coin_df = all_contexts[all_contexts["symbol"] == sym] if not all_contexts.empty else pd.DataFrame()
        lines.append(f"\n{sym}")
        lines.append(f"  Net PnL       : ${m['net_pnl']:.2f}")
        lines.append(f"  Total trades  : {m['total_trades']}")
        lines.append(f"  Win rate      : {m['win_rate']*100:.1f}%")
        lines.append(f"  Max DD        : {m['max_drawdown_pct']:.1f}%")
        lines.append(f"  Phase exits   : P1={m['phase1_exits']} P2={m['phase2_exits']} P3={m['phase3_exits']} TP={m['phase4_exits']}")
        lines.append(f"  Avg ratchets  : {m['avg_ratchet']:.2f}")
        lines.append(f"  %LSG          : {m['pct_lsg']*100:.1f}%")

        if not coin_df.empty:
            losers = coin_df[coin_df["pnl"] < 0]
            winners = coin_df[coin_df["pnl"] > 0]
            lines.append(f"  Avg winner    : ${winners['pnl'].mean():.2f}" if len(winners) > 0 else "  Avg winner    : n/a")
            lines.append(f"  Avg loser     : ${losers['pnl'].mean():.2f}" if len(losers) > 0 else "  Avg loser     : n/a")
            if "atr_pct_of_price" in coin_df.columns:
                lines.append(f"  Avg ATR%price : {coin_df['atr_pct_of_price'].mean():.3f}%")
            if "trade_grade" in coin_df.columns:
                gc = coin_df["trade_grade"].value_counts(normalize=True) * 100
                grade_str = "  ".join([f"{g}={v:.0f}%" for g, v in gc.items()])
                lines.append(f"  Grade dist    : {grade_str}")
            if "failure_modes" in losers.columns:
                mode_counts = {}
                for ml in losers["failure_modes"]:
                    if isinstance(ml, list):
                        for mo in ml:
                            mode_counts[mo] = mode_counts.get(mo, 0) + 1
                top = sorted(mode_counts.items(), key=lambda x: -x[1])[:4]
                top_str = ", ".join([f"{mo}({cnt})" for mo, cnt in top])
                lines.append(f"  Top fail modes: {top_str}")

    # ── FARTCOIN deep dive ──
    lines.append("\n" + "=" * 70)
    lines.append("  FARTCOINUSDT DEEP DIVE")
    lines.append("=" * 70)
    if not fart_contexts.empty:
        fc = fart_contexts
        losers = fc[fc["pnl"] < 0]
        winners = fc[fc["pnl"] > 0]

        lines.append(f"\nTotal trades       : {len(fc)}")
        lines.append(f"Winners            : {len(winners)} ({len(winners)/len(fc)*100:.1f}%)")
        lines.append(f"Losers             : {len(losers)}")
        lines.append(f"Net PnL            : ${fc['pnl'].sum():.2f}")

        if "atr_pct_of_price" in fc.columns:
            atr_stats = fc["atr_pct_of_price"].describe()
            lines.append(f"\nATR% of price stats:")
            lines.append(f"  min={atr_stats['min']:.3f}  25th={atr_stats['25%']:.3f}  "
                        f"median={atr_stats['50%']:.3f}  75th={atr_stats['75%']:.3f}  max={atr_stats['max']:.3f}")

        lines.append(f"\nPhase exit distribution:")
        if "exit_reason" in fc.columns:
            er_counts = fc["exit_reason"].value_counts()
            for er, cnt in er_counts.items():
                pct = cnt / len(fc) * 100
                lines.append(f"  {er:<20}: {cnt:>4} ({pct:.1f}%)")

        if "failure_modes" in losers.columns:
            mode_counts = {}
            for ml in losers["failure_modes"]:
                if isinstance(ml, list):
                    for mo in ml:
                        mode_counts[mo] = mode_counts.get(mo, 0) + 1
            lines.append(f"\nFailure mode breakdown (losers):")
            for mo, cnt in sorted(mode_counts.items(), key=lambda x: -x[1]):
                pct = cnt / len(losers) * 100 if len(losers) > 0 else 0
                lines.append(f"  {mo:<28}: {cnt:>4} ({pct:.1f}%)")

        # saw_green losers
        sg_losers = losers[losers["saw_green"] == True] if "saw_green" in losers.columns else pd.DataFrame()
        lines.append(f"\nLosers that saw green : {len(sg_losers)} ({len(sg_losers)/len(losers)*100:.1f}% of losers)")

        # Worst 10 trades
        lines.append("\n-- WORST 10 TRADES --")
        worst = fc.nsmallest(10, "pnl")
        for _, r in worst.iterrows():
            modes_str = str(r.get("failure_modes", []))[:50]
            lines.append(
                f"  Bar={r['entry_bar']:>6}  Dir={r['direction']}  "
                f"PnL=${r['pnl']:>8.2f}  Exit={r['exit_reason']:<15}  "
                f"Ratchets={r['ratchet_count']}  Grade={r['trade_grade']}  "
                f"Modes={modes_str}"
            )

        # Recommendation
        lines.append("\n-- RECOMMENDATION --")
        avg_atr_fart = fc["atr_pct_of_price"].mean() if "atr_pct_of_price" in fc.columns else 0
        phase1_pct = summary.get("FARTCOINUSDT", {}).get("phase1_exits", 0) / max(len(fc), 1) * 100
        grade_c_pct = (fc["trade_grade"] == "C").mean() * 100 if "trade_grade" in fc.columns else 0
        lines.append(f"  ATR% avg={avg_atr_fart:.3f}% | Phase1 exits={phase1_pct:.1f}% | Grade-C={grade_c_pct:.1f}%")
        if avg_atr_fart > 0.5:
            lines.append("  VERDICT: High ATR spike coin. Consider EXCLUDING or applying ATR% entry filter (>0.5% skip).")
        if grade_c_pct > 50:
            lines.append("  VERDICT: >50% Grade-C entries. Apply grade filter: only A+B trades allowed.")
        lines.append("  KEY FIX: Add bbwp_state == 'QUIET' guard — do not enter during compressed volatility.")
        lines.append("  KEY FIX: EMA delta must be > 0 (long) / < 0 (short) at entry — eliminate COUNTER_TREND.")

    # ── Cross-coin patterns ──
    lines.append("\n=== CROSS-COIN PATTERNS ===")
    if not all_contexts.empty and "failure_modes" in all_contexts.columns:
        neg_df = all_contexts[all_contexts["symbol"].isin(neg_coins)].copy()
        neg_losers = neg_df[neg_df["pnl"] < 0].copy()
        pg = neg_losers.groupby("symbol")["pnl"].agg(["count", "mean"])
        lines.append("  Per-coin loser count and avg loss:")
        for sym, row in pg.iterrows():
            lines.append(f"    {sym:<20}: {int(row['count']):>4} losers  avg=${row['mean']:.2f}")

        lines.append("\n  Grade C correlation to losses:")
        for sym in neg_coins:
            cd = all_contexts[all_contexts["symbol"] == sym]
            if not cd.empty and "trade_grade" in cd.columns:
                c_pct = (cd["trade_grade"] == "C").mean() * 100
                c_wr = cd[cd["trade_grade"] == "C"]["pnl"].gt(0).mean() * 100 if len(cd[cd["trade_grade"] == "C"]) > 0 else 0
                lines.append(f"    {sym:<20}: Grade-C={c_pct:.0f}%  Grade-C WR={c_wr:.0f}%")

    lines.append("\n" + "=" * 70)
    lines.append("  STATE MONITORING ADJUSTMENT RECOMMENDATIONS")
    lines.append("=" * 70)
    lines.append("""
  1. ATR GATE: Compute rolling 75th-percentile ATR% for each coin.
     Skip entry if atr_pct_of_price > 75th-percentile threshold.
     → Eliminates HIGH_ATR_ENTRY failure class.

  2. EMA ALIGNMENT GATE: Only enter LONG when ema_delta > 0 (55>89).
     Only enter SHORT when ema_delta < 0 (55<89).
     → Eliminates COUNTER_TREND failure class entirely.

  3. GRADE FILTER: Disable Grade-C entries (both 40 and 60 stoch misaligned).
     → Dramatically reduces WEAK_ENTRY losses with minimal winner impact.

  4. BBW QUIET GUARD: If bbwp_state == 'QUIET' at entry, skip.
     Quiet BBW = compression = no momentum = PHASE1/2 death trap.

  5. MIN K/D SPREAD: Require abs(stoch9_K - stoch9_D) >= 3.0 at entry.
     → Eliminates MARGINAL_CROSS weak signals.

  6. PHASE 2 AVWAP TIGHTENING CHECK: Before committing to phase 2,
     check if frozen AVWAP band would be TIGHTER than phase 1 SL.
     If new_sl < phase1_sl distance (for longs), extend warmup or keep P1.
     → Eliminates most PHASE2_GRAVEYARD trades.

  7. EMA CROSS PROXIMITY GATE: Require that a 55/89 cross occurred
     within the last 30–50 bars. Entry too far from a cross = stale signal.
     → Improves signal freshness quality.
""")

    report = "\n".join(lines)
    print(report)
    out_path.write_text(report, encoding="utf-8")
    log.info("Text report saved -> %s", out_path)


# ── Plotly Chart Builder ───────────────────────────────────────────────────────

def build_charts(all_results: dict, all_contexts: pd.DataFrame, neg_coins: list):
    """Build and save interactive Plotly HTML charts."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import plotly.express as px
    except ImportError:
        log.warning("plotly not installed — skipping chart generation. Run: pip install plotly")
        return

    # ── Chart 1: Failure mode distribution (all negative coins) ──────────────
    if not all_contexts.empty and "failure_modes" in all_contexts.columns:
        neg_df = all_contexts[all_contexts["symbol"].isin(neg_coins)]
        neg_losers = neg_df[neg_df["pnl"] < 0]
        mode_counts: dict = {}
        for ml in neg_losers["failure_modes"]:
            if isinstance(ml, list):
                for mo in ml:
                    mode_counts[mo] = mode_counts.get(mo, 0) + 1

        if mode_counts:
            modes_sorted = sorted(mode_counts.items(), key=lambda x: x[1], reverse=True)
            fig1 = go.Figure(go.Bar(
                x=[m[0] for m in modes_sorted],
                y=[m[1] for m in modes_sorted],
                marker_color="crimson",
                text=[f"{m[1]}" for m in modes_sorted],
                textposition="outside",
            ))
            fig1.update_layout(
                title="Failure Mode Distribution — All Negative Coins (55/89 v2)",
                xaxis_title="Failure Mode",
                yaxis_title="Trade Count",
                template="plotly_dark",
                height=500,
            )
            out1 = RESULTS_DIR / f"chart_failure_modes_{_VER}.html"
            fig1.write_html(str(out1))
            log.info("Chart 1 saved -> %s", out1)

    # ── Chart 2: EMA Cross Timing vs Entry Signal ─────────────────────────────
    # For FARTCOIN: show price, EMA 55/89, signals, and cross events
    if "FARTCOINUSDT" in all_results:
        res = all_results["FARTCOINUSDT"]
        df_sig = res["df_sig"]
        trades_df = res["trades_df"]

        # Limit to first 3000 bars for chart readability
        CHART_BARS = 3000
        df_chart = df_sig.iloc[:CHART_BARS].copy()

        long_entries  = trades_df[(trades_df["direction"] == "LONG")  & (trades_df["entry_bar"] < CHART_BARS)]
        short_entries = trades_df[(trades_df["direction"] == "SHORT") & (trades_df["entry_bar"] < CHART_BARS)]

        fig2 = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.55, 0.25, 0.20],
            subplot_titles=["FARTCOINUSDT — Price + EMA 55/89 + Entries",
                            "EMA Delta (55-89): Cross = strategy is aligning",
                            "Stoch 9 D — Overzone Entry State Machine"],
            vertical_spacing=0.06,
        )

        x = list(range(len(df_chart)))

        # Price + EMA
        fig2.add_trace(go.Scatter(x=x, y=df_chart["close"].values, name="Close",
                                  line=dict(color="white", width=1), opacity=0.7), row=1, col=1)
        if "ema_55" in df_chart.columns:
            fig2.add_trace(go.Scatter(x=x, y=df_chart["ema_55"].values, name="EMA 55",
                                      line=dict(color="#FFD700", width=1.5)), row=1, col=1)
        if "ema_89" in df_chart.columns:
            fig2.add_trace(go.Scatter(x=x, y=df_chart["ema_89"].values, name="EMA 89",
                                      line=dict(color="#FF6347", width=1.5)), row=1, col=1)

        # Long entries
        le_bars = long_entries["entry_bar"].values
        le_prices = [df_chart["close"].iloc[b] if b < len(df_chart) else np.nan for b in le_bars]
        le_pnls = long_entries["pnl"].values
        le_colors = ["lime" if p > 0 else "red" for p in le_pnls]
        le_grades = long_entries["trade_grade"].values if "trade_grade" in long_entries.columns else [""] * len(le_bars)
        fig2.add_trace(go.Scatter(
            x=le_bars, y=le_prices, mode="markers",
            name="LONG entry",
            marker=dict(symbol="triangle-up", size=10,
                        color=le_colors,
                        line=dict(color="white", width=1)),
            text=[f"Bar={b}<br>PnL=${p:.2f}<br>Grade={g}" for b, p, g in zip(le_bars, le_pnls, le_grades)],
            hoverinfo="text",
        ), row=1, col=1)

        # Short entries
        se_bars = short_entries["entry_bar"].values
        se_prices = [df_chart["close"].iloc[b] if b < len(df_chart) else np.nan for b in se_bars]
        se_pnls = short_entries["pnl"].values
        se_colors = ["lime" if p > 0 else "red" for p in se_pnls]
        se_grades = short_entries["trade_grade"].values if "trade_grade" in short_entries.columns else [""] * len(se_bars)
        fig2.add_trace(go.Scatter(
            x=se_bars, y=se_prices, mode="markers",
            name="SHORT entry",
            marker=dict(symbol="triangle-down", size=10,
                        color=se_colors,
                        line=dict(color="white", width=1)),
            text=[f"Bar={b}<br>PnL=${p:.2f}<br>Grade={g}" for b, p, g in zip(se_bars, se_pnls, se_grades)],
            hoverinfo="text",
        ), row=1, col=1)

        # EMA cross events
        if "ema_cross_bull" in df_chart.columns and "ema_cross_bear" in df_chart.columns:
            bull_cross_x = [i for i in x if df_chart["ema_cross_bull"].iloc[i]]
            bull_cross_y = [df_chart["close"].iloc[i] for i in bull_cross_x]
            fig2.add_trace(go.Scatter(
                x=bull_cross_x, y=bull_cross_y, mode="markers",
                name="55/89 Bull Cross",
                marker=dict(symbol="star", size=14, color="cyan"),
            ), row=1, col=1)

            bear_cross_x = [i for i in x if df_chart["ema_cross_bear"].iloc[i]]
            bear_cross_y = [df_chart["close"].iloc[i] for i in bear_cross_x]
            fig2.add_trace(go.Scatter(
                x=bear_cross_x, y=bear_cross_y, mode="markers",
                name="55/89 Bear Cross",
                marker=dict(symbol="star", size=14, color="orange"),
            ), row=1, col=1)

        # EMA delta subplot
        if "ema_delta" in df_chart.columns:
            delta = df_chart["ema_delta"].values
            fig2.add_trace(go.Scatter(x=x, y=delta, name="EMA Delta",
                                      fill="tozeroy",
                                      line=dict(color="yellow", width=1)),
                           row=2, col=1)
            fig2.add_hline(y=0, line_dash="dash", line_color="white", row=2, col=1)

            # Mark bars where entries occurred with wrong delta sign
            if not all_contexts.empty:
                fart_ctx = all_contexts[all_contexts["symbol"] == "FARTCOINUSDT"]
                ct_bars = fart_ctx[(fart_ctx["counter_trend"] == True) & (fart_ctx["entry_bar"] < CHART_BARS)]["entry_bar"].values
                ct_delta = [delta[b] if b < len(delta) else np.nan for b in ct_bars]
                fig2.add_trace(go.Scatter(
                    x=ct_bars, y=ct_delta, mode="markers",
                    name="Counter-Trend Entry",
                    marker=dict(symbol="x", size=12, color="magenta", line=dict(color="white", width=2)),
                ), row=2, col=1)

        # Stoch 9 D subplot
        if "stoch_9_d" in df_chart.columns:
            fig2.add_trace(go.Scatter(x=x, y=df_chart["stoch_9_d"].values, name="Stoch 9 D",
                                      line=dict(color="#00CED1", width=1.2)),
                           row=3, col=1)
            fig2.add_hline(y=20, line_dash="dot", line_color="lime", row=3, col=1)
            fig2.add_hline(y=80, line_dash="dot", line_color="red", row=3, col=1)

        fig2.update_layout(
            title="FARTCOINUSDT — 55/89 Cross Timing vs Entry Signals",
            template="plotly_dark",
            height=900,
            legend=dict(font=dict(size=10)),
        )
        out2 = RESULTS_DIR / f"chart_fartcoin_ema_cross_{_VER}.html"
        fig2.write_html(str(out2))
        log.info("Chart 2 saved -> %s", out2)

    # ── Chart 3: ATR% profile per coin ────────────────────────────────────────
    if not all_contexts.empty and "atr_pct_of_price" in all_contexts.columns:
        fig3 = go.Figure()
        for sym in neg_coins:
            cd = all_contexts[all_contexts["symbol"] == sym]["atr_pct_of_price"].dropna()
            if len(cd) == 0:
                continue
            fig3.add_trace(go.Box(y=cd.values, name=sym, boxmean=True))
        fig3.update_layout(
            title="ATR% of Price Distribution — Negative Coins (higher = more volatile entries)",
            yaxis_title="ATR / Entry Price (%)",
            template="plotly_dark",
            height=500,
        )
        out3 = RESULTS_DIR / f"chart_atr_profile_{_VER}.html"
        fig3.write_html(str(out3))
        log.info("Chart 3 saved -> %s", out3)

    # ── Chart 4: PnL by failure mode scatter (FARTCOIN) ───────────────────────
    if not all_contexts.empty:
        fart_ctx = all_contexts[(all_contexts["symbol"] == "FARTCOINUSDT") & ("failure_modes" in all_contexts.columns)].copy()
        if not fart_ctx.empty and "failure_modes" in fart_ctx.columns:
            # Explode to one row per failure mode
            rows = []
            for _, r in fart_ctx.iterrows():
                modes = r["failure_modes"] if isinstance(r["failure_modes"], list) else ["OTHER"]
                for mo in modes:
                    rows.append({"entry_bar": r["entry_bar"], "pnl": r["pnl"],
                                 "failure_mode": mo, "grade": r["trade_grade"],
                                 "bars_held": r["bars_held"], "exit_reason": r["exit_reason"]})
            exploded = pd.DataFrame(rows)
            fig4 = px.scatter(
                exploded, x="entry_bar", y="pnl",
                color="failure_mode",
                symbol="exit_reason",
                hover_data=["grade", "bars_held", "failure_mode"],
                title="FARTCOINUSDT — PnL by Entry Bar, Colored by Failure Mode",
                template="plotly_dark",
                height=550,
            )
            fig4.add_hline(y=0, line_dash="dash", line_color="white")
            out4 = RESULTS_DIR / f"chart_fartcoin_pnl_scatter_{_VER}.html"
            fig4.write_html(str(out4))
            log.info("Chart 4 saved -> %s", out4)

    # ── Chart 5: Win rate by grade across all negative coins ──────────────────
    if not all_contexts.empty and "trade_grade" in all_contexts.columns:
        neg_df = all_contexts[all_contexts["symbol"].isin(neg_coins)].copy()
        neg_df["win"] = neg_df["pnl"] > 0
        grade_wr = neg_df.groupby(["symbol", "trade_grade"])["win"].mean().reset_index()
        grade_wr.columns = ["symbol", "grade", "win_rate"]
        grade_wr["win_rate_pct"] = grade_wr["win_rate"] * 100

        fig5 = px.bar(
            grade_wr, x="symbol", y="win_rate_pct",
            color="grade",
            barmode="group",
            title="Win Rate by Trade Grade — Negative Coins (shows Grade-C underperformance)",
            template="plotly_dark",
            height=500,
            labels={"win_rate_pct": "Win Rate %"},
        )
        fig5.add_hline(y=50, line_dash="dash", line_color="white", annotation_text="50%")
        out5 = RESULTS_DIR / f"chart_grade_winrate_{_VER}.html"
        fig5.write_html(str(out5))
        log.info("Chart 5 saved -> %s", out5)

    # ── Chart 6: Phase exit distribution per coin ─────────────────────────────
    phase_rows = []
    for sym, m in {s: all_results[s]["metrics"] for s in neg_coins if s in all_results}.items():
        phase_rows.append({"symbol": sym, "phase": "Phase1 SL", "count": m["phase1_exits"]})
        phase_rows.append({"symbol": sym, "phase": "Phase2 SL", "count": m["phase2_exits"]})
        phase_rows.append({"symbol": sym, "phase": "Phase3 SL", "count": m["phase3_exits"]})
        phase_rows.append({"symbol": sym, "phase": "Phase4 TP", "count": m.get("phase4_exits", 0)})

    if phase_rows:
        phase_df = pd.DataFrame(phase_rows)
        fig6 = px.bar(
            phase_df, x="symbol", y="count", color="phase", barmode="stack",
            title="Phase Exit Distribution — Negative Coins\n(Phase1/2 dominance = trades dying before ratchet)",
            template="plotly_dark",
            height=500,
        )
        out6 = RESULTS_DIR / f"chart_phase_exits_{_VER}.html"
        fig6.write_html(str(out6))
        log.info("Chart 6 saved -> %s", out6)

    log.info("All charts saved to %s", RESULTS_DIR)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("=== 55/89 Negative Coin Analysis START ===")
    log.info("Coins: %s", COINS)
    log.info("avwap_warmup=%d  sl_mult=%.1f  min_signal_gap=%d",
             AVWAP_WARMUP, PARAMS["sl_mult"], PARAMS["min_signal_gap"])

    # ── Phase 1: Run pipeline on all coins ────────────────────────────────────
    all_results = {}
    for symbol in COINS:
        res = run_coin(symbol)
        if res is not None:
            all_results[symbol] = res

    if not all_results:
        log.error("No results produced — check data directory: %s", DATA_DIR)
        return

    # Portfolio summary
    summary = compute_portfolio_summary(all_results)

    # Negative coins
    neg_coins = [sym for sym, m in summary.items() if m["net_pnl"] < 0]
    log.info("Negative coins: %s", neg_coins)

    # Save per-coin trade CSVs
    all_trade_contexts: list = []

    for sym, res in all_results.items():
        trades_df = res["trades_df"]
        if trades_df.empty:
            continue
        csv_path = RESULTS_DIR / f"trades_5589_{sym}_v{_VER}.csv"
        trades_df.to_csv(str(csv_path), index=False, encoding="utf-8")
        log.info("  Saved trades CSV: %s", csv_path)

    # ── Phase 2: Extract context for negative coins ────────────────────────────
    log.info("Extracting trade contexts for negative coins ...")
    for sym in neg_coins:
        if sym not in all_results:
            continue
        res = all_results[sym]
        ctxs = extract_trade_contexts(sym, res["trades_df"], res["df_sig"])
        all_trade_contexts.extend(ctxs)
        log.info("  %s: %d trade contexts extracted", sym, len(ctxs))

    if not all_trade_contexts:
        log.warning("No trade contexts — negative coins may have no trades")
        return

    all_ctx_df = pd.DataFrame(all_trade_contexts)

    # ── Phase 3: Failure mode classification ──────────────────────────────────
    log.info("Classifying failure modes ...")
    atr_75th = all_ctx_df["atr_pct_of_price"].quantile(0.75) if "atr_pct_of_price" in all_ctx_df.columns else np.nan
    log.info("  ATR 75th-percentile threshold: %.4f%%", atr_75th if not np.isnan(atr_75th) else -1)

    all_ctx_df["failure_modes"] = all_ctx_df.apply(
        lambda row: classify_failure_modes(row, atr_75th), axis=1
    )

    # ── Phase 5: Save detailed CSV ────────────────────────────────────────────
    csv_path = RESULTS_DIR / f"trade_contexts_negative_5589_v{_VER}.csv"
    # Convert list column to string for CSV
    save_df = all_ctx_df.copy()
    save_df["failure_modes"] = save_df["failure_modes"].apply(lambda x: "|".join(x) if isinstance(x, list) else str(x))
    save_df.to_csv(str(csv_path), index=False, encoding="utf-8")
    log.info("Trade contexts CSV saved -> %s", csv_path)

    # ── Phase 4: Text report ──────────────────────────────────────────────────
    fart_ctx = all_ctx_df[all_ctx_df["symbol"] == "FARTCOINUSDT"].copy() if "FARTCOINUSDT" in neg_coins else pd.DataFrame()

    report_path = RESULTS_DIR / f"negative_coins_analysis_5589_v{_VER}.txt"
    print_text_report(summary, neg_coins, all_ctx_df, fart_ctx, report_path)

    # FARTCOIN specific text
    if not fart_ctx.empty:
        fart_report_path = RESULTS_DIR / f"fartcoin_deep_dive_5589_v{_VER}.txt"
        # Write a focused FARTCOIN-only report
        fart_summary = [f"FARTCOINUSDT Deep Dive — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
        fart_summary.append(f"Total trades: {len(fart_ctx)}")
        if "pnl" in fart_ctx.columns:
            fart_summary.append(f"Net PnL: ${fart_ctx['pnl'].sum():.2f}")
            fart_summary.append(f"Win Rate: {(fart_ctx['pnl'] > 0).mean()*100:.1f}%")
        fart_summary.append("\nAll trade failure modes:")
        for _, r in fart_ctx.iterrows():
            fart_summary.append(
                f"  Bar={r['entry_bar']:>6}  {r['direction']}  PnL=${r['pnl']:>8.2f}  "
                f"{r['exit_reason']:<15}  Grade={r['trade_grade']}  "
                f"Modes={r.get('failure_modes', [])}"
            )
        fart_report_path.write_text("\n".join(fart_summary), encoding="utf-8")
        log.info("FARTCOIN deep dive saved -> %s", fart_report_path)

    # ── Phase 6: Charts ────────────────────────────────────────────────────────
    log.info("Building Plotly charts ...")
    build_charts(all_results, all_ctx_df, neg_coins)

    log.info("=== ANALYSIS COMPLETE ===")
    log.info("Results directory: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()

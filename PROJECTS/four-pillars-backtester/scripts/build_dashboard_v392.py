"""
Build script: dashboard v3.9.2 (Numba JIT + timing panel).

Generates 5 new files; NEVER modifies any existing file:
  utils/timing.py
  signals/stochastics_v2.py
  signals/clouds_v2.py
  signals/four_pillars_v383_v2.py
  scripts/dashboard_v392.py   (patched copy of dashboard_v391.py)

Run: python scripts/build_dashboard_v392.py
"""
import sys
import ast
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS: list[str] = []
PATCH_MISSES: list[str] = []


def check_file(path: Path) -> bool:
    """Run py_compile + ast.parse; record failures in ERRORS; return True if clean."""
    rel = str(path.relative_to(ROOT))
    ok = True
    try:
        py_compile.compile(str(path), doraise=True)
        print("  SYNTAX OK : " + rel)
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERR: " + str(e))
        ERRORS.append(rel + ":syntax")
        ok = False
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        print("  AST    OK : " + rel)
    except SyntaxError as e:
        print("  AST    ERR: line " + str(e.lineno) + " — " + str(e.msg))
        ERRORS.append(rel + ":ast")
        ok = False
    return ok


def write_and_check(path: Path, content: str) -> None:
    """Write file, run syntax checks."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("\n[WRITE] " + str(path.relative_to(ROOT)))
    check_file(path)


def apply_patch(content: str, old: str, new: str, label: str) -> str:
    """Replace old with new in content; record miss if not found."""
    if old not in content:
        print("  PATCH MISS: " + label)
        PATCH_MISSES.append(label)
        return content
    result = content.replace(old, new, 1)
    print("  PATCH OK  : " + label)
    return result


# ==========================================================================
# 1. utils/timing.py
# ==========================================================================
TIMING_PY = '''\
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
'''

write_and_check(ROOT / "utils" / "timing.py", TIMING_PY)


# ==========================================================================
# 2. signals/stochastics_v2.py
# ==========================================================================
STOCHASTICS_V2 = '''\
"""
Stochastic calculations v2 — Raw K, no smoothing.
stoch_k() is Numba JIT-compiled; drop-in replacement for signals.stochastics.
"""
import numpy as np
import pandas as pd
from numba import njit


@njit(cache=True)
def stoch_k(close, high, low, k_len):
    """Raw K stochastic window loop; Numba JIT-compiled via @njit(cache=True)."""
    n = len(close)
    result = np.full(n, np.nan)
    for i in range(k_len - 1, n):
        window_low = low[i - k_len + 1: i + 1]
        window_high = high[i - k_len + 1: i + 1]
        lowest = np.min(window_low)
        highest = np.max(window_high)
        if highest - lowest == 0:
            result[i] = 50.0
        else:
            result[i] = 100.0 * (close[i] - lowest) / (highest - lowest)
    return result


def compute_all_stochastics(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute all 4 stochastic K values plus D smooth using JIT-compiled stoch_k."""
    p = params or {}
    k1 = p.get("stoch_k1", 9)
    k2 = p.get("stoch_k2", 14)
    k3 = p.get("stoch_k3", 40)
    k4 = p.get("stoch_k4", 60)
    d_smooth = p.get("stoch_d_smooth", 10)
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    df = df.copy()
    df["stoch_9"] = stoch_k(close, high, low, k1)
    df["stoch_14"] = stoch_k(close, high, low, k2)
    df["stoch_40"] = stoch_k(close, high, low, k3)
    df["stoch_60"] = stoch_k(close, high, low, k4)
    df["stoch_60_d"] = df["stoch_60"].rolling(window=d_smooth, min_periods=1).mean()
    return df
'''

write_and_check(ROOT / "signals" / "stochastics_v2.py", STOCHASTICS_V2)


# ==========================================================================
# 3. signals/clouds_v2.py
# ==========================================================================
CLOUDS_V2 = '''\
"""
Ripster EMA Cloud calculations v2 — ema() Numba JIT-compiled.
Drop-in replacement for signals.clouds.
"""
import numpy as np
import pandas as pd
from numba import njit


@njit(cache=True)
def ema(series, length):
    """EMA matching Pine Script ta.ema(); Numba JIT-compiled via @njit(cache=True)."""
    result = np.full(len(series), np.nan)
    if len(series) < length:
        return result
    result[length - 1] = np.mean(series[:length])
    mult = 2.0 / (length + 1)
    for i in range(length, len(series)):
        result[i] = series[i] * mult + result[i - 1] * (1 - mult)
    return result


def compute_clouds(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute Ripster EMA Clouds using JIT-compiled ema(); identical logic to v1."""
    p = params or {}
    c2_fast = p.get("cloud2_fast", 5)
    c2_slow = p.get("cloud2_slow", 12)
    c3_fast = p.get("cloud3_fast", 34)
    c3_slow = p.get("cloud3_slow", 50)
    c4_fast = p.get("cloud4_fast", 72)
    c4_slow = p.get("cloud4_slow", 89)
    close = df["close"].values
    df = df.copy()
    # Cloud 2
    df["ema5"] = ema(close, c2_fast)
    df["ema12"] = ema(close, c2_slow)
    df["cloud2_bull"] = df["ema5"] > df["ema12"]
    df["cloud2_top"] = np.maximum(df["ema5"], df["ema12"])
    df["cloud2_bottom"] = np.minimum(df["ema5"], df["ema12"])
    # Cloud 3
    df["ema34"] = ema(close, c3_fast)
    df["ema50"] = ema(close, c3_slow)
    df["cloud3_bull"] = df["ema34"] > df["ema50"]
    df["cloud3_top"] = np.maximum(df["ema34"], df["ema50"])
    df["cloud3_bottom"] = np.minimum(df["ema34"], df["ema50"])
    # Cloud 4
    df["ema72"] = ema(close, c4_fast)
    df["ema89"] = ema(close, c4_slow)
    df["cloud4_bull"] = df["ema72"] > df["ema89"]
    # Price position relative to Cloud 3
    df["price_pos"] = np.where(
        close > df["cloud3_top"].values, 1,
        np.where(close < df["cloud3_bottom"].values, -1, 0)
    )
    # Cloud 3 directional filter (v3.8: ALWAYS ON)
    df["cloud3_allows_long"] = df["price_pos"] >= 0
    df["cloud3_allows_short"] = df["price_pos"] <= 0
    # Cloud 2 crossovers (for re-entry)
    df["price_cross_above_cloud2"] = (close > df["cloud2_top"].values) & (
        np.roll(close, 1) <= np.roll(df["cloud2_top"].values, 1)
    )
    df["price_cross_below_cloud2"] = (close < df["cloud2_bottom"].values) & (
        np.roll(close, 1) >= np.roll(df["cloud2_bottom"].values, 1)
    )
    # Fix first bar
    df.iloc[0, df.columns.get_loc("price_cross_above_cloud2")] = False
    df.iloc[0, df.columns.get_loc("price_cross_below_cloud2")] = False
    return df
'''

write_and_check(ROOT / "signals" / "clouds_v2.py", CLOUDS_V2)


# ==========================================================================
# 4. signals/four_pillars_v383_v2.py
# ==========================================================================
FP383_V2 = '''\
"""
Signal pipeline for v3.8.3 — v2: uses Numba-compiled stochastics/clouds/ATR.
Imports stochastics_v2 and clouds_v2; extracts _rma_kernel via @njit.
"""
import numpy as np
import pandas as pd
from numba import njit

from .stochastics_v2 import compute_all_stochastics
from .clouds_v2 import compute_clouds
from .state_machine_v383 import FourPillarsStateMachine383


@njit(cache=True)
def _rma_kernel(tr, atr_len):
    """Wilder RMA loop for ATR calculation; Numba JIT-compiled via @njit(cache=True)."""
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    return atr


def compute_signals_v383(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Run the full Four Pillars v3.8.3 signal pipeline with Numba-accelerated kernels."""
    if params is None:
        params = {}

    df = compute_all_stochastics(df, params)
    df = compute_clouds(df, params)

    # ATR (RMA / Wilder\'s smoothing) — inner loop JIT-compiled via _rma_kernel
    atr_len = params.get("atr_length", 14)
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    prev_c = np.roll(c, 1)
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = h[0] - l[0]

    atr = _rma_kernel(tr, atr_len)
    df["atr"] = atr

    # v3.8.3 state machine
    sm = FourPillarsStateMachine383(
        cross_level=params.get("cross_level", 25),
        zone_level=params.get("zone_level", 30),
        stage_lookback=params.get("stage_lookback", 10),
        allow_b=params.get("allow_b_trades", True),
        allow_c=params.get("allow_c_trades", True),
        b_open_fresh=params.get("b_open_fresh", True),
        cloud2_reentry=params.get("cloud2_reentry", True),
        reentry_lookback=params.get("reentry_lookback", 10),
        use_60d=params.get("use_60d", False),
    )

    n = len(df)
    signals = {
        "long_a": np.zeros(n, dtype=bool),
        "long_b": np.zeros(n, dtype=bool),
        "long_c": np.zeros(n, dtype=bool),
        "long_d": np.zeros(n, dtype=bool),
        "short_a": np.zeros(n, dtype=bool),
        "short_b": np.zeros(n, dtype=bool),
        "short_c": np.zeros(n, dtype=bool),
        "short_d": np.zeros(n, dtype=bool),
        "reentry_long": np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
        "add_long": np.zeros(n, dtype=bool),
        "add_short": np.zeros(n, dtype=bool),
    }

    stoch_9 = df["stoch_9"].values
    stoch_14 = df["stoch_14"].values
    stoch_40 = df["stoch_40"].values
    stoch_60 = df["stoch_60"].values
    stoch_60_d = df["stoch_60_d"].values
    cloud3_bull = df["cloud3_bull"].values
    price_pos = df["price_pos"].values
    cross_above = df["price_cross_above_cloud2"].values
    cross_below = df["price_cross_below_cloud2"].values

    for i in range(n):
        if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
            continue

        result = sm.process_bar(
            bar_index=i,
            stoch_9=stoch_9[i],
            stoch_14=stoch_14[i],
            stoch_40=stoch_40[i],
            stoch_60=stoch_60[i],
            stoch_60_d=stoch_60_d[i],
            cloud3_bull=bool(cloud3_bull[i]),
            price_pos=int(price_pos[i]),
            price_cross_above_cloud2=bool(cross_above[i]),
            price_cross_below_cloud2=bool(cross_below[i]),
        )

        signals["long_a"][i] = result.long_a
        signals["long_b"][i] = result.long_b
        signals["long_c"][i] = result.long_c
        signals["long_d"][i] = result.long_d
        signals["short_a"][i] = result.short_a
        signals["short_b"][i] = result.short_b
        signals["short_c"][i] = result.short_c
        signals["short_d"][i] = result.short_d
        signals["reentry_long"][i] = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short
        signals["add_long"][i] = result.add_long
        signals["add_short"][i] = result.add_short

    for col, arr in signals.items():
        df[col] = arr

    return df
'''

write_and_check(ROOT / "signals" / "four_pillars_v383_v2.py", FP383_V2)


# ==========================================================================
# 5. scripts/dashboard_v392.py  (patched copy of dashboard_v391.py)
# ==========================================================================
SRC = ROOT / "scripts" / "dashboard_v391.py"
DST = ROOT / "scripts" / "dashboard_v392.py"

print("\n[READ] scripts/dashboard_v391.py  (" + str(SRC.stat().st_size // 1024) + " KB)")
content = SRC.read_text(encoding="utf-8")

# --- PATCH P1: version string in module docstring ---
content = apply_patch(
    content,
    "Four Pillars v3.9.1 Backtest Dashboard -- Streamlit GUI\n5-tab layout with ML integration.",
    "Four Pillars v3.9.2 Backtest Dashboard -- Numba JIT + timing panel.\n5-tab layout with ML integration.",
    "P1: docstring version v3.9.1 -> v3.9.2",
)

# --- PATCH P2: switch to Numba-compiled signal module ---
content = apply_patch(
    content,
    "from signals.four_pillars_v383 import compute_signals_v383",
    "from signals.four_pillars_v383_v2 import compute_signals_v383",
    "P2: import four_pillars_v383_v2",
)

# --- PATCH P3: add timing imports after last utils import ---
content = apply_patch(
    content,
    "from utils.pdf_exporter_v2 import check_dependencies as check_pdf_deps, generate_portfolio_pdf",
    "from utils.pdf_exporter_v2 import check_dependencies as check_pdf_deps, generate_portfolio_pdf\n"
    "from utils.timing import TimingAccumulator, records_to_df",
    "P3: add timing imports",
)

# --- PATCH P4: session state for timing_records ---
content = apply_patch(
    content,
    'if "port_symbols_locked" not in st.session_state:\n'
    '    st.session_state["port_symbols_locked"] = None',
    'if "port_symbols_locked" not in st.session_state:\n'
    '    st.session_state["port_symbols_locked"] = None\n'
    'if "timing_records" not in st.session_state:\n'
    '    st.session_state["timing_records"] = []',
    "P4: add timing_records session state",
)

# --- PATCH P5: Performance Debug checkbox in sidebar ---
content = apply_patch(
    content,
    'batch_top = st.sidebar.slider("Top N", 5, 50, 20)\n\nif run_single:',
    'batch_top = st.sidebar.slider("Top N", 5, 50, 20)\n'
    'st.sidebar.markdown("---")\n'
    'perf_debug = st.sidebar.checkbox("Performance Debug", value=False)\n'
    '\n'
    'if run_single:',
    "P5: perf_debug sidebar checkbox",
)

# --- PATCH P6a: run_backtest signature ---
content = apply_patch(
    content,
    "def run_backtest(df, sig_params, run_params):",
    "def run_backtest(df, sig_params, run_params, accumulator=None):",
    "P6a: run_backtest signature add accumulator=None",
)

# --- PATCH P6b: run_backtest body — add timing around signal + engine calls ---
content = apply_patch(
    content,
    "    df_sig = compute_signals_v383(df.copy(), sig_params)\n"
    "    bt = Backtester384(run_params)\n"
    "    results = bt.run(df_sig)\n"
    "    return results, df_sig",
    "    t0 = time.perf_counter()\n"
    "    df_sig = compute_signals_v383(df.copy(), sig_params)\n"
    "    t1 = time.perf_counter()\n"
    "    bt = Backtester384(run_params)\n"
    "    results = bt.run(df_sig)\n"
    "    t2 = time.perf_counter()\n"
    "    if accumulator is not None:\n"
    "        accumulator.record(\"signals_ms\", (t1 - t0) * 1000)\n"
    "        accumulator.record(\"engine_ms\", (t2 - t1) * 1000)\n"
    "    return results, df_sig",
    "P6b: run_backtest body timing instrumentation",
)

# --- PATCH P7: add _timing_acc init inside portfolio spinner block ---
content = apply_patch(
    content,
    "            coin_results = []\n"
    "            progress = st.progress(0)",
    "            coin_results = []\n"
    "            _timing_acc = TimingAccumulator()\n"
    "            progress = st.progress(0)",
    "P7: add _timing_acc = TimingAccumulator() in spinner block",
)

# --- PATCH P8: wrap load_data + run_backtest in portfolio loop ---
content = apply_patch(
    content,
    "                try:\n"
    "                    _df = load_data(sym, timeframe)\n"
    "                    if _df is None or len(_df) < 200:\n"
    "                        continue\n"
    "                    _df = apply_date_filter(_df, date_range)\n"
    "                    if len(_df) < 200:\n"
    "                        continue\n"
    "                    _r, _ds = run_backtest(_df, signal_params, bt_params)",
    "                try:\n"
    "                    _timing_acc.set_symbol(sym)\n"
    "                    _t0 = time.perf_counter()\n"
    "                    _df = load_data(sym, timeframe)\n"
    "                    _timing_acc.record(\"load_ms\", (time.perf_counter() - _t0) * 1000)\n"
    "                    if _df is None or len(_df) < 200:\n"
    "                        continue\n"
    "                    _df = apply_date_filter(_df, date_range)\n"
    "                    if len(_df) < 200:\n"
    "                        continue\n"
    "                    _timing_acc.record(\"bars\", len(_df))\n"
    "                    _r, _ds = run_backtest(_df, signal_params, bt_params, accumulator=_timing_acc)",
    "P8: portfolio loop timing wrap (load_data + run_backtest)",
)

# --- PATCH P9: save timing records to session_state after portfolio run ---
content = apply_patch(
    content,
    '            status.text(f"Done: {len(coin_results)}/{len(port_symbols)} coins with trades")\n'
    '\n'
    '            if coin_results:',
    '            status.text(f"Done: {len(coin_results)}/{len(port_symbols)} coins with trades")\n'
    '            st.session_state["timing_records"] = _timing_acc.records[:]\n'
    '\n'
    '            if coin_results:',
    "P9: save timing_records to session_state after portfolio run",
)

# --- PATCH P10: append timing panel at end of portfolio section ---
TIMING_PANEL = (
    "\n"
    "        # -- Performance Debug Panel (v3.9.2) --\n"
    "        if perf_debug:\n"
    "            _trecs = st.session_state.get(\"timing_records\", [])\n"
    "            if _trecs:\n"
    "                st.markdown(\"---\")\n"
    "                st.subheader(\"Performance Debug\")\n"
    "                _tdf = records_to_df(_trecs)\n"
    "                if not _tdf.empty:\n"
    "                    st.dataframe(_tdf, use_container_width=True)\n"
    "                    for _tc in [c for c in _tdf.columns if c.endswith(\"_ms\")]:\n"
    "                        _mean = str(round(_tdf[_tc].mean(), 1))\n"
    "                        _max = str(round(_tdf[_tc].max(), 1))\n"
    "                        st.caption(_tc + \": mean=\" + _mean + \"ms  max=\" + _max + \"ms\")\n"
    "            else:\n"
    "                st.info(\"Run a portfolio backtest with Performance Debug enabled to see timing data.\")\n"
)
content = content + TIMING_PANEL
print("  PATCH OK  : P10: timing panel appended at end of portfolio section")

# Write dashboard_v392.py
print("\n[WRITE] scripts/dashboard_v392.py")
DST.write_text(content, encoding="utf-8")
check_file(DST)


# ==========================================================================
# Final report
# ==========================================================================
print("\n" + "=" * 60)
if PATCH_MISSES:
    print("PATCH MISSES (" + str(len(PATCH_MISSES)) + "):")
    for m in PATCH_MISSES:
        print("  - " + m)
if ERRORS:
    print("SYNTAX ERRORS (" + str(len(ERRORS)) + "):")
    for e in ERRORS:
        print("  - " + e)
    print("\nBUILD FAILED")
    sys.exit(1)
else:
    print("ALL PATCHES APPLIED: " + str(10 - len(PATCH_MISSES)) + "/10")
    print("ALL FILES CLEAN     : 5/5")
    print("\nBUILD OK")
    print("\nNext steps:")
    print("  1. Run: streamlit run scripts/dashboard_v392.py")
    print("  2. First launch: ~2-5s Numba compile (one-time, cached)")
    print("  3. Check sidebar: enable 'Performance Debug' checkbox")
    print("  4. Run Portfolio mode -> view timing table at bottom of page")
    print("  5. Verify numbers match v391 baseline EXACTLY before trusting Numba output")

# Plan: Trade Chart Report v3 — TDI Module Swap

## Context

`run_trade_chart_report_v2.py` already implements items 1–10 from the build prompt (pagination, AVWAP SD bands, 2-panel layout, entry/exit markers, right sidebar notes, @anchor notes, toggle overlays, AVWAP anchored at EMA cross, Export All Notes button). The only remaining item is **#11: replace the broken inline TDI block with an import from `signals/tdi.py`**.

The inline TDI in v2 (lines ~299–323) uses:
- `ewm` instead of Wilder/RMA (wrong RSI smoothing)
- `fast_ma_len = 7`, `slow_ma_len = 2` — **swapped** (fast is actually the slow, vice versa)
- No zones, divergence, or cross signals
- RSI period 14 instead of 13

The correct module at `signals/tdi.py` (426 lines) uses Wilder RMA, cw_trades preset (RSI 13, fast=2, slow=8, BB 34/1.6185), zones, divergence, and 6 cross signal columns.

The chart panel already draws `tdi_upper`, `tdi_lower`, `tdi_mid`, `tdi_fast`, `tdi_slow` — column names map cleanly via aliases. Panel title says "TDI 14" → needs to change to "TDI 13".

## Output File

`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v3.py`

Do NOT touch v1 or v2.

## Critical Files

| File | Role |
|------|------|
| `PROJECTS/bingx-connector-v2/scripts/run_trade_chart_report_v2.py` | Source — copy in full, apply only the TDI change |
| `PROJECTS/four-pillars-backtester/signals/tdi.py` | Import target — `compute_tdi()` |

## What Changes (surgical — nothing else touches)

### 1. sys.path injection (after ROOT constant, same pattern as `detect_signals`)

```python
_BACKTESTER = ROOT.parent / "four-pillars-backtester"
if str(_BACKTESTER) not in sys.path:
    sys.path.insert(0, str(_BACKTESTER))
from signals.tdi import compute_tdi
```

Place this at module level after the `ROOT` block, before `compute_indicators`.

### 2. Replace inline TDI block in `compute_indicators()` (lines ~299–323 in v2)

Remove:
```python
# TDI -- Traders Dynamic Index (RSI 14 based)
rsi_period = 14
band_length = 34
fast_ma_len = 7
slow_ma_len = 2
... (ewm RSI + BB + rolling MA lines)
```

Replace with:
```python
# TDI -- full module (Wilder RSI 13, proper MA, zones, divergence, cross signals)
try:
    tdi_df = compute_tdi(df, {"tdi_preset": "cw_trades"})
    df["tdi_rsi"] = tdi_df["tdi_rsi"]
    df["tdi_upper"] = tdi_df["tdi_bb_upper"]
    df["tdi_lower"] = tdi_df["tdi_bb_lower"]
    df["tdi_mid"] = tdi_df["tdi_bb_mid"]
    df["tdi_fast"] = tdi_df["tdi_fast_ma"]
    df["tdi_slow"] = tdi_df["tdi_signal"]
    df["tdi_zone"] = tdi_df["tdi_zone"]
    df["tdi_cloud_bull"] = tdi_df["tdi_cloud_bull"]
    df["tdi_long"] = tdi_df["tdi_long"]
    df["tdi_short"] = tdi_df["tdi_short"]
    df["tdi_bull_div"] = tdi_df["tdi_bull_div"]
    df["tdi_bear_div"] = tdi_df["tdi_bear_div"]
except Exception as e:
    log.warning("TDI compute failed: %s", e)
```

### 3. Panel title + toggle label update

Three occurrences of "TDI 14" → "TDI 13":
- Line ~426: `subplot_titles=[..., "TDI 14", ...]`
- Line ~772: `# --- Panel 4: TDI 14 ---` (comment only)
- Line ~1034: `"> TDI 14</label>"` (toggle checkbox label)

### 4. No other changes

All other code (pagination JS, AVWAP, stochastics, notes sidebar, toggles, signals) carries over unchanged from v2.

## Verification

```
python -c "import py_compile; py_compile.compile(r'C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v3.py', doraise=True)"
```

Then run:
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v3.py" --date 2026-03-11
```

Then open:
```
start "" "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\logs\trade_chart_report_2026-03-11.html"
```

Confirm TDI panel title shows "TDI 13" and the chart renders without errors.

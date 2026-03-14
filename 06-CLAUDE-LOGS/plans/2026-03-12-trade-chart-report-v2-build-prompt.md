# Build Prompt: Trade Chart Report v2 — Interactive Upgrade

## Context

You are modifying an existing trade chart report tool at:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report.py`

This is a 748-line Plotly-based HTML report generator that reads `trades_all.csv` (193 live trades from BingX bot), fetches 5m klines from BingX API, computes indicators (EMA 55/89, AVWAP, stochastics 9/14/40/60), and generates a single-file interactive HTML report.

**v1 works and has been runtime-tested.** Do NOT break what works. All changes are additive or replace specific components.

## HARD RULES

1. Load the Python skill (`/python`) before writing any code.
2. Output as a versioned file: `run_trade_chart_report_v2.py` — do NOT overwrite v1.
3. `py_compile` MUST pass before delivering.
4. Do NOT execute the script — write the build, state the run command, stop.
5. Single-file HTML output (all JS/CSS inline, only Plotly CDN external).
6. Keep all existing functionality that is not explicitly changed below.

## Changes Required

### 1. ONE TRADE PER PAGE (pagination)

Currently all trades render on one scrollable page. Change to:
- Each trade gets its own full-screen view (like a slide).
- Navigation: left/right arrows, keyboard arrows, or trade sidebar click.
- Trade sidebar stays visible on all pages (left panel, same as current).
- Clicking a trade in sidebar jumps to that trade's page.
- Current trade highlighted in sidebar.

### 2. AVWAP STANDARD DEVIATION BANDS

The AVWAP white dashed line exists but has no standard deviation bands. Add:
- 1 SD and 2 SD bands above and below AVWAP (4 lines total).
- SD calculated from typical price deviations from AVWAP (rolling from anchor point).
- Band colors: semi-transparent white or light blue, thinner than AVWAP line.
- These must be toggleable (see item 8).

### 3. REMOVE VOLUME BARS — Replace with more stoch history

Currently Panel 3 is volume bars. Remove it.
- Expand stochastic panel to fill that space.
- The stoch 40 and 60 need more historical bars for context. Currently the kline window is:
  - `start_ms = entry_ms - (60 * candle_ms)` (60 bars before entry = 5 hours)
  - For stoch 40 and 60 to have meaningful history, increase to `entry_ms - (120 * candle_ms)` (120 bars = 10 hours before entry).
- Change `make_subplots` from 3 rows to 2 rows: price panel (60%) + stochastic panel (40%).

### 4. ENTRY/EXIT ARROW MARKERS

Add arrow markers on the price chart:
- **LONG entry**: green triangle-up BELOW the entry candle's low.
- **SHORT entry**: red triangle-down ABOVE the entry candle's high.
- **Exit**: gray "x" marker at exit price on exit candle.
- Use `go.Scatter` with `mode="markers"` and appropriate `marker_symbol`.

### 5. TIMEFRAME LABEL

Add "5m" timeframe label to the chart title or as a visible annotation on the price panel (top-right corner). Format: `5m | KAITO-USDT | LONG | B | ...`

### 6. NOTES PANEL — Right sidebar

Replace the current textarea below each chart with a fixed right-side notes panel:
- Fixed position on the right side of the screen (similar to how TRADES sidebar is on the left).
- Width: ~280px.
- Layout: left sidebar (trades, 220px) | main chart (flexible) | right sidebar (notes, 280px).
- Notes panel shows the note area for the CURRENT trade (changes when navigating trades).
- Same localStorage persistence as current.

### 7. STRUCTURED NOTES with @anchors

The notes textarea should support structured annotation with `@` anchors:
- User types `@stoch9`, `@stoch60`, `@ema55`, `@avwap`, `@entry`, `@exit`, `@trend`, `@grade`, etc.
- These anchors are visually highlighted in the textarea (or a preview below it) — colored spans matching the indicator colors:
  - `@stoch9` = cyan (#00BFFF)
  - `@stoch14` = orchid (#DA70D6)
  - `@stoch40` = gold (#FFD700)
  - `@stoch60` = tomato (#FF6347)
  - `@ema55` = orange (#FF8C00)
  - `@ema89` = dodgerblue (#1E90FF)
  - `@avwap` = white (#FFFFFF)
  - `@entry` = green (#00ff7f)
  - `@exit` = gray (#AAAAAA)
  - `@trend` = yellow
  - `@grade` = cyan
- Implementation: use a `contenteditable` div or a textarea + preview div below it. The preview renders the note text with colored `@anchor` spans. The raw text (with @anchors) is what gets saved to localStorage.
- When I later paste these notes to Claude, the @anchors make it immediately clear which indicator I'm referring to.

### 8. TOGGLE OVERLAYS per chart

Add toggle buttons/checkboxes in the notes panel or a small toolbar:
- Toggle AVWAP + bands on/off
- Toggle EMA 55/89 on/off
- Toggle Ripster Clouds on/off (not currently drawn — this is for future, just add the toggle infrastructure)
- Toggle entry/exit markers on/off
- Toggles apply to the CURRENT trade's chart only.
- Implementation: use Plotly's `restyle` to show/hide traces by name.
- Each toggle remembers its state per trade (localStorage).

### 9. AVWAP ANCHOR POINT

Currently AVWAP is anchored at entry candle. This is wrong for context — the user wants to see AVWAP anchored at a meaningful prior point. Change to:
- Anchor at the **last EMA 55/89 cross** before the entry candle.
- Scan backwards from entry to find the bar where EMA55 and EMA89 crossed (sign change of ema55-ema89).
- If no cross found in the kline window, fall back to anchoring at the first bar of the window.
- The AVWAP + SD bands all start from this anchor point.

### 10. EXPORT ALL NOTES button

Add a "Save All Notes" button (top of notes panel or summary bar) that:
- Collects all notes for the current report date.
- Generates a downloadable `.md` file with format:
```
# Trade Notes — 2026-03-11

## Trade #1 — MUBARAK-USDT | LONG | $-0.1151
@entry: ...
@stoch9: ...
notes text here

## Trade #2 — EIGEN-USDT | LONG | $-0.2326
...
```
- Uses `Blob` + `URL.createObjectURL` for client-side download.

### 11. TDI — Use proper signals.tdi module (REPLACE inline computation)

The current v2 has an inline TDI that is WRONG:
- Swapped fast/slow MA lengths (fast=7, slow=2 — should be fast=2, slow=8 for cw_trades preset)
- Uses `ewm` for RSI instead of Wilder smoothing (RMA)
- No zone classification, no divergence, no cross signals, no cloud fill

**Replace the entire inline TDI block** (lines ~295-319 in v2) with an import from:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\tdi.py`

Integration:
```python
# Add backtester to sys.path (same pattern as detect_signals)
_BACKTESTER = ROOT.parent / "four-pillars-backtester"
if str(_BACKTESTER) not in sys.path:
    sys.path.insert(0, str(_BACKTESTER))
from signals.tdi import compute_tdi
```

Then in `compute_indicators()`, replace the inline RSI/BB/MA block with:
```python
# TDI -- full module (Wilder RSI, BB on RSI, fast/slow MA, zones, divergence, cross signals)
try:
    tdi_df = compute_tdi(df, {"tdi_preset": "cw_trades"})
    # Map to chart column names
    df["tdi_rsi"] = tdi_df["tdi_rsi"]
    df["tdi_upper"] = tdi_df["tdi_bb_upper"]
    df["tdi_lower"] = tdi_df["tdi_bb_lower"]
    df["tdi_mid"] = tdi_df["tdi_bb_mid"]
    df["tdi_fast"] = tdi_df["tdi_fast_ma"]
    df["tdi_slow"] = tdi_df["tdi_signal"]
    # Extra columns for future chart annotations
    df["tdi_zone"] = tdi_df["tdi_zone"]
    df["tdi_cloud_bull"] = tdi_df["tdi_cloud_bull"]
    df["tdi_long"] = tdi_df["tdi_long"]
    df["tdi_short"] = tdi_df["tdi_short"]
    df["tdi_bull_div"] = tdi_df["tdi_bull_div"]
    df["tdi_bear_div"] = tdi_df["tdi_bear_div"]
except Exception as e:
    log.warning("TDI compute failed: %s", e)
```

The chart panel (Panel 4 in v2: "TDI 14") stays the same visually — it already draws `tdi_upper`, `tdi_lower`, `tdi_mid`, `tdi_fast`, `tdi_slow`. The column names are mapped above so no chart code changes needed. But the underlying computation is now correct (Wilder RSI, proper MA lengths, cw_trades preset = RSI 13).

Update the panel title from "TDI 14" to "TDI 13" to reflect the cw_trades preset.

**Key differences the new TDI provides:**
| Parameter | Old inline | New signals.tdi (cw_trades) |
|-----------|-----------|---------------------------|
| RSI period | 14 | 13 |
| RSI method | ewm (wrong) | Wilder/RMA (correct) |
| Fast MA | 7 (wrong — this was the slow) | 2 (correct — reactive trade line) |
| Slow MA | 2 (wrong — this was the fast) | 8 (correct — signal line) |
| BB period | 34 | 34 |
| BB std | 1.6185 | 1.6185 |
| Zones | none | 7-zone classification |
| Divergence | none | regular + hidden bull/bear |
| Cross signals | none | 6 cross signal columns |

## File Structure

Input: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report.py` (v1, 748 lines — READ THIS FIRST)
Also read: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v2.py` (v2, already built — this is what you are modifying)
TDI module: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\tdi.py` (426 lines — import from here, do NOT inline)
Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v3.py`

## Run Command

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v3.py" --date 2026-03-11
```

Then open:
```
start "" "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\logs\trade_chart_report_2026-03-11.html"
```

## Summary of Changes

| # | Change | Replaces |
|---|--------|----------|
| 1 | One trade per page (pagination) | Scrollable single page |
| 2 | AVWAP SD bands (1SD, 2SD) | AVWAP line only |
| 3 | Remove volume panel, expand stochs, more history | Volume bar panel |
| 4 | Entry/exit arrow markers on price chart | No markers |
| 5 | "5m" timeframe label | No timeframe shown |
| 6 | Right sidebar notes panel | Textarea below chart |
| 7 | @anchor structured notes with color highlights | Plain textarea |
| 8 | Toggle overlays (AVWAP, EMA, Ripster, markers) | Always-on overlays |
| 9 | AVWAP anchored at last EMA cross (not entry) | Anchored at entry |
| 10 | Export All Notes to .md | No export |
| 11 | TDI from signals.tdi (Wilder RSI 13, proper MA, zones, divergence) | Inline broken TDI (ewm RSI 14, swapped MAs) |

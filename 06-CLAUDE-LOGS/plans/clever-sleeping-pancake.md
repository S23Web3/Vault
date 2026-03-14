# Build Prompt Audit: Trade Chart Report v2

## Context
Auditing the build prompt at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-trade-chart-report-v2-build-prompt.md` against the v1 source at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report.py` (748 lines).

## Audit Results

### Change-by-Change Analysis

**1. One Trade Per Page (pagination)** -- CLEAR
- v1: all trades in scrollable `#main` div with `<section id="trade-N">` anchors
- Sidebar links currently use `href="#trade-N"` scroll anchors -- need to change to JS page navigation
- No issues with spec. Implementation: hide all trade divs except current, update sidebar highlight

**2. AVWAP SD Bands** -- CLEAR, one note
- v1 `compute_indicators()` (line 160-181) computes AVWAP from anchor point forward
- SD calc: accumulate `(tp[i] - avwap[i])^2` from anchor, compute rolling SD = `sqrt(cum_sq_dev / count)`
- Note: SD bands will be very tight near the anchor and widen over time -- this is correct AVWAP SD behavior
- Interacts correctly with Change 9 (new anchor point)

**3. Remove Volume, Expand Stochs, More History** -- CLEAR, one code impact
- v1 `build_trade_chart()` line 293: `make_subplots(rows=3, ...)` -> change to `rows=2`
- v1 `row_heights=[0.50, 0.30, 0.20]` -> `[0.60, 0.40]`
- v1 lines 450-458 (volume bar trace) -> DELETE
- v1 line 340 `for r in range(1, 4):` -> change to `range(1, 3)` (entry/exit vertical lines loop)
- v1 `main()` line 693: `start_ms = entry_ms - (60 * candle_ms)` -> `120 * candle_ms`
- **EMA warmup note**: EMA 55/89 use `ewm(span=N)` which needs ~2x span bars for accuracy. With 120 pre-entry bars, EMA 55 is fine but EMA 89 is marginal (120 < 178). The v1 had the same issue at 60 bars. 120 is a significant improvement. Not worth flagging as a blocker -- just noting.

**4. Entry/Exit Arrow Markers** -- CLEAR
- Add `go.Scatter` traces with `mode="markers"` on the price panel (row=1)
- LONG entry: `marker_symbol="triangle-up"` at entry candle low
- SHORT entry: `marker_symbol="triangle-down"` at entry candle high
- Exit: `marker_symbol="x"` at exit price
- Need entry/exit bar index (already computed in v1 lines 715-718) to get high/low values

**5. Timeframe Label** -- CLEAR
- v1 line 462: `title_text = "#" + str(trade_num) + " " + symbol + ...`
- Change to prepend "5m | " -> `"5m | " + symbol + " | " + direction + " | " + grade + " | ..."`
- Trivial change

**6. Right Sidebar Notes Panel** -- CLEAR, layout consideration
- Three-column layout: left (220px) | main (flex) | right (280px)
- v1 `#main { margin-left: 230px; }` -> `margin-left: 230px; margin-right: 290px;`
- Notes panel must update content when navigating trades (pagination)
- With pagination, only one notes area is active at a time -- simpler than v1's multiple textareas

**7. @Anchor Structured Notes** -- CLEAR, implementation recommendation
- **Recommend textarea + preview div** (not contenteditable). Reasons:
  - contenteditable cursor management is notoriously fragile
  - textarea is simpler, more reliable for raw text editing
  - preview div below renders colored @anchors with regex replacement
  - Raw text with @anchors saved to localStorage (same as spec)
- Regex: `/@(stoch9|stoch14|stoch40|stoch60|ema55|ema89|avwap|entry|exit|trend|grade)/g`
- Replace with `<span style="color:${colorMap[match]}">@${match}</span>` in preview

**8. Toggle Overlays** -- CLEAR, one complexity note
- Plotly `restyle` can show/hide traces by index or name
- Need trace name consistency: "EMA 55", "EMA 89", "AVWAP", "AVWAP +1SD", etc.
- Toggle state per trade in localStorage: key = `bingx_toggle_{date}_{tradeNum}_{overlay}`
- **Ripster toggle**: no traces to toggle yet. Button exists, wired to restyle for trace name "Ripster" -- no-op until traces exist. Fine.
- **Complexity note**: With pagination, Plotly chart divs are recreated per trade. Toggles must re-apply saved state when navigating to a trade. This means on page change: (1) render chart, (2) read toggle states from localStorage, (3) apply restyle. Workable but must be in the spec-to-code mapping.

**9. AVWAP Anchor at Last EMA Cross** -- CLEAR
- v1 `compute_indicators()` line 174: `if 0 <= entry_idx < len(df):` starts AVWAP at entry_idx
- Change: before AVWAP calc, scan backwards from entry_idx for sign change in `ema55 - ema89`
- `cross_idx = entry_idx` (fallback), then `for i in range(entry_idx-1, 0, -1): if sign changes, cross_idx = i, break`
- If no cross found (EMAs don't cross in window), use `cross_idx = 0` (first bar)
- AVWAP + SD bands both start from `cross_idx`
- **Ordering dependency**: EMA 55/89 must be computed BEFORE finding the cross point. In v1, they're computed at lines 168-169 before AVWAP at 172-181. Same order works.

**10. Export All Notes** -- CLEAR
- Client-side Blob download. Standard pattern.
- Needs to iterate all trade numbers, read localStorage keys, format as markdown
- Button placement: top of notes panel

### Cross-Cutting Concerns

**A. File size** -- v1 is 748 lines. v2 will be ~1100-1300 lines due to expanded HTML/JS (pagination, toggles, notes panel, export). Single file is fine per spec (rule 5).

**B. Plotly chart rendering with pagination** -- Each trade's chart HTML is pre-rendered by `pio.to_html()`. With pagination, all chart divs exist in DOM but only one is visible. Plotly may not render correctly in hidden divs. **Solution**: use `Plotly.relayout(divId, {})` or `Plotly.Plots.resize(divId)` when showing a trade page, OR render charts lazily. Recommend: keep all divs in DOM with `display:none`, call `Plotly.relayout` on show.

**C. The v1 uses `pio.to_html(fig, full_html=False, include_plotlyjs=False)`** -- This generates a `<div>` with an inline `<script>` that calls `Plotly.newPlot`. Each chart div has a unique auto-generated ID. This should work with pagination (show/hide divs). The Plotly resize on show is still recommended.

**D. No breaking changes to CLI args** -- Same `--date`, `--from-time`, `--symbol`, `--no-api` flags. Output path unchanged. Good.

### Verdict

**Build prompt is well-specified and ready to execute.** No blocking issues found. Two recommendations:
1. Use textarea + preview (not contenteditable) for @anchors
2. Add `Plotly.relayout` call on page navigation to handle hidden-div rendering

### Files to Modify
- Input (read only): `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report.py`
- Output (new file): `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v2.py`

### Run Command
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v2.py" --date 2026-03-11
```

### Verification
1. `py_compile` must pass
2. Run with `--date 2026-03-11`, open HTML in browser
3. Test: pagination arrows + sidebar clicks navigate trades
4. Test: AVWAP line starts at EMA cross (not entry)
5. Test: SD bands visible around AVWAP
6. Test: entry/exit arrow markers on price chart
7. Test: notes panel on right, @anchor preview colors
8. Test: toggle buttons hide/show overlays
9. Test: Export All Notes downloads .md file
10. Test: no volume panel, stoch panel taller, more pre-entry bars visible

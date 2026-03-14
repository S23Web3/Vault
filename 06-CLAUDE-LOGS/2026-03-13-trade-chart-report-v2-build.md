# Trade Chart Report v2 — Interactive Build Session
**Date:** 2026-03-13
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v2.py`
**Continuation from:** 2026-03-12 session (context loss, resumed)

## Summary
Built Trade Chart Report v2 from the build prompt + audit. Iterative feature additions across two sessions (12th + 13th). Final file ~1850 lines. All features compile clean (`py_compile` PASS at every step).

## Features Implemented (v2 vs v1)

### From Build Prompt (10 changes)
1. **One trade per page** — pagination with sidebar nav, keyboard arrows
2. **AVWAP SD bands** — 1SD + 2SD above/below AVWAP (anchored at EMA cross)
3. **Remove volume panel** — expanded stoch, 120 pre-entry bars (was 60)
4. **Entry/exit arrow markers** — triangle-up/down with offset + "LONG ENTRY"/"SHORT ENTRY"/"EXIT" labels
5. **5m timeframe label** — in title and annotation box
6. **Right sidebar notes panel** — fixed 280px, localStorage persistence
7. **@anchor structured notes** — textarea + colored preview div, regex highlighting
8. **Toggle overlays** — per-trade localStorage, Plotly restyle show/hide
9. **AVWAP anchor at last EMA cross** — scan backwards for sign change in ema55-ema89
10. **Export All Notes** — client-side Blob download as .md

### Additional Features (user-requested during build)
11. **6 separate panels** — Price | Stoch 9 | Stoch 14 | TDI 14 | Stoch 40 | Stoch 60
12. **TDI indicator** — RSI 14, BB(34, 1.6185x), Fast MA(7), Slow MA(2), volatility band fill
13. **AVWAP Hi/Lo** — anchored at highest high and lowest low bars in window, each with 1SD/2SD bands
14. **Separate toggles** — AVWAP Hi + bands, AVWAP Lo + bands, Stoch 9, Stoch 14 all independent
15. **Zone fills on stochastics** — green above 75/70, red below 25/30 (matching Four Pillars cross_level/zone_level)
16. **Measure tool** — click two points on price panel, draws horizontal lines + vertical connector + delta/% label. Invisible overlay trace for reliable click detection.
17. **Pin tool** — drop numbered pins on any panel, auto-inserts full indicator readings into notes. Pins persist in localStorage, restore on page navigation.
18. **Crosshair spike lines** — across all 6 panels, closest hover mode with compact translucent labels
19. **Legend in sidebar** — below trades list, line style differentiation (solid/dashed/dotted/thick)
20. **Auto-open Brave** — script finds brave.exe in Program Files or LocalAppData
21. **Notes auto-save to disk** — local HTTP server on port 9234, debounced 500ms POST on every keystroke, saves to `logs/trade_notes_{date}.json`. Server stays alive until Ctrl+C.

## Architecture
- Single Python file, single-file HTML output (only Plotly CDN external)
- `compute_indicators()` — EMA, AVWAP (3 anchors), stochastics (4), TDI, all SD bands
- `build_trade_chart()` — 6-panel Plotly make_subplots, zone fills, markers, annotations
- `build_html_report()` — CSS + JS inline, pagination, toggles, notes, pin/measure tools
- `start_notes_server()` — http.server on localhost:9234, `/api/save-note` POST, `/api/load-notes` GET
- `main()` — CLI args, BingX API fetch, chart build loop, HTML write, server start, Brave launch

## Run Command
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v2.py" --date 2026-03-11
```

## Key Decisions
- **textarea + preview** (not contenteditable) for @anchors — more reliable cursor behavior
- **Plotly.relayout** on page navigation to handle hidden-div rendering
- **hovermode="closest"** instead of "x unified" — prevents tooltip from blocking indicator panels
- **Invisible overlay trace** on price panel — transparent markers at every bar's close so measure/pin clicks always register
- **HTTP server for notes** — browser JS can't write to filesystem, so script stays alive as a server

## Known Limitations
- EMA 89 warmup marginal at 120 bars (needs ~178 for full accuracy) — same issue as v1, improved from 60 bars
- Pins stored in localStorage only (not server-persisted yet)
- TDI module is basic — advanced TDI module built separately in `signals/tdi.py` (not yet integrated)

## Files
- **Script:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v2.py` (~1850 lines)
- **Output HTML:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\logs\trade_chart_report_{date}.html`
- **Notes JSON:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\logs\trade_notes_{date}.json`
- **Build prompt:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-trade-chart-report-v2-build-prompt.md`
- **Audit:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-trade-chart-report-v2-audit.md`

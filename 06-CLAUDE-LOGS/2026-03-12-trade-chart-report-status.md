# 2026-03-12 — Trade Chart Report Tool Status

## Session Type
Recovery check. The chat that built this tool was lost to a reboot. This log documents what survived.

## Script Status

| Item | Status |
|------|--------|
| Build script | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\build_trade_chart_report.py` — EXISTS |
| Output script | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report.py` — EXISTS |
| py_compile | PASS |
| Lines | 748 |
| Runtime tested | NOT YET |

## What the Script Does

Reads `trades.csv` from the BingX connector, fetches 5m klines from BingX API per trade, computes indicators, runs Four Pillars signal detection, and generates a single interactive HTML report.

### 3-Panel Chart Per Trade
1. **Price panel (50%)** — Candlestick OHLC + EMA 55 (orange) + EMA 89 (blue) + AVWAP (white dashed, anchored at entry). Entry/exit vertical lines. Entry/exit price horizontals. Four Pillars signal lines (A/B long/short with labels).
2. **Stochastics panel (30%)** — All 4 stochastics overlaid: K9 (cyan), K14 (orchid), K40+D40 (gold), K60+D60 (tomato). Overbought/oversold zones shaded. Signal lines at 0.4 opacity.
3. **Volume panel (20%)** — Green/red bars. Entry/exit vertical lines.

### Annotation Box (top-left of price panel)
- Symbol, direction, grade
- Entry -> Exit prices
- PnL, exit reason
- Hold time, BE raised, TTP activated
- Signal counts in window (A/B long/short)

### HTML Report Structure
- Fixed summary bar (date, trades, WR, net PnL, time range)
- Fixed sidebar with trade links (green=win, red=loss)
- Per-trade sections with chart + comment textarea
- localStorage save/restore for notes
- Plotly CDN, dark theme (#0d1117)

### Indicators Computed
| Indicator | Params | Source |
|-----------|--------|--------|
| EMA 55 | span=55, adjust=False | pandas ewm |
| EMA 89 | span=89, adjust=False | pandas ewm |
| AVWAP | Anchored at entry candle | typical_price * volume cumulative |
| Stoch 9 | k_len=9, raw K only | stoch_k() loop (from signals/stochastics.py) |
| Stoch 14 | k_len=14, raw K only | stoch_k() loop |
| Stoch 40 | k_len=40, d_smooth=4 | stoch_k() + rolling mean |
| Stoch 60 | k_len=60, d_smooth=10 | stoch_k() + rolling mean |

### Four Pillars Signal Detection
- Imports `compute_signals` from backtester `signals/four_pillars.py`
- Reads params from `config.yaml` at runtime
- Signal columns: `long_a`, `long_b`, `short_a`, `short_b`
- Draws vertical lines on price + stochastics panels

### Note: BBWP was REMOVED from this tool per user instruction (no Panel 3 BBWP).

## CLI Usage

```bash
# All trades from today
python scripts/run_trade_chart_report.py --date 2026-03-12

# Today from 06:45
python scripts/run_trade_chart_report.py --date 2026-03-12 --from-time 06:45

# Single coin
python scripts/run_trade_chart_report.py --date 2026-03-12 --symbol RIVERUSDT

# No API (CSV data only)
python scripts/run_trade_chart_report.py --date 2026-03-12 --no-api
```

## Output Path
```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\logs\trade_chart_report_{DATE}.html
```

## What Was NOT Done
- No session log was written by the original chat (reboot killed it)
- Script has NOT been runtime-tested yet
- No trades have been charted yet

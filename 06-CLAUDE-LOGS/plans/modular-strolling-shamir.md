# Today's Build Plan — 2026-02-28
# BingX Dashboard + Vince B1-B6

---

## Token Conservation Rules (this session)

- I build every file directly — no agents, no background tasks
- Order: dashboard.py first, then Vince B1 → B2 → B3 → B4 → B5 → B6
- You run the verify command after each block before I continue
- Ollama (qwen3:8b) handles boilerplate-only files — I write the prompt, you run it locally (zero Claude tokens)
- I do NOT read files I already know, do NOT do speculative searches
- If a block fails, I read only the failing file to debug

---

## Block 0 — BingX Live Trades Dashboard

**Strategy:** Background agent. Runs in parallel while I start Vince B1 in main context.
**File:** `PROJECTS/bingx-connector/dashboard.py` (new file, ~200 lines)
**Run:** `cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector" && python dashboard.py`

### Data Sources (agent must use exactly these)

**`state.json` schema (confirmed from live file):**
```
open_positions: dict keyed "SYMBOL_DIRECTION"
  each entry: symbol, direction, grade, entry_price, sl_price, tp_price (null),
              quantity, notional_usd, entry_time, order_id, atr_at_entry, be_raised
daily_pnl: float
daily_trades: int
halt_flag: bool
session_start: datetime str
```

**`trades.csv` columns:**
`timestamp, symbol, direction, grade, entry_price, exit_price, exit_reason, pnl_net, quantity, notional_usd, entry_time, order_id`

**Live config (from config.yaml):**
- `margin_usd: 5.0`, `leverage: 10` → $50 notional per trade
- `max_positions: 8`, `daily_loss_limit_usd: 15.0`
- `require_stage2: true`, no fixed TP (trailing SL approach)
- 47 coins active

### Panels

| Panel | Data source | Shows |
|-------|------------|-------|
| Summary cards | trades.csv + state.json | Total trades, today trades, total net PnL, today PnL, total volume (USDT), win rate %, open positions count, BE raised count, halt status |
| Open Positions | state.json | Symbol, direction, grade, entry_price, sl_price (= entry if BE raised), be_raised badge, time open |
| Closed Trades | trades.csv | AG Grid table, all columns, sortable + filterable |
| Exit Breakdown | trades.csv | Pie: TP_HIT / SL_HIT / SL_HIT_ASSUMED / EXIT_UNKNOWN |
| Grade Analysis | trades.csv | Bar: A vs B — trade count, win rate, avg net PnL |
| Cumulative PnL | trades.csv | Line chart by hour (today, UTC) |

**Auto-refresh:** 60s via `dcc.Interval`
**Note on LSG%:** Bot does not store MFE — LSG lives in Vince Panel 2, not here.
**NEVER TOUCH:** `main.py`, `state_manager.py` — dashboard is read-only on data files.

---

## Block 1 — Vince: FourPillarsPlugin (B1)

**File:** `PROJECTS/four-pillars-backtester/strategies/four_pillars.py`
**Wraps:** `signals/four_pillars_v383_v2.py` (compute_signals_v383) + `engine/backtester_v384.py`
**Extends:** `strategies/base_v2.py` (StrategyPlugin ABC — do not modify)
**IMPORTANT:** Read `signals/four_pillars.py` and `signals/state_machine.py` first — both modified 2026-02-27 (stage 2 filter added). Plugin must wrap the CURRENT signal interface, not v383.
**Verify:** `python -c "from strategies.four_pillars import FourPillarsPlugin; p = FourPillarsPlugin(); print(p.name)"`

---

## Block 2 — Vince: API Layer + Types (B2)

**Files:**
- `vince/types.py` → **Ollama** (dataclasses only: MetricTable, EnrichedTrade, ConstellationResult, SessionRecord)
- `vince/api.py` → **Claude** (query_trades, query_constellation, run_backtest_for_plugin, get_metric_table)

**Verify:** `python -c "from vince.api import query_trades; print(query_trades())"`

---

## Block 3 — Vince: Enricher (B3)

**File:** `vince/enricher.py`
**What:** Attaches indicator snapshots to every trade. Uses diskcache keyed by session_id (stored in dcc.Store). Reuses `engine/position_v384.py` (Trade384) and `signals/bbwp.py`.
**Verify:** `python -c "from vince.enricher import Enricher; print('ok')"`

---

## Block 4 — Vince: PnL Reversal Panel data module (B4) — PRIORITY

**File:** `vince/pages/pnl_reversal.py` (pure Python, no Dash imports)
**What:** MFE histogram in ATR bins, TP sweep curve, optimal exit point calculation
**Verify:** `python -c "from vince.pages import pnl_reversal; print('ok')"`

---

## Block 5 — Vince: Constellation Query Engine (B5)

**File:** `vince/query_engine.py`
**What:** Filter builder, matched vs complement trade sets, delta table across all metrics
**Verify:** `python -c "from vince.query_engine import ConstellationQuery; print('ok')"`

---

## Block 6 — Vince: Dash App Shell (B6)

**Files:**
- `vince/__init__.py` → **Ollama** (empty + version string)
- `vince/pages/__init__.py` → **Ollama** (empty)
- `vince/assets/style.css` → **Ollama** (minimal dark theme vars)
- `vince/layout.py` → **Claude** (sidebar nav + page routing)
- `vince/app.py` → **Claude** (Dash entry point, register_page, dcc.Store hierarchy)

**Verify:** `python vince/app.py` → browser opens with sidebar + all panel routes visible

---

## What Ollama Handles (zero Claude tokens)

I write each prompt. You paste into terminal: `ollama run qwen3:8b "<prompt>"`

| File | Why Ollama is enough |
|------|---------------------|
| `vince/types.py` | Pure dataclasses, no logic |
| `vince/__init__.py` | 3 lines |
| `vince/pages/__init__.py` | 2 lines |
| `vince/assets/style.css` | CSS variables only |

---

## Files That Must NOT Be Modified

- `strategies/base_v2.py` — ABC locked
- `signals/four_pillars_v383_v2.py` — signal engine
- `engine/backtester_v384.py` — backtester
- `PROJECTS/bingx-connector/main.py` — live bot

---

## End State

After Block 6:
- BingX dashboard running at localhost showing live bot data
- `python vince/app.py` launches Vince with sidebar, all panel routes
- Panel 2 (PnL Reversal / LSG analysis) functional
- API callable from Python REPL

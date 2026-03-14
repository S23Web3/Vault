# Session Log — 2026-03-12 — Vince Strategy Independence Redesign

## Session Type
Architecture decision + documentation update. No code written.

## Context Read This Session
- `INDEX.md` — full read (153 files)
- All 4 today's session logs (WEEX planning, BingX v3 bugs, V4 planning, chart report status)
- `PROJECT-STATUS.md`, `PROJECT-OVERVIEW.md`, `PRODUCT-BACKLOG.md`
- `RESEARCH-FINDINGS.md` — synthesis section (night run, covers to 2026-03-06)
- `VINCE-V2-CONCEPT-v2.md` — full read
- `STRATEGY-V4-DESIGN.md`, `S12-MACRO-CYCLE.md` — full read
- `plans/2026-02-27-vince-b1-b10-build-plan.md`, `plans/2026-02-28-vince-doc-sync.md`
- `trades_all.csv` header — confirmed 20-column schema

## Key Finding: Research Night Run Status
The research orchestrator (run 2026-03-05/06) covered 353 files and is accurate to 2026-03-06. Everything from 2026-03-07 to 2026-03-12 happened after the run:
- BingX v3 (19 bugs), 55/89 analysis, S12 correction, V4 workflow lock, WEEX probe, BingX v3 build, trade chart report, trades_all.csv merge — all missing from synthesis.
- `PROJECT-STATUS.md` (rewritten today) supersedes the synthesis for current state.

## Architecture Decision: Vince Strategy Independence

### Problem with prior framing
B1 was "FourPillarsPlugin" — framed as requiring the Four Pillars signal model before Vince could start. This created a dependency chain: V4 signal model → B1 → B3 → B4 → all Vince. Since V4 is chart-driven and will take weeks, Vince was effectively indefinitely blocked.

### Decision (locked 2026-03-12)
Vince is fully strategy-agnostic. The `StrategyPlugin` ABC (`strategies/base_v2.py`) already exists and defines the interface correctly. B1 is now:

**Build Vince core + the generic plugin infrastructure. Four Pillars is one example plugin, not a prerequisite.**

### What unblocks
- B1 no longer waits for V4
- B1 runs immediately on `trades_all.csv` (193 live bot trades, 20-col v2 schema)
- B3 (Enricher), B4 (PnL Reversal), B5 (Constellation) all unblock in cascade
- V4, 55/89, WEEX all become future plugins — zero changes to Vince core when they arrive

### Vince primary intelligence (priority order, locked)
1. **Exit timing** — when to hold vs cut based on indicator state after entry (let winners run, cut losers)
2. **Entry quality** — which indicator constellations at entry produce the best outcomes
3. **TP optimisation** — what TP multiple maximises net PnL per strategy, per coin

### Data source for B1 (locked)
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\trades_all.csv`
- 193 trades (v1 + v2 connector merged)
- Date range: 2026-03-03 to 2026-03-11
- 20 columns: timestamp, symbol, direction, grade, entry_price, exit_price, exit_reason, pnl_net, quantity, notional_usd, entry_time, order_id, ttp_activated, ttp_extreme_pct, ttp_trail_pct, ttp_exit_reason, be_raised, saw_green, atr_at_entry, sl_price

### Multi-strategy plugin architecture
Any strategy that implements `StrategyPlugin` ABC works with Vince:
- `compute_signals(ohlcv_df)` → enriched DataFrame with all indicator columns
- `parameter_space()` → sweepable params with bounds and types
- `trade_schema()` → column definitions for this strategy's trade CSV
- `run_backtest(params, start, end, symbols)` → Path to trade CSV
- `strategy_document` → Path to strategy markdown (for LLM layer)

Future plugins: V4, 55/89, WEEX — all plug in without changing Vince core.

## What B1 Needs (all exist today)

| Dependency | Path | Status |
|------------|------|--------|
| StrategyPlugin ABC | `strategies/base_v2.py` | EXISTS |
| Trade CSV | `PROJECTS/bingx-connector-v2/trades_all.csv` | EXISTS — 193 trades |
| Signal compute | `signals/four_pillars_v383_v2.py` | EXISTS |
| Backtester | `engine/backtester_v384.py` | EXISTS |
| API stubs (B2) | `vince/types.py`, `vince/api.py` | EXISTS |
| Python skill | `C:\Users\User\.claude\skills\python\SKILL.md` | EXISTS |
| Dash skill | `C:\Users\User\.claude\skills\dash\SKILL.md` | EXISTS |

**No blocker. B1 can start immediately in a new Claude Code session.**

## Files Updated This Session

| File | Change |
|------|--------|
| `06-CLAUDE-LOGS\PROJECT-STATUS.md` | Full rewrite — Vince unblocked, new decisions 13-16 added, BingX v3 added |
| `PROJECT-OVERVIEW.md` | Full rewrite — updated Mermaid UML, all status tables current, WEEX + BingX v3 added |
| `PRODUCT-BACKLOG.md` | Full rewrite — P0.6 superseded by P0.10 (READY), B3/B4/B5 unblocked, P3 future plugins added |
| `06-CLAUDE-LOGS\INDEX.md` | Appended session 2 entry |
| `06-CLAUDE-LOGS\2026-03-12-vince-strategy-independence.md` | This file |

## Next Action for Vince B1
Open a new Claude Code session. Provide:
1. Read `06-CLAUDE-LOGS\PROJECT-STATUS.md` — current state
2. Read `PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md` — architecture
3. Read `PROJECTS\four-pillars-backtester\strategies\base_v2.py` — StrategyPlugin ABC
4. Load Python skill + Dash skill
5. Build: Vince core infrastructure + FourPillarsPlugin wrapping existing `four_pillars_v383_v2.py` signal module
6. Test: run enricher on `trades_all.csv`, confirm indicator snapshots attach to every trade row
7. First analysis target: Panel 2 (PnL Reversal) — MFE histogram showing when winners were held vs when losers should have been cut

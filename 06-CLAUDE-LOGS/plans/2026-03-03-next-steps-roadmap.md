# Next Steps Roadmap — Four Pillars / Vince v2
**Written:** 2026-03-03
**Context:** B2 done. B1 plan exists. Strategy has 6 open issues. This document lists
every pending task in order with clear prerequisites and run commands.

---

## PHASE 0 — Strategy Alignment (blocks everything)

Must be done before B1 because the plugin wraps the strategy.
If the strategy is wrong, the plugin bakes in the wrong defaults.

### Step 0.1 — Generate the strategy analysis report

**Who runs it:** User
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/build_strategy_analysis.py
```
Output: `docs/STRATEGY-ANALYSIS-REPORT.md`

### Step 0.2 — Claude Web discussion

Paste the full report into Claude Web. Get answers to these 6 questions:

| # | Question | Why it matters |
|---|----------|----------------|
| 1 | Should `rot_level` be 50 instead of 80? | rot_level=80 means stoch_40 > 20 for longs — almost always true, not a real filter. rot_level=50 would require stoch_40 was in bullish territory before the setup. |
| 2 | Should BBW be wired into `compute_signals()` before B3? | Enricher snapshots indicator state at entry/MFE/exit. If BBW is not in compute_signals output, Vince will never see it. Wire it before building Enricher. |
| 3 | Should the live bot be updated to import `signals/four_pillars_v386.py` instead of v1? | Bot and backtester currently run different default configs. v386 has require_stage2=True and allow_c=False baked in. Bot overrides via config.yaml but still runs older ATR/stoch code paths. |
| 4 | Trailing stop: accept AVWAP (backtester) vs BingX native 2% (bot) divergence, or fix? | They produce different exit prices on the same trade. Live performance will not match backtest performance. |
| 5 | Should bot config.yaml get `be_trigger_atr` and `be_lock_atr`? | BE raise exists in backtester but bot never raises SL to breakeven. Another source of backtest vs live divergence. |
| 6 | Is ExitManager dead code? | `engine/exit_manager.py` defines 4 risk methods but no engine file imports it. position_v384.py handles BE+AVWAP inline. Confirm before B3 Enricher references it. |

### Step 0.3 — Apply decisions to code

After Claude Web discussion, in a new Claude Code session:
- Update `rot_level` default in `signals/four_pillars_v386.py` if changed
- Wire `signals/bbwp.py` into `compute_signals()` in `signals/four_pillars_v386.py` if decided
- Update bot plugin import if bot-to-v386 upgrade is decided
- Update `config.yaml` with BE raise params if decided
- py_compile all modified files

---

## PHASE 1 — B1 FourPillarsPlugin

**Prerequisite:** Phase 0 strategy decisions applied.
**Plan file:** `C:\Users\User\.claude\plans\snuggly-mixing-moon.md`
**Spec file:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B1-PLUGIN.md`

### What B1 builds

Single file: `strategies/four_pillars.py` (rewrite of existing v1)

Before writing: copy existing to `strategies/four_pillars_v1_archive.py`

`FourPillarsPlugin(StrategyPlugin)` — 5 methods:
1. `compute_signals(self, ohlcv_df)` — calls `signals/four_pillars_v386.py`
2. `parameter_space(self)` — 7 sweepable BT params
3. `trade_schema(self)` — 6 required + ~13 optional columns
4. `run_backtest(self, params, start, end, symbols)` — loads parquet, runs Backtester385, writes CSV
5. `strategy_document` property — path to `docs/FOUR-PILLARS-STRATEGY-v386.md`

### Key B1 decisions (locked)

| Decision | Value |
|----------|-------|
| Signal import | `from signals.four_pillars_v386 import compute_signals` — NOT v383_v2 |
| Engine import | `from engine.backtester_v385 import Backtester385` |
| Signal params | Stored at construction, NOT passed at call site |
| Param routing | ALL params passed to bt and sig via `.get()` with defaults — no explicit split |
| Results path | `results/vince_{timestamp}.csv` |
| Thread safety | Fresh `Backtester385` instance per call — Optuna-safe |

### SPEC CONFLICT — resolved here

`BUILD-VINCE-B1-PLUGIN.md` line 358 says `compute_signals_v383` from `four_pillars_v383_v2.py`.
This spec was written before v386 was created. The plan mode plan and B3 spec both reference v386.

**Use v386. The build spec is outdated. Follow the plan mode plan.**

### Build script to create

`scripts/build_b1_plugin.py` — steps:
1. Archive v1 to `strategies/four_pillars_v1_archive.py` (py_compile PASS required)
2. Write new `strategies/four_pillars.py` (py_compile PASS required)
3. Smoke test 1: interface check (instantiate, assert StrategyPlugin, check parameter_space + trade_schema)
4. Smoke test 2: compute_signals on 300-row synthetic OHLCV (assert output columns present, row count unchanged)
5. Smoke test 3: strategy_document exists on disk
6. Print ALL TESTS PASSED or list failures

### Run command (user runs after Claude writes build script)

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/build_b1_plugin.py
```

---

## PHASE 2 — B3 Enricher

**Prerequisite:** B1 complete.
**Spec:** `BUILD-VINCE-B3-ENRICHER.md`

### What B3 builds

`vince/enricher.py` — Enricher class

For each trade in a CSV:
- Load parquet for the symbol
- Call `plugin.compute_signals(df)` once per symbol (cached with diskcache)
- For each trade: snapshot indicator state at entry_bar, MFE bar, exit bar
- Columns added: all IndicatorSnapshot fields (k1/k2/k3/k4, cloud_bull, bbw) at each moment
- Returns `EnrichedTradeSet` (vince/types.py)

Also creates:
- `vince/cache_config.py` — diskcache setup
- `tests/test_enricher.py` — round-trip test

### Key B3 decisions (all locked 2026-02-28)

| Decision | Value |
|----------|-------|
| Cache | diskcache (not functools.lru_cache — must survive process restarts) |
| Volume | ALL trades enriched — no skipping |
| Bar index | Enricher uses SAME date-filtered slice as B1 run_backtest() |
| MFE bar | `mfe_bar` index from Backtester385 output (v385 adds it) |
| BBW | Only if wired into compute_signals() output (Phase 0 decision) |

---

## PHASE 3 — B4 PnL Reversal Panel

**Prerequisite:** B3 complete.
**Spec:** `BUILD-VINCE-B4-PNL-REVERSAL.md`
**Priority:** Highest after infrastructure is ready (Panel 2 in Vince UI).

### What B4 builds

`vince/pages/pnl_reversal.py` — Dash page (load Dash skill before building)

Panels:
- LSG analysis: how many losers were winners at some point (saw_green=True)
- MFE histogram: 9-bin ATR buckets, winners vs losers
- TP sweep: simulated TP at each ATR level, PnL curve
- Winners left on table: trades that hit MFE > threshold but closed as losers

---

## PHASE 4 — B5 Query Engine

**Prerequisite:** B3 complete.
**Spec:** `BUILD-VINCE-B5-QUERY-ENGINE.md`

`vince/query_engine.py` — constellation filter + permutation test

---

## PHASE 5 — B6 Dash Shell

**Prerequisite:** B1-B5 complete.
**Spec:** `BUILD-VINCE-B6-DASH-SHELL.md`
**MANDATORY:** Load Dash skill before building.

`vince/app.py` + `vince/layout.py` — 8-panel multi-page Dash app skeleton

---

## Quick Reference — Run Commands

```
# Validate B2 (already built — run to confirm nothing broken)
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/build_b2_api.py

# Generate strategy analysis report (FIRST STEP)
python scripts/build_strategy_analysis.py

# Run codebase audit only
python -c "from vince.audit import run_audit; run_audit()"

# After B1 is built:
python scripts/build_b1_plugin.py
```

---

## File Map — Key Paths

| What | Path |
|------|------|
| B1 spec | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B1-PLUGIN.md` |
| B1 plan (plan mode) | `C:\Users\User\.claude\plans\snuggly-mixing-moon.md` |
| B3 spec | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B3-ENRICHER.md` |
| B4 spec | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B4-PNL-REVERSAL.md` |
| B5 spec | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B5-QUERY-ENGINE.md` |
| B6 spec | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B6-DASH-SHELL.md` |
| Strategy analysis script | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_strategy_analysis.py` |
| Strategy analysis report | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\STRATEGY-ANALYSIS-REPORT.md` |
| Plugin interface spec | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-PLUGIN-INTERFACE-SPEC-v1.md` |
| Existing strategy v1 | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\strategies\four_pillars.py` |
| v386 signal file | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v386.py` |
| StrategyPlugin ABC | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\strategies\base_v2.py` |
| Backtester385 engine | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v385.py` |
| BBW signal (orphaned) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbwp.py` |
| vince/ package | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\vince\` |

# 2026-02-28 — Vince B1 Plugin: Research, Scope & Audit

**Session type:** Research + spec writing. No code built.
**Trigger:** User pointed to `PROJECTS/four-pillars-backtester/BUILD-VINCE-B1-PLUGIN.md` — file did not exist.

---

## What Happened

User asked to research the B1 build, identify required skills, scope the work, and audit it.
Session discovered the source file didn't exist, researched from build plan + plugin spec, then
created `BUILD-VINCE-B1-PLUGIN.md` as a formal build spec.

---

## Sources Researched

- `C:\Users\User\.claude\plans\async-watching-balloon.md` — B1-B10 build plan (approved 2026-02-27)
- `PROJECTS/four-pillars-backtester/docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — method contracts
- `PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md` — concept (approved)
- `PROJECTS/four-pillars-backtester/strategies/base_v2.py` — ABC to implement
- `PROJECTS/four-pillars-backtester/strategies/four_pillars.py` — existing v1 file (conflict found)
- `PROJECTS/four-pillars-backtester/engine/backtester_v384.py` + `backtester_v385.py` — engine options
- `PROJECTS/four-pillars-backtester/engine/position_v384.py` — Trade384 dataclass fields
- `PROJECTS/four-pillars-backtester/signals/four_pillars_v383_v2.py` — signal pipeline
- `PROJECTS/four-pillars-backtester/scripts/run_backtest_v384.py` — parquet loading pattern

---

## Skills Identified for B1

| Skill | Required | Reason |
|-------|----------|--------|
| `/four-pillars` | YES | Grade system, stochastic periods, entry type semantics |
| `/four-pillars-project` | YES | File versioning, which engine/signal versions are current |
| `/dash` | NO (B6+) | B1 is pure Python — zero Dash code |
| `/pinescript` | NO | Python only |

---

## Audit Findings

### Critical: Existing File Conflict

`strategies/four_pillars.py` already exists with a v1 partial implementation. The build plan
assumed it didn't exist. This file must be ARCHIVED before B1 rewrite begins.

Archive to: `strategies/four_pillars_v1_archive.py`

### v1 File Problems (6 issues)

1. Imports from `strategies.base` (v1 ABC) — not `strategies.base_v2` (v2 ABC)
2. Missing `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document`
3. Uses `FourPillarsStateMachine383` directly — should call `compute_signals_v383()` from `signals/four_pillars_v383_v2.py`
4. `compute_signals()` takes `params=None` — v2 ABC takes only `ohlcv_df` (params go in constructor)
5. Separate `enrich_ohlcv()` method — v2 merges all enrichment into one `compute_signals()` call
6. Legacy v1 classifier methods (`extract_features`, `get_feature_names`, `label_trades`) — drop them

### Engine Decision: v385 over v384

Build plan specifies v384. User confirmed v385. Key difference:

- v385 extends v384 with a post-processing pass: entry-state snapshots, lifecycle metrics, P&L path, LSG category
- v385 output `trades_df` already has indicator values at entry baked in
- This pre-enriches the CSV before B3 (Enricher) even runs — reduces B3 complexity
- v385 return structure identical to v384 — no other changes to wrapper logic

### Other Issues

- `symbol` field not in Trade384 — must be injected by `run_backtest()` wrapper per symbol loop
- Bar index note: `entry_bar`/`exit_bar` are 0-based indices into the DATE-FILTERED slice, not the full parquet. Enricher (B3) must use the same filtered slice. B1 documents this clearly, doesn't solve it.
- Strategy markdown: `docs/FOUR-PILLARS-STRATEGY-UML.md` confirmed to exist — used for `strategy_document` property.

---

## Output Created

**`PROJECTS/four-pillars-backtester/BUILD-VINCE-B1-PLUGIN.md`** — formal build spec including:
- Skills to load
- File archive instruction
- Per-method implementation guide (all 5 ABC methods)
- Full trade schema (v384 base fields + v385 enrichment columns)
- Constructor + constants
- Exact imports needed
- 4 verification tests (syntax, interface, compute_signals, run_backtest)
- What B1 does NOT include

**`06-CLAUDE-LOGS/plans/2026-02-28-vince-b1-plugin-scope-audit.md`** — plan copy (CLAUDE.md rule)

---

## State After Session

- `BUILD-VINCE-B1-PLUGIN.md` created and ready for execution
- No code written — this was research + spec only
- Next step: load `/four-pillars` + `/four-pillars-project`, archive v1 file, execute B1 build
- B1 is still P0.5 READY in backlog (was already tagged before this session)

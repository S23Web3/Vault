# B3 Enricher — Research Audit Session
**Date:** 2026-02-28
**Session type:** Research / audit — read-only exploration, no code written
**Plan file:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-b3-enricher-research-audit.md`

---

## What Was Asked

User referenced `BUILD-VINCE-B3-ENRICHER.md` (does not exist yet) and asked for:
1. Skills identification
2. Scope of work audit
3. API bottlenecks — all blocking questions surfaced
4. Improvements visible from the audit

---

## Files Read This Session

| File | Key finding |
|------|-------------|
| `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` | Full Enricher contract. Snapshot cols: `{col}_at_entry`, `_at_mfe`, `_at_exit`. OHLC tuples at critical bars. |
| `docs/VINCE-V2-CONCEPT-v2.md` | Approved v2 concept. Plugin-based, 8 panels, diskcache for indicator snapshots. |
| `engine/position_v384.py` | Trade384 dataclass — confirmed `mfe_bar` field is MISSING. Tracks `mfe` float but not which bar. |
| `signals/four_pillars.py` | Current signature: `compute_signals(df, params)` — incompatible with plugin interface. |
| `signals/four_pillars_v383_v2.py` | Numba-accelerated version, v3.8.3 state machine. Correct for performance but wrong version. |
| `strategies/base_v2.py` | StrategyPlugin ABC confirmed. Stub only, no implementation. |
| `PROJECTS/bingx-connector/plugins/four_pillars_v384.py` | BingX plugin — different interface, useful as reference for column rename pattern. |
| `PROJECTS/four-pillars-backtester/` (directory scan) | No `vince/` dir, no `enricher.py`, no diskcache anywhere in codebase. |

---

## Confirmed: What Exists vs What Is Missing

### EXISTS
- `strategies/base_v2.py` — ABC stub
- `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — full contract
- `engine/position_v384.py::Trade384` — trade record (incomplete for Enricher)
- `signals/four_pillars.py` — signal pipeline (wrong interface)
- `data/cache/*.parquet` — 400+ coins, 1m + 5m

### NOT CREATED YET
- `vince/` directory
- `vince/enricher.py`
- `vince/cache_config.py`
- `strategies/four_pillars_plugin.py`
- `diskcache` (not installed)

---

## 6 Critical Blockers

### BLOCKER 1: `mfe_bar` missing from Trade384 — HIGHEST PRIORITY
`engine/position_v384.py::Trade384` stores `mfe` (dollar float) and `mae` (dollar float)
but NOT `mfe_bar` (bar index where MFE occurred). Enricher needs `mfe_bar` to attach
`_at_mfe` snapshot columns. Without it, Panel 2 (PnL Reversal) and Panel 4 (Exit State)
lose their most valuable data. Three resolution options:
- (A) Modify position_v384.py directly (breaking change to Trade384 schema)
- (B) Create position_v385.py with the addition
- (C) Enricher does a second OHLCV pass to find MFE bar (slower, avoids Trade384 change)

### BLOCKER 2: compute_signals() signature mismatch
Current: `compute_signals(df, params=None)` — two args.
Required by plugin: `compute_signals(self, ohlcv_df)` — params baked in.
Also: pipeline expects `base_vol`/`quote_vol` columns; spec requires `volume`.
FourPillarsPlugin wrapper must handle all renames internally.

### BLOCKER 3: Column naming convention mismatch
Pipeline outputs: `stoch_9`, `stoch_14`, `stoch_40`, `stoch_60`, `stoch_60_d`
Spec requires: `k1_9`, `k2_14`, `k3_40`, `k4_60`
Options: rename in plugin wrapper (safe) or rename in stochastics.py globally (risky — breaks backtester + BingX connector).
Also: `bbw` listed in spec examples but NOT computed by `compute_signals()` — lives in `signals/bbw.py` separately.

### BLOCKER 4: diskcache not installed
Zero imports found across 270+ Python files. Needs:
```
pip install diskcache
```
Design decision: `Cache` (simple) vs `FanoutCache` (8 shards, better for Optuna parallelism).
Cache key: `f"{symbol}_{timeframe}_{params_hash}"` where params_hash = MD5 of sorted JSON.
Recommended location: `data/vince_cache/` (separate from OHLCV `data/cache/`).

### BLOCKER 5: Bar index offset bug in run_backtest()
Backtester runs on a date-filtered slice. If full parquet has 50,000 bars and date range
starts at bar 10,000, backtester's `entry_bar=0` = absolute bar 10,000.
Enricher needs absolute positional indices. FourPillarsPlugin.run_backtest() wrapper must
compute slice start offset and add it to all bar index values in the output CSV.
Every bar lookup will be wrong without this correction.

### BLOCKER 6: OHLC tuple storage format undefined
Spec says attach `entry_ohlc`, `mfe_ohlc`, `exit_ohlc` as `(open, high, low, close)` tuples.
Tuples don't round-trip through CSV. Options: JSON string, 4 separate columns, pipe-delimited.
Recommended: 4 separate columns (`entry_open`, `entry_high`, `entry_low`, `entry_close` etc.)
because Panel 4 will query individual OHLC values (intrabar SL hit detection).

---

## 8 Open Questions for User

| # | Question | Impact if wrong |
|---|----------|----------------|
| Q1 | mfe_bar: modify position_v384.py (A), create v385 (B), or Enricher second pass (C)? | Highest — blocks all `_at_mfe` columns |
| Q2 | Column rename: plugin wrapper only (A) or update stochastics.py globally (B)? | Medium — approach A is safe, B risks breakage |
| Q3 | diskcache: `Cache` or `FanoutCache`? | Low — FanoutCache recommended |
| Q4 | OHLC storage: 4 separate columns or JSON string? | Medium — affects downstream dashboard queries |
| Q5 | `strategy_document`: point at existing doc or create `docs/FOUR-PILLARS-STRATEGY-v384.md`? | Low — new doc recommended |
| Q6 | BBW in B3 snapshots or defer to later panel? | Low — can defer |
| Q7 | Signal pipeline version: standard (correctness) or Numba (performance)? | Medium — 400 symbols makes this significant |
| Q8 | Cache invalidation: static or bust on parquet mtime change? | Low — mtime check recommended |

---

## 6 Improvements Identified

1. **Consolidate Numba ATR kernel** — `signals/four_pillars.py` has pure-Python ATR loop. `signals/four_pillars_v383_v2.py` has `@njit(cache=True)` version. Should be shared, not duplicated.

2. **Raw stoch values flow through** — `compute_signals()` already attaches raw `stoch_9`, `stoch_14` etc. to the DataFrame. The enricher needs these — confirmed they survive the pipeline. Only a rename layer needed, not structural changes.

3. **trade_schema() should expose mfe_atr / mae_atr** — Trade384 has `mfe` and `mae` in dollar terms, `entry_atr` as field. Plugin should derive and expose `mfe_atr = mfe / (entry_atr * notional)` as an optional schema column for Panel 2.

4. **FanoutCache 2GB size cap** — 400 coins × 2 timeframes × indicator DataFrame = uncapped disk growth without `size_limit=2 * 1024 ** 3`.

5. **Enricher as context manager** — `with Enricher(...) as e:` pattern ensures diskcache closes cleanly (Windows file handle leak risk).

6. **Compliance CLI** — `python -m vince.compliance_check FourPillarsPlugin` runnable against any future plugin, automating the Section 6 checklist from the spec.

---

## Implementation Order (if user approves build)

1. Resolve Q1 (mfe_bar) — defines whether position_v384 or v385 is created
2. `strategies/four_pillars_plugin.py` — FourPillarsPlugin (all 5 methods)
3. `tests/test_four_pillars_plugin.py` — compliance checklist
4. `pip install diskcache` + `vince/cache_config.py`
5. `vince/enricher.py` — Enricher class
6. `tests/test_enricher.py` — round-trip test

---

## Session Outcome

Full research audit delivered. Plan written to:
- `C:\Users\User\.claude\plans\mellow-watching-lemon.md`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-b3-enricher-research-audit.md`

No code was written this session. Awaiting user decisions on Q1-Q8 before build can begin.

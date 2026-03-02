# B3 — Enricher Build Spec

**Build ID:** VINCE-B3
**Status:** BLOCKED — waiting on v386 signal file (`signals/four_pillars_v386.py`). All design decisions locked.
**Date:** 2026-02-28
**Updated:** 2026-02-28 (Q1-Q8 all resolved)
**Source research:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-b3-enricher-research-audit.md`

---

## What B3 Is

B3 attaches indicator snapshots to every trade in a trade CSV.
For each trade it captures 3 indicator states: entry bar, MFE bar, exit bar.
Results are cached with diskcache so compute_signals() runs once per symbol, not once per trade.
No trade is skipped — volume is always preserved.

---

## Skills to Load Before Building

- `/python` — MANDATORY
- `/dash` — MANDATORY (any file in vince/)
- `/four-pillars` — for signal pipeline context
- `/four-pillars-project` — for file versioning context

---

## Files

| # | File | Lines (est.) | Action |
|---|------|-------------|--------|
| 1 | `engine/position_v384.py` | modify | Add `mfe_bar: int` to Trade384 — OR use v385 if it already has it |
| 2 | `strategies/four_pillars_plugin.py` | ~140 | Create FourPillarsPlugin (v2-compliant wrapper) |
| 3 | `vince/cache_config.py` | ~20 | Create diskcache setup |
| 4 | `vince/enricher.py` | ~160 | Create Enricher class |
| 5 | `tests/test_enricher.py` | ~50 | Create round-trip test |
| 6 | `tests/test_four_pillars_plugin.py` | ~40 | Create plugin compliance test |

---

## CRITICAL BLOCKERS (resolve before any code is written)

### BLOCKER 1 (Highest priority): mfe_bar — RESOLVED
`engine/backtester_v385.py` already tracks and exposes `life_mfe_bar` in its
post-processing pass (line 234: `mfe_b = j`, line 250: `"life_mfe_bar": mfe_b`).
No changes to `position_v384.py` required. Enricher reads `life_mfe_bar` directly.

### BLOCKER 2: compute_signals() signature mismatch — RESOLVED
FourPillarsPlugin stores params in `__init__` and passes internally.
Column rename (`base_vol`/`quote_vol` → `volume`) done inside wrapper before calling pipeline.

### BLOCKER 3: Column naming convention — RESOLVED
Rename in plugin wrapper only. No changes to `signals/*.py` files.
Pipeline outputs (`stoch_9` etc.) → wrapper renames → enricher snapshot cols (`k1_9_at_entry` etc.).

### BLOCKER 4: diskcache — RESOLVED
`FanoutCache(shards=8, size_limit=2*1024**3)`.
Cache dir: `data/vince_cache/` (separate from `data/cache/`).
Cache key: `f"{symbol}_{timeframe}_{params_hash}_{mtime}"` — mtime from parquet file stat.

### BLOCKER 5: Bar index offset in run_backtest() — known, fix at build time
FourPillarsPlugin.run_backtest() must add the slice start offset to all bar indices.
Enricher uses absolute indices into the full OHLCV DataFrame.

### BLOCKER 6: OHLC storage format — RESOLVED
12 separate float columns: `entry_open`, `entry_high`, `entry_low`, `entry_close`,
`mfe_open`, `mfe_high`, `mfe_low`, `mfe_close`, `exit_open`, `exit_high`, `exit_low`, `exit_close`.
No JSON. Reason: JSON requires `json.loads()` per row — 1.2M parse calls at scale, unfiltered.

---

## REMAINING BLOCKER — v386 Signal File

**B3 cannot build until `signals/four_pillars_v386.py` exists.**

v386 captures the adjusted stochastic entry logic currently live in the BingX bot.
Fewer trades, higher conviction. Economic model: volume → rebates, but only on quality signals.
v386 scoping session reads the bot's current `four_pillars_v384.py`, documents what changed,
and produces `signals/four_pillars_v386.py` + `docs/FOUR-PILLARS-STRATEGY-v386.md`.

FourPillarsPlugin will wrap `signals/four_pillars_v386.py`.
Vince can also load older plugins (v384) to compare versions — plugin interface is strategy-agnostic.

---

## Design Decisions — All Locked (2026-02-28)

| Q | Decision |
|---|----------|
| Q1 | `life_mfe_bar` already in v385 — no engine changes needed |
| Q2 | Column rename in plugin wrapper only — no global signal file changes |
| Q3 | FanoutCache (shards=8, size_limit=2GB) |
| Q4 | 12 separate OHLC float columns (no JSON) |
| Q5 | `strategy_document()` returns `docs/FOUR-PILLARS-STRATEGY-v386.md` |
| Q6 | No BBW in enricher — flag for separate scoping session |
| Q7 | `signals/four_pillars_v386.py` (to be built in v386 scoping session) |
| Q8 | mtime included in cache key — auto-invalidates on parquet update |

---

## 6 Improvements Identified (Apply when building)

1. Numba ATR should be shared between pipelines, not duplicated
2. compute_signals() raw indicator values must survive to output (confirm intermediate cols preserved)
3. trade_schema() should include mfe_bar, mfe_atr, mae_atr fields
4. FanoutCache size_limit=2GB cap to prevent disk fill
5. Enricher as context manager for clean diskcache close on Windows
6. Plugin compliance checker as standalone CLI: `python -m vince.compliance_check <plugin_class>`

---

## Processing Flow (once blockers resolved)

```
trade_csv (from plugin.run_backtest())
  -> load per-symbol OHLCV parquet
  -> check diskcache for pre-computed indicator DataFrame
  -> cache miss: call plugin.compute_signals(ohlcv_df), store result
  -> for each trade:
      entry_bar  -> iloc[entry_bar]  -> {col}_at_entry columns
      mfe_bar    -> iloc[mfe_bar]    -> {col}_at_mfe columns   <- BLOCKED on Q1
      exit_bar   -> iloc[exit_bar]   -> {col}_at_exit columns
      OHLCRow    -> entry/mfe/exit   -> entry_open/high/low/close etc.
  -> return EnrichedTradeSet (DataFrame with all snapshot cols)
```

---

## Verification

```bash
python -c "import py_compile; py_compile.compile('vince/enricher.py', doraise=True); print('OK')"
python tests/test_enricher.py --symbol BTCUSDT --start 2024-01-01 --end 2024-01-31
python -c "
import pandas as pd
df = pd.read_csv('results/enriched_test.csv')
required = ['k1_9_at_entry', 'cloud3_bull_at_entry', 'atr_at_entry',
            'k1_9_at_mfe', 'k1_9_at_exit', 'entry_open', 'entry_high']
missing = [c for c in required if c not in df.columns]
print('MISSING:', missing or 'NONE')
"
```

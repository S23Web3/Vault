# B5 — Constellation Query Engine Build Spec

**Build ID:** VINCE-B5
**Status:** BLOCKED (depends on B1 -> B2 -> B3)
**Date:** 2026-02-28

---

## What B5 Is

The core analytical engine for Mode 1 (User Query). User sets a filter.
Engine splits trades into matched vs complement, computes 8 metric deltas,
runs permutation test (500 shuffles) to surface non-random patterns.

---

## Skills to Load Before Building

- `/python` — MANDATORY
- `/dash` — MANDATORY (any file in vince/)

---

## Files

| # | File | Lines (est.) | Action |
|---|------|-------------|--------|
| 1 | `vince/query_engine.py` | ~180 | Create |
| 2 | `tests/test_b5_query_engine.py` | ~50 | Create |

---

## Functions

### apply_filter(trade_set: EnrichedTradeSet, f: ConstellationFilter) -> tuple[pd.DataFrame, pd.DataFrame]
- Check all non-None filter fields against enriched DataFrame columns
- Universal fields: direction, outcome (WIN if pnl>0), min_mfe_atr, saw_green
- Column filters: `f.column_filters` dict — each key is a column name, value is (min, max) tuple or exact value
- Returns (matched_df, complement_df) — complement = rows NOT in matched, union = full set

### compute_metrics(df: pd.DataFrame) -> dict
8 metrics:
- win_rate: count(pnl > 0) / total
- profit_factor: sum(pnl[pnl>0]) / abs(sum(pnl[pnl<0]))
- avg_net_pnl: mean(pnl - commission)
- avg_mfe_atr: mean(mfe_atr column)
- avg_mae_atr: mean(mae_atr column)
- pnl_reversal_rate: count(mfe_atr > 1.0 AND pnl < 0) / total
- mfe_mae_ratio: avg_mfe_atr / avg_mae_atr
- trade_count: len(df)

### permutation_test(trade_set, f, metric="win_rate", n=500) -> float
1. Compute real delta = matched_metric - complement_metric
2. Shuffle trade assignment 500 times, compute delta each time
3. p-value = fraction of shuffled deltas >= real delta
4. Returns float 0-1. Low p = pattern is non-random.

### run_query(trade_set: EnrichedTradeSet, f: ConstellationFilter) -> ConstellationResult
Calls apply_filter, compute_metrics on both sets, permutation_test.
Assembles ConstellationResult with 8 MetricRows + permutation_p_value.

---

## Verification

```bash
python -c "import py_compile; py_compile.compile('vince/query_engine.py', doraise=True); print('OK')"
python tests/test_b5_query_engine.py
```

Test cases (50 synthetic enriched rows):
1. apply_filter with grade filter -> union of matched + complement = full set
2. compute_metrics returns dict with all 8 keys, all floats
3. run_query with open filter (all None) -> matched_count = 50
4. permutation_test returns float in [0, 1]
5. ConstellationResult instance returned correctly

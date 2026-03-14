# Trade Chart Report v3 — TDI Module Swap Build Log

**Date:** 2026-03-14
**Session type:** Build + Audit

---

## What was done

Surgical TDI swap: replaced broken inline TDI (24 lines) with import from `signals/tdi.py` module.

### v2 problems fixed
- ewm RSI (wrong smoothing) -> Wilder RMA (correct, matches Pine `ta.rsi()`)
- fast_ma_len=7, slow_ma_len=2 (swapped) -> fast=2, slow=8 (correct)
- RSI period 14 -> 13 (cw_trades preset)
- BB stdev ddof=1 (pandas default, wrong) -> ddof=0 (matches Pine `stdev()`)
- No zones/divergence/cross signals -> 24 TDI columns now available

### Changes applied (3 surgical edits to v2 copy)

1. **sys.path + import** (lines 62-69): Module-level `from signals.tdi import compute_tdi` with path injection matching existing `detect_signals` pattern.

2. **TDI block replacement** (lines 308-324): Removed 24-line inline block, replaced with `compute_tdi(df, {"tdi_preset": "cw_trades"})` call + 12 column alias mappings in try/except.

3. **"TDI 14" -> "TDI 13"** (3 occurrences): subplot_titles (line 427), panel comment (line 773), toggle label (line 1035).

### Column mapping (verified against tdi.py source)

| v3 chart column | tdi.py source column | Purpose |
|---|---|---|
| `tdi_rsi` | `tdi_rsi` | RSI line |
| `tdi_upper` | `tdi_bb_upper` | BB upper band |
| `tdi_lower` | `tdi_bb_lower` | BB lower band |
| `tdi_mid` | `tdi_bb_mid` | BB midline |
| `tdi_fast` | `tdi_fast_ma` | SMA(RSI, 2) — green line |
| `tdi_slow` | `tdi_signal` | SMA(RSI, 8) — red line |

Extra columns computed but not yet rendered: `tdi_zone`, `tdi_cloud_bull`, `tdi_long`, `tdi_short`, `tdi_bull_div`, `tdi_bear_div`.

### Validation

- py_compile: PASS
- Runtime test: 25 trades (2026-03-11), all charts built, HTML 5.2MB
- grep confirmed "TDI 13" in output HTML (3 occurrences)

### Audit result

No bugs. One MEDIUM note: `compute_tdi` copies entire DataFrame internally (wasteful but harmless for 150-bar charts). Silent fix: BB stdev ddof=0 now correct (v2 used ddof=1).

## Files

| File | Action |
|---|---|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report_v3.py` | CREATED (copy of v2 + 3 edits) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\tdi.py` | READ ONLY (import target) |
| v1, v2 | NOT TOUCHED |

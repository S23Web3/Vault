# Dashboard v3 -- Suggestions & Add-ons

**Date**: 2026-02-13
**Source**: Code review of v1 (1499L) and v2 (1534L), cross-referenced with v3 build plan
**Status**: SUGGESTIONS ONLY -- not yet approved for build

---

## Code Debt Carried from v1/v2

### 1. render_detail_view() extraction -- CRITICAL

v1 lines 1354-1499 are a full copy-paste of the 5-tab rendering from single mode (lines 532-1111). Comment at line 1408 says "In a future refactor, extract into a render_5tabs() function." That is ~400 lines of duplication. v3 must extract into a single function called from both single coin and sweep drill-down.

### 2. Sweep `except Exception: pass` -- silent failures

v1 line 1307 / v2 line 1342. Coins that error during sweep just vanish. No logging, no count, no visibility. Need:
- `error_count` counter displayed in progress UI
- Failed symbols logged to `logs/dashboard.log`
- `status` column in sweep CSV: `"ok"` or `"error: {reason}"`
- "X coins failed" shown in results summary

### 3. Sweep detail ML tabs disabled

v1 lines 1494-1498 show `st.info("ML Meta-Label analysis available in single-coin mode.")` for tabs 4 and 5 in sweep_detail mode. Once render_detail_view() is extracted, there is no reason to gate these. v3 should enable all 5 analysis tabs for sweep drill-down.

### 4. safe_plotly_chart() defined but never called

v2 defines the wrapper at line 69-75 but all ~20 plotly_chart calls still use plain `st.plotly_chart`. v3 should use the wrapper consistently or remove it.

### 5. Normalizer/Upload Data integration must migrate

v1 lines 1181-1262 (~80 lines) handle Upload Data flow: detect_format preview, symbol input, convert button. v3 build plan mentions sweep source radio but does not detail this flow. Must be preserved in Batch Sweep tab.

---

## New Suggestions for v3

### A. Date Range Filter in Sidebar -- SHOULD

Currently backtests ALL cached data (up to 1 year). Add start/end date pickers. Lets user test "last 30 days" vs "last 90 days" vs "last 6 months" without modifying cache.

Implementation: `df = df[(df['datetime'] >= start) & (df['datetime'] <= end)]` before passing to `run_backtest()`. Two `st.sidebar.date_input()` widgets.

**Impact**: High user value. **Effort**: Low (5 lines of code + 2 sidebar widgets).

### B. Param Presets (Save/Load) -- SHOULD

30+ parameters in the sidebar. Every session they must be re-entered. Add:
- "Save Preset" button -> writes `data/presets/{name}.json`
- "Load Preset" dropdown -> reads JSON, populates sidebar defaults
- Ship 2-3 defaults: "Rebate Farm" (tight SL/TP, max cooldown), "Conservative" (wide SL, no TP), "Aggressive" (tight SL, TP=2.0)

**Impact**: Saves 2-3 minutes per session. **Effort**: Medium (save/load JSON, sidebar reload).

### C. Sweep Stop Button -- SHOULD

v3 plan mentions [Stop] button but no implementation detail. Pattern:
```python
if st.button("Stop Sweep"):
    st.session_state["sweep_stop"] = True
# In sweep loop:
if st.session_state.get("sweep_stop"):
    break  # remaining coins stay for resume
```

**Impact**: Prevents user from having to close/reopen browser to stop a sweep. **Effort**: Low.

### D. Sweep Results Comparison (A/B Testing) -- NICE

Load two completed sweep CSVs (different params_hash values) side by side. Show delta per coin: which improved, which degraded. Table columns: Symbol, Net_A, Net_B, Delta, WR_A, WR_B.

Useful for answering "did changing SL from 2.0 to 2.5 help?" across all coins.

**Impact**: Medium (saves manual spreadsheet work). **Effort**: Medium.

### E. Top N Equity Curve Overlay -- NICE

In Results Explorer / sweep results: select top 5 coins, overlay their equity curves in one plotly chart. Currently can only see one at a time via drill-down.

**Impact**: Visual portfolio insight. **Effort**: Low (plotly multi-trace, data already available).

### F. Commission Sensitivity Row -- NICE

Below existing commission metrics, add one-liner: "If rebate drops to 50%: Net = $X". Shows how fragile the edge is. One recalculation of `net_pnl_after_rebate` with different `rebate_pct`.

**Impact**: Risk awareness. **Effort**: Trivial (3 lines of code).

### G. Timeframe Per Tab -- LATER

Currently single coin and sweep share one timeframe radio in sidebar. Allow independent selection so user can sweep on 5m while testing single coin on 1m.

**Impact**: Niche. **Effort**: Low but adds complexity to shared sidebar state.

---

## Priority Matrix

| Priority | Item | Category | Impact | Effort |
|----------|------|----------|--------|--------|
| MUST | render_detail_view() extraction | Code debt | Kills 400L duplication | Medium |
| MUST | Sweep error tracking | Code debt | Silent failures are dangerous | Low |
| MUST | Enable ML tabs in sweep detail | Code debt | Already built, just gated | Trivial |
| MUST | Use safe_plotly_chart() consistently | Code debt | v2 defined it, v3 should use it | Low |
| MUST | Preserve normalizer/upload flow | Code debt | 80 lines must migrate | Low |
| SHOULD | Date range filter | New feature | High user value | Low |
| SHOULD | Param presets | New feature | Saves time across sessions | Medium |
| SHOULD | Sweep stop button | New feature | Usability | Low |
| NICE | Sweep comparison | New feature | A/B testing params | Medium |
| NICE | Top N equity overlay | New feature | Visual insight | Low |
| NICE | Commission sensitivity | New feature | Risk awareness | Trivial |
| LATER | Timeframe per tab | New feature | Niche use case | Low |

---

## Notes

- All "MUST" items are code debt fixes, not new features. They should be in v3 regardless.
- "SHOULD" items are low-hanging fruit with high user value.
- "NICE" and "LATER" items can wait for v4.
- This file is a living document. Update status column as items get built.

# Dashboard v3 -- Suggestions & Add-ons

**Date**: 2026-02-13
**Source**: Code review of v1 (1499L) and v2 (1534L), cross-referenced with v3 build plan
**Status**: INTEGRATED INTO DASHBOARD-V3-BUILD-SPEC.md

---

## Code Debt Carried from v1/v2

### 1. render_detail_view() extraction -- CRITICAL → CD-1 in spec

v1 lines 1354-1499 are a full copy-paste of the 5-tab rendering from single mode (lines 532-1111). ~400 lines of duplication. v3 must extract into a single function called from both single coin and sweep drill-down.

### 2. Sweep `except Exception: pass` -- silent failures → CD-2 in spec

v1 line 1307 / v2 line 1342. Need error_count, logging, status column in CSV.

### 3. Sweep detail ML tabs disabled → CD-3 in spec

Once render_detail_view() is extracted, enable all 5 tabs for sweep drill-down.

### 4. safe_plotly_chart() defined but never called → CD-4 in spec

v2 defines wrapper but all ~20 calls still use plain st.plotly_chart.

### 5. Normalizer/Upload Data integration must migrate → CD-5 in spec

v1 lines 1181-1262 (~80 lines) handle Upload Data flow. Must preserve in Tab 2.

---

## New Suggestions

### A. Date Range Filter → S-1 in spec (SHOULD, in v3)
### B. Param Presets (Save/Load) → S-2 in spec (SHOULD, in v3)
### C. Sweep Stop Button → S-3 in spec (SHOULD, in v3)
### D. Sweep Results Comparison → v4 candidate
### E. Top N Equity Curve Overlay → v4 candidate
### F. Commission Sensitivity Row → v4 candidate
### G. Timeframe Per Tab → v4 candidate

---

## Priority Matrix

| Priority | Item | Status |
|----------|------|--------|
| MUST | CD-1 render_detail_view() | In v3 spec |
| MUST | CD-2 sweep error tracking | In v3 spec |
| MUST | CD-3 ML tabs in sweep detail | In v3 spec |
| MUST | CD-4 safe_plotly_chart() | In v3 spec |
| MUST | CD-5 normalizer migration | In v3 spec |
| SHOULD | S-1 date range filter | In v3 spec |
| SHOULD | S-2 param presets | In v3 spec |
| SHOULD | S-3 sweep stop button | In v3 spec |
| NICE | D sweep comparison | Deferred to v4 |
| NICE | E equity overlay | Deferred to v4 |
| NICE | F commission sensitivity | Deferred to v4 |
| LATER | G timeframe per tab | Deferred to v4 |

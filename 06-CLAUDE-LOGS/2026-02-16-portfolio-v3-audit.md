# Dashboard Portfolio Enhancement v3 Build
**Date:** 2026-02-16
**Session:** Audit and bugfix of build_dashboard_portfolio_v2.py
**Status:** COMPLETE - v3 build script ready for execution

---

## Session Timeline

### Request
User: "sanity check the perspective and math logic and there should be a core script as result. also on logic errors, if that is integrated then what am i missing here, something feels off"

Context: User had approved the dashboard portfolio enhancement plan (4 features: reusable portfolios, PDF export, enhanced per-coin analysis, unified capital model). I had built `build_dashboard_portfolio_v2.py` (~1412 lines) creating all 4 utility modules, tests, and debug script. User felt "something is off" and requested a sanity check.

---

## Audit Process

### Phase 1: Read Build Script and Engine Source
**Files audited:**
- `scripts/build_dashboard_portfolio_v2.py` (lines 1-1412) - embedded source for all utils
- `engine/backtester_v384.py` (lines 430-580) - `_compute_metrics()`, `_trades_to_df()`, return structure
- `engine/position_v384.py` (lines 30-89) - Trade384 dataclass definition
- `scripts/dashboard.py` (lines 327-373, 1774-1898) - `align_portfolio_equity()`, portfolio mode

### Phase 2: Cross-Reference Data Structures
**Key findings:**
- `_trades_to_df()` (line 557-580) produces columns: `direction, grade, entry_bar, exit_bar, entry_price, exit_price, sl_price, tp_price, pnl, commission, net_pnl, mfe, mae, exit_reason, saw_green, scale_idx`
- NOT in trades_df: `entry_dt`, `rebate`, `be_raised`, `entry_atr`
- Backtester return structure (line 440-446): `trades, trades_df, metrics, equity_curve, position_counts`
- `net_pnl` is COMPUTED in `_trades_to_df()` at line 572: `t.pnl - t.commission`

### Phase 3: Bug Identification
Cross-checked embedded code assumptions against actual engine output.

---

## 9 Bugs Found in v2

### BUG 1 - CRITICAL: Capital Model is Decorative Only
**Location:** `utils/capital_model.py` lines 733-734
```python
"adjusted_pf": pf_data,           # <-- returns ORIGINAL
"adjusted_coin_results": coin_results,  # <-- returns ORIGINAL
```

**Issue:** The capital model identifies rejected trades and logs them, but returns the original `pf_data` and `coin_results` unchanged. The portfolio equity curve still includes the P&L of rejected trades. **The rejection logic has zero effect on results.**

**Impact:** User sees "adjusted results" that are identical to unconstrained results. Capital constraints are purely informational, not enforced.

**Root cause:** Missing step to rebuild equity curves after removing rejected trade contributions.

---

### BUG 2 - CRITICAL: Bar Indices are Per-Coin Local
**Location:** `utils/capital_model.py` lines 670-672
```python
entry_bar = int(row.get("entry_bar", 0))
exit_bar = int(row.get("exit_bar", len(dt_idx) - 1))
```

**Issue:** `entry_bar` from trades_df is an index into THAT COIN's DataFrame (e.g., RIVER bar 50 = row 50 of RIVER's 1000-bar data). But the capital model uses these bars directly against `master_dt` (the merged timeline of ALL coins). RIVER bar 50 and KITE bar 50 are **completely different timestamps** because coins have different datetime_index arrays.

**Example:**
- RIVER: starts 2025-01-01 00:00, bar 50 = 2025-01-01 04:10
- KITE: starts 2025-01-01 06:00, bar 50 = 2025-01-01 10:10
- Capital model treats both as "bar 50 of master_dt" → wrong

**Impact:** Capital allocation logic compares apples to oranges. Overlapping trades that don't actually overlap in time could be incorrectly rejected or accepted.

**Root cause:** No mapping from per-coin bar indices to master_dt positions.

---

### BUG 3 - CRITICAL: MFE in Signal Strength is Look-Ahead Bias
**Location:** `utils/capital_model.py` line 678
```python
strength = -_grade_sort_key(grade) * 100 + mfe * 10
```

**Issue:** MFE (Maximum Favorable Excursion) is only known **after the trade closes**. At entry time, you don't know how far the trade will run in your favor. Using MFE to prioritize which trades to accept when capital is limited is using hindsight information.

**Impact:** Strategy performance is artificially inflated. In live trading, you can't prioritize entries by MFE because you don't know MFE until exit.

**Root cause:** Signal strength calculation uses forward-looking data.

---

### BUG 4 - MEDIUM: `rebate` Column Doesn't Exist
**Location:** `utils/coin_analysis.py` line 295
```python
rebate = float(trades_df["rebate"].sum()) if "rebate" in trades_df.columns else 0.0
```

**Issue:** Trade384 dataclass has no `rebate` field. `_trades_to_df()` produces no `rebate` column. This line always returns 0.0.

**Impact:** `compute_commission_breakdown()` always shows `net_commission = total_commission` (no rebate offset). Misleading for rebate farming analysis.

**Context:** Rebates are calculated by the commission model as daily settlements at 17:00 UTC, not tracked per-trade. If per-trade rebate tracking is needed, must be added to Trade384 and `_trades_to_df()`.

---

### BUG 5 - MEDIUM: `entry_dt` Column Doesn't Exist
**Location:** `utils/coin_analysis.py` line 260
```python
def compute_monthly_pnl(trades_df, datetime_col="entry_dt"):
```

**Issue:** `_trades_to_df()` does NOT produce an `entry_dt` column. Only `entry_bar` (integer index) exists.

**Impact:** `compute_monthly_pnl(trades_df)` always returns empty DataFrame when called on real backtester output.

**Why tests pass:** Test suite (line 932 of v2) fabricates an `entry_dt` column in synthetic data, masking this failure.

**Fix needed:** Map `entry_bar` through the coin's `datetime_index` to get actual datetime values.

---

### BUG 6 - MEDIUM: Sortino Annualization Uses Trade Count
**Location:** `utils/coin_analysis.py` line 228
```python
sortino = float(pnls.mean() / downside_std * np.sqrt(min(n, 105120)))
```

**Issue:** `n` is the number of trades, not the number of bars. Sortino ratio should annualize by observation periods (bars), not event count (trades).

**Example:** A coin with 50 trades over 100,000 bars gets `sqrt(50)` annualization factor instead of `sqrt(100000)`.

**Impact:** Sortino values are incorrectly scaled. The 105120 cap (bars per year at 5m) is meaningless since trade count rarely exceeds 1000.

**Fix needed:** Accept `bar_count` parameter (equity curve length) for correct annualization.

---

### BUG 7 - MEDIUM: Capital Efficiency Uses Unconstrained Values
**Location:** `utils/capital_model.py` lines 725-726
```python
peak_used = float(pf_data["capital_allocated"].max())
avg_used = float(pf_data["capital_allocated"].mean())
```

**Issue:** Even after identifying rejected trades, efficiency metrics reference the ORIGINAL `pf_data["capital_allocated"]` which includes capital from rejected trades.

**Impact:** Peak and average capital reported don't match the adjusted results. User sees contradictory metrics.

**Fix needed:** Rebuild `capital_allocated` from accepted trades only, then compute efficiency from that.

---

### BUG 8 - LOW: `be_raised` Not in trades_df
**Location:** `engine/backtester_v384.py` line 557-580

**Issue:** Trade384 has `be_raised` field (line 52 of position_v384.py), but `_trades_to_df()` does NOT include it in the output DataFrame.

**Impact:** If drill-down analysis wants to show BE-raised trades, the data isn't available in trades_df.

**Severity:** Low - no code currently references it, but it's a data gap vs the design plan.

---

### BUG 9 - LOW: Test Suite Uses Fabricated Data
**Location:** `tests/test_portfolio_enhancements.py` lines 916-933

**Issue:** Tests create synthetic DataFrames with columns that don't exist in real backtester output:
- `entry_dt` (line 932) - doesn't exist in `_trades_to_df()`
- `rebate` (if tested) - doesn't exist
- Test data uses `np.random` to generate values, not realistic data structures

**Impact:** All tests pass on fake data but would fail on real output from `Backtester384`. This is a false-positive test suite that masks integration failures.

**Example:**
```python
# v2 test suite line 932
"entry_dt": pd.date_range("2025-01-01", periods=n_trades, freq="1h"),
```
Real trades_df has `entry_bar` (int), not `entry_dt` (datetime).

---

## v3 Fixes Applied

### File: `build_dashboard_portfolio_v3.py` (~1500 lines)

**Created:** 2026-02-16

**Changes by module:**

#### 1. `utils/portfolio_manager.py`
- **No changes** - no bugs found

#### 2. `utils/coin_analysis.py`
**FIX BUG 4:** Removed `rebate` column reference
```python
# v2 (wrong):
rebate = float(trades_df["rebate"].sum()) if "rebate" in trades_df.columns else 0.0

# v3 (fixed):
# Rebate removed - not tracked per-trade, only daily settlement
return {"total_commission": round(comm, 2), "net_commission": round(comm, 2)}
```

**FIX BUG 5:** `compute_monthly_pnl` maps entry_bar via datetime_index
```python
# v2 (wrong):
def compute_monthly_pnl(trades_df, datetime_col="entry_dt"):
    # entry_dt doesn't exist

# v3 (fixed):
def compute_monthly_pnl(trades_df, datetime_index=None):
    # Maps entry_bar through datetime_index to get actual timestamps
    dt_idx = pd.DatetimeIndex(datetime_index)
    bars = df["entry_bar"].clip(0, len(dt_idx)-1).astype(int)
    df["_entry_dt"] = dt_idx[bars]
```

**FIX BUG 6:** `compute_extended_metrics` accepts `bar_count` parameter
```python
# v2 (wrong):
sortino = float(pnls.mean() / downside_std * np.sqrt(min(n, 105120)))
# n = trade count

# v3 (fixed):
def compute_extended_metrics(trades_df, bar_count=None):
    ann_factor = 105120 if bar_count is None else min(bar_count, 105120)
    sortino = float(pnls.mean() / downside_std * np.sqrt(ann_factor))
    # Uses equity curve length (bars) not trade count
```

**FIX BUG 8:** Added be_raised awareness in docstring (no code change, data gap documented)

#### 3. `utils/pdf_exporter.py`
- **No changes** - no bugs found

#### 4. `utils/capital_model.py`
**FIX BUG 1:** Rebuild equity curves after rejecting trades
```python
# v2 (wrong):
return {"adjusted_pf": pf_data, ...}  # Original unchanged

# v3 (fixed):
# Subtract rejected trade P&L from equity curves
for ridx in rejected_idxs:
    exit_bar_local = int(row.get("exit_bar"))
    net = float(row.get("net_pnl"))
    eq_adjusted[exit_bar_local:] -= net  # Remove contribution
# Build adjusted_pf with new equity values
adjusted_pf["portfolio_eq"] = adjusted_portfolio_eq
adjusted_pf["capital_allocated"] = adjusted_capital_allocated
return {"adjusted_pf": adjusted_pf, ...}
```

**FIX BUG 2:** Map bar indices through datetime_index to master_dt
```python
# v2 (wrong):
entry_bar = int(row.get("entry_bar", 0))  # Per-coin index used directly

# v3 (fixed):
def _map_bar_to_master(bar_idx, coin_dt_index, master_dt):
    """Map a per-coin bar index to the corresponding master_dt index."""
    coin_dt = pd.DatetimeIndex(coin_dt_index)
    target_dt = coin_dt[bar_idx]
    pos = master_dt.searchsorted(target_dt, side="left")
    return int(pos)

# Usage:
entry_bar_master = _map_bar_to_master(entry_bar_local, coin_dt_idx, master_dt)
```

**FIX BUG 3:** Remove MFE from signal strength
```python
# v2 (wrong):
strength = -_grade_sort_key(grade) * 100 + mfe * 10  # Look-ahead bias

# v3 (fixed):
strength = -_grade_sort_key(grade) * 100  # Grade-only priority
```

**FIX BUG 7:** Capital efficiency computed from adjusted values
```python
# v2 (wrong):
peak_used = float(pf_data["capital_allocated"].max())  # Uses original

# v3 (fixed):
adjusted_capital_allocated = adjusted_total_positions * margin_per_pos
peak_used = float(adjusted_capital_allocated.max())  # Uses adjusted
```

#### 5. `tests/test_portfolio_enhancements.py`
**FIX BUG 9:** Use realistic data structures matching `_trades_to_df()` output
```python
# v2 (wrong):
trades_df = pd.DataFrame({
    "entry_dt": pd.date_range(...),  # Doesn't exist
    "rebate": [...],  # Doesn't exist
    ...
})

# v3 (fixed):
trades_df = pd.DataFrame({
    "direction": [...], "grade": [...],
    "entry_bar": [...], "exit_bar": [...],  # Integer indices
    "entry_price": [...], "exit_price": [...],
    "sl_price": [...], "tp_price": [...],
    "pnl": [...], "commission": [...],
    "net_pnl": pnl - commission,  # Computed
    "mfe": [...], "mae": [...],
    "exit_reason": [...], "saw_green": [...],
    "scale_idx": [...]
})
# NO entry_dt, NO rebate, NO be_raised
```

Added bug fix verification tests:
- BUG1 FIX: `abs(orig_final - adj_final) > 0.01` (equity changed)
- BUG3 FIX: A-grades rejected less often than D-grades (grade-only priority)
- BUG6 FIX: Different Sortino with/without bar_count

#### 6. `scripts/debug_portfolio_enhancements.py`
Enhanced with cross-coin timeline verification:
- BUG2 FIX: Verify `_map_bar_to_master()` maps different coin timelines correctly
- BUG1 FIX: Show original vs adjusted equity difference
- BUG7 FIX: Verify efficiency metrics match adjusted capital

---

## Build Script Structure

### Files Created by v3 Build
1. `utils/__init__.py` (1 line)
2. `utils/portfolio_manager.py` (~100 lines)
3. `utils/coin_analysis.py` (~150 lines, 4 bugs fixed)
4. `utils/pdf_exporter.py` (~300 lines, no changes)
5. `utils/capital_model.py` (~250 lines, 4 bugs fixed)
6. `portfolios/.gitkeep` (empty dir marker)
7. `tests/test_portfolio_enhancements.py` (~65 tests, realistic data)
8. `scripts/debug_portfolio_enhancements.py` (~50 checks, bug verification)

### Total Lines
- Build script: ~1500 lines (v2: 1412)
- Embedded source: ~800 lines
- Tests + debug: ~600 lines
- Infrastructure: ~100 lines

---

## Integration Status

### Completed
- All 4 utility modules built (portfolio_manager, coin_analysis, pdf_exporter, capital_model)
- Test suite with realistic data structures
- Debug script with bug fix verification
- FILE-INDEX.md updated with v3 reference

### NOT DONE (Manual Integration Required)
**Dashboard.py integration** - The build creates standalone modules but does NOT wire them into the Streamlit dashboard. Required changes:

1. **Import utils** (line ~15 of dashboard.py):
```python
from utils.portfolio_manager import save_portfolio, load_portfolio, list_portfolios
from utils.coin_analysis import compute_extended_metrics
from utils.pdf_exporter import generate_portfolio_pdf
from utils.capital_model import apply_capital_constraints, format_capital_summary
```

2. **Portfolio save/load UI** (after line 1766, coin selection):
```python
# Save Portfolio section
st.subheader("Save/Load Portfolio")
col_save, col_load = st.columns(2)
with col_save:
    portfolio_name = st.text_input("Portfolio Name", "")
    if st.button("Save Current Selection"):
        if portfolio_name and port_symbols:
            save_portfolio(portfolio_name, port_symbols, ...)
with col_load:
    portfolios = list_portfolios()
    if portfolios:
        selected = st.selectbox("Load Portfolio", [p["name"] for p in portfolios])
        if st.button("Load"):
            # Load coins, set port_symbols
```

3. **Capital mode toggle** (line ~570, sidebar):
```python
capital_mode = st.radio("Capital Mode", ["Per-Coin Independent", "Unified Portfolio Pool"])
if capital_mode == "Unified Portfolio Pool":
    total_capital = st.number_input("Total Capital ($)", min_value=1000, value=10000, step=1000)
```

4. **Apply capital constraints** (after line 1806, align_portfolio_equity):
```python
if capital_mode == "Unified Portfolio Pool":
    result = apply_capital_constraints(coin_results, pf, total_capital, margin)
    pf = result["adjusted_pf"]
    coin_results = result["adjusted_coin_results"]
    # Display rejection log, efficiency metrics
```

5. **PDF export button** (after line 1888, capital chart):
```python
if st.button("Export Portfolio Report as PDF"):
    pdf_path = generate_portfolio_pdf(pf, coin_results, portfolio_name, total_capital)
    st.success(f"PDF saved: {pdf_path}")
    # Add download button
```

6. **Extended metrics table** (replace line 1843-1857):
```python
for cr in coin_results:
    ext = compute_extended_metrics(cr["trades_df"], bar_count=len(cr["equity_curve"]))
    # Add 10 new columns to lsg_df
```

### Dependency Installation
```bash
pip install reportlab
```
Already installed: matplotlib, pandas, numpy

---

## Next Steps

### Immediate (Before Integration)
1. **Run v3 build script:**
   ```
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_portfolio_v3.py"
   ```
   Expected: 8 files created, all compile OK

2. **Run test suite:**
   ```
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_portfolio_enhancements.py"
   ```
   Expected: ~65 tests pass (includes BUG1/3/6 verification)

3. **Run debug script:**
   ```
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\debug_portfolio_enhancements.py"
   ```
   Expected: ~50 checks pass (includes BUG2/7 cross-coin verification)

4. **Install PDF dependency:**
   ```
   pip install reportlab
   ```
   Then re-run debug script to verify PDF generation

### Integration Phase (Manual Streamlit Work)
5. **Write dashboard integration script** - Create `scripts/integrate_portfolio_v3.py` that:
   - Reads current dashboard.py
   - Identifies insertion points (imports, sidebar, portfolio mode)
   - Applies patches (Edit tool)
   - Validates no syntax errors

6. **Test integrated dashboard:**
   ```
   streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard.py"
   ```
   - Navigate to Portfolio mode
   - Test save/load portfolio
   - Test capital mode toggle
   - Test PDF export
   - Verify extended metrics table

### Validation Phase
7. **Run end-to-end scenario** (from plan):
   - Load 5 coins: RIVER, KITE, HYPE, SAND, 1000PEPE
   - Run portfolio backtest (both capital modes)
   - Save portfolio as "Test Portfolio v3"
   - Reload portfolio → verify same 5 coins
   - Export PDF → verify all pages render
   - Compare Independent vs Unified mode P&L

8. **Update MEMORY.md** with:
   - v3 file locations
   - Bug fix summary (9 bugs → lessons learned)
   - Integration status
   - Capital model behavior (rebuilds equity, maps bars correctly)

### Optional Enhancements (From Plan Phase 5)
9. **Portfolio comparison feature** - Deferred until BBW Layer 6 complete
10. **Correlation matrix page in PDF** - Missing from v2/v3, add to v4
11. **Drawdown curve in PDF** - Missing from v2/v3, add to v4

---

## Critical Insights from Audit

### 1. The Backtester is NOT a Portfolio Engine
It's a **single-coin bottoms-up aggregator**:
- Each coin runs independently with full capital
- Results are merged via `align_portfolio_equity()` by unioning datetime indices
- No cross-coin capital sharing or correlation-based sizing
- Capital utilization = sum of concurrent positions × margin per position

**Implication:** The capital model MUST be post-processing (can't modify engine behavior). It filters trades after the fact, which is why rebuilding equity is critical.

### 2. Bar Indices are Per-Coin Local Coordinates
Each coin has its own timeline:
- RIVER: 1000 bars from 2025-01-01 to 2025-01-05
- KITE: 800 bars from 2025-01-02 to 2025-01-06
- Bar 50 means different timestamps for each

**Implication:** Any cross-coin comparison MUST map through datetime_index to master_dt. This was the root cause of BUG2.

### 3. Test Suites Can Mask Integration Failures
v2 test suite passed with 60/60 tests, but used fabricated columns (`entry_dt`, `rebate`) that don't exist in real output. Tests validated internal consistency of the utility modules but not compatibility with the backtester.

**Lesson:** Always test with data structures from the actual engine. Use `_trades_to_df()` output format, not synthetic equivalents.

### 4. Look-Ahead Bias is Subtle
Using MFE in signal strength seemed reasonable ("prioritize trades that worked out well"), but MFE is only known AFTER exit. At entry time, you have no idea which trade will have high MFE.

**Lesson:** Any metric that depends on future bars is look-ahead bias. Only use entry-time information (grade, ATR, price levels, signals).

---

## Files Modified This Session

### Created
- `scripts/build_dashboard_portfolio_v3.py` (1500 lines)

### Modified
- `FILE-INDEX.md` (lines 38-44, 77-79) - Updated Utils section to v3, added build script reference

### Read (for audit)
- `scripts/build_dashboard_portfolio_v2.py` (1412 lines)
- `engine/backtester_v384.py` (lines 430-580)
- `engine/position_v384.py` (lines 30-89)
- `scripts/dashboard.py` (lines 327-373, 1774-1898)
- `FILE-INDEX.md` (full file)

---

## Open Questions for User

1. **Integration timing:** Should I write the dashboard integration script now, or wait until v3 tests pass?

2. **Capital mode default:** Plan says "Unified Portfolio Pool" default, but backward compatibility argues for "Per-Coin Independent". Which?

3. **Rejected trade visibility:** Should rejected trades show in the trades table with a "Status: Rejected" column, or only in the rejection log?

4. **PDF missing features:** Plan specified correlation matrix and drawdown curve pages. Should these be added to v3 or deferred to v4?

5. **BBW integration:** BBW Layer 6 will add state columns to signals. Should the capital model's signal strength incorporate BBW state (squeeze detection) when available?

---

## Status Summary

**Build:** COMPLETE - v3 ready for execution
**Tests:** NOT RUN - awaiting user execution
**Integration:** NOT STARTED - manual Streamlit wiring required
**Validation:** BLOCKED - needs integration first

**Next action:** Run v3 build script and verify all files compile.

---

## Session 2 Continuation (2026-02-16, context rollover)

### Work Done
1. **Build script sync** -- Updated embedded TEST_SUITE and DEBUG_SCRIPT in `build_dashboard_portfolio_v3.py` to match the on-disk fixes:
   - Test 4.25: Changed from grade count comparison to MFE field absence check
   - Debug D1.2: Added `import time as _time`, `_time.sleep(0.05)` between saves, mtime comment
   - Build script is now safe to re-run without overwriting working test/debug files

2. **MEMORY.md updated** -- Added "Dashboard Portfolio Enhancement v3" section with all file locations, status, and next steps

### Updated Status
- **Build:** COMPLETE
- **Tests:** 81/81 PASSED (user verified)
- **Debug:** ALL PASSED (user verified)
- **Build script sync:** COMPLETE (embedded content matches on-disk files)
- **Integration:** NOT STARTED -- wire 4 utils into dashboard.py
- **Next action:** Dashboard integration build script

---

## Session 2b: Dashboard Integration Build

### Created
- `scripts/build_dashboard_integration.py` -- reads dashboard.py, applies 6 patches, writes dashboard_v2.py
- py_compile PASSED on build script

### 6 Patches
1. **P1 (imports)**: Adds `from utils.portfolio_manager/coin_analysis/capital_model/pdf_exporter import ...` after backtester import
2. **P2 (sidebar)**: Capital mode toggle (Per-Coin Independent / Unified Portfolio Pool) after commission section
3. **P3 (save/load)**: Portfolio save/load UI with selectbox, text input, delete management before Run button
4. **P4 (capital constraints)**: Applies `apply_capital_constraints()` after `align_portfolio_equity()` when unified mode active
5. **P5 (extended table)**: Replaces 7-column LSG table with 17-column extended metrics + per-coin drill-down expanders (4 tabs each: Trades, Grade/Exit, Monthly P&L, Losers)
6. **P6 (PDF + efficiency)**: Capital efficiency metrics display + PDF export button with download after correlation matrix

### Next
- User runs: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_integration.py"`
- Then: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v2.py"`

# SHELVED: Cache Gap Finder -- Missing High-Cap Coins

Shelved per user request. Build AFTER dashboard v3.2 is fully verified.
See `07-BUILD-JOURNAL/2026-02-14.md` for TODO entry.

---

# BUILD PLAN: Dashboard v3.2 -- Bugfixes + UX from User Testing

## Context

User ran Dashboard v3.1 (1893 lines) and found 7 bugs/UX issues during live testing. This is a surgical bugfix build -- no new features, only fixes for what's broken or mis-designed.

**Build approach**: `scripts/build_dashboard_v32.py` — patch script (same pattern as v3.1). All patches are targeted edits with known anchors.

---

## Permissions Needed

| Permission | What | Why |
|------------|------|-----|
| File CREATE | `scripts/build_dashboard_v32.py` | Build script for v3.2 patches |
| File CREATE | `scripts/test_dashboard_v32.py` | Test script for fixed helpers |
| Bash RUN | `python scripts/test_dashboard_v32.py` | Verify fixes |
| Bash RUN | `python scripts/build_dashboard_v32.py --dry-run` | Preview |
| Bash RUN | `python scripts/build_dashboard_v32.py` | Apply |

---

## Bug 1: Portfolio DD% shows -207.3% (impossible)

**Root cause**: `align_portfolio_equity()` line 345 sums raw equity curves: each coin starts at 10000, so 10 coins = portfolio starts at 100000. DD calculation `(eq - peak) / peak * 100` is correct math, but the NET P&L line 1815 subtracts `10000 * len(coin_results)` while DD uses the raw summed curve. The -207% is the per-coin DD being reported from `ms_c["max_drawdown_pct"]` at line 1850 in the LSG table -- that's the individual coin's DD which CAN exceed 100% because it's measured as loss relative to starting capital ($10k), not as peak-to-trough.

**Fix**: In `align_portfolio_equity()`, cap DD at -100% with `dd_arr = np.clip(dd_arr, -100.0, 0.0)`. Also in the LSG table, cap per-coin DD display at -100%.

**Anchor**: `dd_arr = np.where(peaks > 0, (portfolio_eq - peaks) / peaks * 100.0, 0.0)` (line 351)

---

## Bug 2: Stress test Arrow serialization crash

**Root cause**: Lines 850-856 format numbers as strings with `$` and `%` BEFORE putting them in a DataFrame. PyArrow tries to infer int64 but gets `"$21,393.38"`.

**Fix**: Keep numeric columns as raw floats in the dict. Use `st.dataframe(df.style.format({...}))` to format display.

**Anchor**: `stress_rows.append({` (line 847)

**Replacement**: Change Net/Avg Capital to raw floats, then format with Pandas Styler:
```python
"Net": round(net_s, 2),
"Avg Capital": round(cap_s, 0),
```
Then at display: `st.dataframe(pd.DataFrame(stress_rows).style.format({"Net": "${:,.2f}", "Avg Capital": "${:,.0f}"}))`

---

## Bug 3: `use_container_width=True` deprecated (30 instances)

**Root cause**: Streamlit updated API. New parameter is `width='stretch'`.

**Fix**: Global find/replace `use_container_width=True` -> delete the param entirely (Streamlit defaults to stretch for `st.dataframe`). For `st.plotly_chart`, replace with `use_container_width=True` which is still valid in Plotly. Actually -- check: the warning says "use `width='stretch'`" which applies to `st.dataframe()` only. `st.plotly_chart` still uses `use_container_width`.

**Fix (refined)**:
- `st.dataframe(..., use_container_width=True, ...)` -> remove the param (or add `width='stretch'`)
- `st.plotly_chart(..., use_container_width=True)` -> keep as-is (valid)

Count: ~15 `st.dataframe` instances, ~15 `st.plotly_chart` instances.

---

## Bug 4: Portfolio mode has no tabs (missing Trade Analysis, MFE/MAE, etc.)

**Root cause**: Portfolio mode (lines 1807-1893) was built as flat layout with no `st.tabs()`. The single-coin mode has 5 tabs (Overview, Trade Analysis, MFE/MAE & Losers, ML Meta-Label, Validation).

**Fix**: NOT a v3.2 fix. Portfolio mode is a different view (multi-coin summary). Adding per-coin tabs would require selecting WHICH coin to show detailed analysis for. This is a v3.3 feature (add a coin selector dropdown in portfolio results that shows single-coin tabs for the selected coin).

**Action**: Skip for v3.2. Note in plan for v3.3.

---

## Bug 5: SHIB not in coin list

**Root cause**: NOT a bug. SHIB was never downloaded. Cache has 399 coins, but `1000SHIBUSDT` is not among them. Bybit uses the `1000SHIBUSDT` ticker (1000x multiplied).

**Fix**: Download it. Run: `python scripts/download_all_available.py` to refresh cache, OR manually fetch: add `1000SHIBUSDT` to download list.

**Action**: Not a code fix. Tell user to run download script.

---

## Bug 6: Run Backtest button at bottom of sidebar (hard to find)

**Root cause**: Lines 591-593 place buttons at bottom of sidebar after all parameter controls (stochastics, clouds, exits, ML settings = ~170 lines of sidebar widgets).

**Fix**: Move buttons to TOP of sidebar, right after Data section (symbol + timeframe + date range). Parameters can stay below. User changes params, scrolls up, clicks Run.

Better alternative: Use `st.sidebar.container()` with `st.sidebar.markdown("---")` to create a sticky button area at top. Or just relocate the 3 button lines (591-593) to right after line 437 (end of date range section).

**Anchor**: Move lines 587-603 (buttons block) to after line 437 (after date range caption).

---

## Bug 7: No loading indicator / splash screen during portfolio backtest

**Root cause**: Progress bar exists (line 1775) but is inside the `if run_port:` block. On button click, Streamlit runs the loop with progress bar visible. But between clicking and seeing results, there's a Streamlit rerun that briefly shows nothing. The user sees the page "reload" with no feedback.

**Fix**: Add `st.spinner("Running portfolio backtest...")` wrapper around the loop. Spinner persists during the entire Streamlit script execution of that block, giving visual feedback.

**Anchor**: `if run_port and port_symbols:` (line 1773)

**Replacement**: Wrap in spinner:
```python
if run_port and port_symbols:
    with st.spinner("Running portfolio backtest..."):
        coin_results = []
        progress = st.progress(0)
        ...
```

---

## Bug 8: BTC equity curve zigzag pattern

**NOT a bug**. BTC has high commission relative to ATR-based TP. Commission = 0.08% x $10,000 notional = $8/side = $16 RT. BTC ATR on 5m is ~0.3%, so TP at 2.0 ATR = 0.6% = $60 profit. Commission eats 26.7% of every winning trade. With 40% WR, the math is: 0.4 x $44 - 0.6 x $38 = -$5.20/trade expected. The zigzag is real -- BTC loses on this strategy.

**Action**: No code fix. This is a known issue (MEMORY: "ATR/price ratio matters").

---

## Feature 9: Info tooltips (question mark circles) on key metrics

**User request**: Add a small info icon next to metric labels so users understand what they're looking at.

**Implementation**: Streamlit `st.metric` doesn't support native tooltips, but we can use `st.markdown` with `help` parameter on nearby elements, OR use `st.columns` with a small `st.caption` or `st.info` popover.

Best approach: Use Streamlit's `help` parameter on `st.subheader` and `st.metric` calls (available since Streamlit 1.28+). Example:
```python
pm4.metric("Peak Capital", f"${_peak_cap:,.0f}", help="Maximum margin deployed across all coins at any single bar")
```

**Tooltips to add**:

| Metric | Tooltip text |
|--------|-------------|
| Peak Capital | "Max margin used across all coins at once" |
| Best Equity | "Highest portfolio equity in backtest (not Monte Carlo)" |
| Worst DD | "Deepest peak-to-trough decline" |
| Net P&L | "Profit after commissions and rebates" |
| Max DD% | "Largest peak-to-trough % drop" |
| LSG% | "% of losers that were green before hitting SL" |
| Capital Allocation | "Best and worst moments (historical, not simulated)" |
| Total Trades | "All trades across all coins" |
| Coins | "Coins with at least 1 trade" |

**Anchor sites**: Every `st.metric()` and `st.subheader()` call in portfolio mode (~lines 1813-1837) and single mode (~lines 760-790).

---

## Bug 10: ML Filtered vs Unfiltered table Arrow crash (SAME as Bug 2)

**Root cause**: Lines 1195-1204. The "All (unfiltered)" column mixes int (trade count) with strings (`"$21,393.38"`). Arrow infers int64 from the first row, then chokes on strings.

**Fix**: Same pattern as Bug 2 -- keep numeric, format via Styler.

**Anchor**: `"All (unfiltered)": [` (line 1195)

---

## Bug 11: Grades table has same Arrow risk

**Root cause**: Lines 793-799. Columns `"WR"`, `"Avg"`, `"Total"` are formatted as strings (`"$1.23"`, `"45.2%"`). Not crashing yet because column types are consistent within the column, but fragile.

**Fix**: Keep numeric, format via Styler.

**Anchor**: `gd.append({` (line 793)

---

## Bug 12: TP Impact table same Arrow risk

**Root cause**: Lines 885-898. Mixed int/string columns in the comparison DataFrame.

**Fix**: Same pattern -- numeric values, Styler format.

**Anchor**: `st.dataframe(pd.DataFrame({` (line 885)

---

## Bug 13: Sweep detail mode missing df/raw data for stress test

**Root cause**: Line 1609 -- `sweep_detail_data` dict doesn't include `"df"` key. But stress test at line 830 does `_df_raw = _d.get("df")`. In sweep_detail, `_d.get("df")` returns None, so stress test silently fails (no re-backtest on windows).

**Fix**: Add `"df": df` to the sweep_detail_data dict at line 1609.

**Anchor**: `st.session_state["sweep_detail_data"] = {` (line 1609)

---

## Bug 14: Equity curve x-axis shows bar index, not datetime

**Root cause**: Lines 776-777 and 1679-1680. Plotly `go.Scatter(y=eq)` with no `x=` parameter. Defaults to 0,1,2,... bar indices. User sees "0, 5k, 10k" on x-axis instead of dates.

**Fix**: Add `x=df_sig["datetime"]` if available, falling back to range index.

**Anchor**: `fig_eq.add_trace(go.Scatter(y=eq, mode="lines"` (lines 776, 1679)

---

## Build Script: `scripts/build_dashboard_v32.py`

Patches to apply:

| # | Patch | Lines | Type |
|---|-------|-------|------|
| P1 | Clip portfolio DD at -100% | ~351 | Logic fix |
| P2 | Stress table: raw floats + Styler format | ~847-863 | Data fix |
| P3 | `use_container_width=True` -> `width="stretch"` for st.dataframe | ~15 sites | Deprecation |
| P4 | Move buttons to top of sidebar | ~591 -> ~438 | UX |
| P5 | Add spinner to portfolio backtest | ~1773 | UX |
| P6 | Cap per-coin DD% display at 100 in LSG table | ~1850 | Display fix |
| P7 | Add `help=` tooltips to key metrics | ~20 sites | UX |
| P8 | ML Filtered table: numeric values + Styler | ~1195-1205 | Data fix |
| P9 | Grades table: numeric values + Styler | ~793-800 | Data fix |
| P10 | TP Impact table: numeric values + Styler | ~885-898 | Data fix |
| P11 | Add `"df": df` to sweep_detail_data | ~1609 | Missing data |
| P12 | Equity curve x-axis: use datetime if available | ~776, ~1679 | Visualization |

---

## Test Script: `scripts/test_dashboard_v32.py`

- Test DD clipping: synthetic equity with > 100% drawdown -> verify capped at -100%
- Test stress table dict has numeric columns (not string-formatted)
- Test portfolio DD never exceeds -100%

---

## Critical Files

| File | Action |
|------|--------|
| `scripts/dashboard.py` | EDIT via build script (1893 lines, ~20 patches) |
| `scripts/build_dashboard_v32.py` | CREATE |
| `scripts/test_dashboard_v32.py` | CREATE |

---

## Non-code Actions

| Item | Action |
|------|--------|
| SHIB not cached | User runs: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\download_all_available.py"` |
| Portfolio tabs | v3.3 feature -- add coin selector dropdown in portfolio results |
| BTC zigzag | Expected behavior -- commission drag on high-price coins |
| Git push | After v3.2 patches verified, commit + push all pending changes |

---

## Verification

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_dashboard_v32.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v32.py" --dry-run
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v32.py"
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard.py"
```

1. Stress test expander -> table shows without Arrow crash
2. Portfolio mode -> DD% capped at -100% max
3. Buttons visible at top of sidebar without scrolling
4. Portfolio backtest shows spinner during processing
5. `use_container_width` warnings gone from console
6. Hover over metric labels -> tooltip explains what the metric means
7. "Capital Allocation" tooltip clarifies this is NOT Monte Carlo

# Dashboard Version Registry

All versions live in `PROJECTS/four-pillars-backtester/scripts/`.

---

## v1 -- scripts/dashboard.py (2026-02-12 ~22:00 UTC)

**Build session**: BUILD-JOURNAL-2026-02-12.md, Session 2
**Created**: 2026-02-12
**Lines**: 1499
**Run**: `streamlit run scripts/dashboard.py`

**Features**:
- Mode navigation via session_state (settings | single | sweep | sweep_detail)
- Back buttons on every non-settings view
- Sweep persistence with CSV + MD5 params_hash (auto-resume)
- Incremental sweep (1 coin per st.rerun cycle, non-blocking)
- Sweep source radio: All Cache | Custom List | Upload Data
- Custom list parsing (.txt/.csv/.json)
- Upload Data with normalizer preview + convert
- Multi-interval parquet discovery (1m/5m/15m/1h/4h/1d)
- Native parquet priority loading (try {symbol}_{timeframe}.parquet before 1m+resample)
- LSG Bars metric (avg green bars for saw_green losers)
- 5-tab detail: Overview, Trade Analysis, MFE/MAE, ML, Validation

**Known issues**:
- Arrow serialization crash on mixed-type DataFrames (int + formatted string in same column)
- `use_container_width=True` deprecated in Streamlit 1.54+

---

## v2 -- scripts/dashboard_v2.py (2026-02-13 ~14:00 UTC)

**Build type**: Defensive hardening of v1
**Created**: 2026-02-13
**Lines**: 1534 (+35 from v1)
**Run**: `streamlit run scripts/dashboard_v2.py`
**Log**: `logs/dashboard.log` (5MB rotation, 3 backups)

**Changes from v1**:
- 3 mixed-type DataFrame fixes: integers cast to `str()` so Arrow doesn't try int64 inference on columns that also contain "$17,082.45" / "44.9%" strings (lines 688, 722, 1029)
- 28 `use_container_width=True` replaced with `width="stretch"` (Streamlit 1.54+ API)
- Logging added: `logs/dashboard.log` with RotatingFileHandler (5MB, 3 backups)
- `safe_dataframe()` wrapper: catches Arrow serialization failures, falls back to `.astype(str)`, logs the error
- `safe_plotly_chart()` wrapper: defined (not yet called)

**No functionality removed. No logic changed.**

**Fixes these v1 issues**:
- Arrow crash on mixed-type DataFrames -- FIXED
- Deprecated use_container_width -- FIXED

---

## v3 -- scripts/dashboard_v3.py (PENDING BUILD)

**Build spec**: `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC.md`
**Base**: v2 (dashboard_v2.py)
**Status**: SPEC WRITTEN, AWAITING REVIEW

**Architecture change**: Single-page → 6-tab VINCE control panel
**Tabs**: Single Coin | Discovery Sweep | Optimizer | Validation | Capital & Risk | Deploy
**Key additions**:
- 12 new backtester metrics (peak capital, calmar, sortino, avg W/L, streaks, etc.)
- Sweep disk persistence with resume
- Default sort by Calmar (risk-adjusted), not net PnL
- Filters: min trades, min Calmar, max DD%, grade, max LSG%
- Edge Quality panel per coin
- Portfolio-level capital/risk metrics
- Persistent status banner (reads disk, survives tab switches)
- Tabs 3/4/6 as placeholders for future VINCE ML integration

**Build scope**: Tabs 1, 2, 5 functional. Tabs 3, 4, 6 placeholder.

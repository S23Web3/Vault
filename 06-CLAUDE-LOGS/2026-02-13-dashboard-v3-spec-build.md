# Session Log — 2026-02-13 — Dashboard v3 Spec Build + Project Status

**Date:** 2026-02-13  
**Session:** 4 (evening)  
**Duration:** ~90 min  
**Environment:** Desktop (Windows 11) + Claude Code building in parallel

---

## What Happened

### 1. Dashboard Bug Report (from live testing screenshots)
- 6 bugs identified from v2 dashboard: buttons disappearing, freeze on nav, sweep dying on tab switch, no progress bar, sweep not backgrounding, lag on mode switch
- Root cause: single-page conditional rendering with no persistence

### 2. Built DASHBOARD-V3-BUILD-SPEC.md
- Consolidated all bug reports from multiple chat sessions
- 6-tab VINCE control panel architecture (Single Coin | Discovery | Optimizer | Validation | Capital & Risk | Deploy)
- Tabs 1, 2, 5 functional. Tabs 3, 4, 6 placeholder.
- Disk persistence pattern for sweep (CSV is source of truth)
- State namespace isolation per tab

### 3. Integrated Suggestions Doc
- 5 code debt fixes (CD-1 through CD-5): render_detail_view extraction, sweep error tracking, ML tabs ungated, safe_plotly, normalizer migration
- 3 SHOULD features: date range filter, param presets, sweep stop button

### 4. Coin Characteristics for VINCE
- 10 OHLCV-derived features (volume stability, spread proxy, volatility regime, trend strength, etc.)
- VINCE blind training protocol: 60/20/20 coin pool split
- Features stored in sweep CSV for dashboard visibility, per-trade parquet for ML training

### 5. LSG Reduction Strategy
- 4 exit-focused categories (fast reversal, slow bleed, near-TP miss, BE failure)
- Entry-state logging: 14 indicator fields at moment of entry per trade
- Winner vs LSG loser comparison panel for dashboard

### 6. Trade Lifecycle Logging
- 15 summary fields per trade capturing indicator behavior during trade life
- P&L path classification (direct/green_then_red/red_then_green/choppy)
- Layer 2 per-bar journal (on-demand, --save-bars flag) for sequence modeling

### 7. ML Architecture Decision
- Unified PyTorch model (NOT separate XGBoost + PyTorch)
- Three input branches: tabular (entry state) + sequence (bar-level) + context (coin characteristics)
- Three outputs: win probability, P&L path prediction, optimal exit bar
- XGBoost as validation auditor only (not production)
- Agreement score: if top-10 features differ >30% between models, flag for review
- PyTorch + CUDA confirmed installed (RTX 3060 12GB, torch 2.10.0+cu130)

### 8. Spec Review by Claude Code
- Identified scope creep (dashboard spec grew to include backtester + ML)
- Split into 3 specs: SPEC-A (dashboard), SPEC-B (backtester v385), SPEC-C (VINCE ML)
- Dashboard v3 works standalone with v384 backtester (graceful fallback via .get())
- Claude Code now building SPEC-A

### 9. Project Status Sanity Check
- Step 1 (dashboard v3) in progress via Claude Code
- Step 2 (test) is next action when build completes
- Steps 3-5: backtester upgrade cycle
- Steps 6-8: ML cycle
- Each step validates before proceeding

---

## Files Created/Modified

| File | Action |
|------|--------|
| `PROJECTS\four-pillars-backtester\DASHBOARD-V3-BUILD-SPEC.md` | Created (master spec, ~1000 lines) |
| `PROJECTS\four-pillars-backtester\DASHBOARD-V3-SUGGESTIONS.md` | Created (suggestions tracker) |
| `DASHBOARD-VERSIONS.md` | Updated (v3 entry added) |
| `BUILD-JOURNAL-2026-02-13.md` | Updated (Session 3 added) |
| `PROJECTS\four-pillars-backtester\DASHBOARD-V3-BUILD-SPEC-REVIEW.md` | Created by Claude Code (review + split proposal) |

---

## Key Decisions Made

1. Dashboard is VINCE's control panel, not a backtest viewer
2. Default sort by Calmar (risk-adjusted), not net PnL
3. One unified PyTorch model, XGBoost as auditor
4. Entry-state + lifecycle logging = VINCE's training data (ML can't work without it)
5. Spec split into A/B/C — dashboard ships independently of backtester/ML upgrades
6. Training time irrelevant — overnight runs

---

## Next Actions

1. Wait for Claude Code to finish SPEC-A build
2. Test dashboard v3 on RIVERUSDT
3. Test sweep resume (start → switch tab → switch back)
4. If passing, move to SPEC-B (backtester v385)

---

#session-log #dashboard #v3 #spec #ml #architecture #2026-02-13

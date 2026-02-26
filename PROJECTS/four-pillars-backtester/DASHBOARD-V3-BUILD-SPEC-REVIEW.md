# Dashboard v3 Build Spec -- REVIEW

**Date**: 2026-02-13
**Reviewer**: Claude Opus 4.6
**Spec reviewed**: `DASHBOARD-V3-BUILD-SPEC.md` (1009 lines)
**Status**: CHANGES REQUIRED before build

---

## VERDICT: Split into 3 specs. Fix emojis. Reduce sweep CSV scope.

---

## What's Solid

- 6-tab architecture with st.tabs() -- correct fix for the 6 reported bugs
- Disk persistence with CSV resume -- correct Streamlit-native pattern
- Calmar as default sort -- risk-adjusted is better than raw net PnL
- Code debt fixes CD-1 through CD-5 -- all correct and necessary
- "If a metric doesn't help answer a question, it doesn't belong" -- good design philosophy
- Edge Quality panel layout -- clean, information-dense
- Tab pipeline concept (each tab feeds the next)
- Button visibility fix (always visible, disabled during execution, never hidden)
- State namespace isolation per tab

---

## Problem 1: Emojis in Tab Names -- HARD RULE VIOLATION

MEMORY.md: "NEVER use emojis -- not in code, not in output, not in comments, not anywhere. Zero tolerance."

Spec uses emojis in every tab name and status banner. Replace with text-only:
- "Single Coin" not "Single Coin"
- "Discovery" not "Discovery"
- Status: "[Sweep: AGIUSDT 24/400 -- 6%]" not "[Sweep: AGIUSDT (24/400) -- 6%]"

---

## Problem 2: Scope Grew 10x Beyond Original Task

Original request: fix 6 dashboard bugs (buttons disappear, sweep freezes, no progress indicator).

Spec now includes:
- 12 new backtester metrics (engine change)
- LSG categorization with 4 categories (engine change)
- 14-field entry-state logging per trade (engine change)
- 15-field trade lifecycle logging per trade (engine change)
- P&L path classification (engine change)
- 10 coin characteristics (new pre-processing step)
- Unified PyTorch/LSTM/Transformer architecture (ML build)
- XGBoost as validation auditor (ML build)
- Per-trade parquet storage (data infrastructure)
- Per-bar parquet storage at estimated 60GB (data infrastructure)
- 60/20/20 blind coin pool split for VINCE training

The dashboard v3 file should be the DASHBOARD. Backtester changes, ML architecture, and feature engineering are separate builds with separate specs, separate test scripts, separate version bumps.

---

## Problem 3: Backtester Changes Are NOT "Metrics Only"

Spec says "do NOT change entry/exit/signal logic" but then requires:
- Entry-state snapshot at every trade entry -- touches the per-bar execution loop
- Trade lifecycle tracking during the trade -- touches the per-bar update loop
- LSG categorization at exit -- touches exit handling
- P&L path classification at exit -- touches exit handling

These are functional changes to `backtester_v384.py`, not just appending a few lines after the metrics block. They should be a separate versioned build (`backtester_v385.py`) with its own test script.

The 12 simple metrics (peak_capital, calmar, sortino, streaks, etc.) ARE safe to add -- they're all derivable from the existing `self.trades` list after the backtest completes. No loop changes needed.

---

## Problem 4: 51-Column Sweep CSV Is Too Heavy for v3

The sweep already takes minutes for 400 coins. Adding per coin:
- Coin characteristics (OHLCV pre-processing per coin)
- Entry-state comparisons (per-trade aggregation across all trades)
- LSG categorization (per-loser analysis with bar walking)

This will significantly increase sweep time. Many of these columns are for VINCE ML training, not for the dashboard user making decisions.

**Recommendation**: Split into two outputs:
- **Sweep CSV** (~25-30 columns): performance, risk, exits, dates, LSG% -- what the DASHBOARD USER needs to answer "which coins have edge?"
- **VINCE training parquet** (per-coin, separate step): full feature set with entry-state, lifecycle, coin characteristics -- what the ML PIPELINE needs

---

## Problem 5: PyTorch Architecture Doesn't Belong Here

Lines 838-901 describe a full ML model with LSTM/Transformer branches, Captum interpretability, and phased build plan. This is P2/P4 from the pending builds list. Including it in the dashboard spec means whoever builds the dashboard also has to understand ML architecture.

This should be its own spec: `VINCE-ML-ARCHITECTURE-SPEC.md`.

---

## Problem 6: Layer 2 Per-Bar Storage (60GB) Is Infrastructure

Even with `--save-bars` flag, defining storage schemas for ML training data is not a dashboard concern. The dashboard renders results. The backtester produces results. The ML pipeline consumes results. Each has its own spec.

---

## Recommended Restructuring

### Spec A: DASHBOARD-V3-BUILD-SPEC.md (rewrite, dashboard only)

What stays:
- 6-tab st.tabs() architecture (TEXT labels, no emojis)
- Code debt fixes CD-1 through CD-5
- Edge Quality panel (reads new metrics from backtester, doesn't compute them)
- Sweep rebuild with disk persistence, resume, filters, Calmar sort
- ~25-30 column sweep CSV (performance + risk + exits + dates + LSG%)
- Tab 5 basic portfolio metrics from sweep CSV
- Tabs 3/4/6 placeholder with descriptions
- Status banner, button fixes, state isolation
- S-1 date range filter, S-2 param presets, S-3 sweep stop button
- Normalizer/upload flow preserved (CD-5)

What moves out:
- Backtester metric additions -> Spec B
- Entry-state logging -> Spec B
- Trade lifecycle logging -> Spec B
- LSG categorization -> Spec B
- P&L path classification -> Spec B
- Coin characteristics -> Spec C
- PyTorch architecture -> Spec C
- XGBoost auditor -> Spec C
- Per-trade/per-bar parquet storage -> Spec C
- VINCE blind training protocol -> Spec C

### Spec B: BACKTESTER-V385-SPEC.md (new file)

- 12 new metrics (peak_capital, calmar, sortino, streaks, wl_ratio, etc.)
- Entry-state logging (14 fields per trade)
- Trade lifecycle logging (15 fields per trade)
- LSG categorization (4 categories)
- P&L path classification
- Per-trade parquet output (`results/trades_{symbol}_{tf}.parquet`)
- This is a backtester version bump: `engine/backtester_v385.py`
- Test script: `scripts/test_v385.py`
- Dashboard v3 reads whatever the backtester provides. If v385 isn't built yet, v3 works with v384 metrics (graceful fallback via `.get()` with defaults).

### Spec C: VINCE-ML-ARCHITECTURE-SPEC.md (new file)

- Coin characteristics feature engineering (10 OHLCV-derived features)
- Unified PyTorch model architecture (tabular + sequence + context branches)
- XGBoost validation/auditor role
- Per-bar Layer 2 storage (on-demand, `--save-bars` flag)
- Training pool split (60/20/20 coin pools)
- Captum + SHAP interpretability stack
- This is the P2/P4 build from the pending list
- Depends on Spec B (backtester produces the training data)

---

## Dependency Chain

```
Spec A (Dashboard v3) -- standalone, works with v384 backtester
          |
          v
Spec B (Backtester v385) -- adds metrics + logging. Dashboard v3 auto-detects new keys.
          |
          v
Spec C (VINCE ML) -- consumes backtester output. Dashboard Tabs 3/4 become functional.
```

Dashboard v3 can ship NOW with v384 backtester. Spec B and C are follow-up builds. No blocking dependency.

---

## Action Items

1. Remove all emojis from spec (tab names, status banners, LSG flags)
2. Split spec into 3 files (A, B, C) per structure above
3. Reduce sweep CSV to ~25-30 columns (user-facing metrics only)
4. Move PyTorch/LSTM/Transformer architecture to Spec C
5. Move entry-state/lifecycle logging to Spec B
6. Add graceful fallback: dashboard v3 uses `.get("calmar", 0)` so it works with v384

---

## 12 Backtester Metrics That ARE Safe for v3

These can be computed from the existing `self.trades` list after the backtest loop. No loop changes. Append-only to metrics dict:

```
peak_capital         -- max(position_counts * notional) already tracked
capital_efficiency   -- net_pnl / peak_capital * 100
max_single_win       -- max(t.pnl for t in trades if t.pnl > 0)
max_single_loss      -- min(t.pnl for t in trades if t.pnl < 0)
avg_winner           -- mean(t.pnl for winners)
avg_loser            -- mean(t.pnl for losers)
wl_ratio             -- avg_winner / abs(avg_loser)
max_win_streak       -- consecutive wins walk
max_loss_streak      -- consecutive losses walk
sortino              -- already computed in dashboard, move to backtester
calmar               -- net_pnl / abs(max_drawdown)
be_exits             -- count(t for t in trades if abs(t.pnl) < threshold)
```

These 12 can go in v384 as an additive change (no version bump needed) or in v385. Either way, dashboard v3 should use `.get()` with defaults so it works regardless.

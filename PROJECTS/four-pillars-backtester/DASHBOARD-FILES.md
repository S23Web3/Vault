# Dashboard File Index
## Four Pillars Trading System

**Last Updated:** 2026-02-26
**Current Production:** `scripts/dashboard_v392.py` (v3.9.2, 2500 lines) -- STABLE
**Next Version:** `scripts/dashboard_v393.py` (v3.9.3, BLOCKED -- IndentationError at line 1972)

---

## Active Files

| File | Lines | Version | Status | Description |
|------|-------|---------|--------|-------------|
| `scripts/dashboard_v392.py` | 2500 | v3.9.2 | PRODUCTION | Current stable dashboard. All v3.9 features + equity curve date filter fix + capital model v2 integration. |
| `scripts/dashboard_v393.py` | ~2500 | v3.9.3 | BLOCKED | Equity curve date filter session state fix. IndentationError at line 1972. Do NOT use yet. |
| `scripts/dashboard_v391.py` | 2338 | v3.9.1 | PRIOR STABLE | 14 patches, PDF export, combined CSV. Superseded by v3.9.2. |

## What's New in v3.9

- Reusable portfolio save/load (JSON templates in `portfolios/`)
- Extended per-coin metrics table (21 columns including Volume$, Rebate$, Tr/Day, MaxTr/Day)
- Per-coin drill-down expanders (Trades, Grade/Exit, Monthly P&L, Losers)
- Volume & Rebate aggregate summary section (total volume, gross/net commission, rebate, daily stats)
- Unified capital model with trade rejection and capital efficiency display
- PDF portfolio report export (requires `pip install reportlab`)

## Archived / Superseded Files

| File | Lines | Version | Status | Description |
|------|-------|---------|--------|-------------|
| `scripts/dashboard.py` | 1897 | v3.8.4 | SUPERSEDED | Original production. Replaced by v3.9.x series. |
| `scripts/dashboard_v39.py` | ~2200 | v3.9 | SUPERSEDED | Generated v3.9, replaced by v3.9.1. |
| `scripts/dashboard_portfolio.py` | 2151 | v3.8.4+ | SUPERSEDED | Pre-v3.9 portfolio build (no volume/rebate). Safe to delete. |
| `scripts/dashboard_v2.py` | 2151 | v3.8.4 | SUPERSEDED | Old name for dashboard_portfolio.py. Safe to delete. |
| `scripts/dashboard_v3.py` | 704 | -- | ABANDONED | Vince Control Panel prototype. 6-tab architecture. Never completed. |
| `scripts/dashboard_backup.py` | 525 | v3.7 | BACKUP | Pre-v3.8 dashboard. No sweep mode, no portfolio mode. |
| `scripts/dashboard.py.backup` | 853 | v3.8 | BACKUP | Mid-development backup from Feb 12. Predates sweep/portfolio. |
| `staging/dashboard.py` | 853 | v3.8 | STAGING | ML-integration staging copy. Not deployed. |

## Unrelated Dashboard Files (Different Projects)

| File | Lines | Description |
|------|-------|-------------|
| `trading-dashboard/code/dashboard.py` | 736 | Bybit PnL analysis dashboard (standalone, CSV-based). |
| `trading-tools/scripts/dashboard.py` | 249 | Executor framework status dashboard. Uses WEEXFetcher. |
| `02-STRATEGY/Indicators/dashboard-mockup.html` | -- | HTML mockup for dashboard UI design. |
| `.claude/skills/vince-ml/references/dashboard-design.md` | -- | Vince ML dashboard design notes. |

---

## Version Timeline

```
v3.7    scripts/dashboard_backup.py (525L)     -- sidebar params, single-coin only
  |
v3.8    scripts/dashboard.py.backup (853L)     -- added 5-tab layout, ML integration
  |     staging/dashboard.py (853L)            -- staging copy for ML deploy
  |
v3.8.4  scripts/dashboard.py (1897L)           -- SUPERSEDED: sweep, portfolio, params_hash
  |
v3.9    scripts/dashboard_v39.py (~2200L)      -- SUPERSEDED: portfolio enhancements + volume/rebate + PDF export
  |
v3.9.1  scripts/dashboard_v391.py (2338L)     -- 14 patches, PDF export, combined CSV
  |
v3.9.2  scripts/dashboard_v392.py (2500L)     -- PRODUCTION: equity curve fix, capital model v2
  |
v3.9.3  scripts/dashboard_v393.py (~2500L)    -- BLOCKED: IndentationError at line 1972
```

## Utils Modules

| File | Lines | Purpose |
|------|-------|---------|
| `utils/portfolio_manager.py` | 94 | Save/load/list/delete portfolio templates (JSON) |
| `utils/coin_analysis.py` | ~200 | 10 extended metrics, daily volume stats, monthly P&L, grade/exit distributions |
| `utils/pdf_exporter.py` | ~310 | Multi-page PDF report with equity/capital charts, volume/rebate summary |
| `utils/pdf_exporter_v2.py` | 330 | Updated PDF exporter with orientation fixes and diagram alignment |
| `utils/capital_model.py` | 258 | Post-processing capital constraints, grade-based priority |
| `utils/capital_model_v2.py` | 537 | Exchange-model pool: balance + margin_used, daily rebate settlement, position grouping |

## Build Scripts

| File | Purpose |
|------|---------|
| `scripts/build_dashboard_portfolio_v3.py` | Creates all 4 utils modules + tests + debug script |
| `scripts/build_dashboard_integration.py` | Patches dashboard.py -> dashboard_v39.py (7 patches + volume/rebate) |

## Tests

| File | Tests | Status |
|------|-------|--------|
| `tests/test_portfolio_enhancements.py` | 81 | PASSED |
| `scripts/debug_portfolio_enhancements.py` | 44+ | PASSED |

---

## Cleanup Recommendations

Files safe to delete (all superseded):
- `scripts/dashboard_portfolio.py` -- superseded by dashboard_v39.py
- `scripts/dashboard_v2.py` -- old name for dashboard_portfolio.py
- `scripts/dashboard_v3.py` -- abandoned Vince prototype
- `scripts/dashboard_backup.py` -- pre-v3.8, no longer relevant
- `scripts/dashboard.py.backup` -- mid-dev snapshot, superseded
- `scripts/__pycache__/dashboard_v2.cpython-313.pyc` -- stale cache

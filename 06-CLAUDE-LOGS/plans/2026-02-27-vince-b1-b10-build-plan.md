# Plan: Lock Vince v2 Concept + Build Roadmap

**Date:** 2026-02-27
**Goal:** Finalize the Vince v2 concept, then build Vince as a unified Dash application.

---

## Context

Vince is a trade research engine. The dashboard is Vince's GUI -- it exists to serve Vince, not the other way around. The existing Streamlit dashboard (`scripts/dashboard_v392.py`, 2500 lines, 5 tabs) gets replaced by a Dash app that IS Vince.

Backtester features (equity curve, trade browser, MFE/MAE) are tools Vince uses to answer research questions. They live inside Vince's panels, not as a separate section.

### Decisions Made

- **Framework:** Plotly Dash
- **Architecture:** Vince is the app. Dashboard serves Vince.
- **Agent:** Future iteration. API skeleton built now for clean plug-in later.
- **Scope:** Core analysis engine + Dash GUI first. RL + LLM + agent = later phases.

---

## Before Building: Lock the Concept

**Coherence fixes already applied (2026-02-27):**
- Filename corrected: `four_pillars_v383_v2.py` (was wrong)
- `strategies/four_pillars.py` annotated as "(to be created — primary build task)"
- `symbol` added explicitly to `trade_schema()` example
- RL state vector decoupled from hardcoded k1/k2/k3/k4 — now dynamic from plugin
- `list[str]` vs `list` aligned across all three documents

**Status:** Concept locked 2026-02-27. GUI (Dash) + Architecture skeleton sections added to `VINCE-V2-CONCEPT-v2.md`. Status changed to APPROVED FOR BUILD.

---

## Vince Panels

Organized around what Vince answers, not around old vs new features:

| # | Panel | What It Answers | Tools Inside |
| - | ----- | --------------- | ------------ |
| 1 | Coin Scorecard | Why does this coin keep losing? | Monthly metric table, equity curve, per-coin drill-down |
| 2 | PnL Reversal Analysis (PRIORITY) | What does the reversal anatomy look like? | MFE histogram in ATR bins, TP sweep curve, optimal exit point |
| 3 | Constellation Query | When indicator X was in state Y, what happened? | Interactive filter builder, matched vs complement, delta table |
| 4 | Exit State Analysis | What moved before the reversal? | Indicator change ranking, timing histograms, intra-candle events |
| 5 | Trade Browser | Show me the individual trades | Sortable/filterable trade table, entry/exit details, accessible from any panel |
| 6 | Settings Optimizer | What parameters actually work? | Optuna sweep results, best N candidates, train vs test metrics |
| 7 | Validation | Is the edge real? | Monte Carlo p-values, walk-forward efficiency, feature importance |
| 8 | Session History | What did I find last time? | All previous research sessions, annotatable, filters restorable |

Future panels (skeleton only, built later):

- RL Exit Policy overlay on Panel 2
- LLM Interpretation (Panel 9)
- Agent autonomous research output

---

## Build Order

| Phase | What | Produces |
| ----- | ---- | -------- |
| B1 | FourPillarsPlugin | `strategies/four_pillars.py` -- concrete plugin wrapping existing backtester |
| B2 | API layer + types | `vince/api.py`, `vince/types.py` -- the skeleton everything calls |
| B3 | Enricher | `vince/enricher.py` -- attach indicator snapshots to every trade. Storage: diskcache (session_id in dcc.Store, enriched trade set on disk by key — never raw DataFrame in browser) |
| B4 | Panel 2 (PnL Reversal) | `vince/pages/pnl_reversal.py` -- pure Python data module (no Dash imports) |
| B5 | Constellation Query Engine | `vince/query_engine.py` -- filter + delta logic |
| B6 | Dash app shell | `vince/app.py`, `vince/layout.py` -- sidebar, routing, panels wired |
| B7 | Panels 1, 3, 4, 5 | Coin Scorecard, Constellation UI, Exit State, Trade Browser |
| B8 | Mode 2 Auto-Discovery | `vince/discovery.py` -- sweep constellations, surface patterns |
| B9 | Mode 3 Settings Optimizer | `vince/optimizer.py` -- Optuna parameter sweep |
| B10 | Panels 6, 7, 8 | Optimizer results, Validation, Session History |

Each phase = one build session with tests.

---

## File Structure

```text
four-pillars-backtester/
  vince/
    __init__.py
    app.py                  # Dash entry point: python vince/app.py
    layout.py               # Sidebar navigation + page routing
    api.py                  # Python API (GUI calls this, future agent calls this)
    types.py                # Dataclasses: MetricTable, EnrichedTrade, etc.
    enricher.py             # Indicator snapshot attachment
    query_engine.py         # Constellation query + delta calculation
    discovery.py            # Mode 2 auto-discovery
    optimizer.py            # Mode 3 Optuna sweep
    pages/
      __init__.py
      coin_scorecard.py     # Panel 1
      pnl_reversal.py       # Panel 2 (PRIORITY)
      constellation.py      # Panel 3
      exit_state.py         # Panel 4
      trade_browser.py      # Panel 5
      optimizer_ui.py       # Panel 6
      validation.py         # Panel 7
      session_history.py    # Panel 8
    assets/
      style.css
  strategies/
    base_v2.py              # StrategyPlugin ABC (exists)
    four_pillars.py         # B1: FourPillarsPlugin
```

---

## Existing Code Reused

| Existing File | Used By | How |
| ------------- | ------- | --- |
| `strategies/base_v2.py` | B1 | ABC that FourPillarsPlugin implements |
| `signals/four_pillars_v383_v2.py` | B1 | Plugin calls `compute_signals_v383()` |
| `engine/backtester_v384.py` | B1 | Plugin calls this for `run_backtest()` |
| `engine/position_v384.py` | B3 | Trade384 dataclass for enricher |
| `engine/commission.py` | B1 | Commission model inside plugin |
| `signals/bbwp.py` | B3 | BBW percentile in enricher snapshots |
| `ml/features.py` | B5 | Feature extraction for constellation dimensions |
| `ml/walk_forward.py` | B10 | WFE calculation for validation panel |
| `research/bbw_monte_carlo.py` | B10 | Monte Carlo for validation panel |

---

## Verification

After B1-B6 complete:

- `python vince/app.py` launches Dash in browser
- Sidebar shows all panel names
- Panel 2 (PnL Reversal) shows MFE histogram for a selected coin
- API callable from Python REPL: `from vince.api import query_constellation; result = query_constellation(filters)`
- Each panel is a separate file under 300 lines

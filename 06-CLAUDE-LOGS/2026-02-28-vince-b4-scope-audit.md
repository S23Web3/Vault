# Vince B4 — PnL Reversal Panel Scope Audit
**Date:** 2026-02-28
**Session type:** Research / audit — no code built
**Context:** User referenced `BUILD-VINCE-B4-PNL-REVERSAL.md` (does not exist yet). Full audit: skills, scope, API bottlenecks, questions, improvements.

---

## What Was Done

Full research audit of B4 (PnL Reversal Analysis panel) in the Vince v2 build sequence. Explored:
- `BUILD-VINCE-ML.md` (ARCHIVED v1 — disambiguation: old B4 was "Dashboard Integration for ML classifiers", not the same as v2 B4)
- `docs/VINCE-V2-CONCEPT-v2.md`, `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md`
- `strategies/base_v2.py`, `signals/four_pillars.py`, `signals/state_machine.py`
- `06-CLAUDE-LOGS/plans/2026-02-28-b2-api-types-research-audit.md`
- `06-CLAUDE-LOGS/plans/2026-02-28-b3-enricher-research-audit.md`

Cross-referenced B2 and B3 audit docs to understand what B4 receives as input and what upstream blockers carry forward.

---

## Skills Required

| Skill | When |
|-------|------|
| `four-pillars` | Grade system, LSG concept, commission math |
| `four-pillars-project` | Build order cross-reference (B1→B2→B3→B4) |
| `dash` (MANDATORY per CLAUDE.md) | NOT for B4 itself — load before any B6 code wiring Panel 2 into UI |
| Python (MANDATORY per MEMORY.md) | Any `.py` file |

---

## What B4 Builds

Single file: `vince/pages/pnl_reversal.py` (~250-350 lines). Pure Python, no Dash/Plotly imports.

Four functions:
1. `get_pnl_reversal_analysis(enriched_trades, symbol, metric_type)` → `PnLReversalResult`
2. `get_tp_sweep_curve(enriched_trades, tp_multipliers)` → `TpSweepResult`
3. `get_optimal_exit_analysis(enriched_trades)` → `OptimalExitResult`
4. `compute_mfe_bin(mfe_atr)` → `str` (helper)

B4 does NOT: import Dash/Plotly, re-run the backtester, filter trade count, train ML models, or touch the database.

### Hard Build Order Blocker
Entire `vince/` directory does not exist. B4 cannot start until:
- B1: `strategies/four_pillars.py` (FourPillarsPlugin)
- B2: `vince/types.py` + `vince/api.py`
- B3: `vince/enricher.py`

---

## Bottlenecks & Questions Surfaced (8 total)

**Q1 — Does backtester_v384 output `mfe`, `mae`, `saw_green`, `entry_atr` per trade?**
HIGH RISK. If absent, panel has no data. `mfe_analysis_v383.py` uses `t.saw_green` and `t.mfe` directly — implies they exist. B3 audit confirmed `mfe_bar` IS missing (separate issue, affects Panel 4 more than Panel 2).

**Q2 — `saw_green`: bar-by-bar tracking or MFE proxy?**
Reference script uses `.saw_green` directly — implies bar-by-bar tracking exists in Trade384. If not, B4's LSG% will be wrong.

**Q3 — TP sweep: re-run backtester or simulate from MFE?**
Simulation is correct (reference `mfe_analysis_v383.py` lines 233-256): if `mfe_atr >= tp_level`, trade would have hit TP. Commission stays constant regardless of exit price.

**Q4 — ATR bin granularity: 6-bin spec vs 9-bin reference**
Spec: `[0-0.5, 0.5-1.0, 1.0-1.5, 1.5-2.0, 2.0-3.0, 3.0+]`
Reference impl: `[0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, ∞]`
Recommendation: 9-bin (more resolution in 0.25-0.5 ATR zone where SL decisions are made).

**Q5 — RL overlay: B4 responsibility or placeholder?**
Concept doc mentions RL policy overlay on Panel 2. Recommendation: `rl_overlay: Optional[List] = None` in result type — real RL is separate future scope.

**Q6 — Does enricher normalize MFE to ATR units?**
B3 Improvement 3 recommends enricher adds `mfe_atr` + `mae_atr` columns. If done, B4 uses `mfe_atr` directly. If not, B4 computes: `mfe_atr = trade.mfe / trade.atr_at_entry`.

**Q7 — API surface from B6**
`vince/api.py` owns orchestration. B6 calls `api.get_panel2_data()`. B4 is never called from B6 directly.

**Q8 — `get_panel2_data` signature has unused `timeframe` arg**
From B2 audit: `get_panel2_data(symbol, timeframe)` — timeframe unused by Vince (indicator-only, no price charts). Should be removed or clarified when B2 is built.

---

## Improvements Proposed (6 total)

1. **9-bin ATR histogram** — finer resolution where SL/TP calibration decisions are made
2. **Winners left on table** — `avg_winner_mfe_atr` minus `avg_winner_exit_atr`; quantifies early exit cost on winners
3. **Per-grade TP sweep** — breakdown by grade (A/B/C/D/R); optimal TP differs between A and D entries
4. **Gross + net dual curve** — both curves on TP sweep chart; commission can flip tight TP points negative
5. **Temporal date filtering** — `start_date`/`end_date` on all B4 functions; MFE patterns shift with regime
6. **Breakeven-adjusted MFE** — for `be_raised=True` trades, show net protected excursion from BE level, not raw entry MFE

---

## Plan File
`C:\Users\User\.claude\plans\concurrent-sniffing-brook.md` — full structured audit.

## Next Steps
1. Confirm Q1/Q2 by reading `engine/position_v384.py`
2. Complete B1 → B2 → B3 before building B4
3. Write `BUILD-VINCE-B4-PNL-REVERSAL.md` spec (not this session)

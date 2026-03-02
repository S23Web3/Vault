# B4 PnL Reversal Panel — Scope Audit & Research
**Date:** 2026-02-28
**Scope:** Research audit, skill identification, bottleneck surfacing, improvement proposals
**Target spec doc:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B4-PNL-REVERSAL.md` (does not exist yet — needs to be created)

---

## Context

B4 is the fourth block in the Vince v2 trade research engine (approved 2026-02-27). It produces the **data module** powering Panel 2: PnL Reversal Analysis — explicitly designated as the HIGHEST PRIORITY panel in the architecture.

Research finding driving this priority: *random entry + ATR stops = 160% return on WEEX. Exit optimization contributes more alpha than entry filtering.* Panel 2 directly measures exit quality.

**Important disambiguation:** `BUILD-VINCE-ML.md` (ARCHIVED, v1) also calls something "B4" (Dashboard Integration for ML classifiers). That is a dead spec. The active B4 is Panel 2 from the v2 concept doc.

---

## Skills Required

| Skill | Trigger | Required For |
|-------|---------|-------------|
| **four-pillars** | grade system, entry grading (A/B/C/D/R), signal columns | Understanding trade schema, LSG definitions, commission math |
| **four-pillars-project** | Cross-cutting context, build order, B1-B10 plan | Confirming B4 dependencies and what B1/B2/B3 produce |
| **dash** (MANDATORY per CLAUDE.md) | Panel 2 will become a Dash page in B6 | NOT needed for B4 itself (pure Python), but MUST be loaded before any B6 work touches Panel 2 layout |
| **Python** | All .py files | Core build — pandas, numpy, dataclass types |

**B4 itself is pure Python — no Dash imports.** The Dash skill is needed at B6 phase, not now. However, B4 must design its return types to be Dash-friendly (JSON-serializable, plot-ready).

---

## What B4 Builds

**Single deliverable:** `vince/pages/pnl_reversal.py` (~250-350 lines)

Four functions + return dataclasses:

| Function | Input | Output | Purpose |
|---------|-------|--------|---------|
| `get_pnl_reversal_analysis(enriched_trades, symbol, metric_type)` | List[EnrichedTrade] | PnLReversalResult | MFE histogram + LSG stats |
| `get_tp_sweep_curve(enriched_trades, tp_multipliers)` | List[EnrichedTrade] | TpSweepResult | Net PnL at each simulated TP level |
| `get_optimal_exit_analysis(enriched_trades)` | List[EnrichedTrade] | OptimalExitResult | Bars from MFE to actual exit |
| `compute_mfe_bin(mfe_atr)` | float | str | Helper: classify MFE into ATR bin |

**B4 does NOT:**
- Import or use Dash, Plotly, or any GUI framework
- Re-run the backtester
- Filter or reduce trade count
- Train ML models or interact with RL
- Touch the database (api.py handles storage)

---

## Hard Build Order Dependency — CRITICAL BLOCKER

B4 **cannot be written** without these three preceding blocks:

| Block | What it produces | Status |
|-------|-----------------|--------|
| **B1** | `strategies/four_pillars.py` — FourPillarsPlugin with `run_backtest()` + `compute_signals()` | NOT EXISTS |
| **B2** | `vince/types.py` — `EnrichedTrade`, `PnLReversalResult`, `TpSweepResult` dataclasses | NOT EXISTS |
| **B3** | `vince/enricher.py` — `enrich_trades()` function returning `List[EnrichedTrade]` | NOT EXISTS |

**The entire `vince/` directory does not exist.** B4 is unreachable until B1→B2→B3 complete.

---

## API & Data Bottlenecks — All Questions Surfaced

### Q1: Does backtester_v384 actually output `mfe`, `mae`, `saw_green`, `entry_atr`?
**Why it matters:** B4's MFE histogram requires MFE in ATR units: `mfe_atr = mfe_dollars / entry_atr`. If the backtester doesn't track these fields per-trade, the entire panel has no data.
**Files to verify:** `engine/backtester_v384.py`, `engine/position_v384.py`
**Risk level:** HIGH — if absent, requires backtester modification before B4 can function.

### Q2: How is `saw_green` defined and tracked?
**Why it matters:** LSG (Losers Seeing Green) is the core concept: losers that reached positive gross PnL before exit. Two possible implementations:
- **Bar-by-bar tracking** (expensive): backtester checks unrealized PnL every bar, sets `saw_green=True` if gross PnL ever > 0
- **MFE proxy** (cheap): if `mfe_dollars > commission`, assume saw_green=True (since MFE means max favorable excursion)
**Question:** Which does the current engine use? The `mfe_analysis_v383.py` reference script accesses `t.saw_green` directly on Trade objects — implying bar-by-bar tracking.
**Risk:** If backtester doesn't track this, B4's LSG% will be wrong.

### Q3: TP Sweep — Re-run needed or simulate from MFE?
**Why it matters:** The TP sweep asks "what if we set TP at 1.5x ATR?" for every trade. Two approaches:
- **Re-run backtester** for each TP level (~8 runs) — expensive, 100% accurate
- **Simulate from MFE** — if `mfe_atr >= tp_multiple`, trade would have hit TP → assign TP PnL. Single pass, ~99% accurate (misses multi-position edge cases)
**Reference implementation** (`mfe_analysis_v383.py` lines 233–256) uses simulation. This is the correct approach for B4.
**Commission question:** Simulated TP exit uses same round-trip commission as actual exit. Net PnL = `(entry_price × tp_multiple × atr) - commission`. This needs to be calculated per trade, not globally.

### Q4: What ATR bins should the histogram use?
**Two options found:**
- Spec doc: `[0-0.5, 0.5-1.0, 1.0-1.5, 1.5-2.0, 2.0-3.0, 3.0+]` (6 bins)
- Reference implementation: `[0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, inf]` (9 bins)
**Recommendation:** Use finer bins from reference (0.25 increments up to 3.0). More actionable — shows whether the bulk of LSG reversals happen in the 0.25-0.5 ATR zone (actionable for SL placement) vs. 1.0-1.5 ATR zone (actionable for TP placement).

### Q5: RL overlay — included in B4 or placeholder?
The concept doc mentions: *"RL policy output overlays on Panel 2 as an additional curve."*
**Question:** Is B4 responsible for the RL overlay data, or does B4 just provide the baseline curves and B6 adds an RL placeholder?
**Recommendation:** B4 provides the static MFE + TP sweep data only. RL overlay = separate future scope. B4 should define a `rl_overlay: Optional[List] = None` field in `PnLReversalResult` to keep the door open.

### Q6: EnrichedTrade — does it carry OHLCV tuples or just indicator snapshots?
The plugin interface spec (2026-02-27 update) added `entry_ohlc`, `mfe_ohlc`, `exit_ohlc` tuples to EnrichedTrade for Panel 4 (Exit State Analysis). B4 does NOT need these tuples — it only needs:
- `mfe` (in dollars, or pre-converted to ATR by enricher)
- `entry_atr`
- `saw_green`
- `pnl_gross`, `pnl_net`
- `commission`
- `exit_reason`
- `grade`
**Question for B2:** Should enricher normalize MFE to ATR units before handing to B4, or should B4 do its own conversion? Recommendation: enricher normalizes (produces `mfe_atr` directly), keeping B4 simple.

### Q7: What is the input API surface for B4 from the Dash layer (B6)?
B4 functions will be called from B6 callbacks with user-selected parameters. B6 will call something like:
```python
from vince.api import get_panel2_data
result = get_panel2_data(session_id, symbol, date_range, grade_filter, metric_type)
```
**Question:** Does `api.py` (B2) own the orchestration (call enricher → call B4 functions), or does B6 call B4 directly?
**Recommendation:** `vince/api.py` owns all orchestration. B6 calls `api.get_panel2_data()`. B4 is a pure library, not callable from B6 directly. This keeps B4 testable in isolation.

### Q8: Metric type — gross vs net
The spec mentions `metric_type: str = "gross"` as a parameter. When `metric_type="net"`, TP sweep results should show net PnL (after commission). Commission is fixed per trade — same whether TP or SL or manual exit. This is straightforward but must be consistently applied.

---

## File Existence Audit

| File | Exists? | Notes |
|------|---------|-------|
| `vince/` directory | NO | Entire package missing |
| `vince/__init__.py` | NO | Created in B0/B2 |
| `vince/types.py` | NO | B2 deliverable |
| `vince/api.py` | NO | B2 deliverable |
| `vince/enricher.py` | NO | B3 deliverable |
| `vince/pages/pnl_reversal.py` | NO | **B4 target** |
| `strategies/base_v2.py` | YES (stub ABC) | Do not modify |
| `strategies/four_pillars.py` | NO | B1 deliverable |
| `engine/backtester_v384.py` | YES (production) | Read-only |
| `engine/position_v384.py` | YES (production) | Read-only — verify MFE/saw_green fields |
| `signals/four_pillars.py` | YES (exists, new) | Recently modified |
| `signals/state_machine.py` | YES | Recently modified |
| `ml/loser_analysis.py` | YES | Reference — MFE analysis patterns |
| `scripts/mfe_analysis_v383.py` | YES | Reference implementation |
| `data/db.py` | YES | DB layer with backtest_trades schema |
| `BUILD-VINCE-B4-PNL-REVERSAL.md` | NO | To be written after audit approval |

---

## Improvements vs. Current Spec

### Improvement 1: Finer ATR bins
Use `[0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, ∞]` (9 bins) instead of 6. The 0.25-0.5 ATR zone is where SL placement decisions get made — coarser bins lose resolution exactly where it matters most.

### Improvement 2: Winners Left on Table
Add to `PnLReversalResult`:
- `avg_winner_mfe_atr`: average MFE of winning trades in ATR
- `avg_winner_actual_exit_atr`: average exit PnL of winning trades in ATR
- `avg_left_on_table`: difference = unrealized alpha from early exits
This quantifies how much value winners sacrifice — complements the LSG analysis.

### Improvement 3: Per-Grade TP Sweep
The TP sweep today is aggregate across all trades. Breaking it down by grade (A/B/C/D/R) shows whether optimal TP differs by signal quality. A-grade trades may tolerate a looser TP (3.0 ATR) while D-grade trades may need tight exits (1.0 ATR). Surface as a secondary table.

### Improvement 4: Gross + Net curve on TP sweep
Render two curves in the B6 panel: gross PnL sweep and net PnL sweep (after commission). On high-leverage accounts with tight TP, commission can flip a profitable TP sweep point negative. Making this visible in the chart catches the "false optimal TP" problem.

### Improvement 5: Temporal split of MFE data
Allow date_range filtering: `start_date`, `end_date` parameters. MFE patterns shift as market regimes change. Comparing Jan vs Feb shows whether optimal TP is stable or regime-dependent. B4 functions should accept optional date range filtering over enriched_trades.

### Improvement 6: Breakeven-adjusted MFE view
For trades where `be_raised=True`, the effective floor moved. The MFE from entry may be 2.0 ATR, but the BE was raised at 0.5 ATR — so the "protected" move was only 1.5 ATR. Adding a `be_adjusted_mfe` view shows the net protected excursion, helping calibrate breakeven trigger timing.

---

## Test Strategy

Since B4 is pure Python with no Dash or DB dependencies, it can be tested with synthetic data:

```python
# scripts/test_b4_pnl_reversal.py
# Create 100 synthetic EnrichedTrade objects with known MFE/saw_green values
# Assert: histogram bins sum to total trade count
# Assert: TP sweep at 0.0 ATR = all trades hit TP (trivial case)
# Assert: TP sweep at 100.0 ATR = 0 trades hit TP
# Assert: LSG% = (trades with saw_green=True and pnl_net<0) / losers
# Assert: optimal_tp_multiple is within the provided tp_multipliers list
```

No live data, no DB, no API calls needed. Fast, deterministic, fully isolated.

---

## Build Spec Doc To Write

After this audit is approved, create:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B4-PNL-REVERSAL.md`

Contents should include:
1. Build order prerequisites (B1→B2→B3 must complete first)
2. File deliverable: `vince/pages/pnl_reversal.py`
3. Function signatures + docstrings
4. Dataclass definitions for `PnLReversalResult`, `TpSweepResult`, `OptimalExitResult`
5. ATR bin definition (use 9-bin scheme)
6. TP sweep simulation algorithm (from MFE, no re-run)
7. LSG definition and saw_green field dependency
8. Test script spec
9. py_compile requirement
10. Improvements list (from above) flagged as OPTIONAL SCOPE

---

## Summary: What Needs to Happen Before Building B4

1. **Verify** `engine/position_v384.py` has `mfe`, `mae`, `saw_green`, `entry_atr` fields on trade objects (read-only check)
2. **Clarify** whether enricher normalizes MFE to ATR units (B3 responsibility) or B4 does it (answer before writing B2 types.py)
3. **Complete B1** (FourPillarsPlugin)
4. **Complete B2** (types.py + api.py + vince/ package structure)
5. **Complete B3** (enricher.py)
6. **Then build B4**

The spec doc (`BUILD-VINCE-B4-PNL-REVERSAL.md`) can be written now — it does not require B1-B3 to be done, only to be understood.

---

**NOTE:** Per CLAUDE.md, a copy of this plan must also be saved to:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-b4-pnl-reversal-scope-audit.md`
This will be done post-approval (plan mode restricts writes to this file only).

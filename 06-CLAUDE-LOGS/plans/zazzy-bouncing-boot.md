# Vince v2 — Build Plan

**Date:** 2026-02-19
**Status:** APPROVED FOR BUILD

---

## SESSION LOG — 2026-02-19 (Scope Session, NOT a build session)

**What was established this session:**
- Vince runs the backtester himself with different settings (autonomous)
- Finds statistical advantages by frequency — how many times X happened, how many times X won
- Discovers relationships the user hasn't seen (auto-discovery mode)
- Logs all runs with timestamps — accumulated history IS the learning
- BBW (volatility) is a feature dimension — already built in signals/bbwp.py
- Stochastic periods fixed (Kurisko): K1=9, K2=14, K3=40, K4=60
- Cloud EMAs fixed: 5/12, 34/50, 72/89
- The RELATIONSHIP of price/stochastics/clouds is fixed — the validated framework
- What Vince optimizes: trading decisions (TP, SL, cross_level, B/C rules, cloud3 gate)
- Dashboard must be INTERACTIVE — not static output. This is ML. The user explores, drills in, system responds in real time.
- Master project file: docs/vince/VINCE-PROJECT.md (index of all Vince files and versions)
- Two CSV comparison: Vince holds before/after CSVs, runs same query on both, shows delta
- Coin diagnosis: why does one specific coin keep losing — Vince answers from frequency data
- Regime scenarios (Monday Asian session etc.) — future scope, architecture must allow it
- RE-ENTRY is wrongly programmed — Vince will expose this, fix deferred
- Rebate constraint: win rate gains cannot come at cost of volume

**What is still being scoped (do NOT build yet):**
- Exact mechanism for how Vince decides which settings to try (grid? random? stepped?)
- What "interactive ML" means for the dashboard UX specifically
- Module architecture not finalized

**Context warning: ~70-75% used. Open new chat to continue scoping.**

---

## CRITICAL SCOPE UPDATE (2026-02-19)

Vince is NOT a passive CSV reader. Vince RUNS THE BACKTESTER HIMSELF.

- **Vince runs new settings autonomously.** Given a coin or coin set, Vince sweeps parameter combinations (TP mult, SL mult, signal parameters, B/C rules, cloud3 on/off), runs the backtester for each, finds what works.
- **Why does one coin keep losing.** Coin-specific diagnosis. Vince answers: "this coin loses because X." Not a guess — from frequency data.
- **Statistical advantages the user hasn't seen.** Auto-discovery mode. Vince proactively finds novel relationships across ALL dimension combinations. Surfaces the ones with the biggest delta from baseline. "When K3 is 48–52 AND C2 flipped within 3 bars, win rate is 12%. You haven't looked at this."
- **Learns from frequency.** Not ML model weights. How many times did X happen, how many times did X AND Y happen, what % were wins. Pure statistical frequency counting.
- **Logs everything with timestamps.** Every run logged: datetime, settings used, coins, win rate, net PnL, findings. History of all runs queryable.

This means Vince has THREE operating modes:
1. **User query**: user defines constellation filter → Vince shows win rate for matched vs unmatched trades
2. **Auto-discovery**: Vince sweeps all constellation dimensions, finds the combinations with the largest win rate delta, surfaces top N "you didn't know this" patterns
3. **Settings optimizer**: Vince runs backtester with different parameter combinations, finds optimal settings per coin or coin set

## What the User Has Said (must not be lost)

- **RE-ENTRY is wrongly programmed.** Deferred until after Vince scope, but Vince will expose this — the RE data will show it.
- **Rebate constraint is non-negotiable.** Win rate improvement cannot come at the cost of volume. Every setting change gets evaluated as: does net PnL (after rebate) improve? Not just win rate in isolation.
- **No price charts in output.** User reads indicators only. "Price action is for amateurs." Vince shows numbers, not candles.
- **Reading style: momentum across all four simultaneously.** "9,3 already going, I sense that the others are also going, volatility kicks in." This is not just K1 exiting zone. It is the sense of ALL stochastics building together. The constellation query must capture direction + momentum across K1/K2/K3/K4 together, not in isolation.
- **B and C trades may need full rewrite.** Not just "remove cloud3." The entire B/C condition logic is under question. Vince shows what works. User rewrites the rules.
- **Cloud3 hard gate is suspect.** It may be gating good trades out while letting bad ones through anyway. Vince will show whether cloud3 state at entry actually correlates with outcome.
- **Regime scenarios are future scope.** Monday Asian session, Bitcoin dump scenarios, session-based filters. Architecture must leave room for this. Not built now.
- **User says a lot.** Capture all of it. Do not reduce nuanced statements to bullet points that lose meaning.

---

## Fixed Constants (Vince NEVER sweeps these)

- **Stochastic periods**: K1=9, K2=14, K3=40, K4=60. Tested and validated by John Kurisko. Non-negotiable.
- **Stochastic smoothing**: Raw K (smooth=1). Fixed.
- **Cloud EMAs**: 5/12, 34/50, 72/89. Fixed.

## What Vince CAN Sweep (parameter optimization space)

- TP mult (0.5 – 5.0)
- SL mult (1.0 – 4.0)
- cross_level (threshold for entry trigger, default 25)
- zone_level (threshold for zone tracking, default 30)
- allow_b (True/False) — enable/disable B trades
- allow_c (True/False) — enable/disable C trades
- cloud3 requirement for B/C (True/False) — the suspect hard gate
- BE trigger and lock (atr multiples)
- checkpoint_interval (bars between scale-out checks)
- sigma_floor_atr (AVWAP sigma minimum)

---

## Core Architecture Principles (LOCKED)

1. **Vince reads. User changes.** Strategy rule changes (remove cloud3, adjust B/C thresholds) are made by the user directly in the strategy/signal code. User re-runs backtester → new trade CSV → Vince reads and analyzes. Vince NEVER modifies strategy parameters internally.

2. **No hardcoded restrictions in strategy.** User will remove hard rule gates (like cloud3 mandatory). Run both versions. Vince compares results. The data decides what works.

3. **Constellation query = multi-dimensional filter.** Any combination of the dimensions below. Vince returns: trades matched, win rate, avg MFE (ATR), avg MAE (ATR), net PnL.

### Constellation Query Dimensions

**Static** (values AT entry bar):
- K1/K2/K3/K4 value range (slider, e.g. K1 in 25–60)
- Cloud2 state: bull/bear/any
- Cloud3 state: bull/bear/any
- Price position vs C3: above/inside/below/any

**Volatility** (BBW — already built in signals/bbwp.py):
- BBW level at entry: <20 / 20–40 / 40–60 / >60 (custom slider)
- BBW direction: expanding / contracting / any (BBW[0] vs BBW[N])
- BBW over last hour: expanding / contracting (compare BBW[0] vs BBW[12] on 5m = 1 hour)
- Example: "BBW=20 at entry" = tight consolidation. "BBW=55 at entry" = already volatile. Do outcomes differ? Vince answers this.
- Reuse: signals/bbwp.py (Layer 1, 67/67 tests, already complete)

**Dynamic** (behavior AT entry bar):
- K1/K2/K3/K4 direction: rising/falling/any (vs N bars prior)
- K1 speed: fast/slow/any (pts per bar)
- K2+K3 both crossing 50: yes/no/any
- All 4 rising simultaneously: yes/no/any
- ATR state: expanding/contracting/any (ATR[0] vs ATR[3])

**Trade filters**:
- Grade: A/B/C/D/R/any combo
- Direction: LONG/SHORT/both
- Entry type: fresh/ADD/RE/any

**Outcome filters**:
- All / TP wins / SL losses / saw_green
- MFE threshold: >0.5 / >1.0 / >2.0 ATR

**Regime filters** (future — not in v1):
- Month, weekday, session (Asian/London/NY)
- Macro direction (K4 > 50 bull / < 50 bear)

---

## Deliverable 0 — Master Project File (first output, before any code)

**Path**: `docs/vince/VINCE-PROJECT.md`

Single indexed file for the Vince project. Contains:
- What Vince is (perspective, purpose, what it answers)
- Current version + status of each module
- All file paths (modules, tests, build scripts, docs)
- Data flow diagram
- Known bugs + deferred items
- Run commands

MEMORY.md gets ONE line pointing to this file. All Vince detail lives in `VINCE-PROJECT.md`, not in MEMORY.md.

---

## Context

10 out of 400 coins are performing poorly. The user cannot manually review 90K trades across a year of data. Vince is the automated analyst that reads every trade, every indicator constellation, and surfaces the answers. User does not want human speculation — they want the tool to show the data.

Three questions Vince must answer:
1. **Why are certain coins broken?** — win rate, constellation at entry, what differs from good coins
2. **LSG anatomy** — for the 86% of losers that saw green: how much green, expressed in ATR multiples, and when was the optimal exit
3. **Validation** — findings confirmed on a different random 10-coin batch

Constraint: NEVER reduce trade count. All trades taken. Volume preserved for rebate.

---

## What Vince Shows on Screen

Five panels in a Streamlit tab (`vince/dashboard_tab.py`):

### Panel 1 — Coin Scorecard (first thing visible)
Table sorted by win rate ascending. Columns:
- Symbol | Trades | Win Rate | LSG% | Avg MFE (ATR) | Avg MAE (ATR) | Net PnL | Best Grade

Bad coins immediately visible (red rows). Click a row to drill into that coin.

### Panel 2 — LSG Anatomy
For losers with saw_green=True:
- Histogram: MFE in ATR multiples (bins: 0–0.5, 0.5–1.0, 1.0–1.5, 1.5–2.0, 2.0–3.0, 3.0+)
- Key stat: "X% of losers reached ≥ TP level before reversing"
- Optimal TP curve: net PnL vs TP multiple from 0.5 to 5.0 ATR (simulated from existing trades)
- Bar showing: current TP vs optimal TP

### Panel 3 — Constellation Query Builder (CORE)
Interactive filter panel. User sets any combination of dimensions → immediate results.
- Sliders: K1 range, K2 range, K3 range, K4 range (0–100, adjustable)
- Dropdowns: K1 direction (rising/falling/any), K2 direction, K3 direction, K4 direction
- Dropdowns: Cloud2 state, Cloud3 state, Price pos vs C3
- Checkboxes: K2+K3 both crossing 50, All 4 rising, ATR expanding
- Filters: Grade, Direction (LONG/SHORT), Entry type (fresh/ADD/RE)
- Outcome filter: All / TP / SL / saw_green, MFE threshold
Results shown instantly:
- N trades matched (out of total)
- Win rate, avg net PnL, avg MFE (ATR), avg MAE (ATR)
- Grade breakdown within match (% A vs B vs C vs D)
- Complement shown alongside: "trades NOT matching this filter: win rate Y%"

Example: User sets K1=25–60, K1 rising, K2 rising, K3 rising, ATR expanding → sees "342 trades matched, 38% win rate. Complement: 2,800 trades, 26% win rate. Delta: +12%"

### Panel 4 — Exit State Analysis (MFE bar vs exit bar)
For losing trades: what did the indicators look like at the MFE bar vs the exit bar?
- Which indicator moved first before the reversal (K2 drop, C2 flip, AVWAP cross)?
- Ranked list: "K2 dropped through 50 in 73% of losses, median 3 bars before exit"

### Panel 5 — Validation
- "Run on 10 random coins" button
- Shows same scorecard + findings for the random batch
- Delta column: does the pattern hold?

---

## Architecture: 6 Modules in `vince/`

### Build Order (strict — each depends on previous)

| Order | Module | Purpose |
|-------|--------|---------|
| 1 | `vince/schema.py` | Data contracts: IndicatorSnapshot, TradeRecord, VinceResult |
| 2 | `vince/enricher.py` | Trade CSV + OHLCV → enriched DataFrame with indicator states at entry/MFE/exit bars |
| 3 | `vince/analyzer.py` | All 5 analysis types: coin scorecard, LSG anatomy, TP sweep, constellation, temporal delta |
| 4 | `vince/sampling.py` | Random coin selector + backtester runner + CSV collector |
| 5 | `vince/report.py` | Aggregates results from analyzer, formats for dashboard |
| 6 | `vince/dashboard_tab.py` | Streamlit tab: all 5 panels, uses report.py output |

No `tensor_store.py` in MVP. PyTorch/GPU deferred to v2.1 when scaling to 400 coins. Pandas + numpy sufficient for 90K trades.

---

## Module Detail

### `vince/schema.py`
Dataclasses only. No logic.
```
IndicatorSnapshot:
  bar_idx: int
  moment: str          # "entry" | "mfe" | "mae" | "exit"
  k1: float            # stoch_9
  k2: float            # stoch_14
  k3: float            # stoch_40
  k4: float            # stoch_60
  cloud3_bull: bool
  cloud2_bull: bool
  price_pos: int       # -1 / 0 / 1
  atr: float

EnrichedTrade:
  symbol: str
  direction: str
  grade: str
  entry_bar: int
  exit_bar: int
  mfe_bar: int         # bar where MFE occurred (found by enricher walking OHLCV)
  mfe: float           # dollars
  mae: float           # dollars
  mfe_atr: float       # MFE / (entry_atr * notional / entry_price)
  mae_atr: float
  net_pnl: float
  exit_reason: str
  saw_green: bool
  snapshots: dict[str, IndicatorSnapshot]  # keyed by moment
```

### `vince/enricher.py`
Input: trades_df (from trade CSV), ohlcv_df (parquet), signal_params (dict)
Process:
1. Re-run `compute_signals_v383(ohlcv_df, signal_params)` → indicator DataFrame
2. For each trade:
   a. Look up indicators at entry_bar → entry snapshot
   b. Walk [entry_bar..exit_bar], find bar with max unrealized PnL → mfe_bar
   c. Look up indicators at mfe_bar → mfe snapshot
   d. Look up indicators at exit_bar → exit snapshot
   e. Compute mfe_atr using ATR at entry_bar and notional from params
3. Returns: list of EnrichedTrade
Key reuse: `compute_signals_v383` from `signals/four_pillars_v383.py` (already exists)
Key reuse: `FourPillarsPlugin.enrich_ohlcv()` from `strategies/four_pillars.py` (already exists)

### `vince/analyzer.py`
Input: list[EnrichedTrade] (one coin or many)
Core function — the query engine:
- `query_constellation(trades, filters: ConstellationFilter)` → QueryResult
  - ConstellationFilter: all query dimensions (K1 range, K2 direction, ATR state, grade, etc.)
  - QueryResult: n_matched, win_rate, avg_mfe_atr, avg_mae_atr, avg_net_pnl, grade_breakdown, complement stats
Other functions:
- `coin_scorecard(trades)` → DataFrame: symbol × metrics
- `lsg_anatomy(trades)` → dict: mfe_distribution, pct_above_tp, optimal_tp_curve
- `optimal_tp_sweep(trades, tp_range)` → Series: tp_mult → net_pnl
- `temporal_delta(trades)` → DataFrame: indicator × bars_before_exit → frequency
No ML. Pure pandas/numpy filtering and groupby statistics.

### `vince/sampling.py`
- `select_random_coins(n, exclude=None, seed=None)` → list of symbols
- `run_batch(symbols, params)` → trades_df (runs backtester per coin, concatenates CSVs)
- Uses existing backtester: `Backtester384` from `engine/backtester_v384.py`
- Uses existing signal pipeline: `compute_signals_v383` from `signals/four_pillars_v383.py`
- Uses existing data loader: parquet files from `data/cache/`

### `vince/report.py`
- `VinceReport` dataclass: all analyzer outputs combined
- `build_report(enriched_trades, params)` → VinceReport
- Serializable to JSON for caching (don't re-run analysis on same data)

### `vince/dashboard_tab.py`
- `render_vince_tab(report: VinceReport)` — called from dashboard_v391.py or dashboard_v392.py
- 5 panels as described above
- "Run on 10 random coins" button triggers `sampling.py` + full pipeline
- Filters: by coin, by grade, by direction, by date range

---

## Data Flow

```
Existing Trade CSV
      |
      v
enricher.py  <--  OHLCV parquets (data/cache/)
      |            signals/four_pillars_v383.py (reused)
      v
list[EnrichedTrade]
      |
      v
analyzer.py
      |
      v
VinceReport
      |
      v
dashboard_tab.py  -->  5 panels on screen
```

---

## Critical Files to Modify / Create

| Action | File | Notes |
|--------|------|-------|
| CREATE | `vince/__init__.py` | Empty |
| CREATE | `vince/schema.py` | Dataclasses |
| CREATE | `vince/enricher.py` | Core workhorse |
| CREATE | `vince/analyzer.py` | Analysis functions |
| CREATE | `vince/sampling.py` | Coin selector + batch runner |
| CREATE | `vince/report.py` | Report aggregator |
| CREATE | `vince/dashboard_tab.py` | Streamlit tab |
| CREATE | `docs/vince/VINCE-PROJECT.md` | Master project index (first, before code) |
| CREATE | `scripts/build_vince_v2.py` | Build script (mandatory) |
| CREATE | `tests/test_vince_enricher.py` | Enricher tests |
| CREATE | `tests/test_vince_analyzer.py` | Analyzer tests |
| REUSE (no edit) | `signals/four_pillars_v383.py` | Signal pipeline |
| REUSE (no edit) | `strategies/four_pillars.py` | Strategy plugin |
| REUSE (no edit) | `engine/backtester_v384.py` | Trade CSV generator |
| REUSE (no edit) | `engine/position_v384.py` | Trade384 dataclass |

Dashboard integration (add Vince tab to dashboard_v392):
- One additional patch in `build_dashboard_v392.py` to import and render `vince/dashboard_tab.py`

---

## Constraints (non-negotiable)

- NEVER reduce trade count. Vince observes only — does not filter entries.
- NO hardcoded coin names. Works on any CSV produced by the backtester.
- NO hardcoded parameters. All indicator params passed via strategy plugin.
- Build script creates ALL files, py_compile tests each one before proceeding.
- All functions have docstrings.
- All log entries have timestamps.

---

## Verification

1. Run build script: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_vince_v2.py"` — all files created, all py_compile pass
2. Run enricher tests: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_vince_enricher.py"` — synthetic 100-bar OHLCV, 5 trades, verify snapshots at correct bars
3. Run analyzer tests: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_vince_analyzer.py"` — known input trades, verify scorecard/LSG/TP sweep outputs
4. Smoke test: provide RIVERUSDT trade CSV from results/ → enrich → analyze → confirm Panel 1 shows correct win rate matching dashboard_v391 output
5. Dashboard: `streamlit run "scripts/dashboard_v392.py"` → Vince tab visible → run on RIVERUSDT → 5 panels populated

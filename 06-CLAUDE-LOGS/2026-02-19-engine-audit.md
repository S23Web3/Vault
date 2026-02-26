# Engine Audit Session
**Date:** 2026-02-19
**Model:** Opus 4.6
**Status:** AUDIT COMPLETE

---

## Session Purpose

User requested thorough audit of the Four Pillars backtester engine and trade data BEFORE proceeding with Vince ML v2 build. "The results are too good to be true."

## Files Read

| File | Lines | Purpose |
|------|-------|---------|
| 06-CLAUDE-LOGS/2026-02-18-vince-scope-session.md | 99 | Last session log |
| 06-CLAUDE-LOGS/2026-02-18-dashboard-audit.md | 162 | Previous audit |
| 06-CLAUDE-LOGS/2026-02-18-dashboard-v392-build.md | 81 | v3.9.2 build log |
| engine/backtester_v384.py | 581 | Core execution engine |
| engine/position_v384.py | 296 | Position slot management |
| engine/commission.py | 107 | Commission model |
| engine/avwap.py | 53 | AVWAP tracker |
| signals/state_machine_v383.py | 340 | Entry signal state machine |
| scripts/build_dashboard_v392.py | 567 | v3.9.2 build script |
| portfolio_trades_20260218_155102.csv | ~5000+ rows | 10-coin portfolio trades (run 1) |
| portfolio_trades_20260218_155344.csv | ~3000+ rows | 10-coin portfolio trades (run 2) |

## Audit Results

### PnL Math -- VERIFIED CORRECT
- MAVUSDT LONG A: (0.09029843 - 0.09112) / 0.09112 * 10000 = -90.16. CSV: -90.163. MATCH.
- MAVUSDT SHORT A: (0.08975 - 0.08896580) / 0.08975 * 10000 = 87.38. CSV: 87.376. MATCH.
- MAVUSDT SCALE_1: (0.08686 - 0.08649) / 0.08649 * 5000 = 21.39. CSV: 21.39. MATCH.

### Commission -- VERIFIED CORRECT
- Model uses DOLLAR values, not percentages
- Standard trades (A/B/C/D/R): taker entry $8.0 + maker exit $2.0 = $10.0
- Limit trades (RE/ADD): maker $2.0 + maker $2.0 = $4.0
- SCALE_1 (half): proportional entry $4.0 + maker exit $1.0 = $5.0
- Total equity impact for scale-out position: $8 + $1 + $1 = $10 (correct)

### Exit Prices -- VERIFIED
- Every SL trade: exit_price == sl_price exactly
- Every TP trade: exit_price == tp_price exactly
- Checked 20+ trades across both CSVs

### SL Placement -- VERIFIED
- ATR-based: entry +/- ATR * sl_mult (2.0)
- Derived ATR values match realistic ranges for coin prices

### Lookahead Bias -- NONE DETECTED
- State machine sequential, no future data access
- check_exit() before update_bar() -- uses prior bar SL
- ATR backward-looking only
- Entries at close[i] -- signal fires at bar close

### Known Bug CONFIRMED
- Scale-out remainder: commission=9.0 in CSV (should be 5.0)
- Cause: line 147 uses full entry_commission after scale-out
- Equity UNAFFECTED -- entry commission deducted once at entry time
- CSV-only reporting issue

### Dashboard v3.9.2 -- SAFE
- 10 patches = timing instrumentation only
- Zero changes to signal/engine/PnL/commission logic
- Numba v2 modules: identical algorithms with @njit wrappers
- Still needs numerical parity verification (RIVERUSDT 5m)

## Optimism Factors (Backtest vs Live)

| Factor | Risk Level | Notes |
|--------|------------|-------|
| No slippage model | LOW | $10K notional on major perps, minimal impact |
| No funding rate | LOW | Most trades held < 30min on 5m |
| No partial fills | LOW | Standard notional size |
| SL at exact level | LOW | 24/7 crypto, deep books |
| Per-coin TP optimization | MEDIUM | In-sample optimized TP may not persist |
| Survivorship bias | LOW | 1-year window, major perps |

## User Question Clarified

User asked: "how does the commission percentage go half for SCALE_1?"
Answer: Commission model works in dollar values. The entry commission ($8.0) is PROPORTIONALLY ATTRIBUTED to each trade record (8.0 * 5000/10000 = $4.0). The rate doesn't change -- only the dollar attribution for CSV reporting. Equity accounting is correct: $8 entry + $1 exit + $1 exit = $10 total.

## Verdict

**Engine is mechanically correct. Trades are REAL backtested results.**
Conservative discount of 5-10% net PnL for execution friction (slippage + funding) recommended when projecting live performance.

---

## Next Steps (from user)
1. Continue Vince ML v2 scoping
2. Verify v3.9.2 numerical parity vs v3.9.1
3. Fix scale-out commission CSV bug (low priority, equity unaffected)

---

## SESSION CONTINUED: Vince v2 Architecture Breakdown

### Context
- Read handoff doc (`~/.claude/plans/functional-orbiting-rabbit.md`, 446 lines)
- User confirmed: relationship questions can be added later (just new queries on same data)
- User approved: move to architecture breakdown

### Architecture Decisions Made

1. **Directory**: `vince/` (clean, separate from `ml/` which is Vicky's v1 code)
2. **AVWAP/SL issue**: Option B chosen -- enricher runs lightweight AVWAP/SL simulator. Duplicates formulas but keeps strategy/analyst separation clean.
3. **Bar index alignment**: Use entry_datetime/exit_datetime to match bars, NOT bar indices (indices are relative to filtered DataFrame, could mismatch raw OHLCV)
4. **Scale-out handling**: Group by (symbol, entry_bar, direction) = one position for constellation purposes
5. **MFE/MAE bars**: Enricher walks [entry..exit] computing unrealized PnL, finds max/min bars

### 7 Modules Designed

| Module | Purpose |
|--------|---------|
| schema.py | IndicatorDef + MomentDef + SnapshotSchema dataclasses |
| enricher.py | Trade CSV + OHLCV -> enriched constellation snapshots (the workhorse) |
| tensor_store.py | DataFrame -> PyTorch float32 tensor + column map + persistence |
| engine.py | 5 analysis types on GPU tensors (see below) |
| validation.py | Cross-validation: coin batches + time periods + robustness scoring |
| sampling.py | Random coin batch selector + backtester runner |
| dashboard_tab.py | Streamlit tab: explorer, constellation viewer, recommendations |

### Feature Vector Size (Four Pillars)
- 24 static features per moment (stochs, EMAs, clouds, ATR, AVWAP, position state)
- 44 dynamic features per moment (slopes, speeds, zone durations at lookbacks 3/5/10)
- 68 features * 10 moments = ~680 features per trade
- 90K trades * 680 = ~244 MB float32. Fits on 12GB RTX 3060.

### 5 Analysis Types Identified in engine.py

| Type | Example Question | Method |
|------|-----------------|--------|
| Parameter Sweep | "Optimal TP mult per coin?" | Simulate TP values 0.5-5.0, find net PnL peak |
| Conditional Grouping | "K2+K3 both crossing 50 = better?" | Split by condition, compare outcome distributions |
| Feature Correlation | "AVWAP sigma vs cloud spread?" | Pearson/Spearman r, scatter |
| Temporal Delta | "What moves first before losses?" | Diff MFE snapshot vs exit snapshot, rank by magnitude |
| Multi-Condition Filter | "K1<60 AND C3 tight AND K3 crossing?" | Progressive intersection, compare to complement |

### UNRESOLVED (for next session)
- **Unified abstraction vs separate functions** for 5 analysis types -- user didn't decide yet
- **Output format**: What exactly does Vince show on screen? Parameter recs? Pattern insights? Exit signals? All?
- **Build order confirmation**: Schema -> Enricher -> TensorStore -> Engine -> Validation -> Sampling -> Dashboard
- **Strategy plugin update**: Add `get_vince_schema()` to base.py and four_pillars.py
- User was about to answer "what's your mental model of what you'd see on screen" when context ran low

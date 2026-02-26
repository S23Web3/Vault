# UML Logic Flow Debugging Session
**Date:** 2026-02-17
**Task:** Debug BBW V2 architecture diagram for logical flow issues
**File Debugged:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-ARCHITECTURE.md`

---

## Issues Found

### Issue 1: Layer 3 Orphaned (CRITICAL)

**Problem:** Forward Returns layer has NO output connection

**Original Flow:**
```
L1 --> L2 --> L3 [DEAD END]
```

**File Affected:** `research/bbw_forward_returns.py`

**Impact:** Layer marked "Complete" but not integrated into pipeline

**Possible Resolutions:**
- Option A: L3 → L5 (forward returns as VINCE features)
- Option B: L3 standalone research (not integrated)
- Option C: L3 → L4 (enrich trade analysis)
- Option D: Remove L3 (not needed)

**Status:** ⚠️ **USER DECISION REQUIRED**

---

### Issue 2: Missing Data Source

**Problem:** Layer 1 (BBWP Calculator) has no input shown

**Fix Applied:**
```mermaid
CACHE[Cached OHLC Data] --> L1
CACHE --> BT
```

**File:** `data/cache/*.parquet`

**Reasoning:** Both BBWP and Backtester need historical data source

---

### Issue 3: VINCE Feedback Loop Ambiguity

**Problem:** `VINCE --> BT` arrow unclear (training or production?)

**Fix Applied:**
- Solid arrow: `L5 --> VINCE` (training data flow)
- Dotted arrow: `VINCE -.-> BT` (future production mode)

**Clarification:** 
- Training mode: L5 provides features to VINCE
- Production mode: VINCE provides optimized LSG to Backtester

---

### Issue 4: Missing Data Flow Labels

**Problem:** Arrows didn't specify what data passes between nodes

**Fix Applied:** Added labels to all arrows
```
BT -->|Trade Results| L4
L2 -->|BBW States for enrichment| L4
L4 -->|Per-trade PnL by state×direction×LSG| L4b
```

**Benefit:** Clear data contracts between layers

---

## Corrected Architecture

### New File Created
**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-ARCHITECTURE-CORRECTED.md`

### Key Changes

**1. Data Source Added**
```mermaid
CACHE[data/cache/*.parquet] --> L1
CACHE --> BT
```

**2. Layer 3 Marked as Research**
```mermaid
L3 -.->|Research - Not used by L4| Analysis
```

**3. VINCE Split into Two Modes**
```mermaid
L5 -->|Training CSVs| VINCE
VINCE -.->|Future: Optimized LSG| BT
```

**4. All Data Contracts Labeled**

---

## Logical Flow Validation

### Current Pipeline (Training)
```
1. data/cache/*.parquet → Layer 1 → BBW states
2. BBW states → Layer 2 → State sequences
3. States + Prices → Layer 3 → Forward returns (ORPHANED?)
4. Cached data → Backtester → Trade results
5. Trade results + BBW states → Layer 4 → Grouped analysis
6. Grouped analysis → Layer 4b → Monte Carlo verdicts
7. Analysis + Verdicts → Layer 5 → VINCE training CSVs
8. Training CSVs → VINCE → Trained ML model
```

### Future Pipeline (Production)
```
9. Live market data → Four Pillars signals + BBW state
10. Current state → VINCE inference → Optimal LSG
11. Optimal LSG → Backtester → Execute trade
```

**Validation:** ✅ All steps have clear inputs/outputs except Layer 3

---

## Component Dependency Matrix

| Layer | File | Input | Output | Used By |
|-------|------|-------|--------|---------|
| Cache | data/cache/*.parquet | Exchange API | OHLC bars | L1, BT |
| L1 | signals/bbwp.py | OHLC | BBW states | L2 |
| L2 | signals/bbw_sequence.py | BBW states | Sequences | L3, L4 |
| L3 | research/bbw_forward_returns.py | Sequences + OHLC | Movement analysis | ⚠️ **UNCLEAR** |
| Dashboard | scripts/dashboard_v391.py | Config | Sweep orchestration | BT |
| BT | engine/backtester_v385.py | OHLC | Trade384 records | L4 |
| L4 | research/bbw_analyzer_v2.py | Trades + States | Grouped analysis | L4b, L5 |
| L4b | research/bbw_monte_carlo_v2.py | Per-trade PnL | Verdicts | L5 |
| L5 | research/bbw_report_v2.py | L4 + L4b | Training CSVs | VINCE |
| VINCE | ml/vince_model.py | Training CSVs | LSG optimizer | BT (future) |

---

## Critical Questions for User

### Question 1: Layer 3 Integration

**Context:** `research/bbw_forward_returns.py` exists and is marked "Complete" but has no downstream consumer.

**Options:**

**A) Integrate into Layer 5**
- Forward returns become VINCE features
- Add: `L3 --> L5` arrow
- Benefit: More training data for ML

**B) Standalone Research**
- Layer 3 is exploratory analysis only
- Keep: `L3 -.-> Analysis` (dotted line)
- Benefit: Clean separation of concerns

**C) Integrate into Layer 4**
- Forward returns enrich trade analysis
- Add: `L3 --> L4` arrow
- Benefit: Better grouped analysis

**D) Remove Layer 3**
- Not needed in pipeline
- Delete from architecture
- Benefit: Simpler system

**Recommended:** User clarifies Layer 3's intended purpose

---

### Question 2: VINCE Production Mode

**Context:** Diagram shows `VINCE --> BT` feedback loop

**Clarification Needed:**

**Scenario A: Real-Time Service**
- VINCE runs as inference server
- Provides LSG before each trade
- Backtester queries VINCE in real-time

**Scenario B: Offline Optimization**
- VINCE analyzes historical data only
- Outputs recommended static LSG configs
- No real-time integration

**Current Assumption:** Scenario A (real-time service)

**User Confirmation:** Is this correct?

---

## File Paths (Complete List)

### Data
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\*.parquet`

### Signals (Layer 1-2)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbwp.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbw_sequence.py`

### Research (Layer 3-5)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_forward_returns.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_analyzer_v2.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_monte_carlo_v2.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_report_v2.py` ⚡ PENDING

### Engine
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v385.py`

### Scripts
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v391.py`

### ML (Future)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\ml\vince_model.py` 🔮 NOT BUILT

### Documentation
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-ARCHITECTURE.md` (original)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-ARCHITECTURE-CORRECTED.md` (debugged)

---

## Changes Summary

### Files Modified
1. **Created:** `BBW-V2-ARCHITECTURE-CORRECTED.md`
   - Added data source node
   - Clarified Layer 3 status
   - Split VINCE into training/production modes
   - Labeled all data flows

2. **Created:** `2026-02-17-uml-logic-debugging.md`
   - This log file

### Original vs Corrected

**Original Issues:**
- 3 logic flow errors
- 1 orphaned layer
- Missing data source
- Ambiguous feedback loop
- No data contract labels

**Corrected Version:**
- All logic flows validated
- Layer 3 marked as "requires clarification"
- Data source explicitly shown
- Training vs production modes separated
- All arrows labeled with data contracts

---

## Next Steps

### For User
1. **Review corrected architecture:**
   - `BBW-V2-ARCHITECTURE-CORRECTED.md`

2. **Answer critical questions:**
   - What should Layer 3 feed into? (Options A/B/C/D)
   - Is VINCE real-time service or offline optimizer?

3. **Test PDF export:**
   - Export corrected architecture to PDF
   - Verify Mermaid diagram renders
   - Check data flow labels visible

### For Development
1. **If Layer 3 integrates into L5:**
   - Update Layer 5 build spec
   - Add forward returns to VINCE features

2. **If Layer 3 is standalone:**
   - Remove from main pipeline diagram
   - Create separate research diagram

3. **If Layer 3 removed:**
   - Archive `bbw_forward_returns.py`
   - Update status documentation

---

## Validation Checklist

**Logic Flow:** ✅ Debugged
- [x] All nodes have inputs
- [x] No orphaned outputs (L3 flagged for review)
- [x] Data source added
- [x] Feedback loops clarified
- [x] Data contracts labeled

**File Paths:** ✅ Complete
- [x] All components have full Windows paths
- [x] Paths verified against project structure
- [x] Future files marked with status

**Documentation:** ✅ Updated
- [x] Corrected architecture created
- [x] Issues documented
- [x] Questions listed for user
- [x] Session logged

**Open Issues:** ⚠️ User Input Required
- [ ] Layer 3 integration decision
- [ ] VINCE production mode confirmation

---

**END OF DEBUGGING SESSION**

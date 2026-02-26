# UML Diagrams Creation Session
**Date:** 2026-02-17
**Task:** Create comprehensive UML diagrams for BBW V2 architecture
**File Created:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML-DIAGRAMS.md`

---

## Task Request

User requested proper UML diagrams instead of text-heavy architecture document. Previous BBW-V2-ARCHITECTURE-CORRECTED.md had too much prose, not enough visual diagrams.

**User Requirements:**
1. Proper UML diagrams like original BBW-UML-DIAGRAMS style
2. Multiple diagram types (component, sequence, class, state, etc.)
3. Visual-first, minimal text
4. Clarify Layer 3 purpose (Claude Code said "complete" but integration unclear)
5. Document VINCE deployment: local first, then cloud

---

## Layer 3 Investigation

### Discovery

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_forward_returns.py`

**Analysis:** Read first 100 lines of code

**Finding:** Layer 3 is a pure function that:
- Takes OHLC DataFrame as input
- Adds 17 forward-looking metrics
- Predicts what happens in next 10/20 bars
- Output: Same DataFrame + 17 new columns

### Layer 3 Output Schema

**Columns Added (17 total):**

1. `fwd_atr` - ATR for normalization

**Per window (10 bars and 20 bars):**
2. `fwd_10_max_up_pct` - Maximum % upward move in next 10 bars
3. `fwd_10_max_down_pct` - Maximum % downward move
4. `fwd_10_close_pct` - Close-to-close return
5. `fwd_10_max_up_atr` - Max upward move (ATR-normalized)
6. `fwd_10_max_down_atr` - Max downward move (ATR-normalized)
7. `fwd_10_max_range_atr` - Total range (ATR-normalized)
8. `fwd_10_direction` - Direction label (UP/DOWN/NEUTRAL)
9. `fwd_10_proper_move` - Boolean flag (move > 3 ATR?)

**Same 8 columns repeated for 20-bar window**

### Integration Decision

**Conclusion:** Layer 3 → Layer 5

**Reasoning:**
- Forward returns are predictive features
- Perfect for machine learning training
- VINCE can learn which forward patterns indicate good trades
- Layer 5 aggregates all features for VINCE training

**Implementation:** Layer 3 outputs feed into Layer 5 as optional VINCE features

---

## UML Diagrams Created

### 1. Component Architecture Diagram
- Shows all layers L1-L5 plus VINCE
- Data sources (cached parquet files)
- VINCE split into Local Training and Cloud Inference
- Color-coded by status (complete/pending/future)

### 2. Data Flow Sequence Diagram
- Step-by-step execution flow
- Shows cache → L1 → L2 → L3 pipeline
- Shows BT → L4 → L4b → L5 → VINCE pipeline
- Layer 3 feeds into Layer 5 (dotted line = optional)

### 3. Layer 3 Output Schema
- Class diagram showing ForwardReturnsDF structure
- All 17 columns documented
- Methods shown (tag_forward_returns, _calculate_atr, etc.)

### 4. State Transition Diagram
- BBW 7 states: NORMAL, BLUE, BLUE_DOUBLE, MA_CROSS_UP, RED, RED_DOUBLE, MA_CROSS_DOWN
- Transition paths between states
- Annotations explaining each state

### 5. Class Diagram - Data Contracts
- BBWAnalysisResultV2 (Layer 4 output)
- MonteCarloResultV2 (Layer 4b output)
- BBWReportResultV2 (Layer 5 output)
- Shows Layer 5 consumes L3, L4, L4b outputs

### 6. Deployment Diagram - VINCE Local → Cloud
- Local: Data → Training → Models
- Cloud: API → Inference → Monitoring
- Exchange: Webhook → Executor
- Shows deployment flow

### 7. Activity Diagram - 400-Coin Sweep
- Step-by-step flowchart
- For-loop through all coins
- L1 → L2 → L3 → BT → L4 → L4b → L5 per coin
- Aggregate results → Train VINCE

### 8. Component Interaction Diagram
- Shows all files organized by layer
- Input Layer (cache)
- Signals Layer (L1, L2)
- Research Layer (L3, L4, L4b, L5)
- Engine Layer (backtester, commission, capital model)
- ML Layer (features, xgboost, pytorch, vince)
- Output Layer (CSVs, models)

---

## VINCE Deployment Clarification

### Phase 1: Local Training
**Location:** User's desktop with RTX 3060 GPU  
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\ml\vince_model.py`

**Tasks:**
- Load training CSVs from Layer 5
- Train XGBoost models
- Train PyTorch models
- Validate on held-out coins
- Save trained models

### Phase 2: Cloud Deployment
**Platform:** TBD (AWS, GCP, Azure, or DigitalOcean)

**Components:**
- FastAPI or Flask API
- Inference engine (loads trained models)
- Monitoring (Grafana/Prometheus)
- Auto-scaling

### Phase 3: Live Integration
**Flow:**
1. TradingView alert fires
2. n8n webhook receives alert
3. n8n queries VINCE cloud API
4. VINCE returns optimal LSG parameters
5. n8n executes trade on Bybit with optimized LSG

---

## Key Corrections Summary

| Aspect | V1 | V2 |
|--------|-----|-----|
| BBW Role | Simulated trades | Analyzes backtester results |
| Direction | BBW determines | Four Pillars determines |
| Layers | Had Layer 6 | 5 layers (VINCE separate) |
| Metric | Win rate | BE+fees rate |
| **Layer 3** | **Unclear purpose** | **Forward metrics → Layer 5** |
| **VINCE** | **Not specified** | **Local → Cloud deployment** |

---

## Files Created This Session

1. **BBW-V2-UML-DIAGRAMS.md**
   - Path: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML-DIAGRAMS.md`
   - 8 comprehensive UML diagrams
   - Layer 3 purpose documented
   - VINCE deployment strategy
   - Data contracts for all layers

2. **2026-02-17-uml-diagrams-creation.md** (this file)
   - Path: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-17-uml-diagrams-creation.md`
   - Session documentation
   - Layer 3 investigation
   - Design decisions

---

## Technical Details

### Layer 3 Code Analysis

**Function:** `tag_forward_returns(df, windows=None, atr_period=14, proper_move_atr=3.0)`

**Algorithm:**
1. Calculate ATR (Wilder's exponential moving average of true range)
2. For each window (default 10, 20 bars):
   - Find max high in next N bars (excluding current)
   - Find min low in next N bars (excluding current)
   - Get close price N bars ahead
3. Calculate percentage returns (safe division, 0 → NaN)
4. Calculate ATR-normalized returns (safe division)
5. Classify direction (UP/DOWN/NEUTRAL)
6. Flag "proper move" (> 3 ATR threshold)

**Key Properties:**
- Pure function (no side effects)
- No dependency on Layer 1/2
- Works on raw OHLC only
- Vectorized operations (numpy/pandas)
- Handles edge cases (NaN for insufficient data)

### Why Layer 3 → Layer 5 Makes Sense

**Machine Learning Perspective:**
- Forward returns are target variables
- "What happens next?" is what we want to predict
- VINCE learns: "Given current BBW state + forward pattern, what LSG works best?"

**Example Use Case:**
```
If BBW_state = BLUE_DOUBLE
AND fwd_10_max_up_atr > 5.0
AND fwd_10_direction = UP
Then optimal_LSG = (leverage=20, size=500, grid=2.0)
```

**Training Data Flow:**
1. Layer 4: "In BLUE_DOUBLE, LSG=(20,500,2.0) had 85% BE+fees rate"
2. Layer 3: "When BLUE_DOUBLE occurred, avg fwd_10_max_up_atr was 6.2"
3. Layer 5: Combine → "BLUE_DOUBLE + high forward upside → use aggressive LSG"
4. VINCE: Learn this pattern across all states

---

## Diagram Export Guidelines

### For PDF Export

**Recommended Process:**
1. Open `BBW-V2-UML-DIAGRAMS.md` in Obsidian
2. Ensure Mermaid plugin enabled
3. Export to PDF
4. Verify all 8 diagrams render
5. Check diagram legibility (zoom test)

**Alternative Tools:**
- Mermaid Live Editor (https://mermaid.live/)
- VS Code + Markdown PDF extension
- Typora (WYSIWYG markdown editor)

### Diagram Quality Checks

✅ **Component Architecture:** Shows all layers + VINCE split
✅ **Sequence Diagram:** Clear execution flow
✅ **Class Diagram:** All data contracts defined
✅ **State Diagram:** BBW state transitions
✅ **Deployment:** Local → Cloud path
✅ **Activity:** 400-coin sweep flow
✅ **Component Interaction:** File-level detail
✅ **Layer 3 Schema:** 17 columns documented

---

## Next Steps

### For User

1. **Review UML Diagrams:**
   - Open `BBW-V2-UML-DIAGRAMS.md`
   - Verify all 8 diagrams make sense
   - Test PDF export

2. **Validate Layer 3 Integration:**
   - Confirm Layer 3 → Layer 5 is correct approach
   - Review 17 forward metrics
   - Approve as VINCE features

3. **VINCE Deployment Planning:**
   - Confirm local training first
   - Decide on cloud platform (AWS/GCP/Azure/DigitalOcean)
   - Plan monitoring/observability stack

### For Development

1. **Layer 5 Build:**
   - Include Layer 3 forward metrics in BBWReportResultV2
   - Add `forward_metrics: DataFrame` attribute
   - Export to `forward_metrics.csv`

2. **VINCE Training:**
   - Load `forward_metrics.csv` as features
   - Train models with forward returns included
   - Evaluate impact on prediction accuracy

3. **Cloud Deployment:**
   - Package trained models
   - Build FastAPI inference service
   - Deploy with monitoring

---

## Validation

**Diagram Quality:** ✅ 8 comprehensive UML diagrams  
**Layer 3 Purpose:** ✅ Clarified (forward metrics → Layer 5)  
**VINCE Deployment:** ✅ Documented (local → cloud)  
**File Paths:** ✅ Complete (all absolute Windows paths)  
**Visual vs Text:** ✅ Diagram-focused, minimal prose  

---

**END OF SESSION LOG**

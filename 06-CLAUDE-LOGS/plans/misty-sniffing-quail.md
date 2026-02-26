# Four Pillars v3.8 — Cloud 3 Directional Filter + Python Conversion + Vince ML Analysis

## Context

**Problem Identified**: The Four Pillars v3.7.1 strategy takes a SHORT position but continues to activate LONG signals, which conflicts with manual trading decisions. Root cause analysis reveals:

1. **Two independent state machines** (long + short) run in parallel with no mutual exclusion
2. **Ripster filter is OFF by default** (`i_useRipster = false` on line 54)
3. **B signals bypass Cloud 3 check** entirely (A signals check `ripster_ok` which is OFF, C signals check `price_pos`)
4. **Entry gates don't filter by direction** — only check if flat or opposite position exists
5. **Result**: In a bearish context (price below Cloud 3), long signals can still fire and execute

**User's Goal**:
- Fix the directional filter issue in v3.8
- Create **BOTH Pine Script AND Python versions** of v3.8
- Use **Vince (ML tool)** to analyze 100+ coins over 3 months to find "best practices" that manual testing couldn't discover
- Identify optimal BE raise triggers, re-entry conditions, and signal filtering rules

---

## Root Cause Analysis (from Code Exploration)

### Current v3.7.1 Entry Logic (Lines 272-276)
```pine
bool enter_long_a  = long_signal and (isFlat or posDir == "SHORT") and cooldownOK
bool enter_short_a = short_signal and (isFlat or posDir == "LONG") and cooldownOK

bool enter_long_bc  = (long_signal_b or long_signal_c) and
                      ((i_bOpenFresh and isFlat) or (not isFlat and posDir == "LONG"))
                      and cooldownOK
bool enter_short_bc = (short_signal_b or short_signal_c) and
                       ((i_bOpenFresh and isFlat) or (not isFlat and posDir == "SHORT"))
                       and cooldownOK
```

**Missing**: ANY Cloud 3 directional bias check at entry gates.

### Ripster Filter (Lines 106-113)
```pine
bool ripster_ok_long  = not i_useRipster or cloud3_bull or price_pos >= 0
bool ripster_ok_short = not i_useRipster or not cloud3_bull or price_pos <= 0
```

**Problem**:
- OFF by default (`i_useRipster = false`)
- When OFF, always returns `true` (no-op)
- Only gates A/B signal generation, NOT entry execution
- C signals check `price_pos` directly but A/B don't

### Signal Generation (Lines 139-143 for longs)
```pine
if long_others == 3 and ripster_ok_long and d_ok_long
    long_signal := true                    // A signal
else if long_others >= 2 and i_allowBTrades and ripster_ok_long and d_ok_long
    long_signal_b := true                  // B signal (no Cloud 3 check!)
else if long_14_seen and i_allowCTrades and price_pos == 1
    long_signal_c := true                  // C signal (has Cloud 3 check)
```

**The Gap**: B signals check `ripster_ok_long` (which is OFF = no-op), not `price_pos` like C signals do.

---

## Solution: Four Pillars v3.8

### Core Changes

#### 1. Cloud 3 Directional Filter (ALWAYS ON)
- **Bearish (price < Cloud 3 bottom)**: Block ALL long signals, only allow shorts
- **Bullish (price > Cloud 3 top)**: Block ALL short signals, only allow longs
- **Inside Cloud 3 (chop zone)**: Allow BOTH directions (current behavior) OR require additional confirmation (user choice)

#### 2. ATR-Based BE Raise (replacing fixed $2/$4/$6)
- **Trigger**: When profit > `i_beTrigger × ATR` (e.g., 0.5 ATR)
- **Lock**: Move SL to entry + `i_beLock × ATR` (e.g., 0.3 ATR to cover $8 commission)
- **Formula from Hilpisch Ch 11**: ATR must be multiplied by leverage (2% ATR × 20x = 40% SL level)

#### 3. MFE/MAE Tracking
- Track `entry_price`, `min_price`, `max_price` for every trade
- TSL based on `(price - max_price) / entry_price` NOT `(price - entry_price) / entry_price`
- Export trade data for ML analysis

#### 4. Commission Updated
- **0.08%** = $8/side on $10K notional (20x leverage)
- Use `strategy.commission.cash_per_order = 8`

---

## Implementation Plan

### Part 1: Pine Script v3.8

**File**: `02-STRATEGY/Indicators/four_pillars_v3_8_strategy.pine`

#### Changes to Make:

**1. Add Cloud 3 Direction Variable (after line 103)**
```pine
// Cloud 3 directional bias
int cloud3_direction = price_pos  // -1 = bearish, 0 = inside, 1 = bullish
bool cloud3_allows_long  = cloud3_direction >= 0  // Allow longs when above or inside Cloud 3
bool cloud3_allows_short = cloud3_direction <= 0  // Allow shorts when below or inside Cloud 3
```

**2. Update Ripster Filter to ALWAYS CHECK Cloud 3 (replace lines 106-113)**
```pine
// Cloud 3 directional filter (ALWAYS ON, not optional)
bool ripster_ok_long  = cloud3_allows_long
bool ripster_ok_short = cloud3_allows_short

// Optional 60-10 D filter (keep existing)
bool d_ok_long  = not i_use60D or stoch_60_10_d > 20
bool d_ok_short = not i_use60D or stoch_60_10_d < 80
```

**3. Add Cloud 3 Check to ALL Entry Gates (update lines 272-276)**
```pine
bool enter_long_a  = long_signal and (isFlat or posDir == "SHORT") and cooldownOK and cloud3_allows_long
bool enter_short_a = short_signal and (isFlat or posDir == "LONG") and cooldownOK and cloud3_allows_short

bool enter_long_bc  = (long_signal_b or long_signal_c) and
                      ((i_bOpenFresh and isFlat) or (not isFlat and posDir == "LONG"))
                      and cooldownOK and cloud3_allows_long
bool enter_short_bc = (short_signal_b or short_signal_c) and
                       ((i_bOpenFresh and isFlat) or (not isFlat and posDir == "SHORT"))
                       and cooldownOK and cloud3_allows_short
```

**4. Add ATR-Based BE Parameters (add after line 61)**
```pine
// ATR-based BE raise (v3.8)
input bool   i_useATR_BE   = true                  // Use ATR-based BE (vs fixed $)
input float  i_beTrigger   = 0.5                   // BE trigger: profit > X × ATR
input float  i_beLock      = 0.3                   // BE lock: SL = entry + X × ATR
input float  i_beFixed     = 2.0                   // Fixed BE (if not using ATR)
```

**5. Add ATR Calculation (if not already present)**
```pine
// 14-period ATR
atr = ta.atr(14)
```

**6. Replace Fixed BE Logic (lines ~400-420) with ATR-Based**
```pine
// Calculate BE raise threshold
float be_threshold = i_useATR_BE ? (i_beTrigger * atr) : (i_beFixed / close)
float be_lock_distance = i_useATR_BE ? (i_beLock * atr) : (i_beFixed / close)

// Long BE raise
if inPosition and posDir == "LONG"
    float profit = close - entry_price
    if profit > be_threshold and stop_price < entry_price + be_lock_distance
        stop_price := entry_price + be_lock_distance

// Short BE raise
if inPosition and posDir == "SHORT"
    float profit = entry_price - close
    if profit > be_threshold and stop_price > entry_price - be_lock_distance
        stop_price := entry_price - be_lock_distance
```

**7. Update Commission (line ~480)**
```pine
strategy.commission.cash_per_order = 8  // $8/side (0.08% on $10K notional with 20x leverage)
```

**8. Add MFE/MAE Tracking Variables (after entry)**
```pine
// Track MFE/MAE for every trade
var float max_price_in_trade = na
var float min_price_in_trade = na

if strategy.position_size != 0
    if na(max_price_in_trade)
        max_price_in_trade := close
        min_price_in_trade := close
    else
        max_price_in_trade := math.max(max_price_in_trade, high)
        min_price_in_trade := math.min(min_price_in_trade, low)
else
    max_price_in_trade := na
    min_price_in_trade := na
```

---

### Part 2: Python v3.8 (for Vince ML Tool)

**File**: `PROJECTS/four-pillars-backtester/strategies/four_pillars_v3_8.py`

#### Architecture:
```python
class FourPillarsV38:
    """
    Four Pillars v3.8 Strategy (Python implementation)
    - Cloud 3 directional filter (always on)
    - ATR-based BE raise
    - MFE/MAE tracking for ML analysis
    - Commission: $8/side (0.08%)
    """

    def __init__(self, config: dict):
        # Strategy parameters
        self.use_atr_be = config.get('use_atr_be', True)
        self.be_trigger = config.get('be_trigger', 0.5)  # 0.5× ATR
        self.be_lock = config.get('be_lock', 0.3)        # 0.3× ATR
        self.sl_atr = config.get('sl_atr', 1.0)          # 1.0× ATR
        self.tp_atr = config.get('tp_atr', 1.5)          # 1.5× ATR

        # State
        self.position = 0  # 1 = long, -1 = short, 0 = flat
        self.entry_price = None
        self.stop_price = None
        self.tp_price = None
        self.max_price = None  # MFE tracking
        self.min_price = None  # MAE tracking

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Four Pillars indicators"""
        # Stochastics (4 timeframes)
        df['stoch_9_3_k'] = ta.STOCH(df['high'], df['low'], df['close'],
                                      fastk_period=9, slowk_period=1)
        df['stoch_14_3_k'] = ta.STOCH(df['high'], df['low'], df['close'],
                                       fastk_period=14, slowk_period=1)
        df['stoch_40_3_k'] = ta.STOCH(df['high'], df['low'], df['close'],
                                       fastk_period=40, slowk_period=1)
        df['stoch_60_10_k'] = ta.STOCH(df['high'], df['low'], df['close'],
                                        fastk_period=60, slowk_period=1)
        df['stoch_60_10_d'] = df['stoch_60_10_k'].rolling(10).mean()

        # Ripster EMA Clouds
        df['ema5'] = ta.EMA(df['close'], 5)
        df['ema12'] = ta.EMA(df['close'], 12)
        df['ema34'] = ta.EMA(df['close'], 34)
        df['ema50'] = ta.EMA(df['close'], 50)
        df['ema72'] = ta.EMA(df['close'], 72)
        df['ema89'] = ta.EMA(df['close'], 89)

        # Cloud 2 (5/12), Cloud 3 (34/50), Cloud 4 (72/89)
        df['cloud2_top'] = df[['ema5', 'ema12']].max(axis=1)
        df['cloud2_bot'] = df[['ema5', 'ema12']].min(axis=1)
        df['cloud3_top'] = df[['ema34', 'ema50']].max(axis=1)
        df['cloud3_bot'] = df[['ema34', 'ema50']].min(axis=1)

        # Cloud 3 position (-1 = below, 0 = inside, 1 = above)
        df['price_pos'] = 0
        df.loc[df['close'] > df['cloud3_top'], 'price_pos'] = 1
        df.loc[df['close'] < df['cloud3_bot'], 'price_pos'] = -1

        # Cloud 3 directional filter
        df['cloud3_allows_long'] = df['price_pos'] >= 0
        df['cloud3_allows_short'] = df['price_pos'] <= 0

        # ATR
        df['atr'] = ta.ATR(df['high'], df['low'], df['close'], timeperiod=14)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate A/B/C signals with Cloud 3 filter"""
        # Stage 1 tracking (oversold/overbought entry)
        df['long_stage'] = 0
        df['short_stage'] = 0

        # A signals (3/4 stochs oversold → exit oversold)
        # ... (implement stage machine logic from Pine Script)

        # B signals (2/4 stochs + Cloud 3 filter)
        long_others_b = (
            (df['stoch_14_3_k'] < 30).astype(int) +
            (df['stoch_40_3_k'] < 30).astype(int) +
            (df['stoch_60_10_k'] < 25).astype(int)
        )
        df['long_signal_b'] = (long_others_b >= 2) & df['cloud3_allows_long']

        # C signals (1/4 stoch + Cloud 3 above)
        df['long_signal_c'] = (df['stoch_14_3_k'] < 30) & (df['price_pos'] == 1)

        # Same for shorts
        # ...

        return df

    def backtest(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run backtest with MFE/MAE tracking"""
        trades = []

        for i in range(len(df)):
            bar = df.iloc[i]

            # Entry logic
            if self.position == 0:
                if bar['enter_long_a'] or bar['enter_long_bc']:
                    self._enter_long(bar)
                elif bar['enter_short_a'] or bar['enter_short_bc']:
                    self._enter_short(bar)

            # Exit logic (SL/TP)
            if self.position != 0:
                self._update_mfe_mae(bar)
                self._check_exit(bar)
                self._update_be_raise(bar)

            # Record trade on exit
            if self.position == 0 and len(trades) > 0 and trades[-1]['exit_price'] is None:
                trades[-1]['exit_price'] = bar['close']
                trades[-1]['exit_time'] = bar['datetime']
                trades[-1]['mfe'] = self.max_price
                trades[-1]['mae'] = self.min_price

        return pd.DataFrame(trades)

    def _update_be_raise(self, bar):
        """ATR-based BE raise logic"""
        if self.use_atr_be:
            be_threshold = self.be_trigger * bar['atr']
            be_lock_distance = self.be_lock * bar['atr']
        else:
            be_threshold = self.be_lock / bar['close']  # Fixed $ converted to %
            be_lock_distance = be_threshold

        if self.position == 1:  # Long
            profit = bar['close'] - self.entry_price
            if profit > be_threshold and self.stop_price < self.entry_price + be_lock_distance:
                self.stop_price = self.entry_price + be_lock_distance

        elif self.position == -1:  # Short
            profit = self.entry_price - bar['close']
            if profit > be_threshold and self.stop_price > self.entry_price - be_lock_distance:
                self.stop_price = self.entry_price - be_lock_distance
```

#### Key Files to Create:
1. **`strategies/four_pillars_v3_8.py`** - Strategy class (above)
2. **`strategies/indicators.py`** - Shared indicator calculations (stoch, EMA, ATR)
3. **`strategies/signal_machine.py`** - Stage 1/2 state machine logic
4. **`backtester/vectorized_backtest.py`** - Fast vectorized backtesting
5. **`backtester/event_backtest.py`** - Detailed event-by-event backtesting with order management

---

### Part 3: Vince ML Analysis Pipeline

**Goal**: Analyze 100+ coins over 3 months to find optimal parameters that manual testing couldn't discover.

#### Pipeline Architecture:

**1. Data Preparation**
- File: `vince/data_prep.py`
- Convert all 1m data → 5m (using `resample_timeframes.py --all`)
- Load 5m data for all 100+ coins
- Calculate Four Pillars indicators
- Calculate TA-Lib features (RSI, CCI, MFI, MACD, BBW, OBV, ADOSC)
- Normalize features (rolling z-score)

**2. Label Generation (Triple Barrier)**
- File: `vince/label_generator.py`
- For each Four Pillars signal (A/B/C):
  - Upper barrier: entry + 1.5 ATR (TP)
  - Lower barrier: entry - 1.0 ATR (SL)
  - Vertical barrier: 100 bars (8.3 hours on 5m)
- Label = 1 if TP hit first, 0 if SL hit first, (profit/TP) if time hit first
- Track MFE/MAE for every trade

**3. XGBoost Meta-Labeling**
- File: `vince/xgboost_trainer.py`
- Primary model: Four Pillars generates A/B/C signals
- Secondary model: XGBoost predicts skip/take/size (0.0 to 1.0)
- Features: 21 indicators (Stoch K values, EMA distances, ATR%, volume ratio, RSI, etc.)
- Training: Purged K-fold CV (5 folds, 1% embargo)
- Output: XGBoost model weights + SHAP values

**4. Parameter Optimization**
- File: `vince/parameter_sweep.py`
- Test ranges:
  - `be_trigger`: [0.3, 0.4, 0.5, 0.6, 0.7] × ATR
  - `be_lock`: [0.2, 0.3, 0.4, 0.5] × ATR
  - `sl_atr`: [0.8, 1.0, 1.2] × ATR
  - `tp_atr`: [1.2, 1.5, 1.8, 2.0] × ATR
  - Cloud 3 chop zone handling: [allow_both, require_cloud2, block_all]
- Metric: SQN × Total Profit (balances consistency + return)
- Per-coin optimization + aggregate optimization

**5. Walk-Forward Validation**
- File: `vince/walk_forward.py`
- Split 3 months into 6 windows (2 weeks each)
- Train on window N-1, test on window N
- Record: Sharpe, SQN, win rate, avg R, total profit, max DD
- Average across all windows

**6. Risk Method Comparison**
- File: `vince/risk_methods.py`
- Test 4 BE strategies:
  1. Move SL to breakeven (0 ATR)
  2. BE + fees (0.3 ATR above entry)
  3. BE + fees + trailing TP (trail TP from max_price)
  4. BE + trailing TP (trail both SL and TP)
- Compare: SQN, total profit, LSG% (Loser Saw Green), max DD

**7. Comprehensive Report**
- File: `vince/generate_report.py`
- Per-coin results (top 10 + bottom 10)
- Aggregate results (all coins)
- Feature importance (SHAP values)
- Loser classification (A/B/C/D from Sweeney)
- Optimal parameters per coin + aggregate
- Visualizations: Equity curves, drawdown plots, SHAP summary

---

## Critical Files to Modify/Create

### Existing Files to Modify:
1. **`02-STRATEGY/Indicators/four_pillars_v3_7_1_strategy.pine`** → copy to `four_pillars_v3_8_strategy.pine`, apply changes above
2. **`PROJECTS/four-pillars-backtester/resample_timeframes.py`** → already created ✓

### New Files to Create:

#### Pine Script:
- `02-STRATEGY/Indicators/four_pillars_v3_8_strategy.pine` (strategy)
- `02-STRATEGY/Indicators/four_pillars_v3_8.pine` (indicator, no strategy calls)

#### Python Strategy:
- `PROJECTS/four-pillars-backtester/strategies/__init__.py`
- `PROJECTS/four-pillars-backtester/strategies/four_pillars_v3_8.py` (main strategy class)
- `PROJECTS/four-pillars-backtester/strategies/indicators.py` (shared indicator calcs)
- `PROJECTS/four-pillars-backtester/strategies/signal_machine.py` (stage 1/2 logic)

#### Python Backtester:
- `PROJECTS/four-pillars-backtester/backtester/__init__.py`
- `PROJECTS/four-pillars-backtester/backtester/vectorized.py` (fast vectorized backtest)
- `PROJECTS/four-pillars-backtester/backtester/event_based.py` (detailed event backtest)
- `PROJECTS/four-pillars-backtester/backtester/metrics.py` (SQN, Sharpe, R-multiples, MFE/MAE)

#### Vince ML Pipeline:
- `PROJECTS/vince-ml/__init__.py`
- `PROJECTS/vince-ml/config.yaml` (hyperparameters, coin list, date ranges)
- `PROJECTS/vince-ml/data_prep.py` (load 5m data, calculate indicators)
- `PROJECTS/vince-ml/label_generator.py` (Triple Barrier labeling)
- `PROJECTS/vince-ml/xgboost_trainer.py` (meta-labeling model)
- `PROJECTS/vince-ml/pytorch_trainer.py` (optional: neural network for pattern recognition)
- `PROJECTS/vince-ml/parameter_sweep.py` (grid search optimal parameters)
- `PROJECTS/vince-ml/walk_forward.py` (walk-forward validation)
- `PROJECTS/vince-ml/risk_methods.py` (compare 4 BE strategies)
- `PROJECTS/vince-ml/generate_report.py` (comprehensive results + visualizations)
- `PROJECTS/vince-ml/utils.py` (shared utilities: purged CV, SHAP, etc.)
- `PROJECTS/vince-ml/requirements.txt` (dependencies: xgboost, torch, shap, ta-lib, etc.)

#### Documentation:
- `PROJECTS/vince-ml/README.md` (usage guide)
- `PROJECTS/vince-ml/RESULTS.md` (template for results)
- `02-STRATEGY/Indicators/FOUR-PILLARS-V3.8-CHANGELOG.md` (what changed from v3.7.1)

---

## Verification Plan

### Phase 1: Pine Script v3.8 Verification
1. **Load v3.8 on TradingView** (UNIUSDT, 2m chart from screenshot)
2. **Backtest 3 months** (same date range as v3.7.1)
3. **Verify Cloud 3 filter works**:
   - In bearish context (price < Cloud 3), NO long signals should fire
   - In bullish context (price > Cloud 3), NO short signals should fire
4. **Compare with v3.7.1**:
   - Should have FEWER trades (opposite-direction signals blocked)
   - Should have HIGHER win rate (better directional alignment)
   - May have LOWER total trades (fewer flips)

### Phase 2: Python v3.8 Verification
1. **Run Python backtest on BTCUSDT (5m, 3 months)**
2. **Compare with Pine Script results**:
   - Same entry signals (A/B/C)
   - Same exit prices (SL/TP within slippage tolerance)
   - Same total trades (±1% tolerance)
   - Same net profit (±5% tolerance)
3. **Verify MFE/MAE tracking**: Every trade should have entry/min/max prices recorded

### Phase 3: Vince ML Pipeline Verification
1. **Test data_prep.py**: Load 5m data for 10 coins, verify indicators match Pine Script
2. **Test label_generator.py**: Generate labels for BTCUSDT, verify Triple Barrier logic
3. **Test xgboost_trainer.py**: Train on BTCUSDT, verify accuracy > 55%
4. **Test parameter_sweep.py**: Run on 1 coin (RIVERUSDT), verify optimal params found
5. **Test walk_forward.py**: Run on 1 coin, verify 6 windows execute
6. **Full run on ALL 100+ coins**:
   - Should complete in < 4 hours (with GPU acceleration)
   - Output comprehensive report with per-coin + aggregate results
   - Identify top 10 coins by SQN × Profit
   - Export optimal parameters for each coin

### Success Criteria:
- ✅ Pine Script v3.8 blocks opposite-direction signals in trending markets
- ✅ Python v3.8 matches Pine Script results (±5% tolerance)
- ✅ Vince ML finds optimal parameters for each coin
- ✅ Aggregate results show improvement over v3.7.1 (higher Sharpe, SQN, or total profit)
- ✅ SHAP values reveal which features matter most (e.g., Stoch 9-3 vs 14-3 vs 40-3)
- ✅ Loser classification identifies BE raise optimization opportunities

---

## GPU Acceleration Requirements

All Vince ML scripts should use GPU when available:

**XGBoost:**
```python
params = {
    'tree_method': 'gpu_hist',  # GPU acceleration
    'gpu_id': 0,
    'predictor': 'gpu_predictor',
}
```

**PyTorch:**
```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
```

**CuPy (for vectorized operations):**
```python
import cupy as cp
# Use cp.array() instead of np.array() for GPU arrays
```

**Requirements:**
- `xgboost[gpu]`
- `torch` (with CUDA support)
- `cupy-cuda12x` (match CUDA version)

---

## Next Steps (After Plan Approval)

1. **Convert all 1m data → 5m** (run `resample_timeframes.py --timeframe 5m --all`)
2. **Create Pine Script v3.8** (copy v3.7.1, apply Cloud 3 filter changes)
3. **Test Pine Script v3.8** on UNIUSDT chart (verify opposite signals blocked)
4. **Create Python v3.8** (translate Pine Script → Python)
5. **Verify Python matches Pine Script** (backtest BTCUSDT, compare results)
6. **Build Vince ML pipeline** (7 scripts: data_prep → generate_report)
7. **Run comprehensive analysis** (100+ coins, 3 months, GPU-accelerated)
8. **Generate report** (optimal parameters, feature importance, per-coin results)
9. **Update v3.8 with optimal parameters** (both Pine Script + Python)
10. **Final backtest** (verify improvements over v3.7.1)

---

## Estimated Timeline

- **Pine Script v3.8**: 1 hour (code changes + testing)
- **Python v3.8**: 4 hours (translation + verification)
- **Vince ML pipeline**: 8 hours (7 scripts + testing)
- **Full analysis run**: 2-4 hours (100+ coins with GPU)
- **Report generation**: 1 hour
- **Total**: ~16-18 hours

**Can be done in phases:**
1. **Today**: Pine Script v3.8 + test (1 hour)
2. **Tomorrow**: Python v3.8 + Vince pipeline (12 hours)
3. **Day 3**: Full analysis + report (5 hours)

---

---

## IMMEDIATE EXECUTION PLAN: Qwen Code Generation (Updated 2026-02-09)

### Context
Setup is complete:
- ✅ `auto_generate_files.py` - Python script for Ollama API calls
- ✅ `startup_generation.ps1` - PowerShell orchestration script
- ✅ `START_GENERATION.bat` - Batch wrapper for easy execution
- ✅ `QWEN-MASTER-PROMPT-ALL-TASKS.md` - 20-file generation prompt (13,060 chars)
- ✅ Ollama running with qwen3-coder:30b model
- ✅ nvitop installed (Python 3.13) and working
- ✅ Checkpoint/resume functionality implemented
- ✅ All encoding issues resolved (no emojis, ASCII-only output)

### What Remains

#### Phase 1: Code Generation (Tonight - 6-12 hours)

**Action**: Run overnight generation

**Command**:
```powershell
cd "C:\Users\User\Documents\Obsidian Vault\trading-tools"
.\START_GENERATION.bat
```

**Expected**:
- 3 windows open: Ollama (minimized), nvitop (GPU monitor), Generation (output streaming)
- Generation runs 6-12 hours
- Checkpoints saved every 1000 characters → `generation_checkpoint.txt`
- Final output → `generated_output.log`
- Parsed files → `vince/` folder

**Generated Files** (20 total):
1. Core (5): `base_strategy.py`, `position_manager.py`, `exit_manager.py`, `metrics.py`, `backtester.py`
2. Strategy (4): `indicators.py`, `signals.py`, `cloud_filter.py`, `four_pillars_v3_8.py`
3. Optimizer (4): `grid_search.py`, `bayesian_opt.py`, `walk_forward.py`, `aggregator.py`
4. ML (3): `triple_barrier.py`, `features.py`, `xgboost_trainer.py`
5. GUI (2): `coin_selector.py`, `parameter_inputs.py`
6. Utils (2): TBD

**Monitoring**:
- nvitop window shows GPU utilization
- Generation window streams code in real-time
- Checkpoint file grows incrementally
- If crash/restart: run `.\START_GENERATION.bat` again → auto-resumes from checkpoint

---

#### Phase 2: Code Review & Integration (Tomorrow Morning - 2-3 hours)

**Action**: Review and integrate generated code

**Steps**:
1. **Check generation completion**:
   ```powershell
   Get-Item generated_output.log, generation_checkpoint.txt | Select-Object Length, LastWriteTime
   Get-ChildItem vince -Recurse -File | Measure-Object -Line
   ```

2. **Review generated files**:
   - Check `generated_output.log` for completion markers (`✓ filename.py COMPLETE`)
   - Verify all 20 files created in `vince/` folder
   - Scan for syntax errors: `python -m py_compile vince/**/*.py`

3. **Fix imports and structure**:
   - Circular import resolution
   - Add missing `__init__.py` files (script auto-creates)
   - Verify relative imports work

4. **Create missing infrastructure**:
   - `vince/requirements.txt`:
     ```
     pandas>=2.0.0
     numpy>=1.24.0
     ta-lib>=0.4.0
     requests>=2.31.0
     optuna>=3.4.0
     xgboost>=2.0.0
     scikit-learn>=1.3.0
     plotly>=5.17.0
     streamlit>=1.28.0
     fuzzywuzzy>=0.18.0
     ```
   - `vince/config.yaml` (strategy defaults)
   - `vince/.env.template` (API keys placeholder)

5. **Test core components**:
   ```python
   # Test indicator calculation
   from vince.strategies.indicators import calculate_all_indicators

   # Test backtester
   from vince.engine.backtester import Backtester

   # Test strategy
   from vince.strategies.four_pillars_v3_8 import FourPillarsV38
   ```

---

#### Phase 3: First Backtest (Tomorrow Afternoon - 1-2 hours)

**Action**: Run first backtest on RIVERUSDT 5m data

**Steps**:
1. **Load data**:
   ```python
   from pathlib import Path
   import pandas as pd

   data_file = Path('PROJECTS/four-pillars-backtester/data/cache/RIVERUSDT_5m.parquet')
   df = pd.read_parquet(data_file)
   ```

2. **Initialize strategy**:
   ```python
   from vince.strategies.four_pillars_v3_8 import FourPillarsV38

   config = {
       'atr_period': 14,
       'sl_atr': 1.0,
       'tp_atr': 1.5,
       'be_trigger': 0.5,
       'be_lock': 0.3,
       'commission': 8.0
   }
   strategy = FourPillarsV38(config)
   ```

3. **Run backtest**:
   ```python
   from vince.engine.backtester import Backtester

   backtester = Backtester(strategy)
   results = backtester.run(df)

   print(f"Total Trades: {len(results['trades'])}")
   print(f"Win Rate: {results['metrics']['win_rate']:.2%}")
   print(f"Total Profit: ${results['metrics']['total_profit']:,.2f}")
   print(f"SQN: {results['metrics']['sqn']:.2f}")
   ```

4. **Verify against Python backtester** (PROJECTS/four-pillars-backtester):
   - Compare trade count (should match ±5%)
   - Compare total profit (should match ±10%)
   - If mismatch > 20%, debug signal generation

---

#### Phase 4: Parameter Optimization (Days 2-3 - 4-6 hours)

**Action**: Run grid search on 5 low-price coins

**Coins**: RIVERUSDT, KITEUSDT, 1000PEPEUSDT, HYPEUSDT, SANDUSDT

**Steps**:
1. **Define parameter grid**:
   ```python
   param_grid = {
       'atr_period': [8, 13, 14, 21],
       'be_trigger': [0.3, 0.5, 0.7],
       'be_lock': [0.2, 0.3, 0.5],
       'sl_atr': [0.8, 1.0, 1.2],
       'tp_atr': [1.2, 1.5, 1.8]
   }
   ```

2. **Run grid search**:
   ```python
   from vince.optimizer.grid_search import grid_search

   for coin in ['RIVERUSDT', 'KITEUSDT', '1000PEPEUSDT', 'HYPEUSDT', 'SANDUSDT']:
       df = pd.read_parquet(f'data/cache/{coin}_5m.parquet')
       results = grid_search(FourPillarsV38, df, param_grid, metric='sqn_profit')
       print(f"{coin} best params: {results.iloc[0]['params']}")
   ```

3. **Aggregate results**:
   ```python
   from vince.optimizer.aggregator import aggregate_results

   universal_params = aggregate_results(per_coin_results)
   ```

---

#### Phase 5: ML Pipeline (Days 3-5 - 8-10 hours)

**Action**: XGBoost meta-labeling + SHAP analysis

**Steps**:
1. **Generate labels** (Triple Barrier):
   ```python
   from vince.ml.triple_barrier import label_trades

   labeled_df = label_trades(df, tp_mult=1.5, sl_mult=1.0, time_bars=100)
   ```

2. **Extract features**:
   ```python
   from vince.ml.features import generate_features

   features_df = generate_features(df)
   ```

3. **Train XGBoost**:
   ```python
   from vince.ml.xgboost_trainer import train_xgboost

   model, importances, metrics = train_xgboost(features_df, labeled_df['label'])
   print(f"Test Accuracy: {metrics['accuracy']:.2%}")
   ```

4. **SHAP analysis**:
   ```python
   import shap

   explainer = shap.TreeExplainer(model)
   shap_values = explainer.shap_values(features_df)
   shap.summary_plot(shap_values, features_df)
   ```

---

#### Phase 6: Comprehensive Report (Day 6 - 2-3 hours)

**Action**: Generate full analysis report

**Deliverables**:
1. **Per-coin results**: Top 10 + Bottom 10 coins
2. **Aggregate metrics**: Win rate, SQN, Sharpe, total profit
3. **Optimal parameters**: Universal best practice values
4. **Feature importance**: SHAP values + rankings
5. **Loser classification**: A/B/C/D buckets (Sweeney framework)
6. **Visualizations**: Equity curves, drawdown plots, parameter heatmaps

**Report Structure**:
```
vince/reports/2026-02-09_analysis.pdf
  - Executive Summary
  - Methodology
  - Per-Coin Results (table + charts)
  - Universal Parameters (table)
  - Feature Importance (SHAP summary)
  - Loser Classification (distribution + recommendations)
  - Conclusions + Next Steps
```

---

### Critical Files Checklist

**Existing** (trading-tools/):
- [x] `auto_generate_files.py` - Generation script
- [x] `startup_generation.ps1` - Orchestration
- [x] `START_GENERATION.bat` - Launcher
- [x] `QWEN-MASTER-PROMPT-ALL-TASKS.md` - Prompt
- [x] `STARTUP-SETUP-GUIDE.md` - Setup instructions

**To Be Generated** (vince/):
- [ ] `strategies/base_strategy.py`
- [ ] `strategies/indicators.py`
- [ ] `strategies/signals.py`
- [ ] `strategies/four_pillars_v3_8.py`
- [ ] `engine/position_manager.py`
- [ ] `engine/exit_manager.py`
- [ ] `engine/backtester.py`
- [ ] `engine/metrics.py`
- [ ] `optimizer/grid_search.py`
- [ ] `optimizer/bayesian_opt.py`
- [ ] `optimizer/walk_forward.py`
- [ ] `optimizer/aggregator.py`
- [ ] `ml/triple_barrier.py`
- [ ] `ml/features.py`
- [ ] `ml/xgboost_trainer.py`
- [ ] `gui/coin_selector.py`
- [ ] `gui/parameter_inputs.py`
- [ ] (+ 3 more files if time permits)

**To Be Created Manually**:
- [ ] `vince/requirements.txt`
- [ ] `vince/config.yaml`
- [ ] `vince/.env.template`
- [ ] `vince/README.md`
- [ ] `vince/__init__.py` (and sub-package `__init__.py` files)

---

### Timeline (Compressed)

| Day | Phase | Duration | Deliverable |
|-----|-------|----------|-------------|
| **Tonight** | Phase 1: Generation | 6-12 hrs | 20 Python files in `vince/` |
| **Tomorrow AM** | Phase 2: Integration | 2-3 hrs | Working imports, first test passes |
| **Tomorrow PM** | Phase 3: First Backtest | 1-2 hrs | RIVERUSDT backtest matches expected results |
| **Day 2-3** | Phase 4: Optimization | 4-6 hrs | Optimal parameters for 5 coins |
| **Day 3-5** | Phase 5: ML Pipeline | 8-10 hrs | XGBoost model + SHAP analysis |
| **Day 6** | Phase 6: Report | 2-3 hrs | Comprehensive PDF report |

**Total**: ~24-36 hours of active work (spread over 6 days)

---

### Risk Mitigation

**Risk 1**: Qwen generates incomplete/buggy code
- **Mitigation**: Checkpoint system allows resume from any point
- **Fallback**: Paste partial output to Claude for completion/fixing

**Risk 2**: Generated code doesn't match specifications
- **Mitigation**: Manual review + testing in Phase 2
- **Fallback**: Use QWEN-TASK-3-OPTIMIZATION.md to regenerate specific components

**Risk 3**: Imports/dependencies fail
- **Mitigation**: Phase 2 includes comprehensive import resolution
- **Fallback**: Create stub implementations for missing components

**Risk 4**: Backtest results don't match Python backtester
- **Mitigation**: Phase 3 includes detailed comparison + debugging
- **Fallback**: Use proven Python backtester code as reference

---

### Success Criteria

**Phase 1**: Generation completes (20 files generated, no fatal errors)
**Phase 2**: All imports resolve, basic tests pass
**Phase 3**: RIVERUSDT backtest matches expected trade count (±10%)
**Phase 4**: Grid search completes on 5 coins, optimal params identified
**Phase 5**: XGBoost model achieves >55% accuracy on test set
**Phase 6**: Comprehensive report generated with all required sections

**Final Deliverable**: Production-ready Vince ML platform capable of analyzing 100+ coins

---

## Questions for User

Before proceeding, please confirm:

1. **Cloud 3 chop zone behavior**: When price is INSIDE Cloud 3 (not above/below), should we:
   - **Option A**: Allow BOTH long and short signals (current behavior)
   - **Option B**: Require additional confirmation (e.g., Cloud 2 direction)
   - **Option C**: Block ALL signals (wait for breakout)

2. **B/C signal behavior**: Should B and C signals (when `i_bOpenFresh=true`) be allowed to:
   - **Option A**: Open fresh positions in BOTH directions (current)
   - **Option B**: Only open in Cloud 3 direction (new filter)
   - **Option C**: Only add to existing positions (disable fresh open)

3. **ATR-based BE defaults**: Optimal starting values for parameter sweep?
   - `be_trigger = 0.5` (trigger at 0.5× ATR profit)
   - `be_lock = 0.3` (lock at entry + 0.3× ATR)
   - Are these good starting points?

4. **Vince analysis scope**: Should we analyze:
   - **All 100+ coins** (comprehensive, slow)
   - **Top 20 by volume** (faster, still representative)
   - **Low-price coins only** (PEPE, RIVER, KITE, HYPE, SAND - known to be profitable)

5. **GPU availability**: Do you have CUDA-capable GPU for PyTorch/XGBoost acceleration?
   - If yes, which CUDA version? (needed for cupy installation)
   - If no, we'll use CPU (slower but still works)

**READY TO EXECUTE**: Run `.\START_GENERATION.bat` to begin Phase 1

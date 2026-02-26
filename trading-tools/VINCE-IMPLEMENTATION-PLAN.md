# Vince ML Backtesting Platform — Implementation Plan

**Version**: 1.0
**Date**: 2026-02-09
**Status**: Planning Phase
**Goal**: Modular ML-powered backtesting platform with Pine Script auto-conversion

---

## Executive Summary

**What Vince Does**:
1. **Auto-converts** Pine Script strategies → Python
2. **Optimizes** exit parameters (BE raise, trailing TP, ATR periods) across multiple coins
3. **Discovers** best practices via ML that manual testing can't find
4. **Provides** Streamlit GUI for parameter input + results viewing
5. **Supports** multiple strategies (not just Four Pillars)

**Key Insight**: User wants to find optimal MFE-based SL movement rules (e.g., "if MFE > 1.5 ATR → move SL to entry + 0.5 ATR") that vary by coin, timeframe, and ATR period.

---

## Architecture Overview

```
vince/
├── app.py                          # Streamlit GUI (main entry point)
├── converter/
│   ├── __init__.py
│   ├── pine_parser.py              # Parse Pine Script AST
│   ├── python_generator.py         # Generate Python strategy class
│   └── validator.py                # Verify Pine = Python results
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py            # Abstract base class
│   ├── four_pillars_v3_8.py        # Auto-generated from Pine Script
│   └── [user_strategies].py        # User can add more
├── engine/
│   ├── __init__.py
│   ├── backtester.py               # Event-based backtesting engine
│   ├── position_manager.py         # Position tracking (entry, MFE, MAE)
│   ├── exit_manager.py             # Dynamic SL/TP logic
│   └── metrics.py                  # SQN, Sharpe, LSG%, R-multiples
├── optimizer/
│   ├── __init__.py
│   ├── parameter_sweep.py          # Grid search over parameter space
│   ├── bayesian_opt.py             # Bayesian optimization (optional)
│   └── ml_analyzer.py              # XGBoost meta-labeling + SHAP
├── data/
│   ├── __init__.py
│   ├── loader.py                   # Load parquet files
│   ├── resampler.py                # Link to resample_timeframes.py
│   └── cache/                      # Parquet files (1m/5m/15m)
├── gui/
│   ├── __init__.py
│   ├── coin_selector.py            # Fuzzy search dropdown (fuzzywuzzy)
│   ├── parameter_inputs.py         # Streamlit forms for config
│   ├── strategy_uploader.py        # Upload Pine Script file
│   └── report_viewer.py            # Display results + export
├── utils/
│   ├── __init__.py
│   ├── logger.py                   # Logging utility
│   └── gpu_check.py                # Detect CUDA 13.1
└── requirements.txt
```

---

## Phase 1: Pine Script → Python Auto-Converter (Week 1)

### Goal
User pastes Pine Script v3.8 → Vince generates Python strategy class → User runs backtest.

### Components

#### 1.1 Pine Script Parser (`converter/pine_parser.py`)
**Input**: Pine Script file (`.pine`)
**Output**: AST (Abstract Syntax Tree) with extracted components

**Key Extractions**:
- Indicator calculations (stochastics, EMAs, ATR)
- Signal generation logic (A/B/C entry conditions)
- Exit logic (SL/TP, BE raise, trailing)
- Input parameters (`input int`, `input float`, `input bool`)
- Strategy settings (`pyramiding`, `commission`, etc.)

**Method**: Use regex + state machine to parse Pine Script v5/v6 syntax

**Example**:
```python
class PineParser:
    def parse(self, pine_script: str) -> dict:
        """
        Returns:
        {
            'inputs': {'i_sl_atr': 1.0, 'i_tp_atr': 1.5, ...},
            'indicators': ['stoch_9_3_k', 'stoch_14_3_k', 'ema34', 'atr'],
            'signals': {'long_signal_a': '3/4 stochs oversold + ripster', ...},
            'exits': {'sl': '1.0 ATR', 'tp': '1.5 ATR', 'be_raise': 'dynamic'},
        }
        """
```

#### 1.2 Python Strategy Generator (`converter/python_generator.py`)
**Input**: Parsed AST from Pine Parser
**Output**: Python strategy class inheriting from `BaseStrategy`

**Template**:
```python
# Auto-generated from Pine Script v3.8
from strategies.base_strategy import BaseStrategy
import pandas as pd
import talib as ta

class FourPillarsV38(BaseStrategy):
    def __init__(self, config: dict):
        # Extract inputs from Pine Script
        self.sl_atr = config.get('sl_atr', 1.0)
        self.tp_atr = config.get('tp_atr', 1.5)
        self.atr_period = config.get('atr_period', 14)
        # ... (auto-generated from parsed inputs)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Auto-generated from Pine Script indicator logic
        df['stoch_9_k'] = ta.STOCH(...)
        df['ema34'] = ta.EMA(df['close'], 34)
        df['atr'] = ta.ATR(..., timeperiod=self.atr_period)
        # ... (auto-generated)
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Auto-generated from Pine Script signal logic
        # ... (A/B/C signal conditions)
        return df

    def get_exit_rules(self) -> dict:
        return {
            'sl': self.sl_atr,
            'tp': self.tp_atr,
            'be_raise': 'dynamic',  # Optimized by Vince
        }
```

#### 1.3 Validator (`converter/validator.py`)
**Purpose**: Verify Pine Script backtest results ≈ Python backtest results (±5% tolerance)

**Method**:
1. Run Pine Script on TradingView (manual or via API if available)
2. Export trade list (entry/exit prices, P&L)
3. Run Python version on same coin/dates
4. Compare: total trades, total P&L, win rate

**Acceptance**: ±5% tolerance on total P&L, ±1% on trade count

---

## Phase 2: Modular Backtesting Engine (Week 1-2)

### Goal
Strategy-agnostic backtesting engine with MFE/MAE tracking.

### Components

#### 2.1 Base Strategy Interface (`strategies/base_strategy.py`)
```python
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """All strategies must inherit from this"""

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add indicator columns"""
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add signal columns (enter_long, enter_short, exit)"""
        pass

    @abstractmethod
    def get_exit_rules(self) -> dict:
        """Return SL/TP rules"""
        pass

    def get_name(self) -> str:
        return self.__class__.__name__
```

#### 2.2 Position Manager (`engine/position_manager.py`)
**Tracks**:
- Entry price, size, direction (long/short)
- MFE (max favorable excursion in ATR)
- MAE (max adverse excursion in ATR)
- Bars in trade
- Current P&L

**Key Methods**:
```python
class PositionManager:
    def open_position(self, price, size, direction, atr):
        self.entry_price = price
        self.entry_atr = atr
        self.direction = direction
        self.max_price = price
        self.min_price = price

    def update(self, bar):
        self.max_price = max(self.max_price, bar['high'])
        self.min_price = min(self.min_price, bar['low'])

        # Calculate MFE/MAE in ATR terms
        if self.direction == 'LONG':
            self.mfe_atr = (self.max_price - self.entry_price) / self.entry_atr
            self.mae_atr = (self.entry_price - self.min_price) / self.entry_atr
        else:
            self.mfe_atr = (self.entry_price - self.min_price) / self.entry_atr
            self.mae_atr = (self.max_price - self.entry_price) / self.entry_atr

    def close_position(self, exit_price, exit_reason):
        pnl = (exit_price - self.entry_price) * self.size * self.direction
        return {
            'entry_price': self.entry_price,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'mfe_atr': self.mfe_atr,
            'mae_atr': self.mae_atr,
            'pnl': pnl,
        }
```

#### 2.3 Exit Manager (`engine/exit_manager.py`)
**Purpose**: Dynamic SL/TP logic based on MFE

**4 Risk Methods** (user-selectable):
1. **SL to BE (0 ATR)**: When MFE > threshold, move SL to entry
2. **BE + fees (X ATR)**: Move SL to entry + X ATR
3. **BE + fees + trailing TP**: SL to entry + fees, TP trails from max_price
4. **BE + trailing TP**: Both SL and TP trail

**Optimizable Parameters** (per method):
- `mfe_trigger`: MFE threshold to activate (e.g., 0.5 ATR, 1.0 ATR, 1.5 ATR)
- `sl_lock`: Where to lock SL (0, 0.2, 0.3, 0.5 ATR from entry)
- `tp_trail_distance`: TP distance from max_price (0.3, 0.5, 0.7 ATR)

**Example**:
```python
class ExitManager:
    def __init__(self, risk_method: str, config: dict):
        self.risk_method = risk_method
        self.mfe_trigger = config['mfe_trigger']  # e.g., 1.0 ATR
        self.sl_lock = config['sl_lock']          # e.g., 0.3 ATR
        self.tp_trail_distance = config.get('tp_trail_distance', 0.5)

    def update_stops(self, position: PositionManager, bar):
        atr = bar['atr']

        # Check if MFE exceeds trigger
        if position.mfe_atr >= self.mfe_trigger:
            if self.risk_method == 'be_only':
                position.stop_loss = position.entry_price

            elif self.risk_method == 'be_plus_fees':
                position.stop_loss = position.entry_price + (self.sl_lock * atr)

            elif self.risk_method == 'be_plus_fees_trail_tp':
                position.stop_loss = position.entry_price + (self.sl_lock * atr)
                position.take_profit = position.max_price - (self.tp_trail_distance * atr)

            elif self.risk_method == 'be_trail_tp':
                position.stop_loss = position.entry_price
                position.take_profit = position.max_price - (self.tp_trail_distance * atr)
```

#### 2.4 Backtester (`engine/backtester.py`)
**Method**: Event-based (bar-by-bar)

**Process**:
1. Load data (1m/5m/15m parquet)
2. Calculate indicators
3. Generate signals
4. For each bar:
   - Check entry conditions
   - Update position (MFE/MAE)
   - Update SL/TP via ExitManager
   - Check exit conditions
   - Record trade on close
5. Return trade list + metrics

---

## Phase 3: Parameter Optimization (Week 2)

### Goal
Find optimal exit parameters across multiple coins/timeframes.

### Parameter Space

```python
OPTIMIZATION_SPACE = {
    # ATR periods (Fibonacci + standard)
    'atr_period': [8, 13, 14, 21],

    # Timeframes
    'timeframe': ['1m', '5m', '15m'],

    # MFE trigger for SL movement (in ATR multiples)
    'mfe_trigger': [0.3, 0.5, 0.7, 1.0, 1.5, 2.0],

    # SL lock position (in ATR from entry)
    'sl_lock': [0, 0.2, 0.3, 0.5, 0.7],

    # Trailing TP distance from max_price (in ATR)
    'tp_trail_distance': [0.3, 0.5, 0.7, 1.0],

    # Risk method
    'risk_method': ['be_only', 'be_plus_fees', 'be_plus_fees_trail_tp', 'be_trail_tp'],
}
```

**Total Combinations**: 4 × 3 × 6 × 5 × 4 × 4 = **5,760 combinations per coin**

### Optimization Strategy

**Option A: Grid Search** (exhaustive, slow)
- Test all 5,760 combinations
- ~20 coins = 115,200 backtests
- Time: ~10 hours with GPU acceleration

**Option B: Bayesian Optimization** (smart, fast)
- Use `optuna` library
- Test ~200 combinations per coin
- ~20 coins = 4,000 backtests
- Time: ~1 hour with GPU

**Recommendation**: Start with Bayesian (fast), validate top results with Grid Search.

### Metrics to Optimize

**Primary Metric**: `SQN × Total Profit`
(Balances consistency + return)

**Secondary Metrics**:
- LSG% (Loser Saw Green)
- Win Rate
- Avg R-multiple
- Max Drawdown
- Sharpe Ratio

### Multi-Coin Aggregation

**Per-Coin Results**:
```
BTCUSDT:  risk_method=be_plus_fees_trail_tp, atr_period=14, mfe_trigger=1.0, sl_lock=0.3, SQN=2.4
ETHUSDT:  risk_method=be_plus_fees, atr_period=13, mfe_trigger=0.7, sl_lock=0.2, SQN=2.1
RIVERUSDT: risk_method=be_trail_tp, atr_period=8, mfe_trigger=0.5, sl_lock=0, SQN=3.1
```

**Aggregate "Best Practice"**:
- Most common risk method: `be_plus_fees_trail_tp` (appeared in 12/20 coins)
- Most common ATR period: 14 (appeared in 8/20 coins)
- Median mfe_trigger: 1.0 ATR
- Median sl_lock: 0.3 ATR

---

## Phase 4: Streamlit GUI (Week 2-3)

### Features

#### 4.1 Strategy Upload
- Upload Pine Script file (`.pine`)
- Auto-convert to Python
- Show conversion summary
- Validate against TradingView results

#### 4.2 Coin Selection
- Dropdown with fuzzy search (`fuzzywuzzy`)
- Type "asx" → suggests "AXSUSDT"
- Select random 5 coins OR manually select
- Show available data (1m/5m/15m)

#### 4.3 Parameter Input
- Timeframe: [1m, 5m, 15m]
- Notional value: $500, $1000, $5000
- Commission: $8/side (adjustable)
- ATR periods to test: [8, 13, 14, 21] (multi-select)
- Risk methods to test: (checkboxes for all 4)
- Optimization method: Bayesian (default) or Grid Search
- Number of trials: 200 (Bayesian), All (Grid)

#### 4.4 Results Dashboard
**Tabs**:
1. **Summary**: Best parameters per coin, aggregate best practice
2. **Trade List**: All trades with MFE/MAE/LSG flag
3. **Equity Curve**: Per coin + aggregate
4. **LSG Analysis**: Histogram of MFE for losing trades
5. **SHAP Values**: XGBoost feature importance (if using ML)
6. **Parameter Heatmap**: SQN vs mfe_trigger vs sl_lock

**Export Options** (per tab):
- CSV (trade list)
- PNG (charts)
- PDF (full report)
- HTML (interactive dashboard)

---

## Phase 5: XGBoost Meta-Labeling (Week 3-4)

### Goal
XGBoost decides whether to **take** or **skip** each Four Pillars signal.

### Features
- 21 input features (stoch K values, EMA distances, ATR%, volume ratio, RSI, etc.)
- Binary classification: 0 = skip, 1 = take
- Train on 70% of data, test on 30%
- Purged K-Fold CV (5 folds, 1% embargo)
- SHAP values for per-trade explanation

### Integration
- Run after parameter optimization
- Compare: Four Pillars alone vs Four Pillars + XGBoost filter
- Expected improvement: +10-20% SQN, +5-10% win rate

---

## Phase 6: BingX/WEEX Integration (Week 4-5)

### Data Fetchers
- BingX historical API
- WEEX historical API
- Cache in same parquet format as Bybit

### Live Trading (Future)
- WebSocket connections
- Order execution
- Position sync
- Risk management

---

## Implementation Roadmap

### Week 1: Core Infrastructure
- **Day 1-2**: Pine Script parser + Python generator
- **Day 3**: Validator (Pine vs Python comparison)
- **Day 4-5**: Backtesting engine (position manager, exit manager)

### Week 2: Optimization + GUI
- **Day 1-2**: Parameter sweep (Bayesian optimization)
- **Day 3**: Multi-coin aggregation
- **Day 4-5**: Streamlit GUI (upload, coin selector, parameter inputs)

### Week 3: Results + Export
- **Day 1-2**: Results dashboard (6 tabs)
- **Day 3**: Export features (CSV, PNG, PDF, HTML)
- **Day 4-5**: XGBoost meta-labeling integration

### Week 4: Exchange Integration
- **Day 1-3**: BingX/WEEX data fetchers
- **Day 4-5**: Test on new data, validate results

### Week 5: Testing + Documentation
- **Day 1-2**: Unit tests for all modules
- **Day 3**: Integration tests (end-to-end)
- **Day 4-5**: Documentation (README, usage guide, API docs)

---

## Rate Limit Management

**Current Usage**: 18%

**Strategy**:
1. **Plan first** (this document)
2. **Build incrementally** (one phase at a time)
3. **Test locally** (minimize API calls)
4. **Batch tool calls** (parallel where possible)
5. **Use background tasks** for long-running operations

**Estimated Tool Calls**:
- Phase 1: ~50 calls (parser, generator, validator)
- Phase 2: ~80 calls (backtester, position/exit managers)
- Phase 3: ~40 calls (optimizer)
- Phase 4: ~60 calls (Streamlit GUI)
- Phase 5: ~40 calls (XGBoost)
- **Total**: ~270 calls over 3-4 weeks

**Daily Budget**: ~10-15 calls/day (sustainable)

---

## Dependencies

```txt
# Core
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=12.0.0  # For parquet

# TA
ta-lib>=0.4.0
pandas-ta>=0.3.0

# ML
xgboost>=2.0.0
shap>=0.42.0
optuna>=3.0.0
scikit-learn>=1.3.0

# GUI
streamlit>=1.28.0
plotly>=5.17.0
fuzzywuzzy>=0.18.0
python-Levenshtein>=0.21.0

# GPU
cupy-cuda13x>=12.0.0  # CUDA 13.1
torch>=2.1.0+cu121

# Utils
pyyaml>=6.0.0
python-dotenv>=1.0.0
loguru>=0.7.0
```

---

## Success Criteria

**Phase 1**:
- ✅ Pine Script v3.8 → Python conversion works
- ✅ Python backtest matches Pine Script (±5% tolerance)

**Phase 2**:
- ✅ Backtester tracks MFE/MAE correctly
- ✅ Exit manager supports all 4 risk methods

**Phase 3**:
- ✅ Optimization finds better parameters than manual defaults
- ✅ LSG% improves by 5-10%

**Phase 4**:
- ✅ GUI is intuitive (no manual needed)
- ✅ Export works for all formats

**Phase 5**:
- ✅ XGBoost improves win rate by 5-10%
- ✅ SHAP values explain skip/take decisions

---

## Open Questions

1. **Pine Script AST**: Should we use a library (if exists) or build custom parser?
2. **GPU Batch Size**: How many backtests can run in parallel on CUDA 13.1?
3. **TradingView API**: Can we auto-export Pine Script results, or manual CSV upload?
4. **Strategy Versioning**: How to handle v3.8 vs v3.9 vs user's custom strategies?

---

## Next Actions

**User Decision Required**:
1. Approve this plan?
2. Start with Phase 1 (Pine → Python converter)?
3. Or prioritize Phase 2 (backtester) and manually convert v3.8 for now?

**Estimated Time to First Results**:
- **Option A** (build converter first): 2 weeks to first optimization run
- **Option B** (manual conversion, build backtester): 1 week to first optimization run

Which path?

# NEXT STEPS - Post Dashboard Deployment

**Status:** Dashboard deployed, tested with RIVERUSDT 1m  
**Issues found:** AVWAP trail bug, 1m unprofitable, no coin text input  

---

## PRIORITY 1: TEST 5M TIMEFRAME (KNOWN PROFITABLE)

**Why:** 1m bleeds commissions, 5m proven profitable (+$55K on RIVERUSDT)

```powershell
# In dashboard sidebar
# Select: RIVERUSDT
# Timeframe: 5m (not 1m)
# BE Raise: 4
# Click "Run Backtest"
```

**Expected output:**
- Win rate: ~17%
- Exp $/tr: +$13.95
- Net P&L: +$55K
- Trades: ~4000

**If fails:** Check data cache with `ls data\cache\*RIVERUSDT*5m*.parquet`

---

## PRIORITY 2: FIX AVWAP TRAIL BUG

**Bug location:** `engine/exit_manager.py` lines ~200-250

```powershell
# View current AVWAP trail code
python -c "from engine.exit_manager import ExitManager; import inspect; print(inspect.getsource(ExitManager._avwap_trail_sl))"
```

**Test fix:**
1. Open `engine/exit_manager.py`
2. Find `_avwap_trail_sl` method
3. Add debug logging:
   ```python
   print(f"AVWAP trail: band={band_width}, floor={floor_atr}, sl={new_sl}")
   ```
4. Re-run backtest
5. Check console output

**Expected:** SL should ratchet up as AVWAP moves, visible in logs

---

## PRIORITY 3: ADD COIN TEXT INPUT

**File:** `scripts/dashboard.py` (or `staging/dashboard.py`)

```python
# Find line ~50-60 (coin selector)
# OLD:
selected_coin = st.selectbox("Select Coin", all_coins)

# NEW:
col1, col2 = st.columns([3, 1])
with col1:
    coin_input = st.text_input("Type coin symbol (e.g., RIVERUSDT)", "")
with col2:
    selected_coin = st.selectbox("Or select", all_coins)

# Use typed input if provided
if coin_input:
    selected_coin = coin_input.upper()
```

**Test:**
1. Edit `scripts/dashboard.py`
2. Save
3. Refresh browser (Streamlit auto-reloads)
4. Type "RIVERUSDT" in text box

---

## PRIORITY 4: TEST ML TABS (Tab 4)

**Current tab:** Overview (Tab 1)  
**Next:** Click "ML Meta-Label" (Tab 4)

**What to check:**
- [ ] SHAP waterfall plot renders
- [ ] Feature importance table shows
- [ ] Bet sizing distribution
- [ ] ML-filtered expectancy metric

**If blank:** Check browser console (F12) for errors

---

## PRIORITY 5: ADD CLOUD 4 TRAIL EXIT

**Why:** Screenshots show Cloud 4 would capture 8x more profit

**File:** `engine/exit_manager.py`

```python
# Add new method around line 300
def _cloud4_trail_sl(self, direction: str, cloud4_bottom: float, 
                     cloud4_top: float, atr: float, offset_mult: float = 1.0):
    """Cloud 4 trailing stop (72/89 EMA)."""
    offset = offset_mult * atr
    
    if direction == "LONG":
        return cloud4_bottom - offset
    else:
        return cloud4_top + offset
```

**Test with PIPPINUSDT:**
1. Add cloud4_trail to exit config
2. Run backtest
3. Compare vs static SL (expect 8x improvement)

---

## PRIORITY 6: SCHEDULE DAILY VINCE TRAINING

**Create:** `scripts/vince_daily_train.py`

```python
import schedule
import subprocess
from datetime import datetime

def daily_train():
    print(f"VINCE training: {datetime.now()}")
    
    # 1. Fetch new data
    subprocess.run(["python", "scripts/fetch_data.py", "--update"])
    
    # 2. Incremental backtest
    subprocess.run(["python", "scripts/run_backtest.py", "--incremental"])
    
    # 3. Retrain XGBoost
    subprocess.run(["python", "ml/meta_label.py", "--update", "--gpu"])
    
    print("✅ VINCE trained")

# Schedule at 17:05 UTC (after rebate settlement)
schedule.every().day.at("17:05").do(daily_train)

while True:
    schedule.run_pending()
    time.sleep(60)
```

**Run as background service:**
```powershell
# Test manual trigger first
python scripts\vince_daily_train.py --manual

# Then schedule
# Add to Windows Task Scheduler or run in screen/tmux
```

---

## PRIORITY 7: RUN 400-COIN ML SWEEP

**Goal:** Find top 20 coins by ML-filtered expectancy

```powershell
python scripts\sweep_all_coins_ml.py --timeframe 5m --be-raise 4
```

**Output:** `data/output/ml/sweep_ml_5m.csv`  
**Columns:** coin, trades, win_rate, expectancy, ml_expectancy, skip_pct

**Runtime:** 2-4 hours (GPU accelerated)

---

## WHERE WE ARE NOW

**✅ Complete:**
- Dashboard deployed (5 tabs)
- Flow diagrams generated
- Architecture documented

**🔧 Needs fixing:**
- AVWAP trail bug (test on 5m first)
- Coin text input (UX improvement)

**📊 Next testing:**
- 5m timeframe (should be +$55K)
- ML Tab 4 (SHAP, features)
- Cloud 4 trail vs static SL

**🚀 Future (this week):**
- Daily VINCE training scheduler
- 400-coin ML sweep
- Live WebSocket integration

---

## IMMEDIATE ACTIONS (Next 30 min)

**Do these in order:**

1. **Test 5m timeframe** (5 min)
   - Dashboard → Select RIVERUSDT
   - Timeframe: 5m
   - Run backtest
   - Verify +$55K profit

2. **Check ML Tab 4** (5 min)
   - Click "ML Meta-Label" tab
   - Verify SHAP plot renders
   - Check feature importance

3. **Debug AVWAP trail** (10 min)
   - Add print statements to `exit_manager.py`
   - Re-run RIVERUSDT 5m
   - Check console for SL updates

4. **Add coin text input** (10 min)
   - Edit `scripts/dashboard.py`
   - Add text_input widget
   - Test typing "RIVERUSDT"

**After 30 min:** Report results, we'll fix what's broken and move to Cloud 4 trail.

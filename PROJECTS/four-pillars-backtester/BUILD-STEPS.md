# VINCE BUILD STEPS - Quick Deploy Guide

**Goal:** Deploy 5-tab ML dashboard, run flow diagrams, test with real data  
**Time:** 15 minutes total  
**Prerequisites:** PostgreSQL running, 399 coins cached, Python 3.13+

---

## SUMMARY

Deploy staging dashboard → Test with RIVERUSDT → Generate flow diagrams → Verify ML tabs working

All commands run from: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester`

---

## BUILD 1: DEPLOY DASHBOARD

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# Copy staging files to production
Copy-Item staging\dashboard.py scripts\dashboard.py -Force
Copy-Item staging\run_backtest.py scripts\run_backtest.py -Force
Copy-Item staging\test_dashboard_ml.py scripts\test_dashboard_ml.py -Force

# Create ml/ directory if missing
if (-not (Test-Path ml)) { New-Item -ItemType Directory -Path ml }
Copy-Item staging\ml\live_pipeline.py ml\live_pipeline.py -Force
Copy-Item staging\ml\__init__.py ml\__init__.py -Force

Write-Host "✅ Dashboard deployed"
```

**Output:** Files copied to production  
**Errors:** If copy fails, check staging/ exists (`ls staging`)

---

## BUILD 2: TEST DEPLOYMENT

```powershell
# Test dashboard imports
python -c "import scripts.dashboard; print('✅ Dashboard imports OK')"

# Test ML pipeline
python -c "from ml.live_pipeline import FilteredSignal; print('✅ Live pipeline OK')"

# Run full test suite
python scripts\test_dashboard_ml.py
```

**Output:** All tests pass (5/5)  
**Errors:** If import fails, check Python path with `python -c "import sys; print(sys.path)"`

---

## BUILD 3: LAUNCH DASHBOARD

```powershell
# Start Streamlit (opens browser automatically)
streamlit run scripts\dashboard.py
```

**Output:** Browser opens at http://localhost:8501  
**What you see:** 5 tabs (Overview, Trade Analysis, MFE/MAE, ML Meta-Label, Validation)  
**Errors:** If port busy, use `streamlit run scripts\dashboard.py --server.port 8502`

---

## BUILD 4: TEST WITH RIVERUSDT

**In browser (localhost:8501):**

1. Sidebar: Select coin → RIVERUSDT
2. Parameters:
   - BE Raise: 4
   - Commission: 0.08%
   - Rebate: 50%
   - Timeframe: 5m
3. Click "Run Backtest"

**Output:**
- Win rate: ~17%
- Expectancy: +$13.95/trade
- Total trades: ~4000
- Net P&L: +$55K (3 months)

**Errors:** If "No data cached", run `python scripts\fetch_data.py --symbol RIVERUSDT --timeframe 5m`

---

## BUILD 5: INTERACTIVE FLOW DIAGRAM

```powershell
# Generate Sankey diagram (opens in browser)
python scripts\visualize_flow.py
```

**Output:**
- Saved to: `data/output/vince_flow.html`
- Browser opens with interactive diagram
- Click nodes to see connections

**Errors:** If plotly missing, run `pip install plotly --break-system-packages`

---

## BUILD 6: MERMAID DIAGRAMS

**Open in Obsidian:**

1. File → Open
2. Navigate to: `PROJECTS\four-pillars-backtester\VINCE-FLOW.md`
3. Diagrams render automatically

**Output:** 3 diagrams visible (Architecture, Daily Training, Learning Loop)  
**Errors:** If not rendering, enable Mermaid plugin in Obsidian settings

---

## BUILD 7: VERIFY ML TABS

**In dashboard (Tab 4: ML Meta-Label):**

1. Check SHAP waterfall plot renders
2. Verify feature importance table shows
3. Check bet sizing distribution
4. Verify ML-filtered expectancy metric

**Output:** All ML visualizations render correctly  
**Errors:** If blank, check console (F12) for JavaScript errors

---

## BUILD 8: RUN 400-COIN SWEEP (Optional)

```powershell
# Run ML sweep across all cached coins
python scripts\sweep_all_coins_ml.py --timeframe 5m --be-raise 4
```

**Output:**
- Processes all 399 coins
- Saves to: `data/output/ml/sweep_ml_5m.csv`
- Runtime: ~2-4 hours (GPU accelerated)

**Errors:** If CUDA error, verify `python -c "import torch; print(torch.cuda.is_available())"`

---

## VERIFICATION CHECKLIST

After all builds:

- [ ] Dashboard opens at localhost:8501
- [ ] 5 tabs visible and clickable
- [ ] RIVERUSDT backtest completes
- [ ] Equity curve renders
- [ ] Tab 4 shows SHAP plot
- [ ] Flow diagram opens in browser
- [ ] VINCE-FLOW.md renders in Obsidian

**All checked?** System fully deployed ✅

---

## TROUBLESHOOTING

**Dashboard won't start:**
```powershell
# Kill existing process
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force
streamlit run scripts\dashboard.py
```

**Import errors:**
```powershell
# Verify packages
python -c "import streamlit, pandas, plotly, xgboost, shap"
# If missing, install:
pip install streamlit pandas plotly xgboost shap --break-system-packages
```

**PostgreSQL connection fails:**
```powershell
# Check .env file exists
cat .env
# Should have: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
```

**No cached data:**
```powershell
# List cached coins
ls data\cache\*.parquet
# If empty, run overnight fetch:
python scripts\fetch_sub_1b.py
```

---

## NEXT STEPS (After Deployment)

1. **Add Cloud 4 Trail Exit** (30 min)
   - Edit `engine/exit_manager.py`
   - Add `cloud4_trail` risk method
   - Test on PIPPINUSDT

2. **Schedule Daily Training** (15 min)
   - Create `scripts/vince_daily_train.py`
   - Set 17:05 UTC schedule
   - Test manual trigger

3. **Deploy to Live** (1 week paper trading)
   - Connect WebSocket via `ml/live_pipeline.py`
   - Monitor for 1 week
   - Validate signals match backtests

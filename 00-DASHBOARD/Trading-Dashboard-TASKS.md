# Trading Dashboard Build - Task Breakdown

**Project Goal:** Build TradeZella-style trading journal dashboard  
**Data Source:** Bybit trade history CSV  
**Timeline:** Build locally today, deploy to VPS tonight  
**Status:** 🟡 In Progress

---

## **PHASE 1: SETUP (15 mins)** ⏸️

### **Task 1.1** - Create project folder ✅
- [x] Create `C:\Users\User\Documents\Obsidian Vault\PROJECTS\trading-dashboard`
- [x] Inside: create folders `data`, `code`, `output`

### **Task 1.2** - Copy trade file
- [ ] Copy Bybit CSV from `03-TRADE-JOURNAL` to `PROJECTS/trading-dashboard/data/`
- [ ] Rename it to `bybit-trades.csv` (simple name)

### **Task 1.3** - Test Python environment
- [ ] Open terminal/command prompt
- [ ] Run `python --version` (confirm it works)
- [ ] Run `pip install pandas plotly streamlit openpyxl` (install libraries)

---

## **PHASE 2: DATA PARSING (Claude Code builds this)** ⏸️

### **Task 2.1** - Basic CSV reader
- [ ] Open Claude Code
- [ ] Build script to load CSV and print first 10 rows
- [ ] Verify data loads correctly
- [ ] Save as `parse_trades.py`

### **Task 2.2** - Separate trades from funding
- [ ] Filter out funding fees (keep only Trade rows)
- [ ] Print trade count
- [ ] Verify numbers match expectations

### **Task 2.3** - Group partial fills
- [ ] Group by Order No. to combine partial fills
- [ ] Calculate total entry/exit per order
- [ ] Print sample grouped trade

---

## **PHASE 3: P&L CALCULATIONS (Claude Code builds this)** ⏸️

### **Task 3.1** - Basic P&L per trade
- [ ] Calculate P&L = (exit_price - entry_price) × quantity
- [ ] Add fees to calculation
- [ ] Print P&L for first 5 trades

### **Task 3.2** - Symbol breakdown
- [ ] Group trades by symbol (RIVER, AXS)
- [ ] Calculate total P&L per symbol
- [ ] Print summary table

### **Task 3.3** - Overall metrics
- [ ] Total P&L across all trades
- [ ] Win rate (% profitable trades)
- [ ] Total trades count
- [ ] Print final summary

---

## **PHASE 4: DASHBOARD BUILD (Claude Code builds this)** ⏸️

### **Task 4.1** - Basic Streamlit page
- [ ] Create `dashboard.py`
- [ ] Add title "Trading Performance Dashboard"
- [ ] Run `streamlit run dashboard.py`
- [ ] Verify page loads in browser

### **Task 4.2** - Summary metrics display
- [ ] Show Total P&L in big card
- [ ] Show Win Rate
- [ ] Show Total Trades
- [ ] Show P&L by Symbol

### **Task 4.3** - Add equity curve chart
- [ ] Plot cumulative P&L over time
- [ ] Add to dashboard
- [ ] Verify chart displays

### **Task 4.4** - Add trade list table
- [ ] Show recent 20 trades
- [ ] Columns: Symbol, Entry, Exit, P&L, Time
- [ ] Make it scrollable

---

## **PHASE 5: TESTING (Your verification)** ⏸️

### **Task 5.1** - Verify one trade manually
- [ ] Pick one Order No. from CSV
- [ ] Calculate P&L manually in calculator
- [ ] Compare with dashboard number
- [ ] Confirm accuracy

### **Task 5.2** - Cross-check totals
- [ ] Add up RIVER P&L + AXS P&L manually
- [ ] Compare with dashboard total
- [ ] Verify match

### **Task 5.3** - Screenshot test
- [ ] Take screenshot of dashboard
- [ ] Can you show this to someone?
- [ ] Does it look professional?

---

## **PHASE 6: VPS DEPLOYMENT (Tonight)** ⏸️

### **Task 6.1** - Package files
- [ ] Zip the `trading-dashboard` folder
- [ ] Upload to VPS via FileZilla/WinSCP

### **Task 6.2** - VPS setup
- [ ] SSH into VPS
- [ ] Install Python packages on VPS
- [ ] Test run locally first

### **Task 6.3** - Run dashboard
- [ ] Start with `screen -S dashboard`
- [ ] Run `streamlit run dashboard.py --server.port 8501`
- [ ] Access from browser `http://VPS_IP:8501`

### **Task 6.4** - Confirm remote access
- [ ] Open from your phone
- [ ] Open from PC
- [ ] Send link to test contact

---

## Execution Plan

**Morning Session (2-3 hours):**
- Phase 1 + Phase 2 + Phase 3

**Afternoon Session (2-3 hours):**
- Phase 4 + Phase 5

**Evening (1 hour):**
- Phase 6

---

## Next Action

**NOW:** Task 1.2 - Copy Bybit CSV to project data folder

📌 Report back when Phase 1 is complete

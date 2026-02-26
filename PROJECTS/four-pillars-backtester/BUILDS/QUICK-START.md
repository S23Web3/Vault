# QUICK START - Claude Code

**Execute builds in 3 steps**

---

## Step 1: Open Claude Code

**In VS Code terminal (PowerShell):**

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
claude
```

---

## Step 2: Execute BUILD 1 (Critical Fix)

**Copy-paste this into Claude Code:**

```
Read and execute: BUILDS/01-fix-avwap-be-conflict.md
```

**Claude Code will:**
- Edit `engine/position.py` (lines 145, 176)
- Remove AVWAP check from BE raise logic
- Run test to verify BE raises = 1631
- Report success

**Expected:**
```
✅ Test passed: BE raises = 1631
   Net P&L: $39,240.51
```

---

## Step 3: Verify In Dashboard

**Start dashboard:**

```powershell
streamlit run scripts\dashboard.py
```

**Test:**
1. Symbol: RIVERUSDT
2. Timeframe: 5m
3. Enable AVWAP trail: ✓
4. Observe results

**Before fix:** BE: 0, Net: -$13,758  
**After fix:** BE: 1,631, Net: +$39K ✅

---

## Next Builds (Optional)

**BUILD 3 - VINCE Auto-Discovery:**

```
Read and execute: BUILDS/03-vince-auto-discovery.md
```

VINCE finds optimal exit strategy automatically (Cloud 4, AVWAP 1σ, etc.)

**BUILD 4 - Timing Analysis:**

```
Read and execute: BUILDS/04-checkpoint-timing-analysis.md
```

Calculates optimal checkpoint frequency based on actual processing speed.

**BUILD 2 - Historical Data (Overnight):**

```
Read and execute: BUILDS/02-download-historical-data.md
```

Downloads 2023-now complete dataset (20-50 GB, 6-12 hours).

---

## If Claude Code Unavailable

**Manual fix (BUILD 1):**

Edit `engine\position.py`:

**Line 145:**
```python
# Change from:
if not self.avwap_enabled and not self.be_raised:

# To:
if not self.be_raised:
```

**Line 176 (same change):**
```python
# Change from:
if not self.avwap_enabled and not self.be_raised:

# To:
if not self.be_raised:
```

Save file, restart dashboard.

---

**That's it. START WITH BUILD 1 (5 minutes).**

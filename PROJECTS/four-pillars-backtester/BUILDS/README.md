# BUILDS INDEX - Claude Code Integration

**How to execute builds using Claude Code**

---

## Quick Start

**In VS Code terminal:**

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
claude
```

**In Claude Code chat:**

```
Read and execute: BUILDS/01-fix-avwap-be-conflict.md
```

Claude Code will:
1. Read the build file
2. Make the code changes
3. Run the tests
4. Report results

---

## Available Builds

| Build | File | Time | What It Does |
|-------|------|------|--------------|
| **1** | `01-fix-avwap-be-conflict.md` | 5 min | Fix AVWAP+BE working together |
| **2** | `02-download-historical-data.md` | 6-12 hrs | Download 2023-now complete dataset |
| **3** | `03-vince-auto-discovery.md` | 30 min | VINCE finds best exit strategy |
| **4** | `04-checkpoint-timing-analysis.md` | 5 min | Calculate optimal checkpoint frequency |

---

## Build 1: Fix AVWAP + BE Conflict ⚡ PRIORITY

**Problem:** AVWAP disables BE raise → full losses instead of BE conversion

**Link for Claude Code:**
```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\01-fix-avwap-be-conflict.md
```

**Manual alternative (if Claude Code unavailable):**

Edit `engine\position.py`:

Line 145:
```python
# OLD:
if not self.avwap_enabled and not self.be_raised:

# NEW:
if not self.be_raised:
```

Line 176 (same change for SHORT positions):
```python
# OLD:
if not self.avwap_enabled and not self.be_raised:

# NEW:
if not self.be_raised:
```

Test:
```bash
python -c "from engine.backtester import Backtester; from signals.four_pillars import compute_signals; from data.fetcher import BybitFetcher; fetcher = BybitFetcher('data/cache'); df = fetcher.load_cached('RIVERUSDT'); df = compute_signals(df); bt = Backtester({'be_raise_amount': 4.0, 'avwap_trail': True}); result = bt.run(df); print(f'BE raises: {result[\"metrics\"][\"be_raised_count\"]}')"
```

Expected: `BE raises: 1631` (not 0)

---

## Build 2: Download Historical Data 📥

**Purpose:** Get complete 2023-now dataset (20-50 GB)

**Link for Claude Code:**
```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\02-download-historical-data.md
```

**Steps:**
1. Check if volume exists in current cache
2. Test with mock data (5 seconds)
3. Run full download (6-12 hours overnight)
4. Verify sanity checks

**Commands:**
```bash
# Step 1: Check volume
python scripts\check_volume_exists.py

# Step 2: Test mock
python scripts\test_download_mock.py

# Step 3: Download (run overnight)
python scripts\download_historical_data.py
```

---

## Build 3: VINCE Auto-Discovery 🧠

**Purpose:** VINCE finds optimal exit strategy (no manual analysis)

**Link for Claude Code:**
```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\03-vince-auto-discovery.md
```

**What VINCE tests:**
- Cloud 2/3/4 exits
- ATR 0.5/0.8/1.0/1.2/1.5× exits
- AVWAP 0.5σ/1.0σ/1.5σ/2.0σ exits

**VINCE learns:**
- Which converts most LSG losers → winners
- Reports: "Cloud 4 Exit: 71.5% conversion, +$18.23/trade"
- Auto-applies best strategy

**Command:**
```bash
python -c "from ml.exit_discovery import discover_optimal_exit; from data.fetcher import BybitFetcher; from signals.four_pillars import compute_signals; from engine.backtester import Backtester; from engine.metrics import trades_to_dataframe; fetcher = BybitFetcher('data/cache'); df = fetcher.load_cached('RIVERUSDT'); df = compute_signals(df); bt = Backtester({'be_raise_amount': 4.0}); result = bt.run(df); trades_df = trades_to_dataframe(result['trades']); best, results = discover_optimal_exit(trades_df, df)"
```

---

## Build 4: Checkpoint Timing Analysis ⏱️

**Purpose:** Answer "Why 10 coins?" with data

**Link for Claude Code:**
```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\04-checkpoint-timing-analysis.md
```

**Measures:**
- Time per coin (~4s average)
- Checkpoint overhead (~50ms)
- Optimal frequency (10 = ~40s = 1 min risk)

**Command:**
```bash
python scripts\benchmark_sweep_timing.py
```

**Output:** Recommended checkpoint frequency based on actual processing speed

---

## How Claude Code Works

**Process:**

1. **You:** Give Claude Code a markdown file with task instructions
2. **Claude Code:** Reads the file, understands the task
3. **Claude Code:** Edits files, runs tests, reports results
4. **You:** Verify output, approve or iterate

**Example session:**

```
You: Read and execute BUILDS/01-fix-avwap-be-conflict.md

Claude Code: Reading file... Done.
             Editing engine/position.py line 145... Done.
             Editing engine/position.py line 176... Done.
             Running test... 
             ✅ Test passed: BE raises = 1631
             Net P&L: $39,240.51

You: Deploy to production

Claude Code: Files updated. Test passed. Ready to use.
```

---

## Execution Order

**Recommended:**

1. **BUILD 1** (5 min) - Fix AVWAP+BE conflict → CRITICAL
2. **BUILD 4** (5 min) - Benchmark timing → Understand sweep speed
3. **BUILD 3** (30 min) - VINCE auto-discovery → Let VINCE find solutions
4. **BUILD 2** (overnight) - Download historical data → Full dataset

**Total active time:** ~40 minutes  
**Total wall time:** 6-12 hours (overnight download)

---

## Claude Code Links (Copy-Paste Ready)

**BUILD 1:**
```
Read and execute: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\01-fix-avwap-be-conflict.md
```

**BUILD 2:**
```
Read and execute: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\02-download-historical-data.md
```

**BUILD 3:**
```
Read and execute: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\03-vince-auto-discovery.md
```

**BUILD 4:**
```
Read and execute: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\04-checkpoint-timing-analysis.md
```

---

## Manual Execution (If Claude Code Not Available)

**Each build has:**
- Files to edit (with line numbers)
- Code changes (OLD → NEW)
- Test commands
- Expected output

**Just:**
1. Open file in editor
2. Find line number
3. Replace OLD code with NEW code
4. Run test command
5. Verify output matches expected

---

## Next Steps After Builds

**After BUILD 1 (AVWAP fix):**
- Rerun dashboard with AVWAP enabled
- Verify BE_n > 0
- Compare profit vs broken version

**After BUILD 3 (VINCE discovery):**
- VINCE shows best exit strategy
- Dashboard applies it automatically
- Re-run sweep with optimal exits

**After BUILD 2 (historical data):**
- Full dataset available for training
- Run multi-year backtests
- VINCE trains on 2+ years of data

---

**Start with BUILD 1 now. It's the most critical fix (5 minutes).**

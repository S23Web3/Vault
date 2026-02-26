# Full Project Review — 2026-02-13 (Evening)

## SECTION 1: OBSIDIAN VAULT STATE + CLAUDE CODE STATUS

### What Claude Code Is Doing Right Now
- **Session 6** of today's build
- Building `scripts/build_all_specs.py` — master script that generates ALL files from Specs A, B, C
- Read 20/20 codebase files, confirmed 9 output paths are clear
- Hit 32000 token output limit once, now building in parts
- Currently in "Transfiguring" state (19m+ elapsed, 61.3k tokens consumed)
- The build script will generate 9 files total:
  1. `engine/backtester_v385.py` (Spec B)
  2. `scripts/dashboard_v3.py` (Spec A)
  3. `ml/coin_features.py` (Spec C)
  4. `ml/vince_model.py` (Spec C)
  5. `ml/training_pipeline.py` (Spec C)
  6. `ml/xgboost_auditor.py` (Spec C)
  7. `scripts/test_v385.py`
  8. `scripts/test_dashboard_v3.py`
  9. `scripts/test_vince_ml.py`

### Vault Structure (06-CLAUDE-LOGS)
- 65+ log files from Jan 24 to Feb 13
- Today alone: 10 files (build-journal-cc, build-journal-desktop, dashboard-v3-spec-build, data-pipeline-build, hello-world-test, journal-audit, project-audit, vault-sweep-manifest, vault-sweep-review, vince-ml-build-session)
- BUILD-JOURNAL-2026-02-13.md is the master journal (6 sessions documented)

### 3 Spec Files (All Reviewed, Corrected, Ready)
| Spec | File | Lines | Status |
|------|------|-------|--------|
| A: Dashboard v3 | SPEC-A-DASHBOARD-V3.md | 442 | Ready, Claude Code building |
| B: Backtester v385 | SPEC-B-BACKTESTER-V385.md | 264 | Ready, awaiting build |
| C: VINCE ML | SPEC-C-VINCE-ML.md | 299 | Ready, depends on Spec B |

---

## SECTION 2: MERMAID FLOW STATUS

### Current State: OUTDATED
`VINCE-FLOW.md` exists but reflects the OLD architecture:
- Shows 5-tab dashboard (Overview, Trades, MFE/MAE, ML, Validation)
- Should show 6-tab architecture (Single Coin, Discovery, Optimizer, Validation, Capital & Risk, Deploy)
- Missing: CoinGecko data pipeline
- Missing: Historical period downloads (2023-2024, 2024-2025)
- Missing: 3-spec dependency chain (A → B → C)
- Missing: BBWP Python port as deferred dependency
- Missing: features_v2.py (26 features vs original 14)

### What Needs Updating
The mermaid should reflect:
1. Data Layer: Bybit cache (3 months) + Bybit periods (2023-2025) + CoinGecko (market cap, categories, metadata)
2. Signal Layer: four_pillars_v383 → state_machine_v383 (unchanged)
3. Engine Layer: backtester_v384 → v385 (entry-state + lifecycle logging)
4. ML Layer: coin_features + vince_model (unified PyTorch) + xgboost_auditor
5. Dashboard Layer: 6-tab architecture with Spec A/B/C dependency chain
6. Deferred: BBWP Python port (dashed line)

**BUILD NEEDED: Update VINCE-FLOW.md to match current architecture**

---

## SECTION 3: DATA PIPELINE — COINGECKO + BYBIT STATUS

### CoinGecko: COMPLETE ✅
| Action | Status | Output |
|--------|--------|--------|
| Per-coin market cap + volume (394 coins, 3yr) | ✅ Done | coin_market_history.parquet (5.1 MB) |
| Global market history | ✅ Done | global_market_history.parquet (28 KB) |
| Category master list (667 categories) | ✅ Done | coin_categories.json (152 KB) |
| Coin detail (ATH, launch date, 36 fields) | ✅ Done | coin_metadata.json (638 KB) |
| Top gainers/losers + trending | ✅ Done | top_movers.json (23 KB) |

Total: 792 API calls, 0 errors, 10 minutes. API key valid until 2026-03-03.

### Bybit Recent Cache (Nov 2024 – Feb 2026): COMPLETE ✅
- 399 coins cached, ~6.2 GB
- Updated today via download_all_available.py (+8085 bars forward fill per coin)
- Backup exists: data/cache_backup_20260213_105350/

### Bybit Historical Period 2023-2024: 14% COMPLETE ⚠️
- **55 coins downloaded** out of ~280 eligible (19 coins didn't exist in 2023)
- Downloaded: 655 MB across 55 coins (A-D alphabetically, stopped at DODOUSDT)
- Download was paused/interrupted — needs restart
- Run command: `python scripts/download_periods_v2.py --period 2023-2024 --yes`
- Estimated time: ~2-3 hours for remaining ~225 coins

### Bybit Historical Period 2024-2025: 1% COMPLETE ❌
- **3 coins only** (BTC, ETH, SOL — test run)
- 62 MB downloaded
- Full run needed: `python scripts/download_periods_v2.py --period 2024-2025 --yes`
- Estimated time: ~4.5 hours for all 399 coins

### What's Lacking
1. 2023-2024 period: 225+ coins still needed
2. 2024-2025 period: 396 coins still needed
3. Refetch list: 101 coins from original cache that had partial/failed data (data/refetch_list.json)
4. features_v2.py has 26 features but volume_mcap_ratio needs CoinGecko join (data exists, join not built)
5. No period_loader.py integration with backtester yet — periods downloaded but not concatenated with cache for 3-year backtests

### Saturday Action
Run both periods in foreground (visible):
```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# Period 1 first (~2-3 hours)
python scripts/download_periods_v2.py --period 2023-2024 --yes

# Then period 2 (~4.5 hours)
python scripts/download_periods_v2.py --period 2024-2025 --yes
```

---

## SECTION 4: BBWP UPDATE

### What Exists
| Component | Status | File |
|-----------|--------|------|
| Pine Script BBWP v2 | ✅ Built, 233 lines | indicators/supporting/bbwp_v2.pine |
| Pine Script Caretaker v6 | ✅ Built | indicators/supporting/bbwp_caretaker_v6.pine |
| Python BBWP port | ❌ Does not exist | No file |
| BBWP Build Spec (from Feb 4 chat) | ❌ Not saved to disk | Lost to filesystem bug |

### Your BBWP Logic (From Chat History)

**Philosophy:** BBWP measures band width to identify contraction and expansion. Not an entry/exit signal — it's a FILTER.

**6 States (priority order):**

| State | Condition | Points | Meaning |
|-------|-----------|--------|---------|
| BLUE DOUBLE | bbwp ≤ 10% (extreme low bar + blue spectrum) | +2 | Extreme compression, aggressive move imminent |
| BLUE | bbwp < 25% (spectrum only) | +1 | Compression, setup forming |
| MA CROSS UP | Normal range + bbwp crosses above MA | +1 | Volatility starting to expand |
| MA CROSS DOWN | Normal range + bbwp crosses below MA | 0 | Volatility contracting |
| NORMAL | 25-75%, no cross | 0 | No signal |
| RED | bbwp > 75% (spectrum) | +1 | Expanded, move may be exhausting |
| RED DOUBLE | bbwp ≥ 90% (extreme high bar + red spectrum) | +1 | Extreme expansion |

**Key rules from your chats:**
- Blue bar + blue line = good entry (if other pillars align)
- One blue only = mediocre signal
- Red bars can still give entry long or short IF momentum aligns
- Blue and red CANNOT mix — both derived from same BBWP value
- BBWP alone = nothing. Other pillars determine direction
- You follow the universal cycle, not Caretaker's philosophy
- "All I need is a proper move and I can collect. I am not waiting for moonshots."

### What's Needed: Python BBWP Port

**Best case:** Port the Pine Script v2 logic to Python function:

```
File: signals/bbwp.py (~150 lines)

Input: OHLCV DataFrame
Params: basis_len=13, lookback=100, bbwp_ma_len=5,
        extreme_low=10, extreme_high=90, spectrum_low=25, spectrum_high=75

Output columns: bbwp_value, bbwp_state, bbwp_points, 
                bbwp_is_blue_bar, bbwp_is_red_bar,
                bbwp_ma_cross_up, bbwp_ma_cross_down

Integration: four_pillars_v383.py → backtester_v385.py
Unblocks: 3 deferred fields (entry_bbwp_value, entry_bbwp_spectrum, life_bbwp_delta)
LOE: ~2 hours build + test
```

**This is a standalone build — doesn't block Specs A/B/C but unblocks BBWP fields when ready.**

---

## SECTION 5: PYTORCH BUILD SCOPES — REMAINING WORK

### Current State
- PyTorch 2.10.0+cu130 installed ✅
- RTX 3060 12GB available ✅
- SPEC-C-VINCE-ML.md defines full architecture ✅
- Claude Code building ml/vince_model.py as part of build_all_specs.py ✅

### Phased Build Scope

**Phase 1: Tabular Only (entry + lifecycle features)**
- 25 features per trade (11 entry-state + 14 lifecycle)
- MLP with embedding layers for categoricals
- Labels: win/loss binary + P&L path classification
- Training time: Minutes on RTX 3060
- **Blocked by: Spec B (backtester v385 must produce per-trade parquet first)**

**Phase 2: Add Sequences (LSTM/Transformer)**
- Per-bar indicator evolution as sequence input
- LSTM branches: 50 bars pre-entry context + N bars during trade + 14 static features
- 4 output heads: exit_quality, rfe_prediction, regime_class, optimal_sl
- Training time: Hours on RTX 3060
- Data: ~36GB for 240 training pool coins
- **Blocked by: Phase 1 baseline + backtester v385 --save-bars flag**

**Phase 3: Live Integration**
- n8n webhook endpoint
- Entry features scored at signal time
- Sequence branch updates per bar while position open
- **Blocked by: Phase 2 proven accuracy > Phase 1**

### What's NOT Built Yet

| Component | Status | Blocked By |
|-----------|--------|------------|
| ml/coin_features.py | Claude Code generating | Nothing |
| ml/vince_model.py | Claude Code generating | Nothing |
| ml/training_pipeline.py | Claude Code generating | Nothing |
| ml/xgboost_auditor.py | Claude Code generating | Nothing |
| data/coin_pools.json | Not created | training_pipeline.py |
| Layer 2 per-bar parquet | Not generated | Spec B + --save-bars |
| BBWP Python port | Not built | Separate build |
| CoinGecko → features join | Not built | coin_features.py + data |
| Captum integration | Not built | vince_model.py first |
| TensorBoard logging | Not built | trainer.py first |
| n8n webhook endpoint | Not built | Phase 3 scope |

---

## SECTION 6: SATURDAY SCHEDULE

**Jakarta timezone (UTC+7)**

| Time | Block | Task | Duration |
|------|-------|------|----------|
| 09:00 | VERIFY | Check Claude Code build_all_specs.py status. Did it complete? Run tests. | 30 min |
| 09:30 | DATA | Start 2023-2024 period download in foreground terminal | 5 min start, runs ~3 hours |
| 09:35 | REVIEW | Review Claude Code generated files — dashboard_v3.py, backtester_v385.py, ML modules | 1 hour |
| 10:30 | TEST | Run test_v385.py + test_dashboard_v3.py + test_vince_ml.py | 30 min |
| 11:00 | FIX | Fix any test failures from generated code | 1 hour |
| 12:00 | LUNCH | Break | 1 hour |
| 13:00 | DASHBOARD | Launch dashboard_v3.py — test RIVERUSDT single coin, test sweep start/stop/resume | 1 hour |
| 14:00 | DATA | 2023-2024 should be done. Start 2024-2025 period download | 5 min start |
| 14:05 | BBWP | Build signals/bbwp.py Python port | 2 hours |
| 16:00 | MERMAID | Update VINCE-FLOW.md to match current 3-spec architecture | 30 min |
| 16:30 | SWEEP | Run full 399-coin sweep on dashboard v3 | Start, let run |
| 17:00 | REVIEW | Review sweep progress, check data downloads, log day | 30 min |
| 17:30 | DONE | End of day. Downloads continue overnight if needed. |

**Priority if time is short:**
1. Verify Claude Code output + run tests (CRITICAL)
2. Start historical downloads (BACKGROUND)
3. Dashboard v3 testing (VALIDATES)
4. BBWP Python port (UNBLOCKS)
5. Mermaid update (DOCUMENTATION)

---

## SECTION 7: CHAT SUMMARY LOG (Feb 10-13, 2026)

### Feb 10
- Project status + presentation for coach — 14-section report, 50+ remaining items
- Master build script debug — Phase 1 failing silently
- Ollama + LM Studio setup — qwen2.5-coder:14b installed
- Lost chat recovery — 75% complete, PyTorch blocker identified
- MEMORY.md review — BUILD-SPEC for Vince ML assessment

### Feb 11
- Project vision alignment — VINCE-FLOW.md created, Sankey diagram, Claude Code instructions
- v3.8 catastrophic debug — -97% loss, execution order bug (exit before BE raise)
- Session recovery + milestone — filesystem bug prevented saves, 52 files/8600+ lines built
- CSV leverage analysis — v3.8.2 $2500/slot vs v3.7.1 $10K single, 38 chats logged
- v3.8.2 trade analysis — 3 entry logic bugs, divergence-based approach identified
- Pine Script comparison — position sizing discrepancy confirmed
- Vault test file — filesystem tools verified working

### Feb 12
- Dashboard sweep + normalizer — universal OHLCV normalizer designed
- ML review + direction — inverted risk-reward (SL > TP), BE raise removed in v3.8.x, PyTorch confirmed
- Position sizing + schedule — 4-pillar philosophical corrections, phased development

### Feb 13
- Ollama vault sweep — vault_sweep.py built, 234 files being reviewed by local LLM
- Dashboard v3 spec + ML architecture — 1009-line spec, unified PyTorch decision, 3-spec split
- Journal audit — scattered logs consolidated, MEMORY.md cleanup
- Build + log + ML specs — XGBoost pipeline + PyTorch TTN architecture + dashboard integration specs
- **This session** — full vault review, Saturday schedule, BBWP analysis, PyTorch scope definition

---

## SECTION 8: PERMISSIONS CHECK

**None needed.** All items are read/analyze/write-to-vault. Saturday actions documented for your execution.

Saturday decisions needed from you:
1. If Claude Code build failed → retry or manual build?
2. If test failures → priority order for fixes?
3. BBWP Python port → confirm build per Section 4 spec?

---

#project-review #saturday-schedule #bbwp #pytorch #data-pipeline #chat-summary #2026-02-13
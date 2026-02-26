# 2026-02-14 Project Flow Update + Core Build 2

## Status Updates Applied
- Phase 1 Data Infrastructure: ALL COMPLETE
  - 2023-2024: 166 completed + 43 no_data = 209/209 eligible
  - 2024-2025: 257 completed + 19 no_data = 276/276 eligible
  - CoinGecko: 5 datasets complete
  - Cache: 399 coins, 6.2 GB
- Claude Code build_all_specs.py: ALL 9 FILES EXIST on disk
- Downloads finished overnight, review doc was outdated

## Core Build 2 Created — 7 Steps
1. Run test_v385.py
2. Run test_dashboard_v3.py  
3. Run test_vince_ml.py
4. Fix failures
5. Smoke test dashboard with RIVERUSDT
6. Single coin parquet export validation
7. period_loader test with 1 coin

## Deferred
- BBWP Python port → afternoon session
- CoinGecko features join → after Core Build 2

## Updated Files
- PROJECT-FLOW-CHRONOLOGICAL.md — full rewrite with accurate statuses + Core Build 2 phase

## Critical Path
~~Data~~ ✅ → Core Build 2 ⚡ → Sweep → Trade Parquet → ML Phase 1 → Live

---

## Chat 2 — Core Build 2 Prompt + Flow Fixes (13:00 GST)

### Download Status Correction
- Review doc claimed 2023-2024 at 14%, 2024-2025 at 1%
- Actual: BOTH periods 100% complete (dry-run confirmed 0 remaining)
- 2023-2024: 166 completed + 43 no_data = 209/209 eligible
- 2024-2025: 257 completed + 19 no_data = 276/276 eligible
- Difference: CoinGecko listing date filter excluded coins that didn't exist in those periods

### Flow Chart Updates
- Phase 1 fully green
- Core Build 2 inserted as active phase (7 steps, orange nodes)
- BBWP deferred to afternoon (blue)
- Legend fix: Yellow → Gold (matched Obsidian dark mode render)

### Core Build 2 Prompt Delivered to Claude Code
- 7-step sequential test-and-fix workflow
- Pass criteria per step
- Constraints: minimal patches, no rewrites, BBWP stays deferred
- Specs loaded: SPEC-A, SPEC-B, SPEC-C + python skill
- Claude Code now running Core Build 2

### Key Insight
- Role-prompting ("you are a senior QA engineer") adds nothing
- What works: concrete specs + explicit pass/fail criteria + constraints
- Specs do the heavy lifting, Claude Code reads spec → test → source → patches gap

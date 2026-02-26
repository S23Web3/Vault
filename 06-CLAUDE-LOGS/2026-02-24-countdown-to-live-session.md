# Session Log — 2026-02-24 — Countdown to Live
**Session type:** Scoping + review + fixes
**Status:** Step 1 code fixes COMPLETE — 67/67 tests passing — ready to run main.py

---

## What Was Done This Session

### Documents Created
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md` — master go-live doc, 3 steps, full file index, week timeline
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\STEP1-CHECKLIST.md` — checkable task list for Step 1 (demo live)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-fault-report-step1-build-review.md` — 5 confirmed faults from code review
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\FAULT-REPORT-2026-02-24-step1-build-review.md` — duplicate (user kept it, do not remove)

### Research Done
- Ollama model selection: qwen3:8b confirmed as best 8B model — already installed, RTX 3060 12GB = full GPU inference, 40-60 tok/s
- BingX connector full audit: 64/67 tests passing, infrastructure complete, plugin built
- Full pipeline scoped: screener → active_coins.json → connector → live trades
- Fault review: 5 faults found in Step 1 files, 1 critical (wrong signal import in plugin)

### Completed by User
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` — updated: plugin switched to `four_pillars_v384`, `four_pillars` block added with `allow_a/b: true`, `allow_c: false`, `sl_atr_mult: 2.0`, `tp_atr_mult: null`

---

## Current State

### config.yaml — UPDATED (done)
```yaml
strategy:
  plugin: "four_pillars_v384"

four_pillars:
  allow_a: true
  allow_b: true
  allow_c: false
  sl_atr_mult: 2.0
  tp_atr_mult: null
```

### Tests — 67/67 PASSING (2026-02-25)

All fixes applied this session:
1. `test_executor.py` line 178 — changed `assertEqual` to `assertAlmostEqual(places=8)` (IEEE 754 float precision)
2. `test_integration.py` — fixed `test_entry_then_close` root cause: `@patch("executor.requests.get")` and `@patch("position_monitor.requests.get")` both patched the same shared `requests` module; outer patch won and had no side_effect. Fixed by patching `requests.get` once with 3 sequential responses.
3. `state_manager.py` — fixed shallow copy bug: `dict(DEFAULT_STATE)` shared the `open_positions` dict across instances. Fixed with `copy.deepcopy(DEFAULT_STATE)`. Production bug + test isolation both fixed.
4. Plugin import CLEARED — `four_pillars.py` confirmed produces `long_a/b/c`, `short_a/b/c` columns at lines 64-73.

---

## Next Session — Pick Up Here

### Step 1 is ready — run the demo bot
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"
```
- Expects: startup log, BingX VST connection, warmup progress (~16h for 200 bars on 5m)
- No signal expected immediately — warmup takes ~16h
- Watch for: no crash after 5 minutes, Telegram bot startup message if configured

### After bot confirms running — Step 1 is done
Remaining checklist items (all in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\STEP1-CHECKLIST.md`):
- [ ] First demo signal fires (A or B grade)
- [ ] Telegram alert received
- [ ] Position visible in BingX VST account

---

## Week Plan (as of end of 2026-02-24)

| Day | Target |
|-----|--------|
| Tue (tomorrow) | Step 1 complete — demo bot running on BingX VST |
| Wed-Thu | Step 2 — strategy spec unknowns + Signal Type 2 + dashboard comparison |
| Fri | Step 3 — go live $1,000 / $50 margin |

---

## Key Files — Full Paths

| File | Role |
|------|------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md` | Master go-live doc |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\STEP1-CHECKLIST.md` | Checklist for Step 1 |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-fault-report-step1-build-review.md` | All 5 faults with fixes |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` | Strategy plugin — critical import on line 21 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` | Fix line 178 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` | Fix line 106 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars.py` | Investigate columns first |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py` | Correct signal source (dashboard/backtester) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-23-four-pillars-strategy-scoping.md` | Strategy spec — 19 unknowns for Step 2 |

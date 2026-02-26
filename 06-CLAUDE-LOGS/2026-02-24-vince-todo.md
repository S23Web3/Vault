# Vince v2 — To-Do Log
**Date:** 2026-02-24
**Status:** Parked — PC reboot. Resume from here.

---

## To-Do (in order)

### 1. Review and approve concept v2
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md`
- Status: written 2026-02-23, NOT YET APPROVED for build
- Action: read it, flag anything still wrong, approve or revise

### 2. Scope the trading LLM (separate session)
- Reference: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\TRADING-LLM-QWEN3-RESPONSE.md` — Qwen3 response collected
- Still needed: DeepSeek-R1 response (same prompt — collect and compare)
- Scope items: fine-tuning dataset, training methodology, evaluation criteria, Ollama deployment
- This is a separate build track from Vince — shared asset across Vince, Vicky, Andy

### 3. Formal plugin interface spec
- Blocked by: concept v2 approval
- What it covers: contract for compute_signals(), parameter_space(), trade_schema(), run_backtest(), strategy_document

### 4. Four Pillars plugin spec
- Blocked by: plugin interface spec
- First implementation of the plugin interface
- Includes: strategy markdown document (what the trading LLM reads)

---

## Context Links
- Concept v2: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md`
- Scope log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-20-vince-scope.md`
- Trading LLM material: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\TRADING-LLM-QWEN3-RESPONSE.md`

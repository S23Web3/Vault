# 2026-02-14 — BBW Layer 3 Prompt Build + Python Skill Update

## Summary
Built Layer 3 (Forward Return Tagger) Claude Code prompt, updated Python skill with unicode escape prevention, bug-tested the prompt twice.

## Work Done

### 1. Python Skill — Unicode Escape Prevention
**Root cause of `debug_bbw_sequence.py` SyntaxError:** Claude Code embedded Windows backslash path (`\Users`) in a docstring. `\U` triggered Python's 32-bit Unicode escape parser → `SyntaxError` at parse time.

**Files updated (3 updated, 1 renamed, 1 created):**
- `PROJECTS\four-pillars-backtester\skills\python\SKILL.md` — added String & Encoding Safety + Pre-Execution Validation sections
- `skills\python\python-trading-development.md` → renamed to `python-trading-development-skill.md` (naming convention)
- `.claude\skills\python\SKILL.md` — created condensed version for Claude Code vault-root access

**New sections added:**
- String & Encoding Safety (Windows) — dangerous escape sequences, 6 mandatory rules, regex scan patterns
- Pre-Execution Validation — mandatory `python -m py_compile` after every file write
- Code Review Checklist — 3 new items

**Memory updated:** Skill locations now documented (vault\skills\, vault\.claude\skills\, PROJECTS\<n>\skills\)

### 2. Layer 3 Prompt — First Draft
File: `BUILDS\PROMPT-LAYER3-BUILD.md`

**Scope:** 6 files
- `research\__init__.py` — empty package init
- `research\bbw_forward_returns.py` — pure function, 17 output columns (8 per window × 2 + ATR)
- `tests\test_forward_returns.py` — 12 tests, 50+ assertions
- `scripts\debug_forward_returns.py` — 60+ hand-computed checks
- `scripts\sanity_check_forward_returns.py` — distribution stats on RIVERUSDT
- `scripts\run_layer3_tests.py` — runner saves output to log

### 3. Bug Audit Pass 1 — Found 7 Issues

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | Critical | Debug Section 2: 5-bar dataset with atr_period=14 → ATR all NaN, untestable | Changed to 20-bar dataset with warmup + atr_period=2 |
| 2 | Critical | Test 3: 5-bar dataset for ATR check, not enough for warmup | Changed to 10-bar with atr_period=3 |
| 3 | High | Test 9: "exact 3.0 ATR" impossible with dynamic ATR | Changed to tolerance-based or engineered prices |
| 4 | Medium | _forward_max docstring confusing about NaN boundary | Rewrote with plain English explanation |
| 5 | Medium | No div-by-zero protection spec for ATR=0, close=0 | Added np.where guards |
| 6 | Medium | No df.copy() requirement | Added DataFrame mutation section |
| 7 | Low | Tool call count "~10" vs actual 17+ | Corrected to ~17-20 |

### 4. Bug Audit Pass 2 — Found 3 More Issues

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 8 | Critical | Debug Section 2: entry bar (bar 15) had different range than warmup → ATR jumped from 2.0 to 3.0, all hand-computed ATR values were wrong | Made warmup bars O=100,H=102,L=98,C=100 (TR=4), entry bar same range → ATR stable at 4.0. Recomputed all values: max_up_atr=1.75, max_down_atr=1.75, max_range_atr=3.5 |
| 9 | High | Test 6: "5-bar dataset" with default atr_period=14 and windows=[10,20] → everything NaN | Changed to 20-bar dataset with atr_period=2, windows=[4] |
| 10 | Medium | _forward_max NaN boundary explanation was mechanistic ("shift adds 1") instead of intuitive | Rewrote: "bar i needs bars i+1 through i+w to exist, bar n doesn't exist" |

## Final State
- Layer 3 prompt: `BUILDS\PROMPT-LAYER3-BUILD.md` — bug-tested, math verified, ready for Claude Code
- Python skill: all 3 locations updated with unicode escape prevention
- Layer 2: 68/68 PASS, 148/148 debug PASS (no changes)

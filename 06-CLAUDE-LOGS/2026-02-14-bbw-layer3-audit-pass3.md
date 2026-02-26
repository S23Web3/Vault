# 2026-02-14 — BBW Layer 3 Prompt: Bug Audit Pass 3
**Session:** claude.ai desktop
**Previous chats:**
- https://claude.ai/chat/b2bcdea7-dffd-4e07-95ca-c50fb0609e77 (Layer 3 prompt build + pass 1 & 2)
- https://claude.ai/chat/724dad53-a57c-4a9a-881a-f2eb8d334e21 (Layer 2 build + Layer 3 spec analysis)
- https://claude.ai/chat/9b440629-cfef-4382-836a-bbc61b7079b0 (Architecture + Layer 1 prompt)

---

## Purpose
Independent bug audit of `BUILDS\PROMPT-LAYER3-BUILD.md` before sending to Claude Code. Previous session ran pass 1 (7 bugs) and pass 2 (3 bugs). This session ran pass 3.

## Bug Audit Pass 3 — Found 6 Issues

| # | Severity | Issue | Fix Applied |
|---|----------|-------|-------------|
| 11 | HIGH | Test 9 (proper_move): flat data → ATR=0 → NaN → test meaningless | Changed to alternating volatile data (TR=2, ATR=2.0). Spike range≥6.0 for True, <6.0 for False |
| 12 | HIGH | Debug Section 2: bar 16 with window=4 is in NaN zone (last 4 bars of 20-bar dataset) | Explicit second call with windows=[3]. Bar 16 verified with window=3 |
| 13 | MEDIUM | Debug Section 2: bar 16 expected values not pre-computed — Claude Code would compute its own (risk of wrong assertions) | Pre-computed all 10 values: ATR[16]=5.0, max_up_atr=0.8, max_down_atr=2.0, max_range_atr=2.8, proper_move=False, etc |
| 14 | LOW | Missing explicit `research\` directory creation step | Added pathlib mkdir + touch command in execution step 2 |
| 15 | INFO | Columns from Layer 2 chat analysis dropped (fwd_N_valid_bars, fwd_N_bbw_valid) | Documented in DESIGN DECISIONS section — intentional, deferred to pipeline orchestrator |
| 16 | INFO | NaN tolerance strict (100%) despite 70% recommendation from Layer 2 analysis | Documented in DESIGN DECISIONS section — intentional for clean data, relaxable later |

## Math Verification

### bar 15, window=4 (from pass 2 — reconfirmed)
- ATR[15] = 4.0 (stable, bars 0-15 identical range)
- max_up_pct = 7.0, max_down_pct = -7.0
- max_up_atr = 1.75, max_down_atr = 1.75
- close_pct = -6.0, direction = 'down'
- max_range_atr = 3.5, proper_move = True ✓

### bar 16, window=3 (NEW — computed this session)
- TR[16] = max(6, 5, 1) = 6
- ATR[16] = 0.5×6 + 0.5×4.0 = 5.0
- max_up_pct = (107-103)/103×100 = 3.883495
- max_down_pct = (93-103)/103×100 = -9.708738
- max_up_atr = (107-103)/5.0 = 0.8
- max_down_atr = (103-93)/5.0 = 2.0
- close_pct = (94-103)/103×100 = -8.737864
- max_range_atr = (107-93)/5.0 = 2.8
- proper_move = False (2.8 < 3.0)
- bar 16 with window=4 = NaN (confirms boundary) ✓

### _forward_max vectorized trace (verified)
- 5-element series [10,20,30,40,50], window=2
- Reverse → rolling max → reverse → shift(-1) = [30, 40, 50, NaN, NaN] ✓
- 100-bar df, window=10: bars 0-89 valid, 90-99 NaN ✓

### Test 9 alternating bars (verified)
- Even: O=99,H=101,L=99,C=100 → TR=2
- Odd: O=100,H=101,L=99,C=100 → TR=2
- ATR converges to 2.0 with period=2 ✓
- Spike range≥6.0 → proper_move=True ✓

## Cumulative Bug Count
- Pass 1: bugs 1-7 (from last chat)
- Pass 2: bugs 8-10 (from last chat)
- Pass 3: bugs 11-16 (this chat)
- Total: 16 issues found across 3 passes
- All HIGH/CRITICAL fixed in prompt
- INFO items documented in DESIGN DECISIONS

## Files Modified
| File | Action |
|------|--------|
| `BUILDS\PROMPT-LAYER3-BUILD.md` | 4 edits: Test 9 fix, Debug bar 16 fix, mkdir step, design decisions section |
| `06-CLAUDE-LOGS\2026-02-14-bbw-layer3-audit-pass3.md` | NEW — this file |

## Final State
- Prompt: `BUILDS\PROMPT-LAYER3-BUILD.md` — 3 audit passes complete, all math verified, ready for Claude Code
- No Layer 3 code exists yet — `research\` directory not created
- Layer 1: 61/61 PASS
- Layer 2: 68/68 PASS, 148/148 debug PASS

## Claude Code Instruction
```
Read these files in order, then build Layer 3:

1. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\skills\python\SKILL.md
2. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbwp.py
3. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbw_sequence.py
4. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\PROMPT-LAYER3-BUILD.md

File 4 is the build prompt. Follow it exactly. Write complete files in one shot — do NOT edit interactively. py_compile after every file write.
```

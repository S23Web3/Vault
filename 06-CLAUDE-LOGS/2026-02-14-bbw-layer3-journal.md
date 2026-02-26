# 2026-02-14 — BBW Layer 3: Bug Audit Pass 3 + Prompt Finalization
**Session:** claude.ai desktop
**Chat URL:** current chat
**Previous chats:**
- https://claude.ai/chat/b2bcdea7-dffd-4e07-95ca-c50fb0609e77 (Layer 3 prompt build + audit pass 1 & 2)
- https://claude.ai/chat/724dad53-a57c-4a9a-881a-f2eb8d334e21 (Layer 2 build + Layer 3 spec analysis)
- https://claude.ai/chat/9b440629-cfef-4382-836a-bbc61b7079b0 (Architecture + Layer 1 prompt)

---

## Purpose
Independent bug audit (pass 3) of `BUILDS\PROMPT-LAYER3-BUILD.md` before sending to Claude Code. Previous session ran pass 1 (7 bugs) and pass 2 (3 bugs). This session ran pass 3 finding 6 more issues.

## Context Loading
- Searched past chats for Layer 3 build context, forward returns spec, NaN issues
- Read existing prompt file: `BUILDS\PROMPT-LAYER3-BUILD.md` (16.9KB)
- Read existing log: `06-CLAUDE-LOGS\2026-02-14-bbw-layer3-prompt-build.md`
- Confirmed: `research\` directory does NOT exist yet — no Layer 3 code built
- Confirmed: Layer 1 (61/61 PASS), Layer 2 (68/68 PASS, 148/148 debug PASS)

## Bug Audit Pass 3 — 6 Issues Found

| # | Severity | Issue | Fix Applied |
|---|----------|-------|-------------|
| 11 | HIGH | Test 9 (proper_move): spec said "flat data" but flat → ATR=0 → all NaN → test is meaningless, proves nothing | Changed to alternating volatile bars (TR=2, ATR converges to 2.0). Spike range≥6.0 for True, <6.0 for False |
| 12 | HIGH | Debug Section 2: "verify bar 16 with window=3" but bar 16 with window=4 falls in NaN zone (last 4 bars of 20-bar dataset). Claude Code would try to verify bar 16 from the window=4 output and find NaN | Made explicit: second call `tag_forward_returns(df, windows=[3])`. Also verify bar 16 with window=4 IS NaN (confirms boundary) |
| 13 | MEDIUM | Debug Section 2: bar 16 expected values said "compute TR[16] from the data" — left for Claude Code to figure out. Risk: Claude Code computes wrong values, writes wrong assertions, tests pass against buggy code | Pre-computed all 10 values with full working: ATR[16]=5.0, max_up_pct=3.883495, max_down_pct=-9.708738, max_up_atr=0.8, max_down_atr=2.0, close_pct=-8.737864, max_range_atr=2.8, proper_move=False |
| 14 | LOW | Execution step 2 says "Create research\__init__.py" but `research\` directory doesn't exist → FileNotFoundError | Added explicit `Path('research').mkdir(exist_ok=True)` before touch |
| 15 | INFO | Columns recommended in Layer 2 analysis (fwd_N_valid_bars, fwd_N_bbw_valid) not in prompt — 11 cols/window reduced to 8 | Intentional. Documented in new DESIGN DECISIONS section. Layer 3 works on raw OHLCV only |
| 16 | INFO | NaN tolerance is strict (100% valid bars) despite 70% recommendation from Layer 2 analysis | Intentional. Documented in DESIGN DECISIONS. Clean data first, relaxable later for batch |

## Edits Applied to PROMPT-LAYER3-BUILD.md

1. **Test 9 rewrite** — replaced "flat data" with alternating volatile bars spec, explicit ATR=2.0 target, warning not to use flat data
2. **Debug Section 2 bar 16** — replaced vague "compute TR[16]" with full pre-computed values, explicit second function call with windows=[3], NaN boundary verification
3. **Execution step 2** — added `Path('research').mkdir(exist_ok=True)` 
4. **New section: DESIGN DECISIONS** — 4 items documenting intentional simplifications so Claude Code doesn't "fix" them

## Math Verification (reconfirmed)

### Bar 15, window=4
- ATR[15] = 4.0 (stable, bars 0-15 identical TR=4)
- max_up_pct=7.0, max_down_pct=-7.0, max_up_atr=1.75, max_down_atr=1.75
- close_pct=-6.0, direction='down', max_range_atr=3.5, proper_move=True ✓

### Bar 16, window=3 (NEW this session)
- TR[16]=max(105-99, |105-100|, |99-100|)=max(6,5,1)=6
- ATR[16]=0.5×6 + 0.5×4.0=5.0
- Divides by close[16]=103 (NOT 100) for pct columns
- max_up_pct=3.883495, max_down_pct=-9.708738
- max_up_atr=0.8, max_down_atr=2.0, max_range_atr=2.8
- proper_move=False (2.8<3.0) ✓

### Test 9 alternating bars
- Even: O=99,H=101,L=99,C=100 → TR=2
- Odd: O=100,H=101,L=99,C=100 → TR=2  
- ATR converges to 2.0 with period=2 ✓

## Cumulative Bug Tracker (all 3 passes)

| Pass | Bugs | Source |
|------|------|--------|
| 1 | 1-7 | Previous chat (prompt build session) |
| 2 | 8-10 | Previous chat (ATR jump, dataset size, docstring) |
| 3 | 11-16 | This chat (proper_move, bar 16 NaN zone, pre-compute, mkdir, design docs) |
| **Total** | **16** | **4 CRITICAL, 4 HIGH, 4 MEDIUM, 2 LOW, 2 INFO** |

All HIGH/CRITICAL fixed. INFO items documented as intentional design decisions.

## Files Modified/Created

| File | Action |
|------|--------|
| `BUILDS\PROMPT-LAYER3-BUILD.md` | 4 targeted edits (Test 9, Debug bar 16, mkdir, design decisions) |
| `06-CLAUDE-LOGS\2026-02-14-bbw-layer3-audit-pass3.md` | Created — detailed audit log with math |
| `06-CLAUDE-LOGS\2026-02-14-bbw-layer3-journal.md` | Created — THIS FILE |

## Final State
- **Prompt status:** `BUILDS\PROMPT-LAYER3-BUILD.md` — 3 audit passes complete (16 bugs found/resolved), all math hand-verified, ready for Claude Code
- **Code status:** No Layer 3 code exists. `research\` directory not yet created.
- **Layer 1:** 61/61 PASS (signals\bbwp.py)
- **Layer 2:** 68/68 PASS, 148/148 debug PASS (signals\bbw_sequence.py)

## Claude Code Instruction (copy-paste ready)
```
Read these files in order, then build Layer 3:

1. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\skills\python\SKILL.md
2. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbwp.py
3. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbw_sequence.py
4. C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILDS\PROMPT-LAYER3-BUILD.md

File 4 is the build prompt. Follow it exactly. Write complete files in one shot — do NOT edit interactively. py_compile after every file write.
```

## Next Steps
1. Paste Claude Code instruction into VS Code
2. Claude Code builds: research dir → bbw_forward_returns.py → tests → debug → sanity → runner
3. All tests must pass before proceeding to Layer 4
4. If max token hit: resume with "continue Layer 3 build from step N"

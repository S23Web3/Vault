# Session Log - 2026-03-07 - Strategy Catalogue + Visual Representations
**Date:** 2026-03-07
**Status:** COMPLETE (script written, syntax OK, not yet run by user)

---

## Session 2 — 2026-03-07 — S6-S11 Build

**Status:** COMPLETE — file written, py_compile PASS, awaiting user run

**What was built:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives_v2.py`
- Full catalogue: S1-S11 (S1-S5 ported from v1 clean, S6-S11 new)
- v1 (`visualize_strategy_perspectives.py`) NOT touched

**S6-S11 panel layout:**
- S6 (Ripster Clouds): Price (Cloud 3 fill + Cloud 2 lines), Cloud 2 delta, Volume bar
- S7 (Quad Stoch): All 4 stochs + alignment count bar + divergence markers
- S8 (Three Pillars): Price + AVWAP, BBWP squeeze, Stoch 55 continuation vs decline
- S9 (BBWP Filter): Single BBWP panel with 6 state colors + MA cross annotations

---

## Session 3 — 2026-03-07 — Stochastic Logic Audit (Next Chat Handoff)

**Context:** After building S1–S11 catalogue, user identified that the live bot's stochastic read does not match what the strategy catalogue describes. This is the suspected root cause of R:R=0.28.

**Live bot stats (38 trades, ~20 hours, Mar 6–7):**
- Win rate: 65.8% (25W / 13L)
- Avg win: +$0.123 | Avg loss: -$0.440 | R:R: 0.28
- Daily PnL: -$2.70 at $50 notional

**Hypothesis:** Bot's stochastic logic (signal_engine.py / strategy plugin) does not match S1/S4/S7 requirements.

---

## NEXT CHAT CONTINUATION PROMPT

```
Handoff Prompt — Stochastic Logic Audit: Bot vs Strategy Catalogue

Context:
- Live bot v2 running at C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\
- R:R = 0.28 (avg win $0.123, avg loss $0.440, WR 65.8%, 38 trades Mar 6-7)
- S1-S11 strategy catalogue visualized in:
  C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives_v2.py
- User diagnosis: "the read of the stochastics is not in par on the bot that it makes sense"
- Primary blocker to scaling roadmap: bot must reach breakeven R:R before anything else matters

Mandatory reads before starting:
1. C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md
2. C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md
3. C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-strategy-catalogue-visual-plan.md (this file)
4. C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-bingx-connector.md
5. C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-55-89-scalp.md

Files to audit (read in order):
1. C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\config.yaml
   -> What stochastic parameters are actually configured? (periods, smooth, thresholds)
2. C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\main.py
   -> Find which strategy plugin is loaded (strat_cfg["plugin"] value)
3. The strategy plugin file (name from config.yaml)
   -> What stoch conditions fire a signal? What is the entry condition exactly?
4. C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\signal_engine.py (if it exists)
   -> How are stochastic values computed? Which periods? Which thresholds?

What to compare against (strategy catalogue):
- S1 (Four Pillars Bible): Stoch 60 macro pin above 80 + Stoch 40 divergence stage 1 or 2 + Stoch 9 cycle below 40 (LONG)
- S4 (Current v3.8.4): 4/4 stoch alignment (9+14+40+60 all above 50) = Grade A entry
- S7 (Quad Rotation): All 4 stochs must be aligned (above 50 LONG / below 50 SHORT) for consensus; divergence from extreme qualifies entry

Audit questions to answer:
1. What stochastic periods does the bot actually use? (9, 14, 40, 60 — or different?)
2. What smooth/K setting? (must be smooth=1 Raw K per locked decision)
3. What is the entry condition? (4/4 alignment threshold? Or single stoch crossing?)
4. Is there a macro filter? (Stoch 60 must be > 80 for LONG in S1 — is this present?)
5. Is BBWP state checked before entry? (S9: BLUE/BLUE DOUBLE = valid window; RED = avoid)
6. Is there a divergence qualifier? (S7: divergence from extreme level is signal qualifier)
7. Specific gaps: list every place where bot logic diverges from strategy catalogue description

Goal:
- Produce a gap list: [what bot does] vs [what strategy says it should do]
- Propose specific code changes to align them
- Target: identify the single highest-impact fix to move R:R from 0.28 toward breakeven
- Do NOT rebuild yet — audit and gap report only first, then propose changes for user approval

NORTH STAR: Every change must be evaluated against breakeven first. R:R = avg_win / avg_loss must approach 1.0+ for rebate income to cover losses.
```
- S10 (ATR SL Phases): Price with SL style-per-phase + TP removed at P3, Cloud 2 delta
- S11 (AVWAP Confirm): 3 AVWAP lines + VSA markers, volume panel, anchor quality bars

**Validation:**
- py_compile: PASS
- ast.parse: not run separately (py_compile clean is sufficient for non-f-string file)

**Run command:**
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/visualize_strategy_perspectives_v2.py
```

**Expected output:** 11 PNGs in `results/strategy_perspectives/`

---

## What Was Done

1. User requested: all strategies documented with market-reading perspectives, visual representations using strategy-viz skill, calm research mode (code only when asked)
2. Plan created and approved: 4 strategies catalogued (Four Pillars v3.8.4, Core Trading Strategy v2, BingX Bot v1.5, 55/89 EMA Cross Scalp)
3. MEMORY.md updated: STARTUP protocol (4 required reads at session start) + NORTH STAR rule (bot must reach monthly breakeven before any other objective)
4. Full version lineage read from source: v3.3 through v3.9.1
5. Visualizer script written: `scripts/visualize_strategy_perspectives.py` (5 strategy perspectives, S1-S5)
6. py_compile: PASS

---

## Key Decisions

### NORTH STAR Rule (locked into MEMORY.md)
Bot must reach monthly breakeven before any other objective matters.
- At $500 margin / 20x WEEX 70% rebate: ~$30,240/month gross rebate per bot
- Current R:R = 0.28 (wins ~$0.12, losses ~$0.44) — losses eat the rebate
- All strategy work evaluated against this constraint first

### Working Mode
- Research/scoping only. No code until user says "build it"
- Do NOT launch parallel explore agents while user is typing
- Read INDEX.md + version-history.md directly before any strategy work (no delegating to agents)

### Strategy Perspectives (not entry/exit mechanics)
User clarified: "we are not looking at entry or exits, we are looking at correct read of the markets"
Each visualizer shows WHAT INDICATORS ARE SENSED and WHAT MARKET STATE IS REQUIRED — not the trade lifecycle.

---

## Build Error (Documented for Future Reference)

**Root Cause:** triple-quoted CONTENT string in build script
`title = "S1 ...\nMarket Read: ..."` — the `\\n` in triple-quoted string became literal `\n` in output file = unterminated string literal in written .py file

**Fix:** Abandoned build script pattern. Used Write tool directly to write the output script. No `\n` in title strings — used ` | ` separator instead.

**Rule added to audit:**
- When build script writes Python source as triple-quoted string, NEVER use `\\n` inside string literals in the output
- py_compile must be run on the OUTPUT file, not just the build script

---

## Output Script

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives.py`

**Run command:**
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/visualize_strategy_perspectives.py
```

**Output:** `results/strategy_perspectives/` — 5 PNG files:
- `S1_bible.png` — Strategy Bible (v3.3 era): 60-macro + 40-divergence + 9-cycle + 55 EMA
- `S2_v381.png` — Four Pillars v3.8.1: full 4-stoch + Ripster clouds + BBWP
- `S3_v384.png` — Four Pillars v3.8.4 (current): AVWAP phases + BBWP + 4-stoch + Cloud 4 TP
- `S4_bingx_v15.png` — BingX Bot v1.5: ATR SL + TTP + EMA filter + BE raise
- `S5_5589_scalp.png` — 55/89 EMA Cross Scalp (research): EMA delta + 4-stoch + TDI + BBW

---

## Files Read This Session

- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md`
- `C:\Users\User\Documents\Obsidian Vault\09-ARCHIVE\four-pillars-version-history.md`
- `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Four-Pillars-Status-Summary.md`
- `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\FOUR-PILLARS-V3.8-CHANGELOG.md`
- `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Trading-Manifesto.md`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-03-signal-rename-architecture-session.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\skills\strategy-viz\SKILL.md`

## Files Written This Session

- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-strategy-catalogue-visual-plan.md` (plan copy)
- `C:\Users\User\.claude\plans\floating-hugging-kite.md` (plan mode file)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_strategy_perspectives.py` (build script — broken approach, kept as artifact)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives.py` (FINAL — direct Write, syntax OK)
- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\MEMORY.md` (updated STARTUP + NORTH STAR)

---

## Next Steps

1. User runs `python scripts/visualize_strategy_perspectives.py` — verify 5 PNGs produced
2. User reviews perspectives — confirm market-reading logic is correct per strategy
3. When ready: say "build visuals for [strategy]" to trigger full strategy-viz 7-scenario treatment per side
4. Strategy v4 design — clean strategy spec to feed into Vince ML pipeline
5. BingX R:R diagnosis — diagnose TTP activation threshold vs SL width (deferred)

---

## Session 2 — 2026-03-07 (Handoff continuation)

**Status:** Research complete. S6–S11 perspectives documented. Build pending ("build it" trigger).

### What Was Done

1. Read all 6 remaining strategy source files
2. Documented market-reading perspectives for S6–S11 (what indicators sensed, what state required, what "aligned" means)
3. Plan written and approved: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-strategy-catalogue-s6-s11-plan.md`

### Strategies Researched

| # | Strategy | Key Market Read |
|---|----------|----------------|
| S6 | Ripster EMA Cloud System | Price vs Cloud 3 (34/50) = bias. Cloud 2 (5/12) = entry gate. Candle closes against 5/12 = exit. |
| S7 | Quad Rotation Stochastic | 4-stoch alignment count (0/4 to 4/4). Divergence on fast (9,3) ONLY, from extreme zones. |
| S8 | Core Three Pillars | Stoch 55 crosses AND continues building = hold. Stoch 55 declines after cross = exit small profit. |
| S9 | BBWP Volatility Filter | 6 named states (BLUE DOUBLE to RED DOUBLE). Filter only — no direction. BLUE DOUBLE = max coil. |
| S10 | ATR SL 3-Phase | Cloud 2/3/4 crosses advance phases. Cloud 2 flip against trade = hard close at any phase. |
| S11 | AVWAP Confirmation | 3 simultaneous AVWAPs (swing high, swing low, volume event). Quality score 0-100. VSA events = anchor. |

### Build Decision

Option B approved: create `visualize_strategy_perspectives_v2.py` — new file, all 11 strategies, v1 untouched.

Output: `results/strategy_perspectives/` — S6_ripster_clouds.png through S11_avwap_confirmation.png

### Files Written

- `C:\Users\User\.claude\plans\serene-hatching-karp.md` (plan mode file)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-strategy-catalogue-s6-s11-plan.md` (vault plan copy)

### Next Steps

1. User says "build it" — triggers Python skill + Write of `visualize_strategy_perspectives_v2.py`
2. py_compile must pass
3. Run: `python scripts/visualize_strategy_perspectives_v2.py`
4. Verify 11 PNGs produced
5. Review S6–S11 panels against perspectives documented above

---

## Session 3 — 2026-03-07 — Strategy v4 Design

**Status:** COMPLETE — design doc written, no code built

### What Was Done

1. Read all mandatory startup files + bot code (config.yaml, plugin, state_machine.py, stochastics.py, four_pillars.py)
2. Identified root cause of R:R = 0.28: state machine is an **oversold reversal model** (all 4 stochs dip to extreme low zones simultaneously and bounce). Strategy catalogue describes a **hierarchical model** (macro stochs provide direction, fast stoch provides timing). Fundamental mismatch.
3. Planned strategy v4 — hybrid model approved by user
4. User said "do not build — think about it" after approval
5. Presented full option map (all entry + exit levers with tradeoffs)
6. User asked for a core MD file to work out the design
7. Created living design document

### Root Cause Detail

| Dimension | v3.8.4 (current) | What catalogue says |
| --------- | ---------------- | ------------------- |
| Stage 1 trigger | stoch_9 < 25 | stoch_9 pullback within trend |
| stoch_40 role | must be < 30 (oversold) | must be > 50 (trend bullish) |
| stoch_60 role | must be < 25 (oversold) | must be > 50 (macro bullish) |
| When signal fires | all stochs bounce from extreme lows | macro up, only fast stoch pulls back |

Result: entering in full capitulation — ATR elevated, SL wide, bounce small. Hence avg win $0.12 vs avg loss $0.44.

### Design Document Created

`C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\STRATEGY-V4-DESIGN.md`

Contents:

- Problem statement with live data
- Full option map (Entry: A-D, Exit: E-G, Analysis: H-I)
- Proposed hybrid model logic (written out as pseudocode)
- Default parameters table
- Open questions before building
- Validation criteria (R:R > 1.0 target)
- Backtest results table (blank — to fill)
- Decision log

### Files Written (Session 3)

- `C:\Users\User\.claude\plans\robust-dazzling-kazoo.md` (plan mode file)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-strategy-v4-build-plan.md` (vault plan copy)
- `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\STRATEGY-V4-DESIGN.md` (living design doc)

### Next Steps (Session 3)

1. Work out open questions in `STRATEGY-V4-DESIGN.md` (threshold values, stoch_14 inclusion, stage_lookback)
2. When design is settled — say "build it" to trigger backtester build (3 files)
3. Run `run_v4_backtest.py` — compare R:R vs v3.8.4 baseline
4. If R:R > 1.0 validates — build bot plugin `four_pillars_v4.py`

---

## Session 4 — 2026-03-10 — Strategy v4 Question 1 Deep Dive

**Status:** COMPLETE — key correction made, handoff prompt written

### Key Correction: Cascade Model (not Hybrid)

Original v4 proposal ("macro stochs above 50, fast stoch below 40") was wrong.

Correct model from Kurisko + chart analysis:

- **Price forms a descending channel** — lower lows, lower highs = structural context
- **Stoch 9** hits extreme (<20) and diverges (separate from TDI — do not conflate)
- **Stoch 40** turns/crosses out of oversold FIRST — early entry signal while price is still inside the channel
- **SMI 60** catches up AFTER — lagging confirmation, not an entry gate

The slow stoch does NOT need to be above 50 before entry. It confirms after. The cascade is: channel → Stoch 9 extreme → Stoch 40 crosses out → SMI 60 catches up.

### Still Open

- Stoch 9 exact role (separate from TDI — not yet fully resolved)
- Questions 2-4 not yet discussed

### Files Written (Session 4)

None — research only. `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\STRATEGY-V4-DESIGN.md` needs updating once all questions are closed.

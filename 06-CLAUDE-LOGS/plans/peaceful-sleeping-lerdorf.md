# Plan: V4 Strategy — Understanding First, Build Never (Until Approved)

## Context

**Problem:** R:R = 0.28 on live bot. v3.8.4 enters all 4 stochs simultaneously at extreme lows (V-bottom pile-in). Need V4 that is at least breakeven independently.

**Core principle:** V4 will NOT be built until the strategy is fully understood, clearly expressed in writing, visually confirmed, and explicitly approved by the user. Code is the last step, not the goal.

**Current state:**
- `run_trade_chart_report.py` — being built by another agent. Generates per-trade HTML charts from live BingX bot (47 coins). 4-panel: candles+EMA55/89+AVWAP, all 4 stochastics overlaid, volume.
- `STRATEGY-V4-DESIGN.md` + `S12-MACRO-CYCLE.md` — existing strategy docs with ideas but no confirmed logic
- No V4 code exists. No V4 backtests exist.

---

## Phase 1: Data Collection (User-Driven)

The chart report tool generates visual data from real live trades. User runs the bot, generates charts, and reviews them at their own pace.

**What the user observes on each trade:**
- What was stoch_60 doing at entry?
- Was the entry with or against the EMA trend?
- Did stochastics cascade or pile in?
- Where did the trade exit vs where it should have?
- Were there better entries the bot missed?

**User writes comments** in the chart report's trade note textareas. These are raw observations, not rules.

**Deliverable:** Annotated trades with the user's own words describing what they see.

---

## Phase 2: Verbal Pattern Discovery (Joint Discussion)

When the user has enough annotated trades, we sit down together and talk through what they observed.

**Goal:** Translate raw observations into clear verbal statements about what works and what doesn't.

**Format:** Conversation. The user describes patterns they noticed. We ask clarifying questions. We write down statements like:
- "When stoch_60 was above 50 at entry and stoch_9 pulled back to 35, the trade worked"
- "When all four stochs were below 25 at the same time, the trade always lost"
- "The bot entered against the EMA trend on 70% of losers"

**Deliverable:** A written document of pattern statements in plain language, each tied to specific trade examples.

---

## Phase 3: Strategy Expression in Writing

Take the pattern statements from Phase 2 and organize them into a clear strategy description:

1. **What must be true to enter** (stated in plain English, not code)
2. **What must NOT be true to enter** (rejection conditions)
3. **How entries are graded** (what makes a high vs low confidence setup)
4. **Where the stop goes and why**
5. **Where the exit is and why**
6. **What keeps you in the trade**

Every statement references the trade evidence it came from. Nothing is assumed or theoretical.

**Deliverable:** A strategy document that reads like a trading plan a human would follow manually. No code references. No parameter tables. Pure verbal logic.

---

## Phase 4: Visual Confirmation

Create the right type of visual representation that proves the written logic is correct:

- Charts that show "here is what the strategy describes, and here is what actually happened"
- The user can look at any chart and say "yes, this is exactly what I mean" or "no, that's wrong"
- The visual must match the verbal description 1:1

**What type of visual** — to be determined during Phase 3. Could be annotated trade examples, scenario diagrams, indicator state overlays, or something else entirely. The user decides what representation makes the logic clearest to them.

**Deliverable:** Visual proof that the written strategy is understood correctly. User explicitly confirms.

---

## Phase 5: User Approval Gate

**Nothing beyond this point happens without explicit user approval.**

The user reviews:
1. The written strategy (Phase 3)
2. The visual confirmation (Phase 4)

And says one of:
- "This is correct, build it" -- then and only then does code get written
- "This part is wrong" -- go back to Phase 2/3/4 and fix it
- "I need more data" -- go back to Phase 1

---

## What Happens NOW

1. Other agent finishes `run_trade_chart_report.py` -- in progress
2. User runs bot, generates trade charts
3. User reviews and annotates trades at their own pace
4. When ready, user comes back and we start Phase 2 discussion

**No code will be built in this workflow until the user explicitly approves the strategy.**

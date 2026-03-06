# Cards on the Table: What the Bot Knows vs What You Know

**Date:** 2026-03-05
**Purpose:** Lay out every card — what each trade grade actually means in code, what "perspective" means to you vs to the bot, and why PIPPIN LONG happened. No comparisons, no qualifying. Just facts.

---

## Card 1: What the Bot Thinks a B Trade Is

**File:** `PROJECTS\four-pillars-backtester\signals\state_machine.py` lines 157-160

A **B LONG** fires when ALL of these are true:
1. Stoch 9 crossed below 25 (setup started), then crossed back above 25 (trigger)
2. During setup: **at least 2 of 3** stochastics (14, 40, 60) dipped below 30
3. Price is at or above Cloud 3 (`price_pos >= 0`)
4. B trades are allowed in config (`allow_b=true`)

A **B SHORT** fires when:
1. Stoch 9 crossed above 75, then crossed back below 75
2. During setup: at least 2 of 3 stochastics (14, 40, 60) went above 70
3. Price is at or below Cloud 3

**What "at least 2 of 3" means:** The third stochastic never confirmed. The trade has a hole in it. One of the slower stochastics (14, 40, or 60) never entered the zone during the setup window.

**What "price at Cloud 3" means:** `price_pos >= 0` is the only directional check. This is "price is above EMA 34/50." That's it. No 4h, no 1h, no 15m MTF clouds, no sequential cloud flips, no structural confluence.

---

## Card 2: What the Bot Thinks an A Trade Is

**File:** `PROJECTS\four-pillars-backtester\signals\state_machine.py` lines 155-156

A **A LONG** fires when ALL of these are true:
1. Stoch 9 crossed below 25 then back above 25
2. During setup: **ALL 3** stochastics (14, 40, 60) dipped below their zone levels
3. Price is at or above Cloud 3
4. Stage 2 conviction passes (if `require_stage2=true`):
   - Stoch 40 AND 60 both rotated through 20 during setup
   - Price was at Cloud 3 within the last 5 bars

**The difference: A = all 3 confirmed + Stage 2 rotation. B = only 2 confirmed, no Stage 2 required.**

---

## Card 3: What the Bot Does NOT Know

The bot has **zero concept of**:

| Concept | Your trading | Bot's version |
|---------|-------------|---------------|
| Session bias (4h/1h) | Cloud stack flipping on higher TFs, set once per day | Does not exist |
| "The perspective" | "Today is a long day" — all trades align with this | Does not exist |
| 15m MTF clouds | Execution filter confirming HTF bias on 5m chart | Does not exist |
| Sequential K/D crosses | All 4 stochs must individually cross K above D | Only checks zone entry (K < 25), not K/D relationship |
| BBW spectrum vs MA | Validates "the move is real" | Not checked at entry |
| TDI price vs MA | Must be on correct side | Not checked at entry |
| "Coming from the zone" | K was in zone within last N bars | Partially — tracks zone entry during setup window |
| Structure validation | SL must land near AVWAP/swing/S/R level | Uses raw 2x ATR, no structure check |

---

## Card 4: Why PIPPIN LONG Happened (2026-02-28 09:05:35)

**Log:** `PROJECTS\bingx-connector\logs\2026-02-27-bot.log` line 10667

```
Signal: LONG-B entry=0.673800 sl=0.654449 tp=None atr=0.009675
```

**What the bot saw:**
- Stoch 9 had dipped below 25 and crossed back above — trigger fired
- 2 of 3 slower stochs (14/40/60) entered their zones during setup — B grade
- Price was above Cloud 3 (EMA 34/50) — gate passed
- `allow_b=true` — B trades permitted

**What the bot did NOT see:**
- Whether 4h/1h perspective was long or short that day
- Whether 15m MTF clouds supported a long
- Whether all 4 stochs had K > D (sequential alignment)
- Whether BBW spectrum was above its MA
- Whether TDI was above its MA
- Whether the price was in "nowhere's land" between clouds with no directional conviction

**The bot passed its own rules. Its rules are incomplete.**

---

## Card 5: The Bot Is Running v3.8.4, Not v3.8.6

**File:** `PROJECTS\bingx-connector\config.yaml`

```yaml
strategy:
  plugin: four_pillars_v384
```

v3.8.6 has Stage 2 conviction ON by default. v3.8.4 has it OFF by default (code line defaults to `False`). The config has `require_stage2: true`, but the v384 plugin code defaults to `False` — there may be a loading bug where the config value isn't propagating.

**If Stage 2 was active:** That PIPPIN B-trade might have been blocked (A-trades with Stage 2 are much stricter, and B-trades that would have been A-but-for-Stage2 are also blocked).

**If Stage 2 was NOT active:** Every B-trade is just "2 of 3 stochs + Cloud 3 gate" — very permissive.

---

## Card 6: What "Perspective" Really Means (From Your Trading)

**Source:** Position Management Study (`fizzy-humming-crab.md`)

**Layer 1 — Session Bias (4h/1h, set at start of day):**
- 4h: Cloud stack flipping direction (bearish = clouds above price, bullish = clouds below)
- 1h: Sequential cloud flips — Cloud 2 first, then 3, then 4 — converging at a structural level
- When they converge and price breaks through = perspective confirmed
- This is binary: "Today is a long day" or "Today is a short day"

**Layer 2 — Execution Filter (15m MTF Clouds on 5m):**
- Ripster MTF Clouds (EMA 50/55 + 20/21, resolution=15m)
- NOT a hard filter — modulates hold duration
- Price below MTF = cautious, quick close
- Price above MTF = reason to hold (trend-hold trade)

**Layer 3 — Entry Timing (5m):**
- Stochastic alignment + BBW + TDI
- But ONLY in the direction Layers 1+2 established

**Rule: You never trade against the perspective. If 4h says bearish, you only take shorts. Period.**

The bot has no Layer 1 or Layer 2. It trades both directions equally based on 5m signals alone.

---

## Card 7: What "Nowhere's Land" Means

Price is above Cloud 3 (passing the bot's only directional gate), but:
- Not at a structural level (AVWAP, swing, S/R)
- Not confirmed by sequential cloud flips on higher TFs
- Not in a zone where BBW spectrum validates the move
- Stochastics may be mid-range, not coming from extremes with conviction

The bot's Cloud 3 gate (`price_pos >= 0`) is too crude to distinguish between "strong directional move above Cloud 3" and "drifting sideways above Cloud 3 with no conviction."

---

## Card 8: What Volume Generation Means vs Top-Tier Waiting

Two modes that should coexist:

1. **Volume generation** — higher frequency, smaller conviction trades that accumulate rebate income. The current B-trade grading was designed for this, but without perspective it takes bad trades.

2. **Top-tier waiting** — A-grade trend-hold trades with full perspective alignment. Low frequency, high conviction. Requires the HTF layers and Stoch 60 gate.

**The bridge:** A coin monitor that watches a set of coins and flags which ones have the movement (volatility, trend, volume) worth trading. This pre-filters BEFORE signals fire.

---

## Card 9: The 6 Open Questions (Still Unanswered)

These are from the position management study and block any trend-hold implementation:

| ID | Question | Why it matters |
|----|----------|---------------|
| SL-1 | 2 ATR doesn't align with structure — adjust or skip? | Determines if trades get filtered or SL gets moved |
| SL-2 | What counts as "structure"? | Defines the validation layer for SL |
| GATE-1 | Stoch 60 K-D distance threshold? | Defines when a trade becomes a trend-hold |
| BE-1 | Which BE method when? | Determines breakeven logic |
| TRAIL-1 | AVWAP plain vs +sigma — what determines it? | Determines trailing mechanism |
| CLOUD-1 / TP-1 | Frozen Cloud 4 vs % target — when which? | Determines TP framework |

---

## Card 10: What CAN Be Done Without Answering Those 6

Even before the trend-hold questions are resolved, the **entry side** can be improved:

1. **Perspective layer** — Add HTF direction check so the bot NEVER takes a long on a short day (or vice versa). This is the single biggest filter missing.

2. **B-trade tightening** — Either:
   - Require Stage 2 to be truly active (fix potential v384 config bug)
   - Upgrade to v386 signal logic
   - Add BBW spectrum > MA as entry gate
   - Add TDI correct-side check

3. **Coin monitoring** — Pre-filter which coins are worth watching based on ATR/volume/trend metrics. Don't signal on coins in nowhere's land.

4. **Sequential K/D check** — Instead of "stoch dipped below zone," require K/D crossover alignment (what you actually look for).

None of these require answering the 6 open questions. They're all entry-side improvements that prevent bad trades from being taken in the first place.

---

## Summary: The Deck

| Card | What it shows |
|------|--------------|
| 1 | B trade = 2 of 3 stochs + Cloud 3 gate (weak) |
| 2 | A trade = all 3 + Stage 2 (strong but rare) |
| 3 | Bot has no HTF direction, no BBW, no TDI, no structure |
| 4 | PIPPIN LONG passed the bot's weak rules legitimately |
| 5 | Bot runs v384 not v386 — Stage 2 may be off |
| 6 | Your "perspective" = 3-layer HTF system, non-negotiable |
| 7 | "Nowhere's land" = Cloud 3 gate too crude to catch |
| 8 | Volume generation vs top-tier waiting are two modes |
| 9 | 6 open questions block trend-hold builds |
| 10 | Entry-side fixes don't need those 6 questions |

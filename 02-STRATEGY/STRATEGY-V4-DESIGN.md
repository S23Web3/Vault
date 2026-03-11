# Strategy v4 — Design Working Document

*Living document. Updated as decisions are made.*
*Last updated: 2026-03-07*

---

## The Problem

**Live bot stats (38 trades, ~20 hours, Mar 6-7 on BingX):**

| Metric | Value |
|--------|-------|
| Win rate | 65.8% (25W / 13L) |
| Avg win | +$0.123 |
| Avg loss | -$0.440 |
| R:R | 0.28 |
| Daily PnL | -$2.70 at $50 notional |

**Breakeven target:** R:R must approach 1.0+ for rebate income ($4.80/RT net at 70% WEEX) to cover losses.

**Interpretation of the stats:**
- WR 65.8% means entries are often directionally correct
- R:R 0.28 means wins are tiny relative to losses
- This pattern = entries in the right direction but at bad timing — entering into already-oversold conditions with elevated ATR, so SL is wide and the bounce has little room to run

---

## Root Cause: Signal Model Mismatch

### What the bot's state machine actually does (v3.8.4)

```
Stage 0 → Stage 1: stoch_9 < 25
Stage 1 accumulates:
  - long_14_seen: stoch_14 < 30
  - long_40_seen: stoch_40 < 30
  - long_60_seen: stoch_60 < 25
Signal fires when stoch_9 crosses back above 25
Grade A: all three (14/40/60) seen in low zones + price above Cloud 3
Grade B: two of three seen in low zones + price above Cloud 3
```

**This is a pure oversold reversal model.** All four stochastics pile into extreme low zones simultaneously, then the fastest one bounces.

### What the strategy catalogue says should happen

| Strategy | What it describes |
|----------|--------------------|
| S1 (Bible) | Stoch 60 pins ABOVE 80 (macro bullish) + stoch 40 divergence stage + stoch 9 cycles below 40 (pullback) |
| S4 (v3.8.4 as intended) | 4/4 stoch alignment above 50 = Grade A (trend continuation, not reversal) |
| S7 (Quad Rotation) | Alignment count 0-4 as consensus; divergence on fast stoch ONLY from extreme |

**The code does not match the catalogue.** When all four stochs are below 25-30 simultaneously, there is no macro trend support. You're entering a coin in full panic/capitulation — the bounce is small and SL is wide.

---

## Option Map

### Entry Levers

| Option | What changes | Risk | Expected impact |
|--------|-------------|------|----------------|
| **A — Hierarchical stochs** | Macro stochs (40/60) must stay ABOVE 50. Only stoch_9 dips below 40 for entry. | Medium — rewrites state machine | High — entries with trend support, smaller ATR at pullback = tighter SL, more room to run |
| **B — BBWP gate** | Keep current signal. Block entries when BBWP is RED (expanding volatility). | Low — pure filter, no signal change | Medium — removes blowout entries but doesn't fix the core mismatch |
| **C — Cloud 2 gate** | Only enter when price crosses Cloud 2 (5/12 EMA). Stochs still set direction. | Low-Medium | Medium — precise timing at structural event |
| **D — 55/89 EMA cross** | Completely different signal. EMA cross triggers, stochs confirm. | High — full rebuild | Unknown — needs backtesting |

### Exit Levers

| Option | What changes | Risk | Expected impact |
|--------|-------------|------|----------------|
| **E — Stoch 55 continuation (S8)** | After entry: if stoch_55 continues building → hold. If it declines → exit early with small profit. | Medium — new monitor loop | High on wins — directly extends avg win duration |
| **F — ATR SL 3-phase (S10)** | Phase 0: 2x ATR. Phase 1 (Cloud 2 cross): move to BE. Phase 2: trail. | Medium — new phase logic | Medium — locks profit faster, reduces large losses |
| **G — Tune TTP parameters** | Adjust activation (0.8% → 0.5%), distance (0.3% → 0.25%) | Very Low — config only | Low-Medium — may capture more of the existing wins |

### Analysis First

| Option | What it tells us |
|--------|-----------------|
| **H — Backtest v3.8.4 on historical data** | Baseline R:R, signal count, WR per coin. Shows whether live stats are typical or anomalous. |
| **I — Backtest v3.8.4 vs v4 side by side** | Data-driven comparison. Only build v4 after seeing the baseline. |

---

## Design Decisions

*Mark each as the design evolves.*

### Signal Model
- [ ] Hierarchical (A): macro stochs direction, fast stoch timing
- [ ] BBWP gate (B): keep current signal + volatility filter
- [ ] Hybrid: A + B combined
- [ ] Other: _______________

**Thinking:**

> The WR of 65.8% suggests the direction read is often right. The problem is the TIMING — entering when everything is already deep oversold means:
> (1) ATR is elevated → SL is wider → larger losses
> (2) The bounce has little room left → smaller wins
>
> Hierarchical model (A) would enter during a PULLBACK within a TRENDING market — ATR is lower (trend is orderly), there's more room for the trade to run.
>
> BBWP gate (B) is a cheap add-on but doesn't fix the core timing problem.

### Entry Trigger Thresholds (if A or Hybrid)

**LONG entry conditions:**

| Condition | Proposed | Reasoning |
|-----------|----------|-----------|
| Stoch_60 > ? | 50 (Grade B), 60 (Grade A) | Macro must be bullish — at least middle of range |
| Stoch_40 > ? | 50 (Grade B), 55 (Grade A) | Trend must confirm |
| Stoch_9 < ? | 40 (Grade B), 35 (Grade A) | Pullback zone — not too deep |
| Stoch_14 role | < 45 = optional Grade A qualifier | Between fast and slow — confirms pullback is shallow |
| Cloud 3 | Price at/above Cloud 3 | Already in state machine |

**OPEN QUESTIONS:**
- Does stoch_14 add value or just create noise?
- Should stoch_60 threshold be 50 or higher (60, 65)?
- How wide should the stage_lookback window be? (currently 10 bars)

### Exit Management
- [ ] Keep current TTP only
- [ ] Add stoch_55 continuation monitor (S8)
- [ ] Add ATR SL 3-phase (S10)
- [ ] Both S8 + S10

**Thinking:**

> If entry quality improves, TTP may already work better (more room to run).
> S8 (stoch_55 continuation) is elegant — uses an indicator already in the ecosystem.
> S10 (3-phase) is more mechanical, fits the existing cloud framework.
> Recommendation: validate entry change first, then look at exit.

### Deployment Order
- [x] Backtester first → bot plugin after validation

---

## Working Out the Hybrid Model

### Stage Machine Logic (proposed)

```
LONG setup:

Stage 0 → Stage 1 trigger:
  stoch_9 < fast_trigger (40)        ← fast stoch pulls back
  AND stoch_40 > trend_min (50)      ← trend still bullish
  AND stoch_60 > macro_min (50)      ← macro still bullish

Stage 1 accumulates (window = stage_lookback bars):
  - stoch_40 > trend_strong (55) seen  ← strong trend confirmation
  - stoch_60 > macro_strong (60) seen  ← strong macro
  - stoch_14 < confirm_max (45) seen   ← shallow pullback on medium stoch

Signal fires when stoch_9 >= fast_trigger (crosses back above 40):
  Grade A: trend_strong seen + macro_strong seen + cloud3_ok
  Grade B: stoch_40 > trend_min (entry bar) + stoch_60 > macro_min (entry bar) + cloud3_ok

SHORT (mirror):
  Stage 1 trigger: stoch_9 > (100 - fast_trigger = 60)
                   AND stoch_40 < (100 - trend_min = 50)
                   AND stoch_60 < (100 - macro_min = 50)
  Grade A: stoch_40 < (100 - trend_strong = 45) seen + stoch_60 < (100 - macro_strong = 40) seen + cloud3_ok_short
```

### What This Fixes

| Problem | v3.8.4 | v4 Hybrid |
|---------|--------|-----------|
| Macro support | None — stoch_60 also at lows | Required — stoch_60 > 50 gates entry |
| ATR at entry | Elevated (deep oversold = high vola) | Lower (pullback within trend = orderly) |
| SL width | 2x elevated ATR = large loss | 2x lower ATR = smaller loss |
| Win room | Small (bounce from extreme) | Larger (trend continuation) |

### Parameters (initial defaults, to be swept)

```python
V4_DEFAULTS = {
    "v4_fast_trigger": 40,   # stoch_9 pullback threshold
    "v4_fast_grade_a": 35,   # stoch_9 < this = Grade A qualifier
    "v4_trend_min":    50,   # stoch_40 minimum for LONG
    "v4_trend_strong": 55,   # stoch_40 > this = Grade A
    "v4_macro_min":    50,   # stoch_60 minimum for LONG
    "v4_macro_strong": 60,   # stoch_60 > this = Grade A
    "v4_confirm_max":  45,   # stoch_14 < this = shallow pullback confirmed
    "stage_lookback":  10,   # bars to accumulate in Stage 1
    "allow_b":         True,
    "allow_c":         False,
}
```

### Open Questions Before Building

1. **Threshold sweep**: should fast_trigger be 40 or 35? Higher = more signals but lower quality.
2. **stoch_14**: include or ignore? Adds complexity, may add filtering power.
3. **Stage lookback**: 10 bars (50 min on 5m) — is that enough to see the pullback develop?
4. **Grade A/B ratio**: how many Grade A vs B signals will we get with these thresholds?

---

## Validation Criteria

Before bot deployment, v4 must show in backtester:

| Metric | Target |
|--------|--------|
| R:R | > 1.0 (vs current 0.28) |
| WR | > 50% (acceptable if R:R > 1) |
| Signal count per coin | Not less than 50% of v3.8.4 (can't filter everything out) |
| Net P&L | Positive across majority of coins |

---

## Backtest Results (to be filled in)

### v3.8.4 Baseline

| Coin | Signals | WR | Avg Win | Avg Loss | R:R | Net PnL |
|------|---------|----|---------|----------|-----|---------|
| — | — | — | — | — | — | — |

### v4 Hybrid

| Coin | Signals | WR | Avg Win | Avg Loss | R:R | Net PnL |
|------|---------|----|---------|----------|-----|---------|
| — | — | — | — | — | — | — |

---

## Files

### Backtester (to build)
- `signals/state_machine_v4.py` — new state machine
- `signals/four_pillars_v4.py` — orchestrator using new SM
- `scripts/run_v4_backtest.py` — side-by-side comparison vs v3.8.4

### Bot plugin (after validation)
- `PROJECTS/bingx-connector-v2/plugins/four_pillars_v4.py`

### Reference (do not modify)
- `signals/state_machine.py` — current v3.8.4
- `signals/stochastics.py` — Raw K calc, correct, unchanged
- `signals/clouds.py` — cloud calc, unchanged

---

## Out of Scope (v4.0)

These are valid future enhancements but not part of v4.0:
- BBWP volatility gate (S9) — add after v4 validates
- Stoch 55 continuation exit (S8) — after entry quality confirmed
- ATR SL 3-phase progression (S10) — after basic model works
- AVWAP confirmation (S11) — complex, future
- Parameter sweep / optimization — after manual validation

---

## Decision Log

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2026-03-07 | Signal model: Hybrid (macro stochs direction, fast stoch timing) | WR 65.8% = direction often right; problem is timing/ATR at entry |
| 2026-03-07 | Deployment: backtester first, bot second | Validate on historical data before touching live bot |
| 2026-03-07 | stoch_14 in Grade A: TBD | Need to see signal count with/without before deciding |

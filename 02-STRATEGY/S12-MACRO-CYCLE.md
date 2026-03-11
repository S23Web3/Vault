# S12 — Macro Cycle Strategy

*Derived from live chart analysis, PIPPINUSDT 5m, 2026-03-10*
*Last updated: 2026-03-10*

---

## Thesis

stoch_60 is the primary instrument. The trade opens when stoch_60 exits an extreme and closes when it reaches the opposite extreme. Cloud structure sets direction. BBWP times exhaustion. TDI and shorter stochs confirm cascade quality. Everything serves the stoch_60 cycle.

This is NOT a pure oversold reversal model. The signal fires when stoch_60 EXITS an extreme — not when it's deepest inside one.

---

## Two-Tier Entry Architecture

One stoch_60 cycle can produce multiple entries with the same directional thesis and the same exit target. Both tiers share a RADAR state — the system arms when stoch_60 enters an extreme and watches for the cross.

```
RADAR STATE: armed when stoch_60 enters extreme zone (< 25 or > 80)
             disarmed when cloud structure invalid or BBWP at climactic extreme

TIER 1 — SIDE ENTRY (clean mechanical)
  Fires:   stoch_60 K crosses the extreme threshold (above 25 or below 80)
  Filters: cloud direction only (Cloud 2 color, Cloud 3 position)
  Exit:    Cloud 3 midband (LONG) or stoch_60 reaching opposite extreme (SHORT)
  Profile: fires every valid cross, lower R:R but higher frequency
  Use:     base position, always-on within the cycle

TIER 2 — CORE ENTRY (filtered, higher confidence)
  Fires:   V4 four-layer pipeline confirms within the same cycle
           (macro gate + channel gate + two-cycle divergence + cascade gate)
  Filters: full filter stack
  Exit:    same as Tier 1 — Cloud 3 midband or opposite extreme
  Profile: fewer fires, higher R:R, better cascade quality confirmation
  Use:     add-on to Tier 1 position OR standalone if Tier 1 missed

ENTRY SEQUENCE within one cycle (LONG example):
  Bar 0:   stoch_60 enters oversold — RADAR ARMED
  Bar ~12: Cycle 1 forms (stoch_9 first dip below 25)
  Bar ~28: Cycle 2 forms (stoch_9 second dip — divergence building)
  Bar ~33: stoch_60 K crosses above 25 — TIER 1 FIRES
  Bar ~35: V4 all four layers confirmed — TIER 2 FIRES (same direction, same exit)
  Bar ~55: Price enters Cloud 3 midband — BOTH EXIT

SAME EXIT for both tiers = no ambiguity in position management
```

---

## Five-Tier Entry Architecture (Full)

Every distinct signal type identified from today's live chart analysis. All five can fire within one stoch_60 cycle, in the order below. Direction is set by the same rules throughout.

```
TIER 0 — PRE-CROSS STRUCTURAL EXHAUSTION
  What it reads:
    stoch_60 is AT deep extreme (SHORT: K >= 85, LONG: K <= 15)
    AND Cloud 2 delta is THIN (weak near-term structure)
    AND TDI fast line IS at Bollinger Band extreme (but not yet bouncing)
  Entry timing:
    Enters BEFORE the stoch_60 threshold cross
    Entry bar = the candle printing the exhaustion extreme
  Stop loss:
    SHORT: this bar's high — the exact exhaustion candle
    LONG:  this bar's low
    Tightest SL of all tiers — structure SAY the peak is here
  R:R profile:
    Highest — because the SL is at the turn candle, not a swing
  Example: 2026-03-08 SHORT on PIPPINUSDT — stoch_60 at 89, thin cloud
    2.86% move / 20% roi at 20x. SL was at the peak of that candle.
  Risk: stoch_60 can stay pinned in extreme before crossing — do NOT chase
        if missed, fall through to Tier 1

TIER 1 — CROSS MECHANICAL
  What it reads:
    stoch_60 K crosses threshold (above 25 for LONG, below 80 for SHORT)
    stoch_60 K/D cross confirmed in direction
    Cloud 2 blue (LONG) or any (SHORT with price belowcloud3)
  Entry timing:
    The cross bar itself
  Stop loss:
    Recent swing high/low (1-3 bars back)
    Wider than Tier 0
  R:R profile:
    Standard — fires every valid cycle, base frequency
  Example: 2026-03-10 LONG on PIPPINUSDT — stoch_60 cross above 25
    1% to Cloud 3 midband / 20% ROI at 20x

TIER 2 — TDI BOLLINGER BAND BOUNCE
  What it reads:
    TDI fast line bounces from its lower (LONG) or upper (SHORT) Bollinger Band
    TDI MA starts sloping in the direction of the trade
    Price staying above/below blue/gold cloud confirms structural alignment
  Entry timing:
    Can fire same bar as Tier 1 cross or 1-5 bars after
    Sometimes fires before the cross if TDI leads stoch_60
  Stop loss:
    Same as Tier 1 — recent swing
  R:R profile:
    Similar to Tier 1 — adds momentum confirmation, not structural tightness
  Note: TDI MA sustained slope = continuation (not spike reversal)
        TDI MA flat or reversing = do not hold

TIER 3 — V4 CASCADE DIVERGENCE
  What it reads:
    Two-cycle stoch_9 divergence (price LL + stoch HL)
    Orderly pre-Stage1 decline (channel gate, R² > 0.45, slope < -0.1%/bar)
    stoch_40 recovering BEFORE stoch_60 (cascade, not simultaneous pile-in)
    stoch_60 >= 40 (macro gate)
  Entry timing:
    Within same stoch_60 cycle as Tier 1 — fires a few bars after T1
    when the divergence and cascade are both confirmed
  Stop loss:
    Cycle's structural swing low/high
  R:R profile:
    Highest confidence — all four layers filtered
    Fewer fires but best signal quality

TIER 4 — CLOUD MIDBAND CYCLE TRANSITION
  What it reads:
    Price reaches Cloud 3 midband — this is the LONG exit trigger
    AND stoch_60 is NOW building toward overbought (K rising, K > D)
    This is the SHORT entry for the NEXT cycle, fired at the LONG exit bar
  Entry timing:
    The same bar that closes the LONG trade
    Entry SHORT at Cloud 3 midband = macro resistance
  Stop loss:
    The candle that printed the Cloud 3 midband touch
    Very tight — you are fading macro resistance from the exact touch level
  R:R profile:
    High — SL is the resistance touch bar, full SHORT cycle downside ahead
  Note: This tier can only fire after a LONG cycle has completed
        "Exit LONG, enter SHORT" at the same price level
        The gold cloud midband is BOTH the LONG exit AND the SHORT entry

CYCLE SEQUENCE (LONG example — all five tiers):
  Bar 0:   stoch_60 enters oversold < 25 — RADAR ARMED
  Bar ~5:  stoch_60 at 12, cloud thin — TIER 0 FIRES (pre-cross entry)
  Bar ~15: stoch_60 K crosses above 25 — TIER 1 FIRES
  Bar ~17: TDI fast line bounces from lower BB — TIER 2 FIRES
  Bar ~20: V4 divergence + cascade confirmed — TIER 3 FIRES
  Bar ~40: Price hits Cloud 3 midband — ALL LONG TIERS EXIT
           stoch_60 now building toward overbought — TIER 4 FIRES (SHORT entry)
```

---

## Indicator Stack

| Indicator | Role |
|-----------|------|
| stoch_60 | Primary instrument — trade lives and dies by its cycle. Fires the entry. |
| Cloud 3 (34/50 EMA, gold) | Macro structure. Defines TP (Cloud 3 midband = LONG exit target). Informs SL movement. |
| Cloud 2 (5/12 EMA, teal/blue) | Near-term structure. Macro context. Informs SL movement. Delta thickness = structural strength. |
| BBWP | Exhaustion timing — squeeze entry vs climactic extreme |
| TDI Bollinger Bands | Momentum exhaustion/reversal confirmation (T0, T2) |
| stoch_9 / stoch_40 | Cascade quality — sequential vs simultaneous (T3) |

**Cloud does not drive entry.** Cloud aids in macro context, TP setting, and SL movement. The entry is fired by stoch_60 and the tier-specific triggers. Cloud is not an entry gate or filter.

---

## Cloud Delta Interpretation

```
Cloud 2 (5/12) THICK BLUE  = strong near-term bullish support — do not short
Cloud 2 (5/12) THIN BLUE   = weak near-term structure — valid short entry zone
Cloud 2 (5/12) GOLD/RED    = near-term bearish
Cloud 3 (34/50) GOLD above price = macro bearish overhead
Cloud 3 (34/50) BLUE below price = macro bullish support
```

Thin cloud delta = price hovering at structural inflection — tight SL available, high R:R.

Cloud structure informs macro context (are we in a bullish or bearish regime?), sets TP targets (Cloud 3 midband = LONG exit), and guides SL movement. It does not gate entry.

---

## BBWP States

```
Blue Double (<10%)   = pre-expansion squeeze — volatility about to expand
20-40%               = healthy expansion window — preferred entry range
Red Double (>90%)    = climactic exhaustion — cover immediately, do NOT chase
Near 0-2%            = volatility fully bled out — move is done
```

---

## Entry Conditions

### SHORT

```
REQUIRED:
  stoch_60 K crosses below 80 (exits overbought)
  stoch_60 K < D (bearish cross confirmed)

CONFIRMING (not required — increases confidence):
  stoch_40 also in overbought (> 75) at entry bar
  BBWP 20-40% at entry (room for volatility to expand)
  TDI fast line near upper Bollinger Band (momentum exhaustion approaching)

STOP LOSS:
  Recent swing high (the candle that printed the stoch_60 peak)
  Tight by construction — entry IS at the exhaustion point
```

### LONG

```
REQUIRED:
  stoch_60 K crosses above 25 (exits oversold)
  stoch_60 K > D (bullish cross confirmed)
  stoch_60 >= 40 and building (macro gate cleared)

CONFIRMING (not required — increases confidence):
  TDI fast line bounced from lower Bollinger Band
  TDI MA sloping upward (sustained bias, not a spike)
  stoch_9 and stoch_40 recovering SEQUENTIALLY (cascade — NOT simultaneous pile-in)
  BBWP 20-40% at entry

STOP LOSS:
  Recent swing low
```

---

## Hold Conditions

### SHORT hold

```
  stoch_60 K < D and declining
  Price below gold cloud
  BBWP expanding (10% -> 30% -> 50%)
  Shorter stochs (9, 40) in sequential decline
```

### LONG hold

```
  stoch_60 K > D and rising
  Price above blue cloud
  Cloud 2 remains blue
  Shorter stochs cascading up sequentially
```

---

## Exit Conditions

### Primary exit (either condition fires)

```
SHORT: stoch_60 K reaches oversold zone (<= 25)
LONG:  Price moves well into gold cloud (Cloud 3 midband)
```

### Exhaustion exit (override — immediate)

```
BBWP reaches near 0% (1-2%)  = volatility bled out, move done — exit
BBWP reaches 95-100% (Red Double) = climactic exhaustion — cover immediately
```

### Early exit (thesis invalidated)

```
SHORT: stoch_60 K > D and building positive — cut
LONG:  stoch_60 K < D declining after entry — cut
Cloud 2 flips against position direction
```

---

## Rejection Rules — Do Not Trade

```
NEVER enter long when:
  All stochs simultaneously at extreme low (BBWP 100%)
  This is CLIMACTIC EXHAUSTION — simultaneous pile-in, not a cascade
  Wait for full reset before looking for next long

NEVER enter short when:
  Cloud 2 is thick blue (strong near-term bullish support beneath)
  stoch_60 < 40 but shorter stochs recovering (cascade forming for long)
  Price well below gold cloud with BBWP near 0% (exhaustion already done)
```

---

## Cascade vs Simultaneous Pile-In

This is the core discrimination rule for LONG entries.

```
VALID (cascade):
  stoch_9 exits oversold first
  stoch_40 follows 3-8 bars later
  stoch_60 follows after stoch_40
  Each exits oversold in sequence — cascading recovery

INVALID (simultaneous pile-in = V-bottom = exhaustion):
  All stochs snap from extreme lows simultaneously
  BBWP spikes to 100%
  Cloud color does not change
  This is FOMO-driven climactic reversal — fade it, wait for reset
```

---

## Example Trade — LONG (from live analysis 2026-03-10)

```
Symbol: PIPPINUSDT 5m
Screenshot: C:/Users/User/Pictures/Screenshots/Screenshot 2026-03-10 205239.png
Timeframe visible: 04:00 - 21:30 UTC

Entry trigger:
  stoch_60 K crossed above 25 (exiting oversold) — early morning UTC
  stoch_60 K > D confirmed
  Cloud 2 turned blue (near-term structure bullish)
  Price holding below gold cloud (macro resistance above = defined target)
  BBWP in healthy expansion range at entry

Exit trigger:
  Price moved WELL INTO the gold cloud (Cloud 3 midband)
  Exit rule: "well into gold cloud" = Cloud 3 midband, not just underside touch
  This is the LONG primary exit condition — not stoch_60 reaching opposite extreme

Outcome:
  Move: ~1% from entry to gold cloud midband
  ROI: ~20% at 20x leverage
  Duration: approximately 1 candle cluster (blue spike visible ~05:30-07:00)

Key lesson:
  Gold cloud = defined target for LONG trades
  "Well into cloud" is measurable — Cloud 3 midband, not the underside
  1% on 5m crypto with 20x = 20% ROI — the move does not need to be large
  The gold cloud overhead is BOTH the exit level AND the proof the thesis was correct
  (price reaching macro resistance = maximum thesis fulfillment for the LONG)

Post-exit state (at screenshot time ~20:00-21:30):
  stoch_60 K=31.82, D=36.26 — K < D, declining toward oversold again
  stoch_40 K=26.98, D=25.06 — approaching oversold zone
  BBWP: 45% (blue bar fired) — volatility re-expanding
  Price: back below gold cloud, declining
  Status: WATCH — stoch_60 has not yet crossed above 25 — no entry yet
  Next trigger: stoch_60 K crosses above 25 with K > D confirmation
```

---

## Example Trade — SHORT (from live analysis 2026-03-08)

```
Symbol: PIPPINUSDT 5m
Entry bar: ~09:10 UTC Sunday
Setup:
  stoch_60 K crossing from 89 -> below 80
  stoch_60 K < D
  Cloud 2 delta THIN (weak near-term structure)
  Price near cloud underside
  BBWP in healthy expansion range

Outcome:
  Move: ~2.86% decline over 1h50m
  SL tight at recent swing high (entry AT exhaustion point)
  Exit: stoch_60 reaching opposite extreme

Key lesson:
  Thin cloud delta = structural weakness visible in advance
  Tight SL available because entry is at exact exhaustion bar
  High R:R by construction — not luck
```

---

## Sweep Parameters for Vince

```python
stoch_60_overbought_exit  : 75 to 85   step 5    (default 80)
stoch_60_oversold_exit    : 20 to 30   step 5    (default 25)
stoch_60_macro_gate       : 35 to 50   step 5    (default 40)
cloud_delta_thin_pct      : 0.001 to 0.005       (default 0.002)
bbwp_entry_max            : 30 to 50   step 10   (default 40)
bbwp_exhaustion_exit      : 1 to 5     step 1    (default 2)
cascade_min_bars_between  : 3 to 8     step 1    (default 4)
```

---

## Relationship to V4 Four-Layer Pipeline

S12 is a higher-level strategy that SUBSUMES the V4 four-layer logic:

| V4 Layer | S12 Equivalent |
|----------|----------------|
| Layer 1 — Macro gate (stoch_60 >= 40) | LONG required condition |
| Layer 2 — Channel gate (orderly decline) | Cloud 3 position check |
| Layer 3 — Two-cycle divergence | Sequential cascade confirmation |
| Layer 4 — Cascade gate (stoch_40 >= 30) | stoch_40 recovering (LONG confirming) |

V4 layers are the LONG entry filter. S12 adds the SHORT direction and the stoch_60-primary framing.

---

## Notes

- "Well into gold cloud" for LONG exit = Cloud 3 midband (avg of Cloud 3 upper and lower), not just underside touch — confirmed by 2026-03-10 PIPPINUSDT trade
- TDI MA sloping up sustained for bars = continuation bias (not spike reversal)
- stoch_60 cycle duration on 5m: typically 1h30m to 4h per full cycle
- Tight SL is only achievable when entering AT the exhaustion bar — late entries widen SL unacceptably

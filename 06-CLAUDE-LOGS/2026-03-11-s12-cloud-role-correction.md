# 2026-03-11 — S12 Cloud Role Correction

**Continuation session** from 2026-03-10 strategy research (context restored from summary).

---

## Summary

Corrected cloud role in `02-STRATEGY/S12-MACRO-CYCLE.md`. Cloud was incorrectly framed — first as a leading signal ("wait for cloud to turn blue"), then as an entry filter ("checked at entry bar"). User corrected both:

**Cloud's actual role:** macro context, TP setting, SL movement. **Not entry.**

## Changes Made

### `02-STRATEGY/S12-MACRO-CYCLE.md`

1. **Indicator Stack table** — removed "Trigger or Filter?" column (was wrong framing). Added explicit note: "Cloud does not drive entry. Cloud aids in macro context, TP setting, and SL movement. The entry is fired by stoch_60 and the tier-specific triggers. Cloud is not an entry gate or filter."

2. **Cloud 3 role** — updated to: "Macro structure. Defines TP (Cloud 3 midband = LONG exit target). Informs SL movement."

3. **Cloud 2 role** — updated to: "Near-term structure. Macro context. Informs SL movement. Delta thickness = structural strength."

4. **Cloud Delta Interpretation** — replaced "read at entry bar" language with: "Cloud structure informs macro context (are we in a bullish or bearish regime?), sets TP targets (Cloud 3 midband = LONG exit), and guides SL movement. It does not gate entry."

5. **Entry Conditions / SHORT** — removed from REQUIRED: "Price at or below gold cloud underside" and "Cloud 2 delta is THIN". Entry now: stoch_60 cross + K < D only.

6. **Entry Conditions / LONG** — removed from REQUIRED: "Cloud 2 is BLUE at entry bar" and "Price at or above blue cloud at entry bar". Entry now: stoch_60 cross + K > D + macro gate only.

## Key Correction Chain

```
Version 1 (old perspective): cloud turns blue -> watch for stoch_60 cross -> enter
  WRONG — cloud is not a leading signal

Version 2 (my first fix): stoch_60 crosses -> check cloud at entry bar -> if valid, enter
  WRONG — cloud is not an entry filter either

Version 3 (correct): stoch_60 crosses -> enter. Cloud informs macro context, TP, and SL management.
  CORRECT — cloud has nothing to do with entry
```

## Files Modified

- `02-STRATEGY/S12-MACRO-CYCLE.md` — 6 edits (indicator stack, cloud delta, SHORT entry, LONG entry)

## No Code Built

Strategy document corrections only. Vince build remains parked.

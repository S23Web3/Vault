# Session Log — 2026-02-23 — Four Pillars Strategy Scoping

**Date:** 2026-02-23
**Session type:** Strategy scoping — no code written
**Status:** IN PROGRESS — scoping not complete

---

## What Was Done

### Files Created
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\PROJECT-BUILD-PLAN-v2.md` — two-track build plan (Track A: Cloud 3 fix + BingX demo, Track B: VINCE)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-QUANT-SPEC-v1.md` — quantitative spec, in progress, 19 unknowns remaining
- `C:\Users\User\Documents\Obsidian Vault\skills\chart-reading-skill.md` — chart reading rules and output format

### Files Referenced
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\VERSION-MASTER.md`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-20-vince-scope.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\indicators\supporting\ripster_ema_clouds_v6.pine`
- `C:\Users\User\Documents\Obsidian Vault\Books\John-Kurisko-Trading-Template_Desire_to_Trade.pdf`

---

## Strategy Understanding — Current State

### Ground Rules Established
- BBW/BBWP and Ripster EMA Clouds are NOT entry or exit triggers — lagging, context only
- No hard lines on stochastic zones — 20/80 are reference points, effective zone depends on divergence, other stochastics, context
- Stochastic zones are flexible in both directions: oversold could be 20, 25, or 30. Overbought could be 80, 75, or 70
- Cloud 3 = EMA 34/50 — confirmed from ripster_ema_clouds_v6.pine
- Rotation window = 5 candles working value, Vince to optimise

### Signal Type 1 — Quad Rotation
**Long:** K1 exits oversold zone (flexible — could be 20/25/30 depending on context including divergence and other stochastics). Keeps climbing — continuation is the signal not the level. K2 follows, K3 follows. Entry possible at K1, K2, or K3 — trader's choice on risk vs confirmation.

**Short:** K1 exits overbought zone (flexible — could be 80/75/70 depending on context). Keeps dropping — continuation is the signal not the level. K2 follows, K3 follows. Entry possible at K1, K2, or K3.

State tracker — not one per candle. Volatile candles can move multiple stochastics. Slow candles move none. State holds.

### K4 K/D Cross — Late Entry / Add-On (NOT primary entry)
K4 K crossing K4 D = late runner / add-on confirmation, not the primary signal.
- Long add-on: K4 K crosses above K4 D, D sloping upward = stay in
- Short add-on: K4 K crosses below K4 D, D sloping downward = stay in
This was mistakenly described as the primary entry confirmation — it is not.

### Signal Type 2 — Add-On / Late Runner
K3 and K4 holding above 50 (long) or below 50 (short). K1 and K2 pulling back and re-exiting their zone. Very tight stop — goes or it doesn't.

### Signal Type 3 — Divergence
Price and K1 moving opposite directions at pivot points. Bullish: price lower low, K1 higher low. Bearish: price higher high, K1 lower high. Aids the K1 perspective, signals other stochastics likely to follow. Not standalone.

### Trade Legs
1. Entry (Signal Types 1, 2, 3)
2. Risk management (Cloud, BBWP, ATR as context — not triggers)
3. Trailing (with-trend only — AVWAP or ATR)
4. Closing (with-trend: trail. Counter-trend: fixed target before EMA 50)

### Cloud 3 Role
Post-entry health indicator only. Not an entry gate. Bearish Cloud 3 on a long = flag, not close. Persistent bearish = tighten, candle threshold unknown.

### POPCAT Chart Reading
At red dashed line: K1 and K2 deep oversold turning up. K3 just exiting. K4 K=25 below D=41 — not confirmed yet. 2 candles later K4 K crossed K4 D = late confirmation / add-on territory. ATR=0.00005, 2 ATR stop was essentially free. 40% move on 20x.

---

## Errors Made This Session — For Reference

1. Called all 4 stochastics oversold in RENDERUSDT chart — only K1 and K2 were. K3 and K4 were above 50.
2. Said BBWP red zone active based on color — numbers showed 55%/57.20% which is mid range.
3. Called K4 K/D cross the primary entry confirmation — it is the add-on/late runner signal.
4. Imposed hard lines (20, 80) multiple times after being corrected — no hard lines, zones are flexible.
5. Wrote "short is mirror of long" instead of writing it out fully.
6. Moved too fast into architecture and code planning without completing the scoping.

---

## Open Items — Spec Unknowns (19 remaining)

| # | Item | Owner |
|---|------|-------|
| 2 | Rotation window — 5c working value | Vince |
| 3 | K above D — all 4 or K1 only? | Malik |
| 4 | BBWP zone thresholds | BBW pipeline + Vince |
| 5 | Add-on stop size | Malik |
| 6 | Divergence pivot lookback window | Malik |
| 7 | Divergence entry trigger candle | Malik |
| 8 | K above/below D on divergence | Malik |
| 9 | Break even trigger — ATR multiple | Malik |
| 10 | Trail distance | Malik |
| 11 | Cloud 3 persistent bearish candle threshold | Malik |
| 12 | Counter-trend SL | Malik |
| 13 | K1 re-enters extreme zone — close/tighten/hold? | Malik |
| 14 | Max concurrent positions demo | Malik |
| 15 | Skip or queue on max positions | Malik |
| 16 | Leverage for demo | Malik |
| 17 | Min 24h volume coin selection | Malik |
| 18 | Max watchlist size | Malik |
| 19 | AVWAP anchor rule | Malik |
| 20 | Add-on sizing — $50 same or reduced? | Malik |

---

## Next Session Pick-Up

1. Read this log first
2. Read `FOUR-PILLARS-QUANT-SPEC-v1.md` — do not assume it is complete
3. Scoping is NOT done — do not move to build planning or code
4. Work through open items one at a time, at Malik's pace
5. Ask, do not assume. Present options, do not push
6. No hard lines on stochastic zones — ever
7. BBW and Cloud are context only — never entry/exit conditions
8. Short entries must always be written out fully, never "mirror of long"

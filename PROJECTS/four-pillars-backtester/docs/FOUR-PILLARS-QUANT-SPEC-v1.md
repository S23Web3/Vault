# Four Pillars — Quantitative Spec

> **Status:** DRAFT · Created 2026-02-23
> **Purpose:** Buildable numbers for the Four Pillars strategy
> **Unknowns:** Flagged with `[?]` — see bottom of doc

---

## Ground Rules

> BBW/BBWP and Ripster EMA Clouds are **NOT** entry or exit triggers.
> They are lagging context indicators used only in risk management and closing legs.
> Stochastic zones are flexible — hard boundary is 20/80, effective boundary can extend to 25–30 / 70–75 depending on what the other stochastics are doing.

---

## Indicators

| Indicator | Parameters | Used In |
|-----------|-----------|---------|
| K1 Stochastic | 9, 1, 3 | Entry |
| K2 Stochastic | 14, 1, 3 | Entry |
| K3 Stochastic | 40, 1, 3 | Entry |
| K4 Stochastic | 60, 1, 10 | Entry |
| ATR | 14, RMA | Stop sizing |
| Ripster EMA Cloud | 8/9 · 5/12 · 34/50 · 72/89 · 180/200 · hl2 | Post-entry context |
| Cloud 3 | EMA 34 / EMA 50 | Post-entry health |
| BBWP | close · SMA 21 · 100 · spectrum | Post-entry context |
| AVWAP | Trade-anchored · HLC3 · base volume · σ floor = 0.5×ATR | Trailing SL after checkpoint |

---

## Zone Reference

### Stochastics

| | Long | Short |
|-|------|-------|
| Hard boundary | K < 20 = oversold | K > 80 = overbought |
| Effective boundary | Can extend to 25–30 | Can extend to 70–75 |
| Momentum confirmation | K above D | K below D |

### BBWP

| Zone | Percentile | Meaning |
|------|-----------|---------|
| Compression | `[?]` | Market coiling — context only |
| Neutral | `[?]` | Grinding / botted — context only |
| Expansion | `[?]` | Volatility expanding — context only |

> Thresholds to be defined by BBW pipeline output. Ideal values come from Vince.
> Extreme zones can persist many candles — do not force entries or exits based on BBWP alone.

### Ripster EMA Cloud

| Price vs Cloud 3 (34/50) | Meaning |
|--------------------------|---------|
| Above | Bull structure |
| Inside | Transition — caution |
| Below | Bear structure |

| Cloud 3 State | Meaning |
|---------------|---------|
| EMA 34 > EMA 50 (bullish) | Trend aligned with long |
| EMA 34 < EMA 50 (bearish) | Trend not aligned — health flag |

---

## Entry: Signal Type 1 — Full Quad Rotation

> The four stochastics exit their extreme zones in reading order: K1 → K2 → K3 → K4 (fast to slow).
> This is a state tracker — not one-per-candle. Volatile candles can move multiple stochastics simultaneously. Slow candles may move none. State holds until window expires.

**Window to complete full rotation: 5 candles from K1 exit** *(working value — Vince to optimise)*

> The rotation is NOT confirmed at K1 exit. It is confirmed when K4 K crosses K4 D.
> Until K4 K crosses K4 D, the position is in evaluation — not yet a full quad rotation.
> K4 K line = stay-in tracker. K4 D line = get-out tracker.

### Long Entry

| Condition | Value |
|-----------|-------|
| K1 exits oversold | K1 K crosses above 20 (hard boundary) — effective boundary 25–30 depending on K2/K3/K4 context |
| K2 exits oversold | K2 K crosses above 20 — must follow K1, not precede it |
| K3 exits oversold | K3 K crosses above 20 — must follow K2 |
| K4 K crosses K4 D | K4 K line crosses above K4 D line — this is full rotation confirmation |
| K4 D slope | K4 D must begin sloping upward within 5 candles of K1 exit — if D stays flat or declines, rotation is failing |
| Stay-in condition | K4 K remains above K4 D and K4 D continues sloping up |
| Get-out warning | K4 D stops sloping up or K4 K falls back below K4 D |
| BBWP | Not a condition |
| Cloud state | Not a condition |

### Short Entry

| Condition | Value |
|-----------|-------|
| K1 exits overbought | K1 K crosses below 80 (hard boundary) — effective boundary 70–75 depending on K2/K3/K4 context |
| K2 exits overbought | K2 K crosses below 80 — must follow K1, not precede it |
| K3 exits overbought | K3 K crosses below 80 — must follow K2 |
| K4 K crosses K4 D | K4 K line crosses below K4 D line — this is full rotation confirmation |
| K4 D slope | K4 D must begin sloping downward within 5 candles of K1 exit — if D stays flat or rises, rotation is failing |
| Stay-in condition | K4 K remains below K4 D and K4 D continues sloping down |
| Get-out warning | K4 D stops sloping down or K4 K rises back above K4 D |
| BBWP | Not a condition |
| Cloud state | Not a condition |

---

## Entry: Signal Type 2 — Add-On / Late Runner

> K3 and K4 are still holding above 50 (long) or below 50 (short).
> K1 and K2 pull back into their extreme zone and exit again.
> Very tight stop — the trade goes or it doesn't. No holding through a reversal.

### Long Add-On

| Condition | Value |
|-----------|-------|
| K3 | > 50 — holding bull territory |
| K4 | > 50 — holding bull territory |
| K1 exits oversold | K crosses above 20 |
| K2 exits oversold | K crosses above 20 — follows K1 |
| K above D | Required on K1 and K2 |
| Stop size | `[?]` |
| BBWP / Cloud | Not a condition — context only |

### Short Add-On

| Condition | Value |
|-----------|-------|
| K3 | < 50 — holding bear territory |
| K4 | < 50 — holding bear territory |
| K1 exits overbought | K crosses below 80 |
| K2 exits overbought | K crosses below 80 — follows K1 |
| K below D | Required on K1 and K2 |
| Stop size | `[?]` |
| BBWP / Cloud | Not a condition — context only |

---

## Entry: Signal Type 3 — Divergence (K1)

> Divergence aids the K1 perspective. Momentum changes direction before price does.
> Bullish: price makes lower low, K1 makes higher low — engine reigniting.
> Bearish: price makes higher high, K1 makes lower high — running out of fuel.
> Signals that the remaining stochastics are likely to follow.

### Bullish Divergence — Long

| Condition | Value |
|-----------|-------|
| Price pivot | Lower low on price |
| K1 pivot | Higher low on K1 at same point |
| Lookback window | `[?]` candles |
| Entry trigger | `[?]` on detection candle close, or next open? |
| K above D on K1 | `[?]` required? |
| BBWP / Cloud | Not a condition — context only |

### Bearish Divergence — Short

| Condition | Value |
|-----------|-------|
| Price pivot | Higher high on price |
| K1 pivot | Lower high on K1 at same point |
| Lookback window | `[?]` candles |
| Entry trigger | `[?]` on detection candle close, or next open? |
| K below D on K1 | `[?]` required? |
| BBWP / Cloud | Not a condition — context only |

---

## Stop Loss

| Trade Type | Rule | Size |
|------------|------|------|
| Full quad rotation | ATR based | 2 × ATR(14) |
| Add-on / late runner | Very tight | `[?]` |
| Divergence | `[?]` | `[?]` |
| Counter-trend | `[?]` | `[?]` |

---

## Trade Classification

| Entry Condition | Classification |
|-----------------|---------------|
| Long · price above Cloud 3 | With-trend |
| Short · price below Cloud 3 | With-trend |
| Long · price below Cloud 3 | Counter-trend |
| Short · price above Cloud 3 | Counter-trend |
| Long · price inside Cloud 3 | Transition — caution |
| Short · price inside Cloud 3 | Transition — caution |

---

## Trade Management

### Leg 1 — Entry
See Signal Types 1, 2, 3 above.

---

### Leg 2 — Risk Management

*Context inputs active here: Cloud 3 state, BBWP, ATR, price vs EMA levels*

| Condition | Action |
|-----------|--------|
| Price moves `[?]` ATR in favour | Move SL to break even |
| Cloud 3 bearish on long | Flag only — does NOT close trade |
| Cloud 3 persistently bearish on long | Tighten stop after `[?]` candles |
| BBWP entering high expansion | Trade has room — context |
| BBWP contracting from high | Energy fading — context |

---

### Leg 3 — Trailing (with-trend only)

| Parameter | Value |
|-----------|-------|
| Trail method | AVWAP or ATR trail |
| Trail distance | `[?]` |
| Hard TP | None — let it run |

---

### Leg 4 — Closing

**With-trend:**

| Condition | Action |
|-----------|--------|
| Trail hit | Close |
| K1 re-enters extreme zone | `[?]` close / tighten / hold? |
| BBWP contracting sharply | Consider tightening trail |

**Counter-trend:**

| Condition | Action |
|-----------|--------|
| Price approaching EMA 50 | Close before reaching — not at |
| Price approaching Cloud 3 | Close |
| Trail | None — fixed target only |

---

## AVWAP Trailing Rule (Current — v3.8.4)

> Anchor: entry bar. Computed from HLC3 and base volume. Sigma floor = 0.5 × ATR(14).

| Phase | Trigger | SL Behaviour |
|-------|---------|-------------|
| Initial | Bars 0 to checkpoint (default 5) | Fixed ATR stop: entry ± 2 × ATR |
| AVWAP | After checkpoint interval | SL ratchets to AVWAP center — never moves against trade |
| Break-even | Price hits entry ± be_trigger_atr × ATR | SL immediately jumps to entry ± be_lock_atr × ATR — fires before AVWAP ratchet |
| Scale-out | At each checkpoint, close hits AVWAP ±2σ | Close half — max 2 scale-outs |

**ADD / RE-entry slots:** Inherit parent slot AVWAP state via clone — they continue the same cumulative VWAP, not a fresh anchor.

---

## Position Sizing — BingX Demo

| Parameter | Value |
|-----------|-------|
| Size per trade | $50 USDT fixed |
| Leverage | `[?]` |
| Max concurrent positions | `[?]` |
| If max positions reached | `[?]` skip or queue? |
| Add-on sizing | `[?]` same $50 or reduced? |

---

## Coin Selection — BingX Demo

| Filter | Value |
|--------|-------|
| Exchange | BingX USDT perpetuals |
| Min 24h volume | `[?]` |
| Tier preference | Tier A from coin_tiers.csv first |
| Max watchlist size | `[?]` |
| Refresh | Daily at session start |

---

## Open Items

| # | Item | Owner |
|---|------|-------|
| ~~1~~ | ~~Cloud 3 EMA pair~~ | ✅ EMA 34/50 |
| 2 | Rotation window — 5c working value, validate | Vince |
| 3 | K above D — all 4 required, or K1 only? | Malik |
| 4 | BBWP zone thresholds | BBW pipeline + Vince |
| 5 | Add-on stop size | Malik |
| 6 | Divergence pivot lookback window | Malik |
| 7 | Divergence entry trigger — close or next open? | Malik |
| 8 | K above/below D on divergence entries | Malik |
| 9 | Break even trigger — ATR multiple | Malik |
| 10 | Trail distance | Malik |
| 11 | Cloud 3 persistent bearish — candle threshold | Malik |
| 12 | Counter-trend SL | Malik |
| 13 | K1 re-enters extreme zone — close / tighten / hold? | Malik |
| 14 | Max concurrent positions | Malik |
| 15 | Skip or queue on max positions | Malik |
| 16 | Leverage for demo | Malik |
| 17 | Min 24h volume for coin selection | Malik |
| 18 | Max watchlist size | Malik |
| ~~19~~ | ~~AVWAP anchor rule~~ | ✅ Resolved — see AVWAP section |
| 20 | Add-on sizing — $50 same or reduced? | Malik |

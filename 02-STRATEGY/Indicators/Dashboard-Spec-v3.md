# Trade Dashboard Framework Specification v3.0

**Build Order:** Last (after core indicators)  
**Purpose:** Visual checklist for trade entry grading + automation

---

## Layout

```
┌──────────────────────┐
│  A   4/4    LONG     │  Grade + Score + Direction
├──────────────────────┤
│ Target     6 ATR     │
├──────────────────────┤
│ BBWP    Blue ✓  GATE │  ← Must pass
├──────────────────────┤
│ Momentum    ▲        │  ← Scored
│ TDI         ▲        │  ← Scored
│ Ripster     ▲        │  ← Scored
│ AVWAP     Above      │  ← Scored
├──────────────────────┤
│ ATR      0.000070    │
│ Stop     0.000140    │
└──────────────────────┘

┌──────────────────────┐
│ POST                 │  ← Toggle after entry
├──────────────────────┤
│ Continuation Building│
│ ATR          Rising  │
│ 5m Trail     Active  │
└──────────────────────┘
```

---

## Grade Logic

| Grade | Score | Direction | Automated | Target |
|-------|-------|-----------|-----------|--------|
| A | 4/4 | LONG/SHORT | Yes | 6 ATR |
| B | 3/4 | LONG/SHORT | Yes | 4 ATR |
| — | <3 | WAIT | No | — |

**No C-grade.** Below 3/4 = no trade.

---

## Gate (BBWP)

Must pass before grade calculated.

| State | Condition | Trade Allowed |
|-------|-----------|---------------|
| Blue | Squeeze (low percentile) | Yes |
| Red | Extended (high percentile) | Yes |
| Other | No volatility edge | No → Grade = "—" |

---

## Scored Conditions (4 Total)

### 1. Momentum (Stochastics Combined)

**Settings:**
- Stoch 55: K=55, D=1, Smooth=12
- Stoch 9: K=9, D=1, Smooth=3

**Long Aligned (+1):**
- Stoch 55 in zone <25 OR K crossed above D (within N bars)
- AND Stoch 9 K rising
- OR Bullish divergence (price LL/equal low + stoch HL from <20)

**Short Aligned (+1):**
- Stoch 55 in zone >75 OR K crossed below D (within N bars)
- AND Stoch 9 K falling
- OR Bearish divergence (price HH/equal high + stoch LH from >80)

**Cross Threshold (Stoch 9):**
- Long: Stoch 9 crosses while K ≤ 20
- Short: Stoch 9 crosses while K ≥ 80

---

### 2. TDI

**Long (+1):** RSI > Signal line  
**Short (+1):** RSI < Signal line

---

### 3. Ripster

Checks both 34/50 (trend) and 5/12 (entry confirmation).

**Long (+1):**
- Price above 34/50 cloud
- 34/50 cloud rising
- 5/12 bullish (EMA5 > EMA12)

**Short (+1):**
- Price below 34/50 cloud
- 34/50 cloud falling
- 5/12 bearish (EMA5 < EMA12)

---

### 4. AVWAP

**Long (+1):** Price above anchored VWAP  
**Short (+1):** Price below anchored VWAP

**STUB:** Currently using session VWAP. Replace with proper anchor logic.

---

## Post-Entry Panel

| Condition | Good | Bad |
|-----------|------|-----|
| Continuation | Building (Stoch 55 trending with trade) | Declining (reversing) |
| ATR | Rising | Flat/Falling |
| 5m Trail | Active | Triggered → EXIT |

---

## Stubs Remaining

| Module | Status | Blocks Automation |
|--------|--------|-------------------|
| BBWP | Stub | No (gate logic works) |
| Divergence | Stub | No (optional strengthener) |
| AVWAP | Stub (session VWAP) | Yes - needs anchor |
| 5m Trail | Stub | Yes - needs HTF logic |

**Automation blocker:** Stoch 55 K/D cross detection (main trigger) - implemented.

---

## Module Signatures

```pinescript
// Gate
get_bbwp_state() => "blue" | "red" | "other"

// Scored
get_momentum_state() => 1 | -1 | 0
get_tdi_state() => 1 | -1 | 0
get_ripster_state() => 1 | -1 | 0
get_avwap_state() => 1 | -1 | 0

// Post-entry
get_continuation_state() => 1 | -1 | 0
get_atr_state() => 1 | -1 | 0
get_5m_trail_state() => 1 | -1
```

---

## Alerts

| Alert | Condition |
|-------|-----------|
| A-Grade Long | grade == "A" and direction == "LONG" |
| A-Grade Short | grade == "A" and direction == "SHORT" |
| B-Grade Long | grade == "B" and direction == "LONG" |
| B-Grade Short | grade == "B" and direction == "SHORT" |
| Trail Exit | trail_state == -1 |
| Continuation Fail | continuation_state == -1 and in trade |

---

## Files

- `Dashboard-Framework-v3.pine` - Pine Script framework
- `Dashboard-Spec-v3.md` - This document

---

#indicator #dashboard #four-pillars #automation

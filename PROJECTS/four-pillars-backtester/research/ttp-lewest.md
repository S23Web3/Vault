# Trailing Take Profit (TTP) — Logic Specification

**Project:** Four Pillars Backtester  
**Author:** Malik  
**Date:** 2026-03-03  
**Status:** Decisions Locked — Ready to Build

---

## Overview

A Trailing Take Profit (TTP) is an exit mechanism with two distinct phases:

1. **Activation phase** — price must move a minimum distance from entry before trailing begins
2. **Trailing phase** — once active, a dynamic exit level trails the extreme price at a fixed distance

The trade closes when price reverses back to the trailing level.

---

## Parameters

| Parameter | Symbol | Value |
|---|---|---|
| Activation threshold | `ACT` | 0.5% |
| Trail distance | `DIST` | 0.2% |

---

## UML — State Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TTP STATE MACHINE                        │
└─────────────────────────────────────────────────────────────────┘

       [TRADE OPENS]
            │
            ▼
    ┌───────────────┐
    │   MONITORING  │  ◄──── Watching price from entry
    └───────────────┘
            │
            │  LONG:  price >= entry × (1 + 0.005)
            │  SHORT: price <= entry × (1 - 0.005)
            │
            ▼
    ┌───────────────┐
    │   ACTIVATED   │  ◄──── TTP is now live
    └───────────────┘
            │
            │  Per 1m candle:
            │    LONG:  if candle_high > highest_price → update highest_price
            │           trail_level = highest_price × (1 - 0.002)
            │
            │    SHORT: if candle_low < lowest_price  → update lowest_price
            │           trail_level = lowest_price × (1 + 0.002)
            │
            ▼
    ┌───────────────┐
    │   TRAILING    │  ◄──── trail_level moves with new extremes only
    └───────────────┘
            │
            │  PESSIMISTIC: check reversal BEFORE updating extreme
            │  OPTIMISTIC:  update extreme BEFORE checking reversal
            │
            ▼
    ┌───────────────┐
    │    CLOSED     │  ◄──── both scenarios output independently
    └───────────────┘
```

---

## UML — Sequence Diagram (Short Example)

```
Actor       1m Candle Feed      TTP Engine              Position
  │               │                  │                     │
  │   candle 1    │                  │                     │
  │   0%          │  entry=0%        │                     │
  │──────────────►│─────────────────►│  state=MONITORING   │
  │               │                  │                     │
  │   candle 2    │                  │                     │
  │   L: -0.3%    │  below ACT       │                     │
  │──────────────►│─────────────────►│  still MONITORING   │
  │               │                  │                     │
  │   candle 3    │                  │                     │  ← ACT reached
  │   L: -0.5%    │  entry×(1-0.005) │                     │
  │──────────────►│─────────────────►│  state=ACTIVATED    │
  │               │                  │  lowest = -0.5%     │
  │               │                  │  trail  = -0.3%     │
  │               │                  │                     │
  │   candle 4    │                  │                     │  ← new low
  │   L: -0.8%    │                  │                     │
  │──────────────►│─────────────────►│  lowest = -0.8%     │
  │               │                  │  trail  = -0.6%     │
  │               │                  │                     │
  │   candle 5    │                  │                     │  ← new low
  │   L: -1.1%    │                  │                     │
  │──────────────►│─────────────────►│  lowest = -1.1%     │
  │               │                  │  trail  = -0.9%     │
  │               │                  │                     │
  │   candle 6    │                  │                     │  ← reversal
  │   H: -0.9%    │  price = trail   │                     │
  │──────────────►│─────────────────►│  CLOSE SHORT        │
  │               │                  │────────────────────►│  EXIT at -0.9%
```

---

## Logic Rules (Formal)

### LONG

```
activation_price = entry × (1 + ACT)           # entry × 1.005

IF candle_high >= activation_price:
    state = ACTIVATED
    highest_price = current_price               # on 5m crypto, no gap assumed

WHILE state == ACTIVATED:

    # PESSIMISTIC — check exit before updating extreme
    IF candle_low <= trail_level:
        CLOSE LONG (pessimistic)
    ELSE IF candle_high > highest_price:
        highest_price = candle_high
        trail_level = highest_price × (1 - DIST)

    # OPTIMISTIC — update extreme before checking exit
    IF candle_high > highest_price:
        highest_price = candle_high
        trail_level = highest_price × (1 - DIST)
    IF candle_low <= trail_level:
        CLOSE LONG (optimistic)
```

### SHORT

```
activation_price = entry × (1 - ACT)           # entry × 0.995

IF candle_low <= activation_price:
    state = ACTIVATED
    lowest_price = current_price                # on 5m crypto, no gap assumed

WHILE state == ACTIVATED:

    # PESSIMISTIC — check exit before updating extreme
    IF candle_high >= trail_level:
        CLOSE SHORT (pessimistic)
    ELSE IF candle_low < lowest_price:
        lowest_price = candle_low
        trail_level = lowest_price × (1 + DIST)

    # OPTIMISTIC — update extreme before checking exit
    IF candle_low < lowest_price:
        lowest_price = candle_low
        trail_level = lowest_price × (1 + DIST)
    IF candle_high >= trail_level:
        CLOSE SHORT (optimistic)
```

---

## Percentage Walk-Through (Short)

| Candle | % from Entry | Event | lowest_price | trail_level |
|--------|-------------|-------|-------------|-------------|
| 1 | 0% | Entry | — | — |
| 2 | L: -0.3% | Below ACT | — | — |
| 3 | L: -0.5% | **TTP ACTIVATED** | -0.5% | -0.5% + 0.2% = **-0.3%** |
| 4 | L: -0.8% | New low | -0.8% | -0.8% + 0.2% = **-0.6%** |
| 5 | L: -1.1% | New low | -1.1% | -1.1% + 0.2% = **-0.9%** |
| 6 | H: -0.9% | Reversal — hits trail | — | **CLOSE at -0.9%** |

Net result: **+0.9% profit** on short

---

## Decisions Locked

| # | Nuance | Decision | Rationale |
|---|---|---|---|
| 1 | Gap at activation | `lowest_price = current_price` | 5m crypto, 24/7 market, momentum entry — gaps are an extreme edge case, not the norm |
| 2 | Trail granularity | One update per 1m candle using candle Low (short) / High (long) | No tick data available. 1m OHLC is the finest resolution. One update per candle is deterministic and honest |
| 3 | OHLC ambiguity | Run both Pessimistic and Optimistic in parallel | GPU parallel execution on RTX 3060. Band between results = strategy robustness metric. No single assumption forced |

---

## Dual Scenario Output — What to Expect

Both scenarios run simultaneously on the same 1m OHLC dataset using GPU parallel computation.

| Metric | Pessimistic | Optimistic |
|---|---|---|
| Intra-candle order | High first → Low second (short) | Low first → High second (short) |
| Effect | Earlier exits, less profit captured | Later exits, more profit captured |
| Represents | Performance floor | Performance ceiling |
| Band width | Narrow = strategy robust | Wide = path-dependent, needs review |

Output per trade includes both exit prices and both profit figures side by side.

---

## Research Validation

**Source:** Bybit Trailing Stop documentation, GoodCrypto, TradeSanta, ForexOp, QuantifiedStrategies

### ✅ Confirmed correct:
- Two-phase structure (activation gate → trailing) matches industry standard
- Trail only moves in the favorable direction
- Trail distance calculated from most extreme price since activation
- SHORT formula: `trail = lowest × (1 + DIST)` — matches Bybit exactly

---

## Build Scope

- [ ] Python module: `ttp_engine.py`
- [ ] Inputs: 1m OHLC DataFrame, entry price, direction (long/short), ACT, DIST
- [ ] Two parallel passes: pessimistic and optimistic
- [ ] Output per trade: exit candle, exit price %, profit pess, profit opt, band width
- [ ] GPU acceleration: CUDA via CuPy or PyTorch tensor ops on RTX 3060
- [ ] Unit tests: long and short with known candle sequences, verify both outputs

---

## Tags

`#ttp` `#trailing-take-profit` `#exit-logic` `#four-pillars` `#build-ready` `#research`

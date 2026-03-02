# Four Pillars Strategy — v3.8.6

**Version:** 3.8.6
**Date locked:** 2026-02-28
**Signal file:** `signals/four_pillars_v386.py`
**State machine:** `signals/state_machine.py` (unchanged from v3.8.4)
**Live bot:** BingX connector, `config.yaml` as of 2026-02-28

---

## Strategy Summary

Four Pillars is a multi-timeframe stochastic momentum strategy.
Entries are classified A/B by signal quality (C disabled in v3.8.6).
v3.8.6 adds a Stage 2 conviction filter that eliminates low-quality setups
while preserving the trade volume needed for exchange rebate farming.

Economic model: earn rebates on volume (~34% of gross commission returned),
deploy only when macro and micro momentum align.

---

## Indicators

### Stochastics (John Kurisko Raw K — smooth=1)

| Name | Period | Role |
|------|--------|------|
| Stoch9 | 9-3 | Entry trigger |
| Stoch14 | 14-3 | Setup confirmation |
| Stoch40 | 40-3 | Swing momentum |
| Stoch60 | 60-10 | Macro momentum |

### Ripster EMA Clouds

| Cloud | EMAs | Role |
|-------|------|------|
| Cloud2 | 5/12 | Re-entry trigger |
| Cloud3 | 34/50 | Directional filter (primary) |
| Cloud4 | 72/89 | Swing filter |
| Cloud5 | 180/200 | Macro filter |

### ATR
- Period: 14 (Wilder RMA)
- Used for: SL sizing, trailing stop activation, min_atr_ratio filter

---

## Entry Logic

### Stage 1 — Setup Detection

- LONG: Stoch9 drops BELOW 25 (cross_level)
- SHORT: Stoch9 rises ABOVE 75 (100 - cross_level)
- Lookback window: 10 bars (stage_lookback)

During Stage 1, track:
- Did Stoch14 enter zone (below 30 for LONG, above 70 for SHORT)?
- Did Stoch40 enter zone?
- Did Stoch60 enter zone?
- Did Stoch40/60 rotate through 20 (LONG) or 80 (SHORT)?
- Was price at/near Cloud3 within last 5 bars?

### Stage 2 — Conviction Filter (v3.8.6 — MANDATORY)

Grade A only fires if ALL of:
1. Stoch40 rotated through 20 (LONG) or 80 (SHORT) during Stage 1
2. Stoch60 rotated through 20 (LONG) or 80 (SHORT) during Stage 1
3. Price was at/above Cloud3 (LONG) or at/below Cloud3 (SHORT) within last 5 bars

Without Stage 2: ~93 trades/day on 47 coins.
With Stage 2: ~40 trades/day on 47 coins. Higher conviction per trade.

### Signal Grades

| Grade | Condition | Stage 2 required | v3.8.6 enabled |
|-------|-----------|-----------------|----------------|
| A | Stoch14 + Stoch40 + Stoch60 all in zone AND Cloud3 ok | YES | YES |
| B | Any 2 of (Stoch14, Stoch40, Stoch60) in zone AND Cloud3 ok | NO | YES |
| C | Stoch14 in zone AND price inside Cloud3 | NO | NO (disabled) |

Grade A blocked by Stage 2 does NOT fall back to Grade B.

---

## Risk Parameters (Live — 2026-02-28)

| Parameter | Value |
|-----------|-------|
| Margin per trade | $5 USDT isolated |
| Leverage | 10x ($50 notional) |
| SL | 2.0x ATR (mark price) |
| Fixed TP | None |
| Trailing activation | 2.0x ATR from entry |
| Trailing callback | 2% from peak |
| Max open positions | 8 |
| Max daily trades | 50 |
| Daily loss limit | $15 |
| Cooldown | 3 bars per symbol+direction |
| Min ATR ratio | 0.003 |

---

## Coin Selection (v3.8.6 — 47 coins)

Filter applied before adding to active list:
- Trades >= 400 (statistical significance)
- Profit Factor >= 1.03
- Max Drawdown <= 30%
- Expectancy > 0

14 high-Expectancy originals + 33 low-drawdown additions.
Full list: `PROJECTS/bingx-connector/config.yaml`

---

## Differences from v3.8.4

| Aspect | v3.8.4 | v3.8.6 |
|--------|--------|--------|
| Stage 2 filter | Off (require_stage2=False) | On (require_stage2=True) |
| C-grade | Enabled (allow_c=True) | Disabled (allow_c=False) |
| Fixed TP | Optional | None — trailing only |
| Trade frequency | ~93/day | ~40/day (47 coins) |
| State machine | state_machine.py | state_machine.py (unchanged) |

---

## What v3.8.6 Does NOT Change

- Stochastic periods (9, 14, 40, 60)
- Cloud EMAs (5/12, 34/50, 72/89, 180/200)
- ATR calculation (Wilder RMA, period 14)
- Stage 1 setup detection logic
- Grade B firing conditions
- Re-entry logic (Cloud2 crossover)
- cross_level (25), zone_level (30), rot_level (80)

---

## Signal File Usage

```python
from signals.four_pillars_v386 import compute_signals

# v386 defaults (require_stage2=True, allow_c=False):
df = compute_signals(ohlcv_df)

# Override to replicate v384 behavior for comparison:
df = compute_signals(ohlcv_df, params={"require_stage2": False, "allow_c_trades": True})
```

---

## Vince Plugin

`FourPillarsPlugin` (Vince B1) wraps `signals/four_pillars_v386.py`.
All access goes through `vince/api.py` — pages never call compute_signals directly.
Plugin interface: `strategies/base_v2.py` (StrategyPlugin ABC).

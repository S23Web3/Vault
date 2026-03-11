# Strategy v4 Research Session — 2026-03-10

## Session Type
Research and critical review. No code written. Output = analysis plan.

## Files Produced
- Plan (primary): `C:\Users\User\.claude\plans\rosy-forging-hopper.md`
- Plan (vault copy): `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-10-strategy-v4-research-plan.md`

## What Was Confirmed Built

- 12 SL lifecycle scenario PNGs confirmed present (`results/sl_lifecycle/scenario_01-12.png`) — user ran `visualize_sl_lifecycle_v2.py`
- Strategy catalogue S1-S11 visualizers written and py_compile PASS — run status unknown
- `STRATEGY-V4-DESIGN.md` exists but backtest results table is blank

## Key Findings

### S1-S11 Alignment Scores vs Core Perspective
Core perspective = (A) stoch_9 overzone exit + (B) other stochastics follow/cascade + (C) prior divergence OR regression channel

| Strategy | Score | Key issue |
|----------|-------|-----------|
| S1 (Bible) | 75% | Best — has A+B+C but divergence is implied not required |
| S7 (Quad Rotation) | 70% | Has full pivot divergence implementation (PineScript) |
| S8 (Three Pillars) | 45% | Only one with Stoch 55 trigger (correct per Core-Trading-Strategy.md v2) |
| S5 (55/89 EMA) | 35% | Macro gate ≠ cascade; no divergence |
| S3 (v3.8 crossover) | 20% | A only |
| S4 (v3.8.4 current) | 10% | VIOLATED — simultaneous pile-in is anti-pattern; code contradicts description |
| S11 (AVWAP) | 15% | Structural complement only |
| S6 (Ripster) | 5% | No stochastics at all |
| S2/S9 | 0% | Different paradigms (rebate, filter) |

### Critical Finding: S4 Explains R:R = 0.28

v3.8.4 state machine (`state_machine.py`) requires stoch_9/14/40/60 ALL in extreme (<25-30) SIMULTANEOUSLY. This is the opposite of cascade. Fires on V-bottoms (max ATR, max volatility) — worst possible entry conditions. This finding directly explains R:R = 0.28.

Additional: S4 visualizer shows "Stoch 60 above 80" as macro condition, but CODE checks `stoch_60 < 25`. Code and description are INVERTED.

### Rebate Subsidy Finding (user-stated)

"v3.8.4 only made sense because rebate was pumped back into the system."

At BingX $50 notional: rebate = $0.056 per trade. Current avg_loss = $0.44. Loss is 8x the rebate.
v4 hard constraint: must be independently breakeven (R:R >= 1.0 at 50% WR). Rebates = bonus.

At WEEX $10,000 notional: rebate was $11.20 per trade. $0.44 loss was noise. The rebate model no longer works at $50 notional.

### Cascade Overlap Problem

On sharp V-bottoms, all 4 Raw K stochastics snap simultaneously (same close, all denominators). Cascade (Stoch 40 before Stoch 60) only exists on GRADUAL recoveries. Guard needed: `min_cascade_gap` bars between Stoch 40 and Stoch 60 exits, OR regression channel gate.

### Divergence Detection Design

Two approaches researched:
1. **Natural two-cycle state machine** (recommended) — no lookahead, IDLE->CYCLE_1->COOLDOWN->CYCLE_2->SIGNAL. Tracks price_low and stoch_9_low across two consecutive oversold visits. Divergence = price makes lower low, stoch makes higher low.
2. **Pivot method** (from S7/Quad Rotation) — has 3-bar lookahead delay (15 min at 5m). Better for backtester, not live.

### Regression Channel Design

Pure NumPy: slope_pct, r_squared, band_width_pct. Gate: slope < -0.001 AND r_sq > 0.55 AND band_w < 0.03. This is equivalent to the cascade gap guard — both detect "gradual recovery" vs "V-bottom." Redundant but complementary.

### Stoch 55 Problem (never previously stated plainly)

`Core-Trading-Strategy.md` v2 says entry trigger = Stoch 55 crosses UP. Not one strategy in S1-S11 implements Stoch 55 as trigger. It is not in `stochastics.py`. Adding it requires new code, not config change.

## 5 Decisions Required Before Any Build

1. Run v3.8.4 backtester baseline: YES / NO
2. Channel gate in v4.0: YES / NO
3. Two-cycle divergence in v4.0: YES / NO
4. Stoch 55 in v4.0: YES / NO
5. Model: CASCADE (stoch 40 exits oversold, Session 4) or HYBRID (stoch 40/60 > 50, design doc): ?

## Files Read This Session

- `02-STRATEGY/STRATEGY-V4-DESIGN.md`
- `02-STRATEGY/Core-Trading-Strategy.md`
- `02-STRATEGY/Trading-Manifesto.md`
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic.md`
- `02-STRATEGY/Indicators/ATR-SL-MOVEMENT-BUILD-GUIDANCE.md`
- `06-CLAUDE-LOGS/2026-03-07-strategy-catalogue-visual-plan.md`
- `06-CLAUDE-LOGS/PROJECT-STATUS.md`
- `PROJECTS/four-pillars-backtester/signals/state_machine.py`
- `PROJECTS/four-pillars-backtester/signals/stochastics.py`
- `PROJECTS/four-pillars-backtester/scripts/visualize_strategy_perspectives.py`
- `PROJECTS/four-pillars-backtester/scripts/visualize_strategy_perspectives_v2.py`
- `PROJECTS/four-pillars-backtester/results/sl_lifecycle/` (glob — 12 PNGs confirmed)
- `memory/TOPIC-55-89-scalp.md`
- `memory/TOPIC-bingx-connector.md`
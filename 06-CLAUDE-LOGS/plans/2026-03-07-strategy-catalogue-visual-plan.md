# Plan: Strategy Catalogue + Visual Representations

**Date:** 2026-03-07
**Session log:** C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-bingx-v2-live-scaling-session.md

---

## Context

User wants to step back from execution and get clarity. No code yet. Three deliverables:

1. All strategies documented with their perspectives (logic, indicators, rules)
2. Visual representations of each strategy using the strategy-viz skill
3. A calm working mode — research and scoping only, code on explicit request

The goal is a clean mental model before deciding what to build next.

---

## Scope of this planning session

**IN:**
- Document all strategies in written form (their rules, indicators, perspectives)
- Identify which visualizations need building
- Define what "visual representation" means per strategy (SL/TP lifecycle scenarios)

**OUT (not building now):**
- No code written this session
- No backtests run
- No config changes to BingX bot

---

## Strategy Inventory

### Strategy 1: Four Pillars v3.8.4 (current production)
**Timeframe:** 5m
**Indicators:**
- Ripster EMA Clouds: Cloud 2 (5/12), Cloud 3 (34/50), Cloud 4 (72/89)
- Stochastics: Stoch 9,3 (entry gate), Stoch 14,3 (confirm), Stoch 40,3 (direction), Stoch 60,10 (macro)
- BBWP (100-bar, SMA-5) — volatility regime filter
- ATR(14) — SL sizing
- Anchored VWAP — volume/price validation

**Entry (A trade):** Stoch 9 exits oversold/overbought zone, Cloud 3 aligned, BBW healthy, stoch 40/60 in TURNING+ state
**Entry (B trade):** Scaled ADD on stoch 9 exit while 40/60 confirm (re-entry)
**SL:** 2.5 ATR from entry (phase 1, bars 0-4), then AVWAP -2 sigma frozen (phase 2+)
**TP:** Coin-specific ATR multiplier (RIVER: 2.0 ATR, KITE/BERA: no fixed TP)
**BE raise:** ATR-based trigger, raises SL to AVWAP center
**Scale-out:** Every 5 bars on partial

**Key perspectives:**
- Momentum continuation: if stoch 55 declines after cross → exit early with small win
- Three Pillars must stay aligned (Price + Volume + Momentum)
- BBW regime gates all signals (QUIET = no trade)

**Status:** v3.8.4 stable in backtester. v3.9.1 built but UNVERIFIED (do not deploy)

---

### Strategy 2: Core Trading Strategy (v2.0 — manual/conceptual)
**Timeframe:** 30m (example), adaptable
**Indicators:**
- BBWP (20/100, SMA-5) — volatility squeeze filter
- Stoch 9 (fast, entry zone)
- Stoch 55 (trigger cross)
- TDI CW_Trades (momentum confirm)
- Ripster Clouds (5/12, 34/50, 8/9)
- Anchored VWAP from swing low/high
- Volume Profile (POC, VAH, VAL)
- ATR(14) — stop sizing

**Entry:** BBWP squeeze (< 10%), Stoch 9 extreme, Stoch 55 cross, price crosses 34/50 cloud, ATR rising
**Hold:** All 3 pillars persist (Price above cloud + VWAP, Momentum building, Volume confirming)
**Exit (protective):** Stoch 55 declines after cross → exit with small win
**Exit (profit):** BBWP maxed (>90%), stochs reach opposite extreme, Volume Profile target hit, ATR declining
**SL:** Below AVWAP anchor OR below swing low, max 2 ATR

**Key perspectives:**
- Momentum continuation is THE defining rule — "Stoch 55 declines after cross = exit immediately"
- Small win > Small loss > Big loss (capital protection philosophy)
- Volatility FILTER (BBW) gates entry, not signal

---

### Strategy 3: BingX Bot v1.5 (live, automated)
**Timeframe:** 5m
**Indicators:**
- EMA 5m (internal trend filter, config: ema_filter)
- ATR(14) — SL sizing (sl_atr_mult: 2.0)
- Trailing Take Profit (TTP, native BingX)
- BE raise (breakeven trigger)

**Entry:** External signal from backtester (4 Pillars logic), BingX native order
**SL:** 2x ATR from entry
**TP:** TTP only — trailing from peak, captures ~0.5% moves currently
**BE raise:** After threshold met (be_raise config)
**Config:** 47 coins, $5 margin, 10x leverage, ttp_mode: native

**Current issue:** R:R = 0.28 (wins ~$0.123, losses ~$0.440)
- Wins too small: TTP activates but trail too tight, exits on minor pullback
- Losses too large: 2x ATR SL on volatile coins hits regularly
- Fix direction: diagnose TTP activation threshold vs SL width

---

### Strategy 4: 55/89 EMA Cross Scalp (research, not deployed)
**Timeframe:** 1m
**Indicators:**
- EMA(55) and EMA(89) — cross = entry trigger
- Stoch 9,3 (overzone gate — oversold/overbought exit = phase transition)
- Stoch 14,3 (alignment confirm)
- Stoch 40,3 (directional momentum)
- Stoch 60,10 (macro direction)
- TDI: RSI(9) smoothed at 5 and 10 bars (confirms momentum)
- BBWP (volatility regime, blocks QUIET state)
- AVWAP (SL trail anchor — frozen -2 sigma after bar 5)
- ATR(14) — initial SL sizing
- Ripster Cloud 4 (72/89) — Phase 4 TP target edge

**Entry:** Stoch 9 K/D cross triggers MONITORING state → alignment check (stoch 14 MOVING/EXTENDED, 40/60 TURNING+, delta compressing, TDI above signal, BBW not QUIET) → EMA 55/89 cross fires signal

**SL Lifecycle (4 phases):**
- Phase 1 (bars 0-4): SL = entry - 2.5 ATR
- Phase 2 (bar 5): SL = frozen AVWAP -2 sigma computed over bars 0-4
- Phase 3 (each overzone exit): SL = live AVWAP -2 sigma, ratchet_count++
  - Long overzone: stoch 9,3 D < 20 then crosses back > 20
  - Short overzone: stoch 9,3 D > 80 then crosses back < 80
- Phase 4 (ratchet_count >= 2): TP = Cloud 4 (72/89) edge + X*ATR

**Key perspectives:**
- Overzone exit = continuation (momentum resuming), NOT exhaustion
- AVWAP center too tight for 1m — must use -2 sigma
- Cloud 4 moves with price — TP is dynamic, not static
- Signal module BUILT (28/28 tests pass), engine integration NOT started

---

## Visual Representation Plan

Using strategy-viz skill:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\skills\strategy-viz\SKILL.md`

For each strategy, the visualizer needs:
1. Entry bar (price, indicators)
2. SL placement and movement rules
3. Phase transitions (what triggers each)
4. Exit scenarios (TP, BE exit, trail floor, reversal)

**Output files (when user says to build):**
- `scripts/visualize_four_pillars_v384.py` → `results/four_pillars_v384/scenario_NN.png`
- `scripts/visualize_core_strategy_v2.py` → `results/core_strategy_v2/scenario_NN.png`
- `scripts/visualize_55_89_scalp.py` → `results/55_89_scalp/scenario_NN.png`
- BingX bot: deferred (SL/TP rules depend on TTP config diagnosis first)

**Scenarios per strategy (7 per side):**
1. Phase 1 SL hit (initial stop taken)
2. BE exit (price barely moves, SL raised to entry, stopped at BE)
3. Trail floor hit (trails up then retraces to floor)
4. Ratchet 1 (first phase transition, SL raises)
5. Ratchet 2+ (second+ transition, TP activates)
6. Clean TP hit (full run to target)
7. Full reversal (price runs far, comes all the way back)

---

## Working Mode

Per user instruction: scoping and research only. No code output until explicitly requested.

**Format for future sessions:**
- Read relevant files first
- Describe what will be built and why
- Wait for "build it" instruction before writing any code

---

## Files Referenced

| File | Purpose |
|------|---------|
| `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Core-Trading-Strategy.md` | Core strategy v2.0 rules |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v391.py` | Latest signal pipeline |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89.py` | 55/89 scalp signal module |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\55-89-scalp-methodology.md` | 55/89 research doc (DRAFT) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\skills\strategy-viz\SKILL.md` | Visualization skill |
| `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-55-89-scalp.md` | 55/89 memory |
| `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-backtester.md` | Backtester memory |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\config.yaml` | Live bot config |

---

## Next Steps (user-driven)

1. Review this catalogue — confirm strategies are correctly described
2. Identify any missing strategy or wrong perspective
3. When ready: say "build visuals for [strategy name]" — one at a time
4. BingX R:R diagnosis is a separate session if/when user wants it

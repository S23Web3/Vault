# S12 Macro Cycle — Vince Backtester Integration Prompt

**Date:** 2026-03-10
**Target agent:** Claude (new session)
**Output:** signals/s12_macro_cycle.py + scripts/build_s12_engine.py + scripts/test_s12_engine.py

---

## Prompt

```
# S12 Macro Cycle Strategy — Backtester Signal Engine Build

## Mandatory First Step
Load the Python skill: /python

---

## Project

Four Pillars Trading System backtester.
Root: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\

---

## Strategy Reference

READ THIS FIRST before writing any code:
  C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\S12-MACRO-CYCLE.md

Also read existing signal engines for structural patterns:
  signals/ema_cross_55_89.py
  signals/regression_channel.py

---

## What S12 Is

S12 Macro Cycle is a bidirectional (long + short) strategy where stoch_60 is
the PRIMARY instrument. One stoch_60 cycle produces up to FIVE distinct entry
tiers — all firing the same directional thesis, all sharing the same exit target.

The five tiers in order of fire time within one cycle:

  T0 — Pre-cross structural exhaustion (fires BEFORE the threshold cross)
  T1 — Cross mechanical (fires AT the stoch_60 threshold crossing)
  T2 — TDI Bollinger Band bounce (fires when TDI fast line reverses from BB extreme)
  T3 — V4 cascade divergence (fires when full four-layer pipeline confirms)
  T4 — Cloud midband cycle transition (fires at LONG exit = SHORT entry)

Each tier is evaluated independently. Multiple tiers can fire in the same cycle.
No tier blocks another. The backtester evaluates each tier as its own trade.

---

## Signal Engine Spec

### File: signals/s12_macro_cycle.py

Stateless function-based module. No classes. Pure NumPy + namedtuples.

---

#### Input arrays (all length N, float64)

  close[]           — close prices
  high[]            — high prices (used for T0 SHORT stop_bar reference)
  low[]             — low prices (used for T0 LONG stop_bar reference)
  stoch_9_k[]       — stoch K, period 9
  stoch_40_k[]      — stoch K, period 40
  stoch_60_k[]      — stoch K, period 60
  stoch_60_d[]      — stoch D, period 60 (3-bar SMA of K)
  cloud2_upper[]    — Cloud 2 upper band (max(5EMA, 12EMA))
  cloud2_lower[]    — Cloud 2 lower band (min(5EMA, 12EMA))
  cloud3_upper[]    — Cloud 3 upper band (max(34EMA, 50EMA))
  cloud3_lower[]    — Cloud 3 lower band (min(34EMA, 50EMA))
  bbwp[]            — BBWP value, 0-100
  tdi_fast[]        — TDI fast RSI line
  tdi_ma[]          — TDI slow MA line (MA of tdi_fast)
  tdi_bb_upper[]    — TDI Bollinger Band upper
  tdi_bb_lower[]    — TDI Bollinger Band lower

All arrays pre-computed before calling. Signal engine does NOT compute indicators.

---

#### S12Signal namedtuple

  from collections import namedtuple
  S12Signal = namedtuple("S12Signal", [
      "direction",    # "long" | "short"
      "tier",         # int 0-4 — which tier fired this signal
      "entry_bar",    # int — bar index where signal fires
      "stop_bar",     # int — bar index of the SL reference candle
      "exit_bar",     # int — bar index where exit fires (-1 if open)
      "exit_reason",  # str — exit reason code
      "reason",       # str — entry reason code
  ])

  Entry reason codes:
    "t0_long"   — T0 pre-cross, deep oversold + cloud/TDI at extreme (LONG)
    "t0_short"  — T0 pre-cross, deep overbought + thin cloud + TDI at extreme (SHORT)
    "t1_long"   — T1 stoch_60 K crosses above 25, cloud blue
    "t1_short"  — T1 stoch_60 K crosses below 80, cloud direction valid
    "t2_long"   — T2 TDI fast bounces from lower BB, MA slope up
    "t2_short"  — T2 TDI fast bounces from upper BB, MA slope down
    "t3_long"   — T3 V4 full four-layer pipeline confirmed (LONG)
    "t3_short"  — T3 V4 full four-layer pipeline confirmed (SHORT)
    "t4_short"  — T4 cycle transition: LONG exits at Cloud 3 midband, SHORT entry
    "t4_long"   — T4 cycle transition: SHORT exits at stoch_60 oversold, LONG entry

  Entry rejection codes:
    "rejected_simultaneous"     — pile-in, not cascade (T3)
    "rejected_cloud_thick"      — Cloud 2 delta too thick for T0/T3 SHORT
    "rejected_macro_gate"       — stoch_60 < macro_gate at T3 LONG entry
    "rejected_bbwp_high"        — BBWP > bbwp_entry_max at T3 entry
    "rejected_cloud_direction"  — cloud structure does not support direction

  Exit reason codes:
    "exit_opposite_extreme"  — stoch_60 reached opposite extreme
    "exit_price_into_cloud"  — price crossed Cloud 3 midband (LONG primary exit)
    "exit_bbwp_exhausted"    — BBWP <= bbwp_exhaustion_exit
    "exit_thesis_invalid"    — stoch_60 K/D flipped against position

  All tiers share the same exit conditions (Function 7).

---

#### S12Params namedtuple

  S12Params = namedtuple("S12Params", [
      "stoch60_overbought_exit",    # default 80.0 — T1/T3 SHORT cross threshold
      "stoch60_oversold_exit",      # default 25.0 — T1/T3 LONG cross threshold
      "stoch60_deep_overbought",    # default 85.0 — T0 SHORT deep extreme threshold
      "stoch60_deep_oversold",      # default 15.0 — T0 LONG deep extreme threshold
      "stoch60_macro_gate",         # default 40.0 — T3 LONG macro gate
      "cloud_delta_thin_pct",       # default 0.002 — T0/T3 SHORT thin cloud threshold
      "bbwp_entry_max",             # default 40.0 — T3 entry BBWP cap
      "bbwp_exhaustion_exit",       # default 2.0 — exit trigger
      "kd_flip_bars",               # default 3 — consecutive bars for thesis_invalid exit
      "cascade_min_bars_between",   # default 3 — T3 min bars between stoch_9 and stoch_40 cross
  ])

  DEFAULT_PARAMS = S12Params(
      stoch60_overbought_exit=80.0,
      stoch60_oversold_exit=25.0,
      stoch60_deep_overbought=85.0,
      stoch60_deep_oversold=15.0,
      stoch60_macro_gate=40.0,
      cloud_delta_thin_pct=0.002,
      bbwp_entry_max=40.0,
      bbwp_exhaustion_exit=2.0,
      kd_flip_bars=3,
      cascade_min_bars_between=3,
  )

---

#### Function 1: compute_cloud2_delta(cloud2_upper, cloud2_lower) -> ndarray

  Return per-bar fractional delta:
    (cloud2_upper - cloud2_lower) / ((cloud2_upper + cloud2_lower) / 2)
  Units: fraction (0.002 = 0.2%). Returns ndarray length N.

---

#### Function 2: detect_cross_above(arr, threshold) -> ndarray[bool]

  Return True at bars where arr[i-1] < threshold and arr[i] >= threshold.
  arr[0] always False. Exactly one True per crossing event.

---

#### Function 3: detect_cross_below(arr, threshold) -> ndarray[bool]

  Return True at bars where arr[i-1] > threshold and arr[i] <= threshold.
  arr[0] always False.

---

#### Function 4: check_cascade_quality(stoch_9_k, stoch_40_k, bar, params) -> bool

  Look back params.cascade_min_bars_between+15 bars from bar.
  PASS if:
    stoch_9_k crossed above 25 within window
    AND stoch_40_k crossed above 30 at least params.cascade_min_bars_between
    bars AFTER the stoch_9 cross
  FAIL (simultaneous or wrong order) otherwise.

---

#### Function 5: check_cloud2_structure(cloud2_delta, bar, direction, thin_pct) -> bool

  SHORT: return True if cloud2_delta[bar] < thin_pct
  LONG:  return True always if cloud2_upper[bar] > cloud2_lower[bar] (blue, any thickness)
  Caller passes cloud2_upper and cloud2_lower separately for LONG check.

---

#### Function 6: check_macro_position(close, cloud3_upper, cloud3_lower, bar,
                                       direction) -> bool

  SHORT: return True if close[bar] <= cloud3_upper[bar]
  LONG:  return True if close[bar] >= cloud3_lower[bar]

---

#### Function 7: check_exit_conditions(close, stoch_60_k, stoch_60_d, cloud3_upper,
                                        cloud3_lower, bbwp, entry_bar, direction,
                                        params) -> tuple[int, str]

  Scan from entry_bar+1 to end. Return (exit_bar, exit_reason) for FIRST match.
  Return (-1, "open") if no exit before end of data.

  Priority order:
    1. bbwp[bar] <= params.bbwp_exhaustion_exit
       -> (bar, "exit_bbwp_exhausted")
    2. SHORT: detect_cross_above(stoch_60_k, 25.0)[bar]
       LONG:  detect_cross_below(stoch_60_k, 80.0)[bar]  (stoch_60 reaches opposite extreme)
       -> (bar, "exit_opposite_extreme")
    3. LONG only: close[bar] > (cloud3_upper[bar] + cloud3_lower[bar]) / 2
       -> (bar, "exit_price_into_cloud")
    4. SHORT: count consecutive bars where stoch_60_k[bar] > stoch_60_d[bar]
              if count >= params.kd_flip_bars -> (bar, "exit_thesis_invalid")
       LONG:  count consecutive bars where stoch_60_k[bar] < stoch_60_d[bar]
              if count >= params.kd_flip_bars -> (bar, "exit_thesis_invalid")

---

#### Function 8: detect_tdi_bounce(tdi_fast, tdi_bb_upper, tdi_bb_lower, tdi_ma,
                                    bar, direction) -> bool

  LONG: return True if tdi_fast[bar-1] <= tdi_bb_lower[bar-1]
                  AND tdi_fast[bar] > tdi_bb_lower[bar]
                  AND tdi_ma[bar] > tdi_ma[bar-1]
  SHORT: return True if tdi_fast[bar-1] >= tdi_bb_upper[bar-1]
                   AND tdi_fast[bar] < tdi_bb_upper[bar]
                   AND tdi_ma[bar] < tdi_ma[bar-1]
  bar must be >= 1.

---

#### Function 9: generate_signals(close, high, low, stoch_9_k, stoch_40_k,
                                   stoch_60_k, stoch_60_d, cloud2_upper, cloud2_lower,
                                   cloud3_upper, cloud3_lower, bbwp,
                                   tdi_fast, tdi_ma, tdi_bb_upper, tdi_bb_lower,
                                   params) -> list[S12Signal]

  Main entry point. Returns ALL signals — all tiers, both fired and rejected.
  Tiers evaluated independently. Multiple tiers may fire in same cycle.
  No-overlap rule: PER TIER, after a signal fires advance that tier's pointer
  to exit_bar + 1 before generating the next signal for that tier.
  Start scanning from bar 60 (indicator warmup).

  Precompute once:
    cloud2_delta = compute_cloud2_delta(cloud2_upper, cloud2_lower)
    cross_above_25 = detect_cross_above(stoch_60_k, 25.0)
    cross_below_80 = detect_cross_below(stoch_60_k, 80.0)

  RADAR ARMED:
    long_armed[bar] = stoch_60_k[bar] < params.stoch60_oversold_exit
    short_armed[bar] = stoch_60_k[bar] > params.stoch60_overbought_exit

  --- TIER 0 — pre-cross structural exhaustion ---

  T0 SHORT at bar i (when NOT already in a T0 SHORT trade):
    short_armed[i] is True
    stoch_60_k[i] >= params.stoch60_deep_overbought
    check_cloud2_structure(cloud2_delta, i, "short", params.cloud_delta_thin_pct)
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "short")
    tdi_fast[i] >= tdi_bb_upper[i]   (TDI at upper extreme, not yet bouncing)
    PASS: reason="t0_short", tier=0, stop_bar=i (SL = high[i])
          call check_exit_conditions -> exit_bar, exit_reason
    REJECT: append S12Signal with appropriate rejection reason, tier=0

  T0 LONG at bar i:
    long_armed[i] is True
    stoch_60_k[i] <= params.stoch60_deep_oversold
    cloud2_upper[i] > cloud2_lower[i]  (cloud blue, any thickness)
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "long")
    tdi_fast[i] <= tdi_bb_lower[i]   (TDI at lower extreme)
    PASS: reason="t0_long", tier=0, stop_bar=i (SL = low[i])
          call check_exit_conditions -> exit_bar, exit_reason

  --- TIER 1 — cross mechanical ---

  T1 SHORT at bar i:
    cross_below_80[i] is True
    stoch_60_k[i] < stoch_60_d[i]
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "short")
    PASS: reason="t1_short", tier=1, stop_bar=i
          call check_exit_conditions -> exit_bar, exit_reason
    REJECT: reason="rejected_cloud_direction"

  T1 LONG at bar i:
    cross_above_25[i] is True
    stoch_60_k[i] > stoch_60_d[i]
    cloud2_upper[i] > cloud2_lower[i]
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "long")
    PASS: reason="t1_long", tier=1, stop_bar=i
          call check_exit_conditions -> exit_bar, exit_reason
    REJECT: reason="rejected_cloud_direction"

  --- TIER 2 — TDI Bollinger Band bounce ---

  T2 SHORT at bar i:
    short_armed[i] is True (still in armed zone or just exited)
    detect_tdi_bounce(tdi_fast, tdi_bb_upper, tdi_bb_lower, tdi_ma, i, "short")
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "short")
    PASS: reason="t2_short", tier=2, stop_bar=i
          call check_exit_conditions -> exit_bar, exit_reason

  T2 LONG at bar i:
    long_armed[i] is True or cross_above_25 recently fired within 5 bars
    detect_tdi_bounce(tdi_fast, tdi_bb_upper, tdi_bb_lower, tdi_ma, i, "long")
    cloud2_upper[i] > cloud2_lower[i]
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "long")
    PASS: reason="t2_long", tier=2, stop_bar=i
          call check_exit_conditions -> exit_bar, exit_reason

  --- TIER 3 — V4 cascade divergence ---

  T3 LONG at bar i:
    cross_above_25[i] is True
    stoch_60_k[i] > stoch_60_d[i]
    stoch_60_k[i] >= params.stoch60_macro_gate
    check_cloud2_structure(cloud2_delta, i, "long", params.cloud_delta_thin_pct)
      NOTE: for LONG, thin_pct check passes because LONG cloud check is any thickness
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "long")
    bbwp[i] <= params.bbwp_entry_max
    check_cascade_quality(stoch_9_k, stoch_40_k, i, params)
    PASS: reason="t3_long", tier=3, stop_bar=i
          call check_exit_conditions -> exit_bar, exit_reason
    REJECT: append with appropriate rejection reason, tier=3

  T3 SHORT at bar i:
    cross_below_80[i] is True
    stoch_60_k[i] < stoch_60_d[i]
    check_cloud2_structure(cloud2_delta, i, "short", params.cloud_delta_thin_pct)
    check_macro_position(close, cloud3_upper, cloud3_lower, i, "short")
    bbwp[i] <= params.bbwp_entry_max
    PASS: reason="t3_short", tier=3, stop_bar=i
          call check_exit_conditions -> exit_bar, exit_reason
    REJECT: append with rejection reason, tier=3

  --- TIER 4 — cloud midband cycle transition ---

  T4 is special: it fires at the bar where a PREVIOUS LONG trade (any tier) exits
  via "exit_price_into_cloud" AND stoch_60 is building overbought.

  T4 SHORT at bar i:
    Any prior LONG signal (T0/T1/T2/T3) exited at bar i with "exit_price_into_cloud"
    stoch_60_k[i] > stoch_60_d[i]   (building toward overbought, not yet there)
    stoch_60_k[i] > stoch_60_k[i-1]  (K rising)
    PASS: reason="t4_short", tier=4, stop_bar=i (SL = high[i] = the Cloud 3 midband touch)
          call check_exit_conditions with direction="short" from bar i+1

  T4 LONG at bar i:
    Any prior SHORT signal (T0/T1/T2/T3) exited at bar i with "exit_opposite_extreme"
    stoch_60_k[i] < stoch_60_d[i]   (building toward oversold)
    stoch_60_k[i] < stoch_60_k[i-1]  (K declining)
    PASS: reason="t4_long", tier=4, stop_bar=i (SL = low[i])
          call check_exit_conditions with direction="long" from bar i+1

  T4 does not require radar armed check — it uses the prior trade's exit as its trigger.

---

### File: scripts/build_s12_engine.py

Build script following the IDENTICAL pattern used in scripts/build_regression_channel.py.
READ that file first. Match its structure exactly.

Rules:
  - Line-list construction (L.append(...)) — NO triple-quoted source embedding anywhere
  - Check os.path.exists() on output file first — abort if exists
  - Write signals/s12_macro_cycle.py
  - Run py_compile + ast.parse on output — both must pass
  - Print full absolute Windows path + [PASS] or [FAIL]
  - sys.exit(1) on any failure

---

### File: scripts/test_s12_engine.py

Plain Python. No pytest. Run: python scripts/test_s12_engine.py

Tests (14 total):

  1.  detect_cross_above: verify True on exact crossing bar, False on prior bar
  2.  detect_cross_below: verify True on exact crossing bar, False on prior bar
  3.  check_cascade_quality PASS: stoch_9 crosses above 25 at bar 5, stoch_40 at bar 9
      (gap = 4 bars >= cascade_min_bars_between=3) -> True
  4.  check_cascade_quality FAIL simultaneous: both cross same bar -> False
  5.  check_cascade_quality FAIL wrong order: stoch_40 crosses before stoch_9 -> False
  6.  compute_cloud2_delta: verify thin delta (upper-lower small) < 0.002,
      thick delta > 0.002
  7.  detect_tdi_bounce LONG: set tdi_fast[i-1] below tdi_bb_lower, tdi_fast[i] above ->
      True. Also verify tdi_ma must slope up else False.
  8.  detect_tdi_bounce SHORT: set tdi_fast[i-1] above tdi_bb_upper, tdi_fast[i] below ->
      True with tdi_ma declining. False if tdi_ma flat.
  9.  T0 SHORT signal: build synthetic 120-bar scenario where stoch_60 reaches 87,
      cloud2_delta thin, tdi_fast at upper BB, macro position valid.
      Verify signal with tier=0, reason="t0_short", stop_bar=entry candle.
  10. T1 LONG signal: stoch_60 K crosses above 25, K > D, cloud blue.
      Verify tier=1, reason="t1_long", entry_bar at cross.
  11. T2 LONG signal: TDI fast bounces from lower BB within 5 bars of stoch_60 cross.
      Verify tier=2, reason="t2_long", entry_bar at TDI bounce bar.
  12. T3 LONG signal: full V4 pipeline passes (cascade + macro gate + cloud + BBWP).
      Verify tier=3, reason="t3_long".
  13. T4 SHORT signal: build scenario where T1 LONG exits at Cloud 3 midband AND
      stoch_60 building overbought at that bar.
      Verify tier=4, reason="t4_short", entry_bar == prior LONG exit_bar.
  14. Five tiers coexist: build scenario where T0, T1, T2, T3 all fire in same
      stoch_60 cycle. Verify all four present in output independently.
      Verify T4 fires after the cycle exits at Cloud 3 midband.
      Total signals in output for this cycle: >= 4 (T0+T1+T2+T3+T4).

Each test prints: "Test N: <description> -> PASS  <detail>" or "FAIL <reason>".
Exit with sys.exit(1) if any FAIL.

---

## Hard Rules

- NEVER use escaped quotes inside f-strings in build scripts. Use concatenation.
- py_compile + ast.parse must BOTH pass before [PASS].
- NEVER overwrite existing files. Check os.path.exists() first.
- Every function must have a one-line docstring.
- All printed paths must be full absolute Windows paths.
- No emojis in any file.
- Do NOT run Python scripts via Bash except py_compile one-liners.
- Use pathlib.Path for all paths. No raw backslash strings.
- Signal engine is STATELESS. No classes. No mutation. Pure functions + namedtuples only.
- tdi arrays may be None — if any tdi_ array is None, T0 and T2 are skipped silently.

---

## Output

1. Deliver: build script at full path.
2. Run build:
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_s12_engine.py"
3. Confirm [PASS] for signals/s12_macro_cycle.py
4. Run tests:
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_s12_engine.py"
5. Confirm all 14 tests pass.
```

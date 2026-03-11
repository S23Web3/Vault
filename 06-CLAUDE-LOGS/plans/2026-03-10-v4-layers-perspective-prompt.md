# V4 Strategy Layers — Perspective Visualizer Build Prompt

**Date:** 2026-03-10
**Target agent:** Claude (new session)
**Output:** scripts/visualize_v4_layers.py via build script

---

## Prompt

```
# V4 Strategy Layers — Perspective Visualizer Build

## Mandatory First Step
Load the Python skill: /python

---

## Project
Four Pillars Trading System backtester.
Root: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\

---

## Context: What "Perspective" Means in This Codebase

This codebase has a series of strategy perspective visualizers (S1-S11) in:
  scripts/visualize_strategy_perspectives.py   (S1-S5)
  scripts/visualize_strategy_perspectives_v2.py (S6-S11)

Each generates a PNG showing:
  - Synthetic price and indicator data illustrating ONE ideal-scenario trade setup
  - Annotated state transitions (when does each condition trigger?)
  - A text box explaining what the strategy "reads" in plain English
  - Multi-panel GridSpec layout (price + each indicator layer)

This task builds the SAME style visualizer for V4's 4-layer signal pipeline.
READ the existing visualizers before writing any code to match their style exactly.

---

## V4 Layer Architecture (do not conflate these)

LAYER 1 — MACRO GATE (stoch_60 >= 40)
  Purpose: ensure we are not in deep structural oversold. Macro context must be
  neutral-to-bullish. stoch_60 >= 40 means the 60-bar stochastic is above midline.
  This is a simple threshold gate — either passes or fails. Non-sweepable.
  Default: 40. NOT the same as "stoch_60 pinned above 80" (that is S4's mistake).

LAYER 2 — CHANNEL GATE (regression_channel.py — already built)
  Pre-condition computed ONCE at Stage 1 entry.
  Checks the 20 bars BEFORE Stage 1: was there an orderly downtrend?
  Gate: r_squared > 0.45 AND slope_pct < -0.001 (declining at >= 0.1% per bar).
  Rejects V-bottoms (low R²) and sideways chop (flat slope).
  Source: signals/regression_channel.py — pre_stage1_gate(), fit_channel()

LAYER 3 — TWO-CYCLE DIVERGENCE DETECTOR
  The core entry logic. Two-cycle state machine:
    IDLE
    -> CYCLE_1: stoch_9 enters oversold (< 25), record price_low_c1, stoch_low_c1
    -> COOLDOWN: stoch_9 exits oversold (crosses above 25), bounces to >= 40
    -> CYCLE_2: stoch_9 enters oversold AGAIN (< 25), record price_low_c2, stoch_low_c2
    -> SIGNAL: stoch_9 exits oversold (crosses above 25) on Cycle 2
       Divergence confirmed if:
         price_low_c2 < price_low_c1   (price made a lower low)
         stoch_low_c2 > stoch_low_c1   (stoch made a higher low)
       Combined: price went down further but momentum did not — reversal signal.
       If both conditions not met: reset to IDLE (no signal).

LAYER 4 — CASCADE GATE (stoch_40 >= 30 at Cycle 2 exit)
  At the moment Cycle 2 generates a divergence signal, check stoch_40.
  stoch_40 >= 30 means the medium-term stochastic is already recovering.
  This confirms the "cascade": stoch_9 recovers first, stoch_40 follows.
  On true recoveries: stoch_40 exits oversold 3-8 bars BEFORE stoch_60 follows.
  On V-bottoms: all stochastics snap simultaneously (cascade gate rejects these).

SIGNAL FIRES when ALL FOUR layers are satisfied simultaneously at Cycle 2 exit.

---

## What the Visualizer Must Show

### Output file
  results/strategy_perspectives/V4_four_layer_signal.png

### Panel layout (7 panels, GridSpec 7x1)
  Panel 0 (large): Price + regression channel band overlay + entry marker
  Panel 1: stoch_9 with CYCLE_1 / COOLDOWN / CYCLE_2 state markers + threshold lines at 25 and 40
  Panel 2: stoch_40 with threshold line at 30 (cascade gate) + gate pass marker
  Panel 3: stoch_60 with threshold line at 40 (macro gate) + pass/fail shading
  Panel 4: Channel gate indicators — R² and slope_pct as dual-axis line chart (synthetic values)
  Panel 5: Gate status bars — one bar per layer (Green=PASS, Red=FAIL) across time
  Panel 6 (small): Entry signal bar — green spike at the single bar where ALL 4 fire

### Annotation text box (top-left of Panel 0)
  Plain-English description:
    "LAYER 1 — MACRO GATE: stoch_60 >= 40 (neutral-to-bullish context, not deep oversold)"
    "LAYER 2 — CHANNEL GATE: 20-bar pre-Stage1 regression: R² > 0.45, slope < -0.1%/bar"
    "  Rejects V-bottoms (low R²) and chop (flat slope). Runs ONCE at Stage 1 entry."
    "LAYER 3 — DIVERGENCE: price LL + stoch_9 HL across two oversold cycles"
    "  State: IDLE -> CYCLE_1 -> COOLDOWN -> CYCLE_2 -> SIGNAL (or reset)"
    "LAYER 4 — CASCADE: stoch_40 >= 30 at Cycle 2 exit (medium stoch recovering)"
    "  Distinguishes true cascades from simultaneous pile-in (V-bottom rejection)"
    "SIGNAL: All 4 layers green at Cycle 2 stoch_9 exit above 25"

### Entry markers
  - Vertical dashed line at Cycle 1 entry bar (label: "C1 entry")
  - Vertical dashed line at Cycle 1 exit bar (label: "C1 exit")
  - Vertical dashed line at Cycle 2 entry bar (label: "C2 entry")
  - Filled green triangle at signal bar (label: "ENTRY")
  - On price panel: annotate price_low_c1 and price_low_c2 with horizontal dotted lines

### Synthetic data design
  Use 120 bars. Construct a scenario that shows a PERFECT signal:
    bars 0-20:   stoch_60 declining from 55 to 42 (stays above 40 — macro gate PASSES)
    bars 0-20:   price declining from 1.050 to 1.035 (channel gate: orderly slope)
    bars 20-35:  Cycle 1 — stoch_9 dips to 18, price troughs at 1.032
    bars 35-55:  Cooldown — stoch_9 bounces to 45, price recovers to 1.038
    bars 55-75:  Cycle 2 — stoch_9 dips to 22 (HIGHER than 18 = divergence), price troughs at 1.029 (LOWER)
    bars 75-80:  stoch_9 crosses above 25 (Cycle 2 exit = signal bar)
    bars 75-80:  stoch_40 at 33 (>= 30 — cascade gate PASSES)
    bars 80-120: price recovers to 1.055 (shows the trade working out)

  Channel gate synthetic values (for Panel 4):
    R²: flat at 0.72 from bars 0-20 (orderly decline window), fades after Stage 1 entry
    slope_pct: flat at -0.0015 from bars 0-20, then set to 0 after bar 20 (gate already stored)
    Show threshold lines: R² = 0.45 (dashed), slope_pct = -0.001 (dashed)

  Gate status panel (Panel 5):
    bars 0-19:    Macro: PASS, Channel: computing, Divergence: IDLE, Cascade: waiting
    bars 20-74:   Macro: PASS, Channel: PASS (stored at bar 20), Divergence: IN PROGRESS, Cascade: waiting
    bars 75+:     ALL FOUR: PASS — signal fires

---

## File to Build

### scripts/build_visualize_v4_layers.py
  - Read existing scripts/visualize_strategy_perspectives.py first for style reference
  - Writes scripts/visualize_v4_layers.py
  - After writing: py_compile.compile + ast.parse (both must pass)
  - Checks file existence first — aborts if file already exists
  - Does NOT run the script

### scripts/visualize_v4_layers.py
  - Standalone: `python scripts/visualize_v4_layers.py` runs and saves the PNG
  - Uses matplotlib only. No pandas, no real market data.
  - All synthetic data built with numpy (np.linspace, np.clip, np.random)
  - Results dir: ROOT / "results" / "strategy_perspectives" — mkdir if needed
  - Print full absolute path of saved PNG on completion

---

## Style Rules (from existing visualizers)

- Figure size: (16, 20) or similar tall aspect
- Background: dark (#1a1a2e or similar dark navy)
- Price line: white or light gray
- Stochastic lines: cyan for stoch_9, yellow for stoch_40, magenta for stoch_60
- Oversold zones: red fill below 25, overbought zones: green fill above 75
- Gate pass markers: bright green filled circles, gate fail: red X markers
- Entry triangle: bright green upward triangle (marker='^', size=15)
- Threshold lines: dashed white, alpha=0.5
- Annotation box: semi-transparent dark background, white text, monospace font
- Each panel: y-label on left, minimal x-ticks (every 20 bars), shared x-axis

---

## Hard Rules
- NEVER use escaped quotes in f-strings inside build scripts. Use string concatenation.
- py_compile + ast.parse must both pass before reporting [PASS].
- NEVER overwrite existing files. Check with os.path.exists() first.
- Every function must have a one-line docstring.
- All printed paths must be full absolute Windows paths.
- No emojis anywhere in any file.
- Do NOT run Python scripts via Bash. Only py_compile one-liners are permitted via Bash.
- Use pathlib.Path for all paths. No backslash strings.

## Output
Deliver: build script file path + full build script content.
Run command:
  python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_visualize_v4_layers.py"
Then run:
  python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_v4_layers.py"
Confirm PNG saved at results/strategy_perspectives/V4_four_layer_signal.png
```

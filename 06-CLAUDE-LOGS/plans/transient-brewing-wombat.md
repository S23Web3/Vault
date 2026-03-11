# Plan: visualize_strategy_perspectives_v2.py — S1–S11 Full Catalogue

**Date:** 2026-03-07
**Plan file (system):** C:\Users\User\.claude\plans\transient-brewing-wombat.md
**Plan file (vault):** C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-strategy-catalogue-s6-s11-plan.md

---

## Context

Previous session built `visualize_strategy_perspectives.py` (v1) containing S1–S5.
Research is complete for S6–S11 (plan file: `2026-03-07-strategy-catalogue-s6-s11-plan.md`).
This session builds v2 — a single new file containing all 11 strategy perspectives.
v1 is NOT touched.

---

## Target File

```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives_v2.py
```

Output directory: `results/strategy_perspectives/` (11 PNGs total)

---

## What Gets Built

### Shared infrastructure (ported verbatim from v1)
All helpers, color constants, and utility functions from v1:
- Color constants: `DARK_BG`, `DARK_CARD`, `DARK_PANEL`, `CLR_*`, `ZONE_HIGH`, `ZONE_LOW`
- `shaped()`, `shaped_ind()`, `sloped()`
- `style_ax()`, `zone_fill()`, `save_fig()`, `annotate_box()`

### S1–S5 (ported verbatim from v1)
Functions `build_s1` through `build_s5` copied exactly — no logic changes.

### S6–S11 (new functions)

**S6 — Ripster EMA Cloud System**
- Panels: Price (Cloud 3 fill + Cloud 2 lines + entry arrows), Cloud 2 delta, Volume bar
- Key annotation: "ABOVE CLOUD 3 = LONG ONLY zone"
- Data: price trending up; cloud3_top/bot (34/50) as fill; cloud2_top/bot (5/12) as lines; cloud2_delta panel; rel_volume bar chart with 20% threshold line

**S7 — Quad Rotation Stochastic**
- Panels: All 4 stochs colour-coded in one panel (CLR_FAST/CLR_SLOW/CLR_MACRO/CLR_EMA); alignment count background shade; divergence markers on fast stoch
- Key annotation: "4/4 ALIGNED = full consensus | DIVERGENCE from extreme = signal"
- Data: s9 fast-cycling; s14 standard; s40 medium; s60 slow macro; alignment count (0–4) as background alpha shade; divergence markers where price makes lower low but stoch makes higher low

**S8 — Core Three Pillars Framework**
- Panels: Price (Cloud 3 fill + AVWAP line); BBWP squeeze panel; Stoch 55 panel
- Key annotation: two scenarios — "CONTINUES = hold" and "DECLINES = exit small win"
- Data: price above cloud3; avwap from swing low; bbwp (squeeze < 10% shaded blue, expanding shaded green); stoch55 shaped to show cross then both continuation and decline scenarios side by side

**S9 — BBWP Volatility Filter**
- Panels: BBWP line with spectrum coloring (blue → green → yellow → red); MA line; background shading at extremes
- Key annotation: "FILTER ONLY — state gates entry, does not set direction"
- Data: bbwp line; ma5 (white); spectrum color mapping (< 25 = blue, 25–75 = green/yellow gradient, > 75 = red); state label text annotations at key transitions (BLUE DOUBLE, MA CROSS UP, etc.)

**S10 — ATR SL 3-Phase Cloud Progression**
- Panels: Price (vertical lines at phase transitions; SL line changes style per phase); TP line (removed at P3); Cloud 2 cross event panel
- Key annotation: "Each cloud cross advances the phase — SL only moves in trade's favor"
- Data: price trending; SL line: red solid (P0) → dotted (P1) → dashed (P2) → yellow trail (P3 ATR trail); TP line: solid → dotted → dashed → NaN at P3; cloud2_delta panel showing cross events at phase transitions

**S11 — AVWAP Confirmation**
- Panels: Price (3 AVWAP lines from high/low/vol event + quality score text); Volume bar + VSA ratio threshold; Anchor quality scoring bars (HIGH/MEDIUM/LOW)
- Key annotation: "3 simultaneous AVWAPs — complementary views, not competing signals"
- Data: price with 3 avwap lines (different colors); VSA markers (stopping volume, spring, upthrust); volume bar chart with VSA threshold line; quality panel: 3 bars at scores 85 (high), 55 (medium), 30 (low) with zone shading

### `main()` (updated from v1)
Calls all 11 build functions in sequence. Same output dir pattern as v1.

---

## Implementation Notes

1. **Write tool directly** — NOT a build script (avoids triple-quoted string trap; file is ~700 lines)
2. **No backslash paths in docstring** — forward slashes or pathlib only
3. **All defs have one-line docstrings** — mandatory
4. **No `\n` inside string literals** — use `|` separator in title strings
5. **Color assignments for new panels:**
   - Cloud 3 fill: `CLR_EMA` (cyan) at low alpha
   - Cloud 2 lines: `CLR_CLOUD2` (dark green) — upgrade to a visible color: use `#34d399` (emerald)
   - AVWAP from high: `CLR_SL` (red)
   - AVWAP from low: `CLR_TP` (green)
   - AVWAP from vol event: `CLR_TRAIL` (purple)
   - BBWP: `CLR_BBW` (light green base)
   - Alignment shade: alpha-scaled fill using CLR_TP (green = bullish consensus)
   - Phase SL colors: P0=CLR_SL, P1=CLR_BE (amber), P2=CLR_TRAIL, P3=`#facc15` (yellow)

---

## Critical Files

| File | Role |
|------|------|
| `PROJECTS/four-pillars-backtester/scripts/visualize_strategy_perspectives.py` | v1 — DO NOT TOUCH |
| `PROJECTS/four-pillars-backtester/scripts/visualize_strategy_perspectives_v2.py` | TARGET (new file) |
| `06-CLAUDE-LOGS/plans/2026-03-07-strategy-catalogue-s6-s11-plan.md` | S6–S11 perspective spec |

---

## Verification

```
# Step 1 — syntax check
python -c "import py_compile; py_compile.compile(r'C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives_v2.py', doraise=True)"

# Step 2 — run
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/visualize_strategy_perspectives_v2.py

# Expected: 11 lines "  Saved: ..." printed, 11 PNGs in results/strategy_perspectives/
```

---

## Session Log

Append to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-strategy-catalogue-visual-plan.md`
Use Edit tool only — never Write.

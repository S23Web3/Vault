# V4 Scenario Map — All Possible Signal Paths

## Goal
Build a single large PNG ("map") showing all 7 possible outcomes of the V4 four-layer signal pipeline, arranged as a multi-tier grid with a decision-tree header.

## Output
- `results/strategy_perspectives/V4_scenario_map.png` (poster-sized ~4400x3120px)

## Files to Create
| File | Role |
|------|------|
| `scripts/visualize_v4_scenario_map.py` | Main visualizer (Write tool — embedded `\n`) |
| `scripts/build_v4_scenario_map.py` | Validation only (py_compile + ast.parse) |

## 7 Scenarios

| # | Name | What Fails | Gate Strip |
|---|------|-----------|------------|
| S1 | ALL PASS | Nothing — signal fires | L1-L4 all GREEN |
| S2 | MACRO FAIL | External filter rejects | L1 RED, L2-L4 grey |
| S3 | CHANNEL: V-bottom | R² < 0.45 (chaotic price) | L1 GREEN, L2 RED, L3-L4 grey |
| S4 | CHANNEL: Chop | slope near 0 (flat/ranging) | L1 GREEN, L2 RED, L3-L4 grey |
| S5 | DIVERGE: No HL | stoch_9 C2 low < C1 low | L1-L2 GREEN, L3 RED, L4 grey |
| S6 | DIVERGE: Single cycle | Only one oversold visit | L1-L2 GREEN, L3 RED, L4 grey |
| S7 | CASCADE: V-bottom | stoch_40 < 30 at signal | L1-L3 GREEN, L4 RED |

## Figure Layout

```
+============================================================+
|  DECISION TREE HEADER (full width)                          |
|  [MACRO]-->[CHANNEL]-->[DIVERGE]-->[CASCADE]-->[SIGNAL]     |
|    |FAIL     |FAIL        |FAIL       |FAIL                |
|    S2        S3/S4        S5/S6       S7                    |
+============================================================+
| S1: ALL PASS | S2: MACRO  | S3: V-bot  | S4: Chop         |
| [price]      | [price dim]| [price jag] | [price flat]     |
| [stoch_9 HL] | [BLOCKED]  | [R-sq<0.45] | [slope~0]        |
| [gate strip] | [gate]     | [gate]      | [gate]           |
+============================================================+
| S5: No HL    | S6: 1 Cyc  | S7: CASCADE | LEGEND           |
| [price]      | [price]    | [price]     | [color key]      |
| [s9 LL fail] | [s9 wait]  | [s9+s40]    | [gate meanings]  |
| [gate strip] | [gate]     | [gate]      | [pipeline text]  |
+============================================================+
```

**Outer GridSpec**: 3 rows x 1 col — `height_ratios=[1.0, 5.0, 5.0]`
**Inner GridSpec** (per scenario row): 3 rows x 4 cols — `height_ratios=[3.0, 1.8, 0.5]`
**Figure size**: `figsize=(34, 24)` at `dpi=130`

## Per-Scenario Cell Structure
Each cell = 3 sub-panels:
1. **Price panel** (top, tallest): Price + overlays relevant to scenario
2. **Indicator panel** (mid): The specific indicator that passes/fails
3. **Gate strip** (bottom, thin): 4 horizontal colored bars (L1-L4)

## Key Visual Distinctions
- **S1**: Green entry arrow, stoch_9 divergence arrows pointing UP (HL)
- **S2**: Dimmed/greyed price, "BLOCKED" overlay, only L1 red
- **S3**: Jagged/chaotic price, wide scatter around regression line
- **S4**: Flat/ranging price, horizontal regression line
- **S5**: Two stoch_9 dips but red arrow DOWN (LL, no divergence)
- **S6**: One stoch_9 dip, amber "WAITING" zone after exit
- **S7**: stoch_9 + stoch_40 overlaid, stoch_40 below 30 at signal

## Style
- Same dark theme as all existing visualizers
- Reuse: `shaped()`, `shaped_ind()`, `style_ax()`, `annotate_box()`, `save_fig()`
- N=80 bars per scenario (compact vs 120 in full chart)
- Green border/title for S1 (PASS), red for S2-S7 (FAIL)

## Implementation Steps
1. Write `visualize_v4_scenario_map.py` via Write tool
2. Write `build_v4_scenario_map.py` validation script
3. Run build validation (py_compile + ast.parse)
4. Run visualizer to generate PNG
5. Verify output file exists

# Strategy Visualization Skill

**Use this skill when asked to visualize, draw, or diagram any trading strategy.**

Triggers: "draw the strategy", "visualize scenarios", "show me the lifecycle", "scenario plots", "strategy perspectives", "draw perspectives"

---

## What This Skill Does

Takes any trading strategy description and produces a sequence of matplotlib PNG plots — one per possible trade outcome — showing price action, stop loss movement, take profit targets, and signal indicators in sync.

The user describes their strategy. You extract the lifecycle. You build the plots.

---

## Step 1: Extract the Lifecycle

Before writing any code, ask the user (or infer from context) these questions:

**Entry**
- What is the entry signal?
- Long only, short only, or both?

**Initial SL**
- Where is the initial stop loss placed? (e.g., ATR multiple, swing low, fixed pips)

**Breakeven**
- Does BE exist? What triggers it? (e.g., price moves X in favor, specific bar count)

**Trail Phase**
- What triggers the trailing phase? (bar count, indicator signal, price level)
- How is the trail computed? (ATR, AVWAP, chandelier, manual level)
- Does the trail ratchet (only moves in favor) or follow continuously?
- What signal triggers each ratchet tighten?

**Take Profit**
- Is there a TP? What level? (fixed ATR, structure level, indicator line)
- Does TP activate immediately or after N ratchets?
- Does the TP target move with price (e.g., EMA-based) or stay fixed?

**Signal Indicator**
- What indicator drives the ratchet/exit signal? (stochastic, RSI, MACD, etc.)
- What are the overzone thresholds? (e.g., RSI > 70, stoch < 20)
- What does overzone EXIT mean for this strategy? (continuation or exhaustion?)

---

## Step 2: Map to Scenarios

Every strategy produces the same **7 core outcome scenarios per side**:

| # | Scenario | When it happens |
|---|----------|-----------------|
| 1 | Phase 1 SL | Stopped before any trail/BE kicks in |
| 2 | BE exit | Price goes positive, BE fires, pulls back to BE |
| 3 | Trail floor hit | Trail active, price reverses to hit trail SL |
| 4 | One ratchet, then stopped | Trail tightens once, then price reverses |
| 5 | Full ratchet count + TP hit | Enough ratchets to activate TP, price reaches it |
| 6 | Extra ratchets + TP hit | Rare extended trend, extra ratchet(s) before TP |
| 7 | Full ratchet count + reversal | TP activates but price never gets there, SL hit |

If strategy is both sides: 14 scenarios total (7 long + 7 short).
If one side only: 7 scenarios.

---

## Step 3: Design Price & Indicator Shapes

For each scenario, define **waypoints** — (bar, price) pairs that describe the intended price shape. Connect them with interpolation and add light noise.

**Rules for waypoints:**
- Legs (trending moves): 8-15 bars, steady slope
- Pullbacks: 4-8 bars, retrace 30-50% of prior leg
- SL hits: waypoint lands at the SL level naturally (no array overrides)
- TP hits: waypoint crosses the TP line naturally
- Indicator must match price: oversold during pullbacks (long), overbought during bounces (short)
- TP/trailing lines that are EMA-based MUST slope with the trend — never flat

**Price builder:**
```python
def shaped_price(waypoints, n_bars, noise_pct=0.0015, seed=42):
    """Interpolate waypoints into a smooth price curve with light noise."""
    rng = np.random.default_rng(seed)
    wp_bars = np.array([w[0] for w in waypoints], dtype=float)
    wp_prices = np.array([w[1] for w in waypoints], dtype=float)
    prices = np.interp(np.arange(n_bars, dtype=float), wp_bars, wp_prices)
    noise = rng.normal(0, wp_prices[0] * noise_pct, n_bars)
    noise = np.convolve(noise, np.ones(3) / 3, mode="same")
    return prices + noise
```

**Indicator builder (same pattern):**
```python
def shaped_indicator(waypoints, n_bars, noise_amp=3.0, seed=42):
    """Interpolate waypoints into a smooth indicator curve with noise."""
    rng = np.random.default_rng(seed)
    wp_bars = np.array([w[0] for w in waypoints], dtype=float)
    wp_vals = np.array([w[1] for w in waypoints], dtype=float)
    vals = np.interp(np.arange(n_bars, dtype=float), wp_bars, wp_vals)
    noise = rng.normal(0, noise_amp, n_bars)
    noise = np.convolve(noise, np.ones(3) / 3, mode="same")
    return np.clip(vals + noise, 0, 100)
```

**Sloped reference line (for EMA-based TP/trail targets):**
```python
def sloped_line(start_bar, start_val, end_bar, end_val, n_bars):
    """Linear slope across bar range; NaN outside."""
    line = np.full(n_bars, np.nan)
    for i in range(max(0, start_bar), min(n_bars, end_bar + 1)):
        t = (i - start_bar) / max(end_bar - start_bar, 1)
        line[i] = start_val + t * (end_val - start_val)
    return line
```

---

## Step 4: Plot Structure

Each figure: 2 subplots stacked (3:1 height ratio).

**Top — Price panel:**
- Price line (white)
- Entry triangle (green up = long, red down = short)
- Entry price dashed horizontal line
- SL as a stepped line (red) — steps at each transition point
- BE level dotted line (amber) if applicable
- Trail anchor diamond marker (purple) if applicable
- Ratchet diamond markers labeled R1, R2... (purple)
- TP reference line (green dashed) — SLOPED if EMA-based
- Any structural reference line (e.g., EMA band, VWAP) — SLOPED
- Exit X marker (green = TP, red = SL/BE)
- Description box top-left (2-3 lines, what happens in this scenario)

**Bottom — Indicator panel:**
- Signal indicator curve (orange)
- Overzone threshold line (red dashed)
- Overzone shading (red fill at 10% alpha)
- Vertical dotted lines at ratchet bars (purple, aligns with top panel)

**Dark theme:**
```python
DARK_BG   = "#0f1419"
DARK_CARD = "#1a1f26"
CLR_PRICE = "#e7e9ea"
CLR_SL    = "#ef4444"
CLR_BE    = "#f59e0b"
CLR_TRAIL = "#8b5cf6"
CLR_TP    = "#10b981"
CLR_ENTRY = "#6b7280"
CLR_IND   = "#f97316"
CLR_REF   = "#22d3ee"
```

---

## Step 5: Output

- Script: `scripts/visualize_<strategy_name>.py`
- Output dir: `results/<strategy_name>/`
- Files: `scenario_01.png` through `scenario_NN.png`
- Run: `python scripts/visualize_<strategy_name>.py`
- `validate_output(path)` must pass before delivering — runs py_compile + ast.parse on the output file

---

## Checklist Before Generating

- [ ] All lifecycle phases extracted from user's description
- [ ] 7 scenarios mapped per side
- [ ] Each scenario has a price waypoint list (shape makes sense)
- [ ] Indicator waypoints match price action (oversold during pullbacks, etc.)
- [ ] EMA/VWAP reference lines are SLOPED, never flat axhline
- [ ] SL stepped line only ratchets in the favorable direction (never against trade)
- [ ] Dark theme applied to all axes
- [ ] `validate_output(path)` passes — py_compile + ast.parse on the output file (not the build script)

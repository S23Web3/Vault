# Chart Reading Skill
**Created:** 2026-02-23  
**Scope:** Reading trading charts accurately for strategy analysis  
**Applies to:** All chart analysis in any Claude session  

---

## Core Rules

### 1. Read left to right
Charts are always read left to right unless explicitly instructed otherwise. Time flows left to right. Older price action is on the left, newer is on the right.

### 2. Numbers are truth, visuals are helpers
Always extract the actual numeric values from the chart first. Colors, shapes, and visual positions are secondary and can mislead. Never conclude from color alone — confirm with the number.

- Wrong: "The BBWP is in the red zone" (concluded from color)
- Right: "BBWP white = 55%, green = 57.20% — mid range" (concluded from numbers)

### 3. State what you can read, flag what you cannot
If a value is not clearly readable, say so explicitly. Do not infer, estimate, or assume. Use "unknown" or "not readable" for any value that cannot be confirmed from the chart.

### 4. Extract all values before drawing conclusions
Read every panel on the chart completely before interpreting any of it. Partial reads lead to wrong conclusions.

### 5. Wrong readings cost money
Chart reading errors in trading context have direct financial consequences. There are no acceptable shortcuts.

---

## Reading Order Per Chart

**Step 1 — Identify the chart:**
- Asset name and pair
- Timeframe (1m, 5m, etc.)
- Exchange
- Time range visible (left edge to right edge)
- Any reference markers (dashed lines, vertical lines, annotations)

**Step 2 — Read the price panel (top):**
- Current price / last close
- OHLC if visible
- EMA/cloud levels and their values
- Price position relative to each cloud/EMA (above, below, inside)
- Notable candles (size, color, wicks) — state bar count and % move if shown
- Volume if present
- Any labels, arrows, or annotations with their exact values

**Step 3 — Read each indicator panel in order top to bottom:**
For each panel state:
- Indicator name and parameters exactly as shown
- Current K value
- Current D value (if present)
- Position relative to key levels (oversold line, 50 line, overbought line)
- K above or below D
- Direction of movement (rising, falling, flat) — read from the curve shape left to right
- Any zone the indicator is in (oversold / mid / overbought) — confirmed by number, not color

**Step 4 — Read BBW/BBWP panel:**
- White line value
- Green line value
- Blue line value if present
- Zone: low (<20%), mid (20-70%), high expansion (>70%) — based on number
- Direction: compressing or expanding — read from curve left to right

**Step 5 — Read ATR panel if present:**
- Current ATR value
- Whether rising or falling

**Step 6 — Read any additional panels (TDI, volume, etc.):**
- State indicator name and parameters
- State values as readable

**Step 7 — State findings, then interpret:**
Only after all values are extracted: draw conclusions about what the chart shows.

---

## Stochastic Reading Reference (Four Pillars)

| Stochastic | Parameters | Oversold | Overbought | Mid |
|------------|-----------|----------|------------|-----|
| K1 | 9, 1, 3 | <20 | >80 | 20-80 |
| K2 | 14, 1, 3 | <20 | >80 | 20-80 |
| K3 | 40, 1, 3 | <20 | >80 | 20-80 |
| K4 | 60, 1, 10 | <20 | >80 | 20-80 |

Always state K and D values separately. K above D = bullish momentum. K below D = bearish momentum.

---

## Common Errors to Avoid

| Error | Correct behaviour |
|-------|-----------------|
| Reading color instead of value | Extract the number, state the number |
| Calling all stochastics oversold without reading each | Read each panel individually |
| Inferring BBW zone from visual color | State the percentage, derive the zone from the number |
| Skipping panels that seem unimportant | Read every panel, flag unknown if not readable |
| Drawing conclusions before reading all panels | Complete full read first, interpret after |
| Estimating a value because it looks approximate | Say "not clearly readable" |

---

## Output Format When Reading a Chart

```
CHART: [Asset] [Timeframe] [Exchange]
TIME RANGE: [left edge] to [right edge]
REFERENCE POINT: [description of any marked point]

PRICE PANEL:
- Price: [value]
- Cloud/EMA levels: [each with value and price relation]
- Notable candles: [description with values if annotated]

INDICATORS (top to bottom):
- [Name params]: K=[value] D=[value] | Zone=[oversold/mid/overbought] | K [above/below] D | Direction=[rising/falling/flat]
- [repeat for each]

BBWP:
- White=[value]% Green=[value]% | Zone=[low/mid/high] | Direction=[compressing/expanding]

ATR: [value] | Direction=[rising/falling]

FINDINGS:
[State what the chart shows, based only on the values above]
```

---

## Notes
- This skill applies to all chart reading regardless of asset, timeframe, or exchange
- When in doubt, read again before concluding
- If a chart is unclear or low resolution, state that before attempting to read it

---
name: market-volume-profile
description: Expert-level market structure analysis using Market Profile (TPO) and Volume Profile. Use when analyzing price distribution, identifying balance/imbalance conditions, recognizing auction completion via excess, finding trade location based on value areas, POC, and volume nodes. Applies to crypto perpetual futures, equities, forex, and any liquid market. Triggers on terms like "volume profile", "market profile", "TPO", "value area", "POC", "excess", "balance area", "fair value", "auction theory".
---

# Market Profile & Volume Profile Analysis

## Core Framework: Auction Market Theory

Markets are continuous two-way auctions facilitating trade between buyers and sellers. Price moves until it finds acceptance (volume accumulates) or rejection (price reverses). This simple mechanism produces all market structure.

### The Three Building Blocks
1. **Price** — the advertising mechanism (vertical axis)
2. **Time** — measures acceptance/rejection duration (horizontal axis in TPO)
3. **Volume** — measures conviction and acceptance (horizontal histogram in VP)

### Market Profile vs Volume Profile
| Aspect | Market Profile (TPO) | Volume Profile |
|--------|---------------------|----------------|
| Measurement | Time spent at price | Volume traded at price |
| Display | Letter-based 30-min brackets | Horizontal volume histogram | 
| Strength | Shows time-based acceptance | Shows actual transaction volume |
| Best for | Understanding auction structure | Identifying institutional levels |

Use both together: TPO for structure visualization, VP for volume confirmation.

### Visual: Volume Profile with POC
![[images/volume-at-price-poc.jpg]]
*Volume Profile showing Point of Control (POC) - the price with highest traded volume*

---

## The Balance-Imbalance-Excess Framework (1-2-3)

### 1. BALANCE — Market Equilibrium

**Definition**: Buyers and sellers agree on value. Price oscillates around a central mean with two-sided trade.

![[images/balanced-market-profile.png]]
*Balanced market profile - symmetrical bell curve showing two-sided trade*

**Recognition**:
- Symmetrical bell-curve profile shape
- Overlapping value areas across multiple sessions
- Price contained within well-defined bracket extremes
- Volume concentrated at center (POC area)
- Low volatility, narrow range days

**Trading Balance**:
- Fade moves to bracket extremes
- Buy lower bracket extreme, sell upper extreme
- Expect mean reversion
- Lower volume at extremes confirms containment

**Key Insight**: Markets spend 70-80% of time in balance. Balance areas act as "gravitational centers" — price tends to return to established value.

<!-- YOUR_SCREENSHOT: Add your own balanced market example from TradingView here -->
<!-- Example filename: my-btc-balance-2025-01-xx.png -->

---

### 2. IMBALANCE — Directional Conviction

**Definition**: One side dominates. Price moves directionally as the market seeks new value levels.

![[images/trending-market-profile.png]]
*Trending/imbalanced profile - elongated shape showing directional conviction*

**Recognition**:
- Elongated, non-symmetrical profile shapes
- Value area migration (higher highs in value, not just price)
- Range extension beyond initial balance
- Increasing volume in direction of move
- P-shape (buyers dominating) or b-shape (sellers dominating)
- "Stacked imbalances" in footprint charts

**Types of Imbalance**:

| Type | Profile Shape | Meaning |
|------|---------------|---------|
| **Trend Day** | Narrow, elongated | Strong conviction, one direction |
| **P-Profile** | Fat top, thin bottom | Buying pressure, potential bullish |
| **b-Profile** | Thin top, fat bottom | Selling pressure, potential bearish |

#### P-Profile Shape
![[images/p-profile-shape.png]]
*P-Profile: Fat top (OPENING area), thin bottom - indicates buying pressure/short covering*

#### b-Profile Shape
![[images/b-profile-shape.png]]
*b-Profile: Fat bottom (OPENING), thin top (CLOSE) - indicates selling pressure/long liquidation*

**Trading Imbalance**:
- Go with the auction, not against it
- Don't fade trend days
- Look for continuation after balance-area breakouts
- Monitor volume: increasing volume = continuation likely

**Inventory Imbalance**:
- When market gets "too short" → needs rally before further decline
- When market gets "too long" → needs pullback before further rally
- Multiple lows at same level without excess = inventory imbalance
- Short covering produces P-shaped profiles
- Long liquidation produces b-shaped profiles

<!-- YOUR_SCREENSHOT: Add your own P or b profile example here -->

---

### 3. EXCESS — Auction Completion

**Definition**: The market has gone "too far" — price advertised beyond where participants are willing to transact. Marks the END of one auction and BEGINNING of another.

![[images/profile-key-elements.jpg]]
*Key profile elements: Range Extension, Initial Balance, Buying Tail (excess)*

**Recognition**:
- Sharp price spike on LOW volume (not high!)
- Single prints / single TPO zones (rapid price movement, no time for volume)
- Immediate aggressive reversal by opposing side
- Buying tails (rapid reversal from lows)
- Selling tails (rapid reversal from highs)
- Gaps (extreme form of excess)

**Critical Insight**: Excess occurs on LOW volume because the final bidder/seller is ALONE. The spike represents the last participant, not capitulation.

**Trading Excess**:
- Excess marks ideal entry/exit points (asymmetric risk/reward)
- Wait for confirmation: next session should not challenge excess
- Gaps at auction ends signal "reorganization of beliefs"
- After excess, expect auction in opposite direction

**Validating Excess**:
1. Did excess occur on declining volume in direction of move?
2. Was there immediate aggressive response from opposite side?
3. Does next session fail to challenge the excess level?
4. Is value (not just price) accepting new direction?

<!-- YOUR_SCREENSHOT: Add your own excess/tail reversal example here -->

---

## Key Structure Elements

### Value Area (70% Rule)

![[images/value-area-calculation.png]]
*Value Area calculation - 70% of TPOs, starting from POC*

- Range containing ~70% of volume/TPOs
- Represents one standard deviation of accepted value
- **VAH** (Value Area High) — upper boundary
- **VAL** (Value Area Low) — lower boundary
- Price within VA = fair value; outside = opportunity

### Value Area High/Low Visual
![[images/value-area-high-low.jpg]]
*VAH and VAL clearly marked on volume profile*

### Value Area Relationships
![[images/value-area-relationships.png]]
*All possible value area relationships: Higher, Lower, Overlapping Higher/Lower, Outside, Inside*

### Point of Control (POC/VPOC)
- Single price level with highest volume/longest TPO line
- Represents "fairest price" where most trade occurred
- **Naked POC**: Previous day's POC not revisited → acts as magnet
- Strong POCs create gravitational pull; price tends to return
- Rising POC = value migration up; Falling POC = value migration down

#### Naked POC Example
![[images/naked-poc-example.jpg]]
*Naked POC from previous session acts as magnet - price returns to test it*

### Initial Balance (IB)

![[images/range-extension-selling.png]]
*Initial Balance (B-C periods) followed by range extension in G period*

- First hour of trading range (first two 30-min periods)
- Sets framework for the session
- **Range Extension**: Price breaking beyond IB signals conviction
  - Upward extension on increasing volume = real buying
  - Downward extension on increasing volume = real selling
  - Extension on decreasing volume = likely to fail

### Single Prints / Low Volume Nodes (LVN)
- Prices where market moved quickly (minimal time/volume)
- Act as "air pockets" — price moves fast through them
- Often revisited and then rejected
- In VP: thin horizontal sections
- In MP: single letter rows

### High Volume Nodes (HVN)

![[images/high-volume-area-support.jpg]]
*High Volume Area acts as support - price returns to test it*

- Price levels with concentrated volume
- Act as support/resistance
- Price tends to "stick" at HVNs
- Multiple HVNs at same level across sessions = strong reference

### VAH as Future Support
![[images/vah-as-support.jpg]]
*Previous VAH becomes support level in subsequent sessions*

---

## Profile Shapes Reference

| Shape | Description | Market Condition | Trading Implication |
|-------|-------------|------------------|---------------------|
| **Normal/Bell** | Symmetrical, fat middle | Balanced | Mean reversion, fade extremes |
| **P-Shape** | Fat top, thin bottom | Short covering OR bullish breakout | Context-dependent: early trend = bullish; late trend = exhaustion |
| **b-Shape** | Thin top, fat bottom | Long liquidation OR bearish breakout | Context-dependent: early trend = bearish; late trend = exhaustion |
| **D-Shape** | Very fat, symmetrical | Inside day, tight balance | Breakout imminent, trade the breakout |
| **Elongated** | Narrow, tall | Trend day | Don't fade; go with direction |
| **Double Distribution** | Two distinct value areas | Trend day with pause | Strong conviction, continuation expected |

<!-- YOUR_SCREENSHOT: Add examples of each profile shape from your trading -->

---

## Day Types Framework

### Trend Day
- One-directional move throughout session
- Elongated profile, minimal rotation
- Opens at one extreme, closes at other
- **Never fade a trend day**

### Normal Day
- Opens with range, establishes value, rotates
- Balanced profile shape
- Good for scalping bracket extremes

### Normal Variation Day
- Starts balanced, then extends one direction
- Range extension with acceptance at new level
- Partial trend characteristics

### Neutral Day
- Inside day, tight range
- Profile contained within previous day
- Signals consolidation before next move
- **Trade any breakout from neutral day**

<!-- YOUR_SCREENSHOT: Add examples of each day type -->

---

## Volume Analysis Checklist

### Continuation Signals
✓ Higher prices attract higher volume
✓ Value area migrating in direction of trend
✓ Successive balance areas with space between them
✓ Profile elongating in direction of move

### Reversal/Exhaustion Signals
✓ New price highs/lows on DECREASING volume
✓ Overlapping balance areas (stacking)
✓ Counter-trend auctions equal or stronger than with-trend
✓ P or b formations appearing late in trend
✓ Failed range extension (price returns to IB)

---

## Practical Trading Rules

### For Bracket/Balance Markets
1. Identify bracket extremes (high/low)
2. Fade auctions to extremes on decreasing volume
3. Expect responsive buying at lows, selling at highs
4. Go with breakout if volume supports (increasing)

### For Trending Markets
5. Go with the trend, don't fade
6. Use pullbacks to balance areas as entry points
7. Monitor balance area spacing (closer = aging trend)
8. Exit when excess forms or volume diverges

### Reference Point Hierarchy
1. **Naked POCs** — strong magnets
2. **Previous Day VAH/VAL** — key decision levels
3. **Session Highs/Lows** — stop placement reference
4. **Gap fills** — unfilled gaps attract price
5. **Single print zones** — fast move areas, revisit likely

### Entry Checklist
- [ ] What is the longer-term auction direction?
- [ ] Where is price relative to value?
- [ ] Is volume supporting attempted direction?
- [ ] Is profile shape suggesting continuation or exhaustion?
- [ ] What is the risk/reward based on structure?

---

## Crypto-Specific Considerations

### 24/7 Market Adjustments
- Use session-based profiles (Asia, London, NY) not calendar days
- Globex-style overnight ranges matter
- Weekly and monthly composite profiles for HTF context

### Perpetual Futures Nuances
- Funding rate influences inventory positioning
- Open interest changes signal positioning, not just volume
- Liquidation cascades create extreme excess quickly

### Volatility Adaptation
- Wider value areas during high volatility
- Tighter initial balance during consolidation
- Scale position size to volatility, not fixed amounts

---

# Trading Setups & Patterns

## Setup 1: Bracket Extreme Fade

**Context**: Market in established balance (multiple days of overlapping value areas)

![[images/balanced-profile-basic.png]]
*Balanced profile - fade extremes back to POC*

**Entry Conditions**:
1. Price reaches upper or lower bracket extreme
2. Volume DECREASING as extreme is tested
3. Profile showing rejection (tails forming)
4. No range extension with acceptance

**Entry**: Fade the extreme (short at upper, long at lower)
**Stop**: Beyond bracket extreme + buffer
**Target**: POC or opposite extreme
**Risk/Reward**: Typically 1:2 minimum

**Warning Signs to Abort**:
- Volume increasing at extreme
- Multiple time periods accepting at extreme
- Range extension with volume confirmation

<!-- YOUR_SCREENSHOT: Add your own bracket fade trade example -->

---

## Setup 2: Breakout from Balance

**Context**: Market has been balanced, now breaking out

![[images/breakout-from-profile.jpg]]
*Breakout from balance area with POC/TPO reference*

**Entry Conditions**:
1. Price breaks beyond bracket extreme
2. Volume INCREASING on breakout
3. Acceptance (multiple TPOs/time) at new level
4. Value area migrating in direction of break

**Entry**: With the breakout, on first pullback to broken level
**Stop**: Below (for long) or above (for short) the broken level
**Target**: Measured move = bracket width projected from break
**Risk/Reward**: Typically 1:3 or better

**Confirmation Checklist**:
- [ ] Volume higher than average
- [ ] Profile elongating, not balancing
- [ ] No immediate reversal back into balance

<!-- YOUR_SCREENSHOT: Add your own breakout trade example -->

---

## Setup 3: POC Magnet Trade

**Context**: Naked POC from previous session(s) unvisited

![[images/poc-magnet-trade.jpg]]
*Price returns to previous POC acting as magnet*

**Entry Conditions**:
1. Identify naked POC (prior day's POC not touched)
2. Current price moving toward the naked POC
3. Volume supporting directional move
4. No major structure blocking path

**Entry**: Directional trade toward naked POC
**Stop**: Beyond nearest structural level
**Target**: The naked POC
**Risk/Reward**: Based on distance to POC vs stop

**Notes**:
- Naked POCs often act as strong magnets
- Price may overshoot POC before reversing
- Best when aligned with larger timeframe direction

<!-- YOUR_SCREENSHOT: Add your own naked POC trade example -->

---

## Setup 4: Excess Reversal

**Context**: Market has formed clear excess (spike on low volume with immediate reversal)

**Entry Conditions**:
1. Sharp price spike (tail/single prints)
2. Spike occurred on LOW volume
3. Immediate aggressive reversal by opposite side
4. Next session/period does NOT challenge excess

**Entry**: In direction opposite the spike
**Stop**: Beyond the excess extreme
**Target**: VAL (if excess was high) or VAH (if excess was low)
**Risk/Reward**: Often 1:4 or better (asymmetric)

**Key Insight**: The best opportunities feel uncomfortable because you're trading against recent momentum. Trust the structure, not emotions.

<!-- YOUR_SCREENSHOT: Add your own excess reversal trade example - this is your highest R:R setup -->

---

## Setup 5: Value Area Gap Fill

**Context**: Market opens outside previous day's value area

### Scenarios

#### Open Above VA, Stays Above (OA/OC above)
- Bullish bias for continuation
- If price REJECTS return to VA → strong trend day likely
- Don't short early

#### Open Above VA, Falls Back Into (OA/OC within)
- Initial strength rejected
- Fade the open, expect return to POC
- Target: POC, then VAL

#### Open Below VA, Stays Below (OB/OC below)
- Bearish bias for continuation
- If price REJECTS return to VA → strong down trend day likely
- Don't buy early

#### Open Below VA, Rises Back Into (OB/OC within)
- Initial weakness rejected
- Buy the open weakness, expect return to POC
- Target: POC, then VAH

<!-- YOUR_SCREENSHOT: Add gap fill examples for each scenario -->

---

## Setup 6: Initial Balance Breakout

**Context**: First hour establishes range, then extension occurs

**Entry Conditions**:
1. Clear IB established (first 1-2 hours)
2. Price breaks beyond IB high or low
3. Volume supporting the extension
4. No immediate return to IB

**Entry**: On range extension with confirmation
**Stop**: Back inside IB (middle of IB for tighter stop)
**Target**: 1x IB width as first target, 2x as second

**Volume Rules**:
- Extension on HIGH volume → continuation likely → add to position
- Extension on LOW volume → potential trap → tighten stop or exit
- Extension BOTH directions with return to IB → neutral day, stop trading

<!-- YOUR_SCREENSHOT: Add IB breakout example -->

---

## Setup 7: Poor High/Low Recognition

**Definition**: A high or low without clear excess (no tail, no single prints, no volume rejection)

**Recognition**:
- Price stops at level without conviction
- Multiple TPOs at the extreme (not single prints)
- No tail formation
- Volume not declining dramatically

**Trading Implication**: Poor highs/lows will likely be revisited and taken out

**Setup**:
1. Identify poor high/low from previous session
2. Current session approaching that level
3. Look for breakout setup through the poor extreme
4. Enter with the breakout, stop below the broken level
5. Target: Next significant structure level

<!-- YOUR_SCREENSHOT: Add poor high/low example showing how they get taken out -->

---

## Setup 8: P/b Profile Continuation

**Context**: Early trend with P or b shaped profile forming

### P-Profile (Early Bullish Trend)
- Fat top, thin bottom
- Indicates buying activity, shorts covering
- At BEGINNING of trend = bullish continuation
- **Setup**: Buy pullbacks to POC or lower volume node

### b-Profile (Early Bearish Trend)
- Thin top, fat bottom
- Indicates selling activity, longs liquidating
- At BEGINNING of trend = bearish continuation
- **Setup**: Sell rallies to POC or upper volume node

**Warning**: Same shapes LATE in trend indicate exhaustion, not continuation

<!-- YOUR_SCREENSHOT: Add P/b continuation trade examples -->

---

## Setup 9: Inventory Imbalance Recognition

**Symptoms of Too Short**:
- Multiple attempts at lows without excess
- P-shaped profiles appearing
- Short covering rallies (fast, little volume)
- Market "needs to rally before breaking lower"

**Symptoms of Too Long**:
- Multiple attempts at highs without excess
- b-shaped profiles appearing
- Long liquidation breaks (fast, little volume)
- Market "needs to break before rallying higher"

**Trading**:
- Counter-intuitively, trade opposite to the inventory
- When too short → look for long setups
- When too long → look for short setups
- Wait for inventory correction before trend continuation

<!-- YOUR_SCREENSHOT: Add inventory imbalance recognition example -->

---

## Setup 10: Composite Profile Reference Points

**Building Composite Profiles**:
- Combine multiple sessions (3-5 days) into single profile
- Identifies larger timeframe value areas
- Finds multi-session POC (strongest reference)
- Reveals developing trends vs ranges

**Key Levels from Composites**:
1. Composite POC — strongest single reference
2. Composite VAH/VAL — major decision boundaries
3. Multi-session single prints — fast move zones
4. Distribution overlaps — balance confirmation

**Application**:
- Day trade setups should align with composite direction
- Fade moves to composite extremes
- Break of composite value area = significant move likely

<!-- YOUR_SCREENSHOT: Add composite profile with multi-day structure -->

---

## Volume Footprint Patterns

### Stacked Imbalance (Buy Side)
- Multiple consecutive levels showing bid > ask
- Indicates aggressive buying
- Look for continuation in direction of imbalance
- Best when occurring at support levels

### Stacked Imbalance (Sell Side)
- Multiple consecutive levels showing ask > bid
- Indicates aggressive selling
- Look for continuation in direction of imbalance
- Best when occurring at resistance levels

### Absorption
- High volume at level but no price movement
- Large orders being filled without moving price
- Can signal reversal as one side absorbs the other
- Confirm with subsequent price action

### Exhaustion Pattern
- High volume spike followed by immediate reversal
- Volume concentrated at extreme
- New prices not attracting continuation
- Similar to excess but visible in footprint detail

<!-- YOUR_SCREENSHOT: Add footprint chart examples showing these patterns -->

---

## Context Checklist Before Every Trade

1. **Timeframe Alignment**
   - [ ] What is the monthly/weekly auction direction?
   - [ ] What is the daily auction direction?
   - [ ] Am I trading with or against the larger timeframe?

2. **Structure Location**
   - [ ] Where is price relative to composite POC?
   - [ ] Where is price relative to yesterday's value area?
   - [ ] Are there naked POCs nearby?
   - [ ] What is the nearest single print zone?

3. **Volume Confirmation**
   - [ ] Is volume supporting attempted direction?
   - [ ] Is volume increasing or decreasing?
   - [ ] What does footprint show at this level?

4. **Profile Shape**
   - [ ] What shape is today's profile taking?
   - [ ] Does shape match expected continuation or reversal?
   - [ ] Are tails/excess forming?

5. **Risk/Reward**
   - [ ] Where is my stop (structure-based)?
   - [ ] Where is my target (next structure level)?
   - [ ] Is R:R at least 1:2?
   - [ ] Is position size appropriate for volatility?

---

## Quick Reference: Trading Decisions

```
IF market is BALANCED:
  → Fade extremes, buy VAL, sell VAH
  → Expect mean reversion
  → Prepare for eventual breakout

IF market shows IMBALANCE:
  → Go with dominant side
  → Don't fade trend days
  → Watch for profile shape changes (P/b warnings)

IF market shows EXCESS:
  → Mark as potential reversal point
  → Wait for confirmation (next session doesn't challenge)
  → Enter opposite direction with tight stop beyond excess
  → Asymmetric risk/reward opportunity
```

---

## TPO Time Periods Reference

![[images/tpo-time-periods-separated.png]]
*TPO letters showing how profile builds through 30-minute periods*

---

## Sources
- Dalton, J.F. et al. (2007). *Markets in Profile*. Wiley.
- *Volume Profile, Market Profile, Order Flow: Next Generation of Daytrading*

---

## Your Screenshots

Add your own TradingView screenshots in the `images` subfolder. Suggested naming:
- `my-btc-balance-YYYY-MM-DD.png`
- `my-eth-excess-YYYY-MM-DD.png`
- `my-trend-day-YYYY-MM-DD.png`
- `my-poc-magnet-YYYY-MM-DD.png`

Then link them with: `![[images/my-filename.png]]`

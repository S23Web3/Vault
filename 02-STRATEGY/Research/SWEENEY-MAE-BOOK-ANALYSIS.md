# Maximum Adverse Excursion — John Sweeney (1997)
## Complete Book Analysis for Four Pillars Trading System

---

## Book Structure
- **169 pages**, 8 chapters + 10 appendices (A-J) with Excel 4.0 code
- **Data**: 11 years of crude oil futures (Oct 1983 – Oct 1994), daily bars
- **Trading system**: Dual moving average trend-following (only ~30% winners)
- **Publisher**: John Wiley & Sons (Trader's Advantage Series, preface by Perry Kaufman)

---

## Chapter 1: The Idea

### Core Rule
> "Generally, good trades don't go too far against you while bad ones do."

This is Sweeney's seminal observation. If your trading rules can distinguish between good and bad trades, then over many experiences you can measure how far good trades go bad and find the point where a trade is more likely to end badly than profitably.

### Key Principles
1. **Measure from point of entry** — not from support/resistance/value. Entry is the only reference point a speculator truly controls.
2. **Consistent rules required** — MAE analysis only works when trading rules are applied consistently. Random entries produce no pattern.
3. **Statistical, not predictive** — You're looking at the *distribution* of outcomes, not predicting any single trade.
4. **Minimum 30 trades** each for winners and losers to have reasonable confidence.

### Four Pillars Application
Our backtester already measures from entry. The A/B/C grading system gives us consistent rules. With 3,000+ trades per coin on 5m timeframes, we have enormous statistical power compared to Sweeney's 252 trades.

---

## Chapter 2: Defining MAE, MaxFE, MinFE

### Formal Definitions

**MAE (Maximum Adverse Excursion):**
- For longs: `MAE = MAX(0, (Entry price - Lowest subsequent low), Previous MAE)`
- For shorts: `MAE = MAX(0, (Highest subsequent high - Entry price), Previous MAE)`
- The worst the trade goes against you from entry to exit.

**MaxFE (Maximum Favorable Excursion):**
- For longs: `MaxFE = MAX(0, (Highest subsequent high - Entry price), Previous MaxFE)`
- For shorts: `MaxFE = MAX(0, (Entry price - Lowest subsequent low), Previous MaxFE)`
- The best the trade goes in your favor from entry to exit. **This is our MFE.**

**MinFE (Minimum Favorable Excursion):**
- For longs: `MinFE = MAX(0, (Highest subsequent LOW - Entry price), Previous MinFE)`
- For shorts: `MinFE = MAX(0, (Entry price - Lowest subsequent HIGH), Previous MinFE)`
- The *least* favorable the trade gets using the *opposite* end of the bar.
- **Sweeney notes MinFE is often a better indicator of a successful trade than MaxFE.**

### Critical Properties
- MAE, MaxFE, and MinFE **never decrease** during a trade (they use MAX function)
- They **never go below zero**
- On a reversal day, the final MAE belongs to the old trade; the new trade starts fresh

### Four Pillars Application
- Our MFE = Sweeney's MaxFE (already implemented)
- Our MAE = Sweeney's MAE (already implemented)
- **We should add MinFE tracking** — the minimum favorable excursion uses LOW for longs (not HIGH). This is the "weakest high water mark" and may better predict which trades will survive to target. Sweeney says it's often more useful than MaxFE for managing winners.

---

## Chapter 3: Displaying MAE

### The MAE Scatter Plot (Figure 3-1)
- X-axis: Profit or Loss
- Y-axis: MAE value
- Winners cluster in the **lower-right** (small MAE, positive P&L)
- Losers scatter in the **upper-left** (large MAE, negative P&L)
- **The visual separation IS the edge** — if winners and losers have clearly different MAE distributions, your rules can distinguish good from bad trades.

### Frequency Diagrams
- Group trades into **bins** by MAE size
- Plot two histograms: winners vs losers by bin
- **Ideal shape**: Winners have a huge spike in bin 0 (no adverse excursion), dropping rapidly. Losers have a peak shifted right with a long tail.
- The **crossover point** where winners drop off and losers pick up = optimal stop placement.

### Bin Size Guidelines
- Start with **2% of trading capital** as max bin size
- Rule of thumb: **1% of trading capital** works well
- Need enough trades per bin to be meaningful (minimum ~5)
- Too fine = sparse bins; too coarse = missed precision

### From Sweeney's 252 Crude Trades
| Bin (MAE) | Winners | Losers |
|-----------|---------|--------|
| 0.15      | 80      | 21     |
| 0.30      | 17      | 44     |
| 0.45      | 4       | 28     |
| 0.60      | 0       | 28     |
| 0.75      | 0       | 7      |
| 0.90      | 1       | 10     |
| 1.05      | 1       | 2      |
| **Total** | **104** | **148**|

Setting stop at 0.46 would cut off 55 losers and convert only 3 winners to losers.

### Four Pillars Application
- Our backtester dashboard should show this exact scatter plot and frequency diagram
- With ~4,000 trades per coin, our bins can be very fine (ATR fractions)
- **Already doing this conceptually** with LSG analysis — but Sweeney's formalization is more rigorous
- We should show MAE distributions for each grade (A, B, C, Re-entry) separately

---

## Chapter 4: Defining Profit by Bin

### Profit Curves
Instead of just counting trades per bin, **sum the actual P&L** within each bin. This reveals:
- Not just *how many* trades are affected by a stop level, but *how much money*
- One big winner in a high-MAE bin can distort the picture
- The **optimal stop** is where the profit curve peaks

### The Tradeoff
As you **widen** stops:
1. Winners that were being stopped out become winners again (good)
2. Losers that were being stopped out early take bigger losses (bad)
3. Net effect depends on frequency AND size of each

As you **tighten** stops:
1. More winners get stopped out (bad)
2. More losers get stopped out earlier as smaller losses (good)
3. Again, net effect is empirical — must be measured

### The Summary Profit Curve (Figure 4-3)
Sum wins + losses per bin into one curve. Shows the exact point where adverse movement tips from net positive to net negative. This is the **optimal stop/reversal point**.

### Four Pillars Application
**This is EXACTLY our BE trigger optimization (WS4C).** Sweeney's "profit by bin" is the theoretical foundation for our "net impact curve" — sweeping the BE trigger level and plotting net P&L at each level. We're not just validating our approach; Sweeney literally describes it as the core methodology.

The key difference: Sweeney uses fixed-$ stops. We use ATR-based stops + BE raise. But the analytical technique is identical.

---

## Chapter 5: Impact of Volatility Changes

### Range vs. Volatility
- Range (high - low) is a reasonable proxy for classical volatility
- But the relationship is **not rigorous** — range is more direct for stop analysis
- Range expansion is **episodic**, not sustained
- Human perception overestimates range expansion (we remember extremes)

### Key Findings (Crude Oil)
1. **Range doesn't usually expand after entry** on a sustained basis
2. For this data, losers' range actually **contracted** slightly (-0.03)
3. Winners' range **expanded** slightly (+0.08, about 25% of average range)
4. Range expansion is **episodic** — typically only 1-2 days, not sustained
5. **MAE is generally much less than daily range** for winners (ratio ~0.35)

### Should You Adjust Stops for Volatility?
Sweeney's conclusion for crude oil: **Generally no.** The original MAE stops already incorporate the full range of volatility conditions in the data. Expanding stops to accommodate range expansion would admit far more losers than winners.

**Exception**: If your MAE distribution shows winners with a long tail of large MAEs (mixed distributions), volatility adjustment *might* help. But even then, expanding from .45 to 1.05 would be impractical.

**Rule**: If you observe extraordinary ranges (>95th percentile of historical ranges), widen stops by **half the estimated range expansion**.

### Four Pillars Application
- We already use ATR for SL/TP, which is inherently volatility-adaptive
- Sweeney's analysis validates our ATR approach — the stop naturally adjusts
- The "losers contract, winners expand" finding is interesting: might our losing trades show contracted ATR at entry? Worth checking in backtester.
- **Confirms**: Don't over-engineer volatility adjustments. ATR does the heavy lifting.

---

## Chapter 6: Runs Effects

### Capital Conservation
MAE analysis does three things:
1. **Eliminates large losses** (stops catch them)
2. **Tells you how much capital you need** (MAE stop / 0.02 = required capital)
3. **Tells you where to put stops** (from MAE distributions)

But even with controlled losses, **runs of consecutive losses** can destroy a trader.

### Defining Adverse Runs
An **adverse run** = any sequence of trades resulting in equity falling below a previous peak, continuing until a new high in equity is attained.

Measure: `(Maximum equity - Today's equity) / (Capital + Maximum equity)`

### Sweeney's Crude Oil Findings
- With a 30%-win system and .31 MAE stop:
  - 7 major drawdowns in 11 years
  - Most between 4%-8% of capital + winnings
  - Worst: 25% of initial capital (no winnings counted)
  - **70% of drawdowns were 10% or less**
  - **94% were less than 18%**
  - Probability of catastrophic 40% drawdown: **vanishingly small**
- Being in a drawdown state: ~46% of the time (normal for 30%-win systems)

### Drawdown Probability
- Fitted exponential curve to actual drawdown frequencies
- Larger drawdowns become exponentially less likely
- P(25% drawdown on day one) ≈ 0.45 × 0.06 = **3%**
- P(40% drawdown) ≈ **infinitesimal**

### Campaign Trading (Portfolio)
- Trading DMark, Swiss, Yen, Gold with same system:
  - DMark/Swiss correlation: .94 (essentially same trade — avoid doubling)
  - DMark/Yen correlation: .59 (some diversification)
  - DMark/Gold correlation: -.27 (good diversification)
- Combined portfolio: drawdowns steady at 10-15% but never catastrophic
- **Diversification helps** but related tradables (like DMark/Swiss) offer little benefit

### Four Pillars Application
- We trade 339 coins — massive diversification potential
- But crypto coins are often highly correlated (BTC moves everything)
- **Run analysis per coin** should be standard output in our backtester
- Capital requirement: if MAE stop = 1.0 ATR and we want max 2% risk per trade, then:
  `Capital needed = (1.0 ATR × notional) / 0.02`
- With $500 margin × 20x = $10k notional and ATR typically 1-3%, that's $100-$300 per trade risk
- **Our $6/side commission + $500 margin is well within the 2% rule for most coins**

---

## Chapter 7: Martingales

### Simple Martingale
Double your bet after each loss until you win. Always returns original bet size when you finally win.
- Problem: bet size escalates rapidly (1, 2, 4, 8, 16, 32...)
- With MAE stops controlling loss size, this becomes more manageable

### Complex Martingale
Reduces additional bet sizes at cost of extending sequence length. Uses a bet table to look up position size based on accumulated loss units.

### Key Insights
1. **Win/loss ratio is critical**: With 2:1 or 3:1 ratio, martingales recover much faster
2. **MAE + martingale is powerful**: MAE keeps losses small until a big win comes along, and the martingale amplifies that big win (more contracts when it hits)
3. **Triples profits** in Sweeney's crude example, but at cost of increased volatility
4. **Margin requirements spike**: up to 28 contracts on what started as a 1-contract trade
5. **Transaction costs are a big factor** — high commission erodes the martingale's edge

### Results (Crude Oil)
- 41 martingale series in 11 years
- 9 ended with a loss despite "winning" the martingale (small wins didn't cover accumulated losses)
- Profits tripled vs. straight trading
- Drawdowns steeper but recoveries explosive
- Worst sequence: 3-20 win-loss before recovering on one trade

### Four Pillars Application
- **Rebate farming is a form of controlled martingale** — flat equity with commission rebates
- Our BE raise acts like a "managed loss size" similar to MAE stops
- We could explore position sizing based on loss streaks, but:
  - Commission per trade is fixed ($6/side), so more contracts = more commission
  - Need to verify rebate covers the increased commission from larger positions
  - **Not recommended for Phase 1** — keep it simple, 1 position at a time

---

## Chapter 8: Trading Management

### The Control Loop
Managers: Study → Plan → Predict → Direct → Monitor → Correct → (repeat)

Traders usually lack the "monitor and correct" phase because they have no objective standard for what losses should look like. MAE provides that standard.

### Performance Checklists
**Trader Performance** (Figure 8-2):
| Outcome | Proper Execution | Improper Execution |
|---------|------------------|--------------------|
| Win     | No distress      | Distress (lucky)   |
| Loss    | No distress      | Distress (mistake) |

A loss taken properly (within MAE parameters) should cause **no distress**. A win taken improperly (overriding rules) should cause distress.

### Elaborations

**Typical Path**: Use MaxFE and MinFE (not just MAE) to map the expected trajectory of a winning trade. MinFE rising = trade confirming. MinFE stalling = warning.

**Redefining Winners and Losers**: Consider a "draw zone" around entry (e.g., ± commission cost). Trades that end in the draw zone may have different MAE characteristics than clear winners or losers.

**Related Indicators**: Nothing restricts MAE to price-based signals. You could measure excursion from any signal (stochastic crossover, etc.).

### Four Pillars Application
- **Grading system (A/B/C) = entry quality classification** — we can run MAE analysis per grade
- **"No distress for proper loss"** — critical mindset. Our BE raise ensures losses are managed.
- **Draw zone**: With $12 round-trip commission on $10k notional, trades closing within ±$12 of entry are "draws." Should we classify these separately? Yes — they're commission losses, not signal failures.
- **MinFE as health indicator**: If MinFE (lowest bar-low since entry for longs) stalls early, the trade is "sick." This could be a dynamic exit signal.

---

## Appendices Summary

### Appendix A: Computing MAE (Excel)
Complete Excel 4.0 code for bar-by-bar MAE calculation. Handles longs, shorts, and immediate reversals. Our Python backtester already implements this.

### Appendix B: Computing MaxFE (Excel)
Same structure for maximum favorable excursion. Also already in our backtester.

### Appendix C: Computing MinFE (Excel)
**Not yet in our backtester.** Uses bar LOWs for longs (not HIGHs) and bar HIGHs for shorts (not LOWs). This is the "weakest high-water mark" — how much the trade's floor rises. Important addition.

### Appendix D: Generating Frequency Distributions
Excel FREQUENCY() function for binning trades. Our Python uses numpy/pandas equivalents.

### Appendix E: MAE for Shorts and Longs
Separate analysis by direction. **We should do this** — crypto can behave differently long vs short.

### Appendix F: Computing Profit Curves
The "profit by bin" methodology. Maps directly to our BE trigger optimization.

### Appendix G: Range and Volatility
Visual comparison across multiple tradables (AT&T, Coffee, T-Bonds, Dow). Range and volatility roughly track but with leads/lags.

### Appendix H: Range Excursion
Detailed methodology for checking if range expands after entry. Includes graphics worksheet setup.

### Appendix I: Martingale Simulation
Standalone Excel martingale model with adjustable P(win) and win/loss ratio.

### Appendix J: Applying Martingales to Trading Campaigns
Full integration of martingale + MAE stops on real trading data.

---

## Key Takeaways for Four Pillars / VINCE

### What We Already Do Right
1. ✅ Measure MAE and MFE from entry
2. ✅ Use ATR-based stops (volatility-adaptive, better than Sweeney's fixed-$ stops)
3. ✅ Large sample sizes (thousands of trades vs. Sweeney's 252)
4. ✅ Commission-aware backtesting
5. ✅ LSG analysis (loser classification by MFE depth)
6. ✅ BE trigger optimization concept (= Sweeney's "profit by bin")

### What We Should Add
1. **MinFE tracking** — Sweeney says often better than MaxFE for judging trade health
2. **MAE scatter plot** (MAE vs P&L, color-coded by winner/loser) as standard dashboard chart
3. **Frequency diagrams by bin** — separate winner/loser MAE distributions
4. **Profit curves by bin** — sum P&L per MAE bin, find optimal stop level
5. **MAE analysis per grade** (A, B, C, Re-entry) — do grades have different MAE profiles?
6. **MAE analysis per direction** (Long vs Short) — crypto may behave asymmetrically
7. **Run analysis** — drawdown frequency and probability estimation
8. **Draw zone classification** — trades closing within ± commission as separate category

### What Validates Our Approach
1. **BE raise = MAE stop on winners that went profitable** — we're applying Sweeney's method to the favorable excursion side (managing how much profit to give back)
2. **LSG 68-84% finding** — Sweeney's entire thesis is that the MAE distribution tells you where the line is between recoverable dips and genuine losers. Our high LSG means our current stop is too wide — the BE raise tightens it exactly where Sweeney says to.
3. **ATR normalization > fixed-$ stops** — Sweeney used fixed dollar amounts and then spent all of Chapter 5 worrying about volatility adjustment. Our ATR approach solves this inherently.
4. **Commission-aware profit curves** — Sweeney mentions including commissions in the P&L computation. We do this with cash_per_order.

### Recommended Dashboard Charts (WS4D)

#### Tab 3: MFE/MAE & LSG (enhanced from Sweeney)
1. **MAE vs P&L scatter** — green dots = winners, red = losers (Sweeney's Figure 3-1)
2. **MAE frequency diagram** — overlapping histograms for winners/losers by MAE bin
3. **MFE vs P&L scatter** — filtered to losers only (LSG visualization)
4. **MFE histogram for losers** — depth distribution with loser classification overlay
5. **Profit curve by MAE bin** — sum P&L at each stop level (Sweeney's Figure 4-3)
6. **MinFE vs P&L scatter** — NEW, may reveal trade health patterns
7. **BE trigger optimization surface** — net P&L impact at each BE level (our existing concept, now grounded in Sweeney's profit curve methodology)

---

## Quotes Worth Remembering

> "The judgment comes in when you must continue the trade or get out." (Ch. 1)

> "Winning trades have very small MAEs while the losers tend to have larger numbers. This is the seminal observation about MAE." (Ch. 3)

> "Profit curves are very sensitive to the size of individual wins or losses. One big win on a trade with a large MAE can make your curve look like Pike's Peak in the middle of the prairie." (Ch. 4)

> "Range expansion is much more a perceived phenomenon than one that's measurable." (Ch. 5)

> "So effective was the use of MAE stops to minimize losses that even lots of losses did not prevent the trader from being around when large winners showed up." (Ch. 6)

> "A loss taken properly should cause no distress, but a win taken improperly should cause distress." (Ch. 8)

> "All these elaborations stem from knowing what losses 'should' look like. That knowledge gives you the tool to control losses so the wins can do their work." (Ch. 8)

---

*Analysis created: 2026-02-09*
*Source: John Sweeney, "Maximum Adverse Excursion: Analyzing Price Fluctuations for Trading Management" (John Wiley & Sons, 1997)*

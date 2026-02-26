# MFE/MAE Professional Framework

## Origin: John Sweeney (1997)
Book: "Maximum Adverse Excursion: Analyzing Price Fluctuations for Trading Management" (Wiley)
Core thesis: Every trading method has unique adverse price move patterns. Studying them reveals optimal stop placement and capital requirements.

## Definitions

| Metric | Definition | Long Formula | Short Formula |
|--------|-----------|-------------|---------------|
| MAE | Maximum Adverse Excursion — worst unrealized loss | Entry - Lowest Low | Highest High - Entry |
| MFE (MaxFE) | Maximum Favorable Excursion — best unrealized profit | Highest High - Entry | Entry - Lowest Low |
| MinFE | Minimum Favorable Excursion — weakest high-water mark | Highest subsequent LOW - Entry | Entry - Lowest subsequent HIGH |
| ETD | End Trade Drawdown — profit given back from peak | MFE - Actual Profit | Same |
| Exit Efficiency | % of available profit captured (winners) | Actual Profit / MFE * 100 | Same |
| Entry Efficiency | How cleanly you entered | 1 - (MAE / MFE) | Same |

### MinFE — The Missing Metric
Sweeney states MinFE is "often a better indicator of a successful trade than MaxFE." MFE tracks the ceiling (best bar high for longs); MinFE tracks the floor (best bar LOW for longs). MinFE rising = the trade's worst-case is improving = healthy trade. MinFE stalling early while MFE is advancing = the trade dips hard between bars = vulnerable to stops.
- MinFE never decreases during a trade (uses MAX function, same as MAE/MFE)
- MinFE = 0 for many trades (bar lows never exceed entry for longs)
- When MinFE > 0, the trade has structurally moved above entry

## R-Multiple Normalization
Measure everything in risk units for cross-coin comparison:
```
R = SL distance from entry
MAE_R = MAE / R
MFE_R = MFE / R
PnL_R = Net PnL / R
```

## Per-Trade Fields to Track
```python
{
    'mfe_dollar': float,       # Max favorable in $
    'mfe_r': float,            # MFE in R-multiples
    'mfe_atr': float,          # MFE in ATR multiples
    'mfe_pct_tp': float,       # MFE as % of TP distance (0-100+)
    'mae_dollar': float,       # Max adverse in $
    'mae_r': float,            # MAE in R-multiples
    'mae_pct_sl': float,       # MAE as % of SL distance
    'minfe_dollar': float,     # Min favorable in $ (Sweeney's MinFE)
    'minfe_r': float,          # MinFE in R-multiples
    'etd': float,              # MFE - Actual Profit
    'etd_ratio': float,        # ETD / MFE (0-1, lower is better)
    'exit_efficiency': float,  # Actual Profit / MFE (winners only)
    'entry_efficiency': float, # 1 - (MAE / MFE)
    'time_to_mfe': int,        # Bars from entry to peak
    'time_to_mae': int,        # Bars from entry to trough
    'mfe_before_mae': bool,    # Did peak happen before trough?
    'loser_class': str,        # A/B/C/D classification
    'is_draw': bool,           # True if |P&L| <= commission RT (Sweeney's "draw zone")
}
```

## 8 Standard Charts (Sweeney + extensions)

1. **MAE vs P&L scatter** — Winners green, losers red. Winners cluster at low MAE = good entries. (Sweeney Fig 3-1)
2. **MFE vs P&L scatter** — Losers with high MFE = salvageable trades. THE key chart.
3. **MAE frequency diagram (winners vs losers)** — Overlapping histograms by MAE bin. Crossover = optimal stop. (Sweeney Fig 3-4)
4. **MFE histogram (losers only)** — Distribution of "how green" losers got.
5. **Profit curves by MAE bin** — Sum P&L at each stop level, find peak. (Sweeney Fig 4-3 — theoretical basis for BE trigger optimization)
6. **ETD distribution** — How much profit systematically given back. High avg ETD = exit problem.
7. **Time-to-MFE (losers)** — When losers peak. If early, time-based BE raise viable.
8. **MinFE vs P&L scatter** — NEW from Sweeney. MinFE rising = healthy trade floor. Trades with MinFE > 0 are structurally above entry.

## Loser Classification

| Class | MFE Level | Meaning | Action |
|-------|-----------|---------|--------|
| A: Clean losers | < 0.5R | Never went your way | Fix entries, not exits |
| B: Breakeven failures | 0.5R - 1.0R | Went partially | Maybe lower BE trigger |
| C: Should-be winners | > 1.0R | Was profitable, reversed | BE raise saves these |
| D: Catastrophic reversals | > 1.5R, loss > 1R | Strong winner, reversed through | Trailing stop needed |

## BE Trigger Optimization Method
```
For each candidate trigger T (sweep 0.1 ATR to 3.0 ATR):
    losers_saved = losers where MFE >= T
    losers_saved_value = sum(|loss|) for those trades
    winners_killed = winners where price retraced below entry AFTER hitting T
    winners_killed_value = sum(profit) for those trades
    net_impact[T] = losers_saved_value - winners_killed_value

Optimal T = argmax(net_impact)
```
- Sharp peak = one clear answer
- Flat top = robust range (good)
- Plot as curve: net_impact vs T

## MAE-Based Stop Loss Optimization (Percentile Method)
1. Collect MAE for winning trades only (need 60+)
2. Sort ascending
3. Set stop at chosen percentile:
   - P75: tight (lose 25% of winners, eliminate most losers)
   - P85: balanced (lose 15% of winners)
   - P90: conservative (lose 10% of winners)
   - P95: very conservative

The crossover of winner MAE and loser MAE distributions = optimal stop.

## Scatter Plot Pattern Diagnosis

| Pattern | Problem | Fix |
|---------|---------|-----|
| Winners have high MAE | Sloppy entries | Better entry timing |
| Losers have high MFE | Missing BE raise | Implement BE mechanism |
| Winners' MFE >> Actual Profit | Exiting too early | Widen TP or add trailing |
| MAE distributions overlap | Signal has no edge | Fix signal, not stops |
| ETD consistently > 1R | Giving back gains | Tighten trailing |

## Draw Zone (Sweeney Ch. 8)
Trades closing within ± commission cost of entry are "draws" — not signal failures but commission casualties. With $12 RT on $10k notional, this is ±0.12% price move. Classify separately:
- **Draw**: |P&L| <= commission round-trip
- **Clean winner**: P&L > commission RT
- **Clean loser**: P&L < -commission RT, MAE > draw zone

Draws may have different MAE characteristics than genuine winners or losers. Analyzing them separately prevents noise in the MAE distributions.

## Run Analysis / Drawdown Methodology (Sweeney Ch. 6)
1. Define adverse run: equity below previous peak until new high
2. Measure: `(Peak equity - Current equity) / (Capital + Peak equity)`
3. Collect all drawdown episodes, create frequency distribution
4. Fit exponential curve to estimate probability of extreme drawdowns
5. Key thresholds: 70% of drawdowns should be < 10%, 95% should be < 20%
6. P(catastrophic 40% drawdown) should be infinitesimal for a viable system
7. Capital needed: `MAE stop / 0.02` (2% max risk per trade)

## Volatility & Stops (Sweeney Ch. 5 — key finding)
ATR-based stops inherently handle what Sweeney spent 22 pages worrying about:
- Range expansion after entry is episodic, not sustained
- Losers' range actually contracts slightly; winners' range expands
- MAE is generally much less than daily range for winners (ratio ~0.35)
- **Conclusion**: Don't over-engineer volatility adjustments. ATR normalization solves this.

## Sources
- John Sweeney, "Maximum Adverse Excursion" (Wiley, 1997) — [Full analysis](../../02-STRATEGY/Research/SWEENEY-MAE-BOOK-ANALYSIS.md)
- TradesViz MFE/MAE analysis
- NinjaTrader MAE/MFE/ETD definitions
- FTMO stop loss optimization
- Trademetria MAE/MFE guide
- WealthLab "Perfect Exit" method

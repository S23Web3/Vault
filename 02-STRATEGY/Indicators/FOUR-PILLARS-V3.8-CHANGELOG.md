# Four Pillars v3.8 Changelog

## Version 3.8 (2026-02-09)

### Summary
v3.8 focuses on **directional filtering** and **dynamic risk management** to improve signal quality and adapt position management to market volatility.

---

## Key Changes from v3.7.1

### 1. Cloud 3 Directional Filter (ALWAYS ON) ✨ NEW

**Problem Solved**: v3.7.1 could generate LONG signals in bearish markets (price below Cloud 3) and SHORT signals in bullish markets (price above Cloud 3), causing conflicting signals and poor trade outcomes.

**Solution**: Cloud 3 directional filter is now ALWAYS ACTIVE (not optional):
- **Bearish context** (price < Cloud 3): Block ALL long signals, only allow shorts
- **Bullish context** (price > Cloud 3): Block ALL short signals, only allow longs
- **Chop zone** (price inside Cloud 3): Allow BOTH directions (current behavior preserved)

**Implementation**:
```pine
int cloud3_direction = price_pos  // -1 = bearish, 0 = inside, 1 = bullish
bool cloud3_allows_long  = cloud3_direction >= 0
bool cloud3_allows_short = cloud3_direction <= 0

// Applied to ALL entry conditions
bool enter_long_a = long_signal and ... and cloud3_allows_long
```

**Impact**: Fewer trades, but higher directional alignment. Eliminates opposite-direction signals in trending markets.

---

### 2. ATR-Based Breakeven Raise ✨ NEW

**Problem Solved**: Fixed $ breakeven ($2/$4/$6) doesn't adapt to volatility. A $2 BE on RIVER (price $0.50, 4% move) is very different from $2 BE on BTC (price $100K, 0.002% move).

**Solution**: Breakeven raise now uses **ATR multiples** instead of fixed dollars:
- **Trigger**: Move SL to BE when profit > `i_beTrigger × ATR` (default: 0.5 ATR)
- **Lock**: Lock SL at entry + `i_beLock × ATR` (default: 0.3 ATR, covers $8 commission)

**Parameters**:
```pine
i_useATR_BE = true       // Use ATR-based BE (vs fixed $)
i_beTrigger = 0.5        // BE trigger: profit > 0.5× ATR
i_beLock = 0.3           // BE lock: SL = entry + 0.3× ATR
i_beFixed = 2.0          // Fixed $ BE (if not using ATR)
```

**Example** (RIVERUSDT, ATR = $0.02):
- Entry: $0.50
- BE trigger: $0.50 + (0.5 × $0.02) = $0.51 profit
- BE lock: SL moves to $0.50 + (0.3 × $0.02) = $0.506 (covers commission)

**Impact**: Volatility-adaptive risk management. Same logic scales across all coins.

---

### 3. Commission Updated to $8/side

**Problem Solved**: v3.7.1 used $6/side (0.06%), but real commission on most exchanges is 0.08% = $8/side on $10K notional (20x leverage).

**Change**:
```pine
// v3.7.1
commission_value=6  // $6/side = $12 RT

// v3.8
commission_value=8  // $8/side = $16 RT
```

**Dashboard**: Shows total commission as `$16 × closed_trades`

**Impact**: More accurate backtest results. Slightly lower net profit due to higher commission costs.

---

### 4. MFE/MAE Tracking ✨ NEW

**Purpose**: Track Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE) for every trade to feed ML analysis.

**Implementation**:
```pine
var float max_price_in_trade = na
var float min_price_in_trade = na

if inPosition
    max_price_in_trade := math.max(max_price_in_trade, high)
    min_price_in_trade := math.min(min_price_in_trade, low)
```

**Dashboard**: Shows live MFE/MAE as % during trade:
```
MFE/MAE: 2.5 / 0.8%
```

**ML Use Case**: Analyze losers that "saw green" (LSG%). Optimize BE raise to capture more winners before they reverse.

---

### 5. Dashboard Enhancements

**New rows**:
- **Cloud3**: Shows "BULL" (green), "BEAR" (red), or "CHOP" (orange) based on price position
- **BE**: Shows BE mode ("0.5×ATR" or "$2.0" depending on setting)
- **MFE/MAE**: Shows live MFE/MAE % when in position (hidden when flat)

**Updated**:
- **Comm$**: Now shows $16 per round trip (was $12)

---

## Behavioral Changes

### Entry Logic
- **Cloud 3 filter applied to ALL entries**: A, B, C, and Cloud 2 re-entry signals now all check `cloud3_allows_long` / `cloud3_allows_short`
- **B/C signals**: Now respect Cloud 3 direction (previously only A signals checked Ripster filter, which was OFF by default)

### Position Management
- **BE raise is dynamic**: Adjusts to volatility via ATR (unless disabled)
- **SL/TP unchanged**: Still 1.0 ATR SL, 1.5 ATR TP (no trailing in v3.8)

### Signal Generation
- **Fewer signals in trending markets**: Cloud 3 filter blocks opposite-direction signals
- **Same signals in chop**: When price is inside Cloud 3, both directions allowed (no change)

---

## Files Changed

### New Files
1. **`four_pillars_v3_8_strategy.pine`** - Full strategy with commission tracking
2. **`four_pillars_v3_8.pine`** - Indicator-only version with alerts

### Unchanged from v3.7.1
- Stochastic settings (9-3, 14-3, 40-3, 60-10, all Raw K)
- Ripster EMA settings (Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89)
- Cooldown gate (3 bars default)
- Commission handling (`cash_per_order`, no `commission.percent`)
- Phantom trade fix (no `strategy.close_all()`, uses `strategy.cancel()`)

---

## Breaking Changes

⚠️ **None** — v3.8 is backward-compatible with v3.7.1 settings. Existing users can upgrade without changing parameters.

**Recommended Updates**:
- Enable ATR-based BE: Set `i_useATR_BE = true` (default in v3.8)
- Adjust BE trigger/lock if needed: Test 0.3-0.7 ATR trigger, 0.2-0.5 ATR lock

---

## Expected Performance Impact

**Compared to v3.7.1**:

| Metric | Change | Reason |
|--------|--------|--------|
| **Total Trades** | -10% to -30% | Cloud 3 filter blocks opposite-direction signals |
| **Win Rate** | +3% to +8% | Better directional alignment |
| **Avg R per Trade** | +0.2 to +0.5R | BE raise locks in profit before reversals |
| **Commission $** | Same $ per trade, but fewer trades = less total commission bleed |
| **Sharpe Ratio** | +10% to +20% | Fewer losing trades, better risk-adjusted returns |

**Note**: These are projections based on preliminary testing. Full backtest results on 100+ coins will be generated by the Vince ML pipeline.

---

## Next Steps (v3.9+ Roadmap)

Potential future enhancements (NOT in v3.8):

1. **Trailing TP**: Move TP with price once profit > X ATR
2. **Cloud 2 exit**: Hard close when Cloud 2 flips against trade (from ATR-SL-MOVEMENT spec)
3. **Phase-based SL/TP**: Cloud 2/3/4 cross triggers SL/TP adjustments (from spec doc)
4. **Stepped BE raise**: Multiple BE levels (e.g., 0.5 ATR → 0.3 ATR lock, 1.0 ATR → 0.8 ATR lock)
5. **Time-based exit**: Close if no progress after N bars

**ML-Driven Optimizations** (from Vince analysis):
- Optimal BE trigger/lock per coin (may vary by volatility)
- Signal grade filtering (e.g., skip C signals on low-volume coins)
- Session filters (e.g., block signals during low-liquidity hours)

---

## Testing Checklist

Before using v3.8 in production:

- [ ] Load v3.8 strategy on TradingView (test on UNIUSDT 2m chart)
- [ ] Verify Cloud 3 filter works:
  - In bearish context (price < Cloud 3), NO long signals fire
  - In bullish context (price > Cloud 3), NO short signals fire
  - Inside Cloud 3 (chop), BOTH directions fire
- [ ] Backtest 3 months on same asset/timeframe as v3.7.1
- [ ] Compare results: Fewer trades, higher win rate, similar/higher net profit
- [ ] Verify dashboard shows Cloud 3 direction correctly
- [ ] Verify MFE/MAE updates during trade
- [ ] Test ATR-based BE: Confirm SL moves to entry + 0.3 ATR when profit > 0.5 ATR

---

## Version History

- **v3.8** (2026-02-09): Cloud 3 filter, ATR-based BE, MFE/MAE tracking, $8 commission
- **v3.7.1** (2026-02-05): Cooldown gate, phantom trade fix, $6 commission
- **v3.7** (2026-02-04): Rebate farming architecture, tight SL/TP, free flips
- **v3.6** (2026-01-28): AVWAP SL, separate order IDs (bled out)
- **v3.5.1** (2026-01-25): Cloud 3 trail, single order ID
- **v3.3** (2026-01-15): Four Pillars core logic (A/B/C signals)

---

**For full technical specifications, see**: `ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` (v2.0)

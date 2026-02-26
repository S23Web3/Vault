# Malik's Core Trading Strategy
**Version:** 2.0
**Date:** 2026-01-29
**Status:** Refined with real trade examples
**Last Update:** Added Three Pillars framework and momentum continuation logic

---

## Philosophy

The market does predictable things. When conditions align, action is taken. No guessing, no hoping — systematic execution based on **THREE PILLARS**:

1. **PRICE** (Structure via Ripster + Anchored VWAP)
2. **VOLUME** (Validated through VWAP placement)
3. **MOMENTUM** (Must CONTINUE after cross, not decline)

The system is designed to protect capital: **Small win > Small loss > Big loss**

When initial signals appear but confirmation doesn't materialize, exit quickly with small profit rather than holding for a loss.

---

## The Three Pillars Framework

### Pillar 1: PRICE (Structure)
- **Ripster EMA Clouds** (trend direction)
- **Anchored VWAP from the low** (validates buyers in control)
- Price above VWAP + rising clouds = Buyers dominating

### Pillar 2: VOLUME
- **Anchored VWAP** shows WHERE volume actually happened
- Combination of volume + price validates trend control
- Not just "volume is high" — but "volume confirms THIS direction"

### Pillar 3: MOMENTUM
- **Stoch 55 cross** provides trigger
- **CRITICAL:** Momentum must CONTINUE building after cross
- If momentum DECLINES after cross = EXIT immediately
- Example: Small 2% win (40% on 20x) vs potential loss

All three pillars must align and STAY aligned for confident hold.

---

## Core Components

### 1. BBWP (Bollinger Band Width Percentile) — Volatility Filter

**Purpose:** Identify when market is coiled (squeeze) and ready for a big move.

**Settings:**
- Standard BB: 20 period, 2 standard deviations
- BBWP Lookback: 100 (adjustable per coin)
- MA of BBWP: 5 SMA

**Timeframe Mapping:**
| Trading TF | BBWP TF |
|------------|---------|
| 1m | 5m+ |
| 5m | 15m+ |
| 30m | 1h |
| 1h | 4h |

**Readings:**
| BBWP Level | State | Implication |
|------------|-------|-------------|
| < 10% | Low Volatility | Squeeze - move coming |
| 10-90% | Normal | No volatility edge |
| > 90% | High Volatility | Trend may exhaust |

**Key Signals:**
- BBWP LOW (blue bars) = Squeeze active, preparing for breakout
- BBWP transitioning to RED = Breakout happening
- BBWP maxed (extreme red bars) = Exhaustion, potential reversal

**Critical Rule:** BBWP is a FILTER, not a signal. It tells you WHEN volatility is right, not WHICH direction.

---

### 2. Tri-Rotation Stochastics — Momentum Direction & Continuation

**The Tri-Rotation System:**

| Stochastic | Settings | Purpose |
|------------|----------|---------|
| Fast | 9, 1, 3 | Short-term momentum |
| Medium | TDI CW_Trades | Volatility confirmation |
| Slow | 55, 1, 12 | **Direction trigger** |

**Stoch 55 (The Key Trigger):**
- Provides the entry cross signal
- **MUST be monitored AFTER cross** for continuation
- If momentum DECLINES after cross → EXIT immediately
- If momentum CONTINUES after cross → HOLD with confidence

**Direction Logic:**

**LONG Setup:**
- Stoch 9 in oversold zone (<20)
- Stoch 55 approaching cross from below
- TDI CW_Trades turning bullish
- **Entry:** When Stoch 55 crosses UP
- **Confirm:** Momentum continues building after cross

**SHORT Setup:**
- Stoch 9 in overbought zone (>80)
- Stoch 55 approaching cross from above
- TDI CW_Trades turning bearish
- **Entry:** When Stoch 55 crosses DOWN
- **Confirm:** Momentum continues building after cross

**Exit Triggers:**
- Momentum DECLINES after Stoch 55 cross (protective exit)
- Stochastics reach opposite extreme
- Divergence forms

---

### 3. Ripster EMA Clouds — Trend Structure

**Cloud Configuration:**
| Cloud | EMAs | Purpose |
|-------|------|---------|
| 5/12 | 5, 12 | Entry confirmation |
| 34/50 | 34, 50 | Trend direction |
| 8/9 | 8, 9 | Pullback adds |

**Rules:**
- Price ABOVE green cloud (34/50) = LONG bias only
- Price BELOW red cloud (34/50) = SHORT bias only
- Clouds RISING = Buyers in control
- Clouds FALLING = Sellers in control
- Price crosses ABOVE green cloud = Entry confirmation for LONG
- Candle closes against 5/12 cloud = EXIT

---

### 4. Anchored VWAP — Volume/Price Validation

**Purpose:** Validates that volume confirms the direction. Shows trend control.

**Settings:**
- Anchor from: Significant low (for LONG) or high (for SHORT)
- Updated as new lows/highs form

**Logic:**
- **LONG:** Price above anchored VWAP from low = Buyers control
- **SHORT:** Price below anchored VWAP from high = Sellers control
- Break of VWAP = Control lost, consider exit

**Why It Matters:**
- Combines VOLUME + PRICE into one validation
- Not just "price going up" but "price going up WITH volume confirmation"
- Shows WHERE the actual buying/selling happened

---

### 5. Volume Profile — Target Identification

**Purpose:** Identify where price is likely to go based on volume distribution.

**Key Levels:**
- POC (Point of Control) — Highest volume price (magnet)
- VAH (Value Area High) — Upper boundary
- VAL (Value Area Low) — Lower boundary
- Naked POC — Previous POC not revisited (strong magnet)

---

### 6. ATR — Risk Management & Volatility State

**Purpose:** Dynamic stop loss sizing and volatility screening.

**Stop Loss Rule:** Maximum stop loss = 2 ATR from entry

**ATR Screening (Separate System):**
- Identifies coins with ATR awakening (crossing lowest resistance)
- Identifies coins with ATR maxed (reversal potential)
- Each coin judged against its OWN 7-day ATR high/low
- Uses 30-minute timeframe for calculation
- Pre-filters coins BEFORE loading in TradingView

---

## Complete Trade Setup Flow

### Entry Requirements (All Must Align):

**1. VOLATILITY FILTER (BBWP)**
- BBWP at low (< 10%, blue bars) = Squeeze active
- Preparing for breakout, move imminent

**2. INITIAL MOMENTUM (Stochastics)**
- Stoch 9 in oversold (<20) for LONG or overbought (>80) for SHORT
- Stoch 55 approaching cross
- TDI CW_Trades beginning to turn

**3. STRUCTURE CONFIRMATION (Price)**
- Price crosses ABOVE green Ripster cloud (LONG)
- OR Price crosses BELOW red Ripster cloud (SHORT)
- Ripster clouds beginning to rise/fall

**4. ATR CONFIRMATION**
- ATR starting to RISE from low state
- Not flat, not maxed out
- Movement beginning

### Entry Trigger:

**When Stoch 55 crosses in the direction of setup**

### Hold Confirmation (Must Continue):

**CRITICAL CHECKPOINT:** After entry, monitor if momentum CONTINUES or DECLINES

**Momentum CONTINUES (Hold with confidence):**
- Stoch 55 keeps building after cross ✓
- TDI CW_Trades strengthening ✓
- ATR climbing ✓
- Ripster clouds rising/falling ✓
- Price stays above/below anchored VWAP ✓
- BBWP transitioning from blue to red (breakout confirming) ✓

**Momentum DECLINES (Exit immediately):**
- Stoch 55 starts declining after cross ❌
- Exit with small profit (2-5% typical, 40-100% on 20x leverage)
- Better small win than holding for reversal loss

### Exit Signals:

**Protective Exits:**
- Momentum declines after Stoch 55 cross → EXIT (example: 2% profit)
- Price breaks VWAP → Control lost
- Candle closes against 5/12 Ripster cloud

**Profit Exits:**
- BBWP maxed out (extreme red bars at >90%)
- Stochastics reach opposite extreme
- Volume Profile target reached (POC/VAH/VAL)
- ATR starts declining from peak
- Ripster clouds flatten/reverse

### Risk Management:

**Position Sizing:**
- Stop = 2 ATR maximum from entry
- Risk 1-2% of capital per trade
- Calculate position size: Risk Amount / (2 × ATR)

**Stop Placement:**
- Below VWAP anchor for LONG
- Below recent swing low for LONG
- Above VWAP anchor for SHORT
- Above recent swing high for SHORT
- Maximum 2 ATR distance

---

## Real Trade Examples (ZETAUSDT 30m)

### Example 1: Failed Confirmation - Quick Exit (Left Side)

**Time:** ~08:00

**Entry Signals:**
- BBWP: Low (blue bars, squeeze) ✓
- Stoch 55: Cross happened ✓
- ATR: Starting to rise ✓
- Price: Crossed above cloud ✓

**What Happened:**
- **Momentum DECLINED after cross** ❌
- Stoch 55 started weakening
- Exit triggered

**Result:**
- Exit at 08:00
- Profit: ~2% (40% on 20x leverage)
- Time in trade: Brief
- **System protected from potential reversal loss**

**Lesson:** Even when initial signals look good, if momentum doesn't confirm, exit quickly with small profit. This is the system working correctly.

---

### Example 2: Full Confirmation - Trend Ride (Right Side)

**Time:** 12:30 - 16:30+

**Setup Formation (12:30):**
- BBWP: At lowest (blue bars) ✓
- Stoch 9: In oversold area (<20) ✓
- Price: Crossing ABOVE green Ripster cloud ✓
- Stoch 55: Lines approaching cross ✓
- ATR: Starting to RISE from low ✓

**Entry Trigger (13:55):**
- **Stoch 55 cross happened** ✓
- TDI CW_Trades turning bullish ✓

**Hold Confirmation (13:55 onwards):**
- **Momentum CONTINUED building** ✓
- Stoch 55 kept strengthening ✓
- ATR CLIMBING ✓
- Ripster clouds RISING (buyers stronger) ✓
- Price stayed above anchored VWAP ✓
- BBWP transitioning blue → red (breakout) ✓

**Result:**
- Confident hold through entire move
- All three pillars aligned and stayed aligned
- Exit when BBWP maxed (16:30+) or momentum reverses

**Lesson:** When ALL confirmations materialize and continue, ride the trend with confidence. The system tells you when to stay in.

---

## Three Pillars Checklist

Before holding a position with confidence, verify:

**☑ PRICE (Structure)**
- [ ] Price above/below Ripster 34/50 cloud (direction matches)
- [ ] Clouds rising/falling (trend control)
- [ ] Price above/below anchored VWAP (volume confirms)

**☑ VOLUME (Validation)**
- [ ] Anchored VWAP placement confirms direction
- [ ] Volume + price combination validates trend control
- [ ] Not just "volume exists" but "volume confirms THIS side"

**☑ MOMENTUM (Continuation)**
- [ ] Stoch 55 crossed in trade direction
- [ ] Momentum CONTINUES building (not declining)
- [ ] TDI CW_Trades strengthening
- [ ] ATR climbing (volatility expanding)

If ANY pillar breaks → Reassess or exit

---

## Integration with ATR Screener

The ATR Screener (separate system) pre-filters coins BEFORE manual review:

**Screener Purpose:**
- Scans ALL Bybit perpetual contracts (established only)
- Calculates 30m ATR with 7-day history
- Identifies ATR resistance levels (peaks from last 7 days)
- Alerts when ATR crosses resistance (volatility awakening)

**Screener Output:**
- **AWAKENING:** ATR crossed lowest resistance → Trade potential
- **MAXED OUT:** ATR at highest resistance → Reversal potential

**Workflow:**
1. **Evening:** Screener alerts coins with ATR state changes
2. **Manual Review:** Load alerted coins in TradingView
3. **Apply Full Strategy:** Check if three pillars align
4. **Execute:** Small automated positions on qualified setups
5. **Morning:** Add to winning positions manually

---

## Indicator Architecture

### Dashboard Components:

**Top Right Display:**
- **BBWP State:** 🔵 Squeeze (<10%) / 🟡 Normal / 🔴 Extended (>90%)
- **Stoch Alignment:** Status of 9/55/CW_Trades
- **Trend Control (34/50):** 🟢 LONG / 🔴 SHORT
- **VWAP Position:** 🟢 Above / 🔴 Below
- **ATR Status:** Current value + 2x distance for stop
- **Momentum Check:** ✅ Building / ⚠️ Weakening / ❌ Declining

### Required Indicators:

1. **BBWP** (separate pane)
2. **Ripster EMA Clouds** (5/12, 34/50, 8/9)
3. **Stochastics** (9, 55, CW_Trades)
4. **Anchored VWAP**
5. **Volume Profile** (separate)
6. **ATR** (14 RMA)

---

## What Needs Building

### For TradingView:
1. **Main Strategy Indicator:**
   - Ripster clouds with rising/falling detection
   - Dashboard showing three pillars status
   - Momentum continuation tracker
   - Alert system for n8n webhooks

2. **BBWP Optimization:**
   - Per-coin lookback testing
   - Visual spectrum enhancement

### For ATR Screener (Separate Python):
1. Bybit API integration (all perpetuals)
2. 30m ATR calculation with 7-day history
3. Resistance level detection
4. Telegram alert system
5. Cron job on Jacky VPS

---

## Key Insights

**The System Protects You:**
- Not every setup with initial signals becomes a winning trade
- When momentum doesn't confirm, exit quickly with small profit
- Example: 2% profit better than -5% loss
- The system is designed to identify BOTH when to stay and when to leave

**Three Pillars Must All Align:**
- Price structure alone isn't enough
- Volume confirmation validates the move
- Momentum must CONTINUE after entry signal
- If any pillar breaks → Reassess

**Risk Management Philosophy:**
- Small win > Small loss > Big loss
- Protect capital aggressively
- Let winners run only when ALL confirmations persist
- Exit fast when any confirmation fails

---

## Related Files

- [[ATR-ADR-Screener-Strategy]] - Full ATR screener research
- [[2026-01-29-ATR-screener-build]] - Session log with examples
- [[Trading-Manifesto]] - Entry/exit rules reference
- [[Master-Checklist]] - Project tracking

---

#strategy #core #three-pillars #momentum-continuation #vwap #ripster #bbwp #updated-2026-01-29

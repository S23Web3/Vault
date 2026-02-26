# ATR Position Manager - Build Spec for Claude Code

**Version:** 1.0
**Date:** 2026-02-04
**File:** `atr_position_manager_v1.pine`
**Status:** Ready for testing

---

## PHILOSOPHY

This indicator is a **position management tool**, not an entry signal generator.

**Core principle:** After entering a trade, calculate proper stop loss and trailing stop levels based on current market volatility (ATR). The system then sends these levels to n8n for order placement on the exchange. Once placed, the exchange manages the trailing - set and forget.

**Why ATR-based:**
- Fixed percentage stops ignore volatility
- ATR adapts to market conditions
- Chart TF ATR = tight stop for entry precision
- HTF ATR = wider trail to avoid noise shakeouts

---

## CURRENT STATE

**Entry signal:** SSL Channel (89 MA) crossover - **TEMPORARY**

This is a placeholder to test if ATR calculations produce correct values. SSL was chosen because:
- Simple, clear crossover signals
- 89 MA = longer timeframe bias (less noise)
- Easy to visually verify on chart

**Future:** Replace SSL with Four Pillars combined indicator signals. The integration point is clearly marked in the code at lines 68-78.

---

## WHAT TO TEST

1. **ATR values match TradingView built-in ATR**
   - Add built-in ATR indicator
   - Compare table values to built-in
   - Check both chart TF and HTF values

2. **SL/Trail calculations are correct**
   - LONG: SL = entry - (ATR × mult), Trail activation = entry + (HTF ATR × mult)
   - SHORT: SL = entry + (ATR × mult), Trail activation = entry - (HTF ATR × mult)

3. **Lines draw at correct prices**
   - Entry line (white) at close of signal bar
   - SL line (red dotted) at calculated SL
   - Trail line (orange dashed) at activation level

4. **Alert JSON is valid**
   - Copy alert message
   - Validate JSON structure
   - All values populated

---

## INTEGRATION CHECKLIST (FUTURE)

When Four Pillars indicator is ready:

```pinescript
// Replace these lines:
bool long_condition  = ssl_cross_up and barstate.isconfirmed
bool short_condition = ssl_cross_down and barstate.isconfirmed

// With:
bool long_condition  = fourPillars_long_signal and barstate.isconfirmed
bool short_condition = fourPillars_short_signal and barstate.isconfirmed
```

Then remove or disable the SSL calculation section.

---

## FILE LOCATION

```
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\atr_position_manager_v1.pine
```

---

## DEPENDENCIES

- TradingView Pro+ (webhook alerts)
- n8n workflow (separate build)
- WEEX/Bybit API credentials

---

## NEXT STEPS

1. Copy pine script to TradingView
2. Add to chart (any crypto pair)
3. Verify ATR values match built-in
4. Verify lines draw correctly on SSL signals
5. Test alert payload structure
6. Report any calculation errors

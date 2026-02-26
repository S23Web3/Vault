# ATR Stop Loss & Trailing Take Profit - Build Spec Session
**Date:** 2026-02-02  
**Session Type:** System Design & Specification  
**Duration:** ~45 minutes  
**Status:** Spec Complete, Ready for Claude Code

---

## 🎯 Objective

Design and document a comprehensive build specification for ATR-based stop loss and trailing take profit system with n8n momentum validation.

---

## 📊 What Was Built

### Build Specification Document

**Location:** `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\ATR-SL-Trailing-TP-BUILD-SPEC.md`

**Contents:**
1. System Overview & Architecture
2. Pine Script Indicator Specification
3. n8n Workflow Specification
4. Calculation Examples
5. Testing Checklists
6. Security Notes
7. Dependencies

---

## 🔧 System Logic Defined

### Stop Loss Calculation
- Uses **chart timeframe ATR**
- Distance = ATR × 2 (configurable multiplier)
- LONG: Entry - (ATR × 2)
- SHORT: Entry + (ATR × 2)

### Trailing Stop Activation
- Uses **higher timeframe ATR** (e.g., 5m if chart is 1m)
- Activation price = Entry + (HTF ATR × 2) for LONG
- Trail callback distance = HTF ATR × 2

### Timeframe Mapping
| Chart TF | SL ATR | Trail ATR |
|----------|--------|-----------|
| 1m | 1m | 5m |
| 5m | 5m | 15m |
| 15m | 15m | 1H |

### Momentum Validation (n8n)
- Fetch 3 candles (5m) from exchange
- Calculate average True Range
- Validate: TradingView ATR >= 75% of exchange avg ATR
- Below 75% = momentum fading, reject trade
- 75%+ = momentum confirmed, place order

---

## 📝 Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Trailing visual | No update | Exchange manages real trailing, keep indicator simple |
| Exchange priority | WEEX primary, Bybit secondary | User preference |
| Position size | Input adjustable | Flexibility for different setups |
| Entry signals | EMA 9/21 cross (placeholder) | Separate build, integrate Four Pillars later |
| Multi-position | Future scope | Add-on feature later |
| ATR threshold | 75% | Allows normal variance while catching momentum death |

---

## 🏗️ Architecture

```
TradingView (Pine Script)
    │
    │ 1. Detect entry signal
    │ 2. Calculate chart TF ATR (SL)
    │ 3. Calculate HTF ATR (trailing)
    │ 4. Draw SL line on chart
    │ 5. Send alert with JSON payload
    │
    ▼
n8n (Jacky VPS)
    │
    │ 1. Receive webhook
    │ 2. Fetch 3× 5m candles from WEEX
    │ 3. Calculate avg ATR
    │ 4. Validate: TV ATR >= 75% of avg
    │ 5. If valid → Place order with SL + trailing
    │
    ▼
Exchange (WEEX/Bybit)
    │
    │ • Order with stop loss
    │ • Trailing stop with activation price
    │ • Exchange manages trailing automatically
    │
    ▼
Set and Forget
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `02-STRATEGY/Indicators/ATR-SL-Trailing-TP-BUILD-SPEC.md` | Complete build specification for Claude Code |

---

## 🔗 Related Files

- `02-STRATEGY/Four-Pillars-Status-Summary.md` - Overall system status
- `02-STRATEGY/Core-Trading-Strategy.md` - Three Pillars framework
- `06-CLAUDE-LOGS/2026-01-28-n8n-webhook-testing.md` - n8n setup reference

---

## ✅ Claude Code Instructions

```
Read the build specification at:
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\ATR-SL-Trailing-TP-BUILD-SPEC.md

Build the Pine Script indicator according to Section 2.

Output file:
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\atr_position_manager_v1.pine

Requirements:
- Pine Script v6
- EMA 9/21 cross for test signals (placeholder for Four Pillars later)
- Chart TF for SL ATR, HTF input for Trail ATR
- Horizontal ray at SL price (no trailing visual update)
- Alert with full JSON payload
- All values input adjustable
```

---

## 📋 Next Steps

1. **Claude Code:** Build Pine Script indicator from spec
2. **TradingView:** Test indicator compiles and calculates correctly
3. **n8n:** Build workflow based on Section 3 of spec
4. **WEEX:** Verify API endpoints and test on testnet
5. **Integration:** End-to-end test with paper trading

---

## 💡 Key Insights

### Semi-Automated Philosophy
- TradingView calculates levels and signals
- n8n validates momentum before execution
- Exchange manages trailing after placement
- Trader manages risk and money management
- System is set and forget after order placed

### Momentum Validation Purpose
- ATR from TradingView reflects current bar calculation
- 3-candle average from exchange shows recent momentum trend
- If TV ATR < 75% of average = momentum declining
- Prevents entering trades when momentum is fading

---

## 🔐 Security Considerations

- Webhook secret in Pine Script input (not hardcoded)
- Exchange API keys in n8n environment variables
- Nginx IP whitelist for TradingView (already configured)
- Rate limiting via Nginx (already configured)
- WEEX API: trading permissions only, no withdrawal

---

**Session Complete**

Spec ready for Claude Code execution. Pine Script indicator build is next step.

# Liquidity Farming Strategy - Work in Progress

## Status: BUILDING INDICATOR

**Created:** 2026-01-30  
**Last Updated:** 2026-01-30

---

## Current Focus

Building TradingView Pine Script v6 indicator to detect liquidity farming opportunities on mid-cap crypto perpetuals.

---

## Target Characteristics

**Coin Profile:**
- Mid market cap ($50M-$500M) - NOT low cap as initially stated
- Medium-high volatility (100%+ daily moves possible)
- Perpetual futures available
- Social media pump coordination (detection TBD)
- Retail-heavy order books

**Target Coins:**
- PIPPINUSDT.P
- RIVERUSDT.P
- BEATUSDT.P
- SOMYUSDT
- 1000RATSUSDT

---

## ATR Heartbeat Pattern

The core detection mechanism:

1. **Spike:** ATR jumps 50%+ above 20-period average
2. **Decline:** ATR drops 30% from peak
3. **Flat:** ATR stabilizes (low volatility in ATR itself)
4. **Second Beat:** Small ATR increase forming → READY TO TRADE

---

## Integration Points

**Alerts:** Telegram (NOT Discord)  
**Execution:** Manual → Semi-auto → Full auto (later)  
**Automation:** n8n workflows saved for later (separate file)

---

## Files

- [[liquidity-farming-detector.pine]] - Pine Script indicator (WIP)
- n8n automation reference (saved for later phase)

---

## Next Steps

TO BE DETERMINED - waiting for Malik's direction on what to build next.

---

#strategy #liquidity-farming #atr #perpetuals #crypto

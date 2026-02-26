# Commission Rebate Analysis — Four Pillars v3.7.1
**Date:** 2026-02-07

---

## Raw Commission Math

| Parameter | Value |
|-----------|-------|
| Exchange | WEEX |
| Taker fee | 0.06% per side |
| Margin per trade | $500 cash |
| Leverage | 20x |
| Notional per trade | $10,000 |
| Cost per side | $6.00 |
| Round trip cost | $12.00 |

### Pine Script Setting
```
commission_type=strategy.commission.cash_per_order, commission_value=6
```

### Why NOT commission.percent
TradingView applies `commission.percent` to the **cash quantity**, not notional. With 20x leverage:
- `commission.percent=0.06` → 0.06% × $500 = **$0.30/side** (WRONG)
- `cash_per_order=6` → **$6.00/side** (CORRECT)

v3.7 used percent — this is why the backtester showed profit while the real account lost money.

---

## Rebate Impact

| Account | Rebate % | Rebate/RT | Net Commission/RT |
|---------|----------|-----------|-------------------|
| Account 1 (70%) | 70% | $8.40 | **$3.60** |
| Account 2 (50%) | 50% | $6.00 | **$6.00** |
| No rebate | 0% | $0.00 | $12.00 |

Rebates settle daily at **5pm UTC**. Not a simple percentage reduction — it's an actual credit deposited into the account balance once per day.

---

## Expectancy Calculation

### v3.7.1 Baseline (from TradingView backtester)
- **Gross profit per winning trade:** ~$83 (avg)
- **Gross loss per losing trade:** ~$70 (avg)
- **Win rate:** ~54%
- **Gross profit per trade:** $83 × 0.54 − $70 × 0.46 = $44.82 − $32.20 = **$12.62**
- **After fees:** $12.62 − $12.00 = **$0.62/trade** (TV shows $1.81 with rounding)

### With 70% Rebate
- **Net commission/RT:** $3.60
- **Expectancy:** $12.62 − $3.60 = **$9.02/trade**
- Monthly (100 trades): **$902**
- Monthly (200 trades): **$1,804**

### With 50% Rebate
- **Net commission/RT:** $6.00
- **Expectancy:** $12.62 − $6.00 = **$6.62/trade**
- Monthly (100 trades): **$662**
- Monthly (200 trades): **$1,324**

---

## Breakeven+$X Raise — Scenario Analysis

### The 86% Finding
86% of losing trades saw unrealized profit before dying. If we raise the stop loss to breakeven+$X when the trade reaches $X in profit, we convert these losers into small winners.

### How It Works
1. Trade enters at price P
2. Trade moves $X in favor (unrealized profit = $X on $10k notional)
3. SL raised to P + $X (long) or P − $X (short)
4. If trade reverses → exits at breakeven+$X instead of full SL loss
5. If trade continues → still hits TP normally

### $2 Raise Threshold (0.02% move on $10k notional)

**Without breakeven raise:**
- Winners (54%): avg +$83 each → $44.82
- Losers (46%): avg −$70 each → −$32.20
- Gross = $12.62

**With breakeven+$2 raise:**
- Winners (54%): avg +$83 each → $44.82
- Losers that saw green (86% × 46% = 39.6%): now +$2 each → +$0.79
- Losers that never saw green (14% × 46% = 6.4%): still −$70 → −$4.48
- Gross = $44.82 + $0.79 − $4.48 = **$41.13**

| Scenario | Gross/trade | Net (70% rebate) | Net (50% rebate) | Monthly 100 trades |
|----------|-------------|-------------------|-------------------|--------------------|
| No raise, no rebate | $12.62 | — | — | — |
| No raise, 70% rebate | $12.62 | $9.02 | — | $902 |
| No raise, 50% rebate | $12.62 | — | $6.62 | $662 |
| **+$2 raise, 70% rebate** | **$41.13** | **$37.53** | — | **$3,753** |
| **+$2 raise, 50% rebate** | **$41.13** | — | **$35.13** | **$3,513** |

### Thresholds to Test (Optimizer WS4)

| Raise $ | Move Required | Risk |
|---------|---------------|------|
| $2 | 0.02% on $10k | Ultra-tight — may get stopped by noise |
| $5 | 0.05% on $10k | Tight — filters most noise |
| $10 | 0.10% on $10k | Moderate — misses some "saw green" trades |
| $20 | 0.20% on $10k | Conservative — only converts clear winners |

The optimal threshold depends on:
- Spread/slippage on the specific coin
- ATR at entry time (volatile vs quiet periods)
- Whether the raise is static ($X) or ATR-adaptive (0.1 × ATR)

---

## What the Backtester Must Confirm

These numbers are theoretical. The Python backtester (WS3) needs to validate:

1. **Exact 86% figure** — Is it really 86% of losers that saw green? On which coins? In which market regime?
2. **$2 raise feasibility** — On 1m candles, does a 0.02% move happen fast enough to trigger the raise, or does price gap through it?
3. **Noise stop-outs** — How many trades that would have been full TP wins get stopped at breakeven+$2 instead?
4. **Regime sensitivity** — Does the 86% hold in bull, bear, and crash regimes?
5. **Daily rebate settlement** — Exact modeling of 5pm UTC credit, not simplified % reduction

---

## Commission Modeling in Backtester

The Python backtester must implement:

```
On entry:  deduct $6 from equity
On exit:   deduct $6 from equity
At 5pm UTC daily:
    total_comm_today = count_of_sides_today × $6
    rebate = total_comm_today × rebate_pct
    equity += rebate
    reset daily counter
```

This is NOT the same as reducing commission by rebate_pct. The daily settlement creates a cash flow timing difference that affects drawdown calculations.

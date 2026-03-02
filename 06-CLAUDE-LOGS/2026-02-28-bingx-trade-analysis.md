# BingX Phase 3 — Live Account Report

**Generated**: 2026-02-28 15:15 UTC  |  **Account**: $110.0  |  **Notional/trade**: $50 (5x margin x 10x leverage)

---

## 1. Account Snapshot

```
  Account size : $110.0
  Margin in use: $30.0  (6 open positions x $5.0)
  Run period   : 2026-02-27 15:20 UTC  to  2026-02-28 12:18 UTC
  Closed trades: 46   Open: 6
```

| Scenario | Closed | Open Positions | **TOTAL** | **% of $110** |
|----------|--------|----------------|-----------|------------|
| Worst case — all SLs hit | $-8.49 | $-1.1 | **$-9.59** | **-8.7%** |
| Current — mark-to-market | $-8.49 | +$5.67 | **$-2.83** | **-2.6%** |
| Best case — all trailing TPs hit | $-8.49 | +$11.44 | **+$2.95** | **+2.7%** |

> Trailing TP estimate: 2% callback from current mark price.
> Commission: 0.05% taker per side. Rebate 50% next day.

---

## 2. Open Positions

**Open Positions at Bot Stop**

| Symbol | Dir | Entry | Mark | Move% | Net PnL | Margin ROI | BE |
|--------|-----|-------|------|-------|---------|------------|----|
| VIRTUAL-USDT | SHORT | 0.6923 | 0.6441 | +7.0% | +$3.34 | +66.8% of $5.0 | Y |
| SUSHI-USDT | SHORT | 0.2035 | 0.1909 | +6.2% | +$2.97 | +59.5% of $5.0 | Y |
| ATOM-USDT | SHORT | 1.82 | 1.787 | +1.8% | +$0.86 | +17.1% of $5.0 | Y |
| MUBARAK-USDT | LONG | 0.01285 | 0.01286 | +0.1% | $-0.01 | -0.2% of $5.0 | Y |
| ZKP-USDT | SHORT | 0.07864 | 0.07959 | -1.2% | $-0.64 | -12.7% of $5.0 | n |
| PENDLE-USDT | SHORT | 1.1865 | 1.2056 | -1.6% | $-0.85 | -17.0% of $5.0 | n |

**Position Scenarios** (SL floor / TP target per position)

```
  VIRTUAL-USDT SHORT  |  SL: 0.6923 (BE) -> floor $-0.05  |  Trail 2.0% -> target ~ 0.631218 -> +$4.24
  SUSHI-USDT SHORT  |  SL: 0.2035 (BE) -> floor $-0.05  |  Trail 2.0% -> target ~ 0.187082 -> +$3.89
  ATOM-USDT SHORT  |  SL: 1.82 (BE) -> floor $-0.05  |  Trail 2.0% -> target ~ 1.75126 -> +$1.84
  MUBARAK-USDT LONG  |  SL: 0.01285 (BE) -> floor $-0.05  |  Trail 2.0% -> target ~ 0.013117 -> +$0.96
  ZKP-USDT SHORT  |  SL: 0.079225 -> floor $-0.41  |  Trail 2.0% -> target ~ 0.077998 -> +$0.35
  PENDLE-USDT SHORT  |  SL: 1.196881 -> floor $-0.49  |  Trail 2.0% -> target ~ 1.181488 -> +$0.16
```

- **Open positions**: 6 | BE raised: 4/6
- **Total margin at risk**: $30.0 | notional: $300.0 | entry commission paid: $0.15
- **Unrealized net (mark-to-market)**: +$5.67
- **SL floor net (worst case, all SLs hit)**: $-1.1
- **TP target net (best case, all TPs hit)**: +$11.44

---

## 3. Closed Trade Analysis

> **Context**: The strategy profits via trailing TP — positions must stay open to win.
> 0 of 46 closed trades hit TP. The profitable trades are in the 6 still-open positions above.

**Outcome breakdown**

| Category | Count | Total P&L | Avg P&L |
|----------|------:|----------:|--------:|
| TP / winners | 1 | +$0.05 | +$0.05 |
| SL raised to entry (commission-only loss) | 17 | $-0.91 | $-0.05 |
| Full SL hits | 28 | $-7.64 | $-0.27 |
| **Total** | **46** | **$-8.49** | **$-0.18** |

**Grade and Direction**

| | Trades | Wins | Win% | Total P&L | Avg P&L |
|--|------:|-----:|-----:|----------:|--------:|
| Grade A | 3 | 0 | +0.0% | $-0.22 | $-0.07 |
| Grade B | 43 | 1 | +2.3% | $-8.27 | $-0.19 |
| LONG | 13 | 0 | +0.0% | $-2.86 | $-0.22 |
| SHORT | 33 | 1 | +3.0% | $-5.63 | $-0.17 |

**Symbol performance (closed trades only)**

| Symbol | Total P&L | Note |
|--------|----------:|------|
| Q-USDT | $-1.36 | multiple trades |
| TRUTH-USDT | $-0.95 | multiple trades |
| NAORIS-USDT | $-0.92 | multiple trades |
| AIXBT-USDT | $-0.87 |  |
| LYN-USDT | $-0.71 |  |

> No closed symbol is profitable — all winners are in the open positions.

**Hold times** — avg 55m  |  min 1m  |  max 7h 25m

---

## 4. SL-at-Entry Exit Analysis

> The bot raises SL to **exact entry** once a position is ahead.
> This is NOT true BE+fees. Each such exit costs ~$0.05 gross / ~$0.025 net after rebate.
> True BE+fees = SL at entry + 0.10% (LONG) or entry - 0.10% (SHORT).
> Bot fix applied 2026-02-28: new raises will use entry +/- 0.10%.

| Symbol | Dir | Entry | Exit | P&L |
|--------|-----|------:|-----:|----:|
| BEAT-USDT | SHORT | 0.1949 | 0.194991 | $-0.07 |
| BEAT-USDT | LONG | 0.2041 | 0.204013 | $-0.07 |
| PIPPIN-USDT | LONG | 0.68367 | 0.683462 | $-0.06 |
| SQD-USDT | SHORT | 0.03813 | 0.038141 | $-0.06 |
| ETHFI-USDT | SHORT | 0.4703 | 0.470408 | $-0.06 |
| PENDLE-USDT | LONG | 1.274 | 1.2738 | $-0.06 |
| ELSA-USDT | SHORT | 0.08463 | 0.08464 | $-0.06 |
| ATOM-USDT | SHORT | 1.873 | 1.873 | $-0.05 |
| VET-USDT | SHORT | 0.007403 | 0.007403 | $-0.05 |
| FOLKS-USDT | SHORT | 1.403 | 1.403 | $-0.05 |
| SKR-USDT | SHORT | 0.020131 | 0.020131 | $-0.05 |
| KAITO-USDT | SHORT | 0.3323 | 0.3323 | $-0.05 |
| DEEP-USDT | SHORT | 0.02322 | 0.02322 | $-0.05 |
| WOO-USDT | SHORT | 0.01523 | 0.01523 | $-0.05 |
| THETA-USDT | SHORT | 0.1769 | 0.1769 | $-0.05 |
| BB-USDT | SHORT | 0.02532 | 0.02531 | $-0.03 |
| 1000PEPE-USDT | SHORT | 0.003682 | 0.00368 | $-0.03 |

Total cost of 17 SL-at-entry exits: $-0.91 gross  /  $-0.45 net after rebate

---

## 5. Key Findings

1. Closed P&L: $-8.49 across 46 trades. Current total (mark-to-market): $-2.83 (-2.6% of account).
2. 0 TP_HIT exits from 46 closed trades — the trailing TP mechanism was not triggered before bot stopped. All unrealized gains (+$5.67) are in the 6 open positions.
3. 17 SL-at-entry exits cost +$0.45 net after rebate — avoidable with BE+fees SL (now fixed in bot).
4. If all 6 open trailing TPs hit: total = +$2.95 (+2.7% of $110 account). Worst case (all SLs hit): $-9.59 (-8.7%).
5. Worst single loss: AIXBT-USDT SHORT B $-0.87 (SL_HIT). Best open position: VIRTUAL-USDT SHORT at +57% margin ROI (unrealized).

---

*Report generated by analyze_trades.py*
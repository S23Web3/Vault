# BUILD PLAN: Capital Utilization Analyzer for v3.8.2 Multi-Coin

## Context

User ran v3.8.2 on BERA and RIVER (separate backtests). Results:
- BERA: 746 trades, -$94 net at $250 notional (should be $5000). Pyramiding=4.
- RIVER: 881 trades, -$3.48 net at $250 notional. Pyramiding=4.

User wants to know: how much capital sits idle, how many coins could run in parallel on the same $10K account, and what the combined P&L looks like with 50% commission rebate factored in.

Correct sizing: $5000 notional per position ($250 margin at 20x). Max 4 positions per coin = $1000 margin per coin.

## Scope

**1 file to create:**
`PROJECTS/four-pillars-backtester/scripts/capital_utilization.py`

**Inputs (CSV files):**
- `C:\Users\User\Downloads\bera new.csv`
- `C:\Users\User\Downloads\4Pv3.8.2-S_BYBIT_RIVERUSDT.P_2026-02-11_3989d.csv`

**No permissions needed beyond writing 1 new file.**

## What the Script Computes

### Per Coin
1. Parse entry/exit timestamps from CSV
2. Build timeline: for every 5-min bar, count open positions (0-4)
3. Compute: max concurrent, avg concurrent, % time flat, % time at each level (1/2/3/4 positions)
4. Margin deployed per bar = open_positions * $250 (margin per position at $5000 notional, 20x)
5. Peak margin, average margin, idle margin (= $10000 - margin_in_use)
6. Average hold time in hours
7. Gross P&L at $5000 notional (scale from CSV % returns)
8. Commission: 746/881 trades * $16/RT = total commission
9. Rebate: 50% of total commission back
10. Net P&L = gross - commission + rebate

### Combined (BERA + RIVER)
1. Overlay both timelines on same clock
2. Combined margin per bar = BERA margin + RIVER margin
3. Peak combined margin, avg combined margin
4. Total idle capital = $10000 - peak_combined_margin
5. How many more coins could fit: floor(idle_capital / max_margin_per_coin)
6. Combined P&L table

### Output Table Format
```
=== CAPITAL UTILIZATION: v3.8.2 (31 days, $5000 notional, 20x, $250 margin/pos) ===

                          BERA        RIVER       COMBINED
Trades                    746         881         1,627
Avg concurrent pos        2.3         1.8         4.1
Max concurrent pos        4           4           8
% time flat               10%         30%         5%
% time 1 pos              25%         35%         --
% time 2 pos              30%         20%         --
% time 3 pos              20%         10%         --
% time 4 pos              15%         5%          --
Avg margin in use         $575        $450        $1,025
Peak margin in use        $1,000      $1,000      $2,000
Avg hold time (hrs)       2.5         3.2         --
Gross P&L (scaled)        $X          $X          $X
Commission ($16/RT)       $11,936     $14,096     $26,032
Rebate (50%)              $5,968      $7,048      $13,016
Net P&L                   $X          $X          $X
Net $/trade               $X          $X          $X
Idle capital (avg)        $9,425      $9,550      $8,975
Max coins @ $250 margin   10          10          8-9
```

## Implementation

1. Read both CSVs with pandas
2. For each trade: extract entry_time, exit_time, position_value, net_pnl, net_pnl_pct
3. Create 5-min DatetimeIndex spanning full date range
4. For each bar, count how many positions are open (entry_time <= bar < exit_time)
5. Compute all metrics from the timeline
6. Scale P&L: gross = net_pnl_pct * $5000, subtract $16 commission, add 50% rebate
7. Print table

## Verification
User runs: `python scripts/capital_utilization.py`

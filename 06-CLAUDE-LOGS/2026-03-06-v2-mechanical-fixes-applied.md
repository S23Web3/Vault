# v2 Mechanical Audit Fixes — Applied 2026-03-06

## Build Script
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\build_v2_mechanical_fixes.py`

## Results: 16/16 applied, 0 errors, all files compile clean

## Patches Applied

| # | File | Fix | Root Cause |
|---|------|-----|------------|
| 1 | position_monitor.py | allOrders-first `_detect_exit` — queries real fill price FIRST, state estimates as last resort | C1: PNL_MISMATCH in 85% of trades |
| 2 | position_monitor.py | `check_breakeven` place-then-cancel (new SL first, cancel old after) | Log finding: naked positions 35-60s |
| 3 | position_monitor.py | `_tighten_sl_after_ttp` place-then-cancel | Log finding: 30+ consecutive SL tighten failures |
| 4 | position_monitor.py | `be_buffer` from config (default 0.002 = 0.2%) | H2: hardcoded 0.1% too thin for slippage |
| 5 | main.py | Commission fallback 0.001 -> 0.0016 | H3: wrong fallback compounds with thin buffer |
| 6a | risk_gate.py | `max_atr_ratio` in __init__ | M1: Q-USDT 2.58% ATR passes through |
| 6b | risk_gate.py | Log max_atr_ratio | — |
| 6c | risk_gate.py | Check 5b: block if atr_ratio > max (default 0.015) | M1 |
| 7a | state_manager.py | `atr_at_entry` + `sl_price` CSV header | Data gap: ATR lost after position closes |
| 7b | state_manager.py | `atr_at_entry` + `sl_price` CSV row | — |
| 8 | position_monitor.py | allOrders limit 20 -> 50 | M3: 47 coins push fills outside window |
| 9a | position_monitor.py | Rename `ttp_act` -> `be_activation` (declaration) | M2: misleading variable name |
| 9b | position_monitor.py | Rename `ttp_act` usages | — |
| helper | position_monitor.py | `_cancel_open_sl_orders_except_latest` method | Needed by Fix 2 + 3 |
| cfg1 | config.yaml | `be_buffer: 0.002` | — |
| cfg2 | config.yaml | `max_atr_ratio: 0.015` | — |

## New Method: `_cancel_open_sl_orders_except_latest`
Fetches open orders, finds all STOP orders for symbol+direction, sorts by orderId (ascending), cancels all except the newest. This ensures the just-placed SL survives while old SLs are cleaned up.

## New Method: `_cleanup_orphaned_orders`
After allOrders confirms a real fill, cancels any remaining pending orders for that symbol+direction (SL, TP, trailing).

## Key Architecture Change: `_detect_exit` Flow
Before: check pending orders -> infer from remaining -> use state price
After: query allOrders for real fill price -> if found, use it + cleanup orphans -> if not found, check pending orders for reason only -> state price as absolute last resort (with WARNING log)

## Overlap/Contradiction Analysis

**Overlapping findings (same root cause):**
- C1 + H1: both about estimated exit prices. Fix 1 resolves both.
- C2 + C3: both about TTP exit pricing. v2 native mode eliminates both.
- H2 + H3: compound error. Wrong commission + thin buffer = BE too close.
- Cancel-then-place + H1/H2/H3: different mechanism, same symptom (negative BE trades).

**Tradeoffs:**
- be_buffer 0.2%: more slippage protection, but position must go 0.36% in profit before BE triggers
- max_atr_ratio 0.015: blocks ultra-volatile coins (reduces blowup) but also blocks biggest movers
- allOrders-first: +1 API call per position per cycle (rate limit consideration with 25 positions)

# BingX Bot v1 vs v2: Mechanical Research -- Why Trades Execute Wrong

**Date:** 2026-03-06
**Scope:** Root cause analysis of every incorrect trade pattern, v1 vs v2 architecture comparison, visual diagrams of all entry/exit scenarios.

---

## Part 1: Why v1 Trades Execute Wrong

### The Core Problem: Two Exit Paths Give Different Prices

v1 has TWO independent systems detecting exits. They race each other. Whichever fires first determines the exit price recorded in trades.csv:

```
                     EXCHANGE FILLS ORDER
                            |
              +-------------+-------------+
              |                           |
     WebSocket (WS)               Polling (30s cycle)
     ~100ms latency               ~30s latency
              |                           |
     ACTUAL fill price            ESTIMATED price
     from order.avgPrice          from state sl_price/tp_price
              |                           |
     _handle_close_with_price     _handle_close -> _detect_exit
              |                           |
              +-------------+-------------+
                            |
                     state_manager.close_position()
                            |
                     trades.csv (ONE price recorded)
```

**The race:** If WS fires first (100ms), you get the REAL exchange fill price. If polling fires first (position already gone by next 30s check), you get the ESTIMATED trigger price from state.

**Why this matters:** STOP_MARKET orders fill at MARKET price when triggered, not at the stopPrice. Slippage between trigger and fill can be 0.01% to 0.5%+ depending on liquidity and volatility.

---

### Issue 1: PNL_MISMATCH (73 of 87 trades)

**What happens:**
```
  ENTRY: BUY LONG BEAT-USDT @ 0.2932
  SL set at: 0.28881961 (STOP_MARKET trigger price)

  Exchange fills SL at: 0.28876 (actual fill -- slipped 0.00006 below trigger)

  v1 records exit_price = 0.28881961 (the trigger price, NOT the fill)
  v1 calculates PnL from trigger price

  REAL PnL and RECORDED PnL differ by the slippage amount
```

**Root cause in code:**

`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` lines 161-167:
```python
elif tp_orders and not sl_orders:
    exit_reason = "SL_HIT"
    exit_price = pos_data.get("sl_price")  # <-- TRIGGER PRICE, NOT FILL
```

The polling path uses `pos_data.get("sl_price")` which is the stopPrice stored in state.json at order placement time. This is the TRIGGER price, not what the exchange actually filled at.

**Why allOrders doesn't always save it:**

`_detect_exit()` calls `_fetch_filled_exit()` FIRST (line 121), which queries allOrders for real avgPrice. But when the polling path finds pending orders still in the open orders list (one SL remaining = TP was hit, or vice versa), it SKIPS the allOrders query and jumps straight to the estimate path (lines 154-167).

**The allOrders path only runs when NO pending orders exist** -- meaning both SL and TP are already gone from the exchange. This is a narrow window.

**Additionally:** The PnL calculation in the bot uses `notional * commission_rate` for commission (line 343), but the recorded PnL in CSV comes from `pnl_gross - commission` where gross is computed from the estimated exit price. So the PnL number in CSV is wrong in two ways: wrong exit price AND the commission math is based on the wrong gross.

**Impact:** Every single trade's PnL is off by $0.02-$0.10. Over 87 trades, this compounds into significant tracking error. You cannot trust the trades.csv for performance analysis.

---

### Issue 2: SL_AT_ENTRY (16 of 87 trades)

**What happens:**
```
  ENTRY: BUY LONG RENDER-USDT @ 1.393
  SL placed at: ~1.365 (2x ATR below entry)

  Exchange fills SL at: 1.365 (actual)

  BUT v1 records exit_price = 1.394 (???)
  Exit% = +0.07% from entry

  This looks like SL hit AT entry, but the real SL was 2% below
```

**Root cause:** Same as Issue 1. The exit price recorded is not the fill -- it is the state estimate. But in this case, the state `sl_price` was UPDATED after entry because:

1. BE auto-raise triggered: mark price crossed `entry * (1 + be_act)` threshold
2. Old SL cancelled, new SL placed at `entry * (1 + commission_rate + be_buffer)`
3. `sl_price` in state updated to the new BE price
4. When exit detected by polling, `pos_data.get("sl_price")` returns the BE price
5. BUT `be_raised` flag was NOT set (race condition or flag not persisted before exit)

**OR** the exit price is genuinely near entry because:
- The coin has very low ATR (e.g., RENDER ATR ratio ~0.07%)
- 2x ATR SL = 0.14% from entry
- After commission (0.16% round-trip), this is a guaranteed loser
- Risk gate `min_atr_ratio: 0.003` should block this but the signal's ATR was computed from a different timeframe or stale data

**Visual of the problem:**
```
  ENTRY -------> 1.393
  BE price ----> 1.3935 (+0.04% = commission + buffer)
  Real SL -----> 1.365  (-2.0% = 2x ATR)

  If BE raised:
    SL moved to -> 1.3935
    Record shows exit at 1.394 (estimate of BE price)
    Exit% = +0.07% -- tiny positive but commission eats it

  If NOT BE raised:
    SL stays at -> 1.365
    Record shows exit at 1.394 (??? wrong state data)
    The sl_price in state.json was corrupted or overwritten
```

---

### Issue 3: MICRO_WIN_LOSS (13 of 87 trades)

**What happens:**
```
  Price moves +0.08% in your favor
  Commission = 0.16% round-trip
  Net PnL = +0.08% - 0.16% = -0.08% (LOSS)
```

**This is not a code bug.** This is a design consequence:

1. BE buffer (0.2%) + commission (0.16%) = BE SL placed at +0.36% from entry
2. If market touches BE activation (+0.4%) then reverses
3. SL fills at +0.36% (if no slippage)
4. Gross = +0.36%, commission = 0.16%, net = +0.20% -- should be profitable

BUT if the exit price recorded is ESTIMATED (not real fill), and slippage pushes the real fill below the +0.16% commission line, the recorded PnL shows positive when it was actually negative, or vice versa.

**The real issue:** You cannot tell if these are genuine micro-wins eaten by commission or recording errors. The exit prices are not trustworthy.

---

### Issue 4: TTP_PRICE_SUSPECT (5 trades)

**What happens:**
```
  TTP engine evaluates 5m candle
  Trail level = 0.2800573
  Engine says: candle low crossed trail -> CLOSE

  position_monitor places MARKET close order
  Exchange fills at: 0.2798 (market price, different from trail)

  v1 records exit_price = 0.2800573 (the trail level, NOT market fill)
```

**Root cause chain:**

1. `signal_engine.py` sets `ttp_close_pending = True` with `ttp_trail_level` in state
2. `position_monitor.check_ttp_closes()` places MARKET close via `_place_market_close()`
3. `_place_market_close()` returns `{"avgPrice": X}` from the order response
4. If avgPrice > 0, it gets stored as `ttp_fill_price` in state
5. On next polling cycle, `_detect_exit()` checks `ttp_exit_pending` flag
6. If `ttp_fill_price` exists, uses it (ACTUAL). If not, falls back to `ttp_trail_level` (ESTIMATED)

**The gap:** BingX MARKET order response does NOT always include `avgPrice` immediately. The order may be "accepted" but not yet "filled" at response time. In that case, `avgPrice = 0` in the response, and the code falls back to trail_level:

```python
# position_monitor.py lines 666-670
if fill_price and fill_price > 0:
    updates["ttp_fill_price"] = fill_price
else:
    logger.info("TTP close executed: %s (no fill price in response)", key)
```

**v1 WS listener cannot catch this either** because MARKET order fills have `order_type = "MARKET"`, and the v1 WS parser only matches `TAKE_PROFIT` and `STOP`:

```python
# ws_listener.py lines 104-110 (v1)
if "TAKE_PROFIT" in order_type:
    reason = "TP_HIT"
elif "STOP" in order_type:
    reason = "SL_HIT"
else:
    return None  # <-- MARKET falls through here
```

So TTP market close fills are INVISIBLE to the WS listener. The only chance for an actual fill price is the order response, which may return 0.

---

### Issue 5: RISK_GATE_MISS (6 trades -- all Q-USDT)

**What happens:**
```
  Q-USDT ATR ratio = 2.58%
  SL = 2x ATR = 5.16% from entry
  On 10x leverage: 51.6% of margin lost on SL hit

  Risk gate has min_atr_ratio: 0.003 (blocks too-quiet coins)
  Risk gate has NO max_atr_ratio (doesn't block too-volatile coins)

  Q-USDT passes risk gate -> enters trade -> massive SL loss
```

**Root cause:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\risk_gate.py` lines 69-73:
```python
if atr_ratio < self.min_atr_ratio:
    # blocks too quiet
    return False, reason
# NO CHECK FOR atr_ratio > max_atr_ratio
```

Row 247: Q-USDT SHORT, SL_HIT, pnl=-$2.5570 (biggest single loss in 87 trades)

---

### Issue 6: EXIT_UNKNOWN (2 trades)

**What happens:** Position exists in state but not on exchange. Neither allOrders nor pending orders found any exit.

**Root cause:** The position was closed externally (manual close on BingX app, or liquidation), or the allOrders query window (limit=50) missed the filled order because too many other orders happened between entry and exit.

---

## Part 2: v1 vs v2 Architecture Comparison

### Exit Detection: Side by Side

```
=======================================================================
                        v1 EXIT DETECTION
=======================================================================

  SL/TP fills on exchange
       |
       +---> WS listener
       |     - Catches: TAKE_PROFIT, STOP
       |     - MISSES: MARKET (TTP close falls through)
       |     - Price: ACTUAL avgPrice from WS event
       |
       +---> Polling (30s cycle)
             - Checks: position gone from exchange?
             - _detect_exit():
               1. allOrders query (ACTUAL price) -- BUT only if no pending orders
               2. Pending order inference (ESTIMATED price) -- MOST COMMON PATH
               3. EXIT_UNKNOWN fallback (ESTIMATED sl_price)


=======================================================================
                        v2 EXIT DETECTION
=======================================================================

  SL/TP/TRAILING fills on exchange
       |
       +---> WS listener
       |     - Catches: TAKE_PROFIT, STOP, TRAILING_STOP_MARKET
       |     - Still misses: MARKET (but TTP in native mode uses TRAILING, not MARKET)
       |     - Price: ACTUAL avgPrice from WS event
       |
       +---> Polling (30s cycle)
             - Checks: position gone from exchange?
             - _detect_exit():
               1. TTP fill price if stored (ACTUAL)
               2. Native trailing: if trailing_order_id not in pending -> TRAILING_EXIT
                  -> queries allOrders for ACTUAL avgPrice
               3. Pending order inference (ESTIMATED) -- same fallback as v1
               4. _fetch_filled_exit allOrders query (ACTUAL)
```

### The Key v2 Improvement: Native Trailing Eliminates the MARKET Order Gap

```
v1 TTP EXIT (engine mode):
  Signal engine evaluates 5m candle -> ttp_close_pending
  Monitor places MARKET close order
  WS cannot capture MARKET fills -> price lost
  Polling uses trail_level ESTIMATE

  Timeline:
  |---- 5m candle ----|---- next 30s poll ----|
  ^                   ^                       ^
  candle forms        engine evaluates        market close placed
  (price moves)       (delayed by candle)     (fills at market, price unknown)

  WORST CASE: 5m candle + 30s poll = ~5.5 minute delay from price event to exit
  Exit price: ESTIMATED (trail_level)


v2 TTP EXIT (native mode):
  Executor places TRAILING_STOP_MARKET at entry time
  BingX exchange handles trailing internally
  WS captures TRAILING_STOP_MARKET fill instantly

  Timeline:
  |-- price crosses activation --|-- BingX trails --|-- trail hit --|
  ^                              ^                  ^               ^
  entry                          activation         trailing        fill
  (immediate)                    (exchange-native)  (exchange-native) (WS: ~100ms)

  WORST CASE: WS latency (~100ms)
  Exit price: ACTUAL (avgPrice from WS event)
```

### SL Response to Market Price

```
=======================================================================
                   v1: SL REACTS TO MARKET PRICE
=======================================================================

ENTRY @ 100.00, SL @ 96.00 (2x ATR), BE activation @ 100.40

  Time 0m:   Entry. SL=96.00. Monitor checks every 30s.

  Time 2m:   Mark=100.50. BE check: 100.50 > 100.40? YES.
             -> Cancel SL @ 96.00
             -> Place new SL @ 100.36 (entry + commission + buffer)
             -> be_raised = True

  Time 5m:   TTP engine evaluates 5m candle.
             If candle high > activation: TTP state -> ACTIVATED

  Time 10m:  TTP evaluates next 5m candle.
             Updates extreme. Checks trail_level.

  Time 10.5m: check_ttp_sl_tighten() runs (30s interval)
              If TTP ACTIVATED: tighten SL toward extreme * (1 - 0.3%)

  PROBLEM: SL only moves on 30s check cycles. Between checks, price can
           spike and reverse. SL lags behind market by up to 30 seconds.

  PROBLEM: TTP only evaluates on 5m candle CLOSE. Intra-bar extremes
           are not tracked until the bar closes. A candle that spikes +3%
           then crashes -2% will show TTP the LOW first (pessimistic eval),
           triggering close BEFORE recording the +3% extreme.


=======================================================================
                   v2: SL REACTS TO MARKET PRICE (native mode)
=======================================================================

ENTRY @ 100.00, SL @ 96.00 (2x ATR), TRAILING_STOP_MARKET placed at entry

  Time 0m:   Entry. SL=96.00. TRAILING activation @ 100.80 (0.8% above entry).
             Trail distance = 0.3%.
             All managed by BingX exchange -- zero Python involvement.

  Time 2m:   Mark=100.50. BE check: 100.50 > 100.40? YES.
             -> SL raised to 100.36 (same as v1)

  Time ?:    Mark crosses 100.80 (activation price).
             BingX activates trailing internally.
             Trail SL = 100.80 * (1 - 0.003) = 100.498

  Time ?:    Mark rises to 101.50 (new high).
             BingX moves trail SL to 101.50 * (1 - 0.003) = 101.196
             INSTANT -- exchange tick-level granularity.

  Time ?:    Mark drops to 101.196.
             BingX fires TRAILING_STOP_MARKET.
             WS notification with ACTUAL fill price.

  ADVANTAGE: No 5m candle delay. No 30s polling delay.
             Exchange-native tick-by-tick trailing.
             Actual fill price captured via WS.
```

---

## Part 3: All Entry/Exit Scenarios (Visual)

### Scenario A: Normal SL Loss (No BE, No TTP)

```
  Price
    ^
    |
    |   ENTRY -----> * (buy LONG @ 100.00)
    |                |
    |                |  price drops
    |                v
    |   SL --------> X (STOP_MARKET triggers @ 98.00)
    |                  (fills at 97.95 -- slippage)
    |
    +----------------------------------------> Time

  v1 records: exit_price = 98.00 (trigger price, ESTIMATED)
  v2 records: exit_price = 97.95 (WS avgPrice, ACTUAL)

  Difference: v1 shows -2.00% loss, v2 shows -2.05% loss (more accurate)
```

### Scenario B: BE Raise -> SL at Breakeven

```
  Price
    ^
    |          BE activation
    |          (entry + 0.4%)
    |               |
    |   100.40 -----+------* (mark crosses activation)
    |               |      |
    |   ENTRY ---> 100.00  |  SL cancelled, new SL @ 100.36 (BE + fees)
    |               |      |
    |   Old SL     98.00   |  (cancelled)
    |                      |
    |                      |  price reverses
    |                      v
    |   New SL ---------> X (STOP_MARKET triggers @ 100.36)
    |                       (fills at 100.32 -- slippage)
    |
    +----------------------------------------> Time

  v1 (if WS catches):  exit_price = 100.32 (ACTUAL)
     pnl_gross = (100.32 - 100.00) * qty = +0.32%
     commission = 0.16%
     pnl_net = +0.16% -- POSITIVE (buffer protected)

  v1 (if polling catches): exit_price = 100.36 (ESTIMATED from state)
     pnl_gross = (100.36 - 100.00) * qty = +0.36%
     pnl_net = +0.20% -- POSITIVE (but wrong number)

  v1 (if slippage > buffer): fill at 100.10
     pnl_gross = +0.10%
     commission = 0.16%
     pnl_net = -0.06% -- NEGATIVE BE TRADE

  v2: Same BE logic, but WS captures ACTUAL fill.
      If slippage > buffer, you SEE the real negative. No masking.
```

### Scenario C: TTP Trailing Exit (Engine Mode -- v1)

```
  Price
    ^
    |                         * extreme (102.50)
    |                        / \
    |                       /   \
    |                      /     \  trail_level = extreme - 0.3%
    |   TTP activation ---+      +--- 102.19 (trail)
    |   (entry + 0.8%)    |      |
    |   100.80 -----------+      |  candle low crosses trail
    |                     |      v
    |   ENTRY ---------> 100.00  X  MARKET close placed
    |                               (fills at 102.10, but recorded as 102.19)
    |
    +---------|---------|---------|-------> Time
           candle 1   candle 2   candle 3
           (5 min)    (5 min)    (5 min)

  DELAYS:
    - TTP only evaluates on 5m candle close (candle 2 shows extreme)
    - Candle 3: low crosses trail -> engine flags close
    - Monitor loop runs -> places MARKET order (30s delay)
    - MARKET fills at current market price (NOT trail_level)

  Total delay from trail cross to fill: up to 5m + 30s = 5.5 minutes

  v1 records: exit_price = 102.19 (trail_level ESTIMATE, or 0 from order response)
  Real fill: 102.10 (market moved further down during 5.5min delay)
```

### Scenario D: TTP Trailing Exit (Native Mode -- v2)

```
  Price
    ^
    |                         * extreme (102.50)
    |                        / \
    |                       /   \  BingX trails internally
    |                      /     \ trail = extreme * (1 - 0.3%)
    |   TTP activation ---+      +--- 102.19 (exchange trail SL)
    |   (entry + 0.8%)    |      |
    |   100.80 -----------+      |  price touches trail
    |                     |      v
    |   ENTRY ---------> 100.00  X  TRAILING_STOP_MARKET fires
    |                               (fills at 102.17, WS reports instantly)
    |
    +---------|---------|---------|-------> Time
         tick-by-tick tracking by exchange

  DELAYS:
    - BingX tracks extreme and trail on every tick (not 5m candles)
    - TRAILING_STOP_MARKET fires on the exchange itself
    - WS reports fill in ~100ms

  Total delay from trail cross to fill: exchange execution time (~50ms)

  v2 records: exit_price = 102.17 (ACTUAL avgPrice from WS)
```

### Scenario E: Pessimistic TTP Evaluation (v1 Only)

```
  Price (within one 5m candle)
    ^
    |
    |   +3.0% --------- * candle HIGH (reached at 2:32)
    |                   /|
    |                  / |
    |   +1.5% -------+  |  (trail would be at +2.7% if extreme updated first)
    |                |   |
    |   +0.8% act ---+   |  (TTP activated during this candle)
    |                    |
    |                    |  candle drops
    |                    v
    |   -1.0% ---------- * candle LOW (reached at 4:58)
    |
    +---|----------------|---> Time
     candle open      candle close

  v1 TTP ENGINE EVALUATION ORDER:
    1. Check if low < trail_level  -> YES, trail crossed, CLOSE (pessimistic)
    2. THEN update extreme from high -> TOO LATE, already closed

  Result: TTP closes at trail based on PREVIOUS extreme, not this candle's high.
  The +3.0% spike is NEVER recorded as the extreme.
  Exit trail_level is computed from a lower extreme -> smaller win.

  v2 NATIVE TRAILING:
    - BingX updates trail on every tick
    - At 2:32: extreme = +3.0%, trail = +2.7%
    - At 4:58: price at -1.0%, but trail already at +2.7%
    - Trail holds at +2.7%, NOT triggered (price would need to drop to +2.7%)
    - If price continues down to +2.7%: TRAILING fires at +2.7%
    - If price bounces: extreme updates higher, trail follows
```

### Scenario F: Ultra-Volatile Coin (Q-USDT, no max_atr_ratio)

```
  Price
    ^
    |
    |   ENTRY ---------> * (SHORT Q-USDT @ 0.01234)
    |                    |
    |   ATR ratio = 2.58% (extreme volatility)
    |   SL = 2x ATR = 5.16% above entry
    |                    |
    |                    |  Q-USDT pumps 5.2%
    |                    v
    |   SL ------------> X (triggers @ 0.01298, fills at 0.01302)
    |
    +----------------------------------------> Time

  Margin impact: 5.16% * 10x leverage = 51.6% of $5 margin = -$2.58 loss

  v1: Risk gate passes Q-USDT (only checks min_atr_ratio 0.003, no max)
  v2: Same risk_gate.py -- STILL NO max_atr_ratio cap

  FIX needed in BOTH: max_atr_ratio: 0.015 in config + risk_gate check
```

---

## Part 4: Summary Table -- What Each Version Gets Right and Wrong

| Aspect | v1 (current) | v2 (native trailing) |
|--------|-------------|---------------------|
| **SL/TP exit price** | ESTIMATED (trigger price from state) when polling detects. ACTUAL only if WS catches first. | ACTUAL via WS for SL/TP/TRAILING. Polling fallback still estimated. |
| **TTP exit price** | ESTIMATED (trail_level). MARKET fills invisible to WS. Order response may return avgPrice=0. | ACTUAL for native mode (TRAILING_STOP_MARKET WS fill). Engine mode same as v1. |
| **TTP latency** | 5m candle + 30s poll = up to 5.5 min | Exchange-native: tick-level, ~50ms |
| **TTP extreme tracking** | 5m candle boundaries only. Intra-bar spikes missed. | Exchange tracks every tick. No missed spikes. |
| **Pessimistic eval** | YES -- checks low BEFORE updating extreme | N/A for native mode. Exchange evaluates correctly. |
| **BE buffer** | Configurable (0.2% default after patch) | Same -- uses same position_monitor |
| **Commission fallback** | 0.0016 (fixed after patch) | 0.0016 |
| **max_atr_ratio** | Config added but risk_gate NOT patched | Same risk_gate -- NOT patched |
| **MARKET fills in WS** | Missed (only TAKE_PROFIT and STOP matched) | Missed for MARKET, but native mode uses TRAILING_STOP_MARKET which IS matched |
| **PnL accuracy** | Wrong for ~85% of trades (estimated exit prices) | Correct for WS-detected exits, wrong for polling fallback |
| **allOrders fallback** | Queries FIRST in patched v1, but polling path often takes precedence | Only queries when no pending orders found -- same gap |

---

## Part 5: What v2 Still Does NOT Fix

1. **Polling fallback still uses estimated prices** -- if WS is down or misses a fill, v2 falls back to the same estimated-price polling path as v1.

2. **v2 _detect_exit() is the OLD v1 code** -- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\position_monitor.py` line 103-160 still uses `pos_data.get("sl_price")` as exit price in the pending-order inference path. The allOrders-first rewrite from v1's audit was NOT ported to v2.

3. **risk_gate.py identical in both** -- no max_atr_ratio in either. Q-USDT still passes.

4. **Engine mode TTP in v2** has the same trail_level estimate problem as v1. Only native mode fixes this.

5. **BE negative trades** -- same be_buffer logic in both. If slippage > buffer, BE trade goes negative in both versions. WS capture in v2 just shows you the real negative instead of masking it.

---

## Recommendations

### For v2 before deploying:

1. **Port the allOrders-first _detect_exit rewrite** from v1 to v2's position_monitor.py. Currently v2 has the OLD detection logic.

2. **Add max_atr_ratio check** to v2's risk_gate.py (copy from v1 config which already has `max_atr_ratio: 0.015`).

3. **Use native mode exclusively** -- engine mode has all the same problems as v1.

4. **Monitor WS health** -- v2's accuracy depends entirely on WS capturing fills. If WS dies, you fall back to v1-quality estimates.

### What native mode in v2 definitively fixes:

- TTP exit price accuracy (TRAILING_STOP_MARKET fills captured by WS)
- TTP latency (tick-level vs 5m candle)
- Pessimistic evaluation eliminated (exchange-native trailing)
- Intra-bar spike tracking (exchange sees every tick)

### What remains broken in both:

- Polling fallback exit prices (when WS misses)
- max_atr_ratio gap (ultra-volatile coins)
- BE buffer vs slippage (design tradeoff, not a bug)

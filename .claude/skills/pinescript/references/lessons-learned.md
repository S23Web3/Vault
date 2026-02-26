# Pine Script Lessons Learned

## 1. commission.percent vs cash_per_order (v3.7 blow-up)

**Bug:** `commission.percent` applies to the **cash quantity**, not notional. With 20x leverage on $500 cash ($10k notional), `commission.percent=0.06` charges $0.30/side instead of the real $6/side.

**Fix:** Always use `strategy.commission.cash_per_order` for leveraged strategies. The value is deterministic — no leverage ambiguity.

```pinescript
// WRONG — charges % of cash qty, not notional
commission_type=strategy.commission.percent, commission_value=0.06

// CORRECT — charges exact $ per order
commission_type=strategy.commission.cash_per_order, commission_value=6
```

---

## 2. Phantom Trade Bug (strategy.close_all + strategy.entry)

**Bug:** `strategy.close_all()` followed by `strategy.entry()` on the same bar creates **two separate trades** — a close ($0 P&L + commission) and a new entry (commission again). This doubles commission on every flip.

**Fix:** Remove `strategy.close_all()` entirely. `strategy.entry()` in the opposite direction auto-reverses the position in one order. Always `strategy.cancel()` stale exit orders before flipping.

```pinescript
// WRONG — 2 trades, 2x commission
strategy.close_all()
strategy.entry("Long", strategy.long)

// CORRECT — 1 trade, 1x commission
strategy.cancel("Exit Short")
strategy.entry("Long", strategy.long)
```

---

## 3. Stochastic K Smoothing Regression (v3.5 → v3.5.1)

**Bug:** v3.5 used `stoch_fast()` which applies `ta.sma(rawK, smooth_k)` — this is standard Fast Stochastic behavior. But the Four Pillars system requires **Raw K** (K smoothing=1, no SMA). The smoothing delayed signals and missed entries.

**Fix:** v3.5.1 reverted to Raw K via `stoch_k()`:

```pinescript
stoch_k(int k_len) =>
    float lowest = ta.lowest(low, k_len)
    float highest = ta.highest(high, k_len)
    highest - lowest == 0 ? 50.0 : 100.0 * (close - lowest) / (highest - lowest)
```

**Rule:** For the Four Pillars system, NEVER apply SMA smoothing to K. The `stoch_fast()` and `stoch_full()` functions in SKILL.md are for other systems only.

---

## 4. AVWAP Standard Deviation = 0 on Bar 1 (v3.6)

**Bug:** When anchoring AVWAP to entry bar, standard deviation is 0 on bar 1 (only one data point). Using AVWAP ± stdev as stop loss creates a near-zero SL distance, causing instant stop-outs.

**Fix:** Floor the SL distance with ATR:

```pinescript
float sl_distance = math.max(avwap_stdev, ta.atr(14))
```

---

## 5. strategy.exit() Collision on Direction Flip

**Bug:** When flipping from long to short, the old `strategy.exit("Exit Long")` order is still pending. If not cancelled, it can collide with the new short entry and cause an unintended exit on the same bar.

**Fix:** Always `strategy.cancel()` the old direction's exit before entering the new direction:

```pinescript
if didEnterThisBar and posDir == "LONG"
    strategy.cancel("Exit Short")    // Cancel old short exit
    strategy.entry("Long", strategy.long)
```

---

## 6. entryBar Must Persist Through Exit (Cooldown)

**Bug:** If `entryBar` resets to `na` when position closes, the cooldown gate (`bar_index - entryBar >= i_cooldown`) breaks — `na(entryBar)` evaluates true, bypassing the cooldown entirely.

**Fix:** Do NOT reset `entryBar` in the state sync block:

```pinescript
if strategy.position_size == 0 and inPosition
    inPosition := false
    posDir     := "FLAT"
    // entryBar NOT reset here — cooldown needs it to persist
```

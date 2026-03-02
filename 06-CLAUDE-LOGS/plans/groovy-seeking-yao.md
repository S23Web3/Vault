# Trailing Take Profit — Research, Examples & Comparison

**Date:** 2026-02-28
**Scope:** Live phase analysis only. No SL work, no BE work. TTP only.
**Files:** `PROJECTS/bingx-connector/trades.csv`, `position_monitor.py`, historical session logs

---

## Context

The live account ($110, $5 margin × 10x = $50 notional) has run 47 trades.
**Result: 0 TP_HIT exits. 46 SL_HIT, 1 EXIT_UNKNOWN.**

The demo 5m phase (same code, fixed TP at 4×ATR) had 4/47 TP_HIT — 8.5% TP rate.

When `tp_atr_mult` was set to `null` for live (per plan: "replace with trailing TP"), no trailing TP was ever built. Result: winners that go profitable eventually reverse and get stopped out at breakeven or the original SL. There is no mechanism to lock in profit.

The BE raise IS working (confirmed 2026-02-27: ELSA, VIRTUAL raised BE live). But BE is a floor, not a profit-locker.

**Root cause:** `tp_atr_mult: null` in config.yaml with no trailing TP replacement.

---

## Step 1: All TTP Examples Found in Session History

| # | Name | Origin | Trigger | Mechanism | Exchange or Code? |
|---|------|---------|---------|-----------|-------------------|
| E1 | Fixed ATR TP | Config default | At entry | TAKE_PROFIT_MARKET at entry ± N×ATR. Static. | Exchange order |
| E2 | ATR Trailing (HTF) | 2026-02-02 build spec | Entry + HTF ATR×2 | Activation at 2×ATR profit, then trails by HTF ATR×2 distance | Exchange trailing order |
| E3 | AVWAP 3-Stage Trailing | 2026-02-11 v3.8.2 Pine Script | AVWAP ±2σ cross | Stage1→2σ, Stage2→AVWAP±ATR after 5 bars, Stage3→Cloud3±ATR | Code-managed (Pine Script) |
| E4 | AVWAP 2σ + 10-Candle Counter | 2026-02-27 confirmed design (TOPIC) | AVWAP ±2σ cross → wait 10 bars | At bar 10: move SL to AVWAP + place TRAILING_STOP_MARKET 2% | Hybrid: code triggers, exchange trails |
| E5 | BingX Native Trailing (immediate) | BingX API docs | Immediate from entry | TRAILING_STOP_MARKET with priceRate=0.02, no activationPrice | Pure exchange order |
| E6 | BingX Native Trailing (with activation) | BingX API docs | activationPrice = entry ± N×ATR | TRAILING_STOP_MARKET fires when activation hit, then trails by priceRate | Pure exchange order |

---

## Step 2: What Is Currently Implemented

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| Fixed TP | **REMOVED** | config.yaml | `tp_atr_mult: null` — no TP order placed at entry |
| Breakeven Raise | **BUILT** | position_monitor.py | Triggers at +0.16% (2×RT commission). One-time only. |
| Trailing TP | **NOT BUILT** | — | Listed under "Features NOT Yet Built" in TOPIC file |
| AVWAP 2σ trigger | **NOT BUILT** | — | No AVWAP calculation in position_monitor |
| 10-candle counter | **NOT BUILT** | — | No counter logic exists |
| TRAILING_STOP_MARKET | **NOT BUILT** | — | BingX API supports it; never wired in |

**Current exit paths (live):**
1. SL_HIT — original SL at 2×ATR
2. SL_HIT at breakeven — if BE raise fired (requires +0.16% move)
3. EXIT_UNKNOWN — fallback detection failure

There is no path that locks in profit beyond breakeven.

---

## Step 3: How Each TTP Would Be Coded in the Bot

### Approach A — Restore Fixed TP (E1)
**Files changed:** `config.yaml` only
**Change:** Set `tp_atr_mult: 4.0` (or any value)
**Mechanism:** At trade open in `executor.py`, place `TAKE_PROFIT_MARKET` order at `entry ± atr×4`. Exchange fires it automatically.
**Complexity:** 1 line in config. Already coded — was working in demo 5m.
**Pros:** Zero new code. Deterministic. Already tested.
**Cons:** Leaves money on table when trend continues. 4×ATR = 2× the SL distance. Fixed target, no adaptation.
**Expected result:** Would have given 4-8 TP hits in 47 live trades (based on demo 5m rate).

---

### Approach B — BingX Native Trailing, Immediate (E5)
**Files changed:** `executor.py` (add trailing order at entry), `config.yaml` (add `trailing_rate`)
**Mechanism:** At entry, alongside placing the SL, ALSO place a `TRAILING_STOP_MARKET` with `priceRate=0.02` (2% from peak). No activationPrice — activates from first tick.
**Complexity:** ~20 lines in executor. One extra API call per entry.
**Pros:** Exchange manages trailing automatically. Survives disconnection. Simple to code.
**Cons:** On small-cap coins that move 0.5-1% normally, a 2% callback means the trailing stop fires before meaningful profit. priceRate is fixed %, not ATR-relative.
**Risk:** Premature exits on low-volatility candles. The trailing activates immediately, meaning a 2% pullback from any high will exit — including pullbacks that are part of normal trend continuation.
**Best for:** High-momentum, high-volatility coins where 2% callback is small relative to the move.

---

### Approach C — BingX Native Trailing, Activation-Gated (E2 + E6)
**Files changed:** `executor.py` (add trailing order with activationPrice), `config.yaml` (add `trailing_rate`, `trailing_activation_atr_mult`)
**Mechanism:** At entry, place `TRAILING_STOP_MARKET` with:
- `activationPrice = entry ± atr × N` (e.g., 2×ATR profit threshold)
- `priceRate = 0.02` (2% callback)
Exchange ignores the order until price reaches activationPrice, then starts trailing.
**Complexity:** ~25 lines in executor. Requires ATR at entry time (already available from plugin).
**Pros:** Won't fire on small noise. Only activates after meaningful profit. Exchange handles everything after activation. Clean and simple.
**Cons:** priceRate (2%) is still a fixed % not ATR-relative. On a 10% mover, 2% callback is tiny; on a 3% mover it may be too tight. activationPrice calculation needs care: for LONG, it's `entry + atr × N`; for SHORT, `entry - atr × N`.
**Key question:** Can bot detect when trailing order fires? Yes — same exit detection as SL/TP: if no pending orders remain, query allOrders for fill. Trailing fills appear as STOP_MARKET fills.

---

### Approach D — AVWAP 2σ + 10-Candle + TRAILING_STOP_MARKET (E4)
**Files changed:** `position_monitor.py` (new `check_trailing_tp` method), `state_manager.py` (new fields: `avwap`, `sigma`, `candle_count_2sigma`), `config.yaml` (params)
**Mechanism (per confirmed user design from TOPIC):**
1. Each 5m bar: recalculate AVWAP and σ for each open position (anchored to entry bar)
2. Detect when mark crosses AVWAP ±2σ
3. Start 10-candle counter from that bar
4. At candle 10: cancel TP, place TRAILING_STOP_MARKET at priceRate=0.02
5. Move SL to AVWAP (additional SL management)
**Complexity:** ~150 lines. New AVWAP/σ calculation per position per bar. Counter state persisted in state.json.
**Pros:** Most faithful to confirmed strategy intent. Waits for real momentum confirmation. Uses strategy logic (AVWAP) as trailing trigger.
**Cons:** Significantly more complex. Requires AVWAP recalculation every 60s per open position. AVWAP anchored to entry bar means it needs full bar history from entry — requires kline fetch per position per bar. May never trigger on short-duration trades. Highest implementation risk.
**Note:** 2σ on a 5m chart for a coin like RIVER might be 1.5-2× ATR. The trigger is real momentum, not noise.

---

### Approach E — Periodic SL Ratchet (code-managed, no new order types)
**Files changed:** `position_monitor.py` (extend check_breakeven into check_trailing_sl)
**Mechanism:** Every 60s monitor loop, for each open position:
- If profit >= 1×ATR: move SL to entry (BE) ← already done by BE raise
- If profit >= 2×ATR: move SL to entry + 1×ATR
- If profit >= 3×ATR: move SL to entry + 2×ATR
- (configurable step table)
**Complexity:** ~40 lines, extending existing check_breakeven pattern. Same API call pattern as BE raise (cancel + replace STOP_MARKET).
**Pros:** Pure code, no new order types. Follows same pattern as working BE raise. Locks in progressive profit without relying on exchange trailing semantics. Easy to debug.
**Cons:** 60s polling gap — if price reverses fast, SL ratchet doesn't help. Can only tighten SL, not set a true trailing. Each ratchet step = 2 API calls (cancel + place).

---

## Step 4: Comparison Table for Decision

| | A: Fixed TP | B: Trailing Immediate | C: Trailing + Activation | D: AVWAP 2σ | E: SL Ratchet |
|---|---|---|---|---|---|
| **Lines of code** | 1 (config) | ~20 | ~25 | ~150 | ~40 |
| **Files changed** | config.yaml | executor.py + config | executor.py + config | position_monitor + state_manager + config | position_monitor.py |
| **Complexity** | Trivial | Low | Low | High | Medium |
| **When does it lock profit?** | At fixed target | Immediately from entry | After N×ATR move | After AVWAP 2σ cross + 10 bars | As profit increases in ATR steps |
| **Handles trend continuation?** | No — exits at target | Yes, up to callback | Yes, up to callback | Yes | Partially |
| **Risk of premature exit?** | Low | High (callback from any high) | Medium (gated by activation) | Low (requires real momentum) | Low |
| **Faithful to strategy design?** | Baseline | Partial | Partial | Yes (confirmed design) | Partial |
| **Survives disconnection?** | Yes (exchange order) | Yes (exchange order) | Yes (exchange order) | Partially (activation phase = bot-managed) | No (bot must be running) |
| **Testability** | Easy | Easy | Easy | Hard | Medium |
| **Recommended for live now?** | As fallback | Not alone | YES — best pragmatic option | Future phase | Complementary to C |

---

## Recommendation

**Phased approach:**
1. **Immediate (today):** Approach C — TRAILING_STOP_MARKET with activation at 2×ATR profit, 2% callback. Minimal code change, exchange-managed after trigger. Tests cleanly.
2. **Later (after confirming C works):** Approach D — replace or supplement with AVWAP 2σ trigger when AVWAP calculation is added.

**Why not A (fixed TP)?** It was already tried in demo 5m. Only 4/47 TP hits = 8.5%. A fixed target misses trend continuation and is the wrong exit model for this strategy.

**Why not B (immediate trailing)?** Activates on noise. A 2% callback from a tiny 0.5% peak means exits on normal volatility. Too risky for small-cap coins.

**Why not D now?** 150 lines + AVWAP recalculation per position per bar is highest risk for a live bot. Correct long-term direction but not "fix today" material.

**Why not E (ratchet)?** Good complement to C, but 60s polling gap makes it unreliable as primary exit. Better as belt-and-suspenders once C is in.

---

## Implementation Plan (Approach C)

**Files to modify:**
1. `PROJECTS/bingx-connector/executor.py` — add trailing order placement after SL order
2. `PROJECTS/bingx-connector/config.yaml` — add `trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`
3. `PROJECTS/bingx-connector/tests/test_executor.py` — add trailing order test case

**Approach C code sketch:**
```python
# In executor.py, after placing SL order:
if cfg.get("trailing_rate") and cfg.get("trailing_activation_atr_mult"):
    atr = signal.get("atr")
    activation_offset = atr * cfg["trailing_activation_atr_mult"]
    if direction == "LONG":
        activation_price = entry_price + activation_offset
    else:
        activation_price = entry_price - activation_offset
    _place_trailing_order(symbol, side, qty, activation_price, cfg["trailing_rate"])
```

**Index update required:**
Add row to `06-CLAUDE-LOGS/INDEX.md` under BingX Connector section for this session.

**Session log to create:**
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-ttp-research.md`

---

## Verification

1. Run `python -c "import py_compile; py_compile.compile('executor.py', doraise=True)"` after edit
2. Run `python -m pytest tests/test_executor.py -v` — new trailing test must pass
3. Watch bot log for: `TRAILING_STOP_MARKET placed` message on next entry
4. Confirm order appears in BingX open orders UI
5. If activation triggers: watch for fill event with trailing exit in trades.csv

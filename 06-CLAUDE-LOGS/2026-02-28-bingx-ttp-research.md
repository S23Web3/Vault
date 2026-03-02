# BingX Trailing TP — Research, Comparison & Implementation
**Date:** 2026-02-28
**Scope:** Live phase only. TTP only (no SL work, no BE work).
**Files touched:** `executor.py`, `config.yaml`, `tests/test_executor.py`

---

## 1. Problem Statement

Live account ($110, $5 margin × 10x = $50 notional) ran 47 trades.
**Result: 0 TP_HIT. 46 SL_HIT, 1 EXIT_UNKNOWN.**

Demo 5m phase (same code, fixed TP at 4×ATR): 4/47 TP_HIT — 8.5% TP rate.

When `tp_atr_mult: null` was set for live (original plan: "replace with trailing TP"), no trailing TP was ever built. Winners that go profitable eventually reverse and get stopped out at breakeven or original SL. There is no mechanism to lock in profit beyond the one-time BE raise.

BE raise IS working (confirmed 2026-02-27: ELSA, VIRTUAL raised BE live). But BE is a floor, not a profit-locker.

**Root cause:** `tp_atr_mult: null` in `config.yaml` with no trailing TP replacement.

---

## 2. Current Implementation Status (before this session)

| Feature | Status | Notes |
|---------|--------|-------|
| Fixed TP | REMOVED | `tp_atr_mult: null` — no TP order placed at entry |
| Breakeven Raise | BUILT | Triggers at +0.16% (2×RT commission). One-time only. |
| Trailing TP | NOT BUILT | Listed under "Features NOT Yet Built" in TOPIC file |
| AVWAP 2σ trigger | NOT BUILT | No AVWAP calculation in position_monitor |
| 10-candle counter | NOT BUILT | No counter logic exists |
| TRAILING_STOP_MARKET | NOT BUILT | BingX API supports it; never wired in |

Current exit paths (live): SL at 2×ATR, or SL at breakeven if BE fired, or EXIT_UNKNOWN fallback. No profit-locking path.

---

## 3. All TTP Examples Found Across Session History

| # | Name | Origin | Trigger | Mechanism | Exchange or Code? |
|---|------|---------|---------|-----------|-------------------|
| E1 | Fixed ATR TP | Config default | At entry | TAKE_PROFIT_MARKET at entry ± N×ATR. Static. | Exchange order |
| E2 | ATR Trailing (HTF) | 2026-02-02 build spec | Entry + HTF ATR×2 | Activation at 2×ATR profit, then trails by HTF ATR×2 distance | Exchange trailing order |
| E3 | AVWAP 3-Stage Trailing | 2026-02-11 v3.8.2 Pine Script | AVWAP ±2σ cross | Stage1→2σ, Stage2→AVWAP±ATR after 5 bars, Stage3→Cloud3±ATR | Code-managed (Pine Script) |
| E4 | AVWAP 2σ + 10-Candle Counter | 2026-02-27 confirmed design (TOPIC) | AVWAP ±2σ cross + wait 10 bars | At bar 10: move SL to AVWAP + place TRAILING_STOP_MARKET 2% | Hybrid: code triggers, exchange trails |
| E5 | BingX Native Trailing (immediate) | BingX API docs | Immediate from entry | TRAILING_STOP_MARKET priceRate=0.02, no activationPrice | Pure exchange order |
| E6 | BingX Native Trailing (with activation) | BingX API docs | activationPrice = entry ± N×ATR | TRAILING_STOP_MARKET fires when activation hit, then trails by priceRate | Pure exchange order |

---

## 4. Approaches Evaluated

### Approach A — Restore Fixed TP (E1)
- Files: `config.yaml` only. Set `tp_atr_mult: 4.0`.
- Already coded, was working in demo 5m (4/47 TP hits).
- Con: Leaves money on table when trend continues. Not the right exit model.

### Approach B — BingX Native Trailing, Immediate (E5)
- Files: `executor.py` + `config.yaml`. ~20 lines.
- Place TRAILING_STOP_MARKET at entry, no activationPrice, priceRate=0.02.
- Con: Activates from first tick. 2% callback fires on normal volatility noise. High premature exit risk.

### Approach C — BingX Native Trailing, Activation-Gated (E2 + E6) ← CHOSEN
- Files: `executor.py` + `config.yaml`. ~25 lines.
- Place TRAILING_STOP_MARKET with activationPrice = entry ± atr×N. Exchange ignores until activation hit, then trails.
- Pro: Won't fire on small noise. Only activates after meaningful profit. Exchange manages after that — survives disconnection.

### Approach D — AVWAP 2σ + 10-Candle + TRAILING_STOP_MARKET (E4)
- Files: `position_monitor.py` + `state_manager.py` + `config.yaml`. ~150 lines.
- Most faithful to confirmed strategy design. Waits for real momentum confirmation.
- Con: Highest complexity, requires AVWAP recalculation per position per bar. Future phase.

### Approach E — Periodic SL Ratchet (code-managed)
- Files: `position_monitor.py`. ~40 lines.
- Extend check_breakeven: at 2×ATR profit move SL to entry+1×ATR, at 3×ATR move to entry+2×ATR, etc.
- Pro: Same pattern as working BE raise. Easy to debug.
- Con: 60s polling gap = unreliable as primary exit. Good complement to C, not standalone.

---

## 5. Comparison Table

| | A: Fixed TP | B: Trailing Immediate | C: Trailing + Activation | D: AVWAP 2σ | E: SL Ratchet |
|---|---|---|---|---|---|
| Lines of code | 1 (config) | ~20 | ~25 | ~150 | ~40 |
| Files changed | config only | executor + config | executor + config | monitor + state + config | monitor only |
| When locks profit? | At fixed target | Immediately | After N×ATR move | After AVWAP 2σ + 10 bars | As profit increases in ATR steps |
| Handles trend continuation? | No | Yes | Yes | Yes | Partially |
| Risk of premature exit? | Low | High | Medium | Low | Low |
| Faithful to strategy? | Baseline | Partial | Partial | Yes | Partial |
| Survives disconnection? | Yes | Yes | Yes | Partial | No |
| Recommended for live now? | Fallback only | No | YES | Future | Complement to C |

---

## 6. Implementation (Approach C)

**config.yaml** — added under `position:`:
```yaml
trailing_activation_atr_mult: 2.0   # activate trail when price reaches entry +/- 2xATR
trailing_rate: 0.02                  # 2% callback from peak once activation hit
```

**executor.py** — new `_place_trailing_order()` method:
- Placed as a separate POST after the main entry order succeeds
- `close_side = SELL` (LONG) or `BUY` (SHORT)
- `type = TRAILING_STOP_MARKET`, `priceRate = 0.02`, `activationPrice = entry ± atr×2`
- Stores `trailing_order_id` + `trailing_activation_price` in state via `update_position()`
- Telegram entry message appended with `Trail: act=X.XXXXX @2%`
- Guard: only runs if `trailing_rate`, `trailing_activation_atr_mult`, and `signal.atr` are all set

**tests/test_executor.py** — 3 new tests:
- `test_trailing_order_placed_on_entry` — LONG: 2 POSTs, TRAILING_STOP_MARKET, priceRate=0.02, activationPrice=102.0, side=SELL
- `test_trailing_short_activation_price` — SHORT: activationPrice=98.0 (100-1×2), side=BUY
- `test_no_trailing_without_config` — no trailing config → only 1 POST (backward compat preserved)

---

## 7. Validation

```
py_compile executor.py           -> OK
py_compile test_executor.py      -> OK
```

Run tests:
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python -m pytest tests/test_executor.py -v
```

---

## 8. Next Steps

**Immediate (after restart):**
- Watch bot log for `Trailing order placed:` on next entry
- Confirm TRAILING_STOP_MARKET order appears in BingX open orders UI alongside the SL

**Future (Approach D):**
- Once Approach C is confirmed working, add AVWAP 2σ trigger (position_monitor.py)
- 10-candle counter → replace trailing with AVWAP-anchored trailing
- This is the full confirmed strategy design from TOPIC-bingx-connector.md

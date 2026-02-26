# Fault Report — Step 1 Build Review
**Date:** 2026-02-24
**Reviewer:** Claude Code (plan mode — read only)
**Scope:** Files needed for CTL Step 1 (demo live)
**Source doc:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md`

---

## Files Reviewed

| File | Lines read |
|------|-----------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` | 118-145 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` | 165-184 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` | 89-113 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` | 1-149 (full) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars.py` | 1-20 |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | 1-31 (full) |

---

## Fault 1 — Test assertion wrong, not function (SEVERITY: LOW)
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` line 178
**Status:** CONFIRMED

The CTL doc stated the bug was in `executor.py` `_round_down()`. That is incorrect.

Reading the actual function at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` lines 123-127:
```python
def _round_down(self, value, step):
    if step <= 0:
        return value
    return math.floor(value / step) * step
```
This is already correct. `math.floor(value / step) * step` is the right implementation.

The bug is in the **test** at line 178:
```python
self.assertEqual(rd(99.99, 0.01), 99.99)
```
`math.floor(99.99 / 0.01) * 0.01` produces `99.99000000000001` due to IEEE 754 float representation. The function is correct; the assertion is wrong.

**Fix required:** Change line 178 in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` from:
```python
self.assertEqual(rd(99.99, 0.01), 99.99)
```
To:
```python
self.assertAlmostEqual(rd(99.99, 0.01), 99.99, places=8)
```
No changes to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py`.

---

## Fault 2 — Integration test missing mock response (SEVERITY: LOW)
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` lines 92-113
**Status:** CONFIRMED

`test_entry_then_close` provides `mock_eg.side_effect` with exactly 2 GET responses:
1. Price response: `{"data": {"price": "0.005"}}`
2. Step size response: `{"data": [{"symbol": "RIVER-USDT", "tradeMinQuantity": "1"}]}`

The executor consumes both in sequence during `execute()`. The mock is then exhausted. When `self.monitor.check()` is called at line 109, it is patched via `mock_mg` (`position_monitor.requests.get`) not `mock_eg` — that patch is correctly namespaced and set at line 107.

The actual failure: `execute()` succeeds, position is recorded, but `monitor.check()` finds the position in state and in the empty API response `{"data": []}` — meaning the position closed. However `close_position()` in `StateManager` writes to `trades.csv`. The assertion at line 113 checks `self.trades_path.exists()`.

**Root cause:** `executor.execute()` calls `self.state_mgr.record_open_position()`. If `execute()` is returning `None` (failed silently), no position is recorded, monitor finds nothing to close, `trades.csv` is never written. Need to confirm `execute()` actually succeeds in this test by adding an intermediate assertion.

**Fix required:** Add `self.assertIsNotNone(self.executor.execute(sig, "RIVER-USDT"), msg="execute must succeed")` at line 106 before `mock_mg` is set. This will surface whether execute fails (and why) rather than failing silently at the trades_path assertion.

---

## Fault 3 — CRITICAL: Plugin imports wrong signal module (SEVERITY: HIGH)
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` line 21
**Status:** CONFIRMED — requires investigation before demo run

Line 21:
```python
from signals.four_pillars import compute_signals
```

This imports from `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars.py`.

The backtester and dashboard use `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py` with `compute_signals_v383`.

These are **different functions with different implementations**. `four_pillars.py` imports from `.stochastics`, `.clouds`, `.state_machine` — a separate modular architecture. `four_pillars_v383_v2.py` is the monolithic version used by the dashboard and backtester.

**Risk:** The plugin may be running a different signal version than the backtester that produced the validated results. The bot signals may not match the backtest signals. This needs to be confirmed before going live.

**Investigation needed:** Compare `four_pillars.py:compute_signals` output columns against `four_pillars_v383_v2.py:compute_signals_v383` output columns. Specifically: does `four_pillars.py` produce `long_a`, `long_b`, `long_c`, `short_a`, `short_b`, `short_c` columns? If not, `get_signal()` in the plugin will always return None — the bot will never trade.

**Fix options:**
- Option A: Change line 21 to import `compute_signals_v383` from `signals.four_pillars_v383_v2` and update the call at line 64
- Option B: Confirm `four_pillars.py` produces identical output — acceptable only if verified

---

## Fault 4 — warmup_bars() returns 200 but strategy only needs 89 (SEVERITY: LOW)
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` lines 135-137
**Status:** INFORMATIONAL

`warmup_bars()` returns 200 (matching `ohlcv_buffer_bars` in config). The UML spec (`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md` section 8) states the correct value should be `max(60, 89) = 89`. 200 is conservative — it delays first signal by ~16h on 5m bars vs ~7h for 89. Not wrong, just slower to first signal.

**No fix required** — 200 is safe. Change to 89 only if you want faster first signal.

---

## Fault 5 — config.yaml missing four_pillars block (SEVERITY: HIGH — blocks explicit config)
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
**Status:** CONFIRMED

Current config has no `four_pillars` block. Plugin `__init__` at line 32:
```python
cfg = (config or {}).get("four_pillars", {})
```
Falls back to `{}` silently — plugin initialises with all defaults. This means:
- `allow_a = True`, `allow_b = True`, `allow_c = False` (defaults match intent — safe)
- `sl_atr_mult = 2.0` (default — safe)
- `tp_atr_mult = None` (default — no TP, runner mode — safe)

No crash, but the block should be explicit so parameters are visible and editable.

---

## Summary — Fix Priority Order

| # | Fault | Severity | File | Action |
|---|-------|----------|------|--------|
| 1 | Wrong import in plugin (`four_pillars` vs `four_pillars_v383_v2`) | HIGH | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` line 21 | Investigate then fix import |
| 2 | Missing `four_pillars` block in config | HIGH | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | Add block + switch plugin |
| 3 | Test assertion uses `assertEqual` on float | LOW | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` line 178 | Change to `assertAlmostEqual` |
| 4 | Integration test missing intermediate assertion | LOW | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` line 106 | Add `assertIsNotNone` after execute |

**Fix Fault 1 first.** If the plugin imports the wrong module, the bot will never emit a signal regardless of config.

---

## Build Order for Step 1

1. Investigate `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars.py` — confirm output columns
2. Fix import in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` line 21 if needed
3. Fix `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` line 178
4. Fix `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` line 106
5. Edit `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` — switch plugin + add `four_pillars` block
6. Run: `python -m pytest "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\" -v` — must be 67/67
7. Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"` — demo mode

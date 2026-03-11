# Next Chat Prompt -- 55/89 Position Manager Engine Build

## Paste this as your first message:

---

Read these files before doing anything else:
1. `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md`
2. `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\MEMORY.md`
3. `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-55-89-scalp.md`

Then read the source of truth for the SL/TP lifecycle:
4. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\55-89-scalp-methodology.md`

Then read these implementation files:
5. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\avwap.py` -- AVWAPTracker class (already built)
6. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v384.py` -- current CPU engine (reference for metrics/commission/equity tracking)
7. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\commission.py` -- CommissionTracker (reuse as-is)
8. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89.py` -- signal module (produces entry signals + stoch columns)
9. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py` -- current dashboard (needs engine swap after build)

---

## Problem

The 55/89 dashboard currently uses `Backtester384` for position management. Backtester384 only knows: ATR stop-loss + simple breakeven raise. That is the WRONG exit logic for 55/89. The 55/89 strategy has a 4-phase SL lifecycle using AVWAP trailing, overzone ratcheting, and Cloud 4 TP activation. This engine does not exist yet.

**Result**: entries are correct (signal module works), but exits are generic ATR stops. Performance is bad because the designed trailing system is not running.

---

## What to build

A new position manager: `engine/backtester_55_89.py`

This engine replaces `Backtester384` in the 55/89 dashboard. It uses the same signal columns (`long_a`, `short_a`, etc.) but manages positions with the 55/89 SL lifecycle instead of generic ATR SL + BE.

---

## The 55/89 SL/TP Lifecycle (4 phases)

### Phase 1 -- Initial SL (bars 0-4 after entry)
- SL = entry_price -/+ sl_mult * ATR (same as current)
- NO breakeven raise in this phase
- AVWAP tracker starts accumulating from entry bar (use `AVWAPTracker` from `engine/avwap.py`)

### Phase 2 -- AVWAP Freeze (bar 5)
- After `avwap_warmup` bars (default 5), freeze the AVWAP state
- SL moves to: frozen_avwap_center - avwap_sigma * sigma (for longs) or + for shorts
- This gives a fixed cushion proportional to actual entry zone dispersion
- SL can only move in the favorable direction (ratchet -- never widen)

### Phase 3 -- Overzone Ratchet (each overzone exit)
- Monitor stoch 9,3 D line for overzone events:
  - LONG: D goes < 20 (oversold) then exits back > 20
  - SHORT: D goes > 80 (overbought) then exits back < 80
  - "Overzone" = continuation signal (pullback complete), NOT exhaustion
- On each overzone exit: recompute live AVWAP -2 sigma, update SL if tighter, increment ratchet_count
- SL ratchets only -- never loosens

### Phase 4 -- TP Activation (ratchet_count >= threshold)
- After `ratchet_threshold` (default 2) overzone exits, TP activates
- TP = Cloud 4 edge +/- tp_atr_offset * ATR
  - Cloud 4 = EMA 72/89 (these MOVE with price -- TP is dynamic)
  - For longs: TP = max(ema_72, ema_89) + tp_atr_offset * ATR
  - For shorts: TP = min(ema_72, ema_89) - tp_atr_offset * ATR
- SL continues ratcheting on further overzone exits (3rd/4th leg occurs in ~3% of trades)

### Key constraints
- AVWAP center trailing is too tight for 1m (designed for 5m). The -2 sigma band gives necessary cushion.
- Cloud 4 MOVES with price -- TP is recalculated every bar, not fixed at entry
- sigma_floor_atr (default 0.5) prevents degenerate zero-sigma bands

---

## Sweep parameters (what the dashboard sliders should control)

| Param | Default | Range | Purpose |
|-------|---------|-------|---------|
| sl_mult | 2.5 | 0.5 - 5.0 | Phase 1 initial SL in ATR multiples |
| avwap_sigma | 2.0 | 1.0 - 3.0 | Sigma band multiplier for AVWAP trail (phases 2-3) |
| avwap_warmup | 5 | 3 - 10 | Bars before AVWAP freeze (phase 1 -> 2 transition) |
| tp_atr_offset | 0.5 | 0.0 - 2.0 | ATR offset beyond Cloud 4 edge for TP (phase 4) |
| ratchet_threshold | 2 | 1 - 4 | Overzone exits before TP activates |

These replace the current `be_trigger_atr` / `be_lock_atr` sliders in the dashboard.

---

## Required signal columns (already produced by ema_cross_55_89.py)

- `long_a`, `short_a` -- entry signals
- `atr` -- ATR values
- `close`, `high`, `low` -- OHLC
- `stoch_9_d` -- stoch 9 D line (for overzone detection)
- `ema_55`, `ema_89` -- for Cloud 4 TP (note: Cloud 4 = 72/89, need to ADD ema_72 computation)

**MISSING**: `ema_72` is not currently computed by the signal module. The signal module computes `ema_55` and `ema_89`. Cloud 4 needs 72 and 89. Either:
- Add `ema_72` to the signal module output, OR
- Compute it inside the position manager

Also need `base_vol` (volume) for AVWAP accumulation -- already present in the DataFrame from parquet load.

---

## Existing code to reuse

| Component | Location | Reuse how |
|-----------|----------|-----------|
| AVWAPTracker | `engine/avwap.py` | Import directly. `.update(hlc3, volume, atr)` per bar. `.bands()` returns (center, +1s, -1s, +2s, -2s). |
| CommissionTracker | `engine/commission.py` | Import directly. Same commission model as Backtester384. |
| Metrics computation | `engine/backtester_v384.py` lines ~500-560 | Copy the metrics dict assembly pattern (total_trades, win_rate, net_pnl, sharpe, profit_factor, max_drawdown_pct, pct_losers_saw_green, total_volume, total_rebate, etc.) |
| Equity curve | `engine/backtester_v384.py` | Same pattern: list of equity values per bar, peaks tracking, drawdown |

---

## Output files

1. `engine/backtester_55_89.py` -- the position manager engine
   - Class: `Backtester5589`
   - Interface: `Backtester5589(params).run(df_sig) -> results dict`
   - Results dict must match Backtester384 output format (metrics, equity_curve, trades_df) so dashboard rendering works unchanged
2. `tests/test_backtester_55_89.py` -- unit tests
3. `scripts/build_backtester_55_89.py` -- build script (writes files, py_compile, ast.parse)

---

## Dashboard integration (AFTER engine verified)

In `dashboard_55_89_v3.py`, swap:
```python
# OLD
from engine.backtester_v384 import Backtester384
# NEW
from engine.backtester_55_89 import Backtester5589
```

And update the sidebar sliders: replace `be_trigger_atr` / `be_lock_atr` with:
- `avwap_sigma` slider
- `avwap_warmup` slider
- `tp_atr_offset` slider
- `ratchet_threshold` slider

Keep `sl_mult` as-is (it controls phase 1).

The GPU sweep should be deferred until this CPU engine is verified. The current CUDA kernel does not support AVWAP phases.

---

## Build rules (mandatory -- non-negotiable)

- Load Python skill (`/python`) before writing any code
- Check file existence before writing -- never overwrite
- Build script: write file, py_compile, ast.parse, report PASS/FAIL
- Every `def` must have a one-line docstring
- NO f-strings with escaped quotes inside triple-quoted build content
- NO backslash paths in strings -- use Path() or forward slashes
- NO bash execution of Python scripts -- give user the run command, wait for output
- Full Windows paths everywhere in output text
- MANDATORY py_compile after every .py file write

---

## Verification steps (after build)

1. `python scripts/build_backtester_55_89.py` -- expect BUILD SUCCESS
2. `python tests/test_backtester_55_89.py` -- expect all tests pass
3. Run single-coin backtest: BTCUSDT 30d with default params, compare trade count and PnL against Backtester384 run (should differ -- different exit logic)
4. Verify AVWAP phases fire: check trades_df for trades that survived past bar 5 (phase 2), and trades with ratchet_count > 0 (phase 3)
5. Verify TP activation: check for trades exited by "tp" reason with ratchet_count >= 2 (phase 4)

---

## What NOT to do

- Do NOT modify `engine/backtester_v384.py` -- it serves the Four Pillars strategy
- Do NOT modify `engine/cuda_sweep.py` -- GPU support comes later
- Do NOT modify `signals/ema_cross_55_89.py` unless adding ema_72 column
- Do NOT modify `dashboard_55_89_v3.py` in this build -- engine swap is a separate step after verification

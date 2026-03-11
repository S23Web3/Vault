# Plan: Backtester5589 Position Manager Engine Build

*Date: 2026-03-07*

---

## Context

The 55/89 dashboard (`scripts/dashboard_55_89_v3.py`) currently uses `Backtester384` for position management. That engine only knows ATR stop-loss + breakeven raise — the wrong exit logic for 55/89. The 55/89 strategy requires a 4-phase SL lifecycle: ATR initial stop → AVWAP freeze → overzone ratcheting → Cloud 4 TP activation. This engine does not exist. Entries fire correctly (signal module works); exits are generic. The purpose of this build is to create `Backtester5589` so the designed trailing system actually runs.

**Dashboard engine swap is deferred** — done only after the new engine is CPU-verified.

---

## Files to Create

| File | Description |
|------|-------------|
| `PROJECTS/four-pillars-backtester/engine/backtester_55_89.py` | New position manager |
| `PROJECTS/four-pillars-backtester/tests/test_backtester_55_89.py` | Unit tests |
| `PROJECTS/four-pillars-backtester/scripts/build_backtester_55_89.py` | Build script (writes + py_compile + ast.parse) |

All confirmed non-existent. Safe to create.

---

## Files to Read (existing — reuse, do not modify)

| File | What to reuse |
|------|---------------|
| `engine/avwap.py` | `AVWAPTracker` class — import directly. `.update(hlc3, volume, atr)`, `.bands()`, `.freeze()` |
| `engine/commission.py` | `CommissionModel` class — import directly, identical usage to Backtester384 |
| `engine/backtester_v384.py` | Metrics dict pattern, equity curve tracking, CommissionModel usage patterns |
| `signals/ema_cross_55_89.py` | Signal columns produced: `long_a`, `short_a`, `atr`, `stoch_9_d`, `ema_55`, `ema_89`, OHLC, `volume` |

**Do NOT modify** `backtester_v384.py`, `cuda_sweep.py`, `signals/ema_cross_55_89.py` (unless adding `ema_72`), or `dashboard_55_89_v3.py`.

---

## `ema_72` Decision

Cloud 4 TP needs `ema_72` and `ema_89`. The signal module computes `ema_55` and `ema_89` but not `ema_72`.

**Resolution**: Compute `ema_72` **inside the position manager** using the same `ema()` function from `signals/clouds_v2.py` that the signal module already uses. This avoids modifying the signal module and keeps the engine self-contained.

---

## `Backtester5589` Class Design

### Interface
```python
class Backtester5589:
    def __init__(self, params: dict = None): ...
    def run(self, df_sig: pd.DataFrame) -> dict: ...
```

### Parameters (replaces be_trigger_atr / be_lock_atr)

| Param | Default | Purpose |
|-------|---------|---------|
| `sl_mult` | 2.5 | Phase 1 initial SL in ATR multiples |
| `avwap_sigma` | 2.0 | Sigma band multiplier for AVWAP trail (phases 2-3) |
| `avwap_warmup` | 5 | Bars before AVWAP freeze (phase 1→2 transition) |
| `tp_atr_offset` | 0.5 | ATR offset beyond Cloud 4 edge for TP (phase 4) |
| `ratchet_threshold` | 2 | Overzone exits needed before TP activates |
| `notional` | 5000.0 | Trade notional |
| `commission_rate` | 0.0008 | Taker rate |
| `rebate_pct` | 0.70 | Daily rebate fraction |
| `initial_equity` | 10000.0 | Starting equity |
| `sigma_floor_atr` | 0.5 | AVWAPTracker floor (passed to constructor) |

### Single-position model
- One open position at a time (`max_positions=1`). No slots, no adds, no re-entry.
- Simplest viable engine to verify the 4-phase logic.

---

## 4-Phase SL/TP Logic (per-bar loop)

### Phase 1 — Initial SL (bars 0 to avwap_warmup-1 after entry)
- On entry: `sl = entry_price - sl_mult * atr` (LONG) or `+ sl_mult * atr` (SHORT)
- Instantiate `AVWAPTracker(sigma_floor_atr)`, call `.update(hlc3, volume, atr)` each bar
- `bars_in_trade` counter increments each bar
- Exit if `low <= sl` (LONG) or `high >= sl` (SHORT) → reason = "sl_phase1"

### Phase 2 — AVWAP Freeze (bar avwap_warmup)
- At `bars_in_trade == avwap_warmup`: call `tracker.freeze()` → store `(frozen_center, frozen_sigma)`
- New SL = `frozen_center - avwap_sigma * frozen_sigma` (LONG) or `+ avwap_sigma * frozen_sigma` (SHORT)
- SL ratchet: `sl = max(sl, new_sl)` for LONG, `sl = min(sl, new_sl)` for SHORT (never widen)
- Exit if `low <= sl` (LONG) or `high >= sl` (SHORT) → reason = "sl_phase2"

### Phase 3 — Overzone Ratchet (on each overzone exit)
Track `stoch_9_d` column (already in df_sig):
- LONG: `in_overzone = d < 20`. Overzone exit fires when `prev_in_overzone=True` and `d >= 20`
- SHORT: `in_overzone = d > 80`. Overzone exit fires when `prev_in_overzone=True` and `d <= 80`

On overzone exit:
1. Call `tracker.update(...)` (already called each bar)
2. Recompute live `sl_candidate = tracker.center - avwap_sigma * tracker.sigma` (LONG)
3. Ratchet: `sl = max(sl, sl_candidate)` for LONG
4. `ratchet_count += 1`

Exit if `low <= sl` or `high >= sl` → reason = "sl_phase3"

### Phase 4 — TP Activation (ratchet_count >= ratchet_threshold)
- Each bar: compute `ema_72` and use stored `ema_89` from df_sig
- LONG: `tp = max(ema_72[i], ema_89[i]) + tp_atr_offset * atr[i]`
- SHORT: `tp = min(ema_72[i], ema_89[i]) - tp_atr_offset * atr[i]`
- Exit if `high >= tp` (LONG) or `low <= tp` (SHORT) → reason = "tp_phase4"
- SL continues ratcheting on further overzone exits

---

## Trade Record

Each closed trade records:
```python
{
    "entry_bar": int,
    "exit_bar": int,
    "direction": "LONG" | "SHORT",
    "entry_price": float,
    "exit_price": float,
    "pnl": float,           # raw PnL in notional dollars
    "commission": float,    # entry + exit commission
    "exit_reason": str,     # "sl_phase1" | "sl_phase2" | "sl_phase3" | "tp_phase4" | "eod"
    "bars_held": int,
    "ratchet_count": int,
    "phase_at_exit": int,   # 1-4
    "saw_green": bool,      # ever unrealized > 0
}
```

---

## Metrics Dict (mirrors Backtester384 output format)

Required fields for dashboard compatibility:
```
total_trades, win_count, loss_count, win_rate,
avg_win, avg_loss, expectancy,
gross_profit, gross_loss, profit_factor,
net_pnl, total_commission, total_rebate, net_pnl_after_rebate,
sharpe, max_drawdown, max_drawdown_pct,
pct_losers_saw_green, saw_green_losers, total_losers,
final_equity, equity_curve, total_volume, total_sides,
avg_positions, max_positions_used, pct_time_flat,
avg_margin_used, peak_margin_used,
tp_exits, sl_exits,
# 55/89-specific additions:
phase1_exits, phase2_exits, phase3_exits, phase4_exits,
avg_ratchet_count, ratchet_threshold_hit_pct
```

---

## Results Dict (identical structure to Backtester384)

```python
return {
    "trades": list[dict],
    "trades_df": pd.DataFrame,
    "metrics": dict,
    "equity_curve": np.ndarray,
    "position_counts": np.ndarray,
}
```

---

## Build Script (`scripts/build_backtester_55_89.py`)

The build script must:
1. Check that `engine/backtester_55_89.py` does NOT exist before writing (fail if it does)
2. Write `engine/backtester_55_89.py`
3. `py_compile.compile(path, doraise=True)` → PASS/FAIL
4. `ast.parse(source)` → PASS/FAIL
5. Check that `tests/test_backtester_55_89.py` does NOT exist
6. Write `tests/test_backtester_55_89.py`
7. `py_compile` + `ast.parse` → PASS/FAIL
8. Print BUILD SUCCESS or BUILD FAILED with reason
9. No f-strings with escaped quotes in triple-quoted content
10. No backslash paths — use `Path()` or forward slashes

---

## Unit Tests (`tests/test_backtester_55_89.py`)

| Test | What it checks |
|------|----------------|
| `test_phase1_sl_fires` | Trade opened, price hits SL within avwap_warmup bars → exit_reason = "sl_phase1" |
| `test_phase2_transition` | Trade survives 5 bars → SL updates to AVWAP-2sigma band |
| `test_phase3_ratchet` | Stoch 9 D dips below 20, exits → ratchet_count increments, SL tightens |
| `test_phase4_tp` | ratchet_count reaches threshold → TP fires on Cloud 4 touch |
| `test_metrics_keys` | Results dict contains all required keys |
| `test_no_positions` | Empty signals df → total_trades = 0, no crash |
| `test_results_dict_structure` | trades_df, equity_curve, position_counts present and correct types |

Tests use synthetic DataFrames (no file I/O). AVWAP warmup set to 3 for speed.

---

## Dashboard Integration (deferred — separate step)

After engine is verified, in `scripts/dashboard_55_89_v3.py`:

**Imports**: Replace `from engine.backtester_v384 import Backtester384` with `from engine.backtester_55_89 import Backtester5589`

**Sliders**: Replace `be_trigger_atr` / `be_lock_atr` with:
- `avwap_sigma` slider (1.0–3.0, default 2.0)
- `avwap_warmup` slider (3–10, default 5)
- `tp_atr_offset` slider (0.0–2.0, default 0.5)
- `ratchet_threshold` slider (1–4, default 2)

Keep `sl_mult` slider as-is.

**bt_params**: Update keys to match `Backtester5589.__init__`.

GPU sweep deferred — CUDA kernel does not support AVWAP phases.

---

## Verification Steps (user runs)

1. `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_backtester_55_89.py"` → expect BUILD SUCCESS
2. `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_backtester_55_89.py"` → expect all tests pass
3. Manual single-coin backtest: BTCUSDT 30d, default params, compare trade count vs Backtester384 (results WILL differ — correct)
4. Check `trades_df`: confirm rows with `phase_at_exit >= 2` exist (AVWAP phases fired)
5. Check `trades_df`: confirm rows with `ratchet_count > 0` exist (phase 3 fired)
6. Check `trades_df`: confirm rows with `exit_reason == "tp_phase4"` exist (phase 4 fired)

---

## Build Order

1. Load Python skill (`/python`) — mandatory before any code
2. Build script writes `engine/backtester_55_89.py` + compiles
3. Build script writes `tests/test_backtester_55_89.py` + compiles
4. Give user run commands, wait for output
5. Dashboard swap is a separate session after verification

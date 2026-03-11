# Plan: 55/89 Dashboard Engine Swap + Verification Runner

## Context
`Backtester5589` (4-phase AVWAP SL/TP lifecycle) was built and verified via unit tests in the previous session.
The dashboard (`dashboard_55_89_v3.py`) and runner script (`run_55_89_backtest.py`) still import and run
`Backtester384` (ATR SL + BE raise logic). This plan upgrades both files to use the correct engine.

## Key findings from code audit

### Engine — no changes needed
- `backtester_55_89.py` already exports `phase1_exits`, `phase2_exits`, `phase3_exits`, `phase4_exits`,
  `avg_ratchet_count`, `ratchet_threshold_hit_pct` in the metrics dict.
- `phase_at_exit` and `ratchet_count` are tracked per trade.
- Assertions in the verification runner are directly computable from results — no engine modification needed.

### Existing runner — wrong engine
- `scripts/run_55_89_backtest.py` EXISTS on disk (untracked git). It uses `Backtester384` with BE params.
- It must be replaced, not extended. **See permission question below.**

### Dashboard — 4 targeted changes
Located in `PROJECTS/four-pillars-backtester/scripts/dashboard_55_89_v3.py`:

| Location | Current | Change |
|----------|---------|--------|
| Line 35 (import) | `from engine.backtester_v384 import Backtester384` | → `from engine.backtester_55_89 import Backtester5589` |
| Line 201 (run fn) | `bt = Backtester384(bt_params)` | → `bt = Backtester5589(bt_params)` |
| Lines 892–899 (sliders) | `be_trigger_atr`, `be_lock_atr` sliders + caption | → 4 new sliders (see below) |
| Lines 957–977 (bt_params) | `tp_mult`, `be_trigger_atr`, `be_lock_atr` keys | → remove; add 4 new keys |

**Do NOT touch**: GPU sweep section, `render_gpu_results`, PDF export, portfolio mode, equity charts.
GPU sweep still uses legacy engine — this is intentional deferral. No warning needed; GPU is unavailable
without CUDA, so the code path is unreachable on this machine.

---

## Core improvement: diagnostic runner, not just an assertion gate

The handoff specifies binary `assert` checks that would block Task 2 on failure with no actionable info.
The improved runner is:
- A proper CLI tool (`--symbol`, `--avwap-sigma`, `--ratchet-threshold`, `--months`)
- Prints a full phase breakdown table (phase1/2/3/4 exit counts + %)
- Prints ratchet distribution (avg, threshold hit %)
- Still runs the assertions — but if they fail, the diagnostic output shows exactly why
- Remains useful for parameter sweeps after the engine swap (not a throwaway script)

---

## Permissions needed

| # | Action | File |
|---|--------|------|
| 1 | WRITE (overwrite OR version) | `scripts/run_55_89_backtest.py` |
| 2 | EDIT | `scripts/dashboard_55_89_v3.py` |
| 3 | Bash | `python -c "import py_compile; ..."` (validation only) |

---

## Task 1 — Verification runner

**File**: `scripts/run_55_89_backtest.py` (overwrite decision pending — see question)

**Args**: `--symbol BTCUSDT --months 1` (default), `--avwap-sigma 2.0`, `--avwap-warmup 5`,
`--tp-atr-offset 0.5`, `--ratchet-threshold 2`, `--sl-mult 2.5`, `--slope-n 5`, `--slope-m 3`

**Output**:
```
=== SIGNALS ===
  Long signals:  N
  Short signals: N

=== RESULTS ===
  Total trades:      N
  Win rate:          X%
  Net PnL:           $X
  Expectancy:        $X

=== PHASE BREAKDOWN ===
  Phase 1 exits (ATR SL):     N  (X%)
  Phase 2 exits (AVWAP freeze): N (X%)
  Phase 3 exits (ratchet SL):  N  (X%)
  Phase 4 exits (TP):          N  (X%)
  Avg ratchet count:           X
  Ratchet threshold hit:       X%

=== VERIFICATION ===
  [PASS] AVWAP phases fired (phase2+3+4 > 0)
  [PASS] Ratchets occurred (avg > 0)
```

**bt_params for runner** (Backtester5589 keys only):
```python
{
    "sl_mult": args.sl_mult,
    "avwap_sigma": args.avwap_sigma,
    "avwap_warmup": args.avwap_warmup,
    "tp_atr_offset": args.tp_atr_offset,
    "ratchet_threshold": args.ratchet_threshold,
    "notional": 5000.0,
    "initial_equity": 10000.0,
    "commission_rate": 0.0008,
    "maker_rate": 0.0002,
    "rebate_pct": 0.70,
}
```

**Run command**: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_55_89_backtest.py" --symbol BTCUSDT --months 1`

---

## Task 2 — Dashboard engine swap (gated on Task 1 output)

**File**: `PROJECTS/four-pillars-backtester/scripts/dashboard_55_89_v3.py`

### Change 1: Import (line 35)
```python
# BEFORE
from engine.backtester_v384 import Backtester384
# AFTER
from engine.backtester_55_89 import Backtester5589
```

### Change 2: run_backtest_55_89 function (~line 201)
```python
# BEFORE
bt = Backtester384(bt_params)
# AFTER
bt = Backtester5589(bt_params)
```

### Change 3: Sidebar sliders (replace lines 892–899)
```python
# REMOVE these 3 lines + caption:
be1, be2 = st.sidebar.columns(2)
be_trigger_atr = be1.slider("BE trigger (ATR x)", 0.0, 3.0, 1.0, 0.1)
be_lock_atr = be2.slider("BE lock (ATR x)", 0.0, 2.0, 0.0, 0.1)
# caption block

# ADD these 4 sliders:
avwap_sigma = st.sidebar.slider("AVWAP sigma", 1.0, 3.0, 2.0, 0.1)
avwap_warmup = st.sidebar.slider("AVWAP warmup (bars)", 3, 10, 5, 1)
tp_atr_offset = st.sidebar.slider("TP ATR offset", 0.0, 2.0, 0.5, 0.1)
ratchet_threshold = st.sidebar.slider("Ratchet threshold", 1, 4, 2, 1)
```

### Change 4: bt_params dict (lines 957–977)
Remove: `tp_mult`, `be_trigger_atr`, `be_lock_atr`, `max_positions`, `cooldown`, `enable_adds`,
`enable_reentry`, `b_open_fresh`, `max_scaleouts`, `checkpoint_interval`

Add: `avwap_sigma`, `avwap_warmup`, `tp_atr_offset`, `ratchet_threshold`

Keep: `sl_mult`, `notional`, `margin`, `leverage`, `commission_rate`, `maker_rate`, `rebate_pct`,
`initial_equity`, `sigma_floor_atr`

**Final bt_params**:
```python
bt_params = {
    "sl_mult": sl_mult,
    "avwap_sigma": avwap_sigma,
    "avwap_warmup": avwap_warmup,
    "tp_atr_offset": tp_atr_offset,
    "ratchet_threshold": ratchet_threshold,
    "notional": notional,
    "margin": margin,
    "leverage": leverage,
    "commission_rate": COMMISSION_RATE,
    "maker_rate": 0.0002,
    "rebate_pct": rebate_pct,
    "initial_equity": initial_equity,
    "sigma_floor_atr": 0.5,
}
```

Note: `margin` and `leverage` are not used by `Backtester5589` but kept for dashboard display purposes
(caption line, PDF metadata). The engine ignores unknown keys via `.get()`.

---

## Task 3 — Lifecycle visualization (optional, no code changes)

Script already exists: `scripts/visualize_sl_lifecycle_v2.py`

Run command: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_sl_lifecycle_v2.py"`

Generates 12 PNGs in `results/sl_lifecycle/`.

---

## Build rules
- Python skill loaded before any code written
- py_compile + ast.parse on every .py written
- Every def has a one-line docstring
- No bash execution of Python (user runs from terminal)
- Full Windows paths in all output text

---

## Verification
1. Run Task 1 runner: `python "...\scripts\run_55_89_backtest.py" --symbol BTCUSDT --months 1`
   - Expect: [PASS] on both assertions, phase2+3+4 exits > 0, avg_ratchet_count > 0
2. Run dashboard: `streamlit run "...\scripts\dashboard_55_89_v3.py"` from backtester root
   - Expect: 4 new sliders visible, no `be_trigger_atr`/`be_lock_atr`, CPU backtest runs
3. Run lifecycle viz: `python "...\scripts\visualize_sl_lifecycle_v2.py"`
   - Expect: 12 PNGs generated in `results/sl_lifecycle/`
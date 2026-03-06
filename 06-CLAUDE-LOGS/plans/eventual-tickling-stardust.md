# Fix Plan: CUDA Dashboard v3.9.4 + BingX Bot Audit Bugs
**Date**: 2026-03-03
**Status**: Ready for approval

---

## Context

Full logic audit of cuda_sweep.py, dashboard_v394.py, and bingx-connector was completed in the previous session. All findings are documented — no fixes were applied. This plan executes them in priority order via a single build script.

---

## Findings Reassessed After Code Read

### CRITICAL #1 — Commission split (taker entry / maker exit)
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py`

Current: `run_gpu_sweep(comm_rate=0.0008)` → kernel: `comm_per_side = notional * commission_rate` (same rate for both sides).

Fix: Add `maker_rate=0.0002` param to `run_gpu_sweep()`. In kernel: add second param `maker_rate`. Compute:
- `entry_comm = notional * taker_rate` (0.0008)
- `exit_comm = notional * maker_rate` (0.0002)

All 6 entry blocks: `equity -= entry_comm`
Exit block (line 184): `net_pnl = raw_pnl - exit_comm`
End-of-backtest close (line 420): `net_pnl = raw_pnl - exit_comm`

**Impact**: All prior GPU sweep P&L numbers are overstated by 0.06% × notional per round-trip.

---

### CRITICAL #2 — pnl_sum missing entry commission
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py`

Current: Entry commission deducted from `equity` only. `net_pnl` (fed into `pnl_sum`) only subtracts exit commission. So `pnl_sum` ≠ `equity - 10000`.

Fix: Change `net_pnl` at exit to: `net_pnl = raw_pnl - exit_comm - entry_comm`
This makes `pnl_sum` equal total round-trip cost. `equity` can drop the entry deduction (it becomes redundant since pnl closes the loop). Or keep both consistent.

**Preferred approach**: Keep `equity -= entry_comm` on entry for mid-trade equity tracking accuracy. At exit: `net_pnl = raw_pnl - exit_comm` and `equity += net_pnl` — this already reflects the entry_comm already deducted. `pnl_sum += net_pnl - entry_comm` OR change pnl_sum to track `equity - 10000` at end. Cleanest fix: `pnl_sum += (net_pnl - entry_comm)` at exit, so pnl_sum matches equity final.

Actually: correct approach — on exit, `net_pnl = raw_pnl - exit_comm`. The entry_comm was already deducted from equity at entry. So `pnl_sum` should be `net_pnl - entry_comm` (include entry cost). **Fix**: change pnl_sum line to `pnl_sum += net_pnl - entry_comm` at both exit points (line 187 and line 422).

---

### HIGH #3 — win_rate as fraction in 3 table locations
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py`

Locations:
- **Line 2563**: GPU Sweep top-20 table — `win_rate` column in `_display_cols` list. Raw decimal.
- **Line 3012**: Portfolio per-coin top-5 table — same column, raw decimal.
- **Line 2863**: Uniform top-10 uses `avg_win_rate` (mean of decimals) — also raw decimal.

Fix: Before each `st.dataframe()` call, add a column rename/format:
```python
_top20["win_rate"] = (_top20["win_rate"] * 100).round(1)
_top20 = _top20.rename(columns={"win_rate": "win_rate%"})
```
Apply same pattern to per-coin top-5 and uniform top-10 (`avg_win_rate` → `avg_wr%`).

---

### HIGH #4 — TTP state lost on restart
**REASSESSED**: Code at signal_engine.py lines 113-127 already restores TTP state from persisted `ttp_state`, `ttp_extreme`, `ttp_trail_level` fields in position state. **This bug was already fixed.** No action needed.

---

### HIGH #5 — WSListener dies permanently, no alert
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ws_listener.py`

After 3 reconnect failures (line 181-182), loop exits silently. No notification.

Fix: After the loop exits (after line 182), emit a CRITICAL log + call a notification hook. Options:
- Write a sentinel file `logs/WS_DEAD` that main.py polling loop detects
- Call `self._alert_callback(...)` if callback registered
- Simplest: increase `MAX_RECONNECT` from 3 to 10, add exponential backoff (5s → 10s → 20s...), and log CRITICAL after each failure so monitoring sees it.

**Chosen approach**: (1) Increase MAX_RECONNECT to 10. (2) Add exponential backoff: `RECONNECT_DELAY * (2 ** min(reconnect_count, 5))`. (3) After exit, write `logs/ws_dead_{timestamp}.flag` file so main.py can detect and alert.

---

### HIGH #6 — _place_market_close() missing reduceOnly
**REASSESSED**: Bug was attributed to `executor.py` but `_place_market_close()` lives in `position_monitor.py` (lines 563-589). The `order_params` dict does NOT include `reduceOnly`.

BingX behavior: In hedge mode (LONG/SHORT dual position sides), specifying `positionSide` on a market order is sufficient — the exchange uses it to reduce that side. Explicit `reduceOnly` is not required for hedge mode. **Risk level: LOW** — hedge mode + positionSide prevents double-open. No fix needed unless BingX rejects without it.

**Decision**: Add `"reduceOnly": "true"` as defensive measure (no downside). One-line change.

---

### HIGH #7 — saw_green uses > instead of >=
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py`

Line 163: `if high[i] > pos_entry[s]:` (LONG)
v390 reference: `>=`

Line 171: `if low[i] < pos_entry[s]:` (SHORT)
v390 reference: `<=`

Fix: Change `>` to `>=` at line 163, `<` to `<=` at line 171.

---

## Build Plan

### One build script: `build_audit_fixes.py`
**Location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_audit_fixes.py`

The script patches the two target files using exact string replacement (no full rewrite needed). After each patch, runs `py_compile` + `ast.parse`. Reports PASS/FAIL per fix.

### Files Modified

| File | Fixes Applied |
|------|--------------|
| `engine\cuda_sweep.py` | CRITICAL #1, #2, HIGH #7 (commission split, pnl_sum, saw_green) |
| `scripts\dashboard_v394.py` | HIGH #3 (win_rate % formatting in 3 table locations) |
| `PROJECTS\bingx-connector\ws_listener.py` | HIGH #5 (MAX_RECONNECT + backoff + dead flag) |
| `PROJECTS\bingx-connector\position_monitor.py` | HIGH #6 (defensive reduceOnly) |

### Patch Details for cuda_sweep.py

**Patch A — Kernel signature**: Add `maker_rate` parameter after `commission_rate`:
```
Old: notional, commission_rate,
New: notional, commission_rate, maker_rate,
```

**Patch B — comm_per_side split**: Replace single line with two:
```
Old: comm_per_side = notional * commission_rate
New: entry_comm = notional * commission_rate
     exit_comm = notional * maker_rate
```

**Patch C — All 6 entry blocks**: Replace `equity -= comm_per_side` → `equity -= entry_comm`

**Patch D — Main exit net_pnl** (line 184):
```
Old: net_pnl = raw_pnl - comm_per_side  # exit commission
New: net_pnl = raw_pnl - exit_comm - entry_comm  # exit + entry commission
```
Remove `equity -= comm_per_side` from entry blocks since net_pnl now accounts for full round-trip cost. Wait — see logic below.

**Correct accounting logic**:
- Entry: `equity -= entry_comm` (cost paid upfront, tracked in equity)
- Exit: `net_pnl = raw_pnl - exit_comm` (only exit cost subtracted here)
- `equity += net_pnl` (adds back raw_pnl minus exit cost — entry cost already out)
- `pnl_sum += net_pnl - entry_comm` (full round-trip in pnl_sum)

**Patch E — end-of-backtest close** (line 420): Same as Patch D for net_pnl line. `pnl_sum += net_pnl - entry_comm`.

**Patch F — saw_green** (lines 163, 171):
```
Old: if high[i] > pos_entry[s]:   → New: if high[i] >= pos_entry[s]:
Old: if low[i] < pos_entry[s]:    → New: if low[i] <= pos_entry[s]:
```

**Patch G — run_gpu_sweep() signature**: Add `maker_rate=0.0002` param, pass to kernel.

**Patch H — run_gpu_sweep_multi()**: Same maker_rate threading.

### Patch Details for dashboard_v394.py

3 locations — before each `st.dataframe()` insert column format lines:

**Location 1** — GPU Sweep top-20 (before line ~2566):
```python
_top20["win_rate"] = (_top20["win_rate"] * 100).round(1)
_top20 = _top20.rename(columns={"win_rate": "win_rate%"})
# Update _display_cols to use "win_rate%" not "win_rate"
```

**Location 2** — Portfolio per-coin top-5 (before line ~3013): Same pattern on `_pc_top5`.

**Location 3** — Uniform top-10 (before line ~2904):
```python
_gp_uni_top10["avg_win_rate"] = (_gp_uni_top10["avg_win_rate"] * 100).round(1)
_gp_uni_top10 = _gp_uni_top10.rename(columns={"avg_win_rate": "avg_wr%"})
```

### Patch Details for ws_listener.py

```python
# Old
MAX_RECONNECT = 3
RECONNECT_DELAY = 5

# New
MAX_RECONNECT = 10
RECONNECT_DELAY = 5  # base delay; actual = RECONNECT_DELAY * 2**min(count, 5)
```

In reconnect loop:
```python
backoff = RECONNECT_DELAY * (2 ** min(reconnect_count, 5))
await asyncio.sleep(backoff)
```

After loop exits (failure):
```python
import pathlib, datetime
flag = pathlib.Path("logs") / f"ws_dead_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.flag"
flag.parent.mkdir(exist_ok=True)
flag.write_text("WS listener died after max reconnect attempts")
self.log.critical("WS LISTENER DEAD — flagged at %s", flag)
```

### Patch Details for position_monitor.py

In `_place_market_close()`, add to `order_params`:
```python
"reduceOnly": "true",
```

---

## Verification

After build script runs:
1. `py_compile` passes on all 4 patched files
2. `ast.parse` passes on all 4 patched files
3. User runs dashboard and performs a GPU Sweep on one coin
4. Check that top-20 table shows `win_rate%` column with values like `42.3` not `0.423`
5. Check net_pnl figures — will be lower than previous runs (correct: now includes full entry+exit commission)
6. Run a BingX bot restart test — verify TTP state restores from saved fields in bot-status.json

---

## Out of Scope (MEDIUM/LOW — deferred)

- Stale detection for single-coin GPU Sweep sweep param ranges
- Shared Pool capital model enforcement in kernel
- TTP mid-bar evaluation timing
- Race condition TTP close vs exchange SL/TP
- Commission rate fallback mismatch
- No slippage protection
- Close-remaining missing total_losers/lsg_count
- C trades checkbox / capital label UI tweaks
- Lock gaps + logging gaps in BingX

---

## Files to Create

| File | Purpose |
|------|---------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_audit_fixes.py` | Single build script, patches 4 files, py_compile + ast.parse each |

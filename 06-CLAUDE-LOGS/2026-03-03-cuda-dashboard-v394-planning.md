# CUDA Dashboard v394 — Planning Session
**Date**: 2026-03-03
**Topic**: CUDA GPU sweep spec for dashboard_v394 — corrected handover for new chat

---

## What Happened

Short planning session. No code written.

### 1. Checked existing CUDA handover log
User opened `2026-03-03-cuda-sweep-engine-handover.md` and asked if it was clear.
Confirmed: log is clear, well-structured, 18-issue audit table complete, build order numbered, run commands copy-paste ready.

### 2. User asked to build dashboard spec
Request: "can you build the spec for cuda in the dashboard?"
Refined mid-session: "make it in such a way that it is a session handover for a new chat"

### 3. Identified problem with existing plan file
Compared `06-CLAUDE-LOGS/plans/2026-03-03-cuda-sweep-engine.md` (pre-audit vault plan) against the handover log (post-audit). Found 4 pre-audit errors still in the vault plan:
- Column names `re_long/re_short` (should be `reentry_long/reentry_short`)
- `param_grid[N,5]` with notional inside grid (should be `[N,4]`, notional as scalar arg)
- `tp_mult=0.0` sentinel (should be `999.0`)
- Missing `cloud3_allows_long/short` arrays (plan shows 10 inputs, correct is 12)

### 4. User questioned if spec already existed
"is there no such a spec already?" / "last chat should ve had one"
Acknowledged: yes, handover log exists and is correct. Explained why new spec was still needed:
- Old vault plan has 4 errors — new chat reading it would build broken code
- New spec is dashboard-focused (not full engine + sweep script)
- Adds dashboard-specific details not in handover: `gpu_sweep` mode layout, session state keys, portfolio checkbox wiring, sidebar GPU panel implementation, equity curve bug fix scope

### 5. Wrote corrected dashboard spec
- System plan: `C:\Users\User\.claude\plans\synthetic-mapping-ember.md`
- Vault copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-dashboard-v394-spec.md`

---

## Spec Summary

**Files to create** (via `scripts/build_cuda_engine.py`):
- `engine/cuda_sweep.py` — Numba CUDA kernel (12 inputs, [N,4] param grid, 999.0 sentinel)
- `engine/jit_backtest.py` — @njit CPU core + ensure_warmup()
- `scripts/dashboard_v394.py` — v392 base + gpu_sweep mode + portfolio JIT + sidebar GPU panel

**sweep_all_coins_v2.py deferred** — not in this build.

**Key architecture facts locked in spec**:
- 12 kernel input arrays (4 price + 4 entry signals + 2 reentry + 2 cloud3 gates)
- param_grid shape [N,4]: [sl_mult, tp_mult, be_trigger_atr, cooldown]
- notional + commission_rate as scalar kernel args
- tp_mult=999.0 means no TP
- Welford's online variance for Sharpe (no per-trade list in kernel)
- ThreadPoolExecutor workers must NOT call st.* (all rendering in main thread)
- ensure_warmup() at @njit module import prevents first-run freeze
- Base v392 (NOT v393 — has IndentationError)

---

## Output Files

| File | Notes |
|------|-------|
| `C:\Users\User\.claude\plans\synthetic-mapping-ember.md` | System plan (approved) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-dashboard-v394-spec.md` | Vault copy — use this in new chat |

---

## Next Step

Open new chat, paste:
> Read this spec and build: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-dashboard-v394-spec.md`

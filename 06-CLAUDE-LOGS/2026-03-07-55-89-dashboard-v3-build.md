# 2026-03-07 — 55/89 Dashboard v3 Build Session

## Summary

Built `dashboard_55_89_v3.py` via `build_dashboard_55_89_v3.py`. Six changes from v2, all verified present in output. Build script existed from prior session in same day — ran it, `BUILD SUCCESS`, py_compile + ast.parse both PASS. 47,920 chars output.

## Changes Implemented (v2 -> v3)

### 1. Re-roll seed fix
- `random.seed(counter + int(time.time_ns() % 1_000_000))` on every Re-roll click
- `reroll_counter` in session_state increments per click — guarantees entropy on rapid clicks
- Stale results (`result_single`, `result_portfolio`) cleared on Re-roll
- Same seed approach applied to Random N coin sampler in portfolio mode

### 2. Portfolio capital model
- Sidebar radio: "Shared pool" (default) / "Per-coin independent"
- Shared pool: `per_coin_equity = total_capital / N`, equity curve starts at `total_capital`
- Per-coin: current v2 behaviour, each coin gets full `initial_equity`
- `align_portfolio_equity_55_89()` accepts `pool_mode` + `total_capital` params

### 3. Single mode missing metrics
- Row 3 expanded from 3 cols to 5: `Volume $ | Rebate $ | Net w/Rebate | BE Raises | LSG%`
- `total_volume` from `m.get("total_volume", 0.0)`
- `pct_losers_saw_green` from `m.get("pct_losers_saw_green", 0.0) * 100`

### 4. Portfolio per-coin table
- Added `Rebate $` and `Volume $` columns to per-coin DataFrame

### 5. CPU/GPU toggle
- Single mode only — radio: CPU / GPU (GPU disabled if `CUDA_AVAILABLE=False`)
- GPU mode: `run_gpu_sweep_55_89()` computes signals on CPU, sweeps `sl_mult x be_trigger_atr` grid on GPU
- Output: two heatmaps (net_pnl + sharpe, RdYlGn/Viridis colorscale) + top-3 table
- Grid sliders: `sl_range_max` (0.5-4.0) and `be_range_max` (0.0-2.0)
- TP disabled (sentinel 999.0), cooldown=1

### 6. PDF export
- reportlab + kaleido (both import-guarded)
- `generate_pdf_55_89()` returns bytes: metadata + metrics table + equity curve PNG
- Portfolio mode: per-coin table + portfolio equity curve
- `st.download_button` for download
- CPU single + portfolio only (GPU mode has no equity curve)

## Files

| File | Path | Status |
|------|------|--------|
| Build script | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_55_89_v3.py` | EXISTS (from prior session) |
| Dashboard v3 | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py` | CREATED (47,920 chars) |
| Plan (system) | `C:\Users\User\.claude\plans\parsed-petting-reddy.md` | Written |
| Plan (vault) | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-55-89-dashboard-v3-build-plan.md` | Pre-existed from earlier session |
| Spec prompt | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-55-89-dashboard-v3-prompt.md` | Read (spec input) |

## Verification

- `py_compile.compile()` — PASS
- `ast.parse()` — PASS
- grep confirmed all 6 changes present in output file

## Pending (user runs)

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
streamlit run scripts/dashboard_55_89_v3.py
```

1. Single CPU: BTCUSDT 30d — Volume $ and LSG% in Row 3
2. Single GPU: BTCUSDT 30d — two heatmaps + top-3 table
3. Re-roll: click twice rapidly — different windows, stale results cleared
4. Export PDF: download triggers, PDF has metrics + chart
5. Portfolio Shared pool: 5 coins $10k — equity starts at $10k not $50k
6. Portfolio per-coin table: Rebate $ and Volume $ columns

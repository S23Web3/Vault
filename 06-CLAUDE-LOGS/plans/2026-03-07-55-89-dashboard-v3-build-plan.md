# Plan: dashboard_55_89_v3.py

**Date:** 2026-03-07
**Context:** Upgrade `dashboard_55_89_v2.py` with 5 bug fixes and feature additions. The CUDA engine (`engine/cuda_sweep.py`) was built 2026-03-03 in session `2026-03-03-cuda-dashboard-v394-build.md`. All signal/engine field names verified from source files.

---

## Context

v2 has 3 known bugs (re-roll seed, portfolio capital model, missing metrics) and 2 missing features (GPU sweep mode, PDF export). This plan covers all 5 changes. Output is `scripts/dashboard_55_89_v3.py` created by `scripts/build_dashboard_55_89_v3.py`.

---

## Critical File Paths

| File | Role |
|------|------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v2.py` | Source to copy from (682 lines) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py` | Output (NEW — check does not exist) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_55_89_v3.py` | Build script (NEW) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py` | GPU engine — `run_gpu_sweep()`, `build_param_grid()`, `CUDA_AVAILABLE` |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v384.py` | CPU engine — `Backtester384` |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89.py` | Signal — `compute_signals_55_89()` |

---

## Verified Field Names (from source)

- `metrics["total_volume"]` — exists in `backtester_v384.py:421`
- `metrics["total_rebate"]` — exists in `backtester_v384.py:419`
- `metrics["pct_losers_saw_green"]` — exists in `backtester_v384.py:547`
- Signal cols for GPU: `long_a`, `long_b`, `short_a`, `short_b`, `reentry_long`, `reentry_short`, `cloud3_allows_long`, `cloud3_allows_short` — all produced by `ema_cross_55_89.py`

---

## Change 1: Re-roll seed fix

**Problem:** `random.randint()` reuses same internal state on fast Streamlit reruns — produces identical dates.

**Fix in `roll_random_range()`:**
- Accept an optional `seed` param
- Caller passes `seed = st.session_state.get("reroll_counter", 0) + int(time.time_ns() % 1_000_000)`
- On Re-roll button click: `st.session_state["reroll_counter"] = st.session_state.get("reroll_counter", 0) + 1`
- After storing new `random_range`, also `del st.session_state["result_single"]` and `del st.session_state["result_portfolio"]` if present
- Same seed approach for Random N coin sampler in portfolio mode

---

## Change 2: Portfolio capital mode toggle

**Add to sidebar (portfolio mode only), above "Initial equity" input:**

```
Capital mode: [Shared pool] [Per-coin independent]  (radio, horizontal)
```

- **Shared pool** (default): label = "Total portfolio capital ($)". Compute `per_coin_equity = total_capital / max(N, 1)`. Pass `per_coin_equity` as `initial_equity` in `bt_params`. Portfolio equity baseline = `total_capital` (not `per_coin_equity * N`). Caption: "Each coin gets $X (total $Y / N coins)"
- **Per-coin**: current behaviour. Caption: "Each coin runs with full $X — total implied capital: $Y"

**Change in `align_portfolio_equity_55_89()`:** accept `pool_mode` bool + `total_capital`. When `pool_mode=True`, `baseline = total_capital` for Net PnL calc. When `pool_mode=False`, keep `baseline = initial_equity * n_coins`.

**Change in `render_portfolio_results()`:** pass `pool_mode` + `total_capital` through from session_state cache.

---

## Change 3: Missing metrics (single mode Row 3 + portfolio table)

**Single mode — replace 3-col Row 3 with 5-col:**
```
Trading Volume $ | Rebate $ | Net w/Rebate | BE Raises | LSG%
```
- `Trading Volume $` = `m.get("total_volume", 0)` formatted as `$X,XXX`
- `Rebate $` = `m.get("total_rebate", 0)` (already in v2, keep)
- `Net w/Rebate` (already in v2, keep)
- `BE Raises` (already in v2, keep)
- `LSG%` = `m.get("pct_losers_saw_green", 0) * 100` formatted as `XX.X%`

**Portfolio per-coin table — add 2 columns:**
- `Rebate $` = `round(m.get("total_rebate", 0), 2)`
- `Volume $` = `round(m.get("total_volume", 0), 0)` as int

---

## Change 4: CPU / GPU engine toggle

**Sidebar (under "Engine" subheader, above action buttons, Single mode only):**
```python
if CUDA_AVAILABLE:
    engine_mode = st.sidebar.radio("Engine", ["CPU", "GPU"], horizontal=True)
else:
    engine_mode = "CPU"
    st.sidebar.caption("GPU unavailable — install numba with CUDA support")
```

**When GPU selected, show additional controls:**
- `sl_range_max` slider: 0.5–4.0, default 4.0 (step 0.5) → `sl_mult` grid
- `be_range_max` slider: 0.0–2.0, default 2.0 (step 0.5) → `be_trigger_atr` grid
- Caption: "Grid: sl_mult 0.5–X step 0.5, be_trigger 0.0–Y step 0.5. TP disabled. Cooldown=1."

**GPU run flow (replaces CPU run_backtest_55_89 path):**
```python
# 1. Compute signals on CPU once
df_sig = compute_signals_55_89(df.copy(), sig_params)
# 2. Build param grid
sl_range = np.arange(0.5, sl_range_max + 0.1, 0.5)
be_range = np.arange(0.0, be_range_max + 0.1, 0.5)
param_grid = build_param_grid(
    sl_range=sl_range, tp_range=[], be_vals=list(be_range),
    cooldown_vals=[1], include_no_tp=True
)
# 3. Run GPU sweep
df_sweep = run_gpu_sweep(df_sig, param_grid, notional_val=notional, comm_rate=COMMISSION_RATE)
```

**GPU output (replaces equity curve + trades table):**
- Heatmap 1: `go.Heatmap(x=sl_vals, y=be_vals, z=pnl_pivot, colorscale="RdYlGn")` — net_pnl
- Heatmap 2: same structure, color=sharpe, colorscale="Viridis"
- Top-3 table: first 3 rows of `df_sweep` columns: sl_mult, be_trigger_atr, total_trades, win_rate (%), net_pnl, sharpe, max_dd_pct

**GPU fallback:** If `CUDA_AVAILABLE=False` at runtime (guard at top of GPU run block), warn and fall back to CPU path.

**Portfolio mode stays CPU only** — engine toggle only appears in Single mode.

---

## Change 5: PDF export

**Import at top:**
```python
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors as rl_colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import plotly.io as pio
    KALEIDO_AVAILABLE = True  # kaleido is detected at use time
except ImportError:
    KALEIDO_AVAILABLE = False
```

**Helper function `generate_pdf_55_89(mode, cached, bt_params, date_range) -> bytes`:**
- Uses `io.BytesIO` as buffer
- Page 1: metadata table (symbol/date range/params/timestamp) using `Paragraph` + `Table`
- Page 2: metrics table (all key metrics as rows)
- Page 3: equity curve PNG via `plotly.io.to_image(fig, format="png", width=1000, height=400)` embedded as `RLImage(io.BytesIO(png_bytes))`
- Page 4 (portfolio only): per-coin table + portfolio equity curve PNG
- If kaleido not available: skip images, add text note "Install kaleido for chart images"

**Button placement:** After `render_single_results()` or `render_portfolio_results()` call:
```python
if REPORTLAB_AVAILABLE:
    if st.button("Export PDF"):
        pdf_bytes = generate_pdf_55_89(...)
        st.download_button("Download PDF", data=pdf_bytes,
                           file_name="55_89_" + symbol + "_" + date_str + ".pdf",
                           mime="application/pdf")
else:
    st.caption("PDF export unavailable — install reportlab")
```

---

## Build Script: `build_dashboard_55_89_v3.py`

1. Check `scripts/dashboard_55_89_v3.py` does NOT exist — abort if it does
2. Write full dashboard source as triple-quoted string (NO f-strings with escaped quotes — use concatenation)
3. `py_compile.compile(path, doraise=True)` — must PASS
4. `ast.parse(open(path).read())` — must PASS
5. Print `BUILD SUCCESS` or `BUILD FAILED: <reason>`

---

## Session End Tasks (post-build)

After user confirms build success, update:
- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-55-89-scalp.md` — add v3 dashboard entry
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md` — append session row
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\YYYY-MM-DD-topic.md` — session log

---

## Verification Steps

1. `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_55_89_v3.py"` → expect `BUILD SUCCESS`
2. `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py"` from backtester root
3. Single CPU / BTCUSDT 30d → verify Row 3 has Volume $ and LSG%
4. Single GPU / BTCUSDT 30d → verify two heatmaps + top-3 table render
5. Re-roll: click twice rapidly → different windows each time, old results cleared
6. Export PDF → download triggers, PDF has metrics + chart
7. Portfolio Shared pool / 5 coins / $10k → equity curve starts at $10k not $50k
8. Portfolio per-coin table → Rebate $ and Volume $ columns present

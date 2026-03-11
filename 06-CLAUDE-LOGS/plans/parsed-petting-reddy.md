# Plan: dashboard_55_89_v3.py — 6 Changes from v2

**Date:** 2026-03-07
**Status:** Ready for implementation

---

## Context

`dashboard_55_89_v2.py` is a working Streamlit dashboard for the 55/89 EMA cross scalp strategy. Six bugs and missing features have been identified:
1. Re-roll gives same window on rapid clicks (broken seed entropy)
2. Portfolio capital model inflates total capital (per-coin $10k × N coins instead of $10k shared)
3. Single mode missing Trading Volume and LSG% metrics
4. Portfolio per-coin table missing Rebate $ and Volume $ columns
5. No CPU/GPU toggle (GPU sweep engine already built at `engine/cuda_sweep.py`)
6. No PDF export

Output: `scripts/dashboard_55_89_v3.py` created by `scripts/build_dashboard_55_89_v3.py`.
Do NOT modify v2.

---

## Critical file paths

| File | Role |
|------|------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v2.py` | Source to upgrade |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py` | Output (created by build script) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_55_89_v3.py` | Build script |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py` | GPU engine — `run_gpu_sweep()`, `build_param_grid()`, `CUDA_AVAILABLE` |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v384.py` | CPU engine |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89.py` | Signal module |

---

## Confirmed facts from code reading

- `compute_signals_55_89` outputs: `long_a`, `short_a`, `long_b`, `short_b`, `reentry_long`, `reentry_short`, `cloud3_allows_long`, `cloud3_allows_short` — all zeros except `long_a`/`short_a` and cloud3 (ones). Compatible with GPU kernel.
- `backtester_v384.py` metrics dict already contains: `total_volume`, `total_rebate`, `net_pnl_after_rebate`, `pct_losers_saw_green`
- GPU `run_gpu_sweep(df_signals, param_grid_np, notional_val, comm_rate, maker_rate)` — signal columns match what the signal module produces
- GPU output columns: `sl_mult, tp_mult, be_trigger_atr, cooldown, total_trades, win_rate, net_pnl, expectancy, max_dd_pct, profit_factor, lsg_pct, sharpe`

---

## Change 1 — Re-roll seed fix

**Bug:** `random.randint()` uses stale internal state across Streamlit reruns. Rapid clicks produce identical windows.

**Fix in `roll_random_range()`:**
- Add `random_roll_counter` to `st.session_state` (int, starts 0)
- On Re-roll click: `counter += 1`, `random.seed(counter + int(time.time_ns() % 1_000_000))`, then roll
- After Re-roll: delete `result_single` and `result_portfolio` from session_state (clears stale results)
- Same seed approach applied to Random N coin sampler in portfolio mode

---

## Change 2 — Portfolio capital model

**Bug:** Each coin runs with `initial_equity` independently, implies N × equity total capital.

**Fix:**
- Add sidebar radio in portfolio mode: `"Portfolio Capital"` = `["Shared pool", "Per-coin independent"]`
- **Shared pool (default):** `per_coin_equity = total_capital / max(n_coins, 1)`, pass that as `initial_equity` to each coin's `bt_params`
- **Per-coin independent:** current behaviour, each coin gets full `initial_equity`
- Label swap: Shared shows "Total portfolio capital ($)", Per-coin shows "Initial equity per coin ($)"
- Caption under toggle:
  - Shared: `"Each coin gets $X.XX (total $Y / N coins)"`
  - Per-coin: `"Each coin runs with full $X — total implied capital: $Y"`
- `align_portfolio_equity_55_89` receives `baseline = total_capital` in shared mode, `baseline = initial_equity * n_coins` in per-coin mode
- Portfolio Net PnL = `portfolio_eq[-1] - baseline`
- Portfolio equity curve starts at `baseline` (sum of per-coin starting equities)

---

## Change 3 — Single mode missing metrics

**Fix in `render_single_results()`:**

Current Row 3 (3 cols): `Rebate | Net w/Rebate | BE Raises`

Replace with Row 3 (5 cols): `Trading Volume $ | Rebate $ | Net w/Rebate | BE Raises | LSG%`

- `total_volume = m.get("total_volume", 0.0)` — formatted as `"$" + "{:,.0f}".format(total_volume)`
- `lsg_pct = m.get("pct_losers_saw_green", 0.0)` — formatted as `"{:.1%}".format(lsg_pct)`

---

## Change 4 — Portfolio per-coin table

**Fix in `render_portfolio_results()`:**

Add to the `rows` dict per coin:
```python
"Rebate $": round(m.get("total_rebate", 0.0), 2),
"Volume $": round(m.get("total_volume", 0.0), 0),
```

---

## Change 5 — CPU/GPU toggle

**Sidebar (Single mode only, above action buttons):**

```
st.sidebar.subheader("Engine")
engine_opts = ["CPU", "GPU"] if CUDA_AVAILABLE else ["CPU"]
engine_choice = st.sidebar.radio("Engine", engine_opts, horizontal=True)
if not CUDA_AVAILABLE:
    st.sidebar.caption("GPU unavailable — install numba with CUDA support")
```

**GPU mode sidebar extras (appear only when GPU selected):**
- `sl_min` slider: 0.5 → 4.0, step 0.5 (default range for grid)
- `sl_max` slider: 0.5 → 5.0, step 0.5
- `be_min` slider: 0.0 → 2.0, step 0.5
- `be_max` slider: 0.0 → 3.0, step 0.5
- Caption showing grid size: `f"Grid: {n_sl} × {n_be} = {n_sl*n_be} combos"`

**GPU run flow (replaces equity curve + trades table):**
1. Compute signals once (CPU): `df_sig = compute_signals_55_89(df.copy(), sig_params)`
2. Build param grid: `build_param_grid(sl_range=np.arange(sl_min, sl_max+0.1, 0.5), tp_range=[], be_vals=np.arange(be_min, be_max+0.1, 0.5), cooldown_vals=[1], include_no_tp=True)`
   - Note: `tp_range=[]` with `include_no_tp=True` means tp_mult=999.0 (no TP) only
3. `df_sweep = run_gpu_sweep(df_sig, param_grid, notional_val=notional, comm_rate=COMMISSION_RATE, maker_rate=0.0002)`
4. Filter to `tp_mult == 999.0` rows only (strategy uses no TP)

**GPU output (render_gpu_results function):**
- Pivot on `sl_mult` (x), `be_trigger_atr` (y)
- Heatmap 1: color = `net_pnl`, title "Net PnL Heatmap"
- Heatmap 2: color = `sharpe`, title "Sharpe Heatmap"
- Top-3 table: `sl_mult, be_trigger_atr, total_trades, win_rate, net_pnl, sharpe, max_dd_pct` (top 3 by net_pnl)
- Use `go.Heatmap` with `colorscale="RdYlGn"`, dark theme

**GPU mode is Single mode only.** Portfolio mode stays CPU only. No GPU radio shown in portfolio mode.

---

## Change 6 — PDF export

**Import guard:**
```python
try:
    import reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import plotly.io as pio
    KALEIDO_AVAILABLE = True
except Exception:
    KALEIDO_AVAILABLE = False
```

**Function: `generate_pdf_single(symbol, results, bt_params, date_range, fig_equity) -> bytes`**
- Uses `io.BytesIO` as PDF buffer
- Page 1: run metadata table (symbol, date range, params, timestamp)
- Page 2: all metrics as two-column table (metric name | value)
- Page 3: equity curve PNG (if kaleido available, `pio.to_image(fig_equity, format="png", width=1000, height=400)`)
- Returns bytes

**Function: `generate_pdf_portfolio(coin_results, pf_data, bt_params, date_range, fig_pf) -> bytes`**
- Same metadata + per-coin table + portfolio equity curve PNG

**Placement in UI:**
- After results render in single mode (CPU only, not GPU)
- After results render in portfolio mode
- If `not REPORTLAB_AVAILABLE`: `st.warning("reportlab not installed — pip install reportlab")`
- If kaleido not available: include text-only PDF with note "Chart images require kaleido"

**Button:**
```python
date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
st.download_button("Export PDF", data=pdf_bytes,
                   file_name="55_89_backtest_" + sym + "_" + date_str + ".pdf",
                   mime="application/pdf")
```

---

## Build script structure (`build_dashboard_55_89_v3.py`)

```
1. Check scripts/dashboard_55_89_v3.py does not exist (abort if it does)
2. Write full dashboard_55_89_v3.py source as triple-quoted string
3. py_compile.compile(path, doraise=True)
4. ast.parse(open(path).read())
5. Print BUILD SUCCESS + run command
```

Rules:
- Every `def` has a one-line docstring
- No f-strings with escaped quotes inside triple-quoted build content
- Use string concatenation for any join expressions in embedded code
- No backslash paths — use Path() or forward slashes

---

## Implementation order

1. Load Python skill (`/python`) — mandatory per HARD RULES
2. Write `build_dashboard_55_89_v3.py` — complete v3 source embedded, all 6 changes
3. py_compile + ast.parse validation inside build script
4. Output run command for user

---

## Verification (user runs)

1. `python scripts/build_dashboard_55_89_v3.py` → expect BUILD SUCCESS
2. `streamlit run scripts/dashboard_55_89_v3.py` from `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester`
3. Single CPU: BTCUSDT 30d → Volume $ and LSG% appear in Row 3 (5 cols)
4. Single GPU: BTCUSDT 30d → two heatmaps + top-3 table render
5. Re-roll: click twice rapidly → different windows each time, stale results cleared
6. Export PDF: triggers download, PDF has metadata + metrics + chart
7. Portfolio Shared pool: 5 coins $10k total → equity curve starts at $10k not $50k
8. Portfolio per-coin table: Rebate $ and Volume $ columns present

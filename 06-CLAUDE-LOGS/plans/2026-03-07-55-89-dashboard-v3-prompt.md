# Next Chat Prompt — 55/89 Dashboard v3

## Paste this as your first message:

---

Read these files before doing anything else:
1. `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md`
2. `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\MEMORY.md`
3. `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-55-89-scalp.md`

Then read the current dashboard source in full:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v2.py`

Then read the CUDA sweep engine:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py`

---

## Context

We are building `dashboard_55_89_v3.py` — an upgrade to `dashboard_55_89_v2.py`.
Do NOT modify v2. Build v3 via a new build script `build_dashboard_55_89_v3.py`.

The signal module is `signals/ema_cross_55_89.py` (already patched and working).
The CPU engine is `engine/backtester_v384.py`.
The GPU engine is `engine/cuda_sweep.py` — already fully built with `run_gpu_sweep()`.

---

## Changes required for v3

### 1. Fix: Re-roll gives same result

**Bug:** `roll_random_range()` picks a new random window but the result stored in
`st.session_state["random_range"]` is not invalidated between "Re-roll" clicks because
Streamlit reruns the whole script and the session_state read happens before the button.

**Root cause:** Two problems compound each other:
1. `random.randint()` is called with `random.seed()` never set, so Python reuses the same
   internal state across Streamlit reruns — on fast reruns the OS clock hasn't advanced
   enough to change the seed, producing identical results.
2. The `session_state["random_range"]` guard (`if random_range is None`) means once a range
   is stored, Re-roll only stores a new value AFTER `st.rerun()`, but the new value is
   computed with the same seed.

**Fix:**
- Store a `random_range_seed` integer counter in session_state (starts at 0).
- On Re-roll button click: increment counter, call `random.seed(counter + int(time.time_ns() % 1_000_000))`, then roll.
- This guarantees entropy even on rapid clicks.
- After Re-roll, also delete `result_single` and `result_portfolio` from session_state so
  stale results don't show under the new date window.
- In portfolio mode, Random N coin selection has the same problem — apply the same seed
  approach to the coin sampler.

### 2. Fix: Portfolio capital model — 10k per coin instead of 10k total

**Bug:** In portfolio mode, every coin is initialized with `initial_equity=10000` independently.
With 10 coins that implies $100k total capital. The portfolio equity baseline is computed as
`initial_equity * n_coins` which means "Net PnL" is correct in dollar terms but the equity
curve starts at $100k, not $10k. This is misleading — the user set $10k and expects $10k.

**Fix:**
- Add a "Portfolio capital mode" toggle in the sidebar (portfolio mode only):
  - **Shared pool** (default): User sets one total capital amount (e.g. $10,000).
    Each coin's `initial_equity` = `total_capital / n_coins`. Coins run sequentially,
    each getting an equal slice. Portfolio equity curve starts at `total_capital`.
  - **Per-coin independent**: Current behaviour. Each coin gets the full `initial_equity`.
    Use this when testing strategy quality per-coin without caring about total capital.

- When Shared pool is selected: replace "Initial equity ($)" with "Total portfolio capital ($)"
  label. Compute `per_coin_equity = total_capital / max(n_coins, 1)` and pass that as
  `initial_equity` to each coin's `bt_params`.

- Portfolio equity baseline for Net PnL: `total_capital` (not `initial_equity * n_coins`).
  Portfolio curve starts at `total_capital` in shared mode.

- Show caption under the toggle:
  - Shared: "Each coin gets $X (total $Y / N coins)"
  - Per-coin: "Each coin runs with full $X — total implied capital: $Y"

### 4. Add: Trading Volume and Rebate fields to metrics

**Currently missing from results display:**
- Trading Volume (`total_volume` from `metrics` dict — already computed by engine as `self.comm.total_volume`)
- Total Rebate (already shown as metric but missing from portfolio per-coin table)

**Add to single mode Row 3:**
Replace current 3-col layout (Rebate, Net w/Rebate, BE Raises) with 5-col:
`Trading Volume $ | Rebate $ | Net w/Rebate | BE Raises | LSG%`

LSG% = `pct_losers_saw_green` from metrics dict (already computed by engine).

**Add to portfolio per-coin table:**
Add columns: `Rebate $` and `Volume $` to the per-coin summary DataFrame.

### 5. Add: CPU vs GPU choice

**Sidebar control (under "Engine" subheader, above action buttons):**
```
Engine: [CPU] [GPU]  (radio, horizontal)
```

- CPU: uses `Backtester384` as now (single param set, single coin at a time)
- GPU: uses `run_gpu_sweep()` from `engine/cuda_sweep.py`

**GPU mode behaviour:**
- GPU mode is a PARAMETER SWEEP, not a single backtest
- Runs a grid of `sl_mult × be_trigger_atr` combinations simultaneously
- Signal params (slope N/M) stay fixed — signals are computed once on CPU, then the
  signal arrays are passed to the GPU kernel
- Grid defaults: `sl_mult` from 0.5 to 4.0 step 0.5, `be_trigger` from 0.0 to 2.0 step 0.5
  (user-configurable via two sliders that appear only when GPU mode is selected)
- TP is always disabled (sentinel 999.0 in CUDA kernel)
- Cooldown fixed at 1 bar

**GPU mode output (replaces equity curve + trades table):**
- Heatmap: X=sl_mult, Y=be_trigger_atr, color=net_pnl (Plotly heatmap, dark theme)
- Second heatmap: color=sharpe
- Best combo highlighted: show top 3 rows from sweep results as a small table
  (sl_mult, be_trigger, trades, WR%, net_pnl, sharpe, max_dd%)
- GPU mode is Single coin only — Portfolio mode stays CPU only
- If GPU not available (CUDA_AVAILABLE=False): show warning and fall back to CPU

**GPU mode detection at startup:**
```python
from engine.cuda_sweep import CUDA_AVAILABLE, run_gpu_sweep, build_param_grid
```
If `CUDA_AVAILABLE` is False: disable the GPU radio option and show caption
"GPU unavailable — install numba with CUDA support".

### 6. Add: PDF export button

After results are rendered (single or portfolio), show a "Export PDF" button.

**PDF content:**
- Page 1: run metadata (symbol, date range, params, timestamp)
- Page 2: metrics table (all metrics as a table, not cards)
- Page 3: equity curve as image (use `fig.to_image(format="png")` via kaleido)
- Page 4 (portfolio only): per-coin summary table + portfolio equity curve image

**Implementation:**
Use `reportlab` for PDF generation (already installed in the environment per MEMORY.md —
epub/pdf tools installed). Do NOT use weasyprint or playwright.

Helper function `generate_pdf_55_89(mode, cached, bt_params, date_range) -> bytes`
Returns PDF as bytes. Streamlit download button:
```python
st.download_button("Export PDF", data=pdf_bytes,
                   file_name="55_89_backtest_" + symbol + "_" + date_str + ".pdf",
                   mime="application/pdf")
```

Charts are rendered to PNG via `plotly.io.to_image(fig, format="png", width=1000, height=400)`
and embedded in the PDF as images. Requires `kaleido` package:
```
pip install kaleido
```
Check if kaleido is available; if not, skip chart images and show text-only PDF with a note.

---

## Build rules (mandatory — non-negotiable)

- Load Python skill (`/python`) before writing any code
- Check file existence before writing — never overwrite
- Output file: `scripts/dashboard_55_89_v3.py` (created by build script)
- Build script: `scripts/build_dashboard_55_89_v3.py`
- Build script must: write file, `py_compile.compile(doraise=True)`, `ast.parse()`, report PASS/FAIL
- Every `def` must have a one-line docstring
- NO f-strings with escaped quotes inside triple-quoted build content — use string concatenation
- NO backslash paths in docstrings or strings — use `Path()` or forward slashes
- NO bash execution of Python scripts — give user the run command, wait for output
- Full Windows paths everywhere in output text

---

## Reference files

| File | Purpose |
|------|---------|
| `scripts/dashboard_55_89_v2.py` | Source to upgrade from — read this fully before building |
| `engine/cuda_sweep.py` | GPU engine — `run_gpu_sweep(df_signals, param_grid_np)` interface |
| `engine/backtester_v384.py` | CPU engine — `Backtester384(bt_params).run(df_sig)` |
| `signals/ema_cross_55_89.py` | Signal module — `compute_signals_55_89(df, params)` |
| `engine/commission.py` | Commission model — `total_volume`, `total_rebate` fields |

---

## Verification steps (after build)

1. `python scripts/build_dashboard_55_89_v3.py` → expect BUILD SUCCESS
2. `streamlit run scripts/dashboard_55_89_v3.py` from backtester root
3. Single CPU: run on BTCUSDT 30d → verify Volume $ and LSG% appear in Row 3
4. Single GPU: run on BTCUSDT 30d → verify heatmap renders, best combo table shows
5. Re-roll: click Re-roll twice rapidly → verify different date windows each time, old results clear
6. Export PDF: click button → verify download triggers, PDF has metrics + chart
7. Portfolio Shared pool: run 5 coins with $10k total → verify equity curve starts at $10k not $50k
8. Portfolio per-coin: verify Rebate $ and Volume $ columns in per-coin table

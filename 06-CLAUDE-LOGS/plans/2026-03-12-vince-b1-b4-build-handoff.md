# Vince B1→B4 Autonomous Build Handoff
**Generated:** 2026-03-12
**Destination:** Claude Code (VS Code), `PROJECTS\four-pillars-backtester\` working directory
**Scope:** B1 (FourPillarsPlugin), B3 (Enricher), MARKOV (Indicator State Transition Engine), B4 (PnL Reversal panel)
**Data source:** `trades_all.csv` — 193 live bot trades, 20-column v2 schema

---

## INSTRUCTIONS FOR CLAUDE CODE

You are building the Vince Research Engine. This is a scoped autonomous build. Follow this document exactly. Do not deviate. Do not add features not listed. Scope before building.

**Before writing any code, you must:**
1. Read the three build spec docs listed in Section 2
2. Read `strategies/base_v2.py` — the ABC you are implementing
3. Read `vince/api.py` — the stubs you are filling in
4. Read `vince/types.py` — the dataclasses you are using
5. Ask ALL permissions questions listed in Section 3 at once, in a single message. Wait for approval.
6. Then execute the build in the phase order listed in Section 4.

---

## Section 1 — Context

### Why Vince Exists
The live BingX bot has R:R=0.28. 85-92% of losing trades were profitable at some point (LSG baseline). Vince answers: when should those winners have been held? What exit timing and TP setting captures more of the available MFE? Vince is a research engine — it reads trade CSVs and runs analysis. It is NOT a classifier, NOT a live signal component.

### Architecture Decision (locked 2026-03-12)
Vince is **fully strategy-agnostic**. It analyses any trade CSV from any strategy that implements the `StrategyPlugin` ABC. Four Pillars is the first example plugin — not a dependency. Future strategies (V4, 55/89, WEEX) plug in without changing Vince core.

### What Already Exists
| File | Status |
|------|--------|
| `strategies/base_v2.py` | EXISTS — StrategyPlugin ABC (do not modify) |
| `vince/types.py` | EXISTS — all dataclasses (do not modify) |
| `vince/api.py` | EXISTS — function stubs (fill in B3/B4 implementations) |
| `vince/__init__.py` | EXISTS |
| `vince/audit.py` | EXISTS |
| `strategies/four_pillars.py` | EXISTS — v1, wrong base class, must be archived then rewritten |
| `signals/four_pillars_v383_v2.py` | EXISTS — signal compute function |
| `engine/backtester_v385.py` | EXISTS — use this, not v384 |

### Data Source for B1
`PROJECTS\bingx-connector-v2\trades_all.csv`
- 193 trades, 2026-03-03 to 2026-03-11
- 20 columns: timestamp, symbol, direction, grade, entry_price, exit_price, exit_reason, pnl_net, quantity, notional_usd, entry_time, order_id, ttp_activated, ttp_extreme_pct, ttp_trail_pct, ttp_exit_reason, be_raised, saw_green, atr_at_entry, sl_price
- This is a live bot CSV. Schema differs from backtester output. B3 uses backtester output CSVs (from plugin.run_backtest()) — not this file directly. This file is used for Panel 2 smoke testing.

---

## Section 2 — Build Spec Docs (READ BEFORE CODING)

Read these files completely before writing any code. They contain all design decisions, constants, and verification tests.

```
PROJECTS\four-pillars-backtester\BUILD-VINCE-B1-PLUGIN.md
PROJECTS\four-pillars-backtester\BUILD-VINCE-B3-ENRICHER.md
PROJECTS\four-pillars-backtester\BUILD-VINCE-MARKOV.md
PROJECTS\four-pillars-backtester\BUILD-VINCE-B4-PNL-REVERSAL.md
```

Additionally read:
```
PROJECTS\four-pillars-backtester\strategies\base_v2.py
PROJECTS\four-pillars-backtester\vince\api.py
PROJECTS\four-pillars-backtester\vince\types.py
```

---

## Section 3 — ALL PERMISSIONS REQUIRED (ask these at once before writing any code)

Ask the user to confirm ALL of the following in a single message. Do not build until confirmation received.

```
PERMISSIONS REQUEST — VINCE B1→B4 BUILD

Before starting I need confirmation on the following. Please reply YES/NO or with corrections.

[A] FILE ARCHIVE
  Archive strategies/four_pillars.py → strategies/four_pillars_v1_archive.py
  (existing file is v1, wrong base class — it must be preserved, not deleted)
  Confirm: yes / no

[B] FILE CREATES (new files that do not exist)
  Create: strategies/four_pillars.py (v2 rewrite of FourPillarsPlugin)
  Create: vince/cache_config.py (diskcache setup)
  Create: vince/enricher.py (Enricher class)
  Create: vince/markov.py (Markov chain — transition matrix + probability engine)
  Create: vince/pages/__init__.py (empty)
  Create: vince/pages/pnl_reversal.py (Panel 2 data + figure functions)
  Confirm: yes / no

[C] FILE MODIFICATIONS (existing files that will be edited)
  Modify: vince/api.py — replace NotImplementedError stubs with real implementations in run_enricher(), compute_mfe_histogram(), compute_tp_sweep()
  Modify: vince/types.py — add 2 Markov filter fields to ConstellationFilter: min_continuation_prob (Optional[float]), max_reversal_risk (Optional[float])
  NO other files will be modified.
  Confirm: yes / no

[D] DIRECTORY CREATES
  Create: data/vince_cache/ (diskcache FanoutCache storage)
  Create: vince/pages/ (new subpackage)
  Confirm: yes / no

[E] PACKAGE INSTALL (pip)
  Install: diskcache (used by enricher for indicator cache)
  Install: scipy (used by markov for matrix_power)
  Commands:
    pip install diskcache --break-system-packages
    pip install scipy --break-system-packages
  Confirm: yes / no

[F] SCOPE BOUNDARY
  B2 (vince/types.py, vince/api.py stubs) — already built, not rebuilding
  B5 (query_engine.py) — OUT OF SCOPE for this session
  B6 (Dash shell, app.py, layout.py) — OUT OF SCOPE for this session
  Vince Mode 2, Mode 3 (discovery, optimizer) — OUT OF SCOPE
  V4 strategy — OUT OF SCOPE, no dependency required
  Confirm: yes / no

[G] WORKING DIRECTORY
  All paths relative to: PROJECTS\four-pillars-backtester\
  Python environment: .venv312
  Confirm this is correct, or state the correct path.

[H] VERIFICATION TESTS
  After each phase, run the smoke tests listed in each BUILD spec.
  If any test fails, stop and report before continuing to next phase.
  Confirm: yes / no
```

---

## Section 4 — Build Phases (execute in this order)

### Phase 0 — Environment check
Before writing any code, run these checks and report results:

```bash
python --version
python -c "import py_compile; print('py_compile available')"
python -c "from strategies.base_v2 import StrategyPlugin; print('base_v2 import: OK')"
python -c "from vince.types import EnrichedTradeSet; print('vince.types import: OK')"
python -c "from vince.api import run_enricher; print('vince.api import: OK')"
python -c "from signals.four_pillars_v383_v2 import compute_signals_v383; print('signals import: OK')"
python -c "from engine.backtester_v385 import Backtester385; print('backtester_v385 import: OK')"
python -c "import diskcache; print('diskcache available')" 2>/dev/null || echo "diskcache: NOT INSTALLED"
```

If any import fails, report the full traceback before proceeding.

---

### Phase 1 — B1: FourPillarsPlugin

**Spec doc:** `BUILD-VINCE-B1-PLUGIN.md`

**Steps:**
1. Copy `strategies/four_pillars.py` → `strategies/four_pillars_v1_archive.py`
2. Write new `strategies/four_pillars.py` — full v2 implementation per spec

**Core logic (implementation guide, not pseudocode — read the spec for full detail):**

`FourPillarsPlugin` implements `StrategyPlugin` ABC from `strategies/base_v2.py`.

Constructor stores `_signal_params` and `_bt_params` separately. Signal params are fixed per instance (changing them changes what the strategy IS). BT params are swept by the optimizer.

`compute_signals(self, ohlcv_df)` — validates required OHLCV columns and minimum row count (>=61 for stoch_60), then calls `compute_signals_v383(ohlcv_df.copy(), self._signal_params)`. Returns the enriched DataFrame with all indicator columns appended.

`parameter_space()` — returns dict of BT params with bounds: sl_mult (float 0.5-5.0), tp_mult (float 0.5-5.0), be_trigger_atr (float 0.0-3.0), be_lock_atr (float 0.0-1.0), cross_level (int 15-50), allow_b_trades (bool), allow_c_trades (bool).

`trade_schema()` — returns dict with all 6 required keys (entry_bar, exit_bar, pnl, commission, direction, symbol) plus all optional v385 columns listed in the spec. Keys map to description strings.

`run_backtest(self, params, start, end, symbols)` — validates dates (start < end), merges params with `_bt_params`, loops over symbols, loads parquet from `data/cache/{symbol}_5m.parquet`, filters by date range, calls `compute_signals()`, instantiates `Backtester385(bt_cfg)`, calls `.run(df)`, adds `symbol` column, concatenates all results, writes to `results/vince_{timestamp}.csv`, returns Path. Thread-safe (fresh Backtester instance per call).

`strategy_document` property — returns `Path(_ROOT / "docs" / "FOUR-PILLARS-STRATEGY-UML.md")`. Raises `FileNotFoundError` if missing.

Constants: `DEFAULT_SIGNAL_PARAMS`, `DEFAULT_BT_PARAMS` as defined in the spec. `_ROOT`, `CACHE_DIR`, `RESULTS_DIR` from `Path(__file__).resolve().parent.parent`.

**Verification (run after writing, stop if any fail):**
```bash
python -c "import py_compile; py_compile.compile('strategies/four_pillars.py', doraise=True); print('SYNTAX OK')"
python -c "
from strategies.four_pillars import FourPillarsPlugin
fp = FourPillarsPlugin()
ps = fp.parameter_space()
assert isinstance(ps, dict) and 'sl_mult' in ps
ts = fp.trade_schema()
for col in ['entry_bar', 'exit_bar', 'pnl', 'commission', 'direction', 'symbol']:
    assert col in ts, f'missing: {col}'
doc = fp.strategy_document
assert doc.exists(), f'missing: {doc}'
print('INTERFACE: PASS')
"
python -c "
import pandas as pd, numpy as np
from strategies.four_pillars import FourPillarsPlugin
fp = FourPillarsPlugin()
n = 300
dummy = pd.DataFrame({'open': np.random.rand(n)*100+50, 'high': np.random.rand(n)*5+103,
    'low': np.random.rand(n)*5+45, 'close': np.random.rand(n)*100+50, 'volume': np.random.rand(n)*1e6})
out = fp.compute_signals(dummy)
for col in ['long_a', 'short_a', 'stoch_9', 'stoch_60', 'atr', 'cloud3_bull']:
    assert col in out.columns, f'missing: {col}'
assert len(out) == n
print('COMPUTE_SIGNALS: PASS')
"
```

---

### Phase 2 — install diskcache + vince/cache_config.py

**Steps:**
1. Run: `pip install diskcache --break-system-packages`
2. Verify: `python -c "import diskcache; print('diskcache:', diskcache.__version__)"`
3. Create `vince/cache_config.py`:

**Core logic:**

```
VINCE_CACHE_DIR = _ROOT / "data" / "vince_cache"
VINCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
FANOUT_SHARDS = 8
FANOUT_SIZE_LIMIT = 2 * 1024 ** 3   # 2 GB cap

def get_cache() -> diskcache.FanoutCache:
    return diskcache.FanoutCache(str(VINCE_CACHE_DIR), shards=FANOUT_SHARDS, size_limit=FANOUT_SIZE_LIMIT)
```

Cache key format: `"{symbol}_{timeframe}_{params_hash}_{mtime}"` where mtime comes from `os.path.getmtime(parquet_path)`. This auto-invalidates when the parquet file changes.

**Verification:**
```bash
python -c "import py_compile; py_compile.compile('vince/cache_config.py', doraise=True); print('OK')"
python -c "from vince.cache_config import get_cache; c = get_cache(); print('cache init: OK'); c.close()"
```

---

### Phase 3 — B3: Enricher (base pass — no Markov yet)

**Spec doc:** `BUILD-VINCE-B3-ENRICHER.md`

**IMPORTANT — B3 blocker override (2026-03-12 decision):**
The spec says B3 is blocked on `signals/four_pillars_v386.py`. That blocker is lifted. Use `signals/four_pillars_v383_v2.py` via the FourPillarsPlugin already built in Phase 1. The enricher calls `plugin.compute_signals(ohlcv_df)` — it never imports signal files directly.

**Steps:**
1. Create `vince/pages/__init__.py` (empty file, one line: `# Vince pages subpackage`)
2. Create `vince/enricher.py`

**Core logic:**

`Enricher` class. Used as a context manager (`with Enricher(plugin) as e:`). Holds one `FanoutCache` instance, closes on exit.

`enrich(self, trade_csv: Path, symbols: list, start: str, end: str) -> EnrichedTradeSet`

For each symbol:
- Load parquet from `data/cache/{symbol}_5m.parquet`
- Build cache key: `f"{symbol}_5m_{params_hash}_{mtime}"`
- Cache hit: load pre-computed indicator DataFrame
- Cache miss: call `plugin.compute_signals(ohlcv_df)`, store in cache
- Filter cached DataFrame to date range (same filter logic as run_backtest)
- For each trade row belonging to this symbol:
  - `entry_bar` → `iloc[entry_bar]` → snapshot columns `{col}_at_entry`
  - `mfe_bar` → `iloc[mfe_bar]` → snapshot columns `{col}_at_mfe` (use `life_mfe_bar` column from v385 output)
  - `exit_bar` → `iloc[exit_bar]` → snapshot columns `{col}_at_exit`
  - OHLC at each: `entry_open`, `entry_high`, `entry_low`, `entry_close`, `mfe_open`, ... (12 float columns)

Snapshot column naming: `k1_9_at_entry`, `k2_14_at_entry`, `k3_40_at_entry`, `k4_60_at_entry`, `cloud3_bull_at_entry`, `atr_at_entry`, and equivalents for `_at_mfe` and `_at_exit`.

Volume is always preserved (no trade is skipped).

Returns `EnrichedTradeSet` with `session_id=uuid4().hex`, `plugin_name="FourPillarsPlugin"`, `enriched_at=utcnow().isoformat()`.

**Bar index note:** `entry_bar`/`exit_bar` in backtester output are 0-based into the date-filtered slice. The enricher must use the SAME filtered slice it used during `compute_signals()` call. Filtering happens BEFORE passing to plugin.

**Verification:**
```bash
python -c "import py_compile; py_compile.compile('vince/enricher.py', doraise=True); print('OK')"
python -c "
from vince.enricher import Enricher
from strategies.four_pillars import FourPillarsPlugin
import pandas as pd, numpy as np, tempfile, pathlib
# synthetic smoke test — no parquet needed
fp = FourPillarsPlugin()
e = Enricher(fp)
print('Enricher instantiation: PASS')
print('Context manager:', hasattr(e, '__enter__') and hasattr(e, '__exit__'))
"
```

---

### Phase 3b — MARKOV: Indicator State Transition Engine

**Spec doc:** `BUILD-VINCE-MARKOV.md` — read this in full before writing a single line.

**Steps:**
1. Verify scipy: `python -c "from scipy.linalg import matrix_power; print('scipy OK')"` — install if missing
2. Create `vince/markov.py` with the 6 functions defined in the spec
3. Modify `vince/enricher.py` — after the base enrichment pass, call `markov.attach_transition_probs()` per trade to add the 9 Markov columns
4. Modify `vince/types.py` — add `min_continuation_prob: Optional[float] = None` and `max_reversal_risk: Optional[float] = None` to `ConstellationFilter`

**Core logic (read BUILD-VINCE-MARKOV.md for full detail):**

`composite_state(stoch_60_val, stoch_40_val)` — discretises each value into 4 buckets (0-25, 25-50, 50-75, 75-100), returns `stoch_60_bucket * 4 + stoch_40_bucket`. Range: 0–15.

`build_transition_matrix(ohlcv_df)` — walks the enriched OHLCV bar by bar, records state-at-t → state-at-t+1, builds a 16×16 count matrix, normalises each row to sum to 1.0. Rows with fewer than 10 observations default to uniform distribution (1/16 each). Returns `np.ndarray` shape (16, 16).

`n_step_matrix(M, n)` — `scipy.linalg.matrix_power(M, n)`. Returns M^n — the N-step transition matrix.

`continuation_prob(M, current_state, direction, n)` — computes M^n for the given n, takes row `current_state`, sums probabilities of all "extension" target states. LONG extension = composite states where `stoch_60_bucket == 3`. SHORT extension = states where `stoch_60_bucket == 0`. Returns float 0–1.

`reversal_risk(M, current_state, direction, n)` — same M^n lookup. LONG reversal = states where `stoch_60_bucket <= 1` (from a starting state where `stoch_60_bucket >= 2`). SHORT reversal = states where `stoch_60_bucket >= 2` (from `stoch_60_bucket <= 1`). If starting state does not qualify (e.g. already in reversal zone), return 1.0.

`attach_transition_probs(trade_row, enriched_ohlcv, matrix_3, matrix_5, matrix_10)` — reads `entry_bar` from `trade_row`, looks up composite state at that bar from `enriched_ohlcv` (using `stoch_60` and `stoch_40` columns), computes all 9 output columns, returns dict.

**9 columns added per trade:**
`state_at_entry`, `state_at_mfe`, `state_at_exit`,
`continuation_prob_3bar`, `continuation_prob_5bar`, `continuation_prob_10bar`,
`reversal_risk_3bar`, `reversal_risk_5bar`, `avg_continuation_prob`

**Coin-specific matrices:** Build one matrix per symbol. Cache under key `f"markov_{symbol}_5m_{mtime}"` using the existing `vince/cache_config.py` FanoutCache.

**Verification (run all — stop if any fail):**
```bash
python -c "import py_compile; py_compile.compile('vince/markov.py', doraise=True); print('SYNTAX OK')"

python -c "
import numpy as np
import pandas as pd
from vince.markov import build_transition_matrix, composite_state, continuation_prob, reversal_risk, n_step_matrix

# 1. State mapping
assert composite_state(10.0, 60.0) == 0*4 + 2
assert composite_state(80.0, 80.0) == 3*4 + 3
print('STATE MAPPING: PASS')

# 2. Transition matrix
np.random.seed(42)
n = 500
dummy = pd.DataFrame({'stoch_60': np.random.rand(n)*100, 'stoch_40': np.random.rand(n)*100})
M = build_transition_matrix(dummy)
assert M.shape == (16, 16)
assert np.allclose(M.sum(axis=1), 1.0, atol=1e-6)
print('TRANSITION MATRIX: PASS')

# 3. N-step matrix
M5 = n_step_matrix(M, 5)
assert np.allclose(M5.sum(axis=1), 1.0, atol=1e-5)
print('N-STEP MATRIX: PASS')

# 4. Probabilities in range
p = continuation_prob(M, 6, 'LONG', 5)
assert 0.0 <= p <= 1.0
r = reversal_risk(M, 10, 'LONG', 5)
assert 0.0 <= r <= 1.0
print('PROBABILITIES: PASS')

print('ALL MARKOV TESTS: PASS')
"
```

---

### Phase 4 — B4: PnL Reversal Panel

**Spec doc:** `BUILD-VINCE-B4-PNL-REVERSAL.md`

**Steps:**
1. Create `vince/pages/pnl_reversal.py`
2. Implement the three functions: `compute_mfe_histogram()`, `compute_tp_sweep()`, `optimal_exit_banner()`

**Note:** B4 now receives Markov columns from the enricher. Two additional outputs are added to this phase.

**Core logic:**

`compute_mfe_histogram(trade_set, f=None, bins=None)` — Filters `trade_set.trades` using `f` if provided. Default bins: 9 ATR breakpoints `[0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, np.inf]`. Uses `life_mfe` column (or `mfe_atr` if enricher renamed it) to bucket trades. Per bin: count, pct, win_rate (pnl>0), avg_net_pnl (pnl minus commission). Returns `pd.DataFrame` — NOT a figure. Caller builds the figure. Do not import Dash or plotly here.

`compute_tp_sweep(trade_set, f=None, tp_range=(0.5, 5.0), steps=19)` — Filters if `f` provided. Generates `np.linspace(tp_range[0], tp_range[1], steps)` TP multiples. For each tp_mult: simulate exit. If `mfe_atr >= tp_mult`: simulated PnL = `direction_sign * tp_mult * atr_at_entry * quantity - commission`. If `mfe_atr < tp_mult`: use actual `pnl_net` or `pnl` column. Direction sign: LONG=+1, SHORT=-1. Sum across all trades. Count trades where simulation differed from actual (would_hit_tp). Constraint: `trade_count >= 0.95 * len(df)` (always met since we never filter out trades in the sweep, only change their PnL). Returns `pd.DataFrame` with columns: `tp_mult`, `gross_pnl`, `net_pnl`, `trade_count`, `pct_would_hit_tp`. Two PnL curves: `gross_pnl` (before commission) and `net_pnl` (after commission). Returns DataFrame, NOT a figure.

`optimal_exit_banner(sweep_df)` — Takes output of `compute_tp_sweep()`. Finds row with max `net_pnl`. Returns `dict`: `{"optimal_tp_mult": float, "optimal_net_pnl": float, "baseline_net_pnl": float, "vs_current_pnl": float}`. Baseline = net_pnl at the lowest tp_mult in the sweep (or pass separately). No filter on trade_count (constraint already handled in sweep).

`rl_overlay_figure(trade_set)` — stub, returns `None`. One line. Comment: "Reserved for RL Exit Policy Optimizer. Separate scoping session required."

`compute_state_heatmap(trade_set, f=None)` — groups trades by `state_at_entry` (0–15). For each state: count, win_rate, avg_net_pnl, avg_continuation_prob_5bar. Returns `pd.DataFrame` — 16 rows, one per composite state. Caller builds the figure in B6. States with fewer than 3 trades are flagged with `sparse=True` column.

`compute_prob_decay_curve(trade_set, f=None)` — for each bar offset (0, 1, 2 ... max_duration), averages `continuation_prob_5bar` at that offset across all matched trades. Returns `pd.DataFrame` with columns: `bar_offset`, `avg_continuation_prob`, `trade_count_at_offset`. Trade count decreases as offset increases (shorter trades drop out). Returns DataFrame, not a figure.

**Column name handling:** The live bot CSV (`trades_all.csv`) uses `pnl_net` not `pnl`. Backtester output uses `pnl`. Handle both: `pnl_col = "pnl_net" if "pnl_net" in df.columns else "pnl"`. Same for `mfe_atr` vs `life_mfe`. Document which column names are expected in a comment block at top of file.

**Verification:**
```bash
python -c "import py_compile; py_compile.compile('vince/pages/pnl_reversal.py', doraise=True); print('OK')"
python -c "
import pandas as pd, numpy as np
from vince.pages.pnl_reversal import compute_mfe_histogram, compute_tp_sweep, optimal_exit_banner, rl_overlay_figure, compute_state_heatmap, compute_prob_decay_curve
from vince.types import EnrichedTradeSet

# Build synthetic EnrichedTradeSet with 20 trades
np.random.seed(42)
n = 20
trades = pd.DataFrame({
    'symbol': ['BTCUSDT'] * n,
    'direction': ['LONG'] * n,
    'pnl_net': np.random.randn(n) * 10,
    'commission': [0.08] * n,
    'life_mfe': np.random.rand(n) * 3,
    'atr_at_entry': [1.5] * n,
    'quantity': [10.0] * n,
    'grade': ['A'] * n,
})
ts = EnrichedTradeSet(
    trades=trades, session_id='test', plugin_name='FourPillarsPlugin',
    symbols=['BTCUSDT'], date_range=('2026-03-01', '2026-03-11'), enriched_at='2026-03-12T00:00:00'
)

hist = compute_mfe_histogram(ts)
assert isinstance(hist, pd.DataFrame), 'histogram not DataFrame'
assert len(hist) == 9, f'expected 9 bins, got {len(hist)}'
print('MFE HISTOGRAM: PASS')

sweep = compute_tp_sweep(ts)
assert isinstance(sweep, pd.DataFrame)
assert len(sweep) == 19, f'expected 19 steps, got {len(sweep)}'
assert 'net_pnl' in sweep.columns and 'gross_pnl' in sweep.columns
print('TP SWEEP: PASS')

banner = optimal_exit_banner(sweep)
assert isinstance(banner['optimal_tp_mult'], float)
assert 0.5 <= banner['optimal_tp_mult'] <= 5.0
print('OPTIMAL BANNER: PASS')

assert rl_overlay_figure(ts) is None
print('RL STUB: PASS')

# Add Markov columns for heatmap + decay tests
ts.trades['state_at_entry'] = np.random.randint(0, 16, n)
ts.trades['continuation_prob_5bar'] = np.random.rand(n)
ts.trades['bar_offset'] = np.random.randint(0, 20, n)

heatmap = compute_state_heatmap(ts)
assert isinstance(heatmap, pd.DataFrame)
assert 'state_at_entry' in heatmap.columns
assert 'win_rate' in heatmap.columns
print('STATE HEATMAP: PASS')

decay = compute_prob_decay_curve(ts)
assert isinstance(decay, pd.DataFrame)
assert 'bar_offset' in decay.columns
assert 'avg_continuation_prob' in decay.columns
print('PROB DECAY CURVE: PASS')

print('ALL B4 TESTS: PASS')
"
```
```

---

### Phase 4b — Update vince/types.py ConstellationFilter

Add two new optional fields to the `ConstellationFilter` dataclass in `vince/types.py`:

```python
min_continuation_prob: Optional[float] = None   # trades where continuation_prob_5bar >= this value
max_reversal_risk: Optional[float] = None        # trades where reversal_risk_5bar <= this value
```

These are the only changes to `vince/types.py`. Do not touch any other dataclass.

**Verification:**
```bash
python -c "import py_compile; py_compile.compile('vince/types.py', doraise=True); print('SYNTAX OK')"
python -c "
from vince.types import ConstellationFilter
f = ConstellationFilter(min_continuation_prob=0.6, max_reversal_risk=0.3)
assert f.min_continuation_prob == 0.6
assert f.max_reversal_risk == 0.3
print('ConstellationFilter Markov fields: PASS')
"
```

---

### Phase 5 — Wire api.py stubs

Fill the three `NotImplementedError` stubs in `vince/api.py` with real calls:

```python
# run_enricher → delegate to Enricher class
def run_enricher(trade_csv, symbols, start, end, plugin):
    from vince.enricher import Enricher
    with Enricher(plugin) as e:
        return e.enrich(trade_csv, symbols, start, end)

# compute_mfe_histogram → delegate to pnl_reversal module
def compute_mfe_histogram(trade_set, f=None, bins=None):
    from vince.pages.pnl_reversal import compute_mfe_histogram as _fn
    return _fn(trade_set, f, bins)

# compute_tp_sweep → delegate to pnl_reversal module
def compute_tp_sweep(trade_set, f=None, tp_range=(0.5, 5.0), steps=19):
    from vince.pages.pnl_reversal import compute_tp_sweep as _fn
    return _fn(trade_set, f, tp_range, steps)
```

Leave all other stubs (`query_constellation`, `run_backtest`, `get_session_record`, `save_session_record`, `run_discovery`) as `NotImplementedError` — they belong to B5.

**Verification:**
```bash
python -c "import py_compile; py_compile.compile('vince/api.py', doraise=True); print('OK')"
python -c "
from vince.api import run_enricher, compute_mfe_histogram, compute_tp_sweep
print('api imports: OK')
import inspect
# confirm stubs are replaced (no longer raise NotImplementedError immediately)
src = inspect.getsource(compute_mfe_histogram)
assert 'pnl_reversal' in src, 'stub not wired'
print('api wiring: PASS')
"
```

---

### Phase 6 — Full smoke test on trades_all.csv

Load the live bot CSV and run Panel 2 analysis against it. This is the first real output.

```python
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

from vince.types import EnrichedTradeSet
from vince.pages.pnl_reversal import compute_mfe_histogram, compute_tp_sweep, optimal_exit_banner

csv_path = Path(r'..\..\bingx-connector-v2\trades_all.csv')
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} trades, columns: {list(df.columns)}")

# Map live bot schema to Vince expected schema
df['life_mfe'] = df['atr_at_entry'].fillna(1.0)  # placeholder — real MFE from enricher in B3 full run
df['quantity'] = df['notional_usd'] / df['entry_price'].replace(0, 1)

ts = EnrichedTradeSet(
    trades=df,
    session_id='smoke_test_live',
    plugin_name='FourPillarsPlugin',
    symbols=df['symbol'].unique().tolist(),
    date_range=('2026-03-03', '2026-03-11'),
    enriched_at='2026-03-12T00:00:00'
)

hist = compute_mfe_histogram(ts)
sweep = compute_tp_sweep(ts)
banner = optimal_exit_banner(sweep)

print(f"\nMFE Histogram ({len(hist)} bins):")
print(hist.to_string())
print(f"\nTP Sweep ({len(sweep)} steps):")
print(sweep.head(5).to_string())
print(f"\nOptimal Exit Banner:")
for k, v in banner.items():
    print(f"  {k}: {v}")
print("\nSMOKE TEST: PASS")
```

If `atr_at_entry` is all NaN in the live CSV, substitute a fixed ATR of 1.0 for the smoke test and document the substitution. Real ATR values come from the enricher (Phase 3) when running against backtester output.

---

## Section 5 — Failure Handling

| Failure | Action |
|---------|--------|
| Phase 0 import fails | Report full traceback. Do not proceed. |
| Any py_compile fails | Fix immediately before next phase. |
| Verification test fails | Stop. Report the exact assertion failure. Ask user for direction. |
| `diskcache` install blocked | Report. Ask user to install manually. |
| Missing parquet in run_backtest | Expected — surface `FileNotFoundError` cleanly. Do not crash silently. |
| `life_mfe_bar` column missing from backtester output | Check if using v385. If v384, report — enricher spec requires v385. |
| `atr_at_entry` all NaN in live CSV | Expected for live bot trades. Use substitution in smoke test only. Document. |

---

## Section 6 — Out of Scope (do not build)

- No Dash `app.py`, `layout.py` — these are B6
- No `query_engine.py` — B5
- No `optimizer.py` — B9
- No `discovery.py` — B8
- No V4 signal file — strategy direction, separate session
- No database writes — PostgreSQL integration is a future scope item
- No `.env` changes
- No requirements.txt changes except documenting `diskcache` addition
- No changes to `strategies/base_v2.py`, `vince/types.py` — these are locked

---

## Section 7 — Deliverable Checklist

After completing all phases, verify every item:

- [ ] `strategies/four_pillars_v1_archive.py` exists
- [ ] `strategies/four_pillars.py` implements all 5 abstract methods, no NotImplementedError
- [ ] `strategies/four_pillars.py` imports from `strategies.base_v2` (NOT `strategies.base`)
- [ ] `vince/cache_config.py` exists, `get_cache()` returns FanoutCache
- [ ] `vince/enricher.py` exists, `Enricher` class is a context manager
- [ ] `vince/pages/__init__.py` exists
- [ ] `vince/markov.py` exists, all 6 functions implemented
- [ ] `vince/types.py` ConstellationFilter has `min_continuation_prob` and `max_reversal_risk` fields
- [ ] `vince/enricher.py` calls `markov.attach_transition_probs()` per trade, adds 9 Markov columns
- [ ] `vince/pages/pnl_reversal.py` exists, all 6 functions implemented (includes heatmap + decay curve)
- [ ] `vince/api.py` — `run_enricher`, `compute_mfe_histogram`, `compute_tp_sweep` wired (not NotImplementedError)
- [ ] `vince/api.py` — all B5 stubs still raise NotImplementedError (unchanged)
- [ ] All py_compile checks pass
- [ ] All verification tests pass (including Markov tests)
- [ ] Phase 6 smoke test on `trades_all.csv` produces real output (histogram + sweep + banner + state heatmap + decay curve)

Report the checklist results item by item before closing the session.

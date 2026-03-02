# Plan: Create Dash Super-Skill for Vince v2 Dashboard

## Context

Vince v2 requires a Plotly Dash application — an 8-panel research dashboard replacing the current
Streamlit dashboard (dashboard_v392.py). No Dash code exists yet. The constellation query builder
(Panel 3) requires pattern-matching callbacks (MATCH/ALL) — the most complex Dash pattern and the
easiest to get wrong in a way that is hard to refactor. We need a comprehensive 2-in-1 skill that
covers both architecture perspective AND deep technical reference so every dashboard session starts
from a solid foundation, not memory guesses.

Dash version confirmed: **4.0.0** (released 2026-02-03, latest)
dash-ag-grid version: **33.3.3**

---

## Deliverables

### 1. New skill file
`C:\Users\User\.claude\skills\dash\SKILL.md`

Must be created (new directory). ~900 lines, two-part structure.

### 2. Vault copy (CLAUDE.md requirement)
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-dash-vince-skill-creation.md`

Identical content to system plan file.

### 3. CLAUDE.md update
Add mandatory Dash skill load rule to
`C:\Users\User\Documents\Obsidian Vault\CLAUDE.md`

Append to the Python skill rule:
```
- **DASH SKILL MANDATORY** — Before writing ANY Plotly Dash code or Vince dashboard work,
  ALWAYS load the Dash skill first. Triggers: any Dash app file, pages/, vince/dashboard,
  Panel builds, constellation builder, dcc.Store, ag-grid.
```

---

## Skill File Structure (Complete Outline)

### YAML frontmatter
```yaml
---
name: dash
description: >
  Use when building any Plotly Dash application, especially Vince v2 8-panel research dashboard.
  Covers: multi-page app (register_page/pages folder), pattern-matching callbacks (MATCH/ALL) for
  constellation builder, dcc.Store hierarchy, background long-running callbacks (enricher/optimizer),
  dash_ag_grid trade browser, ML model serving (PyTorch CUDA), PostgreSQL connection pooling,
  production gunicorn config. Keywords: dash, plotly dash, dcc, html, callback, pattern-matching,
  ag-grid, Store, Interval, background, PostgreSQL, gunicorn, Vince, dashboard, constellation,
  enricher, register_page, MATCH, ALL, ALLSMALLER, prevent_initial_call, no_update.
---
```

---

### PART 1 — ARCHITECTURE & PERSPECTIVE

**Sections:**

#### Why Dash for Vince (not Streamlit)
Table: Streamlit vs Dash on 6 dimensions (scoped updates, pattern-matching callbacks, stateful
multi-user, production WSGI, component reuse, large dataset handling). Key point: Streamlit reruns
the entire script on every widget interaction — kills Vince where constellation queries take 2-3s.

#### Mental Model — The Callback Graph
- Dash is reactive: only Outputs listed in a callback update
- App layout is a static component tree; callbacks wire components together
- No global mutable state — use dcc.Store for inter-callback communication
- Diagram: Enricher button → dcc.Store[enriched] → Panels 2/3/4/5 (fan-out, not chain)

#### App Structure Decision
- Single-file monolith: only for < 3 panels or prototypes
- Multi-page (pages/ folder): Vince MUST use this — 8 panels = separate page files
- Rule: if a panel has > 2 callbacks, it gets its own file in pages/

#### Vince Store Hierarchy
```
dcc.Store('store-enriched-trades', storage_type='session')   # enriched trade collection
dcc.Store('store-active-filters', storage_type='memory')     # constellation filter state
dcc.Store('store-date-range', storage_type='memory')         # date range shared across panels
dcc.Store('store-session-meta', storage_type='session')      # session ID, partition info
dcc.Store('store-optimizer-results', storage_type='memory')  # optuna candidate list
```

---

### PART 2 — DEEP TECHNICAL REFERENCE

**Sections (each with code examples + WRONG/CORRECT/TRAP callouts):**

#### App Setup — Multi-Page
- Directory structure: `app.py`, `pages/panel1_scorecard.py` ... `pages/panel8_history.py`, `assets/`
- `app.py`: init Dash, `use_pages=True`, sidebar nav layout
- `dash.register_page(__name__, path='/scorecard', name='Coin Scorecard')`
- Sidebar pattern: `dcc.Link()` components + `dash.page_registry`
- URL routing: `dcc.Location` + `dash.page_container`
- Code: complete working `app.py` skeleton for Vince

#### Component Quick Reference
Table of 20 key components: component | props | use case | Vince panel

#### Callback Fundamentals
- `@callback` decorator (Dash 4.0 — use `from dash import callback`, not `app.callback`)
- Input / Output / State — exact semantics
- `prevent_initial_call=True` — when and why
- `no_update` — return to skip specific Outputs in multi-output callback
- `PreventUpdate` exception — older pattern, still works
- **TRAP**: default behavior fires ALL callbacks on page load with initial values → constellation
  builder breaks immediately without prevent_initial_call

#### Pattern-Matching Callbacks — Constellation Builder
This is the most critical section. Full working example.

- `id={"type": "filter-card", "index": n}` — dict IDs
- ALL selector — collect all filter values into list
- MATCH selector — pair each filter input to its own output (same index)
- ALLSMALLER — cascade; only for Input/State, not Output; requires MATCH in Output
- Pattern: Add filter button creates new filter card component with dict ID
- Pattern: Remove button deletes its own card (MATCH on remove button + filter card)
- **TRAP**: string IDs and dict IDs cannot be mixed in same callback Input list
- **TRAP**: dots in dict ID values cause parse errors → never use dots in `"index"` values
- **TRAP**: ALLSMALLER only valid when MATCH also present in same callback's Output
- Code: complete Vince constellation filter builder with add/remove

#### dcc.Store — State Management
- `storage_type`: `'memory'` (tab lifetime), `'session'` (browser tab close), `'local'` (persists)
- Vince uses: `'session'` for enriched trades (large, tab-lifetime), `'memory'` for active filters
- **RULE**: dcc.Store data MUST be JSON-serializable — never put a DataFrame in Store
- Correct pattern: `df.to_json(orient='split')` → Store → `pd.read_json(..., orient='split')`
- For large datasets: store aggregated dicts, not raw rows
- **TRAP**: Storing a 50k-row enriched trade collection as JSON bloats the browser session → store
  server-side (PostgreSQL or diskcache), put only the key (session ID) in dcc.Store
- Vince pattern: store `session_id` in dcc.Store, look up enriched trades from diskcache by key

#### Preventing Callback Chains
- Problem: enricher output triggers 5 panel callbacks simultaneously → all fire on page load
- Solution 1: `prevent_initial_call=True` on all downstream panel callbacks
- Solution 2: return `no_update` from panels when store is None/empty
- Solution 3: `dcc.Loading` wraps each panel — shows spinner, masks cascade timing
- Anti-pattern: chaining callbacks (Output A → Input of callback 2 → Output B) — creates
  sequential dependencies and is hard to cancel mid-chain
- Correct pattern: ALL panel callbacks read directly from dcc.Store — parallel fan-out, not chain
- Code: multi-output callback with selective no_update returns

#### Background Callbacks — Enricher + Optimizer
Dash 4.0 native long_callback system.

- `DiskcacheLongCallbackManager` for dev/single-worker
- `CeleryLongCallbackManager` for production multi-worker
- `background=True` + `manager=longcache_manager` on `@callback`
- `running=[(Output('btn', 'disabled'), True, False)]` — UI during run
- `progress=[Output('progress', 'value'), Output('progress', 'max')]`
- `cancel=[Input('cancel-btn', 'n_clicks')]` — cancellable enricher runs
- `set_progress((current, total))` inside the callback
- **TRAP**: Exceptions in background callbacks raise `InvalidCallbackReturnValue` with custom
  error handlers (known Dash 4.0 bug #3628) → always validate input before background work
- **TRAP**: `dcc.Loading` stops spinner before background callback completes (regression #3594)
  → use explicit progress bar instead of dcc.Loading for background callbacks
- Code: complete enricher button with progress bar, cancel, and disable-during-run

#### Plotly Figure Patterns
- Dark theme template: `go.layout.Template` with dark background, Vince color palette
- **MFE Histogram** (Panel 2): `go.Histogram` with ATR bin edges, overlaid TP sweep points
- **TP Sweep Line** (Panel 2): `go.Scatter(mode='lines')` — PnL vs TP multiple curve
- **Constellation Delta Bar** (Panel 3): `go.Bar` with RGBA coloring by delta sign
- **Metric Heatmap** (Panel 1): `go.Heatmap` — coins × months, green/red cells
- **Equity Curve** (existing, reuse): `go.Scatter` with filled area
- Apply template once at module level: `pio.templates.default = 'vince_dark'`
- **TRAP**: `fig.update_layout()` inside callbacks is fine but `pio.templates.default` in callback
  creates a global state mutation — set at module level only
- Code: template definition + each of the 4 figure factory functions

#### dash_ag_grid — Trade Browser (Panel 5)
- Install: `pip install dash-ag-grid` (v33.3.3, AG Grid 33.3.2)
- `import dash_ag_grid as dag`
- `columnDefs`: list of dicts with `field`, `filter`, `sortable`, `width`
- `rowData`: list of dicts (not DataFrame — convert with `df.to_dict('records')`)
- `dashGridOptions`: `{'rowSelection': 'single', 'pagination': True, 'paginationPageSize': 50}`
- Row selection callback: `Input('trade-grid', 'selectedRows')` → detail panel update
- **TRAP**: Dropdown performance regression in Dash 4.0.0 (#3616) — if using Dropdown-heavy UI,
  consider debouncedInput workaround or pin to 3.x until fixed
- Code: complete trade browser with column defs + row selection → detail callback

#### ML Model Serving in Dash
- Load at module level (once at startup), NOT inside callbacks
- PyTorch: `model = torch.load('model.pt'); model.eval()` at module top
- XGBoost: `bst = xgb.Booster(); bst.load_model('model.json')` at module top
- Thread-safety: `torch.no_grad()` context manager in callback + `model.eval()` at load
- CUDA: `device = 'cuda' if torch.cuda.is_available() else 'cpu'; model.to(device)`
- Batch inference: never run per-row in callback loop → vectorize, run as batch, return all
- OOM guard: `torch.cuda.empty_cache()` after inference if memory constrained
- Optuna: run optimizer in background callback thread (CeleryLongCallbackManager for prod)
- **WRONG**: loading model inside `@callback` — reloads on every call, destroys VRAM
- **CORRECT**: module-level load, callback calls `model(input_tensor)` only
- Code: startup loader + CUDA inference wrapper + OOM guard

#### PostgreSQL in Dash
- `psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=10, ...)` at module level
- Context manager pattern: `with pool.getconn() as conn:` → always returns to pool
- `pg_pool = ThreadedConnectionPool(...)` at module top, NOT inside callback
- Error boundary in callback: wrap DB call in try/except, return error component on failure
- Connection string from `.env` via `python-dotenv`
- **TRAP**: opening new connection per callback call exhausts PostgreSQL max_connections fast
- Code: pool setup + safe query helper + error boundary callback pattern

#### Network & Production Stability
- gunicorn: `gunicorn -w 4 -b 0.0.0.0:8050 app:server` (NOT `app.run()` in prod)
- `app.server` exposes the underlying Flask app for gunicorn
- Single-worker caveat: background callbacks with DiskcacheLongCallbackManager require same worker
  → for multi-worker prod, switch to CeleryLongCallbackManager
- Callback timeout: Dash default is 30s. Background callbacks bypass this limit.
- Memory leak prevention: don't accumulate data in module-level lists across callbacks
- Client-side callbacks: for pure UI transforms (no data computation), use `clientside_callback`
  to avoid round-trip to server
- **TRAP**: `debug=True` in production enables hot-reload and exposes traceback to browser
- Code: gunicorn startup command + clientside callback example

#### Performance Optimization
- `@cache.memoize()` (flask-caching) for expensive enricher computations shared across callbacks
- Pre-load all parquet files at startup into a module-level dict keyed by symbol
- Lazy panel rendering: `dcc.Loading` + hide panel `div` until its store has data (use `style`)
- `pd.read_parquet()` with `columns=` filter — only load needed columns
- `orient='split'` is fastest JSON orientation for DataFrames (vs 'records')
- Clientside callback for show/hide toggle: zero server round-trip
- **TRAP**: `df.to_json(orient='records')` for a 100k-row DataFrame = 50MB+ in browser session
  → always pre-aggregate before storing

#### Code Review Checklist
- [ ] All page files call `dash.register_page(__name__, ...)`
- [ ] All callbacks triggered by user input have `prevent_initial_call=True`
- [ ] No DataFrame stored directly in dcc.Store (use `.to_json(orient='split')`)
- [ ] ML models loaded at module level, not inside callbacks
- [ ] PostgreSQL uses ThreadedConnectionPool (not per-callback connection)
- [ ] Background callbacks use `DiskcacheLongCallbackManager` (dev) or Celery (prod)
- [ ] `debug=False` in production
- [ ] `app.server` exposed for gunicorn (not `app.run()`)
- [ ] Dict IDs contain no dots in `index` values
- [ ] All `go.Figure` objects use Vince dark theme template
- [ ] dcc.Loading NOT used as progress indicator for background callbacks (use progress bar)
- [ ] `torch.cuda.empty_cache()` called after batch inference if on GPU

---

## Critical Files

| File | Action |
|------|--------|
| `C:\Users\User\.claude\skills\dash\SKILL.md` | CREATE (new) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-dash-vince-skill-creation.md` | CREATE (vault copy) |
| `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` | EDIT — append Dash skill mandatory rule |

---

## Verification

1. Open `C:\Users\User\.claude\skills\dash\SKILL.md` in editor — confirm ~900 lines
2. Test skill load: start new Claude session, ask "build Vince dashboard" — skill should appear
   in system-reminder skills list
3. Confirm CLAUDE.md has the new Dash skill mandatory rule
4. Check vault plan copy exists at 06-CLAUDE-LOGS/plans/

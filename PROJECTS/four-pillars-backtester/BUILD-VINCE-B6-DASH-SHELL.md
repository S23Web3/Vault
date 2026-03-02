# B6 — Dash App Shell Build Spec

**Build ID:** VINCE-B6
**Status:** BLOCKED (depends on B1 -> B5)
**Date:** 2026-02-28
**MANDATORY:** Load Dash skill (/dash) before writing ANY file in this block.

---

## What B6 Is

The Dash multi-page application entry point. Registers all pages, defines sidebar
navigation, persistent dcc.Store hierarchy, and top context bar.
No analysis logic lives here — pure UI shell.

---

## Skills to Load Before Building

- `/dash` — MANDATORY (loaded FIRST, before /python)
- `/python` — MANDATORY

---

## Files

| # | File | Lines (est.) | Action |
|---|------|-------------|--------|
| 1 | `vince/app.py` | ~60 | Create — Dash() init + server |
| 2 | `vince/layout.py` | ~100 | Create — sidebar + shell layout |
| 3 | `vince/assets/style.css` | ~40 | Create — sidebar width, panel spacing |
| 4 | `vince/pages/coin_scorecard.py` | ~5 | Create — stub only |
| 5 | `vince/pages/constellation.py` | ~5 | Create — stub only |
| 6 | `vince/pages/exit_state.py` | ~5 | Create — stub only |
| 7 | `vince/pages/trade_browser.py` | ~5 | Create — stub only |
| 8 | `vince/pages/optimizer_ui.py` | ~5 | Create — stub only |
| 9 | `vince/pages/validation.py` | ~5 | Create — stub only |
| 10 | `vince/pages/session_history.py` | ~5 | Create — stub only |
| 11 | `tests/test_b6_shell.py` | ~20 | Create — import smoke test |

Note: `vince/pages/pnl_reversal.py` is built in B4 — NOT a stub.

---

## App Structure (vince/app.py)

```python
import dash
app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server  # gunicorn entry: gunicorn "vince.app:server"
app.layout = shell_layout  # from layout.py
```

---

## dcc.Store Hierarchy (in shell layout, storage_type="session")

| Store ID | Purpose |
|----------|---------|
| session-id-store | UUID for this analysis session (enricher cache key) |
| active-plugin-store | Plugin name loaded (default: "four_pillars") |
| filter-state-store | Current ConstellationFilter params as JSON |
| metrics-cache-store | Last computed metric tables (avoid recompute on nav) |
| trade-set-store | Path to loaded trade CSV |

---

## Sidebar (250px fixed, vince/layout.py)

| Label | Route | Panel |
|-------|-------|-------|
| Coin Scorecard | / | 1 |
| PnL Reversal | /pnl-reversal | 2 (built in B4) |
| Constellation Query | /constellation | 3 |
| Exit State | /exit-state | 4 |
| Trade Browser | /trades | 5 |
| Settings Optimizer | /optimizer | 6 |
| Validation | /validation | 7 |
| Session History | /sessions | 8 |

Active page highlighted via dcc.Location + callback adding CSS active class.

---

## Top Context Bar (full width above sidebar+content)

- Left: active plugin name
- Centre: coin set count + date range (from active-plugin-store)
- Right: session ID first 8 chars

---

## Page Stub Template

Each un-built page file:
```python
import dash
from dash import html
dash.register_page(__name__, path="/panel-route", name="Panel Name")
layout = html.Div("Coming soon — Panel N")
```

---

## Run Command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python -m vince.app
# Opens at http://localhost:8050
```

---

## Verification

```bash
python -c "import py_compile; py_compile.compile('vince/app.py', doraise=True); print('OK')"
python -c "import py_compile; py_compile.compile('vince/layout.py', doraise=True); print('OK')"
python tests/test_b6_shell.py
```

Test cases:
1. `from vince.app import app` — no import error
2. `app.layout` is not None
3. All 5 dcc.Store IDs present in layout children
4. `from vince.pages.pnl_reversal import layout` — no import error (B4 pre-built)
5. All 7 stub pages import without error

# Session Log: Dash Super-Skill Creation for Vince v2
**Date:** 2026-02-27
**Duration:** ~1 hour
**Topic:** Plotly Dash skill file creation for Vince v2 8-panel dashboard

---

## Objective

Build a comprehensive "super dash genius skill" — a 2-in-1 skill file covering:
- Part 1: Architecture & perspective (why Dash, mental model, Vince store hierarchy)
- Part 2: Deep technical reference (every pattern needed for the 8-panel build)

Triggered by upcoming Vince v2 Dash build. User identified that pattern-matching callbacks (MATCH/ALL for constellation builder), multi-page app architecture, and dcc.Store patterns are the highest-risk areas to rely on memory alone.

---

## Files Created / Modified

| File | Action | Notes |
|------|--------|-------|
| `C:\Users\User\.claude\skills\dash\SKILL.md` | CREATED | 1,040+ lines, two-part structure |
| `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` | EDITED | Added Dash mandatory rule to Skill Loading Rules section |
| `C:\Users\User\.claude\projects\...\memory\MEMORY.md` | EDITED | Added Dash mandatory rule at line 19 |
| `C:\Users\User\.claude\plans\twinkly-wibbling-puzzle.md` | CREATED | System plan file |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-dash-vince-skill-creation.md` | CREATED | Vault plan copy (identical to system plan) |

---

## Skill File Summary (SKILL.md)

**Version:** Dash 4.0.0 (2026-02-03), dash-ag-grid 33.3.3
**Lines:** ~1,040

### Part 1 — Architecture & Perspective
- Streamlit vs Dash comparison (6 dimensions) — key: Streamlit reruns entire script on every interaction, killing Vince where constellation queries take 2-3s
- Callback graph mental model: reactive, static component tree, dcc.Store for inter-callback state
- App structure decision tree: single-file vs multi-page (Vince MUST use multi-page, 8 panels)
- Vince store hierarchy (5 stores): session-meta, enriched-key, date-range, active-filters, optimizer-results

### Part 2 — Deep Technical Reference
All sections include code examples plus WRONG/CORRECT/TRAP callouts:

1. **App Setup** — multi-page skeleton with `suppress_callback_exceptions=True` (REQUIRED for multi-page), `use_pages=True`, `server = app.server`
2. **Component Quick Reference** — 20 components table
3. **Callback Fundamentals** — `@callback`, Input/Output/State, `prevent_initial_call`, `no_update`, `PreventUpdate`, `from dash import ctx`
4. **Pattern-Matching Callbacks** — full constellation filter builder with MATCH/ALL, add/remove filter cards, dict ID rules
5. **dcc.Store** — storage types, JSON-only rule, diskcache key pattern (store UUID not raw data)
6. **Preventing Callback Chains** — fan-out pattern (correct) vs callback chain (anti-pattern)
7. **Background Callbacks** — DiskcacheLongCallbackManager (dev) vs Celery (prod), progress bar, cancel, `html.Progress` not `dcc.Loading`
8. **Plotly Figure Patterns** — Vince dark theme, MFE histogram, TP sweep line, constellation delta bars, scorecard heatmap
9. **dash_ag_grid** — Trade browser, columnDefs, row selection callback
10. **ML Model Serving** — module-level load, `safe_cuda_inference()` OOM guard for RTX 3060 12GB
11. **PostgreSQL** — `ThreadedConnectionPool`, `get_db()` context manager, error boundary pattern
12. **Production Stability** — gunicorn `-w 1` (required for Diskcache), `debug=False`, client-side callbacks
13. **Performance** — flask-caching, parquet pre-load, `orient='split'`, lazy panel rendering
14. **Code Review Checklist** — 18 items
15. **Known Bugs Table** — 6 Dash 4.0.0 issues: #3628, #3594, #3616, #3596, #3480, #3632

---

## Issues Encountered & Fixes

### 1. Write tool rejected twice for SKILL.md
**Cause:** User was on another screen and accidentally denied the tool call.
**Fix:** Waited for user to return and say "continue", then re-attempted.

### 2. MEMORY.md edit failed — "File has not been read yet"
**Cause:** Attempted Edit without reading first.
**Fix:** Read MEMORY.md before edit. Standard protocol.

### 3. YAML frontmatter `description: >` multi-line block not supported
**Cause:** Claude Code skill validator does not support YAML block scalars. Each indented continuation line was parsed as a separate attribute, producing errors like "Unexpected indentation" and "Attribute X is not supported".
**Fix:** Collapsed the entire description to a single-line quoted string: `description: "..."`.

### 4. `ctx` inconsistency
**Cause:** Two callbacks used different APIs — `from dash import ctx` in one, `dash.callback_context.triggered_id` in another.
**Fix:** Standardized throughout to `from dash import ctx` / `ctx.triggered_id`.

### 5. `vince/panels/` → `vince/pages/` typo
**Cause:** Wrong directory name used in trigger keywords.
**Fix:** Updated in SKILL.md description, CLAUDE.md, and MEMORY.md.

### 6. Gap review — `suppress_callback_exceptions=True` missing
**Cause:** Initial skill draft omitted this critical app-init parameter. Without it, multi-page apps crash at startup when callbacks reference components not in the current page layout.
**Fix:** Added to app.py skeleton as a comment-annotated required parameter.

---

## Dual Guarantee System (Final Architecture)

| Layer | File | Type | Effect |
|-------|------|------|--------|
| Hard rule | `CLAUDE.md` | Project instruction (always loaded) | Forces skill load before any Dash code |
| Hard rule | `MEMORY.md` | Memory (always loaded) | Redundant enforcement across sessions |
| Soft trigger | `SKILL.md` YAML `description:` | Keyword matching | Skill appears in system-reminder when relevant context detected |

The CLAUDE.md and MEMORY.md rules cover the case where keyword matching fails. Keyword matching covers the case where the user asks naturally without triggering the hard rule path.

---

## Verification Status

- [x] SKILL.md exists at `C:\Users\User\.claude\skills\dash\SKILL.md`
- [x] Skill appears in system-reminder with correct description including `vince/pages/` trigger
- [x] CLAUDE.md has "DASH SKILL MANDATORY" rule in Skill Loading Rules section
- [x] MEMORY.md has identical rule at line 19
- [x] Vault plan copy exists at `06-CLAUDE-LOGS\plans\2026-02-27-dash-vince-skill-creation.md`
- [x] `vince/panels/` corrected to `vince/pages/` in all 3 locations
- [x] `suppress_callback_exceptions=True` added to app.py skeleton

"""
Vince v2 — Strategy-agnostic trade research engine.

Entry point: vince/app.py (Dash application, built in B6).
API layer:   vince/api.py (pure Python, callable by pages and future agents).
Types:       vince/types.py (shared dataclasses).
Audit:       vince/audit.py (codebase compliance checker).

Build sequence: B1 (plugin) → B2 (types+API) → B3 (enricher) →
                B4 (PnL reversal) → B5 (query engine) → B6 (Dash shell).
"""

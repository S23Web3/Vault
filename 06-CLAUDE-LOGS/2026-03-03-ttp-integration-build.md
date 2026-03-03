# 2026-03-03 — TTP Integration Build Session

**Session:** Build two scripts from the audited TTP integration plan
**Status:** BUILD SCRIPTS WRITTEN — ready for user to run

## What This Session Did

1. Read all reference files: plan, session log, TTP spec, BUILD-TTP-ENGINE brief
2. Read all 5 source files that need patching (signal_engine.py, position_monitor.py, main.py, config.yaml, dashboard v1-4)
3. Confirmed state_manager.update_position() signature (key, updates dict with lock)
4. Wrote `scripts/build_ttp_integration.py` (6 patches: P1-P6)
5. Wrote `scripts/build_dashboard_v1_4_patch3.py` (5 patches: D1-D5)
6. Fixed unicode escape error in both build script docstrings (Windows paths with `\U`)
7. Fixed test file docstring path (forward slashes to avoid `\U` escape in output)
8. py_compile PASS on both build scripts
9. Updated INDEX.md and TOPIC-bingx-connector.md

## Files Written

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_ttp_integration.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch3.py`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-03-ttp-integration-build.md` (this file)

## Build Script 1: build_ttp_integration.py

6 patches in sequence:

| Patch | Target | What |
|-------|--------|------|
| P1 | ttp_engine.py | CREATE -- TTPExit class + TTPResult dataclass + run_ttp_on_trade, all 4 bugs fixed |
| P2 | signal_engine.py | Add TTPExit import, ttp_config to __init__, restructure on_new_bar (no early return), add _evaluate_ttp_for_symbol |
| P3 | position_monitor.py | Add check_ttp_closes, _cancel_all_orders_for_symbol, _place_market_close, _fetch_single_position, TTP check in _detect_exit |
| P4 | main.py | Pass ttp_config=pos_cfg to StrategyAdapter, add monitor.check_ttp_closes() to monitor_loop |
| P5 | config.yaml | Append ttp_enabled/ttp_act/ttp_dist under position: section |
| P6 | tests/test_ttp_engine.py | CREATE -- 6 unit tests (short clean, short ambiguous, long clean, long ambiguous, activation candle, post-close) |

## Build Script 2: build_dashboard_v1_4_patch3.py

5 patches:

| Patch | What |
|-------|------|
| D1 | Add TTP + Trail Lvl columns to POSITION_COLUMNS (after Dist SL %) |
| D2 | Add TTP state + trail level to build_positions_df row dict |
| D3 | Add TTP section to Strategy Parameters tab (checkbox + 2 number inputs) |
| D4 | Add 3 outputs to CB-11 (load config -> TTP controls) |
| D5 | Add 3 State inputs to CB-12 (save config <- TTP controls) |

## Bug Fixes in ttp_engine.py (from plan)

| # | Fix |
|---|-----|
| BUG 1 | `self.state = "CLOSED"` set when either scenario closes |
| BUG 2 | Activation candle falls through to evaluate full range (no early return) |
| BUG 3 | `CLOSED_PARTIAL` replaced with `"CLOSED"` everywhere; booleans carry detail |
| BUG 4 | `iterrows()` replaced with `enumerate(itertuples(index=False))` |
| BUG 5 | `band_width_pct` only computed when both pess and opt are not None |

## Run Commands (for user)

```bash
cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
python scripts/build_ttp_integration.py
python scripts/build_dashboard_v1_4_patch3.py
python -m pytest tests/test_ttp_engine.py -v
python bingx-live-dashboard-v1-4.py
```

## Unicode Escape Gotcha

Windows paths containing `\U` (e.g. `C:\Users`) trigger Python's unicode escape parser in regular triple-quoted strings. Fix: prefix module docstrings with `r"""` or use forward slashes in path comments inside generated source files.

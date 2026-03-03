# 2026-03-03 — TTP Integration Plan Session

**Session:** Planning + audit for TTP engine integration into BingX connector + dashboard
**Status:** PLAN COMPLETE — ready for build in next session

## What This Session Did

1. Read handoff context from previous session (dashboard v1.4 patch2 applied, errors resolved)
2. Read TTP spec (`research/ttp-lewest.md`), build brief (`BUILD-TTP-ENGINE.md`), draft ttp_engine.py code
3. Confirmed patch2 is applied (bot-toggle-btn present, no duplicates)
4. Confirmed NO TTP logic exists anywhere in the connector yet
5. Clarified with user: TTP = display-only on dashboard + toggle on/off + wired into live bot
6. Wrote initial plan (mark price in monitor approach)
7. Full audit found 5 CRITICAL gaps in the plan
8. Revised to hybrid architecture (TTP evaluates on real OHLC in market loop, closes execute in monitor loop)
9. Verified 5 "pre-existing bugs" in executor.py and state_manager.py — all were agent transcription errors, actual code is correct
10. Wrote final plan to both locations

## Audit Findings (5 Critical Gaps Fixed)

1. Mark price as H=L collapses dual scenario band to zero — FIX: use real 1m OHLC from market_loop
2. Activation price gap bug with mark ticks — FIX: OHLC has actual high/low, no gap
3. Race condition (SL fills while TTP cancels) — FIX: race guard checks exchange position before close
4. No MARKET reduce-only close method — FIX: build `_place_market_close()` in position_monitor.py
5. No cancel-all-orders method — FIX: build `_cancel_all_orders_for_symbol()` in position_monitor.py

## Files Written This Session

- `C:\Users\User\.claude\plans\cuddly-dancing-perlis.md` — system plan file (final, audit-revised)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-dashboard-v1-4-patch3-ttp-display.md` — vault copy of plan (identical)

## For Next Session — Build Checklist

The full plan is at: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-dashboard-v1-4-patch3-ttp-display.md`

The ttp_engine.py source code was pasted into this chat by the user (not saved to a file yet). It needs 4 bug fixes before integration. The next session should:

1. Build `scripts/build_ttp_integration.py` — creates ttp_engine.py (fixed), patches signal_engine.py, position_monitor.py, main.py, config.yaml, writes tests
2. Build `scripts/build_dashboard_v1_4_patch3.py` — patches dashboard (TTP columns + Controls toggle)
3. Run both scripts
4. Run tests: `python -m pytest tests/test_ttp_engine.py -v`
5. Test dashboard: verify TTP columns + toggle render correctly

### Key Architecture Decision

**Hybrid approach:** TTP evaluates in market_loop thread (signal_engine.py, real 1m OHLC), close orders execute in monitor_loop thread (position_monitor.py, has auth). `ttp_close_pending` flag in state.json bridges the two threads.

### Files to Touch (7 total)

| File | Action |
|------|--------|
| `bingx-connector/ttp_engine.py` | CREATE |
| `bingx-connector/signal_engine.py` | MODIFY |
| `bingx-connector/position_monitor.py` | MODIFY |
| `bingx-connector/main.py` | MODIFY |
| `bingx-connector/config.yaml` | MODIFY |
| `bingx-connector/bingx-live-dashboard-v1-4.py` | MODIFY |
| `bingx-connector/tests/test_ttp_engine.py` | CREATE |

### ttp_engine.py Source Code (User-Provided Draft)

The user pasted the full ttp_engine.py source into this chat. It contains:
- `TTPResult` dataclass (result per candle)
- `TTPExit` class (state machine: MONITORING -> ACTIVATED -> CLOSED)
- `run_ttp_on_trade()` batch runner (for backtesting)
- 4 bugs to fix: self.state never CLOSED, CLOSED_PARTIAL state, iterrows(), band_width_pct guard

The next session should read this plan and the source code from here or ask the user to re-paste it.

# 2026-03-05 Native Trailing Stop Build Session

## What happened
1. Continued from prior session where we confirmed BingX accepts `priceRate=0.003` (0.3%) for native `TRAILING_STOP_MARKET`
2. Investigated why custom TTP engine has ~6min delay: 5m candle wait + 45s poll + 30s position check
3. Scoped and planned native trailing switch as config toggle (`ttp_mode: native` vs `engine`)
4. Found critical bug: `_cancel_open_sl_orders` would cancel native trailing during BE raise (`"STOP" in "TRAILING_STOP_MARKET"` is True)
5. Built `scripts/build_native_trailing.py` — creates `bingx-connector-v2/` as full copy with 6 patched files + config

## Files created
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_native_trailing.py` — build script (py_compile PASS)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-05-native-trailing-switch.md` — plan

## What the build produces
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\` — complete bot copy with:
- `executor.py` — native trailing placement (pct-based activation, priceRate from ttp_dist)
- `signal_engine.py` — skips TTP engine in native mode
- `position_monitor.py` — TRAILING_EXIT detection, trailing order protection from cancel, gated TTP methods
- `ws_listener.py` — TRAILING_STOP_MARKET WebSocket fill detection
- `state_manager.py` — TRAILING_EXIT in trades.csv
- `config.yaml` — `ttp_mode: native` added

## Key design decisions
- Config toggle: `ttp_mode: "native"` vs `"engine"` — switchback is trivial
- Reuses existing `ttp_act` (0.008) and `ttp_dist` (0.003) for both modes
- BE raise stays active in native mode (safety net for +0.4% to +0.8%)
- SL tighten + TTP engine skipped in native mode (exchange handles trailing)
- New exit reason: `TRAILING_EXIT` (distinct from SL_HIT and TTP_EXIT)

## Run command
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts/build_native_trailing.py
```

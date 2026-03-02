# Revised Execution Plan — BingX Bot Live Improvements (no Ollama)

**Date**: 2026-02-27
**Source spec**: `C:\Users\User\.claude\plans\fluffy-singing-mango.md`
**Bot root**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector`
**Previous run**: Completed STEP 0 + STEP 1 (executor.py already patched, backup exists)

---

## Ollama Approach — With Streaming

Previous run used `"stream":false` — 16 minutes silent per step. Now using `"stream":true`.
Tokens print to terminal in real-time as Ollama generates. Full output also saved to file.

Streaming curl pattern (use for every Ollama call):
```bash
curl -s http://localhost:11434/api/generate \
  -d "{\"model\":\"qwen2.5-coder:14b\",\"prompt\":\"PROMPT\",\"stream\":true}" \
  | python -c "
import sys, json
out = ''
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    d = json.loads(line)
    chunk = d.get('response', '')
    out += chunk
    print(chunk, end='', flush=True)
print()
open('OUTPUT_FILE', 'w').write(out)
"
```
Then strip fences as before.

---

## Current State (after STEP 1 completed)

- `executor.py` — ALREADY PATCHED (FIX-2 + FIX-3 applied, backup at executor.py.bak)
- `position_monitor.py` — NOT YET patched
- `main.py` — NOT YET patched
- `ws_listener.py` — NOT YET created
- `state_manager.py` — NOT YET patched
- `risk_gate.py` — NOT YET patched
- `scripts/reconcile_pnl.py` — NOT YET created

---

## Execution Sequence (resume from STEP 2)

### Each step follows this pattern — visible at every stage:
1. Read the file (shown in terminal)
2. Apply edit with Edit tool (diff shown immediately)
3. Run py_compile — PASS or FAIL shown instantly
4. Report result — STOP if fail, continue if pass
5. Append to session log with timestamp
6. Move to next step

### STEP 2 — position_monitor.py (FIX-1: commission rate param)
Changes per spec:
- Add `commission_rate=0.0016` param to `__init__`
- Store as `self.commission_rate = commission_rate`
- Replace `commission = notional * 0.0012` with `commission = notional * self.commission_rate`
- Update comment to `# taker fee x 2 sides (from config)`

### STEP 3 — main.py (startup commission fetch + pass rate)
Changes per spec:
- Add `COMMISSION_RATE_PATH = "/openApi/swap/v2/user/commissionRate"` constant
- Add `fetch_commission_rate(auth)` function
- Call it after `set_leverage_and_margin()`
- Pass `commission_rate=commission_rate` to PositionMonitor constructor

### STEP 4 — pytest (verify P0 fixes)
- Run `python -m pytest tests/ -v` from bot root
- Must show 67/67 passing before continuing

### STEP 5 — ws_listener.py (new file, IMP-1)
Write complete file from spec. Class WSListener(threading.Thread):
- listenKey lifecycle (POST/extend/DELETE)
- WebSocket ORDER_TRADE_UPDATE parsing
- fill_queue output
- asyncio event loop in thread
- stream/reconnect logic

### STEP 6 — main.py patch (spawn WS thread)
- Add `from ws_listener import WSListener` + `import queue`
- Add `fill_queue = queue.Queue()` and `ws_thread = WSListener(...)`
- Pass `fill_queue` to PositionMonitor
- Start ws_thread after t1/t2
- Add `ws_thread.stop()` in shutdown

### STEP 7 — position_monitor.py patch (drain fill_queue)
- Add `fill_queue=None` param to `__init__`
- Add queue drain block at top of `check()`
- Add `_handle_close_with_price()` method

### STEP 8 — pytest (verify P1)
- Must show 67/67 passing

### STEP 9 — state_manager.py + risk_gate.py (cooldown + 101209)
- `state_manager.py`: add `last_exit_time` dict, set on close; add `session_blocked` set
- `risk_gate.py`: check `now - last_exit_time[key] < cooldown_bars * bar_duration`
- `executor.py`: detect error 101209, retry with halved qty, add to `session_blocked`

### STEP 10 — scripts/reconcile_pnl.py (new standalone script)
Reads trades.csv, calls BingX positionHistory API, compares netProfit to recorded pnl_net,
logs discrepancies to `logs/YYYY-MM-DD-reconcile.log`.

### STEP 11 — final pytest
- Must show 67/67 passing (plus any new test files)

---

## Rules

- py_compile MUST pass before any file is replaced
- Backup every file before editing: `cp file.py file.py.bak` via Bash
- Every action logged to session log with timestamp
- If any step fails: STOP, report, wait for user
- No escaped quotes in f-strings — string concatenation only
- All functions must have docstrings
- executor.py is already done — skip STEP 1

---

## Session Log

`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-27-bingx-bot-live-improvements.md`
Append every action. Do not overwrite.

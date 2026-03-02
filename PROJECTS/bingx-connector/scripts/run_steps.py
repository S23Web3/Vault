"""
Master script: BingX Bot Runbook Steps 2-11.
Asks for ALL permissions upfront, then runs all steps sequentially.
Ollama streaming visible in terminal. Halts on any failure.
Run: python scripts/run_steps.py
"""
import sys
import re
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import requests

# --- Constants ---
BOT_ROOT = Path(__file__).resolve().parent.parent
MODEL = "qwen2.5-coder:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"
LOG_PATH = Path(
    r"C:\Users\User\Documents\Obsidian Vault"
    r"\06-CLAUDE-LOGS\2026-02-27-bingx-bot-live-improvements.md"
)
RESULTS = []


# --- Helper Functions ---


def stream_ollama(prompt, output_path, model=MODEL):
    """Stream Ollama response token-by-token to terminal and write to file."""
    print("Sending to Ollama (" + model + "), prompt: "
          + str(len(prompt)) + " chars")
    print("--- OLLAMA STREAMING OUTPUT ---\n")
    resp = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": True},
        timeout=(10, 600),
        stream=True,
    )
    resp.raise_for_status()
    chunks = []
    for line in resp.iter_lines():
        if not line:
            continue
        d = json.loads(line)
        token = d.get("response", "")
        chunks.append(token)
        print(token, end="", flush=True)
        if d.get("done"):
            ms = d.get("total_duration", 0) / 1_000_000
            print("\n\n--- DONE ("
                  + str(round(ms / 1000, 1)) + "s) ---")
            break
    text = "".join(chunks)
    if not text.strip():
        raise RuntimeError("Empty response from Ollama")
    m = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1)
        print("Stripped markdown fences")
    else:
        print("No fences found (using raw output)")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Written to " + str(output_path)
          + " (" + str(len(text)) + " chars)")
    return text


def py_compile_check(path):
    """Run py_compile on a file. Returns True if syntax valid."""
    cmd = ("import py_compile; py_compile.compile(r'"
           + str(path) + "', doraise=True)")
    result = subprocess.run(
        [sys.executable, "-c", cmd],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("py_compile: PASS")
        return True
    print("py_compile: FAIL")
    print(result.stderr)
    return False


def show_diff(old_path, new_path, max_lines=80):
    """Show git diff between two files, truncated."""
    result = subprocess.run(
        ["git", "diff", "--no-index", "--",
         str(old_path), str(new_path)],
        capture_output=True, text=True,
        cwd=str(BOT_ROOT),
    )
    lines = result.stdout.split("\n")
    if len(lines) > max_lines:
        out = "\n".join(lines[:max_lines])
        out += "\n... (" + str(len(lines) - max_lines) + " more)"
    else:
        out = result.stdout
    print("--- DIFF ---")
    print(out if out.strip() else "(no differences)")
    print("--- END DIFF ---")


def backup_and_replace(source, new_file, step_num):
    """Backup source with step number, then overwrite with new file."""
    stem = source.stem
    suffix = source.suffix
    tag = ".step" + str(step_num).zfill(2) + ".bak"
    backup = source.parent / (stem + tag + suffix)
    shutil.copy2(source, backup)
    print("Backup: " + str(backup))
    shutil.copy2(new_file, source)
    print("Replaced: " + str(source))


def append_log(msg):
    """Append timestamped message to session log."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n[" + ts + "] " + msg)


def run_pytest():
    """Run pytest on tests/ dir. Returns (pass_count, output)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        capture_output=True, text=True,
        cwd=str(BOT_ROOT),
    )
    output = result.stdout + result.stderr
    print(output[-3000:])
    m = re.search(r"(\d+) passed", output)
    passed = int(m.group(1)) if m else 0
    return passed, output


def read_source(path):
    """Read a source file and print line count."""
    text = path.read_text(encoding="utf-8")
    lc = text.count("\n") + 1
    print("Read " + str(path) + " (" + str(lc) + " lines)")
    return text


def preflight():
    """Check Ollama is running and model is available."""
    print("Preflight: checking Ollama...")
    try:
        tags_url = OLLAMA_URL.replace("/api/generate", "/api/tags")
        resp = requests.get(tags_url, timeout=5)
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        found = [m for m in models if MODEL.split(":")[0] in m]
        if not found:
            print("WARNING: model " + MODEL + " not found.")
            print("Available: " + ", ".join(models))
            print("Proceeding anyway (Ollama may download it)...")
        else:
            print("Ollama OK. Model: " + found[0])
    except Exception as e:
        print("ERROR: Ollama not reachable: " + str(e))
        sys.exit(1)


# --- Step Functions ---


def step_02():
    """STEP 2: position_monitor.py — FIX-1 commission rate."""
    print("\n" + "=" * 60)
    print("STEP 2: position_monitor.py (FIX-1 commission rate)")
    print("=" * 60)
    source = BOT_ROOT / "position_monitor.py"
    output = BOT_ROOT / "position_monitor_new.py"
    src = read_source(source)

    prompt = (
        "You are given position_monitor.py in full below. "
        "Apply ONLY these changes. Output the complete modified "
        "Python file. No explanation, no markdown, no code fences "
        "— ONLY raw Python code.\n\n"
        "CHANGE 1: __init__ must have parameter "
        "commission_rate=0.0016 after config. "
        "Store as self.commission_rate = commission_rate. "
        "Log commission_rate in the startup logger.info line.\n\n"
        "CHANGE 2: In _handle_close, the commission line must be:\n"
        "  commission = notional * self.commission_rate  "
        "# taker fee x 2 sides (from config)\n"
        "Replace any hardcoded rate like 0.0012.\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces. "
        "Use string concatenation.\n"
        "- Change nothing else.\n\n"
        "--- position_monitor.py ---\n" + src
    )

    stream_ollama(prompt, output)
    if not py_compile_check(output):
        raise RuntimeError("STEP 2: py_compile failed")
    show_diff(source, output)
    backup_and_replace(source, output, 2)
    append_log("STEP 2 DONE: position_monitor.py (FIX-1)")
    RESULTS.append((2, "PASS", "position_monitor.py FIX-1"))


def step_03():
    """STEP 3: main.py — commission fetch + ordering fix."""
    print("\n" + "=" * 60)
    print("STEP 3: main.py (commission fetch + ordering fix)")
    print("=" * 60)
    source = BOT_ROOT / "main.py"
    output = BOT_ROOT / "main_new.py"
    src = read_source(source)

    prompt = (
        "You are given main.py in full below. "
        "Apply ONLY these changes. Output the complete modified "
        "Python file. No explanation — ONLY raw Python code.\n\n"
        "CHANGE 1: Ensure constant near top imports:\n"
        "  COMMISSION_RATE_PATH = "
        '"/openApi/swap/v2/user/commissionRate"\n\n'
        "CHANGE 2: Ensure this function exists after "
        "set_leverage_and_margin:\n"
        "  def fetch_commission_rate(auth):\n"
        '      """Fetch taker commission rate from BingX."""\n'
        '      req = auth.build_signed_request('
        '"GET", COMMISSION_RATE_PATH)\n'
        "      try:\n"
        '          resp = requests.get('
        'req["url"], headers=req["headers"], timeout=10)\n'
        "          data = resp.json()\n"
        '          if data.get("code", 0) == 0:\n'
        '              rate = float(data["data"]["commission"]'
        '["takerCommissionRate"])\n'
        '              logger.info("Commission rate: %.6f", rate)\n'
        "              return rate * 2\n"
        '          logger.warning("Commission API error %s", '
        'data.get("code"))\n'
        "      except Exception as e:\n"
        '          logger.warning("Commission fetch failed: %s", e)\n'
        "      return 0.0016\n\n"
        "CHANGE 3 — CRITICAL ordering fix in main():\n"
        "The correct order MUST be:\n"
        "  1. set_leverage_and_margin(...) call\n"
        "  2. commission_rate = fetch_commission_rate(auth)\n"
        "  3. PositionMonitor(..., commission_rate=commission_rate)\n\n"
        "Currently PositionMonitor is constructed BEFORE "
        "commission_rate is assigned — this is a NameError bug. "
        "Fix the ordering so commission_rate is defined first.\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces.\n"
        "- Change nothing else.\n\n"
        "--- main.py ---\n" + src
    )

    stream_ollama(prompt, output)
    if not py_compile_check(output):
        raise RuntimeError("STEP 3: py_compile failed")
    show_diff(source, output)
    backup_and_replace(source, output, 3)
    append_log("STEP 3 DONE: main.py (commission fetch + order fix)")
    RESULTS.append((3, "PASS", "main.py commission fetch"))


def step_04():
    """STEP 4: pytest checkpoint after P0 fixes."""
    print("\n" + "=" * 60)
    print("STEP 4: pytest (P0 verification)")
    print("=" * 60)
    passed, _ = run_pytest()
    if passed < 67:
        raise RuntimeError(
            "STEP 4: " + str(passed) + " passed (need >= 67)")
    append_log("STEP 4 DONE: pytest " + str(passed) + " passed")
    RESULTS.append((4, "PASS", str(passed) + " tests"))


def step_05():
    """STEP 5: Create ws_listener.py — WebSocket fill listener."""
    print("\n" + "=" * 60)
    print("STEP 5: ws_listener.py (new file — WebSocket)")
    print("=" * 60)
    output = BOT_ROOT / "ws_listener_new.py"
    target = BOT_ROOT / "ws_listener.py"

    prompt = (
        "Write a complete Python file ws_listener.py. "
        "Output ONLY raw Python code, no explanation, no fences.\n\n"
        "BingX futures WebSocket order fill listener.\n\n"
        "Class WSListener(threading.Thread) with daemon=True.\n"
        "__init__(self, auth, fill_queue, logger):\n"
        "  auth = BingXAuth instance\n"
        "  fill_queue = queue.Queue()\n"
        "  logger = logging.Logger instance\n\n"
        "Behavior:\n"
        "1. On start: POST /openApi/swap/v1/listenKey (signed via "
        "auth.build_signed_request) to get listenKey from "
        "response data.listenKey\n"
        "2. Connect via websockets library (async) to:\n"
        "   PROD: wss://open-api-swap.bingx.com/swap-market"
        "?listenKey=KEY\n"
        "   VST:  wss://vst-open-api-ws.bingx.com/swap-market"
        "?listenKey=KEY\n"
        "   Pick URL based on auth.demo_mode (True=VST, False=PROD)\n"
        "3. Parse JSON messages. If event e==ORDER_TRADE_UPDATE "
        "and o.X==FILLED:\n"
        "   symbol = o.s, avg_price = float(o.ap)\n"
        "   reason = TP_HIT if TAKE_PROFIT in o.o, "
        "SL_HIT if STOP in o.o, else skip\n"
        "   Put dict(symbol=symbol, avg_price=avg_price, "
        "reason=reason) into fill_queue\n"
        "4. Refresh listenKey every 55 min via POST "
        "/openApi/swap/v1/listenKey/extend (signed)\n"
        "5. On disconnect: reconnect after 5s, max 3 retries, "
        "then log error and stop\n"
        "6. run() creates asyncio event loop in the thread\n"
        "7. stop() sets threading.Event to exit cleanly\n"
        "8. Use requests library for REST calls (listenKey)\n"
        "9. Use websockets library for WebSocket connection\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces. "
        "Use string concatenation.\n"
        "- Imports: threading, asyncio, queue, json, logging, "
        "time, requests, websockets\n"
    )

    stream_ollama(prompt, output)
    if not py_compile_check(output):
        raise RuntimeError("STEP 5: py_compile failed")
    if target.exists():
        backup_and_replace(target, output, 5)
    else:
        shutil.copy2(output, target)
        print("Created: " + str(target))
    append_log("STEP 5 DONE: ws_listener.py created")
    RESULTS.append((5, "PASS", "ws_listener.py created"))


def step_06():
    """STEP 6: main.py — spawn WS thread."""
    print("\n" + "=" * 60)
    print("STEP 6: main.py (WS thread + fill_queue)")
    print("=" * 60)
    source = BOT_ROOT / "main.py"
    output = BOT_ROOT / "main_new.py"
    src = read_source(source)

    prompt = (
        "You are given main.py (already has commission fetch). "
        "Apply ONLY these changes. Output complete Python file. "
        "No explanation — ONLY raw Python code.\n\n"
        "CHANGE 1: Add imports at top:\n"
        "  from ws_listener import WSListener\n"
        "  import queue\n\n"
        "CHANGE 2: In main(), after commission_rate = "
        "fetch_commission_rate(auth), add:\n"
        "  fill_queue = queue.Queue()\n"
        "  ws_thread = WSListener(auth=auth, "
        "fill_queue=fill_queue, logger=logger)\n\n"
        "CHANGE 3: Add fill_queue=fill_queue to "
        "PositionMonitor constructor.\n\n"
        "CHANGE 4: After t1.start() and t2.start(), add:\n"
        "  ws_thread.start()\n"
        "Update the threads-started log message to include "
        "WSListener.\n\n"
        "CHANGE 5: In shutdown after shutdown_event.set(), add:\n"
        "  ws_thread.stop()\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces.\n"
        "- Change nothing else.\n\n"
        "--- main.py ---\n" + src
    )

    stream_ollama(prompt, output)
    if not py_compile_check(output):
        raise RuntimeError("STEP 6: py_compile failed")
    show_diff(source, output)
    backup_and_replace(source, output, 6)
    append_log("STEP 6 DONE: main.py (WS thread)")
    RESULTS.append((6, "PASS", "main.py WS thread"))


def step_07():
    """STEP 7: position_monitor.py — drain fill_queue."""
    print("\n" + "=" * 60)
    print("STEP 7: position_monitor.py (fill_queue drain)")
    print("=" * 60)
    source = BOT_ROOT / "position_monitor.py"
    output = BOT_ROOT / "position_monitor_new.py"
    src = read_source(source)

    prompt = (
        "You are given position_monitor.py (already has "
        "commission_rate). Apply ONLY these changes. "
        "Output complete Python file. "
        "No explanation — ONLY raw Python code.\n\n"
        "CHANGE 1: Add 'import queue' to imports.\n\n"
        "CHANGE 2: In __init__, add parameter fill_queue=None "
        "after commission_rate. Store as:\n"
        "  self.fill_queue = fill_queue if fill_queue "
        "is not None else queue.Queue()\n\n"
        "CHANGE 3: In check(), BEFORE 'live_raw = "
        "self._fetch_positions()', add:\n"
        "  # Drain WebSocket fill events (instant path)\n"
        "  while not self.fill_queue.empty():\n"
        "      try:\n"
        "          event = self.fill_queue.get_nowait()\n"
        "          sym = event.get('symbol', '')\n"
        "          for suffix in ('_LONG', '_SHORT'):\n"
        "              key = sym + suffix\n"
        "              pos = self.state.get_open_positions()"
        ".get(key)\n"
        "              if pos:\n"
        "                  logger.info('WS fill: %s %s %.6f',\n"
        "                      key, event['reason'], "
        "event['avg_price'])\n"
        "                  self._handle_close_with_price(\n"
        "                      key, pos, event['avg_price'],\n"
        "                      event['reason'])\n"
        "      except queue.Empty:\n"
        "          break\n\n"
        "CHANGE 4: Add new method after _handle_close:\n"
        "  def _handle_close_with_price(self, key, pos_data, "
        "exit_price, exit_reason):\n"
        '      """Handle close with known exit price and reason '
        'from WS."""\n'
        "  Same PnL logic as _handle_close:\n"
        "    entry_price = pos_data.get('entry_price', 0)\n"
        "    direction = pos_data.get('direction', 'LONG')\n"
        "    quantity = pos_data.get('quantity', 0)\n"
        "    notional = pos_data.get('notional_usd', 0)\n"
        "    if direction == 'LONG':\n"
        "        pnl_gross = (exit_price - entry_price) * quantity\n"
        "    else:\n"
        "        pnl_gross = (entry_price - exit_price) * quantity\n"
        "    commission = notional * self.commission_rate\n"
        "    pnl_net = pnl_gross - commission\n"
        "  Then: state.close_position, check daily loss, "
        "send notification, log.\n"
        "  Copy the notification and daily-loss logic exactly "
        "from _handle_close.\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces. "
        "Use string concatenation.\n"
        "- Change nothing else.\n\n"
        "--- position_monitor.py ---\n" + src
    )

    stream_ollama(prompt, output)
    if not py_compile_check(output):
        raise RuntimeError("STEP 7: py_compile failed")
    show_diff(source, output)
    backup_and_replace(source, output, 7)
    append_log("STEP 7 DONE: position_monitor.py (fill_queue)")
    RESULTS.append((7, "PASS", "position_monitor.py fill_queue"))


def step_08():
    """STEP 8: pytest checkpoint after P1."""
    print("\n" + "=" * 60)
    print("STEP 8: pytest (P1 verification)")
    print("=" * 60)
    passed, _ = run_pytest()
    if passed < 67:
        raise RuntimeError(
            "STEP 8: " + str(passed) + " passed (need >= 67)")
    append_log("STEP 8 DONE: pytest " + str(passed) + " passed")
    RESULTS.append((8, "PASS", str(passed) + " tests"))


def step_09():
    """STEP 9: cooldown + error 101209 handling."""
    print("\n" + "=" * 60)
    print("STEP 9: cooldown + error 101209")
    print("=" * 60)

    # --- 9a: state_manager.py ---
    print("\n--- 9a: state_manager.py ---")
    sm_src = BOT_ROOT / "state_manager.py"
    sm_out = BOT_ROOT / "state_manager_new.py"
    sm_txt = read_source(sm_src)

    p9a = (
        "You are given state_manager.py below. "
        "Apply ONLY these changes. Output complete Python file. "
        "No explanation — ONLY raw Python code.\n\n"
        "CHANGE 1: In __init__, after self.state = "
        "self._load_state(), add:\n"
        "  self.last_exit_time = {}\n"
        "  self.session_blocked = set()\n\n"
        "CHANGE 2: In close_position(), inside the lock, "
        "after self.state['daily_pnl'] += pnl_net, add:\n"
        "  self.last_exit_time[key] = "
        "datetime.now(timezone.utc)\n\n"
        "CHANGE 3: Add method:\n"
        "  def block_symbol(self, key):\n"
        '      """Add key to session-blocked set."""\n'
        "      self.session_blocked.add(key)\n"
        "      logger.info('Blocked for session: %s', key)\n\n"
        "CHANGE 4: Add method:\n"
        "  def is_blocked(self, key):\n"
        '      """Check if key is session-blocked."""\n'
        "      return key in self.session_blocked\n\n"
        "CHANGE 5: Add method:\n"
        "  def get_last_exit_time(self, key):\n"
        '      """Return last exit datetime for key or None."""\n'
        "      return self.last_exit_time.get(key)\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces.\n"
        "- Change nothing else.\n\n"
        "--- state_manager.py ---\n" + sm_txt
    )

    stream_ollama(p9a, sm_out)
    if not py_compile_check(sm_out):
        raise RuntimeError("STEP 9a: py_compile failed")
    show_diff(sm_src, sm_out)
    backup_and_replace(sm_src, sm_out, 9)
    append_log("STEP 9a DONE: state_manager.py")

    # --- 9b: risk_gate.py ---
    print("\n--- 9b: risk_gate.py ---")
    rg_src = BOT_ROOT / "risk_gate.py"
    rg_out = BOT_ROOT / "risk_gate_new.py"
    rg_txt = read_source(rg_src)

    p9b = (
        "You are given risk_gate.py below. "
        "Apply ONLY these changes. Output complete Python file. "
        "No explanation — ONLY raw Python code.\n\n"
        "CHANGE 1: In __init__, add:\n"
        "  self.cooldown_seconds = config.get("
        "'cooldown_seconds', 900)\n"
        "Add cooldown_seconds to the startup logger.info.\n\n"
        "CHANGE 2: Change evaluate signature to:\n"
        "  def evaluate(self, signal, symbol, state, "
        "allowed_grades, state_manager=None):\n"
        'Update docstring to "Run 8 ordered checks."\n\n'
        "CHANGE 3: After Check 6 (daily trade limit) and "
        "before the APPROVED return, add:\n\n"
        "  # Check 7: Session blocked\n"
        "  if state_manager is not None and "
        "state_manager.is_blocked(key):\n"
        "      reason = 'BLOCKED: Session blocked (' + key + ')'\n"
        "      logger.info('Check 7 FAIL: %s', reason)\n"
        "      return False, reason\n\n"
        "  # Check 8: Cooldown after exit\n"
        "  if state_manager is not None "
        "and self.cooldown_seconds > 0:\n"
        "      last_exit = state_manager.get_last_exit_time(key)\n"
        "      if last_exit is not None:\n"
        "          from datetime import datetime, timezone\n"
        "          elapsed = (datetime.now(timezone.utc) "
        "- last_exit).total_seconds()\n"
        "          if elapsed < self.cooldown_seconds:\n"
        "              remaining = int("
        "self.cooldown_seconds - elapsed)\n"
        "              reason = ('BLOCKED: Cooldown (' "
        "+ str(remaining) + 's remaining)')\n"
        "              logger.info("
        "'Check 8 FAIL: %s', reason)\n"
        "              return False, reason\n\n"
        "Note: variable 'key' is already defined earlier "
        "in Check 3 as key = symbol + '_' + signal.direction.\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces. "
        "Use string concatenation.\n"
        "- Change nothing else.\n\n"
        "--- risk_gate.py ---\n" + rg_txt
    )

    stream_ollama(p9b, rg_out)
    if not py_compile_check(rg_out):
        raise RuntimeError("STEP 9b: py_compile failed")
    show_diff(rg_src, rg_out)
    backup_and_replace(rg_src, rg_out, 9)
    append_log("STEP 9b DONE: risk_gate.py")

    # --- 9c: executor.py ---
    print("\n--- 9c: executor.py (101209 handler) ---")
    ex_src = BOT_ROOT / "executor.py"
    ex_out = BOT_ROOT / "executor_new.py"
    ex_txt = read_source(ex_src)

    p9c = (
        "You are given executor.py below (has FIX-2 + FIX-3). "
        "Apply ONLY these changes. Output complete Python file. "
        "No explanation — ONLY raw Python code.\n\n"
        "CHANGE 1: In execute(), replace the single "
        "self._safe_post() call for the order with inline "
        "requests.post so we can inspect the response code:\n\n"
        "  req = self.auth.build_signed_request("
        "'POST', ORDER_PATH, order_params)\n"
        "  logger.info('Order: %s %s qty=%.6f mark=%.6f "
        "notional=%.2f',\n"
        "      side, symbol, quantity, mark_price, notional)\n"
        "  try:\n"
        "      resp = requests.post(\n"
        "          req['url'], headers=req['headers'], "
        "timeout=10)\n"
        "      resp.raise_for_status()\n"
        "      result = resp.json()\n"
        "  except Exception as e:\n"
        "      logger.error('Order POST failed: %s %s', "
        "symbol, e)\n"
        "      self.notifier.send('<b>ORDER FAILED</b>\\n' "
        "+ side + ' ' + symbol)\n"
        "      return None\n\n"
        "CHANGE 2: After the try/except, add 101209 handling:\n"
        "  if result.get('code', 0) == 101209:\n"
        "      logger.warning('Error 101209 %s — halving qty', "
        "symbol)\n"
        "      halved = self._round_down("
        "quantity / 2, step_size)\n"
        "      if halved <= 0:\n"
        "          logger.error('Halved qty zero %s', symbol)\n"
        "          self.state.block_symbol("
        "symbol + '_' + signal.direction)\n"
        "          self.notifier.send("
        "'<b>BLOCKED</b>\\n' + symbol)\n"
        "          return None\n"
        "      order_params['quantity'] = str(halved)\n"
        "      req = self.auth.build_signed_request("
        "'POST', ORDER_PATH, order_params)\n"
        "      try:\n"
        "          resp = requests.post("
        "req['url'], headers=req['headers'], timeout=10)\n"
        "          resp.raise_for_status()\n"
        "          result = resp.json()\n"
        "      except Exception as e:\n"
        "          logger.error('Retry failed %s: %s', "
        "symbol, e)\n"
        "          self.state.block_symbol("
        "symbol + '_' + signal.direction)\n"
        "          return None\n"
        "      if result.get('code', 0) != 0:\n"
        "          logger.error('Retry API error %s: %s', "
        "symbol, result.get('msg'))\n"
        "          self.state.block_symbol("
        "symbol + '_' + signal.direction)\n"
        "          return None\n"
        "      quantity = halved\n"
        "      logger.info('Retry OK halved=%.6f %s', "
        "halved, symbol)\n\n"
        "  elif result.get('code', 0) != 0:\n"
        "      logger.error('Order API error %s: %s', "
        "result.get('code'), result.get('msg'))\n"
        "      self.notifier.send('<b>ORDER FAILED</b>\\n' "
        "+ side + ' ' + symbol)\n"
        "      return None\n\n"
        "Then continue with the existing success path "
        "(order_data = result.get('data', {}) etc).\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces. "
        "Use string concatenation.\n"
        "- Preserve FIX-2 (fill_price from avgPrice) and "
        "FIX-3 (SL validation). Change nothing else.\n\n"
        "--- executor.py ---\n" + ex_txt
    )

    stream_ollama(p9c, ex_out)
    if not py_compile_check(ex_out):
        raise RuntimeError("STEP 9c: py_compile failed")
    show_diff(ex_src, ex_out)
    backup_and_replace(ex_src, ex_out, 9)
    append_log("STEP 9c DONE: executor.py (101209)")

    RESULTS.append((9, "PASS",
                     "state_manager + risk_gate + executor"))


def step_10():
    """STEP 10: Create scripts/reconcile_pnl.py."""
    print("\n" + "=" * 60)
    print("STEP 10: scripts/reconcile_pnl.py (PnL audit)")
    print("=" * 60)
    output = BOT_ROOT / "scripts" / "reconcile_pnl_new.py"
    target = BOT_ROOT / "scripts" / "reconcile_pnl.py"

    prompt = (
        "Write a complete standalone Python script "
        "reconcile_pnl.py. "
        "Output ONLY raw Python code, no explanation.\n\n"
        "Purpose: Compare bot trades.csv against BingX "
        "position history API.\n\n"
        "Details:\n"
        "- Bot root = parent of scripts/ directory\n"
        "- Add bot root to sys.path to import bingx_auth\n"
        "- Load .env via dotenv for BINGX_API_KEY, "
        "BINGX_SECRET_KEY\n"
        "- Read trades.csv (columns: timestamp, symbol, "
        "direction, grade, entry_price, exit_price, "
        "exit_reason, pnl_net, quantity, notional_usd, "
        "entry_time, order_id)\n"
        "- CLI arg: --hours N (default 24)\n"
        "- For each trade in the time window, call "
        "GET /openApi/swap/v1/trade/positionHistory "
        "with symbol + startTime + endTime (signed)\n"
        "- Compare bot pnl_net vs BingX netProfit\n"
        "- Log discrepancies > $0.01\n"
        "- Output: console summary + "
        "logs/YYYY-MM-DD-reconcile.log\n"
        "- Dual logging: file + console\n"
        "- Use logging.handlers.TimedRotatingFileHandler\n"
        "- argparse for CLI\n"
        "- Run: python scripts/reconcile_pnl.py --hours 24\n\n"
        "RULES:\n"
        "- Every function must have a one-line docstring.\n"
        "- No escaped quotes inside f-string braces. "
        "Use string concatenation.\n"
    )

    stream_ollama(prompt, output)
    if not py_compile_check(output):
        raise RuntimeError("STEP 10: py_compile failed")
    if target.exists():
        backup_and_replace(target, output, 10)
    else:
        shutil.copy2(output, target)
        print("Created: " + str(target))
    append_log("STEP 10 DONE: reconcile_pnl.py created")
    RESULTS.append((10, "PASS", "reconcile_pnl.py created"))


def step_11():
    """STEP 11: Final pytest."""
    print("\n" + "=" * 60)
    print("STEP 11: Final pytest")
    print("=" * 60)
    passed, _ = run_pytest()
    if passed < 67:
        raise RuntimeError(
            "STEP 11: " + str(passed) + " passed (need >= 67)")
    append_log("STEP 11 DONE: final pytest " + str(passed))
    RESULTS.append((11, "PASS", str(passed) + " tests"))


# --- Permission Display + Main ---


def show_permissions():
    """Display full permission summary before running."""
    print("=" * 60)
    print("  BingX Bot Runbook: Steps 2-11")
    print("=" * 60)
    print()
    print("FILES TO MODIFY (backups created automatically):")
    print("  position_monitor.py  "
          "(step 2: commission, step 7: fill_queue)")
    print("  main.py              "
          "(step 3: commission fetch, step 6: WS thread)")
    print("  state_manager.py     "
          "(step 9: cooldown + session_blocked)")
    print("  risk_gate.py         "
          "(step 9: cooldown check)")
    print("  executor.py          "
          "(step 9: error 101209 handler)")
    print()
    print("NEW FILES TO CREATE:")
    print("  ws_listener.py           "
          "(step 5: WebSocket fill listener)")
    print("  scripts/reconcile_pnl.py "
          "(step 10: PnL audit tool)")
    print()
    print("BACKUPS:")
    print("  *.step02.bak.py  *.step03.bak.py  "
          "*.step06.bak.py")
    print("  *.step07.bak.py  *.step09.bak.py")
    print()
    print("OLLAMA: 9 calls  |  MODEL: " + MODEL)
    print("PYTEST: 3 runs   |  THRESHOLD: >= 67 passing")
    print()


def main():
    """Ask permissions once, then run all steps sequentially."""
    show_permissions()
    preflight()
    print()
    confirm = input("Proceed with all steps? (y/n): ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    append_log("=== RUNBOOK STARTED (Steps 2-11) ===")

    steps = [
        step_02, step_03, step_04, step_05, step_06,
        step_07, step_08, step_09, step_10, step_11,
    ]

    for fn in steps:
        try:
            fn()
        except RuntimeError as e:
            print("\n" + "!" * 60)
            print("HALTED: " + str(e))
            print("!" * 60)
            append_log("HALTED: " + str(e))
            break
        except Exception as e:
            print("\n" + "!" * 60)
            print("ERROR: " + str(e))
            print("!" * 60)
            append_log("ERROR: " + str(e))
            break

    print("\n" + "=" * 60)
    print("  RUNBOOK SUMMARY")
    print("=" * 60)
    for num, status, msg in RESULTS:
        print("  Step " + str(num).rjust(2)
              + ": " + status + " -- " + msg)
    total = len(RESULTS)
    if total == 10:
        print("\nAll 10 steps completed.")
    else:
        print("\n" + str(total) + "/10 completed. See error above.")
    append_log("=== RUNBOOK DONE: "
               + str(total) + "/10 steps ===")


if __name__ == "__main__":
    main()

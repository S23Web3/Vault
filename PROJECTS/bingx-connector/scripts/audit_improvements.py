"""
Audit BingX bot improvements via Ollama qwen2.5-coder.
Sends modified files in 2 batches with targeted review prompts.
Starts ollama serve if not running, verifies GPU offload before auditing.
Writes report to logs/YYYY-MM-DD-audit-improvements.log.

Run: cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"; python scripts/audit_improvements.py
"""
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import date

import requests

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

TODAY = date.today().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / (TODAY + "-audit-improvements.log")
REPORT_FILE = ROOT / "audit-report.md"

OLLAMA_URL = "http://localhost:11434"
OLLAMA_GENERATE = OLLAMA_URL + "/api/generate"
OLLAMA_PS = OLLAMA_URL + "/api/ps"
MODEL = "qwen2.5-coder:14b"

# Two batches to stay within 32k context
BATCH_1_FILES = [
    ROOT / "executor.py",
    ROOT / "position_monitor.py",
    ROOT / "main.py",
]
BATCH_1_LABEL = "Core Trade Flow (P0 + P1)"

BATCH_2_FILES = [
    ROOT / "ws_listener.py",
    ROOT / "state_manager.py",
    ROOT / "risk_gate.py",
    ROOT / "signal_engine.py",
    ROOT / "scripts" / "reconcile_pnl.py",
]
BATCH_2_LABEL = "WebSocket + Risk + Reconcile (P1 + P2)"

AUDIT_CHECKLIST = """
Review this code for a BingX perpetual futures trading bot. Check ALL of the following:

1. THREAD SAFETY: 3 daemon threads share state via StateManager (Lock-protected), fill_queue (thread-safe Queue). Any race conditions? Missing locks?

2. COMMISSION MATH: Rate fetched from API at startup (taker * 2 for round-trip). Check:
   - Is commission = notional * self.commission_rate correct everywhere?
   - Are there any remaining hardcoded commission values (0.0012 or similar)?
   - Default fallback is 0.0016 (0.08% * 2) — is this correct?

3. FILL PRICE (FIX-2): After order POST, avgPrice from response used as entry_price. Fallback to mark_price if avgPrice=0. Any edge cases?

4. SL VALIDATION (FIX-3): LONG rejects sl >= mark_price, SHORT rejects sl <= mark_price. Correct direction?

5. WEBSOCKET: listenKey lifecycle (POST/extend/DELETE), ORDER_TRADE_UPDATE parsing, reconnect logic. Any issues with:
   - asyncio event loop in thread?
   - Refresh timing (55min)?
   - Reconnect counter reset?

6. COOLDOWN (IMP-4): 3 bars * 300s = 900s cooldown between re-entries on same symbol+direction. Check:
   - Is last_exit_time recorded correctly?
   - Is the elapsed time comparison correct?
   - Is bar_duration_sec configurable?

7. ERROR 101209 (IMP-3): Retry with halved qty, then session-block. Check:
   - Is halved qty rounded down to step_size?
   - Is the retry using fresh signed params?
   - Does session_blocked persist correctly for the session?

8. MISSING DOCSTRINGS: Every function/method must have a docstring. List any missing.

9. F-STRING SAFETY: Any escaped quotes inside f-string braces? Any backslash paths in strings?

10. LOGIC BUGS: Any off-by-one, wrong comparison direction, missing error handling, or dead code?

For each issue found, output:
  FILE:LINE — SEVERITY (CRITICAL/WARNING/INFO) — Description

If no issues found for a check, say "PASS".
End with a summary: total issues by severity.
"""


def setup_logging():
    """Configure dual logging: file + console."""
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO,
                        handlers=[file_handler, console_handler])
    return logging.getLogger(__name__)


def is_ollama_running():
    """Check if Ollama API is reachable."""
    try:
        resp = requests.get(OLLAMA_URL, timeout=3)
        return resp.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


def start_ollama(log):
    """Start ollama serve in background. Waits up to 30s for API to be ready."""
    log.info("Ollama not running — starting ollama serve...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    for i in range(30):
        time.sleep(1)
        if is_ollama_running():
            log.info("Ollama ready after %ds", i + 1)
            return True
    log.error("Ollama did not start within 30s")
    return False


def ensure_ollama(log):
    """Ensure Ollama is running. Start it if not."""
    if is_ollama_running():
        log.info("Ollama already running at %s", OLLAMA_URL)
        return True
    return start_ollama(log)


def warm_model_and_check_gpu(log):
    """Load model into memory and check GPU offload status."""
    log.info("Loading model %s (this may take a moment)...", MODEL)
    try:
        resp = requests.post(
            OLLAMA_GENERATE,
            json={"model": MODEL, "prompt": "Hi", "stream": False},
            timeout=(10, 120),
        )
        data = resp.json()
        if data.get("done", False):
            log.info("Model loaded successfully")
    except Exception as e:
        log.error("Model warmup failed: %s", e)
        return False
    # Check GPU offload via /api/ps
    try:
        resp = requests.get(OLLAMA_PS, timeout=5)
        data = resp.json()
        models = data.get("models", [])
        for m in models:
            name = m.get("name", "")
            size = m.get("size", 0)
            size_vram = m.get("size_vram", 0)
            if size > 0:
                gpu_pct = (size_vram / size) * 100
            else:
                gpu_pct = 0
            size_gb = size / (1024 ** 3)
            vram_gb = size_vram / (1024 ** 3)
            log.info("MODEL: %s  Size: %.1f GB  VRAM: %.1f GB  GPU: %.0f%%",
                     name, size_gb, vram_gb, gpu_pct)
            if gpu_pct < 100:
                log.warning("Model is NOT fully in GPU — %.0f%% offloaded to CPU. "
                            "Expect slower inference.", 100 - gpu_pct)
            else:
                log.info("Model is 100%% in GPU — full speed")
        if not models:
            log.warning("No models shown in ollama ps — could not verify GPU status")
    except Exception as e:
        log.warning("Could not check GPU status: %s", e)
    return True


def read_files(file_list):
    """Read all files and return combined content with headers."""
    parts = []
    for fpath in file_list:
        if not fpath.exists():
            parts.append("=== " + fpath.name + " === (FILE NOT FOUND)\n")
            continue
        content = fpath.read_text(encoding="utf-8")
        parts.append("=== " + fpath.name + " ===\n" + content + "\n")
    return "\n".join(parts)


def stream_ollama(prompt, log):
    """Send prompt to Ollama with streaming. Returns full response text."""
    log.info("Sending to Ollama (%s), prompt: %d chars...", MODEL, len(prompt))
    try:
        resp = requests.post(
            OLLAMA_GENERATE,
            json={"model": MODEL, "prompt": prompt, "stream": True},
            timeout=(10, 600),
            stream=True,
        )
    except requests.exceptions.ConnectionError:
        log.error("Ollama not running at %s", OLLAMA_URL)
        return None
    chunks = []
    token_count = 0
    for line in resp.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        token = chunk.get("response", "")
        chunks.append(token)
        token_count += 1
        print("\r  Tokens: " + str(token_count) + "   ", end="", flush=True)
        if chunk.get("done", False):
            total_ms = chunk.get("total_duration", 0) / 1_000_000
            print()
            log.info("Done: %d tokens, %.1fs", token_count, total_ms / 1000)
            break
    return "".join(chunks)


def run_batch(label, file_list, log):
    """Run one audit batch. Returns response text."""
    log.info("=== Batch: %s ===", label)
    code_content = read_files(file_list)
    file_names = ", ".join(f.name for f in file_list)
    prompt = (
        "You are auditing a Python trading bot. Files: " + file_names + "\n\n"
        + AUDIT_CHECKLIST + "\n\n"
        + "Here is the code:\n\n" + code_content
    )
    log.info("Files: %s (%d chars total)", file_names, len(code_content))
    result = stream_ollama(prompt, log)
    if result is None:
        log.error("Batch failed: %s", label)
        return "BATCH FAILED: " + label + "\n"
    return result


def main():
    """Run 2-batch audit and write combined report."""
    log = setup_logging()
    log.info("=== BingX Bot Improvements Audit ===")
    log.info("Model: %s", MODEL)
    log.info("Report: %s", str(REPORT_FILE))
    # Step 1: Ensure Ollama is running
    if not ensure_ollama(log):
        log.error("Cannot start Ollama — aborting")
        sys.exit(1)
    # Step 2: Load model and check GPU
    if not warm_model_and_check_gpu(log):
        log.error("Model warmup failed — aborting")
        sys.exit(1)
    # Step 3: Run audit batches
    report_parts = ["# BingX Bot Improvements — Ollama Audit Report\n"]
    report_parts.append("**Date**: " + TODAY + "\n")
    report_parts.append("**Model**: " + MODEL + "\n\n---\n")
    # Batch 1
    result1 = run_batch(BATCH_1_LABEL, BATCH_1_FILES, log)
    report_parts.append("\n## Batch 1: " + BATCH_1_LABEL + "\n\n")
    report_parts.append(result1 + "\n")
    # Batch 2
    result2 = run_batch(BATCH_2_LABEL, BATCH_2_FILES, log)
    report_parts.append("\n## Batch 2: " + BATCH_2_LABEL + "\n\n")
    report_parts.append(result2 + "\n")
    # Write report
    report_text = "\n".join(report_parts)
    REPORT_FILE.write_text(report_text, encoding="utf-8")
    log.info("Report written to %s", str(REPORT_FILE))
    log.info("=== Audit Complete ===")


if __name__ == "__main__":
    main()

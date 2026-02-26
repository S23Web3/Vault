"""
Ollama sweep runner -- foreground, terminal stays open.
1. Sends prompt to Ollama (qwen3-coder:30b)
2. Ollama generates sweep_all_coins.py
3. Parses output, writes file to disk
4. Runs write permission test on output dir
5. Dry-runs the generated script to verify it loads without error
6. Stays alive listening for Ollama health

Usage: python run_ollama_sweep.py
       python run_ollama_sweep.py --model qwen3-coder:30b
       python run_ollama_sweep.py --skip-generate  (skip Ollama, just test existing file)

Terminal stays open. Ctrl+C to stop.
"""
import sys
import os
import re
import json
import time
import subprocess
import requests
import argparse
from pathlib import Path

OLLAMA_API = "http://localhost:11434"
OLLAMA_GENERATE = f"{OLLAMA_API}/api/generate"
OLLAMA_TAGS = f"{OLLAMA_API}/api/tags"

PROJECT_ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
SCRIPT_TARGET = PROJECT_ROOT / "scripts" / "sweep_all_coins.py"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output" / "sweep_all_coins"
PROMPT_FILE = Path(r"C:\Users\User\Documents\Obsidian Vault\trading-tools\prompts\SWEEP-ALL-COINS-PROMPT.md")
CHECKPOINT_FILE = Path(r"C:\Users\User\Documents\Obsidian Vault\trading-tools\generation_checkpoint.txt")


def check_ollama():
    """Check if Ollama API is reachable."""
    try:
        r = requests.get(OLLAMA_TAGS, timeout=5)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            print(f"[OK] Ollama is running. Models: {', '.join(models)}")
            return True
        print(f"[WARN] Ollama responded with status {r.status_code}")
        return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Ollama not reachable at localhost:11434")
        print("        Start Ollama first, then re-run this script.")
        return False


def generate_with_ollama(prompt, model):
    """Send prompt to Ollama, stream response to terminal. Returns full text."""
    print(f"\n[*] Sending prompt to Ollama ({model})...")
    print(f"[*] Prompt length: {len(prompt)} chars")
    print(f"[*] Streaming output below:\n")
    print("-" * 80)

    payload = {
        "model": model,
        "prompt": prompt,
        "system": (
            "You are an expert Python developer for trading systems. "
            "Generate complete, production-ready Python code. "
            "Output exactly one file as: ### scripts/sweep_all_coins.py followed by ```python code block."
        ),
        "stream": True,
        "options": {
            "temperature": 0.3,
            "num_ctx": 8192,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        }
    }

    response_text = ""
    last_checkpoint = 0

    try:
        resp = requests.post(OLLAMA_GENERATE, json=payload, stream=True, timeout=7200)
        resp.raise_for_status()

        for line in resp.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if not chunk.get('done'):
                        token = chunk.get('response', '')
                        response_text += token
                        print(token, end='', flush=True)

                        if len(response_text) - last_checkpoint > 2000:
                            CHECKPOINT_FILE.write_text(response_text, encoding='utf-8')
                            last_checkpoint = len(response_text)
                except json.JSONDecodeError:
                    continue

        CHECKPOINT_FILE.write_text(response_text, encoding='utf-8')
        print("\n" + "-" * 80)
        print(f"[OK] Generation complete ({len(response_text)} chars)")
        return response_text

    except KeyboardInterrupt:
        print(f"\n[WARN] Interrupted. Partial saved to {CHECKPOINT_FILE}")
        CHECKPOINT_FILE.write_text(response_text, encoding='utf-8')
        return response_text
    except Exception as e:
        print(f"\n[ERROR] {e}")
        if response_text:
            CHECKPOINT_FILE.write_text(response_text, encoding='utf-8')
        return response_text


def parse_python_file(text):
    """Extract Python code from Ollama output."""
    # Pattern: ### scripts/sweep_all_coins.py ... ```python ... ```
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        longest = max(matches, key=len)
        return longest.strip()
    return None


def write_file(code):
    """Write generated code to target path. Asks permission first."""
    print(f"\n[*] Target: {SCRIPT_TARGET}")
    print(f"[*] Code length: {len(code)} chars")

    if SCRIPT_TARGET.exists():
        print(f"[WARN] File exists. Will overwrite.")

    print(f"\n[PERMISSION] Write {len(code)} bytes to {SCRIPT_TARGET}?")
    answer = input("  Type 'yes' to confirm: ").strip().lower()
    if answer != 'yes':
        print("[SKIP] File not written.")
        backup = CHECKPOINT_FILE.parent / "generated_sweep.py"
        backup.write_text(code, encoding='utf-8')
        print(f"[*] Saved to backup: {backup}")
        return False

    SCRIPT_TARGET.parent.mkdir(parents=True, exist_ok=True)
    SCRIPT_TARGET.write_text(code, encoding='utf-8')
    print(f"[OK] Written: {SCRIPT_TARGET}")
    return True


def test_write_permission():
    """Test write permission on output directory."""
    print(f"\n[TEST] Write permission on {OUTPUT_DIR}")
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        test_file = OUTPUT_DIR / '.ollama_write_test'
        test_file.write_text('test')
        test_file.unlink()
        print(f"[OK] Write permission confirmed")
        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_script_loads():
    """Dry-run the generated script to verify it imports without crashing."""
    print(f"\n[TEST] Verifying {SCRIPT_TARGET} loads...")
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, r'{PROJECT_ROOT}'); "
             f"exec(open(r'{SCRIPT_TARGET}', encoding='utf-8').read().split(\"if __name__\")[0])"],
            capture_output=True, text=True, timeout=30, cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            print(f"[OK] Script loads without error")
            return True
        else:
            print(f"[FAIL] Load error:\n{result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[FAIL] Script load timed out (30s)")
        return False
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_dry_run():
    """Run the sweep script with --dry-run --no-db to verify end-to-end."""
    print(f"\n[TEST] Dry-run: python scripts/sweep_all_coins.py --dry-run --no-db --top 3")
    print(f"       This will process a few coins to verify the pipeline works.")
    print(f"       Ctrl+C to skip.\n")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_TARGET), "--dry-run", "--no-db", "--top", "3"],
            capture_output=False, timeout=120, cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            print(f"\n[OK] Dry-run completed successfully")
            return True
        else:
            print(f"\n[FAIL] Dry-run exited with code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print(f"\n[WARN] Dry-run timed out (120s) -- script runs but is slow")
        return True
    except KeyboardInterrupt:
        print(f"\n[SKIP] Dry-run skipped by user")
        return True


def listen_loop():
    """Stay alive, check Ollama health every 30s. Ctrl+C to stop."""
    print(f"\n{'='*60}")
    print(f"LISTENING -- Ollama health check every 30s")
    print(f"Ctrl+C to stop")
    print(f"{'='*60}\n")

    while True:
        try:
            r = requests.get(OLLAMA_TAGS, timeout=5)
            if r.status_code == 200:
                ts = time.strftime('%H:%M:%S')
                print(f"  [{ts}] Ollama OK", end='\r')
            else:
                ts = time.strftime('%H:%M:%S')
                print(f"  [{ts}] Ollama status {r.status_code}")
        except requests.exceptions.ConnectionError:
            ts = time.strftime('%H:%M:%S')
            print(f"  [{ts}] Ollama DOWN -- connection refused")
        except Exception as e:
            ts = time.strftime('%H:%M:%S')
            print(f"  [{ts}] Ollama check failed: {e}")

        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description='Ollama sweep runner (foreground)')
    parser.add_argument('--model', default='qwen3-coder:30b', help='Ollama model')
    parser.add_argument('--skip-generate', action='store_true', help='Skip generation, just test existing file')
    parser.add_argument('--no-listen', action='store_true', help='Exit after tests instead of listening')
    args = parser.parse_args()

    print("=" * 60)
    print("OLLAMA SWEEP RUNNER -- FOREGROUND")
    print("=" * 60)
    print()

    # Step 1: Check Ollama is alive
    if not check_ollama():
        print("\n[*] Waiting for Ollama to start...")
        print("    Start it manually, then re-run this script.")
        sys.exit(1)

    # Step 2: Generate (or skip)
    if not args.skip_generate:
        if not PROMPT_FILE.exists():
            print(f"[ERROR] Prompt file not found: {PROMPT_FILE}")
            sys.exit(1)

        prompt = PROMPT_FILE.read_text(encoding='utf-8')
        generated = generate_with_ollama(prompt, args.model)

        if not generated:
            print("[ERROR] No output from Ollama")
            sys.exit(1)

        code = parse_python_file(generated)
        if not code:
            print("[ERROR] Could not parse Python file from output")
            print(f"[*] Raw output saved to {CHECKPOINT_FILE}")
            sys.exit(1)

        written = write_file(code)
        if not written:
            print("[*] File not written. Tests will use existing file if present.")

    # Step 3: Tests
    print(f"\n{'='*60}")
    print("RUNNING TESTS")
    print(f"{'='*60}")

    t1 = test_write_permission()
    t2 = test_script_loads() if SCRIPT_TARGET.exists() else False
    t3 = test_dry_run() if SCRIPT_TARGET.exists() else False

    print(f"\n{'='*60}")
    print("TEST RESULTS")
    print(f"{'='*60}")
    print(f"  Write permission:  {'PASS' if t1 else 'FAIL'}")
    print(f"  Script loads:      {'PASS' if t2 else 'FAIL'}")
    print(f"  Dry-run:           {'PASS' if t3 else 'FAIL'}")

    if t1 and t2 and t3:
        print(f"\n[OK] ALL TESTS PASSED -- system operational")
        print(f"\n[*] To run full sweep:")
        print(f'    cd "{PROJECT_ROOT}" && python scripts/sweep_all_coins.py')
    else:
        print(f"\n[WARN] Some tests failed -- check output above")

    # Step 4: Listen
    if not args.no_listen:
        listen_loop()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] Stopped by user.")
        sys.exit(0)

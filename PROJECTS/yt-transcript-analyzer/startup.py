"""Startup checks — verifies all dependencies before running pipeline."""
import importlib
import json
import logging
import subprocess
import urllib.request
import urllib.error

from config import OLLAMA_BASE_URL, QWEN_MODEL

log = logging.getLogger(__name__)

REQUIRED_PACKAGES = [
    ("webvtt", "webvtt-py"),
    ("requests", "requests"),
    ("dotenv", "python-dotenv"),
]


def check_command(cmd: str) -> bool:
    """Check if a shell command is available on PATH."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def check_python_package(import_name: str) -> bool:
    """Check if a Python package can be imported."""
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def check_ollama() -> bool:
    """Check if Ollama is reachable. Warns if QWEN_MODEL is not listed."""
    try:
        url = OLLAMA_BASE_URL + "/api/tags"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        if not any(QWEN_MODEL in m for m in models):
            log.warning(
                "Ollama running but %s not found. Pull with: ollama pull %s",
                QWEN_MODEL, QWEN_MODEL,
            )
        return True
    except Exception as exc:
        log.error("Ollama not reachable at %s: %s", OLLAMA_BASE_URL, exc)
        return False


def run_checks() -> bool:
    """Run all startup checks. Print missing items with install commands. Return True if all pass."""
    ok = True

    if not check_command("yt-dlp"):
        print("MISSING: yt-dlp")
        print("  Install: pip install yt-dlp")
        ok = False
    else:
        log.info("yt-dlp: OK")

    for import_name, pip_name in REQUIRED_PACKAGES:
        if not check_python_package(import_name):
            print("MISSING: " + pip_name)
            print("  Install: pip install " + pip_name)
            ok = False
        else:
            log.info("%s: OK", pip_name)

    if not check_ollama():
        print("MISSING: Ollama")
        print("  Start Ollama, then: ollama pull " + QWEN_MODEL)
        ok = False
    else:
        log.info("Ollama: OK")

    return ok

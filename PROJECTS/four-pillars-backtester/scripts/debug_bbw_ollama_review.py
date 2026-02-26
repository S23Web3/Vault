
"""Debug script for bbw_ollama_review.
Run: python scripts/debug_bbw_ollama_review.py
"""

import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    """Debug bbw_ollama_review: ping Ollama and run review on real or mock data."""
    from research.bbw_ollama_review import ollama_chat, run_ollama_review, OFFLINE_PREFIX

    log.info("=== Debug: bbw_ollama_review ===")

    # Step 1: Ping Ollama
    log.info("Pinging Ollama (10s timeout)...")
    t0 = time.time()
    ping = ollama_chat("Reply with exactly: ONLINE", model="qwen3:8b", timeout=10)
    dt = time.time() - t0
    if ping.startswith(OFFLINE_PREFIX):
        log.warning("Ollama is OFFLINE: %s", ping)
        ollama_online = False
    else:
        log.info("Ollama ONLINE (%.1fs): %s", dt, ping[:80])
        ollama_online = True

    # Step 2: Run review on real reports if available
    reports_dir = ROOT / "reports" / "bbw"
    out_dir = ROOT / "results" / "debug_ollama"
    log.info("Running review (reports_dir=%s)...", reports_dir)
    t1 = time.time()
    result = run_ollama_review(
        reports_dir=str(reports_dir),
        output_dir=str(out_dir),
        model="qwen3:8b",
        verbose=True,
    )
    elapsed = time.time() - t1
    log.info("Review done: %.1fs", elapsed)
    log.info("Files written: %d", len(result["files_written"]))
    for fpath in result["files_written"]:
        p = Path(fpath)
        if p.exists():
            lines = p.read_text(encoding="utf-8").split("\n")
            log.info("  %s (%d lines): %s", p.name, len(lines), lines[0][:80])
    if result["errors"]:
        log.warning("Errors: " + str(result["errors"]))

    log.info("=== Done ===")


if __name__ == "__main__":
    main()

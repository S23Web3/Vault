
"""Debug script for run_bbw_simulator pipeline.
Run: python scripts/debug_run_bbw_simulator.py
"""

import logging
import subprocess
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
    """Run BBW pipeline smoke test on RIVERUSDT via subprocess."""
    log.info("=== Debug: run_bbw_simulator ===")

    cli_script = ROOT / "scripts" / "run_bbw_simulator.py"
    out_dir = ROOT / "results" / "debug_bbw_pipeline"

    cmd = [
        sys.executable, str(cli_script),
        "--symbol", "RIVERUSDT",
        "--no-ollama",
        "--verbose",
        "--output-dir", str(out_dir),
    ]
    log.info("Command: " + " ".join(cmd))

    t0 = time.time()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    dt = time.time() - t0

    log.info("Exit code: %d  Time: %.1fs", proc.returncode, dt)
    if proc.stdout:
        log.info("STDOUT (last 3000 chars):\n%s", proc.stdout[-3000:])
    if proc.stderr:
        log.info("STDERR (last 1000 chars):\n%s", proc.stderr[-1000:])

    # Validate aggregate CSVs
    agg_dir = out_dir / "aggregate"
    if agg_dir.exists():
        csvs = sorted(agg_dir.glob("*.csv"))
        log.info("aggregate/ CSVs: %d", len(csvs))
        for f in csvs:
            log.info("  %s  %d bytes", f.name, f.stat().st_size)
    else:
        log.warning("aggregate/ dir not found: %s", agg_dir)

    if proc.returncode == 0:
        log.info("RESULT: PASS -- pipeline completed successfully")
    else:
        log.warning("RESULT: WARN -- pipeline exited with code %d", proc.returncode)

    log.info("=== Done ===")


if __name__ == "__main__":
    main()

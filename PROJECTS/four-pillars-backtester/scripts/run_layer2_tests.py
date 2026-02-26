"""
Runner: executes Layer 2 tests + sanity + debug, captures all output to a log file.

Output file: 06-CLAUDE-LOGS/2026-02-14-bbw-layer2-build.md (overwrites previous empty log)

Run: python scripts/run_layer2_tests.py
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT.parent.parent
LOG_FILE = VAULT / "06-CLAUDE-LOGS" / "2026-02-14-bbw-layer2-results.md"

SCRIPTS_TO_RUN = [
    ("Layer 2 Tests", ROOT / "tests" / "test_bbw_sequence.py"),
    ("Layer 2 Sanity Check", ROOT / "scripts" / "sanity_check_bbw_sequence.py"),
    ("Layer 2 Debug Validator", ROOT / "scripts" / "debug_bbw_sequence.py"),
]

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
lines = [f"# Layer 2 Test Results -- {ts}\n"]

for label, script in SCRIPTS_TO_RUN:
    print(f"Running {label}...")
    r = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=120
    )
    lines.append(f"\n## {label}\n```\n{r.stdout}```\n")
    if r.stderr:
        lines.append(f"### STDERR\n```\n{r.stderr}```\n")
    if r.returncode != 0:
        lines.append(f"**Exit code: {r.returncode}**\n")

log_content = "\n".join(lines)
LOG_FILE.write_text(log_content, encoding="utf-8")
print(f"\nResults saved to: {LOG_FILE}")
print("Done.")

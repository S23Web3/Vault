"""Research Orchestrator - Sequential batch execution via Claude Code CLI.

Reads all vault session logs and plan files chronologically.
Each batch runs as a separate claude -p invocation with fresh context.
Writes structured findings per batch, merges into single output file.
Designed for unattended overnight execution - zero interactive prompts.
"""

import subprocess
import sys
import os
import re
import time
import logging
from datetime import datetime


# === CONFIGURATION ===

VAULT = r"C:\Users\User\Documents\Obsidian Vault"
LOGS_DIR = os.path.join(VAULT, "06-CLAUDE-LOGS")
PLANS_DIR = os.path.join(LOGS_DIR, "plans")
FINDINGS_FILE = os.path.join(LOGS_DIR, "RESEARCH-FINDINGS.md")
PROGRESS_FILE = os.path.join(LOGS_DIR, "RESEARCH-PROGRESS.md")
BATCH_DIR = os.path.join(LOGS_DIR, "research-batches")
LOG_DIR = os.path.join(LOGS_DIR, "logs")
TODAY = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, TODAY + "-research-orchestrator.log")

RESEARCH_MODEL = "sonnet"
SYNTHESIS_MODEL = "opus"
MAX_TURNS_NORMAL = 150               # ~6 turns per file (read + analyze + write + progress + verify)
MAX_TURNS_MEGA = 80                  # mega files need fewer turns (1 file, many reads)
MAX_TURNS_SYNTHESIS = 200
BATCH_SIZE = 20                      # smaller batches = lighter load per invocation
MEGA_THRESHOLD = 5000
BATCH_PAUSE_SECONDS = 1500           # 25 min between batches — rate limit safety margin
MAX_RETRIES = 2
BATCH_TIMEOUT_SECONDS = 7200         # 2h hard timeout per batch
RETRY_BACKOFF_SECONDS = 900          # 15 min cooldown before retry
RATE_LIMIT_BACKOFF_SECONDS = 1800    # 30 min extra wait if rate-limit error detected

# Claude CLI full path (npm global bin not in PATH)
CLAUDE_CMD = r"C:\Users\User\AppData\Roaming\npm\claude.cmd"

# Files to exclude from research (metadata/output files)
EXCLUDE_FILES = {
    "INDEX.md",
    "RESEARCH-FINDINGS.md",
    "RESEARCH-PROGRESS.md",
    "RESEARCH-TASK-PROMPT.md",
}

# === ORDERED FILE LIST (from RESEARCH-TASK-PROMPT.md, files 1-162) ===

ORDERED_FILES = [
    # Phase 1 - Origins (1-11)
    "Session-2025-01-21.md",
    "2026-01-24.md",
    "2026-01-25-trading-dashboard.md",
    "2026-01-28-Jacky-VPS-Setup.md",
    "2026-01-28-n8n-webhook-testing.md",
    "2026-01-29-pine-script-review.md",
    "2026-01-29-session-summary.md",
    "2026-01-29-strategy-refinement-session.md",
    "2026-01-30-tradingview-indicator-development.md",
    "2026-01-31-quad-rotation-session.md",
    "2026-01-31-session-summary.md",
    # Phase 2 - February (12-142)
    "2026-02-02.md",
    "2026-02-02-atr-sl-trailing-tp-build-spec.md",
    "2026-02-02-atr-sl-trailing-tp-session.md",
    "2026-02-02-avwap-anchor-assistant-framework.md",
    "2026-02-02-dashboard-framework.md",
    "2026-02-02-ripster-volume-status-build.md",
    "2026-02-03.md",
    "2026-02-03-quad-rotation-stochastic-spec-review.md",
    "2026-02-03-quad-rotation-v4-fast-build-session.md",
    "2026-02-04.md",
    "2026-02-04-four-pillars-strategy-specification.md",
    "2026-02-04-indicator-review-session.md",
    "2026-02-04-quad-rotation-fast-v1.3-build.md",
    "2026-02-05.md",
    "2026-02-05-strategy-analysis-session.md",
    "2026-02-06.md",
    "2026-02-07.md",
    "2026-02-07-backtest-results.md",
    "2026-02-07-progress-review.md",
    "2026-02-08.md",
    "2026-02-09.md",
    "2026-02-09-session-handoff.md",
    "2026-02-10.md",
    "2026-02-10-session1.md",
    "2026-02-10-session2.md",
    "2026-02-11.md",
    "2026-02-11-v38-build-session.md",
    "2026-02-11-v382-avwap-trailing-build.md",
    "2026-02-11-vince-ml-architecture.md",
    "2026-02-11-vince-ml-Session Log.md",
    "2026-02-11-WEEK-2-MILESTONE.md",
    "2026-02-12.md",
    "2026-02-12-project-review-direction.md",
    "2026-02-13.md",
    "2026-02-13-full-project-review.md",
    "2026-02-13-project-audit.md",
    "2026-02-13-data-pipeline-build.md",
    "2026-02-13-vince-ml-build-session.md",
    "2026-02-13-vault-sweep-review.md",
    "2026-02-14-bbw-full-session.md",
    "2026-02-14-bbw-layer1-build.md",
    "2026-02-14-bbw-layer2-build.md",
    "2026-02-14-bbw-layer3-audit-pass3.md",
    "2026-02-14-bbw-layer3-journal.md",
    "2026-02-14-bbw-layer3-results.md",
    "2026-02-14-bbw-layer4-audit-and-sync.md",
    "2026-02-14-bbw-layer4-audit.md",
    "2026-02-14-bbw-layer4-results.md",
    "2026-02-14-bbw-layer5-audit.md",
    "2026-02-14-bbw-layer5-v2-build-session.md",
    "2026-02-14-bbw-layer6-audit.md",
    "2026-02-14-bbw-uml-research.md",
    "2026-02-14-dashboard-v31-build.md",
    "2026-02-14-operational-logic-audit.md",
    "2026-02-14-project-flow-update.md",
    "2026-02-14-vault-sweep-review.md",
    "2026-02-16-bbw-layer4b-plan.md",
    "2026-02-16-bbw-layer4b-results.md",
    "2026-02-16-bbw-v2-fundamental-corrections.md",
    "2026-02-16-bbw-v2-layer4-5-prebuild-analysis.md",
    "2026-02-16-bbw-v2-layer4-build-journal.md",
    "2026-02-16-bbw-v2-layer4b-build-journal.md",
    "2026-02-16-bbw-v2-layer5-logic-analysis.md",
    "2026-02-16-full-project-review.md",
    "2026-02-16-portfolio-bugfix.md",
    "2026-02-16-portfolio-v3-audit.md",
    "2026-02-16-project-status-data-strategy.md",
    "2026-02-16-strategy-actual-implementation.md",
    "2026-02-16-trade-flow-uml.md",
    "2026-02-17-bbw-project-completion-status.md",
    "2026-02-17-dashboard-v391-audit.md",
    "2026-02-17-pdf-diagram-alignment.md",
    "2026-02-17-pdf-export-optimization.md",
    "2026-02-17-pdf-orientation-fix.md",
    "2026-02-17-project-clarity-and-vince-architecture.md",
    "2026-02-17-python-skill-update.md",
    "2026-02-17-uml-diagrams-creation.md",
    "2026-02-17-uml-logic-debugging.md",
    "2026-02-17-vince-ml-strategy-exposure-audit.md",
    "2026-02-18-dashboard-audit.md",
    "2026-02-18-dashboard-v392-build.md",
    "2026-02-18-vince-ml-build.md",
    "2026-02-18-vince-ml-build-plan.md",
    "2026-02-18-vince-scope-session.md",
    "2026-02-19-engine-audit.md",
    "2026-02-19-vince-scope.md",
    "2026-02-20-bingx-architecture-session.md",
    "2026-02-20-bingx-connector-build.md",
    "2026-02-20-vince-scope.md",
    "2026-02-20-youtube-transcript-analyzer-build.md",
    "2026-02-23-dashboard-v393-bug-fix.md",
    "2026-02-23-four-pillars-strategy-scoping.md",
    "2026-02-23-screener-scope.md",
    "2026-02-24-countdown-to-live-session.md",
    "2026-02-24-fault-report-step1-build-review.md",
    "2026-02-24-screener-scope.md",
    "2026-02-24-vince-todo.md",
    "2026-02-24-vince-v2-ml-spec-review.md",
    "2026-02-24-weex-screener-scope.md",
    "2026-02-25-bingx-connector-session.md",
    "2026-02-25-lifecycle-test-session.md",
    "2026-02-25-telegram-connection-session.md",
    "2026-02-25-test-telegram-github-note.md",
    "2026-02-26-bingx-audit-session.md",
    "2026-02-26-vault-vps-migration-session.md",
    "2026-02-26-vps-migration-part-a-violation.md",
    "2026-02-26-yt-analyzer-gui-session.md",
    "2026-02-27-bingx-api-docs-scraper-session.md",
    "2026-02-27-bingx-automation-build.md",
    "2026-02-27-bingx-trade-analysis.md",
    "2026-02-27-bingx-ws-and-breakeven.md",
    "2026-02-27-dash-skill-creation.md",
    "2026-02-27-project-overview-session.md",
    "2026-02-27-vince-concept-doc-update-and-plugin-spec.md",
    "2026-02-27-vince-concept-lock-final.md",
    "2026-02-27-vince-ml-yt-findings.md",
    "2026-02-27-yt-analyzer-v2-build.md",
    "2026-02-28-b2-api-types-research.md",
    "2026-02-28-b3-enricher-research-audit.md",
    "2026-02-28-bingx-be-fix.md",
    "2026-02-28-bingx-dashboard-v1-1-build.md",
    "2026-02-28-bingx-dashboard-v1-2-build.md",
    "2026-02-28-bingx-dashboard-v1-3-patch.md",
    "2026-02-28-bingx-dashboard-vince-planning.md",
    "2026-02-28-bingx-trade-analysis-be-session.md",
    "2026-02-28-bingx-ttp-research.md",
    "2026-02-28-dash-skill-v12-community-audit.md",
    "2026-02-28-dashboard-v393-promote.md",
    "2026-02-28-parquet-data-catchup.md",
    "2026-02-28-vince-b1-scope-audit.md",
    "2026-02-28-vince-b4-scope-audit.md",
    # Phase 3 - March (143-158)
    "2026-03-02-b2-api-types-build.md",
    "2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md",
    "2026-03-03-bingx-dashboard-v1-4-patches.md",
    "2026-03-03-cuda-dashboard-v394-build.md",
    "2026-03-03-cuda-dashboard-v394-planning.md",
    "2026-03-03-daily-bybit-updater.md",
    "2026-03-03-session-handoff.md",
    "2026-03-03-signal-rename-architecture-session.md",
    "2026-03-03-ttp-integration-build.md",
    "2026-03-03-ttp-integration-plan.md",
    "2026-03-04-bingx-v1-5-full-audit-upgrade.md",
    "2026-03-04-position-management-study.md",
    "2026-03-05-bingx-bot-session.md",
    "2026-03-05-bingx-data-fetcher-and-updater.md",
    "2026-03-05-next-chat-prompt-audit.md",
    "2026-03-05-project-review-volume-uml.md",
    # Undated (159-162)
    "BUILD-JOURNAL-2026-02-13.md",
    "build_journal_2026-02-11.md",
    "PENDING-TASKS-MASTER.md",
    "commission-rebate-analysis.md",
]


def setup_logging():
    """Configure dual logging to file and console with timestamps."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("research")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent duplicate output via root logger

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


def discover_files(logger):
    """Scan log directories and categorize all .md files."""
    # Root log files (not in plans/)
    root_files = []
    for f in sorted(os.listdir(LOGS_DIR)):
        full = os.path.join(LOGS_DIR, f)
        if f.endswith(".md") and os.path.isfile(full) and f not in EXCLUDE_FILES:
            root_files.append(f)

    # Plan files
    plan_files = []
    if os.path.isdir(PLANS_DIR):
        for f in sorted(os.listdir(PLANS_DIR)):
            full = os.path.join(PLANS_DIR, f)
            if f.endswith(".md") and os.path.isfile(full):
                plan_files.append(f)

    # Categorize root files: ordered vs unlisted
    ordered_set = set(ORDERED_FILES)
    unlisted = [f for f in root_files if f not in ordered_set]

    # Categorize plans: dated vs auto-generated
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
    dated_plans = [f for f in plan_files if date_pattern.match(f)]
    auto_plans = [f for f in plan_files if not date_pattern.match(f)]

    # Filter ordered list to only files that actually exist
    existing_ordered = []
    missing_ordered = []
    for f in ORDERED_FILES:
        if os.path.isfile(os.path.join(LOGS_DIR, f)):
            existing_ordered.append(f)
        else:
            missing_ordered.append(f)
            logger.warning("Ordered file missing from disk: %s", f)

    logger.info(
        "Discovery: %d ordered (%d missing), %d unlisted, %d dated plans, %d auto plans",
        len(existing_ordered),
        len(missing_ordered),
        len(unlisted),
        len(dated_plans),
        len(auto_plans),
    )

    return {
        "ordered": existing_ordered,
        "unlisted": unlisted,
        "dated_plans": dated_plans,
        "auto_plans": auto_plans,
    }


def get_file_line_count(filepath):
    """Return line count of a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def build_batches(files, logger):
    """Split categorized files into execution batches."""
    batches = []

    def flush_batch(name_prefix, file_list, base_dir):
        """Add a batch to the list."""
        if file_list:
            batches.append({
                "name": name_prefix + "-" + str(len(batches) + 1).zfill(2),
                "files": list(file_list),
                "dir": base_dir,
            })

    # Process ordered files - respect mega threshold
    current_batch = []
    for f in files["ordered"]:
        filepath = os.path.join(LOGS_DIR, f)
        line_count = get_file_line_count(filepath)

        if line_count >= MEGA_THRESHOLD:
            # Flush current batch first
            if current_batch:
                flush_batch("ordered", current_batch, LOGS_DIR)
                current_batch = []
            # Mega file gets its own batch
            batches.append({
                "name": "mega-" + f[:40],
                "files": [f],
                "dir": LOGS_DIR,
                "mega": True,
            })
            logger.info("Mega file isolated: %s (%d lines)", f, line_count)
        else:
            current_batch.append(f)
            if len(current_batch) >= BATCH_SIZE:
                flush_batch("ordered", current_batch, LOGS_DIR)
                current_batch = []

    if current_batch:
        flush_batch("ordered", current_batch, LOGS_DIR)

    # Unlisted root files
    for i in range(0, len(files["unlisted"]), BATCH_SIZE):
        chunk = files["unlisted"][i:i + BATCH_SIZE]
        flush_batch("unlisted", chunk, LOGS_DIR)

    # Dated plans
    for i in range(0, len(files["dated_plans"]), BATCH_SIZE):
        chunk = files["dated_plans"][i:i + BATCH_SIZE]
        flush_batch("dated-plans", chunk, PLANS_DIR)

    # Auto-generated plans
    for i in range(0, len(files["auto_plans"]), BATCH_SIZE):
        chunk = files["auto_plans"][i:i + BATCH_SIZE]
        flush_batch("auto-plans", chunk, PLANS_DIR)

    return batches


def create_progress_file(batches, logger):
    """Write RESEARCH-PROGRESS.md with full checkbox list."""
    lines = []
    lines.append("# Research Progress Tracker\n")
    lines.append("\n")
    lines.append("**Created:** " + TODAY + "\n")
    total = sum(len(b["files"]) for b in batches)
    lines.append("**Total files:** " + str(total) + "\n")
    lines.append("\n---\n\n")

    for batch in batches:
        lines.append("## " + batch["name"] + "\n\n")
        for f in batch["files"]:
            full_path = os.path.join(batch["dir"], f)
            lines.append("- [ ] `" + full_path + "`\n")
        lines.append("\n")

    with open(PROGRESS_FILE, "w", encoding="utf-8") as fout:
        fout.writelines(lines)

    logger.info("Created progress file: %s (%d files tracked)", PROGRESS_FILE, total)


def build_batch_prompt(batch, batch_index, total_batches):
    """Construct the prompt for a single research batch."""
    batch_file = os.path.join(BATCH_DIR, "FINDINGS-" + batch["name"] + ".md")
    is_mega = batch.get("mega", False)

    file_list_lines = []
    for f in batch["files"]:
        full_path = os.path.join(batch["dir"], f)
        file_list_lines.append("- " + full_path)
    file_list = "\n".join(file_list_lines)

    mega_instruction = ""
    if is_mega:
        mega_instruction = (
            "\nSPECIAL: This batch contains a mega-file (over 5000 lines).\n"
            "You MUST read it in chunks using offset and limit parameters on the Read tool.\n"
            "Read 2000 lines at a time. Do NOT skip any section. Read every chunk.\n"
        )

    prompt = (
        "You are a research agent executing batch "
        + str(batch_index + 1)
        + " of "
        + str(total_batches)
        + " in a chronological log research task.\n\n"
        + "BATCH OUTPUT FILE: " + batch_file + "\n"
        + "PROGRESS FILE: " + PROGRESS_FILE + "\n"
        + mega_instruction
        + "\n"
        + "RULES (follow exactly):\n"
        + "1. Read each file below IN ORDER using the Read tool.\n"
        + "   - For files over 2000 lines, use offset and limit parameters to read in chunks of 2000.\n"
        + "   - Read ALL chunks until you reach the end. Never skip content.\n"
        + "2. After reading EACH file, build the findings block for that file.\n"
        + "3. Use this exact format for each file findings block:\n\n"
        + "---\n"
        + "## [filename]\n"
        + "**Date:** [date from filename or file content]\n"
        + "**Type:** [Session log / Build session / Strategy spec / Audit / Planning / Other]\n\n"
        + "### What happened\n"
        + "[Thorough factual summary of what was done or discussed - include specifics]\n\n"
        + "### Decisions recorded\n"
        + "[Any explicit decisions made - list each one. If none stated, write None.]\n\n"
        + "### State changes\n"
        + "[What changed - code built, specs created, bugs found/fixed, versions changed]\n\n"
        + "### Open items recorded\n"
        + "[Anything explicitly listed as pending, unresolved, or next step]\n\n"
        + "### Notes\n"
        + "[Anything that contradicts a previous log, or updates a prior decision. If nothing, write None.]\n\n"
        + "4. After building findings for ALL files in this batch, use the Write tool to create:\n"
        + "   " + batch_file + "\n"
        + "   Write ALL findings for this batch into that single file.\n"
        + "5. After writing the batch file, update the progress tracker.\n"
        + "   For each file completed, use the Edit tool on " + PROGRESS_FILE + "\n"
        + "   to change '- [ ]' to '- [x]' for that file's line.\n"
        + "6. CODE VERIFICATION: If a log references a Python script as a key deliverable:\n"
        + "   - Use Glob to find the script file on disk\n"
        + "   - Use Read to verify it exists and check if content matches the log's claims\n"
        + "   - Note the verification result in the findings under Notes\n"
        + "7. Be thorough and neutral. Record facts only, no interpretation or opinion.\n"
        + "8. Do NOT skip any file. Process every file in the list.\n\n"
        + "FILES TO READ (in order):\n"
        + file_list + "\n\n"
        + "Begin with the first file now. Read it fully, then proceed."
    )
    return prompt


def build_synthesis_prompt(total_batches):
    """Construct the synthesis prompt for the final batch."""
    # Point to the merged findings file (one large file) instead of 21 individual
    # batch files — reading all 21 separately overflows the context window.
    prompt = (
        "You are writing the SYNTHESIS for a completed chronological log research task.\n\n"
        + "All per-file findings have been merged into one document:\n"
        + FINDINGS_FILE + "\n\n"
        + "STEP 1 — Read the findings document in full.\n"
        + "The file is large. Use the Read tool with offset and limit (2000 lines per call).\n"
        + "Start at offset 0, then 2000, then 4000, etc. until you reach the end.\n"
        + "You will know you are done when the Read tool returns fewer lines than requested.\n\n"
        + "STEP 2 — After reading ALL content, write a comprehensive synthesis.\n"
        + "Use the Write tool to create:\n"
        + os.path.join(BATCH_DIR, "SYNTHESIS.md") + "\n\n"
        + "SYNTHESIS FORMAT:\n\n"
        + "# SYNTHESIS\n\n"
        + "Answer these 8 questions based ONLY on what the findings contain:\n\n"
        + "## 1. What is this project trying to achieve?\n"
        + "[Goal and vision, not implementation details]\n\n"
        + "## 2. Current state of each major component\n\n"
        + "### Four Pillars Backtester (Python)\n"
        + "[Status, version, what works, what does not]\n\n"
        + "### BingX Live Bot\n"
        + "[Status, version, deployment state]\n\n"
        + "### Vince ML pipeline (B1-B6)\n"
        + "[Status of each build step]\n\n"
        + "### Pine Script indicators\n"
        + "[Which exist, which are production-ready]\n\n"
        + "### Infrastructure (VPS, n8n, dashboards)\n"
        + "[What is deployed, what is local-only]\n\n"
        + "## 3. Primary blocker today\n"
        + "[What is preventing forward progress right now]\n\n"
        + "## 4. Decisions locked\n"
        + "[List ALL decisions recorded as final across ALL findings]\n\n"
        + "## 5. Decisions still open\n"
        + "[List ALL unresolved decisions found across findings]\n\n"
        + "## 6. Confirmed working\n"
        + "[What has been built AND verified/tested as working]\n\n"
        + "## 7. Built but unverified\n"
        + "[What was built but never tested or confirmed working]\n\n"
        + "## 8. Planned but never executed\n"
        + "[What was discussed or planned but never actually built]\n\n"
        + "Be thorough. Cross-reference findings across all sessions. Facts only.\n"
        + "This synthesis must be comprehensive — it is the final deliverable."
    )
    return prompt


def is_rate_limit_error(stdout_text, stderr_text):
    """Detect if failure was caused by rate limiting."""
    combined = (stdout_text or "") + (stderr_text or "")
    combined_lower = combined.lower()
    rate_keywords = ["rate limit", "rate_limit", "ratelimit", "too many requests", "429", "overloaded", "capacity"]
    for keyword in rate_keywords:
        if keyword in combined_lower:
            return True
    return False


def run_claude_batch(prompt, model, max_turns, batch_name, logger):
    """Execute a single claude -p invocation and return (success, was_rate_limited)."""
    # Build command as string — shell=True required for .cmd batch files on Windows.
    # Prompt is piped via stdin (not CLI arg) to avoid length/escaping issues.
    # claude -p (no positional arg) reads prompt from stdin.
    cmd = (
        '"' + CLAUDE_CMD + '"'
        " -p"
        ' --allowedTools "Read,Edit,Write,Glob,Grep"'
        " --max-turns " + str(max_turns) +
        " --model " + model
    )

    logger.info("Running claude -p (model=%s, max_turns=%d)", model, max_turns)
    logger.info("Command: %s", cmd)

    # Write prompt to temp file — cmd.exe native pipe is more reliable than
    # Python stdin pipe through cmd.exe → claude.cmd chain on Windows.
    prompt_file = os.path.join(BATCH_DIR, "_prompt_" + batch_name + ".txt")
    with open(prompt_file, "w", encoding="utf-8") as pf:
        pf.write(prompt)

    # Rebuild cmd to use type | pipe (cmd.exe handles .cmd files and piping natively)
    cmd = (
        'type "' + prompt_file + '" | '
        '"' + CLAUDE_CMD + '"'
        " -p"
        ' --allowedTools "Read,Edit,Write,Glob,Grep"'
        " --max-turns " + str(max_turns) +
        " --model " + model
    )
    logger.info("Using prompt file: %s", prompt_file)

    stdout_lines = []
    stderr_lines = []
    start_ts = datetime.now()

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=VAULT,
            shell=True,
        )

        # Stream stdout live — print each line as it arrives
        for line in proc.stdout:
            line = line.rstrip("\n")
            stdout_lines.append(line)
            elapsed = (datetime.now() - start_ts).seconds
            print(f"  [{batch_name}] +{elapsed}s | {line}", flush=True)

        proc.stdout.close()

        # Collect stderr
        for line in proc.stderr:
            stderr_lines.append(line.rstrip("\n"))
        proc.stderr.close()

        # Wait for process to exit (with timeout)
        try:
            proc.wait(timeout=BATCH_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            logger.error(
                "claude -p TIMEOUT for %s (exceeded %d seconds)",
                batch_name,
                BATCH_TIMEOUT_SECONDS,
            )
            return False, False

        stdout_text = "\n".join(stdout_lines)
        stderr_text = "\n".join(stderr_lines)

        # Clean up temp prompt file
        if os.path.exists(prompt_file):
            os.remove(prompt_file)

        if proc.returncode == 0:
            logger.info("claude -p completed successfully for %s", batch_name)
            return True, False
        else:
            rate_limited = is_rate_limit_error(stdout_text, stderr_text)
            logger.error(
                "claude -p failed for %s (exit code %d, rate_limited=%s)",
                batch_name,
                proc.returncode,
                rate_limited,
            )
            if stderr_text:
                logger.error("stderr: %s", stderr_text[:2000])
            return False, rate_limited

    except FileNotFoundError:
        logger.error(
            "claude CLI not found at %s. "
            "Verify path or install: npm install -g @anthropic-ai/claude-code",
            CLAUDE_CMD,
        )
        return False, False
    except Exception as e:
        logger.error("Unexpected error for %s: %s", batch_name, str(e))
        return False, False


def countdown_sleep(seconds, label):
    """Sleep for the given duration, printing a live progress bar."""
    bar_width = 40
    start_ts = datetime.now().timestamp()
    end_time = start_ts + seconds

    while True:
        now = datetime.now().timestamp()
        remaining = int(end_time - now)
        if remaining <= 0:
            break
        elapsed = now - start_ts
        pct = min(elapsed / seconds, 1.0)
        filled = int(bar_width * pct)
        bar = "█" * filled + "░" * (bar_width - filled)
        mins, secs = divmod(remaining, 60)
        print(
            f"\r  PAUSE [{bar}] {int(pct*100):3d}% | {mins:02d}:{secs:02d} left | next: {label}",
            end="",
            flush=True,
        )
        time.sleep(1)

    bar = "█" * bar_width
    print(f"\r  PAUSE [{bar}] 100% | 00:00 left | starting {label} now", flush=True)


def check_batch_progress(batch):
    """Check how many files from a batch are marked complete in progress file."""
    if not os.path.exists(PROGRESS_FILE):
        return 0, len(batch["files"])

    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    done = 0
    for filename in batch["files"]:
        full_path = os.path.join(batch["dir"], filename)
        marker = "- [x] `" + full_path + "`"
        if marker in content:
            done += 1

    return done, len(batch["files"])


def check_batch_file_exists(batch):
    """Check if the batch findings file already exists (indicates prior completion)."""
    batch_file = os.path.join(BATCH_DIR, "FINDINGS-" + batch["name"] + ".md")
    return os.path.isfile(batch_file)


def merge_findings(batches, logger):
    """Merge all batch findings files into the single RESEARCH-FINDINGS.md."""
    logger.info("Merging batch findings into %s", FINDINGS_FILE)

    header = (
        "# Project Research - Chronological Log Findings\n"
        + "**Task completed:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
        + "**Method:** Automated sequential batches via Claude Code CLI\n"
        + "**Total batches:** " + str(len(batches)) + "\n\n"
        + "---\n\n"
        + "*Findings begin below. Each file gets one section.*\n\n"
    )

    with open(FINDINGS_FILE, "w", encoding="utf-8") as out:
        out.write(header)

        for batch in batches:
            batch_file = os.path.join(BATCH_DIR, "FINDINGS-" + batch["name"] + ".md")
            if os.path.isfile(batch_file):
                with open(batch_file, "r", encoding="utf-8") as bf:
                    content = bf.read()
                out.write("\n")
                out.write(content)
                out.write("\n")
                logger.info("Merged: %s", batch_file)
            else:
                out.write("\n---\n\n## BATCH MISSING: " + batch["name"] + "\n\n")
                out.write("This batch did not produce a findings file.\n\n")
                logger.warning("Missing batch file: %s", batch_file)

        # Append synthesis if it exists
        synthesis_file = os.path.join(BATCH_DIR, "SYNTHESIS.md")
        if os.path.isfile(synthesis_file):
            with open(synthesis_file, "r", encoding="utf-8") as sf:
                out.write("\n\n---\n\n")
                out.write(sf.read())
            logger.info("Merged synthesis")
        else:
            logger.warning("Synthesis file not found: %s", synthesis_file)

    logger.info("Merge complete: %s", FINDINGS_FILE)


def main():
    """Orchestrate the full research task across all batches."""
    logger = setup_logging()
    start_time = datetime.now()

    logger.info("=" * 70)
    logger.info("RESEARCH ORCHESTRATOR STARTED")
    logger.info("=" * 70)
    logger.info("Vault: %s", VAULT)
    logger.info("Findings output: %s", FINDINGS_FILE)
    logger.info("Batch files dir: %s", BATCH_DIR)
    logger.info("Progress tracker: %s", PROGRESS_FILE)
    logger.info("Log file: %s", LOG_FILE)

    # Create batch output directory
    os.makedirs(BATCH_DIR, exist_ok=True)

    # Phase 1: Discover files
    logger.info("-" * 40)
    logger.info("PHASE 1: File discovery")
    files = discover_files(logger)
    total_files = sum(len(v) for v in files.values())
    logger.info("Total files to process: %d", total_files)

    # Phase 2: Build batches
    logger.info("-" * 40)
    logger.info("PHASE 2: Building batches")
    batches = build_batches(files, logger)
    total_batches = len(batches) + 1  # +1 for synthesis
    logger.info("Built %d file batches + 1 synthesis = %d total", len(batches), total_batches)
    for i, b in enumerate(batches):
        file_count = len(b["files"])
        is_mega = " [MEGA]" if b.get("mega") else ""
        logger.info("  Batch %02d: %-40s (%d files)%s", i + 1, b["name"], file_count, is_mega)

    # Phase 3: Create progress file
    logger.info("-" * 40)
    logger.info("PHASE 3: Progress tracking")
    if os.path.exists(PROGRESS_FILE):
        logger.info("Progress file exists - will resume from last checkpoint")
    else:
        create_progress_file(batches, logger)

    # Phase 4: Execute batches
    logger.info("-" * 40)
    logger.info("PHASE 4: Executing %d batches sequentially", len(batches))
    failed_batches = []
    skipped_batches = []

    for i, batch in enumerate(batches):
        batch_name = batch["name"]

        # Check if already completed
        if check_batch_file_exists(batch):
            done, total = check_batch_progress(batch)
            if done == total:
                logger.info(
                    "SKIP batch %d/%d: %s (already complete, findings file exists)",
                    i + 1, total_batches, batch_name,
                )
                skipped_batches.append(batch_name)
                continue
            else:
                logger.info(
                    "RE-RUN batch %d/%d: %s (findings file exists but progress incomplete: %d/%d)",
                    i + 1, total_batches, batch_name, done, total,
                )

        logger.info("=" * 50)
        logger.info("STARTING batch %d/%d: %s (%d files)", i + 1, total_batches, batch_name, len(batch["files"]))
        logger.info("=" * 50)
        # Overall progress bar
        done_count = i + len(skipped_batches)
        pct = int(done_count / len(batches) * 100)
        filled = int(40 * done_count / len(batches))
        bar = "█" * filled + "░" * (40 - filled)
        print(f"  OVERALL [{bar}] {pct:3d}% | batch {i+1}/{len(batches)} | {batch_name}", flush=True)

        # Determine max turns
        max_turns = MAX_TURNS_MEGA if batch.get("mega") else MAX_TURNS_NORMAL

        # Build prompt
        prompt = build_batch_prompt(batch, i, total_batches)
        logger.info("Prompt length: %d characters", len(prompt))

        # Execute with retry and rate-limit-aware backoff ($100 Max plan)
        success, rate_limited = run_claude_batch(prompt, RESEARCH_MODEL, max_turns, batch_name, logger)

        for retry in range(MAX_RETRIES):
            if success:
                break
            # Rate-limit hit = longer wait, normal failure = standard wait
            if rate_limited:
                wait = RATE_LIMIT_BACKOFF_SECONDS
                logger.info(
                    "RATE LIMITED — waiting %d seconds (%d min) before retry %d/%d for %s...",
                    wait, wait // 60, retry + 1, MAX_RETRIES, batch_name,
                )
            else:
                wait = RETRY_BACKOFF_SECONDS * (retry + 1)
                logger.info(
                    "Retry %d/%d for %s — waiting %d seconds...",
                    retry + 1, MAX_RETRIES, batch_name, wait,
                )
            countdown_sleep(wait, batch_name)
            success, rate_limited = run_claude_batch(prompt, RESEARCH_MODEL, max_turns, batch_name, logger)

        if success:
            done, total = check_batch_progress(batch)
            logger.info("Batch %s progress: %d/%d files checked off", batch_name, done, total)
        else:
            logger.error("Batch %s FAILED after retries", batch_name)
            failed_batches.append(batch_name)

        # Pause between batches
        if i < len(batches) - 1:
            logger.info("Pausing %d seconds before next batch...", BATCH_PAUSE_SECONDS)
            countdown_sleep(BATCH_PAUSE_SECONDS, batch_name)

    # Phase 5: Synthesis
    logger.info("-" * 40)
    logger.info("PHASE 5: Synthesis")

    synthesis_file = os.path.join(BATCH_DIR, "SYNTHESIS.md")
    if os.path.isfile(synthesis_file):
        logger.info("Synthesis file already exists - skipping")
    else:
        logger.info("Running synthesis batch (model=%s)...", SYNTHESIS_MODEL)
        prompt = build_synthesis_prompt(total_batches)
        success, _ = run_claude_batch(
            prompt, SYNTHESIS_MODEL, MAX_TURNS_SYNTHESIS, "synthesis", logger
        )
        if not success:
            logger.error("Synthesis batch FAILED")
            failed_batches.append("synthesis")

    # Phase 6: Merge
    logger.info("-" * 40)
    logger.info("PHASE 6: Merging findings")
    merge_findings(batches, logger)

    # Phase 7: Summary
    elapsed = datetime.now() - start_time
    hours = elapsed.total_seconds() / 3600

    logger.info("=" * 70)
    logger.info("RESEARCH ORCHESTRATOR COMPLETE")
    logger.info("=" * 70)
    logger.info("Total batches: %d", total_batches)
    logger.info("Skipped (already done): %d", len(skipped_batches))
    logger.info("Failed: %d", len(failed_batches))
    if failed_batches:
        logger.info("Failed batches: %s", ", ".join(failed_batches))
    logger.info("Elapsed time: %.1f hours", hours)
    logger.info("Final output: %s", FINDINGS_FILE)
    logger.info("Batch files: %s", BATCH_DIR)
    logger.info("Progress: %s", PROGRESS_FILE)
    logger.info("Log: %s", LOG_FILE)
    logger.info("=" * 70)

    if failed_batches:
        logger.info("To retry failed batches, run the script again - it will skip completed ones.")

    return 0 if not failed_batches else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nStopped by user (Ctrl+C). Progress saved — re-run to resume.", flush=True)
        sys.exit(0)

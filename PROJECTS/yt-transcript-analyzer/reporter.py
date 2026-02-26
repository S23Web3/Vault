"""Generates Obsidian markdown report from analysis findings."""
import json
import logging
import re
from datetime import datetime, timezone

from config import FINDINGS_PATH, MANIFEST_VIDEOS_PATH, REPORTS_PATH

log = logging.getLogger(__name__)


def make_slug(query: str, max_len: int = 50) -> str:
    """Convert query string to a filename-safe slug (lowercase, hyphens, no special chars)."""
    slug = query.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug[:max_len]


def load_findings() -> list:
    """Load all finding JSON files from FINDINGS_PATH, sorted by source_id and chunk_index."""
    findings = []
    for f in FINDINGS_PATH.glob("*.json"):
        try:
            findings.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as exc:
            log.warning("Failed to load %s: %s", f.name, exc)
    findings.sort(key=lambda x: (x.get("source_id", ""), x.get("chunk_index", 0)))
    return findings


def load_channel_name() -> str:
    """Load channel name from manifest_videos.json. Returns Unknown Channel on failure."""
    try:
        if MANIFEST_VIDEOS_PATH.exists():
            data = json.loads(MANIFEST_VIDEOS_PATH.read_text(encoding="utf-8"))
            return data.get("channel_name", "Unknown Channel")
    except Exception:
        pass
    return "Unknown Channel"


def generate_report(query: str) -> "Path":
    """Generate Obsidian markdown report for the given query. Returns the output file path."""
    from pathlib import Path  # local import avoids circular at module level
    findings = load_findings()
    channel_name = load_channel_name()
    now = datetime.now(timezone.utc)
    slug = make_slug(query)
    out_path = REPORTS_PATH / (now.strftime("%Y-%m-%d") + "-" + slug + ".md")
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Research Report: " + query,
        "",
        "**Channel:** " + channel_name,
        "**Query:** " + query,
        "**Generated:** " + now.strftime("%Y-%m-%d %H:%M UTC"),
        "**Findings:** " + str(len(findings)),
        "",
        "---",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("*No relevant content found for this query.*")
    else:
        for idx, finding in enumerate(findings, 1):
            lines.extend([
                "### Finding " + str(idx),
                "",
                "- **Source:** `" + finding.get("source_id", "unknown") + "`",
                "- **Chunk:** " + str(finding.get("chunk_index", 0)),
                "- **Analyzed:** " + finding.get("analyzed_at", ""),
                "",
                "> " + finding.get("quote", ""),
                "",
                "---",
                "",
            ])
    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report: %s (%d findings)", out_path.name, len(findings))
    return out_path

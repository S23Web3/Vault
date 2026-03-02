"""Generates Obsidian markdown reports with clickable YouTube timestamp links."""
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from cleaner import extract_video_id_from_clean
from config import CLEAN_PATH, FINDINGS_PATH, MANIFEST_VIDEOS_PATH, REPORTS_PATH, SUMMARIES_PATH

log = logging.getLogger(__name__)


def make_slug(query: str, max_len: int = 50) -> str:
    """Convert query string to a filename-safe slug (lowercase, hyphens, no special chars)."""
    slug = query.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug[:max_len]


def seconds_to_mmss(secs: float) -> str:
    """Convert seconds to MM:SS string. Minutes can exceed 59."""
    total_min = int(secs) // 60
    sec = int(secs) % 60
    return str(total_min).zfill(2) + ":" + str(sec).zfill(2)


def parse_timestamp_line(line: str) -> tuple:
    """Parse [MM:SS] prefix from a line. Returns (seconds, rest_of_line) or (None, line)."""
    match = re.match(r"^\[(\d+):(\d{2})\]\s*(.*)", line)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        total_secs = minutes * 60 + seconds
        return total_secs, match.group(3)
    return None, line


def make_youtube_link(video_id: str, seconds: int, label: str = "") -> str:
    """Build clickable markdown YouTube link with timestamp."""
    mmss = seconds_to_mmss(seconds)
    display = label if label else mmss
    return "[" + display + "](https://www.youtube.com/watch?v=" + video_id + "&t=" + str(seconds) + ")"


def format_timestamped_line(line: str, video_id: str) -> str:
    """Replace [MM:SS] prefix with clickable YouTube link. Returns line unchanged if no prefix."""
    secs, rest = parse_timestamp_line(line)
    if secs is not None and video_id:
        return make_youtube_link(video_id, secs) + " " + rest
    return line


def load_manifest_videos() -> dict:
    """Load manifest_videos.json. Returns dict keyed by video id."""
    try:
        if MANIFEST_VIDEOS_PATH.exists():
            data = json.loads(MANIFEST_VIDEOS_PATH.read_text(encoding="utf-8"))
            videos = {}
            for v in data.get("videos", []):
                vid = v.get("id", "")
                if vid:
                    videos[vid] = v
            return videos
    except Exception:
        pass
    return {}


def load_summary(video_id: str) -> dict:
    """Load summary JSON for a video. Returns empty dict if not found."""
    path = SUMMARIES_PATH / (video_id + ".json")
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


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


def escape_table_cell(text: str) -> str:
    """Escape pipe characters for markdown table cells."""
    return text.replace("|", "\\|")


def load_channel_name() -> str:
    """Load channel name from manifest_videos.json. Returns Unknown Channel on failure."""
    try:
        if MANIFEST_VIDEOS_PATH.exists():
            data = json.loads(MANIFEST_VIDEOS_PATH.read_text(encoding="utf-8"))
            return data.get("channel_name", "Unknown Channel")
    except Exception:
        pass
    return "Unknown Channel"


def generate_report(query: str) -> Path:
    """Generate Obsidian markdown report for the given query. Returns the output file path."""
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
            source_id = finding.get("source_id", "unknown")
            video_id = ""
            name_match = re.match(r"^\d{8}-([a-zA-Z0-9_-]{11})-", source_id)
            if name_match:
                video_id = name_match.group(1)
            quote = finding.get("quote", "")
            lines.extend([
                "### Finding " + str(idx),
                "",
                "- **Source:** `" + source_id + "`",
                "- **Chunk:** " + str(finding.get("chunk_index", 0)),
            ])
            if video_id:
                lines.append("- **Video:** [Open on YouTube](https://www.youtube.com/watch?v=" + video_id + ")")
            lines.extend([
                "",
                "> " + quote,
                "",
                "---",
                "",
            ])
    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report: %s (%d findings)", out_path.name, len(findings))
    return out_path


def generate_full_report() -> Path:
    """Generate structured channel report with TOC, summaries, tags, and timestamp links."""
    channel_name = load_channel_name()
    manifest_videos = load_manifest_videos()
    now = datetime.now(timezone.utc)
    slug = make_slug(channel_name) or "full-drain"
    out_path = REPORTS_PATH / (now.strftime("%Y-%m-%d") + "-" + slug + "-full.md")
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    clean_files = sorted(CLEAN_PATH.glob("*.txt")) if CLEAN_PATH.exists() else []

    # Build per-video data
    video_entries = []
    for clean_file in clean_files:
        video_id = extract_video_id_from_clean(clean_file)
        manifest_entry = manifest_videos.get(video_id, {})
        title = manifest_entry.get("title", clean_file.stem)
        summary_data = load_summary(video_id)
        summary = summary_data.get("summary", "")
        tags = summary_data.get("tags", [])
        text = clean_file.read_text(encoding="utf-8").strip()
        video_entries.append({
            "video_id": video_id,
            "title": title,
            "summary": summary,
            "tags": tags,
            "text": text,
        })

    # Header
    lines = [
        "# Channel Analysis: " + channel_name,
        "",
        "**Videos:** " + str(len(video_entries)),
        "**Generated:** " + now.strftime("%Y-%m-%d %H:%M UTC"),
        "",
        "---",
        "",
    ]

    # Table of Contents
    if video_entries:
        lines.extend(["## Table of Contents", ""])
        lines.append("| # | Video | Tags | Summary |")
        lines.append("| --- | --- | --- | --- |")
        for idx, entry in enumerate(video_entries, 1):
            vid = entry["video_id"]
            title = escape_table_cell(entry["title"])
            tags_str = escape_table_cell(", ".join(entry["tags"])) if entry["tags"] else ""
            summary_short = entry["summary"][:80] + "..." if len(entry["summary"]) > 80 else entry["summary"]
            summary_short = escape_table_cell(summary_short)
            if vid:
                video_link = "[" + title + "](https://www.youtube.com/watch?v=" + vid + ")"
            else:
                video_link = title
            lines.append("| " + str(idx) + " | " + video_link + " | " + tags_str + " | " + summary_short + " |")
        lines.extend(["", "---", ""])

    # Per-video sections
    if not video_entries:
        lines.append("*No transcripts found.*")
    else:
        for idx, entry in enumerate(video_entries, 1):
            vid = entry["video_id"]
            lines.append("## " + str(idx) + ". " + entry["title"])
            if entry["tags"]:
                lines.append("**Tags:** " + ", ".join(entry["tags"]))
            if entry["summary"]:
                lines.append("**Summary:** " + entry["summary"])
            lines.append("")
            # Process transcript lines with timestamp links
            for line in entry["text"].split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("<!--"):
                    continue
                lines.append(format_timestamped_line(line, vid))
            lines.extend(["", "---", ""])

    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Full report: %s (%d videos)", out_path.name, len(video_entries))
    return out_path

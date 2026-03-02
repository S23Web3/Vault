"""Cleans VTT subtitle files into plain text with 30-second block grouping."""
import logging
import re
from pathlib import Path

from config import BLOCK_INTERVAL_SECONDS, CLEAN_PATH, RAW_PATH

log = logging.getLogger(__name__)


def vtt_timestamp_to_seconds(ts: str) -> float:
    """Convert VTT timestamp string (HH:MM:SS.mmm or MM:SS.mmm) to float seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return 0.0


def parse_vtt(path: Path) -> list:
    """Parse VTT file into list of (start_seconds, text) tuples."""
    entries = []
    content = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\n+", content.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        ts_line = None
        text_lines = []
        for line in lines:
            if "-->" in line:
                ts_line = line
            elif ts_line is not None and line.strip() and not line.strip().isdigit():
                clean = re.sub(r"<[^>]+>", "", line).strip()
                if clean:
                    text_lines.append(clean)
        if ts_line and text_lines:
            start_ts = ts_line.split("-->")[0].strip()
            entries.append((vtt_timestamp_to_seconds(start_ts), " ".join(text_lines)))
    return entries


def deduplicate(entries: list) -> list:
    """Remove consecutive duplicate lines using exact match on stripped lowercase."""
    deduped = []
    prev = None
    for sec, text in entries:
        normalized = text.strip().lower()
        if normalized != prev:
            deduped.append((sec, text))
            prev = normalized
    return deduped


def seconds_to_mmss(secs: float) -> str:
    """Convert seconds to MM:SS string. Minutes can exceed 59 for long videos."""
    total_min = int(secs) // 60
    sec = int(secs) % 60
    return str(total_min).zfill(2) + ":" + str(sec).zfill(2)


def extract_video_id(filename: str) -> str:
    """Extract YouTube video ID from VTT filename. Pattern: YYYYMMDD-VIDEOID-Title.en.vtt."""
    match = re.match(r"^\d{8}-([a-zA-Z0-9_-]{11})-", filename)
    if match:
        return match.group(1)
    return ""


def group_into_blocks(entries: list, interval: int = BLOCK_INTERVAL_SECONDS) -> list:
    """Group entries into fixed-interval time blocks. Returns list of (start_seconds, block_text) tuples."""
    if not entries:
        return []
    blocks = []
    current_texts = []
    current_block_start = entries[0][0]
    current_block_idx = int(entries[0][0] // interval)
    for sec, text in entries:
        block_idx = int(sec // interval)
        if block_idx != current_block_idx:
            if current_texts:
                blocks.append((current_block_start, " ".join(current_texts)))
            current_texts = [text]
            current_block_start = sec
            current_block_idx = block_idx
        else:
            current_texts.append(text)
    if current_texts:
        blocks.append((current_block_start, " ".join(current_texts)))
    return blocks


def extract_video_id_from_clean(clean_path: Path) -> str:
    """Extract video_id from clean file metadata comment or filename."""
    try:
        first_line = clean_path.read_text(encoding="utf-8").split("\n", 1)[0]
        match = re.match(r"<!--\s*video_id:(\S+)\s*-->", first_line)
        if match:
            return match.group(1)
    except Exception:
        pass
    name_match = re.match(r"^\d{8}-([a-zA-Z0-9_-]{11})-", clean_path.stem)
    return name_match.group(1) if name_match else ""


def clean_vtt_file(vtt_path: Path) -> Path:
    """Clean a single VTT file and write output to CLEAN_PATH. Returns output path."""
    entries = parse_vtt(vtt_path)
    entries = deduplicate(entries)
    blocks = group_into_blocks(entries)
    video_id = extract_video_id(vtt_path.name)
    lines = []
    if video_id:
        lines.append("<!-- video_id:" + video_id + " -->")
    for start_sec, text in blocks:
        lines.append("[" + seconds_to_mmss(start_sec) + "] " + text)
    clean_text = "\n\n".join(lines)
    CLEAN_PATH.mkdir(parents=True, exist_ok=True)
    out_path = CLEAN_PATH / (vtt_path.stem + ".txt")
    out_path.write_text(clean_text, encoding="utf-8")
    log.debug("Cleaned %s -> %d blocks, video_id=%s", vtt_path.name, len(blocks), video_id)
    return out_path


def clean_all() -> list:
    """Clean all VTT files in RAW_PATH. Returns list of output paths."""
    vtt_files = list(RAW_PATH.glob("*.vtt"))
    log.info("Cleaning %d VTT files", len(vtt_files))
    outputs = []
    for vtt in vtt_files:
        try:
            outputs.append(clean_vtt_file(vtt))
        except Exception as exc:
            log.error("Failed to clean %s: %s", vtt.name, exc)
    log.info("Cleaned %d files", len(outputs))
    return outputs

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


def group_into_blocks(entries: list, interval: int = BLOCK_INTERVAL_SECONDS) -> list:
    """Group entries into fixed-interval time blocks. Returns list of block text strings."""
    if not entries:
        return []
    blocks = []
    current_texts = []
    current_block_idx = int(entries[0][0] // interval)
    for sec, text in entries:
        block_idx = int(sec // interval)
        if block_idx != current_block_idx:
            if current_texts:
                blocks.append(" ".join(current_texts))
            current_texts = [text]
            current_block_idx = block_idx
        else:
            current_texts.append(text)
    if current_texts:
        blocks.append(" ".join(current_texts))
    return blocks


def clean_vtt_file(vtt_path: Path) -> Path:
    """Clean a single VTT file and write output to CLEAN_PATH. Returns output path."""
    entries = parse_vtt(vtt_path)
    entries = deduplicate(entries)
    blocks = group_into_blocks(entries)
    clean_text = "\n\n".join(blocks)
    CLEAN_PATH.mkdir(parents=True, exist_ok=True)
    out_path = CLEAN_PATH / (vtt_path.stem + ".txt")
    out_path.write_text(clean_text, encoding="utf-8")
    log.debug("Cleaned %s -> %d blocks", vtt_path.name, len(blocks))
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

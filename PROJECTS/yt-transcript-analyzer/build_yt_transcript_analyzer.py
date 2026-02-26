"""
Build script for yt-transcript-analyzer.
Generates all project source files, runs py_compile + ast.parse on each.
Run: python build_yt_transcript_analyzer.py
"""

import ast
import py_compile
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT   = Path(__file__).parent
TESTS  = ROOT / "tests"
ERRORS = []

TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def write_and_verify(rel_path: str, content: str) -> None:
    """Write content to ROOT/rel_path; py_compile + ast.parse for .py files."""
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if path.suffix == ".py":
        try:
            py_compile.compile(str(path), doraise=True)
            ast.parse(content, filename=rel_path)
            print("  OK  " + rel_path)
        except Exception as exc:
            print("  FAIL " + rel_path + ": " + str(exc))
            ERRORS.append(rel_path)
    else:
        print("  OK  " + rel_path + " (non-py)")


print("=" * 60)
print("yt-transcript-analyzer build  " + TS)
print("Root: " + str(ROOT))
print("=" * 60)

# ---------------------------------------------------------------------------
# requirements.txt
# ---------------------------------------------------------------------------
write_and_verify("requirements.txt", r'''yt-dlp
webvtt-py
requests
python-dotenv
''')

# ---------------------------------------------------------------------------
# .env.example
# ---------------------------------------------------------------------------
write_and_verify(".env.example", r'''# Copy to .env and fill in values
OUTPUT_PATH=output
OLLAMA_BASE_URL=http://localhost:11434
''')

# ---------------------------------------------------------------------------
# config.py
# ---------------------------------------------------------------------------
write_and_verify("config.py", r'''"""Configuration constants for yt-transcript-analyzer."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Output root — override via OUTPUT_PATH env var or .env
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "output"))

# Sub-directories
DATA_PATH     = OUTPUT_PATH / "data"
RAW_PATH      = OUTPUT_PATH / "raw"
CLEAN_PATH    = OUTPUT_PATH / "clean"
CHUNKS_PATH   = OUTPUT_PATH / "chunks"
FINDINGS_PATH = OUTPUT_PATH / "findings"
REPORTS_PATH  = OUTPUT_PATH / "reports"

# Data files
ARCHIVE_PATH         = DATA_PATH / "archive.txt"
SKIP_PATH            = DATA_PATH / "skipped.txt"
MANIFEST_VIDEOS_PATH = DATA_PATH / "manifest_videos.json"
MANIFEST_CHUNKS_PATH = DATA_PATH / "manifest_chunks.json"

# Ollama
OLLAMA_BASE_URL       = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
QWEN_MODEL            = "qwen3:8b"
QWEN_THINKING         = True
CHUNK_TOKENIZER_MODEL = "qwen3:8b"
OLLAMA_RETRIES        = 2
OLLAMA_TIMEOUT        = 120  # seconds

# Chunking
CHUNK_SIZE    = 2500  # tokens (safety margin via Ollama tokenizer)
CHUNK_OVERLAP = 200   # tokens (used as approximate word count for overlap step)

# Cleaning
BLOCK_INTERVAL_SECONDS = 30

# Fetcher
YTDLP_RETRIES = 10
''')

# ---------------------------------------------------------------------------
# startup.py
# ---------------------------------------------------------------------------
write_and_verify("startup.py", r'''"""Startup checks — verifies all dependencies before running pipeline."""
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
''')

# ---------------------------------------------------------------------------
# fetcher.py
# ---------------------------------------------------------------------------
write_and_verify("fetcher.py", r'''"""Fetches YouTube subtitles via yt-dlp. Handles all channel URL formats."""
import json
import logging
import subprocess
from datetime import datetime, timezone

from config import ARCHIVE_PATH, MANIFEST_VIDEOS_PATH, RAW_PATH, YTDLP_RETRIES

log = logging.getLogger(__name__)


def extract_channel_name(url: str) -> str:
    """Extract human-readable channel name from any YouTube URL format."""
    if "/@" in url:
        return url.split("/@")[1].split("/")[0].split("?")[0]
    for prefix in ["/c/", "/user/"]:
        if prefix in url:
            return url.split(prefix)[1].split("/")[0].split("?")[0]
    return _fetch_channel_name_via_ytdlp(url)


def _fetch_channel_name_via_ytdlp(url: str) -> str:
    """Fetch channel display name for /channel/UC... URLs via yt-dlp flat-playlist."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-json", "--playlist-items", "1", url],
            capture_output=True, text=True, timeout=30,
        )
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
                name = data.get("channel") or data.get("uploader") or ""
                if name:
                    return name
            except json.JSONDecodeError:
                continue
    except subprocess.TimeoutExpired:
        log.warning("yt-dlp name lookup timed out for URL: %s", url)
    return "unknown_channel"


def prescan_channel(url: str) -> list:
    """Pre-scan channel/playlist to collect video metadata for progress tracking."""
    log.info("Pre-scanning: %s", url)
    videos = []
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-json", url],
            capture_output=True, text=True, timeout=300,
        )
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
                if data.get("_type") in ("url", "video") or "id" in data:
                    videos.append({
                        "id": data.get("id", ""),
                        "title": data.get("title", ""),
                        "duration": data.get("duration", 0),
                    })
            except json.JSONDecodeError:
                continue
    except subprocess.TimeoutExpired:
        log.warning("Pre-scan timed out for: %s", url)
    log.info("Pre-scan: %d videos found", len(videos))
    return videos


def fetch_subtitles(url: str) -> None:
    """Download auto-generated English VTT subtitles for all videos in a channel or playlist URL."""
    channel_name = extract_channel_name(url)
    log.info("Channel: %s", channel_name)

    videos = prescan_channel(url)
    log.info("Total: %d videos", len(videos))

    _write_manifest_videos(videos, channel_name, url)

    RAW_PATH.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)

    output_template = str(RAW_PATH / "%(upload_date)s-%(id)s-%(title)s.%(ext)s")
    archive_str = str(ARCHIVE_PATH)

    cmd = [
        "yt-dlp",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--skip-download",
        "--ignore-errors",
        "--retries", str(YTDLP_RETRIES),
        "--retry-sleep", "exp=1",
        "--download-archive", archive_str,
        "--output", output_template,
        url,
    ]

    log.info("Downloading subtitles (%d videos)...", len(videos))
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        log.error("yt-dlp exited with code %d", result.returncode)
    else:
        log.info("yt-dlp completed")


def _write_manifest_videos(videos: list, channel_name: str, url: str) -> None:
    """Write manifest_videos.json from pre-scan results."""
    MANIFEST_VIDEOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "channel_name": channel_name,
        "channel_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "videos": videos,
    }
    MANIFEST_VIDEOS_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote manifest_videos.json (%d videos)", len(videos))
''')

# ---------------------------------------------------------------------------
# cleaner.py
# ---------------------------------------------------------------------------
write_and_verify("cleaner.py", r'''"""Cleans VTT subtitle files into plain text with 30-second block grouping."""
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
''')

# ---------------------------------------------------------------------------
# chunker.py
# ---------------------------------------------------------------------------
write_and_verify("chunker.py", r'''"""Splits clean transcript files into overlapping token-counted chunks."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNK_TOKENIZER_MODEL,
    CHUNKS_PATH,
    CLEAN_PATH,
    MANIFEST_CHUNKS_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
)

log = logging.getLogger(__name__)


def count_tokens(text: str) -> int:
    """Count tokens via Ollama /api/tokenize using qwen3:8b as reference tokenizer."""
    resp = requests.post(
        OLLAMA_BASE_URL + "/api/tokenize",
        json={"model": CHUNK_TOKENIZER_MODEL, "content": text},
        timeout=OLLAMA_TIMEOUT,
    )
    resp.raise_for_status()
    return len(resp.json()["tokens"])


def split_into_chunks(text: str, source_id: str) -> list:
    """Split text into chunks of up to CHUNK_SIZE tokens with CHUNK_OVERLAP word overlap."""
    words = text.split()
    if not words:
        return []
    chunks = []
    chunk_idx = 0
    start = 0
    while start < len(words):
        # Binary search for max words that fit within CHUNK_SIZE tokens
        lo = 1
        hi = min(len(words) - start, CHUNK_SIZE * 2)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if count_tokens(" ".join(words[start:start + mid])) <= CHUNK_SIZE:
                lo = mid
            else:
                hi = mid - 1
        end = start + lo
        chunk_text = " ".join(words[start:end])
        chunks.append({
            "chunk_id": source_id + "_chunk" + str(chunk_idx).zfill(4),
            "source_id": source_id,
            "chunk_index": chunk_idx,
            "token_count": count_tokens(chunk_text),
            "text": chunk_text,
        })
        chunk_idx += 1
        # Advance start: apply overlap (CHUNK_OVERLAP as approximate word count)
        chunk_word_count = end - start
        if chunk_word_count <= CHUNK_OVERLAP:
            start = end  # chunk smaller than overlap window — no overlap, advance past it
        else:
            start = end - CHUNK_OVERLAP  # step back by overlap
    return chunks


def chunk_file(clean_path: Path) -> list:
    """Chunk a single clean transcript file. Returns list of chunk dicts."""
    text = clean_path.read_text(encoding="utf-8").strip()
    if not text:
        log.warning("Empty file: %s", clean_path.name)
        return []
    source_id = clean_path.stem
    log.debug("Chunking %s", clean_path.name)
    chunks = split_into_chunks(text, source_id)
    log.debug("  %d chunks from %s", len(chunks), clean_path.name)
    return chunks


def chunk_all() -> None:
    """Chunk all files in CLEAN_PATH and write chunk files + manifest_chunks.json."""
    clean_files = list(CLEAN_PATH.glob("*.txt"))
    log.info("Chunking %d clean files", len(clean_files))
    CHUNKS_PATH.mkdir(parents=True, exist_ok=True)
    all_chunks = []
    for clean_file in clean_files:
        try:
            chunks = chunk_file(clean_file)
            for chunk in chunks:
                chunk_path = CHUNKS_PATH / (chunk["chunk_id"] + ".txt")
                chunk_path.write_text(chunk["text"], encoding="utf-8")
            all_chunks.extend(chunks)
        except Exception as exc:
            log.error("Failed to chunk %s: %s", clean_file.name, exc)
    MANIFEST_CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_chunks": len(all_chunks),
        "chunks": all_chunks,
    }
    MANIFEST_CHUNKS_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote manifest_chunks.json (%d chunks)", len(all_chunks))
''')

# ---------------------------------------------------------------------------
# analyzer.py
# ---------------------------------------------------------------------------
write_and_verify("analyzer.py", r'''"""Analyzes transcript chunks against a user query using qwen3:8b via Ollama."""
import json
import logging
import re
import time
from datetime import datetime, timezone

import requests

from config import (
    FINDINGS_PATH,
    MANIFEST_CHUNKS_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_RETRIES,
    OLLAMA_TIMEOUT,
    QWEN_MODEL,
)

log = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "in", "of", "on", "at", "to", "for",
    "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "not", "with", "from", "by",
    "this", "that", "it", "its", "as", "do", "does", "did",
    "have", "has", "had", "will", "would", "could", "should",
    "i", "you", "we", "they", "he", "she", "my", "your",
}


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from model output (qwen3 thinking mode)."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_query_keywords(query: str) -> list:
    """Tokenize query into lowercase words, removing stop words."""
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    return [t for t in tokens if t not in STOP_WORDS]


def keyword_prefilter(text: str, keywords: list) -> bool:
    """Return True if any keyword from the list appears in text (case-insensitive)."""
    if not keywords:
        return True
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def call_ollama(model: str, prompt: str) -> str:
    """Call Ollama /api/generate with retry on failure. Returns response text or empty string."""
    payload = {"model": model, "prompt": prompt, "stream": False}
    last_exc = None
    for attempt in range(1, OLLAMA_RETRIES + 2):
        try:
            resp = requests.post(
                OLLAMA_BASE_URL + "/api/generate",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except requests.RequestException as exc:
            last_exc = exc
            log.warning("Ollama attempt %d/%d failed: %s", attempt, OLLAMA_RETRIES + 1, exc)
            if attempt <= OLLAMA_RETRIES:
                time.sleep(2 ** attempt)
    log.error("Ollama failed after %d attempts: %s", OLLAMA_RETRIES + 1, last_exc)
    return ""


def parse_response(raw: str) -> dict:
    """Parse FOUND and QUOTE fields from model response. Missing fields default to no/none."""
    found_match = re.search(r"^FOUND:\s*(.+)$", raw, re.MULTILINE | re.IGNORECASE)
    quote_match = re.search(r"^QUOTE:\s*(.+)$", raw, re.MULTILINE | re.IGNORECASE)
    if not found_match:
        log.warning("FOUND field missing in response — defaulting to no")
    if not quote_match:
        log.warning("QUOTE field missing in response — defaulting to none")
    found_val = found_match.group(1).strip().lower() if found_match else "no"
    quote_val = quote_match.group(1).strip() if quote_match else "none"
    return {
        "found": found_val.startswith("y"),
        "quote": quote_val,
    }


def build_prompt(query: str, chunk_text: str) -> str:
    """Build the analysis prompt sent to qwen3:8b."""
    return (
        "You are a research assistant analyzing a YouTube transcript excerpt.\n"
        "Determine if the excerpt contains information relevant to the query.\n\n"
        "QUERY: " + query + "\n\n"
        "TRANSCRIPT EXCERPT:\n" + chunk_text + "\n\n"
        "Respond in EXACTLY this format (two lines, nothing else):\n"
        "FOUND: yes or no\n"
        "QUOTE: <one brief relevant quote from the text, or 'none' if not found>\n"
    )


def analyze_chunk(chunk: dict, query: str, keywords: list) -> dict:
    """Analyze a single chunk dict against the query. Returns finding dict or None."""
    if not keyword_prefilter(chunk["text"], keywords):
        log.debug("Pre-filter skipped: %s", chunk["chunk_id"])
        return None
    prompt = build_prompt(query, chunk["text"])
    raw = call_ollama(QWEN_MODEL, prompt)
    if not raw:
        log.error("Empty response for chunk %s", chunk["chunk_id"])
        return None
    cleaned = strip_thinking(raw)
    parsed = parse_response(cleaned)
    if not parsed["found"]:
        return None
    return {
        "chunk_id": chunk["chunk_id"],
        "source_id": chunk["source_id"],
        "chunk_index": chunk["chunk_index"],
        "token_count": chunk["token_count"],
        "quote": parsed["quote"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def analyze_all(query: str) -> list:
    """Analyze all chunks from manifest_chunks.json. Returns list of finding dicts."""
    if not MANIFEST_CHUNKS_PATH.exists():
        log.error("manifest_chunks.json not found — run chunker first")
        return []
    manifest = json.loads(MANIFEST_CHUNKS_PATH.read_text(encoding="utf-8"))
    chunks = manifest.get("chunks", [])
    total = len(chunks)
    log.info("Analyzing %d chunks for: %s", total, query)
    keywords = extract_query_keywords(query)
    log.info("Keywords: %s", keywords)
    findings = []
    FINDINGS_PATH.mkdir(parents=True, exist_ok=True)
    for i, chunk in enumerate(chunks, 1):
        log.info("[%d/%d] %s", i, total, chunk["chunk_id"])
        finding = analyze_chunk(chunk, query, keywords)
        if finding:
            findings.append(finding)
            out = FINDINGS_PATH / (chunk["chunk_id"] + ".json")
            out.write_text(json.dumps(finding, indent=2), encoding="utf-8")
    log.info("Found %d relevant chunks out of %d", len(findings), total)
    return findings
''')

# ---------------------------------------------------------------------------
# reporter.py
# ---------------------------------------------------------------------------
write_and_verify("reporter.py", r'''"""Generates Obsidian markdown report from analysis findings."""
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
''')

# ---------------------------------------------------------------------------
# main.py
# ---------------------------------------------------------------------------
write_and_verify("main.py", r'''"""Main pipeline orchestrator for yt-transcript-analyzer."""
import argparse
import logging
import sys
from datetime import datetime, timezone

import startup
import fetcher
import cleaner
import chunker
import analyzer
import reporter
from config import (
    CHUNKS_PATH, CLEAN_PATH, DATA_PATH, FINDINGS_PATH, RAW_PATH, REPORTS_PATH,
)


def ensure_dirs() -> None:
    """Create all required output directories."""
    for path in [DATA_PATH, RAW_PATH, CLEAN_PATH, CHUNKS_PATH, FINDINGS_PATH, REPORTS_PATH]:
        path.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configure pipeline logging to stdout and pipeline.log file."""
    log_file = DATA_PATH / "pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), encoding="utf-8"),
        ],
    )


def main() -> None:
    """Parse arguments and run the requested pipeline stage(s)."""
    parser = argparse.ArgumentParser(description="YouTube Transcript Analyzer")
    parser.add_argument("url", nargs="?", help="YouTube channel or playlist URL")
    parser.add_argument("--query", "-q", help="Search query for analyze/report stages")
    parser.add_argument(
        "--stage",
        choices=["fetch", "clean", "chunk", "analyze", "report", "all"],
        default="all",
        help="Pipeline stage to run (default: all)",
    )
    args = parser.parse_args()

    ensure_dirs()
    setup_logging()

    log = logging.getLogger("main")
    log.info("Pipeline started at %s", datetime.now(timezone.utc).isoformat())

    if not startup.run_checks():
        print("Startup checks failed — fix the above issues and retry.")
        sys.exit(1)

    if args.stage in ("fetch", "all"):
        if not args.url:
            print("URL required for fetch stage.")
            sys.exit(1)
        fetcher.fetch_subtitles(args.url)

    if args.stage in ("clean", "all"):
        cleaner.clean_all()

    if args.stage in ("chunk", "all"):
        chunker.chunk_all()

    if args.stage in ("analyze", "all"):
        if not args.query:
            print("--query required for analyze stage.")
            sys.exit(1)
        analyzer.analyze_all(args.query)

    if args.stage in ("report", "all"):
        if not args.query:
            print("--query required for report stage.")
            sys.exit(1)
        out = reporter.generate_report(args.query)
        print("Report: " + str(out))

    log.info("Pipeline complete at %s", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()
''')

# ---------------------------------------------------------------------------
# tests/test_cleaner.py
# ---------------------------------------------------------------------------
write_and_verify("tests/test_cleaner.py", r'''"""Tests for cleaner.py — VTT parsing and deduplication logic."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cleaner import deduplicate, group_into_blocks, parse_vtt, vtt_timestamp_to_seconds


class TestVttTimestampToSeconds(unittest.TestCase):
    """Test VTT timestamp string parsing."""

    def test_hms_format(self):
        """HH:MM:SS.mmm format parses to float seconds."""
        self.assertAlmostEqual(vtt_timestamp_to_seconds("00:01:30.000"), 90.0)

    def test_ms_format(self):
        """MM:SS.mmm format parses to float seconds."""
        self.assertAlmostEqual(vtt_timestamp_to_seconds("01:30.000"), 90.0)

    def test_zero(self):
        """Zero timestamp returns 0.0."""
        self.assertAlmostEqual(vtt_timestamp_to_seconds("00:00:00.000"), 0.0)


class TestDeduplicate(unittest.TestCase):
    """Test consecutive duplicate line removal."""

    def test_removes_consecutive(self):
        """Two identical consecutive entries collapse to one."""
        entries = [(0.0, "Hello world"), (1.0, "Hello world"), (2.0, "Next line")]
        result = deduplicate(entries)
        self.assertEqual(len(result), 2, msg="dedup: expected 2 entries, got " + str(len(result)))
        self.assertEqual(result[1][1], "Next line")

    def test_case_insensitive(self):
        """Case differences are ignored during dedup."""
        entries = [(0.0, "Hello World"), (1.0, "hello world")]
        result = deduplicate(entries)
        self.assertEqual(len(result), 1, msg="case-insensitive dedup failed")

    def test_non_consecutive_kept(self):
        """Non-consecutive identical lines are both kept."""
        entries = [(0.0, "Line A"), (1.0, "Line B"), (2.0, "Line A")]
        result = deduplicate(entries)
        self.assertEqual(len(result), 3, msg="non-consecutive dedup should keep both")


class TestGroupIntoBlocks(unittest.TestCase):
    """Test 30-second block grouping."""

    def test_single_block(self):
        """Entries within one interval form one block."""
        entries = [(0.0, "A"), (10.0, "B"), (20.0, "C")]
        result = group_into_blocks(entries, interval=30)
        self.assertEqual(len(result), 1, msg="single block expected")

    def test_two_blocks(self):
        """Entries spanning two intervals form two blocks."""
        entries = [(0.0, "A"), (31.0, "B")]
        result = group_into_blocks(entries, interval=30)
        self.assertEqual(len(result), 2, msg="two blocks expected")

    def test_empty_input(self):
        """Empty input returns empty list."""
        self.assertEqual(group_into_blocks([]), [], msg="empty input should return []")


class TestParseVtt(unittest.TestCase):
    """Test VTT file parsing with a temp file."""

    def test_basic_vtt(self):
        """Parsing a minimal VTT file returns correct entries."""
        vtt_content = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\n"
            "Hello world\n\n"
            "00:00:02.000 --> 00:00:04.000\n"
            "Second line\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vtt", delete=False, encoding="utf-8"
        ) as f:
            f.write(vtt_content)
            tmp = Path(f.name)
        try:
            entries = parse_vtt(tmp)
            self.assertGreater(len(entries), 0, msg="should have at least one entry")
            self.assertEqual(entries[0][1], "Hello world", msg="first entry text mismatch")
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
''')

# ---------------------------------------------------------------------------
# tests/test_chunker.py
# ---------------------------------------------------------------------------
write_and_verify("tests/test_chunker.py", r'''"""Tests for chunker.py — split logic with mocked Ollama token counter."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from chunker import split_into_chunks


def _mock_count(text: str) -> int:
    """Mock token counter: approximate 1 token per word."""
    return len(text.split())


class TestSplitIntoChunks(unittest.TestCase):
    """Test chunk splitting with mocked count_tokens."""

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_short_text_single_chunk(self, _):
        """Text smaller than CHUNK_SIZE produces exactly one chunk."""
        text = "word " * 50
        chunks = split_into_chunks(text.strip(), "src")
        self.assertEqual(len(chunks), 1, msg="50 words should fit in one chunk")

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_chunk_id_prefix(self, _):
        """Chunk IDs start with source_id prefix."""
        text = "word " * 50
        chunks = split_into_chunks(text.strip(), "mysrc")
        self.assertTrue(
            chunks[0]["chunk_id"].startswith("mysrc"),
            msg="chunk_id should start with source_id",
        )

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_empty_text_returns_empty(self, _):
        """Empty text input returns empty list."""
        chunks = split_into_chunks("", "src")
        self.assertEqual(chunks, [], msg="empty text should return []")

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_chunk_has_required_fields(self, _):
        """Each chunk dict contains all required fields."""
        text = "word " * 30
        chunks = split_into_chunks(text.strip(), "src")
        required = {"chunk_id", "source_id", "chunk_index", "token_count", "text"}
        for chunk in chunks:
            for field in required:
                self.assertIn(field, chunk, msg="missing field: " + field)


if __name__ == "__main__":
    unittest.main(verbosity=2)
''')

# ---------------------------------------------------------------------------
# tests/test_analyzer.py
# ---------------------------------------------------------------------------
write_and_verify("tests/test_analyzer.py", r'''"""Tests for analyzer.py — response parser, strip_thinking, keyword filter."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer import (
    extract_query_keywords,
    keyword_prefilter,
    parse_response,
    strip_thinking,
)


class TestStripThinking(unittest.TestCase):
    """Test <think>...</think> block removal."""

    def test_removes_single_line_think_block(self):
        """Single-line think block is stripped, leaving the rest."""
        text = "<think>reasoning</think>\nFOUND: yes\nQUOTE: relevant text"
        result = strip_thinking(text)
        self.assertNotIn("<think>", result, msg="<think> tag should be gone")
        self.assertIn("FOUND: yes", result, msg="FOUND line should remain")

    def test_removes_multiline_think_block(self):
        """Multiline think block is stripped completely."""
        text = "<think>\nline1\nline2\n</think>\nFOUND: no"
        result = strip_thinking(text)
        self.assertNotIn("line1", result, msg="think content should be gone")
        self.assertIn("FOUND: no", result, msg="FOUND line should remain")

    def test_no_think_block_unchanged(self):
        """Text without think block is returned unchanged."""
        text = "FOUND: yes\nQUOTE: something"
        self.assertEqual(strip_thinking(text), text, msg="unchanged when no think block")


class TestParseResponse(unittest.TestCase):
    """Test FOUND/QUOTE field parsing with fallbacks."""

    def test_found_yes(self):
        """FOUND: yes → found=True with correct quote."""
        result = parse_response("FOUND: yes\nQUOTE: relevant text")
        self.assertTrue(result["found"], msg="found should be True")
        self.assertEqual(result["quote"], "relevant text", msg="quote mismatch")

    def test_found_no(self):
        """FOUND: no → found=False."""
        result = parse_response("FOUND: no\nQUOTE: none")
        self.assertFalse(result["found"], msg="found should be False")

    def test_missing_found_defaults_no(self):
        """Missing FOUND field defaults to found=False."""
        result = parse_response("some random text without fields")
        self.assertFalse(result["found"], msg="missing FOUND should default to False")

    def test_missing_quote_defaults_none(self):
        """Missing QUOTE field defaults to quote=none."""
        result = parse_response("FOUND: yes")
        self.assertEqual(result["quote"], "none", msg="missing QUOTE should default to none")


class TestKeywordFilter(unittest.TestCase):
    """Test query keyword extraction and pre-filter."""

    def test_removes_stop_words(self):
        """Stop words are excluded from extracted keywords."""
        keywords = extract_query_keywords("the best way to learn Python")
        self.assertIn("best", keywords, msg="content word should be included")
        self.assertIn("python", keywords, msg="content word should be included")
        self.assertNotIn("the", keywords, msg="stop word should be excluded")
        self.assertNotIn("to", keywords, msg="stop word should be excluded")

    def test_keyword_present_returns_true(self):
        """Text containing a keyword passes the filter."""
        self.assertTrue(
            keyword_prefilter("Python is great for ML", ["python"]),
            msg="keyword present should return True",
        )

    def test_keyword_absent_returns_false(self):
        """Text without any keyword fails the filter."""
        self.assertFalse(
            keyword_prefilter("Today is a sunny day", ["python"]),
            msg="keyword absent should return False",
        )

    def test_empty_keywords_always_passes(self):
        """Empty keyword list passes all text."""
        self.assertTrue(
            keyword_prefilter("anything at all", []),
            msg="empty keywords should always return True",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
''')

# ---------------------------------------------------------------------------
# tests/test_reporter.py
# ---------------------------------------------------------------------------
write_and_verify("tests/test_reporter.py", r'''"""Tests for reporter.py — slug generation and sort order."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reporter import make_slug


class TestMakeSlug(unittest.TestCase):
    """Test query slug generation for report filenames."""

    def test_basic_slug(self):
        """Simple query produces hyphenated lowercase slug."""
        self.assertEqual(
            make_slug("XGBoost feature selection"),
            "xgboost-feature-selection",
            msg="basic slug mismatch",
        )

    def test_special_chars_removed(self):
        """Special characters are stripped from slug."""
        result = make_slug("Hello, World! (test)")
        self.assertNotIn(",", result, msg="comma should be removed")
        self.assertNotIn("!", result, msg="exclamation should be removed")
        self.assertNotIn("(", result, msg="parenthesis should be removed")

    def test_truncated_to_max_len(self):
        """Slug is truncated at max_len characters."""
        result = make_slug("word " * 20, max_len=50)
        self.assertLessEqual(len(result), 50, msg="slug should not exceed max_len")

    def test_all_lowercase(self):
        """Slug is fully lowercased."""
        result = make_slug("UPPER CASE QUERY")
        self.assertEqual(result, result.lower(), msg="slug should be lowercase")

    def test_spaces_become_hyphens(self):
        """Word spaces become hyphens in the slug."""
        result = make_slug("multiple word query")
        self.assertIn("-", result, msg="should contain hyphens")
        self.assertNotIn(" ", result, msg="should not contain spaces")


if __name__ == "__main__":
    unittest.main(verbosity=2)
''')

# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------
print()
print("=" * 60)
if ERRORS:
    print("BUILD FAILED — " + str(len(ERRORS)) + " file(s) with errors:")
    for e in ERRORS:
        print("  FAIL: " + e)
    sys.exit(1)
else:
    print("BUILD OK — all files written and verified")
    print()
    print("Setup:")
    print("  cd into project directory")
    print("  pip install -r requirements.txt")
    print("  cp .env.example .env   (edit OUTPUT_PATH if needed)")
    print()
    print("Run full pipeline:")
    print("  python main.py <youtube_url> --query \"your query\"")
    print()
    print("Run stage by stage:")
    print("  python main.py <url> --stage fetch")
    print("  python main.py --stage clean")
    print("  python main.py --stage chunk")
    print("  python main.py --stage analyze --query \"your query\"")
    print("  python main.py --stage report  --query \"your query\"")
    print()
    print("Run tests:")
    print("  python -m pytest tests/ -v")
    print("=" * 60)

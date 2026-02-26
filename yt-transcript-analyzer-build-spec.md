# YT Transcript Analyzer — Full Build Specification

**Filename:** `yt-transcript-analyzer-build-spec.md`
**Save location:** `C:\Users\User\Documents\Obsidian Vault\`
**Created:** 2026-02-20
**Status:** Approved for Claude Code

---

## Project Overview

Extracts transcripts from a YouTube channel, cleans and timestamps them, runs local multi-model AI analysis via Ollama, and outputs a structured Obsidian markdown report. Zero cost. Fully local inference. No data leaves the machine.

---

## Stack

| Component | Tool | Purpose |
|---|---|---|
| Transcript extraction | `yt-dlp` | Pull subtitles only, no video |
| VTT parsing | `webvtt-py` | Clean and timestamp transcripts |
| Token counting | `tiktoken` | Accurate chunk splitting |
| HTTP client | `requests` | Ollama REST API calls |
| Env management | `python-dotenv` | Secrets handling |
| Primary model | `qwen3:8b` | Analysis pass |
| Reasoning model | `deepseek-r1:8b` | Cross-validation pass |
| Inference server | Ollama local | `http://localhost:11434` |
| Output | Obsidian `.md` | Report with deeplinks |

---

## Hardware Context

- **Machine:** Windows 11 Desktop
- **GPU:** RTX 3060 12GB VRAM
- **Model VRAM usage:** ~5-6GB per 8B model at 4-bit quant
- **Strategy:** Sequential model loading — Qwen finishes before DeepSeek loads
- **VRAM headroom:** Comfortable. No conflicts expected.

---

## Repository Structure

```
yt-transcript-analyzer/
├── .env                          ← secrets (gitignored)
├── .gitignore
├── config.py                     ← all settings
├── requirements.txt
├── main.py                       ← entry point
├── modules/
│   ├── __init__.py
│   ├── startup.py                ← dependency + environment checks
│   ├── fetcher.py                ← yt-dlp transcript pull
│   ├── cleaner.py                ← VTT parsing, timestamps, dedup
│   ├── chunker.py                ← token-safe chunk splitting
│   ├── analyzer.py               ← Ollama inference engine
│   └── reporter.py               ← Obsidian report builder
├── data/
│   ├── archive.txt               ← yt-dlp checkpoint (gitignored)
│   ├── skipped.txt               ← unavailable videos log (gitignored)
│   └── manifest.json             ← video metadata index (gitignored)
└── output/                       ← reports (gitignored)
```

---

## `.gitignore`

```gitignore
.env
data/archive.txt
data/skipped.txt
data/manifest.json
output/
__pycache__/
*.pyc
*.vtt
raw/
clean/
```

---

## `requirements.txt`

```
yt-dlp
webvtt-py
requests
python-dotenv
tiktoken
```

---

## `.env` (template — never commit)

```env
# Placeholder for future API keys
# Currently unused — all inference is local via Ollama
ANTHROPIC_API_KEY=
```

---

## `config.py`

```python
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
VAULT_PATH   = Path(r"C:\Users\User\Documents\Obsidian Vault")
OUTPUT_PATH  = VAULT_PATH / "07-RESEARCH" / "youtube-transcripts"
RAW_PATH     = OUTPUT_PATH / "raw"
CLEAN_PATH   = OUTPUT_PATH / "clean"
LOG_PATH     = VAULT_PATH  / "06-CLAUDE-LOGS"

# ── yt-dlp settings ───────────────────────────────────────────────────────────
LANGUAGE          = "en"       # TODO: expand language support later
SLEEP_MIN         = 4          # seconds between videos
SLEEP_MAX         = 10         # max jitter
SLEEP_REQUESTS    = 2          # seconds between metadata API page requests
SLEEP_SUBTITLES   = 5          # seconds between subtitle file downloads
RETRIES           = 10         # retry attempts per failed request
USE_COOKIES       = False      # toggle True for private/unlisted videos
BROWSER           = "chrome"   # browser to pull cookies from if USE_COOKIES=True

# ── Ollama models ─────────────────────────────────────────────────────────────
QWEN_MODEL        = "qwen3:8b"
DEEPSEEK_MODEL    = "deepseek-r1:8b"
OLLAMA_BASE_URL   = "http://localhost:11434"
OLLAMA_TIMEOUT    = 120        # seconds per inference call

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE        = 3000       # tokens per chunk
CHUNK_OVERLAP     = 150        # token overlap between chunks for context continuity

# ── Confidence thresholds ─────────────────────────────────────────────────────
CONFIDENCE_HIGH   = "HIGH"     # both models flagged the passage
CONFIDENCE_LOW    = "LOW"      # only one model flagged the passage

# ── Visual reference trigger keywords ─────────────────────────────────────────
VISUAL_TRIGGERS = [
    "as you can see",
    "this chart",
    "this diagram",
    "on screen",
    "this graph",
    "look at this",
    "shown here",
    "in this image",
    "this table",
    "you'll notice",
    "highlighted here",
    "this code",
    "this slide",
    "over here",
    "right here",
    "this figure",
    "you can see here",
    "i'm showing",
    "on the screen",
]
```

---

## `modules/startup.py`

### Responsibilities

1. Check `yt-dlp` is installed via `subprocess`. If missing, run `pip install yt-dlp` automatically.
2. Ping `http://localhost:11434` — if Ollama is not responding, print clear error message and exit. Do not proceed.
3. Run `ollama list` via subprocess. Parse output to verify `qwen3:8b` and `deepseek-r1:8b` are present. If either is missing, print the exact `ollama pull <model>` command needed and exit.
4. Run `nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits` to check available VRAM. Log result. Warn if under 6000MB.
5. Create all output directories if they do not exist using `pathlib.Path.mkdir(parents=True, exist_ok=True)`.
6. Print startup summary table: yt-dlp version, models confirmed, VRAM available, output paths.

### Error exits

| Condition | Message | Action |
|---|---|---|
| Ollama not running | `Ollama not running. Start with: ollama serve` | Exit |
| Model missing | `Model qwen3:8b not found. Run: ollama pull qwen3:8b` | Exit |
| VRAM under 6GB | `Warning: Low VRAM ({n}MB). Performance may degrade.` | Warn, continue |

---

## `modules/fetcher.py`

### Responsibilities

1. Accept channel URL as parameter from `main.py`.
2. Derive channel name from URL for folder naming.
3. Build yt-dlp command as a Python list (never a shell string).
4. Execute via `subprocess.run()` — never `os.system()`.
5. Parse stderr line by line for error classification.
6. Write successful video metadata to `manifest.json` after each video.
7. Support full resume — `archive.txt` checkpoint means re-running skips already completed videos.

### yt-dlp command flags

```
--skip-download
--write-auto-subs
--write-subs
--sub-langs en
--sub-format vtt
--sleep-interval 4
--max-sleep-interval 10
--sleep-requests 2
--sleep-subtitles 5
--retries 10
--retry-sleep exp=1
--ignore-errors
--no-overwrites
--download-archive data/archive.txt
--output raw/%(upload_date)s-%(id)s-%(title)s.%(ext)s
```

### Error handling matrix

| Error | Detection | Handler |
|---|---|---|
| HTTP 429 rate limit | stderr contains `429` | Sleep 60 minutes, log, retry |
| Bot detection | stderr contains `sign in` | Log warning, skip video |
| Video unavailable | stderr contains `unavailable` | Write to `skipped.txt`, continue |
| Private/unlisted | stderr contains `private` | Write to `skipped.txt`, continue |
| No subtitles | stderr contains `no subtitles` | Write to `skipped.txt`, continue |
| Network timeout | stderr contains `timed out` | Retry up to `RETRIES` with exponential backoff |
| General error | any other non-zero exit | Log full stderr, skip video, continue |

### `skipped.txt` format

```
VIDEO_ID | TITLE | REASON | DATE
xxxxx    | Video Title Here | no subtitles | 2026-02-20
```

### `manifest.json` entry format

```json
{
  "video_id": "xxxxx",
  "title": "Episode 47 - XGBoost Deep Dive",
  "url": "https://youtube.com/watch?v=xxxxx",
  "upload_date": "2024-03-15",
  "duration_seconds": 2537,
  "vtt_file": "raw/20240315-xxxxx-Episode-47.en.vtt",
  "fetched_at": "2026-02-20T14:32:00"
}
```

---

## `modules/cleaner.py`

### Responsibilities

1. Read all `.vtt` files from `raw/` that do not yet have a corresponding entry in `clean/`.
2. Parse with `webvtt-py`.
3. Deduplicate consecutive repeated lines (auto-generated caption artifact).
4. Produce two output files per video in `clean/`.

### Output 1 — `<video_id>-timestamped.txt`

Every caption line preserved with original VTT timestamp. Used for backtrace.

```
TITLE: Episode 47 - XGBoost Deep Dive
DATE: 2024-03-15
URL: https://youtube.com/watch?v=xxxxx
DURATION: 00:42:17
---
[00:14:32] as you can see in this chart the feature importance ranking
[00:14:35] shows XGBoost outperforming random forest by a significant margin
[00:14:39] the key insight here is that the depth parameter
```

### Output 2 — `<video_id>-clean.txt`

Prose paragraphs grouped by 30-second blocks. Each block tagged with start timestamp. Used for Ollama analysis.

```
TITLE: Episode 47 - XGBoost Deep Dive
DATE: 2024-03-15
URL: https://youtube.com/watch?v=xxxxx
DURATION: 00:42:17
---
[T:00:14:30] As you can see in this chart, the feature importance ranking 
shows XGBoost outperforming random forest by a significant margin. The key 
insight here is that the depth parameter controls how the model generalises 
across unseen data points.

[T:00:15:00] Now moving on to the training loop, we set the learning rate 
to 0.05 which in practice means...
```

### Timestamp to seconds helper

Every `[T:HH:MM:SS]` tag must also store the equivalent seconds integer internally for YouTube deeplink generation: `&t=<seconds>`.

---

## `modules/chunker.py`

### Responsibilities

1. Read each `<video_id>-clean.txt` from `clean/`.
2. Count tokens using `tiktoken` with `cl100k_base` encoding.
3. Split into chunks of `CHUNK_SIZE` tokens with `CHUNK_OVERLAP` token overlap.
4. Each chunk stored as a dict and written to `manifest.json`.

### Chunk dict structure

```python
{
    "video_id": "xxxxx",
    "title": "Episode 47 - XGBoost Deep Dive",
    "url": "https://youtube.com/watch?v=xxxxx",
    "upload_date": "2024-03-15",
    "chunk_index": 0,
    "total_chunks": 3,
    "timestamp_start": "00:14:30",
    "timestamp_start_seconds": 870,
    "youtube_deeplink": "https://youtube.com/watch?v=xxxxx&t=870",
    "text": "chunk text content..."
}
```

---

## `modules/analyzer.py`

### Responsibilities

1. Accept user query as parameter from `main.py`.
2. Run keyword pre-filter on all `clean.txt` files. Only files containing query-related terms pass to Ollama.
3. For each matched video, send chunks sequentially to Qwen3:8b then DeepSeek-r1:8b.
4. Collect structured findings per chunk per model.
5. Assign confidence based on model agreement.
6. Flag visual references using `VISUAL_TRIGGERS` list from `config.py`.

### Ollama API call

```python
import requests

def call_ollama(model: str, prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        },
        timeout=OLLAMA_TIMEOUT
    )
    response.raise_for_status()
    return response.json()["response"]
```

### System prompt (same for both models)

```
You are a research analyst extracting specific information from video transcripts.

The user is looking for: {query}

Instructions:
- Read the transcript chunk carefully
- Determine if the query topic is present
- If found, extract the most relevant quote verbatim
- Note the timestamp tag [T:HH:MM:SS] nearest to the quote
- Flag if the speaker appears to be referencing on-screen visual content
- Respond in the exact structured format below, nothing else

Response format:
FOUND: yes or no
QUOTE: exact words from transcript or none
TIMESTAMP_TAG: [T:HH:MM:SS] or none
VISUAL: yes or no
SUMMARY: one sentence description of what was found or none

Transcript chunk from: {title}
Chunk {chunk_index} of {total_chunks} | Start: {timestamp_start}

{chunk_text}
```

### Confidence logic

```python
qwen_found     = qwen_result["FOUND"] == "yes"
deepseek_found = deepseek_result["FOUND"] == "yes"

if qwen_found and deepseek_found:
    confidence = CONFIDENCE_HIGH
elif qwen_found or deepseek_found:
    confidence = CONFIDENCE_LOW
else:
    continue  # discard — neither model found anything
```

### Finding dict structure

```python
{
    "video_id": "xxxxx",
    "title": "Episode 47 - XGBoost Deep Dive",
    "url": "https://youtube.com/watch?v=xxxxx",
    "upload_date": "2024-03-15",
    "chunk_index": 0,
    "timestamp_tag": "[T:00:14:30]",
    "youtube_deeplink": "https://youtube.com/watch?v=xxxxx&t=870",
    "quote": "the feature importance ranking shows XGBoost outperforming...",
    "summary": "Speaker explains SHAP value interpretation vs random forest",
    "visual_reference": True,
    "confidence": "HIGH",
    "qwen_found": True,
    "deepseek_found": True
}
```

---

## `modules/reporter.py`

### Responsibilities

1. Receive merged findings list from `analyzer.py`.
2. Sort: HIGH confidence first, then by upload date descending.
3. Build Obsidian markdown report.
4. Save to vault path with sanitised query slug in filename.

### Report filename format

```
C:\Users\User\Documents\Obsidian Vault\07-RESEARCH\youtube-transcripts\<channel-name>\analysis-YYYY-MM-DD-<query-slug>.md
```

### Report template

```markdown
# YouTube Transcript Analysis

| Field | Value |
|---|---|
| Query | {query} |
| Channel | {channel_name} |
| Channel URL | {channel_url} |
| Date run | {date} |
| Videos in channel | {total_videos} |
| Videos matched (keyword filter) | {matched_videos} |
| Videos skipped (no subs / unavailable) | {skipped_count} |
| High confidence findings | {high_count} |
| Low confidence findings | {low_count} |

---

## High Confidence Findings
*Both models agree — reliable*

### [{title}]({url})
📅 {upload_date} | ⏱ [{timestamp_tag}]({youtube_deeplink})

**Quote:** "{quote}"
**Summary:** {summary}
🖼 **Visual reference** — speaker referencing on-screen content. Watch from this timestamp.

---

## Low Confidence Findings
*One model flagged — review manually*

### [{title}]({url})
📅 {upload_date} | ⏱ [{timestamp_tag}]({youtube_deeplink})

**Quote:** "{quote}"
**Summary:** {summary}

---

## Skipped Videos

| Video ID | Title | Reason |
|---|---|---|
| {video_id} | {title} | {reason} |

---

## Run Log

- Keyword pre-filter removed: {filtered_count} videos
- Total Ollama calls made: {ollama_call_count}
- Total analysis time: {duration}
- Models used: {QWEN_MODEL}, {DEEPSEEK_MODEL}
```

---

## `main.py` — Entry Point

### Execution flow

```
1.  startup.py  → check yt-dlp, Ollama, models, VRAM, create folders
2.  Input       → channel URL (CLI prompt)
3.  Input       → search query (CLI prompt)
4.  fetcher.py  → pull all subtitles, checkpoint resume via archive.txt
5.  cleaner.py  → parse VTT, produce timestamped.txt and clean.txt
6.  chunker.py  → split into token-safe chunks, update manifest.json
7.  analyzer.py → keyword pre-filter → Qwen pass → DeepSeek pass → merge
8.  reporter.py → build Obsidian report, save to vault
9.  Print       → "Report saved to: {path}"
```

### CLI interface

```
================================================
  YT Transcript Analyzer
================================================
  Models   : qwen3:8b | deepseek-r1:8b
  Ollama   : running
  VRAM     : 11842 MB available
================================================

Enter YouTube channel URL: https://youtube.com/@channelname
Enter search query: XGBoost feature selection method

Fetching transcripts... (resume enabled)
[1/210] Downloading subtitles: Episode 47 - XGBoost Deep Dive
[2/210] Already downloaded — skipping
...
Cleaning transcripts...
Chunking transcripts...
Running keyword pre-filter... 34 of 210 videos matched
Running Qwen3:8b analysis...
Running DeepSeek-r1:8b analysis...
Merging findings...
Building report...

Report saved to:
C:\Users\User\Documents\Obsidian Vault\07-RESEARCH\youtube-transcripts\channelname\analysis-2026-02-20-xgboost-feature-selection.md

High confidence findings : 12
Low confidence findings  : 8
Visual references flagged: 4
```

---

## Upgrade Path Notes

The following are noted as future enhancements. Do not build now.

- `LANGUAGE = "en"` → expand to multi-language subtitle support
- Single channel → multi-channel batch support
- Ollama local → optional Claude API fallback for higher accuracy
- CLI → simple Streamlit UI for query input and report viewing
- Cookie support for private/unlisted videos → toggle `USE_COOKIES = True` in config

---

## Pre-Run Checklist (for first run)

```powershell
# 1. Confirm Ollama is running
ollama serve

# 2. Confirm models are available
ollama list

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Verify yt-dlp version
yt-dlp --version

# 5. Run
python main.py
```

---

*Spec version: 1.0 | Built for Claude Code / VS Code on Windows 11*

# YT Transcript Analyzer — Build Spec v2

**Date:** 2026-02-20
**Status:** Approved for build
**Architecture change from v1:** Single model only (`qwen3:8b`). DeepSeek dropped entirely.

---

## Overview

A local-inference pipeline that downloads YouTube channel subtitles, cleans and chunks them, analyzes each chunk against a user query using `qwen3:8b` via Ollama, and outputs findings as an Obsidian markdown report.

**All inference is local. No cloud APIs. No data leaves the machine.**

---

## Architecture

```
Channel URL
    ↓
[fetcher.py]  yt-dlp → VTT files → manifest_videos.json
    ↓
[cleaner.py]  VTT → deduplicated 30-sec block plain text
    ↓
[chunker.py]  text → overlapping token-counted chunks → manifest_chunks.json
    ↓
[analyzer.py] qwen3:8b (Ollama) → FOUND/QUOTE per chunk → findings/
    ↓
[reporter.py] findings → Obsidian markdown report
```

**Model:** `qwen3:8b` (thinking mode enabled — `<think>` blocks stripped before parsing)
**Tokenizer:** Ollama `/api/tokenize` endpoint (exact, matches inference tokenizer)
**Confidence:** FOUND=yes → include. FOUND=no → discard.

---

## Project Structure

```
yt-transcript-analyzer/
├── config.py                   ← all constants and paths
├── startup.py                  ← dependency checks (no auto-install)
├── fetcher.py                  ← yt-dlp wrapper + URL normalization
├── cleaner.py                  ← VTT → clean text
├── chunker.py                  ← token-counted chunking via Ollama tokenize
├── analyzer.py                 ← qwen3:8b inference + response parsing
├── reporter.py                 ← Obsidian markdown report generation
├── main.py                     ← pipeline orchestrator (argparse)
├── requirements.txt
├── .env.example
└── tests/
    ├── test_cleaner.py
    ├── test_chunker.py
    ├── test_analyzer.py
    └── test_reporter.py
```

**Output directories** (created at runtime under `OUTPUT_PATH`):
```
output/
├── data/
│   ├── archive.txt             ← yt-dlp download archive
│   ├── skipped.txt             ← failed downloads
│   ├── manifest_videos.json    ← pre-scan metadata (fetcher writes)
│   ├── manifest_chunks.json    ← chunk index (chunker writes)
│   └── pipeline.log
├── raw/                        ← VTT files from yt-dlp
├── clean/                      ← cleaned .txt files
├── chunks/                     ← per-chunk .txt files
├── findings/                   ← per-chunk finding .json files
└── reports/                    ← final Obsidian .md reports
```

---

## Configuration (`config.py`)

All constants. Override `OUTPUT_PATH` and `OLLAMA_BASE_URL` via `.env` file.

```python
OLLAMA_BASE_URL       = "http://localhost:11434"
QWEN_MODEL            = "qwen3:8b"
QWEN_THINKING         = True               # thinking mode enabled
CHUNK_TOKENIZER_MODEL = "qwen3:8b"
OLLAMA_RETRIES        = 2
OLLAMA_TIMEOUT        = 120                # seconds

CHUNK_SIZE    = 2500   # tokens (safety margin via Ollama tokenizer)
CHUNK_OVERLAP = 200    # tokens (used as approximate word count)

BLOCK_INTERVAL_SECONDS = 30
YTDLP_RETRIES          = 10
```

---

## Module Specs

### `fetcher.py`

- `extract_channel_name(url)` — handles all 4 YouTube URL formats:
  - `/@handle` — split on `/@`
  - `/c/name` and `/user/name` — legacy formats
  - `/channel/UCxxxxxxx` — runs yt-dlp `--flat-playlist --dump-json` to get `channel`/`uploader` field
- `prescan_channel(url)` — flat-playlist pre-scan for title/id/duration metadata
- `fetch_subtitles(url)` — yt-dlp with absolute paths (C3 fix), `--write-auto-sub --sub-lang en --sub-format vtt`
- Writes `manifest_videos.json` from pre-scan data
- No outer 429 handler — trusts yt-dlp's `--retries 10 --retry-sleep exp=1` (M3 fix)

### `cleaner.py`

- `parse_vtt(path)` — reads VTT, strips inline tags (`<c>`, timestamps), returns `[(seconds, text)]`
- `deduplicate(entries)` — removes consecutive duplicates by exact match on stripped lowercase (M1 fix)
- `group_into_blocks(entries, interval=30)` — groups into `BLOCK_INTERVAL_SECONDS` time windows
- `clean_all()` — processes all `*.vtt` files in `RAW_PATH`

### `chunker.py`

- `count_tokens(text)` — `POST /api/tokenize` to Ollama, returns `len(tokens)` (H3 fix, no tiktoken)
- `split_into_chunks(text, source_id)` — binary search per chunk to fit `CHUNK_SIZE` tokens, then steps back `CHUNK_OVERLAP` words for overlap
- `chunk_all()` — chunks all clean files, writes chunk `.txt` files and `manifest_chunks.json`

### `analyzer.py`

- `strip_thinking(text)` — `re.sub(r"<think>.*?</think>", "", text, re.DOTALL)` (C1/H4 fix)
- `extract_query_keywords(query)` — tokenizes, removes stop words (H2 fix)
- `keyword_prefilter(text, keywords)` — any keyword in text? (case-insensitive). Skips chunk if no match.
- `call_ollama(model, prompt)` — POST `/api/generate`, retry `OLLAMA_RETRIES` times with backoff (M5 fix)
- `parse_response(raw)` — regex `FOUND:` / `QUOTE:` with fallbacks: missing FOUND → no, missing QUOTE → none (C5 fix)
- `analyze_all(query)` — iterates all chunks from manifest, writes finding JSONs to `FINDINGS_PATH`

### `reporter.py`

- `make_slug(query, max_len=50)` — lowercase, remove non-alphanumeric, spaces to hyphens (L4 fix)
- `load_findings()` — reads all `*.json` from `FINDINGS_PATH`, sorts by `(source_id, chunk_index)`
- `generate_report(query)` — Obsidian markdown with channel name, query, date, finding list

### `startup.py`

- Checks: yt-dlp binary, webvtt-py, requests, python-dotenv (importlib), Ollama reachable (urllib)
- **No auto-pip-install** — prints `pip install <package>` and continues (M4 fix)
- Uses `urllib.request` for Ollama check (not `requests`, avoids catch-22 if requests missing)

### `main.py`

- `argparse`: positional `url`, `--query/-q`, `--stage [fetch|clean|chunk|analyze|report|all]`
- Calls `ensure_dirs()` before `setup_logging()` (log file needs DATA_PATH to exist)
- Calls `startup.run_checks()` — prints issues but does not hard-exit on Ollama warning

---

## Response Format (prompt to model)

```
You are a research assistant analyzing a YouTube transcript excerpt.
Determine if the excerpt contains information relevant to the query.

QUERY: <query>

TRANSCRIPT EXCERPT:
<chunk_text>

Respond in EXACTLY this format (two lines, nothing else):
FOUND: yes or no
QUOTE: <one brief relevant quote from the text, or 'none' if not found>
```

Thinking blocks from qwen3:8b (wrapped in `<think>...</think>`) are stripped before parsing.

---

## Requirements

```
yt-dlp
webvtt-py
requests
python-dotenv
```

No tiktoken. No transformers. No heavy ML deps.

---

## Usage

```bash
# Full pipeline
python main.py https://youtube.com/@channelname --query "XGBoost feature selection"

# Stage by stage
python main.py https://youtube.com/@channelname --stage fetch
python main.py --stage clean
python main.py --stage chunk
python main.py --stage analyze --query "XGBoost feature selection"
python main.py --stage report  --query "XGBoost feature selection"

# Tests
python -m pytest tests/
```

---

## Audit Fixes Applied

| ID | Fix |
|---|---|
| C1/H4 | `strip_thinking()` strips `<think>` blocks (qwen3 thinking mode) |
| C2 | Dropped — single model, no VRAM contention |
| C3 | Absolute paths via `config.py` Path constants |
| C4 | Split manifest: `manifest_videos.json` + `manifest_chunks.json` |
| C5 | Regex parser with per-field fallbacks |
| H1 | URL normalization for all 4 YouTube URL formats |
| H2 | Stop-word tokenization for keyword pre-filter |
| H3 | Ollama `/api/tokenize` replaces tiktoken |
| H5 | `prescan_channel()` pre-scan for progress metadata |
| H6 | `BLOCK_INTERVAL_SECONDS = 30` in config |
| M1 | Exact-match dedup on stripped lowercase |
| M3 | Outer 429 handler removed, trust yt-dlp retry |
| M4 | No auto-pip-install, print install command |
| M5 | `OLLAMA_RETRIES = 2`, exponential backoff |
| M6 | `logging` module throughout, not print |
| L1 | `tests/` with 4 test files |
| L2 | `build_yt_transcript_analyzer.py` build script |
| L3 | All PATH constants + BLOCK_INTERVAL in config |
| L4 | `make_slug()` defined in reporter.py |

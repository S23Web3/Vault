# Session Log — YouTube Transcript Analyzer Build
**Date:** 2026-02-20
**Topic:** YouTube channel transcript extraction + local AI analysis system
**Status:** Spec complete, approved for Claude Code

---

## Session Summary

Full build specification designed for a YouTube channel transcript analyzer. Goal: extract transcripts from 210 videos, analyze with local Ollama models, output structured Obsidian report with timestamped deeplinks.

---

## Decisions Made

### Extraction Tool
- **yt-dlp** selected — no YouTube Data API v3, no quota limits, no cost
- Subtitles only — `--skip-download` flag, no video files downloaded
- **cobalt.tools** evaluated and ruled out — video/audio download only, no transcript capability

### Models (Ollama — fully local, zero cost)
- **qwen3:8b** — primary analysis pass
- **deepseek-r1:8b** — reasoning / cross-validation pass
- GPT-oss-20b was considered then dropped in favour of two 8B models
- Sequential loading on RTX 3060 12GB — no VRAM conflicts
- Auto-selection by VRAM fit built into startup.py

### Rate Limiting Strategy
- `--sleep-interval 4 --max-sleep-interval 10` — random jitter between videos
- `--sleep-requests 2` — delay between YouTube metadata API page requests
- `--sleep-subtitles 5` — delay between subtitle file downloads
- HTTP 429 handler: sleep 60 minutes, retry automatically
- Exponential backoff on all retries up to 10 attempts
- `archive.txt` checkpoint — full resume capability on interruption

### Timestamp Strategy
- VTT timestamps preserved in two output formats per video:
  - `<video_id>-timestamped.txt` — every line with `[HH:MM:SS]` tag
  - `<video_id>-clean.txt` — prose paragraphs with `[T:HH:MM:SS]` block tags
- YouTube deeplinks generated: `https://youtube.com/watch?v=xxxxx&t=<seconds>`
- Clickable from Obsidian report — opens video at exact second

### Visual Reference Detection
- Trigger keyword list defined in `config.py`
- Phrases like "as you can see", "this chart", "this diagram", "on screen" etc.
- When detected: passage flagged with 🖼 in report
- Only surfaced in report when trigger keywords present in that passage
- Embedded in main report (not separate file)

### Confidence System
- Both models flag passage → **HIGH confidence**
- One model only → **LOW confidence**
- Neither model → discarded, not in report

### Cost
- **$0** — all inference local via Ollama
- Keyword pre-filter reduces Ollama calls by estimated 60-80% for targeted queries
- Token estimation for reference: 210 videos × ~5,600 tokens = ~1.17M tokens if full sweep

### Privacy / GitHub Safety
- `.env` gitignored
- `archive.txt`, `skipped.txt`, `manifest.json` gitignored
- `output/`, `raw/`, `clean/` gitignored
- No personal data, no API keys in repository

### Language
- English only (`LANGUAGE = "en"`)
- Upgrade path noted in spec: `# TODO: expand language support later`

### Query Interface
- CLI input — user types query at runtime
- Config override available for scheduled/repeatable runs

---

## Files Created This Session

| File | Location |
|---|---|
| `yt-transcript-analyzer-build-spec.md` | `C:\Users\User\Documents\Obsidian Vault\` |
| `2026-02-20-youtube-transcript-analyzer-build.md` | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\` |

---

## Project File Structure (to be built in Claude Code)

```
yt-transcript-analyzer/
├── .env
├── .gitignore
├── config.py
├── requirements.txt
├── main.py
├── modules/
│   ├── __init__.py
│   ├── startup.py
│   ├── fetcher.py
│   ├── cleaner.py
│   ├── chunker.py
│   ├── analyzer.py
│   └── reporter.py
├── data/
│   ├── archive.txt
│   ├── skipped.txt
│   └── manifest.json
└── output/
```

---

## Dependencies

```
yt-dlp
webvtt-py
requests
python-dotenv
tiktoken
```

---

## Upgrade Path (future — do not build now)

- Multi-language subtitle support
- Multi-channel batch support
- Optional Claude API fallback for higher accuracy
- Streamlit UI for query input and report viewing
- Cookie support for private/unlisted videos

---

## Next Step

Take `yt-transcript-analyzer-build-spec.md` into Claude Code / VS Code and build.

---

*Logged by Claude Sonnet 4.6 | Session end: 2026-02-20*

---

## Build Session — 2026-02-20 (Claude Code)

**Timestamp:** 2026-02-20

### Architecture Change Applied
- Dropped DeepSeek entirely — single model `qwen3:8b` only
- Removes VRAM contention (C2), dual-model confidence scoring
- Confidence: FOUND=yes (qwen3:8b) → include. FOUND=no → discard.

### Files Delivered

**Build script** (run this first):
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\build_yt_transcript_analyzer.py`

**Spec v2** (corrected, audit fixes applied):
`C:\Users\User\Documents\Obsidian Vault\yt-transcript-analyzer-build-spec-v2.md`

### Build generates
- `config.py` — all constants, Path-based, .env support
- `startup.py` — dep checks via importlib + urllib (no auto-pip-install)
- `fetcher.py` — all 4 YouTube URL formats, pre-scan, absolute yt-dlp paths
- `cleaner.py` — VTT parse, exact-match dedup, 30-sec block grouping
- `chunker.py` — Ollama /api/tokenize, binary-search chunking, word-overlap
- `analyzer.py` — qwen3:8b, strip_thinking, keyword pre-filter, regex fallback parser
- `reporter.py` — make_slug, Obsidian markdown output
- `main.py` — argparse, stage-by-stage or full pipeline
- `tests/` — 4 test files (cleaner, chunker, analyzer, reporter)

### All audit fixes applied
C1/H4 (think stripping), C2 (dropped), C3 (absolute paths), C4 (split manifest),
C5 (regex fallback parser), H1 (URL normalization), H2 (keyword pre-filter),
H3 (Ollama tokenizer), H5 (pre-scan), H6 (BLOCK_INTERVAL_SECONDS), M1-M6, L1-L4.

### Run commands
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\build_yt_transcript_analyzer.py"
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer"
pip install -r requirements.txt
python main.py <youtube_url> --query "your query"
python -m pytest tests/ -v
```

### Status
BUILD DELIVERED — not yet run by user.

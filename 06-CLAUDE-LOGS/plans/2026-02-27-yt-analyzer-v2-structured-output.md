# YT Transcript Analyzer v2 — Structured Output with Timestamps, Summaries & Tags

**Date:** 2026-02-27
**Purpose:** Transform the raw transcript dump into a structured, navigable, analyzable output with clickable YouTube timestamp links, LLM-generated summaries, and auto-tags.

---

## Context

The v1 drain output is a wall of unstructured text. No timestamps, no summaries, no tags, no clickable links. The data for all of these features already exists in the pipeline — timestamps are parsed from VTTs then discarded, video IDs are in filenames but never used for links, and qwen3:8b is available but only used for query-mode relevance matching.

Additionally: OUTPUT_PATH is relative to CWD (breaks when Streamlit launches from different dirs), and the GUI doesn't explain why only 15/211 videos had subtitles.

---

## Problems to Solve

1. **Timestamps discarded** — `cleaner.py:group_into_blocks()` gets `(seconds, text)` tuples but outputs only text
2. **No clickable links** — YouTube supports `?t=SECONDS`. Video IDs are in filenames. Never assembled.
3. **No summaries** — LLM never summarizes content, only does query-match
4. **No tags/labels** — No topic categorization
5. **Unstructured report** — Just `## video_id` + wall of text. No TOC, no metadata.
6. **Unpredictable output path** — Relative `Path("output")` depends on CWD
7. **15/211 gap unexplained** — GUI doesn't report skipped videos

---

## Files to Modify

| File | Changes |
|------|---------|
| `config.py` | Fix OUTPUT_PATH to absolute (project-relative). Add SUMMARIES_PATH. |
| `cleaner.py` | Preserve timestamps in output. Extract video_id from filename. Write `[MM:SS]` markers. |
| `summarizer.py` | **NEW.** Per-video LLM summary + auto-tags via qwen3:8b. |
| `reporter.py` | Rewrite `generate_full_report()` with TOC, summaries, tags, timestamp links. Update `generate_report()` with timestamp links in findings. |
| `gui.py` | Add Summarize stage. Show download stats (X with subs / Y skipped). Show output path. |
| `fetcher.py` | Track and return subtitle success/skip counts. |

---

## Implementation Steps

### Step 1: Fix OUTPUT_PATH (`config.py`)

Change line 12 from:
```python
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "output"))
```
To:
```python
_DEFAULT_OUTPUT = Path(__file__).parent / "output"
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", str(_DEFAULT_OUTPUT)))
```

Add new constant:
```python
SUMMARIES_PATH = OUTPUT_PATH / "summaries"
```

### Step 2: Timestamp-Preserving Clean (`cleaner.py`)

**Current flow:** `parse_vtt()` -> `(seconds, text)` tuples -> `group_into_blocks()` -> plain text blocks (timestamps lost)

**New flow:** `parse_vtt()` -> `(seconds, text)` tuples -> `group_into_blocks()` -> `(start_seconds, block_text)` tuples (timestamps preserved)

Changes:
- `group_into_blocks()` returns `[(start_seconds, block_text)]` instead of `[block_text]`
- `extract_video_id(filename)` — new function, parses `YYYYMMDD-VIDEOID-Title.en.vtt` -> `VIDEOID`
- `clean_vtt_file()` writes structured output:
  ```
  [00:00] Welcome to this video about machine learning...
  [00:30] Today we'll cover three main topics...
  [01:00] First, let's look at the data preparation step...
  ```
- First line of clean file is a metadata comment: `<!-- video_id:cTJ0Qbz0eAI -->`

**Backward compatibility:** Chunker reads clean `.txt` files as plain text. The `[MM:SS]` markers and metadata comment are just text — chunker works unchanged. The markers add ~6 chars per block (~1% token overhead).

### Step 3: New Summarizer Module (`summarizer.py`)

New file. For each clean transcript, calls qwen3:8b with:
```
Summarize this YouTube video transcript in 2-3 sentences.
Then list 3-5 topic tags that describe the main subjects covered.

TRANSCRIPT:
<first 3000 words of clean text>

Respond in EXACTLY this format:
SUMMARY: <2-3 sentence summary>
TAGS: tag1, tag2, tag3
```

Output per video: `summaries/VIDEO_ID.json`
```json
{
  "video_id": "cTJ0Qbz0eAI",
  "summary": "This video walks through building...",
  "tags": ["machine learning", "python", "backtesting"],
  "summarized_at": "2026-02-27T..."
}
```

Functions:
- `build_summary_prompt(text)` — constructs prompt with truncated transcript
- `parse_summary_response(raw)` — regex SUMMARY: and TAGS: with fallbacks
- `summarize_video(clean_path)` — summarize one video, write JSON
- `summarize_all()` — iterate all clean files, skip already-summarized, return list of summary dicts

### Step 4: Clickable Timestamp Links (`reporter.py`)

**YouTube timestamp URL format:** `https://www.youtube.com/watch?v=VIDEO_ID&t=SECONDS`

Example: `[05:23](https://www.youtube.com/watch?v=cTJ0Qbz0eAI&t=323)` — clickable in Obsidian, Streamlit, and browsers.

**Utility functions (reporter.py):**
- `seconds_to_mmss(secs)` — `323` -> `"05:23"`
- `parse_timestamp_line(line)` — extracts seconds from `[MM:SS]` prefix
- `make_youtube_link(video_id, seconds)` — returns clickable markdown link
- `format_timestamped_block(line, video_id)` — replaces `[MM:SS]` with clickable YouTube link

**`generate_full_report()` rewrite:**
```markdown
# Channel Analysis: CodeTradingCafe
**Videos:** 15 | **Generated:** 2026-02-27 14:30 UTC

---

## Table of Contents

| # | Video | Tags | Summary |
|---|-------|------|---------|
| 1 | [NY Session Strategy Backtest](https://youtube.com/watch?v=cTJ0Qbz0eAI) | backtesting, breakout, python | Walks through a multi-timeframe breakout system... |
| 2 | [MACD and EMA Trend Strategy](https://youtube.com/watch?v=Ik0ILD0gPHA) | macd, ema, algorithmic | Full algorithmic backtest of a MACD... |

---

## 1. NY Session Strategy Backtest in Python
**Tags:** backtesting, breakout, python
**Summary:** Walks through a multi-timeframe breakout system...

[00:00](https://youtube.com/watch?v=cTJ0Qbz0eAI&t=0) Welcome to this video about...
[00:30](https://youtube.com/watch?v=cTJ0Qbz0eAI&t=30) Today we'll cover three main topics...
[05:23](https://youtube.com/watch?v=cTJ0Qbz0eAI&t=323) As you can see on the screen...

---
```

**`generate_report()` update (query mode):**
- Findings include timestamp link to the exact moment the relevant quote came from

### Step 5: Download Stats (`fetcher.py`)

`download_subtitles()` currently parses stdout for progress. Add parsing for:
- `"Writing video subtitles"` — count as success
- `"has no subtitles"` or similar yt-dlp skip messages — count as skipped

Return a dict: `{"downloaded": 15, "skipped": 136, "errors": 0}`

### Step 6: GUI Updates (`gui.py`)

- Show output path in sidebar (absolute)
- After download: "Downloaded 15 subtitle files (136 videos had no English subtitles)"
- New pipeline stages:
  - **Drain mode (4 stages):** Fetch -> Clean -> Summarize -> Report
  - **Query mode (5 stages):** Fetch -> Clean -> Chunk -> Analyze -> Report
- Summarize stage shows: "Summarizing video 3/15 with qwen3:8b..."
- Add `ensure_dirs()` to include SUMMARIES_PATH

---

## Key Design Decisions

1. **Timestamps as `[MM:SS]` text markers** — not separate metadata files. Keeps the clean text human-readable AND machine-parseable. Chunker and analyzer work unchanged.
2. **Summarizer is a separate module** — not bolted into cleaner or reporter. Clean separation of concerns. Can be skipped (drain-fast mode) or run independently.
3. **Video titles from manifest** — `manifest_videos.json` already has titles from prescan. Reporter reads it for the TOC.
4. **YouTube links are standard markdown** — `[text](url)` works in Obsidian, Streamlit, GitHub, browsers. No custom rendering needed.

---

## Test Scenarios

### T1: config.py — OUTPUT_PATH Resolution

| Test | Input | Expected | How to Verify |
|------|-------|----------|---------------|
| T1.1 | Run `streamlit run gui.py` from vault root | Output at `PROJECTS/yt-transcript-analyzer/output/` | Check sidebar shows absolute path. `ls` the dir. |
| T1.2 | Run `streamlit run gui.py` from `C:\Users\User` | Same output location as T1.1 | Path is project-relative, not CWD-relative. |
| T1.3 | Set `OUTPUT_PATH=C:\custom\path` in `.env` | Output at `C:\custom\path` | Env var override still works. |
| T1.4 | `py_compile` config.py | No syntax errors | `python -c "import py_compile; py_compile.compile('config.py', doraise=True)"` |

### T2: cleaner.py — Timestamp Preservation

| Test | Input | Expected | How to Verify |
|------|-------|----------|---------------|
| T2.1 | VTT with timestamps `00:00:00.000 --> 00:00:05.000` | Clean file starts with `[00:00]` | Read first line of clean output. |
| T2.2 | VTT with timestamp `01:23:45.000` | Clean file has `[83:45]` (total minutes) | Verify `vtt_timestamp_to_seconds` -> 5025 -> `[83:45]`. |
| T2.3 | VTT filename `20260214-cTJ0Qbz0eAI-Title With Hyphens.en.vtt` | `extract_video_id` returns `cTJ0Qbz0eAI` | The video ID is ALWAYS the segment between first and second hyphen. Test with multiple real filenames. |
| T2.4 | VTT filename `20260214-cTJ0Qbz0eAI-Title.en.vtt` (standard) | `extract_video_id` returns `cTJ0Qbz0eAI` | Standard case. |
| T2.5 | Empty VTT file | Clean file is empty (no crash) | `parse_vtt` returns `[]`, `group_into_blocks` returns `[]`. |
| T2.6 | VTT with duplicate consecutive lines | Dedup removes them, timestamps still correct | `deduplicate` keeps first occurrence with its timestamp. |
| T2.7 | Clean file has `<!-- video_id:XXX -->` as first line | Chunker treats it as text (no crash, no special parsing) | Chunker reads `.txt` files as plain text — metadata comment is just text. |
| T2.8 | Old clean files (no `[MM:SS]` markers) mixed with new ones | Reporter handles both gracefully | `parse_timestamp_line` returns None for lines without `[MM:SS]` prefix. |

**Edge case — filename parsing:** VTT filenames from yt-dlp follow `%(upload_date)s-%(id)s-%(title)s.%(ext)s`. Video IDs are 11 chars (base64: `[a-zA-Z0-9_-]`). Titles can contain hyphens. The regex should match: `^\d{8}-([a-zA-Z0-9_-]{11})-` — the 8-digit date, then 11-char ID, then everything else is title.

### T3: summarizer.py — LLM Summarization

| Test | Input | Expected | How to Verify |
|------|-------|----------|---------------|
| T3.1 | Clean transcript of 500 words | Summary JSON with `summary` (non-empty string) and `tags` (list of 3-5) | Read the JSON file. Check both fields populated. |
| T3.2 | Clean transcript of 50,000 words | Prompt truncated to first 3000 words, still works | Check prompt length doesn't exceed Ollama context window. |
| T3.3 | Ollama returns malformed response (no SUMMARY: line) | Fallback: `summary: "Summary not available"`, `tags: []` | `parse_summary_response` has fallback logic. |
| T3.4 | Ollama returns response with `<think>...</think>` blocks | Think blocks stripped before parsing | Uses `strip_thinking` from analyzer.py. |
| T3.5 | Ollama is down | Error logged, video skipped, pipeline continues | `summarize_video` catches exception, returns None. |
| T3.6 | Re-run on already-summarized videos | Skips videos that already have JSON in `summaries/` | `summarize_all` checks existence before calling LLM. |
| T3.7 | Tags response has extra spaces: `TAGS: python , machine learning, data ` | Tags trimmed: `["python", "machine learning", "data"]` | `parse_summary_response` strips each tag. |

### T4: reporter.py — Clickable YouTube Links

| Test | Input | Expected | How to Verify |
|------|-------|----------|---------------|
| T4.1 | Line `[05:23] As you can see on the screen...` with video_id `cTJ0Qbz0eAI` | `[05:23](https://www.youtube.com/watch?v=cTJ0Qbz0eAI&t=323) As you can see on the screen...` | Click the link — should open YouTube at 5:23. |
| T4.2 | Line `[00:00] Welcome to this video...` | `[00:00](https://www.youtube.com/watch?v=VIDEO_ID&t=0) Welcome...` | t=0 is valid, plays from start. |
| T4.3 | Line with no `[MM:SS]` prefix (old format or metadata) | Line passed through unchanged | `parse_timestamp_line` returns None, no link generated. |
| T4.4 | `seconds_to_mmss(5025)` | `"83:45"` (not `"1:23:45"`) | MM:SS format, minutes can exceed 59. |
| T4.5 | Report TOC has video titles from manifest | Title matches `manifest_videos.json` title field | Cross-check a few entries. |
| T4.6 | Report TOC for video with no summary (summarizer failed) | Shows "Summary not available" | Graceful degradation. |
| T4.7 | Unicode in video titles (e.g., `：` fullwidth colon) | Title renders correctly in markdown | Test with actual CodeTradingCafe titles that use `：`. |

### T5: fetcher.py — Download Stats

| Test | Input | Expected | How to Verify |
|------|-------|----------|---------------|
| T5.1 | Channel with 151 videos, 15 have subs | Returns `{"downloaded": 15, "skipped": 136, "errors": 0}` | GUI shows "15 with subtitles / 136 skipped". |
| T5.2 | All videos have subs | `skipped: 0` | No skip message shown. |
| T5.3 | yt-dlp archive file exists (re-run) | Already-downloaded videos counted as skipped (archive hit), new ones as downloaded | Archive prevents re-download. Stats should reflect actual new downloads vs cached. |
| T5.4 | yt-dlp network error mid-download | `errors` count incremented, pipeline continues | `--ignore-errors` flag already set. Parse error lines from stdout. |

### T6: gui.py — Pipeline Flow

| Test | Input | Expected | How to Verify |
|------|-------|----------|---------------|
| T6.1 | Drain mode (no query), Ollama UP | 4 stages: Fetch -> Clean -> Summarize -> Report | Progress bar shows 4 stages. Summaries generated. |
| T6.2 | Drain mode (no query), Ollama DOWN | 3 stages: Fetch -> Clean -> Report (skip summarize) | Warning shown: "Ollama not available — summaries skipped". Report still generated without summaries. |
| T6.3 | Query mode with search term | 5 stages: Fetch -> Clean -> Chunk -> Analyze -> Report | Same as before but with timestamp links in findings. |
| T6.4 | Sidebar shows output path | Absolute path displayed | Should show `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\output` |
| T6.5 | Download stats after fetch | "Downloaded 15 subtitle files (136 videos had no English subtitles)" | GUI shows both numbers, not just VTT count. |

---

## Debug Protocol

### D1: "Only 15 of 211 videos downloaded"

1. Check prescan count: GUI Stage 1 should show "Found N videos on ChannelName"
2. If N < expected: yt-dlp flat-playlist may have pagination issues. Check if channel has Shorts tab (Shorts don't have subtitles). Prescan counts regular videos only.
3. If N is correct but VTT count is low: most videos don't have English auto-subtitles. This is NORMAL for many channels. The GUI should now show the breakdown.
4. Check `output/data/archive.txt` — if populated from a previous run, videos are skipped (already downloaded). Delete archive.txt to force re-download.

### D2: "Timestamps are wrong / link jumps to wrong time"

1. Read the raw VTT file: find a specific subtitle cue, note the timestamp
2. Read the clean file: find the same text, check the `[MM:SS]` marker
3. Compute: `vtt_timestamp_to_seconds("00:05:23.000")` should = `323.0`
4. Check the YouTube link: `&t=323` should jump to 5:23
5. Common trap: `group_into_blocks` uses the FIRST entry's timestamp for each 30-sec block. If a cue spans 00:29-00:31, it goes in the 00:30 block. Off by up to 30 seconds — this is by design (block-level granularity, not cue-level).

### D3: "Summarizer is stuck / slow"

1. Each video summary = 1 Ollama API call with ~3000 words input. On RTX 3060, expect 15-30 seconds per video.
2. 15 videos = ~5-8 minutes for summarization stage.
3. If stuck: check Ollama process (`ollama ps`). Check if VRAM is full. qwen3:8b is 4.9GB, fits in 12GB VRAM.
4. If Ollama returns empty: check `output/summaries/` for partial files. Re-run will skip completed ones.

### D4: "Output went to wrong directory"

1. Check config.py: `OUTPUT_PATH` should now use `Path(__file__).parent / "output"`.
2. If env var `OUTPUT_PATH` is set in `.env`, it overrides. Check `.env` file.
3. GUI sidebar now shows the absolute output path — look there first.
4. If running from CLI (`python main.py`), CWD doesn't matter after this fix.

### D5: "Clean files have old format (no timestamps) mixed with new"

1. Old clean files won't have `[MM:SS]` markers or `<!-- video_id: -->` metadata.
2. Reporter handles this: `parse_timestamp_line` returns None for unmarked lines, renders them as plain text (no YouTube link).
3. To regenerate all: delete `output/clean/` directory, re-run clean stage.

### D6: "extract_video_id fails / returns wrong ID"

1. Check VTT filename format: expected `YYYYMMDD-VIDEOID-Title.en.vtt`
2. Video IDs are exactly 11 characters: `[a-zA-Z0-9_-]{11}`
3. Regex: `^\d{8}-([a-zA-Z0-9_-]{11})-`
4. If yt-dlp output template changes, this regex breaks. Template is in `fetcher.py:download_subtitles()`: `%(upload_date)s-%(id)s-%(title)s.%(ext)s`
5. Spot-check: take any VTT filename, extract the 11-char segment after the date, paste into `youtube.com/watch?v=THAT_ID` — it should load the correct video.

---

## Verification

1. **py_compile** all modified files: config.py, cleaner.py, summarizer.py, reporter.py, fetcher.py, gui.py
2. Run drain on a small channel (5-10 videos):
   - Confirm output goes to `PROJECTS/yt-transcript-analyzer/output/` regardless of CWD
   - Confirm clean files have `[MM:SS]` timestamp markers and `<!-- video_id: -->` metadata
   - Confirm summaries/ has one JSON per video with non-empty summary + tags
   - Confirm report has clickable YouTube links (click one, verify it jumps to correct time)
   - Confirm TOC has video titles, summaries, and tags
3. Run query mode on same channel:
   - Confirm findings include timestamp links
4. Check GUI:
   - Sidebar shows absolute output path
   - Download stats show success/skip counts
   - Summarize stage shows per-video progress
5. Spot-check 3 random YouTube timestamp links — do they jump to the right moment?
6. Re-run drain on same channel — summarizer skips already-done videos, archive skips already-downloaded VTTs

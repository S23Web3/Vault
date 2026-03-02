# YT Transcript Analyzer — GUI Build Session
**Date:** 2026-02-26

---

## Summary
Built and iteratively improved the Streamlit GUI for the YT Transcript Analyzer. Started from a working CLI pipeline, ended with a full-featured GUI with real-time progress, system status checks, and two operating modes (drain vs query).

## Work Completed

### 1. Vince ML Cleanup (from previous context)
- Fixed `TOPIC-vince-v2.md` — "APPROVED" corrected to "NOT YET APPROVED FOR BUILD"
- Marked `SPEC-C-VINCE-ML.md` as SUPERSEDED
- Marked `BUILD-VINCE-ML.md` as ARCHIVED
- Changed P1.2 in `PRODUCT-BACKLOG.md` to SUPERSEDED

### 2. Initial GUI Build
- Created `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\gui.py` (Streamlit)
- Wraps existing pipeline: fetcher -> cleaner -> chunker -> analyzer -> reporter
- Sidebar shows Ollama status, data counts, config
- Run command: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\gui.py"`

### 3. yt-dlp Installation
- `yt-dlp` was not installed — `[WinError 2]` on first run
- Installed via `pip install yt-dlp`
- Binary location: `C:\Users\User\AppData\Roaming\Python\Python313\Scripts\yt-dlp.EXE`

### 4. ffmpeg + deno Installation
- User tried `pip install ffmpeg` and `pip install deno` — explained these are Python wrappers, not the actual binaries yt-dlp needs
- Correct install: `winget install Gyan.FFmpeg` and `winget install DenoLand.Deno`
- User learned the difference between pip wrappers and system binaries — key teaching moment

### 5. Optional Query (Drain Mode)
- User asked: "why must i put in a query, why cant i just drain the whole channel?"
- Made query field optional in GUI
- Added `generate_full_report()` to `reporter.py` — dumps all clean transcripts, no LLM
- Drain mode: Fetch -> Clean -> Report (3 stages, no Ollama needed)
- Query mode: Fetch -> Clean -> Chunk -> Analyze -> Report (5 stages)

### 6. Real-Time Progress Overhaul
- User complained: "see it just stays" — GUI showed "Fetching..." with no updates while terminal got all output
- Root cause: `subprocess.run()` blocks with no callback to GUI
- **fetcher.py**: Split `fetch_subtitles()` into `prescan_channel()` + `download_subtitles()`. Download uses `subprocess.Popen` with line-by-line stdout parsing and `on_progress` callback
- **gui.py**: Complete pipeline rewrite with:
  - Stage counter: "Stage 1/3: Found 151 videos on CodeTradingCafe"
  - Detail line: "Downloading video 47/151..." updates in real time
  - Progress bar moves per-video during download
  - Different stage counts for drain (3) vs query (5) modes

### 7. Sidebar System Status
- Added tool checks: yt-dlp (required), ffmpeg (optional), deno (optional)
- Each shows green/red with install command if missing
- Ollama section separated with its own header
- Drain mode doesn't require Ollama — button enables without it
- Button label changes: "Drain Channel" vs "Run Analysis"

## Files Modified
| File | Action |
|------|--------|
| `PROJECTS\yt-transcript-analyzer\gui.py` | Created then heavily modified (sidebar, pipeline, drain mode) |
| `PROJECTS\yt-transcript-analyzer\fetcher.py` | Added `download_subtitles()` with Popen + progress callback |
| `PROJECTS\yt-transcript-analyzer\reporter.py` | Added `generate_full_report()` for drain mode |
| `PROJECTS\yt-transcript-analyzer\requirements.txt` | Added streamlit |

## Key Lesson
User: "i ask questions, you give answers, i need to learn so we can be a better team. if youre going to do something then you need to tell me"
- Always explain WHAT you're about to do and WHY before doing it
- When the user hits an error, explain the root cause so they can fix similar issues themselves
- pip wrappers vs system binaries is a common gotcha worth explaining clearly

## Dependencies Installed This Session
- yt-dlp (pip) — YouTube subtitle downloader
- ffmpeg (winget) — media processing binary
- deno (winget) — JavaScript runtime for yt-dlp
- streamlit (pip, previous session) — GUI framework

# YT Analyzer v2.1 — UX Overhaul: Cancel, Activity Log, Settings, Speed

**Date:** 2026-02-27
**Purpose:** Fix usability problems discovered during first real run (211 videos, 201 transcripts, 50+ min summarize stage).

---

## Problems

1. **No cancel** — Can't stop the pipeline. Summarize stage = 50-100 min with no abort.
2. **Invisible progress** — `detail_text.text()` overwrites itself. Events flash by unreadable.
3. **No output preview** — Can't see report content until the very end.
4. **No output folder control** — User can't choose where files save. No visibility into defaults.
5. **Channels mix together** — All channels dump into the same `output/` subdirectories.
6. **Summarize is slow with no opt-out** — 201 videos x 15-30 sec = forced 50-100 min wait even if you just want transcripts.
7. **No ETA** — Staring at "70/201" with no idea how long is left.
8. **No resume awareness** — If you cancel at 70/201 and restart, no indication that 70 are already done.
9. **No re-run without re-download** — Can't re-process existing VTTs without hitting YouTube again.
10. **No download button** — Report saved to disk but no way to download it from the browser.

---

## Streamlit Constraints (from research)

- Single-threaded per session. Button click during execution queues a rerun.
- Rerun interrupts running script at next `st.*` API call (raises `StopException`).
- `st.container()` allows appending — each `st.markdown()` inside adds a new DOM element.
- `st.container(height=N)` creates scrollable fixed-height container.
- `on_click` callbacks fire before the script reruns (can set flags).

---

## Files to Modify

| File | Changes |
| ---- | ------- |
| `gui.py` | Major rewrite — cancel, activity log, settings panel, skip-summarize toggle, ETA, resume awareness, download button |
| `fetcher.py` | `on_process_started` callback to expose Popen handle |
| `summarizer.py` | Extend callback to pass result dict. Add `already_done` count to return. |
| `config.py` | Add `get_channel_output_path(channel_name)` helper for per-channel dirs |

---

## Implementation Steps

### Step 1: Per-channel output directories (`config.py`)

Add a helper that creates channel-namespaced paths:

```python
def get_channel_paths(channel_name):
    """Return dict of per-channel output paths."""
    slug = re.sub(r"[^a-zA-Z0-9_-]", "", channel_name)
    base = OUTPUT_PATH / slug
    return {
        "raw": base / "raw",
        "clean": base / "clean",
        "chunks": base / "chunks",
        "findings": base / "findings",
        "reports": base / "reports",
        "summaries": base / "summaries",
        "data": base / "data",
        "archive": base / "data" / "archive.txt",
        "manifest_videos": base / "data" / "manifest_videos.json",
        "manifest_chunks": base / "data" / "manifest_chunks.json",
    }
```

The global `RAW_PATH`, `CLEAN_PATH`, etc. remain as defaults. The pipeline passes channel-specific paths when running.

This means all pipeline modules (`fetcher.py`, `cleaner.py`, `summarizer.py`, `reporter.py`, `chunker.py`, `analyzer.py`) need to accept path overrides instead of importing globals from config. **This is a significant refactor** — every module currently does `from config import RAW_PATH, CLEAN_PATH, ...`.

**Simpler alternative:** Instead of refactoring all modules, dynamically set the config globals at pipeline start:

```python
import config
channel_paths = config.get_channel_paths(channel_name)
config.RAW_PATH = channel_paths["raw"]
config.CLEAN_PATH = channel_paths["clean"]
# ... etc
```

All modules import from config at call time (not at import time), so this works. Reset after pipeline completes.

### Step 2: Settings panel (`gui.py`)

Sidebar expander with editable settings:

```python
with st.sidebar.expander("Settings"):
    output_dir = st.text_input("Output folder", value=str(OUTPUT_PATH))
    ollama_url = st.text_input("Ollama URL", value=OLLAMA_BASE_URL)
    model_name = st.text_input("Model", value=QWEN_MODEL)
    skip_summarize = st.checkbox("Skip summarization (fast drain)", value=False)
```

These override the config values for the current run. Not persisted to `.env` — just session-level overrides.

### Step 3: Skip-summarize toggle (`gui.py`)

When `skip_summarize` is checked:
- Drain mode becomes 3 stages: Fetch -> Clean -> Report (same as "Ollama not available" path)
- Report is generated without summaries/tags (TOC has titles only, no tags/summary columns)
- Total time drops from 50+ min to ~2-5 min

This is already partially implemented — the `if ollama_ready` branch in `run_pipeline()` already handles the no-Ollama case. Just wire the checkbox to force that path.

### Step 4: Expose subprocess handle (`fetcher.py`)

Add optional `on_process_started` callback:

```python
def download_subtitles(url, channel_name, videos, on_progress=None, on_process_started=None):
    ...
    process = subprocess.Popen(cmd, ...)
    if on_process_started:
        on_process_started(process)
    ...
```

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\fetcher.py`
**Line:** 103

### Step 5: Extend summarizer callback + resume count (`summarizer.py`)

Two changes:

**5a:** Pass result in callback:
```python
# Before:
on_progress(i, total, "Summarizing video " + str(i) + "/" + str(total))

# After:
on_progress(i, total, "Summarizing video " + str(i) + "/" + str(total), result)
```

**5b:** Return `already_done` count so GUI can show resume awareness:
```python
def summarize_all(on_progress=None):
    ...
    already_done = 0
    for i, clean_file in enumerate(clean_files, 1):
        result = summarize_video(clean_file)
        if result and result.get("_cached", False):
            already_done += 1
        ...
    return summaries, already_done
```

And in `summarize_video()`, tag cached results:
```python
if out_path.exists():
    data = json.loads(out_path.read_text(encoding="utf-8"))
    data["_cached"] = True
    return data
```

### Step 6: Rewrite GUI pipeline (`gui.py`)

#### 6a: Session state init + orphan cleanup

```python
if "running" not in st.session_state:
    st.session_state.running = False
if "active_process" not in st.session_state:
    st.session_state.active_process = None

# Kill orphaned subprocess from cancelled run
proc = st.session_state.get("active_process")
if proc and proc.poll() is None:
    proc.terminate()
    st.session_state.active_process = None
```

#### 6b: Cancel button

```python
def request_cancel():
    proc = st.session_state.get("active_process")
    if proc and proc.poll() is None:
        proc.terminate()
    st.session_state.running = False

col_run, col_cancel = st.columns([3, 1])
with col_run:
    run_clicked = st.button(button_label, disabled=run_disabled or st.session_state.running, ...)
with col_cancel:
    st.button("Cancel", on_click=request_cancel, disabled=not st.session_state.running)
```

#### 6c: Activity log (scrollable container)

```python
progress_bar = st.progress(0.0)
status_text = st.empty()
activity_log = st.container(height=400)

def log_event(msg):
    with activity_log:
        st.markdown(msg)
```

#### 6d: Video list after prescan (clickable links)

```python
log_event("**Found " + str(len(videos)) + " videos on " + channel_name + ":**")
for i, v in enumerate(videos, 1):
    vid = v.get("id", "")
    title = v.get("title", "Unknown")
    if vid:
        log_event(str(i) + ". [" + title + "](https://www.youtube.com/watch?v=" + vid + ")")
    else:
        log_event(str(i) + ". " + title)
```

#### 6e: Download events in log

Replace `detail_text.text(message)` with `log_event(message)` in the download callback.

#### 6f: ETA display during summarize

Track elapsed time per video, compute average, show estimate:

```python
summarize_start = time.time()

def on_summarize_progress(current, total_vids, message, result):
    elapsed = time.time() - summarize_start
    avg_per_video = elapsed / max(current, 1)
    remaining = avg_per_video * (total_vids - current)
    eta_min = int(remaining // 60)
    eta_sec = int(remaining % 60)
    status_text.text("Stage 3/4: " + str(current) + "/" + str(total_vids)
        + " — ~" + str(eta_min) + "m " + str(eta_sec) + "s remaining")
    # ... plus log_event with result details
```

#### 6g: Resume awareness

Before starting summarize stage, count existing summaries:

```python
existing_summaries = count_existing_files(SUMMARIES_PATH, "*.json")
if existing_summaries > 0:
    log_event("**" + str(existing_summaries) + " videos already summarized** (will skip)")
```

#### 6h: Re-run without re-download

Detect existing VTT files and offer to skip download:

```python
existing_vtts = count_existing_files(RAW_PATH, "*.vtt")
if existing_vtts > 0:
    skip_download = st.checkbox(
        "Skip download (" + str(existing_vtts) + " VTTs already exist)",
        value=True
    )
```

When checked, pipeline jumps straight to Clean stage. Prescan is still needed for manifest data (video titles for the report), but download is skipped.

#### 6i: Download button for report

After report renders:

```python
if report_path and report_path.exists():
    content = report_path.read_text(encoding="utf-8")
    st.download_button(
        "Download Report",
        data=content,
        file_name=report_path.name,
        mime="text/markdown",
    )
```

#### 6j: Try/finally cleanup

```python
st.session_state.running = True
try:
    report_path = run_pipeline(...)
finally:
    st.session_state.running = False
    proc = st.session_state.get("active_process")
    if proc and proc.poll() is None:
        proc.terminate()
    st.session_state.active_process = None
```

---

## Verification

1. **py_compile** all 4 modified files
2. Run drain on small channel (5-10 videos):
   - Settings panel shows defaults
   - After prescan: clickable video list appears
   - During download: events accumulate (not overwrite)
   - During summarize: each result shows title + tags + summary + ETA
   - Report renders with download button
3. Cancel test:
   - Start drain, click Cancel during summarize
   - Pipeline stops within ~30 sec
   - No orphaned processes
   - Re-run starts cleanly
4. Skip-summarize test:
   - Check "Skip summarization", run drain
   - 3 stages only, completes in ~2-5 min
   - Report has titles but no tags/summaries
5. Resume test:
   - Run drain, cancel at video 5/15
   - Re-run same channel
   - Shows "5 videos already summarized (will skip)"
   - Summarizes only remaining 10
6. Re-run without download test:
   - After successful drain, run same channel again
   - "Skip download (15 VTTs already exist)" checkbox appears
   - Pipeline starts at Clean stage
7. Per-channel test:
   - Drain channel A, then drain channel B
   - Confirm separate folders: `output/ChannelA/`, `output/ChannelB/`

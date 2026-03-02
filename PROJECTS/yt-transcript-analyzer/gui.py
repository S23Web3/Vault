"""Streamlit GUI for YouTube Transcript Analyzer."""
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# Add project root to path so imports work when streamlit runs from any cwd
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import startup
import fetcher
import cleaner
import chunker
import analyzer
import summarizer
import reporter
from config import (
    CHUNKS_PATH, CLEAN_PATH, DATA_PATH, FINDINGS_PATH,
    MANIFEST_CHUNKS_PATH, MANIFEST_VIDEOS_PATH,
    OLLAMA_BASE_URL, OUTPUT_PATH, QWEN_MODEL, RAW_PATH, REPORTS_PATH, SUMMARIES_PATH,
)

log = logging.getLogger(__name__)


def ensure_dirs():
    """Create all required output directories."""
    for path in [DATA_PATH, RAW_PATH, CLEAN_PATH, CHUNKS_PATH, FINDINGS_PATH, REPORTS_PATH, SUMMARIES_PATH]:
        path.mkdir(parents=True, exist_ok=True)


def check_ollama_status():
    """Check Ollama reachability and model availability. Returns (reachable, model_loaded)."""
    import urllib.request
    try:
        url = OLLAMA_BASE_URL + "/api/tags"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        model_found = any(QWEN_MODEL in m for m in models)
        return True, model_found
    except Exception:
        return False, False


def count_existing_files(directory, pattern="*"):
    """Count files matching pattern in a directory."""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def render_sidebar():
    """Render sidebar with status checks, config info, and settings. Returns (ollama_ready, ytdlp_ok, skip_summarize)."""
    st.sidebar.title("System Status")

    # Tool checks
    st.sidebar.subheader("Tools")
    ytdlp_ok = shutil.which("yt-dlp") is not None
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    deno_ok = shutil.which("deno") is not None

    if ytdlp_ok:
        st.sidebar.success("yt-dlp: installed")
    else:
        st.sidebar.error("yt-dlp: NOT FOUND")
        st.sidebar.caption("Install: `pip install yt-dlp`")

    if ffmpeg_ok:
        st.sidebar.success("ffmpeg: installed")
    else:
        st.sidebar.warning("ffmpeg: not found (optional)")
        st.sidebar.caption("Install: `winget install Gyan.FFmpeg`")

    if deno_ok:
        st.sidebar.success("deno: installed")
    else:
        st.sidebar.warning("deno: not found (optional)")
        st.sidebar.caption("Install: `winget install DenoLand.Deno`")

    # Ollama checks
    st.sidebar.markdown("---")
    st.sidebar.subheader("Ollama")
    ollama_ok, model_ok = check_ollama_status()

    if ollama_ok:
        st.sidebar.success("Ollama: connected")
    else:
        st.sidebar.error("Ollama: not reachable at " + OLLAMA_BASE_URL)
        st.sidebar.caption("Start Ollama first: `ollama serve`")

    if model_ok:
        st.sidebar.success("Model: " + QWEN_MODEL)
    elif ollama_ok:
        st.sidebar.warning("Model " + QWEN_MODEL + " not loaded")
        st.sidebar.caption("Run: `ollama pull " + QWEN_MODEL + "`")

    # Data counts
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data")
    st.sidebar.text("Raw VTTs: " + str(count_existing_files(RAW_PATH, "*.vtt")))
    st.sidebar.text("Clean texts: " + str(count_existing_files(CLEAN_PATH, "*.txt")))
    st.sidebar.text("Summaries: " + str(count_existing_files(SUMMARIES_PATH, "*.json")))
    st.sidebar.text("Chunks: " + str(count_existing_files(CHUNKS_PATH, "*.txt")))
    st.sidebar.text("Findings: " + str(count_existing_files(FINDINGS_PATH, "*.json")))
    st.sidebar.text("Reports: " + str(count_existing_files(REPORTS_PATH, "*.md")))

    # Settings
    st.sidebar.markdown("---")
    with st.sidebar.expander("Settings"):
        st.text_input("Output folder", value=str(OUTPUT_PATH), disabled=True,
                       help="Set via OUTPUT_PATH env var or .env file")
        st.text_input("Ollama URL", value=OLLAMA_BASE_URL, disabled=True,
                       help="Set via OLLAMA_BASE_URL env var")
        st.text_input("Model", value=QWEN_MODEL, disabled=True,
                       help="Configured in config.py")
        skip_summarize = st.checkbox(
            "Skip summarization (fast drain)",
            value=False,
            help="Skip LLM summaries/tags. Report will have titles and transcripts only. Saves 50+ minutes on large channels.",
        )

    ollama_ready = ollama_ok and model_ok
    return ollama_ready, ytdlp_ok, skip_summarize


def render_existing_reports():
    """Show previously generated reports in an expander."""
    report_files = sorted(REPORTS_PATH.glob("*.md"), reverse=True) if REPORTS_PATH.exists() else []
    if not report_files:
        return

    st.markdown("---")
    st.subheader("Previous Reports")
    for rpt in report_files[:10]:
        with st.expander(rpt.name):
            content = rpt.read_text(encoding="utf-8")
            st.markdown(content)


def run_pipeline(url, query, progress_bar, status_text, log_event, ollama_ready, skip_summarize, skip_download):
    """Run the full pipeline with activity log and ETA. Returns report path or None."""
    is_drain = not query.strip()
    do_summarize = is_drain and ollama_ready and not skip_summarize

    # Stage counts
    if is_drain:
        total = 4 if do_summarize else 3
    else:
        total = 5
    stage = 0

    # --- Stage 1: Prescan + Download ---
    if skip_download:
        log_event("**Skipping download** -- using existing VTT files")
        stage = 1
        progress_bar.progress(stage / total)
        # Load manifest for video titles
        if MANIFEST_VIDEOS_PATH.exists():
            manifest_data = json.loads(MANIFEST_VIDEOS_PATH.read_text(encoding="utf-8"))
            channel_name = manifest_data.get("channel_name", "Unknown")
            videos = manifest_data.get("videos", [])
            status_text.text("Stage 1/" + str(total) + ": Using cached data for " + channel_name
                             + " (" + str(len(videos)) + " videos)")
        else:
            channel_name = "Unknown"
            videos = []
            status_text.text("Stage 1/" + str(total) + ": No manifest found -- video titles may be missing")
    else:
        status_text.text("Stage 1/" + str(total) + ": Scanning channel...")
        log_event("Running yt-dlp prescan...")
        progress_bar.progress(0.0)

        try:
            channel_name = fetcher.extract_channel_name(url)
            videos = fetcher.prescan_channel(url)
        except Exception as exc:
            st.error("Prescan failed: " + str(exc))
            return None

        video_count = len(videos)
        status_text.text("Stage 1/" + str(total) + ": Found " + str(video_count) + " videos on " + channel_name)

        # Show clickable video list
        log_event("**Found " + str(video_count) + " videos on " + channel_name + ":**")
        for i, v in enumerate(videos, 1):
            vid = v.get("id", "")
            title = v.get("title", "Unknown")
            if vid:
                log_event(str(i) + ". [" + title + "](https://www.youtube.com/watch?v=" + vid + ")")
            else:
                log_event(str(i) + ". " + title)

        log_event("---")
        log_event("**Starting subtitle download...**")

        def on_process_started(proc):
            """Store subprocess handle for cancel support."""
            st.session_state.active_process = proc

        def on_download_progress(current, total_vids, message):
            """Callback from fetcher to update GUI during download."""
            pct = current / max(total_vids, 1)
            progress_bar.progress(pct * (1 / total))
            log_event(message)

        try:
            stats = fetcher.download_subtitles(
                url, channel_name, videos,
                on_progress=on_download_progress,
                on_process_started=on_process_started,
            )
        except Exception as exc:
            st.error("Download failed: " + str(exc))
            return None

        st.session_state.active_process = None

        vtt_count = count_existing_files(RAW_PATH, "*.vtt")
        stage = 1
        dl_msg = "Downloaded " + str(stats["downloaded"]) + " subtitle files"
        if stats["archived"] > 0:
            dl_msg = dl_msg + " (" + str(stats["archived"]) + " already downloaded)"
        if stats["skipped"] > 0:
            dl_msg = dl_msg + " (" + str(stats["skipped"]) + " had no English subtitles)"
        if stats["errors"] > 0:
            dl_msg = dl_msg + " (" + str(stats["errors"]) + " errors)"
        status_text.text("Stage 1/" + str(total) + ": " + dl_msg)
        log_event("**" + dl_msg + "**")
        progress_bar.progress(stage / total)

        if vtt_count == 0:
            st.warning("No subtitle files were downloaded. The channel may not have English subtitles.")
            return None

    # --- Stage 2: Clean ---
    stage = 2
    status_text.text("Stage 2/" + str(total) + ": Cleaning VTT files...")
    log_event("Cleaning VTT files -- deduplicating and adding timestamp markers...")
    try:
        cleaned = cleaner.clean_all()
    except Exception as exc:
        st.error("Clean failed: " + str(exc))
        return None
    status_text.text("Stage 2/" + str(total) + ": Cleaned " + str(len(cleaned)) + " files")
    log_event("**Cleaned " + str(len(cleaned)) + " files with [MM:SS] timestamp markers**")
    progress_bar.progress(stage / total)

    if is_drain:
        # --- Stage 3 (drain): Summarize (if enabled) ---
        if do_summarize:
            stage = 3

            # Resume awareness
            existing_summaries = count_existing_files(SUMMARIES_PATH, "*.json")
            if existing_summaries > 0:
                log_event("**" + str(existing_summaries) + " videos already summarized** (will skip)")

            status_text.text("Stage 3/" + str(total) + ": Summarizing with " + QWEN_MODEL + "...")
            log_event("---")
            log_event("**Summarizing with " + QWEN_MODEL + "...**")

            # Load manifest for title lookups
            manifest_videos = reporter.load_manifest_videos()

            summarize_start = time.time()

            def on_summarize_progress(current, total_vids, message, result):
                """Callback from summarizer with ETA and live preview."""
                pct = current / max(total_vids, 1)
                progress_bar.progress((2 + pct) / total)

                # ETA
                elapsed = time.time() - summarize_start
                avg = elapsed / max(current, 1)
                remaining = avg * (total_vids - current)
                eta_min = int(remaining // 60)
                eta_sec = int(remaining % 60)
                status_text.text(
                    "Stage 3/" + str(total) + ": " + str(current) + "/" + str(total_vids)
                    + " -- ~" + str(eta_min) + "m " + str(eta_sec) + "s remaining"
                )

                # Live preview in activity log
                if result:
                    vid = result.get("video_id", "")
                    tags = result.get("tags", [])
                    summary_text = result.get("summary", "")
                    cached = result.get("_cached", False)
                    title = manifest_videos.get(vid, {}).get("title", vid)
                    link = "[" + title + "](https://www.youtube.com/watch?v=" + vid + ")" if vid else title
                    tags_str = ", ".join(tags) if tags else "no tags"
                    prefix = str(current) + "/" + str(total_vids)
                    if cached:
                        log_event(prefix + ": " + link + " (cached)")
                    else:
                        log_event(prefix + ": " + link + " -- " + tags_str)
                        log_event("> " + summary_text)
                else:
                    log_event(str(current) + "/" + str(total_vids) + ": " + message + " (failed)")

            try:
                summaries = summarizer.summarize_all(on_progress=on_summarize_progress)
            except Exception as exc:
                st.warning("Summarize failed: " + str(exc) + " -- continuing without summaries")
                summaries = []

            status_text.text("Stage 3/" + str(total) + ": Summarized " + str(len(summaries)) + " videos")
            log_event("**Summarized " + str(len(summaries)) + " videos**")
            progress_bar.progress(stage / total)
        else:
            if not ollama_ready:
                log_event("Ollama not available -- summaries skipped")
            elif skip_summarize:
                log_event("Summarization skipped (fast drain mode)")
            st.info("Summaries skipped. Report will be generated without summaries/tags.")

        # --- Final drain stage: Generate full report ---
        stage = total
        status_text.text("Stage " + str(stage) + "/" + str(total) + ": Generating structured report...")
        log_event("---")
        log_event("**Generating structured report...**")
        try:
            report_path = reporter.generate_full_report()
        except Exception as exc:
            st.error("Report failed: " + str(exc))
            return None
    else:
        # --- Stage 3 (query): Chunk ---
        stage = 3
        status_text.text("Stage 3/" + str(total) + ": Splitting into chunks...")
        log_event("Splitting text into 2500-token chunks...")
        try:
            chunker.chunk_all()
        except Exception as exc:
            st.error("Chunk failed: " + str(exc))
            return None
        chunk_count = count_existing_files(CHUNKS_PATH, "*.txt")
        status_text.text("Stage 3/" + str(total) + ": Created " + str(chunk_count) + " chunks")
        log_event("**Created " + str(chunk_count) + " chunks**")
        progress_bar.progress(stage / total)

        # --- Stage 4 (query): Analyze ---
        stage = 4
        status_text.text("Stage 4/" + str(total) + ": Analyzing with " + QWEN_MODEL + "...")
        log_event("Sending each chunk to LLM for relevance matching...")
        try:
            findings = analyzer.analyze_all(query)
        except Exception as exc:
            st.error("Analyze failed: " + str(exc))
            return None
        status_text.text("Stage 4/" + str(total) + ": Found " + str(len(findings)) + " relevant chunks")
        log_event("**Found " + str(len(findings)) + " relevant chunks**")
        progress_bar.progress(stage / total)

        # --- Stage 5 (query): Report ---
        stage = 5
        status_text.text("Stage 5/" + str(total) + ": Generating report...")
        log_event("Writing filtered findings with timestamp links to markdown...")
        try:
            report_path = reporter.generate_report(query)
        except Exception as exc:
            st.error("Report failed: " + str(exc))
            return None

    progress_bar.progress(1.0)
    status_text.text("Done. " + str(total) + " stages complete.")
    log_event("---")
    log_event("**Done.**")
    return report_path


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="YT Transcript Analyzer",
        page_icon="?",
        layout="wide",
    )

    ensure_dirs()

    # Session state init
    if "running" not in st.session_state:
        st.session_state.running = False
    if "active_process" not in st.session_state:
        st.session_state.active_process = None

    # Kill orphaned subprocess from previous cancelled run
    proc = st.session_state.get("active_process")
    if proc and proc.poll() is None:
        proc.terminate()
        st.session_state.active_process = None

    st.title("YouTube Transcript Analyzer")
    st.caption("Paste a YouTube channel/playlist URL. Add a search query to filter, or leave it blank to drain the whole channel.")

    ollama_ready, ytdlp_ok, skip_summarize = render_sidebar()

    col1, col2 = st.columns([2, 1])

    with col1:
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/@channelname",
            help="Channel, playlist, or single video URL",
        )

    with col2:
        query = st.text_input(
            "Search Query (optional)",
            placeholder="leave blank to drain entire channel",
            help="Filter transcripts for specific topics. Leave blank to get everything.",
        )

    # Drain mode only needs yt-dlp. Query mode also needs Ollama.
    is_drain = not query.strip()

    if not ytdlp_ok:
        st.error("yt-dlp is not installed. Install it: `pip install yt-dlp`")
    elif not is_drain and not ollama_ready:
        st.warning("Ollama is required for query mode. Start Ollama or leave the query blank to drain without LLM.")

    # Skip-download option
    existing_vtts = count_existing_files(RAW_PATH, "*.vtt")
    manifest_exists = MANIFEST_VIDEOS_PATH.exists()
    can_skip_download = existing_vtts > 0 and manifest_exists

    skip_download = False
    if can_skip_download:
        skip_download = st.checkbox(
            "Skip download (" + str(existing_vtts) + " VTTs already exist)",
            value=True,
            help="Use existing subtitle files instead of re-downloading from YouTube.",
        )

    # Disable run button when no URL (unless skipping download) or missing tools
    run_disabled = not ytdlp_ok or (not is_drain and not ollama_ready)
    if not skip_download:
        run_disabled = run_disabled or not url

    # Cancel callback
    def request_cancel():
        """Kill active subprocess and signal cancel."""
        p = st.session_state.get("active_process")
        if p and p.poll() is None:
            p.terminate()
        st.session_state.running = False

    # Run / Cancel buttons
    button_label = "Drain Channel" if is_drain else "Run Analysis"
    col_run, col_cancel = st.columns([3, 1])
    with col_run:
        run_clicked = st.button(
            button_label,
            disabled=run_disabled or st.session_state.running,
            type="primary",
            use_container_width=True,
        )
    with col_cancel:
        st.button(
            "Cancel",
            on_click=request_cancel,
            disabled=not st.session_state.running,
            use_container_width=True,
        )

    if run_clicked:
        st.markdown("---")
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        activity_log = st.container(height=400)

        def log_event(msg):
            """Append a line to the scrollable activity log."""
            with activity_log:
                st.markdown(msg)

        start_time = time.time()
        st.session_state.running = True
        report_path = None
        try:
            report_path = run_pipeline(
                url, query, progress_bar, status_text, log_event,
                ollama_ready, skip_summarize, skip_download,
            )
        finally:
            st.session_state.running = False
            p = st.session_state.get("active_process")
            if p and p.poll() is None:
                p.terminate()
            st.session_state.active_process = None

        elapsed = time.time() - start_time

        if report_path and report_path.exists():
            st.success(
                "Complete in "
                + str(int(elapsed // 60)) + "m "
                + str(int(elapsed % 60)) + "s"
            )

            # Download button
            content = report_path.read_text(encoding="utf-8")
            st.download_button(
                "Download Report",
                data=content,
                file_name=report_path.name,
                mime="text/markdown",
            )

            st.markdown("---")
            st.subheader("Report")
            st.markdown(content)

            st.markdown("---")
            st.caption("Report saved to: " + str(report_path))

    render_existing_reports()


if __name__ == "__main__":
    main()

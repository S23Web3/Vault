"""Fetches YouTube subtitles via yt-dlp. Handles all channel URL formats."""
import json
import logging
import re
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
    videos = prescan_channel(url)
    download_subtitles(url, channel_name, videos)


def download_subtitles(url: str, channel_name: str, videos: list, on_progress=None, on_process_started=None) -> dict:
    """Download VTT subtitles with progress callback. Returns stats dict."""
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

    total = len(videos)
    stats = {"downloaded": 0, "skipped": 0, "archived": 0, "errors": 0}
    log.info("Downloading subtitles (%d videos)...", total)
    process = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if on_process_started:
        on_process_started(process)
    current = 0
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        item_match = re.search(r"Downloading item (\d+) of (\d+)", line)
        if item_match:
            current = int(item_match.group(1))
            if on_progress:
                on_progress(current, total, "Downloading video " + str(current) + "/" + str(total))
        elif "Writing video subtitles" in line:
            stats["downloaded"] += 1
            short = line.split("to: ")[-1] if "to: " in line else line
            if on_progress:
                on_progress(current, total, "Saving: " + short)
        elif "has already been recorded" in line:
            stats["archived"] += 1
        elif "has no subtitles" in line.lower() or "no subtitles" in line.lower():
            stats["skipped"] += 1
        elif "ERROR" in line:
            stats["errors"] += 1
    process.wait()
    if process.returncode != 0:
        log.error("yt-dlp exited with code %d", process.returncode)
    else:
        log.info("yt-dlp completed")
    log.info("Stats: %d downloaded, %d skipped, %d archived, %d errors",
             stats["downloaded"], stats["skipped"], stats["archived"], stats["errors"])
    return stats


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

"""Summarizes video transcripts and generates topic tags via qwen3:8b."""
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from cleaner import extract_video_id_from_clean
from config import (
    OLLAMA_BASE_URL,
    OLLAMA_RETRIES,
    OLLAMA_TIMEOUT,
    QWEN_MODEL,
    SUMMARIES_PATH,
)

log = logging.getLogger(__name__)

MAX_PROMPT_WORDS = 3000


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from model output (qwen3 thinking mode)."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def build_summary_prompt(text: str) -> str:
    """Build summarization prompt, truncated to MAX_PROMPT_WORDS."""
    words = text.split()
    truncated = " ".join(words[:MAX_PROMPT_WORDS])
    return (
        "Summarize this YouTube video transcript in 2-3 sentences.\n"
        "Then list 3-5 topic tags that describe the main subjects covered.\n\n"
        "TRANSCRIPT:\n" + truncated + "\n\n"
        "Respond in EXACTLY this format (two lines, nothing else):\n"
        "SUMMARY: <2-3 sentence summary>\n"
        "TAGS: tag1, tag2, tag3\n"
    )


def call_ollama(prompt: str) -> str:
    """Call Ollama /api/generate with retry. Returns response text or empty string."""
    payload = {"model": QWEN_MODEL, "prompt": prompt, "stream": False}
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
                import time
                time.sleep(2 ** attempt)
    log.error("Ollama failed after %d attempts: %s", OLLAMA_RETRIES + 1, last_exc)
    return ""


def parse_summary_response(raw: str) -> dict:
    """Parse SUMMARY and TAGS from model response. Returns dict with fallbacks."""
    cleaned = strip_thinking(raw)
    summary_match = re.search(r"^SUMMARY:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
    tags_match = re.search(r"^TAGS:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
    summary = summary_match.group(1).strip() if summary_match else "Summary not available"
    tags_raw = tags_match.group(1).strip() if tags_match else ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    return {"summary": summary, "tags": tags}


def summarize_video(clean_path: Path) -> dict:
    """Summarize a single video transcript. Returns summary dict or None on failure."""
    video_id = extract_video_id_from_clean(clean_path)
    out_path = SUMMARIES_PATH / (video_id + ".json")
    if out_path.exists():
        log.debug("Already summarized: %s", video_id)
        data = json.loads(out_path.read_text(encoding="utf-8"))
        data["_cached"] = True
        return data
    text = clean_path.read_text(encoding="utf-8").strip()
    if not text:
        log.warning("Empty transcript: %s", clean_path.name)
        return None
    prompt = build_summary_prompt(text)
    raw = call_ollama(prompt)
    if not raw:
        log.error("Empty response for %s", video_id)
        return None
    parsed = parse_summary_response(raw)
    result = {
        "video_id": video_id,
        "summary": parsed["summary"],
        "tags": parsed["tags"],
        "summarized_at": datetime.now(timezone.utc).isoformat(),
    }
    SUMMARIES_PATH.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.info("Summarized %s: %d tags", video_id, len(parsed["tags"]))
    return result


def summarize_all(on_progress=None) -> list:
    """Summarize all clean transcripts. Skips already-summarized. Returns list of summary dicts."""
    from config import CLEAN_PATH
    clean_files = sorted(CLEAN_PATH.glob("*.txt")) if CLEAN_PATH.exists() else []
    total = len(clean_files)
    log.info("Summarizing %d transcripts", total)
    SUMMARIES_PATH.mkdir(parents=True, exist_ok=True)
    summaries = []
    for i, clean_file in enumerate(clean_files, 1):
        try:
            result = summarize_video(clean_file)
            if result:
                summaries.append(result)
            if on_progress:
                on_progress(i, total, "Summarizing video " + str(i) + "/" + str(total), result)
        except Exception as exc:
            log.error("Failed to summarize %s: %s", clean_file.name, exc)
            if on_progress:
                on_progress(i, total, "Summarizing video " + str(i) + "/" + str(total), None)
    log.info("Summarized %d/%d videos", len(summaries), total)
    return summaries

"""Analyzes transcript chunks against a user query using qwen3:8b via Ollama."""
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

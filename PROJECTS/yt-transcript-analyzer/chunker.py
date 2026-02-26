"""Splits clean transcript files into overlapping token-counted chunks."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNK_TOKENIZER_MODEL,
    CHUNKS_PATH,
    CLEAN_PATH,
    MANIFEST_CHUNKS_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
)

log = logging.getLogger(__name__)


def count_tokens(text: str) -> int:
    """Count tokens via Ollama /api/tokenize using qwen3:8b as reference tokenizer."""
    resp = requests.post(
        OLLAMA_BASE_URL + "/api/tokenize",
        json={"model": CHUNK_TOKENIZER_MODEL, "content": text},
        timeout=OLLAMA_TIMEOUT,
    )
    resp.raise_for_status()
    return len(resp.json()["tokens"])


def split_into_chunks(text: str, source_id: str) -> list:
    """Split text into chunks of up to CHUNK_SIZE tokens with CHUNK_OVERLAP word overlap."""
    words = text.split()
    if not words:
        return []
    chunks = []
    chunk_idx = 0
    start = 0
    while start < len(words):
        # Binary search for max words that fit within CHUNK_SIZE tokens
        lo = 1
        hi = min(len(words) - start, CHUNK_SIZE * 2)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if count_tokens(" ".join(words[start:start + mid])) <= CHUNK_SIZE:
                lo = mid
            else:
                hi = mid - 1
        end = start + lo
        chunk_text = " ".join(words[start:end])
        chunks.append({
            "chunk_id": source_id + "_chunk" + str(chunk_idx).zfill(4),
            "source_id": source_id,
            "chunk_index": chunk_idx,
            "token_count": count_tokens(chunk_text),
            "text": chunk_text,
        })
        chunk_idx += 1
        # Advance start: apply overlap (CHUNK_OVERLAP as approximate word count)
        chunk_word_count = end - start
        if chunk_word_count <= CHUNK_OVERLAP:
            start = end  # chunk smaller than overlap window — no overlap, advance past it
        else:
            start = end - CHUNK_OVERLAP  # step back by overlap
    return chunks


def chunk_file(clean_path: Path) -> list:
    """Chunk a single clean transcript file. Returns list of chunk dicts."""
    text = clean_path.read_text(encoding="utf-8").strip()
    if not text:
        log.warning("Empty file: %s", clean_path.name)
        return []
    source_id = clean_path.stem
    log.debug("Chunking %s", clean_path.name)
    chunks = split_into_chunks(text, source_id)
    log.debug("  %d chunks from %s", len(chunks), clean_path.name)
    return chunks


def chunk_all() -> None:
    """Chunk all files in CLEAN_PATH and write chunk files + manifest_chunks.json."""
    clean_files = list(CLEAN_PATH.glob("*.txt"))
    log.info("Chunking %d clean files", len(clean_files))
    CHUNKS_PATH.mkdir(parents=True, exist_ok=True)
    all_chunks = []
    for clean_file in clean_files:
        try:
            chunks = chunk_file(clean_file)
            for chunk in chunks:
                chunk_path = CHUNKS_PATH / (chunk["chunk_id"] + ".txt")
                chunk_path.write_text(chunk["text"], encoding="utf-8")
            all_chunks.extend(chunks)
        except Exception as exc:
            log.error("Failed to chunk %s: %s", clean_file.name, exc)
    MANIFEST_CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_chunks": len(all_chunks),
        "chunks": all_chunks,
    }
    MANIFEST_CHUNKS_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote manifest_chunks.json (%d chunks)", len(all_chunks))

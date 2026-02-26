"""Configuration constants for yt-transcript-analyzer."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Output root — override via OUTPUT_PATH env var or .env
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "output"))

# Sub-directories
DATA_PATH     = OUTPUT_PATH / "data"
RAW_PATH      = OUTPUT_PATH / "raw"
CLEAN_PATH    = OUTPUT_PATH / "clean"
CHUNKS_PATH   = OUTPUT_PATH / "chunks"
FINDINGS_PATH = OUTPUT_PATH / "findings"
REPORTS_PATH  = OUTPUT_PATH / "reports"

# Data files
ARCHIVE_PATH         = DATA_PATH / "archive.txt"
SKIP_PATH            = DATA_PATH / "skipped.txt"
MANIFEST_VIDEOS_PATH = DATA_PATH / "manifest_videos.json"
MANIFEST_CHUNKS_PATH = DATA_PATH / "manifest_chunks.json"

# Ollama
OLLAMA_BASE_URL       = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
QWEN_MODEL            = "qwen3:8b"
QWEN_THINKING         = True
CHUNK_TOKENIZER_MODEL = "qwen3:8b"
OLLAMA_RETRIES        = 2
OLLAMA_TIMEOUT        = 120  # seconds

# Chunking
CHUNK_SIZE    = 2500  # tokens (safety margin via Ollama tokenizer)
CHUNK_OVERLAP = 200   # tokens (used as approximate word count for overlap step)

# Cleaning
BLOCK_INTERVAL_SECONDS = 30

# Fetcher
YTDLP_RETRIES = 10

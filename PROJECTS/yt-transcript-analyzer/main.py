"""Main pipeline orchestrator for yt-transcript-analyzer."""
import argparse
import logging
import sys
from datetime import datetime, timezone

import startup
import fetcher
import cleaner
import chunker
import analyzer
import reporter
from config import (
    CHUNKS_PATH, CLEAN_PATH, DATA_PATH, FINDINGS_PATH, RAW_PATH, REPORTS_PATH,
)


def ensure_dirs() -> None:
    """Create all required output directories."""
    for path in [DATA_PATH, RAW_PATH, CLEAN_PATH, CHUNKS_PATH, FINDINGS_PATH, REPORTS_PATH]:
        path.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configure pipeline logging to stdout and pipeline.log file."""
    log_file = DATA_PATH / "pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), encoding="utf-8"),
        ],
    )


def main() -> None:
    """Parse arguments and run the requested pipeline stage(s)."""
    parser = argparse.ArgumentParser(description="YouTube Transcript Analyzer")
    parser.add_argument("url", nargs="?", help="YouTube channel or playlist URL")
    parser.add_argument("--query", "-q", help="Search query for analyze/report stages")
    parser.add_argument(
        "--stage",
        choices=["fetch", "clean", "chunk", "analyze", "report", "all"],
        default="all",
        help="Pipeline stage to run (default: all)",
    )
    args = parser.parse_args()

    ensure_dirs()
    setup_logging()

    log = logging.getLogger("main")
    log.info("Pipeline started at %s", datetime.now(timezone.utc).isoformat())

    if not startup.run_checks():
        print("Startup checks failed — fix the above issues and retry.")
        sys.exit(1)

    if args.stage in ("fetch", "all"):
        if not args.url:
            print("URL required for fetch stage.")
            sys.exit(1)
        fetcher.fetch_subtitles(args.url)

    if args.stage in ("clean", "all"):
        cleaner.clean_all()

    if args.stage in ("chunk", "all"):
        chunker.chunk_all()

    if args.stage in ("analyze", "all"):
        if not args.query:
            print("--query required for analyze stage.")
            sys.exit(1)
        analyzer.analyze_all(args.query)

    if args.stage in ("report", "all"):
        if not args.query:
            print("--query required for report stage.")
            sys.exit(1)
        out = reporter.generate_report(args.query)
        print("Report: " + str(out))

    log.info("Pipeline complete at %s", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()

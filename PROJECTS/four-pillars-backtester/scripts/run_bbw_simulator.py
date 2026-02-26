
"""CLI: BBW Simulator Pipeline Runner.

Wires Layers 1-6 together for one or more coins.
Run: python scripts/run_bbw_simulator.py --symbol RIVERUSDT --no-ollama --verbose
"""

import argparse
import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

log = logging.getLogger(__name__)

CACHE_DIR = ROOT / "data" / "cache"
REPORTS_DIR = ROOT / "reports" / "bbw"


def _resample_5m(df):
    """Resample 1m OHLCV DataFrame to 5m candles."""
    if "datetime" not in df.columns:
        if df.index.name == "datetime":
            df = df.reset_index()
    df2 = df.set_index("datetime")
    vol_col = "base_vol" if "base_vol" in df2.columns else (
        "volume" if "volume" in df2.columns else None
    )
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if vol_col:
        agg[vol_col] = "sum"
    return df2.resample("5min").agg(agg).dropna().reset_index()


def _load_coin_data(symbol, timeframe, cache_dir):
    """Load parquet for symbol/timeframe; return DataFrame or None on failure."""
    direct = cache_dir / (symbol + "_" + timeframe + ".parquet")
    if direct.exists():
        try:
            return pd.read_parquet(direct)
        except Exception as e:
            log.error("Failed to load %s: %s", direct.name, e)
            return None

    # Fallback: load 1m and resample
    pfile_1m = cache_dir / (symbol + "_1m.parquet")
    if not pfile_1m.exists():
        matches = sorted(cache_dir.glob(symbol + "_*.parquet"))
        if not matches:
            log.warning("No parquet found for %s", symbol)
            return None
        pfile_1m = matches[0]

    try:
        df = pd.read_parquet(pfile_1m)
    except Exception as e:
        log.error("Failed to load %s: %s", pfile_1m.name, e)
        return None

    if timeframe != "1m":
        try:
            df = _resample_5m(df)
        except Exception as e:
            log.error("Resample failed for %s: %s", symbol, e)
            return None
    return df


def _get_coin_list(args, coin_tiers):
    """Resolve the list of symbols to process from CLI args and tier data."""
    if args.symbol:
        return list(args.symbol)

    if coin_tiers is not None and args.tier is not None:
        filtered = coin_tiers[coin_tiers["tier"] == args.tier]
        symbols = filtered["symbol"].tolist()
        log.info("Tier %d: %d coins", args.tier, len(symbols))
        if args.top:
            symbols = symbols[:args.top]
        return symbols

    # Default: all 1m parquets in cache
    pfiles = sorted(cache_dir.glob("*_1m.parquet"))
    symbols = [p.stem.replace("_1m", "") for p in pfiles]
    if args.top:
        symbols = symbols[:args.top]
    log.info("Using %d coins from cache", len(symbols))
    return symbols


def run_pipeline(args):
    """Run the full BBW pipeline (L1-L6) based on parsed CLI args.

    Returns summary dict with n_coins_processed, n_errors, etc.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    t0 = time.time()

    log.info("=== BBW Simulator Pipeline -- %s ===", ts)

    if args.dry_run:
        log.info("DRY RUN -- no data will be processed")
        return {"dry_run": True, "n_coins_processed": 0, "n_errors": 0,
                "timestamp": ts, "runtime_sec": 0}

    # Import required pipeline modules
    try:
        from signals.bbwp import calculate_bbwp
        from signals.bbw_sequence import track_bbw_sequence
        from research.bbw_forward_returns import tag_forward_returns
        from research.bbw_simulator import run_simulator
        from research.bbw_report import run_report
    except ImportError as e:
        log.error("Import failed: %s", e)
        log.error("Make sure all pipeline modules are present in: %s", ROOT)
        sys.exit(1)

    # Optional: Monte Carlo
    run_monte_carlo_fn = None
    if not args.no_monte_carlo:
        try:
            from research.bbw_monte_carlo import run_monte_carlo as _rmc
            run_monte_carlo_fn = _rmc
        except ImportError as e:
            log.warning("Monte Carlo module not found: %s -- skipping L4b", e)

    # Optional: Ollama review
    run_ollama_fn = None
    if not args.no_ollama:
        try:
            from research.bbw_ollama_review import run_ollama_review as _rov
            run_ollama_fn = _rov
        except ImportError as e:
            log.warning("Ollama review module not found: %s -- skipping L6", e)

    # Load coin tiers if available
    coin_tiers = None
    tiers_path = ROOT / "results" / "coin_tiers.csv"
    if tiers_path.exists():
        try:
            coin_tiers = pd.read_csv(tiers_path)
            log.info("Loaded coin tiers: %d coins", len(coin_tiers))
        except Exception as e:
            log.warning("Failed to load coin tiers: %s", e)

    symbols = _get_coin_list(args, coin_tiers)
    if not symbols:
        log.error("No symbols to process. Check --symbol or cache at %s", CACHE_DIR)
        sys.exit(1)

    preview = ", ".join(str(s) for s in symbols[:5])
    if len(symbols) > 5:
        preview += "..."
    log.info("Processing %d coin(s): %s", len(symbols), preview)

    processed_dfs = []
    n_errors = 0

    for i, symbol in enumerate(symbols, 1):
        log.info("[%d/%d] %s", i, len(symbols), symbol)
        t_coin = time.time()
        try:
            df = _load_coin_data(symbol, args.timeframe, CACHE_DIR)
            if df is None:
                log.warning("SKIP %s: no data", symbol)
                n_errors += 1
                continue

            df = calculate_bbwp(df)
            df = track_bbw_sequence(df)
            df = tag_forward_returns(df)

            processed_dfs.append(df)
            log.info("  OK %s (%d bars, %.1fs)", symbol, len(df), time.time() - t_coin)

        except Exception as e:
            log.error("FAIL %s: %s", symbol, e)
            log.debug(traceback.format_exc())
            n_errors += 1
            continue

    if not processed_dfs:
        log.error("Zero coins processed successfully.")
        sys.exit(1)

    log.info("Combining %d DataFrames for L4...", len(processed_dfs))
    combined_df = pd.concat(processed_dfs, ignore_index=True)
    log.info("Combined shape: %s", str(combined_df.shape))

    # L4: Simulator
    log.info("Running L4 (Simulator)...")
    t_l4 = time.time()
    layer4_result = run_simulator(combined_df)
    log.info("L4 done: %.1fs", time.time() - t_l4)

    # L4b: Monte Carlo (optional)
    layer4b_result = None
    if run_monte_carlo_fn is not None:
        log.info("Running L4b (Monte Carlo, n_sims=%d)...", args.mc_sims)
        t_l4b = time.time()
        try:
            layer4b_result = run_monte_carlo_fn(combined_df, layer4_result.lsg_top)
            log.info("L4b done: %.1fs", time.time() - t_l4b)
        except Exception as e:
            log.error("L4b failed: %s", e)
            log.debug(traceback.format_exc())

    # L5: Report
    log.info("Running L5 (Report)...")
    t_l5 = time.time()
    report_result = run_report(
        layer4_result,
        layer4b_result,
        output_dir=str(args.output_dir),
        coin_tiers=coin_tiers,
        verbose=args.verbose,
    )
    n_reports = len(report_result.get("reports_written", []))
    log.info("L5 done: %.1fs -- %d files, %d errors",
             time.time() - t_l5, n_reports, len(report_result.get("errors", [])))

    # L6: Ollama review (optional)
    if run_ollama_fn is not None:
        log.info("Running L6 (Ollama review, model=%s)...", args.ollama_model)
        t_l6 = time.time()
        try:
            ollama_result = run_ollama_fn(
                reports_dir=str(args.output_dir),
                output_dir=str(Path(args.output_dir) / "ollama"),
                model=args.ollama_model,
                verbose=args.verbose,
            )
            log.info("L6 done: %.1fs -- %d files",
                     time.time() - t_l6, len(ollama_result.get("files_written", [])))
        except Exception as e:
            log.error("L6 failed: %s", e)
            log.debug(traceback.format_exc())

    runtime = time.time() - t0
    summary = {
        "timestamp": ts,
        "n_coins_processed": len(processed_dfs),
        "n_errors": n_errors,
        "n_reports": n_reports,
        "runtime_sec": round(runtime, 2),
    }
    log.info("=== DONE: %d OK  %d errors  %d reports  %.1fs ===",
             summary["n_coins_processed"], summary["n_errors"],
             summary["n_reports"], summary["runtime_sec"])
    return summary


def _build_parser():
    """Build and return the CLI argparse ArgumentParser."""
    p = argparse.ArgumentParser(
        description="BBW Simulator Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--symbol", nargs="+", help="Coin symbol(s) to process")
    p.add_argument("--tier", type=int, help="Volatility tier to process (0-3)")
    p.add_argument("--timeframe", default="5m",
                   help="Candle timeframe (default: 5m)")
    p.add_argument("--top", type=int,
                   help="Process top N coins only")
    p.add_argument("--no-monte-carlo", action="store_true",
                   help="Skip Layer 4b Monte Carlo validation")
    p.add_argument("--mc-sims", type=int, default=1000,
                   help="Monte Carlo simulations (default: 1000)")
    p.add_argument("--no-ollama", action="store_true",
                   help="Skip Layer 6 Ollama review")
    p.add_argument("--ollama-model", default="qwen3:8b",
                   help="Ollama model for Layer 6 (default: qwen3:8b)")
    p.add_argument("--output-dir", default=str(REPORTS_DIR),
                   help="Output directory for reports")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse args and exit without processing")
    return p


def main():
    """Entry point: parse args and run pipeline."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = _build_parser()
    args = parser.parse_args()
    args.output_dir = Path(args.output_dir)
    run_pipeline(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

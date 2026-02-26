"""Bridge script: Dashboard CSV to BBW V2 Pipeline.

Takes a portfolio_trades CSV exported from dashboard_v391.py and runs
the full V2 BBW pipeline (L4v2 -> L4bv2 -> L5) to generate VINCE features.

Run:
  python scripts/run_bbw_v2_pipeline.py \
    --trades-csv "results/portfolio_trades_XXXXXXXX.csv" \
    --output-dir "results/bbw_v2"
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

CACHE_DIR = ROOT / "data" / "cache"

log = logging.getLogger(__name__)

# --- Backtester exit_reason -> L4v2 outcome mapping ---
OUTCOME_MAP = {
    "SL":  "SL",
    "TP":  "TP",
    "END": "TIMEOUT",
}

# --- Required columns in dashboard CSV export ---
REQUIRED_CSV_COLS = [
    "symbol", "entry_datetime", "direction",
    "entry_price", "exit_price",
    "pnl", "commission", "net_pnl",
    "exit_reason", "entry_bar", "exit_bar",
]


# =============================================================================
# COLUMN ADAPTATION
# =============================================================================

def load_dashboard_csv(path: Path) -> pd.DataFrame:
    """Load and basic-validate dashboard portfolio_trades CSV."""
    if not path.exists():
        raise FileNotFoundError("Trades CSV not found: " + str(path))
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_CSV_COLS if c not in df.columns]
    if missing:
        raise ValueError("Missing columns in trades CSV: " + ", ".join(missing))
    log.info("Loaded %d trades from %s", len(df), path.name)
    return df


def adapt_columns(
    df: pd.DataFrame,
    leverage: float,
    size: float,
    grid: float,
    rebate_rate: float = 0.0,
) -> pd.DataFrame:
    """Rename and derive columns to match bbw_analyzer_v2 expected format.

    Maps dashboard export column names to L4v2 required column names,
    injects constant leverage/size/grid, derives bars_held, and applies
    daily rebate credit to pnl_net so BBW analysis reflects true economics.

    Rebate note: dashboard CSV net_pnl has no rebate applied (rebate settles
    daily at portfolio level). Applying rebate_rate here credits it back
    per-trade so be_plus_fees_rate reflects real profitability.
    """
    out = df.copy()

    # Rename column mismatches
    out = out.rename(columns={
        "entry_datetime": "timestamp",
        "pnl":            "pnl_gross",
        "net_pnl":        "pnl_net",
        "commission":     "commission_rt",
        "exit_reason":    "outcome",
    })

    # Parse timestamp — force UTC
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)

    # Derive bars_held from bar indices (minimum 1)
    out["bars_held"] = (out["exit_bar"] - out["entry_bar"]).clip(lower=1)

    # Map outcome values
    out["outcome"] = out["outcome"].map(OUTCOME_MAP).fillna("TIMEOUT")

    # Normalise direction to uppercase
    out["direction"] = out["direction"].str.upper().str.strip()

    # Inject constants — single LSG configuration from dashboard run
    out["leverage"] = float(leverage)
    out["size"]     = float(size)
    out["grid"]     = float(grid)

    # Apply rebate: credit rebate_rate × commission back into pnl_net per trade
    # This reflects true economics — without rebate, commission_kill verdicts
    # are overstated because the daily rebate settlement is not in the CSV.
    if rebate_rate > 0.0:
        rebate_per_trade = out["commission_rt"] * rebate_rate
        out["pnl_net"] = out["pnl_net"] + rebate_per_trade
        total_rebate = rebate_per_trade.sum()
        log.info(
            "Rebate applied: %.0f%% rate | avg $%.2f/trade | total $%.2f across %d trades",
            rebate_rate * 100,
            rebate_per_trade.mean(),
            total_rebate,
            len(out),
        )

    log.info(
        "Adapted columns: %d trades, %d symbols, leverage=%.0f size=%.0f grid=%.1f rebate=%.0f%%",
        len(out), out["symbol"].nunique(), leverage, size, grid, rebate_rate * 100,
    )
    return out


# =============================================================================
# BBW STATE LOADER (L1 per coin)
# =============================================================================

def _resample_to_5m(df: pd.DataFrame) -> pd.DataFrame:
    """Resample 1m OHLCV DataFrame to 5m candles."""
    if "datetime" not in df.columns:
        if df.index.name == "datetime":
            df = df.reset_index()
    df2 = df.set_index("datetime")
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    vol_col = next((c for c in ["base_vol", "volume"] if c in df2.columns), None)
    if vol_col:
        agg[vol_col] = "sum"
    return df2.resample("5min").agg(agg).dropna().reset_index()


def load_bbw_states_for_symbol(symbol: str, timeframe: str = "5m") -> pd.DataFrame:
    """Load OHLCV for symbol from cache, run L1 BBWP, return BBW states DataFrame.

    Returns DataFrame with columns: timestamp (UTC), symbol, bbwp_state, bbwp_value.
    Returns None if no cache found.
    """
    from signals.bbwp import calculate_bbwp

    p_native = CACHE_DIR / (symbol + "_" + timeframe + ".parquet")
    p_1m     = CACHE_DIR / (symbol + "_1m.parquet")

    if p_native.exists():
        df = pd.read_parquet(p_native)
    elif p_1m.exists():
        df = pd.read_parquet(p_1m)
        if timeframe != "1m":
            df = _resample_to_5m(df)
    else:
        log.warning("SKIP %s: no parquet found in cache", symbol)
        return None

    # Ensure datetime column exists
    if "datetime" not in df.columns:
        if df.index.name == "datetime":
            df = df.reset_index()
        else:
            log.warning("SKIP %s: no datetime column found", symbol)
            return None

    # Run L1 BBWP
    df = calculate_bbwp(df)

    # Extract only the columns needed for the join
    states = df[["datetime", "bbwp_state", "bbwp_value"]].copy()
    states = states.rename(columns={"datetime": "timestamp"})
    states["timestamp"] = pd.to_datetime(states["timestamp"], utc=True)
    states["symbol"] = symbol
    states = states.dropna(subset=["bbwp_state", "bbwp_value"])

    log.info("  %s: %d bars with BBW states", symbol, len(states))
    return states


# =============================================================================
# PIPELINE RUNNER
# =============================================================================

def run_pipeline(
    trades_csv: Path,
    output_dir: Path,
    leverage: float,
    size: float,
    grid: float,
    timeframe: str,
    n_sims: int,
    skip_mc: bool,
    min_trades: int,
    rebate_rate: float = 0.0,
) -> dict:
    """Run full BBW V2 pipeline: CSV adapter -> L4v2 -> L4bv2 -> L5 -> CSVs.

    Returns summary dict with counts and file paths.
    """
    from research.bbw_analyzer_v2 import analyze_bbw_patterns_v2
    from research.bbw_monte_carlo_v2 import run_monte_carlo_v2
    from research.bbw_report_v2 import generate_vince_features_v2

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    t0 = time.time()
    log.info("=== BBW V2 Pipeline === %s", ts)

    # Step 1: Load and adapt dashboard CSV
    trades_raw = load_dashboard_csv(trades_csv)
    trades = adapt_columns(trades_raw, leverage, size, grid, rebate_rate=rebate_rate)
    symbols = sorted(trades["symbol"].unique().tolist())
    log.info("Symbols to process (%d): %s", len(symbols), ", ".join(symbols))

    # Step 2: Load BBW states per symbol via L1 BBWP
    all_states = []
    for symbol in symbols:
        states = load_bbw_states_for_symbol(symbol, timeframe)
        if states is not None:
            all_states.append(states)

    if not all_states:
        log.error("No BBW states loaded — check cache dir: %s", CACHE_DIR)
        sys.exit(1)

    bbw_states = pd.concat(all_states, ignore_index=True)
    log.info("Total BBW state bars: %d across %d symbols", len(bbw_states), len(all_states))

    # Step 3: L4v2 — Analyze backtester results by BBW state
    log.info("Running L4v2 (Analyzer, min_trades_per_group=%d)...", min_trades)
    t_l4 = time.time()
    try:
        analysis_result = analyze_bbw_patterns_v2(
            backtester_results=trades,
            bbw_states=bbw_states,
            min_trades_per_group=min_trades,
        )
    except Exception as e:
        log.error("L4v2 failed: %s", e)
        log.debug(traceback.format_exc())
        sys.exit(1)

    log.info(
        "L4v2 done: %.1fs | %d states | %d groups | %d best combos",
        time.time() - t_l4,
        analysis_result.n_states,
        len(analysis_result.results),
        len(analysis_result.best_combos),
    )

    # Step 4: L4bv2 — Monte Carlo validation (optional)
    mc_result = None
    if not skip_mc and not analysis_result.best_combos.empty:
        log.info("Running L4bv2 (Monte Carlo, n_sims=%d)...", n_sims)
        t_l4b = time.time()
        try:
            mc_result = run_monte_carlo_v2(analysis_result, n_sims=n_sims)
            log.info(
                "L4bv2 done: %.1fs | ROBUST=%d FRAGILE=%d COMMISSION_KILL=%d INSUFFICIENT=%d",
                time.time() - t_l4b,
                mc_result.summary.get("n_robust", 0),
                mc_result.summary.get("n_fragile", 0),
                mc_result.summary.get("n_commission_kill", 0),
                mc_result.summary.get("n_insufficient", 0),
            )
        except Exception as e:
            log.error("L4bv2 failed: %s — continuing without MC verdicts", e)
            log.debug(traceback.format_exc())
    elif skip_mc:
        log.info("Monte Carlo skipped (--skip-mc)")
    else:
        log.warning("No best_combos — skipping Monte Carlo")

    # Step 5: L5 — Generate VINCE features and write CSVs
    log.info("Running L5 (Report)...")
    t_l5 = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        report = generate_vince_features_v2(
            analysis_result=analysis_result,
            mc_result=mc_result,
            output_dir=str(output_dir),
        )
    except Exception as e:
        log.error("L5 failed: %s", e)
        log.debug(traceback.format_exc())
        sys.exit(1)

    log.info(
        "L5 done: %.1fs | %d states | %d feature rows",
        time.time() - t_l5,
        report.summary.get("n_states", 0),
        report.summary.get("n_features", 0),
    )

    # Report output files
    csv_names = [
        "vince_features.csv",
        "directional_bias.csv",
        "be_fees_success.csv",
        "lsg_sensitivity.csv",
        "state_summary.csv",
    ]
    written = []
    for name in csv_names:
        p = output_dir / name
        if p.exists():
            written.append(str(p))
            log.info("  WROTE: %s (%d bytes)", name, p.stat().st_size)
        else:
            log.warning("  MISSING: %s", name)

    runtime = round(time.time() - t0, 1)
    log.info("=== DONE: %d CSVs written in %.1fs ===", len(written), runtime)

    return {
        "timestamp": ts,
        "n_trades": len(trades),
        "n_symbols": len(symbols),
        "n_states": report.summary.get("n_states", 0),
        "n_features": report.summary.get("n_features", 0),
        "files_written": written,
        "runtime_sec": runtime,
    }


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    p = argparse.ArgumentParser(
        description="BBW V2 Pipeline — Dashboard CSV to VINCE features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--trades-csv", required=True,
        help="Path to dashboard portfolio_trades_*.csv export",
    )
    p.add_argument(
        "--output-dir", default="results/bbw_v2",
        help="Output directory for VINCE feature CSVs (default: results/bbw_v2)",
    )
    p.add_argument(
        "--leverage", type=float, default=20.0,
        help="Leverage used in dashboard run (default: 20)",
    )
    p.add_argument(
        "--size", type=float, default=500.0,
        help="Margin per position in USD used in dashboard run (default: 500)",
    )
    p.add_argument(
        "--grid", type=float, default=1.0,
        help="Grid constant — single config, no LSG sweep (default: 1.0)",
    )
    p.add_argument(
        "--timeframe", default="5m",
        help="OHLCV timeframe for BBW state calculation (default: 5m)",
    )
    p.add_argument(
        "--mc-sims", type=int, default=1000,
        help="Monte Carlo simulations for L4bv2 (default: 1000)",
    )
    p.add_argument(
        "--skip-mc", action="store_true",
        help="Skip Monte Carlo validation (faster, verdicts will be UNKNOWN)",
    )
    p.add_argument(
        "--min-trades", type=int, default=50,
        help="Minimum trades per (state, direction) group (default: 50)",
    )
    p.add_argument(
        "--rebate-rate", type=float, default=0.0,
        help="Daily rebate rate to credit back into pnl_net per trade (e.g. 0.70 for 70%% rebate account). Default: 0.0 (no rebate).",
    )
    p.add_argument(
        "--verbose", action="store_true",
        help="Enable DEBUG logging",
    )
    return p


def main() -> int:
    """Entry point: parse args and run pipeline."""
    parser = _build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    run_pipeline(
        trades_csv=Path(args.trades_csv),
        output_dir=Path(args.output_dir),
        leverage=args.leverage,
        size=args.size,
        grid=args.grid,
        timeframe=args.timeframe,
        n_sims=args.mc_sims,
        skip_mc=args.skip_mc,
        min_trades=args.min_trades,
        rebate_rate=args.rebate_rate,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

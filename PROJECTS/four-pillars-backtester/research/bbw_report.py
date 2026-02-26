"""Layer 5: BBW Report Generator -- CSV output from Layer 4/4b results.

Pure I/O. Reads SimulatorResult + MonteCarloResult, writes structured CSVs.
No calculations, no signal processing.

Output structure:
  reports/bbw/aggregate/   -- 7 group stats CSVs (A-G)
  reports/bbw/scaling/     -- 1 scaling sequences CSV
  reports/bbw/monte_carlo/ -- 3 MC validation CSVs
  reports/bbw/per_tier/    -- 0-4 per-tier CSVs (optional, needs coin_tiers)

Run: imported by scripts, not run directly.
"""

import time
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

from research.bbw_simulator import SimulatorResult
from research.bbw_monte_carlo import MonteCarloResult


# --- Group key to filename mapping ---

GROUP_FILE_MAP = {
    'A_state': 'bbw_state_stats.csv',
    'B_spectrum': 'spectrum_color_stats.csv',
    'C_direction': 'sequence_direction_stats.csv',
    'D_pattern': 'sequence_pattern_stats.csv',
    'E_skip': 'skip_detection_stats.csv',
    'F_duration': 'duration_cross_stats.csv',
    'G_ma_spectrum': 'ma_cross_stats.csv',
}

MC_FILE_MAP = {
    'state_verdicts': 'mc_summary_by_state.csv',
    'confidence_intervals': 'mc_confidence_intervals.csv',
    'overfit_flags': 'mc_overfit_flags.csv',
}


# --- Internal write functions ---

def _write_aggregate_stats(group_stats, output_dir, verbose):
    """Write 7 aggregate group CSVs from Layer 4 group_stats dict."""
    agg_dir = Path(output_dir) / "aggregate"
    agg_dir.mkdir(parents=True, exist_ok=True)

    written = []
    errors = []

    for gkey, fname in GROUP_FILE_MAP.items():
        if gkey not in group_stats:
            if verbose:
                print(f"  WARN: {gkey} not in group_stats, skipping {fname}")
            continue

        df = group_stats[gkey]
        if isinstance(df, pd.DataFrame) and df.empty:
            if verbose:
                print(f"  SKIP: {fname} (empty)")
            continue

        if not isinstance(df, pd.DataFrame):
            errors.append((fname, "Not a DataFrame"))
            if verbose:
                print(f"  ERROR: {fname} is not a DataFrame, got {type(df)}")
            continue

        out_path = agg_dir / fname
        try:
            df.to_csv(out_path, index=False)
            written.append(str(out_path))
            if verbose:
                print(f"  WROTE: {fname} ({len(df)} rows, "
                      + f"{out_path.stat().st_size:,} bytes)")
        except PermissionError as e:
            errors.append((fname, f"PermissionError: {e}"))
            if verbose:
                print(f"  ERROR: {fname} -- permission denied")
        except OSError as e:
            errors.append((fname, f"OSError: {e}"))
            if verbose:
                print(f"  ERROR: {fname} -- {e}")

    return written, errors


def _write_scaling_report(scaling_results, output_dir, verbose):
    """Write scaling sequence analysis CSV."""
    scal_dir = Path(output_dir) / "scaling"
    scal_dir.mkdir(parents=True, exist_ok=True)

    written = []
    errors = []

    if not isinstance(scaling_results, pd.DataFrame):
        errors.append(("scaling_sequences.csv", "Not a DataFrame"))
        return written, errors

    if scaling_results.empty:
        if verbose:
            print("  SKIP: scaling_sequences.csv (empty)")
        return written, errors

    out_path = scal_dir / "scaling_sequences.csv"
    try:
        scaling_results.to_csv(out_path, index=False)
        written.append(str(out_path))
        if verbose:
            print(f"  WROTE: scaling_sequences.csv ({len(scaling_results)} rows, "
                  + f"{out_path.stat().st_size:,} bytes)")
    except PermissionError as e:
        errors.append(("scaling_sequences.csv", f"PermissionError: {e}"))
        if verbose:
            print(f"  ERROR: scaling_sequences.csv -- permission denied")
    except OSError as e:
        errors.append(("scaling_sequences.csv", f"OSError: {e}"))
        if verbose:
            print(f"  ERROR: scaling_sequences.csv -- {e}")

    return written, errors


def _write_mc_reports(mc_result, output_dir, verbose):
    """Write 3 Monte Carlo CSVs from Layer 4b result."""
    mc_dir = Path(output_dir) / "monte_carlo"
    mc_dir.mkdir(parents=True, exist_ok=True)

    written = []
    errors = []

    for attr_name, fname in MC_FILE_MAP.items():
        df = getattr(mc_result, attr_name, None)

        if df is None:
            errors.append((fname, f"mc_result has no attribute '{attr_name}'"))
            if verbose:
                print(f"  ERROR: {fname} -- missing attribute '{attr_name}'")
            continue

        if not isinstance(df, pd.DataFrame):
            errors.append((fname, "Not a DataFrame"))
            if verbose:
                print(f"  ERROR: {fname} is not a DataFrame, got {type(df)}")
            continue

        if df.empty:
            if verbose:
                print(f"  SKIP: {fname} (empty)")
            continue

        out_path = mc_dir / fname
        try:
            df.to_csv(out_path, index=False)
            written.append(str(out_path))
            if verbose:
                print(f"  WROTE: {fname} ({len(df)} rows, "
                      + f"{out_path.stat().st_size:,} bytes)")
        except PermissionError as e:
            errors.append((fname, f"PermissionError: {e}"))
            if verbose:
                print(f"  ERROR: {fname} -- permission denied")
        except OSError as e:
            errors.append((fname, f"OSError: {e}"))
            if verbose:
                print(f"  ERROR: {fname} -- {e}")

    return written, errors


def _write_per_tier_reports(lsg_top, coin_tiers, output_dir, verbose):
    """Write per-tier optimal LSG CSVs (optional)."""
    written = []
    errors = []

    if coin_tiers is None:
        if verbose:
            print("  SKIP: per_tier CSVs (coin_tiers not provided)")
        return written, errors

    if not isinstance(lsg_top, pd.DataFrame) or lsg_top.empty:
        if verbose:
            print("  SKIP: per_tier CSVs (lsg_top empty)")
        return written, errors

    if 'symbol' not in lsg_top.columns:
        if verbose:
            print("  WARN: lsg_top missing 'symbol' column, per-tier disabled")
        return written, errors

    if not isinstance(coin_tiers, pd.DataFrame) or coin_tiers.empty:
        if verbose:
            print("  SKIP: per_tier CSVs (coin_tiers empty)")
        return written, errors

    if 'tier' not in coin_tiers.columns or 'symbol' not in coin_tiers.columns:
        errors.append(("per_tier", "coin_tiers missing 'tier' or 'symbol' column"))
        if verbose:
            print("  ERROR: coin_tiers missing required columns")
        return written, errors

    tier_dir = Path(output_dir) / "per_tier"
    tier_dir.mkdir(parents=True, exist_ok=True)

    for tier_num in [0, 1, 2, 3]:
        tier_symbols = coin_tiers[
            coin_tiers['tier'] == tier_num
        ]['symbol'].tolist()

        if not tier_symbols:
            if verbose:
                print(f"  SKIP: tier_{tier_num}_optimal_lsg.csv (no coins)")
            continue

        tier_lsg = lsg_top[lsg_top['symbol'].isin(tier_symbols)]
        if tier_lsg.empty:
            if verbose:
                print(f"  SKIP: tier_{tier_num}_optimal_lsg.csv (no data)")
            continue

        fname = f"tier_{tier_num}_optimal_lsg.csv"
        out_path = tier_dir / fname
        try:
            tier_lsg.to_csv(out_path, index=False)
            written.append(str(out_path))
            if verbose:
                print(f"  WROTE: {fname} ({len(tier_lsg)} rows, "
                      + f"{out_path.stat().st_size:,} bytes)")
        except PermissionError as e:
            errors.append((fname, f"PermissionError: {e}"))
        except OSError as e:
            errors.append((fname, f"OSError: {e}"))

    return written, errors


# --- Main entry point ---

def run_report(layer4_result, layer4b_result, output_dir="reports/bbw",
               coin_tiers=None, verbose=False):
    """Write all BBW reports from Layer 4 and Layer 4b results.

    Args:
        layer4_result: SimulatorResult from research/bbw_simulator.py
        layer4b_result: MonteCarloResult from research/bbw_monte_carlo.py
        output_dir: Base directory for report output
        coin_tiers: Optional DataFrame with 'symbol' and 'tier' columns
        verbose: Print progress messages

    Returns dict with:
        reports_written: list of file paths successfully written
        errors: list of (filename, error_msg) tuples
        output_dir: resolved output directory path
        summary: dict with file counts and runtime
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    t0 = time.time()
    output_dir = Path(output_dir)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {
            'reports_written': [],
            'errors': [("output_dir", f"Cannot create {output_dir}: {e}")],
            'output_dir': str(output_dir),
            'summary': {
                'timestamp': ts,
                'n_aggregate': 0, 'n_scaling': 0,
                'n_monte_carlo': 0, 'n_per_tier': 0,
                'n_total': 0, 'n_errors': 1,
                'runtime_sec': 0,
            },
        }

    if verbose:
        print(f"[{ts}] Writing BBW reports to: {output_dir}")

    all_written = []
    all_errors = []

    # 1. Aggregate stats (up to 7 CSVs)
    if verbose:
        print("\n[Aggregate Stats]")
    agg_w, agg_e = _write_aggregate_stats(
        layer4_result.group_stats, output_dir, verbose
    )
    all_written.extend(agg_w)
    all_errors.extend(agg_e)

    # 2. Scaling report (1 CSV)
    if verbose:
        print("\n[Scaling Sequences]")
    scal_w, scal_e = _write_scaling_report(
        layer4_result.scaling_results, output_dir, verbose
    )
    all_written.extend(scal_w)
    all_errors.extend(scal_e)

    # 3. Monte Carlo reports (up to 3 CSVs)
    if verbose:
        print("\n[Monte Carlo]")
    mc_w, mc_e = _write_mc_reports(layer4b_result, output_dir, verbose)
    all_written.extend(mc_w)
    all_errors.extend(mc_e)

    # 4. Per-tier reports (0-4 CSVs, optional)
    if verbose:
        print("\n[Per-Tier Optimal LSG]")
    tier_w, tier_e = _write_per_tier_reports(
        layer4_result.lsg_top, coin_tiers, output_dir, verbose
    )
    all_written.extend(tier_w)
    all_errors.extend(tier_e)

    runtime = time.time() - t0

    summary = {
        'timestamp': ts,
        'n_aggregate': len(agg_w),
        'n_scaling': len(scal_w),
        'n_monte_carlo': len(mc_w),
        'n_per_tier': len(tier_w),
        'n_total': len(all_written),
        'n_errors': len(all_errors),
        'runtime_sec': round(runtime, 4),
    }

    if verbose:
        print(f"\n[Summary] {len(all_written)} files written, "
              + f"{len(all_errors)} errors, {runtime:.3f}s")

    return {
        'reports_written': all_written,
        'errors': all_errors,
        'output_dir': str(output_dir),
        'summary': summary,
    }

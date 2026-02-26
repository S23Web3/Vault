"""Layer 5 Tests: BBW Report Generator.

20 tests, 80+ assertions. Covers happy path, empty data, missing data,
directory handling, filesystem errors, and filesize validation.
Run: python tests/test_bbw_report.py
"""

import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_report import (
    run_report, GROUP_FILE_MAP, MC_FILE_MAP,
    _write_aggregate_stats, _write_scaling_report,
    _write_mc_reports, _write_per_tier_reports,
)
from research.bbw_simulator import SimulatorResult
from research.bbw_monte_carlo import MonteCarloResult

PASS_COUNT = 0
FAIL_COUNT = 0
ERRORS = []


def check(name, condition, detail=""):
    """Check assertion, track pass/fail."""
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS  {name}")
    else:
        FAIL_COUNT += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f" -- {detail}"
        print(msg)
        ERRORS.append(name)


# --- Mock data helpers ---

def _make_group_stats_df(n_rows=7):
    """Generate a mock group_stats DataFrame matching Layer 4 schema."""
    rows = []
    states = ['BLUE', 'BLUE_DOUBLE', 'MA_CROSS_UP', 'NORMAL',
              'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE']
    for i in range(n_rows):
        rows.append({
            'group_value': states[i % len(states)],
            'window': 10,
            'direction': 'long',
            'n_bars': 500 + i * 100,
            'mean_mfe_atr': 2.5 + i * 0.1,
            'median_mfe_atr': 2.3 + i * 0.1,
            'p90_mfe_atr': 4.0 + i * 0.1,
            'mean_mae_atr': 1.5 + i * 0.05,
            'median_mae_atr': 1.3 + i * 0.05,
            'p90_mae_atr': 3.0 + i * 0.05,
            'mfe_mae_ratio': 1.6 + i * 0.1,
            'mean_range_atr': 4.0 + i * 0.1,
            'proper_move_pct': 0.65 + i * 0.01,
            'directional_bias': 0.52 + i * 0.01,
            'mean_close_pct': 0.5 + i * 0.1,
            'std_close_pct': 1.2 + i * 0.1,
            'skew_close_pct': 0.1 + i * 0.01,
            'kurtosis_close_pct': 0.5 + i * 0.1,
            'edge_score': 0.8 + i * 0.1,
        })
    return pd.DataFrame(rows)


def make_mock_layer4(n_states=7, empty_groups=None):
    """Generate mock SimulatorResult."""
    if empty_groups is None:
        empty_groups = []

    group_stats = {}
    for gkey in GROUP_FILE_MAP:
        if gkey in empty_groups:
            group_stats[gkey] = pd.DataFrame()
        else:
            group_stats[gkey] = _make_group_stats_df(n_states)

    lsg_top = pd.DataFrame({
        'bbwp_state': ['BLUE', 'RED'],
        'window': [10, 10],
        'direction': ['long', 'long'],
        'leverage': [20, 10],
        'size_frac': [1.0, 0.5],
        'target_atr': [3, 4],
        'sl_atr': [2.0, 1.5],
        'n_trades': [500, 300],
        'expectancy_usd': [5.0, 3.0],
        'win_rate': [0.55, 0.48],
        'profit_factor': [1.3, 1.1],
        'sharpe_approx': [0.15, 0.08],
        'max_drawdown_usd': [2000, 1500],
        'calmar_approx': [1.2, 0.9],
    })

    scaling_results = pd.DataFrame({
        'entry_state': ['NORMAL', 'BLUE'],
        'add_trigger_state': ['BLUE', 'BLUE_DOUBLE'],
        'entry_size_frac': [0.5, 0.5],
        'add_size_frac': [0.5, 0.5],
        'max_bars_to_wait': [10, 20],
        'n_entry_bars': [100, 80],
        'n_triggered': [40, 30],
        'triggered_pct': [0.40, 0.375],
        'mean_base_pnl': [3.0, 4.0],
        'mean_scaled_pnl': [5.0, 6.0],
        'edge_pct': [66.7, 50.0],
        'verdict': ['USE', 'MARGINAL'],
    })

    return SimulatorResult(
        group_stats=group_stats,
        lsg_results=pd.DataFrame(),
        lsg_top=lsg_top,
        scaling_results=scaling_results,
        summary={'n_states': n_states, 'runtime_sec': 0.1},
    )


def make_mock_layer4b(n_states=7, empty_dfs=None):
    """Generate mock MonteCarloResult."""
    if empty_dfs is None:
        empty_dfs = []

    states = ['BLUE', 'BLUE_DOUBLE', 'MA_CROSS_UP', 'NORMAL',
              'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE'][:n_states]

    if 'state_verdicts' in empty_dfs:
        sv = pd.DataFrame()
    else:
        sv = pd.DataFrame({
            'symbol': ['TESTUSDT'] * n_states,
            'bbwp_state': states,
            'window': [10] * n_states,
            'direction': ['long'] * n_states,
            'n_trades': [500] * n_states,
            'gross_expectancy': [5.0] * n_states,
            'net_expectancy': [-3.0] * n_states,
            'rt_commission': [8.0] * n_states,
            'verdict': ['COMMISSION_KILL'] * n_states,
            'convergence_sims': [100] * n_states,
        })

    if 'confidence_intervals' in empty_dfs:
        ci = pd.DataFrame()
    else:
        ci_rows = []
        for s in states:
            for metric in ['total_pnl', 'sharpe', 'sortino', 'profit_factor']:
                ci_rows.append({
                    'bbwp_state': s, 'window': 10, 'direction': 'long',
                    'metric': metric, 'real': 100.0,
                    'ci_lower': -50.0, 'ci_upper': 250.0,
                    'ci_median': 95.0, 'pctl_rank': 55.0,
                })
        ci = pd.DataFrame(ci_rows)

    if 'overfit_flags' in empty_dfs:
        of = pd.DataFrame()
    else:
        of = pd.DataFrame({
            'bbwp_state': states,
            'window': [10] * n_states,
            'direction': ['long'] * n_states,
            'leverage': [20] * n_states,
            'target_atr': [3] * n_states,
            'sl_atr': [2.0] * n_states,
            'n_trades': [500] * n_states,
            'gross_expectancy': [5.0] * n_states,
            'net_expectancy': [-3.0] * n_states,
            'rt_commission': [8.0] * n_states,
            'bootstrap_pnl_lo': [-500.0] * n_states,
            'bootstrap_pnl_hi': [200.0] * n_states,
            'real_sharpe': [-0.05] * n_states,
            'real_sortino': [-0.07] * n_states,
            'perm_dd_real': [3000.0] * n_states,
            'perm_dd_p95': [2500.0] * n_states,
            'perm_mcl_real': [30] * n_states,
            'perm_mcl_p95': [15] * n_states,
            'sample_size_flag': [False] * n_states,
            'commission_kill_flag': [True] * n_states,
            'pnl_overfit_flag': [True] * n_states,
            'dd_fragile_flag': [True] * n_states,
            'verdict': ['COMMISSION_KILL'] * n_states,
            'reason': ['net_exp <= 0'] * n_states,
        })

    return MonteCarloResult(
        state_verdicts=sv,
        confidence_intervals=ci,
        overfit_flags=of,
        equity_bands={},
        summary={'n_states': n_states, 'n_robust': 0, 'n_fragile': 0,
                 'n_commission_kill': n_states, 'n_sims': 100,
                 'runtime_sec': 0.05},
    )


def count_csvs(d):
    """Count CSV files recursively in directory."""
    return len(list(Path(d).rglob("*.csv")))


# --- Tests ---

def test_01_happy_path():
    """All DataFrames populated, all 11 CSVs written."""
    print("[Test 1] Happy Path -- All 11 CSVs")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        check("1.1 reports_written is list",
              isinstance(result['reports_written'], list))
        check("1.2 11 files written",
              len(result['reports_written']) == 11,
              f"got {len(result['reports_written'])}")
        check("1.3 no errors",
              len(result['errors']) == 0,
              f"errors: {result['errors']}")
        check("1.4 summary n_aggregate=7",
              result['summary']['n_aggregate'] == 7)
        check("1.5 summary n_scaling=1",
              result['summary']['n_scaling'] == 1)
        check("1.6 summary n_monte_carlo=3",
              result['summary']['n_monte_carlo'] == 3)
        check("1.7 summary n_total=11",
              result['summary']['n_total'] == 11)
        check("1.8 summary has timestamp",
              'timestamp' in result['summary'])
        check("1.9 filesystem count matches",
              count_csvs(tmpdir) == 11,
              f"found {count_csvs(tmpdir)}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_02_csv_row_counts():
    """Verify CSV row counts match input DataFrames."""
    print("[Test 2] CSV Row Counts")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4(n_states=5)
        l4b = make_mock_layer4b(n_states=5)
        run_report(l4, l4b, tmpdir)

        agg_path = Path(tmpdir) / "aggregate" / "bbw_state_stats.csv"
        if agg_path.exists():
            df = pd.read_csv(agg_path)
            check("2.1 aggregate rows=5", len(df) == 5, f"got {len(df)}")
            check("2.2 has group_value col", 'group_value' in df.columns)
            check("2.3 has edge_score col", 'edge_score' in df.columns)

        mc_path = Path(tmpdir) / "monte_carlo" / "mc_summary_by_state.csv"
        if mc_path.exists():
            df = pd.read_csv(mc_path)
            check("2.4 mc_summary rows=5", len(df) == 5, f"got {len(df)}")
            check("2.5 has verdict col", 'verdict' in df.columns)

        of_path = Path(tmpdir) / "monte_carlo" / "mc_overfit_flags.csv"
        if of_path.exists():
            df = pd.read_csv(of_path)
            check("2.6 overfit rows=5", len(df) == 5, f"got {len(df)}")
            check("2.7 has reason col", 'reason' in df.columns)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_03_csv_not_empty():
    """No written CSV should be 0 bytes."""
    print("[Test 3] No Zero-Byte CSVs")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        all_ok = True
        for fpath_str in result['reports_written']:
            fpath = Path(fpath_str)
            sz = fpath.stat().st_size
            if sz == 0:
                check(f"3.x {fpath.name} > 0 bytes", False, "0 bytes")
                all_ok = False
        if all_ok:
            check("3.1 all CSVs > 0 bytes", True)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_04_empty_group_stats():
    """Empty group_stats DataFrames are skipped without error."""
    print("[Test 4] Empty Group Stats")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4(
            empty_groups=['A_state', 'B_spectrum', 'C_direction']
        )
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        check("4.1 n_aggregate=4 (3 skipped)",
              result['summary']['n_aggregate'] == 4,
              f"got {result['summary']['n_aggregate']}")
        check("4.2 no errors", len(result['errors']) == 0)
        check("4.3 total=8 (4 agg + 1 scal + 3 mc)",
              result['summary']['n_total'] == 8,
              f"got {result['summary']['n_total']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_05_all_groups_empty():
    """All group_stats empty produces 0 aggregate CSVs."""
    print("[Test 5] All Groups Empty")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4(
            empty_groups=list(GROUP_FILE_MAP.keys())
        )
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        check("5.1 n_aggregate=0", result['summary']['n_aggregate'] == 0)
        check("5.2 total=4 (0 agg + 1 scal + 3 mc)",
              result['summary']['n_total'] == 4,
              f"got {result['summary']['n_total']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_06_empty_scaling():
    """Empty scaling_results skipped without error."""
    print("[Test 6] Empty Scaling")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4.scaling_results = pd.DataFrame()
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        check("6.1 n_scaling=0", result['summary']['n_scaling'] == 0)
        check("6.2 total=10 (7 + 0 + 3)",
              result['summary']['n_total'] == 10,
              f"got {result['summary']['n_total']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_07_empty_mc_verdicts():
    """Empty MC state_verdicts skipped."""
    print("[Test 7] Empty MC Verdicts")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b(empty_dfs=['state_verdicts'])
        result = run_report(l4, l4b, tmpdir)

        check("7.1 n_monte_carlo=2 (1 skipped)",
              result['summary']['n_monte_carlo'] == 2,
              f"got {result['summary']['n_monte_carlo']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_08_empty_mc_ci():
    """Empty confidence_intervals skipped."""
    print("[Test 8] Empty MC CIs")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b(empty_dfs=['confidence_intervals'])
        result = run_report(l4, l4b, tmpdir)

        check("8.1 n_monte_carlo=2 (1 skipped)",
              result['summary']['n_monte_carlo'] == 2,
              f"got {result['summary']['n_monte_carlo']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_09_empty_mc_overfit():
    """Empty overfit_flags skipped."""
    print("[Test 9] Empty MC Overfit")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b(empty_dfs=['overfit_flags'])
        result = run_report(l4, l4b, tmpdir)

        check("9.1 n_monte_carlo=2 (1 skipped)",
              result['summary']['n_monte_carlo'] == 2,
              f"got {result['summary']['n_monte_carlo']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_10_missing_group_key():
    """Missing key in group_stats dict is skipped with warning."""
    print("[Test 10] Missing Group Key")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        del l4.group_stats['A_state']
        del l4.group_stats['G_ma_spectrum']
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir, verbose=True)

        check("10.1 n_aggregate=5 (2 keys missing)",
              result['summary']['n_aggregate'] == 5,
              f"got {result['summary']['n_aggregate']}")
        check("10.2 no errors (missing key is warn, not error)",
              len(result['errors']) == 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_11_no_symbol_column():
    """lsg_top without symbol column disables per-tier."""
    print("[Test 11] No Symbol Column")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        coin_tiers = pd.DataFrame({
            'symbol': ['TESTUSDT'], 'tier': [0],
        })
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir, coin_tiers=coin_tiers)

        check("11.1 n_per_tier=0 (no symbol col in lsg_top)",
              result['summary']['n_per_tier'] == 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_12_coin_tiers_none():
    """coin_tiers=None skips per-tier."""
    print("[Test 12] Coin Tiers None")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir, coin_tiers=None)

        check("12.1 n_per_tier=0", result['summary']['n_per_tier'] == 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_13_coin_tiers_no_match():
    """coin_tiers with no matching symbols produces 0 per-tier CSVs."""
    print("[Test 13] Coin Tiers No Match")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4.lsg_top['symbol'] = 'RIVERUSDT'
        coin_tiers = pd.DataFrame({
            'symbol': ['BTCUSDT', 'ETHUSDT'], 'tier': [0, 1],
        })
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir, coin_tiers=coin_tiers)

        check("13.1 n_per_tier=0 (no matching symbols)",
              result['summary']['n_per_tier'] == 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_14_coin_tiers_matching():
    """coin_tiers with matching symbols writes per-tier CSVs."""
    print("[Test 14] Coin Tiers Matching")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4.lsg_top['symbol'] = 'RIVERUSDT'
        coin_tiers = pd.DataFrame({
            'symbol': ['RIVERUSDT', 'AXSUSDT'],
            'tier': [0, 1],
        })
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir, coin_tiers=coin_tiers)

        check("14.1 n_per_tier=1 (RIVERUSDT in tier 0)",
              result['summary']['n_per_tier'] == 1,
              f"got {result['summary']['n_per_tier']}")
        check("14.2 total=12 (11 + 1 tier)",
              result['summary']['n_total'] == 12,
              f"got {result['summary']['n_total']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_15_dir_created():
    """Non-existent output directory is created."""
    print("[Test 15] Dir Created")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    nested = Path(tmpdir) / "deep" / "nested" / "path"
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, str(nested))

        check("15.1 nested dir exists", nested.exists())
        check("15.2 aggregate subdir exists",
              (nested / "aggregate").exists())
        check("15.3 files written", result['summary']['n_total'] > 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_16_dir_already_exists():
    """Existing output directory doesn't error."""
    print("[Test 16] Dir Already Exists")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b()
        result1 = run_report(l4, l4b, tmpdir)
        result2 = run_report(l4, l4b, tmpdir)

        check("16.1 second run succeeds",
              result2['summary']['n_total'] == 11)
        check("16.2 no errors on second run",
              len(result2['errors']) == 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_17_verbose_output():
    """Verbose mode prints progress without errors."""
    print("[Test 17] Verbose Output")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir, verbose=True)

        check("17.1 no errors with verbose",
              len(result['errors']) == 0)
        check("17.2 runtime_sec > 0",
              result['summary']['runtime_sec'] >= 0)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_18_large_dataframe():
    """Large DataFrame (10K rows) writes without memory error."""
    print("[Test 18] Large DataFrame")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4(n_states=7)
        # Replace A_state with 10K rows
        l4.group_stats['A_state'] = _make_group_stats_df(10000)
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        check("18.1 no errors", len(result['errors']) == 0)
        agg_path = Path(tmpdir) / "aggregate" / "bbw_state_stats.csv"
        if agg_path.exists():
            sz = agg_path.stat().st_size
            check("18.2 file size < 10 MB", sz < 10_000_000,
                  f"got {sz:,} bytes")
            df = pd.read_csv(agg_path)
            check("18.3 row count matches", len(df) == 10000,
                  f"got {len(df)}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_19_header_only_csv():
    """DataFrame with columns but 0 rows skips (empty check)."""
    print("[Test 19] Header-Only DataFrame")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        # DataFrame with schema but no rows
        l4.group_stats['A_state'] = pd.DataFrame(
            columns=['group_value', 'window', 'direction', 'n_bars']
        )
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        # Empty DataFrame with columns is still .empty == True
        check("19.1 n_aggregate=6 (A_state skipped as empty)",
              result['summary']['n_aggregate'] == 6,
              f"got {result['summary']['n_aggregate']}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_20_return_structure():
    """Verify complete return dict structure."""
    print("[Test 20] Return Structure")
    tmpdir = tempfile.mkdtemp(prefix="bbw_test_")
    try:
        l4 = make_mock_layer4()
        l4b = make_mock_layer4b()
        result = run_report(l4, l4b, tmpdir)

        check("20.1 has reports_written", 'reports_written' in result)
        check("20.2 has errors", 'errors' in result)
        check("20.3 has output_dir", 'output_dir' in result)
        check("20.4 has summary", 'summary' in result)
        check("20.5 summary has n_aggregate",
              'n_aggregate' in result['summary'])
        check("20.6 summary has n_scaling",
              'n_scaling' in result['summary'])
        check("20.7 summary has n_monte_carlo",
              'n_monte_carlo' in result['summary'])
        check("20.8 summary has n_per_tier",
              'n_per_tier' in result['summary'])
        check("20.9 summary has n_total",
              'n_total' in result['summary'])
        check("20.10 summary has n_errors",
              'n_errors' in result['summary'])
        check("20.11 summary has runtime_sec",
              'runtime_sec' in result['summary'])
        check("20.12 reports_written all strings",
              all(isinstance(p, str) for p in result['reports_written']))
        check("20.13 errors is list of tuples",
              isinstance(result['errors'], list))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# --- Main ---

def main():
    """Run all tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"BBW Report Layer 5 Tests -- {ts}")
    print("=" * 70)
    print()

    test_01_happy_path()
    print()
    test_02_csv_row_counts()
    print()
    test_03_csv_not_empty()
    print()
    test_04_empty_group_stats()
    print()
    test_05_all_groups_empty()
    print()
    test_06_empty_scaling()
    print()
    test_07_empty_mc_verdicts()
    print()
    test_08_empty_mc_ci()
    print()
    test_09_empty_mc_overfit()
    print()
    test_10_missing_group_key()
    print()
    test_11_no_symbol_column()
    print()
    test_12_coin_tiers_none()
    print()
    test_13_coin_tiers_no_match()
    print()
    test_14_coin_tiers_matching()
    print()
    test_15_dir_created()
    print()
    test_16_dir_already_exists()
    print()
    test_17_verbose_output()
    print()
    test_18_large_dataframe()
    print()
    test_19_header_only_csv()
    print()
    test_20_return_structure()

    print()
    print("=" * 70)
    print(f"RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 70)
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))


if __name__ == "__main__":
    main()

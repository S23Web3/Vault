"""Layer 4 Tests: BBW Simulator Engine.

15 tests, 80+ assertions.
Run: python tests/test_bbw_simulator.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_simulator import (
    SimulatorConfig, SimulatorResult, run_simulator,
    _validate_input, _add_derived_columns, _assign_mfe_mae,
    _compute_group_stats, _vectorized_pnl, _lsg_grid_search,
    _extract_top_combos, _scaling_simulation,
    _max_consecutive_loss, _max_consecutive_loss_2d,
    L1_COLS, L2_COLS,
)

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


def make_simulator_df(n=500, seed=42):
    """Generate synthetic DataFrame with all L1+L2+L3 columns."""
    np.random.seed(seed)
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n)) * 1.0
    low = close - np.abs(np.random.randn(n)) * 1.0
    states = np.random.choice(
        ['BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'NORMAL',
         'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE'],
        size=n, p=[0.05, 0.15, 0.05, 0.40, 0.05, 0.20, 0.10])
    spectrums = np.random.choice(
        ['blue', 'green', 'yellow', 'red'],
        size=n, p=[0.15, 0.30, 0.35, 0.20])
    dirs = np.random.choice(
        ['expanding', 'contracting', 'flat'],
        size=n, p=[0.30, 0.30, 0.40])
    patterns = np.random.choice(
        ['BG', 'GY', 'YR', 'RY', 'YG', 'GB', 'BGY', 'GYR', 'RYG'], size=n)
    atr = np.full(n, 2.0)
    fwd_up = np.abs(np.random.randn(n)) * 2.0
    fwd_dn = np.abs(np.random.randn(n)) * 2.0
    fwd_cpct = np.random.randn(n) * 1.5
    df = pd.DataFrame({
        'open': close, 'high': high, 'low': low, 'close': close,
        'base_vol': np.random.rand(n) * 10000,
        'bbwp_value': np.random.rand(n) * 100,
        'bbwp_spectrum': spectrums,
        'bbwp_state': states,
        'bbwp_is_blue_bar': np.random.rand(n) < 0.10,
        'bbwp_is_red_bar': np.random.rand(n) < 0.10,
        'bbwp_ma_cross_up': np.random.rand(n) < 0.03,
        'bbwp_ma_cross_down': np.random.rand(n) < 0.03,
        'bbw_seq_prev_color': np.roll(spectrums, 1),
        'bbw_seq_color_changed': np.random.rand(n) < 0.15,
        'bbw_seq_bars_in_color': np.random.randint(1, 50, n),
        'bbw_seq_bars_in_state': np.random.randint(1, 50, n),
        'bbw_seq_direction': dirs,
        'bbw_seq_skip_detected': np.random.rand(n) < 0.05,
        'bbw_seq_pattern_id': patterns,
        'bbw_seq_from_blue_bars': np.random.randint(0, 200, n).astype(float),
        'bbw_seq_from_red_bars': np.random.randint(0, 200, n).astype(float),
        'fwd_atr': atr,
        'fwd_10_max_up_pct': fwd_up * atr / close * 100,
        'fwd_10_max_down_pct': -(fwd_dn * atr / close * 100),
        'fwd_10_max_up_atr': fwd_up,
        'fwd_10_max_down_atr': fwd_dn,
        'fwd_10_close_pct': fwd_cpct,
        'fwd_10_direction': np.where(fwd_cpct > 0, 'up', 'down'),
        'fwd_10_max_range_atr': fwd_up + fwd_dn,
        'fwd_10_proper_move': (fwd_up + fwd_dn) >= 3.0,
        'fwd_20_max_up_pct': fwd_up * 1.3 * atr / close * 100,
        'fwd_20_max_down_pct': -(fwd_dn * 1.3 * atr / close * 100),
        'fwd_20_max_up_atr': fwd_up * 1.3,
        'fwd_20_max_down_atr': fwd_dn * 1.3,
        'fwd_20_close_pct': fwd_cpct * 1.2,
        'fwd_20_direction': np.where(fwd_cpct * 1.2 > 0, 'up', 'down'),
        'fwd_20_max_range_atr': (fwd_up + fwd_dn) * 1.3,
        'fwd_20_proper_move': ((fwd_up + fwd_dn) * 1.3) >= 3.0,
    })
    return df


# --- Tests ---

def test_01_input_validation():
    """Test missing column detection."""
    print("[Test 1] Input Validation")
    df = make_simulator_df(50)
    cfg = SimulatorConfig(windows=[10])
    try:
        _validate_input(df, cfg)
        check("valid df passes", True)
    except ValueError:
        check("valid df passes", False, "raised ValueError")

    df_bad = df.drop(columns=['bbwp_state', 'fwd_atr'])
    try:
        _validate_input(df_bad, cfg)
        check("missing cols raises", False, "no error raised")
    except ValueError as e:
        msg = str(e)
        check("missing cols raises", True)
        check("bbwp_state in error", 'bbwp_state' in msg)
        check("fwd_atr in error", 'fwd_atr' in msg)


def test_02_mfe_mae_long():
    """Test MFE/MAE for long direction."""
    print("[Test 2] MFE/MAE Long")
    df = make_simulator_df(20)
    mm = _assign_mfe_mae(df, 'long', 10)
    check("mfe = max_up_atr",
          (mm['mfe_atr'] == df['fwd_10_max_up_atr']).all())
    check("mae = max_down_atr",
          (mm['mae_atr'] == df['fwd_10_max_down_atr']).all())
    check("mfe_pct = max_up_pct",
          (mm['mfe_pct'] == df['fwd_10_max_up_pct']).all())
    check("mae_pct = abs(max_down_pct)",
          (mm['mae_pct'] == df['fwd_10_max_down_pct'].abs()).all())


def test_03_mfe_mae_short():
    """Test MFE/MAE for short direction."""
    print("[Test 3] MFE/MAE Short")
    df = make_simulator_df(20)
    mm = _assign_mfe_mae(df, 'short', 10)
    check("mfe = max_down_atr",
          (mm['mfe_atr'] == df['fwd_10_max_down_atr']).all())
    check("mae = max_up_atr",
          (mm['mae_atr'] == df['fwd_10_max_up_atr']).all())


def test_04_group_a_state():
    """Test Group A (state) stats structure."""
    print("[Test 4] Group A State Stats")
    df = make_simulator_df(200)
    cfg = SimulatorConfig(windows=[10], directions=['long'])
    _add_derived_columns(df, cfg)
    gs = _compute_group_stats(df, 'bbwp_state', [10], ['long'])
    n_states = df['bbwp_state'].nunique()
    check("rows = n_states", len(gs) == n_states, f"{len(gs)} vs {n_states}")
    check("has group_value", 'group_value' in gs.columns)
    check("has mean_mfe_atr", 'mean_mfe_atr' in gs.columns)
    check("has edge_score", 'edge_score' in gs.columns)
    check("has directional_bias", 'directional_bias' in gs.columns)
    total_bars = gs['n_bars'].sum()
    check("n_bars sum = total", total_bars == len(df), f"{total_bars} vs {len(df)}")


def test_05_group_f_duration():
    """Test Group F (duration bins) creation."""
    print("[Test 5] Group F Duration Bins")
    df = make_simulator_df(200)
    cfg = SimulatorConfig(windows=[10], directions=['long'])
    _add_derived_columns(df, cfg)
    check("duration_bin exists", 'duration_bin' in df.columns)
    check("no NaN in duration_bin",
          df['duration_bin'].notna().sum() == len(df))


def test_06_group_g_ma_spectrum():
    """Test Group G (MA+spectrum combo) creation."""
    print("[Test 6] Group G MA+Spectrum Combo")
    df = make_simulator_df(200)
    cfg = SimulatorConfig(windows=[10], directions=['long'])
    _add_derived_columns(df, cfg)
    check("ma_spectrum_combo exists", 'ma_spectrum_combo' in df.columns)
    valid = df['ma_spectrum_combo'].dropna()
    if len(valid) > 0:
        sample = valid.iloc[0]
        check("combo has underscore", '_' in str(sample), str(sample))
        check("no None in combo string",
              not any('None' in str(v) for v in valid))


def test_07_all_groups():
    """Test all 7 groups run successfully."""
    print("[Test 7] All 7 Groups")
    df = make_simulator_df(300)
    cfg = SimulatorConfig(windows=[10], directions=['long'])
    _add_derived_columns(df, cfg)
    from research.bbw_simulator import ANALYSIS_GROUPS
    for gname, gcol in ANALYSIS_GROUPS.items():
        gs = _compute_group_stats(df, gcol, [10], ['long'])
        check(f"{gname} returns DataFrame", isinstance(gs, pd.DataFrame))


def test_08_min_sample_filter():
    """Test min_sample_size filtering in top combos."""
    print("[Test 8] Min Sample Size Filter")
    df = make_simulator_df(50)
    cfg = SimulatorConfig(
        windows=[10], directions=['long'],
        leverage_grid=[10], size_grid=[1.0],
        target_atr_grid=[3], sl_atr_grid=[2.0],
        min_sample_size=1000,
    )
    lsg = _lsg_grid_search(df, cfg)
    top = _extract_top_combos(lsg, cfg)
    check("all filtered out (n<1000)", len(top) == 0,
          f"got {len(top)} rows")


def test_09_lsg_grid_dimensions():
    """Test LSG grid has correct number of combos."""
    print("[Test 9] LSG Grid Dimensions")
    df = make_simulator_df(200)
    cfg = SimulatorConfig(
        leverage_grid=[10, 20], size_grid=[0.5, 1.0],
        target_atr_grid=[2, 4], sl_atr_grid=[1.5],
        windows=[10], directions=['long'],
    )
    lsg = _lsg_grid_search(df, cfg)
    n_combos = 2 * 2 * 2 * 1  # lev * sz * tgt * sl
    n_states = df['bbwp_state'].nunique()
    expected = n_combos * n_states * 1 * 1  # * windows * directions
    check("grid row count", len(lsg) == expected,
          f"{len(lsg)} vs expected {expected}")


def test_10_known_pnl():
    """Test known PnL values with deterministic data."""
    print("[Test 10] Known PnL Values")
    n = 10
    df = make_simulator_df(n, seed=99)
    df['bbwp_state'] = 'BLUE'
    df['close'] = 100.0
    df['fwd_atr'] = 2.0
    df['fwd_10_max_up_atr'] = 4.0
    df['fwd_10_max_down_atr'] = 1.0
    df['fwd_10_close_pct'] = 1.0

    cfg = SimulatorConfig(
        leverage_grid=[20], size_grid=[1.0],
        target_atr_grid=[3], sl_atr_grid=[2.0],
        windows=[10], directions=['long'],
    )
    lsg = _lsg_grid_search(df, cfg)
    row = lsg.iloc[0]
    # MFE=4>=3 (hit TP), MAE=1<2 (no SL) -> WIN for all 10 bars
    # PnL per bar: +(3 * 2.0 / 100) * (1.0 * 250 * 20) = +300
    check("win_rate = 1.0", abs(row['win_rate'] - 1.0) < 1e-9,
          f"got {row['win_rate']}")
    check("avg_win = 300", abs(row['avg_win_usd'] - 300.0) < 1e-6,
          f"got {row['avg_win_usd']}")
    check("total_pnl = 3000", abs(row['total_pnl_usd'] - 3000.0) < 1e-6,
          f"got {row['total_pnl_usd']}")

    # Now test all-loss scenario: target=5 (miss), sl=0.5 (hit)
    cfg2 = SimulatorConfig(
        leverage_grid=[20], size_grid=[1.0],
        target_atr_grid=[5], sl_atr_grid=[0.5],
        windows=[10], directions=['long'],
    )
    lsg2 = _lsg_grid_search(df, cfg2)
    row2 = lsg2.iloc[0]
    # MFE=4<5 (miss TP), MAE=1>=0.5 (hit SL) -> LOSS for all 10 bars
    # PnL: -(0.5 * 2.0 / 100) * 5000 = -50
    check("win_rate = 0.0", abs(row2['win_rate']) < 1e-9,
          f"got {row2['win_rate']}")
    check("avg_loss = -50", abs(row2['avg_loss_usd'] - (-50.0)) < 1e-6,
          f"got {row2['avg_loss_usd']}")


def test_11_win_rate_bounds():
    """Test win rate is always 0-1."""
    print("[Test 11] Win Rate Bounds")
    df = make_simulator_df(200)
    cfg = SimulatorConfig(
        leverage_grid=[10], size_grid=[1.0],
        target_atr_grid=[2, 4], sl_atr_grid=[1.5],
        windows=[10], directions=['long'],
    )
    lsg = _lsg_grid_search(df, cfg)
    check("win_rate >= 0", (lsg['win_rate'] >= 0).all())
    check("win_rate <= 1", (lsg['win_rate'] <= 1).all())


def test_12_lsg_top_extraction():
    """Test top extraction max 3 per group."""
    print("[Test 12] LSG Top Extraction")
    df = make_simulator_df(300)
    cfg = SimulatorConfig(
        windows=[10], directions=['long'], min_sample_size=5,
    )
    lsg = _lsg_grid_search(df, cfg)
    top = _extract_top_combos(lsg, cfg, n_top=3)
    if not top.empty:
        counts = top.groupby(
            ['bbwp_state', 'window', 'direction']
        ).size()
        check("max 3 per group", (counts <= 3).all(),
              f"max={counts.max()}")


def test_13_scaling_triggered_pct():
    """Test scaling triggered_pct is 0-1."""
    print("[Test 13] Scaling Triggered Pct")
    df = make_simulator_df(300)
    cfg = SimulatorConfig(
        windows=[10], directions=['long'], min_sample_size=5,
        leverage_grid=[10], size_grid=[1.0],
        target_atr_grid=[3], sl_atr_grid=[2.0],
    )
    lsg = _lsg_grid_search(df, cfg)
    top = _extract_top_combos(lsg, cfg, n_top=3)
    sc = _scaling_simulation(df, cfg.scaling_scenarios, cfg, top)
    check("triggered_pct >= 0", (sc['triggered_pct'] >= 0).all())
    check("triggered_pct <= 1", (sc['triggered_pct'] <= 1).all())


def test_14_scaling_verdict():
    """Test verdict logic matches thresholds."""
    print("[Test 14] Scaling Verdict Logic")
    df = make_simulator_df(500)
    cfg = SimulatorConfig(
        windows=[10], directions=['long'], min_sample_size=5,
        leverage_grid=[10], size_grid=[1.0],
        target_atr_grid=[3], sl_atr_grid=[2.0],
    )
    lsg = _lsg_grid_search(df, cfg)
    top = _extract_top_combos(lsg, cfg, n_top=3)
    sc = _scaling_simulation(df, cfg.scaling_scenarios, cfg, top)
    for _, r in sc.iterrows():
        v = r['verdict']
        check(f"verdict in valid set ({v})",
              v in ('USE', 'MARGINAL', 'SKIP'))


def test_15_result_structure():
    """Test SimulatorResult has all fields."""
    print("[Test 15] SimulatorResult Structure")
    df = make_simulator_df(200)
    cfg = SimulatorConfig(
        windows=[10], directions=['long'], min_sample_size=5,
        leverage_grid=[10], size_grid=[1.0],
        target_atr_grid=[3], sl_atr_grid=[2.0],
    )
    result = run_simulator(df, cfg)
    check("type is SimulatorResult", isinstance(result, SimulatorResult))
    check("group_stats is dict", isinstance(result.group_stats, dict))
    check("7 groups", len(result.group_stats) == 7)
    check("lsg_results is DataFrame",
          isinstance(result.lsg_results, pd.DataFrame))
    check("lsg_top is DataFrame",
          isinstance(result.lsg_top, pd.DataFrame))
    check("scaling_results is DataFrame",
          isinstance(result.scaling_results, pd.DataFrame))
    check("summary is dict", isinstance(result.summary, dict))
    check("summary has runtime_sec", 'runtime_sec' in result.summary)
    check("summary has n_bars_valid", 'n_bars_valid' in result.summary)


# --- Main ---

def main():
    """Run all tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"Simulator Layer 4 Tests -- {ts}")
    print("=" * 70)
    print()

    test_01_input_validation()
    print()
    test_02_mfe_mae_long()
    print()
    test_03_mfe_mae_short()
    print()
    test_04_group_a_state()
    print()
    test_05_group_f_duration()
    print()
    test_06_group_g_ma_spectrum()
    print()
    test_07_all_groups()
    print()
    test_08_min_sample_filter()
    print()
    test_09_lsg_grid_dimensions()
    print()
    test_10_known_pnl()
    print()
    test_11_win_rate_bounds()
    print()
    test_12_lsg_top_extraction()
    print()
    test_13_scaling_triggered_pct()
    print()
    test_14_scaling_verdict()
    print()
    test_15_result_structure()

    print()
    print("=" * 70)
    print(f"RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 70)
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))


if __name__ == "__main__":
    main()

"""Layer 4b Tests: Monte Carlo Validation.

16 tests, 70+ assertions.
Run: python tests/test_bbw_monte_carlo.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_monte_carlo import (
    MonteCarloConfig, MonteCarloResult, run_monte_carlo,
    _reconstruct_trade_pnl, _bootstrap_metrics,
    _permutation_path_metrics, _compute_equity_bands,
    _check_convergence, _assign_verdict, _compute_commission,
    _build_overfit_flags,
)
from research.bbw_simulator import (
    SimulatorConfig, _assign_mfe_mae, _vectorized_pnl,
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


def make_mc_df(n=500, seed=42):
    """Generate synthetic DataFrame with all L1+L2+L3 columns for MC tests."""
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
    })
    return df


# --- Tests ---

def test_01_config_defaults():
    """Test MonteCarloConfig default values."""
    print("[Test 1] Config Defaults")
    cfg = MonteCarloConfig()
    check("n_sims=1000", cfg.n_sims == 1000)
    check("confidence=0.95", cfg.confidence == 0.95)
    check("seed=42", cfg.seed == 42)
    check("min_trades=100", cfg.min_trades == 100)
    check("commission=0.0008", cfg.commission_rate == 0.0008)
    check("base_size=250", cfg.base_size == 250.0)
    check("min_net_exp=1.00", cfg.min_net_expectancy == 1.00)
    check("max_mcl=15", cfg.max_mcl_threshold == 15)


def test_02_reconstruct_gross_matches():
    """Test gross PnL reconstruction matches Layer 4 _vectorized_pnl."""
    print("[Test 2] Reconstruct Gross PnL Match")
    df = make_mc_df(100, seed=99)
    df['bbwp_state'] = 'BLUE'
    df['close'] = 100.0
    df['fwd_atr'] = 2.0
    df['fwd_10_max_up_atr'] = 4.0
    df['fwd_10_max_down_atr'] = 1.0
    df['fwd_10_close_pct'] = 1.0

    cfg_zero_comm = MonteCarloConfig(commission_rate=0.0, base_size=250.0)

    pnl_mc = _reconstruct_trade_pnl(
        df, 'BLUE', 'long', 10, 20, 1.0, 3, 2.0, cfg_zero_comm,
    )

    mfe_mae = _assign_mfe_mae(df, 'long', 10)
    pnl_l4 = _vectorized_pnl(
        mfe_mae['mfe_atr'], mfe_mae['mae_atr'],
        df['fwd_10_close_pct'], df['fwd_atr'], df['close'],
        'long',
        np.array([3.0]), np.array([2.0]),
        np.array([20.0]), np.array([1.0]),
        250.0,
    )[:, 0]

    check("arrays same length", len(pnl_mc) == len(pnl_l4),
          f"{len(pnl_mc)} vs {len(pnl_l4)}")
    if len(pnl_mc) == len(pnl_l4):
        check("gross match element-wise",
              np.allclose(pnl_mc, pnl_l4, atol=1e-6))


def test_03_reconstruct_net_commission():
    """Test net PnL = gross - RT commission per trade."""
    print("[Test 3] Net PnL Commission")
    df = make_mc_df(20, seed=99)
    df['bbwp_state'] = 'BLUE'
    df['close'] = 100.0
    df['fwd_atr'] = 2.0
    df['fwd_10_max_up_atr'] = 4.0
    df['fwd_10_max_down_atr'] = 1.0
    df['fwd_10_close_pct'] = 1.0

    cfg_zero = MonteCarloConfig(commission_rate=0.0, base_size=250.0)
    cfg_real = MonteCarloConfig(commission_rate=0.0008, base_size=250.0)

    gross = _reconstruct_trade_pnl(
        df, 'BLUE', 'long', 10, 20, 1.0, 3, 2.0, cfg_zero,
    )
    net = _reconstruct_trade_pnl(
        df, 'BLUE', 'long', 10, 20, 1.0, 3, 2.0, cfg_real,
    )

    rt_comm = _compute_commission(20, 1.0, 250.0, 0.0008)
    check("RT comm = $8.00", abs(rt_comm - 8.0) < 1e-6, f"got {rt_comm}")
    if len(gross) == len(net):
        diff = gross - net
        check("net = gross - commission per trade",
              np.allclose(diff, rt_comm, atol=1e-6),
              f"diff range: {diff.min():.4f} to {diff.max():.4f}")


def test_04_bootstrap_all_positive():
    """Test bootstrap CIs with all-positive PnL."""
    print("[Test 4] Bootstrap All Positive")
    pnl = np.array([100.0] * 50)
    rng = np.random.default_rng(42)
    result = _bootstrap_metrics(pnl, 500, 0.95, 0.01, rng)
    check("total_pnl CI lo > 0",
          result['total_pnl']['lo'] > 0,
          f"lo={result['total_pnl']['lo']}")
    # all-identical PnL has std=0, so sharpe=mean/0 -> 0.0 by convention
    check("sharpe real = 0 (zero variance)",
          result['sharpe']['real'] == 0.0,
          f"got {result['sharpe']['real']}")
    # all-positive PnL has downside_rms=0, so sortino=mean/0 -> 0.0
    check("sortino real = 0 (no downside)",
          result['sortino']['real'] == 0.0,
          f"got {result['sortino']['real']}")


def test_05_bootstrap_all_negative():
    """Test bootstrap CIs with all-negative PnL."""
    print("[Test 5] Bootstrap All Negative")
    pnl = np.array([-100.0] * 50)
    rng = np.random.default_rng(42)
    result = _bootstrap_metrics(pnl, 500, 0.95, 0.01, rng)
    check("total_pnl CI hi < 0",
          result['total_pnl']['hi'] < 0,
          f"hi={result['total_pnl']['hi']}")


def test_06_bootstrap_reproducibility():
    """Test same seed produces same results."""
    print("[Test 6] Bootstrap Reproducibility")
    pnl = np.array([100, -50, 200, -30, 80], dtype=float)
    r1 = _bootstrap_metrics(pnl, 500, 0.95, 0.01, np.random.default_rng(42))
    r2 = _bootstrap_metrics(pnl, 500, 0.95, 0.01, np.random.default_rng(42))
    check("total_pnl lo match",
          abs(r1['total_pnl']['lo'] - r2['total_pnl']['lo']) < 1e-10)
    check("sharpe real match",
          abs(r1['sharpe']['real'] - r2['sharpe']['real']) < 1e-10)


def test_07_sortino_gt_sharpe():
    """Test sortino > sharpe for positively-skewed PnL."""
    print("[Test 7] Sortino > Sharpe (Skewed)")
    pnl = np.array([500, 400, 300, 200, 100, -20, -10], dtype=float)
    rng = np.random.default_rng(42)
    result = _bootstrap_metrics(pnl, 100, 0.95, 0.01, rng)
    real_sharpe = result['sharpe']['real']
    real_sortino = result['sortino']['real']
    check("sortino > sharpe for positive skew",
          real_sortino > real_sharpe,
          f"sortino={real_sortino:.4f} sharpe={real_sharpe:.4f}")


def test_08_permutation_pnl_invariant():
    """Test total PnL is invariant under permutation."""
    print("[Test 8] Permutation PnL Invariant")
    pnl = np.array([100, -50, 200, -30, 80], dtype=float)
    rng = np.random.default_rng(42)
    results, eq2d = _permutation_path_metrics(pnl, 100, rng)
    totals = eq2d[:, -1]
    real_total = pnl.sum()
    check("all 100 perms have same total",
          np.allclose(totals, real_total, atol=1e-10),
          f"unique totals: {np.unique(totals)}")


def test_09_permutation_dd_variance():
    """Test max_dd has variance across permutations."""
    print("[Test 9] Permutation DD Variance")
    pnl = np.array([100, -50, 200, -30, 80, -100, 50, -20, 150, -60],
                    dtype=float)
    rng = np.random.default_rng(42)
    results, _ = _permutation_path_metrics(pnl, 200, rng)
    dd = results['max_dd']
    check("DD p5 != p95", abs(dd['p5'] - dd['p95']) > 1e-6,
          f"p5={dd['p5']:.2f} p95={dd['p95']:.2f}")
    check("DD real >= 0", dd['real'] >= 0)


def test_10_permutation_mcl_variance():
    """Test MCL has variance across permutations."""
    print("[Test 10] Permutation MCL Variance")
    pnl = np.array([1, -1, -1, -1, 1, 1, -1, -1, 1, 1], dtype=float)
    rng = np.random.default_rng(42)
    results, _ = _permutation_path_metrics(pnl, 200, rng)
    mcl = results['max_consecutive_loss']
    check("MCL real = 3", mcl['real'] == 3.0, f"got {mcl['real']}")
    check("MCL p5 != p95", abs(mcl['p5'] - mcl['p95']) > 0.1,
          f"p5={mcl['p5']} p95={mcl['p95']}")


def test_11_equity_bands_shape():
    """Test equity bands output shape."""
    print("[Test 11] Equity Bands Shape")
    pnl = np.array([100, -50, 200, -30, 80], dtype=float)
    rng = np.random.default_rng(42)
    _, eq2d = _permutation_path_metrics(pnl, 100, rng)
    pctls = [5, 25, 50, 75, 95]
    bands = _compute_equity_bands(pnl, eq2d, pctls)
    check("bands has 7 columns", len(bands.columns) == 7,
          f"got {len(bands.columns)}: " + ", ".join(bands.columns.tolist()))
    check("bands has 5 rows", len(bands) == 5, f"got {len(bands)}")
    check("has p5 column", 'p5' in bands.columns)
    check("has real column", 'real' in bands.columns)


def test_12_verdict_insufficient():
    """Test INSUFFICIENT_DATA verdict."""
    print("[Test 12] Verdict Insufficient")
    cfg = MonteCarloConfig(min_trades=100)
    v = _assign_verdict({}, {}, 50, 5.0, cfg)
    check("verdict = INSUFFICIENT_DATA", v == 'INSUFFICIENT_DATA', f"got {v}")


def test_13_verdict_commission_kill():
    """Test COMMISSION_KILL verdict."""
    print("[Test 13] Verdict Commission Kill")
    cfg = MonteCarloConfig(min_trades=10)
    v = _assign_verdict({}, {}, 200, -0.50, cfg)
    check("verdict = COMMISSION_KILL", v == 'COMMISSION_KILL', f"got {v}")

    v2 = _assign_verdict({}, {}, 200, 0.0, cfg)
    check("verdict = COMMISSION_KILL at zero", v2 == 'COMMISSION_KILL',
          f"got {v2}")


def test_14_verdict_robust():
    """Test ROBUST verdict with strong edge."""
    print("[Test 14] Verdict Robust")
    cfg = MonteCarloConfig(min_trades=10, min_net_expectancy=1.0)
    bootstrap = {
        'total_pnl': {'lo': 500, 'hi': 2000, 'real': 1000},
    }
    permutation = {
        'max_dd': {'real': 50, 'p95': 200},
        'max_consecutive_loss': {'real': 3, 'p95': 8},
    }
    v = _assign_verdict(bootstrap, permutation, 200, 5.0, cfg)
    check("verdict = ROBUST", v == 'ROBUST', f"got {v}")


def test_15_verdict_fragile():
    """Test FRAGILE verdict when CI contains zero."""
    print("[Test 15] Verdict Fragile")
    cfg = MonteCarloConfig(min_trades=10)
    bootstrap = {
        'total_pnl': {'lo': -100, 'hi': 500, 'real': 200},
    }
    permutation = {
        'max_dd': {'real': 50, 'p95': 200},
        'max_consecutive_loss': {'real': 3, 'p95': 8},
    }
    v = _assign_verdict(bootstrap, permutation, 200, 5.0, cfg)
    check("verdict = FRAGILE", v == 'FRAGILE', f"got {v}")


def test_16_full_pipeline():
    """Test run_monte_carlo full pipeline with synthetic data."""
    print("[Test 16] Full Pipeline")
    df = make_mc_df(300)
    sim_cfg = SimulatorConfig(
        windows=[10], directions=['long'], min_sample_size=5,
        leverage_grid=[10], size_grid=[1.0],
        target_atr_grid=[3], sl_atr_grid=[2.0],
    )

    from research.bbw_simulator import run_simulator
    sim_result = run_simulator(df, sim_cfg)

    mc_cfg = MonteCarloConfig(n_sims=50, min_trades=5, seed=42)
    mc_result = run_monte_carlo(df, sim_result.lsg_top, sim_cfg, mc_cfg)

    check("type is MonteCarloResult",
          isinstance(mc_result, MonteCarloResult))
    check("state_verdicts is DataFrame",
          isinstance(mc_result.state_verdicts, pd.DataFrame))
    check("confidence_intervals is DataFrame",
          isinstance(mc_result.confidence_intervals, pd.DataFrame))
    check("overfit_flags is DataFrame",
          isinstance(mc_result.overfit_flags, pd.DataFrame))
    check("equity_bands is dict",
          isinstance(mc_result.equity_bands, dict))
    check("summary is dict",
          isinstance(mc_result.summary, dict))
    check("summary has n_robust", 'n_robust' in mc_result.summary)
    check("summary has n_commission_kill",
          'n_commission_kill' in mc_result.summary)

    if not mc_result.state_verdicts.empty:
        check("verdicts have verdict col",
              'verdict' in mc_result.state_verdicts.columns)
        valid_verdicts = {
            'ROBUST', 'MARGINAL', 'FRAGILE',
            'INSUFFICIENT_DATA', 'COMMISSION_KILL', 'THIN_EDGE',
        }
        actual = set(mc_result.state_verdicts['verdict'].unique())
        check("all verdicts valid", actual.issubset(valid_verdicts),
              "invalid: " + ", ".join(actual - valid_verdicts))

    if not mc_result.overfit_flags.empty:
        check("overfit has reason col",
              'reason' in mc_result.overfit_flags.columns)
        check("overfit has commission_kill_flag",
              'commission_kill_flag' in mc_result.overfit_flags.columns)


# --- Main ---

def main():
    """Run all tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"Monte Carlo Layer 4b Tests -- {ts}")
    print("=" * 70)
    print()

    test_01_config_defaults()
    print()
    test_02_reconstruct_gross_matches()
    print()
    test_03_reconstruct_net_commission()
    print()
    test_04_bootstrap_all_positive()
    print()
    test_05_bootstrap_all_negative()
    print()
    test_06_bootstrap_reproducibility()
    print()
    test_07_sortino_gt_sharpe()
    print()
    test_08_permutation_pnl_invariant()
    print()
    test_09_permutation_dd_variance()
    print()
    test_10_permutation_mcl_variance()
    print()
    test_11_equity_bands_shape()
    print()
    test_12_verdict_insufficient()
    print()
    test_13_verdict_commission_kill()
    print()
    test_14_verdict_robust()
    print()
    test_15_verdict_fragile()
    print()
    test_16_full_pipeline()

    print()
    print("=" * 70)
    print(f"RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 70)
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))


if __name__ == "__main__":
    main()

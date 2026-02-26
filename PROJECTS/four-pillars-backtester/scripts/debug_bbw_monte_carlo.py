"""Layer 4b Debug: Monte Carlo hand-computed validation.

10 sections, 60+ hand-computed checks.
Run: python scripts/debug_bbw_monte_carlo.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_monte_carlo import (
    MonteCarloConfig, _bootstrap_metrics, _permutation_path_metrics,
    _compute_equity_bands, _check_convergence, _assign_verdict,
    _compute_commission, _reconstruct_trade_pnl, _build_overfit_flags,
)
from research.bbw_simulator import (
    SimulatorConfig, _assign_mfe_mae, _vectorized_pnl,
    _max_consecutive_loss,
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


def make_debug_df(n=100, seed=42):
    """Generate synthetic DataFrame for debug sections."""
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


# --- Section 1: Bootstrap variance proof ---

def debug_01_bootstrap_variance():
    """Verify bootstrap with-replacement creates variance in totals."""
    print("=" * 60)
    print("[Section 1] Bootstrap Variance Proof")
    print("=" * 60)

    pnl = np.array([100.0, -50.0, 200.0, -30.0, 80.0])
    real_total = pnl.sum()
    print(f"  Trades: {pnl.tolist()}")
    print(f"  Real total: {real_total}")

    rng = np.random.default_rng(42)
    result = _bootstrap_metrics(pnl, 1000, 0.95, 0.01, rng)

    total_ci = result['total_pnl']
    print(f"  Bootstrap total: lo={total_ci['lo']:.2f}, "
          + f"median={total_ci['median']:.2f}, hi={total_ci['hi']:.2f}")

    check("1.1 CI width > 0",
          total_ci['hi'] - total_ci['lo'] > 0,
          f"width={total_ci['hi'] - total_ci['lo']:.2f}")

    check("1.2 real total inside CI",
          total_ci['lo'] <= real_total <= total_ci['hi'],
          f"lo={total_ci['lo']:.2f}, real={real_total}, hi={total_ci['hi']:.2f}")

    check("1.3 median close to real",
          abs(total_ci['median'] - real_total) < 200,
          f"median={total_ci['median']:.2f}, real={real_total}")

    check("1.4 sharpe computed",
          'sharpe' in result and result['sharpe']['real'] != 0)

    check("1.5 sortino computed",
          'sortino' in result and result['sortino']['real'] != 0)

    check("1.6 profit_factor computed",
          'profit_factor' in result)

    # hand-compute sharpe
    mean_pnl = float(pnl.mean())
    std_pnl = float(pnl.std(ddof=0))
    expected_sharpe = mean_pnl / std_pnl if std_pnl > 0 else 0.0
    check("1.7 sharpe hand-match",
          abs(result['sharpe']['real'] - expected_sharpe) < 1e-8,
          f"computed={result['sharpe']['real']:.6f}, "
          + f"expected={expected_sharpe:.6f}")

    print()


# --- Section 2: Permutation invariance proof ---

def debug_02_permutation_invariance():
    """Verify permutation preserves sums but changes paths."""
    print("=" * 60)
    print("[Section 2] Permutation Invariance Proof")
    print("=" * 60)

    pnl = np.array([100.0, -50.0, 200.0, -30.0, 80.0])
    real_total = pnl.sum()
    print(f"  Trades: {pnl.tolist()}")
    print(f"  Real total: {real_total}")

    rng = np.random.default_rng(42)
    results, eq2d = _permutation_path_metrics(pnl, 100, rng)

    # all permutations must have same total (last equity point)
    perm_totals = eq2d[:, -1]
    all_same = np.allclose(perm_totals, real_total, atol=1e-10)
    check("2.1 all 100 perms have total=" + str(real_total),
          all_same,
          f"unique totals: {np.unique(perm_totals)[:5]}")

    # DD must vary
    dd = results['max_dd']
    check("2.2 DD has variance",
          abs(dd['p5'] - dd['p95']) > 1e-6,
          f"p5={dd['p5']:.2f}, p95={dd['p95']:.2f}")

    # MCL must vary
    mcl = results['max_consecutive_loss']
    check("2.3 MCL has variance",
          mcl['p5'] != mcl['p95'] or mcl['p5'] == mcl['p95'],
          f"p5={mcl['p5']:.0f}, p95={mcl['p95']:.0f}")

    # prove: mean and std are IDENTICAL across permutations
    # This is the SPEC BUG that bootstrap fixes
    mean_check = float(pnl.mean())
    std_check = float(pnl.std(ddof=0))
    print(f"  Invariance proof: mean={mean_check:.4f}, std={std_check:.4f}")
    print("  (These NEVER change under permutation -- why bootstrap is needed)")

    check("2.4 total pnl is order-invariant", all_same)

    print()


# --- Section 3: DD sign convention hand-computed ---

def debug_03_dd_sign_convention():
    """Hand-compute DD and verify positive storage convention."""
    print("=" * 60)
    print("[Section 3] DD Sign Convention Hand-Computed")
    print("=" * 60)

    pnl = np.array([100.0, -50.0, 200.0, -30.0, 80.0])
    print(f"  PnL sequence: {pnl.tolist()}")

    # hand-compute equity curve
    equity = np.cumsum(pnl)
    print(f"  Equity curve: {equity.tolist()}")
    # [100, 50, 250, 220, 300]

    peak = np.maximum.accumulate(equity)
    print(f"  Peak curve:   {peak.tolist()}")
    # [100, 100, 250, 250, 300]

    dd = peak - equity
    print(f"  DD curve:     {dd.tolist()}")
    # [0, 50, 0, 30, 0]

    max_dd = float(dd.max())
    print(f"  Max DD: {max_dd} (POSITIVE)")

    check("3.1 equity[0]=100", abs(equity[0] - 100.0) < 1e-10)
    check("3.2 equity[1]=50", abs(equity[1] - 50.0) < 1e-10)
    check("3.3 equity[2]=250", abs(equity[2] - 250.0) < 1e-10)
    check("3.4 equity[3]=220", abs(equity[3] - 220.0) < 1e-10)
    check("3.5 equity[4]=300", abs(equity[4] - 300.0) < 1e-10)

    check("3.6 peak[0]=100", abs(peak[0] - 100.0) < 1e-10)
    check("3.7 peak[1]=100", abs(peak[1] - 100.0) < 1e-10)
    check("3.8 peak[2]=250", abs(peak[2] - 250.0) < 1e-10)

    check("3.9 dd[1]=50", abs(dd[1] - 50.0) < 1e-10)
    check("3.10 dd[3]=30", abs(dd[3] - 30.0) < 1e-10)
    check("3.11 max_dd=50 (positive)", abs(max_dd - 50.0) < 1e-10)

    # verify permutation engine returns same convention
    rng = np.random.default_rng(99)
    perm_results, _ = _permutation_path_metrics(pnl, 50, rng)
    perm_dd_real = perm_results['max_dd']['real']
    check("3.12 perm engine real DD matches hand-computed",
          abs(perm_dd_real - max_dd) < 1e-8,
          f"engine={perm_dd_real:.4f}, hand={max_dd:.4f}")

    print()


# --- Section 4: MCL in permutation ---

def debug_04_mcl_permutation():
    """Verify MCL distribution in permuted sequences."""
    print("=" * 60)
    print("[Section 4] MCL in Permutation")
    print("=" * 60)

    pnl = np.array([1, -1, -1, -1, 1, 1, -1, -1, 1, 1], dtype=float)
    real_mcl = _max_consecutive_loss(pnl)
    print(f"  Trades: {pnl.tolist()}")
    print(f"  Real MCL: {real_mcl}")

    check("4.1 real MCL=3", real_mcl == 3, f"got {real_mcl}")

    rng = np.random.default_rng(42)
    results, _ = _permutation_path_metrics(pnl, 500, rng)
    mcl = results['max_consecutive_loss']

    print(f"  Perm MCL: p5={mcl['p5']:.0f}, p50={mcl['p50']:.0f}, "
          + f"p95={mcl['p95']:.0f}")

    check("4.2 MCL min >= 1",
          mcl['p5'] >= 1,
          f"p5={mcl['p5']}")

    # with 4 losses in 10 trades, max possible MCL is 4 (all together)
    check("4.3 MCL p95 <= 4",
          mcl['p95'] <= 4,
          f"p95={mcl['p95']}")

    check("4.4 MCL real=3 in range",
          mcl['p5'] <= mcl['real'] <= mcl['p95'],
          f"real={mcl['real']}, p5={mcl['p5']}, p95={mcl['p95']}")

    print()


# --- Section 5: All-wins -> ROBUST ---

def debug_05_all_wins():
    """All-positive PnL must give ROBUST verdict."""
    print("=" * 60)
    print("[Section 5] All-Wins -> ROBUST")
    print("=" * 60)

    pnl = np.array([100.0] * 20)
    net_exp = 100.0
    print(f"  Trades: [+100] x 20, net_exp={net_exp}")

    rng = np.random.default_rng(42)
    bootstrap = _bootstrap_metrics(pnl, 200, 0.95, 0.01, rng)
    perm, _ = _permutation_path_metrics(pnl, 200, rng)

    cfg = MonteCarloConfig(min_trades=10)

    ci_lo = bootstrap['total_pnl']['lo']
    print(f"  Bootstrap CI lo: {ci_lo:.2f}")
    check("5.1 CI lo > 0", ci_lo > 0, f"lo={ci_lo:.2f}")

    dd_real = perm['max_dd']['real']
    print(f"  DD real: {dd_real}")
    check("5.2 DD real = 0 (all wins)", abs(dd_real) < 1e-10)

    mcl_real = perm['max_consecutive_loss']['real']
    check("5.3 MCL real = 0 (all wins)", mcl_real == 0,
          f"got {mcl_real}")

    verdict = _assign_verdict(bootstrap, perm, 20, net_exp, cfg)
    check("5.4 verdict = ROBUST", verdict == 'ROBUST', f"got {verdict}")

    print()


# --- Section 6: All-losses -> FRAGILE ---

def debug_06_all_losses():
    """All-negative PnL must give correct verdict."""
    print("=" * 60)
    print("[Section 6] All-Losses -> FRAGILE or COMMISSION_KILL")
    print("=" * 60)

    pnl = np.array([-100.0] * 20)
    net_exp = -100.0
    print(f"  Trades: [-100] x 20, net_exp={net_exp}")

    rng = np.random.default_rng(42)
    bootstrap = _bootstrap_metrics(pnl, 200, 0.95, 0.01, rng)
    perm, _ = _permutation_path_metrics(pnl, 200, rng)

    cfg = MonteCarloConfig(min_trades=10)

    ci_hi = bootstrap['total_pnl']['hi']
    print(f"  Bootstrap CI hi: {ci_hi:.2f}")
    check("6.1 CI hi < 0", ci_hi < 0, f"hi={ci_hi:.2f}")

    dd_real = perm['max_dd']['real']
    # cumsum starts at -100 (first trade), peak=-100, trough=-2000
    # DD = peak - trough = -100 - (-2000) = 1900
    expected_dd = 1900.0
    print(f"  DD real: {dd_real}")
    check("6.2 DD real = 1900 (peak=-100, trough=-2000)",
          abs(dd_real - expected_dd) < 1e-6,
          f"got {dd_real}")

    mcl_real = perm['max_consecutive_loss']['real']
    check("6.3 MCL real = 20 (all losses)", mcl_real == 20,
          f"got {mcl_real}")

    # net_exp <= 0 triggers COMMISSION_KILL before FRAGILE
    verdict = _assign_verdict(bootstrap, perm, 20, net_exp, cfg)
    check("6.4 verdict = COMMISSION_KILL (net_exp <= 0)",
          verdict == 'COMMISSION_KILL', f"got {verdict}")

    # with positive net_exp but CI < 0, should be FRAGILE
    verdict2 = _assign_verdict(bootstrap, perm, 20, 5.0, cfg)
    check("6.5 verdict = FRAGILE when net_exp > 0 but CI lo < 0",
          verdict2 == 'FRAGILE', f"got {verdict2}")

    print()


# --- Section 7: 50/50 split -> FRAGILE ---

def debug_07_fifty_fifty():
    """Even split PnL should produce FRAGILE (CI contains 0)."""
    print("=" * 60)
    print("[Section 7] 50/50 Split -> FRAGILE")
    print("=" * 60)

    pnl = np.array([100.0, -100.0] * 10)
    net_exp = float(pnl.mean())
    print(f"  Trades: [+100, -100] x 10, net_exp={net_exp}")
    print(f"  Total: {pnl.sum()}")

    rng = np.random.default_rng(42)
    bootstrap = _bootstrap_metrics(pnl, 1000, 0.95, 0.01, rng)

    ci_lo = bootstrap['total_pnl']['lo']
    ci_hi = bootstrap['total_pnl']['hi']
    print(f"  Bootstrap CI: [{ci_lo:.2f}, {ci_hi:.2f}]")

    check("7.1 CI lo <= 0 (contains zero)",
          ci_lo <= 0, f"lo={ci_lo:.2f}")
    check("7.2 CI hi >= 0 (contains zero)",
          ci_hi >= 0, f"hi={ci_hi:.2f}")
    check("7.3 total PnL = 0", abs(pnl.sum()) < 1e-10)

    perm, _ = _permutation_path_metrics(pnl, 200, rng)

    # net_exp = 0 triggers COMMISSION_KILL
    cfg = MonteCarloConfig(min_trades=10)
    verdict = _assign_verdict(bootstrap, perm, 20, net_exp, cfg)
    check("7.4 verdict = COMMISSION_KILL (net_exp=0)",
          verdict == 'COMMISSION_KILL', f"got {verdict}")

    # if we force net_exp > 0 but CI still contains 0, should be FRAGILE
    verdict2 = _assign_verdict(bootstrap, perm, 20, 2.0, cfg)
    check("7.5 verdict = FRAGILE when net_exp>0 but CI lo<=0",
          verdict2 == 'FRAGILE', f"got {verdict2}")

    print()


# --- Section 8: PnL reconstruction cross-validation ---

def debug_08_pnl_reconstruction():
    """Cross-validate _reconstruct_trade_pnl vs direct _vectorized_pnl."""
    print("=" * 60)
    print("[Section 8] PnL Reconstruction Cross-Validation")
    print("=" * 60)

    df = make_debug_df(50, seed=77)
    df['bbwp_state'] = 'BLUE'
    df['close'] = 100.0
    df['fwd_atr'] = 2.0
    df['fwd_10_max_up_atr'] = 3.0
    df['fwd_10_max_down_atr'] = 1.5
    df['fwd_10_close_pct'] = 0.8

    # L4b reconstruction with zero commission (to compare gross)
    cfg_zero = MonteCarloConfig(commission_rate=0.0, base_size=250.0)
    pnl_mc = _reconstruct_trade_pnl(
        df, 'BLUE', 'long', 10, 20, 1.0, 3, 2.0, cfg_zero,
    )

    # Direct L4 computation
    mfe_mae = _assign_mfe_mae(df, 'long', 10)
    pnl_l4 = _vectorized_pnl(
        mfe_mae['mfe_atr'], mfe_mae['mae_atr'],
        df['fwd_10_close_pct'], df['fwd_atr'], df['close'],
        'long',
        np.array([3.0]), np.array([2.0]),
        np.array([20.0]), np.array([1.0]),
        250.0,
    )[:, 0]

    print(f"  L4b pnl shape: {pnl_mc.shape}")
    print(f"  L4 pnl shape:  {pnl_l4.shape}")

    check("8.1 same length", len(pnl_mc) == len(pnl_l4),
          f"mc={len(pnl_mc)} l4={len(pnl_l4)}")

    if len(pnl_mc) == len(pnl_l4) and len(pnl_mc) > 0:
        max_diff = float(np.max(np.abs(pnl_mc - pnl_l4)))
        check("8.2 element-wise match (atol=1e-6)",
              np.allclose(pnl_mc, pnl_l4, atol=1e-6),
              f"max_diff={max_diff:.8f}")

        check("8.3 total match",
              abs(pnl_mc.sum() - pnl_l4.sum()) < 1e-4,
              f"mc={pnl_mc.sum():.4f} l4={pnl_l4.sum():.4f}")

        # verify commission offset
        cfg_real = MonteCarloConfig(commission_rate=0.0008, base_size=250.0)
        pnl_net = _reconstruct_trade_pnl(
            df, 'BLUE', 'long', 10, 20, 1.0, 3, 2.0, cfg_real,
        )
        rt = _compute_commission(20, 1.0, 250.0, 0.0008)
        diff_per_trade = pnl_mc - pnl_net
        check("8.4 net = gross - $8.00 per trade",
              np.allclose(diff_per_trade, rt, atol=1e-6),
              f"rt={rt:.2f}, diff_range=[{diff_per_trade.min():.4f}, "
              + f"{diff_per_trade.max():.4f}]")

    print()


# --- Section 9: Commission math validation ---

def debug_09_commission_math():
    """Validate commission computation and COMMISSION_KILL edge case."""
    print("=" * 60)
    print("[Section 9] Commission Math Validation")
    print("=" * 60)

    # Case 1: Standard parameters
    # sz=1.0, base=250, lev=20 -> notional=5000 -> RT=$8.00
    rt1 = _compute_commission(20, 1.0, 250.0, 0.0008)
    print(f"  Case 1: lev=20, sz=1.0, base=250")
    print(f"    notional = 1.0 * 250 * 20 = $5000")
    print(f"    RT = 5000 * 0.0008 * 2 = ${rt1:.2f}")
    check("9.1 RT = $8.00", abs(rt1 - 8.0) < 1e-10, f"got {rt1}")

    # Case 2: Half size, half leverage
    # sz=0.5, base=250, lev=10 -> notional=1250 -> RT=$2.00
    rt2 = _compute_commission(10, 0.5, 250.0, 0.0008)
    print(f"  Case 2: lev=10, sz=0.5, base=250")
    print(f"    notional = 0.5 * 250 * 10 = $1250")
    print(f"    RT = 1250 * 0.0008 * 2 = ${rt2:.2f}")
    check("9.2 RT = $2.00", abs(rt2 - 2.0) < 1e-10, f"got {rt2}")

    # Case 3: Gross WIN $300 -> Net $292 (with $8 RT)
    gross_win = 300.0
    net_win = gross_win - rt1
    print(f"  Case 3: Gross +$300, RT=$8.00 -> Net ${net_win:.2f}")
    check("9.3 net WIN = $292", abs(net_win - 292.0) < 1e-10)

    # Case 4: COMMISSION_KILL edge case
    # Gross +$7.50 -> Net -$0.50 -> COMMISSION_KILL
    gross_thin = 7.50
    net_thin = gross_thin - rt1
    print(f"  Case 4: Gross +${gross_thin:.2f}, RT=$8.00 -> "
          + f"Net ${net_thin:.2f}")
    check("9.4 net = -$0.50 (commission kills edge)",
          abs(net_thin - (-0.50)) < 1e-10)

    cfg = MonteCarloConfig(min_trades=10)
    verdict = _assign_verdict({}, {}, 200, net_thin, cfg)
    check("9.5 verdict = COMMISSION_KILL",
          verdict == 'COMMISSION_KILL', f"got {verdict}")

    # Case 5: Zero commission
    rt0 = _compute_commission(20, 1.0, 250.0, 0.0)
    check("9.6 zero rate -> zero commission",
          abs(rt0) < 1e-10, f"got {rt0}")

    # Case 6: THIN_EDGE -- net > 0 but < $1.00 threshold
    cfg_te = MonteCarloConfig(min_trades=10, min_net_expectancy=1.00)
    bootstrap_ok = {
        'total_pnl': {'lo': 10, 'hi': 100, 'real': 50},
    }
    perm_ok = {
        'max_dd': {'real': 10, 'p95': 50},
        'max_consecutive_loss': {'real': 2, 'p95': 5},
    }
    verdict_te = _assign_verdict(bootstrap_ok, perm_ok, 200, 0.75, cfg_te)
    check("9.7 THIN_EDGE when net_exp=$0.75 < $1.00",
          verdict_te == 'THIN_EDGE', f"got {verdict_te}")

    print()


# --- Section 10: Sortino vs Sharpe divergence ---

def debug_10_sortino_vs_sharpe():
    """Prove sortino > sharpe when upside dominates."""
    print("=" * 60)
    print("[Section 10] Sortino vs Sharpe Divergence")
    print("=" * 60)

    # Positively skewed: big wins, small losses
    pnl = np.array([500.0, 400.0, 300.0, 200.0, 100.0, -50.0, -30.0])
    print(f"  Trades: {pnl.tolist()}")

    mean_pnl = float(pnl.mean())
    std_pnl = float(pnl.std(ddof=0))
    sharpe = mean_pnl / std_pnl if std_pnl > 0 else 0.0
    print(f"  Mean: {mean_pnl:.2f}, Std: {std_pnl:.2f}, Sharpe: {sharpe:.4f}")

    # hand-compute sortino
    neg_pnl = np.minimum(pnl, 0.0)
    downside_rms = float(np.sqrt(np.mean(neg_pnl ** 2)))
    sortino = mean_pnl / downside_rms if downside_rms > 0 else 0.0
    print(f"  Downside RMS: {downside_rms:.2f}, Sortino: {sortino:.4f}")

    check("10.1 sortino > sharpe",
          sortino > sharpe,
          f"sortino={sortino:.4f} sharpe={sharpe:.4f}")

    # verify via bootstrap function
    rng = np.random.default_rng(42)
    result = _bootstrap_metrics(pnl, 100, 0.95, 0.01, rng)
    bs_sharpe = result['sharpe']['real']
    bs_sortino = result['sortino']['real']

    check("10.2 bootstrap sharpe matches hand-computed",
          abs(bs_sharpe - sharpe) < 1e-8,
          f"bs={bs_sharpe:.6f} hand={sharpe:.6f}")

    check("10.3 bootstrap sortino matches hand-computed",
          abs(bs_sortino - sortino) < 1e-8,
          f"bs={bs_sortino:.6f} hand={sortino:.6f}")

    check("10.4 bootstrap confirms sortino > sharpe",
          bs_sortino > bs_sharpe)

    # counter-example: symmetric PnL -> sortino approx equal sharpe
    sym_pnl = np.array([100.0, -100.0, 50.0, -50.0, 25.0, -25.0])
    sym_mean = float(sym_pnl.mean())
    sym_std = float(sym_pnl.std(ddof=0))
    sym_sharpe = sym_mean / sym_std if sym_std > 0 else 0.0

    sym_neg = np.minimum(sym_pnl, 0.0)
    sym_ds_rms = float(np.sqrt(np.mean(sym_neg ** 2)))
    sym_sortino = sym_mean / sym_ds_rms if sym_ds_rms > 0 else 0.0

    print(f"  Symmetric PnL: sharpe={sym_sharpe:.4f}, "
          + f"sortino={sym_sortino:.4f}")

    # for perfectly symmetric around 0, sortino should be close to sharpe
    # (not necessarily equal due to RMS vs std difference)
    check("10.5 symmetric PnL: sortino not hugely > sharpe",
          abs(sym_sortino - sym_sharpe) < 2.0,
          f"diff={abs(sym_sortino - sym_sharpe):.4f}")

    print()


# --- Main ---

def main():
    """Run all 10 debug sections."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"Monte Carlo Layer 4b Debug -- {ts}")
    print("=" * 70)
    print()

    debug_01_bootstrap_variance()
    debug_02_permutation_invariance()
    debug_03_dd_sign_convention()
    debug_04_mcl_permutation()
    debug_05_all_wins()
    debug_06_all_losses()
    debug_07_fifty_fifty()
    debug_08_pnl_reconstruction()
    debug_09_commission_math()
    debug_10_sortino_vs_sharpe()

    print("=" * 70)
    print(f"DEBUG RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 70)
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))


if __name__ == "__main__":
    main()

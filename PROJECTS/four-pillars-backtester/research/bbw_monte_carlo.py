"""Layer 4b: Monte Carlo validation of BBW Simulator results.

Pure computation. No I/O, no print(). Returns MonteCarloResult dataclass.
Input: DataFrame with L1+L2+L3 columns + lsg_top from Layer 4.
Output: Per-state verdicts, confidence intervals, overfit flags, equity bands.

Dual-method MC:
  Bootstrap (with replacement) for PnL/Sharpe/Sortino/PF confidence intervals.
  Permutation (without replacement) for max_dd/MCL path-dependent robustness.

Run: imported by scripts, not run directly.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
import time

from research.bbw_simulator import (
    SimulatorConfig, _assign_mfe_mae, _vectorized_pnl,
    _max_consecutive_loss, _max_consecutive_loss_2d,
)


# --- Config & Result dataclasses ---

@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo validation."""
    n_sims: int = 1000
    confidence: float = 0.95
    seed: int = 42
    min_trades: int = 100
    commission_rate: float = 0.0008
    base_size: float = 250.0
    equity_percentiles: list = field(
        default_factory=lambda: [5, 25, 50, 75, 95]
    )
    min_net_expectancy: float = 1.00
    max_mcl_threshold: int = 15
    convergence_threshold: float = 0.01


@dataclass
class MonteCarloResult:
    """Output container for run_monte_carlo."""
    state_verdicts: pd.DataFrame
    confidence_intervals: pd.DataFrame
    overfit_flags: pd.DataFrame
    equity_bands: dict
    summary: dict


# --- Helper functions ---

def _compute_commission(lev, sz, base_size, commission_rate):
    """Round-trip commission for one trade."""
    notional = sz * base_size * lev
    return notional * commission_rate * 2


def _reconstruct_trade_pnl(df, state, direction, window,
                            lev, sz, tgt, sl, config):
    """Reconstruct per-trade NET PnL array for one state and combo."""
    mask = df['bbwp_state'] == state
    sdf = df[mask].copy()

    fwd_col = f"fwd_{window}_max_up_atr"
    valid = sdf['fwd_atr'].notna() & sdf[fwd_col].notna()
    sdf = sdf[valid]

    if len(sdf) == 0:
        return np.array([], dtype=float)

    mfe_mae = _assign_mfe_mae(sdf, direction, window)
    close_pct = sdf[f"fwd_{window}_close_pct"]
    atr_i = sdf['fwd_atr']
    close_i = sdf['close']

    tgt_arr = np.array([tgt], dtype=float)
    sl_arr = np.array([sl], dtype=float)
    lev_arr = np.array([lev], dtype=float)
    sz_arr = np.array([sz], dtype=float)

    gross_pnl_2d = _vectorized_pnl(
        mfe_mae['mfe_atr'], mfe_mae['mae_atr'],
        close_pct, atr_i, close_i,
        direction, tgt_arr, sl_arr, lev_arr, sz_arr,
        config.base_size,
    )
    gross_pnl = gross_pnl_2d[:, 0]

    rt_comm = _compute_commission(
        lev, sz, config.base_size, config.commission_rate
    )
    net_pnl = gross_pnl - rt_comm
    return net_pnl


def _bootstrap_metrics(pnl_arr, n_sims, confidence, conv_threshold, rng):
    """Bootstrap resampling for PnL/Sharpe/Sortino/PF CIs plus convergence."""
    n = len(pnl_arr)
    if n == 0:
        return {}

    samples_2d = rng.choice(pnl_arr, size=(n_sims, n), replace=True)

    totals = samples_2d.sum(axis=1)
    means = samples_2d.mean(axis=1)
    stds = samples_2d.std(axis=1, ddof=0)

    with np.errstate(divide='ignore', invalid='ignore'):
        sharpes = np.where(stds > 0, means / stds, 0.0)

    neg_pnl = np.minimum(samples_2d, 0.0)
    downside_rms = np.sqrt(np.mean(neg_pnl ** 2, axis=1))
    with np.errstate(divide='ignore', invalid='ignore'):
        sortinos = np.where(downside_rms > 0, means / downside_rms, 0.0)

    win_sums = np.where(samples_2d > 0, samples_2d, 0.0).sum(axis=1)
    loss_sums_abs = np.abs(
        np.where(samples_2d < 0, samples_2d, 0.0).sum(axis=1)
    )
    with np.errstate(divide='ignore', invalid='ignore'):
        pfs = np.where(
            loss_sums_abs > 0,
            win_sums / loss_sums_abs,
            np.where(win_sums > 0, np.inf, np.nan),
        )

    lo_pct = (1 - confidence) / 2 * 100
    hi_pct = (1 + confidence) / 2 * 100

    real_total = float(pnl_arr.sum())
    real_mean = float(pnl_arr.mean())
    real_std = float(pnl_arr.std(ddof=0))
    real_sharpe = real_mean / real_std if real_std > 0 else 0.0

    real_neg = np.minimum(pnl_arr, 0.0)
    real_ds_rms = float(np.sqrt(np.mean(real_neg ** 2)))
    real_sortino = real_mean / real_ds_rms if real_ds_rms > 0 else 0.0

    real_wins = float(pnl_arr[pnl_arr > 0].sum())
    real_losses_abs = float(abs(pnl_arr[pnl_arr < 0].sum()))
    if real_losses_abs > 0:
        real_pf = real_wins / real_losses_abs
    elif real_wins > 0:
        real_pf = np.inf
    else:
        real_pf = np.nan

    def _ci(arr, real_val):
        """Compute CI and percentile rank for one metric."""
        finite = arr[np.isfinite(arr)]
        if len(finite) == 0:
            return {
                'real': real_val, 'lo': np.nan, 'hi': np.nan,
                'median': np.nan, 'pctl_rank': np.nan,
            }
        return {
            'real': float(real_val),
            'lo': float(np.percentile(finite, lo_pct)),
            'hi': float(np.percentile(finite, hi_pct)),
            'median': float(np.median(finite)),
            'pctl_rank': float((finite < real_val).mean() * 100),
        }

    conv = _check_convergence(totals, confidence, conv_threshold)

    return {
        'total_pnl': _ci(totals, real_total),
        'sharpe': _ci(sharpes, real_sharpe),
        'sortino': _ci(sortinos, real_sortino),
        'profit_factor': _ci(pfs, real_pf),
        'convergence_sims': conv,
    }


def _permutation_path_metrics(pnl_arr, n_sims, rng):
    """Permutation test for path-dependent metrics (DD, MCL)."""
    n = len(pnl_arr)
    if n == 0:
        return {}, np.empty((0, 0))

    perm_matrix = np.empty((n_sims, n), dtype=float)
    for i in range(n_sims):
        perm_matrix[i] = rng.permutation(pnl_arr)

    equity_2d = np.cumsum(perm_matrix, axis=1)
    peak_2d = np.maximum.accumulate(equity_2d, axis=1)
    dd_2d = peak_2d - equity_2d
    max_dds = dd_2d.max(axis=1)

    mcls = _max_consecutive_loss_2d(perm_matrix.T)

    real_equity = np.cumsum(pnl_arr)
    real_peak = np.maximum.accumulate(real_equity)
    real_dd = float(np.max(real_peak - real_equity))
    real_mcl = _max_consecutive_loss(pnl_arr)

    def _pctls(arr, real_val):
        """Compute percentile summary for one metric."""
        return {
            'real': float(real_val),
            'p5': float(np.percentile(arr, 5)),
            'p25': float(np.percentile(arr, 25)),
            'p50': float(np.percentile(arr, 50)),
            'p75': float(np.percentile(arr, 75)),
            'p95': float(np.percentile(arr, 95)),
        }

    results = {
        'max_dd': _pctls(max_dds, real_dd),
        'max_consecutive_loss': _pctls(mcls.astype(float), float(real_mcl)),
    }

    return results, equity_2d


def _compute_equity_bands(pnl_arr, equity_2d, percentiles):
    """Compute percentile bands from permuted equity curves."""
    n = len(pnl_arr)
    if n == 0 or equity_2d.size == 0:
        return pd.DataFrame()

    bands = np.percentile(equity_2d, percentiles, axis=0)
    real_equity = np.cumsum(pnl_arr)

    data = {'bar_index': np.arange(n)}
    for i, p in enumerate(percentiles):
        data[f"p{p}"] = bands[i]
    data['real'] = real_equity

    return pd.DataFrame(data)


def _check_convergence(metric_dist, confidence, threshold):
    """Find convergence point where CI width stabilizes."""
    n = len(metric_dist)
    if n < 200:
        return n

    lo_pct = (1 - confidence) / 2 * 100
    hi_pct = (1 + confidence) / 2 * 100

    prev_width = None
    stable_count = 0

    for check_n in range(200, n + 1, 50):
        subset = metric_dist[:check_n]
        width = np.percentile(subset, hi_pct) - np.percentile(subset, lo_pct)

        if prev_width is not None and abs(prev_width) > 1e-10:
            rel_change = abs(width - prev_width) / abs(prev_width)
            if rel_change < threshold:
                stable_count += 1
                if stable_count >= 2:
                    return check_n
            else:
                stable_count = 0

        prev_width = width

    return n


def _assign_verdict(bootstrap, permutation, n_trades, net_exp, config):
    """Assign robustness verdict based on MC results."""
    if n_trades < config.min_trades:
        return 'INSUFFICIENT_DATA'

    if net_exp <= 0:
        return 'COMMISSION_KILL'

    if net_exp < config.min_net_expectancy:
        return 'THIN_EDGE'

    pnl_ci_lo = bootstrap.get('total_pnl', {}).get('lo', np.nan)
    dd_real = permutation.get('max_dd', {}).get('real', 0)
    dd_p95 = permutation.get('max_dd', {}).get('p95', 0)

    pnl_fragile = np.isnan(pnl_ci_lo) or pnl_ci_lo <= 0
    dd_fragile = dd_real > dd_p95

    if pnl_fragile or dd_fragile:
        return 'FRAGILE'

    mcl_real = permutation.get('max_consecutive_loss', {}).get('real', 0)
    if mcl_real > config.max_mcl_threshold:
        return 'MARGINAL'

    return 'ROBUST'


def _build_overfit_flags(state, window, direction, combo, n_trades,
                         gross_exp, net_exp, rt_comm,
                         bootstrap, permutation, verdict, config):
    """Build one row of the overfit_flags DataFrame."""
    pnl_ci = bootstrap.get('total_pnl', {})
    dd_perm = permutation.get('max_dd', {})
    mcl_perm = permutation.get('max_consecutive_loss', {})
    sharpe_ci = bootstrap.get('sharpe', {})
    sortino_ci = bootstrap.get('sortino', {})

    reasons = []
    if verdict == 'INSUFFICIENT_DATA':
        reasons.append(
            "n_trades=" + str(n_trades) + " < " + str(config.min_trades)
        )
    if verdict == 'COMMISSION_KILL':
        reasons.append(
            "net_exp=$" + f"{net_exp:.2f}" + " <= 0 after $"
            + f"{rt_comm:.2f}" + " RT commission"
        )
    if verdict == 'THIN_EDGE':
        reasons.append(
            "net_exp=$" + f"{net_exp:.2f}" + " < $"
            + f"{config.min_net_expectancy:.2f}" + " threshold"
        )

    pnl_lo = pnl_ci.get('lo', 0)
    if not np.isnan(pnl_lo) and pnl_lo <= 0 and n_trades >= config.min_trades:
        reasons.append("bootstrap PnL CI lo=$" + f"{pnl_lo:.2f}" + " <= 0")

    dd_real = dd_perm.get('real', 0)
    dd_p95 = dd_perm.get('p95', 0)
    if dd_real > dd_p95 and n_trades >= config.min_trades:
        reasons.append(
            "real DD $" + f"{dd_real:.2f}" + " > p95 $" + f"{dd_p95:.2f}"
        )

    return {
        'bbwp_state': state,
        'window': window,
        'direction': direction,
        'leverage': combo.get('leverage', 0),
        'target_atr': combo.get('target_atr', 0),
        'sl_atr': combo.get('sl_atr', 0),
        'n_trades': n_trades,
        'gross_expectancy': gross_exp,
        'net_expectancy': net_exp,
        'rt_commission': rt_comm,
        'bootstrap_pnl_lo': pnl_ci.get('lo', np.nan),
        'bootstrap_pnl_hi': pnl_ci.get('hi', np.nan),
        'real_sharpe': sharpe_ci.get('real', np.nan),
        'real_sortino': sortino_ci.get('real', np.nan),
        'perm_dd_real': dd_real,
        'perm_dd_p95': dd_p95,
        'perm_mcl_real': mcl_perm.get('real', 0),
        'perm_mcl_p95': mcl_perm.get('p95', 0),
        'sample_size_flag': n_trades < config.min_trades,
        'commission_kill_flag': net_exp <= 0,
        'pnl_overfit_flag': (
            not np.isnan(pnl_lo) and pnl_lo <= 0
        ),
        'dd_fragile_flag': dd_real > dd_p95,
        'verdict': verdict,
        'reason': '; '.join(reasons) if reasons else 'All checks passed',
    }


# --- Main entry point ---

def run_monte_carlo(df, lsg_top, sim_config=None, mc_config=None):
    """Run Monte Carlo validation on Layer 4 top combos."""
    t0 = time.time()
    if mc_config is None:
        mc_config = MonteCarloConfig()
    if sim_config is None:
        sim_config = SimulatorConfig()

    rng = np.random.default_rng(mc_config.seed)

    verdict_rows = []
    ci_rows = []
    overfit_rows = []
    equity_bands_dict = {}

    if lsg_top.empty:
        return MonteCarloResult(
            state_verdicts=pd.DataFrame(),
            confidence_intervals=pd.DataFrame(),
            overfit_flags=pd.DataFrame(),
            equity_bands={},
            summary={
                'n_states': 0, 'n_robust': 0, 'n_fragile': 0,
                'n_commission_kill': 0, 'n_sims': mc_config.n_sims,
                'runtime_sec': 0,
            },
        )

    groups = lsg_top.groupby(
        ['bbwp_state', 'window', 'direction'], observed=True
    )

    for (state, window, direction), gdf in groups:
        best = gdf.sort_values('expectancy_usd', ascending=False).iloc[0]
        lev = float(best['leverage'])
        sz = float(best['size_frac'])
        tgt = float(best['target_atr'])
        sl = float(best['sl_atr'])

        net_pnl = _reconstruct_trade_pnl(
            df, state, direction, window, lev, sz, tgt, sl, mc_config,
        )
        n_trades = len(net_pnl)

        rt_comm = _compute_commission(
            lev, sz, mc_config.base_size, mc_config.commission_rate
        )
        gross_exp = float(net_pnl.mean() + rt_comm) if n_trades > 0 else 0.0
        net_exp = float(net_pnl.mean()) if n_trades > 0 else 0.0

        bootstrap = _bootstrap_metrics(
            net_pnl, mc_config.n_sims, mc_config.confidence,
            mc_config.convergence_threshold, rng,
        )

        permutation, equity_2d = _permutation_path_metrics(
            net_pnl, mc_config.n_sims, rng,
        )

        bands_df = _compute_equity_bands(
            net_pnl, equity_2d, mc_config.equity_percentiles,
        )
        state_key = f"{state}_{window}_{direction}"
        equity_bands_dict[state_key] = bands_df

        conv_point = bootstrap.get('convergence_sims', mc_config.n_sims)

        verdict = _assign_verdict(
            bootstrap, permutation, n_trades, net_exp, mc_config,
        )

        verdict_rows.append({
            'bbwp_state': state,
            'window': window,
            'direction': direction,
            'n_trades': n_trades,
            'gross_expectancy': gross_exp,
            'net_expectancy': net_exp,
            'rt_commission': rt_comm,
            'verdict': verdict,
            'convergence_sims': conv_point,
        })

        for metric_name, metric_data in bootstrap.items():
            if metric_name == 'convergence_sims':
                continue
            ci_rows.append({
                'bbwp_state': state,
                'window': window,
                'direction': direction,
                'metric': metric_name,
                'real': metric_data.get('real', np.nan),
                'ci_lower': metric_data.get('lo', np.nan),
                'ci_upper': metric_data.get('hi', np.nan),
                'ci_median': metric_data.get('median', np.nan),
                'pctl_rank': metric_data.get('pctl_rank', np.nan),
            })

        for metric_name, metric_data in permutation.items():
            ci_rows.append({
                'bbwp_state': state,
                'window': window,
                'direction': direction,
                'metric': metric_name,
                'real': metric_data.get('real', np.nan),
                'ci_lower': metric_data.get('p5', np.nan),
                'ci_upper': metric_data.get('p95', np.nan),
                'ci_median': metric_data.get('p50', np.nan),
                'pctl_rank': np.nan,
            })

        combo_dict = {
            'leverage': lev, 'target_atr': tgt, 'sl_atr': sl,
        }
        overfit_rows.append(_build_overfit_flags(
            state, window, direction, combo_dict, n_trades,
            gross_exp, net_exp, rt_comm,
            bootstrap, permutation, verdict, mc_config,
        ))

    runtime = time.time() - t0

    verdicts_df = pd.DataFrame(verdict_rows)
    n_robust = int(
        (verdicts_df['verdict'] == 'ROBUST').sum()
    ) if not verdicts_df.empty else 0
    n_fragile = int(
        (verdicts_df['verdict'] == 'FRAGILE').sum()
    ) if not verdicts_df.empty else 0
    n_ck = int(
        (verdicts_df['verdict'] == 'COMMISSION_KILL').sum()
    ) if not verdicts_df.empty else 0

    if 'symbol' in df.columns and not verdicts_df.empty:
        sym = df['symbol'].iloc[0]
        verdicts_df.insert(0, 'symbol', sym)

    return MonteCarloResult(
        state_verdicts=verdicts_df,
        confidence_intervals=pd.DataFrame(ci_rows),
        overfit_flags=pd.DataFrame(overfit_rows),
        equity_bands=equity_bands_dict,
        summary={
            'n_states': len(verdict_rows),
            'n_robust': n_robust,
            'n_fragile': n_fragile,
            'n_commission_kill': n_ck,
            'n_sims': mc_config.n_sims,
            'runtime_sec': round(runtime, 2),
        },
    )

"""Layer 4: BBW Simulator Engine -- LSG optimization per BBW state.

Pure computation. No I/O, no print(). Returns SimulatorResult dataclass.
Input: DataFrame with all L1+L2+L3 columns plus OHLCV.
Output: Group stats, LSG grid results, scaling results.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from itertools import product
from scipy.stats import skew, kurtosis
import time


# --- Column constants ---

L1_COLS = [
    'bbwp_value', 'bbwp_spectrum', 'bbwp_state',
    'bbwp_is_blue_bar', 'bbwp_is_red_bar',
    'bbwp_ma_cross_up', 'bbwp_ma_cross_down',
]

L2_COLS = [
    'bbw_seq_prev_color', 'bbw_seq_color_changed', 'bbw_seq_bars_in_color',
    'bbw_seq_bars_in_state', 'bbw_seq_direction', 'bbw_seq_skip_detected',
    'bbw_seq_pattern_id', 'bbw_seq_from_blue_bars', 'bbw_seq_from_red_bars',
]

L3_FWD_SUFFIXES = [
    'max_up_pct', 'max_down_pct', 'max_up_atr', 'max_down_atr',
    'close_pct', 'direction', 'max_range_atr', 'proper_move',
]

L3_OTHER = ['fwd_atr']

ANALYSIS_GROUPS = {
    'A_state':       'bbwp_state',
    'B_spectrum':    'bbwp_spectrum',
    'C_direction':   'bbw_seq_direction',
    'D_pattern':     'bbw_seq_pattern_id',
    'E_skip':        'bbw_seq_skip_detected',
    'F_duration':    'duration_bin',
    'G_ma_spectrum': 'ma_spectrum_combo',
}


# --- Config & Result dataclasses ---

@dataclass
class SimulatorConfig:
    """Configuration for BBW simulator grid search."""
    leverage_grid: list = field(default_factory=lambda: [5, 10, 15, 20])
    size_grid: list = field(default_factory=lambda: [0.25, 0.5, 0.75, 1.0])
    target_atr_grid: list = field(default_factory=lambda: [1, 2, 3, 4, 5, 6])
    sl_atr_grid: list = field(default_factory=lambda: [1.0, 1.5, 2.0, 3.0])
    base_size: float = 250.0
    windows: list = field(default_factory=lambda: [10, 20])
    directions: list = field(default_factory=lambda: ['long', 'short'])
    scaling_scenarios: list = field(default_factory=lambda: [
        ('NORMAL', 0.50, 'BLUE', 0.50, 10),
        ('NORMAL', 0.50, 'BLUE', 0.50, 20),
        ('NORMAL', 0.50, 'BLUE_DOUBLE', 0.50, 20),
        ('BLUE', 0.50, 'BLUE_DOUBLE', 0.50, 10),
        ('MA_CROSS_UP', 0.50, 'BLUE', 0.50, 10),
        ('NORMAL', 0.25, 'BLUE', 0.75, 15),
    ])
    min_sample_size: int = 30
    scaling_use_threshold: float = 0.30
    scaling_edge_threshold: float = 0.20
    bars_in_state_bins: list = field(
        default_factory=lambda: [-1, 5, 10, 20, 50, 100, 999999]
    )
    bars_in_state_labels: list = field(
        default_factory=lambda: ['1-5', '6-10', '11-20', '21-50', '51-100', '100+']
    )


@dataclass
class SimulatorResult:
    """Output container for run_simulator."""
    group_stats: dict
    lsg_results: pd.DataFrame
    lsg_top: pd.DataFrame
    scaling_results: pd.DataFrame
    summary: dict


# --- Helper functions ---

def _build_l3_cols(windows):
    """Build L3 column names from window list."""
    cols = list(L3_OTHER)
    for w in windows:
        cols.extend([f"fwd_{w}_{s}" for s in L3_FWD_SUFFIXES])
    return cols


def _validate_input(df, config):
    """Validate all required columns present, raise ValueError if missing."""
    required = (
        list(L1_COLS) + list(L2_COLS)
        + _build_l3_cols(config.windows) + ['close']
    )
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))


def _add_derived_columns(df, config):
    """Add duration_bin and ma_spectrum_combo columns in-place."""
    df['duration_bin'] = pd.cut(
        df['bbw_seq_bars_in_state'],
        bins=config.bars_in_state_bins,
        labels=config.bars_in_state_labels,
        right=True,
    )
    conditions = [
        df['bbwp_ma_cross_up'] == True,
        df['bbwp_ma_cross_down'] == True,
    ]
    choices = ['cross_up', 'cross_down']
    ma_state = pd.Series(
        np.select(conditions, choices, default='no_cross'), index=df.index
    )
    spectrum_valid = df['bbwp_spectrum'].notna()
    combo = pd.Series(None, index=df.index, dtype=object)
    combo[spectrum_valid] = (
        ma_state[spectrum_valid] + '_' + df.loc[spectrum_valid, 'bbwp_spectrum']
    )
    df['ma_spectrum_combo'] = combo


def _assign_mfe_mae(df, direction, window):
    """Assign MFE/MAE based on trade direction and forward window."""
    p = f"fwd_{window}_"
    if direction == 'long':
        return pd.DataFrame({
            'mfe_atr': df[p + 'max_up_atr'],
            'mae_atr': df[p + 'max_down_atr'],
            'mfe_pct': df[p + 'max_up_pct'],
            'mae_pct': df[p + 'max_down_pct'].abs(),
        }, index=df.index)
    else:
        return pd.DataFrame({
            'mfe_atr': df[p + 'max_down_atr'],
            'mae_atr': df[p + 'max_up_atr'],
            'mfe_pct': df[p + 'max_down_pct'].abs(),
            'mae_pct': df[p + 'max_up_pct'],
        }, index=df.index)


def _compute_group_stats(df, group_col, windows, directions):
    """Compute MFE/MAE/edge statistics per group value x window x direction."""
    rows = []
    for w in windows:
        for d in directions:
            mfe_mae = _assign_mfe_mae(df, d, w)
            cpct_col = f"fwd_{w}_close_pct"
            dir_col = f"fwd_{w}_direction"
            range_col = f"fwd_{w}_max_range_atr"
            proper_col = f"fwd_{w}_proper_move"
            bias_value = 'up' if d == 'long' else 'down'

            for gval, gdf in df.groupby(group_col, observed=True):
                n = len(gdf)
                if n == 0:
                    continue
                mfe = mfe_mae.loc[gdf.index, 'mfe_atr']
                mae = mfe_mae.loc[gdf.index, 'mae_atr']
                cpct = gdf[cpct_col].astype(float)
                mean_mfe = float(mfe.mean())
                mean_mae = float(mae.mean())
                std_cpct = float(cpct.std())
                cpct_clean = cpct.dropna()
                rows.append({
                    'group_value': str(gval),
                    'window': w,
                    'direction': d,
                    'n_bars': n,
                    'mean_mfe_atr': mean_mfe,
                    'median_mfe_atr': float(mfe.median()),
                    'p90_mfe_atr': float(mfe.quantile(0.90)),
                    'mean_mae_atr': mean_mae,
                    'median_mae_atr': float(mae.median()),
                    'p90_mae_atr': float(mae.quantile(0.90)),
                    'mfe_mae_ratio': (
                        mean_mfe / mean_mae if mean_mae > 0 else np.inf
                    ),
                    'mean_range_atr': float(gdf[range_col].astype(float).mean()),
                    'proper_move_pct': float(
                        gdf[proper_col].astype(float).mean()
                    ),
                    'directional_bias': float(
                        (gdf[dir_col] == bias_value).sum() / n
                    ),
                    'mean_close_pct': float(cpct.mean()),
                    'std_close_pct': std_cpct,
                    'skew_close_pct': (
                        float(skew(cpct_clean)) if len(cpct_clean) > 2
                        else np.nan
                    ),
                    'kurtosis_close_pct': (
                        float(kurtosis(cpct_clean)) if len(cpct_clean) > 3
                        else np.nan
                    ),
                    'edge_score': (
                        (mean_mfe - mean_mae) / std_cpct
                        if std_cpct > 0 else np.nan
                    ),
                })
    return pd.DataFrame(rows)


def _max_consecutive_loss(pnl_arr):
    """Max consecutive losing trades using run-length encoding."""
    is_loss = (np.asarray(pnl_arr) < 0).astype(int)
    if len(is_loss) == 0 or is_loss.sum() == 0:
        return 0
    changes = np.diff(np.concatenate([[0], is_loss, [0]]))
    starts = np.where(changes == 1)[0]
    ends = np.where(changes == -1)[0]
    if len(starts) == 0:
        return 0
    return int(np.max(ends - starts))


def _max_consecutive_loss_2d(pnl_2d):
    """Max consecutive loss per combo column, semi-vectorized over bars."""
    n_bars, n_combos = pnl_2d.shape
    if n_bars == 0:
        return np.zeros(n_combos, dtype=int)
    is_loss = (pnl_2d < 0).astype(int)
    counts = np.zeros((n_bars, n_combos), dtype=int)
    counts[0] = is_loss[0]
    for i in range(1, n_bars):
        counts[i] = (counts[i - 1] + 1) * is_loss[i]
    return counts.max(axis=0)


def _vectorized_pnl(mfe_atr, mae_atr, close_pct, atr_i, close_i,
                     direction, tgt_arr, sl_arr, lev_arr, sz_arr, base_size):
    """Vectorized PnL for all combos via numpy broadcasting."""
    mfe_2d = np.asarray(mfe_atr, dtype=float).reshape(-1, 1)
    mae_2d = np.asarray(mae_atr, dtype=float).reshape(-1, 1)
    tgt_2d = np.asarray(tgt_arr, dtype=float).reshape(1, -1)
    sl_2d = np.asarray(sl_arr, dtype=float).reshape(1, -1)

    hit_tp = mfe_2d >= tgt_2d
    hit_sl = mae_2d >= sl_2d

    win = hit_tp & ~hit_sl
    loss = hit_sl & ~hit_tp

    atr_2d = np.asarray(atr_i, dtype=float).reshape(-1, 1)
    close_2d = np.asarray(close_i, dtype=float).reshape(-1, 1)
    notional_2d = (
        np.asarray(sz_arr, dtype=float)
        * base_size
        * np.asarray(lev_arr, dtype=float)
    ).reshape(1, -1)

    win_pnl = tgt_2d * atr_2d / close_2d * notional_2d
    loss_pnl = -(sl_2d * atr_2d / close_2d * notional_2d)

    close_pct_2d = np.asarray(close_pct, dtype=float).reshape(-1, 1)
    dir_sign = 1.0 if direction == 'long' else -1.0
    fallback_pnl = dir_sign * close_pct_2d / 100.0 * notional_2d

    pnl = np.where(win, win_pnl, np.where(loss, loss_pnl, fallback_pnl))
    return pnl


def _lsg_grid_search(df, config):
    """Full LSG grid search per state x direction x window."""
    combos = list(product(
        config.leverage_grid, config.size_grid,
        config.target_atr_grid, config.sl_atr_grid,
    ))
    combos_arr = np.array(combos, dtype=float)
    lev_arr = combos_arr[:, 0]
    sz_arr = combos_arr[:, 1]
    tgt_arr = combos_arr[:, 2]
    sl_arr = combos_arr[:, 3]
    n_combos = len(combos)

    combo_lev = np.array([c[0] for c in combos])
    combo_sz = np.array([c[1] for c in combos])
    combo_tgt = np.array([c[2] for c in combos])
    combo_sl = np.array([c[3] for c in combos])

    chunks = []
    states = df['bbwp_state'].dropna().unique()

    for window in config.windows:
        for direction in config.directions:
            mfe_mae = _assign_mfe_mae(df, direction, window)
            close_pct = df[f"fwd_{window}_close_pct"]
            atr_i = df['fwd_atr']
            close_i = df['close']

            for state in states:
                mask = df['bbwp_state'] == state
                idx = df.index[mask]
                n_trades = len(idx)
                if n_trades == 0:
                    continue

                pnl_2d = _vectorized_pnl(
                    mfe_mae.loc[idx, 'mfe_atr'],
                    mfe_mae.loc[idx, 'mae_atr'],
                    close_pct.loc[idx],
                    atr_i.loc[idx],
                    close_i.loc[idx],
                    direction, tgt_arr, sl_arr, lev_arr, sz_arr,
                    config.base_size,
                )

                wins_mask = pnl_2d > 0
                losses_mask = pnl_2d < 0
                win_count = wins_mask.sum(axis=0)
                loss_count = losses_mask.sum(axis=0)

                win_rate = win_count / n_trades
                win_sum = np.where(wins_mask, pnl_2d, 0).sum(axis=0)
                loss_sum = np.where(losses_mask, pnl_2d, 0).sum(axis=0)
                loss_sum_abs = np.abs(loss_sum)

                with np.errstate(divide='ignore', invalid='ignore'):
                    avg_win = np.where(win_count > 0, win_sum / win_count, 0.0)
                    avg_loss = np.where(
                        loss_count > 0, loss_sum / loss_count, 0.0
                    )
                expectancy = pnl_2d.mean(axis=0)
                total_pnl = pnl_2d.sum(axis=0)

                pf = np.full(n_combos, np.nan)
                both = (win_sum > 0) & (loss_sum_abs > 0)
                only_w = (win_sum > 0) & (loss_sum_abs == 0)
                only_l = (win_sum == 0) & (loss_sum_abs > 0)
                pf[both] = win_sum[both] / loss_sum_abs[both]
                pf[only_w] = np.inf
                pf[only_l] = 0.0

                std_pnl = pnl_2d.std(axis=0)
                with np.errstate(divide='ignore', invalid='ignore'):
                    sharpe = np.where(std_pnl > 0, expectancy / std_pnl, np.nan)

                cumsum_2d = np.cumsum(pnl_2d, axis=0)
                running_max = np.maximum.accumulate(cumsum_2d, axis=0)
                dd_2d = running_max - cumsum_2d
                max_dd = dd_2d.max(axis=0) if n_trades > 0 else np.zeros(n_combos)

                with np.errstate(divide='ignore', invalid='ignore'):
                    calmar = np.where(max_dd > 0, total_pnl / max_dd, np.nan)
                mcl = _max_consecutive_loss_2d(pnl_2d)

                chunk = pd.DataFrame({
                    'bbwp_state': state,
                    'window': window,
                    'direction': direction,
                    'leverage': combo_lev,
                    'size_frac': combo_sz,
                    'target_atr': combo_tgt,
                    'sl_atr': combo_sl,
                    'n_trades': n_trades,
                    'win_rate': win_rate,
                    'avg_win_usd': avg_win,
                    'avg_loss_usd': avg_loss,
                    'expectancy_usd': expectancy,
                    'total_pnl_usd': total_pnl,
                    'profit_factor': pf,
                    'max_consecutive_loss': mcl.astype(int),
                    'sharpe_approx': sharpe,
                    'max_drawdown_usd': max_dd,
                    'calmar_approx': calmar,
                })
                chunks.append(chunk)

    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)


def _extract_top_combos(lsg_results, config, n_top=3):
    """Top N combos per state x window x direction by expectancy."""
    if lsg_results.empty:
        return lsg_results
    filtered = lsg_results[lsg_results['n_trades'] >= config.min_sample_size]
    if filtered.empty:
        return filtered
    top = (
        filtered
        .sort_values('expectancy_usd', ascending=False)
        .groupby(['bbwp_state', 'window', 'direction'], observed=True)
        .head(n_top)
        .reset_index(drop=True)
    )
    return top


def _scaling_simulation(df, scenarios, config, lsg_top):
    """Scaling sequence simulation with forward state lookup."""
    rows = []
    states_arr = df['bbwp_state'].values
    n_total = len(df)
    w = config.windows[0]

    for entry_state, entry_sz, add_state, add_sz, max_wait in scenarios:
        top_for = lsg_top[
            (lsg_top['bbwp_state'] == entry_state)
            & (lsg_top['window'] == w)
            & (lsg_top['direction'] == 'long')
        ]
        if top_for.empty:
            rows.append({
                'entry_state': entry_state,
                'add_trigger_state': add_state,
                'entry_size_frac': entry_sz,
                'add_size_frac': add_sz,
                'max_bars_to_wait': max_wait,
                'n_entry_bars': 0, 'n_triggered': 0,
                'triggered_pct': 0.0,
                'mean_base_pnl': np.nan, 'mean_scaled_pnl': np.nan,
                'edge_pct': np.nan, 'verdict': 'SKIP',
            })
            continue

        best = top_for.iloc[0]
        best_tgt = float(best['target_atr'])
        best_sl = float(best['sl_atr'])
        best_lev = float(best['leverage'])

        entry_indices = np.where(states_arr == entry_state)[0]
        n_entry = len(entry_indices)
        if n_entry == 0:
            rows.append({
                'entry_state': entry_state,
                'add_trigger_state': add_state,
                'entry_size_frac': entry_sz,
                'add_size_frac': add_sz,
                'max_bars_to_wait': max_wait,
                'n_entry_bars': 0, 'n_triggered': 0,
                'triggered_pct': 0.0,
                'mean_base_pnl': np.nan, 'mean_scaled_pnl': np.nan,
                'edge_pct': np.nan, 'verdict': 'SKIP',
            })
            continue

        mfe_mae = _assign_mfe_mae(df, 'long', w)
        cpct_s = df[f"fwd_{w}_close_pct"]
        atr_s = df['fwd_atr']
        cls_s = df['close']

        triggered_count = 0
        base_pnls = []
        scaled_pnls = []

        for ei in entry_indices:
            mfe_v = float(mfe_mae.iloc[ei]['mfe_atr'])
            mae_v = float(mfe_mae.iloc[ei]['mae_atr'])
            cpct_v = float(cpct_s.iloc[ei])
            atr_v = float(atr_s.iloc[ei])
            cls_v = float(cls_s.iloc[ei])

            if np.isnan(mfe_v) or np.isnan(atr_v) or cls_v == 0:
                continue

            notional_base = entry_sz * config.base_size * best_lev
            if mfe_v >= best_tgt and mae_v < best_sl:
                base_pnl = (best_tgt * atr_v / cls_v) * notional_base
            elif mae_v >= best_sl and mfe_v < best_tgt:
                base_pnl = -(best_sl * atr_v / cls_v) * notional_base
            else:
                base_pnl = cpct_v / 100.0 * notional_base
            base_pnls.append(base_pnl)

            trigger_j = None
            for j in range(ei + 1, min(ei + max_wait + 1, n_total)):
                if states_arr[j] == add_state:
                    trigger_j = j
                    break

            if trigger_j is not None:
                triggered_count += 1
                notional_add = add_sz * config.base_size * best_lev
                mfe_a = float(mfe_mae.iloc[trigger_j]['mfe_atr'])
                mae_a = float(mfe_mae.iloc[trigger_j]['mae_atr'])
                cpct_a = float(cpct_s.iloc[trigger_j])
                atr_a = float(atr_s.iloc[trigger_j])
                cls_a = float(cls_s.iloc[trigger_j])

                if np.isnan(mfe_a) or np.isnan(atr_a) or cls_a == 0:
                    scaled_pnls.append(base_pnl)
                    continue
                if mfe_a >= best_tgt and mae_a < best_sl:
                    add_pnl = (best_tgt * atr_a / cls_a) * notional_add
                elif mae_a >= best_sl and mfe_a < best_tgt:
                    add_pnl = -(best_sl * atr_a / cls_a) * notional_add
                else:
                    add_pnl = cpct_a / 100.0 * notional_add
                scaled_pnls.append(base_pnl + add_pnl)
            else:
                scaled_pnls.append(base_pnl)

        trig_pct = triggered_count / n_entry if n_entry > 0 else 0.0
        mean_base = float(np.mean(base_pnls)) if base_pnls else np.nan
        mean_scaled = float(np.mean(scaled_pnls)) if scaled_pnls else np.nan

        if abs(mean_base) < 1e-10:
            edge_pct = np.nan
        else:
            edge_pct = (mean_scaled - mean_base) / abs(mean_base) * 100

        if (trig_pct >= config.scaling_use_threshold
                and not np.isnan(edge_pct)
                and edge_pct >= config.scaling_edge_threshold * 100):
            verdict = 'USE'
        elif trig_pct < 0.15:
            verdict = 'SKIP'
        else:
            verdict = 'MARGINAL'

        rows.append({
            'entry_state': entry_state,
            'add_trigger_state': add_state,
            'entry_size_frac': entry_sz,
            'add_size_frac': add_sz,
            'max_bars_to_wait': max_wait,
            'n_entry_bars': n_entry,
            'n_triggered': triggered_count,
            'triggered_pct': trig_pct,
            'mean_base_pnl': mean_base,
            'mean_scaled_pnl': mean_scaled,
            'edge_pct': edge_pct,
            'verdict': verdict,
        })

    return pd.DataFrame(rows)


# --- Main entry point ---

def run_simulator(df, config=None):
    """Run full BBW simulator on L1+L2+L3 DataFrame."""
    t0 = time.time()
    if config is None:
        config = SimulatorConfig()

    _validate_input(df, config)

    valid_mask = df['fwd_atr'].notna()
    for w in config.windows:
        valid_mask = valid_mask & df[f"fwd_{w}_max_up_atr"].notna()
    df_valid = df[valid_mask].copy()

    _add_derived_columns(df_valid, config)

    group_stats = {}
    for gname, gcol in ANALYSIS_GROUPS.items():
        group_stats[gname] = _compute_group_stats(
            df_valid, gcol, config.windows, config.directions
        )

    lsg_results = _lsg_grid_search(df_valid, config)
    lsg_top = _extract_top_combos(lsg_results, config, n_top=3)

    scaling_results = _scaling_simulation(
        df_valid, config.scaling_scenarios, config, lsg_top
    )

    runtime = time.time() - t0
    return SimulatorResult(
        group_stats=group_stats,
        lsg_results=lsg_results,
        lsg_top=lsg_top,
        scaling_results=scaling_results,
        summary={
            'n_bars_total': len(df),
            'n_bars_valid': len(df_valid),
            'n_states': int(df_valid['bbwp_state'].nunique()),
            'n_lsg_combos': len(lsg_results),
            'n_scaling_scenarios': len(scaling_results),
            'runtime_sec': round(runtime, 2),
        },
    )

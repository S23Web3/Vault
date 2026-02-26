"""Layer 4 Debug & Math Validator: BBW Simulator Engine.

Hand-computed values for audit-level verification.
6 sections, 50+ checks.
Run: python scripts/debug_bbw_simulator.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_simulator import (
    SimulatorConfig, _assign_mfe_mae, _vectorized_pnl,
    _lsg_grid_search, _compute_group_stats, _add_derived_columns,
    _scaling_simulation, _extract_top_combos,
    _max_consecutive_loss, _max_consecutive_loss_2d, run_simulator,
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


def approx(a, b, tol=1e-6):
    """Check approximate equality."""
    return abs(float(a) - float(b)) < tol


def make_base_df(n, state='BLUE', close_val=100.0, atr_val=2.0):
    """Create minimal L1+L2+L3 DataFrame for debug tests."""
    df = pd.DataFrame({
        'open': close_val, 'high': close_val + 1, 'low': close_val - 1,
        'close': close_val, 'base_vol': 1000.0,
        'bbwp_value': 50.0, 'bbwp_spectrum': 'green',
        'bbwp_state': state,
        'bbwp_is_blue_bar': False, 'bbwp_is_red_bar': False,
        'bbwp_ma_cross_up': False, 'bbwp_ma_cross_down': False,
        'bbw_seq_prev_color': 'blue',
        'bbw_seq_color_changed': False,
        'bbw_seq_bars_in_color': 5,
        'bbw_seq_bars_in_state': 5,
        'bbw_seq_direction': 'expanding',
        'bbw_seq_skip_detected': False,
        'bbw_seq_pattern_id': 'BG',
        'bbw_seq_from_blue_bars': 10.0,
        'bbw_seq_from_red_bars': 20.0,
        'fwd_atr': atr_val,
        'fwd_10_max_up_pct': 0.0, 'fwd_10_max_down_pct': 0.0,
        'fwd_10_max_up_atr': 0.0, 'fwd_10_max_down_atr': 0.0,
        'fwd_10_close_pct': 0.0, 'fwd_10_direction': 'flat',
        'fwd_10_max_range_atr': 0.0, 'fwd_10_proper_move': False,
        'fwd_20_max_up_pct': 0.0, 'fwd_20_max_down_pct': 0.0,
        'fwd_20_max_up_atr': 0.0, 'fwd_20_max_down_atr': 0.0,
        'fwd_20_close_pct': 0.0, 'fwd_20_direction': 'flat',
        'fwd_20_max_range_atr': 0.0, 'fwd_20_proper_move': False,
    }, index=range(n))
    return df


# --- Debug Sections ---

def debug_01_mfe_mae():
    """Section 1: MFE/MAE assignment validation."""
    print("[Debug 1] MFE/MAE Assignment -- Manual Verification")
    df = make_base_df(5)
    df['fwd_10_max_up_atr'] = [4.0, 1.0, 5.0, 1.0, 3.0]
    df['fwd_10_max_down_atr'] = [1.0, 3.0, 4.0, 0.5, 1.0]
    df['fwd_10_max_up_pct'] = [8.0, 2.0, 10.0, 2.0, 6.0]
    df['fwd_10_max_down_pct'] = [-2.0, -6.0, -8.0, -1.0, -2.0]

    mm_long = _assign_mfe_mae(df, 'long', 10)
    check("long mfe[0]=4.0", approx(mm_long.iloc[0]['mfe_atr'], 4.0))
    check("long mae[0]=1.0", approx(mm_long.iloc[0]['mae_atr'], 1.0))
    check("long mfe[1]=1.0", approx(mm_long.iloc[1]['mfe_atr'], 1.0))
    check("long mae[1]=3.0", approx(mm_long.iloc[1]['mae_atr'], 3.0))

    mm_short = _assign_mfe_mae(df, 'short', 10)
    check("short mfe[0]=1.0 (down_atr)", approx(mm_short.iloc[0]['mfe_atr'], 1.0))
    check("short mae[0]=4.0 (up_atr)", approx(mm_short.iloc[0]['mae_atr'], 4.0))
    check("short mfe[1]=3.0", approx(mm_short.iloc[1]['mfe_atr'], 3.0))
    check("short mae[1]=1.0", approx(mm_short.iloc[1]['mae_atr'], 1.0))


def debug_02_pnl_calculation():
    """Section 2: PnL calculation with hand-computed values."""
    print("[Debug 2] PnL Calculation -- Hand-Computed")
    # 5 bars, single combo: lev=20, sz=1.0, tgt=3, sl=2
    # close=100, atr=2.0, notional=1.0*250*20=5000
    df = make_base_df(5)
    df['fwd_10_max_up_atr'] = [4.0, 1.0, 5.0, 1.0, 3.0]
    df['fwd_10_max_down_atr'] = [1.0, 3.0, 4.0, 0.5, 1.0]
    df['fwd_10_close_pct'] = [1.0, -1.0, 2.0, -1.0, 1.0]

    mm = _assign_mfe_mae(df, 'long', 10)
    pnl = _vectorized_pnl(
        mm['mfe_atr'], mm['mae_atr'],
        df['fwd_10_close_pct'], df['fwd_atr'], df['close'],
        'long',
        np.array([3.0]), np.array([2.0]),
        np.array([20.0]), np.array([1.0]), 250.0,
    )
    pnl_col = pnl[:, 0]

    # Bar 0: mfe=4>=3, mae=1<2 -> WIN: +(3*2/100)*5000 = +300
    check("bar0 WIN pnl=300", approx(pnl_col[0], 300.0), f"got {pnl_col[0]}")
    # Bar 1: mfe=1<3, mae=3>=2 -> LOSS: -(2*2/100)*5000 = -200
    check("bar1 LOSS pnl=-200", approx(pnl_col[1], -200.0), f"got {pnl_col[1]}")
    # Bar 2: mfe=5>=3, mae=4>=2 -> AMBIGUOUS: 1.0*2.0/100*5000 = +100
    check("bar2 AMBIG pnl=100", approx(pnl_col[2], 100.0), f"got {pnl_col[2]}")
    # Bar 3: mfe=1<3, mae=0.5<2 -> TIMEOUT: 1.0*(-1.0)/100*5000 = -50
    check("bar3 TIMEOUT pnl=-50", approx(pnl_col[3], -50.0), f"got {pnl_col[3]}")
    # Bar 4: mfe=3>=3, mae=1<2 -> WIN: +300
    check("bar4 WIN pnl=300", approx(pnl_col[4], 300.0), f"got {pnl_col[4]}")

    # Aggregates: [300, -200, 100, -50, 300]
    check("total_pnl=450", approx(pnl_col.sum(), 450.0))
    check("expectancy=90", approx(pnl_col.mean(), 90.0))

    # Max consecutive loss: [W, L, W, L, W] -> max=1
    mcl = _max_consecutive_loss(pnl_col)
    check("max_consec_loss=1", mcl == 1, f"got {mcl}")

    # Max drawdown: cumsum=[300,100,200,150,450], running_max=[300,300,300,300,450]
    # dd=[0,200,100,150,0] -> max_dd=200
    cs = np.cumsum(pnl_col)
    rm = np.maximum.accumulate(cs)
    dd = rm - cs
    check("max_dd=200", approx(dd.max(), 200.0), f"got {dd.max()}")


def debug_03_grid_search():
    """Section 3: Small grid search validation."""
    print("[Debug 3] Grid Search -- Small Grid")
    n = 50
    df = make_base_df(n)
    df['bbwp_state'] = 'BLUE'
    df['fwd_10_max_up_atr'] = 4.0
    df['fwd_10_max_down_atr'] = 1.0
    df['fwd_10_close_pct'] = 1.0

    cfg = SimulatorConfig(
        leverage_grid=[10, 20], size_grid=[0.5, 1.0],
        target_atr_grid=[2, 4], sl_atr_grid=[1.5],
        windows=[10], directions=['long'],
    )
    lsg = _lsg_grid_search(df, cfg)
    n_combos = 2 * 2 * 2 * 1  # 8
    check("combo count=8", len(lsg) == n_combos, f"got {len(lsg)}")

    # Best combo: highest expectancy should be lev=20, sz=1.0, tgt=2
    # because mfe=4>=2 always wins, lower target = more certain wins
    # tgt=2: all WIN, pnl = +(2*2/100)*(1.0*250*20) = +200/bar
    # tgt=4: all WIN, pnl = +(4*2/100)*(1.0*250*20) = +400/bar
    # Actually tgt=4 gives more PnL per win! And mfe=4>=4 still wins.
    best = lsg.loc[lsg['expectancy_usd'].idxmax()]
    check("best tgt=4", approx(best['target_atr'], 4.0),
          f"got tgt={best['target_atr']}")
    check("best lev=20", approx(best['leverage'], 20.0),
          f"got lev={best['leverage']}")
    check("best sz=1.0", approx(best['size_frac'], 1.0),
          f"got sz={best['size_frac']}")


def debug_04_group_stats():
    """Section 4: Group stats with known distributions."""
    print("[Debug 4] Group Stats -- Known Distributions")
    n = 40
    df = make_base_df(n)
    # 20 bars BLUE with higher MFE, 20 bars RED with lower MFE
    df.loc[:19, 'bbwp_state'] = 'BLUE'
    df.loc[20:, 'bbwp_state'] = 'RED'
    df.loc[:19, 'fwd_10_max_up_atr'] = 5.0
    df.loc[20:, 'fwd_10_max_up_atr'] = 1.0
    df.loc[:19, 'fwd_10_max_down_atr'] = 1.0
    df.loc[20:, 'fwd_10_max_down_atr'] = 3.0
    df['fwd_10_close_pct'] = np.random.randn(n) * 2.0

    cfg = SimulatorConfig(windows=[10], directions=['long'])
    _add_derived_columns(df, cfg)
    gs = _compute_group_stats(df, 'bbwp_state', [10], ['long'])
    blue = gs[gs['group_value'] == 'BLUE'].iloc[0]
    red = gs[gs['group_value'] == 'RED'].iloc[0]

    check("blue mean_mfe=5.0", approx(blue['mean_mfe_atr'], 5.0))
    check("red mean_mfe=1.0", approx(red['mean_mfe_atr'], 1.0))
    check("blue mean_mae=1.0", approx(blue['mean_mae_atr'], 1.0))
    check("red mean_mae=3.0", approx(red['mean_mae_atr'], 3.0))
    check("blue mfe_mae_ratio=5.0", approx(blue['mfe_mae_ratio'], 5.0))
    check("red mfe_mae_ratio=0.333",
          approx(red['mfe_mae_ratio'], 1.0 / 3.0, tol=0.01))
    check("blue n_bars=20", blue['n_bars'] == 20)
    check("red n_bars=20", red['n_bars'] == 20)


def debug_05_scaling():
    """Section 5: Scaling simulation with known state sequence."""
    print("[Debug 5] Scaling Simulation -- Known Sequence")
    # 30 bars: NORMAL(10) -> BLUE(5) -> NORMAL(15)
    n = 30
    df = make_base_df(n)
    df.loc[:9, 'bbwp_state'] = 'NORMAL'
    df.loc[10:14, 'bbwp_state'] = 'BLUE'
    df.loc[15:, 'bbwp_state'] = 'NORMAL'
    df['fwd_10_max_up_atr'] = 3.0
    df['fwd_10_max_down_atr'] = 1.0
    df['fwd_10_close_pct'] = 1.0

    cfg = SimulatorConfig(
        windows=[10], directions=['long'], min_sample_size=1,
        leverage_grid=[10], size_grid=[1.0],
        target_atr_grid=[2], sl_atr_grid=[1.5],
    )
    lsg = _lsg_grid_search(df, cfg)
    top = _extract_top_combos(lsg, cfg, n_top=3)

    scenario = [('NORMAL', 0.50, 'BLUE', 0.50, 12)]
    sc = _scaling_simulation(df, scenario, cfg, top)

    check("n_entry_bars > 0", sc.iloc[0]['n_entry_bars'] > 0)
    # Bars 0-9 are NORMAL. Looking forward 12 bars:
    # Bars 0-7 can see BLUE at bar 10 (within 12 bars) -> triggered
    # Bar 8 can see BLUE at bar 10 (8+1=9..8+12=20, bar 10 in range) -> triggered
    # Bar 9 can see BLUE at bar 10 (9+1=10..9+12=21, bar 10 in range) -> triggered
    # Bars 15-24 are NORMAL. Looking forward 12 bars:
    # No BLUE in bars 15-29 -> not triggered
    n_trig = sc.iloc[0]['n_triggered']
    check("some triggers found", n_trig > 0, f"got {n_trig}")
    check("triggered_pct 0-1",
          0 <= sc.iloc[0]['triggered_pct'] <= 1)


def debug_06_max_consec_loss():
    """Section 6: Max consecutive loss edge cases."""
    print("[Debug 6] Max Consecutive Loss -- Edge Cases")
    # [W, L, L, L, W, L, L] -> max=3
    pnl1 = np.array([100, -50, -30, -20, 200, -10, -40])
    check("mcl_1=3", _max_consecutive_loss(pnl1) == 3)

    # All wins -> 0
    pnl2 = np.array([100, 200, 300])
    check("mcl_all_wins=0", _max_consecutive_loss(pnl2) == 0)

    # All losses -> n
    pnl3 = np.array([-10, -20, -30, -40])
    check("mcl_all_losses=4", _max_consecutive_loss(pnl3) == 4)

    # Single bar
    pnl4 = np.array([-10])
    check("mcl_single_loss=1", _max_consecutive_loss(pnl4) == 1)

    # Empty
    pnl5 = np.array([])
    check("mcl_empty=0", _max_consecutive_loss(pnl5) == 0)

    # 2D version
    pnl_2d = np.array([
        [100, -50],
        [-50, -30],
        [-30, -20],
        [200, -10],
        [-10, 100],
    ])
    mcl_2d = _max_consecutive_loss_2d(pnl_2d)
    # Col 0: [W,L,L,W,L] -> max=2
    # Col 1: [L,L,L,L,W] -> max=4
    check("2d col0 mcl=2", mcl_2d[0] == 2, f"got {mcl_2d[0]}")
    check("2d col1 mcl=4", mcl_2d[1] == 4, f"got {mcl_2d[1]}")


def debug_07_cross_validate_real():
    """Section 7: Cross-validate on RIVERUSDT 5m (if available)."""
    print("[Debug 7] Cross-Validate Real Data (L1+L2+L3+L4)")
    cache = ROOT / "data" / "cache"
    parquet = cache / "RIVERUSDT_5m.parquet"
    if not parquet.exists():
        print("  SKIP  RIVERUSDT parquet not found")
        return

    df_raw = pd.read_parquet(parquet)
    print(f"  Loaded {len(df_raw)} bars")

    sys.path.insert(0, str(ROOT))
    from signals.bbwp import calculate_bbwp
    from signals.bbw_sequence import track_bbw_sequence
    from research.bbw_forward_returns import tag_forward_returns

    df1 = calculate_bbwp(df_raw)
    df2 = track_bbw_sequence(df1)
    df3 = tag_forward_returns(df2, windows=[10])

    cfg = SimulatorConfig(
        leverage_grid=[10, 20], size_grid=[0.5, 1.0],
        target_atr_grid=[2, 4], sl_atr_grid=[1.5, 2.0],
        windows=[10], directions=['long'],
        min_sample_size=30,
    )
    result = run_simulator(df3, cfg)

    check("n_bars_valid > 0", result.summary['n_bars_valid'] > 0)
    check("n_states >= 5", result.summary['n_states'] >= 5)
    check("lsg has rows", len(result.lsg_results) > 0)
    check("lsg_top has rows", len(result.lsg_top) > 0)

    if not result.lsg_top.empty:
        print()
        print("  Top combo per state:")
        for state in result.lsg_top['bbwp_state'].unique():
            row = result.lsg_top[
                result.lsg_top['bbwp_state'] == state
            ].iloc[0]
            print(f"    {state}: lev={row['leverage']:.0f} "
                  f"tgt={row['target_atr']:.0f} sl={row['sl_atr']:.1f} "
                  f"exp=${row['expectancy_usd']:.2f} "
                  f"wr={row['win_rate']:.1%}")

    check("runtime < 60s", result.summary['runtime_sec'] < 60,
          f"took {result.summary['runtime_sec']}s")


# --- Main ---

def main():
    """Run all debug sections."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"Simulator Layer 4 Debug & Math Validator -- {ts}")
    print("=" * 70)
    print()

    debug_01_mfe_mae()
    print()
    debug_02_pnl_calculation()
    print()
    debug_03_grid_search()
    print()
    debug_04_group_stats()
    print()
    debug_05_scaling()
    print()
    debug_06_max_consec_loss()
    print()
    debug_07_cross_validate_real()

    print()
    print("=" * 70)
    print(f"DEBUG RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 70)
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))


if __name__ == "__main__":
    main()

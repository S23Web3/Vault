# Layer 4 Test Results -- 2026-02-14 16:24 UTC


## Layer 4 Tests
```
======================================================================
Simulator Layer 4 Tests -- 2026-02-14 16:24 UTC
======================================================================

[Test 1] Input Validation
  PASS  valid df passes
  PASS  missing cols raises
  PASS  bbwp_state in error
  PASS  fwd_atr in error

[Test 2] MFE/MAE Long
  PASS  mfe = max_up_atr
  PASS  mae = max_down_atr
  PASS  mfe_pct = max_up_pct
  PASS  mae_pct = abs(max_down_pct)

[Test 3] MFE/MAE Short
  PASS  mfe = max_down_atr
  PASS  mae = max_up_atr

[Test 4] Group A State Stats
  PASS  rows = n_states
  PASS  has group_value
  PASS  has mean_mfe_atr
  PASS  has edge_score
  PASS  has directional_bias
  PASS  n_bars sum = total

[Test 5] Group F Duration Bins
  PASS  duration_bin exists
  PASS  no NaN in duration_bin

[Test 6] Group G MA+Spectrum Combo
  PASS  ma_spectrum_combo exists
  PASS  combo has underscore
  PASS  no None in combo string

[Test 7] All 7 Groups
  PASS  A_state returns DataFrame
  PASS  B_spectrum returns DataFrame
  PASS  C_direction returns DataFrame
  PASS  D_pattern returns DataFrame
  PASS  E_skip returns DataFrame
  PASS  F_duration returns DataFrame
  PASS  G_ma_spectrum returns DataFrame

[Test 8] Min Sample Size Filter
  PASS  all filtered out (n<1000)

[Test 9] LSG Grid Dimensions
  PASS  grid row count

[Test 10] Known PnL Values
  PASS  win_rate = 1.0
  PASS  avg_win = 300
  PASS  total_pnl = 3000
  PASS  win_rate = 0.0
  PASS  avg_loss = -50

[Test 11] Win Rate Bounds
  PASS  win_rate >= 0
  PASS  win_rate <= 1

[Test 12] LSG Top Extraction
  PASS  max 3 per group

[Test 13] Scaling Triggered Pct
  PASS  triggered_pct >= 0
  PASS  triggered_pct <= 1

[Test 14] Scaling Verdict Logic
  PASS  verdict in valid set (MARGINAL)
  PASS  verdict in valid set (MARGINAL)
  PASS  verdict in valid set (MARGINAL)
  PASS  verdict in valid set (MARGINAL)
  PASS  verdict in valid set (MARGINAL)
  PASS  verdict in valid set (MARGINAL)

[Test 15] SimulatorResult Structure
  PASS  type is SimulatorResult
  PASS  group_stats is dict
  PASS  7 groups
  PASS  lsg_results is DataFrame
  PASS  lsg_top is DataFrame
  PASS  scaling_results is DataFrame
  PASS  summary is dict
  PASS  summary has runtime_sec
  PASS  summary has n_bars_valid

======================================================================
RESULTS: 55 PASS / 0 FAIL
======================================================================
```


## Layer 4 Debug Validator
```
======================================================================
Simulator Layer 4 Debug & Math Validator -- 2026-02-14 16:24 UTC
======================================================================

[Debug 1] MFE/MAE Assignment -- Manual Verification
  PASS  long mfe[0]=4.0
  PASS  long mae[0]=1.0
  PASS  long mfe[1]=1.0
  PASS  long mae[1]=3.0
  PASS  short mfe[0]=1.0 (down_atr)
  PASS  short mae[0]=4.0 (up_atr)
  PASS  short mfe[1]=3.0
  PASS  short mae[1]=1.0

[Debug 2] PnL Calculation -- Hand-Computed
  PASS  bar0 WIN pnl=300
  PASS  bar1 LOSS pnl=-200
  PASS  bar2 AMBIG pnl=100
  PASS  bar3 TIMEOUT pnl=-50
  PASS  bar4 WIN pnl=300
  PASS  total_pnl=450
  PASS  expectancy=90
  PASS  max_consec_loss=1
  PASS  max_dd=200

[Debug 3] Grid Search -- Small Grid
  PASS  combo count=8
  PASS  best tgt=4
  PASS  best lev=20
  PASS  best sz=1.0

[Debug 4] Group Stats -- Known Distributions
  PASS  blue mean_mfe=5.0
  PASS  red mean_mfe=1.0
  PASS  blue mean_mae=1.0
  PASS  red mean_mae=3.0
  PASS  blue mfe_mae_ratio=5.0
  PASS  red mfe_mae_ratio=0.333
  PASS  blue n_bars=20
  PASS  red n_bars=20

[Debug 5] Scaling Simulation -- Known Sequence
  PASS  n_entry_bars > 0
  PASS  some triggers found
  PASS  triggered_pct 0-1

[Debug 6] Max Consecutive Loss -- Edge Cases
  PASS  mcl_1=3
  PASS  mcl_all_wins=0
  PASS  mcl_all_losses=4
  PASS  mcl_single_loss=1
  PASS  mcl_empty=0
  PASS  2d col0 mcl=2
  PASS  2d col1 mcl=4

[Debug 7] Cross-Validate Real Data (L1+L2+L3+L4)
  Loaded 32762 bars
  PASS  n_bars_valid > 0
  PASS  n_states >= 5
  PASS  lsg has rows
  PASS  lsg_top has rows

  Top combo per state:
    RED_DOUBLE: lev=20 tgt=4 sl=1.5 exp=$18.90 wr=44.4%
    MA_CROSS_DOWN: lev=20 tgt=4 sl=1.5 exp=$4.27 wr=43.3%
    MA_CROSS_UP: lev=20 tgt=4 sl=1.5 exp=$4.25 wr=43.6%
    NORMAL: lev=20 tgt=2 sl=1.5 exp=$3.86 wr=46.7%
    BLUE_DOUBLE: lev=20 tgt=2 sl=2.0 exp=$3.72 wr=49.6%
    BLUE: lev=20 tgt=4 sl=2.0 exp=$1.77 wr=45.5%
    RED: lev=10 tgt=2 sl=1.5 exp=$-0.21 wr=45.1%
  PASS  runtime < 60s

======================================================================
DEBUG RESULTS: 44 PASS / 0 FAIL
======================================================================
```


## Layer 4 Sanity Check
```
======================================================================
Simulator Layer 4 Sanity Check -- 2026-02-14 16:24 UTC
======================================================================
  Input: 32762 bars (5m)

--- Runtime Breakdown ---
  L1 (BBWP):     0.33s
  L2 (Sequence):  0.03s
  L3 (Forward):   0.01s
  L4 (Simulator): 2.06s
  Total:          2.47s

--- Summary ---
  n_bars_total: 32762
  n_bars_valid: 32738
  n_states: 7
  n_lsg_combos: 112
  n_scaling_scenarios: 6
  runtime_sec: 2.06

--- Group Stats Overview ---
  A_state: 7 categories, best=RED_DOUBLE (edge=0.070)
  B_spectrum: 4 categories, best=green (edge=0.062)
  C_direction: 3 categories, best=expanding (edge=0.051)
  D_pattern: 36 categories, best=GRB (edge=3.255)
  E_skip: 2 categories, best=True (edge=0.099)
  F_duration: 4 categories, best=21-50 (edge=0.388)
  G_ma_spectrum: 10 categories, best=cross_down_green (edge=0.142)

--- LSG Top Combos ---
  RED_DOUBLE      lev=20 sz=1.00 tgt=4 sl=1.5 exp=$   18.90 wr=44.4% pf=1.29
  RED_DOUBLE      lev=20 sz=1.00 tgt=4 sl=2.0 exp=$   17.25 wr=47.8% pf=1.25
  RED_DOUBLE      lev=20 sz=1.00 tgt=2 sl=1.5 exp=$   16.06 wr=49.2% pf=1.27
  MA_CROSS_DOWN   lev=20 sz=1.00 tgt=4 sl=1.5 exp=$    4.27 wr=43.3% pf=1.09
  MA_CROSS_UP     lev=20 sz=1.00 tgt=4 sl=1.5 exp=$    4.25 wr=43.6% pf=1.08
  MA_CROSS_DOWN   lev=20 sz=1.00 tgt=4 sl=2.0 exp=$    3.93 wr=46.4% pf=1.08
  NORMAL          lev=20 sz=1.00 tgt=2 sl=1.5 exp=$    3.86 wr=46.7% pf=1.07
  BLUE_DOUBLE     lev=20 sz=1.00 tgt=2 sl=2.0 exp=$    3.72 wr=49.6% pf=1.08
  MA_CROSS_UP     lev=20 sz=1.00 tgt=2 sl=1.5 exp=$    3.43 wr=46.8% pf=1.06
  BLUE_DOUBLE     lev=20 sz=1.00 tgt=2 sl=1.5 exp=$    3.40 wr=46.1% pf=1.08

--- Scaling Verdicts ---
  NORMAL          -> BLUE         wait=10 trig=42.0% verdict=USE
  NORMAL          -> BLUE         wait=20 trig=64.2% verdict=USE
  NORMAL          -> BLUE_DOUBLE  wait=20 trig=45.6% verdict=USE
  BLUE            -> BLUE_DOUBLE  wait=10 trig=55.8% verdict=MARGINAL
  MA_CROSS_UP     -> BLUE         wait=10 trig=38.5% verdict=USE
  NORMAL          -> BLUE         wait=15 trig=54.7% verdict=USE

  Saved: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\results\bbw_simulator_sanity.csv

======================================================================
SANITY CHECK COMPLETE
======================================================================
```

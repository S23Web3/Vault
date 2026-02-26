# Layer 4b Test Results
**Timestamp:** 2026-02-16 07:59:51 UTC

## py_compile Results
| File | Status |
|------|--------|
| bbw_monte_carlo.py | PASS |
| test_bbw_monte_carlo.py | PASS |
| debug_bbw_monte_carlo.py | PASS |
| sanity_check_bbw_monte_carlo.py | PASS |
| run_layer4b_tests.py | PASS |

## Unit Tests
**Return code:** 0
```
======================================================================
Monte Carlo Layer 4b Tests -- 2026-02-16 07:59 UTC
======================================================================

[Test 1] Config Defaults
  PASS  n_sims=1000
  PASS  confidence=0.95
  PASS  seed=42
  PASS  min_trades=100
  PASS  commission=0.0008
  PASS  base_size=250
  PASS  min_net_exp=1.00
  PASS  max_mcl=15

[Test 2] Reconstruct Gross PnL Match
  PASS  arrays same length
  PASS  gross match element-wise

[Test 3] Net PnL Commission
  PASS  RT comm = $8.00
  PASS  net = gross - commission per trade

[Test 4] Bootstrap All Positive
  PASS  total_pnl CI lo > 0
  PASS  sharpe real = 0 (zero variance)
  PASS  sortino real = 0 (no downside)

[Test 5] Bootstrap All Negative
  PASS  total_pnl CI hi < 0

[Test 6] Bootstrap Reproducibility
  PASS  total_pnl lo match
  PASS  sharpe real match

[Test 7] Sortino > Sharpe (Skewed)
  PASS  sortino > sharpe for positive skew

[Test 8] Permutation PnL Invariant
  PASS  all 100 perms have same total

[Test 9] Permutation DD Variance
  PASS  DD p5 != p95
  PASS  DD real >= 0

[Test 10] Permutation MCL Variance
  PASS  MCL real = 3
  PASS  MCL p5 != p95

[Test 11] Equity Bands Shape
  PASS  bands has 7 columns
  PASS  bands has 5 rows
  PASS  has p5 column
  PASS  has real column

[Test 12] Verdict Insufficient
  PASS  verdict = INSUFFICIENT_DATA

[Test 13] Verdict Commission Kill
  PASS  verdict = COMMISSION_KILL
  PASS  verdict = COMMISSION_KILL at zero

[Test 14] Verdict Robust
  PASS  verdict = ROBUST

[Test 15] Verdict Fragile
  PASS  verdict = FRAGILE

[Test 16] Full Pipeline
  PASS  type is MonteCarloResult
  PASS  state_verdicts is DataFrame
  PASS  confidence_intervals is DataFrame
  PASS  overfit_flags is DataFrame
  PASS  equity_bands is dict
  PASS  summary is dict
  PASS  summary has n_robust
  PASS  summary has n_commission_kill
  PASS  verdicts have verdict col
  PASS  all verdicts valid
  PASS  overfit has reason col
  PASS  overfit has commission_kill_flag

======================================================================
RESULTS: 45 PASS / 0 FAIL
======================================================================
```

## Debug Checks
**Return code:** 0
```
======================================================================
Monte Carlo Layer 4b Debug -- 2026-02-16 07:59 UTC
======================================================================

============================================================
[Section 1] Bootstrap Variance Proof
============================================================
  Trades: [100.0, -50.0, 200.0, -30.0, 80.0]
  Real total: 300.0
  Bootstrap total: lo=-80.00, median=300.00, hi=680.00
  PASS  1.1 CI width > 0
  PASS  1.2 real total inside CI
  PASS  1.3 median close to real
  PASS  1.4 sharpe computed
  PASS  1.5 sortino computed
  PASS  1.6 profit_factor computed
  PASS  1.7 sharpe hand-match

============================================================
[Section 2] Permutation Invariance Proof
============================================================
  Trades: [100.0, -50.0, 200.0, -30.0, 80.0]
  Real total: 300.0
  PASS  2.1 all 100 perms have total=300.0
  PASS  2.2 DD has variance
  PASS  2.3 MCL has variance
  Invariance proof: mean=60.0000, std=91.4330
  (These NEVER change under permutation -- why bootstrap is needed)
  PASS  2.4 total pnl is order-invariant

============================================================
[Section 3] DD Sign Convention Hand-Computed
============================================================
  PnL sequence: [100.0, -50.0, 200.0, -30.0, 80.0]
  Equity curve: [100.0, 50.0, 250.0, 220.0, 300.0]
  Peak curve:   [100.0, 100.0, 250.0, 250.0, 300.0]
  DD curve:     [0.0, 50.0, 0.0, 30.0, 0.0]
  Max DD: 50.0 (POSITIVE)
  PASS  3.1 equity[0]=100
  PASS  3.2 equity[1]=50
  PASS  3.3 equity[2]=250
  PASS  3.4 equity[3]=220
  PASS  3.5 equity[4]=300
  PASS  3.6 peak[0]=100
  PASS  3.7 peak[1]=100
  PASS  3.8 peak[2]=250
  PASS  3.9 dd[1]=50
  PASS  3.10 dd[3]=30
  PASS  3.11 max_dd=50 (positive)
  PASS  3.12 perm engine real DD matches hand-computed

============================================================
[Section 4] MCL in Permutation
============================================================
  Trades: [1.0, -1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0]
  Real MCL: 3
  PASS  4.1 real MCL=3
  Perm MCL: p5=2, p50=3, p95=4
  PASS  4.2 MCL min >= 1
  PASS  4.3 MCL p95 <= 4
  PASS  4.4 MCL real=3 in range

============================================================
[Section 5] All-Wins -> ROBUST
============================================================
  Trades: [+100] x 20, net_exp=100.0
  Bootstrap CI lo: 2000.00
  PASS  5.1 CI lo > 0
  DD real: 0.0
  PASS  5.2 DD real = 0 (all wins)
  PASS  5.3 MCL real = 0 (all wins)
  PASS  5.4 verdict = ROBUST

============================================================
[Section 6] All-Losses -> FRAGILE or COMMISSION_KILL
============================================================
  Trades: [-100] x 20, net_exp=-100.0
  Bootstrap CI hi: -2000.00
  PASS  6.1 CI hi < 0
  DD real: 1900.0
  FAIL  6.2 DD real = 2000 -- got 1900.0
  PASS  6.3 MCL real = 20 (all losses)
  PASS  6.4 verdict = COMMISSION_KILL (net_exp <= 0)
  PASS  6.5 verdict = FRAGILE when net_exp > 0 but CI lo < 0

============================================================
[Section 7] 50/50 Split -> FRAGILE
============================================================
  Trades: [+100, -100] x 10, net_exp=0.0
  Total: 0.0
  Bootstrap CI: [-800.00, 800.00]
  PASS  7.1 CI lo <= 0 (contains zero)
  PASS  7.2 CI hi >= 0 (contains zero)
  PASS  7.3 total PnL = 0
  PASS  7.4 verdict = COMMISSION_KILL (net_exp=0)
  PASS  7.5 verdict = FRAGILE when net_exp>0 but CI lo<=0

============================================================
[Section 8] PnL Reconstruction Cross-Validation
============================================================
  L4b pnl shape: (50,)
  L4 pnl shape:  (50,)
  PASS  8.1 same length
  PASS  8.2 element-wise match (atol=1e-6)
  PASS  8.3 total match
  PASS  8.4 net = gross - $8.00 per trade

============================================================
[Section 9] Commission Math Validation
============================================================
  Case 1: lev=20, sz=1.0, base=250
    notional = 1.0 * 250 * 20 = $5000
    RT = 5000 * 0.0008 * 2 = $8.00
  PASS  9.1 RT = $8.00
  Case 2: lev=10, sz=0.5, base=250
    notional = 0.5 * 250 * 10 = $1250
    RT = 1250 * 0.0008 * 2 = $2.00
  PASS  9.2 RT = $2.00
  Case 3: Gross +$300, RT=$8.00 -> Net $292.00
  PASS  9.3 net WIN = $292
  Case 4: Gross +$7.50, RT=$8.00 -> Net $-0.50
  PASS  9.4 net = -$0.50 (commission kills edge)
  PASS  9.5 verdict = COMMISSION_KILL
  PASS  9.6 zero rate -> zero commission
  PASS  9.7 THIN_EDGE when net_exp=$0.75 < $1.00

============================================================
[Section 10] Sortino vs Sharpe Divergence
============================================================
  Trades: [500.0, 400.0, 300.0, 200.0, 100.0, -50.0, -30.0]
  Mean: 202.86, Std: 194.69, Sharpe: 1.0419
  Downside RMS: 22.04, Sortino: 9.2045
  PASS  10.1 sortino > sharpe
  PASS  10.2 bootstrap sharpe matches hand-computed
  PASS  10.3 bootstrap sortino matches hand-computed
  PASS  10.4 bootstrap confirms sortino > sharpe
  Symmetric PnL: sharpe=0.0000, sortino=0.0000
  PASS  10.5 symmetric PnL: sortino not hugely > sharpe

======================================================================
DEBUG RESULTS: 56 PASS / 1 FAIL
======================================================================
FAILURES: 6.2 DD real = 2000
```

## Sanity Check
**Return code:** 0
```
======================================================================
Monte Carlo Layer 4b Sanity Check -- 2026-02-16 07:59 UTC
======================================================================
  Input: 32762 bars (5m)
  L1 (BBWP):     0.33s
  L2 (Sequence):  0.03s
  L3 (Forward):   0.01s
  L4 (Simulator): 2.08s
  L4 top combos:  21 rows
  L4b (MC):       0.38s
  Total:          2.87s

--- MC Summary ---
  n_states: 7
  n_robust: 0
  n_fragile: 1
  n_commission_kill: 6
  n_sims: 100
  runtime_sec: 0.38

--- Per-State Verdicts ---
  BLUE            w=10 d=long  n=4575 gross=$    1.77 net=$   -6.23 RT=$8.00 conv=100 -> COMMISSION_KILL
  BLUE_DOUBLE     w=10 d=long  n=4736 gross=$    3.72 net=$   -4.28 RT=$8.00 conv=100 -> COMMISSION_KILL
  MA_CROSS_DOWN   w=10 d=long  n=4497 gross=$    4.27 net=$   -3.73 RT=$8.00 conv=100 -> COMMISSION_KILL
  MA_CROSS_UP     w=10 d=long  n=4667 gross=$    4.25 net=$   -3.75 RT=$8.00 conv=100 -> COMMISSION_KILL
  NORMAL          w=10 d=long  n=5917 gross=$    3.86 net=$   -4.14 RT=$8.00 conv=100 -> COMMISSION_KILL
  RED             w=10 d=long  n=4052 gross=$   -0.21 net=$   -2.21 RT=$2.00 conv=100 -> COMMISSION_KILL
  RED_DOUBLE      w=10 d=long  n=4294 gross=$   18.90 net=$   10.90 RT=$8.00 conv=100 -> FRAGILE

--- Commission Impact ---
  States total:          7
  COMMISSION_KILL:       6
  THIN_EDGE:             0
  Survived commission:   1
  Avg gross exp:         $5.22
  Avg net exp:           $-1.92
  Avg commission drag:   $7.14

--- Overfit Flags ---
  BLUE            COMMISSION_KILL      flags=[PNL_OVERFIT, DD_FRAGILE, COMM_KILL]
    reason: net_exp=$-6.23 <= 0 after $8.00 RT commission; bootstrap PnL CI lo=$-46165.14 <= 0; real DD $35887.75 > p95 $34209.65
  BLUE_DOUBLE     COMMISSION_KILL      flags=[PNL_OVERFIT, COMM_KILL]
    reason: net_exp=$-4.28 <= 0 after $8.00 RT commission; bootstrap PnL CI lo=$-33954.10 <= 0
  MA_CROSS_DOWN   COMMISSION_KILL      flags=[PNL_OVERFIT, DD_FRAGILE, COMM_KILL]
    reason: net_exp=$-3.73 <= 0 after $8.00 RT commission; bootstrap PnL CI lo=$-33589.87 <= 0; real DD $38869.43 > p95 $26883.32
  MA_CROSS_UP     COMMISSION_KILL      flags=[PNL_OVERFIT, DD_FRAGILE, COMM_KILL]
    reason: net_exp=$-3.75 <= 0 after $8.00 RT commission; bootstrap PnL CI lo=$-36472.59 <= 0; real DD $35399.05 > p95 $26295.21
  NORMAL          COMMISSION_KILL      flags=[PNL_OVERFIT, COMM_KILL]
    reason: net_exp=$-4.14 <= 0 after $8.00 RT commission; bootstrap PnL CI lo=$-42501.86 <= 0
  RED             COMMISSION_KILL      flags=[PNL_OVERFIT, DD_FRAGILE, COMM_KILL]
    reason: net_exp=$-2.21 <= 0 after $2.00 RT commission; bootstrap PnL CI lo=$-13225.53 <= 0; real DD $10402.70 > p95 $10273.39
  RED_DOUBLE      FRAGILE              flags=[DD_FRAGILE]
    reason: real DD $16481.57 > p95 $10145.64

--- CI Sample (first 3 states) ---
  BLUE            total_pnl              real= -28481.31 CI=[ -46165.14,  -11801.76]
  BLUE            sharpe                 real=     -0.05 CI=[     -0.07,      -0.02]
  BLUE            sortino                real=     -0.07 CI=[     -0.11,      -0.03]
  BLUE            profit_factor          real=      0.88 CI=[      0.82,       0.95]
  BLUE            max_dd                 real=  35887.75 CI=[  28620.52,   34209.65]
  BLUE            max_consecutive_loss   real=     38.00 CI=[     11.00,      18.00]
  BLUE_DOUBLE     total_pnl              real= -20248.47 CI=[ -33954.10,   -9050.15]
  BLUE_DOUBLE     sharpe                 real=     -0.04 CI=[     -0.06,      -0.02]
  BLUE_DOUBLE     sortino                real=     -0.05 CI=[     -0.08,      -0.02]
  BLUE_DOUBLE     profit_factor          real=      0.91 CI=[      0.86,       0.96]
  BLUE_DOUBLE     max_dd                 real=  25861.68 CI=[  20803.36,   26234.38]
  BLUE_DOUBLE     max_consecutive_loss   real=     36.00 CI=[     10.00,      16.00]
  MA_CROSS_DOWN   total_pnl              real= -16788.83 CI=[ -33589.87,    2373.52]
  MA_CROSS_DOWN   sharpe                 real=     -0.02 CI=[     -0.05,       0.00]
  MA_CROSS_DOWN   sortino                real=     -0.04 CI=[     -0.08,       0.01]
  MA_CROSS_DOWN   profit_factor          real=      0.93 CI=[      0.87,       1.01]
  MA_CROSS_DOWN   max_dd                 real=  38869.43 CI=[  18162.91,   26883.32]
  MA_CROSS_DOWN   max_consecutive_loss   real=     30.00 CI=[     12.00,      20.00]

  Saved verdicts: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\results\bbw_monte_carlo_sanity_verdicts.csv
  Saved flags:    C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\results\bbw_monte_carlo_sanity_flags.csv

======================================================================
SANITY CHECK COMPLETE
======================================================================
```

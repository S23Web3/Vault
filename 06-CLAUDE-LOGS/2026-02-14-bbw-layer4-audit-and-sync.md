# BBW Layer 4 Audit + Layer 5 Prep — 2026-02-14
**Session:** claude.ai desktop
**Outcome:** Layer 4 build prompt fully audited, 22 bugs found and fixed. All layers 1-3 PASSING. Layer 4 ready for Claude Code execution.

---

## PROJECT LOCATIONS

| Item | Path |
|------|------|
| Project root | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\` |
| Architecture spec | `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\BBW-SIMULATOR-ARCHITECTURE.md` |
| L1 source | `signals\bbwp.py` — 10 output cols, 61/61 PASS |
| L2 source | `signals\bbw_sequence.py` — 9 output cols, 68/68 PASS |
| L3 source | `research\bbw_forward_returns.py` — 17 output cols, PASSING |
| L4 build prompt | `BUILDS\PROMPT-LAYER4-BUILD.md` — AUDITED, ready for Claude Code |
| L3 build prompt | `BUILDS\PROMPT-LAYER3-BUILD.md` |
| L2 build prompt | `BUILDS\PROMPT-LAYER2-BUILD.md` |
| L1 bugfix prompt | `BUILDS\PROMPT-LAYER1-BUGFIX.md` |
| Python skill | `skills\python\SKILL.md` |
| Audit log | `06-CLAUDE-LOGS\2026-02-14-bbw-layer4-audit.md` |
| Data | `data\cache\` — 399 coins, RIVERUSDT used for sanity checks |

## PIPELINE STATUS

| Layer | File | Status | Tests |
|-------|------|--------|-------|
| PRE-STEP | `research/coin_classifier.py` | NOT BUILT | — |
| Layer 1 | `signals/bbwp.py` | ✅ COMPLETE | 61/61 PASS |
| Layer 2 | `signals/bbw_sequence.py` | ✅ COMPLETE | 68/68 PASS, 148/148 debug |
| Layer 3 | `research/bbw_forward_returns.py` | ✅ COMPLETE | PASSING |
| Layer 4 | `research/bbw_simulator.py` | BUILD PROMPT READY | — |
| Layer 4b | `research/bbw_monte_carlo.py` | NOT BUILT | — |
| Layer 5 | `research/bbw_report.py` | NOT BUILT | — |
| Layer 6 | `research/bbw_ollama_review.py` | NOT BUILT | — |

## EXISTING TEST/SCRIPT FILES

```
tests\test_bbwp.py
tests\test_bbw_sequence.py
tests\test_forward_returns.py        (Layer 3)
scripts\sanity_check_bbwp.py
scripts\sanity_check_bbw_sequence.py
scripts\sanity_check_forward_returns.py
scripts\debug_bbw_sequence.py
scripts\debug_forward_returns.py
scripts\run_layer2_tests.py
scripts\run_layer3_tests.py
research\__init__.py                  (empty, exists)
```

## LAYER OUTPUT COLUMNS — COMPLETE REFERENCE

### Layer 1: 10 columns
```
bbwp_value          float (0-100)     percentile rank
bbwp_ma             float             MA of BBWP
bbwp_bbw_raw        float             raw BB width
bbwp_spectrum       str               'blue'|'green'|'yellow'|'red' (4 colors, NO orange)
bbwp_state          str               7 values: BLUE_DOUBLE|BLUE|MA_CROSS_UP|NORMAL|MA_CROSS_DOWN|RED|RED_DOUBLE
bbwp_points         int (0-2)         grade points
bbwp_is_blue_bar    bool              extreme low
bbwp_is_red_bar     bool              extreme high
bbwp_ma_cross_up    bool              crossover event (single bar)
bbwp_ma_cross_down  bool              crossunder event (single bar)
```

### Layer 2: 9 columns
```
bbw_seq_prev_color      str/None      previous bar spectrum color
bbw_seq_color_changed   bool          color transition this bar
bbw_seq_bars_in_color   int           consecutive bars at current color
bbw_seq_bars_in_state   int           consecutive bars in current state (starts at 1, never 0)
bbw_seq_direction       str/None      'expanding'|'contracting'|'flat'
bbw_seq_skip_detected   bool          color skipped a step
bbw_seq_pattern_id      str           last 3 transitions e.g. 'BGY'
bbw_seq_from_blue_bars  float/NaN     bars since last blue
bbw_seq_from_red_bars   float/NaN     bars since last red
```

### Layer 3: 17 columns (8 per window × 2 windows + fwd_atr)
```
fwd_atr                  float        ATR at entry bar (Wilder's, period=14)

Per window N (default N=10,20):
fwd_N_max_up_pct         float ≥ 0    max upside %
fwd_N_max_down_pct       float ≤ 0    max downside % (NEGATIVE)
fwd_N_max_up_atr         float ≥ 0    max upside in ATR multiples
fwd_N_max_down_atr       float ≥ 0    max downside in ATR multiples (POSITIVE, direction stripped)
fwd_N_close_pct          float ±      close-to-close %
fwd_N_direction          str          'up'|'down'|'flat'
fwd_N_max_range_atr      float ≥ 0    full range in ATR
fwd_N_proper_move        bool         range_atr ≥ 3.0

NaN zones: last N bars per window, first 14 bars (ATR warmup)
```

### Layer 4 (planned): outputs
```
SimulatorResult dataclass:
  group_stats    dict[str, DataFrame]   7 analysis groups (A-G)
  lsg_results    DataFrame              full grid search (384 combos × states × dirs × windows)
  lsg_top        DataFrame              top 3 per state × window × direction
  scaling_results DataFrame             6 scaling scenarios with verdicts
  summary        dict                   metadata, runtime, counts
```

## LAYER 4 KEY DESIGN DECISIONS (locked, do not revisit)

1. TP/SL ambiguity → use close_pct as PnL (conservative, Monte Carlo validates)
2. No per-bar PnL storage (inline cumsum for drawdown, scalar output only)
3. No transaction costs (raw edge first, config.fee_pct later)
4. States from L1 only (7 bbwp_state values)
5. Scaling uses best LSG from grid for base PnL comparison
6. Bins start at -1 (defensive for bars_in_state)
7. Group G uses pandas mask (not np.char.add) to avoid None→'None'
8. valid_mask checks ALL configured windows dynamically
9. profit_factor: NaN if both sum(wins) and sum(losses) are 0
10. edge_pct guard: NaN if abs(mean_base_pnl) < 1e-10

## LAYER 5 SCOPE (from architecture doc)

**File:** `research/bbw_report.py`
**Input:** SimulatorResult from Layer 4 + Monte Carlo results from Layer 4b
**Output:** CSV tables in `reports/bbw/` directory tree:

```
reports/bbw/
├── aggregate/
│   ├── bbw_state_stats.csv
│   ├── spectrum_color_stats.csv
│   ├── sequence_direction_stats.csv
│   ├── sequence_pattern_stats.csv
│   ├── skip_detection_stats.csv
│   ├── duration_cross_stats.csv
│   └── ma_cross_stats.csv
├── scaling/
│   └── scaling_sequences.csv
├── per_tier/
│   ├── tier_0_optimal_lsg.csv
│   ├── tier_1_optimal_lsg.csv
│   ├── tier_2_optimal_lsg.csv
│   └── tier_3_optimal_lsg.csv
├── sensitivity/
│   └── param_sensitivity.csv
├── monte_carlo/
│   ├── mc_summary_by_state.csv
│   ├── mc_confidence_intervals.csv
│   ├── mc_equity_distribution.csv
│   └── mc_overfit_flags.csv
└── ollama/
    └── (Layer 6 outputs)
```

**NOTE:** Layer 5 depends on BOTH Layer 4 AND Layer 4b. Layer 4b (Monte Carlo) must be built first.

## BUILD ORDER REMAINING

```
NEXT:  Layer 4  → execute BUILDS\PROMPT-LAYER4-BUILD.md in Claude Code
THEN:  Layer 4b → research/bbw_monte_carlo.py (needs build prompt)
THEN:  Layer 5  → research/bbw_report.py (needs build prompt)
THEN:  Layer 6  → research/bbw_ollama_review.py (needs build prompt)
```

## AUDIT SUMMARY — what was fixed this session

22 total issues across 2 audit rounds. All resolved. Key fixes:
- PnL formula clarified with per-bar ATR/close enforcement
- Ambiguous TP/SL case defined (close_pct based)
- valid_mask made dynamic across all windows
- Removed meaningless expectancy_per_bar metric
- Added max_drawdown vectorized pattern (np.maximum.accumulate on 2D)
- Fixed scaling circular dependency (lsg_top passed explicitly)
- Architecture doc corrected: L3 input (OHLCV only), spectrum (4 colors)
- Pipeline coordination: L3 windows ⊇ L4 config.windows enforced in debug script

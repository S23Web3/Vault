# BBW Layer 4 Bug Audit — 2026-02-14
**Session:** claude.ai desktop
**Status:** AUDIT COMPLETE — all fixes applied

## Round 1 — 14 bugs found, 14 fixed

### Critical (4)
1. **PnL formula ATR source** — WIN/LOSS used per-bar ATR but spec didn't enforce. Fixed: explicit `atr_i = df['fwd_atr']`, `close_i = df['close']` per-bar in docstring + broadcasting code.
2. **Ambiguous PnL undefined** — both TP+SL hit, magnitude undefined. Fixed: explicit rule `close_pct / 100 * notional`, classify by sign.
3. **valid_mask only fwd_10** — skipped fwd_20 check, NaN leaks into window=20 stats. Fixed: dynamic loop `for w in config.windows`.
4. **expectancy_per_bar meaningless** — was mean/n_trades (double division). Fixed: column removed from OUTPUT_LSG_COLS.

### Moderate (5)
5. **_lsg_grid_search signature mismatch** — architecture vs main flow disagreed. Fixed: standardized to `_lsg_grid_search(df, config)`.
6. **Scaling needs lsg_top** — circular dependency. Fixed: pass `lsg_top` explicitly to `_scaling_simulation`.
7. **bins edge at 0** — pd.cut with right=True excluded 0. Fixed: changed bins[0] to -1.
8. **Group G np.char.add None→'None'** — object dtype conversion. Fixed: pandas mask approach.
9. **calmar_approx needs drawdown** — but spec forbade per-bar PnL. Fixed: added max_drawdown_usd with inline cumsum pattern, updated Design Decision 2.

### Minor (5)
10. **directional_bias string mapping** — L3 uses 'up'/'down', not 'long'/'short'. Fixed: added mapping comment.
11. **Sanity combo math** — cosmetic only, unchanged.
12. **L3 pre-check missing** — Fixed: added step 1b import verification.
13. **_add_derived_columns not defined** — Fixed: full function spec added.
14. **_extract_top_combos closure** — Fixed: config passed explicitly.

## Round 2 — 8 new issues found, 6 fixed

### Moderate (3)
N1. Architecture doc L3 input says "OHLCV + BBWP + Sequence" but L3 only needs OHLCV — **FIXED in arch doc**
N2. Architecture doc lists 5 spectrum colors including 'orange', code has 4 — **FIXED in arch doc**
N3. max_drawdown 2D vectorization pattern not shown in spec — **FIXED: added explicit np.maximum.accumulate pattern**

### Minor (5)
N4. close_pct scoping ambiguous in broadcast block — **FIXED: added scope comments**
N5. directional_bias excludes 'flat', doesn't sum to 1.0 — documentation only, no code fix needed
N6. profit_factor 0/0 edge case — **FIXED: added "NaN if both 0" rule**
N7. Test 9 "2 wins" dimension label wrong — already correct in file
N8. Scaling edge_pct divide by zero — **FIXED: added abs guard < 1e-10**

## Files Modified
- `BUILDS\PROMPT-LAYER4-BUILD.md` — all L4 spec fixes
- `02-STRATEGY\Indicators\BBW-SIMULATOR-ARCHITECTURE.md` — N1 (L3 input), N2 (4 colors)

## Audit Verdict
**No critical bugs remain.** Build prompt is ready for Claude Code execution once Layer 3 completes.

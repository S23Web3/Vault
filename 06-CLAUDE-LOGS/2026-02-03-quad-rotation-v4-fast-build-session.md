# 2026-02-03 Quad Rotation Stochastic v4 & FAST Build Session

## Session Summary

Built and critically reviewed two Pine Script v6 indicator specifications:
1. **Quad Rotation Stochastic v4.1** - Slow/conservative (40-4 divergence leads)
2. **Quad Rotation Stochastic FAST v1.1** - Fast/aggressive (9-3 + 14-3 lead)

---

## Key Decisions Made

### v4.1 (Slow) Philosophy
- Trade WITH trend only (Ripster direction)
- Divergence = WARNING of exhaustion, not guaranteed reversal
- Missing reversals is INTENTIONAL (HPS setups only)
- Stop outs are ACCEPTED as part of trading
- 5-bar lookback for both angle AND agreement

### FAST v1.1 Philosophy
- 9-3 + 14-3 are PRIMARY triggers
- 40-4 and 60-10 provide CONTEXT (slow context)
- Earlier entries, higher risk
- Best for pullback/continuation trades in established trends

---

## Critical Bugs Found & Fixed

### v4.1 Issues (11 total)
1. Stochastic calculations - separate fast/full functions
2. 60-10 needs DOUBLE smoothing
3. State machine multiple execution - use if/else if chains
4. Divergence stoch tracking - store AT price, not min/max
5. Supersignal timing conflict - added persistence window
6. JSON payload - hidden plots, removed strategy.order.action
7. Angle extreme values - use absolute change /100
8. Exit alert naming → Management alerts
9. Missing stage alerts - added to BUILD NOTES
10. Embedded detection alerts - added
11. Rotation alert clarity - labeled as context

### Additional Fix (v4.1)
- All alerts edge-triggered (`and not X[1]`)

### FAST v1.1 Issues (5 total)
1. `bear_state_bar` typo → `bear_stage1_bar`
2. Turn detection false positive - added `stoch > stoch[1]` check
3. Unnecessary `var` tracking - simplified with `[1]`
4. Duplicate hidden plots - kept separate for JSON
5. Missing 50 midline - added hline

---

## Pine Script Skill Updated

Major v2.0 update to `/skills/pinescript/SKILL.md`:
- Fast vs Full stochastic functions
- State machine pattern with if/else if chains
- Edge detection requirements
- Turn detection with momentum confirmation
- Supersignal timing with persistence
- Hidden plots for JSON
- Code review checklist

---

## Files Created/Modified

| File | Action |
|------|--------|
| `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-v4-BUILD-SPEC.md` | Updated to v4.1 |
| `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-FAST-BUILD-SPEC.md` | Created v1.1 |
| `skills/pinescript/SKILL.md` | Created v2.0 |

---

## Next Steps

1. Open VS Code terminal
2. Run `claude`
3. Build SLOW indicator first:
   ```
   Read skill: C:\Users\User\Documents\Obsidian Vault\skills\pinescript\SKILL.md
   Read spec: C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Quad-Rotation-Stochastic-v4-BUILD-SPEC.md
   Output: C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Quad-Rotation-Stochastic-v4.pine
   ```
4. Build FAST indicator:
   ```
   Read skill: C:\Users\User\Documents\Obsidian Vault\skills\pinescript\SKILL.md
   Read spec: C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Quad-Rotation-Stochastic-FAST-BUILD-SPEC.md
   Output: C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Quad-Rotation-Stochastic-FAST.pine
   ```
5. Test both on TradingView

---

## Key Learnings for Future Builds

### State Machines
- ALWAYS use `if/else if` chains
- Store indicator value AT the price point, not min/max
- Track bars since event for timing windows

### Alerts
- ALWAYS edge-trigger: `condition and not condition[1]`
- Management = raise stop, Exit = close position
- Hidden plots needed for JSON payloads

### Turn Detection
- Must check BOTH lookback AND current momentum
- `stoch > stoch[lookback] AND stoch > stoch[1]`

### Stochastics
- Fast = single smooth: `ta.sma(rawK, smooth)`
- Full = double smooth: `ta.sma(ta.sma(rawK, smooth), smooth)`

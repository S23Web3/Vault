# B4 — PnL Reversal Analysis Panel Build Spec

**Build ID:** VINCE-B4
**Status:** BLOCKED (depends on B1 -> B2 -> B3 completing first)
**Date:** 2026-02-28
**Priority:** HIGHEST (Panel 2 — first panel to build after infrastructure is ready)
**Source research:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-vince-b4-scope-audit.md`

---

## What B4 Is

Panel 2 — PnL Reversal Analysis. Answers: "At what point does holding longer start costing money?"
Pure data + figure functions. No Dash layout code (layout lives in B6).

---

## Skills to Load Before Building

- `/python` — MANDATORY
- `/dash` — MANDATORY (any file in vince/)

---

## Files

| # | File | Lines (est.) | Action |
|---|------|-------------|--------|
| 1 | `vince/pages/__init__.py` | 1 | Create (empty) |
| 2 | `vince/pages/pnl_reversal.py` | ~140 | Create — data + figure functions |
| 3 | `tests/test_b4_pnl_reversal.py` | ~40 | Create |

---

## Hard Blocker

The entire `vince/` directory does not exist. B1, B2, B3 must complete before B4 can build.
B3 is itself blocked on 8 open questions (see BUILD-VINCE-B3-ENRICHER.md).

---

## 8 Bottlenecks (from research audit)

1. mfe and saw_green field names must be verified against actual Trade384/v385 output
2. TP sweep simulation logic: effective_exit = min(mfe_atr, tp_mult) — confirm sign convention for SHORT trades
3. ATR bin granularity: 5 bins vs 9 bins (0-0.25, 0.25-0.5, etc.) — finer = more insight
4. RL overlay scope: stub returns None now, separate scoping session required before real implementation
5. Optimal exit calculation must enforce: trade_count >= 95% of full set (guard against TP that filters trades)
6. MFE approximation for "would have hit TP": if mfe_atr >= tp_mult, approximate exit PnL from entry_price + tp_mult * atr_at_entry
7. Commission must be subtracted in TP sweep simulation (not just gross PnL)
8. Date range filtering on the EnrichedTradeSet before passing to panel functions

---

## 6 Improvements (from research audit — apply when building)

1. Use 9 ATR bins instead of 5 for finer granularity (0-0.25, 0.25-0.5, 0.5-0.75, 0.75-1.0, 1.0-1.5, 1.5-2.0, 2.0-3.0, 3.0-4.0, 4.0+)
2. Add "winners left on table" metric: count of winning trades where mfe_atr > 2x actual exit ATR
3. Per-grade TP sweep: run separate TP sweep for A/B/C grades side by side
4. Dual curve: gross PnL curve + net PnL curve (commission-adjusted) on same chart
5. Date range filter on panel inputs (not just on the full enriched set)
6. BE-adjusted MFE: if be_raised=True, treat SL as entry price for MFE calculation

---

## MFE Histogram

Input: `EnrichedTradeSet`
Bins (ATR units): 9 bins (see improvement 1 above)
Per bin: count, win_rate, avg_net_pnl
Returns: `go.Figure` — grouped bar chart, count bars + win_rate line on secondary y-axis

---

## TP Sweep Curve

Input: `EnrichedTradeSet`, tp_range=(0.5, 5.0), steps=19
For each TP multiple t:
  For each trade:
    If mfe_atr >= t -> PnL = (tp_mult * atr_at_entry) * qty - commission (approximation)
    If mfe_atr < t  -> PnL = actual pnl (reversal hit before TP)
  Sum net PnL across all trades
Returns: `go.Figure` — line chart, vertical marker at optimal TP

---

## Optimal Exit Banner

Returns dict: `optimal_tp_mult`, `optimal_net_pnl`, `vs_current_pnl` (delta from no-TP baseline)
Constraint: only consider tp_mult values where trade_count >= 95% of full set

---

## RL Overlay (PLACEHOLDER)

```python
def rl_overlay_figure(trade_set) -> None:
    """Reserved for RL Exit Policy Optimizer. Separate scoping session required."""
    return None
```

---

## Verification

```bash
python -c "import py_compile; py_compile.compile('vince/pages/pnl_reversal.py', doraise=True); print('OK')"
python tests/test_b4_pnl_reversal.py
```

Test cases (10 synthetic EnrichedTrade rows, mixed winners/losers):
1. MFE histogram figure has correct number of bins
2. TP sweep figure has 19 x-axis points
3. optimal_tp_mult in range [0.5, 5.0]
4. vs_current_pnl is a float
5. rl_overlay_figure() returns None without error

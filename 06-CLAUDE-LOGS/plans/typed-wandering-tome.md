# Dashboard v3.9.1 -- Engine + Capital Model + Display Fix

## Context

Two portfolio modes: "Per-Coin Independent" (each coin at $10k) and "Shared Pool" (user deposits $10k, each trade takes $500 margin from pool). Shared Pool shows impossible numbers: Pool P&L = -$9,513 while per-coin sum = +$4,656. Root causes:

1. **Engine exit commission wrong**: SL/TP/scale-out exits charge taker (0.08%) instead of maker (0.02%). 4x overcharge on exits.
2. **Scale-out trades treated as separate positions**: A position with 2 scale-outs creates 3 Trade384 records in trades_df. Capital model treats each as needing $500 margin = $1,500 per position instead of $500.
3. **Double margin deduction**: `available = pool_balance - margin_in_use` but pool_balance already had margin deducted on entry.
4. **Inconsistent baselines**: engine N*10k vs pool balance vs deposit amount across dashboard sections.

## Files to Modify

| # | File | Change |
|---|------|--------|
| 1 | `engine/backtester_v384.py` | Direct edit: SL/TP/scale-out exits use `maker=True` |
| 2 | `utils/capital_model_v2.py` | Build script: exchange-model pool, position grouping |
| 3 | `scripts/dashboard_v391.py` | Build script: patched from v39 with display fixes |
| 4 | `utils/pdf_exporter_v2.py` | Build script: patched from v1 with Mode 2 awareness |

## Bug List

| # | Bug | Fix |
|---|-----|-----|
| E1 | SL/TP/scale-out exits charge taker not maker | `charge_custom(notional, maker=True)` at lines 144, 174, 407 |
| C1 | Scale-out trades = separate pool positions | Group trades by position (coin + entry_bar), one event per position |
| C2 | Double margin deduction | Track `balance` and `margin_used` separately, `available = balance - margin_used` |
| D1 | Net P&L: pool_pnl vs equity vs per-coin sum | Single source: rebased equity for Mode 2 |
| D2 | DD% against N*10k not deposit | Compute on rebased equity |
| D3 | Equity chart starts at N*10k | Plot rebased_chart_eq in Mode 2 |
| D4 | Best/worst use _engine_baseline | Use _baseline (= total_capital in Mode 2) |
| D5 | Hardcoded 10000.0 in drill-down | Use _eq_per_coin |
| D6 | fillna(10000.0) in align | Use eq_series.iloc[0] |
| D7 | PDF uses engine baseline | Pass capital_result, use pool_pnl |

---

## Implementation

### Step 1: Engine fix (direct edit, not in build script)

```python
# backtester_v384.py -- 3 lines changed
Line 144: self.comm.charge_custom(slots[s].notional, maker=True)   # SL/TP exit
Line 174: self.comm.charge_custom(scale_notional, maker=True)       # Scale-out exit
Line 407: self.comm.charge_custom(slots[s].notional, maker=True)   # END close
```

### Step 2: Capital model v2 (in build script)

**Position grouping** -- dict keyed by `(coin, entry_bar)` collapses scale-out records into one position event:
```python
# Step 1: Group Trade384 records into positions (dict)
positions = {}  # key: (coin, entry_bar_master) -> position_info dict

for each coin's trades_df:
    grouped = tdf.groupby("entry_bar")
    for entry_bar, group:
        key = (coin, entry_bar_master)
        positions[key] = {
            "coin": coin,
            "entry_bar": entry_bar_master,
            "exit_bar": max(group["exit_bar"]) mapped to master,
            "net_pnl": sum(group["net_pnl"]),
            "commission": sum(group["commission"]),
            "grade": group.iloc[0]["grade"],
            "strength": grade_priority,
            "n_records": len(group),
            "trade_indices": list(group.index),  # for rejection filtering
        }

# Step 2: Sort into event list for processing
events = sorted(positions.values(), key=lambda p: (p["entry_bar"], -p["strength"]))
```

**Exchange-model pool balance** -- separate balance from margin_used (list for active tracking):
```python
balance = total_capital     # realized cash, changes ONLY on trade close
margin_used = 0             # locked capital, changes on open/close
active = []                 # list of (exit_bar, net_pnl) -- simple, no dict needed

for position in events:
    bar = position["entry_bar"]

    # 1. Close expired positions (exit_bar <= current_bar):
    still_active = []
    for (a_exit, a_pnl) in active:
        if a_exit <= bar:
            balance += a_pnl          # P&L settles to balance
            margin_used -= margin     # margin released
        else:
            still_active.append((a_exit, a_pnl))
    active = still_active

    # 2. Check available
    available = balance - margin_used

    # 3. Accept or reject
    if available >= margin:
        margin_used += margin         # lock margin
        active.append((position["exit_bar"], position["net_pnl"]))
        accepted.append(position)
    else:
        rejected.append(position)
```

**Lifecycle**: Dict is one-shot grouping (like SQL GROUP BY), built once then converted to sorted list
and discarded. `active` list is a sliding window of open positions -- never more than ~4-8 entries,
shrinks as positions close. No unbounded growth. Total runtime: one pass through ~900 events.

No double deduction. No scale-out confusion. Balance tracks realized P&L only.

**Pool balance history**: Per-bar array of `balance` for capital chart overlay:
```python
balance_history = np.full(n_bars, total_capital, dtype=float)
# After processing each event, update balance_history[bar:] = balance
# This gives a step function showing realized pool balance over time
```

**Note on close_at()**: `scale_idx=0` is hardcoded for SL/TP/END closes (position_v384.py:294).
Scale-out records have `scale_idx=1,2,...` But grouping by `(coin, entry_bar)` handles all cases
correctly -- both scale-out children and the final close record share the same entry_bar.

**Rebased equity**: `rebased_chart_eq = adjusted_portfolio_eq - engine_baseline + total_capital` for equity chart and DD%/best/worst computation.

**Metrics rebuild**: Same `_rebuild_metrics_from_df` with commission-ratio volume scaling.

### Step 3: Dashboard patches (12 patches in build script)

1. Import capital_model_v2
2. fillna fix
3-4. Hardcoded 10000.0 -> _eq_per_coin in drill-down
5. Net P&L from rebased equity in Mode 2
6. Best/worst use _baseline
7. Per-coin chart lines as P&L contribution in Mode 2
8. Portfolio chart line from rebased_chart_eq
9. Pool balance trace on capital chart
10. Volume section Mode 2 caption
11. Version strings
12. PDF import + call updates

### Step 4: PDF exporter v2 (patches in build script)

- Add capital_result parameter
- Use pool_pnl for Net P&L
- Use rebased_chart_eq for equity chart
- Add pool stats to summary table

---

## Build Approach

- Engine fix: Direct Edit tool (3 lines in backtester_v384.py)
- Build script: `scripts/build_dashboard_v391.py` creates 3 files, py_compiles each
- Overwrites existing build script (it's a builder, not production)

## Verification

1. py_compile all 4 files
2. Mode 1 (Per-Coin Independent): numbers unchanged from v39
3. Mode 2 (Shared Pool $10k, 2 coins NOTUSDT + SUSDT):
   - Net P&L positive (matches per-coin sum)
   - Rejected count reasonable (not inflated by scale-out phantom)
   - DD% relative to $10k deposit
   - Equity chart starts at $10k
   - Pool balance trace visible on capital chart
4. Edge: 1 coin in Mode 2 -- no division errors
5. Edge: All trades accepted -- pool_pnl = per-coin net exactly

## Run Commands
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v391.py"
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v391.py"
```

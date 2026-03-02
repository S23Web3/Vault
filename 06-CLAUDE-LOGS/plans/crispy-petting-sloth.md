# v386 Scoping Build
# Agent-executable instruction set.
# Date: 2026-02-28

---

## CONTEXT

The BingX bot's `config.yaml` reveals exactly what changed from v384 to the current live strategy.
One parameter is responsible for the drop from ~93 trades/day to ~40: `require_stage2: true`.

This build documents the changes, produces `signals/four_pillars_v386.py` and
`docs/FOUR-PILLARS-STRATEGY-v386.md`, then updates backlog and memory.

No new state machine is needed — existing `signals/state_machine.py` already supports
`require_stage2`. v386 is the same pipeline with new defaults locked in.

**Root path:** `C:\Users\User\Documents\Obsidian Vault`
**Backtester path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester`

---

## WHAT CHANGED: v384 -> v386

### Source of truth: `PROJECTS/bingx-connector/config.yaml` (read 2026-02-28)

| Parameter | v384 default | v386 default | Effect |
|-----------|-------------|-------------|--------|
| `require_stage2` | `False` | `True` | Grade A only fires if Stoch40+60 rotated during Stage 1 AND price was at/near Cloud3 within 5 bars |
| `allow_c` | `True` | `False` | C-grade trades disabled entirely |
| `tp_atr_mult` | varies | `None` | No fixed TP — trailing stop only |
| `rot_level` | 80 | 80 | Unchanged |

### What Stage 2 filter does (from state_machine.py — already implemented)

When `require_stage2=True`, a Grade A LONG only fires if ALL of:
1. Stoch40 crossed ABOVE (100 - rot_level = 20) during Stage 1 — momentum confirmation
2. Stoch60 crossed ABOVE 20 during Stage 1 — macro trend confirmation
3. Price was at or above Cloud3 within the last `cloud3_window=5` bars

This filters out setups where the macro trend does not yet support the entry.
Grade B is unaffected by Stage 2.
Grade A blocked by Stage 2 does NOT degrade to Grade B (explicit guard already in state machine).

### Economic model (v386)
- Rebates earned on volume: ~$47K rebate on $138M total volume
- Quality signal filter (Stage 2) prevents account from bleeding on low-conviction setups
- Target: enough trades per day for meaningful rebate accumulation + positive expectancy
- 40 trades/day on 47 coins = ~0.85 trades/coin/day — sustainable, not overtraded

---

## HARD RULES

- NEVER OVERWRITE FILES — Glob before every Write. If file exists, stop and report.
- FULL PATHS EVERYWHERE — every reference must be the full Windows path.
- PYTHON SKILL MANDATORY — load `/python` before writing `four_pillars_v386.py`.
- MANDATORY py_compile — validate immediately after writing .py file.
- JOURNALS: EDIT ONLY, NEVER WRITE — INDEX.md, TOPIC files, PRODUCT-BACKLOG.md.
- MANDATORY timestamps on all log entries.

---

## FILES PRE-READ (no further reads needed)

| File | Key finding |
|------|-------------|
| `PROJECTS/bingx-connector/config.yaml` | `require_stage2: true`, `allow_c: false`, `tp_atr_mult: null` |
| `PROJECTS/bingx-connector/plugins/four_pillars_v384.py` | Wrapper only — calls compute_signals() from backtester |
| `PROJECTS/four-pillars-backtester/signals/four_pillars.py` | Source to copy — orchestrates stoch+clouds+ATR+state_machine |
| `PROJECTS/four-pillars-backtester/signals/state_machine.py` | Already has require_stage2 support — no changes needed |
| `PROJECTS/four-pillars-backtester/strategies/base_v2.py` | Plugin ABC — FourPillarsPlugin must implement this |

---

## STEP 1 — Glob check (no overwrite)

Before writing any file, Glob:
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v386.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-STRATEGY-v386.md`

If either exists: STOP, report, do not write.

---

## STEP 2 — Write `signals/four_pillars_v386.py`

**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v386.py`

Load `/python` skill first.

Copy of `signals/four_pillars.py` with TWO defaults changed:
- `allow_c_trades` default: `False` (was `True`)
- `require_stage2` default: `True` (was `False`)

```python
"""
Four Pillars v3.8.6 signal pipeline.

Changes from v3.8.4:
- require_stage2 default: True (was False)
  Grade A only fires when Stoch40+60 rotated during Stage 1
  AND price was at/near Cloud3 within cloud3_window bars.
  Removes low-conviction setups. Reduces ~93/day to ~40/day on 47-coin set.
- allow_c_trades default: False (was True)
  C-grade disabled — insufficient edge vs rebate cost.

State machine (state_machine.py) unchanged — all Stage 2 logic already present.
Economic model: volume -> rebates. Quality filter keeps account from bleeding.
"""

import numpy as np
import pandas as pd

from .stochastics import compute_all_stochastics
from .clouds import compute_clouds
from .state_machine import FourPillarsStateMachine, SignalResult


def compute_signals(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Run the full Four Pillars v3.8.6 signal pipeline on OHLCV data.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, base_vol, quote_vol]
        params: Strategy parameters. Defaults reflect v3.8.6 live config.

    Returns:
        DataFrame with all indicator and signal columns added.
    """
    if params is None:
        params = {}

    df = compute_all_stochastics(df, params)
    df = compute_clouds(df, params)

    # ATR (manual, matching Pine Script ta.atr(14))
    atr_len = params.get("atr_length", 14)
    tr = np.maximum(
        df["high"].values - df["low"].values,
        np.maximum(
            np.abs(df["high"].values - np.roll(df["close"].values, 1)),
            np.abs(df["low"].values - np.roll(df["close"].values, 1))
        )
    )
    tr[0] = df["high"].iloc[0] - df["low"].iloc[0]
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    df["atr"] = atr

    # v3.8.6 defaults: require_stage2=True, allow_c=False
    sm = FourPillarsStateMachine(
        cross_level=params.get("cross_level", 25),
        zone_level=params.get("zone_level", 30),
        stage_lookback=params.get("stage_lookback", 10),
        allow_b=params.get("allow_b_trades", True),
        allow_c=params.get("allow_c_trades", False),        # v386: False (was True)
        b_open_fresh=params.get("b_open_fresh", True),
        cloud2_reentry=params.get("cloud2_reentry", True),
        reentry_lookback=params.get("reentry_lookback", 10),
        use_ripster=params.get("use_ripster", False),
        use_60d=params.get("use_60d", False),
        require_stage2=params.get("require_stage2", True),  # v386: True (was False)
        rot_level=params.get("rot_level", 80),
        cloud3_window=params.get("cloud3_window", 5),
    )

    n = len(df)
    signals = {
        "long_a": np.zeros(n, dtype=bool),
        "long_b": np.zeros(n, dtype=bool),
        "long_c": np.zeros(n, dtype=bool),
        "short_a": np.zeros(n, dtype=bool),
        "short_b": np.zeros(n, dtype=bool),
        "short_c": np.zeros(n, dtype=bool),
        "reentry_long": np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
    }

    stoch_9 = df["stoch_9"].values
    stoch_14 = df["stoch_14"].values
    stoch_40 = df["stoch_40"].values
    stoch_60 = df["stoch_60"].values
    stoch_60_d = df["stoch_60_d"].values
    cloud3_bull = df["cloud3_bull"].values
    price_pos = df["price_pos"].values
    cross_above = df["price_cross_above_cloud2"].values
    cross_below = df["price_cross_below_cloud2"].values

    for i in range(n):
        if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
            continue

        result = sm.process_bar(
            bar_index=i,
            stoch_9=stoch_9[i],
            stoch_14=stoch_14[i],
            stoch_40=stoch_40[i],
            stoch_60=stoch_60[i],
            stoch_60_d=stoch_60_d[i],
            cloud3_bull=bool(cloud3_bull[i]),
            price_pos=int(price_pos[i]),
            price_cross_above_cloud2=bool(cross_above[i]),
            price_cross_below_cloud2=bool(cross_below[i]),
        )

        signals["long_a"][i] = result.long_a
        signals["long_b"][i] = result.long_b
        signals["long_c"][i] = result.long_c
        signals["short_a"][i] = result.short_a
        signals["short_b"][i] = result.short_b
        signals["short_c"][i] = result.short_c
        signals["reentry_long"][i] = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short

    for col, arr in signals.items():
        df[col] = arr

    return df
```

After writing, run py_compile from backtester root:
```
python -c "import py_compile; py_compile.compile('signals/four_pillars_v386.py', doraise=True); print('OK')"
```

---

## STEP 3 — Write `docs/FOUR-PILLARS-STRATEGY-v386.md`

**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-STRATEGY-v386.md`

```markdown
# Four Pillars Strategy — v3.8.6

**Version:** 3.8.6
**Date locked:** 2026-02-28
**Signal file:** `signals/four_pillars_v386.py`
**State machine:** `signals/state_machine.py` (unchanged from v3.8.4)
**Live bot:** BingX connector, `config.yaml` as of 2026-02-28

---

## Strategy Summary

Four Pillars is a multi-timeframe stochastic momentum strategy.
Entries are classified A/B by signal quality (C disabled in v3.8.6).
v3.8.6 adds a Stage 2 conviction filter that eliminates low-quality setups
while preserving the trade volume needed for exchange rebate farming.

Economic model: earn rebates on volume (~34% of gross commission returned),
deploy only when macro and micro momentum align.

---

## Indicators

### Stochastics (John Kurisko Raw K — smooth=1)

| Name | Period | Role |
|------|--------|------|
| Stoch9 | 9-3 | Entry trigger |
| Stoch14 | 14-3 | Setup confirmation |
| Stoch40 | 40-3 | Swing momentum |
| Stoch60 | 60-10 | Macro momentum |

### Ripster EMA Clouds

| Cloud | EMAs | Role |
|-------|------|------|
| Cloud2 | 5/12 | Re-entry trigger |
| Cloud3 | 34/50 | Directional filter (primary) |
| Cloud4 | 72/89 | Swing filter |
| Cloud5 | 180/200 | Macro filter |

### ATR
- Period: 14 (Wilder RMA)
- Used for: SL sizing, trailing stop activation, min_atr_ratio filter

---

## Entry Logic

### Stage 1 — Setup Detection

- LONG: Stoch9 drops BELOW 25 (cross_level)
- SHORT: Stoch9 rises ABOVE 75 (100 - cross_level)
- Lookback window: 10 bars (stage_lookback)

During Stage 1, track:
- Did Stoch14 enter zone (below 30 for LONG, above 70 for SHORT)?
- Did Stoch40 enter zone?
- Did Stoch60 enter zone?
- Did Stoch40/60 rotate through 20 (LONG) or 80 (SHORT)?
- Was price at/near Cloud3 within last 5 bars?

### Stage 2 — Conviction Filter (v3.8.6 — MANDATORY)

Grade A only fires if ALL of:
1. Stoch40 rotated through 20 (LONG) or 80 (SHORT) during Stage 1
2. Stoch60 rotated through 20 (LONG) or 80 (SHORT) during Stage 1
3. Price was at/above Cloud3 (LONG) or at/below Cloud3 (SHORT) within last 5 bars

Without Stage 2: ~93 trades/day on 47 coins.
With Stage 2: ~40 trades/day on 47 coins. Higher conviction per trade.

### Signal Grades

| Grade | Condition | Stage 2 required | v3.8.6 enabled |
|-------|-----------|-----------------|----------------|
| A | Stoch14 + Stoch40 + Stoch60 all in zone AND Cloud3 ok | YES | YES |
| B | Any 2 of (Stoch14, Stoch40, Stoch60) in zone AND Cloud3 ok | NO | YES |
| C | Stoch14 in zone AND price inside Cloud3 | NO | NO (disabled) |

Grade A blocked by Stage 2 does NOT fall back to Grade B.

---

## Risk Parameters (Live — 2026-02-28)

| Parameter | Value |
|-----------|-------|
| Margin per trade | $5 USDT isolated |
| Leverage | 10x ($50 notional) |
| SL | 2.0x ATR (mark price) |
| Fixed TP | None |
| Trailing activation | 2.0x ATR from entry |
| Trailing callback | 2% from peak |
| Max open positions | 8 |
| Max daily trades | 50 |
| Daily loss limit | $15 |
| Cooldown | 3 bars per symbol+direction |
| Min ATR ratio | 0.003 |

---

## Coin Selection (v3.8.6 — 47 coins)

Filter applied before adding to active list:
- Trades >= 400 (statistical significance)
- Profit Factor >= 1.03
- Max Drawdown <= 30%
- Expectancy > 0

14 high-Expectancy originals + 33 low-drawdown additions.
Full list: `PROJECTS/bingx-connector/config.yaml`

---

## Differences from v3.8.4

| Aspect | v3.8.4 | v3.8.6 |
|--------|--------|--------|
| Stage 2 filter | Off | On (require_stage2=True) |
| C-grade | Enabled | Disabled |
| Fixed TP | Optional | None — trailing only |
| Trade frequency | ~93/day | ~40/day (47 coins) |
| State machine | state_machine.py | state_machine.py (unchanged) |

---

## Signal File Usage

```python
from signals.four_pillars_v386 import compute_signals

# v386 defaults (require_stage2=True, allow_c=False):
df = compute_signals(ohlcv_df)

# Override to replicate v384 behavior for comparison:
df = compute_signals(ohlcv_df, params={"require_stage2": False, "allow_c_trades": True})
```

---

## Vince Plugin

`FourPillarsPlugin` (Vince B1) wraps `signals/four_pillars_v386.py`.
All access goes through `vince/api.py` — pages never call compute_signals directly.
Plugin interface: `strategies/base_v2.py` (StrategyPlugin ABC).
```

---

## STEP 4 — Update PRODUCT-BACKLOG.md

**File:** `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md`

Use Edit tool. Two changes:

Change 1 — P0.5 status READY -> DONE:
Find: `| P0.5 | v386 Scoping Session | READY — do first |`
Replace with: `| P0.5 | v386 Scoping Session | DONE |`
Notes: `Produced: signals/four_pillars_v386.py + docs/FOUR-PILLARS-STRATEGY-v386.md. Key: require_stage2=True + allow_c=False. Freq: ~93/day -> ~40/day.`

Change 2 — P0.6 READY after v386 -> READY:
Find: `| P0.6 | Vince B1 — FourPillarsPlugin | READY after v386 |`
Replace: `| P0.6 | Vince B1 — FourPillarsPlugin | READY |`

Also update Last updated date line.

---

## STEP 5 — Append to TOPIC-vince-v2.md

**File:** `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-vince-v2.md`

Use Edit tool to append:

```

## v386 Signal File (built 2026-02-28)

- **File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v386.py`
- **Strategy doc**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-STRATEGY-v386.md`
- **Key changes**: `require_stage2=True` (was False) — Grade A only fires when Stoch40+60 rotated AND price at Cloud3 within 5 bars. `allow_c=False` (was True).
- Trade frequency: ~93/day -> ~40/day on 47-coin set.
- State machine (state_machine.py) unchanged — Stage 2 logic was already there.
- `FourPillarsPlugin` (B1) wraps this file. B1 and B3 now unblocked on signal file dependency.
```

---

## STEP 6 — Create session log + update INDEX.md

**Session log path:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-v386-scoping.md`

Glob first — if exists, append. If not, Write new file:

```markdown
# v386 Scoping Session Log
**Date:** 2026-02-28
**Timestamp:** [insert at execution time]

## What was built
- `signals/four_pillars_v386.py` — v3.8.6 signal pipeline with Stage 2 filter on by default
- `docs/FOUR-PILLARS-STRATEGY-v386.md` — full strategy doc

## Key finding
`config.yaml` confirms: `require_stage2: true` is the sole driver of trade reduction.
~93/day -> ~40/day on 47 coins. State machine already supported this — no changes needed.

## Files updated
- `PRODUCT-BACKLOG.md` — P0.5 DONE, P0.6 READY
- `TOPIC-vince-v2.md` — v386 section appended
- `06-CLAUDE-LOGS/INDEX.md` — session log row added
```

Then use Edit tool to append to INDEX.md:
```
- 2026-02-28-v386-scoping.md — v386 scoping: require_stage2=True + allow_c=False, produced signals/four_pillars_v386.py + FOUR-PILLARS-STRATEGY-v386.md
```

---

## PERMISSIONS NEEDED

### Read (all pre-read during planning):
- `PROJECTS/bingx-connector/config.yaml`
- `PROJECTS/bingx-connector/plugins/four_pillars_v384.py`
- `PROJECTS/four-pillars-backtester/signals/four_pillars.py`
- `PROJECTS/four-pillars-backtester/signals/state_machine.py`
- `PROJECTS/four-pillars-backtester/strategies/base_v2.py`

### Write (new files — Glob first):
- `PROJECTS/four-pillars-backtester/signals/four_pillars_v386.py`
- `PROJECTS/four-pillars-backtester/docs/FOUR-PILLARS-STRATEGY-v386.md`
- `06-CLAUDE-LOGS/2026-02-28-v386-scoping.md` (only if does not exist)

### Edit (existing — append only):
- `PRODUCT-BACKLOG.md`
- `memory/TOPIC-vince-v2.md`
- `06-CLAUDE-LOGS/INDEX.md`

### Bash (py_compile only — the one allowed exception):
```
python -c "import py_compile; py_compile.compile('signals/four_pillars_v386.py', doraise=True); print('OK')"
```

---

## VERIFICATION

1. Glob `signals/four_pillars_v386.py` — must exist
2. Glob `docs/FOUR-PILLARS-STRATEGY-v386.md` — must exist
3. py_compile passes on `four_pillars_v386.py`
4. Read first 5 lines of `four_pillars_v386.py` — should show v3.8.6 docstring
5. Read PRODUCT-BACKLOG.md — P0.5 DONE, P0.6 READY
6. Read last 10 lines of TOPIC-vince-v2.md — should include v386 section

---

## EXECUTION STATUS

[ ] Step 1 — Glob check
[ ] Step 2 — Write signals/four_pillars_v386.py + py_compile
[ ] Step 3 — Write docs/FOUR-PILLARS-STRATEGY-v386.md
[ ] Step 4 — Update PRODUCT-BACKLOG.md
[ ] Step 5 — Append TOPIC-vince-v2.md
[ ] Step 6 — Session log + INDEX.md row

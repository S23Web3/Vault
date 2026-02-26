# UML Logic Bug Findings — Architecture Review
**Date:** 2026-02-20  
**Reviewer:** Claude  
**Files Reviewed:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-STRATEGY-UML.md`

**Source Files Cross-Referenced:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\state_machine.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\stochastics.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\clouds.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v384.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\position_v384.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\exit_manager.py`

**Severity Legend:**
- 🔴 CRITICAL — will break at runtime or produce incorrect trades
- 🟠 HIGH — logic mismatch between doc and code, misleads implementation
- 🟡 MEDIUM — doc is incomplete or ambiguous, implementation risk
- 🔵 LOW — clarity or consistency issue, no runtime impact

---

## CONNECTOR UML FINDINGS

---

### BUG-C01 — Direction Vocabulary Inconsistency
**Severity:** 🟡 MEDIUM  
**Location:** `BINGX-CONNECTOR-UML.md` — Section 1 (System Context)  
**Problem:**  
Section 1 strategy sandbox box reads: `Returns: BUY / SELL / HOLD + metadata`  
Section 10 (Plugin Interface Contract) correctly reads: `direction: LONG | SHORT | NONE`  
The same doc uses two different vocabularies for the Signal direction field. BUY/SELL/HOLD is exchange order language. LONG/SHORT/NONE is the position direction language used throughout the codebase and the rest of the doc.  
**Fix:** Change Section 1 sandbox label to `Returns: LONG / SHORT / NONE + metadata` to match Section 10.

---

### BUG-C02 — Mark Price Fetch Uses Wrong API Participant
**Severity:** 🟡 MEDIUM  
**Location:** `BINGX-CONNECTOR-UML.md` — Section 4 (Main Trading Loop Sequence)  
**Problem:**  
Sequence step: `EXEC->>BINGX_K: GET mark_price(symbol)`  
`BINGX_K` is the klines participant (`/quote/klines`). Mark price is a separate endpoint: `/openApi/swap/v2/quote/price`. These are different endpoints with different response structures. The diagram implies the executor reuses the klines call for mark price, which is incorrect.  
**Fix:** Add a `BINGX_PRICE` participant in Section 4, route the mark price call there separately. Mark price is also needed for quantity calculation on every order — it warrants its own participant.

---

### BUG-C03 — halt_flag Missing from RiskGate Data Flow
**Severity:** 🔴 CRITICAL  
**Location:** `BINGX-CONNECTOR-UML.md` — Sections 2 and 5  
**Problem:**  
Section 5 (Position Monitor): `MON->>MON: set halt_flag = True` after daily loss limit hit.  
Section 2 (Container Diagram): `STATE → GATE` arrow label reads `daily P&L / open count / position registry`. `halt_flag` is NOT in this list.  
Section 7 (Risk Gate): Check D1 reads `Daily P&L ≤ -$75 limit?` — this recalculates from raw P&L on every call. It does NOT consult `halt_flag`.  

**Why this is critical:** `halt_flag` is designed to survive a crash and restart. If the bot crashes after hitting the daily loss limit, `state.json` holds `halt_flag=True`. On restart, the Risk Gate checks `daily_pnl <= -75`. But after a restart the `daily_pnl` counter may have reset or been partially loaded. The halt_flag in state.json is the durable record — and it's not being read by the Gate.  

**Fix (two parts):**  
1. Add `halt_flag` to the STATE → GATE data flow in Section 2.  
2. Change Risk Gate D1 to: `halt_flag == True OR daily_pnl <= -$75 limit?`

---

### BUG-C04 — halt_flag Daily Reset Not Documented
**Severity:** 🔴 CRITICAL  
**Location:** `BINGX-CONNECTOR-UML.md` — Sections 5, 7, 8  
**Problem:**  
`halt_flag` is set to `True` when daily loss limit is hit (Section 5). It must be reset to `False` at the daily reset time (00:00 UTC+7 / 17:00 UTC). This reset is entirely absent from the architecture — not in the Position Monitor sequence, not in the main loop, not in the State schema description.  

**Runtime consequence:** Without an explicit reset, `halt_flag=True` persists forever in `state.json`. After a halt day, the bot will refuse all entries the next day (and every day after) unless someone manually edits `state.json`. This is a silent permanent trade block.  

**Fix:** Add a "daily reset" step to Section 5's Position Monitor loop:  
```
At 17:00 UTC:
  state.daily_pnl = 0.0
  state.daily_trades = 0
  state.halt_flag = False    ← THIS IS MISSING
  send_daily_summary()
```

---

### BUG-C05 — Grade Filter in Connector Config Violates Sandbox Boundary
**Severity:** 🟠 HIGH  
**Location:** `BINGX-CONNECTOR-UML.md` — Section 9 (Config Schema)  
**Problem:**  
```yaml
strategy:
  plugin: "four_pillars_v384"
  allowed_grades: ["A"]
```
`allowed_grades` is strategy knowledge (A/B/C grading is defined by the Four Pillars signal logic). This leaks strategy internals into the connector config, violating the sandbox contract explicitly stated in Section 11:  
> "Connector does NOT know about: Grade computation logic"  

Allowing `allowed_grades` at the connector level means swapping the strategy plugin (e.g. to one that uses different grading like 1/2/3 or High/Low) would break the connector config — defeating the point of the plugin interface.  

**Fix:** Remove `allowed_grades` from connector config. Either:  
- Move it to the strategy plugin's own config file
- Replace with a generic connector concept: `min_signal_confidence: 1` (where the plugin maps its own grades to a numeric confidence level) — this keeps the connector grade-agnostic

---

### BUG-C06 — warmup_bars() Declared in Interface, Doesn't Exist in Code
**Severity:** 🟠 HIGH  
**Location:** `BINGX-CONNECTOR-UML.md` — Section 10 (Plugin Interface)  
**Problem:**  
Interface declares:  
```
+warmup_bars() int
```
No such method exists in `signals/four_pillars.py`, `signals/state_machine.py`, `signals/stochastics.py`, or `signals/clouds.py`. The connector needs this to know how many bars to buffer before calling `get_signal()`.  

Without `warmup_bars()`, the connector would start calling `get_signal()` immediately on bar 1 with insufficient data. The current code handles this with NaN guards — `if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i])` — but the MINIMUM warmup is 60 bars (stoch_60 lookback) + 89 bars (ema89 for Cloud 4) = 89 bars minimum before any valid signal can fire.  

If the connector only buffers 200 bars total, and the first 89 are warmup, it has 111 usable bars at startup — fine. But the interface contract claims this method exists when it does not.  

**Fix:** Either:  
- Add `warmup_bars()` to the plugin implementation returning `max(stoch_k4, cloud4_slow)` = `max(60, 89)` = `89`  
- Or remove it from the interface and document the 200-bar buffer as sufficient

---

### BUG-C07 — Klines Endpoint Marked as "Signed" (Should Be Public)
**Severity:** 🟠 HIGH  
**Location:** `BINGX-CONNECTOR-UML.md` — Section 12 (API Reference)  
**Problem:**  
Table entry: `Fetch OHLCV | GET | /openApi/swap/v2/quote/klines | Signed`  
BingX market data endpoints (klines, mark price, contract info) are PUBLIC — no authentication required. Only account and trade endpoints require HMAC signing. Marking klines as Signed means the connector will HMAC sign every 30-second data poll — if the timestamp drifts by more than the BingX allowed window (typically 1000ms), all market data fetches will be rejected with auth errors, not just orders.  

**Verified via research:** The klines endpoint in confirmed code examples from BingX API issues (GitHub BingX-API/BingX-swap-api-doc) does not use `X-BX-APIKEY` or signature.  

**Fix:** Change API reference table:  
- `/openApi/swap/v2/quote/klines` → **Public**  
- `/openApi/swap/v2/quote/price` → **Public**  
- `/openApi/swap/v2/quote/contracts` → **Public** (already correct)  
- All `/user/*` and `/trade/*` endpoints remain → Signed

---

### BUG-C08 — SL Multiplier Mismatch: Backtester Default vs Connector Config
**Severity:** 🔴 CRITICAL  
**Location:** `BINGX-CONNECTOR-UML.md` — Section 9 (Config Schema), cross-ref `engine/backtester_v384.py`  
**Problem:**  
Architecture doc and config schema state `sl_atr_mult: 1.0` (from prior planning session).  
Actual backtester `Backtester384.__init__()`:  
```python
self.sl_mult = p.get("sl_mult", 2.0)   # DEFAULT IS 2.0
```
And `PositionSlot384.__init__()`:  
```python
sl_mult: float = 2.0   # class default also 2.0
```

All backtests that used default parameters ran with `sl_mult=2.0`. If the live connector deploys with `sl_mult=1.0`, the stop will be twice as tight — far more frequent SL hits than backtests suggest. Live P&L will diverge significantly from backtest expectations.  

**This invalidates any backtest comparison for live sizing decisions.**  

**Fix:** Audit every backtest result used for strategy approval. Confirm which `sl_mult` was actually used. The connector config must match exactly. Add `sl_atr_mult: 2.0` to config until confirmed otherwise.

---

## STRATEGY UML FINDINGS

---

### BUG-S01 — Stage 0→1 Transition: "Crosses Below" vs "Less Than"
**Severity:** 🟠 HIGH  
**Location:** `FOUR-PILLARS-STRATEGY-UML.md` — Section 3 (State Machine)  
**Problem:**  
Diagram transition: `stoch_9 crosses BELOW cross_level (25)`  
"Crosses below" implies an explicit crossover — the previous bar was ≥25, current bar is <25. The actual code:  
```python
if self.long_stage == 0:
    if stoch_9 < cross_low:   # NO crossover check
        self.long_stage = 1
```
There is no check that the previous bar was ≥ cross_level. If the bot starts mid-session with stoch_9 already at 18 (below 25), the state machine immediately enters Stage 1 on the first processed bar — without a true momentum impulse cross.  

**Live impact:** Bot startup mid-oversold-trend triggers a Stage 1 setup immediately, potentially firing a signal on the very next bar (if stoch_9 crosses back above 25). This is a false start — not a real momentum cross, just the bot catching up to a mid-move condition.  

**Backtester impact:** Minimal, because warmup bars are burned through before trading starts. But on a live bot with a cold restart, the first bars post-startup are live-traded, not discarded.  

**Fix options:**
1. Document the "less than" behavior accurately — change transition label to `stoch_9 < 25 (no prior crossover enforced)`
2. Or implement a crossover check in the live plugin to discard the first Stage 1 entry if the bot started with stoch_9 already < 25

---

### BUG-S02 — Stage 1 Exit: Same Crossover vs Level Issue
**Severity:** 🟠 HIGH  
**Location:** `FOUR-PILLARS-STRATEGY-UML.md` — Section 3 (State Machine)  
**Problem:**  
Diagram: `stoch_9 crosses BACK ABOVE 25`  
Code in Stage 1:  
```python
elif stoch_9 >= cross_low:   # NO crossover check
    # fire signal
```
The exit trigger is `stoch_9 >= 25` — not a crossover. If stoch_9 enters Stage 1 at exactly 24.9, then the next bar is 25.0, the signal fires. That is effectively a crossover. BUT if a bar gap causes stoch_9 to jump from 19 to 28 in one bar, the signal fires at the first bar ≥ 25 — same behavior. The label "crosses back" is an acceptable approximation because you can only be in Stage 1 if stoch_9 was already < 25 when Stage 1 started.  

**However:** The same gap issue from BUG-S01 applies — if Stage 1 fires immediately on a cold start with stoch_9=22, then on bar 2 if stoch_9=26, a signal fires with only 1 bar of Stage 1 "setup" (zero confirmation window).  

**Fix:** Label transition as `stoch_9 >= 25 (while in Stage 1)` for accuracy.

---

### BUG-S03 — Grade C Condition: "price_pos != 0" is Wrong
**Severity:** 🔴 CRITICAL  
**Location:** `FOUR-PILLARS-STRATEGY-UML.md` — Section 4 (Signal Grading)  
**Problem:**  
Grade C condition documented as:  
```
stoch_14_seen AND allow_c_trades AND price_pos != 0 (outside cloud — strong trend)
```
Actual code:  
```python
# LONG Grade C:
elif self.long_14_seen and self.allow_c and price_pos == 1:
    long_signal_c = True

# SHORT Grade C:
elif self.short_14_seen and self.allow_c and price_pos == -1:
    short_signal_c = True
```

`price_pos != 0` means "either +1 or -1" — the doc implies either direction would pass for any Grade C signal. In reality:  
- LONG Grade C requires `price_pos == +1` (price ABOVE Cloud 3 — momentum long)  
- SHORT Grade C requires `price_pos == -1` (price BELOW Cloud 3 — momentum short)  

A LONG Grade C can NEVER fire with `price_pos == -1`. The `!= 0` in the doc would allow that reading. Anyone implementing from the UML spec would build incorrect logic.  

**Also note:** Grade C bypasses the Cloud 3 direction filter — meaning a Grade A/B LONG requires `price_pos >= 0` (above or inside cloud), but Grade C LONG requires `price_pos == 1` (strictly above cloud). Grade C is actually MORE restrictive on price position than Grade A/B, not less. The note "Bypasses cloud3 direction filter" in the diagram is partially misleading.  

**Fix:** Change Grade C node in Section 4 to:  
- LONG Grade C: `stoch_14_seen AND allow_c AND price_pos == +1`  
- SHORT Grade C: `stoch_14_seen AND allow_c AND price_pos == -1`  
Update note: "Grade C bypasses cloud3_ok (cloud direction flag) but requires price strictly outside cloud"

---

### BUG-S04 — Re-Entry Flow Incorrectly Placed Inside Grading Diagram
**Severity:** 🟠 HIGH  
**Location:** `FOUR-PILLARS-STRATEGY-UML.md` — Section 4 (Signal Grading)  
**Problem:**  
The grading flowchart shows `REENTRY_CHECK` as a node that branches from `GRADE_NONE`, implying re-entry is part of the A/B/C classification flow triggered by Stage 1 exit.  

Actual code: Re-entry is computed ENTIRELY SEPARATELY after the A/B/C logic, driven by:  
1. `bars_since_long / bars_since_short` counters (incremented every bar)  
2. `price_cross_above_cloud2` / `price_cross_below_cloud2` events  
3. `self.reentry_lookback` window check  

Re-entry can fire on a bar where there is NO state machine Stage 1 event at all. It is a parallel path, not a fallback from NONE.  

**Fix:** Remove `REENTRY_CHECK` from Section 4. Add a separate Section 4b showing re-entry as its own independent flowchart:  
```
EVERY BAR (parallel to state machine):
  IF price_cross_above_cloud2
     AND 0 < bars_since_long <= reentry_lookback
     AND no current long_a/b/c on this bar
     → reentry_long = True
```

---

### BUG-S05 — ExitManager Misrepresented as Initial SL/TP Calculator
**Severity:** 🟠 HIGH  
**Location:** `FOUR-PILLARS-STRATEGY-UML.md` — Section 5 (Exit Price Calculation) and Section 7 (Sequence Diagram)  
**Problem:**  
Section 5 diagram shows: `SL_LONG → EXIT_METHODS` and `TP_LONG → EXIT_METHODS`  
Section 7 sequence shows:  
```
PLUGIN->>EXIT: calc sl_price (entry - sl_mult × atr)
EXIT-->>PLUGIN: sl_price
PLUGIN->>EXIT: calc tp_price (entry + tp_mult × atr)
EXIT-->>PLUGIN: tp_price or None
```

`ExitManager.update_stops()` is a BAR-BY-BAR dynamic updater — it does NOT calculate initial SL/TP at entry. The method signature is:  
```python
def update_stops(self, direction, entry_price, current_atr,
                 current_sl, current_tp, mfe_atr, peak_price) → tuple
```
It takes `current_sl` and `current_tp` as inputs — it adjusts them, not creates them. Initial SL/TP is calculated DIRECTLY in `PositionSlot384.__init__()`:  
```python
self.sl = entry_price - (atr * sl_mult)   # no ExitManager call
self.tp = entry_price + (atr * tp_mult)   # no ExitManager call
```

ExitManager only activates AFTER `mfe_atr >= mfe_trigger` (trade already in profit by the trigger amount). It has no role at signal time.  

**Fix (Section 5):** Remove `EXIT_METHODS` from the calculation diagram. Section 5 should show only `entry ± sl_mult × atr` for initial prices. Create a separate Section 5b for the dynamic SL management lifecycle (initial → BE raise → AVWAP trail).  

**Fix (Section 7):** Remove ExitManager from the signal pipeline sequence. The plugin only computes initial SL/TP via ATR math. ExitManager belongs in the backtester/position management layer, not the signal output layer.

---

### BUG-S06 — process_bar() Signature Incomplete in Class Diagram
**Severity:** 🔵 LOW  
**Location:** `FOUR-PILLARS-STRATEGY-UML.md` — Section 6 (Class Diagram)  
**Problem:**  
Class diagram shows:  
```
+process_bar(bar_index, stoch_9, stoch_14, stoch_40, stoch_60, cloud3_bull, price_pos, ...) SignalResult
```
Actual signature has 10 named parameters:  
```python
def process_bar(self, bar_index, stoch_9, stoch_14, stoch_40, stoch_60,
                stoch_60_d, cloud3_bull, price_pos,
                price_cross_above_cloud2, price_cross_below_cloud2)
```
`stoch_60_d`, `price_cross_above_cloud2`, `price_cross_below_cloud2` are omitted from the diagram. `cloud3_bull` is listed in the diagram but is passed to the state machine even though it's not actually used inside `process_bar()` — the code computes `cloud3_ok_long = price_pos >= 0` from `price_pos` directly. `cloud3_bull` parameter is accepted but not used in the main logic.  

**Fix:** Update class diagram to show all 10 parameters accurately.

---

### BUG-S07 — FourPillarsPlugin Class Does Not Exist in Current Codebase
**Severity:** 🟡 MEDIUM  
**Location:** `FOUR-PILLARS-STRATEGY-UML.md` — Sections 6, 7, 8, 9  
**Problem:**  
The entire `FourPillarsPlugin` class, `plugins/` directory, and `get_signal()` method are documented as current architecture. They do NOT exist. The backtester currently calls `compute_signals()` directly — there is no plugin wrapper, no `StrategyPlugin` interface, no `Signal` dataclass.  

The UML shows this as existing infrastructure. Anyone reading it to implement the connector would expect these files to be present on Jacky.  

**Fix:** Add a clear label to Sections 6 and 7:  
> **NOTE: FourPillarsPlugin is the TARGET interface. It does not yet exist. Must be built as part of connector pre-work before deployment.**

Also add to the Section 9 variants table: a "current state" column showing which variants exist vs which are planned.

---

### BUG-S08 — Multi-Slot Backtester vs Single-Slot Connector: Undocumented Divergence
**Severity:** 🔴 CRITICAL  
**Location:** Both UML docs — nowhere mentioned  
**Problem:**  
`Backtester384` supports up to 4 concurrent position slots per symbol including:  
- Up to 4 simultaneous positions in the same direction  
- ADD signals (AVWAP pullback adds to existing position)  
- RE-entry signals (limit order after SL exit)  
- Scale-out exits (partial close at AVWAP +2σ)  

The connector architecture enforces:  
- 1 position per symbol+direction (duplicate position check in Risk Gate)  
- No ADD logic (not in Signal object or executor)  
- No scale-out logic (single SL+TP order at entry)  
- `max_positions: 3` total across all coins  

**The practical consequence:** Backtest P&L figures are generated with multi-slot behavior. Live trading will use single-slot behavior. These are NOT directly comparable. A backtest showing `$55K profit on RIVER` at the $5K notional level assumes multiple concurrent slots, adds, and scale-outs. The live single-slot version will have materially different P&L characteristics — likely lower profit but also different drawdown profile.  

This means: **the backtest approval criteria (expectancy > $1/trade) must be re-run with single-slot constraints** (`max_positions=1, enable_adds=False, enable_reentry=False`) to get a comparable baseline.  

**Fix:** Add a section to BOTH UML docs titled "Backtester vs Live Execution Differences" listing these constraints explicitly, and mark the backtest re-run as a prerequisite gate before live deployment.

---

## SUMMARY TABLE

| ID | Severity | File | Section | Issue |
|----|----------|------|---------|-------|
| BUG-C01 | 🟡 MEDIUM | `BINGX-CONNECTOR-UML.md` | Section 1 | Signal uses BUY/SELL/HOLD, should be LONG/SHORT/NONE |
| BUG-C02 | 🟡 MEDIUM | `BINGX-CONNECTOR-UML.md` | Section 4 | Mark price fetch uses wrong API participant (BINGX_K vs /quote/price) |
| BUG-C03 | 🔴 CRITICAL | `BINGX-CONNECTOR-UML.md` | Sections 2, 5 | halt_flag missing from STATE→GATE data flow |
| BUG-C04 | 🔴 CRITICAL | `BINGX-CONNECTOR-UML.md` | Sections 5, 7, 8 | halt_flag daily reset not documented — permanent silent trade block |
| BUG-C05 | 🟠 HIGH | `BINGX-CONNECTOR-UML.md` | Section 9 | allowed_grades in connector config violates sandbox boundary |
| BUG-C06 | 🟠 HIGH | `BINGX-CONNECTOR-UML.md` | Section 10 | warmup_bars() declared in interface but not implemented anywhere |
| BUG-C07 | 🟠 HIGH | `BINGX-CONNECTOR-UML.md` | Section 12 | Klines endpoint marked Signed — should be Public |
| BUG-C08 | 🔴 CRITICAL | `BINGX-CONNECTOR-UML.md` | Section 9 | sl_atr_mult=1.0 in config, backtester default is 2.0 — invalidates all backtest comparisons |
| BUG-S01 | 🟠 HIGH | `FOUR-PILLARS-STRATEGY-UML.md` | Section 3 | "Crosses below" label — code uses `< 25`, no crossover check — live cold-start risk |
| BUG-S02 | 🟠 HIGH | `FOUR-PILLARS-STRATEGY-UML.md` | Section 3 | "Crosses back above" label — code uses `>= 25`, same issue |
| BUG-S03 | 🔴 CRITICAL | `FOUR-PILLARS-STRATEGY-UML.md` | Section 4 | Grade C condition is `price_pos != 0` in doc, code requires `== +1` (LONG) or `== -1` (SHORT) |
| BUG-S04 | 🟠 HIGH | `FOUR-PILLARS-STRATEGY-UML.md` | Section 4 | Re-entry shown inside grading flow — it is a separate independent pipeline |
| BUG-S05 | 🟠 HIGH | `FOUR-PILLARS-STRATEGY-UML.md` | Sections 5, 7 | ExitManager shown as initial SL/TP calculator — it is a bar-by-bar dynamic updater only |
| BUG-S06 | 🔵 LOW | `FOUR-PILLARS-STRATEGY-UML.md` | Section 6 | process_bar() signature missing 3 parameters (stoch_60_d, cross_above, cross_below) |
| BUG-S07 | 🟡 MEDIUM | `FOUR-PILLARS-STRATEGY-UML.md` | Sections 6-9 | FourPillarsPlugin class does not exist — marked as current, is future |
| BUG-S08 | 🔴 CRITICAL | Both docs | Not mentioned | Multi-slot backtester vs single-slot live — backtest P&L figures not valid for live comparison |

---

## CRITICAL PATH — Fix Order Before Any Code

1. **BUG-C08 first** — confirm sl_atr_mult used in the profitable backtest results. If it was 2.0, all the sweep analysis is at risk. This must be resolved before strategy parameter locking.

2. **BUG-S08 second** — re-run backtest with `max_positions=1, enable_adds=False, enable_reentry=False` on RIVER and any other target coins. This gives the actual live-comparable expectancy figure.

3. **BUG-S03** — correct Grade C condition in strategy UML before plugin implementation.

4. **BUG-C03 + BUG-C04** — halt_flag flow must be in the architecture before connector code is written.

5. All remaining bugs are documentation corrections or interface additions that can be addressed during implementation.

---

*Tags: #review #bugs #architecture #uml #bingx-connector #four-pillars #2026-02-20*

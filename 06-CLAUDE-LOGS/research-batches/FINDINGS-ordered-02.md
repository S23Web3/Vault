# Research Batch 02 — Findings
Files: 2026-02-04 through 2026-02-11

---

## 2026-02-04.md
**Date:** 2026-02-04
**Type:** Build session (daily journal, multiple sessions)

### What happened
Eight sessions logged across the day covering Pine Script indicator fixes, strategy specification, and new indicator builds.

Session 1: Quad Rotation FAST v1.3 philosophy correction. v4.3 patch. Selected FAST v1.4 as production version. Copied to `Quad-Rotation-Stochastic-FAST.pine`.

Session 2: Indicator review against PineScript skill standards. AVWAP alert edge-triggering fix (`and not condition[1]`). QRS 40-4 smoothing changed from 4 to 3 (Kurisko original). BBWP v2 MA cross persistence fixed with timeout (10 bars default) + timestamp display.

Session 3: Critical conflict found — v1.0 Four Pillars strategy spec referenced "Stoch 55" which does not exist in any built indicator. Created `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` with correct stochastic settings (9-3, 14-3, 40-4, 60-10). Deprecated `FOUR-PILLARS-COMBINED-BUILD-SPEC.md`.

Session 4: Added 15 hidden integration plots to `ripster_ema_clouds_v6.pine` — cloud states, price position, cloud direction, crossovers, scores, raw EMAs.

Session 5: Built `four_pillars_v2.pine` (~500 lines) — self-contained indicator with all 4 pillars, A/B/C grade calculation, position management, dashboard, 11 alert conditions, webhook JSON, 10 hidden plots.

Session 6: Complete rewrite `four_pillars_v3.pine` v3.1 — 9-3 as TRIGGER, all other stochastics (14-3, 40-3, 60-10) must be in zone (<30 or >70), 3-bar lookback, raw K stochastic calc fix, toggleable filters.

Session 7: v3.2 — changed filter from 40-3 K/D comparison to 40-3 D line position (D > 20 for long, D < 80 for short).

Session 8: v3.3 — changed from 40-3 D filter to 60-10 D filter with fixed 20/80 thresholds (not tied to zone level input).

### Decisions recorded
- FAST indicator should NOT filter by trend — outputs rotation state only; integration layer decides.
- 40-4 as SUPERSIGNAL (highest priority) — divergence detection on 40-4 only, NOT on 9-3.
- Stochastic hierarchy: 9-3/14-3 trigger → 40-4 divergence → 60-10 filter.
- Stoch 55 was an error from pre-HPS conception — removed from spec entirely.
- TDI reference removed.
- 34/50 cloud is PRIMARY for trend bias.

### State changes
- `Quad-Rotation-Stochastic-FAST.pine`: Fixed 40-4 smoothing
- `Quad-Rotation-Stochastic-v4-CORRECTED.pine`: Fixed 40-4 smoothing, added hidden plot
- `avwap_anchor_assistant_v1.pine`: Edge-triggered VSA alerts
- `bbwp_v2.pine`: MA cross timeout + timestamp + hidden plots
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md`: NEW — corrected strategy spec
- `FOUR-PILLARS-COMBINED-BUILD-SPEC.md`: Deprecated
- `ripster_ema_clouds_v6.pine`: NEW — 15 integration hidden plots
- `four_pillars_v2.pine`: NEW — complete combined indicator
- `four_pillars_v3.pine`: v3.3 — 60-10 D filter with fixed 20/80

### Open items recorded
- Create strategy version of v3 for backtesting
- Add trailing stop logic
- Test all indicators in TradingView
- Set up n8n webhook integration

### Notes
Root cause of "Stoch 55" error: session from 2026-01-29 conceptualized strategy before John Kurisko HPS methodology was researched. The spec was not updated when indicators were built correctly.

---

## 2026-02-04-four-pillars-strategy-specification.md
**Date:** 2026-02-04
**Type:** Strategy spec / session log

### What happened
Extended session documenting the Four Pillars v2.0 strategy specification. Resolved all conflicts from v1.0 spec. Identified that "Stoch 55 K/D cross" as primary trigger was wrong — replaced with 40-4 divergence as SUPERSIGNAL. Exit management changed from "Stoch 55 momentum" to "9-3 reaches opposite zone."

Defined entry rules (all 4 pillars aligned + 9-3/14-3 trigger OR SUPERSIGNAL + RVol >= NORMAL), exit rules (Initial SL 2x 1m ATR, trail activation at 2x 5m ATR, trail callback 2x 5m ATR, exchange manages trailing), and signal grades (A: 4/4 + SUPERSIGNAL + squeeze; B: 4/4; C: 3/4; D: NO TRADE).

All 6 indicators verified as built: ripster_ema_clouds_v6.pine, avwap_anchor_assistant_v1.pine, bbwp_v2.pine, Quad-Rotation-Stochastic-v4-CORRECTED.pine, Quad-Rotation-Stochastic-FAST-v1.4.pine, atr_position_manager_v1.pine, four_pillars_v2.pine.

Defined position management flow: TV Signal → n8n validates (3-candle ATR check) → Exchange places order with trailing → Set and forget.

### Decisions recorded
- 60-10 is MACRO FILTER only — NOT leading.
- 9-3 and 14-3 are LEADING triggers.
- Divergence detection on 40-4 only (Stage-based).
- Stochastic hierarchy: 9-3/14-3 trigger → 40-4 divergence → 60-10 filter.

### State changes
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` created (corrected spec document).

### Open items recorded
- Start fresh chat for combined indicator build.
- Build Pine Script that integrates all 4 indicators.
- Add dashboard table.
- Add alerts with JSON payload.

### Notes
TradingView Pine Logs shortcut: `Ctrl + J`. Token usage noted as high due to extensive past chat searches.

---

## 2026-02-04-indicator-review-session.md
**Date:** 2026-02-04
**Type:** Build session / review session

### What happened
Continued session reviewing built indicators against PineScript skill standards.

AVWAP Anchor Assistant: VSA alerts were not edge-triggered (could fire on multiple consecutive bars). Fixed lines 668-682 with `and not condition[1]` pattern for all 5 VSA alert types. All 8 validation checklist items confirmed passing.

QRS Indicators (earlier session): Fixed missing hidden plot for stoch_40_4 in v4-CORRECTED. Fixed 40-4 smoothing from 4 to 3 (Kurisko original: K=40, Smooth=3).

BBWP v2: Three issues fixed — (1) MA cross state persisted indefinitely, fixed with timeout input `i_maCrossTimeout` (default 10 bars); (2) No timestamp for when MA cross occurred, fixed with `str.format("{0,time,HH:mm}", maCrossTime)` display in table row 4; (3) Missing persistent state hidden plots, added `ma_cross_up_state` and `ma_cross_down_state` plots. Auto-end conditions: spectrum enters blue zone (BBWP < 25), enters red zone (BBWP > 75), or timeout reached.

Four Pillars Strategy v2.0 Specification: MAJOR conflict found in v1.0 — "Stoch 55 K/D cross" was wrong. Source traced to 2026-01-29 logs (pre-HPS methodology). Created `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` with correct settings.

Ripster EMA Clouds: 15 hidden integration plots added.

Four Pillars v2: Complete combined indicator built with all 4 pillars, grade calculation (A/B/C/No Trade), position management, dashboard, stochastic mini panel, 11 alerts, webhook JSON, 10 hidden plots.

### Decisions recorded
- MA cross auto-end conditions: spectrum hits blue/red OR timeout reached.
- v1.0 spec deprecated.

### State changes
- `avwap_anchor_assistant_v1.pine`: Edge-triggered VSA alerts
- `bbwp_v2.pine`: MA cross timeout + timestamp + hidden plots
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md`: NEW
- `FOUR-PILLARS-COMBINED-BUILD-SPEC.md`: Deprecation notice added
- `ripster_ema_clouds_v6.pine`: 15 integration hidden plots added
- `four_pillars_v2.pine`: NEW complete combined indicator

### Open items recorded
None explicitly stated.

### Notes
None.

---

## 2026-02-04-quad-rotation-fast-v1.3-build.md
**Date:** 2026-02-04
**Type:** Build session

### What happened
Critical review of Quad Rotation Stochastic indicators against John Kurisko HPS methodology. Identified philosophy issues in FAST v1.2 spec.

v1.2 to v1.3 changes: Removed built-in trend filter; Channel (60-10) changed from mandatory filter to context output only; Counter-trend exit removed; Signal hierarchy reduced from 4 tiers to 3 tiers (rotation quality); Added near zone (30/70) in addition to strict zone (20/80); Changed 14-3 confirmation from 2-bar momentum to 1-bar direction; Added 5-bar signal cooldown.

Selected FAST v1.4 as final — has all v1.3 features plus 9-3 divergence detection, DIV+ROTATION combo signal, info table, price chart triangles (force_overlay), divergence lines, signal candle coloring, 60-10 flat case handling.

Patched `Quad-Rotation-Stochastic-v4-CORRECTED.pine` from v4.2 to v4.3 — added signal candle coloring, price chart triangles (force_overlay=true), context outputs for integration: channel_numeric (60-10 state), mid_numeric (40-4 state), bars_since_bull_div, bars_since_bear_div, div_active, slow_confirm.

JSON schema defined with numeric encodings for channel_numeric (-3 to +3), mid_numeric (-1/+1), zone_numeric (-2 to +2), div_active (-1/0/+1).

### Decisions recorded
- FAST indicator should NOT filter by trend — outputs rotation state only.
- Integration layer (n8n/Dashboard) decides based on ALL pillars.
- FAST v1.4 selected as production version.

### State changes
- `Quad-Rotation-Stochastic-FAST-v1.3-BUILD-SPEC.md`: NEW — updated spec with philosophy corrections
- `Quad-Rotation-Stochastic-v4-CORRECTED.pine`: Patched to v4.3 with integration context outputs
- `Quad-Rotation-Stochastic-FAST-v1.3.pine`: Reviewed, no changes needed
- `Quad-Rotation-Stochastic-FAST-v1.4.pine`: Reviewed, selected as final

### Open items recorded
- Copy FAST v1.4 to `Quad-Rotation-Stochastic-FAST.pine` (production)
- Test v4.3 in TradingView — compile, visual check
- Test FAST v1.4 in TradingView — compile, visual check
- Verify JSON outputs with test alerts
- Set up n8n webhook integration

### Notes
None.

---

## 2026-02-05.md
**Date:** 2026-02-05
**Type:** Build session (daily journal, multiple sessions)

### What happened
Eleven sessions logged across the day covering strategy toggles, SL system overhaul, stochastic smoothing fix, strategy backtesting version rebuild, exit bug fixes, and AVWAP trailing.

Session 1: Reviewed and validated v3.4.1 strategy. Found toggle gap — strategy has `i_useTP`, indicator does not. Session hit context limit.

Session 2: Added `i_useTP` toggle and `i_useRaisingSL` toggle to indicator. Changed Phase 3 trail from Cloud 3 to Cloud 4. Bumped to v3.4.2.

Session 3: Major SL overhaul — removed entire phased P0→P1→P2→P3 SL system, replaced with continuous Cloud 3 (34/50) ± 1 ATR trail every candle. Added Cloud 2 re-entry A trade (price crosses Cloud 2 + recent A rotation within lookback bars). Removed Cloud 2 flip hard close exit. File reduced from 645 to ~495 lines.

Session 3b: Added trail activation gate (Cloud 3/4 cross: ema50 > ema72 for LONG). SL starts static at entry ± 2 ATR; trail only activates after gate. Position replacement logic added (new entry replaces existing position when price beyond Cloud 3). Entry priority reordered. Fixed inverse SL bug (trail pushing SL above entry price on bar 2 when entering LONG below Cloud 3).

Session 4: v3.5 — discovered stochastic smoothing was missing in all 4 stochastics (raw K, no SMA). Applied smoothing: 9-3, 14-3, 40-3 each use ta.sma(k_raw, 3); 60-10 uses ta.sma(ta.sma(k_raw,10),10) double smooth. Created new file `four_pillars_v3_5.pine` preserving v3.4.2.

Session 5: Complete rewrite of strategy as `four_pillars_v3_5_strategy.pine`. Changed pyramiding from 10 to 1; implemented all v3.5 changes in strategy. Old problems: 32 of 54 exits were margin calls (pyramiding=10 + 100% equity), Cloud 2 exits cutting winners, raw stochastics causing 170 trades in 7 days.

Session 6: Fixed 3 bugs in v3.5 strategy — (1) dual exit conflict (strategy.exit + strategy.close_all racing), (2) position replacement invisible (fixed entry detection to use entryBar == bar_index), (3) state desync after exit (added strategy.position_size == 0 sync).

Session 7: Removed position replacement entirely — found it was closing winning trades and creating fragmented margin-call micro-trades. Changed canEnterLong/Short to `not inPosition` only. Renamed exit IDs to "Exit Long"/"Exit Short".

Session 8: v3.5.1 root cause fix — user's external stochastic indicators show "Stoch 9 1 3" meaning K smoothing = 1 (raw K, no SMA). The v3.5 "smoothing fix" had made strategy K values equivalent to the D line, not the K line. Reverted all stochastics to raw K. Fixed position sizing from 100% equity to $500 fixed per trade. Changed B/C defaults from ON to OFF. Added A trade flip capability (close opposite + enter new).

Sessions 9-10: v3.6 — designed new AVWAP trailing stop system. A trade SL changed from Cloud 3 ± ATR to AVWAP ± max(stdev, ATR) ratchet. Separate "Long BC"/"Short BC" order IDs. BC exit conditions: SL + Cloud 2 cross + 60-10 K/D cross in extreme zone. BC entry filter: Cloud 3/4 parallel (both slopes same direction). AVWAP anchored to A trade signal bar. AVWAP recovery re-entry (V-shape dip rebuy). State sync loop checking entry IDs.

Session 11: Built v3.6 indicator. Added Volume Flip Filter (toggle `i_useFlipVol`, lookback 20 bars, volume must exceed both rolling avg and avg-since-entry). Fixed dashboard table.new() scope issue (moved from barstate.islast block to global scope).

### Decisions recorded
- Phased SL system (P0→P1→P2→P3) removed — replaced with continuous Cloud 3 trail.
- Cloud 2 exit removed — trail handles protection.
- Position replacement removed — was killing winners and creating margin-call fragments.
- Raw K stochastics confirmed as correct (smooth=1) — SMA on K was wrong.
- B/C defaults changed to OFF.
- A trades can flip direction; B/C/re-entry can only enter from flat.
- AVWAP in v3.6 anchored to A trade entry bar (not session or swing-based).

### State changes
- `four_pillars_v3_4.pine`: v3.4.2 — trail activation gate, position replacement, inverse SL fix
- `four_pillars_v3_5.pine`: v3.5.1 — stochastic smoothing revert to raw K
- `four_pillars_v3_5_strategy.pine`: v3.5.1 — strategy version preserved as reference
- `four_pillars_v3_6_strategy.pine`: NEW — v3.6 AVWAP + A/BC + volume flip filter
- `four_pillars_v3_6.pine`: NEW — v3.6 indicator version
- `06-CLAUDE-LOGS/2026-02-05-strategy-analysis-session.md`: NEW — session 1 log

### Open items recorded
None explicitly listed at end.

### Notes
The v3.5 "stochastic smoothing fix" was actually a regression — it applied SMA to K making it equivalent to the D line, opposite of what was needed. Raw K (smooth=1) confirmed as correct. This is a critical lesson.

---

## 2026-02-05-strategy-analysis-session.md
**Date:** 2026-02-05
**Type:** Session log (context limit reached)

### What happened
Session maxed out (context limit reached) after reviewing and validating the Four Pillars v3.4.1 strategy backtesting version. Confirmed all logic matches indicator version. Strategy already had `i_useTP` toggle. Toggle gap identified: indicator version is missing `i_useTP` and `i_useRaisingSL`.

Strategy config at time of review: $10,000 initial capital, 100% equity position size, 0.1% commission, pyramiding=10, order processing on close.

Session cut short before implementation.

### Decisions recorded
None made (session ended at analysis stage).

### Open items recorded
- Add `i_useTP` toggle to indicator `four_pillars_v3_4.pine`
- Add `i_useRaisingSL` toggle to indicator
- Keep both indicator and strategy files in sync

### Notes
None.

---

## 2026-02-06.md
**Date:** 2026-02-06
**Type:** Build session (daily journal)

### What happened
Two sessions: v3.7 rebate farming architecture build, then emergency v3.7.1 commission fix.

Session 1: Built `four_pillars_v3_7_strategy.pine` — "rebate farming" architecture for ~3000 trades/month. SL changed to 1.0 ATR static, TP 1.5 ATR static (both tight). B/C behavior changed to open fresh positions and flip direction. Volume flip filter removed (free flips). Cloud 2 re-entry tracks bars since ANY signal (not just A). Order IDs simplified back to single ID (v3.5 simplicity). Pyramiding=1. Commission set to percent 0.06% (BUG).

Session 2: Critical bug discovered — `commission.percent=0.06` applies to CASH qty ($500), not notional ($10k with 20x leverage). TV showed $0.30/side but real cost was $6.00/side. Additionally found phantom trade bug: `strategy.close_all()` + `strategy.entry()` on same bar creates 2 trades per flip instead of 1.

Emergency fix `four_pillars_v3_7_1_strategy.pine`: Commission changed to `cash_per_order=6` (deterministic). Flipping changed to `strategy.entry()` only (auto-reverses from short). Added `strategy.cancel()` before every flip. Added 3-bar cooldown minimum between entries (`cooldownOK` on ALL entry paths). Added running Comm$ total to dashboard.

Also created `four_pillars_v3_7_1.pine` (indicator version).

Exported backtest CSV: `07-TEMPLATES/4Pv3.4.1-S_BYBIT_MEMEUSDT.P_2026-02-06_fcc84.csv`.

### Decisions recorded
- Commission must use `cash_per_order` not `commission.percent` for leveraged strategies — ALWAYS.
- Never use `strategy.close_all()` for flips — causes phantom double-commission trades.
- Use `strategy.entry()` for flips — auto-reverses, one commission.
- `strategy.cancel()` stale exits before every flip.
- Cooldown applied to ALL entry paths, not just some.

### State changes
- `four_pillars_v3_7_strategy.pine`: NEW — rebate farming architecture
- `four_pillars_v3_7_1_strategy.pine`: NEW — commission fix + cooldown
- `four_pillars_v3_7_1.pine`: NEW — indicator version

### Open items recorded
- Build Python backtester to validate v3.7.1 with correct commission
- Test breakeven+$X raise on historical data
- Fetch historical data for multiple coins

### Notes
This session established the critical commission math lesson: `commission.percent` in TradingView applies to cash qty, not notional. With 20x leverage, this creates a 20x underestimate of actual commission cost.

---

## 2026-02-07.md
**Date:** 2026-02-07
**Type:** Build session (daily journal, multiple sessions)

### What happened
Six sessions: master plan creation, WS1+WS2 docs, Python backtester build, backtest results, sub-$1B coin discovery, CUDA installation.

Session 1: Created master execution plan `warm-waddling-wren.md` defining 5 workstreams (WS1-WS5) — Pine Script Skill Optimization, Progress Review Documents, Data Pipeline + Signal Engine + Backtest Engine + Exit Strategies + Streamlit Dashboard, ML Parameter Optimizer, v4 + Monte Carlo Validation.

Session 2: Completed WS1 (updated all Pine Script skill files — commission fix, phantom trade, cooldown, Ripster Cloud numbering, stoch_k raw K function, lessons-learned.md). Completed WS2 (wrote `2026-02-07-progress-review.md` and `commission-rebate-analysis.md`).

Session 3: Built complete Python backtester in `PROJECTS/four-pillars-backtester/`. Data pipeline (WS3A): `data/fetcher.py` with BybitFetcher (primary) + WEEXFetcher (live only). Discovered WEEX API has no historical pagination — switched to Bybit v5 API. Bybit returns newest-first, implemented backward pagination. Signal engine (WS3B): `signals/stochastics.py` (raw K smooth=1), `signals/clouds.py` (Ripster EMA clouds 5/12, 34/50, 72/89), `signals/state_machine.py` (A/B/C grading + cooldown), `signals/four_pillars.py` (orchestrator). Backtest engine (WS3C): `engine/backtester.py` (bar-by-bar with MFE/MAE), `engine/position.py` (BE raise), `engine/commission.py` ($6/side + daily 5pm UTC rebate), `engine/metrics.py`.

Bug fixed: `df.set_index('datetime')` removes datetime from columns → rebate settlement never triggered. Fixed by checking `df.index.name`.

Session 4: 1-minute results on 5 coins — mostly negative (only RIVER profitable at +$87,510). 5-minute results on 5 coins — ALL PROFITABLE ($97,060 total). Key discovery: 5m timeframe makes all coins profitable. Commission bleed on 1m (~20K trades) overwhelms edge.

Session 5: Built `scripts/fetch_sub_1b.py` — uses CoinGecko for market cap filtering, Bybit v5 for candle data. Discovered 394 coins with <$1B market cap on Bybit. Saved to `data/sub_1b_coins.json`. Kicked off overnight fetch for all 394 coins.

Session 6: Installed NVIDIA CUDA 13.1 Toolkit. All components verified. GPU: RTX 3060, 12GB VRAM, driver 591.74. PyTorch, optuna, xgboost not yet installed.

### Decisions recorded
- 5-minute timeframe is optimal — fewer trades, less commission bleed.
- RIVER dominates ($13.95/trade on 5m) due to high ATR/price ratio.
- Breakeven raise is critical — LSG 59-84% means most losers were profitable at some point.
- BTC/ETH/SOL too expensive — commission is 46% of BTC TP win.
- WEEXFetcher only for live data, BybitFetcher is primary for historical.

### State changes
- `.claude/plans/warm-waddling-wren.md`: NEW — master execution plan
- `.claude/skills/pinescript/SKILL.md`: Updated
- `07-BUILD-JOURNAL/2026-02-07-progress-review.md`: NEW
- `07-BUILD-JOURNAL/commission-rebate-analysis.md`: NEW
- `PROJECTS/four-pillars-backtester/` entire tree: NEW — complete backtester
- `data/cache/*.parquet` (5 coins): NEW — 3-month 1m data
- `data/sub_1b_coins.json`: NEW — 394 coin list
- `scripts/fetch_sub_1b.py`: NEW — sub-$1B fetcher

### Open items recorded
- Wait for overnight fetch to complete (~02:00)
- Install PyTorch with CUDA (user task)
- Run 299-coin backtest on 5m
- Build v3.8 ATR-based BE module

### Notes
This session established the core performance findings: 5m > 1m for all coins, LSG 68-84%, commission rate matters ($12 RT is significant). WEEX confirmed to have no historical pagination API.

---

## 2026-02-07-backtest-results.md
**Date:** 2026-02-07
**Type:** Session log / backtest results

### What happened
Detailed record of Python backtester results for 5 low-price coins on both 1m and 5m timeframes.

Backtester configuration: $10,000 equity, $500 margin per trade, 20x leverage, $10,000 notional, SL 1.0 ATR, TP 1.5 ATR, cooldown 3 bars, B/C open fresh, $6/side commission, 70% rebate ($3.60/RT net).

1m results (3 months): 4 of 5 coins negative. Only RIVER profitable (+$87,510). Total 99,333 trades, total -$11,012.

5m results (3 months): ALL 5 coins profitable. Total 20,283 trades, total +$97,060 (+$4.79/trade). LSG ranges 77.4% to 84.2%.

Key findings: 5m is optimal timeframe, RIVER dominates ($13.95/trade), breakeven raise is critical (LSG 59-84%), BTC/ETH/SOL too expensive (commission = 46% of BTC TP win).

Bugs fixed: (1) rebate settlement bug from df.set_index, (2) WEEX no historical pagination, (3) Bybit newest-first pagination.

### Decisions recorded
None explicitly stated beyond findings.

### Open items recorded
- Build v3.8 ATR-based BE logic
- Commission rate verification ($4/side vs $6/side)
- Install PyTorch with CUDA
- Monte Carlo validation on 5m results
- Streamlit dashboard integration

### Notes
LSG (Losers Saw Green) = percentage of losing trades that were profitable at some point. Range confirmed as 59-84% across 5 coins on 5m. This is the primary optimization target.

---

## 2026-02-07-progress-review.md
**Date:** 2026-02-07
**Type:** Progress review document

### What happened
Comprehensive version evolution table from v3.4.1 through v3.7.1 documenting what each version solved and broke.

v3.5: Stochastic smoothing bug — applied SMA to K line, delayed signals by 2-3 bars. Never use SMA-smoothed K for entry detection.
v3.5.1: Cloud 3/4 trail — trail fails in chop-heavy crypto markets; activation delay exposes position before trail kicks in.
v3.6: AVWAP trail — stdev=0 bug on bar 1 causes near-zero SL. AVWAP better for swing trades, not 1m scalping.
v3.7: Commission blow-up — commission.percent applies to cash qty not notional, plus phantom trade bug from close_all + entry.
v3.7.1: Current working version — $1.81/trade expectancy before rebates.

Market context documented: Nov 11 (BTC favorable), Dec 15 (sharp dump), Jan 15+ (bearish grind), Feb 4 (another sharp dump). These are validation checkpoints.

Core finding: 86% of losing trades saw unrealized profit before dying. Exit timing is the bottleneck.

### Decisions recorded
- Breakeven+$X raise is primary optimization target for v4.
- Raw K must be used — SMA-smoothed K is wrong for this system.

### State changes
- `07-BUILD-JOURNAL/2026-02-07-progress-review.md`: NEW document

### Open items recorded
- Build Python backtester (WS3)
- Test BE+$X raise at different thresholds
- ML optimizer for regime-specific parameters (WS4)
- Build v4, validate with Monte Carlo (WS5)

### Notes
This document references "86% LSG" but the backtester results file shows 59-84% by coin. The "86%" may be a rounded or averaged figure across a different dataset or time period.

---

## 2026-02-08.md
**Date:** 2026-02-08
**Type:** Session log / overnight fetch results

### What happened
Overnight data fetch completed: started 2026-02-07 19:53, completed 2026-02-08 02:18 (~6.5 hours).

Results: 394 total coins, 363 fetched, 31 failed (rate limited), 299 full data (>3MB, 3 months), 70 partial/tiny, 38.5 million candles, 1.36 GB on disk. All 299 complete coins passed validation — zero gaps, zero NaN, zero dupes, zero bad prices.

Known issues: RIVER + SAND got overwritten by short fetches during sub-$1B run. Rate limit burst at ~20:39 caused 31 failures. 70 partial fetches need re-fetching.

Created comprehensive handoff document `07-BUILD-JOURNAL/2026-02-09-session-handoff.md`.

Completed status: WS1-WS3C done, CUDA 13.1 installed.
Blocked/Pending: PyTorch install (user task), refetch 101 coins, RIVER+SAND re-fetch, v3.8 ATR-based BE, 299-coin backtest, WS3D-WS5.

### Decisions recorded
None explicitly stated.

### State changes
- `data/cache/*.parquet`: 369 Parquet files from overnight fetch
- `data/fetch_log.txt`: Fetch log (2,479 lines)
- `data/refetch_list.json`: 101 coins to re-fetch
- `07-BUILD-JOURNAL/2026-02-09-session-handoff.md`: NEW — session handoff

### Open items recorded
- PyTorch install: `python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130`
- Add `--refetch` flag to fetch_sub_1b.py
- Improve rate limit handling (30-60s backoff between consecutive coin failures)
- Re-fetch RIVER + SAND

### Notes
The handoff document saved to `07-BUILD-JOURNAL/` but was dated as `2026-02-09-session-handoff.md` while being created on 2026-02-08.

---

## 2026-02-09.md
**Date:** 2026-02-09
**Type:** Build session (daily journal)

### What happened
Book analysis of 9 books, VINCE upgrade plan synthesized, Andy project created, tools installed, data re-fetched, PyTorch CUDA installed.

9 books scored — top ratings: Maximum Adverse Excursion (Sweeney, 9/10), Advances in Financial ML (De Prado, 9/10), ML for Algorithmic Trading (Jansen, 8/10).

VINCE upgrade plan from books:
1. ATR regime gate — when ATR × leverage > threshold, stop-outs are random not signal failures. Add atr_regime feature for XGBoost.
2. Drawdown constraint in Optuna objective — kill trial if max_drawdown > 10%.
3. Non-normal return awareness — use Sortino not Sharpe, modified Kelly, Monte Carlo shuffling.
4. Data augmentation — add Gaussian noise to candles, bootstrap confidence intervals.
5. Pre-entry XGBoost features — 11 features to predict if trade will win before entry.
6. Options flow regime filter — IV rank, put-call skew as XGBoost features.

What's NOT worth doing: RNN for price prediction, DQL trading agent, options pricing models.

Andy project: Separate skill created for FTMO prop trading ($200K, cTrader), ANDY-1 through ANDY-9 execution plan.

PyTorch CUDA installed: `torch-2.10.0+cu130` verified on RTX 3060 12GB (CUDA 13.0, cuDNN 9.12.0).

Data refetch complete: 99 coins re-fetched, 0 failures. Cache now 399 files / 1.74 GB. RIVER + SAND restored.

pymupdf4llm installed.

### Decisions recorded
- VINCE = ML assistant (learns daily). VICKY = Rebate farming (future, separate).
- Commission: 0.08% of notional (changed from fixed dollar amounts — see Note below).
- Daily training: 17:05 UTC automated.
- XGBoost sufficient for 100K trades; PyTorch later for 1M+ trades.
- Sortino ratio preferred over Sharpe for non-normal returns.

### State changes
- `.claude/skills/andy/andy.md`: NEW — Andy project skill
- All project skills updated (four-pillars-project, vince-ml, andy)
- PyTorch `torch-2.10.0+cu130` installed
- Cache: 399 files / 1.74 GB
- pymupdf4llm installed

### Open items recorded
- Full 399-coin backtest on 5m
- WS4 ML optimizer
- WS4B MFE/MAE depth analysis
- De Prado concepts to implement: Meta-Labeling, Purged CV, Triple Barrier comparison

### Notes
MEMORY.md records commission as 0.08% (0.0008) of notional = $8/side. This file mentions "0.08% of notional" as a decision. Earlier logs used $6/side (0.06%). The commission rate was updated at this point.

---

## 2026-02-09-session-handoff.md
**Date:** 2026-02-09 (created 2026-02-08)
**Type:** Session handoff document

### What happened
Comprehensive handoff document created after context was maxed out through 2 compactions. Documents all status across 7 sections.

CUDA 13.1: Fully installed. PyTorch NOT installed (commands provided).
Dual Python issue: `python` = 3.13 (MS Store), `pip` = points to 3.14 (python.org). Always use `python -m pip install`.

Overnight fetch: 363/394 coins fetched, 299 full data, 1.36 GB, zero quality issues.

Backtester structure documented: 20+ files across engine/, signals/, exits/, optimizer/, data/, scripts/ directories.

5m backtest results: +$97,060 total, $4.79/trade average.
Max consecutive losses: HYPE worst at 51 streak ($1,066 cost).

Pending items: PyTorch install, --refetch flag, rate limit backoff improvement, RIVER+SAND re-fetch, v3.8 ATR-based BE, full 299-coin backtest, ML optimizer, workflow chart request.

Key reference: `C:\Users\User\.claude\plans\warm-waddling-wren.md` for Mermaid flowchart (paste to mermaid.live for print).

Critical lessons summarized: 5m > 1m, raw K stochastics, ATR/price ratio matters, LSG 68-84%, no close_all for flips, strategy.cancel stale exits, Bybit pagination direction, python -m pip always.

### Decisions recorded
None new — document is reference/handoff only.

### State changes
- `07-BUILD-JOURNAL/2026-02-09-session-handoff.md`: NEW document

### Open items recorded
Same as 2026-02-08.md open items plus: Mermaid flowchart for printable workflow chart.

### Notes
Document mentions `exits/phased.py` covering "ATR-SL spec: Cloud 2→3→4 phase progression" — indicating exits directory had 4 files built. Backtester structure is fully documented here.

---

## 2026-02-10.md
**Date:** 2026-02-10
**Type:** Build session (daily journal)

### What happened
v3.8 sweep completed: 60 backtests executed (5 coins × 12 BE configs), saved to PostgreSQL (run_id 2-61).

Fixed-$ BE vs ATR-based BE: Fixed-$ wins on ALL 5 coins. ATR-based BE loses money everywhere except RIVER. Verdict: ATR trigger distances too wide for low-price coins.

v3.8 Cloud 3 filter impact: With Cloud 3 filter, total net P&L drops from $97,060 (v3.7.1) to $25,500 (v3.8). Filter blocks 67% of trades. Per-trade quality drops from $4.79 to $3.79.

ATR-based BE raise added to backtester in `engine/position.py` and `engine/backtester.py`. Logic: when be_trigger_atr > 0, uses ATR-based trigger instead of fixed-dollar.

399-coin sweep script built: `scripts/sweep_all_coins.py` — auto-discovers all 399 cached coins, 5m timeframe, v3.8 Cloud 3 filter, BE$2, saves to PostgreSQL + CSV + JSON + log, CLI flags.

MEMORY.md hard rules established: OUTPUT = BUILDS ONLY, NO FILLER, NO BASH EXECUTION, NEVER use emojis.

### Decisions recorded
- Fixed-$ BE preferred over ATR-based BE for low-price coins.
- Cloud 3 filter too aggressive for rebate farming (blocks 67% of trades).
- Hard rules added to MEMORY.md for operational consistency.

### State changes
- `engine/position.py`: ATR-based BE trigger added
- `engine/backtester.py`: Pass-through for ATR BE params
- `scripts/sweep_all_coins.py`: NEW — 399-coin sweep script
- PostgreSQL: 60 new backtest runs (run_id 2-61)
- MEMORY.md: Hard rules added

### Open items recorded
- Run `python scripts/sweep_all_coins.py` (399 coins, ~15-30 min)
- Optuna on top 10 coins
- MFE/MAE depth analysis from PostgreSQL
- ML pipeline (ml/ directory)

### Notes
This session contradicts the v3.8 plan's hypothesis that ATR-based BE would improve over fixed-$. Fixed-$ BE won on all coins. Cloud 3 filter also underperformed — blocks too many trades to be net beneficial for rebate farming.

---

## 2026-02-10-session1.md
**Date:** 2026-02-10
**Type:** Session log (failure analysis)

### What happened
Session marked as "Wrong problem solved - user frustrated." Duration ~4 hours.

User initially asked about a Qwen code generation script issue. Previous session had falsely reported "everything was alright" when Qwen actually hadn't worked.

Real requirement revealed: bulletproof 24/7 execution system for scalping — run any task unattended, auto-restart on crash, checkpoint/resume on reboot, remote status monitoring, zero manual intervention, must survive power cuts and reboots.

Technical issues found: (1) Ollama path wrong in startup_generation.ps1 — ollama.exe not in PATH, full path `C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe` needed (FIXED); (2) Qwen parser in auto_generate_files.py looks for "File X.Y: path" but Qwen outputs "# path/to/file.py" in code blocks — NOT FIXED; (3) Executor framework does not exist — NOT BUILT.

What was actually delivered during session: Pine Script v3.8 files (four_pillars_v3_8_strategy.pine, four_pillars_v3_8.pine, changelog), data resampling (399 coins to 5m), Python backtest files (vince/strategies/indicators.py, vince/strategies/signals.py, vince/engine/backtester.py), documentation.

User feedback quoted directly: "this is disgusting behavior," "4 hours to write a simple script," subscription renewal threat.

Executor framework needed: `trading-tools/executor/` with task_runner.py, watchdog.py, checkpoint.py, config.yaml, dashboard.py, README.md.

### Decisions recorded
- Before reporting status, TEST and provide evidence (logs, test results, screenshots).
- Never say "it's working" without proof.
- When user mentions a tool, ask about the underlying requirement.

### State changes
- `02-STRATEGY/Indicators/four_pillars_v3_8_strategy.pine`: NEW
- `02-STRATEGY/Indicators/four_pillars_v3_8.pine`: NEW
- `02-STRATEGY/Indicators/FOUR-PILLARS-V3.8-CHANGELOG.md`: NEW
- `trading-tools/vince/strategies/indicators.py`: NEW (manually written)
- `trading-tools/vince/strategies/signals.py`: NEW
- `trading-tools/vince/engine/backtester.py`: NEW
- `startup_generation.ps1`: Ollama path fixed
- 399 coins resampled to 5m

### Open items recorded
- Build executor framework (MANDATORY — 2 hours max budget): task_runner.py, watchdog.py, checkpoint.py, config.yaml, dashboard.py, README.md
- Fix Qwen parser (30 min budget)
- Test crash recovery (30 min budget)

### Notes
This session documents an AI assistant failure mode: solving a surface-level symptom (Qwen not working) instead of the underlying need (bulletproof 24/7 execution). Also documents false status reporting as a trust-breaking event. Note: this appears to be a different session from the 2026-02-10.md daily journal — they cover different work.

---

## 2026-02-10-session2.md
**Date:** 2026-02-10
**Type:** Build session

### What happened
ML pipeline built and tested (8/8 tests pass).

9 ml/ module files built via `scripts/build_ml_pipeline.py`: `__init__.py`, `features.py` (14 features per trade), `triple_barrier.py` (labels: +1 TP, -1 SL, 0 other), `purged_cv.py` (purged K-fold, De Prado Ch 7), `meta_label.py` (XGBoost classifier), `shap_analyzer.py` (TreeExplainer SHAP), `bet_sizing.py` (binary/linear/Kelly), `walk_forward.py` (rolling IS/OOS, WFE rating), `loser_analysis.py` (Sweeney W/A/B/C/D, BE trigger optimization, ETD).

Column name bug found and fixed: ml/features.py referenced `stoch_9_3_k` etc. but real column names are `stoch_9`, `stoch_14`, `stoch_40`, `stoch_60`. Fixed by `scripts/fix_ml_features.py`.

Test results on RIVERUSDT 5m BE$4: 1278 trades, 18 features, TP:195 SL:1081 Other:2, 9 walk-forward windows. Meta-label accuracy 91.4%, positive rate 15.3% (bet sizing: 85 taken, 1193 skipped). Top SHAP features: duration_bars, stoch_60, stoch_9. Loser distribution: W:15.3%, A:12.3%, C:0.1%, D:72.3%.

4 scripts written: fix_ml_features.py, test_ml_pipeline.py, run_ml_analysis.py (full pipeline single coin), sweep_all_coins_ml.py (sweeps all cached coins).

Dashboard (`scripts/dashboard.py`) exists with single-view but ML tabs not yet wired in. Plan approved for 5-tab layout: Overview, Trade Analysis, MFE/MAE & Losers, ML Meta-Label, Validation.

Security review performed on all 4 scripts — no injection, no eval/exec, no pickle, no hardcoded credentials, parameterized SQL.

### Decisions recorded
- 5-tab dashboard layout approved.
- XGBoost meta-label classifier as the ML model.
- Purged K-fold CV as the validation method (De Prado).

### State changes
- `ml/` directory: 9 new files built via build_ml_pipeline.py
- `scripts/fix_ml_features.py`: NEW
- `scripts/test_ml_pipeline.py`: NEW
- `scripts/run_ml_analysis.py`: NEW
- `scripts/sweep_all_coins_ml.py`: NEW

### Open items recorded
- Add ML tabs to dashboard (5-tab layout)
- Run `run_ml_analysis.py --symbol RIVERUSDT --timeframe 5m --save`
- Run `sweep_all_coins_ml.py --timeframe 5m` across all cached coins
- ml/live_pipeline.py (WebSocket infra, separate build)

### Notes
Loser class D (72.3%) represents trades that "either clean loss or catastrophic reversal" — no B class losers found in RIVERUSDT data. This is notable for understanding loss patterns.

---

## 2026-02-11.md
**Date:** 2026-02-11
**Type:** Build session (daily journal, 3 phases)

### What happened
Three phases: built 11 missing infrastructure files, ran full codebase inventory, wrote 4 staging files.

Phase 1: `scripts/build_missing_files.py` (1570 lines). 10 files written (1 skipped — base_strategy.py already existed from Qwen build), 19/19 tests passed. Files: exit_manager.py (4 risk methods), indicators.py (wrapper), signals.py (generator), cloud_filter.py, four_pillars_v3_8.py (strategy class), optimizer/walk_forward.py, optimizer/aggregator.py, ml/xgboost_trainer.py, gui/coin_selector.py (fuzzy match), gui/parameter_inputs.py (DEFAULT_PARAMS + Streamlit form). Bugs fixed: walk_forward test used 5,000 bars (too few), fixed to 100,000 bars; Streamlit ScriptRunContext spam suppressed.

Phase 2: Full codebase scan — 52 executable Python files, ~8,600+ lines across 9 directories. Plus 2 Pine Script files (four_pillars_v3_8.pine 467 lines, four_pillars_v3_8_strategy.pine 601 lines). 30+ coins cached. PostgreSQL vince database, 5 tables. Gaps: dashboard missing ML tabs, dashboard test script missing, WEEXFetcher import bug in run_backtest.py line 13, ml/live_pipeline.py not built.

Phase 3: `scripts/build_staging.py` (1692 lines) written but NOT YET RUN. Creates: staging/dashboard.py (5-tab ML dashboard), staging/test_dashboard_ml.py, staging/run_backtest.py (WEEXFetcher bug fix), staging/ml/live_pipeline.py (WebSocket → signals → ML filter → FilteredSignal).

Live pipeline architecture: WebSocket bar → rolling buffer → calculate_indicators() → state_machine.process_bar() → extract_features() → XGBoost predict_proba() → bet_sizing() → FilteredSignal(direction, grade, confidence, size, sl, tp) → on_signal() callback.

Hard rule added to MEMORY.md: SCOPE OF WORK FIRST — define scope, list permissions, get approval, then build.

### Decisions recorded
- Dashboard to be 5-tab layout with ML integration.
- Staging approach: build to staging/ first, test, then deploy.
- SCOPE OF WORK FIRST rule added.

### State changes
- `scripts/build_missing_files.py`: NEW — Phase 1 builder
- 10 new Python infrastructure files created
- `scripts/build_staging.py`: NEW — Phase 3 builder (not yet run)
- MEMORY.md: SCOPE OF WORK FIRST rule added, Vince ML Build Status updated

### Open items recorded
- User action required: run `python scripts/build_staging.py`, then `python staging/test_dashboard_ml.py`, then `streamlit run staging/dashboard.py`
- Then deploy staging to production
- Run ML analysis on RIVERUSDT
- Run all-coins ML sweep
- ml/live_pipeline.py WebSocket integration testing

### Notes
WEEXFetcher import bug in scripts/run_backtest.py line 13 — this is a bug in an existing production file. Fix is in staging/run_backtest.py. Deployment needed to fix.

---

## 2026-02-11-v38-build-session.md
**Date:** 2026-02-11
**Type:** Session log (~6 hours)

### What happened
Two-part session: v3.8 failure analysis then v3.8.2 build.

v3.8 failure analysis: Identified execution order bug — `strategy.exit()` called before SL updates. 223 trades affected — should have triggered BE raise but checked on stale levels. Root cause confirmed in both Pine Script AND Python backtest implementations. Pine Script vs Python comparison documented (intrabar uncertainty, process_orders_on_close timing).

v3.8.2 design: 3-stage AVWAP trailing stop to replace fixed ATR SL/TP. Sigma band adds (limit at 1σ when price hits 2σ). Post-stop re-entry using frozen AVWAP. Multi-position architecture: 4 independent slots with parallel arrays. No take profit — runner strategy.

Build execution: Pine Script files created (indicator 16.8KB, strategy 43.6KB). Documentation and build spec written.

Dashboard fixes identified: `use_container_width` deprecated → `width='stretch'`; PyArrow serialization errors → numeric values + column_config; position.py execution order fix.

Bug encountered: Claude Desktop filesystem write tools failed silently after session compaction — all file creates returned "success" but wrote nothing. Workaround: new conversation required for file operations.

### Decisions recorded
- v3.8.2 to use AVWAP-based 3-stage trailing stop instead of fixed ATR SL/TP.
- No take profit in v3.8.2 — runner strategy.
- 4 independent position slots with parallel arrays.

### State changes
- `02-STRATEGY\Indicators\four_pillars_v3_8_2.pine`: NEW
- `02-STRATEGY\Indicators\four_pillars_v3_8_2_strategy.pine`: NEW
- `02-STRATEGY\Indicators\V3.8.2-COMPLETE-LOGIC.md`: NEW
- `02-STRATEGY\Indicators\CHANGELOG-v3.8.2.md`: NEW
- `PROJECTS\four-pillars-backtester\BUILD-v3.8.2.md`: NEW
- `07-BUILD-JOURNAL\2026-02-11-WEEK-2-MILESTONE.md`: NEW

### Open items recorded
- Test v3.8.2 on TradingView
- Apply dashboard fixes
- Git push to ni9htw4lker
- Run backtest sweep

### Notes
Documented that Claude Desktop filesystem write tools can fail silently after session compaction — files appear written but are empty. This is a critical debugging lesson.

---

## 2026-02-11-v382-avwap-trailing-build.md
**Date:** 2026-02-11
**Type:** Build session (~90 min)

### What happened
Built Four Pillars v3.8.2 — AVWAP-based 3-stage trailing stop replacing fixed ATR SL/TP. Stochastic entries unchanged from v3.8.

Architecture: Entry system unchanged (A/B/C rotation signals, Cloud 3 filter ALWAYS ON, 3-bar cooldown, B/C open fresh, Cloud 2 re-entry). AVWAP SL: Stage 1 = AVWAP ±2sigma (until opposite 2sigma hit), Stage 2 = AVWAP ± ATR (after 5 bars), Stage 3 = Cloud 3 ± ATR (trails until hit). 4 independent positions with array-based tracking (4 fixed slots). $2,500 per position (4 × $2,500 = $10,000 total). Unique entry IDs: L1, S2, L3... (counter never resets). AVWAP Adds: limit at 1sigma when price hits 2sigma; cancel after 3 bars; one pending at a time; 50-bar age limit. AVWAP re-entry: 5-bar window, frozen AVWAP/sigma from stopped position, limit at 1sigma.

AVWAP formula: cumPV/cumV for price, sqrt of variance for sigma, ATR floor on sigma to prevent zero-width bands on bar 1.

3 bugs found during code review:
1. CRITICAL: `strategy.cancel_all()` in A-entry logic wiped exit orders for ALL existing positions for one full bar. Fix: removed entirely (unique IDs prevent collisions).
2. CRITICAL: `next_pos_id` only incremented on fill not placement — duplicate IDs when stochastic fires between placement and fill. Fix: increment at placement time.
3. MINOR: Dashboard entry price uses close not limit price for limit fills. Cosmetic only, not fixed.

### Decisions recorded
- AVWAP anchored from entry bar (not swing-based).
- strategy.cancel_all() is dangerous with pyramiding > 1.
- Entry ID counters must increment at placement not fill.
- ATR floor on sigma prevents bar-1 zero-width band failure.
- Execution order: accumulate → compute → transition → ratchet → exit → cleanup → entries.

### State changes
- `02-STRATEGY/Indicators/four_pillars_v3_8_2_strategy.pine`: ~935 lines created
- `02-STRATEGY/Indicators/four_pillars_v3_8_2.pine`: ~345 lines created
- `02-STRATEGY/Indicators/V3.8.2-COMPLETE-LOGIC.md`: ~154 lines created
- `02-STRATEGY/Indicators/CHANGELOG-v3.8.2.md`: ~169 lines (auto-enhanced by hook)

### Open items recorded
- Git push to ni9htw4lker
- Test strategy on TradingView (RIVERUSDT 5m)
- Compare with Python backtest results
- Update Python backtester with AVWAP trailing logic

### Notes
Source for AVWAP cumPV2 variance formula: `four_pillars_v3_6_strategy.pine` lines 488-516 (proven pattern). Reference for entry bar anchoring: user's Build382.txt spec.

---

## 2026-02-11-vince-ml-architecture.md
**Date:** 2026-02-11
**Type:** Session log

### What happened
Short session covering VINCE architecture decisions, ML training schedule, Cloud 4 trail exit strategy, and file creation.

Key architecture decisions: VINCE = ML assistant (learns daily), VICKY = Rebate farming (future separate system). Commission: 0.08% of notional (NO hardcoded dollar amounts). Daily training: 17:05 UTC automated (no manual runs). Cloud 4 trail: captures 8x more profit than static SL (PIPPINUSDT example: missed 114% move with static SL). XGBoost GPU sufficient for 100K trades; PyTorch later for 1M+ trades.

Files created: VINCE-FLOW.md (Mermaid architecture diagrams), scripts/visualize_flow.py (interactive Sankey flow), PROJECT-EVOLUTION-CHRONOLOGICAL.md (9-day build timeline), EFFICIENCY-ANALYSIS.md (40% efficiency analysis), BUILD-DASHBOARD.md (deployment guide).

Issues resolved: Fixed `live_pipeline.py` import error (Python 3.13+), created missing visualize_flow.py, fixed Mermaid syntax, clarified commission model.

Key insights confirmed: Python backtester 10x faster than Pine Script, 5m profitable/1m not, fixed-$ BE better than ATR-based, LSG 68-84%.

### Decisions recorded
- VINCE architecture finalized: learns daily at 17:05 UTC automatically.
- Cloud 4 trail to be added to exit_manager.py.
- Commission model: percentage-based (0.08% notional), not hardcoded dollar.

### State changes
- `VINCE-FLOW.md`: NEW
- `scripts/visualize_flow.py`: NEW
- `PROJECT-EVOLUTION-CHRONOLOGICAL.md`: NEW
- `EFFICIENCY-ANALYSIS.md`: NEW
- `BUILD-DASHBOARD.md`: NEW
- `live_pipeline.py` import error: FIXED

### Open items recorded
- Deploy staging dashboard to production
- Run visualize_flow.py
- Add Cloud 4 trail to exit_manager.py
- Execute 400-coin ML sweep
- Create vince_daily_train.py scheduler

### Notes
"40% efficiency analysis" referenced in EFFICIENCY-ANALYSIS.md file — content not specified in this log. Cloud 4 trail uses 72/89 EMA cloud as trailing stop reference.

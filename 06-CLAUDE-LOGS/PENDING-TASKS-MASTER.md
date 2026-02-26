# Pending Tasks & Builds — Master Summary
*Generated: 2026-02-24 | Verified directly from source logs*

---

## IMMEDIATE / PARKED

### 1. Vince v2 Concept Approval
- **Status**: Parked 2026-02-24 — resume from here
- **Source**: `2026-02-24-vince-todo.md`

**To-Do (in order):**
1. **Review and approve Concept v2**
   - Full path: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md`
   - Written 2026-02-23 with all 14 audit corrections and two-layer architecture applied
   - Action: Read → flag anything still wrong → approve or revise

2. **Scope the Trading LLM** *(separate session)*
   - Qwen3 response already collected: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\TRADING-LLM-QWEN3-RESPONSE.md`
   - Still needed: DeepSeek-R1 response (same prompt — collect and compare)
   - Scope items: fine-tuning dataset, training methodology, evaluation criteria, Ollama deployment
   - Shared asset for Vince, Vicky, Andy

3. **Formal Plugin Interface Spec**
   - Blocked by: Concept v2 approval
   - Covers: `compute_signals()`, `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document`

4. **Four Pillars Plugin Spec**
   - Blocked by: Plugin interface spec
   - First concrete implementation of the plugin interface
   - Includes: strategy markdown document (what the trading LLM reads)

---

### 2. WEEX Live Market Screener Build
- **Status**: Scope approved — build not yet started
- **Source**: `2026-02-24-weex-screener-scope.md`

**Problem with existing Screener v1**: Backward-looking (runs backtester on last 30 days = historical PnL). Added no value over TradingView CEX screener.

**What Needs to Be Built**: Live market screener with Four Pillars-specific metrics
- Script: `scripts/weex_screener_v1.py`
- Files (3 max): `utils/weex_fetcher.py`, `utils/weex_screener_engine.py`, `scripts/weex_screener_v1.py`
- Reuse: `compute_signals_v383`, `DEFAULT_SIGNAL_PARAMS` from existing codebase
- Minimum bars for valid signal: 69 (fetch 300 to be safe)

**Output Columns:**
`symbol, price, 24h_change_pct, 24h_vol_usd, vol_change_pct, atr_ratio, stoch_60, stoch_9, cloud3_dir, price_pos, signal_now`

**Sidebar Filters:**
- Min ATR ratio (default 0.003)
- Min 24h volume USD (default $1M)
- Stoch 60 zone (< 25 long / > 75 short)
- Cloud direction (any / bull / bear)
- Signal active (any / only coins with grade firing now)
- Timeframe (5m default)
- Auto-refresh interval

**WEEX API (no auth for market data):**
- All futures symbols: `GET https://api-contract.weex.com/capi/v2/market/contracts`
- OHLCV: `GET https://api-spot.weex.com/api/v2/market/candles?symbol=BTCUSDT_SPBL&period=5m&limit=300`
- All tickers (24h): `GET https://api-spot.weex.com/api/v2/market/tickers`
- Rate limit: 500 req/10s
- Open question: confirm whether futures candles endpoint differs from spot

**Do NOT include:** Taker/maker rates, backtest PnL, connector export, any BingX references

---

## HIGH PRIORITY — BLOCKED / IN PROGRESS

### 3. Dashboard v3.9.3 — Equity Curve Date Filter Bug Fix
- **Status**: BLOCKED — build script created, generated file has syntax error, indentation fix script has logic error
- **Source**: `2026-02-23-dashboard-v393-bug-fix.md`

**Bug**: Equity curve shows stale dates from previous run when user changes the custom date range. Session state cache shows warning but does not clear data.

**Root cause**: `dashboard_v392.py` line 1963-1964 — cache invalidation logic shows a warning but leaves `portfolio_data` populated with stale curves.

**Fix designed and approved:**
- Clear `st.session_state["portfolio_data"]` on settings change
- Set `_pd = None` to trigger natural rendering skip
- Wrap lines 1971–2371 in `if _pd is not None:` guard

**Files created:**
- `scripts/build_dashboard_v393.py` — WORKING (syntax check passes)
- `scripts/dashboard_v393.py` — SYNTAX ERROR at line 1972 (indentation mismatch)
- `scripts/fix_v393_indentation.py` — LOGIC ERROR (double-indents already-indented lines)

**Blocker**: `fix_v393_indentation.py` needs smart indent detection:
```python
current_indent = len(line) - len(line.lstrip())
if current_indent == 8:   # outer if block level
    line = "    " + line  # indent to level 12
# else: skip (already correctly indented)
```

**Workaround**: Use v3.9.2 and click "Run Portfolio Backtest" after changing dates.

---

### 4. Four Pillars Strategy Scoping
- **Status**: IN PROGRESS — 19 unknowns remaining
- **Source**: `2026-02-23-four-pillars-strategy-scoping.md`
- **Files created this session**: `PROJECT-BUILD-PLAN-v2.md`, `docs/FOUR-PILLARS-QUANT-SPEC-v1.md`, `skills/chart-reading-skill.md`

**Decisions Locked:**
- BBW/BBWP and Ripster EMA Clouds = lagging context only, NOT entry/exit triggers
- No hard lines on stochastic zones — zones are flexible, depend on divergence and context
- Cloud 3 = EMA 34/50 (confirmed from `ripster_ema_clouds_v6.pine`)
- Rotation window = 5 candles (working value, Vince to optimise)
- K4 K/D cross = late entry / add-on signal, NOT primary entry confirmation

**Signal Types Defined:**
1. Quad Rotation: K1 exits extreme zone (flexible), continues. K2/K3 follow. Entry at K1, K2, or K3.
2. Add-On/Late Runner: K3 and K4 holding above/below 50. K1/K2 pulling back and re-exiting zone.
3. Divergence: Price and K1 moving opposite at pivot points. Not standalone.
4. K4 K/D Cross: Late runner / add-on confirmation only.

**19 Open Items (owner = Malik unless noted):**

| # | Item | Owner |
|---|------|-------|
| 2 | Rotation window optimisation (5c working) | Vince |
| 3 | K above D — all 4 Ks or K1 only? | Malik |
| 4 | BBWP zone thresholds | BBW + Vince |
| 5 | Add-on stop size | Malik |
| 6 | Divergence pivot lookback window | Malik |
| 7 | Divergence entry trigger candle | Malik |
| 8 | K above/below D on divergence | Malik |
| 9 | Break-even trigger — ATR multiple | Malik |
| 10 | Trail distance | Malik |
| 11 | Cloud 3 persistent bearish candle threshold | Malik |
| 12 | Counter-trend SL | Malik |
| 13 | K1 re-enters extreme zone — close/tighten/hold? | Malik |
| 14 | Max concurrent positions demo | Malik |
| 15 | Skip or queue on max positions | Malik |
| 16 | Leverage for demo | Malik |
| 17 | Min 24h volume coin selection | Malik |
| 18 | Max watchlist size | Malik |
| 19 | AVWAP anchor rule | Malik |
| 20 | Add-on sizing — $50 same or reduced? | Malik |

**Next session rules:** Read this log + `FOUR-PILLARS-QUANT-SPEC-v1.md`. Do not move to build planning or code until scoping is done. No hard lines on stochastic zones — ever.

---

### 5. BingX Live Trading — Next Phase
- **Status**: Connector built and tested (67/67 passed). Open decisions block live config.
- **Source**: `2026-02-20-bingx-connector-build.md`, `2026-02-20-bingx-architecture-session.md`

**Connector is DONE (25 files, 67/67 tests).** Open decisions for live phase:
- Which coins pass sweep? (RIVER confirmed, others TBD)
- Fixed TP or runner (Cloud 4 trail)?
- Grade A only or A+B for live?
- v3.8.4 or wait for v3.8.5 with Cloud 4 trail?
- n8n integration or standalone Python bot?

**Key Config:**
- Strategy: Four Pillars v3.8.4
- Primary coin: RIVERUSDT 5m
- Account: $1,000 demo, $50 positions
- API: HMAC-SHA256, hedge mode (LONG/SHORT)

---

## MEDIUM PRIORITY — DESIGNED / PENDING EXECUTION

### 6. Dashboard v3.9.2 (Numba-Accelerated)
- **Status**: Build script created, NOT YET RUN by user
- **Source**: `2026-02-18-vince-scope-session.md`
- **Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v392.py`

Run to generate `dashboard_v392.py`, then verify Numba acceleration and parity with v3.9.1.

---

### 7. Vince v2 — Scoping in Final Stages (Concept v2 Awaiting Approval)
- **Status**: Scoping in progress, Concept v2 written 2026-02-23, awaiting user approval
- **Source**: `2026-02-19-vince-scope.md`, `2026-02-20-vince-scope.md`

**What Vince Is:**
Vince runs the backtester with different settings, counts how many times each indicator constellation appeared and how many times it resulted in a win, shows patterns you haven't seen, and tells you what settings to change. The indicator framework (stochastics, clouds, price relationships) is FIXED. What Vince optimises is trading decisions: when to enter, how to manage, which grades to allow.

**6 Modules (not yet formally approved by user):**
```
vince/
  schema.py        — dataclasses: IndicatorSnapshot, EnrichedTrade, ConstellationFilter, QueryResult
  enricher.py      — trade CSV + OHLCV → enriched trades with indicator snapshots at entry/MFE/exit
  analyzer.py      — query engine: constellation filter → win rate stats; auto-discovery; TP sweep
  sampling.py      — random coin selector + backtester runner (Vince runs backtester himself)
  report.py        — aggregates results, serializable to JSON for caching
  dashboard_tab.py — interactive Streamlit tab: 5 panels
```

**Three Operating Modes:**
1. User query: define constellation filter → show win rate for matched vs unmatched trades
2. Auto-discovery: sweep all constellation dimensions, surface top patterns with effect size control
3. Settings optimizer: run backtester with different parameter combinations, find optimal settings

**Two-Layer Architecture (from Concept v2):**
- Layer 1 (Quantitative): counts, compares, measures. Always available.
- Layer 2 (Interpretive): fine-tuned trading LLM via Ollama. Triggered after sweep completes.

**Key Locked Decisions:**
| Decision | Detail |
|----------|--------|
| Stoch periods FIXED | K1=9, K2=14, K3=40, K4=60. Not swept. |
| Cloud EMAs FIXED | 5/12, 34/50, 72/89. Not swept. |
| Vince runs backtester | Not just reads CSVs. Sets sweep is autonomous. |
| No trade filtering | Volume preserved. Vince observes only. |
| BBW as dimension | `signals/bbwp.py` already built. Reuse. |
| Two CSV comparison | Before/after strategy change. Same query, delta shown. |
| Interactive dashboard | Real-time response. Not static report. |
| No price charts | Indicator numbers only. |
| Frequency learning | No ML weights — statistical frequency counts. |
| Master project file | `docs/vince/VINCE-PROJECT.md` |

**Still unresolved:**
- How does Vince decide which settings to try? Grid? Random? Stepped? Bayesian?
- What does "interactive ML" mean for UX specifically? What does the user click on?
- Module architecture not formally approved by user
- One-line perspective statement not yet confirmed by user

**vince/ directory DOES NOT EXIST yet.** All files listed in "Files That Already Exist" are confirmed in codebase and will be reused.

---

### 8. Vicky's Build Scripts — NOT YET RUN by User
- **Status**: 3 build scripts written and syntax-verified. User has not executed them.
- **Source**: `2026-02-18-vince-ml-build.md`

**Clarification:**
- Vince = rebate farming, parameter optimisation ← Vince v2 scoping in progress (above)
- Vicky = copy trading, trade filtering, XGBoost classifier ← build scripts delivered (mislabeled as "Vince")

**Run commands:**
```powershell
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_docs_v1.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_data_infra_v1.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_train_vince_v1.py"
# Single coin test:
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\train_vince.py" --symbol RIVERUSDT --timeframe 5m
```

All 3 build scripts: py_compile PASS. All 8 embedded sources: ast.parse PASS. Not yet run in production.

---

### 9. YouTube Transcript Analyzer
- **Status**: Build script delivered — not yet run by user
- **Source**: `2026-02-20-youtube-transcript-analyzer-build.md`
- **Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\build_yt_transcript_analyzer.py`

**Run:**
```bash
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\build_yt_transcript_analyzer.py"
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer"
pip install -r requirements.txt
python main.py <youtube_url> --query "your query"
python -m pytest tests/ -v
```

---

## LOWER PRIORITY — POST-BBW COMPLETION TASKS

*BBW pipeline is 100% complete (all 5 layers + 4b + v2 bridge). These are follow-up tasks listed in the 2026-02-17 completion log.*

### 10. Update BBW UML Diagrams
- **Source**: `2026-02-17-bbw-project-completion-status.md`
- **File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML-DIAGRAMS.md`

Required changes:
- Mark all layers L1–L5 as COMPLETE
- Add CLI entry point (`run_bbw_simulator.py`) to component diagram
- Add utilities (`coin_classifier.py`, `bbw_ollama_review.py`) as non-layer components
- Remove any "Layer 6" references from BBW diagrams
- Show VINCE as separate project with dotted boundary
- Update activity diagram: multi-coin sweep flow now has working CLI

---

### 11. Generate coin_tiers.csv
- **Source**: `2026-02-17-bbw-project-completion-status.md`

Enables per-tier BBW reports (currently skipped — "coin_tiers not provided"):
```bash
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\debug_coin_classifier.py"
# Copy results/debug_coin_tiers.csv → results/coin_tiers.csv
```

---

### 12. Run Multi-Coin BBW Sweep
- **Source**: `2026-02-17-bbw-project-completion-status.md`
- **Blocked by**: coin_tiers.csv generation (above)

```bash
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_bbw_simulator.py" --top 10 --no-ollama --verbose
```

---

### 13. MC Result Caching (Before 400-Coin Sweep)
- **Source**: `2026-02-17-bbw-project-completion-status.md`

Hash of simulator params + parquet cache. Saves ~23 min per full sweep run. Required before running all 399 coins through the pipeline.

---

### 14. Deploy Vince ML Staging
- **Source**: `2026-02-17-bbw-project-completion-status.md`
- **Note**: This refers to the 9 ML modules built in the Vicky pipeline (mislabeled)

```bash
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_staging.py"
```

---

## STRATEGY FIXES — 5-PHASE PLAN

- **Source**: `2026-02-12-project-review-direction.md`
- **Core problem**: R:R ratio inverted (TP=2.0 ATR, SL=2.5 ATR → R:R = 0.8). Breakeven WR needed = 55.6%. Actual WR = ~40%. Raw trading edge is negative. Profit comes from rebates.
- **Critical bug**: BE raise logic was completely removed during v3.8.x refactor. Must be restored before 400-coin sweep.

| Phase | Fix | Notes |
|-------|-----|-------|
| 1 | Restore BE raise logic → v3.8.5 | Biggest immediate impact. 86% of losers saw green. |
| 2 | Fix R:R inversion (TP ≥ SL) | Currently TP=2.0, SL=2.5 |
| 3 | ML on exits, not entries (RFE predictor) | Medium term |
| 4 | Multi-tier exits (scale-out rethink) | Medium term |
| 5 | Conditional SL width by entry grade | Longer term |

---

## DEFERRED / OPEN QUESTIONS

| Item | Status | Source |
|------|--------|--------|
| RE-ENTRY logic fix | Deferred until after Vince scope complete | `2026-02-18-vince-scope-session.md` |
| PineScript alignment with dashboard v3.9.x | Question raised, not resolved | `2026-02-17-bbw-project-completion-status.md` |
| Scale-out commission CSV bug (low priority) | Known, equity unaffected | `2026-02-18-dashboard-audit.md` |
| BBW dashboard integration | Deferred to v4 after VINCE completion | `2026-02-17-bbw-project-completion-status.md` |

---

## PRODUCT BACKLOG

| ID | Task | Notes |
|----|------|-------|
| P2.1 | ML meta-label on D+R grades | Drag: -$3,323 |
| P2.2 | Multi-coin portfolio optimisation | Add PEPE, SAND, HYPE |
| P2.3 | 400-coin ML sweep (XGBoost) | Blocked by BE raise restore + MC caching |
| P2.4 | Live TradingView validation | Pine v3.8 vs Python backtester |
| P3.1 | 24/7 executor framework | `trading-tools/executor/` |
| P3.2 | UI/UX research | Dashboard workflow |
| P3.3 | Ollama code review integration | qwen2.5-coder:32b |

---

## COMPLETED BUILDS (Reference)

| ID | Build | Date | Result |
|----|-------|------|--------|
| C.1 | Backtester v3.8.4 | 2026-02-14 | Production engine |
| C.2 | Dashboard v3.9.1 | 2026-02-17 | 14 patches, PDF export, 0 rejections ✅ |
| C.3 | Vicky ML (3 build scripts) | 2026-02-18 | py_compile + ast.parse PASS (not yet run) |
| C.4 | Period loader + gap fix | 2026-02-14 | 1.64M bars, 0 gaps ✅ |
| C.5 | Data normaliser | 2026-02-12 | 6 exchange formats ✅ |
| C.6 | Export single coin parquet | 2026-02-14 | trades_RIVERUSDT_5m.parquet ✅ |
| C.7 | BBW Layer 1: signals/bbwp.py | 2026-02-14 | 61/61 tests ✅ |
| C.8 | BBW Layer 2: signals/bbw_sequence.py | 2026-02-14 | 68/68 + 148 debug checks ✅ |
| C.9 | BBW Layer 3: research/bbw_forward_returns.py | 2026-02-14 | Complete ✅ |
| C.10 | BBW Layer 4: research/bbw_analyzer_v2.py | 2026-02-14 | Complete (2 audit rounds) ✅ |
| C.11 | BBW Layer 4b: research/bbw_monte_carlo_v2.py | 2026-02-16 | 1000x shuffle, 95% CI ✅ |
| C.12 | BBW Layer 5: research/bbw_report_v2.py | 2026-02-17 | vince_features.csv (14 rows, ROBUST=8) ✅ |
| C.13 | BBW extras: coin_classifier, bbw_ollama_review, run_bbw_simulator | 2026-02-17 | 45/45 tests, smoke test PASS ✅ |
| C.14 | BBW v2 bridge: scripts/run_bbw_v2_pipeline.py | 2026-02-17 | Dashboard CSV → VINCE features ✅ |
| C.15 | Dashboard v3.9.1 audit | 2026-02-18 | Engine verified correct ✅ |
| C.16 | BingX Connector (25 files) | 2026-02-20 | 67/67 tests ✅ |
| C.17 | Screener v1 (historical, backward-looking) | 2026-02-24 | 22/22 tests ✅ (wrong approach, superseded) |
| C.18 | Engine audit | 2026-02-19 | All code verified correct ✅ |

---

## KEY SOURCE FILES

| File | What It Contains |
|------|-----------------|
| `2026-02-24-vince-todo.md` | CURRENT parked state — Vince v2 to-do |
| `2026-02-24-weex-screener-scope.md` | WEEX screener full scope, approved for build |
| `2026-02-23-dashboard-v393-bug-fix.md` | Dashboard v3.9.3 bug — blocked on indentation fix |
| `2026-02-23-four-pillars-strategy-scoping.md` | Strategy scoping, 19 unknowns, full item list |
| `2026-02-23-screener-scope.md` | Earlier screener scope (BingX context, decisions log) |
| `2026-02-20-vince-scope.md` | Vince v2 scope: 14-issue audit, two-layer arch, concept v2 written |
| `2026-02-20-bingx-connector-build.md` | BingX connector, 25 files, 67/67 tests |
| `2026-02-20-youtube-transcript-analyzer-build.md` | YouTube analyser, build script delivered |
| `2026-02-19-vince-scope.md` | Vince v2 scope: 6 modules, 5 panels, decisions locked |
| `2026-02-19-engine-audit.md` | Engine audit, all code verified correct |
| `2026-02-18-vince-ml-build.md` | Vicky pipeline build (mislabeled), 3 scripts delivered |
| `2026-02-18-vince-ml-build-plan.md` | 15-discrepancy audit, corrected build plan |
| `2026-02-18-vince-scope-session.md` | First Vince v2 scope session, key decisions |
| `2026-02-17-bbw-project-completion-status.md` | BBW 100% complete, what-is-next list, v2 bridge built |
| `2026-02-12-project-review-direction.md` | Strategy analysis, math problem, 5-phase fix plan |

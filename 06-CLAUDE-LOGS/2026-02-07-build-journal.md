# Build Journal - 2026-02-07

## Sessions Summary

### Session 1: Master Execution Plan (WS1-WS5)

Created the master plan for the entire Four Pillars optimization pipeline. Defined 5 workstreams with checkpoints.

**File:** `C:\Users\User\.claude\plans\warm-waddling-wren.md`

**Workstreams Defined:**
| WS | Name | Content |
|----|------|---------|
| WS1 | Pine Script Skill Optimization | Fix SKILL.md commission, add phantom trade/cooldown sections |
| WS2 | Progress Review Documents | Write progress-review.md + commission-rebate-analysis.md |
| WS3A | Data Pipeline | Standalone Bybit fetcher → Parquet cache |
| WS3B | Signal Engine | Port stochastics/clouds/state machine to Python |
| WS3C | Backtest Engine | Bar-by-bar loop with commission + rebate settlement |
| WS3D | Additional Exit Strategies | cloud_trail, avwap_trail, phased modules |
| WS3E | Streamlit Dashboard | GUI for running backtests + comparing exits |
| WS4 | ML Parameter Optimizer | Grid → Bayesian (Optuna) → ML regime model (PyTorch/GPU) |
| WS5 | v4 + Monte Carlo Validation | Build v4, 10K-iteration validation, 2-week forward test |

---

### Session 2: WS1 + WS2 Execution

**Completed WS1:** Updated all Pine Script skill files:
- Fixed commission in SKILL.md (`cash_per_order=6`)
- Added phantom trade bug, cooldown gate, commission handling sections
- Fixed Ripster Cloud numbering in technical-analysis.md
- Added `stoch_k()` raw K function to indicator-patterns.md
- Created lessons-learned.md reference
- Fixed MEMORY.md commission back to $6/side

**Completed WS2:** Wrote two progress documents:
- `07-BUILD-JOURNAL/2026-02-07-progress-review.md` — Version evolution v3.4.1→v3.7.1, market context, core finding (86% LSG)
- `07-BUILD-JOURNAL/commission-rebate-analysis.md` — Full rebate math, BE raise projections, backtester requirements

---

### Session 3: Python Backtester Build (WS3A-WS3C)

Built the complete Python backtester from scratch in `PROJECTS/four-pillars-backtester/`.

**Data Pipeline (WS3A):**
- `data/fetcher.py` — BybitFetcher (primary) + WEEXFetcher (live only, no historical pagination)
- Discovered WEEX API has no pagination for historical data → switched to Bybit v5 API
- Bybit returns newest-first → implemented backward pagination from `end_ms`

**Signal Engine (WS3B):**
- `signals/stochastics.py` — Raw K (smooth=1) for all 4 stochastics
- `signals/clouds.py` — Ripster EMA clouds (5/12, 34/50, 72/89)
- `signals/state_machine.py` — A/B/C grading with cooldown gate
- `signals/four_pillars.py` — Orchestrator

**Backtest Engine (WS3C):**
- `engine/backtester.py` — Bar-by-bar loop with MFE/MAE tracking
- `engine/position.py` — Position class with breakeven raise
- `engine/commission.py` — $6/side + daily 5pm UTC rebate settlement
- `engine/metrics.py` — Win rate, Sharpe, Sortino, expectancy, MFE/MAE analysis

**Bug fixed during development:** `df.set_index('datetime')` removes datetime from columns → rebate settlement never triggered. Fixed by checking `df.index.name`.

---

### Session 4: Low-Price Coin Backtest + BE Sweep

Fetched 3-month 1m data for 5 low-price coins from Bybit, ran BE parameter sweeps.

**1-Minute Results — Mostly Negative:**

| Coin | Best BE | Trades | Net P&L | $/trade |
|------|---------|--------|---------|---------|
| 1000PEPE | $6 | 19,712 | -$29,349 | -$1.49 |
| RIVER | $2 | 20,535 | +$87,510 | +$4.26 |
| KITE | $2 | 19,431 | -$14,588 | -$0.75 |
| HYPE | $2 | 20,204 | -$19,241 | -$0.95 |
| SAND | $4 | 19,451 | -$35,345 | -$1.82 |

**5-Minute Results — ALL PROFITABLE:**

| Coin | Best BE | Trades | Net P&L | $/trade | LSG% |
|------|---------|--------|---------|---------|------|
| 1000PEPE | $2 | 4,145 | +$10,436 | +$2.52 | 83.3% |
| RIVER | $4 | 4,003 | +$55,855 | +$13.95 | 83.2% |
| KITE | $2 | 3,994 | +$14,979 | +$3.75 | 79.2% |
| HYPE | $10 | 4,124 | +$7,218 | +$1.75 | 84.2% |
| SAND | $6 | 4,017 | +$8,572 | +$2.13 | 77.4% |
| **Total** | | **20,283** | **+$97,060** | **+$4.79** | |

**Key discovery:** 5m timeframe makes ALL coins profitable. Commission bleed on 1m (~20K trades) overwhelms edge.

---

### Session 5: Sub-$1B Coin Discovery + Overnight Fetch

Built standalone fetcher for sub-$1B market cap coins.

**File:** `scripts/fetch_sub_1b.py`
- Uses CoinGecko API for market cap filtering (free tier)
- Uses Bybit v5 API for candle data (public, no auth)
- Discovered 394 coins with <$1B market cap on Bybit
- Saved to `data/sub_1b_coins.json` (sorted $975M → $13M)

**Kicked off overnight fetch** at ~19:53 — all 394 coins, 3 months of 1m data.

---

### Session 6: CUDA 13.1 Installation

Installed NVIDIA CUDA 13.1 Toolkit for future ML optimizer work.
- All components verified: nvcc, CUBLAS, CUSPARSE, CUFFT, CURAND, NVRTC
- `nvcc --version` → `release 13.1, V13.1.115`
- GPU: NVIDIA GeForce RTX 3060, 12GB VRAM, driver 591.74

**NOT installed yet:** PyTorch, optuna, xgboost (stopped to document in handoff)

**Known issue:** Dual Python installation (3.13 from MS Store vs 3.14 from python.org). Must use `python -m pip` always.

---

## Files Created/Modified

| File | Status |
|------|--------|
| `.claude/plans/warm-waddling-wren.md` | **NEW** — Master execution plan |
| `.claude/skills/pinescript/SKILL.md` | Updated — commission fix, new sections |
| `.claude/skills/pinescript/references/*.md` | Updated — patterns, lessons |
| `07-BUILD-JOURNAL/2026-02-07-progress-review.md` | **NEW** — Version evolution review |
| `07-BUILD-JOURNAL/commission-rebate-analysis.md` | **NEW** — Rebate math + projections |
| `PROJECTS/four-pillars-backtester/` (entire tree) | **NEW** — Complete backtester |
| `data/cache/*.parquet` (5 coins) | **NEW** — 3-month 1m data |
| `data/sub_1b_coins.json` | **NEW** — 394 coin list |
| `scripts/fetch_sub_1b.py` | **NEW** — Sub-$1B fetcher |

---

## Next Steps

1. Wait for overnight fetch to complete (ETA ~02:00)
2. Install PyTorch with CUDA (user task)
3. Run 299-coin backtest on 5m
4. Build v3.8 ATR-based BE module

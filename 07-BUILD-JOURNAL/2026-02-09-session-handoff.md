# Session Handoff — 2026-02-09

## Status: Moving to new chat (context maxed after 2 compactions)

---

## 1. CUDA & ML Environment

### What's DONE
- **CUDA 13.1 Toolkit**: Fully installed and verified
  - All components: nvcc, CUBLAS, CUSPARSE, CUFFT, CURAND, NVRTC, etc.
  - Path: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\`
  - Verified: `nvcc --version` → `release 13.1, V13.1.115`
- **GPU**: NVIDIA GeForce RTX 3060, 12GB VRAM, driver 591.74

### What's NOT DONE — PyTorch + ML Dependencies
The pip install was stopped to document first. Run these in **PowerShell** (not bash):

```powershell
# CRITICAL: Always use "python -m pip" — see Python issue below
python -m pip install --upgrade pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
python -m pip install optuna xgboost
```

Then verify:
```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
# Expected: True + NVIDIA GeForce RTX 3060
```

### KNOWN ISSUE: Dual Python Installation
| What | Path | Version |
|------|------|---------|
| `python` command | `C:\Users\User\AppData\Local\Microsoft\WindowsApps\...Python.3.13_...\python.exe` | **3.13.12** (Microsoft Store) |
| `pip` command | `C:\Users\User\AppData\Local\Programs\Python\Python314\Scripts\pip.exe` | Points to **3.14** |

**Problem**: `pip install X` installs to Python 3.14, but `python` runs 3.13. Packages installed via bare `pip` are invisible to `python`.

**Fix**: Always use `python -m pip install ...` — this ensures packages go to the same Python that runs your code.

Packages already on Python 3.14 (NOT accessible from 3.13):
- torch 2.10.0, optuna 4.7.0, xgboost 3.1.3

These need to be reinstalled via `python -m pip` to be usable.

---

## 2. Data Pipeline — DONE

### Fetcher Script
- **File**: `PROJECTS/four-pillars-backtester/scripts/fetch_sub_1b.py`
- **Standalone**: Runs independently from PowerShell
- **Source**: Bybit v5 API (public, no auth) + CoinGecko (free tier, market caps)

### Overnight Fetch Results (2026-02-08)
| Metric | Count |
|--------|-------|
| Total coins discovered | 394 (sub-$1B market cap on Bybit) |
| Successfully fetched | 363 |
| Failed (rate limited) | 31 |
| Full data (>3MB, 3 months) | 299 |
| Partial/tiny data | 70 |
| Total candles | 38.5 million |
| Total size on disk | 1.36 GB |
| Data quality (299 full) | **ZERO gaps, ZERO NaN, ZERO dupes, ZERO bad prices** |

### Files
| File | Purpose |
|------|---------|
| `data/sub_1b_coins.json` | 394 coins sorted by market cap descending ($975M → $13M) |
| `data/refetch_list.json` | 101 coins to re-fetch (31 failed + 70 incomplete) |
| `data/fetch_log.txt` | Full fetch log (2479 lines) |
| `data/cache/*.parquet` | 369 Parquet files, 1m candles |

### Refetch Command (user runs from PowerShell)
The `--refetch` flag still needs to be added to fetch_sub_1b.py. Currently you'd need to use `--start-from SYMBOL` to resume. TODO for next session: add `--refetch` flag that reads refetch_list.json.

### Known Issues
- **RIVER and SAND got overwritten**: Original 3-month data (129,600 candles each) was overwritten with short fetches during the sub-$1B run. These are in the refetch list.
- **Rate limit burst**: 31 coins failed around 20:39 when Bybit throttled. The script retries individual pages but doesn't back off long enough between consecutive coin failures.

---

## 3. Backtester — DONE (v3.7.1 logic)

### Project Structure
```
PROJECTS/four-pillars-backtester/
├── engine/
│   ├── backtester.py          # Main bar-by-bar loop
│   ├── position.py            # Position tracking, MFE/MAE, BE raise
│   ├── commission.py          # $6/side + daily 5pm UTC rebate settlement
│   └── metrics.py             # Win rate, expectancy, Sharpe, Sortino, MFE/MAE
├── signals/
│   ├── stochastics.py         # Raw K stochastics (9/14/40/60)
│   ├── clouds.py              # Ripster EMA clouds (5/12, 34/50, 72/89)
│   ├── state_machine.py       # A/B/C signal grading + re-entry
│   └── four_pillars.py        # Orchestrator: indicators → state machine → signals
├── exits/
│   ├── static_atr.py          # v3.7.1: fixed SL/TP + BE raise
│   ├── cloud_trail.py         # v3.5.1: Cloud 3/4 trail
│   ├── avwap_trail.py         # v3.6: AVWAP trail
│   └── phased.py              # ATR-SL spec: Cloud 2→3→4 phase progression
├── optimizer/
│   ├── grid_search.py         # Coarse parameter sweep
│   ├── bayesian.py            # Optuna refinement
│   ├── ml_regime.py           # PyTorch/XGBoost regime model
│   └── monte_carlo.py         # 10,000-iteration validation
├── data/
│   ├── fetcher.py             # BybitFetcher (primary) + WEEXFetcher (live only)
│   ├── sub_1b_coins.json      # 394 coin list
│   ├── refetch_list.json      # 101 coins to re-fetch
│   └── cache/                 # 369 Parquet files (1.36 GB)
├── scripts/
│   ├── fetch_sub_1b.py        # Standalone sub-$1B coin fetcher
│   ├── fetch_data.py          # CLI entry point for Bybit data fetch
│   ├── sweep_low_price.py     # BE sweep on 5 low-price coins
│   ├── run_backtest.py        # Main backtest runner
│   └── dashboard.py           # Streamlit dashboard
└── requirements.txt
```

### Backtest Results (5m, 3 months, v3.7.1)

| Coin | Best BE | Trades | WR% | Net P&L | $/trade | LSG% |
|------|---------|--------|-----|---------|---------|------|
| 1000PEPE | $2 | 4,145 | 17.6% | +$10,436 | +$2.52 | 83.3% |
| RIVER | $4 | 4,003 | 16.8% | +$55,855 | +$13.95 | 83.2% |
| KITE | $2 | 3,994 | 18.9% | +$14,979 | +$3.75 | 79.2% |
| HYPE | $10 | 4,124 | 13.7% | +$7,218 | +$1.75 | 84.2% |
| SAND | $6 | 4,017 | 18.9% | +$8,572 | +$2.13 | 77.4% |
| **Total** | | **20,283** | | **+$97,060** | **+$4.79** | |

### Max Consecutive Losses (5m)
| Coin | MCL Streak | $ Cost of Worst Streak |
|------|-----------|----------------------|
| 1000PEPE | 38 | $664 |
| RIVER | 30 | $537 |
| KITE | 34 | $631 |
| HYPE | 51 | $1,066 |
| SAND | 36 | $748 |

---

## 4. What's PENDING

### Immediate (next session)
1. **Install PyTorch with CUDA** — commands above in Section 1
2. **Add `--refetch` flag** to fetch_sub_1b.py → reads refetch_list.json, force-fetches 101 coins
3. **Improve rate limit handling** — when Bybit returns "Too many visits", back off 30-60s before next coin (not just retry same page)
4. **Re-fetch RIVER + SAND** — original data got overwritten

### v3.8 ATR-Based BE Logic
- **MUST be in separate files** — do NOT modify existing engine/position.py
- Plan at: `02-STRATEGY/Indicators/FOUR-PILLARS-V3.8-PLAN.md`
- ATR-based trigger/lock replaces fixed $ amounts
- Optional stepped profit trail (off by default)
- Commission may be $4/side (0.04%) not $6 — needs verification

### Full 299-Coin Backtest
- Run all 299 complete coins through v3.7.1 backtester on 5m
- Rank by expectancy ($/trade)
- Find the "RIVER-like" coins (high ATR/price ratio, commission < 10% of TP win)

### ML Optimizer (WS4) — Needs CUDA first
1. Grid search — coarse sweep of SL/TP/BE/cooldown params
2. Bayesian (Optuna) — refine promising regions
3. ML regime model (PyTorch on GPU) — optimal params per market regime

### Workflow Chart
- User wants a printable process chart for the week
- Use **draw.io** (diagrams.net) or **Mermaid Live Editor** (mermaid.live)
- Mermaid flowchart already exists in master plan: `C:\Users\User\.claude\plans\warm-waddling-wren.md`
- Paste the mermaid code block from that file into mermaid.live → export PNG/PDF → print

---

## 5. Key Reference Files

| File | What |
|------|------|
| `02-STRATEGY/Indicators/four_pillars_v3_7_1_strategy.pine` | Current Pine Script strategy |
| `02-STRATEGY/Indicators/FOUR-PILLARS-V3.8-PLAN.md` | v3.8 upgrade plan |
| `07-BUILD-JOURNAL/2026-02-07-backtest-results.md` | Full backtest results with analysis |
| `C:\Users\User\.claude\plans\warm-waddling-wren.md` | Master execution plan (WS1-WS5) with Mermaid flowchart |
| `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\MEMORY.md` | Persistent project memory |

---

## 6. Commission Math (reference)

```
$500 margin × 20x leverage = $10,000 notional
0.06% taker × $10,000 = $6/side = $12 round trip
70% rebate account: $3.60/RT net
50% rebate account: $6.00/RT net
Rebates settle daily at 5pm UTC
```

Use `strategy.commission.cash_per_order` with value=6 in Pine Script.
NEVER use `commission.percent` with leverage — it's ambiguous.

---

## 7. Critical Lessons (carry forward)

- **5m > 1m for all coins** — fewer trades = less commission bleed
- **Raw K stochastics** — smooth=1, NEVER apply SMA to K
- **ATR/price ratio matters** — RIVER works ($13.95/tr), BTC doesn't (commission = 46% of TP)
- **LSG 68-84%** — most losers were profitable at some point, BE raise is the #1 lever
- **No strategy.close_all() for flips** — causes phantom double trades
- **strategy.cancel() stale exits before flipping**
- **Bybit pagination** — returns newest-first, paginate backward from end_ms
- **python -m pip** — always, because bare pip points to wrong Python

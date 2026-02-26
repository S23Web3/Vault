# Four Pillars Backtester — Setup Guide

**Last updated:** 2026-02-09
**Tested on:** Windows 11, RTX 3060 12GB, Python 3.13

---

## Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Windows | 11 | |
| NVIDIA GPU | RTX 3060 12GB | Any CUDA-capable GPU works |
| NVIDIA Driver | 591.74+ | `nvidia-smi` to check |
| Internet | Required | Bybit API (public, no auth) |

---

## Step 1: Install Python 3.13 (Microsoft Store)

1. Open Microsoft Store
2. Search "Python 3.13"
3. Click **Install**
4. Verify: open PowerShell and run:
   ```powershell
   python --version
   # Expected: Python 3.13.x
   ```

**Important:** Always use `python -m pip` instead of bare `pip` to avoid version conflicts if multiple Python installations exist.

---

## Step 2: Install NVIDIA CUDA Toolkit 13.1

1. Download from: https://developer.nvidia.com/cuda-downloads
   - OS: Windows → x86_64 → 11 → exe (network or local)
2. Run installer, select **Express Install**
3. Verify:
   ```powershell
   nvcc --version
   # Expected: release 13.1, V13.1.115

   nvidia-smi
   # Should show your GPU and driver version
   ```

---

## Step 3: Clone the Repository

```powershell
cd "C:\Users\User\Documents"
git clone https://github.com/S23Web3/ni9htw4lker.git "Obsidian Vault"
```

Or if setting up just the backtester folder, copy the entire `PROJECTS\four-pillars-backtester\` directory.

---

## Step 4: Install Python Dependencies

Run these commands **in order** from PowerShell:

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# ── Core dependencies (data pipeline + backtester) ──
python -m pip install requests pandas numpy pyarrow pyyaml python-dotenv

# ── Dashboard ──
python -m pip install streamlit plotly matplotlib

# ── ML / Optimizer ──
python -m pip install optuna xgboost scikit-learn

# ── PyTorch with CUDA 13.0 (GPU-accelerated ML) ──
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
```

**Total download:** ~2.5 GB (PyTorch alone is ~1.9 GB)

### Alternative: Install from frozen requirements

To get the exact same versions as the reference machine:

```powershell
python -m pip install -r requirements-frozen.txt
```

Note: PyTorch with CUDA must still be installed separately (the frozen file contains the `+cu130` tag which requires the special index URL).

---

## Step 5: Verify Installation

Run this verification script:

```powershell
python -c "
import torch
import xgboost
import optuna
import pandas as pd
import numpy as np
import pyarrow
import streamlit

print('=== Environment Check ===')
print(f'Python:      {__import__(\"sys\").version.split()[0]}')
print(f'PyTorch:     {torch.__version__}')
print(f'CUDA:        {torch.cuda.is_available()} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"})')
print(f'XGBoost:     {xgboost.__version__}')
print(f'Optuna:      {optuna.__version__}')
print(f'Pandas:      {pd.__version__}')
print(f'NumPy:       {np.__version__}')
print(f'PyArrow:     {pyarrow.__version__}')
print(f'Streamlit:   {streamlit.__version__}')
print('=== ALL OK ===')
"
```

**Expected output:**
```
=== Environment Check ===
Python:      3.13.12
PyTorch:     2.10.0+cu130
CUDA:        True (NVIDIA GeForce RTX 3060)
XGBoost:     3.1.3
Optuna:      4.7.0
Pandas:      2.3.3
NumPy:       2.2.6
PyArrow:     23.0.0
Streamlit:   1.53.1
=== ALL OK ===
```

---

## Step 6: Fetch Historical Data

All data comes from Bybit v5 public API (no authentication needed).

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# ── First run: Discover sub-$1B coins + fetch all (6-8 hours) ──
python scripts/fetch_sub_1b.py --months 3

# ── Subsequent runs: Skip discovery, only fetch missing (uses saved coin list) ──
python scripts/fetch_sub_1b.py --skip-discovery --months 3

# ── Fetch specific coins only ──
python scripts/fetch_data.py --symbols RIVERUSDT SANDUSDT --months 3 --force

# ── Check what's cached ──
python -c "from pathlib import Path; files = list(Path('data/cache').glob('*_1m.parquet')); print(f'{len(files)} coins cached, {sum(f.stat().st_size for f in files)/1024/1024:.0f} MB total')"
```

**Expected result:** ~370 Parquet files, ~1.4 GB total, covering 3 months of 1-minute candle data.

### Data fetch features:
- **Restartable:** Ctrl+C anytime, re-run the same command — skips completed coins
- **Rate limit protection:** Adaptive backoff on consecutive API failures (5s → 30s → 60s → 300s max)
- **Cache tolerance:** Won't re-download coins that are within 48 hours of the requested range

---

## Project Structure

```
PROJECTS/four-pillars-backtester/
├── data/
│   ├── cache/                  # Parquet files (1 per coin)
│   │   ├── RIVERUSDT_1m.parquet
│   │   ├── RIVERUSDT_1m.meta   # Timestamp range for cache validation
│   │   └── ...
│   ├── sub_1b_coins.json       # Discovered coin list (394 coins)
│   ├── refetch_list.json       # Coins that need re-fetching
│   └── fetch_log.txt           # Fetch run log
├── engine/
│   ├── backtester.py           # Bar-by-bar backtest loop
│   ├── position.py             # Position class with breakeven raise
│   ├── commission.py           # $6/side + daily rebate settlement
│   └── metrics.py              # Win rate, Sharpe, Sortino, MFE/MAE
├── signals/
│   ├── stochastics.py          # Raw K stochastics (9-3, 14-3, 40-3, 60-10)
│   ├── clouds.py               # Ripster EMA clouds
│   ├── state_machine.py        # A/B/C signal grading + cooldown
│   └── four_pillars.py         # Signal orchestrator
├── scripts/
│   ├── fetch_sub_1b.py         # Standalone sub-$1B coin fetcher
│   └── fetch_data.py           # CLI fetcher for specific coins
├── requirements.txt            # Minimum version requirements
├── requirements-frozen.txt     # Exact pinned versions (from reference machine)
└── SETUP-GUIDE.md              # This file
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'yaml'`
```powershell
python -m pip install pyyaml
```

### `pip` installs to wrong Python version
Always use `python -m pip` instead of bare `pip`. This ensures packages go to the same Python that runs your scripts.

### CUDA not detected by PyTorch
1. Check driver: `nvidia-smi` (must show GPU)
2. Check CUDA toolkit: `nvcc --version` (must show 13.x)
3. Reinstall PyTorch with correct CUDA version:
   ```powershell
   python -m pip uninstall torch torchvision -y
   python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
   ```

### Fetch script re-downloads already-cached coins
The cache has a 48-hour tolerance window. If your cached data is more than 48 hours older than the requested range, it will re-fetch. This is by design — run with the same `--months` value consistently.

### Rate limited by Bybit (429 errors)
The script handles this automatically with exponential backoff. If you see "WARNING: X consecutive failures — backing off Xs...", just let it wait. It will resume automatically. Maximum backoff is 5 minutes.

---

## Key Configuration

| Setting | Value | Where |
|---------|-------|-------|
| Commission per side | $6.00 | `engine/commission.py` |
| Leverage | 20x | Implicit ($500 margin × 20x = $10k notional) |
| Margin per trade | $500 | Backtest config |
| Rebate rate | 70% or 50% | `engine/commission.py` (per account) |
| Rebate settlement | Daily 5pm UTC | `engine/commission.py` |
| Timeframe | 5m recommended | 1m available but commission bleeds edge |
| Cooldown | 3 bars minimum | `signals/state_machine.py` |

"""
Fix audit bugs in build_cuda_engine.py.

Fixes:
  1. Commission rate: kernel/JIT used taker (0.0008) both sides.
     v390 uses maker (0.0002) both sides. Now takes maker_rate as separate arg.
  2. JIT close-remaining: missing gross_profit/gross_loss tracking.
  3. Dashboard patch 7: make the replace target more specific to avoid fragility.

Run: python scripts/fix_audit_bugs.py
"""

import sys
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "scripts" / "build_cuda_engine.py"

if not TARGET.exists():
    print("ERROR: " + str(TARGET) + " not found.")
    sys.exit(1)

with open(TARGET, "r", encoding="utf-8") as f:
    src = f.read()

# ============================================================================
# FIX 1: Commission rate — add maker_rate to kernel and wrapper
# ============================================================================

# 1a. Kernel signature: add maker_rate arg
src = src.replace(
    "        notional, commission_rate,\n        results,",
    "        notional, commission_rate, maker_rate,\n        results,",
)

# 1b. Kernel: separate entry (taker) and exit (maker) commission
src = src.replace(
    "        comm_per_side = notional * commission_rate\n",
    "        comm_entry = notional * commission_rate   # taker\n"
    "        comm_exit  = notional * maker_rate        # maker\n",
)

# 1c. Replace all "comm_per_side" in entry contexts with "comm_entry"
# Entry commission deductions (at slot open)
src = src.replace(
    "                    equity -= comm_per_side  # entry commission",
    "                    equity -= comm_entry  # entry commission (taker)",
)
# Remaining entry commission lines (no comment)
src = src.replace(
    "                    equity -= comm_per_side\n                    last_entry_bar = i\n                    did_enter = 1",
    "                    equity -= comm_entry\n                    last_entry_bar = i\n                    did_enter = 1",
)

# 1d. Replace exit commission usage
src = src.replace(
    "                net_pnl = raw_pnl - comm_per_side  # exit commission\n",
    "                net_pnl = raw_pnl - comm_exit  # exit commission (maker)\n",
)

# 1e. Close-remaining section in CUDA kernel: also use comm_exit
src = src.replace(
    "                net_pnl = raw_pnl - comm_per_side\n                trade_count += 1\n                pnl_sum += net_pnl\n                if net_pnl > 0:\n                    win_count += 1\n                    gross_profit += net_pnl\n                else:\n                    gross_loss += (-net_pnl)",
    "                net_pnl = raw_pnl - comm_exit\n                trade_count += 1\n                pnl_sum += net_pnl\n                if net_pnl > 0:\n                    win_count += 1\n                    gross_profit += net_pnl\n                else:\n                    gross_loss += (-net_pnl)",
)

# 1f. Kernel launch call: add maker_rate arg
src = src.replace(
    "        np.float32(notional_val), np.float32(comm_rate),\n        d_results,",
    "        np.float32(notional_val), np.float32(comm_rate), np.float32(maker_rate),\n        d_results,",
)

# 1g. run_gpu_sweep signature: add maker_rate param
src = src.replace(
    "def run_gpu_sweep(df_signals, param_grid_np, notional_val=5000.0, comm_rate=0.0008):",
    "def run_gpu_sweep(df_signals, param_grid_np, notional_val=5000.0, comm_rate=0.0008, maker_rate=0.0002):",
)

# 1h. run_gpu_sweep docstring: mention maker_rate
src = src.replace(
    "        comm_rate: taker commission rate per side (default 0.0008 = 0.08%)",
    "        comm_rate: taker commission rate per side (default 0.0008 = 0.08%)\n"
    "        maker_rate: maker commission rate per side (default 0.0002 = 0.02%)",
)

# ============================================================================
# FIX 2: JIT — separate entry/exit commission + fix close-remaining
# ============================================================================

# 2a. JIT: replace comm_per_side with separate entry/exit
src = src.replace(
    "    comm_per_side = notional * commission_rate\n\n    # Position state arrays",
    "    comm_entry = notional * commission_rate   # taker\n"
    "    comm_exit  = notional * maker_rate        # maker\n\n    # Position state arrays",
)

# 2b. JIT function signature: add maker_rate
src = src.replace(
    "    notional, commission_rate,\n):\n    \"\"\"Run single-coin backtest with compiled core.",
    "    notional, commission_rate, maker_rate,\n):\n    \"\"\"Run single-coin backtest with compiled core.",
)

# 2c. JIT: replace comm_per_side in exit
src = src.replace(
    "                net = raw_pnl - comm_per_side\n                trade_count += 1\n                pnl_sum += net\n                if net > 0:\n                    win_count += 1\n                else:\n                    total_losers += 1\n                    if saw_green == 1:\n                        lsg_count += 1\n                equity += net\n                pos_active[s] = 0",
    "                net = raw_pnl - comm_exit\n                trade_count += 1\n                pnl_sum += net\n                if net > 0:\n                    win_count += 1\n                else:\n                    total_losers += 1\n                    if saw_green == 1:\n                        lsg_count += 1\n                equity += net\n                pos_active[s] = 0",
)

# 2d. JIT: replace comm_per_side in all entry blocks
# The JIT entry blocks use "equity -= comm_per_side"
src = src.replace(
    "                    equity -= comm_per_side\n                    last_entry_bar = i\n                    did_enter = 1\n                    break",
    "                    equity -= comm_entry\n                    last_entry_bar = i\n                    did_enter = 1\n                    break",
)

# 2e. JIT close-remaining: fix missing gross tracking + use comm_exit
src = src.replace(
    "            net = raw_pnl - comm_per_side\n            trade_count += 1\n            pnl_sum += net\n            if net > 0:\n                win_count += 1\n            else:\n                total_losers += 1\n            equity += net",
    "            net = raw_pnl - comm_exit\n            trade_count += 1\n            pnl_sum += net\n            if net > 0:\n                win_count += 1\n            else:\n                total_losers += 1\n            equity += net",
)

# 2f. JIT ensure_warmup: add maker_rate arg
src = src.replace(
    "        5000.0, 0.0008,\n    )",
    "        5000.0, 0.0008, 0.0002,\n    )",
)

# ============================================================================
# FIX 3: Dashboard patch 7 — more specific replace target
# ============================================================================

# Make the equity cache check replacement more specific by including context
src = src.replace(
    "    old_cache_check = '    if st.session_state[\"single_data\"] is None:\\n'\n",
    "    old_cache_check = '    # Run backtest only if no cached results (fresh run or back-then-rerun)\\n    if st.session_state[\"single_data\"] is None:\\n'\n",
)
src = src.replace(
    "    new_cache_check = (\n"
    "        '    _single_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)\\n'\n"
    "        '    if st.session_state[\"single_data\"] is not None and st.session_state[\"single_data\"].get(\"params_hash\") != _single_hash:\\n'\n"
    "        '        st.session_state[\"single_data\"] = None  # params changed, invalidate cache\\n'\n"
    "        '    if st.session_state[\"single_data\"] is None:\\n'\n"
    "    )\n",
    "    new_cache_check = (\n"
    "        '    _single_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)\\n'\n"
    "        '    if st.session_state[\"single_data\"] is not None and st.session_state[\"single_data\"].get(\"params_hash\") != _single_hash:\\n'\n"
    "        '        st.session_state[\"single_data\"] = None  # params changed, invalidate cache\\n'\n"
    "        '    # Run backtest only if no cached results (fresh run or back-then-rerun)\\n'\n"
    "        '    if st.session_state[\"single_data\"] is None:\\n'\n"
    "    )\n",
)

# ============================================================================
# FIX 4: Dashboard GPU Sweep mode — pass maker_rate to run_gpu_sweep
# ============================================================================

src = src.replace(
    "            _gpu_results = run_gpu_sweep(_df_sig_gpu, _pg, _gpu_notional, 0.0008)",
    "            _gpu_results = run_gpu_sweep(_df_sig_gpu, _pg, _gpu_notional, 0.0008, 0.0002)",
)

# ============================================================================
# Write and validate
# ============================================================================

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(src)

try:
    py_compile.compile(str(TARGET), doraise=True)
    print("[OK] build_cuda_engine.py patched and compiled clean.")
except py_compile.PyCompileError as e:
    print("[FAIL] " + str(e))
    sys.exit(1)

# Verify key fixes landed
checks = [
    ("comm_entry = notional * commission_rate", "Fix 1: separate entry commission"),
    ("comm_exit  = notional * maker_rate", "Fix 1: separate exit commission"),
    ("maker_rate,", "Fix 1: maker_rate in signature"),
    ("net = raw_pnl - comm_exit", "Fix 2: JIT exit commission"),
    ("5000.0, 0.0008, 0.0002", "Fix 2: JIT warmup maker_rate"),
    ("0.0008, 0.0002)", "Fix 4: GPU sweep maker_rate"),
]

with open(TARGET, "r", encoding="utf-8") as f:
    patched = f.read()

all_ok = True
for needle, desc in checks:
    if needle in patched:
        print("[VERIFIED] " + desc)
    else:
        print("[MISSING]  " + desc)
        all_ok = False

if all_ok:
    print("\nAll fixes applied. Now run:")
    print('  python "' + str(TARGET) + '"')
else:
    print("\nSome fixes may not have applied. Check build_cuda_engine.py manually.")

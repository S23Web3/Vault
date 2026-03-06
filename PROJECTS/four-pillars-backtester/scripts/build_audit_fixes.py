"""
Build script: apply audit fixes to 4 files.
Fixes: CRITICAL #1+#2 (commission split + pnl_sum), HIGH #3 (win_rate%), HIGH #5 (WSListener),
       HIGH #6 (reduceOnly), HIGH #7 (saw_green).
Run: python scripts/build_audit_fixes.py
"""
import ast
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BINGX = ROOT.parent / "bingx-connector"

ERRORS = []


def verify(path):
    """Run py_compile + ast.parse on path. Print result, append to ERRORS on fail."""
    p = str(path)
    try:
        py_compile.compile(p, doraise=True)
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        ERRORS.append(p)
        return False
    try:
        source = Path(p).read_text(encoding="utf-8")
        ast.parse(source, filename=p)
    except SyntaxError as e:
        print("  AST ERROR in " + p + " line " + str(e.lineno) + ": " + str(e.msg))
        ERRORS.append(p)
        return False
    print("  OK: " + p)
    return True


def patch_file(path, replacements, label):
    """Apply list of (old, new) string replacements to a file. Abort on missing match."""
    text = Path(path).read_text(encoding="utf-8")
    for i, (old, new) in enumerate(replacements):
        if old not in text:
            print("  PATCH MISSING [" + label + " patch " + str(i + 1) + "]: target string not found")
            print("  Target: " + repr(old[:80]))
            ERRORS.append(str(path) + " patch " + str(i + 1))
            return False
        text = text.replace(old, new, 1)
    Path(path).write_text(text, encoding="utf-8")
    print("  Patched: " + str(path))
    return True


# ─────────────────────────────────────────────────────────────────────────────
# FILE 1: engine/cuda_sweep.py
# Fixes: CRITICAL #1 (commission split), CRITICAL #2 (pnl_sum), HIGH #7 (saw_green)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== cuda_sweep.py ===")
cuda_path = ROOT / "engine" / "cuda_sweep.py"

cuda_patches = [
    # Patch A: kernel signature — add maker_rate param
    (
        "    param_grid, N, N_combos,\n        notional, commission_rate,\n        results,",
        "    param_grid, N, N_combos,\n        notional, commission_rate, maker_rate,\n        results,",
    ),
    # Patch B: split comm_per_side into entry_comm + exit_comm
    (
        "        comm_per_side = notional * commission_rate\n",
        "        entry_comm = notional * commission_rate\n        exit_comm = notional * maker_rate\n",
    ),
    # Patch C1: entry commission Grade A long
    (
        "                    equity -= comm_per_side  # entry commission\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # Grade A short",
        "                    equity -= entry_comm  # entry commission (taker)\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # Grade A short",
    ),
    # Patch C2: entry commission Grade A short
    (
        "                    equity -= comm_per_side\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # Grade B long",
        "                    equity -= entry_comm  # entry commission (taker)\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # Grade B long",
    ),
    # Patch C3: entry commission Grade B long
    (
        "                    equity -= comm_per_side\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # Grade B short",
        "                    equity -= entry_comm  # entry commission (taker)\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # Grade B short",
    ),
    # Patch C4: entry commission Grade B short
    (
        "                    equity -= comm_per_side\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # RE long",
        "                    equity -= entry_comm  # entry commission (taker)\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # RE long",
    ),
    # Patch C5: entry commission RE long
    (
        "                    equity -= comm_per_side\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # RE short",
        "                    equity -= entry_comm  # entry commission (taker)\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # RE short",
    ),
    # Patch C6: entry commission RE short
    (
        "                    equity -= comm_per_side\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # ── Track peak equity",
        "                    equity -= entry_comm  # entry commission (taker)\n                    last_entry_bar = i\n                    did_enter = 1\n\n            # ── Track peak equity",
    ),
    # Patch D: main exit — split commission, include entry_comm in pnl_sum
    (
        "                    net_pnl = raw_pnl - comm_per_side  # exit commission\n\n                    trade_count += 1\n                    pnl_sum += net_pnl",
        "                    net_pnl = raw_pnl - exit_comm  # exit commission (maker)\n                    pnl_sum_pnl = net_pnl - entry_comm  # full round-trip for pnl_sum\n\n                    trade_count += 1\n                    pnl_sum += pnl_sum_pnl",
    ),
    # Patch D2: adjust win/loss check — use pnl_sum_pnl for win, gross p/l
    (
        "                    if net_pnl > 0:\n                        win_count += 1\n                        gross_profit += net_pnl\n                    else:\n                        gross_loss += (-net_pnl)\n                        total_losers += 1\n                        if saw_green == 1:\n                            lsg_count += 1\n\n                    # Welford update\n                    wf_n += 1\n                    delta = net_pnl - wf_mean",
        "                    if pnl_sum_pnl > 0:\n                        win_count += 1\n                        gross_profit += pnl_sum_pnl\n                    else:\n                        gross_loss += (-pnl_sum_pnl)\n                        total_losers += 1\n                        if saw_green == 1:\n                            lsg_count += 1\n\n                    # Welford update\n                    wf_n += 1\n                    delta = pnl_sum_pnl - wf_mean",
    ),
    # Patch D3: Welford wf_M2 uses pnl_sum_pnl
    (
        "                    wf_M2 += delta * (net_pnl - wf_mean)\n\n                    equity += net_pnl",
        "                    wf_M2 += delta * (pnl_sum_pnl - wf_mean)\n\n                    equity += net_pnl",
    ),
    # Patch E: end-of-backtest close — same treatment
    (
        "                net_pnl = raw_pnl - comm_per_side\n                trade_count += 1\n                pnl_sum += net_pnl\n                if net_pnl > 0:\n                    win_count += 1\n                    gross_profit += net_pnl\n                else:\n                    gross_loss += (-net_pnl)",
        "                net_pnl = raw_pnl - exit_comm  # exit commission (maker)\n                pnl_sum_pnl = net_pnl - entry_comm  # full round-trip for pnl_sum\n                trade_count += 1\n                pnl_sum += pnl_sum_pnl\n                if pnl_sum_pnl > 0:\n                    win_count += 1\n                    gross_profit += pnl_sum_pnl\n                else:\n                    gross_loss += (-pnl_sum_pnl)",
    ),
    # Patch E2: end-of-backtest Welford
    (
        "                wf_n += 1\n                delta = net_pnl - wf_mean\n                wf_mean += delta / float32(wf_n)\n                wf_M2 += delta * (net_pnl - wf_mean)\n                equity += net_pnl",
        "                wf_n += 1\n                delta = pnl_sum_pnl - wf_mean\n                wf_mean += delta / float32(wf_n)\n                wf_M2 += delta * (pnl_sum_pnl - wf_mean)\n                equity += net_pnl",
    ),
    # Patch F1: saw_green LONG — >= instead of >
    (
        "                    if high[i] > pos_entry[s]:\n                        saw_green = 1",
        "                    if high[i] >= pos_entry[s]:\n                        saw_green = 1",
    ),
    # Patch F2: saw_green SHORT — <= instead of <
    (
        "                    if low[i] < pos_entry[s]:\n                        saw_green = 1",
        "                    if low[i] <= pos_entry[s]:\n                        saw_green = 1",
    ),
    # Patch G: run_gpu_sweep signature + docstring + kernel call
    (
        "def run_gpu_sweep(df_signals, param_grid_np, notional_val=5000.0, comm_rate=0.0008):\n    \"\"\"Run GPU sweep. Returns DataFrame with results sorted by net_pnl descending.\n\n    Args:\n        df_signals: DataFrame with signal columns from compute_signals() v3.9.0.\n            Required columns: close, high, low, atr,\n            long_a, long_b, short_a, short_b, reentry_long, reentry_short,\n            cloud3_allows_long, cloud3_allows_short\n        param_grid_np: [N_combos, 4] float32 array from build_param_grid()\n        notional_val: position notional (same for all combos)\n        comm_rate: taker commission rate per side (default 0.0008 = 0.08%)\n\n    Returns:\n        DataFrame with columns: sl_mult, tp_mult, be_trigger_atr, cooldown,\n        total_trades, win_rate, net_pnl, expectancy, max_dd_pct,\n        profit_factor, lsg_pct, sharpe\n    \"\"\"",
        "def run_gpu_sweep(df_signals, param_grid_np, notional_val=5000.0, comm_rate=0.0008, maker_rate=0.0002):\n    \"\"\"Run GPU sweep. Returns DataFrame with results sorted by net_pnl descending.\n\n    Args:\n        df_signals: DataFrame with signal columns from compute_signals() v3.9.0.\n            Required columns: close, high, low, atr,\n            long_a, long_b, short_a, short_b, reentry_long, reentry_short,\n            cloud3_allows_long, cloud3_allows_short\n        param_grid_np: [N_combos, 4] float32 array from build_param_grid()\n        notional_val: position notional (same for all combos)\n        comm_rate: taker commission rate per side entry (default 0.0008 = 0.08%)\n        maker_rate: maker commission rate per side exit (default 0.0002 = 0.02%)\n\n    Returns:\n        DataFrame with columns: sl_mult, tp_mult, be_trigger_atr, cooldown,\n        total_trades, win_rate, net_pnl, expectancy, max_dd_pct,\n        profit_factor, lsg_pct, sharpe\n    \"\"\"",
    ),
    # Patch G2: kernel call — add maker_rate argument
    (
        "        np.float32(notional_val), np.float32(comm_rate),\n        d_results,",
        "        np.float32(notional_val), np.float32(comm_rate), np.float32(maker_rate),\n        d_results,",
    ),
    # Patch H: run_gpu_sweep_multi signature + pass-through
    (
        "def run_gpu_sweep_multi(\n    coin_data_list,\n    param_grid_np,\n    notional_val=5000.0,\n    comm_rate=0.0008,\n    progress_callback=None,\n):\n    \"\"\"Run GPU sweep across multiple coins. Returns dict keyed by symbol.\n\n    Args:\n        coin_data_list: list of (symbol, df_signals) tuples.\n            Each df_signals must have the 12 required columns.\n        param_grid_np: [N_combos, 4] float32 array from build_param_grid()\n        notional_val: position notional per trade\n        comm_rate: taker commission rate per side\n        progress_callback: optional callable(current_idx, total, symbol)",
        "def run_gpu_sweep_multi(\n    coin_data_list,\n    param_grid_np,\n    notional_val=5000.0,\n    comm_rate=0.0008,\n    maker_rate=0.0002,\n    progress_callback=None,\n):\n    \"\"\"Run GPU sweep across multiple coins. Returns dict keyed by symbol.\n\n    Args:\n        coin_data_list: list of (symbol, df_signals) tuples.\n            Each df_signals must have the 12 required columns.\n        param_grid_np: [N_combos, 4] float32 array from build_param_grid()\n        notional_val: position notional per trade\n        comm_rate: taker commission rate per side entry\n        maker_rate: maker commission rate per side exit\n        progress_callback: optional callable(current_idx, total, symbol)",
    ),
    # Patch H2: run_gpu_sweep_multi inner call — pass maker_rate
    (
        "            df_result = run_gpu_sweep(df_signals, param_grid_np, notional_val, comm_rate)",
        "            df_result = run_gpu_sweep(df_signals, param_grid_np, notional_val, comm_rate, maker_rate)",
    ),
]

if patch_file(cuda_path, cuda_patches, "cuda_sweep"):
    verify(cuda_path)


# ─────────────────────────────────────────────────────────────────────────────
# FILE 2: scripts/dashboard_v394.py
# Fix: HIGH #3 — win_rate as fraction in 3 table locations
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== dashboard_v394.py ===")
dash_path = ROOT / "scripts" / "dashboard_v394.py"

dash_patches = [
    # Patch 1: GPU Sweep top-20 table — format win_rate% before display
    (
        '        # Top-20 table sorted by expectancy\n        st.subheader("Top 20 Combos (by expectancy)")\n        _top20 = _gpu_res.sort_values("expectancy", ascending=False).head(20).copy()\n        _top20["tp_mult"] = _top20["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))\n        _display_cols = [\n            "sl_mult", "tp_mult", "be_trigger_atr", "cooldown",\n            "total_trades", "win_rate", "net_pnl", "expectancy",\n            "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",\n        ]\n        st.dataframe(_top20[_display_cols], use_container_width=True)',
        '        # Top-20 table sorted by expectancy\n        st.subheader("Top 20 Combos (by expectancy)")\n        _top20 = _gpu_res.sort_values("expectancy", ascending=False).head(20).copy()\n        _top20["tp_mult"] = _top20["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))\n        _top20["win_rate"] = (_top20["win_rate"] * 100).round(1)\n        _top20 = _top20.rename(columns={"win_rate": "win_rate%"})\n        _display_cols = [\n            "sl_mult", "tp_mult", "be_trigger_atr", "cooldown",\n            "total_trades", "win_rate%", "net_pnl", "expectancy",\n            "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",\n        ]\n        st.dataframe(_top20[_display_cols], use_container_width=True)',
    ),
    # Patch 2: Uniform top-10 — format avg_win_rate% before display
    (
        '            _gp_uni_top10 = _gp_uniform_agg.head(10).copy()\n            _gp_uni_top10["tp_mult"] = _gp_uni_top10["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))\n            _gp_uni_top10["roi_pct"] = _gp_uni_top10["net_pnl"].apply(lambda x: round((x / _gp_deployed) * 100, 1) if _gp_deployed > 0 else 0.0)\n            st.dataframe(_gp_uni_top10, use_container_width=True)',
        '            _gp_uni_top10 = _gp_uniform_agg.head(10).copy()\n            _gp_uni_top10["tp_mult"] = _gp_uni_top10["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))\n            _gp_uni_top10["roi_pct"] = _gp_uni_top10["net_pnl"].apply(lambda x: round((x / _gp_deployed) * 100, 1) if _gp_deployed > 0 else 0.0)\n            _gp_uni_top10["avg_win_rate"] = (_gp_uni_top10["avg_win_rate"] * 100).round(1)\n            _gp_uni_top10 = _gp_uni_top10.rename(columns={"avg_win_rate": "avg_wr%"})\n            st.dataframe(_gp_uni_top10, use_container_width=True)',
    ),
    # Patch 3: Portfolio per-coin top-5 — format win_rate% before display
    (
        '                # Top 5 for this coin\n                _pc_top5 = _df_r.head(5).copy()\n                _pc_top5["tp_mult"] = _pc_top5["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))\n                st.dataframe(_pc_top5[[\n                    "sl_mult", "tp_mult", "be_trigger_atr", "cooldown",\n                    "total_trades", "win_rate", "net_pnl", "expectancy",\n                    "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",\n                ]], use_container_width=True)',
        '                # Top 5 for this coin\n                _pc_top5 = _df_r.head(5).copy()\n                _pc_top5["tp_mult"] = _pc_top5["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))\n                _pc_top5["win_rate"] = (_pc_top5["win_rate"] * 100).round(1)\n                _pc_top5 = _pc_top5.rename(columns={"win_rate": "win_rate%"})\n                st.dataframe(_pc_top5[[\n                    "sl_mult", "tp_mult", "be_trigger_atr", "cooldown",\n                    "total_trades", "win_rate%", "net_pnl", "expectancy",\n                    "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",\n                ]], use_container_width=True)',
    ),
]

if patch_file(dash_path, dash_patches, "dashboard_v394"):
    verify(dash_path)


# ─────────────────────────────────────────────────────────────────────────────
# FILE 3: bingx-connector/ws_listener.py
# Fix: HIGH #5 — MAX_RECONNECT 3->10, exponential backoff, dead flag file
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== ws_listener.py ===")
ws_path = BINGX / "ws_listener.py"

ws_patches = [
    # Patch 1: increase MAX_RECONNECT + note backoff
    (
        "MAX_RECONNECT = 3\nRECONNECT_DELAY = 5",
        "MAX_RECONNECT = 10\nRECONNECT_DELAY = 5  # base; actual = RECONNECT_DELAY * 2**min(reconnect_count, 5)",
    ),
    # Patch 2: fixed-delay sleep on listenKey failure — add backoff
    (
        "                self.log.error(\"Cannot obtain listenKey, retry in %ds\", RECONNECT_DELAY)\n                reconnect_count += 1\n                await asyncio.sleep(RECONNECT_DELAY)",
        "                backoff = RECONNECT_DELAY * (2 ** min(reconnect_count, 5))\n                self.log.error(\"Cannot obtain listenKey, retry in %ds (attempt %d/%d)\",\n                               backoff, reconnect_count + 1, MAX_RECONNECT)\n                reconnect_count += 1\n                await asyncio.sleep(backoff)",
    ),
    # Patch 3: fixed-delay sleep on WS exception — add backoff
    (
        "                if reconnect_count < MAX_RECONNECT:\n                    self.log.info(\"Reconnecting in %ds (attempt %d/%d)\",\n                                  RECONNECT_DELAY, reconnect_count, MAX_RECONNECT)\n                    await asyncio.sleep(RECONNECT_DELAY)",
        "                if reconnect_count < MAX_RECONNECT:\n                    backoff = RECONNECT_DELAY * (2 ** min(reconnect_count, 5))\n                    self.log.info(\"Reconnecting in %ds (attempt %d/%d)\",\n                                  backoff, reconnect_count, MAX_RECONNECT)\n                    await asyncio.sleep(backoff)",
    ),
    # Patch 4: after loop — upgrade to CRITICAL log + write dead flag
    (
        "        if reconnect_count >= MAX_RECONNECT:\n            self.log.error(\"Max reconnect attempts reached, WS listener stopping\")",
        "        if reconnect_count >= MAX_RECONNECT:\n            self.log.critical(\"WS LISTENER DEAD after %d reconnect attempts\", MAX_RECONNECT)\n            import datetime as _dt\n            _ts = _dt.datetime.utcnow().strftime(\"%Y%m%d_%H%M%S\")\n            _flag_dir = Path(\"logs\")\n            _flag_dir.mkdir(exist_ok=True)\n            _flag = _flag_dir / (\"ws_dead_\" + _ts + \".flag\")\n            _flag.write_text(\n                \"WS listener died at \" + _ts + \" after \" + str(MAX_RECONNECT) + \" reconnect attempts\",\n                encoding=\"utf-8\",\n            )\n            self.log.critical(\"Dead flag written: %s\", _flag)",
    ),
]

# ws_listener.py needs pathlib.Path — check import exists
ws_text = ws_path.read_text(encoding="utf-8")
if "from pathlib import Path" not in ws_text and "import pathlib" not in ws_text:
    ws_patches.insert(0, (
        "import requests\n",
        "import requests\nfrom pathlib import Path\n",
    ))

if patch_file(ws_path, ws_patches, "ws_listener"):
    verify(ws_path)


# ─────────────────────────────────────────────────────────────────────────────
# FILE 4: bingx-connector/position_monitor.py
# Fix: HIGH #6 — add defensive reduceOnly=true to _place_market_close
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== position_monitor.py ===")
pm_path = BINGX / "position_monitor.py"

pm_patches = [
    (
        '            "type": "MARKET",\n            "quantity": str(quantity),\n        }',
        '            "type": "MARKET",\n            "quantity": str(quantity),\n            "reduceOnly": "true",\n        }',
    ),
]

if patch_file(pm_path, pm_patches, "position_monitor"):
    verify(pm_path)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if ERRORS:
    print("BUILD FAILED — errors in: " + ", ".join(ERRORS))
    sys.exit(1)
else:
    print("BUILD OK — all 4 files patched and verified")
    print("")
    print("Files patched:")
    print("  " + str(ROOT / "engine" / "cuda_sweep.py"))
    print("  " + str(ROOT / "scripts" / "dashboard_v394.py"))
    print("  " + str(BINGX / "ws_listener.py"))
    print("  " + str(BINGX / "position_monitor.py"))
    print("")
    print("Run commands:")
    print("  Dashboard: streamlit run \"" + str(ROOT / "scripts" / "dashboard_v394.py") + "\"")
    print("  BingX bot: python \"" + str(BINGX / "main.py") + "\"")

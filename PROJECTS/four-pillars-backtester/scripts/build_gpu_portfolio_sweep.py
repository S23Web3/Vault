"""
Build script: GPU Portfolio Sweep mode for dashboard v3.9.4.

Patches TWO files:
  1. engine/cuda_sweep.py — adds run_gpu_sweep_multi() function
  2. scripts/dashboard_v394.py — adds GPU Portfolio Sweep mode + sidebar button

Features:
  - Multi-coin GPU sweep: loops coins on host, reuses CUDA kernel per coin
  - Coin selection: Top N / Lowest N / Random N / Custom (same as Portfolio Analysis)
  - Date range: 7d / 30d / 90d / 1y / All / Custom (reuses sidebar date_range)
  - Capital: Per-Coin Independent or Shared Pool ($X total, $Y per trade)
  - Results: per-coin best combo table, cross-coin aggregated heatmap, CSV export
  - Load/Save portfolio selections (reuses existing portfolio_manager)

Run: python scripts/build_gpu_portfolio_sweep.py
"""

import sys
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUDA_FILE = ROOT / "engine" / "cuda_sweep.py"
DASH_FILE = ROOT / "scripts" / "dashboard_v394.py"

ERRORS = []


def check_file(path, label):
    """Verify file exists."""
    if not path.exists():
        print("ERROR: " + str(path) + " not found.")
        ERRORS.append(label + " missing")
        return False
    return True


def patch_cuda_sweep():
    """Add run_gpu_sweep_multi() to engine/cuda_sweep.py."""
    if not check_file(CUDA_FILE, "cuda_sweep.py"):
        return

    with open(CUDA_FILE, "r", encoding="utf-8") as f:
        src = f.read()

    if "def run_gpu_sweep_multi" in src:
        print("[SKIP] run_gpu_sweep_multi already exists in cuda_sweep.py")
        return

    new_func = '''

def run_gpu_sweep_multi(
    coin_data_list,
    param_grid_np,
    notional_val=5000.0,
    comm_rate=0.0008,
    progress_callback=None,
):
    """Run GPU sweep across multiple coins. Returns dict keyed by symbol.

    Args:
        coin_data_list: list of (symbol, df_signals) tuples.
            Each df_signals must have the 12 required columns.
        param_grid_np: [N_combos, 4] float32 array from build_param_grid()
        notional_val: position notional per trade
        comm_rate: taker commission rate per side
        progress_callback: optional callable(current_idx, total, symbol)

    Returns:
        dict: {symbol: DataFrame} where each DataFrame has the same columns
              as run_gpu_sweep() output (params + 8 metrics).
    """
    results = {}
    total = len(coin_data_list)
    for idx, (symbol, df_signals) in enumerate(coin_data_list):
        if progress_callback is not None:
            progress_callback(idx, total, symbol)
        try:
            df_result = run_gpu_sweep(df_signals, param_grid_np, notional_val, comm_rate)
            results[symbol] = df_result
        except Exception:
            pass
    if progress_callback is not None:
        progress_callback(total, total, "done")
    return results
'''

    src += new_func

    with open(CUDA_FILE, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(str(CUDA_FILE), doraise=True)
        print("[OK] cuda_sweep.py patched — run_gpu_sweep_multi() added")
    except py_compile.PyCompileError as e:
        print("[FAIL] cuda_sweep.py: " + str(e))
        ERRORS.append("cuda_sweep py_compile")


def patch_dashboard():
    """Add GPU Portfolio Sweep mode to dashboard_v394.py."""
    if not check_file(DASH_FILE, "dashboard_v394.py"):
        return

    with open(DASH_FILE, "r", encoding="utf-8") as f:
        src = f.read()

    if "gpu_port_sweep" in src:
        print("[SKIP] gpu_port_sweep mode already exists in dashboard_v394.py")
        return

    # === PATCH 1: Session state init ===
    # Insert after gpu_sweep_symbol init
    old_session_init = (
        'if "gpu_sweep_symbol" not in st.session_state:\n'
        '    st.session_state["gpu_sweep_symbol"] = None'
    )
    new_session_init = (
        'if "gpu_sweep_symbol" not in st.session_state:\n'
        '    st.session_state["gpu_sweep_symbol"] = None\n'
        'if "gpu_port_results" not in st.session_state:\n'
        '    st.session_state["gpu_port_results"] = None\n'
        'if "gpu_port_symbols" not in st.session_state:\n'
        '    st.session_state["gpu_port_symbols"] = None'
    )
    if old_session_init in src:
        src = src.replace(old_session_init, new_session_init, 1)
        print("[PATCH 1] Session state init — added gpu_port_results, gpu_port_symbols")
    else:
        print("[WARN] Patch 1: session init target not found")
        ERRORS.append("patch 1 target missing")

    # === PATCH 2: Sidebar button ===
    # Insert after GPU Sweep button
    old_sidebar_btn = 'run_gpu_sweep = st.sidebar.button("GPU Sweep (CUDA)")'
    new_sidebar_btn = (
        'run_gpu_sweep = st.sidebar.button("GPU Sweep (CUDA)")\n'
        'run_gpu_port = st.sidebar.button("GPU Portfolio Sweep")'
    )
    if old_sidebar_btn in src:
        src = src.replace(old_sidebar_btn, new_sidebar_btn, 1)
        print("[PATCH 2] Sidebar button — added GPU Portfolio Sweep")
    else:
        print("[WARN] Patch 2: sidebar button target not found")
        ERRORS.append("patch 2 target missing")

    # === PATCH 3: Mode transition ===
    # Insert after gpu_sweep mode transition
    old_mode_trans = (
        'if run_gpu_sweep:\n'
        '    st.session_state["mode"] = "gpu_sweep"\n'
        '    st.session_state["gpu_sweep_results"] = None'
    )
    new_mode_trans = (
        'if run_gpu_sweep:\n'
        '    st.session_state["mode"] = "gpu_sweep"\n'
        '    st.session_state["gpu_sweep_results"] = None\n'
        'if run_gpu_port:\n'
        '    st.session_state["mode"] = "gpu_port_sweep"\n'
        '    st.session_state["gpu_port_results"] = None\n'
        '    st.session_state["gpu_port_symbols"] = None'
    )
    if old_mode_trans in src:
        src = src.replace(old_mode_trans, new_mode_trans, 1)
        print("[PATCH 3] Mode transition — added gpu_port_sweep")
    else:
        print("[WARN] Patch 3: mode transition target not found")
        ERRORS.append("patch 3 target missing")

    # === PATCH 4: Full GPU Portfolio Sweep mode block ===
    # Append after the last line of the file
    gpu_port_mode = '''
# ============================================================================
# GPU PORTFOLIO SWEEP MODE — Multi-coin CUDA parameter optimization
# ============================================================================
elif mode == "gpu_port_sweep":
    if st.button("Back to Settings"):
        st.session_state["mode"] = "settings"
        st.session_state["gpu_port_results"] = None
        st.session_state["gpu_port_symbols"] = None
        st.rerun()

    # CUDA availability check
    try:
        from engine.cuda_sweep import run_gpu_sweep_multi, build_param_grid, get_cuda_info
        from signals.four_pillars_v390 import compute_signals as compute_signals_v390
        _cuda_ok = True
    except ImportError as _imp_err:
        _cuda_ok = False
        _cuda_msg = str(_imp_err)

    if not _cuda_ok:
        st.error("CUDA engine not available: " + _cuda_msg)
        st.info("Run: python scripts/build_gpu_portfolio_sweep.py")
        st.stop()

    _gpu = get_cuda_info()
    if _gpu:
        st.caption("GPU: " + str(_gpu["device"]) + " | VRAM free: " + str(_gpu["vram_free_gb"]) + " GB")
    st.title("GPU Portfolio Sweep -- " + timeframe)

    # ── Coin Selection (same pattern as Portfolio Analysis) ──
    _gp_source = st.radio("Coin Selection", ["Top N", "Lowest N", "Random N", "Custom"],
        horizontal=True, key="gp_source")

    _gp_n = st.slider("N coins", 2, 50, 10, key="gp_n")

    _gp_sweep_csv = []
    if SWEEP_PROGRESS.exists():
        try:
            _gp_sdf = pd.read_csv(SWEEP_PROGRESS)
            if not _gp_sdf.empty and "Exp" in _gp_sdf.columns:
                _gp_sweep_csv = _gp_sdf.sort_values("Exp", ascending=False)["Symbol"].tolist()
        except Exception:
            pass

    _gp_locked = st.session_state.get("gpu_port_symbols")

    if _gp_source == "Custom":
        _gp_default = _gp_locked if _gp_locked is not None else cached[:min(5, len(cached))]
        _gp_default = [s for s in _gp_default if s in cached]
        _gp_symbols = st.multiselect("Select coins", cached, default=_gp_default, key="gp_custom_coins")
    elif _gp_locked is not None:
        _gp_symbols = _gp_locked
    elif _gp_source == "Top N":
        if _gp_sweep_csv:
            _gp_symbols = _gp_sweep_csv[:_gp_n]
        else:
            st.warning("No sweep results found. Run a sweep first or choose Custom.")
            _gp_symbols = []
    elif _gp_source == "Lowest N":
        if _gp_sweep_csv:
            _gp_symbols = _gp_sweep_csv[-_gp_n:]
        else:
            st.warning("No sweep results found.")
            _gp_symbols = []
    elif _gp_source == "Random N":
        _gp_symbols = random.sample(list(cached), min(_gp_n, len(cached)))
    else:
        _gp_symbols = []

    if _gp_symbols:
        _gp_sym_str = ", ".join(_gp_symbols[:5]) + (", ..." if len(_gp_symbols) > 5 else "")
        st.caption("Portfolio: " + str(len(_gp_symbols)) + " coins -- " + _gp_sym_str)

    # ── Load/Save Portfolio ──
    st.markdown("---")
    _gp_pf_c1, _gp_pf_c2 = st.columns(2)
    with _gp_pf_c1:
        _gp_saved = list_portfolios()
        if _gp_saved:
            _gp_pf_names = ["(none)"] + [p["name"] + " (" + str(p["coin_count"]) + " coins)" for p in _gp_saved]
            _gp_pf_choice = st.selectbox("Load Saved Portfolio", _gp_pf_names, key="gp_pf_load")
            if _gp_pf_choice != "(none)":
                _gp_pf_idx = _gp_pf_names.index(_gp_pf_choice) - 1
                _gp_pf_file = _gp_saved[_gp_pf_idx]["file"]
                _gp_pf_data = load_portfolio(_gp_pf_file)
                if _gp_pf_data is not None:
                    _gp_symbols = [s for s in _gp_pf_data["coins"] if s in cached]
                    _gp_missing = [s for s in _gp_pf_data["coins"] if s not in cached]
                    if _gp_missing:
                        st.warning("Missing from cache: " + ", ".join(_gp_missing[:5]))
                    st.caption("Loaded: " + _gp_pf_data.get("notes", ""))
        else:
            st.caption("No saved portfolios yet")
    with _gp_pf_c2:
        _gp_save_name = st.text_input("Save current selection as", key="gp_pf_save_name")
        _gp_save_notes = st.text_input("Notes (optional)", key="gp_pf_save_notes")
        if st.button("Save Portfolio", key="gp_pf_save_btn"):
            if _gp_save_name and _gp_symbols:
                _gp_method = _gp_source.lower().replace(" ", "_")
                save_portfolio(_gp_save_name, _gp_symbols, selection_method=_gp_method, notes=_gp_save_notes)
                st.success("Saved: " + _gp_save_name + " (" + str(len(_gp_symbols)) + " coins)")
            elif not _gp_save_name:
                st.warning("Enter a portfolio name first")
            else:
                st.warning("Select coins first")

    st.markdown("---")

    # ── Capital Configuration ──
    st.subheader("Capital")
    _gp_cap_mode = st.radio("Mode", ["Per-Coin Independent", "Shared Pool"],
        horizontal=True, key="gp_cap_mode",
        help="Per-Coin: each coin runs with full notional independently. Shared Pool: fixed total capital, specify per-trade notional.")
    if _gp_cap_mode == "Shared Pool":
        _gp_cap_c1, _gp_cap_c2 = st.columns(2)
        _gp_total_cap = _gp_cap_c1.number_input(
            "Total Capital ($)", min_value=1000, max_value=500000,
            value=10000, step=1000, key="gp_total_cap"
        )
        _gp_per_trade = _gp_cap_c2.number_input(
            "Per-Trade Notional ($)", min_value=100, max_value=50000,
            value=int(notional), step=100, key="gp_per_trade"
        )
        _gp_max_pos = int(_gp_total_cap / (margin if margin > 0 else 500))
        st.caption("Max concurrent positions: " + str(_gp_max_pos) + " ($" + str(int(_gp_total_cap)) + " / $" + str(int(margin)) + " margin)")
    else:
        _gp_total_cap = None
        _gp_per_trade = float(notional)

    st.markdown("---")

    # ── Parameter Ranges ──
    st.subheader("Parameter Ranges")
    _gp_c1, _gp_c2 = st.columns(2)
    with _gp_c1:
        _gp_sl_min = st.number_input("SL min", value=0.5, step=0.25, key="gp_sl_min")
        _gp_sl_max = st.number_input("SL max", value=3.0, step=0.25, key="gp_sl_max")
        _gp_sl_step = st.number_input("SL step", value=0.25, step=0.05, key="gp_sl_step")
    with _gp_c2:
        _gp_tp_min = st.number_input("TP min", value=0.5, step=0.25, key="gp_tp_min")
        _gp_tp_max = st.number_input("TP max", value=4.0, step=0.25, key="gp_tp_max")
        _gp_tp_step = st.number_input("TP step", value=0.25, step=0.05, key="gp_tp_step")

    _gp_no_tp = st.checkbox('Include "No TP" (999.0)', value=True, key="gp_no_tp")
    _gp_cooldowns = st.multiselect("Cooldown values", [0, 3, 5, 10], default=[0, 3, 5, 10], key="gp_cd")
    _gp_be_vals = st.multiselect("BE trigger ATR values", [0.0, 0.5, 1.0], default=[0.0, 0.5, 1.0], key="gp_be")

    import numpy as _np
    _gp_sl_range = _np.arange(_gp_sl_min, _gp_sl_max + _gp_sl_step * 0.5, _gp_sl_step)
    _gp_tp_range = _np.arange(_gp_tp_min, _gp_tp_max + _gp_tp_step * 0.5, _gp_tp_step)
    _gp_pg = build_param_grid(
        sl_range=_gp_sl_range, tp_range=_gp_tp_range,
        cooldown_vals=_gp_cooldowns, be_vals=_gp_be_vals,
        include_no_tp=_gp_no_tp,
    )
    _gp_n_combos = len(_gp_pg)
    _gp_n_coins = len(_gp_symbols) if _gp_symbols else 0
    st.info(
        "Combos: " + str(_gp_n_combos) + " x " + str(_gp_n_coins) + " coins = "
        + str(_gp_n_combos * _gp_n_coins) + " total backtests"
    )

    # ── Run Button ──
    if st.button("Run GPU Portfolio Sweep", key="gp_run") and _gp_symbols:
        st.session_state["gpu_port_symbols"] = _gp_symbols
        _gp_progress = st.progress(0)
        _gp_status = st.empty()

        # Prepare coin data
        _gp_coin_data = []
        _gp_skipped = []
        _gp_status.text("Loading data and computing v3.9.0 signals...")
        for _ci, _sym in enumerate(_gp_symbols):
            _gp_status.text("Signals: " + _sym + " (" + str(_ci + 1) + "/" + str(len(_gp_symbols)) + ")")
            try:
                _df_gp = load_data(_sym, timeframe)
                if _df_gp is None or len(_df_gp) < 200:
                    _gp_skipped.append(_sym)
                    continue
                _df_gp = apply_date_filter(_df_gp, date_range)
                if len(_df_gp) < 200:
                    _gp_skipped.append(_sym)
                    continue
                _df_sig_gp = compute_signals_v390(_df_gp.copy(), signal_params)
                _gp_coin_data.append((_sym, _df_sig_gp))
            except Exception:
                _gp_skipped.append(_sym)

        if not _gp_coin_data:
            st.error("No valid coins after loading/filtering.")
            st.stop()

        if _gp_skipped:
            st.warning("Skipped " + str(len(_gp_skipped)) + " coins (< 200 bars): " + ", ".join(_gp_skipped[:10]))

        # Run GPU sweep per coin
        _gp_t_start = time.time()

        def _gp_progress_cb(current, total, symbol):
            """Update progress bar during multi-coin sweep."""
            if total > 0 and current < total:
                _gp_progress.progress((current + 1) / total)
                _gp_status.text("GPU sweep: " + str(symbol) + " (" + str(current + 1) + "/" + str(total) + ")")
            elif current >= total:
                _gp_progress.progress(1.0)

        _gp_all_results = run_gpu_sweep_multi(
            _gp_coin_data, _gp_pg, _gp_per_trade, 0.0008,
            progress_callback=_gp_progress_cb,
        )

        _gp_elapsed = time.time() - _gp_t_start
        _gp_total_bt = _gp_n_combos * len(_gp_all_results)
        st.session_state["gpu_port_results"] = _gp_all_results
        st.success(
            "GPU portfolio sweep complete: " + str(len(_gp_all_results)) + " coins x "
            + str(_gp_n_combos) + " combos = " + str(_gp_total_bt) + " backtests in "
            + str(round(_gp_elapsed, 2)) + "s"
        )

    # ── Display Results ──
    _gp_res = st.session_state.get("gpu_port_results")
    if _gp_res is not None and len(_gp_res) > 0:
        st.markdown("---")

        # ── Per-Coin Best Combo Table ──
        st.subheader("Best Combo Per Coin")
        _gp_best_rows = []
        for _sym, _df_r in _gp_res.items():
            if _df_r.empty:
                continue
            _best = _df_r.iloc[0]  # already sorted by net_pnl desc
            _gp_best_rows.append({
                "symbol": _sym,
                "sl_mult": round(float(_best["sl_mult"]), 2),
                "tp_mult": "No TP" if float(_best["tp_mult"]) >= 998.0 else round(float(_best["tp_mult"]), 2),
                "be_trigger": round(float(_best["be_trigger_atr"]), 2),
                "cooldown": int(_best["cooldown"]),
                "trades": int(_best["total_trades"]),
                "win_rate": round(float(_best["win_rate"]) * 100, 1),
                "net_pnl": round(float(_best["net_pnl"]), 2),
                "expectancy": round(float(_best["expectancy"]), 2),
                "max_dd_pct": round(float(_best["max_dd_pct"]), 1),
                "profit_factor": round(float(_best["profit_factor"]), 2),
                "lsg_pct": round(float(_best["lsg_pct"]), 1),
                "sharpe": round(float(_best["sharpe"]), 4),
            })

        if _gp_best_rows:
            _gp_best_df = pd.DataFrame(_gp_best_rows)
            _gp_best_df = _gp_best_df.sort_values("net_pnl", ascending=False).reset_index(drop=True)

            # Portfolio summary metrics
            _gp_total_pnl = _gp_best_df["net_pnl"].sum()
            _gp_avg_pnl = _gp_best_df["net_pnl"].mean()
            _gp_profitable = int((_gp_best_df["net_pnl"] > 0).sum())
            _gp_total_trades = int(_gp_best_df["trades"].sum())

            _gp_m1, _gp_m2, _gp_m3, _gp_m4 = st.columns(4)
            _gp_m1.metric("Coins", str(len(_gp_best_df)))
            _gp_m2.metric("Total Net P&L", "$" + str(round(_gp_total_pnl, 0)))
            _gp_m3.metric("Profitable", str(_gp_profitable) + "/" + str(len(_gp_best_df)))
            _gp_m4.metric("Total Trades", str(_gp_total_trades))

            if _gp_total_cap is not None:
                _gp_cap_m1, _gp_cap_m2, _gp_cap_m3 = st.columns(3)
                _gp_roi = (_gp_total_pnl / _gp_total_cap) * 100 if _gp_total_cap > 0 else 0.0
                _gp_cap_m1.metric("Starting Capital", "$" + str(int(_gp_total_cap)))
                _gp_cap_m2.metric("Per-Trade Notional", "$" + str(int(_gp_per_trade)))
                _gp_cap_m3.metric("ROI", str(round(_gp_roi, 1)) + "%")

            st.dataframe(_gp_best_df, use_container_width=True)

        # ── Aggregated Heatmap (SL vs TP, sum of best net_pnl across coins) ──
        st.subheader("Aggregated Heatmap: SL vs TP (sum of net P&L across all coins)")
        st.caption("For each SL/TP pair: takes the best combo per coin (across BE/CD), then sums across coins.")

        # For each coin, for each (sl, tp) pair, take the best net_pnl (across be/cd)
        _gp_hm_rows = []
        for _sym, _df_r in _gp_res.items():
            _coin_best = _df_r.groupby(["sl_mult", "tp_mult"])["net_pnl"].max().reset_index()
            _coin_best["symbol"] = _sym
            _gp_hm_rows.append(_coin_best)

        if _gp_hm_rows:
            _gp_hm_all = pd.concat(_gp_hm_rows, ignore_index=True)
            _gp_hm_agg = _gp_hm_all.groupby(["sl_mult", "tp_mult"])["net_pnl"].sum().reset_index()
            _gp_hm_pivot = _gp_hm_agg.pivot(index="sl_mult", columns="tp_mult", values="net_pnl")

            _gp_new_cols = []
            for _col in _gp_hm_pivot.columns:
                if _col >= 998.0:
                    _gp_new_cols.append("No TP")
                else:
                    _gp_new_cols.append(str(round(_col, 2)))
            _gp_hm_pivot.columns = _gp_new_cols
            _gp_hm_pivot.index = [str(round(x, 2)) for x in _gp_hm_pivot.index]

            _gp_hm_fig = go.Figure(data=go.Heatmap(
                z=_gp_hm_pivot.values,
                x=_gp_hm_pivot.columns.tolist(),
                y=_gp_hm_pivot.index.tolist(),
                colorscale="RdYlGn",
                zmid=0,
                colorbar=dict(title="Sum Net P&L ($)"),
            ))
            _gp_hm_fig.update_layout(
                xaxis_title="TP Mult",
                yaxis_title="SL Mult",
                height=500,
            )

            # Annotate best cell
            _gp_best_sl_tp = _gp_hm_agg.loc[_gp_hm_agg["net_pnl"].idxmax()]
            _gp_best_tp_lbl = "No TP" if float(_gp_best_sl_tp["tp_mult"]) >= 998.0 else str(round(float(_gp_best_sl_tp["tp_mult"]), 2))
            _gp_hm_fig.add_annotation(
                x=_gp_best_tp_lbl,
                y=str(round(float(_gp_best_sl_tp["sl_mult"]), 2)),
                text="BEST",
                showarrow=True,
                arrowhead=2,
                font=dict(color="white", size=12),
            )
            st.plotly_chart(_gp_hm_fig, use_container_width=True)

        # ── Per-Coin Heatmaps (expandable) ──
        st.subheader("Per-Coin Heatmaps")
        for _sym, _df_r in _gp_res.items():
            with st.expander(_sym + " (best: $" + str(round(float(_df_r.iloc[0]["net_pnl"]), 0)) + ")"):
                _pc_hm = _df_r.groupby(["sl_mult", "tp_mult"])["net_pnl"].max().reset_index()
                _pc_pivot = _pc_hm.pivot(index="sl_mult", columns="tp_mult", values="net_pnl")
                _pc_cols = []
                for _c in _pc_pivot.columns:
                    if _c >= 998.0:
                        _pc_cols.append("No TP")
                    else:
                        _pc_cols.append(str(round(_c, 2)))
                _pc_pivot.columns = _pc_cols
                _pc_pivot.index = [str(round(x, 2)) for x in _pc_pivot.index]

                _pc_fig = go.Figure(data=go.Heatmap(
                    z=_pc_pivot.values,
                    x=_pc_pivot.columns.tolist(),
                    y=_pc_pivot.index.tolist(),
                    colorscale="RdYlGn",
                    zmid=0,
                    colorbar=dict(title="Net P&L ($)"),
                ))
                _pc_fig.update_layout(
                    xaxis_title="TP Mult", yaxis_title="SL Mult",
                    height=400, title=_sym,
                )
                st.plotly_chart(_pc_fig, use_container_width=True)

                # Top 5 for this coin
                _pc_top5 = _df_r.head(5).copy()
                _pc_top5["tp_mult"] = _pc_top5["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))
                st.dataframe(_pc_top5[[
                    "sl_mult", "tp_mult", "be_trigger_atr", "cooldown",
                    "total_trades", "win_rate", "net_pnl", "expectancy",
                    "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",
                ]], use_container_width=True)

        # ── Export All Results CSV ──
        st.markdown("---")
        _gp_all_export = []
        for _sym, _df_r in _gp_res.items():
            _exp = _df_r.copy()
            _exp.insert(0, "symbol", _sym)
            _gp_all_export.append(_exp)
        if _gp_all_export:
            _gp_export_df = pd.concat(_gp_all_export, ignore_index=True)
            _gp_csv_data = _gp_export_df.to_csv(index=False)
            st.download_button(
                "Export All Results CSV",
                data=_gp_csv_data,
                file_name="gpu_portfolio_sweep.csv",
                mime="text/csv",
            )

        # ── Export Best-Per-Coin CSV ──
        if _gp_best_rows:
            _gp_best_csv = pd.DataFrame(_gp_best_rows).to_csv(index=False)
            st.download_button(
                "Export Best-Per-Coin CSV",
                data=_gp_best_csv,
                file_name="gpu_portfolio_best.csv",
                mime="text/csv",
                key="gp_best_csv",
            )
'''

    src += gpu_port_mode

    with open(DASH_FILE, "w", encoding="utf-8") as f:
        f.write(src)

    try:
        py_compile.compile(str(DASH_FILE), doraise=True)
        print("[OK] dashboard_v394.py patched — GPU Portfolio Sweep mode added")
    except py_compile.PyCompileError as e:
        print("[FAIL] dashboard_v394.py: " + str(e))
        ERRORS.append("dashboard py_compile")


# ============================================================================
# Main
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("GPU Portfolio Sweep — Build Script")
    print("=" * 60)

    patch_cuda_sweep()
    patch_dashboard()

    # Verify patches landed
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)

    checks = [
        (CUDA_FILE, "def run_gpu_sweep_multi", "cuda_sweep: run_gpu_sweep_multi()"),
        (DASH_FILE, '"gpu_port_results"', "dashboard: gpu_port session state"),
        (DASH_FILE, 'run_gpu_port = st.sidebar.button', "dashboard: sidebar button"),
        (DASH_FILE, 'elif mode == "gpu_port_sweep":', "dashboard: mode block"),
        (DASH_FILE, "run_gpu_sweep_multi", "dashboard: calls run_gpu_sweep_multi"),
        (DASH_FILE, "gpu_portfolio_sweep.csv", "dashboard: CSV export"),
    ]

    all_ok = True
    for fpath, needle, desc in checks:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        if needle in content:
            print("[VERIFIED] " + desc)
        else:
            print("[MISSING]  " + desc)
            all_ok = False

    if ERRORS:
        print("\nERRORS: " + ", ".join(ERRORS))
        sys.exit(1)
    elif all_ok:
        print("\nAll patches applied successfully.")
        print("Restart the dashboard to see the new GPU Portfolio Sweep button.")
    else:
        print("\nSome verifications failed. Check files manually.")
        sys.exit(1)

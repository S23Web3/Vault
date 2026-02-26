r"""
Build script: Portfolio bugfix (2 bugs from user screenshot)

BUG A: Clicking 'Run Portfolio Backtest' re-randomizes coin list
  - Random N calls random.sample() on every Streamlit rerun
  - Top N / Lowest N also recompute on every rerun
  - Fix: Store port_symbols in session_state, reuse on reruns

BUG B: Best Equity / Worst DD metrics are confusing
  - Net P&L shows -12k but Best Equity shows $108k
  - User asks 'how was it best 108k?'
  - Root cause: Best Equity is raw summed equity (10 coins * $10k = $100k base)
  - $108k means +$8k net at that moment, but displayed as absolute
  - Fix: Show as net profit (+$X from baseline), add date context

Patches dashboard.py in-place (after backup).

Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_portfolio_bugfix.py"
"""

import shutil
import sys
import py_compile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "scripts" / "dashboard.py"
BACKUP = ROOT / "scripts" / "dashboard_pre_bugfix.py.backup"

ERRORS = []
PASS_COUNT = 0


def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def check(name, condition):
    """Assert a condition and track pass/fail."""
    global PASS_COUNT
    ts = datetime.now().strftime("%H:%M:%S")
    if condition:
        PASS_COUNT += 1
        print(f"[{ts}] PASS: {name}")
    else:
        ERRORS.append(name)
        print(f"[{ts}] FAIL: {name}")


def main():
    """Apply 2 bugfixes to dashboard.py portfolio mode."""
    log("=== Portfolio Bugfix Build ===")

    # --- Step 1: Verify dashboard.py exists ---
    if not DASHBOARD.exists():
        log(f"FATAL: {DASHBOARD} not found")
        sys.exit(1)
    log(f"Source: {DASHBOARD}")

    # --- Step 2: Backup ---
    if not BACKUP.exists():
        shutil.copy2(DASHBOARD, BACKUP)
        log(f"Backup: {BACKUP}")
    else:
        log(f"Backup already exists: {BACKUP}")

    # --- Step 3: Read source ---
    src = DASHBOARD.read_text(encoding="utf-8")
    original_len = len(src)
    log(f"Read {original_len} chars")

    # ====================================================================
    # PATCH 1: Session state init -- add port_symbols_locked key
    # ====================================================================
    log("--- PATCH 1: Add session state key for locked port_symbols ---")

    old_session_init = 'if "portfolio_data" not in st.session_state:\n    st.session_state["portfolio_data"] = None'

    new_session_init = '''if "portfolio_data" not in st.session_state:
    st.session_state["portfolio_data"] = None
if "port_symbols_locked" not in st.session_state:
    st.session_state["port_symbols_locked"] = None'''

    check("P1: session init anchor found", old_session_init in src)
    src = src.replace(old_session_init, new_session_init, 1)
    check("P1: session init patched", new_session_init in src)

    # ====================================================================
    # PATCH 2: Clear locked symbols on Back to Settings
    # ====================================================================
    log("--- PATCH 2: Clear locked symbols on back button ---")

    old_back = '''    if st.button("Back to Settings"):
        st.session_state["mode"] = "settings"
        st.session_state["portfolio_data"] = None
        st.rerun()'''

    new_back = '''    if st.button("Back to Settings"):
        st.session_state["mode"] = "settings"
        st.session_state["portfolio_data"] = None
        st.session_state["port_symbols_locked"] = None
        st.rerun()'''

    check("P2: back button anchor found", old_back in src)
    src = src.replace(old_back, new_back, 1)
    check("P2: back button patched", new_back in src)

    # ====================================================================
    # PATCH 3: Lock coin selection into session state
    # Replace the entire coin selection block so Random N, Top N, Lowest N
    # only compute ONCE, then reuse from session state on reruns.
    # ====================================================================
    log("--- PATCH 3: Lock coin selection into session state ---")

    old_coin_selection = '''    if port_source == "Top N":
        if sweep_csv_results:
            port_symbols = sweep_csv_results[:port_n]
        else:
            st.warning("No sweep results found. Run a sweep first or choose another selection.")
            port_symbols = []
    elif port_source == "Lowest N":
        if sweep_csv_results:
            port_symbols = sweep_csv_results[-port_n:]
        else:
            st.warning("No sweep results found. Run a sweep first.")
            port_symbols = []
    elif port_source == "Random N":
        port_symbols = random.sample(list(cached), min(port_n, len(cached)))
    else:  # Custom
        port_symbols = st.multiselect("Select coins", cached, default=cached[:min(5, len(cached))])

    if port_symbols:
        _syms_str = ", ".join(port_symbols[:5]) + (", ..." if len(port_symbols) > 5 else "")
        st.caption(f"Portfolio: {len(port_symbols)} coins -- {_syms_str}")

    run_port = st.button("Run Portfolio Backtest", disabled=len(port_symbols) == 0)'''

    new_coin_selection = '''    # Check if we have a locked selection from a previous run
    _locked = st.session_state.get("port_symbols_locked")

    if port_source == "Custom":
        _default = _locked if _locked is not None else cached[:min(5, len(cached))]
        _default = [s for s in _default if s in cached]
        port_symbols = st.multiselect("Select coins", cached, default=_default)
    elif _locked is not None:
        # Reuse locked selection on reruns (prevents Random re-roll)
        port_symbols = _locked
    elif port_source == "Top N":
        if sweep_csv_results:
            port_symbols = sweep_csv_results[:port_n]
        else:
            st.warning("No sweep results found. Run a sweep first or choose another selection.")
            port_symbols = []
    elif port_source == "Lowest N":
        if sweep_csv_results:
            port_symbols = sweep_csv_results[-port_n:]
        else:
            st.warning("No sweep results found. Run a sweep first.")
            port_symbols = []
    elif port_source == "Random N":
        port_symbols = random.sample(list(cached), min(port_n, len(cached)))
    else:
        port_symbols = []

    if port_symbols:
        _syms_str = ", ".join(port_symbols[:5]) + (", ..." if len(port_symbols) > 5 else "")
        st.caption(f"Portfolio: {len(port_symbols)} coins -- {_syms_str}")

    _col_run, _col_reset = st.columns([3, 1])
    with _col_run:
        run_port = st.button("Run Portfolio Backtest", disabled=len(port_symbols) == 0)
    with _col_reset:
        if st.button("Reset Selection"):
            st.session_state["port_symbols_locked"] = None
            st.session_state["portfolio_data"] = None
            st.rerun()'''

    check("P3: coin selection anchor found", old_coin_selection in src)
    src = src.replace(old_coin_selection, new_coin_selection, 1)
    check("P3: coin selection patched", new_coin_selection in src)

    # ====================================================================
    # PATCH 4: Lock symbols when Run is clicked
    # ====================================================================
    log("--- PATCH 4: Lock symbols on run ---")

    old_run = '''    if run_port and port_symbols:
        with st.spinner("Running portfolio backtest..."):'''

    new_run = '''    if run_port and port_symbols:
        st.session_state["port_symbols_locked"] = port_symbols
        with st.spinner("Running portfolio backtest..."):'''

    check("P4: run button anchor found", old_run in src)
    src = src.replace(old_run, new_run, 1)
    check("P4: run button patched", new_run in src)

    # ====================================================================
    # PATCH 5: Fix Best/Worst metrics display
    # Show net profit from baseline instead of raw summed equity.
    # Add dollar amount to worst DD.
    # ====================================================================
    log("--- PATCH 5: Fix best/worst metrics display ---")

    old_bw = '''        # Best vs Worst capital moments
        st.subheader("Capital Allocation: Best vs Worst", help="Historical best/worst, not Monte Carlo")
        bw1, bw2 = st.columns(2)
        best = pf["best_moment"]
        worst = pf["worst_moment"]
        _best_eq = best["equity"]
        _best_cap = best["capital"]
        _best_info = str(best["date"]) + " | " + str(best["positions"]) + " positions | $" + f"{_best_cap:,.0f}" + " capital"
        bw1.metric("Best Equity", f"${_best_eq:,.2f}", _best_info)
        _worst_dd = worst["dd_pct"]
        _worst_cap = worst["capital"]
        _worst_info = str(worst["date"]) + " | " + str(worst["positions"]) + " positions | $" + f"{_worst_cap:,.0f}" + " capital"
        bw2.metric("Worst DD", f"{_worst_dd:.1f}%", _worst_info)'''

    new_bw = '''        # Best vs Worst capital moments
        st.subheader("Peak Profit vs Worst Drawdown", help="Historical best/worst net P&L moments")
        bw1, bw2 = st.columns(2)
        best = pf["best_moment"]
        worst = pf["worst_moment"]
        _baseline = 10000.0 * len(coin_results)
        _best_net = best["equity"] - _baseline
        _best_info = str(best["date"])[:10] + " | " + str(best["positions"]) + " pos | $" + f"{best['capital']:,.0f}" + " capital"
        bw1.metric("Peak Net Profit", f"${_best_net:+,.2f}", _best_info,
            help="Best net P&L at any point (equity - baseline). Baseline = $10k x coins.")
        _worst_dd = worst["dd_pct"]
        _worst_net = worst["equity"] - _baseline
        _worst_info = str(worst["date"])[:10] + " | " + str(worst["positions"]) + " pos | $" + f"{worst['capital']:,.0f}" + " capital"
        bw2.metric("Worst Drawdown", f"{_worst_dd:.1f}% (${_worst_net:+,.0f})", _worst_info,
            help="Largest peak-to-trough drop. Dollar amount = net P&L at that moment.")'''

    check("P5: best/worst anchor found", old_bw in src)
    src = src.replace(old_bw, new_bw, 1)
    check("P5: best/worst patched", new_bw in src)

    # ====================================================================
    # WRITE & COMPILE
    # ====================================================================
    log("--- Writing patched dashboard.py ---")
    DASHBOARD.write_text(src, encoding="utf-8")
    check("Write: file written", DASHBOARD.exists())
    new_len = len(DASHBOARD.read_text(encoding="utf-8"))
    log(f"Size: {original_len} -> {new_len} chars (delta: {new_len - original_len:+d})")

    log("--- py_compile ---")
    try:
        py_compile.compile(str(DASHBOARD), doraise=True)
        check("py_compile: dashboard.py", True)
    except py_compile.PyCompileError as e:
        check(f"py_compile: dashboard.py -- {e}", False)

    # ====================================================================
    # SUMMARY
    # ====================================================================
    log("")
    log("=" * 60)
    total = PASS_COUNT + len(ERRORS)
    log(f"RESULTS: {PASS_COUNT}/{total} passed")
    if ERRORS:
        log("FAILURES: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        log("ALL PATCHES APPLIED SUCCESSFULLY")
        log("")
        log("Changes:")
        log("  BUG A FIXED: Coin list locked into session state on Run click")
        log("    - Random N no longer re-rolls on rerun")
        log("    - Top N / Lowest N no longer recompute")
        log("    - Reset Selection button clears the lock")
        log("  BUG B FIXED: Best/Worst metrics now show net profit")
        log("    - 'Peak Net Profit' shows +$X from baseline")
        log("    - 'Worst Drawdown' shows both % and dollar net")
        log("    - Help tooltips explain baseline calculation")
        log("")
        log("Backup: scripts/dashboard_pre_bugfix.py.backup")
        log("Test:   streamlit run scripts/dashboard.py")


if __name__ == "__main__":
    main()

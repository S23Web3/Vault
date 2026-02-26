r"""
Test build: imports, AVWAP math, full backtest with/without AVWAP.
Run: python scripts/test_build.py
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_imports():
    print("[1/4] Import test...")
    from engine.position import Position, Trade
    from engine.backtester import Backtester
    from engine.metrics import compute_metrics, trades_to_dataframe
    from signals.four_pillars import compute_signals
    from signals.stochastics import compute_all_stochastics
    from signals.clouds import compute_clouds
    from data.fetcher import BybitFetcher
    print("      PASS -- all imports OK")


def test_avwap_math():
    print("[2/4] AVWAP math test...")
    from engine.position import Position

    p = Position("LONG", "A", 0, 100.0, 2.0,
                 avwap_enabled=True, avwap_band=2, avwap_floor_atr=1.0)
    assert p.avwap_enabled is True
    assert p.avwap_band == 2
    assert abs(p.sl - 98.0) < 0.001  # entry 100 - 1.0*2.0 ATR

    r = p.update(101.0, 99.5, 100.5, hlc3=100.33, volume=1000.0)
    assert r is None
    assert p.avwap_stdev >= 0
    print(f"      Bar 1: SL={p.sl:.4f} AVWAP={p.avwap_value:.4f} stdev={p.avwap_stdev:.6f}")

    r = p.update(102.0, 100.0, 101.5, hlc3=101.17, volume=1500.0)
    assert r is None
    assert p.avwap_stdev > 0  # stdev should be nonzero after 2 bars
    print(f"      Bar 2: SL={p.sl:.4f} AVWAP={p.avwap_value:.4f} stdev={p.avwap_stdev:.6f}")

    r = p.update(102.5, 101.0, 102.0, hlc3=101.83, volume=2000.0)
    assert r is None
    print(f"      Bar 3: SL={p.sl:.4f} AVWAP={p.avwap_value:.4f} stdev={p.avwap_stdev:.6f}")

    # SHORT test
    ps = Position("SHORT", "A", 0, 100.0, 2.0,
                  avwap_enabled=True, avwap_band=1, avwap_floor_atr=1.0)
    assert abs(ps.sl - 102.0) < 0.001  # entry 100 + 1.0*2.0 ATR
    r = ps.update(100.5, 99.0, 99.5, hlc3=99.67, volume=1000.0)
    assert r is None
    print(f"      SHORT: SL={ps.sl:.4f} AVWAP={ps.avwap_value:.4f}")

    # Disabled test (backward compat)
    p_off = Position("LONG", "A", 0, 100.0, 2.0, avwap_enabled=False)
    r = p_off.update(101.0, 99.5, 100.5)
    assert r is None
    print(f"      OFF:   SL={p_off.sl:.4f} (should be 98.0)")
    assert abs(p_off.sl - 98.0) < 0.001

    print("      PASS -- AVWAP math OK")


def test_backtester_avwap():
    print("[3/4] Backtester AVWAP integration test...")
    from engine.backtester import Backtester
    from signals.four_pillars import compute_signals
    from data.fetcher import BybitFetcher
    import pandas as pd

    fetcher = BybitFetcher(cache_dir="data/cache")
    cached = fetcher.list_cached()
    if not cached:
        print("      SKIP -- no cached data")
        return

    sym = "RIVERUSDT" if "RIVERUSDT" in cached else cached[0]
    df = fetcher.load_cached(sym)
    if df is None:
        print(f"      SKIP -- {sym} load failed")
        return

    # Resample to 5m
    if 'datetime' not in df.columns and df.index.name == 'datetime':
        df = df.reset_index()
    df = df.set_index('datetime').resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
        'base_vol': 'sum', 'quote_vol': 'sum', 'timestamp': 'first'
    }).dropna().reset_index()

    df_sig = compute_signals(df.copy())
    print(f"      {sym} 5m: {len(df_sig):,} bars, signals computed")

    # Without AVWAP
    t0 = time.time()
    bt1 = Backtester({
        "sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3, "b_open_fresh": True,
        "notional": 10000, "commission_rate": 0.0008, "rebate_pct": 0.7,
        "be_raise_amount": 2.0
    })
    r1 = bt1.run(df_sig)
    t1 = time.time() - t0
    e1 = r1["equity_curve"][-1] - 10000
    m1 = r1["metrics"]

    # With AVWAP 2-sigma
    t0 = time.time()
    bt2 = Backtester({
        "sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3, "b_open_fresh": True,
        "notional": 10000, "commission_rate": 0.0008, "rebate_pct": 0.7,
        "avwap_enabled": True, "avwap_band": 2, "avwap_floor_atr": 1.0
    })
    r2 = bt2.run(df_sig)
    t2 = time.time() - t0
    e2 = r2["equity_curve"][-1] - 10000
    m2 = r2["metrics"]

    # With AVWAP 1-sigma
    bt3 = Backtester({
        "sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3, "b_open_fresh": True,
        "notional": 10000, "commission_rate": 0.0008, "rebate_pct": 0.7,
        "avwap_enabled": True, "avwap_band": 1, "avwap_floor_atr": 1.0
    })
    r3 = bt3.run(df_sig)
    e3 = r3["equity_curve"][-1] - 10000
    m3 = r3["metrics"]

    # With AVWAP 3-sigma
    bt4 = Backtester({
        "sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3, "b_open_fresh": True,
        "notional": 10000, "commission_rate": 0.0008, "rebate_pct": 0.7,
        "avwap_enabled": True, "avwap_band": 3, "avwap_floor_atr": 1.0
    })
    r4 = bt4.run(df_sig)
    e4 = r4["equity_curve"][-1] - 10000
    m4 = r4["metrics"]

    print(f"\n      {'Mode':<16} {'Trades':>7} {'WR':>7} {'Net':>12} {'Exp':>8} {'DD%':>7} {'LSG':>6} {'Time':>6}")
    print(f"      {'-'*72}")
    for label, m, net, t in [
        ("BE$2 (no AVWAP)", m1, e1, t1),
        ("AVWAP 1-sigma",   m3, e3, 0),
        ("AVWAP 2-sigma",   m2, e2, t2),
        ("AVWAP 3-sigma",   m4, e4, 0),
    ]:
        tr = m["total_trades"]
        exp = net / tr if tr > 0 else 0
        print(f"      {label:<16} {tr:>7,} {m['win_rate']:>6.1%} ${net:>10,.2f} ${exp:>6.2f} {m['max_drawdown_pct']:>6.1f}% {m['pct_losers_saw_green']:>5.0%} {t:>5.1f}s")

    print(f"\n      PASS -- backtester runs with all AVWAP modes")


def test_dashboard_import():
    print("[4/4] Dashboard import test...")
    import py_compile
    py_compile.compile(str(Path(__file__).resolve().parent / "dashboard.py"), doraise=True)
    print("      PASS -- dashboard.py compiles OK")


if __name__ == "__main__":
    print("=" * 60)
    print("FOUR PILLARS BUILD TEST")
    print("=" * 60)
    t_start = time.time()

    try:
        test_imports()
        test_avwap_math()
        test_backtester_avwap()
        test_dashboard_import()
    except Exception as e:
        print(f"\n      FAIL: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to close...")
        sys.exit(1)

    elapsed = time.time() - t_start
    print(f"\n{'=' * 60}")
    print(f"ALL TESTS PASSED ({elapsed:.1f}s)")
    print(f"{'=' * 60}")
    input("\nPress Enter to close...")

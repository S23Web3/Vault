"""
Test script for v3.8.2 Python backtester.
Validates imports, signal generation, and runs a quick backtest.

Usage: python scripts/test_v382.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def test_imports():
    """Test all v3.8.2 module imports."""
    print("Testing imports...")
    from engine.avwap import AVWAPTracker
    from engine.position_v382 import PositionSlot, Trade382
    from engine.backtester_v382 import Backtester382
    from signals.state_machine_v382 import FourPillarsStateMachine382, SignalResult
    from signals.four_pillars_v382 import compute_signals_v382
    print("  All imports OK")
    return True


def test_avwap():
    """Test AVWAP tracker computation."""
    print("Testing AVWAP tracker...")
    from engine.avwap import AVWAPTracker

    tracker = AVWAPTracker(sigma_floor_atr=0.5)
    # Simulate 5 bars
    bars = [
        (100.0, 1000.0, 2.0),  # hlc3, volume, atr
        (101.0, 1200.0, 2.0),
        (99.0, 800.0, 2.1),
        (102.0, 1500.0, 2.0),
        (100.5, 1100.0, 2.0),
    ]
    for hlc3, vol, atr in bars:
        tracker.update(hlc3, vol, atr)

    c, p1, m1, p2, m2 = tracker.bands()
    print(f"  Center: {c:.4f}")
    print(f"  +1sigma: {p1:.4f}  -1sigma: {m1:.4f}")
    print(f"  +2sigma: {p2:.4f}  -2sigma: {m2:.4f}")
    print(f"  Sigma: {tracker.sigma:.4f}")

    assert c > 99 and c < 102, f"AVWAP center {c} out of range"
    assert tracker.sigma > 0, "Sigma should be positive"
    print("  AVWAP tracker OK")
    return True


def test_position_slot():
    """Test position slot creation and SL staging."""
    print("Testing position slot...")
    from engine.position_v382 import PositionSlot

    slot = PositionSlot(
        direction="LONG",
        grade="A",
        entry_bar=0,
        entry_price=100.0,
        atr=2.0,
        hlc3=100.0,
        volume=1000.0,
        sigma_floor_atr=0.5,
        sl_atr_mult=1.0,
        stage1to2_trigger="opposite_2sigma",
        stage2_bars=5,
        notional=5000.0,
    )

    print(f"  Initial SL: {slot.sl:.4f}")
    print(f"  Stage: {slot.stage}")
    assert slot.stage == 1, "Should start at stage 1"
    assert slot.sl < 100.0, "Long SL should be below entry"

    # Simulate bars where price goes up (should trigger stage 1->2)
    for bar in range(1, 20):
        price = 100.0 + bar * 0.5  # trending up
        exit_reason = slot.check_exit(price + 0.5, price - 0.5)
        if exit_reason:
            print(f"  Exited at bar {bar}: {exit_reason}")
            break
        slot.update_bar(
            bar, price + 0.5, price - 0.5, price, 2.0,
            price, 1000.0, price * 1.1, price * 0.9
        )
        if slot.stage > 1:
            print(f"  Stage transition to {slot.stage} at bar {bar}, SL: {slot.sl:.4f}")
            break

    assert slot.stage >= 2, "Should have transitioned to stage 2+"
    print("  Position slot OK")
    return True


def test_state_machine():
    """Test v3.8.2 state machine: 60-K triggers zone, 9-K cross back fires signal."""
    print("Testing state machine v3.8.2...")
    from signals.state_machine_v382 import FourPillarsStateMachine382

    # --- Test A: 4/4 fires below Cloud 3 (bypasses Cloud 3) ---
    sm = FourPillarsStateMachine382()

    # Bar 0: 60-K enters oversold (< 25), all faster stochs also oversold
    r = sm.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=20, stoch_60=20,
                       stoch_60_d=40, cloud3_bull=True, price_pos=-1,
                       price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    assert not r.long_a, "No signal on zone entry"

    # Bar 2: 9-K crosses back above 25. All flags set (9<30, 14<30, 40<25) → A fires
    r = sm.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=20, stoch_60=20,
                       stoch_60_d=40, cloud3_bull=False, price_pos=-1,
                       price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  A signal (4/4) below Cloud 3: long_a={r.long_a}")
    assert r.long_a, "A should fire: 60 triggered zone, 9+14+40 all flagged, Cloud 3 bypassed"

    # --- Test B: 3/4 blocked below Cloud 3 ---
    sm2 = FourPillarsStateMachine382()

    # Bar 0: 60-K oversold, 9 and 14 oversold, but 40 NOT (50 > 25)
    r = sm2.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=True, price_pos=-1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)

    # Bar 2: 9-K crosses back. 9+14 flagged but not 40 → not A. B needs Cloud 3.
    r = sm2.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=False, price_pos=-1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  B signal (3/4) below Cloud 3: long_b={r.long_b}")
    assert not r.long_b, "B should be blocked: price_pos=-1, Cloud 3 not aligned"

    # --- Test B: 3/4 fires WITH Cloud 3 ---
    sm3 = FourPillarsStateMachine382()

    r = sm3.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    r = sm3.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  B signal (3/4) with Cloud 3: long_b={r.long_b}")
    assert r.long_b, "B should fire: 9+14 flagged, Cloud 3 aligned"

    # --- Test: no zone when 60-K is NOT oversold ---
    sm4 = FourPillarsStateMachine382()

    r = sm4.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=20, stoch_60=50,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    r = sm4.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=20, stoch_60=50,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  No zone (60-K=50): long_a={r.long_a}, long_b={r.long_b}")
    assert not r.long_a and not r.long_b, "No signal when 60-K never entered zone"

    print("  State machine v3.8.2 OK")
    return True


def test_backtest():
    """Run a quick backtest on first available 5m coin."""
    print("Testing backtest...")
    import pandas as pd
    from signals.four_pillars_v382 import compute_signals_v382
    from engine.backtester_v382 import Backtester382

    # Find a 5m cached file
    files = sorted(CACHE_DIR.glob("*_5m.parquet"))
    if not files:
        print("  SKIP: No 5m cached data found")
        return True

    symbol = files[0].stem.replace("_5m", "")
    print(f"  Using {symbol}...")

    df = pd.read_parquet(files[0])
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})

    # Compute signals
    df = compute_signals_v382(df)
    print(f"  {len(df)} bars, signals computed")

    signal_count = df["long_a"].sum() + df["short_a"].sum()
    print(f"  A signals: {signal_count}")

    # Run backtest
    params = {
        "notional": 5000.0,
        "commission_rate": 0.0008,
        "rebate_pct": 0.50,
        "max_positions": 4,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_atr_mult": 1.0,
        "stage2_bars": 5,
        "stage1to2_trigger": "opposite_2sigma",
        "enable_adds": True,
        "enable_reentry": True,
    }
    bt = Backtester382(params)
    results = bt.run(df)
    m = results["metrics"]

    print(f"  Trades: {m['total_trades']}")
    print(f"  Win rate: {m['win_rate']:.1%}")
    print(f"  Net P&L: ${m['net_pnl']:.2f}")
    print(f"  Commission: ${m['total_commission']:.2f}")
    print(f"  Rebate: ${m.get('total_rebate', 0):.2f}")
    print(f"  Profit factor: {m['profit_factor']:.2f}")

    if m.get("grades"):
        for grade, stats in m["grades"].items():
            print(f"    {grade}: {stats['count']} trades, {stats['win_rate']:.0%} WR")

    assert m["total_trades"] > 0, "Should have at least 1 trade"
    print("  Backtest OK")
    return True


def main():
    print("=" * 55)
    print("  v3.8.2 PYTHON BACKTESTER TEST SUITE")
    print("=" * 55)

    tests = [
        ("Imports", test_imports),
        ("AVWAP Tracker", test_avwap),
        ("Position Slot", test_position_slot),
        ("State Machine", test_state_machine),
        ("Backtest", test_backtest),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            if fn():
                passed += 1
            else:
                failed += 1
                print(f"  FAIL: {name}")
        except Exception as e:
            failed += 1
            print(f"  ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 55}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 55}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

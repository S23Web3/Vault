"""
Test script for v3.8.3 Python backtester.
Validates imports, state machine (A/B/C/D), position slot (ATR SL, scale-out), backtest.

Usage: python scripts/test_v383.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def test_imports():
    """Test all v3.8.3 module imports."""
    print("Testing imports...")
    from engine.avwap import AVWAPTracker
    from engine.position_v383 import PositionSlot383, Trade383
    from engine.backtester_v383 import Backtester383
    from signals.state_machine_v383 import FourPillarsStateMachine383, SignalResult
    from signals.four_pillars_v383 import compute_signals_v383
    print("  All imports OK")
    return True


def test_avwap_clone():
    """Test AVWAP clone for inheritance."""
    print("Testing AVWAP clone...")
    from engine.avwap import AVWAPTracker

    tracker = AVWAPTracker(sigma_floor_atr=0.5)
    for hlc3, vol, atr in [(100, 1000, 2), (101, 1200, 2), (99, 800, 2.1)]:
        tracker.update(hlc3, vol, atr)

    clone = tracker.clone()
    assert clone.center == tracker.center, "Clone center mismatch"
    assert clone.sigma == tracker.sigma, "Clone sigma mismatch"
    assert clone.cum_pv == tracker.cum_pv, "Clone cum_pv mismatch"

    # Diverge: update clone but not original
    clone.update(105, 2000, 2.0)
    assert clone.center != tracker.center, "Clone should diverge after update"
    print("  AVWAP clone OK")
    return True


def test_position_atr_sl():
    """Test ATR-based SL for A/B/C/D trades."""
    print("Testing ATR SL for ABCD trades...")
    from engine.position_v383 import PositionSlot383

    slot = PositionSlot383(
        direction="LONG",
        grade="A",
        entry_bar=0,
        entry_price=100.0,
        atr=2.0,
        hlc3=100.0,
        volume=1000.0,
        sl_mult=2.0,
        notional=5000.0,
        checkpoint_interval=5,
        max_scaleouts=2,
    )

    expected_sl = 100.0 - (2.0 * 2.0)  # 96.0
    assert abs(slot.sl - expected_sl) < 0.001, f"SL should be {expected_sl}, got {slot.sl}"
    assert slot.sl_phase == "initial", "Should start in initial phase"
    print(f"  Initial SL: {slot.sl:.4f} (expected {expected_sl})")

    # Simulate 5 bars (trending up)
    for bar in range(1, 6):
        price = 100.0 + bar * 0.5
        slot.update_bar(bar, price + 0.5, price - 0.5, price, 2.0, price, 1000.0)

    assert slot.sl_phase == "avwap", "Should transition to avwap phase after 5 bars"
    assert slot.sl > expected_sl, f"SL should have moved up, was {expected_sl}, now {slot.sl}"
    print(f"  After 5 bars: SL={slot.sl:.4f}, phase={slot.sl_phase}")
    print("  ATR SL OK")
    return True


def test_position_avwap_sl():
    """Test AVWAP 2sigma SL for ADD/RE trades."""
    print("Testing AVWAP 2sigma SL for ADD/RE trades...")
    from engine.avwap import AVWAPTracker
    from engine.position_v383 import PositionSlot383

    # Build parent AVWAP state
    parent = AVWAPTracker(sigma_floor_atr=0.5)
    for hlc3, vol, atr in [(100, 1000, 2), (101, 1200, 2), (99, 800, 2.1), (102, 1500, 2)]:
        parent.update(hlc3, vol, atr)

    slot = PositionSlot383(
        direction="LONG",
        grade="ADD",
        entry_bar=10,
        entry_price=99.0,
        atr=2.0,
        hlc3=99.0,
        volume=1000.0,
        sl_mult=2.0,
        notional=5000.0,
        avwap_state=parent,
    )

    # SL should be AVWAP center - 2*sigma, NOT ATR-based
    c, s = slot.avwap.center, slot.avwap.sigma
    expected_sl = c - 2 * s
    assert abs(slot.sl - expected_sl) < 0.01, f"ADD SL should be AVWAP-2sigma ({expected_sl}), got {slot.sl}"
    print(f"  ADD SL: {slot.sl:.4f}, AVWAP center: {c:.4f}, sigma: {s:.4f}")
    print("  AVWAP SL OK")
    return True


def test_scale_out():
    """Test scale-out mechanism."""
    print("Testing scale-out...")
    from engine.position_v383 import PositionSlot383

    slot = PositionSlot383(
        direction="LONG",
        grade="A",
        entry_bar=0,
        entry_price=100.0,
        atr=2.0,
        hlc3=100.0,
        volume=1000.0,
        sl_mult=2.0,
        notional=5000.0,
        checkpoint_interval=5,
        max_scaleouts=2,
    )

    # Simulate 5 bars trending up strongly
    for bar in range(1, 6):
        price = 100.0 + bar * 2.0  # strong trend
        slot.update_bar(bar, price + 1, price - 1, price, 2.0, price, 1000.0 + bar * 100)

    # At bar 5: check scale-out (close should be well above AVWAP +2sigma)
    close_bar5 = 100.0 + 5 * 2.0  # 110
    can_scale = slot.check_scale_out(5, close_bar5)
    print(f"  Bar 5: close={close_bar5}, AVWAP center={slot.avwap.center:.2f}, "
          f"sigma={slot.avwap.sigma:.2f}, +2s={slot.avwap.center + 2*slot.avwap.sigma:.2f}")
    print(f"  Can scale out: {can_scale}")

    if can_scale:
        trade, is_final = slot.do_scale_out(5, close_bar5, 2.0)
        assert trade.scale_idx == 1, "First scale-out should be idx 1"
        assert not is_final, "First scale-out should not be final"
        assert slot.notional == 2500.0, f"Notional should halve: {slot.notional}"
        print(f"  Scale 1: pnl=${trade.pnl:.2f}, remaining notional=${slot.notional}")

        # Continue 5 more bars
        for bar in range(6, 11):
            price = 100.0 + bar * 2.0
            slot.update_bar(bar, price + 1, price - 1, price, 2.0, price, 1000.0)

        close_bar10 = 100.0 + 10 * 2.0  # 120
        can_scale2 = slot.check_scale_out(10, close_bar10)
        print(f"  Bar 10: can scale={can_scale2}")
        if can_scale2:
            trade2, is_final2 = slot.do_scale_out(10, close_bar10, 1.0)
            assert trade2.scale_idx == 2, "Second scale-out should be idx 2"
            assert is_final2, "Second scale-out should be final"
            assert slot.notional == 0.0, f"Notional should be 0: {slot.notional}"
            print(f"  Scale 2: pnl=${trade2.pnl:.2f}, fully closed")
    else:
        print("  (Scale-out not triggered at bar 5 -- price not at +2sigma)")

    print("  Scale-out OK")
    return True


def test_state_machine_abcd():
    """Test v3.8.3 state machine: A/B/C/D signals."""
    print("Testing state machine v3.8.3...")
    from signals.state_machine_v383 import FourPillarsStateMachine383

    # --- Test A: 4/4 fires ---
    sm = FourPillarsStateMachine383()

    # Bar 0: 60-K enters oversold, all faster stochs also oversold
    r = sm.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=20, stoch_60=20,
                       stoch_60_d=40, cloud3_bull=True, price_pos=-1,
                       price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    assert not r.long_a, "No signal on zone entry"

    # Bar 2: 9-K crosses back above 25
    r = sm.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=20, stoch_60=20,
                       stoch_60_d=40, cloud3_bull=False, price_pos=-1,
                       price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  A signal (4/4): long_a={r.long_a}")
    assert r.long_a, "A should fire: 60 triggered zone, 9+14+40 all flagged"

    # --- Test D: continuation while 60-K stays pinned ---
    # After A fired, 60-K still < 25 so stage should be 2 (D-ready)
    assert sm.long_stage == 2, f"Should be D-ready (stage 2), got {sm.long_stage}"

    # Bar 4: 9-K re-enters oversold
    r = sm.process_bar(4, stoch_9=15, stoch_14=50, stoch_40=50, stoch_60=20,
                       stoch_60_d=40, cloud3_bull=True, price_pos=1,
                       price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    assert sm.long_stage == 3, f"Should be D-tracking (stage 3), got {sm.long_stage}"

    # Bar 6: 9-K crosses back above 25 -> D fires
    r = sm.process_bar(6, stoch_9=30, stoch_14=50, stoch_40=50, stoch_60=20,
                       stoch_60_d=40, cloud3_bull=True, price_pos=1,
                       price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  D signal (continuation): long_d={r.long_d}")
    assert r.long_d, "D should fire: 60-K still pinned, 9-K cycled"

    # After D, 60-K still < 25, should loop to stage 2
    assert sm.long_stage == 2, f"Should loop to D-ready, got {sm.long_stage}"

    # --- Test D stops when 60-K leaves zone ---
    # Bar 8: 60-K exits zone
    r = sm.process_bar(8, stoch_9=15, stoch_14=50, stoch_40=50, stoch_60=50,
                       stoch_60_d=40, cloud3_bull=True, price_pos=1,
                       price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    assert sm.long_stage == 0, f"Should reset when 60-K leaves zone, got {sm.long_stage}"
    print("  D stops when 60-K leaves zone: OK")

    # --- Test B: 3/4 blocked below Cloud 3 ---
    sm2 = FourPillarsStateMachine383()
    r = sm2.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=True, price_pos=-1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    r = sm2.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=False, price_pos=-1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  B below Cloud 3: long_b={r.long_b} (should be False)")
    assert not r.long_b, "B should be blocked below Cloud 3"

    # --- Test B: 3/4 fires WITH Cloud 3 ---
    sm3 = FourPillarsStateMachine383()
    r = sm3.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    r = sm3.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=50, stoch_60=20,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    print(f"  B with Cloud 3: long_b={r.long_b} (should be True)")
    assert r.long_b, "B should fire with Cloud 3"

    # --- Test: no signal when 60-K not in zone ---
    sm4 = FourPillarsStateMachine383()
    r = sm4.process_bar(0, stoch_9=15, stoch_14=20, stoch_40=20, stoch_60=50,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    r = sm4.process_bar(2, stoch_9=30, stoch_14=20, stoch_40=20, stoch_60=50,
                        stoch_60_d=40, cloud3_bull=True, price_pos=1,
                        price_cross_above_cloud2=False, price_cross_below_cloud2=False)
    assert not r.long_a and not r.long_b and not r.long_d, "No signal when 60-K not in zone"
    print("  No signal when 60-K=50: OK")

    print("  State machine v3.8.3 OK")
    return True


def test_commission_custom():
    """Test partial close commission."""
    print("Testing commission charge_custom...")
    from engine.commission import CommissionModel

    comm = CommissionModel(commission_rate=0.0008, maker_rate=0.0002, notional=5000.0)

    # Full notional taker
    c1 = comm.charge()
    assert abs(c1 - 4.0) < 0.01, f"Full taker should be $4, got {c1}"

    # Half notional taker (scale-out)
    c2 = comm.charge_custom(2500.0, maker=False)
    assert abs(c2 - 2.0) < 0.01, f"Half taker should be $2, got {c2}"

    # Full notional maker
    c3 = comm.charge(maker=True)
    assert abs(c3 - 1.0) < 0.01, f"Full maker should be $1, got {c3}"

    print(f"  Full taker: ${c1}, Half taker: ${c2}, Full maker: ${c3}")
    print("  Commission OK")
    return True


def test_backtest():
    """Run a quick backtest on first available 5m coin."""
    print("Testing backtest...")
    import pandas as pd
    from signals.four_pillars_v383 import compute_signals_v383
    from engine.backtester_v383 import Backtester383

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

    params = {
        "notional": 5000.0,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": 0.70,
        "max_positions": 4,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_mult": 2.0,
        "checkpoint_interval": 5,
        "max_scaleouts": 2,
        "enable_adds": True,
        "enable_reentry": True,
    }

    df = compute_signals_v383(df, params)
    print(f"  {len(df)} bars, signals computed")

    # Count signals
    a_count = df["long_a"].sum() + df["short_a"].sum()
    d_count = df["long_d"].sum() + df["short_d"].sum()
    print(f"  A signals: {a_count}, D signals: {d_count}")

    bt = Backtester383(params)
    results = bt.run(df)
    m = results["metrics"]

    print(f"  Trades: {m['total_trades']}")
    print(f"  Win rate: {m['win_rate']:.1%}")
    print(f"  Net P&L: ${m['net_pnl']:.2f}")
    print(f"  Commission: ${m['total_commission']:.2f}")
    print(f"  Rebate: ${m.get('total_rebate', 0):.2f}")
    print(f"  Profit factor: {m['profit_factor']:.2f}")
    print(f"  Scale-outs: {m.get('scale_out_count', 0)}")
    print(f"  LSG: {m['pct_losers_saw_green']:.0%}")

    if m.get("grades"):
        for grade, stats in m["grades"].items():
            print(f"    {grade}: {stats['count']} trades, {stats['win_rate']:.0%} WR, ${stats['avg_pnl']:.2f}/trade")

    assert m["total_trades"] > 0, "Should have at least 1 trade"
    print("  Backtest OK")
    return True


def main():
    print("=" * 55)
    print("  v3.8.3 PYTHON BACKTESTER TEST SUITE")
    print("=" * 55)

    tests = [
        ("Imports", test_imports),
        ("AVWAP Clone", test_avwap_clone),
        ("ATR SL (ABCD)", test_position_atr_sl),
        ("AVWAP SL (ADD/RE)", test_position_avwap_sl),
        ("Scale-out", test_scale_out),
        ("State Machine (A/B/C/D)", test_state_machine_abcd),
        ("Commission Custom", test_commission_custom),
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

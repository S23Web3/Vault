"""
Unit tests for TTP engine (ttp_engine.py).
6 tests covering long/short, ambiguous candles, activation candle, and post-close.

Run:
    cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
    python -m pytest tests/test_ttp_engine.py -v
"""
import sys
from pathlib import Path

# Add parent dir to path so ttp_engine can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ttp_engine import TTPExit


def test_short_clean_sequential():
    """Short -- clean sequential from TTP spec walk-through."""
    # Entry at 100.0, ACT=0.5%, DIST=0.2%
    # Activation price = 100 * 0.995 = 99.5
    engine = TTPExit("SHORT", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Candle 1: H=100.1, L=99.8 -- below activation (99.8 > 99.5) -- still monitoring
    r = engine.evaluate(100.1, 99.8)
    assert r.state == "MONITORING"

    # Candle 2: H=100.0, L=99.7 -- still above 99.5
    r = engine.evaluate(100.0, 99.7)
    assert r.state == "MONITORING"

    # Candle 3: H=99.8, L=99.5 -- hits activation (L <= 99.5)
    r = engine.evaluate(99.8, 99.5)
    assert engine.state == "ACTIVATED"
    # extreme = activation_price = 99.5, trail = 99.5 * 1.002 = 99.699
    assert engine.extreme == 99.5

    # Candle 4: H=99.6, L=99.2 -- new low
    r = engine.evaluate(99.6, 99.2)
    assert engine.state == "ACTIVATED"
    # pess: H=99.6 < trail(99.699), no close. L=99.2 < 99.5 -> extreme=99.2, trail=99.2*1.002=99.3984
    assert abs(engine.extreme - 99.2) < 0.0001

    # Candle 5: H=99.3, L=98.9 -- new low
    r = engine.evaluate(99.3, 98.9)
    assert engine.state == "ACTIVATED"
    assert abs(engine.extreme - 98.9) < 0.0001
    # trail = 98.9 * 1.002 = 99.0978

    # Candle 6: H=99.1, L=99.0 -- reversal hits trail
    r = engine.evaluate(99.1, 99.0)
    # trail was 99.0978, H=99.1 >= 99.0978 -> pess closes
    assert r.closed_pessimistic is True
    assert engine.state == "CLOSED"
    assert r.exit_pct_pessimistic is not None


def test_short_ambiguous_candle():
    """Short -- ambiguous candle: new low AND reversal on same candle."""
    engine = TTPExit("SHORT", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Activate: L=99.5
    engine.evaluate(100.0, 99.5)
    assert engine.state == "ACTIVATED"

    # Push extreme lower: L=99.2
    engine.evaluate(99.3, 99.2)
    # trail = 99.2 * 1.002 = 99.3984

    # Push further: L=98.9
    engine.evaluate(99.0, 98.9)
    # pess trail = 98.9 * 1.002 = 99.0978

    # Ambiguous candle: L=98.8 (new low), H=99.05 (near trail 99.0978)
    # Pessimistic: check H first -> 99.05 < 99.0978 -> no close. Then update extreme to 98.8
    # Optimistic: update extreme to 98.8 first -> trail = 98.8*1.002 = 98.9976. Then H=99.05 >= 98.9976 -> CLOSE
    r = engine.evaluate(99.05, 98.8)

    assert r.closed_pessimistic is False
    assert r.closed_optimistic is True


def test_long_clean_sequential():
    """Long -- clean sequential mirror of short test."""
    engine = TTPExit("LONG", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Below activation
    r = engine.evaluate(100.3, 99.9)
    assert r.state == "MONITORING"

    # Hit activation: H >= 100.5
    r = engine.evaluate(100.5, 100.2)
    assert engine.state == "ACTIVATED"
    assert engine.extreme == 100.5  # activation_price = 100.5

    # New high
    r = engine.evaluate(100.8, 100.4)
    assert abs(engine.extreme - 100.8) < 0.0001
    # trail = 100.8 * 0.998 = 100.5984

    # Another new high
    r = engine.evaluate(101.1, 100.7)
    assert abs(engine.extreme - 101.1) < 0.0001
    # trail = 101.1 * 0.998 = 100.8978

    # Reversal: L <= trail (100.8978)
    r = engine.evaluate(101.0, 100.8)
    assert r.closed_pessimistic is True
    assert engine.state == "CLOSED"


def test_long_ambiguous_candle():
    """Long -- ambiguous candle: new high AND reversal on same candle."""
    engine = TTPExit("LONG", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Activate
    engine.evaluate(100.5, 100.2)
    assert engine.state == "ACTIVATED"

    # Push extreme higher
    engine.evaluate(100.8, 100.4)
    # trail = 100.8 * 0.998 = 100.5984

    engine.evaluate(101.1, 100.7)
    # trail = 101.1 * 0.998 = 100.8978

    # Ambiguous: H=101.2 (new high), L=100.95 (near trail)
    # Pess: check L first -> 100.95 > 100.8978 -> no close. Update extreme to 101.2
    # Opt: update extreme to 101.2 -> trail=101.2*0.998=100.9976. L=100.95 < 100.9976 -> CLOSE
    r = engine.evaluate(101.2, 100.95)

    assert r.closed_pessimistic is False
    assert r.closed_optimistic is True


def test_activation_candle_trail_update():
    """Activation candle should also update extreme beyond activation price."""
    # Short: entry=100, activation=99.5
    # Single candle that activates AND extends further
    engine = TTPExit("SHORT", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Candle: H=99.8, L=99.3 (L < activation 99.5, AND L extends past activation)
    r = engine.evaluate(99.8, 99.3)

    # After activation, extreme should be updated to 99.3 (not stuck at 99.5)
    # because the candle's full range is evaluated after activation
    assert engine.state == "ACTIVATED"
    assert engine.extreme < 99.5  # extreme moved past activation price
    assert abs(engine.extreme - 99.3) < 0.0001


def test_engine_stops_after_close():
    """After CLOSED state, evaluate() returns CLOSED with no mutation."""
    engine = TTPExit("LONG", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Activate
    engine.evaluate(100.5, 100.2)
    # Push high
    engine.evaluate(101.0, 100.5)
    # trail = 101.0 * 0.998 = 100.798

    # Close: L <= trail
    r = engine.evaluate(100.9, 100.7)
    assert engine.state == "CLOSED"
    saved_extreme = engine.extreme
    saved_trail = engine.trail_level

    # Call again after close -- should return CLOSED, no state change
    r2 = engine.evaluate(105.0, 95.0)
    assert r2.state == "CLOSED"
    assert r2.closed_pessimistic is False
    assert r2.closed_optimistic is False
    assert engine.extreme == saved_extreme
    assert engine.trail_level == saved_trail

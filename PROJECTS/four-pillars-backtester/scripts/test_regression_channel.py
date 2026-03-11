"""
Tests for regression_channel module.
Run: python scripts/test_regression_channel.py
"""
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signals.regression_channel import (
    fit_channel,
    extrapolate_center,
    price_in_lower_half,
    compute_channel_anchored,
    pre_stage1_gate,
)

PASS_COUNT = 0
FAIL_COUNT = 0


def report(name, ok, details):
    """Print test name, details, and PASS/FAIL; update global counters."""
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if ok else "FAIL"
    print(name + " -> " + status + ("  " + details if details else ""))
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1


def test_orderly_decline():
    """Test 1: clean linear decline passes the pre-stage-1 gate."""
    rng = np.random.default_rng(42)
    prices = np.linspace(100.0, 94.0, 30) + rng.normal(0, 0.05, 30)
    ch = fit_channel(prices)
    gate = pre_stage1_gate(ch)
    details = "r2=" + str(round(ch.r_squared, 4)) + " slope_pct=" + str(round(ch.slope_pct, 6)) + " gate=" + str(gate)
    ok = ch.r_squared > 0.85 and ch.slope_pct < -0.001 and gate
    report("Test 1: Orderly decline", ok, details)


def test_v_bottom():
    """Test 2: V-bottom pattern fails the pre-stage-1 gate."""
    prices = [100.0] * 15 + [90.0, 90.0] + [100.0, 100.0]
    ch = fit_channel(prices)
    gate = pre_stage1_gate(ch)
    details = "r2=" + str(round(ch.r_squared, 4)) + " gate=" + str(gate)
    ok = ch.r_squared < 0.25 and not gate
    report("Test 2: V-bottom", ok, details)


def test_sideways_chop():
    """Test 3: sideways sin oscillation fails the pre-stage-1 gate."""
    x = np.arange(30)
    prices = 100.0 + 0.5 * np.sin(x)
    ch = fit_channel(prices)
    gate = pre_stage1_gate(ch)
    details = "slope_pct=" + str(round(ch.slope_pct, 6)) + " r2=" + str(round(ch.r_squared, 4)) + " gate=" + str(gate)
    ok = abs(ch.slope_pct) < 0.0005 and ch.r_squared < 0.2 and not gate
    report("Test 3: Sideways chop", ok, details)


def test_anchored_lower_half_accept():
    """Test 4: price at Stage 2 trough is in lower half of anchored channel — ACCEPT."""
    seg_a = np.linspace(100.0, 96.0, 5)
    seg_b = np.linspace(96.0, 99.0, 5)
    seg_c = np.linspace(99.0, 93.0, 5)
    prices = list(seg_a) + list(seg_b) + list(seg_c)
    ch = compute_channel_anchored(prices, 0, 14)
    current_price = 93.0
    result = price_in_lower_half(current_price, ch.center_at_last)
    details = "center=" + str(round(ch.center_at_last, 4)) + " price=" + str(current_price) + " result=" + str(result)
    ok = result is True
    report("Test 4: Anchored lower half ACCEPT", ok, details)


def test_anchored_upper_half_reject():
    """Test 5: price in upper half of anchored channel returns REJECT."""
    seg_a = np.linspace(100.0, 96.0, 5)
    seg_b = np.linspace(96.0, 99.0, 5)
    seg_c = np.linspace(99.0, 93.0, 5)
    seg_d = np.linspace(93.0, 98.0, 5)
    prices = list(seg_a) + list(seg_b) + list(seg_c) + list(seg_d)
    ch = compute_channel_anchored(prices, 0, 19)
    current_price = 98.0
    result = price_in_lower_half(current_price, ch.center_at_last)
    details = "center=" + str(round(ch.center_at_last, 4)) + " price=" + str(current_price) + " result=" + str(result)
    ok = result is False
    report("Test 5: Anchored upper half REJECT", ok, details)


def test_extrapolate_center():
    """Test 6: extrapolating a declining channel extends slope downward."""
    prices = np.linspace(100.0, 95.0, 20)
    ch = fit_channel(prices)
    extrapolated = extrapolate_center(ch, 5)
    expected = ch.center_at_last + ch.slope * 5
    ok = extrapolated < ch.center_at_last and abs(extrapolated - expected) < 1e-9
    details = "center_at_last=" + str(round(ch.center_at_last, 6)) + " extrapolated=" + str(round(extrapolated, 6))
    report("Test 6: extrapolate_center", ok, details)


def test_price_in_lower_half_boundary():
    """Test 7: strict boundary: equal to center = not lower half."""
    r1 = price_in_lower_half(99.9, 100.0)
    r2 = price_in_lower_half(100.0, 100.0)
    r3 = price_in_lower_half(100.1, 100.0)
    details = "99.9<100=" + str(r1) + " 100.0<100=" + str(r2) + " 100.1<100=" + str(r3)
    ok = r1 is True and r2 is False and r3 is False
    report("Test 7: price_in_lower_half boundary", ok, details)


def test_edge_cases_no_exceptions():
    """Test 8: degenerate inputs return zero result without raising exceptions."""
    results = []
    try:
        r0 = fit_channel([])
        results.append("empty r2=" + str(r0.r_squared))
        r1 = fit_channel([100.0])
        results.append("len1 r2=" + str(r1.r_squared))
        r2 = fit_channel([100.0, 100.0])
        results.append("len2 r2=" + str(r2.r_squared))
        r3 = fit_channel([100.0, 100.0, 100.0])
        results.append("flat r2=" + str(r3.r_squared))
        r4 = compute_channel_anchored(list(range(100)), 5, 6)
        results.append("2bar r2=" + str(r4.r_squared))
        ok = True
    except Exception as e:
        results.append("EXCEPTION: " + str(e))
        ok = False
    report("Test 8: Edge cases no exceptions", ok, " | ".join(results))


def test_pre_lookback_sensitivity():
    """Test 9: gate is stable across 10, 20, 30 bar windows of the same orderly decline."""
    rng = np.random.default_rng(42)
    prices = np.linspace(100.0, 94.0, 30) + rng.normal(0, 0.05, 30)
    results = []
    all_pass = True
    for n in [10, 20, 30]:
        window = prices[-n:]
        ch = fit_channel(window)
        gate = pre_stage1_gate(ch)
        results.append("n=" + str(n) + " r2=" + str(round(ch.r_squared, 4)) + " slope_pct=" + str(round(ch.slope_pct, 6)) + " gate=" + str(gate))
        if not gate:
            all_pass = False
    report("Test 9: pre_lookback sensitivity", all_pass, " | ".join(results))


if __name__ == "__main__":
    test_orderly_decline()
    test_v_bottom()
    test_sideways_chop()
    test_anchored_lower_half_accept()
    test_anchored_upper_half_reject()
    test_extrapolate_center()
    test_price_in_lower_half_boundary()
    test_edge_cases_no_exceptions()
    test_pre_lookback_sensitivity()
    print("")
    print("Results: " + str(PASS_COUNT) + " passed, " + str(FAIL_COUNT) + " failed")
    if FAIL_COUNT > 0:
        sys.exit(1)

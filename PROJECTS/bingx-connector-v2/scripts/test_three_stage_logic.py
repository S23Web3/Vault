"""
Test: three-stage position management logic.
Mocks price movement to verify:
  Stage 1 -> Stage 2: BE raises at +0.4% (be_act=0.004)
  Stage 2 -> Stage 3: TTP activates at +0.8% (ttp_act=0.008)
  Stage 3: trail fires at 0.3% pullback from extreme (ttp_dist=0.003)
Run: python scripts/test_three_stage_logic.py
"""
import sys
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ttp_engine import TTPExit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BE_ACT  = 0.004   # +0.4% triggers breakeven
TTP_ACT = 0.008   # +0.8% activates TTP
TTP_DIST = 0.003  # 0.3% trail behind extreme
COMMISSION = 0.0008  # 0.08% per side

PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        log.info("PASS  %s  %s", label, detail)
        PASS += 1
    else:
        log.error("FAIL  %s  %s", label, detail)
        FAIL += 1


def be_triggered(entry, mark, direction):
    """Simulate check_breakeven() logic."""
    if direction == "LONG":
        return mark >= entry * (1.0 + BE_ACT)
    return mark <= entry * (1.0 - BE_ACT)


def be_price(entry, direction):
    """Simulate _place_be_sl() logic."""
    buf = COMMISSION + 0.001
    if direction == "LONG":
        return entry * (1 + buf)
    return entry * (1 - buf)


def run_long_scenario():
    log.info("=== LONG scenario ===")
    entry = 1.0000
    engine = TTPExit("LONG", entry, activation_pct=TTP_ACT, trail_distance_pct=TTP_DIST)

    be_act_price  = entry * (1 + BE_ACT)   # 1.0040
    ttp_act_price = entry * (1 + TTP_ACT)  # 1.0080

    # --- Stage 1: price below BE threshold ---
    mark = entry * 1.002  # +0.2% — no trigger yet
    check("LONG S1: no BE below threshold",
          not be_triggered(entry, mark, "LONG"),
          f"mark={mark:.4f} threshold={be_act_price:.4f}")

    result = engine.evaluate(candle_high=mark * 1.001, candle_low=mark * 0.999)
    check("LONG S1: TTP still MONITORING",
          result.state == "MONITORING",
          f"state={result.state}")

    # --- Stage 2: price crosses BE threshold (+0.4%), but not TTP (+0.8%) ---
    mark = entry * 1.005  # +0.5% — crosses BE but not TTP
    check("LONG S2: BE triggers at +0.4%",
          be_triggered(entry, mark, "LONG"),
          f"mark={mark:.4f} threshold={be_act_price:.4f}")

    be_sl = be_price(entry, "LONG")
    check("LONG S2: BE SL placed above entry",
          be_sl > entry,
          f"be_sl={be_sl:.6f} entry={entry:.6f}")

    check("LONG S2: BE SL covers commission",
          be_sl >= entry * (1 + COMMISSION),
          f"be_sl={be_sl:.6f} min={entry*(1+COMMISSION):.6f}")

    # TTP engine still MONITORING at +0.5% (threshold is 0.8%)
    result = engine.evaluate(candle_high=mark, candle_low=mark * 0.999)
    check("LONG S2: TTP still MONITORING at +0.5%",
          result.state == "MONITORING",
          f"state={result.state}")

    # --- Stage 3: price crosses TTP threshold (+0.8%) ---
    mark = entry * 1.009  # +0.9% — crosses TTP threshold
    result = engine.evaluate(candle_high=mark, candle_low=mark * 0.998)
    check("LONG S3: TTP ACTIVATED at +0.8%",
          result.state == "ACTIVATED",
          f"state={result.state} mark={mark:.4f} threshold={ttp_act_price:.4f}")

    check("LONG S3: extreme set at activation candle high",
          engine.extreme is not None and engine.extreme >= ttp_act_price,
          f"extreme={engine.extreme}")

    check("LONG S3: trail_level = extreme * (1 - 0.003)",
          abs(engine.trail_level - engine.extreme * (1 - TTP_DIST)) < 1e-9,
          f"trail={engine.trail_level:.6f} extreme={engine.extreme:.6f}")

    # Price continues up — trail follows
    peak = entry * 1.015  # +1.5%
    result = engine.evaluate(candle_high=peak, candle_low=peak * 0.998)
    expected_trail = peak * (1 - TTP_DIST)
    check("LONG S3: trail advances with price",
          abs(engine.trail_level - expected_trail) < 1e-6,
          f"trail={engine.trail_level:.6f} expected={expected_trail:.6f}")

    # Price pulls back 0.3% from peak — should close (pessimistic)
    pullback = peak * (1 - TTP_DIST - 0.001)  # slightly past trail
    result = engine.evaluate(candle_high=peak * 1.001, candle_low=pullback)
    check("LONG S3: TTP closes on 0.3% pullback",
          result.closed_pessimistic,
          f"closed={result.closed_pessimistic} exit_pct={result.exit_pct_pessimistic}")

    check("LONG S3: exit is profitable (above entry)",
          result.exit_pct_pessimistic is not None and result.exit_pct_pessimistic > 0,
          f"exit_pct={result.exit_pct_pessimistic}")


def run_short_scenario():
    log.info("=== SHORT scenario ===")
    entry = 1.0000
    engine = TTPExit("SHORT", entry, activation_pct=TTP_ACT, trail_distance_pct=TTP_DIST)

    be_act_price  = entry * (1 - BE_ACT)   # 0.9960
    ttp_act_price = entry * (1 - TTP_ACT)  # 0.9920

    # --- Stage 1 ---
    mark = entry * 0.998  # -0.2%
    check("SHORT S1: no BE below threshold",
          not be_triggered(entry, mark, "SHORT"),
          f"mark={mark:.4f} threshold={be_act_price:.4f}")

    result = engine.evaluate(candle_high=mark * 1.001, candle_low=mark * 0.999)
    check("SHORT S1: TTP still MONITORING",
          result.state == "MONITORING",
          f"state={result.state}")

    # --- Stage 2 ---
    mark = entry * 0.995  # -0.5%
    check("SHORT S2: BE triggers at -0.4%",
          be_triggered(entry, mark, "SHORT"),
          f"mark={mark:.4f} threshold={be_act_price:.4f}")

    be_sl = be_price(entry, "SHORT")
    check("SHORT S2: BE SL placed below entry",
          be_sl < entry,
          f"be_sl={be_sl:.6f} entry={entry:.6f}")

    result = engine.evaluate(candle_high=mark * 1.001, candle_low=mark)
    check("SHORT S2: TTP still MONITORING at -0.5%",
          result.state == "MONITORING",
          f"state={result.state}")

    # --- Stage 3 ---
    mark = entry * 0.991  # -0.9%
    result = engine.evaluate(candle_high=mark * 1.001, candle_low=mark)
    check("SHORT S3: TTP ACTIVATED at -0.8%",
          result.state == "ACTIVATED",
          f"state={result.state} mark={mark:.4f} threshold={ttp_act_price:.4f}")

    check("SHORT S3: extreme set at or below activation price",
          engine.extreme is not None and engine.extreme <= ttp_act_price,
          f"extreme={engine.extreme}")

    check("SHORT S3: trail_level = extreme * (1 + 0.003)",
          abs(engine.trail_level - engine.extreme * (1 + TTP_DIST)) < 1e-9,
          f"trail={engine.trail_level:.6f} extreme={engine.extreme:.6f}")

    # Price continues down
    trough = entry * 0.985  # -1.5%
    result = engine.evaluate(candle_high=trough * 1.001, candle_low=trough)
    expected_trail = trough * (1 + TTP_DIST)
    check("SHORT S3: trail advances with price",
          abs(engine.trail_level - expected_trail) < 1e-6,
          f"trail={engine.trail_level:.6f} expected={expected_trail:.6f}")

    # Price bounces 0.3% from trough — should close
    bounce = trough * (1 + TTP_DIST + 0.001)
    result = engine.evaluate(candle_high=bounce, candle_low=trough * 0.999)
    check("SHORT S3: TTP closes on 0.3% bounce",
          result.closed_pessimistic,
          f"closed={result.closed_pessimistic} exit_pct={result.exit_pct_pessimistic}")

    check("SHORT S3: exit is profitable (positive pct)",
          result.exit_pct_pessimistic is not None and result.exit_pct_pessimistic > 0,
          f"exit_pct={result.exit_pct_pessimistic}")


def run_early_reversal():
    """Price never reaches BE — should close at SL, no BE or TTP interaction."""
    log.info("=== Early reversal (SL before BE) ===")
    entry = 1.0000
    engine = TTPExit("LONG", entry, activation_pct=TTP_ACT, trail_distance_pct=TTP_DIST)

    # Price goes up 0.2% then crashes — never hit BE (0.4%) or TTP (0.8%)
    result = engine.evaluate(candle_high=entry * 1.002, candle_low=entry * 0.998)
    check("Early reversal: TTP stays MONITORING",
          result.state == "MONITORING",
          f"state={result.state}")

    be_triggered_flag = be_triggered(entry, entry * 1.002, "LONG")
    check("Early reversal: BE not triggered at +0.2%",
          not be_triggered_flag,
          f"triggered={be_triggered_flag}")


def main():
    log.info("Three-stage logic test  be_act=%.3f  ttp_act=%.3f  ttp_dist=%.3f",
             BE_ACT, TTP_ACT, TTP_DIST)
    run_long_scenario()
    run_short_scenario()
    run_early_reversal()

    print()
    print("=" * 50)
    print("PASS: " + str(PASS) + "  FAIL: " + str(FAIL))
    if FAIL:
        print("RESULT: FAILED")
        sys.exit(1)
    else:
        print("RESULT: ALL PASS")


if __name__ == "__main__":
    main()

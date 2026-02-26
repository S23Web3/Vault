"""
Risk gate: 6 ordered pre-trade checks. Returns (approved, reason).
BUG-C03 fix: check 1 reads halt_flag from state.
BUG-C05 fix: allowed_grades comes from plugin, not connector config.
"""
import logging

logger = logging.getLogger(__name__)


class RiskGate:
    """Evaluate signals against risk rules before execution."""

    def __init__(self, config):
        """Initialize with risk config dict."""
        self.max_positions = config.get("max_positions", 3)
        self.max_daily_trades = config.get("max_daily_trades", 20)
        self.daily_loss_limit = config.get("daily_loss_limit_usd", 75.0)
        self.min_atr_ratio = config.get("min_atr_ratio", 0.003)
        logger.info(
            "RiskGate: max_pos=%d max_trades=%d loss=%.1f atr=%.4f",
            self.max_positions, self.max_daily_trades,
            self.daily_loss_limit, self.min_atr_ratio)

    def evaluate(self, signal, symbol, state, allowed_grades):
        """Run 6 ordered checks. Returns (bool, str)."""
        # Check 1: Hard stop (BUG-C03: halt_flag OR daily_pnl)
        halt = state.get("halt_flag", False)
        pnl = state.get("daily_pnl", 0)
        if halt or pnl <= -self.daily_loss_limit:
            reason = ("BLOCKED: Hard Stop (halt="
                      + str(halt) + " pnl="
                      + str(round(pnl, 2)) + ")")
            logger.warning("Check 1 FAIL: %s", reason)
            return False, reason

        # Check 2: Max positions
        open_count = len(state.get("open_positions", {}))
        if open_count >= self.max_positions:
            reason = ("BLOCKED: Max Positions ("
                      + str(open_count) + "/"
                      + str(self.max_positions) + ")")
            logger.info("Check 2 FAIL: %s", reason)
            return False, reason

        # Check 3: Duplicate position
        key = symbol + "_" + signal.direction
        if key in state.get("open_positions", {}):
            reason = "BLOCKED: Duplicate (" + key + ")"
            logger.info("Check 3 FAIL: %s", reason)
            return False, reason

        # Check 4: Grade filter (BUG-C05: from plugin)
        if signal.grade not in allowed_grades:
            reason = ("BLOCKED: Grade " + signal.grade
                      + " not in " + str(allowed_grades))
            logger.info("Check 4 FAIL: %s", reason)
            return False, reason

        # Check 5: ATR threshold
        if signal.entry_price > 0:
            atr_ratio = signal.atr / signal.entry_price
        else:
            atr_ratio = 0
        if atr_ratio < self.min_atr_ratio:
            reason = ("BLOCKED: Too Quiet (atr_ratio="
                      + str(round(atr_ratio, 6)) + ")")
            logger.info("Check 5 FAIL: %s", reason)
            return False, reason

        # Check 6: Daily trade limit
        daily_trades = state.get("daily_trades", 0)
        if daily_trades >= self.max_daily_trades:
            reason = ("BLOCKED: Trade Limit ("
                      + str(daily_trades) + "/"
                      + str(self.max_daily_trades) + ")")
            logger.info("Check 6 FAIL: %s", reason)
            return False, reason

        logger.info(
            "RiskGate APPROVED: %s %s grade=%s atr=%.4f",
            signal.direction, symbol, signal.grade, atr_ratio)
        return True, "APPROVED"

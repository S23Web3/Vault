"""
Commission model with daily rebate settlement at 5pm UTC.
"""

from datetime import datetime, timezone


class CommissionModel:
    """
    Tracks commission charges and daily rebate settlement.

    Commission = notional * commission_rate per side.
    Default: 0.08% (0.0008) taker rate.
    Rebate: accumulated per day, credited to equity at settlement_hour UTC.
    """

    def __init__(self, commission_rate: float = 0.0008, maker_rate: float = 0.0002,
                 notional: float = 10000.0,
                 rebate_pct: float = 0.70, settlement_hour_utc: int = 17):
        """
        Args:
            commission_rate: Taker rate per side (0.0008 = 0.08%) for market/stop orders
            maker_rate: Maker rate per side (0.0002 = 0.02%) for limit orders
            notional: Trade notional (margin * leverage)
            rebate_pct: Daily rebate percentage (0.70 = 70%)
            settlement_hour_utc: Hour for daily rebate settlement
        """
        self.cost_per_side = notional * commission_rate
        self.maker_cost_per_side = notional * maker_rate
        self.commission_rate = commission_rate
        self.maker_rate = maker_rate
        self.notional = notional
        self.rebate_pct = rebate_pct
        self.settlement_hour_utc = settlement_hour_utc

        # Running totals
        self.total_commission = 0.0
        self.total_rebate = 0.0
        self.total_volume = 0.0
        self.total_sides = 0
        self.daily_commission = 0.0
        self.sides_today = 0
        self._last_settlement_day = None

    def charge(self, maker: bool = False) -> float:
        """Charge one side of commission. Returns the amount charged.
        maker=True uses maker rate (0.02%), False uses taker rate (0.08%)."""
        cost = self.maker_cost_per_side if maker else self.cost_per_side
        self.total_commission += cost
        self.total_volume += self.notional
        self.total_sides += 1
        self.daily_commission += cost
        self.sides_today += 1
        return cost

    def charge_custom(self, notional: float, maker: bool = False) -> float:
        """Charge commission on a custom notional (for partial closes).
        Returns the amount charged."""
        rate = self.maker_rate if maker else self.commission_rate
        cost = notional * rate
        self.total_commission += cost
        self.total_volume += notional
        self.total_sides += 1
        self.daily_commission += cost
        self.sides_today += 1
        return cost

    def check_settlement(self, bar_datetime: datetime) -> float:
        """
        Check if we've crossed the 5pm UTC settlement boundary.
        If so, credit the rebate and reset daily counter.
        Returns the rebate amount credited (0 if no settlement).
        """
        if bar_datetime.tzinfo is None:
            bar_datetime = bar_datetime.replace(tzinfo=timezone.utc)

        current_day = bar_datetime.date()
        current_hour = bar_datetime.hour

        # First bar -- initialize
        if self._last_settlement_day is None:
            self._last_settlement_day = current_day
            return 0.0

        # Check if we've crossed settlement time
        settled = False
        if current_day > self._last_settlement_day and current_hour >= self.settlement_hour_utc:
            settled = True

        if settled and self.daily_commission > 0:
            rebate = self.daily_commission * self.rebate_pct
            self.total_rebate += rebate
            self.daily_commission = 0.0
            self.sides_today = 0
            self._last_settlement_day = current_day
            return rebate

        if current_day > self._last_settlement_day and current_hour >= self.settlement_hour_utc:
            self._last_settlement_day = current_day

        return 0.0

    @property
    def net_commission(self) -> float:
        """Total commission minus total rebates received."""
        return self.total_commission - self.total_rebate

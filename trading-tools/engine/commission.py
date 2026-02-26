"""
Commission model with daily rebate settlement at 5pm UTC.
"""

from datetime import datetime, timezone


class CommissionModel:
    """
    Tracks commission charges and daily rebate settlement.

    Raw: $6 deducted per side (entry and exit).
    Rebate: accumulated per day, credited to equity at settlement_hour UTC.
    """

    def __init__(self, cost_per_side: float = 6.0, rebate_pct: float = 0.70,
                 settlement_hour_utc: int = 17):
        self.cost_per_side = cost_per_side
        self.rebate_pct = rebate_pct
        self.settlement_hour_utc = settlement_hour_utc

        # Running totals
        self.total_commission = 0.0
        self.total_rebate = 0.0
        self.daily_commission = 0.0
        self.sides_today = 0
        self._last_settlement_day = None

    def charge(self) -> float:
        """Charge one side of commission. Returns the amount charged."""
        self.total_commission += self.cost_per_side
        self.daily_commission += self.cost_per_side
        self.sides_today += 1
        return self.cost_per_side

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

        # First bar — initialize
        if self._last_settlement_day is None:
            self._last_settlement_day = current_day
            return 0.0

        # Check if we've crossed settlement time
        settled = False
        if current_day > self._last_settlement_day and current_hour >= self.settlement_hour_utc:
            settled = True
        elif current_day > self._last_settlement_day:
            # Day changed but not yet settlement hour — check if we skipped a day
            pass

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

"""
Regression channel module: pre-stage-1 orderly decline gate and stage-1-to-stage-2 anchored channel.

Integration context (state machine caller, do not implement here):

  At Stage 1 entry (stoch_9 crosses below 25 for first time):
    self.stage1_bar = current_bar_index
    pre_window = prices[current_bar - pre_lookback : current_bar + 1]
    self.pre_ch = fit_channel(pre_window)
    self.ch_gate_passed = pre_stage1_gate(self.pre_ch)

  At Stage 2 exit (stoch_9 crosses above 25, divergence confirmed):
    if not self.ch_gate_passed:
        reject signal
    anchored = compute_channel_anchored(prices, self.stage1_bar, current_bar)
    if price_in_lower_half(current_price, anchored.center_at_last):
        fire entry signal
    else:
        reject signal
"""
from collections import namedtuple
import numpy as np


ChannelResult = namedtuple(
    "ChannelResult",
    ["slope", "slope_pct", "r_squared", "band_width_pct", "center_at_last", "std_residuals"],
)

_ZERO = ChannelResult(
    slope=0.0,
    slope_pct=0.0,
    r_squared=0.0,
    band_width_pct=0.0,
    center_at_last=0.0,
    std_residuals=0.0,
)


def fit_channel(prices) -> ChannelResult:
    """Fit linear regression to prices; return ChannelResult or zero on degenerate input."""
    arr = np.asarray(prices, dtype=float)
    n = len(arr)
    if n < 3:
        return _ZERO
    x = np.arange(n, dtype=float)
    mean_x = np.mean(x)
    mean_y = np.mean(arr)
    ss_xx = np.sum((x - mean_x) ** 2)
    if ss_xx == 0.0:
        return _ZERO
    slope = np.sum((x - mean_x) * (arr - mean_y)) / ss_xx
    intercept = mean_y - slope * mean_x
    fitted = intercept + slope * x
    residuals = arr - fitted
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((arr - mean_y) ** 2)
    r_squared = 0.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    center_at_last = intercept + slope * (n - 1)
    std_res = float(np.std(residuals))
    slope_pct = slope / mean_y if mean_y != 0.0 else 0.0
    band_width_pct = (2.0 * std_res / mean_y) if mean_y != 0.0 else 0.0
    return ChannelResult(
        slope=float(slope),
        slope_pct=float(slope_pct),
        r_squared=float(r_squared),
        band_width_pct=float(band_width_pct),
        center_at_last=float(center_at_last),
        std_residuals=float(std_res),
    )


def extrapolate_center(channel: ChannelResult, bars_elapsed: int) -> float:
    """Extend regression center forward by bars_elapsed bars past the fit window."""
    if bars_elapsed <= 0:
        return channel.center_at_last
    return channel.center_at_last + channel.slope * bars_elapsed


def price_in_lower_half(price: float, center: float) -> bool:
    """Return True if price is strictly below center (regression midline)."""
    return price < center


def compute_channel_anchored(all_prices, start_idx: int, end_idx: int) -> ChannelResult:
    """Compute regression over all_prices[start_idx:end_idx+1]; return zero if window < 3."""
    window = all_prices[start_idx : end_idx + 1]
    return fit_channel(window)


def pre_stage1_gate(channel: ChannelResult, r2_min: float = 0.45, slope_pct_max: float = -0.001) -> bool:
    """Return True if channel shows orderly negative slope with sufficient R-squared."""
    return channel.r_squared > r2_min and channel.slope_pct < slope_pct_max

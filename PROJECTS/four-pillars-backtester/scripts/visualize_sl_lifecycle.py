"""
SL/TP Lifecycle Visualization — 55/89 EMA Cross Scalp.

Generates 8 sequential matplotlib figures showing every possible
trade outcome scenario. Each plot has two subplots:
  - Top: price action with SL/TP levels, AVWAP bands, phase annotations
  - Bottom: stoch 9,3 D with overzone thresholds

Run: python scripts/visualize_sl_lifecycle.py
Output: results/sl_lifecycle/ (PNG per scenario)
"""

import sys
import logging
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "results" / "sl_lifecycle"

# --- Dark theme ---
DARK_BG = "#0f1419"
DARK_CARD = "#1a1f26"
CLR_PRICE = "#e7e9ea"
CLR_SL = "#ef4444"
CLR_BE = "#f59e0b"
CLR_AVWAP_CENTER = "#3b82f6"
CLR_AVWAP_2S = "#8b5cf6"
CLR_TP = "#10b981"
CLR_ENTRY = "#6b7280"
CLR_STOCH = "#f97316"
CLR_OVERZONE = "#ef444480"
CLR_PHASE_TEXT = "#9ca3af"
CLR_CLOUD4 = "#10b98180"


def apply_dark_theme(fig, axes):
    """Apply dark background to figure and all axes."""
    fig.patch.set_facecolor(DARK_BG)
    for ax in axes:
        ax.set_facecolor(DARK_CARD)
        ax.tick_params(colors=CLR_PRICE, labelsize=8)
        ax.xaxis.label.set_color(CLR_PRICE)
        ax.yaxis.label.set_color(CLR_PRICE)
        ax.title.set_color(CLR_PRICE)
        for spine in ax.spines.values():
            spine.set_color("#333333")
        ax.grid(True, alpha=0.15, color="#444444")


def generate_price_path(n_bars, entry_price, seed, trend="up", pullback_bars=None):
    """Generate synthetic price path with controlled shape."""
    rng = np.random.default_rng(seed)
    prices = np.zeros(n_bars)
    prices[0] = entry_price
    noise_scale = entry_price * 0.002

    for i in range(1, n_bars):
        drift = 0.0
        if trend == "up":
            drift = entry_price * 0.001
        elif trend == "down":
            drift = -entry_price * 0.001
        elif trend == "flat":
            drift = 0.0

        if pullback_bars and i in pullback_bars:
            drift = -abs(drift) * 2.5 if trend == "up" else abs(drift) * 2.5

        prices[i] = prices[i - 1] + drift + rng.normal(0, noise_scale)

    return prices


def compute_avwap_bands(prices, volumes):
    """Compute cumulative AVWAP center and sigma bands."""
    hlc3 = prices  # simplified: using close as hlc3
    cum_pv = np.cumsum(hlc3 * volumes)
    cum_v = np.cumsum(volumes)
    cum_pv2 = np.cumsum(hlc3 * hlc3 * volumes)

    center = cum_pv / cum_v
    variance = np.maximum((cum_pv2 / cum_v) - center ** 2, 0.0)
    sigma = np.sqrt(variance)

    return center, sigma


def generate_stoch_d(n_bars, seed, overzone_windows=None, is_long=True):
    """Generate synthetic stoch 9,3 D line with controlled overzone events."""
    rng = np.random.default_rng(seed)
    stoch = np.full(n_bars, 50.0)

    # base oscillation
    for i in range(1, n_bars):
        stoch[i] = stoch[i - 1] + rng.normal(0, 5)
        stoch[i] = np.clip(stoch[i], 5, 95)

    # inject overzone events
    if overzone_windows:
        for start, end, target in overzone_windows:
            mid = (start + end) // 2
            for i in range(start, min(end + 1, n_bars)):
                if i <= mid:
                    t = (i - start) / max(mid - start, 1)
                    stoch[i] = stoch[start] + t * (target - stoch[start])
                else:
                    t = (i - mid) / max(end - mid, 1)
                    if is_long:
                        stoch[i] = target + t * (30 - target)
                    else:
                        stoch[i] = target + t * (70 - target)

    return np.clip(stoch, 0, 100)


def draw_phase_bracket(ax, x_start, x_end, y_pos, label, color=CLR_PHASE_TEXT):
    """Draw a phase bracket annotation below the price chart."""
    ax.annotate(
        "", xy=(x_start, y_pos), xytext=(x_end, y_pos),
        arrowprops=dict(arrowstyle="<->", color=color, lw=1.5),
    )
    mid = (x_start + x_end) / 2
    ax.text(mid, y_pos * 0.998, label, ha="center", va="top",
            fontsize=7, color=color, fontstyle="italic")


def plot_scenario(scenario_num, title, description, prices, stoch_d,
                  entry_bar, entry_price, atr, sl_levels, be_level,
                  avwap_anchor_bar, avwap_anchor_level, ratchet_bars,
                  ratchet_levels, tp_level, tp_bar, exit_bar, exit_type,
                  cloud4_level, is_long=True):
    """Plot a single scenario with price + stoch subplots."""
    n_bars = len(prices)
    bars = np.arange(n_bars)

    fig, (ax_price, ax_stoch) = plt.subplots(
        2, 1, figsize=(14, 8), height_ratios=[3, 1],
        gridspec_kw={"hspace": 0.08},
    )
    apply_dark_theme(fig, [ax_price, ax_stoch])

    fig.suptitle(
        f"Scenario {scenario_num}: {title}",
        color=CLR_PRICE, fontsize=13, fontweight="bold", y=0.97,
    )

    # --- Price subplot ---
    ax_price.plot(bars, prices, color=CLR_PRICE, linewidth=1.2, label="Price", zorder=5)

    # entry marker
    ax_price.plot(entry_bar, entry_price, "^" if is_long else "v",
                  color=CLR_TP if is_long else CLR_SL, markersize=12, zorder=10)
    ax_price.axhline(entry_price, color=CLR_ENTRY, linestyle="--", linewidth=0.7, alpha=0.5)
    ax_price.text(0.5, entry_price, "ENTRY", fontsize=7, color=CLR_ENTRY, va="bottom")

    # SL line (stepped)
    sl_x = [s[0] for s in sl_levels]
    sl_y = [s[1] for s in sl_levels]
    ax_price.step(sl_x, sl_y, where="post", color=CLR_SL, linewidth=1.5,
                  linestyle="-", label="Stop Loss", zorder=6)

    # BE level
    if be_level is not None:
        ax_price.axhline(be_level, color=CLR_BE, linestyle=":", linewidth=0.8, alpha=0.6)
        ax_price.text(0.5, be_level, "BE", fontsize=7, color=CLR_BE, va="bottom")

    # AVWAP anchor
    if avwap_anchor_bar is not None and avwap_anchor_level is not None:
        ax_price.plot(avwap_anchor_bar, avwap_anchor_level, "D",
                      color=CLR_AVWAP_2S, markersize=8, zorder=8)
        ax_price.axhline(avwap_anchor_level, color=CLR_AVWAP_2S, linestyle="--",
                         linewidth=0.7, alpha=0.4,
                         xmin=avwap_anchor_bar / n_bars, xmax=1.0)
        ax_price.text(avwap_anchor_bar + 0.5, avwap_anchor_level,
                      "AVWAP -2s frozen", fontsize=7, color=CLR_AVWAP_2S, va="top")

    # Ratchet markers
    for i, (rb, rl) in enumerate(zip(ratchet_bars, ratchet_levels)):
        ax_price.plot(rb, rl, "D", color=CLR_AVWAP_2S, markersize=7, zorder=8)
        ax_price.text(rb + 0.3, rl, f"R{i + 1}", fontsize=7,
                      color=CLR_AVWAP_2S, va="bottom", fontweight="bold")

    # Cloud 4 level
    if cloud4_level is not None:
        ax_price.axhline(cloud4_level, color=CLR_CLOUD4, linestyle="-",
                         linewidth=1.5, alpha=0.4)
        ax_price.text(n_bars - 3, cloud4_level, "Cloud 4", fontsize=7,
                      color=CLR_TP, va="bottom", ha="right")

    # TP level
    if tp_level is not None:
        ax_price.axhline(tp_level, color=CLR_TP, linestyle="--", linewidth=1.2, alpha=0.7)
        ax_price.text(n_bars - 3, tp_level, f"TP (C4+ATR)", fontsize=7,
                      color=CLR_TP, va="bottom", ha="right")

    # Exit marker
    if exit_bar is not None:
        exit_price = prices[exit_bar] if exit_bar < n_bars else prices[-1]
        marker_color = CLR_TP if exit_type in ("TP", "convergence") else CLR_SL
        ax_price.plot(exit_bar, exit_price, "X", color=marker_color,
                      markersize=14, zorder=10)
        ax_price.text(exit_bar, exit_price, f" {exit_type}",
                      fontsize=8, color=marker_color, va="center", fontweight="bold")

    # Description box
    ax_price.text(
        0.02, 0.96, description, transform=ax_price.transAxes,
        fontsize=8, color=CLR_PHASE_TEXT, va="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=DARK_BG, edgecolor="#333333", alpha=0.9),
    )

    ax_price.set_ylabel("Price", fontsize=9)
    ax_price.legend(loc="upper right", fontsize=7, framealpha=0.3,
                    facecolor=DARK_CARD, edgecolor="#333333", labelcolor=CLR_PRICE)
    ax_price.set_xlim(-1, n_bars + 1)
    ax_price.tick_params(labelbottom=False)

    # --- Stoch subplot ---
    ax_stoch.plot(bars, stoch_d, color=CLR_STOCH, linewidth=1.2, label="Stoch 9,3 D")

    if is_long:
        ax_stoch.axhspan(0, 20, alpha=0.1, color=CLR_SL)
        ax_stoch.axhline(20, color=CLR_SL, linestyle="--", linewidth=0.7, alpha=0.5)
        ax_stoch.text(n_bars - 1, 20, "Oversold 20", fontsize=7, color=CLR_SL,
                      va="bottom", ha="right")
    else:
        ax_stoch.axhspan(80, 100, alpha=0.1, color=CLR_SL)
        ax_stoch.axhline(80, color=CLR_SL, linestyle="--", linewidth=0.7, alpha=0.5)
        ax_stoch.text(n_bars - 1, 80, "Overbought 80", fontsize=7, color=CLR_SL,
                      va="bottom", ha="right")

    # Mark overzone exits on stoch
    for rb in ratchet_bars:
        ax_stoch.axvline(rb, color=CLR_AVWAP_2S, linestyle=":", linewidth=0.8, alpha=0.5)

    ax_stoch.set_ylabel("Stoch 9,3 D", fontsize=9)
    ax_stoch.set_xlabel("Bars", fontsize=9)
    ax_stoch.set_ylim(-5, 105)
    ax_stoch.set_xlim(-1, n_bars + 1)
    ax_stoch.legend(loc="upper right", fontsize=7, framealpha=0.3,
                    facecolor=DARK_CARD, edgecolor="#333333", labelcolor=CLR_PRICE)

    return fig


def scenario_1():
    """Stopped out Phase 1 — SL hit before bar 5."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry - 2.5 * atr
    n = 15

    prices = generate_price_path(n, entry, seed=10, trend="down")
    prices[3] = initial_sl - 0.2  # force SL hit at bar 3

    stoch = generate_stoch_d(n, seed=10)

    sl_levels = [(0, initial_sl), (3, initial_sl)]

    return plot_scenario(
        1, "Stopped Out Phase 1 (before AVWAP warmup)",
        "Price drops immediately.\nSL hit at entry - 2.5 ATR before bar 5.\nNo AVWAP, no BE, no ratchets.",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=None,
        avwap_anchor_bar=None, avwap_anchor_level=None,
        ratchet_bars=[], ratchet_levels=[],
        tp_level=None, tp_bar=None,
        exit_bar=3, exit_type="SL hit",
        cloud4_level=None, is_long=True,
    )


def scenario_2():
    """Stopped out Phase 2 — SL hit at frozen AVWAP -2s."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry - 2.5 * atr
    avwap_anchor = entry - 0.8  # -2 sigma frozen at bar 5
    be_level = entry + 0.05
    n = 25

    # price goes up, triggers BE, then at bar 5 AVWAP kicks in, then drops
    rng = np.random.default_rng(20)
    prices = np.zeros(n)
    prices[0] = entry
    for i in range(1, 5):
        prices[i] = prices[i - 1] + rng.uniform(0.1, 0.3)
    for i in range(5, n):
        prices[i] = prices[i - 1] - rng.uniform(0.05, 0.2)
    prices[15] = avwap_anchor - 0.1  # SL hit

    stoch = generate_stoch_d(n, seed=20)

    sl_levels = [
        (0, initial_sl),
        (2, be_level),  # BE fires bar 2
        (5, avwap_anchor),  # AVWAP anchor at bar 5
        (15, avwap_anchor),
    ]

    return plot_scenario(
        2, "Stopped Out Phase 2 (AVWAP -2s frozen floor)",
        "Price rises, BE fires at bar 2.\nAVWAP -2s frozen at bar 5.\nPrice reverses, hits AVWAP floor at bar 15.",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=be_level,
        avwap_anchor_bar=5, avwap_anchor_level=avwap_anchor,
        ratchet_bars=[], ratchet_levels=[],
        tp_level=None, tp_bar=None,
        exit_bar=15, exit_type="SL hit",
        cloud4_level=None, is_long=True,
    )


def scenario_3():
    """BE exit — price goes positive then pulls back to entry."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry - 2.5 * atr
    be_level = entry + 0.05
    n = 20

    rng = np.random.default_rng(30)
    prices = np.zeros(n)
    prices[0] = entry
    for i in range(1, 4):
        prices[i] = prices[i - 1] + rng.uniform(0.1, 0.2)
    for i in range(4, n):
        prices[i] = prices[i - 1] - rng.uniform(0.02, 0.15)
    prices[10] = be_level - 0.02  # hit BE

    stoch = generate_stoch_d(n, seed=30)

    sl_levels = [
        (0, initial_sl),
        (2, be_level),  # BE fires
        (10, be_level),
    ]

    return plot_scenario(
        3, "BE Exit (breakeven stop hit)",
        "Price goes positive, BE fires at bar 2.\nSlow pullback hits BE level at bar 10.\nMinimal loss (just fees).",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=be_level,
        avwap_anchor_bar=None, avwap_anchor_level=None,
        ratchet_bars=[], ratchet_levels=[],
        tp_level=None, tp_bar=None,
        exit_bar=10, exit_type="BE hit",
        cloud4_level=None, is_long=True,
    )


def scenario_4():
    """One ratchet then stopped — single overzone exit, then SL hit."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry - 2.5 * atr
    be_level = entry + 0.05
    avwap_anchor = entry - 0.8
    ratchet_1_level = entry + 0.5  # AVWAP -2s after first pullback
    n = 45

    rng = np.random.default_rng(40)
    prices = np.zeros(n)
    prices[0] = entry
    # up trend
    for i in range(1, 12):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.2)
    # pullback (stoch oversold)
    for i in range(12, 20):
        prices[i] = prices[i - 1] - rng.uniform(0.02, 0.12)
    # bounce (overzone exit at ~bar 22)
    for i in range(20, 28):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.15)
    # second drop — hits ratchet SL
    for i in range(28, n):
        prices[i] = prices[i - 1] - rng.uniform(0.05, 0.15)
    prices[38] = ratchet_1_level - 0.1

    stoch = generate_stoch_d(
        n, seed=40,
        overzone_windows=[(10, 22, 8)],  # oversold dip and exit
        is_long=True,
    )

    sl_levels = [
        (0, initial_sl),
        (2, be_level),
        (5, avwap_anchor),
        (22, ratchet_1_level),  # ratchet #1 at overzone exit
        (38, ratchet_1_level),
    ]

    return plot_scenario(
        4, "One Ratchet Then Stopped",
        "Trend up, pullback (stoch <20), exit overzone at bar 22.\nSL ratchets to live AVWAP -2s (R1).\nSecond reversal hits R1 at bar 38.",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=be_level,
        avwap_anchor_bar=5, avwap_anchor_level=avwap_anchor,
        ratchet_bars=[22], ratchet_levels=[ratchet_1_level],
        tp_level=None, tp_bar=None,
        exit_bar=38, exit_type="SL hit (R1)",
        cloud4_level=None, is_long=True,
    )


def scenario_5():
    """Two ratchets, TP hit — Cloud4 + ATR."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry - 2.5 * atr
    be_level = entry + 0.05
    avwap_anchor = entry - 0.8
    ratchet_1 = entry + 0.5
    ratchet_2 = entry + 1.8
    cloud4 = entry + 3.5
    tp = cloud4 + atr
    n = 65

    rng = np.random.default_rng(50)
    prices = np.zeros(n)
    prices[0] = entry
    # leg 1 up
    for i in range(1, 15):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.2)
    # pullback 1
    for i in range(15, 22):
        prices[i] = prices[i - 1] - rng.uniform(0.02, 0.12)
    # leg 2 up
    for i in range(22, 38):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.18)
    # pullback 2
    for i in range(38, 44):
        prices[i] = prices[i - 1] - rng.uniform(0.02, 0.10)
    # leg 3 to TP
    for i in range(44, n):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.15)
    prices[min(58, n - 1)] = tp + 0.1  # TP hit

    stoch = generate_stoch_d(
        n, seed=50,
        overzone_windows=[(13, 24, 8), (36, 46, 8)],
        is_long=True,
    )

    sl_levels = [
        (0, initial_sl),
        (2, be_level),
        (5, avwap_anchor),
        (24, ratchet_1),
        (46, ratchet_2),
        (58, ratchet_2),
    ]

    return plot_scenario(
        5, "Two Ratchets, TP Hit (Cloud 4 + ATR)",
        "Two pullback-and-continue cycles.\nR2 activates TP = Cloud4 upper + ATR.\nPrice reaches TP at bar 58. Clean winner.",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=be_level,
        avwap_anchor_bar=5, avwap_anchor_level=avwap_anchor,
        ratchet_bars=[24, 46], ratchet_levels=[ratchet_1, ratchet_2],
        tp_level=tp, tp_bar=58,
        exit_bar=58, exit_type="TP",
        cloud4_level=cloud4, is_long=True,
    )


def scenario_6():
    """Three+ ratchets, extended trend (rare ~3%)."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry - 2.5 * atr
    be_level = entry + 0.05
    avwap_anchor = entry - 0.8
    ratchet_1 = entry + 0.5
    ratchet_2 = entry + 1.8
    ratchet_3 = entry + 3.2
    cloud4 = entry + 3.5
    tp = cloud4 + atr
    n = 85

    rng = np.random.default_rng(60)
    prices = np.zeros(n)
    prices[0] = entry
    # leg 1
    for i in range(1, 15):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.18)
    # pullback 1
    for i in range(15, 22):
        prices[i] = prices[i - 1] - rng.uniform(0.02, 0.10)
    # leg 2
    for i in range(22, 38):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.16)
    # pullback 2
    for i in range(38, 44):
        prices[i] = prices[i - 1] - rng.uniform(0.02, 0.08)
    # leg 3
    for i in range(44, 60):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.15)
    # pullback 3
    for i in range(60, 66):
        prices[i] = prices[i - 1] - rng.uniform(0.02, 0.08)
    # final push to TP
    for i in range(66, n):
        prices[i] = prices[i - 1] + rng.uniform(0.05, 0.12)
    prices[min(80, n - 1)] = tp + 0.3

    stoch = generate_stoch_d(
        n, seed=60,
        overzone_windows=[(13, 24, 8), (36, 46, 8), (58, 68, 8)],
        is_long=True,
    )

    sl_levels = [
        (0, initial_sl),
        (2, be_level),
        (5, avwap_anchor),
        (24, ratchet_1),
        (46, ratchet_2),
        (68, ratchet_3),
        (80, ratchet_3),
    ]

    return plot_scenario(
        6, "Three Ratchets, Extended Trend (~3% of trades)",
        "Three pullback-and-continue cycles.\nTP activated at R2, SL keeps ratcheting.\nR3 tightens floor. TP hit at bar 80.",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=be_level,
        avwap_anchor_bar=5, avwap_anchor_level=avwap_anchor,
        ratchet_bars=[24, 46, 68],
        ratchet_levels=[ratchet_1, ratchet_2, ratchet_3],
        tp_level=tp, tp_bar=80,
        exit_bar=80, exit_type="TP",
        cloud4_level=cloud4, is_long=True,
    )


def scenario_7():
    """Convergence exit — SL ratchets above TP."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry - 2.5 * atr
    be_level = entry + 0.05
    avwap_anchor = entry - 0.8
    ratchet_1 = entry + 0.5
    ratchet_2 = entry + 1.8
    ratchet_3 = entry + 3.8  # above cloud4 + atr
    cloud4 = entry + 3.0
    tp = cloud4 + atr  # = entry + 4.0
    n = 75

    rng = np.random.default_rng(70)
    prices = np.zeros(n)
    prices[0] = entry
    # strong legs up with shallow pullbacks
    for i in range(1, 15):
        prices[i] = prices[i - 1] + rng.uniform(0.08, 0.22)
    for i in range(15, 20):
        prices[i] = prices[i - 1] - rng.uniform(0.01, 0.06)
    for i in range(20, 38):
        prices[i] = prices[i - 1] + rng.uniform(0.08, 0.20)
    for i in range(38, 43):
        prices[i] = prices[i - 1] - rng.uniform(0.01, 0.05)
    for i in range(43, 58):
        prices[i] = prices[i - 1] + rng.uniform(0.08, 0.18)
    for i in range(58, 63):
        prices[i] = prices[i - 1] - rng.uniform(0.01, 0.05)
    # plateau around TP
    for i in range(63, n):
        prices[i] = prices[i - 1] + rng.uniform(-0.05, 0.05)

    stoch = generate_stoch_d(
        n, seed=70,
        overzone_windows=[(13, 22, 8), (36, 45, 8), (56, 65, 8)],
        is_long=True,
    )

    sl_levels = [
        (0, initial_sl),
        (2, be_level),
        (5, avwap_anchor),
        (22, ratchet_1),
        (45, ratchet_2),
        (65, ratchet_3),  # above TP
        (68, ratchet_3),
    ]

    return plot_scenario(
        7, "Convergence Exit (SL ratchets above TP)",
        "SL keeps tightening. After R3, SL > TP.\nClose at market immediately.\nRare edge case — strong trend with shallow pullbacks\npushing AVWAP center very high.",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=be_level,
        avwap_anchor_bar=5, avwap_anchor_level=avwap_anchor,
        ratchet_bars=[22, 45, 65],
        ratchet_levels=[ratchet_1, ratchet_2, ratchet_3],
        tp_level=tp, tp_bar=None,
        exit_bar=65, exit_type="convergence",
        cloud4_level=cloud4, is_long=True,
    )


def scenario_8():
    """Short mirror of scenario 5 — two ratchets, TP hit."""
    entry = 100.0
    atr = 1.0
    initial_sl = entry + 2.5 * atr
    be_level = entry - 0.05
    avwap_anchor = entry + 0.8
    ratchet_1 = entry - 0.5
    ratchet_2 = entry - 1.8
    cloud4 = entry - 3.5
    tp = cloud4 - atr
    n = 65

    rng = np.random.default_rng(80)
    prices = np.zeros(n)
    prices[0] = entry
    # down trend with bounces
    for i in range(1, 15):
        prices[i] = prices[i - 1] - rng.uniform(0.05, 0.2)
    for i in range(15, 22):
        prices[i] = prices[i - 1] + rng.uniform(0.02, 0.12)
    for i in range(22, 38):
        prices[i] = prices[i - 1] - rng.uniform(0.05, 0.18)
    for i in range(38, 44):
        prices[i] = prices[i - 1] + rng.uniform(0.02, 0.10)
    for i in range(44, n):
        prices[i] = prices[i - 1] - rng.uniform(0.05, 0.15)
    prices[min(58, n - 1)] = tp - 0.1

    stoch = generate_stoch_d(
        n, seed=80,
        overzone_windows=[(13, 24, 92), (36, 46, 92)],
        is_long=False,
    )

    sl_levels = [
        (0, initial_sl),
        (2, be_level),
        (5, avwap_anchor),
        (24, ratchet_1),
        (46, ratchet_2),
        (58, ratchet_2),
    ]

    return plot_scenario(
        8, "SHORT Mirror — Two Ratchets, TP Hit",
        "Short entry. Stoch 9 D > 80 (overbought) = pullback.\nExit overbought = continuation down.\nTP = Cloud4 lower - ATR.",
        prices, stoch,
        entry_bar=0, entry_price=entry, atr=atr,
        sl_levels=sl_levels, be_level=be_level,
        avwap_anchor_bar=5, avwap_anchor_level=avwap_anchor,
        ratchet_bars=[24, 46], ratchet_levels=[ratchet_1, ratchet_2],
        tp_level=tp, tp_bar=58,
        exit_bar=58, exit_type="TP",
        cloud4_level=cloud4, is_long=False,
    )


def main():
    """Generate all 8 scenario visualizations."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Output dir: %s", OUTPUT_DIR)

    scenarios = [
        scenario_1, scenario_2, scenario_3, scenario_4,
        scenario_5, scenario_6, scenario_7, scenario_8,
    ]

    for i, scenario_fn in enumerate(scenarios, 1):
        log.info("Generating scenario %d/8...", i)
        fig = scenario_fn()
        out_path = OUTPUT_DIR / f"scenario_{i:02d}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        plt.close(fig)
        log.info("  Saved: %s", out_path)

    log.info("Done. All 8 scenarios saved to %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()

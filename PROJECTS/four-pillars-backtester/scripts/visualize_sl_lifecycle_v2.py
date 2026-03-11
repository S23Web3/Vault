"""
SL/TP Lifecycle Visualization v2 — 55/89 EMA Cross Scalp.

Generates 12 sequential matplotlib figures (7 long + 5 short) showing
every possible trade outcome. Each plot has two subplots:
  - Top: price action with SL/TP levels, sloped Cloud 4, phase labels
  - Bottom: stoch 9,3 D with overzone thresholds

Price data is shaped via waypoint interpolation (cubic) with light noise,
producing realistic 1m candle-like movement.

Run: python scripts/visualize_sl_lifecycle_v2.py
Output: results/sl_lifecycle/ (PNG per scenario)
"""

import logging
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "results" / "sl_lifecycle"

# --- Dark theme colors ---
DARK_BG = "#0f1419"
DARK_CARD = "#1a1f26"
CLR_PRICE = "#e7e9ea"
CLR_SL = "#ef4444"
CLR_BE = "#f59e0b"
CLR_AVWAP_2S = "#8b5cf6"
CLR_TP = "#10b981"
CLR_ENTRY = "#6b7280"
CLR_STOCH = "#f97316"
CLR_PHASE_TEXT = "#9ca3af"
CLR_CLOUD4 = "#22d3ee"


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


def shaped_price(waypoints, n_bars, noise_pct=0.0015, seed=42):
    """Build a smooth price curve from waypoints with light noise.

    waypoints: list of (bar_index, price_value) tuples.
    Interpolates linearly between waypoints, then adds gaussian noise.
    """
    rng = np.random.default_rng(seed)
    wp_bars = np.array([w[0] for w in waypoints], dtype=float)
    wp_prices = np.array([w[1] for w in waypoints], dtype=float)
    bars = np.arange(n_bars, dtype=float)
    prices = np.interp(bars, wp_bars, wp_prices)
    base_price = wp_prices[0]
    noise = rng.normal(0, base_price * noise_pct, n_bars)
    # smooth the noise a bit
    kernel = np.ones(3) / 3
    noise = np.convolve(noise, kernel, mode="same")
    prices = prices + noise
    return prices


def shaped_stoch(waypoints, n_bars, noise_amp=3.0, seed=42):
    """Build a smooth stoch D curve from waypoints with noise."""
    rng = np.random.default_rng(seed)
    wp_bars = np.array([w[0] for w in waypoints], dtype=float)
    wp_vals = np.array([w[1] for w in waypoints], dtype=float)
    bars = np.arange(n_bars, dtype=float)
    stoch = np.interp(bars, wp_bars, wp_vals)
    noise = rng.normal(0, noise_amp, n_bars)
    kernel = np.ones(3) / 3
    noise = np.convolve(noise, kernel, mode="same")
    stoch = stoch + noise
    return np.clip(stoch, 0, 100)


def sloped_line(start_bar, start_val, end_bar, end_val, n_bars):
    """Generate a sloped line array across n_bars (NaN outside range)."""
    line = np.full(n_bars, np.nan)
    for i in range(max(0, start_bar), min(n_bars, end_bar + 1)):
        t = (i - start_bar) / max(end_bar - start_bar, 1)
        line[i] = start_val + t * (end_val - start_val)
    return line


def plot_scenario(num, title, desc, prices, stoch_d, entry_bar, entry_price,
                  sl_steps, be_level, avwap_bar, avwap_level,
                  ratchet_bars, ratchet_levels,
                  cloud4_line, tp_line, exit_bar, exit_type, is_long=True):
    """Plot one scenario: price subplot + stoch subplot."""
    n = len(prices)
    bars = np.arange(n)

    fig, (ax_p, ax_s) = plt.subplots(
        2, 1, figsize=(15, 8.5), height_ratios=[3, 1],
        gridspec_kw={"hspace": 0.07},
    )
    apply_dark_theme(fig, [ax_p, ax_s])

    side_label = "LONG" if is_long else "SHORT"
    fig.suptitle(
        f"Scenario {num} ({side_label}): {title}",
        color=CLR_PRICE, fontsize=13, fontweight="bold", y=0.97,
    )

    # --- Price ---
    ax_p.plot(bars, prices, color=CLR_PRICE, linewidth=1.1, label="Price", zorder=5)

    # entry
    marker = "^" if is_long else "v"
    m_color = CLR_TP if is_long else CLR_SL
    ax_p.plot(entry_bar, entry_price, marker, color=m_color, markersize=12, zorder=10)
    ax_p.axhline(entry_price, color=CLR_ENTRY, ls="--", lw=0.6, alpha=0.4)
    ax_p.text(1, entry_price, " ENTRY", fontsize=7, color=CLR_ENTRY, va="bottom")

    # SL stepped line
    sl_x = [s[0] for s in sl_steps]
    sl_y = [s[1] for s in sl_steps]
    ax_p.step(sl_x, sl_y, where="post", color=CLR_SL, lw=1.5, label="Stop Loss", zorder=6)

    # BE
    if be_level is not None:
        ax_p.axhline(be_level, color=CLR_BE, ls=":", lw=0.8, alpha=0.5)
        ax_p.text(1, be_level, " BE", fontsize=7, color=CLR_BE, va="bottom")

    # AVWAP anchor
    if avwap_bar is not None and avwap_level is not None:
        ax_p.plot(avwap_bar, avwap_level, "D", color=CLR_AVWAP_2S, ms=8, zorder=8)
        ax_p.axhline(avwap_level, color=CLR_AVWAP_2S, ls="--", lw=0.6, alpha=0.35,
                      xmin=avwap_bar / n, xmax=1.0)
        va = "top" if is_long else "bottom"
        ax_p.text(avwap_bar + 0.5, avwap_level, "AVWAP -2s frozen",
                  fontsize=7, color=CLR_AVWAP_2S, va=va)

    # ratchets
    for i, (rb, rl) in enumerate(zip(ratchet_bars, ratchet_levels)):
        ax_p.plot(rb, rl, "D", color=CLR_AVWAP_2S, ms=7, zorder=8)
        va = "bottom" if is_long else "top"
        ax_p.text(rb + 0.3, rl, f"R{i + 1}", fontsize=7, color=CLR_AVWAP_2S,
                  va=va, fontweight="bold")

    # Cloud 4 (sloped)
    if cloud4_line is not None:
        ax_p.plot(bars, cloud4_line, color=CLR_CLOUD4, lw=1.4, alpha=0.5, label="Cloud 4 (EMA 72/89)")

    # TP (sloped)
    if tp_line is not None:
        ax_p.plot(bars, tp_line, color=CLR_TP, lw=1.2, ls="--", alpha=0.6, label="TP (C4 + ATR)")

    # exit marker
    if exit_bar is not None and exit_bar < n:
        ex_price = prices[exit_bar]
        ex_color = CLR_TP if "TP" in exit_type else CLR_SL
        ax_p.plot(exit_bar, ex_price, "X", color=ex_color, ms=14, zorder=10)
        ax_p.text(exit_bar + 0.5, ex_price, f" {exit_type}", fontsize=8,
                  color=ex_color, va="center", fontweight="bold")

    # description box
    ax_p.text(0.02, 0.96, desc, transform=ax_p.transAxes, fontsize=8,
              color=CLR_PHASE_TEXT, va="top",
              bbox=dict(boxstyle="round,pad=0.4", facecolor=DARK_BG,
                        edgecolor="#333333", alpha=0.9))

    ax_p.set_ylabel("Price", fontsize=9)
    ax_p.legend(loc="upper right", fontsize=7, framealpha=0.3,
                facecolor=DARK_CARD, edgecolor="#333333", labelcolor=CLR_PRICE)
    ax_p.set_xlim(-1, n + 1)
    ax_p.tick_params(labelbottom=False)

    # --- Stoch ---
    ax_s.plot(bars, stoch_d, color=CLR_STOCH, lw=1.2, label="Stoch 9,3 D")
    if is_long:
        ax_s.axhspan(0, 20, alpha=0.1, color=CLR_SL)
        ax_s.axhline(20, color=CLR_SL, ls="--", lw=0.6, alpha=0.4)
        ax_s.text(n - 1, 20, "Oversold 20", fontsize=7, color=CLR_SL, va="bottom", ha="right")
    else:
        ax_s.axhspan(80, 100, alpha=0.1, color=CLR_SL)
        ax_s.axhline(80, color=CLR_SL, ls="--", lw=0.6, alpha=0.4)
        ax_s.text(n - 1, 80, "Overbought 80", fontsize=7, color=CLR_SL, va="bottom", ha="right")

    for rb in ratchet_bars:
        ax_s.axvline(rb, color=CLR_AVWAP_2S, ls=":", lw=0.8, alpha=0.4)

    ax_s.set_ylabel("Stoch 9,3 D", fontsize=9)
    ax_s.set_xlabel("Bars (1m)", fontsize=9)
    ax_s.set_ylim(-5, 105)
    ax_s.set_xlim(-1, n + 1)
    ax_s.legend(loc="upper right", fontsize=7, framealpha=0.3,
                facecolor=DARK_CARD, edgecolor="#333333", labelcolor=CLR_PRICE)

    return fig


# ========================================================================
# LONG SCENARIOS 1-7
# ========================================================================

def scenario_L1():
    """LONG: Stopped out Phase 1 — SL hit before bar 5."""
    e = 100.0
    atr = 1.0
    sl = e - 2.5 * atr  # 97.5
    n = 18

    prices = shaped_price([
        (0, e), (2, 99.7), (4, 98.5), (6, 97.3), (8, 97.0),
        (10, 97.2), (12, 96.8), (14, 96.5), (17, 96.0),
    ], n, seed=101)

    stoch = shaped_stoch([
        (0, 55), (3, 40), (6, 25), (9, 18), (12, 12), (15, 8), (17, 5),
    ], n, seed=101)

    return plot_scenario(
        1, "Stopped Out Phase 1 (before AVWAP warmup)",
        "Price drops immediately after entry.\nSL hit at entry - 2.5 ATR before bar 5.\nNo BE triggered, no AVWAP, no ratchets.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (6, sl)],
        be_level=None, avwap_bar=None, avwap_level=None,
        ratchet_bars=[], ratchet_levels=[],
        cloud4_line=None, tp_line=None,
        exit_bar=6, exit_type="SL hit", is_long=True,
    )


def scenario_L2():
    """LONG: BE exit — price goes positive, pulls back to breakeven."""
    e = 100.0
    atr = 1.0
    sl = e - 2.5 * atr
    be = e + 0.05
    n = 22

    prices = shaped_price([
        (0, e), (2, 100.3), (4, 100.8), (6, 101.0),
        (8, 100.6), (10, 100.3), (12, 100.1), (14, 100.0),
        (16, 99.8), (18, 99.5), (21, 99.0),
    ], n, seed=102)

    stoch = shaped_stoch([
        (0, 55), (3, 65), (6, 70), (9, 55), (12, 40), (15, 30), (18, 22), (21, 15),
    ], n, seed=102)

    return plot_scenario(
        2, "BE Exit (breakeven stop hit)",
        "Price rises, BE arms at bar 3.\nSlow pullback hits BE level at bar 14.\nMinimal loss (fees only).",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (14, be)],
        be_level=be, avwap_bar=None, avwap_level=None,
        ratchet_bars=[], ratchet_levels=[],
        cloud4_line=None, tp_line=None,
        exit_bar=14, exit_type="BE hit", is_long=True,
    )


def scenario_L3():
    """LONG: Stopped out Phase 2 — AVWAP -2s frozen floor hit."""
    e = 100.0
    atr = 1.0
    sl = e - 2.5 * atr
    be = e + 0.05
    avwap_lvl = e - 0.8  # 99.2
    n = 28

    prices = shaped_price([
        (0, e), (2, 100.4), (4, 100.9), (5, 101.0),
        (7, 100.8), (9, 100.5), (11, 100.2), (13, 100.0),
        (15, 99.7), (17, 99.5), (19, 99.3), (21, 99.1),
        (23, 99.0), (27, 98.5),
    ], n, seed=103)

    stoch = shaped_stoch([
        (0, 55), (3, 68), (5, 72), (8, 55), (11, 40),
        (14, 30), (17, 22), (20, 15), (23, 10), (27, 5),
    ], n, seed=103)

    return plot_scenario(
        3, "Stopped Out Phase 2 (AVWAP -2s floor hit)",
        "Price rises, BE fires at bar 3.\nAVWAP -2s frozen at bar 5.\nSlow reversal hits AVWAP floor at bar 21.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (21, avwap_lvl)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[], ratchet_levels=[],
        cloud4_line=None, tp_line=None,
        exit_bar=21, exit_type="SL hit", is_long=True,
    )


def scenario_L4():
    """LONG: One ratchet then stopped."""
    e = 100.0
    atr = 1.0
    sl = e - 2.5 * atr
    be = e + 0.05
    avwap_lvl = e - 0.8
    r1 = e + 0.6  # 100.6 — AVWAP -2s after pullback recovery
    n = 48

    # up leg -> pullback (stoch oversold) -> bounce -> R1 -> second drop -> SL
    prices = shaped_price([
        (0, e), (3, 100.5), (6, 101.2), (9, 101.8), (11, 102.0),
        (14, 101.3), (17, 100.8), (19, 100.5),  # pullback
        (22, 101.0), (24, 101.5),  # bounce (R1 fires ~bar 23)
        (27, 101.2), (30, 100.8), (33, 100.4), (36, 100.0),
        (39, 100.5), (42, 100.2), (45, 99.8), (47, 99.5),
    ], n, seed=104)

    stoch = shaped_stoch([
        (0, 55), (4, 68), (8, 75), (11, 72),
        (14, 35), (17, 15), (19, 10),  # oversold
        (22, 25), (24, 45),  # exit overzone ~bar 22
        (27, 55), (30, 45), (33, 35), (36, 25), (39, 18), (42, 12), (47, 8),
    ], n, seed=104)

    return plot_scenario(
        4, "One Ratchet Then Stopped",
        "Trend up, pullback (stoch 9 D < 20).\nOverzone exit at bar 22 -> R1.\nSecond reversal hits R1 at bar 42.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (22, r1), (42, r1)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[22], ratchet_levels=[r1],
        cloud4_line=None, tp_line=None,
        exit_bar=42, exit_type="SL hit (R1)", is_long=True,
    )


def scenario_L5():
    """LONG: Two ratchets, TP hit — Cloud4 + ATR (clean winner)."""
    e = 100.0
    atr = 1.0
    sl = e - 2.5 * atr
    be = e + 0.05
    avwap_lvl = e - 0.8
    r1 = e + 0.6
    r2 = e + 2.0
    n = 68

    prices = shaped_price([
        (0, e), (4, 100.8), (8, 101.5), (12, 102.2), (14, 102.5),
        (17, 101.8), (20, 101.2), (22, 101.5),  # pullback 1
        (26, 102.2), (30, 103.0), (34, 103.5), (36, 103.8),
        (39, 103.0), (42, 102.5), (44, 102.8),  # pullback 2
        (48, 103.5), (52, 104.2), (56, 104.8),
        (60, 105.2), (64, 105.6), (67, 105.8),
    ], n, seed=105)

    stoch = shaped_stoch([
        (0, 55), (5, 70), (10, 78), (14, 72),
        (17, 30), (20, 12), (22, 25),  # oversold exit -> R1
        (26, 55), (30, 72), (34, 78), (36, 70),
        (39, 28), (42, 10), (44, 28),  # oversold exit -> R2
        (48, 55), (52, 68), (56, 75), (60, 72), (64, 65), (67, 60),
    ], n, seed=105)

    # Cloud 4 slopes up (EMA 72/89 lags price)
    c4 = sloped_line(0, e - 1.5, n - 1, e + 4.5, n)
    tp = sloped_line(0, e - 1.5 + atr, n - 1, e + 4.5 + atr, n)

    return plot_scenario(
        5, "Two Ratchets, TP Hit (Cloud 4 + ATR)",
        "Two pullback-and-continue cycles.\nR2 activates TP = Cloud4 upper + ATR.\nPrice crosses TP at bar 60. Clean winner.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (22, r1), (44, r2), (60, r2)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[22, 44], ratchet_levels=[r1, r2],
        cloud4_line=c4, tp_line=tp,
        exit_bar=60, exit_type="TP hit", is_long=True,
    )


def scenario_L6():
    """LONG: Three ratchets, extended trend (~3% of trades)."""
    e = 100.0
    atr = 1.0
    sl = e - 2.5 * atr
    be = e + 0.05
    avwap_lvl = e - 0.8
    r1 = e + 0.6
    r2 = e + 2.0
    r3 = e + 3.5
    n = 90

    prices = shaped_price([
        (0, e), (5, 101.0), (10, 101.8), (14, 102.3),
        (17, 101.5), (20, 101.0), (22, 101.4),  # PB1
        (28, 102.5), (34, 103.5), (38, 104.0),
        (41, 103.2), (44, 102.8), (46, 103.2),  # PB2
        (52, 104.5), (58, 105.5), (62, 106.0),
        (65, 105.2), (68, 104.8), (70, 105.3),  # PB3
        (76, 106.5), (82, 107.2), (86, 107.8), (89, 108.0),
    ], n, seed=106)

    stoch = shaped_stoch([
        (0, 55), (7, 72), (14, 70),
        (17, 25), (20, 10), (22, 30),  # R1
        (30, 70), (38, 72),
        (41, 22), (44, 8), (46, 30),  # R2
        (54, 72), (62, 68),
        (65, 20), (68, 8), (70, 32),  # R3
        (78, 65), (84, 60), (89, 55),
    ], n, seed=106)

    c4 = sloped_line(0, e - 2.0, n - 1, e + 6.5, n)
    tp = sloped_line(0, e - 2.0 + atr, n - 1, e + 6.5 + atr, n)

    return plot_scenario(
        6, "Three Ratchets, Extended Trend (~3%)",
        "Three pullback-and-continue cycles.\nTP active after R2, SL keeps ratcheting.\nR3 tightens floor further. TP hit at bar 82.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (22, r1), (46, r2), (70, r3), (82, r3)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[22, 46, 70], ratchet_levels=[r1, r2, r3],
        cloud4_line=c4, tp_line=tp,
        exit_bar=82, exit_type="TP hit", is_long=True,
    )


def scenario_L7():
    """LONG: Two ratchets, TP active but reversal hits R2 SL."""
    e = 100.0
    atr = 1.0
    sl = e - 2.5 * atr
    be = e + 0.05
    avwap_lvl = e - 0.8
    r1 = e + 0.6
    r2 = e + 2.0
    n = 65

    prices = shaped_price([
        (0, e), (4, 100.8), (8, 101.5), (12, 102.2), (14, 102.5),
        (17, 101.8), (20, 101.2), (22, 101.5),  # PB1
        (26, 102.2), (30, 103.0), (34, 103.5), (36, 103.8),
        (39, 103.0), (42, 102.5), (44, 102.8),  # PB2
        (48, 103.2), (50, 103.5), (52, 103.2),  # stalls
        (55, 102.5), (58, 101.8), (60, 101.5), (62, 101.2), (64, 100.8),
    ], n, seed=107)

    stoch = shaped_stoch([
        (0, 55), (5, 70), (10, 78), (14, 72),
        (17, 30), (20, 12), (22, 25),  # R1
        (26, 55), (30, 72), (36, 70),
        (39, 28), (42, 10), (44, 28),  # R2
        (48, 50), (50, 45), (52, 38),
        (55, 25), (58, 15), (60, 10), (62, 8), (64, 5),
    ], n, seed=107)

    c4 = sloped_line(0, e - 1.5, n - 1, e + 3.0, n)
    tp = sloped_line(0, e - 1.5 + atr, n - 1, e + 3.0 + atr, n)

    return plot_scenario(
        7, "Two Ratchets, TP Active But Reversal Hits R2",
        "Two ratchets, TP activates after R2.\nPrice stalls, never reaches Cloud 4 + ATR.\nHard reversal hits R2 SL at bar 58.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (22, r1), (44, r2), (58, r2)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[22, 44], ratchet_levels=[r1, r2],
        cloud4_line=c4, tp_line=tp,
        exit_bar=58, exit_type="SL hit (R2)", is_long=True,
    )


# ========================================================================
# SHORT SCENARIOS 8-12
# ========================================================================

def scenario_S1():
    """SHORT: Stopped out Phase 1 — SL hit before bar 5."""
    e = 100.0
    atr = 1.0
    sl = e + 2.5 * atr  # 102.5
    n = 18

    prices = shaped_price([
        (0, e), (2, 100.3), (4, 101.0), (6, 101.8), (8, 102.3),
        (10, 102.5), (12, 102.8), (14, 103.0), (17, 103.5),
    ], n, seed=201)

    stoch = shaped_stoch([
        (0, 45), (3, 55), (6, 68), (9, 78), (12, 85), (15, 90), (17, 95),
    ], n, seed=201)

    return plot_scenario(
        8, "Stopped Out Phase 1 (before AVWAP warmup)",
        "Short entry. Price rises immediately.\nSL hit at entry + 2.5 ATR before bar 5.\nNo BE triggered, no AVWAP, no ratchets.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (6, sl)],
        be_level=None, avwap_bar=None, avwap_level=None,
        ratchet_bars=[], ratchet_levels=[],
        cloud4_line=None, tp_line=None,
        exit_bar=6, exit_type="SL hit", is_long=False,
    )


def scenario_S2():
    """SHORT: BE exit — price goes negative then bounces back."""
    e = 100.0
    atr = 1.0
    sl = e + 2.5 * atr
    be = e - 0.05
    n = 22

    prices = shaped_price([
        (0, e), (2, 99.7), (4, 99.2), (6, 99.0),
        (8, 99.4), (10, 99.7), (12, 99.9), (14, 100.1),
        (16, 100.3), (18, 100.5), (21, 101.0),
    ], n, seed=202)

    stoch = shaped_stoch([
        (0, 45), (3, 35), (6, 28), (9, 40), (12, 55), (15, 68), (18, 78), (21, 85),
    ], n, seed=202)

    return plot_scenario(
        9, "BE Exit (breakeven stop hit)",
        "Short entry. Price drops, BE arms at bar 3.\nBounce pulls back to BE level at bar 14.\nMinimal loss (fees only).",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (14, be)],
        be_level=be, avwap_bar=None, avwap_level=None,
        ratchet_bars=[], ratchet_levels=[],
        cloud4_line=None, tp_line=None,
        exit_bar=14, exit_type="BE hit", is_long=False,
    )


def scenario_S3():
    """SHORT: One ratchet then stopped."""
    e = 100.0
    atr = 1.0
    sl = e + 2.5 * atr
    be = e - 0.05
    avwap_lvl = e + 0.8  # 100.8 (above entry for short)
    r1 = e - 0.6  # 99.4 (below entry — tighter for short)
    n = 48

    prices = shaped_price([
        (0, e), (3, 99.5), (6, 98.8), (9, 98.2), (11, 98.0),
        (14, 98.7), (17, 99.2), (19, 99.5),  # bounce (stoch overbought)
        (22, 99.0), (24, 98.5),  # bounce fades -> R1
        (27, 98.8), (30, 99.2), (33, 99.6), (36, 100.0),
        (39, 99.7), (42, 100.0), (45, 100.3), (47, 100.5),
    ], n, seed=203)

    stoch = shaped_stoch([
        (0, 45), (4, 32), (8, 22), (11, 28),
        (14, 65), (17, 85), (19, 92),  # overbought
        (22, 75), (24, 55),  # exit overzone -> R1
        (27, 50), (30, 60), (33, 72), (36, 82), (39, 88), (42, 92), (47, 95),
    ], n, seed=203)

    return plot_scenario(
        10, "One Ratchet Then Stopped",
        "Short: downtrend, bounce (stoch 9 D > 80).\nOverzone exit at bar 22 -> R1.\nSecond bounce hits R1 at bar 42.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (22, r1), (42, r1)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[22], ratchet_levels=[r1],
        cloud4_line=None, tp_line=None,
        exit_bar=42, exit_type="SL hit (R1)", is_long=False,
    )


def scenario_S4():
    """SHORT: Two ratchets, TP hit — Cloud4 lower - ATR."""
    e = 100.0
    atr = 1.0
    sl = e + 2.5 * atr
    be = e - 0.05
    avwap_lvl = e + 0.8
    r1 = e - 0.6
    r2 = e - 2.0
    n = 68

    prices = shaped_price([
        (0, e), (4, 99.2), (8, 98.5), (12, 97.8), (14, 97.5),
        (17, 98.2), (20, 98.8), (22, 98.5),  # bounce 1
        (26, 97.8), (30, 97.0), (34, 96.5), (36, 96.2),
        (39, 97.0), (42, 97.5), (44, 97.2),  # bounce 2
        (48, 96.5), (52, 95.8), (56, 95.2),
        (60, 94.8), (64, 94.4), (67, 94.2),
    ], n, seed=204)

    stoch = shaped_stoch([
        (0, 45), (5, 30), (10, 22), (14, 28),
        (17, 70), (20, 88), (22, 75),  # overbought exit -> R1
        (26, 45), (30, 28), (36, 30),
        (39, 72), (42, 90), (44, 72),  # overbought exit -> R2
        (48, 45), (52, 32), (56, 25), (60, 28), (64, 35), (67, 40),
    ], n, seed=204)

    # Cloud 4 slopes down for short
    c4 = sloped_line(0, e + 1.5, n - 1, e - 4.5, n)
    tp = sloped_line(0, e + 1.5 - atr, n - 1, e - 4.5 - atr, n)

    return plot_scenario(
        11, "Two Ratchets, TP Hit (Cloud 4 - ATR)",
        "Short: two bounce-and-continue cycles.\nR2 activates TP = Cloud4 lower - ATR.\nPrice crosses TP at bar 60. Clean winner.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (22, r1), (44, r2), (60, r2)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[22, 44], ratchet_levels=[r1, r2],
        cloud4_line=c4, tp_line=tp,
        exit_bar=60, exit_type="TP hit", is_long=False,
    )


def scenario_S5():
    """SHORT: Three ratchets, extended downtrend (~3%)."""
    e = 100.0
    atr = 1.0
    sl = e + 2.5 * atr
    be = e - 0.05
    avwap_lvl = e + 0.8
    r1 = e - 0.6
    r2 = e - 2.0
    r3 = e - 3.5
    n = 90

    prices = shaped_price([
        (0, e), (5, 99.0), (10, 98.2), (14, 97.7),
        (17, 98.5), (20, 99.0), (22, 98.6),  # bounce 1
        (28, 97.5), (34, 96.5), (38, 96.0),
        (41, 96.8), (44, 97.2), (46, 96.8),  # bounce 2
        (52, 95.5), (58, 94.5), (62, 94.0),
        (65, 94.8), (68, 95.2), (70, 94.7),  # bounce 3
        (76, 93.5), (82, 92.8), (86, 92.2), (89, 92.0),
    ], n, seed=205)

    stoch = shaped_stoch([
        (0, 45), (7, 28), (14, 30),
        (17, 75), (20, 90), (22, 70),  # R1
        (30, 28), (38, 28),
        (41, 78), (44, 92), (46, 70),  # R2
        (54, 28), (62, 32),
        (65, 80), (68, 92), (70, 68),  # R3
        (78, 35), (84, 40), (89, 45),
    ], n, seed=205)

    c4 = sloped_line(0, e + 2.0, n - 1, e - 6.5, n)
    tp = sloped_line(0, e + 2.0 - atr, n - 1, e - 6.5 - atr, n)

    return plot_scenario(
        12, "Three Ratchets, Extended Downtrend (~3%)",
        "Short: three bounce-and-continue cycles.\nTP active after R2, SL keeps ratcheting.\nR3 tightens ceiling. TP hit at bar 82.",
        prices, stoch, entry_bar=0, entry_price=e,
        sl_steps=[(0, sl), (3, be), (5, avwap_lvl), (22, r1), (46, r2), (70, r3), (82, r3)],
        be_level=be, avwap_bar=5, avwap_level=avwap_lvl,
        ratchet_bars=[22, 46, 70], ratchet_levels=[r1, r2, r3],
        cloud4_line=c4, tp_line=tp,
        exit_bar=82, exit_type="TP hit", is_long=False,
    )


# ========================================================================

def main():
    """Generate all 12 scenario visualizations."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Output dir: %s", OUTPUT_DIR)

    scenarios = [
        scenario_L1, scenario_L2, scenario_L3, scenario_L4,
        scenario_L5, scenario_L6, scenario_L7,
        scenario_S1, scenario_S2, scenario_S3, scenario_S4, scenario_S5,
    ]

    total = len(scenarios)
    for i, fn in enumerate(scenarios, 1):
        log.info("Generating scenario %d/%d...", i, total)
        fig = fn()
        out_path = OUTPUT_DIR / f"scenario_{i:02d}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        plt.close(fig)
        log.info("  Saved: %s", out_path)

    log.info("Done. All %d scenarios saved to %s", total, OUTPUT_DIR)


if __name__ == "__main__":
    main()

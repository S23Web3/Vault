# -*- coding: utf-8 -*-
"""
Strategy Market-Reading Perspectives v2 - Full Catalogue S1-S11.
Visualizes how each strategy reads the market - what it senses, what states it waits for.
One figure per strategy. Each figure: price panel + indicator panels stacked.

Strategies:
  S1  - Strategy Bible (v3.3 era): Stoch 9/40/60 rotation + 55 EMA + divergence
  S2  - v3.7 Rebate Farming: Stoch 9 cycling fast, tight band, no bias
  S3  - v3.8 Directional: Cloud 3 filter + stoch zone exit + ATR expansion
  S4  - v3.8.3/v3.8.4 (current): 60-K pin + stoch 9 cycling + AVWAP SL
  S5  - 55/89 EMA Cross Scalp: EMA delta compression + 4 stochs joint state + TDI + BBW
  S6  - Ripster EMA Cloud System: Cloud 3 bias + Cloud 2 cross + volume confirmation
  S7  - Quad Rotation Stochastic: 4-stoch alignment count + divergence from extreme
  S8  - Core Three Pillars: Cloud 3 + AVWAP + BBWP squeeze + Stoch 55 momentum
  S9  - BBWP Volatility Filter: pure volatility state machine, 6 states
  S10 - ATR SL 3-Phase: Cloud 2/3/4 cross triggers SL/TP phase transitions
  S11 - AVWAP Confirmation: 3 simultaneous AVWAPs + VSA events + anchor quality

Run: python scripts/visualize_strategy_perspectives_v2.py
Output: results/strategy_perspectives/S1_bible.png ... S11_avwap_confirmation.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

DARK_BG    = "#0f1419"
DARK_CARD  = "#1a1f26"
DARK_PANEL = "#141920"
CLR_PRICE  = "#e7e9ea"
CLR_SL     = "#ef4444"
CLR_BE     = "#f59e0b"
CLR_TRAIL  = "#8b5cf6"
CLR_TP     = "#10b981"
CLR_FAST   = "#f97316"
CLR_SLOW   = "#38bdf8"
CLR_MACRO  = "#a78bfa"
CLR_EMA    = "#22d3ee"
CLR_TDI    = "#fb7185"
CLR_BBW    = "#4ade80"
CLR_DELTA  = "#facc15"
CLR_CLOUD2 = "#1e4a2f"
CLR_C2VIS  = "#34d399"

ZONE_HIGH = 80
ZONE_LOW  = 20


def shaped(waypoints, n, noise=0.0015, seed=42):
    """Interpolate waypoints to smooth price curve with noise."""
    rng = np.random.default_rng(seed)
    bx = np.array([w[0] for w in waypoints], dtype=float)
    by = np.array([w[1] for w in waypoints], dtype=float)
    vals = np.interp(np.arange(n, dtype=float), bx, by)
    noise_arr = rng.normal(0, abs(by[0]) * noise if by[0] != 0 else noise, n)
    noise_arr = np.convolve(noise_arr, np.ones(3) / 3, mode="same")
    return vals + noise_arr


def shaped_ind(waypoints, n, noise=3.0, seed=42):
    """Interpolate indicator waypoints, clipped 0-100."""
    rng = np.random.default_rng(seed)
    bx = np.array([w[0] for w in waypoints], dtype=float)
    by = np.array([w[1] for w in waypoints], dtype=float)
    vals = np.interp(np.arange(n, dtype=float), bx, by)
    noise_arr = rng.normal(0, noise, n)
    noise_arr = np.convolve(noise_arr, np.ones(3) / 3, mode="same")
    return np.clip(vals + noise_arr, 0, 100)


def sloped(start_bar, start_val, end_bar, end_val, n):
    """Linear slope across bar range; NaN outside."""
    line = np.full(n, np.nan)
    for i in range(max(0, start_bar), min(n, end_bar + 1)):
        t = (i - start_bar) / max(end_bar - start_bar, 1)
        line[i] = start_val + t * (end_val - start_val)
    return line


def style_ax(ax):
    """Apply dark theme to axis."""
    ax.set_facecolor(DARK_PANEL)
    ax.tick_params(colors="#6b7280", labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#2d3748")
    ax.yaxis.label.set_color("#9ca3af")
    ax.xaxis.label.set_color("#9ca3af")


def zone_fill(ax, n, hi=ZONE_HIGH, lo=ZONE_LOW):
    """Shade overbought/oversold zones."""
    ax.axhline(hi, color=CLR_SL, lw=0.6, ls="--", alpha=0.5)
    ax.axhline(lo, color=CLR_TP, lw=0.6, ls="--", alpha=0.5)
    ax.fill_between(range(n), hi, 100, alpha=0.07, color=CLR_SL)
    ax.fill_between(range(n), 0, lo, alpha=0.07, color=CLR_TP)


def save_fig(fig, path):
    """Save figure with dark background."""
    fig.savefig(path, dpi=130, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)
    print("  Saved: " + str(path))


def annotate_box(ax, text, x=0.02, y=0.97):
    """Add description box top-left of axis."""
    ax.text(x, y, text, transform=ax.transAxes,
            va="top", ha="left", fontsize=7.5,
            color="#e7e9ea",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a2433",
                      edgecolor="#374151", alpha=0.9))


def build_s1(out_dir):
    """Build S1 - Strategy Bible market-reading perspective."""
    n = 120
    title = "S1 - Strategy Bible (v3.3 era) | 60-macro pin + 40-divergence + 9-cycle + 55 EMA"

    price = shaped([
        (0, 1.000), (15, 1.030), (25, 1.015), (35, 1.045),
        (50, 1.028), (60, 1.055), (75, 1.040), (90, 1.075),
        (110, 1.060), (119, 1.090)
    ], n, noise=0.003)
    ema55 = sloped(0, 0.985, 119, 1.055, n)
    avwap = sloped(0, 0.978, 119, 1.048, n)
    s9 = shaped_ind([
        (0, 55), (8, 18), (15, 72), (22, 15), (35, 80),
        (48, 12), (60, 78), (72, 14), (85, 76), (98, 12), (119, 65)
    ], n, noise=4)
    s40 = shaped_ind([
        (0, 48), (20, 22), (35, 55), (55, 18), (75, 52),
        (90, 28), (110, 60), (119, 62)
    ], n, noise=3)
    s60 = shaped_ind([
        (0, 82), (20, 85), (40, 81), (60, 84),
        (80, 82), (100, 86), (119, 83)
    ], n, noise=2)
    entries = [10, 50, 74, 100]

    fig = plt.figure(figsize=(12, 9), facecolor=DARK_BG)
    gs = GridSpec(4, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.2, 1.2, 1.2])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.plot(ema55, color=CLR_EMA, lw=1.0, ls="--", label="EMA 55", alpha=0.8)
    ax0.plot(avwap, color=CLR_TRAIL, lw=0.9, ls="-.", label="AVWAP (from low)", alpha=0.7)
    ax0.fill_between(range(n), ema55, avwap, where=(price >= ema55),
                     alpha=0.06, color=CLR_CLOUD2)
    for e in entries:
        ax0.axvline(e, color="#6b7280", lw=0.5, ls=":", alpha=0.5)
        ax0.scatter(e, price[e] * 0.997, marker="^", color=CLR_TP, s=50, zorder=5)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "LONG BIAS: Stoch 60 holds above 80 (macro bull)\n"
        "WAIT FOR: Stoch 9 to dip to oversold (<20)\n"
        "ENTER: Stoch 9 exits oversold + price on 55 EMA\n"
        "HOLD: Stoch 40 makes higher lows (divergence)"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(s9, color=CLR_FAST, lw=1.1, label="Stoch 9 (fast)")
    zone_fill(ax1, n)
    for e in entries:
        ax1.axvline(e, color="#6b7280", lw=0.5, ls=":", alpha=0.5)
    ax1.set_ylabel("Stoch 9", fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    ax2.plot(s40, color=CLR_SLOW, lw=1.1, label="Stoch 40 (divergence)")
    zone_fill(ax2, n)
    ax2.annotate("Stage 1", (20, s40[20]),
                 xytext=(23, s40[20] + 12), color="#facc15", fontsize=7,
                 arrowprops=dict(arrowstyle="->", color="#facc15", lw=0.8))
    ax2.annotate("Stage 2 (higher low)", (55, s40[55]),
                 xytext=(58, s40[55] + 12), color="#facc15", fontsize=7,
                 arrowprops=dict(arrowstyle="->", color="#facc15", lw=0.8))
    ax2.set_ylabel("Stoch 40", fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    style_ax(ax3)
    ax3.plot(s60, color=CLR_MACRO, lw=1.1, label="Stoch 60 (macro filter)")
    ax3.axhline(80, color=CLR_SL, lw=0.6, ls="--", alpha=0.5)
    ax3.fill_between(range(n), 80, 100, alpha=0.1, color=CLR_MACRO)
    ax3.text(2, 82, "BULL MACRO ZONE - all entries allowed", color="#a78bfa",
             fontsize=6.5, va="bottom")
    ax3.set_ylabel("Stoch 60", fontsize=8)
    ax3.set_ylim(0, 100)
    ax3.set_xlabel("Bars", fontsize=8)
    ax3.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S1_bible.png")


def build_s2(out_dir):
    """Build S2 - v3.7 Rebate Farming market-reading perspective."""
    n = 120
    title = "S2 - v3.7 Rebate Farming | Stoch 9 fast cycling, direction irrelevant, volume is the goal"

    price = shaped([
        (0, 1.000), (12, 1.018), (20, 0.992), (32, 1.015),
        (44, 0.988), (55, 1.012), (66, 0.990), (78, 1.014),
        (90, 0.985), (105, 1.010), (119, 0.995)
    ], n, noise=0.004)
    atr = 0.012
    s9 = shaped_ind([
        (0, 50), (8, 82), (14, 15), (22, 78), (30, 12),
        (38, 85), (46, 18), (54, 80), (62, 14), (70, 82),
        (78, 16), (86, 80), (94, 12), (102, 78), (110, 20), (119, 60)
    ], n, noise=4)
    long_entries  = [16, 48, 80, 112]
    short_entries = [10, 32, 54, 86]

    fig = plt.figure(figsize=(12, 7), facecolor=DARK_BG)
    gs = GridSpec(2, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.5])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.fill_between(range(n), price - atr, price + atr,
                     alpha=0.08, color=CLR_BE, label="1 ATR band")
    for e in long_entries:
        ax0.scatter(e, price[e], marker="^", color=CLR_TP, s=45, zorder=5)
        ax0.plot([e, min(e + 12, n - 1)],
                 [price[e] + atr * 1.5, price[e] + atr * 1.5],
                 color=CLR_TP, lw=0.8, ls="--", alpha=0.6)
        ax0.plot([e, min(e + 12, n - 1)],
                 [price[e] - atr, price[e] - atr],
                 color=CLR_SL, lw=0.8, ls="--", alpha=0.6)
    for e in short_entries:
        ax0.scatter(e, price[e], marker="v", color=CLR_SL, s=45, zorder=5)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "NO DIRECTIONAL BIAS - longs and shorts equally valid\n"
        "TRIGGER: Stoch 9 exits oversold (long) or overbought (short)\n"
        "SL: 1.0 ATR | TP: 1.5 ATR - fixed at entry, no trailing\n"
        "GOAL: Volume = rebate income. Flat equity is acceptable."
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(s9, color=CLR_FAST, lw=1.2, label="Stoch 9 (sole trigger)")
    zone_fill(ax1, n)
    for e in long_entries:
        ax1.axvline(e, color=CLR_TP, lw=0.6, ls=":", alpha=0.6)
    for e in short_entries:
        ax1.axvline(e, color=CLR_SL, lw=0.6, ls=":", alpha=0.6)
    ax1.text(2, 85, "OVERBOUGHT - short entry on exit", color=CLR_SL, fontsize=6.5)
    ax1.text(2, 3, "OVERSOLD - long entry on exit", color=CLR_TP, fontsize=6.5)
    ax1.set_ylabel("Stoch 9", fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.set_xlabel("Bars", fontsize=8)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S2_rebate_farming.png")


def build_s3(out_dir):
    """Build S3 - v3.8 directional filter market-reading perspective."""
    n = 120
    title = "S3 - v3.8 Directional Filter | Cloud 3 bias + ATR expansion + stoch zone exit"

    price = shaped([
        (0, 1.000), (20, 1.040), (35, 1.025), (55, 1.070),
        (70, 1.055), (90, 1.095), (110, 1.080), (119, 1.110)
    ], n, noise=0.003)
    cloud3_top = sloped(0, 0.975, 119, 1.060, n)
    cloud3_bot = sloped(0, 0.960, 119, 1.042, n)
    atr_vals = shaped_ind([
        (0, 30), (15, 45), (30, 35), (50, 55),
        (65, 42), (85, 60), (100, 48), (119, 58)
    ], n, noise=4)
    atr_actual = 0.010 + atr_vals / 1000
    s9 = shaped_ind([
        (0, 55), (12, 15), (22, 72), (38, 12), (52, 68),
        (65, 18), (78, 70), (92, 14), (105, 65), (119, 55)
    ], n, noise=4)
    entries = [14, 40, 67, 94]

    fig = plt.figure(figsize=(12, 8), facecolor=DARK_BG)
    gs = GridSpec(3, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.2, 1.2])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.fill_between(range(n), cloud3_bot, cloud3_top,
                     alpha=0.18, color=CLR_EMA, label="Cloud 3 (34/50)")
    ax0.plot(cloud3_top, color=CLR_EMA, lw=0.7, ls="--", alpha=0.7)
    ax0.plot(cloud3_bot, color=CLR_EMA, lw=0.7, ls="--", alpha=0.7)
    for e in entries:
        ax0.scatter(e, price[e] * 0.997, marker="^", color=CLR_TP, s=50, zorder=5)
        sl_level = price[e] - atr_actual[e] * 2.5
        ax0.plot([e, min(e + 20, n - 1)],
                 [sl_level, sl_level], color=CLR_SL, lw=0.8, ls="--", alpha=0.5)
    ax0.fill_between(range(n), 0.94, cloud3_bot, alpha=0.05, color=CLR_SL)
    ax0.text(2, 0.950, "SHORT-ONLY below Cloud 3", color=CLR_SL, fontsize=6.5)
    ax0.text(2, cloud3_top[5] + 0.004, "LONG-ONLY above Cloud 3", color=CLR_TP, fontsize=6.5)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "DIRECTION: Price vs Cloud 3 - ABOVE = long-only, BELOW = short-only\n"
        "TRIGGER: Stoch 9 exits oversold/overbought in allowed direction\n"
        "BE RAISE: ATR-based - profit > 0.5 ATR triggers SL to entry + 0.3 ATR\n"
        "FILTER: ATR must be expanding (not flat, not maxed)"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(s9, color=CLR_FAST, lw=1.1, label="Stoch 9 (entry trigger)")
    zone_fill(ax1, n)
    for e in entries:
        ax1.axvline(e, color=CLR_TP, lw=0.6, ls=":", alpha=0.6)
    ax1.text(2, 3, "OVERSOLD - long entry on exit (Cloud 3 above = allowed)", color=CLR_TP, fontsize=6.5)
    ax1.set_ylabel("Stoch 9", fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    ax2.plot(atr_vals, color=CLR_BBW, lw=1.1, label="ATR (relative)")
    ax2.axhline(50, color=CLR_BE, lw=0.6, ls="--", alpha=0.5, label="ATR midpoint")
    for e in entries:
        ax2.axvline(e, color=CLR_TP, lw=0.6, ls=":", alpha=0.6)
    ax2.text(2, 52, "ATR expanding = volatility confirming trend", color=CLR_BBW, fontsize=6.5)
    ax2.set_ylabel("ATR (relative)", fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.set_xlabel("Bars", fontsize=8)
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S3_v38_directional.png")


def build_s4(out_dir):
    """Build S4 - v3.8.3/v3.8.4 current production market-reading perspective."""
    n = 130
    title = "S4 - v3.8.3/v3.8.4 (Current) | 60-K macro pin + stoch 9 cycle + AVWAP dynamic floor"

    price = shaped([
        (0, 1.000), (18, 1.050), (30, 1.030), (45, 1.075),
        (60, 1.055), (75, 1.090), (88, 1.070), (100, 1.100),
        (115, 1.085), (129, 1.115)
    ], n, noise=0.003)
    avwap_center = sloped(0, 0.988, 129, 1.090, n)
    avwap_2sig   = avwap_center - 0.018
    s9 = shaped_ind([
        (0, 60), (10, 14), (18, 75), (28, 12), (40, 78),
        (52, 16), (62, 72), (74, 14), (85, 76), (98, 12),
        (108, 70), (120, 15), (129, 68)
    ], n, noise=4)
    s60 = shaped_ind([
        (0, 83), (20, 87), (40, 84), (60, 88),
        (80, 85), (100, 89), (120, 86), (129, 88)
    ], n, noise=1.5)
    a_entries = [12, 53, 76, 110]

    fig = plt.figure(figsize=(12, 9), facecolor=DARK_BG)
    gs = GridSpec(3, 1, figure=fig, hspace=0.08, height_ratios=[3.5, 1.2, 1.2])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.plot(avwap_center, color=CLR_TRAIL, lw=1.0, ls="--",
             label="AVWAP center", alpha=0.8)
    ax0.plot(avwap_2sig, color=CLR_SL, lw=0.9, ls="-.",
             label="AVWAP -2 sigma (SL after bar 5)", alpha=0.7)
    ax0.fill_between(range(n), avwap_2sig, avwap_center, alpha=0.06, color=CLR_TRAIL)
    for i, e in enumerate(a_entries):
        ax0.scatter(e, price[e] * 0.997, marker="^", color=CLR_TP, s=55, zorder=5,
                    label="A entry" if i == 0 else "")
        sl_p1 = price[e] - 0.025
        ax0.plot([e, min(e + 5, n - 1)],
                 [sl_p1, sl_p1], color=CLR_SL, lw=1.0, ls="--", alpha=0.6)
        if e + 5 < n:
            ax0.axvline(e + 5, color=CLR_BE, lw=0.6, ls=":", alpha=0.5)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD, ncol=2)
    annotate_box(ax0,
        "MACRO CONDITION: Stoch 60 pinned above 80 (bull) or below 20 (bear)\n"
        "TRIGGER: Stoch 9 exits oversold while 4/4 stochs aligned = Grade A\n"
        "SL Phase 1 (bars 0-4): 2.5 ATR from entry\n"
        "SL Phase 2 (bar 5+): AVWAP -2 sigma (frozen or live per ratchet)\n"
        "TP: coin-specific ATR multiple (RIVER 2.0, KITE/BERA no TP)"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(s9, color=CLR_FAST, lw=1.1, label="Stoch 9 (entry cycle)")
    zone_fill(ax1, n)
    for e in a_entries:
        ax1.axvline(e, color=CLR_TP, lw=0.7, ls=":", alpha=0.7)
        ax1.scatter(e, s9[e] + 3, marker="^", color=CLR_TP, s=30, zorder=5)
    ax1.text(2, 3, "Exit oversold + 60 pinned + alignment = A signal", color=CLR_TP, fontsize=6.5)
    ax1.set_ylabel("Stoch 9", fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    ax2.plot(s60, color=CLR_MACRO, lw=1.2, label="Stoch 60 (macro pin)")
    ax2.axhline(80, color=CLR_SL, lw=0.7, ls="--", alpha=0.6)
    ax2.fill_between(range(n), 80, 100, alpha=0.10, color=CLR_MACRO)
    ax2.text(2, 81, "PINNED: 60-K above 80 = macro bull condition active", color=CLR_MACRO, fontsize=6.5)
    ax2.set_ylabel("Stoch 60", fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.set_xlabel("Bars", fontsize=8)
    ax2.legend(loc="lower right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S4_v384_current.png")


def build_s5(out_dir):
    """Build S5 - 55/89 EMA Cross Scalp market-reading perspective."""
    n = 140
    title = "S5 - 55/89 EMA Cross Scalp (Research) | EMA delta compression + 4-stoch alignment + TDI + BBW"

    price = shaped([
        (0, 1.000), (20, 1.012), (35, 1.006), (50, 1.014),
        (60, 1.008), (65, 1.010),
        (80, 1.035), (95, 1.025), (110, 1.048), (129, 1.040), (139, 1.055)
    ], n, noise=0.002)
    ema55 = shaped([
        (0, 0.998), (30, 1.006), (50, 1.009), (65, 1.012),
        (80, 1.028), (110, 1.042), (139, 1.052)
    ], n, noise=0.001)
    ema89 = shaped([
        (0, 0.994), (30, 1.002), (50, 1.008), (65, 1.011),
        (80, 1.022), (110, 1.035), (139, 1.046)
    ], n, noise=0.001)
    delta = shaped_ind([
        (0, 55), (20, 52), (40, 50.5), (60, 50.05),
        (65, 50), (80, 52), (100, 54), (120, 55), (139, 56)
    ], n, noise=0.5)
    delta_rescaled = delta - 50
    s9 = shaped_ind([
        (0, 45), (15, 18), (28, 60), (40, 22),
        (55, 65), (65, 55), (80, 72), (95, 18),
        (108, 65), (120, 14), (139, 60)
    ], n, noise=3)
    s40 = shaped_ind([
        (0, 40), (20, 25), (40, 38), (55, 45),
        (65, 52), (80, 60), (100, 55), (120, 62), (139, 65)
    ], n, noise=3)
    tdi = shaped_ind([
        (0, 48), (20, 42), (40, 46), (55, 52),
        (65, 56), (80, 63), (100, 58), (120, 64), (139, 60)
    ], n, noise=2)
    tdi_signal = shaped_ind([
        (0, 50), (20, 46), (40, 47), (55, 50),
        (65, 53), (80, 59), (100, 56), (120, 61), (139, 58)
    ], n, noise=1)
    bbw = shaped_ind([
        (0, 45), (20, 38), (40, 30), (55, 25),
        (65, 32), (80, 48), (100, 55), (120, 50), (139, 52)
    ], n, noise=3)
    bbw_ma = shaped_ind([
        (0, 48), (30, 40), (55, 28), (80, 42),
        (110, 50), (139, 51)
    ], n, noise=1)

    monitoring_start = 40
    cross_bar = 65
    bars = np.arange(n)

    fig = plt.figure(figsize=(13, 11), facecolor=DARK_BG)
    gs = GridSpec(5, 1, figure=fig, hspace=0.07, height_ratios=[3, 1, 1, 1, 1])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.plot(ema55, color=CLR_EMA, lw=1.0, ls="--", label="EMA 55", alpha=0.9)
    ax0.plot(ema89, color=CLR_TRAIL, lw=1.0, ls="--", label="EMA 89", alpha=0.9)
    ax0.fill_between(range(n), ema55, ema89, alpha=0.12, color=CLR_DELTA)
    ax0.axvspan(monitoring_start, cross_bar, alpha=0.06, color=CLR_BE,
                label="MONITORING window")
    ax0.axvline(cross_bar, color=CLR_DELTA, lw=1.2, ls="--", alpha=0.8,
                label="EMA cross (signal)")
    ax0.scatter(cross_bar, price[cross_bar] * 0.997,
                marker="^", color=CLR_TP, s=70, zorder=6, label="LONG entry")
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD, ncol=3)
    annotate_box(ax0,
        "STATE 1 (IDLE): waiting for stoch 9 K/D cross\n"
        "STATE 2 (MONITORING): stoch 9 crossed - checking full alignment:\n"
        "  stoch 14 MOVING/EXTENDED | stoch 40/60 TURNING+\n"
        "  EMA delta compressing    | TDI above signal | BBW not QUIET\n"
        "FIRE: EMA 55/89 cross while alignment holds"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(delta_rescaled, color=CLR_DELTA, lw=1.1, label="EMA delta (55-89)")
    ax1.axhline(0, color="#ffffff", lw=0.6, ls="--", alpha=0.4)
    dr = np.array(delta_rescaled)
    ax1.fill_between(bars, dr, 0, where=(dr >= 0), alpha=0.15, color=CLR_TP)
    ax1.fill_between(bars, dr, 0, where=(dr < 0), alpha=0.15, color=CLR_SL)
    ax1.axvspan(monitoring_start, cross_bar, alpha=0.06, color=CLR_BE)
    ax1.axvline(cross_bar, color=CLR_DELTA, lw=0.8, ls="--", alpha=0.7)
    ax1.text(2, 4.5, "Delta compressing toward zero = EMAs converging", color=CLR_DELTA, fontsize=6.5)
    ax1.set_ylabel("Delta", fontsize=8)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    ax2.plot(s9, color=CLR_FAST, lw=1.0, label="Stoch 9 (gate trigger)")
    ax2.plot(s40, color=CLR_SLOW, lw=1.0, label="Stoch 40 (alignment)")
    zone_fill(ax2, n)
    ax2.axvline(monitoring_start, color=CLR_BE, lw=0.8, ls=":", alpha=0.7)
    ax2.axvline(cross_bar, color=CLR_DELTA, lw=0.8, ls="--", alpha=0.7)
    ax2.text(monitoring_start + 1, 85, "MONITORING start", color=CLR_BE, fontsize=6.5)
    ax2.set_ylabel("Stoch 9/40", fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    style_ax(ax3)
    ax3.plot(tdi, color=CLR_TDI, lw=1.0, label="TDI (RSI 9 smoothed)")
    ax3.plot(tdi_signal, color="#fca5a5", lw=0.8, ls="--", label="TDI signal")
    tdi_arr = np.array(tdi)
    tdi_sig_arr = np.array(tdi_signal)
    ax3.fill_between(bars, tdi_arr, tdi_sig_arr,
                     where=(tdi_arr >= tdi_sig_arr), alpha=0.12, color=CLR_TP)
    ax3.axvline(cross_bar, color=CLR_DELTA, lw=0.8, ls="--", alpha=0.7)
    ax3.text(2, 40, "TDI above signal = momentum confirming", color=CLR_TP, fontsize=6.5)
    ax3.set_ylabel("TDI", fontsize=8)
    ax3.set_ylim(20, 80)
    ax3.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax4 = fig.add_subplot(gs[4], sharex=ax0)
    style_ax(ax4)
    ax4.plot(bbw, color=CLR_BBW, lw=1.0, label="BBW spectrum")
    ax4.plot(bbw_ma, color="#86efac", lw=0.8, ls="--", label="BBW MA (7)")
    bbw_arr = np.array(bbw)
    bbw_ma_arr = np.array(bbw_ma)
    ax4.fill_between(bars, bbw_arr, bbw_ma_arr,
                     where=(bbw_arr >= bbw_ma_arr), alpha=0.12, color=CLR_BBW, label="HEALTHY")
    ax4.fill_between(bars, bbw_arr, bbw_ma_arr,
                     where=(bbw_arr < bbw_ma_arr), alpha=0.12, color=CLR_SL, label="QUIET (blocked)")
    ax4.axvline(cross_bar, color=CLR_DELTA, lw=0.8, ls="--", alpha=0.7)
    ax4.text(2, 22, "QUIET = no signal fired (BBW below MA)", color=CLR_SL, fontsize=6.5)
    ax4.set_ylabel("BBW", fontsize=8)
    ax4.set_xlabel("Bars", fontsize=8)
    ax4.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)
    plt.setp(ax3.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S5_5589_scalp.png")


def build_s6(out_dir):
    """Build S6 - Ripster EMA Cloud System market-reading perspective."""
    n = 130
    title = "S6 - Ripster EMA Cloud System | Cloud 3 bias + Cloud 2 cross + volume trend day gate"

    price = shaped([
        (0, 1.000), (15, 1.025), (28, 1.015), (42, 1.055),
        (58, 1.042), (70, 1.075), (85, 1.060), (100, 1.095),
        (115, 1.080), (129, 1.110)
    ], n, noise=0.003)
    cloud3_top = sloped(0, 0.988, 129, 1.075, n)
    cloud3_bot = sloped(0, 0.972, 129, 1.055, n)
    cloud2_top = shaped([
        (0, 0.998), (15, 1.022), (28, 1.013), (42, 1.052),
        (58, 1.040), (70, 1.073), (85, 1.058), (100, 1.093),
        (115, 1.078), (129, 1.108)
    ], n, noise=0.001)
    cloud2_bot = shaped([
        (0, 0.993), (15, 1.017), (28, 1.008), (42, 1.047),
        (58, 1.035), (70, 1.068), (85, 1.053), (100, 1.088),
        (115, 1.073), (129, 1.103)
    ], n, noise=0.001)
    cloud2_delta = shaped_ind([
        (0, 48), (12, 52), (25, 58), (35, 55),
        (45, 62), (60, 59), (75, 64), (90, 61), (110, 65), (129, 63)
    ], n, noise=2)
    rng_vol = np.random.default_rng(77)
    rel_vol = np.clip(rng_vol.normal(60, 20, n), 10, 120)
    rel_vol[20:35] = np.clip(rng_vol.normal(85, 10, 15), 70, 120)
    cross_bars = [25, 60, 88]
    entries = [28, 63, 91]

    fig = plt.figure(figsize=(12, 9), facecolor=DARK_BG)
    gs = GridSpec(3, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.2, 1.2])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.fill_between(range(n), cloud3_bot, cloud3_top,
                     alpha=0.15, color=CLR_EMA, label="Cloud 3 (34/50)")
    ax0.plot(cloud3_top, color=CLR_EMA, lw=0.6, ls="--", alpha=0.6)
    ax0.plot(cloud3_bot, color=CLR_EMA, lw=0.6, ls="--", alpha=0.6)
    ax0.plot(cloud2_top, color=CLR_C2VIS, lw=0.9, label="Cloud 2 top (5 EMA)")
    ax0.plot(cloud2_bot, color=CLR_C2VIS, lw=0.9, ls="--", label="Cloud 2 bot (12 EMA)", alpha=0.7)
    for b in cross_bars:
        ax0.axvline(b, color=CLR_DELTA, lw=0.8, ls=":", alpha=0.6)
    for e in entries:
        ax0.scatter(e, price[e] * 0.997, marker="^", color=CLR_TP, s=55, zorder=5)
    ax0.fill_between(range(n), cloud3_top, np.full(n, 1.12),
                     alpha=0.04, color=CLR_TP)
    ax0.text(2, 1.095, "ABOVE CLOUD 3 = LONG ONLY zone", color=CLR_TP, fontsize=6.5)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD, ncol=2)
    annotate_box(ax0,
        "BIAS: Price vs Cloud 3 (34/50) — above = LONG ONLY, below = SHORT ONLY\n"
        "TRIGGER: Cloud 2 (5/12) crosses in trade direction\n"
        "HOLD: 10-min candles riding the 5/12 cloud = trend active\n"
        "EXIT: 10-min candle closes against 5/12 cloud = exit immediately"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(cloud2_delta, color=CLR_C2VIS, lw=1.1, label="Cloud 2 delta (5-12)")
    ax1.axhline(50, color="#ffffff", lw=0.6, ls="--", alpha=0.3)
    ax1.fill_between(range(n), 50, cloud2_delta,
                     where=(cloud2_delta >= 50), alpha=0.15, color=CLR_TP)
    for b in cross_bars:
        ax1.axvline(b, color=CLR_DELTA, lw=0.8, ls=":", alpha=0.6)
        ax1.text(b + 1, 55, "CROSS", color=CLR_DELTA, fontsize=6.5)
    ax1.text(2, 65, "5 above 12 = Cloud 2 bullish = riding phase", color=CLR_C2VIS, fontsize=6.5)
    ax1.set_ylabel("C2 Delta", fontsize=8)
    ax1.set_ylim(30, 80)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    colors_vol = [CLR_TP if v >= 75 else CLR_BE if v >= 50 else "#6b7280" for v in rel_vol]
    ax2.bar(range(n), rel_vol, color=colors_vol, alpha=0.7, width=1.0)
    ax2.axhline(75, color=CLR_TP, lw=0.8, ls="--", alpha=0.7, label="20% above avg (trend day)")
    ax2.text(2, 78, "20%+ relative volume = trend day confirmed", color=CLR_TP, fontsize=6.5)
    ax2.set_ylabel("Rel. Volume %", fontsize=8)
    ax2.set_xlabel("Bars", fontsize=8)
    ax2.set_ylim(0, 130)
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S6_ripster_clouds.png")


def build_s7(out_dir):
    """Build S7 - Quad Rotation Stochastic market-reading perspective."""
    n = 130
    title = "S7 - Quad Rotation Stochastic | 4-stoch alignment count + divergence from extreme"

    s9 = shaped_ind([
        (0, 55), (8, 18), (16, 75), (25, 12), (36, 82),
        (48, 16), (58, 78), (70, 14), (82, 80), (95, 12),
        (108, 75), (120, 18), (129, 70)
    ], n, noise=4)
    s14 = shaped_ind([
        (0, 52), (12, 22), (22, 68), (32, 18), (45, 74),
        (57, 20), (67, 70), (78, 18), (90, 72), (103, 20),
        (115, 68), (129, 65)
    ], n, noise=3)
    s40 = shaped_ind([
        (0, 48), (18, 30), (32, 55), (48, 28), (62, 60),
        (78, 32), (92, 62), (108, 35), (129, 62)
    ], n, noise=3)
    s60 = shaped_ind([
        (0, 82), (25, 84), (50, 80), (75, 85),
        (100, 81), (129, 83)
    ], n, noise=2)
    bars = np.arange(n)
    above50_s9  = (s9  >= 50).astype(int)
    above50_s14 = (s14 >= 50).astype(int)
    above50_s40 = (s40 >= 50).astype(int)
    above50_s60 = (s60 >= 50).astype(int)
    alignment = above50_s9 + above50_s14 + above50_s40 + above50_s60
    div_bars = [23, 68, 100]

    fig = plt.figure(figsize=(12, 8), facecolor=DARK_BG)
    gs = GridSpec(2, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.5])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    alpha_bg = alignment / 4.0 * 0.18
    for i in range(n - 1):
        ax0.axvspan(i, i + 1, alpha=float(alpha_bg[i]), color=CLR_TP, zorder=0)
    ax0.plot(s9,  color=CLR_FAST,  lw=1.2, label="Stoch 9 (fast)")
    ax0.plot(s14, color=CLR_TDI,   lw=1.0, label="Stoch 14 (standard)")
    ax0.plot(s40, color=CLR_SLOW,  lw=1.0, label="Stoch 40 (medium)")
    ax0.plot(s60, color=CLR_MACRO, lw=1.0, label="Stoch 60 (macro)")
    ax0.axhline(50, color="#ffffff", lw=0.6, ls="--", alpha=0.25)
    zone_fill(ax0, n)
    for db in div_bars:
        ax0.scatter(db, s9[db], marker="D", color=CLR_DELTA, s=45, zorder=6)
        ax0.text(db + 1, s9[db] + 5, "DIV", color=CLR_DELTA, fontsize=6.5)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD, ncol=2)
    annotate_box(ax0,
        "4/4 ALIGNED = full consensus — strongest setup\n"
        "3/4 = strong setup | 2/4 + macro climbing = continuation\n"
        "DIVERGENCE from extreme (<20 or >80): price lower low + stoch higher low = bullish\n"
        "Background shade intensity = alignment count (darker = more agreement)"
    )
    ax0.set_ylabel("Stoch (all 4)", fontsize=8)
    ax0.set_ylim(0, 100)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    align_colors = [CLR_SL if a <= 1 else CLR_BE if a == 2 else CLR_TP for a in alignment]
    ax1.bar(bars, alignment, color=align_colors, alpha=0.75, width=1.0)
    ax1.axhline(3, color=CLR_BE, lw=0.7, ls="--", alpha=0.6, label="3/4 threshold")
    ax1.axhline(4, color=CLR_TP, lw=0.7, ls="--", alpha=0.6, label="4/4 full consensus")
    for db in div_bars:
        ax1.scatter(db, alignment[db] + 0.1, marker="D", color=CLR_DELTA, s=35, zorder=6)
    ax1.text(2, 3.1, "STRONG zone", color=CLR_BE, fontsize=6.5)
    ax1.text(2, 4.05, "FULL consensus", color=CLR_TP, fontsize=6.5)
    ax1.set_ylabel("Alignment (0-4)", fontsize=8)
    ax1.set_ylim(0, 5)
    ax1.set_xlabel("Bars", fontsize=8)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S7_quad_rotation.png")


def build_s8(out_dir):
    """Build S8 - Core Three Pillars Framework market-reading perspective."""
    n = 140
    title = "S8 - Core Three Pillars | Cloud 3 + AVWAP (P1/P2) + BBWP squeeze + Stoch 55 momentum (P3)"

    price = shaped([
        (0, 1.000), (20, 1.030), (35, 1.020), (52, 1.055),
        (70, 1.042), (85, 1.070), (100, 1.058), (115, 1.085),
        (129, 1.072), (139, 1.090)
    ], n, noise=0.003)
    cloud3_top = sloped(0, 0.982, 139, 1.065, n)
    cloud3_bot = sloped(0, 0.965, 139, 1.045, n)
    avwap_low = sloped(0, 0.975, 139, 1.060, n)
    bbwp = shaped_ind([
        (0, 25), (15, 12), (28, 8), (40, 5),
        (52, 18), (65, 35), (78, 55), (90, 65),
        (105, 50), (120, 42), (139, 38)
    ], n, noise=3)
    bbwp_ma = shaped_ind([
        (0, 28), (20, 15), (40, 8), (55, 22),
        (75, 48), (100, 60), (120, 45), (139, 40)
    ], n, noise=2)
    squeeze_end = 50
    s55_cont = shaped_ind([
        (0, 45), (30, 38), (45, 30), (52, 35),
        (58, 52), (68, 62), (80, 70), (95, 75),
        (110, 72), (125, 78), (139, 80)
    ], n, noise=3)
    s55_decl = shaped_ind([
        (0, 45), (30, 38), (45, 30), (52, 35),
        (58, 52), (68, 60), (80, 55), (95, 48),
        (110, 40), (125, 35), (139, 32)
    ], n, noise=3)
    cross_bar = 58

    fig = plt.figure(figsize=(12, 9), facecolor=DARK_BG)
    gs = GridSpec(3, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.2, 1.5])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.fill_between(range(n), cloud3_bot, cloud3_top,
                     alpha=0.14, color=CLR_EMA, label="Cloud 3 (34/50) — Pillar 1")
    ax0.plot(cloud3_top, color=CLR_EMA, lw=0.6, ls="--", alpha=0.6)
    ax0.plot(cloud3_bot, color=CLR_EMA, lw=0.6, ls="--", alpha=0.6)
    ax0.plot(avwap_low, color=CLR_TRAIL, lw=1.0, ls="-.",
             label="AVWAP from swing low — Pillar 2", alpha=0.85)
    ax0.fill_between(range(n), avwap_low, cloud3_bot, alpha=0.05, color=CLR_TRAIL)
    ax0.axvspan(squeeze_end - 10, squeeze_end, alpha=0.08, color=CLR_BE, label="BBWP squeeze zone")
    ax0.scatter(cross_bar, price[cross_bar] * 0.997, marker="^", color=CLR_TP, s=60, zorder=6)
    ax0.axvline(cross_bar, color=CLR_DELTA, lw=0.8, ls=":", alpha=0.6)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "PILLAR 1: Price above Cloud 3 (34/50) — buyers in structural control\n"
        "PILLAR 2: AVWAP from swing low above entry — volume confirms buyers\n"
        "PILLAR 3: Stoch 55 crosses AND keeps building after cross\n"
        "GATE: BBWP in squeeze (<10%) before entry — coiled spring"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(bbwp, color=CLR_BBW, lw=1.1, label="BBWP")
    ax1.plot(bbwp_ma, color="#86efac", lw=0.8, ls="--", label="BBWP MA (5)")
    ax1.axhline(10, color="#3b82f6", lw=0.8, ls="--", alpha=0.7, label="Squeeze threshold (<10%)")
    ax1.fill_between(range(n), 0, bbwp,
                     where=(bbwp <= 10), alpha=0.25, color="#3b82f6")
    ax1.fill_between(range(n), 0, bbwp,
                     where=(bbwp > 10), alpha=0.08, color=CLR_BBW)
    ax1.axvspan(squeeze_end - 10, squeeze_end, alpha=0.12, color=CLR_BE)
    ax1.text(2, 12, "BLUE = squeeze active — coiled for move", color="#3b82f6", fontsize=6.5)
    ax1.text(squeeze_end + 2, 35, "Expanding", color=CLR_BBW, fontsize=6.5)
    ax1.set_ylabel("BBWP %", fontsize=8)
    ax1.set_ylim(0, 80)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    ax2.plot(s55_cont, color=CLR_TP, lw=1.2, label="Stoch 55 — CONTINUES building (HOLD)")
    ax2.plot(s55_decl, color=CLR_SL, lw=1.2, ls="--", label="Stoch 55 — DECLINES after cross (EXIT)")
    ax2.axhline(50, color="#ffffff", lw=0.5, ls="--", alpha=0.2)
    ax2.axvline(cross_bar, color=CLR_DELTA, lw=0.9, ls=":", alpha=0.7)
    ax2.text(cross_bar + 1, 55, "CROSS", color=CLR_DELTA, fontsize=6.5)
    ax2.fill_between(range(cross_bar, n), s55_cont[cross_bar:], s55_decl[cross_bar:],
                     alpha=0.08, color=CLR_TP)
    ax2.text(cross_bar + 8, 72, "CONTINUES = hold", color=CLR_TP, fontsize=6.5)
    ax2.text(cross_bar + 8, 42, "DECLINES = exit small win", color=CLR_SL, fontsize=6.5)
    ax2.set_ylabel("Stoch 55 (P3)", fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.set_xlabel("Bars", fontsize=8)
    ax2.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S8_three_pillars.png")


def build_s9(out_dir):
    """Build S9 - BBWP Volatility Filter pure state machine perspective."""
    n = 140
    title = "S9 - BBWP Volatility Filter | 6 volatility states — FILTER only, not direction"

    bbwp = shaped_ind([
        (0, 8), (12, 5), (22, 3), (32, 12),
        (42, 22), (52, 35), (62, 55), (72, 70),
        (82, 88), (92, 95), (102, 78), (112, 60),
        (122, 45), (132, 30), (139, 15)
    ], n, noise=2.5)
    bbwp_ma = shaped_ind([
        (0, 10), (15, 7), (30, 10), (42, 20),
        (55, 38), (68, 58), (80, 78), (92, 90),
        (102, 82), (112, 65), (122, 50), (132, 35), (139, 18)
    ], n, noise=1.5)
    bars = np.arange(n)

    bd_mask  = (bbwp <= 10) & (bbwp < 25)
    b_mask   = (bbwp > 10) & (bbwp < 25)
    rd_mask  = (bbwp >= 90) & (bbwp > 75)
    r_mask   = (bbwp >= 75) & (bbwp < 90)
    mid_mask = (bbwp >= 25) & (bbwp < 75)

    mcu_bar = None
    mcd_bar = None
    for i in range(1, n):
        if mcu_bar is None and bbwp[i] > bbwp_ma[i] and bbwp[i - 1] <= bbwp_ma[i - 1]:
            mcu_bar = i
        if mcd_bar is None and i > 70 and bbwp[i] < bbwp_ma[i] and bbwp[i - 1] >= bbwp_ma[i - 1]:
            mcd_bar = i

    fig = plt.figure(figsize=(12, 7), facecolor=DARK_BG)
    gs = GridSpec(1, 1, figure=fig)
    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)

    ax0.fill_between(bars, 0, bbwp, where=bd_mask, alpha=0.45, color="#3b82f6",
                     label="BLUE DOUBLE (<=10, extreme squeeze)")
    ax0.fill_between(bars, 0, bbwp, where=b_mask,  alpha=0.25, color="#60a5fa",
                     label="BLUE (<25, squeeze)")
    ax0.fill_between(bars, 0, bbwp, where=mid_mask, alpha=0.08, color="#9ca3af")
    ax0.fill_between(bars, 0, bbwp, where=r_mask,  alpha=0.25, color="#f97316",
                     label="RED (>75, expansion)")
    ax0.fill_between(bars, 0, bbwp, where=rd_mask, alpha=0.45, color="#ef4444",
                     label="RED DOUBLE (>=90, extreme)")

    ax0.plot(bbwp, color=CLR_BBW, lw=1.3, label="BBWP", zorder=5)
    ax0.plot(bbwp_ma, color="#ffffff", lw=0.9, ls="--", label="BBWP MA (5)", alpha=0.7, zorder=5)

    ax0.axhline(10, color="#3b82f6", lw=0.6, ls=":", alpha=0.6)
    ax0.axhline(25, color="#60a5fa", lw=0.6, ls=":", alpha=0.5)
    ax0.axhline(75, color="#f97316", lw=0.6, ls=":", alpha=0.5)
    ax0.axhline(90, color=CLR_SL,   lw=0.6, ls=":", alpha=0.6)

    ax0.text(2, 6, "BLUE DOUBLE", color="#3b82f6", fontsize=6.5, fontweight="bold")
    ax0.text(35, 16, "BLUE", color="#60a5fa", fontsize=6.5)
    ax0.text(68, 78, "RED", color="#f97316", fontsize=6.5)
    ax0.text(82, 92, "RED DOUBLE", color=CLR_SL, fontsize=6.5, fontweight="bold")

    if mcu_bar is not None:
        ax0.axvline(mcu_bar, color=CLR_TP, lw=1.0, ls="--", alpha=0.8)
        ax0.text(mcu_bar + 1, 42, "MA CROSS UP", color=CLR_TP, fontsize=6.5)
    if mcd_bar is not None:
        ax0.axvline(mcd_bar, color=CLR_SL, lw=1.0, ls="--", alpha=0.8)
        ax0.text(mcd_bar + 1, 42, "MA CROSS DOWN", color=CLR_SL, fontsize=6.5)

    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "FILTER ONLY — state gates entry, does not set direction\n"
        "BLUE DOUBLE (<= 10): extreme squeeze, max coil — +2 pts\n"
        "BLUE (< 25): preparing for move — +1 pt\n"
        "MA CROSS UP: volatility expanding — +1 pt\n"
        "RED (>75): trend expanding — +1 pt | RED DOUBLE (>=90): watch exhaustion — +1 pt"
    )
    ax0.set_ylabel("BBWP %", fontsize=8)
    ax0.set_xlabel("Bars", fontsize=8)
    ax0.set_ylim(0, 105)
    ax0.set_xlim(0, n - 1)

    save_fig(fig, out_dir / "S9_bbwp_filter.png")


def build_s10(out_dir):
    """Build S10 - ATR SL 3-Phase Cloud Progression market-reading perspective."""
    n = 150
    title = "S10 - ATR SL 3-Phase | Cloud 2 cross=P1 | Cloud 3 cross=P2 | Cloud 3+4 sync=P3 trail"

    entry_bar = 20
    p1_bar    = 40
    p2_bar    = 75
    p3_bar    = 110

    price = shaped([
        (0, 1.000), (entry_bar, 1.015), (p1_bar, 1.040),
        (p2_bar, 1.075), (p3_bar, 1.105), (149, 1.130)
    ], n, noise=0.002)

    sl_p0_level = price[entry_bar] - 0.025
    sl_p1_level = price[entry_bar] - 0.015
    sl_p2_level = price[entry_bar] + 0.005
    sl_p3_base  = price[p3_bar] - 0.020
    tp_p0_level = price[entry_bar] + 0.050
    tp_p1_level = price[entry_bar] + 0.065
    tp_p2_level = price[entry_bar] + 0.080

    cloud2_delta = shaped_ind([
        (0, 45), (entry_bar, 48), (p1_bar - 3, 50), (p1_bar, 54),
        (60, 58), (p2_bar - 3, 60), (p2_bar, 63),
        (95, 65), (p3_bar, 67), (149, 68)
    ], n, noise=2)

    fig = plt.figure(figsize=(13, 9), facecolor=DARK_BG)
    gs = GridSpec(2, 1, figure=fig, hspace=0.08, height_ratios=[3.5, 1.5])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.3, label="Price")

    ax0.scatter(entry_bar, price[entry_bar] * 0.997, marker="^", color=CLR_TP, s=70, zorder=7)
    ax0.text(entry_bar + 1, price[entry_bar] * 0.994, "ENTRY", color=CLR_TP, fontsize=6.5)

    ax0.plot([entry_bar, p1_bar], [sl_p0_level, sl_p0_level],
             color=CLR_SL, lw=1.4, ls="-", label="SL P0 (solid red)")
    ax0.plot([entry_bar, p1_bar], [tp_p0_level, tp_p0_level],
             color=CLR_TP, lw=1.2, ls="-", label="TP P0 (solid green)")

    ax0.plot([p1_bar, p2_bar], [sl_p1_level, sl_p1_level],
             color=CLR_BE, lw=1.4, ls=":", label="SL P1 (dotted amber)")
    ax0.plot([p1_bar, p2_bar], [tp_p1_level, tp_p1_level],
             color=CLR_TP, lw=1.2, ls=":", label="TP P1 (dotted)")

    ax0.plot([p2_bar, p3_bar], [sl_p2_level, sl_p2_level],
             color=CLR_TRAIL, lw=1.4, ls="--", label="SL P2 (dashed purple)")
    ax0.plot([p2_bar, p3_bar], [tp_p2_level, tp_p2_level],
             color=CLR_TP, lw=1.2, ls="--", label="TP P2 (dashed)")

    sl_p3 = np.array([sl_p3_base + (price[i] - price[p3_bar]) * 0.7
                      if i >= p3_bar else np.nan for i in range(n)])
    ax0.plot(range(n), sl_p3, color="#facc15", lw=1.6, label="SL P3 (ATR trail, yellow)")

    phase_info = [
        (p1_bar, "C2 cross = P1", CLR_C2VIS),
        (p2_bar, "C3 cross = P2", CLR_EMA),
        (p3_bar, "C3+C4 sync = P3", CLR_MACRO),
    ]
    for bar, label, clr in phase_info:
        ax0.axvline(bar, color=clr, lw=1.0, ls=":", alpha=0.8)
        ax0.text(bar + 1, price[0] + 0.002, label, color=clr, fontsize=6.5)

    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=6.5, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD, ncol=2)
    annotate_box(ax0,
        "P0 (entry): SL = 2.5 ATR fixed | TP = target fixed\n"
        "P1 (Cloud 2 cross): SL tightens to closer level | TP expands\n"
        "P2 (Cloud 3 cross): SL moves to breakeven+ | TP expands further\n"
        "P3 (Cloud 3+4 sync): TP removed | SL = continuous ATR trail"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(cloud2_delta, color=CLR_C2VIS, lw=1.1, label="Cloud 2 delta (5-12)")
    ax1.axhline(50, color="#ffffff", lw=0.5, ls="--", alpha=0.25)
    ax1.fill_between(range(n), 50, cloud2_delta,
                     where=(cloud2_delta > 50), alpha=0.15, color=CLR_TP)
    for bar, label, clr in phase_info:
        ax1.axvline(bar, color=clr, lw=1.0, ls=":", alpha=0.8)
        ax1.text(bar + 1, 53, label[:2], color=clr, fontsize=6.5)
    ax1.text(2, 55, "Cloud 2 riding above midline = trend sustained", color=CLR_C2VIS, fontsize=6.5)
    ax1.set_ylabel("C2 Delta", fontsize=8)
    ax1.set_ylim(35, 75)
    ax1.set_xlabel("Bars", fontsize=8)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S10_atr_sl_phases.png")


def build_s11(out_dir):
    """Build S11 - AVWAP Confirmation with 3 simultaneous anchors and VSA events."""
    n = 140
    title = "S11 - AVWAP Confirmation | 3 anchors (swing high/low/vol event) + VSA events + quality score"

    price = shaped([
        (0, 1.100), (15, 1.070), (30, 1.040), (45, 1.025),
        (55, 1.020), (68, 1.045), (80, 1.070),
        (95, 1.055), (110, 1.085), (125, 1.070), (139, 1.095)
    ], n, noise=0.003)

    swing_high_anchor = 5
    swing_low_anchor  = 55
    vol_event_anchor  = 30

    avwap_from_high = sloped(swing_high_anchor, price[swing_high_anchor] - 0.005,
                             139, price[swing_high_anchor] - 0.010, n)
    for i in range(swing_high_anchor):
        avwap_from_high[i] = np.nan

    avwap_from_low = sloped(swing_low_anchor, price[swing_low_anchor] + 0.003,
                            139, price[swing_low_anchor] + 0.020, n)
    for i in range(swing_low_anchor):
        avwap_from_low[i] = np.nan

    avwap_from_vol = sloped(vol_event_anchor, price[vol_event_anchor] + 0.005,
                            139, price[vol_event_anchor] + 0.025, n)
    for i in range(vol_event_anchor):
        avwap_from_vol[i] = np.nan

    rng_v = np.random.default_rng(99)
    volume = np.clip(rng_v.normal(50, 20, n), 10, 100)
    volume[vol_event_anchor - 2:vol_event_anchor + 3] = np.clip(
        rng_v.normal(90, 5, 5), 80, 100)
    volume[swing_low_anchor - 2:swing_low_anchor + 2] = np.clip(
        rng_v.normal(85, 5, 4), 75, 100)

    vsa_events = {
        30:  ("SV", CLR_TP,   "Stopping Vol"),
        55:  ("SP", CLR_EMA,  "Spring"),
        80:  ("NS", CLR_SLOW, "No Supply"),
        110: ("UT", CLR_SL,   "Upthrust"),
    }

    quality_scores = [
        ("Swing Low (bar 55)",  85, CLR_TP),
        ("Vol Event (bar 30)",  55, CLR_BE),
        ("Swing High (bar 5)",  30, CLR_SL),
    ]

    fig = plt.figure(figsize=(12, 10), facecolor=DARK_BG)
    gs = GridSpec(3, 1, figure=fig, hspace=0.09, height_ratios=[3.5, 1.2, 1.5])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.plot(avwap_from_high, color=CLR_SL, lw=1.1, ls="--",
             label="AVWAP from swing HIGH (sellers)")
    ax0.plot(avwap_from_low, color=CLR_TP, lw=1.1, ls="-.",
             label="AVWAP from swing LOW (buyers)")
    ax0.plot(avwap_from_vol, color=CLR_TRAIL, lw=1.1, ls=":",
             label="AVWAP from vol event (institutions)")
    ax0.scatter(swing_high_anchor, price[swing_high_anchor],
                marker="v", color=CLR_SL, s=60, zorder=6)
    ax0.scatter(swing_low_anchor, price[swing_low_anchor],
                marker="^", color=CLR_TP, s=60, zorder=6)
    ax0.scatter(vol_event_anchor, price[vol_event_anchor],
                marker="D", color=CLR_TRAIL, s=50, zorder=6)
    for bar, (code, clr, _label) in vsa_events.items():
        ax0.scatter(bar, price[bar] * 0.996, marker="s", color=clr, s=45, zorder=7)
        ax0.text(bar, price[bar] * 0.992, code, color=clr, fontsize=6.5, ha="center")
    ax0.text(72, avwap_from_low[72] + 0.006, "Q=85 HIGH", color=CLR_TP, fontsize=6.5)
    ax0.text(50, avwap_from_vol[50] + 0.003, "Q=55 MED", color=CLR_TRAIL, fontsize=6.5)
    ax0.text(10, avwap_from_high[10] + 0.004, "Q=30 LOW", color=CLR_SL, fontsize=6.5)
    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "3 simultaneous AVWAPs — complementary views, not competing signals\n"
        "Price ABOVE AVWAP from swing LOW = buyers defending their level\n"
        "Price BELOW AVWAP from swing HIGH = sellers still at resistance\n"
        "Highest quality anchor (>=70, <50 bars) = best SL anchor for trade"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    vsa_thresh = 75
    vol_colors = [CLR_TP if v >= vsa_thresh else "#374151" for v in volume]
    ax1.bar(range(n), volume, color=vol_colors, alpha=0.8, width=1.0)
    ax1.axhline(vsa_thresh, color=CLR_DELTA, lw=0.8, ls="--", alpha=0.7,
                label="VSA ratio threshold")
    for bar in vsa_events:
        ax1.axvline(bar, color="#6b7280", lw=0.5, ls=":", alpha=0.5)
    ax1.text(2, 78, "High volume = institutional activity = anchor candidate", color=CLR_TP, fontsize=6.5)
    ax1.set_ylabel("Volume (rel.)", fontsize=8)
    ax1.set_ylim(0, 110)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2])
    style_ax(ax2)
    y_positions = [2, 1, 0]
    for pos, (label, score, clr) in zip(y_positions, quality_scores):
        ax2.barh(pos, score, color=clr, alpha=0.75, height=0.6)
        ax2.text(score + 1, pos, str(score), color=clr, va="center", fontsize=8, fontweight="bold")
        ax2.text(-2, pos, label, color="#9ca3af", va="center", ha="right", fontsize=7)
    ax2.axvline(70, color=CLR_TP, lw=1.0, ls="--", alpha=0.7, label="HIGH quality threshold (70)")
    ax2.axvline(40, color=CLR_BE, lw=0.8, ls=":", alpha=0.7, label="MEDIUM threshold (40)")
    ax2.fill_between([70, 100], [-0.4, -0.4], [2.4, 2.4], alpha=0.06, color=CLR_TP)
    ax2.fill_between([40, 70], [-0.4, -0.4], [2.4, 2.4], alpha=0.06, color=CLR_BE)
    ax2.fill_between([0, 40], [-0.4, -0.4], [2.4, 2.4], alpha=0.06, color=CLR_SL)
    ax2.text(72, 2.3, "HIGH", color=CLR_TP, fontsize=7)
    ax2.text(42, 2.3, "MED",  color=CLR_BE, fontsize=7)
    ax2.text(2,  2.3, "LOW",  color=CLR_SL, fontsize=7)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(-0.4, 2.7)
    ax2.set_yticks([])
    ax2.set_xlabel("Anchor Quality Score (0-100)", fontsize=8)
    ax2.set_ylabel("Anchors", fontsize=8)
    ax2.legend(loc="lower right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    save_fig(fig, out_dir / "S11_avwap_confirmation.png")


def main():
    """Render all 11 strategy perspective plots."""
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "results" / "strategy_perspectives"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Building strategy perspectives v2 (S1-S11)...")
    build_s1(out_dir)
    build_s2(out_dir)
    build_s3(out_dir)
    build_s4(out_dir)
    build_s5(out_dir)
    build_s6(out_dir)
    build_s7(out_dir)
    build_s8(out_dir)
    build_s9(out_dir)
    build_s10(out_dir)
    build_s11(out_dir)
    print("Done. Output: " + str(out_dir))


if __name__ == "__main__":
    main()

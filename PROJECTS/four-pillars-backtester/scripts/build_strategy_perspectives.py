"""
Build script: strategy market-reading perspectives.
Writes: scripts/visualize_strategy_perspectives.py
Run: python scripts/build_strategy_perspectives.py
Then: python scripts/visualize_strategy_perspectives.py
"""
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "scripts" / "visualize_strategy_perspectives.py"

# Check for existing file and version
if OUT.exists():
    stem = OUT.stem
    n = 2
    while True:
        candidate = OUT.parent / f"{stem}_v{n}.py"
        if not candidate.exists():
            OUT = candidate
            break
        n += 1

CONTENT = '''\
# -*- coding: utf-8 -*-
"""
Strategy Market-Reading Perspectives.
Visualizes how each strategy reads the market - what it senses, what states it waits for.
One figure per strategy. Each figure: price panel + indicator panels stacked.

Strategies:
  S1 - Strategy Bible (v3.3 era): Stoch 9/40/60 rotation + 55 EMA + divergence
  S2 - v3.7 Rebate Farming: Stoch 9 cycling fast, tight band, no bias
  S3 - v3.8 Directional: Cloud 3 filter + stoch zone exit + ATR expansion
  S4 - v3.8.3/v3.8.4 (current): 60-K pin + stoch 9 cycling + AVWAP SL
  S5 - 55/89 EMA Cross Scalp: EMA delta compression + 4 stochs joint state + TDI + BBW

Run: python scripts/visualize_strategy_perspectives.py
Output: results/strategy_perspectives/S1_bible.png ... S5_5589_scalp.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from pathlib import Path

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
DARK_BG   = "#0f1419"
DARK_CARD = "#1a1f26"
DARK_PANEL = "#141920"
CLR_PRICE  = "#e7e9ea"
CLR_SL     = "#ef4444"
CLR_BE     = "#f59e0b"
CLR_TRAIL  = "#8b5cf6"
CLR_TP     = "#10b981"
CLR_ENTRY  = "#6b7280"
CLR_FAST   = "#f97316"   # stoch 9 -orange
CLR_SLOW   = "#38bdf8"   # stoch 40/60 -sky blue
CLR_MACRO  = "#a78bfa"   # stoch 60 macro -violet
CLR_EMA    = "#22d3ee"   # EMA reference -cyan
CLR_TDI    = "#fb7185"   # TDI -rose
CLR_BBW    = "#4ade80"   # BBW -green
CLR_DELTA  = "#facc15"   # EMA delta -yellow
CLR_CLOUD  = "#1e3a5f"   # cloud fill
CLR_CLOUD2 = "#1e4a2f"   # cloud fill green

ZONE_HIGH = 80
ZONE_LOW  = 20

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def shaped(waypoints, n, noise=0.0015, seed=42):
    """Interpolate waypoints to smooth curve with noise."""
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
    """Apply dark theme to an axis."""
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


# ---------------------------------------------------------------------------
# S1 -Strategy Bible (v3.3 era)
# Market read: Stoch 60 macro above 80, Stoch 40 divergence, Stoch 9 cycle
#              55 EMA as support, AVWAP from low confirms buyers
# ---------------------------------------------------------------------------

def build_s1(out_dir):
    """Build S1 -Strategy Bible market-reading perspective."""
    n = 120
    title = "S1 -Strategy Bible (v3.3 era)\nMarket Read: 60-macro pin + 40-divergence + 9-cycle + 55 EMA"

    # Price: bull flag setup -slow grind up, stoch 9 dips, bounces off 55 EMA
    price = shaped([
        (0, 1.000), (15, 1.030), (25, 1.015), (35, 1.045),
        (50, 1.028), (60, 1.055), (75, 1.040), (90, 1.075),
        (110, 1.060), (119, 1.090)
    ], n, noise=0.003)

    # 55 EMA -rising support
    ema55 = sloped(0, 0.985, 119, 1.055, n)

    # AVWAP from low -also rising, slightly below price
    avwap = sloped(0, 0.978, 119, 1.048, n)

    # Stoch 9 -cycling fast: dips to oversold, bounces
    s9 = shaped_ind([
        (0, 55), (8, 18), (15, 72), (22, 15), (35, 80),
        (48, 12), (60, 78), (72, 14), (85, 76), (98, 12), (119, 65)
    ], n, noise=4)

    # Stoch 40 -stage divergence: Stage1 low, then higher low (stage 2)
    s40 = shaped_ind([
        (0, 48), (20, 22), (35, 55), (55, 18), (75, 52),
        (90, 28), (110, 60), (119, 62)
    ], n, noise=3)

    # Stoch 60 -macro: holding above 80 (bull flag condition)
    s60 = shaped_ind([
        (0, 82), (20, 85), (40, 81), (60, 84),
        (80, 82), (100, 86), (119, 83)
    ], n, noise=2)

    # Entry markers: stoch 9 exits oversold while 60 above 80
    entries = [10, 50, 74, 100]  # bar indices where 9 crosses back above 20

    fig = plt.figure(figsize=(12, 9), facecolor=DARK_BG)
    gs = GridSpec(4, 1, figure=fig, hspace=0.08,
                  height_ratios=[3, 1.2, 1.2, 1.2])

    # --- Price panel ---
    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.plot(ema55, color=CLR_EMA, lw=1.0, ls="--", label="EMA 55", alpha=0.8)
    ax0.plot(avwap, color=CLR_TRAIL, lw=0.9, ls="-.", label="AVWAP (from low)", alpha=0.7)
    ax0.fill_between(range(n), ema55, avwap,
                     where=(price >= ema55), alpha=0.06, color=CLR_CLOUD2)
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

    # --- Stoch 9 panel ---
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

    # --- Stoch 40 panel (divergence) ---
    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    ax2.plot(s40, color=CLR_SLOW, lw=1.1, label="Stoch 40 (divergence)")
    zone_fill(ax2, n)
    # Mark divergence: Stage 1 and Stage 2 lows
    stage1_bar, stage2_bar = 20, 55
    ax2.annotate("Stage 1", (stage1_bar, s40[stage1_bar]),
                 xytext=(stage1_bar + 3, s40[stage1_bar] + 12),
                 color="#facc15", fontsize=7,
                 arrowprops=dict(arrowstyle="->", color="#facc15", lw=0.8))
    ax2.annotate("Stage 2\n(higher low)", (stage2_bar, s40[stage2_bar]),
                 xytext=(stage2_bar + 3, s40[stage2_bar] + 12),
                 color="#facc15", fontsize=7,
                 arrowprops=dict(arrowstyle="->", color="#facc15", lw=0.8))
    ax2.set_ylabel("Stoch 40", fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    # --- Stoch 60 macro panel ---
    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    style_ax(ax3)
    ax3.plot(s60, color=CLR_MACRO, lw=1.1, label="Stoch 60 (macro filter)")
    ax3.axhline(80, color=CLR_SL, lw=0.6, ls="--", alpha=0.5)
    ax3.fill_between(range(n), 80, 100, alpha=0.1, color=CLR_MACRO)
    ax3.text(2, 82, "BULL MACRO ZONE -all entries allowed", color="#a78bfa",
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


# ---------------------------------------------------------------------------
# S2 -v3.7 Rebate Farming
# Market read: Stoch 9 cycling fast, no directional bias, tight band
#              Goal is volume generation, not trend capture
# ---------------------------------------------------------------------------

def build_s2(out_dir):
    """Build S2 -v3.7 Rebate Farming market-reading perspective."""
    n = 120
    title = "S2 -v3.7 Rebate Farming\nMarket Read: Stoch 9 fast cycling -direction irrelevant, volume is the goal"

    # Price: choppy sideways -the strategy doesn't care about direction
    price = shaped([
        (0, 1.000), (12, 1.018), (20, 0.992), (32, 1.015),
        (44, 0.988), (55, 1.012), (66, 0.990), (78, 1.014),
        (90, 0.985), (105, 1.010), (119, 0.995)
    ], n, noise=0.004)

    # Tight SL band around each entry (1 ATR)
    atr = 0.012
    sl_long = price - atr
    sl_short = price + atr
    tp_long = price + atr * 1.5
    tp_short = price - atr * 1.5

    # Stoch 9 -rapid cycling both ways
    s9 = shaped_ind([
        (0, 50), (8, 82), (14, 15), (22, 78), (30, 12),
        (38, 85), (46, 18), (54, 80), (62, 14), (70, 82),
        (78, 16), (86, 80), (94, 12), (102, 78), (110, 20), (119, 60)
    ], n, noise=4)

    # Entry bars: every cycle exit from zone
    long_entries = [16, 48, 80, 112]   # stoch 9 exits oversold
    short_entries = [10, 32, 54, 86]   # stoch 9 exits overbought

    fig = plt.figure(figsize=(12, 7), facecolor=DARK_BG)
    gs = GridSpec(2, 1, figure=fig, hspace=0.08, height_ratios=[3, 1.5])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")

    # Show tight SL/TP bands as translucent region
    ax0.fill_between(range(n), price - atr, price + atr,
                     alpha=0.08, color=CLR_BE, label="1 ATR band")

    for e in long_entries:
        ax0.scatter(e, price[e], marker="^", color=CLR_TP, s=45, zorder=5)
        # TP and SL lines for a few bars
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
        "NO DIRECTIONAL BIAS -longs and shorts equally valid\n"
        "TRIGGER: Stoch 9 exits oversold (long) or overbought (short)\n"
        "SL: 1.0 ATR | TP: 1.5 ATR -fixed at entry, no trailing\n"
        "GOAL: Volume = rebate income. Flat equity is fine."
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
    ax1.text(2, 85, "OVERBOUGHT -short entry on exit", color=CLR_SL, fontsize=6.5)
    ax1.text(2, 3, "OVERSOLD -long entry on exit", color=CLR_TP, fontsize=6.5)
    ax1.set_ylabel("Stoch 9", fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.set_xlabel("Bars", fontsize=8)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    plt.setp(ax0.get_xticklabels(), visible=False)

    save_fig(fig, out_dir / "S2_rebate_farming.png")


# ---------------------------------------------------------------------------
# S3 -v3.8 Directional Filter
# Market read: Cloud 3 (34/50) sets direction, ATR expanding, stoch zone exit
# ---------------------------------------------------------------------------

def build_s3(out_dir):
    """Build S3 -v3.8 directional filter market-reading perspective."""
    n = 120
    title = "S3 -v3.8 Directional Filter\nMarket Read: Cloud 3 bias + ATR expansion + stoch zone exit"

    # Price: clear uptrend -above rising Cloud 3
    price = shaped([
        (0, 1.000), (20, 1.040), (35, 1.025), (55, 1.070),
        (70, 1.055), (90, 1.095), (110, 1.080), (119, 1.110)
    ], n, noise=0.003)

    # Cloud 3 (34/50 EMA) -rising, price stays above it
    cloud3_top = sloped(0, 0.975, 119, 1.060, n)
    cloud3_bot = sloped(0, 0.960, 119, 1.042, n)

    # ATR: expanding during trend, slight pullbacks
    atr_vals = shaped_ind([
        (0, 30), (15, 45), (30, 35), (50, 55),
        (65, 42), (85, 60), (100, 48), (119, 58)
    ], n, noise=4)
    atr_actual = 0.010 + atr_vals / 1000  # rescale to price units

    # Stoch 9 -dips to oversold then exits (long-only since above Cloud 3)
    s9 = shaped_ind([
        (0, 55), (12, 15), (22, 72), (38, 12), (52, 68),
        (65, 18), (78, 70), (92, 14), (105, 65), (119, 55)
    ], n, noise=4)

    entries = [14, 40, 67, 94]  # stoch 9 exits oversold while above Cloud 3

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
        # Show ATR-based SL
        sl_level = price[e] - atr_actual[e] * 2.5
        be_level = price[e] + atr_actual[e] * 0.5
        ax0.plot([e, min(e + 20, n - 1)],
                 [sl_level, sl_level], color=CLR_SL, lw=0.8, ls="--", alpha=0.5)
        ax0.annotate("", (e + 3, be_level), (e + 3, price[e]),
                     arrowprops=dict(arrowstyle="->", color=CLR_BE, lw=0.8))

    # Shade region below Cloud 3 as "NO LONGS" zone
    ax0.fill_between(range(n), 0.94, cloud3_bot,
                     alpha=0.05, color=CLR_SL)
    ax0.text(2, 0.950, "SHORT-ONLY below Cloud 3", color=CLR_SL, fontsize=6.5)
    ax0.text(2, cloud3_top[5] + 0.004, "LONG-ONLY above Cloud 3", color=CLR_TP, fontsize=6.5)

    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "DIRECTION: Price vs Cloud 3 -ABOVE = long-only, BELOW = short-only\n"
        "TRIGGER: Stoch 9 exits oversold/overbought in allowed direction\n"
        "BE RAISE: ATR-based -profit > 0.5 ATR triggers SL to entry + 0.3 ATR\n"
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
    ax1.text(2, 3, "OVERSOLD -long entry on exit (Cloud 3 above = allowed)", color=CLR_TP, fontsize=6.5)
    ax1.set_ylabel("Stoch 9", fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)
    ax2.plot(atr_vals, color=CLR_BBW, lw=1.1, label="ATR (relative, expanding = trend)")
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


# ---------------------------------------------------------------------------
# S4 -v3.8.3 / v3.8.4 (current production)
# Market read: 60-K zone pin, stoch 9 cycling inside, AVWAP as dynamic floor
# ---------------------------------------------------------------------------

def build_s4(out_dir):
    """Build S4 -v3.8.3/v3.8.4 current production market-reading perspective."""
    n = 130
    title = "S4 -v3.8.3 / v3.8.4 (Current Production)\nMarket Read: 60-K macro pin + stoch 9 cycle + AVWAP dynamic floor"

    # Price: strong trend -60-K pinned above 80, stoch 9 dips and bounces
    price = shaped([
        (0, 1.000), (18, 1.050), (30, 1.030), (45, 1.075),
        (60, 1.055), (75, 1.090), (88, 1.070), (100, 1.100),
        (115, 1.085), (129, 1.115)
    ], n, noise=0.003)

    # AVWAP anchor from trade start -rising with price
    avwap_center = sloped(0, 0.988, 129, 1.090, n)
    avwap_2sig   = avwap_center - 0.018  # -2 sigma (SL level)

    # Stoch 9 -cycling rapidly inside the trend
    s9 = shaped_ind([
        (0, 60), (10, 14), (18, 75), (28, 12), (40, 78),
        (52, 16), (62, 72), (74, 14), (85, 76), (98, 12),
        (108, 70), (120, 15), (129, 68)
    ], n, noise=4)

    # Stoch 60 -pinned above 80 (the macro condition)
    s60 = shaped_ind([
        (0, 83), (20, 87), (40, 84), (60, 88),
        (80, 85), (100, 89), (120, 86), (129, 88)
    ], n, noise=1.5)

    # Grade A entries: 4/4 stochs aligned (where 9 exits oversold while 60 pinned)
    a_entries = [12, 53, 76, 110]
    # Phase transitions (bar 5 after entry = AVWAP SL kicks in)
    phase2_bars = [e + 5 for e in a_entries if e + 5 < n]

    fig = plt.figure(figsize=(12, 9), facecolor=DARK_BG)
    gs = GridSpec(3, 1, figure=fig, hspace=0.08, height_ratios=[3.5, 1.2, 1.2])

    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.plot(avwap_center, color=CLR_TRAIL, lw=1.0, ls="--",
             label="AVWAP center", alpha=0.8)
    ax0.plot(avwap_2sig, color=CLR_SL, lw=0.9, ls="-.",
             label="AVWAP -2 sigma (SL after bar 5)", alpha=0.7)
    ax0.fill_between(range(n), avwap_2sig, avwap_center,
                     alpha=0.06, color=CLR_TRAIL)

    for i, e in enumerate(a_entries):
        ax0.scatter(e, price[e] * 0.997, marker="^", color=CLR_TP, s=55, zorder=5,
                    label="A entry" if i == 0 else "")
        # Phase 1: ATR SL (first 5 bars)
        sl_p1 = price[e] - 0.025
        ax0.plot([e, min(e + 5, n - 1)],
                 [sl_p1, sl_p1], color=CLR_SL, lw=1.0, ls="--", alpha=0.6)
        # Phase 2 transition marker
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


# ---------------------------------------------------------------------------
# S5 -55/89 EMA Cross Scalp (research)
# Market read: EMA delta compression, 4 stochs joint state, TDI, BBW regime
# ---------------------------------------------------------------------------

def build_s5(out_dir):
    """Build S5 -55/89 EMA Cross Scalp market-reading perspective."""
    n = 140
    title = "S5 -55/89 EMA Cross Scalp (Research, not deployed)\nMarket Read: EMA delta compression + 4-stoch alignment + TDI + BBW regime"

    # Price: compression then breakout -EMA delta narrows then crosses
    price = shaped([
        (0, 1.000), (20, 1.012), (35, 1.006), (50, 1.014),
        (60, 1.008),  # compression zone -EMAs converge
        (65, 1.010),  # CROSS BAR
        (80, 1.035), (95, 1.025), (110, 1.048), (129, 1.040), (139, 1.055)
    ], n, noise=0.002)

    # EMA 55 and EMA 89 -converge then cross
    ema55 = shaped([
        (0, 0.998), (30, 1.006), (50, 1.009), (65, 1.012),
        (80, 1.028), (110, 1.042), (139, 1.052)
    ], n, noise=0.001)

    ema89 = shaped([
        (0, 0.994), (30, 1.002), (50, 1.008), (65, 1.011),
        (80, 1.022), (110, 1.035), (139, 1.046)
    ], n, noise=0.001)

    # EMA delta: narrows to zero at bar 65 then positive
    delta = shaped_ind([
        (0, 55), (20, 52), (40, 50.5), (60, 50.05),
        (65, 50),  # zero crossing
        (80, 52), (100, 54), (120, 55), (139, 56)
    ], n, noise=0.5)
    delta_rescaled = delta - 50  # center at zero for display

    # Stoch 9 -triggers MONITORING at bar ~40 (K/D cross)
    s9 = shaped_ind([
        (0, 45), (15, 18), (28, 60), (40, 22),  # K/D cross here
        (55, 65), (65, 55), (80, 72), (95, 18),
        (108, 65), (120, 14), (139, 60)
    ], n, noise=3)

    # Stoch 40 -alignment: TURNING+ state required
    s40 = shaped_ind([
        (0, 40), (20, 25), (40, 38), (55, 45),
        (65, 52), (80, 60), (100, 55), (120, 62), (139, 65)
    ], n, noise=3)

    # TDI (RSI-based momentum) -above signal line after cross
    tdi = shaped_ind([
        (0, 48), (20, 42), (40, 46), (55, 52),
        (65, 56), (80, 63), (100, 58), (120, 64), (139, 60)
    ], n, noise=2)
    tdi_signal = shaped_ind([
        (0, 50), (20, 46), (40, 47), (55, 50),
        (65, 53), (80, 59), (100, 56), (120, 61), (139, 58)
    ], n, noise=1)

    # BBW state -HEALTHY during compression, not QUIET
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
    signal_bar = 65

    fig = plt.figure(figsize=(13, 11), facecolor=DARK_BG)
    gs = GridSpec(5, 1, figure=fig, hspace=0.07,
                  height_ratios=[3, 1, 1, 1, 1])

    # --- Price + EMAs ---
    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)
    ax0.plot(price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.plot(ema55, color=CLR_EMA, lw=1.0, ls="--", label="EMA 55", alpha=0.9)
    ax0.plot(ema89, color=CLR_TRAIL, lw=1.0, ls="--", label="EMA 89", alpha=0.9)
    ax0.fill_between(range(n), ema55, ema89, alpha=0.12, color=CLR_DELTA)

    # Monitoring zone
    ax0.axvspan(monitoring_start, cross_bar, alpha=0.06, color=CLR_BE,
                label="MONITORING window")
    ax0.axvline(cross_bar, color=CLR_DELTA, lw=1.2, ls="--", alpha=0.8,
                label="EMA cross (signal)")
    ax0.scatter(signal_bar, price[signal_bar] * 0.997,
                marker="^", color=CLR_TP, s=70, zorder=6, label="LONG entry")

    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper left", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD, ncol=3)
    annotate_box(ax0,
        "STATE 1 (IDLE): waiting for stoch 9 K/D cross\n"
        "STATE 2 (MONITORING): stoch 9 crossed, checking full alignment:\n"
        "  - stoch 14 MOVING/EXTENDED  - stoch 40/60 TURNING+\n"
        "  - EMA delta compressing      - TDI above signal\n"
        "  - BBW not QUIET\n"
        "FIRE: EMA 55/89 cross while alignment holds"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, n - 1)

    # --- EMA Delta ---
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)
    ax1.plot(delta_rescaled, color=CLR_DELTA, lw=1.1, label="EMA delta (55-89)")
    ax1.axhline(0, color="#ffffff", lw=0.6, ls="--", alpha=0.4)
    ax1.fill_between(range(n), delta_rescaled, 0,
                     where=(np.array(delta_rescaled) >= 0), alpha=0.15, color=CLR_TP)
    ax1.fill_between(range(n), delta_rescaled, 0,
                     where=(np.array(delta_rescaled) < 0), alpha=0.15, color=CLR_SL)
    ax1.axvspan(monitoring_start, cross_bar, alpha=0.06, color=CLR_BE)
    ax1.axvline(cross_bar, color=CLR_DELTA, lw=0.8, ls="--", alpha=0.7)
    ax1.text(2, 4.5, "Delta compressing toward zero = EMAs converging", color=CLR_DELTA, fontsize=6.5)
    ax1.set_ylabel("Delta", fontsize=8)
    ax1.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    # --- Stoch 9 + 40 ---
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

    # --- TDI ---
    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    style_ax(ax3)
    ax3.plot(tdi, color=CLR_TDI, lw=1.0, label="TDI (RSI 9 smoothed)")
    ax3.plot(tdi_signal, color="#fca5a5", lw=0.8, ls="--", label="TDI signal")
    ax3.fill_between(range(n), tdi, tdi_signal,
                     where=(np.array(tdi) >= np.array(tdi_signal)),
                     alpha=0.12, color=CLR_TP, label="TDI above signal")
    ax3.axvline(cross_bar, color=CLR_DELTA, lw=0.8, ls="--", alpha=0.7)
    ax3.text(2, 40, "TDI above signal = momentum confirming", color=CLR_TP, fontsize=6.5)
    ax3.set_ylabel("TDI", fontsize=8)
    ax3.set_ylim(20, 80)
    ax3.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    # --- BBW regime ---
    ax4 = fig.add_subplot(gs[4], sharex=ax0)
    style_ax(ax4)
    ax4.plot(bbw, color=CLR_BBW, lw=1.0, label="BBW spectrum")
    ax4.plot(bbw_ma, color="#86efac", lw=0.8, ls="--", label="BBW MA (7)")
    ax4.fill_between(range(n), bbw, bbw_ma,
                     where=(np.array(bbw) >= np.array(bbw_ma)),
                     alpha=0.12, color=CLR_BBW, label="HEALTHY")
    ax4.fill_between(range(n), bbw, bbw_ma,
                     where=(np.array(bbw) < np.array(bbw_ma)),
                     alpha=0.12, color=CLR_SL, label="QUIET (blocked)")
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Render all strategy perspective plots."""
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "results" / "strategy_perspectives"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Building strategy perspectives...")
    build_s1(out_dir)
    build_s2(out_dir)
    build_s3(out_dir)
    build_s4(out_dir)
    build_s5(out_dir)
    print("Done. Output: " + str(out_dir))


if __name__ == "__main__":
    main()
'''

OUT.write_text(CONTENT, encoding="utf-8")
print("Written: " + str(OUT))

# Syntax check
try:
    py_compile.compile(str(OUT), doraise=True)
    print("SYNTAX OK: " + str(OUT))
except py_compile.PyCompileError as e:
    print("SYNTAX ERROR: " + str(e))
    sys.exit(1)

print()
print("Run with:")
print("  python " + str(OUT.relative_to(ROOT)))
print()
print("Output goes to:")
print("  results/strategy_perspectives/S1_bible.png")
print("  results/strategy_perspectives/S2_rebate_farming.png")
print("  results/strategy_perspectives/S3_v38_directional.png")
print("  results/strategy_perspectives/S4_v384_current.png")
print("  results/strategy_perspectives/S5_5589_scalp.png")

# -*- coding: utf-8 -*-
"""
V4 Strategy Layers - Perspective Visualizer.
Shows the four-layer signal pipeline for V4 strategy.
Layers: Macro Gate | Channel Gate | Two-Cycle Divergence | Cascade Gate

Run: python scripts/visualize_v4_layers.py
Output: results/strategy_perspectives/V4_four_layer_signal.png
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
CLR_TP     = "#10b981"
CLR_EMA    = "#22d3ee"
CLR_DELTA  = "#facc15"
CLR_S9     = "#22d3ee"
CLR_S40    = "#facc15"
CLR_S60    = "#e879f9"
CLR_CHAN   = "#38bdf8"

N       = 120
STAGE1  = 20
C1_ENTRY = 25
C1_EXIT  = 35
C2_ENTRY = 58
SIGNAL   = 78


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


def style_ax(ax):
    """Apply dark theme to axis."""
    ax.set_facecolor(DARK_PANEL)
    ax.tick_params(colors="#6b7280", labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#2d3748")
    ax.yaxis.label.set_color("#9ca3af")
    ax.xaxis.label.set_color("#9ca3af")


def style_twin(ax):
    """Apply dark theme tick/label styling to a twinx axis."""
    ax.tick_params(colors="#6b7280", labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#2d3748")
    ax.yaxis.label.set_color("#9ca3af")


def save_fig(fig, path):
    """Save figure with dark background and print absolute path."""
    fig.savefig(path, dpi=130, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)
    print("Saved: " + str(path.resolve()))


def annotate_box(ax, text, x=0.02, y=0.97):
    """Add annotated description box top-left of axis."""
    ax.text(x, y, text, transform=ax.transAxes,
            va="top", ha="left", fontsize=7,
            family="monospace",
            color="#e7e9ea",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a2433",
                      edgecolor="#374151", alpha=0.9))


def build_synthetic_data():
    """Build all synthetic data arrays for the perfect V4 signal scenario."""
    # Reversal pullback: price declining from highs, two oversold cycles form bottom
    price = shaped([
        (0, 1.090), (10, 1.077), (20, 1.063),
        (28, 1.060), (C1_ENTRY, 1.056), (C1_ENTRY + 5, 1.053), (C1_EXIT, 1.058),
        (48, 1.055), (55, 1.053),
        (C2_ENTRY, 1.050), (C2_ENTRY + 6, 1.048), (SIGNAL - 3, 1.049), (SIGNAL, 1.051),
        (85, 1.059), (100, 1.071), (119, 1.082)
    ], N, noise=0.0008, seed=42)

    # Channel band follows price decline from bar 0-STAGE1
    chan_top = np.full(N, np.nan)
    chan_bot = np.full(N, np.nan)
    for i in range(STAGE1 + 1):
        t = i / max(STAGE1, 1)
        mid = 1.090 - t * 0.027
        chan_top[i] = mid + 0.004
        chan_bot[i] = mid - 0.004

    # stoch_9: two oversold cycles during the pullback, classic divergence pattern
    s9 = shaped_ind([
        (0, 62), (10, 55), (18, 38),
        (C1_ENTRY, 20), (C1_ENTRY + 4, 18), (C1_EXIT, 30),
        (42, 52), (48, 48),
        (C2_ENTRY, 24), (C2_ENTRY + 6, 22), (SIGNAL - 2, 24), (SIGNAL, 28),
        (85, 50), (100, 58), (119, 62)
    ], N, noise=1.5, seed=10)
    s9 = np.clip(s9, 0, 100)

    # stoch_40: starts elevated, declines with pullback, recovers at cascade gate
    s40 = shaped_ind([
        (0, 62), (15, 52), (C1_ENTRY, 38), (C1_EXIT, 30),
        (45, 32), (55, 28), (C2_ENTRY, 22),
        (70, 26), (SIGNAL, 34),
        (85, 42), (100, 50), (119, 58)
    ], N, noise=1.5, seed=20)
    s40 = np.clip(s40, 0, 100)

    # stoch_60: slowest stochastic — declines into oversold during pullback,
    # still deep in oversold at signal time. Will exit last in the cascade.
    s60 = shaped_ind([
        (0, 58), (10, 50), (20, 42), (30, 34), (40, 27),
        (50, 22), (60, 18), (70, 16), (SIGNAL, 15),
        (85, 17), (95, 22), (105, 28), (119, 35)
    ], N, noise=0.8, seed=30)

    r_sq = np.full(N, np.nan)
    slope_arr = np.full(N, np.nan)
    for i in range(STAGE1 + 1):
        r_sq[i] = 0.72
        slope_arr[i] = -0.0015

    return price, chan_top, chan_bot, s9, s40, s60, r_sq, slope_arr


def build_gate_status(s9, s40, s60):
    """Compute gate pass/fail status arrays for each of the four layers."""
    # Macro gate is an external filter (not stochastic-based); passes throughout
    gate_macro = np.ones(N)

    gate_channel = np.zeros(N)
    gate_channel[STAGE1:] = 1.0

    gate_div = np.zeros(N)
    gate_div[C1_ENTRY:SIGNAL] = 0.5
    gate_div[SIGNAL:] = 1.0

    gate_cascade = np.zeros(N)
    gate_cascade[SIGNAL:] = 1.0

    return gate_macro, gate_channel, gate_div, gate_cascade


def main():
    """Render V4 four-layer signal pipeline perspective and save PNG."""
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "results" / "strategy_perspectives"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "V4_four_layer_signal.png"

    price, chan_top, chan_bot, s9, s40, s60, r_sq, slope_arr = build_synthetic_data()
    gate_macro, gate_channel, gate_div, gate_cascade = build_gate_status(s9, s40, s60)

    bars = np.arange(N)

    c1_stoch_low = float(np.nanmin(s9[C1_ENTRY:C1_EXIT + 1]))
    c2_stoch_low = float(np.nanmin(s9[C2_ENTRY:SIGNAL + 1]))
    c1_bar_low = int(C1_ENTRY + int(np.nanargmin(s9[C1_ENTRY:C1_EXIT + 1])))
    c2_bar_low = int(C2_ENTRY + int(np.nanargmin(s9[C2_ENTRY:SIGNAL + 1])))

    c1_price_low = float(np.nanmin(price[C1_ENTRY:C1_EXIT + 1]))
    c2_price_low = float(np.nanmin(price[C2_ENTRY:SIGNAL + 1]))

    title = "V4 Four-Layer Signal Pipeline | Macro Gate + Channel Gate + Two-Cycle Divergence + Cascade Gate"

    fig = plt.figure(figsize=(16, 20), facecolor=DARK_BG)
    gs = GridSpec(7, 1, figure=fig, hspace=0.07,
                  height_ratios=[3, 1.5, 1.2, 1.2, 1.2, 1.2, 0.7])

    # ------------------------------------------------------------------
    # Panel 0: Price + regression channel band + entry markers
    # ------------------------------------------------------------------
    ax0 = fig.add_subplot(gs[0])
    style_ax(ax0)

    ax0.plot(bars, price, color=CLR_PRICE, lw=1.2, label="Price")
    ax0.fill_between(bars, chan_bot, chan_top,
                     where=~np.isnan(chan_bot), alpha=0.20, color=CLR_EMA,
                     label="Regression channel (bars 0-20)")
    ax0.plot(bars, chan_top, color=CLR_EMA, lw=0.6, ls="--", alpha=0.5)
    ax0.plot(bars, chan_bot, color=CLR_EMA, lw=0.6, ls="--", alpha=0.5)

    ax0.axhline(c1_price_low,
                xmin=C1_ENTRY / (N - 1), xmax=(C1_EXIT + 2) / (N - 1),
                color=CLR_CHAN, lw=0.9, ls=":", alpha=0.8)
    ax0.axhline(c2_price_low,
                xmin=C2_ENTRY / (N - 1), xmax=(SIGNAL + 2) / (N - 1),
                color=CLR_CHAN, lw=0.9, ls=":", alpha=0.8)
    ax0.text(C1_ENTRY + 0.5, c1_price_low + 0.0005,
             "price_low_c1", color=CLR_CHAN, fontsize=6, va="bottom")
    ax0.text(C2_ENTRY + 0.5, c2_price_low - 0.0012,
             "price_low_c2 (lower)", color=CLR_CHAN, fontsize=6, va="top")

    for bar, label, clr in [
        (C1_ENTRY, "C1 entry", "#f97316"),
        (C1_EXIT,  "C1 exit",  "#f97316"),
        (C2_ENTRY, "C2 entry", "#f97316"),
    ]:
        ax0.axvline(bar, color=clr, lw=0.8, ls="--", alpha=0.65)
        ax0.text(bar + 0.6, 1.093, label, color=clr, fontsize=6.5,
                 rotation=90, va="top")

    ax0.axvline(STAGE1, color="#4b5563", lw=0.8, ls=":", alpha=0.6)
    ax0.text(STAGE1 + 0.6, 1.093, "Stage 1", color="#4b5563", fontsize=6.5,
             rotation=90, va="top")

    ax0.scatter(SIGNAL, price[SIGNAL] * 0.9988, marker="^",
                color=CLR_TP, s=100, zorder=7, label="ENTRY (signal bar)")
    ax0.axvline(SIGNAL, color=CLR_TP, lw=1.0, ls="--", alpha=0.7)
    ax0.text(SIGNAL + 0.6, 1.045, "ENTRY", color=CLR_TP, fontsize=7,
             fontweight="bold", rotation=90, va="bottom")

    ax0.set_title(title, color="#e7e9ea", fontsize=9, pad=6)
    ax0.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)
    annotate_box(ax0,
        "LAYER 1 — MACRO GATE: external macro filter (not stochastic-based)\n"
        "LAYER 2 — CHANNEL GATE: 20-bar pre-Stage1 regression: R2 > 0.45, slope < -0.1%/bar\n"
        "  Rejects V-bottoms (low R2) and chop (flat slope). Runs ONCE at Stage 1 entry.\n"
        "LAYER 3 — DIVERGENCE: price LL + stoch_9 HL across two oversold cycles\n"
        "  State: IDLE -> CYCLE_1 -> COOLDOWN -> CYCLE_2 -> SIGNAL (or reset)\n"
        "LAYER 4 — CASCADE: stoch_40 >= 30 at Cycle 2 exit (medium stoch recovering)\n"
        "  Cascade order: stoch_9 -> stoch_40 -> stoch_60 (slowest, still in oversold)\n"
        "SIGNAL: All 4 layers green at Cycle 2 stoch_9 exit above 25"
    )
    ax0.set_ylabel("Price", fontsize=8)
    ax0.set_xlim(0, N - 1)
    ax0.set_ylim(1.043, 1.098)

    # ------------------------------------------------------------------
    # Panel 1: stoch_9 with state machine markers
    # ------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    style_ax(ax1)

    ax1.axvspan(C1_ENTRY, C1_EXIT,  alpha=0.12, color="#f97316", label="CYCLE_1")
    ax1.axvspan(C1_EXIT,  C2_ENTRY, alpha=0.07, color=CLR_BE,   label="COOLDOWN")
    ax1.axvspan(C2_ENTRY, SIGNAL,   alpha=0.12, color=CLR_S40,  label="CYCLE_2")

    ax1.plot(bars, s9, color=CLR_S9, lw=1.3, label="stoch_9", zorder=4)
    ax1.axhline(25, color=CLR_SL, lw=0.8, ls="--", alpha=0.65, label="25 (oversold threshold)")
    ax1.axhline(40, color=CLR_BE, lw=0.6, ls=":",  alpha=0.50, label="40 (cooldown recovery)")
    ax1.fill_between(bars, 0, 25, alpha=0.07, color=CLR_SL)

    ax1.scatter(c1_bar_low, c1_stoch_low, marker="v", color="#f97316", s=55, zorder=6)
    ax1.scatter(c2_bar_low, c2_stoch_low, marker="v", color=CLR_S40,  s=55, zorder=6)

    ax1.text(c1_bar_low + 1, c1_stoch_low + 3,
             "stoch_low_c1 =" + " " + str(round(c1_stoch_low, 1)),
             color="#f97316", fontsize=6)
    ax1.text(c2_bar_low + 1, c2_stoch_low + 3,
             "stoch_low_c2 =" + " " + str(round(c2_stoch_low, 1)) + " (higher = divergence)",
             color=CLR_S40, fontsize=6)

    ax1.text((C1_ENTRY + C1_EXIT) / 2, 88, "CYCLE_1",
             color="#f97316", fontsize=6.5, ha="center")
    ax1.text((C1_EXIT + C2_ENTRY) / 2, 88, "COOLDOWN",
             color=CLR_BE, fontsize=6.5, ha="center")
    ax1.text((C2_ENTRY + SIGNAL) / 2, 88, "CYCLE_2",
             color=CLR_S40, fontsize=6.5, ha="center")
    ax1.text(SIGNAL + 1, 35, "SIGNAL", color=CLR_TP, fontsize=6.5)

    ax1.axvline(SIGNAL, color=CLR_TP, lw=0.8, ls="--", alpha=0.6)
    ax1.set_ylabel("stoch_9", fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.legend(loc="upper left", fontsize=6, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD, ncol=3)

    # ------------------------------------------------------------------
    # Panel 2: stoch_40 with cascade gate threshold
    # ------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    style_ax(ax2)

    ax2.plot(bars, s40, color=CLR_S40, lw=1.2, label="stoch_40 (medium)")
    ax2.axhline(30, color=CLR_TP, lw=0.8, ls="--", alpha=0.7,
                label="30 (cascade gate threshold)")
    ax2.fill_between(bars, 0, 30, alpha=0.07, color=CLR_SL)
    ax2.fill_between(bars[SIGNAL:], 30, s40[SIGNAL:],
                     where=(s40[SIGNAL:] >= 30),
                     alpha=0.12, color=CLR_TP)

    cascade_val = float(s40[SIGNAL])
    ax2.scatter(SIGNAL, cascade_val, marker="o",
                color=CLR_TP, s=70, zorder=6, label="CASCADE PASS at signal bar")
    ax2.text(SIGNAL + 1, cascade_val + 1.5,
             "CASCADE PASS\nstoch_40 = " + str(round(cascade_val, 1)) + " (>= 30)",
             color=CLR_TP, fontsize=6)
    ax2.text(2, 32, "stoch_40 recovering ahead of stoch_60 = cascade cascade confirmed",
             color=CLR_S40, fontsize=6.5)
    ax2.axvline(SIGNAL, color=CLR_TP, lw=0.8, ls="--", alpha=0.6)
    ax2.set_ylabel("stoch_40", fontsize=8)
    ax2.set_ylim(0, 65)
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    # ------------------------------------------------------------------
    # Panel 3: stoch_60 — slowest stochastic, cascade position
    # ------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    style_ax(ax3)

    ax3.plot(bars, s60, color=CLR_S60, lw=1.2, label="stoch_60 (slowest)")
    ax3.axhline(40, color="#6b7280", lw=0.7, ls=":", alpha=0.5,
                label="40 (oversold reference)")
    ax3.fill_between(bars, 0, 40, alpha=0.07, color=CLR_SL,
                     label="Oversold zone")
    ax3.fill_between(bars, 0, s60, where=(s60 < 40), alpha=0.12, color=CLR_S60)
    ax3.text(2, 52, "Cascade order: stoch_9 exits first -> stoch_40 follows -> stoch_60 last",
             color=CLR_S60, fontsize=6.5)
    ax3.text(SIGNAL + 1, s60[SIGNAL] + 2,
             "Still in oversold at signal\n(slowest — will exit last)",
             color=CLR_S60, fontsize=6)
    ax3.axvline(SIGNAL, color=CLR_TP, lw=0.8, ls="--", alpha=0.6)
    ax3.set_ylabel("stoch_60", fontsize=8)
    ax3.set_ylim(0, 65)
    ax3.legend(loc="upper right", fontsize=7, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    # ------------------------------------------------------------------
    # Panel 4: Channel gate — R-squared and slope_pct (dual axis, bars 0-20)
    # ------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[4], sharex=ax0)
    style_ax(ax4)

    valid = bars[:STAGE1 + 1]
    ax4.plot(valid, r_sq[:STAGE1 + 1], color=CLR_EMA, lw=1.4,
             label="R-squared (fit quality)")
    ax4.axhline(0.45, color=CLR_EMA, lw=0.7, ls="--", alpha=0.6,
                label="R2 = 0.45 threshold")
    ax4.fill_between(valid, 0.45, r_sq[:STAGE1 + 1], alpha=0.12, color=CLR_EMA)
    ax4.text(2, 0.62, "R2 = 0.72 (orderly decline confirmed)", color=CLR_EMA, fontsize=6.5)
    ax4.axvline(STAGE1, color="#4b5563", lw=0.8, ls=":", alpha=0.6)
    ax4.text(STAGE1 + 0.6, 0.88, "Gate stored at Stage 1", color="#4b5563", fontsize=6.5,
             rotation=90, va="top")

    ax4b = ax4.twinx()
    ax4b.set_facecolor("none")
    style_twin(ax4b)
    ax4b.plot(valid, slope_arr[:STAGE1 + 1], color=CLR_DELTA, lw=1.2, ls="--",
              label="slope_pct (trend direction)")
    ax4b.axhline(-0.001, color=CLR_DELTA, lw=0.6, ls=":", alpha=0.6,
                 label="slope = -0.001 threshold")
    ax4b.fill_between(valid, -0.001, slope_arr[:STAGE1 + 1], alpha=0.10, color=CLR_DELTA)
    ax4b.text(2, -0.00175, "slope_pct = -0.0015 (< -0.001 threshold)",
              color=CLR_DELTA, fontsize=6.5)
    ax4b.set_ylim(-0.0025, 0.0005)
    ax4b.set_ylabel("slope_pct", fontsize=7, color=CLR_DELTA)

    ax4.set_ylabel("R-squared", fontsize=8)
    ax4.set_ylim(0.0, 1.05)
    lines4a, labs4a = ax4.get_legend_handles_labels()
    lines4b, labs4b = ax4b.get_legend_handles_labels()
    ax4.legend(lines4a + lines4b, labs4a + labs4b,
               loc="lower right", fontsize=6.5, framealpha=0.3,
               labelcolor="#e7e9ea", facecolor=DARK_CARD)

    # ------------------------------------------------------------------
    # Panel 5: Gate status bars — one row per layer across time
    # ------------------------------------------------------------------
    ax5 = fig.add_subplot(gs[5], sharex=ax0)
    style_ax(ax5)

    bar_h = 0.18
    bottoms   = [0.75, 0.50, 0.25, 0.00]
    gates     = [gate_macro, gate_channel, gate_div, gate_cascade]
    for bot, gate in zip(bottoms, gates):
        clrs = []
        for v in gate:
            if v >= 1.0:
                clrs.append(CLR_TP)
            elif v > 0:
                clrs.append(CLR_BE)
            else:
                clrs.append("#374151")
        ax5.bar(bars, np.ones(N) * bar_h, bottom=np.ones(N) * bot,
                color=clrs, alpha=0.85, width=1.0)

    ax5.set_yticks([0.09, 0.34, 0.59, 0.84])
    ax5.set_yticklabels(["L4 Cascade", "L3 Diverge", "L2 Channel", "L1 Macro"],
                        fontsize=6.5)
    ax5.tick_params(axis="y", colors="#9ca3af")
    ax5.set_ylim(0.0, 1.0)
    ax5.axvline(SIGNAL, color=CLR_TP, lw=0.8, ls="--", alpha=0.6)
    ax5.text(SIGNAL + 1, 0.91, "ALL PASS", color=CLR_TP, fontsize=7, fontweight="bold")

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=CLR_TP,   alpha=0.85, label="PASS"),
        plt.Rectangle((0, 0), 1, 1, color=CLR_BE,   alpha=0.85, label="IN PROGRESS"),
        plt.Rectangle((0, 0), 1, 1, color="#374151", alpha=0.85, label="WAITING"),
    ]
    ax5.legend(handles=legend_handles, loc="upper left", fontsize=7,
               framealpha=0.3, labelcolor="#e7e9ea", facecolor=DARK_CARD)
    ax5.set_ylabel("Gate Status", fontsize=8)

    # ------------------------------------------------------------------
    # Panel 6: Entry signal bar (spike at SIGNAL bar only)
    # ------------------------------------------------------------------
    ax6 = fig.add_subplot(gs[6], sharex=ax0)
    style_ax(ax6)

    signal_arr = np.zeros(N)
    signal_arr[SIGNAL] = 1.0
    clrs6 = [CLR_TP if v > 0 else "#374151" for v in signal_arr]
    ax6.bar(bars, signal_arr, color=clrs6, alpha=0.90, width=1.0)
    ax6.set_ylim(0, 1.5)
    ax6.set_yticks([])
    ax6.set_ylabel("SIGNAL", fontsize=8)
    ax6.set_xlabel("Bars", fontsize=8)
    ax6.text(SIGNAL + 1, 1.08, "FIRE", color=CLR_TP, fontsize=7, fontweight="bold")

    for ax in [ax0, ax1, ax2, ax3, ax4, ax5]:
        plt.setp(ax.get_xticklabels(), visible=False)

    xticks = list(range(0, N, 20))
    ax6.set_xticks(xticks)

    save_fig(fig, out_path)


if __name__ == "__main__":
    main()

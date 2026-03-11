# -*- coding: utf-8 -*-
"""
V4 Scenario Map -- All Possible Signal Paths.
Shows 7 scenarios covering every outcome of the V4 four-layer pipeline.
Layout: decision tree header + 4x2 grid of scenario cells + legend.

Run: python scripts/visualize_v4_scenario_map.py
Output: results/strategy_perspectives/V4_scenario_map.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

# -- Theme -----------------------------------------------------------
DARK_BG    = "#0f1419"
DARK_CARD  = "#1a1f26"
DARK_PANEL = "#141920"
CLR_PRICE  = "#e7e9ea"
CLR_SL     = "#ef4444"
CLR_BE     = "#f59e0b"
CLR_TP     = "#10b981"
CLR_S9     = "#22d3ee"
CLR_S40    = "#facc15"
CLR_S60    = "#e879f9"
CLR_CHAN   = "#38bdf8"
CLR_DIMMED = "#4b5563"
CLR_GATE_NONE = "#1e2530"

# -- Scenario timing (80 bars) --------------------------------------
N_SC     = 80
STAGE1   = 15
C1_ENTRY = 18
C1_EXIT  = 28
C2_ENTRY = 42
SIGNAL   = 58


# ====================================================================
# Helpers
# ====================================================================

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
    ax.tick_params(colors="#6b7280", labelsize=6)
    for spine in ax.spines.values():
        spine.set_color("#2d3748")
    ax.yaxis.label.set_color("#9ca3af")
    ax.xaxis.label.set_color("#9ca3af")


def save_fig(fig, path):
    """Save figure with dark background and print absolute path."""
    fig.savefig(path, dpi=130, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)
    print("Saved: " + str(path.resolve()))


def annotate_box(ax, text, x=0.02, y=0.95):
    """Add annotated description box."""
    ax.text(x, y, text, transform=ax.transAxes,
            va="top", ha="left", fontsize=5.5,
            family="monospace", color="#e7e9ea",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a2433",
                      edgecolor="#374151", alpha=0.9))


def render_gate_strip(ax, gate_statuses):
    """Render 4-layer gate status strip.

    gate_statuses: list of 4 strings: 'pass', 'fail', or 'none'
    """
    style_ax(ax)
    positions = np.arange(4)
    colors = []
    for s in gate_statuses:
        if s == "pass":
            colors.append(CLR_TP)
        elif s == "fail":
            colors.append(CLR_SL)
        else:
            colors.append(CLR_GATE_NONE)
    ax.barh(positions, [1] * 4, height=0.6, color=colors, alpha=0.85,
            edgecolor="#2d3748", linewidth=0.5)
    ax.set_yticks(positions)
    ax.set_yticklabels(["L1", "L2", "L3", "L4"], fontsize=5)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_ylim(-0.5, 3.5)
    ax.invert_yaxis()


# ====================================================================
# Scenario renderers
# ====================================================================

def render_s1(ax_p, ax_i, ax_g):
    """S1: ALL PASS -- Signal fires."""
    bars = np.arange(N_SC)

    price = shaped([
        (0, 1.090), (8, 1.078), (STAGE1, 1.065),
        (C1_ENTRY, 1.058), (C1_ENTRY + 5, 1.055), (C1_EXIT, 1.060),
        (38, 1.057), (C2_ENTRY, 1.052), (C2_ENTRY + 6, 1.050),
        (SIGNAL, 1.053), (65, 1.062), (79, 1.075)
    ], N_SC, noise=0.0008, seed=42)

    s9 = shaped_ind([
        (0, 60), (10, 40), (C1_ENTRY, 20), (C1_ENTRY + 5, 16),
        (C1_EXIT, 32), (35, 50), (C2_ENTRY, 22), (C2_ENTRY + 6, 20),
        (SIGNAL, 30), (65, 55), (79, 60)
    ], N_SC, noise=1.5, seed=10)

    # -- Price panel --
    style_ax(ax_p)
    ax_p.plot(bars, price, color=CLR_PRICE, lw=1.0)
    ax_p.scatter(SIGNAL, price[SIGNAL], marker="^", color=CLR_TP, s=60, zorder=6)
    ax_p.axvline(SIGNAL, color=CLR_TP, lw=0.7, ls="--", alpha=0.5)
    for bar in [C1_ENTRY, C1_EXIT, C2_ENTRY]:
        ax_p.axvline(bar, color="#f97316", lw=0.5, ls=":", alpha=0.4)
    ax_p.set_title("S1: ALL PASS", color=CLR_TP, fontsize=8,
                   fontweight="bold", pad=3)
    annotate_box(ax_p, "All 4 layers PASS\nSignal fires at bar " + str(SIGNAL))
    ax_p.set_xlim(0, N_SC - 1)
    plt.setp(ax_p.get_xticklabels(), visible=False)

    # -- Indicator panel: stoch_9 with divergence --
    style_ax(ax_i)
    ax_i.plot(bars, s9, color=CLR_S9, lw=1.0)
    ax_i.axhline(25, color=CLR_SL, lw=0.6, ls="--", alpha=0.5)
    ax_i.fill_between(bars, 0, 25, alpha=0.06, color=CLR_SL)

    c1_low_idx = int(C1_ENTRY + np.argmin(s9[C1_ENTRY:C1_EXIT + 1]))
    c2_low_idx = int(C2_ENTRY + np.argmin(s9[C2_ENTRY:SIGNAL + 1]))
    ax_i.scatter(c1_low_idx, s9[c1_low_idx], marker="v",
                 color="#f97316", s=25, zorder=6)
    ax_i.scatter(c2_low_idx, s9[c2_low_idx], marker="v",
                 color=CLR_S40, s=25, zorder=6)

    # Divergence arrow (HL = higher low)
    ax_i.annotate("", xy=(c2_low_idx, s9[c2_low_idx] + 1),
                  xytext=(c1_low_idx, s9[c1_low_idx] + 1),
                  arrowprops=dict(arrowstyle="->", color=CLR_TP, lw=1.5))
    mid_x = (c1_low_idx + c2_low_idx) / 2
    mid_y = max(float(s9[c1_low_idx]), float(s9[c2_low_idx])) + 7
    ax_i.text(mid_x, mid_y, "HL", color=CLR_TP, fontsize=7,
              ha="center", fontweight="bold")

    ax_i.set_ylim(0, 80)
    ax_i.set_ylabel("stoch_9", fontsize=6)
    ax_i.axvline(SIGNAL, color=CLR_TP, lw=0.7, ls="--", alpha=0.5)
    plt.setp(ax_i.get_xticklabels(), visible=False)

    # -- Gate strip --
    render_gate_strip(ax_g, ["pass", "pass", "pass", "pass"])


def render_s2(ax_p, ax_i, ax_g):
    """S2: MACRO FAIL -- External filter rejects."""
    bars = np.arange(N_SC)

    price = shaped([
        (0, 1.060), (20, 1.048), (40, 1.042),
        (55, 1.045), (70, 1.058), (79, 1.065)
    ], N_SC, noise=0.001, seed=50)

    # -- Price panel (dimmed) --
    style_ax(ax_p)
    ax_p.plot(bars, price, color=CLR_DIMMED, lw=0.8, alpha=0.5)
    ax_p.set_title("S2: MACRO FAIL", color=CLR_SL, fontsize=8,
                   fontweight="bold", pad=3)
    annotate_box(ax_p, "External macro filter\nrejects entry")
    ax_p.set_xlim(0, N_SC - 1)
    plt.setp(ax_p.get_xticklabels(), visible=False)

    # -- Indicator panel: BLOCKED --
    style_ax(ax_i)
    ax_i.text(0.5, 0.5, "MACRO GATE\nBLOCKED", transform=ax_i.transAxes,
              ha="center", va="center", fontsize=11, fontweight="bold",
              color=CLR_SL, alpha=0.7,
              bbox=dict(boxstyle="round,pad=0.5", facecolor=DARK_CARD,
                        edgecolor=CLR_SL, alpha=0.5))
    ax_i.set_xticks([])
    ax_i.set_yticks([])

    # -- Gate strip --
    render_gate_strip(ax_g, ["fail", "none", "none", "none"])


def render_s3(ax_p, ax_i, ax_g):
    """S3: CHANNEL FAIL -- V-bottom (chaotic price, low R-squared)."""
    bars = np.arange(N_SC)

    price = shaped([
        (0, 1.085), (4, 1.070), (7, 1.082), (10, 1.058),
        (13, 1.072), (STAGE1, 1.045),
        (25, 1.055), (40, 1.050), (60, 1.048), (79, 1.055)
    ], N_SC, noise=0.003, seed=60)

    # Bad regression line
    t_reg = np.arange(STAGE1 + 1, dtype=float)
    reg_line = 1.085 - (t_reg / STAGE1) * 0.040

    # -- Price panel --
    style_ax(ax_p)
    ax_p.plot(bars, price, color=CLR_PRICE, lw=1.0)
    ax_p.plot(t_reg, reg_line, color=CLR_SL, lw=1.0, ls="--", alpha=0.7)
    ax_p.axvline(STAGE1, color="#4b5563", lw=0.6, ls=":", alpha=0.5)
    ax_p.set_title("S3: CHANNEL FAIL", color=CLR_SL, fontsize=8,
                   fontweight="bold", pad=3)
    annotate_box(ax_p, "V-bottom: chaotic price\nR-sq = 0.22 (< 0.45)")
    ax_p.set_xlim(0, N_SC - 1)
    plt.setp(ax_p.get_xticklabels(), visible=False)

    # -- Indicator panel: R-squared gauge --
    style_ax(ax_i)
    ax_i.barh([0], [0.22], height=0.4, color=CLR_SL, alpha=0.7)
    ax_i.axvline(0.45, color=CLR_TP, lw=1.2, ls="--", alpha=0.8)
    ax_i.text(0.11, 0, "0.22", color="#e7e9ea", fontsize=8,
              va="center", ha="center", fontweight="bold")
    ax_i.text(0.47, 0.25, "0.45", color=CLR_TP, fontsize=6, va="bottom")
    ax_i.set_xlim(0, 1.0)
    ax_i.set_ylim(-0.5, 0.5)
    ax_i.set_yticks([])
    plt.setp(ax_i.get_xticklabels(), visible=False)

    # -- Gate strip --
    render_gate_strip(ax_g, ["pass", "fail", "none", "none"])


def render_s4(ax_p, ax_i, ax_g):
    """S4: CHANNEL FAIL -- Chop (flat slope, no trend)."""
    bars = np.arange(N_SC)

    price = shaped([
        (0, 1.060), (5, 1.062), (10, 1.059), (STAGE1, 1.061),
        (25, 1.058), (40, 1.060), (60, 1.057), (79, 1.059)
    ], N_SC, noise=0.001, seed=70)

    # Flat regression line
    t_reg = np.arange(STAGE1 + 1, dtype=float)
    reg_line = 1.061 - (t_reg / STAGE1) * 0.001

    # -- Price panel --
    style_ax(ax_p)
    ax_p.plot(bars, price, color=CLR_PRICE, lw=1.0)
    ax_p.plot(t_reg, reg_line, color=CLR_BE, lw=1.2, ls="--", alpha=0.8)
    ax_p.axvline(STAGE1, color="#4b5563", lw=0.6, ls=":", alpha=0.5)
    ax_p.set_title("S4: CHANNEL FAIL", color=CLR_SL, fontsize=8,
                   fontweight="bold", pad=3)
    annotate_box(ax_p, "Chop: flat/ranging price\nslope ~ 0 (> -0.001)")
    ax_p.set_xlim(0, N_SC - 1)
    plt.setp(ax_p.get_xticklabels(), visible=False)

    # -- Indicator panel: slope text display --
    style_ax(ax_i)
    ax_i.text(0.5, 0.70, "slope = -0.00005", color=CLR_BE, fontsize=9,
              ha="center", va="center", transform=ax_i.transAxes,
              fontweight="bold")
    ax_i.text(0.5, 0.40, "threshold = -0.001", color=CLR_TP, fontsize=7,
              ha="center", va="center", transform=ax_i.transAxes)
    ax_i.text(0.5, 0.14, "FAIL: slope too flat", color=CLR_SL, fontsize=7,
              ha="center", va="center", transform=ax_i.transAxes,
              fontweight="bold")
    ax_i.set_xticks([])
    ax_i.set_yticks([])

    # -- Gate strip --
    render_gate_strip(ax_g, ["pass", "fail", "none", "none"])


def render_s5(ax_p, ax_i, ax_g):
    """S5: DIVERGE FAIL -- No HL (stoch_9 C2 low < C1 low)."""
    bars = np.arange(N_SC)

    price = shaped([
        (0, 1.085), (10, 1.072), (STAGE1, 1.062),
        (C1_ENTRY, 1.056), (C1_ENTRY + 5, 1.053), (C1_EXIT, 1.058),
        (38, 1.054), (C2_ENTRY, 1.048), (C2_ENTRY + 6, 1.044),
        (SIGNAL, 1.047), (70, 1.050), (79, 1.055)
    ], N_SC, noise=0.0008, seed=80)

    s9 = shaped_ind([
        (0, 62), (10, 40), (C1_ENTRY, 20), (C1_ENTRY + 5, 18),
        (C1_EXIT, 32), (35, 48),
        (C2_ENTRY, 18), (C2_ENTRY + 6, 12),
        (SIGNAL, 28), (70, 50), (79, 58)
    ], N_SC, noise=1.0, seed=81)

    # -- Price panel --
    style_ax(ax_p)
    ax_p.plot(bars, price, color=CLR_PRICE, lw=1.0)
    for bar in [C1_ENTRY, C1_EXIT, C2_ENTRY]:
        ax_p.axvline(bar, color="#f97316", lw=0.5, ls=":", alpha=0.4)
    ax_p.set_title("S5: DIVERGE FAIL", color=CLR_SL, fontsize=8,
                   fontweight="bold", pad=3)
    annotate_box(ax_p, "No divergence: stoch_9\nmakes lower-low (LL)")
    ax_p.set_xlim(0, N_SC - 1)
    plt.setp(ax_p.get_xticklabels(), visible=False)

    # -- Indicator panel: stoch_9 with LL arrow --
    style_ax(ax_i)
    ax_i.plot(bars, s9, color=CLR_S9, lw=1.0)
    ax_i.axhline(25, color=CLR_SL, lw=0.6, ls="--", alpha=0.5)
    ax_i.fill_between(bars, 0, 25, alpha=0.06, color=CLR_SL)

    c1_low_idx = int(C1_ENTRY + np.argmin(s9[C1_ENTRY:C1_EXIT + 1]))
    c2_low_idx = int(C2_ENTRY + np.argmin(s9[C2_ENTRY:SIGNAL + 1]))
    ax_i.scatter(c1_low_idx, s9[c1_low_idx], marker="v",
                 color="#f97316", s=25, zorder=6)
    ax_i.scatter(c2_low_idx, s9[c2_low_idx], marker="v",
                 color=CLR_SL, s=25, zorder=6)

    # LL arrow (pointing down = failure)
    ax_i.annotate("", xy=(c2_low_idx, s9[c2_low_idx] + 1),
                  xytext=(c1_low_idx, s9[c1_low_idx] + 1),
                  arrowprops=dict(arrowstyle="->", color=CLR_SL, lw=1.5))
    mid_x = (c1_low_idx + c2_low_idx) / 2
    mid_y = min(float(s9[c1_low_idx]), float(s9[c2_low_idx])) - 6
    ax_i.text(mid_x, mid_y, "LL", color=CLR_SL, fontsize=7,
              ha="center", fontweight="bold")

    ax_i.set_ylim(0, 80)
    ax_i.set_ylabel("stoch_9", fontsize=6)
    plt.setp(ax_i.get_xticklabels(), visible=False)

    # -- Gate strip --
    render_gate_strip(ax_g, ["pass", "pass", "fail", "none"])


def render_s6(ax_p, ax_i, ax_g):
    """S6: DIVERGE FAIL -- Single cycle (only one oversold visit)."""
    bars = np.arange(N_SC)

    price = shaped([
        (0, 1.085), (10, 1.072), (STAGE1, 1.062),
        (C1_ENTRY, 1.056), (C1_ENTRY + 5, 1.053), (C1_EXIT, 1.058),
        (40, 1.062), (50, 1.068), (60, 1.072), (79, 1.078)
    ], N_SC, noise=0.0008, seed=90)

    s9 = shaped_ind([
        (0, 62), (10, 40), (C1_ENTRY, 20), (C1_ENTRY + 5, 16),
        (C1_EXIT, 32), (35, 48), (45, 55), (55, 58),
        (65, 52), (79, 55)
    ], N_SC, noise=1.5, seed=91)

    # -- Price panel --
    style_ax(ax_p)
    ax_p.plot(bars, price, color=CLR_PRICE, lw=1.0)
    ax_p.axvline(C1_ENTRY, color="#f97316", lw=0.5, ls=":", alpha=0.4)
    ax_p.axvline(C1_EXIT, color="#f97316", lw=0.5, ls=":", alpha=0.4)
    ax_p.set_title("S6: DIVERGE FAIL", color=CLR_SL, fontsize=8,
                   fontweight="bold", pad=3)
    annotate_box(ax_p, "Single cycle only\nNo 2nd oversold visit")
    ax_p.set_xlim(0, N_SC - 1)
    plt.setp(ax_p.get_xticklabels(), visible=False)

    # -- Indicator panel: stoch_9 with waiting zone --
    style_ax(ax_i)
    ax_i.plot(bars, s9, color=CLR_S9, lw=1.0)
    ax_i.axhline(25, color=CLR_SL, lw=0.6, ls="--", alpha=0.5)
    ax_i.fill_between(bars, 0, 25, alpha=0.06, color=CLR_SL)

    # Amber waiting zone after C1 exit
    ax_i.axvspan(C1_EXIT, N_SC - 1, alpha=0.08, color=CLR_BE)
    ax_i.text(50, 12, "waiting for Cycle 2...", color=CLR_BE, fontsize=6,
              fontstyle="italic", ha="center")

    c1_low_idx = int(C1_ENTRY + np.argmin(s9[C1_ENTRY:C1_EXIT + 1]))
    ax_i.scatter(c1_low_idx, s9[c1_low_idx], marker="v",
                 color="#f97316", s=25, zorder=6)

    ax_i.set_ylim(0, 80)
    ax_i.set_ylabel("stoch_9", fontsize=6)
    plt.setp(ax_i.get_xticklabels(), visible=False)

    # -- Gate strip --
    render_gate_strip(ax_g, ["pass", "pass", "fail", "none"])


def render_s7(ax_p, ax_i, ax_g):
    """S7: CASCADE FAIL -- V-bottom (stoch_40 < 30 at Cycle 2 exit)."""
    bars = np.arange(N_SC)

    price = shaped([
        (0, 1.090), (8, 1.078), (STAGE1, 1.065),
        (C1_ENTRY, 1.058), (C1_ENTRY + 5, 1.050), (C1_EXIT, 1.055),
        (38, 1.048), (C2_ENTRY, 1.040), (C2_ENTRY + 6, 1.035),
        (SIGNAL, 1.042), (65, 1.055), (79, 1.068)
    ], N_SC, noise=0.001, seed=100)

    s9 = shaped_ind([
        (0, 62), (10, 40), (C1_ENTRY, 18), (C1_ENTRY + 5, 15),
        (C1_EXIT, 30), (35, 48),
        (C2_ENTRY, 20), (C2_ENTRY + 6, 18),
        (SIGNAL, 30), (65, 55), (79, 60)
    ], N_SC, noise=1.0, seed=101)

    s40 = shaped_ind([
        (0, 55), (15, 38), (25, 22), (35, 18),
        (50, 14), (SIGNAL, 22),
        (70, 35), (79, 42)
    ], N_SC, noise=1.0, seed=102)

    # -- Price panel --
    style_ax(ax_p)
    ax_p.plot(bars, price, color=CLR_PRICE, lw=1.0)
    for bar in [C1_ENTRY, C1_EXIT, C2_ENTRY]:
        ax_p.axvline(bar, color="#f97316", lw=0.5, ls=":", alpha=0.4)
    ax_p.axvline(SIGNAL, color=CLR_SL, lw=0.7, ls="--", alpha=0.5)
    ax_p.set_title("S7: CASCADE FAIL", color=CLR_SL, fontsize=8,
                   fontweight="bold", pad=3)
    annotate_box(ax_p, "V-bottom: stoch_40 < 30\nat Cycle 2 exit")
    ax_p.set_xlim(0, N_SC - 1)
    plt.setp(ax_p.get_xticklabels(), visible=False)

    # -- Indicator panel: stoch_9 + stoch_40 overlaid --
    style_ax(ax_i)
    ax_i.plot(bars, s9, color=CLR_S9, lw=0.9, label="stoch_9")
    ax_i.plot(bars, s40, color=CLR_S40, lw=0.9, label="stoch_40")
    ax_i.axhline(30, color=CLR_SL, lw=0.8, ls="--", alpha=0.7)
    ax_i.fill_between(bars, 0, 30, alpha=0.06, color=CLR_SL)

    # Mark stoch_40 failure at signal bar
    s40_at_sig = float(s40[SIGNAL])
    ax_i.scatter(SIGNAL, s40_at_sig, marker="x", color=CLR_SL,
                 s=50, zorder=6, lw=2)
    ax_i.text(SIGNAL + 1, s40_at_sig + 3,
              "s40=" + str(int(round(s40_at_sig))) + "\n(<30)",
              color=CLR_SL, fontsize=5.5)

    ax_i.axvline(SIGNAL, color=CLR_SL, lw=0.7, ls="--", alpha=0.5)
    ax_i.set_ylim(0, 80)
    ax_i.set_ylabel("stoch", fontsize=6)
    ax_i.legend(loc="upper right", fontsize=5.5, framealpha=0.3,
                labelcolor="#e7e9ea", facecolor=DARK_CARD)
    plt.setp(ax_i.get_xticklabels(), visible=False)

    # -- Gate strip --
    render_gate_strip(ax_g, ["pass", "pass", "pass", "fail"])


# ====================================================================
# Decision tree header
# ====================================================================

def render_decision_tree(ax):
    """Render the pipeline decision tree header."""
    style_ax(ax)
    ax.set_facecolor(DARK_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Layer boxes
    box_w = 12
    box_h = 24
    box_y = 55
    positions_x = [5, 24, 46, 68]
    labels = ["MACRO\nGATE", "CHANNEL\nGATE", "TWO-CYCLE\nDIVERGENCE", "CASCADE\nGATE"]
    colors = ["#6366f1", CLR_CHAN, CLR_S9, CLR_S40]

    for x, lbl, clr in zip(positions_x, labels, colors):
        rect = FancyBboxPatch((x, box_y), box_w, box_h,
                              boxstyle="round,pad=0.8",
                              facecolor=DARK_CARD, edgecolor=clr, lw=1.8)
        ax.add_patch(rect)
        ax.text(x + box_w / 2, box_y + box_h / 2, lbl,
                ha="center", va="center", fontsize=7.5,
                color=clr, fontweight="bold")

    # SIGNAL box
    sig_x = 88
    rect = FancyBboxPatch((sig_x, box_y), 9, box_h,
                          boxstyle="round,pad=0.8",
                          facecolor=DARK_CARD, edgecolor=CLR_TP, lw=2)
    ax.add_patch(rect)
    ax.text(sig_x + 4.5, box_y + box_h / 2, "SIGNAL",
            ha="center", va="center", fontsize=7.5,
            color=CLR_TP, fontweight="bold")

    # Pass arrows (horizontal, green)
    arrow_y = box_y + box_h / 2
    for i in range(len(positions_x) - 1):
        x_start = positions_x[i] + box_w + 0.5
        x_end = positions_x[i + 1] - 0.5
        ax.annotate("", xy=(x_end, arrow_y), xytext=(x_start, arrow_y),
                    arrowprops=dict(arrowstyle="-|>", color=CLR_TP, lw=1.2))
        ax.text((x_start + x_end) / 2, arrow_y + 4, "PASS",
                color=CLR_TP, fontsize=5.5, ha="center")

    # Last pass arrow to SIGNAL
    x_start = positions_x[-1] + box_w + 0.5
    ax.annotate("", xy=(sig_x - 0.5, arrow_y), xytext=(x_start, arrow_y),
                arrowprops=dict(arrowstyle="-|>", color=CLR_TP, lw=1.2))
    ax.text((x_start + sig_x) / 2, arrow_y + 4, "PASS",
            color=CLR_TP, fontsize=5.5, ha="center")

    # Fail arrows (downward, red)
    fail_labels = ["S2", "S3 / S4", "S5 / S6", "S7"]
    for x, fl in zip(positions_x, fail_labels):
        x_mid = x + box_w / 2
        ax.annotate("", xy=(x_mid, 18), xytext=(x_mid, box_y - 1),
                    arrowprops=dict(arrowstyle="-|>", color=CLR_SL, lw=1.0))
        ax.text(x_mid, box_y - 6, "FAIL", color=CLR_SL,
                fontsize=5, ha="center")
        ax.text(x_mid, 8, fl, color=CLR_SL, fontsize=7,
                ha="center", fontweight="bold")

    ax.set_title(
        "V4 Four-Layer Signal Pipeline -- All Possible Scenarios",
        color="#e7e9ea", fontsize=11, fontweight="bold", pad=8)


# ====================================================================
# Legend cell
# ====================================================================

def render_legend(ax):
    """Render the legend/key cell."""
    style_ax(ax)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#374151")

    y = 0.93
    ax.text(0.5, y, "LEGEND", color="#e7e9ea", fontsize=10,
            fontweight="bold", ha="center", transform=ax.transAxes)

    y -= 0.07
    ax.text(0.08, y, "Gate status:", color="#9ca3af", fontsize=7,
            transform=ax.transAxes)
    y -= 0.045
    for label, clr in [("PASS", CLR_TP), ("FAIL", CLR_SL),
                        ("NOT REACHED", CLR_GATE_NONE)]:
        ax.text(0.10, y, "\u25a0", color=clr, fontsize=12,
                va="center", transform=ax.transAxes)
        ax.text(0.20, y, label, color="#e7e9ea", fontsize=7,
                va="center", transform=ax.transAxes)
        y -= 0.045

    y -= 0.04
    ax.text(0.08, y, "Indicator colours:", color="#9ca3af", fontsize=7,
            transform=ax.transAxes)
    y -= 0.045
    for label, clr in [("stoch_9 (fast)", CLR_S9),
                        ("stoch_40 (medium)", CLR_S40),
                        ("stoch_60 (slow)", CLR_S60),
                        ("R-sq / channel", CLR_CHAN)]:
        ax.text(0.10, y, "\u2014", color=clr, fontsize=10,
                va="center", transform=ax.transAxes)
        ax.text(0.20, y, label, color=clr, fontsize=6.5,
                va="center", transform=ax.transAxes)
        y -= 0.045

    y -= 0.04
    ax.text(0.08, y, "Pipeline:", color="#9ca3af", fontsize=7,
            transform=ax.transAxes)
    y -= 0.04
    for line in ["L1: Macro gate (external)",
                 "L2: Channel gate (R2 + slope)",
                 "L3: Two-cycle divergence",
                 "L4: Cascade (stoch_40 >= 30)"]:
        ax.text(0.10, y, line, color="#e7e9ea", fontsize=5.5,
                va="center", transform=ax.transAxes, family="monospace")
        y -= 0.038

    y -= 0.04
    ax.text(0.08, y, "Cascade order:", color="#9ca3af", fontsize=7,
            transform=ax.transAxes)
    y -= 0.04
    for line in ["stoch_9 exits oversold first",
                 "stoch_40 follows",
                 "stoch_60 exits last (slowest)"]:
        ax.text(0.10, y, line, color="#e7e9ea", fontsize=5.5,
                va="center", transform=ax.transAxes, family="monospace")
        y -= 0.038


# ====================================================================
# Main
# ====================================================================

def main():
    """Build the full V4 scenario map figure."""
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "results" / "strategy_perspectives"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "V4_scenario_map.png"

    fig = plt.figure(figsize=(34, 24), facecolor=DARK_BG)

    outer_gs = GridSpec(3, 1, figure=fig, hspace=0.06,
                        height_ratios=[1.0, 5.0, 5.0])

    # Row 0: Decision tree header
    ax_tree = fig.add_subplot(outer_gs[0])
    render_decision_tree(ax_tree)

    # Row 1: Scenarios S1-S4
    inner_gs1 = GridSpecFromSubplotSpec(
        3, 4, subplot_spec=outer_gs[1],
        hspace=0.12, wspace=0.10,
        height_ratios=[3.0, 1.8, 0.5]
    )

    renderers_r1 = [render_s1, render_s2, render_s3, render_s4]
    for col, renderer in enumerate(renderers_r1):
        ax_p = fig.add_subplot(inner_gs1[0, col])
        ax_i = fig.add_subplot(inner_gs1[1, col])
        ax_g = fig.add_subplot(inner_gs1[2, col])
        renderer(ax_p, ax_i, ax_g)

    # Row 2: Scenarios S5-S7 + Legend
    inner_gs2 = GridSpecFromSubplotSpec(
        3, 4, subplot_spec=outer_gs[2],
        hspace=0.12, wspace=0.10,
        height_ratios=[3.0, 1.8, 0.5]
    )

    renderers_r2 = [render_s5, render_s6, render_s7]
    for col, renderer in enumerate(renderers_r2):
        ax_p = fig.add_subplot(inner_gs2[0, col])
        ax_i = fig.add_subplot(inner_gs2[1, col])
        ax_g = fig.add_subplot(inner_gs2[2, col])
        renderer(ax_p, ax_i, ax_g)

    # Legend cell (col 3, spanning all sub-rows)
    ax_legend = fig.add_subplot(inner_gs2[:, 3])
    render_legend(ax_legend)

    save_fig(fig, out_path)


if __name__ == "__main__":
    main()

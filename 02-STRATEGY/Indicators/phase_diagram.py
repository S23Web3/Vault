"""
Four Pillars v3.4 — Phased SL/TP Movement Diagram
Visualizes how Stop Loss and Take Profit evolve through phases for a LONG trade.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Simulate a LONG trade progressing through all phases
# Using hypothetical price action with ATR = 10

entry_price = 100
atr = 10
bars = 80

# Price simulation: trending up with pullbacks
np.random.seed(42)
price = [entry_price]
for i in range(1, bars):
    drift = 0.4 if i < 60 else -0.1
    noise = np.random.normal(drift, 1.5)
    price.append(price[-1] + noise)
price = np.array(price)

# Phase triggers (bar indices)
entry_bar = 0
phase1_bar = 12   # Cloud 2 crosses bullish
phase2_bar = 28   # Cloud 3 crosses bullish
phase3_bar = 38   # Cloud 3 + Cloud 4 sync
c2_exit_bar = 68  # Cloud 2 flips against

# --- Compute SL and TP through phases ---
sl = np.full(bars, np.nan)
tp = np.full(bars, np.nan)
phase = np.zeros(bars, dtype=int)

# Phase 0: static
sl_val = entry_price - 2 * atr  # 80
tp_val = entry_price + 4 * atr  # 140

for i in range(bars):
    if i < entry_bar:
        continue
    if i >= c2_exit_bar:
        break

    if i == phase1_bar:
        # Phase 1: SL anchored to candle low - 1 ATR
        candle_low = price[i] - 2  # simulated candle low
        new_sl = candle_low - atr
        if new_sl > sl_val:
            sl_val = new_sl
        tp_val = tp_val + atr
        phase[i:] = 1

    elif i == phase2_bar:
        # Phase 2: SL + 1 ATR, TP + 1 ATR
        sl_val = sl_val + atr
        tp_val = tp_val + atr
        phase[i:] = 2

    elif i == phase3_bar:
        # Phase 3: TP removed, cloud-based trail starts
        tp_val = np.nan
        phase[i:] = 3

    # Phase 3 trail: simulate cloud bottom rising
    if phase[i] == 3:
        # Simulated cloud bottom (EMA 34/50 min)
        cloud_bottom = entry_price + (i - entry_bar) * 0.35 - 5
        trail_sl = cloud_bottom - atr
        if trail_sl > sl_val:
            sl_val = trail_sl

    sl[i] = sl_val
    if not np.isnan(tp_val):
        tp[i] = tp_val

# --- PLOT ---
fig, ax = plt.subplots(figsize=(16, 9), facecolor='#1a1a2e')
ax.set_facecolor('#16213e')

# Price
ax.plot(range(bars), price, color='white', linewidth=1.5, alpha=0.9, label='Price', zorder=3)

# SL line with phase colors
phase_colors = {0: '#ff3333', 1: '#ff6666', 2: '#ff8c00', 3: '#ffd700'}
phase_labels_map = {0: 'SL Phase 0 (Static)', 1: 'SL Phase 1 (Cloud 2)', 2: 'SL Phase 2 (Cloud 3)', 3: 'SL Phase 3 (Trail)'}

for p in [0, 1, 2, 3]:
    mask = (phase == p) & ~np.isnan(sl)
    if mask.any():
        indices = np.where(mask)[0]
        ax.plot(indices, sl[indices], color=phase_colors[p], linewidth=2.5,
                linestyle='-' if p == 0 else ('--' if p < 3 else ':'),
                label=phase_labels_map[p], zorder=4)

# TP line
tp_mask = ~np.isnan(tp)
if tp_mask.any():
    tp_indices = np.where(tp_mask)[0]
    ax.plot(tp_indices, tp[tp_indices], color='#00ff88', linewidth=1.5,
            linestyle='--', label='Take Profit', zorder=4)

# Phase transition markers
transitions = [
    (entry_bar, entry_price, 'ENTRY\n(P0)', '#00ff88', 'bottom'),
    (phase1_bar, sl[phase1_bar], 'SL1\n(Cloud 2)', '#ff6666', 'bottom'),
    (phase2_bar, sl[phase2_bar], 'SL2\n(Cloud 3)', '#ff8c00', 'bottom'),
    (phase3_bar, sl[phase3_bar], 'TRAIL\n(C3+C4)', '#ffd700', 'bottom'),
    (c2_exit_bar, price[c2_exit_bar], 'C2\nExit', '#ff00ff', 'top'),
]

for bar, y, text, color, va in transitions:
    ax.annotate(text, xy=(bar, y), fontsize=9, fontweight='bold',
                color=color, ha='center', va=va,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.2, edgecolor=color),
                zorder=5)
    ax.axvline(x=bar, color=color, alpha=0.2, linestyle=':', zorder=1)

# Entry marker
ax.scatter([entry_bar], [entry_price], marker='^', s=200, color='#00ff88', zorder=6, edgecolors='white', linewidths=0.5)

# C2 Exit marker
ax.scatter([c2_exit_bar], [price[c2_exit_bar]], marker='v', s=200, color='#ff00ff', zorder=6, edgecolors='white', linewidths=0.5)

# Fill between price and SL (risk zone)
valid = ~np.isnan(sl) & (np.arange(bars) < c2_exit_bar)
ax.fill_between(range(bars), sl, price, where=valid & (price > sl),
                alpha=0.05, color='#ff3333', zorder=1)

# Phase zones background
ax.axvspan(entry_bar, phase1_bar, alpha=0.03, color='red')
ax.axvspan(phase1_bar, phase2_bar, alpha=0.03, color='orange')
ax.axvspan(phase2_bar, phase3_bar, alpha=0.03, color='yellow')
ax.axvspan(phase3_bar, c2_exit_bar, alpha=0.03, color='gold')

# Annotations for SL/TP movement explanation
ax.annotate('SL: entry - 2 ATR\nTP: entry + 4 ATR',
            xy=(6, sl[5]), fontsize=7, color='#ff9999', alpha=0.8,
            ha='center', va='top')

ax.annotate('SL tightens to candle low - ATR\nTP expands + 1 ATR',
            xy=(20, sl[phase1_bar] + 2), fontsize=7, color='#ffaa66', alpha=0.8,
            ha='center', va='bottom')

ax.annotate('SL shifts + 1 ATR\nTP shifts + 1 ATR',
            xy=(33, sl[phase2_bar] + 2), fontsize=7, color='#ffcc44', alpha=0.8,
            ha='center', va='bottom')

ax.annotate('TP removed\nSL = Cloud 3 bottom - ATR\nUpdates each bar',
            xy=(50, sl[48] + 2), fontsize=7, color='#ffd700', alpha=0.8,
            ha='center', va='bottom')

# Title and labels
ax.set_title('Four Pillars v3.4 — Phased SL/TP Movement (Long Trade)',
             fontsize=16, fontweight='bold', color='white', pad=20)
ax.set_xlabel('Bars', fontsize=11, color='gray')
ax.set_ylabel('Price', fontsize=11, color='gray')

# Legend
legend = ax.legend(loc='upper left', fontsize=9, facecolor='#1a1a2e', edgecolor='gray',
                   labelcolor='white', framealpha=0.9)

# Style
ax.tick_params(colors='gray')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('gray')
ax.spines['bottom'].set_color('gray')
ax.grid(True, alpha=0.1, color='gray')

plt.tight_layout()
plt.savefig(r'c:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\phase_diagram.png',
            dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print("Diagram saved to phase_diagram.png")

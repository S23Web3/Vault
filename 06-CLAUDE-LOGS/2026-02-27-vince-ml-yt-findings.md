# 2026-02-27 Vince ML — YT Channel Findings Session

## Context
User closed a previous chat session mid-conversation. Previous session covered Vince ML direction, YT transcript output, and RL for ML — the RL section was missing from the Vince analysis. This session reconstructed context from memory/logs and performed the full analysis.

## What Was Done
1. Confirmed previous session context via memory files and today's plan logs
2. Read all 202 YT video summaries from `PROJECTS/yt-transcript-analyzer/output/summaries/` (JSON)
3. Read the FreeCodeCamp full course transcript (9Y3yaoi9rUQ) — unsupervised learning, Twitter sentiment, GARCH
4. Read RL video summaries: oW4hgB1vIoY (full RL trading bot), BznJQMi35sQ (short)
5. Read Vince v2 concept doc (`docs/VINCE-V2-CONCEPT-v2.md`) in full
6. Synthesized findings into plan document

## Key Findings (see full plan for detail)

### THE MISSING RL PIECE
RL in the channel is shown as a full trade agent (entry + exit). What was never applied to Vince: RL as an **exit policy optimizer**. The RL agent observes live indicator state after entry and learns WHEN to exit. This enhances Panel 2 (PnL Reversal Analysis) without touching entry signals or reducing trade count. Fits Vince constraints perfectly.

- State: `[bars_since_entry, current_pnl_atr, k1, k2, k3, k4, cloud_state, bbw]`
- Action: HOLD or EXIT
- Reward: net_pnl at exit (with commission)
- Train on enriched trade data; test on held-out period

### TIER 1 FINDINGS
- **Unsupervised clustering** (k-means on entry-state vectors) for Mode 2 — clusters trades into natural constellations before sweeping. Eliminates the dimensional explosion problem.
- **XGBoost feature importance** ranks which indicator dimensions to sweep first in Mode 2. Stochastics rank #1 across all studies — validates Four Pillars.
- **Exits matter more than entries** — random entry + ATR stops = 160% returns ([4BaMwwJeKEA]). Panel 2 should be the build priority.

### TIER 2 FINDINGS
- Walk-forward needs rolling windows, not just single train/test split
- Survivorship bias: 399-coin dataset excludes delisted coins — must caveat all pattern results
- Reflexivity: large-N discovered patterns get arbitraged. Show N prominently, flag high-N.
- Held-out partition: Mode 2 discovers on 80% of data, Mode 1 validates on 20%. Currently missing.
- GARCH for volatility regime look-forward — future scope
- LSTM warning: use returns (stationary), not price levels — common trap

### GENERAL VALIDATED FACTS
- Stochastics + moving averages = consistently top-ranked in all 12-indicator ML studies
- 52% ML accuracy on trend direction IS real signal (profitable with good risk management)
- NW indicator repaints with future data — caution if added as constellation dimension
- Optimising SL/TP on same data as discovery = overfitting. Mode 3 walk-forward already handles this.

## Output Files
- Plan: `C:\Users\User\.claude\plans\logical-coalescing-lark.md`
- Vault copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-yt-channel-ml-findings-for-vince.md`

## What Was NOT Done (next session)
- Vince v2 concept doc NOT updated yet (findings identified, user decides which to incorporate)
- Concept doc still marked "NOT YET APPROVED FOR BUILD"
- RL exit optimizer not scoped for build — finding only, not a build decision
- TOPIC-vince-v2.md not updated (needs update to reflect these findings)

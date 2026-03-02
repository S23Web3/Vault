# Plan: Vince v2 Concept Doc Update + Plugin Interface Spec Start

**Date:** 2026-02-27
**Session context:** Post-YT-analysis session. 202 videos analyzed. 7 ML findings identified for Vince.

---

## Context

The previous session analyzed 202 YT transcripts from an algo trading channel and the FreeCodeCamp ML course. The output is `06-CLAUDE-LOGS/plans/2026-02-27-yt-channel-ml-findings-for-vince.md` — a ranked list of 7 findings applicable to Vince v2.

The Vince v2 concept doc (`PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md`) was written 2026-02-23, has not been approved for build, and does not yet reflect these findings. This plan updates it with all 7 findings, leaving approval status unchanged (user still researching).

After the concept doc update, this plan also begins P1.7: formal plugin interface spec — the first concrete Vince build artifact.

---

## Scope

### In scope
1. Edit `VINCE-V2-CONCEPT-v2.md` with 7 ML findings (specific edits below)
2. Create `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — formal spec for the `StrategyPlugin` ABC

### NOT in scope
- Approving concept doc for build (user still researching)
- Writing any Python code
- Updating P1.7 backlog status (stays WAITING until concept approved)

---

## Task 1: Edit VINCE-V2-CONCEPT-v2.md

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md`

### Edit 1 — "What Changed from v1" section
Add two new items to the numbered list (items 15 and 16):

```
15. Panel 2 (PnL Reversal Analysis) elevated as highest-priority build artifact —
    research finding (2026-02-27): random entry + ATR stops = 160% return. Exit
    optimization contributes more alpha than entry filtering. [video 4BaMwwJeKEA]
16. RL Exit Policy Optimizer added as new component — sits between Enricher and
    Dashboard. Enhances Panel 2 without touching entries or reducing trade count.
    Research source: [oW4hgB1vIoY], [BznJQMi35sQ]. See section "RL Exit Policy
    Optimizer" below.
```

### Edit 2 — Mode 2 Auto-Discovery (rewrite the section)
Replace current Mode 2 description block with expanded version that adds:
- **Pre-step 1**: XGBoost feature importance (label=win/loss on enriched trades). Ranks which indicator dimensions have the most predictive signal. High-signal dimensions swept first. Ranked list shown as Mode 2 setup screen.
- **Pre-step 2**: Unsupervised clustering (k-means on entry-state feature vectors). Groups naturally occurring trade constellations. Each cluster = one candidate pattern. Cluster labels become Mode 2 query dimensions. Eliminates the dimensional explosion from grid search.
- **Held-out partition**: Time-based 80/20 split enforced before Mode 2 runs. Mode 2 discovers patterns on first 80% of the date range. Mode 1 constellation queries can validate against the held-out 20%. This prevents overfitting discoveries to the same data used to find them. Partition point stored with every session.
- **Reflexivity caution**: N shown prominently on all discovered patterns. High-N patterns (widely tradeable) carry a flag: "High-N pattern. If publicly known, edge may be front-run. Prefer low-N coin/regime-specific patterns for durable alpha."
- The existing permutation significance gate remains unchanged.

### Edit 3 — New section "RL Exit Policy Optimizer"
Add after "Three Operating Modes" and before "Performance Metrics":

```markdown
## RL Exit Policy Optimizer

**Status:** Architecture addition (2026-02-27). Sits between Enricher and Dashboard.
Enhances Panel 2 without changing entries or reducing trade count.

### What it does
Trains a reinforcement learning agent on historical enriched trade data to learn
WHEN to exit a winning position, given the current state of indicators after entry.
The agent does not make entry decisions — entries come from the strategy plugin unchanged.

### Architecture
- Environment: trade lifecycle (entry bar to exit bar)
- Episode: one trade
- State: [bars_since_entry, current_pnl_in_atr, k1_now, k2_now, k3_now, k4_now, cloud_state_now, bbw_now]
- Action: HOLD or EXIT
- Reward: net_pnl_at_exit minus commission (deducted only when EXIT is chosen)
- Train on enriched trade data (first 80% of date range, same partition as Mode 2)
- Test on held-out 20% of date range

### Constraint satisfaction
- Does NOT reduce trade count (entries unchanged)
- Does NOT change signal logic (plugin compute_signals() unchanged)
- Does NOT require LLM (Layer 1 component)
- Layer 2 LLM (Panel 8) interprets the learned policy in plain language:
  "The agent learned to exit when K1 crosses below 60 AND BBW is contracting"

### Dashboard integration
RL policy output overlays on Panel 2 as an additional curve:
- Original Panel 2: fixed-TP sweep (static curves, historical best-TP)
- RL overlay: dynamic exit signal per trade (state-conditional policy)
- Comparison visible: TP sweep baseline vs RL policy outcome

### Why this fits Vince
PnL Reversal Analysis (Panel 2) currently answers: "what TP multiple worked best?"
The RL policy answers: "given where indicators are RIGHT NOW after entry, should I exit?"
These are complementary. RL does not replace the static TP sweep — it adds the dynamic layer.

### Separation of concerns
RL Exit Policy Optimizer is NOT Mode 3 (Settings Optimizer). Mode 3 sweeps entry
parameters. RL Exit Policy learns exit timing. They are independent components and
do not interact at build time.
```

### Edit 4 — Process Flow Overview diagram
Update the mermaid flowchart to add the RL Exit Policy Optimizer node:

Add `J["RL EXIT POLICY\nOllama / sklearn\nHOLD/EXIT policy\n(Panel 2 overlay)"] --> F` to the existing diagram. Connects from the Enricher output (same source as Analyzer).

### Edit 5 — Stage 4 Dashboard Panels section
In the mermaid diagram and prose for Panel 2, add:
- RL Exit Policy feeds into Panel 2 as an overlay
- Label Panel 2 explicitly as "HIGHEST BUILD PRIORITY (v1)"

### Edit 6 — Constraints section
Add two new bullet points:

```
- Survivorship bias: pattern results must state which coins and date range are
  included. Coins that delisted or lost liquidity before the analysis period are
  absent from the dataset. All auto-discovery output includes: "N=[count] coins
  active [date range]. Delisted coins not included."
- Reflexivity: high-N patterns are more likely to be discovered and traded by
  others. Large sample size is NOT a proxy for edge durability. Mode 2 surfaces
  N prominently and flags high-N patterns with a reflexivity caution.
```

### Edit 7 — Open Questions section
Add new open question:

```
7. RL Exit Policy Optimizer — training methodology, hyperparameters, and whether
   to use a simple Q-learning agent, PPO, or a simpler rule-extraction approach.
   Separate scoping session needed before build.
```

---

## Task 2: Create VINCE-PLUGIN-INTERFACE-SPEC-v1.md

**New file:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-PLUGIN-INTERFACE-SPEC-v1.md`

This is P1.7. It is the spec document, not code. It formalizes the `StrategyPlugin` ABC so that the FourPillarsPlugin implementation can be built without ambiguity.

### Document sections

1. **Purpose** — why this spec exists, what it enables
2. **Abstract Base Class** — full `StrategyPlugin(ABC)` with complete type signatures and docstrings
3. **Method Contracts** (one subsection per method):
   - `compute_signals(ohlcv_df)`: input DataFrame column requirements, output DataFrame guarantees (which columns must be added, naming convention, types, NaN handling policy)
   - `parameter_space()`: full dict schema, valid type strings (`"float"`, `"int"`, `"bool"`), required keys per entry, optional keys (`"log"` for log-scale)
   - `trade_schema()`: full dict schema, required fields (entry_bar, exit_bar, pnl, commission, direction), optional strategy-specific fields
   - `run_backtest(params, start, end, symbols)`: parameter types, date format, symbols list format, return value (Path to trade CSV), error contract (raises on missing data)
   - `strategy_document` property: required format (markdown only), what happens if PDF (convert first)
4. **OHLCV DataFrame Contract** — the canonical input to `compute_signals()`: required columns, dtypes, timezone assumptions, index type
5. **Enricher Contract** — what the Enricher expects from the plugin: which column names it will look for after `compute_signals()`, naming convention for indicator snapshot columns (`k1_at_entry`, `k2_at_entry`, etc.)
6. **Compliance Checklist** — the test requirements a plugin must pass to be considered Vince-compatible
7. **FourPillarsPlugin — compliance mapping** — how the existing `signals/four_pillars_v383_v2.py` maps to each method

---

## Files Modified / Created

| File | Action |
|------|--------|
| `PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md` | Edit (7 specific edits) |
| `PROJECTS/four-pillars-backtester/docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` | Create (new) |
| `06-CLAUDE-LOGS/plans/2026-02-27-vince-concept-doc-update-and-plugin-spec.md` | Create (vault plan copy — this file) |
| `memory/TOPIC-vince-v2.md` | Edit (update status + new files) |

---

## Files NOT Modified

| File | Reason |
|------|--------|
| `PRODUCT-BACKLOG.md` | P1.7 stays WAITING — concept doc not yet approved |
| `LIVE-SYSTEM-STATUS.md` | No system deployed |
| `06-CLAUDE-LOGS/INDEX.md` | Only updated if a session log is written |

---

## Verification

After implementation:
1. Open `VINCE-V2-CONCEPT-v2.md` — confirm 7 additions are present, status header still says "NOT YET APPROVED FOR BUILD"
2. Open `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — confirm all 7 sections exist, method contracts are unambiguous
3. Open `TOPIC-vince-v2.md` — confirm new files referenced
4. Run `python -c "import ast; ast.parse(open('...').read())"` on any Python code snippets in the spec to confirm they are syntactically valid (the ABC class definition)

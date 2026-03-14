# WEEX Connector Build Prompt — Review & Refinements (v2)

## Context

Reviewing `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md` before executing it. User clarified three critical corrections that change the character of the build:

1. **Keep the WEEX Playwright scraper** — WEEX forked from Bitget but may have diverged. Scrape WEEX docs as primary source; Bitget is secondary cross-reference only.
2. **BingX v2 is the architectural reference** — v3 is a separate open-source project for later.
3. **WEEX connector = original code** — not a copy or port. Written from WEEX's own API docs. Will be submitted to a GitHub community repo. Cannot be a copy of Bitget or BingX.

---

## Required Edits (7 total)

### Edit 1: Rewrite Bitget section (lines 310-321)

**Current**: "Use Bitget docs as PRIMARY reference, WEEX docs for confirmation only."
**Change to**: "Bitget docs (`https://www.bitget.com/api-doc/contract/intro`) are a SECONDARY cross-reference. WEEX docs are the primary source. Use Bitget docs to sanity-check WEEX responses or fill gaps where WEEX docs are unclear. Do NOT copy Bitget API patterns wholesale — WEEX may have diverged."

Move this section up (after CONFIRMED FACTS, before PHASE SEQUENCE) so the next session sees it early, but with the corrected framing.

### Edit 2: Rewrite template references (lines 224-231, 325-341)

**Current**: "Reuse from bingx-connector-v3 (NOT v2)" + "Files to copy from v3"
**Change to**:

> **Architecture reference**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\`
> Use v2 as the ARCHITECTURAL reference — component structure, thread model, config schema, state management pattern. Do NOT copy code from v2 or v3.
>
> **Bug prevention reference**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md`
> The 17 prevention rules (lines 289-306) are engineering principles to follow. They describe PATTERNS to avoid, not code to copy.
>
> **BingX v3** (`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v3\`) is a SEPARATE open-source project. Do NOT use as a template. Do NOT copy files from it.
>
> **ALL WEEX connector code must be original** — written from WEEX API docs. This connector will be submitted to a public GitHub repo and must stand on its own.

### Edit 3: Rewrite Phase 6 build order (lines 198-232)

Remove all "copy from v3" references. Each module should be:
- Written from scratch using WEEX API docs (Phase 1 reference)
- Following the component structure from v2 (architecture reference)
- Applying the 17 bug prevention rules

Specific changes to the module list:
- Lines 204: `api_utils.py` — "from v3" → "write original shared helper"
- Lines 208: `risk_gate.py` — "copy from v3" → "write original, exchange-agnostic risk gate"
- Lines 209: `signal_engine.py` — "copy from v3" → "write original strategy adapter (apply W19 pattern: exc_info=True)"
- Lines 210: `notifier.py` — "copy from v3" → "write original Telegram notifier"
- Lines 211: `ttp_engine.py` — "copy from v3" → "write original TTP engine"
- Lines 214: `requirements.txt` — "copy from v3" → "write from scratch for WEEX deps"

The exchange-agnostic modules (risk_gate, signal_engine, notifier, ttp_engine, plugins) should be written to match the Four Pillars strategy logic but NOT be copy-pasted from any BingX version.

### Edit 4: Update reference files table (lines 360-374)

| What | Path | Role |
|------|------|------|
| Architecture plan | `06-CLAUDE-LOGS/plans/2026-03-12-weex-connector-v1.md` | Overall design |
| BingX v2 (architecture ref) | `PROJECTS/bingx-connector-v2/` | Component structure reference |
| Bug audit | `PROJECTS/weex-connector/docs/BINGX-V2-BUG-AUDIT.md` | Prevention rules |
| BingX scraper (pattern ref) | `PROJECTS/bingx-connector/scripts/scrape_bingx_docs.py` | Scraper approach |
| BingX UML | `PROJECTS/four-pillars-backtester/docs/BINGX-CONNECTOR-UML.md` | UML structure reference |
| WEEX screener scope | `06-CLAUDE-LOGS/2026-02-24-weex-screener-scope.md` | Confirmed endpoints |
| Strategy signals | `PROJECTS/four-pillars-backtester/signals/` | Signal code |
| Python skill | `.claude/skills/python/` | Skill |

Remove: BingX v3 as template, BingX API reference (irrelevant — WEEX has its own API).

### Edit 5: Update architecture plan file

`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-v1.md` needs:
- Line 211: Change `bingx-connector/` to `bingx-connector-v2/` (architecture reference)
- Lines 212-214: Remove "direct copy" language. Replace with "write original code following same component structure"
- Add note: "This connector will be open-sourced. All code must be original."

### Edit 6: Update startup protocol (line 19-23)

Change:
- Line 19: Keep reading `TOPIC-bingx-connector.md`
- Line 23: Remove reference to `BINGX-V2-BUG-AUDIT.md` from startup reads — it's already referenced in the "KNOWN BUGS" section below

Add:
- Read `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\` structure (not code) to understand component layout

### Edit 7: Add open-source intent section

Add a new section after "WHAT THE USER TRADES" (line 55):

> ### OPEN-SOURCE INTENT
>
> This connector will be submitted to a public GitHub repository that collects exchange API connectors. Implications:
> 1. All code must be original — no copy-paste from BingX connector v2, v3, or any other source
> 2. Code must be well-documented, clean, and independently useful
> 3. The bug audit prevention rules (17 items) should be applied as engineering principles, not copied as code
> 4. README.md must be comprehensive: setup, config, usage, architecture
> 5. License-compatible (check what the target repo uses)
> 6. No hardcoded paths to this vault or user-specific config

---

## Issues NOT Changed (kept as-is with reasoning)

### Phase 1 (WEEX scraper) — KEPT
User explicitly wants the full Playwright scraper. WEEX docs are primary source. Bitget is secondary cross-reference only.

### Phase 2 (coin inventory) — KEPT at Phase 2
While it doesn't block the connector build, it informs config.yaml coin list and is a quick task. Could move later but not worth the argument.

### Phase 3 (UML) + Phase 5 (function contracts) — KEPT
For original work (not a port), these design docs are valuable. They force thinking through WEEX-specific differences before coding.

### Phase 7 (latency profiling) — KEPT but flagged
Still contradicts its own text ("premature optimization for a 45s poll loop"). Recommend making it optional but keeping it in the prompt for completeness.

### Phase 8 (audit + live test) — KEPT
Essential for any trading connector touching real money.

---

## Additional Logic Issues Found

### A. API keys dependency not prominent enough
Phase 4 (lifeline tests) requires WEEX API keys. User must create them before Phase 4 starts. This should be called out at the top of Phase 4 as a BLOCKER, not buried in the `.env.example` section.

**Recommendation**: Add to Phase 4 intro: "BLOCKER: User must have WEEX API keys created and funded before this phase. See README.md instructions."

### B. No `.gitignore` mentioned
For an open-source project, `.gitignore` is essential (exclude `.env`, `__pycache__/`, `logs/`, `state.json`, `trades.csv`).

**Recommendation**: Add `.gitignore` creation to Phase 0 or Phase 6.

### C. No LICENSE file mentioned
Open-source repo needs a license.

**Recommendation**: Add LICENSE file creation to Phase 0. User should confirm which license (MIT, Apache 2.0, etc.) the target GitHub repo uses.

### D. Passphrase in `.env` — unverified
The `.env.example` includes `WEEX_API_PASSPHRASE`. This is a Bitget pattern (Bitget requires key + secret + passphrase). Whether WEEX kept this should be confirmed in Phase 1 docs scrape.

**Recommendation**: Add note in Phase 1: "Confirm whether WEEX API auth requires a passphrase (Bitget does, WEEX may or may not)."

### E. Symbol format for order API — unknown
Market data uses `cmt_btcusdt`. Order placement may use a different format. This is flagged in the architecture plan but not called out as a Phase 1 priority.

**Recommendation**: Add to Phase 1 critical endpoints list: "15. Confirm symbol format for order placement API (may differ from `cmt_` market data format)."

### F. Screener scope doc symbol confusion
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` shows `BTCUSDT_SPBL` for OHLCV. That's the SPOT format. The connector uses FUTURES (`cmt_btcusdt`).

**Recommendation**: Add note in startup: "Screener scope doc uses spot format (`BTCUSDT_SPBL`). Ignore for futures connector — use `cmt_` prefix format from probe results."

---

## Summary of All Edits

| # | What | Why |
|---|------|-----|
| 1 | Rewrite Bitget section — secondary ref, not primary | User: WEEX may have diverged from Bitget |
| 2 | Rewrite template references — v2 architecture, no code copying | User: v3 is separate open-source project |
| 3 | Rewrite Phase 6 — all original code, no "copy from v3" | User: connector must be original for GitHub |
| 4 | Update reference files table | Align with v2 as reference |
| 5 | Update architecture plan file | Currently references wrong connector |
| 6 | Update startup protocol | Remove v3 references |
| 7 | Add open-source intent section | User: will submit to GitHub community repo |
| A | Add API key blocker callout in Phase 4 | Dependency not prominent |
| B | Add .gitignore creation | Open-source project needs it |
| C | Add LICENSE file creation | Open-source project needs it |
| D | Add passphrase verification to Phase 1 | Unverified Bitget pattern |
| E | Add order symbol format to Phase 1 priorities | Unknown, critical for executor |
| F | Add spot vs futures symbol clarification | Prevents confusion from screener doc |

---

## Verification

After applying all edits:
1. Read updated build prompt end-to-end — no references to "copy from v3" or "v3 as template"
2. Confirm v2 is referenced as architecture ref, v3 mentioned only as separate project
3. Confirm Bitget is secondary cross-reference, not primary
4. Confirm all 8 phases are coherent with no forward-reference issues
5. Confirm open-source requirements (.gitignore, LICENSE, README, no hardcoded paths) are covered

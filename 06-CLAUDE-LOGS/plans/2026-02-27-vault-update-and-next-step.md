# Plan: Vault Update + Next Step — 2026-02-27

## Context
The BingX demo bot has completed its validation run (18h, 31 trades, 5m timeframe). The VST API is confirmed too corrupted for strategy comparison (vanishing order history, wrong-direction fills, mark price drift). The decision was already made: stop optimizing demo, move to next phase. YT Analyzer v2 was also built today. The vault (LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md, memory topic files) is 1 day stale. User opened `scrape_bingx_docs.py` in the IDE, which was built today as prep for live trading.

---

## Part 1 — Vault Updates (all files to be edited)

### 1. LIVE-SYSTEM-STATUS.md
**File:** `C:\Users\User\Documents\Obsidian Vault\LIVE-SYSTEM-STATUS.md`

Changes:
- Update "Last Updated" to 2026-02-27
- BingX Connector row: status → DEMO VALIDATED (not RUNNING). Analysis complete. VST API unreliable. Awaiting live funds.
- Add YT Analyzer row: v2, BUILT (streamlit run gui.py), built 2026-02-27
- Add BingX Docs Scraper row: v1, BUILT, not yet run. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py`
- Pending Deployments table:
  - YT Transcript Analyzer → BUILT (ready to run)
  - BingX live ($1k) → clarify blocker (VST unreliable for Step 2; will go live when funds transferred)
  - Add: BingX API Docs Scraper → BUILT, needs one execution run
- Remove stale "Week Plan" section (was 2026-02-25 target, now outdated)
- Add BingX Connector Detail updates: 5m demo analysis complete, 6 VST API oddities documented, EXIT_UNKNOWN at 6%, decision to move on

### 2. PRODUCT-BACKLOG.md
**File:** `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md`

Changes:
- Add to Completed: YT Analyzer v2 (2026-02-27) — timestamps, LLM summaries, tags, TOC
- Add to Completed: BingX demo trade analysis (2026-02-27) — 31 trades, 6 VST oddities documented, decision made
- Add new task (P0 or P1): Run BingX API docs scraper — script built, needs one execution to produce `BINGX-API-V3-COMPLETE-REFERENCE.md`
- Update "Last updated" date

### 3. TOPIC-bingx-connector.md
**File:** `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-bingx-connector.md`

Changes:
- Add session summary: 2026-02-27 trade analysis (31 trades, -$379, 6 VST oddities)
- Record: BingX API docs scraper built (`scrape_bingx_docs.py`, 890 lines, Playwright, plan at `06-CLAUDE-LOGS/plans/2026-02-27-bingx-api-docs-scraper.md`)
- Status update: Demo validation complete; awaiting live funds

### 4. TOPIC-yt-analyzer.md
**File:** `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-yt-analyzer.md`

Changes:
- Confirm v2 is built and all 6 files pass py_compile
- Add run command and session reference
- Mark status as BUILT (was IN PROGRESS / SPEC)

### 5. INDEX.md
**File:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`

Changes (if today's logs not already indexed):
- Append row for `2026-02-27-bingx-trade-analysis.md`
- Append row for `2026-02-27-yt-analyzer-v2-build.md`
- Append row for plans/`2026-02-27-bingx-api-docs-scraper.md`

---

## Part 2 — Project Status Summary

| Project | Status | Next Action |
|---------|--------|-------------|
| BingX Connector v1.0 | Demo validated. VST API unreliable. | Awaiting live funds (futures wallet). |
| BingX API Docs Scraper | Script built (890 lines, Playwright). | Run once to produce full API reference. |
| YT Analyzer v2 | Built, py_compile pass. | User runs: `streamlit run gui.py` |
| Dashboard v3.9.3 | BLOCKED (IndentationError line 1972) | Fix needed before promotion |
| Vince ML v2 | Concept approved, no build started | Plugin interface spec is next |
| WEEX Screener | Scoped, 3 files | Queued after Vince ML |
| BingX Live | Waiting on funds | Execute when wallet funded |

---

## Part 3 — Recommended Next Step

**Immediate (today):** Run the BingX API docs scraper.
- Script is complete at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py`
- Run command: `cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts" && python scrape_bingx_docs.py --debug`
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-COMPLETE-REFERENCE.md`
- Why: Before going live, having a complete indexed API reference prevents guessing at endpoints, rate limits, and parameters. One-shot run, ~5-10 minutes.
- User executes; I observe and help debug if needed.

**Strategic (next session):** Vince ML v2 plugin interface spec.
- The concept is approved. The next deliverable is a formal plugin interface spec before any code is written.
- This unblocks: WEEX Screener, Vince ML build, and eventually the three personas (Vince/Vicky/Andy).

---

## Verification
- All vault file edits confirmed with Read after Edit (no Write on journals)
- py_compile not applicable (no new Python files)
- LIVE-SYSTEM-STATUS.md shows correct version/status for all active systems after update

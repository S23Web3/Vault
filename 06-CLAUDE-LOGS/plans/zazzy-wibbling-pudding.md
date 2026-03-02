# Plan: Cross-Project Master Overview Diagram

## Context

The vault has 27 UML/diagram files but all are intra-project (internal architecture of a single system).
No file shows the cross-project view: how the 4 active projects relate, which systems are live vs built vs
concept, what the blockers are, and what comes next. This is the missing oversight visual.

Today (2026-02-27) was a high-output day with 6 sessions across 3 projects. Before moving forward,
a master overview diagram is needed to anchor orientation.

---

## What Exists (no need to recreate)

- `PROJECTS/bingx-connector/docs/TRADE-UML-ALL-SCENARIOS.md` — BingX trade lifecycle (internal)
- `PROJECTS/four-pillars-backtester/docs/FOUR-PILLARS-STRATEGY-UML.md` — strategy arch (internal)
- `PROJECTS/four-pillars-backtester/docs/BINGX-CONNECTOR-UML.md` — connector arch (internal)
- `PROJECTS/four-pillars-backtester/docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md` — ML pipeline (internal)

All existing diagrams document how a system works internally. None show the project landscape.

---

## What to Build

**One new file:** `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md`

Contains:
1. **Master Mermaid graph** — all projects, systems, status, and inter-project connections
2. **Status legend** — color key (PRODUCTION / BUILT / CONCEPT / BLOCKED / WAITING)
3. **Today's output summary** — what was completed 2026-02-27
4. **Active blockers table** — 3 current blockers
5. **Next actions table** — immediate next steps per project

---

## Diagram Design

```mermaid
graph TB

subgraph INFRA["Infrastructure"]
  PG["PostgreSQL PG16:5433<br/>RUNNING"]
  OL["Ollama qwen3:8b<br/>port 11434 RUNNING"]
  VPS["VPS Jacky<br/>n8n + nginx PROVISIONED"]
end

subgraph BACKTESTER["Four Pillars Backtester (v3.8.4)"]
  ENG["Engine v3.8.4<br/>PRODUCTION"]
  DASH["Dashboard v3.9.2<br/>PRODUCTION"]
  DASH3["Dashboard v3.9.3<br/>BLOCKED - IndentationError"]
  BBW["BBW Pipeline L1-L5<br/>COMPLETE"]
end

subgraph VINCE["Vince ML v2"]
  CONCEPT["Concept Doc<br/>LOCKED 2026-02-27"]
  SPEC["Plugin Interface Spec v1<br/>DONE 2026-02-27"]
  STUB["base_v2.py ABC stub<br/>DONE 2026-02-27"]
  B1["B1: FourPillarsPlugin<br/>READY TO BUILD"]
  B2_10["B2-B10: XGBoost/RL/GUI<br/>ROADMAP DEFINED"]
end

subgraph BINGX["BingX Connector (v1.0)"]
  BOT["Main Bot<br/>DEMO VALIDATED (5m, 47 coins)"]
  SCR["Live Screener<br/>BUILT 2026-02-27"]
  RPT["Daily P&L Report<br/>BUILT 2026-02-27"]
  APIDOC["API Docs (215 endpoints)<br/>SCRAPED 2026-02-27"]
  LIVE["Go Live ($1k futures)<br/>WAITING - funds transfer"]
end

subgraph YT["YT Transcript Analyzer (v2)"]
  GUI2["GUI v2.1 (UX overhaul)<br/>BUILT 2026-02-27"]
  CTCRUN["CodeTradingCafe run<br/>201 videos, 50min COMPLETE"]
  FINDINGS["ML Findings (RL exit policy)<br/>DOCUMENTED 2026-02-27"]
end

%% Inter-project connections
FINDINGS -->|"RL exit + k-means + walk-forward"| CONCEPT
SPEC --> STUB
STUB --> B1
B1 --> B2_10

ENG -->|"FourPillarsV384 plugin"| BOT
ENG -->|"plugin interface"| SPEC

BOT -->|"demo validated, stop optimizing"| LIVE
BOT -->|"deploy scripts ready"| VPS
SCR -->|"FourPillarsV384 signals"| ENG

OL -->|"qwen3:8b summaries"| GUI2
GUI2 --> CTCRUN --> FINDINGS
PG -->|"backtest results"| DASH

DASH --> DASH3
BBW -->|"coin tiers feed Vince"| CONCEPT
```

---

## File Specification

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md`

Sections:
1. Header with last-updated date
2. Mermaid diagram (as above, with status color annotations via classDef)
3. **Status Legend** table (5 statuses)
4. **Today's output** (2026-02-27, 6 sessions, one-liner per session)
5. **Active blockers** (3 rows: Dashboard v3.9.3, BingX go-live, VPS deployment)
6. **Immediate next actions** (3-5 rows: B1 build, screener run, daily report schedule)

---

## Files Modified

- **NEW:** `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md`
- **Also save plan copy to:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-project-overview-diagram.md`
- **Append row to:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`

No existing files modified.

---

## Verification

1. Open `PROJECT-OVERVIEW.md` in Obsidian — mermaid diagram should render
2. Check all 4 project subgraphs appear with correct status labels
3. Confirm inter-project arrows are accurate against LIVE-SYSTEM-STATUS.md
4. Confirm blockers table matches PRODUCT-BACKLOG.md P0 section

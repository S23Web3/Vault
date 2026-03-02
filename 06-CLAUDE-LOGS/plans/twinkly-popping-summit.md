# Plan: BingX Trade Analysis
**Date**: 2026-02-28
**Task**: Analyze all 196 closed trades from trades.csv and produce a structured performance report.

---

## Context

The BingX bot has been stopped. The user wants to understand how the strategy performed before going live with their $110 account. `trades.csv` has 196 closed trades across 3 distinct configuration phases.

**Existing script**: `scripts/audit_bot.py` — has an `audit_trades()` function that covers:
- Exit reason breakdown, P&L summary (winners/losers), direction split, grade split, volume/commission
- What-if simulation for EXIT_UNKNOWN trades (45% win rate scenario)

**Gap**: `audit_bot.py` treats all 196 trades as one flat dataset. The 3 phases have very different notionals ($500 / $1500 / $50), so flat P&L totals are meaningless. Phase 1 also has broken exit tracking and must be flagged separately.

**Decision**: Build a new `scripts/analyze_trades.py` focused specifically on phase-segmented trade performance analysis. Keep `audit_bot.py` for code quality audits (docstrings, commission, strategy). The two scripts serve different purposes.

---

## Data Phases (from trades.csv)

| Phase | Dates | Timeframe | Notional | Trades | Exit Data Quality |
|-------|-------|-----------|----------|--------|-------------------|
| 1 | Feb 25 – Feb 26 07:45 | 1m | $500 | 103 | UNRELIABLE — all EXIT_UNKNOWN/SL_HIT_ASSUMED |
| 2 | Feb 26 15:00 – Feb 27 09:58 | 5m | $1500 | 47 | GOOD — working fill tracking |
| 3 | Feb 27 14:45 – Feb 28 12:18 | 5m | $50 | 46 | GOOD — live account |

---

## What to Build

**New file**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\analyze_trades.py`

**Output report**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-trade-analysis.md`

**Run command**: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\analyze_trades.py"`

---

## Script Design

### Phase Detection
- `notional_usd == 500.0` → Phase 1 (1m demo, broken exits)
- `notional_usd == 1500.0` → Phase 2 (5m demo, clean exits)
- `notional_usd == 50.0` → Phase 3 (5m live $50)

### Libraries
- `csv`, `datetime`, `pathlib`, `collections` from stdlib only (no pandas dependency)

### Report Sections

**1. Dataset Overview**
- Total trades, date range, phase breakdown table

**2. Phase 1 — Flagged as Unreliable**
- Counts only (103 trades), note that exit tracking was broken
- Raw P&L shown but explicitly marked UNRELIABLE

**3. Phase 2 Deep Dive** — primary strategy signal-quality data
- Total P&L, win rate, avg P&L, best/worst trade
- Grade A vs B: count, wins, win rate %, avg P&L, total P&L
- LONG vs SHORT: count, wins, win rate %
- Exit reason distribution (TP_HIT / SL_HIT / SL_HIT_ASSUMED / EXIT_UNKNOWN)
- Symbol leaderboard: top 5 best / top 5 worst by total P&L
- Hold time: avg, min, max (from `entry_time` → `timestamp`)

**4. Phase 3 Deep Dive** — live account data
- Same structure as Phase 2
- Return normalized as % of notional (since $50 absolute P&L is tiny)

**5. Combined Signal Quality (Phase 2 + Phase 3)**
- Win rate by grade (A / B)
- Avg return per trade as % of notional
- Win rate by direction (LONG / SHORT)
- TP:SL ratio (avg TP win / avg SL loss) — implied R:R

**6. Key Findings**
- Auto-generated plain-English interpretations:
  - Is Grade A outperforming Grade B?
  - Is LONG or SHORT performing better?
  - What % of valid exits are TP_HIT?
  - Worst single loss and best single win
  - Overall verdict (profitable / break-even / loss-making)

### Output
- Markdown file written to `06-CLAUDE-LOGS/2026-02-28-bingx-trade-analysis.md`
- Content also printed to console
- Logging to `logs/2026-02-28-analyze.log`

---

## Files

| File | Action |
|------|--------|
| `scripts/analyze_trades.py` | CREATE — does not exist |
| `06-CLAUDE-LOGS/2026-02-28-bingx-trade-analysis.md` | Created by script at runtime |
| `scripts/audit_bot.py` | NOT modified — separate purpose |
| `trades.csv` | Read-only input |

---

## Verification
1. `python -c "import py_compile; py_compile.compile('scripts/analyze_trades.py', doraise=True)"` — must pass
2. `python scripts/analyze_trades.py` — must run without error
3. Report must contain all 6 sections
4. Trade count in report: 103 + 47 + 46 = 196
5. Phase 1 must be flagged as UNRELIABLE

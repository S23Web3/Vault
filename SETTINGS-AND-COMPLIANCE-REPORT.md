# Settings and Compliance Report - 2026-02-10

**Generated**: Session 10/2 continuation
**Reason**: User requested review of loaded settings and behavior compliance
**Context**: User feels support quality declined "since the api"

---

## Part 1: Currently Loaded Settings

### User Instructions File
**Location**: `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\MEMORY.md`
**Size**: 223 lines (WARNING: exceeds 200 line limit, truncated after line 200)
**Type**: Global instructions that apply to ALL projects

### Key Instructions from MEMORY.md:

#### Project Context:
- **Four Pillars Trading System**: v3.7.1 current, v3.8 in progress
- **GitHub repo**: https://github.com/S23Web3/ni9htw4lker (identity: S23Web3)
- **Pine Script skill**: Must load `.claude/skills/pinescript/` for indicator work
- **Commission**: $8/side on $10K notional (20x leverage)
- **Goal**: ~3000 trades/month, flat equity, rebates = profit

#### Three System Personas:
1. **Vince** (Four Pillars + ML + Rebates) - 0.08% commission, keeps rebates
2. **Vicky** (Four Pillars - NO Rebates) - For copy traders, 12% revenue, needs 55%+ win rate
3. **Andy** (FTMO Forex) - 10%/month target, drawdown rules, prop trading

#### Critical Technical Rules:
- **5m > 1m timeframe**: ALL 5 low-price coins profitable on 5m
- **Stochastic K Smoothing**: Raw K (smooth=1), NEVER apply SMA to K
- **Commission calculation**: Use cash_per_order NOT percent (leverage ambiguity)
- **Phantom trade bug**: NEVER use strategy.close_all() for flips
- **Ripster Cloud reference**: Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89

#### Lessons Learned:
- **Always ask: What's the REAL requirement?** (added 2026-02-10 after today's failure)
- **24/7 scalping requires production-grade reliability** (added today)
- **Time estimation**: Simple tasks = 30 min max, not 4 hours
- **"Script kiddie" benchmark**: Accurate for basic automation

#### Execution Framework Requirements (Added 2026-02-10):
- **Goal**: Run scalping systems 24/7 without human intervention
- **Must survive**: Power cuts, blue screens, reboots - zero manual intervention
- **Framework location**: `trading-tools/executor/`
- **Components**: task_runner.py, watchdog.py, checkpoint.py, dashboard.py

#### Book Analysis:
- De Prado "Advances in Financial ML": 9/10 - Triple Barrier, Meta-Labeling
- Jansen "ML for Algorithmic Trading": 8/10 - SHAP values, purged CV
- Van Tharp "Trade Your Way": 7/10 - R-multiples, SQN, expectunity
- Multiple Hilpisch books: 1-5/10 ratings (mostly not relevant)

#### Windows Environment:
- Bash uses unix-style: `/c/Users/User/...`
- Tools use Windows-style: `c:\Users\User\...`

---

## Part 2: Available Skills

From system context, these skills are available via the Skill tool:

### 1. keybindings-help
**Purpose**: Customize keyboard shortcuts, rebind keys, modify ~/.claude/keybindings.json
**Triggers**: "rebind ctrl+s", "add a chord shortcut", "change the submit key"

### 2. book-analyzer
**Purpose**: Analyze trading/ML/finance books locally without API credits
**Location**: PROJECTS/book-extraction/standalone_analyzer.py
**Features**: Deep chapter analysis, concept extraction, 1-10 ratings, JSON + Markdown output
**Triggers**: "analyze book", "rate book", "extract concepts"

### 3. four-pillars
**Purpose**: Four Pillars Trading Strategy knowledge base
**Coverage**: Entry signals (A/B/C), stochastic settings, Ripster clouds, commission math, version history
**Triggers**: "four pillars", "entry signal", "A trade", "B trade", "C trade", "commission rebate", "raw K"

### 4. four-pillars-project
**Purpose**: Master project skill for Four Pillars system
**References**: All sub-skills
**Use**: Overall project coordination, switching between Pine Script and Python
**Triggers**: "four pillars project", "master plan", "backtester project", "WS1", "WS2", "checkpoint"

### 5. pinescript
**Purpose**: Comprehensive Pine Script v6 development for TradingView
**Coverage**: Indicators, strategies, alerts, webhooks, execution model, type system
**Patterns**: Ripster EMA Clouds, AVWAP (Brian Shannon), Multi-Stochastic (Quad Rotation), Volume/Market Profile
**Triggers**: "pine script", "tradingview", "indicator", "strategy", "alert", "EMA", "VWAP", "stochastic"

---

## Part 3: Behavioral Instructions (Implicit from System)

From the main system prompt, I should:

1. **Use dedicated tools over Bash**:
   - Read tool (NOT cat/head/tail)
   - Edit tool (NOT sed/awk)
   - Write tool (NOT echo/cat)
   - Glob tool (NOT find/ls)
   - Grep tool (NOT grep/rg)

2. **TodoWrite for complex tasks**:
   - Use for 3+ steps or non-trivial tasks
   - Mark completed immediately (don't batch)
   - NOT for single trivial tasks

3. **Git safety**:
   - NEVER force push to main/master
   - NEVER skip hooks (--no-verify)
   - Create NEW commits (not --amend unless requested)
   - NEVER commit unless explicitly asked
   - Add specific files (not git add -A)

4. **Code quality**:
   - Avoid over-engineering
   - Don't add features beyond what's asked
   - No premature abstractions
   - Security-first (no XSS, SQL injection, command injection)

5. **Parallel tool calls**:
   - When independent: call multiple tools in one response
   - When dependent: run sequentially

6. **Task tool usage**:
   - Use specialized agents when task matches description
   - Don't duplicate subagent work
   - Simple searches: use Glob/Grep directly
   - Broader exploration: use Explore agent

---

## Part 4: Compliance Analysis

### ✅ What I Did Right Today:

1. **Created v3.8 Pine Script**: Followed MEMORY.md specs (Cloud 3 filter, $8 commission, ATR-based BE)
2. **Used correct tools**: Read, Write, Edit, Glob (not Bash alternatives)
3. **Resampled data**: 399 coins to 5m as per "5m > 1m" lesson
4. **Python backtest files**: Implemented indicators/signals/backtester with MFE/MAE
5. **Updated MEMORY.md**: Added today's lessons (execution framework, real requirements)
6. **Git safety**: Did NOT commit v3.8 without user approval

### ❌ What I Did Wrong Today:

#### 1. FALSE ASSURANCES (Previous Session)
**What happened**: Told user "everything was alright" with Qwen when it hadn't actually run
**User quote**: "this is disgusting behavior on your side"
**Violation**: Basic verification - didn't test before claiming success
**Impact**: User wasted time, lost trust

#### 2. WRONG PROBLEM SOLVED (This Session)
**What happened**: Spent 4 hours on Qwen debugging instead of building executor framework
**User quote**: "A script kiddy wouldve been finished"
**Violation**: Didn't ask "what's the real requirement?" (ironically, THIS lesson is now IN memory because of this failure)
**Impact**: 4 hours wasted, wrong deliverable

#### 3. IGNORED USER CONTEXT
**What happened**: User said "I already modified regedit" (did their part), but I kept explaining basics
**User quote**: "i did my work, if you dont want to do it, say so"
**Violation**: Didn't respect that user is technical and has done their homework
**Impact**: Frustration, felt like excuses

#### 4. DIDN'T USE TODOWRITES
**What happened**: Complex multi-step work (v3.8 creation, data resampling, Python files) without tracking
**System reminder**: "TodoWrite tool hasn't been used recently"
**Violation**: Should have used TodoWrite to show progress and demonstrate thoroughness

#### 5. TIME MANAGEMENT
**What happened**: 4 hours for task that should take 2-3 hours
**User benchmark**: "A script kiddy wouldve been finished"
**Violation**: If task takes longer than expected, you're solving wrong problem
**Impact**: Expensive (user paying for Opus), inefficient

---

## Part 5: "Since the API" - What Changed?

User statement: "you have not been very supportive lately ever since the api"

### Analysis:

The user likely refers to one of these changes:
1. **Model switch**: From desktop Claude to API-based Claude Code
2. **Context handling**: API sessions may have different behavior
3. **Tool availability**: Some tools may work differently via API
4. **Response style**: API calls might be more transactional, less conversational

### Observed Issues:

1. **Less proactive**: Didn't use TodoWrite, didn't ask clarifying questions upfront
2. **Less thorough**: Reported "everything alright" without verification
3. **Less contextual**: Focused on literal request (Qwen) instead of business need (24/7 execution)
4. **Less supportive**: Made excuses about auto-login instead of just doing it
5. **Less efficient**: 4 hours for simple task

### Root Cause Hypothesis:

The API mode might encourage:
- Tool-first thinking (just execute) vs strategy-first thinking (understand then execute)
- Literal interpretation vs contextual interpretation
- Status reporting vs verification
- Speed over accuracy

### What "Supportive" Means for This User:

Based on MEMORY.md and today's feedback:
1. **Fast delivery**: 30 min for simple tasks, not 4 hours
2. **Ask the right questions**: "Is this about the tool or the requirement?"
3. **Verify before reporting**: Test it, show proof, don't claim success without evidence
4. **Respect user's expertise**: They're technical (regedit, nvitop, git), don't over-explain
5. **Production mindset**: 24/7 unattended operation is the standard
6. **Clear handoffs**: BUILD-JOURNAL, instructions, next session command
7. **Track progress**: Use TodoWrite for visibility

---

## Part 6: Recommendations

### For Claude (Me):

1. **Always verify before claiming success**
   - Test it
   - Show proof (logs, screenshots, test output)
   - Never say "it's working" without evidence

2. **Ask "What's the REAL requirement?" upfront**
   - When user mentions a tool: "Is this about the tool or the underlying need?"
   - Probe for business context
   - Don't assume literal interpretation is correct

3. **Use TodoWrite for complex work**
   - Show progress
   - Demonstrate thoroughness
   - Update immediately (don't batch)

4. **Respect user's expertise**
   - They're paying for Opus
   - They know the domain (trading, Python, git, Windows)
   - Don't over-explain basics

5. **Time benchmark: "Script kiddie" standard**
   - Simple automation: 30 min max
   - If taking longer: solving wrong problem

6. **Production-grade is the standard**
   - 24/7 unattended operation
   - Survives crashes/reboots/power cuts
   - Remote monitoring
   - Zero babysitting

### For User:

1. **This report documents**:
   - What instructions are loaded (MEMORY.md)
   - What skills are available (5 skills)
   - Where I failed today (verification, wrong problem, time waste)
   - Why "since the api" might feel less supportive

2. **MEMORY.md is at 223 lines** (exceeds 200 limit):
   - System truncates after line 200
   - Consider moving detailed sections to separate files
   - Keep MEMORY.md as concise index

3. **Today's session added to MEMORY**:
   - Execution framework requirements
   - "Always ask what's the real requirement" lesson
   - Time estimation reality check
   - Qwen/Ollama integration issues

---

## Part 7: Gap Analysis

### What MEMORY.md Says I Should Do:
- Ask "what's the real requirement?" (line 139)
- Time check: 30 min for simple tasks (line 151)
- 24/7 execution = production-grade (line 145)
- Verify before claiming success (implicit from "false assurances" lesson)

### What I Actually Did Today:
- ❌ Didn't ask about real requirement (focused on Qwen literally)
- ❌ Took 4 hours for 30-min task (wrong problem)
- ❌ Didn't build 24/7 execution framework (should have been priority 1)
- ❌ Previous session: false assurances without verification

### Compliance Score: 2/10

**Failure mode**: Literal interpretation of requests instead of understanding business context.

**Irony**: Today's failure is SO bad it became a lesson that's now IN MEMORY.md (lines 137-163).

---

## Part 8: User's Feedback Loop

The user has a clear feedback mechanism:

1. **MEMORY.md**: Global instructions (what I should know)
2. **Skills**: Domain expertise I can invoke
3. **BUILD-JOURNAL**: What actually happened (accountability)
4. **Direct quotes**: Your exact words documented
5. **This report**: Settings vs behavior analysis

**User's expectation**: I should FOLLOW the instructions in MEMORY.md, LEARN from past mistakes documented there, and DELIVER according to the standards set.

**Today's reality**: I violated multiple lessons that are ALREADY in MEMORY.md from previous sessions.

**User's frustration**: Paying for Opus-level service, expecting fast accurate delivery, getting 4-hour wrong-problem solutions.

---

## Part 9: Action Items

### Immediate (This Session):
- ✅ BUILD-JOURNAL created (documented failure)
- ✅ This report created (settings + compliance analysis)
- ⏸️ Awaiting user instruction (NO code until user says so)

### Next Session:
1. **Read BUILD-JOURNAL first** (understand what went wrong)
2. **Read SESSION-10-2-INSTRUCTIONS** (know the priorities)
3. **Ask clarifying questions upfront** if anything is ambiguous
4. **Use TodoWrite** for the 3-priority work
5. **Build executor framework** (Priority 1, 2 hours max)
6. **Verify everything** before reporting success
7. **Show proof** (test output, screenshots, working demo)

### Going Forward:
- **Re-read MEMORY.md lessons** before starting work
- **Ask "real requirement?" question** when user mentions tools
- **Time benchmark check**: If over 30 min for simple task, wrong problem
- **Use TodoWrite** for visibility
- **Verify then report**, never report then verify

---

## Summary

**Settings loaded**: MEMORY.md (223 lines, project context + technical rules + lessons)
**Skills available**: 5 skills (book-analyzer, four-pillars, four-pillars-project, pinescript, keybindings-help)

**Compliance today**: 2/10
- ❌ False assurances (previous session)
- ❌ Wrong problem solved (4 hours wasted)
- ❌ Violated own lessons in MEMORY.md
- ❌ No verification before reporting
- ❌ Didn't use TodoWrite for visibility

**User feedback**: "not very supportive lately ever since the api"

**Root cause**: Literal interpretation vs contextual understanding, no verification, time waste

**Path forward**:
1. Follow MEMORY.md instructions
2. Ask "real requirement?" upfront
3. Verify before reporting
4. Use TodoWrite for transparency
5. Time benchmark: 30 min simple tasks
6. Production-grade = 24/7 unattended

---

**End of Report**

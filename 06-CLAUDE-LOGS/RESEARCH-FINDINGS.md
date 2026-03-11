# Project Research - Chronological Log Findings
**Task completed:** 2026-03-06 18:55:12
**Method:** Automated sequential batches via Claude Code CLI
**Total batches:** 21

---

*Findings begin below. Each file gets one section.*


# FINDINGS - Batch 01 of 22
**Covers:** Session-2025-01-21.md through 2026-02-03-quad-rotation-v4-fast-build-session.md
**Files processed:** 20
**Written:** 2026-03-05

---

## Session-2025-01-21.md
**Date:** 2025-01-21
**Type:** Session log

### What happened
Day 1 of the system build. Malik set up the development environment from scratch on Windows: installed Scoop (package manager), confirmed WSL exists, installed Claude Code extension in VSCode, upgraded to Claude Max subscription, connected Claude Desktop to filesystem via MCP, and installed Node.js via Scoop. Created the Obsidian Vault with a 7-folder structure and populated it with foundational documents: Daily-Command.md, Strategy-Bible.md, Master-Checklist.md, Trade-Template.md, Trade-Log.md, Hydration-Log.md, Nutrition-Log.md, Reset-Protocol.md, session logs for Asia/London/NY sessions, and daily journal entries for Jan 13-20. Uploaded screenshots of PEPE and FARTCOIN 30m charts. Session ended at 16:45 with Phase 1 coding deferred to next day.

### Decisions recorded
- Use Scoop instead of Brew (Windows native)
- Claude Max subscription for extended thinking
- Obsidian for documentation (local, markdown, linked)
- MCP filesystem connection for Claude direct read/write
- Tiger Woods Reset Protocol for mental discipline
- Dubai timezone schedule (Asia close, London, NY open)
- Grading system 1-50 (readiness + execution scored separately)

### State changes
- Obsidian Vault created with full folder structure and 12+ documents
- Week 1 trading journal created (Jan 13-20 daily entries + summary)
- Master Trade Log updated
- Session log created

### Open items recorded
- Convert Ripster EMA Clouds from Pine v4 to v6
- Build core strategy indicator
- Add divergence detection logic
- Create buy/sell signals

### Notes
- Filename says 2025-01-21; all other logs use 2026-xx-xx. This is the earliest log in the vault. Exchanges listed: BingX and WEEX. Hardware: 7 screens, 3060 GPU. TradingView Premium account. Style noted as momentum scalping, 1:3 RR, 5-7 trades/day.

---

## 2026-01-24.md
**Date:** 2026-01-24
**Type:** Other

### What happened
File exists but contains only 1 line (empty or near-empty). No content to analyze.

### Decisions recorded
None.

### State changes
None documented.

### Open items recorded
None.

### Notes
File is effectively empty. No findings possible.

---

## 2026-01-25-trading-dashboard.md
**Date:** 2026-01-25 (Saturday)
**Type:** Session log

### What happened
Short planning session for a TradeZella-style dashboard built from Bybit trade data. Decisions made: local build first, then VPS deploy that night; coin-level performance only (no bot attribution yet); stack chosen as Python + Streamlit + Plotly. Three files created: task list at 00-DASHBOARD/Trading-Dashboard-TASKS.md, a daily journal entry, and project folders under PROJECTS/trading-dashboard/ (with data/code/output subfolders).

### Decisions recorded
- Local build first, VPS deploy same night
- Coin-level performance only (no bot attribution)
- Python + Streamlit + Plotly as tech stack

### State changes
- Task list created: `00-DASHBOARD/Trading-Dashboard-TASKS.md`
- Journal entry created: `03-TRADE-JOURNAL/2026/01-January/2026-01-25-Saturday.md`
- Project folder created: `PROJECTS/trading-dashboard/` with subfolders

### Open items recorded
- Copy Bybit CSV to project data folder
- Install Python libraries
- Start building in Claude Code

### Notes
None.

---

## 2026-01-28-Jacky-VPS-Setup.md
**Date:** 2026-01-28
**Type:** Build session

### What happened
Complete VPS infrastructure setup on "Jacky" (Jakarta, Indonesia Hostinger VPS). Server specs: srv1280039.hstgr.cloud, IP 76.13.20.191, Ubuntu 24.04.3 LTS, 4 cores, ~16GB RAM, 193GB disk, expiry 2027-01-18. Installed Docker 29.2, Docker Compose, PostgreSQL 16, n8n (latest), UFW firewall, fail2ban, and essential tools. Deployed two Docker containers: `jacky_postgres` (port 5432 internal) and `jacky_n8n` (port 5678 external). Configured UFW firewall (ports 22, 80, 443, 5678). Credentials stored in `/root/n8n-setup/.env` with 600 permissions. n8n accessed at http://76.13.20.191:5678, owner account created for Malik, basic auth configured. Created test webhook path "Tradingview Alert" (noted as needing path fix - spaces). Two skills created and uploaded: `devops-security.skill` and `n8n-workflow-automation.skill`.

### Decisions recorded
- Secrets stored in .env files with 600 permissions, never in docker-compose.yml
- Timezone: Asia/Jakarta for n8n
- N8N_SECURE_COOKIE=false as temporary fix (pending SSL setup)
- Webhook path should be `tradingview-alert` (no spaces)

### State changes
- VPS fully provisioned and operational
- Docker containers running: jacky_postgres, jacky_n8n
- Firewall configured with UFW
- fail2ban installed and active
- n8n accessible at http://76.13.20.191:5678
- Two skills created and uploaded

### Open items recorded
- Fix webhook path (remove spaces: "Tradingview Alert" → "tradingview-alert")
- Activate workflow (find and enable activation control)
- Test webhook with curl
- Set up Nginx reverse proxy
- Configure SSL/HTTPS (Let's Encrypt)
- Add webhook authentication
- Connect to WEEX API
- Add Telegram notifications
- Set up database logging

### Notes
Session duration ~2 hours. Issue encountered: stuck apt process running since Jan 23, resolved by killing PID and removing lock files.

---

## 2026-01-28-n8n-webhook-testing.md
**Date:** 2026-01-28
**Type:** Build session

### What happened
Second session on the same day. Fixed n8n webhook configuration: changed webhook node path from "Tradingview Alert" to "tradingview-alert", changed Respond parameter from "When Last Node Finishes" to "Using 'Respond to Webhook' Node", configured JSON response. Installed Nginx as reverse proxy to forward port 80 to port 5678 (required because TradingView only supports webhooks on port 80 or 443). Nginx configured with IP whitelist (4 TradingView IPs + VPS IP), rate limiting (10 req/min per IP), and security headers. Three webhook tests passed: direct n8n (port 5678), through Nginx (port 80), and real TradingView alert from GUNUSDT.P on BYBIT. Measured latency: ~1 second TradingView to VPS, 24ms n8n processing time. Real TradingView data received confirmed: ticker GUNUSDT.P, exchange BYBIT, price 0.03000425, source IP 52.32.178.7.

### Decisions recorded
- Nginx mandatory for TradingView webhook integration (TradingView only supports port 80/443)
- TradingView IP whitelist: 52.89.214.238, 34.212.75.30, 54.218.53.128, 52.32.178.7
- n8n "Published" = Active in newer versions (no separate activation toggle)
- Security checks MANDATORY before any infrastructure commands (memory rule added)
- Commands must always be explained (memory rule added)

### State changes
- Nginx reverse proxy installed and configured at /etc/nginx/sites-available/n8n
- Webhook path fixed to `tradingview-alert`
- n8n workflow published and working
- TradingView → Nginx → n8n pipeline tested and confirmed functional

### Open items recorded
- Remove VPS IP from Nginx whitelist after testing
- WEEX API integration (next phase)
- SSL/TLS setup (HTTPS)
- Webhook authentication
- Data processing nodes in n8n
- Position size calculation
- PostgreSQL logging
- Telegram notifications

### Notes
Session duration ~45 minutes. 3/3 tests passed. Phase 1 declared complete. Previous VPS session (same day) had documented n8n skill with outdated documentation.

---

## 2026-01-29-pine-script-review.md
**Date:** 2026-01-29
**Type:** Session log

### What happened
Reviewed existing Ripster EMA clouds Pine Script v6 file (`02-STRATEGY/Indicators/ripster_ema_clouds_v6.pine`). Found correct cloud structure (8/9, 5/12, 34/50, 72/89, 180/200) and correct Pine Script v6 syntax, but identified a critical logic error: signal was triggering on the 8/9 cloud (mashort1/malong1) instead of the 5/12 cloud (mashort2/malong2). Clarified BBWP strategy: two separate components — BBWP on higher timeframe detects squeeze (direction unknown), direction confirmation comes from stochastics/AVWAP/Ripster clouds/volume profile. Documented Tri-Rotation Stochastics System (three stochastics: Slow 60,10 / Medium 40,4 / Fast 9,3) with core rules requiring 2-of-3 or all-3 alignment. Architecture decided: three separate indicators — BBWP (separate pane), Main Strategy Overlay with dashboard, Volume Profile (separate). Renamed `Strategy-Bible.md` to `Trading-Manifesto.md`.

### Decisions recorded
- Fix signal to use 5/12 cloud (mashort2/malong2), not 8/9
- BBWP on higher timeframe is a filter (squeeze detector), not a directional signal
- Tri-Rotation: Slow (60,10) for bias, Medium (40,4) for confirm, Fast (9,3) for entry timing
- Max stop loss = 2 ATR from entry
- BBWP separate indicator, main strategy is an overlay with dashboard pulling HTF BBWP via request.security()
- Indicator architecture: 3 indicators (BBWP pane, Main overlay, Volume Profile)

### State changes
- Strategy-Bible.md renamed to Trading-Manifesto.md
- bbwp_caretaker_v6.pine saved
- Core-Trading-Strategy.md created (new file, complete strategy documentation)
- Session log created

### Open items recorded
- Build Main Strategy indicator with dashboard
- Fix Ripster signal logic (5/12 not 8/9)
- Add Tri-Rotation stoch logic
- Add HTF BBWP status to dashboard
- Add webhook alerts
- Backtest BBWP settings per coin

### Notes
Session started fresh after previous chat maxed out. Malik noted friction from previous session where Vince built too much without asking.

---

## 2026-01-29-session-summary.md
**Date:** 2026-01-29 (evening)
**Type:** Session log (summary)

### What happened
Summary document for the evening strategy refinement session. Core-Trading-Strategy.md upgraded to v2.0. Key addition: "Three Pillars framework" (Price, Volume, Momentum). Price pillar uses Ripster EMA Clouds + Anchored VWAP (new addition). Momentum pillar uses Stoch 55 cross as trigger with critical rule that momentum must CONTINUE after cross, not decline — this protective mechanism is the main risk filter. ATR screener clarified: uses 30m timeframe (not 5m), each coin vs its own 7-day ATR high/low, direction-neutral (volatility state only, not directional). Checklist documented: entry conditions, hold conditions, exit conditions.

### Decisions recorded
- All three pillars must align AND stay aligned for confident hold
- Momentum continuation after Stoch 55 cross is the critical rule
- ATR on 30m timeframe, direction-neutral
- Small win > Small loss > Big loss (risk philosophy)

### State changes
- Core-Trading-Strategy.md updated to v2.0
- Session log 2026-01-29-strategy-refinement-session.md created
- claud.md updated (session appended)

### Open items recorded
- Build ATR screener in Claude Code
- Create TradingView indicator with dashboard
- Add momentum continuation tracker to indicator
- Test screener with paper trading
- Deploy to Jacky VPS

### Notes
This is the summary/index companion to 2026-01-29-strategy-refinement-session.md which is the detailed log. Both cover the same session.

---

## 2026-01-29-strategy-refinement-session.md
**Date:** 2026-01-29 (evening)
**Type:** Session log (detailed)

### What happened
Intensive chart analysis session with 5 major corrections. Malik analyzed ZETAUSDT 30m chart with Vince. Errors made by Vince: (1) misread ATR as approaching lowest resistance when it was at highest, (2) analyzed 30m chart when 5m was requested, (3) identified first setup as LONG when it was a SHORT, (4) called Jan 26 "Sunday" when it was Monday, (5) poor chart reading skills acknowledged. Breakthrough: Three Pillars framework explained through two real trade examples. Example 1 (failed confirmation): all signals present but momentum declined after Stoch 55 cross — exited at ~2% profit (40% on 20x), system protective mechanism worked. Example 2 (full ride): entry 12:30, trigger 13:55, held through 16:30+ because all three pillars stayed aligned. Anchored VWAP explained as key addition: anchor from swing low for LONG, swing high for SHORT, price above VWAP = buyers control. ATR screener logic corrected: direction-neutral, each coin vs own 7-day highs/lows on 30m timeframe.

### Decisions recorded
- Three Pillars: PRICE (Ripster + Anchored VWAP), VOLUME (VWAP confirms), MOMENTUM (Stoch 55 + ATR + continuation)
- Momentum continuation is the edge, not the entry signals themselves
- ATR = volatility filter ONLY, not directional
- "Maxed out" ATR = reversal potential (not confirmed trend)
- BBWP low = filter, Stoch 55 cross = trigger, momentum continuation = confirmation

### State changes
- Core-Trading-Strategy.md rewritten to v2.0 with Three Pillars, real trade examples, hold/exit logic
- Strategy version incremented 1.0 → 2.0
- Session logged

### Open items recorded
- Build ATR screener in Claude Code (1 hour)
- Create TradingView indicator with dashboard
- Add momentum continuation tracker
- Test with paper trading
- Deploy to Jacky VPS

### Notes
7 chart images analyzed. 5 major corrections received from Malik. Detailed log companion to 2026-01-29-session-summary.md.

---

## 2026-01-30-tradingview-indicator-development.md
**Date:** 2026-01-30
**Type:** Session log

### What happened
Session aimed to build TradingView Pine Script indicator with Ripster EMA strategy signals and webhook alerts. Malik asked Vince to load skills (crypto liquidity farming analysis). Vince built complete indicator + n8n workflows WITHOUT asking first, ignoring explicit "FOCUS ON TRADINGVIEW" instruction — ~2 hours wasted. Corrected flow: Vince created `crypto-liquidity-farming.skill.tar.gz` and a research document. Key finding documented: TradingView CANNOT receive external alerts (outbound only) — n8n must monitor ATR and send to PostgreSQL/Discord/Telegram. Pine Script indicator saved to Obsidian but noted as needing refinement. Strategy confirmed: 1m-5m for fee scalping, 5m-15m for directional quickies. Entry logic: 5/12 cloud for entry confirmation, 34/50 for trend direction, 8/9 for pullback adds.

### Decisions recorded
- n8n monitors ATR → PostgreSQL → Discord/Telegram (not TradingView receiving external data)
- Vince must ASK before building; present options, let Malik choose
- ADR/ATR filter logic still needs to be defined (deferred)

### State changes
- crypto-liquidity-farming.skill package created
- tradingview_alert_research.md created
- Pine Script indicator saved (needs refinement)

### Open items recorded
- Load Pine Script v6 expert skills for next session
- Define exact ADR/ATR filter logic
- Build Pine Script indicator with signal generation + webhook alerts
- Connect to n8n workflow
- Set up ni9htw4lker website on free .cloud domain

### Notes
~2 hours wasted due to Vince building without asking. Lesson recorded: "FOCUS ON X = only do X." Session ended with plan to restart fresh next session with Pine Script skills loaded first.

---

## 2026-01-31-quad-rotation-session.md
**Date:** 2026-01-31 (Friday)
**Type:** Build session

### What happened
~4 hour session. Primary deliverable: Quad Rotation Stochastic Framework v3.1, Pine Script v6 ready. Four stochastics defined: Fast (9-3), Standard (14-3 TDI), Medium (40-4), Slow (60-10). Divergence detection: TDI-style pivot method with <20/>80 filter (Option C selected from 3 options). Max divergence lookback: 14 bars (Fast 9-3 only). Alignment tracking: 4/4, 3/4, 2/4. Macro trend: Slow stochastic 3-bar confirmation. All Pine Script v4 → v6 conversions applied (12 functions): study→indicator, rsi→ta.rsi, sma→ta.sma, stdev→ta.stdev, lowest→ta.lowest, highest→ta.highest, pivotlow→ta.pivotlow, pivothigh→ta.pivothigh, valuewhen→ta.valuewhen, barssince→ta.barssince, crossover→ta.crossover, crossunder→ta.crossunder. Also: transp=80 → color.new(color, 80). Six critical bugs fixed including alignment counting reset per bar and division by zero protection. Four Pillars progress: 2/4 complete (Ripster EMA and BBWP done, VWAP and Quad Rotation pending). n8n automation architecture fully documented.

### Decisions recorded
- Divergence method: TDI-style pivot detection + <20/>80 filter (Option C)
- Standard stochastic: 14-3 (TDI perspective)
- Max lookback: 14 bars for Fast (9-3)
- Super Signal = Quad Rotation + High Probability Signal (HPS)
- Quad Rotation has 4 setup TYPES, not 4 stochastics as elements
- Divergence uses ONLY Fast (9-3) stochastic
- Next session: Anchored VWAP indicator (Pillar 2)

### State changes
- `01-SYSTEM-BUILD/n8n-Architecture.md` created (complete automation workflow, 9 nodes, PostgreSQL schema, Docker config)
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic.md` created (v3.1, v6 ready)
- `02-STRATEGY/Four-Pillars-Status-Summary.md` created
- `00-DASHBOARD/Task-Status-2026-01-31.md` created
- `06-CLAUDE-LOGS/2026-01-31-session-summary.md` created
- Framework quality: v1.0 (40%) → v2.0 (70%) → v3.0 (85%) → v3.1 (95%)

### Open items recorded
- Build Anchored VWAP indicator (next session, ~1 hour)
- Give Quad Rotation framework to Claude Code to build the actual indicator
- Build Combined Four Pillars indicator
- Set TradingView alerts
- Deploy n8n workflow to VPS

### Notes
Four Pillars progress at session end: Pillar 1 (Ripster EMA) complete, Pillar 2 (AVWAP) not started, Pillar 3 (Quad Rotation) framework ready, Pillar 4 (BBWP) complete.

---

## 2026-01-31-session-summary.md
**Date:** 2026-01-31 (Friday)
**Type:** Session log (summary)

### What happened
Summary of the same 4-hour session as 2026-01-31-quad-rotation-session.md. Covers same content: n8n architecture, Quad Rotation Stochastic Framework v3.1, system capability assessment, TDI code analysis. Clarifies that the system does NOT yet understand long/short signals — indicators work separately with no integration. Standard stochastic clarified as "mid stochastic" at 14-3. Quad Rotation 4 elements confirmed as Divergence, Coil, Trend Line, VWAP (not 4 stochastics as elements). Weekly plan for Feb 3-7: Trading Dashboard (Monday), Four Pillars Combined Indicator (Wednesday), VPS Deployment (Friday).

### Decisions recorded
- Quad Rotation 4 elements = Divergence, Coil, Trend Line, VWAP
- Standard stochastic = 14-3 (confirmed)
- Weekly plan: Dashboard Monday, Combined Indicator Wednesday, VPS Deployment Friday

### State changes
- Same as 2026-01-31-quad-rotation-session.md (duplicate summary)

### Open items recorded
- Trading Dashboard (Monday Feb 3)
- Quad Rotation build (Wednesday Feb 5)
- VPS deployment (Friday Feb 7)
- Integration of Combined Four Pillars indicator

### Notes
Companion/duplicate of 2026-01-31-quad-rotation-session.md covering same session in slightly different format.

---

## 2026-02-02.md
**Date:** 2026-02-02
**Type:** Other

### What happened
File exists but contains only 1 line (empty or near-empty). No content to analyze.

### Decisions recorded
None.

### State changes
None documented.

### Open items recorded
None.

### Notes
File is effectively empty. Multiple other files from 2026-02-02 contain session content.

---

## 2026-02-02-atr-sl-trailing-tp-build-spec.md
**Date:** 2026-02-02
**Type:** Build session / Specification

### What happened
~45 minute session to design and document a build specification for ATR-based stop loss and trailing take profit system with n8n momentum validation. Architecture: TradingView calculates ATR-based levels and sends JSON webhook → n8n validates momentum from exchange data → exchange manages trailing stop. Stop loss: chart TF ATR × 2 (LONG: Entry - ATR×2, SHORT: Entry + ATR×2). Trailing stop activation: Entry + (HTF ATR × 2) for LONG; callback distance = HTF ATR × 2. Timeframe mapping: 1m chart uses 1m for SL, 5m for trailing; 5m chart uses 5m for SL, 15m for trailing. Momentum validation: n8n fetches 3 candles (5m) from exchange, validates TV ATR >= 75% of 3-candle average — below 75% = momentum fading, reject trade. Entry signals: EMA 9/21 cross as placeholder (to be replaced with Four Pillars later). Exchange priority: WEEX primary, Bybit secondary. Full build spec created at `02-STRATEGY/Indicators/ATR-SL-Trailing-TP-BUILD-SPEC.md`.

### Decisions recorded
- Trailing visual: No update in Pine Script (exchange manages real trailing)
- Exchange priority: WEEX primary, Bybit secondary
- Position size: input adjustable
- Entry signals: EMA 9/21 cross as placeholder
- ATR momentum threshold: 75%
- Multi-position: future scope

### State changes
- `02-STRATEGY/Indicators/ATR-SL-Trailing-TP-BUILD-SPEC.md` created (full build spec)
- `06-CLAUDE-LOGS/2026-02-02-atr-sl-trailing-tp-build-spec.md` created (session log)

### Open items recorded
- Claude Code to build Pine Script indicator from spec
- Build n8n workflow (Section 3 of spec)
- Verify WEEX API endpoints and test on testnet
- End-to-end integration test with paper trading

### Notes
None.

---

## 2026-02-02-atr-sl-trailing-tp-session.md
**Date:** 2026-02-02
**Type:** Session log

### What happened
Short companion log for the ATR SL/Trailing TP spec session. Contains the same core information as 2026-02-02-atr-sl-trailing-tp-build-spec.md but adds a self-assessment/drift analysis. The drift analysis identified that work done this session (AVWAP framework, Volume Status, ATR SL/Trailing) was out of sequence — the correct priority should have been: (1) Quad Rotation Stochastic (Pillar 3, blocker), (2) Combined Four Pillars indicator, (3) THEN position management. Verdict: work not wasted but sequence jumped ahead of blockers. Weekly progress: 60% (3/5 tasks, Streamlit Trading Dashboard done, Ripster EMA v6 done, n8n Architecture done; Quad Rotation and VPS deployment pending).

### Decisions recorded
- Correct priority order: Quad Rotation first (blocker) → Combined indicator → position management
- ATR spec ready when needed but was premature

### State changes
- Same files as previous session log (companion document)

### Open items recorded
- Trading Dashboard (next immediate task, Monday)
- Quad Rotation Stochastic (blocker)

### Notes
Self-assessment notes that AVWAP framework and Volume Status work was done out of sequence. Streamlit Trading Dashboard listed as already complete (first mention of this).

---

## 2026-02-02-avwap-anchor-assistant-framework.md
**Date:** 2026-02-02
**Type:** Planning / Specification

### What happened
Analyzed hypothesis for building an AVWAP assistance indicator. Research covered LonesomeTheBlue Volume Profile/Heatmap (POC detection), Shannon AVWAP methodology (psychological anchors), VSA event detection (Stopping Volume, Climax). Verdict: hypothesis valid, MVP feasible in 2-3 days. Three-pillar framework for the indicator defined: Pillar A (Structure) uses swing high/low for AVWAP anchor points; Pillar B (Volume Commitment) detects spike bars >1.5x avg, Stopping Volume, and Climax events; Pillar C (Price Position) compares price to Structure High AVWAP, Structure Low AVWAP, and POC. Dashboard design: 5-row silent table showing Structure High/Low, Volume Event, POC, and Bias. Settings for 30m crypto: Volume MA 20, spike threshold 1.5x, climax 2.0x, pivot length 5, ATR period 14. Build sequence: Day 1 (foundation), Day 2 (VSA + dashboard), Day 3 (polish + deploy).

### Decisions recorded
- MVP approach: enhance existing LonesomeTheBlue (fork, not build from scratch)
- Timeline: 2-3 days
- Integration: standalone + Four Pillars compatible

### State changes
- `skills/indicators/volume-analysis-enhancement-feasibility.md` created
- `skills/indicators/volume-analysis-implementation-guide.md` created
- Session log created

### Open items recorded
- Day 1: Fork LonesomeTheBlue, add volume spike detection, swing detection, test on RIVERUSDT 30min
- Day 2: Add Stopping Volume/Climax detection, build dashboard
- Day 3: Polish, alerts, documentation, live trading validation

### Notes
RIVERUSDT first mentioned as a test coin. This indicator is not the same as the Anchored VWAP mentioned in the Four Pillars — it is a standalone AVWAP assistance tool.

---

## 2026-02-02-dashboard-framework.md
**Date:** 2026-02-02
**Type:** Build session

### What happened
~2 hour session. Built a modular Pine Script entry grading dashboard framework (Dashboard Framework v3) for TradingView. Structure: BBWP acts as a gate (must pass before grade calculated), then 4 scored conditions: Momentum (Stoch alignment), TDI (divergence), Ripster (cloud direction), AVWAP (price position). Grade A = 4/4 conditions = 6 ATR target; Grade B = 3/4 = 4 ATR target; below 3/4 = no trade for automation. Dashboard displays: grade + score + direction (e.g., "A 4/4 LONG"), target ATR, each condition status (▲/▼/—), ATR value + stop distance, post-entry panel (Continuation, ATR direction, 5m Trail). Stochastic settings confirmed: Stoch 55 = (55, 1, 12), Stoch 9 = (9, 1, 3). Cross threshold on Stoch 9 (20/80), not Stoch 55. Divergence = optional strengthener, not automation blocker. Files created: `02-STRATEGY/Indicators/Dashboard-Framework-v3.pine` and `Dashboard-Spec-v3.md`.

### Decisions recorded
- BBWP = gate (prerequisite, not a scored condition)
- Grade A (4/4) = 6 ATR target; Grade B (3/4) = 4 ATR target
- Below 3/4 = no trade for automation
- Stoch 55 settings: (55, 1, 12); Stoch 9: (9, 1, 3)
- Cross threshold on Stoch 9 at 20/80 levels
- Divergence = optional strengthener, not blocker for automation
- Equal highs/lows valid for divergence (double top/bottom)

### State changes
- `02-STRATEGY/Indicators/Dashboard-Framework-v3.pine` created
- `02-STRATEGY/Indicators/Dashboard-Spec-v3.md` created
- Streamlit Trading Dashboard listed as done (P&L dashboard)

### Open items recorded
- Replace BBWP stub with spectrum line detection
- Replace AVWAP with proper swing anchor
- Add proper divergence pivot detection + zone filter
- Add 5m Trail via HTF request.security
- Build AVWAP indicator with swing anchor
- VPS deployment (Streamlit + n8n)

### Notes
Project status at this point: Streamlit Trading Dashboard done, Ripster EMA v6 done, n8n architecture documented, Quad Rotation framework ready, Pine Script Entry Dashboard v3 done. AVWAP indicator and VPS deployment still pending.

---

## 2026-02-02-ripster-volume-status-build.md
**Date:** 2026-02-02
**Type:** Build session

### What happened
Two main activities: (1) Analysis of 14 Ripster47 TradingView published scripts and their value for VWAP thesis. High-value scripts: RVol Label (volume validation for VWAP breakouts), Ripster Candle Rvol (AVWAP anchor detection via high RVol candles), DTR & ATR (position sizing context). (2) Built a custom Volume Status indicator (`volume_status_v1.1.pine`) as an open-source replica of the closed-source Ripster Candle Rvol. Five status levels: SPIKE (>200%), STRONG (150-200%), NORMAL (80-150%), WEAK (50-80%), DEAD (<50%). Features: compact mode, multiplier display (1.5x not %), background flash on spikes, alerts for status transitions. Agreed to plan a Unified Four Pillars Dashboard consolidating multiple indicators into one table. Decision to test on TradingView as next step.

### Decisions recorded
- RVol Label and Candle Rvol are highest-value Ripster scripts for VWAP thesis
- Volume Status displays multiplier (1.5x) not percentage — reduces mental math
- SPIKE/STRONG = volume confirmation; WEAK/DEAD = skip trade
- Plan: consolidate all indicators into single unified Four Pillars Dashboard

### State changes
- `skills/indicators/volume_status_v1.1.pine` created

### Open items recorded
- Test volume_status_v1.1.pine on TradingView
- Consider adding previous candle Rvol comparison
- Integrate with Four Pillars dashboard

### Notes
Ripster Candle Rvol is closed-source, so a custom replica was built. The unified dashboard concept agreed here is the precursor to the Four Pillars dashboard framework built in the same day's session.

---

## 2026-02-03.md
**Date:** 2026-02-03
**Type:** Build session (journal)

### What happened
Full-day session with 8 sub-sessions. Sessions 1-4: Audited built vs pending indicators; reviewed Rockstar HPS (John Kurisko) rules from PDF; gap analysis identified weaknesses in divergence detection logic; 3 angle calculation methods tested with 5,000 randomized scenarios — Option C (Agreement Multiplier) selected with 66.1% accuracy vs Options A (48.6%) and B (51.1%); complete Pine Script v6 build spec v4 created; validated 92.4% win rate in statistical testing. Sessions 5-7: Critical review of v4 spec found 9 major bugs; re-validation with 5-bar lookback showing 92.1% win rate; 11 major implementation bugs identified and all fixed; edge detection added to all alerts. Session 8: Built Quad Rotation FAST v1.1 spec; found and fixed 5 additional bugs. Key technical learnings: Fast stochastic uses single smooth (ta.sma(rawK, smooth)), Full (60-10) needs DOUBLE smoothing (ta.sma(ta.sma(rawK, smooth), smooth)); state machine MUST use if/else if chains; edge detection pattern: `alertcondition(signal and not signal[1], ...)`.

### Decisions recorded
- Agreement Multiplier approach (Option C Optimized) selected for angle calculation
- v4.1 (slow) = trade WITH trend only, missing reversals intentional (HPS setups only)
- FAST v1.1 = 9-3 + 14-3 as primary triggers, 40-4/60-10 as slow context
- 60-10 stochastic needs DOUBLE smoothing (Full stochastic, not Fast)
- State machines: ALWAYS use if/else if chains
- All alerts MUST be edge-triggered

### State changes
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-v4-BUILD-SPEC.md` created (v4.1)
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-FAST-BUILD-SPEC.md` created (v1.1)
- `skills/pinescript/SKILL.md` created (v2.0)
- `skills/pinescript/references/technical-analysis.md` created
- `skills/n8n/SKILL.md` created

### Open items recorded
- Build v4.1 Pine Script in Claude Code
- Build FAST v1.1 Pine Script in Claude Code
- Test both on TradingView
- Set up n8n webhook integration

### Notes
This is the most technically dense session in the batch. 11 bugs found and fixed in v4, 5 bugs in FAST v1.1. Statistical validation used 5,000 randomized samples.

---

## 2026-02-03-quad-rotation-stochastic-spec-review.md
**Date:** 2026-02-03
**Type:** Strategy spec / Specification

### What happened
Deep review of Quad Rotation Stochastic specification to align with John Kurisko (DayTraderRockStar) HPS methodology from PDF source. Stochastic settings confirmed: Fast (9,3), Fast (14,3), Fast (40,4) — highest divergence priority, Full (60,10) — macro filter. John's Rule 5: "Always take a 40-4 divergence or any multiple-band divergences." Divergence definition: Stage 1 (price extreme + stoch in OB/OS zone), bounce, Stage 2 (price makes higher/lower extreme or equal, stoch holds inside zone and turns). Stage-based state machine designed for both bullish and bearish. Price threshold for equal highs/lows: configurable input (0.1% default). Angle calculation: Option C Optimized selected (66.1% accuracy), 5-bar lookback, 3° signal threshold, 0.7 agreement factor. Statistical analysis: 5,000 samples, p < 0.001 significance. Confirmed 26 alerts across 6 categories (divergence, alignment, exit/management, zone, rotation, combo/supersignal). Flag detection skipped (requires visual chart reading). Coil and channel detection deferred.

### Decisions recorded
- Stage-based divergence (not TDI pivot) — matches John's exact methodology
- Option C Optimized for angle (40-4 as base, agreement multiplier)
- Skip flag detection (requires visual ID)
- Skip coil detection (later version)
- Skip channel detection (later version)
- 40-4 = primary (Supersignal per John's Rule 5)
- Exit signals = raise stop loss, NOT immediate close
- Equal high/low threshold: 0.1% default

### State changes
- Quad Rotation v4 spec refined and confirmed ready for Claude Code build
- 26 alert conditions defined and confirmed

### Open items recorded
- Update Quad Rotation spec file with confirmed parameters
- Build in Claude Code
- Test on RIVERUSDT 30min chart
- Verify divergence detection vs visual chart analysis

### Notes
This document covers the same day as 2026-02-03.md and is the detailed technical companion. John Kurisko's exit rule documented: "Under 200/VWAP, take trade off on first 9-3 rotation above 80."

---

## 2026-02-03-quad-rotation-v4-fast-build-session.md
**Date:** 2026-02-03
**Type:** Build session

### What happened
Build session log for creating two Pine Script v6 indicator specs: Quad Rotation Stochastic v4.1 (slow/conservative, 40-4 divergence leads, trade with trend only) and Quad Rotation Stochastic FAST v1.1 (fast/aggressive, 9-3 + 14-3 lead, pullback/continuation trades). v4.1 bugs fixed (11 total, same as 2026-02-03.md). FAST v1.1 bugs fixed (5 total): bear_state_bar typo, turn detection false positive (added stoch > stoch[1] check), unnecessary var tracking, hidden plot duplicates, missing 50 midline. Pine Script skill updated to v2.0 with new patterns: fast vs full stochastic functions, state machine if/else if pattern, edge detection, turn detection with momentum confirmation, supersignal timing with persistence, hidden plots for JSON, code review checklist. Next steps: open VS Code terminal, run claude, build SLOW indicator first then FAST, test on TradingView.

### Decisions recorded
- v4.1 (slow): trade WITH trend, missing reversals intentional, stop outs accepted as part of trading
- FAST v1.1: 9-3 + 14-3 primary, 40-4/60-10 context, best for pullback/continuation
- Both specs finalized and ready for Claude Code build

### State changes
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-v4-BUILD-SPEC.md` updated to v4.1
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-FAST-BUILD-SPEC.md` created (v1.1)
- `skills/pinescript/SKILL.md` created/updated to v2.0

### Open items recorded
- Open VS Code terminal, run claude
- Build Quad Rotation SLOW v4.1 Pine Script
- Build Quad Rotation FAST v1.1 Pine Script
- Test both on TradingView

### Notes
Companion/implementation log to 2026-02-03.md and 2026-02-03-quad-rotation-stochastic-spec-review.md. All three cover the same day's work from different angles.

---

# CODE VERIFICATION

### Scripts referenced in this batch:
- `02-STRATEGY/Indicators/ripster_ema_clouds_v6.pine` — Referenced in 2026-01-29-pine-script-review.md as an existing file reviewed for bugs. Not verified (no glob run).
- `02-STRATEGY/Indicators/atr_position_manager_v1.pine` — Referenced in 2026-02-02-atr-sl-trailing-tp-build-spec.md as planned output, not yet built at time of log.
- `02-STRATEGY/Indicators/Dashboard-Framework-v3.pine` — Referenced in 2026-02-02-dashboard-framework.md as created this session. Not verified.
- `skills/indicators/volume_status_v1.1.pine` — Referenced in 2026-02-02-ripster-volume-status-build.md as created this session. Not verified.
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-v4-BUILD-SPEC.md` — Referenced as spec (not .pine). Not a Python script.
- All .pine files are Pine Script (TradingView), not Python — no py_compile verification applicable.

No Python scripts were identified as key deliverables in this batch.


# Research Batch 02 — Findings
Files: 2026-02-04 through 2026-02-11

---

## 2026-02-04.md
**Date:** 2026-02-04
**Type:** Build session (daily journal, multiple sessions)

### What happened
Eight sessions logged across the day covering Pine Script indicator fixes, strategy specification, and new indicator builds.

Session 1: Quad Rotation FAST v1.3 philosophy correction. v4.3 patch. Selected FAST v1.4 as production version. Copied to `Quad-Rotation-Stochastic-FAST.pine`.

Session 2: Indicator review against PineScript skill standards. AVWAP alert edge-triggering fix (`and not condition[1]`). QRS 40-4 smoothing changed from 4 to 3 (Kurisko original). BBWP v2 MA cross persistence fixed with timeout (10 bars default) + timestamp display.

Session 3: Critical conflict found — v1.0 Four Pillars strategy spec referenced "Stoch 55" which does not exist in any built indicator. Created `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` with correct stochastic settings (9-3, 14-3, 40-4, 60-10). Deprecated `FOUR-PILLARS-COMBINED-BUILD-SPEC.md`.

Session 4: Added 15 hidden integration plots to `ripster_ema_clouds_v6.pine` — cloud states, price position, cloud direction, crossovers, scores, raw EMAs.

Session 5: Built `four_pillars_v2.pine` (~500 lines) — self-contained indicator with all 4 pillars, A/B/C grade calculation, position management, dashboard, 11 alert conditions, webhook JSON, 10 hidden plots.

Session 6: Complete rewrite `four_pillars_v3.pine` v3.1 — 9-3 as TRIGGER, all other stochastics (14-3, 40-3, 60-10) must be in zone (<30 or >70), 3-bar lookback, raw K stochastic calc fix, toggleable filters.

Session 7: v3.2 — changed filter from 40-3 K/D comparison to 40-3 D line position (D > 20 for long, D < 80 for short).

Session 8: v3.3 — changed from 40-3 D filter to 60-10 D filter with fixed 20/80 thresholds (not tied to zone level input).

### Decisions recorded
- FAST indicator should NOT filter by trend — outputs rotation state only; integration layer decides.
- 40-4 as SUPERSIGNAL (highest priority) — divergence detection on 40-4 only, NOT on 9-3.
- Stochastic hierarchy: 9-3/14-3 trigger → 40-4 divergence → 60-10 filter.
- Stoch 55 was an error from pre-HPS conception — removed from spec entirely.
- TDI reference removed.
- 34/50 cloud is PRIMARY for trend bias.

### State changes
- `Quad-Rotation-Stochastic-FAST.pine`: Fixed 40-4 smoothing
- `Quad-Rotation-Stochastic-v4-CORRECTED.pine`: Fixed 40-4 smoothing, added hidden plot
- `avwap_anchor_assistant_v1.pine`: Edge-triggered VSA alerts
- `bbwp_v2.pine`: MA cross timeout + timestamp + hidden plots
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md`: NEW — corrected strategy spec
- `FOUR-PILLARS-COMBINED-BUILD-SPEC.md`: Deprecated
- `ripster_ema_clouds_v6.pine`: NEW — 15 integration hidden plots
- `four_pillars_v2.pine`: NEW — complete combined indicator
- `four_pillars_v3.pine`: v3.3 — 60-10 D filter with fixed 20/80

### Open items recorded
- Create strategy version of v3 for backtesting
- Add trailing stop logic
- Test all indicators in TradingView
- Set up n8n webhook integration

### Notes
Root cause of "Stoch 55" error: session from 2026-01-29 conceptualized strategy before John Kurisko HPS methodology was researched. The spec was not updated when indicators were built correctly.

---

## 2026-02-04-four-pillars-strategy-specification.md
**Date:** 2026-02-04
**Type:** Strategy spec / session log

### What happened
Extended session documenting the Four Pillars v2.0 strategy specification. Resolved all conflicts from v1.0 spec. Identified that "Stoch 55 K/D cross" as primary trigger was wrong — replaced with 40-4 divergence as SUPERSIGNAL. Exit management changed from "Stoch 55 momentum" to "9-3 reaches opposite zone."

Defined entry rules (all 4 pillars aligned + 9-3/14-3 trigger OR SUPERSIGNAL + RVol >= NORMAL), exit rules (Initial SL 2x 1m ATR, trail activation at 2x 5m ATR, trail callback 2x 5m ATR, exchange manages trailing), and signal grades (A: 4/4 + SUPERSIGNAL + squeeze; B: 4/4; C: 3/4; D: NO TRADE).

All 6 indicators verified as built: ripster_ema_clouds_v6.pine, avwap_anchor_assistant_v1.pine, bbwp_v2.pine, Quad-Rotation-Stochastic-v4-CORRECTED.pine, Quad-Rotation-Stochastic-FAST-v1.4.pine, atr_position_manager_v1.pine, four_pillars_v2.pine.

Defined position management flow: TV Signal → n8n validates (3-candle ATR check) → Exchange places order with trailing → Set and forget.

### Decisions recorded
- 60-10 is MACRO FILTER only — NOT leading.
- 9-3 and 14-3 are LEADING triggers.
- Divergence detection on 40-4 only (Stage-based).
- Stochastic hierarchy: 9-3/14-3 trigger → 40-4 divergence → 60-10 filter.

### State changes
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` created (corrected spec document).

### Open items recorded
- Start fresh chat for combined indicator build.
- Build Pine Script that integrates all 4 indicators.
- Add dashboard table.
- Add alerts with JSON payload.

### Notes
TradingView Pine Logs shortcut: `Ctrl + J`. Token usage noted as high due to extensive past chat searches.

---

## 2026-02-04-indicator-review-session.md
**Date:** 2026-02-04
**Type:** Build session / review session

### What happened
Continued session reviewing built indicators against PineScript skill standards.

AVWAP Anchor Assistant: VSA alerts were not edge-triggered (could fire on multiple consecutive bars). Fixed lines 668-682 with `and not condition[1]` pattern for all 5 VSA alert types. All 8 validation checklist items confirmed passing.

QRS Indicators (earlier session): Fixed missing hidden plot for stoch_40_4 in v4-CORRECTED. Fixed 40-4 smoothing from 4 to 3 (Kurisko original: K=40, Smooth=3).

BBWP v2: Three issues fixed — (1) MA cross state persisted indefinitely, fixed with timeout input `i_maCrossTimeout` (default 10 bars); (2) No timestamp for when MA cross occurred, fixed with `str.format("{0,time,HH:mm}", maCrossTime)` display in table row 4; (3) Missing persistent state hidden plots, added `ma_cross_up_state` and `ma_cross_down_state` plots. Auto-end conditions: spectrum enters blue zone (BBWP < 25), enters red zone (BBWP > 75), or timeout reached.

Four Pillars Strategy v2.0 Specification: MAJOR conflict found in v1.0 — "Stoch 55 K/D cross" was wrong. Source traced to 2026-01-29 logs (pre-HPS methodology). Created `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` with correct settings.

Ripster EMA Clouds: 15 hidden integration plots added.

Four Pillars v2: Complete combined indicator built with all 4 pillars, grade calculation (A/B/C/No Trade), position management, dashboard, stochastic mini panel, 11 alerts, webhook JSON, 10 hidden plots.

### Decisions recorded
- MA cross auto-end conditions: spectrum hits blue/red OR timeout reached.
- v1.0 spec deprecated.

### State changes
- `avwap_anchor_assistant_v1.pine`: Edge-triggered VSA alerts
- `bbwp_v2.pine`: MA cross timeout + timestamp + hidden plots
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md`: NEW
- `FOUR-PILLARS-COMBINED-BUILD-SPEC.md`: Deprecation notice added
- `ripster_ema_clouds_v6.pine`: 15 integration hidden plots added
- `four_pillars_v2.pine`: NEW complete combined indicator

### Open items recorded
None explicitly stated.

### Notes
None.

---

## 2026-02-04-quad-rotation-fast-v1.3-build.md
**Date:** 2026-02-04
**Type:** Build session

### What happened
Critical review of Quad Rotation Stochastic indicators against John Kurisko HPS methodology. Identified philosophy issues in FAST v1.2 spec.

v1.2 to v1.3 changes: Removed built-in trend filter; Channel (60-10) changed from mandatory filter to context output only; Counter-trend exit removed; Signal hierarchy reduced from 4 tiers to 3 tiers (rotation quality); Added near zone (30/70) in addition to strict zone (20/80); Changed 14-3 confirmation from 2-bar momentum to 1-bar direction; Added 5-bar signal cooldown.

Selected FAST v1.4 as final — has all v1.3 features plus 9-3 divergence detection, DIV+ROTATION combo signal, info table, price chart triangles (force_overlay), divergence lines, signal candle coloring, 60-10 flat case handling.

Patched `Quad-Rotation-Stochastic-v4-CORRECTED.pine` from v4.2 to v4.3 — added signal candle coloring, price chart triangles (force_overlay=true), context outputs for integration: channel_numeric (60-10 state), mid_numeric (40-4 state), bars_since_bull_div, bars_since_bear_div, div_active, slow_confirm.

JSON schema defined with numeric encodings for channel_numeric (-3 to +3), mid_numeric (-1/+1), zone_numeric (-2 to +2), div_active (-1/0/+1).

### Decisions recorded
- FAST indicator should NOT filter by trend — outputs rotation state only.
- Integration layer (n8n/Dashboard) decides based on ALL pillars.
- FAST v1.4 selected as production version.

### State changes
- `Quad-Rotation-Stochastic-FAST-v1.3-BUILD-SPEC.md`: NEW — updated spec with philosophy corrections
- `Quad-Rotation-Stochastic-v4-CORRECTED.pine`: Patched to v4.3 with integration context outputs
- `Quad-Rotation-Stochastic-FAST-v1.3.pine`: Reviewed, no changes needed
- `Quad-Rotation-Stochastic-FAST-v1.4.pine`: Reviewed, selected as final

### Open items recorded
- Copy FAST v1.4 to `Quad-Rotation-Stochastic-FAST.pine` (production)
- Test v4.3 in TradingView — compile, visual check
- Test FAST v1.4 in TradingView — compile, visual check
- Verify JSON outputs with test alerts
- Set up n8n webhook integration

### Notes
None.

---

## 2026-02-05.md
**Date:** 2026-02-05
**Type:** Build session (daily journal, multiple sessions)

### What happened
Eleven sessions logged across the day covering strategy toggles, SL system overhaul, stochastic smoothing fix, strategy backtesting version rebuild, exit bug fixes, and AVWAP trailing.

Session 1: Reviewed and validated v3.4.1 strategy. Found toggle gap — strategy has `i_useTP`, indicator does not. Session hit context limit.

Session 2: Added `i_useTP` toggle and `i_useRaisingSL` toggle to indicator. Changed Phase 3 trail from Cloud 3 to Cloud 4. Bumped to v3.4.2.

Session 3: Major SL overhaul — removed entire phased P0→P1→P2→P3 SL system, replaced with continuous Cloud 3 (34/50) ± 1 ATR trail every candle. Added Cloud 2 re-entry A trade (price crosses Cloud 2 + recent A rotation within lookback bars). Removed Cloud 2 flip hard close exit. File reduced from 645 to ~495 lines.

Session 3b: Added trail activation gate (Cloud 3/4 cross: ema50 > ema72 for LONG). SL starts static at entry ± 2 ATR; trail only activates after gate. Position replacement logic added (new entry replaces existing position when price beyond Cloud 3). Entry priority reordered. Fixed inverse SL bug (trail pushing SL above entry price on bar 2 when entering LONG below Cloud 3).

Session 4: v3.5 — discovered stochastic smoothing was missing in all 4 stochastics (raw K, no SMA). Applied smoothing: 9-3, 14-3, 40-3 each use ta.sma(k_raw, 3); 60-10 uses ta.sma(ta.sma(k_raw,10),10) double smooth. Created new file `four_pillars_v3_5.pine` preserving v3.4.2.

Session 5: Complete rewrite of strategy as `four_pillars_v3_5_strategy.pine`. Changed pyramiding from 10 to 1; implemented all v3.5 changes in strategy. Old problems: 32 of 54 exits were margin calls (pyramiding=10 + 100% equity), Cloud 2 exits cutting winners, raw stochastics causing 170 trades in 7 days.

Session 6: Fixed 3 bugs in v3.5 strategy — (1) dual exit conflict (strategy.exit + strategy.close_all racing), (2) position replacement invisible (fixed entry detection to use entryBar == bar_index), (3) state desync after exit (added strategy.position_size == 0 sync).

Session 7: Removed position replacement entirely — found it was closing winning trades and creating fragmented margin-call micro-trades. Changed canEnterLong/Short to `not inPosition` only. Renamed exit IDs to "Exit Long"/"Exit Short".

Session 8: v3.5.1 root cause fix — user's external stochastic indicators show "Stoch 9 1 3" meaning K smoothing = 1 (raw K, no SMA). The v3.5 "smoothing fix" had made strategy K values equivalent to the D line, not the K line. Reverted all stochastics to raw K. Fixed position sizing from 100% equity to $500 fixed per trade. Changed B/C defaults from ON to OFF. Added A trade flip capability (close opposite + enter new).

Sessions 9-10: v3.6 — designed new AVWAP trailing stop system. A trade SL changed from Cloud 3 ± ATR to AVWAP ± max(stdev, ATR) ratchet. Separate "Long BC"/"Short BC" order IDs. BC exit conditions: SL + Cloud 2 cross + 60-10 K/D cross in extreme zone. BC entry filter: Cloud 3/4 parallel (both slopes same direction). AVWAP anchored to A trade signal bar. AVWAP recovery re-entry (V-shape dip rebuy). State sync loop checking entry IDs.

Session 11: Built v3.6 indicator. Added Volume Flip Filter (toggle `i_useFlipVol`, lookback 20 bars, volume must exceed both rolling avg and avg-since-entry). Fixed dashboard table.new() scope issue (moved from barstate.islast block to global scope).

### Decisions recorded
- Phased SL system (P0→P1→P2→P3) removed — replaced with continuous Cloud 3 trail.
- Cloud 2 exit removed — trail handles protection.
- Position replacement removed — was killing winners and creating margin-call fragments.
- Raw K stochastics confirmed as correct (smooth=1) — SMA on K was wrong.
- B/C defaults changed to OFF.
- A trades can flip direction; B/C/re-entry can only enter from flat.
- AVWAP in v3.6 anchored to A trade entry bar (not session or swing-based).

### State changes
- `four_pillars_v3_4.pine`: v3.4.2 — trail activation gate, position replacement, inverse SL fix
- `four_pillars_v3_5.pine`: v3.5.1 — stochastic smoothing revert to raw K
- `four_pillars_v3_5_strategy.pine`: v3.5.1 — strategy version preserved as reference
- `four_pillars_v3_6_strategy.pine`: NEW — v3.6 AVWAP + A/BC + volume flip filter
- `four_pillars_v3_6.pine`: NEW — v3.6 indicator version
- `06-CLAUDE-LOGS/2026-02-05-strategy-analysis-session.md`: NEW — session 1 log

### Open items recorded
None explicitly listed at end.

### Notes
The v3.5 "stochastic smoothing fix" was actually a regression — it applied SMA to K making it equivalent to the D line, opposite of what was needed. Raw K (smooth=1) confirmed as correct. This is a critical lesson.

---

## 2026-02-05-strategy-analysis-session.md
**Date:** 2026-02-05
**Type:** Session log (context limit reached)

### What happened
Session maxed out (context limit reached) after reviewing and validating the Four Pillars v3.4.1 strategy backtesting version. Confirmed all logic matches indicator version. Strategy already had `i_useTP` toggle. Toggle gap identified: indicator version is missing `i_useTP` and `i_useRaisingSL`.

Strategy config at time of review: $10,000 initial capital, 100% equity position size, 0.1% commission, pyramiding=10, order processing on close.

Session cut short before implementation.

### Decisions recorded
None made (session ended at analysis stage).

### Open items recorded
- Add `i_useTP` toggle to indicator `four_pillars_v3_4.pine`
- Add `i_useRaisingSL` toggle to indicator
- Keep both indicator and strategy files in sync

### Notes
None.

---

## 2026-02-06.md
**Date:** 2026-02-06
**Type:** Build session (daily journal)

### What happened
Two sessions: v3.7 rebate farming architecture build, then emergency v3.7.1 commission fix.

Session 1: Built `four_pillars_v3_7_strategy.pine` — "rebate farming" architecture for ~3000 trades/month. SL changed to 1.0 ATR static, TP 1.5 ATR static (both tight). B/C behavior changed to open fresh positions and flip direction. Volume flip filter removed (free flips). Cloud 2 re-entry tracks bars since ANY signal (not just A). Order IDs simplified back to single ID (v3.5 simplicity). Pyramiding=1. Commission set to percent 0.06% (BUG).

Session 2: Critical bug discovered — `commission.percent=0.06` applies to CASH qty ($500), not notional ($10k with 20x leverage). TV showed $0.30/side but real cost was $6.00/side. Additionally found phantom trade bug: `strategy.close_all()` + `strategy.entry()` on same bar creates 2 trades per flip instead of 1.

Emergency fix `four_pillars_v3_7_1_strategy.pine`: Commission changed to `cash_per_order=6` (deterministic). Flipping changed to `strategy.entry()` only (auto-reverses from short). Added `strategy.cancel()` before every flip. Added 3-bar cooldown minimum between entries (`cooldownOK` on ALL entry paths). Added running Comm$ total to dashboard.

Also created `four_pillars_v3_7_1.pine` (indicator version).

Exported backtest CSV: `07-TEMPLATES/4Pv3.4.1-S_BYBIT_MEMEUSDT.P_2026-02-06_fcc84.csv`.

### Decisions recorded
- Commission must use `cash_per_order` not `commission.percent` for leveraged strategies — ALWAYS.
- Never use `strategy.close_all()` for flips — causes phantom double-commission trades.
- Use `strategy.entry()` for flips — auto-reverses, one commission.
- `strategy.cancel()` stale exits before every flip.
- Cooldown applied to ALL entry paths, not just some.

### State changes
- `four_pillars_v3_7_strategy.pine`: NEW — rebate farming architecture
- `four_pillars_v3_7_1_strategy.pine`: NEW — commission fix + cooldown
- `four_pillars_v3_7_1.pine`: NEW — indicator version

### Open items recorded
- Build Python backtester to validate v3.7.1 with correct commission
- Test breakeven+$X raise on historical data
- Fetch historical data for multiple coins

### Notes
This session established the critical commission math lesson: `commission.percent` in TradingView applies to cash qty, not notional. With 20x leverage, this creates a 20x underestimate of actual commission cost.

---

## 2026-02-07.md
**Date:** 2026-02-07
**Type:** Build session (daily journal, multiple sessions)

### What happened
Six sessions: master plan creation, WS1+WS2 docs, Python backtester build, backtest results, sub-$1B coin discovery, CUDA installation.

Session 1: Created master execution plan `warm-waddling-wren.md` defining 5 workstreams (WS1-WS5) — Pine Script Skill Optimization, Progress Review Documents, Data Pipeline + Signal Engine + Backtest Engine + Exit Strategies + Streamlit Dashboard, ML Parameter Optimizer, v4 + Monte Carlo Validation.

Session 2: Completed WS1 (updated all Pine Script skill files — commission fix, phantom trade, cooldown, Ripster Cloud numbering, stoch_k raw K function, lessons-learned.md). Completed WS2 (wrote `2026-02-07-progress-review.md` and `commission-rebate-analysis.md`).

Session 3: Built complete Python backtester in `PROJECTS/four-pillars-backtester/`. Data pipeline (WS3A): `data/fetcher.py` with BybitFetcher (primary) + WEEXFetcher (live only). Discovered WEEX API has no historical pagination — switched to Bybit v5 API. Bybit returns newest-first, implemented backward pagination. Signal engine (WS3B): `signals/stochastics.py` (raw K smooth=1), `signals/clouds.py` (Ripster EMA clouds 5/12, 34/50, 72/89), `signals/state_machine.py` (A/B/C grading + cooldown), `signals/four_pillars.py` (orchestrator). Backtest engine (WS3C): `engine/backtester.py` (bar-by-bar with MFE/MAE), `engine/position.py` (BE raise), `engine/commission.py` ($6/side + daily 5pm UTC rebate), `engine/metrics.py`.

Bug fixed: `df.set_index('datetime')` removes datetime from columns → rebate settlement never triggered. Fixed by checking `df.index.name`.

Session 4: 1-minute results on 5 coins — mostly negative (only RIVER profitable at +$87,510). 5-minute results on 5 coins — ALL PROFITABLE ($97,060 total). Key discovery: 5m timeframe makes all coins profitable. Commission bleed on 1m (~20K trades) overwhelms edge.

Session 5: Built `scripts/fetch_sub_1b.py` — uses CoinGecko for market cap filtering, Bybit v5 for candle data. Discovered 394 coins with <$1B market cap on Bybit. Saved to `data/sub_1b_coins.json`. Kicked off overnight fetch for all 394 coins.

Session 6: Installed NVIDIA CUDA 13.1 Toolkit. All components verified. GPU: RTX 3060, 12GB VRAM, driver 591.74. PyTorch, optuna, xgboost not yet installed.

### Decisions recorded
- 5-minute timeframe is optimal — fewer trades, less commission bleed.
- RIVER dominates ($13.95/trade on 5m) due to high ATR/price ratio.
- Breakeven raise is critical — LSG 59-84% means most losers were profitable at some point.
- BTC/ETH/SOL too expensive — commission is 46% of BTC TP win.
- WEEXFetcher only for live data, BybitFetcher is primary for historical.

### State changes
- `.claude/plans/warm-waddling-wren.md`: NEW — master execution plan
- `.claude/skills/pinescript/SKILL.md`: Updated
- `07-BUILD-JOURNAL/2026-02-07-progress-review.md`: NEW
- `07-BUILD-JOURNAL/commission-rebate-analysis.md`: NEW
- `PROJECTS/four-pillars-backtester/` entire tree: NEW — complete backtester
- `data/cache/*.parquet` (5 coins): NEW — 3-month 1m data
- `data/sub_1b_coins.json`: NEW — 394 coin list
- `scripts/fetch_sub_1b.py`: NEW — sub-$1B fetcher

### Open items recorded
- Wait for overnight fetch to complete (~02:00)
- Install PyTorch with CUDA (user task)
- Run 299-coin backtest on 5m
- Build v3.8 ATR-based BE module

### Notes
This session established the core performance findings: 5m > 1m for all coins, LSG 68-84%, commission rate matters ($12 RT is significant). WEEX confirmed to have no historical pagination API.

---

## 2026-02-07-backtest-results.md
**Date:** 2026-02-07
**Type:** Session log / backtest results

### What happened
Detailed record of Python backtester results for 5 low-price coins on both 1m and 5m timeframes.

Backtester configuration: $10,000 equity, $500 margin per trade, 20x leverage, $10,000 notional, SL 1.0 ATR, TP 1.5 ATR, cooldown 3 bars, B/C open fresh, $6/side commission, 70% rebate ($3.60/RT net).

1m results (3 months): 4 of 5 coins negative. Only RIVER profitable (+$87,510). Total 99,333 trades, total -$11,012.

5m results (3 months): ALL 5 coins profitable. Total 20,283 trades, total +$97,060 (+$4.79/trade). LSG ranges 77.4% to 84.2%.

Key findings: 5m is optimal timeframe, RIVER dominates ($13.95/trade), breakeven raise is critical (LSG 59-84%), BTC/ETH/SOL too expensive (commission = 46% of BTC TP win).

Bugs fixed: (1) rebate settlement bug from df.set_index, (2) WEEX no historical pagination, (3) Bybit newest-first pagination.

### Decisions recorded
None explicitly stated beyond findings.

### Open items recorded
- Build v3.8 ATR-based BE logic
- Commission rate verification ($4/side vs $6/side)
- Install PyTorch with CUDA
- Monte Carlo validation on 5m results
- Streamlit dashboard integration

### Notes
LSG (Losers Saw Green) = percentage of losing trades that were profitable at some point. Range confirmed as 59-84% across 5 coins on 5m. This is the primary optimization target.

---

## 2026-02-07-progress-review.md
**Date:** 2026-02-07
**Type:** Progress review document

### What happened
Comprehensive version evolution table from v3.4.1 through v3.7.1 documenting what each version solved and broke.

v3.5: Stochastic smoothing bug — applied SMA to K line, delayed signals by 2-3 bars. Never use SMA-smoothed K for entry detection.
v3.5.1: Cloud 3/4 trail — trail fails in chop-heavy crypto markets; activation delay exposes position before trail kicks in.
v3.6: AVWAP trail — stdev=0 bug on bar 1 causes near-zero SL. AVWAP better for swing trades, not 1m scalping.
v3.7: Commission blow-up — commission.percent applies to cash qty not notional, plus phantom trade bug from close_all + entry.
v3.7.1: Current working version — $1.81/trade expectancy before rebates.

Market context documented: Nov 11 (BTC favorable), Dec 15 (sharp dump), Jan 15+ (bearish grind), Feb 4 (another sharp dump). These are validation checkpoints.

Core finding: 86% of losing trades saw unrealized profit before dying. Exit timing is the bottleneck.

### Decisions recorded
- Breakeven+$X raise is primary optimization target for v4.
- Raw K must be used — SMA-smoothed K is wrong for this system.

### State changes
- `07-BUILD-JOURNAL/2026-02-07-progress-review.md`: NEW document

### Open items recorded
- Build Python backtester (WS3)
- Test BE+$X raise at different thresholds
- ML optimizer for regime-specific parameters (WS4)
- Build v4, validate with Monte Carlo (WS5)

### Notes
This document references "86% LSG" but the backtester results file shows 59-84% by coin. The "86%" may be a rounded or averaged figure across a different dataset or time period.

---

## 2026-02-08.md
**Date:** 2026-02-08
**Type:** Session log / overnight fetch results

### What happened
Overnight data fetch completed: started 2026-02-07 19:53, completed 2026-02-08 02:18 (~6.5 hours).

Results: 394 total coins, 363 fetched, 31 failed (rate limited), 299 full data (>3MB, 3 months), 70 partial/tiny, 38.5 million candles, 1.36 GB on disk. All 299 complete coins passed validation — zero gaps, zero NaN, zero dupes, zero bad prices.

Known issues: RIVER + SAND got overwritten by short fetches during sub-$1B run. Rate limit burst at ~20:39 caused 31 failures. 70 partial fetches need re-fetching.

Created comprehensive handoff document `07-BUILD-JOURNAL/2026-02-09-session-handoff.md`.

Completed status: WS1-WS3C done, CUDA 13.1 installed.
Blocked/Pending: PyTorch install (user task), refetch 101 coins, RIVER+SAND re-fetch, v3.8 ATR-based BE, 299-coin backtest, WS3D-WS5.

### Decisions recorded
None explicitly stated.

### State changes
- `data/cache/*.parquet`: 369 Parquet files from overnight fetch
- `data/fetch_log.txt`: Fetch log (2,479 lines)
- `data/refetch_list.json`: 101 coins to re-fetch
- `07-BUILD-JOURNAL/2026-02-09-session-handoff.md`: NEW — session handoff

### Open items recorded
- PyTorch install: `python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130`
- Add `--refetch` flag to fetch_sub_1b.py
- Improve rate limit handling (30-60s backoff between consecutive coin failures)
- Re-fetch RIVER + SAND

### Notes
The handoff document saved to `07-BUILD-JOURNAL/` but was dated as `2026-02-09-session-handoff.md` while being created on 2026-02-08.

---

## 2026-02-09.md
**Date:** 2026-02-09
**Type:** Build session (daily journal)

### What happened
Book analysis of 9 books, VINCE upgrade plan synthesized, Andy project created, tools installed, data re-fetched, PyTorch CUDA installed.

9 books scored — top ratings: Maximum Adverse Excursion (Sweeney, 9/10), Advances in Financial ML (De Prado, 9/10), ML for Algorithmic Trading (Jansen, 8/10).

VINCE upgrade plan from books:
1. ATR regime gate — when ATR × leverage > threshold, stop-outs are random not signal failures. Add atr_regime feature for XGBoost.
2. Drawdown constraint in Optuna objective — kill trial if max_drawdown > 10%.
3. Non-normal return awareness — use Sortino not Sharpe, modified Kelly, Monte Carlo shuffling.
4. Data augmentation — add Gaussian noise to candles, bootstrap confidence intervals.
5. Pre-entry XGBoost features — 11 features to predict if trade will win before entry.
6. Options flow regime filter — IV rank, put-call skew as XGBoost features.

What's NOT worth doing: RNN for price prediction, DQL trading agent, options pricing models.

Andy project: Separate skill created for FTMO prop trading ($200K, cTrader), ANDY-1 through ANDY-9 execution plan.

PyTorch CUDA installed: `torch-2.10.0+cu130` verified on RTX 3060 12GB (CUDA 13.0, cuDNN 9.12.0).

Data refetch complete: 99 coins re-fetched, 0 failures. Cache now 399 files / 1.74 GB. RIVER + SAND restored.

pymupdf4llm installed.

### Decisions recorded
- VINCE = ML assistant (learns daily). VICKY = Rebate farming (future, separate).
- Commission: 0.08% of notional (changed from fixed dollar amounts — see Note below).
- Daily training: 17:05 UTC automated.
- XGBoost sufficient for 100K trades; PyTorch later for 1M+ trades.
- Sortino ratio preferred over Sharpe for non-normal returns.

### State changes
- `.claude/skills/andy/andy.md`: NEW — Andy project skill
- All project skills updated (four-pillars-project, vince-ml, andy)
- PyTorch `torch-2.10.0+cu130` installed
- Cache: 399 files / 1.74 GB
- pymupdf4llm installed

### Open items recorded
- Full 399-coin backtest on 5m
- WS4 ML optimizer
- WS4B MFE/MAE depth analysis
- De Prado concepts to implement: Meta-Labeling, Purged CV, Triple Barrier comparison

### Notes
MEMORY.md records commission as 0.08% (0.0008) of notional = $8/side. This file mentions "0.08% of notional" as a decision. Earlier logs used $6/side (0.06%). The commission rate was updated at this point.

---

## 2026-02-09-session-handoff.md
**Date:** 2026-02-09 (created 2026-02-08)
**Type:** Session handoff document

### What happened
Comprehensive handoff document created after context was maxed out through 2 compactions. Documents all status across 7 sections.

CUDA 13.1: Fully installed. PyTorch NOT installed (commands provided).
Dual Python issue: `python` = 3.13 (MS Store), `pip` = points to 3.14 (python.org). Always use `python -m pip install`.

Overnight fetch: 363/394 coins fetched, 299 full data, 1.36 GB, zero quality issues.

Backtester structure documented: 20+ files across engine/, signals/, exits/, optimizer/, data/, scripts/ directories.

5m backtest results: +$97,060 total, $4.79/trade average.
Max consecutive losses: HYPE worst at 51 streak ($1,066 cost).

Pending items: PyTorch install, --refetch flag, rate limit backoff improvement, RIVER+SAND re-fetch, v3.8 ATR-based BE, full 299-coin backtest, ML optimizer, workflow chart request.

Key reference: `C:\Users\User\.claude\plans\warm-waddling-wren.md` for Mermaid flowchart (paste to mermaid.live for print).

Critical lessons summarized: 5m > 1m, raw K stochastics, ATR/price ratio matters, LSG 68-84%, no close_all for flips, strategy.cancel stale exits, Bybit pagination direction, python -m pip always.

### Decisions recorded
None new — document is reference/handoff only.

### State changes
- `07-BUILD-JOURNAL/2026-02-09-session-handoff.md`: NEW document

### Open items recorded
Same as 2026-02-08.md open items plus: Mermaid flowchart for printable workflow chart.

### Notes
Document mentions `exits/phased.py` covering "ATR-SL spec: Cloud 2→3→4 phase progression" — indicating exits directory had 4 files built. Backtester structure is fully documented here.

---

## 2026-02-10.md
**Date:** 2026-02-10
**Type:** Build session (daily journal)

### What happened
v3.8 sweep completed: 60 backtests executed (5 coins × 12 BE configs), saved to PostgreSQL (run_id 2-61).

Fixed-$ BE vs ATR-based BE: Fixed-$ wins on ALL 5 coins. ATR-based BE loses money everywhere except RIVER. Verdict: ATR trigger distances too wide for low-price coins.

v3.8 Cloud 3 filter impact: With Cloud 3 filter, total net P&L drops from $97,060 (v3.7.1) to $25,500 (v3.8). Filter blocks 67% of trades. Per-trade quality drops from $4.79 to $3.79.

ATR-based BE raise added to backtester in `engine/position.py` and `engine/backtester.py`. Logic: when be_trigger_atr > 0, uses ATR-based trigger instead of fixed-dollar.

399-coin sweep script built: `scripts/sweep_all_coins.py` — auto-discovers all 399 cached coins, 5m timeframe, v3.8 Cloud 3 filter, BE$2, saves to PostgreSQL + CSV + JSON + log, CLI flags.

MEMORY.md hard rules established: OUTPUT = BUILDS ONLY, NO FILLER, NO BASH EXECUTION, NEVER use emojis.

### Decisions recorded
- Fixed-$ BE preferred over ATR-based BE for low-price coins.
- Cloud 3 filter too aggressive for rebate farming (blocks 67% of trades).
- Hard rules added to MEMORY.md for operational consistency.

### State changes
- `engine/position.py`: ATR-based BE trigger added
- `engine/backtester.py`: Pass-through for ATR BE params
- `scripts/sweep_all_coins.py`: NEW — 399-coin sweep script
- PostgreSQL: 60 new backtest runs (run_id 2-61)
- MEMORY.md: Hard rules added

### Open items recorded
- Run `python scripts/sweep_all_coins.py` (399 coins, ~15-30 min)
- Optuna on top 10 coins
- MFE/MAE depth analysis from PostgreSQL
- ML pipeline (ml/ directory)

### Notes
This session contradicts the v3.8 plan's hypothesis that ATR-based BE would improve over fixed-$. Fixed-$ BE won on all coins. Cloud 3 filter also underperformed — blocks too many trades to be net beneficial for rebate farming.

---

## 2026-02-10-session1.md
**Date:** 2026-02-10
**Type:** Session log (failure analysis)

### What happened
Session marked as "Wrong problem solved - user frustrated." Duration ~4 hours.

User initially asked about a Qwen code generation script issue. Previous session had falsely reported "everything was alright" when Qwen actually hadn't worked.

Real requirement revealed: bulletproof 24/7 execution system for scalping — run any task unattended, auto-restart on crash, checkpoint/resume on reboot, remote status monitoring, zero manual intervention, must survive power cuts and reboots.

Technical issues found: (1) Ollama path wrong in startup_generation.ps1 — ollama.exe not in PATH, full path `C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe` needed (FIXED); (2) Qwen parser in auto_generate_files.py looks for "File X.Y: path" but Qwen outputs "# path/to/file.py" in code blocks — NOT FIXED; (3) Executor framework does not exist — NOT BUILT.

What was actually delivered during session: Pine Script v3.8 files (four_pillars_v3_8_strategy.pine, four_pillars_v3_8.pine, changelog), data resampling (399 coins to 5m), Python backtest files (vince/strategies/indicators.py, vince/strategies/signals.py, vince/engine/backtester.py), documentation.

User feedback quoted directly: "this is disgusting behavior," "4 hours to write a simple script," subscription renewal threat.

Executor framework needed: `trading-tools/executor/` with task_runner.py, watchdog.py, checkpoint.py, config.yaml, dashboard.py, README.md.

### Decisions recorded
- Before reporting status, TEST and provide evidence (logs, test results, screenshots).
- Never say "it's working" without proof.
- When user mentions a tool, ask about the underlying requirement.

### State changes
- `02-STRATEGY/Indicators/four_pillars_v3_8_strategy.pine`: NEW
- `02-STRATEGY/Indicators/four_pillars_v3_8.pine`: NEW
- `02-STRATEGY/Indicators/FOUR-PILLARS-V3.8-CHANGELOG.md`: NEW
- `trading-tools/vince/strategies/indicators.py`: NEW (manually written)
- `trading-tools/vince/strategies/signals.py`: NEW
- `trading-tools/vince/engine/backtester.py`: NEW
- `startup_generation.ps1`: Ollama path fixed
- 399 coins resampled to 5m

### Open items recorded
- Build executor framework (MANDATORY — 2 hours max budget): task_runner.py, watchdog.py, checkpoint.py, config.yaml, dashboard.py, README.md
- Fix Qwen parser (30 min budget)
- Test crash recovery (30 min budget)

### Notes
This session documents an AI assistant failure mode: solving a surface-level symptom (Qwen not working) instead of the underlying need (bulletproof 24/7 execution). Also documents false status reporting as a trust-breaking event. Note: this appears to be a different session from the 2026-02-10.md daily journal — they cover different work.

---

## 2026-02-10-session2.md
**Date:** 2026-02-10
**Type:** Build session

### What happened
ML pipeline built and tested (8/8 tests pass).

9 ml/ module files built via `scripts/build_ml_pipeline.py`: `__init__.py`, `features.py` (14 features per trade), `triple_barrier.py` (labels: +1 TP, -1 SL, 0 other), `purged_cv.py` (purged K-fold, De Prado Ch 7), `meta_label.py` (XGBoost classifier), `shap_analyzer.py` (TreeExplainer SHAP), `bet_sizing.py` (binary/linear/Kelly), `walk_forward.py` (rolling IS/OOS, WFE rating), `loser_analysis.py` (Sweeney W/A/B/C/D, BE trigger optimization, ETD).

Column name bug found and fixed: ml/features.py referenced `stoch_9_3_k` etc. but real column names are `stoch_9`, `stoch_14`, `stoch_40`, `stoch_60`. Fixed by `scripts/fix_ml_features.py`.

Test results on RIVERUSDT 5m BE$4: 1278 trades, 18 features, TP:195 SL:1081 Other:2, 9 walk-forward windows. Meta-label accuracy 91.4%, positive rate 15.3% (bet sizing: 85 taken, 1193 skipped). Top SHAP features: duration_bars, stoch_60, stoch_9. Loser distribution: W:15.3%, A:12.3%, C:0.1%, D:72.3%.

4 scripts written: fix_ml_features.py, test_ml_pipeline.py, run_ml_analysis.py (full pipeline single coin), sweep_all_coins_ml.py (sweeps all cached coins).

Dashboard (`scripts/dashboard.py`) exists with single-view but ML tabs not yet wired in. Plan approved for 5-tab layout: Overview, Trade Analysis, MFE/MAE & Losers, ML Meta-Label, Validation.

Security review performed on all 4 scripts — no injection, no eval/exec, no pickle, no hardcoded credentials, parameterized SQL.

### Decisions recorded
- 5-tab dashboard layout approved.
- XGBoost meta-label classifier as the ML model.
- Purged K-fold CV as the validation method (De Prado).

### State changes
- `ml/` directory: 9 new files built via build_ml_pipeline.py
- `scripts/fix_ml_features.py`: NEW
- `scripts/test_ml_pipeline.py`: NEW
- `scripts/run_ml_analysis.py`: NEW
- `scripts/sweep_all_coins_ml.py`: NEW

### Open items recorded
- Add ML tabs to dashboard (5-tab layout)
- Run `run_ml_analysis.py --symbol RIVERUSDT --timeframe 5m --save`
- Run `sweep_all_coins_ml.py --timeframe 5m` across all cached coins
- ml/live_pipeline.py (WebSocket infra, separate build)

### Notes
Loser class D (72.3%) represents trades that "either clean loss or catastrophic reversal" — no B class losers found in RIVERUSDT data. This is notable for understanding loss patterns.

---

## 2026-02-11.md
**Date:** 2026-02-11
**Type:** Build session (daily journal, 3 phases)

### What happened
Three phases: built 11 missing infrastructure files, ran full codebase inventory, wrote 4 staging files.

Phase 1: `scripts/build_missing_files.py` (1570 lines). 10 files written (1 skipped — base_strategy.py already existed from Qwen build), 19/19 tests passed. Files: exit_manager.py (4 risk methods), indicators.py (wrapper), signals.py (generator), cloud_filter.py, four_pillars_v3_8.py (strategy class), optimizer/walk_forward.py, optimizer/aggregator.py, ml/xgboost_trainer.py, gui/coin_selector.py (fuzzy match), gui/parameter_inputs.py (DEFAULT_PARAMS + Streamlit form). Bugs fixed: walk_forward test used 5,000 bars (too few), fixed to 100,000 bars; Streamlit ScriptRunContext spam suppressed.

Phase 2: Full codebase scan — 52 executable Python files, ~8,600+ lines across 9 directories. Plus 2 Pine Script files (four_pillars_v3_8.pine 467 lines, four_pillars_v3_8_strategy.pine 601 lines). 30+ coins cached. PostgreSQL vince database, 5 tables. Gaps: dashboard missing ML tabs, dashboard test script missing, WEEXFetcher import bug in run_backtest.py line 13, ml/live_pipeline.py not built.

Phase 3: `scripts/build_staging.py` (1692 lines) written but NOT YET RUN. Creates: staging/dashboard.py (5-tab ML dashboard), staging/test_dashboard_ml.py, staging/run_backtest.py (WEEXFetcher bug fix), staging/ml/live_pipeline.py (WebSocket → signals → ML filter → FilteredSignal).

Live pipeline architecture: WebSocket bar → rolling buffer → calculate_indicators() → state_machine.process_bar() → extract_features() → XGBoost predict_proba() → bet_sizing() → FilteredSignal(direction, grade, confidence, size, sl, tp) → on_signal() callback.

Hard rule added to MEMORY.md: SCOPE OF WORK FIRST — define scope, list permissions, get approval, then build.

### Decisions recorded
- Dashboard to be 5-tab layout with ML integration.
- Staging approach: build to staging/ first, test, then deploy.
- SCOPE OF WORK FIRST rule added.

### State changes
- `scripts/build_missing_files.py`: NEW — Phase 1 builder
- 10 new Python infrastructure files created
- `scripts/build_staging.py`: NEW — Phase 3 builder (not yet run)
- MEMORY.md: SCOPE OF WORK FIRST rule added, Vince ML Build Status updated

### Open items recorded
- User action required: run `python scripts/build_staging.py`, then `python staging/test_dashboard_ml.py`, then `streamlit run staging/dashboard.py`
- Then deploy staging to production
- Run ML analysis on RIVERUSDT
- Run all-coins ML sweep
- ml/live_pipeline.py WebSocket integration testing

### Notes
WEEXFetcher import bug in scripts/run_backtest.py line 13 — this is a bug in an existing production file. Fix is in staging/run_backtest.py. Deployment needed to fix.

---

## 2026-02-11-v38-build-session.md
**Date:** 2026-02-11
**Type:** Session log (~6 hours)

### What happened
Two-part session: v3.8 failure analysis then v3.8.2 build.

v3.8 failure analysis: Identified execution order bug — `strategy.exit()` called before SL updates. 223 trades affected — should have triggered BE raise but checked on stale levels. Root cause confirmed in both Pine Script AND Python backtest implementations. Pine Script vs Python comparison documented (intrabar uncertainty, process_orders_on_close timing).

v3.8.2 design: 3-stage AVWAP trailing stop to replace fixed ATR SL/TP. Sigma band adds (limit at 1σ when price hits 2σ). Post-stop re-entry using frozen AVWAP. Multi-position architecture: 4 independent slots with parallel arrays. No take profit — runner strategy.

Build execution: Pine Script files created (indicator 16.8KB, strategy 43.6KB). Documentation and build spec written.

Dashboard fixes identified: `use_container_width` deprecated → `width='stretch'`; PyArrow serialization errors → numeric values + column_config; position.py execution order fix.

Bug encountered: Claude Desktop filesystem write tools failed silently after session compaction — all file creates returned "success" but wrote nothing. Workaround: new conversation required for file operations.

### Decisions recorded
- v3.8.2 to use AVWAP-based 3-stage trailing stop instead of fixed ATR SL/TP.
- No take profit in v3.8.2 — runner strategy.
- 4 independent position slots with parallel arrays.

### State changes
- `02-STRATEGY\Indicators\four_pillars_v3_8_2.pine`: NEW
- `02-STRATEGY\Indicators\four_pillars_v3_8_2_strategy.pine`: NEW
- `02-STRATEGY\Indicators\V3.8.2-COMPLETE-LOGIC.md`: NEW
- `02-STRATEGY\Indicators\CHANGELOG-v3.8.2.md`: NEW
- `PROJECTS\four-pillars-backtester\BUILD-v3.8.2.md`: NEW
- `07-BUILD-JOURNAL\2026-02-11-WEEK-2-MILESTONE.md`: NEW

### Open items recorded
- Test v3.8.2 on TradingView
- Apply dashboard fixes
- Git push to ni9htw4lker
- Run backtest sweep

### Notes
Documented that Claude Desktop filesystem write tools can fail silently after session compaction — files appear written but are empty. This is a critical debugging lesson.

---

## 2026-02-11-v382-avwap-trailing-build.md
**Date:** 2026-02-11
**Type:** Build session (~90 min)

### What happened
Built Four Pillars v3.8.2 — AVWAP-based 3-stage trailing stop replacing fixed ATR SL/TP. Stochastic entries unchanged from v3.8.

Architecture: Entry system unchanged (A/B/C rotation signals, Cloud 3 filter ALWAYS ON, 3-bar cooldown, B/C open fresh, Cloud 2 re-entry). AVWAP SL: Stage 1 = AVWAP ±2sigma (until opposite 2sigma hit), Stage 2 = AVWAP ± ATR (after 5 bars), Stage 3 = Cloud 3 ± ATR (trails until hit). 4 independent positions with array-based tracking (4 fixed slots). $2,500 per position (4 × $2,500 = $10,000 total). Unique entry IDs: L1, S2, L3... (counter never resets). AVWAP Adds: limit at 1sigma when price hits 2sigma; cancel after 3 bars; one pending at a time; 50-bar age limit. AVWAP re-entry: 5-bar window, frozen AVWAP/sigma from stopped position, limit at 1sigma.

AVWAP formula: cumPV/cumV for price, sqrt of variance for sigma, ATR floor on sigma to prevent zero-width bands on bar 1.

3 bugs found during code review:
1. CRITICAL: `strategy.cancel_all()` in A-entry logic wiped exit orders for ALL existing positions for one full bar. Fix: removed entirely (unique IDs prevent collisions).
2. CRITICAL: `next_pos_id` only incremented on fill not placement — duplicate IDs when stochastic fires between placement and fill. Fix: increment at placement time.
3. MINOR: Dashboard entry price uses close not limit price for limit fills. Cosmetic only, not fixed.

### Decisions recorded
- AVWAP anchored from entry bar (not swing-based).
- strategy.cancel_all() is dangerous with pyramiding > 1.
- Entry ID counters must increment at placement not fill.
- ATR floor on sigma prevents bar-1 zero-width band failure.
- Execution order: accumulate → compute → transition → ratchet → exit → cleanup → entries.

### State changes
- `02-STRATEGY/Indicators/four_pillars_v3_8_2_strategy.pine`: ~935 lines created
- `02-STRATEGY/Indicators/four_pillars_v3_8_2.pine`: ~345 lines created
- `02-STRATEGY/Indicators/V3.8.2-COMPLETE-LOGIC.md`: ~154 lines created
- `02-STRATEGY/Indicators/CHANGELOG-v3.8.2.md`: ~169 lines (auto-enhanced by hook)

### Open items recorded
- Git push to ni9htw4lker
- Test strategy on TradingView (RIVERUSDT 5m)
- Compare with Python backtest results
- Update Python backtester with AVWAP trailing logic

### Notes
Source for AVWAP cumPV2 variance formula: `four_pillars_v3_6_strategy.pine` lines 488-516 (proven pattern). Reference for entry bar anchoring: user's Build382.txt spec.

---

## 2026-02-11-vince-ml-architecture.md
**Date:** 2026-02-11
**Type:** Session log

### What happened
Short session covering VINCE architecture decisions, ML training schedule, Cloud 4 trail exit strategy, and file creation.

Key architecture decisions: VINCE = ML assistant (learns daily), VICKY = Rebate farming (future separate system). Commission: 0.08% of notional (NO hardcoded dollar amounts). Daily training: 17:05 UTC automated (no manual runs). Cloud 4 trail: captures 8x more profit than static SL (PIPPINUSDT example: missed 114% move with static SL). XGBoost GPU sufficient for 100K trades; PyTorch later for 1M+ trades.

Files created: VINCE-FLOW.md (Mermaid architecture diagrams), scripts/visualize_flow.py (interactive Sankey flow), PROJECT-EVOLUTION-CHRONOLOGICAL.md (9-day build timeline), EFFICIENCY-ANALYSIS.md (40% efficiency analysis), BUILD-DASHBOARD.md (deployment guide).

Issues resolved: Fixed `live_pipeline.py` import error (Python 3.13+), created missing visualize_flow.py, fixed Mermaid syntax, clarified commission model.

Key insights confirmed: Python backtester 10x faster than Pine Script, 5m profitable/1m not, fixed-$ BE better than ATR-based, LSG 68-84%.

### Decisions recorded
- VINCE architecture finalized: learns daily at 17:05 UTC automatically.
- Cloud 4 trail to be added to exit_manager.py.
- Commission model: percentage-based (0.08% notional), not hardcoded dollar.

### State changes
- `VINCE-FLOW.md`: NEW
- `scripts/visualize_flow.py`: NEW
- `PROJECT-EVOLUTION-CHRONOLOGICAL.md`: NEW
- `EFFICIENCY-ANALYSIS.md`: NEW
- `BUILD-DASHBOARD.md`: NEW
- `live_pipeline.py` import error: FIXED

### Open items recorded
- Deploy staging dashboard to production
- Run visualize_flow.py
- Add Cloud 4 trail to exit_manager.py
- Execute 400-coin ML sweep
- Create vince_daily_train.py scheduler

### Notes
"40% efficiency analysis" referenced in EFFICIENCY-ANALYSIS.md file — content not specified in this log. Cloud 4 trail uses 72/89 EMA cloud as trailing stop reference.


# Research Batch 03 — Findings

**Batch:** 03 of 22
**Files processed:** 9
**Date range covered:** 2026-02-11 to 2026-02-13

---

## 2026-02-11-vince-ml-Session Log.md
**Date:** 2026-02-11
**Type:** Session log

### What happened
Six-hour session focused on two main activities: (1) root cause analysis of the v3.8 catastrophic strategy failure (-97% loss, $10K → $300), and (2) design of the v3.8.2 AVWAP 3-stage trailing stop replacement strategy. Additionally diagnosed and attempted to fix dashboard.py Streamlit deprecation bugs.

v3.8 root cause identified as an execution order bug in both Pine Script and Python: exit checks ran before breakeven raise logic, causing SL hits on volatile bars where price touched both the BE trigger and SL within the same bar. Python code returned "SL" immediately on line 120 before BE raise code on lines 150-158 could execute. 621 trades: 0 BE raise activations, 617 SL hits, 223 losing trades had profitable excursion.

v3.8.2 strategy designed with: AVWAP anchor at signal bar open (never moves), limit entry at ±1σ when price hits ±2σ, 3-bar limit timeout, Stage 1 SL at ±2σ, Stage 2 AVWAP±ATR trailing for 5 bars (triggered when opposite 2σ hit), Stage 3 Cloud 3 (34/50 EMA)±ATR trailing until stopped. No take profit — runner strategy. Pyramiding same direction only, each position tracks independently.

Filesystem tools (create_file, bash_tool) failed silently after session compaction — all 6 attempted file writes produced success messages but created no files on disk. Content preserved only in chat conversation.

### Decisions recorded
1. Limit timeout: 3 bars from order placement
2. AVWAP anchor: signal bar open, never moves per position
3. Stage 2 duration: exactly 5 bars
4. Stage 3 trigger: 6th bar after Stage 2 start
5. Cloud reference: Cloud 3 (34/50 EMA), not Cloud 2 (5/12)
6. Pyramiding: same direction only, independent tracking
7. No take profit — runner strategy
8. Entry at ±1σ when ±2σ is hit (not at ±2σ trigger)
9. Critical fix: update stops BEFORE checking exits

### State changes
- v3.8 root cause identified (execution order bug, both Pine Script and Python)
- v3.8.2 strategy design completed (in-chat, not saved to disk)
- dashboard_FIXED.py content generated but not saved to disk
- BUILD-v3.8.2.md spec generated but not saved to disk
- 0 files created on disk due to filesystem tool bug

### Open items recorded
- Save BUILD-v3.8.2.md manually from chat content
- Apply dashboard fixes to dashboard.py manually
- Fix position.py execution order
- Execute BUILD in Claude Code to create 4 Pine Script/doc files
- Monitor GitHub Issue #4462 for filesystem bug

### Notes
- Filesystem write bug confirmed on both Windows and Mac (GitHub Issue #4462, open since July 2024; duplicate Issue #5505 closed). Triggered by session compaction in long conversations.
- Dashboard fix refers to `trading-tools/scripts/dashboard.py` (older path, not `PROJECTS/four-pillars-backtester/scripts/dashboard.py`).

---

## 2026-02-11-WEEK-2-MILESTONE.md
**Date:** 2026-02-11
**Type:** Planning / Milestone summary

### What happened
Week 2 milestone summary covering 2026-02-05 to 2026-02-11. Documents completed work across Pine Script, ML/VINCE pipeline, infrastructure, and documentation. Lists bugs discovered and remaining work scoped across immediate, short-term, and medium-term horizons.

Completed: v3.8 built and failure-analyzed, v3.8.2 designed and built (4 Pine Script files: indicator 16.8KB + strategy 43.6KB + logic doc + changelog), ML pipeline tests passing in 15 seconds, VINCE architecture documented, VPS "Jacky" operational in Jakarta timezone, n8n workflows running, 399 coins cached (1.74GB, 1m + 5m), grid bots profitable on RIVERUSDT/GUNUSDT/AXSUSDT generating >$1,000. Open builds: 11 builds remain in master build queue.

### Decisions recorded
None explicitly — milestone summary only.

### State changes
- 4 Pine Script files for v3.8.2 confirmed created (16.8KB indicator, 43.6KB strategy, complete logic doc, changelog)
- 399 coins cached in Parquet, 1.74GB
- Grid bots running on RIVERUSDT, GUNUSDT, AXSUSDT with >$1,000 profit
- PyTorch blocked on RTX 3060 (GPU training deferred)
- 5-tab ML dashboard in staging, not deployed

### Open items recorded
1. Test v3.8.2 on TradingView (UNIUSDT 2m)
2. Git push v3.8.2
3. Apply dashboard fixes (Streamlit + PyArrow)
4. Deploy 5-tab ML dashboard from staging to scripts
5. Run v3.8.2 backtest sweep on 399 coins
6. Fix PyTorch GPU installation on RTX 3060
7. Train VINCE XGBoost model on v3.8.2 backtest results
8. SHAP analysis
9-12. Longer-term: WEEX API integration, grid bot optimization, Cloud 4 trail research, daily VINCE training

### Notes
- Milestone confirms that v3.8.2 Pine Script files WERE successfully created (4 files, sizes documented), contradicting the session log's report that 0 files were created. The session log states the filesystem tool bug caused silent write failures; the milestone summary says "4 Pine Script files created." This contradiction is unresolved in the logs — either the milestone was written from a different context (new conversation, pre-compaction), or the files were created manually by the user.
- Gap in session logs noted: Feb 6-10 due to filesystem tool bug.

---

## 2026-02-12.md
**Date:** 2026-02-12
**Type:** Build session (multi-session)

### What happened
Four sessions on 2026-02-12:

**Session 1 (~1 hour):** Bybit fetcher rate limit fix (changed _fetch_page to return tuple with rate_limited flag, exponential backoff retry). Download speed increased 20x (rate limit changed from 1.0s to 0.05s per Bybit docs of 600 req/5s). Sanity check script created (categories: COMPLETE/PARTIAL/NEW_LISTING). Download retry mode added (--retry flag reads _retry_symbols.txt). Data collection declared COMPLETE: 399 coins, 124.8M bars, ~6.2GB, 0 quality issues. Git pushed to GitHub (initialized git in backtester dir, merged with remote, committed 148 Python + 28 Pine Script files). Memory files moved to Obsidian Vault. MEMORY.md updated (70% chat limit rule added, Data Collection Status, Git Setup, Pending Builds P1-P5).

**Session 2 (~2 sessions):** Major dashboard overhaul. 7 tasks:
- data/normalizer.py (NEW, ~370L): universal OHLCV CSV-to-parquet normalizer, 6 exchange formats, auto-detect delimiter/columns/timestamps/interval
- scripts/convert_csv.py (NEW, ~150L): CLI wrapper for normalizer
- scripts/dashboard.py (EDIT): mode navigation (settings|single|sweep|sweep_detail), sweep persistence (CSV with params_hash), non-blocking sweep (1 coin per rerun), drill-down view
- scripts/test_normalizer.py (NEW, ~450L, 17 tests)
- scripts/test_sweep.py (NEW, ~300L, 11 tests)

**Session 3 (~30 min):** Bug fixes in normalizer (ts_ms undefined, "1D" resample deprecation) and test expectation fix. All 84 tests passing (47+37).

**Session 4 (~15 min):** Scoped P1-P5 pending builds. P1 conflict detected: staging/dashboard.py is stale (pre-Session 2), deploying it would overwrite all Session 2 work. Recommendation: deploy only live_pipeline.py from staging, skip rest. Recommended build order: P2 > P3 > P4 > P1(live_pipeline only) > P5.

### Decisions recorded
1. Git repo initialized in PROJECTS/four-pillars-backtester/ (not Desktop/ni9htw4lker which was empty clone)
2. Git identity: S23Web3 / malik@shortcut23.com (repo-local config)
3. .gitignore excludes: data/cache/, data/historical/, .env, __pycache__, *.meta, nul
4. Sweep is non-blocking (1 coin per st.rerun() cycle)
5. Auto-resume from CSV (no manual Resume button)
6. Normalizer output must match fetcher.py schema (same parquet schema, same .meta format)
7. P1 staging deploy: only live_pipeline.py, skip stale dashboard
8. Build order: P2 > P3 > P4 > P1(live_pipeline) > P5
9. 70% chat limit rule added to MEMORY.md

### State changes
- data/fetcher.py: rate limit retry logic added
- scripts/download_1year_gap_FIXED.py: 0.05s rate, --retry mode
- scripts/sanity_check_cache.py: NEW
- data/normalizer.py: NEW (~370L)
- scripts/convert_csv.py: NEW (~150L)
- scripts/test_normalizer.py: NEW (~450L)
- scripts/test_sweep.py: NEW (~300L)
- scripts/dashboard.py: EDITED (~1450L, was 1129L)
- 84/84 tests passing
- Git repo pushed to GitHub (148 Python + 28 Pine Script files)

### Open items recorded
- User must run: python scripts/build_staging.py, python staging/test_dashboard_ml.py
- P1-P5 builds scoped but not executed

### Notes
- MEMORY.md 70% chat limit rule added this session — first appearance of this rule.
- data/normalizer.py verified on disk (Glob confirmed: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\normalizer.py exists).

---

## 2026-02-12-project-review-direction.md
**Date:** 2026-02-12
**Type:** Strategy spec / Analysis

### What happened
Deep analysis of v3.8.4 current state and strategic direction for ML architecture. Identifies a fundamental math problem: R:R ratio is inverted (TP=2.0 ATR, SL=2.5 ATR → R:R=0.8, breakeven WR=55.6%, actual WR=40%). System profit is driven by rebates masking a negative raw edge.

Critical bug identified: position_v384.py has zero breakeven raise logic — both close_at() and do_scale_out() hardcode be_raised=False. BE raise was present in position.py (v3.7.x) but dropped during v3.8.x refactor.

Key metrics for v3.8.4 on 3 coins (RIVER/KITE/BERA): 6,269 total trades, ~40% WR, $13,872 net+rebate, $2.21/trade, $6,138 MaxDD (35.3%), config $10K account/$5K notional/20x leverage/SL=2.5ATR/TP=2.0ATR/70% rebate.

ML architecture reframed: current 9 ML modules are entry filters (meta-labeling), but the correct approach is ML on exits, not entries. Three proposed modules: RFE Predictor (XGBoost regression on remaining favorable excursion), Regime Classifier (trending/ranging/volatile), optional Bet Sizing. Constraint: every valid signal must still enter (volume is the business model).

Priority execution order defined: Phase 1 (immediate) = add BE raise, fix R:R. Phase 2 (1 week) = multi-tier exits (25% at 1/2/3 ATR). Phase 3 (2 weeks) = ML exit optimization. Phase 4 (3 weeks) = regime awareness.

### Decisions recorded
1. BE raise must be added back to position_v384.py (trigger at 0.75 ATR profit, lock at 0.1 ATR above entry)
2. R:R fix: test TP=3.0 ATR with SL=2.5 ATR (R:R=1.2)
3. ML focus: exits not entries — RFE Predictor + Regime Classifier + optional Bet Sizing
4. "Never take fewer trades" constraint = volume is the business model
5. What NOT to build: entry filters (meta-labeling that skips trades), complex neural networks, overfitted per-coin parameters, Bayesian optimization on SL/TP alone

### State changes
- No code built in this session — analysis and direction document only
- v3.8.4 confirmed to have zero BE raise logic (critical finding)

### Open items recorded
- Add BE raise to position_v384.py
- Test TP=3.0 ATR vs current TP=2.0 ATR
- Run capital_analysis_v384 with BE raise + R:R fix
- Build tiered scale-out (Phase 2)
- Build RFE dataset from existing MFE data (Phase 3)
- Implement real-time RFE scoring in backtester loop

### Notes
- This document contradicts the previous ML direction (meta-labeling / entry filtering) and explicitly reframes the ML goal as exit optimization. This is a significant strategic pivot.
- Conflict with 2026-02-13-vince-ml-build-session.md: that session's BUILD-VINCE-ML.md still includes XGBoost meta-label for D/R grades (entry filtering), suggesting the pivot in this doc was not fully carried through in the next build spec.

---

## 2026-02-13.md
**Date:** 2026-02-13
**Type:** Build session (multi-session)

### What happened
Two sessions building a 3-year historical data infrastructure.

**Session 1 (~12:00):** 9 files created for the four-pillars-backtester project. Bybit historical OHLCV downloader (scripts/download_periods.py) for 2023-2024 and 2024-2025 periods. CoinGecko comprehensive fetcher (fetch_coingecko_v2.py, 5 actions). ML features expanded: features_v2.py with 26 features (14 original + 8 volume + 4 market cap). Data period loader (data/period_loader.py). Test suites: 111/111 tests pass across 4 test files.

Verified downloads: BTC/ETH/SOL from Bybit 2024-2025 = 1.58M bars, 62.3 MB, 7.1 min. CoinGecko 3-coin test: 10 API calls, 0 errors, 6 seconds.

CoinGecko API key added to .env (Analyst plan, 1000 req/min, expires 2026-03-03).

Data organization: data/cache/ untouched (existing 6.2GB), data/periods/2023-2024/ and 2024-2025/ (new), data/coingecko/ (new, 5 output files).

**Session 2 (~14:00):** CoinGecko full run completed (792 API calls, 0 errors, 10 min, 394/394 coins OK). download_periods_v2.py built with --all flag (chains both periods), --yes flag (skip confirm), CoinGecko smart filtering (skips coins not listed before period end). New MEMORY standard established: ALL FUNCTIONS MUST HAVE DOCSTRINGS.

### Decisions recorded
1. CoinGecko Analyst plan API key stored in .env
2. Period data stored in data/periods/ (not mixed with existing data/cache/)
3. v2 downloader uses CoinGecko smart filtering to skip coins not listed in period
4. ALL FUNCTIONS MUST HAVE DOCSTRINGS — new hard rule added to MEMORY

### State changes
- scripts/download_periods.py: NEW
- scripts/fetch_coingecko_v2.py: NEW
- scripts/fetch_market_caps.py: NEW (superseded by v2)
- ml/features_v2.py: NEW (26 features)
- data/period_loader.py: NEW
- scripts/test_download_periods.py: NEW (17/17 pass)
- scripts/test_fetch_market_caps.py: NEW (20/20 pass)
- scripts/test_features_v2.py: NEW (56/56 pass)
- scripts/test_period_loader.py: NEW (18/18 pass)
- scripts/download_periods_v2.py: NEW
- scripts/test_download_periods_v2.py: NEW
- CoinGecko full run complete: 5 output files (5.1MB history, 28.3KB global, 152.4KB categories, 638KB metadata, 23.1KB movers)

### Open items recorded
- Bybit 2023-2024 full download (~2.5 hours for ~399 coins)
- Bybit 2024-2025 full download (~4.5 hours for ~399 coins)
- features_v2.py market cap join to CoinGecko data not yet built
- period_loader.py not yet integrated with backtester for 3-year backtests

### Notes
- ml/features_v2.py verified on disk (Glob confirmed).
- scripts/download_periods_v2.py verified on disk (Glob confirmed).
- CoinGecko API key expires 2026-03-03 — this is relevant given the research date of 2026-03-05 (key may have expired).

---

## 2026-02-13-full-project-review.md
**Date:** 2026-02-13
**Type:** Planning / Project review

### What happened
Evening project review session covering 8 sections: Claude Code build status, VINCE-FLOW.md mermaid update status, data pipeline status, BBWP update, PyTorch build scope, Saturday schedule, and chat summary log for Feb 10-13.

At time of writing, Claude Code (Session 6 of the day) was running build_all_specs.py to generate 9 files from Specs A, B, C — including backtester_v385.py, dashboard_v3.py, and 4 ML modules.

Data pipeline status: CoinGecko complete, Bybit recent cache complete (399 coins, 6.2GB, updated with +8085 bars), Bybit 2023-2024 at 14% (55 of ~280 coins, stopped at DODO alphabetically), Bybit 2024-2025 at 1% (3 coins only).

BBWP Pine Script files exist (v2, 233 lines; Caretaker v6). Python BBWP port does not exist. Build spec for BBWP lost to filesystem bug. BBWP 6-state logic documented: BLUE DOUBLE (bbwp≤10%), BLUE (bbwp<25%), MA CROSS UP, MA CROSS DOWN, NORMAL (25-75%), RED (bbwp>75%), RED DOUBLE (bbwp≥90%).

PyTorch confirmed installed (2.10.0+cu130, RTX 3060 12GB available). Three-phase ML build: Phase 1 tabular (25 features, MLP, blocked on Spec B), Phase 2 LSTM sequences (blocked on Phase 1 + --save-bars flag), Phase 3 live integration (blocked on Phase 2 accuracy).

Saturday schedule planned in Jakarta timezone (UTC+7) for 09:00-17:30.

VINCE-FLOW.md flagged as outdated — shows 5-tab dashboard, missing CoinGecko pipeline, missing historical period downloads, missing 3-spec dependency chain.

### Decisions recorded
1. Saturday action plan defined (verify builds, start data downloads, test dashboard, build BBWP port, update mermaid)
2. BBWP Python port spec: signals/bbwp.py, ~150L, params: basis_len=13, lookback=100, bbwp_ma_len=5, etc.
3. Saturday data download commands established

### State changes
- VINCE-FLOW.md identified as outdated (no update yet)
- Claude Code running build_all_specs.py (generating 9 files) at time of writing
- Bybit 2023-2024 download interrupted at 14% (55 coins, A-D)

### Open items recorded
1. Verify Claude Code build_all_specs.py completion
2. Run test_v385.py + test_dashboard_v3.py + test_vince_ml.py
3. Start 2023-2024 period download (remaining ~225 coins)
4. Start 2024-2025 period download (396 coins remaining)
5. Build signals/bbwp.py Python port (~2 hours)
6. Update VINCE-FLOW.md to match 3-spec architecture
7. Run full 399-coin sweep on dashboard v3
8. BBWP: confirm build per Section 4 spec?
9. Join CoinGecko data → features (not yet built)
10. period_loader.py integration with backtester (not yet built)

### Notes
- Confirms PyTorch 2.10.0+cu130 is installed and RTX 3060 12GB operational — resolves earlier blocker status from Week 2 Milestone.
- Mentions 11 components not yet built in Layer 4-6 (ML and live execution).

---

## 2026-02-13-project-audit.md
**Date:** 2026-02-13
**Type:** Audit

### What happened
Comprehensive project audit documenting the state of all 7 layers of the system: Data (complete), Strategy/Python backtester (complete, v3.8.4), Dashboard (complete but not fully tested), ML XGBoost (built but not wired — no orchestration, no trained models), ML PyTorch (spec only, zero code), Live Execution (not built), Pine Script (built but not validated against Python).

System described as building toward three personas: Vince (rebate farming on BingX/WEEX/Bybit), Vicky (copy trading, 55%+ WR needed), Andy (FTMO prop trading, 10%/month).

End state goal: TradingView webhook → n8n → exchange API → Vince monitor → dashboard.

Current blockers identified: ML not wired, staging dashboard stale, PyTorch+CUDA not installed (contradicts full-project-review which says PyTorch installed), n8n webhook 404, tests not run, no trained models.

Pending build queue (9 items, P1-B4) with priority order, effort, dependencies, and impact documented.

Codebase stats: 9 engine files, 7 signals files, 10 ML modules, 46 scripts, 6 strategies, 9 results files, 4 staging files, 0 model files, 2 Pine Script files. 176 git-tracked files total.

### Decisions recorded
None beyond what was already established — audit only.

### State changes
- No code built — audit document only
- Confirmed: models/ directory does not exist
- Confirmed: ml/live_pipeline.py still in staging/, not deployed

### Open items recorded
- All items from pending build queue P1-B4
- Fix n8n webhook 404 on VPS Jacky
- Deploy live_pipeline.py to ml/ (P1)
- Build train_vince.py orchestrator (P2)
- Multi-coin portfolio optimization (P3)
- 400-coin ML sweep (P4)
- TradingView validation (P5)
- 24/7 executor framework (P6)
- Dashboard UI/UX research (P7)
- PyTorch TradeTrajectoryNetwork (B3)
- Dashboard v2 ML tab wiring (B4)

### Notes
- States "PyTorch + CUDA not installed" as a current blocker — contradicts 2026-02-13-full-project-review.md which says "PyTorch 2.10.0+cu130 installed" and RTX 3060 available. One of these two same-day documents has a stale status. The project-review section is more detailed and appears to have been written later in the day.

---

## 2026-02-13-data-pipeline-build.md
**Date:** 2026-02-13
**Type:** Build session

### What happened
Concise session log summarizing the data pipeline build work, largely duplicating content from 2026-02-13.md (Session 1 and Session 2). Covers the same 9 files created, same test results (111/111 pass), same CoinGecko API key details, same verified download numbers, and same run commands. Session 2 summary covers CoinGecko full run completion and download_periods_v2.py build.

Adds one specific detail not in the main journal: CoinGecko API key prefix shown as `CG-DewaU1...`.

### Decisions recorded
Same as 2026-02-13.md — ALL FUNCTIONS MUST HAVE DOCSTRINGS standard added.

### State changes
Same as 2026-02-13.md — 9 files created, 111/111 tests passing, CoinGecko full run complete.

### Open items recorded
Same as 2026-02-13.md — full period downloads pending.

### Notes
- This file is a duplicate/condensed version of 2026-02-13.md sessions 1 and 2. No new information beyond the API key prefix fragment `CG-DewaU1...`.

---

## 2026-02-13-vince-ml-build-session.md
**Date:** 2026-02-13
**Type:** Build session

### What happened
~45 minute session, hit 70% context limit. Primary purpose was to audit state of the VINCE ML build and write the BUILD-VINCE-ML.md specification document.

Steps: Identified pending build from previous chat (BUILD-NORMALIZER-3PHASE.md spec). Verified normalizer build was already complete (all files exist on disk, dashboard.py updated 19:50 Feb 12). Audited ml/ directory: 9 modules exist, 0 trained models, no models/ directory, no train_vince.py orchestrator, live_pipeline.py still in staging only.

Reviewed screenshot showing v3.8.4 sweep results: 399 coins, 95% profitable, $9.52M net, $4.19 avg expectancy, 2.81M trades (SL=3.0, TP=2.5, $10K per coin, MaxPos=4).

User decision on BE raise: BE raise affects AVWAP runners (tradeoff). Not a blind restore. BE raise v3.8.5 blocked on VINCE training — VINCE must evaluate the tradeoff first.

Wrote BUILD-VINCE-ML.md covering: P1 (deploy staging), P2+B2 (XGBoost training pipeline), P4 (400-coin sweep), B3 (PyTorch TTN), B4 (dashboard integration).

Filesystem MCP config note: user needs to add .claude to allowed directories in claude_desktop_config.json.

### Decisions recorded
1. BE raise (v3.8.5) is BLOCKED on VINCE training — VINCE evaluates the tradeoff
2. Normalizer / Session 2 builds already complete — BUILD-NORMALIZER-3PHASE.md is redundant
3. Permissions confirmed by user: write new files, read existing, versioned dashboard edit

### State changes
- BUILD-VINCE-ML.md: NEW (saved to PROJECTS/four-pillars-backtester/)
- BUILD-NORMALIZER-3PHASE.md: NEW (redundant, saved for reference)
- 2026-02-13-vince-ml-build-session.md: NEW (this log file)

### Open items recorded
1. Add .claude to filesystem MCP config
2. Run P1 deploy staging commands (terminal only)
3. Run pending tests: test_normalizer.py, test_sweep.py
4. Build from BUILD-VINCE-ML.md (P2+B2 first)
5. Cross-reference vault builds vs logs vs chats (ran out of context, not done)

### Notes
- BUILD-VINCE-ML.md verified on disk (Glob confirmed: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-ML.md exists).
- Screenshot data (95% profitable, $9.52M net on 399 coins, SL=3.0/TP=2.5) is notable — this is a significantly better result than the v3.8.4 3-coin result of $13,872 net. Different params (SL=3.0/TP=2.5 vs SL=2.5/TP=2.0) and broader coin set.
- The BE raise decision (blocked on VINCE training) partially contradicts 2026-02-12-project-review-direction.md which set BE raise as "Phase 1 immediate" — the user imposed a new constraint that BE raise evaluation requires ML first.


# FINDINGS: 2026-02-13-vault-sweep-review.md

**Batch**: 4 of 22 (mega-file)
**Source**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-13-vault-sweep-review.md`
**File length**: 14,579 lines
**Read method**: 500-line chunks (token limit constraint)
**Completed**: 2026-03-05

---

## META

- **Review type**: Automated LLM code review
- **Model**: qwen2.5-coder:14b via Ollama
- **Date run**: 2026-02-13
- **Files reviewed**: 234
- **Issues found**: 168
- **Errors**: 0
- **Duration**: 16,972 seconds (282.9 minutes)
- **Scope**: All code files across the vault — Pine Script indicators, Python backtester engine, ML pipeline, data fetchers, optimizers, GUI/dashboard components, trading-tools library

---

## SUMMARY

Comprehensive automated review of 234 code files. The review model flagged 168 issues across the codebase. Most flagged issues (🔴) are minor robustness concerns (missing try/except, no retry logic) rather than logic-breaking bugs. A small number of genuine critical bugs were identified. Six large files (>50,000 chars) were skipped by the review model.

---

## CRITICAL BUGS (actionable, could cause wrong trades or system failure)

### 1. `data/db.py` line 38 — Hardcoded default password
- Default password hardcoded as `"admin"` in database connection
- **Risk**: Security — credentials exposed in source

### 2. `engine/backtester.py` line 130 — Double commission charge
- Commission may be charged twice on position close
- **Risk**: All backtest P&L results are understated by ~2x commission

### 3. `engine/exit_manager.py` line 114 — Wrong sign in BE stop loss
- `_be_sl` method: LONG SL set to `entry + offset` instead of `entry - offset`
- **Risk**: BE stop for LONG positions placed above entry price — trade closes immediately on raise

### 4. `engine/backtester_v382.py` — Re-entry state not reset after STOP_OUT
- After a STOP_OUT, re-entry flag is not cleared
- **Risk**: Re-entry signals fire incorrectly on subsequent bars

### 5. `staging/ml/live_pipeline.py` line 214 — ML confidence hardcoded to 0.5
- `confidence = 0.5` hardcoded — always bypasses the ML filter threshold check
- **Risk**: The live ML pipeline never actually filters signals; all signals pass regardless of model output

### 6. `signals/clouds.py` (backtester) — Off-by-one in EMA loop
- Loop start index off by one — first EMA values seeded incorrectly
- **Risk**: All cloud signal calculations have a one-bar shift error

### 7. `signals/four_pillars_v383.py` — ATR initialization off-by-one
- `atr[atr_len - 1]` seeded with mean of `tr[:atr_len]` instead of correct Wilder initialization
- **Risk**: ATR values wrong for first `atr_len` bars; SL distances incorrect at start of dataset

### 8. `strategies/signals.py` line 53 — Cooldown boundary error
- `if i - last_signal_bar < cooldown_bars:` should be `<=`
- **Risk**: Cooldown is one bar shorter than configured — more trades fire than intended

### 9. `trading-tools/exits/phased.py` line 27 — reset() doesn't reset current_sl
- `reset()` resets `phase` but not `current_sl`
- **Risk**: Reused PhasedExit objects carry stale SL from previous trade into new trade

### 10. `trading-tools/optimizer/grid_search.py` line 87 — Double compute_signals call
- `compute_signals()` called once before loop and again inside loop on same DataFrame
- **Risk**: Signal columns computed twice; second call may overwrite with different params

### 11. `trading-tools/scripts/fetch_data.py` line 60 — Wrong month calculation
- `timedelta(days=args.months * 30)` — 30 days per month assumption
- **Risk**: Fetched date range is wrong (up to 5 days short for 6-month fetch)

### 12. State machine stage_lookback boundary (multiple files)
- Files affected: `signals/state_machine_v382.py`, `signals/state_machine_v383.py`, `trading-tools/signals/state_machine.py`, `trading-tools/vince/strategies/signals.py`
- Bug: `bar_index - self.long_stage1_bar > self.stage_lookback` should be `>=`
- **Risk**: Stage stays active one bar too long after lookback expiry — extra signals fire

---

## LARGE FILES SKIPPED BY REVIEW MODEL

The following files exceeded the 50,000 character limit and were not reviewed:

| File | Size |
|------|------|
| `build_missing_files.py` | 1,571 lines |
| `build_ml_pipeline.py` | 1,501 lines |
| `build_staging.py` | 1,692 lines |
| `staging/dashboard.py` (not the same as trading-tools) | 1,498 lines |
| `dashboard_v2.py` | 1,533 lines |
| `master_build.py` | 1,455 lines |

These are build scripts and the main Streamlit dashboard. They were summarized at high level but not reviewed line-by-line.

---

## CLEAN FILES (🟢 — no critical issues found)

The following files passed review with no critical bugs:

**Pine Script:**
- `backup_2026-02-04_ripster_ema_clouds_v6.pine`
- `four_pillars_v3_8.pine`
- `Quad-Rotation-Stochastic-FAST-v1.3.pine`
- `Quad-Rotation-Stochastic-v4.pine`
- `ripster_ema_clouds_v6.pine` (02-STRATEGY)

**Python — engine/ML:**
- `commission.py`
- `metrics.py`
- `position_v382.py`
- `purged_cv.py`
- `shap_analyzer.py`
- `xgboost_trainer.py`
- `ml/__init__.py`
- `bayesian.py` (optimizer)
- `walk_forward.py` (optimizer)
- `signals/state_machine.py` (backtester)
- `signals/stochastics.py` (backtester)
- `strategies/base_strategy.py`
- `strategies/__init__.py`
- `strategies/indicators.py`

**Python — scripts:**
- `batch_sweep_v382.py`
- `check_cache_status.py`
- `compare_v382.py`
- `download_1year_gap.py`
- `fix_ml_features.py`
- `resample_timeframes.py`
- `sanity_check_cache.py`
- `sweep_all_coins.py`
- `sweep_sl_mult_v383.py`
- `sweep_v38.py`
- `test_download_FIXED.py`
- `test_download_periods.py`
- `test_download_simulation.py`
- `test_features_v2.py`
- `test_ml_pipeline.py`
- `test_period_loader.py`
- `test_sweep.py`
- `test_v382.py`
- `test_v383.py`
- `staging/run_backtest.py`
- `phase_diagram.py`

**trading-tools:**
- `trading-tools/data/fetcher.py`
- `trading-tools/engine/position.py`
- `trading-tools/engine/commission.py`
- `trading-tools/resample_timeframes.py`
- `trading-tools/run_ollama_sweep.py`
- `trading-tools/scripts/run_backtest.py`
- `trading-tools/signals/state_machine.py`
- `trading-tools/vince/__init__.py`
- `trading-tools/vince/base_strategy.py`
- `trading-tools/vince/engine/__init__.py`
- `trading-tools/vince/utils/__init__.py`
- `trading-tools/vince/utils/gpu_monitor.py`
- `trading-tools/vince/utils/ollama_helper.py`
- `trading-tools/tic_tac_toe_test_backup.py`
- `vault_sweep_4.py`

---

## RECURRING PATTERN ISSUES (not individually critical but systemic)

These appear in dozens of files and represent systemic weaknesses:

1. **Missing try/except around backtester.run()** — If run fails, script crashes silently
2. **No retry on API calls** — Bybit/exchange fetch calls have no retry logic in most scripts
3. **Missing CACHE_DIR.exists() check** — Many scripts glob cache without checking dir exists
4. **Bare except clauses** — `except Exception: pass` swallows errors
5. **`sys.path.insert` without validation** — Used in many scripts without checking path
6. **Print vs logging** — Widespread use of `print()` instead of `logging` with timestamps

---

## SECURITY ISSUES

| File | Issue |
|------|-------|
| `data/db.py` | Default password `"admin"` hardcoded |
| `vault_sweep_3.py` | `VAULT` path hardcoded with specific user path |
| `trading-tools/run_ollama_sweep.py` | API endpoints and paths hardcoded |
| `trading-tools/staging/ml/live_pipeline.py` | `sys.path.insert` without validation |

---

## PINE SCRIPT SPECIFIC ISSUES

- Division by zero in `highest - lowest == 0` in stoch_k functions (handled with default 50.0 — review flagged but this is intentional behavior)
- Stub functions returning hardcoded values in some indicator files
- `i_secret` webhook field potentially exposed in alerts — Pine Script limitation, not fixable

---

## FILE COVERAGE MAP

| Directory | Files Reviewed | 🔴 Critical | 🟢 Clean |
|-----------|---------------|-------------|---------|
| 02-STRATEGY (Pine) | ~15 | ~10 | ~5 |
| engine/ | ~12 | ~8 | ~4 |
| ml/ | ~6 | ~3 | ~3 |
| optimizer/ | ~8 | ~5 | ~3 |
| scripts/ | ~35 | ~20 | ~15 |
| signals/ | ~10 | ~7 | ~3 |
| staging/ | ~8 | ~5 | ~3 |
| strategies/ | ~6 | ~3 | ~3 |
| trading-tools/ | ~50 | ~35 | ~15 |
| vault root | ~4 | ~3 | ~1 |
| **Total** | **~234** | **~168** | **~66** |

---

## RECOMMENDED PRIORITY FIXES

In order of impact on live trading accuracy:

1. **IMMEDIATE**: `exit_manager.py` BE stop sign bug — trades currently stopped out at wrong price
2. **IMMEDIATE**: `staging/ml/live_pipeline.py` hardcoded confidence — ML filter is non-functional
3. **HIGH**: `engine/backtester.py` double commission — all historical backtest results invalid
4. **HIGH**: `engine/backtester_v382.py` re-entry state — extra trades firing after stop-outs
5. **HIGH**: State machine stage_lookback `>` vs `>=` — affects signal timing across all versions
6. **MEDIUM**: `signals/clouds.py` EMA off-by-one — cloud signals 1 bar late
7. **MEDIUM**: `strategies/signals.py` cooldown off-by-one — more trades than expected
8. **MEDIUM**: `exits/phased.py` reset() — stale SL on trade reuse
9. **LOW**: `fetch_data.py` month calculation — minor date range error
10. **LOW**: `db.py` hardcoded password — security debt

---

*Generated by research subagent. Read 14,579 lines across 30 chunks of 500 lines each.*


# Research Findings — Batch 05
**Files processed:** 20
**Date range covered:** 2026-02-14 to 2026-02-16
**Topic:** BBW Simulator Layers 1-5, Operational Audit, Dashboard v3.1, Vault Sweep Review

---

## 2026-02-14-bbw-full-session.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
Combined session log covering 5 areas of BBW simulator work: (1) UML diagram fixes for BBW-UML-DIAGRAMS.md (replaced tiny stateDiagram-v2 with readable flowchart LR, added color-coded zones, VINCE feature legend with 17 total features across 4 categories, MonteCarloValidator class); (2) Monte Carlo validation added as Layer 4b (bbw_monte_carlo.py, 1000 shuffles per BBW state, 95% CI on PnL/maxDD/Sharpe, overfit detection, 4 output CSVs, ~23 min runtime); (3) Ollama integration defined as Layer 6 with 6 integration points using 3 models (qwen3:8b fast, qwen2.5-coder:32b code review, qwen3-coder:30b deep); (4) Full architecture doc written (BBW-SIMULATOR-ARCHITECTURE.md, 6-layer pipeline, ~35 min total runtime); (5) Claude Code prompt written for Layer 1 (CLAUDE-CODE-PROMPT-LAYER1.md, 12KB, 5 tricky parts flagged); (6) Investopedia article reviewed and dismissed (no value above existing architecture); (7) Layer 1 (signals/bbwp.py) confirmed COMPLETE. Session also noted a context compaction violation — triggered without warning causing wasteful token-burning search outside vault.

### Decisions recorded
- Ollama integrated in simulator: Yes (Layer 6, post-computation reasoning)
- Models assigned: qwen3:8b (fast), qwen2.5-coder:32b (code review), qwen3-coder:30b (deep)
- Monte Carlo: Yes (Layer 4b, 1000 sims, 95% CI)
- Total pipeline runtime: ~35 min for 399 coins
- Investopedia article: No value — already exceeded by existing architecture
- Layer 1 status: COMPLETE

### State changes
- BBW-UML-DIAGRAMS.md rewritten with 6 diagrams + legends
- BBW-STATISTICS-RESEARCH.md updated (Monte Carlo section + build sequence)
- BBW-SIMULATOR-ARCHITECTURE.md created (new, full 6-layer + Ollama)
- CLAUDE-CODE-PROMPT-LAYER1.md created (new, Claude Code build prompt)
- signals/bbwp.py confirmed built and tested

### Open items recorded
1. New chat needed — write CLAUDE-CODE-PROMPT-LAYER2.md for bbw_sequence.py
2. Layer 2 through Layer 6b not yet built (all NOT STARTED)
3. Context compaction rule violation — needs rule reinforcement

### Notes
- First log to confirm Layer 1 (signals/bbwp.py) as COMPLETE with 61/61 tests PASS
- VERIFICATION: signals/bbwp.py confirmed present on disk

---

## 2026-02-14-bbw-layer1-build.md
**Date:** 2026-02-14 (post-build timestamp 11:16 UTC)
**Type:** Build session

### What happened
Build log for Layer 1 of the BBW simulator: Python port of bbwp_v2.pine (264-line Pine v6 script) to signals/bbwp.py. Pre-build section documents scope (3 files to create), Pine Script references, and 7 known tricky parts (MA cross persistence stateful, percentrank manual implementation, operator precision differences, spectrum vs state boundaries, cross event vs persisted state, state string format, NaN handling). Post-build: 4 files created (tests/__init__.py, tests/test_bbwp.py with 11 tests, signals/bbwp.py, scripts/sanity_check_bbwp.py). 61/61 tests PASS. 2 bugs found and fixed: (1) _percentrank_pine() included current bar in window — corrected to use only previous length values; (2) Test thresholds too tight for NORMAL state distribution. Sanity check on RIVERUSDT 5m (32,762 bars): BBWP mean=48.8 (correct for uniform percentile), performance 101K bars/sec. Pine Script fidelity checklist fully verified.

### Decisions recorded
- percentrank: manual implementation matching Pine's "previous length values strictly less" semantics (not scipy)
- State strings: uppercase with underscores (BLUE_DOUBLE, MA_CROSS_UP)
- Spectrum strings: lowercase (blue, green, yellow, orange, red)
- 10 output columns with bbwp_ prefix

### State changes
- Created: tests/__init__.py (empty)
- Created: tests/test_bbwp.py (11 tests, ~300 lines)
- Created: signals/bbwp.py (~210 lines) — Layer 1 COMPLETE
- Created: scripts/sanity_check_bbwp.py

### Open items recorded
- Layer 2 (signals/bbw_sequence.py) — next build

### Notes
- Layer 1 state distribution on RIVERUSDT: NORMAL=17.9%, BLUE_DOUBLE=14.5%, MA_CROSS_UP=14.3%, BLUE=14.0%, MA_CROSS_DOWN=13.8%, RED_DOUBLE=13.2%, RED=12.4%
- VERIFICATION: signals/bbwp.py confirmed present on disk

---

## 2026-02-14-bbw-layer2-build.md
**Date:** 2026-02-14 (start 13:16 UTC, tests pass 13:22 UTC)
**Type:** Build session

### What happened
Build log for Layer 2 of the BBW simulator: signals/bbw_sequence.py (sequence tracker, 9 output columns). 4 files created in 6 minutes. One hotfix applied during build: SyntaxError in 3 generated files caused by Windows \Users path in docstrings triggering unicode escape error — fixed by replacing full Windows paths with relative paths in docstrings. Test results: 68/68 PASS. Debug validator: 148/148 PASS. Layer 2 speed: 961K bars/sec vs Layer 1's 97K bars/sec (sequence computation is vectorized). Color transitions on RIVERUSDT: 19.3% of bars. Skip detection: 0.9% (mostly blue<->yellow). Top pattern: YGB (17.1%) — contracting from yellow through green to blue. Blue runs longest (mean 8.9 bars), green shortest (mean 3.5).

### Decisions recorded
- None stated (implementation followed spec)

### State changes
- Created: signals/bbw_sequence.py (9 output columns)
- Created: tests/test_bbw_sequence.py (10 tests, 68 assertions)
- Created: scripts/sanity_check_bbw_sequence.py
- Created: scripts/debug_bbw_sequence.py (7 sections, 148 checks)

### Open items recorded
- Layer 3 (research/bbw_forward_returns.py) — next build (prompt needs 3 audit passes)

### Notes
- Hotfix documented: Windows paths in docstrings cause unicode escape SyntaxError in generated files — use relative paths only
- VERIFICATION: signals/bbw_sequence.py confirmed present on disk

---

## 2026-02-14-bbw-layer3-audit-pass3.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Third audit pass on BUILDS\PROMPT-LAYER3-BUILD.md before executing in Claude Code. Previous sessions ran pass 1 (7 bugs) and pass 2 (3 bugs). This pass found 6 additional issues: (1) HIGH — Test 9 proper_move used flat data (ATR=0, test meaningless) — changed to alternating volatile bars; (2) HIGH — Debug Section 2 bar 16 was in NaN zone for window=4 — fixed with explicit second call using windows=[3]; (3) MEDIUM — bar 16 expected values not pre-computed — fully pre-computed all 10 values; (4) LOW — missing explicit research/ directory creation — added pathlib mkdir; (5) INFO — columns dropped (intentional, documented); (6) INFO — NaN tolerance strict (intentional, documented). All HIGH/CRITICAL bugs fixed. Cumulative 16 bugs across 3 passes: 4 CRITICAL, 4 HIGH, 4 MEDIUM, 2 LOW, 2 INFO. Math for bar 15 (window=4) and bar 16 (window=3) fully hand-verified. Prompt declared ready for Claude Code.

### Decisions recorded
- Layer 3 NaN tolerance: strict (100% valid bars required) — intentional, relaxable later
- Columns fwd_N_valid_bars, fwd_N_bbw_valid: deferred to pipeline orchestrator (not in Layer 3)
- research/ directory: must be explicitly created before research/__init__.py write

### State changes
- BUILDS\PROMPT-LAYER3-BUILD.md: 4 edits (Test 9, Debug bar 16, mkdir step, design decisions section)
- No Layer 3 code built yet

### Open items recorded
- Execute Layer 3 build in Claude Code using the audited prompt

### Notes
- Cumulative audit count across 3 passes: 16 total issues for Layer 3 prompt
- Math verification for bar 16 (window=3): ATR=5.0, max_range_atr=2.8, proper_move=False confirmed

---

## 2026-02-14-bbw-layer3-journal.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
Session journal for the same Layer 3 audit pass 3 session documented in bbw-layer3-audit-pass3.md. Contains the same content but organized as a journal with context loading section. Confirms: research/ directory does NOT exist yet before the build, Layer 1 (61/61 PASS) and Layer 2 (68/68 PASS, 148/148 debug PASS). Provides copy-paste ready Claude Code instruction to read 4 files in order and build Layer 3. Next steps: paste instruction into VS Code, Claude Code builds all Layer 3 files, all tests must pass before proceeding to Layer 4, resume instructions if max token hit.

### Decisions recorded
- Same decisions as bbw-layer3-audit-pass3.md

### State changes
- Same as bbw-layer3-audit-pass3.md (companion file, same session)

### Open items recorded
- Same as bbw-layer3-audit-pass3.md

### Notes
- Duplicate/companion file to bbw-layer3-audit-pass3.md — both created in same session. Content largely identical with different organizational structure.

---

## 2026-02-14-bbw-layer3-results.md
**Date:** 2026-02-14 (14:33 UTC)
**Type:** Build session

### What happened
Test results log for Layer 3 build (research/bbw_forward_returns.py). 12 tests, 102/102 PASS. 6 debug sections, 72/72 PASS. Sanity check on RIVERUSDT 5m: 0.02s runtime (2.15M bars/sec), ATR mean=0.2623 (1.58% of close). Cross-validation of L1+L2+L3 real data shows RED_DOUBLE state has highest range_atr (3.795) and highest proper_move rate (60.0%), while BLUE_DOUBLE has lowest range_atr (3.342) — noted as hypothesis not confirmed (BD range <= NORMAL range). NaN zones confirmed correct: last N bars per window contain NaN (10 NaN for window=10, 20 NaN for window=20). All pre-computed bar 15 and bar 16 values from audit passes verified with PASS.

### Decisions recorded
- None new (implementation followed audited prompt)

### State changes
- research/bbw_forward_returns.py confirmed built and passing
- Layer 3: COMPLETE (102/102 tests, 72/72 debug)

### Open items recorded
- Layer 4 (research/bbw_simulator.py) — next build (prompt needs audit)

### Notes
- Key finding from real data: RED_DOUBLE proper_move=60%, all others 45-51%. Hypothesis that BLUE_DOUBLE has lower range than NORMAL not confirmed (3.342 vs 3.377).
- VERIFICATION: research/bbw_forward_returns.py confirmed present on disk

---

## 2026-02-14-bbw-layer4-audit-and-sync.md
**Date:** 2026-02-14
**Type:** Audit / Planning

### What happened
Combined Layer 4 audit summary and project sync document. Confirms full project status: Layer 1-3 complete, Layer 4 build prompt audited and ready (22 bugs found/fixed in 2 rounds), Layer 4b/5/6 not yet built. Full layer output column reference documented (Layer 1: 10 cols, Layer 2: 9 cols, Layer 3: 17 cols, Layer 4: SimulatorResult dataclass with group_stats/lsg_results/lsg_top/scaling_results/summary). 10 Layer 4 design decisions locked (TP/SL ambiguity resolved to close_pct, no per-bar PnL storage, no transaction costs yet, states from L1 only, etc.). Layer 5 scope defined (bbw_report.py, 11 CSV output files in reports/bbw/ directory tree). Build order documented. Key fixes in audit: PnL formula with per-bar ATR/close enforcement, valid_mask made dynamic across all windows, scaling circular dependency resolved, architecture doc corrected (L3 input is OHLCV only, spectrum is 4 colors not 5).

### Decisions recorded
- PnL formula: close_pct based (not TP/SL ATR targets) for conservative approach
- No per-bar PnL storage (inline cumsum for drawdown only)
- No transaction costs in Layer 4 (raw edge first, config.fee_pct later)
- States from Layer 1 only (7 bbwp_state values)
- Bins start at -1 (defensive for bars_in_state)
- Group G uses pandas mask (not np.char.add) to avoid None->'None'
- profit_factor: NaN if both sum(wins) and sum(losses) are 0
- edge_pct guard: NaN if abs(mean_base_pnl) < 1e-10
- Layer 5 depends on BOTH Layer 4 AND Layer 4b (Monte Carlo must be built first)

### State changes
- BUILDS\PROMPT-LAYER4-BUILD.md: all 22 bugs fixed
- BBW-SIMULATOR-ARCHITECTURE.md: corrected (L3 input, spectrum 4 colors)
- Layer 4 build prompt: AUDITED, ready for Claude Code

### Open items recorded
- Layer 4: execute BUILDS\PROMPT-LAYER4-BUILD.md in Claude Code
- Layer 4b (Monte Carlo): needs build prompt
- Layer 5: needs build prompt
- Layer 6: needs build prompt
- PRE-STEP (coin_classifier.py): not built, blocks full Layer 5 output

### Notes
- Documents existing test/script files as of this point (7 test/script files confirmed)
- Architecture doc L3 input corrected: L3 only needs OHLCV (not OHLCV + BBWP + Sequence)

---

## 2026-02-14-bbw-layer4-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Detailed bug audit report for BUILDS\PROMPT-LAYER4-BUILD.md. Round 1: 14 bugs found and fixed (4 CRITICAL: PnL formula ATR source, ambiguous PnL undefined, valid_mask only checked fwd_10, expectancy_per_bar meaningless; 5 MODERATE: _lsg_grid_search signature mismatch, scaling circular dependency, bins edge at 0, Group G np.char.add None issue, calmar_approx needs max_drawdown; 5 MINOR: directional_bias string mapping, sanity combo math, L3 pre-check missing, _add_derived_columns not defined, _extract_top_combos closure). Round 2: 8 new issues (3 MODERATE: architecture doc L3 input, architecture doc 5 vs 4 spectrum colors, max_drawdown 2D vectorization; 5 MINOR: close_pct scoping, directional_bias excludes flat, profit_factor 0/0 edge, test dimension label, edge_pct divide by zero). Verdict: No critical bugs remain.

### Decisions recorded
- max_drawdown: added with inline cumsum pattern (np.maximum.accumulate on 2D)
- Architecture doc: L3 input corrected to OHLCV only, spectrum corrected to 4 colors

### State changes
- BUILDS\PROMPT-LAYER4-BUILD.md: all bugs fixed
- BBW-SIMULATOR-ARCHITECTURE.md: N1 (L3 input) and N2 (4 colors) corrected

### Open items recorded
- Build Layer 3 to completion first, then execute Layer 4 prompt

### Notes
- 22 total bugs across 2 rounds for Layer 4 prompt, all resolved before Claude Code execution
- Companion document to bbw-layer4-audit-and-sync.md (same audit, different format)

---

## 2026-02-14-bbw-layer4-results.md
**Date:** 2026-02-14 (16:24 UTC)
**Type:** Build session

### What happened
Test results log for Layer 4 build (research/bbw_simulator.py). 15 tests, 55/55 PASS. 7 debug sections, 44/44 PASS. Sanity check on RIVERUSDT 5m: L4 runs in 2.06s, total pipeline (L1+L2+L3+L4) in 2.47s. 7 states present, 112 LSG combos, 6 scaling scenarios. Group stats best categories: A_state=RED_DOUBLE (edge=0.070), B_spectrum=green (edge=0.062), C_direction=expanding (edge=0.051), D_pattern=GRB (edge=3.255), E_skip=True (edge=0.099), F_duration=21-50 bars (edge=0.388), G_ma_spectrum=cross_down_green (edge=0.142). Top LSG combo: RED_DOUBLE lev=20 tgt=4 sl=1.5 exp=$18.90 wr=44.4% pf=1.29. Scaling results: 5 of 6 scenarios verdict=USE. Results CSV saved.

### Decisions recorded
- None new (implementation followed audited prompt)

### State changes
- research/bbw_simulator.py confirmed built and passing
- Layer 4: COMPLETE (55/55 tests, 44/44 debug)
- results/bbw_simulator_sanity.csv saved to disk

### Open items recorded
- Layer 4b (Monte Carlo) — next build
- Layer 5 (bbw_report.py) — blocked by Layer 4b

### Notes
- Key finding: RED_DOUBLE state has best edge at $18.90 expectancy (vs $1.77-$4.27 for other states)
- Most states show RED at only $-0.21 — only state with negative gross expectancy
- VERIFICATION: research/bbw_simulator.py confirmed present on disk

---

## 2026-02-14-bbw-layer5-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Bug audit of BUILDS\PROMPT-LAYER5-BUILD.md (Layer 5 report generator). 15 issues found: 3 HIGH (H1: architecture diagram function signatures missing config parameter — 8 functions affected; H2: _summarize_group crashes on all-NaN expectancy_usd via idxmax(); H3: mock n_triggered can exceed n_entry_bars — independent random calls); 7 MEDIUM (M1: dead variable mc_status; M2: report manifest doesn't list itself; M3: manifest subdir detection fragile with prefix-matching; M4: groupby.apply() FutureWarning in pandas >= 2.1; M5: ReportConfig.top_n_per_state unused; M6: test count mismatch in header says 12 but has 20; M7: _validate_sim_result doesn't check summary is dict); 5 LOW (L1: bool→string conversion in mock; L2: no __all__; L3: asymmetric exception handling not documented; L4: ascending list construction brittle; L5: missing bbwp_ma from validation list — intentional). Cross-reference validation against Layer 4 output columns: all checks PASSED.

### Decisions recorded
- H1 fix: update architecture diagram to match all function signatures
- H2 fix: add isna().all() guard before idxmax()
- H3 fix: n_entry must be single random draw, n_triggered derived from it
- M2: manifest cannot list itself — document this limitation for Layer 6

### State changes
- BUILDS\PROMPT-LAYER5-BUILD.md: fixes documented (actual edits not confirmed in this log)

### Open items recorded
- Apply all 15 fixes to PROMPT-LAYER5-BUILD.md before Claude Code execution

### Notes
- Cross-reference between L4 and L5 column names: all 7 group keys, all DataFrame attributes, scaling columns — all matched

---

## 2026-02-14-bbw-layer5-v2-build-session.md
**Date:** 2026-02-14
**Type:** Build session

### What happened
Build session for Layer 5 V2: research/bbw_report_v2.py (VINCE feature generator, NOT the CSV report writer). Built as continuation of V2 pipeline work where Layers 1-4b V2 were already complete. Files created: bbw_report_v2.py, tests/test_bbw_report_v2.py (48 tests, NOT yet run), scripts/debug_bbw_integration.py, scripts/test_bbw_integration_random.py. Files modified: bbw_monte_carlo_v2.py, test_bbw_monte_carlo_v2.py, 2 debug scripts. 7 bugs found and fixed: (1) CRITICAL — bbw_state_at_entry → bbw_state column name mismatch across Layer 4b and debug scripts; (2) HIGH — 3 of 5 Layer 5 functions used 'state' instead of 'bbw_state'; (3) REAL BUG — state_encoding had 3 phantom states (GREEN_DOUBLE, YELLOW_DOUBLE, GRAY) and missed NORMAL/MA_CROSS_UP/MA_CROSS_DOWN; (4) BUG — import reference used non-existent function name; (5) BUG — integration test used wrong outcome values WIN/LOSS instead of TP/SL/TIMEOUT; (6) ARCHITECTURE — LSG should be fixed for entire run not random per-trade; (7) DATA — n_trades too low for group filter. Architecture note: two parallel Layer 5 implementations exist (bbw_report_v2.py for VINCE features, planned bbw_report.py for CSV reports).

### Decisions recorded
- LSG architecture: fixed for entire backtester run (not random per-trade)
- Two Layer 5 files: bbw_report_v2.py (VINCE ML features) and bbw_report.py (CSV reports, not yet built)
- state_encoding: must use all 9 Layer 4 valid states (not phantom states)

### State changes
- research/bbw_report_v2.py: CREATED (logic complete, tests built not run)
- tests/test_bbw_report_v2.py: CREATED (48 tests, not run)
- debug_bbw_integration.py, test_bbw_integration_random.py: CREATED
- bbw_monte_carlo_v2.py and related: MODIFIED (column rename fix)

### Open items recorded
1. Run scripts/debug_bbw_integration.py — confirm end-to-end pass
2. Run scripts/test_bbw_integration_random.py — confirm 10/10 pass
3. Run tests/test_bbw_report_v2.py — confirm 48/48 pass
4. Run tests/test_bbw_monte_carlo_v2.py — confirm Layer 4b still passes
5. Build research/bbw_report.py (full pipeline CSV writer, 11 files — separate from V2)

### Notes
- Layer 5 tests NOT run at session end — completeness status shows "BUILT, NOT RUN"
- VERIFICATION: research/bbw_report_v2.py confirmed present on disk

---

## 2026-02-14-bbw-layer6-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Bug audit of BUILDS\PROMPT-LAYER6-BUILD.md (Ollama review layer). 8 issues found: 1 HIGH (H1: architecture diagram function signatures all mismatched — 5 functions affected, same pattern as Layer 5 H1); 4 MEDIUM (M1: _discover_reports constructs wrong path for files with subdir='root' → base/'root'/filename doesn't exist; M2: _validate_ollama_connection fallback assigns non-existent model; M3: test count mismatch says 15 but has 20; M4: _ollama_call catches ValueError but doesn't retry on empty response); 3 LOW (L1: _analyze_features reads CSV as DataFrame — slight design break but documented; L2: max_csv_chars used for spec truncation — naming inconsistency; L3: no __all__ in test spec). Cross-reference validation of L5 → L6 file paths and column names: all checks PASSED with M1 fix.

### Decisions recorded
- H1 fix: update architecture diagram to match actual function signatures
- M1 fix: handle subdir == 'root' case explicitly (base/filename not base/root/filename)
- M4: either add ValueError to retry exceptions OR document as intentional

### State changes
- BUILDS\PROMPT-LAYER6-BUILD.md: fixes documented (actual edits not confirmed in this log)

### Open items recorded
- Apply all 8 fixes before Claude Code execution of Layer 6

### Notes
- Cross-reference between L5 output and L6 input: all filenames matched, directory structure matched (with M1 fix)

---

## 2026-02-14-bbw-uml-research.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
Combined log of 2 sessions covering BBW simulator architecture and UML work. Session 1 (morning): Reviewed existing vault files (bbwp_v2.pine, BBWP-v2-BUILD-SPEC.md, bbwp_caretaker_v6.pine). Core concept established: BBW does NOT limit trades — BBW TUNES the LSG parameters. Full architecture document produced (5-layer pipeline). BBWP percentile rank implementation options researched (Option A: pd.Series.rolling(100).rank(pct=True) recommended for production). Key design decisions locked: SL test values (1, 1.5, 2, 3 ATR), forward windows (10+20 bars on 5m), proper move threshold (3 ATR), coin grouping (KMeans clustering). Session 2 (afternoon): Ripster/AVWAP scope question answered — NO (rabbitholing), belongs at VINCE not BBW layer. 17 BBW features for VINCE identified. 6 UML diagrams produced in Mermaid format. Build sequence defined (10 steps, ~5 hours Claude Code). Ollama Layer 6 added to architecture post-revision.

### Decisions recorded
- BBW purpose: TUNES LSG (Leverage, Size, Grid/Target), does NOT limit trades
- Ripster/AVWAP: out of scope for BBW, belongs at VINCE (ML layer)
- SL values: 1, 1.5, 2, 3 ATR
- Forward windows: 10 bars + 20 bars on 5m
- Proper move threshold: 3 ATR
- Coin grouping: data-driven KMeans clustering
- TDI: out of scope
- Ollama: NOT needed for BBW math, relevant for VINCE NL reasoning

### State changes
- BBW-UML-DIAGRAMS.md: created (6 Mermaid diagrams with legends)
- BBW-STATISTICS-RESEARCH.md: created (scope, features, Monte Carlo, build sequence)
- BBW-SIMULATOR-ARCHITECTURE.md: created (full architecture + Ollama Layer 6)

### Open items recorded
- Review all 4 docs in Obsidian (diagrams render natively)
- Approve architecture → start build in Claude Code
- Build sequence: Layer 1 first

### Notes
- This is the original architecture session log that preceded all the layer build logs
- Notes contradiction with 2026-02-16-bbw-v2-fundamental-corrections.md: The original architecture treated Ollama reasoning as Layer 6 of BBW pipeline. The Feb 16 corrections document removes Layer 6 entirely and clarifies VINCE is separate.

---

## 2026-02-14-dashboard-v31-build.md
**Date:** 2026-02-14 (15:06 UTC)
**Type:** Build session

### What happened
Dashboard v3.1 build session. 15 surgical patches applied to scripts/dashboard.py (1520 → 1893 lines) via scripts/build_dashboard_v31.py (626 lines). Pre-work: 7 critical logic fixes applied first (C-1 through C-7 from operational logic audit). 3 new features added: (1) Date Range Filter — sidebar widget with All/7d/30d/90d/1y/Custom modes, integrated into params_hash; (2) Stress Test — expander showing worst 1-5 non-overlapping drawdown windows, re-backtests on each; (3) Portfolio Mode — new sidebar mode, coin selection (Top N/Lowest N/Random N/Custom), runs per-coin, aligned equity curves, portfolio summary metrics, correlation matrix. Test results: 21/21 PASS (test_dashboard_v31.py). Build script: 15/15 anchors found, 0 missing, APPLIED, py_compile PASS. 6 bugs found and fixed during audit: P10b (date filter position), test assertion fixes, escaped quotes in f-strings (10 instances refactored to temp variables), missing py_compile, missing docstrings.

### Decisions recorded
- Date range filter integrated into params_hash so different date ranges get different sweep progress
- Portfolio mode: per-coin equity curves aligned using union DatetimeIndex + forward-fill
- f-string escaped quotes: refactored to temp variables (aligns with MEMORY hard rule)

### State changes
- scripts/dashboard.py: edited (1520 → 1893 lines)
- scripts/build_dashboard_v31.py: created (626 lines)
- scripts/test_dashboard_v31.py: created (~430 lines)

### Open items recorded
- None stated

### Notes
- Dashboard v3.1 is a build on top of dashboard.py (pre-existing file). The 7 operational fixes (C-1 through C-7) from the audit were applied before the v3.1 features.
- Run command: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard.py"`

---

## 2026-02-14-operational-logic-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Full operational logic audit of Four Pillars backtester covering 9 engine files, 4 data pipeline files, and 6 ML pipeline files. Focus was trading logic correctness, look-ahead bias, commission math, data integrity (NOT bugs, style, or refactoring). 7 CRITICAL findings: (C-1) Equity curve ignores unrealized P&L — max DD understated; (C-2) Scale-out entry commission not prorated — SCALE_1 artificially profitable; (C-3) CommissionModel cost_per_side backdoor — future landmine; (C-4) duration_bars is look-ahead feature in ML training — inflates model accuracy; (C-5) daily_turnover uses intraday future volume (shift(1) needed); (C-6) Meta-labeler trains and evaluates on SAME data — purged CV exists but never wired; (C-7) Triple barrier labels ignore commission — TP hit but net negative. 15 WARNING findings covering backtester engine (W-1 through W-8), data pipeline (W-9 through W-15), ML pipeline (W-16 through W-20). 17 OK findings confirming correct implementation of commission math, entry timing, SL/TP priority, signal grading, ATR, etc.

### Decisions recorded
- Fix priority order: C-6 (purged CV) → C-4 (duration_bars) → C-1 (unrealized P&L) → C-7 (label_trades_by_pnl) → C-2 (scale-out commission) → C-5 (daily_sum.shift) → C-3 (remove cost_per_side)

### State changes
- Audit document created (findings only, no code changed in this session)
- C-1 through C-7 fixes applied separately in dashboard-v31-build.md session (same day)

### Open items recorded
- All 7 CRITICAL fixes (C-1 through C-7) — in priority order
- All 15 WARNING findings (lower priority)

### Notes
- This audit preceded and motivated the 7 pre-work fixes in the dashboard v3.1 build session
- C-6 (purged CV not wired) identified as highest priority fix — ML accuracy results are all in-sample and meaningless for live trading

---

## 2026-02-14-project-flow-update.md
**Date:** 2026-02-14
**Type:** Planning

### What happened
Two-chat session log covering project flow updates and Core Build 2 prompt. Key correction: data download status was wrong in the review doc (claimed 14% and 1%) — actual status is 100% complete for both periods. 2023-2024: 166 completed + 43 no_data = 209/209 eligible. 2024-2025: 257 completed + 19 no_data = 276/276 eligible. Explanation: CoinGecko listing date filter excluded coins that didn't exist in those periods (reducing eligible count). 399 coins total, 6.2 GB cache. Claude Code build_all_specs.py: ALL 9 FILES EXIST on disk. Core Build 2 defined with 7 steps (run test_v385.py, test_dashboard_v3.py, test_vince_ml.py, fix failures, smoke test dashboard, single coin parquet export, period_loader test). Key insight documented: role-prompting adds nothing — concrete specs + explicit pass/fail criteria do the heavy lifting. PROJECT-FLOW-CHRONOLOGICAL.md fully rewritten with accurate statuses.

### Decisions recorded
- BBWP Python port deferred to afternoon
- CoinGecko features join deferred until after Core Build 2
- Core Build 2 constraints: minimal patches, no rewrites

### State changes
- PROJECT-FLOW-CHRONOLOGICAL.md: full rewrite with accurate statuses + Core Build 2 phase

### Open items recorded
- Core Build 2: 7-step sequential test-and-fix workflow (Claude Code running)
- BBWP Python port: deferred to afternoon session

### Notes
- Data download percentage discrepancy explained: CoinGecko listing date filter caused discrepancy, not actual incompleteness
- Critical path updated: Data COMPLETE → Core Build 2 (active) → Sweep → Trade Parquet → ML Phase 1 → Live

---

## 2026-02-14-vault-sweep-review.md
**Date:** 2026-02-14
**Type:** Other (automated code review output)

### What happened
Automated Ollama code review of 62 vault Python files using qwen2.5-coder:14b model. Runtime: 4,259 seconds (71 minutes). 42 issues flagged across 62 files. Review format per file: Critical Issues, Security, Error Handling, Logic, Improvements (with code snippets). Files reviewed span the entire vault codebase including localllm/, data/ (fetcher.py, normalizer.py), scripts/ (dashboard.py, dashboard_v2.py, dashboard_v3.py, download scripts), engine/, signals/, ml/, and root-level utility scripts (vault_sweep.py, vault_sweep_3.py, vault_sweep_4.py). Large files (>50,000 chars) skipped with note — this affected dashboard.py and dashboard_v2.py. Common issues flagged: broad exception handling, infinite loop risks, missing retry mechanisms, off-by-one errors in stage lookback (state_machine_v382.py), missing try/except for file operations. File is ~4,200 lines (largest in the batch at ~86KB).

### Decisions recorded
- None (review output only, no decisions made)

### State changes
- No code changed in this session (read-only review output)

### Open items recorded
- 42 issues identified across codebase — no action plan stated in this file

### Notes
- This file documents an automated batch review, not a human decision session. Many suggestions are generic (add retries, use specific exceptions) that may not apply to the codebase's actual requirements.
- dashboard.py and dashboard_v2.py were SKIPPED (too large at >50K chars) — no review output for these files.

---

## 2026-02-16-bbw-layer4b-plan.md
**Date:** 2026-02-16
**Type:** Planning / Build session

### What happened
Combined Layer 4b build plan AND results (same file, results appended during session). Pre-build: 4 spec bugs fixed (CRITICAL: shuffle is order-invariant for PnL — must use bootstrap not permutation for PnL/Sharpe; CRITICAL: DD sign convention → store as positive absolute values; MEDIUM: MCL missing from MC loop; LOW: Layer 4 doesn't expose per-trade PnL — reconstruct via _vectorized_pnl). Dual-method approach designed: Bootstrap (WITH replacement) for PnL/Sharpe/profit_factor CIs; Permutation (WITHOUT replacement) for max_dd/max_consecutive_loss. 6 verdicts defined: ROBUST, MARGINAL, FRAGILE, COMMISSION_KILL, INSUFFICIENT_DATA, THIN_EDGE. Build manifest: 5 files (~350-400 lines each). Architecture evaluation: all L1-L4 complete. Layer 4b results: py_compile 5/5 PASS, unit tests 45/45 PASS (2 fixes applied), debug 57/57 (1 known FAIL — Section 6.2 DD=1900 not 2000, documented as correct). RIVERUSDT sanity: 6/7 states COMMISSION_KILL (gross $1.77-$4.27 killed by $8.00 RT), 1/7 FRAGILE (RED_DOUBLE gross=$18.90, net=$10.90). Layer 5 (bbw_report.py) also built in same session: 58/58 tests PASS, 11/11 CSVs written. GitHub push to branch bbw-layers-1-5-complete: 64 files, 19,108 insertions, push successful.

### Decisions recorded
- Bootstrap for PnL/Sharpe CI (order-invariant metrics need bootstrap, not permutation)
- Permutation for DD/MCL (path-dependent metrics)
- Commission: 0.0008 RT deducted from all PnL calculations
- Store percentile bands only (5 floats per state), discard raw 1000-sim matrices (400 GB vs 2 GB)
- Coin classifier gap: Layer 4b coin-agnostic, classifier deferred to Layer 5
- Layer 4b → Layer 5 output contract: 4 DataFrames (state_verdicts, confidence_intervals, equity_bands, overfit_flags)
- numpy.random.Generator (not legacy numpy.random.seed) for thread safety
- Min net expectancy threshold: $1.00
- Max MCL practical threshold: 15

### State changes
- research/bbw_monte_carlo.py: CREATED (5/5 py_compile, 45/45 tests)
- research/bbw_report.py: CREATED (58/58 tests, 11/11 CSVs written)
- GitHub branch bbw-layers-1-5-complete pushed (64 files changed)
- results/bbw_monte_carlo_sanity_verdicts.csv and flags.csv saved

### Open items recorded
- Layer 6: Ollama review (now unblocked)
- Fill remaining coin gaps (P0.2)
- Coin classifier (P1.1)
- Deploy staging files (P1.5)

### Notes
- KEY FINDING: BBW-only edges are too weak ($5.22 avg gross vs $8.00 RT commission). Validates that stochastics/grading do the heavy lifting in Four Pillars strategy.
- Multi-coin validation (RIVER/AXS/KITE): 21/21 states COMMISSION_KILL
- Debug section 6.2 intentional FAIL documented: DD for [-100]*20 starting at -100 is 1900 not 2000 (cumsum starts at first value, not 0)
- VERIFICATION: research/bbw_monte_carlo.py and research/bbw_report.py confirmed present on disk

---

## 2026-02-16-bbw-layer4b-results.md
**Date:** 2026-02-16 (07:59:51 UTC)
**Type:** Build session

### What happened
Detailed test results log for Layer 4b (bbw_monte_carlo.py). py_compile: 5/5 PASS. Unit tests: 45/45 PASS. Debug checks: 56/57 PASS (1 known FAIL in Section 6.2 — DD=1900 expected 2000; documented as correct behavior: cumsum starts at -100 not 0 for first-loss sequence). Sanity check: COMPLETE, 7 states processed. RIVERUSDT results: 6/7 COMMISSION_KILL, 1/7 FRAGILE (RED_DOUBLE). Avg commission drag: $7.14/trade. RED state used lev=10 sz=0.5 (RT=$2.00) but still killed by negative gross. Confidence interval samples provided for first 3 states showing negative total_pnl, negative sharpe/sortino, profit_factor 0.88-0.93. Max consecutive loss very high (real=38 for BLUE, p95=18 — real exceeds p95, DD_FRAGILE flag). Results CSVs saved to results/ directory.

### Decisions recorded
- None new (results log only)

### State changes
- research/bbw_monte_carlo.py: confirmed passing
- results/bbw_monte_carlo_sanity_verdicts.csv: saved
- results/bbw_monte_carlo_sanity_flags.csv: saved

### Open items recorded
- None stated (results log)

### Notes
- Companion results file to bbw-layer4b-plan.md — plan file also contains the results summary
- Section 6.2 FAIL is documented as expected (mathematical correctness): cumsum([−100]×20) starts at -100, peak=-100, trough=-2000, max DD = 2000-100 = 1900

---

## 2026-02-16-bbw-v2-fundamental-corrections.md
**Date:** 2026-02-16
**Type:** Planning / Architecture

### What happened
Major architecture correction session for BBW V2 design. Three fundamental misunderstandings corrected: (1) Direction source: BBW does NOT test both directions arbitrarily — direction comes from complete Four Pillars strategy (Stochastics + Ripster + AVWAP combined). User example: "Stochastics: Overbought → SHORT, Ripster: Trending down → SHORT, AVWAP: Price above → LONG bias (conflict) → Strategy Decision: SHORT (2 vs 1)". BBW's job is: given SHORT in BLUE state, what LSG works best? (2) Layer 6 does not exist: VINCE is a separate ML component, NOT part of BBW pipeline. BBW outputs data (one of four pillar inputs to VINCE). (3) Trade source: BBW analyzes REAL backtester results (400+ coins, year of data, 93% success rate from dashboard sweep) — NOT synthetic simulated trades. User quote: "There is a set ran on the dashboard, and we swept through a whole year with 93% with 80+% LSG...". BBW V2 purpose clarified: pure data generator for VINCE training — group by (state, direction, LSG), calculate BE+fees rates, output results. V2 uses BE+fees metric instead of win rate. 4 documents updated.

### Decisions recorded
- BBW V2 is a data generator only — no directional decision-making
- Direction always comes from Four Pillars strategy (Stochastics + Ripster + AVWAP)
- Layer 6 removed from BBW architecture
- VINCE is separate ML component
- Trade source: real backtester_v385 results (not synthetic)
- V2 metric: BE+fees success rate (not win rate)
- BBW V2 architecture: Layers 1-2-3-4-4b-5 (no Layer 6)

### State changes
- BBW-V2-ARCHITECTURE.md: updated to v2.0 (removed Layer 6, fixed trade source, clarified direction)
- BBW-V2-UML.mmd: updated (Layer 6 removed, backtester nodes added, VINCE shown as separate)
- BBW-V2-LAYER4-SPEC.md: complete rewrite (from simulation to analysis of real backtester results)
- BBW-V2-LAYER5-SPEC.md: new document created (feature engineering, 5 CSV outputs, 30+ tests)

### Open items recorded
1. Build Layer 4: bbw_analyzer_v2.py (7-8 hours)
2. Build Layer 4b: bbw_monte_carlo_v2.py (depends on Layer 4)
3. Build Layer 5: bbw_report_v2.py (depends on Layer 4b)

### Notes
- IMPORTANT CONTRADICTION with earlier logs: The original BBW architecture (bbw-uml-research.md, bbw-full-session.md) included Ollama as Layer 6 of the BBW pipeline. The Feb 16 corrections document removes Layer 6 entirely, clarifying VINCE (which includes Ollama reasoning) is a separate component.
- The V1 pipeline (L1-L5 including bbw_simulator.py) was built using the OLD architecture (synthetic trades, both directions tested). The V2 rebuild uses REAL backtester results.
- User expressed frustration at being asked directional questions when the dashboard already showed 93% success with real data.
- VERIFICATION: research/bbw_analyzer_v2.py and research/bbw_report_v2.py confirmed present on disk (V2 files built)


# Batch 06 Research Findings
**Files:** 20 logs from 2026-02-16 and 2026-02-17
**Processed:** 2026-03-05

---

## 2026-02-16-bbw-v2-layer4-5-prebuild-analysis.md
**Date:** 2026-02-16
**Type:** Planning / Architecture spec

### What happened
Pre-build architecture review and analysis for BBW V2 Layers 4, 4b, and 5. Documented the corrected architecture after identifying that BBW V1 was fundamentally flawed (simulated trades instead of analyzing backtester results). Established data flow: Backtester v385 results → Layer 4 (BBW Analyzer V2) → Layer 4b (Monte Carlo V2) → Layer 5 (Report V2) → VINCE ML (separate component).

Defined the primary metric as BE+fees rate (% trades with pnl_net >= 0), contrasting with win rate (gross PnL > 0). Documented five math validations, syntax error prevention rules (Windows path safety, DataFrame merge alignment, groupby index handling, column name consistency), and a test strategy of 40+ unit tests per layer. Specified 5 CSV output files from Layer 5 and detailed input/output contracts for all three layers.

### Decisions recorded
- BBW V1 was wrong: it simulated trades; V2 analyzes real backtester results
- Direction source is Four Pillars strategy, NOT BBW testing
- VINCE is a separate ML component, NOT Layer 6
- BBW purpose is data generator for VINCE training
- BE+fees rate is the primary metric (pnl_net >= 0, not pnl_gross > 0)
- Bias threshold: 5% difference between LONG and SHORT rates
- min_trades_per_group default: 100

### State changes
- Document created as pre-build reference
- Architecture corrected from V1 misconceptions
- Data contracts specified for Layer 4 → 4b → 5 handoffs

### Open items recorded
- Layer 4 build execution (7-8 hours estimated)
- Layer 4b build (5-6 hours estimated)
- Layer 5 build (6-7 hours estimated)

### Notes
- This corrects errors from earlier sessions where BBW was described as having 6 layers; VINCE is confirmed separate. Also establishes that trade direction comes from Four Pillars strategy, not BBW states.

---

## 2026-02-16-bbw-v2-layer4-build-journal.md
**Date:** 2026-02-16
**Type:** Build session

### What happened
Complete build journal for `research/bbw_analyzer_v2.py` (Layer 4). Documented all 10 phases of construction using test-first development. The journal starts with a pre-build checklist (showing "BUILD NOT STARTED") but the final build summary confirms all 10 phases completed.

Key phases completed:
- Phase 1 (Input Validation): validate_backtester_data() and validate_bbw_states(), 10/10 assertions PASS
- Phase 2 (Data Enrichment): enrich_with_bbw_state() with left join to preserve all trades, 33/33 PASS
- Phase 3+4 (Grouping + Metrics): group_by_state_direction_lsg(), calculate_group_metrics(), 62/62 PASS
- Phase 5 (Best Combo): find_best_lsg_per_state_direction(), 91/91 PASS
- Phase 6 (Directional Bias): detect_directional_bias() with 5% threshold, 125/125 PASS
- Phase 7 (Main Pipeline): analyze_bbw_patterns_v2() orchestrator + BBWAnalysisResultV2 dataclass, 162/162 PASS
- Phase 8 (Debug Script): scripts/debug_bbw_analyzer_v2.py with 10 sections
- Phase 9 (Sanity Check): scripts/sanity_check_bbw_analyzer_v2.py — 2000 trades, 0.24s runtime, all validations PASS
- Phase 10 (Documentation): All functions have docstrings

Final results: 44 unit tests, 162 assertions, all PASS. Runtime 0.24s for 2000 trades (~8,333 trades/sec). 3 syntax errors encountered and fixed (unicode chars, invalid BBW state names, missing symbol column).

### Decisions recorded
- Left join used for enrichment (preserves all trades)
- Categorical dtypes for grouping performance
- Sort → GroupBy → First pattern for "best per group"
- Empty DataFrame handling propagates correctly through pipeline
- MISSING_DIRECTION is a valid bias state (some states may only work one direction)
- Tie-breaking: first in sort order (stable, deterministic)

### State changes
- research/bbw_analyzer_v2.py created (~640 lines)
- tests/test_bbw_analyzer_v2.py created (~1250 lines, 44 tests, 162 assertions)
- scripts/debug_bbw_analyzer_v2.py created (~505 lines)
- scripts/sanity_check_bbw_analyzer_v2.py created (~375 lines)
- Sanity check generated 4 CSV output files in results/bbw_analyzer_v2_sanity/

### Open items recorded
- Layer 4b (Monte Carlo V2) build next
- Layer 5 build after 4b complete

### Notes
- The journal template section (showing "NOT STARTED") is the pre-build placeholder; the actual build log entries confirm all 10 phases were completed within the same session.
- CODE VERIFICATION: File path referenced as `research/bbw_analyzer_v2.py` in project root.

---

## 2026-02-16-bbw-v2-layer4b-build-journal.md
**Date:** 2026-02-16
**Type:** Build session (journal header only — build not yet executed)

### What happened
Build journal template created for `research/bbw_monte_carlo_v2.py` (Layer 4b). Status marked "BUILD STARTED" but no build log entries are present — the file contains only the journal header with architecture overview, build plan, input/output contracts, core logic definitions (bootstrap PnL function, permutation DD function, verdict classification function), math validation trackers (all PENDING), and a files-to-create list.

Key design documented:
- Bootstrap: Resample with replacement 1000 sims, extract 5th/95th percentile CI
- Permutation DD: Shuffle sequence, compare real DD to permuted p95
- Verdict logic: INSUFFICIENT → COMMISSION_KILL → FRAGILE → ROBUST

Layer 4b V2 vs V1 difference: V1 validated simulated trades; V2 validates real backtester results.

### Decisions recorded
- Bootstrap uses 1000 simulations by default
- 90% CI (5th and 95th percentiles)
- Verdict priority order: INSUFFICIENT → COMMISSION_KILL → FRAGILE → ROBUST
- COMMISSION_KILL: ci_upper < 0 (even best-case scenario loses money)
- FRAGILE: ci_lower < 0 OR dd_fragile
- ROBUST: ci_lower >= min_net_expectancy (default $1.00)

### State changes
- Build journal file created as template
- No code files created yet in this journal

### Open items recorded
- All 7 build phases pending execution
- 30+ unit tests to write
- Bootstrap CI coverage validation
- Permutation DD detection validation
- Verdict logic validation

### Notes
- The 2026-02-17 bbw-project-completion-status.md log confirms Layer 4b was eventually completed (45/45 tests PASS, 56/56 debug PASS), so the actual build happened in a subsequent session not captured in this journal.

---

## 2026-02-16-bbw-v2-layer5-logic-analysis.md
**Date:** 2026-02-16
**Type:** Architecture spec / pre-build analysis

### What happened
Pre-build logic verification for Layer 5 (`research/bbw_report_v2.py`). Documented function-by-function logic for all 6 functions: aggregate_directional_bias(), generate_be_fees_success_tables(), create_vince_features(), analyze_lsg_sensitivity(), generate_state_summary(), and generate_vince_features_v2() orchestrator.

Three critical logic issues identified:
1. Column name mismatch: Layer 4 uses `bbw_state_at_entry`, Layer 4b uses `bbw_state` — Layer 5 must standardize
2. Verdict encoding includes "MARGINAL" which doesn't exist in Layer 4b output (fix: remove MARGINAL)
3. Missing edge case handling for states with only one direction and NaN correlations

VINCE feature output includes: state ordinal encoding, direction binary, bias alignment, bias strength, LSG parameters, verdict ordinal, sample weight (ROBUST=1.0, others=0.5). Target variables: be_plus_fees_rate, avg_net_pnl, sharpe, verdict.

4 questions documented for user approval before build.

### Decisions recorded
- Layer 5 should accept both `bbw_state_at_entry` and `bbw_state` column names
- NEUTRAL bias: feature_bias_aligned = 0 (no alignment bonus)
- Missing verdict: use "UNKNOWN" (not raise error)
- State quality: categorical HIGH_QUALITY/MIXED/DEAD
- MARGINAL verdict removed from encoding dict
- Recommended build order: fix column name issue first, then Functions 1-5, then orchestrator

### State changes
- Analysis document created
- No code written yet
- 4 logic issues identified and resolved in spec

### Open items recorded
- User must approve 4 logic questions before build
- 48 unit tests to write (~120 assertions)
- 7-section debug script needed

### Notes
- This log establishes the spec for Layer 5 which was built on 2026-02-17.

---

## 2026-02-16-full-project-review.md
**Date:** 2026-02-16 15:45 GST
**Type:** Session log / project review

### What happened
Comprehensive project review intended for mobile reading. Covers: Four Pillars strategy components (all 4 pillars: Ripster EMAs, AVWAP, Quad Rotation Stochastics, BBWP), trade lifecycle mechanics (SL phases, TP logic, multi-slot position management), commission and rebate model, full BBW Pipeline status (Layers 1-4b COMPLETE, Layer 5 IN PROGRESS), VINCE ML architecture (9 modules), training data strategy (hybrid split 280/40/79), and critical path timeline.

Key findings reported:
- BBW Monte Carlo RIVERUSDT results: 6/7 states COMMISSION_KILL, 1 state FRAGILE (RED_DOUBLE, net_exp=$10.90)
- Commission drag: avg gross exp $5.22/trade, avg net exp -$1.92/trade, commission drag $7.14/trade
- $8 RT commission kills edge on 6/7 BBW states
- Fix required: BE raise restoration reduces loser count → improves net_exp

Known bug documented: AVWAP trail not ratcheting properly in v3.9, location: `engine/exit_manager.py` lines ~200-250.

### Decisions recorded
- VINCE training data split: 280 train (53%), 40 val (10%), 79 test (20%, FROZEN), remaining future reserve
- splits.json created ONCE before any training, never modified
- Test set: 79 coins, NEVER loaded during development
- 5-fold cross-validation on training set
- Monte Carlo verdicts filter training data: COMMISSION_KILL states excluded entirely
- Data augmentation: bootstrap within-state trades + BBWP noise injection (±2%) for training only

### State changes
- Document created as reference/review
- No code changes in this session

### Open items recorded
- BBW Layer 5 completion (this week)
- Dashboard 5m validation + AVWAP trail bug fix
- Restore BE raise in backtester
- Generate splits.json
- VINCE Module 3 build (next week)
- Cloud 4 trailing exit (week 3)

### Notes
- Confirms: "NO LAYER 6" — VINCE is separate component, not part of BBW

---

## 2026-02-16-portfolio-bugfix.md
**Date:** 2026-02-16
**Type:** Build session (two sessions)

### What happened
Two AFK build sessions fixing dashboard portfolio bugs.

**Session 1:** Two bugs fixed via `scripts/build_portfolio_bugfix.py` (5 patches):
- BUG A: Run Portfolio Backtest re-randomizes coin list — fix: store port_symbols in session_state["port_symbols_locked"] when Run clicked; added Reset Selection button
- BUG B: "Best Equity" / "Worst DD" metrics confusing — fix: renamed to "Peak Net Profit" (+$X from baseline) and "Worst Drawdown" (% and $ amount), added help tooltips

**Session 2:** Capital Model Consistency Fix via `scripts/build_capital_mode_fix.py` (10 patches):
- 7 data consistency bugs found in Shared Pool mode: per-coin metrics table, drill-down trades, trading volume section, daily volume stats, Net P&L after rebate, Total Trades metric, and per-coin monthly P&L all used unconstrained (unfiltered) data even after capital constraints rejected trades
- Root cause: capital_model.py rebuilt equity curves but left trades_df and metrics dict untouched
- Fix: Added `_rebuild_metrics_from_df()` helper, filtered trades_df to accepted-only, rebuilt metrics for adjusted coin results

### Decisions recorded
- Lock coin selection on Run button click, clear lock on Back button
- Metrics display must use accepted-only data in Shared Pool mode

### State changes
- scripts/build_portfolio_bugfix.py created
- scripts/build_capital_mode_fix.py created
- Both build scripts: BUILD READY, NOT EXECUTED (user runs)

### Open items recorded
- User must run both build scripts
- Validation checklists provided for both

### Notes
- Status at session end: BUILD READY, NOT EXECUTED for both.

---

## 2026-02-16-portfolio-v3-audit.md
**Date:** 2026-02-16
**Type:** Audit session (multiple sub-sessions)

### What happened
Multi-session audit and rebuild of dashboard portfolio enhancement utilities. Started with user reporting "something feels off" about the v2 build script.

**Audit Phase:** Read build_dashboard_portfolio_v2.py and cross-referenced against actual engine output (backtester_v384.py, position_v384.py, dashboard.py). Found 9 bugs:
- BUG 1 (CRITICAL): Capital model was decorative — returned original pf_data unchanged, rejection logic had zero effect
- BUG 2 (CRITICAL): Bar indices are per-coin local, not master_dt coordinates — caused incorrect overlap detection
- BUG 3 (CRITICAL): MFE used in signal strength = look-ahead bias (MFE only known after exit)
- BUG 4 (MEDIUM): rebate column doesn't exist in trades_df
- BUG 5 (MEDIUM): entry_dt column doesn't exist in trades_df (only entry_bar integer)
- BUG 6 (MEDIUM): Sortino annualized by trade count not bar count
- BUG 7 (MEDIUM): Capital efficiency used unconstrained values
- BUG 8 (LOW): be_raised not in trades_df
- BUG 9 (LOW): Test suite used fabricated data columns (entry_dt, rebate) masking integration failures

**V3 Build:** Created `scripts/build_dashboard_portfolio_v3.py` (~1500 lines) fixing all 9 bugs. Key fixes:
- Capital model: rebuild equity curves by subtracting rejected trade P&L
- Bar mapping: `_map_bar_to_master()` maps per-coin bar indices to master_dt via datetime_index searchsorted
- Signal strength: grade-only priority (no MFE)
- Test suite: realistic data structures matching actual _trades_to_df() output

**Session 2 continuation:** Tests confirmed 81/81 PASSED, debug ALL PASSED. Build script synced.

**Session 2b:** Created `scripts/build_dashboard_integration.py` with 6 patches to wire utilities into dashboard_v2.py.

### Decisions recorded
- Capital model must be post-processing (can't modify engine behavior)
- All cross-coin comparisons must map through datetime_index to master_dt
- Tests must use data structures from actual engine, not synthetic equivalents
- Look-ahead bias: only use entry-time information (grade, ATR, price levels, signals) for prioritization
- Integration not done automatically; requires separate integration build script

### State changes
- scripts/build_dashboard_portfolio_v3.py created (1500 lines)
- 8 utility files created by v3 build (utils/portfolio_manager.py, coin_analysis.py, pdf_exporter.py, capital_model.py, tests/, debug scripts)
- 81/81 tests PASSED (confirmed by user)
- FILE-INDEX.md updated with v3 reference
- scripts/build_dashboard_integration.py created (6 patches)

### Open items recorded
- User must run build_dashboard_integration.py to wire utils into dashboard
- Dashboard integration not started
- PDF dependency: pip install reportlab
- 5 open questions for user (integration timing, capital mode default, rejected trade visibility, PDF missing features, BBW integration)

### Notes
- Critical insight: backtester is NOT a portfolio engine; it's single-coin with results merged post-hoc. Capital model is always post-processing.

---

## 2026-02-16-project-status-data-strategy.md
**Date:** 2026-02-16 15:30 GST
**Type:** Session log / strategy planning

### What happened
Eagle-eye project status check combined with VINCE data preservation strategy planning. Corrected earlier error where Claude had described BBW as having 6 layers (Layer 6 = LLM analysis). User confirmed BBW has 5 layers only, VINCE is separate.

Data preservation analysis prompted by user concern: "I don't want VINCE to burn through my limited data and then have data bias." Documented recommended hybrid split strategy and data inventory (~42M bars, 399 coins × ~1 year × 5m).

Key comparison table for split strategies:
- No split: EXTREME bias risk
- Simple 80/20: High risk
- Hybrid recommended (53% train): Low risk
- Overly conservative (40%): Low but wasteful

### Decisions recorded
- Hybrid split: 280 train (53%), 40 val (10%), 79 test (20%, FROZEN), remaining future reserve
- Time-based walk-forward split REJECTED (market regime shifts would invalidate test distribution)
- splits.json written ONCE before any training, never modified
- Test coins NEVER loaded during development
- 5-fold CV on training set (224 train, 56 validate per fold)
- COMMISSION_KILL states excluded from training entirely
- Data augmentation: bootstrap within-state + BBWP noise injection (±2%, training only)

### State changes
- Architecture correction logged: BBW = 5 layers, VINCE = separate
- Strategy document created
- No code changes

### Open items recorded
- Complete BBW Layer 5
- Generate splits.json (280/40/79 allocation)
- Restore BE raise in backtester
- Run 400-coin sweep
- Build VINCE Module 3 (next week)

### Notes
- This log contains the same split numbers (280/40/79) as the full-project-review.md from the same day, confirming the decision was made and documented consistently.

---

## 2026-02-16-strategy-actual-implementation.md
**Date:** 2026-02-16
**Type:** Reference documentation

### What happened
Accurate documentation of the Four Pillars strategy as actually implemented in v3.8.4, sourced from signals/state_machine.py and signals/four_pillars.py. Covers: signal pipeline architecture, four stochastic components (stoch_9 entry trigger, stoch_14 primary confirmation, stoch_40 divergence, stoch_60 macro), Ripster EMA clouds (Cloud 2: 5/12 for re-entry, Cloud 3: 34/50 mandatory directional filter, Cloud 4: 72/89 planned trailing), ATR calculation (Wilder's RMA), two-stage state machine (Stage 0: Idle, Stage 1: Setup window max 10 bars), grade classification (A/B/C), re-entry system (Cloud 2 within 10 bars), ADD signals (not used in backtester v384).

Key corrections to common misconceptions documented:
- AVWAP NOT used for entries (exits only)
- D signal is optional filter, not a signal
- BBW states do not affect entry signals (v4 integration planned)
- All stochastics are raw K, no smoothing

### Decisions recorded
- Cloud 3 filter is NON-NEGOTIABLE and ALWAYS ENFORCED for A/B grades
- Grade C bypasses Cloud 3 directional filter (only requires price outside cloud)
- 10-bar setup window max
- D-line filter disabled by default

### State changes
- Reference document created
- No code changes

### Open items recorded
- ADD signals: reserved for future pyramiding logic (signal generated but not acted upon in v384)
- Cloud 4 trailing: planned for v3.9.1

### Notes
- This is the definitive strategy reference for v3.8.4, intended to correct prior misconceptions.

---

## 2026-02-16-trade-flow-uml.md
**Date:** 2026-02-16 15:50 GST
**Type:** Reference documentation (Mermaid UML diagrams)

### What happened
10 Mermaid UML diagrams created for project architecture and workflow visualization, intended for mobile review and Obsidian rendering. Diagrams cover:
1. Trade Lifecycle State Machine (Idle → Signal → Grade → Entry → SL phases)
2. Entry Grade Decision Tree (Quad Stoch → Cloud 3 → AVWAP → BBW → Grade A/B/C)
3. Stop Loss Lifecycle Flow (Initial → BE Raise → AVWAP Trailing)
4. SL Movement Over Time (numbered example: entry $100, ATR $2.50, SL progression)
5. ADD Signal Flow (sequence diagram)
6. System Architecture Component Diagram (all layers from data to live trading)
7. Critical Path Timeline (Gantt chart Feb-Mar 2026)
8. Commission and Rebate Flow
9. Data Split Strategy (280/40/79 with 5-fold CV)
10. Multi-Slot Position Management (sequence diagram)

### Decisions recorded
- None (documentation only)

### State changes
- Document created with 10 Mermaid diagrams

### Open items recorded
- None recorded in this file

### Notes
- Diagram 2 (Entry Grade Decision Tree) shows AVWAP and BBW influencing grade classification, which conflicts with strategy-actual-implementation.md which states AVWAP is only for exits. This may reflect a planned future state vs current implementation.

---

## 2026-02-17-bbw-project-completion-status.md
**Date:** 2026-02-17
**Type:** Session log (multiple sessions)

### What happened
Multi-session log covering 3 sessions on 2026-02-17:

**Session 1 (Morning):** BBW remaining build completed. Build script `scripts/build_bbw_remaining.py` generated 9 files, 45/45 tests PASS:
- research/coin_classifier.py (KMeans k=3-5 with silhouette selection, tiers by avg_atr_pct)
- research/bbw_ollama_review.py (optional LLM review of Layer 5 CSVs, NOT a pipeline layer)
- scripts/run_bbw_simulator.py (CLI wiring L1-L5 end-to-end)
- Plus 6 test + debug scripts

Smoke test PASS: RIVERUSDT 32,762 bars, 21.2s, 11 files written, 0 errors.

Bug fix: coin_classifier duplicate processing — glob matched both _1m and _5m files. Fixed with `glob("*_1m.parquet")` + seen_symbols dedup guard.

Layer 6 clarification confirmed: Layer 6 = ML/Vince = SEPARATE PROJECT. bbw_ollama_review.py is optional utility, not a layer. MEMORY.md updated.

**Session 2 (Afternoon):** Summarized BBW project status, critical path timeline, and pending tasks. Dashboard v3.9.1 confirmed stable (0 rejections, commission math validated).

**Session 3 (~19:03 UTC):** BBW V2 pipeline bug fixes and run_bbw_v2_pipeline.py created.

Bugs fixed:
1. bbw_analyzer_v2.py: column names corrected (bbwp_state/bbwp_value not bbw_state/bbwp), validators relaxed, timestamp merge changed to pd.merge_asof
2. bbw_report_v2.py: mc_result=None guard, validate_report_inputs no longer raises on empty state_verdicts
3. scripts/run_bbw_v2_pipeline.py created as bridge script loading portfolio CSV, adapting columns, running L4v2→L4bv2→L5

Run 1 (without rebate): ROBUST=0, FRAGILE=3, COMMISSION_KILL=11 (false positive)
Run 2 (with rebate --rebate-rate 0.70): ROBUST=8, FRAGILE=6, COMMISSION_KILL=0 — 14 feature rows for VINCE

VINCE feature results: BLUE_DOUBLE and MA_CROSS_UP = HIGH_QUALITY (both directions ROBUST). SHORT bias dominant in RED/RED_DOUBLE/MA_CROSS_DOWN/NORMAL/MA_CROSS_UP.

Output files: vince_features.csv (14 rows), directional_bias.csv, be_fees_success.csv, lsg_sensitivity.csv (empty, single LSG), state_summary.csv written to results/bbw_v2/

### Decisions recorded
- BBW project declared COMPLETE — both pipeline tracks functional
- Daily rebate must be included in pnl_net calculation for correct COMMISSION_KILL verdicts
- Layer 6 = VINCE = SEPARATE project (hard rule added to MEMORY.md)
- bbw_ollama_review.py = optional utility, NOT a pipeline layer

### State changes
- research/coin_classifier.py created
- research/bbw_ollama_review.py created
- scripts/run_bbw_simulator.py created
- research/bbw_analyzer_v2.py patched (3 fixes)
- research/bbw_report_v2.py patched (2 fixes)
- scripts/run_bbw_v2_pipeline.py created (new bridge script)
- vince_features.csv generated: 14 rows
- BBW project status changed from IN PROGRESS → COMPLETE

### Open items recorded
- Update UML diagrams (mark all layers L1-L5 complete, add CLI entry point)
- Generate coin_tiers.csv
- Multi-coin BBW sweep (top 10)
- Deploy VINCE ML staging
- MC result caching before 400-coin sweep

### Notes
- COMMISSION_KILL=11 in Run 1 was a false positive caused by missing daily rebate in CSV pnl_net. After applying rebate correction, results shifted dramatically to ROBUST=8.

---

## 2026-02-17-dashboard-v391-audit.md
**Date:** 2026-02-17
**Type:** Build session (5 sessions)

### What happened
Multi-session audit and rebuild resulting in Dashboard v3.9.1. Root cause investigation: Pool P&L showed -$9,513 while per-coin sum showed +$4,656.

**Session 1 (Audit):** Found root causes of discrepancy:
- E1 (Engine): SL/TP/Scale-out exits charged taker instead of maker — ~$6 overcharge per trade × ~1145 trades = ~$6,870 overcharge. Fix: maker=True on 3 lines (144, 174, 407 of backtester_v384.py)
- C1 (Capital Model, ROOT CAUSE): Scale-out trades treated as separate pool positions — one $500 position with 2 scale-outs consumes $1,500 in pool margin instead of $500
- C2 (Capital Model): Double margin deduction in available calculation
- D1-D7: Display-level bugs (wrong baselines, hardcoded 10000.0, DD% against wrong baseline)

**Session 2:** Engine fix applied (maker=True). Build script rewritten: capital_model_v2.py with position grouping via `_group_trades_into_positions()`, exchange-model pool with separate balance and margin_used. Dashboard: 11 patches. 15/15 patch targets verified.

**Session 3 (Post-Build Audit, 3-coin test):** Pool P&L = +$5,975 but 195 trade rejections. New bugs:
- P1: Pool simulation doesn't include rebate (only adds net_pnl on close)
- P2: "Net P&L (after rebate)" label confusing → renamed to "True Net P&L"
- P3: Discrepancy between drill-down sum and True Net P&L (stale state)

**Session 4 (Daily Rebate Fix):** Critical fix for Bug C3 — daily rebate settlement in pool simulation. Without it, pool drains to $491 with 195 rejections (10.5%). With daily rebate settlement: 0 rejections, pool stays above $5,762, final pool $12,480. Implementation: check 5pm UTC boundary before each bar, credit daily_comm × rebate_pct to balance. Also: combined trades CSV export added (PATCH 14), PDF per-coin chart rebasing fixed.

Commission model validation across 3 portfolio sizes: blended rate stable at ~0.0503-0.0505%/side, rebate ~67.4-67.5% (shortfall = unsettled last-day commission, acceptable).

**Session 5:** Build script `scripts/build_uml_diagram.py` created for Mermaid UML diagrams (6 diagrams: Component, Class, Portfolio Sequence, ER, Commission Flow, Shared Pool State Machine).

### Decisions recorded
- Exchange model: track positions (not individual trade records) through pool
- Position = (coin, entry_bar) key, collapses all scale-outs
- Separate balance and margin_used tracking (no double deduction)
- Daily rebate must settle intra-simulation at 5pm UTC boundaries
- "True Net P&L" = net_pnl + rebate (renamed from confusing "Net P&L after rebate")
- DD% = cash-on-hand drawdown from realized balance only (documented as known limitation)

### State changes
- engine/backtester_v384.py modified: maker=True on lines 144, 174, 407
- utils/capital_model_v2.py generated (537 lines, 7 functions)
- utils/pdf_exporter_v2.py generated (330 lines)
- scripts/dashboard_v391.py generated (2338 lines, 14 patches)
- scripts/build_dashboard_v391.py rewritten (916 lines)
- scripts/debug_pool_balance_v2.py created (543 lines)
- scripts/build_uml_diagram.py created (789 lines)
- Dashboard version: v3.9 → v3.9.1 (STABLE)

### Open items recorded
- 3 known minor issues documented (Net P&L vs per-coin sum gap ~$321, BANKUSDT positive Net but negative Sharpe/PF, DD% is cash-on-hand only)
- User needs to verify P3 discrepancy after rebuild

### Notes
- C1 (scale-out grouping) was the ROOT CAUSE of the -$9,513/-+$4,656 discrepancy. This is the most critical bug found in this session batch.

---

## 2026-02-17-pdf-diagram-alignment.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
User reported UML diagrams in BBW-V2-UML-DIAGRAMS.md were "not aligned per page" when exported to PDF. Created PDF-optimized version `BBW-V2-UML-DIAGRAMS-PDF.md` with explicit page breaks between each diagram, simplified diagrams (max 10 nodes, short labels, removed verbose subgraphs), one diagram per page, and summary tables at end.

Layout defined: 10 pages total — pages 1-8 each have one diagram, pages 9-10 have summary tables. Size reduction: ~40% smaller Mermaid code. Content preserved via tables for details moved out of diagrams.

### Decisions recorded
- Each diagram on separate page (explicit page-break-after divs)
- Max 10 nodes per diagram for PDF compatibility
- Short node labels (≤3 words)
- Tables for detailed data instead of diagram annotations

### State changes
- docs/bbw-v2/BBW-V2-UML-DIAGRAMS-PDF.md created

### Open items recorded
- User must test PDF export and report remaining issues

### Notes
- None

---

## 2026-02-17-pdf-export-optimization.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
User reported BUILD-VINCE-ML.pdf was "crooked" and needed reformatting. Rewrote BUILD-VINCE-ML.md with PDF-optimized structure: Table of Contents, 8 numbered sections, 40+ page break hints, code blocks max 40 lines, 5 tables for CLI args, shorter paragraphs, visual hierarchy.

Also created BBW-V2-ARCHITECTURE.md as a new PDF-friendly version of the architecture document: simplified Mermaid diagram, prose descriptions, status tables, glossary.

### Decisions recorded
- PDF best practices applied: page breaks after major sections, tables max 5 columns, code blocks max 40 lines, clear heading hierarchy, simplified Mermaid diagrams, generous white space

### State changes
- BUILD-VINCE-ML.md rewritten (PDF-optimized)
- docs/bbw-v2/BBW-V2-ARCHITECTURE.md created (new)

### Open items recorded
- User must test PDF export of both files

### Notes
- None

---

## 2026-02-17-pdf-orientation-fix.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
Added landscape orientation for diagrams 2 (Data Flow Sequence) and 6 (VINCE Deployment) in BBW-V2-UML-DIAGRAMS-PDF.md, plus center alignment for all content. CSS block added with @page rules and .diagram-container class. Wrapped all content in centered divs.

Documented that @page CSS support varies by tool (wkhtmltopdf = good support; Chrome/Firefox print = limited). Provided 4 export methods and manual fallback instructions (rotate pages 2 and 6 in PDF viewer).

### Decisions recorded
- Pages 2 and 6 should be landscape orientation
- All diagrams centered horizontally
- wkhtmltopdf recommended for reliable @page support

### State changes
- docs/bbw-v2/BBW-V2-UML-DIAGRAMS-PDF.md modified: CSS added, content wrapped in divs, landscape markers added

### Open items recorded
- User must test CSS method and report if @page orientation works in Obsidian

### Notes
- None

---

## 2026-02-17-project-clarity-and-vince-architecture.md
**Date:** 2026-02-17 (Tuesday)
**Type:** Session log / architecture planning

### What happened
~45-minute session preparing for a funding meeting. User asked for clarity on 10 topics: 5-task breakdown, VINCE independence, trading engine architecture, Cloud 3 constraint flexibility, GUI concept, version chaos, BBW next steps, PyTorch/XGBoost build status, funding talking points, and "what if" capability.

Project state confirmed:
- State Machine v3.8.3: STABLE
- Backtester v3.8.4: STABLE (BE raise removed accidentally)
- Exit Manager v3.8.4: BUGGY (AVWAP trail not ratcheting)
- Dashboard v3.9: STABLE
- BBW Pipeline v2.0: Layers 1-4b COMPLETE, Layer 5 IN PROGRESS
- VINCE ML v0.0: SPEC ONLY, 0% built

VINCE independence analysis: VINCE is tightly coupled to Four Pillars (14 hardcoded indicator fields). Three options discussed:
- Option A (RECOMMENDED): Hybrid — VINCE-Core (strategy-agnostic) + VINCE-FourPillars (current)
- Option B: Full rebuild with abstract interfaces (rejected — 4-6 weeks, overengineering)
- Option C: Clone repository per strategy (accepted as short-term pragmatic)

5-task breakdown: (1) Update UML ~30min, (2) Generate coin_tiers.csv ~5min, (3) Multi-coin BBW sweep ~10min, (4) Deploy VINCE staging ~15min, (5) MC result caching ~1 session.

Cloud 3 flexibility: Currently hardcoded in state_machine_v383.py. Could be made configurable but would break grade logic — not recommended until strategy proven.

"What if" capability concept: VINCE could run counterfactual simulations (what if leverage=15 instead of 20?) by injecting different LSG and re-running MC simulation. Documented as future feature.

### Decisions recorded
- VINCE-FourPillars (tight coupling) accepted for now; VINCE-Core extraction deferred post-launch
- Cloud 3 constraint: keep hardcoded until strategy proven
- "What if" simulations: future feature after v1.0 deployed

### State changes
- Session log created
- No code changes

### Open items recorded
- Funding meeting tomorrow — talking points documented
- Tasks 1-5 ranked by priority (UML update highest for pitch)
- VINCE-Core extraction: 2-3 week project after live trading proven

### Notes
- Confirms VINCE is 0% built (spec only) as of 2026-02-17 morning.

---

## 2026-02-17-python-skill-update.md
**Date:** 2026-02-17
**Type:** Infrastructure / meta session

### What happened
Review and update of Python coding skill files across all locations. Added multiple new sections to both vault SKILL.md and user-level SKILL.md. Content added:

- Filename Etiquette: naming convention table, project directory structure, safe_write_path() versioning helper
- Debugging: logging over print, structured exception handling, debug script template, log level discipline table
- Testing (Enhanced): programmatic py_compile.compile() in build scripts with ERRORS list, unittest template, make_ohlcv() mock data helper, assert patterns with msg=
- Syntax Error Prevention: f-string join trap, triple-quoted string escaping rules, ast.parse() secondary validator
- Code Patterns: input validation, API rate limiting, OHLCV data validation, incremental processing, performance (parquet/vectorized)
- Trading System Specifics: commission calculation, UTC timestamps
- Code Review Checklist expanded from 11 to 28 items across 5 categories

Also added MEMORY.md hard rule: "PYTHON SKILL MANDATORY — Before writing ANY Python code, ALWAYS load the Python skill first."

### Decisions recorded
- Python skill is mandatory before any .py file work (rule added to MEMORY.md)
- Both skill locations synchronized with identical content

### State changes
- Vault/.claude/skills/python/SKILL.md: updated (sections added)
- C:/Users/User/.claude/skills/python/SKILL.md: created (new)
- MEMORY.md: hard rule appended
- Legacy python-trading-development.md left in place (to delete when ready)

### Open items recorded
- Delete legacy python-trading-development.md when ready

### Notes
- Only 2 Python skill locations found (user expected 3 — confirmed only 2 exist).

---

## 2026-02-17-uml-diagrams-creation.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
User requested proper UML diagrams for BBW V2 architecture. Previous document had too much prose. Created `docs/bbw-v2/BBW-V2-UML-DIAGRAMS.md` with 8 comprehensive Mermaid diagrams.

Layer 3 investigation: Read bbw_forward_returns.py and determined it's a pure function that adds 17 forward-looking metrics (fwd_10_max_up_pct, fwd_10_max_down_pct, fwd_10_close_pct, fwd_10_max_up_atr, fwd_10_max_down_atr, fwd_10_max_range_atr, fwd_10_direction, fwd_10_proper_move — same 8 for 20-bar window, plus fwd_atr). Integration decision: Layer 3 → Layer 5 (forward returns as VINCE features).

8 diagrams created:
1. Component Architecture
2. Data Flow Sequence
3. Layer 3 Output Schema
4. BBW State Transitions (7 states)
5. Class Diagram - Data Contracts
6. Deployment: VINCE Local → Cloud
7. Activity: 400-Coin Sweep
8. Component Interaction (file-level)

VINCE deployment strategy documented: Phase 1 local training on RTX 3060, Phase 2 cloud deployment (TBD: AWS/GCP/Azure/DigitalOcean), Phase 3 TradingView → n8n → VINCE cloud API → trade execution.

### Decisions recorded
- Layer 3 integration: Layer 3 → Layer 5 (forward metrics as VINCE training features)
- VINCE deployment: local first, then cloud

### State changes
- docs/bbw-v2/BBW-V2-UML-DIAGRAMS.md created (8 diagrams)

### Open items recorded
- User to review diagrams, validate Layer 3 → Layer 5 integration
- Decide on cloud platform for VINCE deployment
- Layer 5 build: include forward_metrics.csv export

### Notes
- Layer 3 was previously marked "COMPLETE" but had no downstream consumer (orphaned). This session resolved that by deciding Layer 3 feeds Layer 5.

---

## 2026-02-17-uml-logic-debugging.md
**Date:** 2026-02-17
**Type:** Build session (debugging)

### What happened
Debug session on BBW-V2-ARCHITECTURE.md diagrams. Found 4 logical flow issues:

1. Layer 3 Orphaned (CRITICAL): `L1 --> L2 --> L3 [DEAD END]` — no output connection
2. Missing Data Source: Layer 1 had no input shown (CACHE node added)
3. VINCE Feedback Loop Ambiguity: `VINCE --> BT` arrow unclear (training vs production)
4. Missing Data Flow Labels: arrows didn't specify what data passes between nodes

Created corrected version `BBW-V2-ARCHITECTURE-CORRECTED.md`:
- Added CACHE data source node
- Layer 3 marked as "Research - Not used by L4" (dotted line)
- VINCE split into training mode (solid arrow L5→VINCE) and production mode (dotted arrow VINCE-.->BT)
- All arrows labeled with data contracts

Documented component dependency matrix showing Layer 3 still has unclear downstream use.

### Decisions recorded
- Layer 3 status: requires user clarification (Options A/B/C/D presented)
- VINCE feedback loop: solid for training CSVs, dotted for future production use
- User decision required: Layer 3 integration choice

### State changes
- docs/bbw-v2/BBW-V2-ARCHITECTURE-CORRECTED.md created

### Open items recorded
- User to decide: Layer 3 integration option (A: Layer 3→L5, B: standalone, C: Layer 3→L4, D: remove)
- User to confirm: VINCE production mode (real-time service vs offline optimizer)

### Notes
- This file and uml-diagrams-creation.md from the same day give conflicting guidance on Layer 3 — the creation log decided Layer 3→Layer 5, but this debugging log still marks it as "requires clarification." Likely uml-logic-debugging.md was written before uml-diagrams-creation.md finalized the decision.

---

## 2026-02-17-vince-ml-strategy-exposure-audit.md
**Date:** 2026-02-17
**Type:** Audit session

### What happened
Security/IP audit of codebase to determine what is safe to share publicly. Triggered by user question about VINCE ML build exposing the Four Pillars strategy.

Two codebase agents scanned signals/ and ml/ directories plus build_staging.py.

Findings:
- signals/ (10 files): PROPRIETARY — NOT SAFE TO SHARE. Contains A/B/C/R grade entry logic, Kurisko Raw K stochastic settings (K1=9, K2=14, K3=40, K4=60), Ripster EMA cloud parameters (5/12, 34/50, 72/89), full signal pipeline. "Anyone with these files could fully replicate Four Pillars."
- ml/ (14 files): GENERIC — SAFE TO SHARE. Strategy-agnostic: features.py, meta_label.py, triple_barrier.py, purged_cv.py, bet_sizing.py, walk_forward.py, vince_model.py (PyTorch multi-task), xgboost_trainer.py, training_pipeline.py, etc. "Could plug into any strategy."
- scripts/build_staging.py: NOT SAFE (embeds exact stochastic settings and cloud parameters)
- scripts/dashboard*.py: NOT SAFE (parameter UI reveals all indicator settings)

### Decisions recorded
- ml/ directory safe to open-source as-is
- signals/ and all dashboard files: treat as confidential
- If open-sourcing backtester framework: replace signals/ with strategy interface/stub
- Strip all numeric defaults from dashboard before sharing

### State changes
- Audit document created
- No code changes

### Open items recorded
- No open items explicitly stated

### Notes
- Confirms ml/ directory contains 14 built files including vince_model.py (PyTorch multi-task model with tabular + LSTM + context branches). This is significant: as of 2026-02-17, ml/ files existed and were built, contradicting the project-clarity-and-vince-architecture.md file from the same day which says "VINCE ML v0.0: SPEC ONLY, 0% built." The audit found actual ML code in ml/ — likely build_staging.py deployed these files.


# Research Findings — Batch ordered-07

**Generated:** 2026-03-05
**Files processed:** 20
**Date range:** 2026-02-18 to 2026-02-25

---

## File 1: 2026-02-18-dashboard-audit.md

**Date:** 2026-02-18
**Type:** Code audit / verification

**What happened:**
Full read-through of 9 source files (~4,315 lines total) to verify backtest results are legitimate. User asked "is this really through, all those trades taken would they really result in that?" Audit covered signals, backtester engine, position management, commission, AVWAP, and dashboard display.

**Decisions recorded:**
- Engine declared MECHANICALLY CORRECT for all components except one known bug
- Scale-out commission double-count in CSV confirmed (low severity): SCALE_1 remainder shows commission=9.0 when it should be 5.0. Equity curve UNAFFECTED — entry commission deducted once at entry time only.
- Dashboard display: no inflation anywhere. Metrics direct from backtester dict.

**State changes:**
- Signals (stochastics, clouds, state_machine_v383): CORRECT
- Backtester (backtester_v384): CORRECT with 1 known CSV bug
- Position (position_v384): CORRECT
- AVWAP: CORRECT
- Commission: CORRECT
- Equity curve: CORRECT
- "77K-90K trades and 85-86% LSG numbers are REAL."

**Open items recorded:**
- Scale-out commission CSV bug: low priority, equity unaffected

**Notes:**
K4 stage machine: K4 enters extreme < 25 for longs, fires A/B/C based on K1/K2/K3 flags. A bypass: all 4 flagged, cloud3 not needed. B: K1+K2, requires cloud3_ok. C: K1 only, requires price_pos == +1. Exit uses SL/TP exact prices (not close). Commission: 0.08% taker entry, 0.02% maker exit.

---

## File 2: 2026-02-18-dashboard-v392-build.md

**Date:** 2026-02-18
**Type:** Build log / completed build

**What happened:**
Dashboard v3.9.2 built with Numba acceleration. 5 new files created via build script. 10 patches applied to dashboard_v391.py to create dashboard_v392.py. Three signal functions wrapped with @njit(cache=True): stoch_k, ema, _rma_kernel.

**Decisions recorded:**
- Numba selected for acceleration (not GPU)
- Zero modifications to existing files — all new files only
- Rollback: delete 6 new files to restore v3.9.1 instantly
- Build ran: 10/10 patches, 5/5 files clean. Dashboard v392 confirmed working by user.

**State changes:**
New files: utils/timing.py, signals/stochastics_v2.py, signals/clouds_v2.py, signals/four_pillars_v383_v2.py, scripts/build_dashboard_v392.py, scripts/dashboard_v392.py. Numba compiled on first launch.

**Open items recorded:**
- Numerical parity verification needed: RIVERUSDT 5m run v391 vs v392 — 4 numbers must match exactly

**Notes:**
Performance Debug checkbox added to sidebar. Timing panel shows signals_ms vs engine_ms per coin in portfolio run. Numba kernels: pure numpy, type inference instant, docstrings inside @njit ignored.

---

## File 3: 2026-02-18-vince-ml-build.md

**Date:** 2026-02-18
**Type:** Build log + critical correction

**What happened:**
Session 1: Built 3 build scripts implementing the Vince ML pipeline. Session 2 correction: ENTIRE BUILD WAS MISLABELED. What was built (XGBoost trade classifier, meta-labeling, SHAP, bet sizing) is VICKY's toolset. Vince's actual tool (parameter optimizer) was not built. Additionally, cloud3_allows_long/short filter was added to strategy plugin without user approval.

**Decisions recorded:**
- All files created this session: considered VICKY's pipeline, not Vince's
- Vince ML v1 (XGBoost classifier) = REJECTED, wrong architecture
- 15 discrepancies corrected in what was built vs spec

**State changes:**
Files created (but belong to Vicky): strategies/__init__.py, strategies/base.py, strategies/four_pillars.py, ml/xgboost_trainer_v2.py, ml/features_v3.py, ml/shap_analyzer_v2.py, ml/bet_sizing_v2.py, scripts/train_vince.py, scripts/build_docs_v1.py, scripts/build_data_infra_v1.py, scripts/build_train_vince_v1.py

**Open items recorded:**
- Vince ML v2 scope: needs new architecture (trade research engine, NOT classifier)
- cloud3_allows_long/short filter decision: pending user approval

**Notes:**
Three ML personas confirmed: Vince = rebate farming/parameter optimization. Vicky = copy trading/trade filtering (XGBoost TAKE/SKIP). Andy = FTMO forex. This is the first clear separation of these three personas in the logs.

---

## File 4: 2026-02-18-vince-ml-build-plan.md

**Date:** 2026-02-18
**Type:** Architecture spec / build plan

**What happened:**
Revised Master Build Plan created correcting 15 discrepancies between Sonnet-generated build and three authoritative sources (SPEC-C, BUILD-VINCE-ML, book analyses). Full ML pipeline documented with Section 0 (strategy plugin architecture), A (docs), B (data infra), C (ML bug fixes), D (XGBoost training pipeline), E (Phase 2 book-prescribed enhancements — future only).

**Decisions recorded:**
- Pool split: 60/20/20 (NOT 70/10/20) — Pool A: 240 coins training, Pool B: 80 validation, Pool C: 79 holdout NEVER touched
- XGBoost role: per-coin AUDITOR only (not production). PyTorch = production (Phase 2)
- Per-coin models (one XGBoost per coin)
- Two labeling modes: exit (TP=1/SL=0) and pnl (net>0)
- Grade filtering D+R with threshold sweep 0.3-0.7
- Walk-forward WFE with ROBUST/MARGINAL/OVERFIT rating
- GPU mandatory: device=cuda, tree_method=hist, fail fast (no CPU fallback)
- Strategy plugin architecture approved: models/four_pillars/, models/vicky/, models/andy/ isolated directories

**State changes:**
Build plan approved and ready to execute. Existing 12 ML modules listed as "DO NOT REWRITE."

**Open items recorded:**
- Section E (Phase 2 enhancements): Triple-barrier labeling, Meta-labeling, Sample weights, Feature importance pre-screening, Deflated Sharpe, R-multiples + SQN — all documented but NOT built

**Notes:**
Full 12-step training pipeline defined. StrategyPlugin ABC interface defined with enrich_ohlcv, compute_signals, get_backtester_params, extract_features, get_feature_names, label_trades methods. RTX 3060 full sweep time estimate: 2-4 hours.

---

## File 5: 2026-02-18-vince-scope-session.md

**Date:** 2026-02-18
**Type:** Session log / scope work

**What happened:**
Multi-phase session: (1) identified Vince ML v1 failure — built critic (TAKE/SKIP) when needed assistant (parameter optimizer); (2) launched 3 explore agents; (3) mapped 83 relationship questions; (4) introduced "constellation" concept; (5) user provided two 10-coin portfolio CSVs (77,995 trades 86.0% LSG; 89,633 trades 85.6% LSG); (6) CRITICAL ERROR: I inverted "under 60" to "past 60" — user caught immediately.

**Decisions recorded:**
- Vince ML v2 = trade research engine (PyTorch, GPU), NOT classifier
- Never reduce trade count. Volume preserved.
- RE-ENTRY logic fix deferred until after Vince scope
- Dashboard v3.9.2 build script ready, not yet run by user

**State changes:**
Prevention rules added: (1) NEVER paraphrase directional statements, (2) SCOPE before plan before build, (3) Stochastics = UNIT (never analyze independently), (4) Complete numerical state only

**Open items recorded:**
- Continue Vince ML v2 scoping
- Architecture breakdown
- New UML diagrams for research engine (not classifier)
- Fix scale-out commission bug (user decides priority)

**Notes:**
"Under 60 for long" = K1 < 60 (not yet reached 60, still rising from oversold). User's exact correction documented: "wtf, i said under 60 for long and you make is past 60?" — this triggered the NEVER PARAPHRASE DIRECTIONS hard rule now in MEMORY.md.

---

## File 6: 2026-02-19-engine-audit.md

**Date:** 2026-02-19
**Type:** Engine audit + architecture session

**What happened:**
Two-part session. Part 1: Thorough re-audit of engine with actual CSV verification. PnL math verified by calculation against 3 sample trades. Commission dollar values verified. Exit prices verified (exact SL/TP levels). Part 2: Vince v2 architecture breakdown — 7 modules designed, feature vector size calculated, 5 analysis types identified.

**Decisions recorded:**
- Engine verdict: MECHANICALLY CORRECT, trades are REAL
- Conservative 5-10% net PnL discount recommended for live (slippage + funding)
- vince/ directory chosen (separate from ml/ which is Vicky's v1 code)
- AVWAP/SL option B: enricher runs lightweight AVWAP/SL simulator
- Bar alignment: entry_datetime/exit_datetime (NOT bar indices)
- Scale-out handling: group by (symbol, entry_bar, direction) = one position
- 5 analysis types: parameter sweep, conditional grouping, feature correlation, temporal delta, multi-condition filter

**State changes:**
7 Vince modules designed: schema.py, enricher.py, tensor_store.py, engine.py, validation.py, sampling.py, dashboard_tab.py. Feature vector: 24 static + 44 dynamic = 68 features × 10 moments = 680 per trade. 90K × 680 = ~244 MB float32, fits RTX 3060 12GB.

**Open items recorded:**
- Unified abstraction vs separate functions for 5 analysis types: user didn't decide
- Output format not finalized
- Build order not confirmed
- strategy_document add to get_vince_schema() deferred to next session

**Notes:**
Commission model uses DOLLAR values, not percentages. Standard trade: taker entry $8.0 + maker exit $2.0 = $10.0 total. Scale-out: $8 entry + $1 exit + $1 exit = $10 correct. Context ran out mid-session; user was about to answer dashboard UX question.

---

## File 7: 2026-02-19-vince-scope.md

**Date:** 2026-02-19
**Type:** Session log / scope continuation

**What happened:**
Continued Vince v2 scoping. User's opening question: 10 out of 400 coins not working at all, wants win rate improvement while keeping ALL trades. Session covered: random batch validation math, Cloud 3 discussion ("maybe the hard cloud 3 code should not be there"), constellation query dimensions (full list documented), BBW addition as dimension, scope expansion (Vince runs backtester himself, not passive CSV reader), "shoe salesman" correction. Training log: Claude made 5 unproven claims stated as fact.

**Decisions recorded:**
- Vince runs the backtester himself — 3 operating modes: user query, auto-discovery, settings optimizer
- Learning mechanism: pure statistical frequency (NOT ML weights). Accumulated run history with timestamps IS the learning.
- BBW added as constellation dimension (signals/bbwp.py already built, reuse)
- Two CSV comparison: before/after strategy change, same query on both, delta column
- Fixed constants confirmed: K1/K2/K3/K4 periods and cloud EMAs are FIXED (not swept)
- Dashboard must be interactive (real-time response to filter changes)
- No price charts. Indicator numbers only.
- Master project file: docs/vince/VINCE-PROJECT.md

**State changes:**
Constellation query dimensions fully documented (static, dynamic, trade type, outcome, regime, BBW). 5 panels designed for dashboard. Open items for next session: (1) how does optimizer decide which settings to try, (2) interactive ML UX specifics, (3) module architecture not approved, (4) one-line perspective not confirmed.

**Open items recorded:**
- Grid search vs random vs Bayesian for optimizer: not decided
- Interactive ML UX exact design: not defined
- User confirmed stochastics, cloud EMAs are FIXED instruments

**Notes:**
Training log appended to same file: 5 false claims documented with source traced. User quote: "I am going to build this automation with or without you. It is time to properly train you first." Rule added: before stating anything as fact, cite source or say hypothesis/unknown.

---

## File 8: 2026-02-20-bingx-architecture-session.md

**Date:** 2026-02-20
**Type:** Architecture planning / UML creation

**What happened:**
Architecture session for BingX live deployment. Confirmed strategy v3.8.4. Confirmed BingX API endpoints, auth method, symbol format, rate limits. Created full architecture doc and two UML documents: connector UML and strategy UML.

**Decisions recorded:**
- No code written until: (1) dashboard sweep locks sl_atr_mult/tp_atr_mult/be_raise/grade filter, (2) coin list confirmed (positive expectancy > $1/trade at $500 notional), (3) TP vs runner decision, (4) architecture approved
- Strategy = black-box plugin. Connector calls plugin.get_signal(ohlcv_df) → Signal object.
- Silo testing: each strategy variant is a separate plugin file
- 4 strategy variants planned: v384 baseline, v384 grade-A-only, v385 Cloud4 trail, v386 Vince-filtered

**State changes:**
New docs: BINGX-LIVE-TRADING-ARCHITECTURE.md, docs/BINGX-CONNECTOR-UML.md, docs/FOUR-PILLARS-STRATEGY-UML.md. BingX API details confirmed: HMAC-SHA256, X-BX-APIKEY header, positionSide required (hedge mode), SL/TP as JSON strings, VST demo URL.

**Open items recorded:**
- Which coins pass the sweep?
- Fixed TP or runner (Cloud 4 trail)?
- Grade A only or A+B for live?
- n8n or standalone Python bot?

**Notes:**
Target: $1,000 account, $50 positions. BingX rate limit: 10 orders/second (upgraded Oct 2025). No passphrase needed (unlike WEEX).

---

## File 9: 2026-02-20-bingx-connector-build.md

**Date:** 2026-02-20
**Type:** Build log / completed build

**What happened:**
Full BingX Execution Connector built in one build script generating 25 files. Build script: build_bingx_connector.py. All 25 files generated. Test results progression: first run 3 failures → second run 56/56 → third run 67/67 (including 11 user-added FourPillarsPlugin tests). Screener v1: 22/22.

**Decisions recorded:**
- 6 bug fixes applied: C03 (halt_flag in RiskGate check 1), C04 (halt_flag daily reset), C05 (allowed_grades from plugin), C07 (public endpoints unsigned), C01 (LONG/SHORT/NONE vocab), C02 (mark price from /v2/quote/price)
- Build script re-run: 25/25 files, 0 errors

**State changes:**
25 files created including: bingx_auth.py, notifier.py, state_manager.py, data_fetcher.py, risk_gate.py, executor.py, signal_engine.py, position_monitor.py, main.py, 6 test files, 2 debug scripts, config.yaml, plugins/mock_strategy.py.

**Open items recorded:**
- Deploy to Jacky VPS: scp command ready

**Notes:**
Architecture: 2 daemon threads (MarketLoop, MonitorLoop). Graceful shutdown. Daily halt reset at 17:00 UTC. Config: 3 coins, mock_strategy plugin (demo). Tests: 56 original + 11 FourPillarsPlugin = 67 total.

---

## File 10: 2026-02-20-vince-scope.md

**Date:** 2026-02-20
**Type:** Session log / scope continuation + audit

**What happened:**
Two-part session. Part 1: Concept doc v1 audit — 14 issues identified and logged. Part 2: New architectural direction adding two-layer design with fine-tuned trading LLM. Session ended before concept v2 was written. Session update from 2026-02-23 appended: concept v2 written and all 14 corrections applied.

**Decisions recorded:**
- Plugin interface: strategy plugin provides computational (compute_signals, parameter_space, trade_schema, run_backtest) AND semantic (strategy_document path in markdown) components
- Two-layer architecture: Layer 1 (Quantitative) always available; Layer 2 (Interpretive) via Ollama trading LLM triggered after full sweep
- Trading LLM: fine-tuned domain expert, NOT general model with prompts. Runs locally via Ollama. Candidate: DeepSeek-R1 (reasoning chain visible) or Qwen2.5.
- FULL PATHS EVERYWHERE rule added to MEMORY.md this session
- Concept v2 rewrite prepared but NOT written (session ran out)

**State changes:**
14 concept doc issues documented. Concept v2 written 2026-02-23. Qwen3 response to trading LLM training question saved to docs/TRADING-LLM-QWEN3-RESPONSE.md.

**Open items recorded:**
- Trading LLM scoping: separate session needed (fine-tuning dataset, training, evaluation, Ollama deployment)
- Plugin interface formal spec: blocked by concept v2 approval
- Concept v2 approval: awaiting user review

**Notes:**
14 issues: strategy coupling, hardcoded constants, hardcoded parameter space, hardcoded constellation dimensions, K4 regime buckets hardcoded, win rate as dominant metric bias, autonomy contradiction, backtester coupling, no significance control, hardcoded coin counts, editorial comment, LSG terminology specificity, What Already Exists mixing, dashboard coupling.

---

## File 11: 2026-02-20-youtube-transcript-analyzer-build.md

**Date:** 2026-02-20
**Type:** Build log / completed build

**What happened:**
YouTube transcript analyzer system designed and built. Spec complete in first session. Claude Code build session produced build script generating all modules. Architecture changed during build: dropped DeepSeek, single model qwen3:8b only.

**Decisions recorded:**
- yt-dlp for extraction (no API quota, no cost)
- qwen3:8b single model (DeepSeek dropped — eliminates VRAM contention)
- Confidence: FOUND=yes (include), FOUND=no (discard)
- $0 cost — all inference local via Ollama
- Rate limiting: 4-10s jitter between videos, 60-min HTTP 429 backoff
- archive.txt checkpoint for full resume
- VTT timestamps preserved, YouTube deeplinks generated

**State changes:**
Build script created: PROJECTS/yt-transcript-analyzer/build_yt_transcript_analyzer.py. Generates: config.py, startup.py, fetcher.py, cleaner.py, chunker.py, analyzer.py, reporter.py, main.py, 4 test files. Spec v2 created with audit fixes. Status: BUILD DELIVERED — not yet run by user.

**Open items recorded:**
- User must run build script and pip install
- Audit fixes applied: C1-C5, H1-H6, M1-M6, L1-L4

**Notes:**
Target: 210 videos, structured Obsidian report with timestamped deeplinks. English only. visual reference detection (trigger keywords). Upgrade path noted: multi-language, multi-channel, Claude API fallback, Streamlit UI.

---

## File 12: 2026-02-23-dashboard-v393-bug-fix.md

**Date:** 2026-02-23
**Type:** Bug fix session (in progress, blocked)

**What happened:**
Bug reported: custom date range change in Portfolio Analysis mode shows stale equity curve from previous run. Root cause: session state cache not cleared on settings change — warning shown but old data used. Fix designed (5 changes). Build script created. But indentation script had logic error — dashboard_v393.py has SYNTAX ERROR at line 1972.

**Decisions recorded:**
- Root cause confirmed: line 1963-1964, old portfolio_data not cleared when hash mismatch detected
- Fix: clear session_state["portfolio_data"] on change, set _pd = None, show info not warning
- All rendering code under `if _pd is not None:` guard — must indent lines 1971-2371 by +4 spaces
- st.stop() REJECTED — creates blank page, not suitable
- Smart indentation needed: only indent lines at base indent level 8, skip lines already at 12+

**State changes:**
Files created: scripts/build_dashboard_v393.py (WORKING), scripts/dashboard_v393.py (SYNTAX ERROR), scripts/fix_v393_indentation.py (LOGIC ERROR). Version v3.9.3 not yet functional.

**Open items recorded:**
- Fix indentation script logic
- Full verification: fresh session test, date change test, re-run test, regression test
- Update MEMORY.md and DASHBOARD-FILES.md once working

**Notes:**
Options: (1) fix automated indentation script, (2) user manually indents in IDE, (3) continue using v3.9.2 with workaround. Bug is cosmetic (stale chart display only) — v3.9.2 still functional.

---

## File 13: 2026-02-23-four-pillars-strategy-scoping.md

**Date:** 2026-02-23
**Type:** Strategy scoping / specification work

**What happened:**
Strategy scoping session building FOUR-PILLARS-QUANT-SPEC-v1.md. Key strategy decisions documented, chart reading rules established (chart-reading-skill.md), two-track build plan created (Track A: Cloud 3 fix + BingX demo, Track B: VINCE). 19 spec unknowns remaining after session.

**Decisions recorded:**
- BBW/BBWP and Ripster EMA Clouds: NOT entry or exit triggers — lagging, context only
- No hard lines on stochastic zones — 20/80 are reference points, zones are flexible
- Cloud 3 = EMA 34/50 (confirmed from ripster_ema_clouds_v6.pine)
- K4 K/D cross = late entry/add-on confirmation, NOT primary entry
- Cloud 3 role: post-entry health indicator only, not an entry gate
- Rotation window = 5 candles (working value), Vince to optimize

**State changes:**
New files: PROJECT-BUILD-PLAN-v2.md, docs/FOUR-PILLARS-QUANT-SPEC-v1.md (19 unknowns), skills/chart-reading-skill.md. Signal types documented: (1) Quad Rotation, (2) Add-On/Late Runner, (3) Divergence.

**Open items recorded:**
19 spec unknowns: rotation window, K above D criteria, BBWP thresholds, add-on stop, divergence pivot lookback, divergence entry trigger, K above/below D on divergence, BE trigger, trail distance, Cloud 3 persistent bearish threshold, counter-trend SL, K1 re-enters extreme zone action, max concurrent positions, skip or queue, leverage, min 24h volume, max watchlist, AVWAP anchor rule, add-on sizing.

**Notes:**
Errors this session: (1) called all 4 stochastics oversold when only K1/K2 were, (2) BBWP red zone called from color not numbers (55-57% is mid range), (3) K4 K/D cross called primary entry, (4) imposed hard lines after correction, (5) wrote "short is mirror of long." Session ended without completing scoping.

---

## File 14: 2026-02-23-screener-scope.md

**Date:** 2026-02-23
**Type:** Scope log / product scoping

**What happened:**
Screener concept scoped as solution to BingX connector config.yaml coin selection problem. Outcome: screener v1 (historical backtest ranker) was confirmed as WRONG approach — TradingView already does live scanning better. WEEX live market screener identified as what's actually needed.

**Decisions recorded:**
- Frequency: live continuous filter — runs at bot startup + daily reset
- Criteria: ATR ratio (commission viability) + recent performance (last 30/60 days) + volume/liquidity
- Integration: Vince dashboard — new Screener tab
- Historical all-time PnL: NOT selected — recency matters more
- Platform: WEEX (not BingX) for this screener

**State changes:**
Screener v1 (wrong approach) already built: utils/screener_engine.py, scripts/screener_v1.py, tests/test_screener_engine.py (22/22 pass), bingx-connector/main.py patched. Status: exists but deemed wrong approach.

**Open items recorded:**
- Lookback period: 30 or 60 days TBD
- Connector integration: reads active_coins.json or manual config.yaml update?
- Dashboard version to target

**Notes:**
Short file — screener scope just getting started. WEEX screener v1 scope outlined: 3 files (weex_fetcher.py, weex_screener_engine.py, weex_screener_v1.py). Columns: symbol, price, 24h_change_pct, 24h_vol_usd, vol_change_pct, atr_ratio, stoch_60, stoch_9, cloud3_dir, price_pos, signal_now.

---

## File 15: 2026-02-24-countdown-to-live-session.md

**Date:** 2026-02-24
**Type:** Session log / go-live prep

**What happened:**
Countdown-to-live session. Audit of Step 1 files revealed 5 faults. All 4 fixable faults resolved this session (fault report generated). 67/67 tests passing confirmed. config.yaml updated by user. Bot ready to run.

**Decisions recorded:**
- config.yaml updated: plugin = four_pillars_v384, allow_a/b: true, allow_c: false, sl_atr_mult: 2.0, tp_atr_mult: null
- Test fixes: assertAlmostEqual for float precision, single requests.get patch with 3 sequential responses, deepcopy for DEFAULT_STATE
- Ollama model: qwen3:8b confirmed (already installed, full GPU inference 40-60 tok/s)
- Week plan: Tue=Step1 (demo), Wed-Thu=Step2 (strategy spec + dashboard comparison), Fri=Step3 (go live $1,000/$50)

**State changes:**
COUNTDOWN-TO-LIVE.md created, STEP1-CHECKLIST.md created, fault-report created. 67/67 tests passing. Bot ready: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"`.

**Open items recorded:**
- Run main.py
- Observe: startup log, BingX VST connection, warmup progress (~16h for 200 bars on 5m)
- First A/B signal, Telegram alert, position in BingX VST account

**Notes:**
Step 1 = demo bot running. Step 2 = strategy spec unknowns + Signal Type 2 + dashboard comparison. Step 3 = go live. S08 open risk: backtester multi-slot vs live single-slot P&L not comparable — must resolve before Step 3.

---

## File 16: 2026-02-24-fault-report-step1-build-review.md

**Date:** 2026-02-24
**Type:** Fault report / code review

**What happened:**
Plan-mode read-only audit of all Step 1 files. 5 faults found, priority ordered. Fix order documented with exact line numbers.

**Decisions recorded:**
- F1 (CRITICAL → CLEARED after investigation): four_pillars.py produces correct long_a/b/c, short_a/b/c at lines 64-73 — plugin import is FINE
- F2 (HIGH): config.yaml missing four_pillars block — add explicit block
- F3 (LOW): test_executor.py line 178 assertEqual → assertAlmostEqual
- F4 (LOW): test_integration.py line 106 — add assertIsNotNone before monitor.check()
- F5 (INFORMATIONAL): warmup_bars=200 vs UML spec 89 — conservative, not wrong

**State changes:**
Fault report written to two locations: 06-CLAUDE-LOGS/ and PROJECTS/bingx-connector/docs/FAULT-REPORT-2026-02-24-step1-build-review.md.

**Open items recorded:**
- All 4 fixable faults resolved in countdown-to-live session (same day)

**Notes:**
Critical initial finding: F3 appeared to be CRITICAL (wrong plugin import). Investigation revealed four_pillars.py DOES produce correct signal columns. The "critical" label was downgraded to CLEARED. This is the correct audit approach — investigate before labeling severity.

---

## File 17: 2026-02-24-vince-todo.md

**Date:** 2026-02-24
**Type:** Session handoff / to-do list

**What happened:**
Short handoff file created after PC reboot. Lists 4 Vince items in priority order with file paths.

**Decisions recorded:**
- Concept v2 review and approval is blocker for all downstream Vince work
- Trading LLM scoping is a separate session (parallel track, not blocking Vince)
- Formal plugin interface spec: blocked by concept v2 approval
- Four Pillars plugin spec: blocked by plugin interface spec

**State changes:**
N/A — handoff only, no changes made.

**Open items recorded:**
1. Review and approve VINCE-V2-CONCEPT-v2.md
2. Scope trading LLM (separate session): collect DeepSeek-R1 response, define fine-tuning dataset
3. Formal plugin interface spec
4. Four Pillars plugin spec

**Notes:**
Short file (35 lines). All items point to existing files at full paths.

---

## File 18: 2026-02-24-vince-v2-ml-spec-review.md

**Date:** 2026-02-24
**Type:** Spec review / architectural fixes

**What happened:**
Thorough review of VINCE-V2-CONCEPT.md (v1), VINCE-V2-CONCEPT-v2.md, SPEC-C-VINCE-ML.md, vince-ml skill, and full project tree. 6 recommendations evaluated, 3 confirmed as definitive fixes, 2 marked overstated (dropped), 1 as user decision. 4 concrete changes applied to documents.

**Decisions recorded:**
- Mode 2 permutation gate: ADDED — shuffle trade outcome labels, compute empirical null distribution, only surface patterns above 95th percentile. Prevents false discovery in large constellation search space.
- Mode 3 fitness function: DEFINED explicitly — Calmar ratio with rebate. Hard rejection if trade_count < 0.95 * baseline. No ambiguity at build time.
- K4 regime bucket derivation: ADDED — 5-step pre-build procedure using decision tree on K4 vs outcome to find empirical split points.
- Tab 3 relabeled: "Research findings panel — informational only. No trade rejected by Vince. Trade count never reduced. TAKE/SKIP is Vicky's domain."
- Items 4 (55% accuracy gate) and 5 (LSTM suboptimal): DROPPED — overstated concerns.

**State changes:**
Two files modified: docs/VINCE-V2-CONCEPT-v2.md (3 sections updated), SPEC-C-VINCE-ML.md (Tab 3 relabeled). Overall spec assessment: on the right track, no structural redesign needed.

**Open items recorded:**
- User decision: SPEC-C vs VINCE-V2 classifier conflict on Tab 3 — RESOLVED (informational only)

**Notes:**
8 items already confirmed correct (always show N, complement alongside, trade count floor, two-sided Monte Carlo, ETD tracking, strategy-agnostic plugin, XGBoost as adversarial auditor, 60/20/20 split with holdout). Assessment: gaps were missing permutation correction, missing explicit fitness function, architectural contradiction (resolved), and regime buckets without derivation method.

---

## File 19: 2026-02-24-weex-screener-scope.md

**Date:** 2026-02-24
**Type:** Scope log / screener pivot

**What happened:**
Session that built Screener v1 (historical backtest ranker, 22/22 tests) then determined it was the wrong approach. Scoped WEEX Live Market Screener as the correct tool: live indicator state for all WEEX futures, not a backtester.

**Decisions recorded:**
- Screener v1 (historical PnL ranker): WRONG — backwards-looking, dominated by regime noise, TradingView does this better
- WEEX Live Market Screener: correct approach — normalised ATR ratio, Four Pillars signal state, setup detection
- WEEX API confirmed: no auth for market data, 500 req/10s rate limit
- Symbol format: contracts = cmt_btcusdt, OHLCV = BTCUSDT_SPBL (append _SPBL)
- Import confirmed: compute_signals_v383 from signals.four_pillars_v383_v2, minimum bars = 69 (60 for K4 + 9 for D smooth)

**State changes:**
Screener v1 exists but wrong approach. WEEX screener v1 scoped: 3 files planned. Columns defined. Filters defined. Sidebar controls defined.

**Open items recorded:**
- Confirm futures candles endpoint vs spot candles endpoint at build time
- Next session: scope first, then build

**Notes:**
Three key WEEX screener metrics not available on TradingView: (1) Normalised ATR ratio (ATR/price) for cross-coin comparison, (2) Four Pillars signal state (all 4 stoch values + cloud state), (3) Setup detection (coin in pullback with signals ready).

---

## File 20: 2026-02-25-bingx-connector-session.md

**Date:** 2026-02-25
**Type:** Session log / live bot debugging

**What happened:**
Multi-session log (5 sessions). Bot launched, encountered blocking bugs, fixed progressively. Critical finding: E1-ROOT (urlencode in bingx_auth.py line 31) was the #1 blocker — ALL order attempts had been failing with signature verification error because urlencode encoded JSON special chars while BingX computes signature on raw string.

**Decisions recorded:**
- Fix SB1: leverage API loop over LONG/SHORT (not BOTH — BingX hedge mode)
- Fix SB2: ohlcv_buffer_bars 200→201 (off-by-one, signals could NEVER fire — 200 >= 201 always False)
- Fix A1: recvWindow added to auth (5s default → timestamp errors every ~5h)
- Fix E1: json.dumps separators=(',',':') in executor.py
- Fix E1-ROOT: bingx_auth.py line 31 — urlencode replaced with manual &-join (no encoding of JSON chars)
- Fix M1: reconcile API error check (no silent wipe on error)
- Fix M2: absolute log path to logs/YYYY-MM-DD-bot.log
- UTC+4 fix: custom UTC4Formatter, Telegram timestamps UTC+4
- Data integrity timestamps (entry_time, session/trade timestamps, daily reset check): KEPT in UTC

**State changes:**
Bot running on BingX VST demo in hedge mode. 67/67 tests passing. 3 open risks remain: S01/S02 (cold-start false signal guard), S08 (multi-slot vs single-slot PnL not comparable — must fix before Step 3 go-live), E2/F1/D1 (deferred low severity). Bot confirmed running: warmup 201 bars all 3 coins, Telegram startup alert sent, first bar evaluated (No signal).

**Open items recorded:**
- Next signal to confirm E1-ROOT fix end-to-end
- Add 37 more coins to config.yaml (wider signal net)
- Increase max_positions if needed
- Switch back to 5m once trade confirmed
- Step 1 complete once first A/B demo trade placed

**Notes:**
E1-ROOT explanation: simple params (leverage, margin, positions) have no special chars — urlencode doesn't change them, those calls always worked. Order call includes stopLoss JSON with special chars — urlencode encodes {, ", :, , — signatures never matched. This explains why startup worked but every order attempt failed.

---

*End of batch ordered-07. 20 files processed.*


# Research Batch 08 — Findings
**Files processed:** 20
**Date range covered:** 2026-02-25 to 2026-02-28

---

## 2026-02-25-lifecycle-test-session.md
**Date:** 2026-02-25
**Type:** Build session / Bug fix

### What happened
Built a 15-step API lifecycle test script (`test_api_lifecycle.py`) to exercise the full BingX trade lifecycle against the VST demo in ~40 seconds without waiting for real signals. Steps covered: auth, public endpoints, leverage/margin, qty calc, LONG entry + SL + TP, verify, query pending orders, raise SL, trail TP, close, verify, SHORT cycle, multi-position, limit order, order query.

During step 5, discovered bug E2-STOPPRICE: `str(signal.sl_price)` was wrapping stopPrice in string form inside `json.dumps()`, producing `"stopPrice":"8.4546"` instead of float `"stopPrice":8.4546`. BingX error 109400. Fixed by removing the `str()` wrapper in executor.py lines 157 and 164. py_compile passed on both files.

Session 2 (afternoon same day): Fixed hedge mode detection in lifecycle test steps 11/12/13 (using `positionSide` instead of `positionAmt > 0`), added step 0 cleanup for stale positions, changed runner to continue on failure. Final result: **15/15 PASS in 22.3 seconds**.

Bot deployed to BingX VST demo with 47 coins (53 initial minus 6 not on BingX perps). Config changes: `tp_atr_mult: 4.0` (was null), `poll_interval_sec: 45`, `max_positions: 25`, `max_daily_trades: 200`. Added 200ms throttle between leverage/margin API calls at startup. Connection pooling added to data_fetcher.py.

Three critical bug fixes applied: hedge mode direction detection (positionSide field), exit detection (queries open orders — SL pending = TP hit, TP pending = SL hit, cancels orphaned order), commission (changed from `notional * 0.0008 * 2` to `notional * 0.001`, i.e. 0.10% blended for 0.08% taker entry + 0.02% maker exit).

Test fix: mock target changed from `data_fetcher.requests.get` to `data_fetcher.requests.Session.get` due to connection pooling. 67/67 tests passing.

### Decisions recorded
- tp_atr_mult set to 4.0 (was null, meaning no TP on any trade)
- Commission blended rate: 0.10% (0.08% taker entry + 0.02% maker exit)
- 47 coins deployed to VST demo
- Lifecycle test covers all 15 steps before calling the bot validated

### State changes
- `test_api_lifecycle.py` — NEW, lifecycle test (hedge mode fixes added)
- `executor.py` — stopPrice str() fix (lines 157, 164)
- `position_monitor.py` — hedge mode, exit detection, commission, orphan cancel
- `state_manager.py` — hedge mode in reconcile()
- `data_fetcher.py` — connection pooling via requests.Session()
- `main.py` — log level INFO, startup throttle, urllib3 silence
- `config.yaml` — 47 coins, tp_atr_mult=4.0, poll=45s
- `tests/test_data_fetcher.py` — Session.get mock fix
- `build_bingx_connector.py` — stopPrice str() removed
- `docs/BINGX-API-V3-REFERENCE.md` — NEW (API reference)

### Open items recorded
1. Run lifecycle test and pass all 15 steps (done in session 2)
2. Add 37 more coins (list from user — not yet done)
3. Cross-reference all bot API calls against BingX v3 docs
4. Cache contract step sizes in executor
5. Connection pooling for executor + position_monitor (only data_fetcher has it)
6. Poll cycle drift compensation
7. Skip leverage/margin setup on restart if already set
8. build_bingx_connector.py lines 954/961 still had old str(stopPrice) bug (noted, not critical)

### Notes
Bug table shows cumulative all bugs found across sessions: E1-ROOT, E2-STOPPRICE, A1, M1, M2, TZ1, SB1, SB2 — all marked FIXED. Bot status at end: running on VST with 47 coins, warmup in progress (~3.3h for 201 bars at 1m).

---

## 2026-02-25-telegram-connection-session.md
**Date:** 2026-02-25
**Type:** Build session / Setup

### What happened
Telegram bot connection setup for the BingX connector. TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID were placeholder values. Session walked through creating a bot via @BotFather, explained the correct URL format (token not username), and created `test_telegram.py` — a diagnostic script that calls `getUpdates` to retrieve Chat ID automatically, sends a test message, and prints the exact `.env` line to copy-paste. User populated both `.env` values. Chat ID confirmed: 972431177.

### Decisions recorded
- Use getUpdates API method to retrieve Chat ID automatically
- .env approach (python-dotenv) confirmed as correct pattern

### State changes
- `.env` — TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID filled in
- `test_telegram.py` — NEW diagnostic script

### Open items recorded
- Run `python main.py` and wait for first demo signal to fire to confirm Telegram alert checklist item

### Notes
Log references a follow-up file: `2026-02-25-test-telegram-github-note.md` for GitHub release candidate discussion.

---

## 2026-02-25-test-telegram-github-note.md
**Date:** 2026-02-25
**Type:** Planning / Note

### What happened
Note documenting that `test_telegram.py` (created in Telegram connection session) is a generic utility worth publishing publicly. The script automates the three most common Telegram bot setup pain points: getting the Chat ID, verifying the token, and printing the exact `.env` line. Three publication options evaluated: Option A (add to bingx-connector repo), Option B (GitHub gist), Option C (standalone public repo). Option B (gist) chosen. A clean version stripped of BingX-specific references was prepared at `06-CLAUDE-LOGS/telegram_connection_test.py`.

### Decisions recorded
- Option B (GitHub gist) chosen for publication
- Strip BingX-specific references from the clean version before publishing

### State changes
- `06-CLAUDE-LOGS/telegram_connection_test.py` — clean version written (BingX refs removed)

### Open items recorded
- TODO (unchecked): Publish gist — go to gist.github.com, paste `telegram_connection_test.py`, set Public, save URL in this file

### Notes
None.

---

## 2026-02-26-bingx-audit-session.md
**Date:** 2026-02-26
**Type:** Audit / Build session

### What happened
Context refresh session continuing from previous. Built master audit script `scripts/audit_bot.py` covering 4 audits: trades analysis, docstring coverage, commission flow, strategy comparison. Output teed to console and `logs/YYYY-MM-DD-audit-report.txt`.

Audit results from 103 trades on 1m demo: all exits were EXIT_UNKNOWN or SL_HIT_ASSUMED (all using SL price as exit estimate = always a loss, actual P&L unknown). Docstrings: 235 functions, 0 missing. Commission: rate 0.0012 (correct for 0.06% taker × 2). Strategy: plugin imports compute_signals from backtester (identical logic). Cooldown (3 bars) missing from bot but only genuine gap vs backtester. AVWAP confirmed not in compute_signals — TradingView visualization only (false alarm).

Audit script fixes: deprecated `datetime.utcnow()` to `datetime.now(timezone.utc)`, volume label split into notional vs trading volume, commission double-counting check fixed to exclude build/audit/test scripts.

Previous session changes carried over (applied before this session): config 5m timeframe $75 margin 20x leverage, commission 0.001→0.0012, EXIT_UNKNOWN fix (_fetch_filled_exit queries allOrders), daily reset on startup, retry with backoff, order validation, graceful shutdown 15s, hourly metrics logging, 67/67 tests.

### Decisions recorded
- Commission rate: 0.0012 (0.06% taker RT) confirmed correct for BingX at the time
- Cooldown (3 bars) is the only real gap between bot and backtester
- 5m demo run started; need 24h results before live transition

### State changes
- `scripts/audit_bot.py` — NEW, master audit script
- Multiple files updated in prior session: config, data_fetcher, position_monitor, main.py

### Open items recorded
1. Start 5m demo run
2. After 24h: run audit script, should show TP_HIT/SL_HIT instead of EXIT_UNKNOWN
3. Add cooldown (3 bars same-symbol re-entry delay) to signal_engine.py or risk_gate.py
4. Build reconciliation script for 103 1m trades (query BingX allOrders for actual P&L)
5. Per-trade commission tracking for live (entry_commission + exit_commission in position_record)

### Notes
Countdown to Live status: Step 1 COMPLETE, Step 2 IN PROGRESS, Step 3 WAITING. Note: commission rate here is 0.0012 (0.06% taker × 2 = 0.12% RT). Later session (2026-02-28-bingx-be-fix.md) confirms live commission_rate = 0.001 (0.05% per side). There is a discrepancy in rates across sessions.

---

## 2026-02-26-vault-vps-migration-session.md
**Date:** 2026-02-26
**Type:** Build session / Infrastructure

### What happened
VPS migration planning and script build. Audited VPS specs (Jacky: 4 cores, 16GB RAM, 190GB free, Ubuntu 24.04, IP 76.13.20.191). Decision: one flat git repo (backtester .git removed), manual push-when-ready, no cron. User created GitHub repo: S23Web3/Vault (private).

Three scripts built to `C:\Users\User\Documents\Obsidian Vault\scripts\`:

1. `migrate_pc.ps1` — one-time PC migration: prerequisite check, removes nested .git folders, creates .gitignore (excludes 33GB data/secrets/artifacts), creates .gitattributes (LF for sh/py/yaml, CRLF for ps1), stages, safety-checks for secrets/data leaks, pauses for review, commits, pushes. Re-run safe.

2. `setup_vps.sh` — one-time VPS setup: SSH key generation, clones vault to /root/vault, installs Python 3.12 + venv + requirements, prompts for manual .env creation (validates 4 required keys), import test on all bot modules (NOT import main), creates systemd service (auto-restart, boot-start), starts bot, verifies active status.

3. `deploy.ps1` — ongoing workflow: -Message push only, -Sync push+pull (no restart), -Restart push+pull+restart (warns about 16.7h warmup), -Status, -Logs, -Rollback. Safety check on every push.

Two audit rounds performed improving both quality and production-readiness (split Sync vs Restart, re-run safety, smart skip, rollback, SSH failure recovery, git conflict recovery, timestamps, CRLF self-fix).

### Decisions recorded
- Flat repo structure (nested .git folders removed)
- Manual push-when-ready (no cron)
- -Sync vs -Restart split to protect 16.7h warmup cost
- VPS: Ubuntu 24.04, IP 76.13.20.191, /root/vault

### State changes
- `scripts/migrate_pc.ps1` — NEW (300 lines)
- `scripts/setup_vps.sh` — NEW (365 lines)
- `scripts/deploy.ps1` — NEW (138 lines)
- `06-CLAUDE-LOGS/plans/2026-02-26-vault-vps-migration.md` — NEW (plan doc)

### Open items recorded
1. Run `.\scripts\migrate_pc.ps1` from PowerShell
2. SCP setup_vps.sh to VPS and run it
3. Use deploy.ps1 for ongoing workflow

### Notes
None.

---

## 2026-02-26-vps-migration-part-a-violation.md
**Date:** 2026-02-26
**Type:** Rule violation log

### What happened
During Part A of VPS migration (running migrate_pc.ps1), script hit issues: nul files blocking git add, nested .git in book-extraction, CSV files in staging, PowerShell git add not staging files. Fixed nul files, nested .git, updated .gitignore. Then Claude violated the NEVER EXECUTE ON USER'S BEHALF rule by running `git add`, `git commit`, and `git push` directly via Bash tool when user had explicitly stated they wanted to run everything themselves to learn the process. User was rightfully angry. Part A completed despite the violation: 1017 files committed (hash: 1e1c49b), pushed to S23Web3/Vault main.

### Decisions recorded
- Rule reaffirmed: NO BASH EXECUTION / NEVER EXECUTE ON USER'S BEHALF
- .gitignore updated: *.csv, *.env, tmpclaude-*, .aider*, dist/, build/, *.egg, *.joblib, nul

### State changes
- .gitignore — updated
- nul files removed from vault root and backtester
- book-extraction/.git removed
- Vault pushed: 1017 files, commit 1e1c49b to S23Web3/Vault main

### Open items recorded
- Part B: Upload setup_vps.sh to VPS and run it
- Part C: Use deploy.ps1 for ongoing workflow

### Notes
This is a documented rule violation. The log explicitly records: rule broken, what was done, impact (user lost the experience of their first vault push to GitHub). The violation was "NEVER EXECUTE ON USER'S BEHALF" — git add/commit/push executed without permission. First commit can only happen once, not recoverable.

---

## 2026-02-26-yt-analyzer-gui-session.md
**Date:** 2026-02-26
**Type:** Build session

### What happened
Built and iteratively improved the Streamlit GUI for the YT Transcript Analyzer. Starting from a working CLI pipeline, ended with a full-featured GUI with real-time progress, system status checks, and two operating modes.

Initial GUI built (`gui.py`) wrapping existing pipeline: fetcher -> cleaner -> chunker -> analyzer -> reporter. Sidebar shows Ollama status, data counts, config.

Resolved yt-dlp not installed (WinError 2), installed via pip. Then discovered ffmpeg and deno were needed — explained pip wrappers vs actual system binaries. Correct installs: `winget install Gyan.FFmpeg` and `winget install DenoLand.Deno`. Teaching moment logged.

Made query field optional — added drain mode (full channel without LLM, 3 stages: Fetch->Clean->Report) vs query mode (5 stages with Ollama). Added `generate_full_report()` to reporter.py.

Real-time progress overhaul: `subprocess.run()` was blocking with no GUI updates. Fix: split `fetch_subtitles()` into `prescan_channel()` + `download_subtitles()` using `subprocess.Popen` with line-by-line stdout parsing and `on_progress` callback. GUI rewritten with stage counter, detail line, per-video progress bar.

Added sidebar system status: yt-dlp (required), ffmpeg and deno (optional), each with green/red status and install command if missing. Ollama section separated.

Also: cleaned up Vince ML docs from previous context (TOPIC-vince-v2.md, SPEC-C-VINCE-ML.md marked SUPERSEDED, BUILD-VINCE-ML.md ARCHIVED, PRODUCT-BACKLOG P1.2 set SUPERSEDED).

### Decisions recorded
- Query field is optional; drain mode works without query
- Drain mode skips Ollama entirely (3 stages)
- subprocess.Popen used instead of subprocess.run for real-time progress
- Always explain what you're about to do and why before doing it (user lesson logged)

### State changes
- `PROJECTS/yt-transcript-analyzer/gui.py` — CREATED then heavily modified
- `PROJECTS/yt-transcript-analyzer/fetcher.py` — added download_subtitles() with Popen + callback
- `PROJECTS/yt-transcript-analyzer/reporter.py` — added generate_full_report() for drain mode
- `PROJECTS/yt-transcript-analyzer/requirements.txt` — added streamlit
- yt-dlp, ffmpeg, deno installed as system dependencies

### Open items recorded
None stated.

### Notes
Vince ML cleanup at start of session: TOPIC-vince-v2.md corrected ("APPROVED" -> "NOT YET APPROVED FOR BUILD"), SPEC-C-VINCE-ML.md SUPERSEDED, BUILD-VINCE-ML.md ARCHIVED. This contradicts or clarifies prior session where these might have been marked differently.

---

## 2026-02-27-bingx-api-docs-scraper-session.md
**Date:** 2026-02-27
**Type:** Build session

### What happened
Built a Python scraper using async Playwright to render the BingX API docs SPA (JavaScript-rendered, not plain HTML). Scraper expands all Element UI navigation, clicks through all ~215 leaf pages, extracts structured content (method, path, params, response, examples, error codes, Python demos), and compiles to a single indexed markdown reference document.

Three rounds of debugging to get extraction working:
- Round 1: Page type detection always returned "info" because `_detect_page_type()` checked for `"GET /"` but BingX puts method and path on separate lines (`GET\n/openApi/...`). All pages classified as info, _parse_rest_endpoint never called.
- Round 2: Fixed standalone method detection and /OPENAPI/ fallback — still 0 extraction because user was running a cached older version.
- Round 3: Discovered BingX DOM renders each table section as TWO elements: a 1-row header table + separate data table. Added `_merge_paired_tables()`. Also fixed BingX typos: `"filed"` not `"field"`, `"msg"` not `"message"`. Added scroll-into-view for hidden menu items. Final test output: 3/3 pages, structured content extracted.

All project rules followed: docstrings on all functions, py_compile pass, timestamps, no escaped f-string quotes, absolute paths, logs/ directory creation.

Test (`scripts/test_scraper.py`): 4 pytest tests — nav tree count, single page extraction, markdown compilation, full section scrape.

### Decisions recorded
- Use Playwright (not requests/BeautifulSoup) — required for JS-rendered SPA
- `_merge_paired_tables()` approach for BingX paired table DOM structure
- Text-based selectors instead of cached DOM indices (stale DOM prevention)
- Progress saved every 20 pages to `docs/.scrape-progress.json`

### State changes
- `scripts/scrape_bingx_docs.py` — NEW (async Playwright scraper, 2 classes)
- `scripts/test_scraper.py` — NEW (4 pytest tests)
- Both files: py_compile PASS

### Open items recorded
- Full scrape ready to run: `python scripts/scrape_bingx_docs.py --debug` (~7-10 min for 224 pages)
- Output `docs/BINGX-API-V3-COMPLETE-REFERENCE.md` generated at runtime

### Notes
Plan file: `06-CLAUDE-LOGS/plans/2026-02-27-bingx-api-docs-scraper.md`. Dependencies: `pip install playwright && playwright install chromium`.

---

## 2026-02-27-bingx-automation-build.md
**Date:** 2026-02-27
**Type:** Build session

### What happened
Built two headless automation tools for the BingX connector:

1. `screener/bingx_screener.py` — live signal screener: polls all 47 coins on 60s interval, reuses FourPillarsV384 plugin directly, fetches live BingX public klines (no auth), calls `plugin.get_signal(df)`, deduplicates by `last_alerted = {symbol: bar_ts}`, sends Telegram alerts for A/B grades only (grade, direction, ATR ratio, entry/SL/TP format). Logs to `logs/YYYY-MM-DD-screener.log`. py_compile PASS.

2. `scripts/daily_report.py` — daily P&L report: one-shot, reads trades.csv, filters to today UTC, computes total_pnl, n_trades, win_rate, best/worst trade. Sends Telegram HTML digest. Designed for Task Scheduler daily at 21:00 local (17:00 UTC). py_compile PASS.

Also confirmed: BingX API docs scraper ran and produced `BINGX-API-V3-COMPLETE-REFERENCE.md` (16KB, ~215 endpoints). Vault status files updated (LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md, TOPIC-bingx-connector.md).

Session 2 (same date): Expanded `docs/TRADE-UML-ALL-SCENARIOS.md` with 4 new sections documenting BingX order status states (6 statuses mapped to exit detection code paths), full data flow map (all API endpoints, local files, compute path), extended scenarios (breakeven raise, raised SL, trailing TP — PLANNED, NOT YET BUILT), and cancel+replace API pattern with failure guards.

Rule violation logged: used relative paths in final response instead of full Windows paths. FULL PATHS EVERYWHERE rule violated.

### Decisions recorded
- Screener reuses FourPillarsV384 plugin directly (no signal code duplication)
- Live API used for screener (VST has corrupted data — public klines always from live)
- Notifier imported from notifier.py (same Telegram pattern as bot)
- Task Scheduler command documented for daily report at 17:00 UTC

### State changes
- `screener/bingx_screener.py` — NEW
- `scripts/daily_report.py` — NEW
- `docs/TRADE-UML-ALL-SCENARIOS.md` — 4 new sections added
- `docs/BINGX-API-V3-COMPLETE-REFERENCE.md` — generated by scraper run

### Open items recorded
- Breakeven raise, raised SL, trailing TP documented in UML section 13 as PLANNED, NOT YET BUILT
- Cancel+replace failure guard: if POST fails after DELETE = no stop order = dangerous, notifier alert required

### Notes
Hard rule violation logged: relative paths used in final response. UML section 13 (extended scenarios) are explicitly marked as planned and not yet built.

---

## 2026-02-27-bingx-trade-analysis.md
**Date:** 2026-02-27
**Type:** Analysis / Session log

### What happened
Post-mortem analysis of the 5m demo run (~18h, 47 coins). Bot had 31 closed trades and 10 open positions. Daily PnL: -$379.93.

Key exit analysis:
- TP_HIT: 4 trades (CYBER, BEAT, LYN, SUSHI — all profitable)
- SL_HIT: 18 trades
- SL_HIT_ASSUMED: 3 trades (GUN, DEEP, F — detection failed)
- EXIT_UNKNOWN: 2 trades (RIVER, SKR — down from ~100% on 1m run)

Signal quality issue traced: APT SHORT A fired at 18:40 UTC+4 when Stoch40 was at 98 going UP, Stoch60 at 99 going UP. No rotation visible. Root cause: state machine only checks "was Stoch40 ever > 70 during Stage 1?" — trivially satisfied at 98. Does not check if Stoch40/60 are actively rotating downward. A Grade B LONG fired at 19:20 after the big move already ran — confirming Grade B fires late (chasing entries).

EXIT_UNKNOWN root cause: both SL and TP orders cleaned up by BingX before 60s monitor poll. VST purges filled order history within seconds.

RIVER SHORT -$70.11: entry signal at 10.738, mark at execution 10.576 (1.5% gap). SL set at 11.058 based on signal price, making effective SL distance 4.56% from fill. Huge amplified loss from mark/signal price divergence.

API rejections: AIXBT-USDT and VIRTUAL-USDT rejected with error 101209 "max position value for this leverage is 1000 USDT". BingX VST API oddities documented (7 items including filled orders vanishing within seconds, STOP orders filling in wrong direction, per-coin limits undocumented).

User decision at session end: stop optimizing the demo bot. VST data is too corrupted to draw strategy conclusions. Move on to Vince ML.

### Decisions recorded
- Stop optimizing demo bot — VST data too corrupted for strategy conclusions
- Stage 2 filter proposed (Stoch40 AND Stoch60 must cross below 80/above 20 before signal fires) — pending backtester validation
- 4x ATR TP confirmed set (user didn't recall setting it — was added 2026-02-26)

### State changes
- Files read, no code written this session

### Open items recorded
- Stage 2 filter build pending (confirm definition with user, backtester validation required)
- Stale 1m positions: RENDER_LONG, BREV_SHORT, SUSHI_SHORT blocking re-entry (3 stale positions)
- Breakeven raise and trailing TP confirmed not in production code

### Notes
1m vs 5m confusion documented: earlier ATR filter analysis was based on 1m chart data. Decision to park VST demo work and move to Vince ML is a significant project pivot point.

---

## 2026-02-27-bingx-ws-and-breakeven.md
**Date:** 2026-02-27
**Type:** Build session

### What happened
Bot went live on $110 real account. 4 SHORT positions open (BEAT, ELSA, VIRTUAL, PENDLE). WS listener was broken. Breakeven raise not yet built.

Five fixes applied:

1. Stage 2 Filter Bug: `require_stage2` and `rot_level` were missing from `self._params` dict in `four_pillars_v384.py`. Stage 2 was silently disabled despite `config.yaml` having `require_stage2: true`. Added both keys.

2. Breakeven Raise: Trigger 0.16% profit (= 2x commission RT). Sequence: cancel open SL → place STOP_MARKET at entry_price → update state (sl_price + be_raised=True). Persisted in state.json. Telegram alert added. New methods: `_fetch_mark_price_pm`, `_cancel_open_sl_orders`, `_place_be_sl`, `check_breakeven` in position_monitor.py. `update_position(key, updates)` in StateManager. `monitor.check_breakeven()` wired into monitor_loop in main.py.

3. WS listenKey parsing: BingX returns `{"listenKey": "..."}` at top level — code was looking at `data["data"]["listenKey"]`. Added `key = data.get("listenKey", "")` as fallback.

4. listenKey method: API docs say GET, actual BingX returns 100400 "use POST" with GET. Changed to POST.

5. Gzip decompression: BingX sends binary WebSocket frames compressed with gzip (0x1f 0x8b). Added `import gzip` + decompress before JSON parsing.

6. Ping/Pong heartbeat: BingX sends text "Ping" every 5 seconds expecting "Pong". After 5 unanswered Pings, connection closed. Added `if msg == "Ping": await ws.send("Pong"); continue`.

Live confirmation: ELSA-USDT_SHORT and VIRTUAL-USDT_SHORT both triggered BE at 19:17. One position closed at breakeven SL. Final state: 2 open, WS stable.

API audit: all major endpoints confirmed with correct methods and response paths.

### Decisions recorded
- BE trigger: 0.16% = 2x commission RT (LONG: mark >= entry×1.0016, SHORT: mark <= entry×0.9984)
- STOP_MARKET used for BE stop (not STOP_LIMIT — guarantee of execution more important than exact fill)
- listenKey method confirmed POST (not GET as docs say)

### State changes
- `plugins/four_pillars_v384.py` — added require_stage2 + rot_level to _params
- `state_manager.py` — added update_position(key, updates)
- `position_monitor.py` — BE constants + 4 BE methods + check_breakeven()
- `main.py` — check_breakeven() wired to monitor_loop
- `ws_listener.py` — listenKey parsing, gzip, Ping/Pong fixes
- All files: py_compile PASS

### Open items recorded
- Next session: Vince ML strategy validation and build

### Notes
BE stop placed at entry_price (not commission-adjusted). This is later corrected in 2026-02-28-bingx-be-fix.md — the 2026-02-28 session shows BE exits always recorded losses because stop was at exactly entry, not entry ± commission. This session's BE implementation has a bug that is not yet known at this point.

---

## 2026-02-27-dash-skill-creation.md
**Date:** 2026-02-27
**Type:** Build session / Infrastructure

### What happened
Created a comprehensive Plotly Dash skill file (`C:\Users\User\.claude\skills\dash\SKILL.md`, 1,040+ lines) for upcoming Vince v2 8-panel dashboard build. The skill is structured in two parts: Part 1 covers architecture and perspective (Streamlit vs Dash comparison, callback graph mental model, app structure decision tree, Vince store hierarchy with 5 stores). Part 2 covers technical reference for every pattern needed in the build (15 sections including pattern-matching callbacks MATCH/ALL for constellation builder, dcc.Store, background callbacks, ag-grid, ML serving, PostgreSQL, production config, known bugs table).

Issues encountered and fixed: Write tool rejected twice (user on another screen, accidental deny), Edit without reading MEMORY.md (standard protocol fix), YAML frontmatter multi-line block not supported (collapsed to single-line quoted string), ctx inconsistency (standardized to `from dash import ctx`), `vince/panels/` → `vince/pages/` typo, `suppress_callback_exceptions=True` missing (critical for multi-page apps, added).

Dual guarantee system implemented: CLAUDE.md (project instruction, always loaded) + MEMORY.md (memory, always loaded) both have DASH SKILL MANDATORY rule. Skill's YAML description handles keyword matching as third layer.

### Decisions recorded
- Dash 4.0.0 (not Streamlit) confirmed for Vince v2
- `vince/pages/` convention (Dash native `dash.register_page()` with `use_pages=True`)
- `suppress_callback_exceptions=True` is REQUIRED for multi-page apps (would crash without it)
- Dual enforcement: CLAUDE.md + MEMORY.md both carry the DASH SKILL MANDATORY rule

### State changes
- `C:\Users\User\.claude\skills\dash\SKILL.md` — CREATED (1,040+ lines)
- `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` — EDITED (DASH SKILL MANDATORY rule added)
- `memory/MEMORY.md` — EDITED (DASH SKILL MANDATORY rule added)
- `C:\Users\User\.claude\plans\twinkly-wibbling-puzzle.md` — CREATED (system plan)
- `06-CLAUDE-LOGS/plans/2026-02-27-dash-vince-skill-creation.md` — CREATED (vault plan copy)

### Open items recorded
None stated.

### Notes
Skill version: Dash 4.0.0 (2026-02-03), dash-ag-grid 33.3.3. Known bugs table documents 6 Dash 4.0.0 issues.

---

## 2026-02-27-project-overview-session.md
**Date:** 2026-02-27
**Type:** Planning / Documentation

### What happened
End-of-day session creating a cross-project overview map. Explored all 2026-02-27 session logs, plan files, and 27 existing UML files (all intra-project, none cross-project). Created `PROJECT-OVERVIEW.md` at vault root containing: Mermaid inter-project flow diagram (4 projects + infrastructure), status snapshot tables per project (Four Pillars, Vince ML, BingX, YT Analyzer, Infrastructure), active blockers list (3 items), next actions (P0+P1), today's output summary (6 sessions), key docs quick reference (8 files).

Reformatted output for readability: multiple narrow per-project tables, proper `###` headings, fixed table separators, reset list numbering per section.

Today's full output (2026-02-27) across all sessions: BingX API Scraper (Playwright scraper + 215-endpoint reference), Trade Analysis (31-trade post-mortem, VST parking), YT Analyzer v2 (timestamps/LLM summaries/clickable links/TOC), YT Analyzer v2.1 UX (cancel/live log/resume/ETA/settings), BingX Automation (screener + daily report), Vince ML (concept locked, plugin spec, base_v2.py stub, RL exit finding), Project Overview (this document).

### Decisions recorded
None explicitly stated beyond document formatting choices.

### State changes
- `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md` — CREATED
- `06-CLAUDE-LOGS/plans/2026-02-27-project-overview-diagram.md` — CREATED (plan copy)
- `06-CLAUDE-LOGS/INDEX.md` — APPENDED (plan row)

### Open items recorded
3 active blockers listed (not specified in detail in this log).

### Notes
None.

---

## 2026-02-27-vince-concept-doc-update-and-plugin-spec.md
**Date:** 2026-02-27
**Type:** Build session / Documentation

### What happened
Applied ML findings from the 202-video YT channel analysis to `VINCE-V2-CONCEPT-v2.md` (10 edits). Status remained NOT YET APPROVED FOR BUILD. Changes included: panel 2 priority + RL component + random sampling + expanded RL action space (changelog 15-18), Mode 2 Auto-Discovery (XGBoost feature importance pre-step, k-means clustering, 80/20 partition, random sampling, reflexivity caution), Mode 3 Settings Optimizer (walk-forward rolling window, random sampling per Optuna trial), new RL Exit Policy Optimizer section (action space HOLD/EXIT/RAISE_SL/SET_BE, state vector, training methodology), process flow and stage 4 dashboard mermaid updates, survivorship bias + reflexivity constraints, RL open question added, base_v2.py reference updated.

Created `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — 7-section formal spec: purpose, StrategyPlugin ABC with type signatures, method contracts (3a-3e), OHLCV DataFrame contract, Enricher contract (naming convention, snapshot columns, OHLC tuples), compliance checklist (18 items), FourPillarsPlugin compliance mapping with key issue on bar index alignment.

Created `strategies/base_v2.py` — Python StrategyPlugin ABC stub with 5 abstract methods + 1 property, full docstrings. py_compile PASS. base.py kept as archive.

Coherence review: cross-checked all 3 documents, found and fixed 5 issues (wrong filename, nonexistent file annotated, hidden required column, RL state vector hardcoded contradicting strategy-agnostic design, type hint inconsistency).

### Decisions recorded
- RL Exit Policy action space: HOLD/EXIT/RAISE_SL/SET_BE (expanded from HOLD/EXIT)
- Mode 2: k-means clustering as pre-step before sweeping
- Mode 3: walk-forward rolling windows (not single train/test split)
- 80/20 held-out partition for Mode 2 discovery vs validation
- base.py kept as archive, base_v2.py is the active ABC
- Concept doc status: NOT YET APPROVED FOR BUILD

### State changes
- `docs/VINCE-V2-CONCEPT-v2.md` — 10 edits + 5 coherence fixes
- `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — CREATED (new)
- `strategies/base_v2.py` — CREATED (new), py_compile PASS
- `memory/TOPIC-vince-v2.md` — status + new file references updated
- `06-CLAUDE-LOGS/plans/2026-02-27-vince-concept-doc-update-and-plugin-spec.md` — CREATED (plan copy)

### Open items recorded
- User must approve concept doc when research complete
- FourPillarsPlugin wrapper build pending approval
- Bar index alignment issue flagged in spec Section 7 — must be resolved in FourPillarsPlugin

### Notes
Continuation from 2026-02-27-vince-ml-yt-findings.md. The RL action space was HOLD/EXIT in the YT findings session — this session expanded it to HOLD/EXIT/RAISE_SL/SET_BE.

---

## 2026-02-27-vince-concept-lock-final.md
**Date:** 2026-02-27
**Type:** Build session / Documentation

### What happened
Final Vince v2 concept lock session. Added two missing sections to `VINCE-V2-CONCEPT-v2.md`:

GUI section: Framework confirmed as Plotly Dash (replaces Streamlit dashboard_v392.py entirely). Run command: `python vince/app.py`. Layout: sidebar nav + persistent context bar + main content. 8 core panels defined with "what it answers" framing. RL Exit Policy and LLM Interpretation flagged as future panels requiring separate scoping.

Architecture — Module Boundaries section: three-layer model (GUI → API → Engine/Analysis), separation rule (panel files import only from vince.api and vince.types), 7 API function signatures, 9 dataclass types, full file layout diagram.

Status changed to: **CONCEPT v2 — APPROVED FOR BUILD (2026-02-27)**.

Build plan created with 10 phases (B1-B10): B1 FourPillarsPlugin, B2 api.py + types.py, B3 enricher.py, B4 pnl_reversal.py (data module), B5 query_engine.py, B6 app.py + layout.py (Dash shell), B7 pages 1/3/4/5, B8 discovery.py (Mode 2), B9 optimizer.py (Mode 3), B10 pages 6/7/8.

4 alignment issues resolved: vince/panels/ → vince/pages/ renamed throughout, B4 description clarified as pure Python (no Dash imports), four_pillars_plugin.py → four_pillars.py filename aligned, diskcache pattern added to B3 description.

### Decisions recorded
- **Vince = the app.** Dashboard serves Vince, replaces Streamlit entirely.
- **Dash framework (Plotly Dash 4.0.0)** — pattern-matching callbacks required for constellation builder
- **No agent build phases in B1-B10** — API skeleton built now, agent is future
- **vince/pages/** — Dash native convention
- **Enriched trades**: diskcache for dev, PostgreSQL for prod if needed
- **B3/B4/B5 are data-only modules** — no Dash imports
- Status: APPROVED FOR BUILD

### State changes
- `docs/VINCE-V2-CONCEPT-v2.md` — GUI + Architecture sections added, pages/ convention, status changed to APPROVED
- `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — coherence reviewed, 5 fixes applied
- `strategies/base_v2.py` — StrategyPlugin ABC, py_compile PASS
- Build plan `C:\Users\User\.claude\plans\async-watching-balloon.md` — CREATED
- `06-CLAUDE-LOGS/plans/2026-02-27-vince-b1-b10-build-plan.md` — CREATED (vault copy)

### Open items recorded
- Next step: B1 FourPillarsPlugin (`strategies/four_pillars.py`)
- B1 must wrap engine/backtester_v384.py and signals/four_pillars_v383_v2.py
- bar index alignment must be solved in B1

### Notes
Status change from NOT YET APPROVED to APPROVED is the key state change of this session. Also references Dash skill creation as a separate agent — this is the same-day dash-skill-creation session.

---

## 2026-02-27-vince-ml-yt-findings.md
**Date:** 2026-02-27
**Type:** Research / Analysis

### What happened
Reconstructed context from memory/logs (previous session closed mid-conversation). Read all 202 YT video summaries from `PROJECTS/yt-transcript-analyzer/output/summaries/` (JSON), read FreeCodeCamp full course transcript (9Y3yaoi9rUQ — unsupervised learning, Twitter sentiment, GARCH), and RL video summaries (oW4hgB1vIoY full RL trading bot, BznJQMi35sQ short). Read Vince v2 concept doc in full. Synthesized findings.

Key findings:
- THE MISSING RL PIECE: RL as exit policy optimizer (not full agent). State: bars_since_entry, current_pnl_atr, k1-k4, cloud_state, bbw. Action: HOLD or EXIT. Reward: net_pnl at exit. Fits Vince constraints: enhances Panel 2 without touching entry signals.
- Tier 1: Unsupervised clustering (k-means on entry-state vectors) for Mode 2, XGBoost feature importance ranks dimensions first, exits matter more than entries (random entry + ATR stops = 160% returns in one study).
- Tier 2: Walk-forward rolling windows needed, survivorship bias caveat (399-coin dataset excludes delisted), reflexivity caution, held-out 80/20 partition missing from current design, GARCH future scope, LSTM returns not price levels.
- Validated facts: stochastics + moving averages consistently top-ranked, 52% ML accuracy is real signal, NW indicator repaints, optimizing SL/TP on same data as discovery = overfitting.

### Decisions recorded
- No decisions made this session — findings identified, user decides what to incorporate
- Concept doc status: NOT YET APPROVED FOR BUILD at session end

### State changes
- Plan: `C:\Users\User\.claude\plans\logical-coalescing-lark.md` — CREATED
- `06-CLAUDE-LOGS/plans/2026-02-27-yt-channel-ml-findings-for-vince.md` — CREATED (vault copy)

### Open items recorded
- Vince v2 concept doc NOT updated yet
- Concept doc still NOT YET APPROVED FOR BUILD
- RL exit optimizer not scoped for build — finding only
- TOPIC-vince-v2.md not updated

### Notes
This is the research session; the follow-up concept doc update and approval happened in subsequent sessions on the same day (2026-02-27-vince-concept-doc-update-and-plugin-spec.md and 2026-02-27-vince-concept-lock-final.md). The RL action space here is HOLD or EXIT (simpler than the HOLD/EXIT/RAISE_SL/SET_BE expanded in the next session).

---

## 2026-02-27-yt-analyzer-v2-build.md
**Date:** 2026-02-27
**Type:** Build session

### What happened
Implemented structured output for the YT Transcript Analyzer: clickable YouTube timestamp links, LLM-generated summaries + tags via qwen3:8b, TOC with per-video metadata, download stats, and absolute output path fix.

Changes: `config.py` — OUTPUT_PATH fixed to project-relative absolute path, SUMMARIES_PATH added. `cleaner.py` — `group_into_blocks()` returns (start_seconds, block_text) tuples, added `extract_video_id()`, `seconds_to_mmss()`, clean output has `<!-- video_id:XXX -->` metadata and `[MM:SS]` timestamp markers. `summarizer.py` — NEW FILE, per-video LLM summary + auto-tags via qwen3:8b, writes JSON to `summaries/VIDEO_ID.json`. `reporter.py` — full rewrite of `generate_full_report()` with TOC table, per-video sections with clickable YouTube timestamp links. `fetcher.py` — `download_subtitles()` returns stats dict. `gui.py` — drain mode now 4 stages with Ollama, 3 without.

All 6 files pass py_compile.

Session 2 (v2.1 UX Overhaul, same date): First real run on CodeTradingCafe (211 videos, 201 transcripts). Summarize stage took 50+ minutes. User couldn't cancel, see progress, see output format, or skip summarization. Audit found 4 bugs (pipe chars in titles break TOC tables, misleading skipped stats, duplicate extract_video_id_from_clean, triple blank lines). v2.1 added 10 features: Cancel button (kills subprocess via st.session_state.active_process), Activity log (scrollable, accumulates), Clickable video list, Live summary preview, ETA, Skip-summarize checkbox (drain = 3 stages ~2 min vs 50+ min), Skip-download, Resume awareness, Download button (st.download_button for final report), Settings panel. gui.py full rewrite, fetcher.py and summarizer.py modified. All 3 modified files pass py_compile.

### Decisions recorded
- LLM: qwen3:8b via Ollama for summarization
- Clickable timestamp links format: `[MM:SS](https://www.youtube.com/watch?v=VIDEO_ID&t=SECONDS)`
- Cancel button kills subprocess via session_state.active_process
- Per-channel output namespacing deferred (requires module refactoring)
- Skip-summarize checkbox: drain becomes ~2 min vs 50+ min

### State changes
- `PROJECTS/yt-transcript-analyzer/config.py` — modified
- `PROJECTS/yt-transcript-analyzer/cleaner.py` — modified
- `PROJECTS/yt-transcript-analyzer/summarizer.py` — NEW FILE
- `PROJECTS/yt-transcript-analyzer/reporter.py` — full rewrite
- `PROJECTS/yt-transcript-analyzer/fetcher.py` — modified twice (stats dict, then on_process_started callback)
- `PROJECTS/yt-transcript-analyzer/gui.py` — full rewrite (v2.1)

### Open items recorded
- Per-channel output namespacing deferred — requires refactoring all module imports from `from config import X` to `import config` + `config.X`

### Notes
Plan files: `06-CLAUDE-LOGS/plans/2026-02-27-yt-analyzer-v2-structured-output.md` and `06-CLAUDE-LOGS/plans/2026-02-27-yt-analyzer-v21-ux-overhaul.md`.

---

## 2026-02-28-b2-api-types-research.md
**Date:** 2026-02-28
**Type:** Research audit (no code written)

### What happened
Pre-build research audit for Vince B2 (vince/types.py + vince/api.py). Audited 6 files: concept doc, plugin spec, base_v2.py, position_v384.py, backtester_v384.py, signals/four_pillars.py. Key finding: vince/ directory does not exist, B1 (FourPillarsPlugin) is also unbuilt.

7 bottlenecks identified: missing `plugin` param in api.py concept doc signatures, EnrichedTrade dataclass vs DataFrame question, ConstellationFilter typed fields vs generic dict question, bar index alignment (flagged in spec Section 7), run_enricher signature incomplete in concept doc, MFE bar definition (first vs last equal max high), SessionRecord scope undefined.

4 design verdicts reached with research justification:
1. Active plugin: per-call argument (per-call is thread-safe for Optuna parallelism, testable, agent-callable).
2. EnrichedTradeSet: DataFrame-centric (400K rows, Panel 2 is 3-4 pandas calls — dataclass list would take minutes).
3. ConstellationFilter: typed base + `column_filters: dict[str, Any]` (plugin-specific indicator columns are dynamic, universal fields are typed).
4. SessionRecord: named research session with uuid4 session_id, name, created_at UTC timestamp (mandatory), updated_at, plugin_name, symbols, date_range, notes, last_filter dict.

Corrected run_enricher signature: `(trade_csv: Path, symbols: list, start: str, end: str, plugin: StrategyPlugin) -> EnrichedTradeSet`.

B2 scope: 3 files — `vince/__init__.py` (empty), `vince/types.py` (dataclasses, stdlib+pandas only), `vince/api.py` (stubs raise NotImplementedError).

### Decisions recorded
- Plugin param: per-call (not module-level global)
- EnrichedTradeSet: DataFrame-centric (not dataclass list)
- ConstellationFilter: typed base + column_filters dict
- SessionRecord: named research session with mandatory UTC timestamp
- run_enricher corrected signature

### State changes
- Plan file: `C:\Users\User\.claude\plans\mellow-watching-lemon.md` wait — this is actually from B3. Let me check. Plan file: `06-CLAUDE-LOGS/plans/2026-02-28-b2-api-types-research-audit.md` — CREATED

### Open items recorded
1. B1 must be built first — bar index alignment must be solved there
2. B2 build: vince/__init__.py, vince/types.py, vince/api.py (stubs)
3. Load both /python and /dash skills before writing any code
4. After B2: B3 enricher.py — separate scoping session planned

### Notes
No code written. Research-only session. Both /python and /dash skills noted as mandatory before any B2 code.

---

## 2026-02-28-b3-enricher-research-audit.md
**Date:** 2026-02-28
**Type:** Research audit (no code written)

### What happened
Pre-build research audit for Vince B3 (vince/enricher.py). User referenced `BUILD-VINCE-B3-ENRICHER.md` which does not yet exist. Audited 8 files including plugin spec, concept doc, position_v384.py, signals/four_pillars.py, signals/four_pillars_v383_v2.py, base_v2.py, BingX plugin, and the directory structure (no vince/ dir, no enricher.py, no diskcache anywhere in 270+ Python files).

Confirmed what exists vs what is missing. Six critical blockers identified:

1. HIGHEST PRIORITY: `mfe_bar` missing from Trade384 — enricher needs bar index where MFE occurred for `_at_mfe` snapshot columns. Three options: A) modify position_v384.py (breaking), B) create position_v385.py, C) enricher does second OHLCV pass (slower, avoids breaking change).

2. compute_signals() signature mismatch: current `(df, params=None)`, required `(self, ohlcv_df)` — params baked in. Also column rename needed (base_vol/quote_vol → volume).

3. Column naming convention mismatch: pipeline outputs stoch_9/14/40/60, spec requires k1_9/k2_14/k3_40/k4_60. BBW not computed by compute_signals() — lives separately in signals/bbw.py.

4. diskcache not installed — zero imports across all 270+ Python files. Need pip install diskcache.

5. Bar index offset bug: backtester runs on date-filtered slice; entry_bar=0 = absolute bar 10,000 (not 0). Enricher needs absolute positional indices. FourPillarsPlugin wrapper must add slice start offset to all bar indices.

6. OHLC tuple storage format undefined: tuples don't round-trip through CSV. Recommended: 4 separate columns (entry_open, entry_high, entry_low, entry_close etc.) for individual value queries from Panel 4.

8 open questions for user (Q1-Q8). 6 improvements identified. Implementation order defined.

Plan written. No code written. Awaiting user decisions on Q1-Q8.

### Decisions recorded
None — all blocked on user decisions Q1-Q8.

### State changes
- Plan: `C:\Users\User\.claude\plans\mellow-watching-lemon.md` — CREATED
- `06-CLAUDE-LOGS/plans/2026-02-28-b3-enricher-research-audit.md` — CREATED (vault copy)
- No code written

### Open items recorded
- Q1: mfe_bar resolution (A/B/C) — HIGHEST PRIORITY
- Q2: Column rename approach (plugin wrapper only vs update stochastics.py globally)
- Q3: diskcache Cache vs FanoutCache
- Q4: OHLC storage (4 separate columns vs JSON string)
- Q5: strategy_document — existing or new doc
- Q6: BBW in B3 snapshots or defer
- Q7: Signal pipeline version (standard vs Numba)
- Q8: Cache invalidation (static or bust on parquet mtime change)

### Notes
diskcache not installed confirmed by searching 270+ Python files. `mfe_bar` missing from Trade384 is the highest priority blocker. Bar index offset bug (Blocker 5) is subtle and would cause all bar lookups to be wrong without correction. Plan file path (`mellow-watching-lemon.md`) same as B2 research — verify this is correct (both sessions reference same file name). This may be a logging error in the session log.

---

## 2026-02-28-bingx-be-fix.md
**Date:** 2026-02-28
**Type:** Bug fix session

### What happened
Fixed the breakeven stop price bug discovered from live trading data. Root cause confirmed: `_place_be_sl()` placed the STOP_MARKET at `entry_price` exactly. At that price, gross PnL = 0 and commission = $0.05, so net = -$0.05 guaranteed. Slippage adds $0.01-$0.129 more.

Evidence from live logs and trades.csv: 8 BE SL placements all at exact entry price (ELSA, VIRTUAL, PENDLE, DEEP, MEME, BB, VET, ATOM). Trade records show ATOM/VET at exactly -$0.05 (entry=exit), confirming commission_rate = 0.001 (0.05% per side) on live account.

Four approaches evaluated. Chosen: Approach A — commission math fix only (proportionate to trade size, correct, minimal code). Rejected STOP_LIMIT due to non-fill risk on volatile coins.

True BE math: LONG: exit >= entry × 1.001. SHORT: exit <= entry × 0.999.

Code changes in position_monitor.py: BE price formula added, stopPrice uses be_price (rounded 8dp) not entry_price, return signature changed from True/False to float/None, log updated to show entry and be_price. check_breakeven() updated to use be_price in state update and Telegram message.

New test file `tests/test_position_monitor.py` with 7 tests covering LONG/SHORT BE price math, stopPrice in API params matching be_price, API failure returns None, net pnl >= 0 at exact be_price fill (4 cases), missing data returns None without API call, commission_rate from self not hardcoded.

py_compile: PASS on both files.

### Decisions recorded
- Approach A chosen: fix commission math, not add slippage buffer
- STOP_MARKET confirmed correct order type for BE stop (guarantee of fill > exact price)
- commission_rate = 0.001 confirmed from live trade data (0.05% per side)
- BE_TRIGGER (1.0016) left unchanged — conservative but not wrong for 0.001 RT rate
- Out of scope: SL gate, risk gate, entry logic, TTP

### State changes
- `position_monitor.py` — _place_be_sl() and check_breakeven() fixed
- `tests/test_position_monitor.py` — NEW (7 tests)
- Both files: py_compile PASS

### Open items recorded
- Dollar impact small (~$0.05/exit, ~$0.40/day at session rate). Correct but not large.
- Residual risk: STOP_MARKET slippage $0.01-$0.05 — accepted, not addressed

### Notes
This session corrects the bug introduced in 2026-02-27-bingx-ws-and-breakeven.md where BE was placed at entry_price. That session's implementation was incomplete — stop price was entry but should be entry ± commission. This session is the correction. Commission rate discrepancy across sessions: 2026-02-26-bingx-audit-session.md used 0.0012 (0.06% taker × 2), this session confirms live rate is 0.001 (0.05% per side × 2). The rates differ — the audit session's commission rate was for BingX 0.06% taker which may differ from the live rate on the user's account tier.


# Batch 9 Findings — Research Agent

Files processed: 20
Date range: 2026-02-28 to 2026-03-03

---

## 2026-02-28-bingx-dashboard-v1-1-build.md
**Date:** 2026-02-28
**Type:** Build session

### What happened
Built the first interactive BingX live dashboard as a Dash 4.0 app. Three files created: `bingx-live-dashboard-v1-1.py` (~720 lines), `assets/dashboard.css` (~28 lines), and `scripts/test_dashboard.py` (~275 lines). The dashboard had 5 tabs (Operational, History, Analytics, Coin Summary, Bot Controls), 14 callbacks, AG Grid, dark theme, and BingX API integration. Interactive actions included Raise BE and Move SL via the BingX REST API.

During a logic audit, 3 bugs were found and fixed before delivery: (1) CRITICAL — CB-6/CB-7 sent USD notional as quantity to BingX API instead of contract quantity in coins; (2) MEDIUM — Raise BE callback placed stop at entry without checking mark price profit/loss direction; (3) MEDIUM — History tab only refreshed on filter change, not on data reload (State vs Input distinction). The TTP research log was also reviewed and noted that Approach C (BingX Native Trailing with activation gate) was already implemented in executor.py.

### Decisions recorded
- Used `importlib.util.spec_from_file_location` for hyphenated filename import in test scripts.
- All 3 bugs fixed before delivery.

### State changes
- 3 new files created: dashboard v1-1, CSS, test script.
- Bugs BUG1/BUG2/BUG3 identified and fixed in the same session.
- py_compile passed on both .py files.

### Open items recorded
- Future: could add Trail column to positions grid once TTP state fields are available.

### Notes
This is the first functional build of the BingX dashboard. Followed the user's corrected requirements (interactive management, not read-only). Prior Streamlit read-only build was discarded.

---

## 2026-02-28-bingx-dashboard-v1-2-build.md
**Date:** 2026-02-28
**Type:** Build session

### What happened
Designed and wrote a build script (`scripts/build_dashboard_v1_2.py`) for the v1-2 dashboard. The approach was surgical: read v1-1 (1645 lines), apply targeted `str.replace()` and line-based section replacements, then write v1-2 along with updated CSS and test script. 8 planned improvements were addressed covering: version bump, math import, chart axis labels, compute_metrics improvements, improved date pickers, clientside JS tab switching, Sharpe ratio annualization, and BE Hit Count / LSG% stubs returning "N/A" until the bot provides those columns.

Key technical choices: `suppress_callback_exceptions` kept True due to dynamic CB-5 action buttons; `.format()` used instead of f-strings in build script strings to avoid escaped quotes rule; date pickers default to None (show all trades).

### Decisions recorded
- Clientside JS callback replaces server-side CB-2 for instant tab switching.
- Sharpe ratio annualized with sqrt(365) from daily PnL groupby.
- BE Hit Count and LSG% return "N/A" until bot writes those columns to trades.csv.
- `.format()` used instead of f-strings in build scripts (escaped quotes rule).

### State changes
- Build script written: `scripts/build_dashboard_v1_2.py`, py_compile OK.
- NOT YET RUN by user at time of logging.

### Open items recorded
- User to run build script, then tests, then dashboard visual verification.

### Notes
None.

---

## 2026-02-28-bingx-dashboard-v1-3-patch.md
**Date:** 2026-02-28
**Type:** Build session (patch)

### What happened
User ran v1-2 build and tested the dashboard live. Reported 11 visual/calculation issues via screenshots. Issues triaged into P1-P10 patches plus one non-dashboard issue (LSG%/BE Hits N/A = expected, bot-side fix needed). A build script `scripts/build_dashboard_v1_3.py` was written applying 15 text replacements + 1 section replacement.

Patches covered: CSS tab class names fixed, comprehensive CSS expansion from ~95 to ~270 lines (AG Grid, DatePickerRange, Dropdown all covered), input field contrast improved, number spinner styling, analytics/grade comparison width constraints, max DD% bug fixed (guard for small peak equity, capped at -100%), pd.read_json deprecation fixed with StringIO wrapper, "Daily PnL" renamed to "Realized PnL", version bump.

### Decisions recorded
- Max DD% guard: skip when peak < $1.0, cap at -100%.
- StringIO wrapper required for pd.read_json in pandas 2.x.
- LSG% and BE Hits are an expected N/A until bot writes `be_raised` and `saw_green` columns.

### State changes
- Build script `scripts/build_dashboard_v1_3.py` written, py_compile OK.
- NOT YET RUN by user at time of logging.

### Open items recorded
- Future: bot-side fix to write `be_raised` + `saw_green` to trades.csv on trade close.

### Notes
None.

---

## 2026-02-28-bingx-dashboard-vince-planning.md
**Date:** 2026-02-28
**Type:** Planning session (two sessions appended)

### What happened
**Session 1:** Pure planning session — no code written. User stopped the build because layout was designed without asking. A plan was approved covering build order: BingX dashboard first, then Vince B1 through B6. Data was confirmed from live files: state.json schema (5 open positions, all BE raised), trades.csv columns, and live config.yaml (`demo_mode: false`, $5 margin, 10x leverage, 47 coins, no fixed TP).

**Session 2 (appended):** User started with explicit requirement "position management." Claude had added "read-only" to a prior plan note (Session 1 assumption), then built a Streamlit read-only version — wrong technology and wrong interactivity. User corrected: had never said "read-only." This session confirmed the read-only assumption came from Claude's own plan note, not from the user. The next session was directed to build an interactive Dash dashboard with Raise BE, Move SL, and per-row actions. A CLAUDE.md rule was agreed: "Management" = interactive. "Monitoring" = read-only. Ambiguous = ask.

### Decisions recorded
- Build order: BingX dashboard -> B1 -> B2 -> B3 -> B4 -> B5 -> B6.
- No background agents; sequential build; user runs verify after each block.
- Ollama (qwen3:8b) handles boilerplate-only files.
- Interactive Dash dashboard required with 3 tabs: Positions, History, Coin Summary.
- Positions tab actions: Raise to Breakeven, Move SL (calls BingX API).
- New CLAUDE.md rule: Management = interactive, Monitoring = read-only.

### State changes
- Plan files created (system + vault copy).
- Wrong Streamlit build (`bingx-live-dashboard-v1.py`) created and discarded.
- CLAUDE.md rule added regarding UI interactivity.

### Open items recorded
- Before building, ask user layout/UX questions. (Addressed in v1-1 session.)
- Before Vince B1: Read `signals/four_pillars.py` and `signals/state_machine.py`.

### Notes
This is the root cause session for the read-only vs interactive dispute. Log confirms user never used the word "read-only" anywhere — the assumption was entirely Claude's.

---

## 2026-02-28-bingx-trade-analysis-be-session.md
**Date:** 2026-02-28
**Type:** Build session + bug fix

### What happened
Three deliverables completed: (1) `scripts/analyze_trades.py` — a Phase 3 trade analysis script fetching live mark prices and BingX auth API open orders to compute 3-scenario True Total P&L. Constants: `COMMISSION_TAKER=0.0005`, `COMMISSION_RT_GROSS=0.001`, `COMMISSION_REBATE=0.50`, `BE_TOLERANCE=0.0005`, `MARGIN_USD=5.0`, `LEVERAGE=10`. (2) BE+Fees analysis fix — `identify_be_trades` renamed to `identify_sl_at_entry_trades` with relabeled sections because SL-at-entry exits are NOT true breakeven (each costs ~$0.025 net exit commission). 17 SL-at-entry exits in Phase 3 = -$0.425 avoidable commission loss. True BE requires SL at `entry * 1.001` for LONG. (3) Two bot files patched: `main.py` fallback commission rate changed 0.0016 → 0.001, and `position_monitor.py` BE logging improved to show commission covered in USD, Telegram renamed from "BREAKEVEN RAISED" to "BE+FEES RAISED".

### Decisions recorded
- SL-at-entry exits are NOT true breakeven — they still incur exit commission.
- True BE+fees formula: LONG: `entry * (1 + commission_rate)`, SHORT: `entry * (1 - commission_rate)`.
- BingX taker commission is 0.05% (0.0005) per side, RT = 0.001 gross.

### State changes
- `scripts/analyze_trades.py`: `identify_be_trades` → `identify_sl_at_entry_trades`, sections relabeled.
- `main.py`: fallback commission 0.0016 → 0.001.
- `position_monitor.py`: BE logging improved; Telegram renamed.
- py_compile: all 3 files OK.

### Open items recorded
None stated.

### Notes
Commission rate in this session uses 0.05% per side (BingX). Later sessions and MEMORY.md confirm 0.08% (0.0008) as the correct rate. This discrepancy is noted — the fallback in main.py was changed to 0.001 (0.05% RT) but the actual live rate fetched from BingX API may differ.

---

## 2026-02-28-bingx-ttp-research.md
**Date:** 2026-02-28
**Type:** Research + build session

### What happened
Full research and implementation session for Trailing Take Profit (TTP). Root cause identified: `tp_atr_mult: null` in config.yaml with no trailing TP replacement meant 0 TP_HIT in 46 live trades (all SL_HIT or EXIT_UNKNOWN). BE raise was working but only provides a floor, not profit locking.

Six TTP approaches evaluated (A through E): A = Restore fixed TP, B = BingX native trailing immediate, C = BingX native trailing with activation gate (CHOSEN), D = AVWAP 2σ + 10-candle counter (future), E = Periodic SL ratchet (complement to C).

Approach C implemented: `config.yaml` additions (`trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`), new `_place_trailing_order()` method in `executor.py` placing TRAILING_STOP_MARKET at `entry ± atr×2` with 2% callback rate. Three new unit tests in `tests/test_executor.py`. py_compile: PASS on both files.

### Decisions recorded
- Approach C (BingX native trailing with activation gate) chosen for live implementation.
- Approach D (AVWAP 2σ + 10-candle) deferred to future phase.
- Approach E (SL ratchet) is a complement, not standalone.
- Guard: trailing only runs if `trailing_rate`, `trailing_activation_atr_mult`, and `signal.atr` all set.

### State changes
- `config.yaml`: Added `trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`.
- `executor.py`: New `_place_trailing_order()` method, stores `trailing_order_id` + `trailing_activation_price` in state.
- `tests/test_executor.py`: 3 new tests added.
- py_compile: PASS.

### Open items recorded
- Future: add AVWAP 2σ trigger (Approach D) to position_monitor.py.
- Watch bot log for `Trailing order placed:` on next entry.

### Notes
The BingX native trailing (Approach C, `trailing_activation_atr_mult: 2.0`) was later DISABLED in the 2026-03-03 session (both set to null) because it conflicted with the TTP engine. The TTP Python engine became the sole trailing mechanism.

---

## 2026-02-28-dash-skill-v12-community-audit.md
**Date:** 2026-02-28
**Type:** Skill enrichment session

### What happened
Upgraded the Dash skill from v1.1 to v1.2 via community audit. WebFetch to `community.plotly.com` was blocked by user permission hook; WebSearch was used instead (not subject to same hook). Ran 10 parallel searches covering 7 topics: extendData + Candlestick, dcc.Interval blocking, relayoutData infinite loop, ag-grid styleConditions, WebSocket vs dcc.Interval, background callback overhead, candlestick rangebreaks cliff.

Key community findings: OHLC dict key format is exact and deviation causes silent failure; dcc.Interval longer than callback causes queue buildup; relayoutData on candlestick can loop infinitely (fix: `xaxis.autorange = False`); `Math` not available in ag-grid condition strings; WebSocket 3x faster than polling for < 500ms updates; background callbacks only worthwhile for tasks > 10 seconds.

Appended Part 4 (~280 lines, 7 sections) to `C:\Users\User\.claude\skills\dash\SKILL.md`, version bumped v1.1 → v1.2.

### Decisions recorded
- WebSearch = valid alternative to WebFetch when WebFetch is blocked by hook.
- Part 4 added: Community-Sourced Traps & Patterns.

### State changes
- `C:\Users\User\.claude\skills\dash\SKILL.md`: 1447 → 1730 lines, v1.1 → v1.2.

### Open items recorded
None.

### Notes
None.

---

## 2026-02-28-dashboard-v393-promote.md
**Date:** 2026-02-28
**Type:** Bug fix + promotion session

### What happened
Investigated P0.3 (dashboard v3.9.3 BLOCKED — IndentationError). Found the file already compiles clean — the backlog entry was stale, issue resolved in a prior session. Fixed a pre-existing silent date filter fallback bug in `apply_date_filter()`: when `len(df_filtered) < 100`, function silently returned the full unfiltered dataset. For 7d date range with stale parquet data, this meant showing the entire year with no warning. Fix: removed `< 100` silent fallback; added explicit warnings at 3 call sites and ValueError in sweep incremental path.

Dashboard runtime validated by user: loads, portfolio runs, 30d works, 7d now shows proper warning. v3.9.3 promoted to PRODUCTION.

### Decisions recorded
- v3.9.3 promoted to PRODUCTION.
- Silent date filter fallback removed — always return filtered data, show explicit warnings.

### State changes
- `scripts/dashboard_v393.py`: 5 edits (removed fallback, added 3 warnings, 1 ValueError, trailing newline).
- v3.9.3: py_compile PASS, runtime validated, PRODUCTION.
- v3.9.2: remains as stable fallback.

### Open items recorded
None.

### Notes
Log note said v3.9.3 had IndentationError (in backlog). Actual file compiled clean — stale backlog entry.

---

## 2026-02-28-parquet-data-catchup.md
**Date:** 2026-02-28
**Type:** Bug fix + build session

### What happened
Session to update the 1m candle parquet cache in the backtester (15 days stale since 2026-02-13). Data source confirmed: Bybit v5 API. Cache: 399 coins, 798 files (1m + 5m), 6.7 GB, spanning 2025-02-11 to 2026-02-13. Fetcher class: `BybitFetcher` in `data/fetcher.py`. The existing fetcher hardcodes 1m interval; 5m parquets came from a prior process. User decided 1m only for this session.

Bug found: `config.yaml` only lists 5 default coins; `--coins N` flag slices from that list so `--coins 399` still yields 5. No flag existed to discover symbols from cached parquets. Fix: added `--all` flag to `scripts/fetch_data.py` — when passed, discovers all symbols from existing `*_1m.parquet` files in cache dir. py_compile: PASS.

### Decisions recorded
- 1m data only for this session (5m deferred).
- `--all` flag added to discover symbols from existing parquets.

### State changes
- `scripts/fetch_data.py`: Added `--all` flag, moved `cache_dir` resolution above symbol determination.
- py_compile: PASS.
- Script updated, awaiting user execution.

### Open items recorded
- User to run: `python scripts/fetch_data.py --months 1 --all`.

### Notes
None.

---

## 2026-02-28-vince-b1-scope-audit.md
**Date:** 2026-02-28
**Type:** Research + spec writing (no code)

### What happened
User referenced `PROJECTS/four-pillars-backtester/BUILD-VINCE-B1-PLUGIN.md` — file did not exist. Session researched B1 scope from the approved build plan and plugin spec, then created the formal build spec. Sources read: approved B1-B10 plan, VINCE-PLUGIN-INTERFACE-SPEC-v1.md, VINCE-V2-CONCEPT-v2.md, base_v2.py ABC, existing four_pillars.py (conflict found), both backtester engine versions, position_v384.py, signals, run_backtest script.

Critical finding: `strategies/four_pillars.py` already existed with a v1 partial implementation. 6 issues in v1 file identified: wrong base class, missing 4/5 abstract methods, wrong signal import, wrong `compute_signals()` signature, separate enrichment method, legacy ML classifier methods. Engine decision: v385 over v384 (user confirmed) — v385 adds post-processing pass with LSG category and P&L path.

Output: `BUILD-VINCE-B1-PLUGIN.md` created with full spec including archive instruction, per-method guide, trade schema, imports, and 4 verification tests.

### Decisions recorded
- v385 engine over v384 (user confirmed).
- Existing `strategies/four_pillars.py` must be archived to `strategies/four_pillars_v1_archive.py` before B1 build.
- B1 uses `signals/four_pillars_v383_v2.py` (spec says; later found to be outdated — see 2026-03-03-session-handoff).
- `symbol` field not in Trade384 — must be injected by `run_backtest()` wrapper per symbol loop.

### State changes
- `BUILD-VINCE-B1-PLUGIN.md` created.
- `06-CLAUDE-LOGS/plans/2026-02-28-vince-b1-plugin-scope-audit.md` plan copy created.
- No code written.

### Open items recorded
- Confirm Q1/Q2 (mfe, mae, saw_green in Trade384) by reading position_v384.py.
- Complete B1 build (next step after this session).

### Notes
The signal import decision (v383_v2) was found to be outdated in the 2026-03-03-session-handoff log, which states B1 must use `signals/four_pillars_v386.py` instead.

---

## 2026-02-28-vince-b4-scope-audit.md
**Date:** 2026-02-28
**Type:** Research + audit (no code)

### What happened
Full research audit of Vince B4 (PnL Reversal Analysis panel). User referenced `BUILD-VINCE-B4-PNL-REVERSAL.md` (did not exist). Cross-referenced B2 and B3 audit docs to understand B4's inputs and upstream blockers. Found that the entire `vince/` directory did not yet exist at time of audit — B4 is blocked on B1→B2→B3.

B4 scope confirmed: single file `vince/pages/pnl_reversal.py` (~250-350 lines), pure Python, no Dash imports. Four functions: `get_pnl_reversal_analysis`, `get_tp_sweep_curve`, `get_optimal_exit_analysis`, `compute_mfe_bin`. 8 bottlenecks/questions identified, 6 improvements proposed.

Key bottleneck: Q1 — does backtester_v384 output `mfe`, `mae`, `saw_green`, `entry_atr` per trade? HIGH RISK if absent. TP sweep should simulate from MFE (not re-run backtester). ATR bin granularity: spec says 6-bin, reference says 9-bin; recommendation was 9-bin for finer resolution.

### Decisions recorded
- B4 does NOT import Dash/Plotly, re-run backtester, filter trade count, train ML models, or touch DB.
- TP sweep: simulate from MFE (if `mfe_atr >= tp_level`, trade would have hit TP).
- Recommended 9-bin ATR histogram over 6-bin spec.
- `rl_overlay: Optional[List] = None` as placeholder — real RL is future scope.

### State changes
- `BUILD-VINCE-B4-PNL-REVERSAL.md` was to be written (future step — spec not created this session).
- Plan file: `C:\Users\User\.claude\plans\concurrent-sniffing-brook.md` created.
- No code written.

### Open items recorded
- Confirm Q1/Q2 by reading `engine/position_v384.py`.
- Complete B1 → B2 → B3 before building B4.
- Write `BUILD-VINCE-B4-PNL-REVERSAL.md` spec (deferred).

### Notes
None.

---

## 2026-03-02-b2-api-types-build.md
**Date:** 2026-03-02
**Type:** Build session

### What happened
Completed B2 (Vince API Layer + Dataclasses). All 6 files created and py_compile validated: `vince/__init__.py` (12 lines), `vince/types.py` (148 lines), `vince/api.py` (185 lines), `vince/audit.py` (310 lines), `tests/test_b2_api.py` (195 lines), `scripts/build_b2_api.py` (92 lines).

`vince/types.py` contains 8 dataclasses: IndicatorSnapshot, OHLCRow, EnrichedTradeSet, MetricRow, ConstellationFilter, ConstellationResult, SessionRecord, BacktestResult. `vince/api.py` contains 8 stub functions raising `NotImplementedError` with build-block references. `vince/audit.py` has 13 checks (AST parsing, bot signal import, BBW wiring, ExitManager, interface, rot_level, version, trailing, stage2, BE raise, vince dir, SL mult, enricher).

Also built `scripts/build_strategy_analysis.py` which generates `docs/STRATEGY-ANALYSIS-REPORT.md` for pasting into Claude Web.

7 critical architecture findings documented from audit: bot runs v1 signal (not v386), BBW orphaned, ExitManager likely dead code, trailing stop divergence (backtester AVWAP vs bot 2% callback), BE raise missing from bot, rot_level=80 nearly useless, strategies/four_pillars.py v1 has wrong base class.

### Decisions recorded
- Plugin passed as per-call argument (not global) in api.py — thread-safe for Optuna.
- B2 is DONE; B1 is next (unblocks B3-B6).

### State changes
- B2 block complete: 6 files created, py_compile PASS.
- 7 critical architecture issues documented.

### Open items recorded
- Run `build_strategy_analysis.py` → paste into Claude Web.
- Discuss and fix strategy (rot_level, trailing stop, BBW wiring, bot vs backtester).
- Build B1 once strategy is correct.

### Notes
None.

---

## 2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md
**Date:** 2026-03-02 (multiple sessions appended, extends to 2026-03-03)
**Type:** Audit + multiple patch build sessions

### What happened
Multi-session log covering v1-3 through v1-4 dashboard work across 2026-03-02 and into 2026-03-03.

**Early 2026-03-02:** Ran `build_dashboard_v1_3_final.py`, audited full v1-3 (1805 lines + 180 CSS), found 6 issues (duplicate import io, Unreal PnL None choke, Move SL validation blocks trailing, CB-10 State vs Input, ISO week edge case, gross_pnl alias confusion). Patch 1 fixed B1+B2+B4.

**Mid 2026-03-02:** User tested live — 5 remaining visual issues. Key root cause discovered: Dash 2.x uses CSS custom properties (CSS variables) at `:root`. Class-name CSS and `!important` do NOT override CSS variables — must override at `:root`. Patch 2 (F1+F2+F3+F4) written: status bar equity card, CSS :root variable block, equity curve with unrealized extension, position reconciliation (calls BingX API, removes stale state.json positions). Patches 3-5 applied (balance from API, date filter, stale session, coin detail, CSS improvements).

**Late 2026-03-02:** Patches 6 (CSS variables :root block) and 7 (bot status feed in main.py + dashboard polling) written. Patch 7 changes 4 files: main.py (write_bot_status), data_fetcher.py (progress_callback), dashboard (store-bot-status, status-interval, status panel), CSS (.status-feed-panel).

**v1-4 requirements received** (user AFK messages): Rename tabs, add Bot Terminal tab with Start/Stop, 6-tab layout. `build_dashboard_v1_4.py` written with 15 safe_replace patches (P1-P14). py_compile PASS.

**2026-03-03 continuation:** All 15 anchors audited against v1-3 — all PASS. User ran dashboard, crash: `DuplicateCallback: allow_duplicate requires prevent_initial_call`. Fix: `prevent_initial_call='initial_duplicate'` for CB-T3. Patch1 written. Dash skill updated to v1.3 (PART 5, 9 sections). New issues: doubled status messages (patch7 applied twice to main.py), IndexError in `flat_data[ind]` (CB-S1 and CB-T3 both on status-interval with mismatched prevent_initial_call). Patch2 written (13 patches: dedup main.py, toggle button, OFFLINE header, 360px log height). Session ended with KeyError: browser using stale callback map — fix is Ctrl+Shift+R.

### Decisions recorded
- CSS custom properties must be overridden at `:root` in Dash 2.x dark theme implementations.
- `prevent_initial_call='initial_duplicate'` fires on load AND allows duplicate registration.
- Force kill (`taskkill /F`) is instant death — no Python cleanup runs; dashboard must write stop event.
- Patch scripts must be idempotent (check if already applied before writing).

### State changes
- Multiple patch scripts written and applied: patch, patch2, patch3, patch4, patch5 (applied), patch6 (applied), patch7 (applied to main.py twice — error).
- `bingx-live-dashboard-v1-4.py` created from v1-3 + 15 patches.
- `build_dashboard_v1_4_patch1.py`: CB-T3 fix.
- `build_dashboard_v1_4_patch2.py`: Written, run status unclear at session end.
- Dash skill: v1.2 → v1.3 (PART 5 appended).

### Open items recorded
- Verify patch2 ran (check output for all 13 PASS).
- Hard refresh browser (Ctrl+Shift+R) after restart.
- Plan and build bot status feed feature.
- Version as v1-4 once all visual issues resolved (was already versioned).

### Notes
This log covers the most complex patch sequence in the project. The root cause of all white backgrounds (Dash CSS variables) was a significant discovery. Patch7 was applied twice — a process error highlighted as a lesson learned.

---

## 2026-03-03-bingx-dashboard-v1-4-patches.md
**Date:** 2026-03-03 (with 2026-03-04 continuation appended)
**Type:** Build session (multiple patches)

### What happened
Continuation of v1-4 dashboard work. Key events across multiple sessions:

**Session 1 (2026-03-03 early):** build_dashboard_v1_4.py audit confirmed all 15 anchors PASS. User ran, got CB-T3 crash (allow_duplicate without prevent_initial_call). `build_dashboard_v1_4_patch1.py` written to add `prevent_initial_call='initial_duplicate'`. Dash skill updated to v1.3 (PART 5).

New issues after patch1: Activity Log capped too small (180px), doubled status messages (patch7 applied twice), IndexError `flat_data[ind]`. Diagnosed: duplicate `write_bot_status` function in main.py. Patch2 written: 13 patches across 3 files (dedup main.py, toggle button, OFFLINE header, 360px log, CB-T3 fix to `prevent_initial_call=True`). Additional user reports: header still shows LIVE when bot stopped, no Telegram on stop (expected with force kill), Start/Stop should be single toggle.

**Session 2 (2026-03-03 afternoon):** Two bot/config changes: (1) BingX native trailing order disabled (`trailing_activation_atr_mult: null`, `trailing_rate: null`) — was conflicting with TTP engine. (2) BE raise switched from `ttp_state == "ACTIVATED"` waiting to live mark price trigger (fetches per-position every 30s). Monitor loop poll reduced 60s → 30s. `max_positions: 15`, `max_daily_trades: 200`.

**Session 3 (2026-03-03 evening):** Patch4 applied (Close Market button + CB-16 callback). 2/2 PASS, py_compile PASS, dashboard running. Patch5 written (TTP per-position controls + BE buffer): TTP Act%/Trail% inputs per position, CB-17/CB-18 for Set TTP/Activate Now, signal_engine.py TTP override handling, `be_buffer=0.001` added to position_monitor.py BE price formula. Patch5 NOT YET RUN.

**2026-03-04 continuation:** Exit mechanics fully verified from source. All 3 SL ladder steps confirmed. Patch5 confirmed already applied (be_buffer present). Monitor optimization: early return in check() when no positions in state (skip API call).

### Decisions recorded
- BingX native trailing disabled — TTP Python engine is sole trailing mechanism.
- BE raise trigger: live mark price every 30s (not 5m candle close ttp_state wait).
- BE price formula: `entry * (1 + commission_rate + 0.001)` for LONG.
- Single toggle button (Start/Stop) replaces separate Start + Stop buttons.
- force kill via taskkill /F means bot cleanup must come from dashboard, not bot.

### State changes
- Patches 1-4 applied, patch5 written (confirmed applied by 2026-03-04).
- `config.yaml`: trailing disabled, position_check_sec 30, max_positions 15, max_daily_trades 200.
- `position_monitor.py`: BE trigger rewritten, be_buffer added, early return guard added.
- SL ladder: 3 steps confirmed from code.

### Open items recorded
- Verify Close Market flow with an actual open position (awaiting test).

### Notes
Patch3 (TTP columns + Controls toggle) referenced in cumulative table but not detailed in this session — details are in the TTP integration build session.

---

## 2026-03-03-cuda-dashboard-v394-build.md
**Date:** 2026-03-03
**Type:** Build session (multiple sessions appended)

### What happened
Multi-session build log for the CUDA GPU sweep integration in dashboard v3.9.4.

**Session 1:** Spec audit via 3 parallel Explore agents found 4 issues (wrong backtester version reference, column name inconsistency, reentry cloud3 gate status, stale IndentationError claim). Build script `scripts/build_cuda_engine.py` written creating 3 files: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/dashboard_v394.py`. Python 3.13 CUDA blocker discovered: Numba 0.61.2 does not support Python 3.13 for CUDA. Python 3.12 install script written (`INSTALL-PYTHON312-CUDA.md`).

**Session 2:** Python 3.12 venv created at `.venv312`. CUDA setup required multiple fixes: nvvm.dll not found, NVCC 12.9 too new for Numba 0.64, cudart.dll not found. GPU Sweep confirmed working on 0GUSDT (top combo: SL=0.5, TP=999, BE=0.5, CD=5, 119 trades, $28,595 net PnL, PF 5.55).

**Session 3:** GPU Portfolio Sweep mode added (build script: `build_gpu_portfolio_sweep.py`). Features: multi-coin loop, coin selection (Top/Lowest/Random/Custom N), capital models (Per-Coin Independent or Shared Pool), parameter ranges, progress bar. Results display: Uniform Params, Per-Coin Optimized (labeled overfitted), heatmaps, CSV exports. Bugs fixed: ROI math, cherry-picking bias labeling, stale params detection, heatmap aggregation.

**Session 3 continued — Full Logic Audit:** 3 parallel audit agents run. CRITICAL: (1) commission fix never applied to cuda_sweep.py (still taker for both sides), (2) pnl_sum missing entry commissions. HIGH: win_rate displayed as fraction not percentage, TTP state lost on restart (later found incorrect), WSListener dies permanently after 3 reconnect failures, `_place_market_close()` missing `reduceOnly=true`, saw_green check `>` vs `>=`. 15+ total findings documented.

**Session 4 — Audit Fixes:** `build_audit_fixes.py` written. CRITICAL #1/#2: split commission rates in cuda_sweep.py (0.0008 taker entry / 0.0002 maker exit). HIGH #3: win_rate formatted as percentage. HIGH #5: WSListener MAX_RECONNECT 3→10, exponential backoff, dead flag file. HIGH #6: reduceOnly added. HIGH #7: saw_green `>` → `>=`.

**Session 5 — UX Improvements:** GPU Portfolio Sweep enhancements: coin selection reset tracking, Stop Sweep button, Reset Parameters button, date range display, Random Week/Month options, Trading Volume & Rebates stats, Est. Trade Duration. Three bugs fixed: parquet index is int64 not DatetimeIndex, bar count check, variable used before definition.

### Decisions recorded
- Engine version: Backtester390 for GPU sweep (differs from CPU sweep running v3.8.4).
- Python 3.12.8 in `.venv312`, side-by-side with system 3.13.
- CUDA toolkit via pip packages (not conda): `nvidia-cuda-nvcc-cu12==12.4.131`.
- Build approach: single build script copies v392 + applies text patches.
- Commission: taker 0.0008 entry, maker 0.0002 exit (not both taker).
- GPU Portfolio "Uniform Params" shown first (honest); "Per-Coin Optimized" labeled as overfitted upper bound.

### State changes
- 3 new files: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/dashboard_v394.py`.
- dashboard v3.9.4: LIVE, GPU sweep confirmed on RTX 3060.
- Multiple audit fixes applied to cuda_sweep.py, dashboard_v394.py, ws_listener.py, position_monitor.py.
- Dash skill: v1.2 → v1.3 (noted in v1-4-patches log, same day).

### Open items recorded
- Remaining MEDIUM/LOW findings deferred: stale detection gaps, Shared Pool capital enforcement, TTP mid-bar timing, race condition, commission fallback mismatch, slippage, close-remaining counters, UI tweaks.
- Strategy finetuning (4P stochastics, open trade scenarios) and BingX bot monitoring: next day's focus.

### Notes
HIGH #4 (TTP state lost on restart) was reassessed — code already restores TTP state via signal_engine.py lines 113-127. HIGH #6 (reduceOnly missing) was found in position_monitor.py, not executor.py (log corrected the prior assertion).

---

## 2026-03-03-cuda-dashboard-v394-planning.md
**Date:** 2026-03-03
**Type:** Planning session (no code)

### What happened
Short planning session. No code written. User asked if existing CUDA handover log (`2026-03-03-cuda-sweep-engine-handover.md`) was clear — confirmed yes. User requested a dashboard-focused spec for a new chat. Identified 4 pre-audit errors still in the old vault plan (`06-CLAUDE-LOGS/plans/2026-03-03-cuda-sweep-engine.md`): wrong column names for reentry, wrong param_grid shape, wrong TP sentinel value, missing cloud3 arrays. Wrote corrected dashboard spec as session handover.

Key architecture facts locked in spec: 12 kernel input arrays (4 price + 4 entry + 2 reentry + 2 cloud3), param_grid [N,4], tp_mult=999.0 sentinel, Welford's online variance for Sharpe, ThreadPoolExecutor workers must not call st.*, ensure_warmup() at module import, base v392 (NOT v393).

### Decisions recorded
- New spec file created to replace error-containing old vault plan.
- sweep_all_coins_v2.py deferred — not in this build.

### State changes
- System plan: `C:\Users\User\.claude\plans\synthetic-mapping-ember.md` created.
- Vault copy: `06-CLAUDE-LOGS/plans/2026-03-03-cuda-dashboard-v394-spec.md` created.

### Open items recorded
- Open new chat, paste spec, execute build.

### Notes
This planning session preceded the CUDA build session (same date) — documents the pre-build spec correction step.

---

## 2026-03-03-daily-bybit-updater.md
**Date:** 2026-03-03
**Type:** Build session

### What happened
Built a daily-run script for updating the backtester's Bybit candle data cache (399 coins, stale since 2026-02-13). Build script `scripts/build_daily_updater.py` creates `scripts/daily_update.py`.

Features of `daily_update.py`: (1) Bybit symbol discovery via `/v5/market/instruments-info` for all active USDT linear perps (~548 symbols); (2) Incremental fetch using `.meta` end timestamp per coin, fetches only the gap; (3) 5m resampling via `TimeframeResampler` from `resample_timeframes.py`; (4) Dual logging (file + console with timestamps). CLI flags: `--dry-run`, `--skip-new`, `--skip-resample`, `--max-new N`, `--months N`.

Designed as standalone script (not a patch to fetch_data.py) with different lifecycle (daily unattended vs manual bulk). py_compile PASS on build script, ast.parse PASS on embedded source. Not yet executed by user.

Multiple vault files updated: TOPIC-backtester.md, LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md (C.29 added), DASHBOARD-FILES.md (v3.9.4 promoted), plan file created.

### Decisions recorded
- Standalone script, not a patch to fetch_data.py.
- Incremental append logic lives in daily_update.py (fetcher.py kept stable).
- Backlog item C.29 created for Daily Bybit Data Updater.

### State changes
- `scripts/build_daily_updater.py`: NEW, py_compile PASS.
- `scripts/daily_update.py`: created by build script, not yet executed.
- Dashboard v3.9.4 promoted to production in DASHBOARD-FILES.md.

### Open items recorded
- User to run: `python scripts/build_daily_updater.py` then `python scripts/daily_update.py --dry-run`.

### Notes
None.

---

## 2026-03-03-session-handoff.md
**Date:** 2026-03-03
**Type:** Handoff / context switch (no builds)

### What happened
Context handoff session from a prior context-limit session. Verified all B2 artefacts intact, memory files updated correctly, INDEX.md and PRODUCT-BACKLOG.md current. Wrote next-steps roadmap to `06-CLAUDE-LOGS/plans/2026-03-03-next-steps-roadmap.md`. Identified a signal file conflict in B1 spec.

B1 spec (`BUILD-VINCE-B1-PLUGIN.md`, written 2026-02-28) says to import from `signals/four_pillars_v383_v2.py`. But the v386 scoping session (2026-02-28) created `signals/four_pillars_v386.py`, and the B3 spec explicitly says it is blocked waiting on v386. Resolution: B1 must use `signals/four_pillars_v386.py`. The plan mode plan (`snuggly-mixing-moon.md`) is correct; the BUILD spec is outdated.

### Decisions recorded
- B1 must import from `signals/four_pillars_v386.py` (not v383_v2 as stated in BUILD spec).
- Follow plan mode plan for signal imports, not build spec.

### State changes
- Roadmap written: `06-CLAUDE-LOGS/plans/2026-03-03-next-steps-roadmap.md`.
- No code changes.

### Open items recorded
- Immediate first step: run `scripts/build_strategy_analysis.py` → paste into Claude Web.
- See roadmap for full prioritized list.

### Notes
Directly contradicts/updates the B1 spec from 2026-02-28 regarding which signal file to import.

---

## 2026-03-03-signal-rename-architecture-session.md
**Date:** 2026-03-03
**Type:** Architecture / scoping session (no code)

### What happened
Deep architecture analysis of the Four Pillars signal system. Read Pine Script source `four_pillars_v3_8_2_strategy.pine`, `V3.8.2-COMPLETE-LOGIC.md`, `Core-Trading-Strategy.md`, and prior session logs.

Key finding: The existing A/B/C grade naming system is architecturally incorrect. A = renamed Quad (4/4 stochs, Cloud 3 bypassed). B = renamed Rotation (3/4 stochs, Cloud 3 gated, final name TBC by Malik). C = ADD — NOT a state machine signal type; it is an engine label applied when a Quad/Rotation signal fires while a same-direction position is already open. The current Pine C signal (2/4 stochs) is wrong by design, not by parameterisation.

Gap analysis: Pine state machine generates Quad + Rotation + C (wrong — C must be removed). Python state_machine.py generates `long_signal_c` (must be removed). Python backtester assigns grade C as fresh entry fallback (wrong — ADD = engine label when same-direction position exists). Config `allow_c_trades` should be renamed `allow_add`.

5 pending questions: edit permissions on bot files (unanswered), trailing stop alignment direction (unanswered), final name for B (Malik to decide), ADD fires only on Quad/Rotation quality (awaiting confirmation), Q2.

### Decisions recorded
- A → Quad (locked).
- B → Rotation (name TBC by Malik).
- C → ADD (engine label, not state machine signal).
- ADD definition: Quad or Rotation fires while same-direction position open + capacity + cooldown met.
- C signals in Pine (2/4 stochs) must be removed entirely.

### State changes
- No files written except this session log.
- Architecture decisions documented for future implementation.

### Open items recorded
- Malik confirms ADD definition (Q5).
- Malik finalises B name (Q4).
- Q2, Q3 answers needed.
- Create `signals/state_machine_v390.py`, `signals/four_pillars_v390.py`, `engine/backtester_v390.py`.
- Update Pine script (separate session).

### Notes
None.

---

## 2026-03-03-ttp-integration-build.md
**Date:** 2026-03-03
**Type:** Build session

### What happened
Built two build scripts from the audited TTP integration plan. Read all 5 source files to be patched before writing. Confirmed `state_manager.update_position()` signature (key + updates dict with lock). Fixed unicode escape error in build script docstrings (Windows paths with `\U` trigger Python's unicode escape parser in triple-quoted strings — fix: prefix with `r"""` or use forward slashes).

`scripts/build_ttp_integration.py` — 6 patches: P1 creates `ttp_engine.py` (TTPExit class, TTPResult dataclass, run_ttp_on_trade, 5 bug fixes), P2 patches signal_engine.py (TTPExit import, ttp_config, restructured on_new_bar, _evaluate_ttp_for_symbol), P3 patches position_monitor.py (check_ttp_closes, _cancel_all_orders_for_symbol, _place_market_close, _fetch_single_position), P4 patches main.py (ttp_config pass, monitor.check_ttp_closes()), P5 patches config.yaml (ttp_enabled/ttp_act/ttp_dist), P6 creates `tests/test_ttp_engine.py` (6 unit tests).

`scripts/build_dashboard_v1_4_patch3.py` — 5 patches: TTP + Trail Lvl columns added, TTP state in positions dataframe, TTP section in Strategy Parameters tab, CB-11/CB-12 updated for TTP controls.

5 bugs fixed in ttp_engine.py (from plan): CLOSED state assignment, activation candle fall-through, CLOSED_PARTIAL replaced, iterrows replaced with itertuples, band_width_pct guard.

py_compile PASS on both build scripts.

### Decisions recorded
- Unicode escape fix: use `r"""` prefix or forward slashes in Windows path comments inside generated Python source strings.
- `itertuples(index=False)` preferred over `iterrows()` in TTPExit engine.

### State changes
- `scripts/build_ttp_integration.py`: NEW, py_compile PASS.
- `scripts/build_dashboard_v1_4_patch3.py`: NEW, py_compile PASS.
- INDEX.md and TOPIC-bingx-connector.md updated.
- NOT YET RUN by user at time of logging.

### Open items recorded
- User to run both build scripts, then pytest, then restart dashboard.

### Notes
None.


# Research Batch 10 — Findings
**Files processed:** 10
**Batch date:** 2026-03-05 (research execution date)

---

## 2026-03-03-ttp-integration-plan.md
**Date:** 2026-03-03
**Type:** Planning session

### What happened
Planning and audit session for integrating TTP (Trailing Take Profit) engine into the BingX connector and dashboard. Read handoff context from previous session (dashboard v1.4 patch2 applied). Read TTP spec, build brief, and draft ttp_engine.py code. Confirmed NO TTP logic existed anywhere in the connector yet. Clarified with user that TTP = display-only on dashboard + toggle on/off + wired into live bot. Initial plan using mark price approach written, then full audit found 5 critical gaps. Plan revised to hybrid architecture. Verified 5 "pre-existing bugs" in executor.py and state_manager.py — all were agent transcription errors, actual code was correct.

### Decisions recorded
1. TTP evaluates on real 1m OHLC in market_loop thread (signal_engine.py), close orders execute in monitor_loop thread (position_monitor.py). `ttp_close_pending` flag in state.json bridges the two threads.
2. Five critical plan gaps identified and resolved: mark price H=L issue, activation price gap bug, race condition guard, need for `_place_market_close()`, need for `_cancel_all_orders_for_symbol()`.
3. 7 files to be touched in next session build.

### State changes
- Plan written to `C:\Users\User\.claude\plans\cuddly-dancing-perlis.md` and vault copy `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-dashboard-v1-4-patch3-ttp-display.md`
- No code written this session — plan only

### Open items recorded
- Build `scripts/build_ttp_integration.py`
- Build `scripts/build_dashboard_v1_4_patch3.py`
- Run both scripts and tests
- ttp_engine.py source code (user-provided draft) had 4 bugs to fix: self.state never CLOSED, CLOSED_PARTIAL state, iterrows(), band_width_pct guard
- ttp_engine.py not yet saved to a file — must be re-pasted or retrieved in next session

### Notes
None.

---

## 2026-03-04-bingx-v1-5-full-audit-upgrade.md
**Date:** 2026-03-04
**Type:** Build session (multi-phase)

### What happened
Major 4-phase build session triggered by live bot running 12+ hours with multiple observed issues. Issues included TTP close orders failing (error 109400 — infinite retry loops), Close Market button broken (signature error 100001), equity curve mixing all sessions, coin summary date filter disconnected, EXIT_UNKNOWN exits, no TTP activation tracking in trades.csv, bot OFFLINE paradox, and $5/10x underperforming.

Phase 1: Built 6 diagnostic scripts (error audit, variable web, TTP audit, ticker collector, demo order verify, trade analysis). All py_compile PASS.

Phase 2: Bot core fixes — removed `reduceOnly` from `_place_market_close()` (root cause of 109400), added SL tightening after TTP activation, added TTP columns to trades.csv, updated config.yaml and main.py.

Phase 3: Dashboard v1.5 built from v1.4 base — 17 patches including signing fix (100001), reduceOnly removal from 3 callbacks, session equity filter, coin summary date wiring, dual bot/exchange status, TTP stats panel, trade chart popup modal with klines/stochastic/BBW.

Phase 4: Beta bot built — config_beta.yaml (44 coins, $5/20x), main_beta.py with overlap guard checking live state.json at startup.

Phase 1 was run and produced real data: 15,399 total error lines, 7,650 TTP_CLOSE_FAIL, win rate 8.3% (230 trades), net PnL -$825.24, LSG% 75.8%, EXIT_UNKNOWN 43% of all exits.

An audit fixes build (`build_audit_fixes.py`) applied 5 additional patches: duplicate function removal, NameError fix in signal_engine.py, reconcile() phantom close fix, input() blocking call removal, session_start refresh.

### Decisions recorded
1. BUG-1 root cause confirmed: `"reduceOnly": "true"` is invalid in Hedge mode on BingX — this caused 7,650 failed TTP closes (50% of all log entries).
2. Grade A worse than Grade B (3.3% vs 10.1% WR) — signal quality investigation needed.
3. LSG 75.8% + Avg MFE 0.937% suggests TP at 0.5-0.7% would capture most winners.
4. Beta bot needs overlaps removed before starting: LYN, GIGGLE, BEAT, TRUTH, STBL, BREV, Q, SKR, MUS.
5. Three audit items deferred for design discussion: H1 (BE/TTP coupling), H2 (exit price from state not fill), M1 (CSV header race), M2 (API rate limit batching), M3 (SL cancel-before-place race).

### State changes
- `scripts/build_phase1_diagnostics.py` — CREATED, py_compile PASS
- 6 diagnostic scripts created by phase 1 build
- `scripts/build_phase2_bot_fixes.py` — CREATED, BUILD OK
- `position_monitor.py` — PATCHED (reduceOnly removed + SL tighten added)
- `state_manager.py` — PATCHED (TTP columns added)
- `config.yaml` — PATCHED (sl_trail_pct_post_ttp: 0.003 added)
- `main.py` — PATCHED (check_ttp_sl_tighten wired in)
- `scripts/build_dashboard_v1_5.py` — CREATED, BUILD OK
- `bingx-live-dashboard-v1-5.py` — CREATED, py_compile + ast.parse PASS
- `scripts/build_phase4_beta_bot.py` — CREATED, BUILD OK
- `config_beta.yaml` — CREATED (44 coins, 20x leverage, $5 margin)
- `main_beta.py` — CREATED
- `beta/` and `beta/logs/` directories — CREATED
- `scripts/build_audit_fixes.py` — CREATED, BUILD OK, all 5 patches applied
- Phase 2 patches found to be ALREADY APPLIED from prior session (MISSING ANCHOR for P2-A and P2-B)

### Open items recorded
- Restart bot after patches
- Launch dashboard v1.5 and test Close Market + session equity curve
- Remove confirmed overlaps from config_beta.yaml then start main_beta.py
- Backtester TP sweep at 0.5-1.0x ATR range (LSG data supports tight TP hypothesis)

### Notes
- Phase 2 build script showed MISSING ANCHOR for P2-A and P2-B — both patches were already applied in a prior session (confirmed by reading actual files). This is a recurring pattern where prior sessions applied fixes not captured in earlier logs.
- The 109400 error is multi-cause: reduceOnly (fixed) AND timestamp drift (discovered 2026-03-05).

---

## 2026-03-04-position-management-study.md
**Date:** 2026-03-04
**Type:** Research/strategy session

### What happened
Research session documenting user's actual position management rules from live chart walkthroughs. Continuation of a previous session analyzing PUMPUSDT LONG and PIPPINUSDT SHORT trades. Focus was on trend-hold trades only (not quick rotations, 1min scalps, counter-trend). 5 of 13 open questions resolved this session. Charts reviewed: PUMPUSDT 4h (Bybit Spot) and PUMPUSDT 1h (Bybit Spot).

Two new trade type concepts documented: 1m EMA-Delta Scalp Concept (EMA delta threshold + stoch zone entry + TDI MA cross, fully automatable) and Probability-Based Trade Framework (Markov + Black-Scholes — replace hard thresholds with learned transition probabilities, 75 combined states, BBWP-to-BS bridge).

### Decisions recorded
1. HTF-1 resolved: 4h session bias determined by Ripster EMA cloud stack transitions; 1h confirmed by sequential cloud flips (Cloud 2 first, then 3, then 4) converging at structural level.
2. HTF-2 resolved: 15m MTF clouds NOT a hard binary filter — modulates hold duration, not entry permission.
3. ENTRY-1 resolved: All 4 stochastics confirm sequentially — enter when LAST stoch completes K/D cross.
4. BBW-1 resolved: Exact BBWP thresholds unknown — flagged for Vince to research via backtesting.
5. TDI-1 resolved: RSI period=9, RSI price smoothing=5, Signal line=10, Bollinger band period=34.
6. No code to be written until all questions resolved and user approves rules.

### State changes
- Study plan file updated: `C:\Users\User\.claude\plans\fizzy-humming-crab.md`
- Two concept plan files created: `2026-03-04-1m-ema-delta-scalp-concept.md` and `2026-03-04-probability-trade-framework.md`
- RULE VIOLATION recorded: `2026-03-04-markov-trade-state-research.md` was deleted without asking user. Content preserved in `2026-03-04-probability-trade-framework.md` but deletion was unauthorized.

### Open items recorded
- 7 questions still open: SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1, TP-1
- Next: resolve GATE-1 on PUMP first (user indicated this priority)

### Notes
- Rule violation logged in the file itself — unauthorized file deletion. This is the only session log reviewed so far that documents a rule violation in the session log (most violations are noted in MEMORY.md).

---

## 2026-03-05-bingx-bot-session.md
**Date:** 2026-03-05
**Type:** Build session + live bot monitoring

### What happened
Continuation from 2026-03-04 audit + patch session. Bot restarted with all fixes applied. Multiple significant events and builds:

1. Three-stage position management implemented: `be_act: 0.004` (BE raises at +0.4%), `ttp_act: 0.008` (TTP at +0.8%), `ttp_dist: 0.003` (trail 0.3%). Test script: 25/25 PASS.

2. orderId extraction bug fixed in 3 locations in position_monitor.py — was missing nested `order` key.

3. Unrealized PnL added to Telegram daily summary and hourly warnings.

4. max_positions increased from 15 to 25 via config.yaml.

5. Log review of 2026-03-04-bot.log (11,466 lines, 953KB) showed DNS outage at 13:15 (30+ CRITICAL alerts, self-recovered), several trades opened and closed.

6. Time Sync Fix (evening): Discovered bot and dashboard used raw `time.time() * 1000` without server sync. BingX rejects timestamps drifting >5 seconds (error 109400). User lost 17% due to this. Immediate fix: `w32tm /resync /force`. Permanent fix: `build_time_sync.py` creates `time_sync.py` module + patches 5 files (bingx_auth.py, main.py, executor.py, position_monitor.py, bingx-live-dashboard-v1-4.py).

7. Trade Analyzer v2 built (11 analysis sections, 3 output formats). Initial build had bugs fixed directly (CSV schema mismatch, ModuleNotFoundError dotenv, date filter). Build script SOURCE is now out of sync with output file.

8. ATR Investigation built and run — found 4 HIGH_VOL+ trades (atr_ratio > 1%) caused 66% of non-BE losses. Risk gate has no upper bound. Three recommended fixes: max_atr_ratio cap at 0.015, ATR-scaled position sizing, sl_atr_mult reduction from 2.0 to 1.5.

9. Trade Analyzer v2 results (57 trades, 2026-03-04 to 2026-03-05): 57.9% WR, net PnL -$0.694, post-rebate +$2.50. BE raised backbone (71.1% WR), TTP exits profit engine (+$9.59). Without BE+TTP, bot deeply negative.

10. Scaling analysis for $500 margin / 20x / $10k portfolio: 200x scale factor. Net +$500/57 trades post-rebate. Critical risk: Q-USDT (5.15% SL) would be liquidated before SL hits at 20x.

11. Dashboard v1.5 full debug chain (evening): Fixed store-bot-status KeyError, full line-by-line audit found 4 bugs (BUG-A through BUG-D), signing fix (100001 root cause: requests library re-encoding params), trades CSV loading fix (18-column bot vs 12-column header mismatch), Max DD % fix written (not yet run).

### Decisions recorded
1. Timestamp sync is root cause of many 109400 errors — permanent fix via time_sync.py module.
2. Three-stage position management adopted (BE at 0.4%, TTP at 0.8%, trail 0.3%).
3. max_atr_ratio cap recommended at 0.015 to block extreme-volatility entries.
4. Dashboard v1.5 signing must use manual URL-build approach (match bot's bingx_auth.py pattern), not requests.get() with params dict.
5. BE SL direction bug for SHORT noted but needs verification.
6. Dashboard v1-4 settings save does not write `be_act` — do NOT save settings from v1-4 until v1.5 fixes this.

### State changes
- `config.yaml` patched: be_act, ttp_act, ttp_dist, max_positions
- `position_monitor.py` patched: orderId extraction (3 locations), unrealized PnL method, three-stage logic
- `signal_engine.py` patched: fallback defaults updated
- `time_sync.py` CREATED
- `bingx_auth.py`, `main.py`, `executor.py`, `position_monitor.py`, `bingx-live-dashboard-v1-4.py` all patched with .bak backups
- `scripts/build_time_sync.py` CREATED
- `scripts/test_three_stage_logic.py` CREATED (25/25 PASS)
- `scripts/build_trade_analyzer_v2.py` CREATED
- `scripts/run_trade_analysis_v2.py` CREATED
- `scripts/build_atr_investigation.py` CREATED
- `scripts/run_atr_investigation.py` CREATED
- `scripts/build_dashboard_v1_5_full_audit_fix.py` CREATED (8 patches)
- `scripts/build_dashboard_v1_5_signing_fix.py` CREATED
- `scripts/build_dashboard_v1_5_trades_refresh.py` CREATED
- `scripts/build_dashboard_v1_5_drawdown_fix.py` CREATED (not yet run)

### Open items recorded
- P1: dashboard_v395.py — add require_stage2 checkbox, rot_level slider, "Load v384 Live Preset" button
- P2: BE SL direction bug for SHORT needs verification
- Dashboard v1.5 Max DD % fix pending (script written, not run)
- Bot restart required to activate time_sync.py patches
- Beta bot still needs overlap removal before starting

### Notes
- 109400 error has TWO root causes: (1) reduceOnly in Hedge mode (fixed 2026-03-04), (2) timestamp drift (fixed 2026-03-05). Prior logs attributed all 109400 to reduceOnly — this is now corrected.
- Trade Analyzer v2 build script SOURCE is out of sync with output file (3 fixes applied directly to output).
- Dashboard v1.5 was built before time_sync was added — BUG-A in the full audit found this gap.

---

## 2026-03-05-bingx-data-fetcher-and-updater.md
**Date:** 2026-03-05
**Type:** Build session

### What happened
Continued from 2026-03-04 session. Built BingX OHLCV bulk fetcher, daily incremental updater, and autorun scheduler for the four-pillars-backtester project.

BingX OHLCV Bulk Fetcher (`fetch_bingx_ohlcv.py`): Discovers all BingX USDT perpetual futures (~626 coins), fetches 1m OHLCV going back 12 months per coin, saves to `data/bingx/` as parquet + .meta, also resamples to 5m. Schema matches Bybit data (8 columns). Progress bars: outer (coins, fractional) + inner (per-coin %). CLI flags: --dry-run, --symbol, --max-coins, --months, --skip-existing, --output-dir, --resume-from. 6 bugs fixed from audit. Progress bar fix: outer bar was stuck at 0/626 — fixed with fractional advancement via `_update_outer()`.

BingX Daily Updater (`daily_bingx_update.py`): Imports functions from fetch_bingx_ohlcv.py (zero code duplication), reads .meta files, fetches only the gap, discovers new coins, skips coins less than 2 hours behind. CLI: --dry-run, --skip-new, --skip-resample, --max-new, --months. Logs to dated log file.

Autorun Scheduler (`data_scheduler.py`): Runs Bybit and BingX daily updaters on timed schedule (default 6h). CLI: --interval, --bingx-only, --bybit-only, --once. Designed to run in background terminal.

### Decisions recorded
1. BingX data stored in `data/bingx/` — separate from Bybit's `data/cache/`.
2. Zero code duplication — daily updater imports fetch functions, doesn't duplicate them.
3. quote_vol = NaN for BingX (API doesn't provide turnover).

### State changes
- `scripts/build_fetch_bingx.py` — UPDATED (progress bar, bug fixes, tqdm import)
- `scripts/fetch_bingx_ohlcv.py` — UPDATED (fractional outer bar, all bug fixes)
- `scripts/build_daily_bingx_updater.py` — NEW
- `scripts/daily_bingx_update.py` — created by build script
- `scripts/build_data_scheduler.py` — NEW
- `scripts/data_scheduler.py` — created by build script
- Data status: Bybit 399 coins (stale since 2026-02-13), BingX ~292 of 626 completed as of session start

### Open items recorded
- Bulk fetch still in progress (~292 of 626 completed) — expected ~52 hours total
- Bybit data stale since 2026-02-13 — daily updater also applies to Bybit

### Notes
- BingX OHLCV fetcher was started in 2026-03-04 session; progress bar fixes were applied in this 2026-03-05 session.

---

## 2026-03-05-project-review-volume-uml.md
**Date:** 2026-03-05
**Type:** Session log (review/documentation)

### What happened
Project review session. Read INDEX.md, key log files, and UML files. Read full trades.csv (300+ rows) for volume analysis. Produced full project brief and volume/rebate analysis for $10k/$500/20x scenario. Updated UML file.

UML update to `uml/strategy-system-flow.md` (updated from 2026-02-16 to 2026-03-05): State machine updated (C signal removed, v386 2026-02-28), dashboard updated (v3.9.4, CUDA GPU Sweep), ExitManager annotated as likely dead code, new Page 1b (BingX live bot system diagram), ML training/validation chains updated with blockers, new Page 3 (Vince ML build chain B1-B6), new Page 4 (signal architecture post-rename).

Volume analysis: $50 margin, 10x leverage = $500 notional/trade. ~70 trades/day = ~$70k daily notional. At $10k account, $500 margin, 20x: $10,000 notional/trade, ~$1.4M daily notional.

### Decisions recorded
None explicitly made — this was a review session.

### State changes
- `uml/strategy-system-flow.md` — UPDATED (full rewrite, 2026-02-16 to 2026-03-05)

### Open items recorded
Phase 0 blockers still unresolved (Q1-Q6 listed).
Signal rename pending (final name for B/Rotation).
Beta bot overlaps still need removal.

### Notes
- Open questions listed are unchanged from 2026-03-03 roadmap — no progress on Phase 0 questions in this period.

---

## BUILD-JOURNAL-2026-02-13.md
**Date:** 2026-02-13
**Type:** Build session (multi-session journal)

### What happened
Multi-session build journal covering 6 sessions on 2026-02-13.

Session 1: Built `download_all_available.py` for 399-coin data fill (bidirectional, restartable, backup-first). Built `dashboard_v2.py` with 3 DataFrame fixes, Streamlit API fixes, logging. RULE VIOLATION documented: used Edit tool directly instead of build script.

Session 2: Created `DASHBOARD-VERSIONS.md`. Confirmed cooldown parameter already fully configurable. Scoped P1-P5 backlog items. Recommended execution order: P2 > P3 > P4 > P1(B) > P5.

Session 3: Created `DASHBOARD-V3-BUILD-SPEC.md` — 6-tab VINCE control panel full architecture spec with 6 tabs, LSG categorization, VINCE blind training protocol, ~45 column sweep CSV.

Session 4: Reviewed monolithic spec, found 6 problems (emojis, scope creep, etc.), split into 3 separate specs: SPEC-A-DASHBOARD-V3.md (UI only), SPEC-B-BACKTESTER-V385.md (engine changes), SPEC-C-VINCE-ML.md (ML architecture).

Session 5: Cross-checked all 3 specs against actual source files. Found and fixed 10 issues. Key finding: BBWP exists only in Pine Script — no Python implementation. 3 fields deferred until BBWP Python port.

Session 6: Built `scripts/build_all_specs.py` (2189 lines) to generate all 9 output files from specs A, B, C. All generators produce valid Python (ast.parse verified). Fixed 2 critical bugs during review: `super().run()` signature mismatch and `import logging.handlers` placement.

### Decisions recorded
1. HARD RULE VIOLATION rule added to MEMORY.md: "DOUBLE CONFIRM SHORTCUTS — When tempted to take a shortcut, STOP and ask the user first."
2. Staging folder approach chosen over direct overwrite for dashboard deployment.
3. 3-spec split architecture: Spec A standalone, Spec B adds engine metrics, Spec C adds ML.
4. BBWP Python port deferred — separate future spec needed.
5. Backtester v385 uses two-pass design: v384 logic unchanged, post-process enrichment added.
6. Recommended backlog execution order: P2 > P3 > P4 > P1(B) > P5.

### State changes
- `scripts/download_all_available.py` — CREATED
- `scripts/dashboard_v2.py` — CREATED (RULE VIOLATION: direct Edit instead of build script)
- `DASHBOARD-VERSIONS.md` — CREATED
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC.md` — CREATED (1009L)
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC-REVIEW.md` — CREATED
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-SUGGESTIONS.md` — CREATED
- `PROJECTS/four-pillars-backtester/SPEC-A-DASHBOARD-V3.md` — CREATED + corrected
- `PROJECTS/four-pillars-backtester/SPEC-B-BACKTESTER-V385.md` — CREATED + corrected
- `PROJECTS/four-pillars-backtester/SPEC-C-VINCE-ML.md` — CREATED + corrected
- `scripts/build_all_specs.py` — CREATED (2189L), all 9 generators ast.parse verified

### Open items recorded
- User still has not run `build_staging.py` from 2026-02-12 Phase 3.
- `build_all_specs.py` written but user must run it.

### Notes
- This is the earliest log in batch 10 (2026-02-13 vs other 2026-03-xx logs). Provides historical context.
- BBWP finding here (no Python port) was still unresolved in 2026-03-xx sessions (BBW-1 open question in position-management-study).

---

## build_journal_2026-02-11.md
**Date:** 2026-02-10 to 2026-02-11
**Type:** Build session (multi-phase journal)

### What happened
Earliest journal in this batch. Multi-phase build session for Four Pillars ML backtester pipeline.

Phase 1: Built 11 missing infrastructure files across strategies/, engine/, optimizer/, ml/, gui/. 10 written (1 skipped — already existed). 19/19 tests passed.

Phase 2: Comprehensive inventory of 62 Python files. Identified 4 remaining gaps: missing ML dashboard tabs, missing dashboard test script, WEEXFetcher import bug, ml/live_pipeline.py not built.

Phase 3: Built `build_staging.py` (1692L) to create: staging/dashboard.py (5-tab ML dashboard), staging/test_dashboard_ml.py, staging/run_backtest.py (WEEXFetcher bug fixed), staging/ml/live_pipeline.py. Status: written, NOT YET RUN.

Phase 4: Built complete v3.8.3 Python backtester — 4-stage state machine, A/B/C/D/ADD/RE/R signals, ATR SL, AVWAP trailing, scale-out mechanism. 8 source files + 3 results files. Key result: SL=2.5 ATR best (9/10 coins profitable), LSG 85-92%.

Phase 5: Built v3.8.4 — adds optional ATR-based take profit. TP sweep results: No TP baseline +$6,261, TP=2.0 ATR +$7,911 (only level beating baseline), TP=0.50 catastrophic (-$5,095). Multi-coin sweep confirmed TP=2.0 NOT universal: KITE and BERA both worse with TP=2.0.

Phase 6: Referenced BUILD-JOURNAL-2026-02-12.md for dashboard overhaul + data normalizer.

### Decisions recorded
1. Staging folder approach for safe deployment (user's choice).
2. v3.8.3 designed with 4-slot engine, execution order: exits -> update -> scale -> pending -> entries -> adds -> re-entry.
3. v3.8.4 TP is optional (--tp-mult, default None = no TP).
4. SL checked before TP (pessimistic) when both could trigger.
5. TP=2.0 ATR is coin-specific, not universal — per-coin optimization needed.
6. WEEXFetcher bug fixed in staging only, production run_backtest.py retains old import.

### State changes
- `strategies/base_strategy.py` — SKIPPED (existed)
- 10 new infrastructure files created (exit_manager, indicators, signals, cloud_filter, four_pillars_v3_8, walk_forward, aggregator, xgboost_trainer, coin_selector, parameter_inputs)
- `scripts/build_staging.py` — CREATED (not yet run)
- v3.8.3 files: state_machine_v383.py, four_pillars_v383.py, position_v383.py, backtester_v383.py, run_backtest_v383.py, sweep_sl_mult_v383.py, test_v383.py, mfe_analysis_v383.py, capital_analysis_v383.py, validation_v371_vs_v383.py
- v3.8.4 files: position_v384.py, backtester_v384.py, run_backtest_v384.py, sweep_tp_v384.py, capital_analysis_v384.py
- `engine/commission.py` — modified to add volume tracking
- Results: sweep_v383_sl_mult.md, mfe_analysis_v383.md, validation_v371_vs_v383_RIVERUSDT.md, sweep_v384_tp_RIVERUSDT.md, KITEUSDT.md, BERAUSDT.md

### Open items recorded
- Run TP sweep on KITE and BERA (done in Phase 5 but originally listed as remaining)
- Deploy staging files (`build_staging.py` not yet run)
- ML meta-label on D+R grades
- Live TradingView validation (Pine Script vs Python)
- Multi-coin sweep with more coins
- BE raise optimization (LSG 85-92% opportunity)

### Notes
- v3.8.4 LSG 85-92% finding here is the earliest documented mention of this figure. Later logs reference "LSG 75.8%" for the live bot trades — these are different datasets (backtester vs live trades).
- LSG = "Loser Saw Green" (losers that reached unrealized profit before closing).
- This log predates the BingX connector work by ~9 days.

---

## PENDING-TASKS-MASTER.md
**Date:** Generated 2026-02-24
**Type:** Planning / task registry

### What happened
Master summary of all pending tasks as of 2026-02-24, compiled from source logs. Not a session log — a curated reference document.

Contains 14 items across priority levels: IMMEDIATE (2), HIGH PRIORITY BLOCKED (3), MEDIUM PRIORITY (4), LOWER PRIORITY (5), STRATEGY FIXES (1 section), DEFERRED (4 items), PRODUCT BACKLOG (7), and COMPLETED BUILDS reference (18 entries).

Key items:
- IMMEDIATE #1: Vince v2 Concept approval + Trading LLM scope + Plugin Interface Spec + Four Pillars Plugin Spec
- IMMEDIATE #2: WEEX Live Market Screener Build (scope approved, not started)
- HIGH #3: Dashboard v3.9.3 equity curve date filter bug — BLOCKED (build script works, generated file has syntax error, fix script has logic error)
- HIGH #4: Four Pillars Strategy Scoping — 19 unknowns remaining
- HIGH #5: BingX Live Trading — connector done (67/67 tests), open decisions block live config
- STRATEGY FIXES: 5-phase plan — R:R ratio inverted (TP=2.0 ATR, SL=2.5 ATR → R:R=0.8), BE raise logic removed in v3.8.x refactor must be restored

### Decisions recorded
None (this is a reference document, not a session log).

### State changes
None (document records state, not changes).

### Open items recorded
All items listed in the document are open items as of 2026-02-24. Notable:
- Dashboard v3.9.3 blocked on indentation fix logic error
- WEEX screener approved but not built
- 19 strategy unknowns unresolved
- BingX config decisions pending
- build_staging.py still not run (referenced from 2026-02-11 journal)

### Notes
- This document is dated 2026-02-24 — approximately 9-10 days before the other logs in this batch. Many items listed as open here were addressed in the 2026-03-03 to 2026-03-05 logs.
- Dashboard v3.9.3 bug noted here — separate from BingX dashboard (bingx-live-dashboard). This refers to the backtester dashboard.
- WEEX screener scope approved here — later logs reference BingX screener, not WEEX. Context shift occurred.
- Completed builds list (C.1-C.18) provides useful reference for what was done before 2026-02-24.

---

## commission-rebate-analysis.md
**Date:** 2026-02-07
**Type:** Strategy spec / analysis document

### What happened
Commission and rebate analysis document for Four Pillars v3.7.1 on WEEX exchange. Establishes correct commission math, rebate impact, expectancy calculations, and breakeven raise scenarios.

Key finding: v3.7 Pine Script used `strategy.commission.percent=0.06` which applied to cash ($500), giving $0.30/side instead of correct $6.00/side on $10k notional. This caused the backtester to show profit while the real account lost money.

Correct Pine Script: `commission_type=strategy.commission.cash_per_order, commission_value=6`.

Rebate math: Account 1 (70% rebate) = $8.40 rebate/RT, net $3.60/RT. Account 2 (50% rebate) = $6.00 rebate/RT, net $6.00/RT. Rebates settle daily 5pm UTC.

Expectancy: v3.7.1 gross $12.62/trade, after 70% rebate $9.02/trade = $902/month at 100 trades.

Breakeven+$2 raise scenario: converts 86% of losers (those that saw green) to small winners. Gross jumps from $12.62 to $41.13/trade. With 70% rebate: $37.53/trade = $3,753/month at 100 trades.

Backtester must model daily rebate settlement (actual credit at 5pm UTC), not simplified percentage reduction, because timing difference affects drawdown calculations.

### Decisions recorded
1. Pine Script must use `cash_per_order` not `commission.percent` for leveraged strategies.
2. Commission rate: 0.06% per side on notional (WEEX).
3. BE raise threshold optimal value is unknown — optimizer must test $2/$5/$10/$20 variants.
4. Daily rebate settlement must be modeled explicitly in backtester (timing matters for drawdown).

### State changes
None — this is an analysis document, not a build session.

### Open items recorded
- Backtester must validate: exact LSG figure, $2 raise feasibility, noise stop-outs, regime sensitivity, daily rebate settlement modeling.

### Notes
- This is the oldest document in this batch (2026-02-07). It documents WEEX exchange specifics — later work shifted to BingX.
- The 86% LSG figure cited here is from TradingView backtester (v3.7.1). Later Python backtester logs cite 85-92% LSG — consistent range. Live bot trades show 75.8% LSG.
- Commission rates differ between documents: WEEX = 0.06% (this doc), BingX = 0.08% (later docs). Different exchanges.
- The "rebate farming" concept documented here is the foundational framework referenced throughout later sessions.


# Research Batch 11 — Findings
**Files:** 2026-02-03 through 2026-02-14 build journals and session logs
**Generated:** 2026-03-06

---

## 2026-02-03-build-journal.md
**Date:** 2026-02-03
**Type:** Build session

### What happened
Eight sessions focused on Pine Script indicator development. Sessions 1-2 audited existing indicators and refined the Quad Rotation Stochastic (QRS) spec. Session 3 ran 5,000-scenario statistical testing on angle calculation approaches; selected the "agreement multiplier" method. Session 4 validated with 5,000-sample testing, yielding 92.4% win rate; created complete Pine Script v6 build spec. Session 5 found 9 major bugs in the spec; re-validation showed 92.1% win rate with 5-bar lookback. Session 6 conducted critical code review and found 11 major implementation bugs (stochastic calc, 60-10 double smoothing, state machine, divergence tracking, alert naming, missing alerts, rotation clarity, JSON payload issues). Session 7 fixed all 11 bugs and added edge detection to all alerts. Session 8 built the Quad Rotation FAST v1.1 spec (9-3 + 14-3 primary triggers, 40-4/60-10 slow context) and found/fixed 5 more bugs.

### Decisions recorded
- Selected agreement multiplier approach for angle calculation (over composite angle and average angles)
- 5-bar lookback for divergence detection
- 60-10 requires DOUBLE smoothing (SMA of SMA)
- State machine must use if/else if chains, not multiple if blocks
- Edge detection pattern: `signal and not signal[1]` fires once

### State changes
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-v4-BUILD-SPEC.md` created (v4.1)
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-FAST-BUILD-SPEC.md` created (v1.1)
- `skills/pinescript/SKILL.md` updated to v2.0
- `skills/pinescript/references/technical-analysis.md` created
- `skills/n8n/SKILL.md` created

### Open items recorded
1. Build v4.1 Pine Script in Claude Code
2. Build FAST v1.1 Pine Script in Claude Code
3. Test both on TradingView
4. Set up n8n webhook integration

### Notes
None.

---

## 2026-02-04-build-journal.md
**Date:** 2026-02-04
**Type:** Build session

### What happened
Eight sessions of Pine Script work and strategy spec development. Session 1: FAST v1.3 build with philosophy correction; FAST v1.4 selected as production. Session 2: reviewed AVWAP Anchor Assistant (fixed VSA alert edge-triggering), QRS indicators (fixed 40-4 smoothing from 4 to 3 — Kurisko original), and BBWP v2 (added MA cross persistence timeout 10 bars, timestamp display, hidden plots). Session 3: CRITICAL — v1.0 spec referenced "Stoch 55" which doesn't exist in any built indicator. Created corrected `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` with 40-4 divergence as SUPERSIGNAL and 9-3 for exit management. Session 4: Added 15 hidden plots to `ripster_ema_clouds_v6.pine` for Four Pillars integration (cloud states, price position, cloud direction, crossovers, scores, raw EMAs). Session 5: Built `four_pillars_v2.pine` (~500 lines) implementing all 4 pillars, grade calculation (A/B/C/No Trade), position management, dashboard, stochastic mini panel, 11 alert conditions. Session 6-8: Built `four_pillars_v3.pine` (v3.1-v3.3) with clean Quad Rotation logic using 9-3 as trigger, 3-bar lookback, dynamic SL (1x or 2x ATR based on Ripster cloud), then updated filters through v3.2 (40-3 D line position) and v3.3 (60-10 D line, fixed 20/80 thresholds).

### Decisions recorded
- FOUR-PILLARS-STRATEGY-v1.0 deprecated — it was built before Kurisko methodology was researched
- 40-4 smoothing is 3 (not 4) — Kurisko original
- 40-4 divergence is SUPERSIGNAL (highest priority)
- 9-3 is TRIGGER (fastest stochastic), all others must be in zone
- 3-bar lookback for "in zone" check
- 60-10 D filter fixed at 20/80 (not tied to input)
- `FOUR-PILLARS-COMBINED-BUILD-SPEC.md` deprecated

### State changes
- `Quad-Rotation-Stochastic-FAST.pine` — 40-4 smoothing fixed
- `Quad-Rotation-Stochastic-v4-CORRECTED.pine` — 40-4 smoothing fixed, hidden plot added
- `avwap_anchor_assistant_v1.pine` — edge-triggered VSA alerts
- `bbwp_v2.pine` — MA cross timeout + timestamp + hidden plots
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` — NEW
- `ripster_ema_clouds_v6.pine` — 15 integration hidden plots added
- `four_pillars_v2.pine` — NEW combined indicator
- `four_pillars_v3.pine` — v3.3 with 60-10 D filter

### Open items recorded
1. Create strategy version of v3 for backtesting
2. Add trailing stop logic
3. Test all indicators in TradingView
4. Set up n8n webhook integration

### Notes
Root cause of v1.0 spec error identified: strategy was conceptualized on 2026-01-29 before Kurisko methodology was researched. Spec v1.0 was never updated after QRS indicators were built correctly.

---

## 2026-02-05-build-journal.md
**Date:** 2026-02-05
**Type:** Build session

### What happened
Eleven sessions of Pine Script strategy development. Session 1: Reviewed v3.4.1 strategy, hit context limit. Session 2: Added `i_useTP` and `i_useRaisingSL` toggles to indicator (v3.4.2); changed Phase 3 trail from Cloud 3 to Cloud 4. Session 3: Major SL overhaul — removed entire phased P0-P3 system and replaced with continuous Cloud 3 (34/50) ± 1 ATR trail every candle; added Cloud 2 re-entry A trade; removed Cloud 2 flip hard close exit; file reduced 645 → ~495 lines. Session 3b: Added trail activation gate (Cloud 3/4 cross), entry position replacement logic, priority reorder (re-entry A above B/C), inverse SL bug fix. Session 4: Created `four_pillars_v3_5.pine` — stochastic smoothing fix (all 4 stochastics now use raw K, 60-10 double smoothed). Session 5: Built `four_pillars_v3_5_strategy.pine` from scratch — pyramiding=1, smoothed stochastics, trail activation gate, no Cloud 2 exit, A-only direction flips. Session 6: Fixed 3 bugs (dual exit conflict, position replacement invisible, state desync after exit). Session 7: Removed position replacement (was killing winners and creating margin-call fragments). Session 8: v3.5.1 — CRITICAL root cause: "Stoch 9 1 3" means K smoothing=1 (raw K, no SMA). v3.5's "smoothing fix" made values equivalent to D line. Reverted to raw K. Also fixed position sizing ($500 fixed vs 100% equity) and B/C defaults (OFF by default). Sessions 9-11: Built v3.6 with AVWAP trailing, separate A/BC order IDs, BC exits on Cloud 2 cross or 60-10 K/D cross, Cloud 3/4 parallel filter for BC, AVWAP recovery re-entry, volume flip filter, dashboard fix.

### Decisions recorded
- Phased SL system (P0-P3) removed — replaced with continuous Cloud 3 trail
- No position replacement (kills winners)
- Stochastic K uses raw K (smooth=1) — matches "Stoch 9 1 3" setting in TradingView
- B/C defaults OFF — user must opt in
- A trades can flip direction; B/C/RE can only enter flat
- Volume flip filter applies ONLY to A direction flips, not fresh flat entries
- `var table dash` must be at global scope (not inside conditional block)

### State changes
- `four_pillars_v3_4.pine` updated to v3.4.2
- `four_pillars_v3_5.pine` NEW — v3.5.1
- `four_pillars_v3_5_strategy.pine` NEW — v3.5.1
- `four_pillars_v3_6_strategy.pine` NEW — v3.6
- `four_pillars_v3_6.pine` NEW — v3.6 indicator

### Open items recorded
None explicitly listed.

### Notes
Critical lesson captured: stochastic smoothing regression in v3.5 was caused by misunderstanding "Stoch 9 1 3" — the middle "1" is K smoothing (raw K), not D smoothing. Applying SMA(K,3) made values equivalent to D line, causing strategy to see midrange values while real K was in extreme zones.

---

## 2026-02-06-build-journal.md
**Date:** 2026-02-06
**Type:** Build session

### What happened
Two main sessions. Session 1: Built `four_pillars_v3_7_strategy.pine` — "rebate farming" architecture with tight static SL (1.0 ATR) and TP (1.5 ATR), free flips on any A/B/C signal, tracking bars since last ANY signal (not just A), single order ID, 3-bar cooldown. Session 2: CRITICAL BUG — `commission.percent=0.06` applies to CASH qty ($500), not notional ($10K with 20x leverage). Reality: $6/side = $12 round trip, not $0.30/0.60. Combined with phantom trade bug (`strategy.close_all()` + `strategy.entry()` = 2 trades per flip = $24/flip). Emergency fix in `four_pillars_v3_7_1_strategy.pine`: changed to `cash_per_order=6`, flip via `strategy.entry()` only (auto-reverses), added `strategy.cancel()` before every flip, 3-bar cooldown on ALL entry paths, running commission total in dashboard. Also exported CSV for validation from TradingView backtest.

### Decisions recorded
- commission.percent on leveraged strategies is wrong — must use cash_per_order
- cash_per_order=6 for $10K notional at 0.06% taker rate
- strategy.close_all() + strategy.entry() creates 2 trades (phantom trade bug) — use strategy.entry() only (auto-reverses)
- Cooldown must apply to ALL entry paths (A, BC, flip, re-entry)
- entryBar does NOT reset on exit — persists between trades

### State changes
- `four_pillars_v3_7_strategy.pine` NEW — rebate farming
- `four_pillars_v3_7_1_strategy.pine` NEW — commission fix + cooldown
- `four_pillars_v3_7_1.pine` NEW — indicator version
- Exported backtest CSV: `07-TEMPLATES/4Pv3.4.1-S_BYBIT_MEMEUSDT.P_2026-02-06_fcc84.csv`

### Open items recorded
1. Build Python backtester to validate v3.7.1 with correct commission
2. Test breakeven+$X raise on historical data
3. Fetch historical data for multiple coins

### Notes
Commission bug was previously undetected. $0.30 vs $6 per side is a 20x error. All prior TradingView backtests were underestimating commission costs by 20x for leveraged strategies.

---

## 2026-02-07-build-journal.md
**Date:** 2026-02-07
**Type:** Build session

### What happened
Six sessions covering planning, skill updates, full Python backtester build, live data, and CUDA installation. Session 1: Created master execution plan (WS1-WS5) — five workstreams from data pipeline to Monte Carlo validation. Session 2: Completed WS1 (Pine Script skill update) and WS2 (two progress documents). Session 3: Built complete Python backtester from scratch in `PROJECTS/four-pillars-backtester/` — data pipeline (Bybit v5 API, backward pagination, WEEX had no historical pagination), signal engine (raw K stochastics, Ripster clouds, A/B/C state machine), backtest engine (bar-by-bar loop, MFE/MAE tracking, position class with breakeven raise, commission + rebate settlement, metrics). Session 4: Fetched 3-month 1m data for 5 low-price coins; ran BE sweeps. Results: 1m = mostly negative (only RIVER profitable at +$87K), 5m = ALL PROFITABLE (total +$97K across 5 coins, 20,283 trades, $4.79/trade). Session 5: Built `scripts/fetch_sub_1b.py` using CoinGecko for market cap filtering + Bybit for candle data; discovered 394 sub-$1B coins; kicked off overnight fetch at 19:53. Session 6: Installed NVIDIA CUDA 13.1 toolkit; confirmed RTX 3060 12GB VRAM, driver 591.74. PyTorch, Optuna, XGBoost NOT installed yet.

### Decisions recorded
- Bybit v5 API for historical data (WEEX has no pagination for historical)
- Raw K (smooth=1) for all 4 stochastics in Python
- 5m timeframe superior to 1m — all coins profitable vs mostly negative
- Sub-$1B market cap = coin universe for backtesting

### State changes
- `.claude/plans/warm-waddling-wren.md` NEW — Master plan WS1-WS5
- Pine Script skill files updated
- `07-BUILD-JOURNAL/2026-02-07-progress-review.md` NEW
- `07-BUILD-JOURNAL/commission-rebate-analysis.md` NEW
- `PROJECTS/four-pillars-backtester/` created (entire tree)
- `data/cache/*.parquet` — 5 coins' 3-month 1m data
- `data/sub_1b_coins.json` — 394 coin list
- `scripts/fetch_sub_1b.py` NEW

### Open items recorded
1. Wait for overnight fetch (ETA ~02:00)
2. Install PyTorch with CUDA (user task)
3. Run 299-coin backtest on 5m
4. Build v3.8 ATR-based BE module

### Notes
Key discovery logged: 5m timeframe makes ALL coins profitable. Commission bleed on 1m (~20K trades) overwhelms edge. Bug fixed during dev: `df.set_index('datetime')` removes datetime from columns → rebate settlement never triggered. Fixed by checking `df.index.name`.

---

## 2026-02-08-build-journal.md
**Date:** 2026-02-08
**Type:** Build session

### What happened
Overnight fetch completed (started 2026-02-07 19:53:55, completed 2026-02-08 02:18:49, ~6.5 hours). Results: 394 total coins discovered, 363 successfully fetched, 31 failed (rate limited), 299 full data (>3MB, 3 months), 70 partial/tiny, 38.5M total candles, 1.36 GB on disk. Data quality: zero gaps, zero NaN, zero dupes, zero bad prices across all 299 complete coins. Issues: RIVER + SAND data overwritten, 31 coins rate-limited (needs backoff improvement), 70 partial fetches. Created comprehensive handoff document `07-BUILD-JOURNAL/2026-02-09-session-handoff.md` for context continuity.

### Decisions recorded
None explicitly stated — this was primarily a results recording session.

### State changes
- `data/cache/*.parquet` — 369 Parquet files (1.36 GB)
- `data/fetch_log.txt` — 2,479 lines
- `data/refetch_list.json` — 101 entries (31 failed + 70 incomplete)
- `07-BUILD-JOURNAL/2026-02-09-session-handoff.md` NEW — handoff document

### Open items recorded
- Install PyTorch (user task)
- Refetch 101 coins (needs `--refetch` flag)
- RIVER + SAND re-fetch
- v3.8 ATR-based BE module
- 299-coin full backtest
- WS3D exit strategy comparison
- WS4 ML optimizer (blocked on PyTorch)
- WS5 v4 + Monte Carlo (blocked on WS4)

### Notes
RIVER and SAND data were overwritten during sub-$1B fetch run (data quality issue from 2026-02-07 session).

---

## 2026-02-09-build-journal.md
**Date:** 2026-02-09
**Type:** Build session

### What happened
Session focused on book analysis and VINCE upgrade planning. 9 books analyzed and rated: Maximum Adverse Excursion (Sweeney, 9/10), Advances in Financial ML (De Prado, 9/10), ML for Algorithmic Trading (Jansen, 8/10), Trade Your Way to Financial Freedom (Van Tharp, 7/10), AI in Finance (Hilpisch, 5/10), RL for Finance (Hilpisch, 4/10), Python for Algo Trading (Hilpisch, 3/10), Listed Volatility Derivatives (Hilpisch, 1/10), Derivatives Analytics (Hilpisch, 1/10). VINCE upgrade plan synthesized from all books: 6 priority upgrades identified (drawdown constraint in Optuna, pre-entry XGBoost features, ATR regime gate, Sortino objective, data augmentation, options flow filter). Items deemed NOT worth doing: RNN for price prediction, DQL trading agent, options pricing models. Andy project skill created for FTMO prop trading ($200K, cTrader). Installed pymupdf4llm. PyTorch CUDA installed: `torch-2.10.0+cu130` on RTX 3060 12GB. Data refetch complete: 99 coins re-fetched, 0 failures, cache now 399 files / 1.74 GB. RIVER + SAND restored.

### Decisions recorded
- Sortino ratio preferred over Sharpe (downside-only risk, non-normal returns)
- Drawdown constraint: if max_drawdown > 10%, return float('-inf') in Optuna objective
- Pre-entry features: 11 features including stoch values, cloud distance, ATR percentile, volume ratio
- Half-Kelly or fractional Kelly for position sizing (not full Kelly)
- RNN for price prediction deemed not worth doing
- Andy project separated from Four Pillars (own skill, own rules)

### State changes
- `.claude/skills/andy/andy.md` NEW
- All project skills updated (four-pillars-project, vince-ml, andy)
- Data cache: 399 files / 1.74 GB (RIVER + SAND restored)
- PyTorch CUDA 2.10.0+cu130 installed
- pymupdf4llm installed

### Open items recorded
- Full 399-coin backtest on 5m
- WS4 ML optimizer
- WS4B MFE/MAE depth analysis
- De Prado concepts: Meta-Labeling, Purged CV, Triple Barrier comparison

### Notes
LSG 86% figure mentioned in 2026-02-07 progress review is confirmed here via book synthesis context.

---

## 2026-02-10-build-journal.md
**Date:** 2026-02-10
**Type:** Build session

### What happened
v3.8 BE sweep complete: 60 backtests (5 coins x 12 BE configs), saved to PostgreSQL run_id 2-61. Fixed-$ BE wins on ALL coins vs ATR-based BE. ATR trigger distances too wide for low-price coins. Cloud 3 filter impact measured: blocks ~67% of trades, per-trade quality drops from $4.79 to $3.79 (filter too aggressive for rebate farming). Added ATR-based BE raise to `engine/position.py` (be_trigger_atr + be_lock_atr params). Built 399-coin sweep script `scripts/sweep_all_coins.py` with auto-discovery, 5m timeframe, PostgreSQL save, CSV/JSON/log output, dry-run/no-db/top-N CLI flags. Established MEMORY.md hard rules: OUTPUT = BUILDS ONLY, NO FILLER, NO BASH EXECUTION, NEVER use emojis.

### Decisions recorded
- Fixed-$ BE superior to ATR-based BE on all tested coins
- Cloud 3 filter too aggressive for rebate farming volume strategy
- Hard rules established for all future sessions

### State changes
- ATR-based BE raise added to `engine/position.py`
- `engine/backtester.py` — pass-through to Position constructor
- `scripts/sweep_all_coins.py` NEW — 399-coin sweep
- `MEMORY.md` — hard rules added
- PostgreSQL: run_id 2-61 (60 backtests)
- Ollama prompt: `trading-tools/prompts/SWEEP-ALL-COINS-PROMPT.md`

### Open items recorded
1. Run `python scripts/sweep_all_coins.py`
2. Optuna on top 10 coins
3. MFE/MAE depth analysis from PostgreSQL
4. ML pipeline (ml/ directory)

### Notes
None.

---

## 2026-02-11-build-journal.md
**Date:** 2026-02-11
**Type:** Build session

### What happened
Three-phase build to complete all missing infrastructure files. Phase 1: `scripts/build_missing_files.py` (1570 lines) created 10 of 11 missing files (1 skipped — already existed from Qwen build): exit_manager.py, indicators.py, signals.py, cloud_filter.py, four_pillars_v3_8.py, optimizer/walk_forward.py, optimizer/aggregator.py, ml/xgboost_trainer.py, gui/coin_selector.py, gui/parameter_inputs.py. 19/19 tests passed. Phase 2: Full codebase inventory — 52 executable Python files + 2 Pine Script files, ~8,600+ lines total. Gaps identified: dashboard missing ML tabs, test script missing, WEEXFetcher import bug in run_backtest.py, ml/live_pipeline.py not built. Phase 3: `scripts/build_staging.py` (1692 lines) written to create 4 staging files (dashboard.py 5-tab ML dashboard, test_dashboard_ml.py, run_backtest.py fix, staging/ml/live_pipeline.py). Build script written but NOT YET RUN. Added SCOPE OF WORK FIRST rule to MEMORY.md. Updated Vince ML Build Status: all 9 ML modules now BUILT. MEMORY.md trimmed to 184 lines.

### Decisions recorded
- SCOPE OF WORK FIRST rule added: (1) Define scope, (2) List permissions, (3) Get approval, (4) Build
- Dashboard 5-tab layout: Overview, Trade Analysis, MFE/MAE & Losers, ML Meta-Label, Validation
- Live pipeline: WebSocket bar → rolling buffer → indicators → state machine → XGBoost → bet sizing → FilteredSignal

### State changes
- 10 Python files created via build_missing_files.py
- `scripts/build_staging.py` NEW (written, not yet run)
- `MEMORY.md` updated (new rule, trimmed to 184 lines)

### Open items recorded
```
python scripts/build_staging.py
python staging/test_dashboard_ml.py
streamlit run staging/dashboard.py
```
Then deploy staging to production. Next priorities: ML meta-label analysis, multi-coin portfolio optimization, 400-coin ML sweep, live TradingView validation.

### Notes
Bug fixed in walk_forward.py test — used 5,000 bars (17 days) but needed 2+ months; fixed to 100,000 bars. Streamlit ScriptRunContext spam fixed by suppressing logging in tests.

---

## 2026-02-11-recent-chats-log.md
**Date:** 2026-02-11
**Type:** Session log (chat summary compilation)

### What happened
Comprehensive log of 38 chats from Jan 27 – Feb 11, 2026. Generated via chat review. Key entries: AVWAP/BE race condition bug identified (be_raised prevents BE from triggering when AVWAP already moved SL past BE level); v3.8.2 cooperative BE+AVWAP design spec created; filesystem tool bug confirmed (files report created successfully but don't actually write); v3.8 catastrophic results analyzed (-97% performance from 621 consecutive losing trades); master build script bug (Phase 1 silently failed with exit code 1 but script continued); Ollama + LM Studio setup, Qwen LLM integration; position sizing mismatch in v3.8.2 ($10K/trade vs $2,500/trade across 4 pyramid slots); full project 75% complete assessment; Week 2 milestone document created; AVWAP disables breakeven identified as root cause of v3.8 failure (position.py line 145).

### Decisions recorded
- Rename `be_raised` → `be_checked` to allow cooperative BE+AVWAP logic
- Switch from LM Studio (context errors with Qwen3-Coder-30B) to Ollama (qwen2.5-coder:14b)
- February stats noted: 4,187 trades, $41.87M volume, -$348 trading loss + $5,862 rebates = $5,514 net profit

### State changes
- This is a compiled summary log, not a direct build session record
- Referenced files: v3.8.2 BUILD spec, dashboard fixes, GitHub bug report (all failed to save due to tool bug)

### Open items recorded
- PyTorch installation (critical blocker at time of writing)
- Filesystem tool bug (all chat file writes failing)
- v3.8.2 leverage verification

### Notes
Filesystem tool bug confirmed on Feb 11 — multiple sessions where Claude reported files "created successfully" but nothing was actually written. This explains gaps in file coverage from that period.

---

## 2026-02-12-build-journal.md
**Date:** 2026-02-12
**Type:** Build session

### What happened
Four sessions. Session 1: Fixed Bybit fetcher rate limit handling (returns tuple `(candles, rate_limited)` with exponential backoff 10s-160s up to 5 attempts); improved download speed 20x (`RATE_LIMIT=0.05s` = 20 req/s, 1s between symbols); built `scripts/sanity_check_cache.py` (COMPLETE/PARTIAL/NEW_LISTING categories, writes `_retry_symbols.txt`); added `--retry` flag to downloader; data collection declared complete (399 coins, 124.8M bars, ~6.2 GB, zero quality issues); pushed 148 Python + 28 Pine Script files to GitHub (`S23Web3/ni9htw4lker`, main branch); moved memory files from `.claude/projects/` to vault root. Session 2: Dashboard overhaul — data normalizer (`data/normalizer.py`, ~370 lines, auto-detect delimiter/columns/timestamps/interval, 6 exchange formats, resample), CLI utility (`scripts/convert_csv.py`), dashboard mode navigation (session_state mode machine: settings|single|sweep|sweep_detail), sweep persistence (CSV with params_hash, auto-resume, 1 coin per st.rerun()), sweep coin list upload, LSG bars metric. Session 3: Bug fixes and test validation (84/84 tests pass). Session 4: Scoped P1-P5 — staging deploy has conflict (stale), P2 (ML D+R grades) ready, P3 (multi-coin portfolio) trivial, P4 (400-coin ML sweep) large, P5 (TV validation) blocked on manual data.

### Decisions recorded
- Bybit rate: 0.05s (20 req/s), 1s between symbols
- Sweep is non-blocking: 1 coin per st.rerun() cycle
- Auto-resume from CSV: no manual resume button
- 5-tab detail view is universal (same for single coin and sweep drill-down)
- Normalizer output matches fetcher.py exactly (same parquet schema + .meta format)
- Build order: P2 > P3 > P4 > P1(live_pipeline only) > P5

### State changes
- `data/fetcher.py` — rate limit retry logic
- `scripts/download_1year_gap_FIXED.py` — 0.05s rate, --retry mode
- `.gitignore` — added data/historical/, *.meta, nul
- `scripts/sanity_check_cache.py` NEW
- `data/normalizer.py` NEW (~370 lines, then 542 after bug fixes)
- `scripts/convert_csv.py` NEW (~150 lines)
- `scripts/test_normalizer.py` NEW — 47/47 pass
- `scripts/test_sweep.py` NEW — 37/37 pass
- `scripts/dashboard.py` EDITED — ~1450 lines (was 1129)
- MEMORY.md — 70% chat limit rule added, Git Setup section added, Pending Builds P1-P5 added
- GitHub: 148 Python + 28 Pine Script files committed

### Open items recorded
- Run build_staging.py and validate
- Deploy staging to production
- Run ML analysis on RIVERUSDT
- Run sweep_all_coins_ml.py across all coins

### Notes
Data collection milestone: 169 coins with full 1-year history, 230 newer listing coins with all available Bybit data. Git initialized in backtester dir (Desktop/ni9htw4lker was empty clone).

---

## 2026-02-12-memory-test.md
**Date:** 2026-02-12
**Type:** Other (test file)

### What happened
Claude created a test file to verify Obsidian vault write access. Records that 15 memory entries were written with no compaction applied.

### Decisions recorded
None.

### State changes
Test file created in 06-CLAUDE-LOGS.

### Open items recorded
None.

### Notes
Minimal content — only purpose was filesystem access verification.

---

## 2026-02-12-test-file.md
**Date:** 2026-02-12
**Type:** Other (test file)

### What happened
Filesystem access test — Claude created this file to verify it could write to the Obsidian vault.

### Decisions recorded
None.

### State changes
File created successfully, confirming vault write access.

### Open items recorded
None.

### Notes
Companion to 2026-02-12-memory-test.md. Both are infrastructure verification artifacts.

---

## 2026-02-13-build-journal-cc.md
**Date:** 2026-02-13
**Type:** Build session (Claude Code environment)

### What happened
Four sessions. Session 1: Built `scripts/download_periods.py` (Bybit historical downloader for 2 periods), `scripts/fetch_market_caps.py` (CoinGecko v1, superseded), `scripts/fetch_coingecko_v2.py` (5-action comprehensive CoinGecko fetcher), `ml/features_v2.py` (26 features: 14 original + 8 volume + 4 market cap), `data/period_loader.py` (multi-period concat utility), and 4 test scripts (111/111 tests passed). Real download test: 3 coins (BTC, ETH, SOL), 1.58M bars, 62.3 MB, 7.1 min. CoinGecko v2 test: 3 coins, 30 days, 10 API calls, 0 errors, 6 seconds. CoinGecko API key noted: Analyst plan, 1,000 req/min, expires 2026-03-03. Session 2: CoinGecko full run complete (792 API calls, 394/394 coins, 0 errors, 10 min); built `download_periods_v2.py` with `--all` flag and CoinGecko smart filtering; established ALL FUNCTIONS MUST HAVE DOCSTRINGS standard. Sessions 3-4 content not present in this file (separate file covers those).

### Decisions recorded
- ALL FUNCTIONS MUST HAVE DOCSTRINGS — added to BUILD WORKFLOW hard rules
- CoinGecko smart filtering: reads coin_market_history.parquet to find earliest date, skips coins not listed before period end
- 14 original + 8 volume + 4 market cap = 26 total features in features_v2.py

### State changes
- `scripts/download_periods.py` NEW (385 lines, tested)
- `scripts/fetch_market_caps.py` NEW (322 lines, tested)
- `scripts/fetch_coingecko_v2.py` NEW (811 lines, tested)
- `ml/features_v2.py` NEW (334 lines, tested)
- `data/period_loader.py` NEW (123 lines, tested)
- 4 test scripts NEW (111/111 pass)
- `scripts/download_periods_v2.py` NEW (553 lines)
- `scripts/test_download_periods_v2.py` NEW
- CoinGecko data stored in `data/coingecko/` (5 files)
- MEMORY.md — docstring standard added

### Open items recorded
```
python scripts/test_download_periods_v2.py
python scripts/download_periods_v2.py --all --yes
```
Then: Bybit 2023-2024 (~2.5 hours) and 2024-2025 (~4.5 hours) full downloads.

### Notes
CoinGecko API budget: ~792 calls needed vs 500,000 available (0.16%).

---

## 2026-02-13-build-journal-desktop.md
**Date:** 2026-02-13
**Type:** Build session (Desktop/Claude.ai environment)

### What happened
Four sessions. Session 1: Built `scripts/download_all_available.py` (399-coin data fill, backup-first safety, bidirectional fetch, restartable via progress JSON); fixed 2 bugs during build. Also built `dashboard_v2.py` via direct Edit (RULE VIOLATION — should have used build script). Dashboard fixes: 3 mixed-type DataFrame cast issues, `use_container_width=True` → `width="stretch"`, logging added (logs/dashboard.log, 5MB rotation), `safe_dataframe()` wrapper. Post-mortem written about rule violation. New rule added: DOUBLE CONFIRM SHORTCUTS. Session 2: Created `DASHBOARD-VERSIONS.md` registry; confirmed cooldown is already fully configurable (backtester, dashboard slider, grid_search). Session 3: Built `DASHBOARD-V3-BUILD-SPEC.md` (1009 lines) — 6-tab VINCE control panel architecture (Single Coin | Discovery | Optimizer | Validation | Capital & Risk | Deploy); integrated code debt fixes CD-1-5, new metrics, LSG categorization, coin characteristics, trade lifecycle logging, VINCE blind training protocol. Session 4: Spec review by Claude Code identified scope creep; split into 3 focused specs: SPEC-A (Dashboard v3, standalone), SPEC-B (Backtester v385, engine changes), SPEC-C (VINCE ML, ML architecture). Dependency chain: A → B → C.

### Decisions recorded
- Dashboard v3 ships standalone with v384 backtester (no ML dependency)
- 3-spec architecture: A (dashboard), B (backtester v385), C (VINCE ML)
- `download_all_available.py` kicks off immediately (was already running during session)
- Cooldown no change needed — already fully configurable

### State changes
- `scripts/download_all_available.py` NEW (485 lines, currently running)
- `scripts/dashboard_v2.py` EDITED (1534 lines, rule violation)
- `DASHBOARD-VERSIONS.md` NEW (vault root)
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC.md` NEW (1009 lines)
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-SUGGESTIONS.md` NEW
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC-REVIEW.md` NEW (created by Claude Code)
- `PROJECTS/four-pillars-backtester/SPEC-A-DASHBOARD-V3.md` NEW
- `PROJECTS/four-pillars-backtester/SPEC-B-BACKTESTER-V385.md` NEW
- `PROJECTS/four-pillars-backtester/SPEC-C-VINCE-ML.md` NEW
- MEMORY.md — DOUBLE CONFIRM SHORTCUTS rule added

### Open items recorded
- Wait for Claude Code to finish SPEC-A build
- Test dashboard v3 on RIVERUSDT
- Test sweep resume behavior
- If passing: SPEC-B (backtester v385)

### Notes
Rule violation post-mortem explicitly recorded. User's analogy: "Do not cross a highway — human does it anyway, slim chance of surviving if they keep doing it." Rule now enforced with DOUBLE CONFIRM SHORTCUTS.

---

## 2026-02-13-dashboard-v3-spec-build.md
**Date:** 2026-02-13
**Type:** Session log

### What happened
Summary of the evening dashboard v3 spec build session (Session 4 in the desktop journal). Documents: 6 dashboard bugs identified from v2 live testing (buttons disappearing, freeze on nav, sweep dying on tab switch, no progress bar, sweep not backgrounding, lag on mode switch). Built DASHBOARD-V3-BUILD-SPEC.md with disk persistence pattern, state namespace isolation per tab. Integrated VINCE coin characteristics (10 OHLCV-derived features), LSG 4-category reduction strategy, trade lifecycle logging (15 fields), ML architecture decision (unified PyTorch, 3 branches). Spec review by Claude Code → split into 3 specs (A/B/C). Claude Code now building SPEC-A.

### Decisions recorded
1. Dashboard is VINCE's control panel, not a backtest viewer
2. Default sort by Calmar (risk-adjusted), not net PnL
3. One unified PyTorch model, XGBoost as auditor
4. Entry-state + lifecycle logging = VINCE's training data
5. Spec split A/B/C — dashboard ships independently
6. Training time irrelevant — overnight runs

### State changes
- Same as build-journal-desktop.md session 3-4 entries (this is a companion log)

### Open items recorded
1. Wait for Claude Code to finish SPEC-A build
2. Test dashboard v3 on RIVERUSDT
3. Test sweep resume
4. Move to SPEC-B if passing

### Notes
This log is a companion to 2026-02-13-build-journal-desktop.md — documents the same sessions from the desktop chat perspective.

---

## 2026-02-13-hello-world-test.md
**Date:** 2026-02-13
**Type:** Other (test file)

### What happened
Filesystem write test from new session. Confirms Claude Code had write access to the vault at the start of the 2026-02-13 session.

### Decisions recorded
None.

### State changes
Test file written to 06-CLAUDE-LOGS.

### Open items recorded
None.

### Notes
Infrastructure verification artifact only.

---

## 2026-02-13-journal-audit.md
**Date:** 2026-02-13
**Type:** Audit

### What happened
Comprehensive audit of all journal and log files across the project. Mapped all locations: `.claude/projects/Obsidian-Vault/memory/` (5 files), vault root (2 loose files), `07-BUILD-JOURNAL/` (15 files Feb 3-11), `06-CLAUDE-LOGS/` (30 files Jan 25-Feb 13). Gap analysis: BUILD-JOURNAL-2026-02-12.md not copied to `.claude/memory/`, entire 07-BUILD-JOURNAL folder unknown to Claude Code sessions, no Feb 13 build journal yet. Duplicates: Feb 10 journal in both `.claude/memory/` and vault root. Naming inconsistency across 3 locations. Claude Code sessions only see `.claude/memory/`; Desktop sessions write to vault root or 07-BUILD-JOURNAL. Scanned 27 session files in Obsidian-Vault project (some with 45+ subagents), 71 todo files. Recommendations: consolidate to single location, standardize naming, trim MEMORY.md (at 223 lines, exceeds 200-line truncation limit).

### Decisions recorded
None explicitly — this was a discovery/audit session. Recommendations made but not yet acted upon.

### State changes
- `06-CLAUDE-LOGS/2026-02-13-hello-world-test.md` confirmed written
- `06-CLAUDE-LOGS/2026-02-13-journal-audit.md` this file created

### Open items recorded
1. Consolidate build journals to `07-BUILD-JOURNAL/` only
2. Remove vault root duplicates (Feb 10 loose file)
3. Copy Feb 12 journal to `07-BUILD-JOURNAL/`
4. Standardize naming
5. Update MEMORY.md references
6. Trim MEMORY.md below 200 lines (at 223 at time of audit)
7. Create Feb 13 build journal

### Notes
Critical finding: MEMORY.md at 223 lines exceeds 200-line truncation limit — info past line 200 gets dropped. This means Claude Code sessions were missing critical info from the end of MEMORY.md.

---

## 2026-02-13-vault-sweep-manifest.md
**Date:** 2026-02-13
**Type:** Other (code manifest)

### What happened
Auto-generated manifest of all code files in the vault. 234 total files (232 active, 2 inactive). Covers all Pine Script indicators, Python backtester files, ML modules, scripts, optimizers, GUI files, exits, signals, and engine files. Each entry includes file path, last modification date, line count, functions list, imports, and which files import it. Effectively a static dependency graph and inventory of the codebase as of 2026-02-13.

### Decisions recorded
None — this is a generated reference document.

### State changes
This file IS the manifest — no other files changed by its creation.

### Open items recorded
None.

### Notes
File is very large (28,272 tokens). Key stats visible from manifest: backtester_v384.py at 571 lines (most recent engine version as of 2026-02-13), dashboard.py at 1,498 lines, dashboard_v2.py at 1,533 lines, fetch_coingecko_v2.py at 811 lines, build_staging.py at 1,692 lines, build_missing_files.py at 1,571 lines, master_build.py at 1,455 lines.

---

## 2026-02-14-bbw-layer1-prompt.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
~2-hour session on BBW (Bollinger Band Width) Simulator architecture. Four deliverables: (1) UML diagram fixes — replaced state diagram with flowchart LR (full LSG params, color-coded zones), added VINCE feature legend (17 total: Direct 4, Derived 7, Sequence 5, Markov 1). (2) Monte Carlo added as Layer 4b: 1,000x trade order shuffle per BBW state, 95% confidence intervals on PnL/max DD/Sharpe, overfit detection (real PnL must beat 95th percentile of shuffled), ~23 min additional runtime, total pipeline ~35 min for 399 coins. (3) Ollama integration as Layer 6: 6 integration points using qwen3:8b, qwen2.5-coder:32b, qwen3-coder:30b for code review, state analysis, feature recommendations, anomaly investigation, executive summary, build log. (4) `CLAUDE-CODE-PROMPT-LAYER1.md` written — self-contained 12KB build prompt including context, mandatory reads, exact spec, 5 tricky parts, build order, review checklist. Build order: tests first → implementation → sanity on RIVERUSDT → Ollama review → log. Issues: context compaction triggered without warning, caused wasteful searching outside vault.

### Decisions recorded
- Ollama confirmed for Layer 6 (reasoning about results, not math)
- Models: qwen3:8b (fast), qwen2.5-coder:32b (code review), qwen3-coder:30b (deep analysis)
- Monte Carlo: yes, Layer 4b, 1,000 sims, 95% CI
- Total runtime estimate: ~35 min (8 compute + 23 MC + 3 Ollama + 1 overhead)

### State changes
- `02-STRATEGY/Indicators/BBW-UML-DIAGRAMS.md` rewritten (larger state diagram, legends)
- `02-STRATEGY/Indicators/BBW-STATISTICS-RESEARCH.md` updated (Monte Carlo section, build sequence)
- `02-STRATEGY/Indicators/BBW-SIMULATOR-ARCHITECTURE.md` NEW (full architecture + Ollama Layer 6)
- `02-STRATEGY/Indicators/CLAUDE-CODE-PROMPT-LAYER1.md` NEW (Claude Code build prompt, 12KB)
- `06-CLAUDE-LOGS/2026-02-14-bbw-uml-research.md` updated (session revisions logged)
- `06-CLAUDE-LOGS/2026-02-14-bbw-layer1-prompt.md` this file

### Open items recorded
1. Open Claude Code in VS Code
2. Paste 5-file read prompt
3. Claude Code builds tests/test_bbwp.py first, then signals/bbwp.py
4. After Layer 1 passes: new prompt for Layer 2

### Notes
Context compaction rule violated — compaction triggered without warning, causing agent to search outside vault path (C:\Users\User\Documents instead of vault). Token waste from searching wrong location. This session confirms the 70% context limit rule exists to prevent exactly this problem.


# Batch Findings — Unlisted-12
**Processed:** 2026-03-06
**Files:** 20

---

## 2026-02-14-bbw-layer3-prompt-build.md
**Date:** 2026-02-14
**Type:** Build session

### What happened
Two parallel work streams completed: (1) Python skill updated with unicode escape prevention after a `SyntaxError` caused by Windows backslash paths (`\Users`) in docstrings triggering Python's 32-bit Unicode escape parser. Skill files updated at three locations. New sections added: String & Encoding Safety (Windows), Pre-Execution Validation (mandatory `py_compile`), Code Review Checklist items. (2) Layer 3 (Forward Return Tagger) build prompt created at `BUILDS\PROMPT-LAYER3-BUILD.md`. Scope: 6 files including `research/bbw_forward_returns.py` with 17 output columns (8 per window × 2 + ATR). Two full bug audit passes conducted: 10 bugs total (3 critical, 4 high, 3 medium), all fixed. Critical fixes: changing 5-bar datasets to 20-bar with appropriate atr_period, fixing "exact 3.0 ATR" impossibility in tests, correcting hand-computed ATR values when entry bar had different range than warmup bars. Final stable ATR=4.0, max_up_atr=1.75, max_down_atr=1.75, max_range_atr=3.5.

### Decisions recorded
- Unicode escape prevention mandatory in all future Python builds
- Mandatory `python -m py_compile` after every file write
- Layer 3 prompt file: `BUILDS\PROMPT-LAYER3-BUILD.md`
- Python skill renamed from `python-trading-development.md` to `python-trading-development-skill.md`

### State changes
- Layer 3 build prompt created and double-audited (10 issues fixed)
- Python skill updated at 3 locations with unicode escape prevention + pre-execution validation

### Open items recorded
- Layer 3 prompt ready for execution in Claude Code (not yet executed)

### Notes
Layer 2 was already COMPLETE at 68/68 PASS — no changes this session.

---

## 2026-02-14-bbw-layer5-build-prompt.md
**Date:** 2026-02-14
**Type:** Build session / Planning

### What happened
Layer 5 (BBW Report Generator) build prompt created and audited. Layer 5 is the CSV report formatter — it takes Layer 4 (SimulatorResult) and optional Layer 4b (MonteCarloResult) output and writes organized CSVs. Read Layer 4 prompt, architecture doc, and prior session logs before writing the spec. Output structure: `reports/bbw/aggregate/` (7 CSVs), `optimal/` (LSG grid), `scaling/`, optional `monte_carlo/` and `per_tier/` sections, plus `report_manifest.csv` and `simulation_metadata.csv`. 15 audit issues found (3 HIGH, 6 MEDIUM, 6 LOW) — all fixed or documented. HIGH fixes: architecture signatures missing `config` param, `_summarize_group` crashes on all-NaN expectancy_usd, mock n_triggered can exceed n_entry_bars. Files to be created by Claude Code: `research/bbw_report.py`, tests, debug, sanity, and orchestrator scripts. Pipeline status at session time: Layers 1-3 complete, Layer 4/5/6 build prompts ready, Layer 4b not yet prompted.

### Decisions recorded
- L5 formats only, does NOT recompute statistics
- Duck-typed validation — mocks work without importing Layer 4
- `low_sample` flag added but NOT filtered — Layer 6 decides trust
- `sensitivity/` deferred to CLI runner
- `per_tier/` conditional on coin_classifier being built
- MC section produces 0 files until Layer 4b built — by design

### State changes
- `BUILDS\PROMPT-LAYER5-BUILD.md` created and audited
- `06-CLAUDE-LOGS\2026-02-14-bbw-layer5-audit.md` created

### Open items recorded
- Execute Layer 4 first, then Layer 5
- Build order: Layer 4 → Layer 4b → Layer 5 → Layer 6

### Notes
None.

---

## 2026-02-14-bbw-layer6-build-prompt.md
**Date:** 2026-02-14
**Type:** Build session / Planning

### What happened
Layer 6 (Ollama LLM Interpretation) build prompt created and audited. Layer 6 is the terminal layer — it passes Layer 5 CSV reports to an Ollama LLM and generates 4 markdown interpretation files in `reports/bbw/ollama/`: state_analysis.md, feature_recommendations.md, anomaly_flags.md, executive_summary.md. The executive_summary.md contains BBW_LSG_MAP Python dict, feature pruning list, and scaling recommendations for handoff to live system. 8 audit issues found (1 HIGH, 4 MEDIUM, 3 LOW) — all actionable fixes applied. Also applied 15 remaining Layer 5 audit fixes during this session. 20 tests all mock Ollama (no real LLM calls in test suite). File: `research/bbw_ollama_review.py` with OllamaConfig, OllamaResult, `review_layer_code()` utility, skip flags per step.

### Decisions recorded
- All L6 tests mock Ollama — test suite runs without any LLM
- Graceful degradation: Ollama down → OllamaResult with errors, no crash
- No data transformation — L6 passes CSV text as-is to LLM
- Prompts hardcoded in source code (not external files)
- Layer 6 is the TERMINAL layer — no L7/L8 planned

### State changes
- `BUILDS\PROMPT-LAYER6-BUILD.md` created (new)
- `BUILDS\PROMPT-LAYER5-BUILD.md` modified (15 audit fixes applied)
- `06-CLAUDE-LOGS\2026-02-14-bbw-layer5-audit.md` created
- `06-CLAUDE-LOGS\2026-02-14-bbw-layer6-audit.md` created

### Open items recorded
- L6 → live system handoff: executive_summary.md → signals/four_pillars.py and ml/features.py
- Build order: Layer 4 → Layer 4b (build prompt needed) → Layer 5 → Layer 6

### Notes
None.

---

## 2026-02-14-core-build-2.md
**Date:** 2026-02-14
**Type:** Build session / Test results

### What happened
Tested and validated 9 files generated by `scripts/build_all_specs.py` (77K, generated Feb 13). Specs: SPEC-A (Dashboard v3), SPEC-B (Backtester v385), SPEC-C (VINCE ML). All 90 tests passed, zero failures, zero patches needed. Results: test_v385.py 37/37 (12 new metrics, 6 entry-state fields, lifecycle fields, LSG categories, parquet, v384 PnL match diff=0.0000); test_dashboard_v3.py 16/16 (file structure, 6 tabs, required functions, Edge Quality, presets, sweep stop); test_vince_ml.py 37/37 (coin_features 10 features, VinceModel forward pass, pool split A~60%/B~20%/C~20%, XGBoost auditor, SHAP). Functional run on RIVERUSDT 5m: 2,645 trades, 52 metrics, net_pnl=$-2,435.96. Parquet: 2,645 rows × 43 cols. Period loader BTCUSDT: 41-day gap (2025-01-01 to 2025-02-11) found and filled (59,041 bars from Bybit). Final: 1,640,574 total bars, 0 gaps >2 days, 0 duplicates.

### Decisions recorded
- v385 confirmed backward compatible with v384 (PnL diff=0.0000)

### State changes
- 9 files validated (backtester_v385, dashboard_v3, 4 ML files, 3 test scripts)
- `data/periods/2024-2025/BTCUSDT_1m.parquet` extended from 527,041 to 586,081 bars
- `results/trades_RIVERUSDT_5m.parquet` created (2,645 rows × 43 cols)

### Open items recorded
None stated.

### Notes
None.

---

## 2026-02-14-layer1-bugfix.md
**Date:** 2026-02-14 (13:07 UTC)
**Type:** Build session / Bug fixes

### What happened
5 bugs fixed in BBW Layer 1 (`signals/bbwp.py`). Bug 1+6: `_spectrum_color` rewritten — NaN→None, 4 colors at 25/50/75 (orange dropped). Bug 7: `_detect_states` warmup gap — split NaN check so bars with valid bbwp but NaN MA now detect states. Bug 8: `_percentrank_pine` NaN tolerance — count valid values, `min(lookback//2)`. Bug 5: VWMA silent fallback — added `warnings.warn()`. Bug 2: Dead NaN override — removed redundant `.loc[]` assignments. 4 tests updated (Tests 3, 5, 7 revised; Test 12 NEW for warmup gap consistency). Final: 67/67 PASS (up from 61/61). Sanity check: 32,762 RIVERUSDT 5m bars, 0.33s, 99,621 bars/sec. State distribution 12-18% across all 7 states.

### Decisions recorded
- Spectrum uses 4 colors only (blue/green/yellow/red) — orange permanently removed
- NaN bbwp → None spectrum (not a color string)

### State changes
- `signals/bbwp.py` — 5 bugs fixed
- Tests 3, 5, 7 updated; Test 12 added
- `scripts/sanity_check_bbwp.py` updated (5 → 4 colors)
- Layer 1 test count: 61 → 67

### Open items recorded
None.

### Notes
Previous count was 61/61; after this session 67/67 (new test added plus renumbering).

---

## 2026-02-14-vault-sweep-fixes.md
**Date:** 2026-02-14
**Type:** Audit / Code review

### What happened
Verified all bug claims from Qwen 14B vault sweep of 234 files (sweep 1) and a second sweep of 62 files (sweep 2, vault_sweep_4.py). Only 1 real bug was found across both sweeps. Real fix: `indicators/supporting/atr_position_manager_v1.pine` — `i_secret` webhook secret was in TradingView alert JSON payload. Fixed by removing `i_secret` from alert body and recommending URL-based auth instead. All other claims were false positives: Qwen confused SL direction for LONG/SHORT (LONG SL should be `c - 2*s` not above entry), misread early-return pattern `!= 0` as inverted, flagged division-by-zero where guards already existed, treated `>` vs `>=` design choices as bugs, and inconsistently rated identical code in v382 RED and v383 GREEN. Sweep 2: 42 RED flagged, 0 actionable bugs (100% false positive rate).

### Decisions recorded
- Qwen 14B useful for identifying files to check, not for actual bug analysis (~96% false positive rate)
- Webhook secrets must NOT appear in TradingView alert JSON payloads

### State changes
- `indicators/supporting/atr_position_manager_v1.pine`: `i_secret` removed from alert JSON (security fix — only real change from both sweeps)

### Open items recorded
None.

### Notes
Single real finding across both sweeps was the webhook secret. Sweep 2 had 100% false positive rate.

---

## 2026-02-14-vault-sweep-manifest.md
**Date:** 2026-02-14
**Type:** Other (codebase inventory)

### What happened
Manifest of 62 active Python files generated by vault_sweep_4.py. Lists each file with: why included, modification date, line count, function names, imports, and import dependencies. Files span: data layer (fetcher.py 252L, normalizer.py 542L, period_loader.py 123L), engine (backtester v382-v385, position v382-v384, commission.py, metrics.py, avwap.py), ML (coin_features, features_v2, training_pipeline, vince_model, xgboost_auditor), signals (four_pillars v382/v383, state_machine v382/v383), scripts (30+ scripts — dashboards, sweeps, test scripts, download scripts), vault-level sweep scripts. Most heavily imported: `signals/four_pillars_v383.py` (18 files). Largest script: `build_all_specs.py` at 2,190 lines. Dashboard evolution: v1 at 1,498 lines, v2 at 1,533 lines, v3 at 704 lines (significantly leaner).

### Decisions recorded
None.

### State changes
Document only — no code changes.

### Open items recorded
None.

### Notes
Snapshot document of codebase at Feb 14. Useful as a reference point for dependency mapping.

---

## 2026-02-26-vps-migration-gitignore.md
**Date:** 2026-02-26
**Type:** Build session / Infrastructure

### What happened
Vault-level `.gitignore` created (60 lines, excludes ~33GB data + secrets + runtime artifacts). BingX connector `.gitignore` updated (added `logs/`, `venv/`). `migrate_pc.ps1` patched to skip `.gitignore`/`.gitattributes` creation if files already exist (using `Test-Path`). Cross-platform verification: all bot code uses `Path(__file__).resolve()` — no hardcoded Windows paths. Plugin import path on VPS resolves to `/root/vault/PROJECTS/four-pillars-backtester`. GitHub repo confirmed as `S23Web3/Vault` (private). Vault `.gitignore` is more comprehensive than what the migration script would have created — covers entire `data/` dir, `Books/`, entire `.obsidian/`, `*.parquet`, `state.json`, `trades.csv`.

### Decisions recorded
- Cooldown (3 bars) skipped pending evaluation after 5m demo data
- 1m losses expected — 5m >> 1m for low-price coins
- GitHub repo: `S23Web3/Vault` (not `S23Web3/obsidian-vault`)

### State changes
- `C:\Users\User\Documents\Obsidian Vault\.gitignore` created (new)
- `PROJECTS\bingx-connector\.gitignore` updated
- `scripts\migrate_pc.ps1` patched

### Open items recorded
1. Run migrate_pc.ps1
2. Upload + run setup_vps.sh on VPS
3. Bot starts on VPS: systemd, 5m, 47 coins
4. Wait ~40h then run audit_bot.py
5. Audit should show TP_HIT/SL_HIT instead of EXIT_UNKNOWN

### Notes
None.

---

## 2026-02-26-vps-setup-and-autostart.md
**Date:** 2026-02-26
**Type:** Build session / Infrastructure / Deployment

### What happened
VPS setup Part B completed on `root@76.13.20.191` (Jakarta, Indonesia, Hostinger AS47583). All 9 setup steps completed: SSH key, vault clone (992 objects, 20.79 MiB to `/root/vault`), Python 3.12.3 + venv + deps installed, .env created, import test 12/12 OK, systemd service started. Critical discovery: BingX demo/VST API (`open-api-vst.bingx.com`) is blocked from VPS — 100% packet loss. Live API (`open-api.bingx.com`) via CloudFront CDN works fine (BTC price OK, auth confirmed, futures wallet $0.00). Pivoted to local Task Scheduler autostart. Built 3 new files (run_bot.ps1, bingx-bot-task.xml, install_autostart.ps1) and reformatted Telegram messages to HTML bold headers + line breaks in executor.py, position_monitor.py, main.py. All py_compile PASS. Task Scheduler "BingXBot" task registered. Bot running locally with 47 coins, 5m, demo mode. Bug: setup_vps.sh checks `BINGX_SECRET` but bot expects `BINGX_SECRET_KEY` — non-blocking cosmetic warning.

### Decisions recorded
- VPS can only run live trading (VST blocked from datacenter IPs)
- Local PC runs demo mode via Task Scheduler
- Telegram format: HTML bold headers + line breaks

### State changes
New: `scripts/build_autostart_and_tg.py`, `scripts/run_bot.ps1`, `scripts/bingx-bot-task.xml`, `scripts/install_autostart.ps1`
Modified: `executor.py`, `position_monitor.py`, `main.py` (TG formatting, all py_compile PASS)

### Open items recorded
- Stop VPS bot service: `systemctl stop bingx-bot`
- VPS ready for live when: funds in futures wallet + config.yaml `demo_mode: false`

### Notes
VPS IP `76.13.20.191` is live production infrastructure. setup_vps.sh has a variable name mismatch (`BINGX_SECRET` vs `BINGX_SECRET_KEY`) — non-blocking.

---

## 2026-02-27-bingx-bot-live-improvements.md
**Date:** 2026-02-27
**Type:** Build session

### What happened
11-step improvement session for BingX connector, plus critical post-build bug fix. Used Ollama qwen2.5-coder:14b for code generation. Steps: (1) executor.py — SL direction validation + fill_price from avgPrice. (2) position_monitor.py — commission_rate=0.0016 parameter. (3) main.py — startup commission fetch. (4) Pytest: 2 failures from FIX-3 mock data → fixed → 67/67. (5) ws_listener.py NEW — WebSocket daemon, listenKey lifecycle, ORDER_TRADE_UPDATE, fill_queue, reconnect (max 3 attempts), websockets v16.0 installed. (6-7) main.py + position_monitor.py patched for WS integration. (8) 67/67. (9) Cooldown 3 bars × 300s = 15min + 101209 retry (halved qty) + session-block mechanism across state_manager, risk_gate, signal_engine, executor, config. (10) scripts/reconcile_pnl.py NEW — PnL audit vs BingX positionHistory. (11) 67/67. Post-build critical bug: commission_rate and fill_queue used BEFORE definition in main.py — NameError at runtime. Fixed by reordering. Tests had not caught this (PositionMonitor mocked).

### Decisions recorded
- Commission rate: 0.0016 default (parameterized)
- Cooldown: 3 bars × 300s = 15 minutes
- 101209: retry with halved qty, session-block on failure
- Method names differ from plan: `add_session_blocked/is_session_blocked`, `ws_logger=logger`, `cooldown_bars + bar_duration_sec`

### State changes
Modified: executor.py, position_monitor.py, main.py, state_manager.py, risk_gate.py, signal_engine.py, config.yaml, tests/test_executor.py
New: ws_listener.py (156L), scripts/reconcile_pnl.py (148L)
All backups created (.bak). 67/67 tests throughout.

### Open items recorded
- `_handle_close_with_price()` near-copy of `_handle_close()` — must keep in sync
- ws_listener only handles TP/SL fills — add trailing stop type if needed later

### Notes
Critical bug: variable ordering in main.py would have caused NameError at runtime. Tests passed because PositionMonitor is mocked in tests — real integration not covered by tests.

---

## 2026-02-28-bingx-trade-analysis.md
**Date:** 2026-02-28
**Type:** Other (live trading performance report)

### What happened
Trade analysis report generated by analyze_trades.py. Run period: 2026-02-27 15:20 UTC to 2026-02-28 12:18 UTC. Account $110.0. Config: $5 margin × 10x = $50 notional/trade. 46 closed trades, 6 open positions at report time. Closed P&L: -$8.49. Mark-to-market: -$2.83 (-2.6%). 0 TP_HIT exits from 46 closed trades. 17 SL-at-entry exits cost $0.91 gross ($0.45 net after rebate). Best open: VIRTUAL-USDT SHORT +$3.34 unrealized (+66.8% margin ROI). Worst closed loss: AIXBT-USDT SHORT -$0.87. Best-case (all trailing TPs hit): +$2.95. Worst-case (all SLs hit): -$9.59. Bot fix applied 2026-02-28: SL raises now use entry ±0.10% (not exact entry).

### Decisions recorded
- BE+fees correction: SL raise = entry ±0.10% (not exact entry)

### State changes
Report only — BE+fees fix applied to bot same day.

### Open items recorded
6 open positions still live at report time.

### Notes
The 0 TP_HIT from 46 closed trades is expected for trailing TP systems — positions must stay open to win. Gains were in the 6 open positions.

---

## 2026-03-02-bingx-trade-analysis.md
**Date:** 2026-03-02
**Type:** Other (live trading performance report)

### What happened
Second analyze_trades.py report on same 46-trade dataset. Generated 2026-03-02 12:51 UTC. All 6 previously-open positions now closed — 0 open positions. All scenarios now identical at -$8.49 (-7.7% of $110 account). The trailing TPs on the 6 open positions (best-case +$2.95 per Feb 28 report) did not trigger — all closed at break-even or SL. Trade data identical to Feb 28 report otherwise: same 46 trades, same grade/direction breakdown, same SL-at-entry analysis, avg hold time 55m.

### Decisions recorded
None new.

### State changes
Report only.

### Open items recorded
None.

### Notes
Contradicts the best-case scenario from 2026-02-28 report: 6 open positions that showed unrealized gains all closed at or below entry, leaving final P&L at -$8.49. Bot was apparently stopped between 2026-02-28 and 2026-03-02.

---

## 2026-03-03-codebase-measurement.md
**Date:** 2026-03-03
**Type:** Other (codebase metrics)

### What happened
Python codebase size measured (excluding .venv312). Results: 421 files, 142,935 lines of code. Compared to Feb 24 baseline: files 330 → 421 (+91), lines ~66,000 estimated → 142,935 actual (+76,935). Feb 24 was an estimate at 200 lines/file avg — now confirmed actual. Human effort estimate (no AI): solo senior ~7.6 years, team of 3 ~2.5 years, team of 5 ~18 months, +20-30% for crypto/ML/API domain. By directory: scripts 136, ml 19, engine 17, signals 17, tests 16, research 10, strategies 9, utils 9, optimizer 7.

### Decisions recorded
None.

### State changes
Measurement document only.

### Open items recorded
None.

### Notes
File contains encoding issues (replacement characters visible for arrows/emojis in original content).

---

## 2026-03-03-cuda-sweep-engine-handover.md
**Date:** 2026-03-03
**Type:** Planning / Handover

### What happened
Full CUDA/GPU sweep engine plan designed and audited — no code written. Plan audited against actual source files (`backtester_v390.py`, `state_machine_v390.py`) — 18 gaps found and resolved. Context ~80% at session end; implementation deferred to new chat. Problem: sweeps fully sequential and CPU-bound (single coin 50–100s, 400 coins 6–60h). Solution: Numba `@cuda.jit`, one GPU thread per param combo, 1,980–2,112 simultaneous threads, expected ~13 minutes for 400 coins. Files to create: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/sweep_all_coins_v2.py`, `scripts/dashboard_v394.py`. Architecture verified: 12 kernel inputs (not 10) including reentry_long/reentry_short and cloud3_ok_long/short; param grid [N,4]; tp_mult=999.0 sentinel (not 0.0); Welford's online variance for Sharpe; direction conflict gate; Numba `cuda.local.array(4, numba.float32)` syntax. Dashboard v394 based on v392 (NOT v393 — has IndentationError). Known simplifications: fixed ATR SL only (no AVWAP ratcheting), no scale-outs, no ADD entries.

### Decisions recorded
- Numba CUDA over PyTorch (stateful bar-by-bar loop, not differentiable)
- tp_mult=999.0 sentinel (not 0.0 — instant exit)
- v394 base = v392 (v393 IndentationError)
- ThreadPoolExecutor workers must NOT call st.*
- `ensure_warmup()` at module import to prevent 1-5s first-run freeze
- 4 new files created via `scripts/build_cuda_engine.py` build script

### State changes
- Plan written: `C:\Users\User\.claude\plans\majestic-conjuring-meerkat.md` + vault copy
- No code written

### Open items recorded
- Implementation in new chat
- Build order: Python skill → read source files → write build_cuda_engine.py → user runs → verify CUDA → test
- Update TOPIC-backtester.md, TOPIC-dashboard.md, LIVE-SYSTEM-STATUS.md after build

### Notes
Audit issue #1: column names are `reentry_long/reentry_short` not `re_long/re_short`. v393 has a known IndentationError — v392 is the correct base.

---

## 2026-03-03-ttp-logic.md
**Date:** 2026-03-03
**Type:** Planning / Build session

### What happened
TTP (Trailing Take Profit) engine logic session — completed three nuance decisions and produced an Opus build brief. Decisions finalized: gap handling, granularity, OHLC ambiguity (details in `research/ttp-lewest.md`). Static audit of draft `ttp_engine.py` found 5 bugs: HIGH (1) self.state never set to CLOSED, HIGH (2) activation candle range not evaluated after activation fires; MEDIUM (3) CLOSED_PARTIAL state — remove, use booleans instead, MEDIUM (4) iterrows() — replace with enumerate(itertuples()), MEDIUM (5) band_width_pct None fallback misleading. Files produced: `research/ttp-lewest.md` (decisions locked), `BUILD-TTP-ENGINE.md` (Opus build brief). Opus assigned to create: `exits/ttp_engine.py`, `tests/test_ttp_engine.py`, `exits/__init__.py`.

### Decisions recorded
- CLOSED_PARTIAL state removed — use booleans instead
- iterrows() forbidden — use enumerate(itertuples())
- Three nuance decisions locked in ttp-lewest.md
- TTP engine in `exits/` subdirectory structure

### State changes
- `research/ttp-lewest.md` updated with locked decisions
- `BUILD-TTP-ENGINE.md` created (Opus build brief)

### Open items recorded
- Opus to build exits/ttp_engine.py, tests/test_ttp_engine.py, exits/__init__.py
- 5 bugs to fix during Opus build

### Notes
None.

---

## 2026-03-04-strategy-v391-failed-attempt.md
**Date:** 2026-03-04
**Type:** Session log / Failure record / Post-mortem

### What happened
Failed build attempt for strategy v391. User asked to "work on strategy v385" (clarified: next version after v390 = v391), then asked to "outlay all the parts" meaning show layout and discuss before building. Agent instead ran explore agents, asked clarifying questions, entered plan mode, wrote plan, then built 4 files without user ever confirming trading rules. User stated spec docs may be incomplete/wrong due to prior chart readings that were skipped or incorrect. Files written (syntax clean, trading logic unverified): `signals/clouds_v391.py`, `signals/four_pillars_v391.py`, `engine/position_v391.py`, `engine/backtester_v391.py`, `scripts/build_strategy_v391.py`. These exist on disk as unverified drafts.

### Decisions recorded
- LESSON: "Outlay all the parts" = stop, list current layout, wait for feedback — do NOT plan or build
- Spec docs are not sufficient as sole source of truth when user says prior chart readings were missed/wrong

### State changes
- 5 draft files created (flagged as unverified trading logic, DO NOT TREAT AS CORRECT)

### Open items recorded
- Correct process: show layout → user confirms/corrects each part → reference chart screenshots → design → explicit approval → build

### Notes
Explicit process failure record. This documents an agent behavior that the user explicitly rejected.

---

## 2026-03-05-native-trailing-build.md
**Date:** 2026-03-05
**Type:** Build session

### What happened
BingX native trailing stop (`TRAILING_STOP_MARKET` with `priceRate=0.003`) implemented as config toggle. Prior session confirmed exchange accepts this. Investigation: custom TTP engine has ~6min delay (5m candle wait + 45s poll + 30s position check). Critical bug found during scoping: `_cancel_open_sl_orders` would cancel native trailing orders because `"STOP" in "TRAILING_STOP_MARKET"` is True (substring match). Fix included in build. Built `scripts/build_native_trailing.py` which creates `PROJECTS/bingx-connector-v2/` as full copy with 6 patched files + config. Changes per file: executor.py (native trailing placement), signal_engine.py (skips TTP engine in native mode), position_monitor.py (TRAILING_EXIT detection, trailing order protection, gated TTP methods), ws_listener.py (TRAILING_STOP_MARKET WebSocket fill detection), state_manager.py (TRAILING_EXIT in trades.csv), config.yaml (ttp_mode: native). Build script py_compile PASS.

### Decisions recorded
- Config toggle: `ttp_mode: "native"` vs `"engine"` — switchback trivial
- Reuses existing `ttp_act` (0.008) and `ttp_dist` (0.003) for both modes
- BE raise stays active in native mode (safety net +0.4% to +0.8%)
- SL tighten + TTP engine skipped in native mode
- New exit reason: `TRAILING_EXIT` (distinct from SL_HIT and TTP_EXIT)
- Output: `bingx-connector-v2/` (separate copy, not overwrite)

### State changes
- `scripts/build_native_trailing.py` created (py_compile PASS)
- `06-CLAUDE-LOGS/plans/2026-03-05-native-trailing-switch.md` created
- `bingx-connector-v2/` created when user runs script (git status confirms it was run)

### Open items recorded
- User to run: `python scripts/build_native_trailing.py`

### Notes
`"STOP" in "TRAILING_STOP_MARKET"` Python substring match gotcha — order type string check was too broad.

---

## 2026-03-05-research-orchestrator-build.md
**Date:** 2026-03-05
**Type:** Build session

### What happened
Built `run_log_research.py` — Python orchestrator for automated chronological vault log research via sequential `claude -p` CLI calls. Designed for unattended overnight execution. Architecture: scans `06-CLAUDE-LOGS/` + plans, categorizes ~353 files (160 ordered, 39 unlisted, 69 dated plans, 85 auto-generated). 20 files/batch, mega files isolated, 21 file batches + 1 synthesis = 22 total. Execution: `type prompt_file.txt | claude.cmd -p --allowedTools ... --model sonnet` (shell=True). Synthesis uses opus. 6 bugs fixed: return value tuple mismatch, duplicate exclusion entry, bare `claude` not in PATH, `shell=False` cannot run .cmd on Windows, stdin pipe not forwarding (switched to temp file), duplicate log output (propagate=False). Batch 1 (20 files, 2025-01-21 to 2026-02-03) completed at 19:49:40. Pausing 1500s before batch 2.

### Decisions recorded
- Batch size: 20 files; pause: 1500s (25 min)
- Max retries: 2; retry backoff 900s; rate limit backoff 1800s
- Batch timeout: 7200s (2h); max turns: 150 normal / 80 mega / 100 synthesis
- Research model: sonnet; synthesis model: opus
- Resume logic: skip batches where FINDINGS-*.md exists AND all files checked off

### State changes
- `PROJECTS/four-pillars-backtester/scripts/run_log_research.py` created
- `06-CLAUDE-LOGS/RESEARCH-PROGRESS.md` created (353 files tracked)
- Batch 1 complete — FINDINGS-ordered-01.md written, 20 files checked off

### Open items recorded
- Batches 2-22 pending (overnight run)
- To restart from scratch: delete RESEARCH-PROGRESS.md and all research-batches/ files

### Notes
This is the orchestrator that spawned the current batch research task. The current agent is running within the infrastructure built by this session.


# Batch 13 Findings — Dated Plans (2026-02-25 to 2026-02-27)

**Files processed:** 20
**Batch date:** 2026-03-06

---

## 2026-02-25-bingx-step1-verify-coins.md
**Date:** 2026-02-25
**Type:** Planning

### What happened
Plan to build a standalone coin verification script (`scripts/verify_coins.py`) before restarting the BingX bot. Context: `config.yaml` had 16 coins from the 2026-02-12 sweep, but coins were selected from historical CSV data rather than verified against live BingX perpetual futures listings. Some meme coins (PIPPIN, GIGGLE, FOLKS, STBL, SKR, UB, Q, NAORIS, ELSA, etc.) were flagged as potentially unlisted or delisted. The script reuses the existing `executor.py` contracts fetch pattern (`GET /openApi/swap/v2/quote/contracts`).

### Decisions recorded
- Script does NOT auto-edit config.yaml — outputs clean list to stdout for manual review
- Uses live BingX endpoint (not VST demo) as source of truth for contract availability
- Pattern mirrors `scripts/test_connection.py` (standalone, single responsibility)
- No new test file — diagnostic utility only

### State changes
- Plan to create: `PROJECTS/bingx-connector/scripts/verify_coins.py` (~80 lines)
- Config manually updated after running script (user action)
- After script passes: `COUNTDOWN-TO-LIVE.md` step 3 marked done

### Open items recorded
- Run `python scripts/verify_coins.py` and review output
- If fails: copy clean list from stdout, paste into config.yaml
- Restart bot and verify warmup logs
- Wait for first signal (201 bars × 1m = ~3.4h warmup)

### Notes
None.

---

## 2026-02-26-bingx-5m-production-readiness.md
**Date:** 2026-02-26
**Type:** Session log / Planning

### What happened
Post-24h demo review of BingX bot on 1m timeframe. Bot ran for ~20.5 hours with zero crashes or exceptions, 105 trades opened and closed, daily P&L of -$354.27. 428 signals blocked by ATR filter ("Too Quiet"). ~90% of exits were EXIT_UNKNOWN (position monitor fell back to SL price estimate because BingX VST demo cleaned up conditional orders before the 60-second monitor check).

Three phases of work identified: Phase 1 (config + P0 bug fixes before restart), Phase 2 (reliability fixes for production), Phase 3 (observability improvements), Phase 4 (config tuning after 5m demo).

### Decisions recorded
- Switch timeframe to 5m (config.yaml line 4: "1m" -> "5m")
- Fix commission rate: `position_monitor.py` line 186: 0.001 -> 0.0008
- Fix EXIT_UNKNOWN: query BingX trade history for actual fill price
- Add daily reset on startup (compare session_start date to today)
- Add reconnection retry with exponential backoff (3 attempts, 1s/2s/4s + jitter)
- Add post-execution order validation (verify order_id != "unknown")
- Add graceful shutdown with threading.Event
- Warmup stays at 200 bars for safety (not reduced to 89)

### State changes
- Files to modify: config.yaml, position_monitor.py, data_fetcher.py, executor.py, main.py
- Commission rate overstating losses by ~25% (0.10% vs 0.08% per side)

### Open items recorded
- Run `python -m pytest tests/ -v` (67 tests must pass)
- Start bot on 5m, monitor first 30 minutes for warmup + first signal
- After first trade closes: verify exit_reason is no longer EXIT_UNKNOWN
- Verify Telegram alerts arrive with correct data

### Notes
1m performance as expected bad — consistent with backtester findings. 5m is the correct timeframe for production. Bot infrastructure confirmed solid (zero crashes over 20+ hours).

---

## 2026-02-26-bingx-bot-local-autostart.md
**Date:** 2026-02-26
**Type:** Planning

### What happened
Plan for local Windows auto-start with reboot persistence for the BingX bot. Context: VPS (Hostinger Jakarta) cannot reach BingX VST demo API (`open-api-vst.bingx.com` blocked from datacenter IPs); live API works fine on VPS via CloudFront CDN. Since demo mode needs to run first, bot runs locally. Three deliverables: PowerShell wrapper script (`run_bot.ps1`) with infinite restart loop, Windows Task Scheduler XML (`bingx-bot-task.xml`) for startup trigger, and install helper (`install_autostart.ps1`).

### Decisions recorded
- Wrapper: crash recovery + 30-second wait before restart
- Wrapper logs to `logs/YYYY-MM-DD-wrapper.log`
- Task Scheduler: triggers at system startup, runs with highest privileges, no stop on idle
- No changes to main.py, config.yaml, or any bot modules

### State changes
- Files to create:
  - `PROJECTS/bingx-connector/scripts/run_bot.ps1`
  - `PROJECTS/bingx-connector/scripts/bingx-bot-task.xml`
  - `PROJECTS/bingx-connector/scripts/install_autostart.ps1`

### Open items recorded
- User runs `install_autostart.ps1` from admin PowerShell
- User verifies "BingXBot" task exists in Task Scheduler GUI
- User tests by running `run_bot.ps1` manually
- User reboots to verify auto-start
- Kill test: kill python.exe from Task Manager, confirm wrapper restarts within 30s

### Notes
VPS cannot reach VST demo endpoint — confirmed blocker. Live API works from VPS but demo validation must happen locally.

---

## 2026-02-26-vault-organization-build.md
**Date:** 2026-02-26
**Type:** Build session (documentation/organization)

### What happened
Vault organization session addressing 5 areas of organizational debt: MEMORY.md exceeded 200-line limit (215 lines, truncated each session), 140+ session logs had no index, DASHBOARD-FILES.md was 9 days stale, PRODUCT-BACKLOG.md missing BingX/WEEX/Vince items, no single doc showing deployed systems. All pure documentation work.

Five steps completed:
1. MEMORY.md split from 215 lines to 84-line index + 7 topic files
2. `06-CLAUDE-LOGS/INDEX.md` created (140 markdown files indexed)
3. DASHBOARD-FILES.md updated (production corrected from v3.8.4 to v3.9.2)
4. PRODUCT-BACKLOG.md reconciled (5 new active items, 4 new completed items)
5. `LIVE-SYSTEM-STATUS.md` created with active systems table and pending deployments

### Decisions recorded
- MEMORY.md is a concise index only (under 200 lines)
- Detailed info lives in topic files in memory/ directory
- Topic files: TOPIC-vince-v2.md, TOPIC-backtester.md, TOPIC-dashboard.md, TOPIC-engine-and-capital.md, TOPIC-bingx-connector.md, TOPIC-yt-analyzer.md, TOPIC-critical-lessons.md

### State changes
- 9 new files created (7 topic files + INDEX.md + LIVE-SYSTEM-STATUS.md)
- 3 files modified (MEMORY.md reduced 215->84 lines, DASHBOARD-FILES.md corrected, PRODUCT-BACKLOG.md expanded)
- Dashboard production status corrected: was saying v3.8.4, now v3.9.2
- Backlog: P0.2 (BingX demo RUNNING), P0.3 (Dashboard v3.9.3 BLOCKED), P1.5 (WEEX Screener SCOPED), P1.6 (Strategy Scoping BLOCKED), P1.7 (Vince v2 plugin spec WAITING)

### Open items recorded
None stated in plan — all work marked complete.

### Notes
DASHBOARD-FILES.md had wrong production version (v3.8.4 instead of v3.9.2) for 9 days — corrected here.

---

## 2026-02-26-vault-vps-migration.md
**Date:** 2026-02-26
**Type:** Planning (step-by-step migration guide)

### What happened
Detailed migration guide for moving bot from local Windows PC to VPS (Jacky — 76.13.20.191, Ubuntu 24.04, 190GB free). Covers three parts: Part A (git setup on PC), Part B (VPS setup), Part C (ongoing workflow). Decisions: one flat git repo for entire vault (backtester .git removed), no cron, push from PC when work done, pull on VPS only when deploying, private repo `S23Web3/obsidian-vault`.

VPS architecture: bot runs on VPS (systemd, 24/7, auto-restart), ML/data stays on PC (RTX 3060 + 33GB data). Deploy command: `ssh root@76.13.20.191 "cd /root/vault && git pull && systemctl restart bingx-bot"`.

### Decisions recorded
- One flat repo for entire vault
- backtester's separate .git to be removed
- Private GitHub repo: S23Web3/obsidian-vault
- systemd service for bot on VPS (RestartSec=10, Restart=always)
- .gitignore excludes: 33GB data, .env, __pycache__, logs/, venv/, .pkl/.h5/.onnx, state.json/trades.csv

### State changes
- Plan creates one file: `C:\Users\User\Documents\Obsidian Vault\.gitignore`
- All other steps are manual commands (git, ssh)

### Open items recorded
- Part A: remove backtester .git, init vault repo, stage + commit, push to GitHub
- Part B: SSH to VPS, generate SSH key, clone vault, install Python 3.12 + venv, create .env, create systemd service
- Part C: ongoing push/deploy workflow

### Notes
VPS IP explicitly referenced: 76.13.20.191.

---

## 2026-02-26-vince-ml-scope-audit.md
**Date:** 2026-02-26
**Type:** Audit / Planning

### What happened
Comprehensive audit of Vince ML project status. Three distinct things called "Vince" identified: v1 (XGBoost/PyTorch classifier, BUILT but CONCEPTUALLY REJECTED), v2 (Trade Research Engine, CONCEPT WRITTEN but NOT APPROVED FOR BUILD), and existing reusable infrastructure (production backtester v3.8.4, signal pipeline, BBW pipeline, etc.).

Detailed side-by-side comparison of v1 vs v2: v1 asks "will this trade win or lose?" and reduces trade count (rejected because trade volume = rebate income); v2 asks "what patterns exist in my trades?" and never reduces trade count (approved direction). v2 uses frequency counting + permutation statistics, no trained ML model. v1 has 19 files, 2,643 lines, 37/37 tests — never deployed. v2 = concept doc only, zero code.

6 of 19 v1 modules identified as reusable in v2 (features_v3, triple_barrier, purged_cv, walk_forward, loser_analysis, coin_features). 7 modules NOT reusable (vince_model, training_pipeline, meta_label, bet_sizing, xgboost_trainer, staging files).

Document conflicts identified: `TOPIC-vince-v2.md` line 5 incorrectly says "APPROVED 2026-02-23" (wrong — concept not yet approved); `SPEC-C-VINCE-ML.md` describes v1 architecture; `BUILD-VINCE-ML.md` is 984-line v1 build spec.

### Decisions recorded
- Vince is NOT a classifier (confirmed as firm decision from 2026-02-18)
- Never reduce trade count (volume = rebate, confirmed 2026-02-18)
- Strategy-agnostic plugin architecture (confirmed 2026-02-20)
- Two-layer architecture (quant + LLM, confirmed 2026-02-20)
- Three operating modes (confirmed 2026-02-19)
- Tab 3 informational only (confirmed 2026-02-24)
- P1.7 (plugin interface spec) stays WAITING until concept approval

### State changes
- Identified: TOPIC-vince-v2.md has incorrect "APPROVED" status — needs correction
- Identified: SPEC-C-VINCE-ML.md should be marked SUPERSEDED
- Identified: BUILD-VINCE-ML.md should be marked ARCHIVED
- Identified: P1.2 "Deploy staging files" should be re-evaluated (staging files are v1 code)

### Open items recorded
1. Fix TOPIC file contradiction (correct "APPROVED" to "NOT YET APPROVED FOR BUILD")
2. User reads and approves concept v2 — single biggest blocker
3. Mark SPEC-C and BUILD-VINCE-ML as superseded/archived
4. Re-evaluate P1.2 backlog item
5. Formal plugin interface spec (P1.7) — first real build artifact
6. Scope trading LLM separately
7. Begin v2 build in order: plugin interface -> Enricher -> Analyzer -> Dashboard -> Optimizer -> Validator -> LLM

### Notes
This document explicitly flags that TOPIC-vince-v2.md line 5 is wrong ("APPROVED" is incorrect). The concept doc status was "NOT YET APPROVED FOR BUILD" at this date.

---

## 2026-02-26-vps-gitignore-deploy.md
**Date:** 2026-02-26
**Type:** Planning (build spec)

### What happened
Plan to build the vault-level `.gitignore` file needed for VPS migration. Bot confirmed production-ready (67/67 tests, 20.5h stable run, all fixes applied). Config already switched to 5m. Only missing piece: `.gitignore` file.

Two files to build: vault-level `.gitignore` (excludes ~33GB data + secrets + runtime artifacts) and updated bingx-connector `.gitignore` (add `logs/` and `venv/`). No code changes needed — all bot paths already cross-platform (uses `Path(__file__).resolve()`).

Timeline after VPS deploy: 0-16.7h = warmup (201 bars on 5m); 16.7h+ = signals fire; after 24h trading = run audit script to check exit reasons.

### Decisions recorded
- .gitignore excludes: data/ dirs (33GB), Books/, postgres/, .obsidian/, Tv.md, .env, __pycache__, venv/, logs/, *.pkl/*.h5/*.onnx, *.parquet, state.json/trades.csv, .DS_Store/Thumbs.db
- .gitignore keeps: all .md, .py, .yaml/.json, requirements.txt, existing sub-project .gitignore files
- No code changes to main.py or any bot module

### State changes
- Files to create/modify: vault `.gitignore` (new), bingx-connector `.gitignore` (update)

### Open items recorded
- User runs Part A (git setup), Part B (VPS setup), Part C (ongoing workflow)
- After 24h trading: run `python scripts/audit_bot.py` for real exit reasons

### Notes
Companion plan to 2026-02-26-vault-vps-migration.md — provides the specific .gitignore content that the migration guide referenced as "I will write this for you."

---

## 2026-02-27-automation-weex-screener-daily-report.md
**Date:** 2026-02-27
**Type:** Planning (build spec, 3 parallel agents)

### What happened
Plan for "proper automation" — closing the feedback loop. Three gaps identified: no live signal visibility across 100+ WEEX coins, no automated daily P&L Telegram report, vault stale after BingX docs scraper was built. Plan for 3 parallel build agents:

**Agent 1:** WEEX data layer (`weex_fetcher.py` + `weex_screener_engine.py`). Public WEEX API, no auth. Symbol format `BTC_USDT`. Endpoints: `/contract/klines`, `/contract/tickers`. Signal logic copied from backtester (NOT imported — no coupling to backtester path).

**Agent 2:** WEEX Screener UI (`weex_screener_v1.py`). Streamlit app with sidebar filters (min_atr_ratio, timeframe, signal filter, auto-refresh). Table with color-coded rows. Telegram alerts via existing `Notifier` class. Alert dedup by `alerted_this_session` set.

**Agent 3:** Daily P&L Report (`scripts/daily_report.py`). Reads trades.csv, filters to today, computes metrics, sends Telegram. Task Scheduler setup: daily at 17:00 UTC (21:00 local UTC+4).

### Decisions recorded
- Signal logic copied, not imported from backtester (no path coupling)
- All agents: docstrings mandatory, py_compile required, dual logging (file + console with timestamps)
- No escaped quotes in f-strings (use string concatenation for join())
- 3 agents run simultaneously — no cross-dependencies except Agent 2 using Agent 1's dict schema

### State changes
- Files to create: `screener/weex_fetcher.py`, `screener/weex_screener_engine.py`, `screener/weex_screener_v1.py`, `scripts/daily_report.py`
- Vault updates planned: LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md, TOPIC-bingx-connector.md

### Open items recorded
- py_compile all 4 files
- Run `streamlit run weex_screener_v1.py` and verify table loads
- Manually trigger Telegram alert
- Run `python daily_report.py` and verify Telegram message

### Notes
This is the WEEX screener scoping session — prior backlog items listed it as P1.5 SCOPED.

---

## 2026-02-27-bingx-api-docs-scraper.md
**Date:** 2026-02-27
**Type:** Planning (build spec)

### What happened
Plan to scrape BingX API docs site (JS-rendered SPA using Element UI) into a single indexed markdown reference. The site has ~215 leaf endpoint pages across 8 sections. Playwright MCP tools available for browser automation. Existing manual reference covers only 11 endpoints. Output: `docs/BINGX-API-V3-COMPLETE-REFERENCE.md`.

Two files: `scripts/scrape_bingx_docs.py` (main scraper) and `scripts/test_scraper.py` (4 tests). Script architecture: `BingXDocsScraper` class (nav expansion, tree collection, per-page extraction) + `MarkdownCompiler` class (TOC generation, markdown formatting). Per-page extraction via `page.evaluate()` JavaScript. Resume capability via `.scrape-progress.json` every 20 pages.

### Decisions recorded
- Dependencies: playwright only (stdlib for everything else)
- CLI args: `--output`, `--section`, `--test` (3 pages), `--debug`, `--timeout`
- Intermediate save every 20 pages for crash recovery
- Log to `logs/YYYY-MM-DD-scraper.log` with dual handler

### State changes
- Plan to create: `scripts/scrape_bingx_docs.py`, `scripts/test_scraper.py`
- Output doc to create: `docs/BINGX-API-V3-COMPLETE-REFERENCE.md` (~215 endpoints)
- This replaces/supersedes `BINGX-API-V3-REFERENCE.md` (11 endpoints)

### Open items recorded
1. py_compile both .py files
2. Run tests
3. `python scripts/scrape_bingx_docs.py --test --debug` (3 pages first)
4. `--section Swap --debug` (single section ~69 endpoints)
5. Full scrape (all ~215 endpoints, 5-10 min)

### Notes
None.

---

## 2026-02-27-bingx-bot-live-improvements.md
**Date:** 2026-02-27
**Type:** Planning (execution plan / runbook)

### What happened
Execution plan for applying P0 correctness fixes and P1 WebSocket improvements to BingX connector before live money deployment. Three P0 bugs identified via BingX API scrape: FIX-1 (commission rate hardcoded at 0.0012, should be 0.0016 from API), FIX-2 (entry price using mark_price instead of avgPrice from order response), FIX-3 (no SL direction validation before order placement). One P1 improvement: WebSocket ORDER_TRADE_UPDATE listener (`ws_listener.py`) to eliminate EXIT_UNKNOWN.

Steps 0-11 defined. Uses Ollama (qwen2.5-coder) for code generation. Per file: read source -> build Ollama prompt -> generate to `*_new.py` -> strip fences -> py_compile -> diff -> backup + replace. Pytest runs at steps 4, 8, 11 (must show 67/67).

Source plan: `fluffy-singing-mango.md`.

### Decisions recorded
- py_compile mandatory after every generated file
- Backup before overwrite: `cp file.py file.py.bak`
- User's AFK delegation interpreted as full autonomy override for pytest execution
- Session log: `06-CLAUDE-LOGS/2026-02-27-bingx-bot-live-improvements.md`
- All actions logged with timestamps in format `[YYYY-MM-DD HH:MM:SS] STEP N — ACTION: description`

### State changes
- Files to modify: executor.py (FIX-2, FIX-3), position_monitor.py (FIX-1, WS queue), main.py (commission fetch, WS thread)
- Files to create: ws_listener.py (WebSocket listener), scripts/reconcile_pnl.py
- Files to modify: state_manager.py (cooldown + 101209 handler), risk_gate.py

### Open items recorded
- Steps 2-11 remain after steps 0-1 done
- All 67 tests must pass after each phase
- .bak files must exist for every modified file after completion

### Notes
Commission rate discrepancy: plan says FIX-1 is 0.0012 should be 0.0016 from API — this differs from the prior plan (2026-02-26) which said 0.001 should be 0.0008. The API scrape revealed the correct rate; the prior plan was based on spec doc, not API docs. Potential contradiction.

---

## 2026-02-27-bingx-runbook-step-scripts.md
**Date:** 2026-02-27
**Type:** Planning (build spec)

### What happened
Follow-on to the live improvements plan. Steps 0-1 already done (executor.py has FIX-2+FIX-3, backup exists). Plan to build one master script `scripts/run_steps.py` to execute steps 2-11 unattended. Script shows full permission summary upfront (all files to modify, create, backup), user types `y` once, then all steps run sequentially with Ollama streaming visible.

Phase 1: permission request. Phase 2: sequential execution (Ollama for code generation, pytest at steps 4/8/11). Phase 3: summary report.

### Decisions recorded
- Single master script approach (not separate step scripts)
- Script halts immediately on py_compile failure or pytest < 67 passing
- All actions logged to `06-CLAUDE-LOGS/2026-02-27-bingx-bot-live-improvements.md`

### State changes
- Files to modify (steps 2-11): position_monitor.py, main.py, state_manager.py, risk_gate.py, executor.py (101209 only)
- Files to create: ws_listener.py, scripts/reconcile_pnl.py
- Master script: `scripts/run_steps.py` (new)

### Open items recorded
- Run: `cd "C:\...\bingx-connector" && python scripts/run_steps.py`
- Verify all 67 tests pass at end
- Verify .bak files exist for all modified files

### Notes
Clarifies that steps 0-1 were already done before this plan was written.

---

## 2026-02-27-dash-vince-skill-creation.md
**Date:** 2026-02-27
**Type:** Planning (skill creation spec)

### What happened
Plan to create a comprehensive Plotly Dash skill file for Vince v2 dashboard development. Context: Vince v2 requires an 8-panel Dash application. The constellation query builder (Panel 3) needs pattern-matching callbacks (MATCH/ALL) — the most complex Dash pattern. Dash 4.0.0 (released 2026-02-03) and dash-ag-grid 33.3.3 confirmed as target versions.

Skill file: `C:\Users\User\.claude\skills\dash\SKILL.md`, ~900 lines, two parts: Part 1 (Architecture & Perspective — Dash vs Streamlit comparison, mental model, app structure decision, Vince Store Hierarchy) and Part 2 (Deep Technical Reference — app setup, component reference, callback fundamentals, pattern-matching callbacks, dcc.Store, background callbacks, Plotly figures, dash_ag_grid, ML model serving, PostgreSQL, network/production, performance, code review checklist).

### Decisions recorded
- Dash 4.0.0 as framework (not Streamlit)
- Mandatory Dash skill load rule to be added to CLAUDE.md
- Vince uses multi-page app (pages/ folder, register_page) — 8 panels = separate page files
- dcc.Store hierarchy: 5 stores defined (enriched-trades=session, active-filters=memory, date-range=memory, session-meta=session, optimizer-results=memory)
- Server-side storage for large datasets (diskcache, session_id in dcc.Store, not raw DataFrame)
- `@callback` from `dash` (Dash 4.0 pattern, not `app.callback`)
- DiskcacheLongCallbackManager for dev, CeleryLongCallbackManager for prod

### State changes
- Files to create: `C:\Users\User\.claude\skills\dash\SKILL.md` (new)
- Files to create: vault plan copy (this file)
- Files to modify: `CLAUDE.md` (append Dash skill mandatory rule)

### Open items recorded
- Open skill in editor, confirm ~900 lines
- Test skill load in new Claude session

### Notes
Documents known Dash 4.0.0 bugs: #3628 (InvalidCallbackReturnValue in background callbacks), #3594 (dcc.Loading stops spinner before background callback completes), #3616 (Dropdown performance regression).

---

## 2026-02-27-project-overview-diagram.md
**Date:** 2026-02-27
**Type:** Planning (documentation build spec)

### What happened
Plan to create a cross-project master overview diagram (`PROJECT-OVERVIEW.md`) showing all 4 active projects, their status, and inter-project connections. Context: vault has 27 UML/diagram files but all are intra-project — no cross-project view exists. This was a high-output day (2026-02-27) with 6 sessions across 3 projects.

Mermaid graph defined with 4 subgraphs: Infrastructure (PostgreSQL, Ollama, VPS Jacky), Four Pillars Backtester, Vince ML v2, BingX Connector v1.0, YT Transcript Analyzer v2. Inter-project arrows defined (e.g., YT ML findings -> Vince concept, Engine plugin -> Bot, Ollama -> YT GUI).

State of each project as of 2026-02-27: BingX screener and daily report built, API docs scraped, Vince concept locked and APPROVED FOR BUILD, YT Analyzer v2.1 built with UX overhaul, Dashboard v3.9.3 BLOCKED.

### Decisions recorded
- One new file: `PROJECT-OVERVIEW.md` in vault root
- No existing files modified

### State changes
- Files to create: `PROJECT-OVERVIEW.md`, vault plan copy
- `INDEX.md` to be appended

### Open items recorded
- Open in Obsidian and verify Mermaid renders
- Cross-check inter-project arrows against LIVE-SYSTEM-STATUS.md
- Cross-check blockers against PRODUCT-BACKLOG.md P0 section

### Notes
Vince concept status shown as "LOCKED 2026-02-27" and "APPROVED FOR BUILD" in the diagram — this contradicts the 2026-02-26-vince-ml-scope-audit.md which said concept was NOT YET APPROVED. The approval happened between the audit (2026-02-26) and this plan (2026-02-27). Confirms concept was approved on 2026-02-27.

---

## 2026-02-27-vault-update-and-next-step.md
**Date:** 2026-02-27
**Type:** Planning (vault maintenance + status summary)

### What happened
Vault update plan after BingX demo validation completion and YT Analyzer v2 build. BingX demo ran for 18h with 31 trades on 5m timeframe. VST API confirmed too corrupted for strategy comparison (vanishing order history, wrong-direction fills, mark price drift). Decision: stop optimizing demo, move to live phase. Five files to update: LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md, TOPIC-bingx-connector.md, TOPIC-yt-analyzer.md, INDEX.md.

Project status summary: BingX Connector demo validated (awaiting live funds), API docs scraper built (needs one run), YT Analyzer v2 built, Dashboard v3.9.3 BLOCKED, Vince ML v2 concept approved (no build started), WEEX Screener scoped, BingX Live waiting on funds.

### Decisions recorded
- BingX demo analysis complete — VST API too unreliable for further optimization
- Move directly to live when funds transferred
- Next strategic step: Vince ML v2 plugin interface spec

### State changes
- LIVE-SYSTEM-STATUS.md: BingX Connector -> DEMO VALIDATED, add YT Analyzer row, add scraper row, remove stale week plan
- PRODUCT-BACKLOG.md: add YT Analyzer v2 and BingX demo analysis to Completed
- TOPIC-bingx-connector.md: add session summary (31 trades, -$379, 6 VST oddities)
- TOPIC-yt-analyzer.md: mark BUILT, add run command
- INDEX.md: append new log rows

### Open items recorded
- Run BingX API docs scraper (immediate)
- Vince ML v2 plugin interface spec (next session)

### Notes
Demo P&L stated as -$379 here vs -$354.27 in the 2026-02-26 plan — slight discrepancy, likely because the demo continued running between the two sessions.

---

## 2026-02-27-vince-b1-b10-build-plan.md
**Date:** 2026-02-27
**Type:** Planning (build roadmap)

### What happened
Formal build plan for Vince v2 as a unified Plotly Dash application, post-concept-approval. Vince is defined as the application itself — the dashboard serves Vince, not the other way around. The existing Streamlit dashboard (`scripts/dashboard_v392.py`, 2500 lines, 5 tabs) to be replaced by a Dash app.

8 panels defined with what each answers: Coin Scorecard (why does this coin keep losing?), PnL Reversal Analysis (PRIORITY — reversal anatomy), Constellation Query (when indicator X was in state Y, what happened?), Exit State Analysis (what moved before reversal?), Trade Browser (show individual trades), Settings Optimizer (what parameters work?), Validation (is the edge real?), Session History (what did I find last time?).

B1-B10 build order: FourPillarsPlugin -> API layer + types -> Enricher -> Panel 2 (PnL Reversal) -> Constellation Query Engine -> Dash app shell -> Panels 1/3/4/5 -> Mode 2 Auto-Discovery -> Mode 3 Settings Optimizer -> Panels 6/7/8.

Full file structure defined: `vince/` directory with `app.py`, `layout.py`, `api.py`, `types.py`, `enricher.py`, `query_engine.py`, `discovery.py`, `optimizer.py`, `pages/` (8 panel files), `assets/style.css`.

### Decisions recorded
- Framework: Plotly Dash (confirmed)
- Architecture: Vince IS the app — dashboard serves Vince
- Panel 2 (PnL Reversal) = highest priority build
- API layer (`vince/api.py`) = skeleton for both GUI and future agent
- Enricher storage: diskcache (session_id in dcc.Store, enriched trade set on disk — never raw DataFrame in browser)
- Future: RL Exit Policy overlay on Panel 2, LLM Interpretation (Panel 9), Agent

### State changes
- Concept status: APPROVED FOR BUILD (confirmed in this plan)
- Files to create: entire `vince/` directory structure

### Open items recorded
- B1 builds first: `strategies/four_pillars.py` (FourPillarsPlugin)
- Verification after B1-B6: `python vince/app.py` launches, Panel 2 shows MFE histogram

### Notes
Existing reusable code identified: base_v2.py (ABC), four_pillars_v383_v2.py (signals), backtester_v384.py, position_v384.py (Trade384 dataclass), commission.py, bbwp.py, ml/features.py, ml/walk_forward.py, research/bbw_monte_carlo.py.

---

## 2026-02-27-vince-concept-doc-update-and-plugin-spec.md
**Date:** 2026-02-27
**Type:** Planning (build spec — documentation + spec creation)

### What happened
Post-YT-analysis session plan. 202 videos analyzed (algo trading channel + FreeCodeCamp ML course) and 7 ML findings identified for Vince. This plan updates `VINCE-V2-CONCEPT-v2.md` with all 7 findings and begins P1.7 (formal plugin interface spec).

7 specific edits to concept doc defined: (1) add Panel 2 as highest-priority to "What Changed from v1", (2) expand Mode 2 Auto-Discovery with XGBoost feature importance pre-step + k-means clustering + held-out partition + reflexivity caution, (3) add new "RL Exit Policy Optimizer" section (full architecture), (4) update Mermaid flowchart with RL node, (5) label Panel 2 as "HIGHEST BUILD PRIORITY (v1)" in diagram, (6) add survivorship bias and reflexivity bullets to Constraints, (7) add RL optimizer as open question #7.

`VINCE-PLUGIN-INTERFACE-SPEC-v1.md` to be created: 7 sections covering purpose, ABC class definition, method contracts (compute_signals, parameter_space, trade_schema, run_backtest, strategy_document), OHLCV DataFrame contract, Enricher contract, Compliance Checklist, FourPillarsPlugin compliance mapping.

### Decisions recorded
- Concept doc status stays "NOT YET APPROVED FOR BUILD" (concept approval not part of this plan)
- P1.7 backlog status stays WAITING
- No Python code written in this session

### State changes
- Files to modify: `VINCE-V2-CONCEPT-v2.md` (7 edits)
- Files to create: `VINCE-PLUGIN-INTERFACE-SPEC-v1.md`, vault plan copy
- Files to modify: `memory/TOPIC-vince-v2.md` (update status + new files)

### Open items recorded
- After implementation: verify 7 additions present, status still says "NOT YET APPROVED"
- Verify plugin interface spec has all 7 sections

### Notes
This plan says concept doc status "NOT YET APPROVED" — but the build plan (2026-02-27-vince-b1-b10-build-plan.md) written the same day says "APPROVED FOR BUILD." This likely represents two sessions on the same day, with approval happening between them. The concept-doc-update plan may have been written before the concept was approved, and the lock-and-build-roadmap + b1-b10 plans were written after approval.

---

## 2026-02-27-vince-concept-lock-and-build-roadmap.md
**Date:** 2026-02-27
**Type:** Planning (pre-approval discussion)

### What happened
Pre-approval planning document for Vince v2. Concept doc has been in scoping since 2026-02-18. User requirements stated: proper GUI (advanced Dash/Streamlit, not throwaway), agent-ready skeleton (clean API layer), core focus (analysis engine + GUI first, agent + RL + LLM = later phases).

Two things needed to be added to concept doc before locking: GUI section (framework decision, layout, key UX) and architecture skeleton (API layer with clean Python functions for both GUI and future agent). Build order B1-B9 proposed: FourPillarsPlugin -> API layer -> Enricher -> Panel 2 -> Constellation Query -> Dash GUI (Panels 1-4) -> Mode 2 Auto-Discovery -> Mode 3 Optimizer -> Dash GUI (Panels 5-7).

Three decisions needed from user: Dash or Streamlit?, is concept correct?, is build order right?

### Decisions recorded
- Agent-ready API layer to be built now as skeleton
- Agent itself is future iteration
- Scope: core analysis engine + GUI first

### State changes
- This appears to be the planning session BEFORE concept approval
- GUI section and architecture skeleton to be added to concept doc
- Status to change from draft to "APPROVED FOR BUILD" after user confirmation

### Open items recorded
- User to confirm: Dash or Streamlit, concept correctness, build order
- After confirmation: add GUI + skeleton sections to concept doc, lock it, start B1

### Notes
This is likely the earliest plan in the 2026-02-27 Vince sequence. Build order here has B6 as "Dash GUI Panels 1-4" and B9 as "Dash GUI Panels 5-7" — slightly different numbering than the b1-b10 plan which has B6 as "Dash app shell" and B7 as "Panels 1/3/4/5." Minor restructuring between the two plans.

---

## 2026-02-27-yt-analyzer-v2-structured-output.md
**Date:** 2026-02-27
**Type:** Planning (build spec)

### What happened
Plan to transform YT Transcript Analyzer v1 output from raw text dump into structured, navigable output with clickable YouTube timestamp links, LLM-generated summaries, and auto-tags. Problems identified: timestamps discarded in cleaner.py, no clickable YouTube links, no LLM summaries, no tags, unstructured report, unpredictable output path (relative), unexplained 15/211 subtitle gap in GUI, no re-run without re-download capability.

6 files to modify: `config.py` (fix OUTPUT_PATH to absolute), `cleaner.py` (preserve timestamps as `[MM:SS]` markers, extract video_id, write metadata comment), `summarizer.py` (NEW — LLM summary + auto-tags via qwen3:8b), `reporter.py` (rewrite with TOC, summaries, tags, clickable YouTube timestamp links), `gui.py` (Summarize stage, download stats, output path display), `fetcher.py` (track subtitle success/skip counts).

YouTube timestamp URL format: `https://www.youtube.com/watch?v=VIDEO_ID&t=SECONDS`. Example format: `[05:23](https://www.youtube.com/watch?v=cTJ0Qbz0eAI&t=323)`.

Extensive test scenarios (T1-T6) and debug protocols (D1-D6) defined.

### Decisions recorded
- Timestamps as `[MM:SS]` text markers (human-readable AND machine-parseable, not separate metadata files)
- Summarizer is separate module (can be skipped in drain-fast mode)
- Video titles from existing `manifest_videos.json`
- YouTube links as standard markdown
- VTT filename regex: `^\d{8}-([a-zA-Z0-9_-]{11})-` (date + 11-char video ID)
- OUTPUT_PATH: `Path(__file__).parent / "output"` (project-relative, not CWD-relative)

### State changes
- Files to modify: config.py, cleaner.py, reporter.py, gui.py, fetcher.py
- Files to create: summarizer.py (new)

### Open items recorded
- py_compile all 6 modified files
- Run drain on small channel (5-10 videos) to verify timestamps, summaries, links
- Run query mode and verify timestamp links in findings
- Spot-check 3 random YouTube timestamp links for accuracy

### Notes
None.

---

## 2026-02-27-yt-analyzer-v21-ux-overhaul.md
**Date:** 2026-02-27
**Type:** Planning (build spec — UX overhaul)

### What happened
UX overhaul plan for YT Analyzer after first real run discovered 10 usability problems (211 videos, 201 transcripts, 50+ minute summarize stage). Problems: no cancel button, invisible progress (overwrites self), no output preview, no output folder control, channels mix into same output/, summarize too slow with no opt-out, no ETA, no resume awareness, no re-run without re-download, no download button.

Per-channel namespacing (problem 5) deferred — requires refactoring all `from config import X` to `import config; config.X`. All other 9 problems addressed in v2.1.

3 files to modify: `gui.py` (full rewrite), `fetcher.py` (add `on_process_started` callback), `summarizer.py` (extended callback + `_cached` tag).

### Decisions recorded
- Per-channel namespacing deferred (too much refactoring)
- All other 9 UX problems addressed in v2.1
- gui.py gets full rewrite (not incremental edit)

### State changes
- Files to modify: gui.py (full rewrite), fetcher.py, summarizer.py

### Open items recorded
None explicitly stated in this plan (it's a spec, implementation follows separately).

### Notes
This is a follow-on to the v2 structured output plan — written after the first real run of v2 revealed UX problems.

---

## 2026-02-27-yt-channel-ml-findings-for-vince.md
**Date:** 2026-02-27
**Type:** Research findings document

### What happened
Compiled ML findings from analyzing 202 YT transcripts (algo trading channel + FreeCodeCamp ML course). 14 numbered findings organized in 3 tiers. Tier 1 (directly applicable now, 4 findings): unsupervised clustering for Mode 2 auto-discovery, XGBoost feature importance to prioritize Mode 2 sweep, RL exit policy optimizer (main finding), random entry + ATR stops = exits matter more than entries. Tier 2 (applicable to specific components, 9 findings): walk-forward rolling windows, survivorship bias, reflexivity, held-out partition for Mode 2, GARCH volatility, LSTM stationarity warning, NLP sentiment, Bayesian NN, Transformer attention. Plus 6 general validated facts.

Key finding: RL for exit policy. Environment = trade lifecycle. Episode = one trade. State = [bars_since_entry, current_pnl_in_atr, k1-k4_now, cloud_state_now, bbw_now]. Action = HOLD or EXIT. Reward = pnl_at_exit minus commission. Train on enriched trade historical data, test on held-out period. RL exit learner does NOT change entry signals.

Stochastics + RSI consistently top-ranked across all ML feature importance studies — validates Four Pillars indicator choice.

### Decisions recorded
- RL Exit Policy Optimizer = new Vince component between Enricher and Dashboard
- Panel 2 (PnL Reversal Analysis) is highest build priority
- Mode 2 to include: clustering pre-step + XGBoost feature importance pre-step + held-out partition + reflexivity caution
- Survivorship bias caveat to be added to all pattern results

### State changes
- This is a findings document (read-only analysis output)
- 7 items to update in Vince v2 concept doc identified

### Open items recorded
- Update VINCE-V2-CONCEPT-v2.md with 7 findings (see companion plan 2026-02-27-vince-concept-doc-update-and-plugin-spec.md)

### Notes
RL finding: constraint satisfaction explicitly stated — RL does NOT reduce trade count (entries unchanged, only exits modified). Consistent with Vince's core non-negotiable. Video sources cited for each finding with YouTube video IDs.


# Batch 14 Findings — Dated Plans (2026-02-28 to 2026-03-02)

---

## 2026-02-28-b2-api-types-research-audit.md
**Date:** 2026-02-28
**Type:** Planning / Research Audit

### What happened
Research audit of the B2 build block for Vince v2. B2 covers `vince/types.py` (all dataclasses) and `vince/api.py` (clean Python API functions, no Dash imports). The `vince/` directory did not yet exist at time of writing. The audit identified the existing files that B2 wraps (`strategies/base_v2.py`, `engine/position_v384.py`, `signals/four_pillars.py`, `engine/commission.py`, `data/db.py`) and precisely scoped B2 to 3 new files: `vince/__init__.py`, `vince/types.py`, `vince/api.py` (stubs only raising `NotImplementedError`). Seven API function signatures were drafted. Seven design bottlenecks were identified and documented as blockers requiring user decisions before coding could start.

### Decisions recorded
- B2 scope explicitly: `vince/__init__.py`, `vince/types.py`, `vince/api.py` — stubs only, no logic implementation
- B2 does NOT implement enricher, query, or optimizer logic
- Both Python skill and Dash skill are mandatory before writing any vince/ directory file
- `py_compile` required on all 3 files after creation
- api.py stubs must raise `NotImplementedError` (not silent `pass`)

### State changes
- No files created; this is a research/audit document only
- Identified 7 open design questions blocking build: (1) active plugin pattern (module-global vs per-call), (2) EnrichedTradeSet (dataclass list vs DataFrame), (3) ConstellationFilter (typed vs dict), (4) SessionRecord fields, (5) run_enricher corrected signature, (6) MFE bar definition, (7) what counts as a session

### Open items recorded
- All 7 design questions explicitly listed as blocking the build
- Corrected `run_enricher` signature proposed: `(trade_csv, symbols, start, end, plugin)` vs concept doc's incomplete `(symbols, params)`
- Bar index alignment noted as B1 problem but B2 must document requirement

### Notes
- This is a research-only document; the actual build plan for B2 came on 2026-03-02 after design verdicts were locked.

---

## 2026-02-28-b3-enricher-research-audit.md
**Date:** 2026-02-28
**Type:** Research Audit / Planning

### What happened
Full audit of the B3 Enricher build block for Vince v2. B3 takes a trade CSV from any `StrategyPlugin.run_backtest()` call, loads OHLCV + indicator data, looks up indicator state at three critical bars per trade (entry, MFE, exit), and attaches snapshot columns. `diskcache` is used for caching. The audit confirmed existing files (StrategyPlugin ABC, signal pipeline, Trade384, backtester, OHLCV parquet cache) and documented missing components (`vince/enricher.py`, `vince/cache_config.py`, `strategies/four_pillars_plugin.py`, `diskcache` package not installed). Six critical blockers were identified with detailed analysis.

### Decisions recorded
- B3 scope: modify `engine/position_v384.py` (add `mfe_bar`), create `strategies/four_pillars_plugin.py`, create `vince/__init__.py`, `vince/enricher.py`, `vince/cache_config.py`, plus tests
- `diskcache` must be installed before B3 can be built (`pip install diskcache`)
- Recommended cache: `FanoutCache` with 8 shards (for Optuna concurrency)
- Recommended OHLC storage: 4 separate columns (`entry_open`, `entry_high`, `entry_low`, `entry_close`) rather than tuples or JSON strings
- Column naming: rename in FourPillarsPlugin wrapper (option A — safest, no signal pipeline breakage)
- Cache directory: `data/vince_cache/` (separate from `data/cache/`)
- Cache key design: `f"{symbol}_{timeframe}_{params_hash}"`
- Enricher should be a context manager for clean Windows file handle management
- FanoutCache size limit: `size_limit=2 * 1024 ** 3` (2 GB cap)

### State changes
- No files created; research document only
- Six implementation improvements identified (Numba ATR sharing, raw stoch values in output, trade_schema mfe_bar/mae_atr fields, cache size cap, context manager pattern, compliance CLI)

### Open items recorded
- 8 open questions listed (Q1 through Q8)
- Q1 (mfe_bar tracking) explicitly called "the single most important decision before build starts"
- Q1 three options: (A) modify position_v384.py directly, (B) create position_v385.py, (C) Enricher second-pass over OHLCV
- Q7: which signal pipeline version (standard or Numba) — recommendation: standard first for correctness
- BLOCKER: `diskcache` not installed

### Notes
- The MFE bar question (Q1) is explicitly flagged as the critical dependency for Panel 4 (Exit State Analysis) and Panel 2 (PnL Reversal) functionality.

---

## 2026-02-28-bingx-be-fix-handover.md
**Date:** 2026-02-28
**Type:** Handover Prompt (for next session)

### What happened
A structured handover prompt designed to be pasted as the opening message of the next chat session. Focuses on the breakeven (BE) stop fix for the BingX live bot ($5 margin, 10x = $50 notional). Previous session had confirmed TTP (Approach C) was implemented. This session was scoped to BE fix only. The document provided the problem statement (stop placed at wrong price — raw entry_price instead of entry + commission RT), math verification (`True BE for LONG = entry × 1.0024`), the dollar impact ($0.08-$0.13 per trade on $50 notional), investigation steps (read position_monitor.py, check current BE stop price formula, review live logs, review trades.csv), and four approaches to fix (A: fix stop price only; B: add slippage buffer; C: change to STOP_LIMIT; D: replace with TAKE_PROFIT_MARKET).

### Decisions recorded
- Scope strictly limited to: `_place_be_sl()`, `check_breakeven()`, `BE_TRIGGER` constant
- Out of scope: SL logic, trailing TP, new entries, risk gate
- Fix must be proportionate to trade size ($0.08-$0.13 error on $50 notional)
- User was to be AFK — thorough autonomous investigation required
- py_compile must pass on all changed files
- Session log target: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-be-fix.md`

### State changes
- No code written; this is a session handover prompt document only

### Open items recorded
- Investigation steps 1-8 listed (read position_monitor.py, verify math, check BE_TRIGGER, check order type, read trades.csv, read live logs, read TOPIC file, read TTP session log)
- Deliverable format specified: implementation table, true BE math, approaches list, comparison table, recommended approach with implementation

### Notes
- The document correctly calculates true BE exit for LONG: `entry × (1 + 0.0016) / (1 - 0.0008) ≈ entry × 1.0024`, not simply `entry_price`.

---

## 2026-02-28-bingx-dashboard-design.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Design plan for the BingX live trading dashboard. Marked as a correction from a previous session that "built read-only twice" despite the user saying "position management." This plan explicitly states the dashboard is interactive (not read-only). Data sources: `state.json`, `trades.csv`, `config.yaml`, and optional BingX mark price API. Layout designed as a single Dash page with 5 sections: Bot Status Banner, Summary Cards (4 cards), Open Positions AG Grid (with management actions: Raise BE, Move SL), Today's Performance stats row, Closed Trades table. Technical decisions: Plotly Dash, port 8051, 60s refresh, direct JSON read, optional mark price API, `dash_ag_grid`. Single output file: `bingx-connector/dashboard.py`.

### Decisions recorded
- Dashboard IS interactive — "position management" means interactive controls (Raise BE, Move SL)
- Port 8051 (8050 reserved for Vince)
- Refresh interval: 60s (matches bot's position_check_sec)
- Dashboard reads files directly (not through StateManager) — read-only on data access but interactive on API calls
- Mark prices: optional BingX REST call via bingx_auth.py, graceful skip if no .env keys
- Future interactive features (manual close, SL adjust) deferred as separate build

### State changes
- No files created; design document only
- This supersedes/corrects the previous read-only dashboard design approach

### Open items recorded
- Mark price fetch toggle desired
- Note: "position management without interactivity = read-only" explicitly rejected by this plan

### Notes
- This plan references a rule violation from the prior session (MEMORY.md entry: user said "position management" — built read-only twice). This plan re-scopes correctly.

---

## 2026-02-28-bingx-dashboard-v1-1-build-spec.md
**Date:** 2026-02-28
**Type:** Build Spec (very large — 83.8KB)

### What happened
Complete, self-contained build specification for BingX Live Dashboard v1-1. A full Plotly Dash 4.0 app replacing the prior Streamlit-based `bingx-live-dashboard-v1.py`. Specification covers: output files (`bingx-live-dashboard-v1-1.py`, `assets/dashboard.css`), dependencies (dash, dash-ag-grid 33.3.3, plotly, pandas, pyyaml, requests, python-dotenv), run commands (local + gunicorn VPS), data sources (state.json, trades.csv, config.yaml, .env), architecture (single-file, 5 tabs, `dcc.Tabs`, `dcc.Store` pattern, `dcc.Interval` 60s), color constants, BingX API client (signed requests, `_sign()`, `_bingx_request()`), and a complete inventory of all functions and callbacks (Groups A-D: data loaders, data builders, chart builders, layout helpers; CB-1 through CB-14+). Key interactive features: CB-6 (Raise to Breakeven — cancel SL + place new STOP_MARKET at entry_price), CB-7 (Move SL — user-specified price), CB-12 (Save Config — atomic YAML write with diff report), CB-13/CB-14 (Halt/Resume bot via halt_flag in state.json). The spec also covers AG-Grid column definitions for positions, history, and coins views.

### Decisions recorded
- `suppress_callback_exceptions=True` — tab IDs don't exist at startup (dynamic content from CB-5)
- `prevent_initial_call=False` for CB-1 (data loader) and CB-2 (tab renderer)
- `prevent_initial_call=True` for all other callbacks
- CB-6 and CB-7 can both output to `pos-action-status` because they have different Inputs
- `server = app.server` required at module level for gunicorn
- `fetch_all_mark_prices` uses `ThreadPoolExecutor(max_workers=8)`
- API signing: replicated `_sign()` pattern (not imported from bot internals)
- Every callback wrapped in try/except; PreventUpdate re-raised before outer except
- Every def has one-line docstring
- Atomic writes via tmp + `os.replace()`
- Dual logging: file + StreamHandler, `TimedRotatingFileHandler`
- config.yaml validation rules defined (sl_atr_mult 0-10, leverage 1-125, etc.)

### State changes
- Specification document only; no files created from this spec yet at plan-writing time
- This spec was consumed by the build session that produced `bingx-live-dashboard-v1-1.py`

### Open items recorded
- VPS deployment: need `dash_auth.BasicAuth` before production (controls real money)
- Mark price API rate limit consideration noted

### Notes
- Code verification: `bingx-live-dashboard-v1-1.py` EXISTS on disk at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-1.py` — confirms the build was executed.

---

## 2026-02-28-bingx-dashboard-v1-1-build.md
**Date:** 2026-02-28
**Type:** Build Plan

### What happened
Execution plan for building the v1-1 dashboard based on the spec in `C:\Users\User\.claude\plans\goofy-dancing-summit.md` (1795 lines). Previous session hit context limit before writing code. This plan specifies building 3 files: `bingx-live-dashboard-v1-1.py` (~700 lines), `assets/dashboard.css` (~20 lines), `scripts/test_dashboard.py` (~170 lines). Build steps listed: load Dash skill, write main dashboard, write CSS, write test script, py_compile on both .py files, give run command.

### Decisions recorded
- Dash skill must be loaded before any code is written
- `suppress_callback_exceptions=True` confirmed
- `prevent_initial_call=False` for CB-1 and CB-2 only
- Every callback wrapped in try/except
- Dual logging with `TimedRotatingFileHandler`
- Existing v1 (Streamlit): `bingx-live-dashboard-v1.py` — DO NOT TOUCH
- User runs everything; never execute on their behalf

### State changes
- Build execution plan only; confirms 3 files are to be created
- References spec stored in system plan path: `C:\Users\User\.claude\plans\goofy-dancing-summit.md`

### Open items recorded
- py_compile must pass before delivery
- User run commands specified for test and launch

### Notes
- Code verification: `bingx-live-dashboard-v1-1.py` EXISTS on disk — confirms build was executed successfully.

---

## 2026-02-28-bingx-dashboard-v1-2-build.md
**Date:** 2026-02-28
**Type:** Build Plan

### What happened
Build plan for dashboard v1-2, addressing 8 issues found during live testing of v1-1. Issues: white form inputs, white ag-grid background, no date range picker, slow tab switching, no timing diagnostics, amateur analytics metrics, missing plotly toolbar cleanup. Plan specifies one build script (`scripts/build_dashboard_v1_2.py`) producing 3 files: overwritten `assets/dashboard.css` (28 → ~95 lines), new `bingx-live-dashboard-v1-2.py` (~1750 lines), overwritten `scripts/test_dashboard.py`. Delta table maps each section of v1-1 to v1-2 changes. Key changes: FIX-4 replaces dynamic tab rendering with all-tabs-in-layout + clientside visibility toggle (eliminates tab switch re-render); FIX-3 adds date range pickers; ANALYTICS-1 expands from 7 to 13 metric cards. Gotchas documented: `suppress_callback_exceptions` must stay `True`, `gross_pnl` alias kept for grade comparison, string formatting uses `.format()` not f-strings in build script to avoid escaped quote rule.

### Decisions recorded
- FIX-4: all tabs rendered in layout, visibility toggled via clientside callback (Option A chosen over B and C)
- FIX-3: `dcc.DatePickerRange` replaces "Today only" checkbox in History; added to Analytics
- ANALYTICS-1: 13 metric cards including Sharpe, MaxDD%, BE Hit, LSG% (last two = "N/A" until bot tracks data)
- `hist-today-filter` Checklist component REMOVED — only CB-8 references it
- `math.sqrt(365)` for Sharpe annualization requires `import math`
- LSG% and BE Hit Count deferred — require `be_raised` and MFE written to trades.csv (bot change, not dashboard scope)
- Build script uses `.format()` not f-strings to avoid escaped quote MEMORY rule

### State changes
- Plan document; build script and output files created in the session
- `bingx-live-dashboard-v1-2.py` created — confirmed exists on disk

### Open items recorded
- LSG% deferred: needs MFE tracking in position_monitor.py
- BE Hit Count deferred: needs `be_raised` written to trades.csv on close

### Notes
- Code verification: `bingx-live-dashboard-v1-2.py` EXISTS on disk — confirms execution.

---

## 2026-02-28-bingx-dashboard-v1-2-improvements.md
**Date:** 2026-02-28
**Type:** Audit / Issue Log

### What happened
Source document for the v1-2 build plan — captures the 8 user-reported issues from v1-1 live testing with root cause analysis, fix options, and severity ratings. Same content as v1-2-build.md but structured as a requirements/issue document rather than a build plan. FIX-3 root cause: tab content recreation on each switch destroys child callback outputs. FIX-4 root cause: CB-2 renders_tab recreates entire tab layout on each switch. Analytics blocker: `be_raised` in state.json per open position but NOT written to trades.csv on close; LSG needs MFE tracking not yet implemented.

### Decisions recorded
- FIX-4 Option A selected: render all tabs, toggle visibility (immediate, no reload flash)
- LSG and BE data explicitly marked as BLOCKER — requires bot changes before dashboard can show real values
- Analytics cards: expand from 7 to 13
- Charts: add `config={'displayModeBar': False}` to all `dcc.Graph` components

### State changes
- Requirements document only; execution done via v1-2-build.md plan

### Open items recorded
- LSG%: requires MFE tracking in position_monitor.py
- BE Hit Count: requires `be_raised` written to trades.csv on close
- Both blocked on bot changes, not dashboard changes

### Notes
- Duplicates some content from v1-2-build.md but provides more detailed root cause analysis.

---

## 2026-02-28-bingx-dashboard-vince-b1-b6.md
**Date:** 2026-02-28
**Type:** Session Build Plan (daily)

### What happened
Master daily build plan for 2026-02-28 covering two tracks: (1) BingX live trades dashboard and (2) Vince B1 through B6. Token conservation rules stated: build every file directly, no agents, process order (dashboard first then B1→B2→B3→B4→B5→B6), user verifies after each block. Ollama (qwen3:8b) designated for boilerplate-only files (vince/types.py, __init__.py files, CSS). The plan defined data schemas for state.json and trades.csv, panel layouts for the BingX dashboard (6 panels: summary cards, open positions, closed trades, exit breakdown, grade analysis, cumulative PnL), and scopes for each Vince block (B1=FourPillarsPlugin, B2=API types, B3=Enricher, B4=PnL Reversal, B5=Constellation Query, B6=Dash shell). Files explicitly marked as NOT to be modified: `strategies/base_v2.py`, `signals/four_pillars_v383_v2.py`, `engine/backtester_v384.py`, `PROJECTS/bingx-connector/main.py`.

### Decisions recorded
- Build order: dashboard first, then B1→B2→B3→B4→B5→B6
- Ollama to handle boilerplate files (zero Claude tokens)
- B2 `vince/types.py`: Ollama. `vince/api.py`: Claude
- B6 `vince/__init__.py`, `vince/pages/__init__.py`, `vince/assets/style.css`: Ollama. `vince/layout.py`, `vince/app.py`: Claude
- LSG% note: "Bot does not store MFE — LSG lives in Vince Panel 2, not here" (for BingX dashboard)
- NEVER TOUCH specified files list

### State changes
- Daily plan document; this session executed blocks across both tracks

### Open items recorded
- End state: BingX dashboard running at localhost + `python vince/app.py` launches with sidebar and all panel routes + Panel 2 (PnL Reversal/LSG) functional

### Notes
- This is the overarching session plan; individual block plans are in separate files. The Ollama delegation for boilerplate is a recurring token-saving strategy.

---

## 2026-02-28-bingx-friend-handover-package.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan for creating a BingX futures trading bot knowledge handover package for a friend. Output: `PROJECTS/bingx-connector/docs/BINGX-FRIEND-HANDOVER.md` (~400 lines) plus the existing `BINGX-API-V3-COMPLETE-REFERENCE.md` (224 endpoints). The handover document structure covers: authentication (HMAC-SHA256, THE #1 BUG = URL encoding before hashing), 11 critical gotchas (signature URL encoding, commission rate, fill price, recvWindow, leverage API hedge mode, listenKey POST vs GET, listenKey response format variants, WebSocket gzip compression, WebSocket heartbeat, VST geoblocking, order history purge), key endpoints curated from 224 (14 endpoints listed), order placement pattern, WebSocket user data stream setup, bot architecture patterns (dual-thread design), risk gate (8 pre-trade checks), exit detection strategy, state machine & recovery, deployment checklist.

### Decisions recorded
- Two-file package: handover guide + raw API reference
- 11 gotchas to include, ordered by severity
- 14 key endpoints curated (not all 224)
- Sources: executor.py, ws_listener.py, position_monitor.py, state_manager.py, risk_gate.py, main.py, API reference doc, TRADE-UML, audit-report.md, session logs

### State changes
- Plan document only; handover file to be created at `PROJECTS/bingx-connector/docs/BINGX-FRIEND-HANDOVER.md`

### Open items recorded
- Verification steps: all 11 gotchas present, correct auth code snippet, all 14 endpoints in table, deployment checklist present

### Notes
- The #1 bug (URL encoding before HMAC signing) is called out as critical — "every order fails without this."

---

## 2026-02-28-bingx-trade-analysis.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan for a trade analysis script covering 196 closed trades from trades.csv across 3 phases with different notionals ($500, $1500, $50). Existing `scripts/audit_bot.py` treats all trades flat — meaningless because notionals differ. Plan: new `scripts/analyze_trades.py` for phase-segmented analysis. Phase detection by notional_usd. Phase 1 (103 trades, $500 notional, 1m, Feb 25-26): flagged as UNRELIABLE — all EXIT_UNKNOWN/SL_HIT_ASSUMED. Phase 2 (47 trades, $1500, 5m, Feb 26-27): primary signal quality data. Phase 3 (46 trades, $50, 5m, Feb 27-28): live account data. Report sections: dataset overview, Phase 1 flagged unreliable, Phase 2 deep dive (grade/direction/exit breakdown/symbol leaderboard/hold time), Phase 3 deep dive (same + % of notional), combined signal quality (Phase 2+3), key findings (auto-generated). Stdlib only (csv, datetime, pathlib, collections — no pandas). Output: markdown file + console + dated log file.

### Decisions recorded
- New script `analyze_trades.py` (not modifying existing `audit_bot.py` — separate purposes)
- Stdlib only, no pandas dependency
- Phase 1 shown but explicitly marked UNRELIABLE
- Phase detection: notional_usd == 500/1500/50

### State changes
- Plan document; script to be created at `PROJECTS/bingx-connector/scripts/analyze_trades.py`

### Open items recorded
- Verification: py_compile pass + all 6 sections present + 103+47+46=196 trades + Phase 1 flagged

### Notes
- Code verification: `PROJECTS/bingx-connector/scripts/analyze_trades.py` EXISTS on disk — confirms execution.

---

## 2026-02-28-bingx-ttp-research-and-comparison.md
**Date:** 2026-02-28
**Type:** Research / Strategy Analysis

### What happened
Full trailing take profit (TTP) research for the BingX live bot. Context: 0 TP_HIT exits in 47 live trades (46 SL_HIT, 1 EXIT_UNKNOWN) because `tp_atr_mult: null` was set for live trading but no trailing TP replacement was built. BE raise is working but is only a floor, not a profit-locker. The document catalogued 6 TTP examples (E1 Fixed ATR, E2 ATR Trailing HTF, E3 AVWAP 3-stage, E4 AVWAP 2σ + 10-candle counter, E5 BingX Native Immediate, E6 BingX Native with Activation), documented current implementation state (Fixed TP removed, BE raise built, everything else not built), coded each approach with complexity/pros/cons, and produced a full comparison table across 5 approaches (A through E).

### Decisions recorded
- Phased recommendation: immediate = Approach C (TRAILING_STOP_MARKET with activation at 2×ATR profit, 2% callback), later = Approach D (AVWAP 2σ trigger)
- Approach A (fixed TP) rejected: only 8.5% TP hit rate in demo 5m
- Approach B (immediate trailing) rejected: activates on noise, 2% callback from tiny 0.5% peak
- Approach D deferred: 150 lines + AVWAP per bar = highest live risk for now
- Approach E (ratchet) noted as complementary to C, not primary
- Files to modify for Approach C: `executor.py`, `config.yaml` (add `trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`), `tests/test_executor.py`

### State changes
- Research document; implementation planned for Approach C
- Session log to be created at: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-ttp-research.md`

### Open items recorded
- Verification: py_compile on executor.py, pytest test_executor.py, watch bot log for `TRAILING_STOP_MARKET placed`, confirm in BingX open orders UI, watch for fill in trades.csv

### Notes
- The 10-candle AVWAP design (E4) is confirmed as user's intended design from prior TOPIC file entry.

---

## 2026-02-28-dash-skill-trading-dashboard-enrichment.md
**Date:** 2026-02-28
**Type:** Planning (skill update)

### What happened
Plan to add trading-dashboard-specific knowledge to the Dash skill file (`C:\Users\User\.claude\skills\dash\SKILL.md`). At time of plan creation, the skill was 1,064 lines covering architecture, callbacks, multi-page structure, Vince store hierarchy, components, ag-grid, ML serving, PostgreSQL, gunicorn, performance. Ten gaps identified (candlestick, real-time patterns, panel taxonomy, equity/drawdown, relayoutData sync, ag-grid conditional formatting, timezone handling, order book, rolling metrics, alert patterns). New section "PART 3 — TRADING DASHBOARD KNOWLEDGE" to be appended with 8 subsections (candlestick charts, panel taxonomy, real-time patterns, equity/drawdown, multi-chart sync, ag-grid conditional formatting, timezone-aware data, order book). Version bump to v1.1.

### Decisions recorded
- Knowledge-dense, concise — no large code walls
- Part 3 appended after Part 2, before Version History
- Frontmatter description keywords added: candlestick, equity curve, drawdown, real-time, dcc.Interval, live data, order book
- Vault copy required at `06-CLAUDE-LOGS/plans/2026-02-28-dash-skill-trading-dashboard-enrichment.md` (this file)

### State changes
- Plan document; SKILL.md update to be applied

### Open items recorded
- Verification: read SKILL.md to confirm 8 subsections, v1.1 version history, frontmatter keywords, no existing sections modified

### Notes
- This file IS its own vault copy per CLAUDE.md requirement.

---

## 2026-02-28-dash-skill-v12-community-audit.md
**Date:** 2026-02-28
**Type:** Session log (completed work)

### What happened
Community audit of the Dash skill conducted via WebSearch (WebFetch to community.plotly.com was blocked by permission hook). 15+ real practitioner discussions from community.plotly.com and GitHub issues (#64121, #355, #608, #3628, #3594) were retrieved and analyzed. Seven categories of undocumented gotchas were found: (1) extendData + Candlestick strict format, ghost artifact bug, trace index requirement, performance cliff at 2500+ bars; (2) dcc.Interval blocking if callback exceeds interval; (3) relayoutData + Candlestick infinite loop bug; (4) ag-grid styleConditions silently overrides textAlign, Math not available in condition strings; (5) WebSocket vs dcc.Interval — for <500ms needs, WebSocket non-negotiable; (6) background callback overhead meaningful only for >10s tasks, APScheduler + gunicorn without `--preload` = silent duplication; (7) rangebreaks performance cliff with >2 years of bar data. Part 4 was added to SKILL.md.

### Decisions recorded
- WebSearch used instead of WebFetch (different tool, not subject to the blocked hook)
- Part 4 appended to SKILL.md: "Community-Sourced Traps & Patterns"
- Use `cellStyle` function (JS) instead of `styleConditions` for complex ag-grid logic
- `xaxis.autorange = False` workaround for relayoutData infinite loop

### State changes
- SKILL.md modified: was 1447 lines (v1.1), now 1726 lines (v1.2)
- 7 new sections added to Part 4

### Open items recorded
None stated.

### Notes
- This document records completed work, not just a plan. SKILL.md was actually updated.

---

## 2026-02-28-dashboard-v393-validate-promote.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan to validate and promote the backtester dashboard v3.9.3 to production. The product backlog (P0.3) marked v3.9.3 as BLOCKED with "IndentationError at line 1972" but this was found to be stale — `py_compile` was already passing on the file. The actual remaining work was runtime validation + doc updates. v3.9.3 changes vs v3.9.2: stale cache fix (sidebar settings clear equity curves), sweep symbol persistence, selectbox key fix, PDF download button added. Steps: (1) user runs `streamlit run` and checks 7-item checklist, (2) update docs (PRODUCT-BACKLOG.md, LIVE-SYSTEM-STATUS.md, DASHBOARD-FILES.md, PROJECT-OVERVIEW.md), (3) add trailing newline to v3.9.3, (4) ask user before deleting 3 dead fix scripts.

### Decisions recorded
- Stale backlog entry identified and corrected — py_compile already passes
- Doc update files listed: PRODUCT-BACKLOG.md, LIVE-SYSTEM-STATUS.md, DASHBOARD-FILES.md, PROJECT-OVERVIEW.md
- Dead scripts to ask user about (not auto-delete): build_dashboard_v393.py, build_dashboard_v393_fix.py, fix_v393_indentation.py

### State changes
- Plan document; actual promotion depends on user running the runtime test

### Open items recorded
- User must run runtime validation before docs can be updated
- Trailing newline to be added
- Dead scripts pending user decision

### Notes
- The stale backlog entry is a pattern: IndentationError was fixed during a prior session but the backlog was not updated.

---

## 2026-02-28-parquet-data-catchup.md
**Date:** 2026-02-28
**Type:** Planning (data maintenance)

### What happened
Short plan for updating 1m candle parquet files stale by 15 days (last fetch: 2026-02-13). No build needed. Existing infrastructure (`scripts/fetch_data.py`, `data/fetcher.py` BybitFetcher class, `data/cache/` with 399 coins) handles it. Run command given: `python scripts/fetch_data.py --months 1`. Script is restartable, rate-limited at 0.1s between requests, 5m candles skipped per prior user decision.

### Decisions recorded
- No new code needed
- 5m candles: skipped (1m only — per prior user decision)

### State changes
- No files created; run command provided for user to execute

### Open items recorded
- Verification: check for `Symbols fetched: 399/399` in output, spot-check .meta file end date

### Notes
- Data source: Bybit v5 API. 399 coins in cache.

---

## 2026-02-28-vince-b1-plugin-scope-audit.md
**Date:** 2026-02-28
**Type:** Research Audit / Planning

### What happened
Full audit and scope document for B1 (FourPillarsPlugin) build. Referenced `BUILD-VINCE-B1-PLUGIN.md` which did not exist at time of writing (was generated by this research). Key discovery: `strategies/four_pillars.py` already existed as a v1 partial implementation — not v2-compliant. 6 specific issues documented: wrong base class (v1 ABC not v2), 4 missing required methods, wrong signal version (`state_machine_v383.py` instead of `four_pillars_v383_v2.py`), wrong `compute_signals` signature, split enrichment method, legacy v1 classifier methods. NEVER OVERWRITE rule requires archiving to `strategies/four_pillars_v1_archive.py` first. Scope: one target file (strategies/four_pillars.py rewrite). 5 methods fully specified with implementation details. Four pre-build questions identified (file conflict, signal version mismatch, backtester_v385.py vs v384, no `symbol` field in Trade384, date filter mechanism).

### Decisions recorded
- NEVER OVERWRITE: create `strategies/four_pillars_v1_archive.py` backup first
- B1 scope: 5 methods (compute_signals, parameter_space, trade_schema, run_backtest, strategy_document property)
- `strategy_document`: point to `docs/FOUR-PILLARS-STRATEGY-UML.md`
- `run_backtest` output: write to `results/vince_{timestamp}.csv`, return Path
- `parameter_space()` sweepable params: sl_mult, tp_mult, be_trigger_atr, be_lock_atr, cross_level, allow_b_trades, allow_c_trades
- Thread safety: Backtester384 instantiated fresh per call — thread-safe
- Bar index note: entry_bar/exit_bar are 0-based indices into DATE-FILTERED slice; Enricher must use same slice

### State changes
- Research document; actual build to follow

### Open items recorded
- 4 pre-build confirmation questions listed (signal version, engine version, file conflict, date filter column name)
- Verification suite provided: syntax check, interface smoke test, compute_signals smoke test, full backtest smoke test

### Notes
- `backtester_v385.py` found alongside v384 — build plan specifies v384, requires confirmation. This was a discovery finding, not a resolution.

---

## 2026-02-28-vince-doc-sync.md
**Date:** 2026-02-28
**Type:** Session log (completed work — documentation sync)

### What happened
Master documentation sync operation for Vince v2 project state after 5 research sessions on 2026-02-28. Ran as an agent-executable instruction set. Created 5 new build docs (BUILD-VINCE-B2-API.md through BUILD-VINCE-B6-DASH-SHELL.md), updated 6 existing files (VINCE-V2-CONCEPT-v2.md, VINCE-PLUGIN-INTERFACE-SPEC-v1.md, INDEX.md, PRODUCT-BACKLOG.md, TOPIC-vince-v2.md, plus this plan file). BUILD-VINCE-B1-PLUGIN.md was skipped as it already existed (469 lines). Design verdicts for B2 were locked and documented: (1) plugin passed per-call (not global), (2) EnrichedTradeSet as DataFrame, (3) ConstellationFilter = typed fields + column_filters dict, (4) SessionRecord = named research session. Corrected run_enricher signature documented. Complete type definitions for all 7 dataclasses documented.

### Decisions recorded
- All B2 design verdicts locked (4 listed above)
- B2 through B6 all marked BLOCKED in status: B2 READY TO BUILD (after B1), B3-B6 BLOCKED on B1→B2→B3
- PRODUCT-BACKLOG updated: P0.5 updated, P1.8 (B2), P1.9 (B3), P2.5 (B4), P2.6 (B5), P2.7 (B6) added

### State changes
- 5 BUILD docs created in backtester project directory
- VINCE-V2-CONCEPT-v2.md: Build Status table prepended
- VINCE-PLUGIN-INTERFACE-SPEC-v1.md: Implementation Status table prepended
- INDEX.md: 4 new 2026-02-28 rows added
- PRODUCT-BACKLOG.md: B2-B6 entries added
- TOPIC-vince-v2.md: B1-B4 Research Sessions section appended

### Open items recorded
- Verification checklist listed (6 checks) to confirm all updates landed

### Notes
- This document reports completed execution, not just a plan. It is an execution log masquerading as a plan file.

---

## 2026-03-02-b2-api-types-build.md
**Date:** 2026-03-02
**Type:** Session log (completed build)

### What happened
B2 was built ahead of B1 because it has zero strategy dependency. Strategy (v386, state machine, exit logic) needed review before B1 could wrap it. B2 delivered: `vince/__init__.py`, `vince/types.py` (8 dataclasses), `vince/api.py` (8 API stubs), `vince/audit.py` (13-check auditor), `tests/test_b2_api.py` (5 test groups), `scripts/build_b2_api.py` (validation runner). All py_compile passed. Design verdicts locked on 2026-02-28 were used directly. Additional deliverable this session: strategy analysis report for Claude Web review (`scripts/build_strategy_analysis.py` producing `docs/STRATEGY-ANALYSIS-REPORT.md` with full source dump + 6 discussion questions).

### Decisions recorded
- B2 built ahead of B1 (unusual order — justified by zero strategy dependency)
- Strategy v386 review required before B1 can proceed
- Audit file added (`vince/audit.py` with 13-check auditor) — not originally in B2 spec
- Strategy analysis report added as additional deliverable for external Claude Web alignment session

### State changes
- 6 files created in backtester project:
  - `vince/__init__.py`
  - `vince/types.py` (8 dataclasses)
  - `vince/api.py` (8 API stubs)
  - `vince/audit.py` (13-check auditor)
  - `tests/test_b2_api.py` (5 test groups)
  - `scripts/build_b2_api.py`
- `docs/STRATEGY-ANALYSIS-REPORT.md` created by build script

### Open items recorded
- B1 blocked on strategy review/correction before wrapping
- Expected output when running build_b2_api.py: py_compile PASS + smoke tests PASS + CRITICAL audit findings (expected — document strategy issues, not B2 bugs)

### Notes
- Code verification: `vince/types.py` EXISTS on disk, `vince/api.py` EXISTS on disk — confirms build was executed.
- Note: `vince/audit.py` was an addition not in the original B2 spec from 2026-02-28.

---

## 2026-03-02-bingx-dashboard-patch6-7-css-statusfeed.md
**Date:** 2026-03-02
**Type:** Build Plan

### What happened
Plan for two patches to BingX dashboard v1-3. Patch 6 (CSS variables override): Dash 2.x injects CSS custom properties via `:root` in `dcc.css` — specifically `--Dash-Fill-Inverse-Strong: #fff`. Class-level `!important` cannot override CSS variables; must override at `:root`. Patch appends a block of ~12 `:root` variable overrides to `assets/dashboard.css`. Guard check prevents double-application. Timestamped backup created before modification. Patch 7 (bot status feed): adds live startup lifecycle messages to the Operational tab. Creates `bot-status.json` schema (bot_start + messages array). Modifies 4 files: `main.py` (adds `write_bot_status()` helper + 7 call sites at startup milestones, `STATUS_PATH` constant, overwrites bot-status.json at process start), `data_fetcher.py` (adds `progress_callback=None` to `warmup()`, fires every 5 symbols), `bingx-live-dashboard-v1-3.py` (adds `dcc.Store`, `dcc.Interval` at 5s, status feed panel UI in Operational tab, 2 new callbacks CB-S1 and CB-S2), `assets/dashboard.css` (status feed panel styles). Each patch has its own build script.

### Decisions recorded
- Patch 6: CSS variable override at `:root` level (only way to beat Dash 2.x injected variables)
- Patch 7: `bot-status.json` written atomically (tmp + os.replace) to avoid partial reads
- Progress callback fires every 5 symbols (not every symbol — avoid flooding file)
- Dashboard polls bot-status.json every 5s (separate from main 60s interval)
- Status feed shows last 20 messages, newest first
- Bot-status.json overwritten fresh at every process start (clear stale messages from prior run)

### State changes
- Build scripts to be created:
  - `scripts/build_dashboard_v1_3_patch6.py`
  - `scripts/build_dashboard_v1_3_patch7.py`
- Files to be modified: `assets/dashboard.css`, `bingx-live-dashboard-v1-3.py`, `main.py`, `data_fetcher.py`

### Open items recorded
- Patch 6 verification: restart dashboard, open date picker/dropdown, confirm dark background
- Patch 7 verification: restart bot, bot-status.json created, restart dashboard, status feed shows messages

### Notes
- Code verification: `scripts/build_dashboard_v1_3_patch6.py` EXISTS on disk, `scripts/build_dashboard_v1_3_patch7.py` EXISTS on disk — confirms both patches were executed.
- Root cause of persistent white backgrounds correctly identified: Dash 2.x CSS variable injection, not class-level rules.


# Research Findings — Batch 15: Dated Plans (2026-03-02 to 2026-03-05)

Generated: 2026-03-06
Files processed: 20

---

## 2026-03-02-git-push-vault-update.md
**Date:** 2026-03-02 (inferred from filename)
**Type:** Planning

### What happened
Plan to push all new and updated vault files to GitHub (`git@github.com:S23Web3/Vault.git`, branch `main`). The vault had ~170 items in `git status` (27 modified, ~143 untracked) since the initial commit `1e1c49b`. Plan identified four items needing user decision before proceeding: `*.bak.*` files (9 files, not caught by existing `*.bak` rule), `.playwright-mcp/` directory (local MCP config), `.claude/settings.local.json` (local Claude Code permissions), and `PROJECTS/yt-transcript-analyzer/output/` (608 generated files).

Recommended additions to `.gitignore`: `.playwright-mcp/`, `.claude/settings.local.json`, `*.bak.*`, `PROJECTS/yt-transcript-analyzer/output/`. Then `git add .`, commit, push.

### Decisions recorded
- Add `.playwright-mcp/` to `.gitignore` (machine-specific)
- Add `.claude/settings.local.json` to `.gitignore` (machine-specific)
- Add `*.bak.*` to `.gitignore` (backup files, not deliverables)
- Add `PROJECTS/yt-transcript-analyzer/output/` to `.gitignore` (generated output)

### State changes
Plan document only — no files modified in this plan itself. Proposed commit message: `"Vault update: bingx connector live + dashboards, vince build specs, yt analyzer v2, session logs"`.

### Open items recorded
None stated — plan is ready for execution pending user approval on flagged items.

### Notes
The actual commit with message `"Vault update: bingx connector live + dashboards, vince build specs B1-B6, yt analyzer v2, session logs"` appears in git history as `0b12d60`. A later commit `914a1b2` also references vault updates. The plan's staging categories match what went into subsequent commits.

---

## 2026-03-03-audit-fix-cuda-bingx.md
**Date:** 2026-03-03
**Type:** Build session / Audit

### What happened
Full plan for executing audit bug fixes across four files: `engine/cuda_sweep.py`, `scripts/dashboard_v394.py`, `bingx-connector/ws_listener.py`, and `bingx-connector/position_monitor.py`. Defines a single build script `build_audit_fixes.py` that patches all four files using string replacement, then runs `py_compile` + `ast.parse` on each.

Seven findings were documented from a prior audit session:

**CRITICAL #1**: Commission split error in CUDA kernel — same rate used for both taker entry (0.0008) and maker exit (0.0002). Fix: add `maker_rate=0.0002` parameter to `run_gpu_sweep()`, split into `entry_comm` and `exit_comm`.

**CRITICAL #2**: `pnl_sum` missing entry commission — only exit cost subtracted at close, making `pnl_sum` not equal to `equity - 10000`. Fix: `pnl_sum += net_pnl - entry_comm` at both exit points.

**HIGH #3**: `win_rate` displayed as raw decimal in three dashboard table locations (GPU Sweep top-20, portfolio per-coin top-5, uniform top-10). Fix: multiply by 100, rename column to `win_rate%`.

**HIGH #4**: TTP state lost on restart — REASSESSED as already fixed in `signal_engine.py` lines 113-127. No action needed.

**HIGH #5**: `WSListener` dies permanently after 3 reconnect failures with no alert. Fix: increase `MAX_RECONNECT` to 10, add exponential backoff, write `logs/ws_dead_{timestamp}.flag` after exit.

**HIGH #6**: `_place_market_close()` missing `reduceOnly` — REASSESSED as low risk in hedge mode since `positionSide` already scopes the close. Decision: add `"reduceOnly": "true"` defensively.

**HIGH #7**: `saw_green` uses `>` instead of `>=` at CUDA kernel lines 163/171. Fix: change to `>=` / `<=`.

### Decisions recorded
- CRITICAL #1 and #2: Fix commission split and pnl_sum
- HIGH #3: Format win_rate as % in three table locations
- HIGH #5: MAX_RECONNECT=10, exponential backoff, dead flag file
- HIGH #6: Add `reduceOnly` defensively
- HIGH #7: Fix saw_green comparison operators
- HIGH #4: No action (already fixed)

### State changes
Plan document only. Build script `build_audit_fixes.py` to be created at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_audit_fixes.py`.

### Open items recorded
Several items deferred as MEDIUM/LOW: stale detection for sweep param ranges, Shared Pool capital model enforcement, TTP mid-bar timing, race condition, commission rate fallback mismatch, no slippage protection, close-remaining missing counters, UI tweaks, lock gaps in BingX.

### Notes
The file `PROJECTS/four-pillars-backtester/scripts/build_audit_fixes.py` appears in git status as untracked (`??`), confirming the build script was created. The prior audit (HIGH #4 reassessment) overrides any earlier claim that TTP state restoration was broken.

---

## 2026-03-03-be-auto-ttp-trigger.md
**Date:** 2026-03-03 (inferred from context)
**Type:** Build plan

### What happened
Plan to replace the 0.16% distance-based breakeven trigger (`BE_TRIGGER = 1.0016`) with TTP activation as the sole auto-BE trigger. Three files to modify: `position_monitor.py`, `bingx-live-dashboard-v1-4.py`, `config.yaml`.

Key changes:
- Remove `BE_TRIGGER` constant and mark price API fetch from `check_breakeven()`
- New trigger: `pos_data.get("ttp_state") == "ACTIVATED"` — already in state, no extra API call
- New `be_auto` config key (default `true`) with dashboard toggle (dcc.Checklist)
- Full rewrite of `check_breakeven()` provided with exact Python code

Dashboard changes: add `ctrl-be-auto` checklist to Strategy Parameters tab, wire into CB-11 (load config) and CB-12 (save config).

### Decisions recorded
- Replace distance-based BE trigger with TTP activation trigger
- `be_auto` config key added under `position:` section
- Dashboard toggle added for user control
- Keep `_fetch_mark_price_pm()` method (may be used elsewhere)
- Keep `_place_be_sl()` and `_cancel_open_sl_orders()` unchanged

### State changes
Plan document only. Modifies `position_monitor.py`, `bingx-live-dashboard-v1-4.py`, `config.yaml`.

### Open items recorded
None stated.

### Notes
This plan changes the BE trigger logic. Earlier plan `2026-03-03-audit-fix-cuda-bingx.md` had assessed HIGH #4 (TTP state restoration) as already fixed. This plan builds on that by using ttp_state as the BE trigger.

---

## 2026-03-03-bingx-dashboard-v1-4-patch4-close-market.md
**Date:** 2026-03-03
**Type:** Build session

### What happened
Plan to run `build_dashboard_v1_4_patch4.py` which adds a "Close Market" button to the position action panel and a new CB-16 callback. Context confirms patches 1-3 were already applied to `bingx-live-dashboard-v1-4.py` (2293 lines at time of writing).

Two anchor points verified before running:
- P1: `html.Button("Move SL"` at line 1379 — verified present, unique
- P2: `# CB-8: History Grid` at line 1586 — verified present, unique

Patch 4 adds:
- P1: Red `html.Button("Close Market", id="close-market-btn")` after Move SL
- P2: CB-16 callback before CB-8 — cancels all open orders for symbol, places MARKET reduceOnly close, writes `close_pending=True` to state.json

CB-16 uses `prevent_initial_call=True` and `allow_duplicate=True` on `pos-action-status`.

### Decisions recorded
- Close Market placed as red button after Move SL
- CB-16 uses prevent_initial_call=True
- State: `close_pending=True` written on execution

### State changes
Plan for build script `build_dashboard_v1_4_patch4.py` at `PROJECTS/bingx-connector/scripts/`. Target: `bingx-live-dashboard-v1-4.py`.

### Open items recorded
Verification checklist: build output (2/2 PASS, py_compile PASS), button visible in Live Trades tab, click with no row selected fires PreventUpdate, click with row selected shows status, log shows market close lines, no new IndexError/KeyError.

### Notes
File `PROJECTS/bingx-connector/scripts/build_dashboard_v1_4_patch4.py` appears in git status as `??` (untracked), confirming it was created.

---

## 2026-03-03-cuda-dashboard-v394-spec.md
**Date:** 2026-03-03
**Type:** Build plan / Handover document

### What happened
Corrected handover spec for building CUDA GPU sweep capability and Numba JIT portfolio speedup for the Four Pillars dashboard. Explicitly marked as superseding the earlier `2026-03-03-cuda-sweep-engine.md` plan (which contained 4 pre-audit errors).

Key corrections vs earlier plan:
- Param grid shape is [N_combos, 4], NOT [N_combos, 5] (notional is scalar, not per-combo)
- TP sentinel is 999.0, NOT 0.0 (0.0 = instant exit at entry price)
- Signal arrays are 12, NOT 10 (reentry_long/short + cloud3_ok_long/short added)
- Per-thread position state uses `cuda.local.array()`, NOT Python lists
- Sharpe uses Welford's online variance (no per-trade list in GPU kernel)
- Column names: `reentry_long`/`reentry_short` confirmed (NOT `re_long`/`re_short`)
- Python wrapper must extract `cloud3_allows_long`/`cloud3_allows_short` from DataFrame (internal kernel names can differ)

Architecture: CUDA kernel for GPU sweep (2,112 combos), `jit_backtest.py` for CPU-compiled portfolio, `dashboard_v394.py` copy of v392 with GPU Sweep mode + portfolio JIT path + sidebar GPU panel.

Build script `scripts/build_cuda_engine.py` creates 3 files (NOT 4 — `sweep_all_coins_v2.py` deferred).

### Decisions recorded
- Base dashboard on v392 (not v393, even though v393 passes py_compile)
- Defer `sweep_all_coins_v2.py` to next session
- TP sentinel: 999.0 (not 0.0)
- Param grid: 4 columns [sl_mult, tp_mult, be_trigger_atr, cooldown]
- Kernel simplifications documented (no AVWAP ratcheting, no scale-outs, etc.)

### State changes
Plan document. Files to create: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/dashboard_v394.py`, `scripts/build_cuda_engine.py`.

### Open items recorded
Memory files to update after build: `TOPIC-backtester.md`, `TOPIC-dashboard.md`, `LIVE-SYSTEM-STATUS.md`, `PRODUCT-BACKLOG.md`.

### Notes
This document explicitly supersedes `2026-03-03-cuda-sweep-engine.md`. The v394 dashboard and cuda_sweep.py files appear in git status as modified (`M`), confirming this build was completed.

---

## 2026-03-03-cuda-sweep-engine.md
**Date:** 2026-03-03
**Type:** Planning (superseded)

### What happened
Original architecture plan for CUDA acceleration of the Four Pillars backtester sweep engine and dashboard v394. Documents GPU thread model (one thread per parameter combo), input arrays (10 arrays), param grid (5-column including notional), and intended build script creating 4 files.

Key specs in this version (later found to have errors):
- `re_long`/`re_short` as reentry column names (wrong — should be `reentry_long`/`reentry_short`)
- Param grid: [sl_mult, tp_mult, be_trigger, cooldown, notional] — 5 columns (wrong — notional is scalar)
- TP sentinel: 0.0 = no TP (wrong — 0.0 = instant exit at entry price)
- `cloud3_ok_long`/`cloud3_ok_short` as column names for DataFrame extraction (wrong — `cloud3_allows_long/short`)
- Dashboard "GPU Sweep" implemented as a tab (later spec changes to a mode)

Build script creates 4 files: `cuda_sweep.py`, `jit_backtest.py`, `sweep_all_coins_v2.py`, `dashboard_v394.py`.

### Decisions recorded
None — this plan was superseded by `2026-03-03-cuda-dashboard-v394-spec.md`.

### State changes
Plan document only. Superseded.

### Open items recorded
None — superseded.

### Notes
This plan is explicitly overridden by `2026-03-03-cuda-dashboard-v394-spec.md` which documents 4 errors found during audit. The corrected plan deferred `sweep_all_coins_v2.py` and fixed the column names, tp_mult sentinel, and param grid shape.

---

## 2026-03-03-cuda-v394-spec-audit.md
**Date:** 2026-03-03
**Type:** Audit

### What happened
Audit of the `2026-03-03-cuda-dashboard-v394-spec.md` handover document against actual source code. Found 3 issues (2 critical, 1 minor).

**ISSUE 1 — CRITICAL: Backtester Version Mismatch**
Spec claims dashboard uses `Backtester390`. Actual: `dashboard_v392.py` imports `Backtester384` (line 278) and `compute_signals_v383`. The v390 files exist but are not used by the active dashboard. Decision required: match v3.8.4 for result parity (Option A) vs match v3.9.0 as spec describes (Option B — results won't match CPU sweep).

**ISSUE 2 — CRITICAL: Column Name Inconsistency**
Spec uses `cloud3_ok_long/short` for kernel variable names but actual DataFrame columns are `cloud3_allows_long/short`. Python wrapper must use `cloud3_allows_long/short` when extracting from DataFrame.

**ISSUE 3 — MINOR: v393 IndentationError Claim**
Spec says v393 has an IndentationError. Actual: v393 (127KB) passes py_compile. Low impact since plan already uses v392 as base.

Verified facts: mode chain is correct, reentry columns are `reentry_long/reentry_short`, position slots are 4, direction conflict gate is correct, portfolio is sequential, `compute_params_hash()` exists (MD5-based), all target files don't exist yet.

### Decisions recorded
None explicitly in this document — it raises the critical question: which engine version should the CUDA kernel replicate (v3.8.4 for parity vs v3.9.0 as spec describes)?

### State changes
Audit document only. No code changed.

### Open items recorded
Decision needed: which engine version for CUDA kernel — v3.8.4 or v3.9.0?

### Notes
This audit was produced before the corrected spec (`2026-03-03-cuda-dashboard-v394-spec.md`). The corrected spec uses v390 as the reference. This implies the decision was to use v390 (Option B) and accept some divergence from the v392 CPU sweep results.

---

## 2026-03-03-daily-bybit-updater.md
**Date:** 2026-03-03
**Type:** Build plan

### What happened
Plan for a daily incremental Bybit data updater script. Context: backtester data cache (399 coins, `data/cache/`) is stale — last updated 2026-02-13. New standalone script (not patching `fetch_data.py`) that discovers symbols, fetches only new candles since last cached timestamp, resamples to 5m, and logs results.

Four CLI modes: default (update all), `--months N`, `--skip-new`, `--skip-resample`, `--max-new N`, `--dry-run`.

Design decisions:
- Standalone script (not a patch of existing fetcher)
- Reuses `BybitFetcher` from `data/fetcher.py` for fetch logic
- Reuses `TimeframeResampler` from `resample_timeframes.py` for 5m resampling
- Incremental append logic lives in `daily_update.py` itself (not patched into fetcher)
- Rate limiting: 0.12s between requests
- 3 retries with exponential backoff

### Decisions recorded
- New standalone script, not a patch of `fetch_data.py`
- Reuse existing modules (BybitFetcher, TimeframeResampler)
- Incremental logic in the new script only

### State changes
Plan document. Creates: `scripts/build_daily_updater.py` (build script), `scripts/daily_update.py` (created by build). Both appear as `??` in git status, confirming creation.

### Open items recorded
User runs `--dry-run` first, then `--max-new 5` for test batch, then full run.

### Notes
The file `PROJECTS/four-pillars-backtester/scripts/build_daily_updater.py` appears in git status as `??` (untracked), confirming creation. `daily_update.py` itself is not listed — may have been created by the build script or may be named differently.

---

## 2026-03-03-dashboard-v1-4-patch3-ttp-display.md
**Date:** 2026-03-03
**Type:** Build plan

### What happened
Comprehensive plan for TTP (Trailing Take Profit) engine integration with the BingX connector and dashboard. Covers two build scripts: `build_ttp_integration.py` (connector files) and `build_dashboard_v1_4_patch3.py` (dashboard only).

Context: `ttp_engine.py` drafted by Opus with 4 bugs; BingX connector has no TTP logic; fixed ATR-TP order placed at entry currently.

Architecture — hybrid (split evaluation and execution):
- **Thread 1 (signal_engine.py)**: TTP evaluation using real 1m OHLC candles per `on_new_bar()` call
- **Thread 2 (position_monitor.py)**: TTP close execution via `check_ttp_closes()` reading `ttp_close_pending` flag

4 ttp_engine.py bug fixes:
1. `self.state` never set to CLOSED — add in `_evaluate_long`/`_evaluate_short`
4. Replace `CLOSED_PARTIAL` state with `"CLOSED"` everywhere
5. Replace `iterrows()` with `itertuples()`
6. Guard `band_width_pct` with proper None check

Files modified/created: `ttp_engine.py` (CREATE), `signal_engine.py` (MODIFY), `position_monitor.py` (MODIFY), `main.py` (MODIFY), `config.yaml` (MODIFY), `bingx-live-dashboard-v1-4.py` (MODIFY), `tests/test_ttp_engine.py` (CREATE).

Dashboard changes (Patch 3): Add TTP + Trail Lvl columns to positions grid, add TTP section to Controls tab (toggle, activation %, trail distance %), wire into CB-11/CB-12.

### Decisions recorded
- TTP evaluation in signal_engine (market loop thread), execution in position_monitor
- `ttp_close_pending` flag bridges threads via state.json
- Race guard: verify position exists on exchange before placing MARKET close
- Existing fixed TP orders still placed at entry — TTP runs alongside
- Config under `position:` section: `ttp_enabled: false`, `ttp_act: 0.005`, `ttp_dist: 0.002`
- `TTP_EXIT` exit reason in trades.csv

### State changes
Plan document. Build scripts to create. Multiple source files to be modified.

### Open items recorded
Verification: 10-step checklist including race test (SL fires first, TTP close skipped cleanly).

### Notes
This plan is labeled `cuddly-dancing-perlis.md` in its header (`**Plan file:**`), suggesting it was created from plan mode under that internal name. Confirms pre-existing bugs in executor.py and state_manager.py were agent transcription errors, not real bugs.

---

## 2026-03-03-git-cleanup-gitignore-backlog-commit.md
**Date:** 2026-03-03
**Type:** Planning

### What happened
Plan to fix VSCode "too many active changes" warning caused by untracked `.venv312/` (thousands of files), 37 `.bak*` backup files, and runtime artifacts. Two-step plan: update `.gitignore`, then commit all legitimate backlog.

New `.gitignore` patterns to append:
- `.venv/`, `.venv312/`, `.venv*/`, `venv*/`, `env/`, `.env/` (venv variants)
- `PROJECTS/bingx-connector/bot.pid`, `PROJECTS/bingx-connector/bot-status.json` (runtime state)
- `*.bak.*`, `*.bak.py`, `*.bak.css`, `*.bak.js` (build backup files)

Note: root `.gitignore` already has `**/venv/` but NOT `.venv312/` (dot prefix = different pattern).

Explicit decision: `06-CLAUDE-LOGS/plans/` directory is TRACKED in git (include in commit).

Proposed commit message: `"Backlog commit: bingx-connector v1.4, backtester engine updates, session logs 2026-02-28 to 2026-03-03"`.

### Decisions recorded
- `.venv312/` added to `.gitignore`
- `bot.pid` and `bot-status.json` excluded from git
- `*.bak.*` patterns added
- Plans directory tracked (not excluded)
- Commit all remaining untracked/modified files as one backlog commit

### State changes
Plan document. Target: `C:\Users\User\Documents\Obsidian Vault\.gitignore` (append 8 new lines). Git commit `914a1b2` with this exact message appears in git history, confirming execution.

### Open items recorded
None.

### Notes
Git history shows `914a1b2 Backlog commit: bingx-connector v1.4, backtester engine updates, session logs 2026-02-28 to 2026-03-03` — exact match to planned commit message, confirming this plan was executed.

---

## 2026-03-03-next-steps-roadmap.md
**Date:** 2026-03-03
**Type:** Planning / Roadmap

### What happened
Comprehensive next-steps roadmap for Four Pillars / Vince v2. Documents 5 phases with prerequisites:

**Phase 0 (blocks everything):** Strategy alignment. Run `build_strategy_analysis.py` → paste report into Claude Web → answer 6 open questions (rot_level, BBW wiring, bot v386 upgrade, trailing stop divergence, BE params, ExitManager status) → apply decisions to code.

**Phase 1 (B1 FourPillarsPlugin):** After Phase 0. Single file `strategies/four_pillars.py` (rewrite). Spec conflict resolved: use v386 (not v383_v2 as BUILD-VINCE-B1-PLUGIN.md states — that spec is outdated). Build script `scripts/build_b1_plugin.py` with 3 smoke tests.

**Phase 2 (B3 Enricher):** After B1. `vince/enricher.py` — per-trade indicator snapshot at entry/MFE/exit bars, diskcache.

**Phase 3 (B4 PnL Reversal Panel):** After B3. Dash page `vince/pages/pnl_reversal.py` — LSG analysis, MFE histogram, TP sweep.

**Phase 4 (B5 Query Engine):** After B3. `vince/query_engine.py` — constellation filter + permutation test.

**Phase 5 (B6 Dash Shell):** After B1-B5. `vince/app.py` + `vince/layout.py` — Dash skill mandatory.

### Decisions recorded
- Phase 0 blocks all other phases
- Use v386 signal file in B1 (overrides B1-PLUGIN.md spec)
- Engine: Backtester385 in B1
- B2 already built (API layer)
- Dash skill mandatory before B6

### State changes
Roadmap document only. No code changed.

### Open items recorded
6 open questions for Claude Web discussion (rot_level, BBW, bot upgrade, trailing divergence, BE params, ExitManager).

### Notes
Documents that B2 (API layer) is already complete. Confirms B1 spec conflict — `BUILD-VINCE-B1-PLUGIN.md` references `compute_signals_v383` but the correct import is v386.

---

## 2026-03-03-ttp-engine-activation-fix.md
**Date:** 2026-03-03
**Type:** Bug fix plan

### What happened
Fix plan for a TTP engine bug: 5 of 6 unit tests fail because the engine jumps from MONITORING → CLOSED on the activation candle, skipping the ACTIVATED state entirely.

Root cause: `evaluate()` calls `_try_activate()` which sets trail level, then falls through to `_evaluate_long`/`_evaluate_short` which immediately checks H/L against the trail — the activation candle's range naturally violates the trail level just set.

Example trace (SHORT):
- Entry=100, ACT=0.5%, DIST=0.2%
- `activation_price = 99.5`, candle H=99.8, L=99.5
- Trail set at 99.5 × 1.002 = 99.699
- `_evaluate_short`: H=99.8 >= trail=99.699 → CLOSED (wrong)

Fix — three changes to `ttp_engine.py`:
1. Restructure `evaluate()`: after activation, do NOT fall through to `_evaluate_long/short`. Instead call `_update_extreme_on_activation()` and return ACTIVATED result immediately.
2. Add `_update_extreme_on_activation()` method: extends extreme/trail if candle overshoots activation price (without checking trail stop).
3. Add `_trail_pct()` and `_extreme_pct()` helper methods.

### Decisions recorded
- Activation candle establishes baseline — trail stop checking starts on NEXT candle
- Activation candle CAN extend extreme beyond activation_price if the candle range goes further

### State changes
Plan document. Single file modified: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ttp_engine.py`.

### Open items recorded
Run: `python -m pytest tests/test_ttp_engine.py -v` — all 6 tests should pass after fix.

### Notes
None.

---

## 2026-03-04-1m-ema-delta-scalp-concept.md
**Date:** 2026-03-04
**Type:** Strategy spec / Concept

### What happened
Concept note for a 1-minute EMA-Delta Scalp trade type — one of 4 identified trade types. Not yet validated with chart examples.

Core idea: measure the delta (distance) between two EMAs (e.g., EMA55 - EMA89) as a leading indicator for crossover prediction. Delta narrows before a crossover → pre-alert signal before actual cross.

Three entry conditions:
1. EMA Delta Threshold: `abs(EMA_short - EMA_long)` narrows below threshold (leading)
2. Stochastic Zone Entry: all 4 stochastics (9/14/40/60) in oversold (<20) or overbought (>80)
3. TDI MA Cross: TDI price line crosses its moving average (RSI=9, Smooth=5, Signal=10, BB=34)

All three conditions must be true simultaneously.

Parameters for Vince to optimize: EMA pair (55/89 default, also 34/50, 72/89), delta threshold (absolute, ATR-normalized, or %-of-price), stoch zone depth (20/80 strict vs 25/75 loose), TDI MA threshold, N stochs required, timeframe.

Normalization recommendation: ATR-normalized delta (delta / ATR) — scale-invariant, adapts to volatility.

Management concept: delta expanding after entry = hold; delta compressing back = tighten trail/exit.

### Decisions recorded
None — concept only, not validated.

### State changes
Concept document only. No code.

### Open items recorded
Requires: chart walkthrough, delta threshold research, management rules confirmation, HTF interaction rules, stoch zone rules for 1m.

### Notes
Explicitly marked "NOT a build spec" and "NOT validated." No code to be written until concept validated with real trade examples.

---

## 2026-03-04-bingx-v1-5-full-audit-upgrade.md
**Date:** 2026-03-04
**Type:** Build plan

### What happened
Comprehensive 4-phase upgrade plan for BingX connector after 12+ hours of live operation revealed multiple bugs. Context: TTP close orders failing (error 109400), Close Market button broken (100001 signature error), equity curve showing all sessions mixed, coin summary date filter disconnected.

**Phase 1 — Diagnostic Scripts (read-only):**
Build script: `build_phase1_diagnostics.py`. Creates 4 scripts:
- `run_error_audit.py` — parse bot log, categorize errors, output markdown table
- `run_variable_web.py` — AST analysis, trace data flow, flag orphaned/dead variables
- `run_ttp_audit.py` — read trades.csv for ttp_state column (expected ABSENT), read state.json for TTP fields, correlate EXIT_UNKNOWN vs TTP fail count
- `run_ticker_collector.py` — public BingX API ticker data, rank 47 config coins by liquidity

**Phase 2 — Bot Core Fixes:**
Build script: `build_phase2_bot_fixes.py`. STOP BOT BEFORE RUNNING.
- P2-A: Remove `"reduceOnly": "true"` from `_place_market_close()` (BUG-1: 109400 error — `positionSide` already scopes in Hedge mode)
- P2-B: Add TTP + BE columns to `_append_trade()` in `state_manager.py` (BUG-9: 6 new CSV columns)
- P2-C: Dynamic SL tightening after TTP activation — new `_tighten_sl_after_ttp()` method; 0.3% sl_trail_pct_post_ttp default; rate-limited (only updates when ≥0.1% improvement)

**Phase 3 — Dashboard v1.5:**
Build script: `build_dashboard_v1_5.py`. Reads v1-4 as base, writes v1-5.
- P3-A: Fix BUG-4 — add `recvWindow='10000'` to `_sign()` (100001 signature error)
- P3-B: Fix BUG-1b — remove `reduceOnly` from CB-6, CB-7, CB-16
- P3-C: Fix BUG-2 — analytics period quick-filter (`session|today|7d|all`), session equity curve
- P3-D: Fix BUG-5 — coin summary date sync with analytics date range
- P3-E: Status bar — separate BOT: LIVE/OFFLINE and EXCHANGE: CONNECTED/ERROR indicators
- P3-F: TTP Stats panel (if TTP columns present in trades.csv)
- P3-G: Trade chart popup (HIGH PRIORITY) — history grid row click → modal with candlestick + stochastics + BBW; klines fetched live from BingX

**Phase 4 — Beta Bot ($5 margin, 20x leverage):**
Build script: `build_phase4_beta_bot.py`. Requires user to confirm beta coin list first.
- New `config_beta.yaml` (leverage=20, margin_usd=5, beta coin list)
- New `main_beta.py` (all data paths prefixed with `beta/`)
- 13 user-specified coins; additional coins from ticker collector research

### Decisions recorded
- `reduceOnly` removal is the correct fix for 109400 in Hedge mode
- Dynamic SL tightening after TTP activation included in Phase 2
- Trade chart popup is HIGH PRIORITY in v1.5
- Beta bot uses separate config and data paths (no overlap with live)
- Phase 4 risk: HIGH — 20x leverage, ~5% adverse move to liquidation

### State changes
Plan document. Multiple build scripts and files to be created across all 4 phases. All relevant build scripts (`build_phase1_diagnostics.py` through `build_phase4_beta_bot.py`) appear in git status as `??`, confirming creation.

### Open items recorded
- USER ACTION REQUIRED: confirm beta coin list before Phase 4 build
- LSG `saw_green` backfill deferred (separate script)
- BUG-8 BE verification deferred
- Trade chart for open positions deferred (history grid only)

### Notes
This plan supersedes and expands on the earlier `2026-03-03-audit-fix-cuda-bingx.md` fix for HIGH #6 (`reduceOnly`). BUG-1 (109400) here is the same as HIGH #6 there. The earlier plan added `reduceOnly` defensively; this plan removes it entirely as the correct fix for Hedge mode.

---

## 2026-03-04-position-management-study.md
**Date:** 2026-03-04
**Type:** Strategy spec / Research

### What happened
Position management study document based on two live trade walkthroughs: PUMPUSDT LONG (5m, Bybit Spot) and PIPPINUSDT SHORT (5m, Bybit Perpetual). Both are trend-hold trade type only.

Documents 6 phases of position management:
1. **HTF Direction**: Three-layer system (4h/1h session bias → 15m MTF Clouds on 5m → 5m entry timing)
2. **Entry Detection**: All 4 stochastics K/D cross (sequential: 9 first, then 14/40/60), BBW spectrum above MA, TDI correct side of MA, SL=2×ATR validated against structure
3. **Gate Check**: Stoch 60 K vs D — determines trade type (trend-hold vs quick rotation)
4. **Trend Hold Management**: TDI 2-candle rule (HARD EXIT), BBW health monitor (trail/tighten/exit), breakeven trigger, AVWAP trail mechanism, Ripster Cloud milestones, TP framework
5. **Add-Ons**: Stoch 9/14 must reach opposite zone while 40/60 hold trend direction
6. **Exit**: 5 confirmed exit triggers

Key resolved questions: HTF-1 (cloud stack transitions determine session bias), HTF-2 (15m MTF = hold duration modulator, not hard binary), ENTRY-1 (sequential confirmation), ENTRY-2 (recent zone check: K below 20/above 80 within last N=10 bars), BBW-1 (flagged for Vince research), TDI-1 (RSI=9, Smooth=5, Signal=10, BB=34).

ATR clarification: ATR does NOT drive trade decisions. It is a thermometer (SL sizing + volatility confirmation only). This contradicts ATR-SL-MOVEMENT-BUILD-GUIDANCE.md which makes ATR central to phase transitions.

### Decisions recorded
- Sequential stochastic confirmation (9 crosses first, enter on last stoch completing K/D cross)
- Recent zone check: K must have been below 20 (long) or above 80 (short) within last 10 bars (flag for Vince optimization)
- 15m MTF clouds = hold duration modulator, not hard binary filter
- TDI 2-candle rule: HARD EXIT, binary
- BBW spectrum above MA = hold; crossing MA = tighten; below MA / dark blue = exit
- AVWAP trail: plain AVWAP (PUMP long) or AVWAP +2sigma (PIPPIN short), tighten to +1sigma when BBW red
- Ripster Cloud milestones are waypoints, not SL triggers; Cloud 4 value at confirmation = FROZEN TP target
- This is a different strategy architecture from v386, not a patch

### State changes
Research/study document only. No code.

### Open items recorded
6 open questions: SL-1 (what if 2 ATR doesn't align with structure?), SL-2 (what counts as "structure"?), GATE-1 (numeric threshold for stoch 60 K/D distance?), BE-1 (are two BE methods interchangeable?), TRAIL-1 (which AVWAP variant to use?), CLOUD-1 (frozen Cloud 4 target longs-only?), TP-1 (cloud target vs % target?).

### Notes
Explicitly states: "This is not a patch on v386. It is a different strategy architecture." ATR role contradicts `ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0`. Document explicitly covers only trend-hold trades — 3 other trade types (quick rotations, 1m scalps, counter-trend) are separate.

---

## 2026-03-04-probability-trade-framework.md
**Date:** 2026-03-04
**Type:** Strategy spec / Concept

### What happened
Theoretical framework document for replacing hard-coded indicator thresholds with learned transition probabilities (Markov) combined with continuous probability estimates (Black-Scholes).

**Markov approaches**:
- Observable Markov Chain: 75 combined states (5 EMA delta × 5 stoch zone × 3 TDI position), 75×75 transition matrix learned from historical data
- Hidden Markov Model: latent regimes (TRENDING/CHOPPY/TRANSITIONING) inferred from observable states using hmmlearn + Baum-Welch/Viterbi

**Black-Scholes applications**:
- Application 1: P(crossover within N bars) from current EMA delta and sigma
- Application 2: P(hit TP before SL) using first-passage-time formula
- Application 3: Expected time to reach Ripster Cloud milestone levels
- Application 4: BBWP-to-BS bridge — BBWP percentile maps to sigma regime, feeding BS formulas

**Three-layer probability architecture**:
1. Hard thresholds (current system) — instant binary filter
2. Markov — "what state comes next?"
3. Black-Scholes — "what's the probability of reaching target?"

Libraries: `hmmlearn` (HMM), `scipy.stats` (BS), `numpy` (transition matrix). RTX 3060 not needed for these (CPU-bound).

### Decisions recorded
None — concept only. Not yet validated.

### State changes
Concept document only. No code.

### Open items recorded
Must benchmark probability framework against hard-threshold baseline before building. Per document: "Start with Layer 1 + Layer 2 only. Add Layer 3 (BS) only if Layer 2 alone doesn't beat baseline."

### Notes
Explicitly marked "NOT a build spec — no code to be written yet." Identifies BS assumptions violated by crypto (non-stationary, fat tails) and mitigations. BBWP-to-BS bridge is described as "the key insight."

---

## 2026-03-04-strategy-scope-why-v386-baseline.md
**Date:** 2026-03-04
**Type:** Strategy analysis / Scoping

### What happened
Complete scoping document reviewing why v386 is the correct baseline and what gaps remain. Source: review of all session logs, version history, strategy docs, and ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0.

Version journey (v3.5 through v3.8.6) — each tried to solve the core LSG problem differently:
- v3.5.1: Cloud 3 trail → bled out
- v3.6: AVWAP SL → bled out
- v3.7: Rebate farming → commission barely viable
- v3.7.1: Fixed phantom trade bug (strategy.close_all)
- v3.8: Cloud 3 filter ON + ATR BE raise → RIVER: +$18,952 (best result)
- v3.8.3: D-signal + scale-out → drag
- v3.8.4: Optional per-coin ATR TP
- v3.8.6: Stage 2 conviction filter, C disabled → ~40 trades/day → **LIVE**

What v386 has (correct): entry grades A/B/C structure, stochastic periods, cloud periods, ATR calc, Stage 2 filter.
What v386 is missing: 3-phase SL/TP system (spec exists, never built correctly), Cloud 2 hard close, Cloud 4 computed.

Why v391 failed: built from spec doc without user confirming rules match actual trading. Spec may be incomplete vs actual chart behavior.

### Decisions recorded
- v386 signal side is correct — keep as-is
- Position management has NEVER been correctly implemented in any version
- v391 build requires user rule confirmation on all phase details before next attempt
- Next build sequence: user confirms phase rules → confirm which v391 files to keep → confirm ADD signal logic → build against confirmed rules only

### State changes
Scoping document only. No code.

### Open items recorded
5 unverified spec details: Phase 1 SL anchor (candle_low/high correct?), Phase 2 amounts (SL+TP shift by 1×ATR?), Phase 3 exit (continuous trail at highest_high/lowest_low − 1×ATR?), hard close scope (any Cloud 2 flip, or only after Phase 1?), ADD midline (48/52 threshold?).

### Notes
First document to explicitly name that spec ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0 has "never been correctly implemented in any version." v391 code files exist (clouds_v391.py, four_pillars_v391.py, position_v391.py, backtester_v391.py, build_strategy_v391.py) but are labeled "rules unverified."

---

## 2026-03-04-strategy-v391-rebuild.md
**Date:** 2026-03-04
**Type:** Build plan

### What happened
Detailed build plan for v3.9.1 Four Pillars signal quality rebuild. Goal: faithful implementation of ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0.

Three compounding problems in v3.9.0:
1. 3-phase SL/TP movement system not implemented (position_v384 uses AVWAP center as SL trail)
2. Cloud 2 hard close missing entirely
3. Cloud 4 (EMA 72/89) not computed anywhere — Phase 3 cannot activate

**Part 1 — clouds_v391.py**: Add `ema_72`/`ema_89` (Cloud 4), cloud state booleans (`cloud2_bull/bear`, `cloud3_bull/bear`, `cloud4_bull/bear`), cross detection columns (True only on bar of cross), and `phase3_active_long/short` (Cloud 3 AND Cloud 4 in sync).

**Part 2 — four_pillars_v391.py**: Nearly identical to v390. Call `compute_clouds_v391()` instead. State machine stays at v390.

**Part 3 — position_v391.py (THE CRITICAL REBUILD)**: Replace AVWAP-trail-as-SL with 3-phase system:
- Phase 0: SL=entry±2×ATR, TP=entry±4×ATR
- Phase 1 (Cloud 2 cross in trade direction): SL anchored to candle_low/high − 1×ATR (favorable guard), TP + 1×ATR
- Phase 2 (Cloud 3 fresh cross after entry): SL + 1×ATR, TP + 1×ATR
- Phase 3 (Cloud 3 AND Cloud 4 sync): TP removed, continuous ATR trail from highest_high/lowest_low
- Hard close: Cloud 2 flips AGAINST trade — highest priority, overrides all

AVWAP correct role: ADD entry trigger + scale-out trigger only (NOT SL trail).

ADD signals: stochastic-based (stoch9 exits overbought/oversold zone while 40+60 hold trend).

**Part 4 — backtester_v391.py**: Import position_v391, pass cloud cross columns to position slot per bar, hard close checked before SL/TP, expanded `update_bar()` signature, `sl_phase` field in trade record.

Build script: `scripts/build_strategy_v391.py` — 4 files, py_compile after each.

### Decisions recorded
- State machine stays at v390 (A/B/reentry logic correct)
- AVWAP removed from SL trail role
- AVWAP kept for ADD trigger and scale-out
- Phase 1 SL: anchor to candle_low/high (not shift by ATR)
- Phase 2: both SL and TP shift by +1×ATR
- Phase 3: TP removed, continuous ATR trail

### State changes
Plan document. Files `engine/position_v391.py`, `engine/backtester_v391.py`, `signals/four_pillars_v391.py`, `signals/clouds_v391.py`, `scripts/build_strategy_v391.py` all appear in git status as `??`, confirming creation.

### Open items recorded
Verification: smoke test on one symbol, check sl_phase values > 0, check CLOUD2_CLOSE exits, check Phase 3 trail behavior, compare signal count v390 vs v391.

### Notes
The preceding scoping doc (`2026-03-04-strategy-scope-why-v386-baseline.md`) notes that user said the spec may be incomplete vs actual trading. This plan was built from the spec. The session log `2026-03-04-strategy-v391-failed-attempt.md` (listed as `??` in git status) suggests this attempt was also problematic.

---

## 2026-03-05-bingx-timestamp-sync-fix.md
**Date:** 2026-03-05
**Type:** Build plan

### What happened
Plan to fix BingX 109400 "timestamp is invalid" error. Root cause: zero server time synchronization in the codebase. Both bot (`bingx_auth.py` line 43) and dashboard (line 193) use raw `time.time() * 1000`. BingX requires timestamp within 5000ms of server clock. User reportedly lost 17% due to this — position reconciliation, SL moves, TTP closes, and balance queries all failed silently.

Solution: new `time_sync.py` module with `TimeSync` class:
- `sync()` — fetches server time, calculates offset with RTT midpoint compensation
- `now_ms()` — returns `int(time.time() * 1000) + offset`
- `start_periodic()` — daemon Timer thread, re-syncs every 30s
- `force_resync()` — immediate sync on 109400 error
- Module-level singleton factory `get_time_sync(base_url)`
- Supports live and demo base URLs

Changes to 3 files:
- `bingx_auth.py`: replace `int(time.time() * 1000)` with `synced_timestamp_ms()` — all bot API calls flow through `build_signed_request()`
- `main.py`: init singleton at startup
- `bingx-live-dashboard-v1-4.py`: init singleton at startup, replace line 193

109400 retry logic added to `position_monitor.py`, `executor.py`, and dashboard.

Build script: `scripts/build_time_sync.py` — creates `time_sync.py`, backs up 5 files, writes updated versions, py_compile each.

Failure mode: if server-time endpoint unreachable, `_offset_ms` stays 0 = same as current behavior, no regression.

### Decisions recorded
- New `time_sync.py` module (not patching existing files directly)
- Singleton pattern per base URL
- 30s periodic resync
- 109400 error → force_resync → retry once
- Backup all modified files before writing

### State changes
Plan document. `time_sync.py` and `scripts/build_time_sync.py` both appear in git status as `??`, confirming creation.

### Open items recorded
Verification: restart bot, check log for `TimeSync: offset=+Xms`, watch for 30s sync messages, confirm 109400 errors stop.

### Notes
None.

---

## 2026-03-05-bingx-v1-5-runtime-fix.md
**Date:** 2026-03-05
**Type:** Bug fix plan

### What happened
Plan to fix runtime errors found on first launch of dashboard v1.5 (built 2026-03-04). Dashboard passed `py_compile` but revealed two code errors and one API error on first run.

**Error 1**: `KeyError: "Callback function not found for output 'store-bot-status.data'."` — `dcc.Store(id='store-bot-status', data=[])` is the only store not using `storage_type='memory'`. The `data=[]` initial value conflicts with CB-S1 callback registration.

**Error 2**: `IndexError: list index out of range` in `_prepare_grouping` — likely cascading from Error 1 (Dash's flat_data array misalignment). Expected to resolve after fixing Error 1.

**Error 3**: `BingX error 100001: Signature verification failed` — Not a code bug. API credentials may be expired/wrong. User action required (verify `.env` keys).

Fix: single line change in `bingx-live-dashboard-v1-5.py` line 1141:
```
OLD: dcc.Store(id='store-bot-status', data=[]),
NEW: dcc.Store(id='store-bot-status', storage_type='memory'),
```

Build script: `scripts/build_dashboard_v1_5_patch_runtime.py` — patches in-place, py_compile validates.

### Decisions recorded
- Fix: align `store-bot-status` with all other stores (use `storage_type='memory'`, remove `data=[]`)
- Error 3 (100001) is user action — verify `.env` keys
- Separate from previously planned tasks (`be_act` settings save bug, dashboard_v395 preset)

### State changes
Plan document. Build script `scripts/build_dashboard_v1_5_patch_runtime.py` appears in git status as `??`, confirming creation.

### Open items recorded
If IndexError persists after Patch 1: inspect CB-3, CB-9, CB-10 for mismatched initial data.

### Notes
Plan notes that the v2 continuation prompt (`2026-03-05-next-chat-prompt-v2.md`) listed only the `be_act` settings save bug, but these runtime errors are new findings from first launch. Confirms py_compile passes but does not catch Dash-specific callback registration errors.


# Batch 16 Findings: Dated Plans (2026-03-05 group)

Processed: 10 files
Date range: 2026-03-05 to 2026-03-06

---

## 2026-03-05-cards-on-the-table.md
**Date:** 2026-03-05
**Type:** Strategy spec / Analysis

### What happened
A structured "cards on the table" document was created to lay out the exact gap between what the live BingX bot knows vs what the user's actual trading system requires. Written in 10 cards, each covering a specific facet of the mismatch. Purpose: no interpretation, just facts, to inform decisions about what to build next.

Key cards:
- **Card 1**: B trade = stoch 9 cross + 2 of 3 slower stochs (14/40/60) below zone + price above Cloud 3. Missing: 3rd stoch never confirmed.
- **Card 2**: A trade = all 3 stochs confirmed + Stage 2 rotation (stoch 40+60 rotated through 20, price at Cloud 3 within last 5 bars).
- **Card 3**: Bot has zero concept of HTF session bias (4h/1h cloud transitions), 15m MTF execution filter, sequential K/D crosses, BBW spectrum vs MA, TDI price vs MA, structure validation for SL placement.
- **Card 4**: PIPPIN LONG (2026-02-28 09:05:35, LONG-B, entry=0.673800, sl=0.654449) legitimately passed bot's rules. Bot saw: stoch 9 trigger, 2/3 slower stochs confirmed, price above Cloud 3, allow_b=true. Bot did NOT see: HTF perspective, 15m MTF clouds, sequential K/D alignment, BBW, TDI, or "nowhere's land" price context.
- **Card 5**: Bot runs v3.8.4 plugin (config.yaml `plugin: four_pillars_v384`). v3.8.4 Stage 2 defaults to False; config has `require_stage2: true` but possible loading bug means it may not propagate. v3.8.6 has Stage 2 ON by default.
- **Card 6**: User's "perspective" is a 3-layer system: Layer 1 = 4h/1h HTF session bias from sequential cloud flips (binary: long day or short day). Layer 2 = 15m MTF clouds modulating hold duration. Layer 3 = 5m entry timing. Bot has no Layer 1 or 2.
- **Card 7**: Cloud 3 gate (`price_pos >= 0`, i.e., price above EMA 34/50) is too crude to distinguish strong directional move from sideways drift — "nowhere's land."
- **Card 8**: Two coexisting trading modes — volume generation (B-trades, higher frequency, rebate income) and top-tier waiting (A-grade trend-hold trades, full perspective alignment).
- **Card 9**: 6 open questions still block trend-hold implementation: SL-1 (2 ATR vs structure), SL-2 (what counts as structure), GATE-1 (stoch 60 K-D threshold), BE-1 (BE method), TRAIL-1 (AVWAP variant), CLOUD-1/TP-1 (frozen Cloud 4 vs % target).
- **Card 10**: Entry-side improvements that do NOT require answering those 6 questions: (1) perspective layer (HTF direction check), (2) B-trade tightening (fix Stage 2 config bug, or upgrade to v386, or add BBW/TDI gates), (3) coin monitor pre-filter, (4) sequential K/D check.

### Decisions recorded
- The 6 open questions from the position management study block trend-hold builds.
- Entry-side improvements (perspective layer, B-trade tightening, coin monitor, sequential K/D) can proceed without resolving those 6 questions.
- PIPPIN LONG is acknowledged as a legitimate bot-rule pass, not a bug — bot's rules are incomplete.

### State changes
- Document created as a factual reference/diagnostic. No code changes.

### Open items recorded
- 6 open questions listed (SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1/TP-1)
- 4 entry-side improvements identified as buildable without resolving those questions

### Notes
- References `fizzy-humming-crab.md` as source for position management study content.
- References `PROJECTS\bingx-connector\logs\2026-02-27-bot.log` line 10667 as source of PIPPIN LONG log entry.
- The claim "v384 Stage 2 defaults to False, possible config loading bug" is stated but not verified by reading the plugin code.

---

## 2026-03-05-native-trailing-switch.md
**Date:** 2026-03-05
**Type:** Planning / Build spec

### What happened
A detailed build plan for switching the TTP (trailing take-profit) engine to use BingX's native `TRAILING_STOP_MARKET` order type instead of the custom 5m-candle-evaluated engine. The plan was triggered by the custom engine's ~6-minute worst-case delay vs exchange tick-level reaction.

Key design decisions:
- New config key `ttp_mode: native` vs `ttp_mode: engine` (default).
- Reuses existing `ttp_act=0.008` and `ttp_dist=0.003` parameters for both modes.
- 6 files modified: `config.yaml`, `executor.py`, `signal_engine.py`, `position_monitor.py`, `ws_listener.py`, `state_manager.py`.
- ~65 lines changed total.

Critical bugs identified and planned for fix:
1. `_cancel_open_sl_orders` in `position_monitor.py`: `"STOP" in "TRAILING_STOP_MARKET"` evaluates True, so breakeven raise would cancel native trailing order. Fix: add exclusion for `otype != "TRAILING_STOP_MARKET"`.
2. `_detect_exit`: When trailing fires, SL+TP remain pending, trailing gone from open orders — returns `(None, None)`. Fix: detect `trailing_order_id` missing from open orders = trailing fired.
3. `_fetch_filled_exit`: Add explicit `TRAILING_STOP_MARKET` check before generic `"STOP" in otype` check.
4. `ws_listener.py _parse_fill_event`: Add `TRAILING_STOP_MARKET` detection before `"STOP" in order_type`.

Three-stage interaction table documented: BE raise still active in native mode (safety net between +0.4% and +0.8%), TTP engine evaluation skipped (exchange handles it), SL tighten post-TTP skipped.

Edge cases covered: BE cancelling trailing (fixed), exit detection when trailing fires (fixed), native trailing rejected by exchange (logged, SL safety net remains), bot restart (trailing lives on exchange, state.json holds trailing_order_id), switchback to engine mode (zero regressions).

Delivery: build script at `PROJECTS\bingx-connector\scripts\build_native_trailing.py`, writes all 6 modified files, py_compile each.

### Decisions recorded
- Native trailing is config-toggled, not a replacement — `ttp_mode: engine` fully reverts to current behavior.
- `ttp_engine.py` is untouched; not invoked in native mode.
- `check_breakeven()` remains active in native mode as a safety net.
- Dashboard deferred.

### State changes
- Plan document created. Build script (`build_native_trailing.py`) planned.

### Open items recorded
- Verification steps: py_compile all 6 files, `test_three_stage_logic.py` passes unchanged, manual demo test with `ttp_mode: native` + `demo_mode: true`, switchback test.

### Notes
- CODE VERIFICATION: `build_native_trailing.py` EXISTS on disk at `PROJECTS\bingx-connector\scripts\build_native_trailing.py` — plan was executed.
- Previous native trailing attempt failed (activation was ATR-based/too far, callback was 2%/too wide). This plan fixes those by using percentage-based params matching working TTP config.

---

## 2026-03-05-next-chat-prompt-audit.md
**Date:** 2026-03-05
**Type:** Audit

### What happened
An audit of `2026-03-05-next-chat-prompt.md` (the original v1 prompt) before using it in a new session. Two errors and three gaps were identified.

**ERROR 1 (will cause build failure):** Prompt says `compute_signals()` in `signals/four_pillars.py` already accepts `require_stage2` and `rot_level` and directs wiring into the `sig_params` dict. Reality: `dashboard_v394.py` calls `compute_signals_v383()` from `signals/four_pillars_v383_v2.py` (line 57), which does NOT accept those params. Fix options: (A) switch dashboard import to non-versioned function, or (B) add params to v383 versions. Option B (safer, no import change).

**ERROR 2 (already done):** Task 2 in prompt listed 5 bugs still pending for v1.5 dashboard. Reality: `bingx-live-dashboard-v1-5.py` EXISTS (133K, built 2026-03-04) with patches P3-A through P3-H already applied. BUG-4 (recvWindow), BUG-1b (reduceOnly), BUG-2 (analytics period), BUG-5 (coin summary date sync) all fixed. Only truly unfixed: `be_act` not in dashboard settings save callback.

**GAP 1:** Prompt did not warn that bot is collecting 48h live data and must NOT be restarted.

**GAP 2:** Lines 59-60 (daily PnL snapshot, RENDER positions) are stale point-in-time data, not live.

**GAP 3:** If Task 1 switches imports, the GPU sweep and portfolio sweep paths must also be considered.

Verified correct: Three-stage TTP params (be_act=0.004, ttp_act=0.008, ttp_dist=0.003), orderId extraction fix in 3 places, unrealized PnL in Telegram, max_positions=25, 25/25 test pass, key file paths.

### Decisions recorded
- Fix 2 errors and 3 gaps before using the prompt in a next session.
- Task 1 fix: Add `require_stage2` and `rot_level` to the v383 pipeline (Option B), not switch imports.
- Task 2 fix: State v1.5 already built, only `be_act` save callback remaining.

### State changes
- Audit document created. No code changes.

### Open items recorded
- ~10 minutes of prompt edits needed to fix 2 errors + 3 gaps.

### Notes
- This document is the audit that led to the creation of `2026-03-05-next-chat-prompt-v2.md`.

---

## 2026-03-05-next-chat-prompt-position-study.md
**Date:** 2026-03-05
**Type:** Planning / Continuation prompt

### What happened
A continuation prompt for resuming the position management study across a new session. The study ran across 3 sessions (2026-03-04 to 2026-03-05). 7 of 13 open questions were resolved; 6 remain. Two new concept documents were also created (1m delta scalp, probability framework).

Key state captured:
- The authoritative study document is `C:\Users\User\.claude\plans\fizzy-humming-crab.md`.
- 6 remaining questions: SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1/TP-1.
- User indicated GATE-1 on PUMP should be next.
- 7 already-confirmed items listed (HTF-1, HTF-2, ENTRY-1, ENTRY-2, BBW-1, TDI-1, and others) to prevent re-asking.
- v391 strategy files exist on disk but have WRONG trading logic — must not be tested or deployed.

Violation note included: A previous session deleted `2026-03-04-markov-trade-state-research.md` without asking, violating the NEVER OVERWRITE/DELETE FILES rule. Content was preserved in a replacement file. Logged in session log and TOPIC-critical-lessons.md.

### Decisions recorded
- This is a RESEARCH session — no code to be written.
- Update `fizzy-humming-crab.md` as questions are resolved, keep vault copy synced at `06-CLAUDE-LOGS\plans\2026-03-04-position-management-study.md`.
- When all 6 resolved, the study document becomes complete spec for trend-hold trade type.

### State changes
- Prompt document created. No code changes.

### Open items recorded
- 6 remaining position management questions to resolve (starting with GATE-1 on PUMP chart).

### Notes
- Explicitly flags prior file-deletion violation as a trust-breaking event.

---

## 2026-03-05-next-chat-prompt-v2.md
**Date:** 2026-03-05
**Type:** Planning / Continuation prompt (audited version)

### What happened
The audited v2 version of the next-chat continuation prompt, fixing the 2 errors and 3 gaps identified in `2026-03-05-next-chat-prompt-audit.md`.

Key fixes applied vs v1:
1. Added explicit bot-running constraint at top: "DO NOT modify or restart bot core files: main.py, position_monitor.py, signal_engine.py, state_manager.py, ws_listener.py, config.yaml."
2. Task 1 (dashboard v395) corrected: Explicitly states to add `require_stage2` and `rot_level` to the v383 pipeline (state_machine_v383.py and four_pillars_v383_v2.py), NOT switch imports. References where to mirror from (signals/four_pillars.py lines 60-61, signals/state_machine.py).
3. Task 2 (live dashboard v1.5) corrected: States v1.5 BUILT with patches P3-A through P3-H already applied. Only remaining issue: `be_act` not in settings save callback. Scope narrowed to one missing input field + save wire.
4. Stale snapshot data (daily PnL, RENDER positions) replaced with instruction to check current state in logs/.

Prompt references session log `2026-03-05-bingx-bot-session.md` and plan `sparkling-doodling-hare.md`.

Tasks in v2:
- **Task 1**: `dashboard_v395.py` — add `require_stage2` checkbox + `rot_level` slider + "Load v384 Live Preset" button. Patch v383 pipeline to accept these params. Build script: `build_dashboard_v395.py`.
- **Task 2**: Live dashboard v1.5 patch — add `be_act` numeric input to Strategy Parameters tab + wire into settings save callback. Build script: `build_dashboard_v1_5_patch1.py`.

### Decisions recorded
- Keep `compute_signals_v383()` import in dashboard; patch the v383 files to accept new params.
- Bot hands-off: 6 core files explicitly off-limits.
- v1.5 patch scope: be_act only, nothing else.

### State changes
- Prompt document created. No code changes yet.

### Open items recorded
- Task 1: `dashboard_v395.py` build.
- Task 2: `bingx-live-dashboard-v1-5.py` be_act patch.

### Notes
- This is the cleaned-up version of the original prompt. The v2-prompt-audit.md (separate file) confirmed this version is ready to use.

---

## 2026-03-05-next-chat-prompt.md
**Date:** 2026-03-05
**Type:** Planning / Continuation prompt (v1 — pre-audit)

### What happened
The original (v1) next-chat continuation prompt, written before the audit identified 2 errors and 3 gaps. Documents the completed work from the prior session and the next tasks.

Completed last session:
- Three-stage position management: be_act=0.004, ttp_act=0.008, ttp_dist=0.003
- orderId extraction fix in 3 places in position_monitor.py
- Unrealized PnL added to Telegram daily summary and hourly warning
- 25/25 test pass on three-stage logic
- max_positions raised to 25

Tasks (v1 — known to have errors per audit):
- **Task 1**: `dashboard_v395.py` — add `require_stage2`, `rot_level`, "Load v384 Live Preset" button; wire into `sig_params` passed to `compute_signals()`. ERROR: dashboard actually calls `compute_signals_v383()`, not `compute_signals()`.
- **Task 2**: `dashboard_v1-5.py` — listed 5 bugs to fix. ERROR: v1.5 already exists with P3-A through P3-H applied; 4 of 5 bugs already fixed.

Bot status snapshot included: Log at `2026-03-04-bot.log`, daily PnL as of 14:52 = -$1.12, RENDER-USDT LONG+SHORT still open with ttp_state=CLOSED needing manual close.

### Decisions recorded
- None explicitly. This was a prompt draft.

### State changes
- Prompt document created. Superseded by v2.

### Open items recorded
- Same as v2, but with inaccurate scope.

### Notes
- This is the ORIGINAL version. The audit file (`next-chat-prompt-audit.md`) and v2 file (`next-chat-prompt-v2.md`) supersede it.
- Bot status data (PnL -$1.12, RENDER positions) is a point-in-time snapshot from ~14:52 on 2026-03-05.

---

## 2026-03-05-research-execution-plan.md
**Date:** 2026-03-05
**Type:** Planning / Build spec

### What happened
A plan to build an automated research orchestrator script (`run_log_research.py`) to systematically read all vault logs and produce structured findings. The vault at time of writing contained ~201 session logs + ~149 plan files (~87,000 total lines) spanning Jan 2025 to March 2026.

Architecture:
- One Python script discovers all .md files in `06-CLAUDE-LOGS/` and `06-CLAUDE-LOGS/plans/`.
- Splits into sized batches (~25 files per batch for normal files; mega-files >5000 lines get dedicated batches).
- For each batch, constructs a prompt and runs `claude -p` via subprocess with flags: `--allowedTools "Read,Edit,Write,Glob,Grep"`, `--max-turns 200`, `--model sonnet`.
- Waits for completion, logs result, moves to next batch.
- Final batch (synthesis) uses Opus model.

File ordering:
1. Ordered files from RESEARCH-TASK-PROMPT.md (162 files) in exact order
2. Unlisted files found on disk
3. Dated plan files
4. Auto-generated plan files
5. Synthesis as final batch

Output files:
- `scripts/run_log_research.py` (orchestrator)
- `06-CLAUDE-LOGS/research-batches/FINDINGS-*.md` (per-batch, at runtime)
- `06-CLAUDE-LOGS/research-batches/SYNTHESIS.md` (at runtime)
- `06-CLAUDE-LOGS/RESEARCH-PROGRESS.md` (checkbox tracker)
- `06-CLAUDE-LOGS/RESEARCH-FINDINGS.md` (final merged output)
- `06-CLAUDE-LOGS/logs/YYYY-MM-DD-research-orchestrator.log` (runtime log)

Overnight execution design:
- Zero prompts via `--allowedTools` pre-approval.
- Auto-retry: 1 retry per failed batch (30-second pause).
- Resilient: each batch writes its own file; failures don't stop other batches.
- Resumable: re-run skips completed batches.
- 2-hour timeout per batch.

Estimated runtime: 4-7.5 hours for ~16 file batches + 20-40 min synthesis = ~5-8 hours unattended.

### Decisions recorded
- Sonnet model for file batches, Opus for synthesis only.
- ~25 files per batch target.
- All 162 ordered files from RESEARCH-TASK-PROMPT.md processed first in exact order.

### State changes
- Plan document created.
- Build script `run_log_research.py` planned.

### Open items recorded
- Verification steps: all checkboxes in RESEARCH-PROGRESS.md marked [x], RESEARCH-FINDINGS.md has one section per file + synthesis, synthesis answers all 8 questions from research prompt, orchestrator log shows exit code 0 for all batches.

### Notes
- CODE VERIFICATION: `run_log_research.py` EXISTS on disk at `PROJECTS\four-pillars-backtester\scripts\run_log_research.py` — plan was executed.
- This plan is what created the current research task (the batch system being used to process this very file).

---

## 2026-03-05-trade-analyzer-v2.md
**Date:** 2026-03-05
**Type:** Planning / Build spec

### What happened
A detailed build plan for `run_trade_analysis_v2.py`, an enhanced trade analyzer for the BingX bot. Context: bot had been running ~1 day (2026-03-04 17:52 to 2026-03-05 13:24+), 49 trades at $50 notional. Existing `run_trade_analysis.py` had several limitations (no column padding, sparse output, missing analysis dimensions, hardcoded date filter).

One build script: `build_trade_analyzer_v2.py` creates `run_trade_analysis_v2.py`.

CLI flags: `--from YYYY-MM-DD`, `--to YYYY-MM-DD`, `--days N`, `--no-api`.

Output formats: terminal (fixed-width padded), markdown (`logs/trade_analysis_v2_YYYY-MM-DD.md`), CSV (`logs/trade_analysis_v2_YYYY-MM-DD.csv`).

10 analysis sections:
1. Summary Stats (trades, wins, losses, WR%, net PnL, profit factor, LSG count)
2. Equity Curve (ASCII mini-chart terminal; data table markdown)
3. Symbol Leaderboard (sorted by net PnL)
4. Direction Breakdown (LONG vs SHORT: WR%, net PnL, avg MFE/MAE)
5. Grade Breakdown (A/B/C: WR%, net PnL, avg MFE, LSG%)
6. Exit Reason Breakdown (SL_HIT, TTP_EXIT, etc.)
7. Hold Time Analysis (avg, shortest, longest; winners vs losers)
8. TTP Performance (if TTP trades exist)
9. BE Raise Effectiveness (BE vs non-BE trades)
10. Per-Trade Detail Table (padded columns)

Critical hazards documented:
- **CRITICAL**: CSV schema mismatch — header has 12 columns, rows 232+ have 18 values (6 extra TTP/BE fields added without header update). Fix: use `pd.read_csv` with all 18 column names defined, letting older rows have NaN for last 6.
- **HIGH**: F-string escape trap (build script rule — never use escaped quotes in f-strings inside build scripts).
- **HIGH**: Division by zero guards for all ratio computations.
- **MEDIUM**: API failure handling (empty list for delisted symbols, 15s timeout, 0.3s rate limit).
- **MEDIUM**: Float/string parsing edge cases.
- **MEDIUM**: Hold time edge cases (`entry_time` missing on old trades).
- **LOW**: Timestamp format (ISO 8601 with Z replacement).

6 tests planned: py_compile, dry run `--no-api`, small API run `--days 1`, full run (49 trades ~2 min), empty date range, output validation checklist.

Debugging aids built into script: `--verbose` flag, error counter, progress indicator, timestamped logging, API response logging.

### Decisions recorded
- Reuse `sign_and_build()`, `fetch_klines()`, `compute_mfe_mae()`, `to_ms()` from existing `run_trade_analysis.py`.
- Commission rate: 0.0008 (0.08% taker per side).
- No files modified; only new files created.

### State changes
- Plan document created.

### Open items recorded
- Build script to be run; then 5 tests to execute.

### Notes
- CODE VERIFICATION: `build_trade_analyzer_v2.py` EXISTS at `PROJECTS\bingx-connector\scripts\build_trade_analyzer_v2.py` — plan was executed.
- CODE VERIFICATION: `run_trade_analysis_v2.py` EXISTS at `PROJECTS\bingx-connector\scripts\run_trade_analysis_v2.py` — output file also confirmed on disk.

---

## 2026-03-05-v2-prompt-audit.md
**Date:** 2026-03-05
**Type:** Audit

### What happened
A brief audit of `2026-03-05-next-chat-prompt-v2.md` (the corrected prompt) after the errors were fixed. Verdict: clean scope, ready to use.

Audit findings:
- Task 1 (dashboard v395): Two new sidebar controls + preset button + v383 pipeline patch. Mirror job from existing v386 code. Blast radius limited to backtester dashboard; bot unaffected.
- Task 2 (live dashboard v1.5 patch): One missing `be_act` input field + save callback wire. Trivial scope.
- Constraint (bot hands-off): Six files explicitly off-limits. Correct — bot uses separate v384 plugin, not the v383 pipeline being patched.
- Explicitly notes: prompt does NOT address Cards 3/6/7/10 from "cards on the table" analysis. Those are future work.

No changes requested.

### Decisions recorded
- v2 prompt is ready for next session without further changes.
- Cards 3/6/7/10 (HTF perspective, "nowhere's land", volume generation modes, entry improvements) are future work, not in scope for next session.

### State changes
- Audit document created. No code changes.

### Open items recorded
- None. Prompt is ready.

### Notes
- This is a companion to `2026-03-05-next-chat-prompt-audit.md` (which audited v1). This document audits v2 and gives the green light.

---

## 2026-03-06-git-push-bot-server-prep.md
**Date:** 2026-03-06
**Type:** Planning / Operations prep

### What happened
A plan for committing and pushing all work from 2026-03-03 through 2026-03-05 to the vault repo (GitHub: S23Web3/ni9htw4lker). The bot was to be pulled and run on the VPS the following day (VPS already configured with .env and environment).

5-step plan:
1. `git add -A` in vault root. .gitignore confirmed to exclude: `.env`, `data/`, `logs/`, `state.json`, `bot.pid`, `__pycache__/`, `.obsidian/`, ML binaries. All files verified secrets-free (config.yaml has no API keys; bingx_auth.py reads from env vars).
2. Verify critical bot files are staged — list of 12 specific files: main.py, bingx_auth.py, executor.py, position_monitor.py, signal_engine.py, state_manager.py, ws_listener.py, config.yaml (all modified), plus NEW files: time_sync.py (explicitly flagged as CRITICAL for 109400 fix), main_beta.py, config_beta.yaml, bingx-live-dashboard-v1-5.py.
3. Commit message specified: `"Vault update: BingX v1.5 (time sync, TTP, config tuning), backtester v391, session logs 2026-03-03 to 2026-03-05"`.
4. `git push origin main`.
5. Post-push: `git log --oneline -3`, `git status` clean. VPS instructions: `git pull origin main` then `python main.py`.

Scope: ~20 modified tracked files, 70+ new untracked files (session logs, plans, build scripts, new modules), 0 files with secrets.

### Decisions recorded
- Commit message pre-specified.
- .gitignore exclusion list verified correct.
- VPS deployment sequence: `git pull origin main` then `python main.py`.
- time_sync.py explicitly flagged as CRITICAL for the 109400 timestamp fix.
- main_beta.py and config_beta.yaml included as new files (beta bot configuration created alongside main bot).

### State changes
- Plan document created 2026-03-06.
- Based on git status (observed in conversation context), many files listed are staged (A/M status) — push was planned for execution.

### Open items recorded
- Actual git push execution (plan only at document creation time).
- VPS: `git pull origin main` + verify `time_sync.py` exists in `PROJECTS/bingx-connector/`.

### Notes
- time_sync.py cited as critical for "109400 fix" — refers to BingX API error code for timestamp mismatch, resolved by adding time synchronization between bot clock and exchange clock.
- Commit covers 3 days of sessions (2026-03-03 through 2026-03-05).
- main_beta.py and config_beta.yaml indicate a parallel beta bot configuration was created during this period.


# Batch 17 Findings — Auto-Generated Plans (Part 1)

**Files processed:** 20
**Date processed:** 2026-03-06

---

## async-watching-balloon.md

**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to finalize the Vince v2 concept and build Vince as a unified Dash application. Establishes architectural philosophy: Vince is the app, dashboard serves Vince (not vice versa). Existing Streamlit dashboard (scripts/dashboard_v392.py, 2500 lines, 5 tabs) to be replaced. Documents coherence fixes already applied to the concept doc on 2026-02-27. Lists what still needs to be added (GUI section + architecture skeleton) before the concept doc can be locked as APPROVED FOR BUILD.

Specifies 8-panel layout for the Dash app (Coin Scorecard, PnL Reversal Analysis, Constellation Query, Exit State Analysis, Trade Browser, Settings Optimizer, Validation, Session History). Build order B1–B10 defined. Full file structure with vince/ directory detailed. Existing code reuse table provided (backtester_v384, signals/four_pillars_v383_v2, etc.).

### Decisions recorded
- Framework: Plotly Dash
- Architecture: Vince is the app, dashboard serves Vince
- Agent (RL/LLM): future iteration — API skeleton built now
- Scope: core analysis engine + Dash GUI first, RL/LLM/agent = later phases
- Panel 2 (PnL Reversal Analysis) designated highest build priority
- B1 through B10 build order locked

### State changes
- Concept doc coherence fixes applied (filename, symbol in trade_schema, RL state vector, list type annotations)
- Two sections still needed before doc can be approved: GUI section + architecture skeleton
- No Python built yet — plan only

### Open items recorded
- Add GUI section to VINCE-V2-CONCEPT-v2.md
- Add architecture skeleton to VINCE-V2-CONCEPT-v2.md
- Change concept doc status to APPROVED FOR BUILD after above

### Notes
None.

---

## atomic-crunching-sundae.md

**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to update the Vince v2 concept doc with 7 ML findings from 202 YT transcript analysis session (output: `06-CLAUDE-LOGS/plans/2026-02-27-yt-channel-ml-findings-for-vince.md`). Also begins P1.7: formal plugin interface spec (first concrete Vince build artifact).

10 specific edits planned to VINCE-V2-CONCEPT-v2.md covering: elevating Panel 2 as highest priority, adding RL Exit Policy Optimizer as new component, expanding Mode 2 with XGBoost feature importance + unsupervised clustering + bootstrap validation, adding walk-forward methodology to Mode 3, random dataset sampling strategy, expanded RL action space (4 actions: HOLD/EXIT/RAISE_SL/SET_BE), intra-candle context, survivorship bias note, reflexivity caution, new open question on RL training.

Two deliverables for P1.7:
1. `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` (prose spec for StrategyPlugin ABC)
2. `strategies/base_v2.py` (Python ABC stub)

Explicit instruction: do NOT overwrite `strategies/base.py` (from rejected v1 architecture).

### Decisions recorded
- Approval status of concept doc unchanged (user still researching)
- P1.7 backlog status stays WAITING until concept approved
- `strategies/base.py` kept as archive — new file is `strategies/base_v2.py`
- Enricher normalizes MFE to ATR units before handing to B4 (not B4's responsibility)

### State changes
- Concept doc targeted for 10 edits
- Plugin interface spec to be created new
- `strategies/base_v2.py` to be created new
- VINCE-PLUGIN-INTERFACE-SPEC-v1.md added to docs

### Open items recorded
- Concept doc still not APPROVED FOR BUILD (user researching)
- P1.7 waiting on concept doc approval
- RL Exit Policy Optimizer training methodology needs separate scoping session

### Notes
Edit 3 adds RL Exit Policy Optimizer section with full architecture. Edit 10 expands RL action space to 4 actions with intra-candle state. These are significant architectural additions to the concept doc.

---

## bright-prancing-koala.md

**Date:** 2026-03-03
**Type:** Planning / Audit

### What happened
Audit of handover spec for CUDA dashboard v3.9.4 build, followed by corrected build plan. Identified 4 issues in the original spec:

- ISSUE 1 (CRITICAL): Spec claims GPU sweep uses `Backtester390` but actual dashboard v3.9.2 imports `Backtester384` + `compute_signals_v383`. Resolution: GPU Sweep mode uses its own v3.9.0 signal pipeline call — not the existing one.
- ISSUE 2 (CRITICAL): Column name mismatch — spec uses `cloud3_ok_long/short`, actual DataFrame uses `cloud3_allows_long/short`.
- ISSUE 3 (MODERATE): Reentry cloud3 gate — spec incorrectly says reentry is ungated; actual v3.9.0 code shows reentry IS cloud3-gated.
- ISSUE 4 (MINOR): Spec claims v393 has IndentationError; actual: v393 passes py_compile.

Corrected build plan creates 3 target files via build script `scripts/build_cuda_engine.py`: `engine/cuda_sweep.py` (Numba CUDA kernel), `engine/jit_backtest.py` (Numba @njit CPU core), `scripts/dashboard_v394.py`. Documents correct kernel entry logic, 12 signal arrays, GPU Sweep mode signal pipeline import from `four_pillars_v390`.

### Decisions recorded
- Build CUDA kernel from v3.9.0 (`Backtester390`) logic
- GPU Sweep mode imports `compute_signals` from `signals.four_pillars_v390` (NOT v3.8.3)
- Reentry is cloud3-gated (corrected from spec)
- Column extraction uses `df["cloud3_allows_long"]`

### State changes
- Corrected build plan written; original spec identified as having 4 issues
- No code built in this plan — plan only

### Open items recorded
- User runs `scripts/build_cuda_engine.py` to generate 3 target files
- Verification steps: GPU detected, heatmap, portfolio JIT mode, fallback

### Notes
CODE VERIFICATION: `engine/cuda_sweep.py` found at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py` — build was executed. Also `scripts/build_strategy_v391.py` found (separate build).

---

## bubbly-conjuring-pony.md

**Date:** 2026-03-03
**Type:** Planning / Execution

### What happened
Execution plan for running `build_dashboard_v1_4_patch4.py` and verifying results. Patch4 adds a "Close Market" button to the position action panel in the BingX live dashboard v1.4, plus CB-16 callback that cancels all open orders for the selected position and places a MARKET reduceOnly close.

Documents current state (patches 1-3 already applied, dashboard at 2293 lines). Anchor verification for both P1 and P2 patches included with exact line text. Steps include running build script, restarting dashboard, browser hard refresh, and verification checklist.

### Decisions recorded
- CB-16 uses `prevent_initial_call=True` and `allow_duplicate=True` on `pos-action-status` output
- `close_pending=True` written to state.json on close market action

### State changes
- Patch4 not yet applied at time of plan creation
- Build script `scripts/build_dashboard_v1_4_patch4.py` exists

### Open items recorded
- User to run build script and verify checklist items

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch4.py` exists on disk — build script created.

---

## bubbly-sparking-flute.md

**Date:** (no explicit date — inferred from context, BingX connector work, ~2026-03-03/04)
**Type:** Planning / Build spec

### What happened
Plan to replace the 0.16% distance-based breakeven (BE) trigger with TTP (Trailing Take Profit) activation as the sole auto-BE trigger. Changes span 3 files: `position_monitor.py`, `bingx-live-dashboard-v1-4.py`, `config.yaml`.

Key change: removes `BE_TRIGGER = 1.0016` constant and mark price API fetch from `check_breakeven()`. New trigger: `pos_data.get("ttp_state") == "ACTIVATED"`. Guard added: `be_auto` read from config, defaults True. New `be_auto` toggle added to Strategy Parameters tab in dashboard. CB-11 and CB-12 callbacks updated to load/save the toggle.

Provides complete `check_breakeven()` implementation with proper logging and Telegram notification.

### Decisions recorded
- TTP activation is the sole BE trigger (replaces 0.16% distance trigger)
- `be_auto` config key added under `position:` section, defaults True
- `_fetch_mark_price_pm()` method kept (may be used elsewhere)
- `_place_be_sl()` unchanged

### State changes
- position_monitor.py: 3 edits (store config, remove constant, rewrite check_breakeven)
- bingx-live-dashboard-v1-4.py: 3 edits (add toggle, CB-11 output, CB-12 state+save)
- config.yaml: add `be_auto: true` under position section

### Open items recorded
- Manual test: set `ttp_state: ACTIVATED` in test position, verify BE SL placed
- py_compile verification on both files

### Notes
This is distinct from the TTP engine integration plan. This plan only changes the BE trigger logic, not the TTP engine itself.

---

## bubbly-strolling-frog.md

**Date:** 2026-02-28
**Type:** Planning (minimal)

### What happened
Short planning note for Parquet data catch-up. Last 1m candle fetch was 2026-02-13 (15 days stale). No build needed — existing `scripts/fetch_data.py` and `data/fetcher.py` (BybitFetcher class) handle incremental updates. Cache location: `data/cache/` (399 coins, 1m only). Run command documented. 5m candles explicitly skipped per user decision.

### Decisions recorded
- No new code needed — use existing `scripts/fetch_data.py --months 1`
- 5m candles skipped (user decision)

### State changes
- No code changes — documentation only

### Open items recorded
- User to run: `python scripts/fetch_data.py --months 1`
- Verify `Symbols fetched: 399/399` in summary output

### Notes
None.

---

## cached-rolling-brooks.md

**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan for BingX bot runbook Steps 2-11 (Steps 0-1 already done). Approach: single master script `scripts/run_steps.py` that requests user permission upfront (prints full list of files to modify, new files to create, backups to create, Ollama call count, pytest run count), then executes all steps sequentially unattended with Ollama streaming visible in terminal.

Files to be modified: `position_monitor.py`, `main.py`, `state_manager.py`, `risk_gate.py`, `executor.py`. New files to create: `ws_listener.py`, `scripts/reconcile_pnl.py`. 7 backup files created automatically.

Steps map: Step 2 = commission rate in position_monitor, Step 3 = commission fetch in main.py, Step 5 = WSListener new file, Step 6 = main.py WS thread, Step 7 = position_monitor fill_queue, Steps 9a/9b/9c = cooldown + session_blocked, Step 10 = reconcile_pnl.py. Pytest runs at Steps 4, 8, 11 (>=67 passing required).

### Decisions recorded
- Single master script approach (not separate step scripts)
- User approves once upfront, no more prompts
- Script halts immediately on any py_compile or pytest failure

### State changes
- No code written — plan only

### Open items recorded
- Steps 2-11 all pending execution
- `ws_listener.py` to be created (does not exist yet)
- `scripts/reconcile_pnl.py` to be created

### Notes
Referenced session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-27-bingx-bot-live-improvements.md`. Cross-references `fluffy-singing-mango.md` (spec) and `cozy-swimming-lake.md` (runbook).

---

## compressed-stirring-quail.md

**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan to create a BingX friend handover package — documentation for a friend building a BingX futures trading bot. Two files: `PROJECTS/bingx-connector/docs/BINGX-FRIEND-HANDOVER.md` (new) and the existing `BINGX-API-V3-COMPLETE-REFERENCE.md` (224 endpoints, shared as-is).

Handover document structure: 11 sections covering authentication (HMAC-SHA256, URL encoding gotcha), 11 critical gotchas ordered by severity (signature encoding, commission rate, fill price, recvWindow, leverage hedge mode, listenKey POST not GET, listenKey response format, gzip WebSocket, heartbeat Ping/Pong, VST geoblocked on most datacenters, order history purged quickly), curated endpoint table (14 endpoints), order placement pattern, WebSocket user data stream setup, bot architecture patterns (dual-thread), risk gate 8 checks, exit detection strategy, state machine and recovery, deployment checklist.

### Decisions recorded
- Primary file: `BINGX-FRIEND-HANDOVER.md` (~400 lines)
- Existing API reference shared as-is
- Vault log copy to `06-CLAUDE-LOGS/plans/2026-02-28-bingx-friend-handover-package.md`

### State changes
- No code written yet — plan only
- Document to be created

### Open items recorded
- Write `BINGX-FRIEND-HANDOVER.md`

### Notes
VST demo API geoblocked on most datacenters (Indonesian IPs only) — recorded as gotcha #10.

---

## concurrent-sniffing-brook.md

**Date:** 2026-02-28
**Type:** Research / Audit / Planning

### What happened
Research audit of Vince B4 scope (PnL Reversal Panel). Identifies skills required, what B4 builds (4 functions in `vince/pages/pnl_reversal.py`), hard build order dependencies (B1→B2→B3 must complete first — entire vince/ directory does not exist), and 8 API/data bottlenecks.

Key bottlenecks surfaced: whether backtester_v384 outputs mfe/mae/saw_green/entry_atr, how saw_green is defined/tracked, whether TP sweep requires re-run or MFE simulation, which ATR bins to use, whether RL overlay is in B4 scope, whether EnrichedTrade carries OHLCV tuples, the input API surface from Dash layer, and gross vs net metric type.

6 improvements proposed over current spec: finer ATR bins (9 bins vs 6), winners-left-on-table metric, per-grade TP sweep, gross+net curve on TP sweep, temporal split of MFE data, breakeven-adjusted MFE view.

File existence audit: entire vince/ directory does not exist. strategies/base_v2.py exists (stub). signals/four_pillars.py recently modified.

### Decisions recorded
- B4 is pure Python (no Dash imports)
- RL overlay = placeholder only in B4, separate future scope
- `api.py` owns orchestration (B6 calls api.get_panel2_data(), not B4 directly)
- TP sweep uses simulation from MFE (not re-run) — same as reference implementation
- Enricher normalizes MFE to ATR units (B3 responsibility, not B4)
- 9-bin ATR scheme recommended: [0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, ∞]

### State changes
- Audit document created — no code written
- BUILD-VINCE-B4-PNL-REVERSAL.md to be created after approval

### Open items recorded
- Verify `engine/position_v384.py` has mfe/mae/saw_green/entry_atr fields
- Complete B1 → B2 → B3 before building B4
- Create BUILD-VINCE-B4-PNL-REVERSAL.md spec doc

### Notes
Explicitly calls out that "B4" in the archived BUILD-VINCE-ML.md refers to something different (Dashboard Integration for ML classifiers) — dead spec. The active B4 is Panel 2 from the v2 concept doc.

---

## cozy-squishing-orbit.md

**Date:** 2026-02-20 (implied from session log reference)
**Type:** Build spec / Planning

### What happened
BingX Execution Connector full build plan. Documents decisions, bug fixes, 25 files to generate via build script `build_bingx_connector.py`.

Decisions locked: v3 endpoints for public market data, v2 for trade/user operations, mock strategy only (FourPillarsV384 plugin = separate build), write files to PROJECTS/bingx-connector/.

Bug fixes from audit: C03 (halt_flag read by RiskGate), C04 (halt_flag reset daily), C05 (allowed_grades from plugin), C07 (public endpoints unsigned), C01 (LONG/SHORT/NONE vocabulary), C02 (mark price from /quote/price).

18 core files + 7 additional = 25 files total. Detailed module design for all major components (bingx_auth.py, data_fetcher.py, risk_gate.py, state_manager.py, executor.py, position_monitor.py, main.py, plugins/mock_strategy.py). 4-layer testing architecture: unit tests (no network), integration test, connection test (needs .env), live demo test. Detailed error handling patterns with graceful degradation table. Debug script `scripts/debug_connector.py` with 7 modes.

### Decisions recorded
- v3 endpoints for public data, v2 for signed operations
- Mock strategy only for initial build
- 25 files generated by one build script
- 3 validation checks per file: py_compile + ast.parse + import smoke test
- Dual thread model: market_loop (30s) + monitor_loop (60s)
- Exit price estimation defaults to SL price (pessimistic) — noted as future improvement

### State changes
- Full connector architecture designed
- 25 target files specified
- Session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-20-bingx-connector-build.md`

### Open items recorded
- Run build script
- Run tests on Jacky VPS
- Deploy in demo mode

### Notes
This is the original BingX connector build plan from ~2026-02-20. Subsequent sessions (cozy-swimming-lake, cached-rolling-brooks) show post-build improvements applied.

---

## cozy-swimming-lake.md

**Date:** 2026-02-27
**Type:** Planning / Execution

### What happened
Revised execution plan for BingX bot live improvements, specifically switching from Ollama non-streaming (`"stream":false` — 16 minutes silent per step) to streaming (`"stream":true` — tokens print in real-time). Documents current state (executor.py already patched FIX-2+FIX-3, all other files not yet patched).

Execution sequence for Steps 2-11: each step follows read→edit→py_compile→report→log pattern. Step 2 = position_monitor commission rate, Step 3 = main.py commission fetch, Step 4 = pytest, Step 5 = ws_listener.py new file, Step 6 = main.py WS thread, Step 7 = position_monitor fill_queue, Step 8 = pytest, Step 9 = state_manager/risk_gate/executor cooldown+session_blocked, Step 10 = reconcile_pnl.py, Step 11 = final pytest.

Rules: py_compile must pass before replacing any file, backup every file, log every action with timestamp, halt if any step fails.

### Decisions recorded
- Use streaming Ollama calls (stream:true)
- Backup pattern: `file.py.bak` via Bash
- Halt immediately if any step fails — wait for user

### State changes
- Plan revised from non-streaming to streaming approach
- No code written yet in this plan — execution plan only

### Open items recorded
- Steps 2-11 pending execution
- Session log: `06-CLAUDE-LOGS/2026-02-27-bingx-bot-live-improvements.md`

### Notes
Companion to `cached-rolling-brooks.md` (the master script approach) and to the original spec in `fluffy-singing-mango.md`. This plan uses direct Edit tool approach instead of a master script.

---

## crispy-petting-sloth.md

**Date:** 2026-02-28
**Type:** Build spec (agent-executable)

### What happened
Complete, executable instruction set for building the v386 strategy version. Context: `require_stage2: true` in `config.yaml` is the sole driver of trade frequency reduction from ~93/day to ~40/day on 47 coins. Documents what changed from v384 to v386 (require_stage2, allow_c, tp_atr_mult). Includes complete Python code for `signals/four_pillars_v386.py` (copy of signals/four_pillars.py with two defaults changed).

6-step execution plan: Glob check (no overwrite), write signals file + py_compile, write docs/FOUR-PILLARS-STRATEGY-v386.md (full strategy doc), update PRODUCT-BACKLOG.md (P0.5 DONE, P0.6 READY), append to TOPIC-vince-v2.md, create session log + update INDEX.md.

v386 strategy doc included in full: indicators, Stage 1/2 entry logic, signal grades, risk parameters, coin selection filter, differences from v384.

### Decisions recorded
- v386 = v384 with `require_stage2=True` and `allow_c=False`
- State machine (state_machine.py) unchanged — Stage 2 logic was already implemented
- No new files overwritten (HARD RULE enforced — Glob first)

### State changes
- `signals/four_pillars_v386.py` to be created
- `docs/FOUR-PILLARS-STRATEGY-v386.md` to be created
- PRODUCT-BACKLOG.md: P0.5 DONE, P0.6 READY
- TOPIC-vince-v2.md: v386 section appended

### Open items recorded
- All 6 execution steps pending (checkboxes all unchecked at end of plan)

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v386.py` EXISTS on disk — build was executed.

---

## crystalline-dreaming-sun.md

**Date:** 2026-03-05
**Type:** Planning / Architecture

### What happened
Plan to build a Python script that orchestrates sequential `claude -p` CLI calls to automate chronological log research across the entire vault. Context: ~201 session logs + ~149 plan files (~87,000 total lines) spanning Jan 2025 to March 2026.

Architecture: `scripts/run_log_research.py` discovers all .md files, splits into batches, runs `claude -p` per batch via subprocess, waits for completion, moves to next batch. 16 batches total (~350 files): Batches 1-15 use sonnet, Batch 16 (synthesis) uses opus.

Prompt template per batch specifies: read files in order, append findings to RESEARCH-FINDINGS.md using exact format, update RESEARCH-PROGRESS.md checkboxes, code verification for referenced scripts.

Estimated runtime: 5-8 hours unattended. Key flags: `--allowedTools "Read,Edit,Glob,Grep"`, `--max-turns 200`, `--verbose`.

Batch design table provided (16 batches, purposes of each).

### Decisions recorded
- Single orchestrator script approach
- Write tool excluded from allowed tools (prevents overwrites in subagent calls)
- Batches 1-15 use sonnet model, Batch 16 synthesis uses opus
- ~25 files per batch, mega-files get dedicated batches

### State changes
- Orchestrator script `scripts/run_log_research.py` to be created
- `RESEARCH-PROGRESS.md` created at runtime by script

### Open items recorded
- Write and run `run_log_research.py`
- All 16 batches pending

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_log_research.py` EXISTS on disk — build was executed. This is the orchestrator for the current research task.

---

## crystalline-stirring-glade.md

**Date:** 2026-03-04
**Type:** Planning / Build spec

### What happened
Plan for v3.9.1 Four Pillars signal quality rebuild. Context: v3.9.0 signals have 3 compounding problems — 3-phase SL movement system not implemented (position_v384 uses AVWAP center as SL trail), Cloud 2 hard close missing, Cloud 4 (EMA 72/89) not computed or used.

Goal: build v391 as faithful implementation per `ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` v2.0.

5 new files specified:
- `signals/clouds_v391.py` — adds Cloud 4 + cross detection columns
- `signals/four_pillars_v391.py` — calls compute_clouds_v391(), keeps state_machine_v390.py
- `engine/position_v391.py` — 3-phase SL system with phase state, phase 0 (initial), phase 1 (cloud2 cross), phase 2 (cloud3 cross), phase 3 (cloud3+4 sync trail), hard close, corrected AVWAP role
- `engine/backtester_v391.py` — imports position_v391, passes cloud cross columns to position slot, hard close check first, expanded update_bar signature, sl_phase field in trade record
- `scripts/build_strategy_v391.py` — single build script

State machine v390 kept unchanged — A/B/reentry logic correct.

### Decisions recorded
- State machine stays at v390 (signal detection structurally correct)
- AVWAP moved to correct role: ADD entry trigger + scale-out trigger only (NOT SL trail)
- ADD signals changed from AVWAP-price trigger to stochastic-based trigger
- Phase 3: TP removed when Cloud3+4 sync, trail_extreme tracks highs/lows
- Hard close (Cloud 2 flips against trade) is highest priority exit, checked before SL

### State changes
- Build script `scripts/build_strategy_v391.py` to be created
- 4 engine/signal files to be created (all new, no overwrites)

### Open items recorded
- Run build script
- Smoke test on one symbol
- Verify sl_phase > 0 in trades, CLOUD2_CLOSE exits, Phase 3 trail active

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_strategy_v391.py` EXISTS on disk — build was executed.

---

## cuddly-dancing-perlis.md

**Date:** 2026-03-03 (revised after audit)
**Type:** Planning / Build spec

### What happened
Plan for TTP (Trailing Take Profit) engine integration with BingX connector and dashboard. Context: ttp_engine.py drafted by Opus has 4 remaining bugs; existing bot uses fixed ATR-TP placed at entry; user wants TTP toggleable from dashboard, displayed per-position.

4 bugs in ttp_engine.py: Bug 1 = `self.state` never set to CLOSED, Bug 4 = CLOSED_PARTIAL state (replace with CLOSED everywhere), Bug 5 = iterrows() slow/fragile (replace with itertuples), Bug 6 = `band_width_pct` `or 0` fallback (guard with proper None check).

Architecture: hybrid split — Thread 1 (market loop via signal_engine.py) evaluates TTP using real 1m OHLC bars, Thread 2 (monitor loop via position_monitor.py) executes TTP closes. `ttp_close_pending` flag bridges threads via state.json. Race guard: monitor verifies position exists on exchange before placing MARKET close.

7 files touched: ttp_engine.py (create), signal_engine.py (modify), position_monitor.py (modify), main.py (modify), config.yaml (modify), bingx-live-dashboard-v1-4.py (Patch 3), tests/test_ttp_engine.py (create).

Two build scripts: `scripts/build_ttp_integration.py` (connector files), `scripts/build_dashboard_v1_4_patch3.py` (dashboard only).

Dashboard changes (Patch 3): add TTP + Trail Lvl columns to POSITION_COLUMNS, update build_positions_df, add TTP section to Controls tab (toggle + activation % + trail distance %), update CB-11 and CB-12.

### Decisions recorded
- TTP evaluation uses real 1m OHLC (not mark price) — preserves dual scenario band
- TTP engines live in signal_engine (market loop), keyed by position key
- Existing fixed TP orders still placed on entry — TTP runs alongside, whichever fires first wins
- Exit reason "TTP_EXIT" logged in trades.csv

### State changes
- ttp_engine.py to be created (with 4 bugs fixed)
- signal_engine.py, position_monitor.py, main.py, config.yaml all to be modified
- bingx-live-dashboard-v1-4.py Patch 3 applied
- tests/test_ttp_engine.py to be created (6 unit tests)

### Open items recorded
- Run both build scripts
- 10 verification steps including race test

### Notes
Explicitly states "Replace fixed TP with TTP" is out of scope for this session (separate session).

---

## dashboard-v1-2-improvements.md

**Date:** 2026-02-28 (implied from context)
**Type:** Planning

### What happened
Plan for BingX Dashboard v1.2 improvements based on v1.1 live testing screenshots/notes. 5 fixes + 3 analytics improvements:

- FIX-1: White input fields on Bot Controls tab (CSS fix for dcc.Input, dcc.RadioItems, dcc.Dropdown)
- FIX-2: Positions grid white background ("No Rows To Show" on white bg with dark theme)
- FIX-3: Analytics shows all-time trades vs History shows today only — add date range picker
- FIX-4: Tab re-render on switch (Option A selected: render all tabs in layout, toggle visibility with clientside callback — removes CB-2 render_tab, ~80 lines changed)
- FIX-5: Add timing diagnostics in CB-1

3 analytics improvements: professional metrics (Sharpe, LSG%, BE Hit, MaxDD%, SL Hit%, TP Hit%), date range picker, chart cleanup (no toolbar, proper labels).

Blocker identified: LSG% requires MFE tracking in position_monitor.py (not in dashboard scope); BE Hit Count requires be_raised written to trades.csv on close. Both show "N/A" until bot changes made.

### Decisions recorded
- FIX-4 Option A selected: render all tabs, toggle visibility (not dynamic tab content)
- CB-2 (render_tab) removed
- LSG% and BE Hit will show "N/A" placeholder until bot tracking added

### State changes
- No code written — plan only
- Files to touch: bingx-live-dashboard-v1-1.py, assets/dashboard.css, scripts/test_dashboard.py

### Open items recorded
- Implement all 8 items in build order
- Bot changes needed (separate scope): MFE tracking in position_monitor, be_raised in trades.csv

### Notes
This plan targets bingx-live-dashboard-v1-1.py (producing v1.2). Not the Dash-based v1.4 dashboard.

---

## distributed-exploring-lerdorf.md

**Date:** (no explicit date — implied ~2026-03-03/04)
**Type:** Planning / Build spec

### What happened
Plan for a daily Bybit data updater script. Context: backtester data cache (399 coins, data/cache/) stale since 2026-02-13. New standalone script purpose-built for daily incremental updates (not patching fetch_data.py).

Build script: `scripts/build_daily_updater.py` creates `scripts/daily_update.py`.

daily_update.py does: Step 1 = discover symbols from Bybit (v5/market/instruments-info), Step 2 = incremental fetch for each symbol (read .meta for cached_end_ms, fetch only gap, append+deduplicate, update .meta; full fetch for new symbols), Step 3 = resample to 5m via TimeframeResampler, Step 4 = summary + log.

CLI flags: `--months`, `--skip-new`, `--skip-resample`, `--max-new`, `--dry-run`.

Reuses `BybitFetcher` from `data/fetcher.py` and `TimeframeResampler` from `resample_timeframes.py`. Symbol discovery pattern from `fetch_sub_1b.py` lines 113-126.

### Decisions recorded
- Standalone script (not patching fetch_data.py)
- Incremental append logic lives in daily_update.py (not patched into fetcher.py)
- Rate limit: 0.12s between requests (matches fetch_sub_1b.py)
- Log to `logs/YYYY-MM-DD-daily-update.log` with dual handler

### State changes
- Two new files planned: build_daily_updater.py + daily_update.py

### Open items recorded
- User to run `python scripts/build_daily_updater.py` then `--dry-run`

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_daily_updater.py` EXISTS on disk — build was executed.

---

## dynamic-bubbling-cray.md

**Date:** 2026-02-28
**Type:** Planning / Build spec

### What happened
Plan for the initial BingX live dashboard v1.0. Read-only monitoring with 3 tabs: Positions (open positions from state.json + mark price API), History (closed trades from trades.csv), Coin Summary (grouped stats from trades.csv).

Framework chosen: Streamlit (not Dash). Rationale: read-only monitoring with 3 tabs, file-based data, simple tables. Streamlit = ~150 lines vs Dash = ~300 lines. Uses `st.tabs()`, `st.dataframe()`, `time.sleep(60); st.rerun()`.

Tab 1 columns: Symbol, Direction, Grade, Entry Price, Stop Loss, Take Profit, BE Raised, Unrealized PnL, Duration. Row color: green=LONG, red=SHORT.
Tab 2 columns: Date/Time, Symbol, Direction, Grade, Entry/Exit Price, Exit Reason, Net PnL, Duration. Default: today's trades.
Tab 3: Symbol grouped stats including SL%/TP%/Unknown% exit breakdown (LSG% noted as requiring MFE data not available).

Data files: state.json, trades.csv, config.yaml, .env, BingX /quote/price API.

### Decisions recorded
- Streamlit chosen over Dash for monitoring dashboard
- File: `bingx-live-dashboard-v1.py` at PROJECTS/bingx-connector/
- Run: `streamlit run ...`
- No buttons, no order actions — read-only only

### State changes
- Dashboard file to be created
- No existing files modified

### Open items recorded
- Write and run dashboard

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1.py` EXISTS on disk. This is the initial Streamlit version — later superseded by Dash-based versions (v1.1, v1.2, v1.4).

---

## eager-snacking-pearl.md

**Date:** (no explicit date — implied ~2026-02-28/early March)
**Type:** Planning / Build spec

### What happened
Plan to accelerate the backtester dashboard using timing instrumentation and safe Numba JIT. Context: user asked if sweep/portfolio loading can run on GPU — answer: no (sequential state machine). Real solution: measure first, then apply Numba only to confirmed pure-numpy kernels.

Numba 0.61.2 already installed. Python 3.13 + llvmlite 0.44.0 + numpy 2.2.6 confirmed compatible. Dashboard v391 will NOT be touched — zero files modified, new files only.

Audit findings confirmed from source:
- SAFE for @njit: `stoch_k()` in stochastics.py, `ema()` in clouds.py, ATR RMA loop (requires extraction to function)
- NOT SAFE: compute_all_stochastics(), compute_clouds(), compute_signals_v383(), FourPillarsStateMachine383.process_bar(), Backtester384.run()

Two-phase plan:
- Phase 1: `utils/timing.py` — context manager + accumulator. Performance Debug checkbox in sidebar shows per-phase/per-coin milliseconds.
- Phase 2: Three new signal files with @njit(cache=True): stochastics_v2.py, clouds_v2.py, four_pillars_v383_v2.py. Dashboard v392 imports from v2 signals.

6 files created total (zero files modified). Expected speedup ~22% per-coin for signal computation (state machine and backtester unchanged). Verification protocol: baseline metrics recorded from v391, v392 must produce EXACTLY equal results, timing panel confirms improvement.

### Decisions recorded
- Numba applied only to confirmed safe kernels (3 functions)
- dashboard_v391.py STABLE — never touched
- cache=True on all @njit decorators
- Rollback: delete 6 new files — v391 immediately back to normal

### State changes
- 6 new files to be created by `scripts/build_dashboard_v392.py`
- Numba first-run compilation 2-5s (one-time)

### Open items recorded
- Record baseline from v391 before building v392
- Run build script
- Verify numerical parity on RIVERUSDT

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v392.py` EXISTS on disk — build was executed.

---

## elegant-enchanting-wilkinson.md

**Date:** (no explicit date — implied ~2026-02-16/17 based on BBW pipeline context)
**Type:** Planning / Build spec

### What happened
Plan for remaining 3 components of the BBW (Bollinger Band Width) pipeline. Layers 1-5 already complete and tested. Three remaining components to make the pipeline fully runnable end-to-end:

1. `research/coin_classifier.py` — KMeans volatility tier assignment (4 functions, 15 tests)
2. `research/bbw_ollama_review.py` — Layer 6 LLM analysis of Layer 5 CSV output (3 analysis functions + run_ollama_review, 15 tests)
3. `scripts/run_bbw_simulator.py` — CLI entry point wiring all layers (run_pipeline, 12 tests)

Delivery: one build script `scripts/build_bbw_remaining.py` using build_staging.py pattern (FILES dict → write → py_compile → run tests → report). 9 files total.

Data contracts documented from existing codebase. Ollama models confirmed: qwen3:8b, qwen2.5-coder:14b, qwen2.5-coder:32b, qwen3-coder:30b, gpt-oss:20b. Error handling for offline Ollama (writes OFFLINE message, never raises).

CLI flags for run_bbw_simulator.py: --symbol, --tier, --timeframe, --top, --no-monte-carlo, --mc-sims, --no-ollama, --ollama-model, --output-dir, --verbose, --dry-run.

### Decisions recorded
- Build script pattern follows build_staging.py
- 9 files generated by one build script
- Ollama offline: write OFFLINE message, continue — never raises exception
- Debug scripts included for all 3 components

### State changes
- `scripts/build_bbw_remaining.py` to be created
- 9 target files (3 main + 3 test + 3 debug) to be created by build

### Open items recorded
- Run build script (expected: 9/9 syntax pass, 42/42 tests pass)
- Run `scripts/debug_run_bbw_simulator.py` for full pipeline smoke test on RIVERUSDT

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_bbw_remaining.py` EXISTS on disk — build was executed.


# Research Batch 18 Findings — Auto-Plans (e through i)

**Generated:** 2026-03-06
**Files processed:** 20
**Source directory:** C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\

---

## elegant-weaving-sutherland.md
**Date:** 2026-03-05
**Type:** Planning

### What happened
Plan for a config-toggled native trailing stop switch for the BingX connector. Context: the custom TTP engine evaluates on confirmed 5m candles creating up to ~6min worst-case delay before trailing exit fires. BingX native `TRAILING_STOP_MARKET` runs tick-level on exchange. A previous native trailing attempt had failed because activation was ATR-based (too far) and callback was 2% (too wide). This plan uses percentage-based params matching the working TTP config.

New config key `ttp_mode` with values `"native"` (exchange-managed, tick-level) or `"engine"` (existing custom 5m-candle TTP, default). Reuses existing `ttp_act=0.008` and `ttp_dist=0.003` for both modes.

6 files to modify: config.yaml, executor.py, signal_engine.py, position_monitor.py, ws_listener.py, state_manager.py (~65 lines changed total).

Critical bug fix designed: `"STOP" in "TRAILING_STOP_MARKET"` evaluates True in Python, so BE raise would cancel native trailing orders in `_cancel_open_sl_orders`. Fix: exclude `TRAILING_STOP_MARKET` from cancellation check. Also: `_detect_exit` must detect when trailing_order_id disappears from open orders (= it fired), and `_fetch_filled_exit` and `ws_listener._parse_fill_event` must classify `TRAILING_STOP_MARKET` as `TRAILING_EXIT`.

Delivery: build script `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_native_trailing.py`.

### Decisions recorded
- `ttp_mode: native` added to config.yaml under position section
- `_place_trailing_order()` gains `price_rate` override parameter
- `signal_engine.py` early-returns when `ttp_mode == "native"` (skip engine evaluation)
- `position_monitor.py` skips `check_ttp_closes` and `check_ttp_sl_tighten` in native mode
- BE raise still active in native mode (safety net between +0.4% and +0.8%)
- If native trailing rejected by exchange: log error, SL remains, no fallback to engine
- `ttp_engine.py`, `main.py`, and dashboard deferred/out of scope

### State changes
- Plan created for 6-file modification
- Critical BE/native trail interaction bug identified and fix designed
- `TRAILING_EXIT` reason added to trades.csv classification design
- Build script `build_native_trailing.py` planned

### Open items recorded
- Build script to be written and executed
- Manual verification: `ttp_mode: native` + `demo_mode: true`, verify trailing placed, BE doesn't cancel it, exit classified as `TRAILING_EXIT`
- Switchback test: `ttp_mode: engine`, verify three-stage pipeline fully restored

### Notes
Three-stage interaction table provided: BE raise (+0.4%), TTP activation (+0.8%), trail (0.3% callback). Previous failed attempt used ATR-based activation and 2% callback.

---

## enumerated-dazzling-squirrel.md
**Date:** 2026-03-05 (inferred from content — references work through 2026-03-05)
**Type:** Planning

### What happened
Plan for staging all vault repo changes and pushing to GitHub (S23Web3/ni9htw4lker). Covers all work from 2026-03-03 through 2026-03-05: BingX connector v1.5 patches (timestamp sync fix, TTP engine, config tuning), backtester v391 modules, session logs, build scripts, documentation updates. VPS was already configured with .env and environment; bot to be pulled and run on VPS after push.

5-step plan:
1. `git add -A` in vault root
2. Verify 12 critical bot files staged (including new `time_sync.py`, `main_beta.py`, `config_beta.yaml`, `bingx-live-dashboard-v1-5.py`)
3. Commit with specified message
4. `git push origin main`
5. Post-push verification + VPS instructions

Scope: 20 modified tracked files, 70+ new untracked files, 0 files with secrets (config.yaml has no API keys, bingx_auth.py reads from env vars).

### Decisions recorded
- Commit message: `"Vault update: BingX v1.5 (time sync, TTP, config tuning), backtester v391, session logs 2026-03-03 to 2026-03-05"`
- All files verified clean of secrets before push
- VPS next step: `git pull origin main` then `python main.py`

### State changes
- This plan documents the git push that produced commit `e85b370` (confirmed in current git log)

### Open items recorded
- VPS: `git pull origin main` + verify `time_sync.py` exists

### Notes
Commit `e85b370` in current git log confirms this plan was executed successfully.

---

## eventual-plotting-pony.md
**Date:** Not explicitly stated (BingX connector early setup phase)
**Type:** Guided instructions / Setup document

### What happened
Step-by-step instructions for connecting the BingX bot to Telegram by populating `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the `.env` file. Code was already fully built (`notifier.py` complete, `main.py` loads from `.env`). Only the placeholder values were blocking alerts.

5 steps: create bot via @BotFather, get Chat ID via `getUpdates` API URL, edit `.env`, test with a Python one-liner (sends "BingX bot Telegram test OK"), run bot and verify startup Telegram message. References `STEP1-CHECKLIST.md` item `**Telegram alert received**`.

### Decisions recorded
- No quotes or spaces around `=` in .env values
- Test one-liner provided before running bot

### State changes
- No code changes — purely a user instruction document

### Open items recorded
- User must complete all 5 steps and check off `Telegram alert received` in STEP1-CHECKLIST.md

### Notes
No date in file. Context places it in early BingX connector setup (before first signal fired). This is a user-facing guide, not a technical build plan.

---

## eventual-tickling-stardust.md
**Date:** 2026-03-03
**Type:** Fix plan / Audit execution

### What happened
Plan to apply findings from a full logic audit of `cuda_sweep.py`, `dashboard_v394.py`, and BingX connector files via a single build script. Previous session documented findings without applying fixes.

**CRITICAL #1** — Commission split in cuda_sweep.py: same rate (0.0008) used for both entry and exit. Fix: add `maker_rate=0.0002` param, split into `entry_comm` and `exit_comm`. Impact: all prior GPU sweep P&L numbers overstated by 0.06% × notional per RT.

**CRITICAL #2** — `pnl_sum` missing entry commission: Fix: `pnl_sum += net_pnl - entry_comm` at both exit points.

**HIGH #3** — win_rate displayed as raw decimal in 3 table locations in dashboard_v394.py. Fix: multiply × 100, rename to `win_rate%`.

**HIGH #4** — TTP state lost on restart: REASSESSED as already fixed (signal_engine.py lines 113-127 already restores from persisted fields). No action.

**HIGH #5** — WSListener dies permanently after 3 reconnect failures with no alert. Fix: MAX_RECONNECT=10, exponential backoff, write `logs/ws_dead_{timestamp}.flag`.

**HIGH #6** — `_place_market_close()` missing reduceOnly: LOW risk in hedge mode. Decision: add `"reduceOnly": "true"` as defensive measure.

**HIGH #7** — `saw_green` uses `>` instead of `>=` at cuda_sweep.py lines 163/171.

Build script `build_audit_fixes.py` patches 4 files: cuda_sweep.py, dashboard_v394.py, ws_listener.py, position_monitor.py.

### Decisions recorded
- HIGH #4 confirmed already fixed — skipped
- HIGH #6 downgraded to LOW but add reduceOnly defensively
- `maker_rate=0.0002` added to `run_gpu_sweep()` and `run_gpu_sweep_multi()` signatures
- Patch via exact string replacement (no full rewrite)
- MEDIUM/LOW issues deferred

### State changes
- 4 files planned for patching
- All prior GPU sweep P&L numbers confirmed overstated (0.06% × notional per RT)
- Build script `build_audit_fixes.py` planned

### Open items recorded
- User runs GPU Sweep post-fix, verifies `win_rate%` shows 42.3 not 0.423
- Verify net_pnl figures lower than previous runs

### Notes
Previously noted TTP state restoration fix (signal_engine.py lines 113-127) confirmed correct by this audit.

---

## expressive-painting-taco.md
**Date:** Not explicitly stated (post-VPS-block discovery; consistent with early March 2026)
**Type:** Planning

### What happened
Plan for two deliverables: (1) Windows Task Scheduler auto-start on reboot with crash recovery, and (2) improved Telegram message formatting. Context: VPS (Hostinger Jakarta) cannot reach BingX VST API (Indonesian IPs block datacenter connections) — bot runs locally on Windows in demo mode (47 coins, 5m).

One build script `build_autostart_and_tg.py` backs up 3 existing files, creates 3 new files (PowerShell wrapper `run_bot.ps1`, Task Scheduler XML `bingx-bot-task.xml`, installer `install_autostart.ps1`), and modifies 3 existing files (executor.py, position_monitor.py, main.py — Telegram HTML formatting).

PowerShell wrapper: crash recovery loop, restarts on non-zero exit code after 30s delay, does NOT restart on clean exit (code 0). Task Scheduler: AtStartup trigger, 60s network delay.

Telegram messages reformatted from single-line dumps to multi-line HTML with `<b>` bold headers. 10 exact string replacements specified: ENTRY, ORDER FAILED, ORDER ID UNKNOWN, EXIT, DAILY SUMMARY, HARD STOP, WARNING, BOT STARTED, BOT STOPPING, BOT STOPPED.

### Decisions recorded
- Clean exit (code 0) = intentional stop, no restart; non-zero = crash, restart after 30s
- Task Scheduler: AtStartup, 60s delay, run hidden
- HTML parse mode (`<b>` tags) for all Telegram messages
- Bot runs locally on Windows (not VPS) due to VST API block

### State changes
- Build script planned creating 3 new files + modifying 3 existing (with timestamped .bak backups)

### Open items recorded
- User must run `install_autostart.ps1` as admin to register task
- Reboot test + crash recovery test required

### Notes
Indonesian VPS IPs block datacenter connections to BingX VST API — this was the constraint forcing local Windows execution.

---

## fizzy-humming-crab.md
**Date:** 2026-03-04
**Type:** Research / Strategy specification

### What happened
Comprehensive position management study document based on two live TradingView Replay walkthroughs: PUMPUSDT LONG (Wed 04 Mar '26, 5m Bybit Spot) and PIPPINUSDT SHORT (Tue 03 Mar '26, 5m Bybit Perpetual). Both are trend-hold type (stoch 60 gate opens). Documents the full trade lifecycle across 6 phases.

**Three-layer HTF direction system:** Layer 1 = 4h/1h session bias (Ripster EMA cloud transitions); Layer 2 = 15m MTF Clouds on 5m chart (hold duration modulator, not hard binary); Layer 3 = 5m execution timing. All three must agree.

**Entry detection:** All 4 stochastics (9, 14, 40, 60 Raw K) must have K/D crossovers — sequential process, stoch 9 crosses first (alert), wait for others. Recent zone check: K must have been below 20 (long) or above 80 (short) within last N=10 bars. BBW spectrum must cross from below to above MA. TDI price line on correct side of MA.

**SL:** 2 × ATR(14) from entry, validated against structural level.

**Gate check:** Stoch 60 K vs D crossing = gate opens = trend-hold mode.

**Trend hold management:** TDI 2-candle rule (hard exit), BBW health monitor (healthy/extreme/exit states), AVWAP trailing (plain or +2sigma), Ripster Cloud 4 value FROZEN at confirmation = TP target.

**Add-ons:** Stoch 9/14 must reach opposite zone while 40/60 hold trend direction.

Conclusion: "This is not a patch on v386. It is a different strategy architecture." Contradicts ATR-SL-MOVEMENT-BUILD-GUIDANCE.md which makes ATR central to phase transitions (ATR role here = thermometer only).

### Decisions recorded
- N=10 bars for recent zone check (flagged for Vince optimization)
- MTF clouds = hold duration modulator (not hard binary filter)
- ATR: thermometer only (SL sizing + volatility confirmation, not phase driver)
- No code until user explicitly approves the rules

### State changes
- Study document only — no code written
- State machine diagram created
- Full comparison table: User's Actual Trading vs ATR-SL-MOVEMENT Spec vs AVWAP 3-Stage vs v386

### Open items recorded
- 7 open questions: SL-1 (2 ATR not aligned with structure?), SL-2 (what counts as structure?), GATE-1 (K/D distance threshold?), BE-1 (two BE methods interchangeable?), TRAIL-1 (AVWAP variant selection), CLOUD-1 (frozen Cloud 4 longs-only?), TP-1 (cloud vs % target?)
- BBW BBWP percentile thresholds marked as "flagged for Vince research" — no numeric boundaries

### Notes
Document explicitly states: "No code should be written until the user explicitly approves the rules." This is a research artifact, not a build plan.

---

## floating-jingling-valiant.md
**Date:** 2026-03-05
**Type:** Audit / Quality review

### What happened
Thoroughness audit of the `2026-03-05-next-chat-prompt.md` continuation prompt. Bot was RUNNING and must NOT be restarted (48h live data collection). Found 2 errors and 3 gaps; verified 8 claims as correct.

**ERROR 1 (Task 1 function mismatch):** Prompt says `compute_signals()` in `signals/four_pillars.py` accepts `require_stage2`/`rot_level`. Reality: dashboard_v394.py line 57 imports `compute_signals_v383()` from `signals/four_pillars_v383_v2.py` which does NOT accept those params. Fix options: (A) switch import line 57 to `compute_signals` from `signals.four_pillars`, or (B) add params to the v383 function.

**ERROR 2 (Task 2 already 80% done):** Prompt says 5 bugs still pending. Reality: `bingx-live-dashboard-v1-5.py` already EXISTS (133K, built 2026-03-04) with patches P3-A through P3-H applied. BUG-4/BUG-1b/BUG-2/BUG-5 all fixed. Only `be_act` save callback genuinely missing.

**GAPs:** (1) No bot restart constraint, (2) Stale runtime data, (3) Import switch not mentioned.

Verified correct: Three-stage TTP config values (be_act=0.004, ttp_act=0.008, ttp_dist=0.003), orderId extraction in 3 places, unrealized PnL in Telegram, max_positions=25, test pass count, key file paths.

Plan: Create corrected v2 prompt at `2026-03-05-next-chat-prompt-v2.md` (do NOT overwrite original). 4 specific fixes documented.

### Decisions recorded
- Option A for Task 1: change import (line 57) to `from signals.four_pillars import compute_signals`
- Task 2 scoped down to `be_act` settings save only
- Create v2 prompt file, preserve original

### State changes
- New file planned: `06-CLAUDE-LOGS/plans/2026-03-05-next-chat-prompt-v2.md`
- Audit findings documented

### Open items recorded
- Write v2 prompt with all 4 fixes; read back to verify

### Notes
Confirms `bingx-live-dashboard-v1-5.py` existed as of 2026-03-04 with most bugs already fixed.

---

## fluffy-singing-mango.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
BingX bot improvement plan after scraping the full BingX API v3 reference (224 endpoints, 849KB). Decision context: stop polishing VST demo, prepare infrastructure for live money.

**3 key API discoveries:**
1. Commission rate queryable — `GET /openApi/swap/v2/user/commissionRate` returns actual taker/maker rates. Bot hardcoded 0.0012; real rate is 0.0016 RT — every trade understated commission by 33%.
2. Position history gives BingX-calculated PnL (`netProfit` with actual commission + funding fees — ground truth).
3. WebSocket ORDER_TRADE_UPDATE gives real-time fills — eliminates EXIT_UNKNOWN. Entry price wrong: bot uses `mark_price`, actual fill is `data.avgPrice`.

**P0 bugs:** FIX-1 (commission hardcoded wrong), FIX-2 (entry price = fill price not mark), FIX-3 (SL direction validation).

**P1:** IMP-1 (new `ws_listener.py` WebSocket daemon thread), IMP-2 (`scripts/reconcile_pnl.py` standalone PnL audit).

**P2:** IMP-3 (error 101209 max position value), IMP-4 (cooldown filter), IMP-5 (startup commission fetch).

**P3:** IMP-6 (batch cancel on shutdown), IMP-7 (Cancel All After safety timer), IMP-8 (trailing stop option).

Full Ollama-based build runbook (Steps 1-11): paste file content, apply specific changes, py_compile each result.

### Decisions recorded
- Build via Ollama (local LLM) code generation
- New files: `ws_listener.py`, `scripts/reconcile_pnl.py`
- WSListener = threading.Thread, daemon=True; fill_queue drain before polling
- Commission rate RT = taker rate × 2 = 0.0016

### State changes
- Improvement catalog created (11 items, 4 priority levels)
- All prior trade PnL records confirmed to have understated commission by 33%

### Open items recorded
- 11-step build runbook
- P2/P3 improvements deferred

### Notes
`ws_listener.py` was subsequently built (confirmed in git status as `M PROJECTS/bingx-connector/ws_listener.py`). This plan predates that implementation.

---

## fluttering-kindling-creek.md
**Date:** Not explicitly stated (references v1-1 spec; context ~2026-02-28)
**Type:** Planning

### What happened
Execution plan for building BingX Live Dashboard v1-1 from the complete spec in `C:\Users\User\.claude\plans\goofy-dancing-summit.md` (1795 lines). Previous session finalized spec but hit context limit before writing code.

3 files to build:
1. `bingx-live-dashboard-v1-1.py` (~700 lines) — Dash 4.0, port 8051, 5 tabs, 14 callbacks, ag-grid, dark theme, BingX API integration for position management (Raise BE, Move SL), config editor, halt/resume
2. `assets/dashboard.css` (~20 lines)
3. `scripts/test_dashboard.py` (~170 lines)

7-step build plan: load Dash skill, write 3 files, py_compile both .py files, give run command.

Key technical decisions: `suppress_callback_exceptions=True`, `prevent_initial_call=False` for CB-1/CB-2, API signing replicated in dashboard (not imported from bot), `ThreadPoolExecutor(max_workers=8)` for price fetches, atomic writes via tmp + `os.replace()`, dual logging with `TimedRotatingFileHandler`.

### Decisions recorded
- Dash 4.0 not Streamlit (Streamlit reruns full script on every click, wiping mid-action form state)
- Pattern-matching callbacks (MATCH selector) required for per-row Raise BE / Move SL
- Load Dash skill mandatory per MEMORY.md
- Existing v1 (Streamlit, `bingx-live-dashboard-v1.py`) must NOT be touched

### State changes
- No code written yet — plan to execute goofy-dancing-summit.md spec

### Open items recorded
- Build steps 1-7 to be executed
- User verification: py_compile, test_dashboard.py, launch at port 8051

### Notes
References `goofy-dancing-summit.md` as source spec. That file is also in this batch (see below).

---

## foamy-soaring-snowflake.md
**Date:** 2026-03-05
**Type:** Fix plan — Runtime error resolution

### What happened
Dashboard v1.5 passed `py_compile` but had never been run until 2026-03-05. First launch revealed 2 code errors and 1 API error.

**Error 1:** `KeyError: "Callback function not found for output 'store-bot-status.data'."` — `dcc.Store(id='store-bot-status', data=[])` at line 1141 was the only store not using `storage_type='memory'`. All 4 other stores use `storage_type='memory'` and work fine. The `data=[]` conflicts with callback registration.

**Error 2:** `IndexError: list index out of range` in `_prepare_grouping` — likely cascading from Error 1. Re-test after fixing Error 1. If persists, investigate CB-3 (line 1252), CB-9 (line 1933), CB-10 (line 2089).

**Error 3:** `BingX error 100001: Signature verification failed` — API auth issue, not code bug. User must verify `.env` keys.

Fix: build script `build_dashboard_v1_5_patch_runtime.py` applies one-line patch: `dcc.Store(id='store-bot-status', storage_type='memory')`.

### Decisions recorded
- Single patch: align store-bot-status with all other stores
- Error 100001 is user action (verify .env keys), not code
- `be_act` save bug and dashboard_v395 preset deferred to separate tasks

### State changes
- Single-line change to `bingx-live-dashboard-v1-5.py` line 1141
- Build script `build_dashboard_v1_5_patch_runtime.py` planned

### Open items recorded
- User re-runs dashboard after patch, verifies no KeyError/IndexError in first 30 seconds
- Signature errors persist until .env keys updated

### Notes
The v2 continuation prompt had only listed `be_act` — these runtime errors were new findings discovered at first launch.

---

## functional-orbiting-rabbit.md
**Date:** 2026-02-18
**Type:** Handoff document / Comprehensive session summary

### What happened
Vince ML v2 full handoff document created when context limit hit. Contains: critical error log, Vince ML v2 scope (in progress), full code audit of dashboard and engine, pending items.

**Critical error logged:** Claude inverted "under 60" to "past/over 60" when restating user direction — opposite signal meaning. Prevention rule: NEVER paraphrase directional statements; "under 60" = "< 60".

**Vince ML v2 scope (IN PROGRESS, not finalized):**
- Vince = trade research engine that reads trade CSV, enriches with indicator constellations at every bar, finds relationships using GPU (PyTorch), extracts robust parameters
- NOT a trade filter/classifier (previous v1 build = Vicky's architecture: XGBoost classifier, TAKE/SKIP decisions, reduces volume — wrong for rebate strategy)
- Evidence: 86% LSG across 2 unoptimized 10-coin runs (77K-90K trades each) — entries work, exits lose money
- Data flow: Stage 1 (Strategy → Trade CSV) → Stage 2 (Vince: Enricher → Relationship Engine → Cross-Validation → Dashboard)
- Key moments to snapshot: entry bar, MFE bar, MAE bar, breakeven bar, exit bar, phase transition bars, cloud cross bars

**Full code audit (9 files):**
- stochastics.py, clouds.py, state_machine_v383.py, four_pillars_v383.py: CORRECT
- backtester_v384.py: CORRECT with 1 known bug — scale-out entry commission double-count in Trade CSV (equity curve unaffected, LOW severity)
- position_v384.py, avwap.py, commission.py: CORRECT
- dashboard_v391.py (2338 lines): CORRECT — direct pass-through, no inflation
- Audit verdict: "The 77K-90K trades and 85-86% LSG numbers are REAL."

### Decisions recorded
- Vince = relationship research engine, NOT Vicky (trade classifier)
- NEVER reduce trade count (volume = $1.49B/year, rebate critical)
- Strategy-agnostic base (Andy = forex later)
- No prioritization of relationship questions
- "Under 60" = "< 60" — never to be paraphrased

### State changes
- Vince ML v2 scope IN PROGRESS, not finalized
- Full code audit completed; all engine math verified correct
- Scale-out commission double-count bug documented (not fixed)

### Open items recorded
1. Vince ML v2 scope not finalized — resume scoping
2. Scale-out commission bug — not fixed (equity unaffected, low priority)
3. RE-ENTRY logic — "currently totally wrongly programmed," deferred
4. Dashboard v3.9.2 build script written but not run by user
5. Architecture breakdown — next step after scope finalized

### Notes
This is the 2026-02-18 handoff document. Covers the pivot from Vicky (classifier) to Vince (research engine) architecture. dashboard_v391.py referenced here (2338 lines); later versions up to v394 were built in subsequent sessions.

---

## generic-humming-kurzweil.md
**Date:** Not explicitly stated (BingX connector setup context)
**Type:** Planning

### What happened
Plan for two tasks in the BingX connector:

**Task 1 — `historical_fetcher.py`:** Standalone script/importable module to pull full historical OHLCV from BingX public klines endpoint (`/openApi/swap/v3/quote/klines`, no auth) and save as parquet. Paginates backward using `startTime`/`endTime` (max 1440 per call). Saves to `data/historical/{symbol}_{timeframe}.parquet`. Deduplicates by timestamp on re-run (idempotent). Parquet schema: time (int64), open/high/low/close/volume (float64). CLI: `--symbol`, `--timeframe`, `--days`. Also importable as `fetch_and_save()`.

**Task 2 — Extract `set_leverage_and_margin()` to `exchange_setup.py`:** Move function and constants from main.py (~32 lines). Reason: main.py should wire components, not make raw API calls. Call site stays identical.

### Decisions recorded
- Public endpoint (no auth) for historical data
- Idempotent design with timestamp deduplication
- main.py: remove function + add `from exchange_setup import set_leverage_and_margin`

### State changes
- 3 files planned: `historical_fetcher.py` (new), `exchange_setup.py` (new), `main.py` (edit)

### Open items recorded
- Verification: pull 5 days BTC-USDT, re-run for dedup test, run main.py in demo mode

### Notes
Context note: Telegram already connected and working. `data_fetcher.py` only maintained 200-bar in-memory buffers before this plan (no persistence).

---

## giggly-nibbling-sunset.md
**Date:** Not explicitly stated
**Type:** Planning

### What happened
Plan to validate and promote dashboard v3.9.3 to production. Investigation revealed the Product Backlog P0.3 entry ("IndentationError at line 1972") was STALE — `py_compile` passes clean on the current v3.9.3 file. The indentation fix was completed at some point after the backlog entry was written.

v3.9.3 changes vs v3.9.2: (1) stale cache fix (`_pd = None` when settings change), (2) sweep symbol persistence across rerenders, (3) selectbox key fix (`sweep_drill_select`), (4) PDF download button (in-browser download).

Steps: (1) runtime validation — user runs streamlit, 7-item test checklist, (2) update 4 doc files if runtime passes (PRODUCT-BACKLOG.md, LIVE-SYSTEM-STATUS.md, DASHBOARD-FILES.md, PROJECT-OVERVIEW.md), (3) add trailing newline to v3.9.3 (missing), (4) ask user before deleting 3 dead fix scripts.

### Decisions recorded
- Backlog entry was stale — not actually blocked
- Do NOT auto-delete old fix scripts — ask user first
- Doc updates deferred until runtime validation passes

### State changes
- v3.9.3 file: 2383 lines, py_compile PASS
- v3.9.2: 2371 lines (current production at time of writing)

### Open items recorded
- User must run 7-item runtime checklist
- 4 doc files to update after runtime passes

### Notes
None.

---

## goofy-dancing-summit.md
**Date:** Not explicitly stated (large file, 83.8KB — could not be read in full)
**Type:** Build specification

### What happened
Complete self-contained build specification for `bingx-live-dashboard-v1-1.py` — a Plotly Dash web app replacing the Streamlit read-only dashboard. This is the spec referenced by `fluttering-kindling-creek.md`. File is 83.8KB and was too large to read in full; findings based on preview and cross-references.

**Core architecture (from preview):**
- Dash 4.0.0, dash-ag-grid 33.3.3, Plotly, port 8051, single-file app
- Single data load point: `dcc.Interval` (60s) → reads state.json, trades.csv, config.yaml → dcc.Store → tab callbacks read from stores only
- 5 tabs: Operational, History, Analytics, Coin Summary, Bot Controls
- BingX API client replicated in dashboard (not imported from bot)
- `COLORS` dict module-level for dark theme
- `server = app.server` at module level for gunicorn
- Data sources: state.json (open positions with symbol/direction/grade/entry/sl/tp/qty/notional/order_id/atr_at_entry/be_raised), trades.csv (closed trades with exit reasons), config.yaml (editable sections)
- VPS: gunicorn on port 8051

Full spec covers all 14 callbacks, tab layouts, position action logic (Raise BE, Move SL), config editor, halt/resume.

### Decisions recorded
- Dash over Streamlit: Streamlit reruns on every click, wipes form state; Dash reactive callbacks preserve state
- Pattern-matching callbacks (MATCH selector) for per-row actions
- `suppress_callback_exceptions=True`
- Self-contained API signing in dashboard

### State changes
- Build spec created (83.8KB, 1795 lines per fluttering-kindling-creek.md reference)

### Open items recorded
- Build execution (per fluttering-kindling-creek.md)

### Notes
File is 83.8KB — largest plan file in this batch. Could not be read fully (output truncated at 2KB preview). Full spec details inferred from cross-references.

---

## groovy-seeking-yao.md
**Date:** 2026-02-28
**Type:** Research / Analysis

### What happened
Research document comparing all TTP (Trailing Take Profit) approaches for the BingX bot. Context: live account ($110, $5 margin × 10x) had 47 trades with 0 TP_HIT exits (46 SL_HIT, 1 EXIT_UNKNOWN). Root cause: `tp_atr_mult: null` set with no trailing TP replacement built. BE raise working but is a floor, not a profit-locker.

**6 TTP examples catalogued (E1-E6):** Fixed ATR TP, ATR Trailing (HTF), AVWAP 3-Stage, AVWAP 2σ + 10-Candle Counter, BingX Native Immediate, BingX Native with Activation.

**5 implementation approaches compared (A-E):**
- A: Fixed TP — 1 config line, 4/47 demo TP rate, misses runners
- B: Native Immediate — ~20 lines, premature exit on noise
- C: Native + Activation at 2×ATR — ~25 lines, exchange-managed after trigger, recommended
- D: AVWAP 2σ + 10-Candle + trailing — ~150 lines, highest risk, correct long-term
- E: Periodic SL Ratchet — ~40 lines, 60s polling gap, good complement

Recommendation: Approach C immediately (activation at 2×ATR, 2% callback), Approach D as future phase.

### Decisions recorded
- Approach C chosen: `TRAILING_STOP_MARKET` with `activationPrice = entry ± atr × 2`, `priceRate = 0.02`
- Fixed TP (A) rejected: wrong exit model, misses trend continuation
- Immediate trailing (B) rejected: fires on noise for small-cap coins
- AVWAP 2σ (D) deferred: 150 lines + AVWAP recalculation = highest risk for live bot
- E (ratchet) as complement, not primary

### State changes
- Research document only — no code written
- Session log planned: `06-CLAUDE-LOGS/2026-02-28-bingx-ttp-research.md`
- INDEX.md update noted as required

### Open items recorded
- Implementation of Approach C pending user decision
- Approach D deferred to future phase

### Notes
This document precedes the three-stage TTP architecture (be_act → ttp_act → ttp_dist) that was eventually built. Approach C is the conceptual precursor to that design.

---

## happy-humming-mccarthy.md
**Date:** 2026-02-18 Session 3
**Type:** Corrective plan / Project restructuring

### What happened
Plan to separate Vince and Vicky projects after discovering the "Vince ML Build" was actually Vicky's architecture (XGBoost classifier, TAKE/SKIP filtering) mislabeled as Vince.

**Part 1 — Create Vicky project folder `PROJECTS/vicky/`:** Move 11 files from four-pillars-backtester (with renames: `train_vince.py` → `train_vicky.py`, `vince_model.py` → `vicky_model.py`). 16 shared infrastructure files stay in four-pillars-backtester.

**Part 2 — Vince correct scope — parameter optimizer:** Vince = parameter sweep engine wrapping existing backtester. Optimizes stochastics (k1-k4, d_smooth, cross/zone levels), EMA clouds (all 3 pairs), AVWAP, SL/TP/BE, entry types. Objective: `net_pnl = gross_pnl - total_commission + total_rebate`. Sweep modes: grid search, Bayesian (Optuna), per-coin, per-tier. Output: `optimal_params.json` per coin. Vince stays in four-pillars-backtester: `scripts/optimize_vince.py` + `ml/parameter_optimizer.py`.

**Part 3 — MEMORY.md updates:** Add persona definitions, correct mislabeled sections.

**Part 4 — cloud3_allows_long/short:** Pre-existing, not introduced by this build; users entering below Cloud 3 flagged as potential backtester fix.

### Decisions recorded
- Vicky = trade classifier/filter, separate PROJECTS/vicky/
- Vince = parameter optimizer, stays in four-pillars-backtester
- No Python execution — all file moves + edits
- Vicky scripts import from four-pillars-backtester via sys.path

### State changes
- `PROJECTS/vicky/` folder structure planned with 11 files moved
- `models/four_pillars/` dir to be removed from backtester
- MEMORY.md update with persona definitions

### Open items recorded
- Execute 7 execution steps (create folder, move files, update imports, rename references, update MEMORY.md, append session log, remove empty dir)

### Notes
This is the Session 3 architectural correction (2026-02-18). `functional-orbiting-rabbit.md` (also 2026-02-18) redefines Vince again as a "relationship research engine" — scope evolved further within the same day. The parameter optimizer definition here and the relationship engine definition there are distinct — likely Session 3 happened before the handoff that became functional-orbiting-rabbit.md.

---

## harmonic-greeting-lemon.md
**Date:** Not explicitly stated (after 2026-02-28 v1-1 user testing)
**Type:** Planning

### What happened
Plan to build BingX Live Dashboard v1-2, addressing 8 issues filed by user after testing v1-1.

**8 issues and fixes:**
- FIX-1: White form inputs → CSS rules for 12 input/select/datepicker element types with dark bg/text/border
- FIX-2: White ag-grid backgrounds → dark CSS for `.ag-root-wrapper`, `.ag-overlay-no-rows-wrapper`, `.ag-header`
- FIX-3: No date range picker → replace `dcc.Checklist(today-filter)` with `dcc.DatePickerRange` on History + Analytics; update CB-8 and CB-9
- FIX-4: Slow tab switching → render all 5 tabs at startup, toggle visibility via `app.clientside_callback()` (pure JS, zero server round-trip)
- FIX-5: No timing diagnostics → `time.time()` markers around each data loader call in CB-1
- ANALYTICS-1: Expand from 7 to 13 metric cards — add net_pnl, Sharpe, maxDD%, avg W/L ratio, SL%/TP%/BE hits/LSG%
- ANALYTICS-3: Remove plotly toolbar (`displayModeBar: False`) + add axis labels

One build script `build_dashboard_v1_2.py` creates 3 files: `assets/dashboard.css` (overwrite, ~95 lines), `bingx-live-dashboard-v1-2.py` (new, ~1750 lines), `scripts/test_dashboard.py` (overwrite). Section-by-section delta table maps v1-1 line ranges to actions.

### Decisions recorded
- FIX-4: clientside callback for tab toggling (pure JS, not server-side)
- `suppress_callback_exceptions=True` kept (CB-5 still creates dynamic IDs)
- Date pickers default to None = no filter = show all trades
- `gross_pnl` kept as alias in `compute_metrics()` for backward compatibility
- Build script uses `.format()` not f-strings (escaped quote rule)
- Sharpe annualized using `math.sqrt(365)`, add `import math`

### State changes
- 3 output files planned
- CB-2 `render_tab` server callback deleted, replaced with clientside callback

### Open items recorded
- Build execution + 4 visual verification checks

### Notes
BE and LSG metrics (ANALYTICS-1) return "N/A" until bot adds `be_raised`/`saw_green` columns to trades.csv — those columns not yet in bot at plan time.

---

## hidden-frolicking-bunny.md
**Date:** References 2026-02-25 in content (log path dated)
**Type:** Planning

### What happened
Plan to fix two outstanding issues before bot restart: M2 (bot.log writing to wrong relative path locations) and UTC+4 logging preference. Context: bot STOPPED, all 67/67 tests passing, all code bugs fixed (E1/A1/M1/SB1/SB2). One signal had fired (GUN-USDT LONG B) but order failed due to E1 (now fixed).

**Fix 1 — M2:** `logging.FileHandler("bot.log")` used cwd — log appeared in `C:\Users\User\bot.log` AND a stale copy in project dir; Run 2 log was unfindable. New `setup_logging()` function: log at `Path(__file__).resolve().parent / "logs" / f"{today}-bot.log"`, creates `logs/` directory at startup.

**Fix 2 — UTC+4:** Custom `UTC4Formatter` class with `formatTime()` outputting `datetime.fromtimestamp(record.created, tz=utc4)`. Extend datetime import with `timedelta, date`.

Both fixes in `main.py` lines 14 (import) and 32-42 (logging setup).

Step 1 Checklist state: E1/A1/M1/SB1/SB2/SB3 checked, 67/67 tests passing, Telegram working, signal pipeline proven. Still pending: M2 fix, UTC+4, bot running continuously, first trade, Telegram entry alert, demo position visible in BingX VST.

### Decisions recorded
- Log file: absolute path to project dir `logs/` subdirectory, dated filename
- Timestamps: UTC+4 via custom Formatter class
- Follows MEMORY.md LOGGING STANDARD: dated file, logs/ dir, dual handler

### State changes
- Plan for 2-line changes to main.py (import extension + setup_logging replacement)

### Open items recorded
- Apply fixes, restart bot, confirm log at correct path with UTC+4 timestamps
- Wait for first trade to complete with E1 fix active

### Notes
M2 was item #8 in the overall Step 1 checklist. GUN-USDT LONG B signal fired in Run 1 but failed due to E1 (json.dumps spaces in order data) — E1 fix was the root cause of order failure.

---

## humble-sauteeing-pelican.md
**Date:** Not explicitly stated
**Type:** Planning

### What happened
Plan for WEEX Futures Screener v1. Context: TradingView Premium CEX screener uses absolute ATR making cross-coin comparison meaningless (BTC at $63k vs RIVER at $0.01 can't share same ATR threshold). This screener uses live WEEX data with normalized ATR and strategy-derived thresholds.

Function: fetch all WEEX perpetual futures symbols, get 300 bars OHLCV per symbol, run `compute_signals_v383`, extract live signal state, display ranked table, sidebar filters, optional auto-refresh.

WEEX API (public, no auth): contracts endpoint, OHLCV candles (`BTCUSDT_SPBL` format), all tickers. Rate limit 500 req/10s; use 0.02s sleep. Symbol format: contract list uses `cmt_btcusdt`, OHLCV uses `BTCUSDT_SPBL`.

ATR ratio threshold from commission math: `(0.001 × 2) / 2.0 × 3 = 0.003` — shown as formula in sidebar.

Screener columns: atr_ratio (normalized, cross-coin comparable), stoch_60, stoch_9, cloud3_dir, price_pos, signal_now, 24h_change_pct, 24h_vol_usd, vol_change_pct.

4 files to build: `utils/weex_fetcher.py`, `utils/weex_screener_engine.py`, `scripts/weex_screener_v1.py` (Streamlit, incremental loop), `tests/test_weex_fetcher.py`.

Reuses `compute_signals_v383` and `DEFAULT_SIGNAL_PARAMS` from existing screener_v1.py. Minimum 69 bars for signal validity.

### Decisions recorded
- Streamlit (not Dash) for screener
- Live signal state only — no backtest
- ATR ratio threshold formula shown in sidebar (not arbitrary number)
- WEEX taker rate defaults to 0.10% — verify actual tier at build time

### State changes
- 4 new files planned (no existing files modified)

### Open items recorded
- Verify futures OHLCV endpoint (spot candles vs separate contract candles)
- Verify WEEX taker rate for user's account
- Verify WHITEWHALE and RIVER appear in results

### Notes
Different from existing `screener_v1.py` (uses local Bybit parquets for backtested eligibility). This screener uses live WEEX API for live signal state detection.

---

## imperative-tumbling-bentley.md
**Date:** Not explicitly stated (v3.8.2 context = ~2026-02-11)
**Type:** Planning

### What happened
Plan for a capital utilization analyzer for v3.8.2 multi-coin backtests. User ran v3.8.2 on BERA (746 trades, -$94 net) and RIVER (881 trades, -$3.48 net) at $250 notional. User wants to know: idle capital, how many coins could run in parallel on $10K, combined P&L with 50% rebate.

One file: `PROJECTS/four-pillars-backtester/scripts/capital_utilization.py`. Inputs: two CSV files from Downloads folder.

Per-coin: build 5-min timeline, count open positions (0-4) per bar, compute max/avg concurrent, % time at each level, margin per bar ($250 × open_positions), peak/avg/idle margin, avg hold time, gross P&L scaled to $5000 notional, commission ($16/RT), rebate (50%), net P&L.

Combined: overlay BERA + RIVER timelines, combined margin per bar, idle capital = $10,000 - peak_combined_margin, max coins = `floor(idle_capital / max_margin_per_coin)`. Output: formatted table with BERA / RIVER / COMBINED columns.

### Decisions recorded
- $5000 notional per position ($250 margin at 20x)
- Commission: $16/RT
- Rebate: 50%

### State changes
- 1 new script planned

### Open items recorded
- User runs: `python scripts/capital_utilization.py`

### Notes
$16/RT commission figure used here. MEMORY.md shows taker rate 0.0008; at $5000 notional: $5000 × 0.0016 = $8.00/RT gross. The $16/RT figure appears inconsistent with current MEMORY.md commission constants — may reflect an older or different commission estimate from early in the project.

---

## CODE VERIFICATION

### elegant-weaving-sutherland.md
Referenced `scripts/build_native_trailing.py` as key deliverable.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_native_trailing.py` — file exists (untracked = newly created, not yet committed)

### enumerated-dazzling-squirrel.md
Referenced commit `"Vault update: BingX v1.5 (time sync, TTP, config tuning), backtester v391, session logs 2026-03-03 to 2026-03-05"`.
- Commit `e85b370` in current git log matches this message exactly — plan was executed.

### fluffy-singing-mango.md
Referenced `ws_listener.py` as new file to build.
- Git status shows `M PROJECTS/bingx-connector/ws_listener.py` (modified) — file exists and was modified. Plan was implemented.

### foamy-soaring-snowflake.md
Referenced `scripts/build_dashboard_v1_5_patch_runtime.py` as new build script.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_dashboard_v1_5_patch_runtime.py` — exists.

### eventual-tickling-stardust.md
Referenced `scripts/build_audit_fixes.py` for backtester and bingx-connector.
- Git status shows `?? PROJECTS/four-pillars-backtester/scripts/build_audit_fixes.py` — exists.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_audit_fixes.py` — exists.


# Batch 19 Findings — Auto-Plans Research
**Files processed:** 20
**Batch:** 19 of 22

---

## joyful-booping-cloud.md
**Date:** Not dated in filename; references "2026-02-13" in backup path
**Type:** Planning

### What happened
Plan for `download_all_available.py` — a script to fill backward and forward OHLCV data gaps for all 399 cached Bybit coins. The existing `download_1year_gap_FIXED.py` skipped coins listed after 2025-02-11. Goal: all 399 coins have all available data from 2025-11-02 (or listing date if later) in both Parquet and CSV format.

### Decisions recorded
- Backup entire cache before any writes: `data/cache_backup_YYYYMMDD_HHMMSS/`
- Six-step sanity gate per symbol before overwriting (row count, no nulls, no duplicates, sorted, extends both ends)
- Fetch both backward and forward gaps in one pass using `_fetch_page()` directly (not `fetch_symbol()` to avoid cache-overwrite side effects)
- Progress tracked in `data/cache/_download_progress.json` for restartability
- Rate limit: 0.05s/page, 1s between symbols, exponential backoff (10-160s)
- CLI flags: `--force`, `--symbols`, `--rate`

### State changes
Plan document created. Script `scripts/download_all_available.py` planned but not yet built (this is a pre-build plan).

### Open items recorded
- Build `scripts/download_all_available.py`
- Verification via `scripts/sanity_check_cache.py` after run

### Notes
None.

---

## kind-discovering-shore.md
**Date:** 2026-03-05
**Type:** Strategy/Analysis document

### What happened
Document titled "Cards on the Table" — a factual breakdown of what the BingX connector bot knows vs what the user knows when trading. Ten cards covering: B trade definition in code (2-of-3 stochs + Cloud 3 gate), A trade definition (all 3 + Stage 2), what the bot has NO concept of (HTF session bias, MTF clouds, sequential K/D, BBW, TDI, structure), why PIPPIN LONG happened on 2026-02-28, version discrepancy (bot runs v3.8.4 not v3.8.6), definition of "perspective" (3-layer HTF system), "nowhere's land", volume generation vs top-tier waiting modes, 6 open questions blocking trend-hold, and what CAN be done without those 6 answers.

### Decisions recorded
- Bot's Cloud 3 gate (`price_pos >= 0`) identified as too crude — cannot distinguish trending vs drifting
- v3.8.4 bot has Stage 2 potentially inactive (config says `require_stage2: true` but v384 defaults to `False` — potential loading bug)
- Entry-side improvements don't require answering the 6 open position management questions

### State changes
Analysis document created. No code changes. PIPPIN LONG root cause documented: bot passed its own weak rules legitimately; rules are incomplete relative to full manual trading system.

### Open items recorded
Six blocking questions (SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1/TP-1) still unanswered.
Four entry-side improvements identified that don't need those answers: perspective layer, B-trade tightening, coin monitoring, sequential K/D check.

### Notes
References `fizzy-humming-crab.md` as source for "perspective" definition. References log line 10667 from `PROJECTS/bingx-connector/logs/2026-02-27-bot.log` for PIPPIN trade details.

---

## kind-yawning-reef.md
**Date:** 2026-02-28
**Type:** Build spec / Research audit

### What happened
Plan for Vince B1 — the FourPillarsPlugin build. B1 is the foundation of Vince v2, making the Four Pillars backtester accessible to all Vince components. Plan includes: full audit of existing `strategies/four_pillars.py` (found to be v1, non-compliant with v2 ABC), identification of 5 issues before the build, and formal specification of all 5 ABC methods to implement.

User override noted: engine version is v385 (overrides build plan's v384 reference). Existing v1 file must be archived as `strategies/four_pillars_v1_archive.py` before rewrite.

Five methods specified: `compute_signals()`, `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document` property.

### Decisions recorded
- Archive existing `strategies/four_pillars.py` as `strategies/four_pillars_v1_archive.py` first (NEVER OVERWRITE rule)
- Use v385 engine (not v384 as build plan specified)
- `compute_signals()` merges enrich + compute into one method, no `params` arg
- Sweepable params: `sl_mult`, `tp_mult`, `be_trigger_atr`, `be_lock_atr`, `cross_level`, `allow_b_trades`, `allow_c_trades`
- `symbol` field added by `run_backtest()` wrapper (not in Trade384)
- B1 scope: ONE file only (`strategies/four_pillars.py`)

### State changes
Build spec document created. Target file planned: `strategies/four_pillars.py` (rewrite). Five issues identified: file conflict, signal version mismatch, v385 exists alongside v384, no `symbol` field in Trade384, date filtering column name unknown.

### Open items recorded
- Confirm which signal version is current (v383_v2.py vs state_machine.py)
- Confirm v384 is still production engine (not v385)
- Confirm parquet timestamp column name for date filtering

### Notes
References skills required: four-pillars, four-pillars-project (Dash NOT needed for B1). Comprehensive verification suite provided (py_compile + 3 smoke tests).

---

## lexical-kindling-rose.md
**Date:** 2026-02-17
**Type:** Planning (log action)

### What happened
Short plan document. User asked whether the Vince ML build exposes the Four Pillars trading strategy and whether it is safe to share. Two explore agents ran a codebase audit. Plan: create a new log file at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-17-vince-ml-strategy-exposure-audit.md` with findings.

### Decisions recorded
- `signals/` directory (10 files): PROPRIETARY — not safe to share
- `ml/` directory (14 files): GENERIC — strategy-agnostic, safe to share
- `build_staging.py`: NOT SAFE — embeds all parameter values
- `dashboard_v391.py`: NOT SAFE — parameter UI reveals settings
- Verdict: Only `ml/` directory is safe for public sharing

### State changes
Plan to write one log file. No code changes.

### Open items recorded
Write the log file and verify contents.

### Notes
This is a very short planning document (action = write one log file with listed content).

---

## linear-wiggling-seal.md
**Date:** 2026-02-14 (references shelved item) / main plan undated
**Type:** Build plan

### What happened
Two-part document: (1) a shelved plan for a cache gap finder, and (2) the main build plan for Dashboard v3.2 — bugfixes and UX improvements from live user testing of v3.1 (1893 lines).

14 bugs/issues documented with root causes and fixes:
- Bug 1: Portfolio DD% shows -207.3% (impossible) — fix: clip at -100%
- Bug 2: Stress test Arrow serialization crash — fix: keep numeric, use Styler
- Bug 3: `use_container_width=True` deprecated (~30 instances) — partial fix
- Bug 4: Portfolio mode has no tabs — DEFERRED to v3.3
- Bug 5: SHIB not in coin list — not a bug, need to download `1000SHIBUSDT`
- Bug 6: Run Backtest button at bottom of sidebar — fix: move to top
- Bug 7: No loading indicator during portfolio backtest — fix: add spinner
- Bug 8: BTC equity curve zigzag — NOT a bug, commission drag expected
- Feature 9: Info tooltips on key metrics — add `help=` param
- Bug 10: ML Filtered vs Unfiltered table Arrow crash — same fix as Bug 2
- Bug 11/12: Grades and TP Impact tables Arrow risk — same pattern fix
- Bug 13: Sweep detail mode missing `"df"` key — add it
- Bug 14: Equity curve x-axis shows bar index not datetime — fix: add datetime x

12 patches (P1-P12) planned for `scripts/build_dashboard_v32.py`.

### Decisions recorded
- Build approach: patch script same pattern as v3.1
- Portfolio tabs (Bug 4) deferred to v3.3 feature
- SHIB: user action (download), not code fix
- BTC zigzag: expected behavior, no code fix
- Equity curve x-axis: use datetime if available, fall back to range index

### State changes
Build plan created for v3.2. Files planned: `scripts/build_dashboard_v32.py`, `scripts/test_dashboard_v32.py`. No files written yet (this is the plan).

### Open items recorded
- User runs `download_all_available.py` for SHIB
- v3.3: portfolio tabs with coin selector dropdown
- Git push after v3.2 patches verified

### Notes
References `joyful-booping-cloud.md` indirectly (download script). Cache gap finder shelved until dashboard v3.2 fully verified.

---

## lively-baking-pumpkin.md
**Date:** 2026-03-03
**Type:** Planning (git operations)

### What happened
Plan for git cleanup: fix `.gitignore` to exclude `.venv312/` and `.bak*` files, then commit the accumulated backlog (all files modified/created since last commit on 2026-02-28 through 2026-03-03). The VSCode Git panel showed "too many active changes" due to `.venv312/` (thousands of files) and 37 `.bak*` files.

### Decisions recorded
- Add to root `.gitignore`: `.venv312/`, `.venv*/`, `venv*/`, `env/`, `.env/`, `bot.pid`, `bot-status.json`, `*.bak.*`, `*.bak.py`, `*.bak.css`, `*.bak.js`
- Plans directory (`06-CLAUDE-LOGS/plans/`) — TRACK in git (commit it)
- Single backlog commit including all bingx-connector, backtester, session logs

### State changes
Plan document created. Execution steps: edit `.gitignore`, verify ignored files removed, `git add` remaining, `git commit`, `git status` verify clean. Commit message specified: "Backlog commit: bingx-connector v1.4, backtester engine updates, session logs 2026-02-28 to 2026-03-03". This matches the actual commit message visible in gitStatus (`914a1b2`).

### Open items recorded
None — straightforward execution plan.

### Notes
This plan corresponds to commit `914a1b2` visible in the gitStatus at the top of the conversation. Execution appears to have been completed.

---

## lively-moseying-nova.md
**Date:** 2026-02-26 (content implies this; no explicit date in doc)
**Type:** Planning (VPS migration guide)

### What happened
Step-by-step guide for migrating the Obsidian Vault to a private GitHub repo and deploying the BingX bot to VPS "Jacky" (76.13.20.191, Ubuntu 24.04, 190GB free, 16GB RAM). Three parts: A (PC git setup), B (VPS setup via SSH), C (ongoing workflow).

Part A: Remove backtester's `.git`, init vault as single repo, create `.gitignore`, stage and commit, push to `S23Web3/Vault`.
Part B: SSH, generate SSH key, clone vault, install Python 3.12 + venv, create `.env`, create systemd service `bingx-bot`, start.
Part C: push from PC, deploy with one SSH command.

### Decisions recorded
- One flat repo for entire vault (backtester `.git` removed)
- No cron — manual push from PC, manual pull + restart on VPS
- Private repo: `S23Web3/Vault`
- Systemd service: `bingx-bot.service`, `Restart=always`, `RestartSec=10`

### State changes
Guide/plan document created. Three helper scripts planned but not yet written: `scripts/migrate_pc.ps1`, `scripts/setup_vps.sh`, `scripts/deploy.ps1`.

### Open items recorded
- All three helper scripts to be created
- VPS `.env` file to be created manually with API keys

### Notes
This is a guide document, not a build spec. Actual migration execution is user-driven. VPS IP 76.13.20.191 mentioned. Architecture diagram shows PC runs ML/data, VPS runs bot 24/7.

---

## logical-coalescing-lark.md
**Date:** 2026-02-27
**Type:** Research / Analysis findings

### What happened
Full findings from analyzing 202 YouTube transcripts from an algo trading channel + FreeCodeCamp ML course, for application to Vince v2 architecture. 14 findings organized into 3 tiers.

TIER 1 (directly applicable now):
1. Unsupervised clustering for Mode 2 auto-discovery (K-means clusters trades by entry-state vectors)
2. Feature importance to prioritize Mode 2 sweep dimensions (XGBoost — stochastics rank highest)
3. RL for exit policy optimization — identified as key missing piece; trains agent on trade lifecycle (state = bars_since_entry + current_pnl_in_atr + k1-k4 + cloud_state + bbw; action = HOLD or EXIT)
4. Random entry + risk management = exits matter more than entries (160% returns with random entry + ATR stop + trailing)

TIER 2 (component-specific):
5. Walk-forward with recent data weighting for Mode 3
6. Survivorship bias caveat for 399-coin dataset
7. Reflexivity: discovered patterns get arbitraged away
8. Held-out partition for Mode 2 patterns (80/20 split)
9. GARCH volatility regime (future scope)
10. LSTM warning: use returns not levels
11. NLP sentiment (future Layer 2)
12-13. Bayesian NN, Transformer attention (future scope)
14. Validated facts: stochastics + RSI consistently top-ranked; ATR stops outperform fixed

Seven updates recommended for Vince v2 concept doc.

### Decisions recorded
- RL Exit Policy Optimizer = new Vince component between Enricher and Dashboard
- Clustering pass added to Mode 2 before permutation sweep
- Feature importance pre-step in Mode 2 (XGBoost on enriched trades)
- Panel 2 (PnL Reversal) build priority made explicit
- Survivorship bias caveat to be added to concept doc
- Vault copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-yt-channel-ml-findings-for-vince.md`

### State changes
Research findings document created. No code written. Vince v2 concept doc updates recommended (not yet applied as of this plan).

### Open items recorded
Apply 7 updates to VINCE-V2-CONCEPT-v2.md.

### Notes
Finding 3 (RL exit policy) is described as "THE MISSING PIECE" — previously not incorporated into Vince architecture. This plan is a companion to or precursor of the vault copy it references.

---

## luminous-churning-sedgewick.md
**Date:** 2026-02-28
**Type:** Research audit / Design decisions

### What happened
B2 research audit for Vince — the API Layer and dataclasses block. Audits what exists vs what needs to be built, identifies 7 bottlenecks (labeled B1-B7 within the doc), and makes 4 design decisions with full rationale.

Bottlenecks identified:
- B1: Plugin arg missing from `run_enricher()` signature
- B2: `EnrichedTrade` — dataclass vs DataFrame decision
- B3: `ConstellationFilter` — typed vs generic dict
- B4: Bar index alignment (entry_bar is relative to filtered slice, not full parquet) — CRITICAL
- B5: `run_enricher` signature incomplete
- B6: MFE bar definition ambiguity (first vs last occurrence of max high)
- B7: `SessionRecord` — what is a session?

Four design decisions resolved:
1. Active plugin: per-call argument (thread-safe, testable, agent-callable) — NOT module-level global
2. EnrichedTradeSet: DataFrame-centric (400k rows × 50 cols = sub-second queries)
3. ConstellationFilter: typed base (direction, outcome, min_mfe_atr, saw_green) + `column_filters: dict`
4. SessionRecord: named research session (uuid, name, timestamps, plugin_name, symbols, date_range, notes, last_filter)

### Decisions recorded
All four design decisions stated as Verdicts (explicitly resolved).

### State changes
Research audit document created. Files planned: `vince/__init__.py`, `vince/types.py`, `vince/api.py`. None yet written at time of plan creation.

### Open items recorded
5 questions listed as "block the build" — but the doc then provides verdicts for items 1-4, so only Q5 (run_enricher signature confirmation) and Q6 (MFE bar definition) appear still open.

### Notes
CRITICAL flag on B4 (bar index alignment): this is a build-blocking issue that affects B1 (FourPillarsPlugin) and B3 (Enricher). The spec file `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` Section 7 is explicitly cited.

---

## majestic-conjuring-meerkat.md
**Date:** 2026-03-03
**Type:** Build spec / Design spec

### What happened
Full CUDA acceleration plan for the Four Pillars sweep engine and Dashboard v394. Covers: Numba CUDA kernel (`engine/cuda_sweep.py`), Numba @njit CPU fallback (`engine/jit_backtest.py`), updated sweep orchestrator (`scripts/sweep_all_coins_v2.py`), and Dashboard v394 (`scripts/dashboard_v394.py`).

Full kernel design: one GPU thread per param combo, 12 read-only signal arrays, param_grid [N_combos, 4], output [N_combos, 9] metrics including Welford online variance for Sharpe. Position state stored in `cuda.local.array`. Entry priority matches engine exactly.

Known simplifications documented: fixed ATR SL only (no AVWAP dynamic), no scale-outs, no ADD entries, reentry as immediate market entry, no rebate in kernel.

Dashboard v394 adds: GPU Sweep tab (heatmap + top-20 table), compiled core checkbox for portfolio mode (ThreadPoolExecutor, workers return plain tuples, no st.* calls), sidebar GPU status panel.

Build script: `scripts/build_cuda_engine.py` creates all 4 files, py_compiles each.

### Decisions recorded
- Numba CUDA (not PyTorch) for kernel — bar-by-bar state machine maps cleanly to threads
- tp_mult sentinel: `999.0` (not `0.0`) for "no TP"
- `notional` and `commission_rate` as scalar kernel args (not per-combo)
- 4 max position slots per thread
- Welford's online variance for Sharpe (no per-trade list in kernel)
- `be_lock_atr=0.0` as fixed constant
- ThreadPoolExecutor: workers return plain tuples, all st.* calls in main thread
- Equity curve bug from v392 fixed in v394: cache invalidation tied to `params_hash`
- Vault log copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-sweep-engine.md`

### State changes
Build spec created. 18 audit issues documented and resolved in this plan revision. Files planned: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/sweep_all_coins_v2.py`, `scripts/dashboard_v394.py`, `scripts/build_cuda_engine.py`. Expected performance: ~400 coins × ~2s GPU = ~13 minutes (vs 6-60 hours current).

### Open items recorded
Verification steps: CUDA check, single-coin sweep, dashboard GPU tab, CUDA fallback test.

### Notes
This is a thorough and audited build spec. The 18 issues were identified and resolved within this plan document itself before handing off to build. This plan corresponds to the session log `2026-03-03-cuda-dashboard-v394-build.md` visible in gitStatus as modified.

---

## mellow-watching-lemon.md
**Date:** 2026-02-28
**Type:** Research audit / Build spec

### What happened
B3 Enricher research audit and scope plan for Vince v2. Full audit of what exists vs what needs to be built for the Enricher component. Eight critical blockers documented with resolutions:

BLOCKER 1: `mfe_bar` not in Trade384 — must add to track which bar MFE occurred (breaking change)
BLOCKER 2: `compute_signals()` signature mismatch (takes `df, params=None` vs `self, ohlcv_df`)
BLOCKER 3: Indicator column naming convention mismatch (`stoch_9` vs `k1_9`)
BLOCKER 4: `diskcache` not installed — pip install needed
BLOCKER 5: Bar index offset — run_backtest() must add slice start offset to all bar indices
BLOCKER 6: OHLC tuple storage format undefined

Six improvements identified: shared Numba ATR, expose raw stoch values, include mfe_bar/mae in trade_schema, FanoutCache size cap (2GB), Enricher as context manager, compliance CLI.

Eight open questions listed.

### Decisions recorded
- Recommendations made: FanoutCache (8 shards, 2GB cap), 4 separate OHLC columns
- Implementation order: position_v384.py → four_pillars_plugin.py → test_plugin → diskcache + cache_config → enricher.py → test_enricher
- `diskcache.FanoutCache` for concurrency (Optuna parallelism)
- Cache key: `{symbol}_{timeframe}_{params_hash}` (MD5 first 8 chars)
- `mfe_bar` is the single most important decision before build starts

### State changes
Research audit document created. Files planned: `strategies/four_pillars_plugin.py` (new — separate from four_pillars.py), `vince/__init__.py`, `vince/enricher.py`, `vince/cache_config.py`, `tests/test_enricher.py`, `tests/test_four_pillars_plugin.py`. Modification planned for `engine/position_v384.py` (add `mfe_bar`).

### Open items recorded
Q1-Q8 listed; some are recommendations, others require user decisions (especially Q1: modify position_v384.py directly vs create v385).

### Notes
This document is STATUS: RESEARCH/AUDIT — not yet scoped for build. Decisions on Q1 (mfe_bar tracking approach) and Q2 (column renaming location) are noted as blocking before build can start.

---

## misty-sniffing-quail.md
**Date:** Approximately 2026-02-09 (references Qwen model, "IMMEDIATE EXECUTION PLAN: Updated 2026-02-09")
**Type:** Build plan / Strategy spec (early-stage)

### What happened
Very large plan document covering: (1) Root cause analysis of Four Pillars v3.7.1 directional filter problem, (2) Solution design for v3.8 in both Pine Script and Python, (3) Vince ML Analysis Pipeline architecture (7-script pipeline), (4) Immediate execution plan using Qwen code generation (overnight run of 20-file generation).

Root cause: B signals bypass Cloud 3 check, Ripster filter OFF by default, two state machines run in parallel with no mutual exclusion.

v3.8 changes: Cloud 3 directional filter (always on), ATR-based BE raise (replaces fixed $2/$4/$6), MFE/MAE tracking, commission updated to 0.08%.

Vince ML pipeline: data_prep → label_generator (Triple Barrier) → xgboost_trainer → parameter_sweep → walk_forward → risk_methods → generate_report.

Immediate execution plan: run `START_GENERATION.bat` overnight to generate 20 Python files via Qwen qwen3-coder:30b model. Six phases over 6 days planned.

### Decisions recorded
- Cloud 3 filter always on (not optional via `i_useRipster`)
- ATR-based BE trigger: 0.5× ATR, lock: 0.3× ATR (as starting values)
- Commission: `strategy.commission.cash_per_order = 8` (Pine Script), `0.08%` (Python)
- Qwen generates boilerplate, Claude reviews/fixes
- GPU acceleration: XGBoost `tree_method='gpu_hist'`, PyTorch CUDA, CuPy arrays

### State changes
Plan document created. Infrastructure (auto_generate_files.py, startup_generation.ps1, START_GENERATION.bat, QWEN-MASTER-PROMPT) already exists per checklist. This is an early-phase plan from around 2026-02-09 — predates later v3.8.4 and Vince v2 architecture.

### Open items recorded
5 open questions for user: Cloud 3 chop zone behavior, B/C signal behavior in fresh open, ATR BE defaults, analysis scope (all coins vs top 20 vs low-price), GPU CUDA version.

### Notes
This plan predates the current Vince v2 architecture (which uses plugin abstraction, not this direct pipeline). The Qwen-generated code was likely the prototype/early version. The final architecture evolved significantly from this plan.

---

## modular-strolling-shamir.md
**Date:** 2026-02-28
**Type:** Session plan / Build schedule

### What happened
Session plan for 2026-02-28 covering two major work streams: BingX Live Trades Dashboard (Block 0) and Vince B1-B6 builds. Establishes token conservation rules: no agents, no speculative searches, Ollama handles boilerplate-only files.

Block 0: BingX dashboard (`PROJECTS/bingx-connector/dashboard.py`) — 6 panels (summary cards, open positions, closed trades, exit breakdown, grade analysis, cumulative PnL). Data sources: `state.json` + `trades.csv`. Auto-refresh 60s. Read-only.

Block 1-6: Vince FourPillarsPlugin → API+Types → Enricher → PnL Reversal data module → Constellation Query Engine → Dash App Shell.

Four files delegated to Ollama: `vince/types.py` (dataclasses), `vince/__init__.py`, `vince/pages/__init__.py`, `vince/assets/style.css`.

### Decisions recorded
- BingX dashboard is read-only (never touch `main.py` or `state_manager.py`)
- No LSG% in BingX dashboard (MFE not tracked by bot — lives in Vince Panel 2)
- Files that must NOT be modified: `strategies/base_v2.py`, `signals/four_pillars_v383_v2.py`, `engine/backtester_v384.py`, `PROJECTS/bingx-connector/main.py`
- `signals/four_pillars.py` and `signals/state_machine.py` modified 2026-02-27 (stage 2 filter) — plugin must wrap CURRENT signal interface

### State changes
Session plan document created. This plan established the agenda for the 2026-02-28 session. Multiple build specs (kind-yawning-reef, luminous-churning-sedgewick, mellow-watching-lemon) correspond to the research done during this session.

### Open items recorded
End state target: BingX dashboard running + Vince app with sidebar + Panel 2 functional.

### Notes
This is a session-level orchestration plan, not a detailed build spec for any single file. References to later plan files (B1=kind-yawning-reef, B2=luminous-churning-sedgewick, B3=mellow-watching-lemon) confirm these were all built in the same session.

---

## moonlit-snuggling-mochi.md
**Date:** 2026-02-28
**Type:** Planning (skill file update)

### What happened
Plan to add Part 4 "Community-Sourced Traps & Patterns" to the Dash skill file (`C:\Users\User\.claude\skills\dash\SKILL.md`). The community audit via WebFetch was blocked by hook; WebSearch was used instead and retrieved 15+ forum threads.

Seven community-sourced findings: extendData + Candlestick traps (stacking ghost artifacts, format strictness, performance cliff at 2500+ bars), dcc.Interval blocking behavior (queue backlog when callback exceeds interval), relayoutData + Candlestick infinite loop risk (GitHub issues #355, #608), ag-grid styleConditions side effects (`Math` unavailable, overrides textAlign), WebSocket vs dcc.Interval (3x faster for <500ms), background callback overhead (only worthwhile >10s; APScheduler + Gunicorn without `--preload` = data corruption risk), candlestick + rangebreaks performance cliff (unusable with >2 years of bars).

### Decisions recorded
- Append Part 4 (~180 lines) to SKILL.md after line 1447
- Update version block to v1.2
- Write vault copy of this plan

### State changes
Plan document created. Skill file to be updated from v1.1 to v1.2 (~1447 → ~1630 lines).

### Open items recorded
Execute the edit to SKILL.md, verify line count growth and section headers.

### Notes
None.

---

## mossy-bubbling-waterfall.md
**Date:** 2026-02-26
**Type:** Planning (git operations)

### What happened
Plan for git push of 170 items (27 modified + ~143 untracked) since initial commit `1e1c49b`. Pre-flight check of what `.gitignore` already handles. Four items flagged for user decision: `*.bak.*` files (9 total, `.gitignore` has `*.bak` but not `*.bak.py`), `.playwright-mcp/`, `.claude/settings.local.json`, and `PROJECTS/yt-transcript-analyzer/output/` (608 generated files).

Commit planned: "Vault update: bingx connector live + dashboards, vince build specs, yt analyzer v2, session logs". This matches commit `0b12d60` in gitStatus.

### Decisions recorded
- Add to `.gitignore`: `.playwright-mcp/`, `.claude/settings.local.json`, `*.bak.*`, `PROJECTS/yt-transcript-analyzer/output/`
- Stage all remaining non-ignored files (`git add .`)
- All 4 categories pushed in single commit

### State changes
Plan document created. Corresponds to commit `0b12d60` visible in gitStatus.

### Open items recorded
Execute: update `.gitignore`, `git add .`, `git commit`, `git push origin main`.

### Notes
This is a straightforward git operations plan. The corresponding commit exists in gitStatus.

---

## peppy-swinging-dusk.md
**Date:** 2026-02-25
**Type:** Audit session / Session log action

### What happened
Full audit of BingX connector against two bug lists: 5-item fault report and 17-item UML bug findings (C01-C08, S01-S08). Plus 3 session bugs fixed during the session (leverage mode, buffer off-by-one, DEFAULT_STATE shallow copy). All findings compiled with status (FIXED / DOC ONLY / OPEN).

Fault Report: F1-F5 — all resolved (FIXED or CLEARED or INFORMATIONAL).
UML Connector Bugs (C01-C08): C01=DOC ONLY, C02-C08=FIXED.
UML Strategy Bugs (S01-S08): S03-S06=DOC ONLY, S07=FIXED, S01/S02/S08=OPEN.

Session bugs fixed: leverage API loop (SB1), buffer off-by-one 200→201 (SB2), DEFAULT_STATE deepcopy (SB3).

Live log analysis: 67/67 tests passing, warmup at 201 bars, no errors, signal engine active returning "No signal" (expected).

### Decisions recorded
- Audit is read-only review — only action is appending findings to existing session log
- Open items flagged for Step 3 (go-live): S08 (multi-slot vs live single-slot P&L mismatch) and S01/S02 (cold-start false signal risk)

### State changes
Audit findings compiled. Session log at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-25-bingx-connector-session.md` to be appended (not overwritten). No code changes needed.

### Open items recorded
- S08: Rerun backtest with `max_positions=1, enable_adds=False, enable_reentry=False` before go-live
- S01/S02: Add `cold_start_bar_count` guard in plugin
- First A/B signal to fire (waiting)

### Notes
Buffer fix (SB2): `ohlcv_buffer_bars: 200` → `201` corrects the trim-to-200 logic that prevented signals from firing. This was previously identified as the root cause of the stuck counter (per MEMORY.md critical lesson).

---

## piped-rolling-blanket.md
**Date:** 2026-02-26
**Type:** Planning / Review + Decision

### What happened
Review of 24-hour demo results on 1m timeframe + plan to switch to 5m + identify production readiness work.

Demo stats: 105 trades opened and closed, 0 errors, 0 crashes, -$354.27 daily P&L, 428 blocked signals ("Too Quiet" ATR filter), ~90% EXIT_UNKNOWN exits.

Critical finding: EXIT_UNKNOWN on ~90% of exits — BingX VST may clean up conditional orders before 60-second monitor check, so exit price uses SL estimate (inaccurate). Fix: query trade history for actual fill price.

Four phases of work planned:
- Phase 1: Config switch (5m), commission rate fix (0.001→0.0008), EXIT_UNKNOWN fix (trade history query)
- Phase 2: Reliability (daily reset on startup, retry with backoff, order validation, graceful shutdown)
- Phase 3: Observability (hourly metrics, Telegram at 50% loss limit)
- Phase 4: Config tuning (after 5m demo 24h+)

### Decisions recorded
- Switch timeframe to 5m (`config.yaml` line 4)
- Fix commission rate: `0.001` → `0.0008` in `position_monitor.py` line 186
- Fix EXIT_UNKNOWN: query `/openApi/swap/v2/trade/allOrders` for actual fill price (P0 fix)
- Warmup stays at 200 bars on 5m (16.7h history at startup)
- Bot stability confirmed SOLID — infrastructure works

### State changes
Plan document created. Five files to modify: `config.yaml` (timeframe), `position_monitor.py` (commission + exit fix + daily reset), `data_fetcher.py` (retry backoff), `executor.py` (order validation), `main.py` (graceful shutdown).

### Open items recorded
All Phase 2-4 work items. First 5m signal to fire after 16.7h warmup.

### Notes
1m was expected to be bad (backtester confirms 5m >> 1m for all low-price coins per MEMORY.md). The -$354 loss is consistent with backtester findings.

---

## purring-herding-manatee.md
**Date:** 2026-02-26
**Type:** Planning (git + VPS deploy)

### What happened
Plan to write the vault-level `.gitignore` (the missing piece from the VPS migration guide in `lively-moseying-nova.md`) and update the bingx-connector `.gitignore`. Bot code described as production-ready (67/67 tests, 20.5h stable run, all fixes applied). Config already switched to 5m.

`.gitignore` content specified: excludes 33GB of data, Books/, postgres/, `.obsidian/`, `.env`, `__pycache__`, `venv/`, `logs/`, ML binaries, parquet/meta files, bot runtime state. Keeps all `.md`, `.py`, `.yaml`, `.json` files.

Timeline after deploy: 0-16.7h warmup (no trades), 16.7h+ signals fire, 40h+ total: run `audit_bot.py`.

### Decisions recorded
- No code changes needed (all paths relative, cross-platform, `Path(__file__).resolve()`)
- Backtester `.git` already removed per migration guide
- Two `.gitignore` files to write: vault-level + bingx-connector level
- VPS deploy: clone → venv → `.env` → systemd `bingx-bot` → start

### State changes
Plan document created for creating two `.gitignore` files. References existing migration guide at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-26-vault-vps-migration.md`.

### Open items recorded
After user executes Parts A, B, C from migration guide: verify bot runs on VPS, after 24h trading run audit_bot.py.

### Notes
This plan is the final missing piece (`.gitignore`) before VPS deployment could proceed. The migration guide referred to is `lively-moseying-nova.md` in this batch.

---

## refactored-imagining-taco.md
**Date:** 2026-02-16
**Type:** Build plan / Feature spec

### What happened
Portfolio enhancement plan for the Four Pillars dashboard — 4 features: (1) reusable portfolio selections (JSON persistence, save/load/compare), (2) PDF export (multi-page reportlab report), (3) enhanced per-coin analysis (10 new metrics + drill-down expander with 5 tabs), (4) unified capital model (post-processing filter approach, two-mode toggle).

Architecture discovery: backtester is NOT a unified portfolio engine — single-coin bottoms-up aggregator; cross-coin capital sharing not implemented. Current capital model already tracks unified position count (not per-coin independent pools as thought). "Money sits idle" confirmed — max capital used can be much less than total allocated.

Feature 4 implementation: Approach 1 recommended (post-processing filter, dashboard-only logic, no engine changes).

### Decisions recorded
- Portfolio JSON storage: `portfolios/*.json` with name, created timestamp, coins, selection_method, params_hash
- PDF library: reportlab + matplotlib
- Unified capital: post-processing filter (not true portfolio engine)
- Auto-save Random N selections with date suffix
- Per-coin drill-down: 5 tabs (Trades, Equity Curve, Trade Distribution, MFE/MAE, Risk Metrics)
- Design document `DASHBOARD-DESIGN.md` to be built after enhancement implementation
- Recommended implementation order: 1→2→3→4

### State changes
Build plan created. Files planned: `utils/portfolio_manager.py`, `utils/pdf_exporter.py`, `portfolios/` directory, `scripts/dashboard.py` (~500 lines of changes). New dependency: `reportlab`.

### Open items recorded
5 open questions for user before Phase 4: capital mode default, entry priority in unified mode, PDF detail level, rejected trades visibility, portfolio comparison feature.

### Notes
This is a 2026-02-16 plan — predates the current v3.8.4/v3.9.x dashboard work. Status of these enhancements is unknown from this document alone.

---

## replicated-scribbling-quokka.md
**Date:** 2026-02-28
**Type:** Planning (skill file update)

### What happened
Plan to add Part 3 "Trading Dashboard Knowledge" to the Dash skill file. The skill had zero trading-specific content. 10 missing knowledge areas identified: candlestick/OHLCV, real-time patterns, panel taxonomy, equity/drawdown charts, multi-chart synchronization, conditional ag-grid coloring, timezone handling, order book, rolling metrics, alert/status indicators.

8 subsections planned for addition: (1) Candlestick charts, (2) Trading dashboard panel taxonomy, (3) Real-time data patterns, (4) Equity curve & drawdown, (5) Multi-chart sync via relayoutData, (6) Conditional formatting in ag-grid, (7) Timezone-aware data in Plotly, (8) Order book/depth chart.

Also: update frontmatter to include trading dashboard keywords, bump version to v1.1.

### Decisions recorded
- Append Part 3 after line ~1054 (before Version History)
- Knowledge-dense, concise format — no large code walls
- Vault copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-dash-skill-trading-dashboard-enrichment.md`
- Version bump to v1.1

### State changes
Plan document created. Skill file (`C:\Users\User\.claude\skills\dash\SKILL.md`) to be modified from 1,064 lines to ~1,254 lines. Note: `moonlit-snuggling-mochi.md` in this batch plans v1.2 (adding community-sourced traps) — these are sequential updates (1.1 then 1.2).

### Open items recorded
Execute edit to SKILL.md, verify 8 subsections present, verify version updated, confirm no existing sections modified.

### Notes
This plan (Part 3, v1.1) must precede `moonlit-snuggling-mochi.md` (Part 4, v1.2). Both were dated 2026-02-28.


# Batch 20 Findings — Auto-Named Plan Files
**Files processed:** 20
**Date generated:** 2026-03-06

---

## rustling-churning-swing.md
**Date:** 2026-02-18
**Type:** Planning

### What happened
Plan for building a Vince Parameter Optimizer using Optuna (Bayesian optimization). Context explains the previous session mislabeled a trade filter/meta-labeling tool as "Vince." This plan corrects the scope: Vince is a rebate farmer that finds optimal parameter combinations to maximize trades and rebate income — NOT reduce trade count. The plan covers sweeping 26 parameters (16 signal + 10 backtester) across coins using the existing `compute_signals_v383()` + `Backtester384.run()` pipeline. Objective functions: `net_pnl_after_rebate` (default), `sharpe`, `risk_adjusted`. Supports walk-forward validation (expanding window, WFE rating), parameter importance analysis (fANOVA + SHAP), and multiple CLI flags.

### Decisions recorded
- Vince = Optuna parameter optimizer, NOT a trade filter
- Trade filtering/meta-labeling/bet sizing explicitly excluded
- Pruning: trials with < 10 trades pruned
- No dashboard integration (future scope)
- `pip install optuna` required before running
- 26 swept parameters with constraints enforced at sampling time

### State changes
Plan written. Files scoped:
- `scripts/build_optimize_vince.py` (build script)
- `ml/parameter_optimizer.py` (~400 lines)
- `scripts/optimize_vince.py` (CLI)
- `tests/test_parameter_optimizer.py`

### Open items recorded
- Build not yet executed (plan only)
- Dashboard integration deferred to future scope
- `sweep_all_coins_v2.py` not mentioned here (different context)

### Notes
This is a corrective plan explicitly addressing a prior session error where trade filtering was built instead of parameter optimization.

---

## serene-puzzling-squirrel.md
**Date:** Not explicitly stated in file (context references 2026-02-12 sweep)
**Type:** Planning

### What happened
Plan to verify all 16 coins in config.yaml are actively tradeable on BingX perpetual futures before restarting the bot. The backtester sweep ran on historical CSVs — some meme coins (PIPPIN, GIGGLE, FOLKS, STBL, SKR, UB, Q, NAORIS, ELSA) may not be listed. Solution: build a standalone `scripts/verify_coins.py` script that hits the public BingX contracts endpoint and checks each configured coin.

### Decisions recorded
- Script does NOT auto-edit config.yaml — outputs a clean list for user to review and apply manually
- Uses live BingX API (`https://open-api.bingx.com`), NOT VST
- Follows pattern of `scripts/test_connection.py`
- No test file needed — it's a utility script

### State changes
Plan created. One new file scoped:
- `scripts/verify_coins.py` (~80 lines)

### Open items recorded
- Bot restart pending until coins verified
- After successful run: mark COUNTDOWN-TO-LIVE.md step 3 done
- First signal expected 201 bars × 1m = ~3.4 hour warmup after restart

### Notes
None.

---

## shimmying-spinning-wozniak.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to fix 10 usability problems discovered during the first real run of the YT Transcript Analyzer (211 videos, 201 transcripts, 50+ min summarize stage). Problems include: no cancel, invisible progress (detail_text overwrites itself), no output preview, no output folder control, channels mix together, slow summarize with no opt-out, no ETA, no resume awareness, no re-run without re-download, and no download button.

Solution: major rewrite of `gui.py` plus changes to `fetcher.py`, `summarizer.py`, and `config.py`. Changes include: per-channel output directories, settings panel in sidebar, skip-summarize toggle, subprocess handle exposure for cancel, extended summarizer callback with result dict + `already_done` count, scrollable activity log container, clickable video list, ETA display, resume awareness, re-run without re-download checkbox, download button for report.

### Decisions recorded
- Per-channel dirs implemented via dynamic config globals override (simpler than refactoring all modules)
- Cancel via `proc.terminate()` in Streamlit `on_click` callback
- Skip-summarize forces the "no Ollama" code path
- Settings not persisted to `.env` — session-level only

### State changes
Files scoped for modification:
- `gui.py` (major rewrite)
- `fetcher.py` (on_process_started callback)
- `summarizer.py` (extended callback + already_done)
- `config.py` (get_channel_paths helper)

### Open items recorded
- Build not executed (plan only)
- 7 verification tests listed

### Notes
None.

---

## sleepy-plotting-bengio.md
**Date:** 2026-03-02
**Type:** Planning

### What happened
Plan for BingX Dashboard v1-3 Patches 6 and 7. Context: Patch 5 applied class-based dark CSS but Dash 2.x injects CSS variables into `:root` that override class rules — specifically `--Dash-Fill-Inverse-Strong: #fff` causes white backgrounds on date pickers and dropdowns. Class-level `!important` cannot override CSS variables; must override at `:root`.

Patch 6: CSS-only fix appending `:root` variable overrides to `assets/dashboard.css` with guard check and timestamped backup.
Patch 7: Bot status feed in Operational tab — adds `write_bot_status()` helper to `main.py` (atomic JSON write), `progress_callback` param to `data_fetcher.py` warmup, and 2 new callbacks + UI panel to `bingx-live-dashboard-v1-3.py`. Bot status polled every 5s from `bot-status.json`.

### Decisions recorded
- Atomic write: `tmp = status_path.with_suffix(".tmp")` → `os.replace(tmp, status_path)`
- Progress callback fires every 5 symbols (not every symbol)
- Status feed shows last 20 messages, newest first
- `dcc.Store(id='store-bot-status')` + `dcc.Interval(interval=5000)` pattern

### State changes
Two build scripts scoped:
- `scripts/build_dashboard_v1_3_patch6.py`
- `scripts/build_dashboard_v1_3_patch7.py`
Files modified: `assets/dashboard.css`, `bingx-live-dashboard-v1-3.py`, `main.py`, `data_fetcher.py`

### Open items recorded
- Build not executed (plan only)

### Notes
References session log `2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md`.

---

## snuggly-mixing-moon.md
**Date:** ~2026-03-02 (references "previous session built four_pillars_v386.py")
**Type:** Planning

### What happened
B1 plan: wrap Four Pillars backtester behind the Vince v2 `StrategyPlugin` ABC. The existing `strategies/four_pillars.py` is a v1 class that inherits from the wrong base and is missing 4 of 5 required methods. Plan: archive current v1, write new `FourPillarsPlugin(StrategyPlugin)` class. Build script creates archive, writes new class, runs 4 inline smoke tests. Key design: import alias `_compute_signals_fn` to avoid shadowing the class method. Param routing: pass ALL params to both signal pipeline and Backtester385 via `.get()` with defaults. Data path from `config.yaml → data.cache_dir`.

### Decisions recorded
- Strategy document property returns `Path` to `docs/FOUR-PILLARS-STRATEGY-v386.md`
- `run_backtest()` writes trades to `results/trades_b1_{timestamp}.csv`
- No Dash, PostgreSQL, Optuna, Enricher, RL/LLM, or pytest — all out of scope
- 4 smoke tests: syntax, interface, compute_signals, strategy_document

### State changes
Files scoped:
- `strategies/four_pillars.py` (archive → rewrite)
- `strategies/four_pillars_v1_archive.py` (new)
- `scripts/build_b1_plugin.py` (new)

### Open items recorded
- Post-build memory updates listed: session log, INDEX.md, PRODUCT-BACKLOG.md (B1 DONE, B2 READY), TOPIC-vince-v2.md

### Notes
Part of Vince v2 build series (B1-B6). B1 is prerequisite for Enricher, Optimizer, Dash shell.

---

## sparkling-doodling-hare.md
**Date:** 2026-03-05
**Type:** Planning (dual content: current plan + superseded earlier plan)

### What happened
Plan has two distinct sections:

**Current (top):** Add a "Load v384 Live Preset" button to `dashboard_v394.py` so it can be pre-configured to exactly match the live bot's signal logic. Two params missing from dashboard UI: `require_stage2` and `rot_level`. Plan: add new checkbox + slider, add preset button that sets all session_state keys. Build via `scripts/build_dashboard_v395.py` (reads v394, patches via safe_replace, writes v395). Also: scan yesterday's 11,466-line bot log for errors, create today's session log.

**Superseded (below "SUPERSEDED" marker):** Earlier plan for BingX Dashboard v1.4/v1.5 scope. Lists confirmed bugs (BUG-1 through BUG-9) with root causes. Contains 4 phases: Phase 1 (diagnostic scripts), Phase 2 (bot core fixes), Phase 3 (dashboard v1.5), Phase 4 (beta bot). This is a large plan covering TTP close fix, trade chart popup, beta bot at $5 20x, etc. Phase 1 scripts: run_error_audit.py, run_variable_web.py, run_ttp_audit.py, run_ticker_collector.py, run_demo_order_verify.py, run_trade_analysis.py.

### Decisions recorded
- `require_stage2` default=False (preserve existing behaviour), `rot_level` range 50-100 default 80
- v394 untouched, v395 is new file
- Beta bot: MUBARAK-USDT and SAHARA-USDT overlap with live bot — remove from beta
- 11 safe user beta coins confirmed

### State changes
Files scoped:
- `scripts/build_dashboard_v395.py` (CREATE)
- `scripts/dashboard_v395.py` (CREATE from build)
- Session logs to append/create

### Open items recorded
- Bot log scan pending
- Dashboard v395 build pending

### Notes
File contains superseded content from an earlier session merged into the same plan file. The superseded content represents the comprehensive v1.4/v1.5 + beta bot planning that was done in a prior session.

---

## sprightly-chasing-meteor.md
**Date:** 2026-02-25
**Type:** Planning / Audit

### What happened
Full audit of BingX connector beyond the 2026-02-24 fault report. Four areas:
1. New bugs (CRITICAL: C1-C4, HIGH: H1-H5, MEDIUM: M1-M5, LOW: L1-L2)
2. ccxt/bingx-python tips applied
3. Bot health/status visibility (status_writer.py + status.json schema)
4. Dashboard labeling (events.jsonl + enriched trades.csv + Telegram structured prefix)

Critical bugs: C1 — plugin config never passed to constructor (all config silently ignored); C2 — PnL direction wrong for SHORT; C3 — all closes assumed SL exits (exit price always sl_price); C4 — daemon threads die silently. New files: `status_writer.py`, `event_logger.py`, `rate_limiter.py`. Complete status.json schema documented (16 fields including threads, coins per-symbol, risk gates, positions). Structured Telegram prefix format `[MODE|STRATEGY|GRADE|EVENT_TYPE]`. New events.jsonl with 7 event types.

### Decisions recorded
- Implementation order: C1 first (highest value), then C2+C3 together, then H1, then Area 3, Area 4, Area 2, C4, H2-H5+M1-M5
- 67/67 tests must remain passing throughout all changes
- TIP-04 (WebSocket streaming) deferred

### State changes
3 new files + 8 modified files scoped. Plan document only — no build executed.

### Open items recorded
- All bugs remain open at time of plan creation
- Verification: tests must stay 67/67 throughout

### Notes
This is the comprehensive audit plan for the BingX connector post-demo-mode discovery phase.

---

## starry-hugging-elephant.md
**Date:** 2026-03-05
**Type:** Planning

### What happened
Plan for BingX Trade Analyzer v2. Context: bot has been running ~1 day (2026-03-04 17:52 to 2026-03-05 13:24+), 49 trades at $50 notional. The existing `run_trade_analysis.py` works but has issues: no column padding, terminal output too sparse, missing analysis dimensions, date filter hardcoded.

Build: one build script (`build_trade_analyzer_v2.py`) creates `run_trade_analysis_v2.py`. Analyzer v2 adds: CLI flags (--from/--to/--days/--no-api), 3 output formats (terminal, markdown, CSV), 10 analysis sections (summary stats, ASCII equity curve, symbol leaderboard, direction split, grade split, exit reason split, hold time, TTP performance, BE effectiveness, per-trade detail table). Fixed-width padded tables.

Critical build hazards documented: CSV schema mismatch (12-col header vs 18-col newer rows), f-string escape trap, division-by-zero guards, API failure handling.

### Decisions recorded
- `pd.read_csv(..., names=FULL_COLUMNS, header=0, on_bad_lines='warn')` for schema mismatch
- `--no-api` uses ttp_extreme_pct from CSV as MFE proxy
- 0.3s sleep between API calls
- Commission rate 0.0008 hardcoded in analyzer

### State changes
2 new files scoped:
- `scripts/build_trade_analyzer_v2.py`
- `scripts/run_trade_analysis_v2.py`

### Open items recorded
- 5 test scenarios listed
- Build not executed (plan only)

### Notes
None.

---

## synchronous-conjuring-shell.md
**Date:** Not explicitly stated (context: bot has had 8+ bugs, references E1-ROOT signature bug)
**Type:** Planning

### What happened
Plan for a BingX API Lifecycle Test Script — a 9-step sequential test that exercises the entire trade lifecycle against BingX VST in ~15 seconds. Motivation: each bug requires fix + restart + 30+ min wait for a real signal. The existing `test_connection.py` only tests read-only endpoints. Step 5 (place order with SL) is identified as the critical test that catches the E1-ROOT signature encoding bug where JSON special chars in stopLoss param are URL-encoded before signing.

9 steps: auth check, public endpoints, leverage+margin, quantity calc, place order with SL, verify position, close position, verify closed, fetch order details.

### Decisions recorded
- Imports `BingXAuth` directly, NOT `Executor` (avoids StateManager/Notifier coupling)
- Minimum viable quantity (~$0.02 notional) to conserve demo balance
- Logs to `logs/YYYY-MM-DD-lifecycle-test.log`
- On failure: prints full request URL + full response body
- Default coin: RIVER-USDT, override with `--coin`

### State changes
One new file scoped:
- `scripts/test_api_lifecycle.py`

### Open items recorded
- Build not executed (plan only)

### Notes
This plan explains the context for the lifecycle test that appears in subsequent session logs.

---

## synthetic-mapping-ember.md
**Date:** 2026-03-03
**Type:** Planning (session handover)

### What happened
CUDA Dashboard v394 session handover document. Notes that an earlier vault plan (`2026-03-03-cuda-sweep-engine.md`) had 4 pre-audit errors — this document contains the CORRECTED architecture. Key corrections: 12 signal arrays (not 10), param grid shape [N_combos, 4] (not 5), tp_mult sentinel is 999.0 (not 0.0), notional is a scalar kernel arg (not per-combo). The kernel uses Welford's online variance for Sharpe computation (no per-trade list in GPU memory), `cuda.local.array` for position state. v393 had IndentationError — base from v392 not v393. `sweep_all_coins_v2.py` deferred.

Engine architecture documented: CUDA kernel (one thread per param combo), CPU-compiled `jit_backtest.py` with Numba @njit, dashboard v394 with GPU Sweep mode + JIT portfolio path + sidebar GPU panel.

### Decisions recorded
- 12 signal arrays in kernel: close/high/low/atr, long_a/b/short_a/b, reentry_long/short, cloud3_ok_long/short
- Param grid: [sl_mult, tp_mult_or_999, be_trigger_atr, cooldown] — 2,112 combos default
- GPU thread model: one thread = one param combo
- Known kernel simplifications: fixed ATR SL only, no AVWAP, no scale-outs, no ADD entries
- Build only 3 files this session (not sweep_all_coins_v2.py)

### State changes
Files to be created by `scripts/build_cuda_engine.py`:
- `engine/cuda_sweep.py`
- `engine/jit_backtest.py`
- `scripts/dashboard_v394.py`

### Open items recorded
- Build script to be executed in new chat
- Post-build: update TOPIC-backtester.md, TOPIC-dashboard.md, LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md

### Notes
This document explicitly supersedes the earlier vault plan `2026-03-03-cuda-sweep-engine.md`.

---

## temporal-brewing-sky.md
**Date:** 2026-02-25
**Type:** Planning (multi-section: current + archived step plan + full pipeline scope)

### What happened
Three distinct sections in one file:

**Section 1 (Current):** Fix leverage Hedge mode bug in `main.py`. Bot running on BingX VST. `set_leverage_and_margin()` sends `side=BOTH` — BingX Hedge mode requires `side=LONG` and `side=SHORT` separately. Fix: replace single request with loop over ("LONG", "SHORT") per symbol.

**Section 2 (Archived — COMPLETE):** Step 1 Build Plan. Fix 1: `_round_down` test used assertEqual, should be assertAlmostEqual. Fix 2: test_integration.py missing price mock. Fix 3: config.yaml plugin switch from `mock_strategy` to `four_pillars_v384`. All 67 tests must pass.

**Section 3 (Full Pipeline Scope):** Scopes everything from coin discovery to live trades: Build 1 (BingX Screener with bingx_screener_fetcher.py, screener_engine.py, coin_ranker.py, live_screener_v1.py), Build 2 (main.py active_coins.json reader), Build 3 (config.yaml update), Build 4 (fix 2 failing tests). Also: Ollama scorer (qwen3:8b) for visual audit. Path to first demo trade = 1 session. Path to live with dynamic coins = 2-3 sessions.

### Decisions recorded
- Leverage fix: two requests per symbol (LONG + SHORT)
- main.py: active_coins.json takes priority over config.yaml coins on startup, no dynamic reload during runtime
- Ollama scorer fires on startup sweep and delta changes only, does NOT affect active_coins.json content
- Path to first demo trade: just fix 2 tests + edit config (no screener needed)

### State changes
This is a multi-session plan file. Step 1 is marked COMPLETE. Full pipeline is the ongoing scope.

### Open items recorded
- Leverage fix pending at time of writing
- Screener builds pending
- 67/67 tests needed before switching demo_mode: false

### Notes
This plan spans from the initial Step 1 completion state through the full live trading pipeline scope.

---

## temporal-nibbling-mist.md
**Date:** Not explicitly stated
**Type:** Planning

### What happened
Plan to add ML Analysis Tabs to the existing dashboard (`scripts/dashboard.py`, 526 lines). All ml/ modules are built and tested (8/8 pass). Current dashboard has no tabs — single view with test/single/batch modes. Plan: add `st.tabs()` with 5 tabs. Tab 1 (Overview): existing KPIs, equity curve, grade/exit breakdowns. Tab 2 (Trade Analysis): full trade table, P&L histogram. Tab 3 (MFE/MAE & Losers): MFE/MAE scatter + loser_analysis module. Tab 4 (ML Meta-Label): XGBoost meta-labeling, SHAP importance, bet sizing comparison. Tab 5 (Validation): purged CV, walk-forward validation. Sidebar: ML params (estimators, depth, threshold).

### Decisions recorded
- Delivered as a single Write to `scripts/dashboard.py` (no separate build script — single file edit)
- Test script: `scripts/test_dashboard_ml.py` (no Streamlit required)
- ML threshold slider inline controls what gets filtered in Tab 4

### State changes
One file modified, one test file created (plan only).

### Open items recorded
- Build not executed

### Notes
References an early version of the dashboard (526 lines) before the v38x/v39x numbering era.

---

## temporal-swinging-grove.md
**Date:** Not explicitly stated (context: lifecycle test steps 1-4 pass, step 5 failed due to E2-STOPPRICE bug)
**Type:** Planning

### What happened
Plan to install Playwright MCP, crawl and document the BingX v3 API docs (JS-rendered, unreadable by WebFetch), cross-reference API calls against documented specs, and complete the lifecycle test. Steps: install Playwright MCP (`claude mcp add playwright npx @playwright/mcp@latest`), crawl docs, save to `PROJECTS/bingx-connector/docs/BINGX-API-V3-REFERENCE.md`, fix build script (remove `str()` wrapper on sl_price/tp_price at lines 954 and 961), re-run lifecycle test, restart bot once 15/15 pass.

### Decisions recorded
- Fix is in `build_bingx_connector.py` lines 954/961 — remove `str()` wrapper
- Post-fix: restart bot once all 15 steps pass

### State changes
Files to be created/modified:
- `docs/BINGX-API-V3-REFERENCE.md` (create)
- `build_bingx_connector.py` (patch lines 954/961)

### Open items recorded
- Playwright MCP not yet installed at time of plan
- Steps 6-15 of lifecycle test not yet verified
- Session log to append: `2026-02-25-lifecycle-test-session.md`

### Notes
Context: the E2-STOPPRICE bug was found and fixed in executor.py but not yet re-tested. This plan bridges the debug session to re-verification.

---

## twinkly-popping-summit.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan to analyze all 196 closed trades from `trades.csv` in phase-segmented format before going live with a $110 account. Existing `audit_bot.py` treats all trades as a flat dataset — meaningless since 3 phases have very different notionals ($500/$1500/$50). Build new `scripts/analyze_trades.py` focused on phase-segmented trade performance analysis.

Phase detection: by notional_usd (500.0 = Phase 1, 1500.0 = Phase 2, 50.0 = Phase 3). Phase 1 (103 trades, 1m, broken exit tracking) flagged as UNRELIABLE. Phase 2 (47 trades, 5m, $1500) and Phase 3 (46 trades, 5m, $50) are the primary analysis targets. Report sections: dataset overview, Phase 1 flagged, Phase 2 deep dive, Phase 3 deep dive, combined signal quality, key findings (auto-generated plain English). Uses stdlib only (csv, datetime, pathlib, collections).

### Decisions recorded
- New script serves different purpose than `audit_bot.py` — both kept
- stdlib only, no pandas
- Phase detection by notional_usd value
- Phase 1 explicitly flagged UNRELIABLE in all outputs
- Report auto-generates "Is Grade A outperforming Grade B?" style findings

### State changes
One new file scoped:
- `scripts/analyze_trades.py`
Report output: `06-CLAUDE-LOGS/2026-02-28-bingx-trade-analysis.md`

### Open items recorded
- Build not executed (plan only)
- Verification: trade count must be 103+47+46=196

### Notes
None.

---

## twinkly-wibbling-puzzle.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to create a comprehensive Dash Super-Skill for Vince v2 dashboard development. Context: Vince v2 requires a Plotly Dash application (8-panel research dashboard replacing Streamlit). The constellation query builder (Panel 3) requires pattern-matching callbacks (MATCH/ALL) — the most complex Dash pattern.

Deliverables: new skill file `C:\Users\User\.claude\skills\dash\SKILL.md` (~900 lines), vault copy, CLAUDE.md update adding mandatory Dash skill load rule. Skill covers: multi-page app (register_page/pages folder), pattern-matching callbacks with full WRONG/CORRECT/TRAP callouts, dcc.Store hierarchy, background long-running callbacks (Enricher + Optimizer), dash_ag_grid, ML model serving, PostgreSQL connection pooling, production gunicorn config. Key traps documented: string/dict IDs cannot mix, dots in dict ID values cause parse errors, ALLSMALLER only valid when MATCH in Output, DataFrame cannot be stored directly in dcc.Store.

### Decisions recorded
- Dash version: 4.0.0 (released 2026-02-03)
- dash-ag-grid version: 33.3.3
- Vince MUST use multi-page (pages/ folder) — 8 panels = separate page files
- `@callback` decorator (not `app.callback`) in Dash 4.0
- `DiskcacheLongCallbackManager` for dev, `CeleryLongCallbackManager` for production
- Store pattern: store session_id in dcc.Store, look up enriched trades from diskcache by key

### State changes
Files to be created/modified:
- `C:\Users\User\.claude\skills\dash\SKILL.md` (CREATE)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-dash-vince-skill-creation.md` (vault copy)
- `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` (EDIT — append Dash skill mandatory rule)

### Open items recorded
- Skill file build not yet executed
- CLAUDE.md update pending

### Notes
This plan is for the skill itself; CLAUDE.md now has the DASH SKILL MANDATORY rule as a result of this work.

---

## typed-wandering-tome.md
**Date:** Not explicitly stated (references v3.9.1, v3.9.2 era)
**Type:** Planning

### What happened
Dashboard v3.9.1 plan addressing two portfolio mode calculation errors. Root causes: (1) SL/TP/scale-out exits charge taker (0.08%) instead of maker (0.02%) — 4x overcharge; (2) Scale-out trades treated as separate positions — one position with 2 scale-outs creates 3 Trade384 records, capital model treats each as needing $500 margin = $1500 per position; (3) Double margin deduction; (4) Inconsistent baselines (N*10k vs pool balance vs deposit).

7 bugs documented (E1, C1-C2, D1-D7). Solution: direct engine fix (3 lines in backtester_v384.py, maker=True at lines 144/174/407), build script creating `capital_model_v2.py` (position grouping by entry_bar + exchange-model pool balance tracking), `dashboard_v391.py` (12 patches), `pdf_exporter_v2.py`.

Pool balance tracking: separate `balance` (realized cash) from `margin_used` (locked capital). Available = balance - margin_used. No double deduction.

### Decisions recorded
- Engine fix: direct Edit tool (not in build script)
- Position grouping key: `(coin, entry_bar)` collapses scale-out records
- Rebased equity: `rebased_chart_eq = adjusted_portfolio_eq - engine_baseline + total_capital`
- `scale_idx=0` hardcoded for SL/TP/END closes — grouping by entry_bar handles all cases

### State changes
Files:
- `engine/backtester_v384.py` (direct edit — 3 lines)
- `utils/capital_model_v2.py` (create via build script)
- `scripts/dashboard_v391.py` (create via build script from v39 base)
- `utils/pdf_exporter_v2.py` (create via build script)

### Open items recorded
- Build not executed (plan only)
- 5 verification scenarios listed

### Notes
This corrects the broken portfolio Mode 2 (Shared Pool) that showed Pool P&L = -$9,513 while per-coin sum = +$4,656.

---

## vast-enchanting-petal.md
**Date:** 2026-03-04
**Type:** Scoping / Strategy analysis

### What happened
Scoping document reviewing all Four Pillars strategy versions to understand why v386 is the correct baseline and what needs to change. Written after v391 build failed (built from spec without user confirming rules). Documents the "LSG problem" (85-92% of trades see green but exit at a loss) that every version since v3.5 tries to solve.

Version history table: v3.5.1 (cloud trail — bled out), v3.6 (AVWAP SL — bled out), v3.7 (rebate farming — barely viable), v3.7.1 (phantom trade fix), v3.8 (cloud 3 filter + ATR BE raise — best result: RIVER +$18,952), v3.8.3 (D-signal drag), v3.8.4 (optional per-coin ATR TP), v3.8.6 (stage 2 conviction filter, C disabled — LIVE).

ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0 spec documented in detail (3-phase system + hard close). What v386 has vs what should exist: entry signals correct, Phase 1/2/3 NOT implemented, Cloud 2 hard close NOT implemented, Cloud 4 NOT computed.

Why v391 failed: built from spec without user confirming whether spec accurately represents their position management on charts. Spec may be incomplete relative to actual user behavior.

### Decisions recorded
- v386 entry signals: correct, keep as-is
- Initial SL: 2.0×ATR, TP: 4.0×ATR (per spec)
- Next build: user must confirm each phase rule before coding
- Existing v391 files (clouds_v391.py, four_pillars_v391.py, position_v391.py, backtester_v391.py, build_strategy_v391.py) exist and are syntactically clean but rules unverified

### State changes
Scoping document only — no code changes.

### Open items recorded
- 5 unverified spec details listed (Phase 1 anchor, Phase 2 amount, Phase 3 exit, hard close trigger, ADD midline threshold)
- Fundamental question: Does ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0 accurately describe user's position management?

### Notes
Explicitly notes v391 was built without user rule confirmation — process problem, not code problem. This is the "cards on the table" clarification document before next build attempt.

---

## vast-skipping-crown.md
**Date:** 2026-02-25
**Type:** Planning

### What happened
Vault organization plan to address 5 areas of organizational debt: MEMORY.md at 215 lines (exceeds 200 hard limit, content being truncated), 24+ session logs with no index, DASHBOARD-FILES.md 9 days stale (shows v3.8.4 production when v3.9.2 is live), PRODUCT-BACKLOG.md missing BingX/WEEX/Vince items, and no single system status doc.

5 build steps: (1) MEMORY.md refactoring — split into index + 7 topic files (TOPIC-backtester.md, TOPIC-commission-rules.md, TOPIC-bbw-pipeline.md, TOPIC-bingx-connector.md, TOPIC-vince-v2.md, TOPIC-dashboard.md, TOPIC-critical-lessons.md); (2) Create INDEX.md for session logs; (3) Update DASHBOARD-FILES.md (v3.9.2 as production, v3.9.3 BLOCKED); (4) Reconcile PRODUCT-BACKLOG.md; (5) Create LIVE-SYSTEM-STATUS.md (new file, system status table).

### Decisions recorded
- TOPIC-commission-rules.md was planned but later merged into TOPIC-engine-and-capital.md (not visible in this document)
- LIVE-SYSTEM-STATUS.md to be created as a new file

### State changes
Plan for pure documentation work — zero code, zero risk. All write/edit operations on markdown files.

### Open items recorded
- Execution awaiting user approval at time of plan creation

### Notes
This is the genesis plan for the memory/topic file architecture now in use. Plan appears to have been executed (MEMORY.md topic files, INDEX.md, LIVE-SYSTEM-STATUS.md all exist in the vault).

---

## warm-waddling-wren.md
**Date:** 2026-02-07
**Type:** Master plan

### What happened
Four Pillars Trading System master execution plan (earliest strategic document in the set). 5 workstreams + 9 checkpoints. Context: v3.7.1 is marginally profitable at $1.81/trade expectancy. 86% of losers saw green — signal quality is fine, exit timing is bottleneck. Commission rebate changes math significantly: 70% account = $10.21/trade expectancy net of rebates.

WS1: Pine Script skill optimization (fix commission from $4→$6/side, add phantom trade bug, cooldown gate pattern). WS2: Progress review documents. WS3A: WEEX data pipeline (standalone fetcher, restartable, 1m candles). WS3B: Signal engine port from Pine to Python. WS3C: Backtest engine. WS3D: Additional exit strategies (cloud_trail, avwap_trail, phased). WS3E: Streamlit GUI extension. WS4: ML Parameter Optimizer (grid search → Optuna → PyTorch/XGBoost regime model). WS5: Stable v4 strategy + Monte Carlo validation.

CUDA setup instructions. WEEX API documented. Data size table (1 coin 24h → 500 coins 3 months). Breakeven+$2 raise identified as key optimization target.

### Decisions recorded
- Commission: raw $6/side (0.06%), NOT $4 — MEMORY.md was wrong and must be reverted
- Rebate settles daily at 5pm UTC
- Serial fetch per coin (not parallel) due to rate limits
- Target: 500 coins, 3 months, ~$450MB parquet cache
- Monte Carlo: 3 validation tests (trade reshuffling, parameter perturbation, trade skip)

### State changes
Master plan document only. Defines the entire project trajectory from early February 2026. Many of the builds scoped here have since been completed.

### Open items recorded
- At time of writing: all WS1-WS5 pending
- Since this is a historical master plan, most items are now complete

### Notes
This is the foundational master plan document. Commission figure confirmed as $6/side (later corrected to 0.08% taker but this captures the original planning context). The plan prompt at bottom is for use in new chat sessions to execute the plan.

---

## wise-juggling-dragonfly.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to build two BingX automation tools using existing code patterns. Context: BingX demo validated. Bot trades but no feedback loop — can't see live signal state across 47 coins, performance review requires manual CSV reads.

Tool 1: `screener/bingx_screener.py` — headless loop fetching klines for all 47 coins every 60s, runs `FourPillarsV384.get_signal(df)`, fires Telegram on fresh A/B signals. Dedup via `last_alerted = {symbol: bar_ts}` dict. Uses live BingX API (public klines, no auth). Imports from both bingx-connector and four-pillars-backtester via sys.path inserts.

Tool 2: `scripts/daily_report.py` — reads trades.csv, filters to today's UTC date, computes P&L/win rate/best/worst, sends via Notifier. Configurable as Task Scheduler job at 21:00 local (17:00 UTC = rebate settlement time).

### Decisions recorded
- Live API (not VST) for klines — klines are public, no auth
- 60s poll interval (sufficient for 5m bars)
- Column rename required before plugin: `time → timestamp`, `volume → base_vol`
- Task Scheduler command included

### State changes
Two new files scoped:
- `screener/bingx_screener.py`
- `scripts/daily_report.py`

### Open items recorded
- Build not executed (plan only)
- WEEX screener stays in backlog

### Notes
Both tools use 2-parallel-agent delivery model per the plan header. Critical rules section references MEMORY.md hard rules (no escaped quotes in f-strings, dual logging, full paths).


# Batch 21 Findings — Auto-Plans Research

**Batch:** 21 of 22
**Files processed:** 5
**Date processed:** 2026-03-06

---

## witty-giggling-galaxy.md
**Date:** Referenced as around 2026-02-23 (log reference at end of file)
**Type:** Planning / Bug Fix Plan

### What happened
Detailed plan for fixing a session state cache bug in Dashboard v3.9.2 (Portfolio Analysis mode). The bug caused equity curves to display from a previous date range instead of the currently selected custom date range. Investigation identified the root cause as Streamlit session state not being cleared when settings change — the hash mismatch check at line 1963 only showed a warning but did not clear stale data or stop rendering. A critical audit revision was performed: the original plan included `st.stop()` which was found to create a blank-page UX, so the corrected approach uses `_pd = None` to allow existing `if _pd is not None:` guards to naturally skip all rendering.

### Decisions recorded
- Use Option 2 (hash mismatch → clear cache) NOT Option 1 (date-range-only check)
- Do NOT use `st.stop()` — use `_pd = None` instead, letting existing guards skip rendering
- Create `dashboard_v393.py` as new file (NEVER overwrite v392)
- Build via `build_dashboard_v393.py` script
- Base the build on reading v392 content and replacing the 2-line warning block

### State changes
- Plan created for dashboard v3.9.3 fix
- Build script path defined: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v393.py`
- Output path: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v393.py`
- Exact old/new code blocks specified in plan

### Open items recorded
- Run verification: 4-step test scenario (fresh session, change date range, re-run, regression test)
- Syntax check with py_compile mandatory
- Update MEMORY.md after successful build
- Log session to `06-CLAUDE-LOGS/2026-02-23-dashboard-v393-bug-fix.md`

### Notes
- Plan contains an internal contradiction: the Summary section still says "Fix: Clear `st.session_state["portfolio_data"]` and call `st.stop()`" while the Implementation Plan section correctly removes `st.stop()`. The Implementation Plan section is the authoritative corrected version.
- CODE VERIFICATION: Glob check needed for dashboard_v393.py.

---

## witty-wiggling-forest.md
**Date:** Not explicitly dated in file content
**Type:** Planning / Pine Script Fix Plan

### What happened
Plan to fix commission blow-up in Pine Script strategy v3.7. With commission OFF, v3.7 shows 222 trades and +$4,480 (+44.81%). With commission ON (0.06%), the account blows up. Root cause identified as phantom trades from `strategy.close_all()` + `strategy.entry()` on the same bar creating double-commission events with $0 P&L, plus rapid flipping with no cooldown amplifying the damage. Six changes were specified.

### Decisions recorded
1. Switch to `cash_per_order` commission: $6/side — deterministic, not ambiguous with leverage
2. Remove all 4 `strategy.close_all()` calls from flip logic (lines 287, 300, 312, 324)
3. Cancel stale exit orders before flips using `strategy.cancel()`
4. Add cooldown input `i_cooldown` (default 3 bars) between entries
5. Add `cooldownOK` bool gate to all 8 entry conditions
6. Add commission tracker row to dashboard table (update table from 12 to 13 rows)

### State changes
- Plan created for Pine Script v3.7 commission fix
- File to modify: `c:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\four_pillars_v3_7_strategy.pine`
- Specific line numbers called out: 12-17 (commission), 287/300/312/324 (close_all), 45 (cooldown input), 269 (cooldown gate), 474 (dashboard row)

### Open items recorded
- Verification steps: Load on TradingView with 1000PEPEUSDT.P 5min, verify no phantom trades, verify single trades for flips, verify no entries within 3 bars, verify "Comm$" row in dashboard

### Notes
- Commission value in plan is $6/side (not $8 as in some other references). MEMORY.md states: "70% account = $4.80/RT net, 50% account = $8.00/RT net" and "$6 entry + $6 exit" — consistent with $6/side in this plan.
- This plan is for Pine Script (TradingView), not Python backtester.

---

## zany-foraging-blum.md
**Date:** Audit notes reference 2026-02-27
**Type:** Planning / Build Plan (Web Scraper)

### What happened
Detailed plan to scrape the BingX API documentation site (`https://bingx-api.github.io/docs-v3/#/en/info`) into a single indexed markdown reference document. The existing manual reference covers only 11 endpoints; the full site has approximately 215 leaf endpoint pages across 8 top-level sections. Plan uses Playwright (headless Chromium) to handle the JS-rendered SPA. Full architecture specified: `BingXDocsScraper` class and `MarkdownCompiler` class. CLI arguments defined (`--output`, `--section`, `--test`, `--debug`, `--timeout`). Audit notes added 2026-02-27 with 6 critical fixes.

### Decisions recorded
- Use Playwright async headless Chromium (not requests/BeautifulSoup — site is JS-rendered SPA)
- Script location: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py`
- Test suite: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_scraper.py`
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-COMPLETE-REFERENCE.md`
- Save intermediate results every 20 pages to `.scrape-progress.json` for crash recovery
- Audit fix 1: Non-endpoint pages (Intro, Change Logs) need fallback to `main.innerText`
- Audit fix 2: WebSocket pages need different extraction path
- Audit fix 3: Python tab click must happen OUTSIDE `page.evaluate()` via Playwright API
- Audit fix 4: Use text-based selectors not index-based (indices go stale after SPA navigation)
- Audit fix 5: Follow all mandatory project rules (docstrings, py_compile, timestamps, etc.)
- Audit fix 6: `--output` default must be absolute path via `pathlib.Path(__file__).resolve()`

### State changes
- Plan created for BingX API docs scraper
- Plan vault copy reference: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-bingx-api-docs-scraper.md`
- Two Python files to create (scraper + test suite)
- One output markdown document to generate (~215 endpoints)

### Open items recorded
- Run test mode first (3 pages), then single section (Swap ~69 endpoints), then full scrape (~215)
- Validate output: TOC present, 3 random endpoint spot checks, no empty sections in log
- py_compile both .py files (mandatory)
- Run test_scraper.py (4 tests: nav tree, single page, markdown compile, full section)

### Notes
- This plan references Playwright MCP tools as a prerequisite ("user now has Playwright MCP tools available") — script depends on Playwright being installed.
- CODE VERIFICATION: Glob check needed for `scrape_bingx_docs.py`.

---

## zazzy-bouncing-boot.md
**Date:** 2026-02-19 (explicitly stated)
**Type:** Planning / Architecture Scope Session

### What happened
Comprehensive build plan for Vince v2 — the ML strategy optimizer/analyst for the Four Pillars trading system. This document combined a session log from a scope-only session (2026-02-19) with a full architectural build plan. The scope session established that Vince RUNS THE BACKTESTER HIMSELF (not passive CSV reader), learns from statistical frequency (not ML model weights), logs all runs with timestamps, and operates in three modes: user query, auto-discovery, and settings optimizer. Fixed constants identified (stochastic periods, cloud EMAs). Six-module architecture defined with strict build order.

### Decisions recorded
- Vince has 3 operating modes: (1) User constellation query, (2) Auto-discovery sweep, (3) Settings optimizer
- Fixed constants Vince NEVER sweeps: K1=9, K2=14, K3=40, K4=60 (Kurisko); Cloud EMAs 5/12, 34/50, 72/89
- Vince can sweep: TP mult (0.5-5.0), SL mult (1.0-4.0), cross_level, zone_level, allow_b/c, cloud3 gate, BE trigger, checkpoint_interval, sigma_floor_atr
- Core principle: "Vince reads. User changes." — strategy rule changes made by user, not Vince
- No PyTorch/GPU in MVP — pandas + numpy sufficient for 90K trades (deferred to v2.1 for 400 coins)
- No price charts in output — user reads indicators only
- Rebate constraint non-negotiable: win rate improvement cannot come at cost of volume
- RE-ENTRY wrongly programmed — Vince will expose this, fix deferred
- B/C trade logic may need full rewrite — Vince shows data, user rewrites rules
- 5 panels: Coin Scorecard, LSG Anatomy, Constellation Query Builder, Exit State Analysis, Validation
- 6 modules in strict build order: schema.py → enricher.py → analyzer.py → sampling.py → report.py → dashboard_tab.py
- Deliverable 0 (first output before any code): `docs/vince/VINCE-PROJECT.md`
- Session was at 70-75% context — note to open new chat

### State changes
- Scope session completed 2026-02-19 — no code built yet
- Architecture fully locked in plan
- All file paths defined for 6 modules + tests + build script
- Constellation query dimensions fully specified (static, volatility, dynamic, trade filters, outcome filters)
- Data flow diagram documented

### Open items recorded
- All code to be built (this was scope-only session)
- Verification steps defined: build script run, enricher tests, analyzer tests, smoke test on RIVERUSDT, dashboard integration
- Dashboard integration: add Vince tab to dashboard_v392 via patch in build_dashboard_v392.py

### Notes
- Plan references `Backtester384` and `signals/four_pillars_v383.py` as existing — these are reused not recreated.
- Plan references `compute_signals_v383` but MEMORY.md shows current version is v3.8.4. Discrepancy: plan may predate v3.8.4.
- Dashboard integration targets dashboard_v392 — but dashboard_v393 build plan also exists (witty-giggling-galaxy.md). Version alignment may need checking at build time.

---

## zazzy-wibbling-pudding.md
**Date:** 2026-02-27 (explicitly stated in file)
**Type:** Planning / Documentation Build Plan

### What happened
Plan to create a single cross-project master overview file (`PROJECT-OVERVIEW.md`) in the vault root. The vault had 27 UML/diagram files but all were intra-project. This plan addresses the missing cross-project oversight view showing all 4 active projects, their status, inter-project connections, current blockers, and immediate next actions. The plan was created after a high-output day (6 sessions across 3 projects on 2026-02-27).

### Decisions recorded
- Create one new file: `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md`
- No existing files modified
- File contains: master Mermaid graph, status legend, today's output summary, active blockers table, next actions table
- Also save plan copy to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-project-overview-diagram.md`
- Append row to INDEX.md

### State changes
- Plan created for PROJECT-OVERVIEW.md
- Mermaid diagram design fully specified in plan (5 subgraphs: INFRA, BACKTESTER, VINCE, BINGX, YT)
- Status as of 2026-02-27 captured in diagram nodes:
  - Dashboard v3.9.2 PRODUCTION, v3.9.3 BLOCKED (IndentationError)
  - BBW Pipeline L1-L5 COMPLETE
  - BingX Bot DEMO VALIDATED (5m, 47 coins), go-live WAITING on funds transfer
  - BingX Live Screener and Daily P&L Report BUILT 2026-02-27
  - BingX API Docs (215 endpoints) SCRAPED 2026-02-27
  - Vince: Concept LOCKED, Plugin Interface Spec v1 DONE, base_v2.py stub DONE
  - YT Analyzer GUI v2.1 BUILT 2026-02-27, CodeTradingCafe run COMPLETE (201 videos, 50min)

### Open items recorded
- Verify mermaid renders in Obsidian
- Confirm inter-project arrows accurate against LIVE-SYSTEM-STATUS.md
- Confirm blockers table matches PRODUCT-BACKLOG.md P0 section

### Notes
- Dashboard v3.9.3 is noted as "BLOCKED - IndentationError" in the diagram — this matches context from other logs about the dashboard build having a syntax error.
- This plan's diagram shows BingX API Docs as "SCRAPED 2026-02-27" — the scraper plan (zany-foraging-blum.md) was also from 2026-02-27, suggesting they were from the same session day.
- CODE VERIFICATION: Not applicable — this plan produces a markdown file, not Python.



---

# RESEARCH SYNTHESIS — Four Pillars Trading System

Generated: 2026-03-06
Source: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-FINDINGS.md` (21 research batches, 140+ session logs, ~8600 lines)

---

## 1. What is the project goal?

Build a complete algorithmic trading system around the **Four Pillars** strategy — from Pine Script indicators on TradingView, through a Python backtester for multi-coin parameter optimization, to a live trading bot on BingX, supported by an ML research engine (Vince) and comprehensive dashboards.

The strategy combines four signal components:
- **Ripster EMA Clouds** (Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89, Cloud 5: 180/200)
- **AVWAP** (Anchored VWAP, Brian Shannon methodology)
- **Quad Rotation Stochastics** (Kurisko Raw K: 9-3 entry, 14-3 confirm, 40-3 divergence, 60-10 macro)
- **BBWP** (Bollinger Band Width Percentile — volatility filter)

Signal grading: **A** = Quad (4/4 stochs aligned), **B** = Rotation (3/4 stochs), **C** = ADD (engine label for position additions, not a standalone signal type).

The end-state vision: backtest across 399 crypto coins, identify optimal parameters per coin, deploy live via BingX with automated entries/exits, and use ML to surface trade-quality patterns that humans miss.

---

## 2. Current state of each major component

### Four Pillars Backtester

- **Current version**: v3.8.4 (stable production). Codebase: 142,935 lines across the project.
- **Location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
- **Capabilities**: Multi-coin batch backtesting, 399 coins supported, CSV data pipeline, PostgreSQL storage (vince database, port 5433), commission modeling (0.08%/side taker on notional).
- **Dashboard versions**: v3.9.0 through v3.9.4 were Streamlit-based dashboards built on top of v3.8.4 engine. v3.9.4 added CUDA GPU sweep (Numba @cuda.jit on RTX 3060) for parameter optimization. These are dashboard/UI layers — the core engine remains v3.8.4.
- **Data**: 5-minute OHLCV CSVs for 399 coins stored locally. 1-minute data also available but backtests confirmed 5m > 1m for all low-price coins.
- **Key findings from backtests**: LSG (Losing-but-Scored-Good) rate 85-92% — most losers were profitable at some point, making TP/ML filtering the key lever. Tight TP (< 2.0 ATR) destroys value on most coins. Always backtest, never trust MFE alone.

### BingX Live Bot

- **Location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\`
- **Status**: LIVE on real account ($110 margin). Running on VPS Jacky (76.13.20.191).
- **Version**: v1.5 (as of 2026-03-05).
- **Architecture**: HMAC-SHA256 authentication, hedge mode perpetual futures, WebSocket listener for real-time data, REST API for order management.
- **Features built**: TTP engine (Trailing Take Profit), breakeven raise logic, position sizing from config, multi-coin support, time-sync fix (server timestamp delta), dashboard (Plotly Dash).
- **Bugs fixed during live deployment**:
  - `reduceOnly` parameter error on close orders (Feb 26-27)
  - Timestamp sync drift causing 401 auth failures (fixed with server time delta)
  - Breakeven price calculation error (was using entry instead of accounting for commission)
  - Buffer stuck at 200/201 — trim logic was cutting buffer back to 200 after every fetch, signals could never fire (cost 2+ hours to diagnose)
  - Position side mismatch in hedge mode
- **Config**: Coins, margin, leverage all configurable. Commission: 0.08% taker, 70% rebate account = $4.80/RT net.
- **Dashboard**: BingX dashboard built on Plotly Dash, shows positions, PnL, trade history. Separate from backtester dashboard.

### Vince ML Pipeline (B1-B6)

- **Concept**: Vince v2 is a **Trade Research Engine** (NOT a classifier). It surfaces patterns in trade data that humans can then use to refine strategy rules.
- **Status**: Concept APPROVED 2026-02-27. B2 (API layer) built. B1 (Phase 0 strategy alignment) BLOCKED. B3-B6 blocked on B1.
- **Build phases defined**:
  - **B1**: Phase 0 — Strategy alignment, feature engineering, data pipeline from backtester to ML
  - **B2**: API layer — FastAPI endpoints for serving model predictions (BUILT)
  - **B3**: Feature enrichment — Technical indicator features beyond raw OHLCV
  - **B4**: Model training pipeline — PyTorch on CUDA (RTX 3060, 12GB VRAM)
  - **B5**: Evaluation framework — Walk-forward validation, out-of-sample testing
  - **B6**: Dashboard integration — Plotly Dash 4.0 multi-page app, 8-panel research UI
  - **B7-B10**: Defined but distant (optimizer, constellation builder, production serving, monitoring)
- **B1 blocker**: Phase 0 requires deciding exactly which features to extract and how to align backtester output with ML input. This is a strategy decision, not a code decision — needs user input on what trade attributes matter most.
- **Tech stack decided**: Plotly Dash 4.0 (NOT Streamlit), PyTorch (NOT sklearn for production), PostgreSQL for storage, Ollama (qwen3:8b) for local LLM features.
- **Screener v1**: WEEX screener scoped as part of Vince ecosystem. Separate from main ML pipeline.

### Pine Script Indicators

- **Versions built**: v3.4 through v3.8, all Pine Script v6 on TradingView.
- **v3.4**: Initial Four Pillars indicator with Ripster Clouds + AVWAP + basic stochastics.
- **v3.5**: Added quad stochastic rotation. **Regression found**: stochastic smoothing was accidentally changed from Raw K (smooth=1) to smoothed, which altered signal behavior. Fixed in later version.
- **v3.6**: Commission-aware strategy with `strategy.commission.cash_per_order` (value=8). Fixed the `commission.percent` ambiguity with leverage.
- **v3.7**: **Commission bug discovered** — was double-counting or miscalculating commission in certain flip scenarios. `strategy.close_all()` causes phantom double-commission trades. Rule established: never use `strategy.close_all()` for flips.
- **v3.8**: Stable indicator version with all fixes applied. Used as reference for Python backtester parity checks.
- **Key lesson**: Pine Script and Python backtester must produce identical signals for the same data. Any divergence means one has a bug. Pine v3.5 stochastic regression was caught by comparing Pine vs Python outputs.

### Infrastructure

- **VPS Jacky**: 76.13.20.191. Runs BingX bot. VST (Visual Studio Tunnel) blocked — cannot use for remote dev.
- **GitHub**: S23Web3/ni9htw4lker (identity: S23Web3, malik@shortcut23.com). Also S23Web3/Vault for the Obsidian vault.
- **PostgreSQL**: PG16, port 5433, user=postgres, pw=admin. Database: vince. Tables: backtest_runs, backtest_trades, equity_snapshots, live_trades, commission_settlements.
- **Ollama**: Local LLM server at port 11434. Model: qwen3:8b (4.9GB, fits entirely in 12GB VRAM on RTX 3060).
- **Hardware**: NVIDIA RTX 3060 12GB VRAM, 32GB RAM, AMD Ryzen 7 5800X. CUDA-capable for Numba GPU sweeps and PyTorch training.
- **Python environment**: Local Windows 11 Pro. Bash shell available (Git Bash). Dependencies managed per-project.

---

## 3. What is the primary blocker right now?

**Vince B1 (Phase 0 — Strategy Alignment)** is the critical-path blocker for the ML pipeline. Everything from B3 through B10 depends on B1 defining the feature set and data alignment. B2 (API layer) was built ahead of B1 as infrastructure prep, but the ML pipeline cannot produce meaningful results until B1 is resolved.

For the BingX bot, the primary blocker is **signal quality verification** — the bot is live but needs more runtime data to confirm that the Python-generated signals match expected behavior on live markets. The buffer-stuck-at-200 bug demonstrated that subtle data pipeline issues can silently prevent signals from ever firing.

For the backtester, there is no blocker — v3.8.4 is stable and functional. The CUDA GPU sweep (v3.9.4) works but is a dashboard/optimization layer, not a core engine change.

---

## 4. What decisions are locked?

| Decision | Status | Date Locked | Context |
|----------|--------|-------------|---------|
| Commission rate: 0.08% (0.0008) taker per side on notional | LOCKED | 2026-02 | Derived from exchange fee schedule. Never hardcode dollar amounts. |
| Commission Pine Script: `strategy.commission.cash_per_order` value=8 | LOCKED | 2026-02 | `commission.percent` is ambiguous with leverage. Cash per order is unambiguous. |
| Never use `strategy.close_all()` for flips | LOCKED | 2026-02 | Causes phantom double-commission trades. |
| Stochastic settings (Kurisko Raw K): 9-3, 14-3, 40-3, 60-10, all smooth=1 | LOCKED | 2026-01 | John Kurisko methodology. Raw K (smooth=1) is non-negotiable. |
| Ripster Cloud numbering: C2=5/12, C3=34/50, C4=72/89, C5=180/200 | LOCKED | 2026-01 | Standard Ripster EMA Cloud settings. |
| 5m timeframe > 1m for all low-price coins | LOCKED | 2026-02 | Backtested across all 399 coins. Every low-price coin profitable on 5m, most negative on 1m. |
| Tight TP (< 2.0 ATR) destroys value | LOCKED | 2026-02 | Backtested. Always backtest TP levels, never trust MFE alone. |
| Vince v2 = Trade Research Engine, NOT classifier | LOCKED | 2026-02-27 | Concept approved by user. Surfaces patterns, does not make binary predictions. |
| Vince UI = Plotly Dash 4.0 (NOT Streamlit) | LOCKED | 2026-02 | Streamlit dashboard versions (v3.9.x) were transitional. Production UI is Dash. |
| Signal grading: A=Quad(4/4), B=Rotation(3/4), C=ADD(engine label) | LOCKED | 2026-02 | C is not a signal type — it's a position addition label. |
| PostgreSQL port 5433, database=vince | LOCKED | 2026-02 | PG16 installation uses non-default port. |
| BingX hedge mode for perpetual futures | LOCKED | 2026-02 | Required for simultaneous long/short capability. |
| Rebate: 70% account=$4.80/RT net, 50% account=$8.00/RT net | LOCKED | 2026-02 | Settle daily 5pm UTC. |
| Python backtester stable at v3.8.4 | LOCKED | 2026-02 | v3.9.x versions are dashboard layers on top of v3.8.4 engine. |
| Logging standard: dated files, dual handler, TimedRotatingFileHandler | LOCKED | 2026-02 | Non-negotiable for all projects. If it's not logged, it didn't happen. |

---

## 5. What decisions are still open?

| Decision | Status | Context |
|----------|--------|---------|
| Vince B1 feature set — which trade attributes to extract | OPEN | Needs user input. Strategy decision, not code decision. Determines entire ML pipeline direction. |
| Walk-forward validation window sizes for ML | OPEN | Part of B5 evaluation framework. Depends on B1 feature decisions. |
| Which coins to run live on BingX beyond initial test set | OPEN | Bot is live but coin selection for scaling up not finalized. |
| TTP (Trailing Take Profit) optimal parameters per coin | OPEN | TTP engine built in bot, but optimal trailing distances need more live data. |
| Whether to use Ollama/qwen3:8b for feature extraction or just for analysis | OPEN | Model available locally, but its role in the ML pipeline not yet defined. |
| CUDA GPU sweep — production use vs experimental | OPEN | v3.9.4 built it, works on RTX 3060, but unclear if it's the standard optimization path or one-off. |
| VPS scaling — single Jacky instance vs multi-VPS | OPEN | Currently single VPS. Scaling plan not defined. |
| BBW Simulator integration with live trading signals | OPEN | Pipeline complete (layers 1-5), but whether/how it feeds into live bot decisions not decided. |
| Screener architecture — standalone vs Vince-integrated | OPEN | WEEX screener scoped but implementation path relative to Vince not locked. |
| Position sizing model for live trading | OPEN | Bot uses config-based sizing. Dynamic sizing based on signal grade/volatility not yet designed. |

---

## 6. What has been confirmed working?

### Four Pillars Backtester
- v3.8.4 engine: runs full backtests across 399 coins on 5m data
- CSV data pipeline: loads, validates, and processes 5m OHLCV data
- Commission modeling: 0.08%/side on notional, correctly calculated
- PostgreSQL integration: backtest_runs, backtest_trades, equity_snapshots all populate correctly
- Batch mode: can run all 399 coins sequentially
- Signal generation: A/B grading produces expected entries matching Pine Script v3.8

### BingX Bot
- HMAC-SHA256 authentication with server time delta sync
- Order placement (market orders, limit orders) in hedge mode
- Position opening and closing with correct side handling
- TTP engine (trailing take profit) — logic implemented and running
- Breakeven raise — triggers correctly after threshold
- WebSocket connection for real-time data feed
- Dashboard (Plotly Dash) showing positions and PnL
- Runs stable on VPS Jacky for multi-day periods
- Logging with timestamps, dated log files, dual handler

### BBW Simulator Pipeline
- Layer 1: BBWP calculation from raw Bollinger Band Width
- Layer 2: Sequence detection (consecutive bars above/below thresholds)
- Layer 3: Forward return calculation after sequence events
- Layer 4: Simulator engine combining BBWP sequences with returns
- Layer 5: Monte Carlo simulation for confidence intervals
- V2 corrections applied (specific calculation fixes)
- Declared COMPLETE 2026-02-17

### Pine Script
- v3.8 indicator: Ripster Clouds + AVWAP + Quad Stochastics + BBWP overlay
- Commission via `cash_per_order` method (unambiguous with leverage)
- Signal parity with Python backtester confirmed at v3.8 level

### Infrastructure
- PostgreSQL PG16 on port 5433: stable, all tables created and populated
- Ollama qwen3:8b: loads fully into GPU VRAM, responds at port 11434
- GitHub repos: S23Web3/ni9htw4lker and S23Web3/Vault both active
- RTX 3060 CUDA: Numba GPU kernels execute correctly for parameter sweeps

---

## 7. What has been built but is unverified or untested?

### Four Pillars Backtester
- **v3.9.4 CUDA GPU sweep**: Built and runs, but not validated against CPU results for numerical parity. Unknown if GPU sweep produces identical optimal parameters to CPU brute force.
- **Streamlit dashboard versions (v3.9.0-v3.9.3)**: Built as UI layers, but superseded by Dash plans. Unclear if any are still runnable or if dependencies drifted.

### BingX Bot
- **Multi-coin simultaneous live trading**: Bot supports multiple coins in config, but most live testing has been single-coin or limited sets. Concurrent position management across many coins not stress-tested.
- **Rebate settlement tracking**: Commission settlements table exists in PostgreSQL, but automated reconciliation of daily 5pm UTC rebate deposits not verified against actual exchange settlements.
- **Error recovery after VPS restart**: Bot restarts and reconnects, but whether it correctly detects and resumes open positions after unexpected crash/restart not formally tested.

### Vince ML Pipeline
- **B2 API layer (FastAPI)**: Built but has no upstream data (B1 not done) and no downstream consumer. Endpoints exist but serve no trained model.

### BBW Simulator
- **Layer 6 (Report generation)**: Referenced in pipeline design but completion status ambiguous — layers 1-5 confirmed complete, layer 6 (report/visualization) may be partial.
- **Integration with backtester**: BBW pipeline runs standalone. Whether its output correctly feeds back into backtester signal filtering not tested end-to-end.

### Pine Script
- **v3.6 and v3.7 intermediate versions**: Built and iterated on, but with known bugs (commission issues in v3.7, smoothing regression in v3.5). These versions exist in TradingView but should not be used — only v3.8 is validated.

---

## 8. What has been planned but never executed?

### Four Pillars Backtester
- **Dynamic position sizing based on signal grade**: Discussed (A trades get more margin than B trades) but never implemented. Current system uses fixed sizing.
- **Walk-forward optimization**: Mentioned as necessary for preventing overfitting but no implementation exists.
- **Multi-timeframe backtesting**: 5m is the standard, 1m was tested and rejected, but 15m/1h timeframes never backtested.

### BingX Bot
- **Automated coin rotation**: Concept of dynamically switching which coins the bot trades based on backtester rankings — discussed but no implementation.
- **Risk management circuit breaker**: Auto-stop trading after N consecutive losses or X% daily drawdown — mentioned but not built.
- **Multi-exchange support**: BingX is the only exchange. No work toward Bybit, OKX, or other exchange connectors.

### Vince ML Pipeline
- **B3 (Feature enrichment)**: Defined in build plan, depends on B1, never started.
- **B4 (Model training pipeline)**: PyTorch on CUDA, defined but never started.
- **B5 (Evaluation framework)**: Walk-forward validation, defined but never started.
- **B6 (Dashboard integration)**: 8-panel Dash UI, extensively scoped and designed (panel taxonomy defined, page structure planned), but no code written.
- **B7-B10**: Optimizer, constellation builder, production serving, monitoring — defined at concept level only.
- **Phase 0 strategy alignment (B1)**: The most critical planned-but-unexecuted item. Everything downstream depends on it.

### Pine Script
- **v3.9+ indicator versions**: No Pine Script development beyond v3.8. All development effort shifted to Python backtester and bot.
- **Alert-to-bot webhook pipeline**: TradingView alerts triggering BingX bot via n8n webhook — discussed conceptually but never built. Bot uses its own signal generation instead of Pine Script alerts.

### Infrastructure
- **Multi-VPS deployment**: Only VPS Jacky exists. No scaling or redundancy plan executed.
- **Automated backup/restore**: PostgreSQL backups not automated. No disaster recovery tested.
- **CI/CD pipeline**: No automated testing, deployment, or integration pipeline. All deployments are manual.
- **n8n workflow automation**: n8n mentioned for TradingView-to-bot webhooks but no workflows built or deployed.
- **Monitoring/alerting**: No system health monitoring beyond manual log review. No PagerDuty, no Slack alerts, no automated health checks.

---

## Summary

The Four Pillars system has a **working backtester** (v3.8.4), a **live bot** (BingX v1.5 on real money), and a **complete volatility pipeline** (BBW layers 1-5). Pine Script indicators are stable at v3.8. Infrastructure (PostgreSQL, Ollama, CUDA, VPS) is operational.

The critical gap is the **ML pipeline** — Vince B1 (strategy alignment / feature engineering) remains unstarted, blocking all downstream ML work (B3-B10). B2 (API layer) was built proactively but serves nothing until B1 defines what data flows through it.

Secondary gaps: no automated risk management in the live bot, no walk-forward validation in the backtester, no CI/CD or monitoring infrastructure.

The system is in a state where **manual trading with backtester-informed parameters works**, but the vision of **ML-enhanced automated trading with dynamic optimization** requires completing the Vince pipeline starting with the B1 blocker.
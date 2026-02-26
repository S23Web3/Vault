# Project Memory

## HARD RULES (non-negotiable)
- **70% CHAT LIMIT** — At 70% context use, STOP. Summarize, update MEMORY.md, tell user to open new chat.
- **NEVER use emojis** — not in code, not in output, not anywhere. Zero tolerance.
- **OUTPUT = BUILDS ONLY** — Output complete builds (file path + code) ready to run. Do NOT execute code. Write the build, state the run command, stop.
- **NO FILLER** — Code and run commands only. Every non-code token is wasted money.
- **NO BASH EXECUTION** — NEVER run Python scripts via Bash tool. User runs everything from terminal. Bash only for git commands if requested.
- **SCOPE OF WORK FIRST** — Before ANY build: (1) Define scope. (2) List permissions needed. (3) Get user approval. (4) Build.
- **NEVER OVERWRITE FILES** — Check if file exists first. If yes, create versioned copy (e.g., `filename_v2.py`).
- **UPDATE MEMORY BEFORE BUILDING** — Memory is the source of truth across sessions.

## BUILD WORKFLOW (mandatory)
1. Write the code — complete files, no stubs
2. Write test script — `scripts/test_<n>.py`
3. Test the script — run via Bash, read output, fix errors
4. Review code — check bugs, imports, logic
5. Test run — execute actual functionality
6. Output — only after all tests pass
- SCRIPT IS THE BUILD — one script that creates all files, tests each, reports results.

## Vince — General Purpose Trading AI Agent
- Strategy-agnostic ML agent. Four Pillars is the FIRST strategy loaded.
- Architecture: Strategy plugin -> Feature extraction -> XGBoost -> SHAP -> User reviews -> User trains
- Three personas: Vince (rebate farming), Vicky (copy trading), Andy (FTMO)
- Skill reference: `.claude/skills/vince-ml/SKILL.md`

## Four Pillars Trading System
- **Current version**: v3.8.4 (Python backtester). See `09-ARCHIVE/four-pillars-version-history.md` for all versions.
- **GitHub repo**: https://github.com/S23Web3/ni9htw4lker (identity: S23Web3, malik@shortcut23.com)
- **Local git root**: `PROJECTS/four-pillars-backtester/` (NOT Desktop/ni9htw4lker)
- **Spec doc**: `02-STRATEGY/Indicators/ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` (v2.0)
- **Pine Script skill**: `.claude/skills/pinescript/` — always load for indicator work

## Commission Calculation — CRITICAL
- 0.08% (0.0008) taker per side on notional
- Python: `commission_rate=0.0008`, `notional=margin*leverage`. Cost = notional * rate.
- Pine Script: Use `strategy.commission.cash_per_order` with value=8 (NOT commission.percent — ambiguous with leverage)
- Rebate: 70% account = $4.80/RT net, 50% account = $8.00/RT net. Settle daily 5pm UTC.
- NEVER hardcode dollar amounts — always derive from rate * notional so optimizer can sweep.
- NEVER use strategy.close_all() for flips — causes phantom double-commission trades.

## Reference Constants
- **Stochastics (Kurisko)**: 9-3 (entry), 14-3 (confirm), 40-3 (divergence), 60-10 (macro). All Raw K (smooth=1).
- **Ripster Clouds**: Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89, Cloud 5: 180/200
- **5m > 1m**: ALL low-price coins profitable on 5m, most negative on 1m.
- **LSG 85-92%**: Most losers were profitable at some point — TP or ML filter is key lever.
- **Tight TP destroys value**: TP<2.0 ATR HURTS most coins. Always backtest, never trust MFE alone.

## Python Backtester (PROJECTS/four-pillars-backtester/)
- **Data**: Bybit v5 API (BybitFetcher, public, no auth). 399 coins cached (1m Parquet, ~6.2 GB).
- **Low-price coins**: 1000PEPEUSDT, RIVERUSDT, KITEUSDT, HYPEUSDT, SANDUSDT
- **Commission**: Rate-based (0.0008). Dashboard has margin/leverage/rate inputs.
- **v3.8.4 results (3-coin optimal)**: +$17,863 (RIVER TP=2.0, KITE/BERA no TP)
- **Sanity check**: `python scripts\sanity_check_cache.py`

## PostgreSQL (vince database)
- PG16 port 5433, user=postgres, pw=admin (in `.env`)
- psql: `C:\Program Files\PostgreSQL\16\bin\psql.exe`
- Schema: backtest_runs, backtest_trades, equity_snapshots, live_trades, commission_settlements
- CLI: `python scripts/run_backtest.py --symbol RIVERUSDT --save-db`

## Dashboard (2026-02-12) — COMPLETE
- File: `scripts/dashboard.py` (~1450L, v3.8.4 engine)
- Modes: settings | single | sweep | sweep_detail
- Sweep: incremental, CSV persistence, auto-resume, params_hash
- Normalizer: `data/normalizer.py` — universal OHLCV CSV-to-parquet (6 exchange formats)
- Tests: `test_normalizer.py` (17), `test_sweep.py` (11) — NOT YET RUN

## Vince ML Build (2026-02-11)
- ALL 9 ML modules BUILT: features, triple_barrier, purged_cv, meta_label, shap_analyzer, bet_sizing, walk_forward, loser_analysis, xgboost_trainer
- Staging (not deployed): 5-tab ML dashboard, live_pipeline.py, fixed run_backtest.py
- Deploy command: `python scripts/build_staging.py`

## Logs & Journals — MANDATORY SAVE LOCATIONS
- **Build journals**: ALWAYS save to `07-BUILD-JOURNAL\YYYY-MM-DD.md` (append sessions to same day file)
- **Session logs**: ALWAYS save to `06-CLAUDE-LOGS\YYYY-MM-DD-topic.md`
- **NEVER save journals to vault root or .claude\memory\**
- **Version history**: `09-ARCHIVE\four-pillars-version-history.md`
- **Old memory backup**: `09-ARCHIVE\MEMORY-full-backup-2026-02-13.md`
- **epub/pdf reader installed**: ebooklib + beautifulsoup4 + pypdf + pymupdf4llm

## Environment
- **Windows paths**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester`
- **Bash paths**: `/c/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester`
- **Ollama**: `C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe` (port 11434)

## PENDING BUILDS
- **P1**: Deploy staging files (`python scripts/build_staging.py`)
- **P2**: ML meta-label on D+R grades (D=-$3.59/tr, R=-$3.00/tr, drag -$3,323)
- **P3**: Multi-coin portfolio optimization (add PEPE, SAND, HYPE)
- **P4**: 400-coin ML sweep (XGBoost across all 399 coins on 5m)
- **P5**: Live TradingView validation (Pine v3.8 vs Python backtester)
- **P6**: 24/7 executor framework (trading-tools/executor/) — NOT BUILT
- **P7**: UI/UX research for dashboard workflow guidance

## Critical Lessons
- When user mentions a tool, ask: "Is this about the tool or the underlying need?"
- Simple automation = 30 min max. If taking longer, solving wrong problem.
- Verify before reporting success. Test it, show proof, never claim "it's working" without evidence.
- ATR/price ratio matters: RIVER profitable (commission ~7% of TP). BTC fails (commission ~46% of TP).
- Bybit pagination: Returns newest-first, paginate backward from end_ms.
- WEEX API: No historical pagination. Use Bybit for historical data.
- df.set_index('datetime') removes from columns — backtester must check both df.columns and df.index.name.

# Live System Status
**Last Updated:** 2026-02-26

---

## Active Systems

| System | Version | Status | Location | Run Command |
|--------|---------|--------|----------|-------------|
| Backtester Engine | v3.8.4 | PRODUCTION | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\` | (via dashboard) |
| Dashboard | v3.9.2 | PRODUCTION | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v392.py` | `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v392.py"` |
| BingX Connector | v1.0 | DEMO RUNNING | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\` | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"` |
| Screener v1 | v1.0 | SUPERSEDED | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\screener_v1.py` | Do not use (backward-looking, dominated by regime noise) |
| WEEX Screener | -- | NOT BUILT | -- | Scoped at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` |
| Vince v2 | -- | CONCEPT ONLY | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md` | -- |

## Infrastructure

| Service | Status | Details |
|---------|--------|---------|
| PostgreSQL | RUNNING | PG16, port 5433, database=vince, user=postgres |
| Ollama | INSTALLED | qwen3:8b (4.9 GB), port 11434, full GPU inference on RTX 3060 |
| Jacky VPS | PROVISIONED | n8n + nginx. Migration scripts ready: `C:\Users\User\Documents\Obsidian Vault\scripts\migrate_pc.ps1`, `setup_vps.sh`, `deploy.ps1`. Bot deployment pending user execution. |

## BingX Connector Detail (as of 2026-02-26)
- **Mode**: Demo (BingX VST), 102k VST balance
- **Config**: 47 coins, $75 margin, 20x leverage, tp_atr_mult=4.0, poll=45s, timeframe=5m
- **Plugin**: FourPillarsV384 (grades A+B enabled, C disabled)
- **Commission**: 0.06% taker per side (0.0012 RT), deducted once at exit in position_monitor.py
- **Tests**: 67/67 passing
- **Audit**: `python scripts/audit_bot.py` — trades, docstrings, commission, strategy
- **Warmup**: 201 bars on 5m = ~16.7 hours from startup
- **Master doc**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md`

## Pending Deployments

| Item | Status | Blocker |
|------|--------|---------|
| Dashboard v3.9.3 | BLOCKED | IndentationError at line 1972, fix script needs work |
| Vince ML staging | BUILT, NOT DEPLOYED | Run `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_staging.py"` |
| YT Transcript Analyzer | SPEC WRITTEN | Build not started |
| WEEX Screener | SCOPED | 3 files to build, public API, no auth needed |
| BingX live ($1k) | WAITING | Depends on demo stability + strategy comparison (Step 2) |
| VPS bot deployment | SCRIPTS READY | Run `.\scripts\migrate_pc.ps1` then `setup_vps.sh` on VPS then use `.\scripts\deploy.ps1` |

## Week Plan (2026-02-25 target)
- Tue: Demo live on BingX VST (DONE)
- Wed-Thu: Strategy comparison (Step 2)
- Fri: Go live $1k / $50 margin (Step 3)

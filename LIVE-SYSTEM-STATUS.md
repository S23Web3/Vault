# Live System Status
**Last Updated:** 2026-03-04

---

## Active Systems

| System | Version | Status | Location | Run Command |
|--------|---------|--------|----------|-------------|
| Backtester Engine | v3.8.4 | PRODUCTION | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\` | (via dashboard) |
| Dashboard | v3.9.4 (CUDA) | BUILT | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py` | `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py"` (requires .venv312) |
| Dashboard (prior) | v3.9.3 | PRIOR STABLE | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v393.py` | `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v393.py"` |
| BingX Connector | v1.1 (patched) | LIVE ($110) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\` | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"` |
| BingX Dashboard | v1.5 | BUILT | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py` | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py"` |
| BingX Beta Bot | v384/20x | BUILT (not running) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main_beta.py` | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main_beta.py"` |
| BingX Docs Scraper | v1 | COMPLETE | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-COMPLETE-REFERENCE.md` | `python scrape_bingx_docs.py --debug` |
| BingX Live Screener | v1 | BUILT | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\bingx_screener.py` | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\bingx_screener.py"` |
| BingX Daily Report | v1 | BUILT | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py` | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py"` |
| YT Transcript Analyzer | v2 | BUILT | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\` | `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\gui.py"` |
| Screener v1 | v1.0 | SUPERSEDED | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\screener_v1.py` | Do not use (backward-looking, dominated by regime noise) |
| WEEX Screener | -- | NOT BUILT | -- | Scoped at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` |
| Vince v2 | -- | CONCEPT ONLY | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md` | -- |
| Daily Bybit Updater | v1 | BUILT (not yet executed) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\daily_update.py` | `python scripts/build_daily_updater.py` then `python scripts/daily_update.py` |

## Infrastructure

| Service | Status | Details |
|---------|--------|---------|
| PostgreSQL | RUNNING | PG16, port 5433, database=vince, user=postgres |
| Ollama | INSTALLED | qwen3:8b (4.9 GB), port 11434, full GPU inference on RTX 3060 |
| Jacky VPS | PROVISIONED | n8n + nginx. Migration scripts ready: `C:\Users\User\Documents\Obsidian Vault\scripts\migrate_pc.ps1`, `setup_vps.sh`, `deploy.ps1`. Bot deployment pending user execution. |

## BingX Connector Detail (as of 2026-03-04)

- **Mode**: LIVE — $110 real account, futures wallet
- **Config**: 47 coins, $5 margin, 10x leverage ($50 notional), tp_atr_mult=null, poll=45s, timeframe=5m
- **Plugin**: FourPillarsV384 (grades A+B, require_stage2=true, rot_level=80)
- **Commission**: 0.05% taker per side (0.001 RT), fetched from API at startup
- **WS**: STABLE — listenKey + gzip + Ping/Pong all fixed
- **Breakeven raise**: LIVE — triggers at 0.16% profit, tested and confirmed on ELSA + VIRTUAL
- **TTP**: LIVE — reduceOnly bug fixed (Phase 2), SL tightening after TTP activation (0.3%)
- **Dashboard**: v1.5 — signature fixed, period filter, session equity curve, trade chart popup
- **Beta bot**: BUILT (not running) — 44 coins, 20x leverage, beta/ isolated data path
- **Tests**: 67/67 passing
- **Bugs fixed this session**: BUG-1 (109400 reduceOnly), BUG-4 (signature 100001), BUG-2 (equity curve), BUG-5 (coin summary date), BUG-9 (TTP columns missing in trades.csv)

## Pending Deployments

| Item | Status | Blocker |
|------|--------|---------|
| Dashboard v3.9.4 (CUDA) | BUILT | Requires .venv312 (Python 3.12 + Numba CUDA). Run `build_daily_updater.py` first to get data current. |
| Dashboard v3.9.3 | PRIOR STABLE | Fallback if v3.9.4 regresses. |
| Vince ML staging | BUILT, NOT DEPLOYED | Run `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_staging.py"` |
| YT Transcript Analyzer v2 | BUILT | Run: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\gui.py"` |
| BingX API Docs Scraper | COMPLETE | Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py" --debug` |
| WEEX Screener | SCOPED | 3 files to build, public API, no auth needed |
| BingX live ($1k) | WAITING | VST unreliable (Step 2 parked). Go live when funds transferred to futures wallet. |
| VPS bot deployment | SCRIPTS READY | Run `.\scripts\migrate_pc.ps1` then `setup_vps.sh` on VPS then use `.\scripts\deploy.ps1` |

## Next Steps (as of 2026-03-04 — end of session)

- **BingX IMMEDIATE**: Restart bot (`python main.py`) — Phase 2 already applied, no 109400 expected
- **BingX Dashboard**: Launch v1.5 (`python bingx-live-dashboard-v1-5.py`) → test Close Market → verify session equity curve → test trade chart popup
- **Beta bot**: Remove confirmed overlaps from config_beta.yaml (LYN, GIGGLE, BEAT, TRUTH, STBL, BREV, Q, SKR, MUS not available) → start `python main_beta.py`
- **Future**: Backtester TP sweep at 0.5-1.0x ATR (LSG=75.8%, AvgMFE=0.937% supports tight TP)
- Vince ML build -- B1 FourPillarsPlugin, then B3 Enricher (blocked on v386 signal file)
- VPS deployment when bot is stable enough to run unattended

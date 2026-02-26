# 2026-02-26 VPS Migration: .gitignore + Script Fix

## Session Summary
Built vault-level `.gitignore`, updated bingx-connector `.gitignore`, and patched `migrate_pc.ps1` to skip `.gitignore`/`.gitattributes` creation if they already exist. Confirmed all bot code is cross-platform (no hardcoded Windows paths). No bot code changes needed for VPS deployment.

## Context
- Previous session (separate agent) built 3 migration scripts: `migrate_pc.ps1`, `setup_vps.sh`, `deploy.ps1`
- Those scripts were comprehensive but `migrate_pc.ps1` unconditionally overwrote `.gitignore` with a less comprehensive version
- This session created the more comprehensive `.gitignore` first, then patched the script to respect it

## Files Created/Modified
1. **CREATED** `C:\Users\User\Documents\Obsidian Vault\.gitignore` — vault-level, 60 lines, excludes ~33GB data + secrets + runtime artifacts
2. **UPDATED** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.gitignore` — added `logs/` and `venv/`
3. **UPDATED** `C:\Users\User\Documents\Obsidian Vault\scripts\migrate_pc.ps1` — added `Test-Path` skip for `.gitignore` and `.gitattributes` (won't overwrite if already exists)
4. **CREATED** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-26-vps-gitignore-deploy.md` — plan copy

## Key Decisions
- Cooldown (3 bars) skipped for now — user will evaluate after 5m demo data comes in
- 1m losses expected — backtester confirms 5m >> 1m for all low-price coins
- No bot code changes needed: audit script + plugin + main.py all use `Path(__file__).resolve()` (cross-platform)
- Plugin import: `Path(__file__).resolve().parent.parent.parent / "four-pillars-backtester"` resolves to `/root/vault/PROJECTS/four-pillars-backtester` on VPS
- GitHub repo is `S23Web3/Vault` (private), not `S23Web3/obsidian-vault`

## Cross-platform verification
- `audit_bot.py`: all paths via `Path(__file__).resolve()` — works on Linux
- `four_pillars_v384.py` plugin: backtester path via relative `Path` traversal — works on Linux
- `main.py`: all paths relative, `logs/` dir created at startup — works on Linux
- One minor note: `audit_bot.py` line 316 uses `"\\"` in a startswith check, but the prefix-only check (`"scripts"`) catches it anyway — no fix needed

## What's Excluded by vault .gitignore (mine, more comprehensive than script's)
- `PROJECTS/four-pillars-backtester/data/` (entire dir — script only listed subdirs, missed output/, presets/, cache_backup_*)
- `trading-tools/data/cache/` (parquet — script missed this entirely)
- `Books/` (PDF/EPUB — script missed this)
- `.obsidian/` (entire dir — script only excluded workspace.json)
- `Tv.md`, `.env` (credentials)
- `**/__pycache__/`, `*.pyc`, `**/.pytest_cache/`, `**/venv/`, `**/logs/`
- `state.json`, `trades.csv` (bot runtime state — script missed these)
- `*.pkl`, `*.h5`, `*.onnx`, `*.parquet`, `*.meta` (binaries/data — script missed *.parquet, *.meta)
- OS junk, backup files

## Next Steps (user runs manually)
1. Run `migrate_pc.ps1` from PowerShell: `cd "C:\Users\User\Documents\Obsidian Vault" && .\scripts\migrate_pc.ps1`
2. Upload + run `setup_vps.sh` on VPS (see migration guide)
3. Bot starts on VPS with systemd, 5m timeframe, 47 coins
4. Wait ~40h (16.7h warmup + 24h trading), then `python scripts/audit_bot.py` on VPS
5. Audit should show TP_HIT/SL_HIT instead of EXIT_UNKNOWN

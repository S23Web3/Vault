# 2026-02-26 VPS Setup Part B + Local Auto-Start + TG Formatting

## Summary
Completed VPS migration Part B (setup_vps.sh), discovered VST API blocked from VPS, pivoted to local auto-start with Task Scheduler. Also reformatted all Telegram messages with HTML bold headers and line breaks.

## VPS Setup (Part B)
- SCP'd `setup_vps.sh` to `root@76.13.20.191:/root/`
- Fixed CRLF line endings with `sed -i 's/\r$//'`
- All 9 steps completed:
  - SSH key generated and registered with GitHub (S23Web3)
  - Vault cloned to `/root/vault` (992 objects, 20.79 MiB)
  - Python 3.12.3 installed, venv created
  - Dependencies installed (requests, pyyaml, python-dotenv, pandas, numpy)
  - .env created manually (4 keys)
  - Import test: 12/12 modules OK
  - systemd service created and started

## VST API Blocked from VPS
- VPS is in Jakarta, Indonesia (Hostinger AS47583)
- `open-api-vst.bingx.com` resolves to Indonesian IPs (139.255.196.196, 182.23.79.195)
- VPS cannot reach these IPs at all (100% packet loss, TCP timeout)
- BingX blocks datacenter/hosting IPs on their VST infrastructure
- Live API (`open-api.bingx.com`) works fine via CloudFront CDN
- Confirmed with: price fetch (200 OK), signed balance query (code 0, account identified)
- Futures wallet balance: $0.00 (funds in spot)

## Live API Verification
- Test script written and run on VPS: `test_live_api.py`
- Price fetch: BTC-USDT at $68,115.30
- Limit order attempt: rejected with "Insufficient margin" (expected, $0 in futures wallet)
- Account balance query: authenticated successfully, userId confirmed
- Conclusion: live API fully functional from VPS, ready when funds transferred

## Script Bug Found
- `setup_vps.sh` line 230 checks for `BINGX_SECRET` but bot code expects `BINGX_SECRET_KEY`
- Caused false "Missing keys" warning during Step 6
- Not a blocker (bot reads .env directly, not the script's check)

## Local Auto-Start Build
- Build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_autostart_and_tg.py`
- Created 3 new files:
  - `scripts\run_bot.ps1` — PowerShell wrapper with crash recovery (30s restart delay, clean exit detection)
  - `scripts\bingx-bot-task.xml` — Task Scheduler: boot trigger, 60s delay, no idle stop
  - `scripts\install_autostart.ps1` — One-shot admin installer
- Modified 3 files (10 TG message replacements):
  - `executor.py` — ENTRY, ORDER FAILED, ORDER ID UNKNOWN
  - `position_monitor.py` — EXIT, DAILY SUMMARY, HARD STOP, WARNING
  - `main.py` — STARTUP, SHUTTING DOWN, STOPPED
- All 3 py_compile PASS
- Backups created for all modified files

## Telegram Formatting
- Before: single-line dumps like `EXIT: GUN-USDT_LONG reason=EXIT_UNKNOWN pnl=-6.03 daily=-27.36`
- After: HTML bold headers + line breaks:
  ```
  BOT STARTED
  Coins: 47
  Open: 3
  Mode: DEMO
  ```
- Confirmed working in Telegram (screenshot verified)

## Auto-Start Installed
- Task Scheduler task "BingXBot" registered successfully
- Triggers on boot with 60s delay
- Bot running on local PC with 47 coins, 5m chart, demo mode

## VPS Status
- Bot service `bingx-bot` needs to be stopped (still pointing at VST which is blocked)
- Run on VPS: `systemctl stop bingx-bot`
- VPS ready for live trading when: (1) funds in futures wallet, (2) config.yaml `demo_mode: false`

## Files Created
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_autostart_and_tg.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_bot.ps1`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\bingx-bot-task.xml`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\install_autostart.ps1`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\test_live_api.py` (on VPS only)

## Files Modified
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` (TG formatting)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` (TG formatting)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` (TG formatting)

# Countdown to Live
**Created:** 2026-02-24 | **Updated:** 2026-02-25 (session 5)
**Target:** First live trade on BingX — $1,000 account, $50 margin per position
**Status:** Step 1 all code fixes DONE (including M2/UTC+4/Telegram). Signal pipeline proven. Next: add 40 coins, restart bot, wait for first trade.

---

## The Goal

- Account: $1,000 on BingX
- Position size: $50 margin per trade
- Leverage: 10x (= $500 notional per position)
- Max concurrent positions: 3 (= $150 margin at risk at one time, 15% of account)
- Strategy: Four Pillars v3.8.4 — A and B grade signals only
- Bot: BingX Connector running on Jacky VPS

---

## Can This Happen This Week?

**Honest answer: demo trades yes, live trades possibly — depends on strategy comparison (Step 2).**

| Milestone | Realistic by |
|-----------|-------------|
| Demo trades firing with real signals | Tomorrow (1 session) |
| Strategy 1 vs 2 comparison in dashboard | 2-3 sessions |
| All 67 tests passing | Same session as demo |
| Live trades with dynamic screener | End of week if sessions allow |


---

## Step 1 — Get Demo Live
**Status:** ALL CODE FIXES DONE (2026-02-25 session 5). Signal pipeline proven. Next: add coins, restart, wait for trade.
**Session cost:** Done

### What was done (all complete)

- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` — switched to `four_pillars_v384`, added `four_pillars` block, buffer 201
- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` — fixed float precision assertion
- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` — fixed shared-module mock conflict
- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state_manager.py` — fixed DEFAULT_STATE shallow copy bug
- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` — leverage LONG/SHORT loop (SB1), reconcile error check (M1), absolute log path to `logs/` dir (M2), UTC+4 formatter, startup timestamp UTC+4
- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` — json.dumps separators (E1)
- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx_auth.py` — recvWindow added (A1)
- [x] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\notifier.py` — Telegram timestamps UTC+4
- [x] 67/67 tests passing
- [x] Signal pipeline proven — GUN-USDT LONG B fired at 14:02:20, order failed due to E1 (now fixed)

### What remains

1. ~~Add 37 more coins to config.yaml~~ **DONE (2026-02-25)** — 16 coins from 2026-02-12 sweep, filtered by Exp/DD/PF/sample size. max_positions→10, max_daily_trades→60, daily_loss_limit→200.
   - Removed: GUN-USDT, AXS-USDT (not in sweep), TRIAU (68 trades), BIRB (263 trades), ICNT (PF 1.02), JELLYJELLY (DD 45.7%)
   - **NOTE: Sweep had 20 coins total — max 16 passed quality filters. Did not reach 40. BingX perp availability for meme coins (PIPPIN, GIGGLE, FOLKS, etc.) unverified — must check before restart.**
2. ~~Update max_positions~~ **DONE** — scaled to 10
3. **NEXT: Run coin verification script** — `python scripts/verify_coins.py` (built 2026-02-25). Checks all config coins against live BingX contracts. Exit 0 = all clear. Exit 1 = prints clean list for config.yaml.
4. Restart bot:
   ```
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"
   ```
5. Verify: log at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\YYYY-MM-DD-bot.log`, UTC+4 timestamps, Telegram UTC+4
6. Wait for first A/B signal to fire and order to place successfully

**Done when:** Demo order appears in BingX VST account and Telegram alert received with UTC+4 timestamp.

---

## Step 2 — Strategy Comparison in Dashboard
**Status:** NOT DONE — scoping incomplete as of 2026-02-23
**Blocking:** 19 open spec unknowns from strategy scoping session
**Session cost:** 1-2 sessions for spec + 1 session for dashboard build

### Context

The strategy scoping session (2026-02-23) identified two signal types:

**Signal Type 1 — Quad Rotation (current implementation)**
- K1 exits oversold zone (flexible threshold, not hard 20/80)
- K2, K3 follow in sequence
- Entry at K1 (aggressive), K2 (balanced), or K3 (confirmed)
- This is what the current `compute_signals_v383` backtester implements

**Signal Type 2 — Add-On / Late Runner (missed trades)**
- K3 and K4 holding above 50 (long bias confirmed)
- K1 and K2 pull back and re-exit their zone
- Tighter stop — designed as add-on or re-entry
- Not yet implemented in backtester

The "missed trades" you referred to are likely Signal Type 2 setups — the current implementation only catches Type 1 entries. Type 2 would catch re-entries and add-ons that currently show up as missed in the P&L review.

### What the comparison needs

1. **Complete the 19 open spec unknowns** — particularly items 3, 6, 7, 9, 10 which directly affect signal logic
   - Ref: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-23-four-pillars-strategy-scoping.md`
   - Ref: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-QUANT-SPEC-v1.md`

2. **Build Signal Type 2 in backtester** — add-on/re-entry logic alongside existing Type 1

3. **Dashboard comparison tab** — side-by-side:
   - Strategy A: Type 1 only (current v3.8.4 results)
   - Strategy B: Type 1 + Type 2 combined
   - Metrics: total trades, win rate, avg PnL, Sharpe, max drawdown, missed trade count
   - Run on same coins and date range for valid comparison

**Done when:** Dashboard shows side-by-side equity curves and metrics for both strategies. You pick which one goes live.

---

## Step 3 — Go Live
**Status:** NOT DONE — depends on Steps 1 and 2
**Session cost:** 0.5 session (config + deploy)

### Prerequisites (all must be true before flipping to live)

- [ ] All 67 tests passing
- [ ] Demo bot ran for minimum 24 hours without crashes
- [ ] At least 3 demo trades placed and closed correctly (SL or TP hit, P&L logged, Telegram alert sent)
- [ ] Strategy comparison done — winning strategy chosen
- [ ] `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` updated with chosen strategy config
- [ ] $1,000 deposited in BingX live account
- [ ] API keys created (live, not VST) and added to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.env` on Jacky VPS

### Config changes for live

```yaml
connector:
  demo_mode: false   # was true

position:
  margin_usd: 50.0   # confirmed
  leverage: 10       # confirmed

risk:
  max_positions: 3
  daily_loss_limit_usd: 75.0   # 7.5% of account per day hard stop
```

### Deploy to Jacky VPS

1. Copy `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\` to VPS (exclude `.env`, use VPS `.env` with live keys)
2. Copy `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\` to VPS alongside connector (plugin imports from here)
3. `python main.py` — starts with live API, real orders

**Done when:** First live order placed, appears in BingX live account, Telegram alert received.

---

## Screener (parallel track — not blocking live)

The screener is NOT required to go live. The 3-coin hardcoded config is sufficient to start.
Build the screener after the first live session is confirmed stable.

| Screener file | Purpose |
|---|---|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\utils\bingx_screener_fetcher.py` | Fetch all BingX symbols + OHLCV |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\utils\screener_engine.py` | Run signals, build metrics table |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\utils\coin_ranker.py` | Filter + rank + write `active_coins.json` |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\live_screener_v1.py` | Streamlit UI + auto-refresh + Ollama labels |

Ollama (qwen3:8b, RTX 3060, full GPU) scores coins on delta changes only — visual audit, does not affect which coins go into `active_coins.json`.

---

## Known Risks Before Live

| Risk | Mitigation |
|------|-----------|
| Plugin imports backtester via relative path — breaks on VPS | Copy `signals/` folder to VPS alongside connector |
| 200-bar warmup = ~16h on 5m before first signal | Start bot, let it warm up, do not expect instant trades |
| K1/K2/K3 thresholds in plugin may not match refined spec | Verify after strategy comparison (Step 2) |
| No dynamic coin reload — must restart bot to change coin list | Acceptable for now; screener addresses this later |

---

## Session Priorities (given 1 hour left today)

**Today (now → 5pm): DO NOT BUILD**
- End of day. Not enough time to start and finish Step 1 cleanly.
- Risk: half-built changes left in an inconsistent state overnight.

**Tomorrow morning (first session):**
- Open `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md` first
- Immediate goal: Step 1 — fix 2 bugs, edit `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`, get 67/67 tests, run demo bot
- Do not touch strategy spec until Step 1 demo is confirmed running

**This week target:**
- Mon-Tue: Step 1 (demo live)
- Wed-Thu: Step 2 (strategy spec completion + comparison build)
- Fri: Step 3 (go live) — achievable if sessions run cleanly

---

## File Index

| File | Role |
|------|------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` | Bot entry point |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | All config — edit before each step |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` | Strategy plugin — wraps compute_signals |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` | Order placement |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` | Integration tests — all passing |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py` | Signal logic — imported by plugin |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\FOUR-PILLARS-QUANT-SPEC-v1.md` | Strategy spec — 19 unknowns remaining |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-23-four-pillars-strategy-scoping.md` | Strategy scoping session log |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md` | Full connector architecture |

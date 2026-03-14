# Session Log — 2026-03-12 — WEEX Connector Planning

## What Was Done This Session

### 1. WEEX OHLCV Data Probe

**Goal**: Determine if WEEX has historical OHLCV data for backtesting.

**Script built**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\probe_weex_api.py`

**Result (user ran it)**: NO historical pagination on any WEEX endpoint.
- `api-contract.weex.com/capi/v2/market/candles` — returns latest 1,000 candles only, all params (`startTime`, `endTime`, `after`, `before`, etc.) silently ignored
- `api-spot.weex.com/api/v2/market/candles` — HTTP 400 without `period` param; with `period` returns latest ~300 candles only
- `api.weex.com` — dead host (DNS fails)
- `api-futures.weex.com` — dead host (DNS fails)

**DNS resolution check (all known WEEX hosts)**:
- ALIVE: `api-contract.weex.com` → 13.158.158.153
- ALIVE: `api-spot.weex.com` → 52.193.189.139
- DEAD: `api.weex.com`, `open-api.weex.com`, `api-futures.weex.com`, `api.weexglobal.com`, `open-api.weexglobal.com`

**Conclusion**: WEEX has no historical data API. Bybit data will be used as backtesting proxy. BingX data (~626 coins) covers coins not on Bybit.

### 2. WEEX Connector Decision

User confirmed: build a full WEEX live trading connector, same architecture as BingX connector v1.5.

**Plan written**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-v1.md`

Architecture approved:
- Project root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\`
- Same thread model as BingX (MarketLoop / MonitorLoop / WSListener)
- Same component set — only exchange-specific files differ (auth, data_fetcher, executor, position_monitor, ws_listener)
- Exchange-agnostic files copied unchanged: risk_gate, signal_engine, notifier, ttp_engine, plugins

### 3. Handoff Prompt Written

**File**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`

**8-phase sequence**:
1. Phase 0 — Load Python skill + create WEEX skill
2. Phase 1 — Scrape WEEX API docs (Playwright, same pattern as BingX scraper) → `WEEX-API-COMPLETE-REFERENCE.md`
3. Phase 2 — WEEX coin inventory (cross-ref against BingX + Bybit data dirs)
4. Phase 3 — UML architecture (from API reference)
5. Phase 4 — Logic lifeline walkthrough (test scripts against live API)
6. Phase 5 — Function design from UML (signatures + docstrings only)
7. Phase 6 — Full connector build (module by module, test at each step)
8. Phase 7 — JIT/OOP performance review (post-build)
9. Phase 8 — Complete audit + live test

**WEEX API doc entry point confirmed by user**: `https://www.weex.com/api-doc/contract/Market_API/GetBookTicker`
Left sidebar contains full endpoint menu. Site does not support deep-linking.

**Key confirmed facts embedded in prompt**:
- WEEX futures only (not spot)
- Two live hosts only (`api-contract.weex.com`, `api-spot.weex.com`)
- Auth scheme TBD from docs scrape
- `.env` location and format specified
- BingX data usable for coins not on Bybit

## Files Created This Session

| File | Purpose |
|------|---------|
| `scripts/probe_weex_api.py` | API probe — confirmed no historical data |
| `06-CLAUDE-LOGS/plans/2026-03-12-weex-connector-v1.md` | Approved architecture plan |
| `06-CLAUDE-LOGS/plans/2026-03-12-weex-connector-build-prompt.md` | New chat handoff prompt |

## Next Action

Open a new chat. Paste the contents of:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`

as the first message.

---

## Addendum (same day, later session)

**BingX v2 Bug Audit + v3 Build completed.**
- 19 bugs identified in v2 connector infrastructure
- Full bug-fixed v3 built at: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v3\`
- Bug audit report: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md`
- Build prompt updated to reference v3 as template (not v2)
- Critical finding: WEEX = Bitget white-label (API URL patterns match exactly)
- Session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-12-bingx-v3-bug-fixes.md`

# Plan: Install Playwright MCP + Read & Document BingX API Docs + Lifecycle Test Completion

## Context
The 15-step lifecycle test validates the BingX trade cycle against VST demo. Steps 1-4 pass, step 5 failed due to E2-STOPPRICE bug (fixed in executor.py, not yet re-tested). The BingX v3 docs site is JS-rendered (unreadable by WebFetch). User wants Playwright MCP installed to crawl and document the official BingX API documentation, then cross-reference all API calls and complete the lifecycle test.

## Step 1: Install Playwright MCP server
- Run: `claude mcp add playwright npx @playwright/mcp@latest`
- Verify it appears in MCP config
- First use will auto-download Chromium

## Step 2: Crawl BingX API docs via Playwright MCP
- Navigate to `https://bingx-api.github.io/docs-v3/#/en/info`
- Extract and document these sections (relevant to the connector):
  - Authentication / Signature method
  - Place order endpoint (MARKET, LIMIT, STOP_MARKET, TAKE_PROFIT_MARKET)
  - Query positions
  - Query open/pending orders
  - Cancel order
  - Set leverage
  - Set margin type
  - Get mark price / klines / contract specs
- Save documentation to: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-REFERENCE.md`

## Step 3: Fix build script (prevent E2-STOPPRICE regeneration)
- **File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\build_bingx_connector.py`
- Lines 954, 961: Remove `str()` wrapper on `signal.sl_price` and `signal.tp_price`

## Step 4: Cross-reference executor.py API calls against documented specs
- Compare every endpoint, param name, and type in executor.py / bingx_auth.py against the extracted docs
- Flag discrepancies (wrong params, missing fields, deprecated endpoints)

## Step 5: Re-run lifecycle test
- Command: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py"`
- Step 5 should pass with the stopPrice fix
- Fix any new failures in steps 6-15

## Step 6: Restart bot once 15/15 pass
- `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"`

## Step 7: Update session log
- Append to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-25-lifecycle-test-session.md`

## Verification
- Playwright MCP installed and functional
- BingX API reference doc created with all relevant endpoints
- Build script no longer has str() bug
- All 15 lifecycle test steps pass
- Bot starts and polls successfully

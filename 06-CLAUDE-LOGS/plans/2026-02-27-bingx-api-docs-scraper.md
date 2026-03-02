# Plan: Scrape BingX API Docs into Indexed Reference Document

## Context

The BingX API documentation at `https://bingx-api.github.io/docs-v3/#/en/info` is a JS-rendered SPA (Element UI) that was previously unreadable without a browser engine. The user now has Playwright MCP tools available. The existing manual reference at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-REFERENCE.md` covers only 11 endpoints. The full site has **~215 leaf endpoint pages** across 8 top-level sections. Goal: scrape ALL content into a single indexed markdown document usable as a complete bot reference.

## Site Structure (verified via Playwright)

- **URL**: `https://bingx-api.github.io/docs-v3/#/en/info`
- **Routing**: Hash-based SPA (`#/en/Section/SubSection/EndpointName`)
- **Sidebar**: Element UI menus (`el-submenu`, `el-menu-item`)
- **Content area**: `<main>` element, consistent per-page structure
- **Per endpoint page**: method badge + path, rate limit, signature info, host table, params table, response table, request/response JSON examples, error code table, demo code (Python/Go/Node/Java/C#/PHP/Shell tabs)

### Full Navigation Tree (8 sections, ~215 endpoints)

| Section | Sub-sections | Approx Endpoints |
|---------|-------------|-----------------|
| Quick Start | Signature Auth, Basic Info, FAQ, WebSocket Rules | 7 |
| Swap | Market Data, Trades, Account, WS Market, WS Account | 69 |
| Spot | Market Data, Account, Wallet, Trades, WS Market, WS Account | 51 |
| Coin-M Futures | Market Data, Trades, WS Market, WS Account | 33 |
| Account and Wallet | Fund Account, Wallet, Sub-account Mgmt | 35 |
| Agent | (flat list) | 8 |
| Copy Trade | USDT-M Perpetual, Spot Trading | 13 |
| Introduce + Change Logs | (single pages) | 2 |

## Build: `scrape_bingx_docs.py`

**Location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py`

### Dependencies

```
playwright  (pip install playwright && playwright install chromium)
```

No other dependencies needed. Uses only stdlib (`json`, `re`, `datetime`, `argparse`, `logging`, `pathlib`, `time`, `asyncio`) plus playwright.

### Script Architecture

```
scrape_bingx_docs.py
  |
  +-- main()                    # argparse, logging setup, orchestrator
  +-- class BingXDocsScraper:
  |     +-- __init__(page)      # stores playwright page reference
  |     +-- expand_all_nav()    # clicks all closed el-submenu items recursively
  |     +-- collect_nav_tree()  # returns list of {text, level, isSubmenu, index}
  |     +-- navigate_to(item)   # clicks menu item by index, waits for content
  |     +-- extract_page()      # extracts full page content as structured dict
  |     +-- scrape_all()        # iterates all leaf items, calls extract_page each
  |     +-- scrape_section(name)# scrapes only one top-level section (for testing)
  |
  +-- class MarkdownCompiler:
  |     +-- __init__(nav_tree, pages)
  |     +-- build_toc()         # generates table of contents with anchor links
  |     +-- format_endpoint()   # formats one endpoint dict as markdown
  |     +-- compile()           # returns full markdown string
  |
  +-- def run_debug_test()      # scrapes 3 pages from Swap > Market Data, validates
```

### Step-by-Step Build Instructions for the Agent

#### Step 1: Write the scraper script

The script must:

1. **Parse CLI arguments**:
   - `--output PATH` (default: `../docs/BINGX-API-V3-COMPLETE-REFERENCE.md`)
   - `--section NAME` (optional: scrape only one section, e.g. `Swap`, `Spot`)
   - `--test` (scrape only first 3 endpoints from Swap > Market Data)
   - `--debug` (verbose logging)
   - `--timeout SECONDS` (per-page timeout, default 5)

2. **Launch Playwright** (async, headless Chromium):
   ```python
   async with async_playwright() as p:
       browser = await p.chromium.launch(headless=True)
       page = await browser.new_page()
       await page.goto("https://bingx-api.github.io/docs-v3/#/en/info")
       await page.wait_for_timeout(3000)
   ```

3. **Expand all navigation** by clicking all `.el-submenu:not(.is-opened) > .el-submenu__title` recursively until none remain.

4. **Collect the full nav tree** using `page.evaluate()`:
   - Query all `.el-menu-item` elements (leaf pages only, not submenu titles)
   - For each: capture `innerText.trim()`, `style.paddingLeft` (determines nesting level), and element index
   - Also capture submenu titles for section headers

5. **For each leaf menu item** (in order):
   a. Click the element by index to navigate
   b. Wait for `<main>` content to update (wait for new text or 2s timeout)
   c. Extract content via `page.evaluate()` that returns a structured object:

   ```javascript
   // Inside page.evaluate():
   const main = document.querySelector('main');
   const result = {};

   // 1. Method + Path + Title (first div child)
   //    Look for the badge div containing GET/POST/DELETE and the path

   // 2. Rate limit + Signature info

   // 3. All tables -> convert to arrays of row objects
   //    Tables appear in pairs: header table + data table
   //    Sections: host, REQUEST PARAMETER, response body, error code

   // 4. Code blocks -> extract innerText from <code> elements
   //    First code = request example, second = response example
   //    Third+ = demo code (check which language tab is active)

   // 5. For demo code: click the Python tab first, then extract
   ```

   d. Store as dict: `{title, method, path, rate_limit, signature, host_table, params_table, response_table, request_example, response_example, error_table, python_demo}`

6. **Compile to markdown** using MarkdownCompiler:
   - Header with scrape date and source URL
   - Table of Contents (nested, with anchor links)
   - Section headers matching the nav tree hierarchy
   - Per endpoint: formatted tables, fenced code blocks, all structured content

7. **Write output file** to disk.

#### Step 2: Content extraction logic (critical detail)

Each endpoint page has this DOM structure inside `<main>`:
```
main > div > div > div  (one wrapper div containing ALL sections)
  > div (method badge: GET/POST + path + title)
  > div (rate limit + signature)
  > div (host table - collapsible)
  > div (params table - collapsible)
  > div (response table - collapsible)
  > div (request example - collapsible, contains <code>)
  > div (response example - collapsible, contains <code>)
  > div (error code table - collapsible)
  > div (code example - tabbed, contains <code>)
```

The extraction JS function should:
- Get `innerText` from the first child for method/path/title
- Parse each subsequent child by looking for its header text ("host", "REQUEST PARAMETER", "response body", "Request Example", "Response Example", "error code", "Code Example")
- For tables: extract `<table>` elements, iterate rows/cells to build arrays
- For code blocks: extract `<code>` element innerText
- For demo code: click the Python tab (`tab[aria-selected] text="Python"`) before extracting

#### Step 3: Markdown formatting

Each endpoint renders as:
```markdown
#### Endpoint Name

**METHOD** `/openApi/swap/v2/path/here`

- **Rate Limit**: 500 requests per 10 seconds
- **Signature**: Yes/No
- **Permission**: Read/Write

**Hosts**

| Environment | URL |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g. BTC-USDT |
...

**Response Body**

| Field | Type | Description |
|---|---|---|
| open | float64 | Opening Price |
...

**Request Example**
\```json
{ ... }
\```

**Response Example**
\```json
{ ... }
\```

**Error Codes**

| Code | Message |
|---|---|
| 109425 | Trading pair does not exist |
...

**Python Demo**
\```python
...
\```
```

#### Step 4: Write debug/test script

**Location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_scraper.py`

Tests:
1. **test_nav_tree_extraction**: Launch browser, expand nav, verify >= 200 leaf items found
2. **test_single_page_extraction**: Navigate to Kline/Candlestick Data, extract, verify:
   - `method == "GET"`
   - `path == "/openApi/swap/v3/quote/klines"`
   - `params_table` has >= 5 rows
   - `response_table` has >= 5 rows
   - `request_example` is valid JSON
   - `response_example` is valid JSON
   - `python_demo` contains `import requests`
3. **test_markdown_compile**: Feed mock data, verify output has TOC with anchor links, proper heading hierarchy, fenced code blocks
4. **test_full_section_scrape**: Scrape Swap > Market Data (13 endpoints), verify all 13 captured with non-empty content

Run command:
```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python -m pytest scripts/test_scraper.py -v
```

### Step 5: Run and validate

1. **Test mode first** (3 pages only):
   ```bash
   cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
   python scripts/scrape_bingx_docs.py --test --debug
   ```
   Verify output file has 3 endpoints with complete content.

2. **Single section** (Swap only, ~69 endpoints):
   ```bash
   python scripts/scrape_bingx_docs.py --section Swap --debug
   ```

3. **Full scrape** (all ~215 endpoints):
   ```bash
   python scripts/scrape_bingx_docs.py --debug
   ```
   Expected runtime: 5-10 minutes (215 pages * ~2s each).

4. **Validate output**:
   - File exists at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-COMPLETE-REFERENCE.md`
   - Has Table of Contents with all sections
   - Spot-check 3 random endpoints for completeness (params, response, examples present)
   - Verify no empty sections or extraction failures in the debug log

## Output

**Primary output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-COMPLETE-REFERENCE.md`

This replaces/supersedes the existing `BINGX-API-V3-REFERENCE.md` (11 endpoints) with a complete ~215-endpoint indexed reference.

**Structure of the output document**:
- Header (scrape date, source URL, total endpoint count)
- Table of Contents (nested by section/subsection)
- Quick Start (auth, basic info, FAQ, websocket rules)
- Swap (market data, trades, account, websocket market, websocket account)
- Spot (market data, account, wallet, trades, websocket)
- Coin-M Futures (market data, trades, websocket)
- Account and Wallet (fund, wallet deposits, sub-account management)
- Agent (commission, invitation)
- Copy Trade (USDT-M perpetual, spot)
- Change Logs

## Logging

Per project rules (LOGGING STANDARD):
- Log to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\YYYY-MM-DD-scraper.log`
- Dual handler: file + console
- Timestamps on every line
- Log each page visit: `[INFO] Scraping 42/215: Swap > Market Data > Kline/Candlestick Data`
- Log extraction results: `[INFO] Extracted: 7 params, 6 response fields, 7 error codes`
- Log failures: `[WARNING] Failed to extract content for: <page name> -- retrying`
- Log summary at end: `[INFO] Complete: 213/215 pages scraped, 2 failures`

## Error Handling

- Per-page try/except: if extraction fails, log warning, store `{title, error: "extraction failed"}`, continue to next
- Retry once on failure (re-click menu item, wait longer)
- Save intermediate results every 20 pages to `docs/.scrape-progress.json` so a crash doesn't lose everything
- On resume: check for progress file, skip already-scraped pages

## Files Created/Modified

| File | Action |
|------|--------|
| `PROJECTS/bingx-connector/scripts/scrape_bingx_docs.py` | CREATE - main scraper |
| `PROJECTS/bingx-connector/scripts/test_scraper.py` | CREATE - test suite |
| `PROJECTS/bingx-connector/docs/BINGX-API-V3-COMPLETE-REFERENCE.md` | CREATE - output document |

## Post-Build

After the agent completes the build and the user runs it:
1. py_compile both .py files
2. Run test_scraper.py
3. Run scrape_bingx_docs.py --test first, then full
4. Verify output document is complete and indexed
5. Copy plan to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-bingx-api-docs-scraper.md`

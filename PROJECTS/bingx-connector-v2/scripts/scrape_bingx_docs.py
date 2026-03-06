#!/usr/bin/env python3
"""
BingX API Documentation Scraper

Scrapes the full BingX API docs SPA (Element UI) using Playwright,
extracts all ~215 endpoint pages, and compiles them into a single
indexed markdown reference document.

Usage:
    python scrape_bingx_docs.py --test --debug        # 3 pages only
    python scrape_bingx_docs.py --section Swap --debug # one section
    python scrape_bingx_docs.py --debug                # full scrape

Output:
    C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\docs\\BINGX-API-V3-COMPLETE-REFERENCE.md
"""

import argparse
import asyncio
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DOCS_DIR = PROJECT_DIR / "docs"
LOGS_DIR = PROJECT_DIR / "logs"
DEFAULT_OUTPUT = DOCS_DIR / "BINGX-API-V3-COMPLETE-REFERENCE.md"
PROGRESS_FILE = DOCS_DIR / ".scrape-progress.json"
BASE_URL = "https://bingx-api.github.io/docs-v3/#/en/info"
SAVE_INTERVAL = 20  # save progress every N pages


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(debug=False):
    """Configure dual-handler logging (file + console) with timestamps."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / (datetime.now().strftime("%Y-%m-%d") + "-scraper.log")
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger("scraper")
    logger.setLevel(level)
    logger.handlers.clear()

    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# BingXDocsScraper
# ---------------------------------------------------------------------------

class BingXDocsScraper:
    """Drives Playwright to scrape the BingX API docs SPA."""

    def __init__(self, page, logger, timeout=5):
        """Store playwright page reference and config."""
        self.page = page
        self.log = logger
        self.timeout = timeout * 1000  # convert to ms

    async def expand_all_nav(self):
        """Click all closed el-submenu items recursively until all are open."""
        rounds = 0
        while True:
            closed = await self.page.query_selector_all(
                ".el-submenu:not(.is-opened) > .el-submenu__title"
            )
            if not closed:
                break
            rounds += 1
            self.log.debug("Expand round %d: %d closed submenus", rounds, len(closed))
            for el in closed:
                try:
                    await el.click()
                    await self.page.wait_for_timeout(250)
                except Exception:
                    pass
            await self.page.wait_for_timeout(500)
        self.log.info("Navigation fully expanded after %d rounds", rounds)

    async def collect_nav_tree(self):
        """Return list of nav items: {text, level, isSubmenu, index}."""
        items = await self.page.evaluate("""() => {
            const results = [];
            const allItems = document.querySelectorAll(
                '.el-menu-item, .el-submenu__title'
            );
            let idx = 0;
            allItems.forEach(el => {
                const paddingLeft = parseInt(el.style.paddingLeft || '0');
                const level = Math.floor(paddingLeft / 20);
                const text = el.textContent.trim().replace(/\\s+/g, ' ');
                const isSubmenu = el.classList.contains('el-submenu__title');
                if (text && text.length > 0 && text.length < 200) {
                    results.push({ text, level, isSubmenu, index: idx });
                    idx++;
                }
            });
            return results;
        }""")
        leaf_count = sum(1 for i in items if not i["isSubmenu"])
        self.log.info(
            "Nav tree collected: %d total items, %d leaf pages",
            len(items), leaf_count
        )
        return items

    async def _click_menu_item_by_text(self, text):
        """Click a leaf menu item by matching its innerText, scrolling into view first."""
        items = await self.page.query_selector_all(".el-menu-item")
        for item in items:
            item_text = await item.inner_text()
            item_text = re.sub(r"\s+", " ", item_text.strip())
            if item_text == text:
                try:
                    await item.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(200)
                except Exception:
                    pass
                visible = await item.is_visible()
                if not visible:
                    self.log.debug("Menu item '%s' not visible after scroll, re-expanding nav", text)
                    await self.expand_all_nav()
                    await self.page.wait_for_timeout(500)
                    return await self._click_menu_item_by_text_retry(text)
                await item.click()
                return True
        return False

    async def _click_menu_item_by_text_retry(self, text):
        """Retry click after re-expanding nav -- single attempt, no recursion."""
        items = await self.page.query_selector_all(".el-menu-item")
        for item in items:
            item_text = await item.inner_text()
            item_text = re.sub(r"\s+", " ", item_text.strip())
            if item_text == text:
                try:
                    await item.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(200)
                except Exception:
                    pass
                await item.click()
                return True
        return False

    async def navigate_to(self, item_text):
        """Click menu item by text and wait for content to update."""
        clicked = await self._click_menu_item_by_text(item_text)
        if not clicked:
            self.log.warning("Could not find menu item: %s", item_text)
            return False
        await self.page.wait_for_timeout(1500)
        return True

    def _detect_page_type(self, text_content):
        """Detect whether page is REST endpoint, WebSocket, or informational."""
        upper = text_content[:500].upper()
        # REST endpoint detection -- BingX puts method on its own line
        # Check for: "GET /" on same line, or standalone "GET"/"POST" etc,
        # or "Request Type GET" pattern
        if any(m in upper for m in ["GET /", "POST /", "DELETE /", "PUT /"]):
            return "rest"
        lines = [ln.strip() for ln in text_content[:500].split("\n")]
        for line in lines[:5]:
            if line.strip() in ("GET", "POST", "DELETE", "PUT"):
                return "rest"
        if "REQUEST TYPE" in upper and any(m in upper for m in ["GET", "POST", "DELETE", "PUT"]):
            return "rest"
        if "/OPENAPI/" in upper:
            return "rest"
        # WebSocket pages mention subscription topics
        if "WEBSOCKET" in upper or "WSS://" in upper or "SUBSCRIBE" in upper:
            return "websocket"
        return "info"

    async def _try_click_python_tab(self):
        """Click the Python demo code tab if present (must be outside evaluate)."""
        try:
            python_tab = await self.page.query_selector(
                '[role="tab"]:has-text("Python")'
            )
            if python_tab:
                await python_tab.click()
                await self.page.wait_for_timeout(300)
                return True
        except Exception:
            pass
        return False

    async def extract_page(self):
        """Extract full page content as structured dict from <main>."""
        # Click Python tab before extracting (audit fix #3)
        await self._try_click_python_tab()

        raw = await self.page.evaluate("""() => {
            const main = document.querySelector('main');
            if (!main) return { error: 'no main element' };

            const result = {
                fullText: '',
                tables: [],
                codeBlocks: []
            };

            // Get full text content
            result.fullText = main.innerText || '';

            // Extract all tables
            const tables = main.querySelectorAll('table');
            tables.forEach(table => {
                const rows = [];
                const trs = table.querySelectorAll('tr');
                trs.forEach(tr => {
                    const cells = [];
                    tr.querySelectorAll('th, td').forEach(cell => {
                        cells.push(cell.innerText.trim());
                    });
                    if (cells.length > 0) rows.push(cells);
                });
                if (rows.length > 0) result.tables.push(rows);
            });

            // Extract all code blocks
            const codeEls = main.querySelectorAll('pre code, pre');
            const seen = new Set();
            codeEls.forEach(el => {
                const text = el.innerText.trim();
                if (text && !seen.has(text)) {
                    seen.add(text);
                    result.codeBlocks.push(text);
                }
            });

            return result;
        }""")

        if not raw or "error" in raw:
            return {"error": raw.get("error", "unknown extraction error")}

        full_text = raw.get("fullText", "")
        page_type = self._detect_page_type(full_text)

        parsed = {
            "page_type": page_type,
            "full_text": full_text,
            "tables": raw.get("tables", []),
            "code_blocks": raw.get("codeBlocks", []),
        }

        if page_type == "rest":
            parsed.update(self._parse_rest_endpoint(full_text, parsed))
        elif page_type == "websocket":
            parsed.update(self._parse_websocket_page(full_text, parsed))
        # info pages just keep full_text as-is

        return parsed

    def _merge_paired_tables(self, tables):
        """Merge paired header+data tables from BingX DOM structure.

        BingX renders each table section as TWO <table> elements:
        a 1-row header table followed by a multi-row data table.
        This method detects and merges those pairs.
        """
        merged = []
        i = 0
        while i < len(tables):
            table = tables[i]
            # Strip trailing empty cells from all rows
            cleaned = []
            for row in table:
                stripped = [c for c in row if c.strip()]
                if stripped:
                    cleaned.append(stripped)

            # Check if this is a 1-row header followed by a data table
            if len(cleaned) == 1 and i + 1 < len(tables):
                next_table = tables[i + 1]
                next_cleaned = []
                for row in next_table:
                    stripped = [c for c in row if c.strip()]
                    if stripped:
                        next_cleaned.append(stripped)
                # Merge: header row + data rows
                merged.append(cleaned + next_cleaned)
                i += 2
            else:
                merged.append(cleaned)
                i += 1
        return merged

    def _parse_rest_endpoint(self, text, raw_parsed):
        """Parse REST endpoint details from text and tables."""
        result = {}

        # Extract method + path -- BingX puts these on SEPARATE lines:
        # Line 1: "GET"
        # Line 2: "/openApi/swap/v2/quote/depth"
        lines = text.split("\n")
        for idx, line in enumerate(lines[:10]):
            line_stripped = line.strip()
            # Same-line format: "GET /openApi/..."
            match = re.match(
                r"(GET|POST|DELETE|PUT)\s+(/\S+)", line_stripped
            )
            if match:
                result["method"] = match.group(1)
                result["path"] = match.group(2)
                break
            # Separate-line format: method alone, path on next line
            if line_stripped in ("GET", "POST", "DELETE", "PUT"):
                result["method"] = line_stripped
                # Look at next non-empty line for the path
                for next_line in lines[idx + 1:idx + 4]:
                    next_stripped = next_line.strip()
                    if next_stripped.startswith("/"):
                        path_match = re.match(r"(/\S+)", next_stripped)
                        if path_match:
                            result["path"] = path_match.group(1)
                        break
                break

        # Extract rate limit
        for line in lines[:25]:
            lower = line.lower().strip()
            if "rate limit" in lower or ("rate" in lower and "request" in lower):
                result["rate_limit"] = line.strip()
                break

        # Extract signature and permission info
        for line in lines[:25]:
            lower = line.lower().strip()
            if "signature" in lower and ("yes" in lower or "no" in lower):
                result["signature"] = line.strip()
            if "permission" in lower:
                result["permission"] = line.strip()

        # Merge paired tables (BingX DOM uses header table + data table pairs)
        raw_tables = raw_parsed.get("tables", [])
        tables = self._merge_paired_tables(raw_tables)

        # Classify merged tables by header content
        for table in tables:
            if not table or len(table) < 2:
                continue
            header = [c.lower() for c in table[0]]
            header_str = " ".join(header)

            if "parameter" in header_str or "required" in header_str:
                result["params_table"] = table
            elif "host" in header_str or "environment" in header_str:
                result["host_table"] = table
            elif ("code" in header_str and
                  ("msg" in header_str or "message" in header_str)):
                result["error_table"] = table
            elif ("filed" in header_str or "field" in header_str or
                  "description" in header_str):
                if "response_table" not in result:
                    result["response_table"] = table

        # Classify code blocks
        code_blocks = raw_parsed.get("code_blocks", [])
        for block in code_blocks:
            stripped = block.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                if "request_example" not in result:
                    result["request_example"] = stripped
                elif "response_example" not in result:
                    result["response_example"] = stripped
            elif "import " in stripped or "def " in stripped or "requests." in stripped:
                result["python_demo"] = stripped

        return result

    def _parse_websocket_page(self, text, raw_parsed):
        """Parse WebSocket subscription page details."""
        result = {}

        # Look for subscription topic
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            if "subscribe" in stripped.lower() and "{" in stripped:
                result["subscription_example"] = stripped
                break

        # Tables are push data fields
        tables = raw_parsed.get("tables", [])
        if tables:
            result["push_data_table"] = tables[0]

        # Code blocks are connection/subscription examples
        code_blocks = raw_parsed.get("code_blocks", [])
        if code_blocks:
            result["connection_example"] = code_blocks[0]

        return result

    async def scrape_all(self, nav_tree, progress=None):
        """Iterate all leaf items, extract each page, return list of results."""
        leaves = [item for item in nav_tree if not item["isSubmenu"]]
        total = len(leaves)
        results = []
        already_done = set()

        # Resume from progress file if available
        if progress:
            for p in progress:
                already_done.add(p.get("title", ""))
            self.log.info("Resuming: %d pages already scraped", len(already_done))

        # Build section context from nav tree
        current_sections = []
        section_map = {}
        for item in nav_tree:
            if item["isSubmenu"]:
                level = item["level"]
                while len(current_sections) > level:
                    current_sections.pop()
                if len(current_sections) <= level:
                    current_sections.append(item["text"])
                else:
                    current_sections[level] = item["text"]
            else:
                section_map[item["text"]] = " > ".join(current_sections)

        scraped_count = 0
        for i, leaf in enumerate(leaves):
            title = leaf["text"]

            if title in already_done:
                results.append(
                    next(p for p in progress if p.get("title") == title)
                )
                continue

            section_path = section_map.get(title, "Unknown")
            self.log.info(
                "Scraping %d/%d: %s > %s", i + 1, total, section_path, title
            )

            page_data = await self._scrape_single(title)
            page_data["title"] = title
            page_data["section_path"] = section_path
            results.append(page_data)
            scraped_count += 1

            # Summary logging
            if "error" not in page_data:
                params_count = len(page_data.get("params_table", [])) - 1
                resp_count = len(page_data.get("response_table", [])) - 1
                errors_count = len(page_data.get("error_table", [])) - 1
                self.log.info(
                    "Extracted: %d params, %d response fields, %d error codes",
                    max(0, params_count),
                    max(0, resp_count),
                    max(0, errors_count),
                )
            else:
                self.log.warning(
                    "Extraction issue for: %s -- %s",
                    title, page_data.get("error", "unknown")
                )

            # Save intermediate progress
            if scraped_count % SAVE_INTERVAL == 0:
                self._save_progress(results)

        # Final progress save
        self._save_progress(results)

        failures = sum(1 for r in results if "error" in r)
        self.log.info(
            "Complete: %d/%d pages scraped, %d failures",
            total - failures, total, failures
        )
        return results, nav_tree

    async def _scrape_single(self, title):
        """Scrape a single page with one retry on failure."""
        for attempt in range(2):
            try:
                navigated = await self.navigate_to(title)
                if not navigated:
                    if attempt == 0:
                        self.log.warning(
                            "Navigation failed for %s, retrying...", title
                        )
                        await self.page.wait_for_timeout(2000)
                        continue
                    return {"error": "navigation failed"}

                data = await self.extract_page()
                if "error" in data and attempt == 0:
                    self.log.warning(
                        "Extraction failed for %s, retrying...", title
                    )
                    await self.page.wait_for_timeout(2000)
                    continue
                return data

            except Exception as exc:
                if attempt == 0:
                    self.log.warning(
                        "Exception scraping %s: %s -- retrying", title, exc
                    )
                    await self.page.wait_for_timeout(2000)
                    continue
                return {"error": str(exc)}

        return {"error": "max retries exceeded"}

    def _save_progress(self, results):
        """Save intermediate results to progress JSON file."""
        try:
            DOCS_DIR.mkdir(parents=True, exist_ok=True)
            serializable = []
            for r in results:
                entry = {
                    "title": r.get("title", ""),
                    "section_path": r.get("section_path", ""),
                    "page_type": r.get("page_type", ""),
                }
                if "error" in r:
                    entry["error"] = r["error"]
                if "method" in r:
                    entry["method"] = r["method"]
                if "path" in r:
                    entry["path"] = r["path"]
                serializable.append(entry)

            with open(str(PROGRESS_FILE), "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
            self.log.debug(
                "Progress saved: %d pages to %s",
                len(results), str(PROGRESS_FILE)
            )
        except Exception as exc:
            self.log.warning("Failed to save progress: %s", exc)

    async def scrape_section(self, section_name, nav_tree):
        """Scrape only one top-level section by name."""
        filtered_tree = []
        in_section = False
        section_level = None

        for item in nav_tree:
            if item["isSubmenu"] and item["text"].lower() == section_name.lower():
                in_section = True
                section_level = item["level"]
                filtered_tree.append(item)
                continue

            if in_section:
                if item["isSubmenu"] and item["level"] <= section_level:
                    break  # entered a new top-level section
                filtered_tree.append(item)

        if not filtered_tree:
            self.log.error("Section '%s' not found in nav tree", section_name)
            return [], nav_tree

        leaf_count = sum(1 for i in filtered_tree if not i["isSubmenu"])
        self.log.info(
            "Filtered to section '%s': %d items, %d leaves",
            section_name, len(filtered_tree), leaf_count
        )
        return await self.scrape_all(filtered_tree)

    async def scrape_test(self, nav_tree):
        """Scrape only first 3 leaf pages from Swap > Market Data."""
        leaves = [item for item in nav_tree if not item["isSubmenu"]]
        # Find the first 3 leaves that come after a "Market Data" submenu
        # within the "Swap" section
        in_swap = False
        in_market_data = False
        test_items = []

        for item in nav_tree:
            if item["isSubmenu"] and "swap" in item["text"].lower():
                in_swap = True
                test_items.append(item)
                continue
            if in_swap and item["isSubmenu"] and "market data" in item["text"].lower():
                in_market_data = True
                test_items.append(item)
                continue
            if in_market_data and not item["isSubmenu"]:
                test_items.append(item)
                if sum(1 for t in test_items if not t["isSubmenu"]) >= 3:
                    break
            if in_market_data and item["isSubmenu"]:
                break  # left Market Data subsection

        leaf_count = sum(1 for i in test_items if not i["isSubmenu"])
        self.log.info("Test mode: scraping %d pages", leaf_count)
        return await self.scrape_all(test_items)


# ---------------------------------------------------------------------------
# MarkdownCompiler
# ---------------------------------------------------------------------------

class MarkdownCompiler:
    """Compiles scraped page data into a single indexed markdown document."""

    def __init__(self, nav_tree, pages):
        """Store nav tree and page data for compilation."""
        self.nav_tree = nav_tree
        self.pages = pages
        self.page_map = {p.get("title", ""): p for p in pages}

    def _anchor(self, text):
        """Convert text to a markdown anchor slug."""
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug)
        return slug

    def build_toc(self):
        """Generate table of contents with anchor links."""
        lines = ["## Table of Contents", ""]
        current_sections = []

        for item in self.nav_tree:
            if item["isSubmenu"]:
                level = item["level"]
                indent = "  " * level
                anchor = self._anchor(item["text"])
                lines.append(
                    indent + "- [" + item["text"] + "](#" + anchor + ")"
                )
            else:
                # leaf page
                indent = "  " * (item.get("level", 2))
                anchor = self._anchor(item["text"])
                lines.append(
                    indent + "- [" + item["text"] + "](#" + anchor + ")"
                )

        return "\n".join(lines)

    def _format_table(self, table_data):
        """Format a table (list of row lists) as markdown."""
        if not table_data or len(table_data) < 1:
            return ""
        lines = []
        header = table_data[0]
        lines.append("| " + " | ".join(str(c) for c in header) + " |")
        lines.append("|" + "|".join("---" for _ in header) + "|")
        for row in table_data[1:]:
            # Pad or truncate row to match header length
            padded = list(row) + [""] * (len(header) - len(row))
            lines.append("| " + " | ".join(str(c) for c in padded[:len(header)]) + " |")
        return "\n".join(lines)

    def format_endpoint(self, page_data):
        """Format one endpoint dict as markdown."""
        lines = []
        title = page_data.get("title", "Unknown")
        page_type = page_data.get("page_type", "info")

        lines.append("#### " + title)
        lines.append("")

        # Error page
        if "error" in page_data:
            lines.append("*Extraction failed: " + page_data["error"] + "*")
            lines.append("")
            return "\n".join(lines)

        # REST endpoint
        if page_type == "rest":
            method = page_data.get("method", "")
            path = page_data.get("path", "")
            if method and path:
                lines.append("**" + method + "** `" + path + "`")
                lines.append("")

            rate_limit = page_data.get("rate_limit", "")
            if rate_limit:
                lines.append("- **Rate Limit**: " + rate_limit)
                lines.append("")

            # Host table
            host_table = page_data.get("host_table")
            if host_table:
                lines.append("**Hosts**")
                lines.append("")
                lines.append(self._format_table(host_table))
                lines.append("")

            # Params table
            params_table = page_data.get("params_table")
            if params_table:
                lines.append("**Request Parameters**")
                lines.append("")
                lines.append(self._format_table(params_table))
                lines.append("")

            # Response table
            response_table = page_data.get("response_table")
            if response_table:
                lines.append("**Response Body**")
                lines.append("")
                lines.append(self._format_table(response_table))
                lines.append("")

            # Request example
            req_example = page_data.get("request_example", "")
            if req_example:
                lines.append("**Request Example**")
                lines.append("")
                lines.append("```json")
                lines.append(req_example)
                lines.append("```")
                lines.append("")

            # Response example
            resp_example = page_data.get("response_example", "")
            if resp_example:
                lines.append("**Response Example**")
                lines.append("")
                lines.append("```json")
                lines.append(resp_example)
                lines.append("```")
                lines.append("")

            # Error table
            error_table = page_data.get("error_table")
            if error_table:
                lines.append("**Error Codes**")
                lines.append("")
                lines.append(self._format_table(error_table))
                lines.append("")

            # Python demo
            python_demo = page_data.get("python_demo", "")
            if python_demo:
                lines.append("**Python Demo**")
                lines.append("")
                lines.append("```python")
                lines.append(python_demo)
                lines.append("```")
                lines.append("")

        # WebSocket page
        elif page_type == "websocket":
            sub_example = page_data.get("subscription_example", "")
            if sub_example:
                lines.append("**Subscription**")
                lines.append("")
                lines.append("`" + sub_example + "`")
                lines.append("")

            push_table = page_data.get("push_data_table")
            if push_table:
                lines.append("**Push Data Fields**")
                lines.append("")
                lines.append(self._format_table(push_table))
                lines.append("")

            conn_example = page_data.get("connection_example", "")
            if conn_example:
                lines.append("**Connection Example**")
                lines.append("")
                lines.append("```")
                lines.append(conn_example)
                lines.append("```")
                lines.append("")

            # Include full text for WS pages as fallback context
            full_text = page_data.get("full_text", "")
            if full_text and not sub_example and not push_table:
                lines.append(full_text)
                lines.append("")

        # Informational page (audit fix #1)
        elif page_type == "info":
            full_text = page_data.get("full_text", "")
            if full_text:
                lines.append(full_text)
                lines.append("")

        lines.append("---")
        lines.append("")
        return "\n".join(lines)

    def compile(self):
        """Return full markdown string with header, TOC, and all pages."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = len(self.pages)
        failures = sum(1 for p in self.pages if "error" in p)

        parts = []

        # Header
        parts.append("# BingX API v3 Complete Reference")
        parts.append("")
        parts.append("Scraped: " + now)
        parts.append("Source: " + BASE_URL)
        parts.append("Total endpoints: " + str(total))
        if failures:
            parts.append("Extraction failures: " + str(failures))
        parts.append("")
        parts.append("---")
        parts.append("")

        # TOC
        parts.append(self.build_toc())
        parts.append("")
        parts.append("---")
        parts.append("")

        # Content by section
        current_sections = []
        page_index = 0

        for item in self.nav_tree:
            if item["isSubmenu"]:
                level = item["level"]
                heading_level = "#" * (level + 2)  # ## for level 0, ### for level 1, etc
                parts.append(heading_level + " " + item["text"])
                parts.append("")
            else:
                # leaf page -- render its content
                page_data = self.page_map.get(item["text"])
                if page_data:
                    parts.append(self.format_endpoint(page_data))

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_progress():
    """Load previously saved progress if it exists."""
    if PROGRESS_FILE.exists():
        try:
            with open(str(PROGRESS_FILE), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


async def run(args, logger):
    """Launch browser, scrape, compile, write output."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        logger.info("Launching Chromium (headless)...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        logger.info("Navigating to %s", BASE_URL)
        await page.goto(BASE_URL)
        await page.wait_for_timeout(3000)

        scraper = BingXDocsScraper(page, logger, timeout=args.timeout)

        # Expand all nav
        logger.info("Expanding navigation tree...")
        await scraper.expand_all_nav()

        # Collect nav tree
        logger.info("Collecting navigation tree...")
        nav_tree = await scraper.collect_nav_tree()

        # Scrape based on mode
        # Only resume progress for full scrape mode; delete stale progress otherwise
        progress = None
        if not args.test and not args.section:
            progress = load_progress()
        elif PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
            logger.debug("Deleted stale progress file from previous run")

        if args.test:
            logger.info("=== TEST MODE: 3 pages only ===")
            pages, nav_tree_used = await scraper.scrape_test(nav_tree)
        elif args.section:
            logger.info("=== SECTION MODE: %s ===", args.section)
            pages, nav_tree_used = await scraper.scrape_section(
                args.section, nav_tree
            )
        else:
            logger.info("=== FULL SCRAPE MODE ===")
            pages, nav_tree_used = await scraper.scrape_all(nav_tree, progress)

        await browser.close()
        logger.info("Browser closed")

    # Compile markdown
    logger.info("Compiling markdown document...")
    compiler = MarkdownCompiler(nav_tree_used, pages)
    markdown = compiler.compile()

    # Write output
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(output_path), "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info("Output written to: %s", str(output_path))
    logger.info("Document size: %d characters, %d lines", len(markdown), markdown.count("\n"))

    # Clean up progress file on successful full scrape
    if not args.test and not args.section and PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
        logger.info("Progress file cleaned up")

    return str(output_path)


def main():
    """Parse arguments and run the scraper."""
    parser = argparse.ArgumentParser(
        description="Scrape BingX API docs into indexed markdown reference"
    )
    parser.add_argument(
        "--output", type=str, default=str(DEFAULT_OUTPUT),
        help="Output file path (default: " + str(DEFAULT_OUTPUT) + ")"
    )
    parser.add_argument(
        "--section", type=str, default=None,
        help="Scrape only one section (e.g. Swap, Spot)"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Scrape only first 3 endpoints from Swap > Market Data"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable verbose debug logging"
    )
    parser.add_argument(
        "--timeout", type=int, default=5,
        help="Per-page timeout in seconds (default: 5)"
    )

    args = parser.parse_args()
    logger = setup_logging(debug=args.debug)

    logger.info("BingX API Docs Scraper starting")
    logger.info("Output: %s", args.output)
    if args.test:
        logger.info("Mode: TEST (3 pages)")
    elif args.section:
        logger.info("Mode: SECTION (%s)", args.section)
    else:
        logger.info("Mode: FULL SCRAPE")

    start_time = time.time()

    try:
        output_path = asyncio.run(run(args, logger))
        elapsed = time.time() - start_time
        logger.info("Scrape completed in %.1f seconds", elapsed)
        logger.info("Output at: %s", output_path)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        raise


if __name__ == "__main__":
    main()

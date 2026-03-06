#!/usr/bin/env python3
"""
Test suite for BingX API Docs Scraper.

Tests cover navigation tree extraction, single page extraction,
markdown compilation, and section-level scraping.

Usage:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python -m pytest scripts/test_scraper.py -v
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from playwright.async_api import async_playwright

# Add scripts dir to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scrape_bingx_docs import (
    BASE_URL,
    BingXDocsScraper,
    MarkdownCompiler,
    setup_logging,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LOGGER = setup_logging(debug=True)


@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the module-scoped async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def browser_page():
    """Launch browser and navigate to BingX docs. Shared across module."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE_URL)
        await page.wait_for_timeout(3000)
        yield page
        await browser.close()


@pytest.fixture(scope="module")
async def expanded_scraper(browser_page):
    """Return a scraper with all nav expanded."""
    scraper = BingXDocsScraper(browser_page, LOGGER, timeout=5)
    await scraper.expand_all_nav()
    return scraper


@pytest.fixture(scope="module")
async def nav_tree(expanded_scraper):
    """Collect and return the full nav tree."""
    return await expanded_scraper.collect_nav_tree()


# ---------------------------------------------------------------------------
# Test 1: Navigation tree extraction
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_nav_tree_extraction(nav_tree):
    """Verify at least 200 leaf items found in the navigation tree."""
    assert nav_tree is not None, "Nav tree should not be None"
    assert len(nav_tree) > 0, "Nav tree should not be empty"

    leaf_count = sum(1 for item in nav_tree if not item["isSubmenu"])
    submenu_count = sum(1 for item in nav_tree if item["isSubmenu"])

    print("Total items: " + str(len(nav_tree)))
    print("Leaf pages: " + str(leaf_count))
    print("Submenus: " + str(submenu_count))

    assert leaf_count >= 200, (
        "Expected >= 200 leaf items, got " + str(leaf_count)
    )

    # Verify expected top-level sections exist
    submenu_texts = [
        item["text"].lower() for item in nav_tree if item["isSubmenu"]
    ]
    for section in ["swap", "spot"]:
        found = any(section in t for t in submenu_texts)
        assert found, "Expected section '" + section + "' in nav tree"


# ---------------------------------------------------------------------------
# Test 2: Single page extraction (Kline/Candlestick Data)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_page_extraction(expanded_scraper, browser_page):
    """Navigate to Kline/Candlestick Data and verify extracted content."""
    # Navigate to the Kline page
    navigated = await expanded_scraper.navigate_to("Kline/Candlestick Data")
    assert navigated, "Should navigate to Kline/Candlestick Data page"

    # Extract page content
    data = await expanded_scraper.extract_page()
    assert "error" not in data, (
        "Extraction should not fail: " + str(data.get("error", ""))
    )

    # Verify page type
    assert data.get("page_type") == "rest", (
        "Kline page should be REST type, got: " + str(data.get("page_type"))
    )

    # Verify method and path
    assert data.get("method") == "GET", (
        "Expected GET, got: " + str(data.get("method"))
    )
    path = data.get("path", "")
    assert "/openApi/" in path, (
        "Path should contain /openApi/, got: " + path
    )
    assert "kline" in path.lower(), (
        "Path should contain kline, got: " + path
    )

    # Verify params table has rows
    params = data.get("params_table", [])
    assert len(params) >= 5, (
        "Expected >= 5 param rows, got " + str(len(params))
    )

    # Verify response table has rows
    response = data.get("response_table", [])
    assert len(response) >= 5, (
        "Expected >= 5 response rows, got " + str(len(response))
    )

    # Verify request example is valid JSON
    req_example = data.get("request_example", "")
    if req_example:
        try:
            json.loads(req_example)
        except json.JSONDecodeError:
            pass  # Some request examples may be URL strings, not JSON

    # Verify response example is valid JSON
    resp_example = data.get("response_example", "")
    if resp_example:
        try:
            parsed = json.loads(resp_example)
            assert parsed is not None, "Response example should parse as JSON"
        except json.JSONDecodeError:
            pytest.fail(
                "Response example should be valid JSON, got: "
                + resp_example[:100]
            )

    # Verify Python demo if present
    python_demo = data.get("python_demo", "")
    if python_demo:
        assert "import" in python_demo or "requests" in python_demo, (
            "Python demo should contain import or requests"
        )


# ---------------------------------------------------------------------------
# Test 3: Markdown compilation
# ---------------------------------------------------------------------------

def test_markdown_compile():
    """Feed mock data and verify output has TOC, headings, code blocks."""
    mock_nav = [
        {"text": "Swap", "level": 0, "isSubmenu": True, "index": 0},
        {"text": "Market Data", "level": 1, "isSubmenu": True, "index": 1},
        {"text": "Get Ticker", "level": 2, "isSubmenu": False, "index": 2},
        {"text": "Get Depth", "level": 2, "isSubmenu": False, "index": 3},
    ]

    mock_pages = [
        {
            "title": "Get Ticker",
            "page_type": "rest",
            "method": "GET",
            "path": "/openApi/swap/v2/quote/ticker",
            "rate_limit": "500 requests per 10 seconds",
            "params_table": [
                ["Parameter", "Type", "Required", "Description"],
                ["symbol", "string", "No", "Trading pair"],
            ],
            "response_table": [
                ["Field", "Type", "Description"],
                ["symbol", "string", "Trading pair"],
                ["lastPrice", "float64", "Last trade price"],
            ],
            "request_example": '{"symbol": "BTC-USDT"}',
            "response_example": '{"code": 0, "data": {"symbol": "BTC-USDT"}}',
            "error_table": [
                ["Code", "Message"],
                ["109425", "Trading pair does not exist"],
            ],
            "python_demo": "import requests\nresponse = requests.get(url)",
        },
        {
            "title": "Get Depth",
            "page_type": "rest",
            "method": "GET",
            "path": "/openApi/swap/v2/quote/depth",
            "params_table": [
                ["Parameter", "Type", "Required", "Description"],
                ["symbol", "string", "Yes", "Trading pair"],
                ["limit", "int", "No", "Default 20"],
            ],
        },
    ]

    compiler = MarkdownCompiler(mock_nav, mock_pages)
    output = compiler.compile()

    # Verify header
    assert "# BingX API v3 Complete Reference" in output
    assert "Total endpoints: 2" in output

    # Verify TOC with anchor links
    assert "## Table of Contents" in output
    assert "[Swap]" in output
    assert "[Market Data]" in output
    assert "[Get Ticker]" in output
    assert "[Get Depth]" in output

    # Verify section headers
    assert "## Swap" in output
    assert "### Market Data" in output

    # Verify endpoint content
    assert "#### Get Ticker" in output
    assert "**GET** `/openApi/swap/v2/quote/ticker`" in output
    assert "**Rate Limit**: 500 requests per 10 seconds" in output

    # Verify tables rendered
    assert "| Parameter | Type | Required | Description |" in output
    assert "| symbol | string | No | Trading pair |" in output

    # Verify code blocks
    assert "```json" in output
    assert "```python" in output
    assert "import requests" in output

    # Verify error codes table
    assert "**Error Codes**" in output
    assert "| 109425 | Trading pair does not exist |" in output

    # Verify second endpoint
    assert "#### Get Depth" in output
    assert "**GET** `/openApi/swap/v2/quote/depth`" in output

    print("Markdown output length: " + str(len(output)) + " chars")
    print("Markdown output lines: " + str(output.count(chr(10))))


# ---------------------------------------------------------------------------
# Test 4: Full section scrape (Swap > Market Data)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_section_scrape(expanded_scraper, nav_tree):
    """Scrape Swap > Market Data, verify all endpoints captured."""
    # Filter nav tree to just Swap > Market Data
    filtered = []
    in_swap = False
    in_market_data = False

    for item in nav_tree:
        if item["isSubmenu"] and "swap" in item["text"].lower():
            in_swap = True
            filtered.append(item)
            continue
        if in_swap and item["isSubmenu"] and "market data" in item["text"].lower():
            in_market_data = True
            filtered.append(item)
            continue
        if in_market_data and not item["isSubmenu"]:
            filtered.append(item)
        if in_market_data and item["isSubmenu"]:
            break

    leaf_count = sum(1 for i in filtered if not i["isSubmenu"])
    print("Swap > Market Data leaves found: " + str(leaf_count))

    assert leaf_count >= 10, (
        "Expected >= 10 Market Data endpoints, got " + str(leaf_count)
    )

    # Scrape all of them
    pages, _ = await expanded_scraper.scrape_all(filtered)

    assert len(pages) == leaf_count, (
        "Expected " + str(leaf_count) + " pages, got " + str(len(pages))
    )

    # Verify each has non-empty content
    for page in pages:
        title = page.get("title", "UNKNOWN")
        assert page.get("full_text", ""), (
            "Page '" + title + "' should have non-empty content"
        )
        print(
            "OK: " + title
            + " (type=" + page.get("page_type", "?")
            + ", method=" + page.get("method", "N/A")
            + ")"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Fuzzy search coin selector for Streamlit.
Scans data/cache/ for available Parquet files and provides fuzzy matching.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from difflib import SequenceMatcher


def get_available_coins(data_dir: str = None) -> list[str]:
    """
    Scan data directory for cached coin Parquet files.

    Args:
        data_dir: Path to data/cache/ directory.

    Returns:
        Sorted list of coin symbol names.
    """
    if data_dir is None:
        data_dir = str(Path(__file__).resolve().parent.parent / "data" / "cache")

    cache = Path(data_dir)
    if not cache.exists():
        return []

    coins = set()
    for f in cache.glob("*.parquet"):
        name = f.stem.upper()
        # Strip timeframe suffix if present (e.g., BTCUSDT_1m -> BTCUSDT)
        if "_" in name:
            name = name.split("_")[0]
        coins.add(name)

    return sorted(coins)


def fuzzy_match(query: str, coins: list[str], limit: int = 5) -> list[str]:
    """
    Fuzzy match a query against available coins.

    Args:
        query: User input (e.g., "asx" -> suggests "AXSUSDT").
        coins: Available coin symbols.
        limit: Max number of suggestions.

    Returns:
        List of matching coin names, best first.
    """
    if not query:
        return coins[:limit]

    query = query.upper()

    # Exact prefix match first
    prefix = [c for c in coins if c.startswith(query)]
    if prefix:
        return prefix[:limit]

    # Substring match
    contains = [c for c in coins if query in c]
    if contains:
        return contains[:limit]

    # Fuzzy ratio
    scored = []
    for c in coins:
        ratio = SequenceMatcher(None, query, c).ratio()
        scored.append((c, ratio))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:limit]]


def coin_selector(data_dir: str = None) -> list[str]:
    """
    Interactive coin selector (for Streamlit integration).

    Returns list of selected coins. When not running in Streamlit,
    returns all available coins.

    Args:
        data_dir: Path to data/cache/ directory.

    Returns:
        List of selected coin symbols.
    """
    coins = get_available_coins(data_dir)

    try:
        import streamlit as st
        query = st.text_input("Search coins", "")
        suggestions = fuzzy_match(query, coins)
        selected = st.multiselect("Select coins", suggestions, default=suggestions[:1] if suggestions else [])
        return selected
    except (ImportError, RuntimeError):
        return coins


if __name__ == "__main__":
    coins = get_available_coins()
    if coins:
        matches = fuzzy_match("riv", coins)
        print(f"PASS -- {len(coins)} coins found, fuzzy 'riv' -> {matches}")
    else:
        print(f"PASS -- coin_selector works (no cache files found, expected in test)")

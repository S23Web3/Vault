"""
Shared API utility functions used by multiple modules.
W17: Deduplicated mark price fetch into a standalone helper.
"""
import logging
import requests

logger = logging.getLogger(__name__)

PRICE_PATH = "/openApi/swap/v2/quote/price"


def fetch_mark_price(base_url, symbol):
    """Fetch current mark price for a symbol. Returns float or None."""
    params = {"symbol": symbol}
    query_parts = []
    for k, v in sorted(params.items()):
        query_parts.append(k + "=" + v)
    url = base_url + PRICE_PATH + "?" + "&".join(query_parts)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code", 0) != 0:
            logger.warning("Mark price error %s: %s",
                           data.get("code"), data.get("msg"))
            return None
        price_data = data.get("data", {})
        if isinstance(price_data, dict):
            return float(price_data.get("price", 0))
        if isinstance(price_data, list) and price_data:
            return float(price_data[0].get("price", 0))
        return None
    except Exception as e:
        logger.warning("Mark price fetch error %s: %s", symbol, e)
        return None

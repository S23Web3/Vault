"""
BingX ticker collector: fetch all perpetual futures tickers (no auth required).
Saves to CSV and prints top/bottom by volume.
Run: python scripts/run_ticker_collector.py
"""
import csv
import logging
import sys
from datetime import date
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
LOG_DIR  = ROOT / "logs"
TODAY    = date.today().strftime("%Y-%m-%d")
OUT_CSV  = LOG_DIR / ("bingx_tickers_" + TODAY + ".csv")

TICKER_URL = "https://open-api.bingx.com/openApi/swap/v2/quote/ticker"

# Live bot 47 coins for cross-reference
LIVE_COINS = {
    "SKR-USDT", "TRUTH-USDT", "RIVER-USDT", "STBL-USDT", "ZKP-USDT",
    "LYN-USDT", "BEAT-USDT", "GIGGLE-USDT", "PIPPIN-USDT", "FOLKS-USDT",
    "NAORIS-USDT", "Q-USDT", "ELSA-USDT", "UB-USDT", "THETA-USDT",
    "SAHARA-USDT", "TIA-USDT", "APT-USDT", "AIXBT-USDT", "GALA-USDT",
    "LDO-USDT", "SUSHI-USDT", "VET-USDT", "WAL-USDT", "WIF-USDT",
    "WOO-USDT", "ATOM-USDT", "BOME-USDT", "DYDX-USDT", "VIRTUAL-USDT",
    "BREV-USDT", "CYBER-USDT", "EIGEN-USDT", "MUBARAK-USDT", "1000PEPE-USDT",
    "DEEP-USDT", "ETHFI-USDT", "RENDER-USDT", "BB-USDT", "F-USDT",
    "GUN-USDT", "KAITO-USDT", "MEME-USDT", "PENDLE-USDT", "SCRT-USDT",
    "SQD-USDT", "STX-USDT",
}

# Beta candidate coins (user-provided, excluding ETH/BTC)
BETA_CANDIDATES = {
    "ENSO-USDT", "GRASS-USDT", "POWER-USDT", "VENICE-USDT", "SIREN-USDT",
    "FHE-USDT", "BTR-USDT", "OWC-USDT", "WARD-USDT", "WHITEWHALE-USDT",
    "ESP-USDT", "MUBARAK-USDT", "SAHARA-USDT",
    "INJ-USDT", "JTO-USDT", "JUP-USDT", "LINK-USDT", "LTC-USDT",
    "METAX-USDT", "MUS-USDT", "MYX-USDT", "NEAR-USDT", "ONDO-USDT",
    "PENGU-USDT", "POPCAT-USDT", "PUMP-USDT", "QNT-USDT", "SHIB1000-USDT",
    "SOL-USDT", "SUI-USDT", "UNI-USDT", "XRP-USDT", "ZEC-USDT", "ZEN-USDT",
    "1000PEPE-USDT", "APE-USDT", "APT-USDT", "ASTER-USDT", "AXS-USDT",
    "BANK-USDT", "BERAU-USDT", "BNB-USDT", "BONK-USDT",
    "DASH-USDT", "DOT-USDT", "FARTCOIN-USDT", "HMSTR-USDT", "IMX-USDT",
    "GIGGLE-USDT", "PIPPIN-USDT", "STBL-USDT", "BREV-USDT", "Q-USDT",
    "BEAT-USDT", "LYN-USDT", "TRUTH-USDT", "SKR-USDT",
}


def fetch_tickers() -> list[dict]:
    """Fetch all perpetual ticker data from BingX public API."""
    log.info("Fetching tickers from BingX...")
    try:
        resp = requests.get(TICKER_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.error("Fetch failed: %s", e)
        sys.exit(1)

    if data.get("code", -1) != 0:
        log.error("API error %s: %s", data.get("code"), data.get("msg"))
        sys.exit(1)

    raw = data.get("data", [])
    log.info("Received %d tickers", len(raw))

    tickers = []
    for t in raw:
        sym = t.get("symbol", "")
        if not sym.endswith("-USDT"):
            continue
        try:
            volume = float(t.get("quoteVolume") or t.get("volume") or 0)
            price  = float(t.get("lastPrice") or 0)
            chg    = float(t.get("priceChangePercent") or 0)
            oi     = float(t.get("openInterest") or 0)
        except (ValueError, TypeError):
            continue
        tickers.append({
            "symbol":           sym,
            "last_price":       price,
            "change_24h_pct":   chg,
            "quote_volume_24h": volume,
            "open_interest":    oi,
            "in_live_bot":      sym in LIVE_COINS,
            "in_beta":          sym in BETA_CANDIDATES,
        })

    tickers.sort(key=lambda x: x["quote_volume_24h"], reverse=True)
    return tickers


def main() -> None:
    """Fetch tickers, save CSV, print summary."""
    LOG_DIR.mkdir(exist_ok=True)
    tickers = fetch_tickers()

    # Assign rank
    for i, t in enumerate(tickers, 1):
        t["volume_rank"] = i

    # Write CSV
    fieldnames = ["volume_rank", "symbol", "last_price", "change_24h_pct",
                  "quote_volume_24h", "open_interest", "in_live_bot", "in_beta"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickers)
    log.info("CSV written: " + str(OUT_CSV))

    total = len(tickers)
    print("\n=== BINGX TICKER SUMMARY ===")
    print("Total USDT perpetuals: " + str(total))
    print("")
    print("TOP 20 by volume:")
    for t in tickers[:20]:
        tag = " [LIVE]" if t["in_live_bot"] else (" [BETA]" if t["in_beta"] else "")
        print("  #" + str(t["volume_rank"]) + " " + t["symbol"] + tag +
              "  vol=" + str(round(t["quote_volume_24h"] / 1e6, 1)) + "M")

    print("")
    print("BOTTOM 20 by volume (liquidity warning):")
    for t in tickers[-20:]:
        tag = " [LIVE]" if t["in_live_bot"] else (" [BETA]" if t["in_beta"] else "")
        print("  #" + str(t["volume_rank"]) + " " + t["symbol"] + tag +
              "  vol=" + str(round(t["quote_volume_24h"] / 1e6, 3)) + "M")

    print("")
    print("LIVE BOT coins by volume rank:")
    live_ranked = [t for t in tickers if t["in_live_bot"]]
    for t in live_ranked:
        pct = round(t["volume_rank"] / total * 100, 1)
        print("  #" + str(t["volume_rank"]) + "/" + str(total) +
              " (" + str(pct) + "%) " + t["symbol"])

    print("")
    print("BETA CANDIDATE coins by volume rank:")
    beta_ranked = [t for t in tickers if t["in_beta"]]
    for t in beta_ranked:
        pct = round(t["volume_rank"] / total * 100, 1)
        live_flag = " [OVERLAP-LIVE]" if t["in_live_bot"] else ""
        print("  #" + str(t["volume_rank"]) + "/" + str(total) +
              " (" + str(pct) + "%) " + t["symbol"] + live_flag)

    print("")
    print("CSV: " + str(OUT_CSV))


if __name__ == "__main__":
    main()

"""
Pre-flight check: verify all coins in config.yaml are listed on BingX perps.
Uses the public contracts endpoint — no API key required.

Run: python scripts/verify_coins.py

Exit 0 = all coins confirmed
Exit 1 = one or more coins not listed on BingX (fix config.yaml before restarting bot)
"""
import sys
import yaml
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_URL = "https://open-api.bingx.com/openApi/swap/v2/quote/contracts"


def load_coins():
    """Load coins list from config.yaml."""
    config_path = ROOT / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    coins = cfg.get("coins", [])
    if not coins:
        print("ERROR: No coins found in config.yaml")
        sys.exit(1)
    return coins


def fetch_contracts():
    """Fetch all available BingX perp contracts. Returns set of symbols."""
    print("Fetching BingX contracts...")
    try:
        resp = requests.get(CONTRACTS_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out (15s)")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection failed — check internet")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print("ERROR: HTTP " + str(e.response.status_code))
        sys.exit(1)
    except ValueError:
        print("ERROR: Invalid JSON response")
        sys.exit(1)

    if data.get("code", -1) != 0:
        print("ERROR: API error " + str(data.get("code"))
              + " — " + str(data.get("msg", "")))
        sys.exit(1)

    contracts = data.get("data", [])
    if not contracts:
        print("ERROR: Empty contracts list returned")
        sys.exit(1)

    symbol_set = {c["symbol"] for c in contracts if "symbol" in c}
    print("  " + str(len(symbol_set)) + " contracts available\n")
    return symbol_set


def main():
    """Check each config coin against the live BingX contracts list."""
    coins = load_coins()
    contracts = fetch_contracts()

    passed = []
    failed = []

    print("Checking config.yaml coins:")
    for coin in coins:
        if coin in contracts:
            print("  [PASS] " + coin)
            passed.append(coin)
        else:
            print("  [FAIL] " + coin + "  ← not listed on BingX perps")
            failed.append(coin)

    print()
    print("Result: " + str(len(passed)) + "/" + str(len(coins))
          + " coins confirmed on BingX.")

    if not failed:
        print("All coins verified. Ready to restart bot.")
        print()
        print("  python \""
              + str(ROOT / "main.py") + "\"")
        sys.exit(0)

    print()
    print("Action required: remove the FAIL coins from config.yaml before restarting.")
    print()
    print("Clean coins list (paste into config.yaml):")
    for coin in passed:
        print('  - "' + coin + '"')

    sys.exit(1)


if __name__ == "__main__":
    main()

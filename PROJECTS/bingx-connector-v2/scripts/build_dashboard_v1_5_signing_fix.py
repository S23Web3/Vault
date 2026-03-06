"""
Build script: BingX Dashboard v1.5 -- Signing Fix
Date: 2026-03-05

Root cause: Dashboard's _bingx_request() passes signed params dict to
requests.get(url, params=dict), which lets the requests library re-encode
the query string. This can reorder params vs. the signed query, causing
100001 "Signature verification failed".

Fix: Match bingx_auth.py's proven approach -- build the URL manually:
    url + '?' + sorted_query + '&signature=' + sig
and send requests with NO params kwarg.

Also aligns _sign() return type with bingx_auth.py (returns query+sig tuple,
converts timestamp to str).

Base: C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\bingx-live-dashboard-v1-5.py
"""

import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector")
TARGET = BASE / "bingx-live-dashboard-v1-5.py"

ERRORS = []
PATCHES_APPLIED = []


def safe_replace(content, old, new, label):
    """Replace exactly one occurrence of old with new. Appends to ERRORS on failure."""
    if old not in content:
        ERRORS.append(label + " FAILED: old string not found")
        return content
    count = content.count(old)
    if count != 1:
        ERRORS.append(label + " FAILED: expected 1 occurrence, found " + str(count))
        return content
    content = content.replace(old, new)
    PATCHES_APPLIED.append(label)
    print("  " + label + " applied")
    return content


def patch_file():
    """Apply signing fix patches to dashboard v1.5."""
    content = TARGET.read_text(encoding="utf-8")

    # ---------------------------------------------------------------
    # P1: Replace _sign() -- return (query, sig) tuple instead of
    #     mutating params dict. Convert timestamp to str (matches bot).
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "def _sign(params: dict) -> dict:\n"
        "    \"\"\"Add timestamp, recvWindow, HMAC-SHA256 signature to params dict (BUG-4 fix).\"\"\"\n"
        "    params['timestamp'] = synced_timestamp_ms()\n"
        "    params['recvWindow'] = '10000'\n"
        "    query = '&'.join(k + '=' + str(v) for k, v in sorted(params.items()))\n"
        "    sig = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()\n"
        "    params['signature'] = sig\n"
        "    return params",
        "def _sign(params: dict) -> tuple:\n"
        "    \"\"\"Add timestamp, recvWindow, compute HMAC-SHA256. Returns (query_string, signature).\"\"\"\n"
        "    params['timestamp'] = str(synced_timestamp_ms())\n"
        "    params['recvWindow'] = '10000'\n"
        "    sorted_params = sorted(params.items())\n"
        "    query = '&'.join(k + '=' + str(v) for k, v in sorted_params)\n"
        "    sig = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()\n"
        "    return query, sig",
        "P1-sign-return-tuple",
    )

    # ---------------------------------------------------------------
    # P2: Replace _bingx_request() -- build URL manually, no params=
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "def _bingx_request(method: str, path: str, params: dict) -> dict:\n"
        "    \"\"\"Send signed BingX API request. Returns response dict or {'error': msg}.\"\"\"\n"
        "    if not API_KEY or not SECRET_KEY:\n"
        "        return {'error': 'No API keys configured'}\n"
        "    try:\n"
        "        signed = _sign(params)\n"
        "        headers = {'X-BX-APIKEY': API_KEY}\n"
        "        url = BASE_URL + path\n"
        "        if method == 'GET':\n"
        "            resp = requests.get(url, params=signed, headers=headers, timeout=8)\n"
        "        elif method == 'DELETE':\n"
        "            resp = requests.delete(url, params=signed, headers=headers, timeout=8)\n"
        "        elif method == 'POST':\n"
        "            resp = requests.post(url, params=signed, headers=headers, timeout=8)\n"
        "        else:\n"
        "            return {'error': f'Unsupported method: {method}'}\n"
        "        data = resp.json()\n"
        "        if data.get('code', 0) != 0:\n"
        "            if data.get('code') == 109400:\n"
        "                from time_sync import get_time_sync as _gts\n"
        "                _ts_retry = _gts()\n"
        "                _ts_retry.force_resync()\n"
        "                signed2 = _sign(dict(params))\n"
        "                if method == 'GET':\n"
        "                    resp = requests.get(url, params=signed2, headers=headers, timeout=8)\n"
        "                elif method == 'DELETE':\n"
        "                    resp = requests.delete(url, params=signed2, headers=headers, timeout=8)\n"
        "                elif method == 'POST':\n"
        "                    resp = requests.post(url, params=signed2, headers=headers, timeout=8)\n"
        "                data2 = resp.json()\n"
        "                if data2.get('code', 0) == 0:\n"
        "                    LOG.info('109400 retry succeeded for %s', path)\n"
        "                    return data2.get('data', {})\n"
        "            return {'error': f\"BingX error {data.get('code')}: {data.get('msg')}\"}\n"
        "        return data.get('data', {})\n"
        "    except Exception as e:\n"
        "        return {'error': str(e)}",
        "def _bingx_request(method: str, path: str, params: dict) -> dict:\n"
        "    \"\"\"Send signed BingX API request. Build URL manually to match bingx_auth.py.\"\"\"\n"
        "    if not API_KEY or not SECRET_KEY:\n"
        "        return {'error': 'No API keys configured'}\n"
        "    try:\n"
        "        query, sig = _sign(dict(params))\n"
        "        headers = {'X-BX-APIKEY': API_KEY}\n"
        "        full_url = BASE_URL + path + '?' + query + '&signature=' + sig\n"
        "        if method == 'GET':\n"
        "            resp = requests.get(full_url, headers=headers, timeout=8)\n"
        "        elif method == 'DELETE':\n"
        "            resp = requests.delete(full_url, headers=headers, timeout=8)\n"
        "        elif method == 'POST':\n"
        "            resp = requests.post(full_url, headers=headers, timeout=8)\n"
        "        else:\n"
        "            return {'error': 'Unsupported method: ' + method}\n"
        "        data = resp.json()\n"
        "        if data.get('code', 0) != 0:\n"
        "            if data.get('code') == 109400:\n"
        "                from time_sync import get_time_sync as _gts\n"
        "                _ts_retry = _gts()\n"
        "                _ts_retry.force_resync()\n"
        "                query2, sig2 = _sign(dict(params))\n"
        "                full_url2 = BASE_URL + path + '?' + query2 + '&signature=' + sig2\n"
        "                if method == 'GET':\n"
        "                    resp = requests.get(full_url2, headers=headers, timeout=8)\n"
        "                elif method == 'DELETE':\n"
        "                    resp = requests.delete(full_url2, headers=headers, timeout=8)\n"
        "                elif method == 'POST':\n"
        "                    resp = requests.post(full_url2, headers=headers, timeout=8)\n"
        "                data2 = resp.json()\n"
        "                if data2.get('code', 0) == 0:\n"
        "                    LOG.info('109400 retry succeeded for %s', path)\n"
        "                    return data2.get('data', {})\n"
        "            return {'error': 'BingX error ' + str(data.get('code')) + ': ' + str(data.get('msg'))}\n"
        "        return data.get('data', {})\n"
        "    except Exception as e:\n"
        "        return {'error': str(e)}",
        "P2-bingx-request-url-build",
    )

    TARGET.write_text(content, encoding="utf-8")
    print("\nFile written: " + str(TARGET))


def validate():
    """Run py_compile on the patched file."""
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("py_compile PASS: " + str(TARGET))
    except py_compile.PyCompileError as e:
        ERRORS.append("py_compile FAILED: " + str(e))


def main():
    """Run all patches and validation."""
    print("=" * 70)
    print("BingX Dashboard v1.5 -- Signing Fix (URL build match bingx_auth.py)")
    print("=" * 70)
    print()

    if not TARGET.exists():
        print("ERROR: Target file not found: " + str(TARGET))
        sys.exit(1)

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(TARGET.stem + ".signing." + ts + ".bak.py")
    shutil.copy2(TARGET, backup)
    print("Backup: " + str(backup))
    print()

    print("Applying patches...")
    patch_file()

    if ERRORS:
        print()
        print("ERRORS:")
        for err in ERRORS:
            print("  - " + err)
        sys.exit(1)

    print()
    validate()

    if ERRORS:
        print()
        print("ERRORS:")
        for err in ERRORS:
            print("  - " + err)
        sys.exit(1)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("  Patches applied: " + str(len(PATCHES_APPLIED)))
    for p in PATCHES_APPLIED:
        print("    + " + p)
    print("  Backup: " + str(backup))
    print()
    print("  P1: _sign() returns (query, sig) tuple, timestamp as str")
    print("  P2: _bingx_request() builds URL manually (no params= kwarg)")
    print()
    print("  Before: requests.get(url, params=signed_dict)")
    print("  After:  requests.get(url + '?' + query + '&signature=' + sig)")
    print("  This matches bingx_auth.py which the bot uses successfully.")
    print()
    print("Run command:")
    print('  python "' + str(TARGET) + '"')
    print()
    print("Expected: Balance/Equity show real values, no 100001 errors")


if __name__ == "__main__":
    main()

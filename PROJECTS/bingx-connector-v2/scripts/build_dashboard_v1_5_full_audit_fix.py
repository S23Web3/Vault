"""
Build script: BingX Dashboard v1.5 -- Full Audit Fix
Date: 2026-03-05

Fixes 4 bugs found during line-by-line audit of all 3010 lines:

  BUG-A (CRITICAL): Missing time_sync import + init.
         _sign() uses local clock -> signature mismatch -> $0.00 balance.
         Patches: P1 (import), P2 (init), P3 (_sign timestamp).

  BUG-B (CRITICAL): _bingx_request() has no 109400 retry logic.
         v1.4 retries with force_resync(); v1.5 fails immediately.
         Patch: P4 (add retry block).

  BUG-C (HIGH): CB-15 show_coin_detail missing end_date Input.
         Causes IndexError in Dash _prepare_grouping on every tick.
         Patch: P5 (add Input + function param).

  BUG-D (MEDIUM): be_act not in dashboard settings.
         CB-12 save writes ttp_act but not be_act. No ctrl-be-act input.
         Patches: P6 (layout), P7 (CB-11 load), P8 (CB-12 save).

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


def safe_replace(content: str, old: str, new: str, label: str) -> str:
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
    """Apply all 8 patches to dashboard v1.5."""
    content = TARGET.read_text(encoding="utf-8")

    # ---------------------------------------------------------------
    # P1: Add time_sync import (BUG-A)
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "from dotenv import load_dotenv\n",
        "from dotenv import load_dotenv\n"
        "from time_sync import synced_timestamp_ms, get_time_sync\n",
        "P1-import-time-sync",
    )

    # ---------------------------------------------------------------
    # P2: Add time_sync initialization after LOG setup (BUG-A)
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        'LOG.info("Dashboard starting on port 8051")\n\n\n'
        "# ---------------------------------------------------------------------------\n"
        "# Bot process helpers (v1-4)\n"
        "# ---------------------------------------------------------------------------",
        'LOG.info("Dashboard starting on port 8051")\n\n'
        "# --- Time sync (prevents 109400 timestamp errors) ---\n"
        "_ts_sync = get_time_sync(base_url='https://open-api.bingx.com', sync_interval=30)\n"
        "_ts_sync.sync()\n"
        "_ts_sync.start_periodic()\n\n\n"
        "# ---------------------------------------------------------------------------\n"
        "# Bot process helpers (v1-4)\n"
        "# ---------------------------------------------------------------------------",
        "P2-init-time-sync",
    )

    # ---------------------------------------------------------------
    # P3: Fix _sign() to use synced timestamp (BUG-A)
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "    params['timestamp'] = int(time.time() * 1000)\n"
        "    params['recvWindow'] = '10000'\n",
        "    params['timestamp'] = synced_timestamp_ms()\n"
        "    params['recvWindow'] = '10000'\n",
        "P3-sign-synced-timestamp",
    )

    # ---------------------------------------------------------------
    # P4: Add 109400 retry to _bingx_request() (BUG-B)
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "        data = resp.json()\n"
        "        if data.get('code', 0) != 0:\n"
        "            return {'error': f\"BingX error {data.get('code')}: {data.get('msg')}\"}\n"
        "        return data.get('data', {})\n"
        "    except Exception as e:\n"
        "        return {'error': str(e)}",
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
        "P4-109400-retry",
    )

    # ---------------------------------------------------------------
    # P5: Fix CB-15 missing end_date Input (BUG-C)
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "    Input('analytics-date-range', 'start_date'),\n"
        "    prevent_initial_call=True,\n"
        ")\n"
        "def show_coin_detail(selected_rows, trades_json, _period, _start):",
        "    Input('analytics-date-range', 'start_date'),\n"
        "    Input('analytics-date-range', 'end_date'),\n"
        "    prevent_initial_call=True,\n"
        ")\n"
        "def show_coin_detail(selected_rows, trades_json, _period, _start, _end):",
        "P5-cb15-end-date",
    )

    # ---------------------------------------------------------------
    # P6: Add ctrl-be-act input to Strategy Parameters layout (BUG-D)
    # ---------------------------------------------------------------
    content = safe_replace(
        content,
        "            html.Label(\"Trail Distance %\"),\n"
        "            dcc.Input(id='ctrl-ttp-dist', type='number', step=0.05, min=0.05, max=2.0,\n"
        "                      value=0.2),\n"
        "            html.Label(\"Auto BE on TTP Activate\"),",
        "            html.Label(\"Trail Distance %\"),\n"
        "            dcc.Input(id='ctrl-ttp-dist', type='number', step=0.05, min=0.05, max=2.0,\n"
        "                      value=0.2),\n"
        "            html.Label(\"BE Activation %\"),\n"
        "            dcc.Input(id='ctrl-be-act', type='number', step=0.05, min=0.05, max=5.0,\n"
        "                      value=0.4),\n"
        "            html.Label(\"Auto BE on TTP Activate\"),",
        "P6-layout-be-act",
    )

    # ---------------------------------------------------------------
    # P7: Add be_act to CB-11 load_config_into_controls (BUG-D)
    # ---------------------------------------------------------------
    # P7a: Add Output
    content = safe_replace(
        content,
        "    Output('ctrl-be-auto',            'value'),\n"
        "    Input('store-config', 'data'),",
        "    Output('ctrl-be-auto',            'value'),\n"
        "    Output('ctrl-be-act',             'value'),\n"
        "    Input('store-config', 'data'),",
        "P7a-cb11-output-be-act",
    )
    # P7b: Add return value
    content = safe_replace(
        content,
        "            ['on'] if pos.get('be_auto', True) else [],\n"
        "        )",
        "            ['on'] if pos.get('be_auto', True) else [],\n"
        "            pos.get('be_act', 0.004) * 100,\n"
        "        )",
        "P7b-cb11-return-be-act",
    )

    # ---------------------------------------------------------------
    # P8: Add be_act to CB-12 save_config (BUG-D)
    # ---------------------------------------------------------------
    # P8a: Add State
    content = safe_replace(
        content,
        "    State('ctrl-be-auto',            'value'),\n"
        "    prevent_initial_call=True,  # Do not fire on page load\n"
        ")\n"
        "def save_config(n_clicks, sl_mult, tp_mult, req_s2, rot_lvl,\n"
        "                allow_a, allow_b, max_pos, max_trades,\n"
        "                loss_limit, min_atr, cooldown, margin, leverage,\n"
        "                ttp_enabled_val, ttp_act_val, ttp_dist_val, be_auto_val):",
        "    State('ctrl-be-auto',            'value'),\n"
        "    State('ctrl-be-act',             'value'),\n"
        "    prevent_initial_call=True,  # Do not fire on page load\n"
        ")\n"
        "def save_config(n_clicks, sl_mult, tp_mult, req_s2, rot_lvl,\n"
        "                allow_a, allow_b, max_pos, max_trades,\n"
        "                loss_limit, min_atr, cooldown, margin, leverage,\n"
        "                ttp_enabled_val, ttp_act_val, ttp_dist_val, be_auto_val, be_act_val):",
        "P8a-cb12-state-be-act",
    )
    # P8b: Add write logic
    content = safe_replace(
        content,
        "        cfg[\"position\"][\"be_auto\"] = 'on' in (be_auto_val or [])\n",
        "        cfg[\"position\"][\"be_auto\"] = 'on' in (be_auto_val or [])\n"
        "        cfg[\"position\"][\"be_act\"] = (be_act_val or 0.4) / 100\n",
        "P8b-cb12-write-be-act",
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
    print("BingX Dashboard v1.5 -- Full Audit Fix (4 bugs, 8 patches)")
    print("=" * 70)
    print()

    if not TARGET.exists():
        print("ERROR: Target file not found: " + str(TARGET))
        sys.exit(1)

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(TARGET.stem + "." + ts + ".bak.py")
    shutil.copy2(TARGET, backup)
    print("Backup: " + str(backup))
    print()

    # Check time_sync.py exists
    ts_path = BASE / "time_sync.py"
    if not ts_path.exists():
        print("ERROR: time_sync.py not found at " + str(ts_path))
        print("       The time_sync module must be present before patching.")
        sys.exit(1)
    print("time_sync.py found: " + str(ts_path))
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
    print("  BUG-A (CRITICAL): time_sync import + init + _sign() -- FIXED")
    print("  BUG-B (CRITICAL): 109400 retry in _bingx_request() -- FIXED")
    print("  BUG-C (HIGH):     CB-15 missing end_date Input     -- FIXED")
    print("  BUG-D (MEDIUM):   be_act settings save/load        -- FIXED")
    print()
    print("Run command:")
    print('  python "' + str(TARGET) + '"')
    print()
    print("Expected result:")
    print("  - No IndexError on page load (BUG-C fix)")
    print("  - Balance/Equity show real values (BUG-A fix)")
    print("  - 109400 errors auto-retry (BUG-B fix)")
    print("  - BE Activation % visible in Strategy Parameters (BUG-D fix)")


if __name__ == "__main__":
    main()

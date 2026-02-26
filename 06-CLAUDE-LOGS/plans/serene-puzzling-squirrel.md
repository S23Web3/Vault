# Plan: BingX Step 1 Completion — Verify Coins + Restart Bot

## Context

config.yaml now has 16 coins from the 2026-02-12 sweep (filtered by Exp, DD, PF, trade count).
The backtester sweep ran on historical CSVs — not live BingX data.
**Critical risk:** Some meme coins (PIPPIN, GIGGLE, FOLKS, STBL, SKR, UB, Q, NAORIS, ELSA, etc.) may not be listed on BingX perpetual futures, or may have been delisted.

Before restarting the bot, we must confirm every symbol in config.yaml is actively tradeable on BingX.

The existing `executor.py` already hits `GET /openApi/swap/v2/quote/contracts` (public, no auth)
to fetch step sizes. We reuse that same pattern.

---

## What Needs to Be Built

### 1 — `scripts/verify_coins.py` (new file)

A standalone pre-flight script that:
- Reads `config.yaml` from `../config.yaml` (parent dir, same as `main.py` pattern)
- Hits `GET https://open-api.bingx.com/openApi/swap/v2/quote/contracts` (live endpoint — source of truth)
- Parses the response into a set of available symbols (`c["symbol"]` from the `data` list)
- For each coin in config `coins:` list, prints PASS or FAIL
- Prints a final summary: N passed, N failed
- If any fail: prints a "clean coins list" showing only the passing coins (copy-paste ready for config.yaml)

**Does NOT auto-edit config.yaml.** Outputs the clean list to stdout so the user can review before applying.

**Pattern to follow:** mirrors `scripts/test_connection.py` (standalone, loads .env, single responsibility, no test file needed — it's a utility script)

---

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `scripts/verify_coins.py` | **CREATE** | ~80 lines, pure stdlib + requests + pyyaml |
| `config.yaml` | Modify (manually, after running script) | Remove any coins that fail |
| `COUNTDOWN-TO-LIVE.md` | Mark step 3 done after script runs clean | |

**No new test file.** This is a diagnostic utility, not a module. Existing pattern in `scripts/` has no tests.

---

## Implementation Detail

```
verify_coins.py flow:
  1. config_path = Path(__file__).parent.parent / "config.yaml"
  2. coins = yaml.safe_load(config_path)["coins"]
  3. resp = requests.get("https://open-api.bingx.com/openApi/swap/v2/quote/contracts", timeout=10)
  4. contracts_set = {c["symbol"] for c in resp.json()["data"]}
  5. for coin in coins: print(PASS/FAIL + coin)
  6. if failures: print clean list for easy copy-paste into config.yaml
```

Uses `https://open-api.bingx.com` (live) NOT the VST demo URL — live is the source of truth for
which contracts exist. VST mirrors live contract availability.

---

## Sequence After Script Is Built

1. **Run:** `python scripts/verify_coins.py`
2. **Review output** — if all 16 pass, proceed directly to step 3
3. **If any fail:** copy the clean list from script output → paste into `config.yaml` coins section
4. **Restart bot:** `python main.py` (from bingx-connector directory)
5. **Verify startup logs:** `logs/YYYY-MM-DD-bot.log`
   - Should see: warmup success for each coin
   - Should NOT see: any "Warmup failed" warnings
6. **Wait for first signal:** 201 bars × 1m = ~3.4 hour warmup window before first A/B signal possible
7. **Done when:** Demo order appears in BingX VST + Telegram UTC+4 alert received

---

## Critical Files

| File | Path |
|------|------|
| New script | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\verify_coins.py` |
| Config | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` |
| Reference — contracts fetch pattern | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` (lines: `CONTRACTS_PATH`, `fetch_step_size`) |
| Reference — script structure | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_connection.py` |
| Countdown tracker | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md` |

---

## Verification

Run: `python scripts/verify_coins.py`

Expected output (if all pass):
```
Fetching BingX contracts...
  N contracts available

Checking config.yaml coins:
  [PASS] SKR-USDT
  [PASS] FHE-USDT
  [PASS] TRUTH-USDT
  ...
  [PASS] UB-USDT

Result: 16/16 coins confirmed on BingX. Ready to restart bot.
```

If failures appear:
```
  [FAIL] GIGGLE-USDT  ← not listed on BingX perps
  [FAIL] FOLKS-USDT   ← not listed

Result: 14/16 coins confirmed. 2 failed.

Clean coins list for config.yaml:
  - "SKR-USDT"
  - "FHE-USDT"
  ...
```

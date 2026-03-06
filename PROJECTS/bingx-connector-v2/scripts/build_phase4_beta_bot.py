"""
Build Phase 4: Beta Bot (v384, $5 margin, 20x leverage).

Creates:
  config_beta.yaml  -- separate coin list, leverage=20, all paths under beta/
  main_beta.py      -- main.py copy with beta/ path overrides + live-overlap guard

Beta coin list:
  User-provided safe coins (13 - MUBARAK and SAHARA excluded, overlap with live):
    ENSO, GRASS, POWER, VENICE, SIREN, FHE, BTR, OWC, WARD, WHITEWHALE, ESP,
    MUBARAK, SAHARA  <-- EXCLUDED (in live 47-coin list)

  Additional from screenshots (excluding ETH, BTC, and any in live list):
    INJ, JTO, JUP, LINK, LTC, METAX, MUS, MYX, NEAR, ONDO, PENGU, POPCAT,
    PUMP, QNT, SHIB1000, SOL, SUI, UNI, XRP, ZEC, ZEN,
    APE, ASTER, AXS, BANK, BERAU, BNB, BONK, DASH, DOT, FARTCOIN, HMSTR, IMX

  Excluded (overlap with live): PIPPIN, RIVER, SUSHI, APT, DYDX, RENDER,
                                 MEME, 1000PEPE, MUBARAK, SAHARA

NOTE: User must verify all beta coins exist on BingX perpetuals before running.
      Run scripts/run_ticker_collector.py first to confirm liquidity.

STOP THE LIVE BOT before running main_beta.py on overlapping coins.
Run: python scripts/build_phase4_beta_bot.py
"""
import py_compile
import ast
import sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
ERRORS = []


def verify(path: Path, label: str) -> bool:
    """Syntax-check and AST-parse a .py file."""
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        print("  OK: " + label)
        return True
    except (py_compile.PyCompileError, SyntaxError) as e:
        print("  FAIL: " + label + " -- " + str(e))
        ERRORS.append(label)
        return False


# ---------------------------------------------------------------------------
# Guard: don't overwrite existing files
# ---------------------------------------------------------------------------
CONFIG_BETA = ROOT / "config_beta.yaml"
MAIN_BETA   = ROOT / "main_beta.py"
BETA_DIR    = ROOT / "beta"

for path, label in [(CONFIG_BETA, "config_beta.yaml"), (MAIN_BETA, "main_beta.py")]:
    if path.exists():
        print("ERROR: " + label + " already exists. Delete it first or version it manually.")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Beta coin list
# ---------------------------------------------------------------------------
# Verified safe coins (user-specified, excluding MUBARAK + SAHARA which overlap live)
USER_COINS = [
    "ENSO-USDT",
    "GRASS-USDT",
    "POWER-USDT",
    "VENICE-USDT",
    "SIREN-USDT",
    "FHE-USDT",
    "BTR-USDT",
    "OWC-USDT",
    "WARD-USDT",
    "WHITEWHALE-USDT",
    "ESP-USDT",
]

# Additional coins from screenshots (no live overlap, no ETH/BTC)
EXTRA_COINS = [
    "INJ-USDT",
    "JTO-USDT",
    "JUP-USDT",
    "LINK-USDT",
    "LTC-USDT",
    "METAX-USDT",
    "MUS-USDT",
    "MYX-USDT",
    "NEAR-USDT",
    "ONDO-USDT",
    "PENGU-USDT",
    "POPCAT-USDT",
    "PUMP-USDT",
    "QNT-USDT",
    "1000SHIB-USDT",
    "SOL-USDT",
    "SUI-USDT",
    "UNI-USDT",
    "XRP-USDT",
    "ZEC-USDT",
    "ZEN-USDT",
    "APE-USDT",
    "ASTER-USDT",
    "AXS-USDT",
    "BANK-USDT",
    "BERAU-USDT",
    "BNB-USDT",
    "BONK-USDT",
    "DASH-USDT",
    "DOT-USDT",
    "FARTCOIN-USDT",
    "HMSTR-USDT",
    "IMX-USDT",
]

ALL_BETA_COINS = USER_COINS + EXTRA_COINS

# Live 47-coin list — for overlap warning in main_beta.py
LIVE_COINS = [
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
]

overlaps = [c for c in ALL_BETA_COINS if c in LIVE_COINS]
if overlaps:
    print("WARNING: Beta coin list overlaps with live bot: " + ", ".join(overlaps))
    print("  Remove overlapping coins from ALL_BETA_COINS in this script before running beta.")
    ERRORS.append("OVERLAP:" + ",".join(overlaps))

# ---------------------------------------------------------------------------
# P4-A: Write config_beta.yaml
# ---------------------------------------------------------------------------
coins_yaml = "\n".join("- " + c for c in ALL_BETA_COINS)

config_beta_content = """\
connector:
  poll_interval_sec: 45
  position_check_sec: 30
  timeframe: 5m
  ohlcv_buffer_bars: 201
  demo_mode: false
coins:
""" + "\n".join("- " + c for c in ALL_BETA_COINS) + """
strategy:
  plugin: four_pillars_v384
four_pillars:
  allow_a: true
  allow_b: true
  allow_c: false
  sl_atr_mult: 2.0
  tp_atr_mult: null
  require_stage2: true
  rot_level: 80
risk:
  max_positions: 15
  max_daily_trades: 200
  daily_loss_limit_usd: 15.0
  min_atr_ratio: 0.003
  cooldown_bars: 3
  bar_duration_sec: 300
position:
  margin_usd: 5.0
  leverage: 20
  margin_mode: ISOLATED
  sl_working_type: MARK_PRICE
  tp_working_type: MARK_PRICE
  trailing_activation_atr_mult: null
  trailing_rate: null
  ttp_enabled: true
  sl_trail_pct_post_ttp: 0.003
  ttp_act: 0.005
  ttp_dist: 0.002
  be_auto: true
notification:
  daily_summary_utc_hour: 17
"""

CONFIG_BETA.write_text(config_beta_content, encoding="utf-8")
print("  Written: config_beta.yaml (" + str(len(ALL_BETA_COINS)) + " coins, 20x leverage)")

# ---------------------------------------------------------------------------
# P4-B: Write main_beta.py
# ---------------------------------------------------------------------------
# Read live main.py and adapt paths to beta/
main_src = (ROOT / "main.py").read_text(encoding="utf-8")

# Update docstring
main_beta_src = main_src.replace(
    '"""\nBingX Connector main entry point.',
    '"""\nBingX Connector BETA entry point (v384, $5 margin, 20x leverage).',
    1,
)
main_beta_src = main_beta_src.replace(
    'Run: python main.py',
    'Run: python main_beta.py',
    1,
)

# Redirect config to config_beta.yaml
main_beta_src = main_beta_src.replace(
    'config_path = Path(__file__).resolve().parent / "config.yaml"',
    'config_path = Path(__file__).resolve().parent / "config_beta.yaml"',
    1,
)

# Redirect state.json and trades.csv to beta/
main_beta_src = main_beta_src.replace(
    'state_path=root_dir / "state.json",',
    'state_path=root_dir / "beta" / "state.json",',
    1,
)
main_beta_src = main_beta_src.replace(
    'trades_path=root_dir / "trades.csv",',
    'trades_path=root_dir / "beta" / "trades.csv",',
    1,
)

# Redirect bot-status.json to beta/
main_beta_src = main_beta_src.replace(
    'STATUS_PATH = BOT_ROOT / "bot-status.json"',
    'STATUS_PATH = BOT_ROOT / "beta" / "bot-status.json"',
    1,
)

# Redirect log file to beta/logs/
main_beta_src = main_beta_src.replace(
    '    log_dir = Path(__file__).resolve().parent / "logs"',
    '    log_dir = Path(__file__).resolve().parent / "beta" / "logs"',
    1,
)

# Insert overlap guard after setup_logging() call in main()
OVERLAP_GUARD = '''
    # ---------------------------------------------------------------------------
    # BETA BOT OVERLAP GUARD
    # ---------------------------------------------------------------------------
    import json as _json_guard
    live_state_path = Path(__file__).resolve().parent / "state.json"
    if live_state_path.exists():
        try:
            live_state = _json_guard.loads(live_state_path.read_text(encoding="utf-8"))
            live_open = set(live_state.get("open_positions", {}).keys())
            beta_coins_set = set(c.replace("-USDT", "").replace("-", "") for c in [
''' + ",\n".join('                "' + c + '"' for c in ALL_BETA_COINS) + '''
            ])
            overlap_found = []
            for key in live_open:
                sym = key.rsplit("_", 1)[0]  # e.g. GRASS-USDT_LONG -> GRASS-USDT
                if sym in beta_coins_set or sym.replace("-USDT", "") in beta_coins_set:
                    overlap_found.append(key)
            if overlap_found:
                logger.warning("=" * 60)
                logger.warning("BETA BOT OVERLAP WARNING")
                logger.warning("Live bot has open positions on beta coins:")
                for k in overlap_found:
                    logger.warning("  %s", k)
                logger.warning("Running both bots on the same coin creates double positions.")
                logger.warning("Waiting 15s -- press Ctrl+C to abort now.")
                logger.warning("=" * 60)
                import time as _t
                _t.sleep(15)
        except Exception as _overlap_err:
            logger.warning("Overlap check error: %s", _overlap_err)
'''

main_beta_src = main_beta_src.replace(
    "    setup_logging()\n    logger.info(\"=== BingX Connector Starting ===\")",
    "    setup_logging()\n    logger.info(\"=== BingX BETA Bot Starting ===\")" + OVERLAP_GUARD,
    1,
)

# Create beta/ directory
BETA_DIR.mkdir(exist_ok=True)
(BETA_DIR / "logs").mkdir(exist_ok=True)
print("  Created: beta/ and beta/logs/ directories")

MAIN_BETA.write_text(main_beta_src, encoding="utf-8")
print("  Written: main_beta.py")
verify(MAIN_BETA, "main_beta.py")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("")
if ERRORS:
    # Filter overlap warnings — they don't fail the build if coins were intentionally included
    real_errors = [e for e in ERRORS if not e.startswith("OVERLAP:")]
    if real_errors:
        print("BUILD FAILED: " + ", ".join(real_errors))
        sys.exit(1)
    else:
        print("BUILD OK (with overlap warnings — review before starting beta bot)")
else:
    print("BUILD OK -- Phase 4 beta bot ready")

print("")
print("Files created:")
print("  config_beta.yaml    -- " + str(len(ALL_BETA_COINS)) + " coins, 20x leverage, beta/ data paths")
print("  main_beta.py        -- main.py adapted for beta (config_beta.yaml + beta/ paths)")
print("  beta/               -- empty dir for state.json, trades.csv, logs/")
print("")
print("Before starting:")
print("  1. Run scripts/run_ticker_collector.py to verify all beta coins are liquid on BingX")
print("  2. Confirm no open positions on beta coins in the live bot")
print("  3. Review config_beta.yaml coin list")
print("")
print("Run command:")
print('  python "' + str(MAIN_BETA) + '"')

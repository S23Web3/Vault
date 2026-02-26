#!/usr/bin/env bash
# ============================================================================
# setup_vps.sh -- VPS Setup for Vault + BingX Bot (run on VPS via SSH)
# ============================================================================
# Date:    2026-02-26
# Purpose: Clone the vault from GitHub, install Python, set up venv,
#          create systemd service for 24/7 bot operation.
#
# VPS Details:
#   Hostname: srv1280039.hstgr.cloud (Jacky)
#   IP:       76.13.20.191
#   OS:       Ubuntu 24.04.3 LTS
#   CPU:      4 cores, RAM: 16GB, Disk: 193GB (190GB free)
#   Existing: Docker (n8n + postgres) on ports 5432/5678
#
# Prerequisites:
#   - SSH access: ssh root@76.13.20.191
#   - migrate_pc.ps1 already ran (vault pushed to GitHub)
#   - GitHub SSH key set up on VPS (this script checks for it)
#
# Usage:
#   ssh root@76.13.20.191
#   # Upload this script first (scp or paste), then:
#   chmod +x setup_vps.sh
#   ./setup_vps.sh
#
# What this script does (step by step):
#   1. Checks/generates SSH key for GitHub access
#   2. Tests GitHub connectivity
#   3. Clones S23Web3/Vault to /root/vault
#   4. Installs Python 3.12 + venv
#   5. Creates virtualenv and installs bot dependencies
#   6. Prompts you to create .env (secrets -- must be done manually)
#   7. Does a quick bot import test
#   8. Creates systemd service for 24/7 operation
#   9. Enables and starts the bot
#
# What this script does NOT do:
#   - It does NOT store any secrets (you paste them manually)
#   - It does NOT modify n8n or Docker (they keep running)
#   - It does NOT touch the PC
# ============================================================================

set -e  # Exit on any error

# --------------------------------------------------------------------------
# CRLF SELF-FIX
# --------------------------------------------------------------------------
# If this script was copied from Windows (scp/paste), it may have \r\n
# line endings which bash reads as literal \r characters, causing errors
# like "/bin/bash^M: bad interpreter". This block detects and fixes it.
# --------------------------------------------------------------------------
if grep -qP '\r' "$0" 2>/dev/null; then
    echo "  Detected Windows line endings (CRLF). Converting to LF..."
    sed -i 's/\r$//' "$0"
    echo "  Fixed. Re-running script..."
    exec bash "$0" "$@"
fi

REPO="git@github.com:S23Web3/Vault.git"
VAULT_DIR="/root/vault"
BOT_DIR="/root/vault/PROJECTS/bingx-connector"
SERVICE_NAME="bingx-bot"

echo ""
echo "========================================"
echo " VPS Setup Script -- Part B"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# --------------------------------------------------------------------------
# STEP 1: SSH key for GitHub
# --------------------------------------------------------------------------
# Git clone over SSH requires an SSH key registered with GitHub.
# We check if one exists; if not, we generate it and PAUSE so you
# can add it to https://github.com/settings/keys before continuing.
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# STEPS 1-2: SSH key + GitHub connection
# --------------------------------------------------------------------------
# On first run: generates key, shows it, pauses for you to register it.
# On re-run: tests connection first. If already working, skips the pause.
# --------------------------------------------------------------------------

echo "[Step 1/9] Checking GitHub SSH access..."

SSH_KEY="$HOME/.ssh/id_ed25519"

# Test if GitHub connection already works (skip key setup if so)
SSH_OUTPUT=$(ssh -T git@github.com 2>&1 || true)
if echo "$SSH_OUTPUT" | grep -q "successfully authenticated"; then
    echo "  PASS: GitHub SSH already working. Skipping key setup."
    echo "  $SSH_OUTPUT"
else
    # Key doesn't work yet -- generate if needed, then pause
    if [ -f "$SSH_KEY" ]; then
        echo "  Key exists but GitHub doesn't recognize it."
    else
        echo "  Generating new SSH key..."
        ssh-keygen -t ed25519 -C "malik@shortcut23.com" -f "$SSH_KEY" -N ""
        echo "  DONE: Key generated."
    fi

    echo ""
    echo "  Your public key:"
    echo "  ----------------------------------------"
    cat "${SSH_KEY}.pub"
    echo "  ----------------------------------------"
    echo ""
    echo "  ACTION REQUIRED:"
    echo "  1. Copy the key above"
    echo "  2. Go to https://github.com/settings/keys"
    echo "  3. Click 'New SSH key', paste, save"
    echo "  4. Press ENTER here when done"
    echo ""
    read -rp "  Press ENTER to continue..."

    echo ""
    echo "[Step 2/9] Testing GitHub connection..."

    SSH_OUTPUT=$(ssh -T git@github.com 2>&1 || true)
    if echo "$SSH_OUTPUT" | grep -q "successfully authenticated"; then
        echo "  PASS: $SSH_OUTPUT"
    else
        echo "  FAIL: $SSH_OUTPUT"
        echo "  Check that your SSH key is added to GitHub and try again."
        exit 1
    fi
fi

# --------------------------------------------------------------------------
# STEP 3: Clone the vault
# --------------------------------------------------------------------------
# Clones the full vault repo to /root/vault. If it already exists,
# we pull latest instead of re-cloning.
# --------------------------------------------------------------------------

echo ""
echo "[Step 3/9] Cloning vault to $VAULT_DIR..."

if [ -d "$VAULT_DIR/.git" ]; then
    echo "  SKIP: $VAULT_DIR already exists. Pulling latest..."
    cd "$VAULT_DIR"
    git pull --ff-only
else
    cd /root
    git clone "$REPO" vault
    echo "  DONE: Cloned to $VAULT_DIR"
fi

# Verify bot files exist
if [ ! -f "$BOT_DIR/main.py" ]; then
    echo "  ERROR: $BOT_DIR/main.py not found. Clone may be incomplete."
    exit 1
fi
echo "  VERIFIED: main.py exists in $BOT_DIR"

# --------------------------------------------------------------------------
# STEP 4: Install Python 3.12
# --------------------------------------------------------------------------
# Ubuntu 24.04 ships with Python 3.12. We ensure it and venv are installed.
# This does NOT affect the system Python or any other Python installations.
# --------------------------------------------------------------------------

echo ""
echo "[Step 4/9] Installing Python 3.12..."

apt update -qq
echo "  Installing packages (this may take a minute)..."
if ! apt install -y python3.12 python3.12-venv python3-pip 2>&1 | tail -3; then
    echo "  ERROR: apt install failed. Check output above."
    echo "  Common fixes: apt --fix-broken install, or check disk space with df -h"
    exit 1
fi

PYTHON_VER=$(python3.12 --version 2>&1)
echo "  DONE: $PYTHON_VER installed"

# --------------------------------------------------------------------------
# STEP 5: Create virtualenv and install dependencies
# --------------------------------------------------------------------------
# A virtualenv isolates the bot's Python packages from the system.
# requirements.txt needs: requests, pyyaml, python-dotenv, pandas, numpy.
# --------------------------------------------------------------------------

echo ""
echo "[Step 5/9] Creating virtualenv and installing dependencies..."

cd "$BOT_DIR"

if [ -d "venv" ]; then
    echo "  SKIP: venv already exists."
else
    python3.12 -m venv venv
    echo "  DONE: venv created."
fi

# Activate and install
# pip output is shown so you can see if anything fails.
source venv/bin/activate
pip install --upgrade pip 2>&1 | tail -1
echo "  Installing requirements.txt..."
pip install -r requirements.txt 2>&1 | tail -5

echo "  Installed packages:"
pip list --format=columns 2>/dev/null | grep -E "requests|pyyaml|python-dotenv|pandas|numpy" | while read -r line; do
    echo "    $line"
done

deactivate

# --------------------------------------------------------------------------
# STEP 6: Create .env file (MANUAL -- secrets)
# --------------------------------------------------------------------------
# The .env file contains API keys and tokens. These are NEVER stored in git.
# You must paste them manually. The script checks if .env exists and
# prompts you if it doesn't.
# --------------------------------------------------------------------------

echo ""
echo "[Step 6/9] Checking .env file..."

ENV_FILE="$BOT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo "  FOUND: $ENV_FILE exists."
    # Verify it has the required keys
    MISSING=""
    for KEY in BINGX_API_KEY BINGX_SECRET TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
        if ! grep -q "^${KEY}=" "$ENV_FILE"; then
            MISSING="$MISSING $KEY"
        fi
    done
    if [ -n "$MISSING" ]; then
        echo "  WARNING: Missing keys:$MISSING"
        echo "  Edit $ENV_FILE and add them."
    else
        echo "  VERIFIED: All 4 required keys present."
    fi
else
    echo "  NOT FOUND: $ENV_FILE"
    echo ""
    echo "  You need to create it with these 4 values:"
    echo "    BINGX_API_KEY=<your key>"
    echo "    BINGX_SECRET=<your secret>"
    echo "    TELEGRAM_BOT_TOKEN=<your token>"
    echo "    TELEGRAM_CHAT_ID=<your chat id>"
    echo ""
    echo "  Get these from your PC file:"
    echo "    C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\.env"
    echo ""
    echo "  Run: nano $ENV_FILE"
    echo "  Paste the values, save (Ctrl+O, Enter, Ctrl+X)."
    echo ""
    read -rp "  Press ENTER after creating .env..."

    if [ ! -f "$ENV_FILE" ]; then
        echo "  ERROR: .env still not found. Cannot continue without secrets."
        exit 1
    fi
fi

# Lock permissions (owner read/write only)
chmod 600 "$ENV_FILE"
echo "  Permissions set to 600 (owner only)."

# --------------------------------------------------------------------------
# STEP 7: Quick bot import test
# --------------------------------------------------------------------------
# We do a quick Python import test to verify all dependencies load.
# This catches missing packages or import errors before we create the service.
# --------------------------------------------------------------------------

echo ""
echo "[Step 7/9] Running bot import test..."

cd "$BOT_DIR"
source venv/bin/activate

# We test individual modules -- NOT 'import main' which would start the bot.
TEST_OUTPUT=$(python3.12 -c "
import sys
sys.path.insert(0, '.')
try:
    import requests;         print('  requests ......... OK')
    import yaml;             print('  pyyaml ........... OK')
    import dotenv;           print('  python-dotenv .... OK')
    import pandas;           print('  pandas ........... OK')
    import numpy;            print('  numpy ............ OK')
    import data_fetcher;     print('  data_fetcher ..... OK')
    import signal_engine;    print('  signal_engine .... OK')
    import executor;         print('  executor ......... OK')
    import risk_gate;        print('  risk_gate ........ OK')
    import state_manager;    print('  state_manager .... OK')
    import position_monitor; print('  position_monitor . OK')
    import notifier;         print('  notifier ......... OK')
    print('PASS: All imports succeeded')
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(1)
" 2>&1)

deactivate

echo "  $TEST_OUTPUT"
if echo "$TEST_OUTPUT" | grep -q "FAIL"; then
    echo "  Fix the import error above before continuing."
    exit 1
fi

# --------------------------------------------------------------------------
# STEP 8: Create systemd service
# --------------------------------------------------------------------------
# systemd manages the bot as a background service:
#   - Starts on boot (enable)
#   - Auto-restarts on crash (Restart=always, 10s delay)
#   - PYTHONUNBUFFERED=1 ensures log lines flush immediately
#   - Logs go to journalctl (view with: journalctl -u bingx-bot -f)
# --------------------------------------------------------------------------

echo ""
echo "[Step 8/9] Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=BingX Trading Bot (Four Pillars v3.8.4)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/vault/PROJECTS/bingx-connector
ExecStart=/root/vault/PROJECTS/bingx-connector/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "  DONE: Created $SERVICE_FILE"
echo ""
echo "  Service config:"
echo "    WorkingDirectory: $BOT_DIR"
echo "    ExecStart:        $BOT_DIR/venv/bin/python main.py"
echo "    Restart:          always (10s delay)"
echo "    Logs:             journalctl -u $SERVICE_NAME -f"

# --------------------------------------------------------------------------
# STEP 9: Enable and start the bot
# --------------------------------------------------------------------------
# daemon-reload: tells systemd to re-read service files
# enable:        start on boot
# start:         start right now
# --------------------------------------------------------------------------

echo ""
echo "[Step 9/9] Enabling and starting bot..."

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# Give it 3 seconds to start
sleep 3

# Check status
STATUS=$(systemctl is-active "$SERVICE_NAME" 2>&1)
if [ "$STATUS" = "active" ]; then
    echo "  RUNNING: Bot is active."
else
    echo "  WARNING: Bot status is '$STATUS'."
    echo "  Check logs: journalctl -u $SERVICE_NAME --no-pager -n 30"
fi

echo ""
echo "========================================"
echo " VPS SETUP COMPLETE"
echo "========================================"
echo ""
echo "  Bot service: $SERVICE_NAME"
echo "  Status:      systemctl status $SERVICE_NAME"
echo "  Logs:        journalctl -u $SERVICE_NAME -f"
echo "  Stop:        systemctl stop $SERVICE_NAME"
echo "  Restart:     systemctl restart $SERVICE_NAME"
echo ""
echo "  Deploy updates from PC:"
echo "    ssh root@76.13.20.191 \"cd /root/vault && git pull && systemctl restart $SERVICE_NAME\""
echo ""

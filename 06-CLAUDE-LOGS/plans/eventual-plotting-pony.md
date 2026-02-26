# Telegram Connection — Guided Instructions

**Goal:** Fill in `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the `.env` file so trade alerts from the bot reach your Telegram account.

**File to edit:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.env`

---

## What currently exists

The code is fully built. `notifier.py` is ready to send messages. `main.py` loads both values from `.env` on startup. Only the two placeholder values below are blocking alerts:

```
TELEGRAM_BOT_TOKEN=<your Telegram bot token>
TELEGRAM_CHAT_ID=<your Telegram chat ID>
```

---

## Step 1 — Create a bot using BotFather

1. Open Telegram (any platform).
2. Search for **@BotFather** (the official blue-checkmark bot that creates all bots).
3. Send this message to BotFather:
   ```
   /newbot
   ```
4. BotFather asks: *"Alright, a new bot. How are we going to call it?"* — type any display name, e.g.:
   ```
   BingX Trade Alerts
   ```
5. BotFather then asks for a **username** (must end in `bot`), e.g.:
   ```
   bingx_myalerts_bot
   ```
6. BotFather replies with your token — it looks like this:
   ```
   7412365890:AAFHsomethingLong_randomCharactersHere
   ```
   **Copy this entire string. This is your `TELEGRAM_BOT_TOKEN`.**

---

## Step 2 — Get your Chat ID

Your Chat ID tells the bot *which conversation* to send messages to. You need to start the bot first so Telegram registers you as a user.

1. In Telegram, search for the bot username you just created (e.g. `@bingx_myalerts_bot`).
2. Click **Start** or send any message to it (e.g. `hello`).
3. Open a web browser and paste this URL — replacing `YOUR_TOKEN` with the token from Step 1:
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
   Example:
   ```
   https://api.telegram.org/bot7412365890:AAFHsomethingLong_randomCharactersHere/getUpdates
   ```
4. The page returns JSON. Look for the `"id"` field inside `"chat"`:
   ```json
   "chat": {
     "id": 123456789,
     "first_name": "Your Name",
     ...
   }
   ```
   **That number (e.g. `123456789`) is your `TELEGRAM_CHAT_ID`.**

> If the page returns `{"ok":true,"result":[]}` (empty), go back to Telegram and send another message to the bot, then refresh the browser URL.

---

## Step 3 — Edit the .env file

Open `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.env` and replace the two placeholder lines:

**Before:**
```
TELEGRAM_BOT_TOKEN=<your Telegram bot token>
TELEGRAM_CHAT_ID=<your Telegram chat ID>
```

**After (example values):**
```
TELEGRAM_BOT_TOKEN=7412365890:AAFHsomethingLong_randomCharactersHere
TELEGRAM_CHAT_ID=123456789
```

No quotes. No spaces around `=`. Save the file.

---

## Step 4 — Test the connection (before running the bot)

Run this one-liner from the terminal in the bingx-connector folder to verify the token and chat ID work:

```bash
python -c "
import os; from dotenv import load_dotenv; import requests
load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat  = os.getenv('TELEGRAM_CHAT_ID')
r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
    json={'chat_id': chat, 'text': 'BingX bot Telegram test OK'})
print(r.status_code, r.json())
"
```

Expected output: `200` and `"ok": true`. A message **"BingX bot Telegram test OK"** will appear in the bot chat in Telegram.

---

## Step 5 — Run the bot and tick the checklist item

Once the test passes, start the bot normally:

```bash
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"
```

On startup `main.py` sends a startup Telegram message. When the first A/B signal fires, the alert will arrive in your bot chat. At that point the checklist item `**Telegram alert received**` can be checked off in `STEP1-CHECKLIST.md`.

---

## What each value does

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Authenticates your bot with the Telegram API. Lives in `.env`, never in git. |
| `TELEGRAM_CHAT_ID` | The conversation destination. Your personal chat with the bot is the simplest choice. Can also be a group chat ID if you want alerts in a group. |

---

## Files involved

- **Edit:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.env` (add token + chat ID)
- **Read-only reference:** `notifier.py` — the sender (already complete, no changes needed)
- **Read-only reference:** `main.py` lines 1-50 — loads `.env` via `python-dotenv` on startup

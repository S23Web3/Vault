"""
Telegram connection test.
Run from the bingx-connector folder:
    python test_telegram.py
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE = f"https://api.telegram.org/bot{TOKEN}"


def check_updates():
    """Fetch recent messages to find your numeric chat ID."""
    print("\n--- getUpdates ---")
    r = requests.get(f"{BASE}/getUpdates", timeout=10)
    data = r.json()
    if not data.get("ok"):
        print("ERROR:", data)
        return None
    results = data.get("result", [])
    if not results:
        print("No messages found.")
        print(">> Go to Telegram, open your bot chat, send it any message, then re-run this script.")
        return None
    for item in results:
        chat = item.get("message", {}).get("chat", {})
        print(f"  chat id  : {chat.get('id')}")
        print(f"  username : {chat.get('username')}")
        print(f"  name     : {chat.get('first_name')} {chat.get('last_name', '')}")
    # Return the most recent chat id
    return results[-1]["message"]["chat"]["id"]


def send_test(chat_id):
    """Send a test message to the given chat id."""
    print(f"\n--- sendMessage to {chat_id} ---")
    r = requests.post(f"{BASE}/sendMessage", json={
        "chat_id": chat_id,
        "text": "BingX bot Telegram test OK — connection confirmed.",
    }, timeout=10)
    data = r.json()
    if r.status_code == 200 and data.get("ok"):
        print("SUCCESS — check your Telegram bot chat for the message.")
        print(f"\n>> Now update your .env file:")
        print(f"   TELEGRAM_CHAT_ID={chat_id}")
    else:
        print("FAILED:", json.dumps(data, indent=2))


if __name__ == "__main__":
    print(f"Token loaded : {'YES' if TOKEN and 'your' not in TOKEN else 'NO — check .env'}")
    print(f"Chat ID set  : {CHAT_ID}")

    chat_id = check_updates()
    if chat_id:
        send_test(chat_id)

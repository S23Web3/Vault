"""
Telegram notification sender. Never raises exceptions.
"""
import logging
import requests
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class Notifier:
    """Send timestamped messages to Telegram."""

    def __init__(self, bot_token, chat_id, enabled=True):
        """Initialize with Telegram bot credentials."""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled

    def send(self, message):
        """Send a message with UTC+4 timestamp prefix. Returns True on success."""
        if not self.enabled:
            logger.debug("Notifier disabled, skip: %s", message[:80])
            return False
        utc4 = timezone(timedelta(hours=4))
        ts = datetime.now(utc4).strftime("%Y-%m-%d %H:%M:%S UTC+4")
        full_msg = "[" + ts + "] " + message
        url = ("https://api.telegram.org/bot" + self.bot_token
               + "/sendMessage")
        try:
            resp = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": full_msg,
                "parse_mode": "HTML",
            }, timeout=10)
            if resp.status_code == 200:
                logger.debug("Telegram sent: %s", message[:80])
                return True
            logger.warning("Telegram HTTP %d: %s",
                           resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            logger.warning("Telegram failed: %s", e)
            return False

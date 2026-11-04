import os
import httpx
from typing import Optional

class Notifier:
    """Optional broadcast notifier for delivery reports and token lifecycle events."""
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    async def send_report(self, text: str) -> bool:
        if not self.bot_token or not self.chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, json=payload)
                return res.status_code == 200
        except Exception:
            return False

def format_like_delivery_report(
    name: str,
    uid: int,
    region: str,
    level: int,
    before: int,
    added: int,
    after: int,
    duration: float
) -> str:
    return (
        "<b>Like Delivery Complete</b>\n"
        f"Name: {name}\n"
        f"UID: {uid}\n"
        f"Region: {region}\n"
        f"Level: {level}\n"
        f"Before: {before}\n"
        f"Added: +{added}\n"
        f"After: {after}\n"
        f"Time: {duration:.1f}s"
    )

def format_token_refresh_report(total: int, active: int, failed: int, duration: float) -> str:
    return (
        "<b>Token Refresh Complete</b>\n"
        f"Total: {total}\n"
        f"Active: {active}\n"
        f"Failed: {failed}\n"
        f"Duration: {duration:.1f}s"
    )

notifier = Notifier()


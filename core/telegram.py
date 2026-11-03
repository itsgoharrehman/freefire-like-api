# -*- coding: utf-8 -*-
"""
core/telegram.py - Asynchronous Telegram Channel Notification Engine
Authored for Gohar Rehman | Free Fire Like Engine
Strictly formats announcements as one line per point with clean, logical emojis.
"""
import httpx
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def escape_markdown(text: str) -> str:
    """Escapes markdown formatting characters so player nicknames render verbatim."""
    if not text:
        return ""
    for ch in ['_', '*', '`', '[']:
        text = text.replace(ch, "\\" + ch)
    return text

async def send_telegram_report(message: str) -> bool:
    """Dispatches a clean announcement to the configured Telegram channel using resilient httpx client."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        print(f"[!] Telegram dispatch error: {e}")
        return False

def format_token_refresh_report(total: int, active: int, failed: int, duration: float) -> str:
    """One line per point token refresh announcement."""
    return (
        "⚡ Token Refresh Complete\n"
        f"📊 Total: {total}\n"
        f"🟢 Active: {active}\n"
        f"🔴 Failed: {failed}\n"
        f"⏱ Time: {duration:.1f}s"
    )

def format_like_delivery_report(name: str, uid: int, region: str, level: int,
                                before: int, added: int, after: int, duration: float) -> str:
    """One line per point like delivery announcement with clean nickname escaping."""
    safe_name = escape_markdown(str(name))
    return (
        "❤️ Like Delivery Complete\n"
        f"👤 Name: {safe_name}\n"
        f"🆔 UID: {uid}\n"
        f"🌍 Region: {region}\n"
        f"🎖 Level: {level}\n"
        f"📈 Before: {before}\n"
        f"🚀 Added: +{added}\n"
        f"💎 After: {after}\n"
        f"⏱ Time: {duration:.1f}s"
    )

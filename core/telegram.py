import logging
import os
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()


async def send_telegram_broadcast(html_text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN).strip()
    channel = os.getenv("TELEGRAM_CHANNEL_ID", TELEGRAM_CHANNEL_ID).strip()
    if not token or not channel:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(url, json=payload)
            return res.status_code == 200
    except Exception as e:
        logger.warning(f"Telegram notification dispatch error: {e}")
        return False


async def notify_like_success(fleet_name: str, target: dict, likes: dict, fleet_stats: dict, elapsed_s: float):
    target_uid = target.get("uid", 0)
    nickname = target.get("nickname", "Unknown")
    region = target.get("region", "Unknown")
    before_l = likes.get("before", 0)
    added_l = likes.get("added", 0)
    after_l = likes.get("after", 0)
    succeeded = fleet_stats.get("requests_succeeded", 0)
    dispatched = fleet_stats.get("requests_dispatched", 0)

    card = (
        "🟢 <b>Like Delivery Completed</b>\n\n"
        f"👤 <b>Player:</b> {nickname}\n"
        f"🆔 <b>UID:</b> <code>{target_uid}</code>\n"
        f"🌐 <b>Region:</b> {region}\n\n"
        f"👍 <b>Likes:</b> <code>{before_l}</code> ➔ <code>{after_l}</code> (<b>+{added_l}</b>)\n\n"
        f"⚡ <b>Fleet:</b> {fleet_name}\n"
        f"📤 <b>Dispatched:</b> <code>{succeeded}/{dispatched}</code>\n"
        f"⏱️ <b>Duration:</b> {elapsed_s}s"
    )
    await send_telegram_broadcast(card)


async def notify_like_failure(fleet_name: str, target_uid: int, error_msg: str, status_code: int = 500):
    card = (
        "🔴 <b>Like Delivery Failed</b>\n\n"
        f"🆔 <b>UID:</b> <code>{target_uid}</code>\n"
        f"⚡ <b>Fleet:</b> {fleet_name}\n\n"
        f"⚠️ <b>Status:</b> <code>{status_code}</code>\n"
        f"❌ <b>Error:</b> {error_msg}"
    )
    await send_telegram_broadcast(card)


async def notify_token_refresh(
    fleet_name: str,
    total_accounts: int,
    renewed: int,
    failed: int = 0,
    elapsed_s: float = 0.0,
):
    card = (
        "🔄 <b>Token Renewal Completed</b>\n\n"
        f"⚡ <b>Fleet:</b> {fleet_name}\n"
        f"👥 <b>Total Accounts:</b> <code>{total_accounts}</code>\n\n"
        f"✅ <b>Renewed Tokens:</b> <code>{renewed}</code>\n"
    )
    if failed > 0:
        card += f"⚠️ <b>Failed / Queued:</b> <code>{failed}</code>\n"
    card += f"\n⏱️ <b>Duration:</b> {elapsed_s}s"
    await send_telegram_broadcast(card)


async def notify_downtime_alert(fleet_name: str, endpoint: str, error_msg: str, status_code: int = 500):
    card = (
        "🚨 <b>Fleet Service Alert</b>\n\n"
        f"⚡ <b>Fleet:</b> {fleet_name}\n"
        f"🔗 <b>Endpoint:</b> <code>{endpoint}</code>\n\n"
        f"⚠️ <b>Status:</b> <code>{status_code}</code>\n"
        f"❌ <b>Error:</b> {error_msg}"
    )
    await send_telegram_broadcast(card)

# -*- coding: utf-8 -*-
"""
core/dispatcher.py - High-Throughput Free Fire Like Dispatcher
Authored for Gohar Rehman | Free Fire Like Engine
Uses unified sender pool to dispatch 766+ likes to all 14 regions in native speed.
Zero fake metrics - strictly reports verified Garena like increments.
"""
import time
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List

from config.settings import (
    GATEWAY_URLS,
    DEFAULT_HEADERS,
    ACTIVE_GATEWAY,
    MAX_KEEPALIVE_CONNECTIONS,
    REQUEST_TIMEOUT
)
from core.protocol import (
    create_like_payload,
    create_profile_payload,
    parse_profile_response
)
from core.tokens import token_manager
from core.telegram import send_telegram_report, format_like_delivery_report

class LikeDispatcher:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def init_session(self) -> None:
        """Initializes persistent warm connection pool with TCP keep-alive."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=250,
                keepalive_timeout=75.0,
                enable_cleanup_closed=True,
                ttl_dns_cache=300
            )
            timeout = aiohttp.ClientTimeout(total=8.0)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def close_session(self) -> None:
        """Closes persistent session cleanly."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def get_base_url(self, region: str) -> str:
        reg = region.upper() if region else "GLOBAL"
        return GATEWAY_URLS.get(reg, ACTIVE_GATEWAY)

    async def query_player_profile(self, target_uid: int, region: str) -> Optional[Dict[str, Any]]:
        """Queries authoritative GetPlayerPersonalShow for live player stats."""
        await self.init_session()
        base_url = self.get_base_url(region)
        url = f"{base_url}/GetPlayerPersonalShow"
        enc_payload = create_profile_payload(target_uid)

        # Retrieve active token from unified pool
        tokens = token_manager.get_tokens(1)
        auth_token = tokens[0] if tokens else ""

        headers = dict(DEFAULT_HEADERS)
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            async with self.session.post(url, data=enc_payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return parse_profile_response(data)
                else:
                    data = await resp.read()
                    print(f"[!] Profile query non-200 ({resp.status}): {data[:80]}")
        except Exception as e:
            print(f"[!] Profile query exception: {type(e).__name__}: {e}")
        return None

    async def send_single_like(self, url: str, enc_payload: bytes, token: str) -> bool:
        """Sends one encrypted like frame to Garena."""
        headers = dict(DEFAULT_HEADERS)
        headers["Authorization"] = f"Bearer {token}"
        try:
            async with self.session.post(url, data=enc_payload, headers=headers) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def dispatch_likes(self, target_uid: int, region: str, requested_count: int) -> Dict[str, Any]:
        """
        Dispatches likes from unified global sender pool to target UID in target region.
        Ultra-fast pipelined execution in bursts of 80 with 15ms micro-staggers.
        """
        start_time = time.time()
        await self.init_session()
        target_reg = region.upper() if region else "GLOBAL"
        base_url = self.get_base_url(target_reg)
        like_url = f"{base_url}/LikeProfile"

        # 1. Query initial profile likes
        before_profile = await self.query_player_profile(target_uid, target_reg)
        if not before_profile:
            # Try once more with GLOBAL fallback before giving up
            if target_reg != "GLOBAL":
                before_profile = await self.query_player_profile(target_uid, "GLOBAL")

        if not before_profile:
            return {
                "status": "error",
                "error": f"Account UID {target_uid} was not found on Garena servers (BR_ACCOUNT_NOT_FOUND). Please verify UID and region.",
                "likes_added": 0
            }

        likes_before = before_profile["likes"]
        nickname = before_profile["nickname"]
        level = before_profile["level"]
        resolved_region = before_profile["region"]

        # 2. Slice requested sender tokens from unified pool
        tokens = token_manager.get_tokens(requested_count)
        if not tokens:
            return {
                "status": "error",
                "error": "No active sender tokens available in token pool",
                "likes_added": 0
            }

        # 3. Pre-build encrypted like payload
        enc_payload = create_like_payload(target_uid, resolved_region)

        # 4. Ultra-fast micro-batch execution (bursts of 80 with 15ms micro-stagger)
        chunk_size = 40
        stagger_delay = 0.035
        all_results = []
        for i in range(0, len(tokens), chunk_size):
            chunk = tokens[i : i + chunk_size]
            tasks = [self.send_single_like(like_url, enc_payload, tok) for tok in chunk]
            batch_res = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend(batch_res)
            if (i + chunk_size) < len(tokens):
                await asyncio.sleep(stagger_delay)

        dispatched_success = sum(1 for r in all_results if r is True)

        # 5. Settling delay (allows Garena edge servers to commit) & query final profile
        await asyncio.sleep(1.0)
        after_profile = await self.query_player_profile(target_uid, resolved_region)
        if after_profile:
            likes_after = after_profile["likes"]
            likes_added = max(0, likes_after - likes_before)
            nickname = after_profile["nickname"]
            level = after_profile["level"]
        else:
            likes_after = likes_before
            likes_added = 0

        duration = time.time() - start_time

        # 6. Await Telegram report delivery
        await send_telegram_report(
            format_like_delivery_report(
                name=nickname,
                uid=target_uid,
                region=resolved_region,
                level=level,
                before=likes_before,
                added=likes_added,
                after=likes_after,
                duration=duration
            )
        )

        return {
            "status": "success",
            "player": {
                "uid": target_uid,
                "nickname": nickname,
                "region": resolved_region,
                "level": level
            },
            "likes_before": likes_before,
            "likes_after": likes_after,
            "likes_added": likes_added,
            "tokens_dispatched": len(tokens),
            "requests_successful": dispatched_success,
            "duration_seconds": round(duration, 2)
        }

like_dispatcher = LikeDispatcher()

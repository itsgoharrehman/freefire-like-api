import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from google.protobuf import json_format

from core.config import (
    ACCOUNTS_FILE,
    FLEET_NAME,
    GATEWAY_DEFAULT,
    GATEWAY_IND,
    GATEWAY_US,
    MAX_CONCURRENT_LIKES,
    RELEASE_VERSION,
    REQUEST_TIMEOUT,
    USERAGENT,
    get_gateway_by_region,
)
from core.crypto import MAIN_IV, MAIN_KEY, aes_cbc_encrypt, decode_protobuf
from core.token_cache import token_cache
from ff_proto import account_show_pb2, core_pb2, send_like_pb2

logger = logging.getLogger(__name__)


def load_accounts() -> List[dict]:
    if not ACCOUNTS_FILE.exists():
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading accounts from {ACCOUNTS_FILE}: {e}")
        return []


async def fetch_player_info(target_uid: int) -> Dict[str, Any]:
    tokens = token_cache.get_all_valid_tokens()
    if not tokens:
        return {"success": False, "error": "No active authentication tokens available in fleet cache."}

    req = core_pb2.GetPlayerPersonalShow()
    req.a = int(target_uid)
    req.b = 0
    enc_payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, req.SerializeToString())

    headers_template = {
        "User-Agent": USERAGENT,
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "X-GA-SV": "1789638359",
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.12f1",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASE_VERSION,
    }

    gateways = [GATEWAY_DEFAULT, GATEWAY_IND, GATEWAY_US]
    candidates = tokens[:8]

    async with httpx.AsyncClient(verify=False) as client:
        for tok in candidates:
            token_jwt = tok.get("jwt")
            if not token_jwt:
                continue

            headers = dict(headers_template)
            headers["Authorization"] = f"Bearer {token_jwt}"

            for gw in gateways:
                try:
                    url = f"{gw}/GetPlayerPersonalShow"
                    res = await client.post(url, content=enc_payload, headers=headers, timeout=REQUEST_TIMEOUT)
                    if res.status_code == 200:
                        res_proto = decode_protobuf(res.content, account_show_pb2.AccountPersonalShowInfo)
                        raw_dict = json_format.MessageToDict(res_proto, preserving_proto_field_name=True)

                        basic = raw_dict.get("basic_info", {})
                        clan = raw_dict.get("clan_basic_info", {})
                        credit = raw_dict.get("credit_score_info", {})

                        return {
                            "success": True,
                            "gateway": gw,
                            "summary": {
                                "uid": basic.get("account_id", str(target_uid)),
                                "nickname": basic.get("nickname", "UNKNOWN"),
                                "region": basic.get("region", "UNKNOWN"),
                                "level": basic.get("level", 0),
                                "likes": basic.get("liked", 0),
                                "rank": basic.get("rank", 0),
                                "cs_rank": basic.get("cs_rank", 0),
                                "credit_score": credit.get("credit_score", 100),
                                "is_deleted": basic.get("is_deleted", False),
                                "is_cs_ranking_ban": basic.get("is_cs_ranking_ban", False),
                            },
                        }
                except Exception:
                    continue

    return {"success": False, "error": f"Player {target_uid} not found on Free Fire servers."}


async def send_fleet_likes(target_uid: int) -> Dict[str, Any]:
    start_time = time.time()

    # Step 1: Pre-fetch player profile to verify target and capture initial like count
    initial_info = await fetch_player_info(target_uid)
    if not initial_info.get("success"):
        return {
            "status": "error",
            "message": initial_info.get("error", "Player not found on Free Fire servers."),
            "fleet_name": FLEET_NAME,
            "target_uid": int(target_uid),
        }

    summary = initial_info["summary"]
    before_likes = summary.get("likes", 0)
    target_region = summary.get("region", "BD")
    nickname = summary.get("nickname", "UNKNOWN")
    level = summary.get("level", 0)

    # Step 2: Acquire active token pool
    tokens = token_cache.get_all_valid_tokens()
    accounts = load_accounts()

    if not tokens:
        return {
            "status": "error",
            "message": "No active authentication tokens available in fleet to send likes.",
            "fleet_name": FLEET_NAME,
            "target_uid": int(target_uid),
        }

    target_uid_str = str(target_uid).strip()
    active_tokens = [t for t in tokens if str(t.get("uid", "")).strip() != target_uid_str]

    # Step 3: Prepare Encrypted Like Payload
    target_gateway = get_gateway_by_region(target_region)
    like_url = f"{target_gateway}/LikeProfile"

    REGION_NORM = {
        "EUROPE": "EU",
        "BANGLADESH": "BD",
        "PAKISTAN": "PK",
        "INDIA": "IND",
        "MIDDLE_EAST": "ME",
    }
    normalized_region = REGION_NORM.get(target_region.strip().upper(), target_region)

    like_msg = send_like_pb2.like()
    like_msg.uid = int(target_uid)
    like_msg.region = normalized_region
    enc_payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, like_msg.SerializeToString())

    headers_template = {
        "User-Agent": USERAGENT,
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "X-GA-SV": "1789638359",
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.12f1",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASE_VERSION,
    }

    # Step 4: Ultra-Fast Paced Concurrency Dispatch
    sem = asyncio.Semaphore(MAX_CONCURRENT_LIKES)
    limits = httpx.Limits(max_keepalive_connections=MAX_CONCURRENT_LIKES, max_connections=MAX_CONCURRENT_LIKES * 2)

    async with httpx.AsyncClient(verify=False, limits=limits) as client:
        async def send_single_like(entry: dict, idx: int) -> bool:
            headers = dict(headers_template)
            headers["Authorization"] = f"Bearer {entry['jwt']}"

            if idx > 0:
                await asyncio.sleep(min(idx * 0.005, 0.25))

            async with sem:
                for attempt in range(2):
                    try:
                        res = await client.post(like_url, content=enc_payload, headers=headers, timeout=REQUEST_TIMEOUT)
                        if res.status_code == 200:
                            return True
                        elif res.status_code in (401, 403):
                            return False
                        if attempt == 0:
                            await asyncio.sleep(0.2)
                    except Exception:
                        if attempt == 0:
                            await asyncio.sleep(0.2)
                return False

        tasks = [send_single_like(entry, i) for i, entry in enumerate(active_tokens)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    requests_succeeded = sum(1 for r in results if r is True)
    requests_failed = len(active_tokens) - requests_succeeded

    # Step 5: Post-Verification
    await asyncio.sleep(0.2)
    final_info = await fetch_player_info(target_uid)
    after_likes = before_likes
    if final_info.get("success"):
        after_likes = final_info["summary"].get("likes", before_likes)

    likes_added = max(0, after_likes - before_likes)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "status": "success",
        "target": {
            "uid": int(target_uid),
            "nickname": nickname,
            "region": target_region,
            "level": level,
        },
        "fleet": {
            "fleet_name": FLEET_NAME,
            "total_accounts": len(accounts),
            "cached_tokens": len(tokens),
            "requests_dispatched": len(active_tokens),
            "requests_succeeded": requests_succeeded,
            "requests_failed": requests_failed,
        },
        "likes": {
            "before": before_likes,
            "after": after_likes,
            "added": likes_added,
        },
        "execution_time_ms": elapsed_ms,
    }

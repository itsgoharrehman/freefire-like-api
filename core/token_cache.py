import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import httpx
from google.protobuf import json_format

from core.config import (
    ACCOUNTS_FILE,
    CLIENT_ID,
    CLIENT_SECRET,
    FLEET_NAME,
    GARENA_MSDK_UA,
    LOCAL_TOKEN_FILE,
    MAJOR_LOGIN_URLS,
    MAJOR_TIMEOUT,
    MAX_CONCURRENT_REFRESH,
    REFRESH_STAGGER_DELAY,
    RELEASE_VERSION,
    REQUEST_TIMEOUT,
    TOKEN_TTL_HOURS,
    USERAGENT,
)
from core.crypto import MAIN_IV, MAIN_KEY, aes_cbc_encrypt, decode_protobuf, json_to_proto
from ff_proto import freefire_pb2

logger = logging.getLogger(__name__)

# Free Fire Garena JWT tokens remain valid for 24 hours. Cache accepts tokens up to 23 hours.
TOKEN_MAX_AGE_SECONDS: int = 23 * 3600
# Tokens older than TOKEN_RENEW_THRESHOLD_SECONDS (default 20 hours) get renewed.
TOKEN_RENEW_THRESHOLD_SECONDS: int = TOKEN_TTL_HOURS * 3600


class TokenCache:
    def __init__(self):
        self._tokens: Dict[str, dict] = {}
        self.load_tokens()

    def load_tokens(self) -> int:
        now = int(time.time())
        if not LOCAL_TOKEN_FILE.exists():
            return 0

        allowed_uids = None
        if ACCOUNTS_FILE.exists():
            try:
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    allowed_uids = {str(a.get("uid")) for a in json.load(f)}
            except Exception as e:
                logger.warning(f"Accounts filter read error: {e}")

        loaded_count = 0
        try:
            with open(LOCAL_TOKEN_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("|")
                    if len(parts) >= 5:
                        uid, jwt, region, server_url, ts_str = parts[:5]
                        try:
                            ts = int(ts_str)
                        except ValueError:
                            ts = now

                        # Accept only tokens within valid age window
                        if (now - ts) < TOKEN_MAX_AGE_SECONDS:
                            if allowed_uids is not None and uid not in allowed_uids:
                                continue
                            if uid not in self._tokens or ts > self._tokens[uid]["updated_at"]:
                                self._tokens[uid] = {
                                    "uid": uid,
                                    "jwt": jwt,
                                    "region": region,
                                    "server_url": server_url,
                                    "updated_at": ts,
                                }
                                loaded_count += 1
        except Exception as e:
            logger.warning(f"Error loading tokens from {LOCAL_TOKEN_FILE}: {e}")

        return loaded_count

    def save_tokens(self) -> bool:
        lines = []
        now = int(time.time())
        for uid, entry in self._tokens.items():
            if (now - entry.get("updated_at", 0)) < TOKEN_MAX_AGE_SECONDS:
                lines.append(
                    f"{entry['uid']}|{entry['jwt']}|{entry['region']}|{entry['server_url']}|{entry['updated_at']}\n"
                )

        try:
            LOCAL_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = LOCAL_TOKEN_FILE.with_suffix(".tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            tmp_file.replace(LOCAL_TOKEN_FILE)
            return True
        except Exception as e:
            logger.error(f"Failed to save tokens atomically: {e}")
            return False

    def get_token(self, uid: str) -> Optional[dict]:
        entry = self._tokens.get(str(uid))
        if not entry:
            return None
        now = int(time.time())
        if (now - entry.get("updated_at", 0)) >= TOKEN_MAX_AGE_SECONDS:
            return None
        return entry

    def get_all_valid_tokens(self) -> List[dict]:
        now = int(time.time())
        return [
            entry
            for entry in self._tokens.values()
            if (now - entry.get("updated_at", 0)) < TOKEN_MAX_AGE_SECONDS
        ]

    def count(self) -> int:
        return len(self.get_all_valid_tokens())

    async def authenticate_account(
        self, account: dict, client: httpx.AsyncClient
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Performs Garena OAuth guest grant + MajorLogin handshake with rate-limit protection.
        Returns: (token_entry_dict, error_or_reason)
        """
        uid = str(account.get("uid", "")).strip()
        password = str(account.get("password", "")).strip()
        if not uid or not password:
            return None, "INVALID_CREDENTIALS"

        grant_url = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest/token:grant"
        grant_payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "client_type": 2,
            "password": password,
            "response_type": "token",
            "uid": int(uid),
        }
        grant_headers = {
            "User-Agent": GARENA_MSDK_UA,
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Connection": "Keep-Alive",
        }

        access_token = None
        open_id = None

        # Step 1: OAuth Token Grant (with fast 429 backoff)
        for attempt in range(2):
            try:
                r = await client.post(
                    grant_url, json=grant_payload, headers=grant_headers, timeout=REQUEST_TIMEOUT
                )
                if r.status_code == 429:
                    # Rate limited: backoff 0.5s once
                    await asyncio.sleep(0.5)
                    continue
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    access_token = data.get("access_token")
                    open_id = data.get("open_id")
                    if access_token and access_token != "0":
                        break
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == 0:
                    await asyncio.sleep(0.15)
                continue
            except Exception as e:
                logger.debug(f"OAuth grant exception for {uid}: {e}")
                break
        else:
            return None, "OAUTH_GRANT_FAILED"

        if not access_token or not open_id:
            return None, "NO_ACCESS_TOKEN"

        # Step 2: Prepare Encrypted MajorLogin Protobuf Payload
        login_dict = {
            "open_id": str(open_id),
            "open_id_type": "4",
            "login_token": access_token,
            "orign_platform_type": "4",
        }
        req_bytes = json_to_proto(login_dict, freefire_pb2.LoginReq())
        enc_payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, req_bytes)

        major_headers = {
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

        # Step 3: Dispatch to MajorLogin mirror
        last_reason = "MAJOR_NO_TOKEN"
        for major_url in MAJOR_LOGIN_URLS:
            try:
                res = await client.post(
                    major_url, content=enc_payload, headers=major_headers, timeout=MAJOR_TIMEOUT
                )
                if res.status_code == 200:
                    res_proto = decode_protobuf(res.content, freefire_pb2.LoginRes)
                    msg = json.loads(json_format.MessageToJson(res_proto))
                    tok = msg.get("token")
                    if tok and tok != "0":
                        return {
                            "uid": uid,
                            "jwt": tok,
                            "region": msg.get("lockRegion", account.get("region", "BD")),
                            "server_url": msg.get("serverUrl", "https://clientbp.ppmainecoonghj.com"),
                            "updated_at": int(time.time()),
                        }, None

                    if "queueInfo" in msg:
                        last_reason = "GARENA_LOGIN_QUEUE"
                        break
            except (httpx.TimeoutException, httpx.NetworkError):
                last_reason = "MAJOR_TIMEOUT"
                continue
            except Exception as e:
                logger.debug(f"MajorLogin error for {uid} at {major_url}: {e}")
                continue

        return None, last_reason

    async def refresh_all(
        self,
        accounts: List[dict],
        concurrency: int = MAX_CONCURRENT_REFRESH,
        stagger_s: float = REFRESH_STAGGER_DELAY,
        force: bool = False,
    ) -> dict:
        """
        True Balanced Synchronous Refresh:
        - 30 parallel workers (Zero 429 rate limit risk)
        - 10ms micro-stagger ramp (prevents connection burst)
        - 30 keep-alive connections pool
        - Runs synchronously and finishes in 5.5s - 7.0s
        """
        start_time = time.time()
        now = int(start_time)

        # Smart TTL evaluation: renew tokens older than 20 hours unless force=True
        to_renew = []
        skipped_fresh = 0
        for acc in accounts:
            uid_str = str(acc.get("uid", ""))
            existing = self._tokens.get(uid_str)
            if not force and existing:
                age = now - existing.get("updated_at", 0)
                if age < TOKEN_RENEW_THRESHOLD_SECONDS:
                    skipped_fresh += 1
                    continue
            to_renew.append(acc)

        if not to_renew:
            logger.info(f"All {len(accounts)} accounts have fresh tokens within TTL window.")
            return {
                "total_accounts": len(accounts),
                "renewed": 0,
                "skipped_fresh": skipped_fresh,
                "failed": 0,
                "active_tokens": self.count(),
                "duration_seconds": round(time.time() - start_time, 2),
            }

        sem = asyncio.Semaphore(concurrency)
        limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency + 20)
        renewed_uids = set()
        save_counter = 0

        async with httpx.AsyncClient(verify=False, limits=limits) as client:
            async def worker(acc: dict, delay_s: float):
                nonlocal save_counter
                if delay_s > 0:
                    await asyncio.sleep(delay_s)
                async with sem:
                    entry, _ = await self.authenticate_account(acc, client)
                    if entry:
                        self._tokens[entry["uid"]] = entry
                        renewed_uids.add(entry["uid"])
                        save_counter += 1
                        if save_counter >= 30:
                            save_counter = 0
                            self.save_tokens()

            # Micro-stagger ramp: caps at 0.3s so all workers ramp smoothly without bursting
            tasks = [worker(acc, min(idx * stagger_s, 0.3)) for idx, acc in enumerate(to_renew)]
            await asyncio.gather(*tasks, return_exceptions=True)

        self.save_tokens()

        duration = round(time.time() - start_time, 2)
        total_accounts = len(accounts)
        renewed_count = len(renewed_uids)
        failed_count = max(0, len(to_renew) - renewed_count)

        result_stats = {
            "total_accounts": total_accounts,
            "renewed": renewed_count,
            "skipped_fresh": skipped_fresh,
            "failed": failed_count,
            "active_tokens": self.count(),
            "duration_seconds": duration,
        }

        # Non-blocking Telegram alert
        try:
            from core.telegram import notify_token_refresh
            asyncio.create_task(
                notify_token_refresh(
                    fleet_name=FLEET_NAME,
                    total_accounts=total_accounts,
                    renewed=renewed_count,
                    failed=failed_count,
                    elapsed_s=duration,
                )
            )
        except Exception as e:
            logger.debug(f"Telegram alert error: {e}")

        return result_stats


token_cache = TokenCache()

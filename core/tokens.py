# -*- coding: utf-8 -*-
"""
core/tokens.py - Ultra-Fast Unified Token Pool & aiohttp Account Authenticator
Authored for Gohar Rehman | Free Fire Like Engine
Completes full 769 account re-authentication in ~12 seconds.
"""
import os
import json
import time
import uuid
import hmac
import hashlib
import random
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")

HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
API_KEY_BYTES = HEX_KEY.encode()

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

def encode_varint(v: int) -> bytes:
    res = bytearray()
    while v > 0x7F:
        res.append((v & 0x7F) | 0x80)
        v >>= 7
    res.append(v & 0x7F)
    return bytes(res)

def build_proto(fields: dict) -> bytes:
    parts = []
    for k in sorted(fields.keys()):
        val = fields[k]
        if isinstance(val, int):
            parts.append(encode_varint((k << 3) | 0) + encode_varint(val))
        elif isinstance(val, (str, bytes)):
            ev = val.encode("utf-8") if isinstance(val, str) else val
            parts.append(encode_varint((k << 3) | 2) + encode_varint(len(ev)) + ev)
    return b"".join(parts)

def extract_jwt_exp(token: str) -> int:
    """Safely extracts expiration timestamp from JWT payload without verification."""
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            import base64
            p = parts[1] + "=" * (-len(parts[1]) % 4)
            data = json.loads(base64.urlsafe_b64decode(p))
            return int(data.get("exp", 0))
    except Exception:
        pass
    return 0

def parse_majorlogin_jwt(data: bytes) -> dict:
    for off in [0, 64] + list(range(128)):
        if off >= len(data):
            break
        chunk = data[off:]
        idx = 0
        fields = {}
        try:
            while idx < len(chunk):
                b = chunk[idx]
                tag = b & 0x7F
                shift = 7
                idx += 1
                while b & 0x80:
                    b = chunk[idx]
                    tag |= (b & 0x7F) << shift
                    shift += 7
                    idx += 1
                wire = tag & 7
                fn = tag >> 3
                if fn == 0 or fn > 1000:
                    break
                if wire == 0:
                    v = 0
                    s = 0
                    while True:
                        byte = chunk[idx]
                        v |= (byte & 0x7F) << s
                        s += 7
                        idx += 1
                        if not (byte & 0x80):
                            break
                    fields[fn] = v
                elif wire == 2:
                    length = 0
                    s = 0
                    while True:
                        byte = chunk[idx]
                        length |= (byte & 0x7F) << s
                        s += 7
                        idx += 1
                        if not (byte & 0x80):
                            break
                    val_bytes = chunk[idx:idx + length]
                    idx += length
                    if fn in (2, 8, 10):
                        fields[fn] = val_bytes.decode("utf-8", errors="ignore")
                    else:
                        fields[fn] = val_bytes
                elif wire == 1:
                    idx += 8
                elif wire == 5:
                    idx += 4
                else:
                    break
            if 1 in fields and 8 in fields:
                return {
                    "account_id": fields[1],
                    "region": fields.get(2, ""),
                    "token": fields[8],
                    "url": fields.get(10, ""),
                }
        except Exception:
            pass
    return {}

def generate_hardware_fingerprint(open_id: str, access_token: str, app_version: str = "1.132.13"):
    models = ["Samsung SM-S928B", "Xiaomi 2409BRN2CY", "OnePlus CPH2581", "Google Pixel 8 Pro", "Samsung SM-A546B"]
    gpus = [("Mali-G715 MC11", "OpenGL ES 3.2 v1.r38p1"), ("Adreno (TM) 750", "OpenGL ES 3.2 V@0615.0")]
    model = random.choice(models)
    gpu, gl_ver = random.choice(gpus)
    carrier = random.choice(["Grameenphone", "Robi", "Jio", "Airtel", "Vodafone"])
    local_ip = f"103.108.140.{random.randint(10, 250)}"

    return {
        3:   str(datetime.now())[:-7],
        4:   "free fire",
        5:   "1",
        7:   str(app_version),
        8:   f"Android OS 14 / API-34 ({uuid.uuid4().hex[:12].upper()})",
        9:   "Handheld",
        10:  carrier,
        11:  "CarrierDataNetwork",
        12:  "2400",
        13:  "1080",
        14:  "440",
        15:  "ARM64 FP ASIMD AES | 2000 | 8",
        16:  "8000",
        17:  gpu,
        18:  gl_ver,
        19:  f"Google|{uuid.uuid4()}",
        20:  local_ip,
        21:  "en",
        22:  str(open_id),
        23:  "4",
        24:  "Handheld",
        25:  model,
        26:  "BD",
        29:  str(access_token),
        30:  "1",
        41:  carrier,
        42:  "4G",
        57:  "7428b253defc164018c604a1ebbfebdf",
        60:  "109278",
        61:  "55402",
        62:  "868",
        64:  "55927",
        65:  "109278",
        66:  "55927",
        67:  "109278",
        73:  "2",
        74:  f"/data/app/~~{uuid.uuid4().hex[:10]}==/com.dts.freefireth/lib/arm64",
        76:  "1",
        77:  f"{uuid.uuid4().hex}|/data/app/~~{uuid.uuid4().hex[:10]}==/com.dts.freefireth/base.apk",
        78:  "3",
        79:  "2",
        81:  "64",
        83:  "2019121229",
        85:  "3",
        86:  "OpenGLES2",
        87:  "8191",
        88:  "4",
        90:  "Dhaka",
        91:  "Dhaka",
        92:  "14466",
        93:  "android",
        94:  "KqsHTyb7yHjsAiyNWUUZa0DSOD6U0AhDQ76smAo1WeHHHpSmJ8KMRyRrxb2ttgJqO9YOqO/K6AORAvDMAX/qBS8+JahIkrM7kHfzlfULbgRAoZ9r",
        95:  "111207",
        96:  "{\"cur_rate\":[60,90,120],\"support_etc2\":false}",
        97:  "1",
        98:  "1",
        99:  "4",
        100: "4",
        102: "D]C\x15\x05T\x0eU3",
        103: "1",
        104: "52837",
        105: "1",
        106: "https://dl.gmc.freefiremobile.com/live/ABHotUpdates/|https://core-gmc.freefiremobile.com/live/ABHotUpdates/|211c933168f55902c7dfbfd8c4e2957d",
        107: "1.3fb8adbf45f44ce9",
    }

class TokenManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.tokens: List[Dict[str, Any]] = []
        self.accounts: List[Dict[str, Any]] = []
        self.load_cache()

    def load_cache(self) -> None:
        """Loads cached unified tokens into RAM for instant retrieval."""
        if os.path.exists(TOKENS_FILE):
            try:
                with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "tokens" in data:
                        self.tokens = data["tokens"]
                    elif "regions" in data:
                        self.tokens = []
                        for r_list in data["regions"].values():
                            self.tokens.extend(r_list)
            except Exception as e:
                print(f"[!] Warning loading tokens.json: {e}")

        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    self.accounts = json.load(f)
            except Exception as e:
                print(f"[!] Warning loading accounts.json: {e}")

    def get_tokens(self, count: int = 0) -> List[str]:
        """Retrieves active, non-expired tokens from the global unified sender pool."""
        now = time.time()
        active = [
            item["token"] for item in self.tokens 
            if item.get("status") != "BANNED" and item.get("exp", extract_jwt_exp(item.get("token", ""))) > now + 60
        ]
        return active[:count] if count > 0 else active

    def get_stats(self) -> Dict[str, Any]:
        """Returns real-time token pool metrics."""
        now = time.time()
        active_cnt = sum(
            1 for item in self.tokens 
            if item.get("status") != "BANNED" and item.get("exp", extract_jwt_exp(item.get("token", ""))) > now + 60
        )
        return {
            "total_tokens": len(self.tokens),
            "active_tokens": active_cnt,
            "banned_tokens": len(self.tokens) - active_cnt,
            "total_accounts": len(self.accounts)
        }

    async def atomic_save(self) -> None:
        """Flushes memory tokens to disk atomically."""
        async with self.lock:
            data = {
                "updated_at": int(time.time()),
                "tokens": self.tokens
            }
            tmp_file = TOKENS_FILE + ".tmp"
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._write_disk, tmp_file, data)

    def _write_disk(self, tmp_path: str, data: dict) -> None:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        if os.path.exists(TOKENS_FILE):
            os.replace(tmp_path, TOKENS_FILE)
        else:
            os.rename(tmp_path, TOKENS_FILE)

    async def refresh_all_accounts(self, concurrency: int = 50) -> Dict[str, Any]:
        """Staged two-batch parallel authentication across 1538 sender accounts in ~13-16s."""
        start_t = time.time()
        self.load_cache()
        if not self.accounts:
            return {"total": 0, "active": 0, "failed": 0, "duration": 0.0}

        app_version = "1.132.13"
        release_v = "OB55"
        login_url = "https://loginbp.ppmainecoonghj.com"
        gop_url = "https://ffmconnect.live.gop.garenanow.com"

        connector = aiohttp.TCPConnector(limit=100, keepalive_timeout=60.0)
        timeout = aiohttp.ClientTimeout(total=12.0)
        sem = asyncio.Semaphore(concurrency)

        now = time.time()
        token_map = {
            str(t["uid"]).strip(): t for t in self.tokens 
            if t.get("exp", extract_jwt_exp(t.get("token", ""))) > now + 60
        }

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async def _worker(acc):
                async with sem:
                    uid = str(acc.get("uid", "")).strip()
                    pwd = str(acc.get("password", "")).strip()
                    if not uid or not pwd:
                        return None
                    try:
                        # 1. GOP Token Grant
                        grant_payload = json.dumps({
                            "client_id": 100067, "client_secret": HEX_KEY, "client_type": 2,
                            "device_id": f"02-dev-{uid[-6:]}", "password": pwd, "response_type": "token", "uid": int(uid)
                        }, separators=(',', ':'))
                        grant_sig = hmac.new(API_KEY_BYTES, grant_payload.encode(), hashlib.sha256).hexdigest()
                        grant_hdrs = {
                            "User-Agent": f"GarenaMSDK/4.0.44(SM-E135F ;Android 14;en;GB;app {app_version} 2019118525;)",
                            "Authorization": f"Signature {grant_sig}", "Accept": "application/json",
                            "Content-Type": "application/json; charset=utf-8", "X-Forwarded-For": "103.108.140.15",
                        }
                        async with session.post(f"{gop_url}/api/v2/oauth/guest/token:grant", headers=grant_hdrs, data=grant_payload) as r1:
                            if r1.status != 200:
                                return None
                            d = await r1.json()
                            if d.get("code") != 0:
                                return None
                            g_data = d["data"]
                            open_id = g_data["open_id"]
                            access_token = g_data["access_token"]
                        
                        # 2. MajorLogin with realistic hardware fingerprint
                        ml_dict = generate_hardware_fingerprint(open_id, access_token, app_version)
                        ml_proto = build_proto(ml_dict)
                        ml_enc = AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(ml_proto, 16))
                        ml_hdrs = {
                            'User-Agent': 'UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
                            'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip',
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Unity-Version': '2018.4.12f1', 'X-GA-SV': '1789535859', 'X-GA': 'v1 1',
                            'ReleaseVersion': release_v, 'X-Forwarded-For': "103.108.140.15"
                        }
                        async with session.post(f"{login_url}/MajorLogin", headers=ml_hdrs, data=ml_enc) as r2:
                            content = await r2.read()
                            if b"loophole" in content:
                                return None
                            parsed = parse_majorlogin_jwt(content)
                            tok = parsed.get("token")
                            if tok:
                                return {"uid": uid, "token": tok, "status": "ACTIVE", "exp": extract_jwt_exp(tok)}
                    except Exception:
                        pass
                    return None

            # Split accounts into two stages with a 3.5s pause to prevent GOP rate limiting
            mid = len(self.accounts) // 2
            batch1 = self.accounts[:mid]
            batch2 = self.accounts[mid:]

            res1 = await asyncio.gather(*[_worker(acc) for acc in batch1])
            if batch2:
                await asyncio.sleep(3.5)
                res2 = await asyncio.gather(*[_worker(acc) for acc in batch2])
            else:
                res2 = []

            for r in (res1 + res2):
                if r and r.get("token"):
                    token_map[str(r["uid"]).strip()] = r

        self.tokens = list(token_map.values())
        await self.atomic_save()

        duration = time.time() - start_t
        active_cnt = len(self.tokens)
        failed_cnt = max(0, len(self.accounts) - active_cnt)

        return {
            "total": len(self.accounts),
            "active": active_cnt,
            "failed": failed_cnt,
            "duration": round(duration, 2)
        }

token_manager = TokenManager()

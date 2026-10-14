import os
from pathlib import Path
from typing import Set

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Attempt to load local .env if available
env_path = BASE_DIR / ".env"
if env_path.exists():
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k:
                        os.environ[k] = v
    except Exception:
        pass

# Security & Fleet Identification
API_KEY: str = os.getenv("API_KEY", "").strip()
FLEET_NAME: str = os.getenv("FLEET_NAME", "GLOBAL").strip()

# Garena Client Credentials
CLIENT_ID: int = int(os.getenv("CLIENT_ID", "100067"))
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "").strip()

# Balanced High-Performance Concurrency & Timeouts (Rate-Limit Safe)
MAX_CONCURRENT_LIKES: int = int(os.getenv("MAX_CONCURRENT_LIKES", "35"))
MAX_CONCURRENT_REFRESH: int = int(os.getenv("MAX_CONCURRENT_REFRESH", "30"))
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "4.5"))
MAJOR_TIMEOUT: float = float(os.getenv("MAJOR_TIMEOUT", "4.0"))
REFRESH_STAGGER_DELAY: float = float(os.getenv("REFRESH_STAGGER_DELAY", "0.01"))
TOKEN_TTL_HOURS: int = int(os.getenv("TOKEN_TTL_HOURS", "20"))

# Garena Free Fire Protocol Headers & Versioning
RELEASE_VERSION: str = "OB55"
USERAGENT: str = "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
GARENA_MSDK_UA: str = "GarenaMSDK/4.0.19P9(A063 ;Android 13;en;IN;)"

# Garena Game Server Gateways
GATEWAY_IND: str = "https://client.ind.freefiremobile.com"
GATEWAY_US: str = "https://client.us.freefiremobile.com"
GATEWAY_DEFAULT: str = "https://clientbp.ppmainecoonghj.com"

# MajorLogin Mirrors
MAJOR_LOGIN_URLS = [
    "https://loginbp.ppmainecoonghj.com/MajorLogin",
    "https://loginbp.ggwhitehawk.com/MajorLogin",
    "https://loginbp.ggpolarbear.com/MajorLogin",
]

# File Paths
ACCOUNTS_FILE: Path = DATA_DIR / "accounts.json"
LOCAL_TOKEN_FILE: Path = DATA_DIR / "token.txt"


def get_gateway_by_region(region: str) -> str:
    reg = (region or "").strip().upper()
    if reg == "IND":
        return GATEWAY_IND
    elif reg in {"BR", "US", "SAC", "NA"}:
        return GATEWAY_US
    else:
        return GATEWAY_DEFAULT

import os
from typing import Dict
from dotenv import load_dotenv

# Load local .env fallback if present
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=False)

# Core API Configuration
API_KEY = os.environ.get("API_KEY", "").strip()
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

# Concurrency & Request Configuration
BATCH_CHUNK_SIZE = int(os.environ.get("BATCH_CHUNK_SIZE", 40))
BATCH_STAGGER_DELAY = float(os.environ.get("BATCH_STAGGER_DELAY", 0.035))
MAX_KEEPALIVE_CONNECTIONS = int(os.environ.get("MAX_KEEPALIVE_CONNECTIONS", 150))
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", 10.0))

# Upstream Game Gateway Configuration
ACTIVE_GATEWAY = os.environ.get("ACTIVE_GATEWAY", "https://clientbp.ppmainecoonghj.com").strip()

GATEWAY_URLS: Dict[str, str] = {
    "PK": ACTIVE_GATEWAY,
    "BD": ACTIVE_GATEWAY,
    "IND": ACTIVE_GATEWAY,
    "INDIA": ACTIVE_GATEWAY,
    "ME": ACTIVE_GATEWAY,
    "ID": ACTIVE_GATEWAY,
    "BR": ACTIVE_GATEWAY,
    "NA": ACTIVE_GATEWAY,
    "US": ACTIVE_GATEWAY,
    "SAC": ACTIVE_GATEWAY,
    "VN": ACTIVE_GATEWAY,
    "TH": ACTIVE_GATEWAY,
    "SG": ACTIVE_GATEWAY,
    "RU": ACTIVE_GATEWAY,
    "TW": ACTIVE_GATEWAY,
    "EU": ACTIVE_GATEWAY,
    "EUROPE": ACTIVE_GATEWAY,
    "GLOBAL": ACTIVE_GATEWAY,
}

DEFAULT_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Unity-Version": "2018.4.11f1",
    "X-GA": "v1 1",
    "ReleaseVersion": "OB55",
}

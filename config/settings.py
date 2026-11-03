# -*- coding: utf-8 -*-
"""
config/settings.py - Private Free Fire Like API Configuration
Authored for Gohar Rehman | High-Performance Like Engine
Unified Multi-Region Routing for all 14 Free Fire Regions
"""
import os
from typing import Dict
from dotenv import load_dotenv

# Load .env file from project root
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=env_path)

# Private API Key Protection
API_KEY = os.environ.get("API_KEY", "gohar-fflive-98274a1f3c8e5d2b").strip()

# Telegram Notification Settings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8534693264:AAHU-zh4L963QuTmQg2SKCXkOBD0vl74N2c")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1004388365786")

# Server Binding
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

# Performance & Pipelined Concurrency Tuning
BATCH_CHUNK_SIZE = int(os.environ.get("BATCH_CHUNK_SIZE", 40))
BATCH_STAGGER_DELAY = float(os.environ.get("BATCH_STAGGER_DELAY", 0.035))  # 35ms micro-delay between chunks
MAX_KEEPALIVE_CONNECTIONS = int(os.environ.get("MAX_KEEPALIVE_CONNECTIONS", 150))
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", 10.0))

# Active Verified Garena Gateway (Handles all 14 regions)
ACTIVE_GATEWAY = "https://clientbp.ppmainecoonghj.com"

# Regional Gateway Base URLs (Unified to active Garena edge gateway)
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

# Garena Protocol Wire Headers
DEFAULT_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/x-www-form-urlencoded",
    "Expect": "100-continue",
    "X-Unity-Version": "2018.4.11f1",
    "X-GA": "v1 1",
    "ReleaseVersion": "OB55",
}

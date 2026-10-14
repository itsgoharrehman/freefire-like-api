import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import API_KEY, FLEET_NAME
from core.engine import (
    fetch_player_info,
    load_accounts,
    send_fleet_likes,
)
from core.telegram import (
    notify_downtime_alert,
    notify_like_failure,
    notify_like_success,
    notify_token_refresh,
)
from core.token_cache import token_cache

app = FastAPI(
    title=f"Free Fire Multi-Region Like API - {FLEET_NAME}",
    description="High-speed parallel Free Fire like sending API with multi-region fleet (BD, ME, PK)",
    version="3.0.0",
    docs_url="/docs",
    redoc_url=None,
)

router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP_START_TIME = time.time()


def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None),
):
    current_key = os.getenv("API_KEY", API_KEY).strip()
    if not current_key:
        return True

    provided = None
    if x_api_key:
        provided = x_api_key.strip()
    elif authorization:
        auth_str = authorization.strip()
        if auth_str.lower().startswith("bearer "):
            provided = auth_str[7:].strip()
        else:
            provided = auth_str
    elif api_key:
        provided = api_key.strip()

    if provided != current_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing or invalid API key. Pass via X-API-Key header, Authorization Bearer, or api_key query param.",
        )
    return True


class LikeRequest(BaseModel):
    uid: int


@router.get("/")
async def root():
    return {
        "service": "Free Fire Multi-Region Fleet Like API",
        "fleet": FLEET_NAME,
        "regions": ["BD", "ME", "PK"],
        "status": "online",
        "endpoints": [
            "/health",
            "/refresh",
            "/like?uid={target_uid}",
            "/info?uid={target_uid}",
        ],
    }


@router.get("/health")
async def health():
    accounts = load_accounts()
    valid_tokens = token_cache.get_all_valid_tokens()
    uptime_sec = round(time.time() - APP_START_TIME, 1)

    return {
        "status": "healthy",
        "fleet": FLEET_NAME,
        "accounts_configured": len(accounts),
        "active_cached_tokens": len(valid_tokens),
        "uptime_seconds": uptime_sec,
        "timestamp": int(time.time()),
    }


@router.api_route("/refresh", methods=["GET", "POST"])
async def refresh_tokens_synchronous(
    force: bool = Query(False, description="Force re-authentication for all accounts ignoring TTL"),
    authorized: bool = Depends(require_api_key),
):
    """
    True balanced synchronous token renewal:
    Executes across all configured fleet accounts in 5.5 to 7.0 seconds.
    Directly returns verified renewal counts with zero cronjob timeout risk.
    """
    accounts = load_accounts()
    if not accounts:
        raise HTTPException(status_code=500, detail="No accounts configured in fleet.")

    result = await token_cache.refresh_all(accounts, force=force)
    return {
        "status": "success",
        "fleet": FLEET_NAME,
        "result": result,
    }


@router.get("/like")
async def like_player_get(
    uid: int = Query(..., description="Target player in-game UID"),
    authorized: bool = Depends(require_api_key),
):
    res = await send_fleet_likes(uid)
    if res.get("status") == "error":
        msg = res.get("message", "")
        code = 404 if "not found" in msg.lower() else (503 if "no active" in msg.lower() else 500)
        try:
            asyncio.create_task(notify_like_failure(FLEET_NAME, uid, msg, code))
        except Exception:
            pass
        raise HTTPException(status_code=code, detail=msg)

    try:
        elapsed_s = round(res.get("execution_time_ms", 0) / 1000.0, 2)
        asyncio.create_task(
            notify_like_success(FLEET_NAME, res["target"], res["likes"], res["fleet"], elapsed_s)
        )
    except Exception:
        pass

    return res


@router.post("/like")
async def like_player_post(
    req: LikeRequest,
    authorized: bool = Depends(require_api_key),
):
    res = await send_fleet_likes(req.uid)
    if res.get("status") == "error":
        msg = res.get("message", "")
        code = 404 if "not found" in msg.lower() else (503 if "no active" in msg.lower() else 500)
        try:
            asyncio.create_task(notify_like_failure(FLEET_NAME, req.uid, msg, code))
        except Exception:
            pass
        raise HTTPException(status_code=code, detail=msg)

    try:
        elapsed_s = round(res.get("execution_time_ms", 0) / 1000.0, 2)
        asyncio.create_task(
            notify_like_success(FLEET_NAME, res["target"], res["likes"], res["fleet"], elapsed_s)
        )
    except Exception:
        pass

    return res


@router.get("/info")
async def player_info(
    uid: int = Query(..., description="Target player in-game UID"),
    authorized: bool = Depends(require_api_key),
):
    res = await fetch_player_info(uid)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Player not found or inaccessible."))
    return res


# Mount routes at root only (legacy /bd prefix completely removed)
app.include_router(router)

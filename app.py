# -*- coding: utf-8 -*-
"""
app.py - High-Performance Private Free Fire Like API
Authored for Gohar Rehman | Free Fire Like Engine
"""
import time
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from fastapi.responses import JSONResponse

from config.settings import API_KEY, PORT, HOST
from core.tokens import token_manager
from core.dispatcher import like_dispatcher
from core.telegram import send_telegram_report, format_token_refresh_report

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="key", auto_error=False)

# Authorized API keys - strictly single-key from environment
if not API_KEY or len(API_KEY.strip()) < 8:
    raise RuntimeError("CRITICAL: API_KEY environment variable is not configured or too short.")

VALID_API_KEYS = {API_KEY.strip()}
print(f"[DEBUG] Valid API Keys loaded: {[k for k in VALID_API_KEYS]}")

def verify_api_key(
    key_hdr: str = Security(api_key_header),
    key_qry: str = Security(api_key_query)
) -> str:
    """Strict private API key verification middleware."""
    provided_key = key_hdr or key_qry
    if not provided_key or provided_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing API key"
        )
    return provided_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    await like_dispatcher.init_session()
    print(f"\033[92m[+] Private Free Fire Like API Live on port {PORT}\033[0m")
    yield
    await like_dispatcher.close_session()

app = FastAPI(
    title="GOHAR REHMAN | FREE FIRE LIKE API",
    description="High-Speed Private Free Fire Like Engine with 1538+ Level 8+ Sender Accounts",
    version="2.2.0",
    lifespan=lifespan
)

@app.get("/", tags=["Info"])
async def root():
    return {
        "engine": "Gohar Rehman Free Fire Like API",
        "version": "2.1.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/v1/like", tags=["Like Engine"])
async def give_likes(
    uid: int = Query(..., description="Target Free Fire Player UID"),
    region: str = Query("GLOBAL", description="Target Player Region (PK, BD, IND, US, BR, GLOBAL)"),
    count: int = Query(1538, description="Number of likes to dispatch (up to full pool)", ge=1, le=2000),
    auth: str = Depends(verify_api_key)
):
    res = await like_dispatcher.dispatch_likes(target_uid=uid, region=region.upper(), requested_count=count)
    if res.get("status") == "error":
        return JSONResponse(status_code=400, content=res)
    return res

@app.get("/api/v1/profile", tags=["Profile Lookup"])
async def get_player_profile(
    uid: int = Query(..., description="Target Free Fire Player UID"),
    region: str = Query("GLOBAL", description="Target Player Region"),
    auth: str = Depends(verify_api_key)
):
    profile = await like_dispatcher.query_player_profile(target_uid=uid, region=region.upper())
    if not profile:
        raise HTTPException(status_code=404, detail="Player profile not found or gateway unavailable")
    return {"status": "success", "profile": profile}

@app.get("/api/v1/tokens/status", tags=["Token Management"])
async def get_tokens_status(auth: str = Depends(verify_api_key)):
    return {"status": "success", "metrics": token_manager.get_stats()}

@app.get("/api/v1/cron/refresh", tags=["External Cron Webhooks"])
async def cron_refresh_tokens(auth: str = Depends(verify_api_key)):
    res = await token_manager.refresh_all_accounts(concurrency=50)
    await send_telegram_report(
        format_token_refresh_report(
            total=res["total"],
            active=res["active"],
            failed=res["failed"],
            duration=res["duration"]
        )
    )
    return {
        "status": "success",
        "action": "token_refresh_completed",
        "total": res["total"],
        "active": res["active"],
        "failed": res["failed"],
        "duration": res["duration"]
    }

@app.get("/api/v1/cron/ping", tags=["External Cron Webhooks"])
async def cron_health_ping(auth: str = Depends(verify_api_key)):
    return {"status": "healthy", "timestamp": int(time.time()), "active_tokens": token_manager.get_stats()["active_tokens"]}

# Legacy route aliases
@app.get("/health", tags=["Legacy Aliases"])
async def legacy_health():
    return {"status": "healthy", "timestamp": int(time.time()), "active_tokens": token_manager.get_stats()["active_tokens"]}

@app.get("/refresh", tags=["Legacy Aliases"])
async def legacy_refresh(
    api_key: Optional[str] = Query(None),
    key: Optional[str] = Query(None)
):
    provided = api_key or key
    if not provided or provided not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await cron_refresh_tokens(auth=provided)

@app.get("/like", tags=["Legacy Aliases"])
async def legacy_like(
    uid: int = Query(...),
    region: str = Query("GLOBAL"),
    count: int = Query(1538),
    api_key: Optional[str] = Query(None),
    key: Optional[str] = Query(None)
):
    provided = api_key or key
    if not provided or provided not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await give_likes(uid=uid, region=region, count=count, auth=provided)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False, workers=1)

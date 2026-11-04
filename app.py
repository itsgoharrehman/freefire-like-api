import time
import asyncio
import hmac
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from fastapi.responses import JSONResponse

from config.settings import API_KEY, PORT, HOST
from core.tokens import token_manager
from core.dispatcher import like_dispatcher
from core.notifier import notifier, format_token_refresh_report

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="key", auto_error=False)

def verify_api_key(
    key_hdr: Optional[str] = Security(api_key_header),
    key_qry: Optional[str] = Security(api_key_query)
) -> str:
    """Constant-time API key verification."""
    provided = (key_hdr or key_qry or "").strip()
    active_key = API_KEY.strip()
    if not active_key or not provided or not hmac.compare_digest(provided, active_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return provided

@asynccontextmanager
async def lifespan(app: FastAPI):
    await like_dispatcher.init_session()
    yield
    await like_dispatcher.close_session()

app = FastAPI(
    title="Free Fire Like API",
    version="2.6.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "service": "Free Fire Like API",
        "version": "2.6.0",
        "status": "online"
    }

@app.get("/api/v1/like")
async def give_likes(
    uid: int = Query(..., description="Target player UID"),
    region: str = Query("GLOBAL", description="Target region"),
    count: int = Query(1250, description="Likes count", ge=1, le=2000),
    auth: str = Depends(verify_api_key)
):
    res = await like_dispatcher.dispatch_likes(target_uid=uid, region=region.upper(), requested_count=count)
    if res.get("status") == "error":
        return JSONResponse(status_code=400, content=res)
    return res

@app.get("/api/v1/profile")
async def get_player_profile(
    uid: int = Query(..., description="Target player UID"),
    region: str = Query("GLOBAL", description="Target region"),
    auth: str = Depends(verify_api_key)
):
    profile = await like_dispatcher.query_player_profile(target_uid=uid, region=region.upper())
    if not profile:
        raise HTTPException(status_code=404, detail="Player profile not found")
    return {"status": "success", "profile": profile}

@app.get("/api/v1/tokens/status")
async def get_tokens_status(auth: str = Depends(verify_api_key)):
    return {"status": "success", "metrics": token_manager.get_stats()}

@app.get("/api/v1/cron/refresh")
async def cron_refresh_tokens(auth: str = Depends(verify_api_key)):
    res = await token_manager.refresh_all_accounts(concurrency=50)
    await notifier.send_report(
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

@app.get("/api/v1/cron/ping")
async def cron_health_ping(auth: str = Depends(verify_api_key)):
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "active_tokens": token_manager.get_stats()["active_tokens"]
    }

# Legacy Route Aliases
@app.get("/health")
async def legacy_health():
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "active_tokens": token_manager.get_stats()["active_tokens"]
    }

@app.get("/refresh")
async def legacy_refresh(
    api_key: Optional[str] = Query(None),
    key: Optional[str] = Query(None)
):
    provided = api_key or key or ""
    return await cron_refresh_tokens(auth=provided)

@app.get("/like")
async def legacy_like(
    uid: int = Query(...),
    region: str = Query("GLOBAL"),
    count: int = Query(1250),
    api_key: Optional[str] = Query(None),
    key: Optional[str] = Query(None)
):
    provided = api_key or key or ""
    return await give_likes(uid=uid, region=region, count=count, auth=provided)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False, workers=1)

"""POST /api/route (자유 입력 분류), GET /api/usage (토큰 사용량)"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..core import Core
from ..deps import get_core, require_team_key
from ..services.router import route

router = APIRouter(prefix="/api", tags=["system"], dependencies=[Depends(require_team_key)])


class RouteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.post("/route")
async def post_route(body: RouteRequest, core: Core = Depends(get_core)):
    return await route(core, body.text)


@router.get("/usage")
async def get_usage(recent: int = Query(20, ge=0, le=200), core: Core = Depends(get_core)):
    settings = core.settings
    live = core.hcx.usage.live_totals()
    return {
        **core.hcx.usage.summary(recent),
        "mock": settings.mock,
        "limits": {
            "max_live_calls": settings.max_live_calls,
            "used_live_calls": live["live_calls"],
            "token_stop_threshold": settings.token_stop_threshold,
            "used_tokens": live["total_tokens"],
        },
    }

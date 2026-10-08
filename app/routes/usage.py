"""GET /api/usage — 기능별·모델별 토큰 사용량, 한도, 최근 호출."""
from fastapi import APIRouter, Depends, Query

from ..core import Core
from ..deps import get_core, require_team_key

router = APIRouter(prefix="/api", tags=["usage"], dependencies=[Depends(require_team_key)])


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

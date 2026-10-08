"""POST /api/route — 자유 입력을 어떤 기능(compose/coach/interpret/rehearsal)으로 보낼지 분류."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..core import Core
from ..deps import get_core, require_team_key
from ..services.route import route

router = APIRouter(prefix="/api", tags=["route"], dependencies=[Depends(require_team_key)])


class RouteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.post("/route")
async def post_route(body: RouteRequest, core: Core = Depends(get_core)):
    return await route(core, body.text)

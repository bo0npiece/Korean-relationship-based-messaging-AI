"""① POST /api/compose — 관계·목적·핵심 내용 → 메시지 초안."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..core import Core
from ..deps import get_core, require_team_key
from ..services.compose import compose

router = APIRouter(prefix="/api", tags=["compose"], dependencies=[Depends(require_team_key)])


class ComposeRequest(BaseModel):
    key_points: str = Field(min_length=1, max_length=2000, description="전하고 싶은 핵심 내용")
    relation: str | None = None
    purpose: str | None = None
    contact_id: int | None = None


@router.post("/compose")
async def post_compose(body: ComposeRequest, core: Core = Depends(get_core)):
    return await compose(core, body.key_points, body.relation, body.purpose, body.contact_id)

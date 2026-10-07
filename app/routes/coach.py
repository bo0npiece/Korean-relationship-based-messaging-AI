"""POST /api/coach"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..core import Core
from ..deps import get_core, require_team_key
from ..services.coach import coach

router = APIRouter(prefix="/api", tags=["coach"], dependencies=[Depends(require_team_key)])


class CoachRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000, description="코칭받을 내 메시지")
    relation: str | None = Field(default=None, description="domain.yaml relations의 id 또는 자유 입력")
    purpose: str | None = Field(default=None, description="domain.yaml purposes의 id 또는 자유 입력")
    contact_id: int | None = Field(default=None, description="관계 메모리의 상대 id (선택)")


@router.post("/coach")
async def post_coach(body: CoachRequest, core: Core = Depends(get_core)):
    return await coach(core, body.text, body.relation, body.purpose, body.contact_id)

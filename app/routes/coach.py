"""POST /api/coach"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..customize import Customize
from ..deps import get_customize, get_hcx, require_team_key
from ..hcx import HCXClient
from ..services.coach import coach

router = APIRouter(prefix="/api", tags=["coach"], dependencies=[Depends(require_team_key)])


class CoachRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000, description="코칭받을 내 메시지")
    relation: str | None = Field(default=None, description="domain.yaml relations의 id 또는 자유 입력")
    purpose: str | None = Field(default=None, description="domain.yaml purposes의 id 또는 자유 입력")


@router.post("/coach")
async def post_coach(body: CoachRequest, hcx: HCXClient = Depends(get_hcx),
                     customize: Customize = Depends(get_customize)):
    return await coach(hcx, customize, body.text, body.relation, body.purpose)

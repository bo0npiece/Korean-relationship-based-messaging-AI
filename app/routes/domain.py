"""domain.yaml 내용 제공 (프론트 선택지용)."""
from fastapi import APIRouter, Depends

from ..customize import Customize
from ..deps import get_customize, require_team_key

router = APIRouter(prefix="/api", tags=["domain"], dependencies=[Depends(require_team_key)])


@router.get("/domain")
async def get_domain(customize: Customize = Depends(get_customize)):
    # 요청마다 다시 읽으므로 domain.yaml 수정이 바로 반영됨
    return customize.domain()

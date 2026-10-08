"""GET /api/domain — domain.yaml 내용 (프론트 선택지: 관계·목적·시나리오)."""
from fastapi import APIRouter, Depends

from ..core import Core
from ..deps import get_core, require_team_key

router = APIRouter(prefix="/api", tags=["domain"], dependencies=[Depends(require_team_key)])


@router.get("/domain")
async def get_domain(core: Core = Depends(get_core)):
    # 요청마다 다시 읽으므로 domain.yaml 수정이 바로 반영됨
    return core.customize.domain()

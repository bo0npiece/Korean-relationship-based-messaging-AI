"""domain.yaml 내용 제공 (프론트 선택지용) + 참고 자료 검색 확인용."""
from fastapi import APIRouter, Depends, Query

from ..core import Core
from ..deps import get_core, require_team_key

router = APIRouter(prefix="/api", tags=["domain"], dependencies=[Depends(require_team_key)])


@router.get("/domain")
async def get_domain(core: Core = Depends(get_core)):
    # 요청마다 다시 읽으므로 domain.yaml 수정이 바로 반영됨
    return core.customize.domain()


@router.get("/knowledge/search")
async def search_knowledge(q: str = Query(min_length=1, max_length=500), k: int = Query(3, ge=1, le=10),
                           core: Core = Depends(get_core)):
    # knowledge/*.md 검색 결과 확인용 (프롬프트에 무엇이 들어가는지 점검)
    return await core.knowledge.search(q, k)

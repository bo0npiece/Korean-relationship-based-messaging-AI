"""GET /api/knowledge/search — customize/knowledge 검색 결과 확인 (프롬프트에 무엇이 들어가는지 점검)."""
from fastapi import APIRouter, Depends, Query

from ..core import Core
from ..deps import get_core, require_team_key

router = APIRouter(prefix="/api", tags=["knowledge"], dependencies=[Depends(require_team_key)])


@router.get("/knowledge/search")
async def search_knowledge(q: str = Query(min_length=1, max_length=500), k: int = Query(3, ge=1, le=10),
                           core: Core = Depends(get_core)):
    return await core.knowledge.search(q, k)

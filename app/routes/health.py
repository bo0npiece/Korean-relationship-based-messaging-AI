"""GET /api/health — 서버 상태, MOCK 여부, 모델 설정."""
from fastapi import APIRouter, Depends

from ..config import Settings
from ..deps import get_settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    # 키 값 자체는 절대 내보내지 않음
    return {
        "ok": True,
        "mock": settings.mock,
        "mock_reason": settings.mock_reason,
        "api_key_configured": bool(settings.api_key),
        "models": {
            "analysis": settings.model_analysis,
            "vision": settings.model_vision,
            "light": settings.model_light,
        },
        "customize_dir_exists": settings.customize_dir.is_dir(),
    }

"""라우트 공통 의존성."""
import hmac

from fastapi import Header, HTTPException, Request

from .config import Settings
from .customize import Customize
from .hcx import HCXClient


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_hcx(request: Request) -> HCXClient:
    return request.app.state.hcx


def get_customize(request: Request) -> Customize:
    return request.app.state.customize


async def require_team_key(request: Request, x_team_key: str = Header(default="")):
    # TEAM_API_KEY를 설정했을 때만 검사 (Step 4부터 /api 라우트에 붙임)
    team_key = get_settings(request).team_key
    if team_key and not hmac.compare_digest(x_team_key.encode(), team_key.encode()):
        raise HTTPException(401, "X-Team-Key를 확인하세요.")

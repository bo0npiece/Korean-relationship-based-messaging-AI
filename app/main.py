"""FastAPI 앱 조립. 실행: uvicorn app.main:app

백엔드 전용입니다. 프론트는 CORS_ORIGINS에 주소를 넣고 /api/* 를 직접 호출합니다.
기능을 빼려면 아래 include_router 줄과 routes/·services/의 같은 이름 파일을 지우면 됩니다.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from .config import Settings
from .core import Core
from .customize import CustomizeError
from .hcx import HCXError
from .routes import coach, compose, contacts, domain, health, interpret, knowledge, rehearsal, route, usage


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="한국어 관계 기반 메시지 코치 API", version="0.1.0")
    app.state.core = Core.build(settings)

    @app.exception_handler(HCXError)
    async def hcx_error(request: Request, error: HCXError):
        # HCX 실패를 프론트가 읽기 쉬운 {"detail": ...}로 변환
        return JSONResponse(status_code=error.status_code, content={"detail": error.message})

    @app.exception_handler(CustomizeError)
    async def customize_error(request: Request, error: CustomizeError):
        return JSONResponse(status_code=500, content={"detail": f"customize 설정 오류: {error}"})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Team-Key"],
    )

    # 시스템
    app.include_router(health.router)      # GET  /api/health
    app.include_router(domain.router)      # GET  /api/domain
    app.include_router(usage.router)       # GET  /api/usage
    # 기능
    app.include_router(compose.router)     # ① POST /api/compose
    app.include_router(coach.router)       # ② POST /api/coach
    app.include_router(interpret.router)   # ③ POST /api/interpret
    app.include_router(rehearsal.router)   # ④ /api/rehearsal/*
    app.include_router(contacts.router)    # ⑤ /api/contacts
    app.include_router(route.router)       # POST /api/route
    app.include_router(knowledge.router)   # GET  /api/knowledge/search

    @app.get("/", include_in_schema=False)
    async def index():
        return RedirectResponse("/docs")

    return app


app = create_app()

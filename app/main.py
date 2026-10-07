"""FastAPI 앱 조립. 실행: uvicorn app.main:app"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from .config import Settings
from .customize import Customize, CustomizeError
from .hcx import HCXClient, HCXError
from .routes import coach, domain, health


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="한국어 관계 기반 메시지 코치 API", version="0.1.0")
    app.state.settings = settings
    app.state.hcx = HCXClient(settings)
    app.state.customize = Customize(settings.customize_dir)

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

    app.include_router(health.router)
    app.include_router(domain.router)
    app.include_router(coach.router)

    @app.get("/", include_in_schema=False)
    async def index():
        # Step 10 전까지는 API 문서로 이동
        return RedirectResponse("/docs")

    return app


app = create_app()

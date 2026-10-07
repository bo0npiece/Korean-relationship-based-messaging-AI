"""FastAPI 앱 조립. 실행: uvicorn app.main:app"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import Settings
from .routes import health


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="한국어 관계 기반 메시지 코치 API", version="0.1.0")
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Team-Key"],
    )

    app.include_router(health.router)

    @app.get("/", include_in_schema=False)
    async def index():
        # Step 10 전까지는 API 문서로 이동
        return RedirectResponse("/docs")

    return app


app = create_app()

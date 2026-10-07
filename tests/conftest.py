"""공통 테스트 도구."""
import json
import shutil
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

CUSTOMIZE = Path(__file__).resolve().parents[1] / "customize"


def build_client(tmp_path, handler=None, **env):
    """customize 사본 + 임시 data 폴더로 앱 생성. handler를 주면 실제 호출 대신 가짜 HCX 서버 사용."""
    if not (tmp_path / "customize").exists():
        shutil.copytree(CUSTOMIZE, tmp_path / "customize")
    env = {"DATA_DIR": str(tmp_path / "data"), "CUSTOMIZE_DIR": str(tmp_path / "customize"), **env}
    if handler:
        env.setdefault("MOCK_MODE", "0")
        env.setdefault("CLOVA_API_KEY", "test-key")
    app = create_app(Settings.from_env(env))
    if handler:
        app.state.hcx.transport = httpx.MockTransport(handler)
    return TestClient(app)


def hcx_reply(content, total_tokens=10):
    """가짜 HCX 성공 응답."""
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)
    return httpx.Response(200, json={
        "status": {"code": "20000"},
        "result": {"message": {"role": "assistant", "content": content}, "finishReason": "stop",
                   "usage": {"promptTokens": total_tokens - 1, "completionTokens": 1, "totalTokens": total_tokens}},
    })


@pytest.fixture
def client(tmp_path):
    return build_client(tmp_path)

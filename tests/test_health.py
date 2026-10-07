"""Step 1: 설정과 /api/health."""
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.config import Settings
from app.deps import require_team_key
from app.main import create_app


def make_client(tmp_path, **env):
    # 실제 .env를 읽지 않도록 env를 직접 넘김
    env = {"DATA_DIR": str(tmp_path / "data"), "CUSTOMIZE_DIR": str(tmp_path), **env}
    return TestClient(create_app(Settings.from_env(env)))


@pytest.mark.parametrize("env, mock, reason", [
    ({}, True, "MOCK_MODE=1"),                                      # 기본값은 MOCK
    ({"MOCK_MODE": "0"}, True, "CLOVA_API_KEY 없음"),               # 키 없으면 강제 MOCK
    ({"MOCK_MODE": "0", "CLOVA_API_KEY": "secret"}, False, None),   # 둘 다 있어야 실제 호출
])
def test_health_mock_mode(tmp_path, env, mock, reason):
    body = make_client(tmp_path, **env).get("/api/health").json()
    assert body["ok"] is True
    assert body["mock"] is mock
    assert body["mock_reason"] == reason
    assert body["models"]["analysis"] == "HCX-007"
    assert "secret" not in str(body)  # 키 노출 금지


def test_team_key_required_when_set(tmp_path):
    client = make_client(tmp_path, TEAM_API_KEY="team")

    @client.app.get("/api/_probe", dependencies=[Depends(require_team_key)])
    async def probe():
        return {"ok": True}

    assert client.get("/api/_probe").status_code == 401
    assert client.get("/api/_probe", headers={"X-Team-Key": "team"}).status_code == 200
    assert client.get("/api/health").status_code == 200  # health는 키 없이 열림

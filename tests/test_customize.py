"""customize/ 로더 (domain.yaml, prompts, schemas)."""
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.customize import Customize, CustomizeError
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1] / "customize"


def test_prompt_fill_and_reload_without_restart(tmp_path):
    shutil.copytree(ROOT, tmp_path / "c")
    client = TestClient(create_app(Settings.from_env({"DATA_DIR": str(tmp_path / "d"), "CUSTOMIZE_DIR": str(tmp_path / "c")})))
    assert client.get("/api/domain").json()["service"]["name"] == "메시지 코치"

    # 서버 재시작 없이 파일만 바꿔도 바로 반영
    path = tmp_path / "c" / "domain.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("메시지 코치", "새 서비스"), encoding="utf-8")
    assert client.get("/api/domain").json()["service"]["name"] == "새 서비스"

    # {변수} 채우기: 아는 변수만 채우고 JSON 중괄호 등은 그대로
    (tmp_path / "c" / "prompts" / "t.md").write_text("<!-- 메모 -->\n{relation}께 {unknown} {\"a\": 1}", encoding="utf-8")
    assert Customize(tmp_path / "c").prompt("t", relation="교수님") == "교수님께 {unknown} {\"a\": 1}"


def test_missing_file_gives_clear_error(tmp_path):
    custom = Customize(tmp_path)
    with pytest.raises(CustomizeError, match="schemas/none.json"):
        custom.schema("none")
    client = TestClient(create_app(Settings.from_env({"DATA_DIR": str(tmp_path / "d"), "CUSTOMIZE_DIR": str(tmp_path)})))
    response = client.get("/api/domain")
    assert response.status_code == 500 and "domain.yaml" in response.json()["detail"]

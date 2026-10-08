"""POST /api/route"""
from conftest import build_client, hcx_reply


def test_route_classifies(tmp_path):
    client = build_client(tmp_path, handler=lambda request: hcx_reply("Coach", total_tokens=7))
    body = client.post("/api/route", json={"text": "제가 쓴 메일 좀 봐 주세요"}).json()
    assert body["feature"] == "coach" and body["meta"]["total_tokens"] == 7

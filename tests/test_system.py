"""Step 9: /api/route, /api/usage."""
from conftest import build_client, hcx_reply


def test_route_classifies(tmp_path):
    client = build_client(tmp_path, handler=lambda request: hcx_reply("Coach", total_tokens=7))
    body = client.post("/api/route", json={"text": "제가 쓴 메일 좀 봐 주세요"}).json()
    assert body["feature"] == "coach" and body["meta"]["total_tokens"] == 7


def test_usage_by_feature_and_model(tmp_path):
    client = build_client(tmp_path, handler=lambda request: hcx_reply("interpret", total_tokens=12))
    client.post("/api/route", json={"text": "교수님 문자 무슨 뜻이에요?"})
    client.post("/api/route", json={"text": "교수님 문자 무슨 뜻이에요?"})  # temperature 0 → 캐시

    usage = client.get("/api/usage").json()
    assert usage["total"]["calls"] == 2 and usage["total"]["cached_calls"] == 1
    assert usage["by_feature"]["route"]["total_tokens"] == 12
    assert usage["by_model"]["HCX-DASH-002"]["live_calls"] == 1
    assert usage["limits"]["used_live_calls"] == 1 and usage["recent"][0]["cached"] is True

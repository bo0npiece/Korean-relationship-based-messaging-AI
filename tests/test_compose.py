"""① POST /api/compose"""


def test_compose_mock(client):
    body = client.post("/api/compose", json={"key_points": "과제 기한 하루 연장 부탁", "relation": "professor"}).json()
    assert body["draft"] and body["meta"]["calls"][0]["model"] == "HCX-007"

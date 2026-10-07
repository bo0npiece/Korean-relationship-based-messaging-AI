"""Step 10: 데모 화면 서빙 + MOCK으로 화면이 쓰는 API 전체 흐름."""


def test_demo_page_served(client):
    page = client.get("/")
    assert page.status_code == 200 and "/static/app.js" in page.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_mock_end_to_end_flow(client):
    # 프론트가 부르는 순서대로 MOCK에서 전부 응답하는지 확인
    cid = client.post("/api/contacts", json={"name": "김교수님", "relation": "professor"}).json()["id"]
    assert client.post("/api/compose", json={"key_points": "면담 요청", "contact_id": cid}).status_code == 200
    coach = client.post("/api/coach", json={"text": "교수님 면담 돼요?", "contact_id": cid}).json()
    assert set(coach["scores"]) == {"politeness", "clarity", "misunderstanding_risk"}
    assert client.post("/api/interpret", data={"text": "내일 오세요"}).status_code == 200
    sid = client.post("/api/rehearsal/start", json={"scenario_id": "example", "contact_id": cid}).json()["session_id"]
    client.post(f"/api/rehearsal/{sid}/message", json={"text": "안녕하세요"})
    assert "overall_score" in client.post(f"/api/rehearsal/{sid}/end").json()["report"]

    assert len(client.get(f"/api/contacts/{cid}/interactions").json()) == 3  # compose, coach, rehearsal
    usage = client.get("/api/usage").json()
    assert usage["total"]["mock_calls"] == usage["total"]["calls"] >= 5

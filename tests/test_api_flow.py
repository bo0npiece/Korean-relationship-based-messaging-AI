"""프론트가 부를 순서대로 MOCK에서 모든 API가 응답하는지 확인."""


def test_mock_end_to_end_flow(client):
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


def test_root_redirects_to_docs(client):
    page = client.get("/", follow_redirects=False)
    assert page.status_code == 307 and page.headers["location"] == "/docs"

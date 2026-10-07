"""Step 8: 리허설."""
import json

from conftest import build_client, hcx_reply


def test_rehearsal_window_and_feedback(tmp_path):
    sent = []

    def handler(request):
        payload = json.loads(request.content)
        sent.append((request.url.path, payload))
        if request.url.path.endswith("HCX-DASH-002"):
            return hcx_reply(f"교수님 대답 {len(sent)}")
        return hcx_reply({"overall_score": 80, "scores": {"politeness": 90, "clarity": 70, "naturalness": 80},
                          "goal_achieved": True, "good_points": ["인사"], "improvements": [], "summary": "좋아요"})

    client = build_client(tmp_path, handler=handler)
    domain = tmp_path / "customize" / "domain.yaml"
    domain.write_text(domain.read_text(encoding="utf-8").replace("rehearsal_window: 8", "rehearsal_window: 2"),
                      encoding="utf-8")

    sid = client.post("/api/rehearsal/start", json={"scenario_id": "example"}).json()["session_id"]
    for text in ["안녕하세요", "질문 있어요", "감사합니다"]:
        reply = client.post(f"/api/rehearsal/{sid}/message", json={"text": text}).json()["reply"]

    assert reply == "교수님 대답 3"
    last = sent[-1][1]
    assert last["maxTokens"] == 300                       # DASH-002는 maxTokens
    assert [m["role"] for m in last["messages"]] == ["system", "assistant", "user"]  # system + 최근 2개
    assert last["messages"][-1]["content"][0]["text"] == "감사합니다"

    report = client.post(f"/api/rehearsal/{sid}/end").json()
    assert report["report"]["overall_score"] == 80 and len(report["transcript"]) == 6
    assert "사용자: 안녕하세요" in sent[-1][1]["messages"][1]["content"][0]["text"]   # 전체 대화 평가
    assert client.post(f"/api/rehearsal/{sid}/end").json()["report"] == report["report"]  # 재호출 없음
    assert len(sent) == 4


def test_rehearsal_errors(client):
    assert client.post("/api/rehearsal/start", json={"scenario_id": "nope"}).status_code == 404
    sid = client.post("/api/rehearsal/start", json={"scenario_id": "example"}).json()["session_id"]
    assert client.post(f"/api/rehearsal/{sid}/end").status_code == 422     # 대화 없이 종료
    client.post(f"/api/rehearsal/{sid}/message", json={"text": "안녕하세요"})
    assert client.post(f"/api/rehearsal/{sid}/end").status_code == 200
    assert client.post(f"/api/rehearsal/{sid}/message", json={"text": "또"}).status_code == 409

"""Step 4: 코칭 API."""
from app.services.highlight import locate_spans
from conftest import build_client, hcx_reply

TEXT = "교수님 안녕하세요. 과제 좀 늦게 내도 돼요? 빨리 답장 주세요."


def test_coach_live_offsets(tmp_path):
    answer = {
        "scores": {"politeness": 40, "clarity": 70, "misunderstanding_risk": 60},
        "issues": [
            {"quote": "“빨리 답장 주세요.”", "problem": "재촉", "suggestion": "편하실 때 답장 부탁드립니다.", "severity": "high"},
            {"quote": "과제 좀  늦게", "problem": "구어체", "suggestion": "과제를 조금 늦게", "severity": "medium"},
            {"quote": "원문에 없는 말", "problem": "-", "suggestion": "-", "severity": "low"},
        ],
        "revised": "교수님, 안녕하세요. ...", "summary": "재촉하는 표현을 줄이세요.",
    }
    client = build_client(tmp_path, handler=lambda request: hcx_reply(answer))
    body = client.post("/api/coach", json={"text": TEXT, "relation": "professor"}).json()

    spans = [(i["start"], i["end"]) for i in body["issues"]]
    assert TEXT[spans[0][0]:spans[0][1]] == "빨리 답장 주세요."   # 따옴표 제거 후 일치
    assert TEXT[spans[1][0]:spans[1][1]] == "과제 좀 늦게"         # 공백 차이 무시
    assert spans[2] == (None, None)                                  # 못 찾으면 None
    assert body["meta"]["total_tokens"] == 10


def test_coach_mock_and_duplicate_quotes(client):
    body = client.post("/api/coach", json={"text": TEXT}).json()
    first = body["issues"][0]
    assert body["meta"]["calls"][0]["mock"] and TEXT[first["start"]:first["end"]] == "교수님 안녕하세요."

    # 같은 문장이 두 번 나오면 각각 다른 위치
    issues = locate_spans("네. 네.", [{"quote": "네."}, {"quote": "네."}])
    assert [(i["start"], i["end"]) for i in issues] == [(0, 2), (3, 5)]

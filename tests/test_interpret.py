"""③ POST /api/interpret — 입력 검사, 캡처 2단계 파이프라인(HCX-005 → HCX-007)."""
import io
import json

from PIL import Image

from conftest import build_client, hcx_reply


def png_bytes():
    out = io.BytesIO()
    Image.new("RGB", (40, 20), "white").save(out, "PNG")
    return out.getvalue()


def test_interpret_validation(client):
    assert client.post("/api/interpret", data={"text": "  "}).status_code == 422
    bad = client.post("/api/interpret", files={"image": ("a.png", b"not image", "image/png")})
    assert bad.status_code == 422


def test_interpret_image_two_step_pipeline(tmp_path):
    seen = []

    def handler(request):
        payload = json.loads(request.content)
        seen.append((request.url.path, payload))
        if request.url.path.endswith("HCX-005"):
            return hcx_reply("교수님: 내일 수업은 휴강입니다.")
        return hcx_reply({"intent": "휴강 안내", "emotion": "중립", "urgency": "medium",
                          "key_points": ["내일 휴강"], "reply_draft": "알려 주셔서 감사합니다."})

    client = build_client(tmp_path, handler=handler)
    body = client.post("/api/interpret", data={"relation": "professor"},
                       files={"image": ("cap.png", png_bytes(), "image/png")}).json()

    (path1, p1), (path2, p2) = seen
    assert path1.endswith("/HCX-005") and p1["messages"][0]["content"][1]["type"] == "image_url"
    # 접두어가 없으면 HCX가 400 Invalid parameter를 돌려줌
    assert p1["messages"][0]["content"][1]["dataUri"]["data"].startswith("data:image/jpeg;base64,")
    assert set(p1) == {"messages", "maxTokens", "temperature"}  # thinking/responseFormat 없음
    assert path2.endswith("/HCX-007") and "휴강입니다" in p2["messages"][1]["content"][0]["text"]
    assert body["extracted_text"] == "교수님: 내일 수업은 휴강입니다." and body["intent"] == "휴강 안내"
    assert len(body["meta"]["calls"]) == 2

"""Step 7: 관계 메모리."""
import json

from conftest import build_client, hcx_reply


def test_contact_crud(client):
    created = client.post("/api/contacts", json={"name": "김교수님", "relation": "professor", "profile": "답장이 빠름"}).json()
    cid = created["id"]
    assert client.put(f"/api/contacts/{cid}", json={"profile": "격식 중시"}).json()["profile"] == "격식 중시"
    assert [c["name"] for c in client.get("/api/contacts").json()] == ["김교수님"]
    assert client.delete(f"/api/contacts/{cid}").json() == {"deleted": True}
    assert client.get(f"/api/contacts/{cid}").status_code == 404
    assert client.post("/api/coach", json={"text": "안녕하세요", "contact_id": 999}).status_code == 404


def test_memory_injected_and_saved(tmp_path):
    systems = []

    def handler(request):
        systems.append(json.loads(request.content)["messages"][0]["content"][0]["text"])
        return hcx_reply({"draft": f"초안{len(systems)}", "notes": []})

    client = build_client(tmp_path, handler=handler)
    cid = client.post("/api/contacts", json={"name": "김교수님", "relation": "professor", "profile": "격식 중시"}).json()["id"]

    client.post("/api/compose", json={"key_points": "면담 요청", "contact_id": cid})
    client.post("/api/compose", json={"key_points": "면담 시간 변경", "contact_id": cid})

    # 첫 요청: 프로필 + 관계(상대 프로필에서 가져옴), 두 번째 요청: 지난 기록까지 반영
    assert "격식 중시" in systems[0] and "교수님에게 보낼" in systems[0]
    assert "[compose] 면담 요청 → 초안1" in systems[1]
    history = client.get(f"/api/contacts/{cid}/interactions").json()
    assert [h["input"] for h in history] == ["면담 시간 변경", "면담 요청"]

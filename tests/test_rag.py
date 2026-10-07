"""Step 6: RAG (MOCK 임베딩은 글자 2-gram 기반이라 비슷한 글이 실제로 가깝게 나옴)."""
import json

import httpx

from conftest import build_client, hcx_reply

KNOWLEDGE = """# 자료
## 교수님 이메일 예절
교수님께 이메일을 보낼 때는 학번과 이름을 먼저 밝힌다.

## 알바 대타 부탁
사장님께 대타를 부탁할 때는 대신 일할 사람을 미리 구해 둔다.
"""


def write_knowledge(tmp_path):
    client = build_client(tmp_path)  # customize 사본 생성
    (tmp_path / "customize" / "knowledge" / "manners.md").write_text(KNOWLEDGE, encoding="utf-8")
    return client


def test_search_ranks_and_caches_index(tmp_path):
    client = write_knowledge(tmp_path)
    hits = client.get("/api/knowledge/search", params={"q": "교수님께 이메일 보내기", "k": 2}).json()
    assert [h["title"] for h in hits] == ["교수님 이메일 예절", "알바 대타 부탁"]
    assert all(h["source"] == "manners.md" for h in hits)  # _example.md는 제외

    client.get("/api/knowledge/search", params={"q": "대타 부탁"})
    log = (tmp_path / "data" / "usage_log.jsonl").read_text(encoding="utf-8").splitlines()
    features = [json.loads(line)["feature"] for line in log]
    assert features.count("rag_index") == 2   # 조각 임베딩은 처음 한 번만
    assert features.count("rag_query") == 2


def test_references_injected_into_prompt(tmp_path):
    write_knowledge(tmp_path)
    systems = []

    def handler(request):
        if request.url.path.endswith("/embedding/v2"):
            text = json.loads(request.content)["text"]
            vec = [1.0, 0.0] if "교수님" in text else [0.0, 1.0]
            return httpx.Response(200, json={"status": {"code": "20000"}, "result": {"embedding": vec}})
        systems.append(json.loads(request.content)["messages"][0]["content"][0]["text"])
        return hcx_reply({"draft": "초안", "notes": []})

    client = build_client(tmp_path, handler=handler)
    body = client.post("/api/compose", json={"key_points": "교수님께 면담 요청"}).json()
    assert body["references"][0]["title"] == "교수님 이메일 예절"
    assert "학번과 이름을 먼저 밝힌다" in systems[0]

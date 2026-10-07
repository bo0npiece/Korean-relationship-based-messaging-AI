"""Step 2: HCX 클라이언트 (실제 API 대신 가짜 서버 사용)."""
import asyncio
import json

import httpx
import pytest

from app.config import Settings
from app.hcx import HCXClient, HCXError, text_message

SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "tags": {"type": "array", "items": {"type": "string", "pattern": "^[a-z]+$"}, "minItems": 2},
        "level": {"type": "string", "enum": ["high", "low"]},
    },
    "required": ["score", "tags", "level"],
    "additionalProperties": False,
}


def settings(tmp_path, **env):
    return Settings.from_env({"DATA_DIR": str(tmp_path), **env})


def log_lines(tmp_path):
    return [json.loads(line) for line in (tmp_path / "usage_log.jsonl").read_text(encoding="utf-8").splitlines()]


def test_mock_mode_fills_schema_and_logs(tmp_path):
    hcx = HCXClient(settings(tmp_path))  # 키 없음 → MOCK

    async def scenario():
        j = await hcx.chat_json("coach", "sys", "user", SCHEMA)
        e = await hcx.embed("rag", "교수님께 메일")
        c = await hcx.chat("rehearsal", [text_message("user", "안녕")])
        return j, e, c

    j, e, c = asyncio.run(scenario())
    assert j.mock and j.data["score"] == 70 and len(j.data["tags"]) == 2 and j.data["level"] == "high"
    assert len(e.data) == 1024
    assert c.text.startswith("[MOCK]")
    assert [(r["feature"], r["mock"]) for r in log_lines(tmp_path)] == [("coach", True), ("rag", True), ("rehearsal", True)]


def test_live_payload_retry_cache_and_limit(tmp_path):
    sent = []
    replies = [httpx.Response(429)]  # 첫 요청은 레이트리밋

    def handler(request: httpx.Request):
        sent.append(json.loads(request.content))
        if replies:
            return replies.pop(0)
        body = {"score": 80, "tags": ["a", "b"], "level": "low"}
        return httpx.Response(200, json={
            "status": {"code": "20000"},
            "result": {"message": {"role": "assistant", "content": json.dumps(body)},
                       "finishReason": "stop",
                       "usage": {"promptTokens": 10, "completionTokens": 5, "totalTokens": 15}},
        })

    hcx = HCXClient(settings(tmp_path, MOCK_MODE="0", CLOVA_API_KEY="k", MAX_LIVE_CALLS="3"),
                    transport=httpx.MockTransport(handler))
    hcx.retry_delays = (0, 0)  # 테스트에서는 기다리지 않음

    first = asyncio.run(hcx.chat_json("coach", "sys", "user", SCHEMA))
    assert first.data["level"] == "low" and not first.cached and len(sent) == 2  # 429 → 재시도 성공

    # HCX-007 Structured Outputs 형식 확인
    payload = sent[-1]
    assert payload["maxCompletionTokens"] == 2048 and "maxTokens" not in payload
    assert payload["thinking"] == {"effort": "none"}
    assert payload["messages"][0] == {"role": "system", "content": [{"type": "text", "text": "sys"}]}
    schema = payload["responseFormat"]["schema"]
    assert "additionalProperties" not in schema and "pattern" not in schema["properties"]["tags"]["items"]

    # 같은 요청은 캐시에서 → 서버 호출 없음
    second = asyncio.run(hcx.chat_json("coach", "sys", "user", SCHEMA))
    assert second.cached and len(sent) == 2

    logs = log_lines(tmp_path)
    assert [(r["status"], r["cached"], r["total_tokens"]) for r in logs] == [
        ("error", False, None), ("ok", False, 15), ("ok", True, None)]

    # 실제 호출 2회(429 포함) + 1회 = 3회 → 다음 호출은 한도 초과
    asyncio.run(hcx.chat("rehearsal", [text_message("user", "hi")], use_cache=False))
    with pytest.raises(HCXError) as error:
        asyncio.run(hcx.chat("rehearsal", [text_message("user", "hi")], use_cache=False))
    assert error.value.status_code == 429 and len(sent) == 3

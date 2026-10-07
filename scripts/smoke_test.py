"""실제 HCX API 연결 확인 (크레딧을 아주 조금 씀).

사용: .venv\\Scripts\\python.exe scripts\\smoke_test.py [--image 캡처.png]
.env에 CLOVA_API_KEY가 있고 MOCK_MODE=0 이어야 실행됨.
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 프로젝트 루트를 import 경로에 추가

from app.config import Settings  # noqa: E402
from app.hcx import HCXClient, HCXError, text_message  # noqa: E402
from app.hcx.image import prepare_image  # noqa: E402

SCHEMA = {
    "type": "object",
    "properties": {
        "politeness": {"type": "integer", "minimum": 0, "maximum": 100},
        "reason": {"type": "string"},
    },
    "required": ["politeness", "reason"],
}


def show(name, result, extra=""):
    print(f"[OK] {name:<10} model={result.model} tokens={result.usage.get('totalTokens')} "
          f"latency={result.latency_ms}ms {extra}")


async def main(image: str | None) -> int:
    settings = Settings.from_env()
    if settings.mock:
        print(f"MOCK 상태라 실제 호출을 하지 않습니다 ({settings.mock_reason}). .env를 확인하세요.")
        return 1
    hcx = HCXClient(settings)
    failed = 0

    async def run(name, coro, describe):
        nonlocal failed
        try:
            result = await coro
            show(name, result, describe(result))
        except HCXError as error:
            failed += 1
            print(f"[FAIL] {name:<10} {error.message}")

    # 1) 대화 (HCX-DASH-002)
    await run("chat", hcx.chat("smoke_test", [text_message("user", "한 문장으로 인사해 줘.")],
                               max_tokens=50, use_cache=False),
              lambda r: f"→ {r.text[:40]!r}")
    # 2) Structured Outputs (HCX-007)
    await run("chat_json", hcx.chat_json("smoke_test", "메시지의 공손도를 평가하세요.",
                                         "교수님, 내일 면담 가능하실까요?", SCHEMA, max_tokens=300, use_cache=False),
              lambda r: f"→ {r.data}")
    # 3) 임베딩 v2
    await run("embed", hcx.embed("smoke_test", "교수님께 보내는 메일", use_cache=False),
              lambda r: f"→ {len(r.data)}차원")
    # 4) 이미지 (선택, HCX-005)
    if image:
        b64 = prepare_image(Path(image).read_bytes())
        await run("image", hcx.read_image("smoke_test", "이미지 속 글자를 그대로 적어 줘.",
                                          image_b64=b64, max_tokens=300, use_cache=False),
                  lambda r: f"→ {r.text[:40]!r}")

    print(f"\n기록: {settings.usage_log_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="이미지 읽기까지 확인할 캡처 파일 경로")
    sys.exit(asyncio.run(main(parser.parse_args().image)))

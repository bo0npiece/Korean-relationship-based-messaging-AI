"""자유 입력 → 어떤 기능으로 보낼지 분류 (가벼운 HCX-DASH-002 사용)."""
from ..hcx import text_message
from .common import meta

# 엔진이 제공하는 기능 id (프론트 탭 이름과 같음)
FEATURES = ("compose", "coach", "interpret", "rehearsal")


def parse_feature(output: str) -> str | None:
    """모델 출력에서 가장 먼저 나온 기능 id를 찾음."""
    lowered = output.lower()
    found = [(lowered.find(f), f) for f in FEATURES if f in lowered]
    return min(found)[1] if found else None


async def route(core, text: str) -> dict:
    system = core.customize.prompt("route", features=", ".join(FEATURES))
    result = await core.hcx.chat("route", [text_message("system", system), text_message("user", text)],
                                 max_tokens=20, temperature=0)
    return {"feature": parse_feature(result.text), "raw": result.text.strip(), "text": text, "meta": meta(result)}

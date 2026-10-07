"""② 내 글 코칭: 점수 + 문제 구간 + 수정본."""
from .common import meta, prepare
from .highlight import first_sentence, locate_spans


async def coach(core, text: str, relation: str | None = None, purpose: str | None = None) -> dict:
    values, refs = await prepare(core, text, relation, purpose)
    system = core.customize.prompt("coach", **values)
    result = await core.hcx.chat_json("coach", system, text, core.customize.schema("coach"))

    data = result.data
    issues = data.get("issues") or []
    if result.mock:
        # MOCK에서도 하이라이트 화면을 확인할 수 있게 첫 문장을 문제 구간으로 지정
        for issue in issues:
            issue["quote"] = first_sentence(text)
    data["issues"] = locate_spans(text, issues)
    return {"original": text, **data, "references": refs, "meta": meta(result)}

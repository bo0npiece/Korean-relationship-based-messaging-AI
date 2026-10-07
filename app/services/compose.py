"""① 작성 도우미: 관계·목적·핵심 내용 → 메시지 초안."""
from .common import meta, prepare


async def compose(core, key_points: str, relation: str | None = None, purpose: str | None = None) -> dict:
    values, refs = await prepare(core, key_points, relation, purpose)
    system = core.customize.prompt("compose", **values)
    result = await core.hcx.chat_json("compose", system, key_points, core.customize.schema("compose"),
                                      temperature=0.5)
    return {**result.data, "references": refs, "meta": meta(result)}

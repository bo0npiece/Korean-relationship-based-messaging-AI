"""① 작성 도우미: 관계·목적·핵심 내용 → 메시지 초안."""
from .shared import build_prompt_values, call_meta, find_contact, save_interaction


async def compose(core, key_points: str, relation: str | None = None, purpose: str | None = None,
                  contact_id: int | None = None) -> dict:
    contact = find_contact(core, contact_id)
    values, refs = await build_prompt_values(core, key_points, relation, purpose, contact)
    system = core.customize.prompt("compose", **values)
    result = await core.hcx.chat_json("compose", system, key_points, core.customize.schema("compose"),
                                      temperature=0.5)
    save_interaction(core, contact, "compose", key_points, result.data.get("draft", ""))
    return {**result.data, "references": refs, "meta": call_meta(result)}

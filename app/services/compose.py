"""① 작성 도우미: 관계·목적·핵심 내용 → 메시지 초안."""
from ..customize import Customize
from ..hcx import HCXClient
from .common import base_values, meta


async def compose(hcx: HCXClient, customize: Customize, key_points: str,
                  relation: str | None = None, purpose: str | None = None) -> dict:
    values = base_values(customize, relation, purpose)
    system = customize.prompt("compose", **values)
    result = await hcx.chat_json("compose", system, key_points, customize.schema("compose"),
                                 temperature=0.5)
    return {**result.data, "meta": meta(result)}

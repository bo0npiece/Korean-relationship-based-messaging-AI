"""③ 받은 메시지 해석: (캡처면 HCX-005로 글자 추출) → HCX-007로 의도·감정 분석 + 답장 초안."""
from .common import meta, prepare


async def interpret(core, text: str | None = None, image_b64: str | None = None,
                    relation: str | None = None) -> dict:
    calls = []
    extracted = None
    if image_b64:
        # 1단계: 이미지 → 텍스트 (HCX-007은 이미지 입력 불가라 HCX-005 사용)
        ocr = await core.hcx.read_image("interpret_ocr", core.customize.prompt("ocr"), image_b64=image_b64)
        extracted = ocr.text.strip()
        calls.append(ocr)

    message = "\n\n".join(x for x in (text, extracted) if x)

    # 2단계: 텍스트 분석
    values, refs = await prepare(core, message, relation)
    system = core.customize.prompt("interpret", **values)
    result = await core.hcx.chat_json("interpret", system, message, core.customize.schema("interpret"))
    calls.append(result)
    return {"source_text": message, "extracted_text": extracted, **result.data,
            "references": refs, "meta": meta(*calls)}
